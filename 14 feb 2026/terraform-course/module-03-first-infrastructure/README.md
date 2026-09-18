# Module 3: Building Your First Infrastructure

## Level: BASIC | Estimated Time: 3 hours

---

## 3.1 Project Setup

Let's build real AWS infrastructure step by step.

```bash
mkdir first-infra && cd first-infra
```

### File Structure Convention

```
first-infra/
├── main.tf          # Primary resource definitions
├── variables.tf     # Input variable declarations
├── outputs.tf       # Output value declarations
├── providers.tf     # Provider configuration
├── terraform.tfvars # Variable values (don't commit secrets)
└── .gitignore       # Ignore state files and .terraform/
```

### .gitignore for Terraform Projects

```gitignore
# .gitignore
.terraform/
*.tfstate
*.tfstate.backup
*.tfvars
!example.tfvars
.terraform.lock.hcl
crash.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json
```

---

## 3.2 Step 1: Provider Configuration

```hcl
# providers.tf

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Project     = "first-infra"
      Environment = var.environment
    }
  }
}
```

### Understanding Version Constraints

```
"~> 5.0"    → >= 5.0, < 6.0     (recommended for providers)
"~> 5.31"   → >= 5.31, < 5.32   (patch-level pinning)
">= 5.0"    → any version 5.0+  (too loose for production)
"= 5.31.0"  → exactly 5.31.0    (too strict, blocks patches)
">= 5.0, < 6.0" → same as ~> 5.0 (explicit range)
```

### Running `terraform init`

```bash
terraform init
```

**Expected Output:**
```
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.31.0...
- Installed hashicorp/aws v5.31.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!
```

---

## 3.3 Step 2: Variables

```hcl
# variables.tf

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "my_ip" {
  description = "Your IP address for SSH access (CIDR notation)"
  type        = string
  default     = "0.0.0.0/0"  # Restrict this in production!
}
```

```hcl
# terraform.tfvars

aws_region  = "us-east-1"
environment = "dev"
my_ip       = "203.0.113.50/32"  # Replace with your actual IP
```

---

## 3.4 Step 3: VPC and Networking

```hcl
# main.tf

# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-vpc"
  }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment}-igw"
  }
}

# --- Public Subnet ---
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-subnet"
  }
}

# --- Route Table ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.environment}-public-rt"
  }
}

# --- Route Table Association ---
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

### What This Creates

```
┌─────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)            │
│                                                  │
│  ┌──────────────────────────────────────┐       │
│  │     Public Subnet (10.0.1.0/24)     │       │
│  │          us-east-1a                  │       │
│  │                                      │       │
│  │  ┌──────────┐                       │       │
│  │  │   EC2    │ (we'll add this next) │       │
│  │  └──────────┘                       │       │
│  └──────────────────────────────────────┘       │
│                    │                             │
│              ┌─────▼─────┐                      │
│              │Route Table│                      │
│              └─────┬─────┘                      │
│                    │                             │
│              ┌─────▼─────┐                      │
│              │    IGW    │                      │
│              └─────┬─────┘                      │
└────────────────────┼────────────────────────────┘
                     │
                 Internet
```

---

## 3.5 Step 4: Security Group

```hcl
# main.tf (continued)

# --- Security Group ---
resource "aws_security_group" "web" {
  name        = "${var.environment}-web-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # HTTP access
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-web-sg"
  }
}
```

---

## 3.6 Step 5: EC2 Instance

```hcl
# main.tf (continued)

# --- Find Latest Amazon Linux 2 AMI ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- EC2 Instance ---
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  # Option 1: Inline heredoc (simple scripts)
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    
    # Create a simple web page
    cat > /var/www/html/index.html <<'HTML'
    <!DOCTYPE html>
    <html>
    <head><title>Terraform Demo</title></head>
    <body>
      <h1>Hello from Terraform!</h1>
      <p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>
      <p>Availability Zone: $(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)</p>
    </body>
    </html>
    HTML
  EOF

  # Option 2: External script file (recommended for larger scripts)
  # user_data = file("${path.module}/scripts/app-install.sh")

  # Option 3: Template file with variables (best for dynamic config)
  # user_data = templatefile("${path.module}/scripts/app-install.tftpl", {
  #   app_port = 8080
  #   db_host  = "db.example.com"
  # })

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.environment}-web-server"
  }
}
```

---

## 3.7 Step 6: Outputs

```hcl
# outputs.tf

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Public IP of the web server"
  value       = aws_instance.web.public_ip
}

output "instance_public_dns" {
  description = "Public DNS of the web server"
  value       = aws_instance.web.public_dns
}

output "website_url" {
  description = "URL to access the web server"
  value       = "http://${aws_instance.web.public_ip}"
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.web.id
}

output "ami_id" {
  description = "AMI ID used for the instance"
  value       = data.aws_ami.amazon_linux.id
}
```

---

## 3.8 Running Terraform Commands

### Step 1: Format and Validate

```bash
terraform fmt
```

**Expected Output:**
```
main.tf
variables.tf
```
(Lists files that were reformatted)

```bash
terraform validate
```

**Expected Output:**
```
Success! The configuration is valid.
```

### Step 2: Plan

```bash
terraform plan
```

**Expected Output (abbreviated):**
```
Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                          = "ami-0c55b159cbfafe1f0"
      + arn                          = (known after apply)
      + associate_public_ip_address  = (known after apply)
      + availability_zone            = (known after apply)
      + cpu_core_count               = (known after apply)
      + get_password_data            = false
      + host_id                      = (known after apply)
      + id                           = (known after apply)
      + instance_state               = (known after apply)
      + instance_type                = "t2.micro"
      + ipv6_address_count           = (known after apply)
      + key_name                     = (known after apply)
      + monitoring                   = false
      + primary_network_interface_id = (known after apply)
      + private_dns                  = (known after apply)
      + private_ip                   = (known after apply)
      + public_dns                   = (known after apply)
      + public_ip                    = (known after apply)
      + secondary_private_ips        = (known after apply)
      + security_groups              = (known after apply)
      + subnet_id                    = (known after apply)
      + tags                         = {
          + "Name" = "dev-web-server"
        }
      + vpc_security_group_ids       = (known after apply)

      + root_block_device {
          + encrypted   = true
          + volume_size = 20
          + volume_type = "gp3"
        }
    }

  # aws_internet_gateway.main will be created
  + resource "aws_internet_gateway" "main" { ... }

  # aws_route_table.public will be created
  + resource "aws_route_table" "public" { ... }

  # aws_route_table_association.public will be created
  + resource "aws_route_table_association" "public" { ... }

  # aws_security_group.web will be created
  + resource "aws_security_group" "web" { ... }

  # aws_subnet.public will be created
  + resource "aws_subnet" "public" { ... }

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" { ... }

Plan: 7 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_id        = (known after apply)
  + instance_public_ip = (known after apply)
  + vpc_id             = (known after apply)
  + website_url        = (known after apply)
```

### Understanding Plan Symbols

```
+   create      → New resource will be created
-   destroy     → Existing resource will be destroyed
~   update      → Existing resource will be modified in-place
-/+ replace     → Resource will be destroyed and recreated
<=  read        → Data source will be read
```

### Saving a Plan File

```bash
# Save the plan to a file (recommended for production)
terraform plan -out=tfplan
```

This creates a binary file `tfplan` that captures exactly what will change. You can then apply it without re-prompting:

```bash
# Apply the saved plan (no confirmation prompt needed)
terraform apply tfplan
```

You can also create a destroy plan:

```bash
# Save a destroy plan
terraform plan -destroy -out=destroyplan

# Execute the destroy plan
terraform apply destroyplan
```

> Saving plans ensures you apply exactly what you reviewed — nothing more, nothing less.

### Step 3: Apply

```bash
# Option 1: Interactive (prompts for confirmation)
terraform apply

# Option 2: Apply a saved plan (no prompt)
terraform apply tfplan

# Option 3: Skip confirmation (use in CI/CD only)
terraform apply -auto-approve
```

**Interactive Prompt (Option 1):**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Expected Output:**
```
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 3s [id=vpc-0abc123def456]
aws_internet_gateway.main: Creating...
aws_subnet.public: Creating...
aws_security_group.web: Creating...
aws_internet_gateway.main: Creation complete after 1s [id=igw-0abc123]
aws_subnet.public: Creation complete after 1s [id=subnet-0abc123]
aws_security_group.web: Creation complete after 2s [id=sg-0abc123]
aws_route_table.public: Creating...
aws_instance.web: Creating...
aws_route_table.public: Creation complete after 1s [id=rtb-0abc123]
aws_route_table_association.public: Creating...
aws_route_table_association.public: Creation complete after 0s [id=rtbassoc-0abc123]
aws_instance.web: Still creating... [10s elapsed]
aws_instance.web: Still creating... [20s elapsed]
aws_instance.web: Creation complete after 23s [id=i-0abc123def456]

Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

instance_id        = "i-0abc123def456"
instance_public_ip = "54.123.45.67"
vpc_id             = "vpc-0abc123def456"
website_url        = "http://54.123.45.67"
```

### Step 4: Inspect with terraform show

```bash
# Show the current state of all resources (human-readable)
terraform show
```

**Expected Output (abbreviated):**
```
# aws_instance.web:
resource "aws_instance" "web" {
    ami                          = "ami-0c55b159cbfafe1f0"
    arn                          = "arn:aws:ec2:us-east-1:123456789012:instance/i-0abc123def456"
    instance_state               = "running"
    instance_type                = "t2.micro"
    private_ip                   = "10.0.1.50"
    public_ip                    = "54.123.45.67"
    subnet_id                    = "subnet-0abc123"
    tags                         = {
        "Name" = "dev-web-server"
    }
    vpc_security_group_ids       = [
        "sg-0abc123",
    ]
}

# aws_vpc.main:
resource "aws_vpc" "main" {
    cidr_block           = "10.0.0.0/16"
    id                   = "vpc-0abc123def456"
    enable_dns_hostnames = true
}

# ... (all other resources)
```

```bash
# Show a saved plan file
terraform show tfplan

# Show state as JSON (useful for scripting)
terraform show -json
```

### Step 5: Verify Outputs

```bash
# Check all outputs
terraform output

# Check specific output
terraform output instance_public_ip

# Get raw value (no quotes — useful in scripts)
terraform output -raw instance_public_ip

# Test the web server (wait ~1 minute for user_data to complete)
curl http://$(terraform output -raw instance_public_ip)
```

### Step 6: View State

```bash
# List all resources in state
terraform state list
```

**Expected Output:**
```
data.aws_ami.amazon_linux
aws_instance.web
aws_internet_gateway.main
aws_route_table.public
aws_route_table_association.public
aws_security_group.web
aws_subnet.public
aws_vpc.main
```

```bash
# Show details of a specific resource
terraform state show aws_instance.web
```

---

## 3.9 Making Changes

### Modify the Instance Type

Change `instance_type` in `terraform.tfvars`:

```hcl
instance_type = "t2.small"
```

```bash
terraform plan
```

**Expected Output:**
```
  # aws_instance.web must be replaced
-/+ resource "aws_instance" "web" {
      ~ instance_type = "t2.micro" -> "t2.small"  # forces replacement
        ...
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

> ⚠️ Some changes force resource replacement (destroy + recreate). The plan shows this with `-/+`.

### Add a Tag (In-Place Update)

```hcl
tags = {
  Name  = "${var.environment}-web-server"
  Owner = "devops-team"  # New tag
}
```

```bash
terraform plan
```

**Expected Output:**
```
  # aws_instance.web will be updated in-place
  ~ resource "aws_instance" "web" {
      ~ tags = {
          + "Owner" = "devops-team"
            # (1 unchanged element hidden)
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

---

## 3.10 Destroying Infrastructure

### Destroy a Specific Resource

```bash
# Destroy only the S3 bucket (leave everything else)
terraform destroy -target aws_s3_bucket.example
```

**Expected Output:**
```
  # aws_s3_bucket.example will be destroyed
  - resource "aws_s3_bucket" "example" {
      - bucket = "my-bucket-12345"
      - id     = "my-bucket-12345"
    }

Plan: 0 to add, 0 to change, 1 to destroy.
```

### Dependency Behavior with -target

```bash
# If you destroy a parent resource, dependent children are also destroyed
terraform destroy -target aws_instance.example
# → Also destroys aws_eip.ip (which depends on the instance)

# If you destroy only a child, the parent is NOT affected
terraform destroy -target aws_eip.ip
# → Only destroys the EIP, instance remains
```

### Destroy Everything

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all managed resources
terraform destroy
```

**Expected Output:**
```
  # aws_instance.web will be destroyed
  - resource "aws_instance" "web" { ... }
  
  # aws_security_group.web will be destroyed
  - resource "aws_security_group" "web" { ... }
  
  # ... (all resources listed)

Plan: 0 to add, 0 to change, 7 to destroy.

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

aws_route_table_association.public: Destroying... [id=rtbassoc-0abc123]
aws_instance.web: Destroying... [id=i-0abc123def456]
aws_route_table_association.public: Destruction complete after 0s
aws_route_table.public: Destroying... [id=rtb-0abc123]
aws_route_table.public: Destruction complete after 1s
aws_instance.web: Still destroying... [10s elapsed]
aws_instance.web: Destruction complete after 30s
aws_security_group.web: Destroying... [id=sg-0abc123]
aws_security_group.web: Destruction complete after 1s
aws_subnet.public: Destroying... [id=subnet-0abc123]
aws_subnet.public: Destruction complete after 1s
aws_internet_gateway.main: Destroying... [id=igw-0abc123]
aws_internet_gateway.main: Destruction complete after 1s
aws_vpc.main: Destroying... [id=vpc-0abc123def456]
aws_vpc.main: Destruction complete after 1s

Destroy complete! Resources: 7 destroyed.
```

> Notice the destroy order is the reverse of creation — Terraform respects dependencies.

---

## 3.11 Common Errors and Solutions

### Error: No Valid Credential Sources

```
Error: No valid credential sources found for AWS Provider.

  on providers.tf line 10, in provider "aws":
  10: provider "aws" {
```

**Fix:** Configure AWS credentials:
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

### Error: Insufficient Permissions

```
Error: creating EC2 Instance: UnauthorizedOperation: You are not authorized
to perform this operation.
```

**Fix:** Ensure your IAM user has the required permissions (see Module 1).

### Error: VPC Limit Exceeded

```
Error: creating VPC: VpcLimitExceeded: The maximum number of VPCs has been reached.
```

**Fix:** Delete unused VPCs or request a limit increase:
```bash
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Error: AMI Not Found

```
Error: creating EC2 Instance: InvalidAMIID.NotFound: The image id
'ami-0c55b159cbfafe1f0' does not exist
```

**Fix:** AMI IDs are region-specific. Use a data source instead of hardcoding:
```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
```

---

## 3.12 Real-Life Best Practices

| Practice | Why |
|----------|-----|
| Always run `terraform plan` before `apply` | Prevents surprises |
| Use `-auto-approve` only in CI/CD | Human review in development |
| Save plans: `terraform plan -out=tfplan` | Ensures you apply exactly what you reviewed |
| Use `terraform fmt` before commits | Consistent formatting |
| Tag everything | Cost tracking, ownership, cleanup |
| Use data sources for AMIs | AMI IDs change per region |
| Restrict security group CIDRs | Never use `0.0.0.0/0` for SSH in production |

---

## Exercises

### Exercise 3.1: Build and Destroy
Follow this module step by step. Build the infrastructure, verify it works, then destroy it.

### Exercise 3.2: Add a Second Subnet
Add a private subnet (`10.0.2.0/24`) in a different AZ. Create a NAT gateway for it.

### Exercise 3.3: Add an S3 Bucket
Add an S3 bucket resource with versioning enabled. Output the bucket name and ARN.

### Exercise 3.4: Modify and Observe
1. Change the instance type and run `plan` — observe the replacement
2. Add a tag and run `plan` — observe the in-place update
3. Change the VPC CIDR and run `plan` — observe the cascade of replacements

---

## Key Takeaways

- Organize code into `main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`
- Always use `terraform plan` before `apply` to preview changes
- Data sources let you reference existing resources without hardcoding IDs
- Some changes cause in-place updates, others force resource replacement
- `terraform destroy` removes resources in reverse dependency order
- Always use `.gitignore` to exclude state files and `.terraform/`

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Provider Configuration | [developer.hashicorp.com/terraform/language/providers/configuration](https://developer.hashicorp.com/terraform/language/providers/configuration) |
| AWS Provider — Getting Started | [registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration) |
| `terraform init` | [developer.hashicorp.com/terraform/cli/commands/init](https://developer.hashicorp.com/terraform/cli/commands/init) |
| `terraform plan` | [developer.hashicorp.com/terraform/cli/commands/plan](https://developer.hashicorp.com/terraform/cli/commands/plan) |
| `terraform apply` | [developer.hashicorp.com/terraform/cli/commands/apply](https://developer.hashicorp.com/terraform/cli/commands/apply) |
| `terraform destroy` | [developer.hashicorp.com/terraform/cli/commands/destroy](https://developer.hashicorp.com/terraform/cli/commands/destroy) |
| `terraform show` | [developer.hashicorp.com/terraform/cli/commands/show](https://developer.hashicorp.com/terraform/cli/commands/show) |
| `terraform output` | [developer.hashicorp.com/terraform/cli/commands/output](https://developer.hashicorp.com/terraform/cli/commands/output) |
| Output Values | [developer.hashicorp.com/terraform/language/values/outputs](https://developer.hashicorp.com/terraform/language/values/outputs) |
| Input Variables | [developer.hashicorp.com/terraform/language/values/variables](https://developer.hashicorp.com/terraform/language/values/variables) |
| `aws_vpc` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc) |
| `aws_subnet` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet) |
| `aws_internet_gateway` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/internet_gateway](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/internet_gateway) |
| `aws_security_group` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) |
| `aws_instance` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance) |

---

[← Previous Module](../module-02-hcl-syntax/README.md) | [Next Module: Providers Deep Dive →](../module-04-providers-deep-dive/README.md)
