# Module 1: GCP Fundamentals

---

## 1.1 What is Google Cloud Platform?

GCP is Google's suite of cloud computing services running on the same infrastructure
Google uses for its products (Search, YouTube, Gmail).

**Key Concepts:**
- **Region**: A geographic location (e.g., `us-central1` = Iowa, USA)
- **Zone**: An isolated deployment area within a region (e.g., `us-central1-a`)
- **Project**: A container for all GCP resources — every resource belongs to exactly one project
- **Organization**: Top-level node in GCP resource hierarchy (tied to a Google Workspace or Cloud Identity domain)

**GCP vs AWS vs Azure — Quick Mapping:**

| Concept | GCP | AWS | Azure |
|---------|-----|-----|-------|
| Virtual Machine | Compute Engine | EC2 | Virtual Machines |
| Kubernetes | GKE | EKS | AKS |
| Object Storage | Cloud Storage | S3 | Blob Storage |
| Serverless Functions | Cloud Functions | Lambda | Azure Functions |
| Managed SQL | Cloud SQL | RDS | Azure SQL |
| NoSQL | Firestore | DynamoDB | Cosmos DB |
| Data Warehouse | BigQuery | Redshift | Synapse |

---

## 1.2 Setting Up Your GCP Account

### Step 1: Create a GCP Account

1. Go to https://cloud.google.com
2. Click "Get started for free"
3. Sign in with your Google account
4. Enter billing information (you won't be charged — $300 free credit for 90 days)
5. Accept terms and create account

### Step 2: Create Your First Project

```
Via Console:
1. Go to https://console.cloud.google.com
2. Click the project dropdown (top-left, next to "Google Cloud")
3. Click "New Project"
4. Name: "my-first-project"
5. Click "Create"
```

**What is a Project?**
A project is the fundamental organizing entity in GCP. It:
- Has a unique Project ID (globally unique, immutable)
- Has a Project Name (human-readable, mutable)
- Has a Project Number (auto-assigned)
- Contains all resources (VMs, databases, storage buckets, etc.)
- Has its own billing, IAM policies, and API enablement

---

## 1.3 Google Cloud Shell

Cloud Shell is a free, browser-based terminal with:
- 5 GB persistent home directory
- Pre-installed tools: gcloud, kubectl, docker, terraform, git, python, node
- Debian-based Linux VM (e2-small)
- Automatic authentication with your GCP account

### Accessing Cloud Shell

1. Go to https://console.cloud.google.com
2. Click the terminal icon (top-right toolbar) — "Activate Cloud Shell"
3. A terminal opens at the bottom of the page

### Basic Cloud Shell Commands

```bash
# Check your authenticated account
whoami
```
**Output:**
```
your_username
```

```bash
# Check available disk space
df -h ~
```
**Output:**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       4.8G  1.2G  3.4G  26% /home
```

```bash
# Check pre-installed tools
gcloud version
```
**Output:**
```
Google Cloud SDK 467.0.0
alpha 2024.01.26
beta 2024.01.26
bq 2.0.101
core 2024.01.26
gcloud-crc32c 1.0.0
gsutil 5.27
kubectl 1.27.9
```

---

## 1.4 The gcloud CLI — Your Primary Tool

`gcloud` is the command-line interface for GCP. It manages almost every GCP resource.

### Installation (Local Machine)

If you're not using Cloud Shell, install the SDK locally:

```bash
# macOS (using Homebrew)
brew install --cask google-cloud-sdk

# Ubuntu/Debian
sudo apt-get install apt-transport-https ca-certificates gnupg curl
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt-get update && sudo apt-get install google-cloud-cli

# Windows
# Download installer from: https://cloud.google.com/sdk/docs/install
```

### Authentication

```bash
# Initialize gcloud (first-time setup)
gcloud init
```
**What it does:** Opens a browser for OAuth login, sets default project and region.

**Output (interactive):**
```
Welcome! This command will take you through the configuration of gcloud.

Pick configuration to use:
 [1] Re-initialize this configuration [default] with new settings
 [2] Create a new configuration
Please enter your numeric choice: 1

Your current configuration has been set to: [default]

You can skip diagnostics next time by using the following flag:
  gcloud init --skip-diagnostics

Network diagnostic passed (1/1 checks passed).

Choose the account you would like to use to perform operations for this configuration:
 [1] yourname@gmail.com
 [2] Log in with a new account
Please enter your numeric choice: 1

You are logged in as: [yourname@gmail.com].

Pick cloud project to use:
 [1] my-first-project-12345
 [2] Enter a project ID
 [3] Create a new project
Please enter numeric choice or text value: 1
```

```bash
# Login only (without full init)
gcloud auth login
```
**What it does:** Opens browser for authentication only. Doesn't change project/region settings.

```bash
# Login for application default credentials (used by client libraries)
gcloud auth application-default login
```
**What it does:** Creates credentials that client libraries (Python, Java, Go, Node.js) use automatically.

```bash
# Check current authenticated account
gcloud auth list
```
**Output:**
```
   ACCOUNT                  ACTIVE
*  yourname@gmail.com       *
   other@company.com
```

```bash
# Revoke access
gcloud auth revoke yourname@gmail.com
```

---

## 1.5 Project Management

### Creating Projects

```bash
# Create a new project
gcloud projects create my-webapp-prod --name="My Web App Production"
```
**What it does:** Creates a new GCP project with ID `my-webapp-prod` and display name "My Web App Production".

**Output:**
```
Create in progress for [https://cloudresourcemanager.googleapis.com/v1/projects/my-webapp-prod].
Waiting for [operations/cp.xxxxxxxxxxxx] to finish...done.
Finished creating project [my-webapp-prod].
```

**⚠️ Common Error:**
```
ERROR: (gcloud.projects.create) ALREADY_EXISTS: Project my-webapp-prod already exists.
```
**Fix:** Project IDs are globally unique across ALL of GCP. Add a random suffix:
```bash
gcloud projects create my-webapp-prod-$(date +%s)
```

### Listing Projects

```bash
# List all projects
gcloud projects list
```
**Output:**
```
PROJECT_ID              NAME                    PROJECT_NUMBER
my-first-project-12345  My First Project        123456789012
my-webapp-prod          My Web App Production   234567890123
```

### Setting Default Project

```bash
# Set default project for all gcloud commands
gcloud config set project my-webapp-prod
```
**What it does:** All subsequent `gcloud` commands will target this project unless overridden with `--project` flag.

**Output:**
```
Updated property [core/project].
```

```bash
# Verify current project
gcloud config get-value project
```
**Output:**
```
my-webapp-prod
```

### Deleting Projects

```bash
# Delete a project (30-day recovery window)
gcloud projects delete my-webapp-prod
```
**What it does:** Marks the project for deletion. Resources are shut down immediately, but the project can be recovered within 30 days.

**Output:**
```
Your project will be deleted.
Do you want to continue (Y/n)?  Y
Deleted [https://cloudresourcemanager.googleapis.com/v1/projects/my-webapp-prod].
```

---

## 1.6 Configurations (Managing Multiple Environments)

Configurations let you switch between projects/accounts/regions quickly.

```bash
# Create a new configuration for production
gcloud config configurations create prod-config
```
**Output:**
```
Created [prod-config].
Activated [prod-config].
```

```bash
# Set properties for this configuration
gcloud config set project my-webapp-prod
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud config set account admin@company.com
```

```bash
# Create another configuration for development
gcloud config configurations create dev-config
gcloud config set project my-webapp-dev
gcloud config set compute/region us-east1
gcloud config set compute/zone us-east1-b
gcloud config set account developer@company.com
```

```bash
# List all configurations
gcloud config configurations list
```
**Output:**
```
NAME          IS_ACTIVE  ACCOUNT               PROJECT           COMPUTE_DEFAULT_ZONE  COMPUTE_DEFAULT_REGION
default       False      yourname@gmail.com    my-first-project  us-central1-a         us-central1
dev-config    True       developer@company.com my-webapp-dev      us-east1-b            us-east1
prod-config   False      admin@company.com     my-webapp-prod     us-central1-a         us-central1
```

```bash
# Switch between configurations
gcloud config configurations activate prod-config
```
**Output:**
```
Activated [prod-config].
```

**Real-world Use Case:**
A DevOps engineer manages 3 environments (dev, staging, prod) across different projects.
Instead of typing `--project=xxx` every time, they switch configurations:
```bash
gcloud config configurations activate staging-config
gcloud compute instances list  # Shows staging VMs only
gcloud config configurations activate prod-config
gcloud compute instances list  # Shows production VMs only
```

---

## 1.7 Enabling APIs

GCP services are disabled by default. You must enable each API before using it.

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com
```
**What it does:** Activates the Compute Engine API for the current project. Required before creating VMs.

**Output:**
```
Operation "operations/acf.p2-123456789012-xxxxxxxx" finished successfully.
```

```bash
# Enable multiple APIs at once
gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  sqladmin.googleapis.com \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com
```

```bash
# List enabled APIs
gcloud services list --enabled
```
**Output:**
```
NAME                              TITLE
bigquery.googleapis.com           BigQuery API
compute.googleapis.com            Compute Engine API
container.googleapis.com          Kubernetes Engine API
storage.googleapis.com            Cloud Storage JSON API
...
```

```bash
# Search for an API
gcloud services list --available --filter="name:translate"
```
**Output:**
```
NAME                              TITLE
translate.googleapis.com          Cloud Translation API
```

**⚠️ Common Error:**
```
ERROR: (gcloud.compute.instances.create) PERMISSION_DENIED: Compute Engine API has not been used in project 123456789012 before or it is disabled.
```
**Fix:**
```bash
gcloud services enable compute.googleapis.com
```

---

## 1.8 IAM — Identity and Access Management

IAM controls WHO can do WHAT on WHICH resources.

### Core Concepts

- **Principal (Member)**: Who — a user, service account, group, or domain
  - `user:alice@company.com`
  - `serviceAccount:my-sa@project.iam.gserviceaccount.com`
  - `group:devs@company.com`
  - `domain:company.com`

- **Role**: What — a collection of permissions
  - **Basic roles**: `roles/owner`, `roles/editor`, `roles/viewer` (broad, avoid in production)
  - **Predefined roles**: `roles/compute.admin`, `roles/storage.objectViewer` (service-specific)
  - **Custom roles**: You define exact permissions

- **Policy**: Binds principals to roles on a resource

### Viewing IAM Policies

```bash
# View IAM policy for current project
gcloud projects get-iam-policy $(gcloud config get-value project)
```
**Output:**
```yaml
bindings:
- members:
  - user:admin@company.com
  role: roles/owner
- members:
  - user:developer@company.com
  - serviceAccount:123456789012-compute@developer.gserviceaccount.com
  role: roles/editor
- members:
  - user:viewer@company.com
  role: roles/viewer
etag: BwXXXXXXXXX=
version: 1
```

### Granting Roles

```bash
# Grant a user the Compute Admin role
gcloud projects add-iam-policy-binding my-webapp-prod \
  --member="user:developer@company.com" \
  --role="roles/compute.admin"
```
**What it does:** Gives `developer@company.com` full control over Compute Engine resources in the `my-webapp-prod` project.

**Output:**
```
Updated IAM policy for project [my-webapp-prod].
bindings:
- members:
  - user:developer@company.com
  role: roles/compute.admin
...
```

### Revoking Roles

```bash
# Remove a role from a user
gcloud projects remove-iam-policy-binding my-webapp-prod \
  --member="user:developer@company.com" \
  --role="roles/compute.admin"
```

### Listing Available Roles

```bash
# List all predefined roles
gcloud iam roles list --filter="name:compute"
```
**Output:**
```
NAME                                  TITLE
roles/compute.admin                   Compute Admin
roles/compute.imageUser               Compute Image User
roles/compute.instanceAdmin           Compute Instance Admin (beta)
roles/compute.instanceAdmin.v1        Compute Instance Admin (v1)
roles/compute.networkAdmin            Compute Network Admin
roles/compute.networkUser             Compute Network User
roles/compute.networkViewer           Compute Network Viewer
roles/compute.osAdminLogin            Compute OS Admin Login
roles/compute.osLogin                 Compute OS Login
roles/compute.securityAdmin           Compute Security Admin
roles/compute.storageAdmin            Compute Storage Admin
roles/compute.viewer                  Compute Viewer
```

```bash
# See permissions in a specific role
gcloud iam roles describe roles/compute.viewer
```
**Output:**
```
description: Read-only access to Compute Engine resources.
etag: AA==
includedPermissions:
- compute.acceleratorTypes.get
- compute.acceleratorTypes.list
- compute.addresses.get
- compute.addresses.list
- compute.disks.get
- compute.disks.list
- compute.instances.get
- compute.instances.list
...
name: roles/compute.viewer
stage: GA
title: Compute Viewer
```

---

## 1.9 Service Accounts

Service accounts are identities for applications (not humans). Your VM, Cloud Function, or CI/CD pipeline uses a service account to authenticate to GCP APIs.

### Creating a Service Account

```bash
# Create a service account
gcloud iam service-accounts create my-app-sa \
  --display-name="My Application Service Account" \
  --description="Used by the web application to access Cloud Storage and Cloud SQL"
```
**What it does:** Creates a service account with email `my-app-sa@PROJECT_ID.iam.gserviceaccount.com`.

**Output:**
```
Created service account [my-app-sa].
```

### Granting Roles to a Service Account

```bash
# Grant Cloud Storage read access
gcloud projects add-iam-policy-binding my-webapp-prod \
  --member="serviceAccount:my-app-sa@my-webapp-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Grant Cloud SQL client access
gcloud projects add-iam-policy-binding my-webapp-prod \
  --member="serviceAccount:my-app-sa@my-webapp-prod.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### Creating and Using Keys

```bash
# Create a JSON key file (for local development or external systems)
gcloud iam service-accounts keys create ~/sa-key.json \
  --iam-account=my-app-sa@my-webapp-prod.iam.gserviceaccount.com
```
**Output:**
```
created key [abcdef1234567890] of type [json] as [/home/user/sa-key.json] for [my-app-sa@my-webapp-prod.iam.gserviceaccount.com]
```

**⚠️ Security Warning:** Service account keys are long-lived credentials. Prefer Workload Identity Federation or attached service accounts instead. If you must use keys:
- Never commit them to git
- Rotate them regularly
- Store them in Secret Manager

```bash
# Use the key to authenticate
gcloud auth activate-service-account \
  --key-file=~/sa-key.json
```

```bash
# List service accounts
gcloud iam service-accounts list
```
**Output:**
```
DISPLAY NAME                          EMAIL                                                    DISABLED
My Application Service Account       my-app-sa@my-webapp-prod.iam.gserviceaccount.com          False
Compute Engine default service account 123456789012-compute@developer.gserviceaccount.com       False
```

### Listing Service Account Keys

```bash
gcloud iam service-accounts keys list \
  --iam-account=my-app-sa@my-webapp-prod.iam.gserviceaccount.com
```
**Output:**
```
KEY_ID                                    CREATED_AT            EXPIRES_AT            DISABLED
abcdef1234567890abcdef1234567890abcdef12  2024-01-15T10:30:00Z  2026-01-14T10:30:00Z  False
```

---

## 1.10 Billing and Budgets

### Linking a Billing Account

```bash
# List billing accounts
gcloud billing accounts list
```
**Output:**
```
ACCOUNT_ID            NAME                OPEN   MASTER_ACCOUNT_ID
0X0X0X-0X0X0X-0X0X0X My Billing Account  True
```

```bash
# Link billing account to a project
gcloud billing projects link my-webapp-prod \
  --billing-account=0X0X0X-0X0X0X-0X0X0X
```

### Setting Budget Alerts

```bash
# Via Console (recommended for budgets):
# 1. Go to Billing > Budgets & alerts
# 2. Click "Create Budget"
# 3. Set amount (e.g., $100/month)
# 4. Set alert thresholds (50%, 90%, 100%)
# 5. Configure notification channels (email, Pub/Sub)
```

**Real-world Example — Startup Cost Control:**
```bash
# Create a budget alert via gcloud (requires billing.budgets API)
gcloud services enable billingbudgets.googleapis.com

# Set a $500/month budget with alerts at 50%, 80%, 100%
gcloud billing budgets create \
  --billing-account=0X0X0X-0X0X0X-0X0X0X \
  --display-name="Monthly Dev Budget" \
  --budget-amount=500 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

---

## 1.11 Resource Hierarchy

```
Organization (company.com)
├── Folder: Engineering
│   ├── Project: webapp-dev
│   ├── Project: webapp-staging
│   └── Project: webapp-prod
├── Folder: Data Science
│   ├── Project: ml-experiments
│   └── Project: ml-production
└── Folder: Shared Services
    ├── Project: shared-networking
    └── Project: shared-monitoring
```

IAM policies are **inherited** downward:
- A role granted at the Organization level applies to ALL projects
- A role granted at the Folder level applies to all projects in that folder
- A role granted at the Project level applies only to that project

```bash
# List folders in an organization
gcloud resource-manager folders list --organization=ORG_ID

# Create a folder
gcloud resource-manager folders create \
  --display-name="Engineering" \
  --organization=ORG_ID

# Move a project into a folder
gcloud projects move my-webapp-prod --folder=FOLDER_ID
```

---

## 1.12 Labels and Tags

Labels are key-value pairs for organizing and filtering resources.

```bash
# Add labels to a project
gcloud projects update my-webapp-prod \
  --update-labels=env=production,team=backend,cost-center=eng-42

# Filter resources by label
gcloud compute instances list --filter="labels.env=production"
```

**Real-world Use Case — Cost Allocation:**
A company with 5 teams uses labels to track spending per team:
```bash
# Label all resources with team name
gcloud compute instances update my-vm \
  --update-labels=team=payments,env=prod

# In BigQuery billing export, query costs by label:
# SELECT labels.value, SUM(cost) FROM billing_export
# WHERE labels.key = 'team' GROUP BY labels.value
```

---

## 1.13 Real-world Example: Setting Up a Multi-Environment Project Structure

**Scenario:** You're a DevOps engineer at an e-commerce startup. Set up GCP for dev, staging, and production environments.

```bash
# Step 1: Create projects
gcloud projects create ecommerce-dev-2024 --name="E-Commerce Dev"
gcloud projects create ecommerce-staging-2024 --name="E-Commerce Staging"
gcloud projects create ecommerce-prod-2024 --name="E-Commerce Prod"

# Step 2: Link billing
for project in ecommerce-dev-2024 ecommerce-staging-2024 ecommerce-prod-2024; do
  gcloud billing projects link $project \
    --billing-account=0X0X0X-0X0X0X-0X0X0X
done

# Step 3: Enable required APIs in all projects
APIS="compute.googleapis.com storage.googleapis.com sqladmin.googleapis.com run.googleapis.com container.googleapis.com"
for project in ecommerce-dev-2024 ecommerce-staging-2024 ecommerce-prod-2024; do
  gcloud services enable $APIS --project=$project
done

# Step 4: Create service accounts per environment
for env in dev staging prod; do
  gcloud iam service-accounts create app-sa \
    --display-name="App Service Account ($env)" \
    --project=ecommerce-${env}-2024
done

# Step 5: Set up gcloud configurations for easy switching
for env in dev staging prod; do
  gcloud config configurations create ecommerce-$env
  gcloud config set project ecommerce-${env}-2024
  gcloud config set compute/region us-central1
  gcloud config set compute/zone us-central1-a
done

# Step 6: Label projects
gcloud projects update ecommerce-dev-2024 --update-labels=env=dev,app=ecommerce
gcloud projects update ecommerce-staging-2024 --update-labels=env=staging,app=ecommerce
gcloud projects update ecommerce-prod-2024 --update-labels=env=prod,app=ecommerce

# Step 7: Grant team access
# Developers get Editor on dev, Viewer on staging
gcloud projects add-iam-policy-binding ecommerce-dev-2024 \
  --member="group:developers@company.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding ecommerce-staging-2024 \
  --member="group:developers@company.com" \
  --role="roles/viewer"

# Only DevOps gets access to production
gcloud projects add-iam-policy-binding ecommerce-prod-2024 \
  --member="group:devops@company.com" \
  --role="roles/editor"
```

---

## Module 1 Summary

| Concept | Command | Purpose |
|---------|---------|---------|
| Initialize | `gcloud init` | First-time setup |
| Auth | `gcloud auth login` | Authenticate |
| Project create | `gcloud projects create ID` | New project |
| Set project | `gcloud config set project ID` | Set default |
| Enable API | `gcloud services enable API` | Activate service |
| IAM grant | `gcloud projects add-iam-policy-binding` | Grant access |
| Service account | `gcloud iam service-accounts create` | App identity |
| Configurations | `gcloud config configurations create` | Multi-env |
| Labels | `--update-labels=key=value` | Organize resources |

**Next: Module 2 — Compute Services →**
