# Module 28: CI/CD with Docker

Docker is the backbone of modern CI/CD pipelines. This module covers
building, testing, scanning, and deploying container images across
GitHub Actions, GitLab CI, and Jenkins.

### Topics Covered

```
28.1  Docker's Role in CI/CD
28.2  Registry Authentication in CI
28.3  GitHub Actions — Complete Docker Pipeline
28.4  GitLab CI — Complete Docker Pipeline
28.5  Jenkins — Docker Pipeline
28.6  Multi-Stage CI: Build, Test, Scan, Push
28.7  Image Caching Strategies in CI
28.8  Security Scanning in CI (Trivy, Snyk, Grype)
28.9  Automated Tagging and Versioning
28.10 Deployment Strategies from CI
28.11 Mono-Repo and Multi-Service Pipelines
28.12 Common Errors and Troubleshooting
```

---

## 28.1 Docker's Role in CI/CD

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE WITH DOCKER                   │
│                                                                 │
│  Source Code                                                    │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Build   │─▶│  Test    │─▶│  Scan    │─▶│  Push    │       │
│  │  Image   │  │  Image   │  │  Image   │  │  Image   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                  │              │
│                                                  ▼              │
│                                            ┌──────────┐        │
│                                            │  Deploy  │        │
│                                            │  (Swarm/ │        │
│                                            │   K8s)   │        │
│                                            └──────────┘        │
│                                                                 │
│  Build: docker buildx build (multi-stage, multi-platform)      │
│  Test:  docker run <test-image> npm test                       │
│  Scan:  trivy image <image>                                    │
│  Push:  docker push to registry                                │
│  Deploy: kubectl apply / docker stack deploy                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 28.2 Registry Authentication in CI

```bash
# Docker Hub
$ echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# AWS ECR
$ aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Google Container Registry (GCR)
$ echo "$GCP_SERVICE_KEY" | docker login -u _json_key --password-stdin gcr.io

# Google Artifact Registry
$ echo "$GCP_SERVICE_KEY" | docker login -u _json_key --password-stdin us-docker.pkg.dev

# GitHub Container Registry (GHCR)
$ echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

# Azure Container Registry (ACR)
$ az acr login --name myregistry
# or
$ docker login myregistry.azurecr.io -u "$ACR_USERNAME" -p "$ACR_PASSWORD"

# Self-hosted registry
$ docker login registry.example.com -u "$REG_USER" -p "$REG_PASS"
```

---

## 28.3 GitHub Actions — Complete Docker Pipeline

```yaml
# .github/workflows/docker.yml
name: Docker CI/CD

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write

    steps:
      # 1. Checkout code
      - name: Checkout
        uses: actions/checkout@v4

      # 2. Set up BuildKit with multi-platform support
      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # 3. Login to registry
      - name: Login to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # 4. Extract metadata (tags, labels)
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      # 5. Build and push
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          sbom: true
          provenance: true

      # 6. Security scan
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.version }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
```

### Key Actions Explained

```
# docker/setup-buildx-action
#   Creates a BuildKit builder instance for the workflow
#   Enables multi-platform builds and advanced caching

# docker/metadata-action
#   Automatically generates image tags based on git context:
#     main branch  → ghcr.io/org/app:main
#     v1.2.3 tag   → ghcr.io/org/app:1.2.3, ghcr.io/org/app:1.2
#     PR #42       → ghcr.io/org/app:pr-42
#     commit sha   → ghcr.io/org/app:sha-abc1234

# docker/build-push-action
#   cache-from: type=gha  → uses GitHub Actions cache (fast, free)
#   cache-to: type=gha,mode=max → caches all layers, not just final
#   sbom: true → generates Software Bill of Materials
#   provenance: true → generates build provenance attestation
```

---

## 28.4 GitLab CI — Complete Docker Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - scan
  - push
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE: $CI_REGISTRY_IMAGE
  TAG: $CI_COMMIT_SHORT_SHA

# Use Docker-in-Docker service
services:
  - docker:24-dind

.docker-base:
  image: docker:24
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

build:
  extends: .docker-base
  stage: build
  script:
    - docker buildx create --use
    - docker buildx build
        --cache-from type=registry,ref=$IMAGE:cache
        --cache-to type=registry,ref=$IMAGE:cache,mode=max
        --tag $IMAGE:$TAG
        --push
        .

test:
  extends: .docker-base
  stage: test
  script:
    - docker run --rm $IMAGE:$TAG npm test
  allow_failure: false

scan:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code 1 --severity CRITICAL $IMAGE:$TAG
  allow_failure: true

push-latest:
  extends: .docker-base
  stage: push
  script:
    - docker pull $IMAGE:$TAG
    - docker tag $IMAGE:$TAG $IMAGE:latest
    - docker push $IMAGE:latest
  only:
    - main

deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/myapp myapp=$IMAGE:$TAG -n staging
  environment:
    name: staging
  only:
    - main
```

---

## 28.5 Jenkins — Docker Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        REGISTRY = 'registry.example.com'
        IMAGE = "${REGISTRY}/myapp"
        TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Build') {
            steps {
                script {
                    docker.build("${IMAGE}:${TAG}", "--no-cache .")
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    docker.image("${IMAGE}:${TAG}").inside {
                        sh 'npm test'
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh "trivy image --exit-code 0 --severity HIGH,CRITICAL ${IMAGE}:${TAG}"
            }
        }

        stage('Push') {
            when { branch 'main' }
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", 'registry-creds') {
                        docker.image("${IMAGE}:${TAG}").push()
                        docker.image("${IMAGE}:${TAG}").push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh "kubectl set image deployment/myapp myapp=${IMAGE}:${TAG}"
            }
        }
    }

    post {
        always {
            sh 'docker system prune -f'
        }
    }
}
```

---

## 28.6 Multi-Stage CI: Build, Test, Scan, Push

### Dockerfile Designed for CI

```dockerfile
# syntax=docker/dockerfile:1

# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Stage 2: Test (CI runs this stage)
FROM deps AS test
COPY . .
RUN npm run lint
RUN npm test -- --coverage
# Test results and coverage are available in this stage

# Stage 3: Build
FROM deps AS build
COPY . .
RUN npm run build

# Stage 4: Production image
FROM node:20-alpine AS production
RUN addgroup -g 1001 app && adduser -u 1001 -G app -s /bin/sh -D app
WORKDIR /app
COPY --from=build --chown=app:app /app/dist ./dist
COPY --from=deps --chown=app:app /app/node_modules ./node_modules
COPY --from=deps --chown=app:app /app/package.json ./
USER app
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

```bash
# CI pipeline commands:

# 1. Run tests (build only up to test stage)
$ docker buildx build --target test -t myapp:test .

# 2. Extract test coverage report
$ docker buildx build --target test --output type=local,dest=./coverage .

# 3. Build production image
$ docker buildx build --target production -t myapp:v1.0.0 .

# 4. Scan for vulnerabilities
$ trivy image --severity CRITICAL,HIGH myapp:v1.0.0

# 5. Push to registry
$ docker push myapp:v1.0.0
```

---

## 28.7 Image Caching Strategies in CI

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Strategy         │ How It Works                                 │
├──────────────────┼──────────────────────────────────────────────┤
│ Registry cache   │ Push cache layers to registry. Pull on next │
│                  │ build. Works across CI runners.              │
│                  │ --cache-from type=registry,ref=img:cache     │
│                  │ --cache-to type=registry,ref=img:cache       │
├──────────────────┼──────────────────────────────────────────────┤
│ GHA cache        │ GitHub Actions native cache. Fast, free.     │
│                  │ --cache-from type=gha                        │
│                  │ --cache-to type=gha,mode=max                 │
├──────────────────┼──────────────────────────────────────────────┤
│ Local cache      │ Cache on the CI runner's disk. Fast but      │
│                  │ only works with persistent runners.          │
│                  │ --cache-from type=local,src=/tmp/cache       │
│                  │ --cache-to type=local,dest=/tmp/cache        │
├──────────────────┼──────────────────────────────────────────────┤
│ Inline cache     │ Embed cache metadata in the pushed image.    │
│                  │ No separate cache image needed.              │
│                  │ --cache-to type=inline                       │
│                  │ Limited: only caches final stage layers.     │
├──────────────────┼──────────────────────────────────────────────┤
│ S3 cache         │ Store cache in S3 bucket. Cross-region.      │
│                  │ --cache-to type=s3,region=us-east-1,         │
│                  │   bucket=my-cache                            │
└──────────────────┴──────────────────────────────────────────────┘
```

```bash
# Registry cache (most portable — works everywhere)
$ docker buildx build \
    --cache-from type=registry,ref=registry.com/myapp:cache \
    --cache-to type=registry,ref=registry.com/myapp:cache,mode=max \
    -t registry.com/myapp:v1.0.0 \
    --push .

# mode=max caches ALL layers (including intermediate stages)
# mode=min caches only the final stage layers (default)
```

---

## 28.8 Security Scanning in CI (Trivy, Snyk, Grype)

### Trivy (Most Popular — Free, Open Source)

```bash
# Install Trivy
$ curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan an image
$ trivy image myapp:latest
# Shows: CRITICAL, HIGH, MEDIUM, LOW vulnerabilities

# Fail CI if critical vulnerabilities found
$ trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scan and output SARIF (for GitHub Security tab)
$ trivy image --format sarif --output results.sarif myapp:latest

# Scan a Dockerfile (misconfigurations)
$ trivy config Dockerfile

# Scan filesystem (dependencies)
$ trivy fs --scanners vuln,secret .

# Ignore unfixed vulnerabilities
$ trivy image --ignore-unfixed myapp:latest
```

### Grype (Anchore — Free, Open Source)

```bash
$ curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
$ grype myapp:latest
$ grype myapp:latest --fail-on critical
```

### Snyk (Commercial — Free Tier Available)

```bash
$ snyk container test myapp:latest
$ snyk container test myapp:latest --severity-threshold=high
```

### Scanning in GitHub Actions

```yaml
- name: Scan with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:latest
    format: 'table'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'
    ignore-unfixed: true
```

---

## 28.9 Automated Tagging and Versioning

### Semantic Versioning from Git Tags

```bash
# Tag format: v1.2.3
# Generated image tags:
#   registry.com/myapp:1.2.3
#   registry.com/myapp:1.2
#   registry.com/myapp:1
#   registry.com/myapp:latest

# Script for automated tagging
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
VERSION=${VERSION#v}  # Remove 'v' prefix
MAJOR=$(echo $VERSION | cut -d. -f1)
MINOR=$(echo $VERSION | cut -d. -f2)
SHA=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

docker buildx build \
    -t registry.com/myapp:${VERSION} \
    -t registry.com/myapp:${MAJOR}.${MINOR} \
    -t registry.com/myapp:${MAJOR} \
    -t registry.com/myapp:sha-${SHA} \
    -t registry.com/myapp:${BRANCH} \
    --push .
```

### GitHub Actions Metadata Action

```yaml
# Automatic tag generation based on git context
- uses: docker/metadata-action@v5
  with:
    images: ghcr.io/myorg/myapp
    tags: |
      # Branch name (main, develop)
      type=ref,event=branch
      # PR number (pr-42)
      type=ref,event=pr
      # Semver from git tag (1.2.3, 1.2, 1)
      type=semver,pattern={{version}}
      type=semver,pattern={{major}}.{{minor}}
      type=semver,pattern={{major}}
      # Git SHA (sha-abc1234)
      type=sha
      # Latest (only on default branch)
      type=raw,value=latest,enable={{is_default_branch}}
```

---

## 28.10 Deployment Strategies from CI

### Deploy to Docker Swarm

```bash
# From CI pipeline:
# 1. SSH into the Swarm manager
$ ssh deploy@swarm-manager "docker service update \
    --image registry.com/myapp:${TAG} \
    --update-parallelism 2 \
    --update-delay 10s \
    --update-failure-action rollback \
    myapp"

# 2. Or use docker stack deploy with a compose file
$ ssh deploy@swarm-manager "
    export TAG=${TAG}
    docker stack deploy -c docker-compose.prod.yml myapp
"
```

### Deploy to Kubernetes

```bash
# Update deployment image
$ kubectl set image deployment/myapp \
    myapp=registry.com/myapp:${TAG} \
    -n production

# Or use kustomize
$ cd k8s/overlays/production
$ kustomize edit set image myapp=registry.com/myapp:${TAG}
$ kubectl apply -k .

# Or use Helm
$ helm upgrade myapp ./charts/myapp \
    --set image.tag=${TAG} \
    --namespace production
```

### Deploy to Docker Compose (Single Server)

```bash
# Pull new image and recreate containers
$ ssh deploy@server "
    cd /opt/myapp
    export TAG=${TAG}
    docker compose pull
    docker compose up -d --no-deps --build api
"
```

---

## 28.11 Mono-Repo and Multi-Service Pipelines

### Detecting Changed Services

```bash
# Only build services that changed (mono-repo optimization)
CHANGED_FILES=$(git diff --name-only HEAD~1)

if echo "$CHANGED_FILES" | grep -q "^services/api/"; then
    docker buildx build -t registry.com/api:${TAG} services/api/ --push
fi

if echo "$CHANGED_FILES" | grep -q "^services/frontend/"; then
    docker buildx build -t registry.com/frontend:${TAG} services/frontend/ --push
fi

if echo "$CHANGED_FILES" | grep -q "^services/worker/"; then
    docker buildx build -t registry.com/worker:${TAG} services/worker/ --push
fi
```

### Bake for Multi-Service Builds

```hcl
# docker-bake.hcl
variable "TAG" { default = "latest" }
variable "REGISTRY" { default = "registry.com" }

group "default" {
    targets = ["api", "frontend", "worker"]
}

target "api" {
    context    = "./services/api"
    tags       = ["${REGISTRY}/api:${TAG}"]
    cache-from = ["type=registry,ref=${REGISTRY}/api:cache"]
    cache-to   = ["type=registry,ref=${REGISTRY}/api:cache,mode=max"]
}

target "frontend" {
    context = "./services/frontend"
    tags    = ["${REGISTRY}/frontend:${TAG}"]
}

target "worker" {
    context = "./services/worker"
    tags    = ["${REGISTRY}/worker:${TAG}"]
}
```

```bash
$ TAG=v1.2.3 docker buildx bake --push
```

---

## 28.12 Common Errors and Troubleshooting

### Error 1: "denied: access forbidden" in CI

```bash
# Registry login failed or expired
# Fix: Ensure login step runs before push
$ echo "$TOKEN" | docker login ghcr.io -u user --password-stdin
# Check: token has write:packages permission
```

### Error 2: "no space left on device" in CI

```bash
# CI runner disk is full from cached images/layers
# Fix: Prune before or after builds
$ docker system prune -af --volumes
# Or use ephemeral runners that start clean
```

### Error 3: Build cache not working in CI

```bash
# Ephemeral runners lose local cache between runs
# Fix: Use registry-based or GHA cache
$ docker buildx build \
    --cache-from type=registry,ref=registry.com/myapp:cache \
    --cache-to type=registry,ref=registry.com/myapp:cache,mode=max \
    .
```

### Error 4: Multi-platform build fails in CI

```bash
# QEMU not installed on the runner
# Fix: Add QEMU setup step
$ docker run --privileged --rm tonistiigi/binfmt --install all
# Or use: docker/setup-qemu-action@v3 in GitHub Actions
```

---

## Module 28 Summary

- Docker is central to CI/CD: build → test → scan → push → deploy
- **Registry authentication** varies by provider (Docker Hub, ECR, GCR, GHCR, ACR)
- **GitHub Actions** uses docker/build-push-action with GHA cache for fast builds
- **GitLab CI** uses Docker-in-Docker service with registry cache
- **Jenkins** uses the Docker Pipeline plugin with docker.build() and docker.withRegistry()
- Design Dockerfiles with **named stages** so CI can target test, build, or production independently
- **Cache strategies**: registry cache (portable), GHA cache (fast), local cache (persistent runners)
- **Security scanning** (Trivy, Grype, Snyk) should run in CI and fail on critical vulnerabilities
- **Automated tagging** uses git context (branch, tag, SHA) for deterministic image versions
- Deploy from CI to **Swarm** (service update), **Kubernetes** (kubectl/helm), or **Compose** (docker compose up)
- **Mono-repo pipelines** detect changed services and build only what's needed
- **Bake** (`docker buildx bake`) orchestrates multi-service builds from a single config

---

**Previous Module: [Module 27 - Docker Logging, Monitoring, and Observability](module-27-logging-monitoring.md)**

**Next Module: [Module 29 - Production Deployment Patterns](module-29-production-patterns.md)**
