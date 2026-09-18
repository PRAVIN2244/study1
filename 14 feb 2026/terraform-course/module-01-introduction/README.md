# Module 1: Introduction to Terraform

## Level: BASIC | Estimated Time: 2 hours

---

## 1.1 Why Not Manual Infrastructure?

Managing infrastructure manually (clicking through the AWS Console) has serious problems:

| Problem | Example |
|---------|---------|
| **Prone to errors** | Launch 10 EC2 instances manually → accidentally choose wrong AMI, forget a security group |
| **Not scalable** | Creating 100 servers by clicking is impractical. With Terraform: `count = 100` — done |
| **Not version controlled** | Manual changes can't be tracked. Terraform code: `git commit -m "Added 3 EC2 instances"` |
| **Not reproducible** | Recreating the same setup from memory leads to inconsistencies |
| **Not cloud agnostic** | Console skills for AWS don't transfer to Azure or GCP |

### What is IaC (Infrastructure as Code)?

IaC solves these problems by treating infrastructure like software:

- **Desired state as code** — you describe what you want in a file, Terraform makes it real
- **Version the code** — track every change with Git
- **Review and reuse** — code review before deploying, reuse modules across projects

---

## 1.2 What is Terraform?

Terraform is an **Infrastructure as Code (IaC)** tool created by HashiCorp. It lets you define cloud and on-premises resources in human-readable configuration files that you can version, reuse, and share.

**How it works:** You describe the desired state. Terraform compares it to the actual state (what exists in AWS). Then it fixes the differences — creating, updating, or deleting resources as needed.

### Key Characteristics

| Feature | Description |
|---------|-------------|
| **Declarative** | You describe the desired end state, not the steps to get there |
| **Cloud-Agnostic** | Works with AWS, Azure, GCP, and 3000+ providers |
| **State-Aware** | Tracks real infrastructure in a state file |
| **Plan Before Apply** | Shows you what will change before making changes |
| **Idempotent** | Running the same config multiple times produces the same result |

### How Terraform Differs from Other Tools

```
┌─────────────────────────────────────────────────────────────────┐
│                    IaC Tool Comparison                          │
├──────────────┬──────────────┬───────────────┬──────────────────┤
│   Feature    │  Terraform   │ CloudFormation│    Ansible       │
├──────────────┼──────────────┼───────────────┼──────────────────┤
│ Approach     │ Declarative  │ Declarative   │ Procedural       │
│ Cloud        │ Multi-cloud  │ AWS only      │ Multi-cloud      │
│ Language     │ HCL          │ JSON/YAML     │ YAML             │
│ State        │ Yes          │ Yes (managed) │ No               │
│ Dry Run      │ terraform plan│ Change sets  │ --check mode     │
│ Agent        │ Agentless    │ Agentless     │ Agentless (SSH)  │
└──────────────┴──────────────┴───────────────┴──────────────────┘
```

### Terraform vs Ansible — Detailed Comparison

Terraform and Ansible are both DevOps tools but operate at different layers:

```
┌──────────────────────┬──────────────────────────┬──────────────────────────┐
│                      │       Terraform          │        Ansible           │
├──────────────────────┼──────────────────────────┼──────────────────────────┤
│ Primary purpose      │ Infrastructure           │ Configuration management │
│                      │ provisioning (IaC)       │ & app deployment         │
│                      │                          │                          │
│ What it manages      │ Cloud resources:         │ Software on servers:     │
│                      │ VPCs, EC2, RDS, S3,      │ packages, files,         │
│                      │ load balancers           │ services, users          │
│                      │                          │                          │
│ Language             │ HCL (declarative)        │ YAML playbooks           │
│                      │                          │ (procedural)             │
│                      │                          │                          │
│ State tracking       │ Yes (tfstate file)       │ No state file            │
│                      │                          │                          │
│ Execution model      │ Builds dependency graph, │ Runs tasks top-to-bottom │
│                      │ parallel where possible  │ in order                 │
│                      │                          │                          │
│ Idempotent           │ Yes (by design)          │ Yes (if tasks written    │
│                      │                          │ correctly)               │
│                      │                          │                          │
│ Agent required       │ No                       │ No (uses SSH/WinRM)      │
│                      │                          │                          │
│ Dry run              │ terraform plan           │ ansible-playbook --check │
│                      │                          │                          │
│ Cloud provider       │ 3000+ providers          │ Cloud modules available  │
│ support              │ (native API integration) │ (but not primary focus)  │
│                      │                          │                          │
│ Best for             │ "Create the server"      │ "Configure the server"   │
└──────────────────────┴──────────────────────────┴──────────────────────────┘
```

**How they work together in practice:**

```
Step 1: Terraform creates the infrastructure
        → VPC, subnets, EC2 instances, RDS, load balancers

Step 2: Ansible configures the servers
        → Install packages, deploy app, configure nginx, set up monitoring
```

```bash
# Terraform creates the server
terraform apply

# Ansible configures it
ansible-playbook -i "$(terraform output -raw instance_ip)," setup.yml
```

---

## 1.3 Terraform Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    YOUR MACHINE                          │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  .tf files   │───▶│  Terraform   │                   │
│  │ (HCL Config) │    │    Core       │                   │
│  └──────────────┘    └──────┬───────┘                   │
│                             │                            │
│  ┌──────────────┐    ┌──────▼───────┐                   │
│  │ State File   │◀──▶│  Providers   │                   │
│  │ (.tfstate)   │    │ (Plugins)    │                   │
│  └──────────────┘    └──────┬───────┘                   │
│                             │                            │
└─────────────────────────────┼────────────────────────────┘
                              │ API Calls
                    ┌─────────▼─────────┐
                    │   Cloud Provider   │
                    │  (AWS, Azure, GCP) │
                    └───────────────────┘
```

### Components Explained

1. **Terraform Core**: The binary that reads configs, builds dependency graphs, and executes plans
2. **Configuration Files (.tf)**: Your infrastructure definitions written in HCL
3. **Providers**: Plugins that translate HCL into API calls for specific platforms
4. **State File**: A JSON file that maps your config to real-world resources
5. **Backend**: Where the state file is stored (local disk or remote like S3)

---

## 1.4 The Terraform Workflow

```
   Write          Plan           Apply          Destroy
  ┌──────┐     ┌──────┐      ┌──────┐       ┌──────┐
  │ .tf  │────▶│ plan │─────▶│apply │──...──▶│destroy│
  │files │     │      │      │      │       │       │
  └──────┘     └──────┘      └──────┘       └──────┘
     │            │              │               │
     ▼            ▼              ▼               ▼
  Define       Preview       Create/          Tear down
  desired      changes       Update           everything
  state                      resources
```

### Core Commands

```bash
# Initialize - downloads providers and sets up backend
terraform init

# Format - auto-formats your .tf files
terraform fmt

# Validate - checks syntax without accessing any remote services
terraform validate

# Plan - preview what Terraform will do (DRY RUN)
terraform plan

# Apply - execute the plan and create/modify resources
terraform apply

# Destroy - tear down all managed resources
terraform destroy
```

---

## 1.5 Installation

### Linux (Ubuntu/Debian)

```bash
# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add the repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install
sudo apt update && sudo apt install terraform

# Verify
terraform version
```

**Expected Output:**
```
Terraform v1.9.x
on linux_amd64
```

### macOS

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version
```

### Windows

```powershell
choco install terraform
terraform version
```

### Installing a Specific Version (Any OS)

```bash
# Download a specific version from the releases page
curl -O https://releases.hashicorp.com/terraform/1.9.0/terraform_1.9.0_linux_amd64.zip

# Install unzip if needed
sudo apt install -y unzip

# Extract directly to a PATH directory
sudo unzip terraform_1.9.0_linux_amd64.zip -d /usr/local/bin/

# Verify
terraform version
```

**Expected Output:**
```
Terraform v1.9.0
on linux_amd64
```

### Creating a Symlink (When Installed to a Non-PATH Location)

If Terraform is installed to `/usr/bin/terraform` but your scripts expect `/usr/local/bin/terraform`:

```bash
sudo ln -s /usr/bin/terraform /usr/local/bin/terraform
```

### Setting the Hostname (Optional, for Lab Environments)

```bash
# Set a meaningful hostname for your Terraform workstation
sudo hostnamectl set-hostname terraform-workstation
```

---

## 1.6 AWS CLI Setup (Required for This Course)

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
sudo apt install unzip && unzip awscliv2.zip
sudo ./aws/install --bin-dir /usr/bin --install-dir /usr/bin/aws-cli --update

# Verify installation
aws --version
```

**Expected Output:**
```
aws-cli/2.15.0 Python/3.11.6 Linux/5.15.0 exe/x86_64.ubuntu.22
```

```bash
# Configure credentials
aws configure
```

**Interactive Prompts:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

This creates a credentials file at `~/.aws/credentials`:

```ini
# ~/.aws/credentials
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

And a config file at `~/.aws/config`:

```ini
# ~/.aws/config
[default]
region = us-east-1
output = json
```

### Two Ways to Pass Credentials to Terraform

```bash
# Method 1: Environment variables (temporary, per-session)
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
```

Verify environment variables are set:

```bash
env | grep AWS
```

**Expected Output:**
```
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

```bash
# Method 2: Credentials file (persistent, created by `aws configure`)
# Terraform automatically reads ~/.aws/credentials — no extra config needed
```

> ⚠️ **Never hardcode credentials in `.tf` files or commit them to Git.**

**Verify:**
```bash
aws sts get-caller-identity
```

**Expected Output:**
```json
{
    "UserId": "AIDAEXAMPLEID",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/terraform-user"
}
```

### IAM Policy for Terraform User (Minimum for this course)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "s3:*",
                "iam:*",
                "rds:*",
                "dynamodb:*",
                "lambda:*",
                "vpc:*",
                "elasticloadbalancing:*",
                "autoscaling:*",
                "route53:*",
                "cloudwatch:*",
                "sns:*",
                "sqs:*"
            ],
            "Resource": "*"
        }
    ]
}
```

> ⚠️ **Warning**: In production, use least-privilege policies. This broad policy is for learning only.

---

## 1.7 Your First Terraform Command

Create a directory and run `terraform init` to see how Terraform initializes:

```bash
mkdir my-first-terraform && cd my-first-terraform
```

Create a minimal config file:

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
}
```

```bash
terraform init
```

**Expected Output:**
```
Initializing the backend...

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure.

If you ever set the value of a variable in the configuration to an expression
that depends on a resource attribute, Terraform will not be able to determine
the value until apply time.
```

```bash
terraform plan
```

**Expected Output:**
```
No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

---

## 1.8 Understanding the .terraform Directory

After `terraform init`, a `.terraform` directory is created:

```
my-first-terraform/
├── .terraform/
│   └── providers/          # Downloaded provider plugins
├── .terraform.lock.hcl     # Dependency lock file (commit this!)
└── main.tf                 # Your configuration
```

| File/Directory | Purpose | Version Control? |
|---|---|---|
| `.terraform/` | Provider binaries, module cache | **NO** (add to .gitignore) |
| `.terraform.lock.hcl` | Locks provider versions | **YES** |
| `*.tf` | Configuration files | **YES** |
| `*.tfstate` | State file | **NO** (use remote backend) |
| `*.tfvars` | Variable values | **DEPENDS** (no secrets) |

---

## 1.9 Real-Life Scenario: Why Terraform?

### Without Terraform (Manual Process)

```
Day 1: Developer opens AWS Console
       → Creates VPC manually
       → Creates subnets manually
       → Creates EC2 instance manually
       → Forgets to document security group rules

Day 30: Another developer needs the same setup
        → "How did you configure that?"
        → Spends 2 days recreating from memory
        → Configuration drift begins

Day 90: Audit reveals inconsistencies
        → Production has different config than staging
        → No one knows what changed or when
```

### With Terraform

```
Day 1: Developer writes main.tf
       → terraform plan (review)
       → terraform apply (deploy)
       → Code is committed to Git

Day 30: Another developer clones the repo
        → terraform apply
        → Identical infrastructure in minutes

Day 90: Audit checks Git history
        → Every change is tracked
        → Production matches code exactly
```

---

## Exercises

### Exercise 1.1: Install and Verify
1. Install Terraform on your machine
2. Run `terraform version` and note the output
3. Run `terraform -help` and identify 5 commands you'll use most

### Exercise 1.2: Explore the CLI
```bash
# Try these commands and observe the output
terraform -help
terraform init -help
terraform plan -help
terraform apply -help
terraform fmt -help
```

### Exercise 1.3: Initialize a Project
1. Create a new directory called `exercise-01`
2. Create an empty `main.tf` file
3. Run `terraform init`
4. Examine the files created
5. Run `terraform plan` and observe the output

---

## Key Takeaways

- Terraform is a declarative IaC tool that manages infrastructure through configuration files
- The core workflow is: **Write → Init → Plan → Apply**
- State files track the mapping between your config and real resources
- Always version control your `.tf` files and `.terraform.lock.hcl`
- Never version control `.terraform/` directory or state files

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| What is Terraform? | [developer.hashicorp.com/terraform/intro](https://developer.hashicorp.com/terraform/intro) |
| Install Terraform | [developer.hashicorp.com/terraform/install](https://developer.hashicorp.com/terraform/install) |
| Terraform CLI | [developer.hashicorp.com/terraform/cli](https://developer.hashicorp.com/terraform/cli) |
| Core Workflow (Write, Plan, Apply) | [developer.hashicorp.com/terraform/intro/core-workflow](https://developer.hashicorp.com/terraform/intro/core-workflow) |
| Use Cases | [developer.hashicorp.com/terraform/intro/use-cases](https://developer.hashicorp.com/terraform/intro/use-cases) |
| `terraform init` | [developer.hashicorp.com/terraform/cli/commands/init](https://developer.hashicorp.com/terraform/cli/commands/init) |
| `terraform plan` | [developer.hashicorp.com/terraform/cli/commands/plan](https://developer.hashicorp.com/terraform/cli/commands/plan) |
| `terraform apply` | [developer.hashicorp.com/terraform/cli/commands/apply](https://developer.hashicorp.com/terraform/cli/commands/apply) |
| `terraform destroy` | [developer.hashicorp.com/terraform/cli/commands/destroy](https://developer.hashicorp.com/terraform/cli/commands/destroy) |
| `terraform fmt` | [developer.hashicorp.com/terraform/cli/commands/fmt](https://developer.hashicorp.com/terraform/cli/commands/fmt) |
| `terraform validate` | [developer.hashicorp.com/terraform/cli/commands/validate](https://developer.hashicorp.com/terraform/cli/commands/validate) |
| Dependency Lock File (.terraform.lock.hcl) | [developer.hashicorp.com/terraform/language/files/dependency-lock](https://developer.hashicorp.com/terraform/language/files/dependency-lock) |
| AWS Provider | [registry.terraform.io/providers/hashicorp/aws/latest/docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) |
| AWS CLI Configuration | [docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) |

---

[Next Module: HCL Syntax →](../module-02-hcl-syntax/README.md)
