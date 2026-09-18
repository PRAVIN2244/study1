# Module 2: HCL Syntax Deep Dive

## Level: BASIC | Estimated Time: 3 hours

---

## 2.1 What is HCL?

**HashiCorp Configuration Language (HCL)** is the language used to write Terraform configurations. It's designed to be both human-readable and machine-parseable.

```hcl
# This is HCL - HashiCorp Configuration Language
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "HelloWorld"
  }
}
```

### HCL vs JSON

Terraform also accepts JSON, but HCL is preferred:

```
┌─────────────────────────────────┬──────────────────────────────────┐
│            HCL                  │             JSON                 │
├─────────────────────────────────┼──────────────────────────────────┤
│ resource "aws_instance" "web" { │ {                                │
│   ami           = "ami-abc123"  │   "resource": {                  │
│   instance_type = "t2.micro"   │     "aws_instance": {            │
│ }                               │       "web": {                   │
│                                 │         "ami": "ami-abc123",     │
│                                 │         "instance_type":"t2.micro│
│                                 │       }                          │
│                                 │     }                            │
│                                 │   }                              │
│                                 │ }                                │
└─────────────────────────────────┴──────────────────────────────────┘
```

---

## 2.2 How Terraform Processes Multiple .tf Files

Terraform does NOT process files one at a time. It **merges all `.tf` files** in the current directory into a single configuration before doing anything.

```
project/
├── providers.tf      ─┐
├── variables.tf       │  Terraform merges ALL of these
├── main.tf            │  into ONE configuration
├── outputs.tf        ─┘
└── terraform.tfvars     (variable values, loaded separately)
```

### What Happens When You Run `terraform apply` with 4 .tf Files

```
Step 1: Terraform finds ALL files ending in .tf in the current directory
Step 2: It merges them into a single configuration (order doesn't matter)
Step 3: terraform init   → downloads providers/modules
Step 4: terraform plan   → refreshes state, compares desired vs actual
Step 5: terraform apply  → shows plan, asks confirmation, applies changes
```

### Key Rules

```
┌──────────────────────────────────────────────────────────────────┐
│  Rule                              │  Example                   │
├──────────────────────────────────────────────────────────────────┤
│  File names don't matter           │  abc.tf works same as      │
│                                    │  main.tf                   │
│                                    │                            │
│  File order doesn't matter         │  Terraform builds a        │
│                                    │  dependency graph, not     │
│                                    │  sequential execution      │
│                                    │                            │
│  Resource names must be unique     │  Can't have two            │
│  across ALL files                  │  aws_instance "web"        │
│                                    │                            │
│  Only .tf files are processed      │  .tf.bak, .txt are ignored │
│                                    │                            │
│  Subdirectories are NOT included   │  Only current directory    │
│  (unless called as modules)        │                            │
└──────────────────────────────────────────────────────────────────┘
```

### Example: 4 Files, 1 Configuration

```hcl
# providers.tf
provider "aws" {
  region = "ap-south-1"
}
```

```hcl
# variables.tf
variable "instance_type" {
  default = "t2.micro"
}
```

```hcl
# main.tf
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type
}
```

```hcl
# outputs.tf
output "instance_id" {
  value = aws_instance.web.id
}
```

```bash
terraform apply
```

Terraform merges all 4 files and treats them as if they were one file. The result is identical to writing everything in a single `main.tf`.

---

## 2.3 Blocks

Blocks are the fundamental building unit of HCL. Every Terraform configuration is made of blocks.

### Block Syntax

```hcl
block_type "label_1" "label_2" {
  argument_name = "argument_value"

  nested_block {
    nested_argument = "value"
  }
}
```

### Common Block Types

```hcl
# 1. Terraform Settings Block - configures Terraform itself
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# 2. Provider Block - configures the cloud provider
provider "aws" {
  region = "us-east-1"
}

# 3. Resource Block - defines infrastructure objects
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# 4. Data Block - reads existing infrastructure
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
}

# 5. Variable Block - defines input parameters
variable "instance_type" {
  type    = string
  default = "t2.micro"
}

# 6. Output Block - exposes values after apply
output "vpc_id" {
  value = aws_vpc.main.id
}

# 7. Locals Block - defines local computed values
locals {
  common_tags = {
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# 8. Module Block - includes reusable configurations
module "vpc" {
  source = "./modules/vpc"
  cidr   = "10.0.0.0/16"
}
```

---

## 2.4 Arguments and Attributes

### Arguments (Input)

Arguments are values you SET in a block:

```hcl
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"   # argument
  instance_type = "t2.micro"                 # argument
  
  tags = {                                    # argument (map type)
    Name = "example"
  }
}
```

### Attributes (Output)

Attributes are values you READ from a resource after creation:

```hcl
# After aws_instance.example is created, you can reference:
# aws_instance.example.id              → "i-0abc123def456"
# aws_instance.example.public_ip       → "54.123.45.67"
# aws_instance.example.private_ip      → "10.0.1.50"
# aws_instance.example.arn             → "arn:aws:ec2:..."
```

### Using Attributes in Other Resources

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.public.id  # Reference another resource's attribute
}

resource "aws_eip" "web_ip" {
  instance = aws_instance.web.id  # Reference the instance's ID attribute
}
```

---

## 2.5 Data Types

### Primitive Types

```hcl
# String
variable "name" {
  type    = string
  default = "my-server"
}

# Number
variable "port" {
  type    = number
  default = 8080
}

# Boolean
variable "enable_monitoring" {
  type    = bool
  default = true
}
```

### Complex Types - Collections

```hcl
# List - ordered collection of same type
variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
# Access: var.availability_zones[0] → "us-east-1a"

# Set - unordered collection of unique values
variable "allowed_ports" {
  type    = set(number)
  default = [80, 443, 8080]
}

# Map - key-value pairs
variable "instance_types" {
  type = map(string)
  default = {
    dev     = "t2.micro"
    staging = "t2.medium"
    prod    = "t2.large"
  }
}
# Access: var.instance_types["dev"] → "t2.micro"

# Tuple - fixed-length collection with specific types per element
variable "mixed_data" {
  type    = tuple([string, number, bool])
  default = ["hello", 42, true]
}
```

### Complex Types - Structural

```hcl
# Object - named attributes with specific types
variable "server_config" {
  type = object({
    name          = string
    instance_type = string
    disk_size     = number
    monitoring    = bool
    tags          = map(string)
  })
  default = {
    name          = "web-server"
    instance_type = "t2.micro"
    disk_size     = 20
    monitoring    = true
    tags = {
      Environment = "dev"
    }
  }
}
# Access: var.server_config.name → "web-server"

# List of Objects
variable "subnets" {
  type = list(object({
    cidr = string
    az   = string
    public = bool
  }))
  default = [
    { cidr = "10.0.1.0/24", az = "us-east-1a", public = true },
    { cidr = "10.0.2.0/24", az = "us-east-1b", public = false },
  ]
}
```

---

## 2.6 Operators and Expressions

### Arithmetic Operators

```hcl
locals {
  total_storage = 50 * 3        # 150
  per_instance  = 1000 / 4      # 250
  remainder     = 10 % 3        # 1
  combined      = 10 + 20       # 30
  difference    = 100 - 25      # 75
}
```

### Comparison Operators

```hcl
locals {
  is_prod       = var.environment == "production"   # true/false
  not_dev       = var.environment != "dev"           # true/false
  needs_scaling = var.instance_count > 5             # true/false
  within_limit  = var.disk_size <= 100               # true/false
}
```

### Logical Operators

```hcl
locals {
  enable_ha = var.environment == "prod" && var.multi_az    # AND
  use_spot  = var.environment == "dev" || var.cost_saving  # OR
  skip_test = !var.run_tests                                # NOT
}
```

### Conditional Expression (Ternary)

```hcl
resource "aws_instance" "web" {
  # condition ? true_value : false_value
  instance_type = var.environment == "prod" ? "t2.large" : "t2.micro"
  
  # Nested conditional
  monitoring = var.environment == "prod" ? true : var.environment == "staging" ? true : false
}
```

---

## 2.7 String Interpolation and Templates

### Basic Interpolation

```hcl
locals {
  bucket_name = "app-${var.environment}-${var.region}"
  # Result: "app-dev-us-east-1"
}

resource "aws_instance" "web" {
  tags = {
    Name = "${var.project}-${var.environment}-web-server"
    # Result: "myapp-dev-web-server"
  }
}
```

### Heredoc Syntax

```hcl
# Standard heredoc
resource "aws_iam_policy" "example" {
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${var.bucket_name}/*"
    }
  ]
}
EOF
}

# Indented heredoc (<<- strips leading whitespace)
resource "aws_instance" "web" {
  user_data = <<-SCRIPT
    #!/bin/bash
    yum update -y
    yum install -y httpd
    echo "Hello from ${var.environment}" > /var/www/html/index.html
    systemctl start httpd
    systemctl enable httpd
  SCRIPT
}
```

### Directive Templates

```hcl
# For loop in templates
locals {
  hosts_entries = <<-EOT
    %{ for ip in var.server_ips ~}
    ${ip} server-${index(var.server_ips, ip)}.example.com
    %{ endfor ~}
  EOT
}

# Conditional in templates
locals {
  greeting = <<-EOT
    %{ if var.environment == "prod" ~}
    WARNING: This is PRODUCTION
    %{ else ~}
    This is ${var.environment}
    %{ endif ~}
  EOT
}
```

---

## 2.8 Comments

```hcl
# Single-line comment (preferred style)

// Single-line comment (also valid, less common)

/*
  Multi-line comment
  Used for longer explanations
  or temporarily disabling blocks
*/

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  # key_name    = "my-key"  # Commented out - not needed for this example
}
```

---

## 2.9 References and Dependencies

### Implicit Dependencies

Terraform automatically detects dependencies through references:

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Terraform knows this depends on aws_vpc.main because of the reference
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id    # ← implicit dependency
  cidr_block = "10.0.1.0/24"
}

# Terraform knows this depends on aws_subnet.public
resource "aws_instance" "web" {
  subnet_id = aws_subnet.public.id  # ← implicit dependency
  ami       = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}
```

**Dependency Graph:**
```
aws_vpc.main
      │
      ▼
aws_subnet.public
      │
      ▼
aws_instance.web
```

### Explicit Dependencies

When there's no attribute reference but a dependency exists:

```hcl
resource "aws_s3_bucket" "logs" {
  bucket = "my-app-logs"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # No direct reference to the bucket, but the app needs it to exist
  depends_on = [aws_s3_bucket.logs]
}
```

---

## 2.10 Meta-Arguments

Meta-arguments work with any resource type:

```hcl
resource "aws_instance" "web" {
  # Regular arguments
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # Meta-arguments
  count      = 3                          # Create 3 instances
  depends_on = [aws_subnet.public]        # Explicit dependency
  provider   = aws.west                   # Use specific provider config
  
  lifecycle {
    create_before_destroy = true          # Create new before destroying old
    prevent_destroy       = true          # Prevent accidental deletion
    ignore_changes        = [tags]        # Ignore external tag changes
  }
}
```

---

## 2.11 Complete Example with All Concepts

```hcl
# examples/complete.tf

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
  region = var.region
}

# --- Variables ---
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_config" {
  type = map(object({
    instance_type = string
    disk_size     = number
  }))
  default = {
    dev     = { instance_type = "t2.micro",  disk_size = 20 }
    staging = { instance_type = "t2.medium", disk_size = 50 }
    prod    = { instance_type = "t2.large",  disk_size = 100 }
  }
}

# --- Locals ---
locals {
  config = var.instance_config[var.environment]
  
  common_tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "hcl-demo"
  }
  
  name_prefix = "hcl-demo-${var.environment}"
}

# --- Data Source ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# --- Resources ---
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = local.config.instance_type

  root_block_device {
    volume_size = local.config.disk_size
    volume_type = "gp3"
  }

  user_data = <<-SCRIPT
    #!/bin/bash
    echo "Environment: ${var.environment}" > /tmp/env.txt
    %{ if var.environment == "prod" ~}
    echo "Production mode enabled" >> /tmp/env.txt
    %{ endif ~}
  SCRIPT

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web"
  })
}

# --- Outputs ---
output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_info" {
  description = "Instance details"
  value = {
    id            = aws_instance.web.id
    public_ip     = aws_instance.web.public_ip
    instance_type = aws_instance.web.instance_type
    ami           = aws_instance.web.ami
  }
}
```

---

## 2.12 Common Syntax Errors and How to Fix Them

### Error 1: Missing Closing Brace

```hcl
# ❌ WRONG
resource "aws_instance" "web" {
  ami = "ami-abc123"
  instance_type = "t2.micro"
# Missing closing brace
```

**Error Output:**
```
Error: Unclosed configuration block

  on main.tf line 1, in resource "aws_instance" "web":
   1: resource "aws_instance" "web" {

There is no closing brace for this block before the end of the file.
```

### Error 2: Wrong Attribute Type

```hcl
# ❌ WRONG - port should be a number, not a string
resource "aws_security_group_rule" "web" {
  from_port = "80"  # This might work due to auto-conversion
  to_port   = "eighty"  # This will fail
}
```

**Error Output:**
```
Error: Invalid value for "to_port"

  on main.tf line 3:
   3:   to_port = "eighty"

A number is required.
```

### Error 3: Invalid Reference

```hcl
# ❌ WRONG - typo in resource name
resource "aws_instance" "web_server" {
  ami = "ami-abc123"
}

output "id" {
  value = aws_instance.web.id  # Should be web_server, not web
}
```

**Error Output:**
```
Error: Reference to undeclared resource

  on main.tf line 6, in output "id":
   6:   value = aws_instance.web.id

A managed resource "aws_instance" "web" has not been declared in the root module.
Did you mean "aws_instance.web_server"?
```

### Error 4: Duplicate Resource Names

```hcl
# ❌ WRONG - duplicate names
resource "aws_instance" "web" {
  ami = "ami-abc123"
  instance_type = "t2.micro"
}

resource "aws_instance" "web" {  # Same name!
  ami = "ami-def456"
  instance_type = "t2.small"
}
```

**Error Output:**
```
Error: Duplicate resource "aws_instance" "web" configuration

  on main.tf line 6:
   6: resource "aws_instance" "web" {

A aws_instance resource named "web" was already declared at main.tf:1,1-31.
Resource names must be unique per type in each module.
```

---

## Exercises

### Exercise 2.1: Type Practice
Create a `variables.tf` file with variables of every type (string, number, bool, list, map, object). Use them in a `main.tf` with local values.

### Exercise 2.2: String Interpolation
Create a configuration that generates resource names using interpolation:
- Pattern: `{project}-{environment}-{resource_type}-{index}`
- Example: `myapp-prod-web-001`

### Exercise 2.3: Fix the Errors
```hcl
# Fix all errors in this configuration
resorce "aws_instance" "web" {
  ami = ami-0c55b159cbfafe1f0
  instance_type = t2.micro
  tags {
    Name = "web"
  }

output "id" {
  value = aws_instance.web.id
```

<details>
<summary>Solution</summary>

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  tags = {
    Name = "web"
  }
}

output "id" {
  value = aws_instance.web.id
}
```
</details>

---

## Key Takeaways

- HCL uses blocks, arguments, and expressions to define infrastructure
- Terraform supports primitive types (string, number, bool) and complex types (list, map, object, tuple, set)
- String interpolation uses `${}` syntax inside double-quoted strings
- Dependencies can be implicit (through references) or explicit (`depends_on`)
- `terraform fmt` auto-formats your code — use it before every commit
- `terraform validate` catches syntax errors without making API calls

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| HCL Native Syntax | [developer.hashicorp.com/terraform/language/syntax/configuration](https://developer.hashicorp.com/terraform/language/syntax/configuration) |
| JSON Syntax (alternative) | [developer.hashicorp.com/terraform/language/syntax/json](https://developer.hashicorp.com/terraform/language/syntax/json) |
| Files and Directories | [developer.hashicorp.com/terraform/language/files](https://developer.hashicorp.com/terraform/language/files) |
| Override Files | [developer.hashicorp.com/terraform/language/files/override](https://developer.hashicorp.com/terraform/language/files/override) |
| Types and Values | [developer.hashicorp.com/terraform/language/expressions/types](https://developer.hashicorp.com/terraform/language/expressions/types) |
| Strings and Templates | [developer.hashicorp.com/terraform/language/expressions/strings](https://developer.hashicorp.com/terraform/language/expressions/strings) |
| Operators | [developer.hashicorp.com/terraform/language/expressions](https://developer.hashicorp.com/terraform/language/expressions) |
| References to Values | [developer.hashicorp.com/terraform/language/expressions/references](https://developer.hashicorp.com/terraform/language/expressions/references) |
| Resource Blocks | [developer.hashicorp.com/terraform/language/resources/syntax](https://developer.hashicorp.com/terraform/language/resources/syntax) |
| `terraform validate` | [developer.hashicorp.com/terraform/cli/commands/validate](https://developer.hashicorp.com/terraform/cli/commands/validate) |
| `terraform fmt` | [developer.hashicorp.com/terraform/cli/commands/fmt](https://developer.hashicorp.com/terraform/cli/commands/fmt) |
| Comments | [developer.hashicorp.com/terraform/language/syntax/configuration#comments](https://developer.hashicorp.com/terraform/language/syntax/configuration#comments) |

---

[← Previous Module](../module-01-introduction/README.md) | [Next Module: First Infrastructure →](../module-03-first-infrastructure/README.md)
