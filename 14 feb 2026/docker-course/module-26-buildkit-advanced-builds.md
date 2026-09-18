# Module 26: BuildKit and Advanced Build Patterns

BuildKit is Docker's next-generation build engine. This module covers
its architecture, cache mounts, secret/SSH forwarding, multi-platform
builds, SBOM generation, and provenance attestations.

### Topics Covered

```
26.1  What is BuildKit and Why It Matters
26.2  Enabling and Configuring BuildKit
26.3  BuildKit Architecture (LLB, Frontends, Exporters)
26.4  Cache Mounts — Persistent Build Caches
26.5  Secret Mounts — Build-Time Secrets Without Leaking
26.6  SSH Mounts — Private Repository Access During Build
26.7  Multi-Platform Builds (buildx + QEMU)
26.8  Build Arguments, Target Stages, and Conditional Logic
26.9  Custom Build Outputs (local, tar, OCI, registry)
26.10 SBOM and Provenance Attestations
26.11 Bake — Declarative Build Orchestration
26.12 Common Errors and Troubleshooting
```

---

## 26.1 What is BuildKit and Why It Matters

```
# Legacy builder (docker build):
#   - Sequential layer execution (each RUN waits for the previous)
#   - No concurrent stage builds
#   - Secrets leak into image layers
#   - No SSH agent forwarding
#   - No cache mounts
#   - No multi-platform support
#
# BuildKit (DOCKER_BUILDKIT=1 or docker buildx):
#   - Parallel execution of independent stages
#   - Cache mounts for package managers (npm, pip, apt)
#   - Secret mounts that never appear in layers
#   - SSH forwarding for private git repos
#   - Multi-platform builds (arm64, amd64, etc.)
#   - SBOM and provenance attestations
#   - Garbage-collected build cache
```

### Performance Comparison

```
┌──────────────────────────┬──────────────┬──────────────┐
│ Feature                  │ Legacy       │ BuildKit     │
├──────────────────────────┼──────────────┼──────────────┤
│ Parallel stage execution │ ✗            │ ✓            │
│ Skip unused stages       │ ✗            │ ✓            │
│ Cache mounts             │ ✗            │ ✓            │
│ Secret mounts            │ ✗            │ ✓            │
│ SSH forwarding           │ ✗            │ ✓            │
│ Multi-platform           │ ✗            │ ✓            │
│ Inline cache export      │ ✗            │ ✓            │
│ Progress output          │ Basic        │ Rich (tty)   │
│ Build speed (typical)    │ Baseline     │ 2-10x faster │
└──────────────────────────┴──────────────┴──────────────┘
```

---

## 26.2 Enabling and Configuring BuildKit

```bash
# Method 1: Environment variable (per command)
$ DOCKER_BUILDKIT=1 docker build -t myapp .

# Method 2: Docker daemon config (permanent)
# /etc/docker/daemon.json:
{
    "features": {
        "buildkit": true
    }
}
$ sudo systemctl restart docker

# Method 3: Use docker buildx (always uses BuildKit)
$ docker buildx build -t myapp .

# Verify BuildKit is active (look for the progress bar output)
$ docker build -t test .
# [+] Building 12.3s (8/8) FINISHED    ← BuildKit output
# vs legacy output: "Step 1/5 : FROM ..."

# Check buildx version
$ docker buildx version
# github.com/docker/buildx v0.12.1 ...
```

### BuildKit Daemon Configuration

```bash
# Create a custom builder instance with specific settings
$ docker buildx create --name mybuilder \
    --driver docker-container \
    --config /etc/buildkitd.toml

# /etc/buildkitd.toml
[worker.oci]
  max-parallelism = 4
  gc = true
  gckeepstorage = 10000000000  # 10GB cache limit

[registry."docker.io"]
  mirrors = ["mirror.gcr.io"]

[registry."registry.example.com"]
  http = true   # allow insecure registry
  insecure = true

# Use the custom builder
$ docker buildx use mybuilder

# List builders
$ docker buildx ls
# NAME/NODE    DRIVER/ENDPOINT   STATUS    PLATFORMS
# mybuilder    docker-container  running   linux/amd64, linux/arm64
# default      docker            running   linux/amd64
```

---

## 26.3 BuildKit Architecture (LLB, Frontends, Exporters)

```
┌─────────────────────────────────────────────────────────────────┐
│                    BuildKit Architecture                        │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Frontend     │    │  Solver      │    │  Exporter    │      │
│  │              │    │              │    │              │      │
│  │ Dockerfile   │───▶│ LLB DAG      │───▶│ Image        │      │
│  │ (gateway)    │    │ (parallel    │    │ Registry     │      │
│  │              │    │  execution)  │    │ Local tar    │      │
│  │ Custom       │    │              │    │ OCI layout   │      │
│  │ frontends    │    │ Cache mgmt   │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
│  Frontend: Parses Dockerfile → produces LLB                    │
│  LLB: Low-Level Build definition (DAG of operations)           │
│  Solver: Executes LLB ops in parallel where possible           │
│  Exporter: Packages result as image, tar, or local files       │
└─────────────────────────────────────────────────────────────────┘
```

### LLB — Low-Level Build Definition

```
# LLB is a binary protocol (protobuf) that represents build steps
# as a Directed Acyclic Graph (DAG).
#
# Example: Multi-stage Dockerfile
#
#   FROM golang AS builder
#   RUN go build -o /app
#
#   FROM node AS frontend
#   RUN npm run build
#
#   FROM alpine
#   COPY --from=builder /app /app
#   COPY --from=frontend /dist /dist
#
# LLB DAG:
#
#   [golang base] ──▶ [go build] ──┐
#                                   ├──▶ [alpine + COPY] ──▶ [final image]
#   [node base] ──▶ [npm build] ──┘
#
# BuildKit runs "go build" and "npm build" IN PARALLEL
# because they are independent branches of the DAG.
# Legacy builder would run them sequentially.
```

---

## 26.4 Cache Mounts — Persistent Build Caches

Cache mounts persist package manager caches across builds,
avoiding re-downloading dependencies every time.

### The Problem Without Cache Mounts

```dockerfile
# Every build re-downloads ALL dependencies from scratch
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# pip downloads 200MB of packages every single build
# Even if requirements.txt hasn't changed, cache invalidation
# from earlier layers forces a full re-download
```

### Solution: Cache Mounts

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
# pip's download cache persists between builds
# Only new/changed packages are downloaded
```

```
# --mount=type=cache explained:
#
#   type=cache     — persistent cache directory
#   target=<path>  — where to mount inside the build container
#   id=<id>        — optional cache identifier (for sharing)
#   sharing=shared — allow concurrent access (default: shared)
#   sharing=locked — exclusive access (for non-concurrent tools)
#   sharing=private — private copy per build
```

### Cache Mounts for Every Package Manager

```dockerfile
# syntax=docker/dockerfile:1

# --- Go modules ---
FROM golang:1.22
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app ./cmd/server

# --- Node.js (npm) ---
FROM node:20
WORKDIR /app
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline
COPY . .
RUN npm run build

# --- Node.js (yarn) ---
FROM node:20
WORKDIR /app
COPY package.json yarn.lock ./
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn \
    yarn install --frozen-lockfile

# --- APT (Debian/Ubuntu) ---
FROM ubuntu:22.04
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y curl git

# --- Maven (Java) ---
FROM maven:3.9
WORKDIR /app
COPY pom.xml .
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn dependency:go-offline
COPY src ./src
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn package -DskipTests

# --- Rust (cargo) ---
FROM rust:1.75
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo build --release
```

### Managing the Build Cache

```bash
# View build cache usage
$ docker buildx du
# ID           RECLAIMABLE  SIZE     LAST ACCESSED
# abc123       true         1.2GB    2 hours ago
# def456       true         800MB    1 day ago

# Prune build cache
$ docker buildx prune
# Remove all unused cache? [y/N] y
# Total: 2.0GB

# Prune cache older than 24 hours
$ docker buildx prune --filter until=24h

# Keep at most 5GB of cache
$ docker buildx prune --keep-storage 5gb
```

---

## 26.5 Secret Mounts — Build-Time Secrets Without Leaking

Secrets mounted during build are never stored in image layers.

### The Problem: Secrets in Layers

```dockerfile
# WRONG — secret is baked into the image layer forever
FROM alpine
ARG NPM_TOKEN
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc
RUN npm install
RUN rm .npmrc
# Even though .npmrc is deleted, it exists in a previous layer!
# Anyone with the image can extract it:
#   docker history --no-trunc <image>
#   docker save <image> | tar -xf - && cat <layer>/layer.tar
```

### Solution: Secret Mounts

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20
WORKDIR /app
COPY package*.json ./

# Mount the secret at build time — never stored in any layer
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install

COPY . .
RUN npm run build
```

```bash
# Build with the secret
$ docker buildx build \
    --secret id=npmrc,src=$HOME/.npmrc \
    -t myapp .

# The .npmrc file is available during the RUN step
# but is NOT present in the final image

# Verify: no trace of the secret in the image
$ docker run --rm myapp cat /root/.npmrc
# cat: /root/.npmrc: No such file or directory

# Multiple secrets
$ docker buildx build \
    --secret id=npmrc,src=$HOME/.npmrc \
    --secret id=aws,src=$HOME/.aws/credentials \
    -t myapp .
```

```dockerfile
# Using multiple secrets in Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    --mount=type=secret,id=aws,target=/root/.aws/credentials \
    pip install -r requirements.txt
```

### Environment Variable Secrets

```bash
# Pass a secret from an environment variable (no file needed)
$ export MY_TOKEN="ghp_abc123..."
$ docker buildx build \
    --secret id=github_token,env=MY_TOKEN \
    -t myapp .
```

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) && \
    git clone https://${GITHUB_TOKEN}@github.com/org/private-repo.git
# Default mount path: /run/secrets/<id>
```

---

## 26.6 SSH Mounts — Private Repository Access During Build

SSH agent forwarding lets builds clone private repos without
copying SSH keys into the image.

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.22

# Configure git to use SSH for private repos
RUN git config --global url."git@github.com:".insteadOf "https://github.com/"

# Mount the SSH agent socket during this RUN step
RUN --mount=type=ssh \
    go mod download

COPY . .
RUN go build -o /app
```

```bash
# Build with SSH agent forwarding
# Your local SSH agent must have the key loaded
$ ssh-add -l
# 256 SHA256:abc... user@host (ED25519)

$ docker buildx build --ssh default -t myapp .

# If your key is in a non-default location:
$ docker buildx build --ssh default=$HOME/.ssh/id_ed25519 -t myapp .

# Named SSH sources (for multiple keys)
$ docker buildx build \
    --ssh github=$HOME/.ssh/github_key \
    --ssh gitlab=$HOME/.ssh/gitlab_key \
    -t myapp .
```

```dockerfile
# Using named SSH sources
# syntax=docker/dockerfile:1
FROM alpine
RUN --mount=type=ssh,id=github \
    git clone git@github.com:org/repo1.git
RUN --mount=type=ssh,id=gitlab \
    git clone git@gitlab.com:org/repo2.git
```

---

## 26.7 Multi-Platform Builds (buildx + QEMU)

Build images for multiple CPU architectures from a single machine.

### Why Multi-Platform Matters

```
# Your CI server is linux/amd64, but you need images for:
#   - linux/amd64   (x86 servers, most cloud VMs)
#   - linux/arm64   (AWS Graviton, Apple Silicon, Raspberry Pi 4)
#   - linux/arm/v7  (Raspberry Pi 3, older ARM devices)
#
# Without multi-platform builds:
#   - Maintain separate Dockerfiles or build scripts per arch
#   - Need physical ARM hardware or cross-compilation toolchains
#   - Manual manifest list creation
#
# With buildx multi-platform:
#   - Single Dockerfile, single build command
#   - QEMU emulation for foreign architectures
#   - Automatic manifest list creation
```

### Setup

```bash
# Install QEMU user-mode emulation (enables running ARM binaries on x86)
$ docker run --privileged --rm tonistiigi/binfmt --install all
# Setting up QEMU for: aarch64, arm, riscv64, ppc64le, s390x, mips64le

# Verify QEMU is registered
$ ls /proc/sys/fs/binfmt_misc/
# qemu-aarch64  qemu-arm  qemu-riscv64  ...

# Create a builder that supports multi-platform
$ docker buildx create --name multiarch --driver docker-container --use
$ docker buildx inspect --bootstrap
# Platforms: linux/amd64, linux/arm64, linux/arm/v7, linux/386, ...
```

### Building Multi-Platform Images

```bash
# Build for multiple platforms and push to registry
$ docker buildx build \
    --platform linux/amd64,linux/arm64,linux/arm/v7 \
    -t myregistry.com/myapp:latest \
    --push \
    .

# Build for multiple platforms and load locally (single platform only)
$ docker buildx build \
    --platform linux/arm64 \
    -t myapp:arm64 \
    --load \
    .

# Build and output to local directory (all platforms)
$ docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t myapp:latest \
    --output type=local,dest=./output \
    .
```

### Platform-Specific Logic in Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM golang:1.22 AS builder

# BUILDPLATFORM = the platform running the build (your machine)
# TARGETPLATFORM = the platform you're building FOR
# TARGETOS = linux
# TARGETARCH = amd64, arm64, arm
# TARGETVARIANT = v7 (for arm)

ARG TARGETOS TARGETARCH

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .

# Cross-compile for the target platform
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o /app/server ./cmd/server

FROM alpine:3.19
COPY --from=builder /app/server /usr/local/bin/server
CMD ["server"]
```

```
# Build variables available in multi-platform builds:
#
# ┌──────────────────┬──────────────────────────────────────────┐
# │ Variable         │ Description                              │
# ├──────────────────┼──────────────────────────────────────────┤
# │ BUILDPLATFORM    │ Platform of the build node (e.g. amd64) │
# │ BUILDOS          │ OS of the build node                     │
# │ BUILDARCH        │ Architecture of the build node           │
# │ BUILDVARIANT     │ Variant of the build node                │
# │ TARGETPLATFORM   │ Platform being built for                 │
# │ TARGETOS         │ Target OS (linux, windows)               │
# │ TARGETARCH       │ Target architecture (amd64, arm64)       │
# │ TARGETVARIANT    │ Target variant (v7 for arm)              │
# └──────────────────┴──────────────────────────────────────────┘
```

### Inspecting Multi-Platform Images

```bash
# View the manifest list (shows all platforms)
$ docker manifest inspect myregistry.com/myapp:latest
# {
#   "manifests": [
#     { "platform": {"architecture":"amd64","os":"linux"}, "digest":"sha256:aaa..." },
#     { "platform": {"architecture":"arm64","os":"linux"}, "digest":"sha256:bbb..." },
#     { "platform": {"architecture":"arm","os":"linux","variant":"v7"}, "digest":"sha256:ccc..." }
#   ]
# }

# Pull a specific platform
$ docker pull --platform linux/arm64 myregistry.com/myapp:latest
```

---

## 26.8 Build Arguments, Target Stages, and Conditional Logic

### Build Arguments (ARG)

```dockerfile
# syntax=docker/dockerfile:1

# Global ARG (available before FROM)
ARG BASE_IMAGE=python:3.12-slim

FROM ${BASE_IMAGE}

# Stage-scoped ARG (must redeclare after FROM)
ARG APP_VERSION=1.0.0
ARG BUILD_ENV=production

LABEL version=${APP_VERSION}

# Conditional logic using ARG
RUN if [ "$BUILD_ENV" = "development" ]; then \
        pip install debugpy pytest; \
    fi

COPY . .
```

```bash
# Override build args at build time
$ docker buildx build \
    --build-arg BASE_IMAGE=python:3.12-alpine \
    --build-arg APP_VERSION=2.1.0 \
    --build-arg BUILD_ENV=development \
    -t myapp:dev .
```

### Target Stages

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20 AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM base AS development
RUN npm install -g nodemon
COPY . .
CMD ["nodemon", "src/index.js"]

FROM base AS test
COPY . .
RUN npm test

FROM base AS production
COPY . .
RUN npm run build
RUN npm prune --production
CMD ["node", "dist/index.js"]
```

```bash
# Build only the development stage
$ docker buildx build --target development -t myapp:dev .

# Build only the test stage (runs tests during build)
$ docker buildx build --target test -t myapp:test .

# Build the production stage (default — last stage)
$ docker buildx build --target production -t myapp:prod .
```

---

## 26.9 Custom Build Outputs (local, tar, OCI, registry)

```bash
# Output to local filesystem (no image created)
$ docker buildx build --output type=local,dest=./build-output .
# Extracts the final stage's filesystem to ./build-output/

# Output as a tar archive
$ docker buildx build --output type=tar,dest=./image.tar .

# Output as OCI image layout
$ docker buildx build --output type=oci,dest=./oci-image .

# Push directly to registry (no local image)
$ docker buildx build --output type=registry -t registry.com/myapp:v1 .
# Same as --push

# Output as Docker image (load into local daemon)
$ docker buildx build --output type=docker -t myapp:latest .
# Same as --load

# Extract only specific files from the build
$ docker buildx build \
    --target builder \
    --output type=local,dest=./bin \
    .
# Useful for extracting compiled binaries without creating an image
```

### Real-World: Extract Build Artifacts

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /app/mybin ./cmd/server
RUN go test -coverprofile=coverage.out ./...

FROM scratch AS artifacts
COPY --from=builder /app/mybin /mybin
COPY --from=builder /app/coverage.out /coverage.out
```

```bash
# Extract just the binary and coverage report — no image needed
$ docker buildx build --target artifacts --output type=local,dest=./dist .
$ ls ./dist/
# mybin  coverage.out
```

---

## 26.10 SBOM and Provenance Attestations

Software Bill of Materials (SBOM) and provenance attestations
provide supply chain security metadata for container images.

### SBOM — What's Inside Your Image

```bash
# Generate SBOM during build
$ docker buildx build \
    --sbom=true \
    -t myapp:latest \
    --push \
    .

# View the SBOM
$ docker buildx imagetools inspect myapp:latest --format '{{json .SBOM}}'
# Lists all packages, versions, and licenses in the image

# SBOM formats supported:
#   SPDX (default) — ISO standard
#   CycloneDX      — OWASP standard
```

### Provenance — How Was the Image Built

```bash
# Generate provenance attestation
$ docker buildx build \
    --provenance=true \
    -t myapp:latest \
    --push \
    .

# View provenance
$ docker buildx imagetools inspect myapp:latest --format '{{json .Provenance}}'
# Shows:
#   - Build timestamp
#   - Builder identity
#   - Source repository and commit
#   - Dockerfile used
#   - Build arguments
#   - Materials (base images and their digests)

# Provenance modes:
#   --provenance=mode=min   — basic metadata
#   --provenance=mode=max   — full build details including Dockerfile
```

### Real-World: Supply Chain Security

```bash
# Build with full attestations for production
$ docker buildx build \
    --sbom=true \
    --provenance=mode=max \
    --platform linux/amd64,linux/arm64 \
    -t registry.com/myapp:v2.1.0 \
    --push \
    .

# Verify image provenance before deploying
$ docker buildx imagetools inspect \
    registry.com/myapp:v2.1.0 \
    --format '{{json .Provenance.SLSA}}'

# Use with cosign for signature verification
$ cosign verify --key cosign.pub registry.com/myapp:v2.1.0
```

---

## 26.11 Bake — Declarative Build Orchestration

`docker buildx bake` reads a declarative file (HCL, JSON, or
docker-compose.yml) to build multiple images with shared config.

### docker-bake.hcl

```hcl
# docker-bake.hcl

# Variables (can be overridden via environment)
variable "REGISTRY" {
    default = "registry.example.com"
}

variable "TAG" {
    default = "latest"
}

# Shared configuration
group "default" {
    targets = ["api", "frontend", "worker"]
}

target "base" {
    dockerfile = "Dockerfile"
    platforms  = ["linux/amd64", "linux/arm64"]
    args = {
        BUILD_DATE = timestamp()
    }
}

target "api" {
    inherits   = ["base"]
    context    = "./services/api"
    tags       = ["${REGISTRY}/api:${TAG}"]
    cache-from = ["type=registry,ref=${REGISTRY}/api:cache"]
    cache-to   = ["type=registry,ref=${REGISTRY}/api:cache,mode=max"]
}

target "frontend" {
    inherits = ["base"]
    context  = "./services/frontend"
    tags     = ["${REGISTRY}/frontend:${TAG}"]
}

target "worker" {
    inherits = ["base"]
    context  = "./services/worker"
    tags     = ["${REGISTRY}/worker:${TAG}"]
}

# CI-specific target with extra settings
target "ci" {
    inherits   = ["base"]
    platforms  = ["linux/amd64"]
    sbom       = true
    provenance = true
}
```

```bash
# Build all targets in the default group
$ docker buildx bake

# Build a specific target
$ docker buildx bake api

# Override variables
$ TAG=v2.1.0 docker buildx bake --push

# Dry run — show what would be built
$ docker buildx bake --print
```

---

## 26.12 Common Errors and Troubleshooting

### Error 1: "failed to solve: rpc error: code = Unknown"

```bash
# Usually a syntax issue in the Dockerfile
# Ensure the syntax directive is on line 1:
# syntax=docker/dockerfile:1

# Check for unsupported features with legacy builder
$ DOCKER_BUILDKIT=1 docker build .  # Force BuildKit
```

### Error 2: "cache mount target already exists"

```bash
# Two concurrent builds using the same cache ID
# Fix: Use sharing=locked for non-concurrent tools
RUN --mount=type=cache,target=/root/.cache,sharing=locked \
    pip install -r requirements.txt
```

### Error 3: Multi-platform build fails with "exec format error"

```bash
# QEMU is not installed or registered
$ docker run --privileged --rm tonistiigi/binfmt --install all

# Verify registration
$ cat /proc/sys/fs/binfmt_misc/qemu-aarch64
# Should show "enabled"
```

### Error 4: "--load does not support multiple platforms"

```bash
# --load only works for a single platform
# For multi-platform, use --push or --output

# Single platform load:
$ docker buildx build --platform linux/amd64 --load -t myapp .

# Multi-platform push:
$ docker buildx build --platform linux/amd64,linux/arm64 --push -t myapp .
```

### Error 5: "secret not found"

```bash
# The --secret flag must match the id in the Dockerfile
$ docker buildx build --secret id=mytoken,src=./token.txt .

# In Dockerfile:
RUN --mount=type=secret,id=mytoken cat /run/secrets/mytoken
# id must match exactly
```

---

## Module 26 Summary

- **BuildKit** replaces the legacy builder with parallel execution, cache mounts, and secret handling
- Enable via `DOCKER_BUILDKIT=1`, daemon.json, or `docker buildx build`
- BuildKit uses **LLB** (Low-Level Build) — a DAG that enables parallel stage execution
- **Cache mounts** (`--mount=type=cache`) persist package manager caches across builds
- **Secret mounts** (`--mount=type=secret`) provide build-time secrets that never appear in layers
- **SSH mounts** (`--mount=type=ssh`) forward SSH agent for private repo access during build
- **Multi-platform builds** use QEMU emulation to build for arm64, arm/v7, etc. from amd64
- Use `$TARGETARCH` and `$TARGETOS` for cross-compilation in Dockerfiles
- **Custom outputs** can extract files, create tarballs, or push directly to registries
- **SBOM** lists all packages in the image; **provenance** records how the image was built
- **Bake** (`docker buildx bake`) orchestrates multi-image builds from declarative HCL/JSON files
- Always use `# syntax=docker/dockerfile:1` as the first line for BuildKit features

---

**Previous Module: [Module 25 - Docker Internals Deep Dive](module-25-docker-internals.md)**

**Next Module: [Module 27 - Docker Logging, Monitoring, and Observability](module-27-logging-monitoring.md)**
