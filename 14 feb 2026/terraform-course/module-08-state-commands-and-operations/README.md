# Module 8: State Commands and Operations

## Level: INTERMEDIATE | Estimated Time: 2 hours

---

## 8.1 terraform state Commands Overview

```bash
terraform state <subcommand>
```

| Command | Purpose |
|---------|---------|
| `list` | List resources in state |
| `show` | Show details of a resource |
| `mv` | Move/rename a resource in state |
| `rm` | Remove a resource from state |
| `pull` | Download remote state to stdout |
| `push` | Upload local state to remote backend |
| `replace-provider` | Replace provider in state |

---

## 8.2 terraform state list

```bash
terraform state list
```

**Output:**
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
# Filter by resource type
terraform state list aws_instance.*
```

**Output:**
```
aws_instance.web
```

```bash
# Filter resources with count
terraform state list 'aws_instance.web[*]'
```

**Output:**
```
aws_instance.web[0]
aws_instance.web[1]
aws_instance.web[2]
```

---

## 8.3 terraform state show

```bash
terraform state show aws_instance.web
```

**Output:**
```
# aws_instance.web:
resource "aws_instance" "web" {
    ami                          = "ami-0c55b159cbfafe1f0"
    arn                          = "arn:aws:ec2:us-east-1:123456789012:instance/i-0abc123def456"
    associate_public_ip_address  = true
    availability_zone            = "us-east-1a"
    cpu_core_count               = 1
    cpu_threads_per_core         = 1
    disable_api_stop             = false
    disable_api_termination      = false
    ebs_optimized                = false
    get_password_data            = false
    hibernation                  = false
    id                           = "i-0abc123def456"
    instance_initiated_shutdown_behavior = "stop"
    instance_state               = "running"
    instance_type                = "t2.micro"
    ipv6_address_count           = 0
    ipv6_addresses               = []
    monitoring                   = false
    primary_network_interface_id = "eni-0abc123"
    private_dns                  = "ip-10-0-1-50.ec2.internal"
    private_ip                   = "10.0.1.50"
    public_dns                   = "ec2-54-123-45-67.compute-1.amazonaws.com"
    public_ip                    = "54.123.45.67"
    secondary_private_ips        = []
    security_groups              = []
    source_dest_check            = true
    subnet_id                    = "subnet-0abc123"
    tags                         = {
        "Environment" = "dev"
        "Name"        = "web-server"
    }
    tenancy                      = "default"
    vpc_security_group_ids       = [
        "sg-0abc123",
    ]

    root_block_device {
        delete_on_termination = true
        device_name           = "/dev/xvda"
        encrypted             = true
        volume_id             = "vol-0abc123"
        volume_size           = 20
        volume_type           = "gp3"
    }
}
```

---

## 8.4 terraform state mv

Rename or move resources without destroying them.

### Rename a Resource

```bash
# Rename aws_instance.web to aws_instance.web_server
terraform state mv aws_instance.web aws_instance.web_server
```

**Output:**
```
Move "aws_instance.web" to "aws_instance.web_server"
Successfully moved 1 object(s).
```

> ⚠️ You must also update the resource name in your `.tf` files to match.

### Move to a Module

```bash
# Move a resource into a module
terraform state mv aws_instance.web module.compute.aws_instance.web
```

**Output:**
```
Move "aws_instance.web" to "module.compute.aws_instance.web"
Successfully moved 1 object(s).
```

### Move Between count and for_each

```bash
# From count index to for_each key
terraform state mv 'aws_instance.web[0]' 'aws_instance.web["app"]'
terraform state mv 'aws_instance.web[1]' 'aws_instance.web["api"]'
```

### Dry Run

```bash
# Preview the move without executing
terraform state mv -dry-run aws_instance.web aws_instance.web_server
```

**Output:**
```
Would move "aws_instance.web" to "aws_instance.web_server"
```

---

## 8.5 terraform state rm

Remove a resource from state WITHOUT destroying it in the cloud.

```bash
# Remove from state (resource continues to exist in AWS)
terraform state rm aws_instance.web
```

**Output:**
```
Removed aws_instance.web
Successfully removed 1 resource instance(s).
```

### When to Use state rm

```
┌─────────────────────────────────────────────────────────────┐
│  Use Case                          │  Command               │
├─────────────────────────────────────────────────────────────┤
│  Hand off resource to another      │  terraform state rm    │
│  Terraform project                 │                        │
│                                    │                        │
│  Resource was created manually     │  terraform state rm    │
│  and imported by mistake           │                        │
│                                    │                        │
│  Moving resource to a different    │  state rm + import     │
│  state file                        │  in new project        │
│                                    │                        │
│  Resource managed by another tool  │  terraform state rm    │
│  now (e.g., CloudFormation)        │                        │
└─────────────────────────────────────────────────────────────┘
```

> After `state rm`, the next `terraform plan` will show the resource as "to be created" because Terraform no longer knows about it.

---

## 8.6 terraform import

Import existing cloud resources into Terraform state.

### Basic Import

```bash
# Syntax: terraform import <resource_address> <cloud_resource_id>
terraform import aws_instance.web i-0abc123def456
```

**Output:**
```
aws_instance.web: Importing from ID "i-0abc123def456"...
aws_instance.web: Import prepared!
  Prepared aws_instance for import
aws_instance.web: Refreshing state... [id=i-0abc123def456]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

### Import Workflow

```
Step 1: Write the resource block (empty or partial)
Step 2: Run terraform import
Step 3: Run terraform state show to see all attributes
Step 4: Fill in the resource block to match
Step 5: Run terraform plan to verify no changes
```

### Example: Import an Existing VPC

```hcl
# Step 1: Write empty resource block
resource "aws_vpc" "imported" {
  # Will fill in after import
  cidr_block = "10.0.0.0/16"  # Must match the real VPC
}
```

```bash
# Step 2: Import
terraform import aws_vpc.imported vpc-0abc123def456
```

```bash
# Step 3: See what was imported
terraform state show aws_vpc.imported
```

```hcl
# Step 4: Update resource to match (from state show output)
resource "aws_vpc" "imported" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "production-vpc"
  }
}
```

```bash
# Step 5: Verify — should show no changes
terraform plan
```

**Expected Output:**
```
No changes. Your infrastructure matches the configuration.
```

### Import Block (Terraform 1.5+)

Instead of CLI import, use import blocks in config:

```hcl
# import.tf
import {
  to = aws_instance.web
  id = "i-0abc123def456"
}

import {
  to = aws_vpc.main
  id = "vpc-0abc123def456"
}

import {
  to = aws_s3_bucket.data
  id = "my-existing-bucket"
}
```

```bash
# Generate config for imported resources
terraform plan -generate-config-out=generated.tf
```

This generates a `generated.tf` file with the full resource configuration.

---

## 8.7 terraform import vs terraform refresh

These two commands are often confused. They solve completely different problems.

```
┌──────────────────────┬──────────────────────────────────────────────────────┐
│                      │  terraform import          │  terraform refresh      │
├──────────────────────┼────────────────────────────┼─────────────────────────┤
│ Purpose              │ Bring an EXISTING resource │ Update state to match   │
│                      │ under Terraform management │ current cloud reality   │
│                      │                            │                         │
│ When to use          │ Resource was created       │ Resource was MODIFIED   │
│                      │ OUTSIDE Terraform (manual, │ outside Terraform and   │
│                      │ CLI, another tool)         │ you want state updated  │
│                      │                            │                         │
│ What it does         │ Adds resource to state     │ Reads current cloud     │
│                      │ file by querying cloud API │ state for ALL resources │
│                      │ for that specific resource │ and updates state file  │
│                      │                            │                         │
│ Changes infra?       │ No                         │ No                      │
│                      │                            │                         │
│ Changes state?       │ Yes (adds new entry)       │ Yes (updates existing)  │
│                      │                            │                         │
│ Changes .tf files?   │ No (you must write the     │ No                      │
│                      │ resource block yourself)   │                         │
│                      │                            │                         │
│ Requires resource    │ Yes (must exist in .tf)    │ No (reads all from      │
│ block in config?     │                            │ state)                  │
│                      │                            │                         │
│ Scope                │ One resource at a time     │ All resources in state  │
│                      │                            │                         │
│ Modern replacement   │ import {} block (1.5+)     │ terraform apply         │
│                      │                            │ -refresh-only           │
└──────────────────────┴────────────────────────────┴─────────────────────────┘
```

### Example Scenario

```bash
# Scenario: EC2 instance i-abc123 was created manually in AWS Console

# Step 1: Write the resource block in your .tf file
# resource "aws_instance" "manual_server" { ... }

# Step 2: Import it into state
terraform import aws_instance.manual_server i-abc123
# → State now knows about this instance

# Step 3: Run plan to verify
terraform plan
# → Should show no changes if your .tf matches reality
```

```bash
# Scenario: Someone changed the instance type in AWS Console

# Option A: Update state to match reality (accept the change)
terraform apply -refresh-only
# → State updated, .tf file still says old value
# → Next plan will show Terraform wants to revert the change

# Option B: Just run apply to revert the manual change
terraform apply
# → Terraform changes the instance back to what .tf says
```

---

## 8.8 terraform state pull / push

### Pull (Download Remote State)

```bash
# Download remote state as JSON
terraform state pull > state_backup.json

# Inspect it
cat state_backup.json | jq '.resources | length'
# → 15

# Find specific resource
cat state_backup.json | jq '.resources[] | select(.type == "aws_instance")'
```

### Push (Upload State — Dangerous!)

```bash
# Upload local state to remote backend
terraform state push terraform.tfstate

# Force push (override serial check — VERY DANGEROUS)
terraform state push -force terraform.tfstate
```

> ⚠️ `state push` can overwrite remote state. Only use for disaster recovery.

---

## 8.9 terraform state replace-provider

When migrating between provider forks or namespaces:

```bash
terraform state replace-provider hashicorp/aws registry.example.com/company/aws
```

**Output:**
```
Terraform will perform the following actions:

  ~ Updating provider:
    - registry.terraform.io/hashicorp/aws
    + registry.example.com/company/aws

Do you approve? (yes/no): yes

Successfully replaced provider for 15 resources.
```

---

## 8.10 Targeted Operations

Apply or destroy specific resources:

```bash
# Plan for a specific resource
terraform plan -target=aws_instance.web

# Apply only a specific resource
terraform apply -target=aws_instance.web

# Destroy only a specific resource
terraform destroy -target=aws_instance.web

# Multiple targets
terraform apply -target=aws_instance.web -target=aws_s3_bucket.data
```

**Output:**
```
Note: You are using the -target option to apply changes to specific resources.
This may cause your state to become inconsistent. Use with caution.

  # aws_instance.web will be created
  + resource "aws_instance" "web" { ... }

Plan: 1 to add, 0 to change, 0 to destroy.
```

> ⚠️ `-target` is for exceptional situations (debugging, recovery). Don't use it as a regular workflow.

---

## 8.11 terraform taint / untaint (Deprecated)

Replaced by `terraform apply -replace` in Terraform 1.0+:

```bash
# Old way (deprecated)
terraform taint aws_instance.web
terraform apply

# New way (recommended)
terraform apply -replace=aws_instance.web
```

**Output:**
```
  # aws_instance.web will be replaced, as requested
-/+ resource "aws_instance" "web" {
      ~ id            = "i-0abc123" -> (known after apply)
        instance_type = "t2.micro"
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

---

## 8.12 Real-Life Scenario: Migrating Resources Between Projects

```bash
# Project A: Remove from state
cd project-a
terraform state rm aws_s3_bucket.shared_data
# Resource still exists in AWS, just not managed by Project A

# Project B: Import into state
cd ../project-b
# Add resource block to main.tf first
terraform import aws_s3_bucket.shared_data my-shared-bucket
terraform plan  # Verify no changes
```

---

## Exercises

### Exercise 8.1: State Exploration
1. Deploy a VPC with 2 subnets and an EC2 instance
2. Use `state list` to see all resources
3. Use `state show` on each resource
4. Practice `state mv` to rename a resource

### Exercise 8.2: Import Practice
1. Create an S3 bucket manually in AWS Console
2. Write a Terraform resource block for it
3. Import it with `terraform import`
4. Run `terraform plan` to verify zero changes

### Exercise 8.3: State Surgery
1. Deploy 3 EC2 instances using `count`
2. Use `state mv` to convert them to `for_each`
3. Update the config to use `for_each`
4. Verify with `terraform plan` — should show no changes

---

## Key Takeaways

- `state list` and `state show` are safe read-only operations
- `state mv` renames resources without destroying them
- `state rm` removes from state but leaves the cloud resource intact
- `terraform import` brings existing resources under Terraform management
- Import blocks (1.5+) are preferred over CLI import
- `-target` is for emergencies, not regular workflow
- Use `-replace` instead of the deprecated `taint` command
- Always backup state before state surgery operations

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| `terraform state` Command | [developer.hashicorp.com/terraform/cli/commands/state](https://developer.hashicorp.com/terraform/cli/commands/state) |
| `terraform state list` | [developer.hashicorp.com/terraform/cli/commands/state/list](https://developer.hashicorp.com/terraform/cli/commands/state/list) |
| `terraform state show` | [developer.hashicorp.com/terraform/cli/commands/state/show](https://developer.hashicorp.com/terraform/cli/commands/state/show) |
| `terraform state mv` | [developer.hashicorp.com/terraform/cli/commands/state/mv](https://developer.hashicorp.com/terraform/cli/commands/state/mv) |
| `terraform state rm` | [developer.hashicorp.com/terraform/cli/commands/state/rm](https://developer.hashicorp.com/terraform/cli/commands/state/rm) |
| `terraform state pull` | [developer.hashicorp.com/terraform/cli/commands/state/pull](https://developer.hashicorp.com/terraform/cli/commands/state/pull) |
| `terraform state push` | [developer.hashicorp.com/terraform/cli/commands/state/push](https://developer.hashicorp.com/terraform/cli/commands/state/push) |
| `terraform state replace-provider` | [developer.hashicorp.com/terraform/cli/commands/state/replace-provider](https://developer.hashicorp.com/terraform/cli/commands/state/replace-provider) |
| `terraform import` | [developer.hashicorp.com/terraform/cli/commands/import](https://developer.hashicorp.com/terraform/cli/commands/import) |
| Import Block (Declarative) | [developer.hashicorp.com/terraform/language/import](https://developer.hashicorp.com/terraform/language/import) |
| `terraform apply -target` | [developer.hashicorp.com/terraform/cli/commands/apply#target](https://developer.hashicorp.com/terraform/cli/commands/apply#target) |
| `terraform apply -replace` | [developer.hashicorp.com/terraform/cli/commands/apply#replace](https://developer.hashicorp.com/terraform/cli/commands/apply#replace) |
| Taint (Deprecated) | [developer.hashicorp.com/terraform/cli/commands/taint](https://developer.hashicorp.com/terraform/cli/commands/taint) |

---

[← Previous Module](../module-07-state-management/README.md) | [Next Module: Remote State and Backends →](../module-09-remote-state-and-backends/README.md)
