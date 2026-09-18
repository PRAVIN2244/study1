# Module 16: CI/CD and Automation

## Level: SUPER ADVANCED | Estimated Time: 3 hours

---

## 16.1 Terraform in CI/CD Pipelines

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Commit  │───▶│  CI      │───▶│  Review  │───▶│  CD      │
│          │    │          │    │          │    │          │
│ Push to  │    │ fmt      │    │ Plan     │    │ Apply    │
│ branch   │    │ validate │    │ output   │    │ (after   │
│          │    │ lint     │    │ in PR    │    │  merge)  │
│          │    │ test     │    │          │    │          │
│          │    │ plan     │    │ Approval │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 16.2 GitHub Actions

### Basic Terraform Workflow

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

env:
  TF_VERSION: "1.9.0"
  AWS_REGION: "us-east-1"

jobs:
  terraform:
    name: Terraform Plan & Apply
    runs-on: ubuntu-latest

    defaults:
      run:
        working-directory: ./infrastructure

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActions
          aws-region: ${{ env.AWS_REGION }}

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        continue-on-error: true

      - name: Terraform Init
        run: terraform init

      - name: Terraform Validate
        run: terraform validate

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        continue-on-error: true

      - name: Comment Plan on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const plan = `${{ steps.plan.outputs.stdout }}`;
            const truncated = plan.length > 60000
              ? plan.substring(0, 60000) + "\n\n... (truncated)"
              : plan;

            const body = `#### Terraform Plan 📋
            \`\`\`
            ${truncated}
            \`\`\`
            *Pushed by: @${{ github.actor }}*`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });

      - name: Terraform Plan Status
        if: steps.plan.outcome == 'failure'
        run: exit 1

      - name: Terraform Apply
        if: github.ref == 'refs/heads/main' && github.event_name == 'push'
        run: terraform apply -auto-approve tfplan
```

### Multi-Environment Workflow

```yaml
# .github/workflows/terraform-multi-env.yml
name: Terraform Multi-Environment

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  determine-environment:
    runs-on: ubuntu-latest
    outputs:
      environment: ${{ steps.set-env.outputs.environment }}
    steps:
      - id: set-env
        run: |
          if [[ "${{ github.base_ref || github.ref_name }}" == "main" ]]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
          fi

  terraform:
    needs: determine-environment
    runs-on: ubuntu-latest
    environment: ${{ needs.determine-environment.outputs.environment }}

    defaults:
      run:
        working-directory: ./environments/${{ needs.determine-environment.outputs.environment }}

    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.0"

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Init
        run: terraform init

      - name: Plan
        run: terraform plan -no-color -out=tfplan

      - name: Apply
        if: github.event_name == 'push'
        run: terraform apply -auto-approve tfplan
```

---

## 16.3 GitLab CI/CD

```yaml
# .gitlab-ci.yml
image:
  name: hashicorp/terraform:1.9.0
  entrypoint: [""]

variables:
  TF_ROOT: ${CI_PROJECT_DIR}/infrastructure
  TF_STATE_NAME: default

cache:
  key: terraform
  paths:
    - ${TF_ROOT}/.terraform

stages:
  - validate
  - plan
  - apply
  - destroy

before_script:
  - cd ${TF_ROOT}
  - terraform init

validate:
  stage: validate
  script:
    - terraform fmt -check
    - terraform validate

plan:
  stage: plan
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan
    expire_in: 1 week

apply:
  stage: apply
  script:
    - terraform apply -auto-approve tfplan
  dependencies:
    - plan
  when: manual
  only:
    - main

destroy:
  stage: destroy
  script:
    - terraform destroy -auto-approve
  when: manual
  only:
    - main
```

---

## 16.4 Atlantis (Pull Request Automation)

Atlantis is a self-hosted application that automates Terraform via pull requests.

### How Atlantis Works

```
Developer                  GitHub                    Atlantis
    │                        │                          │
    │── Push branch ────────▶│                          │
    │── Open PR ────────────▶│── Webhook ──────────────▶│
    │                        │                          │── terraform plan
    │                        │◀── Comment with plan ────│
    │                        │                          │
    │── Comment: atlantis ──▶│── Webhook ──────────────▶│
    │   apply                │                          │── terraform apply
    │                        │◀── Comment with result ──│
    │                        │                          │
    │── Merge PR ───────────▶│                          │
```

### Atlantis Configuration

```yaml
# atlantis.yaml (in repo root)
version: 3
projects:
  - name: networking
    dir: infrastructure/networking
    workspace: default
    terraform_version: v1.9.0
    autoplan:
      when_modified:
        - "*.tf"
        - "*.tfvars"
      enabled: true
    apply_requirements:
      - approved
      - mergeable

  - name: compute
    dir: infrastructure/compute
    workspace: default
    terraform_version: v1.9.0
    autoplan:
      when_modified:
        - "*.tf"
      enabled: true
    apply_requirements:
      - approved

  - name: database
    dir: infrastructure/database
    workspace: default
    terraform_version: v1.9.0
    apply_requirements:
      - approved
      - mergeable
```

### Atlantis PR Commands

```
atlantis plan                    # Run plan for all projects
atlantis plan -p networking      # Plan specific project
atlantis apply                   # Apply all planned projects
atlantis apply -p networking     # Apply specific project
atlantis plan -- -var="env=prod" # Pass extra args
```

---

## 16.5 Terraform Cloud / HCP Terraform

### Open-Source vs Terraform Cloud vs Terraform Enterprise

```
┌──────────────────────┬──────────────────┬──────────────────────┬──────────────────────┐
│                      │ Open-Source (CLI) │ Terraform Cloud      │ Terraform Enterprise │
├──────────────────────┼──────────────────┼──────────────────────┼──────────────────────┤
│ Cost                 │ Free             │ Free tier + paid     │ Paid (self-hosted)   │
│ State management     │ Manual (S3, etc.)│ Built-in             │ Built-in             │
│ Remote execution     │ No (local only)  │ Yes                  │ Yes                  │
│ VCS integration      │ No               │ Yes (GitHub, GitLab) │ Yes                  │
│ Policy as code       │ No               │ Yes (Sentinel, OPA)  │ Yes (Sentinel, OPA)  │
│ Cost estimation      │ No               │ Yes                  │ Yes                  │
│ Private registry     │ No               │ Yes                  │ Yes                  │
│ SSO / SAML           │ No               │ Business tier        │ Yes                  │
│ Audit logging        │ No               │ Business tier        │ Yes                  │
│ Self-hosted          │ Yes (your infra) │ No (SaaS)            │ Yes (your network)   │
│ Air-gapped support   │ Yes              │ No                   │ Yes                  │
│ Run tasks            │ No               │ Yes                  │ Yes                  │
│ Concurrent runs      │ Unlimited        │ 1 (free) / paid      │ Configurable         │
│ Team management      │ Manual           │ Built-in             │ Built-in + RBAC      │
└──────────────────────┴──────────────────┴──────────────────────┴──────────────────────┘
```

**When to use which:**
- **Open-source CLI** — Small teams, simple projects, or when you manage your own backend (S3 + DynamoDB)
- **Terraform Cloud** — Teams needing collaboration, policy enforcement, and VCS-driven workflows without self-hosting
- **Terraform Enterprise** — Enterprises requiring self-hosted deployment, air-gapped environments, SSO/SAML, and audit compliance

### Setup: Open-Source with S3 Backend

```hcl
# backend.tf — open-source approach
terraform {
  backend "s3" {
    bucket         = "my-company-tfstate"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

```bash
terraform init
```

**Output:**
```
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

### Setup: Migrating from S3 to Terraform Cloud

```hcl
# Replace the S3 backend with cloud block
terraform {
  cloud {
    organization = "my-company"
    workspaces {
      name = "my-app-prod"
    }
  }
}
```

```bash
# Login to Terraform Cloud first
terraform login
```

**Output:**
```
Terraform will request an API token for app.terraform.io using your browser.

If login is successful, Terraform will store the token in plain text in
the following file for use by subsequent commands:
    /home/user/.terraform.d/credentials.tfrc.json

Do you want to proceed?
  Only 'yes' will be accepted to confirm.

  Enter a value: yes

Token for app.terraform.io:
  Enter a value:

Retrieved token for user devops-engineer

Success! Terraform has obtained and saved an API token.
```

```bash
# Migrate state from S3 to Terraform Cloud
terraform init
```

**Output:**
```
Initializing Terraform Cloud...
Do you wish to proceed?
  As part of migrating to Terraform Cloud, Terraform can optionally
  copy your current workspace state to the configured Terraform Cloud
  workspace.

  Answer "yes" to copy the latest state snapshot to the configured
  Terraform Cloud workspace.

  Enter a value: yes

Initializing provider plugins...

Terraform Cloud has been successfully initialized!
```

### Common Error: Backend Conflict

```bash
# If you have BOTH a backend block and a cloud block:
terraform init
```

**Error:**
```
Error: Invalid backend configuration

The "cloud" block and "backend" block are mutually exclusive.
Please remove one of them from your configuration.
```

**Fix:** Remove the `backend "s3" {}` block when switching to `cloud {}`.

### Configuration

```hcl
terraform {
  cloud {
    organization = "my-company"

    workspaces {
      name = "my-app-prod"
    }
  }
}
```

### Workspace Configuration via API

```bash
# Create workspace
curl -s \
  --header "Authorization: Bearer $TFC_TOKEN" \
  --header "Content-Type: application/vnd.api+json" \
  --request POST \
  --data '{
    "data": {
      "type": "workspaces",
      "attributes": {
        "name": "my-app-prod",
        "terraform_version": "1.9.0",
        "auto-apply": false,
        "queue-all-runs": false,
        "vcs-repo": {
          "identifier": "myorg/infrastructure",
          "branch": "main",
          "oauth-token-id": "ot-abc123"
        }
      }
    }
  }' \
  https://app.terraform.io/api/v2/organizations/my-company/workspaces
```

### Run Triggers (Workspace Chaining)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ networking  │────▶│  compute    │────▶│  database   │
│ workspace   │     │  workspace  │     │  workspace  │
│             │     │             │     │             │
│ VPC, Subnets│     │ EC2, ALB    │     │ RDS         │
│             │     │             │     │             │
│ Triggers    │     │ Triggers    │     │             │
│ compute     │     │ database    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 16.6 Automated Drift Detection

### Scheduled Drift Detection

```yaml
# .github/workflows/drift-detection.yml
name: Drift Detection

on:
  schedule:
    - cron: '0 8 * * 1-5'  # Weekdays at 8 AM UTC

jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3

      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - name: Init
        run: terraform init

      - name: Detect Drift
        id: drift
        run: |
          terraform plan -detailed-exitcode -no-color 2>&1 | tee plan_output.txt
          EXIT_CODE=${PIPESTATUS[0]}
          if [ $EXIT_CODE -eq 2 ]; then
            echo "drift_detected=true" >> $GITHUB_OUTPUT
          else
            echo "drift_detected=false" >> $GITHUB_OUTPUT
          fi

      - name: Notify on Drift
        if: steps.drift.outputs.drift_detected == 'true'
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "⚠️ Infrastructure drift detected!\nSee: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Plan Exit Codes

```
Exit Code 0: No changes (success, no drift)
Exit Code 1: Error
Exit Code 2: Changes detected (drift found)
```

```bash
terraform plan -detailed-exitcode
echo $?  # Check exit code
```

---

## 16.7 OIDC Authentication (No Static Credentials)

### GitHub Actions with OIDC

```yaml
# No AWS access keys needed!
permissions:
  id-token: write
  contents: read

steps:
  - name: Configure AWS with OIDC
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/GitHubActions
      aws-region: us-east-1
      # No access-key-id or secret-access-key needed
```

### AWS IAM Role for GitHub OIDC

```hcl
# IAM role that GitHub Actions can assume via OIDC
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "GitHubActions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:myorg/infrastructure:*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
```

---

## 16.8 AWS CodePipeline + CodeBuild for Terraform

### Multi-Environment Pipeline Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  GitHub   │───▶│  CodeBuild   │───▶│  CodeBuild   │───▶│  Manual      │
│  Push     │    │  DEV Apply   │    │  STAG Apply  │    │  Approval    │
└──────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                               │
                                                        ┌──────▼───────┐
                                                        │  CodeBuild   │
                                                        │  PROD Apply  │
                                                        └──────────────┘
```

### Backend Config Files (Per Environment)

Use `-backend-config` to share the same Terraform code across environments:

```hcl
# c1-versions.tf — empty backend block
terraform {
  backend "s3" { }  # Config provided via -backend-config flag
}
```

```ini
# dev.conf
bucket         = "mycompany-terraform-state"
key            = "iacdevops/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "iacdevops-dev-tfstate"
```

```ini
# stag.conf
bucket         = "mycompany-terraform-state"
key            = "iacdevops/stag/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "iacdevops-stag-tfstate"
```

```bash
# Initialize with environment-specific backend
terraform init -input=false -backend-config=dev.conf
terraform apply -input=false -var-file=dev.tfvars -auto-approve
```

### Environment-Specific tfvars

```hcl
# dev.tfvars
environment          = "dev"
vpc_cidr_block       = "10.0.0.0/16"
instance_type        = "t3.micro"
private_instance_count = 2
```

```hcl
# stag.tfvars
environment          = "stag"
vpc_cidr_block       = "10.1.0.0/16"
instance_type        = "t3.small"
private_instance_count = 4
```

### CodeBuild Buildspec

```yaml
# buildspec-dev.yml
version: 0.2

env:
  variables:
    TERRAFORM_VERSION: "1.9.0"
    TF_COMMAND: "apply"
  parameter-store:
    AWS_ACCESS_KEY_ID: "/CodeBuild/MY_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY: "/CodeBuild/MY_AWS_SECRET_ACCESS_KEY"

phases:
  install:
    runtime-versions:
      python: 3.11
    on-failure: ABORT
    commands:
      - wget -q https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
      - unzip -q terraform_${TERRAFORM_VERSION}_linux_amd64.zip
      - mv terraform /usr/local/bin/
      - terraform --version

  pre_build:
    on-failure: ABORT
    commands:
      - echo "Terraform execution started on $(date)"
      - cd "$CODEBUILD_SRC_DIR/terraform-manifests"
      - terraform init -input=false -backend-config=dev.conf
      - terraform validate

  build:
    on-failure: ABORT
    commands:
      - cd "$CODEBUILD_SRC_DIR/terraform-manifests"
      - terraform plan -input=false -var-file=dev.tfvars
      - terraform $TF_COMMAND -input=false -var-file=dev.tfvars -auto-approve

  post_build:
    on-failure: CONTINUE
    commands:
      - echo "Terraform execution completed on $(date)"
```

### CodePipeline Terraform Configuration

```hcl
# CodeBuild project for dev environment
resource "aws_codebuild_project" "terraform_dev" {
  name         = "terraform-dev-apply"
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = false
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-dev.yml"
  }
}

# CodePipeline with dev → staging stages
resource "aws_codepipeline" "terraform" {
  name     = "terraform-iac-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.id
    type     = "S3"
  }

  # Stage 1: Source (GitHub)
  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]
      configuration = {
        Owner  = var.github_owner
        Repo   = var.github_repo
        Branch = "main"
      }
    }
  }

  # Stage 2: Deploy to Dev
  stage {
    name = "Dev-Deploy"
    action {
      name            = "Terraform-Apply-Dev"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]
      configuration = {
        ProjectName = aws_codebuild_project.terraform_dev.name
      }
    }
  }

  # Stage 3: Manual Approval for Staging
  stage {
    name = "Staging-Approval"
    action {
      name     = "Manual-Approval"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"
      configuration = {
        NotificationArn = aws_sns_topic.pipeline_approval.arn
        CustomData      = "Review dev deployment before promoting to staging"
      }
    }
  }

  # Stage 4: Deploy to Staging
  stage {
    name = "Staging-Deploy"
    action {
      name            = "Terraform-Apply-Staging"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["source_output"]
      configuration = {
        ProjectName = aws_codebuild_project.terraform_stag.name
      }
    }
  }
}
```

---

## 16.9 Best Practices for CI/CD

| Practice | Why |
|----------|-----|
| Use OIDC, not static credentials | No secrets to rotate or leak |
| Plan on PR, apply on merge | Human review before changes |
| Use `-out=tfplan` and apply the saved plan | Ensures you apply exactly what was reviewed |
| Lock provider versions | Reproducible builds |
| Cache `.terraform` directory | Faster pipeline runs |
| Use `-detailed-exitcode` | Detect drift programmatically |
| Run drift detection on schedule | Catch manual changes early |
| Use separate state per environment | Blast radius reduction |
| Require PR approval for prod | Change control |
| Store plan artifacts | Audit trail |

---

## Exercises

### Exercise 16.1: GitHub Actions Pipeline
Create a GitHub Actions workflow that:
1. Runs `fmt`, `validate`, and `plan` on PRs
2. Comments the plan output on the PR
3. Applies on merge to main

### Exercise 16.2: Drift Detection
Set up a scheduled workflow that:
1. Runs `terraform plan -detailed-exitcode`
2. Sends a notification if drift is detected
3. Creates a GitHub issue with the drift details

### Exercise 16.3: Multi-Environment Pipeline
Create a pipeline that:
1. Deploys to dev on push to `develop`
2. Deploys to staging on push to `release/*`
3. Deploys to prod on push to `main` (with manual approval)

---

## Key Takeaways

- Plan on PR, apply on merge is the standard workflow
- Use OIDC for keyless authentication in CI/CD
- Save plans with `-out` and apply the saved plan for consistency
- Atlantis and Terraform Cloud automate PR-based workflows
- Scheduled drift detection catches manual changes
- Use `-detailed-exitcode` for programmatic drift detection
- Separate pipelines per environment with appropriate approval gates

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Terraform Cloud / HCP Terraform | [developer.hashicorp.com/terraform/cloud-docs](https://developer.hashicorp.com/terraform/cloud-docs) |
| Terraform Cloud — Workspaces | [developer.hashicorp.com/terraform/cloud-docs/workspaces](https://developer.hashicorp.com/terraform/cloud-docs/workspaces) |
| Terraform Cloud — VCS Integration | [developer.hashicorp.com/terraform/cloud-docs/vcs](https://developer.hashicorp.com/terraform/cloud-docs/vcs) |
| Terraform Cloud — Run Triggers | [developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/run-triggers](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/run-triggers) |
| Terraform Cloud — API-Driven Runs | [developer.hashicorp.com/terraform/cloud-docs/run/api](https://developer.hashicorp.com/terraform/cloud-docs/run/api) |
| CLI-Driven Runs | [developer.hashicorp.com/terraform/cloud-docs/run/cli](https://developer.hashicorp.com/terraform/cloud-docs/run/cli) |
| Atlantis | [www.runatlantis.io/docs/](https://www.runatlantis.io/docs/) |
| Atlantis — Server Configuration | [www.runatlantis.io/docs/server-configuration.html](https://www.runatlantis.io/docs/server-configuration.html) |
| Atlantis — `atlantis.yaml` | [www.runatlantis.io/docs/repo-level-atlantis-yaml.html](https://www.runatlantis.io/docs/repo-level-atlantis-yaml.html) |
| GitHub Actions — Terraform Setup | [github.com/hashicorp/setup-terraform](https://github.com/hashicorp/setup-terraform) |
| GitHub Actions — OIDC with AWS | [docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) |
| GitLab CI — Terraform Integration | [docs.gitlab.com/ee/user/infrastructure/iac/](https://docs.gitlab.com/ee/user/infrastructure/iac/) |
| AWS IAM OIDC Identity Provider | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider) |
| **AWS CodePipeline / CodeBuild** | |
| `aws_codepipeline` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codepipeline](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codepipeline) |
| `aws_codebuild_project` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project) |
| AWS CodeBuild Buildspec Reference | [docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html](https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html) |
| Backend Config (`-backend-config`) | [developer.hashicorp.com/terraform/language/backend#partial-configuration](https://developer.hashicorp.com/terraform/language/backend#partial-configuration) |

---

[← Previous Module](../module-15-testing-and-validation/README.md) | [Next Module: Real-World Projects →](../module-17-real-world-projects/README.md)
