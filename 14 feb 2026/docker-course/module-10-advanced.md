# Module 10: Advanced Topics — Security, Optimization, CI/CD, Troubleshooting

---

## 10.1 Docker Security Best Practices

### Run as Non-Root User

```dockerfile
# BAD: Running as root (default)
FROM node:20-alpine
COPY . /app
CMD ["node", "app.js"]
# Container process runs as root — if compromised, attacker has root access

# GOOD: Non-root user
FROM node:20-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --chown=app:app . .
USER app
CMD ["node", "app.js"]
```

### Read-Only Filesystem

```bash
docker run -d \
  --read-only \
  --tmpfs /tmp:rw,size=50m \
  --tmpfs /var/run:rw \
  my-app:1.0

# --read-only: Container filesystem is read-only
# --tmpfs: Writable directories in RAM for temp files
# Prevents attackers from writing malicious files
```

### Drop Linux Capabilities

```bash
# Default: containers get many Linux capabilities
# Drop all, add back only what's needed
docker run -d \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  my-app:1.0

# Common capabilities:
# NET_BIND_SERVICE → Bind to ports below 1024
# CHOWN            → Change file ownership
# SETUID/SETGID    → Change user/group IDs
# SYS_PTRACE       → Debug processes (only for debugging containers)
```

### Scan Images for Vulnerabilities

```bash
# Docker Scout (built into Docker Desktop)
docker scout cves my-app:1.0

# Output:
# ✗ HIGH   CVE-2024-1234  openssl 3.0.12 → Fix: 3.0.13
# ✗ MEDIUM CVE-2024-5678  curl 8.4.0     → Fix: 8.5.0
# ✓ 0 critical, 1 high, 1 medium, 3 low

# Trivy (open-source scanner)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image my-app:1.0

# Snyk
docker scan my-app:1.0
```

### Never Store Secrets in Images

```dockerfile
# ❌ BAD: Secret baked into image
ENV DATABASE_PASSWORD=mysecret
COPY .env /app/.env

# ✅ GOOD: Pass secrets at runtime
# docker run -e DATABASE_PASSWORD=mysecret my-app
# Or use Docker secrets (Swarm) / external secret managers
```

### Use Distroless or Scratch Images

```dockerfile
# Distroless: No shell, no package manager, minimal attack surface
FROM gcr.io/distroless/nodejs20-debian12
COPY --from=builder /app /app
CMD ["app.js"]

# Scratch: Completely empty (for static binaries)
FROM scratch
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

### Protecting Against Malicious Images

Public registries like Docker Hub allow anyone to push images. This creates real risks:

```
┌─────────────────────────────────────────────────────────────┐
│              REAL-WORLD IMAGE ATTACK VECTORS                 │
│                                                              │
│  1. Typosquatting                                           │
│     Attacker publishes "ngnix" (typo of "nginx")            │
│     User accidentally pulls the malicious image             │
│                                                              │
│  2. Cryptominers                                            │
│     Image looks legitimate but runs a cryptocurrency        │
│     miner in the background, consuming your CPU             │
│                                                              │
│  3. Backdoors                                               │
│     Image includes a reverse shell or data exfiltration     │
│     tool that phones home to the attacker                   │
│                                                              │
│  4. Supply chain attacks                                    │
│     Compromised base image affects all downstream images    │
│     (e.g., a popular base image gets hijacked)              │
│                                                              │
│  5. Credential harvesting                                   │
│     Image captures environment variables (secrets, tokens)  │
│     and sends them to an external server                    │
└─────────────────────────────────────────────────────────────┘
```

**Enterprise image trust workflow:**

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE TRUST PIPELINE                            │
│                                                              │
│  Developer builds image                                     │
│       │                                                      │
│       ▼                                                      │
│  CI/CD pipeline runs:                                       │
│  1. Lint Dockerfile (hadolint)                              │
│  2. Build image                                             │
│  3. Scan for CVEs (Trivy/Grype)                             │
│  4. Check for secrets (gitleaks/trufflehog)                 │
│  5. Sign image (Cosign)                                     │
│       │                                                      │
│       ▼                                                      │
│  Push to PRIVATE registry (ECR/ACR/Harbor)                  │
│       │                                                      │
│       ▼                                                      │
│  Deployment policy enforces:                                │
│  • Only signed images allowed                               │
│  • No CRITICAL/HIGH CVEs                                    │
│  • Only from approved registries                            │
│  • Base image must be from approved list                    │
│       │                                                      │
│       ▼                                                      │
│  Container runs in production ✅                            │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Practical: Verify an image is from a trusted source

# Check if image is official
$ docker inspect nginx:latest --format='{{index .RepoDigests 0}}'
nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31

# Verify image signature with Cosign
$ cosign verify --key cosign.pub myregistry/myapp:1.0

Verification for myregistry/myapp:1.0 --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - The signatures were verified against the specified public key

# Block unsigned images in Kubernetes (admission controller)
# OPA Gatekeeper or Kyverno policies can enforce this
```

---

## 10.2 Image Optimization

### Reduce Image Size

```bash
# Check image size
docker images my-app
# REPOSITORY   TAG    SIZE
# my-app       v1     950MB   ← Too large!

# Strategy 1: Use smaller base images
FROM node:20          # 1.1GB
FROM node:20-slim     # 200MB
FROM node:20-alpine   # 130MB

# Strategy 2: Multi-stage builds (covered in Module 5)

# Strategy 3: Minimize layers
# BAD: 4 layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN rm -rf /var/lib/apt/lists/*

# GOOD: 1 layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl wget && \
    rm -rf /var/lib/apt/lists/*

# Strategy 4: Use --no-install-recommends
RUN apt-get install -y --no-install-recommends curl
# Skips suggested/recommended packages — saves 50-200MB

# Strategy 5: Clean up in the same layer
RUN pip install -r requirements.txt && \
    pip cache purge && \
    find /usr/local -name '*.pyc' -delete
```

### Analyze Image Layers with dive

```bash
# Install dive (image layer analyzer)
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive my-app:1.0

# Output: Interactive TUI showing:
# - Each layer and its size
# - Files added/modified/removed per layer
# - Wasted space (files added then deleted in later layers)
# - Image efficiency score
```

### Build Cache Optimization

```dockerfile
# Order instructions from least to most frequently changing:

FROM node:20-alpine          # Rarely changes
WORKDIR /app                 # Never changes

# Dependencies change occasionally
COPY package.json package-lock.json ./
RUN npm ci --production

# Source code changes frequently
COPY src/ ./src/

CMD ["node", "src/app.js"]

# Result: When only source code changes, layers 1-4 are cached.
# npm install is skipped — build takes seconds instead of minutes.
```

---

## 10.3 CI/CD with Docker

### GitHub Actions Pipeline

```yaml
# .github/workflows/docker.yml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests in Docker
        run: |
          docker compose -f docker-compose.yml -f docker-compose.test.yml up \
            --build --abort-on-container-exit --exit-code-from api
          
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=semver,pattern={{version}}
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          target: production
```

### GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE

test:
  stage: test
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $DOCKER_IMAGE:$CI_COMMIT_SHA -t $DOCKER_IMAGE:latest --target production ./backend
    - docker push $DOCKER_IMAGE:$CI_COMMIT_SHA
    - docker push $DOCKER_IMAGE:latest
  only:
    - main

deploy:
  stage: deploy
  script:
    - ssh deploy@server "docker pull $DOCKER_IMAGE:latest && docker compose up -d"
  only:
    - main
```

---

## 10.4 Docker Logging Best Practices

### Configure Log Rotation

```bash
# Per-container log rotation
docker run -d \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  my-app:1.0

# Global log rotation (all containers)
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  }
}
# sudo systemctl restart docker
```

### Centralized Logging with ELK Stack

```yaml
# docker-compose.logging.yml
services:
  app:
    image: my-app:1.0
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: app.{{.Name}}

  fluentd:
    image: fluent/fluentd:v1.16
    ports:
      - "24224:24224"
    volumes:
      - ./fluentd/conf:/fluentd/etc

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es-data:/usr/share/elasticsearch/data

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es-data:
```

---

## 10.5 Docker BuildKit Features

BuildKit is Docker's modern build engine with advanced features.

```bash
# Enable BuildKit (default in Docker 23+)
export DOCKER_BUILDKIT=1

# Or in daemon.json:
# { "features": { "buildkit": true } }
```

### Cache Mounts (Speed Up Builds)

```dockerfile
# Cache package manager downloads across builds
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./

# --mount=type=cache: Persists cache directory across builds
RUN --mount=type=cache,target=/root/.npm \
    npm ci --production

COPY . .
CMD ["node", "app.js"]
```

```dockerfile
# Python example
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

### Secret Mounts (Build-Time Secrets)

```dockerfile
# Access secrets during build without storing them in layers
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci --production

# Build with:
# docker build --secret id=npmrc,src=.npmrc -t my-app .
```

### SSH Mounts (Private Repos)

```dockerfile
# Clone private repos during build
RUN --mount=type=ssh \
    git clone git@github.com:company/private-lib.git

# Build with:
# docker build --ssh default -t my-app .
```

---

## 10.6 Docker Monitoring and Observability

### Prometheus + Grafana Stack

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana-data:/var/lib/grafana

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8081:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

volumes:
  grafana-data:
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

---

## 10.7 Docker in Production Checklist

```
┌──────────────────────────────────────────────────────────────┐
│                 PRODUCTION CHECKLIST                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ IMAGE BUILDING                                               │
│ ☐ Use specific base image tags (not :latest)                 │
│ ☐ Multi-stage build to minimize image size                   │
│ ☐ .dockerignore excludes unnecessary files                   │
│ ☐ No secrets in image (ENV, COPY .env, etc.)                 │
│ ☐ Scan for vulnerabilities before deploying                  │
│                                                              │
│ CONTAINER RUNTIME                                            │
│ ☐ Run as non-root user (USER instruction)                    │
│ ☐ Read-only filesystem where possible                        │
│ ☐ Drop all capabilities, add back only needed ones           │
│ ☐ Set memory and CPU limits                                  │
│ ☐ Configure restart policy (unless-stopped)                  │
│ ☐ Health checks defined                                      │
│ ☐ Log rotation configured (max-size, max-file)               │
│                                                              │
│ DATA                                                         │
│ ☐ Named volumes for persistent data                          │
│ ☐ Regular automated backups                                  │
│ ☐ Never use docker compose down -v in production             │
│                                                              │
│ NETWORKING                                                   │
│ ☐ User-defined networks (not default bridge)                 │
│ ☐ Network isolation (frontend/backend separation)            │
│ ☐ Bind to 127.0.0.1 for internal-only ports                  │
│                                                              │
│ CI/CD                                                        │
│ ☐ Automated builds on push                                   │
│ ☐ Tests run in containers                                    │
│ ☐ Images tagged with git SHA for traceability                │
│ ☐ Vulnerability scanning in pipeline                         │
│                                                              │
│ MONITORING                                                   │
│ ☐ Container metrics collected (CPU, memory, network)         │
│ ☐ Centralized logging                                        │
│ ☐ Alerting on container health/restarts                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 10.8 Master Troubleshooting Guide

### Container Won't Start

```bash
# Step 1: Check logs
docker logs <container>

# Step 2: Check exit code
docker inspect --format='{{.State.ExitCode}}' <container>
# 0   = Clean exit
# 1   = Application error
# 137 = OOMKilled (out of memory) or SIGKILL
# 139 = Segfault
# 143 = SIGTERM (graceful stop)

# Step 3: Check OOM
docker inspect --format='{{.State.OOMKilled}}' <container>
# true = Container ran out of memory

# Step 4: Run interactively to debug
docker run -it --entrypoint sh my-app:1.0
# Manually run commands to find the issue
```

### Container Runs But App Doesn't Work

```bash
# Check if process is running
docker top <container>

# Check if port is listening
docker exec <container> ss -tlnp

# Check environment variables
docker exec <container> env

# Check filesystem
docker exec <container> ls -la /app

# Check DNS resolution
docker exec <container> nslookup database

# Check connectivity
docker exec <container> wget -qO- http://other-service:3000/health
```

### Performance Issues

```bash
# Check resource usage
docker stats --no-stream

# Check for throttling
docker inspect --format='{{.HostConfig.NanoCpus}}' <container>

# Check disk I/O
docker exec <container> iostat -x 1 3

# Check network
docker exec <container> ss -s
```

### Image Build Failures

```bash
# Build with verbose output
docker build --progress=plain -t my-app .

# Build without cache (fresh build)
docker build --no-cache -t my-app .

# Check build context size
du -sh . --exclude=node_modules --exclude=.git

# Verify .dockerignore
cat .dockerignore
```

### Disk Space Issues

```bash
# Check Docker disk usage
docker system df -v

# Clean everything unused
docker system prune -a --volumes

# Find large images
docker images --format "{{.Size}}\t{{.Repository}}:{{.Tag}}" | sort -hr | head -10

# Find large volumes
docker system df -v 2>/dev/null | grep -A 100 "VOLUME NAME"
```

### Network Debugging

```bash
# Use netshoot for network debugging
docker run -it --network <network-name> nicolaka/netshoot

# Inside netshoot:
ping <service-name>
dig <service-name>
curl http://<service-name>:<port>/health
tcpdump -i eth0 port 5432
iperf -c <service-name>
```

---

## 10.9 Docker Command Quick Reference (Complete)

```bash
# ─── IMAGES ──────────────────────────────────────
docker build -t name:tag .          # Build image
docker build --no-cache -t name .   # Build without cache
docker images                       # List images
docker pull image:tag               # Download image
docker push image:tag               # Upload image
docker rmi image                    # Remove image
docker image prune -a               # Remove unused images
docker tag src:tag dst:tag          # Tag image
docker save -o file.tar image       # Export image to file
docker load -i file.tar             # Import image from file
docker history image                # Show image layers
docker inspect image                # Image details (JSON)

# ─── CONTAINERS ──────────────────────────────────
docker run -d -p 80:80 --name x img # Run container
docker ps                           # List running
docker ps -a                        # List all
docker start/stop/restart name      # Lifecycle
docker rm name                      # Remove
docker rm -f name                   # Force remove
docker exec -it name bash           # Shell access
docker logs -f name                 # Follow logs
docker cp src name:/dst             # Copy to container
docker cp name:/src dst             # Copy from container
docker stats                        # Resource usage
docker top name                     # Processes
docker inspect name                 # Details (JSON)
docker diff name                    # Filesystem changes
docker commit name new-image        # Save as image
docker update --memory=1g name      # Update limits

# ─── COMPOSE ─────────────────────────────────────
docker compose up -d                # Start all
docker compose up -d --build        # Rebuild and start
docker compose down                 # Stop and remove
docker compose down -v              # Stop, remove, delete volumes
docker compose ps                   # List services
docker compose logs -f service      # Follow service logs
docker compose exec service cmd     # Run in existing container
docker compose run --rm service cmd # Run in new container
docker compose build                # Build images
docker compose pull                 # Pull images
docker compose config               # Validate config

# ─── NETWORKS ────────────────────────────────────
docker network create name          # Create network
docker network ls                   # List networks
docker network inspect name         # Network details
docker network connect net ctr      # Connect container
docker network disconnect net ctr   # Disconnect container
docker network rm name              # Remove network
docker network prune                # Remove unused

# ─── VOLUMES ─────────────────────────────────────
docker volume create name           # Create volume
docker volume ls                    # List volumes
docker volume inspect name          # Volume details
docker volume rm name               # Remove volume
docker volume prune                 # Remove unused

# ─── SYSTEM ──────────────────────────────────────
docker system df                    # Disk usage
docker system prune -a              # Clean everything
docker info                         # System info
docker version                      # Version info
```

---

## 10.10 Dockerfile Linting with Hadolint

Hadolint is a Dockerfile linter that catches bad practices, security
issues, and inefficiencies before you build.

### Installing and Running Hadolint

```bash
# Method 1: Run via Docker (no installation needed)
$ docker run --rm -i hadolint/hadolint < Dockerfile

# Method 2: Install locally
# macOS
$ brew install hadolint

# Linux
$ wget -O /usr/local/bin/hadolint \
    https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
$ chmod +x /usr/local/bin/hadolint

# Run against a Dockerfile
$ hadolint Dockerfile
```

### Example Output

```bash
$ hadolint Dockerfile
# Dockerfile:3 DL3006 warning: Always tag the version explicitly
# Dockerfile:5 DL3008 warning: Pin versions in apt-get install
# Dockerfile:5 DL3009 info: Delete the apt-get lists after installing
# Dockerfile:8 DL3020 error: Use COPY instead of ADD for files & folders
# Dockerfile:12 DL4006 warning: Set the SHELL option -o pipefail before RUN with a pipe
# Dockerfile:15 DL3025 warning: Use arguments JSON notation for CMD and ENTRYPOINT
```

```
# Common Hadolint rules:
#
# DL3006 — Always tag the version explicitly (no FROM ubuntu)
# DL3007 — Using latest is prone to errors (use specific tag)
# DL3008 — Pin versions in apt-get install (apt-get install curl=7.88.1-10)
# DL3009 — Delete apt-get lists after installing
# DL3020 — Use COPY instead of ADD (ADD has extra features you rarely need)
# DL3025 — Use JSON notation for CMD ["node", "app.js"] not CMD node app.js
# DL4006 — Set SHELL ["/bin/bash", "-o", "pipefail", "-c"] before RUN with pipes
# SC2086 — Double quote variables to prevent globbing (from ShellCheck)
```

### Hadolint in CI/CD

```yaml
# GitHub Actions
- name: Lint Dockerfile
  uses: hadolint/hadolint-action@v3.1.0
  with:
    dockerfile: Dockerfile
    failure-threshold: warning
    # Fails the build if any warning or error is found
```

```yaml
# GitLab CI
lint:
  image: hadolint/hadolint:latest-debian
  script:
    - hadolint Dockerfile
  allow_failure: false
```

```groovy
// Jenkins
stage('Lint Dockerfile') {
    steps {
        sh 'docker run --rm -i hadolint/hadolint < Dockerfile'
    }
}
```

### Configuring Hadolint (.hadolint.yaml)

```yaml
# .hadolint.yaml — place in project root
ignored:
  - DL3008    # Don't require pinned apt versions (too strict for some teams)
  - DL3018    # Allow apk add without --no-cache in dev images

trustedRegistries:
  - docker.io
  - gcr.io
  - registry.example.com

override:
  warning:
    - DL3006  # Treat unpinned FROM as warning (not error)
```

---

## 10.11 Immutable Infrastructure with Docker

Immutable infrastructure means you never modify running containers.
Instead, you build a new image and replace the container entirely.

```
# MUTABLE approach (anti-pattern):
#   1. Container is running myapp:v1
#   2. SSH into the container
#   3. Edit config files, install patches
#   4. Container is now in an unknown state
#   5. If it crashes, you can't reproduce the exact state
#
# IMMUTABLE approach (best practice):
#   1. Container is running myapp:v1
#   2. Need a change? Update Dockerfile or config
#   3. Build new image myapp:v2
#   4. Deploy myapp:v2 (rolling update replaces v1)
#   5. Old container is destroyed, new one is identical everywhere
#
# Benefits:
#   - Reproducibility: every deployment is from a known image
#   - Auditability: git history shows every change
#   - Rollback: just redeploy the previous image version
#   - No configuration drift between environments
```

### Rules for Immutable Containers

```
# 1. Never docker exec to modify a running container
#    (except for debugging — never for permanent changes)
#
# 2. Never install packages inside a running container
#    (update the Dockerfile and rebuild)
#
# 3. Use read-only root filesystem
#    docker run --read-only --tmpfs /tmp myapp
#
# 4. Externalize all state
#    - Data → volumes
#    - Config → environment variables or mounted config files
#    - Secrets → Docker secrets or Vault
#
# 5. Use specific image tags (never :latest in production)
#    docker run myapp:v2.1.3   ← deterministic
#    docker run myapp:latest   ← could be anything
```

---

## 10.12 Docker Management Tools

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Tool             │ Description                                  │
├──────────────────┼──────────────────────────────────────────────┤
│ Portainer        │ Web-based Docker management UI. Manage       │
│                  │ containers, images, volumes, networks.       │
│                  │ Supports Swarm and Kubernetes.               │
│                  │ docker run -d -p 9443:9443                   │
│                  │   -v /var/run/docker.sock:/var/run/docker.sock│
│                  │   portainer/portainer-ce                     │
├──────────────────┼──────────────────────────────────────────────┤
│ Lens             │ Desktop IDE for Kubernetes and Docker.       │
│                  │ Visual cluster management, log viewing,      │
│                  │ resource monitoring. Free and open-source.   │
│                  │ Download from https://k8slens.dev            │
├──────────────────┼──────────────────────────────────────────────┤
│ Lazydocker       │ Terminal UI for Docker. View containers,     │
│                  │ logs, stats, and images in a TUI dashboard.  │
│                  │ go install github.com/jesseduffield/          │
│                  │   lazydocker@latest                          │
├──────────────────┼──────────────────────────────────────────────┤
│ ctop             │ Top-like interface for container metrics.    │
│                  │ Real-time CPU, memory, network, I/O.         │
│                  │ docker run --rm -it -v /var/run/docker.sock: │
│                  │   /var/run/docker.sock quay.io/vektorlab/ctop│
├──────────────────┼──────────────────────────────────────────────┤
│ Dive             │ Explore Docker image layers. Shows what      │
│                  │ each layer adds and identifies wasted space. │
│                  │ dive myapp:latest                            │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## Module 10 Summary

- Run containers as non-root with minimal capabilities and read-only filesystems
- Scan images for vulnerabilities before deploying (Scout, Trivy, Snyk)
- Optimize images: small base images, multi-stage builds, layer caching
- BuildKit features: cache mounts, secret mounts, SSH mounts
- CI/CD: automate build, test, scan, push, deploy in pipelines
- Configure log rotation to prevent disk exhaustion
- Monitor with Prometheus + Grafana + cAdvisor
- Follow the production checklist before every deployment
- Use systematic troubleshooting: logs → exit code → OOM → interactive debug
- **Hadolint** lints Dockerfiles for bad practices (DL3006, DL3008, DL3020, DL4006)
- **Immutable infrastructure**: never modify running containers — rebuild and redeploy
- Management tools: **Portainer** (web UI), **Lens** (K8s IDE), **Lazydocker** (TUI), **ctop** (metrics), **Dive** (layers)

---

## Course Complete

You've covered Docker from fundamentals to production deployment:

| Module | Topic |
|--------|-------|
| 1 | Fundamentals — What, Why, Architecture |
| 2 | Installation — Setup and First Container |
| 3 | Images — Building, Managing, Registries |
| 4 | Containers — Lifecycle and Management |
| 5 | Dockerfile — Every Instruction Explained |
| 6 | Compose — Multi-Container Applications |
| 7 | Networking — Isolation and Communication |
| 8 | Volumes — Data Persistence |
| 9 | Project — Full Stack Deployment |
| 10 | Advanced — Security, CI/CD, Troubleshooting |
| 11 | Container Orchestration and Docker Swarm |
| 12 | Docker Image Optimization |

**Next Module: [Module 11 - Container Orchestration and Docker Swarm](module-11-orchestration.md)**
