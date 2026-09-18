# Module 8: Docker Volumes and Data Persistence

---

## 8.1 Why Volumes Exist — The Real Problem

### Containers Are Ephemeral

Containers are designed to be disposable. If you delete a container, everything inside its writable layer is gone — configs, data, logs, state, all of it.

But applications like Jenkins, databases, and web apps generate **important data** that must survive container restarts and removals:

```
┌─────────────────────────────────────────────────────────────┐
│              THE DATA PROBLEM                                │
│                                                              │
│  Jenkins stores critical data in:                           │
│  /var/jenkins_home/                                         │
│  ├── jobs/          ← build history, job configs            │
│  ├── plugins/       ← installed plugins                     │
│  ├── users/         ← user accounts                         │
│  ├── secrets/       ← credentials                           │
│  └── config.xml     ← global configuration                  │
│                                                              │
│  MySQL stores data in:                                      │
│  /var/lib/mysql/                                            │
│  ├── mydb/          ← your database files                   │
│  ├── ibdata1        ← InnoDB tablespace                     │
│  └── ib_logfile0    ← transaction logs                      │
│                                                              │
│  If container dies and you recreate WITHOUT volumes:        │
│  ❌ Jenkins: All jobs, plugins, configs → GONE              │
│  ❌ MySQL: All databases, tables, data → GONE               │
│                                                              │
│  You need a way to store data OUTSIDE the container         │
│  lifecycle → VOLUMES                                        │
└─────────────────────────────────────────────────────────────┘
```

### The Port Mapping Analogy

Volume mapping works like port mapping — it creates a bridge between the host and the container:

```
┌─────────────────────────────────────────────────────────────┐
│              PORT MAPPING vs VOLUME MAPPING                  │
│                                                              │
│  Port mapping:                                              │
│  -p HOST_PORT:CONTAINER_PORT                                │
│  Maps host network port ↔ container network port            │
│                                                              │
│  Volume mapping:                                            │
│  -v HOST_FOLDER:CONTAINER_FOLDER                            │
│  Maps host filesystem path ↔ container filesystem path      │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  Port example:                                              │
│  -p 8080:8080                                               │
│  Host port 8080 ←→ Container port 8080                      │
│                                                              │
│  Volume example:                                            │
│  -v /data/jenkins:/var/jenkins_home                         │
│  Host folder /data/jenkins ←→ Container folder              │
│                                /var/jenkins_home             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Volume Mapping Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Host Machine                     Container                 │
│  ┌──────────────────┐            ┌──────────────────┐      │
│  │                  │            │                  │      │
│  │ /data/jenkins/   │◄──────────►│ /var/jenkins_home│      │
│  │  ├── jobs/       │  (synced)  │  ├── jobs/       │      │
│  │  ├── plugins/    │            │  ├── plugins/    │      │
│  │  ├── users/      │            │  ├── users/      │      │
│  │  └── config.xml  │            │  └── config.xml  │      │
│  │                  │            │                  │      │
│  │  (persistent)    │            │  (app writes     │      │
│  │                  │            │   here)           │      │
│  └──────────────────┘            └──────────────────┘      │
│                                                              │
│  When Jenkins writes to /var/jenkins_home/jobs/...          │
│  you see it on the host at /data/jenkins/jobs/...           │
│                                                              │
│  If container is deleted → host folder STILL EXISTS         │
│  New container with same volume → data is restored          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Volumes Are Useful — Practical Use Cases

```
┌──────────────────────────────────────────────────────────────┐
│  Use Case                    │ How Volumes Help              │
├──────────────────────────────┼───────────────────────────────┤
│  Read logs without entering  │ Logs are on the host folder   │
│  the container               │ — open them directly, no      │
│                              │ docker exec needed            │
├──────────────────────────────┼───────────────────────────────┤
│  Log rotation / cleanup      │ Host can run cron jobs to     │
│                              │ compress/purge log files      │
│                              │ without touching the container│
├──────────────────────────────┼───────────────────────────────┤
│  Backups                     │ Backup the host folder using  │
│                              │ normal backup tools (rsync,   │
│                              │ tar, cloud backup agents)     │
├──────────────────────────────┼───────────────────────────────┤
│  Persist app state           │ Delete + recreate container   │
│                              │ without losing data           │
│                              │ (DB data, Jenkins jobs, etc.) │
├──────────────────────────────┼───────────────────────────────┤
│  Share data between          │ Multiple containers can mount │
│  containers                  │ the same volume               │
├──────────────────────────────┼───────────────────────────────┤
│  Development workflow        │ Mount source code from host   │
│                              │ → edit on host, changes       │
│                              │ appear in container instantly  │
└──────────────────────────────┴───────────────────────────────┘
```

### Quick Preview: Two Ways to Map Volumes

```bash
# ─── Option 1: Bind Mount (you choose the host path) ────
$ docker run -d \
    -p 8080:8080 \
    -v /data/jenkins:/var/jenkins_home \
    --name jenkins jenkins/jenkins:lts

# Host folder: /data/jenkins (you create and manage this)
# Container folder: /var/jenkins_home (where Jenkins writes)
# You can browse /data/jenkins on the host directly

# ─── Option 2: Named Volume (Docker manages the path) ───
$ docker volume create jenkins_data

$ docker run -d \
    -p 8080:8080 \
    -v jenkins_data:/var/jenkins_home \
    --name jenkins jenkins/jenkins:lts

# Docker stores data at: /var/lib/docker/volumes/jenkins_data/_data
# You don't manually manage the host folder path
# Docker handles permissions and lifecycle

# Check where Docker stored it:
$ docker volume inspect jenkins_data --format='{{.Mountpoint}}'
/var/lib/docker/volumes/jenkins_data/_data
```

Both options are covered in detail in the following sections.

---

## 8.2 The Problem Demonstrated: Data Loss Without Volumes

By default, all data inside a container is lost when the container is removed.

```bash
# Demonstration: Data loss without volumes
docker run -d --name temp-db postgres:16 -e POSTGRES_PASSWORD=secret

# Create some data
docker exec temp-db psql -U postgres -c "CREATE TABLE users (id serial, name text);"
docker exec temp-db psql -U postgres -c "INSERT INTO users (name) VALUES ('Alice'), ('Bob');"
docker exec temp-db psql -U postgres -c "SELECT * FROM users;"
# Output:
#  id | name
# ----+-------
#   1 | Alice
#   2 | Bob

# Remove and recreate the container
docker rm -f temp-db
docker run -d --name temp-db postgres:16 -e POSTGRES_PASSWORD=secret

# Data is GONE
docker exec temp-db psql -U postgres -c "SELECT * FROM users;"
# ERROR: relation "users" does not exist

docker rm -f temp-db
```

---

## 8.3 Three Types of Storage in Docker

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Storage Types                       │
│                                                              │
│  1. VOLUMES (Docker-managed)                                 │
│     Location: /var/lib/docker/volumes/                       │
│     Best for: Database data, persistent app data             │
│     ┌──────────┐     ┌──────────────────┐                   │
│     │Container │────▶│ /var/lib/docker/  │                   │
│     │ /data    │     │ volumes/mydata/   │                   │
│     └──────────┘     └──────────────────┘                   │
│                                                              │
│  2. BIND MOUNTS (Host directory)                             │
│     Location: Anywhere on host filesystem                    │
│     Best for: Source code (dev), config files                │
│     ┌──────────┐     ┌──────────────────┐                   │
│     │Container │────▶│ /home/user/      │                   │
│     │ /app/src │     │ project/src/     │                   │
│     └──────────┘     └──────────────────┘                   │
│                                                              │
│  3. TMPFS MOUNTS (Memory only)                               │
│     Location: Host memory (RAM)                              │
│     Best for: Secrets, temporary data                        │
│     ┌──────────┐     ┌──────────────────┐                   │
│     │Container │────▶│    RAM           │                   │
│     │ /tmp     │     │  (not on disk)   │                   │
│     └──────────┘     └──────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 8.4 Docker Volumes (Recommended for Persistence)

### Creating and Managing Volumes

```bash
# Create a named volume
docker volume create my-data

# Output:
# my-data

# MEANING: Docker creates a directory at /var/lib/docker/volumes/my-data/_data
# Docker manages this directory — you don't need to know the exact path.

# List all volumes
docker volume ls

# Output:
# DRIVER    VOLUME NAME
# local     my-data
# local     postgres-data
# local     redis-data

# Inspect a volume (see details)
docker volume inspect my-data

# Output:
# [
#     {
#         "CreatedAt": "2024-01-15T10:00:00Z",
#         "Driver": "local",
#         "Labels": {},
#         "Mountpoint": "/var/lib/docker/volumes/my-data/_data",
#         "Name": "my-data",
#         "Options": {},
#         "Scope": "local"
#     }
# ]

# Remove a volume
docker volume rm my-data

# Remove all unused volumes (DATA LOSS WARNING!)
docker volume prune

# Output:
# WARNING! This will remove all local volumes not used by at least one container.
# Are you sure you want to continue? [y/N] y
# Deleted Volumes:
# old-data
# temp-volume
# Total reclaimed space: 500MB
```

### Using Volumes with Containers

```bash
# Mount a named volume
docker run -d \
  --name my-postgres \
  -v postgres-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16

# Breakdown:
# -v postgres-data:/var/lib/postgresql/data
#    ├── postgres-data          → Volume name (created automatically if doesn't exist)
#    └── /var/lib/postgresql/data → Mount point inside container

# Create data
docker exec my-postgres psql -U postgres -c "CREATE TABLE test (id serial, value text);"
docker exec my-postgres psql -U postgres -c "INSERT INTO test (value) VALUES ('persistent!');"

# Remove the container
docker rm -f my-postgres

# Create a NEW container with the SAME volume
docker run -d \
  --name my-postgres-2 \
  -v postgres-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=secret \
  postgres:16

# Data survives!
docker exec my-postgres-2 psql -U postgres -c "SELECT * FROM test;"
# Output:
#  id |   value
# ----+------------
#   1 | persistent!

docker rm -f my-postgres-2
```

### Volume with --mount Syntax (More Explicit)

```bash
# --mount syntax (recommended for clarity)
docker run -d \
  --name my-app \
  --mount type=volume,source=app-data,target=/app/data \
  my-app:1.0

# Breakdown:
# type=volume     → Volume mount (Docker-managed)
# source=app-data → Volume name
# target=/app/data → Mount point in container

# Read-only volume
docker run -d \
  --name my-app \
  --mount type=volume,source=app-data,target=/app/data,readonly \
  my-app:1.0

# Comparison: -v vs --mount
# -v postgres-data:/var/lib/postgresql/data
# --mount type=volume,source=postgres-data,target=/var/lib/postgresql/data
# Both do the same thing. --mount is more explicit and less error-prone.
```

---

## 8.5 Bind Mounts (Host Directory Mapping)

Bind mounts map a specific host directory into the container.

```bash
# Bind mount: map host directory to container
docker run -d \
  --name dev-server \
  -v $(pwd)/src:/app/src \
  -p 3000:3000 \
  node:20-alpine npm start

# Breakdown:
# $(pwd)/src     → Absolute path on HOST (must be absolute!)
# /app/src       → Path inside CONTAINER
# Changes on host immediately appear in container (and vice versa)

# Read-only bind mount (container can't modify host files)
docker run -d \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx

# The :ro flag makes the mount read-only inside the container
```

### Bind Mount with --mount Syntax

```bash
docker run -d \
  --mount type=bind,source=$(pwd)/src,target=/app/src \
  my-app:1.0

# Key difference from volumes:
# --mount type=bind will ERROR if the source directory doesn't exist
# -v will silently CREATE the directory (which can cause bugs)
```

### Development Workflow with Bind Mounts

```bash
# Node.js development with live reload
docker run -d \
  --name dev-api \
  -v $(pwd):/app \
  -v /app/node_modules \
  -p 3000:3000 \
  -e NODE_ENV=development \
  node:20-alpine sh -c "cd /app && npm install && npx nodemon app.js"

# Breakdown:
# -v $(pwd):/app           → Mount entire project into container
# -v /app/node_modules     → Anonymous volume for node_modules
#                            (prevents host node_modules from overwriting container's)
# Changes to source files on host → nodemon detects → auto-restart

# Python development with live reload
docker run -d \
  --name dev-flask \
  -v $(pwd):/app \
  -p 5000:5000 \
  -e FLASK_ENV=development \
  python:3.11-slim sh -c "cd /app && pip install -r requirements.txt && flask run --host=0.0.0.0"
```

---

## 8.6 Two-Way Sharing — Host and Container Are Synced

Volume mapping is **not a copy** — it's a live mount. Changes flow in both directions:

```
┌─────────────────────────────────────────────────────────────┐
│              TWO-WAY SHARING (BIND MOUNT)                    │
│                                                              │
│  Host                              Container                │
│  /home/user/mydata/                /tmp/data/               │
│                                                              │
│  ┌──────────────┐    mount (live)  ┌──────────────┐         │
│  │ file1.txt    │◄───────────────►│ file1.txt    │         │
│  │ file2.txt    │                  │ file2.txt    │         │
│  └──────────────┘                  └──────────────┘         │
│                                                              │
│  If you create a file on the HOST:                          │
│  $ echo "from host" > /home/user/mydata/hostfile.txt        │
│  → It appears INSIDE the container at /tmp/data/hostfile.txt│
│                                                              │
│  If you create a file INSIDE the container:                 │
│  root@abc:/# echo "from container" > /tmp/data/cfile.txt    │
│  → It appears on the HOST at /home/user/mydata/cfile.txt    │
│                                                              │
│  This is NOT copying — it's the SAME filesystem location    │
│  being accessed from two different paths.                    │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Demo: Two-Way Sharing

```bash
# Step 1: Create a host directory with a file
$ mkdir -p /tmp/mydata
$ echo "hello from host" > /tmp/mydata/hostfile.txt

# Step 2: Run a container with volume mapping
$ docker run -it --name vol-test -v /tmp/mydata:/tmp/data ubuntu bash

# Step 3: Inside the container — verify host file is visible
root@abc123:/# ls /tmp/data/
hostfile.txt

root@abc123:/# cat /tmp/data/hostfile.txt
hello from host

# Step 4: Create a file INSIDE the container
root@abc123:/# echo "hello from container" > /tmp/data/containerfile.txt
root@abc123:/# exit

# Step 5: Back on the host — verify container's file is visible
$ ls /tmp/mydata/
containerfile.txt  hostfile.txt

$ cat /tmp/mydata/containerfile.txt
hello from container

# CONCLUSION: Both directions work. The volume is a shared mount point,
# not a copy operation.
```

### Why Two-Way Sharing Matters

```
┌──────────────────────────────────────────────────────────────┐
│  Scenario                        │ How Two-Way Helps         │
├──────────────────────────────────┼───────────────────────────┤
│  Development workflow            │ Edit code on host with    │
│                                  │ your IDE → changes appear │
│                                  │ in container instantly    │
├──────────────────────────────────┼───────────────────────────┤
│  Log monitoring                  │ App writes logs inside    │
│                                  │ container → you read them │
│                                  │ on host without exec      │
├──────────────────────────────────┼───────────────────────────┤
│  Config updates                  │ Edit config on host →     │
│                                  │ container picks it up     │
│                                  │ (may need restart)        │
├──────────────────────────────────┼───────────────────────────┤
│  Backup scripts                  │ Host cron job reads data  │
│                                  │ written by container      │
└──────────────────────────────────┴───────────────────────────┘
```

---

## 8.7 Volume Persistence — Data Survives Container Stop

When you stop a container, the volume data remains intact. When you start it again, the data is still there.

```bash
# Step 1: Run a container with a volume and create data
$ docker run -it --name persist-test -v /tmp/persist:/data ubuntu bash
root@abc123:/# echo "important data" > /data/myfile.txt
root@abc123:/# echo "config value=42" > /data/config.txt
root@abc123:/# ls /data/
config.txt  myfile.txt
root@abc123:/# exit

# Step 2: Container has stopped
$ docker ps -a --filter name=persist-test
# CONTAINER ID   IMAGE    STATUS                     NAMES
# abc123def456   ubuntu   Exited (0) 5 seconds ago   persist-test

# Step 3: Check host — data is still there
$ ls /tmp/persist/
config.txt  myfile.txt
$ cat /tmp/persist/myfile.txt
important data

# Step 4: Start the container again
$ docker start -i persist-test
root@abc123:/# cat /data/myfile.txt
important data
root@abc123:/# cat /data/config.txt
config value=42

# CONCLUSION: Stopping a container does NOT delete volume data.
# The data persists on the host filesystem.
```

---

## 8.8 Volume Persistence — Data Survives Container Deletion

Even if you **delete** the container entirely, the volume data remains on the host.

```bash
# Step 1: Create container with volume and add data
$ docker run -it --name delete-test -v /tmp/survive:/data ubuntu bash
root@abc123:/# echo "survive deletion" > /data/critical.txt
root@abc123:/# exit

# Step 2: DELETE the container
$ docker rm delete-test
delete-test

# Step 3: Container is gone
$ docker ps -a --filter name=delete-test
# CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty — container no longer exists)

# Step 4: But the data is STILL on the host
$ cat /tmp/survive/critical.txt
survive deletion

# Step 5: Create a NEW container with the SAME volume path
$ docker run -it --name new-container -v /tmp/survive:/data ubuntu bash
root@def456:/# cat /data/critical.txt
survive deletion

# CONCLUSION: Volume data lives on the HOST filesystem.
# Deleting a container only removes the container — not the host directory.
# This is the entire point of volumes: data independence from container lifecycle.
```

```
┌─────────────────────────────────────────────────────────────┐
│              VOLUME LIFECYCLE vs CONTAINER LIFECYCLE          │
│                                                              │
│  Container:  create ──► run ──► stop ──► rm (GONE)          │
│                                                              │
│  Volume:     create ──► mount ──► unmount ──► STILL EXISTS  │
│                                                              │
│  The volume outlives the container.                          │
│  You can attach it to any new container.                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 8.9 Multi-Container Volume Sharing — Same Host Directory

Multiple containers can mount the **same host directory** simultaneously. This enables data sharing between containers without networking.

```
┌─────────────────────────────────────────────────────────────┐
│              MULTI-CONTAINER VOLUME SHARING                  │
│                                                              │
│  Host Directory: /tmp/shared/                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Container A  │  │ Container B  │  │ Container C  │      │
│  │ /data ───────┼──┼─ /data ──────┼──┼─ /data       │      │
│  │ (writer)     │  │ (reader)     │  │ (backup)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│                    /tmp/shared/                              │
│                    (single source of truth)                  │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Demo: Two Containers Sharing a Volume

```bash
# Step 1: Create a shared directory on the host
$ mkdir -p /tmp/shared

# Step 2: Run Container A — writes data
$ docker run -d --name container-a \
    -v /tmp/shared:/data \
    ubuntu bash -c "while true; do date >> /data/log.txt; sleep 3; done"

# Step 3: Run Container B — reads the same data
$ docker run -it --name container-b \
    -v /tmp/shared:/data \
    ubuntu bash

# Inside Container B — see what Container A is writing
root@def456:/# tail -f /data/log.txt
Thu Feb 20 12:00:00 UTC 2025
Thu Feb 20 12:00:03 UTC 2025
Thu Feb 20 12:00:06 UTC 2025
# (new lines appear every 3 seconds — written by Container A)

# Step 4: Container B can also write
root@def456:/# echo "message from B" >> /data/log.txt
root@def456:/# exit

# Step 5: Verify on host
$ tail -3 /tmp/shared/log.txt
Thu Feb 20 12:00:06 UTC 2025
Thu Feb 20 12:00:09 UTC 2025
message from B

# Cleanup
$ docker rm -f container-a container-b
```

### Real-World Use Cases for Multi-Container Sharing

```bash
# Use Case 1: Web server + log processor
# Nginx writes access logs → Fluentd reads and ships them
$ docker run -d --name nginx \
    -v /data/logs:/var/log/nginx \
    -p 80:80 nginx

$ docker run -d --name log-shipper \
    -v /data/logs:/logs:ro \
    fluentd

# Use Case 2: App server + file processor
# App saves uploaded files → processor converts them
$ docker run -d --name app \
    -v /data/uploads:/app/uploads \
    my-web-app

$ docker run -d --name processor \
    -v /data/uploads:/input \
    -v /data/processed:/output \
    my-image-processor

# Use Case 3: Multiple app instances sharing config
$ docker run -d --name app-1 -v /etc/myapp:/config:ro my-app
$ docker run -d --name app-2 -v /etc/myapp:/config:ro my-app
$ docker run -d --name app-3 -v /etc/myapp:/config:ro my-app
# Update config once on host → all containers see the change
```

---

## 8.10 Docker Internal Storage — Where Docker Keeps Everything

Docker stores all its data under `/var/lib/docker/` on the host. Understanding this structure helps with debugging and disk management.

```
┌─────────────────────────────────────────────────────────────┐
│              /var/lib/docker/ — Docker's Home Directory       │
│                                                              │
│  /var/lib/docker/                                           │
│  ├── containers/          ← Container metadata + logs       │
│  │   ├── abc123.../       ← One directory per container     │
│  │   │   ├── config.v2.json  ← Container configuration     │
│  │   │   ├── hostconfig.json ← Host-specific config        │
│  │   │   └── abc123...-json.log ← Container logs           │
│  │   └── def456.../                                        │
│  │                                                          │
│  ├── image/               ← Image metadata and layers       │
│  │   └── overlay2/        ← Storage driver data             │
│  │       ├── imagedb/     ← Image database                  │
│  │       └── layerdb/     ← Layer database                  │
│  │                                                          │
│  ├── overlay2/            ← Actual layer filesystems        │
│  │   ├── abc123.../       ← Layer content (files)           │
│  │   └── def456.../                                        │
│  │                                                          │
│  ├── volumes/             ← Named volumes                   │
│  │   ├── my-data/                                          │
│  │   │   └── _data/      ← Actual volume data              │
│  │   └── postgres-data/                                    │
│  │       └── _data/                                        │
│  │                                                          │
│  ├── network/             ← Network configuration           │
│  ├── plugins/             ← Installed plugins               │
│  ├── tmp/                 ← Temporary files                 │
│  └── buildkit/            ← Build cache                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Exploring Docker's Internal Storage

```bash
# View the top-level structure (requires root/sudo)
$ sudo ls /var/lib/docker/
buildkit  containers  image  network  overlay2  plugins  runtimes  swarm  tmp  volumes

# See all container directories
$ sudo ls /var/lib/docker/containers/
abc123def456789...
def456abc789012...

# Each container has its own log file
$ sudo ls /var/lib/docker/containers/abc123*/
abc123...-json.log  config.v2.json  hostconfig.json  hostname  hosts  resolv.conf

# View container logs directly from the filesystem
$ sudo cat /var/lib/docker/containers/abc123*/*-json.log
{"log":"Server started on port 8080\n","stream":"stdout","time":"2025-02-20T12:00:00Z"}

# See named volume data
$ sudo ls /var/lib/docker/volumes/
my-data/  postgres-data/  redis-data/

$ sudo ls /var/lib/docker/volumes/my-data/_data/
file1.txt  file2.txt  config.json

# Check disk usage by Docker
$ docker system df
TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images          10      3        5.2GB     3.8GB (73%)
Containers      5       2        100MB     60MB (60%)
Local Volumes   8       3        2.1GB     1.5GB (71%)
Build Cache     15      0        500MB     500MB (100%)

# Detailed breakdown
$ docker system df -v
```

### Key Points About Docker Internal Storage

```
┌──────────────────────────────────────────────────────────────┐
│  Directory              │ What It Stores                     │
├─────────────────────────┼────────────────────────────────────┤
│  containers/            │ Container configs, logs, metadata  │
│                         │ One subdirectory per container     │
├─────────────────────────┼────────────────────────────────────┤
│  image/                 │ Image metadata (not the actual     │
│                         │ layer files — those are in         │
│                         │ overlay2/)                         │
├─────────────────────────┼────────────────────────────────────┤
│  overlay2/              │ Actual filesystem layers           │
│                         │ (the real files: /bin, /usr, etc.) │
├─────────────────────────┼────────────────────────────────────┤
│  volumes/               │ Named volume data                  │
│                         │ Each volume has a _data/ subdir    │
├─────────────────────────┼────────────────────────────────────┤
│  network/               │ Bridge, overlay network configs    │
├─────────────────────────┼────────────────────────────────────┤
│  buildkit/              │ Build cache from docker build      │
└─────────────────────────┴────────────────────────────────────┘

⚠️  WARNING: Never manually modify files under /var/lib/docker/
    Always use Docker CLI commands to manage containers, images, and volumes.
    Direct modification can corrupt Docker's internal state.
```

---

## 8.11 Volume Mapping Is Mounting, Not Copying

A common misconception: volume mapping does **not** copy files between host and container. It **mounts** the host directory into the container's filesystem — like plugging in a USB drive.

```
┌─────────────────────────────────────────────────────────────┐
│              MOUNT vs COPY vs SYMLINK                        │
│                                                              │
│  COPY (docker cp):                                          │
│  ┌──────┐  copy   ┌──────┐                                 │
│  │ Host │ ──────► │ Cont │   Two separate copies exist     │
│  │ file │         │ file │   Changes to one don't affect    │
│  └──────┘         └──────┘   the other                      │
│                                                              │
│  SYMLINK (ln -s):                                           │
│  ┌──────┐  link   ┌──────┐                                 │
│  │ Host │ ◄────── │ Link │   Link points to host file      │
│  │ file │         │      │   Only works within same         │
│  └──────┘         └──────┘   filesystem                     │
│                                                              │
│  MOUNT (volume -v):                                         │
│  ┌──────────────────────────┐                               │
│  │     Same filesystem      │   Host path and container     │
│  │     location             │   path are the SAME location  │
│  │                          │   accessed via different paths │
│  │  Host: /tmp/data/        │                               │
│  │  Cont: /app/data/        │   ← Same physical storage    │
│  └──────────────────────────┘                               │
│                                                              │
│  Volume mapping = kernel-level mount                        │
│  The container's /app/data IS the host's /tmp/data          │
│  There is only ONE copy of the data                         │
└─────────────────────────────────────────────────────────────┘
```

### Proof: It's a Mount, Not a Copy

```bash
# Step 1: Create a large file on the host
$ mkdir -p /tmp/mounttest
$ dd if=/dev/zero of=/tmp/mounttest/bigfile bs=1M count=100
# Created a 100MB file

# Step 2: Check disk usage BEFORE running container
$ df -h /tmp
Filesystem      Size  Used  Avail  Use%
/dev/sda1       50G   10G   40G    20%

# Step 3: Run container with volume mount
$ docker run -d --name mount-test -v /tmp/mounttest:/data ubuntu sleep infinity

# Step 4: Check disk usage AFTER — no change!
$ df -h /tmp
Filesystem      Size  Used  Avail  Use%
/dev/sda1       50G   10G   40G    20%

# If it were a COPY, disk usage would increase by 100MB.
# Since it's a MOUNT, no additional space is used.

# Step 5: Verify same inode (same physical file)
$ ls -i /tmp/mounttest/bigfile
1234567 /tmp/mounttest/bigfile

$ docker exec mount-test ls -i /data/bigfile
1234567 /data/bigfile
# Same inode number = same physical file on disk

$ docker rm -f mount-test
```

---

## 8.12 Automatic Volume Creation

If a volume doesn't exist when you reference it, Docker creates it automatically.

```bash
# This volume doesn't exist yet
$ docker volume ls
# DRIVER    VOLUME NAME
# (empty)

# Run container with a non-existent volume name
$ docker run -it -v newvolume:/data ubuntu bash
# Docker automatically creates "newvolume"

root@abc123:/# echo "auto-created" > /data/test.txt
root@abc123:/# exit

# Verify the volume was created
$ docker volume ls
# DRIVER    VOLUME NAME
# local     newvolume

$ docker volume inspect newvolume
# [
#     {
#         "CreatedAt": "2025-02-20T12:00:00Z",
#         "Driver": "local",
#         "Mountpoint": "/var/lib/docker/volumes/newvolume/_data",
#         "Name": "newvolume",
#         "Scope": "local"
#     }
# ]
```

---

## 8.13 Volume Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              VOLUME LIFECYCLE — FULL WORKFLOW                 │
│                                                              │
│  Step 1: Developer runs container with volume               │
│  docker run -v mydata:/data ubuntu                          │
│          │                                                   │
│          ▼                                                   │
│  Step 2: Docker attaches volume to container                │
│  (creates volume if it doesn't exist)                       │
│          │                                                   │
│          ▼                                                   │
│  Step 3: Container writes data to /data                     │
│  echo "important" > /data/file.txt                          │
│          │                                                   │
│          ▼                                                   │
│  Step 4: Data stored in volume                              │
│  (/var/lib/docker/volumes/mydata/_data/file.txt)            │
│          │                                                   │
│          ▼                                                   │
│  Step 5: Container stopped or deleted                       │
│  docker rm container_id                                     │
│          │                                                   │
│          ▼                                                   │
│  Step 6: Volume STILL EXISTS with all data                  │
│  docker volume ls → mydata still listed                     │
│          │                                                   │
│          ▼                                                   │
│  Step 7: New container uses same volume                     │
│  docker run -v mydata:/data ubuntu                          │
│  → All previous data is available                           │
│                                                              │
│  KEY: Volume lifecycle is INDEPENDENT of container lifecycle│
└─────────────────────────────────────────────────────────────┘
```

---

## 8.14 Real-World DevOps Use Cases — Applications Needing Volumes

```
┌──────────────────────────────────────────────────────────────┐
│  Application          │ Volume Mount Path          │ Why     │
├───────────────────────┼────────────────────────────┼─────────┤
│  MySQL                │ /var/lib/mysql              │ DB data │
│  PostgreSQL           │ /var/lib/postgresql/data    │ DB data │
│  MongoDB              │ /data/db                   │ DB data │
│  Jenkins              │ /var/jenkins_home           │ Jobs,   │
│                       │                            │ plugins │
│  Elasticsearch        │ /usr/share/elasticsearch/  │ Indices │
│                       │ data                       │         │
│  Redis                │ /data                      │ Persist │
│  Grafana              │ /var/lib/grafana            │ Dashbds │
│  Prometheus           │ /prometheus                │ Metrics │
│  GitLab               │ /var/opt/gitlab             │ Repos   │
│  Nginx                │ /etc/nginx/conf.d           │ Config  │
│                       │ /var/log/nginx              │ Logs    │
└───────────────────────┴────────────────────────────┴─────────┘
```

```bash
# MySQL with volume
$ docker run -d \
    -v mysqldata:/var/lib/mysql \
    -e MYSQL_ROOT_PASSWORD=secret \
    mysql

# PostgreSQL with volume
$ docker run -d \
    -v pgdata:/var/lib/postgresql/data \
    -e POSTGRES_PASSWORD=secret \
    postgres

# MongoDB with volume
$ docker run -d \
    -v mongodata:/data/db \
    mongo

# Jenkins with volume
$ docker run -d \
    -v jenkinsdata:/var/jenkins_home \
    -p 8080:8080 \
    jenkins/jenkins:lts

# Elasticsearch with volume
$ docker run -d \
    -v esdata:/usr/share/elasticsearch/data \
    -e "discovery.type=single-node" \
    elasticsearch:8.12.0

# All these applications REQUIRE volumes in production.
# Without volumes, restarting the container loses all data.
```

---

## 8.15 Volume Commands — Quick Reference

```bash
# ─── NAMED VOLUMES ──────────────────────────────────────────

# Create a named volume
$ docker volume create mydata

# List all volumes
$ docker volume ls

# Inspect a volume (see mountpoint, driver, labels)
$ docker volume inspect mydata

# Remove a specific volume
$ docker volume rm mydata

# Remove ALL unused volumes (not attached to any container)
$ docker volume prune

# Remove all unused volumes without confirmation
$ docker volume prune -f

# ─── USING VOLUMES WITH CONTAINERS ─────────────────────────

# Bind mount: host path to container path
$ docker run -v /host/path:/container/path image

# Named volume: Docker-managed storage
$ docker run -v volume-name:/container/path image

# Read-only mount
$ docker run -v /host/path:/container/path:ro image

# Multiple volumes on one container
$ docker run \
    -v /data/config:/app/config:ro \
    -v /data/logs:/app/logs \
    -v db-data:/app/data \
    my-app

# ─── INSPECTING VOLUME USAGE ───────────────────────────────

# See which volumes a container uses
$ docker inspect container-name --format='{{json .Mounts}}' | python3 -m json.tool

# Find containers using a specific volume
$ docker ps -a --filter volume=mydata

# Check total disk usage by volumes
$ docker system df
$ docker system df -v    # detailed per-volume breakdown

# ─── CLEANUP ───────────────────────────────────────────────

# Remove volume (must not be in use)
$ docker volume rm mydata

# Force remove container + its anonymous volumes
$ docker rm -v container-name

# Remove all stopped containers AND their anonymous volumes
$ docker container prune
$ docker volume prune

# Nuclear option: remove everything unused
$ docker system prune --volumes
# ⚠️  This removes: stopped containers, unused networks,
#     dangling images, AND all unused volumes
```

---

## 8.16 tmpfs Mounts (In-Memory Storage)

Data stored in RAM — fast, but lost when container stops.

```bash
# Create a tmpfs mount
docker run -d \
  --name secure-app \
  --tmpfs /tmp:rw,size=100m \
  --tmpfs /run/secrets:rw,size=1m \
  my-app:1.0

# Breakdown:
# --tmpfs /tmp:rw,size=100m
#   /tmp        → Mount point in container
#   rw          → Read-write
#   size=100m   → Maximum 100MB

# With --mount syntax
docker run -d \
  --mount type=tmpfs,target=/tmp,tmpfs-size=104857600 \
  my-app:1.0

# Use cases:
# - Temporary files that shouldn't persist
# - Sensitive data (secrets, tokens) that shouldn't be on disk
# - High-performance scratch space
```

---

## 8.17 Volume vs Bind Mount vs tmpfs — Comparison

```
┌──────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Feature      │ Volume           │ Bind Mount       │ tmpfs            │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Location     │ Docker-managed   │ Anywhere on host │ Host memory      │
│              │ /var/lib/docker/ │                  │ (RAM)            │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Persistence  │ ✅ Survives      │ ✅ On host disk  │ ❌ Lost on stop  │
│              │ container removal│                  │                  │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Portability  │ ✅ Works on any  │ ❌ Path-dependent│ ✅ No host deps  │
│              │ host             │                  │                  │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Performance  │ Good             │ Good (native)    │ Best (RAM)       │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Backup       │ docker volume    │ Standard file    │ ❌ Not possible  │
│              │ commands         │ backup tools     │                  │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Best For     │ Database data,   │ Source code,     │ Secrets,         │
│              │ app state        │ config files     │ temp files       │
├──────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Docker       │ ✅ Full control  │ ⚠️ Limited       │ ✅ Full control  │
│ Management   │                  │ (host-dependent) │                  │
└──────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## 8.18 Volume Backup and Restore

### Backup a Volume

```bash
# Method 1: Using a temporary container
docker run --rm \
  -v postgres-data:/source:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /source .

# Breakdown:
# --rm                          → Remove container after it exits
# -v postgres-data:/source:ro   → Mount the volume to backup (read-only)
# -v $(pwd):/backup             → Mount current directory for output
# tar czf ...                   → Create compressed archive

# Verify backup
ls -lh postgres-backup.tar.gz
# Output: -rw-r--r-- 1 user user 50M Jan 15 12:00 postgres-backup.tar.gz
```

### Restore a Volume

```bash
# Create a new volume
docker volume create postgres-data-restored

# Restore from backup
docker run --rm \
  -v postgres-data-restored:/target \
  -v $(pwd):/backup:ro \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /target

# Use the restored volume
docker run -d \
  --name restored-db \
  -v postgres-data-restored:/var/lib/postgresql/data \
  postgres:16
```

### Automated Backup Script

```bash
#!/bin/bash
# backup-volumes.sh

BACKUP_DIR="/backups/docker-volumes"
DATE=$(date +%Y%m%d_%H%M%S)

# List of volumes to backup
VOLUMES=("postgres-data" "redis-data" "app-uploads")

for VOLUME in "${VOLUMES[@]}"; do
  echo "Backing up $VOLUME..."
  docker run --rm \
    -v "$VOLUME":/source:ro \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/${VOLUME}_${DATE}.tar.gz" -C /source .
  echo "Done: ${VOLUME}_${DATE}.tar.gz"
done

# Clean up backups older than 7 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
echo "Cleanup complete."
```

---

## 8.19 Sharing Data Between Containers

### Using Named Volumes

```bash
# Container 1: Writes data
docker volume create shared-data

docker run -d \
  --name writer \
  -v shared-data:/data \
  alpine sh -c "while true; do date >> /data/log.txt; sleep 5; done"

# Container 2: Reads data
docker run -d \
  --name reader \
  -v shared-data:/data:ro \
  alpine sh -c "while true; do cat /data/log.txt; sleep 10; done"

# Both containers access the same volume
docker logs reader
# Output:
# Mon Jan 15 12:00:00 UTC 2024
# Mon Jan 15 12:00:05 UTC 2024
# Mon Jan 15 12:00:10 UTC 2024

docker rm -f writer reader
docker volume rm shared-data
```

### Using --volumes-from

```bash
# Container 1: Has volumes defined
docker run -d --name data-container \
  -v /app/data \
  -v /app/logs \
  alpine sleep infinity

# Container 2: Shares volumes from container 1
docker run -d --name app \
  --volumes-from data-container \
  my-app:1.0

# Container 3: Also shares the same volumes
docker run -d --name backup \
  --volumes-from data-container \
  alpine sh -c "tar czf /backup.tar.gz /app/data /app/logs"
```

---

## 8.20 Volume Drivers and Remote Storage

```bash
# Default: local driver (stores on host filesystem)
docker volume create --driver local my-volume

# NFS volume (network file system)
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.100,rw \
  --opt device=:/shared/data \
  nfs-volume

# Use in Docker Compose
# docker-compose.yml:
```

```yaml
volumes:
  nfs-data:
    driver: local
    driver_opts:
      type: nfs
      o: addr=192.168.1.100,rw,nfsvers=4
      device: ":/shared/data"

  # CIFS/SMB volume (Windows share)
  smb-data:
    driver: local
    driver_opts:
      type: cifs
      o: username=user,password=pass,addr=192.168.1.200
      device: "//192.168.1.200/shared"
```

---

## 8.21 Real-World Industry Example: Database with Automated Backups

```yaml
# docker-compose.yml — PostgreSQL with automated backups

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-app}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-appdb}
    volumes:
      # Persistent database storage
      - postgres-data:/var/lib/postgresql/data
      # Custom initialization scripts
      - ./database/init:/docker-entrypoint-initdb.d:ro
      # Custom PostgreSQL configuration
      - ./database/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-app} -d ${DB_NAME:-appdb}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
    networks:
      - backend

  # Automated backup service
  db-backup:
    image: postgres:16-alpine
    environment:
      PGHOST: db
      PGUSER: ${DB_USER:-app}
      PGPASSWORD: ${DB_PASSWORD}
      PGDATABASE: ${DB_NAME:-appdb}
    volumes:
      - db-backups:/backups
    # Run backup every 6 hours
    command: >
      sh -c 'while true; do
        FILENAME="/backups/backup_$$(date +%Y%m%d_%H%M%S).sql.gz"
        echo "Creating backup: $$FILENAME"
        pg_dump | gzip > "$$FILENAME"
        echo "Backup complete: $$(du -h $$FILENAME | cut -f1)"
        # Keep only last 7 days of backups
        find /backups -name "*.sql.gz" -mtime +7 -delete
        echo "Next backup in 6 hours..."
        sleep 21600
      done'
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend

  # Redis with persistence
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      - backend

  # Application
  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://${DB_USER:-app}:${DB_PASSWORD}@db:5432/${DB_NAME:-appdb}
      REDIS_URL: redis://redis:6379
    volumes:
      # User uploads persist across deployments
      - uploads:/app/uploads
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - frontend
      - backend

volumes:
  postgres-data:       # Database files
  redis-data:          # Redis AOF persistence
  db-backups:          # Database backup files
  uploads:             # User-uploaded files

networks:
  frontend:
  backend:
```

```bash
# Start everything
docker compose up -d

# Check backup status
docker compose logs db-backup

# Manual backup
docker compose exec db pg_dump -U app appdb > manual-backup.sql

# Restore from backup
docker compose exec -T db psql -U app appdb < manual-backup.sql

# Restore from compressed backup in volume
docker compose run --rm db-backup sh -c \
  'gunzip -c /backups/backup_20240115_120000.sql.gz | psql'

# Check volume sizes
docker system df -v | grep -A 20 "VOLUME NAME"
```

---

## 8.22 Common Errors and Troubleshooting

### Error 1: Permission Denied on Volume
```bash
$ docker run -v mydata:/app/data my-app
# Error: Permission denied: '/app/data/file.txt'

# CAUSE: Container user doesn't own the volume directory

# Fix Option 1: Set ownership in Dockerfile
RUN mkdir -p /app/data && chown -R 1000:1000 /app/data
USER 1000

# Fix Option 2: Use init container to fix permissions
docker run --rm -v mydata:/data alpine chown -R 1000:1000 /data

# Fix Option 3: Run as root (not recommended for production)
docker run --user root -v mydata:/app/data my-app
```

### Error 2: Volume Data Not Persisting
```bash
# CAUSE 1: Using anonymous volume (not named)
docker run -v /data my-app    # Anonymous — hard to reuse
# Fix: Use named volume
docker run -v my-data:/data my-app

# CAUSE 2: Wrong mount path
docker run -v my-data:/var/lib/mysql my-app
# But the app writes to /data/mysql
# Fix: Match the mount path to where the app writes

# CAUSE 3: docker compose down -v (removes volumes!)
docker compose down -v    # ← This deletes ALL volumes!
# Fix: Use docker compose down (without -v)
```

### Error 3: Bind Mount Shows Empty Directory
```bash
# CAUSE: Bind mount OVERRIDES the container directory
# If host directory is empty, container sees empty directory

docker run -v $(pwd)/empty-dir:/app node:20
# /app in container is now empty (even if image had files there)

# Fix: Only mount specific subdirectories
docker run -v $(pwd)/src:/app/src node:20
# /app still has its original files; only /app/src is overridden
```

### Error 4: "Volume is in use" When Trying to Remove
```bash
$ docker volume rm my-data
# Error: volume is in use - [container_id]

# Fix: Remove the container first
docker rm -f <container_id>
docker volume rm my-data

# Or find which containers use the volume
docker ps -a --filter volume=my-data
```

### Error 5: Disk Space Full from Volumes
```bash
# Check volume sizes
docker system df

# Output:
# TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Volumes         15      3        10.5GB    8.2GB (78%)

# Find large volumes
docker system df -v | grep -A 5 "VOLUME NAME"

# Remove unused volumes
docker volume prune

# Remove specific volume
docker volume rm old-unused-volume

# Find the actual data on host
sudo du -sh /var/lib/docker/volumes/*
```

### Error 6: Bind Mount Not Working on macOS/Windows
```bash
# CAUSE: Docker Desktop uses a VM; file sharing must be configured

# macOS Fix:
# Docker Desktop → Settings → Resources → File Sharing
# Add the directory you want to mount

# Windows Fix:
# Docker Desktop → Settings → Resources → File Sharing
# Share the drive containing your project

# Performance Fix (macOS):
# Bind mounts on macOS are slow due to file system translation
# Use :cached or :delegated flags:
docker run -v $(pwd)/src:/app/src:cached my-app
# :cached    → Host is authoritative (reads may be stale in container)
# :delegated → Container is authoritative (reads may be stale on host)
```

---

## 8.23 Real-World Example: Jenkins with Port Mapping + Volumes + Image Commit

This example combines three concepts: port mapping (Module 7), volume mapping, and image creation via `docker commit` (Module 3).

```
┌─────────────────────────────────────────────────────────────┐
│              JENKINS: COMPLETE DOCKER WORKFLOW                │
│                                                              │
│  Goal: Run Jenkins with persistent data, accessible from    │
│  browser, and save the configured state as a custom image.  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    HOST MACHINE                      │    │
│  │                                                      │    │
│  │  Browser ──► http://host-ip:9090                    │    │
│  │                    │                                 │    │
│  │                    │ Port Mapping: -p 9090:8080      │    │
│  │                    ▼                                 │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │           JENKINS CONTAINER                  │   │    │
│  │  │                                              │   │    │
│  │  │  Jenkins Web UI ← port 8080 (internal)       │   │    │
│  │  │                                              │   │    │
│  │  │  /var/jenkins_home/                          │   │    │
│  │  │  ├── jobs/        ← build configs            │   │    │
│  │  │  ├── plugins/     ← installed plugins        │   │    │
│  │  │  ├── users/       ← user accounts            │   │    │
│  │  │  └── config.xml   ← global config            │   │    │
│  │  │         │                                    │   │    │
│  │  └─────────┼────────────────────────────────────┘   │    │
│  │            │                                         │    │
│  │            │ Volume Mapping:                         │    │
│  │            │ -v /data/jenkins:/var/jenkins_home      │    │
│  │            ▼                                         │    │
│  │  /data/jenkins/  (HOST)                             │    │
│  │  ├── jobs/                                          │    │
│  │  ├── plugins/                                       │    │
│  │  ├── users/                                         │    │
│  │  └── config.xml                                     │    │
│  │  (Data persists even if container is deleted)       │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step: Jenkins Setup

```bash
# ─── Step 1: Create host directory for Jenkins data ─────────
$ mkdir -p /data/jenkins

# ─── Step 2: Run Jenkins with port mapping + volume ─────────
$ docker run -d \
    --name jenkins \
    -p 9090:8080 \
    -v /data/jenkins:/var/jenkins_home \
    jenkins/jenkins:lts

# Breakdown:
# -p 9090:8080                          → Access Jenkins at host:9090
# -v /data/jenkins:/var/jenkins_home    → Persist all Jenkins data
# jenkins/jenkins:lts                   → Official Jenkins LTS image

# ─── Step 3: Get initial admin password ─────────────────────
$ docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
# a1b2c3d4e5f6g7h8i9j0

# OR read it from the host (because of volume mapping):
$ cat /data/jenkins/secrets/initialAdminPassword
# a1b2c3d4e5f6g7h8i9j0

# ─── Step 4: Access Jenkins in browser ──────────────────────
# Open: http://<host-ip>:9090
# Enter the initial admin password
# Install suggested plugins
# Create admin user
# Configure Jenkins (add jobs, credentials, etc.)

# ─── Step 5: Verify data is on the host ─────────────────────
$ ls /data/jenkins/
config.xml  jobs/  plugins/  users/  secrets/  ...

# ─── Step 6: Test persistence — delete and recreate ─────────
$ docker rm -f jenkins

# Data is still on the host:
$ ls /data/jenkins/
config.xml  jobs/  plugins/  users/  secrets/  ...

# Recreate with same volume:
$ docker run -d \
    --name jenkins-new \
    -p 9090:8080 \
    -v /data/jenkins:/var/jenkins_home \
    jenkins/jenkins:lts

# Jenkins starts with ALL previous data intact:
# - All jobs restored
# - All plugins restored
# - All users restored
# - No setup wizard (already configured)

# ─── Step 7: Save configured Jenkins as a custom image ──────
$ docker commit \
    --author "DevOps Team" \
    --message "Jenkins with plugins and base config" \
    jenkins-new my-jenkins:1.0

$ docker images my-jenkins
# REPOSITORY    TAG   IMAGE ID       SIZE
# my-jenkins    1.0   abc123def456   800MB

# Now you can share this pre-configured Jenkins image with your team.
# They run it and get Jenkins with all plugins pre-installed.
```

---

## 8.24 Interview Key Points — Volumes

```
┌──────────────────────────────────────────────────────────────┐
│  VOLUME INTERVIEW QUESTIONS AND ANSWERS                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: Why do we need volumes in Docker?                       │
│  A: Containers are ephemeral — data inside is lost when     │
│     the container is removed. Volumes store data on the     │
│     host filesystem so it persists across container          │
│     restarts and deletions.                                  │
│                                                              │
│  Q: What is the difference between -v and --mount?          │
│  A: Both do the same thing. --mount is more explicit and    │
│     will error if the source doesn't exist (safer).         │
│     -v silently creates missing directories.                │
│                                                              │
│  Q: What happens to volume data when a container is deleted?│
│  A: Volume data remains on the host. Only the container     │
│     is removed. A new container can mount the same volume   │
│     and access the data.                                     │
│                                                              │
│  Q: What is the difference between a volume and a bind mount│
│  A: Volumes are managed by Docker (stored in                │
│     /var/lib/docker/volumes/). Bind mounts map any host     │
│     directory into the container. Volumes are more portable │
│     and Docker handles permissions.                          │
│                                                              │
│  Q: Can multiple containers share the same volume?          │
│  A: Yes. Multiple containers can mount the same named       │
│     volume or bind mount simultaneously. Use :ro for        │
│     read-only access where appropriate.                      │
│                                                              │
│  Q: Is volume mapping a copy operation?                     │
│  A: No. It's a kernel-level mount. The host path and        │
│     container path point to the same physical storage.      │
│     No data is duplicated.                                   │
│                                                              │
│  Q: Where does Docker store its data internally?            │
│  A: /var/lib/docker/ — with subdirectories for containers/  │
│     images/, volumes/, overlay2/ (layers), network/.        │
│                                                              │
│  Q: How do you backup a Docker volume?                      │
│  A: Run a temporary container that mounts the volume and    │
│     the backup destination, then use tar to create an       │
│     archive: docker run --rm -v mydata:/src:ro              │
│     -v $(pwd):/backup alpine tar czf /backup/bak.tar.gz     │
│     -C /src .                                                │
│                                                              │
│  Q: What is tmpfs and when would you use it?                │
│  A: tmpfs stores data in RAM (not on disk). Data is lost    │
│     when the container stops. Use for secrets, temporary    │
│     files, or high-performance scratch space.               │
│                                                              │
│  Q: What does docker compose down -v do?                    │
│  A: It stops and removes containers AND deletes all         │
│     associated named volumes. Use with caution — this       │
│     destroys persistent data.                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8.25 Final Summary Diagram — Port Mapping + Volumes + Image Commit

```
┌─────────────────────────────────────────────────────────────────────┐
│              DOCKER COMPLETE PICTURE                                  │
│              Port Mapping + Volume Mapping + Image Creation          │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                        HOST MACHINE                           │  │
│  │                                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │                     CONTAINER                           │  │  │
│  │  │                                                         │  │  │
│  │  │  ┌─────────────┐    ┌──────────────────────────────┐   │  │  │
│  │  │  │ App Process  │    │ /var/app_home/               │   │  │  │
│  │  │  │ (port 8080)  │    │ ├── data/                    │   │  │  │
│  │  │  │              │    │ ├── config/                   │   │  │  │
│  │  │  │              │    │ └── logs/                     │   │  │  │
│  │  │  └──────┬───────┘    └──────────┬───────────────────┘   │  │  │
│  │  │         │                       │                       │  │  │
│  │  └─────────┼───────────────────────┼───────────────────────┘  │  │
│  │            │                       │                           │  │
│  │            │ PORT MAPPING          │ VOLUME MAPPING            │  │
│  │            │ -p 9090:8080          │ -v /data/app:/var/app_home│  │
│  │            │                       │                           │  │
│  │            ▼                       ▼                           │  │
│  │  ┌─────────────────┐    ┌──────────────────────────────┐     │  │
│  │  │ Host Port 9090  │    │ /data/app/ (HOST)            │     │  │
│  │  │                 │    │ ├── data/   (persistent)     │     │  │
│  │  │ Browser access: │    │ ├── config/ (persistent)     │     │  │
│  │  │ http://ip:9090  │    │ └── logs/   (persistent)     │     │  │
│  │  └─────────────────┘    └──────────────────────────────┘     │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     IMAGE CREATION                            │  │
│  │                                                               │  │
│  │  Container (with changes)                                     │  │
│  │       │                                                       │  │
│  │       │ docker commit container-name my-app:1.0               │  │
│  │       ▼                                                       │  │
│  │  New Image: my-app:1.0                                        │  │
│  │  (includes all installed software + config + files)           │  │
│  │       │                                                       │  │
│  │       │ docker run my-app:1.0                                 │  │
│  │       ▼                                                       │  │
│  │  New Container (pre-configured, ready to use)                 │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  KEY COMMANDS:                                                       │
│  ─────────────                                                       │
│  docker run -d -p HOST:CONTAINER -v HOST_DIR:CONT_DIR image         │
│  docker commit container-name new-image:tag                          │
│  docker volume create/ls/inspect/rm/prune                            │
│  docker system df                                                    │
│                                                                      │
│  KEY CONCEPTS:                                                       │
│  ─────────────                                                       │
│  Port mapping  = network bridge (host port ↔ container port)        │
│  Volume mapping = filesystem mount (host dir ↔ container dir)       │
│  docker commit  = snapshot container → new image                     │
│  Volumes persist across container stop, restart, and deletion        │
│  Images are layered, read-only; containers add a writable layer      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module 8 Summary

- Containers are ephemeral — data inside is lost when the container is removed
- Volume mapping (`-v HOST:CONTAINER`) works like port mapping but for filesystems
- Apps like Jenkins, MySQL, PostgreSQL need volumes to persist state across restarts
- Volumes let you read logs, run backups, and manage data without entering the container
- **Two-way sharing**: Changes on host appear in container and vice versa — it's a live mount
- **Persistence**: Volume data survives container stop AND container deletion
- **Multi-container sharing**: Multiple containers can mount the same host directory simultaneously
- **Docker internal storage**: All Docker data lives under `/var/lib/docker/` — containers/, images/, volumes/, overlay2/
- **Volume mapping is mounting, not copying**: No data duplication; same inode, same physical storage
- **Volumes**: Docker-managed, best for databases and app state
- **Bind mounts**: Host directory mapping, best for development (live reload)
- **tmpfs**: In-memory, best for secrets and temporary data
- Use `--mount` syntax for clarity over `-v` shorthand
- **Automatic creation**: Docker auto-creates volumes if they don't exist when referenced
- **Volume lifecycle**: Independent of container lifecycle — volumes outlive containers
- **DevOps essentials**: MySQL, PostgreSQL, MongoDB, Jenkins, Elasticsearch all require volumes in production
- Named volumes survive container removal; anonymous volumes don't
- Backup volumes using temporary containers with tar
- Share data between containers using named volumes or `--volumes-from`
- `docker compose down -v` deletes volumes — use with caution
- Always match mount paths to where the application actually writes data
- Never manually modify files under `/var/lib/docker/` — use Docker CLI commands

---

**Next Module: [Module 9 - Industry-Standard Project](module-09-project.md)**
