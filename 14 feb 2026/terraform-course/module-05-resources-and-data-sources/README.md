# Module 5: Resources and Data Sources

## Level: INTERMEDIATE | Estimated Time: 3 hours

---

## 5.1 Resources In Depth

Resources are the most important element in Terraform. Each resource block describes one or more infrastructure objects.

### Resource Syntax

```hcl
resource "PROVIDER_TYPE" "LOCAL_NAME" {
  # Arguments (inputs)
  argument1 = "value1"
  argument2 = "value2"

  # Nested block
  nested_block {
    nested_arg = "value"
  }
}
```

```
resource "aws_instance" "web"
           │              │
           │              └── Local name (unique within module)
           └── Resource type (provider_resource)
                 │        │
                 │        └── Resource kind
                 └── Provider prefix
```

### Resource Address

Every resource has a unique address:

```
aws_instance.web              → Single resource
aws_instance.web[0]           → First element (count)
aws_instance.web["app"]       → Keyed element (for_each)
module.vpc.aws_subnet.public  → Resource inside a module
```

### Argument Reference vs Attribute Reference

Every resource has two types of properties — understanding the difference is key:

```
┌──────────────────────┬──────────────────────────────────────────────┐
│                      │ Description                                  │
├──────────────────────┼──────────────────────────────────────────────┤
│ Argument (Input)     │ Values YOU set in the .tf file               │
│                      │ Written by you, read by Terraform            │
│                      │ Example: ami, instance_type, tags            │
│                      │                                              │
│ Attribute (Output)   │ Values TERRAFORM computes after creation     │
│                      │ Written by the provider, read by you         │
│                      │ Example: id, arn, public_ip, dns_name        │
└──────────────────────┴──────────────────────────────────────────────┘
```

```hcl
resource "aws_instance" "web" {
  # Arguments — you provide these
  ami           = "ami-0c55b159cbfafe1f0"   # Argument
  instance_type = "t3.micro"                # Argument
  tags          = { Name = "web" }          # Argument
}

# Attributes — Terraform provides these after creation
output "instance_id" {
  value = aws_instance.web.id              # Attribute (computed)
}

output "public_ip" {
  value = aws_instance.web.public_ip       # Attribute (computed)
}

output "arn" {
  value = aws_instance.web.arn             # Attribute (computed)
}
```

> Find the full list of arguments and attributes for any resource in the [AWS Provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs). Each resource page has an **Argument Reference** section and an **Attribute Reference** section.

---

## 5.2 Resource Behavior

### Create

```hcl
# Adding a new resource to config → Terraform creates it
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket-12345"
}
```

```bash
terraform plan
```
```
  + resource "aws_s3_bucket" "data" {
      + bucket = "my-data-bucket-12345"
      + id     = (known after apply)
      + arn    = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

### Update In-Place

```hcl
# Changing a non-destructive argument → Terraform updates in-place
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket-12345"
  tags = {
    Name = "Updated Tag"  # Adding/changing tags is non-destructive
  }
}
```

```
  ~ resource "aws_s3_bucket" "data" {
      ~ tags = {
          + "Name" = "Updated Tag"
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

### Destroy and Recreate (Replace)

```hcl
# Changing a "ForceNew" argument → Terraform destroys and recreates
resource "aws_instance" "web" {
  ami           = "ami-NEW-AMI-ID"  # Changing AMI forces replacement
  instance_type = "t2.micro"
}
```

```
-/+ resource "aws_instance" "web" {
      ~ ami           = "ami-OLD" -> "ami-NEW"  # forces replacement
      ~ id            = "i-abc123" -> (known after apply)
        instance_type = "t2.micro"
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

### Destroy

```bash
# Removing a resource from config OR running terraform destroy
terraform destroy -target=aws_s3_bucket.data
```

```
  - resource "aws_s3_bucket" "data" {
      - bucket = "my-data-bucket-12345"
      - id     = "my-data-bucket-12345"
    }

Plan: 0 to add, 0 to change, 1 to destroy.
```

---

## 5.3 Resource Meta-Arguments

### count — Create Multiple Identical Resources

```hcl
resource "aws_instance" "web" {
  count = 3

  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "web-server-${count.index}"  # web-server-0, web-server-1, web-server-2
  }
}

# Reference specific instance
output "first_instance_id" {
  value = aws_instance.web[0].id
}

# Reference all instances
output "all_instance_ids" {
  value = aws_instance.web[*].id  # Splat expression
}
```

**Problem with count:** Removing an item from the middle shifts indices:

```hcl
# If you had 3 instances and remove the middle one,
# instance[2] becomes instance[1], causing unnecessary replacement.
# Use for_each instead when items have identity.
```

### for_each — Create Resources from a Map or Set

```hcl
# Using a map
variable "instances" {
  default = {
    web  = "t2.micro"
    api  = "t2.small"
    worker = "t2.medium"
  }
}

resource "aws_instance" "server" {
  for_each = var.instances

  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = each.value

  tags = {
    Name = "${each.key}-server"  # web-server, api-server, worker-server
  }
}

# Reference specific instance
output "web_instance_id" {
  value = aws_instance.server["web"].id
}

# Reference all
output "all_instance_ids" {
  value = { for k, v in aws_instance.server : k => v.id }
}
```

```hcl
# Using a set
resource "aws_iam_user" "developers" {
  for_each = toset(["alice", "bob", "charlie"])
  name     = each.value
}
```

### count vs for_each

```
┌──────────────┬─────────────────────┬──────────────────────────┐
│   Feature    │       count         │       for_each           │
├──────────────┼─────────────────────┼──────────────────────────┤
│ Index type   │ Numeric (0, 1, 2)   │ String key               │
│ Removal      │ Shifts all indices  │ Only removes that key    │
│ Input        │ Number              │ Map or Set               │
│ Reference    │ resource[0]         │ resource["key"]          │
│ Best for     │ Identical copies    │ Distinct named resources │
│ Conditional  │ count = 0 or 1     │ for_each = {} (empty)    │
└──────────────┴─────────────────────┴──────────────────────────┘
```

### Real-Life Example: IAM Users with count

```hcl
variable "user_names" {
  description = "Create IAM users with these names"
  type        = list(string)
  default     = ["sai", "mohan", "jayanth", "angel", "dami"]
}

resource "aws_iam_user" "example" {
  count = length(var.user_names)
  name  = var.user_names[count.index]
}
```

- `count.index` gives the current iteration number (0, 1, 2, ...)
- `length()` returns the number of items in the list
- Reference: `aws_iam_user.example[0].name` → `"sai"`

### Real-Life Example: IAM Users with for_each

```hcl
variable "user_names" {
  description = "Create IAM users with these names"
  type        = list(string)
  default     = ["eve", "jayanth", "john", "satya", "sai"]
}

resource "aws_iam_user" "example" {
  for_each = toset(var.user_names)
  name     = each.value
}
```

- `toset()` converts a list to a set (required by `for_each`)
- `each.value` gives the current item's value
- `each.key` equals `each.value` when iterating over a set
- Reference: `aws_iam_user.example["eve"].name` → `"eve"`
- Removing `"john"` from the list only destroys that one user (no index shifting)

### Conditional Resource Creation with count

Use the ternary operator with `count` to conditionally create resources:

```hcl
variable "create_user" {
  default = true
}

resource "aws_iam_user" "example" {
  count = var.create_user ? 1 : 0    # 1 = create, 0 = don't create
  name  = "conditional-user"
}
```

```hcl
# Another pattern: create different counts based on a condition
variable "is_production" {
  default = false
}

resource "aws_instance" "web" {
  count         = var.is_production ? 3 : 1  # 3 in prod, 1 otherwise
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "web-${count.index}"
  }
}
```

> In the ternary expression `condition ? true_value : false_value`:
> - Expression `0` is `false`, expression `1` (or any non-zero) is `true`
> - `var.create_user ? 1 : 0` → if true, create 1 resource; if false, create 0

---

### lifecycle — Control Resource Behavior

#### The Destroy-Before-Create Problem

When Terraform needs to replace a resource (e.g., AMI change forces recreation), its **default behavior** is:

```
1. Destroy the existing resource
2. Create the new resource
```

This causes **downtime** — the old resource is gone before the new one exists.

**Example — Default behavior (destroy first):**

```hcl
# main.tf
resource "aws_instance" "web" {
  ami           = "ami-OLD123"   # Changing this to ami-NEW456 forces replacement
  instance_type = "t3.micro"
  tags = { Name = "web-server" }
}
```

```bash
# Change AMI from ami-OLD123 to ami-NEW456, then:
terraform plan
```

**Output (default — destroy before create):**
```
  # aws_instance.web must be replaced
-/+ resource "aws_instance" "web" {
      ~ ami           = "ami-OLD123" -> "ami-NEW456" # forces replacement
      ~ id            = "i-0abc123" -> (known after apply)
        instance_type = "t3.micro"
        tags          = { "Name" = "web-server" }
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

The `-/+` symbol means **destroy then create**. During this window, no instance exists.

**Solution:** Use `create_before_destroy = true` to reverse the order:

```hcl
resource "aws_instance" "web" {
  ami           = "ami-NEW456"
  instance_type = "t3.micro"
  tags = { Name = "web-server" }

  lifecycle {
    create_before_destroy = true
  }
}
```

```bash
terraform plan
```

**Output (create before destroy):**
```
  # aws_instance.web must be replaced
+/- resource "aws_instance" "web" {
      ~ ami           = "ami-OLD123" -> "ami-NEW456" # forces replacement
      ~ id            = "i-0abc123" -> (known after apply)
        instance_type = "t3.micro"
        tags          = { "Name" = "web-server" }
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

The `+/-` symbol means **create first, then destroy**. Zero downtime.

**Error scenario — unique name conflict:**

```hcl
resource "aws_security_group" "web" {
  name = "web-sg"   # Unique name — can't have two with same name
  # ...
  lifecycle {
    create_before_destroy = true
  }
}
```

```bash
terraform apply
```

**Error:**
```
Error: creating Security Group (web-sg): InvalidGroup.Duplicate:
The security group 'web-sg' already exists for VPC 'vpc-abc123'
```

**Fix — use `name_prefix` instead of `name`:**

```hcl
resource "aws_security_group" "web" {
  name_prefix = "web-sg-"   # Terraform generates: web-sg-20240115abc
  # ...
  lifecycle {
    create_before_destroy = true
  }
}
```

```bash
terraform apply
```

**Output:**
```
  # aws_security_group.web must be replaced
+/- resource "aws_security_group" "web" {
      ~ id          = "sg-old123" -> (known after apply)
      ~ name        = "web-sg-20240101abc" -> (known after apply)
        name_prefix = "web-sg-"
    }

Plan: 1 to add, 0 to change, 1 to destroy.

aws_security_group.web: Creating...
aws_security_group.web: Creation complete [id=sg-new456]
aws_security_group.web (deposed): Destroying... [id=sg-old123]
aws_security_group.web (deposed): Destruction complete

Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

> ⚠️ Not all resources support `name_prefix`. For resources that require globally unique names (S3 buckets), use a random suffix: `"${var.name}-${random_id.suffix.hex}"`.

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  lifecycle {
    # Create the replacement before destroying the original
    create_before_destroy = true

    # Prevent accidental deletion (terraform destroy will fail)
    prevent_destroy = true

    # Ignore changes made outside Terraform
    ignore_changes = [
      tags,           # Ignore all tag changes
      ami,            # Ignore AMI updates (managed by ASG)
      user_data,      # Ignore user_data changes
    ]

    # Ignore ALL changes (make resource read-only after creation)
    # ignore_changes = all

    # Custom condition that must be true
    precondition {
      condition     = var.instance_type != "t2.nano"
      error_message = "t2.nano is too small for this workload."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP."
    }

    # Replace resource when this value changes
    replace_triggered_by = [
      aws_security_group.web.id  # Recreate instance if SG changes
    ]
  }
}
```

### depends_on — Explicit Dependencies

```hcl
resource "aws_iam_role_policy" "s3_access" {
  name   = "s3-access"
  role   = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = ["${aws_s3_bucket.data.arn}/*"]
    }]
  })
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # The app needs the IAM policy to be in place before starting,
  # but there's no attribute reference to create an implicit dependency
  depends_on = [aws_iam_role_policy.s3_access]
}
```

---

## 5.4 Data Sources

Data sources let you **read** information from existing infrastructure or external sources. A data block will return an error if the queried data doesn't exist.

### Syntax

```hcl
data "PROVIDER_TYPE" "LOCAL_NAME" {
  # Query arguments (filters)
  filter_arg = "value"
}

# Reference: data.PROVIDER_TYPE.LOCAL_NAME.attribute
```

### Interpolation Reference Patterns

```
# Resources:    RESOURCETYPE.RESOURCENAME.ATTRIBUTE
aws_instance.web.id              → "i-0abc123"
aws_instance.web.public_ip       → "54.123.45.67"

# Data Sources: data.DATASOURCETYPE.NAME.ATTRIBUTE
data.aws_ami.ubuntu.id           → "ami-0abc123"
data.aws_availability_zones.available.names → ["us-east-1a", ...]

# Modules:      module.MODULENAME.OUTPUT
module.vpc.vpc_id                → "vpc-0abc123"
```

### Common AWS Data Sources

```hcl
# --- Get current AWS account info ---
data "aws_caller_identity" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
  # → "123456789012"
}

# --- Get current region ---
data "aws_region" "current" {}

output "region" {
  value = data.aws_region.current.name
  # → "us-east-1"
}

# --- Get available AZs ---
data "aws_availability_zones" "available" {
  state = "available"
}

output "azs" {
  value = data.aws_availability_zones.available.names
  # → ["us-east-1a", "us-east-1b", "us-east-1c", ...]
}

# --- Find latest AMI ---
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

output "ubuntu_ami" {
  value = data.aws_ami.ubuntu.id
  # → "ami-0abc123def456"
}

# --- Find existing EC2 instances by filter ---
data "aws_instances" "running" {
  filter {
    name   = "instance-type"
    values = ["t2.micro", "t2.small"]
  }

  instance_state_names = ["running", "stopped"]
}

output "found_instance_ids" {
  value = data.aws_instances.running.ids
  # → ["i-abc123", "i-def456"]
}

# --- Look up existing VPC ---
data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["production-vpc"]
  }
}

# --- Look up existing subnets ---
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.existing.id]
  }

  tags = {
    Tier = "private"
  }
}

# --- Get SSM Parameter (secrets) ---
data "aws_ssm_parameter" "db_password" {
  name            = "/myapp/prod/db_password"
  with_decryption = true
}

# --- Get IAM Policy Document ---
data "aws_iam_policy_document" "s3_read" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "s3_read" {
  name   = "s3-read-policy"
  policy = data.aws_iam_policy_document.s3_read.json
}
```

---

## 5.5 Utility Data Source: Check Instance Type Availability per AZ

Not all instance types are available in every AZ. Use `aws_ec2_instance_type_offerings` to check before deploying:

```hcl
# Check which AZs support t3.micro
data "aws_ec2_instance_type_offerings" "t3_micro" {
  filter {
    name   = "instance-type"
    values = ["t3.micro"]
  }

  filter {
    name   = "location"
    values = data.aws_availability_zones.available.names
  }

  location_type = "availability-zone"
}

data "aws_availability_zones" "available" {
  state = "available"
}

output "t3_micro_supported_azs" {
  value = data.aws_ec2_instance_type_offerings.t3_micro.locations
}
```

```bash
terraform apply
```

**Output:**
```
t3_micro_supported_azs = [
  "us-east-1a",
  "us-east-1b",
  "us-east-1c",
  "us-east-1d",
  "us-east-1f",
]
# Note: us-east-1e does NOT support t3.micro
```

**Real-life use — deploy only to supported AZs:**

```hcl
# Filter subnets to only AZs that support the desired instance type
locals {
  supported_azs = toset(data.aws_ec2_instance_type_offerings.t3_micro.locations)
}

resource "aws_instance" "app" {
  for_each = { for idx, subnet in module.vpc.private_subnets :
    idx => subnet
    if contains(local.supported_azs, module.vpc.azs[idx])
  }

  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  subnet_id     = each.value
}
```

---

## 5.6 Real-Life Example: Deploy to Existing Infrastructure

A common scenario: your VPC and subnets already exist, and you need to deploy into them.

```hcl
# Look up existing infrastructure
data "aws_vpc" "main" {
  tags = {
    Name = "main-vpc"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  tags = {
    Tier = "private"
  }
}

data "aws_security_group" "default" {
  vpc_id = data.aws_vpc.main.id
  name   = "default"
}

# Deploy into existing infrastructure
resource "aws_instance" "app" {
  for_each = toset(data.aws_subnets.private.ids)

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.medium"
  subnet_id              = each.value
  vpc_security_group_ids = [data.aws_security_group.default.id]

  tags = {
    Name = "app-${each.value}"
  }
}
```

---

## 5.6 Resource Dependencies Visualization

```bash
# Generate a dependency graph
terraform graph | dot -Tpng > graph.png

# Or view as text
terraform graph
```

**Output (DOT format):**
```
digraph {
  compound = "true"
  "aws_vpc.main" -> "aws_subnet.public"
  "aws_subnet.public" -> "aws_instance.web"
  "aws_vpc.main" -> "aws_security_group.web"
  "aws_security_group.web" -> "aws_instance.web"
  "aws_vpc.main" -> "aws_internet_gateway.main"
  "aws_internet_gateway.main" -> "aws_route_table.public"
}
```

---

## 5.7 Timeouts

Some resources take time to create or destroy:

```hcl
resource "aws_rds_instance" "database" {
  allocated_storage = 20
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro"
  db_name           = "mydb"
  username          = "admin"
  password          = var.db_password

  timeouts {
    create = "60m"   # Wait up to 60 minutes for creation
    update = "30m"   # Wait up to 30 minutes for updates
    delete = "30m"   # Wait up to 30 minutes for deletion
  }
}
```

**Timeout Error:**
```
Error: Error waiting for RDS instance (mydb) to be created:
timeout while waiting for state to become 'available'
(last state: 'creating', timeout: 40m0s)
```

**Fix:** Increase the timeout or check if the resource is stuck in AWS Console.

---

## 5.8 Sensitive Values

```hcl
variable "db_password" {
  type      = string
  sensitive = true  # Won't show in plan/apply output
}

resource "aws_rds_instance" "database" {
  password = var.db_password
}

output "db_endpoint" {
  value = aws_rds_instance.database.endpoint
}

output "db_password" {
  value     = var.db_password
  sensitive = true  # Required when outputting sensitive values
}
```

**Plan Output with Sensitive Values:**
```
  + resource "aws_rds_instance" "database" {
      + password = (sensitive value)
    }
```

---

## 5.9 Moved Blocks (Refactoring)

When you rename a resource, use `moved` to preserve state:

```hcl
# Old name
# resource "aws_instance" "web" { ... }

# New name
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
}

# Tell Terraform about the rename
moved {
  from = aws_instance.web
  to   = aws_instance.web_server
}
```

```bash
terraform plan
```

**Output:**
```
  # aws_instance.web has moved to aws_instance.web_server
    resource "aws_instance" "web_server" {
        id            = "i-0abc123"
        # (no changes)
    }

Plan: 0 to add, 0 to change, 0 to destroy.
```

Without the `moved` block, Terraform would destroy the old resource and create a new one.

---

## Exercises

### Exercise 5.1: count vs for_each
Create 3 S3 buckets using `count`, then refactor to use `for_each` with meaningful names. Observe the plan differences.

### Exercise 5.2: Data Sources
Write a configuration that:
1. Looks up the default VPC
2. Finds all subnets in it
3. Gets the latest Ubuntu AMI
4. Deploys an EC2 instance in the first subnet

### Exercise 5.3: Lifecycle Rules
Create an RDS instance with:
- `prevent_destroy = true`
- `ignore_changes = [engine_version]`
- Try to destroy it and observe the error

### Exercise 5.4: Moved Block
1. Create a resource called `aws_instance.old_name`
2. Apply it
3. Rename to `aws_instance.new_name` with a `moved` block
4. Run plan and verify no destroy/create

---

## Key Takeaways

- Resources represent infrastructure objects; data sources read existing ones
- Use `for_each` over `count` when resources have distinct identities
- `lifecycle` blocks control create/destroy behavior and change detection
- Data sources are read-only and refresh on every plan
- Use `moved` blocks when refactoring to avoid resource recreation
- Mark sensitive values with `sensitive = true` to prevent exposure in logs

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Resources Overview | [developer.hashicorp.com/terraform/language/resources](https://developer.hashicorp.com/terraform/language/resources) |
| Resource Syntax | [developer.hashicorp.com/terraform/language/resources/syntax](https://developer.hashicorp.com/terraform/language/resources/syntax) |
| Resource Behavior (Create, Update, Destroy) | [developer.hashicorp.com/terraform/language/resources/behavior](https://developer.hashicorp.com/terraform/language/resources/behavior) |
| Data Sources | [developer.hashicorp.com/terraform/language/data-sources](https://developer.hashicorp.com/terraform/language/data-sources) |
| `count` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/count](https://developer.hashicorp.com/terraform/language/meta-arguments/count) |
| `for_each` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each) |
| `depends_on` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/depends_on](https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on) |
| `lifecycle` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle) |
| `provider` Meta-Argument | [developer.hashicorp.com/terraform/language/meta-arguments/resource-provider](https://developer.hashicorp.com/terraform/language/meta-arguments/resource-provider) |
| `moved` Blocks (Refactoring) | [developer.hashicorp.com/terraform/language/modules/develop/refactoring](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring) |
| Timeouts | [developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts](https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts) |
| Sensitive Values | [developer.hashicorp.com/terraform/language/values/outputs#sensitive-suppressing-values-in-cli-output](https://developer.hashicorp.com/terraform/language/values/outputs#sensitive-suppressing-values-in-cli-output) |
| `aws_ami` Data Source | [registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami) |
| `aws_availability_zones` Data Source | [registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones) |
| `aws_caller_identity` Data Source | [registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) |
| `aws_iam_role` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) |
| `aws_iam_policy` Resource | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) |

---

[← Previous Module](../module-04-providers-deep-dive/README.md) | [Next Module: Variables, Outputs, and Locals →](../module-06-variables-outputs-locals/README.md)
