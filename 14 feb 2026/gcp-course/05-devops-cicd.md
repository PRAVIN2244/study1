# Module 5: DevOps & CI/CD

---

## 5.1 Artifact Registry (Container & Package Registry)

Stores Docker images, npm packages, Maven artifacts, Python packages. Replaces the deprecated Container Registry (gcr.io).

### Creating a Repository

```bash
# Enable the API
gcloud services enable artifactregistry.googleapis.com

# Create a Docker repository
gcloud artifacts repositories create my-docker-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Production Docker images"

# Create an npm repository
gcloud artifacts repositories create my-npm-repo \
  --repository-format=npm \
  --location=us-central1

# Create a Python repository
gcloud artifacts repositories create my-python-repo \
  --repository-format=python \
  --location=us-central1
```

**Output:**
```
Create request issued for: [my-docker-repo]
Waiting for operation to complete...done.
Created repository [my-docker-repo].
```

### Pushing Docker Images

```bash
# Configure Docker to authenticate with Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag your image
docker tag my-app:latest \
  us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app:v1.0.0

# Push
docker push us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app:v1.0.0
```

**Output:**
```
The push refers to repository [us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app]
abc123def456: Pushed
789ghi012jkl: Pushed
v1.0.0: digest: sha256:abcdef123456... size: 1234
```

### Listing Images

```bash
gcloud artifacts docker images list \
  us-central1-docker.pkg.dev/my-project/my-docker-repo
```
**Output:**
```
IMAGE                                                              DIGEST         CREATE_TIME          UPDATE_TIME
us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app       sha256:abcdef  2024-01-15T10:30:00  2024-01-15T10:30:00
```

### Cleanup Policies

```bash
# Delete images older than 30 days (keep last 5 versions)
gcloud artifacts repositories set-cleanup-policies my-docker-repo \
  --location=us-central1 \
  --policy=policy.json

# policy.json:
# {
#   "cleanupPolicies": {
#     "delete-old": {
#       "action": "DELETE",
#       "condition": {
#         "olderThan": "2592000s",
#         "tagState": "ANY"
#       }
#     },
#     "keep-recent": {
#       "action": "KEEP",
#       "mostRecentVersions": {
#         "keepCount": 5
#       }
#     }
#   }
# }
```

---

## 5.2 Cloud Build (CI/CD Pipeline)

Serverless CI/CD platform. Runs build steps in containers.

### Basic Build — Building a Docker Image

```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Build from current directory (uses Dockerfile)
gcloud builds submit --tag us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app:v1.0.0
```

**What it does:** Uploads source code to Cloud Storage, builds the Docker image on Google's servers, pushes to Artifact Registry.

**Output:**
```
Creating temporary tarball archive of 5 file(s) totalling 2.1 KiB before compression.
Uploading tarball of [.] to [gs://my-project_cloudbuild/source/1705312200.123456-abcdef.tgz]
Created [https://cloudbuild.googleapis.com/v1/projects/my-project/locations/global/builds/abc-123-def].
Logs are available at [https://console.cloud.google.com/cloud-build/builds/abc-123-def].
...
DONE
```

### Cloud Build Configuration (cloudbuild.yaml)

```yaml
# cloudbuild.yaml — Multi-step pipeline
steps:
  # Step 1: Install dependencies
  - name: 'node:20'
    entrypoint: 'npm'
    args: ['ci']

  # Step 2: Run linter
  - name: 'node:20'
    entrypoint: 'npm'
    args: ['run', 'lint']

  # Step 3: Run tests
  - name: 'node:20'
    entrypoint: 'npm'
    args: ['run', 'test']
    env:
      - 'NODE_ENV=test'
      - 'DATABASE_URL=postgresql://test:test@localhost:5432/testdb'

  # Step 4: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app:latest'
      - '.'

  # Step 5: Push image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app'

  # Step 6: Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'my-app'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app:$SHORT_SHA'
      - '--region=us-central1'
      - '--platform=managed'

# Store built images in Artifact Registry
images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/my-docker-repo/my-app:latest'

# Build options
options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'

# Substitution variables
substitutions:
  _DEPLOY_ENV: 'production'

timeout: '1200s'  # 20 minutes max
```

```bash
# Run the build
gcloud builds submit --config=cloudbuild.yaml .
```

### Built-in Substitution Variables

| Variable | Value |
|----------|-------|
| `$PROJECT_ID` | Your GCP project ID |
| `$BUILD_ID` | Unique build ID |
| `$COMMIT_SHA` | Full git commit SHA |
| `$SHORT_SHA` | First 7 chars of commit SHA |
| `$BRANCH_NAME` | Git branch name |
| `$TAG_NAME` | Git tag name |
| `$REPO_NAME` | Repository name |

### Build Triggers (Auto-build on Git Push)

```bash
# Connect a GitHub repository
# (Done via Console: Cloud Build > Triggers > Connect Repository)

# Create a trigger — build on push to main
gcloud builds triggers create github \
  --name="deploy-on-push" \
  --repo-name=my-app \
  --repo-owner=my-org \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml

# Create a trigger — build on pull request
gcloud builds triggers create github \
  --name="pr-checks" \
  --repo-name=my-app \
  --repo-owner=my-org \
  --pull-request-pattern="^main$" \
  --build-config=cloudbuild-pr.yaml \
  --comment-control=COMMENTS_ENABLED

# List triggers
gcloud builds triggers list
```

### Viewing Build History

```bash
# List recent builds
gcloud builds list --limit=10
```
**Output:**
```
ID                                    CREATE_TIME                DURATION  SOURCE                    STATUS
abc-123-def                           2024-01-15T10:30:00+00:00  2M15S    gs://my-project_cloud...  SUCCESS
def-456-ghi                           2024-01-14T15:20:00+00:00  3M42S    gs://my-project_cloud...  FAILURE
```

```bash
# View build logs
gcloud builds log abc-123-def
```

---

## 5.3 Cloud Deploy (Continuous Delivery)

Managed service for deploying to GKE, Cloud Run, or GCE with approval gates and rollback.

### Pipeline Configuration

```yaml
# clouddeploy.yaml — Delivery pipeline
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata:
  name: my-app-pipeline
description: Deploy my-app through dev → staging → prod
serialPipeline:
  stages:
    - targetId: dev
      profiles: [dev]
    - targetId: staging
      profiles: [staging]
      strategy:
        canary:
          runtimeConfig:
            cloudRun:
              automaticTrafficControl: true
          canaryDeployment:
            percentages: [25, 50, 75]
    - targetId: prod
      profiles: [prod]
      strategy:
        standard:
          verify: true
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: dev
description: Dev environment
run:
  location: projects/my-project/locations/us-central1
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: staging
description: Staging environment
run:
  location: projects/my-project/locations/us-central1
requireApproval: true
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: prod
description: Production environment
run:
  location: projects/my-project/locations/us-central1
requireApproval: true
```

```bash
# Register the pipeline
gcloud deploy apply --file=clouddeploy.yaml --region=us-central1

# Create a release
gcloud deploy releases create release-v1 \
  --delivery-pipeline=my-app-pipeline \
  --region=us-central1 \
  --images=my-app=us-central1-docker.pkg.dev/my-project/my-docker-repo/my-app:v1.0.0

# Promote from dev to staging
gcloud deploy releases promote \
  --release=release-v1 \
  --delivery-pipeline=my-app-pipeline \
  --region=us-central1

# Approve a promotion (when requireApproval=true)
gcloud deploy rollouts approve ROLLOUT_NAME \
  --delivery-pipeline=my-app-pipeline \
  --release=release-v1 \
  --region=us-central1
```

---

## 5.4 Terraform on GCP (Infrastructure as Code)

### Setup

```bash
# Install Terraform
sudo apt-get update && sudo apt-get install -y terraform

# Or download directly
curl -fsSL https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip -o tf.zip
unzip tf.zip && sudo mv terraform /usr/local/bin/

# Verify
terraform version
```
**Output:**
```
Terraform v1.7.0
```

### Basic GCP Infrastructure with Terraform

```hcl
# main.tf

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Store state in Cloud Storage
  backend "gcs" {
    bucket = "my-project-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

# VPC
resource "google_compute_network" "vpc" {
  name                    = "${var.environment}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "web" {
  name          = "${var.environment}-web-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

resource "google_compute_subnetwork" "db" {
  name          = "${var.environment}-db-subnet"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true
}

# Firewall
resource "google_compute_firewall" "allow_http" {
  name    = "${var.environment}-allow-http"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["web"]
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${var.environment}-allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/8"]
}

# Compute Engine Instance
resource "google_compute_instance" "web_server" {
  name         = "${var.environment}-web-server"
  machine_type = "e2-medium"
  zone         = "${var.region}-a"

  tags = ["web"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 20
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.web.id
    access_config {} # Gives external IP
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y nginx
    echo "Hello from ${var.environment}" > /var/www/html/index.html
  EOF

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Cloud SQL
resource "google_sql_database_instance" "postgres" {
  name             = "${var.environment}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-custom-2-8192"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = 50
    disk_autoresize   = true

    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = var.environment == "prod" ? true : false
}

resource "google_sql_database" "app_db" {
  name     = "myapp"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = "appuser"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password  # Pass via TF_VAR_db_password env var
}

variable "db_password" {
  type      = string
  sensitive = true
}

# Cloud Storage Bucket
resource "google_storage_bucket" "assets" {
  name     = "${var.project_id}-${var.environment}-assets"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  versioning {
    enabled = true
  }
}

# Outputs
output "web_server_ip" {
  value = google_compute_instance.web_server.network_interface[0].access_config[0].nat_ip
}

output "database_connection" {
  value = google_sql_database_instance.postgres.connection_name
}

output "bucket_url" {
  value = google_storage_bucket.assets.url
}
```

### Terraform Workflow

```bash
# Initialize (downloads providers)
terraform init
```
**Output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
- Installing hashicorp/google v5.12.0...
Terraform has been successfully initialized!
```

```bash
# Plan (preview changes)
terraform plan -var="project_id=my-project" -var="db_password=SecureP@ss123"
```
**Output:**
```
Terraform will perform the following actions:

  # google_compute_firewall.allow_http will be created
  + resource "google_compute_firewall" "allow_http" { ... }

  # google_compute_instance.web_server will be created
  + resource "google_compute_instance" "web_server" { ... }

  # google_compute_network.vpc will be created
  + resource "google_compute_network" "vpc" { ... }

  # google_sql_database_instance.postgres will be created
  + resource "google_sql_database_instance" "postgres" { ... }

Plan: 8 to add, 0 to change, 0 to destroy.
```

```bash
# Apply (create resources)
terraform apply -var="project_id=my-project" -var="db_password=SecureP@ss123" -auto-approve
```

```bash
# Destroy (tear down everything)
terraform destroy -var="project_id=my-project" -var="db_password=SecureP@ss123" -auto-approve
```

### Using tfvars Files

```hcl
# dev.tfvars
project_id  = "my-project-dev"
region      = "us-central1"
environment = "dev"
db_password = "DevP@ss123"

# prod.tfvars
project_id  = "my-project-prod"
region      = "us-central1"
environment = "prod"
db_password = "Pr0dP@ss!456"
```

```bash
terraform apply -var-file=dev.tfvars
terraform apply -var-file=prod.tfvars
```

---

## 5.5 Real-world Example: Full CI/CD Pipeline for a Node.js App

```
Developer pushes code → Cloud Build triggers →
  1. Install deps
  2. Lint
  3. Test
  4. Build Docker image
  5. Push to Artifact Registry
  6. Deploy to Cloud Run (dev)
  7. Run smoke tests
  8. Promote to staging (manual approval)
  9. Promote to prod (manual approval)
```

```yaml
# cloudbuild.yaml
steps:
  - id: 'install'
    name: 'node:20'
    entrypoint: 'npm'
    args: ['ci']

  - id: 'lint'
    name: 'node:20'
    entrypoint: 'npm'
    args: ['run', 'lint']
    waitFor: ['install']

  - id: 'test'
    name: 'node:20'
    entrypoint: 'npm'
    args: ['run', 'test', '--', '--coverage']
    waitFor: ['install']
    env:
      - 'NODE_ENV=test'

  - id: 'build-image'
    name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/apps/my-api:$SHORT_SHA'
      - '.'
    waitFor: ['lint', 'test']

  - id: 'push-image'
    name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/apps/my-api:$SHORT_SHA']
    waitFor: ['build-image']

  - id: 'deploy-dev'
    name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'my-api'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/apps/my-api:$SHORT_SHA'
      - '--region=us-central1'
      - '--set-env-vars=ENV=dev'
    waitFor: ['push-image']

  - id: 'smoke-test'
    name: 'curlimages/curl'
    entrypoint: 'sh'
    args:
      - '-c'
      - |
        sleep 10
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://my-api-abc.a.run.app/api/health)
        if [ "$STATUS" != "200" ]; then
          echo "Smoke test failed! Status: $STATUS"
          exit 1
        fi
        echo "Smoke test passed!"
    waitFor: ['deploy-dev']

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/apps/my-api:$SHORT_SHA'

options:
  machineType: 'E2_HIGHCPU_8'
```

---

## Module 5 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Cloud Build: `PERMISSION_DENIED` | Cloud Build SA missing roles | Grant `roles/run.admin`, `roles/iam.serviceAccountUser` to Cloud Build SA |
| Cloud Build: `Step exceeded timeout` | Build step takes too long | Increase `timeout` in cloudbuild.yaml |
| Artifact Registry: `DENIED: Permission denied` | Docker not configured | Run `gcloud auth configure-docker REGION-docker.pkg.dev` |
| Terraform: `Error acquiring state lock` | Another process holds the lock | Run `terraform force-unlock LOCK_ID` |
| Terraform: `Provider produced inconsistent result` | API changed during apply | Run `terraform refresh` then `terraform apply` |
| Terraform: `Error creating Instance: googleapi: Error 403` | API not enabled | `gcloud services enable compute.googleapis.com` |

**Next: Module 6 — Monitoring, Logging & Security →**
