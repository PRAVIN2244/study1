# Module 25: Containers and Virtualization

## 12.5 Containers Basics (Docker)

### Essential Docker commands

```bash
# Run a container
$ docker run -d --name web -p 80:80 nginx
a1b2c3d4e5f6...

# List running containers
$ docker ps
CONTAINER ID   IMAGE   COMMAND                  STATUS          PORTS                NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   Up 2 minutes   0.0.0.0:80->80/tcp   web

# List all containers (including stopped)
$ docker ps -a

# View logs
$ docker logs web
$ docker logs -f web          # Follow

# Execute command inside container
$ docker exec -it web bash
root@a1b2c3d4e5f6:/# ls /etc/nginx/
nginx.conf  conf.d  mime.types

# Stop and remove
$ docker stop web
$ docker rm web

# Remove all stopped containers
$ docker container prune -f
```

### Docker images

```bash
# List images
$ docker images
REPOSITORY   TAG       IMAGE ID       CREATED        SIZE
nginx        latest    a1b2c3d4e5f6   2 weeks ago    187MB
ubuntu       22.04     f6e5d4c3b2a1   3 weeks ago    77.8MB

# Pull an image
$ docker pull python:3.11-slim

# Build from Dockerfile
$ docker build -t myapp:v1 .

# Remove unused images
$ docker image prune -a -f
```

### Dockerfile example

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

USER nobody

CMD ["python", "app.py"]
```

### Docker Compose

```bash
$ cat docker-compose.yml
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    depends_on:
      - api

  api:
    build: ./api
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://db:5432/myapp
    depends_on:
      - db

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret

volumes:
  pgdata:

$ docker compose up -d
$ docker compose ps
$ docker compose logs -f api
$ docker compose down
```

### Docker resource inspection

```bash
# Container resource usage
$ docker stats
CONTAINER ID   NAME   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O          BLOCK I/O
a1b2c3d4e5f6   web    0.50%   12.5MiB / 7.8GiB    0.16%   1.2kB / 500B     0B / 0B

# Inspect container details
$ docker inspect web | jq '.[0].NetworkSettings.IPAddress'
"172.17.0.2"

# View container filesystem changes
$ docker diff web
C /var
C /var/log
A /var/log/nginx/access.log
```

---


## 12.15 Linux Namespaces and cgroups

These two kernel features are the foundation of container technology.

### Namespaces — Isolation

Namespaces isolate what a process can see:

| Namespace | Isolates |
|-----------|----------|
| **PID** | Process IDs — each container has its own process tree |
| **NET** | Network stack — isolated interfaces, routes, ports |
| **MNT** | Mount points — separate filesystem views |
| **IPC** | Inter-process communication |
| **UTS** | Hostname — allows hostname isolation |
| **USER** | User/group IDs — maps UIDs differently inside vs outside |

```bash
# View namespaces of a process
ls -la /proc/<PID>/ns/

# List all namespaces
lsns

# Enter a namespace of a running container
sudo nsenter -t <PID> -n -p -m
```

### cgroups — Resource Limits

cgroups (control groups) limit what a process can use:

| Controller | Limits |
|-----------|--------|
| `cpu` | CPU time allocation |
| `memory` | RAM limits |
| `blkio` | Disk I/O bandwidth |
| `pids` | Maximum number of processes |

```bash
# View current cgroup assignment
cat /proc/self/cgroup

# View cgroup hierarchy
systemd-cgls

# Run a command with memory limit using systemd-run
sudo systemd-run --scope -p MemoryMax=100M ./heavy_script.sh

# Check cgroup v2 controllers
cat /sys/fs/cgroup/cgroup.controllers
```

**Real-world use**: Docker and Kubernetes use cgroups to enforce `--memory` and `--cpus` limits on containers. When a container exceeds its memory limit, the kernel's OOM killer terminates it.

---

## 12.16 Podman — Daemonless Container Engine

Podman is a Docker-compatible container tool that runs without a background daemon and supports rootless containers.

```bash
# Install Podman
sudo apt install podman        # Debian/Ubuntu
sudo dnf install podman        # RHEL/Fedora

# Run a container (same syntax as Docker)
podman run -d --name web -p 8080:80 nginx

# List containers
podman ps

# View logs
podman logs web

# Execute inside container
podman exec -it web bash

# Stop and remove
podman stop web
podman rm web

# Build an image
podman build -t myapp .

# Run rootless (no sudo needed)
podman run --rm alpine echo "Hello from rootless container"
```

### Docker vs Podman

| Feature | Docker | Podman |
|---------|--------|--------|
| Daemon | Requires `dockerd` | Daemonless |
| Root | Needs root by default | Supports rootless |
| CLI | `docker` | `podman` (compatible) |
| Compose | `docker-compose` | `podman-compose` |
| Kubernetes | Separate tool | Built-in `podman generate kube` |

---


## 12.21 chroot — Filesystem Isolation

`chroot` changes the apparent root directory for a process, restricting its filesystem view.

```bash
# Create a minimal chroot environment
sudo mkdir -p /mychroot/{bin,lib,lib64}
sudo cp /bin/bash /mychroot/bin/
sudo cp /bin/ls /mychroot/bin/

# Copy required libraries
sudo cp $(ldd /bin/bash | grep -o '/lib[^ ]*') /mychroot/lib/ 2>/dev/null
sudo cp $(ldd /bin/bash | grep -o '/lib64[^ ]*') /mychroot/lib64/ 2>/dev/null

# Enter the chroot
sudo chroot /mychroot /bin/bash

# Inside chroot: can only see /mychroot as /
ls /
# Output: bin  lib  lib64
```

### chroot vs Containers

| Feature | chroot | Container (Docker) |
|---------|--------|-------------------|
| Filesystem isolation | Yes | Yes |
| Process isolation | No | Yes (PID namespace) |
| Network isolation | No | Yes (NET namespace) |
| Resource limits | No | Yes (cgroups) |
| Security | Weak (can escape) | Strong (multiple layers) |

**Real-world**: chroot is used for system recovery (boot from live USB, chroot into broken system), building packages in clean environments, and running legacy applications.

---

## 12.22 KVM — Kernel-based Virtual Machine

KVM turns Linux into a Type-1 hypervisor for running full virtual machines.

```bash
# Check if CPU supports virtualization
egrep -c '(vmx|svm)' /proc/cpuinfo
# Output > 0 means supported

# Install KVM
sudo apt install qemu-kvm libvirt-daemon-system virtinst bridge-utils

# Check KVM is loaded
lsmod | grep kvm

# Create a VM
sudo virt-install \
  --name myvm \
  --ram 2048 \
  --vcpus 2 \
  --disk size=20 \
  --os-variant ubuntu22.04 \
  --cdrom /path/to/ubuntu.iso

# List VMs
virsh list --all

# Start/stop VMs
virsh start myvm
virsh shutdown myvm

# Connect to VM console
virsh console myvm
```

### VMs vs Containers — When to Use Each

| Use Case | VM | Container |
|----------|-----|-----------|
| Different OS kernels | Yes | No |
| Legacy applications | Yes | Maybe |
| Strong isolation | Yes | Partial |
| Microservices | Overkill | Ideal |
| Fast startup | Minutes | Milliseconds |
| Resource efficiency | Lower | Higher |

---

## 12.23 Container Security

### Securing Docker/Podman Containers

```bash
# Run as non-root user
docker run --user 1000:1000 myapp

# Drop all capabilities, add only what's needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp

# Read-only filesystem
docker run --read-only myapp

# No new privileges
docker run --security-opt=no-new-privileges myapp

# Resource limits
docker run --memory=256m --cpus=0.5 myapp
```

### Kubernetes Security Context

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: myapp
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
```

### Container Runtime Tools

```bash
# crictl — interact with container runtimes (containerd, CRI-O)
crictl ps                    # List running containers
crictl inspect <container>   # Container details
crictl logs <container>      # Container logs
crictl pods                  # List pods

# ctr — low-level containerd CLI
sudo ctr containers list
sudo ctr images list
```

---

## 12.24 Kubernetes Persistent Volumes

Linux storage is used by Kubernetes for persistent data:

```yaml
# PersistentVolume using hostPath (for testing)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-data
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/data

---
# PersistentVolumeClaim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

```bash
# Linux tools used by CSI drivers under the hood
mkfs.ext4 /dev/xvdf         # Format attached volume
mount /dev/xvdf /mnt/data   # Mount it
blkid /dev/xvdf             # Get UUID
```

**Real-world**: Cloud block storage (AWS EBS, GCP Persistent Disk) attaches as Linux block devices. CSI drivers use `mkfs`, `mount`, and `blkid` to manage them.

---

