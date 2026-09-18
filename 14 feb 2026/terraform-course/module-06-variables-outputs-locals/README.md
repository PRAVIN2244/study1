# Module 6: Variables, Outputs, and Locals

## Level: INTERMEDIATE | Estimated Time: 3 hours

---

## 6.1 Input Variables

Variables make your configurations reusable and flexible.

### Variable Declaration

```hcl
# variables.tf

# Simple variable with default
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# Required variable (no default)
variable "project_name" {
  description = "Name of the project"
  type        = string
  # No default = must be provided
}

# Variable with validation
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Sensitive variable
variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Password must be at least 8 characters."
  }
}

# Nullable variable
variable "override_ami" {
  description = "Override AMI ID (null = use data source)"
  type        = string
  default     = null
  nullable    = true
}

# Complex variable
variable "vpc_config" {
  description = "VPC configuration"
  type = object({
    cidr_block         = string
    enable_dns         = bool
    public_subnets     = list(string)
    private_subnets    = list(string)
    availability_zones = list(string)
  })
  default = {
    cidr_block         = "10.0.0.0/16"
    enable_dns         = true
    public_subnets     = ["10.0.1.0/24", "10.0.2.0/24"]
    private_subnets    = ["10.0.10.0/24", "10.0.20.0/24"]
    availability_zones = ["us-east-1a", "us-east-1b"]
  }
}
```

### Complete Variable Type Reference

```
┌──────────────┬──────────────────────────────┬──────────────────────────────┐
│ Type         │ Syntax                       │ Access                       │
├──────────────┼──────────────────────────────┼──────────────────────────────┤
│ string       │ type = string                │ var.name                     │
│ number       │ type = number                │ var.port                     │
│ bool         │ type = bool                  │ var.enabled                  │
│ list         │ type = list(string)          │ var.zones[0]                 │
│ set          │ type = set(string)           │ (iterate with for_each)      │
│ map          │ type = map(string)           │ var.amis["ubuntu"]           │
│ object       │ type = object({...})         │ var.config.name              │
│ tuple        │ type = tuple([string, num])  │ var.data[0]                  │
│ any          │ type = any                   │ (accepts any type)           │
└──────────────┴──────────────────────────────┴──────────────────────────────┘
```

### The `any` Type

Use `any` when you want a variable to accept any type:

```hcl
variable "settings" {
  type    = any
  default = {
    name  = "web"
    count = 3
    tags  = ["a", "b"]
  }
}

# Terraform infers the actual type at runtime
# Useful for passing through complex data without strict typing
```

```hcl
# Common use: map of any
variable "extra_tags" {
  type    = map(any)
  default = {}
}

# list of any
variable "mixed_list" {
  type    = list(any)
  default = ["hello", 42, true]  # All converted to strings
}
```

> Use `any` sparingly — explicit types catch errors earlier and make code self-documenting.

---

## 6.2 Ways to Set Variable Values

### Priority Order (lowest to highest)

```
1. Default value in variable block          (lowest priority)
2. Environment variable (TF_VAR_name)
3. terraform.tfvars file
4. *.auto.tfvars files (alphabetical order)
5. -var-file flag
6. -var flag on command line                (highest priority)
```

### Method 1: Default Values

```hcl
variable "region" {
  default = "us-east-1"  # Used if nothing else is specified
}
```

### Method 2: Environment Variables

```bash
export TF_VAR_region="us-west-2"
export TF_VAR_db_password="SuperSecret123!"
export TF_VAR_instance_type="t2.large"

terraform plan  # Variables picked up automatically
```

### Method 3: terraform.tfvars

```hcl
# terraform.tfvars (auto-loaded)
region        = "us-east-1"
environment   = "prod"
instance_type = "t2.large"
project_name  = "myapp"
```

### Method 4: Named .tfvars Files

```hcl
# environments/prod.tfvars
region        = "us-east-1"
environment   = "prod"
instance_type = "t2.large"
min_instances = 3

# environments/dev.tfvars
region        = "us-west-2"
environment   = "dev"
instance_type = "t2.micro"
min_instances = 1
```

```bash
terraform plan -var-file="environments/prod.tfvars"
terraform apply -var-file="environments/dev.tfvars"
```

### Method 5: Auto-loaded .tfvars

```
# Files matching these patterns are auto-loaded:
terraform.tfvars
terraform.tfvars.json
*.auto.tfvars
*.auto.tfvars.json
```

### Method 6: Command Line

```bash
terraform plan -var="region=eu-west-1" -var="environment=staging"
```

### Method 7: Interactive Prompt

If a required variable has no value, Terraform prompts:

```bash
terraform plan
```

```
var.project_name
  Name of the project

  Enter a value: myapp
```

---

## 6.3 Variable Validation

```hcl
variable "instance_type" {
  type = string

  validation {
    condition     = can(regex("^t[23]\\.", var.instance_type))
    error_message = "Instance type must be t2.* or t3.* family."
  }
}

variable "cidr_block" {
  type = string

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block (e.g., 10.0.0.0/16)."
  }
}

variable "port" {
  type = number

  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Port must be between 1 and 65535."
  }
}

variable "tags" {
  type = map(string)

  validation {
    condition     = length(var.tags) > 0
    error_message = "At least one tag must be provided."
  }

  validation {
    condition     = contains(keys(var.tags), "Environment")
    error_message = "Tags must include an 'Environment' key."
  }
}
```

**Validation Error Output:**
```
Error: Invalid value for variable

  on variables.tf line 5:
   5: variable "instance_type" {

Instance type must be t2.* or t3.* family.

This was checked by the validation rule at variables.tf:8,3-13.
```

---

## 6.4 Output Values

Outputs expose information about your infrastructure after `terraform apply`.

### Basic Outputs

```hcl
# outputs.tf

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "instance_public_ips" {
  description = "Public IPs of all web instances"
  value       = aws_instance.web[*].public_ip
}

output "database_endpoint" {
  description = "RDS endpoint"
  value       = aws_rds_instance.main.endpoint
  sensitive   = true  # Hide in CLI output
}
```

### Conditional Outputs

```hcl
output "load_balancer_dns" {
  description = "ALB DNS name (only in prod)"
  value       = var.environment == "prod" ? aws_lb.main[0].dns_name : "N/A"
}
```

### Complex Outputs

```hcl
output "infrastructure_summary" {
  description = "Summary of all created resources"
  value = {
    vpc = {
      id   = aws_vpc.main.id
      cidr = aws_vpc.main.cidr_block
    }
    instances = {
      for k, v in aws_instance.server : k => {
        id        = v.id
        public_ip = v.public_ip
        type      = v.instance_type
      }
    }
    subnets = [for s in aws_subnet.public : {
      id   = s.id
      cidr = s.cidr_block
      az   = s.availability_zone
    }]
  }
}
```

### Using Outputs

```bash
# Show all outputs
terraform output

# Show specific output
terraform output vpc_id

# Get raw value (no quotes, useful in scripts)
terraform output -raw vpc_id

# Get as JSON
terraform output -json

# Use in scripts
VPC_ID=$(terraform output -raw vpc_id)
echo "VPC: $VPC_ID"
```

**Output of `terraform output -json`:**
```json
{
  "vpc_id": {
    "sensitive": false,
    "type": "string",
    "value": "vpc-0abc123def456"
  },
  "instance_public_ips": {
    "sensitive": false,
    "type": ["list", "string"],
    "value": ["54.123.45.67", "54.123.45.68"]
  }
}
```

---

## 6.5 Local Values

Locals are computed values used within a module. They reduce repetition and improve readability.

**Key characteristics:**
- Scoped to the module where they are defined — not accessible from outside
- Cannot be overridden by the caller (unlike variables)
- Computed once and reused — useful for generating dynamic values like names, tags, or derived config

### Basic Locals

```hcl
locals {
  # Simple values
  name_prefix = "${var.project}-${var.environment}"
  
  # Common tags applied everywhere
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.team
  }

  # Computed values
  is_production = var.environment == "prod"
  instance_type = local.is_production ? "t3.large" : "t3.micro"
  
  # Derived from other locals
  full_name = "${local.name_prefix}-${var.aws_region}"
}
```

### Using Locals

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = local.instance_type

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web"
    Role = "web-server"
  })
}

resource "aws_s3_bucket" "logs" {
  bucket = "${local.name_prefix}-logs"
  tags   = local.common_tags
}

resource "aws_rds_instance" "db" {
  instance_class    = local.is_production ? "db.r5.large" : "db.t3.micro"
  multi_az          = local.is_production
  backup_retention_period = local.is_production ? 30 : 1

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database"
  })
}
```

### Advanced Locals: Data Transformation

```hcl
variable "subnets" {
  default = {
    public-1  = { cidr = "10.0.1.0/24", az = "a", public = true }
    public-2  = { cidr = "10.0.2.0/24", az = "b", public = true }
    private-1 = { cidr = "10.0.10.0/24", az = "a", public = false }
    private-2 = { cidr = "10.0.20.0/24", az = "b", public = false }
  }
}

locals {
  # Filter public subnets
  public_subnets = {
    for k, v in var.subnets : k => v if v.public
  }

  # Filter private subnets
  private_subnets = {
    for k, v in var.subnets : k => v if !v.public
  }

  # Extract just the CIDRs
  all_cidrs = [for k, v in var.subnets : v.cidr]

  # Create a map of AZ to subnet CIDRs
  az_subnets = {
    for k, v in var.subnets : v.az => v.cidr...
  }
  # Result: { "a" = ["10.0.1.0/24", "10.0.10.0/24"], "b" = ["10.0.2.0/24", "10.0.20.0/24"] }
}
```

---

## 6.6 Variables vs Locals vs Outputs

```
┌──────────────┬──────────────────┬──────────────────┬──────────────────┐
│              │    Variables     │     Locals       │    Outputs       │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Purpose      │ Accept input     │ Compute values   │ Expose values    │
│ Set by       │ User/caller      │ Configuration    │ Terraform        │
│ Scope        │ Module-wide      │ Module-wide      │ Module boundary  │
│ Mutable      │ Yes (per run)    │ No (computed)    │ No (read-only)   │
│ Reference    │ var.name         │ local.name       │ module.x.name    │
│ File         │ variables.tf     │ locals.tf/main.tf│ outputs.tf       │
└──────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## 6.7 Real-Life Example: Environment-Based Configuration

```hcl
# variables.tf
variable "environment" {
  type = string
}

# locals.tf
locals {
  env_config = {
    dev = {
      instance_type       = "t3.micro"
      min_size            = 1
      max_size            = 2
      multi_az            = false
      db_instance_class   = "db.t3.micro"
      enable_monitoring   = false
      backup_retention    = 1
      deletion_protection = false
    }
    staging = {
      instance_type       = "t3.small"
      min_size            = 2
      max_size            = 4
      multi_az            = false
      db_instance_class   = "db.t3.small"
      enable_monitoring   = true
      backup_retention    = 7
      deletion_protection = false
    }
    prod = {
      instance_type       = "t3.large"
      min_size            = 3
      max_size            = 10
      multi_az            = true
      db_instance_class   = "db.r5.large"
      enable_monitoring   = true
      backup_retention    = 30
      deletion_protection = true
    }
  }

  config = local.env_config[var.environment]
}

# main.tf
resource "aws_launch_template" "app" {
  instance_type = local.config.instance_type
  monitoring {
    enabled = local.config.enable_monitoring
  }
}

resource "aws_autoscaling_group" "app" {
  min_size = local.config.min_size
  max_size = local.config.max_size
}

resource "aws_rds_instance" "main" {
  instance_class      = local.config.db_instance_class
  multi_az            = local.config.multi_az
  backup_retention_period = local.config.backup_retention
  deletion_protection = local.config.deletion_protection
}
```

Usage:
```bash
# Deploy dev
terraform apply -var="environment=dev"

# Deploy prod
terraform apply -var="environment=prod"
```

---

## 6.8 Common Errors

### Error: Variable Not Set

```
Error: No value for required variable

  on variables.tf line 1:
   1: variable "project_name" {

The root module input variable "project_name" is not set, and has no
default value. Use a -var or -var-file command line argument or set
the variable in a "tfvars" file.
```

### Error: Invalid Variable Type

```
Error: Invalid value for variable

  on terraform.tfvars line 3:
   3: instance_count = "three"

The given value is not suitable for var.instance_count declared at
variables.tf:10,1-28: a number is required.
```

### Error: Validation Failed

```
Error: Invalid value for variable

  on variables.tf line 5:
   5: variable "environment" {

Environment must be one of: dev, staging, prod.

This was checked by the validation rule at variables.tf:10,3-13.
```

---

## Exercises

### Exercise 6.1: Variable Precedence
1. Set `region = "us-east-1"` as default
2. Set `TF_VAR_region="us-west-1"` as env var
3. Set `region = "eu-west-1"` in terraform.tfvars
4. Run `terraform plan -var="region=ap-southeast-1"`
5. Which value wins? Verify with an output.

### Exercise 6.2: Complex Variables
Create a variable of type `list(object)` that defines multiple EC2 instances with different configurations. Use `for_each` to create them.

### Exercise 6.3: Environment Config
Implement the environment-based configuration pattern from section 6.7. Deploy with different `-var="environment=X"` values and compare the plans.

### Exercise 6.4: Output Formatting
Create outputs that display:
1. A formatted string with instance details
2. A map of instance names to IPs
3. A JSON-encoded summary

---

## Key Takeaways

- Variables accept input; locals compute values; outputs expose results
- Variable precedence: CLI flags > tfvars > env vars > defaults
- Use validation blocks to enforce constraints early
- Locals reduce repetition and centralize computed values
- Use `sensitive = true` for passwords, keys, and tokens
- Environment-based config maps are a clean pattern for multi-env deployments
- Always provide descriptions for variables and outputs

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Input Variables | [developer.hashicorp.com/terraform/language/values/variables](https://developer.hashicorp.com/terraform/language/values/variables) |
| Variable Types (string, number, bool, list, map, object, tuple, set) | [developer.hashicorp.com/terraform/language/expressions/types](https://developer.hashicorp.com/terraform/language/expressions/types) |
| Type Constraints | [developer.hashicorp.com/terraform/language/expressions/type-constraints](https://developer.hashicorp.com/terraform/language/expressions/type-constraints) |
| `optional()` Type Modifier | [developer.hashicorp.com/terraform/language/expressions/type-constraints#optional](https://developer.hashicorp.com/terraform/language/expressions/type-constraints#optional) |
| Variable Validation | [developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules) |
| Variable Definition Precedence | [developer.hashicorp.com/terraform/language/values/variables#variable-definition-precedence](https://developer.hashicorp.com/terraform/language/values/variables#variable-definition-precedence) |
| Output Values | [developer.hashicorp.com/terraform/language/values/outputs](https://developer.hashicorp.com/terraform/language/values/outputs) |
| Local Values | [developer.hashicorp.com/terraform/language/values/locals](https://developer.hashicorp.com/terraform/language/values/locals) |
| Sensitive Variables | [developer.hashicorp.com/terraform/language/values/variables#suppressing-values-in-cli-output](https://developer.hashicorp.com/terraform/language/values/variables#suppressing-values-in-cli-output) |
| `.tfvars` Files | [developer.hashicorp.com/terraform/language/values/variables#variable-definitions-tfvars-files](https://developer.hashicorp.com/terraform/language/values/variables#variable-definitions-tfvars-files) |
| Environment Variables (`TF_VAR_`) | [developer.hashicorp.com/terraform/language/values/variables#environment-variables](https://developer.hashicorp.com/terraform/language/values/variables#environment-variables) |
| `terraform output` Command | [developer.hashicorp.com/terraform/cli/commands/output](https://developer.hashicorp.com/terraform/cli/commands/output) |

---

[← Previous Module](../module-05-resources-and-data-sources/README.md) | [Next Module: State Management →](../module-07-state-management/README.md)
