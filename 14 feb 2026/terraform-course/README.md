# Terraform Complete Course: Basic → Advanced → Super Advanced

## AWS Cloud Examples | Command Outputs | Real-Life Scenarios

---

## Course Overview

An 18-module structured course covering every core Terraform concept. Each module includes:
- Concept explanations with diagrams
- AWS-based working examples
- Expected command outputs for every operation
- Common errors and how to fix them
- Real-life scenarios and best practices
- Hands-on exercises

### Prerequisites

- AWS account with admin access (or scoped IAM user)
- Terraform >= 1.6 installed
- AWS CLI v2 configured
- Basic command-line familiarity
- A code editor (VS Code recommended)

---

## Course Structure

### BASIC (Modules 1-3)

Start here if you're new to Terraform or Infrastructure as Code.

| # | Module | Topics | Time |
|---|--------|--------|------|
| 01 | [Introduction to Terraform](module-01-introduction/README.md) | What is IaC, Terraform architecture, installation, AWS CLI setup, first commands | 2h |
| 02 | [HCL Syntax Deep Dive](module-02-hcl-syntax/README.md) | Blocks, arguments, data types, operators, string interpolation, references, meta-arguments | 3h |
| 03 | [Building Your First Infrastructure](module-03-first-infrastructure/README.md) | VPC, subnets, security groups, EC2, full plan/apply/destroy workflow | 3h |

**After completing Basic:** You can create, modify, and destroy AWS resources with Terraform.

---

### INTERMEDIATE (Modules 4-9)

Core concepts every Terraform user must know.

| # | Module | Topics | Time |
|---|--------|--------|------|
| 04 | [Providers Deep Dive](module-04-providers-deep-dive/README.md) | Authentication, aliases, multi-region, version locking, multiple providers | 2h |
| 05 | [Resources and Data Sources](module-05-resources-and-data-sources/README.md) | CRUD behavior, count vs for_each, lifecycle rules, data sources, moved blocks | 3h |
| 06 | [Variables, Outputs, and Locals](module-06-variables-outputs-locals/README.md) | Variable types, precedence, validation, outputs, locals, environment patterns | 3h |
| 07 | [State Management](module-07-state-management/README.md) | State file structure, how state works, locking, drift detection, security | 3h |
| 08 | [State Commands and Operations](module-08-state-commands-and-operations/README.md) | state list/show/mv/rm, import, targeted operations, replace | 2h |
| 09 | [Remote State and Backends](module-09-remote-state-and-backends/README.md) | S3 backend, DynamoDB locking, remote state data source, backend migration | 3h |

**After completing Intermediate:** You can manage state remotely, use variables effectively, and work with existing infrastructure.

---

### ADVANCED (Modules 10-13)

Patterns for production-grade infrastructure.

| # | Module | Topics | Time |
|---|--------|--------|------|
| 10 | [Terraform Modules](module-10-modules/README.md) | Creating modules, registry modules, composition, for_each with modules, best practices, scalable module registry, module versioning with Git tags, blue-green/canary rollouts, layered design patterns, wrapper/nested modules | 4h |
| 11 | [Workspaces and Environments](module-11-workspaces-and-environments/README.md) | Workspaces, directory-based environments, comparison, Terragrunt overview | 2h |
| 12 | [Provisioners and Dynamic Blocks](module-12-provisioners-and-dynamic-blocks/README.md) | local-exec, remote-exec, file, dynamic blocks, nested dynamics, alternatives | 3h |
| 13 | [Expressions and Functions](module-13-expressions-and-functions/README.md) | For expressions, splat, 100+ built-in functions, templates, try/can | 3h |

**After completing Advanced:** You can build reusable modules, manage multiple environments, and use advanced HCL features.

---

### SUPER ADVANCED (Modules 14-18)

Enterprise patterns, automation, and real-world architecture.

| # | Module | Topics | Time |
|---|--------|--------|------|
| 14 | [Custom Providers and Plugins](module-14-custom-providers-and-plugins/README.md) | Provider internals, terraform-plugin-framework, building providers, external data source | 4h |
| 15 | [Testing and Validation](module-15-testing-and-validation/README.md) | terraform test, tflint, trivy/tfsec, checkov, Sentinel, OPA/Conftest, pre-commit | 3h |
| 16 | [CI/CD and Automation](module-16-cicd-and-automation/README.md) | GitHub Actions, GitLab CI, Atlantis, Terraform Cloud, drift detection, OIDC | 3h |
| 17 | [Real-World Projects](module-17-real-world-projects/README.md) | Three-tier web app, serverless API, EKS cluster (detailed provisioning with custom modules), GCP infrastructure scaling (MIG, Cloud SQL, Cloud Functions), Azure infrastructure scaling (VMSS, SQL Elastic Pool, Function Apps) | 5h |
| 18 | [Troubleshooting Guide](module-18-troubleshooting-guide/README.md) | Error reference, debugging, performance, common patterns, doctor checklist | Reference |
| 19 | [Expert-Level Topics](module-19-expert-level-topics/README.md) | `removed` block, `optional()` types, ephemeral resources, provider functions, mock testing, `check` blocks, provider mirrors, `-target`, `terraform graph`, all CLI flags, internals, performance tuning, zero-downtime deployments, rollback strategies, Terraform limitations | 5h |

**After completing Super Advanced:** You can build enterprise-grade infrastructure, automate deployments, enforce policies, and troubleshoot any issue.

---

## Total Estimated Time: ~55 hours

---

## Quick Reference: Core Commands

```bash
terraform init              # Initialize, download providers
terraform fmt               # Format code
terraform validate          # Check syntax
terraform plan              # Preview changes
terraform apply             # Execute changes
terraform destroy           # Tear down everything
terraform output            # Show outputs
terraform state list        # List managed resources
terraform import            # Import existing resources
terraform test              # Run tests
```

---

## Learning Path Recommendations

### Path 1: "I need to deploy something this week"
Modules 1 → 3 → 6 → 9

### Path 2: "I'm joining a team that uses Terraform"
Modules 1 → 2 → 3 → 5 → 6 → 7 → 8 → 9 → 10

### Path 3: "I want to master Terraform completely"
All modules in order (1 → 18)

### Path 4: "I need to set up CI/CD for Terraform"
Modules 9 → 15 → 16

### Path 5: "I'm preparing for the Terraform certification"
All modules, with extra focus on 5, 6, 7, 10, 13

---

## Topic Index

| Topic | Module(s) |
|-------|-----------|
| Authentication / Credentials | 1, 4 |
| Backends | 9 |
| check Blocks | 19 |
| CI/CD | 16 |
| CLI Commands (complete) | 19 |
| count vs for_each | 5 |
| Custom Providers | 14 |
| Data Sources | 5 |
| Debugging / TF_LOG | 18, 19 |
| Dependencies | 2, 5 |
| Drift Detection / Console Changes | 7, 16 |
| Dynamic Blocks | 12 |
| EKS | 17 |
| Ephemeral Resources | 19 |
| Expressions | 13 |
| Functions (built-in) | 13 |
| Functions (provider) | 19 |
| HCL Syntax | 2 |
| Import | 8 |
| Lambda / Serverless | 17 |
| Lifecycle Rules | 5 |
| Locals | 6 |
| Locking / Lock Recovery | 7, 9 |
| Mock Testing | 19 |
| Modules | 10 |
| Module Sources (Git/Registry) | 10 |
| moved / removed Blocks | 5, 19 |
| null_resource / terraform_data | 12 |
| optional() Type Constraint | 19 |
| Outputs | 6 |
| Parallelism / Performance | 19 |
| Policy as Code | 15 |
| Provider Mirrors | 19 |
| Providers | 4 |
| Provisioners | 12 |
| refresh / refresh-only | 7 |
| Remote State | 9 |
| Security Groups | 3, 12, 17 |
| Sensitive Data | 5, 6, 19 |
| Sentinel | 15 |
| State Corruption / Recovery | 7 |
| State Management | 7, 8, 9 |
| State Modified Mistakenly | 7 |
| -target (Resource Targeting) | 19 |
| Templates | 13 |
| terraform console | 13 |
| terraform graph | 19 |
| terraform init (all flags) | 19 |
| terraform show | 3, 19 |
| Testing | 15, 19 |
| Troubleshooting | 18 |
| Variables | 6 |
| VPC / Networking | 3, 10, 17 |
| Interview Answer Framework | 19 |
| Workspaces | 11 |

---

## Official Documentation — Master Reference

### Terraform Core Documentation

| Topic | Link |
|-------|------|
| Terraform Docs Home | [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform) |
| Introduction to Terraform | [developer.hashicorp.com/terraform/intro](https://developer.hashicorp.com/terraform/intro) |
| Install Terraform | [developer.hashicorp.com/terraform/install](https://developer.hashicorp.com/terraform/install) |
| Terraform Language Reference | [developer.hashicorp.com/terraform/language](https://developer.hashicorp.com/terraform/language) |
| Terraform CLI Reference | [developer.hashicorp.com/terraform/cli](https://developer.hashicorp.com/terraform/cli) |
| Terraform Internals | [developer.hashicorp.com/terraform/internals](https://developer.hashicorp.com/terraform/internals) |

### Language Features

| Topic | Link |
|-------|------|
| Files and Directories | [developer.hashicorp.com/terraform/language/files](https://developer.hashicorp.com/terraform/language/files) |
| Syntax (HCL) | [developer.hashicorp.com/terraform/language/syntax/configuration](https://developer.hashicorp.com/terraform/language/syntax/configuration) |
| Resources | [developer.hashicorp.com/terraform/language/resources](https://developer.hashicorp.com/terraform/language/resources) |
| Data Sources | [developer.hashicorp.com/terraform/language/data-sources](https://developer.hashicorp.com/terraform/language/data-sources) |
| Providers | [developer.hashicorp.com/terraform/language/providers](https://developer.hashicorp.com/terraform/language/providers) |
| Input Variables | [developer.hashicorp.com/terraform/language/values/variables](https://developer.hashicorp.com/terraform/language/values/variables) |
| Output Values | [developer.hashicorp.com/terraform/language/values/outputs](https://developer.hashicorp.com/terraform/language/values/outputs) |
| Local Values | [developer.hashicorp.com/terraform/language/values/locals](https://developer.hashicorp.com/terraform/language/values/locals) |
| Modules | [developer.hashicorp.com/terraform/language/modules](https://developer.hashicorp.com/terraform/language/modules) |
| Module Sources | [developer.hashicorp.com/terraform/language/modules/sources](https://developer.hashicorp.com/terraform/language/modules/sources) |
| Expressions | [developer.hashicorp.com/terraform/language/expressions](https://developer.hashicorp.com/terraform/language/expressions) |
| Built-in Functions | [developer.hashicorp.com/terraform/language/functions](https://developer.hashicorp.com/terraform/language/functions) |
| Type Constraints | [developer.hashicorp.com/terraform/language/expressions/type-constraints](https://developer.hashicorp.com/terraform/language/expressions/type-constraints) |
| Dynamic Blocks | [developer.hashicorp.com/terraform/language/expressions/dynamic-blocks](https://developer.hashicorp.com/terraform/language/expressions/dynamic-blocks) |
| Provisioners | [developer.hashicorp.com/terraform/language/resources/provisioners/syntax](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax) |
| `terraform_data` | [developer.hashicorp.com/terraform/language/resources/terraform-data](https://developer.hashicorp.com/terraform/language/resources/terraform-data) |
| Check Blocks | [developer.hashicorp.com/terraform/language/checks](https://developer.hashicorp.com/terraform/language/checks) |
| Import Block | [developer.hashicorp.com/terraform/language/import](https://developer.hashicorp.com/terraform/language/import) |
| `removed` Block | [developer.hashicorp.com/terraform/language/resources/syntax#removing-resources](https://developer.hashicorp.com/terraform/language/resources/syntax#removing-resources) |
| Ephemeral Resources | [developer.hashicorp.com/terraform/language/resources/ephemeral](https://developer.hashicorp.com/terraform/language/resources/ephemeral) |

### State and Backends

| Topic | Link |
|-------|------|
| State | [developer.hashicorp.com/terraform/language/state](https://developer.hashicorp.com/terraform/language/state) |
| Backends | [developer.hashicorp.com/terraform/language/backend](https://developer.hashicorp.com/terraform/language/backend) |
| S3 Backend | [developer.hashicorp.com/terraform/language/backend/s3](https://developer.hashicorp.com/terraform/language/backend/s3) |
| Workspaces | [developer.hashicorp.com/terraform/language/state/workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces) |

### Testing and Policy

| Topic | Link |
|-------|------|
| `terraform test` | [developer.hashicorp.com/terraform/language/tests](https://developer.hashicorp.com/terraform/language/tests) |
| Mock Providers | [developer.hashicorp.com/terraform/language/tests/mocking](https://developer.hashicorp.com/terraform/language/tests/mocking) |
| Sentinel | [developer.hashicorp.com/sentinel](https://developer.hashicorp.com/sentinel) |

### Terraform Cloud / HCP Terraform

| Topic | Link |
|-------|------|
| Terraform Cloud Docs | [developer.hashicorp.com/terraform/cloud-docs](https://developer.hashicorp.com/terraform/cloud-docs) |
| Workspaces | [developer.hashicorp.com/terraform/cloud-docs/workspaces](https://developer.hashicorp.com/terraform/cloud-docs/workspaces) |
| VCS Integration | [developer.hashicorp.com/terraform/cloud-docs/vcs](https://developer.hashicorp.com/terraform/cloud-docs/vcs) |
| Policy Enforcement | [developer.hashicorp.com/terraform/cloud-docs/policy-enforcement](https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement) |
| Cost Estimation | [developer.hashicorp.com/terraform/cloud-docs/cost-estimation](https://developer.hashicorp.com/terraform/cloud-docs/cost-estimation) |
| Private Registry | [developer.hashicorp.com/terraform/cloud-docs/registry](https://developer.hashicorp.com/terraform/cloud-docs/registry) |

### Plugin Development

| Topic | Link |
|-------|------|
| Plugin Development | [developer.hashicorp.com/terraform/plugin](https://developer.hashicorp.com/terraform/plugin) |
| Plugin Framework | [developer.hashicorp.com/terraform/plugin/framework](https://developer.hashicorp.com/terraform/plugin/framework) |
| Publishing Providers | [developer.hashicorp.com/terraform/registry/providers/publishing](https://developer.hashicorp.com/terraform/registry/providers/publishing) |

### Terraform Registry

| Topic | Link |
|-------|------|
| Registry Home | [registry.terraform.io](https://registry.terraform.io) |
| Browse Providers | [registry.terraform.io/browse/providers](https://registry.terraform.io/browse/providers) |
| Browse Modules | [registry.terraform.io/browse/modules](https://registry.terraform.io/browse/modules) |
| AWS Provider | [registry.terraform.io/providers/hashicorp/aws/latest/docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) |
| AWS VPC Module | [registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest) |
| AWS EKS Module | [registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest) |

### Third-Party Tools

| Tool | Link |
|------|------|
| tflint | [github.com/terraform-linters/tflint](https://github.com/terraform-linters/tflint) |
| trivy | [aquasecurity.github.io/trivy](https://aquasecurity.github.io/trivy) |
| checkov | [www.checkov.io](https://www.checkov.io) |
| Terratest | [terratest.gruntwork.io](https://terratest.gruntwork.io) |
| Terragrunt | [terragrunt.gruntwork.io](https://terragrunt.gruntwork.io) |
| Atlantis | [www.runatlantis.io](https://www.runatlantis.io) |
| OPA / Conftest | [www.conftest.dev](https://www.conftest.dev) |

> Each module also includes topic-specific documentation links at the bottom of its README.

---

## How to Use This Course

1. **Read the module README** — concepts, diagrams, and explanations
2. **Study the code examples** — in the `examples/` subdirectory where available
3. **Run the commands** — type them yourself, don't copy-paste
4. **Compare your output** — with the expected output shown in each module
5. **Do the exercises** — at the end of each module
6. **Break things intentionally** — then fix them using the troubleshooting guide

---

[Start the Course → Module 1: Introduction](module-01-introduction/README.md)
