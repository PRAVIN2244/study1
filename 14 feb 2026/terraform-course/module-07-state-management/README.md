# Module 7: State Management

## Level: INTERMEDIATE | Estimated Time: 3 hours

---

## 7.1 What is Terraform State?

State is how Terraform maps your configuration to real-world resources. Without state, Terraform wouldn't know which cloud resources it manages.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   main.tf       │     │  terraform.tfstate│     │   AWS Cloud     │
│                 │     │                  │     │                 │
│ aws_instance    │◄───▶│ "i-0abc123"      │◄───▶│ EC2 Instance    │
│   "web"         │     │                  │     │ i-0abc123       │
│                 │     │                  │     │                 │
│ aws_s3_bucket   │◄───▶│ "my-bucket"      │◄───▶│ S3 Bucket       │
│   "data"        │     │                  │     │ my-bucket       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     Config                   State                  Real World
```

### What State Tracks

- Resource IDs and attributes
- Resource dependencies
- Metadata (provider info, schema version)
- Sensitive values (encrypted in remote backends)

---

## 7.2 State File Structure

```bash
# After terraform apply, examine the state
cat terraform.tfstate
```

```json
{
  "version": 4,
  "terraform_version": "1.9.0",
  "serial": 3,
  "lineage": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "outputs": {
    "instance_id": {
      "value": "i-0abc123def456",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "i-0abc123def456",
            "ami": "ami-0c55b159cbfafe1f0",
            "instance_type": "t2.micro",
            "public_ip": "54.123.45.67",
            "private_ip": "10.0.1.50",
            "tags": {
              "Name": "web-server"
            }
          }
        }
      ]
    },
    {
      "mode": "data",
      "type": "aws_ami",
      "name": "amazon_linux",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "attributes": {
            "id": "ami-0c55b159cbfafe1f0",
            "name": "amzn2-ami-hvm-2.0.20231218.0-x86_64-gp2"
          }
        }
      ]
    }
  ]
}
```

### Key Fields

| Field | Purpose |
|-------|---------|
| `version` | State file format version |
| `serial` | Increments on every state change (conflict detection) |
| `lineage` | Unique ID for this state's history |
| `outputs` | Current output values |
| `resources` | All managed resources and their attributes |

---

## 7.3 How Terraform Uses State

### During `terraform plan`

```
1. Read state file
2. Refresh: Query cloud APIs for current state of each resource
3. Compare: Diff config vs refreshed state
4. Generate plan: List of create/update/destroy actions
```

```bash
# Skip the refresh step (faster, but may miss drift)
terraform plan -refresh=false
```

### During `terraform apply`

```
1. Execute the plan
2. Update state file with new resource attributes
3. Increment serial number
4. Write state file
```

### State Locking

When using remote backends, Terraform locks the state during operations:

```
User A: terraform apply
  → Acquires lock ✅
  → Makes changes
  → Releases lock

User B: terraform apply (concurrent)
  → Tries to acquire lock ❌
  → Error: "state is locked"
```

**Lock Error:**
```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        a1b2c3d4-e5f6-7890
  Path:      terraform-state/prod/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Version:   1.9.0
  Created:   2024-01-15 10:30:00.000000 UTC
```

**Fix (use with caution):**
```bash
# Force unlock (only if you're sure no one else is running)
terraform force-unlock a1b2c3d4-e5f6-7890
```

---

## 7.4 Local State

By default, state is stored locally in `terraform.tfstate`:

```
project/
├── main.tf
├── terraform.tfstate          # Current state
└── terraform.tfstate.backup   # Previous state (auto-created)
```

### Problems with Local State

```
┌─────────────────────────────────────────────────────────┐
│                  LOCAL STATE PROBLEMS                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. No collaboration                                    │
│     → Only one person has the state file                │
│                                                         │
│  2. No locking                                          │
│     → Two people can run apply simultaneously           │
│     → State corruption                                  │
│                                                         │
│  3. No encryption at rest                               │
│     → Passwords stored in plaintext                     │
│                                                         │
│  4. No versioning                                       │
│     → Can't roll back to previous state                 │
│                                                         │
│  5. Risk of loss                                        │
│     → Laptop dies = state gone = orphaned resources     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Quick Fix: Move State to S3

To solve local state problems, configure a remote backend. Create a `backend.tf` file:

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "default/terraform.tfstate"   # path inside the bucket
    region = "ap-south-1"
  }
}
```

Then reinitialize:

```bash
terraform init
# Terraform will ask to migrate existing local state to S3
```

> See [Module 9](../module-09-remote-state-and-backends/README.md) for full remote backend setup including DynamoDB locking and encryption.

---

## 7.5 Drift Detection

Drift occurs when real infrastructure differs from state:

```bash
# Detect drift by refreshing state
terraform plan -refresh-only
```

**Output when drift is detected:**
```
Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform
since the last "terraform apply" command.

  # aws_instance.web has changed
  ~ resource "aws_instance" "web" {
        id            = "i-0abc123"
      ~ instance_type = "t2.micro" -> "t2.small"  # Changed outside TF!
      ~ tags          = {
          + "ManualTag" = "added-in-console"       # Added outside TF!
        }
    }

Would you like to update the Terraform state to reflect these detected changes?
```

```bash
# Accept the drift into state (don't change infrastructure)
terraform apply -refresh-only

# Or revert drift by applying your config
terraform apply  # Will change instance back to t2.micro
```

### What Happens When You Modify Resources via AWS Console

#### Case 1: Resource MODIFIED in Console (e.g., changed instance type)

```bash
# Someone changed instance type from t2.micro to t2.small in AWS Console
terraform plan
```

```
  # aws_instance.web will be updated in-place
  ~ resource "aws_instance" "web" {
      ~ instance_type = "t2.small" -> "t2.micro"  # Terraform reverts it!
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

**Impact:** `terraform apply` will **revert** the manual change back to what's in your `.tf` file.

#### Case 1b: Security Group Opened Manually (Real-Life Drift)

A common production scenario — someone opens a security group to `0.0.0.0/0` via the AWS Console for debugging and forgets to close it:

```hcl
# Your .tf file says SSH from internal only
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal only
  }
}
```

```bash
# Someone added 0.0.0.0/0 to port 22 in the AWS Console
terraform plan
```

```
  # aws_security_group.web will be updated in-place
  ~ resource "aws_security_group" "web" {
      ~ ingress {
          ~ cidr_blocks = [
              - "0.0.0.0/0",    # Terraform removes the open rule
                "10.0.0.0/8",
            ]
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

**Applying the fix:**

```bash
terraform apply
```

```
  # aws_security_group.web will be updated in-place
  ~ resource "aws_security_group" "web" {
      ~ ingress {
          ~ cidr_blocks = [
              - "0.0.0.0/0",
                "10.0.0.0/8",
            ]
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_security_group.web: Modifying... [id=sg-0abc123]
aws_security_group.web: Modifications complete after 2s [id=sg-0abc123]

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

**Impact:** `terraform apply` closes the security hole automatically. This is Terraform's self-healing behavior — code is the source of truth, and drift gets corrected on the next apply.

**What if you WANT to keep the manual change?**

```bash
# Option 1: Update your .tf file to match the manual change
# Edit the cidr_blocks to include "0.0.0.0/0"

# Option 2: Accept drift into state without changing infra
terraform apply -refresh-only
```

```
Would you like to update the Terraform state to reflect these detected changes?
  Enter a value: yes

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

> ⚠️ Set up automated drift detection (Module 16) so these changes are caught before the next manual apply.

#### Case 2: Resource DELETED in Console

```bash
# Someone terminated the EC2 instance in AWS Console
terraform plan
```

```
  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t2.micro"
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

**Impact:** Terraform detects the resource is gone and **recreates** it.

> ⚠️ **Data loss risk for stateful resources:** Recreation works fine for stateless resources (EC2, security groups, load balancers). But if someone deletes a **database** (RDS, DynamoDB), **S3 bucket with data**, or **EBS volume**, Terraform will recreate an empty resource — all data is lost unless backups exist.

**Protecting stateful resources:**

```hcl
resource "aws_db_instance" "production" {
  identifier     = "prod-db"
  engine         = "postgres"
  instance_class = "db.r5.large"
  allocated_storage = 100

  lifecycle {
    prevent_destroy = true   # terraform destroy will FAIL for this resource
  }
}
```

```bash
# If someone tries to destroy it:
terraform destroy -target=aws_db_instance.production
```

**Error (this is what you want):**
```
Error: Instance cannot be destroyed

  on main.tf line 1:
   1: resource "aws_db_instance" "production" {

Resource aws_db_instance.production has lifecycle.prevent_destroy set,
but the plan calls for this resource to be destroyed. To avoid this
error and destroy the resource, first set prevent_destroy = false in
your configuration.
```

**Best practice for all stateful resources:**

```hcl
# Always protect databases, storage, and data stores
resource "aws_db_instance" "main"    { lifecycle { prevent_destroy = true } }
resource "aws_s3_bucket" "data"      { lifecycle { prevent_destroy = true } }
resource "aws_dynamodb_table" "main" { lifecycle { prevent_destroy = true } }
resource "aws_ebs_volume" "data"     { lifecycle { prevent_destroy = true } }
```

#### Case 3: Resource ADDED in Console (not in Terraform)

```bash
# Someone created a new EC2 instance manually in AWS Console
terraform plan
```

```
No changes. Your infrastructure matches the configuration.
```

**Impact:** Terraform **ignores** it completely. The manually created resource is invisible to Terraform because it's not in the state file. It becomes an "orphaned" resource.

To bring it under Terraform management:
```bash
# Add a resource block to your .tf file, then import
terraform import aws_instance.manual_server i-0xyz789
```

### The terraform refresh Command

```bash
# Legacy command (deprecated in Terraform 0.15.4+)
terraform refresh
```

This updates the state file to match real infrastructure WITHOUT making any changes. It's equivalent to:

```bash
# Modern replacement (recommended)
terraform apply -refresh-only
```

**What refresh does:**
```
1. Queries every resource in state against the cloud API
2. Updates state file attributes to match reality
3. Does NOT change any infrastructure
4. Does NOT modify your .tf files
```

**When to use:**
- After someone made manual changes you want to accept
- Before running `plan` to ensure state is current
- To detect drift without making changes

```bash
# Skip refresh entirely (faster plans, but may miss drift)
terraform plan -refresh=false
```

---

## 7.6 State File Security

> ⚠️ **State files contain sensitive data** — database passwords, API keys, and private IPs are stored in plaintext in local state.

### What NOT to Do

```bash
# ❌ Never commit state to Git
git add terraform.tfstate    # NEVER DO THIS

# ❌ Never share state files via email/Slack
# ❌ Never store state on unencrypted storage
```

### .gitignore for State Files

```gitignore
# Always ignore state files
*.tfstate
*.tfstate.*
*.tfstate.backup

# Ignore .terraform directory
.terraform/

# Ignore tfvars with secrets
*.tfvars
!example.tfvars
```

---

## 7.7 State Disaster Scenarios and Recovery

### Scenario 1: State File is Lost

Your `terraform.tfstate` is deleted or the machine crashed.

```bash
# Step 1: Check if local backup exists
ls -la terraform.tfstate.backup

# Step 2a: Restore from local backup
cp terraform.tfstate.backup terraform.tfstate
terraform plan  # Verify

# Step 2b: If using S3 backend, restore from S3 versioning
aws s3api list-object-versions \
  --bucket my-state-bucket \
  --prefix path/terraform.tfstate \
  --query 'Versions[0:5].[VersionId,LastModified,Size]' \
  --output table

# Restore a specific version
aws s3api get-object \
  --bucket my-state-bucket \
  --key path/terraform.tfstate \
  --version-id "abc123" \
  terraform.tfstate

# Step 2c: If no backup exists — re-import everything
# Write resource blocks for each existing resource, then:
terraform import aws_vpc.main vpc-0abc123
terraform import aws_instance.web i-0abc123
terraform import aws_s3_bucket.data my-bucket
# Repeat for every resource...
terraform plan  # Should show zero changes when done
```

**Impact of lost state:**
```
terraform plan
# Terraform thinks NOTHING exists
# It will try to CREATE everything again
# This causes duplicate resources and errors like:
#   "BucketAlreadyOwnedByYou" or "InvalidGroup.Duplicate"
```

### Scenario 2: State File is Corrupted

State file has invalid JSON (manual edit gone wrong, partial write, disk error).

```bash
cat terraform.tfstate
# Output: unexpected end of JSON input / parse error
```

**Error:**
```
Error: Failed to load state: unexpected end of JSON input
```

**Recovery:**
```bash
# Option 1: Restore from backup
cp terraform.tfstate.backup terraform.tfstate

# Option 2: Pull from remote backend
terraform state pull > terraform.tfstate

# Option 3: If using S3, restore previous version (see Scenario 1)
```

### Scenario 3: State File Modified Mistakenly

Someone manually edited `terraform.tfstate` — changed a resource ID, deleted a resource entry, or modified an attribute.

```bash
# Symptom: terraform plan shows unexpected changes
terraform plan
```

**Possible outputs after manual state edit:**
```
# If resource ID was changed to a non-existent ID:
Error: error reading EC2 Instance (i-WRONG_ID): InvalidInstanceID.NotFound

# If a resource was deleted from state:
  + resource "aws_instance" "web" {  # Terraform wants to CREATE it again
      + ami = "ami-abc123"           # But it already exists in AWS!
    }

# If an attribute was changed:
  ~ resource "aws_instance" "web" {
      ~ instance_type = "t2.large" -> "t2.micro"  # Terraform sees a diff
    }
```

**Recovery:**
```bash
# Option 1: Refresh state from real infrastructure
terraform apply -refresh-only
# This queries AWS and updates state to match reality

# Option 2: Restore from backup
cp terraform.tfstate.backup terraform.tfstate

# Option 3: If a resource was removed from state, re-import it
terraform import aws_instance.web i-0abc123def456

# Option 4: If using remote backend, pull the last good state
terraform state pull > terraform.tfstate
```

> ⚠️ **Never manually edit `terraform.tfstate`**. Use `terraform state` commands instead.

### Scenario 4: State Lock Stuck (Process Crashed)

Someone ran `terraform apply`, the process crashed, and the lock wasn't released.

```
Error: Error acquiring the state lock

Lock Info:
  ID:        a1b2c3d4-e5f6-7890
  Path:      s3://bucket/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Created:   2024-01-15 10:30:00 UTC
```

**Recovery:**
```bash
# Step 1: Verify no one else is actually running Terraform
# Check the "Who" and "Created" fields

# Step 2: Force unlock
terraform force-unlock a1b2c3d4-e5f6-7890
```

**Expected Output:**
```
Terraform state has been successfully unlocked!
```

```bash
# Step 3: Check state integrity after the crash
terraform plan
# If the apply was partial, some resources may exist and others may not
# Fix with targeted applies or imports
```

### Scenario 5: Two People Run Apply Simultaneously (No Locking)

Without remote state locking, concurrent applies corrupt state:

```
Person A: terraform apply → creates instance i-111
Person B: terraform apply → creates instance i-222
                          → overwrites state with i-222
                          → i-111 is now orphaned (exists in AWS but not in state)
```

**Fix:** Always use remote backend with DynamoDB locking (see [Module 9](../module-09-remote-state-and-backends/README.md)).

---

## Exercises

### Exercise 7.1: Examine State
1. Create a simple EC2 instance
2. Run `terraform apply`
3. Examine `terraform.tfstate` — find the instance ID, IP, and tags
4. Modify the instance in AWS Console (add a tag)
5. Run `terraform plan` — observe the drift

### Exercise 7.2: State Backup
1. Apply a configuration
2. Note the `serial` number in state
3. Apply a change
4. Compare `terraform.tfstate` and `terraform.tfstate.backup`

### Exercise 7.3: Break and Fix State
1. Apply a configuration
2. Manually delete the state file
3. Run `terraform plan` — observe that Terraform wants to create everything
4. Restore from backup and verify

---

## Key Takeaways

- State maps configuration to real infrastructure
- Local state is fine for learning but unsuitable for teams
- State files contain sensitive data — never commit to Git
- State locking prevents concurrent modifications
- Use `terraform plan -refresh-only` to detect drift
- Always have a backup strategy for state files
- The `serial` field prevents state conflicts

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| State Overview | [developer.hashicorp.com/terraform/language/state](https://developer.hashicorp.com/terraform/language/state) |
| Purpose of State | [developer.hashicorp.com/terraform/language/state/purpose](https://developer.hashicorp.com/terraform/language/state/purpose) |
| State Locking | [developer.hashicorp.com/terraform/language/state/locking](https://developer.hashicorp.com/terraform/language/state/locking) |
| Sensitive Data in State | [developer.hashicorp.com/terraform/language/state/sensitive-data](https://developer.hashicorp.com/terraform/language/state/sensitive-data) |
| Remote State | [developer.hashicorp.com/terraform/language/state/remote](https://developer.hashicorp.com/terraform/language/state/remote) |
| `terraform refresh` | [developer.hashicorp.com/terraform/cli/commands/refresh](https://developer.hashicorp.com/terraform/cli/commands/refresh) |
| `terraform plan -refresh-only` | [developer.hashicorp.com/terraform/cli/commands/plan#planning-modes](https://developer.hashicorp.com/terraform/cli/commands/plan#planning-modes) |
| `terraform force-unlock` | [developer.hashicorp.com/terraform/cli/commands/force-unlock](https://developer.hashicorp.com/terraform/cli/commands/force-unlock) |
| Backend Configuration | [developer.hashicorp.com/terraform/language/backend](https://developer.hashicorp.com/terraform/language/backend) |

---

[← Previous Module](../module-06-variables-outputs-locals/README.md) | [Next Module: State Commands →](../module-08-state-commands-and-operations/README.md)
