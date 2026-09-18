# Module 12: Docker Image Optimization — Production-Ready Images

---

## 12.1 What a Production Image Should Look Like

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT "GOOD" LOOKS LIKE                           │
│                                                              │
│  ✅ Small          — fast pull/start, cheaper storage       │
│  ✅ Deterministic  — pinned versions, repeatable builds     │
│  ✅ Secure         — minimal packages, non-root, no secrets │
│  ✅ Fast to build  — cache-friendly Dockerfile              │
│  ✅ Observable     — healthcheck, logs to stdout/stderr     │
└─────────────────────────────────────────────────────────────┘
```

### Why Optimization Matters

A "bloated" image causes real production problems:

```
┌─────────────────────────────────────────────────────────────┐
│              WHY OPTIMIZATION MATTERS                        │
│                                                              │
│  ❌ More security risk                                      │
│     More packages/libs = larger attack surface              │
│                                                              │
│  ❌ Slower CI builds                                        │
│     Build time increases with image size                    │
│                                                              │
│  ❌ Slower pushes to registries                             │
│     Bigger upload to Docker Hub / ECR / GCR                 │
│                                                              │
│  ❌ Slower deployments in Kubernetes                        │
│     Nodes must pull large images before starting            │
│                                                              │
│  ❌ Slower container startup                                │
│     Pull + unpack + start takes longer                      │
│                                                              │
│  Goal: Small, fast, secure, production-ready images         │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.2 Docker Image Basics — Layers

A Docker image is built from **layers** (stacked filesystem changes). Every `RUN`, `COPY`, `ADD` instruction creates a new layer.

### Sandwich Analogy

```
+---------------------------+
|  App layer (your code)    |  ← patty (main item)
+---------------------------+
|  Dependencies (libs, pkgs) |  ← veggies (tomato/onion)
+---------------------------+
|  Base image (OS + libs)    |  ← bread (foundation)
+---------------------------+
```

### What's Typically Inside an Image

```
Base image    → OS + core libraries (Ubuntu, Alpine, Debian)
Dependencies  → Runtime libs, packages, language runtimes
Application   → Your code/artifact (JAR, binary, node app, etc.)
```

### Key Takeaway

```
More layers + more packages = bigger size + higher risk + slower deployments
```

---

## 12.3 Method 1 — Use a Minimal Base Image (Alpine / Slim Variants)

### 1A) Minimal OS Footprint: Prefer Alpine

**Bloated Dockerfile (Ubuntu base):**

```dockerfile
# Dockerfile_1
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y mysql-client
CMD ["mysql"]
```

```bash
# Build
$ docker build -t image1:m1 -f Dockerfile_1 .

# Check size
$ docker images

# Output:
# REPOSITORY   TAG   IMAGE ID   CREATED   SIZE
# image1       m1    ...        ...       154MB
# ubuntu       20.04 ...        ...       73MB

# Ubuntu base alone = 73MB
# Rest from installing mysql-client
```

**Optimized Dockerfile (Alpine base):**

```dockerfile
# Dockerfile_1_optimized
FROM alpine:latest
RUN apk add --no-cache mysql-client
CMD ["mysql"]
```

```bash
# Build
$ docker build -t image1opt:m1 -f Dockerfile_1_optimized .

$ docker images
# REPOSITORY    TAG   SIZE
# image1opt     m1    ~40MB     ← 80%+ smaller!
# image1        m1    ~154MB
```

```
┌─────────────────────────────────────────────────────────────┐
│              ALPINE vs UBUNTU                                │
│                                                              │
│  Ubuntu base:  ~73MB                                        │
│  Alpine base:  ~5-6MB                                       │
│                                                              │
│  Same functionality, ~80%+ smaller image                    │
└─────────────────────────────────────────────────────────────┘
```

### 1B) "Slim" Variants of Images

**Bloated (full node image):**

```dockerfile
FROM node:16.19
CMD ["node"]
```

```bash
$ docker build -t image2:m1 -f Dockerfile_2 .
$ docker images
# image2   m1   ~910MB    ← very large!
```

**Option 1: Debian slim + install Node:**

```dockerfile
FROM debian:stable-slim
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
CMD ["node"]
```

```bash
$ docker build -t image2opt:m1 -f Dockerfile_2_optimized .
$ docker images
# image2opt   m1   ~238MB
```

**Option 2 (best): Use node slim directly:**

```dockerfile
FROM node:16-slim
CMD ["node"]
```

```bash
$ docker build -t image2opt2:m1 -f Dockerfile_2_optimized2 .
$ docker images
# image2opt2   m1   ~180MB
```

### Size Comparison

```
┌──────────────────────┬──────────┐
│ Image                │ Size     │
├──────────────────────┼──────────┤
│ node:16.19 (full)    │ ~910MB   │
│ debian:slim + node   │ ~238MB   │
│ node:16-slim         │ ~180MB   │
│ node:16-alpine       │ ~130MB   │
└──────────────────────┴──────────┘

Rule: If there's an official *-slim or *-alpine tag
that supports your app, prefer it.
```

### Alpine Gotcha: glibc vs musl

```
┌─────────────────────────────────────────────────────────────┐
│              ALPINE COMPATIBILITY WARNING                    │
│                                                              │
│  Alpine uses musl libc (not glibc)                          │
│                                                              │
│  Most Linux distros (Ubuntu, Debian) use glibc              │
│  Some apps/libraries are compiled against glibc             │
│  These may NOT work on Alpine without workarounds           │
│                                                              │
│  Common issues:                                             │
│    - Python packages with C extensions                      │
│    - Java apps with native libraries                        │
│    - Node.js native addons (node-gyp)                       │
│                                                              │
│  Tip: Pick the smallest base that still supports your       │
│  dependencies. If Alpine breaks things, use *-slim instead. │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.4 Method 2 — Multi-Stage Builds (Up to 95%+ Reduction)

Especially powerful for compiled apps (Go, Java) or when build tools are needed only during build.

### 2A) The Bloated Single-Stage Go Build

```dockerfile
FROM golang:latest
WORKDIR /app
COPY . .
RUN go build -o mywebapp
EXPOSE 8080
CMD ["./mywebapp"]
```

```bash
$ docker build -t image1:m2 -f Dockerfile_1_combined .
$ docker images
# image1   m2   ~860MB
```

**Why so big?** The final image contains:
- Go compiler toolchain
- Build caches
- Source code
- Plus the runtime binary

At runtime you only need the compiled binary and minimal OS support.

### 2B) Manual Two-Step Optimization

**Step 1:** Build in big image

```bash
$ docker build -t image1:m2 -f Dockerfile_1_combined .
```

**Step 2:** Create container and copy binary out

```bash
$ docker run -d --name temp-container image1:m2
$ docker cp temp-container:/app/mywebapp .
# Now you have mywebapp on your host
```

**Step 3:** Build small runtime image using Alpine

```dockerfile
FROM alpine:latest
WORKDIR /app
COPY mywebapp .
EXPOSE 8080
CMD ["./mywebapp"]
```

```bash
$ docker build -t image1opt:m2 -f Dockerfile_2 .
$ docker images
# image1opt   m2   ~15MB     ← down from ~860MB!
# That's >95% reduction
```

### 2C) Multi-Stage Build (Best Practice — One Dockerfile)

Instead of 2 Dockerfiles + manual `docker cp`, do it in one Dockerfile using stages:

```dockerfile
# Stage 1: build
FROM golang:latest AS builder
WORKDIR /app
COPY . .
RUN go build -o mywebapp

# Stage 2: runtime
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/mywebapp .
EXPOSE 8080
CMD ["./mywebapp"]
```

```bash
$ docker build -t image-multistage:m2 -f Dockerfile_3 .
$ docker images
# image-multistage   m2   ~15MB
```

### Multi-Stage Flow Diagram

```
Stage 1 (builder image — discarded)
+--------------------------+
| golang toolchain         |
| source code              |
| builds → /app/mywebapp   |
+--------------------------+
              │
              │ COPY --from=builder
              ▼
Stage 2 (runtime image — final)
+--------------------------+
| alpine (~5MB)            |
| /app/mywebapp            |
+--------------------------+

Final image contains ONLY:
  ✅ Alpine minimal OS
  ✅ mywebapp binary
  ❌ No Go compiler
  ❌ No source code
  ❌ No build caches
```

### 2D) Dangling Images and Cleanup

Multi-stage creates intermediate images/layers that remain locally as "dangling" (untagged).

```bash
# Remove dangling images
$ docker image prune

# Remove all unused images
$ docker image prune -a
```

---

## 12.5 Method 3 — Minimize the Number of Layers

Every `RUN`, `COPY`, `ADD` typically adds a layer. Too many layers = bigger image + more build time.

### 3A) Bloated Example (Multiple RUN Instructions)

```dockerfile
FROM ubuntu:latest
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y vim
RUN apt-get install -y curl
RUN apt-get install -y dnsutils
```

```bash
# Time the build
$ time docker build -t image1:m3 -f Dockerfile_1 .

# Check layers
$ docker history image1:m3

# docker history output columns:
#   LAYER ID | CREATED | COMMAND | SIZE
# You'll see MANY lines = many layers
```

### 3B) Optimized Example (Combine into One RUN)

```dockerfile
FROM ubuntu:latest
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y vim curl dnsutils && \
    rm -rf /var/lib/apt/lists/*
```

```bash
$ time docker build -t image1opt:m3 -f Dockerfile_1_optimized .
$ docker history image1opt:m3
# Fewer lines = fewer layers
```

### 3C) Mini Example: Create Files

**Bad (3 layers):**

```dockerfile
RUN touch a.txt
RUN touch b.txt
RUN touch c.txt
```

**Good (1 layer):**

```dockerfile
RUN touch a.txt b.txt c.txt
```

Or:

```dockerfile
RUN touch a.txt && touch b.txt && touch c.txt
```

### Benefits of Fewer Layers

```
┌─────────────────────────────────────────────────────────────┐
│              FEWER LAYERS = BETTER                           │
│                                                              │
│  ✅ Fewer layers                                            │
│  ✅ Faster build (especially for heavy steps)               │
│  ✅ Often smaller (when caches are removed in same layer)   │
│  ✅ Cleaner image history                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.6 Method 4 — Avoid Installing Unnecessary Dependencies

### The Problem

When you install packages using a package manager (`apt`, `yum`, `apk`), the manager:
- Installs the requested package
- ALSO installs recommended/dependent packages
- Many of these may not be required for your application

This increases image size, attack surface, and vulnerability risk.

### Bloated Example

```dockerfile
FROM ubuntu:20.04

RUN apt-get update
RUN apt-get install -y vim net-tools dnsutils
```

```bash
$ docker build -t image1:m4 -f Dockerfile_1 .
$ docker images
# REPOSITORY   TAG   SIZE
# image1       m4    237MB
```

### Optimized Version — Use --no-install-recommends

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        vim \
        net-tools \
        dnsutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### What Each Flag Does

```
┌─────────────────────────────────────────────────────────────┐
│  --no-install-recommends                                    │
│    Prevents installing extra suggested dependencies         │
│    Can save 50-200MB per image                              │
│                                                              │
│  apt-get clean                                              │
│    Removes cached .deb files                                │
│                                                              │
│  rm -rf /var/lib/apt/lists/*                                │
│    Deletes package metadata cache                           │
│                                                              │
│  Result:                                                    │
│    Smaller image                                            │
│    Fewer unused packages                                    │
│    Lower vulnerability count                                │
└─────────────────────────────────────────────────────────────┘
```

### Layer Comparison

```
Without cleanup:
  Layer 1 → install packages
  Layer 2 → apt cache still present
  Layer 3 → metadata still present

With cleanup (same RUN):
  Layer 1 → install packages + cleanup
  (no leftover metadata)
```

---

## 12.7 Method 5 — Understand and Use Docker Cache Properly

### What is Docker Cache?

When Docker builds an image:
- Each instruction creates a layer
- Docker stores those layers in `/var/lib/docker`
- This acts as a **cache**

### How Cache Works

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER BUILD CACHE                              │
│                                                              │
│  When building:                                             │
│    Docker checks if a layer already exists                  │
│    If YES → reuse (fast, shows "Using cache")               │
│    If NO  → build new layer                                 │
│                                                              │
│  First Build:                                               │
│    All layers created from scratch                          │
│                                                              │
│  Second Build (nothing changed):                            │
│    All layers reused from cache (super fast)                │
└─────────────────────────────────────────────────────────────┘
```

### Practical Example

```dockerfile
FROM ubuntu:20.04
COPY file1.txt .
COPY file2.txt .
COPY file3.txt .
```

```bash
# First build — all layers created
$ docker build -t image1:m5 .

# Add COPY file4.txt to Dockerfile, build again:
$ docker build -t image2:m5 .

# Output:
# Step 1: Using cache
# Step 2: Using cache
# Step 3: Using cache
# Step 4: COPY file4.txt    ← only this step builds
```

### Cache Chain Dependency (Critical Rule)

Docker cache is **chain-based**. If an earlier layer changes, ALL later layers rebuild.

**Bad Layer Ordering:**

```dockerfile
FROM ubuntu:20.04
COPY . .                          # Changes often (any file change)
RUN apt-get update                # Rebuilds every time!
RUN apt-get install -y python3    # Rebuilds every time!
```

If you change ANY file in your project:
- `COPY . .` changes → everything after it rebuilds
- Install step runs again (slow)

**Optimized Layer Ordering:**

```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y python3    # Rarely changes

COPY . .                                             # Changes often
```

Now:
- If files change → only `COPY` layer rebuilds
- Install layer reused from cache

### Layer Ordering Diagram

```
BAD ORDER:
  Layer 1 → Base
  Layer 2 → COPY (changes often)        ← invalidates cache
  Layer 3 → Install packages            ← rebuilds every time!

GOOD ORDER:
  Layer 1 → Base
  Layer 2 → Install packages (rarely changes)  ← cached
  Layer 3 → COPY (changes often)               ← only this rebuilds
```

### Production Rule

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKERFILE ORDERING RULE                        │
│                                                              │
│  Put RARELY-CHANGING instructions FIRST:                    │
│    ✅ OS updates                                            │
│    ✅ Package installs                                      │
│    ✅ Dependencies (package.json, requirements.txt)         │
│                                                              │
│  Put FREQUENTLY-CHANGING instructions LAST:                 │
│    ✅ Source code (COPY . .)                                │
│    ✅ Config files                                          │
│    ✅ Build artifacts                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.8 Method 6 — Explore Image Layers (Using Dive)

You must not blindly trust your image. You must analyze:
- How many layers?
- What files exist?
- How much space is wasted?
- Efficiency score?

### Tool: dive

Dive is an open-source tool to inspect Docker images layer by layer.

```bash
# Run dive as a container (no installation needed)
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest <image_name>
```

### What Dive Shows

```
┌─────────────────────────────────────────────────────────────┐
│              DIVE OUTPUT                                     │
│                                                              │
│  Left Panel:                                                │
│    Layer list                                               │
│    Size per layer                                           │
│    Efficiency score                                         │
│                                                              │
│  Right Panel:                                               │
│    Files added per layer                                    │
│    Files removed                                            │
│    Duplicate files                                          │
│                                                              │
│  Bottom:                                                    │
│    Wasted space                                             │
│    Efficiency %                                             │
│    Suggested improvements                                   │
└─────────────────────────────────────────────────────────────┘
```

### Example Output Interpretation

```
Efficiency: 95%
Wasted Space: 11MB

Means:
  95% of space used effectively
  11MB is redundant (duplicates, deleted files still in layers)
```

### CI/CD Integration (Automated Quality Gate)

Do NOT manually run dive. Use CI mode in your pipeline:

```bash
$ dive --ci --lowestEfficiency 0.8 --highestWastedBytes 20000000 image:tag
```

```
--ci                    → machine-readable output
--lowestEfficiency 0.8  → fail if efficiency < 80%
--highestWastedBytes    → fail if wasted space > limit
```

### CI Pipeline Flow

```
1. docker build → build image
2. dive --ci check → analyze image
3. if pass → push image to registry
4. if fail → break pipeline, fix Dockerfile
```

---

## 12.9 Method 7 — Use .dockerignore and Avoid Duplicate Files

### Problem 1: Copying Everything

```dockerfile
COPY . .
```

This copies EVERYTHING into the image:
- Source code
- Logs
- Git files (.git/)
- Test files
- Dockerfile itself
- Temp files
- node_modules/

### Solution: .dockerignore

Create a `.dockerignore` file in your project root:

```
# .dockerignore — recommended baseline
.git
.gitignore
Dockerfile*
docker-compose*.yml
*.log
*.tmp
node_modules
dist
build
coverage
__pycache__
.env
.env.*
*.pem
*.key
.vscode
.idea
.DS_Store
```

### How It Works

```
Without .dockerignore:
  Project/
    app.py
    debug.log       ← copied (unnecessary)
    Dockerfile      ← copied (unnecessary)
    .git/           ← copied (unnecessary, large!)

  COPY . .  → ALL files copied into image

With .dockerignore:
  *.log             ← ignored
  Dockerfile        ← ignored
  .git              ← ignored

  COPY . .  → only app.py copied
```

### Problem 2: Duplicate Files Across Layers

```dockerfile
COPY file.txt .
RUN chmod +x file.txt
RUN echo "hello" >> file.txt
RUN mv file.txt file2.txt
RUN rm file2.txt
```

You might think the final image has no file. **Wrong.**

Internally, each layer stores a copy:

```
Layer 1 → file.txt (100KB)
Layer 2 → modified file.txt (100KB)    ← copy created
Layer 3 → modified again (100KB)       ← copy created
Layer 4 → renamed (100KB)              ← copy created
Layer 5 → deleted                      ← but old layers remain

Total stored: ~400KB
Even though final result has NO file!
```

### Fix: Consolidate Operations

```dockerfile
COPY file.txt .
RUN chmod +x file.txt && \
    echo "hello" >> file.txt && \
    mv file.txt file2.txt && \
    rm file2.txt
```

Now:
- Only ONE layer for all modifications
- No duplicates across layers

---

## 12.10 Method 8 — Squashing Layers

### What is Squashing?

Squashing = merge multiple layers into fewer layers. Similar to `git squash`.

```
Before squash:
  Layer 1
  Layer 2
  Layer 3
  Layer 4
  Layer 5

After squash:
  Layer 1 + 2 + 3 + 4 + 5 → Single Layer

Removes duplicates across layers.
```

### Tool: docker-squash

```bash
# Install
$ pip install docker-squash

# Squash entire image
$ docker-squash -t newimage:tag originalimage:tag

# Squash from a specific layer
$ docker-squash -f <layer_id> -t newimage:tag originalimage:tag
```

### What Happens

- Original image remains untouched
- New squashed image created
- Duplicate layers merged
- Wasted space eliminated

### Verify with Dive

```bash
$ dive newimage:tag

# You'll see:
#   Fewer layers
#   Lower wasted space
#   Higher efficiency score
```

---

## 12.11 Commands Quick Reference

```bash
# Build an image
$ docker build -t <name>:<tag> -f <dockerfile> .

# List images (check sizes)
$ docker images

# Show how an image was built (layers)
$ docker history <image>:<tag>

# Run a container (auto-remove after exit)
$ docker run --rm <image>:<tag>

# Run in background with port mapping
$ docker run -d -p 8080:8080 <image>:<tag>

# Test locally
$ curl localhost:8080

# Copy file from container to host
$ docker cp <container>:/path/in/container /path/on/host

# Remove images
$ docker rmi <image_id>
$ docker rmi -f $(docker images -aq)

# Clean dangling images
$ docker image prune

# Analyze image layers
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive:latest <image_name>

# Squash layers
$ docker-squash -t newimage:tag originalimage:tag
```

---

## 12.12 Production Checklist

```
┌─────────────────────────────────────────────────────────────┐
│              BEFORE PUSHING TO PRODUCTION                    │
│                                                              │
│  ✅ 1. Use minimal base image (Alpine / slim variant)       │
│  ✅ 2. Use multi-stage builds                               │
│  ✅ 3. Combine RUN instructions (fewer layers)              │
│  ✅ 4. Use --no-install-recommends                          │
│  ✅ 5. Clean package caches in same layer                   │
│         Debian/Ubuntu: rm -rf /var/lib/apt/lists/*          │
│         Alpine: apk add --no-cache                          │
│  ✅ 6. Order Dockerfile correctly for caching               │
│         Rarely-changing first, frequently-changing last     │
│  ✅ 7. Use .dockerignore                                    │
│  ✅ 8. Avoid duplicate file modifications across layers     │
│  ✅ 9. Analyze using dive                                   │
│  ✅ 10. Optionally squash layers                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.13 Optimization Methods Summary

```
┌──────────┬──────────────────────────────────┬──────────────┐
│ Method   │ Technique                        │ Impact       │
├──────────┼──────────────────────────────────┼──────────────┤
│ 1        │ Minimal base image (Alpine/slim) │ 60-90% less  │
│ 2        │ Multi-stage builds               │ Up to 95%+   │
│ 3        │ Fewer layers (combine RUN)       │ Faster builds│
│ 4        │ --no-install-recommends          │ 50-200MB less│
│ 5        │ Cache-friendly ordering          │ Faster builds│
│ 6        │ Analyze with dive               │ Find waste   │
│ 7        │ .dockerignore + no duplicates    │ Smaller ctx  │
│ 8        │ Squash layers                    │ Remove dupes │
└──────────┴──────────────────────────────────┴──────────────┘
```

---

## 12.14 Final Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│              OPTIMIZED DOCKER IMAGE SHOULD BE                │
│                                                              │
│  ✅ Small         — minimal base, no unnecessary packages   │
│  ✅ Fast to build — cache-friendly ordering, fewer layers   │
│  ✅ Fast to pull  — smaller size = faster registry transfer  │
│  ✅ Fast to start — less to unpack and initialize           │
│  ✅ Low vulnerability — fewer packages = smaller surface    │
│  ✅ High efficiency — verified with dive                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.15 Production Dockerfile Templates

### Template A: Node.js (Build + Runtime)

```dockerfile
# Build stage
FROM node:20-slim AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage
FROM node:20-slim
WORKDIR /app

ENV NODE_ENV=production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

```
Notes:
  ✅ Keeps build tooling out of runtime
  ✅ Cache-friendly dependency install (package.json first)
  ✅ NODE_ENV=production for optimized runtime
  ✅ Only dist/ and node_modules/ in final image
```

### Template B: Python (Fast, Lean)

```dockerfile
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OS deps (only if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
```

```
Notes:
  ✅ PYTHONDONTWRITEBYTECODE=1 → no .pyc files
  ✅ PYTHONUNBUFFERED=1 → logs appear immediately
  ✅ pip --no-cache-dir → no pip cache in image
  ✅ requirements.txt copied first for cache efficiency
```

### Template C: Java (Multi-Stage with Maven)

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=builder /src/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
```

```
Notes:
  ✅ Builder has Maven + JDK (large, ~800MB)
  ✅ Runtime has only JRE (much smaller, ~200MB)
  ✅ No source code or build tools in final image
  ✅ -DskipTests for faster builds in CI
```

---

## 12.16 Security and Reliability Hardening

### 1) Run as Non-Root User

```dockerfile
# Debian/Ubuntu
RUN useradd -m appuser
USER appuser

# Alpine
RUN adduser -D appuser
USER appuser
```

```
┌─────────────────────────────────────────────────────────────┐
│  Why non-root?                                              │
│                                                              │
│  If container is compromised, attacker gets root access     │
│  to the container filesystem and potentially the host.      │
│                                                              │
│  Non-root limits the blast radius of a breach.              │
└─────────────────────────────────────────────────────────────┘
```

### 2) Don't Bake Secrets into the Image

```
┌─────────────────────────────────────────────────────────────┐
│              NEVER DO THIS                                   │
│                                                              │
│  ❌ COPY .env /app/.env                                    │
│  ❌ ENV API_KEY=sk-abc123...                                │
│  ❌ COPY credentials.json /app/                             │
│  ❌ RUN echo "password" > /app/config                      │
│                                                              │
│  Secrets in layers are PERMANENT — even if deleted later.   │
│  Anyone with image access can extract them.                 │
│                                                              │
│  ✅ Use runtime injection:                                  │
│     - Kubernetes secrets                                    │
│     - CI/CD secret variables                                │
│     - Docker secrets (Swarm)                                │
│     - Environment variables at runtime (-e flag)            │
└─────────────────────────────────────────────────────────────┘
```

### 3) Add a HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -qO- http://localhost:8080/health || exit 1
```

```
Why:
  Container "running" ≠ app "healthy"
  HEALTHCHECK lets Docker/orchestrator detect broken apps
  Unhealthy containers get restarted automatically
```

### 4) Pin Versions for Reproducibility

```dockerfile
# ❌ Bad — unpredictable
FROM python:latest
FROM node:lts

# ✅ Good — deterministic
FROM python:3.12-slim
FROM node:20.11-slim
```

```
┌─────────────────────────────────────────────────────────────┐
│              PIN EVERYTHING                                  │
│                                                              │
│  ✅ Pin base image tags (python:3.12-slim, not :latest)     │
│  ✅ Pin OS packages when possible                           │
│  ✅ Pin language deps:                                      │
│     - package-lock.json (Node.js)                           │
│     - requirements.txt with hashes (Python)                 │
│     - go.sum (Go)                                           │
│     - pom.xml with versions (Java)                          │
│                                                              │
│  Unpinned = different builds produce different images       │
│  Pinned = same build always produces same image             │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.17 CI/CD Quality Gate Blueprint

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────┐
│              BUILD → VERIFY → PUSH → DEPLOY                 │
│                                                              │
│  Stage 1: Build                                             │
│    docker build -t myapp:${GIT_SHA} .                       │
│                                                              │
│  Stage 2: Dive efficiency gate                              │
│    dive --ci myapp:${GIT_SHA}                               │
│      --lowestEfficiency 0.9                                 │
│      --highestWastedBytes 10000000                          │
│                                                              │
│  Stage 3: Security scan gate                                │
│    (trivy, snyk, grype — your org's tool)                   │
│                                                              │
│  Stage 4: Push to registry                                  │
│    docker push myapp:${GIT_SHA}                             │
│                                                              │
│  Stage 5: Deploy                                            │
│    (Kubernetes, Swarm, ECS, etc.)                           │
└─────────────────────────────────────────────────────────────┘
```

### Example Pipeline Commands

```bash
# Build with git SHA tag
$ docker build -t myapp:${GIT_SHA} .

# Efficiency gate — fail if below threshold
$ dive --ci myapp:${GIT_SHA} \
    --lowestEfficiency 0.9 \
    --highestWastedBytes 10000000

# If passed → push
$ docker push myapp:${GIT_SHA}
```

---

## 12.18 Dockerfile Checklist (Before Merge)

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKERFILE REVIEW CHECKLIST                     │
│                                                              │
│  ☐ Base image is slim or alpine where possible              │
│  ☐ Multi-stage used for build-heavy stacks                  │
│  ☐ apt-get installs use --no-install-recommends             │
│  ☐ Cache cleaned in same layer:                             │
│      rm -rf /var/lib/apt/lists/*                            │
│      pip --no-cache-dir                                     │
│      apk --no-cache                                         │
│  ☐ COPY ordering optimized (deps first, code last)          │
│  ☐ .dockerignore present and correct                        │
│  ☐ No secrets copied (no .env, no keys, no .pem)            │
│  ☐ Non-root user (USER directive)                           │
│  ☐ HEALTHCHECK defined (if service-based)                   │
│  ☐ Base image version pinned (not :latest)                  │
│  ☐ Dependency lock files used                               │
│  ☐ Logs go to stdout/stderr (not files)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.19 Troubleshooting — Image Still Too Large

```
┌─────────────────────────────────────────────────────────────┐
│              IF IMAGE IS STILL LARGE                         │
│                                                              │
│  Step 1: Use dive → identify biggest layer and file paths   │
│                                                              │
│  Step 2: Look for common culprits:                          │
│    ❌ Build artifacts in runtime stage                      │
│    ❌ Package caches not cleaned                            │
│    ❌ COPY . . pulling in junk (missing .dockerignore)      │
│    ❌ Duplicate files (same binary modified across layers)  │
│    ❌ Full base image instead of slim/alpine                │
│    ❌ Dev dependencies in production image                  │
│                                                              │
│  Step 3: Convert to multi-stage if not already              │
│                                                              │
│  Step 4: Check docker history <image>                       │
│    → Find which layer is largest                            │
│    → Investigate what that RUN/COPY added                   │
│                                                              │
│  Step 5: Run dive --ci to set automated thresholds          │
└─────────────────────────────────────────────────────────────┘
```

---

## 12.20 Which Method Solves Which Problem?

```
┌──────────────────────────────┬──────────────────────────────┐
│ Problem                      │ Method                       │
├──────────────────────────────┼──────────────────────────────┤
│ Huge base OS                 │ Method 1 — Alpine/slim       │
│ Build tools bloating runtime │ Method 2 — Multi-stage       │
│ Too many layers              │ Method 3 — Combine RUN       │
│ Extra dependencies & caches  │ Method 4 — --no-install-rec  │
│ Slow rebuilds                │ Method 5 — Cache ordering    │
│ No visibility into contents  │ Method 6 — dive              │
│ Unnecessary files & dupes    │ Method 7 — .dockerignore     │
│ Legacy images, messy layers  │ Method 8 — Squash            │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 12.21 Core Concepts Recap

### Images Are Layers

```
Each RUN, COPY, ADD creates a new immutable layer.

Impact:
  More layers → larger image + slower build/pull
  Modifying same file across layers → duplicate data stays
```

### Caching Is a Chain

```
Docker cache reuse depends on:
  1. Instruction text + inputs being identical
  2. ALL previous layers being identical

If a layer changes early → everything after rebuilds.
```

---

## 12.9 Language-Specific Dependency Optimization

### Python: Pipenv and Production Serving with Gunicorn

```dockerfile
# syntax=docker/dockerfile:1

# --- Using Pipenv (alternative to pip + requirements.txt) ---
FROM python:3.12-slim AS builder
WORKDIR /app

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy dependency files
COPY Pipfile Pipfile.lock ./

# Install dependencies from Pipfile.lock (deterministic)
RUN pipenv install --deploy --ignore-pipfile --system
#   --deploy:       fail if Pipfile.lock is out of date
#   --ignore-pipfile: use ONLY Pipfile.lock (not Pipfile)
#   --system:       install into system Python (not virtualenv)

COPY . .

# --- Production stage with Gunicorn ---
FROM python:3.12-slim
WORKDIR /app

RUN pip install --no-cache-dir gunicorn

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app

RUN addgroup --system app && adduser --system --group app
USER app

EXPOSE 8000

# Gunicorn serves the Flask/Django app in production
# -w 4: 4 worker processes (rule of thumb: 2 × CPU cores + 1)
# -b 0.0.0.0:8000: bind to all interfaces on port 8000
# app:app: module:variable (Flask app object)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

```
# Why Gunicorn instead of Flask's built-in server:
#
# Flask's dev server (app.run()):
#   - Single-threaded, single-process
#   - No connection queuing
#   - Not designed for production load
#   - Prints "WARNING: This is a development server"
#
# Gunicorn (Green Unicorn):
#   - Pre-fork worker model (multiple processes)
#   - Handles concurrent requests
#   - Graceful worker restart on failure
#   - Production-grade WSGI server
#
# For Django, replace "app:app" with "myproject.wsgi:application"
```

### Node.js: npm ci vs npm install

```dockerfile
# --- Production Node.js ---
FROM node:20-alpine
WORKDIR /app

COPY package.json package-lock.json ./

# npm ci (Clean Install) — preferred for CI/CD and production
RUN npm ci --omit=dev
#   npm ci:
#     - Deletes node_modules/ first (clean state)
#     - Installs EXACT versions from package-lock.json
#     - Fails if package-lock.json is out of sync with package.json
#     - Faster than npm install in CI environments
#   --omit=dev:
#     - Skips devDependencies (test frameworks, linters, etc.)
#     - Reduces node_modules size by 30-70%

COPY . .
CMD ["node", "server.js"]
```

```
# npm ci vs npm install:
#
# ┌──────────────────┬──────────────────────┬──────────────────────┐
# │                  │ npm install          │ npm ci               │
# ├──────────────────┼──────────────────────┼──────────────────────┤
# │ Reads            │ package.json         │ package-lock.json    │
# │ Deterministic    │ No (may resolve new) │ Yes (exact versions) │
# │ Deletes modules  │ No                   │ Yes (clean install)  │
# │ Updates lockfile │ Yes (if needed)      │ Never                │
# │ Speed            │ Slower               │ Faster               │
# │ Use in CI/CD     │ Not recommended      │ Recommended          │
# └──────────────────┴──────────────────────┴──────────────────────┘
```

### Java: Maven Dependency Caching

```dockerfile
# syntax=docker/dockerfile:1
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app

# Copy ONLY pom.xml first — dependencies change less often than code
COPY pom.xml .
RUN mvn dependency:go-offline
#   Downloads all dependencies to local Maven cache
#   This layer is cached as long as pom.xml doesn't change

# Now copy source code and build
COPY src ./src
RUN mvn clean package -DskipTests

# Production stage — JRE only (no Maven, no JDK)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/app.jar app.jar

RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 12.10 docker-slim — Automatic Image Minification

docker-slim (now called SlimToolkit) analyzes a running container
and automatically removes everything not used at runtime.

### How docker-slim Works

```
# 1. Builds and runs your container temporarily
# 2. Monitors which files, libraries, and binaries are accessed
# 3. Creates a new image containing ONLY the accessed files
# 4. Result: dramatically smaller image with reduced attack surface
#
# Typical results:
#   Node.js app:  900MB → 30MB  (97% reduction)
#   Python app:   600MB → 50MB  (92% reduction)
#   Go app:       300MB → 6MB   (98% reduction)
```

### Installation and Usage

```bash
# Install docker-slim
# macOS
$ brew install docker-slim

# Linux
$ curl -sL https://raw.githubusercontent.com/slimtoolkit/slim/master/scripts/install-slim.sh | sudo -E bash -

# Basic usage — analyze and minify an image
$ slim build myapp:latest
# [slim] inspecting image...
# [slim] starting instrumented container...
# [slim] collecting data...
# [slim] building minified image...
# [slim] myapp.slim:latest - size: 32MB (was 900MB)

# The minified image is tagged as myapp.slim:latest
$ docker images | grep myapp
# myapp        latest    900MB
# myapp.slim   latest    32MB
```

### Advanced Options

```bash
# Include specific paths that might not be detected at runtime
$ slim build --include-path=/app/config --include-path=/app/templates myapp:latest

# Include specific binaries
$ slim build --include-bin=/usr/bin/curl myapp:latest

# Expose HTTP probes for web applications
$ slim build --http-probe=true myapp:latest

# Keep shell access in the minified image (for debugging)
$ slim build --include-shell myapp:latest

# Generate a Seccomp profile from the analysis
$ slim build --include-seccomp myapp:latest
# Outputs a seccomp profile based on actual syscalls used
```

### When to Use docker-slim

```
┌──────────────────────┬──────────────────────────────────────────┐
│ Good For             │ Not Recommended For                      │
├──────────────────────┼──────────────────────────────────────────┤
│ Web APIs and servers │ Containers with dynamic file access      │
│ Microservices        │ Containers that load plugins at runtime  │
│ CLI tools            │ Development/debug images                 │
│ Static file servers  │ Images where you need shell access       │
│ Go/Rust binaries     │ Complex init scripts with many branches  │
└──────────────────────┴──────────────────────────────────────────┘
```

### Real-World Example

```bash
# Before: Standard Node.js image
$ docker images myapp
# REPOSITORY   TAG      SIZE
# myapp        latest   943MB

# Run docker-slim
$ slim build --http-probe=true --include-path=/app/views myapp:latest

# After: Minified image
$ docker images myapp.slim
# REPOSITORY   TAG      SIZE
# myapp.slim   latest   35MB

# Verify the minified image works
$ docker run -d -p 3000:3000 myapp.slim:latest
$ curl http://localhost:3000/health
# {"status":"ok"}

# Compare vulnerability scan results
$ trivy image myapp:latest 2>/dev/null | tail -1
# Total: 142 (CRITICAL: 3, HIGH: 28, MEDIUM: 67, LOW: 44)

$ trivy image myapp.slim:latest 2>/dev/null | tail -1
# Total: 8 (CRITICAL: 0, HIGH: 1, MEDIUM: 4, LOW: 3)
# Fewer files = fewer vulnerabilities
```

---

## 12.11 Container-Optimized Operating Systems

For production Docker hosts, consider using an OS designed specifically
for running containers.

```
┌──────────────────────┬──────────────────────────────────────────┐
│ OS                   │ Description                              │
├──────────────────────┼──────────────────────────────────────────┤
│ Google Container-    │ Minimal OS for GKE. Auto-updates.        │
│ Optimized OS (COS)   │ Read-only root filesystem. Locked down.  │
├──────────────────────┼──────────────────────────────────────────┤
│ AWS Bottlerocket     │ Minimal OS for EKS/ECS. API-driven       │
│                      │ configuration (no SSH by default).        │
│                      │ Automatic security updates.               │
├──────────────────────┼──────────────────────────────────────────┤
│ Flatcar Container    │ Successor to CoreOS. Automatic updates    │
│ Linux               │ via Nebraska. Immutable infrastructure.   │
├──────────────────────┼──────────────────────────────────────────┤
│ Talos Linux          │ Kubernetes-focused. No SSH, no shell.     │
│                      │ Managed entirely via API. Immutable.      │
├──────────────────────┼──────────────────────────────────────────┤
│ Ubuntu Core          │ Snap-based minimal Ubuntu. Transactional  │
│                      │ updates. IoT and container workloads.     │
└──────────────────────┴──────────────────────────────────────────┘
```

```
# Why use a container-optimized OS instead of Ubuntu/CentOS?
#
# 1. Smaller attack surface — no package manager, no unnecessary services
# 2. Automatic security updates — OS patches without manual intervention
# 3. Immutable root filesystem — prevents runtime tampering
# 4. Faster boot time — minimal services to start
# 5. Designed for orchestrators — optimized for Docker/Kubernetes
#
# Trade-off: Limited ability to install debugging tools on the host.
# Use debug containers or sidecar patterns instead.
```

---

## Module 12 Summary

- A production image should be **small, deterministic, secure, fast to build, and observable**
- Docker images are built from **layers** — every RUN/COPY/ADD creates a layer
- **Method 1**: Use Alpine (~5MB) or slim variants instead of full OS images (60-90% reduction)
  - Watch for Alpine's musl vs glibc compatibility issues
- **Method 2**: Multi-stage builds keep build tools out of final image (up to 95%+ reduction)
- **Method 3**: Combine RUN instructions to minimize layers — use `&&` and `\`
- **Method 4**: Use `--no-install-recommends` and clean caches in the same layer
- **Method 5**: Order Dockerfile for cache efficiency — rarely-changing first, code last
- **Method 6**: Use `dive` to analyze layers, find wasted space, and set CI quality gates
- **Method 7**: Use `.dockerignore` to exclude logs, .git, node_modules, secrets from build context
- **Method 7b**: Avoid modifying files across multiple layers — consolidate in one RUN
- **Method 8**: Squash layers with `docker-squash` to merge and remove duplicates
- **Production templates**: Node.js, Python, Java multi-stage Dockerfiles ready to use
- **Security hardening**: non-root user, no baked secrets, HEALTHCHECK, pinned versions
- **CI/CD quality gate**: build → dive efficiency check → security scan → push → deploy
- **Troubleshooting**: use `dive` and `docker history` to find biggest layers and culprits
- **Pin everything**: base image tags, OS packages, language dependencies for reproducibility

---

**Previous Module: [Module 11 - Container Orchestration and Docker Swarm](module-11-orchestration.md)**
