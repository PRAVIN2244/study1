# Module 05 — Runners

## Runner Types

### GitHub-Hosted Runners

Managed by GitHub. Fresh VM for every job.

| Runner | OS | vCPUs | RAM | Storage |
|--------|----|-------|-----|---------|
| `ubuntu-latest` | Ubuntu 22.04 | 4 | 16 GB | 14 GB SSD |
| `ubuntu-24.04` | Ubuntu 24.04 | 4 | 16 GB | 14 GB SSD |
| `windows-latest` | Windows Server 2022 | 4 | 16 GB | 14 GB SSD |
| `macos-latest` | macOS 14 (Sonoma) | 3 (M1) | 7 GB | 14 GB SSD |
| `macos-13` | macOS 13 (Ventura) | 4 (Intel) | 14 GB | 14 GB SSD |

**Larger runners** (Team/Enterprise plans):

| Runner | vCPUs | RAM | Storage |
|--------|-------|-----|---------|
| `ubuntu-latest-4-cores` | 4 | 16 GB | 150 GB |
| `ubuntu-latest-8-cores` | 8 | 32 GB | 300 GB |
| `ubuntu-latest-16-cores` | 16 | 64 GB | 600 GB |
| `ubuntu-latest-32-cores` | 32 | 128 GB | 2 TB |
| `ubuntu-latest-64-cores` | 64 | 256 GB | 2 TB |

Pre-installed software: Docker, Node.js, Python, Java, Go, .NET, and more.
Full list: https://github.com/actions/runner-images

### Self-Hosted Runners

You manage the infrastructure. Persistent between jobs.

**Advantages:**
- Custom hardware (GPU, ARM, specialized)
- Access to private networks
- No usage limits
- Persistent caches and tools
- Cost control for high-volume usage

**Disadvantages:**
- You manage updates, security, and maintenance
- Security risk if used with public repos (untrusted code runs on your machine)

## Setting Up Self-Hosted Runners

### Repository-Level Runner

**Settings → Actions → Runners → New self-hosted runner**

### Organization-Level Runner

**Organization → Settings → Actions → Runners → New self-hosted runner**

### Installation (Linux)

```bash
# Create a directory
mkdir actions-runner && cd actions-runner

# Download runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf actions-runner-linux-x64-2.311.0.tar.gz

# Configure
./config.sh \
  --url https://github.com/OWNER/REPO \
  --token <registration-token> \
  --name "linux-runner-01" \
  --labels "linux,docker,x64" \
  --work "_work" \
  --runnergroup "Default"

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

### Installation (Windows)

```powershell
# Create directory
mkdir C:\actions-runner; cd C:\actions-runner

# Download
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-win-x64-2.311.0.zip -OutFile actions-runner.zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD\actions-runner.zip", "$PWD")

# Configure
.\config.cmd --url https://github.com/OWNER/REPO --token <token>

# Install as service
.\svc.cmd install
.\svc.cmd start
```

### Installation (macOS)

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-osx-arm64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-osx-arm64-2.311.0.tar.gz
tar xzf actions-runner-osx-arm64-2.311.0.tar.gz

./config.sh --url https://github.com/OWNER/REPO --token <token>

# Install as launchd service
./svc.sh install
./svc.sh start
```

### Docker-Based Runner

```dockerfile
# Dockerfile
FROM ubuntu:22.04

ARG RUNNER_VERSION=2.311.0

RUN apt-get update && apt-get install -y \
    curl jq build-essential libssl-dev libffi-dev \
    python3 python3-venv python3-dev python3-pip \
    git docker.io && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m runner

WORKDIR /home/runner

RUN curl -o actions-runner.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf actions-runner.tar.gz && \
    rm actions-runner.tar.gz && \
    ./bin/installdependencies.sh && \
    chown -R runner:runner /home/runner

USER runner

ENTRYPOINT ["./config.sh"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  runner:
    build: .
    environment:
      - RUNNER_TOKEN=${RUNNER_TOKEN}
      - RUNNER_REPOSITORY_URL=https://github.com/OWNER/REPO
      - RUNNER_NAME=docker-runner
      - RUNNER_LABELS=docker,linux
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
```

## Kubernetes-Based Runners (ARC)

Actions Runner Controller (ARC) manages self-hosted runners on Kubernetes.

### Install ARC with Helm

```bash
# Add Helm repo
helm repo add actions-runner-controller \
  https://actions-runner-controller.github.io/actions-runner-controller

# Install cert-manager (required)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create GitHub App or PAT for authentication
# GitHub App (recommended): Organization → Settings → Developer settings → GitHub Apps

# Install ARC
helm install arc actions-runner-controller/actions-runner-controller \
  --namespace actions-runner-system \
  --create-namespace \
  --set authSecret.create=true \
  --set authSecret.github_token=<PAT>
  # Or for GitHub App:
  # --set authSecret.github_app_id=<app-id>
  # --set authSecret.github_app_installation_id=<installation-id>
  # --set authSecret.github_app_private_key=<base64-encoded-key>
```

### Runner Deployment

```yaml
# runner-deployment.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: org-runners
  namespace: actions-runner-system
spec:
  replicas: 3
  template:
    spec:
      repository: my-org                # Organization level
      # Or: repository: my-org/my-repo  # Repository level
      labels:
        - linux
        - k8s
      dockerEnabled: true
      resources:
        limits:
          cpu: "2"
          memory: "4Gi"
        requests:
          cpu: "500m"
          memory: "1Gi"
```

### Autoscaling Runners

```yaml
# horizontal-runner-autoscaler.yaml
apiVersion: actions.summerwind.dev/v1alpha1
kind: HorizontalRunnerAutoscaler
metadata:
  name: org-runners-autoscaler
  namespace: actions-runner-system
spec:
  scaleTargetRef:
    kind: RunnerDeployment
    name: org-runners
  minReplicas: 1
  maxReplicas: 20
  scaleDownDelaySecondsAfterScaleOut: 300
  metrics:
    - type: PercentageRunnersBusy
      scaleUpThreshold: '0.75'
      scaleDownThreshold: '0.25'
      scaleUpFactor: '2'
      scaleDownFactor: '0.5'
```

### ARC v2 (GitHub-Managed Controller)

```bash
# Install ARC v2 (newer, GitHub-supported)
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Install runner scale set
helm install arc-runner-set \
  --namespace arc-runners \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set \
  --set githubConfigUrl="https://github.com/my-org" \
  --set githubConfigSecret.github_token="<PAT>" \
  --set minRunners=1 \
  --set maxRunners=10
```

## Using Self-Hosted Runners in Workflows

```yaml
jobs:
  build:
    # Use self-hosted runner with specific labels
    runs-on: [self-hosted, linux, x64]
    steps:
      - uses: actions/checkout@v4
      - run: make build

  gpu-training:
    # Use GPU runner
    runs-on: [self-hosted, gpu, cuda]
    steps:
      - uses: actions/checkout@v4
      - run: python train.py

  deploy:
    # Use runner in specific network
    runs-on: [self-hosted, production-network]
    steps:
      - run: kubectl apply -f deploy.yaml
```

## Runner Groups

Organize runners and control access (Enterprise/Organization):

**Organization → Settings → Actions → Runner groups**

```
Runner Groups:
├── Default
│   ├── runner-01 (linux, docker)
│   └── runner-02 (linux, docker)
├── Production
│   ├── prod-runner-01 (linux, production)
│   └── prod-runner-02 (linux, production)
│   └── Access: deploy-team only
└── GPU
    ├── gpu-runner-01 (linux, gpu, cuda)
    └── Access: ml-team only
```

```yaml
# Use runner from specific group
jobs:
  deploy:
    runs-on:
      group: Production
      labels: [linux]
    steps:
      - run: ./deploy.sh
```

## Runner Security

### Hardening Self-Hosted Runners

1. **Never use self-hosted runners with public repos** — anyone can submit a PR that runs code on your machine
2. **Use ephemeral runners** — `--ephemeral` flag, runner exits after one job
3. **Run as non-root user**
4. **Use runner groups** to restrict access
5. **Network isolation** — place runners in dedicated VLANs
6. **Regular updates** — keep runner software and OS updated
7. **Monitor runner activity** — audit logs

```bash
# Ephemeral runner (exits after one job)
./config.sh \
  --url https://github.com/OWNER/REPO \
  --token <token> \
  --ephemeral

# Just-in-time (JIT) runners
# Created via API, run one job, auto-deregister
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/actions/runners/generate-jitconfig \
  -d '{"name":"jit-runner","runner_group_id":1,"labels":["linux"]}'
```

## Runner Management

```bash
# List runners (CLI)
gh api /repos/OWNER/REPO/actions/runners | jq '.runners[] | {name, status, labels}'

# Remove offline runners
gh api /repos/OWNER/REPO/actions/runners | \
  jq -r '.runners[] | select(.status == "offline") | .id' | \
  xargs -I {} gh api -X DELETE /repos/OWNER/REPO/actions/runners/{}

# Runner diagnostics
# Check logs in: _diag/ directory on the runner
cat _diag/Runner_*.log | tail -50
cat _diag/Worker_*.log | tail -50
```

## Cost Optimization

| Strategy | Description |
|----------|-------------|
| **Spot/Preemptible instances** | Use cloud spot instances for runners (70-90% savings) |
| **Autoscaling** | Scale to zero when idle |
| **Caching** | Reduce build time with dependency caching |
| **Larger runners** | Fewer minutes used with faster builds |
| **Self-hosted for high volume** | Fixed cost vs per-minute billing |
| **Concurrency limits** | Prevent runaway costs |
