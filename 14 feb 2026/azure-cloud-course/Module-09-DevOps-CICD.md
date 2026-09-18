# Module 09: Azure DevOps & CI/CD

## Certification Relevance: AZ-204, AZ-400

---

## 9.1 Azure DevOps Overview

```
Azure DevOps Services:
┌─────────────────────────────────────────────────────────────┐
│                    AZURE DEVOPS                             │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Boards  │  │  Repos   │  │ Pipelines│  │ Artifacts│  │
│  │          │  │          │  │          │  │          │  │
│  │ Work item│  │ Git repos│  │ CI/CD    │  │ Package  │  │
│  │ tracking │  │ (unlimited│  │ build &  │  │ feeds    │  │
│  │ Kanban   │  │  private) │  │ deploy   │  │ npm,NuGet│  │
│  │ Sprints  │  │          │  │          │  │ Maven    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐                                              │
│  │Test Plans│  Free for up to 5 users                      │
│  │          │  URL: dev.azure.com                           │
│  │ Manual & │                                              │
│  │ automated│                                              │
│  └──────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Example
```
Industry Example: A fintech company with 20 developers uses Azure DevOps:

Boards: Product owner creates user stories, developers pick tasks
Repos: All code in Git repos with branch policies (PR required)
Pipelines:
  - Developer pushes code → CI pipeline runs tests (5 min)
  - PR approved → CD pipeline deploys to staging (10 min)
  - QA approves → CD pipeline deploys to production (5 min)
Artifacts: Internal npm packages shared across teams
Test Plans: QA runs automated + manual test suites

Result: Deploy to production 10 times/day (was once/month)
```

---

### Portal UI Walkthrough: Create an Azure DevOps Organization and Project

```
PORTAL STEPS — Set Up Azure DevOps from Scratch:

Step 1: Go to Azure DevOps
   → Open https://dev.azure.com
   → Click "Start free"
   → Sign in with your Microsoft account (same as Azure Portal)

Step 2: Create an Organization
   → You'll be prompted to create an organization
   → Organization name: myorg
     (becomes https://dev.azure.com/myorg)
   → Region: Select closest to you (e.g., "Central US")
   → Click "Continue"

Step 3: Create Your First Project
   ┌─────────────────────────────────────────────────────────┐
   │ Project name:       my-webapp                            │
   │ Description:        E-commerce web application           │
   │ Visibility:         ● Private  ○ Public                  │
   │ Version control:    Git                                  │
   │ Work item process:  Agile (or Scrum, Basic, CMMI)       │
   │ Click "Create project"                                   │
   └─────────────────────────────────────────────────────────┘

Step 4: Explore the Project
   → You'll land on the project summary page
   → Left sidebar shows all services:
     ┌──────────────────────────────────────────┐
     │ Overview    — Project summary             │
     │ Boards      — Work items, sprints, kanban │
     │ Repos       — Git repositories            │
     │ Pipelines   — CI/CD pipelines             │
     │ Test Plans  — Manual/automated testing    │
     │ Artifacts   — Package feeds               │
     └──────────────────────────────────────────┘
```

### Portal UI Walkthrough: Create a Git Repository and Push Code

```
PORTAL STEPS — Create a Repo and Push Your Code:

Step 1: Navigate to Repos
   → In your project, click "Repos" in the left sidebar
   → You'll see an empty default repository

Step 2: Clone the Repository
   → Click "Clone" button (top right)
   → Copy the HTTPS URL:
     https://dev.azure.com/myorg/my-webapp/_git/my-webapp
   → Open your terminal:
     git clone https://dev.azure.com/myorg/my-webapp/_git/my-webapp
     cd my-webapp

Step 3: Add Your Code and Push
   → Add your project files to the folder
   → Then push:
     git add .
     git commit -m "Initial commit"
     git push origin main
   → Refresh the Repos page — your files appear!

Step 4: Create a Branch Policy (Require PR Reviews)
   → Repos → Branches → Click "..." next to "main"
   → Click "Branch policies"
   ┌─────────────────────────────────────────────────────────┐
   │ ☑ Require a minimum number of reviewers: 1              │
   │ ☑ Check for linked work items                           │
   │ ☑ Check for comment resolution                          │
   │ ☑ Build validation: (add your CI pipeline later)        │
   │ Click "Save changes"                                     │
   └─────────────────────────────────────────────────────────┘
   → Now nobody can push directly to main — PRs are required
```

### Portal UI Walkthrough: Create a CI/CD Pipeline

```
PORTAL STEPS — Create a Build and Deploy Pipeline:

Step 1: Navigate to Pipelines
   → Left sidebar → "Pipelines"
   → Click "Create Pipeline"

Step 2: Select Code Source
   → Where is your code?
     ● Azure Repos Git
     ○ GitHub
     ○ Bitbucket Cloud
     ○ Other Git
   → Select "Azure Repos Git"
   → Select your repository: "my-webapp"

Step 3: Configure Pipeline
   → Choose a template:
     ● Starter pipeline (blank YAML)
     ○ Node.js
     ○ .NET
     ○ Python
     ○ Docker
   → Select "Node.js" (or your language)
   → Azure generates a starter azure-pipelines.yml

Step 4: Review and Edit the YAML
   → You'll see the YAML editor in the browser
   → Edit the pipeline (example for Node.js):
     trigger:
       - main
     pool:
       vmImage: 'ubuntu-latest'
     steps:
       - task: NodeTool@0
         inputs:
           versionSpec: '18.x'
       - script: npm ci
         displayName: 'Install dependencies'
       - script: npm test
         displayName: 'Run tests'
       - script: npm run build
         displayName: 'Build'

Step 5: Save and Run
   → Click "Save and run"
   → Commit message: "Add CI pipeline"
   → Click "Save and run" again
   → The pipeline starts executing immediately

Step 6: Monitor the Pipeline
   → You'll see the pipeline running with live logs:
     ┌─────────────────────────────────────────────────────┐
     │ ✅ Initialize job              (2s)                  │
     │ ✅ Checkout repository         (5s)                  │
     │ ✅ Install Node.js             (8s)                  │
     │ ✅ Install dependencies        (30s)                 │
     │ ✅ Run tests                   (15s)                 │
     │ ✅ Build                       (20s)                 │
     │ ✅ Finalize job                (2s)                  │
     │                                                      │
     │ Pipeline succeeded! (1m 22s)                         │
     └─────────────────────────────────────────────────────┘
   → Click any step to see detailed logs

Step 7: Add a Deploy Stage (CD)
   → Go to Pipelines → Click your pipeline → "Edit"
   → Add deployment stage to the YAML (see CD Pipeline section below)
   → Or use the "Release" feature for visual drag-and-drop deployment
```

### Portal UI Walkthrough: Create a Release Pipeline (Visual CD)

```
PORTAL STEPS — Deploy to Azure App Service (Visual Editor):

Step 1: Navigate to Releases
   → Pipelines → Releases → "New pipeline"

Step 2: Select a Template
   → Choose "Azure App Service deployment"
   → Click "Apply"

Step 3: Add Artifact (Build Output)
   → Click "+ Add an artifact"
   → Source type: Build
   → Source pipeline: Select your CI pipeline
   → Click "Add"

Step 4: Configure Stage
   → Click "1 job, 1 task" in Stage 1
   → Stage name: "Deploy to Staging"
   ┌─────────────────────────────────────────────────────────┐
   │ Azure subscription: Select your subscription             │
   │   → Click "Authorize" (first time only)                 │
   │ App type:           Web App on Linux                     │
   │ App service name:   myapp-staging                        │
   └─────────────────────────────────────────────────────────┘
   → Click "Save"

Step 5: Enable Continuous Deployment
   → Click the lightning bolt icon (⚡) on the artifact
   → Enable "Continuous deployment trigger"
   → Every successful build now auto-deploys to staging

Step 6: Add Production Stage with Approval
   → Click "+ Add" → "New stage"
   → Template: "Azure App Service deployment"
   → Stage name: "Deploy to Production"
   → Configure App Service name: myapp-production
   → Click the person icon (👤) on the Production stage
   → Pre-deployment approvals: Enable
   → Approvers: Add your manager or team lead
   → Click "Save"

Step 7: Create a Release
   → Click "Create release" → "Create"
   → Watch it deploy to staging automatically
   → Approve the production deployment when ready
```

---

## 9.2 Azure Repos (Git)

```bash
# Azure DevOps CLI extension
az extension add --name azure-devops

# Configure defaults
az devops configure --defaults organization=https://dev.azure.com/myorg project=MyProject

# Create a new repository
az repos create --name "webapp-api"

# Output:
# {
#   "name": "webapp-api",
#   "remoteUrl": "https://dev.azure.com/myorg/MyProject/_git/webapp-api",
#   "webUrl": "https://dev.azure.com/myorg/MyProject/_git/webapp-api"
# }

# Clone the repository
git clone https://dev.azure.com/myorg/MyProject/_git/webapp-api

# List repositories
az repos list --output table

# Create a branch policy (require PR reviews)
az repos policy approver-count create \
  --branch main \
  --repository-id REPO_ID \
  --minimum-approver-count 2 \
  --enabled true \
  --blocking true

# Meaning: At least 2 reviewers must approve before merging to main

# Create a pull request
az repos pr create \
  --repository webapp-api \
  --source-branch feature/login \
  --target-branch main \
  --title "Add user login feature" \
  --description "Implements OAuth2 login flow"
```

---

## 9.3 Azure Pipelines (CI/CD)

### CI Pipeline (Build)

```yaml
# azure-pipelines.yml (placed in repo root)

# CI Pipeline - Triggers on every push to main
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'  # Microsoft-hosted agent

variables:
  nodeVersion: '18.x'

stages:
  - stage: Build
    displayName: 'Build and Test'
    jobs:
      - job: BuildJob
        displayName: 'Build Application'
        steps:
          # Install Node.js
          - task: NodeTool@0
            inputs:
              versionSpec: '$(nodeVersion)'
            displayName: 'Install Node.js'

          # Install dependencies
          - script: npm ci
            displayName: 'Install dependencies'

          # Run linting
          - script: npm run lint
            displayName: 'Run linter'

          # Run tests
          - script: npm test
            displayName: 'Run tests'

          # Build the application
          - script: npm run build
            displayName: 'Build application'

          # Publish build artifacts
          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.SourcesDirectory)/dist'
              artifactName: 'webapp'
            displayName: 'Publish artifacts'
```

### CD Pipeline (Deploy)

```yaml
# Continuation of azure-pipelines.yml

  - stage: DeployStaging
    displayName: 'Deploy to Staging'
    dependsOn: Build
    condition: succeeded()
    jobs:
      - deployment: DeployToStaging
        displayName: 'Deploy to Staging'
        environment: 'staging'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: 'Azure-Service-Connection'
                    appType: 'webAppLinux'
                    appName: 'myapp-staging'
                    package: '$(Pipeline.Workspace)/webapp/**/*.zip'

  - stage: DeployProduction
    displayName: 'Deploy to Production'
    dependsOn: DeployStaging
    condition: succeeded()
    jobs:
      - deployment: DeployToProduction
        displayName: 'Deploy to Production'
        environment: 'production'  # Requires manual approval
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: 'Azure-Service-Connection'
                    appType: 'webAppLinux'
                    appName: 'myapp-production'
                    package: '$(Pipeline.Workspace)/webapp/**/*.zip'
```

### Pipeline Concepts

```
Trigger:     What starts the pipeline (push, PR, schedule)
Pool:        Where the pipeline runs (Microsoft-hosted or self-hosted agent)
Stage:       A logical phase (Build, Test, Deploy-Staging, Deploy-Prod)
Job:         A unit of work within a stage
Step:        Individual task or script within a job
Task:        Pre-built action (AzureWebApp@1, NodeTool@0)
Artifact:    Output from a build (compiled code, packages)
Environment: Target for deployment (staging, production)
Variable:    Configurable values (secrets, settings)
Condition:   When to run (succeeded(), failed(), always())
```

### Pipeline Variables and Secrets

```yaml
# Define variables
variables:
  - name: environment
    value: 'production'
  - group: 'my-variable-group'  # Linked from Library

# Use variables
steps:
  - script: echo "Deploying to $(environment)"

# Secret variables (set in Pipeline UI or Variable Group)
# Never print secrets in logs
steps:
  - script: |
      curl -H "Authorization: Bearer $(API_KEY)" https://api.example.com
    env:
      API_KEY: $(ApiKey)  # Maps secret variable
```

---

## 9.4 GitHub Actions for Azure

```yaml
# .github/workflows/deploy.yml

name: Deploy to Azure

on:
  push:
    branches: [main]

env:
  AZURE_WEBAPP_NAME: myapp-production
  NODE_VERSION: '18.x'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install and build
        run: |
          npm ci
          npm run build

      - name: Run tests
        run: npm test

      - name: Login to Azure
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          package: ./dist

      - name: Azure logout
        run: az logout
```

### Setting Up Azure Credentials for GitHub Actions

```bash
# Create a service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "github-actions-sp" \
  --role contributor \
  --scopes /subscriptions/SUB_ID/resourceGroups/rg-demo-eastus \
  --json-auth

# Output (add this as GitHub secret AZURE_CREDENTIALS):
# {
#   "clientId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
#   "clientSecret": "secret-value",
#   "subscriptionId": "12345678-1234-1234-1234-123456789012",
#   "tenantId": "87654321-4321-4321-4321-210987654321"
# }
```

---

## 9.5 Azure Container Registry (ACR) with CI/CD

```bash
# Create ACR
az acr create \
  --resource-group rg-demo-eastus \
  --name acrdemo2024 \
  --sku Basic

# Build and push Docker image using ACR Tasks
az acr build \
  --registry acrdemo2024 \
  --image myapp:v1.0 \
  --file Dockerfile .

# Meaning: Build Docker image in the cloud (no local Docker needed)
# ACR builds the image and stores it in the registry

# Set up automated builds (trigger on Git push)
az acr task create \
  --registry acrdemo2024 \
  --name build-on-push \
  --image myapp:{{.Run.ID}} \
  --context https://github.com/myorg/myapp.git \
  --file Dockerfile \
  --git-access-token GITHUB_PAT
```

---

## 9.6 Infrastructure as Code in Pipelines

```yaml
# Deploy ARM template in pipeline
steps:
  - task: AzureResourceManagerTemplateDeployment@3
    inputs:
      azureResourceManagerConnection: 'Azure-Service-Connection'
      subscriptionId: 'SUB_ID'
      resourceGroupName: 'rg-production'
      location: 'East US'
      templateLocation: 'Linked artifact'
      csmFile: '$(Build.SourcesDirectory)/infra/main.bicep'
      csmParametersFile: '$(Build.SourcesDirectory)/infra/parameters.prod.json'
      deploymentMode: 'Incremental'

# Deploy with Terraform in pipeline
steps:
  - script: |
      terraform init
      terraform plan -out=tfplan
      terraform apply -auto-approve tfplan
    workingDirectory: '$(Build.SourcesDirectory)/infra'
    env:
      ARM_CLIENT_ID: $(ARM_CLIENT_ID)
      ARM_CLIENT_SECRET: $(ARM_CLIENT_SECRET)
      ARM_SUBSCRIPTION_ID: $(ARM_SUBSCRIPTION_ID)
      ARM_TENANT_ID: $(ARM_TENANT_ID)
```

---

## 9.7 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Pipeline failed: agent not available` | No hosted agents available or self-hosted agent offline | Check agent pool; use Microsoft-hosted agents |
| `Service connection unauthorized` | Service principal lacks permissions | Assign Contributor role to service principal |
| `npm test failed` | Tests failing in CI | Run tests locally first; check environment differences |
| `Artifact not found` | Wrong artifact name or path | Verify `PublishBuildArtifacts` task output name |
| `Environment approval pending` | Manual approval required | Approve in Azure DevOps Environments |
| `Docker build failed in ACR` | Dockerfile errors or missing context | Test Dockerfile locally; check build context |
| `AZURE_CREDENTIALS invalid` | Wrong format in GitHub secret | Regenerate with `az ad sp create-for-rbac --json-auth` |
| `Pipeline timeout` | Job exceeds time limit (60 min default) | Optimize build or increase timeout |

---

## 9.8 Practice Questions

### Question 1
**What is the purpose of a CI pipeline?**
- A) Deploy code to production
- B) Automatically build and test code on every commit ✅
- C) Monitor application performance
- D) Manage infrastructure

### Question 2
**In Azure Pipelines, what is an "environment"?**
- A) A virtual machine
- B) A target for deployment with approval gates ✅
- C) A variable group
- D) A build agent

### Question 3
**Which file defines an Azure Pipeline?**
- A) pipeline.json
- B) azure-pipelines.yml ✅
- C) Jenkinsfile
- D) deploy.config

### Question 4
**What does `az ad sp create-for-rbac` create?**
- A) A user account
- B) A service principal for automated authentication ✅
- C) A resource group
- D) A managed identity

### Question 5
**Which Azure DevOps service stores Git repositories?**
- A) Azure Boards
- B) Azure Repos ✅
- C) Azure Artifacts
- D) Azure Pipelines

---

[← Previous Module](./Module-08-Monitoring-Logging-Alerts.md) | [Next Module: Containers & Kubernetes →](./Module-10-Containers-and-Kubernetes.md)
