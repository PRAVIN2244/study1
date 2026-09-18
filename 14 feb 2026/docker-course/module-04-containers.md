# Module 4: Docker Containers - Lifecycle, Management, and Deep Dive

---

## 4.1 Container Lifecycle

A container goes through distinct states:

```
                    docker create
                         │
                         ▼
                    ┌─────────┐
                    │ Created  │
                    └────┬────┘
                         │ docker start
                         ▼
    docker restart  ┌─────────┐  docker pause
    ┌──────────────▶│ Running  │──────────────┐
    │               └────┬────┘               ▼
    │                    │              ┌──────────┐
    │                    │              │  Paused   │
    │                    │              └─────┬─────┘
    │                    │                    │ docker unpause
    │                    │◀───────────────────┘
    │                    │
    │                    │ docker stop / process exits
    │                    ▼
    │               ┌─────────┐
    └───────────────│ Exited   │
                    └────┬────┘
                         │ docker rm
                         ▼
                    ┌─────────┐
                    │ Removed  │
                    └─────────┘
```

### Demonstrating Each State

```bash
# CREATE: Container exists but isn't running
docker create --name lifecycle-demo nginx
docker ps -a --filter name=lifecycle-demo
# STATUS: Created

# START: Container begins running
docker start lifecycle-demo
docker ps --filter name=lifecycle-demo
# STATUS: Up 2 seconds

# PAUSE: Freeze all processes (using cgroups freezer)
docker pause lifecycle-demo
docker ps --filter name=lifecycle-demo
# STATUS: Up 30 seconds (Paused)

# UNPAUSE: Resume frozen processes
docker unpause lifecycle-demo
docker ps --filter name=lifecycle-demo
# STATUS: Up 45 seconds

# STOP: Graceful shutdown (SIGTERM, then SIGKILL after 10s)
docker stop lifecycle-demo
docker ps -a --filter name=lifecycle-demo
# STATUS: Exited (0) 2 seconds ago

# RESTART: Stop + Start
docker restart lifecycle-demo
docker ps --filter name=lifecycle-demo
# STATUS: Up 1 second

# REMOVE: Delete the container
docker rm -f lifecycle-demo
docker ps -a --filter name=lifecycle-demo
# (no output — container is gone)
```

---

## 4.2 Container Management: ps, start, stop, and Naming

### docker ps vs docker ps -a

This is one of the first things that confuses beginners. `docker ps` only shows **running** containers. `docker ps -a` shows **all** containers (including stopped ones).

```bash
# First, create some containers to demonstrate
$ docker run -d --name web nginx
$ docker run --name quick centos echo "done"
$ docker run -d --name db postgres:16 -e POSTGRES_PASSWORD=secret

# docker ps — shows ONLY running containers
$ docker ps

CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS          PORTS     NAMES
a1b2c3d4e5f6   nginx        "/docker-entrypoint.…"   10 seconds ago   Up 9 seconds    80/tcp    web
c3d4e5f6a1b2   postgres:16  "docker-entrypoint.s…"   5 seconds ago    Up 4 seconds    5432/tcp  db

# Notice: "quick" container is NOT shown — it already exited

# docker ps -a — shows ALL containers (running + stopped)
$ docker ps -a

CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS                     PORTS     NAMES
a1b2c3d4e5f6   nginx        "/docker-entrypoint.…"   30 seconds ago   Up 29 seconds              80/tcp    web
b2c3d4e5f6a1   centos       "echo done"              20 seconds ago   Exited (0) 19 seconds ago            quick
c3d4e5f6a1b2   postgres:16  "docker-entrypoint.s…"   15 seconds ago   Up 14 seconds              5432/tcp  db

# Now "quick" appears with STATUS: Exited (0)
```

```
┌─────────────────────────────────────────────────────────────┐
│              docker ps vs docker ps -a                       │
│                                                              │
│  docker ps                                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Shows: Running containers ONLY                      │   │
│  │  Use when: Checking what's currently active          │   │
│  │  Missing: Stopped/exited containers                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  docker ps -a                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Shows: ALL containers (running + stopped + created) │   │
│  │  Use when: Finding old containers, debugging exits   │   │
│  │  Includes: Exit codes, creation times                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Common flags:                                              │
│  docker ps -q              → IDs only (for scripting)       │
│  docker ps -a --filter status=exited  → only exited ones   │
│  docker ps --format "table {{.Names}}\t{{.Status}}"        │
│                            → custom output format           │
└─────────────────────────────────────────────────────────────┘
```

### docker stop and docker start

```bash
# ─── STOPPING A CONTAINER ────────────────────────────────
$ docker stop web

# Output:
web

# What happens internally:
# 1. Docker sends SIGTERM to PID 1 (nginx master process)
# 2. Waits 10 seconds for graceful shutdown
# 3. If still running after 10s → sends SIGKILL (force kill)

# Verify it stopped
$ docker ps
CONTAINER ID   IMAGE        COMMAND                  STATUS         NAMES
c3d4e5f6a1b2   postgres:16  "docker-entrypoint.s…"   Up 2 minutes   db
# "web" is gone from running list

$ docker ps -a --filter name=web
CONTAINER ID   IMAGE   COMMAND                  STATUS                     NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   Exited (0) 5 seconds ago   web
# STATUS changed to "Exited (0)" — clean shutdown
```

```bash
# ─── STARTING A STOPPED CONTAINER ────────────────────────
$ docker start web

# Output:
web

# The SAME container restarts (not a new one!)
# All configuration (ports, volumes, env vars) is preserved

$ docker ps
CONTAINER ID   IMAGE        COMMAND                  STATUS         NAMES
a1b2c3d4e5f6   nginx        "/docker-entrypoint.…"   Up 3 seconds   web
c3d4e5f6a1b2   postgres:16  "docker-entrypoint.s…"   Up 3 minutes   db

# Same container ID (a1b2c3d4e5f6) — it's the same container, restarted
```

```
┌─────────────────────────────────────────────────────────────┐
│              docker start vs docker run                      │
│                                                              │
│  docker start <container>                                   │
│  • Restarts an EXISTING stopped container                   │
│  • Same container ID, same config                           │
│  • Data in writable layer is preserved                      │
│  • Does NOT create a new container                          │
│                                                              │
│  docker run <image>                                         │
│  • Creates a BRAND NEW container every time                 │
│  • New container ID, fresh writable layer                   │
│  • Previous container's data is NOT available               │
│  • Equivalent to: docker create + docker start              │
│                                                              │
│  Rule of thumb:                                             │
│  • Use docker start to resume work in an existing container │
│  • Use docker run to create a fresh environment             │
└─────────────────────────────────────────────────────────────┘
```

### Reusing a Container: start + attach Workflow

When you want to get back into a stopped interactive container, you need **two steps**: `docker start` then `docker attach`.

```bash
# Step 1: Create a named container, do some work, then exit
$ docker run --name test00 -it centos /bin/bash

[root@a1b2c3d4e5f6 /]# cd /tmp
[root@a1b2c3d4e5f6 tmp]# touch mywork.txt
[root@a1b2c3d4e5f6 tmp]# echo "important data" > mywork.txt
[root@a1b2c3d4e5f6 tmp]# exit

# Container is now stopped
$ docker ps -a --filter name=test00

CONTAINER ID   IMAGE    COMMAND       CREATED          STATUS                     NAMES
a1b2c3d4e5f6   centos   "/bin/bash"   1 minute ago     Exited (0) 5 seconds ago   test00
```

```bash
# Step 2: Start the stopped container
$ docker start test00

# Output:
test00

# Container is now running again (in background)
$ docker ps --filter name=test00

CONTAINER ID   IMAGE    COMMAND       CREATED          STATUS         NAMES
a1b2c3d4e5f6   centos   "/bin/bash"   2 minutes ago    Up 5 seconds   test00
```

```bash
# Step 3: Attach your terminal to the running container
$ docker attach test00

[root@a1b2c3d4e5f6 /]#

# You're back inside the SAME container!
# Verify your previous work is still there:
[root@a1b2c3d4e5f6 /]# cat /tmp/mywork.txt
important data

# Your data survived because it's the SAME container, not a new one
```

**Why can't `attach` start a stopped container?**

```
┌─────────────────────────────────────────────────────────────┐
│              WHY YOU NEED start BEFORE attach                │
│                                                              │
│  docker attach connects your terminal to an                 │
│  ALREADY-RUNNING container's PID 1 process.                 │
│                                                              │
│  If the container is stopped:                               │
│  • There is no running PID 1 process                        │
│  • There is nothing to attach to                            │
│  • attach will fail or hang                                 │
│                                                              │
│  Correct workflow:                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container stopped                                    │   │
│  │       │                                               │   │
│  │       ▼                                               │   │
│  │  docker start test00  ← restarts PID 1 (/bin/bash)   │   │
│  │       │                                               │   │
│  │       ▼                                               │   │
│  │  Container running (bash is alive but no terminal)    │   │
│  │       │                                               │   │
│  │       ▼                                               │   │
│  │  docker attach test00 ← connects your terminal       │   │
│  │       │                  to the running bash          │   │
│  │       ▼                                               │   │
│  │  [root@a1b2c3d4e5f6 /]#  ← you're back in!         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Wrong: docker attach test00 (while stopped) → ERROR       │
│  Right: docker start test00 && docker attach test00        │
└─────────────────────────────────────────────────────────────┘
```

### Container Naming (--name)

By default, Docker generates random names like `quirky_einstein` or `happy_morse`. Use `--name` to give containers meaningful names.

```bash
# Without --name: Docker generates a random name
$ docker run -d nginx
a1b2c3d4e5f6...

$ docker ps --format "table {{.ID}}\t{{.Names}}"
CONTAINER ID   NAMES
a1b2c3d4e5f6   quirky_einstein    ← Random name!

# With --name: You choose the name
$ docker run -d --name webserver nginx
b2c3d4e5f6a1...

$ docker ps --format "table {{.ID}}\t{{.Names}}"
CONTAINER ID   NAMES
b2c3d4e5f6a1   webserver          ← Your chosen name
a1b2c3d4e5f6   quirky_einstein
```

**Using names instead of IDs:**

```bash
# All these commands work with EITHER name or ID:

# Using container ID (hard to remember)
$ docker stop a1b2c3d4e5f6
$ docker start a1b2c3d4e5f6
$ docker logs a1b2c3d4e5f6
$ docker exec -it a1b2c3d4e5f6 bash

# Using container name (easy to remember)
$ docker stop webserver
$ docker start webserver
$ docker logs webserver
$ docker exec -it webserver bash

# Names are much easier in scripts and daily work
```

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER ID vs CONTAINER NAME                  │
│                                                              │
│  Container ID:                                              │
│  • Generated automatically (e.g., a1b2c3d4e5f6)            │
│  • Cannot be changed                                       │
│  • Always unique                                            │
│  • Full ID is 64 chars; short form is 12 chars              │
│                                                              │
│  Container Name:                                            │
│  • User-defined with --name (e.g., webserver)               │
│  • Random if not specified (e.g., quirky_einstein)          │
│  • Must be unique (can't have two with same name)           │
│  • Can be changed: docker rename old-name new-name          │
│                                                              │
│  Best practice:                                             │
│  Always use --name for containers you'll manage manually.   │
│  It makes docker stop, start, logs, exec much easier.       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Name collision — you can't reuse a name
$ docker run -d --name web nginx
$ docker run -d --name web nginx

# Error:
docker: Error response from daemon: Conflict. The container name "/web" is already
in use by container "a1b2c3d4e5f6". You have to remove (or rename) that container
to be able to reuse that name.

# Fix: Remove the old container first
$ docker rm -f web
$ docker run -d --name web nginx
# Now it works

# Or rename the existing container
$ docker rename web web-old
$ docker run -d --name web nginx
```

```bash
# Clean up all demo containers
$ docker rm -f web db quick webserver quirky_einstein 2>/dev/null
```

---

## 4.3 docker run — The Complete Reference

`docker run` is actually `docker create` + `docker start` combined. It is the most important command in container management.

### What Happens Internally When You Run `docker run`

```
┌─────────────────────────────────────────────────────────────┐
│              docker run ubuntu                               │
│                    │                                         │
│                    ▼                                         │
│  Step 1: Check if image exists locally                      │
│          docker images | grep ubuntu                        │
│                    │                                         │
│          ┌────────┴────────┐                                │
│          │                 │                                 │
│     Found locally    Not found locally                      │
│          │                 │                                 │
│          │                 ▼                                 │
│          │    Step 2: Pull from registry                    │
│          │    (Docker Hub by default)                       │
│          │    "Unable to find image 'ubuntu:latest'         │
│          │     locally"                                     │
│          │    "Pulling from library/ubuntu"                 │
│          │                 │                                 │
│          └────────┬────────┘                                │
│                   │                                         │
│                   ▼                                         │
│  Step 3: Create container                                   │
│          • Allocate container ID                            │
│          • Set up namespaces (PID, NET, MNT, UTS, IPC)     │
│          • Create writable filesystem layer                 │
│          • Configure networking (bridge, IP assignment)     │
│                   │                                         │
│                   ▼                                         │
│  Step 4: Start container                                    │
│          • Start the main process                           │
│                   │                                         │
│                   ▼                                         │
│  Step 5: Execute default CMD (from image metadata)          │
│          • If no command specified → run image's CMD        │
│          • If command specified → run that instead          │
│                   │                                         │
│                   ▼                                         │
│  Step 6: Attach (if -it flags used)                         │
│          • Connect your terminal to container's STDIN/OUT   │
│          • You see the shell prompt                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Example — watching each step happen:**

```bash
# Run ubuntu interactively — observe the output carefully
$ docker run -it ubuntu

# Step 1-2: Image pull (only happens first time)
Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
bccd10f490ab: Pull complete
Digest: sha256:77906da86b60585ce12215807090eb327e7386c8fafb5402369e421f44eff17e
Status: Downloaded newer image for ubuntu:latest

# Step 3-6: Container created, started, CMD executed, terminal attached
root@a1b2c3d4e5f6:/#

# You are now inside the container!
# "a1b2c3d4e5f6" is the container ID
# "root" is the user (default in most images)
```

### Image Pulling Logic

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE PULL DECISION TREE                        │
│                                                              │
│  docker run <image>:<tag>                                   │
│       │                                                      │
│       ▼                                                      │
│  Is image:tag in local cache?                               │
│       │                                                      │
│  ┌────┴────┐                                                │
│  │         │                                                 │
│  YES       NO                                                │
│  │         │                                                 │
│  │         ▼                                                 │
│  │    Pull from registry                                    │
│  │    (Docker Hub default)                                  │
│  │         │                                                 │
│  │    ┌────┴────┐                                           │
│  │    │         │                                            │
│  │  Found    Not found                                      │
│  │    │         │                                            │
│  │    │         ▼                                            │
│  │    │    Error: "manifest unknown"                        │
│  │    │    or "repository not found"                        │
│  │    │                                                      │
│  │    ▼                                                      │
│  │  Download layers                                         │
│  │  (only layers not already cached)                        │
│  │    │                                                      │
│  └────┴────▶ Use image to create container                  │
│                                                              │
│  Key point: Docker only downloads layers it doesn't have.   │
│  If you already have ubuntu:22.04 and pull ubuntu:24.04,    │
│  shared layers are reused from cache.                       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# First pull — downloads all layers
$ docker pull nginx:latest
latest: Pulling from library/nginx
a2abf6c4d29d: Pull complete      # ← Downloaded
a9edb18cadd1: Pull complete      # ← Downloaded
589b7251471a: Pull complete      # ← Downloaded
Status: Downloaded newer image for nginx:latest

# Second pull of same image — nothing to download
$ docker pull nginx:latest
latest: Pulling from library/nginx
Digest: sha256:0d17b565c37bcbd895e9d92315a05c1c3c9a29f762b011a10c54a66cd53c9b31
Status: Image is up to date for nginx:latest

# Pull a different tag — some layers may be shared
$ docker pull nginx:1.25
1.25: Pulling from library/nginx
a2abf6c4d29d: Already exists     # ← Reused from cache!
a9edb18cadd1: Already exists     # ← Reused from cache!
7b396e1a5c40: Pull complete      # ← Only new layer downloaded
Status: Downloaded newer image for nginx:1.25
```

### Syntax

```bash
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

### All Important Options Explained

```bash
# ─── BASIC OPTIONS ───────────────────────────────────────

# -d, --detach: Run in background
docker run -d nginx
# Returns container ID, gives you back the terminal

# -it: Interactive + TTY (for shell access)
docker run -it ubuntu bash
# Opens a bash shell inside the container
# -i = Keep STDIN open
# -t = Allocate a pseudo-terminal

# --name: Assign a name
docker run -d --name webserver nginx
# Without --name, Docker generates random names like "quirky_einstein"

# --rm: Auto-remove container when it exits
docker run --rm ubuntu echo "Hello"
# Container is deleted after "Hello" is printed
# Useful for one-off commands, prevents container accumulation

# ─── PORT MAPPING ────────────────────────────────────────

# -p HOST:CONTAINER: Map specific port
docker run -d -p 8080:80 nginx
# Host port 8080 → Container port 80

# -p HOST_IP:HOST_PORT:CONTAINER_PORT: Bind to specific interface
docker run -d -p 127.0.0.1:8080:80 nginx
# Only accessible from localhost, not from network

# -p CONTAINER_PORT: Map to random host port
docker run -d -p 80 nginx
docker port <container_id>
# Output: 80/tcp -> 0.0.0.0:32768
# Docker chose port 32768 on the host

# -P: Map ALL exposed ports to random host ports
docker run -d -P nginx
docker port <container_id>
# Output: 80/tcp -> 0.0.0.0:32769

# Multiple port mappings
docker run -d -p 8080:80 -p 8443:443 nginx

# ─── ENVIRONMENT VARIABLES ───────────────────────────────

# -e: Set environment variable
docker run -d -e MYSQL_ROOT_PASSWORD=secret mysql:8

# Multiple variables
docker run -d \
  -e DB_HOST=localhost \
  -e DB_PORT=5432 \
  -e DB_NAME=myapp \
  postgres:16

# From a file
# Create env file:
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=myapp
docker run -d --env-file .env postgres:16

# ─── VOLUME MOUNTS ──────────────────────────────────────

# -v: Named volume (Docker manages storage location)
docker run -d -v mydata:/var/lib/mysql mysql:8
# Data persists even if container is removed

# -v: Bind mount (map host directory to container)
docker run -d -v $(pwd)/html:/usr/share/nginx/html nginx
# Changes on host immediately reflected in container

# -v: Read-only mount
docker run -d -v $(pwd)/config:/etc/nginx/conf.d:ro nginx
# Container cannot modify files in this mount

# --tmpfs: In-memory filesystem
docker run -d --tmpfs /tmp:rw,size=100m nginx
# /tmp is stored in RAM, not on disk. Fast but not persistent.

# ─── RESOURCE LIMITS ────────────────────────────────────

# --memory: Limit RAM
docker run -d --memory=512m nginx
# Container is killed (OOMKilled) if it exceeds 512MB

# --cpus: Limit CPU
docker run -d --cpus=1.5 nginx
# Container can use at most 1.5 CPU cores

# --cpu-shares: Relative CPU weight (default: 1024)
docker run -d --cpu-shares=512 nginx
# Gets half the CPU time compared to default containers

# --pids-limit: Limit number of processes
docker run -d --pids-limit=100 nginx
# Prevents fork bombs

# Combined resource limits (production example)
docker run -d \
  --memory=256m \
  --memory-swap=512m \
  --cpus=0.5 \
  --pids-limit=50 \
  --name limited-app \
  my-app:1.0

# ─── NETWORKING ──────────────────────────────────────────

# --network: Connect to a specific network
docker run -d --network my-network nginx

# --hostname: Set container hostname
docker run -d --hostname api-server nginx

# --dns: Custom DNS server
docker run -d --dns 8.8.8.8 nginx

# --add-host: Add host-to-IP mapping (like /etc/hosts)
docker run -d --add-host mydb:192.168.1.100 nginx

# ─── RESTART POLICIES ───────────────────────────────────

# --restart: Define when container should restart
docker run -d --restart=no nginx           # Never restart (default)
docker run -d --restart=always nginx       # Always restart (even after reboot)
docker run -d --restart=unless-stopped nginx # Like always, but not if manually stopped
docker run -d --restart=on-failure:5 nginx  # Restart on failure, max 5 attempts

# Production example: Always restart the database
docker run -d \
  --restart=unless-stopped \
  --name production-db \
  -v db-data:/var/lib/postgresql/data \
  postgres:16

# ─── SECURITY ────────────────────────────────────────────

# --user: Run as specific user (not root)
docker run -d --user 1000:1000 nginx

# --read-only: Read-only filesystem
docker run -d --read-only --tmpfs /tmp nginx
# Container cannot write to filesystem except /tmp

# --cap-drop: Remove Linux capabilities
docker run -d --cap-drop ALL --cap-add NET_BIND_SERVICE nginx
# Drop all capabilities, add back only what's needed

# --security-opt: Security options
docker run -d --security-opt no-new-privileges nginx
# Prevents privilege escalation inside container

# ─── LOGGING ─────────────────────────────────────────────

# --log-driver: Set logging driver
docker run -d --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 nginx
# Rotate logs: max 10MB per file, keep 3 files

# --log-driver none: Disable logging
docker run -d --log-driver none nginx
```

---

## 4.4 Understanding Default CMD vs Custom CMD

When you run `docker run -it centos`, you get a bash shell. But why? Because the image has a **default CMD** defined in its metadata. Understanding this is one of the most important Docker concepts.

### What's Inside a Docker Image (Metadata View)

Every Docker image contains not just files, but also metadata that tells Docker how to run it:

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER IMAGE (centos)                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Filesystem Layers                                    │   │
│  │  ├── OS files (/bin, /usr, /lib, /etc)               │   │
│  │  ├── Libraries (glibc, openssl, etc.)                │   │
│  │  └── Applications (bash, coreutils, etc.)            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Metadata (stored in image config)                    │   │
│  │  ├── Default Command (CMD): /bin/bash                │   │
│  │  ├── Working Directory: /                            │   │
│  │  ├── User: root                                      │   │
│  │  ├── Environment Variables: PATH=...                 │   │
│  │  └── Exposed Ports: (none for centos)                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  When container starts:                                     │
│  Container starts → Runs /bin/bash automatically            │
│  → You get an interactive shell                             │
└─────────────────────────────────────────────────────────────┘
```

### How Default CMD Works

```
┌─────────────────────────────────────────────────────────────┐
│              DEFAULT CMD BEHAVIOR                            │
│                                                              │
│  docker run -it centos                                      │
│       │                                                      │
│       ▼                                                      │
│  Did user specify a command?                                │
│       │                                                      │
│  ┌────┴────┐                                                │
│  │         │                                                 │
│  NO        YES                                               │
│  │         │                                                 │
│  ▼         ▼                                                 │
│  Run the   Run the user's                                   │
│  image's   command instead                                  │
│  default                                                    │
│  CMD                                                        │
│                                                              │
│  centos default CMD: /bin/bash                              │
│  nginx default CMD: nginx -g 'daemon off;'                  │
│  python default CMD: python3                                │
│  alpine default CMD: /bin/sh                                │
└─────────────────────────────────────────────────────────────┘
```

**Inspecting an image's default CMD:**

```bash
# See what command an image runs by default
$ docker inspect centos --format='{{json .Config.Cmd}}'
["/bin/bash"]

$ docker inspect nginx --format='{{json .Config.Cmd}}'
["nginx","-g","daemon off;"]

$ docker inspect python:3.12-slim --format='{{json .Config.Cmd}}'
["python3"]

$ docker inspect alpine --format='{{json .Config.Cmd}}'
["/bin/sh"]

# This is why:
# docker run -it centos     → gives you bash
# docker run -d nginx       → starts nginx server
# docker run -it python     → gives you Python REPL
# docker run -it alpine     → gives you sh (not bash — alpine doesn't have bash)
```

### Overriding the Default CMD (Custom Commands)

You can replace the default command by specifying your own after the image name:

```bash
# Default: runs /bin/bash (the image's CMD)
$ docker run -it centos
[root@a1b2c3d4e5f6 /]#
# bash is running → container stays alive → you can type commands

# Override: run 'echo Hello' instead of bash
$ docker run centos echo Hello

# Output:
Hello

# What happened internally:
# docker run centos echo Hello
#      ↓
# Create container
#      ↓
# Run "echo Hello" as PID 1 (instead of /bin/bash)
#      ↓
# "echo Hello" prints "Hello"
#      ↓
# echo completes → PID 1 exits → container stops
```

**More custom command examples with explanations:**

```bash
# ─── Example 1: ls (list files) ─────────────────────────
$ docker run centos ls

# Output:
bin
boot
dev
etc
home
lib
lib64
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var

# Container ran 'ls', printed directory listing, then STOPPED.
# Why? Because 'ls' finished — PID 1 exited.

# ─── Example 2: cat a file ──────────────────────────────
$ docker run centos cat /etc/os-release

# Output:
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="7"
PRETTY_NAME="CentOS Linux 7 (Core)"

# Container ran 'cat', printed file contents, then STOPPED.

# ─── Example 3: sleep (runs for a duration) ─────────────
$ docker run centos sleep 10

# Container runs for exactly 10 seconds, then exits.
# During those 10 seconds, 'docker ps' would show it as running.

# ─── Example 4: echo with arguments ─────────────────────
$ docker run centos echo "Hello from container"
Hello from container

# Container printed the message and STOPPED immediately.

# ─── Example 5: interactive shell (stays alive) ─────────
$ docker run -it centos bash
[root@a1b2c3d4e5f6 /]#

# Container is RUNNING because bash is waiting for input.
# Type 'exit' to stop bash → container stops.
```

### Why Container Stops Automatically (The PID 1 Rule)

This is one of the **most important Docker concepts** and a frequent interview question.

```
┌─────────────────────────────────────────────────────────────┐
│              THE PID 1 RULE                                  │
│                                                              │
│  Container runs ONLY while its main process (PID 1) runs.  │
│  When PID 1 exits → container stops. Always.               │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  Case 1: echo command (short-lived)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container                                            │   │
│  │  └── PID 1 → echo Hello → FINISHED → container STOPS│   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Case 2: bash (interactive, long-lived)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container                                            │   │
│  │  └── PID 1 → /bin/bash → RUNNING → container ALIVE  │   │
│  │       ├── waiting for input...                        │   │
│  │       ├── user types commands...                      │   │
│  │       └── user types 'exit' → bash STOPS             │   │
│  │           → container STOPS                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Case 3: nginx (daemon, long-lived)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container                                            │   │
│  │  └── PID 1 → nginx → RUNNING → container ALIVE      │   │
│  │       ├── serving HTTP requests...                    │   │
│  │       ├── keeps running indefinitely...               │   │
│  │       └── until 'docker stop' sends SIGTERM           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Interactive Shell (bash) Keeps Container Alive

```
┌─────────────────────────────────────────────────────────────┐
│              WHY BASH KEEPS CONTAINER RUNNING                │
│                                                              │
│  bash is a LONG-RUNNING process:                            │
│                                                              │
│  Container                                                  │
│  └── /bin/bash (PID 1)                                     │
│       │                                                      │
│       ├── 1. Displays prompt: [root@abc123 /]#             │
│       ├── 2. Waits for user input...                        │
│       ├── 3. User types: ls                                 │
│       ├── 4. Executes ls, shows output                      │
│       ├── 5. Displays prompt again                          │
│       ├── 6. Waits for user input...                        │
│       ├── 7. User types: exit                               │
│       └── 8. bash exits → PID 1 gone → container STOPS    │
│                                                              │
│  bash runs in a READ-EVAL-PRINT LOOP:                      │
│  Read input → Evaluate command → Print output → Loop       │
│  This loop keeps bash alive → keeps container alive         │
│                                                              │
│  Compare with 'echo Hello':                                 │
│  Print "Hello" → Done → No loop → Process exits            │
│  → Container stops                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating the difference:**

```bash
# bash keeps container alive (interactive loop)
$ docker run -it --name alive-demo centos bash
[root@abc123 /]# echo "I'm alive"
I'm alive
[root@abc123 /]# ps -ef
UID   PID  PPID  C STIME TTY      TIME CMD
root    1     0  0 10:00 pts/0    00:00:00 bash    ← PID 1 is bash, still running
root   15     1  0 10:01 pts/0    00:00:00 ps -ef
[root@abc123 /]# exit
# bash exits → container stops

# echo does NOT keep container alive (one-shot command)
$ docker run --name dead-demo centos echo "I'm done"
I'm done
# Container already stopped

# Verify both containers
$ docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Command}}"
NAMES       STATUS                     COMMAND
dead-demo   Exited (0) 2 seconds ago   "echo 'I'm done'"
alive-demo  Exited (0) 30 seconds ago  "bash"

# Clean up
$ docker rm alive-demo dead-demo
```

---

## 4.5 Container Process Model (PID 1)

Inside a container, the main process is always **PID 1**. This is a fundamental concept.

### Viewing Processes Inside a Container

```bash
# Start a container and check its processes
$ docker run -d --name proctest nginx
$ docker exec proctest ps -ef

# Output:
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 10:00 ?        00:00:00 nginx: master process nginx -g daemon off;
nginx       29     1  0 10:00 ?        00:00:00 nginx: worker process
nginx       30     1  0 10:00 ?        00:00:00 nginx: worker process

# Key observations:
# • PID 1 is the nginx master process (the main process)
# • Worker processes are children of PID 1
# • There are very FEW processes (compare to a VM with 100+ OS processes)
# • No init, no systemd, no cron, no sshd — just nginx
```

```bash
# Compare: processes on the HOST machine
$ ps -ef | wc -l
187    # Hundreds of processes on a typical host

# Processes inside the container
$ docker exec proctest ps -ef | wc -l
4      # Only 3-4 processes!

# This is why containers are lightweight
```

### Why PID 1 Matters

```
┌─────────────────────────────────────────────────────────────┐
│              PID 1 IN CONTAINERS                             │
│                                                              │
│  In Linux, PID 1 is special:                                │
│  • It's the first process started                           │
│  • It's responsible for reaping zombie processes            │
│  • If PID 1 exits → the container stops                    │
│  • Signals (SIGTERM, SIGKILL) are sent to PID 1            │
│                                                              │
│  When you run 'docker stop':                                │
│  1. Docker sends SIGTERM to PID 1                           │
│  2. Waits 10 seconds for graceful shutdown                  │
│  3. If still running → sends SIGKILL                       │
│                                                              │
│  This is why your app should handle SIGTERM properly!       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# See PID 1 specifically
$ docker exec proctest cat /proc/1/cmdline | tr '\0' ' '
nginx: master process nginx -g daemon off;

# The top command inside a container
$ docker top proctest

UID    PID     PPID    C   STIME   TTY   TIME       CMD
root   12345   12300   0   10:00   ?     00:00:00   nginx: master process nginx -g daemon off;
33     12380   12345   0   10:00   ?     00:00:00   nginx: worker process
33     12381   12345   0   10:00   ?     00:00:00   nginx: worker process

# Note: The PIDs shown here are the HOST PIDs
# Inside the container, the master process thinks it's PID 1
# On the host, it's PID 12345 — this is namespace magic

# Clean up
$ docker rm -f proctest
```

### Interactive vs Detached Mode — When to Use Which

```
┌──────────────────────────────────────────────────────────────┐
│  Mode              │ Flag  │ When to Use                     │
├────────────────────┼───────┼─────────────────────────────────┤
│  Interactive       │ -it   │ • Debugging / troubleshooting   │
│                    │       │ • Running a shell inside         │
│                    │       │ • One-off commands               │
│                    │       │ • Learning / experimenting       │
│                    │       │ • Python/Node REPL               │
├────────────────────┼───────┼─────────────────────────────────┤
│  Detached          │ -d    │ • Web servers (nginx, apache)   │
│                    │       │ • Databases (postgres, mysql)    │
│                    │       │ • API servers                    │
│                    │       │ • Background services            │
│                    │       │ • Production workloads           │
├────────────────────┼───────┼─────────────────────────────────┤
│  Foreground        │ (none)│ • Quick tests                   │
│  (no -d, no -it)   │       │ • See output directly           │
│                    │       │ • docker run ubuntu echo "hi"   │
└────────────────────┴───────┴─────────────────────────────────┘
```

```bash
# Interactive mode — you get a shell, container stops when you exit
$ docker run -it ubuntu bash
root@abc123:/# echo "I'm inside"
I'm inside
root@abc123:/# exit
# Container stops

# Detached mode — runs in background, you get your terminal back
$ docker run -d --name bg-nginx nginx
7a8b9c0d1e2f...
# Container is running in background

# Check it's running
$ docker ps
CONTAINER ID   IMAGE   STATUS         NAMES
7a8b9c0d1e2f   nginx   Up 5 seconds   bg-nginx

# View its output
$ docker logs bg-nginx

# Foreground mode — output goes to your terminal, Ctrl+C stops it
$ docker run nginx
# You see nginx logs directly
# Press Ctrl+C to stop
```

### Detached Mode with Long-Running Scripts

In detached mode (`-d`), the container runs in the background. But the command must be **long-running** — if it finishes, the container stops.

```bash
# ─── BAD: Short command in detached mode ─────────────────
$ docker run -d --name bad-detach centos echo "Hello"

$ docker ps --filter name=bad-detach
# (empty — container already exited because echo finished)

$ docker ps -a --filter name=bad-detach
CONTAINER ID   IMAGE    COMMAND        STATUS                     NAMES
x1y2z3a4b5c6   centos   "echo Hello"   Exited (0) 2 seconds ago   bad-detach

# echo finished instantly → PID 1 exited → container stopped
```

```bash
# ─── GOOD: Long-running command in detached mode ─────────
# Simulate an application with an infinite loop
$ docker run -d --name test01 centos \
    /bin/sh -c 'while true; do echo "Hello_Adam"; sleep 8; done'

# Output:
112233aabbcc...

# Check it's running
$ docker ps --filter name=test01

CONTAINER ID   IMAGE    COMMAND                  STATUS         NAMES
112233aabbcc   centos   "/bin/sh -c 'while t…"   Up 10 seconds  test01

# The while loop runs forever → PID 1 never exits → container stays alive
```

```
┌─────────────────────────────────────────────────────────────┐
│              WHY LONG-RUNNING COMMANDS MATTER IN -d MODE    │
│                                                              │
│  -d means: "run in background, don't attach my terminal"   │
│                                                              │
│  But the PID 1 rule still applies:                          │
│  • If PID 1 finishes → container stops (even in -d mode)   │
│  • So detached containers usually run:                      │
│    - Servers (nginx, apache, mysql, postgres)               │
│    - Daemons (background services)                          │
│    - Infinite loops / long-running scripts                  │
│    - Applications that listen on a port                     │
│                                                              │
│  Common mistake:                                            │
│  docker run -d centos echo "hi"  ← stops immediately       │
│  docker run -d centos sleep 3600 ← runs for 1 hour         │
│  docker run -d nginx             ← runs until stopped      │
└─────────────────────────────────────────────────────────────┘
```

### Viewing Logs of Detached Containers (docker logs)

In detached mode, you can't see the container's output directly. Use `docker logs` to view what the application printed to STDOUT/STDERR.

```bash
# View all logs (non-live, snapshot)
$ docker logs test01

# Output:
Hello_Adam
Hello_Adam
Hello_Adam
Hello_Adam

# Each line was printed by the while loop every 8 seconds
```

```bash
# Follow logs in real-time (like tail -f)
$ docker logs -f test01

Hello_Adam
Hello_Adam
Hello_Adam
Hello_Adam    ← new lines appear every 8 seconds
Hello_Adam
^C            ← Press Ctrl+C to stop following (container keeps running)
```

```bash
# Show only the last N lines
$ docker logs --tail 3 test01

Hello_Adam
Hello_Adam
Hello_Adam

# Show logs since a specific time
$ docker logs --since 1m test01    # Last 1 minute
$ docker logs --since 2h test01    # Last 2 hours

# Show timestamps with each log line
$ docker logs -t test01

2024-01-15T10:30:00.123456789Z Hello_Adam
2024-01-15T10:30:08.234567890Z Hello_Adam
2024-01-15T10:30:16.345678901Z Hello_Adam
```

```
┌─────────────────────────────────────────────────────────────┐
│              IMPORTANT: What docker logs Shows               │
│                                                              │
│  docker logs shows ONLY what the app prints to:             │
│  • STDOUT (standard output — echo, print, console.log)     │
│  • STDERR (standard error — error messages, warnings)       │
│                                                              │
│  It does NOT show:                                          │
│  • Files written inside the container                       │
│    (e.g., /var/log/app.log)                                 │
│  • System logs                                              │
│                                                              │
│  If your app writes to a log FILE instead of STDOUT:        │
│  $ docker exec test01 cat /var/log/app.log                  │
│  (use exec to read the file directly)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.6 Executing Commands in Running Containers

```bash
# Run a command in a running container
docker exec my-container ls /app

# Output:
# app.js
# node_modules
# package.json

# MEANING: Runs "ls /app" inside the container and shows output.
# The container's main process is NOT affected.
```

```bash
# Open an interactive shell
docker exec -it my-container bash

# If bash isn't available (Alpine images):
docker exec -it my-container sh

# Run as a specific user
docker exec -u root my-container whoami
# Output: root

# Set environment variables for the exec session
docker exec -e DEBUG=true my-container node debug-script.js

# Run in a specific working directory
docker exec -w /app/src my-container ls
```

### docker exec -it: The Safe Way to Get a Shell

When you have a detached container running an application, use `docker exec -it` to get a shell **without affecting the main process**:

```bash
# Container test01 is running our while-loop script as PID 1
$ docker exec -it test01 /bin/bash

[root@112233aabbcc /]#

# You're inside the container with a NEW shell process
# The original while-loop (PID 1) is still running

# Verify: check all processes
[root@112233aabbcc /]# ps -ef

UID   PID  PPID  C STIME TTY      TIME CMD
root    1     0  0 10:00 ?        00:00:00 /bin/sh -c while true; do echo Hello_Adam; sleep 8; done
root   85     1  0 10:05 ?        00:00:00 sleep 8
root   86     0  0 10:05 pts/0    00:00:00 /bin/bash    ← This is YOUR shell (from exec)
root   90    86  0 10:05 pts/0    00:00:00 ps -ef

# PID 1 = the while loop (keeps container alive)
# PID 86 = your bash shell (from docker exec)

# Exit your shell — container KEEPS RUNNING
[root@112233aabbcc /]# exit

$ docker ps --filter name=test01
CONTAINER ID   IMAGE    STATUS         NAMES
112233aabbcc   centos   Up 10 minutes  test01    ← Still running!
```

### docker exec vs docker attach — The Critical Difference

```
┌─────────────────────────────────────────────────────────────┐
│              exec vs attach                                  │
│                                                              │
│  docker exec -it test01 bash                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container test01                                     │   │
│  │  ├── PID 1: while loop (app) ← keeps running        │   │
│  │  └── PID 86: /bin/bash ← NEW process (your shell)   │   │
│  │                                                       │   │
│  │  You exit bash → PID 86 ends → PID 1 still runs     │   │
│  │  → Container stays alive ✅                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  docker attach test01                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container test01                                     │   │
│  │  └── PID 1: while loop (app) ← you attach to THIS   │   │
│  │                                                       │   │
│  │  You press Ctrl+C → PID 1 gets SIGINT → PID 1 stops │   │
│  │  → Container stops ❌                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  exec = creates a NEW process (safe)                        │
│  attach = connects to PID 1 (risky)                         │
│                                                              │
│  In production, ALWAYS use exec.                            │
│  attach is only safe for containers where PID 1 is bash     │
│  and you intentionally want to interact with it.            │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating the risk of attach:**

```bash
# Start a detached container with a long-running process
$ docker run -d --name attach-risk centos \
    /bin/sh -c 'while true; do echo "working..."; sleep 5; done'

# Attach to it — you see the output of PID 1
$ docker attach attach-risk
working...
working...
working...
^C                    ← You press Ctrl+C

# What happened? Ctrl+C sent SIGINT to PID 1
# PID 1 (the while loop) stopped → container stopped

$ docker ps --filter name=attach-risk
# (empty — container is gone!)

$ docker ps -a --filter name=attach-risk
CONTAINER ID   IMAGE    STATUS                     NAMES
d4e5f6a1b2c3   centos   Exited (130) 2 seconds ago attach-risk

# Exit code 130 = killed by SIGINT (Ctrl+C)
# You accidentally killed the container!

# Clean up
$ docker rm attach-risk
```

**The safe alternative:**

```bash
# Same container, but use exec instead
$ docker run -d --name exec-safe centos \
    /bin/sh -c 'while true; do echo "working..."; sleep 5; done'

$ docker exec -it exec-safe /bin/bash
[root@e5f6a1b2c3d4 /]# echo "I can work here safely"
I can work here safely
[root@e5f6a1b2c3d4 /]# exit

# Container is STILL running
$ docker ps --filter name=exec-safe
CONTAINER ID   IMAGE    STATUS         NAMES
e5f6a1b2c3d4   centos   Up 30 seconds  exec-safe    ← Still alive!

# Clean up
$ docker rm -f exec-safe
```

### Real-World exec Examples

```bash
# Check database connectivity from app container
docker exec my-app-container ping -c 3 database-container

# Run database migrations
docker exec my-app-container npx prisma migrate deploy

# Check environment variables
docker exec my-app-container env

# View a config file
docker exec my-app-container cat /etc/nginx/nginx.conf

# Install a debugging tool temporarily
docker exec my-app-container apt-get update && apt-get install -y curl
docker exec my-app-container curl http://localhost:3000/health

# Run a one-off database query
docker exec -it my-postgres psql -U postgres -d mydb -c "SELECT count(*) FROM users;"
```

---

## 4.7 Can You SSH or RDP into a Container?

### The Short Answer

Technically **yes**, but operationally **discouraged**. This is an important distinction for interviews and real-world practice.

```
┌─────────────────────────────────────────────────────────────┐
│              SSH/RDP INTO CONTAINERS — THE RULE              │
│                                                              │
│  ✅ Technically possible (you CAN install sshd)             │
│  ❌ Operationally discouraged (you SHOULDN'T)               │
│                                                              │
│  Containers are meant to run ONE main process and be        │
│  managed using:                                              │
│                                                              │
│  • docker exec    → temporary shell access                  │
│  • docker logs    → view application output                 │
│  • Observability  → metrics, traces, dashboards             │
│  • Image rebuild  → change config via Dockerfile, redeploy  │
│                                                              │
│  NOT by SSH-ing in and making manual changes.               │
└─────────────────────────────────────────────────────────────┘
```

### Why SSH/RDP is Not Recommended

```
┌─────────────────────────────────────────────────────────────┐
│  Reason                    │ Explanation                     │
├────────────────────────────┼─────────────────────────────────┤
│  Containers ≠ VMs          │ No init system (systemd),       │
│                            │ no sshd by default, not         │
│                            │ designed as full servers         │
├────────────────────────────┼─────────────────────────────────┤
│  Increased image size      │ Installing openssh-server adds  │
│                            │ ~30-50MB to your image          │
├────────────────────────────┼─────────────────────────────────┤
│  Extra attack surface      │ SSH port = another entry point  │
│                            │ for attackers                   │
├────────────────────────────┼─────────────────────────────────┤
│  Credential management     │ SSH keys/passwords inside       │
│                            │ containers = security risk      │
├────────────────────────────┼─────────────────────────────────┤
│  Configuration drift       │ "Someone changed something      │
│                            │ inside the container manually"  │
│                            │ → not reproducible              │
├────────────────────────────┼─────────────────────────────────┤
│  Breaks immutability       │ Containers should be disposable │
│                            │ — rebuild, don't patch in place │
└────────────────────────────┴─────────────────────────────────┘
```

### Better Alternatives to SSH

```bash
# ─── FOR TROUBLESHOOTING ─────────────────────────────────
# Open a shell inside a running container
$ docker exec -it mycontainer sh

# Or with bash if available
$ docker exec -it mycontainer bash

# Run a specific command without entering the container
$ docker exec mycontainer cat /etc/nginx/nginx.conf
$ docker exec mycontainer env
$ docker exec mycontainer ps aux

# ─── FOR VIEWING LOGS ────────────────────────────────────
$ docker logs mycontainer
$ docker logs -f mycontainer          # Follow in real-time
$ docker logs --tail 50 mycontainer   # Last 50 lines

# ─── FOR ADMIN-STYLE CHANGES ─────────────────────────────
# DON'T: SSH in and edit config files manually
# DO: Update the Dockerfile, rebuild, and redeploy
$ docker build -t myapp:v2 .
$ docker stop mycontainer
$ docker run -d --name mycontainer myapp:v2
```

### Demo: SSH into a Container (Teaching Example Only)

This demonstrates that SSH is technically possible. **Do not use this pattern in production.**

**Step 1: Run a container and install SSH server:**

```bash
# Start an Ubuntu container that stays running
$ docker run -d --name sshbox -p 2222:22 ubuntu:22.04 sleep infinity

# Output:
f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2

# Enter the container and install SSH
$ docker exec -it sshbox bash

root@f1a2b3c4d5e6:/# apt update
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [119 kB]
...
Reading package lists... Done

root@f1a2b3c4d5e6:/# apt install -y openssh-server
Reading package lists... Done
Building dependency tree... Done
...
Setting up openssh-server (1:8.9p1-3ubuntu0.6) ...

# Create the SSH run directory
root@f1a2b3c4d5e6:/# mkdir -p /var/run/sshd

# Set a root password (demo only — never do this in production)
root@f1a2b3c4d5e6:/# passwd root
New password: ********
Retype new password: ********
passwd: password updated successfully

# Allow root login via SSH (demo only)
root@f1a2b3c4d5e6:/# sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Start the SSH server
root@f1a2b3c4d5e6:/# /usr/sbin/sshd

# Exit the container
root@f1a2b3c4d5e6:/# exit
```

**Step 2: SSH into the container from the host:**

```bash
$ ssh root@localhost -p 2222

# Output:
The authenticity of host '[localhost]:2222 ([127.0.0.1]:2222)' can't be established.
ED25519 key fingerprint is SHA256:xYz123AbC456dEf789...
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '[localhost]:2222' (ED25519) to the list of known hosts.
root@localhost's password: ********

Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

root@f1a2b3c4d5e6:~# whoami
root

root@f1a2b3c4d5e6:~# hostname
f1a2b3c4d5e6

root@f1a2b3c4d5e6:~# exit
logout
Connection to localhost closed.
```

**Clean up:**

```bash
$ docker stop sshbox && docker rm sshbox
sshbox
sshbox
```

### RDP into a Container?

```
┌─────────────────────────────────────────────────────────────┐
│                    RDP AND CONTAINERS                         │
│                                                              │
│  RDP = Windows Remote Desktop Protocol (GUI-based)          │
│                                                              │
│  Containers are usually:                                    │
│  • Headless (no GUI / no display server)                    │
│  • Linux-based (RDP is a Windows protocol)                  │
│  • Running a single process (not a desktop environment)     │
│                                                              │
│  Can you do GUI-in-container?                               │
│  • Technically yes (X11 forwarding, VNC, noVNC)             │
│  • But it's rare, heavy, and defeats the purpose            │
│                                                              │
│  GUI use cases are better solved with:                      │
│  ✅ VMs with full desktop environments                      │
│  ✅ Remote desktop into a VM                                │
│  ✅ Browser-based tools (noVNC, Guacamole)                  │
│  ✅ Dev containers + local IDE (VS Code Remote Containers)  │
│                                                              │
│  Practical takeaway:                                        │
│  ✅ SSH sometimes (not recommended, but possible)           │
│  ❌ RDP into containers is NOT how containers are used      │
└─────────────────────────────────────────────────────────────┘
```

**Interview-ready answer:**

```
Q: "Can you SSH or RDP into a Docker container?"

A: "SSH is technically possible by installing openssh-server inside
   the container, but it's not recommended. It increases image size,
   adds attack surface, and breaks the immutability principle.
   Instead, use 'docker exec -it <container> sh' for shell access,
   'docker logs' for output, and rebuild images for config changes.

   RDP is not practical for containers since they're headless and
   don't run desktop environments. GUI workloads belong in VMs."
```

---

## 4.8 Environment Variables at Runtime (-e)

Applications commonly use environment variables for configuration: database passwords, environment mode (dev/prod), API keys, port numbers. Docker lets you pass them at container startup.

### Passing Environment Variables

```bash
# Pass a single environment variable
$ docker run -it -e MYNAME=Adam centos /bin/bash

# Inside the container — verify it's set
[root@a1b2c3d4e5f6 /]# echo $MYNAME
Adam

[root@a1b2c3d4e5f6 /]# env | grep MYNAME
MYNAME=Adam

[root@a1b2c3d4e5f6 /]# exit
```

### Multiple Environment Variables

```bash
# Pass multiple -e flags
$ docker run -d --name app01 \
    -e APP_ENV=production \
    -e DB_HOST=10.0.0.5 \
    -e DB_PORT=5432 \
    -e DB_NAME=myapp \
    -e DB_PASSWORD=secret123 \
    nginx

# Verify all env vars are set
$ docker exec app01 env | grep -E "APP_ENV|DB_"

APP_ENV=production
DB_HOST=10.0.0.5
DB_PORT=5432
DB_NAME=myapp
DB_PASSWORD=secret123

# Clean up
$ docker rm -f app01
```

### Real-World Example: MySQL with Environment Variables

```bash
# MySQL image REQUIRES certain env vars to start
$ docker run -d --name mydb \
    -e MYSQL_ROOT_PASSWORD=rootpass \
    -e MYSQL_DATABASE=webapp \
    -e MYSQL_USER=appuser \
    -e MYSQL_PASSWORD=apppass \
    mysql:8

# Check it's running
$ docker ps --filter name=mydb
CONTAINER ID   IMAGE     STATUS         NAMES
f6a1b2c3d4e5   mysql:8   Up 10 seconds  mydb

# Connect to the database using the env vars we set
$ docker exec -it mydb mysql -u appuser -papppass webapp

mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| webapp             |
+--------------------+

mysql> exit

$ docker rm -f mydb
```

```
┌─────────────────────────────────────────────────────────────┐
│              ENVIRONMENT VARIABLES — KEY POINTS              │
│                                                              │
│  • -e sets env vars INSIDE the container only               │
│  • They don't affect the host machine                       │
│  • Many official images use env vars for configuration:     │
│    - MYSQL_ROOT_PASSWORD (mysql)                            │
│    - POSTGRES_PASSWORD (postgres)                           │
│    - NODE_ENV (node.js apps)                                │
│    - REDIS_PASSWORD (redis)                                 │
│  • For many env vars, use --env-file:                       │
│    docker run --env-file .env myimage                       │
│  • Never put secrets in Dockerfiles — use -e or --env-file │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.9 Working Directory (-w)

By default, a container starts in the directory defined by the image (often `/` or `/root`). Use `-w` to override the starting directory.

```bash
# Default: container starts in / (root directory)
$ docker run -it centos /bin/bash
[root@a1b2c3d4e5f6 /]# pwd
/

[root@a1b2c3d4e5f6 /]# exit

# With -w: container starts in /tmp
$ docker run -it -w /tmp centos /bin/bash
[root@b2c3d4e5f6a1 tmp]# pwd
/tmp

[root@b2c3d4e5f6a1 tmp]# exit
```

```bash
# Practical example: run a command in a specific directory
$ docker run --rm -w /etc centos ls -la passwd

-rw-r--r-- 1 root root 849 Sep 15  2021 passwd

# Without -w, you'd need: docker run centos ls -la /etc/passwd
# With -w, the command runs relative to /etc
```

```bash
# Real-world use: run npm install in the app directory
$ docker run --rm -w /app -v $(pwd):/app node:20-alpine npm install

# -w /app  → start in /app directory
# -v $(pwd):/app → mount current directory into /app
# npm install runs in /app context
```

---

## 4.10 Copying Files To/From Containers (docker cp)

`docker cp` copies files between the host and a container. It works with both running and stopped containers.

### Copy Host → Container

```bash
# Create a test file on the host
$ echo "hello from host" > dummy.txt

# Start a container
$ docker run -d --name test01 centos \
    /bin/sh -c 'while true; do sleep 10; done'

# Copy the file INTO the container
$ docker cp dummy.txt test01:/tmp/

# Verify it arrived
$ docker exec test01 ls /tmp/
dummy.txt

$ docker exec test01 cat /tmp/dummy.txt
hello from host
```

### Copy Container → Host

```bash
# Create a file inside the container
$ docker exec test01 sh -c 'echo "hello from container" > /tmp/container-file.txt'

# Copy it to the host
$ docker cp test01:/tmp/container-file.txt ./from-container.txt

# Verify on the host
$ cat from-container.txt
hello from container
```

### Copy Entire Directories

```bash
# Copy a directory from host to container
$ mkdir -p config && echo "key=value" > config/app.conf
$ docker cp config/ test01:/tmp/config/

$ docker exec test01 ls /tmp/config/
app.conf

$ docker exec test01 cat /tmp/config/app.conf
key=value
```

### Copy from Stopped Containers

```bash
# docker cp works even on stopped containers!
$ docker stop test01
$ docker cp test01:/tmp/dummy.txt ./recovered.txt
$ cat recovered.txt
hello from host

# This is useful for recovering data from crashed containers

# Clean up
$ docker rm test01
$ rm -f dummy.txt from-container.txt recovered.txt
$ rm -rf config
```

---

## 4.11 Deleting Containers and Data Loss Warning

### The Rule: You Cannot Remove a Running Container

```bash
# Try to remove a running container
$ docker run -d --name running-test nginx
$ docker rm running-test

# Error:
Error response from daemon: You cannot remove a running container abc123.
Stop the container before attempting removal or force remove.

# Fix: Stop first, then remove
$ docker stop running-test
$ docker rm running-test

# Or force remove (stop + remove in one step)
$ docker rm -f running-test
```

### What Gets Deleted When You Remove a Container

```
┌─────────────────────────────────────────────────────────────┐
│              WHAT docker rm DELETES                          │
│                                                              │
│  When you run docker rm <container>:                        │
│                                                              │
│  ❌ DELETED:                                                │
│  • Container's writable layer (all filesystem changes)     │
│  • Files created inside the container                      │
│  • Packages installed inside the container                 │
│  • Configuration changes made inside the container         │
│  • Container metadata (name, ID, logs)                     │
│                                                              │
│  ✅ NOT DELETED:                                            │
│  • The image (still available for new containers)          │
│  • Named volumes (persist independently)                   │
│  • Host files (bind mounts are on the host)                │
│                                                              │
│  This is why containers are called EPHEMERAL:              │
│  They are disposable. Data inside them is temporary        │
│  unless you use volumes (covered in Module 8).             │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating data loss:**

```bash
# Create a container and add data
$ docker run -it --name data-test centos /bin/bash
[root@abc123 /]# echo "important data" > /tmp/critical-file.txt
[root@abc123 /]# exit

# Data is still there (container is stopped, not removed)
$ docker start data-test
$ docker exec data-test cat /tmp/critical-file.txt
important data
$ docker stop data-test

# Now REMOVE the container
$ docker rm data-test

# Try to access the data — container is GONE
$ docker start data-test
Error: No such container: data-test

# The file /tmp/critical-file.txt is gone forever
# This is why you need VOLUMES for persistent data
```

### Bulk Cleanup Commands

```bash
# Remove all stopped containers
$ docker container prune

WARNING! This will remove all stopped containers.
Are you sure you want to continue? [y/N] y
Deleted Containers:
a1b2c3d4e5f6
b2c3d4e5f6a1
Total reclaimed space: 125MB

# Remove a specific container by name
$ docker rm mycontainer

# Remove multiple containers at once
$ docker rm container1 container2 container3

# Force remove all containers (including running ones!)
$ docker rm -f $(docker ps -aq)
# ⚠️ Be careful — this kills and removes EVERYTHING
```

---

## 4.12 Attached vs Detached: Best Practices Summary

```
┌──────────────────────────────────────────────────────────────┐
│              ATTACHED vs DETACHED — WHEN TO USE WHICH        │
│                                                               │
│  ATTACHED MODE (-it)                                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Use for:                                             │    │
│  │  • Quick debugging and learning                      │    │
│  │  • Interactive shell experiments                     │    │
│  │  • One-off commands                                  │    │
│  │  • Python/Node REPL sessions                         │    │
│  │                                                       │    │
│  │  Example:                                             │    │
│  │  docker run -it centos /bin/bash                     │    │
│  │                                                       │    │
│  │  Behavior:                                            │    │
│  │  • Your terminal is locked to the container          │    │
│  │  • You see output directly                           │    │
│  │  • exit or Ctrl+D stops the container                │    │
│  │                                                       │    │
│  │  Detach WITHOUT stopping:                             │    │
│  │  • Press Ctrl+P, then Ctrl+Q                         │    │
│  │  • Container keeps running in background             │    │
│  │  • Reattach later with docker attach <name>          │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  DETACHED MODE (-d)                                          │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Use for:                                             │    │
│  │  • Running services (web servers, databases, APIs)   │    │
│  │  • Production workloads                              │    │
│  │  • Background tasks and workers                      │    │
│  │                                                       │    │
│  │  Example:                                             │    │
│  │  docker run -d --name web nginx                      │    │
│  │                                                       │    │
│  │  Behavior:                                            │    │
│  │  • Container runs in background                      │    │
│  │  • Your terminal is free                             │    │
│  │  • Use docker logs to see output                     │    │
│  │  • Use docker exec -it to get a shell                │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                               │
│  TROUBLESHOOTING DETACHED CONTAINERS                         │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  View logs:    docker logs -f <name>                 │    │
│  │  Run command:  docker exec <name> <cmd>              │    │
│  │  Get shell:    docker exec -it <name> bash           │    │
│  │  Check status: docker ps                             │    │
│  │  Check stats:  docker stats <name>                   │    │
│  │                                                       │    │
│  │  NEVER use docker attach on production containers    │    │
│  │  (risk of accidentally killing PID 1)                │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Detaching from an Interactive Container Without Stopping It

When you're inside an interactive container (`-it`), typing `exit` stops the container because it terminates PID 1. To leave the container running and return to your host shell, use the **detach escape sequence**:

```bash
# Start an interactive container
$ docker run -it --name demo ubuntu

# You're now inside the container
root@abc123:/# hostname
abc123

# Press Ctrl+P, then Ctrl+Q (two key combos in sequence)
# Output on host:
# read escape sequence

# Back on the host — container is still running
$ docker ps
# CONTAINER ID   IMAGE    STATUS         NAMES
# abc123         ubuntu   Up 2 minutes   demo

# Reattach to the container
$ docker attach demo

# You're back inside the container
root@abc123:/#

# ⚠️  If you type exit now, the container stops
# Use Ctrl+P, Ctrl+Q again to detach safely
```

```
┌─────────────────────────────────────────────────────────────┐
│              EXITING vs DETACHING                            │
│                                                              │
│  exit / Ctrl+D:                                             │
│    Terminates the shell (PID 1) → container STOPS           │
│    Container status: Exited                                 │
│                                                              │
│  Ctrl+P, Ctrl+Q:                                            │
│    Detaches your terminal → container KEEPS RUNNING         │
│    Container status: Up                                     │
│    Reattach with: docker attach <name>                      │
│                                                              │
│  Ctrl+C:                                                    │
│    Sends SIGINT to PID 1 → usually STOPS the container     │
│    Behavior depends on how PID 1 handles SIGINT             │
└─────────────────────────────────────────────────────────────┘
```

### Command Syntax Styles — Grouped vs Legacy

Docker supports two syntax styles. Both work identically, but the grouped style is recommended for clarity.

```
┌──────────────────┬──────────────────────────────────────────┐
│ Style            │ Example                                  │
├──────────────────┼──────────────────────────────────────────┤
│ Grouped (new)    │ docker container run -it ubuntu          │
│                  │ docker container ls -a                   │
│                  │ docker container rm abc123               │
│                  │ docker image ls                          │
│                  │ docker network create mynet              │
├──────────────────┼──────────────────────────────────────────┤
│ Legacy (old)     │ docker run -it ubuntu                    │
│                  │ docker ps -a                             │
│                  │ docker rm abc123                         │
│                  │ docker images                            │
│                  │ docker network create mynet              │
└──────────────────┴──────────────────────────────────────────┘

Both styles are valid. This course uses both interchangeably.
The grouped style makes it clear which Docker object you're
operating on (container, image, network, volume).
```

---

## 4.13 Container Resource Monitoring

```bash
# Live resource usage (all containers)
docker stats

# Output:
# CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT     MEM %   NET I/O          BLOCK I/O        PIDS
# abc123def456   web-app     0.50%   45.2MiB / 512MiB      8.83%   1.2kB / 800B     0B / 4.1kB       5
# def456abc789   database    2.30%   256MiB / 1GiB          25.0%   5.6kB / 3.2kB    12MB / 45MB      28
# ghi789jkl012   cache       0.10%   12.5MiB / 256MiB      4.88%   800B / 400B      0B / 0B          4

# Column meanings:
# CPU %         → Percentage of host CPU used
# MEM USAGE     → Current memory / Limit
# MEM %         → Percentage of memory limit used
# NET I/O       → Network bytes received / sent
# BLOCK I/O     → Disk bytes read / written
# PIDS          → Number of processes

# Single container, non-streaming
docker stats --no-stream web-app

# Format output
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
# Output:
# NAME        CPU %   MEM USAGE / LIMIT
# web-app     0.50%   45.2MiB / 512MiB
# database    2.30%   256MiB / 1GiB
```

---

## 4.14 Container Resource Limits — Preventing Rogue Containers

### Default Behavior: No Limits

By default, a container process can grow its resource usage until it hits OS constraints or causes system pressure. This means one container can starve others.

```
┌─────────────────────────────────────────────────────────────┐
│              THE "NOISY NEIGHBOR" PROBLEM                    │
│                                                              │
│  Without limits:                                            │
│                                                              │
│  Host RAM: 8 GB                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container A (web app) ......... using 200 MB        │   │
│  │  Container B (database) ........ using 1 GB          │   │
│  │  Container C (rogue process) ... using 6 GB ⚠️       │   │
│  │  Host OS ........................ needs 1 GB          │   │
│  │                                                       │   │
│  │  Total: 7.2 GB → system under pressure!              │   │
│  │  Container A and B start swapping, become slow       │   │
│  │  Or OOM killer randomly kills a container            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ✅ Yes — if you don't set limits, one container can        │
│     starve others. This is the "noisy neighbor" problem.    │
└─────────────────────────────────────────────────────────────┘
```

### How Docker Controls Resources (cgroups)

Docker uses Linux **cgroups** (control groups) to limit container resources:

```
┌──────────────────────────────────────────────────────────────┐
│  Resource    │ What cgroups control                          │
├──────────────┼──────────────────────────────────────────────┤
│  Memory      │ Maximum RAM the container can use             │
│  CPU         │ How much CPU time the container gets          │
│  I/O         │ Disk read/write bandwidth limits              │
│  PIDs        │ Maximum number of processes in the container  │
└──────────────┴──────────────────────────────────────────────┘
```

### Memory Limit Commands + Outputs

**Run a container with a memory limit:**

```bash
# Set a hard memory limit of 256MB
$ docker run -d --name m1 --memory="256m" nginx:latest

# Output:
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2

# What this means:
# The container CANNOT exceed 256 MB RAM
# This is a MAXIMUM LIMIT, not a reservation
# The container will use only what it needs (maybe 10-30MB for nginx)
```

**Check actual usage vs limit:**

```bash
$ docker stats m1 --no-stream

# Output:
CONTAINER ID   NAME   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O       BLOCK I/O
a1b2c3d4e5f6   m1     0.02%   12.5MiB / 256MiB    4.9%    1.2kB / 0B    0B / 0B

# Notice: Using only 12.5 MB out of 256 MB limit
# The limit is the CEILING, not the FLOOR
# Memory is used ON DEMAND, not reserved upfront
```

**Inspect the memory limit programmatically:**

```bash
$ docker inspect m1 --format='{{.HostConfig.Memory}}'

# Output:
268435456

# That's 268435456 bytes = 256 MB (256 × 1024 × 1024)

# More readable format:
$ docker inspect m1 --format='{{.HostConfig.Memory}}' | awk '{printf "%.0f MB\n", $1/1024/1024}'
256 MB
```

### What Happens When a Container Exceeds Its Memory Limit?

The kernel OOM (Out Of Memory) killer terminates the container process. The container exits with code 137.

```bash
# Demo: Create a container that tries to use more memory than allowed
$ docker run -d --name oom-test --memory="50m" python:3.12-slim \
    python -c "
data = []
while True:
    data.append('A' * 1024 * 1024)  # Allocate 1MB at a time
"

# Wait a few seconds, then check
$ docker ps -a --filter name=oom-test

# Output:
CONTAINER ID   IMAGE              COMMAND                  CREATED          STATUS                      NAMES
b2c3d4e5f6a1   python:3.12-slim   "python -c '\ndata =…"   10 seconds ago   Exited (137) 5 seconds ago   oom-test

# Exit code 137 = killed by OOM

# Confirm OOM kill:
$ docker inspect oom-test --format='OOMKilled: {{.State.OOMKilled}} | ExitCode: {{.State.ExitCode}}'

# Output:
OOMKilled: true | ExitCode: 137

# Clean up
$ docker rm oom-test
```

```
┌─────────────────────────────────────────────────────────────┐
│              OOM KILL EXPLAINED                              │
│                                                              │
│  Container tries to allocate more than --memory limit       │
│       │                                                      │
│       ▼                                                      │
│  Linux kernel OOM killer activates                          │
│       │                                                      │
│       ▼                                                      │
│  Container's main process is killed                         │
│       │                                                      │
│       ▼                                                      │
│  Container exits with code 137 (128 + 9 = SIGKILL)         │
│       │                                                      │
│       ▼                                                      │
│  docker inspect shows: OOMKilled: true                      │
│                                                              │
│  This matches the rule: "container will stop/crash           │
│  if it hits the limit."                                     │
└─────────────────────────────────────────────────────────────┘
```

### Limits Are Maximums, Not Reservations

This is a common point of confusion. Setting `--memory="2g"` does NOT immediately consume 2 GB of host RAM.

```
┌─────────────────────────────────────────────────────────────┐
│              LIMITS vs RESERVATIONS                          │
│                                                              │
│  Host has 12 GB RAM. You run 3 containers:                  │
│                                                              │
│  Container A: --memory="2g" (limit)                         │
│  Container B: --memory="2g" (limit)                         │
│  Container C: --memory="2g" (limit)                         │
│                                                              │
│  Does the host immediately lose 6 GB?                       │
│  ❌ NO.                                                     │
│                                                              │
│  Host loses only what's ACTUALLY USED at runtime:           │
│                                                              │
│  Container A currently using: 800 MB                        │
│  Container B currently using: 1.2 GB                        │
│  Container C currently using: 500 MB                        │
│  ─────────────────────────────────────────                  │
│  Total actual usage: 2.5 GB (not 6 GB)                     │
│                                                              │
│  The --memory flag sets the CEILING.                        │
│  Each container can grow UP TO that limit.                  │
│  But it only uses what the app actually needs.              │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating this:**

```bash
# Start a container with 512MB limit
$ docker run -d --name limitdemo --memory="512m" nginx

# Watch actual memory usage
$ docker stats limitdemo --no-stream

CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT   MEM %   NET I/O     BLOCK I/O
a1b2c3d4e5f6   limitdemo   0.00%   12.8MiB / 512MiB    2.5%    0B / 0B     0B / 0B

# Only 12.8 MB used even though limit is 512 MB!
# The remaining 499.2 MB is available for other containers/processes

$ docker rm -f limitdemo
```

### CPU Limit Commands

```bash
# Limit to 1 CPU core
$ docker run -d --name cpu1 --cpus="1.0" nginx:latest

# Limit to half a CPU core
$ docker run -d --name cpu-half --cpus="0.5" nginx:latest

# Combined memory + CPU limits (production pattern)
$ docker run -d --name app \
    --memory="512m" \
    --cpus="1.0" \
    myimage:tag

# Check limits
$ docker stats app --no-stream

CONTAINER ID   NAME   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O     BLOCK I/O
d4e5f6a1b2c3   app    0.05%   45MiB / 512MiB      8.8%    1kB / 0B    0B / 0B

# Inspect all resource limits
$ docker inspect app --format='
Memory Limit: {{.HostConfig.Memory}}
CPU Limit: {{.HostConfig.NanoCpus}}
CPU Shares: {{.HostConfig.CpuShares}}'

# Output:
Memory Limit: 536870912
CPU Limit: 1000000000
CPU Shares: 0
```

### Scaling Containers

Containers scale easily because images are reusable templates and startup is fast.

```bash
# ─── MANUAL SCALING ──────────────────────────────────────
# Run 3 instances of the same app on different ports
$ docker run -d --name web-1 -p 8081:80 nginx:latest
$ docker run -d --name web-2 -p 8082:80 nginx:latest
$ docker run -d --name web-3 -p 8083:80 nginx:latest

$ docker ps
CONTAINER ID   IMAGE          COMMAND                  STATUS          PORTS                  NAMES
a1b2c3d4e5f6   nginx:latest   "/docker-entrypoint.…"   Up 5 seconds    0.0.0.0:8081->80/tcp   web-1
b2c3d4e5f6a1   nginx:latest   "/docker-entrypoint.…"   Up 4 seconds    0.0.0.0:8082->80/tcp   web-2
c3d4e5f6a1b2   nginx:latest   "/docker-entrypoint.…"   Up 3 seconds    0.0.0.0:8083->80/tcp   web-3

# All 3 started in seconds from the same image

# ─── DOCKER COMPOSE SCALING ─────────────────────────────
# Scale with Docker Compose (much easier)
$ docker compose up --scale web=5

# Output:
[+] Running 5/5
 ✔ Container project-web-1  Started
 ✔ Container project-web-2  Started
 ✔ Container project-web-3  Started
 ✔ Container project-web-4  Started
 ✔ Container project-web-5  Started

# Scale down
$ docker compose up --scale web=2

# In Kubernetes (production):
$ kubectl scale deployment web --replicas=10
```

---

## 4.15 Container Logs — Deep Dive

```bash
# View all logs
docker logs my-container

# Follow logs (real-time streaming)
docker logs -f my-container

# Show last N lines
docker logs --tail 50 my-container

# Show logs since a timestamp
docker logs --since 2024-01-15T10:00:00 my-container

# Show logs from last 30 minutes
docker logs --since 30m my-container

# Show logs with timestamps
docker logs -t my-container
# Output:
# 2024-01-15T10:30:00.123456789Z Server started on port 3000
# 2024-01-15T10:30:05.987654321Z GET /api/users 200 15ms

# Combine options: last 100 lines with timestamps, follow
docker logs -f --tail 100 -t my-container

# Redirect logs to a file
docker logs my-container > container.log 2>&1
```

### Log Drivers

```bash
# Check current log driver
docker inspect --format='{{.HostConfig.LogConfig.Type}}' my-container
# Output: json-file

# Available log drivers:
# json-file  → Default. Logs stored as JSON files on host
# syslog     → Send to syslog
# journald   → Send to systemd journal
# fluentd    → Send to Fluentd
# awslogs    → Send to AWS CloudWatch
# gcplogs    → Send to Google Cloud Logging
# none       → Disable logging

# Configure log rotation (prevent disk full)
docker run -d \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  --name my-app \
  my-app:1.0

# MEANING: Each log file max 10MB, keep 5 files.
# Total max log storage: 50MB per container.

# Where are logs stored on the host?
# /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

---

## 4.16 Container Health Checks

```bash
# Run a container with a health check
docker run -d \
  --name healthy-app \
  --health-cmd="curl -f http://localhost:3000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=5s \
  --health-retries=3 \
  --health-start-period=10s \
  my-app:1.0

# Flags:
# --health-cmd          → Command to check health
# --health-interval     → Time between checks (default: 30s)
# --health-timeout      → Max time for check to complete (default: 30s)
# --health-retries      → Consecutive failures before "unhealthy" (default: 3)
# --health-start-period → Grace period for startup (default: 0s)

# Check health status
docker ps
# CONTAINER ID   IMAGE       STATUS                    NAMES
# abc123def456   my-app:1.0  Up 2 min (healthy)        healthy-app

# Possible statuses:
# (health: starting)  → Within start-period, checks running
# (healthy)           → Health check passing
# (unhealthy)         → Health check failing

# View health check history
docker inspect --format='{{json .State.Health}}' healthy-app | python3 -m json.tool

# Output:
# {
#     "Status": "healthy",
#     "FailingStreak": 0,
#     "Log": [
#         {
#             "Start": "2024-01-15T10:30:00Z",
#             "End": "2024-01-15T10:30:00Z",
#             "ExitCode": 0,
#             "Output": "OK"
#         }
#     ]
# }
```

---

## 4.17 Container Restart Policies — Production Patterns

```bash
# Policy: no (default)
docker run -d --restart=no my-app:1.0
# Container stays stopped if it crashes or host reboots.
# Use for: development, one-off tasks

# Policy: always
docker run -d --restart=always my-app:1.0
# Always restarts, even after host reboot.
# Use for: production services that must always run

# Policy: unless-stopped
docker run -d --restart=unless-stopped my-app:1.0
# Like "always", but respects manual docker stop.
# Use for: services you might want to manually stop

# Policy: on-failure[:max-retries]
docker run -d --restart=on-failure:5 my-app:1.0
# Restarts only on non-zero exit code, max 5 times.
# Use for: batch jobs that should retry on failure

# Update restart policy on existing container
docker update --restart=always my-container
```

### Restart Behavior Comparison

```
┌─────────────────┬──────────┬──────────┬──────────────┬──────────────┐
│ Scenario        │ no       │ always   │ unless-stop  │ on-failure   │
├─────────────────┼──────────┼──────────┼──────────────┼──────────────┤
│ Container crash │ Stays    │ Restarts │ Restarts     │ Restarts     │
│                 │ stopped  │          │              │ (up to max)  │
├─────────────────┼──────────┼──────────┼──────────────┼──────────────┤
│ docker stop     │ Stays    │ Stays    │ Stays        │ Stays        │
│                 │ stopped  │ stopped  │ stopped      │ stopped      │
├─────────────────┼──────────┼──────────┼──────────────┼──────────────┤
│ Host reboot     │ Stays    │ Restarts │ Stays        │ Stays        │
│                 │ stopped  │          │ stopped      │ stopped      │
├─────────────────┼──────────┼──────────┼──────────────┼──────────────┤
│ Clean exit (0)  │ Stays    │ Restarts │ Restarts     │ Stays        │
│                 │ stopped  │          │              │ stopped      │
└─────────────────┴──────────┴──────────┴──────────────┴──────────────┘
```

---

## 4.18 Filtering and Formatting Container Output

```bash
# Filter by status
docker ps -a --filter status=exited
docker ps --filter status=running

# Filter by name (partial match)
docker ps --filter name=web

# Filter by image
docker ps --filter ancestor=nginx

# Filter by label
docker run -d --label env=production nginx
docker ps --filter label=env=production

# Filter by network
docker ps --filter network=my-network

# Custom format output
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# Output:
# CONTAINER ID   NAMES        STATUS         PORTS
# abc123def456   web-app      Up 2 hours     0.0.0.0:8080->80/tcp
# def456abc789   database     Up 2 hours     5432/tcp

# JSON format (for scripting)
docker ps --format "{{json .}}" | python3 -m json.tool

# Get only container IDs (useful for scripting)
docker ps -q
# Output:
# abc123def456
# def456abc789

# Stop all running containers
docker stop $(docker ps -q)

# Remove all stopped containers
docker rm $(docker ps -aq --filter status=exited)
```

---

## 4.19 Container Diff — See What Changed

```bash
# See filesystem changes made inside a container
docker diff my-container

# Output:
# C /var                    ← Changed
# C /var/log                ← Changed
# A /var/log/app.log        ← Added
# C /tmp                    ← Changed
# A /tmp/cache.dat          ← Added
# D /app/old-config.json    ← Deleted

# Symbols:
# A = Added
# C = Changed
# D = Deleted

# MEANING: Shows what files were modified compared to the original image.
# Useful for debugging — see what a running process has changed.
```

---

## 4.20 Committing Container Changes to a New Image

```bash
# Make changes inside a container
docker run -it --name custom-ubuntu ubuntu bash
root@abc123:/# apt-get update && apt-get install -y curl vim git
root@abc123:/# exit

# Commit the container as a new image
docker commit custom-ubuntu my-custom-ubuntu:1.0

# Output:
# sha256:abc123def456...

# MEANING: Creates a new image from the container's current state.
# The new image includes all changes made inside the container.

# Verify
docker images my-custom-ubuntu
# REPOSITORY         TAG   IMAGE ID       SIZE
# my-custom-ubuntu   1.0   abc123def456   250MB

# Run the new image — curl, vim, git are pre-installed
docker run -it my-custom-ubuntu:1.0 bash
root@def456:/# which curl vim git
# /usr/bin/curl
# /usr/bin/vim
# /usr/bin/git

# Add metadata during commit
docker commit \
  --author "John Doe <john@example.com>" \
  --message "Added curl, vim, git" \
  custom-ubuntu my-custom-ubuntu:1.1

# NOTE: docker commit is useful for debugging and experimentation.
# For production, ALWAYS use Dockerfiles — they're reproducible and version-controlled.
```

---

## 4.21 Real-World Industry Example: Running a Production Node.js App

```bash
# Production-grade container run command
docker run -d \
  --name production-api \
  --restart=unless-stopped \
  --memory=512m \
  --cpus=1 \
  --pids-limit=100 \
  --read-only \
  --tmpfs /tmp:rw,size=50m \
  --user 1000:1000 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -e DATABASE_URL=postgresql://user:pass@db:5432/myapp \
  --health-cmd="wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1" \
  --health-interval=30s \
  --health-timeout=5s \
  --health-retries=3 \
  --health-start-period=15s \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  --network app-network \
  my-api:1.2.3

# Breakdown of security measures:
# --read-only           → Filesystem is read-only (prevents file tampering)
# --tmpfs /tmp          → Writable /tmp in RAM (for temp files)
# --user 1000:1000      → Non-root user (limits damage if compromised)
# --cap-drop ALL        → Remove all Linux capabilities
# --no-new-privileges   → Prevent privilege escalation
# --pids-limit=100      → Prevent fork bombs
# --memory=512m         → Prevent memory exhaustion
```

---

## 4.22 Common Errors and Troubleshooting

### Error 1: Container OOMKilled (Out of Memory)
```bash
$ docker inspect my-container --format='{{.State.OOMKilled}}'
# true

# CAUSE: Container exceeded its memory limit

# Diagnose:
docker stats --no-stream my-container
docker logs my-container | tail -20

# Fix Option 1: Increase memory limit
docker update --memory=1g my-container
docker restart my-container

# Fix Option 2: Fix the memory leak in your application
# Check for: unclosed connections, growing arrays, event listener leaks
```

### Error 2: Container Keeps Restarting
```bash
$ docker ps
# STATUS: Restarting (1) 2 seconds ago

# Diagnose:
docker logs my-container
# Look for the error causing the crash

# Check restart count:
docker inspect --format='{{.RestartCount}}' my-container
# Output: 15

# Temporarily stop restarts to debug:
docker update --restart=no my-container
docker stop my-container

# Fix the issue, then re-enable:
docker update --restart=unless-stopped my-container
docker start my-container
```

### Error 3: Cannot Connect to Container Port
```bash
# Symptom: curl http://localhost:8080 → Connection refused

# Step 1: Verify port mapping
docker port my-container
# Output: 80/tcp -> 0.0.0.0:8080

# Step 2: Verify container is running
docker ps --filter name=my-container

# Step 3: Check if app is listening inside container
docker exec my-container netstat -tlnp
# or
docker exec my-container ss -tlnp

# Step 4: Check if app is binding to 0.0.0.0 (not 127.0.0.1)
# Common mistake: App binds to localhost inside container
# Fix: Bind to 0.0.0.0 so Docker can forward traffic

# Node.js: server.listen(3000, '0.0.0.0')
# Python Flask: app.run(host='0.0.0.0', port=5000)
# Go: http.ListenAndServe(":8080", handler)
```

### Error 4: "No such container" After Host Reboot
```bash
$ docker start my-container
# Error: No such container: my-container

# CAUSE: Container was created with --rm flag, or was pruned

# Prevention: Use --restart=unless-stopped for persistent containers
# Recovery: Re-run the docker run command

# List all containers (including stopped)
docker ps -a
```

### Error 5: Exec into Container Fails
```bash
$ docker exec -it my-container bash
# OCI runtime exec failed: exec failed: unable to start container process:
# exec: "bash": executable file not found in $PATH

# CAUSE: Container doesn't have bash (common with Alpine images)

# Fix: Use sh instead
docker exec -it my-container sh

# Or use the full path
docker exec -it my-container /bin/sh
```

---

## 4.23 Mini-Lab: Prove That Limits Are Maximums, Not Reservations

This quick lab demonstrates that `--memory` sets a ceiling, not a reservation.

```bash
# ─── LAB A: Memory limit is a ceiling ────────────────────

# Step 1: Start a container with 512MB limit
$ docker run -d --name limitdemo --memory="512m" nginx
a1b2c3d4e5f6...

# Step 2: Watch actual memory usage
$ docker stats limitdemo --no-stream

CONTAINER ID   NAME        CPU %   MEM USAGE / LIMIT   MEM %   NET I/O     BLOCK I/O
a1b2c3d4e5f6   limitdemo   0.00%   12.8MiB / 512MiB    2.5%    0B / 0B     0B / 0B

# Result: Only 12.8 MB used even though limit is 512 MB!
# The remaining 499.2 MB is NOT reserved — it's available for other processes.

# Step 3: Verify with docker inspect
$ docker inspect limitdemo --format='Memory Limit: {{.HostConfig.Memory}} bytes'
Memory Limit: 536870912 bytes

# 536870912 bytes = 512 MB (the ceiling)
# But actual usage is only ~13 MB (the floor)

# Clean up
$ docker rm -f limitdemo
```

```bash
# ─── LAB B: OOM kill when limit exceeded ─────────────────

# Step 1: Run a container that will exceed its memory limit
$ docker run -d --name oom-demo --memory="64m" python:3.12-slim \
    python -c "
data = []
for i in range(100):
    data.append(bytearray(1024 * 1024))  # 1MB per iteration
    print(f'Allocated {i+1} MB')
"

# Step 2: Wait 5-10 seconds, then check
$ docker ps -a --filter name=oom-demo --format "table {{.Names}}\t{{.Status}}"

NAMES      STATUS
oom-demo   Exited (137) 3 seconds ago

# Exit code 137 = OOM killed

# Step 3: Confirm OOM
$ docker inspect oom-demo --format='OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'
OOMKilled=true ExitCode=137

# Step 4: Check logs to see how far it got
$ docker logs oom-demo
Allocated 1 MB
Allocated 2 MB
...
Allocated 52 MB
# Killed before reaching 64 MB (some overhead for Python runtime)

# Clean up
$ docker rm oom-demo
```

```bash
# ─── LAB C: Multiple containers sharing host resources ───

# Start 3 containers with different limits
$ docker run -d --name app1 --memory="256m" --cpus="0.5" nginx
$ docker run -d --name app2 --memory="512m" --cpus="1.0" nginx
$ docker run -d --name app3 --memory="128m" --cpus="0.25" nginx

# Check all resource usage at once
$ docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

NAME   CPU %   MEM USAGE / LIMIT   MEM %
app1   0.00%   3.1MiB / 256MiB     1.21%
app2   0.00%   3.2MiB / 512MiB     0.63%
app3   0.00%   2.9MiB / 128MiB     2.27%

# Total actual usage: ~9.2 MB
# Total limits: 896 MB
# Host RAM is NOT reduced by 896 MB — only by ~9.2 MB

# Clean up
$ docker rm -f app1 app2 app3
```

---

## 4.24 Container Management Commands — Cheat Sheet

```bash
# ─── CONTAINER LIFECYCLE ─────────────────────────────────
docker create --name <n> <image>       # Create (don't start)
docker start <container>               # Start a created/stopped container
docker run -d --name <n> <image>       # Create + start (detached)
docker stop <container>                # Graceful stop (SIGTERM → SIGKILL)
docker kill <container>                # Force stop (SIGKILL immediately)
docker restart <container>             # Stop + start
docker pause <container>               # Freeze (SIGSTOP)
docker unpause <container>             # Unfreeze
docker rm <container>                  # Remove stopped container
docker rm -f <container>               # Force remove (even running)

# ─── INFORMATION ─────────────────────────────────────────
docker ps                              # List running containers
docker ps -a                           # List ALL containers
docker logs <container>                # View logs
docker logs -f <container>             # Follow logs (real-time)
docker logs --tail 100 <container>     # Last 100 lines
docker inspect <container>             # Full JSON details
docker stats                           # Live resource usage
docker stats --no-stream               # Snapshot of resource usage
docker top <container>                 # Running processes
docker port <container>                # Port mappings
docker diff <container>                # Filesystem changes

# ─── INTERACTION ─────────────────────────────────────────
docker exec -it <container> sh         # Shell into container
docker exec <container> <cmd>          # Run command in container
docker cp <src> <container>:<dst>      # Copy file TO container
docker cp <container>:<src> <dst>      # Copy file FROM container
docker attach <container>              # Attach to main process

# ─── RESOURCE LIMITS ─────────────────────────────────────
docker run --memory="512m" <image>     # Memory limit
docker run --cpus="1.0" <image>        # CPU limit
docker run --cpus="0.5" <image>        # Half a CPU core
docker run --pids-limit=100 <image>    # Process count limit
docker update --memory="1g" <container> # Update limits live

# ─── CLEANUP ─────────────────────────────────────────────
docker container prune                 # Remove all stopped containers
docker rm $(docker ps -aq)             # Remove all containers (stopped)
docker rm -f $(docker ps -aq)          # Force remove ALL containers
```

---

## 4.25 Interview-Ready One-Liners

Quick, confident answers for common Docker interview questions:

```
┌─────────────────────────────────────────────────────────────────┐
│  Question                          │ Answer                     │
├────────────────────────────────────┼────────────────────────────┤
│  "Can you SSH into a container?"   │ "Possible but not          │
│                                    │ recommended. Use           │
│                                    │ 'docker exec' and rebuild  │
│                                    │ images for changes."       │
├────────────────────────────────────┼────────────────────────────┤
│  "Why are containers lightweight?" │ "They share the host       │
│                                    │ kernel and don't boot a    │
│                                    │ full OS like VMs."         │
├────────────────────────────────────┼────────────────────────────┤
│  "Why set memory limits?"          │ "To prevent noisy-neighbor │
│                                    │ issues and protect host    │
│                                    │ stability. Limits are      │
│                                    │ enforced by cgroups."      │
├────────────────────────────────────┼────────────────────────────┤
│  "What happens when memory is      │ "Kernel OOM kills the      │
│   exceeded?"                       │ container process.         │
│                                    │ Container exits with       │
│                                    │ code 137."                 │
├────────────────────────────────────┼────────────────────────────┤
│  "What is a Docker image?"         │ "A read-only layered       │
│                                    │ filesystem. A container    │
│                                    │ adds a writable layer      │
│                                    │ on top."                   │
├────────────────────────────────────┼────────────────────────────┤
│  "Are limits reservations?"        │ "No. --memory sets a       │
│                                    │ ceiling, not a floor.      │
│                                    │ Containers use only what   │
│                                    │ they need."                │
├────────────────────────────────────┼────────────────────────────┤
│  "Registry security risk?"         │ "Use trusted sources,      │
│                                    │ scan images for CVEs,      │
│                                    │ and enforce signing         │
│                                    │ policies."                 │
├────────────────────────────────────┼────────────────────────────┤
│  "Docker daemon vs client?"        │ "Client sends commands     │
│                                    │ via REST API. Daemon does  │
│                                    │ the work — manages         │
│                                    │ containers, images,        │
│                                    │ networks, volumes."        │
├────────────────────────────────────┼────────────────────────────┤
│  "What is a Docker host?"          │ "Any machine running       │
│                                    │ Docker Engine — bare       │
│                                    │ metal, VM, or cloud        │
│                                    │ instance."                 │
├────────────────────────────────────┼────────────────────────────┤
│  "Can a rogue container affect     │ "Yes, without limits.      │
│   others?"                         │ Use --memory and --cpus    │
│                                    │ to prevent noisy           │
│                                    │ neighbors."                │
├────────────────────────────────────┼────────────────────────────┤
│  "How do you scale containers?"    │ "Same image, fast startup. │
│                                    │ Use 'docker compose        │
│                                    │ --scale' or Kubernetes     │
│                                    │ replicas."                 │
├────────────────────────────────────┼────────────────────────────┤
│  "RDP into a container?"           │ "Not practical. Containers │
│                                    │ are headless — no desktop  │
│                                    │ environment. GUI workloads │
│                                    │ belong in VMs."            │
├────────────────────────────────────┼────────────────────────────┤
│  "What does docker run do          │ "It combines pull (if      │
│   internally?"                     │ needed), create, and start │
│                                    │ into one command."         │
├────────────────────────────────────┼────────────────────────────┤
│  "Does each docker run create      │ "Yes. Every docker run     │
│   a new container?"                │ creates a new container.   │
│                                    │ Use docker start to reuse  │
│                                    │ an existing one."          │
├────────────────────────────────────┼────────────────────────────┤
│  "What is the default CMD?"        │ "The command defined in    │
│                                    │ image metadata. Runs if    │
│                                    │ user doesn't specify one.  │
│                                    │ Override by appending a    │
│                                    │ command after image name." │
├────────────────────────────────────┼────────────────────────────┤
│  "Why does a container stop        │ "A container runs one main │
│   after a command finishes?"       │ process (PID 1). When that │
│                                    │ process exits, the         │
│                                    │ container stops."          │
├────────────────────────────────────┼────────────────────────────┤
│  "Is the container filesystem      │ "Yes. Files created inside │
│   isolated from the host?"         │ a container are NOT visible│
│                                    │ on the host. Each container│
│                                    │ has its own writable       │
│                                    │ layer."                    │
├────────────────────────────────────┼────────────────────────────┤
│  "Do containers allocate RAM       │ "No. Containers use RAM on │
│   upfront like VMs?"               │ demand. --memory sets a    │
│                                    │ ceiling, not a reservation.│
│                                    │ An idle container uses     │
│                                    │ almost no RAM."            │
└────────────────────────────────────┴────────────────────────────┘
```

---

## 4.26 Real-World Production Example: Web Server Lifecycle

This walkthrough shows the complete lifecycle of a production-style container from start to finish:

```bash
# ─── Step 1: Run a web server in detached mode ──────────
$ docker run -d --name web -p 8080:80 nginx

# Output:
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2

# ─── Step 2: Verify it's running ─────────────────────────
$ docker ps

CONTAINER ID   IMAGE   COMMAND                  CREATED          STATUS          PORTS                  NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   10 seconds ago   Up 9 seconds    0.0.0.0:8080->80/tcp   web

# ─── Step 3: Test the web server ─────────────────────────
$ curl http://localhost:8080

<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...
</html>

# ─── Step 4: Check logs ─────────────────────────────────
$ docker logs web

/docker-entrypoint.sh: Configuration complete; ready for start up
172.17.0.1 - - [15/Jan/2024:10:30:15 +0000] "GET / HTTP/1.1" 200 615

# ─── Step 5: Stop the server ────────────────────────────
$ docker stop web
web

$ docker ps
# (empty — no running containers)

$ docker ps -a --filter name=web
CONTAINER ID   IMAGE   COMMAND                  STATUS                     NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   Exited (0) 5 seconds ago   web

# ─── Step 6: Start it again (same container) ────────────
$ docker start web
web

$ docker ps
CONTAINER ID   IMAGE   COMMAND                  STATUS         PORTS                  NAMES
a1b2c3d4e5f6   nginx   "/docker-entrypoint.…"   Up 2 seconds   0.0.0.0:8080->80/tcp   web

# Same container ID — it's the same container, restarted

# ─── Step 7: Stop and remove (full cleanup) ─────────────
$ docker stop web
$ docker rm web

# Or in one command:
$ docker rm -f web
```

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE CONTAINER LIFECYCLE                    │
│                                                              │
│  docker run -d --name web nginx                             │
│       │                                                      │
│       ▼                                                      │
│  Container Created (ID assigned, layers set up)             │
│       │                                                      │
│       ▼                                                      │
│  Container Started (PID 1 = nginx)                          │
│       │                                                      │
│       ▼                                                      │
│  Process Running (serving HTTP requests)                    │
│       │                                                      │
│       ├──── docker logs web → view output                   │
│       ├──── docker exec -it web bash → shell access         │
│       ├──── docker stats web → resource usage               │
│       │                                                      │
│       ▼                                                      │
│  docker stop web (or process exits on its own)              │
│       │                                                      │
│       ▼                                                      │
│  Container Stopped (Exited state)                           │
│       │                                                      │
│       ├──── docker start web → running again                │
│       │                                                      │
│       ▼                                                      │
│  docker rm web → Container Deleted (gone forever)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.27 The Image-Container Analogy

A simple analogy that makes Docker concepts click:

```
┌─────────────────────────────────────────────────────────────┐
│              IMAGE = BLUEPRINT / RECIPE                      │
│              CONTAINER = HOUSE / DISH                        │
│                                                              │
│  ┌──────────────────┐                                       │
│  │   Blueprint       │ ← Docker Image                      │
│  │   (read-only)     │   (nginx:latest)                    │
│  │                   │                                       │
│  │   Contains:       │                                       │
│  │   • Floor plan    │   • OS files                         │
│  │   • Materials     │   • Libraries                        │
│  │   • Instructions  │   • Application code                 │
│  └────────┬──────────┘                                       │
│           │                                                  │
│     Build from blueprint                                    │
│     (docker run)                                            │
│           │                                                  │
│     ┌─────┼─────┐                                           │
│     │     │     │                                            │
│     ▼     ▼     ▼                                            │
│  ┌─────┐ ┌─────┐ ┌─────┐                                   │
│  │House│ │House│ │House│  ← Docker Containers              │
│  │  A  │ │  B  │ │  C  │   (running instances)             │
│  └─────┘ └─────┘ └─────┘                                   │
│                                                              │
│  • Multiple houses from one blueprint                       │
│  • Each house is independent                                │
│  • Painting one house doesn't change the blueprint          │
│  • Painting one house doesn't affect other houses           │
│  • Demolishing a house doesn't destroy the blueprint        │
│                                                              │
│  Same with Docker:                                          │
│  • Multiple containers from one image                       │
│  • Each container is independent                            │
│  • Changes in one container don't change the image          │
│  • Changes in one container don't affect other containers   │
│  • Removing a container doesn't destroy the image           │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating the analogy:**

```bash
# One image (blueprint)
$ docker images nginx
REPOSITORY   TAG       IMAGE ID       SIZE
nginx        latest    a6bd71f48f68   187MB

# Three containers (houses) from the same image
$ docker run -d --name house-a -p 8081:80 nginx
$ docker run -d --name house-b -p 8082:80 nginx
$ docker run -d --name house-c -p 8083:80 nginx

# Each is independent
$ docker exec house-a sh -c "echo 'Welcome to House A' > /usr/share/nginx/html/index.html"

# house-a shows custom page, house-b and house-c still show default
$ curl http://localhost:8081
Welcome to House A

$ curl http://localhost:8082
<!DOCTYPE html>... Welcome to nginx! ...

# Removing house-a doesn't affect house-b, house-c, or the image
$ docker rm -f house-a

$ docker ps
CONTAINER ID   IMAGE   NAMES
b2c3d4e5f6a1   nginx   house-b    ← Still running
c3d4e5f6a1b2   nginx   house-c    ← Still running

$ docker images nginx
REPOSITORY   TAG       IMAGE ID       SIZE
nginx        latest    a6bd71f48f68   187MB    ← Image still exists

# Clean up
$ docker rm -f house-b house-c
```

---

## 4.28 Full Container Management Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE CONTAINER MANAGEMENT WORKFLOW          │
│                                                              │
│  Docker Hub / Private Registry                              │
│           │                                                  │
│           │ (pull image if missing)                          │
│           ▼                                                  │
│         Image                                               │
│           │                                                  │
│           │ docker run                                       │
│           ▼                                                  │
│    Container Created                                        │
│           │                                                  │
│           │ start PID 1 (command)                            │
│           ▼                                                  │
│    Container Running ◄──────────── docker start             │
│     │     │     │                       ▲                   │
│     │     │     │                       │                   │
│     │     │     │                       │                   │
│     │     │     └── docker exec ──► run command inside      │
│     │     │         (safe shell)   (doesn't affect PID 1)   │
│     │     │                                                  │
│     │     └── docker logs ──► view STDOUT/STDERR            │
│     │         docker logs -f     (follow in real-time)      │
│     │                                                        │
│     │── docker cp ──► copy files in/out                     │
│     │                                                        │
│     │── docker stats ──► view CPU/RAM usage                 │
│     │                                                        │
│     │── docker attach ──► connect to PID 1 (risky!)        │
│     │                                                        │
│     ▼                                                        │
│  docker stop (or PID 1 exits on its own)                    │
│     │                                                        │
│     ▼                                                        │
│  Container Exited ──────────────────────┐                   │
│     │                                    │                   │
│     │ docker start ──► Running again     │                   │
│     │                                    │                   │
│     │ docker cp ──► copy files (works!)  │                   │
│     │                                    │                   │
│     ▼                                    │                   │
│  docker rm (only if stopped) ◄───────────┘                  │
│     │                                                        │
│     ▼                                                        │
│  Deleted (data lost unless volume used)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Quick Command Reference (This Segment)

```bash
# ─── CREATE ──────────────────────────────────────────────
docker run -it --name test00 centos /bin/bash       # Interactive
docker run -d --name test01 centos <long-command>   # Detached

# ─── INSPECT ────────────────────────────────────────────
docker ps                                            # Running only
docker ps -a                                         # All containers

# ─── LIFECYCLE ───────────────────────────────────────────
docker start test00                                  # Start stopped
docker stop test00                                   # Stop running
docker attach test00                                 # Attach to PID 1 (risky)

# ─── INTERACT ───────────────────────────────────────────
docker exec test01 ls /tmp                           # Run command
docker exec -it test01 /bin/bash                     # Safe shell

# ─── LOGS ────────────────────────────────────────────────
docker logs test01                                   # View all logs
docker logs -f test01                                # Follow live

# ─── FILES ───────────────────────────────────────────────
docker cp dummy test01:/tmp/                         # Host → container
docker cp test01:/tmp/dummy .                        # Container → host

# ─── ENVIRONMENT ─────────────────────────────────────────
docker run -e MYNAME=Adam -it centos bash            # Set env var
docker run -e APP_ENV=prod -e DB_HOST=10.0.0.5 ...  # Multiple vars

# ─── WORKING DIRECTORY ──────────────────────────────────
docker run -w /tmp -it centos bash                   # Start in /tmp

# ─── CLEANUP ────────────────────────────────────────────
docker rm test00                                     # Remove stopped
docker rm -f test01                                  # Force remove
```

---

## 4.29 What You Must Know Before Creating a Container

```
┌─────────────────────────────────────────────────────────────┐
│              CONTAINER CREATION CHECKLIST                     │
│                                                              │
│  Before running docker run, decide:                         │
│                                                              │
│  1. Which IMAGE to use?                                     │
│     → nginx, ubuntu, python:3.12-slim, etc.                 │
│                                                              │
│  2. Which REGISTRY and IMAGE TAG?                           │
│     → docker.io/library/nginx:1.25                          │
│     → Default registry: Docker Hub                          │
│     → Default tag: latest                                   │
│                                                              │
│  3. What STARTUP COMMAND to run?                            │
│     → Use image default, or override with custom command    │
│     → e.g., /bin/bash, python app.py, java -jar app.jar    │
│                                                              │
│  4. What PORTS to map?                                      │
│     → -p 8080:80 (host:container)                           │
│     → Must know what port the app listens on inside         │
│                                                              │
│  5. What VOLUMES to mount?                                  │
│     → -v /host/path:/container/path                         │
│     → For persistent data, config files, shared folders     │
│                                                              │
│  6. What is the CONTAINER NAME?                             │
│     → --name myapp                                          │
│     → Meaningful names for easy management                  │
│                                                              │
│  7. DETACHED or INTERACTIVE?                                │
│     → -d for background services (web servers, databases)   │
│     → -it for interactive work (debugging, exploration)     │
│                                                              │
│  8. Should it AUTO-REMOVE on stop?                          │
│     → --rm for temporary/throwaway containers               │
│                                                              │
│  9. What RESOURCES are needed?                              │
│     → --memory 512m --cpus 1.0                              │
│     → Prevents one container from consuming all resources   │
│                                                              │
│  10. What ENVIRONMENT VARIABLES?                            │
│      → -e KEY=VALUE or --env-file .env                      │
└─────────────────────────────────────────────────────────────┘
```

### Quick Reference: docker run Syntax

```bash
$ docker run \
    --name <container-name> \
    -it | -d \
    -p <HostPort>:<ContainerPort> \
    -v <HostDir>:<ContainerDir> \
    -e <KEY>=<VALUE> \
    --memory <limit> \
    --cpus <limit> \
    --rm \
    <image>:<tag> \
    <startup-command>
```

### Practical Examples

```bash
# Interactive Ubuntu
$ docker run -it ubuntu

# Named container with custom command
$ docker run --name test02 -it ubuntu echo "HI-ADAM"

# Detached with logging loop
$ docker run -d --name testd ubuntu /bin/sh -c "while true; do echo hello; sleep 8; done"

# Apache web server (auto-remove)
$ docker run --rm --name myapache -p 80:80 -d httpd

# Nginx on different port
$ docker run --rm --name mynginx -p 8081:80 -d nginx

# Jenkins CI server
$ docker run --rm --name myjenkins -p 8080:8080 -d jenkins/jenkins

# Volume mount
$ docker run --name c1 -it -v /tmp/host:/tmp/cont ubuntu /bin/bash

# Host network mode
$ docker run --net=host --name test -d nginx
```

---

## 4.30 Docker Events — Real-Time Event Stream

`docker events` streams real-time events from the Docker daemon. It shows container, image, volume, network, and daemon events as they happen.

```bash
# Stream all events (blocks and waits)
$ docker events

# In another terminal, run a container:
$ docker run --name test -d nginx

# Events output:
# 2025-01-15T10:00:00 container create abc123 (image=nginx, name=test)
# 2025-01-15T10:00:00 container attach abc123 (image=nginx, name=test)
# 2025-01-15T10:00:00 network connect def456 (container=abc123, name=bridge)
# 2025-01-15T10:00:01 container start abc123 (image=nginx, name=test)
```

### Filtering Events

```bash
# Filter by event type
$ docker events --filter type=container

# Filter by specific event
$ docker events --filter event=stop

# Filter by container name
$ docker events --filter container=web

# Filter by image
$ docker events --filter image=nginx

# Combine filters
$ docker events --filter type=container --filter event=die

# Show events from the last hour
$ docker events --since '1h'

# Show events between two timestamps
$ docker events --since '2025-01-15T09:00:00' --until '2025-01-15T10:00:00'
```

### Event Types

```
┌──────────────────────┬──────────────────────────────────────┐
│ Type                 │ Events                               │
├──────────────────────┼──────────────────────────────────────┤
│ container            │ create, start, stop, die, kill,      │
│                      │ pause, unpause, restart, attach,     │
│                      │ detach, exec_create, exec_start,     │
│                      │ destroy, oom, health_status           │
├──────────────────────┼──────────────────────────────────────┤
│ image                │ pull, push, tag, untag, delete,      │
│                      │ import, build                        │
├──────────────────────┼──────────────────────────────────────┤
│ volume               │ create, destroy, mount, unmount      │
├──────────────────────┼──────────────────────────────────────┤
│ network              │ create, connect, disconnect, destroy │
├──────────────────────┼──────────────────────────────────────┤
│ daemon               │ reload                               │
└──────────────────────┴──────────────────────────────────────┘
```

### Real-World Use Cases

```bash
# Monitor for OOM kills in production
$ docker events --filter event=oom

# Watch for container crashes
$ docker events --filter event=die --format '{{.Actor.Attributes.name}} died with exit {{.Actor.Attributes.exitCode}}'

# Audit who stopped containers
$ docker events --filter event=stop --format '{{json .}}'
```

---

## 4.31 Docker Wait — Block Until Container Stops

`docker wait` blocks until a container stops, then prints its exit code. Useful in scripts that need to wait for a container to finish.

```bash
# Start a container that runs for 5 seconds
$ docker run -d --name job alpine sleep 5

# Wait for it to finish (blocks until container exits)
$ docker wait job
# 0    ← exit code (0 = success)

# Wait for a container that fails
$ docker run -d --name failing alpine sh -c "exit 42"
$ docker wait failing
# 42   ← non-zero exit code
```

### Use in Scripts

```bash
#!/bin/bash
# Run a batch job and wait for completion

docker run -d --name etl-job myapp:1.0 python etl.py

exit_code=$(docker wait etl-job)

if [ "$exit_code" -eq 0 ]; then
    echo "ETL job completed successfully"
    docker logs etl-job > /var/log/etl-success.log
else
    echo "ETL job failed with exit code $exit_code"
    docker logs etl-job > /var/log/etl-failure.log
fi

docker rm etl-job
```

### Wait for Multiple Containers

```bash
# Wait for multiple containers simultaneously
$ docker wait container1 container2 container3
# 0
# 0
# 1
# Prints exit codes in order
```

---

## Module 4 Summary

- Containers have a lifecycle: Created → Running → Paused → Exited → Removed
- `docker ps` shows running containers; `docker ps -a` shows all (including stopped)
- `docker stop` sends SIGTERM then SIGKILL; `docker start` resumes a stopped container
- `docker start` reuses an existing container; `docker run` always creates a new one
- Use `docker start` then `docker attach` to get back into a stopped interactive container
- `--name` gives containers meaningful names instead of random ones
- Container ID is auto-generated and immutable; name is user-defined and changeable
- `docker run` combines create + start with many configuration options
- Key options: `-d`, `-p`, `-e`, `-v`, `-w`, `--name`, `--restart`, `--memory`, `--cpus`
- Default CMD comes from image metadata — override by appending a command
- Container runs one main process (PID 1) — when it exits, container stops
- bash keeps container alive (read-eval-print loop); echo exits immediately
- Detached mode (`-d`) needs a long-running command or the container stops immediately
- `docker logs` and `docker logs -f` view output of detached containers
- `docker logs` shows STDOUT/STDERR only — use `docker exec` to read log files
- `docker exec -it` creates a NEW process (safe); `docker attach` connects to PID 1 (risky)
- Never use `docker attach` on production containers — risk of killing PID 1
- `-e` passes environment variables; use `--env-file` for many variables
- `-w` sets the working directory inside the container
- `docker cp` copies files between host and container (works on stopped containers too)
- `docker rm` deletes a container and all its data — containers are ephemeral
- Data inside containers is lost on removal unless volumes are used
- `docker stats` monitors resource usage in real-time
- Resource limits (`--memory`, `--cpus`) set maximums, not reservations
- Exceeding memory limit triggers OOM kill (exit code 137)
- Image = blueprint (read-only); Container = house (running instance)
- Health checks monitor container application health
- Restart policies ensure containers recover from failures
- Before creating a container, decide: image, tag, ports, volumes, name, mode, resources, env vars
- `docker events` streams real-time daemon events — filter by type, event, container, or image
- `docker wait` blocks until a container stops and returns its exit code — useful in scripts
- `Ctrl+P, Ctrl+Q` detaches from an interactive container without stopping it

---

**Next Module: [Module 5 - Dockerfile Deep Dive](module-05-dockerfile.md)**
