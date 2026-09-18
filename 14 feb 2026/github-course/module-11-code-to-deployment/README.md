# Module 11 — How Code Moves from GitHub to K8s/EC2

## Overview

This module traces the complete journey of code from a developer's machine to a running application on Kubernetes or EC2. Every step is explained with what happens, where it happens, and what tools are involved.

## The Complete Flow (High Level)

```
Developer's Machine          GitHub                    CI/CD (Actions)           Infrastructure
┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐      ┌──────────────┐
│ Write Code   │─────▶│ Push to Repo │─────▶│ Build → Test → Scan │─────▶│ Deploy to    │
│ git commit   │      │ (main branch)│      │ → Package → Push    │      │ K8s or EC2   │
│ git push     │      │              │      │ Docker Image         │      │              │
└──────────────┘      └──────────────┘      └──────────────────────┘      └──────────────┘
```

## Step-by-Step: Code to Kubernetes

### Step 1: Developer Writes Code and Pushes

```bash
# Developer works on a feature branch
git checkout -b feature/user-auth
# ... writes code ...
git add .
git commit -m "Add user authentication"
git push origin feature/user-auth
```

**What happens:**
- Code is pushed to GitHub
- A new branch `feature/user-auth` appears in the repository

### Step 2: Developer Opens a Pull Request

```bash
gh pr create --title "Add user authentication" --body "Implements JWT auth"
```

**What happens:**
- Pull Request is created on GitHub
- GitHub Actions workflow triggers (on `pull_request` event)
- CI pipeline runs: lint → test → security scan
- Results appear as status checks on the PR

```
PR #42: Add user authentication
├── Status Checks:
│   ├── ci/lint         ✅ Passed
│   ├── ci/test         ✅ Passed
│   ├── security/codeql ✅ No issues
│   └── ci/build        ✅ Passed
├── Reviews:
│   └── @reviewer       ✅ Approved
└── Ready to merge
```

### Step 3: PR is Merged to Main

```
Developer clicks "Merge pull request"
    │
    ▼
Code is now in the 'main' branch
    │
    ▼
GitHub Actions workflow triggers (on push to main)
```

### Step 4: CI/CD Pipeline Runs

The workflow file `.github/workflows/deploy.yml` executes:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # Step 4a: Checkout code from GitHub
      - uses: actions/checkout@v4
      # GitHub runner now has the source code

      # Step 4b: Run tests
      - run: npm ci && npm test

      # Step 4c: Build Docker image
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/myorg/myapp:${{ github.sha }}
      # Docker image is now in GitHub Container Registry (GHCR)
```

**What happens at each sub-step:**

```
Step 4a: Checkout
┌─────────────┐         ┌─────────────┐
│   GitHub     │────────▶│  Runner VM  │
│   Repository │  clone  │  (Ubuntu)   │
└─────────────┘         └─────────────┘
Source code is copied to /home/runner/work/repo/repo

Step 4b: Test
┌─────────────┐
│  Runner VM  │
│  npm ci     │  ← installs dependencies from package-lock.json
│  npm test   │  ← runs test suite
│  Exit 0     │  ← tests pass (exit code 0 = success)
└─────────────┘

Step 4c: Docker Build & Push
┌─────────────┐         ┌─────────────┐
│  Runner VM  │         │    GHCR     │
│  docker     │────────▶│  (Registry) │
│  build+push │  push   │  ghcr.io/   │
└─────────────┘         └─────────────┘
Image: ghcr.io/myorg/myapp:abc123def (tagged with commit SHA)
```

### Step 5: Deploy to Kubernetes

```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production          # Requires approval
    steps:
      # Step 5a: Authenticate to AWS
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-deploy
          aws-region: us-east-1

      # Step 5b: Update kubeconfig
      - run: aws eks update-kubeconfig --name my-cluster --region us-east-1

      # Step 5c: Deploy to Kubernetes
      - run: |
          kubectl set image deployment/myapp \
            myapp=ghcr.io/myorg/myapp:${{ github.sha }} \
            --namespace production

      # Step 5d: Wait for rollout
      - run: kubectl rollout status deployment/myapp -n production --timeout=300s
```

**What happens:**

```
Step 5a: Authentication
┌─────────────┐         ┌─────────────┐
│  Runner VM  │────────▶│   AWS IAM   │
│  OIDC Token │  assume │   Role      │
└─────────────┘  role   └─────────────┘
Runner gets temporary AWS credentials (no stored secrets needed)

Step 5b: Kubeconfig
┌─────────────┐         ┌─────────────┐
│  Runner VM  │────────▶│   AWS EKS   │
│  aws eks    │  get    │   Cluster   │
│  update-    │  config │             │
│  kubeconfig │         └─────────────┘
Runner can now talk to the Kubernetes cluster

Step 5c: Deploy
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Runner VM  │────────▶│   K8s API   │────────▶│   K8s Pods  │
│  kubectl    │  update │   Server    │  create  │  (new image)│
│  set image  │  deploy │             │  pods    │             │
└─────────────┘         └─────────────┘         └──────┬──────┘
                                                        │
                                                        ▼
                                                ┌─────────────┐
                                                │    GHCR     │
                                                │  pull image │
                                                └─────────────┘
K8s pulls the new image from GHCR and starts new pods

Step 5d: Rollout Verification
┌─────────────┐         ┌─────────────┐
│  Runner VM  │────────▶│   K8s API   │
│  kubectl    │  watch  │   Server    │
│  rollout    │  status │             │
│  status     │         └─────────────┘
Waits until all new pods are running and healthy
```

**Expected console output:**
```
deployment.apps/myapp image updated
Waiting for deployment "myapp" rollout to finish:
  1 out of 3 new replicas have been updated...
  2 out of 3 new replicas have been updated...
  3 out of 3 new replicas have been updated...
Waiting for deployment "myapp" rollout to finish:
  2 of 3 updated replicas are available...
  3 of 3 updated replicas are available...
deployment "myapp" successfully rolled out
```

## Complete Flow Diagram: GitHub to Kubernetes

```
DEVELOPER                  GITHUB                    RUNNER                    AWS / K8s
─────────                  ──────                    ──────                    ─────────

git push ──────────────▶ Repository
                           │
                           │ webhook trigger
                           ▼
                         Actions ──────────────────▶ Spin up Ubuntu VM
                                                     │
                                                     ├── git clone (checkout)
                                                     ├── npm ci (install deps)
                                                     ├── npm test (run tests)
                                                     │
                                                     ├── docker build
                                                     ├── docker push ────────▶ GHCR (image stored)
                                                     │
                                                     ├── aws configure ──────▶ IAM (get credentials)
                                                     ├── aws eks kubeconfig ─▶ EKS (get cluster config)
                                                     ├── kubectl set image ──▶ K8s API Server
                                                     │                         │
                                                     │                         ├── Create new pods
                                                     │                         ├── Pull image from GHCR
                                                     │                         ├── Start containers
                                                     │                         └── Health checks pass
                                                     │
                                                     └── kubectl rollout ────▶ Verify deployment
                                                          status               │
                                                                               ▼
                                                                         App is LIVE
                                                                         https://myapp.example.com
```

## Step-by-Step: Code to EC2

### Method 1: Direct Deployment (SSH)

```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build application
        run: npm ci && npm run build

      # Copy files to EC2 via SCP
      - name: Copy to EC2
        uses: appleboy/scp-action@v0.1.7
        with:
          host: ${{ secrets.EC2_HOST }}           # e.g., 54.123.45.67
          username: ${{ secrets.EC2_USER }}        # e.g., ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}          # Private SSH key
          source: "dist/*"                        # Built files
          target: "/var/www/myapp"                 # Destination on EC2

      # Restart application on EC2
      - name: Restart app
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd /var/www/myapp
            npm install --production
            pm2 restart myapp
```

**Flow:**
```
GitHub Runner ──── SCP (port 22) ────▶ EC2 Instance
                                        │
                                        ├── Files copied to /var/www/myapp
                                        ├── npm install (production deps)
                                        └── pm2 restart (app restarts)
```

### Method 2: Docker on EC2

```yaml
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Build and push Docker image
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/myorg/myapp:${{ github.sha }}

      # SSH into EC2 and pull new image
      - uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            # Login to GHCR
            echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin

            # Pull new image
            docker pull ghcr.io/myorg/myapp:${{ github.sha }}

            # Stop old container, start new one
            docker stop myapp || true
            docker rm myapp || true
            docker run -d --name myapp -p 80:3000 \
              ghcr.io/myorg/myapp:${{ github.sha }}
```

**Flow:**
```
Runner ── docker push ──▶ GHCR (image stored)
Runner ── SSH ──────────▶ EC2 Instance
                           │
                           ├── docker pull (from GHCR)
                           ├── docker stop (old container)
                           └── docker run (new container)
```

### Method 3: AWS CodeDeploy (Production-Grade)

```yaml
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-deploy
          aws-region: us-east-1

      # Upload to S3
      - run: |
          zip -r app.zip . -x '.git/*'
          aws s3 cp app.zip s3://my-deploy-bucket/app-${{ github.sha }}.zip

      # Trigger CodeDeploy
      - run: |
          aws deploy create-deployment \
            --application-name myapp \
            --deployment-group-name production \
            --s3-location bucket=my-deploy-bucket,key=app-${{ github.sha }}.zip,bundleType=zip
```

**Flow:**
```
Runner ── upload ──▶ S3 Bucket ──▶ CodeDeploy ──▶ EC2 Instances (fleet)
                                      │
                                      ├── Downloads zip from S3
                                      ├── Runs appspec.yml hooks
                                      │   ├── BeforeInstall: stop app
                                      │   ├── Install: copy files
                                      │   ├── AfterInstall: npm install
                                      │   └── ApplicationStart: start app
                                      └── Reports deployment status
```

### Method 4: ECR + ECS (Container on AWS)

```yaml
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-deploy
          aws-region: us-east-1

      # Login to ECR
      - uses: aws-actions/amazon-ecr-login@v2
        id: ecr-login

      # Build and push to ECR
      - run: |
          docker build -t ${{ steps.ecr-login.outputs.registry }}/myapp:${{ github.sha }} .
          docker push ${{ steps.ecr-login.outputs.registry }}/myapp:${{ github.sha }}

      # Update ECS service (pulls new image automatically)
      - run: |
          aws ecs update-service \
            --cluster production \
            --service myapp \
            --force-new-deployment
```

**Flow:**
```
Runner ── docker push ──▶ ECR (AWS Container Registry)
Runner ── ecs update ───▶ ECS Service
                           │
                           ├── Pulls new image from ECR
                           ├── Starts new task (container)
                           ├── Health check passes
                           ├── Routes traffic to new task
                           └── Stops old task
```

## Comparison: Deployment Methods

| Method | Best For | Complexity | Downtime |
|--------|----------|-----------|----------|
| **SSH + SCP** | Single server, simple apps | Low | Brief (restart) |
| **Docker on EC2** | Single server, containerized | Low | Brief (container swap) |
| **CodeDeploy** | EC2 fleet, rolling deploys | Medium | Zero (rolling) |
| **ECR + ECS** | Container orchestration on AWS | Medium | Zero (blue-green) |
| **ECR + EKS** | Kubernetes on AWS | High | Zero (rolling) |
| **GHCR + K8s** | Any Kubernetes cluster | Medium | Zero (rolling) |

## Security at Each Step

```
Step                    Security Measure
────                    ────────────────
git push            →   Branch protection, signed commits
Pull Request        →   Required reviews, status checks, CODEOWNERS
CI Pipeline         →   Pinned action versions, minimal permissions
Docker Build        →   Multi-stage builds, non-root user, image scanning
Image Push          →   GHCR/ECR authentication, image signing
AWS Authentication  →   OIDC (no stored credentials), least-privilege IAM role
K8s Deploy          →   RBAC, network policies, pod security standards
Runtime             →   Health checks, resource limits, secrets management
```

## Troubleshooting Deployments

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ImagePullBackOff` | K8s can't pull image from registry | Check image name, registry auth secret |
| `CrashLoopBackOff` | Container starts and immediately crashes | Check container logs: `kubectl logs pod-name` |
| `Permission denied` | SSH key or IAM role issue | Verify credentials, check IAM policy |
| `Connection refused` | App not listening on expected port | Check Dockerfile EXPOSE, container port mapping |
| `Deployment timeout` | Health check failing | Check readiness probe, app startup time |
| `403 Forbidden` | GITHUB_TOKEN lacks permissions | Add `permissions:` block to workflow |
