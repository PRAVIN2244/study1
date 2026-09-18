# Module 06 — Runners

## What is a GitLab Runner?

A GitLab Runner is an agent that picks up and executes CI/CD jobs. Runners are separate from the GitLab server and can run on any machine.

```
GitLab Server ◀──── polls for jobs ──── Runner
     │                                     │
     │         sends job payload           │
     ├────────────────────────────────────▶│
     │                                     │
     │         reports results             │
     │◀────────────────────────────────────┤
```

## Runner Types

| Type | Scope | Use Case |
|------|-------|----------|
| **Shared** | All projects in instance | General-purpose builds |
| **Group** | All projects in a group | Team-specific builds |
| **Project** | Single project only | Project-specific needs |

## Runner Executors

The executor determines how a job is run:

| Executor | Description | Isolation | Speed |
|----------|-------------|-----------|-------|
| **Shell** | Runs directly on host | None | Fast |
| **Docker** | Runs in Docker container | Container | Fast |
| **Docker Machine** | Auto-provisions Docker hosts | VM + Container | Medium |
| **Kubernetes** | Runs in K8s pod | Pod | Medium |
| **VirtualBox** | Runs in VirtualBox VM | Full VM | Slow |
| **Parallels** | Runs in Parallels VM | Full VM | Slow |
| **SSH** | Runs on remote machine via SSH | None | Fast |
| **Docker Autoscaler** | Cloud-native autoscaling | VM + Container | Medium |

## Installing GitLab Runner

### Linux (Package)

```bash
# Add repository
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash

# Install
sudo apt install -y gitlab-runner

# Verify
gitlab-runner --version
```

### macOS

```bash
brew install gitlab-runner
brew services start gitlab-runner
```

### Docker

```bash
docker run -d \
  --name gitlab-runner \
  --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:latest
```

### Kubernetes (Helm)

```bash
helm repo add gitlab https://charts.gitlab.io
helm install gitlab-runner gitlab/gitlab-runner \
  --namespace gitlab-runner \
  --create-namespace \
  --set gitlabUrl=https://gitlab.example.com \
  --set runnerToken=<runner-token>
```

## Registering a Runner

### Step 1: Get Registration Token

- **Instance runners**: Admin Area → CI/CD → Runners
- **Group runners**: Group → Settings → CI/CD → Runners
- **Project runners**: Project → Settings → CI/CD → Runners

### Step 2: Register (New method — Runner Authentication Token)

GitLab 16.0+ uses runner authentication tokens instead of registration tokens.

1. Create runner in GitLab UI (Admin/Group/Project → CI/CD → Runners → New)
2. Copy the authentication token
3. Register:

```bash
gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.example.com" \
  --token "<runner-authentication-token>" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "docker-runner-01" \
  --tag-list "docker,linux"
```

### Step 3: Register (Legacy method — Registration Token)

```bash
# Interactive registration
sudo gitlab-runner register

# Non-interactive
sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.example.com/" \
  --registration-token "<registration-token>" \
  --executor "docker" \
  --docker-image "alpine:latest" \
  --description "docker-runner-01" \
  --tag-list "docker,linux" \
  --run-untagged="true" \
  --locked="false"
```

## Runner Configuration

### config.toml

```toml
# /etc/gitlab-runner/config.toml

concurrent = 10                    # Max concurrent jobs across all runners
check_interval = 3                 # Seconds between job polls
log_level = "info"
log_format = "text"

[session_server]
  listen_address = "[::]:8093"
  advertise_address = "runner.example.com:8093"
  session_timeout = 1800

[[runners]]
  name = "docker-runner-01"
  url = "https://gitlab.example.com/"
  token = "runner-token-here"
  executor = "docker"
  limit = 5                        # Max concurrent jobs for this runner
  output_limit = 4096              # Max job log size in KB

  [runners.docker]
    image = "alpine:latest"        # Default image
    privileged = false             # Docker-in-Docker needs true
    disable_entrypoint_overwrite = false
    oom_kill_disable = false
    disable_cache = false
    volumes = [
      "/cache",                    # Cache volume
      "/var/run/docker.sock:/var/run/docker.sock"  # Docker socket
    ]
    shm_size = 0
    pull_policy = ["if-not-present"]  # always, never, if-not-present
    allowed_images = ["ruby:*", "python:*", "node:*"]  # Restrict images
    allowed_services = ["postgres:*", "redis:*"]

  [runners.cache]
    Type = "s3"
    Shared = true
    [runners.cache.s3]
      ServerAddress = "s3.amazonaws.com"
      AccessKey = "ACCESS_KEY"
      SecretKey = "SECRET_KEY"
      BucketName = "runner-cache"
      BucketLocation = "us-east-1"
```

## Executor Deep Dive

### Shell Executor

Runs jobs directly on the host machine.

```toml
[[runners]]
  name = "shell-runner"
  executor = "shell"
  shell = "bash"                   # bash, sh, powershell, pwsh
```

```yaml
# .gitlab-ci.yml
build:
  tags:
    - shell
  script:
    - echo "Running on the host machine"
    - whoami
    - pwd
```

⚠️ **Security risk**: Jobs have access to the host filesystem. Use only for trusted projects.

### Docker Executor

Runs each job in a fresh Docker container.

```toml
[[runners]]
  name = "docker-runner"
  executor = "docker"

  [runners.docker]
    image = "alpine:latest"
    privileged = false
    volumes = ["/cache", "/builds:/builds"]
    pull_policy = ["if-not-present"]
    # Resource limits
    cpus = "2"
    memory = "4g"
    memory_swap = "4g"
```

```yaml
# .gitlab-ci.yml — Docker-in-Docker
build-image:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  tags:
    - docker
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

### Kubernetes Executor

Runs each job as a Kubernetes pod.

```toml
[[runners]]
  name = "k8s-runner"
  executor = "kubernetes"

  [runners.kubernetes]
    namespace = "gitlab-runner"
    image = "alpine:latest"
    privileged = false
    cpu_limit = "2"
    memory_limit = "4Gi"
    cpu_request = "500m"
    memory_request = "1Gi"
    service_cpu_limit = "1"
    service_memory_limit = "2Gi"
    poll_interval = 5
    poll_timeout = 3600

    [[runners.kubernetes.volumes.pvc]]
      name = "cache-pvc"
      mount_path = "/cache"

    [runners.kubernetes.pod_labels]
      "app" = "gitlab-runner"

    [runners.kubernetes.pod_annotations]
      "iam.amazonaws.com/role" = "runner-role"

    [runners.kubernetes.node_selector]
      "node-type" = "ci"

    [runners.kubernetes.pod_security_context]
      run_as_non_root = true
      run_as_user = 1000
```

```yaml
# .gitlab-ci.yml — Custom pod spec
build:
  tags:
    - k8s
  image: maven:3.9-eclipse-temurin-17
  variables:
    KUBERNETES_CPU_REQUEST: "1"
    KUBERNETES_MEMORY_REQUEST: "2Gi"
    KUBERNETES_CPU_LIMIT: "2"
    KUBERNETES_MEMORY_LIMIT: "4Gi"
  script:
    - mvn package
```

## Autoscaling Runners

### Docker Machine Autoscaler (Legacy)

```toml
[[runners]]
  name = "autoscale-runner"
  executor = "docker+machine"
  limit = 20

  [runners.machine]
    IdleCount = 2                  # Keep 2 idle machines
    IdleTime = 600                 # Remove idle after 10 min
    MaxBuilds = 100                # Recreate after 100 builds
    MachineDriver = "amazonec2"
    MachineName = "runner-%s"
    MachineOptions = [
      "amazonec2-instance-type=m5.large",
      "amazonec2-region=us-east-1",
      "amazonec2-vpc-id=vpc-xxxxx",
      "amazonec2-subnet-id=subnet-xxxxx",
      "amazonec2-security-group=runner-sg",
      "amazonec2-use-private-address=true"
    ]

    [[runners.machine.autoscaling]]
      Periods = ["* * 9-17 * * mon-fri *"]  # Business hours
      IdleCount = 5
      IdleTime = 600
      Timezone = "UTC"

    [[runners.machine.autoscaling]]
      Periods = ["* * * * * sat,sun *"]      # Weekends
      IdleCount = 0
      IdleTime = 60
```

### Docker Autoscaler (New — Recommended)

```toml
[[runners]]
  name = "autoscaler-runner"
  executor = "docker-autoscaler"

  [runners.autoscaler]
    plugin = "fleeting-plugin-aws"
    capacity_per_instance = 1
    max_use_count = 10
    max_instances = 20

    [runners.autoscaler.plugin_config]
      name = "runner-fleet"
      region = "us-east-1"

    [runners.autoscaler.connector_config]
      username = "ec2-user"
      use_external_addr = false

    [[runners.autoscaler.policy]]
      idle_count = 2
      idle_time = "10m"
      periods = ["* * 9-17 * * mon-fri *"]

    [[runners.autoscaler.policy]]
      idle_count = 0
      idle_time = "1m"
      periods = ["* * * * * sat,sun *"]

  [runners.docker]
    image = "alpine:latest"
```

## Runner Management

### Commands

```bash
# List registered runners
sudo gitlab-runner list

# Verify runner connectivity
sudo gitlab-runner verify

# Start/stop runner service
sudo gitlab-runner start
sudo gitlab-runner stop
sudo gitlab-runner restart

# Run a single job (debugging)
sudo gitlab-runner run-single \
  --url https://gitlab.example.com \
  --token <token> \
  --executor docker \
  --docker-image alpine:latest

# Unregister a runner
sudo gitlab-runner unregister --name "runner-name"
sudo gitlab-runner unregister --all-runners

# View runner logs
sudo journalctl -u gitlab-runner -f
```

### Tags and Job Assignment

```yaml
# .gitlab-ci.yml
build:
  tags:
    - docker
    - linux
  script: make build

deploy-aws:
  tags:
    - aws
    - production
  script: ./deploy.sh

# Runner with matching tags picks up the job
```

### Runner Security

```toml
# Restrict what runners can do
[[runners]]
  [runners.docker]
    # Restrict allowed images
    allowed_images = ["company/*", "node:*", "python:*"]
    allowed_services = ["postgres:*", "redis:*", "mysql:*"]

    # Disable privileged mode
    privileged = false

    # Disable Docker socket mounting
    volumes = ["/cache"]  # Don't include docker.sock

    # Run as non-root
    [runners.docker.sysctls]
      "net.ipv4.ip_forward" = "1"
```

## Monitoring Runners

### Prometheus Metrics

```toml
# config.toml
listen_address = ":9252"           # Expose metrics
```

Key metrics:
- `gitlab_runner_jobs` — running jobs count
- `gitlab_runner_request_concurrency` — concurrent API requests
- `gitlab_runner_errors_total` — error count
- `gitlab_runner_version_info` — runner version

### Health Check

```bash
# Check runner health
curl -s http://runner:9252/metrics | grep gitlab_runner_jobs

# Check from GitLab
# Admin Area → CI/CD → Runners → runner details
# Shows: status, version, IP, last contact, jobs run
```
