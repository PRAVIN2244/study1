# Module 15: Testing and Validation

## Level: SUPER ADVANCED | Estimated Time: 3 hours

---

## 15.1 Testing Pyramid for Terraform

```
                    ┌─────────┐
                    │  E2E    │  terraform apply + verify + destroy
                   ┌┴─────────┴┐
                   │Integration │  terraform plan + validate
                  ┌┴───────────┴┐
                  │  Unit Tests  │  terraform validate + custom checks
                 ┌┴─────────────┴┐
                 │  Static Analysis│  tflint, checkov, tfsec
                ┌┴───────────────┴┐
                │   Formatting     │  terraform fmt -check
                └─────────────────┘
```

---

## 15.2 Built-in Validation

### Variable Validation

```hcl
variable "instance_type" {
  type = string

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "Instance type must be one of: t3.micro, t3.small, t3.medium, t3.large."
  }
}

variable "environment" {
  type = string

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cidr_block" {
  type = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }

  validation {
    condition     = tonumber(split("/", var.cidr_block)[1]) >= 16 && tonumber(split("/", var.cidr_block)[1]) <= 28
    error_message = "CIDR prefix must be between /16 and /28."
  }
}
```

### Preconditions and Postconditions

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  lifecycle {
    # Check BEFORE creating
    precondition {
      condition     = data.aws_ami.ubuntu.architecture == "x86_64"
      error_message = "AMI must be x86_64 architecture."
    }

    # Check AFTER creating
    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP address."
    }
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  lifecycle {
    postcondition {
      condition     = self.image_id != ""
      error_message = "No matching AMI found."
    }
  }
}

output "api_endpoint" {
  value = "https://${aws_lb.main.dns_name}/api"

  precondition {
    condition     = aws_lb.main.dns_name != ""
    error_message = "Load balancer must have a DNS name."
  }
}
```

---

## 15.3 terraform test (Native Testing Framework)

Available since Terraform 1.6+.

### Test File Structure

```
project/
├── main.tf
├── variables.tf
├── outputs.tf
└── tests/
    ├── basic.tftest.hcl
    ├── validation.tftest.hcl
    └── integration.tftest.hcl
```

### Basic Test

```hcl
# tests/basic.tftest.hcl

# Test that the plan succeeds with default values
run "plan_with_defaults" {
  command = plan

  assert {
    condition     = aws_instance.web.instance_type == "t3.micro"
    error_message = "Default instance type should be t3.micro"
  }

  assert {
    condition     = aws_instance.web.tags["Environment"] == "dev"
    error_message = "Default environment tag should be dev"
  }
}

# Test with custom variables
run "plan_with_prod_values" {
  command = plan

  variables {
    environment   = "prod"
    instance_type = "t3.large"
  }

  assert {
    condition     = aws_instance.web.instance_type == "t3.large"
    error_message = "Prod instance type should be t3.large"
  }
}
```

### Integration Test (Apply and Verify)

```hcl
# tests/integration.tftest.hcl

# This actually creates resources!
run "create_infrastructure" {
  command = apply

  variables {
    environment = "test"
    vpc_cidr    = "10.99.0.0/16"
  }

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC ID should not be empty"
  }

  assert {
    condition     = length(output.public_subnet_ids) == 2
    error_message = "Should create 2 public subnets"
  }

  assert {
    condition     = startswith(output.vpc_id, "vpc-")
    error_message = "VPC ID should start with vpc-"
  }
}

# Test that depends on the previous run
run "verify_instance" {
  command = apply

  variables {
    environment = "test"
  }

  assert {
    condition     = aws_instance.web.public_ip != ""
    error_message = "Instance should have a public IP"
  }
}
```

### Testing Modules

```hcl
# tests/module_test.tftest.hcl

# Test a module in isolation
run "test_vpc_module" {
  command = plan

  module {
    source = "./modules/vpc"
  }

  variables {
    vpc_name           = "test-vpc"
    vpc_cidr           = "10.0.0.0/16"
    availability_zones = ["us-east-1a", "us-east-1b"]
    enable_nat_gateway = false
  }

  assert {
    condition     = aws_vpc.this.cidr_block == "10.0.0.0/16"
    error_message = "VPC CIDR should match input"
  }

  assert {
    condition     = length(aws_subnet.public) == 2
    error_message = "Should create 2 public subnets"
  }

  assert {
    condition     = length(aws_nat_gateway.this) == 0
    error_message = "NAT gateway should not be created when disabled"
  }
}
```

### Running Tests

```bash
terraform test
```

**Output:**
```
tests/basic.tftest.hcl... in progress
  run "plan_with_defaults"... pass
  run "plan_with_prod_values"... pass
tests/basic.tftest.hcl... tearing down
tests/basic.tftest.hcl... pass

tests/integration.tftest.hcl... in progress
  run "create_infrastructure"... pass
  run "verify_instance"... pass
tests/integration.tftest.hcl... tearing down
tests/integration.tftest.hcl... pass

Success! 4 passed, 0 failed.
```

```bash
# Run specific test file
terraform test -filter=tests/basic.tftest.hcl

# Verbose output
terraform test -verbose
```

---

## 15.4 Static Analysis Tools

### tflint

```bash
# Install
curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

# Initialize (downloads plugins)
tflint --init

# Run
tflint
```

**Configuration (.tflint.hcl):**
```hcl
plugin "aws" {
  enabled = true
  version = "0.28.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "aws_instance_invalid_type" {
  enabled = true
}
```

**Output:**
```
3 issue(s) found:

Warning: "t1.micro" is an invalid value as instance_type (aws_instance_invalid_type)

  on main.tf line 5:
   5:   instance_type = "t1.micro"

Warning: variable "region" should include a description (terraform_documented_variables)

  on variables.tf line 1:
   1: variable "region" {

Warning: Missing version constraint for provider "aws" (terraform_required_providers)

  on main.tf line 1:
   1: resource "aws_instance" "web" {
```

### tfsec / trivy

```bash
# Install trivy (successor to tfsec)
brew install trivy

# Scan Terraform files
trivy config .
```

**Output:**
```
Results for main.tf:

CRITICAL: Security group rule allows ingress from 0.0.0.0/0 to port 22
══════════════════════════════════════════════════════════════════════
  SSH access should be restricted to specific IP ranges.

  See https://avd.aquasec.com/misconfig/avd-aws-0107

  main.tf:15-21
  ────────────────────────────────────────────────
   15 │   ingress {
   16 │     from_port   = 22
   17 │     to_port     = 22
   18 │     protocol    = "tcp"
   19 │     cidr_blocks = ["0.0.0.0/0"]  ← ISSUE
   20 │   }
  ────────────────────────────────────────────────

HIGH: S3 bucket does not have encryption enabled
══════════════════════════════════════════════════════════════════════
```

### Checkov — Static Analysis and Compliance Scanner

Checkov is an open-source static analysis tool by Bridgecrew (Palo Alto Networks) that scans Terraform code for security misconfigurations, compliance violations, and best-practice deviations — **without deploying anything**.

#### What Checkov Does

```
┌─────────────────────────────────────────────────────────────────┐
│                    Checkov Scan Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  .tf files ──▶ Parse HCL ──▶ Match against 1000+ rules ──▶     │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ PASSED   │  │ FAILED   │  │ SKIPPED  │  │ UNKNOWN  │       │
│  │ (secure) │  │ (fix it) │  │ (exempt) │  │ (review) │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                 │
│  Output: CLI, JSON, JUnit XML, SARIF, CSV, CycloneDX           │
└─────────────────────────────────────────────────────────────────┘
```

#### Installation

```bash
# Method 1: pip (most common)
pip install checkov

# Verify
checkov --version
```

**Output:**
```
checkov 3.2.x
```

```bash
# Method 2: Homebrew (macOS/Linux)
brew install checkov
```

```bash
# Method 3: Docker (no local install needed)
docker run --tty --volume $(pwd):/tf --workdir /tf bridgecrew/checkov -d .
```

```bash
# Method 4: Pre-commit hook (runs automatically on git commit)
# .pre-commit-config.yaml
```

```yaml
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: '3.2.0'
    hooks:
      - id: checkov
        args: ['--directory', '.']
```

```bash
pre-commit install
pre-commit run checkov --all-files
```

---

#### Running Checkov — Files, Folders, and Modules

**Scan a directory (most common):**

```bash
checkov -d .
```

**Scan a specific file:**

```bash
checkov -f main.tf
```

**Scan a module directory:**

```bash
checkov -d modules/vpc/
```

**Scan a Terraform plan (catches runtime values):**

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
checkov -f tfplan.json
```

**Scan with specific framework:**

```bash
checkov -d . --framework terraform
```

**Output in different formats:**

```bash
# JSON output (for CI/CD parsing)
checkov -d . -o json > checkov-results.json

# JUnit XML (for Jenkins/GitLab CI test reports)
checkov -d . -o junitxml > checkov-results.xml

# SARIF (for GitHub Security tab)
checkov -d . -o sarif > checkov-results.sarif

# CLI + JSON together
checkov -d . -o cli -o json --output-file-path console,checkov-results.json
```

---

#### Example: Scanning an Insecure S3 Bucket

**The Terraform code (main.tf):**

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data-bucket"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  # Missing: block_public_acls, block_public_policy, etc.
}
```

```bash
checkov -f main.tf
```

**Full Output:**

```
       _               _
   ___| |__   ___  ___| | _______   __
  / __| '_ \ / _ \/ __| |/ / _ \ \ / /
 | (__| | | |  __/ (__|   < (_) \ V /
  \___|_| |_|\___|\___|_|\_\___/ \_/

By Prisma Cloud | version: 3.2.x

terraform scan results:

Passed checks: 2, Failed checks: 5, Skipped checks: 0

Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
        FAILED for resource: aws_s3_bucket.data
        File: /main.tf:1-3
        Guide: https://docs.prismacloud.io/en/enterprise-edition/policy-reference/aws-policies/s3-policies/s3-13-enable-logging

                1 | resource "aws_s3_bucket" "data" {
                2 |   bucket = "my-app-data-bucket"
                3 | }

Check: CKV_AWS_145: "Ensure that S3 Bucket has server-side encryption enabled"
        FAILED for resource: aws_s3_bucket.data
        File: /main.tf:1-3
        Guide: https://docs.prismacloud.io/en/enterprise-edition/policy-reference/aws-policies/s3-policies/ensure-that-s3-bucket-has-server-side-encryption-enabled

Check: CKV_AWS_21: "Ensure all data stored in the S3 bucket have versioning enabled"
        FAILED for resource: aws_s3_bucket.data
        File: /main.tf:1-3

Check: CKV_AWS_144: "Ensure that S3 bucket has cross-region replication enabled"
        FAILED for resource: aws_s3_bucket.data
        File: /main.tf:1-3

Check: CKV2_AWS_6: "Ensure that S3 bucket has a Public Access block"
        FAILED for resource: aws_s3_bucket.data
        File: /main.tf:1-3
```

---

#### Understanding the Output

```
┌──────────────────────────────────────────────────────────────────┐
│                    Checkov Output Breakdown                       │
├──────────────┬───────────────────────────────────────────────────┤
│ Field        │ Meaning                                           │
├──────────────┼───────────────────────────────────────────────────┤
│ Check ID     │ CKV_AWS_18 — unique rule identifier               │
│ Description  │ Human-readable policy name                        │
│ PASSED       │ Resource complies with the rule                   │
│ FAILED       │ Resource violates the rule — needs fixing         │
│ SKIPPED      │ Rule was explicitly suppressed (see below)        │
│ Resource     │ The Terraform resource that was checked           │
│ File:Line    │ Exact file and line numbers of the violation      │
│ Guide        │ Link to detailed remediation documentation        │
└──────────────┴───────────────────────────────────────────────────┘
```

**Summary line explained:**

```
Passed checks: 12, Failed checks: 5, Skipped checks: 1
│                    │                    │
│                    │                    └── Rules you chose to ignore
│                    └── Security issues to fix
└── Resources that meet security standards
```

---

#### Compliance Benchmarks and Standards

Checkov maps its rules to industry compliance frameworks. Each CKV rule is tagged with one or more benchmarks:

```
┌──────────────────────┬──────────────────────────────────────────────────┐
│ Benchmark            │ Description                                      │
├──────────────────────┼──────────────────────────────────────────────────┤
│ CIS AWS 1.4 / 1.5    │ Center for Internet Security — AWS Foundations   │
│ CIS Azure 1.3        │ CIS Benchmark for Microsoft Azure                │
│ CIS GCP 1.2          │ CIS Benchmark for Google Cloud                   │
│ SOC 2                │ Service Organization Control — Type 2            │
│ HIPAA                │ Health Insurance Portability and Accountability   │
│ PCI-DSS              │ Payment Card Industry Data Security Standard     │
│ NIST 800-53          │ National Institute of Standards and Technology    │
│ ISO 27001            │ International information security standard      │
│ GDPR                 │ General Data Protection Regulation (EU)          │
│ AWS Well-Architected │ AWS best practices framework                     │
└──────────────────────┴──────────────────────────────────────────────────┘
```

**Scan for a specific benchmark:**

```bash
# Only check CIS AWS rules
checkov -d . --check CIS

# Only check PCI-DSS rules
checkov -d . --check PCI
```

---

#### Common CKV Rules for Terraform (AWS)

```
┌──────────────┬──────────────────────────────────────────────────┬──────────┐
│ CKV ID       │ Rule Description                                 │ Severity │
├──────────────┼──────────────────────────────────────────────────┼──────────┤
│              │ --- S3 ---                                       │          │
│ CKV_AWS_18   │ S3 bucket has access logging enabled             │ MEDIUM   │
│ CKV_AWS_19   │ S3 bucket has server-side encryption enabled     │ HIGH     │
│ CKV_AWS_21   │ S3 bucket has versioning enabled                 │ MEDIUM   │
│ CKV_AWS_145  │ S3 bucket uses KMS encryption                    │ HIGH     │
│ CKV_AWS_144  │ S3 bucket has cross-region replication            │ LOW      │
│ CKV2_AWS_6   │ S3 bucket has public access block                │ HIGH     │
│              │                                                  │          │
│              │ --- EC2 / Networking ---                          │          │
│ CKV_AWS_8    │ Launch config is not encrypted                   │ HIGH     │
│ CKV_AWS_23   │ Security group has description                   │ LOW      │
│ CKV_AWS_24   │ Security group allows ingress from 0.0.0.0/0:22 │ HIGH     │
│ CKV_AWS_25   │ Security group allows ingress from 0.0.0.0/0:3389│ HIGH    │
│ CKV_AWS_260  │ Security group allows ingress from 0.0.0.0/0     │ HIGH     │
│ CKV_AWS_88   │ EC2 instance has public IP                       │ MEDIUM   │
│              │                                                  │          │
│              │ --- RDS ---                                      │          │
│ CKV_AWS_16   │ RDS instance is encrypted                        │ HIGH     │
│ CKV_AWS_17   │ RDS instance has CloudWatch logging              │ MEDIUM   │
│ CKV_AWS_118  │ RDS instance has enhanced monitoring             │ LOW      │
│ CKV_AWS_157  │ RDS instance has multi-AZ enabled                │ MEDIUM   │
│ CKV_AWS_161  │ RDS instance has IAM authentication              │ MEDIUM   │
│              │                                                  │          │
│              │ --- IAM ---                                      │          │
│ CKV_AWS_40   │ IAM policy does not use wildcard (*)             │ HIGH     │
│ CKV_AWS_61   │ IAM role allows assume from *                    │ HIGH     │
│ CKV_AWS_273  │ IAM policy not attached to users directly        │ MEDIUM   │
│              │                                                  │          │
│              │ --- General ---                                  │          │
│ CKV_AWS_41   │ No hardcoded credentials in provider             │ CRITICAL │
│ CKV2_AWS_5   │ Security group is attached to a resource         │ LOW      │
│ CKV_AWS_126  │ EBS default encryption enabled                   │ MEDIUM   │
└──────────────┴──────────────────────────────────────────────────┴──────────┘
```

**Severity levels:**

```
┌──────────┬──────────────────────────────────────────────────────────┐
│ Severity │ Meaning                                                  │
├──────────┼──────────────────────────────────────────────────────────┤
│ CRITICAL │ Immediate security risk — hardcoded secrets, open admin  │
│ HIGH     │ Significant risk — unencrypted data, open SSH to world   │
│ MEDIUM   │ Moderate risk — missing logging, no versioning           │
│ LOW      │ Best practice — missing descriptions, no replication     │
└──────────┴──────────────────────────────────────────────────────────┘
```

**Filter by severity:**

```bash
# Only show HIGH and CRITICAL failures
checkov -d . --check-severity HIGH

# Fail CI only on CRITICAL
checkov -d . --hard-fail-on CRITICAL
```

---

#### Fixing Checkov Failures — Complete Examples

**Failure: CKV_AWS_24 — SSH open to the world**

```
Check: CKV_AWS_24: "Ensure no security group allows ingress from 0.0.0.0/0 to port 22"
        FAILED for resource: aws_security_group.web
        File: /main.tf:10-20
```

**Broken code:**

```hcl
# ❌ SSH open to the entire internet
resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # CKV_AWS_24 fails here
  }
}
```

**Fixed code:**

```hcl
# ✅ SSH restricted to internal network
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web server security group"  # Also fixes CKV_AWS_23

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]   # Internal only
  }
}
```

```bash
checkov -f main.tf --check CKV_AWS_24
```

**Output after fix:**
```
Check: CKV_AWS_24: "Ensure no security group allows ingress from 0.0.0.0/0 to port 22"
        PASSED for resource: aws_security_group.web
        File: /main.tf:1-12
```

---

**Failure: CKV_AWS_19 + CKV_AWS_21 + CKV_AWS_18 — Insecure S3 bucket**

```
Check: CKV_AWS_19: "Ensure all data stored in the S3 bucket is securely encrypted at rest"
        FAILED for resource: aws_s3_bucket.data
Check: CKV_AWS_21: "Ensure all data stored in the S3 bucket have versioning enabled"
        FAILED for resource: aws_s3_bucket.data
Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
        FAILED for resource: aws_s3_bucket.data
```

**Broken code:**

```hcl
# ❌ No encryption, no versioning, no logging
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data"
}
```

**Fixed code (all three CKVs resolved):**

```hcl
# ✅ Encrypted, versioned, logged, private
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data"
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"                    # Fixes CKV_AWS_21
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"           # Fixes CKV_AWS_19 + CKV_AWS_145
    }
  }
}

resource "aws_s3_bucket_logging" "data" {
  bucket        = aws_s3_bucket.data.id
  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "logs/"                   # Fixes CKV_AWS_18
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true            # Fixes CKV2_AWS_6
}
```

```bash
checkov -f main.tf
```

**Output after fix:**
```
Passed checks: 5, Failed checks: 0, Skipped checks: 0

Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
        PASSED for resource: aws_s3_bucket.data
Check: CKV_AWS_19: "Ensure all data stored in the S3 bucket is securely encrypted at rest"
        PASSED for resource: aws_s3_bucket.data
Check: CKV_AWS_21: "Ensure all data stored in the S3 bucket have versioning enabled"
        PASSED for resource: aws_s3_bucket.data
Check: CKV_AWS_145: "Ensure that S3 Bucket has server-side encryption enabled"
        PASSED for resource: aws_s3_bucket.data
Check: CKV2_AWS_6: "Ensure that S3 bucket has a Public Access block"
        PASSED for resource: aws_s3_bucket_public_access_block.data
```

---

**Failure: CKV_AWS_16 — Unencrypted RDS**

**Broken code:**

```hcl
# ❌ No encryption
resource "aws_db_instance" "main" {
  identifier     = "prod-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r5.large"
  allocated_storage = 100
  username       = "admin"
  password       = var.db_password
}
```

**Fixed code:**

```hcl
# ✅ Encrypted, multi-AZ, logging, IAM auth
resource "aws_db_instance" "main" {
  identifier     = "prod-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r5.large"
  allocated_storage = 100
  username       = "admin"
  password       = var.db_password

  storage_encrypted          = true                    # Fixes CKV_AWS_16
  multi_az                   = true                    # Fixes CKV_AWS_157
  iam_database_authentication_enabled = true           # Fixes CKV_AWS_161
  enabled_cloudwatch_logs_exports = ["postgresql"]     # Fixes CKV_AWS_17
  monitoring_interval        = 60                      # Fixes CKV_AWS_118
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn

  lifecycle {
    prevent_destroy = true
  }
}
```

---

#### Skipping Rules (When a Check Doesn't Apply)

**Method 1: Inline comment in HCL**

```hcl
resource "aws_s3_bucket" "public_website" {
  bucket = "my-public-website"

  #checkov:skip=CKV_AWS_19:This is a public static website, encryption not needed
  #checkov:skip=CKV2_AWS_6:Intentionally public for website hosting
}
```

```bash
checkov -f main.tf
```

**Output:**
```
Passed checks: 3, Failed checks: 0, Skipped checks: 2

Check: CKV_AWS_19: "Ensure all data stored in the S3 bucket is securely encrypted at rest"
        SKIPPED for resource: aws_s3_bucket.public_website
        Suppress comment: This is a public static website, encryption not needed

Check: CKV2_AWS_6: "Ensure that S3 bucket has a Public Access block"
        SKIPPED for resource: aws_s3_bucket.public_website
        Suppress comment: Intentionally public for website hosting
```

**Method 2: CLI flag (skip globally)**

```bash
# Skip specific checks
checkov -d . --skip-check CKV_AWS_144,CKV_AWS_18

# Run only specific checks
checkov -d . --check CKV_AWS_24,CKV_AWS_16,CKV_AWS_19
```

**Method 3: Configuration file (.checkov.yaml)**

```yaml
# .checkov.yaml — place in project root
directory:
  - .
framework:
  - terraform
skip-check:
  - CKV_AWS_144   # Cross-region replication — not needed for dev
  - CKV_AWS_118   # Enhanced monitoring — too expensive for dev
soft-fail-on:
  - LOW            # Don't fail CI on LOW severity
output:
  - cli
  - json
```

```bash
# Checkov automatically reads .checkov.yaml from the current directory
checkov
```

---

#### Checkov in CI/CD — GitHub Actions Example

```yaml
# .github/workflows/checkov.yml
name: Checkov Security Scan

on:
  pull_request:
    paths:
      - '**/*.tf'

jobs:
  checkov:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform
          soft_fail: false           # Fail the PR if checks fail
          output_format: sarif
          output_file_path: results.sarif
          skip_check: CKV_AWS_144   # Skip cross-region replication

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

**What happens on a PR with violations:**

```
Run bridgecrewio/checkov-action@v12
  ...
  Passed checks: 18, Failed checks: 2, Skipped checks: 1

  Check: CKV_AWS_24: "Ensure no security group allows ingress from 0.0.0.0/0 to port 22"
          FAILED for resource: aws_security_group.web
          File: /modules/compute/main.tf:15-25

  Check: CKV_AWS_16: "Ensure all RDS instances are encrypted"
          FAILED for resource: aws_db_instance.main
          File: /modules/database/main.tf:1-12

Error: Process completed with exit code 1.
```

The PR is blocked until the violations are fixed.

---

#### Checkov vs Other Security Scanners

```
┌──────────────────────┬──────────────┬──────────────┬──────────────┐
│                      │ checkov      │ tfsec/trivy  │ tflint       │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ Focus                │ Security +   │ Security     │ Linting +    │
│                      │ Compliance   │              │ Best practice│
│ Compliance frameworks│ CIS, SOC2,   │ Limited      │ None         │
│                      │ HIPAA, PCI,  │              │              │
│                      │ NIST, GDPR   │              │              │
│ Custom policies      │ Python, YAML │ Rego, YAML   │ Go plugins   │
│ Terraform plan scan  │ Yes          │ Yes          │ No           │
│ Module scanning      │ Yes          │ Yes          │ Yes          │
│ Fix suggestions      │ Guide links  │ AVD links    │ No           │
│ IDE integration      │ VS Code,     │ VS Code      │ VS Code      │
│                      │ JetBrains    │              │              │
│ CI/CD integration    │ GitHub, GL,  │ GitHub, GL   │ GitHub, GL   │
│                      │ Jenkins, BB  │              │              │
│ Output formats       │ CLI, JSON,   │ CLI, JSON,   │ CLI, JSON    │
│                      │ SARIF, JUnit,│ SARIF, JUnit │              │
│                      │ CSV, CycloneDX│             │              │
│ Rule count (AWS)     │ 400+         │ 300+         │ 50+          │
└──────────────────────┴──────────────┴──────────────┴──────────────┘
```

**Recommendation:** Use all three together for layered security:

```bash
# Layer 1: Linting (fast, catches typos and invalid types)
tflint --init && tflint

# Layer 2: Security scanning (catches misconfigurations)
checkov -d . --hard-fail-on HIGH

# Layer 3: Deep security scan (catches additional patterns)
trivy config .
```

---

### Terratest (Go-Based Integration Testing)

Terratest is a Go library for writing automated tests that deploy real infrastructure, validate it, then tear it down:

```bash
# Install Go (required)
# https://go.dev/dl/

# Initialize a Go test module
mkdir -p test && cd test
go mod init terraform-tests
go get github.com/gruntwork-io/terratest/modules/terraform
```

```go
// test/vpc_test.go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVpcModule(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        // Path to the Terraform code
        TerraformDir: "../modules/vpc",

        // Variables to pass
        Vars: map[string]interface{}{
            "vpc_name": "test-vpc",
            "vpc_cidr": "10.99.0.0/16",
        },

        // Disable color in output for CI
        NoColor: true,
    }

    // Clean up after test
    defer terraform.Destroy(t, terraformOptions)

    // Deploy infrastructure
    terraform.InitAndApply(t, terraformOptions)

    // Validate outputs
    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    assert.Contains(t, vpcId, "vpc-")

    publicSubnets := terraform.OutputList(t, terraformOptions, "public_subnet_ids")
    assert.Equal(t, 2, len(publicSubnets))
}
```

```bash
# Run the test
cd test
go test -v -timeout 30m
```

**Output:**
```
=== RUN   TestVpcModule
    TestVpcModule 2024-01-15T10:30:00Z command.go:53: Running command terraform with args [init]
    TestVpcModule 2024-01-15T10:30:05Z command.go:53: Running command terraform with args [apply -auto-approve]
    TestVpcModule 2024-01-15T10:31:20Z command.go:53: Apply complete! Resources: 8 added
    TestVpcModule 2024-01-15T10:31:20Z command.go:53: Running command terraform with args [output -json vpc_id]
    TestVpcModule 2024-01-15T10:31:25Z command.go:53: Running command terraform with args [destroy -auto-approve]
    TestVpcModule 2024-01-15T10:32:00Z command.go:53: Destroy complete! Resources: 8 destroyed
--- PASS: TestVpcModule (120.00s)
PASS
```

### Terratest vs terraform test

```
┌──────────────────────┬──────────────────────────┬──────────────────────────┐
│                      │  terraform test          │  Terratest               │
├──────────────────────┼──────────────────────────┼──────────────────────────┤
│ Language             │ HCL (.tftest.hcl)        │ Go                       │
│ Setup                │ None (built-in)          │ Go toolchain required    │
│ Real infra           │ Optional (plan or apply) │ Always (apply + destroy) │
│ Mock support         │ Yes (mock_provider)      │ No (real APIs only)      │
│ HTTP/API validation  │ Limited                  │ Full (Go HTTP client)    │
│ Best for             │ Unit/plan tests          │ Integration/E2E tests    │
│ Cleanup              │ Automatic                │ defer Destroy()          │
└──────────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## 15.5 Sentinel Policies (Terraform Cloud/Enterprise)

Sentinel is a policy-as-code framework for Terraform Cloud:

```python
# policy.sentinel

import "tfplan/v2" as tfplan

# Require all EC2 instances to use approved instance types
approved_types = ["t3.micro", "t3.small", "t3.medium"]

main = rule {
    all tfplan.resource_changes as _, rc {
        rc.type is "aws_instance" and
        rc.change.after.instance_type in approved_types
    }
}
```

```python
# cost-control.sentinel

import "tfplan/v2" as tfplan
import "decimal"

# Prevent creating expensive instance types
expensive_types = ["p3", "p4", "x1", "x2", "r5.24xlarge"]

deny_expensive_instances = rule {
    all tfplan.resource_changes as _, rc {
        rc.type is "aws_instance" implies
        not any expensive_types as prefix {
            rc.change.after.instance_type starts_with prefix
        }
    }
}

main = rule {
    deny_expensive_instances
}
```

---

## 15.6 OPA (Open Policy Agent) with Conftest

Alternative to Sentinel for open-source policy enforcement:

```bash
# Install conftest
brew install conftest

# Write policy
mkdir -p policy
```

```rego
# policy/main.rego
package main

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_instance"
    resource.change.after.instance_type == "t2.micro"
    msg := "t2.micro is deprecated, use t3.micro instead"
}

deny[msg] {
    resource := input.resource_changes[_]
    resource.type == "aws_security_group"
    ingress := resource.change.after.ingress[_]
    ingress.cidr_blocks[_] == "0.0.0.0/0"
    ingress.from_port == 22
    msg := "SSH must not be open to the world"
}

warn[msg] {
    resource := input.resource_changes[_]
    not resource.change.after.tags
    msg := sprintf("Resource %s has no tags", [resource.address])
}
```

```bash
# Generate plan JSON and test
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
conftest test tfplan.json
```

**Output:**
```
FAIL - tfplan.json - main - SSH must not be open to the world
WARN - tfplan.json - main - Resource aws_instance.web has no tags

2 tests, 0 passed, 1 warning, 1 failure
```

---

## 15.7 Testing Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Pre-commit  │────▶│   CI/CD      │────▶│  Deployment  │
│              │     │              │     │              │
│ terraform fmt│     │ terraform    │     │ terraform    │
│ tflint       │     │   test       │     │   apply      │
│ trivy/tfsec  │     │ conftest     │     │              │
│ validate     │     │ plan review  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_trivy
      - id: terraform_docs
```

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Exercises

### Exercise 15.1: Variable Validation
Add validation rules to ensure:
1. VPC CIDR is a valid /16 network
2. Instance type is from an approved list
3. Environment name matches a pattern
4. Port numbers are in valid range

### Exercise 15.2: terraform test
Write tests for a VPC module that verify:
1. Correct number of subnets created
2. CIDR blocks match inputs
3. NAT gateway is conditional
4. Tags are applied correctly

### Exercise 15.3: Static Analysis
1. Install tflint and trivy
2. Run them against your project
3. Fix all findings
4. Add them to a pre-commit hook

### Exercise 15.4: Policy as Code
Write OPA/Conftest policies that:
1. Enforce tagging standards
2. Restrict instance types
3. Require encryption on S3 buckets
4. Block public security group rules

---

## Key Takeaways

- Use variable validation for input constraints
- Preconditions check assumptions before resource creation
- Postconditions verify resource state after creation
- `terraform test` (1.6+) provides native testing with plan and apply modes
- tflint catches provider-specific issues; trivy/tfsec find security problems
- Sentinel (Terraform Cloud) and OPA/Conftest (open source) enforce policies
- Layer your testing: format → lint → validate → test → policy → apply

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| `terraform test` | [developer.hashicorp.com/terraform/language/tests](https://developer.hashicorp.com/terraform/language/tests) |
| Test File Syntax (`.tftest.hcl`) | [developer.hashicorp.com/terraform/language/tests#syntax](https://developer.hashicorp.com/terraform/language/tests#syntax) |
| Mock Providers in Tests | [developer.hashicorp.com/terraform/language/tests/mocking](https://developer.hashicorp.com/terraform/language/tests/mocking) |
| Variable Validation | [developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) |
| Preconditions and Postconditions | [developer.hashicorp.com/terraform/language/expressions/custom-conditions](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions) |
| Check Blocks | [developer.hashicorp.com/terraform/language/checks](https://developer.hashicorp.com/terraform/language/checks) |
| `terraform validate` | [developer.hashicorp.com/terraform/cli/commands/validate](https://developer.hashicorp.com/terraform/cli/commands/validate) |
| `terraform fmt` | [developer.hashicorp.com/terraform/cli/commands/fmt](https://developer.hashicorp.com/terraform/cli/commands/fmt) |
| Sentinel Policy-as-Code | [developer.hashicorp.com/sentinel](https://developer.hashicorp.com/sentinel) |
| Sentinel in Terraform Cloud | [developer.hashicorp.com/terraform/cloud-docs/policy-enforcement](https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement) |
| tflint | [github.com/terraform-linters/tflint](https://github.com/terraform-linters/tflint) |
| tflint AWS Ruleset | [github.com/terraform-linters/tflint-ruleset-aws](https://github.com/terraform-linters/tflint-ruleset-aws) |
| trivy (Security Scanner) | [aquasecurity.github.io/trivy/latest/docs/scanner/misconfiguration/terraform/](https://aquasecurity.github.io/trivy/latest/docs/scanner/misconfiguration/terraform/) |
| tfsec (Now Part of trivy) | [github.com/aquasecurity/tfsec](https://github.com/aquasecurity/tfsec) |
| checkov | [www.checkov.io/1.Welcome/Quick%20Start.html](https://www.checkov.io/1.Welcome/Quick%20Start.html) |
| Terratest | [terratest.gruntwork.io/docs/](https://terratest.gruntwork.io/docs/) |
| OPA (Open Policy Agent) | [www.openpolicyagent.org/docs/latest/](https://www.openpolicyagent.org/docs/latest/) |
| Conftest | [www.conftest.dev/](https://www.conftest.dev/) |

---

[← Previous Module](../module-14-custom-providers-and-plugins/README.md) | [Next Module: CI/CD and Automation →](../module-16-cicd-and-automation/README.md)
