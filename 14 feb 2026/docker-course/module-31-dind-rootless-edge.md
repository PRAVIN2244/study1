# Module 31: Docker-in-Docker, Rootless Docker, and Edge Cases

Advanced Docker usage patterns: running Docker inside Docker for CI,
rootless mode for security, Podman as an alternative, and WebAssembly
containers.

### Topics Covered

```
31.1  Docker-in-Docker (DinD) — What and Why
31.2  DinD Methods: Privileged vs Socket Bind vs Sidecar
31.3  DinD in CI/CD Pipelines
31.4  Rootless Docker — Running Without Root
31.5  Rootless Docker Setup and Configuration
31.6  Podman — Daemonless Container Engine
31.7  Docker vs Podman — Comparison
31.8  WebAssembly (Wasm) Containers
31.9  Docker Desktop Alternatives
31.10 Docker Contexts — Managing Multiple Hosts
31.11 Docker Plugins and Extensions
31.12 Common Errors and Troubleshooting
```

---

## 31.1 Docker-in-Docker (DinD) — What and Why

```
# Docker-in-Docker means running a Docker daemon inside a container.
#
# Use cases:
#   - CI/CD: Build Docker images inside CI containers
#   - Testing: Test Docker-related tools in isolation
#   - Development: Provide isolated Docker environments
#
# The challenge:
#   Docker daemon needs access to Linux kernel features
#   (namespaces, cgroups, storage drivers) that are normally
#   restricted inside containers.
```

---

## 31.2 DinD Methods: Privileged vs Socket Bind vs Sidecar

### Method 1: Docker Socket Bind Mount (Most Common)

```bash
# Share the host's Docker daemon with the container
$ docker run -it --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    docker:24 sh

# Inside the container:
$ docker ps    # Shows the HOST's containers
$ docker build -t myapp .  # Builds on the HOST's daemon
```

```
# Pros:
#   - Simple setup
#   - Fast (no nested daemon)
#   - Shares image cache with host
#
# Cons:
#   - Container has FULL control over host's Docker
#   - Security risk: can access/delete any container on the host
#   - Not truly isolated
#
# ┌─────────────────────────────────────────────────────┐
# │  Host                                               │
# │  ┌──────────────────────────────────────────────┐   │
# │  │  dockerd (host daemon)                       │   │
# │  │    ├── container A                           │   │
# │  │    ├── container B                           │   │
# │  │    └── CI container (with socket mount)      │   │
# │  │         └── docker CLI → talks to host daemon│   │
# │  └──────────────────────────────────────────────┘   │
# └─────────────────────────────────────────────────────┘
```

### Method 2: Privileged DinD (True Nested Docker)

```bash
# Run a full Docker daemon inside a container
$ docker run --privileged -d --name dind docker:24-dind

# Connect to the inner daemon
$ docker exec -it dind docker ps
# Shows containers running INSIDE the DinD container (empty)

$ docker exec -it dind docker run hello-world
# Runs hello-world inside the nested Docker
```

```
# Pros:
#   - True isolation (separate daemon, separate images)
#   - No access to host's containers
#
# Cons:
#   - --privileged gives the container almost root-level host access
#   - Slower (nested storage drivers)
#   - No shared image cache
#   - Storage driver compatibility issues
#
# ┌─────────────────────────────────────────────────────┐
# │  Host                                               │
# │  ┌──────────────────────────────────────────────┐   │
# │  │  dockerd (host daemon)                       │   │
# │  │    └── DinD container (--privileged)         │   │
# │  │         ┌────────────────────────────────┐   │   │
# │  │         │  dockerd (nested daemon)       │   │   │
# │  │         │    └── inner containers        │   │   │
# │  │         └────────────────────────────────┘   │   │
# │  └──────────────────────────────────────────────┘   │
# └─────────────────────────────────────────────────────┘
```

### Method 3: DinD Sidecar (CI Pattern)

```yaml
# GitLab CI uses this pattern
services:
  - docker:24-dind

variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_CERTDIR: "/certs"

build:
  image: docker:24
  script:
    - docker build -t myapp .
    # docker CLI in the job container talks to the DinD sidecar
```

```
# The CI job container and DinD container run side by side.
# They communicate over TCP (port 2376 with TLS).
#
# ┌─────────────────────────────────────────────────────┐
# │  CI Runner                                          │
# │  ┌──────────────┐    ┌──────────────────────────┐   │
# │  │  Job container│    │  DinD sidecar            │   │
# │  │  (docker CLI) │───▶│  (dockerd on port 2376) │   │
# │  │               │TCP │                          │   │
# │  └──────────────┘    └──────────────────────────┘   │
# └─────────────────────────────────────────────────────┘
```

### Which Method to Use?

```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│                  │ Socket Bind  │ Privileged   │ Sidecar      │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Isolation        │ None         │ Full         │ Full         │
│ Security         │ Low          │ Low          │ Medium       │
│ Performance      │ Fast         │ Slower       │ Medium       │
│ Image cache      │ Shared       │ Separate     │ Separate     │
│ Setup complexity │ Simple       │ Simple       │ Medium       │
│ Best for         │ Dev/local CI │ Testing      │ CI/CD        │
└──────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 31.3 DinD in CI/CD Pipelines

### GitHub Actions (No DinD Needed)

```yaml
# GitHub Actions runners have Docker pre-installed
# No DinD setup required
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp .
      - run: docker run --rm myapp npm test
```

### GitLab CI with DinD

```yaml
# .gitlab-ci.yml
build:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_CERT_PATH: "/certs/client"
    DOCKER_TLS_VERIFY: "1"
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Jenkins with Docker Socket

```groovy
pipeline {
    agent {
        docker {
            image 'docker:24'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp .'
            }
        }
    }
}
```

### Kaniko — Build Without Docker Daemon

```yaml
# Kaniko builds images without a Docker daemon
# No privileged mode, no DinD needed
# Ideal for Kubernetes-based CI

# GitLab CI with Kaniko
build:
  image:
    name: gcr.io/kaniko-project/executor:v1.19.2-debug
    entrypoint: [""]
  script:
    - /kaniko/executor
        --context $CI_PROJECT_DIR
        --dockerfile $CI_PROJECT_DIR/Dockerfile
        --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

---

## 31.4 Rootless Docker — Running Without Root

```
# Standard Docker requires root privileges:
#   - dockerd runs as root
#   - Containers run as root by default
#   - Docker socket (/var/run/docker.sock) is owned by root
#
# Rootless Docker runs the entire Docker stack as a regular user:
#   - dockerd runs as your user
#   - No root privileges needed
#   - Uses user namespaces for isolation
#   - Containers map root (UID 0) to your user's UID
#
# Why rootless matters:
#   - Defense in depth: even if container escapes, attacker is unprivileged
#   - Required by some security policies (CIS benchmarks)
#   - Multi-tenant environments where users can't have root
```

---

## 31.5 Rootless Docker Setup and Configuration

### Installation

```bash
# Prerequisites
$ sudo apt-get install -y uidmap dbus-user-session

# Check subordinate UID/GID ranges
$ grep $USER /etc/subuid
# myuser:100000:65536
$ grep $USER /etc/subgid
# myuser:100000:65536

# Install rootless Docker
$ dockerd-rootless-setuptool.sh install

# Or install from scratch
$ curl -fsSL https://get.docker.com/rootless | sh

# Set environment variables (add to ~/.bashrc)
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

### Rootless Docker Limitations

```
┌──────────────────────────────────────────────────────────────────┐
│  ROOTLESS DOCKER LIMITATIONS                                    │
│                                                                  │
│  ✗ Cannot bind to ports < 1024 (use --publish 8080:80)          │
│  ✗ Cannot use --net=host                                        │
│  ✗ Cannot use overlay network (Swarm mode limited)              │
│  ✗ Some storage drivers not supported (devicemapper)            │
│  ✗ AppArmor not supported                                      │
│  ✗ Cgroup resource limits may not work (depends on cgroups v2)  │
│  ✗ Cannot mount host paths owned by other users                 │
│                                                                  │
│  ✓ Bridge networking works                                      │
│  ✓ Port mapping works (ports >= 1024)                           │
│  ✓ Volumes work                                                 │
│  ✓ BuildKit works                                               │
│  ✓ Docker Compose works                                         │
│  ✓ overlay2 storage driver works                                │
└──────────────────────────────────────────────────────────────────┘
```

### Verifying Rootless Mode

```bash
# Check if running rootless
$ docker info --format '{{.SecurityOptions}}'
# [name=rootless]

$ docker info | grep "Root Dir"
# Docker Root Dir: /home/myuser/.local/share/docker

# Container processes run as your user on the host
$ docker run -d --name test alpine sleep 3600
$ ps aux | grep "sleep 3600"
# myuser  12345  sleep 3600   ← NOT root!
```

---

## 31.6 Podman — Daemonless Container Engine

```
# Podman is a Docker-compatible container engine that:
#   - Runs without a daemon (no dockerd equivalent)
#   - Runs rootless by default
#   - Uses the same CLI commands as Docker
#   - Supports pods (groups of containers, like Kubernetes)
#   - Uses OCI-compliant images (same as Docker)
```

### Podman Commands (Docker-Compatible)

```bash
# Most Docker commands work identically with Podman
$ podman pull nginx
$ podman run -d --name web -p 8080:80 nginx
$ podman ps
$ podman logs web
$ podman exec -it web /bin/sh
$ podman stop web
$ podman rm web
$ podman build -t myapp .
$ podman push myapp registry.com/myapp:latest

# Docker Compose equivalent
$ podman-compose up -d
# Or use podman with Docker Compose directly
$ podman compose up -d

# Alias Docker to Podman
$ alias docker=podman
```

### Podman Pods

```bash
# Pods group containers that share namespaces (like Kubernetes pods)
$ podman pod create --name mypod -p 8080:80

# Add containers to the pod
$ podman run -d --pod mypod --name web nginx
$ podman run -d --pod mypod --name app myapp

# Both containers share:
#   - Network namespace (same IP, same ports)
#   - IPC namespace
#   - UTS namespace (same hostname)

# List pods
$ podman pod list

# Generate Kubernetes YAML from a pod
$ podman generate kube mypod > pod.yaml

# Run a Kubernetes YAML with Podman
$ podman play kube pod.yaml
```

---

## 31.7 Docker vs Podman — Comparison

```
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Feature              │ Docker               │ Podman               │
├──────────────────────┼──────────────────────┼──────────────────────┤
│ Daemon               │ Yes (dockerd)        │ No (daemonless)      │
│ Root required        │ Yes (default)        │ No (rootless default)│
│ CLI compatibility    │ Native               │ Docker-compatible    │
│ Compose              │ docker compose       │ podman-compose       │
│ Swarm                │ Yes                  │ No                   │
│ Kubernetes pods      │ No                   │ Yes (podman pod)     │
│ Systemd integration  │ Via unit files       │ podman generate      │
│                      │                      │ systemd              │
│ Image format         │ OCI / Docker         │ OCI / Docker         │
│ Build tool           │ BuildKit             │ Buildah              │
│ Default on           │ Most distros         │ RHEL 8+, Fedora      │
│ Socket API           │ /var/run/docker.sock │ /run/user/UID/       │
│                      │                      │ podman/podman.sock   │
│ Auto-restart         │ restart policies     │ systemd units        │
└──────────────────────┴──────────────────────┴──────────────────────┘
```

### Podman Systemd Integration

```bash
# Generate a systemd unit file from a running container
$ podman generate systemd --new --name myapp > ~/.config/systemd/user/myapp.service

# Enable and start
$ systemctl --user enable myapp.service
$ systemctl --user start myapp.service

# The container starts on boot and restarts on failure
# No daemon needed — systemd manages the container lifecycle
```

---

## 31.8 WebAssembly (Wasm) Containers

```
# WebAssembly containers run Wasm binaries instead of Linux processes.
# They use a Wasm runtime (WasmEdge, Wasmtime, Spin) instead of runc.
#
# Advantages over traditional containers:
#   - Startup time: ~1ms (vs ~100ms for containers)
#   - Image size: ~1MB (vs ~50-500MB for containers)
#   - Security: sandboxed by design (no kernel access)
#   - Portability: runs on any OS/arch without QEMU
#
# Limitations:
#   - No filesystem access (by default)
#   - No raw network sockets
#   - Limited language support (Rust, Go, C/C++, Python via WASI)
#   - No GPU access
#   - Ecosystem is still maturing
```

### Running Wasm Containers with Docker

```bash
# Docker Desktop 4.15+ supports Wasm containers
# Enable in Docker Desktop → Settings → Features in development
# → Use containerd for pulling and storing images
# → Enable Wasm

# Run a Wasm container
$ docker run --rm \
    --runtime=io.containerd.wasmedge.v1 \
    --platform=wasi/wasm \
    secondstate/rust-example-hello:latest

# Build a Wasm container image
$ cat Dockerfile.wasm
FROM scratch
COPY myapp.wasm /myapp.wasm
ENTRYPOINT ["/myapp.wasm"]

$ docker buildx build \
    --platform wasi/wasm \
    -t myapp:wasm \
    -f Dockerfile.wasm .
```

### Wasm Runtimes in Docker

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Runtime      │ Description                                      │
├──────────────┼──────────────────────────────────────────────────┤
│ WasmEdge     │ High-performance, CNCF project. Supports WASI.  │
│              │ Best for server-side Wasm workloads.             │
├──────────────┼──────────────────────────────────────────────────┤
│ Wasmtime     │ Bytecode Alliance reference runtime.            │
│              │ Focus on security and standards compliance.      │
├──────────────┼──────────────────────────────────────────────────┤
│ Spin         │ Fermyon's framework for Wasm microservices.      │
│              │ Built-in HTTP trigger, key-value store.          │
├──────────────┼──────────────────────────────────────────────────┤
│ Slight       │ Deislabs' lightweight Wasm runtime.              │
│              │ Minimal footprint.                               │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 31.9 Docker Desktop Alternatives

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Tool             │ Description                                  │
├──────────────────┼──────────────────────────────────────────────┤
│ Docker Desktop   │ Official GUI + VM. Free for personal use,   │
│                  │ paid for enterprise (>250 employees).        │
├──────────────────┼──────────────────────────────────────────────┤
│ Rancher Desktop  │ Free, open source. Uses containerd or       │
│                  │ dockerd. Includes Kubernetes (k3s).          │
├──────────────────┼──────────────────────────────────────────────┤
│ Colima           │ macOS/Linux. Lightweight VM with Docker.     │
│                  │ CLI-only. Uses Lima VMs.                     │
│                  │ $ colima start --cpu 4 --memory 8            │
├──────────────────┼──────────────────────────────────────────────┤
│ Podman Desktop   │ Free, open source. Podman with GUI.          │
│                  │ Rootless by default. Kubernetes support.     │
├──────────────────┼──────────────────────────────────────────────┤
│ OrbStack         │ macOS only. Fast, lightweight Docker/Linux.  │
│                  │ Drop-in Docker Desktop replacement.          │
├──────────────────┼──────────────────────────────────────────────┤
│ Lima             │ macOS/Linux. Lightweight Linux VMs.          │
│                  │ Automatic file sharing and port forwarding.  │
└──────────────────┴──────────────────────────────────────────────┘
```

```bash
# Colima setup (macOS)
$ brew install colima docker
$ colima start --cpu 4 --memory 8 --disk 60
$ docker ps   # Works — Colima provides the Docker socket

# Rancher Desktop (macOS/Windows/Linux)
# Download from https://rancherdesktop.io
# Choose container runtime: dockerd (moby) or containerd
```

---

## 31.10 Docker Contexts — Managing Multiple Hosts

```bash
# Docker contexts let you switch between Docker daemons
# (local, remote servers, cloud instances)

# List contexts
$ docker context ls
# NAME        DESCRIPTION                DOCKER ENDPOINT
# default *   Current DOCKER_HOST        unix:///var/run/docker.sock
# staging     Staging server             ssh://deploy@staging.example.com
# production  Production server          ssh://deploy@prod.example.com

# Create a context for a remote host
$ docker context create staging \
    --docker "host=ssh://deploy@staging.example.com"

$ docker context create production \
    --docker "host=ssh://deploy@prod.example.com"

# Switch context
$ docker context use staging
$ docker ps   # Shows containers on the staging server

# Run a command in a specific context without switching
$ docker --context production ps

# Remove a context
$ docker context rm staging

# Export/import contexts
$ docker context export staging > staging.dockercontext
$ docker context import staging staging.dockercontext
```

### Real-World: Multi-Environment Management

```bash
# Deploy to staging
$ docker context use staging
$ docker stack deploy -c docker-compose.yml myapp

# Check production
$ docker --context production service ls

# View logs from production
$ docker --context production service logs myapp_api --tail 50
```

---

## 31.11 Docker Plugins and Extensions

### Volume Plugins

```bash
# Install a volume plugin (e.g., REX-Ray for cloud storage)
$ docker plugin install rexray/ebs

# Create a volume using the plugin
$ docker volume create --driver rexray/ebs \
    --opt size=100 \
    --opt volumeType=gp3 \
    mydata

# Use the volume
$ docker run -d -v mydata:/data myapp

# List plugins
$ docker plugin ls

# Other volume plugins:
#   rexray/ebs     — AWS EBS volumes
#   rexray/s3fs    — AWS S3 as filesystem
#   local-persist  — Persistent local volumes
#   netapp/trident — NetApp storage
```

### Network Plugins

```bash
# Install Weave Net plugin
$ docker plugin install weaveworks/net-plugin:latest_release

# Create a network using the plugin
$ docker network create --driver weaveworks/net-plugin:latest_release mynet

# Other network plugins:
#   calico     — Network policy enforcement
#   flannel    — Simple overlay networking
#   weave      — Mesh networking with encryption
```

### Docker Desktop Extensions

```bash
# List available extensions
$ docker extension ls

# Install an extension
$ docker extension install docker/disk-usage-extension

# Popular extensions:
#   Disk Usage      — Visualize Docker disk usage
#   Logs Explorer   — Advanced log viewing
#   Volumes Backup  — Backup and restore volumes
#   Snyk            — Security scanning
#   Portainer       — Container management UI
```

---

## 31.12 Common Errors and Troubleshooting

### Error 1: DinD "Cannot connect to the Docker daemon"

```bash
# Inside a DinD container, the daemon may not be ready yet
# Fix: Wait for the daemon to start
$ docker run --privileged -d --name dind docker:24-dind
$ sleep 5   # Wait for daemon startup
$ docker exec dind docker info

# Or check daemon readiness in a script
$ until docker exec dind docker info >/dev/null 2>&1; do sleep 1; done
```

### Error 2: Rootless "permission denied" on volume mount

```bash
# Rootless Docker can't access files owned by other users
# Fix: Ensure files are owned by your user
$ sudo chown -R $(id -u):$(id -g) /path/to/data

# Or use --userns=keep-id with Podman
$ podman run -v /path/to/data:/data:Z --userns=keep-id myapp
```

### Error 3: Podman "short-name resolution" prompt

```bash
# Podman asks which registry to use for unqualified image names
# Fix: Configure unqualified-search-registries
$ cat /etc/containers/registries.conf
unqualified-search-registries = ["docker.io"]

# Or use fully qualified names
$ podman pull docker.io/library/nginx
```

### Error 4: Docker context SSH connection fails

```bash
# Fix: Ensure SSH key-based auth is configured
$ ssh-copy-id deploy@staging.example.com

# Test SSH connection
$ ssh deploy@staging.example.com docker info

# Ensure Docker is installed on the remote host
```

---

## Module 31 Summary

- **Docker-in-Docker** has three methods: socket bind (simple, insecure), privileged (isolated, insecure), sidecar (CI pattern)
- Socket bind mount shares the host's Docker daemon — fast but no isolation
- Privileged DinD runs a nested daemon — isolated but requires `--privileged`
- **Kaniko** builds images without a Docker daemon — ideal for Kubernetes CI
- **Rootless Docker** runs the entire stack as a regular user — defense in depth
- Rootless limitations: no ports < 1024, no host networking, limited cgroup support
- **Podman** is a daemonless, rootless-by-default Docker alternative with compatible CLI
- Podman supports **pods** (container groups) and can generate Kubernetes YAML
- **Wasm containers** offer ~1ms startup and ~1MB images but have limited ecosystem
- Docker Desktop alternatives: **Colima**, **Rancher Desktop**, **OrbStack**, **Podman Desktop**
- **Docker contexts** manage multiple Docker hosts (local, staging, production) from one CLI
- Volume and network **plugins** extend Docker with cloud storage and advanced networking

---

**Previous Module: [Module 30 - Debugging and Troubleshooting](module-30-debugging-troubleshooting.md)**

**Next Module: [Module 32 - Enterprise Architecture and Capstone](module-32-enterprise-capstone.md)**
