# Module 9: Remote State and Backends

## Level: INTERMEDIATE | Estimated Time: 3 hours

---

## 9.1 Why Remote State?

```
┌─────────────────────────────────────────────────────────────┐
│              LOCAL STATE vs REMOTE STATE                     │
├──────────────────────────┬──────────────────────────────────┤
│      Local State         │       Remote State               │
├──────────────────────────┼──────────────────────────────────┤
│ Single user only         │ Team collaboration               │
│ No locking               │ Automatic locking                │
│ No encryption            │ Encryption at rest               │
│ No versioning            │ Version history                  │
│ Risk of data loss        │ Durable storage                  │
│ Sensitive data in plain  │ Access control via IAM           │
│ No audit trail           │ CloudTrail logging               │
└──────────────────────────┴──────────────────────────────────┘
```

---

## 9.2 S3 Backend (Most Common for AWS)

### Step 1: Create the Backend Infrastructure

```hcl
# backend-setup/main.tf
# Run this ONCE to create the S3 bucket and DynamoDB table

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "mycompany-terraform-state-123456"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
```

```bash
cd backend-setup
terraform init && terraform apply
```

### Step 2: Configure the Backend

```hcl
# In your project's providers.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state-123456"
    key            = "projects/myapp/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
```

### Step 3: Initialize with Backend

```bash
terraform init
```

**Output:**
```
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.

Initializing provider plugins...

Terraform has been successfully initialized!
```

### Migrating from Local to Remote

If you already have local state:

```bash
terraform init
```

**Output:**
```
Initializing the backend...
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend
  to the newly configured "s3" backend. No existing state was found in the
  newly configured "s3" backend. Do you want to copy this state to the new
  "s3" backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

---

## 9.3 Backend Configuration Options

### Partial Configuration

Don't hardcode backend values — use partial configuration:

```hcl
# providers.tf — minimal backend block
terraform {
  backend "s3" {}
}
```

```hcl
# backend-configs/dev.hcl
bucket         = "mycompany-terraform-state"
key            = "dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks"
encrypt        = true
```

```hcl
# backend-configs/prod.hcl
bucket         = "mycompany-terraform-state"
key            = "prod/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-locks"
encrypt        = true
```

```bash
# Initialize with specific backend config
terraform init -backend-config=backend-configs/dev.hcl
terraform init -backend-config=backend-configs/prod.hcl
```

### Command-Line Backend Config

```bash
terraform init \
  -backend-config="bucket=mycompany-terraform-state" \
  -backend-config="key=myapp/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

---

## 9.4 State File Organization

### Pattern 1: Per-Environment Keys

```
s3://terraform-state/
├── dev/terraform.tfstate
├── staging/terraform.tfstate
└── prod/terraform.tfstate
```

### Pattern 2: Per-Project and Environment

```
s3://terraform-state/
├── networking/
│   ├── dev/terraform.tfstate
│   └── prod/terraform.tfstate
├── compute/
│   ├── dev/terraform.tfstate
│   └── prod/terraform.tfstate
└── database/
    ├── dev/terraform.tfstate
    └── prod/terraform.tfstate
```

### Pattern 3: Per-Account Buckets

```
s3://terraform-state-dev-account/
├── networking/terraform.tfstate
├── compute/terraform.tfstate
└── database/terraform.tfstate

s3://terraform-state-prod-account/
├── networking/terraform.tfstate
├── compute/terraform.tfstate
└── database/terraform.tfstate
```

---

## 9.5 Remote State Data Source

Read outputs from another Terraform project's state:

```hcl
# Project: networking (produces VPC outputs)
# State at: s3://terraform-state/networking/terraform.tfstate

output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}
```

```hcl
# Project: compute (consumes networking outputs)

data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "mycompany-terraform-state"
    key    = "networking/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"

  # Use outputs from the networking project
  subnet_id = data.terraform_remote_state.networking.outputs.private_subnet_ids[0]

  tags = {
    Name  = "app-server"
    VpcId = data.terraform_remote_state.networking.outputs.vpc_id
  }
}
```

### Architecture with Remote State

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Networking    │     │    Compute      │     │    Database     │
│   Project       │     │    Project      │     │    Project      │
│                 │     │                 │     │                 │
│ VPC, Subnets,   │────▶│ EC2, ALB, ASG   │     │ RDS, ElastiCache│
│ IGW, NAT, SG    │     │                 │────▶│                 │
│                 │     │                 │     │                 │
│ Outputs:        │     │ Reads:          │     │ Reads:          │
│ - vpc_id        │     │ - vpc_id        │     │ - vpc_id        │
│ - subnet_ids    │     │ - subnet_ids    │     │ - subnet_ids    │
│ - sg_ids        │     │ - sg_ids        │     │ - sg_ids        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         ▼                       ▼                        ▼
    ┌─────────────────────────────────────────────────────────┐
    │              S3 Bucket (terraform-state)                │
    │  networking/tfstate  compute/tfstate  database/tfstate  │
    └─────────────────────────────────────────────────────────┘
```

---

## 9.6 Other Backend Types

### Terraform Cloud / HCP Terraform

```hcl
terraform {
  cloud {
    organization = "my-org"
    workspaces {
      name = "my-workspace"
    }
  }
}
```

### Consul Backend

```hcl
terraform {
  backend "consul" {
    address = "consul.example.com:8500"
    scheme  = "https"
    path    = "terraform/myapp"
  }
}
```

### HTTP Backend

```hcl
terraform {
  backend "http" {
    address        = "https://myrest.api.com/state"
    lock_address   = "https://myrest.api.com/state/lock"
    unlock_address = "https://myrest.api.com/state/lock"
  }
}
```

### PostgreSQL Backend

```hcl
terraform {
  backend "pg" {
    conn_str = "postgres://user:pass@db.example.com/terraform_state"
  }
}
```

---

## 9.7 Backend Migration

### Switching Backends

```bash
# Change backend config in providers.tf, then:
terraform init -migrate-state
```

**Output:**
```
Initializing the backend...
Backend configuration changed!

Terraform has detected that the configuration specified for the backend
has changed. Terraform will now check for existing state in the backends.

Do you want to copy existing state to the new backend?

  Enter a value: yes

Successfully configured the backend "s3"!
```

### Switching from Remote to Local

```hcl
# Remove the backend block entirely, then:
```

```bash
terraform init -migrate-state
```

**Output:**
```
Terraform has detected you're unconfiguring your previously set "s3" backend.
Do you want to copy the state from the "s3" backend to the "local" backend?

  Enter a value: yes
```

---

## 9.8 State Locking Deep Dive

### What is State Locking?

State locking prevents two Terraform operations from writing to the same state file simultaneously. Without locking, concurrent `terraform apply` runs can corrupt state, orphan resources, or create duplicates.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Why State Locking Exists                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Without locking:                                               │
│                                                                 │
│  User A: apply → reads state → creates EC2 i-111               │
│  User B: apply → reads SAME state → creates EC2 i-222          │
│  User A: writes state (i-111)                                   │
│  User B: writes state (i-222) → OVERWRITES User A's state      │
│                                                                 │
│  Result: i-111 exists in AWS but NOT in state = orphaned        │
│          Next plan shows "1 to add" (creates duplicate)         │
│                                                                 │
│  With locking:                                                  │
│                                                                 │
│  User A: apply → acquires lock ✅ → runs normally               │
│  User B: apply → tries lock → BLOCKED ❌ → waits or fails      │
│  User A: finishes → releases lock                               │
│  User B: retries → acquires lock ✅ → runs with updated state   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Which Operations Acquire Locks?

```
┌──────────────────────┬──────────┬──────────────────────────────┐
│ Command              │ Locks?   │ Notes                        │
├──────────────────────┼──────────┼──────────────────────────────┤
│ terraform plan       │ Yes      │ Read lock (refreshes state)  │
│ terraform apply      │ Yes      │ Write lock (modifies state)  │
│ terraform destroy    │ Yes      │ Write lock (modifies state)  │
│ terraform import     │ Yes      │ Write lock (adds to state)   │
│ terraform refresh    │ Yes      │ Write lock (updates state)   │
│ terraform state mv   │ Yes      │ Write lock (modifies state)  │
│ terraform state rm   │ Yes      │ Write lock (modifies state)  │
│ terraform output     │ No       │ Read-only, no state change   │
│ terraform state list │ No       │ Read-only, no state change   │
│ terraform state show │ No       │ Read-only, no state change   │
│ terraform validate   │ No       │ Doesn't touch state at all   │
│ terraform fmt        │ No       │ Doesn't touch state at all   │
└──────────────────────┴──────────┴──────────────────────────────┘
```

### How DynamoDB Locking Works (S3 Backend)

```
terraform apply
  │
  ├── 1. PUT item to DynamoDB (LockID = state key)
  │      If item exists → ERROR (state locked by someone else)
  │      If item doesn't exist → Lock acquired ✅
  │
  ├── 2. Read state from S3
  │
  ├── 3. Refresh (query cloud APIs for current resource state)
  │
  ├── 4. Build plan and execute changes
  │
  ├── 5. Write updated state to S3
  │
  └── 6. DELETE item from DynamoDB (release lock)
```

### DynamoDB Lock Item Structure

When Terraform acquires a lock, it writes this item to DynamoDB:

```json
{
  "LockID": {
    "S": "mycompany-terraform-state/prod/terraform.tfstate"
  },
  "Info": {
    "S": "{\"ID\":\"a1b2c3d4-e5f6-7890\",\"Operation\":\"OperationTypeApply\",\"Who\":\"devops@ip-10-0-1-50\",\"Version\":\"1.9.0\",\"Created\":\"2024-01-15T10:30:00.123456Z\",\"Path\":\"prod/terraform.tfstate\"}"
  }
}
```

**Fields explained:**

```
┌──────────┬──────────────────────────────────────────────────────┐
│ Field    │ Meaning                                              │
├──────────┼──────────────────────────────────────────────────────┤
│ LockID   │ S3 bucket + key path (unique per state file)        │
│ ID       │ UUID of this specific lock instance                  │
│ Operation│ OperationTypeApply, OperationTypePlan, etc.          │
│ Who      │ username@hostname of the person/CI holding the lock  │
│ Version  │ Terraform version                                    │
│ Created  │ Timestamp when lock was acquired                     │
│ Path     │ State file path within the backend                   │
└──────────┴──────────────────────────────────────────────────────┘
```

**Inspect the lock manually:**

```bash
aws dynamodb get-item \
  --table-name terraform-state-locks \
  --key '{"LockID":{"S":"mycompany-terraform-state/prod/terraform.tfstate"}}'
```

**Output (when locked):**
```json
{
    "Item": {
        "LockID": {
            "S": "mycompany-terraform-state/prod/terraform.tfstate"
        },
        "Info": {
            "S": "{\"ID\":\"a1b2c3d4-e5f6-7890\",\"Operation\":\"OperationTypeApply\",\"Who\":\"devops@ip-10-0-1-50\",\"Version\":\"1.9.0\",\"Created\":\"2024-01-15T10:30:00Z\"}"
        }
    }
}
```

**Output (when NOT locked):**
```json
{}
```

### Local State Locking

Even with local state, Terraform creates a temporary lock file:

```bash
# During terraform apply, this file appears:
ls -la
```

```
-rw-r--r-- 1 user user  5432 Jan 15 10:30 terraform.tfstate
-rw-r--r-- 1 user user   234 Jan 15 10:30 .terraform.tfstate.lock.info
```

**Contents of `.terraform.tfstate.lock.info`:**

```json
{
  "ID": "f8e7d6c5-b4a3-2190",
  "Operation": "OperationTypeApply",
  "Who": "user@laptop",
  "Version": "1.9.0",
  "Created": "2024-01-15T10:30:00Z",
  "Path": "terraform.tfstate"
}
```

This file is automatically deleted when the operation completes. If Terraform crashes, the file remains and blocks subsequent operations.

**Fix for stuck local lock:**

```bash
# Verify no other Terraform process is running
ps aux | grep terraform

# If no process is running, delete the lock file
rm .terraform.tfstate.lock.info

# Resume operations
terraform plan
```

### Lock Error and Recovery

**Error when someone else holds the lock:**

```bash
terraform apply
```

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        a1b2c3d4-e5f6-7890
  Path:      mycompany-terraform-state/prod/terraform.tfstate
  Operation: OperationTypeApply
  Who:       ci-runner@github-actions-runner-abc123
  Version:   1.9.0
  Created:   2024-01-15 10:30:00.123456 UTC

Terraform acquires a state lock to protect the state from being written
by multiple users at the same time. Please resolve the issue above and try
again. For most commands, you can disable locking with the "-lock=false"
flag, but this is not recommended.
```

**Step-by-step recovery:**

```bash
# Step 1: Check who holds the lock (read the "Who" and "Created" fields)
# If "Who" is a CI runner and "Created" was 3 hours ago → probably crashed

# Step 2: Verify the holder isn't still running
aws dynamodb get-item \
  --table-name terraform-state-locks \
  --key '{"LockID":{"S":"mycompany-terraform-state/prod/terraform.tfstate"}}' \
  --query 'Item.Info.S' --output text | python3 -m json.tool
```

```json
{
    "ID": "a1b2c3d4-e5f6-7890",
    "Operation": "OperationTypeApply",
    "Who": "ci-runner@github-actions-runner-abc123",
    "Version": "1.9.0",
    "Created": "2024-01-15T10:30:00Z"
}
```

```bash
# Step 3: Force unlock (use the ID from the error message)
terraform force-unlock a1b2c3d4-e5f6-7890
```

**Output:**
```
Do you really want to force-unlock?
  Terraform will remove the lock on the remote state.
  This will allow local Terraform commands to modify this state, even though it
  may still be in use. Only 'yes' will be accepted to confirm.

  Enter a value: yes

Terraform state has been successfully unlocked!
```

```bash
# Step 4: Verify state integrity
terraform plan
# If the crashed apply was partial, some resources may need import or targeted apply
```

### Lock Timeout (`-lock-timeout`)

Instead of failing immediately when the lock is held, you can wait:

```bash
# Wait up to 5 minutes for the lock to be released
terraform apply -lock-timeout=5m

# Wait up to 30 seconds
terraform plan -lock-timeout=30s
```

**Output (waiting for lock):**
```
Acquiring state lock. This may take a few moments...
Acquiring state lock. This may take a few moments...
Acquiring state lock. This may take a few moments...

# After the other operation finishes:
Lock acquired. Proceeding with plan...
```

**Output (timeout exceeded):**
```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        a1b2c3d4-e5f6-7890
  ...

Terraform timed out waiting for the state lock after 5m0s.
```

### Disabling Locking

```bash
# Skip locking entirely (DANGEROUS — use only for read-only operations or emergencies)
terraform plan -lock=false
terraform apply -lock=false
```

> ⚠️ Never use `-lock=false` in CI/CD pipelines or team environments. It defeats the purpose of remote state and can cause state corruption.

**When `-lock=false` is acceptable:**
- Running `terraform plan` on a read-only CI job that never applies
- Emergency recovery when the lock table is unavailable
- Local development with no team collaboration

---

### Disadvantages of State Locking

```
┌──────────────────────────────────────────────────────────────────┐
│              Disadvantages of State Locking                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. BLOCKED PIPELINES                                            │
│     If one CI/CD pipeline is running terraform apply, all        │
│     other pipelines for the same state are blocked until it      │
│     finishes. Long applies (20+ minutes) create bottlenecks.    │
│                                                                  │
│  2. STUCK LOCKS (STALE LOCKS)                                    │
│     If Terraform crashes, gets killed (kill -9), or the CI       │
│     runner dies mid-apply, the lock remains in DynamoDB.         │
│     All subsequent operations fail until someone manually        │
│     runs terraform force-unlock.                                 │
│                                                                  │
│  3. ADDITIONAL INFRASTRUCTURE COST                               │
│     DynamoDB table required for AWS (even if minimal cost).      │
│     Must be provisioned, maintained, and monitored separately.   │
│     Lock table must exist BEFORE the state backend is used.      │
│                                                                  │
│  4. SINGLE POINT OF FAILURE                                      │
│     If DynamoDB is unavailable (region outage, IAM issue,        │
│     table deleted), ALL Terraform operations fail — even         │
│     terraform plan. No fallback to unlocked mode.                │
│                                                                  │
│  5. PERFORMANCE OVERHEAD                                         │
│     Every plan/apply adds DynamoDB API calls (PUT + DELETE).     │
│     Adds ~1-2 seconds per operation. Negligible for single       │
│     runs, but adds up in CI with many workspaces.                │
│                                                                  │
│  6. LOCK CONTENTION IN LARGE TEAMS                               │
│     Teams with 10+ engineers working on the same state file      │
│     experience frequent lock conflicts. Engineers wait for       │
│     each other's plans to finish before they can run theirs.     │
│                                                                  │
│  7. NO QUEUING MECHANISM                                         │
│     Terraform doesn't queue lock requests. If the lock is        │
│     held, the operation fails (unless -lock-timeout is set).     │
│     No built-in "wait in line" behavior.                         │
│                                                                  │
│  8. FORCE-UNLOCK RISK                                            │
│     terraform force-unlock is dangerous if the original          │
│     operation is still running. Unlocking while another          │
│     apply is in progress can corrupt state.                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Real-Life Scenarios and Solutions

**Problem 1: CI pipeline stuck because lock is held by a crashed job**

```bash
# Jenkins job ran terraform apply, Jenkins killed the job after 30 min timeout
# Lock is now stuck in DynamoDB

# Every subsequent pipeline run fails:
terraform plan
```

```
Error: Error acquiring the state lock
Lock Info:
  Who:       jenkins@build-agent-42
  Created:   2024-01-15 08:00:00 UTC    # 4 hours ago — clearly stale
```

**Solution:**

```bash
# Verify the Jenkins job is actually dead
# Then force-unlock
terraform force-unlock <LOCK_ID>
```

**Prevention:** Add a cleanup step to CI pipelines:

```yaml
# GitHub Actions — always release lock even if apply fails
jobs:
  deploy:
    steps:
      - run: terraform apply -auto-approve
        continue-on-error: true
        id: apply

      # Lock is automatically released on normal exit
      # But if the runner crashes, you need monitoring
```

---

**Problem 2: Lock contention — 5 engineers blocked by one long apply**

```
Engineer A: terraform apply (creating EKS cluster — takes 20 minutes)
Engineer B: terraform plan → BLOCKED ❌
Engineer C: terraform plan → BLOCKED ❌
Engineer D: terraform plan → BLOCKED ❌
Engineer E: terraform plan → BLOCKED ❌
```

**Solution: Split state into smaller, independent state files:**

```
# Before: 1 state with 500 resources (everyone blocks everyone)
infrastructure/
└── terraform.tfstate

# After: 4 states (teams work independently)
networking/     → terraform.tfstate  (VPC, subnets — rarely changes)
compute/        → terraform.tfstate  (EC2, ASG — team A)
database/       → terraform.tfstate  (RDS, DynamoDB — team B)
monitoring/     → terraform.tfstate  (CloudWatch — team C)
```

Each state has its own lock, so teams don't block each other.

---

**Problem 3: DynamoDB table accidentally deleted**

```bash
terraform plan
```

```
Error: Error acquiring the state lock

Error message: ResourceNotFoundException: Requested resource not found:
Table: terraform-state-locks not found
```

**Solution:**

```bash
# Option 1: Recreate the table manually
aws dynamodb create-table \
  --table-name terraform-state-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Option 2: Run without locking temporarily (DANGEROUS)
terraform plan -lock=false
```

**Prevention:** Protect the lock table with `prevent_destroy`:

```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}
```

---

### State Locking: Best Practices

```
┌──────────────────────────────────────────────────────────────────┐
│              State Locking Best Practices                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Always enable locking (never skip in production)             │
│  ✅ Use -lock-timeout=5m in CI to handle brief contention       │
│  ✅ Split large states to reduce lock contention                 │
│  ✅ Monitor for stale locks (alert if lock age > 30 minutes)    │
│  ✅ Protect the DynamoDB table with prevent_destroy              │
│  ✅ Use PAY_PER_REQUEST billing for the lock table               │
│  ✅ Document force-unlock procedures for your team               │
│                                                                  │
│  ❌ Never use -lock=false in CI/CD                               │
│  ❌ Never force-unlock without verifying the holder is dead      │
│  ❌ Never delete the DynamoDB lock table                         │
│  ❌ Never have 500+ resources in a single state file             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9.9 Common Errors

### Error: Backend Initialization Required

```
Error: Backend initialization required, please run "terraform init"

Reason: Initial configuration of the requested backend "s3"
```

**Fix:** Run `terraform init`.

### Error: State Lock Timeout

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException
```

**Fix:**
```bash
# Check who holds the lock
aws dynamodb get-item \
  --table-name terraform-state-locks \
  --key '{"LockID":{"S":"bucket/key/terraform.tfstate"}}'

# Force unlock if the holder crashed
terraform force-unlock <LOCK_ID>
```

### Error: Access Denied to S3

```
Error: Failed to load state: AccessDenied: Access Denied
```

**Fix:** Ensure your IAM user/role has these permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::terraform-state-bucket",
    "arn:aws:s3:::terraform-state-bucket/*"
  ]
}
```

---

## 9.10 Real-Life Best Practices

| Practice | Reason |
|----------|--------|
| One S3 bucket per AWS account | Simplifies IAM and billing |
| Enable versioning on state bucket | Rollback capability |
| Enable encryption (KMS) | Compliance and security |
| Block all public access | State contains secrets |
| Use DynamoDB for locking | Prevent concurrent modifications |
| Use separate state keys per project | Blast radius reduction |
| Use partial backend config | Environment flexibility |
| Enable CloudTrail on state bucket | Audit trail |

---

## Exercises

### Exercise 9.1: Set Up Remote Backend
1. Create an S3 bucket and DynamoDB table
2. Configure the S3 backend in a project
3. Run `terraform init` to migrate state
4. Verify state exists in S3

### Exercise 9.2: Remote State Data Source
1. Create a "networking" project that outputs VPC and subnet IDs
2. Create a "compute" project that reads those outputs via `terraform_remote_state`
3. Deploy an EC2 instance using the networking outputs

### Exercise 9.3: Concurrent Access
1. Open two terminals
2. Run `terraform apply` in both simultaneously
3. Observe the locking behavior
4. Practice `force-unlock`

---

## Key Takeaways

- Remote backends enable team collaboration with locking and encryption
- S3 + DynamoDB is the standard AWS backend setup
- Use partial backend configuration for environment flexibility
- `terraform_remote_state` data source connects projects
- Always enable versioning and encryption on state buckets
- State locking prevents concurrent modifications
- Use `terraform init -migrate-state` when switching backends

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Backend Configuration | [developer.hashicorp.com/terraform/language/backend](https://developer.hashicorp.com/terraform/language/backend) |
| S3 Backend | [developer.hashicorp.com/terraform/language/backend/s3](https://developer.hashicorp.com/terraform/language/backend/s3) |
| Remote State | [developer.hashicorp.com/terraform/language/state/remote](https://developer.hashicorp.com/terraform/language/state/remote) |
| State Locking | [developer.hashicorp.com/terraform/language/state/locking](https://developer.hashicorp.com/terraform/language/state/locking) |
| `terraform_remote_state` Data Source | [developer.hashicorp.com/terraform/language/state/remote-state-data](https://developer.hashicorp.com/terraform/language/state/remote-state-data) |
| `terraform init -migrate-state` | [developer.hashicorp.com/terraform/cli/commands/init#backend-initialization](https://developer.hashicorp.com/terraform/cli/commands/init#backend-initialization) |
| `terraform init -reconfigure` | [developer.hashicorp.com/terraform/cli/commands/init#reconfigure](https://developer.hashicorp.com/terraform/cli/commands/init#reconfigure) |
| `terraform force-unlock` | [developer.hashicorp.com/terraform/cli/commands/force-unlock](https://developer.hashicorp.com/terraform/cli/commands/force-unlock) |
| Consul Backend | [developer.hashicorp.com/terraform/language/backend/consul](https://developer.hashicorp.com/terraform/language/backend/consul) |
| GCS Backend | [developer.hashicorp.com/terraform/language/backend/gcs](https://developer.hashicorp.com/terraform/language/backend/gcs) |
| `aws_s3_bucket` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) |
| `aws_dynamodb_table` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table) |

---

[← Previous Module](../module-08-state-commands-and-operations/README.md) | [Next Module: Modules →](../module-10-modules/README.md)
