# Module 3: Docker Images - Building, Managing, and Registries

---

## 3.1 What is a Docker Image?

A Docker image is a **read-only template** containing:
- Application code
- Runtime (Node.js, Python, Java, etc.)
- System libraries and dependencies
- Environment variables and configuration
- Instructions on how to run the application

```
Think of it like a recipe:
  Image  = Recipe (instructions + ingredients list)
  Container = The actual dish cooked from the recipe

You can cook (run) the same recipe many times.
Each dish (container) is independent.
```

### Image Internals — What's Actually Inside?

An image is a **layered filesystem**, typically containing:

```
┌─────────────────────────────────────────────────────────────┐
│                    WHAT'S IN A DOCKER IMAGE                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 3: Your application code + dependencies       │   │
│  │           (app.js, node_modules, requirements.txt)   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Layer 2: Runtime                                    │   │
│  │           (Python 3.12, Java 21, Node.js 20)         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Layer 1: Base OS filesystem (user-space only)       │   │
│  │           (Ubuntu, Alpine, Debian — NOT the kernel)  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  IMPORTANT: Images do NOT include a kernel.                 │
│  They use the HOST kernel at runtime.                       │
│                                                              │
│  An image contains:                                         │
│  ✅ /bin, /usr, /lib, /etc (user-space OS files)           │
│  ✅ Runtime binaries (python, java, node)                  │
│  ✅ Application code and dependencies                      │
│  ✅ Configuration files                                    │
│  ❌ NOT the Linux kernel (/boot/vmlinuz)                   │
│  ❌ NOT hardware drivers                                   │
│  ❌ NOT a hypervisor                                       │
└─────────────────────────────────────────────────────────────┘
```

**Verify what's inside an image:**

```bash
# See the layers of an image
$ docker history nginx:latest

IMAGE          CREATED       CREATED BY                                      SIZE
a6bd71f48f68   2 weeks ago   CMD ["nginx" "-g" "daemon off;"]                0B
<missing>      2 weeks ago   STOPSIGNAL SIGQUIT                              0B
<missing>      2 weeks ago   EXPOSE map[80/tcp:{}]                           0B
<missing>      2 weeks ago   ENTRYPOINT ["/docker-entrypoint.sh"]            0B
<missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           4.62kB
<missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           3.02kB
<missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           2.12kB
<missing>      2 weeks ago   COPY file:xxx in /                              1.62kB
<missing>      2 weeks ago   RUN /bin/sh -c set -x && addgroup...            61.1MB
<missing>      2 weeks ago   ENV NGINX_VERSION=1.25.3 ...                    0B
<missing>      2 weeks ago   LABEL maintainer=NGINX Docker Maintainers      0B
<missing>      2 weeks ago   /bin/sh -c #(nop) CMD ["bash"]                  0B
<missing>      2 weeks ago   /bin/sh -c #(nop) ADD file:xxx in /             74.8MB

# Bottom layer (74.8MB) = Debian base OS filesystem
# Middle layer (61.1MB) = nginx installation
# Top layers = configuration files and entrypoint scripts
```

### Image is Read-Only; Container Adds a Writable Layer

This is a fundamental concept. When you run a container from an image:

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  CONTAINER (running)                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Writable Layer (Container Layer)                    │   │
│  │  • All changes go here (new files, modified files)   │   │
│  │  • Deleted when container is removed                 │   │
│  │  • Unique to each container                          │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 3 (Read-Only) ── app code              │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 2 (Read-Only) ── runtime               │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 1 (Read-Only) ── base OS               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Key points:                                                │
│  • Image layers are SHARED across all containers            │
│  • Changes inside a container don't change the image        │
│  • This is why you can create many identical containers     │
│    from the same image                                      │
│  • This uses "Copy-on-Write" (CoW) — files are only        │
│    copied to the writable layer when modified               │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating the writable layer:**

```bash
# Run two containers from the same image
$ docker run -d --name web1 nginx:latest
$ docker run -d --name web2 nginx:latest

# Create a file in web1
$ docker exec web1 sh -c "echo 'hello from web1' > /tmp/test.txt"

# Check — file exists in web1
$ docker exec web1 cat /tmp/test.txt
hello from web1

# Check — file does NOT exist in web2 (separate writable layer)
$ docker exec web2 cat /tmp/test.txt
cat: /tmp/test.txt: No such file or directory

# The original image is unchanged
# Both containers share the same read-only image layers
# But each has its own writable layer

# See what changed in web1's writable layer
$ docker diff web1
C /tmp
A /tmp/test.txt
C /var
C /var/cache
C /var/cache/nginx
A /var/cache/nginx/client_temp
...

# A = Added, C = Changed, D = Deleted

# Clean up
$ docker rm -f web1 web2
```

**Why this matters:**

```
┌─────────────────────────────────────────────────────────────┐
│  100 containers from the same nginx image:                  │
│                                                              │
│  Disk usage WITHOUT layer sharing:                          │
│  100 × 187MB = 18.7 GB                                     │
│                                                              │
│  Disk usage WITH layer sharing (how Docker works):          │
│  1 × 187MB (shared image) + 100 × ~1MB (writable layers)   │
│  = ~287 MB total                                            │
│                                                              │
│  That's 65x less disk usage!                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.2 Image Naming Convention

```
registry/repository:tag

Examples:
  docker.io/library/nginx:1.25        # Full form
  nginx:1.25                           # Short form (docker.io/library/ implied)
  nginx                                # Tag defaults to "latest"
  mycompany/backend:v2.3.1             # Custom repository
  ghcr.io/myorg/myapp:sha-abc123      # GitHub Container Registry
  123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:prod  # AWS ECR

Breakdown:
┌──────────────────────────────────────────────────────────┐
│ registry     │ Where the image is stored                 │
│              │ Default: docker.io (Docker Hub)           │
├──────────────┼───────────────────────────────────────────┤
│ repository   │ Name of the image (can include namespace) │
│              │ e.g., library/nginx, mycompany/backend    │
├──────────────┼───────────────────────────────────────────┤
│ tag          │ Version identifier                        │
│              │ Default: latest                           │
│              │ e.g., 1.25, v2.0, alpine, slim           │
└──────────────┴───────────────────────────────────────────┘
```

### Common Tag Patterns

```bash
# Official images use descriptive tags:
python:3.11           # Full Python 3.11 image (~900MB)
python:3.11-slim      # Minimal Debian-based (~130MB)
python:3.11-alpine    # Alpine Linux-based (~50MB)
python:3.11-bookworm  # Debian Bookworm-based

node:20               # Full Node.js 20 (~1GB)
node:20-slim          # Slim variant (~200MB)
node:20-alpine        # Alpine variant (~130MB)

# Size comparison:
# REPOSITORY   TAG          SIZE
# python       3.11         921MB
# python       3.11-slim    131MB
# python       3.11-alpine  51MB
#
# Rule of thumb:
# - Use "slim" for production (good balance of size and compatibility)
# - Use "alpine" for smallest size (may have compatibility issues with some C libraries)
# - Use full image for development (has all tools)
```

### Docker Hub vs Private Registry — How Docker Resolves Image Names

When you type `docker run nginx`, Docker pulls from Docker Hub by default. But in production, companies use private registries.

```
┌─────────────────────────────────────────────────────────────┐
│              HOW DOCKER RESOLVES IMAGE NAMES                 │
│                                                              │
│  docker run nginx                                           │
│       │                                                      │
│       ▼                                                      │
│  No registry specified → use Docker Hub (docker.io)         │
│  No namespace specified → use "library" (official images)   │
│  No tag specified → use "latest"                            │
│       │                                                      │
│       ▼                                                      │
│  Actual pull: docker.io/library/nginx:latest                │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  docker run mycompany.registry.com/backend:v2               │
│       │                                                      │
│       ▼                                                      │
│  Registry: mycompany.registry.com (private)                 │
│  Repository: backend                                        │
│  Tag: v2                                                    │
│       │                                                      │
│       ▼                                                      │
│  Actual pull: mycompany.registry.com/backend:v2             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# ─── DOCKER HUB (default, public) ────────────────────────
$ docker run nginx
# Pulls from: docker.io/library/nginx:latest

$ docker run python:3.12-slim
# Pulls from: docker.io/library/python:3.12-slim

# ─── PRIVATE REGISTRY ────────────────────────────────────
$ docker run mycompany.registry.com/myapp:v1
# Pulls from: mycompany.registry.com/myapp:v1

$ docker run 123456789.dkr.ecr.us-east-1.amazonaws.com/backend:prod
# Pulls from: AWS ECR private registry

$ docker run ghcr.io/myorg/frontend:sha-abc123
# Pulls from: GitHub Container Registry

# Structure: registry/image:tag
# Examples:
#   myregistry.com/backend:v2
#   gcr.io/my-project/api:latest
#   harbor.internal.com/team-a/service:1.0.0
```

### Image Size Differences Explained

Images vary dramatically in size because they contain different amounts of OS files, libraries, and tools. Understanding this helps you choose the right base image.

```
┌──────────────────────────────────────────────────────────────┐
│              WHY IMAGES HAVE DIFFERENT SIZES                  │
│                                                               │
│  An image is made of LAYERS. More layers = larger size.      │
│                                                               │
│  Small image (alpine):              Large image (ubuntu+java)│
│  ┌──────────────────┐              ┌──────────────────┐      │
│  │ App code (1 MB)  │              │ App code (1 MB)  │      │
│  ├──────────────────┤              ├──────────────────┤      │
│  │ Alpine OS (5 MB) │              │ Java JDK (300 MB)│      │
│  └──────────────────┘              ├──────────────────┤      │
│  Total: ~6 MB                      │ Build tools      │      │
│                                    │ (gcc, make) 200MB│      │
│                                    ├──────────────────┤      │
│                                    │ Ubuntu OS (77 MB)│      │
│                                    └──────────────────┘      │
│                                    Total: ~578 MB            │
│                                                               │
│  More layers with more packages = larger image               │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Compare image sizes for the same runtime
$ docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort

REPOSITORY   TAG            SIZE
alpine       3.19           7.38MB      ← Tiny! Minimal Linux
ubuntu       22.04          77.9MB      ← Full Ubuntu user-space
python       3.12-alpine    51.8MB      ← Python on Alpine
python       3.12-slim      143MB       ← Python on slim Debian
python       3.12           1.01GB      ← Full Python (includes gcc, dev tools)
node         20-alpine      130MB       ← Node.js on Alpine
node         20-slim        200MB       ← Node.js on slim Debian
node         20             1.1GB       ← Full Node.js (includes build tools)
openjdk      17-alpine      330MB       ← Java on Alpine
openjdk      17             471MB       ← Full Java image
```

```
┌──────────────────────────────────────────────────────────────┐
│              IMAGE SIZE COMPARISON TABLE                      │
│                                                               │
│  Base Image        │ Size    │ Use Case                      │
│  ──────────────────┼─────────┼───────────────────────────── │
│  scratch           │ 0 MB    │ Static Go/Rust binaries       │
│  alpine:3.19       │ 7 MB    │ Minimal Linux, small tools    │
│  debian:bookworm-  │ 74 MB   │ Slim Debian, good compat     │
│    slim            │         │                               │
│  ubuntu:22.04      │ 78 MB   │ Full Ubuntu user-space        │
│  python:3.12-slim  │ 143 MB  │ Production Python apps        │
│  node:20-slim      │ 200 MB  │ Production Node.js apps       │
│  python:3.12       │ 1.01 GB │ Development (has gcc, make)   │
│  node:20           │ 1.1 GB  │ Development (has build tools) │
│                    │         │                               │
│  Rule of thumb:                                              │
│  • Production: use -slim or -alpine (smaller, fewer CVEs)   │
│  • Development: use full image (has compilers, debuggers)   │
│  • Maximum security: use distroless or scratch              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3.3 Pulling Images

```bash
# Pull the latest version of an image
docker pull nginx

# Output:
# Using default tag: latest
# latest: Pulling from library/nginx
# a2abf6c4d29d: Pull complete          ← Layer 1
# a9edb18cadd1: Pull complete          ← Layer 2
# 589b7251471a: Pull complete          ← Layer 3
# 186b1aaa4aa6: Pull complete          ← Layer 4
# b4df32aa5a72: Pull complete          ← Layer 5
# a0bcbecc962e: Pull complete          ← Layer 6
# Digest: sha256:0d17b565c37bcbd895...  ← Unique content hash
# Status: Downloaded newer image for nginx:latest
# docker.io/library/nginx:latest

# MEANING: Each "Pull complete" line is a layer being downloaded.
# Layers are cached — if another image shares a layer, it's reused.
```

```bash
# Pull a specific version
docker pull nginx:1.25.3

# Pull from a different registry
docker pull ghcr.io/actions/runner:latest

# Pull all tags of an image (rarely needed)
docker pull --all-tags nginx
```

### Understanding Digests

```bash
# A digest is a SHA256 hash of the image content — immutable and unique
docker pull nginx@sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31

# MEANING: Unlike tags (which can be moved to point to different images),
# digests are permanent. Use digests in production for guaranteed reproducibility.

# View digest of a local image
docker inspect --format='{{.RepoDigests}}' nginx
# Output: [nginx@sha256:0d17b565c37bcbd895...]
```

---

## 3.4 Listing and Inspecting Images

```bash
# List all local images
docker images

# Output:
# REPOSITORY   TAG          IMAGE ID       CREATED        SIZE
# nginx        latest       a6bd71f48f68   2 weeks ago    187MB
# nginx        1.25         c20060033e06   3 weeks ago    187MB
# python       3.11-slim    f3b7a8c9d0e1   1 month ago    131MB
# node         20-alpine    b2c3d4e5f6a7   1 week ago     181MB

# Filter images
docker images nginx
# Shows only nginx images

# Show image IDs only
docker images -q
# Output:
# a6bd71f48f68
# c20060033e06
# f3b7a8c9d0e1
# b2c3d4e5f6a7

# Show dangling images (untagged, leftover from builds)
docker images -f "dangling=true"
```

```bash
# Inspect image details
docker inspect nginx:latest

# Output (abbreviated JSON):
# [
#     {
#         "Id": "sha256:a6bd71f48f68...",
#         "Created": "2024-01-10T00:00:00Z",
#         "Architecture": "amd64",
#         "Os": "linux",
#         "Size": 187000000,
#         "Config": {
#             "ExposedPorts": { "80/tcp": {} },
#             "Env": [
#                 "PATH=/usr/local/sbin:/usr/local/bin:...",
#                 "NGINX_VERSION=1.25.3"
#             ],
#             "Cmd": ["nginx", "-g", "daemon off;"]
#         },
#         "RootFS": {
#             "Type": "layers",
#             "Layers": [
#                 "sha256:layer1...",
#                 "sha256:layer2...",
#                 "sha256:layer3..."
#             ]
#         }
#     }
# ]

# MEANING: Shows architecture, exposed ports, environment variables,
# default command, and all layers that make up the image.
```

```bash
# View image history (layers and their sizes)
docker history nginx

# Output:
# IMAGE          CREATED       CREATED BY                                      SIZE
# a6bd71f48f68   2 weeks ago   CMD ["nginx" "-g" "daemon off;"]                0B
# <missing>      2 weeks ago   STOPSIGNAL SIGQUIT                              0B
# <missing>      2 weeks ago   EXPOSE map[80/tcp:{}]                           0B
# <missing>      2 weeks ago   ENTRYPOINT ["/docker-entrypoint.sh"]            0B
# <missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           4.62kB
# <missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           3.02kB
# <missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.sh          1.62kB
# <missing>      2 weeks ago   RUN /bin/sh -c set -x && addgroup...            61.1MB
# <missing>      2 weeks ago   ENV NGINX_VERSION=1.25.3                        0B
# <missing>      3 weeks ago   /bin/sh -c #(nop) CMD ["bash"]                  0B
# <missing>      3 weeks ago   /bin/sh -c #(nop) ADD file:xxx in /             77.8MB

# MEANING: Shows each Dockerfile instruction that created a layer.
# SIZE column shows how much each layer adds.
# The base Debian layer is 77.8MB, nginx installation adds 61.1MB.
```

---

## 3.5 How Docker Images Are Created — The Concept

Before learning Dockerfiles, understand the fundamental concept: **an image is a snapshot of a container's filesystem**.

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE CREATION CONCEPT                           │
│                                                              │
│  Step 1: Pull a base image from Docker Hub                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker Hub                                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │ ubuntu  │  │ alpine  │  │ centos  │  ...         │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼ docker pull / docker run                │
│                                                              │
│  Step 2: Run a container from the base image                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container (running instance of the image)           │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  Base OS (Ubuntu)                              │  │   │
│  │  │  + Read-Write Layer (your changes go here)     │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼ Make changes (install, configure, etc.) │
│                                                              │
│  Step 3: Install software, create files, configure          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container (modified)                                │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  Base OS (Ubuntu)                              │  │   │
│  │  │  + apt-get install tree git curl               │  │   │
│  │  │  + created /app/config.txt                     │  │   │
│  │  │  + modified /etc/environment                   │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    ▼ docker commit                           │
│                                                              │
│  Step 4: Save the container as a NEW image                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  New Image: my-custom-ubuntu:1.0                     │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  Base OS (Ubuntu)                              │  │   │
│  │  │  + tree, git, curl pre-installed               │  │   │
│  │  │  + /app/config.txt included                    │  │   │
│  │  │  + /etc/environment modified                   │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Now you can run containers from YOUR image:                │
│  docker run my-custom-ubuntu:1.0                            │
│  → Container starts with tree, git, curl already installed  │
└─────────────────────────────────────────────────────────────┘
```

### Two Ways to Create Images

```
┌─────────────────────────────────────────────────────────────┐
│  Method 1: docker commit (manual, interactive)              │
│  ─────────────────────────────────────────────              │
│  1. Run a container from a base image                       │
│  2. Enter the container (docker exec / docker run -it)      │
│  3. Make changes manually (install packages, create files)  │
│  4. Exit and run: docker commit container-name new-image    │
│                                                              │
│  ✅ Good for: Quick experiments, debugging, learning        │
│  ❌ Bad for: Production (not reproducible, no version ctrl) │
│                                                              │
│  Method 2: Dockerfile (automated, declarative)              │
│  ─────────────────────────────────────────────              │
│  1. Write a Dockerfile with instructions                    │
│  2. Run: docker build -t my-image .                         │
│  3. Docker executes each instruction and creates layers     │
│                                                              │
│  ✅ Good for: Production, CI/CD, reproducible builds        │
│  ✅ Version controlled, auditable, shareable                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.6 Creating Images with docker commit — Step by Step

`docker commit` takes a container's current filesystem state and saves it as a new image.

### Complete Walkthrough

```bash
# ─── Step 1: Pull and run a base image ──────────────────────
$ docker run -it --name my-ubuntu ubuntu bash

# You're now inside the container
root@abc123:/# 

# ─── Step 2: Check what's NOT installed ─────────────────────
root@abc123:/# which tree
# (no output — tree is not installed)

root@abc123:/# which git
# (no output — git is not installed)

root@abc123:/# which curl
# (no output — curl is not installed)

# The base ubuntu image is minimal — very few tools included.

# ─── Step 3: Install software ──────────────────────────────
root@abc123:/# apt-get update
# Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
# Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease
# ...
# Reading package lists... Done

root@abc123:/# apt-get install -y tree git curl
# Reading package lists... Done
# Building dependency tree... Done
# The following NEW packages will be installed:
#   curl git tree ...
# Setting up tree (2.0.2-1) ...
# Setting up curl (7.81.0-1ubuntu1) ...
# Setting up git (1:2.34.1-1ubuntu1) ...

# ─── Step 4: Create some files ─────────────────────────────
root@abc123:/# mkdir -p /app
root@abc123:/# echo "version=1.0" > /app/config.txt
root@abc123:/# echo "Welcome to my custom image" > /app/README.txt

# ─── Step 5: Verify changes ────────────────────────────────
root@abc123:/# which tree git curl
/usr/bin/tree
/usr/bin/git
/usr/bin/curl

root@abc123:/# cat /app/config.txt
version=1.0

root@abc123:/# tree /app/
/app/
├── README.txt
└── config.txt

# ─── Step 6: Exit the container ────────────────────────────
root@abc123:/# exit

# ─── Step 7: Commit the container as a new image ───────────
$ docker commit my-ubuntu my-custom-ubuntu:1.0

# Output:
# sha256:a1b2c3d4e5f6...

# MEANING: Docker took a snapshot of the container's filesystem
# and saved it as a new image called my-custom-ubuntu:1.0

# ─── Step 8: Verify the new image exists ───────────────────
$ docker images my-custom-ubuntu

# REPOSITORY         TAG   IMAGE ID       CREATED          SIZE
# my-custom-ubuntu   1.0   a1b2c3d4e5f6   10 seconds ago   250MB

# Compare with base image:
$ docker images ubuntu
# REPOSITORY   TAG      IMAGE ID       SIZE
# ubuntu       latest   abc123def456   77.8MB

# The custom image is larger because it includes tree, git, curl.

# ─── Step 9: Test the new image ────────────────────────────
$ docker run -it my-custom-ubuntu:1.0 bash

root@def456:/# which tree git curl
/usr/bin/tree
/usr/bin/git
/usr/bin/curl

root@def456:/# cat /app/config.txt
version=1.0

root@def456:/# tree /app/
/app/
├── README.txt
└── config.txt

# Everything is pre-installed and pre-configured!
root@def456:/# exit
```

### Adding Metadata with docker commit

```bash
# Commit with author and message (like a git commit)
$ docker commit \
    --author "DevOps Team <devops@company.com>" \
    --message "Added tree, git, curl; created /app with config" \
    my-ubuntu my-custom-ubuntu:1.1

# Commit with CMD change (set default command)
$ docker commit \
    --change='CMD ["bash"]' \
    my-ubuntu my-custom-ubuntu:1.2

# Commit with environment variable
$ docker commit \
    --change='ENV APP_VERSION=1.0' \
    --change='WORKDIR /app' \
    my-ubuntu my-custom-ubuntu:1.3

# View commit history
$ docker history my-custom-ubuntu:1.0
# IMAGE          CREATED          CREATED BY                                      SIZE
# a1b2c3d4e5f6   2 minutes ago    bash                                            172MB
# abc123def456   2 weeks ago      /bin/sh -c #(nop) CMD ["/bin/bash"]             0B
# <missing>      2 weeks ago      /bin/sh -c #(nop) ADD file:... in /             77.8MB
```

### When to Use docker commit vs Dockerfile

```
┌──────────────────────────────────────────────────────────────┐
│  docker commit                    │ Dockerfile               │
├───────────────────────────────────┼──────────────────────────┤
│  Manual, interactive              │ Automated, declarative   │
│  Not reproducible                 │ Fully reproducible       │
│  No version control               │ Git-trackable            │
│  Hard to audit what changed       │ Every step documented    │
│  Quick experiments                │ Production builds        │
│  Debugging / troubleshooting      │ CI/CD pipelines          │
│  Learning how images work         │ Team collaboration       │
├───────────────────────────────────┼──────────────────────────┤
│  Use for: learning, prototyping   │ Use for: everything else │
└───────────────────────────────────┴──────────────────────────┘
```

---

## 3.7 Image Layers — How Images Are Built Internally

Every Docker image is made of **layers**. Each layer represents a change to the filesystem. Layers are read-only and stacked on top of each other.

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE LAYERS (Read-Only Stack)                   │
│                                                              │
│  When you run: docker commit my-ubuntu my-custom-ubuntu:1.0 │
│                                                              │
│  The resulting image has these layers:                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 4: Your changes (docker commit)               │   │
│  │  + apt-get install tree git curl                     │   │
│  │  + created /app/config.txt                           │   │
│  │  + created /app/README.txt                           │   │
│  │  Size: ~172MB                                        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Layer 3: CMD ["/bin/bash"]                          │   │
│  │  (metadata only — no filesystem change)              │   │
│  │  Size: 0B                                            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Layer 2: Ubuntu package lists                       │   │
│  │  Size: ~30MB                                         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Layer 1: Base Ubuntu filesystem                     │   │
│  │  /bin, /usr, /lib, /etc, /var                        │   │
│  │  Size: ~77.8MB                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Total image size = sum of all layers                       │
│  Each layer is READ-ONLY and cached                         │
│  Layers are SHARED between images that use the same base    │
└─────────────────────────────────────────────────────────────┘
```

### Layer Sharing Between Images

```
┌─────────────────────────────────────────────────────────────┐
│              LAYER SHARING                                    │
│                                                              │
│  Image A: my-app-1:1.0          Image B: my-app-2:1.0      │
│  ┌────────────────────┐         ┌────────────────────┐      │
│  │ Layer: app-1 code  │         │ Layer: app-2 code  │      │
│  ├────────────────────┤         ├────────────────────┤      │
│  │ Layer: npm install │         │ Layer: pip install  │      │
│  ├────────────────────┤         ├────────────────────┤      │
│  │                    │         │                    │      │
│  │  Layer: Ubuntu     │◄───────►│  Layer: Ubuntu     │      │
│  │  (SHARED — stored  │  same   │  (SHARED — stored  │      │
│  │   only ONCE on     │  layer  │   only ONCE on     │      │
│  │   disk)            │         │   disk)            │      │
│  └────────────────────┘         └────────────────────┘      │
│                                                              │
│  If both images use ubuntu:22.04 as base:                   │
│  - The Ubuntu layer is downloaded and stored ONCE            │
│  - Both images reference the same layer by SHA256 hash      │
│  - Saves disk space and download time                       │
└─────────────────────────────────────────────────────────────┘
```

### Viewing Image Layers

```bash
# See all layers of an image
$ docker history my-custom-ubuntu:1.0

# IMAGE          CREATED          CREATED BY                                      SIZE
# a1b2c3d4e5f6   5 minutes ago    bash                                            172MB
# abc123def456   2 weeks ago      /bin/sh -c #(nop) CMD ["/bin/bash"]             0B
# <missing>      2 weeks ago      /bin/sh -c mkdir -p /run/systemd && echo '...'  7B
# <missing>      2 weeks ago      /bin/sh -c #(nop) ADD file:... in /             77.8MB

# READING THE OUTPUT:
# - Bottom layer = base OS filesystem (77.8MB)
# - Middle layers = base image setup (metadata, small changes)
# - Top layer = YOUR changes from docker commit (172MB)
# - <missing> = intermediate layers (normal for pulled images)

# Inspect image details
$ docker inspect my-custom-ubuntu:1.0 --format='{{json .RootFS.Layers}}' | python3 -m json.tool
# [
#     "sha256:aaa111...",    ← Layer 1 (base OS)
#     "sha256:bbb222...",    ← Layer 2 (package lists)
#     "sha256:ccc333...",    ← Layer 3 (your commit)
# ]

# Each layer is identified by a SHA256 hash
# Same hash = same content = shared between images
```

### Container Writable Layer vs Image Layers

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER = IMAGE LAYERS + WRITABLE LAYER       │
│                                                              │
│  When you run: docker run -it my-custom-ubuntu:1.0 bash     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Writable Layer (Container-specific)                 │   │
│  │  - New files you create                              │   │
│  │  - Modified files (copy-on-write)                    │   │
│  │  - Deleted files (whiteout markers)                  │   │
│  │  ⚠️  LOST when container is removed (unless volume)  │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 3: tree, git, curl (READ-ONLY)         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 2: CMD metadata (READ-ONLY)            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Image Layer 1: Ubuntu base (READ-ONLY)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Copy-on-Write (CoW):                                       │
│  When a container modifies a file from an image layer,      │
│  Docker copies that file to the writable layer first.       │
│  The original image layer is never modified.                │
│                                                              │
│  docker commit = take the writable layer and save it        │
│  as a new read-only image layer                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3.8 Building Your First Image

### Step 1: Create a Simple Node.js Application

```bash
mkdir my-node-app && cd my-node-app
```

```javascript
// app.js
const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({
    message: 'Hello from Docker!',
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  }));
});

server.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

```json
// package.json
{
  "name": "my-node-app",
  "version": "1.0.0",
  "main": "app.js",
  "scripts": {
    "start": "node app.js"
  }
}
```

### Step 2: Create a Dockerfile

```dockerfile
# Dockerfile

# Use Node.js 20 on Alpine Linux as the base image
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json first (for better layer caching)
COPY package.json .

# Install dependencies
RUN npm install --production

# Copy the rest of the application code
COPY . .

# Document that the app uses port 3000
EXPOSE 3000

# Define the command to run the application
CMD ["node", "app.js"]
```

### Step 3: Build the Image

```bash
# Command: Build an image from a Dockerfile
docker build -t my-node-app:1.0 .

# Flags:
# -t my-node-app:1.0  → Tag the image with name:version
# .                    → Build context (current directory)
#                        All files in this directory are sent to the daemon

# Output:
# [+] Building 15.2s (10/10) FINISHED
#  => [internal] load build definition from Dockerfile           0.0s
#  => [internal] load .dockerignore                              0.0s
#  => [internal] load metadata for docker.io/library/node:20-alpine  1.2s
#  => [1/5] FROM docker.io/library/node:20-alpine@sha256:...    3.5s
#  => [2/5] WORKDIR /app                                        0.1s
#  => [3/5] COPY package.json .                                 0.0s
#  => [4/5] RUN npm install --production                        8.3s
#  => [5/5] COPY . .                                            0.0s
#  => exporting to image                                        0.5s
#  => => naming to docker.io/library/my-node-app:1.0            0.0s

# MEANING: Each step corresponds to a Dockerfile instruction.
# Steps are numbered [1/5], [2/5], etc.
# Each step creates a cached layer.
```

### Step 4: Run the Image

```bash
docker run -d -p 3000:3000 --name my-app my-node-app:1.0

# Test it:
curl http://localhost:3000
# Output: {"message":"Hello from Docker!","hostname":"abc123def","timestamp":"2024-01-15T12:00:00.000Z"}
```

---

## 3.9 The .dockerignore File

Like `.gitignore`, `.dockerignore` prevents files from being sent to the build context.

```bash
# .dockerignore

node_modules          # Don't send local node_modules (we install fresh in container)
npm-debug.log
.git                  # Git history not needed in image
.gitignore
Dockerfile            # The Dockerfile itself isn't needed inside the image
.dockerignore
.env                  # NEVER include secrets in images
*.md                  # Documentation not needed at runtime
.vscode               # IDE config
coverage              # Test coverage reports
tests                 # Test files (for production images)
```

**Why this matters:**

```bash
# Without .dockerignore:
# Build context sent to daemon: 500MB (includes node_modules, .git, etc.)
# Build time: 30 seconds

# With .dockerignore:
# Build context sent to daemon: 5KB
# Build time: 3 seconds

# The build context is everything in the directory you specify with "."
# It's sent over the network to the Docker daemon.
# Smaller context = faster builds.
```

---

## 3.10 Image Tagging Strategies

```bash
# Tag an existing image with a new name
docker tag my-node-app:1.0 my-node-app:latest

# MEANING: Creates a new reference to the same image.
# The image is NOT duplicated — both tags point to the same layers.

# Tag for a private registry
docker tag my-node-app:1.0 registry.example.com/my-node-app:1.0

# View all tags for an image
docker images my-node-app
# Output:
# REPOSITORY    TAG      IMAGE ID       SIZE
# my-node-app   1.0      abc123def456   180MB
# my-node-app   latest   abc123def456   180MB
# Note: Same IMAGE ID — they're the same image with different tags
```

### Industry Tagging Best Practices

```bash
# Semantic versioning
my-app:1.0.0          # Specific version
my-app:1.0            # Minor version (points to latest patch)
my-app:1              # Major version (points to latest minor)
my-app:latest         # Latest stable release

# Git-based tagging
my-app:sha-abc123f    # Git commit SHA (immutable, traceable)
my-app:main           # Branch name
my-app:pr-42          # Pull request number

# Environment-based
my-app:staging        # Staging deployment
my-app:production     # Production deployment

# Date-based
my-app:2024-01-15     # Build date
my-app:20240115-1     # Date + build number

# Recommended: Combine approaches
my-app:1.2.3-sha-abc123f
# Version + commit = traceable and semantic
```

---

## 3.11 Docker Hub and Registries

### Docker Hub (Public Registry)

```bash
# Step 1: Create account at https://hub.docker.com

# Step 2: Login from CLI
docker login

# Output:
# Login with your Docker ID to push and pull images from Docker Hub.
# Username: yourusername
# Password:
# Login Succeeded

# Step 3: Tag image for Docker Hub
docker tag my-node-app:1.0 yourusername/my-node-app:1.0

# Step 4: Push to Docker Hub
docker push yourusername/my-node-app:1.0

# Output:
# The push refers to repository [docker.io/yourusername/my-node-app]
# 5f70bf18a086: Pushed
# a3ed95caeb02: Pushed
# ...
# 1.0: digest: sha256:abc123... size: 1234

# Step 5: Anyone can now pull your image
docker pull yourusername/my-node-app:1.0
```

### Private Registries

```bash
# AWS ECR (Elastic Container Registry)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag my-app:1.0 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:1.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:1.0

# Google GCR (Google Container Registry)
gcloud auth configure-docker
docker tag my-app:1.0 gcr.io/my-project/my-app:1.0
docker push gcr.io/my-project/my-app:1.0

# GitHub Container Registry (GHCR)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag my-app:1.0 ghcr.io/myorg/my-app:1.0
docker push ghcr.io/myorg/my-app:1.0

# Self-hosted registry
docker run -d -p 5000:5000 --name registry registry:2
docker tag my-app:1.0 localhost:5000/my-app:1.0
docker push localhost:5000/my-app:1.0
```

### Registry Types — Public vs Private

```
┌─────────────────────────────────────────────────────────────────┐
│                    REGISTRY TYPES                                │
│                                                                  │
│  PUBLIC REGISTRIES                                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Docker Hub (hub.docker.com)                              │   │
│  │  • Default registry for Docker                           │   │
│  │  • Official images (nginx, python, node, postgres)       │   │
│  │  • Community images (varying trust levels)               │   │
│  │  • Free tier: 1 private repo, unlimited public           │   │
│  │                                                           │   │
│  │  GitHub Container Registry (ghcr.io)                     │   │
│  │  • Integrated with GitHub repos and Actions              │   │
│  │                                                           │   │
│  │  Quay.io (Red Hat)                                       │   │
│  │  • Open-source registry with security scanning           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  PRIVATE REGISTRIES (Enterprise)                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Cloud-managed:                                           │   │
│  │  • AWS ECR (Elastic Container Registry)                  │   │
│  │  • Azure ACR (Azure Container Registry)                  │   │
│  │  • Google Artifact Registry (GAR)                        │   │
│  │                                                           │   │
│  │  Self-hosted:                                             │   │
│  │  • Harbor (CNCF project, enterprise features)            │   │
│  │  • JFrog Artifactory                                     │   │
│  │  • Sonatype Nexus                                        │   │
│  │  • GitLab Container Registry                             │   │
│  │  • Docker Registry (official, minimal)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Why use private registries?                                    │
│  • Control who can access your images                          │
│  • Enforce scanning and approval policies                      │
│  • Faster pulls (closer to your infrastructure)                │
│  • Compliance requirements (data residency)                    │
│  • No rate limits (Docker Hub has pull rate limits)             │
└─────────────────────────────────────────────────────────────────┘
```

### "What If the Image Has Malware?" — Image Security

This is a real concern. Anyone can push an image to Docker Hub. Not all images are trustworthy.

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE SECURITY RISKS                            │
│                                                              │
│  ❌ Malicious images on public registries                   │
│     • Cryptominers hidden in base images                    │
│     • Backdoors in "helpful" community images               │
│     • Typosquatting (ngnix instead of nginx)                │
│                                                              │
│  ❌ Known vulnerabilities (CVEs) in base images             │
│     • Outdated OpenSSL, glibc, curl, etc.                   │
│     • Unpatched OS packages                                 │
│                                                              │
│  ❌ Secrets baked into images                               │
│     • API keys, passwords in environment variables          │
│     • SSH keys copied during build                          │
│     • .env files included accidentally                      │
└─────────────────────────────────────────────────────────────┘
```

**Best practices to avoid bad images:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Practice                        │ Why                          │
├──────────────────────────────────┼──────────────────────────────┤
│  Use Official Images             │ Maintained by Docker and     │
│  (marked "Docker Official Image")│ upstream projects            │
├──────────────────────────────────┼──────────────────────────────┤
│  Use Verified Publishers         │ Companies verified by Docker │
│  (marked with checkmark)         │ (Bitnami, Canonical, etc.)  │
├──────────────────────────────────┼──────────────────────────────┤
│  Use private registry with       │ Only approved images can     │
│  approval workflows              │ be deployed                  │
├──────────────────────────────────┼──────────────────────────────┤
│  Scan images for vulnerabilities │ Catch CVEs before deployment │
├──────────────────────────────────┼──────────────────────────────┤
│  Sign images and enforce         │ Verify image hasn't been     │
│  signature verification          │ tampered with                │
├──────────────────────────────────┼──────────────────────────────┤
│  Use minimal base images         │ Fewer packages = fewer       │
│  (alpine, distroless, slim)      │ potential vulnerabilities    │
├──────────────────────────────────┼──────────────────────────────┤
│  Pin image versions              │ Don't use :latest in prod    │
│  (nginx:1.25.3, not nginx:latest)│ — know exactly what runs    │
└──────────────────────────────────┴──────────────────────────────┘
```

**Practical tools for image security:**

```bash
# ─── SCANNING FOR VULNERABILITIES ────────────────────────

# Docker Scout (built into Docker Desktop)
$ docker scout cves nginx:latest

# Output:
    ✗ HIGH 3
    ✗ MEDIUM 12
    ✗ LOW 8
    ✗ UNSPECIFIED 2

# Trivy (open-source, widely used in CI/CD)
$ trivy image nginx:latest

# Output:
nginx:latest (debian 12.4)
Total: 25 (UNKNOWN: 0, LOW: 8, MEDIUM: 12, HIGH: 3, CRITICAL: 2)

┌──────────────┬──────────────────┬──────────┬───────────────┬─────────────────┐
│ Library      │ Vulnerability    │ Severity │ Installed Ver │ Fixed Version   │
├──────────────┼──────────────────┼──────────┼───────────────┼─────────────────┤
│ libcurl4     │ CVE-2024-2398    │ HIGH     │ 7.88.1-10+d12 │ 7.88.1-10+d12u1│
│ openssl      │ CVE-2024-0727    │ MEDIUM   │ 3.0.11-1      │ 3.0.13-1       │
│ zlib1g       │ CVE-2023-45853   │ CRITICAL │ 1:1.2.13      │ 1:1.2.13.1     │
└──────────────┴──────────────────┴──────────┴───────────────┴─────────────────┘

# Grype (another popular scanner)
$ grype nginx:latest

# ─── IMAGE SIGNING ───────────────────────────────────────

# Cosign (sigstore project — industry standard)
# Sign an image
$ cosign sign --key cosign.key myregistry/myapp:1.0

# Verify a signed image
$ cosign verify --key cosign.pub myregistry/myapp:1.0

# Verified OK

# ─── POLICY ENFORCEMENT IN CI/CD ────────────────────────
# Block deployment of unscanned or vulnerable images
# Example: GitHub Actions step
# - name: Scan image
#   run: trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:${{ github.sha }}
#   # Pipeline FAILS if HIGH or CRITICAL CVEs found
```

**Checking if an image is official on Docker Hub:**

```bash
$ docker search nginx --filter is-official=true

NAME    DESCRIPTION                                     STARS   OFFICIAL
nginx   Official build of Nginx.                        19000   [OK]

# The [OK] in OFFICIAL column means it's an official image
# Official images are reviewed and maintained by Docker + upstream maintainers
```

---

## 3.12 Searching for Images

```bash
# Search Docker Hub from CLI
docker search nginx

# Output:
# NAME                    DESCRIPTION                                     STARS   OFFICIAL
# nginx                   Official build of Nginx.                        19000   [OK]
# bitnami/nginx           Bitnami container image for NGINX               180
# nginxproxy/nginx-proxy   Automated nginx proxy for Docker containers    100
# ...

# Filter by stars
docker search --filter stars=100 nginx

# Filter official images only
docker search --filter is-official=true nginx

# Limit results
docker search --limit 5 nginx
```

---

## 3.13 Saving and Loading Images (Offline Transfer)

```bash
# Save an image to a tar file
docker save -o my-app.tar my-node-app:1.0

# MEANING: Exports the image (all layers) to a tar archive.
# Useful for transferring images to air-gapped environments.

# Check the file
ls -lh my-app.tar
# Output: -rw------- 1 user user 180M Jan 15 12:00 my-app.tar

# Load an image from a tar file
docker load -i my-app.tar

# Output:
# Loaded image: my-node-app:1.0

# MEANING: Imports the image into the local Docker daemon.
# The image is now available as if it was pulled from a registry.
```

```bash
# Export a CONTAINER's filesystem (not an image — no layer info)
docker export my-container > container-fs.tar

# Import a filesystem as an image
docker import container-fs.tar my-imported-image:1.0

# Difference:
# docker save/load  → Preserves layers, metadata, tags (for images)
# docker export/import → Flat filesystem snapshot (for containers)
```

---

## 3.14 Real-World Industry Example: Multi-Stage Build for a Go API

```dockerfile
# Dockerfile for a Go REST API (production-grade)

# ─── Stage 1: Build ─────────────────────────────
FROM golang:1.22-alpine AS builder

# Install git (needed for go mod download with private repos)
RUN apk add --no-cache git

WORKDIR /app

# Copy go.mod and go.sum first (dependency caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary
# CGO_ENABLED=0: Static binary (no C dependencies)
# -ldflags="-s -w": Strip debug info (smaller binary)
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

# ─── Stage 2: Runtime ───────────────────────────
FROM alpine:3.19

# Add CA certificates (for HTTPS calls) and timezone data
RUN apk --no-cache add ca-certificates tzdata

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy ONLY the binary from the build stage
COPY --from=builder /app/server .

# Switch to non-root user
USER appuser

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

CMD ["./server"]

# Result:
# Build stage image: ~800MB (Go compiler, source code, dependencies)
# Final image: ~15MB (just the binary + Alpine)
# The build stage is discarded — only the final stage becomes the image.
```

```bash
# Build it
docker build -t go-api:1.0 .

# Check the size
docker images go-api
# REPOSITORY   TAG   IMAGE ID       SIZE
# go-api       1.0   abc123def456   15.2MB

# Compare with single-stage build:
# go-api-single  1.0   xyz789...   823MB
# 
# Multi-stage reduced the image from 823MB to 15MB!
```

---

## 3.15 Common Errors and Troubleshooting

### Error 1: COPY Failed — File Not Found
```bash
$ docker build -t myapp .
# COPY failed: file not found in build context or excluded by .dockerignore

# CAUSE 1: File doesn't exist in the build context directory
# CAUSE 2: File is excluded by .dockerignore

# Fix: Check your .dockerignore and verify the file exists
cat .dockerignore
ls -la  # Verify the file is in the current directory
```

### Error 2: Build Context Too Large
```bash
$ docker build -t myapp .
# Sending build context to Docker daemon  2.5GB

# CAUSE: Large files (node_modules, .git, data files) in build context

# Fix: Create or update .dockerignore
echo "node_modules" >> .dockerignore
echo ".git" >> .dockerignore
echo "*.tar.gz" >> .dockerignore
```

### Error 3: Layer Cache Not Working
```bash
# Symptom: Every build re-runs npm install even when dependencies haven't changed

# BAD Dockerfile (cache breaks on ANY code change):
COPY . .
RUN npm install

# GOOD Dockerfile (cache preserved when only code changes):
COPY package.json package-lock.json ./
RUN npm install
COPY . .

# WHY: Docker invalidates cache for a layer and ALL subsequent layers
# when the input changes. By copying package.json first, npm install
# is only re-run when dependencies actually change.
```

### Error 4: Image Won't Push — Access Denied
```bash
$ docker push my-app:1.0
# denied: requested access to the resource is denied

# CAUSE: Image name doesn't match your Docker Hub username

# Fix: Tag with your username
docker tag my-app:1.0 yourusername/my-app:1.0
docker push yourusername/my-app:1.0
```

### Error 5: Platform Mismatch (ARM vs x86)
```bash
$ docker run my-app:1.0
# WARNING: The requested image's platform (linux/amd64) does not match
# the detected host platform (linux/arm64/v8)

# CAUSE: Image was built on x86 machine, running on ARM (e.g., Apple Silicon Mac)

# Fix: Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t my-app:1.0 .

# Or specify platform when running
docker run --platform linux/amd64 my-app:1.0
```

---

## 3.16 Interview Key Points — Images and Image Creation

```
┌──────────────────────────────────────────────────────────────┐
│  IMAGE CREATION INTERVIEW QUESTIONS AND ANSWERS              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: What is a Docker image?                                 │
│  A: A read-only template containing application code,       │
│     runtime, libraries, and configuration. It's built in    │
│     layers and uses the host kernel at runtime.             │
│                                                              │
│  Q: How do you create a Docker image from a container?      │
│  A: Run a container, make changes (install software, create │
│     files), then run: docker commit container-name image:tag│
│     This saves the container's filesystem as a new image.   │
│                                                              │
│  Q: What are image layers?                                  │
│  A: Each image is a stack of read-only filesystem layers.   │
│     Each layer represents a change (install, copy, config). │
│     Layers are cached and shared between images that use    │
│     the same base, saving disk space and download time.     │
│                                                              │
│  Q: What is Copy-on-Write (CoW)?                            │
│  A: When a container modifies a file from an image layer,   │
│     Docker copies that file to the container's writable     │
│     layer first. The original image layer is never changed. │
│                                                              │
│  Q: Why is docker commit not recommended for production?    │
│  A: It's not reproducible — you can't audit what changed.   │
│     Dockerfiles are declarative, version-controlled, and    │
│     can be reviewed and automated in CI/CD pipelines.       │
│                                                              │
│  Q: What is the difference between docker save and export?  │
│  A: docker save exports an IMAGE (preserves layers and      │
│     metadata). docker export exports a CONTAINER's          │
│     filesystem (flat snapshot, no layer info).              │
│                                                              │
│  Q: How do you reduce Docker image size?                    │
│  A: Use multi-stage builds, Alpine/slim base images,        │
│     .dockerignore, combine RUN commands to reduce layers,   │
│     and avoid installing unnecessary packages.              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Module 3 Summary

- Images are read-only templates built in layers
- Image naming: `registry/repository:tag`
- **Image creation workflow**: Pull base image → run container → make changes → `docker commit` → new image
- **docker commit**: Saves a container's current filesystem state as a new image (good for learning, not production)
- **Dockerfile**: Automated, reproducible, version-controlled way to build images (use for production)
- **Image layers**: Each instruction creates a read-only layer; layers are shared between images with the same base
- **Copy-on-Write**: Containers modify files by copying them to the writable layer; image layers are never changed
- Use `-slim` or `-alpine` variants for smaller images
- `.dockerignore` reduces build context size and prevents secrets from leaking
- `docker build -t name:tag .` builds an image from a Dockerfile
- `docker push/pull` transfers images to/from registries
- Multi-stage builds dramatically reduce final image size
- Tag images with semantic versions + git SHA for traceability
- `docker save/load` for offline image transfer

---

**Next Module: [Module 4 - Docker Containers](module-04-containers.md)**
