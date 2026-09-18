# Module 18: Troubleshooting Guide

## Level: ALL LEVELS | Reference Material

---

## 18.1 Error Categories

```
┌─────────────────────────────────────────────────────────┐
│                  ERROR CATEGORIES                       │
├─────────────────────────────────────────────────────────┤
│  1. Syntax Errors        → terraform validate          │
│  2. Provider Errors       → credentials, versions      │
│  3. State Errors          → locking, corruption        │
│  4. Resource Errors       → API failures, limits       │
│  5. Dependency Errors     → circular, missing          │
│  6. Module Errors         → source, version, inputs    │
│  7. Performance Issues    → large state, slow plans    │
└─────────────────────────────────────────────────────────┘
```

---

## 18.2 Syntax and Validation Errors

### Missing Closing Brace

```
Error: Unclosed configuration block

  on main.tf line 1, in resource "aws_instance" "web":
   1: resource "aws_instance" "web" {

There is no closing brace for this block.
```

**Fix:** Add the missing `}`. Use an editor with bracket matching.

### Invalid Argument

```
Error: Unsupported argument

  on main.tf line 3, in resource "aws_instance" "web":
   3:   ami_id = "ami-abc123"

An argument named "ami_id" is not expected here. Did you mean "ami"?
```

**Fix:** Check the provider documentation for correct argument names.

### Invalid Reference

```
Error: Reference to undeclared resource

  on main.tf line 5:
   5:   subnet_id = aws_subnet.main.id

A managed resource "aws_subnet" "main" has not been declared.
Did you mean "aws_subnet.public"?
```

**Fix:** Verify the resource name matches exactly.

### Type Mismatch

```
Error: Incorrect attribute value type

  on main.tf line 3, in resource "aws_instance" "web":
   3:   count = "3"

Inappropriate value for attribute "count": a number is required.
```

**Fix:** Remove quotes — `count = 3` not `count = "3"`.

---

## 18.3 Provider and Authentication Errors

### No Credentials

```
Error: No valid credential sources found

  on main.tf line 1, in provider "aws":
   1: provider "aws" {

Please see https://registry.terraform.io/providers/hashicorp/aws
for more information about providing credentials.
```

**Fix:**
```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Option 2: AWS CLI profile
aws configure

# Option 3: Check ~/.aws/credentials exists
cat ~/.aws/credentials
```

### Expired Credentials

```
Error: error configuring Terraform AWS Provider: error validating
provider credentials: error calling sts:GetCallerIdentity:
ExpiredToken: The security token included in the request is expired
```

**Fix:**
```bash
# Refresh SSO credentials
aws sso login --profile my-profile

# Or refresh STS credentials
aws sts get-session-token
```

### Provider Version Conflict

```
Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/aws: no available releases match the given constraints
~> 3.0, ~> 5.0
```

**Fix:** Ensure all modules use compatible version constraints. Check with:
```bash
terraform providers
```

---

## 18.4 State Errors

### State Lock

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException
Lock Info:
  ID:        a1b2c3d4-e5f6-7890
  Path:      s3://bucket/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Created:   2024-01-15 10:30:00 UTC
```

**Diagnosis:**
```bash
# Check if someone else is running terraform
# Check the "Who" field in the error

# If the process crashed, force unlock
terraform force-unlock a1b2c3d4-e5f6-7890
```

### State Out of Sync

```
Error: Resource already exists

  aws_s3_bucket.data: Creating...

Error: error creating S3 Bucket (my-bucket): BucketAlreadyOwnedByYou:
Your previous request to create the named bucket succeeded and you
already own it.
```

**Fix:**
```bash
# Import the existing resource
terraform import aws_s3_bucket.data my-bucket
```

### Corrupt State

```
Error: Failed to load state: unexpected end of JSON input
```

**Fix:**
```bash
# Restore from backup
cp terraform.tfstate.backup terraform.tfstate

# Or pull from remote
terraform state pull > recovered.tfstate

# Or restore from S3 versioning
aws s3api list-object-versions \
  --bucket my-state-bucket \
  --prefix terraform.tfstate
```

---

## 18.5 Resource-Specific Errors

### Resource Limit Exceeded

```
Error: error creating VPC: VpcLimitExceeded: The maximum number of
VPCs has been reached.
```

**Fix:**
```bash
# Check current usage
aws ec2 describe-vpcs --query 'Vpcs | length(@)'

# Request limit increase via AWS Console → Service Quotas
```

### Dependency Violation

```
Error: error deleting Security Group (sg-abc123): DependencyViolation:
resource sg-abc123 has a dependent object
```

**Fix:** Terraform usually handles this, but if it doesn't:
```bash
# Find what's using the security group
aws ec2 describe-network-interfaces \
  --filters Name=group-id,Values=sg-abc123

# Remove the dependency first, then retry
terraform apply
```

### Timeout

```
Error: error waiting for RDS Cluster (my-cluster) to become available:
timeout while waiting for state to become 'available'
(last state: 'creating', timeout: 30m0s)
```

**Fix:** Increase the timeout:
```hcl
resource "aws_rds_cluster" "this" {
  # ...
  timeouts {
    create = "60m"
    delete = "60m"
  }
}
```

### Resource Not Found (After Manual Deletion)

```
Error: error reading EC2 Instance (i-abc123): InvalidInstanceID.NotFound:
The instance ID 'i-abc123' does not exist
```

**Fix:**
```bash
# Remove from state since it no longer exists
terraform state rm aws_instance.web

# Then re-plan
terraform plan
```

---

## 18.6 Dependency and Cycle Errors

### Circular Dependency

```
Error: Cycle: aws_security_group.a, aws_security_group.b
```

**Example of the problem:**
```hcl
# ❌ Circular reference
resource "aws_security_group" "a" {
  ingress {
    security_groups = [aws_security_group.b.id]
  }
}

resource "aws_security_group" "b" {
  ingress {
    security_groups = [aws_security_group.a.id]
  }
}
```

**Fix:** Use separate security group rules:
```hcl
# ✅ Break the cycle
resource "aws_security_group" "a" {
  name = "sg-a"
}

resource "aws_security_group" "b" {
  name = "sg-b"
}

resource "aws_security_group_rule" "a_from_b" {
  type                     = "ingress"
  security_group_id        = aws_security_group.a.id
  source_security_group_id = aws_security_group.b.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "b_from_a" {
  type                     = "ingress"
  security_group_id        = aws_security_group.b.id
  source_security_group_id = aws_security_group.a.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
}
```

---

## 18.7 Performance Issues

### Slow Plans with Large State

```bash
# Check state size
wc -c terraform.tfstate
# If > 10MB, consider splitting

# Use -target for quick iterations (not for production)
terraform plan -target=aws_instance.web

# Disable refresh for faster plans (may miss drift)
terraform plan -refresh=false

# Use -parallelism to control concurrency
terraform apply -parallelism=20  # Default is 10
```

### Splitting Large State

```
# Before: One monolithic state with 500+ resources
project/
└── main.tf  (everything)

# After: Split into focused projects
networking/     → VPC, subnets, routes (50 resources)
compute/        → EC2, ALB, ASG (100 resources)
database/       → RDS, ElastiCache (30 resources)
monitoring/     → CloudWatch, SNS (40 resources)
```

---

## 18.8 Debugging

### Enable Debug Logging

```bash
# Set log level
export TF_LOG=DEBUG    # Most verbose
export TF_LOG=TRACE    # Even more verbose
export TF_LOG=INFO     # Informational
export TF_LOG=WARN     # Warnings only
export TF_LOG=ERROR    # Errors only

# Log to file
export TF_LOG_PATH="terraform.log"

# Run terraform
terraform plan

# Disable logging
unset TF_LOG
unset TF_LOG_PATH
```

### Provider-Specific Debug Logging

```bash
# AWS provider debug
export TF_LOG=DEBUG
export TF_LOG_PROVIDER=DEBUG

# See exact API calls
export AWS_DEBUG=true
```

### Crash Logs

When Terraform crashes, it creates a `crash.log`:

```bash
# Check for crash logs
ls crash.log

# Report bugs with crash logs
# https://github.com/hashicorp/terraform/issues
```

---

## 18.9 Common Patterns That Cause Issues

### Pattern: count with Conditional

```hcl
# ❌ Problem: count can't use values that aren't known until apply
resource "aws_instance" "web" {
  count = length(data.aws_subnets.private.ids)  # OK if data source resolves
  # But NOT OK if it depends on a resource being created
}

# ✅ Fix: Use a variable instead
variable "instance_count" {
  default = 3
}

resource "aws_instance" "web" {
  count = var.instance_count
}
```

### Pattern: for_each with Unknown Values

```hcl
# ❌ Problem: for_each keys must be known at plan time
resource "aws_instance" "web" {
  for_each = toset(aws_subnet.private[*].id)
  # Fails if subnets don't exist yet
}

# ✅ Fix: Use a known set
resource "aws_instance" "web" {
  for_each = toset(var.availability_zones)
  subnet_id = aws_subnet.private[each.key].id
}
```

### Pattern: Sensitive Values in Output

```hcl
# ❌ Error
output "password" {
  value = aws_rds_cluster.this.master_password
}
# Error: Output refers to sensitive values

# ✅ Fix
output "password" {
  value     = aws_rds_cluster.this.master_password
  sensitive = true
}
```

---

## 18.10 Quick Reference: Error → Fix

| Error Message | Likely Cause | Fix |
|---|---|---|
| `No valid credential sources` | Missing AWS credentials | `aws configure` or set env vars |
| `Error acquiring the state lock` | Another process running | Wait or `force-unlock` |
| `Resource already exists` | Resource exists but not in state | `terraform import` |
| `Cycle detected` | Circular dependency | Use separate rule resources |
| `Unsupported argument` | Wrong argument name | Check provider docs |
| `Invalid count argument` | Count depends on unknown value | Use a variable |
| `Module not installed` | Missing `terraform init` | Run `terraform init` |
| `Backend initialization required` | Backend config changed | Run `terraform init` |
| `Provider not found` | Typo in provider name | Check `required_providers` |
| `Duplicate resource` | Same type+name used twice | Rename one resource |
| `value is sensitive` | Output needs `sensitive = true` | Add `sensitive = true` |
| `timeout waiting for state` | Resource creation too slow | Increase `timeouts` block |
| `AccessDenied` | IAM permissions missing | Add required IAM policy |
| `InvalidParameterValue` | Wrong value for cloud API | Check AWS docs for valid values |

---

## 18.11 Terraform Doctor Checklist

Run through this when things aren't working:

```bash
# 1. Check Terraform version
terraform version

# 2. Check provider versions
terraform providers

# 3. Validate configuration
terraform validate

# 4. Check formatting
terraform fmt -check -recursive

# 5. Reinitialize (fixes most "module not found" issues)
terraform init -upgrade

# 6. Check state health
terraform state list

# 7. Check for drift
terraform plan -refresh-only

# 8. Check AWS credentials
aws sts get-caller-identity

# 9. Check AWS permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/terraform \
  --action-names ec2:RunInstances

# 10. Enable debug logging if all else fails
export TF_LOG=DEBUG
terraform plan 2>&1 | tee debug.log
```

---

## Key Takeaways

- Most errors fall into predictable categories with known fixes
- `terraform validate` catches syntax errors without API calls
- State issues are the most dangerous — always backup before surgery
- Circular dependencies are solved by using separate rule resources
- Debug logging (`TF_LOG=DEBUG`) reveals the exact API calls being made
- When in doubt: `terraform init -upgrade` fixes many issues
- Keep the error → fix reference table handy

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Debugging Terraform | [developer.hashicorp.com/terraform/internals/debugging](https://developer.hashicorp.com/terraform/internals/debugging) |
| `TF_LOG` Environment Variable | [developer.hashicorp.com/terraform/internals/debugging#setting-tf_log](https://developer.hashicorp.com/terraform/internals/debugging#setting-tf_log) |
| `TF_LOG_PATH` | [developer.hashicorp.com/terraform/internals/debugging#setting-tf_log_path](https://developer.hashicorp.com/terraform/internals/debugging#setting-tf_log_path) |
| `terraform validate` | [developer.hashicorp.com/terraform/cli/commands/validate](https://developer.hashicorp.com/terraform/cli/commands/validate) |
| `terraform force-unlock` | [developer.hashicorp.com/terraform/cli/commands/force-unlock](https://developer.hashicorp.com/terraform/cli/commands/force-unlock) |
| `terraform plan -refresh-only` | [developer.hashicorp.com/terraform/cli/commands/plan#planning-modes](https://developer.hashicorp.com/terraform/cli/commands/plan#planning-modes) |
| `terraform apply -replace` | [developer.hashicorp.com/terraform/cli/commands/apply#replace](https://developer.hashicorp.com/terraform/cli/commands/apply#replace) |
| `terraform graph` | [developer.hashicorp.com/terraform/cli/commands/graph](https://developer.hashicorp.com/terraform/cli/commands/graph) |
| Crash Logs | [developer.hashicorp.com/terraform/internals/debugging#interpreting-a-crash-log](https://developer.hashicorp.com/terraform/internals/debugging#interpreting-a-crash-log) |
| Environment Variables | [developer.hashicorp.com/terraform/cli/config/environment-variables](https://developer.hashicorp.com/terraform/cli/config/environment-variables) |
| Resource Timeouts | [developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts](https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts) |
| Dependency Cycles | [developer.hashicorp.com/terraform/language/resources/behavior#resource-dependencies](https://developer.hashicorp.com/terraform/language/resources/behavior#resource-dependencies) |

---

[← Previous Module](../module-17-real-world-projects/README.md) | [Next Module: Expert-Level Topics →](../module-19-expert-level-topics/README.md)
