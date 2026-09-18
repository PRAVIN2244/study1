# Module 2: Installation and Your First Container

---

## 2.1 Installing Docker

### Quick Install (Ubuntu — using docker.io package)

For learning and development, the simplest way to install Docker on Ubuntu:

```bash
# Step 1: Update package index
$ sudo apt update

# What this does:
# Updates Ubuntu's package index (list of available software).
# Does NOT install anything yet.

# Output:
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [119 kB]
...
Reading package lists... Done

# Step 2: Install Docker
$ sudo apt install docker.io -y

# What gets installed:
# • Docker daemon (dockerd) — the background service
# • Docker client (docker) — the CLI tool you type commands into
# • Container runtime dependencies (containerd, runc)

# Output:
Reading package lists... Done
Building dependency tree... Done
The following NEW packages will be installed:
  containerd docker.io runc
...
Setting up docker.io (24.0.7-0ubuntu2) ...
Created symlink /etc/systemd/system/multi-user.target.wants/docker.service

# Step 3: Verify Docker daemon is running
$ ps -ef | grep dockerd

# Output:
root     1234     1  0 10:00 ?        00:00:05 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
user     5678  4321  0 10:05 pts/0    00:00:00 grep --color=auto dockerd

# The first line confirms: Docker daemon is running as a background process.
# The second line is just your grep command itself (ignore it).

# Step 4: Test with docker info
$ docker info

# If daemon IS running — you'll see:
Server:
 Containers: 0
  Running: 0
  Paused: 0
  Stopped: 0
 Images: 0
 Server Version: 24.0.7
 Storage Driver: overlay2
 Cgroup Driver: systemd
 Kernel Version: 5.15.0-91-generic
 Operating System: Ubuntu 22.04.3 LTS
 Total Memory: 7.773GiB

# If daemon is NOT running — you'll see:
Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?

# Fix: Start the daemon
$ sudo systemctl start docker
$ sudo systemctl enable docker   # Start on boot

# Step 5: Add your user to docker group (avoid sudo for every command)
$ sudo usermod -aG docker $USER
$ newgrp docker

# Now you can run docker commands without sudo
$ docker --version
Docker version 24.0.7, build afdd53b
```

### Production Install (Ubuntu/Debian — Official Docker CE Repository)

For production environments, use the official Docker CE repository for the latest version:

```bash
# Step 1: Remove old versions (if any)
sudo apt-get remove docker docker-engine docker.io containerd runc

# Step 2: Update package index and install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Step 3: Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Step 4: Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Step 5: Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 6: Add your user to docker group (avoid sudo for every command)
sudo usermod -aG docker $USER
newgrp docker

# Step 7: Verify installation
docker --version
# Output: Docker version 27.x.x, build xxxxxxx
```

### Linux (CentOS/RHEL/Fedora)

```bash
# Step 1: Remove old versions
sudo yum remove docker docker-client docker-client-latest docker-common \
  docker-latest docker-latest-logrotate docker-logrotate docker-engine

# Step 2: Install prerequisites
sudo yum install -y yum-utils

# Step 3: Add Docker repository
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Step 4: Install Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Step 5: Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Step 6: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Step 7: Verify
docker --version
# Output: Docker version 27.x.x, build xxxxxxx
```

### macOS

```bash
# Option 1: Download Docker Desktop from https://www.docker.com/products/docker-desktop
# Install the .dmg file and follow the wizard

# Option 2: Using Homebrew
brew install --cask docker

# After installation, open Docker Desktop from Applications
# Wait for the whale icon in the menu bar to stop animating

# Verify:
docker --version
# Output: Docker version 27.x.x, build xxxxxxx
```

### Windows

```
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Run the installer
3. Enable WSL 2 when prompted (recommended)
4. Restart your computer
5. Open Docker Desktop
6. Open PowerShell or Command Prompt:

docker --version
# Output: Docker version 27.x.x, build xxxxxxx
```

---

## 2.2 Verifying Your Installation

Run these commands to confirm everything works:

```bash
# Command 1: Check Docker version (detailed)
docker version

# Output:
# Client:
#  Version:           27.3.1
#  API version:       1.47
#  Go version:        go1.22.7
#  OS/Arch:           linux/amd64
#
# Server:
#  Engine:
#   Version:          27.3.1
#   API version:      1.47
#   Go version:       go1.22.7
#   OS/Arch:          linux/amd64

# MEANING: Shows both client and server (daemon) versions.
# If "Server" section is missing, the daemon isn't running.
```

```bash
# Command 2: Check Docker system info
docker info

# Output (abbreviated):
# Containers: 0
#  Running: 0
#  Paused: 0
#  Stopped: 0
# Images: 0
# Server Version: 27.3.1
# Storage Driver: overlay2
# Docker Root Dir: /var/lib/docker
# CPUs: 4
# Total Memory: 7.764GiB

# MEANING: Shows system-wide information about Docker installation.
# Useful for debugging — shows storage driver, number of containers, etc.
```

```bash
# Command 3: Run the hello-world test container
docker run hello-world

# Output:
# Unable to find image 'hello-world:latest' locally
# latest: Pulling from library/hello-world
# 2db29710123e: Pull complete
# Digest: sha256:...
# Status: Downloaded newer image for hello-world:latest
#
# Hello from Docker!
# This message shows that your installation appears to be working correctly.
#
# To generate this message, Docker took the following steps:
#  1. The Docker client contacted the Docker daemon.
#  2. The Docker daemon pulled the "hello-world" image from Docker Hub.
#  3. The Docker daemon created a new container from that image.
#  4. The Docker daemon streamed that output to the Docker client.

# MEANING: This confirms the entire Docker pipeline works:
# Client → Daemon → Registry → Image Pull → Container Run → Output
```

---

## 2.3 Your First Container - Step by Step

### Running an Nginx Web Server

```bash
# Command: Run an Nginx container
docker run -d -p 8080:80 --name my-first-website nginx

# Let's break down every flag:
#
# docker run     → Create and start a new container
# -d             → Detached mode (runs in background, returns control to terminal)
# -p 8080:80     → Port mapping: HOST_PORT:CONTAINER_PORT
#                  Access container's port 80 via host's port 8080
# --name         → Give the container a human-readable name
# my-first-website → The name we chose
# nginx          → The image to use (pulled from Docker Hub if not local)

# Output:
# Unable to find image 'nginx:latest' locally
# latest: Pulling from library/nginx
# a2abf6c4d29d: Pull complete
# ...
# Digest: sha256:...
# Status: Downloaded newer image for nginx:latest
# 7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b

# The long string is the CONTAINER ID.
# Nginx is now running! Visit http://localhost:8080 in your browser.
```

### Verifying the Container is Running

```bash
# Command: List running containers
docker ps

# Output:
# CONTAINER ID   IMAGE   COMMAND                  CREATED          STATUS          PORTS                  NAMES
# 7a8b9c0d1e2f   nginx   "/docker-entrypoint.…"   30 seconds ago   Up 29 seconds   0.0.0.0:8080->80/tcp   my-first-website

# Column meanings:
# CONTAINER ID  → Unique identifier (short form)
# IMAGE         → Image the container was created from
# COMMAND       → The command running inside the container
# CREATED       → When the container was created
# STATUS        → Current state (Up, Exited, etc.)
# PORTS         → Port mappings (host → container)
# NAMES         → Human-readable name
```

### Accessing the Container

```bash
# Command: Open a shell inside the running container
docker exec -it my-first-website bash

# Flags:
# -i  → Interactive (keep STDIN open)
# -t  → Allocate a pseudo-TTY (terminal)
# bash → The command to run inside the container

# You're now INSIDE the container:
root@7a8b9c0d1e2f:/# ls /usr/share/nginx/html/
# 50x.html  index.html

root@7a8b9c0d1e2f:/# cat /etc/nginx/nginx.conf
# ... nginx configuration ...

root@7a8b9c0d1e2f:/# exit
# Back to your host machine
```

### Viewing Container Logs

```bash
# Command: View container logs
docker logs my-first-website

# Output:
# /docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
# /docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
# ...
# 2024/01/15 10:30:00 [notice] 1#1: nginx/1.25.3
# 2024/01/15 10:30:00 [notice] 1#1: built by gcc 12.2.0
# 172.17.0.1 - - [15/Jan/2024:10:30:15 +0000] "GET / HTTP/1.1" 200 615

# MEANING: Shows stdout/stderr from the container process.
# The last line shows an HTTP request — someone visited the page.
```

```bash
# Command: Follow logs in real-time (like tail -f)
docker logs -f my-first-website

# Flags:
# -f  → Follow log output (stream new logs as they appear)
# Press Ctrl+C to stop following

# Command: Show last N lines
docker logs --tail 10 my-first-website

# Command: Show logs with timestamps
docker logs -t my-first-website
```

### Stopping and Removing the Container

```bash
# Command: Stop a running container
docker stop my-first-website

# Output:
# my-first-website

# MEANING: Sends SIGTERM to the main process, waits 10 seconds,
# then sends SIGKILL if still running. Container moves to "Exited" state.

# Command: List ALL containers (including stopped)
docker ps -a

# Output:
# CONTAINER ID   IMAGE   COMMAND                  CREATED         STATUS                     NAMES
# 7a8b9c0d1e2f   nginx   "/docker-entrypoint.…"   5 minutes ago   Exited (0) 10 seconds ago  my-first-website

# Note: STATUS changed from "Up" to "Exited (0)"
# Exit code 0 means clean shutdown

# Command: Start a stopped container
docker start my-first-website

# Output:
# my-first-website
# Container is running again with the same configuration

# Command: Restart a container (stop + start)
docker restart my-first-website

# Command: Remove a stopped container
docker stop my-first-website
docker rm my-first-website

# Output:
# my-first-website

# Command: Force remove a running container (stop + remove in one step)
docker rm -f my-first-website

# Flag:
# -f  → Force: stops the container first, then removes it
```

---

## 2.4 Running a Container in Interactive Mode (-it)

Interactive mode lets you get a shell inside a container, as if you were logged into a separate machine.

### Starting an Interactive Container

```bash
# Run CentOS interactively
$ docker run -it centos

# Breakdown:
# -i  → Interactive: keeps STDIN open (you can type)
# -t  → TTY: allocates a pseudo-terminal (you see a prompt)
# centos → Image name (pulled from Docker Hub if not local)
```

**What happens step by step:**

```bash
# If image is NOT present locally, Docker pulls it first:
Unable to find image 'centos:latest' locally
latest: Pulling from library/centos
a1d0c7532777: Pull complete
Digest: sha256:a27fd8080b517143cbbbab9dfb7c8571c40d67d534bbdee55bd6c473f432b177
Status: Downloaded newer image for centos:latest

# Then you get a shell prompt INSIDE the container:
[root@f8c3d5c6e7a1 /]#

# You are now inside the container!
# "f8c3d5c6e7a1" is the container ID
# "root" is the user
```

### Confirming You Are Inside the Container

```bash
# Check the hostname — it's the container ID, not your host machine
[root@f8c3d5c6e7a1 /]# hostname
f8c3d5c6e7a1

# Check the OS — it's CentOS, even if your host is Ubuntu!
[root@f8c3d5c6e7a1 /]# cat /etc/os-release
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"

# This proves:
# • Container OS environment is CentOS
# • Host OS is Ubuntu (or whatever you're running)
# • They are completely different environments
```

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Host Machine                    Container                  │
│  ┌──────────────────┐           ┌──────────────────┐       │
│  │ Ubuntu 22.04     │           │ CentOS 7         │       │
│  │ hostname: mypc   │           │ hostname: f8c3d5 │       │
│  │ Python 3.11      │           │ Python 2.7       │       │
│  │ /home/user/...   │           │ /root/...        │       │
│  └──────────────────┘           └──────────────────┘       │
│                                                              │
│  Different OS, different hostname, different filesystem     │
│  But sharing the SAME Linux kernel                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Container Filesystem Isolation

Files created inside a container are NOT visible on the host, and vice versa.

```bash
# INSIDE the container — create a file
[root@f8c3d5c6e7a1 /]# cd /tmp
[root@f8c3d5c6e7a1 tmp]# touch testfile
[root@f8c3d5c6e7a1 tmp]# echo "hello from container" > testfile
[root@f8c3d5c6e7a1 tmp]# ls /tmp
testfile
```

```bash
# Open ANOTHER terminal on the HOST machine — check /tmp
$ ls /tmp
systemd-private-xxx
snap-private-xxx
# "testfile" is NOT here!
```

```
┌─────────────────────────────────────────────────────────────┐
│              FILESYSTEM ISOLATION                            │
│                                                              │
│  Host Machine Filesystem:          Container Filesystem:    │
│  ┌──────────────────────┐         ┌──────────────────────┐ │
│  │ /tmp                 │         │ /tmp                 │ │
│  │   ├── file1          │         │   └── testfile ✅    │ │
│  │   ├── file2          │         │                      │ │
│  │   └── (no testfile)  │         │ /home                │ │
│  │                      │         │ /etc                 │ │
│  │ /home/user           │         │   └── os-release     │ │
│  │   └── documents/     │         │       (CentOS)       │ │
│  └──────────────────────┘         └──────────────────────┘ │
│                                                              │
│  They are COMPLETELY ISOLATED filesystems.                   │
│  Container has its own writable layer on top of the image.  │
│  Changes inside the container don't affect the host.        │
│  Changes on the host don't affect the container.            │
└─────────────────────────────────────────────────────────────┘
```

### Exiting a Container

```bash
# Type 'exit' to leave the container
[root@f8c3d5c6e7a1 /]# exit
exit

# You return to your host machine prompt
user@mypc:~$

# What happened to the container?
$ docker ps
CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty — no running containers)

$ docker ps -a
CONTAINER ID   IMAGE    COMMAND       CREATED          STATUS                     NAMES
f8c3d5c6e7a1   centos   "/bin/bash"   5 minutes ago    Exited (0) 10 seconds ago  quirky_einstein

# The container STOPPED when you exited
# Because the main process (/bin/bash) ended
# Exit code 0 = clean exit
```

### Every `docker run` Creates a NEW Container

This is a fundamental concept. Even with the same image, each `docker run` creates a brand new, independent container.

```bash
# Run centos — first time
$ docker run -it centos
[root@aaa111bbb222 /]# touch /tmp/file_from_first_container
[root@aaa111bbb222 /]# exit

# Run centos — second time
$ docker run -it centos
[root@ccc333ddd444 /]# ls /tmp
# (empty! — file_from_first_container is NOT here)
[root@ccc333ddd444 /]# exit

# Check all containers
$ docker ps -a

CONTAINER ID   IMAGE    COMMAND       CREATED          STATUS                      NAMES
ccc333ddd444   centos   "/bin/bash"   30 seconds ago   Exited (0) 5 seconds ago    happy_morse
aaa111bbb222   centos   "/bin/bash"   2 minutes ago    Exited (0) 1 minute ago     quirky_einstein

# Two DIFFERENT containers from the SAME image
# Different container IDs
# Different names
# Different writable layers (file_from_first_container only exists in aaa111)
```

```
┌─────────────────────────────────────────────────────────────┐
│              EVERY docker run = NEW CONTAINER                │
│                                                              │
│  docker run -it centos  ──→  Container aaa111 (new)         │
│  docker run -it centos  ──→  Container ccc333 (new)         │
│  docker run -it centos  ──→  Container eee555 (new)         │
│                                                              │
│  Same image, but:                                           │
│  • Different container IDs                                  │
│  • Different writable layers                                │
│  • Different filesystems                                    │
│  • Independent of each other                                │
│                                                              │
│  To REUSE an existing container:                            │
│  docker start <container_id>    ← starts a stopped one     │
│  docker attach <container_id>   ← attaches your terminal   │
│                                                              │
│  To create a NEW one:                                       │
│  docker run <image>             ← always creates new       │
└─────────────────────────────────────────────────────────────┘
```

**Reusing a stopped container instead of creating a new one:**

```bash
# Start the stopped container (doesn't create a new one)
$ docker start aaa111bbb222
aaa111bbb222

# Attach your terminal to it
$ docker attach aaa111bbb222
[root@aaa111bbb222 /]#

# The file we created earlier is still there!
[root@aaa111bbb222 /]# ls /tmp
file_from_first_container

# Because we restarted the SAME container, not a new one
```

---

## 2.5 Essential Docker Commands Reference

### Image Commands

```bash
# Pull an image from Docker Hub
docker pull <image>:<tag>
docker pull nginx:1.25
docker pull python:3.11-slim
docker pull node:20-alpine

# MEANING: Downloads the image to your local machine.
# If no tag specified, "latest" is used.

# Output:
# 1.25: Pulling from library/nginx
# a2abf6c4d29d: Pull complete
# ...
# Digest: sha256:abc123...
# Status: Downloaded newer image for nginx:1.25

# List all local images
docker images

# Output:
# REPOSITORY   TAG          IMAGE ID       CREATED        SIZE
# nginx        1.25         a6bd71f48f68   2 weeks ago    187MB
# python       3.11-slim    f3b7a8c9d0e1   3 weeks ago    131MB
# node         20-alpine    b2c3d4e5f6a7   1 week ago     181MB

# MEANING: Shows all images stored locally.
# SIZE is the uncompressed size on disk.

# Remove an image
docker rmi nginx:1.25

# Output:
# Untagged: nginx:1.25
# Deleted: sha256:a6bd71f48f68...

# MEANING: Removes the image from local storage.
# Fails if a container (even stopped) is using it.

# Force remove an image
docker rmi -f nginx:1.25

# Remove all unused images (not referenced by any container)
docker image prune

# Remove ALL images (including ones used by stopped containers)
docker image prune -a
```

### Container Commands

```bash
# Run a container in foreground (see output directly)
docker run nginx
# Press Ctrl+C to stop

# Run in background (detached)
docker run -d nginx

# Run with a custom name
docker run -d --name webserver nginx

# Run with port mapping
docker run -d -p 8080:80 nginx
# Access at http://localhost:8080

# Run with multiple port mappings
docker run -d -p 8080:80 -p 8443:443 nginx

# Run with environment variables
docker run -d -e MYSQL_ROOT_PASSWORD=secret mysql:8
# -e sets an environment variable inside the container

# Run with multiple environment variables
docker run -d \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=myapp \
  postgres:16

# Run and automatically remove container when it stops
docker run --rm nginx echo "Hello"
# --rm: Container is deleted after it exits
# Useful for one-off commands

# Run with resource limits
docker run -d --memory=256m --cpus=0.5 nginx
# --memory=256m: Limit to 256 MB RAM
# --cpus=0.5: Limit to half a CPU core
```

### Inspection Commands

```bash
# View detailed container information
docker inspect my-first-website

# Output (JSON, abbreviated):
# [
#     {
#         "Id": "7a8b9c0d1e2f...",
#         "State": {
#             "Status": "running",
#             "Pid": 12345
#         },
#         "NetworkSettings": {
#             "IPAddress": "172.17.0.2",
#             "Ports": {
#                 "80/tcp": [{"HostPort": "8080"}]
#             }
#         }
#     }
# ]

# MEANING: Complete JSON dump of container configuration.
# Useful for debugging network issues, finding IP addresses, etc.

# Get specific field using Go template
docker inspect --format='{{.NetworkSettings.IPAddress}}' my-first-website
# Output: 172.17.0.2

# View container resource usage (live)
docker stats

# Output:
# CONTAINER ID   NAME              CPU %   MEM USAGE / LIMIT     MEM %   NET I/O          BLOCK I/O
# 7a8b9c0d1e2f   my-first-website  0.00%   3.441MiB / 7.764GiB   0.04%   1.45kB / 0B      0B / 0B

# MEANING: Real-time resource monitoring (like top for containers).
# Press Ctrl+C to exit.

# View resource usage for specific container (non-streaming)
docker stats --no-stream my-first-website

# View processes running inside a container
docker top my-first-website

# Output:
# UID    PID    PPID   CMD
# root   12345  12344  nginx: master process
# 101    12346  12345  nginx: worker process

# MEANING: Shows processes without entering the container.
```

### Cleanup Commands

```bash
# Remove all stopped containers
docker container prune

# Output:
# WARNING! This will remove all stopped containers.
# Are you sure you want to continue? [y/N] y
# Deleted Containers:
# 7a8b9c0d1e2f...
# Total reclaimed space: 5.2MB

# Remove all unused data (containers, images, networks, cache)
docker system prune

# Nuclear option: remove EVERYTHING unused
docker system prune -a --volumes

# Flags:
# -a        → Remove all unused images, not just dangling ones
# --volumes → Also remove unused volumes (DATA LOSS WARNING)

# Check disk usage
docker system df

# Output:
# TYPE            TOTAL   ACTIVE   SIZE      RECLAIMABLE
# Images          5       2        1.234GB   800MB (64%)
# Containers      3       1        50MB      45MB (90%)
# Local Volumes   2       1        200MB     100MB (50%)
# Build Cache     10      0        500MB     500MB (100%)

# MEANING: Shows how much disk space Docker is using.
# RECLAIMABLE shows what can be freed with prune commands.
```

---

## 2.6 Practical Exercise: Running a Full Application Stack

Let's run a real application — a WordPress blog with MySQL database:

```bash
# Step 1: Create a network for the containers to communicate
docker network create wordpress-net

# Step 2: Run MySQL database
docker run -d \
  --name wordpress-db \
  --network wordpress-net \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=wordpress \
  -e MYSQL_USER=wpuser \
  -e MYSQL_PASSWORD=wppassword \
  -v wordpress-db-data:/var/lib/mysql \
  mysql:8.0

# Flags explained:
# --network wordpress-net  → Connect to our custom network
# -e MYSQL_ROOT_PASSWORD   → Set root password (required)
# -e MYSQL_DATABASE        → Create this database on startup
# -e MYSQL_USER            → Create this user on startup
# -e MYSQL_PASSWORD        → Set password for the new user
# -v wordpress-db-data:/var/lib/mysql → Persist data in a named volume

# Step 3: Run WordPress
docker run -d \
  --name wordpress-app \
  --network wordpress-net \
  -p 8080:80 \
  -e WORDPRESS_DB_HOST=wordpress-db \
  -e WORDPRESS_DB_USER=wpuser \
  -e WORDPRESS_DB_PASSWORD=wppassword \
  -e WORDPRESS_DB_NAME=wordpress \
  wordpress:latest

# MEANING: WordPress connects to MySQL using the container name
# "wordpress-db" as the hostname (Docker DNS resolves it).

# Step 4: Visit http://localhost:8080 — WordPress setup page!

# Step 5: Cleanup when done
docker rm -f wordpress-app wordpress-db
docker network rm wordpress-net
docker volume rm wordpress-db-data
```

---

## 2.7 Common Errors and Troubleshooting

### Error 1: Port Already in Use
```bash
$ docker run -d -p 8080:80 nginx
# Error: Bind for 0.0.0.0:8080 failed: port is already allocated

# CAUSE: Another process (or container) is using port 8080

# Fix Option 1: Use a different port
docker run -d -p 8081:80 nginx

# Fix Option 2: Find and stop what's using the port
sudo lsof -i :8080          # Linux/Mac
netstat -ano | findstr 8080  # Windows

# Fix Option 3: Stop the container using that port
docker ps | grep 8080
docker stop <container_id>
```

### Error 2: Image Not Found
```bash
$ docker run myapp:latest
# Error: Unable to find image 'myapp:latest' locally
# Error response from daemon: pull access denied for myapp

# CAUSE: Image doesn't exist on Docker Hub, or it's private

# Fix: Check the image name and tag
docker search myapp          # Search Docker Hub
docker pull myapp:v1.0       # Try a specific tag

# For private registries:
docker login registry.example.com
docker pull registry.example.com/myapp:latest
```

### Error 3: Container Exits Immediately
```bash
$ docker run -d ubuntu
$ docker ps
# (nothing shown — container exited)

$ docker ps -a
# STATUS: Exited (0) 2 seconds ago

# CAUSE: Container's main process finished immediately.
# Ubuntu image's default command is "bash", which exits
# when there's no terminal attached.

# Fix Option 1: Run with interactive terminal
docker run -it ubuntu bash

# Fix Option 2: Run a long-lived process
docker run -d ubuntu sleep infinity

# Fix Option 3: Run a proper service
docker run -d ubuntu tail -f /dev/null
```

### Error 4: Cannot Remove Image (In Use)
```bash
$ docker rmi nginx
# Error: conflict: unable to remove repository reference "nginx"
# (must force) - container abc123 is using its referenced image

# CAUSE: A container (even stopped) is using this image

# Fix: Remove the container first, then the image
docker rm abc123
docker rmi nginx

# Or force remove (removes image even if containers reference it)
docker rmi -f nginx
```

### Error 5: No Space Left on Device
```bash
$ docker pull large-image
# Error: write /var/lib/docker/...: no space left on device

# CAUSE: Docker's storage directory is full

# Fix Step 1: Check Docker disk usage
docker system df

# Fix Step 2: Clean up unused resources
docker system prune -a

# Fix Step 3: If still full, check host disk
df -h /var/lib/docker

# Fix Step 4: Move Docker's data directory (if needed)
# Edit /etc/docker/daemon.json:
# { "data-root": "/new/path/docker" }
# sudo systemctl restart docker
```

### Error 6: DNS Resolution Failure Inside Container
```bash
$ docker run -it ubuntu bash
root@abc123:/# apt-get update
# Err:1 http://archive.ubuntu.com/ubuntu focal InRelease
# Temporary failure resolving 'archive.ubuntu.com'

# CAUSE: Container can't resolve DNS

# Fix Option 1: Use Google DNS
docker run --dns 8.8.8.8 -it ubuntu bash

# Fix Option 2: Configure Docker daemon DNS
# Edit /etc/docker/daemon.json:
# { "dns": ["8.8.8.8", "8.8.4.4"] }
# sudo systemctl restart docker
```

### Error 7: Docker Desktop on Mac — osxkeychain Error

```bash
# Error when pushing/pulling images:
# "error getting credentials - err: exec: "docker-credential-osxkeychain": 
#  executable file not found in $PATH"

# CAUSE: Docker Desktop stores login credentials in macOS Keychain
# but the credential helper is missing or misconfigured.
```

**Fix — Step 1: Docker Desktop settings**

```
Open Docker Desktop → Preferences (Settings)
Uncheck: "Securely store Docker logins in macOS keychain"
```

**Fix — Step 2: Edit config.json**

```bash
# Open the Docker config file:
$ nano ~/.docker/config.json

# Remove this line:
#   "credsStore" : "osxkeychain"

# Save and exit
```

```
┌─────────────────────────────────────────────────────────────┐
│  Before fix (~/.docker/config.json):                        │
│  {                                                          │
│    "credsStore" : "osxkeychain",    ← remove this line      │
│    "auths": { ... }                                         │
│  }                                                          │
│                                                              │
│  After fix:                                                 │
│  {                                                          │
│    "auths": { ... }                                         │
│  }                                                          │
│                                                              │
│  Then run: docker login                                     │
│  Credentials will be stored in config.json directly.        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.8 Docker Command Cheat Sheet

```bash
# ─── LIFECYCLE ───────────────────────────────────
docker run <image>              # Create and start container
docker start <container>        # Start stopped container
docker stop <container>         # Graceful stop (SIGTERM)
docker kill <container>         # Force stop (SIGKILL)
docker restart <container>      # Stop and start
docker rm <container>           # Remove stopped container
docker rm -f <container>        # Force remove (even running)

# ─── INFORMATION ─────────────────────────────────
docker ps                       # List running containers
docker ps -a                    # List ALL containers
docker logs <container>         # View logs
docker logs -f <container>      # Follow logs
docker inspect <container>      # Detailed JSON info
docker stats                    # Live resource usage
docker top <container>          # Processes in container

# ─── INTERACTION ─────────────────────────────────
docker exec -it <container> bash    # Shell into container
docker exec <container> <cmd>       # Run command in container
docker cp file.txt <container>:/path # Copy file to container
docker cp <container>:/path file.txt # Copy file from container

# ─── IMAGES ──────────────────────────────────────
docker images                   # List local images
docker pull <image>:<tag>       # Download image
docker rmi <image>              # Remove image
docker image prune              # Remove unused images

# ─── CLEANUP ─────────────────────────────────────
docker container prune          # Remove stopped containers
docker image prune -a           # Remove unused images
docker system prune -a          # Remove everything unused
docker system df                # Check disk usage
```

---

## 2.9 Complete Docker Flow Summary

This diagram shows the entire flow from installation to working inside a container:

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE DOCKER WORKFLOW                        │
│                                                              │
│  Step 1: Install Docker                                     │
│          sudo apt install docker.io                         │
│                    │                                         │
│                    ▼                                         │
│  Step 2: Verify daemon is running                           │
│          ps -ef | grep dockerd                              │
│          docker info                                        │
│                    │                                         │
│                    ▼                                         │
│  Step 3: Run a container                                    │
│          docker run -it centos                              │
│                    │                                         │
│                    ▼                                         │
│  Step 4: Image pulled (if not local)                        │
│          "Pulling from library/centos..."                   │
│                    │                                         │
│                    ▼                                         │
│  Step 5: Container created                                  │
│          New container ID assigned                          │
│          Namespaces + writable layer set up                 │
│                    │                                         │
│                    ▼                                         │
│  Step 6: Container started                                  │
│          Main process begins                                │
│                    │                                         │
│                    ▼                                         │
│  Step 7: Default CMD executed                               │
│          /bin/bash (for centos)                             │
│                    │                                         │
│                    ▼                                         │
│  Step 8: Terminal attached (because of -it)                 │
│          [root@abc123 /]#                                   │
│                    │                                         │
│                    ▼                                         │
│  Step 9: Work inside container                              │
│          Run commands, create files, install packages       │
│                    │                                         │
│                    ▼                                         │
│  Step 10: Exit                                              │
│           exit → bash ends → container stops                │
│                    │                                         │
│                    ▼                                         │
│  Step 11: Container is in "Exited" state                    │
│           docker ps -a shows it                             │
│           docker start <id> to restart                      │
│           docker rm <id> to delete                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.10 Key Concepts Summary Table

```
┌──────────────────────┬──────────────────────────────────────────────┐
│ Concept              │ Explanation                                   │
├──────────────────────┼──────────────────────────────────────────────┤
│ Container            │ An isolated process running on the host      │
│                      │ kernel with its own filesystem, network,     │
│                      │ and process space                            │
├──────────────────────┼──────────────────────────────────────────────┤
│ Image                │ Read-only template used to create containers │
│                      │ Contains OS files + runtime + app code       │
├──────────────────────┼──────────────────────────────────────────────┤
│ docker run           │ Creates + starts a new container from image  │
│                      │ Combines docker create + docker start        │
├──────────────────────┼──────────────────────────────────────────────┤
│ -it flags            │ Interactive mode: -i keeps STDIN open,       │
│                      │ -t allocates a terminal                      │
├──────────────────────┼──────────────────────────────────────────────┤
│ -d flag              │ Detached mode: runs container in background  │
│                      │ Returns control to your terminal             │
├──────────────────────┼──────────────────────────────────────────────┤
│ Default CMD          │ Command defined in image metadata            │
│                      │ Runs if user doesn't specify a command       │
├──────────────────────┼──────────────────────────────────────────────┤
│ Each run = new       │ Every docker run creates a brand new         │
│ container            │ container, even from the same image          │
├──────────────────────┼──────────────────────────────────────────────┤
│ Container filesystem │ Isolated from host — files created inside    │
│                      │ are NOT visible on the host                  │
├──────────────────────┼──────────────────────────────────────────────┤
│ PID 1                │ The main process in a container              │
│                      │ When PID 1 exits → container stops           │
├──────────────────────┼──────────────────────────────────────────────┤
│ exit                 │ Exits the shell → main process ends          │
│                      │ → container stops                            │
├──────────────────────┼──────────────────────────────────────────────┤
│ docker start         │ Restarts a stopped container (reuses it)     │
│                      │ Does NOT create a new container              │
├──────────────────────┼──────────────────────────────────────────────┤
│ docker attach        │ Connects your terminal to a running          │
│                      │ container's main process                     │
├──────────────────────┼──────────────────────────────────────────────┤
│ docker exec          │ Runs a NEW process inside a running          │
│                      │ container (doesn't affect main process)      │
├──────────────────────┼──────────────────────────────────────────────┤
│ Memory usage         │ Containers use RAM on demand — no upfront    │
│                      │ allocation like VMs                          │
├──────────────────────┼──────────────────────────────────────────────┤
│ Kernel sharing       │ All containers share the host kernel         │
│                      │ Each has isolated user-space (filesystem,    │
│                      │ processes, network)                          │
└──────────────────────┴──────────────────────────────────────────────┘
```

---

## 2.11 Interview-Ready Statements

Quick, confident answers based on the concepts in this module:

```
"docker run combines pull, create, and start into one command."

"Containers share the host kernel but have isolated filesystems."

"Each container has its own writable layer on top of the read-only image."

"Every docker run creates a new container — use docker start to reuse."

"Default CMD comes from image metadata — you can override it by
 specifying a command after the image name."

"When the main process (PID 1) exits, the container stops."

"Containers don't allocate RAM upfront — memory is used on demand
 as the process runs."

"Interactive mode (-it) gives you a shell; detached mode (-d) runs
 the container in the background."

"Files created inside a container are isolated — they don't appear
 on the host filesystem."

"docker exec runs a new process inside a running container without
 affecting the main process. docker attach connects to the existing
 main process."
```

---

## Module 2 Summary

- Docker can be installed on Linux, macOS, and Windows
- Quick install on Ubuntu: `sudo apt install docker.io`
- Verify daemon is running: `ps -ef | grep dockerd` or `docker info`
- `docker run` is the primary command to create and start containers
- `docker run` internally: check image → pull if needed → create → start → execute CMD
- `-it` flags give you an interactive shell inside a container
- `-d` flag runs the container in the background (detached)
- Container has its own hostname (container ID), OS, and filesystem
- Files created inside a container are NOT visible on the host (filesystem isolation)
- `exit` stops the container because the main process (/bin/bash) ends
- Every `docker run` creates a NEW container — use `docker start` to reuse
- Default CMD comes from image metadata — override by appending a command
- PID 1 is the main process — when it exits, the container stops
- Key flags: `-d` (detached), `-p` (ports), `--name` (naming), `-e` (env vars)
- `docker ps` lists running containers; `docker ps -a` lists all
- `docker exec -it` lets you shell into a running container
- `docker logs` shows container output
- `docker stop` + `docker rm` cleans up containers
- `docker system prune` reclaims disk space

---

**Next Module: [Module 3 - Docker Images](module-03-images.md)**
