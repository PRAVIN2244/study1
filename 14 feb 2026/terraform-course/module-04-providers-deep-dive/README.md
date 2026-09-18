# Module 4: Providers Deep Dive

## Level: INTERMEDIATE | Estimated Time: 2 hours

---

## 4.1 What Are Providers?

Providers are plugins that Terraform uses to interact with APIs. Each provider adds a set of resource types and data sources.

```
┌──────────────────────────────────────────────────────┐
│                  Terraform Core                       │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │  AWS     │  │  Azure  │  │  GCP    │  │ Custom │ │
│  │Provider  │  │Provider │  │Provider │  │Provider│ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └───┬────┘ │
└───────┼────────────┼────────────┼────────────┼──────┘
        │            │            │            │
   ┌────▼────┐  ┌────▼────┐  ┌───▼─────┐  ┌──▼──────┐
   │ AWS API │  │Azure API│  │ GCP API │  │Custom API│
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

---

## 4.2 Provider Configuration

### Basic Configuration

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"    # Registry path: namespace/name
      version = "~> 5.0"           # Version constraint
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

### Provider Source Addresses

```
hashicorp/aws          → registry.terraform.io/hashicorp/aws
hashicorp/azurerm      → registry.terraform.io/hashicorp/azurerm
hashicorp/google       → registry.terraform.io/hashicorp/google
integrations/github    → registry.terraform.io/integrations/github
cloudflare/cloudflare  → registry.terraform.io/cloudflare/cloudflare
```

### Authentication Methods (AWS)

```hcl
# Method 1: Static credentials (NEVER do this in production)
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"       # ❌ Don't hardcode
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPx"  # ❌ Don't hardcode
}

# Method 2: Environment variables (recommended for local dev)
# export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
# export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPx"
# export AWS_DEFAULT_REGION="us-east-1"
provider "aws" {
  region = "us-east-1"
  # Credentials picked up automatically from environment
}

# Method 3: Shared credentials file (~/.aws/credentials)
provider "aws" {
  region  = "us-east-1"
  profile = "my-project"  # Uses [my-project] profile
}

# Method 4: IAM Role (recommended for EC2/ECS/Lambda)
provider "aws" {
  region = "us-east-1"
  # Automatically uses instance profile / task role
}

# Method 5: Assume Role (cross-account access)
provider "aws" {
  region = "us-east-1"
  assume_role {
    role_arn     = "arn:aws:iam::987654321098:role/TerraformRole"
    session_name = "terraform-session"
    external_id  = "my-external-id"
  }
}
```

---

## 4.3 Multiple Provider Configurations (Aliases)

Deploy resources to multiple regions or accounts:

```hcl
# Default provider (no alias)
provider "aws" {
  region = "us-east-1"
}

# Aliased provider for another region
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

# Aliased provider for another account
provider "aws" {
  alias  = "production"
  region = "us-east-1"
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/TerraformRole"
  }
}

# Use default provider
resource "aws_s3_bucket" "east_bucket" {
  bucket = "my-app-east-bucket"
}

# Use aliased provider
resource "aws_s3_bucket" "west_bucket" {
  provider = aws.west
  bucket   = "my-app-west-bucket"
}

# Use production account provider
resource "aws_s3_bucket" "prod_bucket" {
  provider = aws.production
  bucket   = "my-app-prod-bucket"
}
```

### Real-Life Example: Multi-Region Disaster Recovery

```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "dr"
  region = "us-west-2"
}

# Primary database
resource "aws_rds_cluster" "primary" {
  cluster_identifier = "myapp-primary"
  engine             = "aurora-mysql"
  master_username    = "admin"
  master_password    = var.db_password
}

# DR replica in another region
resource "aws_rds_cluster" "replica" {
  provider = aws.dr

  cluster_identifier            = "myapp-replica"
  engine                        = "aurora-mysql"
  replication_source_identifier = aws_rds_cluster.primary.arn
}
```

---

## 4.4 Provider Version Locking

### The Lock File (.terraform.lock.hcl)

After `terraform init`, a lock file is created:

```hcl
# .terraform.lock.hcl (auto-generated, DO commit this)
provider "registry.terraform.io/hashicorp/aws" {
  version     = "5.31.0"
  constraints = "~> 5.0"
  hashes = [
    "h1:abc123...",
    "zh:def456...",
  ]
}
```

### Upgrading Providers

```bash
# Upgrade within constraints
terraform init -upgrade

# Check current versions
terraform providers

# Show provider lock info
terraform providers lock
```

**Output of `terraform providers`:**
```
Providers required by configuration:
.
└── provider[registry.terraform.io/hashicorp/aws] ~> 5.0

Providers required by state:
    provider[registry.terraform.io/hashicorp/aws]
```

---

## 4.5 Using Multiple Providers

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Generate a random suffix for unique naming
resource "random_id" "suffix" {
  byte_length = 4
}

# Generate an SSH key pair
resource "tls_private_key" "ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save private key locally
resource "local_file" "ssh_key" {
  content         = tls_private_key.ssh.private_key_pem
  filename        = "${path.module}/ssh-key.pem"
  file_permission = "0600"
}

# Upload public key to AWS
resource "aws_key_pair" "deployer" {
  key_name   = "deployer-${random_id.suffix.hex}"
  public_key = tls_private_key.ssh.public_key_openssh
}

# Use the key pair with an EC2 instance
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  key_name      = aws_key_pair.deployer.key_name

  tags = {
    Name = "web-${random_id.suffix.hex}"
  }
}
```

---

## 4.6 Provider-Specific Features

### AWS Provider: Default Tags

```hcl
provider "aws" {
  region = "us-east-1"

  # These tags are automatically applied to ALL resources
  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Team        = "platform"
      CostCenter  = "CC-12345"
    }
  }
}

# This resource gets default_tags + its own tags
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "web-server"  # Merged with default_tags
  }
}
```

### AWS Provider: Ignoring Tags

```hcl
provider "aws" {
  region = "us-east-1"

  # Ignore tags set by external systems (e.g., AWS Config, Security Hub)
  ignore_tags {
    key_prefixes = ["aws:", "kubernetes.io/"]
    keys         = ["LastScannedBy", "ComplianceStatus"]
  }
}
```

---

## 4.7 Common Provider Errors

### Error: Provider Not Found

```
Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/awss: provider registry registry.terraform.io does not
have a provider named registry.terraform.io/hashicorp/awss
```

**Fix:** Check the provider name for typos. Use `terraform providers` to verify.

### Error: Version Constraint Conflict

```
Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/aws: no available releases match the given constraints
~> 3.0, ~> 5.0
```

**Fix:** Ensure all modules use compatible version constraints.

### Error: Provider Configuration Not Present

```
Error: Provider configuration not present

To work with aws_instance.web its original provider configuration
at provider["registry.terraform.io/hashicorp/aws"] is required,
but it has been removed.
```

**Fix:** Don't remove a provider block while resources using it still exist in state.

---

## Exercises

### Exercise 4.1: Multi-Region Setup
Create a configuration that deploys an S3 bucket in `us-east-1` and another in `eu-west-1` using provider aliases.

### Exercise 4.2: Multiple Providers
Use `aws`, `random`, and `local` providers together to create an EC2 instance with a random name suffix and save its details to a local file.

### Exercise 4.3: Assume Role
Write a provider configuration that assumes a role in another AWS account. (You don't need to apply it — just write valid HCL.)

---

## Key Takeaways

- Providers are plugins that connect Terraform to APIs
- Use version constraints (`~>`) to control provider upgrades
- Commit `.terraform.lock.hcl` to version control
- Use aliases for multi-region or multi-account deployments
- Never hardcode credentials — use environment variables, profiles, or IAM roles
- `default_tags` saves repetition across all resources

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Providers Overview | [developer.hashicorp.com/terraform/language/providers](https://developer.hashicorp.com/terraform/language/providers) |
| Provider Configuration | [developer.hashicorp.com/terraform/language/providers/configuration](https://developer.hashicorp.com/terraform/language/providers/configuration) |
| Provider Requirements (`required_providers`) | [developer.hashicorp.com/terraform/language/providers/requirements](https://developer.hashicorp.com/terraform/language/providers/requirements) |
| Provider Aliases (Multiple Configurations) | [developer.hashicorp.com/terraform/language/providers/configuration#alias-multiple-provider-configurations](https://developer.hashicorp.com/terraform/language/providers/configuration#alias-multiple-provider-configurations) |
| Version Constraints | [developer.hashicorp.com/terraform/language/expressions/version-constraints](https://developer.hashicorp.com/terraform/language/expressions/version-constraints) |
| Dependency Lock File | [developer.hashicorp.com/terraform/language/files/dependency-lock](https://developer.hashicorp.com/terraform/language/files/dependency-lock) |
| `terraform providers` Command | [developer.hashicorp.com/terraform/cli/commands/providers](https://developer.hashicorp.com/terraform/cli/commands/providers) |
| Terraform Registry — Browse Providers | [registry.terraform.io/browse/providers](https://registry.terraform.io/browse/providers) |
| AWS Provider Docs | [registry.terraform.io/providers/hashicorp/aws/latest/docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) |
| AWS Provider — Authentication | [registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#authentication-and-configuration) |
| AWS Provider — `default_tags` | [registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#default_tags) |
| AWS Provider — Assume Role | [registry.terraform.io/providers/hashicorp/aws/latest/docs#assuming-an-iam-role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#assuming-an-iam-role) |

---

[← Previous Module](../module-03-first-infrastructure/README.md) | [Next Module: Resources and Data Sources →](../module-05-resources-and-data-sources/README.md)
