# Module 1: Docker Fundamentals - What, Why, and Architecture

---

## 1.1 What is Docker?

Docker is a **platform for developing, shipping, and running applications inside containers**. A container is a lightweight, standalone, executable package that includes everything needed to run a piece of software: code, runtime, system tools, libraries, and settings.

### Analogy: The Shipping Container

Before standardized shipping containers, goods were loaded individually onto ships — fragile items broke, things got mixed up, and loading took days.

Shipping containers solved this: **pack anything inside a standard box**, and it works on any ship, truck, or train.

Docker does the same for software:

```
Traditional Deployment:
  Developer's Machine  →  "It works on my machine!" 😤
  Testing Server       →  Different OS, missing library
  Production Server    →  Different config, wrong version

Docker Deployment:
  Developer's Machine  →  Container runs perfectly ✅
  Testing Server       →  Same container runs perfectly ✅
  Production Server    →  Same container runs perfectly ✅
```

---

## 1.2 Why Docker? (Problems Docker Solves)

### The "Hotel + Kitchen" Analogy — Understanding Dependency Conflicts

Imagine a hotel with many rooms but only **one shared kitchen**.

```
┌─────────────────────────────────────────────────────────────┐
│                        HOTEL                                 │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Room 101 │  │ Room 102 │  │ Room 103 │  │ Room 104 │   │
│  │ (App A)  │  │ (App B)  │  │ (App C)  │  │ (App D)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────┬───────┴──────────────┘          │
│                             │                                 │
│                    ┌────────▼────────┐                        │
│                    │  SHARED KITCHEN  │                        │
│                    │  (Shared Libs,   │                        │
│                    │   Runtime, OS)   │                        │
│                    └─────────────────┘                        │
│                                                              │
│  Problem: Room 101 wants the oven at 200°C                   │
│           Room 102 wants the oven at 350°C                   │
│           They can't both use the same oven at the same time │
└─────────────────────────────────────────────────────────────┘
```

**Hotel rooms** = separate spaces where each app can do its own thing.
**Shared kitchen** = shared dependencies, libraries, and runtimes on a single server.
**Problem**: Two apps can't peacefully share the same "kitchen" (runtime/libs).

#### Technical Translation

One server runs multiple applications:

```
┌─────────────────────────────────────────────────┐
│              SINGLE SERVER                       │
│                                                  │
│  App A needs: Java 1.7 (JDK 7)                 │
│  App B needs: Java 1.8 (JDK 8)                 │
│                                                  │
│  What happens when you install both?             │
│                                                  │
│  ❌ PATH conflicts — which 'java' binary runs?  │
│  ❌ Default JVM confusion                        │
│  ❌ Shared library incompatibilities             │
│  ❌ Environment variable collisions              │
│  ❌ One app's update breaks the other            │
└─────────────────────────────────────────────────┘
```

**Real-world example — Java version conflict:**

```bash
# Server has Java 8 installed globally
$ java -version
java version "1.8.0_381"

# App A requires Java 7 — you install it alongside
$ sudo apt install openjdk-7-jdk

# Now which java runs by default?
$ java -version
# Could be 7 or 8 depending on PATH order and alternatives config

# You try to fix it with update-alternatives:
$ sudo update-alternatives --config java
There are 2 choices for the alternative java:

  Selection    Path                                     Priority
------------------------------------------------------------
  0            /usr/lib/jvm/java-8-openjdk/bin/java      1081
  1            /usr/lib/jvm/java-7-openjdk/bin/java      1071
* 2            /usr/lib/jvm/java-8-openjdk/bin/java      1081

# You switch to Java 7 for App A → App B breaks
# You switch to Java 8 for App B → App A breaks
# Result: You need ANOTHER server just to isolate dependencies
```

**The cost of this approach:**

```
Without Containers:
  App A conflict with App B
       │
       ▼
  Provision another server/VM
       │
       ▼
  ┌──────────────────────────────────┐
  │ Extra costs:                      │
  │  • Server hardware/cloud cost    │
  │  • OS licensing                  │
  │  • Maintenance overhead          │
  │  • Patching two servers          │
  │  • Monitoring two servers        │
  │  • Backup for two servers        │
  └──────────────────────────────────┘

With Containers:
  App A in Container 1 (Java 7)
  App B in Container 2 (Java 8)
  Both on the SAME server, fully isolated
       │
       ▼
  ┌──────────────────────────────────┐
  │ Savings:                          │
  │  • One server                    │
  │  • One OS to patch               │
  │  • No dependency conflicts       │
  │  • Each app has its own runtime  │
  └──────────────────────────────────┘
```

---

### Problem 1: "It Works on My Machine" (Dev vs QA Firefighting)

This is the most common problem in software development. The same code behaves differently across environments.

```
Developer's Machine              QA/Production Server
┌─────────────────────┐         ┌─────────────────────┐
│ Ubuntu 22.04        │         │ Ubuntu 20.04        │  ← Different OS version
│ Python 3.11.4       │         │ Python 3.8.10       │  ← Different runtime
│ libssl 3.0          │         │ libssl 1.1          │  ← Different library
│ gcc 12.2            │         │ gcc 9.4             │  ← Different compiler
│ pip packages v2023  │         │ pip packages v2021  │  ← Different deps
│                     │         │                     │
│ App runs perfectly  │         │ App CRASHES         │
│        ✅           │         │        ❌            │
└─────────────────────┘         └─────────────────────┘

Developer says: "It works on MY machine!"
QA says: "Well, it doesn't work on MINE!"
```

**Why does this happen?**

```
Root causes of environment inconsistency:

1. OS version differences
   Dev: Ubuntu 22.04 (newer glibc, newer kernel)
   Prod: Ubuntu 20.04 (older glibc, older kernel)

2. Missing libraries
   Dev: Has libmagick installed (for image processing)
   Prod: libmagick not installed → ImportError at runtime

3. Different configurations
   Dev: DEBUG=true, DATABASE_URL=localhost
   Prod: DEBUG=false, DATABASE_URL=prod-db.internal

4. Different runtime versions
   Dev: Node.js 20.10.0
   Prod: Node.js 18.17.0 → syntax errors on newer features

5. Different dependency versions
   Dev: pip install requests → gets 2.31.0
   Prod: pip install requests → gets 2.28.0 (cached/pinned)
```

**The real problem is NOT the code — it's environment consistency.**

**The goal:** Build an environment once, and run it the same way on:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Dev Laptop  │    │  QA Server   │    │   Staging    │    │  Production  │
│              │    │              │    │              │    │              │
│  Container   │ == │  Container   │ == │  Container   │ == │  Container   │
│  (same image)│    │  (same image)│    │  (same image)│    │  (same image)│
│      ✅      │    │      ✅      │    │      ✅      │    │      ✅      │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

Same image → Same OS → Same libraries → Same runtime → Same behavior
```

**Real-world example — Python app failing in QA:**

```bash
# Developer's machine (works fine)
$ python3 --version
Python 3.11.4

$ python3 app.py
 * Running on http://127.0.0.1:5000
 * Serving Flask app 'app'

# QA server (crashes)
$ python3 --version
Python 3.8.10

$ python3 app.py
Traceback (most recent call last):
  File "app.py", line 5, in <module>
    match command:
          ^^^^^^^
SyntaxError: invalid syntax
# Python 3.8 doesn't support match/case (added in 3.10)

# With Docker — BOTH environments run the exact same thing:
$ docker run -d --name myapp -p 5000:5000 myapp:1.0
# Uses Python 3.11 inside the container regardless of host Python version
# Works identically on dev laptop, QA server, staging, and production
```

---

### Problem 2: Dependency Conflicts

```
Scenario: App A needs Node.js 16, App B needs Node.js 20.
Both run on the same server.

Without Docker:
  - Use nvm or similar hacks
  - Risk version conflicts
  - Complex setup scripts

With Docker:
  - App A runs in a container with Node.js 16
  - App B runs in a container with Node.js 20
  - Both run simultaneously, completely isolated
```

---

### Problem 3: CI/CD Pressure (Speed Matters)

In modern CI/CD pipelines, you need:

```
CI/CD Requirements:
┌─────────────────────────────────────────────────────┐
│                                                      │
│  1. Fast setup        → Environment ready in seconds │
│  2. Repeatable envs   → Same result every time       │
│  3. Easy scaling      → Run 5 parallel test suites   │
│  4. Clean isolation   → Tests don't interfere        │
│  5. Quick teardown    → Clean up instantly            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Traditional VMs vs Containers in CI/CD:**

```
┌──────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Comparison                   │
│                                                               │
│  Using VMs:                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Boot VM  │→ │ Install │→ │  Run    │→ │Teardown │        │
│  │ 2-5 min  │  │ deps    │  │ tests   │  │ 1-2 min │        │
│  │          │  │ 3-10min │  │ 5 min   │  │         │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│  Total: 11-22 minutes per pipeline run                       │
│  Cost: High (VM resources reserved even when idle)           │
│                                                               │
│  Using Containers:                                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Start   │→ │  Deps   │→ │  Run    │→ │Teardown │        │
│  │container│  │ already │  │ tests   │  │ instant │        │
│  │ 1-2 sec │  │ in image│  │ 5 min   │  │ <1 sec  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│  Total: ~5 minutes per pipeline run                          │
│  Cost: Low (shared resources, instant cleanup)               │
│                                                               │
│  Scaling parallel tests:                                      │
│  VM: Spin up 5 VMs = 5 × 2GB RAM = 10GB + 5 × boot time    │
│  Container: Spin up 5 containers = 5 × 50MB = 250MB + 2sec  │
└──────────────────────────────────────────────────────────────┘
```

**Example — Running parallel test suites with containers:**

```bash
# Spin up 5 identical test environments in seconds
$ docker run -d --name test-1 myapp-test:latest pytest tests/unit/
$ docker run -d --name test-2 myapp-test:latest pytest tests/integration/
$ docker run -d --name test-3 myapp-test:latest pytest tests/api/
$ docker run -d --name test-4 myapp-test:latest pytest tests/e2e/
$ docker run -d --name test-5 myapp-test:latest pytest tests/performance/

# All 5 start within seconds, run in parallel, fully isolated
# When done, clean up instantly:
$ docker rm -f test-1 test-2 test-3 test-4 test-5
```

---

### Problem 4: Environment Setup Takes Days

```
Scenario: New developer joins the team. Project needs:
  - PostgreSQL 15
  - Redis 7
  - Node.js 20
  - Python 3.11
  - Elasticsearch 8
  - Specific environment variables

Without Docker:
  - 2-3 days of setup
  - "Follow the wiki" (which is outdated)
  - Different results on Mac vs Linux vs Windows

With Docker:
  - Run: docker compose up
  - Everything starts in 30 seconds
  - Identical environment for everyone
```

### Problem 5: Resource Efficiency

```
Virtual Machines vs Containers:

┌─────────────────────────────────────────────────┐
│              Virtual Machines                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  App A   │ │  App B   │ │  App C   │        │
│  │  Bins/   │ │  Bins/   │ │  Bins/   │        │
│  │  Libs    │ │  Libs    │ │  Libs    │        │
│  │ Guest OS │ │ Guest OS │ │ Guest OS │        │
│  │ (1-2 GB) │ │ (1-2 GB) │ │ (1-2 GB) │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│           Hypervisor (VMware, VirtualBox)        │
│                   Host OS                        │
│                 Hardware                         │
└─────────────────────────────────────────────────┘
Total overhead: 3-6 GB just for OS copies
Boot time: Minutes

┌─────────────────────────────────────────────────┐
│                Containers                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  App A   │ │  App B   │ │  App C   │        │
│  │  Bins/   │ │  Bins/   │ │  Bins/   │        │
│  │  Libs    │ │  Libs    │ │  Libs    │        │
│  └──────────┘ └──────────┘ └──────────┘        │
│              Docker Engine                       │
│                 Host OS                          │
│                Hardware                          │
└─────────────────────────────────────────────────┘
Total overhead: MBs (shared kernel)
Boot time: Seconds
```

---

## 1.3 Docker Architecture

Docker uses a **client-server architecture**.

```
┌─────────────────────────────────────────────────────────────┐
│                     DOCKER ARCHITECTURE                      │
│                                                              │
│  ┌──────────────┐         ┌──────────────────────────────┐  │
│  │ Docker Client │ ──────▶│       Docker Daemon          │  │
│  │  (docker CLI) │  REST  │       (dockerd)              │  │
│  │               │  API   │                              │  │
│  │ docker run    │        │  ┌─────────┐ ┌──────────┐   │  │
│  │ docker build  │        │  │ Images  │ │Containers│   │  │
│  │ docker pull   │        │  └─────────┘ └──────────┘   │  │
│  │ docker push   │        │  ┌─────────┐ ┌──────────┐   │  │
│  └──────────────┘         │  │Networks │ │ Volumes  │   │  │
│                           │  └─────────┘ └──────────┘   │  │
│                           └──────────┬───────────────────┘  │
│                                      │                       │
│                           ┌──────────▼───────────────────┐  │
│                           │     Docker Registry          │  │
│                           │     (Docker Hub, ECR,        │  │
│                           │      GCR, ACR)               │  │
│                           └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components Explained

#### 1. Docker Client (`docker`)
The command-line tool you interact with. It sends commands to the Docker daemon.

```bash
# Every command you type goes through the Docker client
docker run nginx        # Client sends "run nginx" to daemon
docker ps               # Client asks daemon "list containers"
docker build .          # Client sends build context to daemon
```

#### 2. Docker Daemon (`dockerd`)
The background service that does the actual work — building images, running containers, managing networks and volumes.

```bash
# Check if the daemon is running
systemctl status docker

# Output:
# ● docker.service - Docker Application Container Engine
#    Loaded: loaded
#    Active: active (running)
```

#### 3. Docker Registry
A storage and distribution system for Docker images. Docker Hub is the default public registry.

```bash
# Pull an image from Docker Hub (default registry)
docker pull nginx

# Pull from a private registry (e.g., AWS ECR)
docker pull 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
```

#### 4. Docker Objects

**Images**: Read-only templates used to create containers. Like a class in OOP.

**Containers**: Running instances of images. Like an object created from a class.

**Volumes**: Persistent data storage that survives container restarts.

**Networks**: Communication channels between containers.

```
Image vs Container (OOP Analogy):

class WebServer:          # ← This is like a Docker IMAGE
    def __init__(self):
        self.port = 80
        self.config = "nginx.conf"

server1 = WebServer()     # ← This is like a CONTAINER (instance 1)
server2 = WebServer()     # ← This is like a CONTAINER (instance 2)
server3 = WebServer()     # ← This is like a CONTAINER (instance 3)

# One image, many containers
```

#### 5. Docker Host

The **Docker Host** is any machine where Docker Engine runs. It can be:

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER HOST                               │
│                                                              │
│  A Docker Host can be:                                      │
│                                                              │
│  • A bare metal server (physical machine + Linux)           │
│  • A virtual machine (EC2, Azure VM, GCP Compute)           │
│  • A cloud VM with Docker pre-installed                     │
│  • Your laptop running Docker Desktop                       │
│                                                              │
│  The host provides:                                         │
│  • The Linux kernel (shared by all containers)              │
│  • CPU, RAM, disk, network resources                        │
│  • The Docker daemon process                                │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Check your Docker host information
$ docker info | grep -E "Operating System|Kernel|Architecture|CPUs|Total Memory"

Operating System: Ubuntu 22.04.3 LTS
Kernel Version: 5.15.0-91-generic
Architecture: x86_64
CPUs: 4
Total Memory: 7.773GiB
```

#### 6. Docker Daemon vs Client — Detailed View

The daemon and client are separate processes that communicate via an API:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  DOCKER CLIENT (docker CLI)          DOCKER DAEMON (dockerd)│
│  ─────────────────────────           ──────────────────────  │
│                                                              │
│  • Your terminal commands            • Background service    │
│  • Sends requests via API            • Does the heavy work   │
│  • Can be on a different             • Manages containers,   │
│    machine than the daemon             images, networks,     │
│  • Lightweight                         volumes               │
│  • Stateless                         • Listens on Unix       │
│                                        socket or TCP         │
│                                                              │
│  Communication path:                                        │
│                                                              │
│  docker run nginx                                           │
│       │                                                      │
│       ▼                                                      │
│  Docker Client                                              │
│       │  (sends REST API request)                           │
│       ▼                                                      │
│  Unix Socket: /var/run/docker.sock                          │
│       │  (or TCP: tcp://host:2376)                          │
│       ▼                                                      │
│  Docker Daemon (dockerd)                                    │
│       │                                                      │
│       ▼                                                      │
│  containerd → runc → Linux Kernel                           │
│       │                                                      │
│       ▼                                                      │
│  Container process starts                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# The daemon listens on a Unix socket by default
$ ls -la /var/run/docker.sock
srw-rw---- 1 root docker 0 Jan 15 10:00 /var/run/docker.sock

# Check if the daemon is running
$ systemctl status docker

● docker.service - Docker Application Container Engine
     Loaded: loaded (/lib/systemd/system/docker.service; enabled)
     Active: active (running) since Mon 2024-01-15 10:00:00 UTC; 2h ago
   Main PID: 1234 (dockerd)
      Tasks: 25
     Memory: 120.5M
        CPU: 15.234s
     CGroup: /system.slice/docker.service
             └─1234 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock

# The client can also talk to a REMOTE daemon
$ docker -H tcp://remote-server:2376 ps
# This runs 'docker ps' on a remote Docker host

# Check which context (daemon) the client is talking to
$ docker context ls
NAME        DESCRIPTION                               DOCKER ENDPOINT
default *   Current DOCKER_HOST based configuration   unix:///var/run/docker.sock
```

---

## 1.4 Docker Image Layers

Docker images are built in **layers**. Each instruction in a Dockerfile creates a new layer.

```
┌─────────────────────────────────┐
│  Layer 5: COPY app.js /app/     │  ← Your application code
├─────────────────────────────────┤
│  Layer 4: RUN npm install       │  ← Dependencies
├─────────────────────────────────┤
│  Layer 3: COPY package.json     │  ← Package file
├─────────────────────────────────┤
│  Layer 2: RUN apt-get update    │  ← System packages
├─────────────────────────────────┤
│  Layer 1: Ubuntu 22.04          │  ← Base OS
└─────────────────────────────────┘

Key insight: Layers are CACHED.
If Layer 1-3 haven't changed, Docker reuses them.
Only Layer 4-5 get rebuilt. This makes builds FAST.
```

---

## 1.5 What Exactly is a Container? (Technical View)

A container is **NOT a virtual machine**. A container is an **isolated process** (or group of processes) created using OS-level features. It feels like a mini-machine, but it is really a controlled and isolated process running on the host kernel.

```
┌─────────────────────────────────────────────────────────────┐
│                  WHAT A CONTAINER REALLY IS                   │
│                                                              │
│  A container = A regular Linux process with:                 │
│                                                              │
│  1. Namespaces  → Isolation (what the process can SEE)      │
│  2. Cgroups     → Resource control (what it can USE)        │
│  3. OverlayFS   → Layered filesystem (what it can ACCESS)   │
│                                                              │
│  It is NOT:                                                  │
│  ❌ A virtual machine                                        │
│  ❌ A separate OS                                            │
│  ❌ Running its own kernel                                   │
│                                                              │
│  It IS:                                                      │
│  ✅ A process with isolation boundaries                      │
│  ✅ Sharing the host kernel                                  │
│  ✅ Packaged with its own filesystem/libraries               │
└─────────────────────────────────────────────────────────────┘
```

### How Docker Creates a Container (Under the Hood)

```
docker run nginx
       │
       ▼
docker CLI  ──→  Docker Daemon (dockerd)  ──→  containerd  ──→  runc
                        │                                         │
                        │                                         ▼
                        │                              Linux Kernel calls:
                        │                              • clone() with namespace flags
                        │                              • Set up cgroups
                        │                              • Mount overlay filesystem
                        │                              • Execute container process
                        │
                        └── manages images, containers, networks, volumes
```

### Namespaces (Isolation — What the Container Can SEE)

Each container gets its own isolated view of system resources:

```
┌──────────────────────────────────────────────────────────────────┐
│ Namespace    │ What it isolates              │ Example            │
├──────────────┼──────────────────────────────┼────────────────────┤
│ PID          │ Process IDs                   │ Container sees its │
│              │                               │ own PID 1, not     │
│              │                               │ host's 500 procs   │
├──────────────┼──────────────────────────────┼────────────────────┤
│ NET          │ Network stack                 │ Container has its  │
│              │ (interfaces, IPs, ports,      │ own eth0, IP addr, │
│              │  routing tables)              │ port space         │
├──────────────┼──────────────────────────────┼────────────────────┤
│ MNT          │ Filesystem mount points       │ Container sees its │
│              │                               │ own / (root fs),   │
│              │                               │ not host's /       │
├──────────────┼──────────────────────────────┼────────────────────┤
│ USER         │ User and group IDs            │ Root (UID 0) in    │
│              │                               │ container can map  │
│              │                               │ to non-root on host│
├──────────────┼──────────────────────────────┼────────────────────┤
│ UTS          │ Hostname and domain name      │ Container has its  │
│              │                               │ own hostname       │
├──────────────┼──────────────────────────────┼────────────────────┤
│ IPC          │ Inter-process communication   │ Shared memory and  │
│              │ (semaphores, message queues)  │ semaphores isolated│
└──────────────┴──────────────────────────────┴────────────────────┘
```

**Example — PID namespace isolation:**

```bash
# On the HOST — you see all processes
$ ps aux | head -5
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 169436 13092 ?        Ss   10:00   0:03 /sbin/init
root         2  0.0  0.0      0     0 ?        S    10:00   0:00 [kthreadd]
root       345  0.1  0.5 723456 45678 ?        Ssl  10:00   0:15 /usr/bin/dockerd
www-data   890  0.0  0.1  12345  6789 ?        S    10:05   0:00 nginx: worker

# INSIDE the container — it only sees its own processes
$ docker exec -it web ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1   8860  5432 ?        Ss   10:05   0:00 nginx: master
www-data    29  0.0  0.0   9288  2456 ?        S    10:05   0:00 nginx: worker
www-data    30  0.0  0.0   9288  2456 ?        S    10:05   0:00 nginx: worker

# The container thinks nginx is PID 1 (its init process)
# It cannot see the host's processes at all
```

**Example — NET namespace isolation:**

```bash
# On the HOST
$ ip addr show
1: lo: <LOOPBACK> ...
2: eth0: <BROADCAST> ... inet 192.168.1.100/24 ...
3: docker0: <BROADCAST> ... inet 172.17.0.1/16 ...

# INSIDE the container
$ docker exec -it web ip addr show
1: lo: <LOOPBACK> ... inet 127.0.0.1/8 ...
15: eth0@if16: <BROADCAST> ... inet 172.17.0.2/16 ...

# Container has its own network interface and IP address
# It doesn't see the host's eth0 or other containers' interfaces
```

### Control Groups (cgroups) — Resource Control (What the Container Can USE)

Cgroups limit and control how much CPU, memory, I/O, and other resources a container can consume.

```
┌─────────────────────────────────────────────────────────────┐
│                    CGROUPS RESOURCE CONTROL                   │
│                                                              │
│  Resource     │ What cgroups control                         │
│  ─────────────┼──────────────────────────────────────────── │
│  CPU          │ How much CPU time the container gets         │
│  Memory       │ Maximum RAM the container can use            │
│  I/O          │ Disk read/write bandwidth limits             │
│  PIDs         │ Maximum number of processes                  │
│  Network      │ Network bandwidth (via tc integration)       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Limit a container to 512MB RAM and 1 CPU
$ docker run -d --name limited --memory=512m --cpus=1 nginx

# Verify the limits are applied
$ docker stats limited --no-stream
CONTAINER ID   NAME      CPU %   MEM USAGE / LIMIT   MEM %   NET I/O       BLOCK I/O
a3c1f2d3e4f5   limited   0.00%   2.5MiB / 512MiB     0.49%   1.2kB / 0B    0B / 0B

# What happens when a container exceeds memory limit?
$ docker run -d --name oom-test --memory=50m python:3.12-slim \
    python -c "x = 'A' * (100 * 1024 * 1024)"  # Try to allocate 100MB

$ docker inspect oom-test --format='{{.State.OOMKilled}}'
true
# The container is killed by the OOM (Out Of Memory) killer

# Without limits — a runaway container could consume ALL host resources
# With cgroups, Docker enforces boundaries and protects the host
```

**Key takeaway:**
Containers feel like mini-machines, but they are really controlled + isolated processes sharing the host kernel.

### Union File System (OverlayFS)
```
Container Layer (Read-Write)     ← Changes go here
─────────────────────────────
Image Layer 3 (Read-Only)        ← Shared across containers
Image Layer 2 (Read-Only)        ← Shared across containers
Image Layer 1 (Read-Only)        ← Shared across containers

# 100 containers from the same image share the read-only layers
# Each container only stores its own changes (copy-on-write)
# This is why containers are so lightweight
```

---

## 1.6 Virtualization vs Containers (Core Difference)

### A) Virtual Machines (VMs) — Full Isolation

A VM includes a full guest OS, virtualized hardware, and a hypervisor layer.

```
┌─────────────────────────────────────────────────────────────┐
│                    VIRTUAL MACHINE ARCHITECTURE              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    App A      │  │    App B      │  │    App C      │      │
│  │  + Libraries  │  │  + Libraries  │  │  + Libraries  │      │
│  │  + Binaries   │  │  + Binaries   │  │  + Binaries   │      │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤      │
│  │  Guest OS     │  │  Guest OS     │  │  Guest OS     │      │
│  │  (Full Linux  │  │  (Full Windows│  │  (Full Linux  │      │
│  │   or Windows) │  │   Server)     │  │   Ubuntu)     │      │
│  │  1-2 GB each  │  │  4-8 GB each  │  │  1-2 GB each  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ─────────────────────────────────────────────────────      │
│                    HYPERVISOR                                 │
│           (VMware ESXi, KVM, Hyper-V, VirtualBox)           │
│  ─────────────────────────────────────────────────────      │
│                    HOST OS (optional with Type 1)            │
│  ─────────────────────────────────────────────────────      │
│                    PHYSICAL HARDWARE                         │
└─────────────────────────────────────────────────────────────┘

What a VM includes:
  ✅ Full guest OS kernel (its own Linux/Windows kernel)
  ✅ Virtualized hardware (virtual CPU, RAM, disk, NIC)
  ✅ Hypervisor layer managing resource allocation
  ✅ Complete isolation — each VM is a separate machine

Pros:
  ✅ Strong isolation (separate kernel per VM)
  ✅ Can run different OS kernels (Linux VM on Windows host)
  ✅ Mature technology, well-understood security model

Cons:
  ❌ Heavy — each VM needs 1-8 GB RAM just for the OS
  ❌ Slow to boot — minutes to start
  ❌ Slow to clone/replicate
  ❌ More overhead → higher infrastructure cost
  ❌ Fewer VMs per host (typically 10-20)
```

### B) Containers — Lightweight Process Isolation

A container is a process (or group of processes) with isolation (namespaces) and resource control (cgroups), sharing the host kernel.

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTAINER ARCHITECTURE                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    App A      │  │    App B      │  │    App C      │      │
│  │  + Libraries  │  │  + Libraries  │  │  + Libraries  │      │
│  │  + Binaries   │  │  + Binaries   │  │  + Binaries   │      │
│  │  (user-space  │  │  (user-space  │  │  (user-space  │      │
│  │   files only) │  │   files only) │  │   files only) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ─────────────────────────────────────────────────────      │
│              CONTAINER RUNTIME (Docker Engine)               │
│  ─────────────────────────────────────────────────────      │
│              HOST OS KERNEL (shared by all containers)       │
│  ─────────────────────────────────────────────────────      │
│              PHYSICAL HARDWARE                               │
└─────────────────────────────────────────────────────────────┘

What a container packages:
  ✅ App + dependencies + user-space OS files
  ❌ NOT a full kernel (shares the host kernel)

Pros:
  ✅ Very fast start (seconds, not minutes)
  ✅ Lightweight (MBs, not GBs)
  ✅ Easy to replicate and ship
  ✅ High density (100s of containers per host)
  ✅ Near-native performance (no hypervisor overhead)

Cons:
  ❌ Shared kernel → kernel-level vulnerabilities affect all containers
  ❌ OS-kernel compatibility constraints (see section 1.12)
  ❌ Less isolation than VMs (process-level, not hardware-level)
```

### Architecture Diagrams

**A) Traditional Hosting (No Isolation):**

```
┌─────────────────────────────────────────────────┐
│              PHYSICAL HARDWARE                   │
│  ─────────────────────────────────────────────  │
│              HOST OS                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  App A   │ │  App B   │ │  App C   │       │
│  │ (shared  │ │ (shared  │ │ (shared  │       │
│  │  libs)   │ │  libs)   │ │  libs)   │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│                                                  │
│  ⚠️ All apps share the same libraries           │
│  ⚠️ Dependency conflicts are inevitable         │
│  ⚠️ One app's crash can affect others           │
└─────────────────────────────────────────────────┘
```

**B) VM-Based Hosting:**

```
┌─────────────────────────────────────────────────┐
│              PHYSICAL HARDWARE                   │
│  ─────────────────────────────────────────────  │
│              HYPERVISOR                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  App A   │ │  App B   │ │  App C   │       │
│  │  Libs    │ │  Libs    │ │  Libs    │       │
│  │ Guest OS │ │ Guest OS │ │ Guest OS │       │
│  │ (1-2 GB) │ │ (1-2 GB) │ │ (1-2 GB) │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│                                                  │
│  ✅ Full isolation between VMs                  │
│  ❌ Heavy — 3-6 GB overhead just for OS copies  │
│  ❌ Slow to boot (minutes)                      │
└─────────────────────────────────────────────────┘
```

**C) Container-Based Hosting:**

```
┌─────────────────────────────────────────────────┐
│              PHYSICAL HARDWARE                   │
│  ─────────────────────────────────────────────  │
│              HOST OS (Kernel)                    │
│  ─────────────────────────────────────────────  │
│         CONTAINER RUNTIME (Docker Engine)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  App A   │ │  App B   │ │  App C   │       │
│  │  + Libs  │ │  + Libs  │ │  + Libs  │       │
│  └──────────┘ └──────────┘ └──────────┘       │
│                                                  │
│  ✅ All share host kernel, but isolated          │
│     user-space                                   │
│  ✅ Lightweight (MBs overhead)                  │
│  ✅ Fast to start (seconds)                     │
└─────────────────────────────────────────────────┘
```

**D) Docker Architecture (What Talks to What):**

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  You type commands                                           │
│       │                                                      │
│       ▼                                                      │
│  docker CLI ────REST API────▶ Docker Daemon (dockerd)       │
│                                      │                       │
│                                      ├── manages images      │
│                                      ├── manages containers  │
│                                      ├── manages networks    │
│                                      ├── manages volumes     │
│                                      │                       │
│                                      ▼                       │
│                               containerd                     │
│                                      │                       │
│                                      ▼                       │
│                                    runc                      │
│                                      │                       │
│                                      ▼                       │
│                               Linux Kernel                   │
│                          (namespaces + cgroups)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Comparison Table

```
┌──────────────────┬──────────────────┬──────────────────┐
│ Feature          │ Docker Container │ Virtual Machine  │
├──────────────────┼──────────────────┼──────────────────┤
│ Boot Time        │ Seconds          │ Minutes          │
│ Size             │ MBs              │ GBs              │
│ Performance      │ Near native      │ ~5-20% overhead  │
│ Isolation        │ Process-level    │ Hardware-level   │
│ OS               │ Shares host      │ Full guest OS    │
│                  │ kernel           │                  │
│ Density          │ 100s per host    │ 10s per host     │
│ Portability      │ Very high        │ Medium           │
│ Security         │ Good (shared     │ Better (full     │
│                  │ kernel risk)     │ isolation)       │
│ Use Case         │ Microservices,   │ Different OS,    │
│                  │ CI/CD, dev envs  │ legacy apps      │
│ Kernel           │ Shared with host │ Own kernel       │
│ Resource Usage   │ Only app needs   │ Full OS + app    │
│ Startup Cost     │ ~50-100ms        │ 30-120 seconds   │
│ Image Size       │ 5MB - 1GB        │ 1GB - 20GB       │
│ Max per Host     │ 100s - 1000s     │ 10s - 50s        │
└──────────────────┴──────────────────┴──────────────────┘
```

### VM vs Container: Memory (RAM) Behavior

This is a key difference that explains why containers are "lightweight."

**Why VMs consume RAM even when idle:**

A VM contains a full OS + kernel + background services. When you boot a VM, the OS consumes RAM immediately, the hypervisor reserves RAM, and that memory is allocated upfront whether the VM is busy or not.

```
┌─────────────────────────────────────────────────────────────┐
│              VM MEMORY MODEL                                 │
│                                                              │
│  Host RAM: 16 GB                                            │
│  ─────────────────────────────────────────────────────      │
│  ├─ Host OS usage .................. 1.5 GB (always)        │
│  ├─ Hypervisor usage ............... 0.5 GB (always)        │
│  ├─ VM1 reserved RAM .............. 4 GB (even if idle)     │
│  │   ├─ Guest OS kernel ........... 0.5 GB                  │
│  │   ├─ Guest OS services ......... 0.3 GB                  │
│  │   ├─ App (currently idle) ...... 0.1 GB                  │
│  │   └─ Reserved but unused ....... 3.1 GB (WASTED)        │
│  ├─ VM2 reserved RAM .............. 4 GB (even if idle)     │
│  │   ├─ Guest OS kernel ........... 0.5 GB                  │
│  │   ├─ Guest OS services ......... 0.3 GB                  │
│  │   ├─ App (currently idle) ...... 0.2 GB                  │
│  │   └─ Reserved but unused ....... 3.0 GB (WASTED)        │
│  └─ Free for host ................. 6 GB                    │
│                                                              │
│  Total used: 10 GB (but apps only need 0.3 GB!)            │
│  Wasted: ~6.1 GB on OS overhead + reserved-but-unused      │
└─────────────────────────────────────────────────────────────┘
```

**Why containers are lightweight in RAM:**

Containers are processes. Processes don't need separate kernels, share the host kernel, and use RAM on demand as they run. You don't allocate RAM just to create an empty container — memory is used only when the process runs.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER MEMORY MODEL                          │
│                                                              │
│  Host RAM: 16 GB                                            │
│  ─────────────────────────────────────────────────────      │
│  ├─ Host OS usage .................. 1.5 GB (always)        │
│  ├─ Docker daemon usage ............ 0.1 GB (small)         │
│  ├─ Container A process memory ..... 0.1 GB (as needed)     │
│  ├─ Container B process memory ..... 0.2 GB (as needed)     │
│  ├─ Container C process memory ..... 0.05 GB (as needed)    │
│  └─ Free for host .................. 14.05 GB               │
│                                                              │
│  Total used: ~1.95 GB                                       │
│  No wasted RAM — containers use only what they need         │
│  No separate kernel per container                           │
│  No reserved-but-unused memory                              │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating the difference:**

```bash
# Create an empty container — check memory usage
$ docker create --name idle-test nginx:latest
a1b2c3d4e5f6...

# The container exists but uses ZERO RAM (it's not running)
$ docker ps -a --filter name=idle-test
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS    NAMES
a1b2c3d4e5f6   nginx:latest   "/docker-entrypoint.…"   5 seconds ago   Created   idle-test

# Start it and check actual memory usage
$ docker start idle-test
$ docker stats idle-test --no-stream

CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT     MEM %   NET I/O     BLOCK I/O
a1b2c3d4e5f6   idle-test   0.00%   3.2MiB / 7.773GiB    0.04%   0B / 0B     0B / 0B

# Only 3.2 MB! Compare that to a VM which would use 500MB-2GB
# just for the OS, even when idle.

# Clean up
$ docker rm -f idle-test
```

**Side-by-side comparison:**

```
┌──────────────────────────────────────────────────────────────┐
│                    MEMORY COMPARISON                          │
│                                                               │
│  Scenario: Run 5 nginx instances                             │
│                                                               │
│  Using VMs (5 VMs):                                          │
│  ┌────────────────────────────────────────────────────┐      │
│  │  VM1: 512MB reserved (OS 400MB + nginx 10MB)      │      │
│  │  VM2: 512MB reserved (OS 400MB + nginx 10MB)      │      │
│  │  VM3: 512MB reserved (OS 400MB + nginx 10MB)      │      │
│  │  VM4: 512MB reserved (OS 400MB + nginx 10MB)      │      │
│  │  VM5: 512MB reserved (OS 400MB + nginx 10MB)      │      │
│  │  Total: 2.5 GB reserved (only 50MB actually used) │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  Using Containers (5 containers):                            │
│  ┌────────────────────────────────────────────────────┐      │
│  │  Container 1: ~3MB (nginx process only)           │      │
│  │  Container 2: ~3MB (nginx process only)           │      │
│  │  Container 3: ~3MB (nginx process only)           │      │
│  │  Container 4: ~3MB (nginx process only)           │      │
│  │  Container 5: ~3MB (nginx process only)           │      │
│  │  Total: ~15MB (no OS overhead per container)      │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
│  Containers use 166x LESS memory for the same workload!      │
└──────────────────────────────────────────────────────────────┘
```

---

## 1.7 When to Use VM vs Container

This is a common interview question and an important architectural decision.

```
┌──────────────────────────────────────────────────────────────┐
│              USE A VM WHEN:                                   │
│                                                               │
│  ✅ You need full OS isolation (different kernels)           │
│     Example: Running Windows apps on a Linux host            │
│                                                               │
│  ✅ You need a different kernel version                      │
│     Example: Testing kernel-specific features                │
│                                                               │
│  ✅ Running legacy applications that need a full system      │
│     Example: Old enterprise apps that expect systemd, cron   │
│                                                               │
│  ✅ You need a desktop GUI environment                       │
│     Example: Windows desktop apps, GUI testing               │
│                                                               │
│  ✅ Strong security isolation is required                    │
│     Example: Multi-tenant environments with untrusted code   │
│                                                               │
│  ✅ You need to run multiple OS types simultaneously         │
│     Example: Linux + Windows on the same physical server     │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              USE A CONTAINER WHEN:                            │
│                                                               │
│  ✅ Microservices architecture                               │
│     Example: Each service (auth, payments, search) in its    │
│     own container                                            │
│                                                               │
│  ✅ CI/CD pipelines                                          │
│     Example: Build, test, deploy in isolated environments    │
│                                                               │
│  ✅ Rapid scaling                                            │
│     Example: Scale web servers from 2 to 20 in seconds       │
│                                                               │
│  ✅ Development and testing environments                     │
│     Example: "docker compose up" gives every developer       │
│     the same environment                                     │
│                                                               │
│  ✅ Stateless applications                                   │
│     Example: API servers, web frontends, workers             │
│                                                               │
│  ✅ Environment consistency (dev = staging = prod)           │
│     Example: Same Docker image runs everywhere               │
│                                                               │
│  ✅ Resource efficiency                                      │
│     Example: Run 50 services on one server instead of 50 VMs│
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**Real-world decision example:**

```bash
# Developer needs to test app with 3 different Java versions
# VM approach: Create 3 VMs (15-30 minutes, 6GB+ RAM)
# Container approach: 3 containers (10 seconds, ~100MB RAM)

$ docker run --rm openjdk:8 java -version
openjdk version "1.8.0_392"

$ docker run --rm openjdk:11 java -version
openjdk version "11.0.21"

$ docker run --rm openjdk:17 java -version
openjdk version "17.0.9"

# All three ran in seconds, used minimal resources, and cleaned up after themselves
```

```bash
# Running a web server — container is the obvious choice
$ docker run -d -p 8080:80 nginx

# Access it:
$ curl http://localhost:8080
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...

# Started in under 1 second, uses ~3MB RAM
# Compare to a VM: 2-5 minutes boot, 500MB+ RAM
```

---

## 1.8 Real-World Industry Use Cases

### Netflix
```
- Runs thousands of containers for microservices
- Each service (recommendations, streaming, billing) is a separate container
- Can scale individual services independently
- Deploy updates to one service without affecting others
```

### Spotify
```
- Uses Docker for their CI/CD pipeline
- Every code change triggers a container build
- Tests run in isolated containers
- Consistent environments from development to production
```

### PayPal
```
- Migrated from VMs to containers
- Reduced VM count by 50%
- 8x more apps per server
- Deployment time: hours → seconds
```

---

## 1.9 Key Terminology Glossary

```
┌──────────────────┬─────────────────────────────────────────────┐
│ Term             │ Definition                                   │
├──────────────────┼─────────────────────────────────────────────┤
│ Image            │ Read-only template to create containers      │
│ Container        │ Running instance of an image                 │
│ Dockerfile       │ Text file with instructions to build image   │
│ Docker Hub       │ Public registry for Docker images            │
│ Registry         │ Storage system for Docker images             │
│ Tag              │ Version label for an image (e.g., nginx:1.25)│
│ Layer            │ Single instruction result in an image        │
│ Volume           │ Persistent storage for container data        │
│ Bind Mount       │ Maps host directory into container           │
│ Docker Compose   │ Tool to define multi-container applications  │
│ Orchestration    │ Managing multiple containers (Kubernetes)    │
│ Daemon           │ Background Docker service (dockerd)          │
│ Build Context    │ Files sent to daemon during docker build     │
└──────────────────┴─────────────────────────────────────────────┘
```

---

## 1.10 Common Errors in This Module

### Error 1: Docker Daemon Not Running
```bash
$ docker ps
# Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
# Is the docker daemon running?

# Fix:
sudo systemctl start docker      # Linux
# Or restart Docker Desktop       # Mac/Windows
```

### Error 2: Permission Denied
```bash
$ docker ps
# Error: Got permission denied while trying to connect to the Docker daemon socket

# Fix: Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker    # Apply without logout

# Verify:
docker ps        # Should work without sudo now
```

---

## 1.11 "How Many Containers Can I Create?"

You can create many empty containers, but what matters is how much CPU, RAM, and disk the running applications need.

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER CAPACITY PLANNING                     │
│                                                              │
│  What determines how many containers you can run:            │
│                                                              │
│  1. CPU usage of each containerized app                     │
│  2. RAM requirements of each app                            │
│  3. Disk I/O usage                                          │
│  4. Network bandwidth                                       │
│  5. Resource limits configured (--memory, --cpus)           │
│                                                              │
│  Empty containers use almost no resources.                   │
│  It's the RUNNING APPLICATIONS inside that matter.          │
└─────────────────────────────────────────────────────────────┘
```

**Example — Memory-based capacity:**

```
Host RAM = 10 GB (available for containers)
Each app needs 4 GB RAM

┌──────────────────────────────────────────────────┐
│  Container 1: App (4 GB)  ✅ Runs fine           │
│  Container 2: App (4 GB)  ✅ Runs fine (8 GB used)│
│  Container 3: App (4 GB)  ❌ Only 2 GB left!     │
│                                                   │
│  Result: 3rd container will either:               │
│  • Be OOM-killed (Out Of Memory)                 │
│  • Swap heavily (very slow)                      │
│  • Fail to start if memory limits are set        │
└──────────────────────────────────────────────────┘
```

**Checking resource usage:**

```bash
# See how much resources all containers are using
$ docker stats --no-stream

CONTAINER ID   NAME     CPU %   MEM USAGE / LIMIT     MEM %   NET I/O          BLOCK I/O
a1b2c3d4e5f6   web      0.50%   45.2MiB / 7.773GiB   0.57%   1.2kB / 648B     0B / 0B
f6e5d4c3b2a1   db       2.30%   256MiB / 7.773GiB     3.21%   5.6kB / 3.2kB   12MB / 8MB
b2c3d4e5f6a1   cache    0.10%   12.8MiB / 7.773GiB    0.16%   800B / 400B      0B / 0B

# See total Docker disk usage
$ docker system df

TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          15        5         3.2GB     2.1GB (65%)
Containers      8         3         125MB     98MB (78%)
Local Volumes   4         2         500MB     200MB (40%)
Build Cache     0         0         0B        0B
```

**Practical guidelines:**

```
┌──────────────────────────────────────────────────────────────┐
│  App Type              │ Typical RAM  │ Containers per 16GB  │
├────────────────────────┼──────────────┼──────────────────────┤
│  Nginx (static files)  │ 10-50 MB     │ 100+                 │
│  Node.js API           │ 50-200 MB    │ 50-100               │
│  Python Flask/Django   │ 100-300 MB   │ 30-80                │
│  Java Spring Boot      │ 256-512 MB   │ 15-30                │
│  PostgreSQL            │ 256MB-2 GB   │ 5-15                 │
│  Elasticsearch         │ 1-4 GB       │ 3-8                  │
└────────────────────────┴──────────────┴──────────────────────┘
```

---

## 1.12 Docker: What It Is (Platform vs Tool)

Docker is not just a single tool — it is a **platform** for container management.

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER PLATFORM                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Container Management                                │    │
│  │  • docker run / stop / start / restart              │    │
│  │  • docker inspect / logs / exec                     │    │
│  │  • docker ps / stats                                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Image Management                                    │    │
│  │  • docker build (from Dockerfile)                   │    │
│  │  • docker pull / push (from/to registries)          │    │
│  │  • docker tag / history / inspect                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Networking                                          │    │
│  │  • docker network create / connect / disconnect     │    │
│  │  • Bridge, Host, Overlay, Macvlan drivers           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Storage (Volumes)                                   │    │
│  │  • docker volume create / inspect / rm              │    │
│  │  • Persistent data independent of container life    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Orchestration                                       │    │
│  │  • Docker Swarm (built-in, simpler)                 │    │
│  │  • Kubernetes (industry standard, more powerful)    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Composition                                         │    │
│  │  • Docker Compose (multi-container apps)            │    │
│  │  • Define entire stacks in docker-compose.yml       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 1.13 Does Docker Need an OS? Can It Run on Bare Metal?

This is a frequently asked question in interviews. The answer:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  ✅ Docker CAN run on a physical server directly            │
│     (bare metal server + Linux OS)                          │
│                                                              │
│  ❌ Docker CANNOT run directly on raw hardware              │
│     without an OS kernel                                    │
│                                                              │
│  Docker ALWAYS needs a host OS because it relies on         │
│  the OS kernel features (namespaces, cgroups).              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**What "bare metal" means in Docker context:**

```
"Bare metal" = No VM layer. Docker installed directly on a physical server's OS.

┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Option 1: Docker on Bare Metal (most common in production) │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Physical Server Hardware                             │   │
│  │  └── Linux OS (Ubuntu, CentOS, RHEL, etc.)           │   │
│  │      └── Docker Engine                                │   │
│  │          ├── Container A                              │   │
│  │          ├── Container B                              │   │
│  │          └── Container C                              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ✅ Best performance (no hypervisor overhead)               │
│  ✅ Direct hardware access                                  │
│                                                              │
│  Option 2: Docker inside a VM (common in cloud)             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Physical Server Hardware                             │   │
│  │  └── Hypervisor (ESXi, KVM)                          │   │
│  │      └── VM (Linux OS)                                │   │
│  │          └── Docker Engine                            │   │
│  │              ├── Container A                          │   │
│  │              ├── Container B                          │   │
│  │              └── Container C                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ⚠️ Slight overhead from hypervisor                        │
│  ✅ Common in AWS EC2, Azure VMs, GCP Compute Engine       │
│                                                              │
│  Option 3: Docker Desktop (dev machines — Mac/Windows)      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Mac/Windows Hardware                                 │   │
│  │  └── macOS / Windows                                  │   │
│  │      └── Lightweight Linux VM (HyperKit / WSL2)      │   │
│  │          └── Docker Engine                            │   │
│  │              ├── Container A                          │   │
│  │              └── Container B                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ⚠️ Needs a Linux VM because containers need Linux kernel  │
│  ✅ Transparent to the user (Docker Desktop handles it)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Verify what Docker is running on:**

```bash
$ docker info | grep -E "Operating System|Kernel|Server Version|Storage Driver"

# Example output on Linux bare metal:
Operating System: Ubuntu 22.04.3 LTS
Kernel Version: 5.15.0-91-generic
Server Version: 24.0.7
Storage Driver: overlay2

# Example output on Docker Desktop (Mac):
Operating System: Docker Desktop
Kernel Version: 6.6.12-linuxkit    # ← This is the Linux VM kernel
Server Version: 24.0.7
Storage Driver: overlay2
```

---

## 1.14 Can One Container Have Windows + Linux Together?

**No.** A single container cannot run two different kernels.

```
┌─────────────────────────────────────────────────────────────┐
│                    THE KERNEL RULE                            │
│                                                              │
│  Linux containers  → require a Linux kernel                 │
│  Windows containers → require a Windows kernel              │
│                                                              │
│  A container shares the HOST kernel.                        │
│  It cannot bring its own kernel.                            │
│  Therefore, the container's OS must be compatible           │
│  with the host kernel.                                      │
└─────────────────────────────────────────────────────────────┘
```

**What works on each host OS:**

```
┌──────────────────────────────────────────────────────────────┐
│  Host OS          │ Linux Containers │ Windows Containers    │
├───────────────────┼──────────────────┼───────────────────────┤
│  Linux            │ ✅ Native        │ ❌ Not possible       │
│                   │                  │    natively            │
├───────────────────┼──────────────────┼───────────────────────┤
│  Windows Server   │ ❌ Not native    │ ✅ Native (Windows    │
│  (Windows         │ (needs WSL2/VM)  │    containers mode)   │
│   containers mode)│                  │                       │
├───────────────────┼──────────────────┼───────────────────────┤
│  Windows          │ ✅ Via WSL2      │ ✅ Switch to Windows  │
│  (Docker Desktop) │ (lightweight     │    containers mode    │
│                   │  Linux VM)       │                       │
├───────────────────┼──────────────────┼───────────────────────┤
│  macOS            │ ✅ Via Linux VM  │ ❌ Not possible       │
│  (Docker Desktop) │ (HyperKit/       │                       │
│                   │  Apple Hypervisor│                       │
│                   │  Framework)      │                       │
└───────────────────┴──────────────────┴───────────────────────┘
```

**Why macOS needs a VM:**

```bash
# macOS does NOT have a Linux kernel
# Docker Desktop creates a lightweight Linux VM automatically

# You can verify this:
$ docker run --rm alpine uname -a
Linux 3a4b5c6d7e8f 6.6.12-linuxkit #1 SMP x86_64 Linux

# Notice: "linuxkit" — this is the Linux VM kernel, not macOS kernel
# Docker Desktop handles this transparently
```

**Common interview question: "Can I run a Windows container on Linux?"**

```
Short answer: No, not natively.

Long answer:
  - Windows containers need the Windows kernel (ntoskrnl.exe)
  - Linux hosts only have the Linux kernel
  - You would need a Windows VM on the Linux host,
    then run Windows containers inside that VM
  - This is rarely done in practice

In the real world:
  - Most containers are Linux-based (90%+)
  - Windows containers are used mainly for legacy .NET Framework apps
  - .NET Core/6/7/8 apps typically run in Linux containers
```

---

## 1.15 If Host Has Vulnerabilities, Do Containers Inherit Them?

**Yes — partly.** This is an important security concept.

```
┌─────────────────────────────────────────────────────────────┐
│                    WHY CONTAINERS INHERIT HOST RISKS         │
│                                                              │
│  Containers share the HOST KERNEL.                          │
│                                                              │
│  If the host kernel has a vulnerability and a container     │
│  breaks isolation (container escape), that's a serious risk.│
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Host Kernel (vulnerable)                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │Container │  │Container │  │Container │           │   │
│  │  │    A     │  │    B     │  │    C     │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  │                                                       │   │
│  │  All containers are exposed to the kernel             │   │
│  │  vulnerability because they ALL share this kernel     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Compare with VMs:                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Host Kernel (vulnerable)                             │   │
│  │  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │ VM1          │  │ VM2          │                  │   │
│  │  │ Own Kernel   │  │ Own Kernel   │                  │   │
│  │  │ (isolated)   │  │ (isolated)   │                  │   │
│  │  └──────────────┘  └──────────────┘                  │   │
│  │                                                       │   │
│  │  VMs have their own kernels — host kernel vuln        │   │
│  │  doesn't directly affect VM workloads                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### What Containers Help With (Security Benefits)

```
┌─────────────────────────────────────────────────────────────┐
│  Containers DO help with:                                    │
│                                                              │
│  ✅ Reduce drift — same image everywhere, no config drift   │
│  ✅ Minimal images — fewer packages = smaller attack surface│
│  ✅ Repeatable patching — rebuild image, redeploy           │
│  ✅ Immutable infrastructure — replace, don't patch in place│
│  ✅ Isolation between apps — one compromised app can't      │
│     easily access another's filesystem/network              │
└─────────────────────────────────────────────────────────────┘
```

### What Containers Don't Magically Fix

```
┌─────────────────────────────────────────────────────────────┐
│  Containers DON'T help if:                                   │
│                                                              │
│  ❌ Host kernel is unpatched                                │
│  ❌ You run containers as privileged/root unnecessarily     │
│  ❌ Images have known CVEs and you never update them        │
│  ❌ You use --privileged flag (disables most isolation)     │
│  ❌ Secrets are baked into images                           │
│  ❌ You expose unnecessary ports                            │
└─────────────────────────────────────────────────────────────┘
```

### Common Security Mitigations (Practical)

```bash
# 1. Keep host OS + kernel patched
$ sudo apt update && sudo apt upgrade -y
$ uname -r   # Check kernel version
5.15.0-91-generic

# 2. Use minimal base images (smaller attack surface)
# BAD: Full Ubuntu image (77MB, hundreds of packages)
FROM ubuntu:22.04

# BETTER: Alpine (5MB, minimal packages)
FROM alpine:3.19

# BEST: Distroless (only your app, no shell, no package manager)
FROM gcr.io/distroless/static-debian12

# 3. Run as non-root user in Dockerfile
FROM node:20-alpine
RUN addgroup -S app && adduser -S app -G app
USER app                    # ← Run as non-root
COPY --chown=app:app . /app
CMD ["node", "app.js"]

# 4. Drop Linux capabilities, avoid --privileged
$ docker run -d --cap-drop ALL --cap-add NET_BIND_SERVICE myapp:1.0
# Only grants the minimum capability needed

# NEVER do this in production:
$ docker run --privileged myapp:1.0   # ❌ Disables most isolation

# 5. Use security profiles
$ docker run -d --security-opt seccomp=default.json myapp:1.0
$ docker run -d --security-opt apparmor=docker-default myapp:1.0

# 6. Scan images for vulnerabilities
$ docker scout cves myapp:1.0
# Or use third-party tools:
$ trivy image myapp:1.0
# Output example:
# myapp:1.0 (alpine 3.19.0)
# Total: 2 (HIGH: 1, MEDIUM: 1)
# ┌──────────────┬──────────────┬──────────┬─────────────────┐
# │ Library      │ Vulnerability│ Severity │ Fixed Version   │
# ├──────────────┼──────────────┼──────────┼─────────────────┤
# │ libcrypto3   │ CVE-2024-XXX │ HIGH     │ 3.1.4-r5       │
# │ libssl3      │ CVE-2024-YYY │ MEDIUM   │ 3.1.4-r5       │
# └──────────────┴──────────────┴──────────┴─────────────────┘
```

---

## 1.16 Hands-On: Core Container Management Commands (with Sample Outputs)

### A) Check Docker Installation

```bash
# Check Docker version (client and server)
$ docker version

# Output (example):
Client: Docker Engine - Community
 Version:           24.0.7
 API version:       1.43
 Go version:        go1.20.10
 Git commit:        afdd53b
 Built:             Thu Oct 26 09:08:17 2023
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          24.0.7
  API version:      1.43 (minimum version 1.12)
  Go version:       go1.20.10
  Git commit:       311b9ff
  Built:            Thu Oct 26 09:08:17 2023
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.6.24
 runc:
  Version:          1.1.9
```

```bash
# Get detailed Docker system information
$ docker info

# Output includes:
Containers: 5
 Running: 2
 Paused: 0
 Stopped: 3
Images: 15
Server Version: 24.0.7
Storage Driver: overlay2
 Backing Filesystem: extfs
Logging Driver: json-file
Cgroup Driver: systemd
Cgroup Version: 2
Kernel Version: 5.15.0-91-generic
Operating System: Ubuntu 22.04.3 LTS
OSType: linux
Architecture: x86_64
CPUs: 4
Total Memory: 7.773GiB
Docker Root Dir: /var/lib/docker
```

### B) Image Management

```bash
# Pull an image from Docker Hub
$ docker pull nginx:latest

# Output (example):
latest: Pulling from library/nginx
a2abf6c4d29d: Pull complete
a9edb18cadd1: Pull complete
589b7251471a: Pull complete
186b1aaa4aa6: Pull complete
b4df32aa5a72: Pull complete
a0bcbecc962e: Pull complete
Digest: sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
Status: Downloaded newer image for nginx:latest
docker.io/library/nginx:latest

# List all local images
$ docker images

# Output (typical columns):
REPOSITORY    TAG           IMAGE ID       CREATED        SIZE
nginx         latest        a6bd71f48f68   2 weeks ago    187MB
python        3.12-slim     2a6b7f3e8c9d   3 weeks ago    143MB
alpine        3.19          05455a08881e   4 weeks ago    7.38MB
ubuntu        22.04         174c8c134b2a   5 weeks ago    77.9MB

# Remove an image
$ docker rmi nginx:latest
# Or by image ID:
$ docker rmi a6bd71f48f68

# Search for images on Docker Hub
$ docker search nginx

# Output:
NAME                    DESCRIPTION                                     STARS   OFFICIAL
nginx                   Official build of Nginx.                        19000   [OK]
bitnami/nginx           Bitnami nginx Docker Image                      180
nginx/nginx-ingress     NGINX and NGINX Plus Ingress Controllers        87
```

### C) Run a Container

```bash
# Run an nginx container in detached mode with port mapping
$ docker run -d --name web -p 8080:80 nginx:latest

# What each flag means:
#   -d           → Run in detached mode (background)
#   --name web   → Name the container "web"
#   -p 8080:80   → Map host port 8080 to container port 80
#   nginx:latest → Image to use

# Output:
a3c1f2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1

# Check running containers
$ docker ps

# Output:
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                  NAMES
a3c1f2d3e4f5   nginx:latest   "/docker-entrypoint.…"   10 seconds ago   Up 9 seconds    0.0.0.0:8080->80/tcp   web

# Check ALL containers (including stopped)
$ docker ps -a

# Output:
CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS                     PORTS                  NAMES
a3c1f2d3e4f5   nginx:latest   "/docker-entrypoint.…"   30 seconds ago   Up 29 seconds              0.0.0.0:8080->80/tcp   web
b4d5e6f7a8b9   python:3.12    "python3"                2 hours ago      Exited (0) 2 hours ago                            pyweb
```

```bash
# View container logs
$ docker logs web

# Output:
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
10-listen-on-ipv6-by-default.sh: info: Enabled listen on IPv6 in /etc/nginx/conf.d/default.conf
/docker-entrypoint.sh: Sourcing /docker-entrypoint.d/15-local-resolvers.envsh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
/docker-entrypoint.sh: Configuration complete; ready for start up
2024/01/15 10:05:23 [notice] 1#1: using the "epoll" event method
2024/01/15 10:05:23 [notice] 1#1: nginx/1.25.3
2024/01/15 10:05:23 [notice] 1#1: built by gcc 12.2.0 (Debian 12.2.0-14)

# Follow logs in real-time (like tail -f)
$ docker logs -f web
# Press Ctrl+C to stop following
```

```bash
# Enter a running container (interactive shell)
$ docker exec -it web bash

# What each flag means:
#   -i  → Interactive (keep STDIN open)
#   -t  → Allocate a pseudo-TTY (terminal)

# Output:
root@a3c1f2d3e4f5:/# ls
bin  boot  dev  docker-entrypoint.d  docker-entrypoint.sh  etc  home  lib  ...
root@a3c1f2d3e4f5:/# nginx -v
nginx version: nginx/1.25.3
root@a3c1f2d3e4f5:/# exit

# If bash isn't available (common in minimal images like alpine):
$ docker exec -it web sh
```

```bash
# Stop a container
$ docker stop web

# Output:
web

# Start a stopped container
$ docker start web

# Output:
web

# Remove a container (must be stopped first)
$ docker stop web && docker rm web

# Force remove a running container
$ docker rm -f web

# Output:
web
```

### D) Inspect (Important for Debugging and Interviews)

```bash
# Get detailed information about a container
$ docker inspect web

# Output (JSON — key sections shown):
[
    {
        "Id": "a3c1f2d3e4f5...",
        "Created": "2024-01-15T10:05:22.123456789Z",
        "State": {
            "Status": "running",
            "Running": true,
            "Pid": 12345,
            "StartedAt": "2024-01-15T10:05:23.456789012Z"
        },
        "NetworkSettings": {
            "IPAddress": "172.17.0.2",
            "Ports": {
                "80/tcp": [
                    {
                        "HostIp": "0.0.0.0",
                        "HostPort": "8080"
                    }
                ]
            }
        },
        "Mounts": [],
        "Config": {
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "NGINX_VERSION=1.25.3"
            ],
            "Image": "nginx:latest"
        }
    }
]

# Get just the IP address (useful for scripting)
$ docker inspect web --format='{{.NetworkSettings.IPAddress}}'
172.17.0.2

# Get just the container status
$ docker inspect web --format='{{.State.Status}}'
running

# Get port mappings
$ docker inspect web --format='{{json .NetworkSettings.Ports}}'
{"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"8080"}]}

# Get environment variables
$ docker inspect web --format='{{json .Config.Env}}'
["PATH=/usr/local/sbin:...","NGINX_VERSION=1.25.3"]
```

---

## 1.17 Dependency Conflict Demo (Java 1.7 vs 1.8)

This is the "separate kitchen" effect in action. You can run different runtimes without any conflict by isolating them in containers:

```bash
# Run Java 8 in one container
$ docker run --rm eclipse-temurin:8-jdk java -version

# Output:
openjdk version "1.8.0_392"
OpenJDK Runtime Environment (Temurin)(build 1.8.0_392-b08)
OpenJDK 64-Bit Server VM (Temurin)(build 25.392-b08, mixed mode)

# Run Java 17 in another container (simultaneously!)
$ docker run --rm eclipse-temurin:17-jdk java -version

# Output:
openjdk version "17.0.9" 2023-10-17
OpenJDK Runtime Environment Temurin-17.0.9+9 (build 17.0.9+9)
OpenJDK 64-Bit Server VM Temurin-17.0.9+9 (build 17.0.9+9, mixed mode, sharing)

# Run Java 21 in yet another container
$ docker run --rm eclipse-temurin:21-jdk java -version

# Output:
openjdk version "21.0.1" 2023-10-17 LTS
OpenJDK Runtime Environment Temurin-21.0.1+12 (build 21.0.1+12-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.1+12 (build 21.0.1+12-LTS, mixed mode, sharing)
```

**What just happened:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Three different Java versions ran on the SAME machine      │
│  at the SAME time with ZERO conflicts.                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Container 1  │  │ Container 2  │  │ Container 3  │      │
│  │ Java 8       │  │ Java 17      │  │ Java 21      │      │
│  │ (JDK 1.8)    │  │ (JDK 17)     │  │ (JDK 21)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │                │
│         └─────────────────┴─────────────────┘                │
│                           │                                  │
│                    Host OS (no Java installed!)              │
│                                                              │
│  Each container has its own JDK, PATH, and libraries.       │
│  They don't interfere with each other or the host.          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Same concept with Node.js:**

```bash
# Node.js 16 (older LTS)
$ docker run --rm node:16-alpine node -v
v16.20.2

# Node.js 18 (current LTS)
$ docker run --rm node:18-alpine node -v
v18.19.0

# Node.js 20 (latest LTS)
$ docker run --rm node:20-alpine node -v
v20.11.0

# Node.js 21 (current)
$ docker run --rm node:21-alpine node -v
v21.5.0

# All four versions available simultaneously, no nvm needed!
```

**Same concept with Python:**

```bash
$ docker run --rm python:3.8-slim python --version
Python 3.8.18

$ docker run --rm python:3.11-slim python --version
Python 3.11.7

$ docker run --rm python:3.12-slim python --version
Python 3.12.1

# No pyenv, no virtualenv conflicts, no PATH issues
```

---

## 1.18 Dev → QA Consistency (Reproducible App Example)

This demonstrates how the same container runs identically across environments.

**A tiny Python web app — run without installing Python locally:**

```bash
# Run a Flask app entirely inside a container
$ docker run -d --name pyweb -p 5000:5000 python:3.12-slim \
    sh -c "pip install flask && python -c \"
from flask import Flask
app = Flask(__name__)

@app.get('/')
def hi():
    return 'Hello from container!'

app.run(host='0.0.0.0', port=5000)
\""

# Output:
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
```

```bash
# Verify it's running
$ docker ps

CONTAINER ID   IMAGE              COMMAND                  CREATED          STATUS          PORTS                    NAMES
a1b2c3d4e5f6   python:3.12-slim   "sh -c 'pip install …"   10 seconds ago   Up 9 seconds    0.0.0.0:5000->5000/tcp   pyweb

# Test the app
$ curl http://localhost:5000
Hello from container!

# Check the logs
$ docker logs pyweb

Collecting flask
  Downloading flask-3.0.0-py3-none-any.whl (101 kB)
Successfully installed flask-3.0.0 ...
 * Serving Flask app '<module>'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000

# Clean up
$ docker stop pyweb && docker rm pyweb
pyweb
pyweb
```

**The key point:**

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  This SAME container runs the SAME way on:                  │
│                                                              │
│  • Developer's Mac (no Python installed locally)            │
│  • QA's Windows machine (Docker Desktop)                    │
│  • CI/CD pipeline (GitHub Actions, Jenkins)                 │
│  • Staging server (Ubuntu 22.04)                            │
│  • Production server (Amazon Linux 2)                       │
│                                                              │
│  Same image → Same Python version → Same Flask version      │
│  → Same behavior → No "works on my machine" issues          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 1.19 How Does the CPU Handle Multiple Containers?

This is a common question: "How does the CPU/processor handle tools in different containers?"

```
┌─────────────────────────────────────────────────────────────┐
│                    CPU SCHEDULING FOR CONTAINERS             │
│                                                              │
│  The HOST KERNEL scheduler schedules processes from         │
│  ALL containers. Containers don't have their own kernel     │
│  scheduler — they share the host kernel scheduling.         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              HOST KERNEL SCHEDULER                    │   │
│  │                                                       │   │
│  │  Time slice 1: Process from Container A              │   │
│  │  Time slice 2: Process from Container B              │   │
│  │  Time slice 3: Host process                          │   │
│  │  Time slice 4: Process from Container A              │   │
│  │  Time slice 5: Process from Container C              │   │
│  │  ...                                                  │   │
│  │                                                       │   │
│  │  The scheduler treats container processes like any    │   │
│  │  other process, but cgroups can limit how much CPU    │   │
│  │  time each container gets.                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Docker + runtime set up namespaces/cgroups.                │
│  The kernel enforces them.                                  │
│  There is NO separate scheduler per container.              │
└─────────────────────────────────────────────────────────────┘
```

**Controlling CPU allocation:**

```bash
# Give a container access to only 1 CPU core
$ docker run -d --name app1 --cpus=1 nginx

# Give a container access to 0.5 CPU cores (50% of one core)
$ docker run -d --name app2 --cpus=0.5 nginx

# Pin a container to specific CPU cores (cores 0 and 1)
$ docker run -d --name app3 --cpuset-cpus="0,1" nginx

# Set relative CPU priority (default is 1024)
$ docker run -d --name high-priority --cpu-shares=2048 nginx
$ docker run -d --name low-priority --cpu-shares=512 nginx
# high-priority gets 4x more CPU time than low-priority when competing

# Verify CPU limits
$ docker stats --no-stream

CONTAINER ID   NAME            CPU %   MEM USAGE / LIMIT     MEM %
a1b2c3d4e5f6   app1            0.00%   2.5MiB / 7.773GiB    0.03%
b2c3d4e5f6a1   app2            0.00%   2.3MiB / 7.773GiB    0.03%
c3d4e5f6a1b2   app3            0.00%   2.4MiB / 7.773GiB    0.03%
```

**What happens under the hood:**

```bash
# Docker creates cgroup entries for each container
# You can see them on the host:
$ ls /sys/fs/cgroup/cpu/docker/
a1b2c3d4e5f6...    # Container 1's cgroup
b2c3d4e5f6a1...    # Container 2's cgroup

# Check CPU quota for a container
$ cat /sys/fs/cgroup/cpu/docker/a1b2c3d4e5f6.../cpu.cfs_quota_us
100000    # 100000 = 1 CPU core (100% of one core)

$ cat /sys/fs/cgroup/cpu/docker/b2c3d4e5f6a1.../cpu.cfs_quota_us
50000     # 50000 = 0.5 CPU cores (50% of one core)
```

---

## 1.20 What You Do Day-to-Day (Container Management Focus)

Typical daily tasks when working with Docker:

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY DOCKER TASKS                         │
│                                                              │
│  1. Pull/build images                                       │
│  2. Run containers for dev/test                             │
│  3. Check logs and health                                   │
│  4. Exec into containers for debugging                      │
│  5. Manage networks and volumes                             │
│  6. Clean up unused containers/images                       │
│  7. Build and push images to registries                     │
│  8. Review container resource usage                         │
└─────────────────────────────────────────────────────────────┘
```

### Useful Cleanup Commands

Over time, Docker accumulates unused images, stopped containers, and dangling volumes. Regular cleanup is important.

```bash
# See how much disk space Docker is using
$ docker system df

TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          15        5         3.2GB     2.1GB (65%)
Containers      8         3         125MB     98MB (78%)
Local Volumes   4         2         500MB     200MB (40%)
Build Cache     12        0         890MB     890MB (100%)

# Detailed breakdown
$ docker system df -v
# Shows each image, container, and volume with sizes
```

```bash
# Remove all stopped containers
$ docker container prune

WARNING! This will remove all stopped containers.
Are you sure you want to continue? [y/N] y
Deleted Containers:
b4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5
Total reclaimed space: 98MB

# Remove unused images (not referenced by any container)
$ docker image prune

WARNING! This will remove all dangling images.
Are you sure you want to continue? [y/N] y
Deleted Images:
deleted: sha256:a1b2c3d4e5f6...
Total reclaimed space: 500MB

# Remove ALL unused images (not just dangling)
$ docker image prune -a

WARNING! This will remove all images without at least one container associated to them.
Are you sure you want to continue? [y/N] y
Total reclaimed space: 2.1GB

# Nuclear option: remove everything unused (containers, images, networks, build cache)
$ docker system prune

WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all dangling images
  - all dangling build cache

Are you sure you want to continue? [y/N] y
Total reclaimed space: 3.5GB

# Even more aggressive: also remove unused volumes
$ docker system prune --volumes
# ⚠️ Be careful — this deletes volume data permanently!
```

### Quick Reference: Most-Used Commands

```bash
# ─── IMAGE COMMANDS ───────────────────────────────────────
docker pull <image>:<tag>          # Download image from registry
docker images                      # List local images
docker rmi <image>                 # Remove an image
docker build -t <name>:<tag> .     # Build image from Dockerfile
docker tag <image> <new-name>      # Tag an image
docker push <image>:<tag>          # Push image to registry
docker history <image>             # Show image layer history
docker image inspect <image>       # Detailed image info

# ─── CONTAINER COMMANDS ──────────────────────────────────
docker run -d --name <n> <image>   # Run container (detached)
docker ps                          # List running containers
docker ps -a                       # List ALL containers
docker stop <container>            # Stop a container
docker start <container>           # Start a stopped container
docker restart <container>         # Restart a container
docker rm <container>              # Remove a stopped container
docker rm -f <container>           # Force remove (even running)
docker logs <container>            # View container logs
docker logs -f <container>         # Follow logs (real-time)
docker exec -it <container> sh     # Shell into container
docker inspect <container>         # Detailed container info
docker stats                       # Live resource usage
docker top <container>             # Show running processes
docker cp <src> <container>:<dst>  # Copy files to/from container
docker diff <container>            # Show filesystem changes
docker commit <container> <image>  # Create image from container

# ─── NETWORK COMMANDS ────────────────────────────────────
docker network ls                  # List networks
docker network create <name>       # Create a network
docker network inspect <name>      # Network details
docker network connect <net> <c>   # Connect container to network
docker network disconnect <n> <c>  # Disconnect from network

# ─── VOLUME COMMANDS ─────────────────────────────────────
docker volume ls                   # List volumes
docker volume create <name>        # Create a volume
docker volume inspect <name>       # Volume details
docker volume rm <name>            # Remove a volume

# ─── SYSTEM COMMANDS ─────────────────────────────────────
docker version                     # Docker version info
docker info                        # System-wide information
docker system df                   # Disk usage
docker system prune                # Clean up unused resources
```

---

## 1.21 Docker Components (Reference)

These are the building blocks you will work with constantly:

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPONENTS                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DOCKER IMAGE                                            │    │
│  │  • Immutable template (read-only layers)                │    │
│  │  • Built from a Dockerfile                              │    │
│  │  • Stored locally and/or in registries                  │    │
│  │  • Example: nginx:latest, python:3.12-slim              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DOCKER CONTAINER                                        │    │
│  │  • A running instance of an image                       │    │
│  │  • Has a writable layer on top of image layers          │    │
│  │  • Can be started, stopped, paused, deleted             │    │
│  │  • Ephemeral by default (data lost when removed)        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  DOCKER ENGINE                                           │    │
│  │  • dockerd daemon + container runtime (containerd/runc) │    │
│  │  • Manages lifecycle, networking, volumes                │    │
│  │  • Listens on unix socket or TCP                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  REGISTRY                                                │    │
│  │  • Where images are stored and distributed              │    │
│  │  • Docker Hub (default public registry)                 │    │
│  │  • AWS ECR, Google GCR, Azure ACR (private registries)  │    │
│  │  • Self-hosted: Harbor, GitLab Container Registry       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  VOLUMES                                                 │    │
│  │  • Persistent storage independent of container lifecycle│    │
│  │  • Data survives container removal                      │    │
│  │  • Managed by Docker (docker volume create)             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  NETWORKS                                                │    │
│  │  • Bridge: Default local network (containers on same    │    │
│  │    host communicate)                                    │    │
│  │  • Host: Container shares host network stack            │    │
│  │  • Overlay: Multi-host networking (Swarm/Kubernetes)    │    │
│  │  • None: No networking                                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module 1 Summary

- Docker packages applications with all dependencies into containers
- Containers share the host OS kernel (unlike VMs which need full guest OS)
- Docker uses client-server architecture: CLI → Daemon → Registry
- Images are read-only templates; containers are running instances
- Images are built in layers, which are cached for fast rebuilds
- Isolation is achieved through Linux namespaces and cgroups
- Containers are isolated processes, not virtual machines
- Docker needs a host OS — it cannot run on raw hardware without a kernel
- Linux containers need a Linux kernel; Windows containers need a Windows kernel
- Container capacity depends on app resource needs, not container count
- Industry leaders (Netflix, Spotify, PayPal) use Docker at massive scale

---

**Next Module: [Module 2 - Installation and Your First Container](module-02-installation.md)**
