# Module 11: Workspaces and Environment Management

## Level: ADVANCED | Estimated Time: 2 hours

---

## 11.1 Terraform Workspaces

Workspaces allow you to manage multiple state files from a single configuration.

```
┌─────────────────────────────────────────────────────┐
│                 Same Configuration                  │
│                    main.tf                          │
│                                                     │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐          │
│  │ default │   │   dev   │   │  prod   │          │
│  │workspace│   │workspace│   │workspace│          │
│  │         │   │         │   │         │          │
│  │ tfstate │   │ tfstate │   │ tfstate │          │
│  └─────────┘   └─────────┘   └─────────┘          │
└─────────────────────────────────────────────────────┘
```

### Workspace Commands

```bash
# List workspaces (* marks current)
terraform workspace list
```

**Output:**
```
* default
```

```bash
# Create a new workspace
terraform workspace new dev
```

**Output:**
```
Created and switched to workspace "dev"!

You're now on a new, empty workspace. Workspaces isolate their state,
so if you run "terraform plan" Terraform will not see any existing state
for this configuration.
```

```bash
# Switch workspace
terraform workspace select prod
```

**Output:**
```
Switched to workspace "prod".
```

```bash
# Show current workspace
terraform workspace show
```

**Output:**
```
prod
```

```bash
# Delete a workspace (must switch away first)
terraform workspace select default
terraform workspace delete dev
```

---

## 11.2 Using Workspaces in Configuration

```hcl
# Access current workspace name
locals {
  environment = terraform.workspace

  instance_type = {
    default = "t2.micro"
    dev     = "t2.micro"
    staging = "t2.small"
    prod    = "t2.large"
  }

  instance_count = {
    default = 1
    dev     = 1
    staging = 2
    prod    = 3
  }
}

resource "aws_instance" "web" {
  count = local.instance_count[terraform.workspace]

  ami           = data.aws_ami.ubuntu.id
  instance_type = local.instance_type[terraform.workspace]

  tags = {
    Name        = "web-${terraform.workspace}-${count.index}"
    Environment = terraform.workspace
  }
}
```

### State File Location with Workspaces

```
# Local backend
terraform.tfstate.d/
├── dev/
│   └── terraform.tfstate
├── staging/
│   └── terraform.tfstate
└── prod/
    └── terraform.tfstate

# S3 backend
s3://my-bucket/
├── env:/dev/terraform.tfstate
├── env:/staging/terraform.tfstate
└── env:/prod/terraform.tfstate
```

---

## 11.3 Workspaces vs Directory-Based Environments

### Approach 1: Workspaces

```
project/
├── main.tf           # Shared config
├── variables.tf
├── dev.tfvars
├── staging.tfvars
└── prod.tfvars
```

```bash
terraform workspace select dev
terraform apply -var-file=dev.tfvars

terraform workspace select prod
terraform apply -var-file=prod.tfvars
```

### Approach 2: Directory-Based (Recommended for Production)

```
infrastructure/
├── modules/
│   ├── vpc/
│   ├── compute/
│   └── database/
├── environments/
│   ├── dev/
│   │   ├── main.tf          # Calls modules
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf       # Separate state per env
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── backend.tf
```

### Comparison

```
┌──────────────────┬──────────────────────┬──────────────────────┐
│                  │    Workspaces        │   Directory-Based    │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Config           │ Shared (one copy)    │ Per-env (can differ) │
│ State isolation  │ Same backend, diff   │ Separate backends    │
│                  │ state keys           │                      │
│ Blast radius     │ Higher (shared code) │ Lower (isolated)     │
│ Flexibility      │ Same resources       │ Different resources  │
│                  │ everywhere           │ per environment      │
│ Complexity       │ Lower                │ Higher (duplication) │
│ CI/CD            │ Workspace switching  │ Directory targeting  │
│ Best for         │ Simple, identical    │ Complex, different   │
│                  │ environments         │ environments         │
└──────────────────┴──────────────────────┴──────────────────────┘
```

---

## 11.4 Directory-Based Environment Example

```hcl
# environments/dev/main.tf

terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = "us-east-1"
}

module "networking" {
  source = "../../modules/networking"

  vpc_cidr           = "10.0.0.0/16"
  environment        = "dev"
  availability_zones = ["us-east-1a", "us-east-1b"]
  enable_nat_gateway = false  # Save costs in dev
}

module "compute" {
  source = "../../modules/compute"

  vpc_id        = module.networking.vpc_id
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "t3.micro"
  min_size      = 1
  max_size      = 2
  environment   = "dev"
}

# No database module in dev — use local SQLite or shared dev DB
```

```hcl
# environments/prod/main.tf

terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = "us-east-1"
}

module "networking" {
  source = "../../modules/networking"

  vpc_cidr           = "10.1.0.0/16"
  environment        = "prod"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway = true
}

module "compute" {
  source = "../../modules/compute"

  vpc_id        = module.networking.vpc_id
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "t3.large"
  min_size      = 3
  max_size      = 10
  environment   = "prod"
}

module "database" {
  source = "../../modules/database"

  vpc_id         = module.networking.vpc_id
  subnet_ids     = module.networking.private_subnet_ids
  instance_class = "db.r5.large"
  multi_az       = true
  environment    = "prod"
}
```

---

## 11.5 Terragrunt (Brief Overview)

Terragrunt is a wrapper around Terraform that reduces duplication in directory-based setups:

```
infrastructure/
├── terragrunt.hcl              # Root config (backend, provider)
├── modules/
│   └── vpc/
├── environments/
│   ├── dev/
│   │   └── terragrunt.hcl     # Just inputs, inherits rest
│   ├── staging/
│   │   └── terragrunt.hcl
│   └── prod/
│       └── terragrunt.hcl
```

```hcl
# environments/dev/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/vpc"
}

inputs = {
  environment        = "dev"
  vpc_cidr           = "10.0.0.0/16"
  enable_nat_gateway = false
}
```

> Terragrunt is optional but popular for large-scale multi-environment setups.

---

## 11.6 When to Use What

| Scenario | Recommendation |
|----------|---------------|
| Learning / small projects | Workspaces |
| Same infra, different sizes | Workspaces |
| Different infra per env | Directory-based |
| Large team, many envs | Directory-based + Terragrunt |
| Temporary environments | Workspaces |
| Compliance requirements | Directory-based (audit trail) |

---

## Exercises

### Exercise 11.1: Workspace Practice
1. Create `dev`, `staging`, and `prod` workspaces
2. Deploy different instance types per workspace
3. Switch between workspaces and verify isolation

### Exercise 11.2: Directory-Based Setup
1. Create a `modules/` directory with a VPC module
2. Create `environments/dev/` and `environments/prod/`
3. Call the module with different parameters per environment

### Exercise 11.3: Compare Approaches
Deploy the same infrastructure using both workspaces and directory-based approaches. Document the trade-offs you observe.

---

## Key Takeaways

- Workspaces provide state isolation with shared configuration
- Directory-based environments allow different configurations per environment
- Use `terraform.workspace` to access the current workspace name
- Workspaces are simpler; directory-based is more flexible
- For production, directory-based with modules is the standard pattern
- Terragrunt reduces duplication in directory-based setups

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Workspaces | [developer.hashicorp.com/terraform/language/state/workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces) |
| `terraform workspace` Commands | [developer.hashicorp.com/terraform/cli/commands/workspace](https://developer.hashicorp.com/terraform/cli/commands/workspace) |
| `terraform workspace new` | [developer.hashicorp.com/terraform/cli/commands/workspace/new](https://developer.hashicorp.com/terraform/cli/commands/workspace/new) |
| `terraform workspace select` | [developer.hashicorp.com/terraform/cli/commands/workspace/select](https://developer.hashicorp.com/terraform/cli/commands/workspace/select) |
| `terraform workspace list` | [developer.hashicorp.com/terraform/cli/commands/workspace/list](https://developer.hashicorp.com/terraform/cli/commands/workspace/list) |
| `terraform.workspace` Expression | [developer.hashicorp.com/terraform/language/expressions/references#filesystem-and-workspace-info](https://developer.hashicorp.com/terraform/language/expressions/references#filesystem-and-workspace-info) |
| S3 Backend Workspace Key Prefix | [developer.hashicorp.com/terraform/language/backend/s3#workspace_key_prefix](https://developer.hashicorp.com/terraform/language/backend/s3#workspace_key_prefix) |
| Terragrunt (Third-Party) | [terragrunt.gruntwork.io/docs/](https://terragrunt.gruntwork.io/docs/) |

---

[← Previous Module](../module-10-modules/README.md) | [Next Module: Provisioners and Dynamic Blocks →](../module-12-provisioners-and-dynamic-blocks/README.md)
