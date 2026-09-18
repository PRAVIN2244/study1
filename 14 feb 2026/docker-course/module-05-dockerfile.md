# Module 5: Dockerfile Deep Dive — Every Instruction Explained

---

## 5.1 Why Automate Image Creation? — The Problem with Manual Builds

### Manual Method Recap (docker commit)

In the previous module, you learned to create images manually:

```
┌─────────────────────────────────────────────────────────────┐
│              MANUAL IMAGE CREATION (docker commit)           │
│                                                              │
│  Step 1: Pick a base image (CentOS, Ubuntu, Alpine...)      │
│  Step 2: Create a container from it                         │
│  Step 3: Enter the container                                │
│  Step 4: Run commands manually:                             │
│          - apt-get update                                   │
│          - apt-get install vim curl git                     │
│          - create config files                              │
│          - set up application                               │
│  Step 5: Exit the container                                 │
│  Step 6: docker commit → new image                          │
│                                                              │
│  ✅ Works for learning and quick experiments                │
│  ❌ But in real projects, this approach fails:              │
│                                                              │
│  Problem 1: Many steps (20–50+ commands in real apps)       │
│  Problem 2: Need to rebuild frequently (every CI build)     │
│  Problem 3: Manual steps are slow + error-prone             │
│  Problem 4: Not repeatable — "works on my machine"          │
│  Problem 5: No version control — can't review changes       │
│  Problem 6: No audit trail — what was installed and why?    │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Flow: Why Docker Images Are the Deliverable

In modern organizations, the build pipeline doesn't just produce a `.jar` or `.war` file — it produces a **Docker image**:

```
┌─────────────────────────────────────────────────────────────┐
│              TRADITIONAL vs DOCKER DELIVERY                   │
│                                                              │
│  Traditional pipeline output:                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Source Code → Build → app.jar / app.war             │   │
│  │  Then: Install Java, configure server, deploy jar    │   │
│  │  Problem: "It works on my machine but not in prod"   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Docker pipeline output:                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Source Code → Build → app-image:1.0                 │   │
│  │  Then: docker run app-image:1.0                      │   │
│  │  Result: Same environment everywhere                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  QA runs:   docker run app-image:1.0                        │
│  Staging:   docker run app-image:1.0                        │
│  Prod:      docker run app-image:1.0                        │
│                                                              │
│  No installation, no configuration, consistent everywhere.  │
└─────────────────────────────────────────────────────────────┘
```

### The Solution: Dockerfile

Instead of running commands manually inside a container, you write them in a **Dockerfile** — a text file that Docker reads and executes automatically.

```
┌─────────────────────────────────────────────────────────────┐
│  Manual (docker commit)          │ Automated (Dockerfile)    │
├──────────────────────────────────┼───────────────────────────┤
│  Enter container, type commands  │ Write commands in a file  │
│  Run docker commit               │ Run docker build          │
│  Not reproducible                │ Fully reproducible        │
│  Can't version control           │ Git-trackable             │
│  Slow for many steps             │ Fast (cached layers)      │
│  Error-prone                     │ Consistent every time     │
│  No audit trail                  │ Every step documented     │
│  Can't automate in CI/CD         │ Perfect for CI/CD         │
└──────────────────────────────────┴───────────────────────────┘
```

---

## 5.2 What is a Dockerfile?

A Dockerfile is a **plain text file** containing instructions that Docker uses to build an image automatically. No special editor needed — any text editor works.

### Format

```dockerfile
# Each line follows this pattern:
INSTRUCTION   arguments

# INSTRUCTION: keyword (usually UPPERCASE by convention)
# arguments:   command or value for that instruction

# Comments start with #
# Instructions are case-insensitive but UPPERCASE is convention
# Docker reads the file top to bottom, executing line by line
```

### Execution Behavior

```
┌─────────────────────────────────────────────────────────────┐
│              HOW DOCKER READS A DOCKERFILE                   │
│                                                              │
│  1. Docker reads the Dockerfile top to bottom               │
│  2. Executes each instruction one by one                    │
│  3. Each instruction creates a new layer in the image       │
│  4. If ANY step fails → build STOPS immediately             │
│     (no if/else, no error recovery, no skipping)            │
│  5. If all steps succeed → final image is created           │
│                                                              │
│  Dockerfile:                                                │
│  ┌────────────────────────┐                                 │
│  │ FROM centos            │ ← Step 1: set base image        │
│  │ RUN yum update -y      │ ← Step 2: run command           │
│  │ RUN yum install -y vim │ ← Step 3: run command           │
│  │ RUN touch /tmp/dummy   │ ← Step 4: run command           │
│  │ CMD ["/bin/bash"]      │ ← Step 5: set default command   │
│  └────────────────────────┘                                 │
│           │                                                  │
│           ▼                                                  │
│  docker build → executes each line → creates image          │
└─────────────────────────────────────────────────────────────┘
```

### Default File Name

```bash
# Docker expects the file to be named exactly:
Dockerfile

# No extension, capital D, lowercase ockerfile
# NOT: dockerfile, DockerFile, Dockerfile.txt

# If you want a different name, use -f flag:
$ docker build -t myimg:1.0 -f Dockerfile.dev .
$ docker build -t myimg:1.0 -f Dockerfile.prod .
$ docker build -t myimg:1.0 -f MyCustomFile .
```

---

## 5.3 The Core Dockerfile Instructions — FROM, RUN, CMD, ENTRYPOINT

### 5.3.1 FROM — The Base Image

Every Dockerfile **must** start with `FROM`. It defines the starting layer (base OS or base runtime).

```dockerfile
# Use an official image
FROM ubuntu:22.04

# Use a minimal image
FROM alpine:3.19

# Use a language-specific image
FROM node:20-alpine
FROM python:3.11-slim
FROM golang:1.22-alpine
FROM openjdk:21-slim

# Use scratch (empty image — for static binaries)
FROM scratch

# Multi-stage: name a stage
FROM node:20-alpine AS builder
```

```bash
# What FROM does:
# 1. Pulls the specified image from Docker Hub (if not cached locally)
# 2. Uses it as the first layer of your new image
# 3. All subsequent instructions build ON TOP of this layer

# Example:
FROM centos
# Meaning: "Start building this image using CentOS as the base layer."
# The CentOS image provides: /bin, /usr, /lib, /etc, yum package manager
# Your RUN commands can now use yum, bash, etc.
```

### Choosing the Right Base Image

```
┌──────────────────┬──────────┬────────────────────────────────────┐
│ Base Image       │ Size     │ When to Use                        │
├──────────────────┼──────────┼────────────────────────────────────┤
│ ubuntu:22.04     │ ~77MB    │ Need apt-get, full Linux tools     │
│ debian:bookworm  │ ~116MB   │ Stable, well-tested base           │
│ alpine:3.19      │ ~7MB     │ Smallest size, uses musl libc      │
│ scratch          │ 0MB      │ Static Go/Rust binaries only       │
│ distroless       │ ~2-20MB  │ No shell, no package manager       │
│                  │          │ (maximum security)                 │
│ node:20-slim     │ ~200MB   │ Node.js apps (production)          │
│ node:20-alpine   │ ~130MB   │ Node.js apps (smallest)            │
│ python:3.11-slim │ ~131MB   │ Python apps (production)           │
└──────────────────┴──────────┴────────────────────────────────────┘
```

### 5.3.2 RUN — Execute Commands During Build

`RUN` executes a command **during image build**, not when the container runs.

```dockerfile
# Each RUN creates a new layer in the image
RUN yum update -y
RUN yum install -y vim
RUN touch /tmp/dummy

# These commands run DURING BUILD:
# - Docker creates a temporary container
# - Executes the command inside it
# - Saves the result as a new layer
# - Removes the temporary container
```

#### Why -y Is Required in RUN Commands

```
┌─────────────────────────────────────────────────────────────┐
│              WHY -y IS REQUIRED                              │
│                                                              │
│  During docker build, there is NO interactive terminal.     │
│  Nobody is sitting at a keyboard to type "y" or "n".        │
│                                                              │
│  Without -y:                                                │
│  RUN yum install vim                                        │
│  → yum asks: "Is this ok [y/d/N]:"                         │
│  → Docker cannot answer                                     │
│  → Build HANGS or FAILS                                     │
│                                                              │
│  With -y:                                                   │
│  RUN yum install -y vim                                     │
│  → yum auto-confirms: "yes, install it"                     │
│  → Build continues                                          │
│                                                              │
│  Same for apt-get:                                          │
│  RUN apt-get install -y curl    ← -y = auto-confirm         │
│                                                              │
│  Same for any command that prompts for input:               │
│  Always use flags that skip interactive prompts.            │
└─────────────────────────────────────────────────────────────┘
```

### 5.3.3 CMD — Default Command When Container Starts

`CMD` sets the default command that runs when someone creates a container from your image **without specifying a command**.

```dockerfile
# Exec form (RECOMMENDED — proper signal handling)
CMD ["/bin/bash"]
CMD ["node", "app.js"]
CMD ["python", "main.py"]

# Shell form (runs via /bin/sh -c)
CMD node app.js
```

#### CMD Override Behavior

```bash
# Dockerfile:
# CMD ["/bin/bash"]

# Run WITHOUT specifying a command → CMD runs
$ docker run -it myimg:1.0
# Result: enters /bin/bash (the CMD)

# Run WITH a command → CMD is REPLACED
$ docker run -it myimg:1.0 sh
# Result: runs sh instead of /bin/bash

$ docker run -it myimg:1.0 echo "hello"
# Result: runs echo "hello" instead of /bin/bash

# KEY RULE: User-provided command REPLACES CMD entirely
```

### 5.3.4 ENTRYPOINT — Fixed Command + User Args Appended

`ENTRYPOINT` ensures a command **always runs**. Anything the user types becomes **arguments appended** to it.

```dockerfile
ENTRYPOINT ["echo", "Hi Adam"]
```

#### ENTRYPOINT Append Behavior

```bash
# Dockerfile:
# ENTRYPOINT ["echo", "Hi Adam"]

# Run WITHOUT args → ENTRYPOINT runs as-is
$ docker run myimg
# Output: Hi Adam

# Run WITH args → args are APPENDED to ENTRYPOINT
$ docker run myimg "Good morning"
# Output: Hi Adam Good morning

# Run WITH more args
$ docker run myimg "from" "Docker"
# Output: Hi Adam from Docker

# KEY RULE: User-provided text becomes ARGUMENTS to ENTRYPOINT
# The ENTRYPOINT command itself is NOT replaced
```

---

## 5.4 Complete Dockerfile Example — Manual Steps Automated

This Dockerfile automates the exact same steps you would do manually with `docker commit`:

```dockerfile
# Dockerfile — automates: CentOS + update + vim + dummy file

FROM centos
RUN yum update -y
RUN yum install -y vim
RUN touch /tmp/dummy
CMD ["/bin/bash"]
```

```
┌─────────────────────────────────────────────────────────────┐
│  Manual (docker commit)          │ Dockerfile equivalent     │
├──────────────────────────────────┼───────────────────────────┤
│  docker run -it centos bash      │ FROM centos               │
│  yum update -y                   │ RUN yum update -y         │
│  yum install -y vim              │ RUN yum install -y vim    │
│  touch /tmp/dummy                │ RUN touch /tmp/dummy      │
│  exit                            │ CMD ["/bin/bash"]         │
│  docker commit container myimg   │ docker build -t myimg .   │
├──────────────────────────────────┼───────────────────────────┤
│  5 manual steps                  │ 1 command: docker build   │
│  Not reproducible                │ Same result every time    │
└──────────────────────────────────┴───────────────────────────┘
```

---

## 5.5 Building an Image from a Dockerfile — docker build

### The Build Command

```bash
# Basic syntax
$ docker build -t myimg:1.0 .

# Breakdown:
# docker build    → "build an image from a Dockerfile"
# -t myimg:1.0    → tag/name the image (name:version)
# .               → build context (current directory — explained below)
```

### Build Output — What Each Line Means

```bash
$ docker build -t myimg:1.0 .

# Output:
Sending build context to Docker daemon  2.048kB

Step 1/5 : FROM centos
 ---> 5d0da3dc9764
# MEANING: Docker pulled/used the CentOS base image (layer ID: 5d0da3dc9764)

Step 2/5 : RUN yum update -y
 ---> Running in a1b2c3d4e5f6
# MEANING: Docker created a TEMPORARY container (a1b2c3d4e5f6)
#          and ran "yum update -y" inside it
Loaded plugins: fastestmirror, ovl
...
Complete!
 ---> 7f8g9h0i1j2k
Removing intermediate container a1b2c3d4e5f6
# MEANING: Command succeeded → saved result as layer 7f8g9h0i1j2k
#          → removed the temporary container

Step 3/5 : RUN yum install -y vim
 ---> Running in b2c3d4e5f6g7
...
Complete!
 ---> 8g9h0i1j2k3l
Removing intermediate container b2c3d4e5f6g7

Step 4/5 : RUN touch /tmp/dummy
 ---> Running in c3d4e5f6g7h8
 ---> 9h0i1j2k3l4m
Removing intermediate container c3d4e5f6g7h8

Step 5/5 : CMD ["/bin/bash"]
 ---> Running in d4e5f6g7h8i9
 ---> 0i1j2k3l4m5n
Removing intermediate container d4e5f6g7h8i9

Successfully built 0i1j2k3l4m5n
Successfully tagged myimg:1.0
```

### Why Docker Creates and Removes Temporary Containers

```
┌─────────────────────────────────────────────────────────────┐
│              TEMPORARY BUILD CONTAINERS                       │
│                                                              │
│  For each RUN instruction, Docker:                          │
│                                                              │
│  1. Creates a temporary container from the previous layer   │
│  2. Executes the command inside that container              │
│  3. Saves the container's filesystem as a new layer         │
│  4. Removes the temporary container                         │
│                                                              │
│  RUN yum update -y                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Create temp container → run command → save layer     │   │
│  │ → remove temp container                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  You don't keep these containers because your goal is       │
│  the FINAL IMAGE, not intermediate containers.              │
│                                                              │
│  The "Removing intermediate container" messages are normal. │
└─────────────────────────────────────────────────────────────┘
```

### Build Context — What the . Means

```bash
$ docker build -t myimg:1.0 .
#                              ^
#                              |
#                     BUILD CONTEXT = current directory
```

```
┌─────────────────────────────────────────────────────────────┐
│              BUILD CONTEXT                                    │
│                                                              │
│  The dot (.) means:                                         │
│  "Send the contents of the current directory to Docker"     │
│                                                              │
│  Why? Docker needs access to files you want to COPY         │
│  into the image. The build context is the set of files      │
│  Docker can access during the build.                        │
│                                                              │
│  Example directory:                                         │
│  my-project/                                                │
│  ├── Dockerfile                                             │
│  ├── app.js                                                 │
│  ├── package.json                                           │
│  └── config/                                                │
│      └── settings.json                                      │
│                                                              │
│  When you run: docker build -t myapp .                      │
│  Docker sends ALL these files to the Docker daemon.         │
│                                                              │
│  Then COPY instructions can reference them:                 │
│  COPY app.js /app/           ← looks in build context       │
│  COPY config/ /app/config/   ← looks in build context       │
│                                                              │
│  ⚠️  Large build contexts slow down builds!                 │
│  Use .dockerignore to exclude node_modules, .git, etc.      │
└─────────────────────────────────────────────────────────────┘
```

### Build Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER BUILD WORKFLOW                            │
│                                                              │
│  Dockerfile                                                 │
│  ┌────────────────────────┐                                 │
│  │ FROM centos            │──► Layer 1: Base OS (CentOS)    │
│  │ RUN yum update -y      │──► Layer 2: Updated packages    │
│  │ RUN yum install -y vim │──► Layer 3: vim installed       │
│  │ RUN touch /tmp/dummy   │──► Layer 4: dummy file created  │
│  │ CMD ["/bin/bash"]      │──► Metadata: default command    │
│  └────────────────────────┘                                 │
│           │                                                  │
│           ▼                                                  │
│  Final Image = Layer1 + Layer2 + Layer3 + Layer4 + Metadata │
│  Tagged as: myimg:1.0                                       │
│                                                              │
│  Each layer is:                                             │
│  - Read-only                                                │
│  - Cached (reused if Dockerfile hasn't changed)             │
│  - Shared between images with the same base                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.6 Docker Build Cache — Why Rebuilds Are Fast

### How Caching Works

Docker caches each step's layer. If the Dockerfile hasn't changed, Docker reuses existing layers instead of re-running commands.

```bash
# First build — takes time (downloads, installs, etc.)
$ docker build -t myimg:1.0 .
Step 1/5 : FROM centos
 ---> 5d0da3dc9764
Step 2/5 : RUN yum update -y
 ---> Running in a1b2c3d4e5f6
...
Complete!
 ---> 7f8g9h0i1j2k
Step 3/5 : RUN yum install -y vim
 ---> Running in b2c3d4e5f6g7
...
Complete!
 ---> 8g9h0i1j2k3l
Step 4/5 : RUN touch /tmp/dummy
 ---> 9h0i1j2k3l4m
Step 5/5 : CMD ["/bin/bash"]
 ---> 0i1j2k3l4m5n
Successfully built 0i1j2k3l4m5n
# Time: ~2 minutes

# Second build (same Dockerfile, no changes) — fraction of a second!
$ docker build -t myimg:1.0 .
Step 1/5 : FROM centos
 ---> Using cache
 ---> 5d0da3dc9764
Step 2/5 : RUN yum update -y
 ---> Using cache                    ← CACHED! Not re-run
 ---> 7f8g9h0i1j2k
Step 3/5 : RUN yum install -y vim
 ---> Using cache                    ← CACHED! Not re-run
 ---> 8g9h0i1j2k3l
Step 4/5 : RUN touch /tmp/dummy
 ---> Using cache                    ← CACHED! Not re-run
 ---> 9h0i1j2k3l4m
Step 5/5 : CMD ["/bin/bash"]
 ---> Using cache                    ← CACHED! Not re-run
 ---> 0i1j2k3l4m5n
Successfully built 0i1j2k3l4m5n
# Time: <1 second
```

### Cache Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER BUILD CACHE                              │
│                                                              │
│  Dockerfile lines → Image layers (cached)                   │
│                                                              │
│  FROM centos            → Layer 1 (base)     ← cached       │
│  RUN yum update -y      → Layer 2            ← cached       │
│  RUN yum install -y vim → Layer 3            ← cached       │
│  RUN touch /tmp/dummy   → Layer 4            ← cached       │
│                                                              │
│  If Dockerfile doesn't change → ALL layers reused           │
│  Build completes in < 1 second                              │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  CACHE INVALIDATION:                                        │
│  If you change Line 3, Docker:                              │
│  - Reuses Layer 1, Layer 2 (unchanged)                      │
│  - Rebuilds Layer 3 (changed)                               │
│  - Rebuilds Layer 4 (everything AFTER the change)           │
│                                                              │
│  Rule: A change invalidates that layer AND all layers below │
│  That's why you put rarely-changing steps FIRST             │
│  (e.g., install dependencies before copying source code)    │
└─────────────────────────────────────────────────────────────┘
```

### Forcing a Fresh Build (No Cache)

```bash
# Skip cache entirely — rebuild everything from scratch
$ docker build --no-cache -t myimg:1.0 .

# Useful when:
# - Package repositories have updated
# - You want to ensure a clean build
# - Debugging cache-related issues
```

### Clearing Build Cache

```bash
# See how much cache is used
$ docker system df
TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
Build Cache     15      0        500MB     500MB (100%)

# Clear build cache
$ docker builder prune

# Clear everything unused (images, containers, cache)
$ docker system prune -a
```

---

## 5.7 Image Name and Tag Behavior

### Can Two Images Have the Same Name?

**No** — a tag (name:version) points to exactly one image ID at a time.

```bash
# Build an image
$ docker build -t myimg:latest .
# myimg:latest → points to image ID a1b2c3d4

# Rebuild with the same tag
$ docker build -t myimg:latest .
# myimg:latest → NOW points to image ID e5f6g7h8

# The tag MOVED to the new image.
# The old image (a1b2c3d4) still exists but is now UNTAGGED (dangling).

$ docker images
# REPOSITORY   TAG      IMAGE ID       CREATED          SIZE
# myimg        latest   e5f6g7h8       5 seconds ago    230MB
# <none>       <none>   a1b2c3d4       2 minutes ago    230MB
#                       ^^^^^^^^
#                       Old image — now "dangling" (no tag)
```

### Keeping Multiple Versions

```bash
# Use different tags to keep both images
$ docker build -t myimg:1.0 .
$ docker build -t myimg:1.1 .

$ docker images myimg
# REPOSITORY   TAG   IMAGE ID       CREATED          SIZE
# myimg        1.1   e5f6g7h8       5 seconds ago    230MB
# myimg        1.0   a1b2c3d4       2 minutes ago    230MB

# Both images exist with their own tags
```

### Cleaning Up Dangling Images

```bash
# List dangling images (untagged)
$ docker images -f dangling=true
# REPOSITORY   TAG     IMAGE ID       SIZE
# <none>       <none>  a1b2c3d4       230MB

# Remove all dangling images
$ docker image prune

# Remove ALL unused images (not just dangling)
$ docker image prune -a
```

---

## 5.8 Listing and Verifying Built Images

```bash
# List all images
$ docker images

# Output:
# REPOSITORY   TAG     IMAGE ID       CREATED          SIZE
# myimg        1.0     a1b2c3d4e5     2 minutes ago    230MB
# centos       latest  5f6g7h8i9j     2 weeks ago      204MB

# Filter by name
$ docker images myimg
# REPOSITORY   TAG   IMAGE ID       CREATED          SIZE
# myimg        1.0   a1b2c3d4e5     2 minutes ago    230MB

# See image history (layers)
$ docker history myimg:1.0
# IMAGE          CREATED          CREATED BY                                      SIZE
# a1b2c3d4e5     2 minutes ago    /bin/sh -c touch /tmp/dummy                     0B
# 7f8g9h0i1j     2 minutes ago    /bin/sh -c yum install -y vim                   60MB
# 3k4l5m6n7o     3 minutes ago    /bin/sh -c yum update -y                        30MB
# 5d0da3dc97     2 weeks ago      /bin/sh -c #(nop) CMD ["/bin/bash"]             0B
# <missing>      2 weeks ago      /bin/sh -c #(nop) ADD file:... in /             204MB

# Inspect image details
$ docker inspect myimg:1.0

# Check total disk usage
$ docker system df
```

---

## 5.9 Running a Container from Your Built Image

```bash
# If CMD is set to ["/bin/bash"] in the Dockerfile:

# Run with default CMD → enters bash
$ docker run -it myimg:1.0
root@abc123:/# which vim
/usr/bin/vim
root@abc123:/# ls /tmp/dummy
/tmp/dummy
root@abc123:/# exit

# Override CMD → runs sh instead
$ docker run -it myimg:1.0 sh
sh-4.4# exit

# Override CMD → runs a specific command
$ docker run myimg:1.0 echo "Hello from my image"
Hello from my image

# Run in detached mode
$ docker run -d --name mycontainer myimg:1.0 sleep infinity
```

---

## 5.10 WORKDIR — Set Working Directory

### Purpose

`WORKDIR` sets the working directory inside the container. It's equivalent to `cd`, but it **persists across layers**. If the directory doesn't exist, Docker creates it automatically.

```dockerfile
# Syntax
WORKDIR /path

# Set the working directory
WORKDIR /app

# All following RUN, CMD, COPY, ADD commands execute relative to /app
# If the directory doesn't exist, it's created automatically
```

### Practical Example

```dockerfile
# Dockerfile
FROM ubuntu
WORKDIR /app
RUN touch testfile
CMD ["bash"]
```

```bash
# Build and run
$ docker build -t workdirdemo .
$ docker run -it workdirdemo

root@abc123:/app# pwd
/app

root@abc123:/app# ls
testfile

# testfile was created in /app because WORKDIR was set to /app
root@abc123:/app# exit
```

### WORKDIR vs cd

```dockerfile
# BAD: Using cd (doesn't persist across layers)
RUN cd /app && npm install
RUN node app.js    # ← This runs in /, NOT /app!
# Each RUN starts a new shell — cd is forgotten

# GOOD: Using WORKDIR (persists across all subsequent instructions)
WORKDIR /app
RUN npm install
RUN node app.js    # ← This runs in /app ✅
```

```
┌─────────────────────────────────────────────────────────────┐
│  WORKDIR /app                                               │
│     │                                                        │
│     ├── RUN touch file     → creates /app/file              │
│     ├── COPY src/ .        → copies to /app/src/            │
│     ├── RUN npm install    → runs in /app                   │
│     └── CMD ["node", "."]  → runs in /app                   │
│                                                              │
│  WORKDIR persists for ALL subsequent instructions           │
└─────────────────────────────────────────────────────────────┘
```

### Multiple WORKDIR

```dockerfile
# You can use WORKDIR multiple times — paths are relative
WORKDIR /app
WORKDIR src        # Now in /app/src
WORKDIR ../config  # Now in /app/config
```

---

## 5.11 COPY — Copy Files from Host to Image

### Purpose

`COPY` copies files from the **host machine** (build context) into the **image**.

```dockerfile
# Syntax
COPY source destination
COPY <host-path> <container-path>
```

### Practical Example

```bash
# On the host — create a file
$ echo "hello from host" > file.txt
```

```dockerfile
# Dockerfile
FROM ubuntu
COPY file.txt /app/file.txt
CMD ["bash"]
```

```bash
# Build and run
$ docker build -t copydemo .
$ docker run copydemo cat /app/file.txt
hello from host

# The file was copied from the host into the image during build
```

### Common COPY Patterns

```dockerfile
# Copy a single file
COPY package.json /app/package.json

# Copy to WORKDIR (if set)
WORKDIR /app
COPY package.json .          # Copies to /app/package.json

# Copy multiple files
COPY package.json package-lock.json ./

# Copy entire directory
COPY src/ /app/src/

# Copy with wildcard
COPY *.json /app/

# Copy and change ownership
COPY --chown=node:node . /app/

# Copy from a build stage (multi-stage builds)
COPY --from=builder /app/dist ./dist
```

---

## 5.12 ADD — Copy Files with Extra Features

### Purpose

`ADD` is similar to `COPY` but has two extra features:
1. **Auto-extracts tar archives** into the destination
2. **Can download from URLs** (not recommended)

### Tar Extraction Example

```bash
# On the host — create a tar archive
$ echo "file1 content" > file1.txt
$ echo "file2 content" > file2.txt
$ tar -cvf files.tar file1.txt file2.txt
file1.txt
file2.txt
```

```dockerfile
# Dockerfile
FROM ubuntu
ADD files.tar /app/
CMD ["bash"]
```

```bash
# Build and run
$ docker build -t adddemo .
$ docker run adddemo ls /app/
file1.txt
file2.txt

# The tar archive was automatically EXTRACTED into /app/
# With COPY, you'd get the tar file itself (not extracted)
```

### COPY vs ADD — When to Use Which

```
┌─────────────────────────────────────────────────────────────┐
│  COPY vs ADD                                                │
│                                                              │
│  COPY file.tar /app/     → /app/file.tar (raw file)        │
│  ADD  file.tar /app/     → /app/file1.txt, /app/file2.txt  │
│                             (auto-extracted!)               │
│                                                              │
│  Rule: Always use COPY unless you specifically need         │
│  tar extraction. ADD's implicit behavior can cause          │
│  surprises.                                                 │
│                                                              │
│  For downloading files, use RUN + curl instead of ADD:      │
│  ❌ ADD https://example.com/file.txt /app/                  │
│  ✅ RUN curl -o /app/file.txt https://example.com/file.txt │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.13 RUN — Execute Commands During Build (Reference)

```dockerfile
# Shell form (runs in /bin/sh -c)
RUN apt-get update && apt-get install -y curl

# Exec form (runs directly, no shell processing)
RUN ["apt-get", "update"]

# Multi-line command (use \ for readability)
RUN apt-get update && \
    apt-get install -y \
      curl \
      wget \
      vim \
    && rm -rf /var/lib/apt/lists/*

# IMPORTANT: Each RUN creates a new layer.
# Combine related commands to reduce layers.
```

### Layer Optimization

```dockerfile
# BAD: 3 layers, apt cache persists in layer 1
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
# Even though layer 3 deletes the cache, it still exists in layer 1!
# Image size includes ALL layers.

# GOOD: 1 layer, apt cache cleaned in same layer
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
# Cache is created and deleted in the same layer = smaller image
```

### DEBIAN_FRONTEND=noninteractive (Avoiding Interactive Prompts)

Some packages (like `tzdata`) prompt for user input during install. In a Dockerfile, there is no terminal to respond — the build hangs or fails.

```dockerfile
# BAD: may hang waiting for timezone selection
RUN apt-get update && apt-get install -y tzdata

# GOOD: suppress all interactive prompts
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      tzdata \
      apache2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

```
┌─────────────────────────────────────────────────────────────┐
│  DEBIAN_FRONTEND=noninteractive                             │
│                                                              │
│  What it does:                                              │
│    Tells apt-get to use default answers for all prompts     │
│    No timezone selection dialog                             │
│    No service restart confirmations                         │
│                                                              │
│  When to use:                                               │
│    Any Dockerfile that installs packages which normally     │
│    prompt for input (tzdata, keyboard-configuration, etc.)  │
│                                                              │
│  Set inline (preferred — does not persist in image):        │
│    RUN DEBIAN_FRONTEND=noninteractive apt-get install ...   │
│                                                              │
│  Avoid setting as ENV (persists and may cause issues):      │
│    ENV DEBIAN_FRONTEND=noninteractive  ← not recommended   │
└─────────────────────────────────────────────────────────────┘
```

### Complete Apache Dockerfile Example (Using All Best Practices)

```dockerfile
FROM ubuntu
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      tzdata \
      apache2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV APACHE_RUN_USER=www-data
ENV APACHE_RUN_GROUP=www-data
ENV APACHE_LOG_DIR=/var/log/apache2
ENV APACHE_RUN_DIR=/var/log/apache2
EXPOSE 80
CMD ["/usr/sbin/apache2", "-D", "FOREGROUND"]
```

```bash
$ docker build -t myapache:v1 -f Dockerfile.apache .
$ docker run --rm -d -p 80:80 myapache:v1
```

---

## 5.14 CMD — Default Command When Container Starts (Reference)

```dockerfile
# Exec form (RECOMMENDED — proper signal handling)
CMD ["node", "app.js"]
CMD ["python", "main.py"]
CMD ["nginx", "-g", "daemon off;"]

# Shell form (runs via /bin/sh -c)
CMD node app.js
# Problem: node runs as a child of sh, doesn't receive SIGTERM directly

# CMD can be overridden at runtime:
# Dockerfile: CMD ["node", "app.js"]
# docker run my-app node other-script.js  ← Overrides CMD
```

---

## 5.15 ENTRYPOINT — The Container's Main Executable (Reference)

```dockerfile
# Exec form
ENTRYPOINT ["python", "app.py"]

# ENTRYPOINT + CMD combination (most flexible pattern)
ENTRYPOINT ["python"]
CMD ["app.py"]

# docker run my-app              → python app.py
# docker run my-app test.py      → python test.py (CMD overridden)
# docker run --entrypoint bash my-app  → bash (ENTRYPOINT overridden)
```

### ENTRYPOINT vs CMD — When to Use Which

```
┌─────────────────────────────────────────────────────────────────┐
│ Pattern              │ Use Case                                 │
├──────────────────────┼──────────────────────────────────────────┤
│ CMD only             │ Default command, easily overridden       │
│                      │ Example: development images              │
│                      │ CMD ["npm", "start"]                     │
├──────────────────────┼──────────────────────────────────────────┤
│ ENTRYPOINT only      │ Container acts as an executable          │
│                      │ Example: CLI tools                       │
│                      │ ENTRYPOINT ["curl"]                      │
│                      │ docker run my-curl https://example.com   │
├──────────────────────┼──────────────────────────────────────────┤
│ ENTRYPOINT + CMD     │ Fixed executable with default arguments  │
│                      │ Example: web servers                     │
│                      │ ENTRYPOINT ["nginx"]                     │
│                      │ CMD ["-g", "daemon off;"]                │
└──────────────────────┴──────────────────────────────────────────┘
```

### Entrypoint Script Pattern (Industry Standard)

```bash
#!/bin/sh
# docker-entrypoint.sh

# Run database migrations before starting the app
echo "Running migrations..."
npx prisma migrate deploy

# Execute the CMD passed to the container
exec "$@"
```

```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node", "app.js"]

# Flow:
# 1. docker-entrypoint.sh runs
# 2. Migrations execute
# 3. exec "$@" replaces shell with "node app.js"
# 4. node becomes PID 1 (receives signals properly)
```

---

## 5.16 CMD vs ENTRYPOINT — Deep Dive with Full Examples

This is one of the **most asked Docker interview questions**. Understanding the difference requires seeing both in action.

### Example 1: CMD — Override Behavior

```dockerfile
# Dockerfile.cmd
FROM centos
CMD ["echo", "Hello"]
```

```bash
# Build the image
$ docker build -t cmd-demo -f Dockerfile.cmd .

# Run WITHOUT args → CMD runs
$ docker run cmd-demo
Hello

# Run WITH a command → CMD is COMPLETELY REPLACED
$ docker run cmd-demo echo "Bye"
Bye

# Run with a different command entirely
$ docker run cmd-demo cat /etc/os-release
CentOS Linux release 8...

# Run with shell
$ docker run -it cmd-demo bash
[root@abc123 /]#

# KEY: Whatever you type after the image name REPLACES the CMD
```

### Example 2: ENTRYPOINT — Append Behavior

```dockerfile
# Dockerfile.entry
FROM centos
ENTRYPOINT ["echo", "Hi Adam"]
```

```bash
# Build the image
$ docker build -t entry-demo -f Dockerfile.entry .

# Run WITHOUT args → ENTRYPOINT runs as-is
$ docker run entry-demo
Hi Adam

# Run WITH args → args are APPENDED to ENTRYPOINT
$ docker run entry-demo "Good morning"
Hi Adam Good morning

# More args
$ docker run entry-demo "from" "Docker" "class"
Hi Adam from Docker class

# KEY: ENTRYPOINT is NOT replaced — user input becomes additional arguments

# To override ENTRYPOINT, you must use --entrypoint flag:
$ docker run --entrypoint bash -it entry-demo
[root@abc123 /]#
```

### Example 3: ENTRYPOINT + CMD Together

```dockerfile
# Dockerfile.both
FROM centos
ENTRYPOINT ["echo"]
CMD ["Hello World"]
```

```bash
# Build
$ docker build -t both-demo -f Dockerfile.both .

# Run without args → ENTRYPOINT + CMD
$ docker run both-demo
Hello World
# Executed: echo "Hello World"

# Run with args → CMD is replaced, ENTRYPOINT stays
$ docker run both-demo "Goodbye"
Goodbye
# Executed: echo "Goodbye"

$ docker run both-demo "Hi" "there"
Hi there
# Executed: echo "Hi" "there"
```

### Comparison Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              CMD vs ENTRYPOINT BEHAVIOR                      │
│                                                              │
│  CMD ["echo", "Hello"]                                      │
│  ─────────────────────                                      │
│  docker run image              → echo Hello                 │
│  docker run image echo Bye     → echo Bye (CMD replaced)   │
│  docker run image bash         → bash (CMD replaced)       │
│                                                              │
│  ENTRYPOINT ["echo", "Hi"]                                  │
│  ─────────────────────────                                  │
│  docker run image              → echo Hi                    │
│  docker run image "Bye"        → echo Hi Bye (appended)    │
│  docker run image bash         → echo Hi bash (appended!)  │
│                                                              │
│  ENTRYPOINT ["echo"] + CMD ["Hello"]                        │
│  ────────────────────────────────────                       │
│  docker run image              → echo Hello                 │
│  docker run image "Bye"        → echo Bye (CMD replaced)   │
│  ENTRYPOINT stays, CMD provides default args                │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│  Interview answer:                                          │
│  CMD = "default command, user can replace it"               │
│  ENTRYPOINT = "fixed command, user input becomes arguments" │
│  Together = "fixed program with overridable default args"   │
└─────────────────────────────────────────────────────────────┘
```

### Real-World Scenario: Java Application with run.sh

This is the scenario that makes the difference clear in production.

Suppose you have a script `run.sh` that starts your Java application:

```bash
#!/bin/bash
# run.sh — starts the Java application
echo "Starting application with args: $@"
java -jar /app/myapp.jar "$@"
```

#### Using CMD — The Problem

```dockerfile
# Dockerfile.cmd-java
FROM ubuntu
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
CMD ["sh", "/app/run.sh"]
```

```bash
# Build
$ docker build -t java-cmd -f Dockerfile.cmd-java .

# Run normally → works fine
$ docker run java-cmd
Starting application with args:
(Java app starts)

# But if someone passes a command → run.sh DOES NOT execute
$ docker run java-cmd echo "Hello"
Hello
# ❌ run.sh was REPLACED by "echo Hello"
# The Java application never started!

# This is dangerous in production:
# Someone debugging might accidentally skip the app startup
$ docker run java-cmd bash
# ❌ Just opens bash — app never runs
```

#### Using ENTRYPOINT — The Solution

```dockerfile
# Dockerfile.entry-java
FROM ubuntu
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
ENTRYPOINT ["sh", "/app/run.sh"]
```

```bash
# Build
$ docker build -t java-entry -f Dockerfile.entry-java .

# Run normally → works fine
$ docker run java-entry
Starting application with args:
(Java app starts)

# Pass arguments → they become arguments to run.sh
$ docker run java-entry --profile=prod
Starting application with args: --profile=prod
(Java app starts with --profile=prod)

$ docker run java-entry --debug --port=9090
Starting application with args: --debug --port=9090
(Java app starts with those flags)

# ✅ The application ALWAYS starts
# ✅ User arguments are passed TO the application
# ✅ Cannot accidentally skip the app startup
```

```
┌─────────────────────────────────────────────────────────────┐
│  REAL-WORLD RULE:                                           │
│                                                              │
│  Use ENTRYPOINT when the container has ONE job:             │
│  - Run a Java app                                           │
│  - Run a Python service                                     │
│  - Run a database                                           │
│  - Run a web server                                         │
│                                                              │
│  Use CMD when the container is a general-purpose tool:      │
│  - Development environment                                  │
│  - Debugging container                                      │
│  - Base image for others to extend                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.17 Build Logs — Saving and Reviewing Build Output

During automated builds (CI/CD, nightly builds), you need to save build output for later review.

```bash
# Redirect build output to a log file
$ docker build -t myimg:1.0 . > build.log 2>&1

# Breakdown:
# >  build.log   → redirect stdout to file
# 2>&1           → redirect stderr to same file
# Result: all output (success + errors) saved to build.log

# Review the log later
$ cat build.log
$ less build.log
$ tail -20 build.log    # last 20 lines

# Search for errors in the log
$ grep -i "error\|fail" build.log
```

```bash
# Build with both console output AND log file (tee)
$ docker build -t myimg:1.0 . 2>&1 | tee build.log

# tee: shows output on screen AND saves to file simultaneously
# Useful during interactive builds where you want to watch progress
```

```bash
# Timestamped log file for nightly builds
$ docker build -t myimg:1.0 . > "build_$(date +%Y%m%d_%H%M%S).log" 2>&1

# Result: build_20250220_143000.log
```

---

## 5.18 Dockerfile Name and the -f Option

```bash
# Default: Docker looks for a file named exactly "Dockerfile"
$ docker build -t myimg:1.0 .
# Looks for: ./Dockerfile

# If your file has a different name, use -f:
$ docker build -t myimg:1.0 -f Dockerfile.dev .
$ docker build -t myimg:1.0 -f Dockerfile.prod .
$ docker build -t myimg:1.0 -f Dockerfile.test .
$ docker build -t myimg:1.0 -f docker/MyDockerfile .
```

```
┌─────────────────────────────────────────────────────────────┐
│              COMMON DOCKERFILE NAMING PATTERNS               │
│                                                              │
│  Dockerfile           ← Default (most common)               │
│  Dockerfile.dev       ← Development build                   │
│  Dockerfile.prod      ← Production build                    │
│  Dockerfile.test      ← Testing/CI build                    │
│  Dockerfile.alpine    ← Alpine-based variant                │
│                                                              │
│  Project structure example:                                 │
│  my-project/                                                │
│  ├── Dockerfile           ← default (production)            │
│  ├── Dockerfile.dev       ← development (with dev tools)    │
│  ├── docker/                                                │
│  │   ├── Dockerfile.api   ← API service                     │
│  │   └── Dockerfile.worker← Worker service                  │
│  ├── src/                                                   │
│  └── package.json                                           │
│                                                              │
│  Build commands:                                            │
│  docker build -t myapp:prod .                               │
│  docker build -t myapp:dev -f Dockerfile.dev .              │
│  docker build -t api:1.0 -f docker/Dockerfile.api .        │
│  docker build -t worker:1.0 -f docker/Dockerfile.worker .  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.19 ENV — Set Environment Variables

### Purpose

`ENV` sets environment variables inside the image. These variables are available in **all containers** created from the image — automatically, without passing `-e` at runtime.

```dockerfile
# Syntax
ENV VARIABLE_NAME value
ENV VARIABLE_NAME=value    # Both forms work

# Set a single variable
ENV NODE_ENV=production

# Set multiple variables
ENV NODE_ENV=production \
    PORT=3000 \
    LOG_LEVEL=info

# Use in subsequent instructions
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY . $APP_HOME

# Environment variables persist in the running container
# docker exec my-container env
# NODE_ENV=production
# PORT=3000
# LOG_LEVEL=info
```

### Practical Example: JAVA_HOME

```dockerfile
# Dockerfile
FROM ubuntu
ENV JAVA_HOME /usr/lib/jvm/java-11
CMD ["bash"]
```

```bash
# Build the image
$ docker build -t myjava .

# Run the container
$ docker run -it myjava

# Check the variable inside the container
root@abc123:/# echo $JAVA_HOME
/usr/lib/jvm/java-11

# It's automatically available — no -e flag needed
root@abc123:/# env | grep JAVA
JAVA_HOME=/usr/lib/jvm/java-11

root@abc123:/# exit
```

```
┌─────────────────────────────────────────────────────────────┐
│              ENV FLOW                                        │
│                                                              │
│  Dockerfile                                                 │
│  ┌──────────────────────────────────┐                       │
│  │ ENV JAVA_HOME /usr/lib/jvm/java  │                       │
│  └──────────────────────────────────┘                       │
│           │                                                  │
│           ▼ docker build                                    │
│  Image (JAVA_HOME stored in image metadata)                 │
│           │                                                  │
│           ▼ docker run                                      │
│  Container                                                  │
│  ┌──────────────────────────────────┐                       │
│  │ JAVA_HOME available automatically│                       │
│  │ echo $JAVA_HOME → /usr/lib/...  │                       │
│  └──────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Override ENV at Runtime

```bash
# ENV in Dockerfile sets the default
# You can override it when running the container:
$ docker run -it -e JAVA_HOME=/usr/lib/jvm/java-17 myjava

root@abc123:/# echo $JAVA_HOME
/usr/lib/jvm/java-17
# Overridden at runtime — Dockerfile default was java-11
```

---

## 5.20 ARG vs ENV — Build-Time vs Runtime Variables

This is a frequently asked interview question. The key difference: **ARG exists only during build, ENV persists into the container.**

### ARG — Build-Time Only

```dockerfile
# Dockerfile
FROM ubuntu
ARG VERSION=1.0
RUN echo $VERSION > /app/version.txt
CMD ["bash"]
```

```bash
# Build the image
$ docker build -t argdemo .

# Run the container — check the file
$ docker run argdemo cat /app/version.txt
1.0

# But the variable itself is NOT available in the container
$ docker run -it argdemo
root@abc123:/# echo $VERSION

# (empty — nothing printed!)
# ARG exists ONLY during build, not at runtime
root@abc123:/# exit
```

### Override ARG at Build Time

```bash
# Pass a different value during build
$ docker build --build-arg VERSION=2.5 -t argdemo:2.5 .

$ docker run argdemo:2.5 cat /app/version.txt
2.5
```

### Comparison Table

```
┌──────────────────────────────────────────────────────────────┐
│  Feature                    │ ENV              │ ARG          │
├─────────────────────────────┼──────────────────┼──────────────┤
│  Available during build     │ ✅ Yes           │ ✅ Yes       │
│  Available in container     │ ✅ Yes           │ ❌ No        │
│  Stored in image metadata   │ ✅ Yes           │ ❌ No        │
│  Used for runtime configs   │ ✅ Yes           │ ❌ No        │
│  Used for build-time configs│ ⚠️ Possible      │ ✅ Yes       │
│  Override at build time     │ ❌ No            │ ✅ --build-arg│
│  Override at runtime        │ ✅ -e flag       │ ❌ N/A       │
│  Visible in docker inspect  │ ✅ Yes           │ ❌ No        │
├─────────────────────────────┼──────────────────┼──────────────┤
│  Example use case           │ JAVA_HOME,       │ Base image   │
│                             │ NODE_ENV,        │ version,     │
│                             │ DATABASE_URL     │ build flags  │
└─────────────────────────────┴──────────────────┴──────────────┘
```

### Passing ARG to ENV (Common Pattern)

```dockerfile
# Make a build-time value available at runtime
FROM ubuntu
ARG APP_VERSION=1.0.0
ENV APP_VERSION=$APP_VERSION

# Now APP_VERSION is available both during build AND in the container
```

```bash
$ docker build --build-arg APP_VERSION=3.0 -t myapp:3.0 .
$ docker run myapp:3.0 bash -c 'echo $APP_VERSION'
3.0
```

---

## 5.21 EXPOSE — Document Container Ports

### Purpose

`EXPOSE` documents which port the application inside the container listens on. It does **NOT** publish the port — it's metadata only.

```dockerfile
# Document that the app listens on port 80
EXPOSE 80

# Multiple ports
EXPOSE 80 443

# UDP port
EXPOSE 53/udp
```

### EXPOSE Does NOT Publish the Port

```
┌─────────────────────────────────────────────────────────────┐
│              EXPOSE vs -p (PORT PUBLISHING)                  │
│                                                              │
│  EXPOSE 80 in Dockerfile:                                   │
│  - Documents "this container uses port 80"                  │
│  - Does NOT make port accessible from outside               │
│  - It's like a comment / documentation                      │
│                                                              │
│  -p 8080:80 at runtime:                                     │
│  - Actually PUBLISHES the port                              │
│  - Maps host port 8080 → container port 80                  │
│  - Makes the app accessible from outside                    │
│                                                              │
│  You MUST use -p to publish:                                │
│  docker run -p 8080:80 myimage                              │
│                                                              │
│  EXPOSE alone does nothing for connectivity.                │
│  But it's good practice — tells users which port to map.    │
└─────────────────────────────────────────────────────────────┘
```

### Example: Apache with EXPOSE

```dockerfile
# Dockerfile
FROM ubuntu
RUN apt-get update && apt-get install -y apache2
EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
```

```bash
# Build
$ docker build -t myapache .

# Run WITHOUT -p → port NOT accessible
$ docker run -d --name web1 myapache
# curl localhost:80 → connection refused

# Run WITH -p → port IS accessible
$ docker run -d -p 8080:80 --name web2 myapache
$ curl localhost:8080
# Apache welcome page HTML

# The EXPOSE instruction told us to map port 80
# But only -p actually made it work
```

---

## 5.22 VOLUME — Declare Mount Points

```dockerfile
# Declare a volume mount point
VOLUME /data

# Multiple volumes
VOLUME ["/data", "/logs"]

# MEANING: When a container runs, Docker creates an anonymous volume
# at this path. Data written here persists beyond container lifecycle.

# In practice, prefer named volumes at runtime:
# docker run -v my-data:/data my-app
```

---

## 5.23 USER — Set the Running User

### Purpose

`USER` defines which user runs commands. By default, everything runs as **root**. Switching to a non-root user is a security best practice.

```dockerfile
# Syntax
USER username
USER uid:gid
```

### File Ownership Demo

```dockerfile
# Dockerfile
FROM ubuntu
RUN touch /rootfile
USER nobody
RUN touch /tmp/nobodyfile
CMD ["bash"]
```

```bash
# Build and run
$ docker build -t userdemo .
$ docker run -it userdemo

# Check file ownership
nobody@abc123:/$ ls -l /rootfile
-rw-r--r-- 1 root root 0 Feb 20 12:00 /rootfile

nobody@abc123:/$ ls -l /tmp/nobodyfile
-rw-r--r-- 1 nobody nogroup 0 Feb 20 12:00 /tmp/nobodyfile

# rootfile was created BEFORE USER nobody → owned by root
# nobodyfile was created AFTER USER nobody → owned by nobody
nobody@abc123:/$ exit
```

```
┌─────────────────────────────────────────────────────────────┐
│              USER INSTRUCTION FLOW                           │
│                                                              │
│  USER root (default)                                        │
│     │                                                        │
│     ├── RUN touch /rootfile      → owned by root            │
│     ├── RUN apt-get install ...  → runs as root             │
│     │                                                        │
│  USER nobody                                                │
│     │                                                        │
│     ├── RUN touch /tmp/file      → owned by nobody          │
│     ├── CMD ["bash"]             → container runs as nobody │
│     │                                                        │
│  All commands AFTER USER run as that user                   │
└─────────────────────────────────────────────────────────────┘
```

### Override User at Runtime

```bash
# Dockerfile has USER nobody, but you need root access for debugging:
$ docker run -it -u root userdemo
root@abc123:/# whoami
root
# Overridden at runtime — useful for debugging permission issues

# Specify user by UID
$ docker run -it -u 1000 userdemo
```

### Production Pattern: Non-Root User

```dockerfile
# Full example: Node.js with non-root user
FROM node:20-alpine

# node:20-alpine already has a 'node' user (UID 1000)
WORKDIR /app

COPY --chown=node:node package*.json ./
RUN npm ci --production

COPY --chown=node:node . .

# Switch to non-root user
USER node

EXPOSE 3000
CMD ["node", "app.js"]

# WHY: Running as root inside a container is a security risk.
# If an attacker escapes the container, they could have root on the host.
# Always switch to a non-root user for production images.
```

---

## 5.24 HEALTHCHECK — Container Health Monitoring

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Options:
# --interval=30s      → Check every 30 seconds
# --timeout=5s        → Fail if check takes longer than 5 seconds
# --start-period=10s  → Wait 10 seconds before first check (app startup time)
# --retries=3         → Mark unhealthy after 3 consecutive failures

# For Alpine images (no curl by default):
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Disable health check (if base image has one)
HEALTHCHECK NONE
```

---

## 5.25 LABEL — Add Metadata

```dockerfile
# Add metadata to the image
LABEL maintainer="team@company.com"
LABEL version="1.0"
LABEL description="API service for user management"

# Multiple labels (compact)
LABEL maintainer="team@company.com" \
      version="1.0" \
      org.opencontainers.image.source="https://github.com/company/repo"

# OCI standard labels (industry convention)
LABEL org.opencontainers.image.title="My API"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="team@company.com"
LABEL org.opencontainers.image.source="https://github.com/company/repo"
LABEL org.opencontainers.image.created="2024-01-15T10:00:00Z"

# View labels
# docker inspect --format='{{json .Config.Labels}}' my-image
```

---

## 5.26 STOPSIGNAL — Custom Stop Signal

```dockerfile
# Default stop signal is SIGTERM
# Some apps need a different signal for graceful shutdown

STOPSIGNAL SIGQUIT    # Nginx uses SIGQUIT for graceful shutdown
STOPSIGNAL SIGINT     # Some apps prefer SIGINT (Ctrl+C)
```

---

## 5.27 SHELL — Change Default Shell

```dockerfile
# Default shell is ["/bin/sh", "-c"]
# Change to bash for better scripting support

SHELL ["/bin/bash", "-c"]

# Now RUN commands use bash
RUN echo "Using bash features: ${VARIABLE:-default}"

# Windows containers might use PowerShell
SHELL ["powershell", "-Command"]
```

---

## 5.28 The Problem with Normal Dockerfile Builds

Consider a Java application Dockerfile:

```dockerfile
FROM ubuntu

RUN apt-get update
RUN apt-get install -y openjdk-11-jdk

COPY App.java .

RUN javac App.java

CMD ["java", "App"]
```

```
┌─────────────────────────────────────────────────────────────┐
│              PROBLEM: LARGE IMAGE SIZE                       │
│                                                              │
│  This image contains:                                       │
│  ✅ Compiled App.class (what we need)                       │
│  ❌ Source code (App.java — not needed at runtime)          │
│  ❌ Java compiler (javac — not needed at runtime)           │
│  ❌ Build tools (apt, package cache)                        │
│  ❌ Full Ubuntu OS (unnecessary packages)                   │
│                                                              │
│  Result: Image size = ~900 MB                               │
│                                                              │
│  We only need the compiled .class file + Java runtime       │
│  to run the application. Everything else is waste.          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.29 What is a Multi-Stage Build?

Multi-stage builds **separate the build environment from the runtime environment**. Build happens in one stage, and the final image contains only what's needed to run.

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-STAGE BUILD CONCEPT                        │
│                                                              │
│  Stage 1: BUILD STAGE                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Base Image: openjdk (full JDK with compiler)        │   │
│  │  - Copy source code                                  │   │
│  │  - Compile application                               │   │
│  │  - Output: App.class                                 │   │
│  │  Size: ~900 MB                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                    │                                         │
│                    │ COPY --from=builder (only App.class)    │
│                    ▼                                         │
│  Stage 2: RUNTIME STAGE                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Base Image: alpine (minimal OS)                     │   │
│  │  - Copy ONLY compiled App.class from Stage 1         │   │
│  │  - No compiler, no source code, no build tools       │   │
│  │  Size: ~120 MB                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Final image = Stage 2 only (small and optimized)           │
│  Stage 1 is discarded after build                           │
└─────────────────────────────────────────────────────────────┘
```

### Simple Java Multi-Stage Example

```dockerfile
# Stage 1: Build stage
FROM openjdk:11 AS builder

WORKDIR /app

COPY App.java .

RUN javac App.java


# Stage 2: Runtime stage
FROM alpine

WORKDIR /app

COPY --from=builder /app/App.class .

CMD ["java", "App"]
```

```
┌─────────────────────────────────────────────────────────────┐
│  HOW THIS WORKS:                                            │
│                                                              │
│  Stage 1 (builder):                                         │
│  - Uses openjdk:11 (has javac compiler)                     │
│  - Copies App.java source code                              │
│  - Compiles: javac App.java → produces App.class            │
│  - This stage is ~900 MB                                    │
│                                                              │
│  Stage 2 (final):                                           │
│  - Uses alpine (minimal 5 MB OS)                            │
│  - COPY --from=builder copies ONLY App.class                │
│  - No compiler, no source code included                     │
│  - This stage is ~120 MB                                    │
│                                                              │
│  RESULT:                                                    │
│  Old image size (single stage): 900 MB                      │
│  New image size (multi-stage):  120 MB                      │
│  Reduction: 87%                                             │
└─────────────────────────────────────────────────────────────┘
```

### Image Size Comparison

```
┌──────────────────────────────────────────────────────────────┐
│  Build Method              │ Image Size  │ Contains           │
├────────────────────────────┼─────────────┼────────────────────┤
│  Normal build (single      │ ~900 MB     │ OS + compiler +    │
│  stage, full Ubuntu)       │             │ source + app       │
├────────────────────────────┼─────────────┼────────────────────┤
│  Optimized build (single   │ ~300 MB     │ Slim OS + compiler │
│  stage, slim base)         │             │ + app              │
├────────────────────────────┼─────────────┼────────────────────┤
│  Multi-stage build         │ ~120 MB     │ Minimal OS + app   │
│  (build + runtime stages)  │             │ only               │
└────────────────────────────┴─────────────┴────────────────────┘
```

### Why Multi-Stage Builds Are Important

```
┌─────────────────────────────────────────────────────────────┐
│  Benefits of Multi-Stage Builds:                            │
│                                                              │
│  ✅ Smaller images — faster pull, push, and deploy          │
│  ✅ Faster deployments — less data to transfer              │
│  ✅ Improved security — no compiler or build tools in prod  │
│  ✅ No unnecessary files — source code stays out of image   │
│  ✅ Single Dockerfile — build and runtime in one file       │
│  ✅ Reproducible — same Dockerfile for dev and prod         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.30 Multi-Stage Build Examples — Real-World

Multi-stage builds use multiple `FROM` statements. Only the final stage becomes the image.

### Example 1: React Frontend

```dockerfile
# ─── Stage 1: Build ─────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (cached layer)
COPY package.json package-lock.json ./
RUN npm ci

# Build the React app
COPY . .
RUN npm run build
# Output: /app/build/ directory with static files

# ─── Stage 2: Serve ─────────────────────────────
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Result:
# Build stage: ~500MB (Node.js, node_modules, source code)
# Final image: ~25MB (just Nginx + static HTML/CSS/JS)
```

### Example 2: Java Spring Boot

```dockerfile
# ─── Stage 1: Build with Maven ──────────────────
FROM maven:3.9-eclipse-temurin-21 AS build

WORKDIR /app

# Cache dependencies
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Build the application
COPY src ./src
RUN mvn package -DskipTests -B

# ─── Stage 2: Runtime ───────────────────────────
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Create non-root user
RUN addgroup -S spring && adduser -S spring -G spring

# Copy JAR from build stage
COPY --from=build /app/target/*.jar app.jar

# Switch to non-root
USER spring

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]

# Result:
# Build stage: ~800MB (Maven, JDK, source code)
# Final image: ~200MB (JRE + JAR only)
```

### Example 3: Python FastAPI

```dockerfile
# ─── Stage 1: Build dependencies ────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Stage 2: Runtime ───────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5.31 Build Arguments and Dynamic Builds

```dockerfile
# Define build arguments with defaults
ARG NODE_VERSION=20
ARG APP_ENV=production

FROM node:${NODE_VERSION}-alpine

ARG APP_ENV
# Note: ARG must be re-declared after FROM (each FROM starts a new scope)

ENV NODE_ENV=${APP_ENV}

WORKDIR /app
COPY . .

# Conditional install based on build arg
RUN if [ "$APP_ENV" = "development" ]; then \
      npm install; \
    else \
      npm ci --production; \
    fi

CMD ["node", "app.js"]
```

```bash
# Build with custom arguments
docker build \
  --build-arg NODE_VERSION=18 \
  --build-arg APP_ENV=development \
  -t my-app:dev .

# Build with default arguments
docker build -t my-app:prod .
```

---

## 5.32 Dockerfile Best Practices Checklist

```dockerfile
# ✅ GOOD Dockerfile (production-grade Node.js API)

# 1. Use specific version tags (not "latest")
FROM node:20.11-alpine AS builder

# 2. Set WORKDIR early
WORKDIR /app

# 3. Copy dependency files first (layer caching)
COPY package.json package-lock.json ./

# 4. Install dependencies in a separate layer
RUN npm ci --production

# 5. Copy source code after dependencies
COPY . .

# 6. Build if needed
RUN npm run build

# --- Production stage ---
FROM node:20.11-alpine

# 7. Use non-root user
RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

# 8. Copy only what's needed from builder
COPY --from=builder --chown=app:app /app/dist ./dist
COPY --from=builder --chown=app:app /app/node_modules ./node_modules
COPY --from=builder --chown=app:app /app/package.json ./

# 9. Switch to non-root user
USER app

# 10. Document the port
EXPOSE 3000

# 11. Add health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# 12. Use exec form for CMD
CMD ["node", "dist/app.js"]
```

### Anti-Patterns to Avoid

```dockerfile
# ❌ BAD: Using latest tag
FROM node:latest
# Fix: FROM node:20.11-alpine

# ❌ BAD: Running as root
CMD ["node", "app.js"]
# Fix: USER node before CMD

# ❌ BAD: Copying everything before npm install
COPY . .
RUN npm install
# Fix: COPY package*.json first, then npm install, then COPY . .

# ❌ BAD: Not cleaning up in the same layer
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
# Fix: Combine into one RUN with &&

# ❌ BAD: Storing secrets in ENV or ARG
ENV DATABASE_PASSWORD=mysecret
# Fix: Use runtime -e flag or Docker secrets

# ❌ BAD: Installing unnecessary packages
RUN apt-get install -y vim nano curl wget git
# Fix: Install only what the app needs at runtime

# ❌ BAD: Not using .dockerignore
# Sends node_modules, .git, etc. to build context
# Fix: Create .dockerignore file

# ❌ BAD: Using ADD when COPY suffices
ADD ./app /app
# Fix: COPY ./app /app (unless you need tar extraction)
```

---

## 5.33 Common Errors and Troubleshooting

### Error 1: "COPY failed: no source files were specified"
```bash
# CAUSE: Source file/directory doesn't exist or is in .dockerignore

# Fix:
ls -la                    # Verify file exists
cat .dockerignore         # Check if file is excluded
# Ensure COPY path is relative to build context (the . in docker build .)
```

### Error 2: "returned a non-zero code: 1" during RUN
```bash
# CAUSE: A command in RUN failed

# Example:
# RUN npm install
# npm ERR! code ENOENT
# npm ERR! syscall open
# npm ERR! path /app/package.json

# Fix: Ensure COPY package.json happens BEFORE RUN npm install
```

### Error 3: "WORKDIR can't be empty"
```bash
# CAUSE: Using a variable that's not set

ARG APP_DIR
WORKDIR $APP_DIR    # ← APP_DIR is empty!

# Fix: Provide a default
ARG APP_DIR=/app
WORKDIR $APP_DIR
```

### Error 4: CMD Not Running as Expected
```dockerfile
# Problem: Container exits immediately
CMD node app.js

# Diagnosis: Shell form wraps in /bin/sh -c
# The actual process tree:
# PID 1: /bin/sh -c "node app.js"
# PID 2: node app.js
# If sh exits, node becomes orphaned

# Fix: Use exec form
CMD ["node", "app.js"]
# Process tree:
# PID 1: node app.js  ← Receives signals directly
```

### Error 5: Build Cache Not Working
```bash
# Symptom: Every build re-downloads dependencies

# CAUSE: A layer before the dependency install changed

# Debug: Look at build output
# => CACHED [2/5] WORKDIR /app                    ← Cached ✅
# => [3/5] COPY . .                               ← NOT cached ❌
# => [4/5] RUN npm install                        ← Rebuilds because layer 3 changed

# Fix: Reorder instructions
# COPY package.json first → npm install → COPY . .
```

### Error 6: "no space left on device" During Build
```bash
# CAUSE: Docker build cache is full

# Fix:
docker builder prune          # Clear build cache
docker system prune -a        # Clear everything unused

# Check space:
docker system df
```

---

## 5.34 Production Architecture Using Docker

```
┌─────────────────────────────────────────────────────────────┐
│              PRODUCTION DOCKER WORKFLOW                       │
│                                                              │
│  Developer                                                  │
│     │                                                        │
│     ▼                                                        │
│  Writes Dockerfile (multi-stage, optimized)                 │
│     │                                                        │
│     ▼                                                        │
│  docker build -t myapp:1.0 .                                │
│     │                                                        │
│     ▼                                                        │
│  Docker Image created (small, secure)                       │
│     │                                                        │
│     ▼                                                        │
│  docker push myapp:1.0                                      │
│     │                                                        │
│     ▼                                                        │
│  Registry (Docker Hub / ECR / ACR)                          │
│     │                                                        │
│     ▼                                                        │
│  Production Server pulls image                              │
│     │                                                        │
│     ▼                                                        │
│  docker run -d -p 8080:8080 myapp:1.0                       │
│     │                                                        │
│     ▼                                                        │
│  Container running application                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.35 CI/CD Pipeline Using Docker

```
┌─────────────────────────────────────────────────────────────┐
│              CI/CD PIPELINE WITH DOCKER                       │
│                                                              │
│  Code Commit (git push)                                     │
│     │                                                        │
│     ▼                                                        │
│  CI/CD Pipeline triggered                                   │
│  (Jenkins / GitHub Actions / GitLab CI)                     │
│     │                                                        │
│     ▼                                                        │
│  docker build -t myapp:${BUILD_NUMBER} .                    │
│     │                                                        │
│     ▼                                                        │
│  Run tests inside container                                 │
│  docker run --rm myapp:${BUILD_NUMBER} npm test             │
│     │                                                        │
│     ▼                                                        │
│  docker push myapp:${BUILD_NUMBER}                          │
│     │                                                        │
│     ▼                                                        │
│  Deploy to server                                           │
│  docker pull myapp:${BUILD_NUMBER}                          │
│  docker run -d myapp:${BUILD_NUMBER}                        │
│                                                              │
│  Tools commonly used:                                       │
│  • Jenkins                                                  │
│  • GitHub Actions                                           │
│  • GitLab CI                                                │
│  • CircleCI                                                 │
│  • AWS CodePipeline                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.36 Security Best Practices for Docker Images

```
┌──────────────────────────────────────────────────────────────┐
│  DOCKER IMAGE SECURITY BEST PRACTICES                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Use OFFICIAL images                                     │
│     ✅ FROM node:20-alpine                                  │
│     ❌ FROM random-user/node-custom                         │
│                                                              │
│  2. Use SPECIFIC version tags                               │
│     ✅ FROM node:20.11-alpine                               │
│     ❌ FROM node:latest (unpredictable)                     │
│                                                              │
│  3. Run as NON-ROOT user                                    │
│     ✅ USER appuser                                         │
│     ❌ Running as root (default)                            │
│                                                              │
│  4. Scan images for vulnerabilities                         │
│     $ docker scout cves myapp:1.0                           │
│     $ trivy image myapp:1.0                                 │
│     $ grype myapp:1.0                                       │
│                                                              │
│  5. Use multi-stage builds                                  │
│     No compiler or build tools in production image          │
│                                                              │
│  6. Don't store secrets in images                           │
│     ❌ ENV DB_PASSWORD=secret123                            │
│     ✅ Pass secrets at runtime: -e DB_PASSWORD=$SECRET      │
│                                                              │
│  7. Use .dockerignore                                       │
│     Exclude .git, node_modules, .env, secrets               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.37 Docker System Cleanup Commands

```bash
# ─── REMOVE UNUSED RESOURCES ───────────────────────────────

# Remove stopped containers
$ docker container prune
# WARNING! This will remove all stopped containers.
# Are you sure you want to continue? [y/N] y

# Remove unused images (dangling)
$ docker image prune

# Remove ALL unused images (not just dangling)
$ docker image prune -a

# Remove unused volumes
$ docker volume prune

# Remove unused networks
$ docker network prune

# Remove EVERYTHING unused (containers + images + networks)
$ docker system prune
# WARNING! This will remove:
#   - all stopped containers
#   - all networks not used by at least one container
#   - all dangling images
#   - all dangling build cache

# Nuclear option: remove everything + volumes
$ docker system prune -a --volumes

# ─── CHECK DISK USAGE ─────────────────────────────────────

$ docker system df
# TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Images          10      3        5.2GB     3.8GB (73%)
# Containers      5       2        100MB     60MB (60%)
# Local Volumes   8       3        2.1GB     1.5GB (71%)
# Build Cache     15      0        500MB     500MB (100%)

# Detailed breakdown
$ docker system df -v
```

---

## 5.38 Multi-Stage and Optimization Interview Questions

```
┌──────────────────────────────────────────────────────────────┐
│  MULTI-STAGE & OPTIMIZATION INTERVIEW Q&A                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: What is a multi-stage build?                            │
│  A: A Dockerfile with multiple FROM statements that         │
│     separates the build environment from the runtime        │
│     environment. Only the final stage becomes the image,    │
│     reducing size by excluding compilers and build tools.   │
│                                                              │
│  Q: Why is Alpine used as a base image?                     │
│  A: Alpine Linux is only ~5 MB compared to Ubuntu's ~80 MB.│
│     It provides a minimal Linux environment sufficient      │
│     for most applications, resulting in much smaller images.│
│                                                              │
│  Q: How do you optimize a Docker image?                     │
│  A: 1. Use Alpine or slim base images                       │
│     2. Use multi-stage builds                               │
│     3. Combine RUN commands to reduce layers                │
│     4. Use .dockerignore to exclude unnecessary files       │
│     5. Order instructions for cache optimization            │
│     6. Clean up package caches in the same RUN layer        │
│                                                              │
│  Q: What is Docker build cache?                             │
│  A: Docker caches each layer. If a Dockerfile instruction   │
│     hasn't changed, Docker reuses the cached layer instead  │
│     of re-executing it. Put rarely-changing instructions    │
│     first (dependencies before source code).                │
│                                                              │
│  Q: How does COPY --from work?                              │
│  A: COPY --from=stagename copies files from a previous      │
│     build stage into the current stage. This is how         │
│     multi-stage builds transfer only the compiled output.   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 5.39 Docker Registry — Where Images Are Stored and Shared

After building images locally, you need a place to **store and share** them — like GitHub for code, but for Docker images. That place is a **Docker Registry**.

### What Is a Registry?

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER REGISTRY                                 │
│                                                              │
│  A registry is a server that stores Docker images.          │
│  You push images to it, and others pull from it.            │
│                                                              │
│  ┌──────────┐   docker push   ┌──────────────────┐         │
│  │ Your     │ ──────────────► │ Registry         │         │
│  │ Machine  │                 │ (Docker Hub,     │         │
│  │          │ ◄────────────── │  ECR, ACR, GCR)  │         │
│  └──────────┘   docker pull   └──────────────────┘         │
│                                                              │
│  Common registries:                                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Docker Hub          │ Public, free for public images  │   │
│  │ AWS ECR             │ Amazon's private registry       │   │
│  │ Azure ACR           │ Azure's private registry        │   │
│  │ Google Artifact Reg │ Google Cloud's registry         │   │
│  │ GitHub GHCR         │ GitHub Container Registry       │   │
│  │ Harbor              │ Open-source private registry    │   │
│  │ Nexus               │ Self-hosted artifact manager    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Image Tagging for Registries

Before pushing to a registry, you must **tag** the image with the registry path. The tag creates a reference — it does NOT copy the image.

```bash
# Syntax
$ docker tag local-image registry/repository:tag

# Example: Tag for Docker Hub
$ docker tag myapp:1.0 deepak/myapp:1.0

# What happened:
$ docker images
# REPOSITORY       TAG   IMAGE ID       SIZE
# myapp            1.0   a1b2c3d4e5     230MB
# deepak/myapp     1.0   a1b2c3d4e5     230MB
#                        ^^^^^^^^^^^^
#                        SAME image ID — tag is just a reference

# If no tag specified → defaults to "latest"
$ docker tag myapp deepak/myapp
# Creates: deepak/myapp:latest
```

### Image Naming Convention for Registries

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE NAMING FOR REGISTRIES                      │
│                                                              │
│  Format: [registry/]repository:tag                          │
│                                                              │
│  Docker Hub (default registry — no prefix needed):          │
│  myapp:1.0                    → docker.io/library/myapp:1.0 │
│  username/myapp:1.0           → docker.io/username/myapp:1.0│
│                                                              │
│  AWS ECR:                                                   │
│  123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0       │
│                                                              │
│  Google Artifact Registry:                                  │
│  us-docker.pkg.dev/project-id/repo-name/myapp:1.0          │
│                                                              │
│  GitHub Container Registry:                                 │
│  ghcr.io/username/myapp:1.0                                 │
│                                                              │
│  Azure Container Registry:                                  │
│  myregistry.azurecr.io/myapp:1.0                            │
│                                                              │
│  Self-hosted:                                               │
│  registry.company.com:5000/myapp:1.0                        │
└─────────────────────────────────────────────────────────────┘
```

### docker login — Authenticate to a Registry

```bash
# Login to Docker Hub (default)
$ docker login
Username: deepak
Password: ********
Login Succeeded

# Login to a specific registry
$ docker login ghcr.io
$ docker login 123456789.dkr.ecr.us-east-1.amazonaws.com
$ docker login myregistry.azurecr.io

# Login with credentials inline (for CI/CD scripts)
$ echo $DOCKER_PASSWORD | docker login -u deepak --password-stdin

# Logout
$ docker logout

# Where credentials are stored:
# ~/.docker/config.json (base64 encoded — NOT encrypted!)
# For production CI/CD, use credential helpers or secrets managers
```

### docker push — Upload Image to Registry

```bash
# Push to Docker Hub
$ docker push deepak/myapp:1.0

# Output:
# The push refers to repository [docker.io/deepak/myapp]
# a1b2c3d4: Pushing [==>                                ] 10MB/230MB
# e5f6g7h8: Pushing [========>                          ] 30MB/100MB
# ...
# a1b2c3d4: Pushed
# e5f6g7h8: Pushed
# f9g0h1i2: Mounted from library/ubuntu
# 1.0: digest: sha256:abc123def456... size: 1234

# MEANING:
# "Pushed"  → Layer uploaded to registry
# "Mounted" → Layer already exists in registry (shared from base image)
#              Docker doesn't re-upload it — saves time and bandwidth

# Push all tags of an image
$ docker push deepak/myapp --all-tags
```

### docker pull — Download Image from Registry

```bash
# Pull a specific version
$ docker pull deepak/myapp:1.0

# Output:
# 1.0: Pulling from deepak/myapp
# a1b2c3d4: Pull complete
# e5f6g7h8: Pull complete
# Digest: sha256:abc123def456...
# Status: Downloaded newer image for deepak/myapp:1.0

# Pull latest (default tag)
$ docker pull deepak/myapp
# Same as: docker pull deepak/myapp:latest

# Pull from a specific registry
$ docker pull ghcr.io/deepak/myapp:1.0
$ docker pull 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0

# After pulling, run it:
$ docker run -d -p 8080:8080 deepak/myapp:1.0
```

### Complete Workflow: Build → Tag → Login → Push → Pull → Run

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE DOCKER REGISTRY WORKFLOW                │
│                                                              │
│  Developer Machine                                          │
│  ─────────────────                                          │
│  Step 1: Write Dockerfile                                   │
│     │                                                        │
│     ▼                                                        │
│  Step 2: docker build -t myapp:1.0 .                        │
│     │    (Image created locally)                            │
│     ▼                                                        │
│  Step 3: docker tag myapp:1.0 deepak/myapp:1.0              │
│     │    (Create registry reference)                        │
│     ▼                                                        │
│  Step 4: docker login                                       │
│     │    (Authenticate to registry)                         │
│     ▼                                                        │
│  Step 5: docker push deepak/myapp:1.0                       │
│     │    (Upload to registry)                               │
│     ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker Hub / ECR / ACR / GCR                        │   │
│  │  deepak/myapp:1.0 stored in registry                 │   │
│  └──────────────────────────────────────────────────────┘   │
│     │                                                        │
│     ▼                                                        │
│  Other Machine (QA / Staging / Production)                  │
│  ─────────────────────────────────────────                  │
│  Step 6: docker pull deepak/myapp:1.0                       │
│     │    (Download from registry)                           │
│     ▼                                                        │
│  Step 7: docker run -d -p 8080:8080 deepak/myapp:1.0       │
│     │    (Run the container)                                │
│     ▼                                                        │
│  Application running — same image, same environment         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Complete workflow in commands:

# On developer machine:
$ docker build -t myapp:1.0 .
$ docker tag myapp:1.0 deepak/myapp:1.0
$ docker login
$ docker push deepak/myapp:1.0

# On production server:
$ docker pull deepak/myapp:1.0
$ docker run -d -p 8080:8080 deepak/myapp:1.0
```

---

## 5.40 Real-World Example: Apache Web Server Dockerfile Web Server Dockerfile

A complete, working example that demonstrates FROM, RUN, EXPOSE, and CMD together.

```dockerfile
# Dockerfile — Apache web server on Ubuntu
FROM ubuntu

RUN apt-get update && apt-get install -y apache2

EXPOSE 80

CMD ["apachectl", "-D", "FOREGROUND"]
```

```
┌─────────────────────────────────────────────────────────────┐
│  Line-by-Line Breakdown:                                    │
│                                                              │
│  FROM ubuntu                                                │
│  → Start with Ubuntu base image                            │
│                                                              │
│  RUN apt-get update && apt-get install -y apache2           │
│  → Update package lists AND install Apache in one layer     │
│  → -y auto-confirms (no interactive prompt during build)    │
│                                                              │
│  EXPOSE 80                                                  │
│  → Document that Apache listens on port 80                  │
│  → Does NOT publish the port (need -p at runtime)           │
│                                                              │
│  CMD ["apachectl", "-D", "FOREGROUND"]                      │
│  → Start Apache in foreground mode                          │
│  → -D FOREGROUND keeps Apache as PID 1 (container stays    │
│    running). Without it, Apache daemonizes and container    │
│    exits immediately.                                       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Build the image
$ docker build -t apacheimg .

# Output:
# Step 1/4 : FROM ubuntu
#  ---> 5d0da3dc9764
# Step 2/4 : RUN apt-get update && apt-get install -y apache2
#  ---> Running in a1b2c3d4e5f6
# ...
# Successfully built 0i1j2k3l4m5n
# Successfully tagged apacheimg:latest

# Run the container with port mapping
$ docker run -d -p 8080:80 --name myweb apacheimg

# Test it
$ curl localhost:8080
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"...
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Apache2 Ubuntu Default Page: It works</title>
...

# ✅ Apache is running inside the container
# ✅ Accessible from host on port 8080
# ✅ Port mapping: host:8080 → container:80

# Check container is running
$ docker ps
# CONTAINER ID   IMAGE       COMMAND                  STATUS         PORTS
# abc123def456   apacheimg   "apachectl -D FOREGR…"   Up 2 minutes   0.0.0.0:8080->80/tcp

# Stop and remove
$ docker rm -f myweb
```

---

## 5.41 Where Docker Stores Images Locally

All Docker data is stored under `/var/lib/docker/` on the host machine.

```
┌─────────────────────────────────────────────────────────────┐
│              /var/lib/docker/ — Docker's Storage              │
│                                                              │
│  /var/lib/docker/                                           │
│  ├── image/               ← Image metadata                  │
│  │   └── overlay2/                                          │
│  │       ├── imagedb/     ← Image database                  │
│  │       └── layerdb/     ← Layer database                  │
│  │                                                          │
│  ├── overlay2/            ← Actual layer filesystems        │
│  │   ├── abc123.../       ← Layer content (the real files)  │
│  │   └── def456.../                                        │
│  │                                                          │
│  ├── containers/          ← Container metadata + logs       │
│  │   └── abc123.../                                        │
│  │       ├── config.v2.json                                │
│  │       └── *-json.log   ← Container logs                 │
│  │                                                          │
│  └── volumes/             ← Named volume data               │
│      └── mydata/_data/                                     │
│                                                              │
│  ⚠️  Never manually modify files here.                     │
│  Use Docker CLI commands to manage images and containers.   │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Check disk usage by Docker
$ docker system df
TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images          10      3        5.2GB     3.8GB (73%)
Containers      5       2        100MB     60MB (60%)
Local Volumes   8       3        2.1GB     1.5GB (71%)
Build Cache     15      0        500MB     500MB (100%)

# See where a specific image's layers are stored
$ docker inspect myapp:1.0 --format='{{.GraphDriver.Data.MergedDir}}'
/var/lib/docker/overlay2/abc123.../merged
```

---

## 5.42 Dockerfile Instructions — Complete Summary Table

```
┌──────────────┬────────────────────────────────────────────────┐
│ Instruction  │ Purpose                                        │
├──────────────┼────────────────────────────────────────────────┤
│ FROM         │ Set base image (required, must be first)       │
│ RUN          │ Execute command during build (creates layer)   │
│ CMD          │ Default command (overridable by user)          │
│ ENTRYPOINT   │ Fixed command (user args appended)             │
│ COPY         │ Copy files from host to image                  │
│ ADD          │ Like COPY + auto tar extraction                │
│ WORKDIR      │ Set working directory (like cd, but persists)  │
│ ENV          │ Set environment variable (build + runtime)     │
│ ARG          │ Set build-time variable (build only)           │
│ EXPOSE       │ Document port (does NOT publish)               │
│ VOLUME       │ Declare mount point                            │
│ USER         │ Set running user (non-root for security)       │
│ HEALTHCHECK  │ Define health check command                    │
│ LABEL        │ Add metadata (maintainer, version, etc.)       │
│ SHELL        │ Change default shell                           │
│ STOPSIGNAL   │ Set custom stop signal                         │
└──────────────┴────────────────────────────────────────────────┘
```

---

## 5.43 Interview Example: Production Java Dockerfile

A realistic Dockerfile you might see in a Java project or be asked to write in an interview:

```dockerfile
# Production Java Application Dockerfile
FROM openjdk:17

WORKDIR /app

COPY app.jar .

ENV JAVA_OPTS="-Xmx512m"

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

```
┌─────────────────────────────────────────────────────────────┐
│  Line-by-Line Explanation:                                  │
│                                                              │
│  FROM openjdk:17                                            │
│  → Base image with Java 17 pre-installed                    │
│                                                              │
│  WORKDIR /app                                               │
│  → All subsequent commands run in /app                      │
│                                                              │
│  COPY app.jar .                                             │
│  → Copy the built JAR file from host into /app/app.jar      │
│                                                              │
│  ENV JAVA_OPTS="-Xmx512m"                                   │
│  → Set max heap size to 512MB (available at runtime)        │
│                                                              │
│  EXPOSE 8080                                                │
│  → Document that the app listens on port 8080               │
│                                                              │
│  ENTRYPOINT ["java", "-jar", "app.jar"]                     │
│  → ENTRYPOINT (not CMD) because:                            │
│    - The container's ONE job is to run this Java app        │
│    - User can pass additional JVM args                      │
│    - App always starts — can't be accidentally overridden   │
│                                                              │
│  Usage:                                                     │
│  docker run -d -p 8080:8080 myapp:1.0                       │
│  docker run -d -p 8080:8080 myapp:1.0 --spring.profiles=prod│
│  (--spring.profiles=prod becomes argument to java -jar)     │
└─────────────────────────────────────────────────────────────┘
```

### Interview Variations

```dockerfile
# Python Flask application
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]

# Node.js Express application
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
ENV NODE_ENV=production
EXPOSE 3000
USER node
CMD ["node", "app.js"]

# Go application (multi-stage)
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o server .

FROM alpine:3.19
COPY --from=builder /app/server /server
EXPOSE 8080
ENTRYPOINT ["/server"]
```

---

## 5.44 Dockerfile Cheat Sheet — Quick Reference

```bash
# ─── BUILDING ───────────────────────────────────────────────

# Build image from Dockerfile (default name)
$ docker build -t name:tag .

# Build with custom Dockerfile name
$ docker build -t name:tag -f Dockerfile.dev .

# Build without cache (fresh build)
$ docker build --no-cache -t name:tag .

# Build with build arguments
$ docker build --build-arg VERSION=1.0 -t name:tag .

# Redirect build output to log file
$ docker build -t name:tag . > build.log 2>&1

# Build and show output + save to log
$ docker build -t name:tag . 2>&1 | tee build.log

# ─── IMAGES ─────────────────────────────────────────────────

# List images
$ docker images

# List images filtered by name
$ docker images myapp

# See image layers/history
$ docker history name:tag

# Remove an image
$ docker rmi name:tag

# Remove dangling images
$ docker image prune

# Remove all unused images
$ docker image prune -a

# ─── RUNNING ────────────────────────────────────────────────

# Run container from built image (interactive)
$ docker run -it name:tag

# Run container overriding CMD
$ docker run -it name:tag sh

# Run container in background
$ docker run -d -p 8080:8080 name:tag

# ─── REGISTRY ──────────────────────────────────────────────

# Login to Docker Hub
$ docker login

# Tag image for registry
$ docker tag name:tag username/name:tag

# Push image to registry
$ docker push username/name:tag

# Pull image from registry
$ docker pull username/name:tag

# ─── CLEANUP ───────────────────────────────────────────────

# Remove build cache
$ docker builder prune

# Remove everything unused
$ docker system prune -a

# Check disk usage
$ docker system df
```

### Dockerfile Instructions Quick Reference

```
┌──────────────┬────────────────────────────────────────────────┐
│ Instruction  │ Purpose                                        │
├──────────────┼────────────────────────────────────────────────┤
│ FROM         │ Set base image (required, must be first)       │
│ RUN          │ Execute command during build (creates layer)   │
│ CMD          │ Default command (overridable by user)          │
│ ENTRYPOINT   │ Fixed command (user args appended)             │
│ COPY         │ Copy files from host to image                  │
│ ADD          │ Like COPY + tar extraction + URL download      │
│ WORKDIR      │ Set working directory                          │
│ ENV          │ Set environment variable (build + runtime)     │
│ ARG          │ Set build-time variable (build only)           │
│ EXPOSE       │ Document port (does NOT publish)               │
│ VOLUME       │ Declare mount point                            │
│ USER         │ Set running user (non-root for security)       │
│ HEALTHCHECK  │ Define health check command                    │
│ LABEL        │ Add metadata (maintainer, version, etc.)       │
│ SHELL        │ Change default shell                           │
│ STOPSIGNAL   │ Set custom stop signal                         │
└──────────────┴────────────────────────────────────────────────┘
```

---

## 5.20 Validating Downloads with Checksums

When a Dockerfile downloads binaries from the internet, always verify
integrity with a checksum. Without verification, a compromised server
or man-in-the-middle attack can inject malicious code.

### The Dangerous Pattern

```dockerfile
# NEVER do this in production — blindly trusts the remote server
RUN curl -sL https://example.com/install.sh | bash
```

```
# Problems:
#   - The script could be tampered with (DNS hijack, MITM)
#   - Content may change between builds (non-deterministic)
#   - No way to audit what was executed
#   - Breaks reproducibility
```

### The Secure Pattern — SHA256 Verification

```dockerfile
# Download, verify checksum, then extract
RUN curl -LO https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip \
    && echo "e4add46c06cb0e2b8d4b4e8f44e0b8d0a585e3e8e1c3e5f7a9b2c4d6e8f0a1b2  terraform_1.7.0_linux_amd64.zip" | sha256sum -c - \
    && unzip terraform_1.7.0_linux_amd64.zip -d /usr/local/bin/ \
    && rm terraform_1.7.0_linux_amd64.zip
```

```
# How it works:
#   1. curl -LO downloads the file (follows redirects, keeps filename)
#   2. echo "<expected-hash>  <filename>" | sha256sum -c -
#      sha256sum -c reads the expected hash and compares it to the
#      actual hash of the file. Exits non-zero if they don't match.
#   3. If the hash doesn't match, the RUN step fails and the build stops
#   4. unzip extracts only if verification passed
#   5. rm cleans up the archive to reduce image size
```

### Getting the Expected Hash

```bash
# Method 1: Download the file locally and compute the hash
$ curl -LO https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip
$ sha256sum terraform_1.7.0_linux_amd64.zip
# e4add46c06cb0e2b8d4b4e8f44e0b8d0...  terraform_1.7.0_linux_amd64.zip

# Method 2: Many projects publish checksums alongside releases
$ curl -sL https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_SHA256SUMS
# Lists hashes for all platform archives
```

### Real-World Example: Installing kubectl

```dockerfile
FROM alpine:3.19

ARG KUBECTL_VERSION=v1.29.0

RUN apk add --no-cache curl \
    && curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256" \
    && echo "$(cat kubectl.sha256)  kubectl" | sha256sum -c - \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
    && rm kubectl kubectl.sha256

# The official kubectl release includes a .sha256 file
# We download both, verify, then install
```

### When to Use Package Managers Instead

```dockerfile
# Prefer package managers over curl when available — they handle
# signature verification automatically:

# Alpine
RUN apk add --no-cache curl git jq

# Debian/Ubuntu
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git jq \
    && rm -rf /var/lib/apt/lists/*

# Package managers verify GPG signatures on packages automatically
# Only use curl + checksum for binaries not in package repositories
```

---

## 5.21 Entrypoint Start Scripts (Wait-for-DB Pattern)

Production containers often need to wait for dependencies (database,
Redis, message queue) before starting the application.

### The Problem

```yaml
# docker-compose.yml
services:
  app:
    build: .
    depends_on:
      - db
  db:
    image: postgres:16
```

```
# depends_on only waits for the container to START, not for the
# service inside to be READY. PostgreSQL takes several seconds
# to initialize. The app container starts immediately and crashes
# because the database isn't accepting connections yet.
```

### Solution: Entrypoint Start Script

```bash
#!/bin/sh
# start.sh — wait for dependencies, then start the app
set -e

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
until nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; do
    echo "  PostgreSQL not ready, retrying in 1s..."
    sleep 1
done
echo "PostgreSQL is ready."

echo "Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
until nc -z "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"; do
    echo "  Redis not ready, retrying in 1s..."
    sleep 1
done
echo "Redis is ready."

echo "Starting application..."
exec "$@"
```

```
# Key points:
#   set -e          — exit on any error
#   nc -z host port — test TCP connection without sending data
#   exec "$@"       — REPLACES the shell with the actual command
#                     This makes the app process PID 1, so it
#                     receives SIGTERM directly from Docker
#
# Without exec: sh(PID 1) → node(PID 2) — signals go to sh, not node
# With exec:    node(PID 1) — signals go directly to node
```

### Dockerfile Using the Start Script

```dockerfile
FROM node:20-alpine

# Install netcat for the wait script
RUN apk add --no-cache netcat-openbsd

WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .

# Copy and make the start script executable
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

USER node
EXPOSE 3000

ENTRYPOINT ["start.sh"]
CMD ["node", "server.js"]
```

```
# How ENTRYPOINT + CMD work together here:
#   ENTRYPOINT = ["start.sh"]
#   CMD = ["node", "server.js"]
#
#   Docker runs: start.sh node server.js
#   start.sh waits for dependencies, then:
#     exec "$@" → exec node server.js
#   node becomes PID 1 and receives signals properly
#
# You can override CMD at runtime:
#   docker run myapp node migrate.js
#   → start.sh waits for DB, then runs: exec node migrate.js
```

### Alternative: Docker Compose healthcheck + depends_on condition

```yaml
# Modern approach — no start script needed
services:
  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
```

```
# With condition: service_healthy, Docker Compose waits until
# the dependency's health check passes before starting the app.
# This is cleaner than a start script but only works with Compose.
# In Kubernetes, use initContainers or readiness probes instead.
```

---

## Module 5 Summary

- **Why automate**: Manual `docker commit` doesn't scale — Dockerfiles are reproducible, version-controlled, and CI/CD-ready
- **Dockerfile**: Plain text file with `INSTRUCTION arguments` format, executed top to bottom
- `FROM` sets the base image — use specific tags, prefer slim/alpine variants
- `RUN` executes build commands — always use `-y` flag for non-interactive installs
- `CMD` sets the default command — user can replace it entirely
- `ENTRYPOINT` sets a fixed command — user input becomes arguments (most asked interview topic)
- `ENTRYPOINT + CMD` together = fixed program with overridable default arguments
- **Real-world rule**: Use ENTRYPOINT when the container has one job (Java app, web server); use CMD for general-purpose containers
- **docker build**: Creates temporary containers per step, saves each as a layer, removes temp containers
- **Build cache**: Docker reuses unchanged layers — second build takes < 1 second
- **Build context** (`.`): The directory sent to Docker daemon; use `.dockerignore` to exclude large files
- **Image tags**: A tag points to one image ID; rebuilding with same tag moves the tag (old image becomes dangling)
- `-f` flag: Use custom Dockerfile names (`Dockerfile.dev`, `Dockerfile.prod`)
- `WORKDIR` sets the working directory — always use it instead of `cd` (persists across layers)
- `COPY` copies files from host to image; `ADD` also auto-extracts tar archives
- `ENV` sets runtime environment variables (persists in container); `ARG` is build-time only (empty in container)
- `EXPOSE` documents ports but does NOT publish them — you must use `-p` at runtime
- `USER` switches to non-root — always do this for production; override with `-u root` for debugging
- `HEALTHCHECK` monitors application health
- **Multi-stage builds**: Separate build and runtime stages — reduces image from ~900MB to ~120MB
- **Image optimization**: Use Alpine base, combine RUN commands, use .dockerignore, specific tags
- Layer caching: copy dependency files before source code
- **Security**: Use official images, specific versions, non-root user, scan for vulnerabilities
- **CI/CD**: Docker is core to modern pipelines — build → push → deploy
- **Cleanup**: `docker system prune` removes unused resources; `docker system df` checks disk usage
- **Registry**: Docker Hub, ECR, ACR, GCR — where images are stored and shared
- **docker login**: Authenticate to a registry before pushing
- **docker tag**: Create a registry reference (same image ID, new name)
- **docker push/pull**: Upload to / download from registry
- Flow: `docker build` → `docker tag` → `docker login` → `docker push` → `docker pull` → `docker run`
- Docker stores all data locally under `/var/lib/docker/` — never modify directly

---

**Next Module: [Module 6 - Docker Compose](module-06-compose.md)**
