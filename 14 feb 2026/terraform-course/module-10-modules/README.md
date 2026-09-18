# Module 10: Terraform Modules

## Level: ADVANCED | Estimated Time: 4 hours

---

## 10.1 What Are Modules?

A module is a container for multiple resources that are used together. Every Terraform configuration is a module (the "root module"). Modules let you organize, reuse, and share infrastructure code.

```
┌─────────────────────────────────────────────────────────┐
│                    Root Module                          │
│                    (your project)                       │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  VPC     │  │ Compute  │  │ Database │             │
│  │  Module  │  │  Module  │  │  Module  │             │
│  │          │  │          │  │          │             │
│  │ vpc.tf   │  │ ec2.tf   │  │ rds.tf   │             │
│  │ subnets  │  │ alb.tf   │  │ replica  │             │
│  │ routes   │  │ asg.tf   │  │ backup   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 10.2 Module Structure

```
modules/
└── vpc/
    ├── main.tf          # Resource definitions
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    ├── versions.tf      # Provider requirements
    └── README.md        # Documentation
```

### Creating a VPC Module

```hcl
# modules/vpc/variables.tf

variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "List of public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "List of private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "availability_zones" {
  description = "List of AZs"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

```hcl
# modules/vpc/main.tf

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = var.vpc_name
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-igw"
  })
}

# --- Public Subnets ---
resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-public-${var.availability_zones[count.index]}"
    Tier = "public"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- Private Subnets ---
resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-private-${var.availability_zones[count.index]}"
    Tier = "private"
  })
}

# --- NAT Gateway (optional) ---
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-nat-eip"
  })
}

resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-nat"
  })

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this[0].id
    }
  }

  tags = merge(var.tags, {
    Name = "${var.vpc_name}-private-rt"
  })
}

resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

```hcl
# modules/vpc/outputs.tf

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ip" {
  description = "Public IP of NAT Gateway"
  value       = var.enable_nat_gateway ? aws_eip.nat[0].public_ip : null
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.this.id
}
```

---

## 10.3 Using Modules

### Calling a Local Module

```hcl
# main.tf (root module)

module "vpc" {
  source = "./modules/vpc"

  vpc_name           = "myapp-${var.environment}"
  vpc_cidr           = "10.0.0.0/16"
  public_subnets     = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets    = ["10.0.10.0/24", "10.0.20.0/24"]
  availability_zones = ["us-east-1a", "us-east-1b"]
  enable_nat_gateway = var.environment == "prod"

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Use module outputs
resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  subnet_id     = module.vpc.private_subnet_ids[0]

  tags = {
    Name = "app-server"
  }
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
```

### Calling Multiple Instances of a Module

```hcl
module "vpc_dev" {
  source = "./modules/vpc"

  vpc_name           = "dev"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  enable_nat_gateway = false
}

module "vpc_prod" {
  source = "./modules/vpc"

  vpc_name           = "prod"
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets     = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  private_subnets    = ["10.1.10.0/24", "10.1.20.0/24", "10.1.30.0/24"]
  enable_nat_gateway = true
}
```

### Using for_each with Modules

```hcl
variable "environments" {
  default = {
    dev = {
      cidr           = "10.0.0.0/16"
      nat_gateway    = false
      instance_type  = "t3.micro"
    }
    staging = {
      cidr           = "10.1.0.0/16"
      nat_gateway    = true
      instance_type  = "t3.small"
    }
    prod = {
      cidr           = "10.2.0.0/16"
      nat_gateway    = true
      instance_type  = "t3.large"
    }
  }
}

module "vpc" {
  source   = "./modules/vpc"
  for_each = var.environments

  vpc_name           = each.key
  vpc_cidr           = each.value.cidr
  availability_zones = ["us-east-1a", "us-east-1b"]
  enable_nat_gateway = each.value.nat_gateway

  tags = {
    Environment = each.key
  }
}

# Access: module.vpc["dev"].vpc_id
# Access: module.vpc["prod"].private_subnet_ids
```

---

## 10.4 Module Sources — Complete Reference

### Source 1: Same Folder

```
project/
├── main.tf
└── modules/
    └── vpc/
        └── main.tf
```

```hcl
module "vpc" {
  source = "./modules/vpc"
}
```

### Source 2: Different Folder (Relative Path)

```
/home/user/
├── project-a/
│   └── main.tf          ← calling module from here
└── shared-modules/
    └── vpc/
        └── main.tf
```

```hcl
module "vpc" {
  source = "../shared-modules/vpc"
}
```

### Source 3: Terraform Registry (Public)

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"    # Always pin the version
}
```

```bash
terraform init
```

**Output:**
```
Downloading registry.terraform.io/terraform-aws-modules/vpc/aws 5.1.0 for vpc...
- vpc in .terraform/modules/vpc
```

### Source 4: GitHub (HTTPS)

```hcl
# Public repo
module "vpc" {
  source = "github.com/terraform-aws-modules/terraform-aws-vpc?ref=v5.1.0"
}

# Private repo (uses git credentials or GITHUB_TOKEN)
module "vpc" {
  source = "github.com/myorg/terraform-modules?ref=v2.0.0"
}
```

### Source 5: GitHub (SSH)

```hcl
module "vpc" {
  source = "git@github.com:myorg/terraform-modules.git?ref=v2.0.0"
}
```

> Requires SSH key configured: `~/.ssh/id_rsa` or SSH agent.

### Source 6: GitLab (HTTPS)

```hcl
# Public GitLab repo
module "vpc" {
  source = "git::https://gitlab.com/myorg/terraform-modules.git//modules/vpc?ref=v1.0.0"
}

# Private GitLab repo (uses GITLAB_TOKEN or git credentials)
module "vpc" {
  source = "git::https://oauth2:${var.gitlab_token}@gitlab.com/myorg/terraform-modules.git//modules/vpc?ref=v1.0.0"
}
```

### Source 7: GitLab (SSH)

```hcl
module "vpc" {
  source = "git@gitlab.com:myorg/terraform-modules.git//modules/vpc?ref=v1.0.0"
}
```

### Source 8: Generic Git Repository

```hcl
# Any Git server
module "vpc" {
  source = "git::https://git.example.com/modules.git//vpc?ref=v1.0.0"
}

# Bitbucket
module "vpc" {
  source = "git::https://bitbucket.org/myorg/terraform-modules.git?ref=main"
}
```

### Source 9: S3 Bucket

```hcl
module "vpc" {
  source = "s3::https://s3-eu-west-1.amazonaws.com/my-modules/vpc.zip"
}
```

### Source 10: Subdirectory of a Mono-Repo

Use `//` to specify a subdirectory within a repository:

```hcl
# GitHub mono-repo subdirectory
module "vpc" {
  source = "github.com/myorg/infra-modules//modules/vpc?ref=v2.0.0"
}

# GitLab mono-repo subdirectory
module "database" {
  source = "git::https://gitlab.com/myorg/infra-modules.git//modules/database?ref=v1.0.0"
}
```

### Module Source Quick Reference

```
┌──────────────────────┬──────────────────────────────────────────────────────┐
│ Source Type           │ Example                                              │
├──────────────────────┼──────────────────────────────────────────────────────┤
│ Same folder           │ source = "./modules/vpc"                            │
│ Parent folder         │ source = "../shared-modules/vpc"                    │
│ Terraform Registry    │ source = "terraform-aws-modules/vpc/aws"            │
│ GitHub (HTTPS)        │ source = "github.com/org/repo?ref=v1.0"            │
│ GitHub (SSH)          │ source = "git@github.com:org/repo.git?ref=v1.0"    │
│ GitLab (HTTPS)        │ source = "git::https://gitlab.com/org/repo.git"    │
│ GitLab (SSH)          │ source = "git@gitlab.com:org/repo.git"             │
│ Bitbucket             │ source = "git::https://bitbucket.org/org/repo.git" │
│ S3 Bucket             │ source = "s3::https://s3.../bucket/module.zip"     │
│ Mono-repo subfolder   │ source = "github.com/org/repo//modules/vpc"        │
└──────────────────────┴──────────────────────────────────────────────────────┘
```

> The `?ref=` parameter pins to a Git tag, branch, or commit SHA. Always use it for stability.

---

## 10.5 Using Registry Modules

```hcl
# Using the official AWS VPC module from Terraform Registry
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

# Using the official AWS EC2 module
module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "5.5.0"

  name = "my-instance"

  instance_type          = "t3.micro"
  monitoring             = true
  vpc_security_group_ids = [module.security_group.security_group_id]
  subnet_id              = module.vpc.private_subnets[0]

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}
```

```bash
terraform init
```

**Output:**
```
Initializing modules...
Downloading registry.terraform.io/terraform-aws-modules/vpc/aws 5.1.0 for vpc...
- vpc in .terraform/modules/vpc
Downloading registry.terraform.io/terraform-aws-modules/ec2-instance/aws 5.5.0 for ec2_instance...
- ec2_instance in .terraform/modules/ec2_instance
```

---

## 10.6 Module Composition Pattern

### Three-Tier Architecture

```
project/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── networking/
│   │   ├── main.tf        # VPC, subnets, NAT, routes
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/
│   │   ├── main.tf        # EC2, ALB, ASG, Launch Template
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── database/
│       ├── main.tf        # RDS, ElastiCache, parameter groups
│       ├── variables.tf
│       └── outputs.tf
```

```hcl
# main.tf — composing modules

module "networking" {
  source = "./modules/networking"

  vpc_cidr           = var.vpc_cidr
  environment        = var.environment
  availability_zones = var.availability_zones
}

module "compute" {
  source = "./modules/compute"

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids
  instance_type      = var.instance_type
  min_size           = var.min_instances
  max_size           = var.max_instances
  environment        = var.environment
}

module "database" {
  source = "./modules/database"

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  instance_class     = var.db_instance_class
  db_name            = var.db_name
  db_password        = var.db_password
  environment        = var.environment

  # Database needs compute security group for access
  allowed_security_groups = [module.compute.app_security_group_id]
}
```

---

## 10.7 Module Best Practices

| Practice | Why |
|----------|-----|
| Pin module versions | Prevent unexpected changes |
| Keep modules focused | One module = one concern |
| Use descriptive variable names | Self-documenting |
| Always provide outputs | Consumers need them |
| Don't hardcode provider config | Let the caller configure providers |
| Use `validation` blocks | Fail fast with clear errors |
| Include a README | Document inputs, outputs, and usage |
| Tag releases in Git | Stable references |

### Anti-Patterns

```hcl
# ❌ Don't configure providers inside modules
module "vpc" {
  source = "./modules/vpc"
  # Module should NOT contain provider blocks
}

# ❌ Don't use remote state inside modules
# Modules should receive data through variables, not fetch it themselves

# ❌ Don't make modules too granular
# A module for a single resource adds complexity without benefit

# ❌ Don't make modules too large
# A module with 50 resources is hard to understand and test
```

---

## 10.8 Building a Module from Scratch — S3 Static Website

Step-by-step example of creating a reusable module:

### Step 1: Module Directory Structure

```
project/
├── main.tf                    # Root module — calls the custom module
├── variables.tf
├── outputs.tf
└── modules/
    └── s3-static-website/     # Custom module
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Step 2: Module Code (`modules/s3-static-website/main.tf`)

```hcl
# S3 bucket for static website hosting
resource "aws_s3_bucket" "website" {
  bucket        = var.bucket_name
  tags          = var.tags
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id
  index_document { suffix = "index.html" }
  error_document { key = "error.html" }
}

resource "aws_s3_bucket_versioning" "website" {
  bucket = aws_s3_bucket.website.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id
  rule { object_ownership = "BucketOwnerPreferred" }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket                  = aws_s3_bucket.website.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.website.arn}/*"
    }]
  })

  depends_on = [aws_s3_bucket_public_access_block.website]
}
```

### Step 3: Module Variables (`modules/s3-static-website/variables.tf`)

```hcl
variable "bucket_name" {
  description = "Globally unique S3 bucket name"
  type        = string
}

variable "tags" {
  description = "Tags for the bucket"
  type        = map(string)
  default     = {}
}
```

### Step 4: Module Outputs (`modules/s3-static-website/outputs.tf`)

```hcl
output "bucket_id" {
  description = "Bucket name"
  value       = aws_s3_bucket.website.id
}

output "bucket_arn" {
  description = "Bucket ARN"
  value       = aws_s3_bucket.website.arn
}

output "website_endpoint" {
  description = "S3 static website URL"
  value       = aws_s3_bucket_website_configuration.website.website_endpoint
}

output "website_url" {
  description = "Full website URL"
  value       = "http://${aws_s3_bucket_website_configuration.website.website_endpoint}"
}
```

### Step 5: Use the Module (`main.tf`)

```hcl
module "website" {
  source      = "./modules/s3-static-website"
  bucket_name = "my-company-website-${random_id.suffix.hex}"
  tags = {
    Environment = "production"
    Project     = "company-website"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

output "website_url" {
  value = module.website.website_url
}
```

```bash
terraform init && terraform apply
```

**Output:**
```
module.website.aws_s3_bucket.website: Creating...
module.website.aws_s3_bucket.website: Creation complete [id=my-company-website-a1b2c3d4]
module.website.aws_s3_bucket_website_configuration.website: Creating...
module.website.aws_s3_bucket_versioning.website: Creating...
module.website.aws_s3_bucket_public_access_block.website: Creating...
...

Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

website_url = "http://my-company-website-a1b2c3d4.s3-website-us-east-1.amazonaws.com"
```

### Using Local Copies of Registry Modules

If your organization blocks access to the Terraform Registry, download modules locally:

```bash
# Download the VPC module from the registry
git clone https://github.com/terraform-aws-modules/terraform-aws-vpc.git modules/aws-vpc
```

```hcl
# Use the local copy instead of the registry
module "vpc" {
  source = "./modules/aws-vpc"   # Local path, no version needed
  # version = "5.0.0"            # Comment out — not used with local source

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  # ...
}
```

---

## 10.9 Common Errors

### Error: Module Not Found

```
Error: Module not installed

  on main.tf line 1:
   1: module "vpc" {

This module is not yet installed. Run "terraform init" to install all
modules required by this configuration.
```

**Fix:** Run `terraform init`.

### Error: Missing Required Variable

```
Error: Missing required argument

  on main.tf line 1, in module "vpc":
   1: module "vpc" {

The argument "vpc_name" is required, but no definition was found.
```

**Fix:** Add the missing variable to the module call.

### Error: Output Not Declared

```
Error: Unsupported attribute

  on main.tf line 10:
  10:   subnet_id = module.vpc.subnet_id

This object has no argument, nested block, or exported attribute
named "subnet_id". Did you mean "public_subnet_ids"?
```

**Fix:** Check the module's `outputs.tf` for available output names.

---

## 10.10 Scalable Module Registry

A module registry enables teams to share, discover, and consume reusable modules across projects and environments.

### Mono-Repo vs Poly-Repo

There are two common patterns for organizing module repositories:

```
Option 1: Mono-Repo                    Option 2: Poly-Repo
─────────────────────                  ─────────────────────
terraform-modules/                     terraform-vpc/       (own repo)
├── vpc/                               terraform-ec2/       (own repo)
├── ec2/                               terraform-alb/       (own repo)
├── rds/                               terraform-eks/       (own repo)
└── alb/
```

| Aspect | Mono-Repo | Poly-Repo |
|--------|-----------|-----------|
| Versioning | All modules share one version | Each module versioned independently |
| CI/CD | Single pipeline | Separate pipeline per module |
| Ownership | Shared | Team-level ownership |
| Best for | Small teams | Large organizations |

### Publishing to the Terraform Registry

**Public Registry** — host your module on GitHub with the naming convention `terraform-<PROVIDER>-<NAME>`:

```hcl
# Consuming a public registry module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"
}
```

**Private Registry** — use Terraform Cloud or Terraform Enterprise:

```hcl
# Consuming a private registry module
module "vpc" {
  source  = "app.terraform.io/my-org/vpc/aws"
  version = "1.2.3"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"
}
```

### Auto-Generating Module Documentation with terraform-docs

```bash
# Install terraform-docs
brew install terraform-docs

# Generate markdown documentation from your module
terraform-docs markdown table ./modules/vpc > modules/vpc/README.md
```

**Sample output:**

```markdown
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| cidr_block | CIDR block for the VPC | `string` | n/a | yes |
| name | Name tag for the VPC | `string` | n/a | yes |
| enable_dns | Enable DNS support | `bool` | `true` | no |
```

### Real-Life Use Case

A platform team maintains a private registry with approved modules for VPC, EKS, RDS, and S3. Application teams consume these modules without needing to understand the underlying resource configuration. When the platform team updates a module (e.g., adds encryption defaults), all consumers get the improvement on their next version bump.

---

## 10.11 Module Versioning and Upgrades Without Downtime

### Version Control with Git Tags

Use semantic versioning with Git tags to version your modules:

```bash
# Tag a stable release
git tag v1.0.0
git push origin v1.0.0

# Minor feature addition
git tag v1.1.0
git push origin v1.1.0

# Breaking change
git tag v2.0.0
git push origin v2.0.0
```

Pin the version in your consuming configuration:

```hcl
module "vpc" {
  source = "git::https://github.com/org/terraform-vpc.git?ref=v1.0.0"

  name       = "prod-vpc"
  cidr_block = "10.0.0.0/16"
}
```

> ⚠️ Never reference `main` or `master` in production. Always pin to a specific tag.

### Safe Upgrade Strategy

```bash
# Step 1: Update the module version in source
# source = "git::https://github.com/org/terraform-vpc.git?ref=v1.1.0"

# Step 2: Re-fetch the module
terraform get -update

# Step 3: Preview changes
terraform plan

# Step 4: Apply only if the plan shows no unexpected resource destruction
terraform apply
```

**Sample `terraform plan` output after a safe upgrade:**

```
module.vpc.aws_vpc.this: Refreshing state... [id=vpc-0abc123]

No changes. Your infrastructure matches the configuration.
```

### Blue-Green Module Rollouts

Deploy two versions of infrastructure side by side, test the new one, then switch traffic:

```hcl
# Blue (current production)
module "vpc_blue" {
  source = "git::https://github.com/org/terraform-vpc.git?ref=v1.0.0"
  name   = "prod-vpc-blue"
  cidr_block = "10.0.0.0/16"
}

# Green (new version under test)
module "vpc_green" {
  source = "git::https://github.com/org/terraform-vpc.git?ref=v1.1.0"
  name   = "prod-vpc-green"
  cidr_block = "10.1.0.0/16"
}
```

**Workflow:** Deploy both → test green → switch traffic via Route 53 or ALB → destroy blue.

### Canary Module Rollouts

Upgrade one region or environment first, validate, then roll out to the rest:

```hcl
# Canary region — upgraded first
module "vpc_ap_south_1" {
  source = "git::https://github.com/org/terraform-vpc.git?ref=v1.1.0"
  name   = "vpc-ap-south-1"
}

# Production region — stays on old version until canary is validated
module "vpc_us_east_1" {
  source = "git::https://github.com/org/terraform-vpc.git?ref=v1.0.0"
  name   = "vpc-us-east-1"
}
```

### Real-Life Use Case

A fintech company runs infrastructure across 3 regions. When upgrading their VPC module to add IPv6 support, they first deploy v2.0.0 to `ap-south-1` (lowest traffic). After 48 hours of monitoring with no issues, they upgrade `eu-west-1`, then finally `us-east-1`. This staged approach prevents a global outage from a module regression.

---

## 10.12 Terraform Composition: Layered Design Patterns

### Layered Module Structure

Design infrastructure as logical tiers where each layer builds on the previous:

```
┌──────────────────────┐
│  Application Layer   │  (App-specific resources)
├──────────────────────┤
│  Services Layer      │  (RDS, ElastiCache, SQS)
├──────────────────────┤
│  Compute Layer       │  (EKS, EC2, ASG, Lambda)
├──────────────────────┤
│  Networking Layer    │  (VPC, Subnets, NAT, IGW)
└──────────────────────┘
```

**Directory structure:**

```
terraform/
├── layers/
│   ├── networking/
│   │   └── main.tf        # Calls modules/vpc
│   ├── compute/
│   │   └── main.tf        # Calls modules/eks, references networking outputs
│   ├── services/
│   │   └── main.tf        # Calls modules/rds, references compute outputs
│   └── application/
│       └── main.tf
├── modules/
│   ├── vpc/
│   ├── eks/
│   └── rds/
└── environments/
    ├── dev/
    │   └── main.tf        # Composes layers with dev-specific variables
    └── prod/
        └── main.tf        # Composes layers with prod-specific variables
```

### Wrapper Modules

Wrap external modules with organization-specific defaults:

```hcl
# modules/org-vpc/main.tf
# Wraps the community VPC module with company standards

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = var.name
  cidr = var.cidr

  enable_dns_hostnames = true
  enable_dns_support   = true

  # Organization-wide defaults
  tags = merge(var.tags, {
    ManagedBy = "terraform"
    Owner     = "platform-team"
    CostCenter = var.cost_center
  })
}
```

This ensures all teams inherit consistent tagging, naming, and security settings.

### Nested Modules

One module calls multiple inner modules to compose behavior:

```hcl
# modules/network/main.tf
# Abstracts VPC + subnets + NAT into a single interface

module "vpc" {
  source     = "../vpc"
  cidr_block = var.cidr_block
  name       = var.name
}

module "subnets" {
  source = "../subnets"
  vpc_id = module.vpc.vpc_id
  azs    = var.availability_zones
}

module "nat" {
  source    = "../nat"
  subnet_id = module.subnets.public_subnet_ids[0]
}
```

Consumers call `module "network"` instead of managing three separate modules.

### Multi-Provider Modules

Inject providers from outside the module for multi-region or multi-cloud deployments:

```hcl
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "aws" {
  alias  = "eu_west_1"
  region = "eu-west-1"
}

module "s3_logs_us" {
  source = "./modules/s3"
  providers = {
    aws = aws.us_east_1
  }
  bucket_name = "logs-us-east-1"
}

module "s3_logs_eu" {
  source = "./modules/s3"
  providers = {
    aws = aws.eu_west_1
  }
  bucket_name = "logs-eu-west-1"
}
```

### Real-Life Use Case

A SaaS company uses layered composition to manage 50+ microservices. The networking layer is owned by the platform team and deployed once per environment. The compute layer (EKS) is shared across services. Each microservice team only manages their application layer, calling shared modules for databases and caches. Changes to the VPC module propagate through layers without requiring each team to update their code.

---

## Exercises

### Exercise 10.1: Create a Module
Build a reusable security group module that accepts a list of ingress rules and creates the security group.

### Exercise 10.2: Use a Registry Module
Use the `terraform-aws-modules/vpc/aws` module to create a VPC with 3 public and 3 private subnets.

### Exercise 10.3: Module Composition
Create a three-tier architecture using separate modules for networking, compute, and database layers.

### Exercise 10.4: Module with for_each
Create a module that deploys an S3 bucket with configurable settings, then use `for_each` to create buckets for dev, staging, and prod.

### Exercise 10.5: Module Versioning
Create a module in a Git repository, tag it as v1.0.0, consume it in a project, then add a feature, tag v1.1.0, and upgrade the consumer safely.

### Exercise 10.6: Wrapper Module
Wrap the `terraform-aws-modules/vpc/aws` module with your organization's default tags and naming conventions.

---

## Key Takeaways

- Modules are reusable containers for related resources
- Every Terraform project is a root module
- Use `source` to reference local paths, Git repos, or the Terraform Registry
- Pin module versions for stability
- Pass data between modules through variables and outputs
- Use `for_each` to create multiple instances of a module
- Keep modules focused on a single concern
- Organize modules in mono-repo (small teams) or poly-repo (large orgs) structures
- Use `terraform-docs` to auto-generate module documentation
- Version modules with semantic Git tags — never reference `main` in production
- Blue-green and canary rollouts reduce risk when upgrading modules
- Layered composition (networking → compute → services → application) enforces separation of concerns
- Wrapper modules enforce organization-wide defaults on top of community modules

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Modules Overview | [developer.hashicorp.com/terraform/language/modules](https://developer.hashicorp.com/terraform/language/modules) |
| Module Syntax | [developer.hashicorp.com/terraform/language/modules/syntax](https://developer.hashicorp.com/terraform/language/modules/syntax) |
| Module Sources | [developer.hashicorp.com/terraform/language/modules/sources](https://developer.hashicorp.com/terraform/language/modules/sources) |
| Local Paths | [developer.hashicorp.com/terraform/language/modules/sources#local-paths](https://developer.hashicorp.com/terraform/language/modules/sources#local-paths) |
| GitHub Source | [developer.hashicorp.com/terraform/language/modules/sources#github](https://developer.hashicorp.com/terraform/language/modules/sources#github) |
| S3 Bucket Source | [developer.hashicorp.com/terraform/language/modules/sources#s3-bucket](https://developer.hashicorp.com/terraform/language/modules/sources#s3-bucket) |
| Generic Git Repository | [developer.hashicorp.com/terraform/language/modules/sources#generic-git-repository](https://developer.hashicorp.com/terraform/language/modules/sources#generic-git-repository) |
| Module Development | [developer.hashicorp.com/terraform/language/modules/develop](https://developer.hashicorp.com/terraform/language/modules/develop) |
| Module Composition | [developer.hashicorp.com/terraform/language/modules/develop/composition](https://developer.hashicorp.com/terraform/language/modules/develop/composition) |
| Publishing Modules | [developer.hashicorp.com/terraform/registry/modules/publish](https://developer.hashicorp.com/terraform/registry/modules/publish) |
| Terraform Registry — Browse Modules | [registry.terraform.io/browse/modules](https://registry.terraform.io/browse/modules) |
| AWS VPC Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest) |
| AWS EC2 Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/ec2-instance/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/ec2-instance/aws/latest) |
| AWS EKS Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest) |
| `terraform get` | [developer.hashicorp.com/terraform/cli/commands/get](https://developer.hashicorp.com/terraform/cli/commands/get) |

---

[← Previous Module](../module-09-remote-state-and-backends/README.md) | [Next Module: Workspaces →](../module-11-workspaces-and-environments/README.md)
