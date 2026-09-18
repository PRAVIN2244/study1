# MODULE 2: Docker & Container Fundamentals

---

## 2.1 Docker & Container Basics (Prerequisites)

Before Kubernetes, you need to understand containers.

### Building a Docker Image

```bash
# Create a simple Node.js application
mkdir my-app && cd my-app

cat > app.js << 'EOF'
const http = require('http');
const os = require('os');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    message: 'Hello from Kubernetes!',
    hostname: os.hostname(),
    platform: os.platform(),
    uptime: process.uptime()
  }));
});

server.listen(3000, () => {
  console.log('Server running on port 3000');
});
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY app.js .
EXPOSE 3000
CMD ["node", "app.js"]
EOF

# Build the image
docker build -t my-app:v1 .

# Output:
# [+] Building 5.2s (8/8) FINISHED
#  => [1/3] FROM docker.io/library/node:18-alpine
#  => [2/3] WORKDIR /app
#  => [3/3] COPY app.js .
#  => exporting to image
#  => => naming to docker.io/library/my-app:v1

# Run the container
docker run -d -p 3000:3000 --name my-app my-app:v1

# Test it
curl http://localhost:3000

# Output:
# {"message":"Hello from Kubernetes!","hostname":"a1b2c3d4e5f6","platform":"linux","uptime":2.345}

# Push to Amazon ECR (Elastic Container Registry)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag my-app:v1 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v1
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v1
```

### Commands, Arguments, and ENTRYPOINT

Understanding how containers run processes is essential — these concepts map directly to Kubernetes pod definitions.

**Why containers exit immediately:**

```bash
docker run ubuntu
```

The container starts and exits immediately. Why?

```bash
docker ps        # Shows nothing — container already exited
docker ps -a     # Shows the exited container
```

```
CONTAINER ID   IMAGE    COMMAND       CREATED          STATUS                     PORTS
45aacca36850   ubuntu   "/bin/bash"   43 seconds ago   Exited (0) 41 seconds ago
```

Containers are designed to run a **single process**. The Ubuntu image's default command is `bash`, which exits immediately when there's no terminal attached. Unlike VMs, a container's lifecycle is tied to its main process — when the process ends, the container stops.

**CMD — setting the default command:**

Every Docker image has a `CMD` instruction that defines what runs when the container starts:

```dockerfile
# nginx image — runs a long-lived server process
CMD ["nginx"]

# ubuntu image — runs bash (exits immediately without a terminal)
CMD ["bash"]
```

CMD can be specified in two formats:

```dockerfile
# Shell form
CMD sleep 5

# JSON array form (preferred — no shell interpretation)
CMD ["sleep", "5"]
```

Override CMD at runtime by appending a command:

```bash
docker run ubuntu sleep 5    # Overrides CMD ["bash"] with sleep 5
```

To make the change permanent, create a new image:

```dockerfile
FROM ubuntu
CMD ["sleep", "5"]
```

```bash
docker build -t ubuntu-sleeper .
docker run ubuntu-sleeper          # Sleeps for 5 seconds, then exits
```

**ENTRYPOINT — fixed command with variable arguments:**

ENTRYPOINT sets the executable, and runtime arguments are **appended** to it (not replaced):

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
```

```bash
docker run ubuntu-sleeper 10       # Runs: sleep 10
docker run ubuntu-sleeper          # Error: sleep requires an operand
```

**CMD + ENTRYPOINT together — default arguments:**

Combine both to set a default argument that can be overridden:

```dockerfile
FROM ubuntu
ENTRYPOINT ["sleep"]
CMD ["5"]
```

```bash
docker run ubuntu-sleeper          # Runs: sleep 5 (CMD provides default)
docker run ubuntu-sleeper 10       # Runs: sleep 10 (runtime arg overrides CMD)
```

**Overriding ENTRYPOINT at runtime:**

```bash
docker run --entrypoint sleep2.0 ubuntu-sleeper 10    # Runs: sleep2.0 10
```

**How this maps to Kubernetes:**

| Docker | Kubernetes Pod Spec | Purpose |
|--------|-------------------|---------|
| `ENTRYPOINT` | `command` | The executable to run |
| `CMD` | `args` | Arguments passed to the executable |

**Example 1 — Override only the arguments (CMD):**

The image's ENTRYPOINT (`sleep`) is kept; only the default argument changes from 5 to 10:

```yaml
# pod-definition.yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper-pod
spec:
  containers:
  - name: ubuntu-sleeper
    image: ubuntu-sleeper
    args: ["10"]             # Overrides CMD ["5"] → runs: sleep 10
```

```bash
kubectl create -f pod-definition.yaml
```

```
pod/ubuntu-sleeper-pod created
```

**Example 2 — Override both the command (ENTRYPOINT) and arguments (CMD):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ubuntu-sleeper-pod
spec:
  containers:
  - name: ubuntu-sleeper
    image: ubuntu-sleeper
    command: ["sleep2.0"]    # Overrides ENTRYPOINT
    args: ["10"]             # Overrides CMD
```

Key rules:
- `command` in Kubernetes overrides `ENTRYPOINT` in Docker
- `args` in Kubernetes overrides `CMD` in Docker
- If you only set `args`, the image's `ENTRYPOINT` is used with your arguments
- If you only set `command`, the image's `CMD` is ignored entirely

**Common pitfall — numbers must be strings in YAML arrays:**

```yaml
# WRONG — causes error
command:
- "sleep"
- 1200
```

```
error: cannot unmarshal number into Go value of type string
```

```yaml
# CORRECT — all elements must be quoted strings
command:
- "sleep"
- "1200"
```

**Changing command on a running pod:**

Container commands are immutable. You cannot edit them on a running pod. Instead, edit the manifest and force-replace:

```bash
kubectl edit pod ubuntu-sleeper-3
# Change "1200" to "2000", save → error: field is immutable
# The edited YAML is saved to a temp file

kubectl replace --force -f /tmp/kubectl-edit-2693604347.yaml
```

```
pod "ubuntu-sleeper-3" deleted
pod/ubuntu-sleeper-3 replaced
```

**Passing arguments with `kubectl run`:**

Use `--` to separate kubectl flags from container arguments:

```bash
kubectl run webapp-green --image=kodekloud/webapp-color -- --color green
```

Everything after `--` is passed as arguments to the container (overrides CMD). The container runs: `python app.py --color green` (assuming the image's ENTRYPOINT is `python app.py`).

### Docker Service Configuration

On Linux, Docker runs as a systemd service. Understanding how to manage and configure the Docker daemon is a prerequisite for troubleshooting container runtime issues.

#### Managing the Docker Service

```bash
# Check Docker service status
systemctl status docker

# Output:
# ● docker.service - Docker Application Container Engine
#    Loaded: loaded (/lib/systemd/system/docker.service; enabled)
#    Active: active (running) since Wed 2024-01-15 04:21:01 UTC; 3 days ago
#    Main PID: 4197 (dockerd)

# Start / stop / restart
systemctl start docker
systemctl stop docker
systemctl restart docker

# Enable Docker to start at boot
systemctl enable docker
```

#### Running the Docker Daemon in the Foreground

For troubleshooting, run `dockerd` directly instead of as a service. Log messages print to the console:

```bash
# Start daemon in foreground
dockerd

# Start with debug logging
dockerd --debug

# Output:
# INFO[2024-01-15T08:20:40.372Z] Starting up
# INFO[2024-01-15T08:20:40.375Z] parsed scheme: "unix"
# INFO[2024-01-15T08:20:40.381Z] [graphdriver] using prior storage driver: overlay2
# DEBU[2024-01-15T08:20:40.332Z] Listener created for HTTP on unix (/var/run/docker.sock)
```

#### Docker Daemon Communication

When Docker starts, it listens on a Unix socket at `/var/run/docker.sock`. The Docker CLI communicates with the daemon through this socket (IPC — Inter-Process Communication).

```
Docker CLI (docker ps) → /var/run/docker.sock → Docker Daemon (dockerd)
```

#### Remote Access via TCP

To manage Docker on a remote host, configure the daemon to listen on a TCP interface:

```bash
# Start daemon with TCP listener (unencrypted — development only)
dockerd --debug --host=tcp://192.168.1.10:2375

# On your laptop — connect to the remote Docker host
export DOCKER_HOST="tcp://192.168.1.10:2375"
docker ps
```

⚠️ Exposing Docker over TCP without TLS is a security risk. Use port 2376 with TLS for production (covered in MODULE-10 Security Hardening).

#### Configuration File: /etc/docker/daemon.json

Instead of passing flags on the command line, use a JSON configuration file. This file is not created by default — you must create it manually:

```json
{
  "debug": true,
  "hosts": ["tcp://192.168.1.10:2376"],
  "tls": true,
  "tlscert": "/var/docker/server.pem",
  "tlskey": "/var/docker/serverkey.pem"
}
```

The `hosts` property is an array — you can specify multiple listeners (Unix socket + TCP).

⚠️ **Conflict rule:** If a parameter is set in both `daemon.json` and as a command-line flag, Docker fails to start with a conflict error. Use one or the other, not both.

```bash
# After updating daemon.json, restart the service
systemctl restart docker
```

**Common daemon.json settings:**

| Setting | Purpose | Example |
|---|---|---|
| `debug` | Enable debug logging | `true` |
| `hosts` | Listening interfaces | `["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"]` |
| `storage-driver` | Storage driver | `"overlay2"` |
| `log-driver` | Default log driver | `"json-file"` |
| `log-opts` | Log driver options | `{"max-size": "10m", "max-file": "3"}` |
| `default-address-pools` | Custom subnet ranges | `[{"base": "172.80.0.0/16", "size": 24}]` |
| `insecure-registries` | Allow HTTP registries | `["myregistry.local:5000"]` |

---


---

## 2.2 Docker Storage Fundamentals

Understanding Docker storage is a prerequisite for Kubernetes storage concepts. Docker manages storage through two mechanisms: **storage drivers** (image layers and container writable layers) and **volume drivers** (persistent data).

### Docker File System

When Docker is installed, it creates a directory structure at `/var/lib/docker`:

```bash
ls /var/lib/docker/
# overlay2/     ← Image and container layers (storage driver data)
# containers/   ← Container runtime data (logs, config)
# images/       ← Image metadata
# volumes/      ← Named volumes
```

### Image Layers and Caching

Each instruction in a Dockerfile creates a new layer. Layers are read-only and cached for reuse.

```dockerfile
# Dockerfile
FROM ubuntu                                    # Layer 1: Base image (~120 MB)
RUN apt-get update && apt-get -y install python # Layer 2: APT packages (~300 MB)
RUN pip install flask flask-mysql              # Layer 3: Python packages
COPY . /opt/source-code                        # Layer 4: Application code
ENTRYPOINT FLASK_APP=/opt/source-code/app.py flask run  # Layer 5: Entrypoint
```

```bash
docker build -t myapp:v1 .
```

If a second application shares the same base image and packages but has different source code, Docker reuses layers 1-3 from cache and only builds layers 4-5. This saves disk space and build time.

### Container Writable Layer and Copy-on-Write

Image layers are immutable. When you run a container, Docker adds a thin **writable layer** on top:

```
┌─────────────────────────────────┐
│  Container Layer (read-write)   │  ← Runtime changes: logs, temp files
├─────────────────────────────────┤
│  Layer 5: ENTRYPOINT            │  ← Read-only (image)
│  Layer 4: COPY source code      │
│  Layer 3: pip install           │
│  Layer 2: apt-get install       │
│  Layer 1: Ubuntu base           │
└─────────────────────────────────┘
```

If a container modifies a file from an image layer (e.g., `app.py`), Docker uses **copy-on-write**: it copies the file to the writable layer first, then applies changes there. The original image layer is untouched.

When the container is removed, the writable layer is deleted — all runtime data is lost. This is why containers are ephemeral.

### Docker Volumes and Bind Mounts

To persist data beyond the container lifecycle, use volumes or bind mounts.

**Volume mount** — Docker manages the storage under `/var/lib/docker/volumes`:

```bash
# Create a named volume
docker volume create data_volume

# Mount it into a container
docker run -v data_volume:/var/lib/mysql mysql

# Docker auto-creates the volume if it doesn't exist
docker run -v data_volume2:/var/lib/mysql mysql
```

**Bind mount** — map a specific host directory into the container:

```bash
docker run -v /data/mysql:/var/lib/mysql mysql
```

**`--mount` flag** — more explicit syntax (preferred in modern Docker):

```bash
docker run \
  --mount type=bind,source=/data/mysql,target=/var/lib/mysql \
  mysql
```

| Mount Type | Managed By | Location | Use Case |
|---|---|---|---|
| Volume | Docker | `/var/lib/docker/volumes/` | Databases, persistent app data |
| Bind mount | User | Any host path | Development, config files |
| tmpfs | Kernel | Memory only | Sensitive data, temp files |

### Storage Drivers vs Volume Drivers

These are two separate systems in Docker:

| | Storage Drivers | Volume Drivers |
|---|---|---|
| **Manages** | Image layers, container writable layer, copy-on-write | Persistent volumes |
| **Data lifecycle** | Tied to container (deleted with container) | Independent of container |
| **Examples** | overlay2, AUFS, devicemapper, ZFS, BTRFS | local, Rex-Ray, Portworx, NetApp |
| **Selection** | Auto-selected by Docker based on OS | Specified per volume |

**Common storage drivers:**

| Driver | OS | Notes |
|---|---|---|
| `overlay2` | Ubuntu, CentOS 7+ | Default on most modern systems |
| `aufs` | Ubuntu (older) | Legacy, being replaced by overlay2 |
| `devicemapper` | CentOS/RHEL | Block-level storage |
| `zfs` | Ubuntu | Advanced features (snapshots, compression) |
| `btrfs` | SUSE | Copy-on-write filesystem |

Docker automatically selects the best storage driver for your OS.

**Volume driver plugins** enable provisioning volumes on external storage systems:

```bash
# Default: local volume driver (stores in /var/lib/docker/volumes/)
docker run -v mydata:/var/lib/mysql mysql

# Third-party: Rex-Ray driver provisions an AWS EBS volume
docker run -it \
  --name mysql \
  --volume-driver rexray/ebs \
  --mount src=ebs-vol,target=/var/lib/mysql \
  mysql
```

With Rex-Ray, the volume is an actual EBS disk in AWS — data persists even if the container and host are destroyed. This concept maps directly to Kubernetes PersistentVolumes backed by cloud storage (EBS, EFS, etc.) via CSI drivers.

---


---

## 2.3 Docker vs ContainerD

Docker and ContainerD are both container runtimes, but they serve different roles in the Kubernetes ecosystem. This section explains how container runtimes evolved, why Docker was deprecated, and which CLI tools to use.

### The Evolution of Container Runtimes

At the dawn of the container era, Docker was the dominant runtime. Kubernetes was initially designed to orchestrate Docker containers, creating a tight coupling between them.

As other runtimes (like Rocket/rkt) emerged, Kubernetes introduced the **Container Runtime Interface (CRI)** — a standard API that any runtime can implement. CRI requires compliance with the **Open Container Initiative (OCI)** standards:

| OCI Standard | Purpose |
|---|---|
| **Image Spec** | How container images are built and structured |
| **Runtime Spec** | How containers are created and executed |

Since Docker predated CRI, it wasn't CRI-compatible. Kubernetes used a workaround called **Docker Shim** — a translation layer between CRI and Docker's API.

### Docker's Internal Architecture

Docker is not just a runtime — it's a collection of tools:

```
Docker CLI / API
    │
    ├── Image build tools
    ├── Volume management
    ├── Authentication & security
    │
    └── containerd  ← The actual container runtime
            │
            └── runc  ← Low-level runtime that creates containers
```

The key insight: **containerd** (the part Kubernetes actually needs) was always inside Docker. Docker added CLI tools, image building, and other features on top.

### Why Docker Was Deprecated (Kubernetes v1.24)

```
Before v1.24:
  kubelet → Docker Shim → Docker → containerd → runc → container

After v1.24:
  kubelet → CRI → containerd → runc → container
```

Kubernetes v1.24 removed Docker Shim because:
- Maintaining the shim added complexity
- containerd is CRI-compatible and works directly with kubelet
- Docker added unnecessary overhead for Kubernetes' needs

**Docker images still work.** They are OCI-compliant. Only the Docker daemon as a runtime was removed.

#### A Note on Docker's Continued Relevance

"Deprecated as a Kubernetes runtime" does **not** mean Docker is dead. Docker remains the most widely used tool for:

| Use Case | Why Docker Is Still Used |
|---|---|
| **Building container images** | `docker build` / `docker buildx` is the standard image build workflow |
| **Local development** | Running containers locally with `docker run`, `docker compose` |
| **Learning container fundamentals** | Docker's CLI is the most intuitive way to understand images, containers, volumes, and networking |
| **CI/CD pipelines** | Most CI systems (GitHub Actions, GitLab CI, Jenkins) use Docker for build steps |

The deprecation only affects the Kubernetes runtime layer:

```
What changed (K8s runtime):
  ❌  kubelet → dockershim → Docker → containerd
  ✅  kubelet → CRI → containerd (direct)

What did NOT change:
  ✅  docker build -t myapp:v1 .          ← Still works
  ✅  docker push myapp:v1                ← Still works
  ✅  Kubernetes pulling Docker images    ← Still works (OCI-compliant)
```

If you learn container concepts using Docker first, transitioning to Kubernetes and containerd is straightforward. Docker commands map directly to `nerdctl` (see CLI Tools Comparison below) and container images built with Docker work identically on containerd.

### ContainerD as a Standalone Runtime

ContainerD started as an internal Docker component but is now an independent project under the **Cloud Native Computing Foundation (CNCF)**. You can install it without Docker:

```bash
# Install ContainerD standalone
tar -C /usr/local -zxvf containerd-1.6.2-linux-amd64.tar.gz

# Output:
# bin/
# bin/ctr
# bin/containerd
# ...
```

### CLI Tools Comparison

Three CLI tools interact with container runtimes. Each serves a different purpose:

| Tool | Maintained By | Purpose | Works With |
|---|---|---|---|
| **ctr** | ContainerD community | Debugging only | ContainerD only |
| **nerdctl** | ContainerD community | General-purpose (Docker replacement) | ContainerD only |
| **crictl** | Kubernetes community | Debugging & inspection | Any CRI-compatible runtime |

#### ctr — ContainerD Debugging Tool

Bundled with ContainerD. Limited features, not user-friendly. Use only for debugging.

```bash
# Pull an image
ctr images pull docker.io/library/redis:alpine

# Run a container
ctr run docker.io/library/redis:alpine redis
```

#### nerdctl — Docker-like CLI for ContainerD

Drop-in replacement for Docker CLI with additional ContainerD features:
- Encrypted container images
- Lazy pulling of images
- Peer-to-peer image distribution
- Image signing and verification

```bash
# Docker command:
docker run --name redis redis:alpine
docker run --name webserver -p 80:80 -d nginx

# Equivalent nerdctl command (just replace "docker" with "nerdctl"):
nerdctl run --name redis redis:alpine
nerdctl run --name webserver -p 80:80 -d nginx
```

#### crictl — Kubernetes CRI Debugging Tool

Works with any CRI-compatible runtime (ContainerD, CRI-O, etc.). Designed for debugging — not for creating production containers.

```bash
# Pull an image
crictl pull busybox

# List images
crictl images

# List all containers (including stopped)
crictl ps -a

# List pods (unique to crictl — Docker CLI cannot do this)
crictl pods

# Execute into a container
crictl exec -i -t <container-id> sh

# View container logs
crictl logs <container-id>
```

> **Warning:** Containers created manually with `crictl` are not part of any Kubernetes Pod. The kubelet will detect and remove them.

### Docker CLI vs crictl Command Mapping

| Docker Command | crictl Equivalent | Description |
|---|---|---|
| `docker attach` | `crictl attach` | Attach to a running container |
| `docker exec` | `crictl exec` | Execute command in container |
| `docker images` | `crictl images` | List images |
| `docker info` | `crictl info` | Display runtime info |
| `docker inspect` | `crictl inspect` | Inspect container details |
| `docker logs` | `crictl logs` | View container logs |
| `docker ps` | `crictl ps` | List containers |
| `docker stats` | `crictl stats` | Display resource usage |
| `docker version` | `crictl version` | Show version |
| `docker pull` | `crictl pull` | Pull an image |
| — | `crictl pods` | List pods (no Docker equivalent) |

### Kubernetes Runtime Endpoint Configuration

Earlier Kubernetes versions tried runtime endpoints in this order:

```
unix:///var/run/dockershim.sock       ← Removed in v1.24
unix:///run/containerd/containerd.sock
unix:///run/crio/crio.sock
unix:///var/run/cri-dockerd.sock      ← Added in v1.24 (for Docker via cri-dockerd)
```

After v1.24, you should explicitly set the runtime endpoint:

```bash
# Option 1: Pass as flag
crictl --runtime-endpoint unix:///run/containerd/containerd.sock ps

# Option 2: Set as environment variable
export CONTAINER_RUNTIME_ENDPOINT=unix:///run/containerd/containerd.sock
crictl ps
```

### Summary Table

| Tool | Use Case | Recommended For |
|---|---|---|
| **ctr** | Low-level ContainerD debugging | Developers debugging ContainerD internals |
| **nerdctl** | General container management (Docker replacement) | Day-to-day container operations |
| **crictl** | CRI-compatible runtime debugging | Kubernetes node troubleshooting |
| **docker** | Building images, local development | Development workflows (not as K8s runtime) |

---

