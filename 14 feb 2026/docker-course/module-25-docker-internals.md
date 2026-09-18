# Module 25: Docker Internals Deep Dive

Understanding what happens beneath `docker run` — the runtime stack,
OCI specifications, and Linux kernel primitives that make containers work.

### Topics Covered

```
25.1  The Container Runtime Stack
25.2  OCI Specifications (image-spec and runtime-spec)
25.3  containerd — The Container Supervisor
25.4  runc — The Low-Level Runtime
25.5  The Shim Process (containerd-shim)
25.6  Linux Namespaces — Full Taxonomy
25.7  Control Groups v2 (cgroups v2)
25.8  Union Filesystems and OverlayFS Internals
25.9  Seccomp, Capabilities, and LSMs at the Kernel Level
25.10 Walking Through docker run — Syscall by Syscall
25.11 Building a Container from Scratch (No Docker)
25.12 Common Errors and Troubleshooting
```

---

## 25.1 The Container Runtime Stack

When you type `docker run nginx`, a chain of components activates.
Each layer has a single responsibility.

```
┌─────────────────────────────────────────────────────────────────┐
│                        docker CLI                               │
│  Parses flags, builds API request, sends to daemon              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (unix socket or TCP+TLS)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        dockerd                                  │
│  Image management, networking, volumes, build                   │
│  Translates high-level requests into containerd gRPC calls      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ gRPC (ttrpc)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      containerd                                 │
│  Manages container lifecycle: create, start, stop, delete       │
│  Manages image pull/push, snapshots, content store              │
│  Spawns a shim per container                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ fork/exec
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   containerd-shim-runc-v2                       │
│  Keeps container alive even if containerd restarts              │
│  Holds stdio pipes, forwards exit status                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ fork/exec
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         runc                                    │
│  Sets up namespaces, cgroups, mounts, seccomp, pivot_root       │
│  Execs the container entrypoint (PID 1 inside container)        │
│  Exits after container process starts                           │
└─────────────────────────────────────────────────────────────────┘
```

### Why So Many Layers?

```
# Before Docker 1.11, dockerd did everything — image pulls,
# container lifecycle, networking, volumes — in one monolithic binary.
#
# Problems:
#   - Restarting dockerd killed all running containers
#   - No standard interface — vendor lock-in
#   - Difficult to test or replace components
#
# The refactoring split responsibilities:
#   dockerd      → orchestration, API, networking, volumes
#   containerd   → container lifecycle, image management
#   runc         → Linux kernel setup (namespaces, cgroups)
#   shim         → keeps containers alive across daemon restarts
#
# Benefit: You can restart dockerd without stopping containers
# (requires "live-restore": true in daemon.json)
```

### Verifying the Stack on Your System

```bash
# Check all components are installed
$ docker version
# Shows Client and Server versions

$ containerd --version
# containerd containerd.io 1.7.x ...

$ runc --version
# runc version 1.1.x
# spec: 1.0.2-dev  ← OCI runtime-spec version

# See the process tree for a running container
$ docker run -d --name test nginx
$ ps auxf | grep -A 5 containerd-shim
# root  1234  containerd-shim-runc-v2 -namespace moby -id <container-id>
#   └─ root  1240  nginx: master process nginx -g daemon off;
#       ├─ www   1280  nginx: worker process
#       └─ www   1281  nginx: worker process

# The shim is the parent of the container process, NOT dockerd
```

### Real-World Implication

```
# Scenario: You need to upgrade Docker Engine on a production server
# with 50 running containers.
#
# With the shim architecture:
#   1. Stop dockerd:  systemctl stop docker
#   2. Upgrade:       apt-get install docker-ce=5:24.0.7-1~ubuntu
#   3. Start dockerd: systemctl start docker
#   4. All 50 containers are still running (shims kept them alive)
#
# Without shim architecture (Docker < 1.11):
#   Stopping dockerd would kill all 50 containers.
```

---

## 25.2 OCI Specifications (image-spec and runtime-spec)

The Open Container Initiative (OCI) defines two standards that ensure
containers are portable across runtimes.

### OCI Runtime Specification

```
# Defines HOW to run a container.
# Input: a "bundle" — a directory containing:
#   1. config.json  — container configuration
#   2. rootfs/      — the filesystem for the container
#
# config.json specifies:
#   - Which process to run (entrypoint, args, env, cwd)
#   - Which namespaces to create or join
#   - Which cgroups limits to apply
#   - Which mounts to set up
#   - Which Linux capabilities to grant
#   - Which seccomp profile to apply

# Any OCI-compliant runtime (runc, crun, youki, gVisor, Kata)
# can take this bundle and run the container.
```

### Examining a Real OCI Bundle

```bash
# Export a container's filesystem and config
$ docker create --name export-test nginx
$ docker export export-test -o nginx-rootfs.tar
$ mkdir -p bundle/rootfs
$ tar -xf nginx-rootfs.tar -C bundle/rootfs

# Generate the OCI config.json using runc
$ cd bundle
$ runc spec
$ ls
# config.json  rootfs/

# View the generated config.json (abbreviated)
$ cat config.json | python3 -m json.tool | head -60
```

```json
{
    "ociVersion": "1.0.2-dev",
    "process": {
        "terminal": true,
        "user": { "uid": 0, "gid": 0 },
        "args": ["sh"],
        "env": [
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin",
            "TERM=xterm"
        ],
        "cwd": "/",
        "capabilities": {
            "bounding": ["CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"],
            "effective": ["CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"],
            "permitted": ["CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"]
        }
    },
    "root": {
        "path": "rootfs",
        "readonly": true
    },
    "linux": {
        "namespaces": [
            { "type": "pid" },
            { "type": "network" },
            { "type": "ipc" },
            { "type": "uts" },
            { "type": "mount" },
            { "type": "cgroup" }
        ]
    }
}
```

```
# Key fields explained:
#
# ociVersion    — which version of the OCI spec this config targets
# process.args  — the command to run (PID 1 inside the container)
# process.env   — environment variables
# process.capabilities — Linux capabilities granted to the process
# root.path     — path to the root filesystem
# root.readonly — whether rootfs is mounted read-only
# linux.namespaces — which namespaces to create for isolation
```

### OCI Image Specification

```
# Defines HOW to package and distribute container images.
# An OCI image consists of:
#
# 1. Image Manifest — lists all layers and the config
# 2. Image Config   — metadata (env, cmd, labels, history)
# 3. Layer Tarballs  — filesystem diffs (each layer is a tar.gz)
#
# Structure on disk (in a registry):
#
#   blobs/
#     sha256/
#       abc123...  ← layer 1 (tar.gz)
#       def456...  ← layer 2 (tar.gz)
#       789fed...  ← image config (JSON)
#   index.json     ← points to the manifest
#   oci-layout     ← {"imageLayoutVersion": "1.0.0"}

# View an image's manifest from a registry:
$ docker manifest inspect nginx:latest
# Shows: mediaType, digest, size for each layer
```

### OCI Image Index (Multi-Platform)

```bash
# An image index (also called "manifest list") points to
# platform-specific manifests:
$ docker manifest inspect --verbose nginx:latest | head -30

# Output shows entries for:
#   linux/amd64
#   linux/arm64
#   linux/arm/v7
#   linux/386
#   linux/ppc64le
#   linux/s390x
#
# When you pull nginx:latest, Docker selects the manifest
# matching your OS and architecture automatically.
```

---

## 25.3 containerd — The Container Supervisor

containerd is the industry-standard container runtime that manages
the complete container lifecycle on a host.

### What containerd Does

```
┌─────────────────────────────────────────────────────────────────┐
│                    containerd responsibilities                  │
│                                                                 │
│  Image Operations                                               │
│    • Pull images from registries (Docker Hub, ECR, GCR, etc.)  │
│    • Push images to registries                                  │
│    • Store images in a content-addressable store                │
│    • Unpack image layers into snapshots                         │
│                                                                 │
│  Container Lifecycle                                            │
│    • Create containers from image snapshots                     │
│    • Start, stop, pause, resume, delete containers             │
│    • Manage container metadata and state                        │
│                                                                 │
│  Task Management                                                │
│    • Spawn shim processes for each container                    │
│    • Collect exit codes and resource usage                      │
│    • Forward signals to container processes                     │
│                                                                 │
│  Snapshot Management                                            │
│    • Manage filesystem snapshots (overlayfs, btrfs, etc.)      │
│    • Provide copy-on-write layers for containers               │
│                                                                 │
│  Plugins                                                        │
│    • Extensible via gRPC plugins                                │
│    • Supports custom snapshotters, differ, content stores       │
└─────────────────────────────────────────────────────────────────┘
```

### Using ctr — The containerd CLI

```bash
# ctr is the low-level CLI for containerd (not for daily use,
# but essential for debugging and understanding internals)

# Pull an image directly via containerd (bypassing Docker)
$ sudo ctr images pull docker.io/library/alpine:latest

# List images in containerd's store
$ sudo ctr images list
# REF                            TYPE     DIGEST       SIZE
# docker.io/library/alpine:latest application/... sha256:... 3.2 MiB

# Run a container directly via containerd
$ sudo ctr run --rm docker.io/library/alpine:latest test-ctr echo "hello from containerd"
# hello from containerd

# List running containers (tasks)
$ sudo ctr tasks list
# TASK          PID      STATUS
# test-ctr      12345    RUNNING

# List containers (metadata)
$ sudo ctr containers list
```

### containerd Namespaces (Not Linux Namespaces)

```bash
# containerd uses its own "namespace" concept to isolate clients.
# Docker uses the "moby" namespace. Kubernetes uses "k8s.io".

$ sudo ctr namespaces list
# NAME    LABELS
# moby           ← Docker's containers live here
# k8s.io         ← Kubernetes containers (if using containerd CRI)

# List Docker's containers from containerd's perspective
$ sudo ctr -n moby containers list

# List Kubernetes containers
$ sudo ctr -n k8s.io containers list

# This is why Docker containers and Kubernetes pods don't
# interfere with each other even on the same host.
```

### containerd Configuration

```bash
# Default config location: /etc/containerd/config.toml
$ sudo containerd config default > /etc/containerd/config.toml

# Key configuration sections:
$ cat /etc/containerd/config.toml
```

```toml
# /etc/containerd/config.toml (key sections)

version = 2

[plugins."io.containerd.grpc.v1.cri"]
  # Container Runtime Interface for Kubernetes
  sandbox_image = "registry.k8s.io/pause:3.9"

[plugins."io.containerd.grpc.v1.cri".containerd]
  # Default runtime
  default_runtime_name = "runc"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
  runtime_type = "io.containerd.runc.v2"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  # Use cgroups v2 (systemd cgroup driver)
  SystemdCgroup = true

[plugins."io.containerd.grpc.v1.cri".registry]
  # Registry mirror configuration
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."docker.io"]
      endpoint = ["https://registry-1.docker.io"]
```

```bash
# After modifying config.toml, restart containerd
$ sudo systemctl restart containerd
```

---

## 25.4 runc — The Low-Level Runtime

runc is the reference implementation of the OCI runtime specification.
It does the actual Linux kernel work to create a container.

### What runc Does (Step by Step)

```
# When containerd asks runc to create a container, runc:
#
# 1. Reads config.json from the OCI bundle
# 2. Creates Linux namespaces (pid, net, mnt, uts, ipc, user, cgroup)
# 3. Sets up cgroups with resource limits
# 4. Prepares the root filesystem (pivot_root or chroot)
# 5. Sets up mounts (/proc, /sys, /dev, tmpfs, bind mounts)
# 6. Applies seccomp filters (syscall whitelist/blacklist)
# 7. Drops Linux capabilities
# 8. Sets the user/group for the process
# 9. Execs the entrypoint process (becomes PID 1 in the container)
# 10. Exits — runc itself is no longer running
#
# The container process is now a child of the shim, not runc.
```

### Running a Container with runc Directly

```bash
# Create an OCI bundle from an Alpine image
$ mkdir -p /tmp/runc-demo/rootfs
$ docker export $(docker create alpine) | tar -C /tmp/runc-demo/rootfs -xf -
$ cd /tmp/runc-demo

# Generate default OCI config
$ runc spec

# Edit config.json to run "sh" with a terminal
$ cat config.json | python3 -c "
import json, sys
c = json.load(sys.stdin)
c['process']['args'] = ['sh']
c['process']['terminal'] = True
json.dump(c, sys.stdout, indent=2)
" > config2.json && mv config2.json config.json

# Run the container with runc
$ sudo runc run my-container
# You are now inside a container created without Docker!
# Type 'exit' to leave

# List runc containers
$ sudo runc list
# ID              PID     STATUS      BUNDLE                  CREATED
# my-container    5678    running     /tmp/runc-demo          2024-...

# Delete the container
$ sudo runc delete my-container
```

### Alternative OCI Runtimes

```
┌──────────────┬────────────────────────────────────────────────────┐
│ Runtime      │ Description                                        │
├──────────────┼────────────────────────────────────────────────────┤
│ runc         │ Reference implementation. Written in Go.           │
│              │ Used by Docker and most Kubernetes setups.          │
├──────────────┼────────────────────────────────────────────────────┤
│ crun         │ Written in C. Faster startup, lower memory.        │
│              │ Default in Podman. Drop-in replacement for runc.   │
├──────────────┼────────────────────────────────────────────────────┤
│ youki        │ Written in Rust. Focus on safety and performance.  │
│              │ Experimental but growing adoption.                 │
├──────────────┼────────────────────────────────────────────────────┤
│ gVisor       │ Google's sandboxed runtime (runsc). Intercepts     │
│ (runsc)      │ syscalls in userspace. Stronger isolation.         │
│              │ Used in GKE Sandbox.                               │
├──────────────┼────────────────────────────────────────────────────┤
│ Kata         │ Runs each container in a lightweight VM.           │
│ Containers   │ Hardware-level isolation. Used for multi-tenant.   │
├──────────────┼────────────────────────────────────────────────────┤
│ Firecracker  │ AWS microVM technology. Powers Lambda and Fargate. │
│              │ Sub-second VM startup. Minimal attack surface.     │
└──────────────┴────────────────────────────────────────────────────┘
```

```bash
# Configure Docker to use an alternative runtime
# Edit /etc/docker/daemon.json:
{
    "runtimes": {
        "crun": {
            "path": "/usr/bin/crun"
        },
        "runsc": {
            "path": "/usr/local/bin/runsc"
        }
    },
    "default-runtime": "runc"
}

# Run a container with a specific runtime
$ docker run --runtime=crun alpine echo "using crun"
$ docker run --runtime=runsc alpine echo "using gVisor"
```

---

## 25.5 The Shim Process (containerd-shim)

The shim is the unsung hero that keeps containers alive independently
of dockerd and containerd.

### Why the Shim Exists

```
# Problem without a shim:
#   Container process is a child of containerd
#   If containerd restarts → all child processes receive SIGHUP → containers die
#   If dockerd restarts → same problem
#
# Solution: The shim becomes the parent of the container process
#   containerd forks the shim
#   shim forks runc
#   runc sets up the container and execs the entrypoint
#   runc exits
#   shim becomes the direct parent of the container's PID 1
#   containerd can restart without affecting the container
```

### Shim Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                    containerd-shim-runc-v2                      │
│                                                                 │
│  1. Keeps STDIN/STDOUT/STDERR pipes open                       │
│     (so docker logs works even after daemon restart)            │
│                                                                 │
│  2. Reports exit status to containerd                          │
│     (when the container process terminates)                     │
│                                                                 │
│  3. Forwards signals to the container process                  │
│     (docker stop sends SIGTERM via the shim)                    │
│                                                                 │
│  4. Reaps zombie processes                                     │
│     (acts as subreaper for orphaned child processes)            │
│                                                                 │
│  5. Provides an API for containerd to query container state    │
│     (via a Unix socket per shim instance)                       │
└─────────────────────────────────────────────────────────────────┘
```

### Observing the Shim in Action

```bash
# Start a container
$ docker run -d --name shim-demo nginx

# Find the shim process
$ ps aux | grep containerd-shim
# root  2345  containerd-shim-runc-v2 -namespace moby -id abc123...

# See the process tree
$ pstree -p 2345
# containerd-shim(2345)─┬─nginx(2400)─┬─nginx(2450)
#                        │             └─nginx(2451)
#                        └─{containerd-sh}(2346)

# The shim (2345) is the parent of nginx master (2400)
# nginx master spawned worker processes (2450, 2451)

# Now restart dockerd — containers survive
$ sudo systemctl restart docker
$ docker ps
# CONTAINER ID   IMAGE   STATUS          NAMES
# abc123...      nginx   Up 5 minutes    shim-demo
# Container is still running!

# Check the shim is still the same PID
$ ps aux | grep containerd-shim | grep abc123
# Same PID 2345 — shim was never restarted
```

### Shim v1 vs Shim v2

```
┌──────────────────┬──────────────────────┬──────────────────────┐
│                  │ Shim v1              │ Shim v2              │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Binary name      │ containerd-shim      │ containerd-shim-     │
│                  │                      │ runc-v2              │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Processes per    │ One shim per         │ One shim per pod     │
│ container        │ container            │ (can manage multiple │
│                  │                      │ containers)          │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Communication    │ Pipe-based           │ ttrpc (lightweight   │
│                  │                      │ gRPC over Unix sock) │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Memory overhead  │ ~10 MB per shim      │ ~3 MB per shim       │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Status           │ Deprecated           │ Current default      │
└──────────────────┴──────────────────────┴──────────────────────┘
```

---

## 25.6 Linux Namespaces — Full Taxonomy

Namespaces are the Linux kernel feature that provides isolation.
Each namespace type isolates a different system resource.

### All 8 Namespace Types

```
┌──────────┬────────────┬──────────────────────────────────────────┐
│ Type     │ Flag       │ What It Isolates                         │
├──────────┼────────────┼──────────────────────────────────────────┤
│ Mount    │ CLONE_NEWNS│ Filesystem mount points. Container sees  │
│ (mnt)    │            │ its own /proc, /sys, /dev, /tmp.         │
├──────────┼────────────┼──────────────────────────────────────────┤
│ PID      │ CLONE_NEWPID│ Process IDs. Container's entrypoint is  │
│          │            │ PID 1. Cannot see host processes.        │
├──────────┼────────────┼──────────────────────────────────────────┤
│ Network  │ CLONE_NEWNET│ Network stack: interfaces, IPs, routes, │
│ (net)    │            │ iptables, sockets. Each container gets   │
│          │            │ its own eth0, loopback, routing table.   │
├──────────┼────────────┼──────────────────────────────────────────┤
│ UTS      │ CLONE_NEWUTS│ Hostname and domain name. Container can │
│          │            │ have its own hostname (--hostname flag). │
├──────────┼────────────┼──────────────────────────────────────────┤
│ IPC      │ CLONE_NEWIPC│ Inter-process communication: shared     │
│          │            │ memory, semaphores, message queues.      │
├──────────┼────────────┼──────────────────────────────────────────┤
│ User     │ CLONE_NEWUSER│ User and group IDs. Root (UID 0) inside│
│          │            │ maps to unprivileged UID on host.        │
├──────────┼────────────┼──────────────────────────────────────────┤
│ Cgroup   │ CLONE_NEWCGROUP│ Cgroup root directory. Container    │
│          │            │ sees only its own cgroup hierarchy.      │
├──────────┼────────────┼──────────────────────────────────────────┤
│ Time     │ CLONE_NEWTIME│ System clocks (CLOCK_MONOTONIC,        │
│          │            │ CLOCK_BOOTTIME). Linux 5.6+.             │
│          │            │ Docker does NOT use this by default.     │
└──────────┴────────────┴──────────────────────────────────────────┘
```

### Inspecting Container Namespaces

```bash
# Start a container
$ docker run -d --name ns-demo alpine sleep 3600

# Get the container's PID on the host
$ CPID=$(docker inspect --format '{{.State.Pid}}' ns-demo)
$ echo $CPID
# 4567

# List all namespaces for this process
$ sudo ls -la /proc/$CPID/ns/
# lrwxrwxrwx  cgroup -> cgroup:[4026532567]
# lrwxrwxrwx  ipc    -> ipc:[4026532565]
# lrwxrwxrwx  mnt    -> mnt:[4026532563]
# lrwxrwxrwx  net    -> net:[4026532568]
# lrwxrwxrwx  pid    -> pid:[4026532566]
# lrwxrwxrwx  user   -> user:[4026531837]  ← same as host (no user ns)
# lrwxrwxrwx  uts    -> uts:[4026532564]

# Compare with host's namespaces
$ sudo ls -la /proc/1/ns/
# The inode numbers differ — proving isolation

# Enter a container's namespace from the host
$ sudo nsenter --target $CPID --mount --uts --ipc --net --pid -- ps aux
# PID  USER  COMMAND
#   1  root  sleep 3600
# You see only the container's processes
```

### Namespace Sharing Between Containers

```bash
# Share the network namespace (containers share IP and ports)
$ docker run -d --name web nginx
$ docker run --rm --network container:web alpine wget -qO- localhost
# Returns nginx welcome page — both containers share the same
# network namespace (same IP, same loopback, same port space)

# Share the PID namespace (containers see each other's processes)
$ docker run -d --name app --pid=container:web alpine sleep 3600
$ docker exec app ps aux
# Shows both nginx and sleep processes

# Share the IPC namespace (containers can use shared memory)
$ docker run -d --name ipc1 --ipc=shareable alpine sleep 3600
$ docker run -d --name ipc2 --ipc=container:ipc1 alpine sleep 3600
```

---

## 25.7 Control Groups v2 (cgroups v2)

Cgroups limit, account for, and isolate resource usage (CPU, memory,
I/O, PIDs) of a collection of processes.

### cgroups v1 vs cgroups v2

```
┌──────────────────┬──────────────────────┬──────────────────────┐
│                  │ cgroups v1           │ cgroups v2           │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Hierarchy        │ Multiple hierarchies │ Single unified       │
│                  │ (one per controller) │ hierarchy            │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Controllers      │ cpu, memory, blkio,  │ Same controllers,    │
│                  │ pids, etc. each in   │ all in one tree      │
│                  │ separate trees       │                      │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Delegation       │ Complex, error-prone │ Clean delegation     │
│                  │                      │ model for rootless   │
├──────────────────┼──────────────────────┼──────────────────────┤
│ Pressure info    │ Not available        │ PSI (Pressure Stall  │
│                  │                      │ Information) built-in│
├──────────────────┼──────────────────────┼──────────────────────┤
│ Default on       │ Ubuntu < 21.10       │ Ubuntu >= 21.10      │
│                  │ RHEL 7               │ RHEL 9, Fedora 31+   │
└──────────────────┴──────────────────────┴──────────────────────┘
```

### Check Which Version You're Running

```bash
# Method 1: Check the filesystem
$ stat -fc %T /sys/fs/cgroup/
# cgroup2fs  → cgroups v2
# tmpfs      → cgroups v1

# Method 2: Check mount
$ mount | grep cgroup
# cgroup2 on /sys/fs/cgroup type cgroup2 (rw,nosuid,nodev,noexec)

# Method 3: Docker info
$ docker info | grep -i cgroup
# Cgroup Driver: systemd
# Cgroup Version: 2
```

### How Docker Uses cgroups

```bash
# Run a container with resource limits
$ docker run -d --name cg-demo \
    --cpus=1.5 \
    --memory=512m \
    --memory-swap=1g \
    --pids-limit=100 \
    nginx

# Find the container's cgroup path
$ CGPATH=$(docker inspect --format '{{.HostConfig.CgroupParent}}' cg-demo)
$ CID=$(docker inspect --format '{{.Id}}' cg-demo)

# On cgroups v2, Docker containers live under:
# /sys/fs/cgroup/system.slice/docker-<container-id>.scope/

# View CPU limit
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/cpu.max
# 150000 100000
# Meaning: 150000 microseconds per 100000 microsecond period = 1.5 CPUs

# View memory limit
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.max
# 536870912  (512 * 1024 * 1024 = 536870912 bytes = 512 MB)

# View current memory usage
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.current
# 12345678  (current usage in bytes)

# View PID limit
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/pids.max
# 100

# View current PID count
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/pids.current
# 5
```

### cgroups v2 Controller Files Reference

```
┌──────────────────────┬───────────────────────────────────────────┐
│ File                 │ Purpose                                   │
├──────────────────────┼───────────────────────────────────────────┤
│ cpu.max              │ CPU bandwidth limit (quota period)        │
│ cpu.weight           │ CPU shares (1-10000, default 100)         │
│ cpu.stat             │ CPU usage statistics                      │
│ cpu.pressure         │ CPU pressure stall information            │
├──────────────────────┼───────────────────────────────────────────┤
│ memory.max           │ Hard memory limit (OOM kill if exceeded)  │
│ memory.high          │ Soft limit (throttle, not kill)           │
│ memory.current       │ Current memory usage                      │
│ memory.swap.max      │ Swap limit                                │
│ memory.pressure      │ Memory pressure stall information         │
│ memory.oom.group     │ Kill all processes in cgroup on OOM       │
├──────────────────────┼───────────────────────────────────────────┤
│ io.max               │ Block I/O bandwidth limit                 │
│ io.weight            │ Block I/O weight (1-10000)                │
│ io.stat              │ I/O statistics per device                 │
│ io.pressure          │ I/O pressure stall information            │
├──────────────────────┼───────────────────────────────────────────┤
│ pids.max             │ Maximum number of processes               │
│ pids.current         │ Current number of processes               │
└──────────────────────┴───────────────────────────────────────────┘
```

### Real-World: Preventing Fork Bombs

```bash
# A fork bomb can crash a host by creating infinite processes.
# Without PID limits, a container can exhaust the host's PID space.

# Protect against fork bombs:
$ docker run -d --pids-limit=50 --name safe-container alpine sleep 3600

# Test: Try to create too many processes inside the container
$ docker exec safe-container sh -c '
  for i in $(seq 1 100); do
    sleep 3600 &
  done 2>&1 | tail -5
'
# sh: can't fork: Resource temporarily unavailable
# The kernel blocks process creation after 50 PIDs

# Without --pids-limit, a malicious container could run:
#   :(){ :|:& };:
# This would exhaust the host's PID space and crash everything.
```

---

## 25.8 Union Filesystems and OverlayFS Internals

OverlayFS is the filesystem that makes Docker's layered image model work.
It merges multiple directories into a single unified view.

### How OverlayFS Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTAINER VIEW (merged)                      │
│                                                                 │
│  /app/server.js    ← from upperdir (container wrote this)      │
│  /etc/nginx.conf   ← from lowerdir (image layer 3)             │
│  /usr/bin/nginx    ← from lowerdir (image layer 2)             │
│  /bin/sh           ← from lowerdir (image layer 1 — base)      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  upperdir (read-write)     ← container's writable layer        │
│    /app/server.js          ← new file created by container     │
│    /etc/.wh.resolv.conf    ← whiteout = file deleted           │
│                                                                 │
│  lowerdir (read-only)      ← image layers (stacked)            │
│    layer3: /etc/nginx.conf                                      │
│    layer2: /usr/bin/nginx                                       │
│    layer1: /bin/sh, /lib/...                                    │
│                                                                 │
│  workdir                   ← scratch space for atomic ops      │
│    (used internally by the kernel during copy-up)               │
│                                                                 │
│  merged                    ← the unified view the container    │
│                              sees as its root filesystem        │
└─────────────────────────────────────────────────────────────────┘
```

### Copy-Up Operation

```
# When a container modifies a file from a lower (image) layer:
#
# 1. The kernel copies the ENTIRE file from lowerdir to upperdir
#    (this is the "copy-up" or "copy-on-write" operation)
# 2. The modification is applied to the copy in upperdir
# 3. The merged view now shows the modified version from upperdir
#
# Important performance implications:
#   - First write to a large file is slow (full copy)
#   - Subsequent writes are fast (already in upperdir)
#   - This is why you should use volumes for write-heavy workloads
#     (databases, logs) — volumes bypass OverlayFS entirely
```

### Whiteout Files and Opaque Directories

```bash
# When a container deletes a file from a lower layer, OverlayFS
# cannot actually remove it (lower layers are read-only).
# Instead, it creates a "whiteout" file in the upperdir.

# Example: Delete a file from the base image
$ docker run --name wo-demo alpine rm /etc/hostname
$ docker diff wo-demo
# D /etc/hostname   ← "D" means deleted

# Inspect the upperdir on the host
$ UPPER=$(docker inspect --format '{{.GraphDriver.Data.UpperDir}}' wo-demo)
$ ls -la $UPPER/etc/
# c--------- .wh.hostname   ← character device with 0/0 major/minor
# This whiteout file tells OverlayFS to hide /etc/hostname

# Opaque directories: When a container replaces an entire directory
# OverlayFS creates a .wh..wh..opq file in the new directory
# This hides ALL files from lower layers in that directory
```

### Inspecting OverlayFS Mounts for a Container

```bash
$ docker run -d --name overlay-demo nginx

# View the overlay mount
$ docker inspect --format '{{.GraphDriver.Data.MergedDir}}' overlay-demo
# /var/lib/docker/overlay2/<id>/merged

$ docker inspect --format '{{.GraphDriver.Data.UpperDir}}' overlay-demo
# /var/lib/docker/overlay2/<id>/diff

$ docker inspect --format '{{.GraphDriver.Data.LowerDir}}' overlay-demo
# /var/lib/docker/overlay2/<id1>/diff:/var/lib/docker/overlay2/<id2>/diff:...
# Multiple lower dirs separated by colons — one per image layer

# View the actual kernel mount
$ mount | grep overlay | grep $(docker inspect --format '{{.Id}}' overlay-demo | cut -c1-12)
# overlay on /var/lib/docker/overlay2/.../merged type overlay
#   (rw,lowerdir=...,upperdir=...,workdir=...)

# List files in the writable layer (changes made by the container)
$ sudo ls -la $(docker inspect --format '{{.GraphDriver.Data.UpperDir}}' overlay-demo)
```

### Layer Sharing in Practice

```bash
# Pull two images that share a base layer
$ docker pull nginx:1.25
$ docker pull nginx:1.24

# Both share the Debian base layers
$ docker inspect nginx:1.25 --format '{{range .RootFS.Layers}}{{.}}
{{end}}' > /tmp/layers-125.txt

$ docker inspect nginx:1.24 --format '{{range .RootFS.Layers}}{{.}}
{{end}}' > /tmp/layers-124.txt

$ comm -12 <(sort /tmp/layers-125.txt) <(sort /tmp/layers-124.txt)
# Shows shared layer digests — these are stored only ONCE on disk

# Check actual disk usage
$ docker system df -v | grep nginx
# nginx  1.25  150MB  (shared: 120MB, unique: 30MB)
# nginx  1.24  148MB  (shared: 120MB, unique: 28MB)
# Total disk: 120 + 30 + 28 = 178MB, not 298MB
```

---

## 25.9 Seccomp, Capabilities, and LSMs at the Kernel Level

These three mechanisms form the defense-in-depth security model
that Docker applies to every container by default.

### Linux Capabilities — Fine-Grained Root Powers

```
# Traditional Unix: a process is either root (all powers) or not.
# Capabilities split root's powers into ~40 individual permissions.
#
# Docker's default capability set (what containers GET):
#   CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FSETID, CAP_FOWNER,
#   CAP_MKNOD, CAP_NET_RAW, CAP_SETGID, CAP_SETUID,
#   CAP_SETFCAP, CAP_SETPCAP, CAP_NET_BIND_SERVICE,
#   CAP_SYS_CHROOT, CAP_KILL, CAP_AUDIT_WRITE
#
# Capabilities Docker DROPS (containers do NOT get):
#   CAP_SYS_ADMIN, CAP_NET_ADMIN, CAP_SYS_PTRACE,
#   CAP_SYS_MODULE, CAP_SYS_RAWIO, CAP_SYS_TIME, ...
```

```bash
# View capabilities of a running container
$ docker run --rm alpine cat /proc/1/status | grep Cap
# CapPrm: 00000000a80425fb
# CapEff: 00000000a80425fb

# Decode the hex bitmask
$ capsh --decode=00000000a80425fb

# Drop all capabilities except what's needed
$ docker run --rm --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx

# Add a specific capability
$ docker run --rm --cap-add=NET_ADMIN alpine ip link add dummy0 type dummy
```

### Seccomp — Syscall Filtering

```bash
# Docker's default profile blocks ~44 dangerous syscalls:
#   reboot, mount, umount, swapon, swapoff,
#   init_module, delete_module, settimeofday, bpf, ...

# View Docker's seccomp status
$ docker info --format '{{.SecurityOptions}}'
# [name=seccomp,profile=builtin]

# Run with no seccomp (debugging only)
$ docker run --rm --security-opt seccomp=unconfined alpine

# Run with a custom seccomp profile
$ docker run --rm --security-opt seccomp=custom-profile.json alpine
```

### Linux Security Modules (AppArmor / SELinux)

```bash
# AppArmor (Ubuntu/Debian default)
$ docker inspect --format '{{.AppArmorProfile}}' <container>
# docker-default

# SELinux (RHEL/CentOS/Fedora)
# Docker applies labels: system_u:system_r:container_t:s0:c123,c456

# Disable for debugging
$ docker run --rm --security-opt apparmor=unconfined alpine
$ docker run --rm --security-opt label=disable alpine
```

### Defense-in-Depth Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Namespaces     — isolate what container can SEE      │
│  Layer 2: Cgroups        — limit what container can USE        │
│  Layer 3: Capabilities   — limit what container can DO         │
│  Layer 4: Seccomp        — limit which SYSCALLS are allowed    │
│  Layer 5: AppArmor/SELinux — mandatory access control          │
│  Layer 6: Read-only rootfs + no-new-privileges                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 25.10 Walking Through docker run — Syscall by Syscall

What happens when you run `docker run -d nginx`:

```
Step 1: docker CLI
  Parses flags → POST /containers/create → POST /containers/<id>/start

Step 2: dockerd
  Validates request → allocates IP → creates veth pair →
  sets iptables rules → calls containerd via gRPC

Step 3: containerd
  Creates OverlayFS snapshot → generates OCI bundle →
  spawns containerd-shim-runc-v2

Step 4: shim
  Opens stdio pipes → forks runc with bundle path

Step 5: runc
  clone(CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|...)
  mount(/proc, /sys, /dev) → pivot_root() →
  cgroup writes → seccomp filter → drop capabilities →
  execve(nginx) → runc exits

Step 6: Container running
  nginx is PID 1 inside container
  shim is parent on host
  dockerd/containerd can restart without affecting container
```

---

## 25.11 Building a Container from Scratch (No Docker)

### Create Root Filesystem

```bash
$ mkdir -p /tmp/mycontainer/rootfs && cd /tmp/mycontainer
$ curl -Lo alpine.tar.gz \
    https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-minirootfs-3.19.0-x86_64.tar.gz
$ tar -xzf alpine.tar.gz -C rootfs
```

### Create Namespaces with unshare

```bash
$ sudo unshare --mount --uts --ipc --pid --fork \
    --mount-proc=rootfs/proc chroot rootfs /bin/sh

/ # hostname my-container   # UTS namespace isolation
/ # ps aux                  # PID 1! PID namespace isolation
/ # exit
```

### Add cgroup Limits

```bash
$ sudo mkdir -p /sys/fs/cgroup/mycontainer
$ echo 67108864 | sudo tee /sys/fs/cgroup/mycontainer/memory.max
$ echo "50000 100000" | sudo tee /sys/fs/cgroup/mycontainer/cpu.max
$ echo 20 | sudo tee /sys/fs/cgroup/mycontainer/pids.max
```

### Add Network Namespace

```bash
$ sudo ip netns add mycontainer
$ sudo ip link add veth-host type veth peer name veth-ct
$ sudo ip link set veth-ct netns mycontainer
$ sudo ip addr add 10.200.0.1/24 dev veth-host && sudo ip link set veth-host up
$ sudo ip netns exec mycontainer ip addr add 10.200.0.2/24 dev veth-ct
$ sudo ip netns exec mycontainer ip link set veth-ct up
$ sudo ip netns exec mycontainer ping -c 1 10.200.0.1
# 64 bytes from 10.200.0.1

# Clean up
$ sudo ip netns delete mycontainer && sudo ip link delete veth-host
$ sudo rmdir /sys/fs/cgroup/mycontainer
```

### Manual Container vs Docker

```
┌──────────────────────┬──────────────┬──────────────┐
│ Feature              │ Manual       │ Docker       │
├──────────────────────┼──────────────┼──────────────┤
│ PID namespace        │ ✓ unshare    │ ✓ clone      │
│ Network namespace    │ ✓ ip netns   │ ✓ clone      │
│ Cgroup limits        │ ✓ cgexec     │ ✓ cgroup fs  │
│ Root filesystem      │ ✓ chroot     │ ✓ pivot_root │
│ Layered filesystem   │ ✗            │ ✓ OverlayFS  │
│ Image distribution   │ ✗            │ ✓ OCI images │
│ Seccomp/Capabilities │ ✗            │ ✓ default    │
│ Shim (daemon-free)   │ ✗            │ ✓ shim       │
└──────────────────────┴──────────────┴──────────────┘
```

---

## 25.12 Common Errors and Troubleshooting

### Error 1: "OCI runtime create failed"

```bash
# Binary in CMD/ENTRYPOINT doesn't exist
$ docker run alpine /nonexistent
# Fix: docker run alpine ls /

# Seccomp blocking a syscall
$ docker run --security-opt seccomp=unconfined <image>

# AppArmor denying access
$ docker run --security-opt apparmor=unconfined <image>
```

### Error 2: "failed to create shim task"

```bash
$ sudo systemctl status containerd   # Is containerd running?
$ which runc && runc --version        # Is runc installed?
$ docker info | grep "Cgroup Driver"  # Driver mismatch?
```

### Error 3: Container OOM Killed (exit code 137)

```bash
$ docker inspect --format '{{.State.OOMKilled}}' <container>
$ dmesg | grep -i "oom\|killed"
# Fix: docker run -m 1g --memory-swap 2g <image>
```

### Error 4: "no space left on device"

```bash
$ docker system df && docker system prune -a --volumes
# Or move data root: {"data-root": "/mnt/large-disk/docker"}
```

---

## Module 25 Summary

- Docker's runtime stack: CLI → dockerd → containerd → shim → runc
- The **shim** keeps containers alive across daemon restarts
- **OCI specs** define portable standards for images and runtimes
- **containerd** manages container lifecycle, image storage, and snapshots
- **runc** sets up namespaces, cgroups, mounts, seccomp, and execs the entrypoint
- Alternative runtimes (crun, gVisor, Kata) replace runc for different isolation
- Linux provides **8 namespace types** for isolation
- **cgroups v2** provides unified resource control in a single hierarchy
- **OverlayFS** merges read-only image layers with a read-write container layer
- Security is defense-in-depth: namespaces → cgroups → capabilities → seccomp → LSMs
- `docker run` triggers: API → snapshot → shim → runc clone/mount/pivot_root/execve
- Containers are Linux processes with kernel-level isolation — no hypervisor

---

**Previous Module: [Module 24 - Kubernetes Storage and Networking](module-24-kubernetes-storage-networking.md)**

**Next Module: [Module 26 - BuildKit and Advanced Build Patterns](module-26-buildkit-advanced-builds.md)**
