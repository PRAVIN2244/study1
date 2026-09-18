# Module 6: Docker Compose — Multi-Container Applications

---

## 6.1 Why Docker Compose Exists — The Microservices Context

### Modern Applications Use Microservices

Modern teams build products using **microservice architecture** for:

- **Developer independence** — each team/service can change without breaking others
- **Isolation** — each service has its own dependencies/runtime
- **Scalability** — scale only what needs more capacity
- **Faster CI/CD** — build/test/deploy each component independently

In a microservice setup, your application is **not one big deployment**. It's a set of components:

```
┌─────────────────────────────────────────────────────────────┐
│              MICROSERVICE APPLICATION COMPONENTS             │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ API      │ │ Frontend │ │ Database │ │ Cache    │      │
│  │ Service  │ │ Service  │ │ Service  │ │ (Redis)  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐                                  │
│  │ Message  │ │ Worker   │                                  │
│  │ Queue    │ │ Service  │                                  │
│  └──────────┘ └──────────┘                                  │
│                                                              │
│  Each component = separate container                        │
└─────────────────────────────────────────────────────────────┘
```

### Traditional Deployment vs Docker Deployment

**Traditional deployment (without Docker):**

```
Step 1: Get a machine/VM
Step 2: Install OS packages
Step 3: Install runtime (Java/Python/Node)
Step 4: Install app server (Tomcat/JBoss)
Step 5: Copy build artifact (WAR/JAR)
Step 6: Configure ports, env vars, etc.

Problems:
- Slow setup
- Inconsistent across environments
- "Works on my machine" issues
```

**Docker deployment:**

```
Everything packaged into a Docker Image:
- OS base
- Runtime version
- App server (if needed)
- Application artifact
- Startup command

Then: docker run → container runs anywhere
```

### The Problem — Running Multiple Containers Manually

Suppose you have an application with 3 services:

```
┌─────────────────────────────────────────────────────────────┐
│              TYPICAL APPLICATION ARCHITECTURE                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Frontend    │  │  Backend     │  │  Database    │      │
│  │  (React /    │  │  (Node /     │  │  (MySQL)     │      │
│  │   Angular)   │  │   Java)      │  │              │      │
│  │  nginx:80    │  │  app:5000    │  │  mysql:3306  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Each service needs its own container.                      │
└─────────────────────────────────────────────────────────────┘
```

Without Docker Compose, you must run each container manually:

```bash
# Create network first
$ docker network create myapp

# Run database
$ docker run -d --name database --network myapp \
    -e MYSQL_ROOT_PASSWORD=password \
    mysql

# Run backend
$ docker run -d --name backend --network myapp \
    -p 5000:5000 \
    node

# Run frontend
$ docker run -d --name frontend --network myapp \
    -p 8080:80 \
    nginx
```

```
┌─────────────────────────────────────────────────────────────┐
│              PROBLEMS WITH MANUAL APPROACH                    │
│                                                              │
│  ❌ Hard to manage — 3+ long docker run commands            │
│  ❌ Hard to restart — must remember exact flags each time   │
│  ❌ Hard to configure networking — manual network creation  │
│  ❌ Hard to manage dependencies — which starts first?       │
│  ❌ Not reproducible — different team members, different    │
│     commands                                                │
│  ❌ Not version controlled — commands live in someone's     │
│     terminal history                                        │
│                                                              │
│  Solution → Docker Compose                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.2 What is Docker Compose?

Docker Compose is a tool to run **multiple containers** using **one YAML file** and **one command**.

Instead of many `docker run` commands, you define everything in `docker-compose.yml` and run:

```bash
$ docker-compose up
# Starts the entire application — all containers, networks, volumes
```

```
┌─────────────────────────────────────────────────────────────┐
│  Without Compose (manual commands):                         │
│  docker network create myapp                                │
│  docker run -d --name db --network myapp mysql              │
│  docker run -d --name backend --network myapp node          │
│  docker run -d --name frontend --network myapp nginx        │
│  # 4 commands, easy to make mistakes, hard to reproduce     │
│                                                              │
│  With Compose (one file, one command):                      │
│  docker compose up -d                                       │
│  # Everything defined in docker-compose.yml                 │
│  # Reproducible, version-controlled, shareable              │
└─────────────────────────────────────────────────────────────┘
```

### Key Idea: Compose Manages "Services", Not "Containers"

A **service** is a definition of how to run containers:

- Which image to use (or how to build it)
- Ports to map
- Volumes to mount
- Environment variables
- Restart policy
- How many instances (scale)

**A service can run 1 or many containers.**

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE vs CONTAINER                            │
│                                                              │
│  Service "api" (definition in YAML)                         │
│     │                                                        │
│     ├── api-1  (container instance 1)                       │
│     ├── api-2  (container instance 2)  ← when scaled       │
│     └── api-3  (container instance 3)  ← when scaled       │
│                                                              │
│  Service "db" (definition in YAML)                          │
│     │                                                        │
│     └── db-1   (container instance 1)                       │
│                                                              │
│  1 service = 1 or more containers                           │
└─────────────────────────────────────────────────────────────┘
```

### Docker Compose Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER COMPOSE ARCHITECTURE                     │
│                                                              │
│  You                                                        │
│   │                                                          │
│   │ docker compose up                                       │
│   ▼                                                          │
│  Docker Compose (reads docker-compose.yml)                  │
│   │                                                          │
│   │ calls                                                   │
│   ▼                                                          │
│  Docker Engine / Docker Daemon                              │
│   │                                                          │
│   ├── builds images (if build: specified)                   │
│   ├── creates network (project_default)                     │
│   ├── creates volumes (if defined)                          │
│   ├── creates containers (per service)                      │
│   └── starts containers                                     │
│                                                              │
│  All containers connected to the same network               │
│  and can communicate using service names.                   │
└─────────────────────────────────────────────────────────────┘
```

### Check Docker Compose Version

```bash
# Modern Docker (v2 — built into Docker CLI)
$ docker compose version
Docker Compose version v2.24.0

# Legacy Docker Compose (v1 — separate binary)
$ docker-compose --version
docker-compose version 1.29.2

# Note: Modern Docker uses "docker compose" (space)
# Legacy uses "docker-compose" (hyphen)
# Both work the same way. Modern is recommended.
```

---

## 6.3 docker-compose.yml — File Structure

The file must be named exactly `docker-compose.yml` (or `docker-compose.yaml`).

### YAML Rules You Must Remember

```
┌─────────────────────────────────────────────────────────────┐
│              YAML RULES                                      │
│                                                              │
│  ✅ Indentation-based (like Python)                         │
│  ✅ Use SPACES, not TABS                                    │
│  ✅ Key-value format:  key: value                           │
│  ✅ Nested/child keys use indentation:                      │
│                                                              │
│     parent:                                                  │
│       child1: value                                         │
│       child2: value                                         │
│                                                              │
│  ✅ Lists use dash:                                         │
│     ports:                                                   │
│       - "8080:80"                                           │
│       - "443:443"                                           │
│                                                              │
│  ❌ TABS will cause parse errors                            │
│  ❌ Inconsistent indentation will break the file            │
└─────────────────────────────────────────────────────────────┘
```

### Basic Structure

```yaml
# docker-compose.yml

services:        # Define your containers
  service1:      # Service name (becomes hostname)
    image: nginx
    ports:
      - "8080:80"

  service2:
    image: mysql
    environment:
      MYSQL_ROOT_PASSWORD: secret

volumes:         # Define named volumes (optional)
  db-data:

networks:        # Define custom networks (optional)
  backend:
```

### Simple Complete Example

```yaml
# docker-compose.yml — nginx + mysql

version: '3'

services:

  web:
    image: nginx
    ports:
      - "8080:80"

  database:
    image: mysql
    environment:
      MYSQL_ROOT_PASSWORD: password
```

```bash
# Run the application
$ docker-compose up

# Output:
# Creating network "myproject_default" with the default driver
# Creating myproject_web_1      ... done
# Creating myproject_database_1 ... done
# Attaching to myproject_web_1, myproject_database_1
# database_1  | Initializing database
# web_1       | nginx: ready for connections

# Both containers are running!
```

---

## 6.4 What Happens Internally When You Run docker-compose up

```
┌─────────────────────────────────────────────────────────────┐
│              docker-compose up — INTERNAL STEPS              │
│                                                              │
│  Step 1: Read docker-compose.yml                            │
│          │                                                   │
│          ▼                                                   │
│  Step 2: Create network (project_default)                   │
│          │                                                   │
│          ▼                                                   │
│  Step 3: Create containers for each service                 │
│          │                                                   │
│          ▼                                                   │
│  Step 4: Connect containers to the network                  │
│          │                                                   │
│          ▼                                                   │
│  Step 5: Start containers (respecting depends_on order)     │
│          │                                                   │
│          ▼                                                   │
│  Step 6: Application is running                             │
│                                                              │
│  docker-compose down — REVERSE:                             │
│  Stop containers → Remove containers → Remove network       │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Run in background (detached mode)
$ docker-compose up -d

# -d = detached mode (runs in background)
# You get your terminal back

# Stop and remove everything
$ docker-compose down

# Stops containers, removes containers, removes network
# Volumes are NOT removed (data preserved)

# Stop and remove everything INCLUDING volumes (DATA LOSS!)
$ docker-compose down -v
```

---

## 6.5 Service Name Is the Hostname

In Docker Compose, each service name automatically becomes a **DNS hostname**. Containers communicate using service names — no IP addresses needed.

```yaml
# docker-compose.yml
services:
  database:
    image: mysql
    environment:
      MYSQL_ROOT_PASSWORD: password

  backend:
    image: node:20-alpine
    command: sleep infinity
```

```bash
# Start the services
$ docker-compose up -d

# From backend, ping database by NAME
$ docker exec -it myproject-backend-1 ping -c 2 database
PING database (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.1 ms
64 bytes from 172.18.0.2: seq=1 ttl=64 time=0.1 ms

# ✅ "database" resolves to the database container's IP
# No hardcoded IPs needed — Docker Compose handles DNS
```

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE NAME = HOSTNAME                         │
│                                                              │
│  services:                                                  │
│    database:  ← hostname "database"                         │
│    backend:   ← hostname "backend"                          │
│    frontend:  ← hostname "frontend"                         │
│                                                              │
│  In application code:                                       │
│  DATABASE_URL=mysql://root:password@database:3306/mydb      │
│                                     ^^^^^^^^                │
│                                     service name as host    │
│                                                              │
│  No IP addresses. Names don't change on restart.            │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.6 Complete Real-World Example

```yaml
# docker-compose.yml — Frontend + Backend + Database

version: '3'

services:

  frontend:
    image: nginx
    ports:
      - "8080:80"

  backend:
    image: node:20-alpine
    ports:
      - "5000:5000"
    environment:
      DB_HOST: database
      DB_PORT: 3306

  database:
    image: mysql
    environment:
      MYSQL_ROOT_PASSWORD: password
    volumes:
      - dbdata:/var/lib/mysql

volumes:
  dbdata:
```

```bash
# Start all services
$ docker-compose up -d

# Output:
# Creating network "myapp_default" with the default driver
# Creating volume "myapp_dbdata" with default driver
# Creating myapp_frontend_1 ... done
# Creating myapp_backend_1  ... done
# Creating myapp_database_1 ... done

# Check running services
$ docker-compose ps

# NAME                 STATUS          PORTS
# myapp_frontend_1     Up 30 seconds   0.0.0.0:8080->80/tcp
# myapp_backend_1      Up 30 seconds   0.0.0.0:5000->5000/tcp
# myapp_database_1     Up 30 seconds   3306/tcp

# View logs
$ docker-compose logs

# View logs for specific service
$ docker-compose logs backend

# Stop everything
$ docker-compose down
```

---

## 6.7 Volumes in Docker Compose

```yaml
# Define volume in service
services:
  database:
    image: mysql
    volumes:
      - dbdata:/var/lib/mysql

# Declare the volume at the top level
volumes:
  dbdata:
```

```
┌─────────────────────────────────────────────────────────────┐
│  volumes:                                                   │
│    dbdata:     ← Docker creates and manages this volume     │
│                                                              │
│  services:                                                  │
│    database:                                                │
│      volumes:                                               │
│        - dbdata:/var/lib/mysql                               │
│          ^^^^^^  ^^^^^^^^^^^^^^^                            │
│          volume  mount point inside container               │
│          name                                               │
│                                                              │
│  Data in /var/lib/mysql persists even after:                │
│  docker-compose down (volume preserved)                     │
│  docker-compose down -v (volume DELETED — data lost!)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.8 Build Image from Dockerfile in Compose

Instead of using a pre-built image, Compose can build from a Dockerfile:

```yaml
services:
  app:
    build: .
    # Docker Compose runs "docker build ." automatically
    ports:
      - "3000:3000"

  app-custom:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    # Builds from ./backend/Dockerfile.prod
```

```bash
# Build and start
$ docker-compose up --build

# --build forces rebuild of images before starting
# Useful when you've changed the Dockerfile or source code

# Build without starting
$ docker-compose build
```

---

## 6.9 Networking in Docker Compose

Compose automatically creates a network for your project. All services are connected to it.

```bash
# When you run docker-compose up in a folder called "myproject":
# Docker creates a network called "myproject_default"

$ docker network ls
# NETWORK ID     NAME               DRIVER
# abc123         myproject_default   bridge

# All containers in the compose file are on this network
# They can communicate using service names
```

```
┌─────────────────────────────────────────────────────────────┐
│              COMPOSE NETWORKING                              │
│                                                              │
│  Project folder: myproject/                                 │
│                                                              │
│  Network created: myproject_default                         │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │   frontend     │  │   backend      │  │  database     │  │
│  │   :80          │  │   :5000        │  │  :3306        │  │
│  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              │                              │
│                    myproject_default                         │
│                    (auto-created network)                    │
│                                                              │
│  Containers communicate using service names:                │
│  frontend → backend:5000                                    │
│  backend → database:3306                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.10 Docker Compose Commands — Quick Reference

```bash
# ─── STARTING ──────────────────────────────────────────────

# Start all services (foreground — see logs)
$ docker-compose up

# Start in background (detached)
$ docker-compose up -d

# Start and rebuild images
$ docker-compose up --build

# Scale a service (run multiple instances)
$ docker-compose up --scale backend=3

# ─── STOPPING ─────────────────────────────────────────────

# Stop and remove containers + network
$ docker-compose down

# Stop and remove containers + network + volumes (DATA LOSS!)
$ docker-compose down -v

# Stop without removing
$ docker-compose stop

# ─── STATUS ───────────────────────────────────────────────

# List running services
$ docker-compose ps

# View logs
$ docker-compose logs

# View logs for specific service
$ docker-compose logs backend

# Follow logs in real-time
$ docker-compose logs -f

# ─── EXECUTING ────────────────────────────────────────────

# Run command in running container
$ docker-compose exec backend bash

# Run one-off command (creates new container)
$ docker-compose run --rm backend npm test

# ─── BUILDING ────────────────────────────────────────────

# Build all images
$ docker-compose build

# Build without cache
$ docker-compose build --no-cache
```

---

## 6.11 Sample Project 1 — Build Images + Run 2 Services

A minimal example showing how Compose builds and runs multiple services.

### Folder Layout

```
example1/
 ├── docker-compose.yml
 ├── one/
 │   └── Dockerfile
 ├── two/
 │   └── Dockerfile
 └── script.sh
```

### docker-compose.yml

```yaml
version: "3"
services:
  one:
    build: ./one
    image: img_one

  two:
    build: ./two
    image: img_two
```

### What This Means

```
┌─────────────────────────────────────────────────────────────┐
│  Service "one":                                             │
│    → Go to ./one directory                                  │
│    → Build using default Dockerfile                         │
│    → Tag image as img_one                                   │
│    → Create 1 container (default) from it                   │
│                                                              │
│  Service "two":                                             │
│    → Go to ./two directory                                  │
│    → Build using default Dockerfile                         │
│    → Tag image as img_two                                   │
│    → Create 1 container (default) from it                   │
└─────────────────────────────────────────────────────────────┘
```

### Run and Verify

```bash
$ cd example1

# Start in detached mode
$ docker compose up -d

# Output:
# [+] Running 2/2
#  ✔ Container example1-one-1  Started
#  ✔ Container example1-two-1  Started

# Check running containers
$ docker compose ps

# Output:
# NAME              COMMAND        STATE    PORTS
# example1-one-1    "/script.sh"   Up
# example1-two-1    "/script.sh"   Up

# View logs
$ docker compose logs

# Output:
# one-1  | 1
# one-1  | 1
# two-1  | 2
# two-1  | 2

# Follow logs live
$ docker compose logs -f

# Logs for only one service
$ docker compose logs -f one

# Stop and remove
$ docker compose down

# Output:
# [+] Running 2/2
#  ✔ Container example1-one-1  Removed
#  ✔ Container example1-two-1  Removed
#  ✔ Network example1_default  Removed
```

### Container Naming Pattern

```
<project_name>-<service_name>-<index>

Example:
  example1-one-1
  example1-one-2   (when scaled)
  example1-two-1
```

---

## 6.12 Sample Project 2 — Apache with Ports, Volumes, and Restart

A service with custom Dockerfile, port mapping, volume mounting, and auto-restart.

### docker-compose.yml

```yaml
version: "3"
services:
  test_service:
    build:
      context: ./myapache
      dockerfile: Dockerfile.apache
    image: myapache
    container_name: myapache_container
    ports:
      - "80:8080"
    volumes:
      - "./website:/var/www/html"
    restart: always
```

### Explanation of Each Field

```
┌─────────────────────────────────────────────────────────────┐
│  build:                                                      │
│    context: ./myapache          ← build context directory   │
│    dockerfile: Dockerfile.apache ← custom Dockerfile name   │
│                                                              │
│  Equivalent docker command:                                 │
│  docker build -t myapache -f Dockerfile.apache ./myapache   │
│                                                              │
│  image: myapache                                            │
│    → Tag the built image as "myapache"                      │
│                                                              │
│  container_name: myapache_container                         │
│    → Fixed name instead of auto-generated                   │
│                                                              │
│  ports: "80:8080"                                           │
│    → Host port 80 → Container port 8080                     │
│    → Browser http://localhost:80 reaches container's 8080   │
│                                                              │
│  volumes: "./website:/var/www/html"                         │
│    → Host folder mounted into container                     │
│    → Edit files locally → Apache serves updated content     │
│                                                              │
│  restart: always                                            │
│    → If container stops/crashes, Docker restarts it         │
└─────────────────────────────────────────────────────────────┘
```

### Port Mapping + Volume Mapping Diagram

```
Browser
  │   http://localhost:80
  ▼
Host machine port 80
  │  mapped to
  ▼
Container port 8080 (Apache)

Volume:

Host folder: ./website
   │ mounted to
   ▼
Container folder: /var/www/html
```

---

## 6.13 Sample Project 3 — Single Apache Web Server (Complete Files)

A complete, runnable example with all files included.

### Folder Structure

```
project1/
│
├── docker-compose.yml
├── website/
│   └── index.html
```

### File: website/index.html

```html
<!DOCTYPE html>
<html>
<head>
    <title>Docker Compose Demo</title>
</head>
<body>
    <h1>Hello from Docker Compose</h1>
    <p>This page is served from Apache container.</p>
</body>
</html>
```

### File: docker-compose.yml

```yaml
version: "3.9"

services:
  web:
    image: httpd:latest

    ports:
      - "8080:80"

    volumes:
      - ./website:/usr/local/apache2/htdocs/
```

### Line-by-Line Explanation

```
version: "3.9"          → Compose file format version
services:               → Define containers
  web:                  → Service name (container: project1-web-1)
    image: httpd:latest → Pull Apache image from Docker Hub
    ports:
      - "8080:80"       → Host 8080 → Container 80
    volumes:
      - ./website:/usr/local/apache2/htdocs/
                        → Local files served by Apache
```

### Architecture Diagram

```
Browser
  │
  │ http://localhost:8080
  ▼
Host Machine port 8080
  │
  ▼
Apache Container port 80
  │
  ▼
Serving files from volume:
./website → /usr/local/apache2/htdocs
```

### Run and Test

```bash
$ cd project1

$ docker compose up -d

# Output:
# Creating network "project1_default"
# Pulling web (httpd:latest)
# Creating project1-web-1

$ docker compose ps

# Output:
# NAME              COMMAND              STATE         PORTS
# project1-web-1    "httpd-foreground"   Up            0.0.0.0:8080->80/tcp

# Test in browser:
# http://localhost:8080
# Output: "Hello from Docker Compose"

$ docker compose down
```

---

## 6.14 Sample Project 4 — Web + MySQL Database (Complete Files)

A multi-service example with a Python Flask app connecting to MySQL.

### Folder Structure

```
project2/
│
├── docker-compose.yml
├── web/
│   ├── Dockerfile
│   └── app.py
```

### File: docker-compose.yml

```yaml
version: "3.9"

services:

  web:
    build: ./web

    ports:
      - "5000:5000"

    depends_on:
      - db

  db:
    image: mysql:8.0

    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: testdb

    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
```

### File: web/Dockerfile

```dockerfile
FROM python:3.10

WORKDIR /app

COPY app.py .

RUN pip install flask mysql-connector-python

CMD ["python", "app.py"]
```

### File: web/app.py

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Web container is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### Architecture Diagram

```
Browser
   │
   ▼
Web Container (Python Flask)  ← port 5000
   │
   │ connects using hostname "db"
   ▼
Database Container (MySQL)    ← port 3306

Compose creates network so "db" resolves to MySQL container IP.
```

### Run and Test

```bash
$ cd project2

$ docker compose up -d

# Output:
# Creating network "project2_default"
# Creating volume "project2_db_data"
# Building web
# Creating project2-db-1
# Creating project2-web-1

$ docker compose ps

# Output:
# NAME               STATE
# project2-web-1     Up
# project2-db-1      Up

# Access:
# http://localhost:5000
# Output: "Web container is running!"

$ docker compose down
```

---

## 6.15 Sample Project 5 — Full Microservice (Web + API + Redis + Database)

Enterprise-style example with 4 services.

### Folder Structure

```
project3/
│
├── docker-compose.yml
├── web/
│   ├── Dockerfile
│   └── index.html
├── api/
│   ├── Dockerfile
│   └── app.py
```

### File: docker-compose.yml

```yaml
version: "3.9"

services:

  web:
    build: ./web

    ports:
      - "8080:80"

    depends_on:
      - api

  api:
    build: ./api

    ports:
      - "5000:5000"

    depends_on:
      - db
      - redis

  db:
    image: mysql:8

    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: mydb

    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:latest

volumes:
  mysql_data:
```

### Architecture Diagram

```
Browser
   │
   ▼
Web Container (Frontend)     ← port 8080
   │
   ▼
API Container (Backend)      ← port 5000
   │        │
   ▼        ▼
MySQL     Redis
Container Container
```

### Run and Test

```bash
$ cd project3

$ docker compose up -d

# Creates 4 containers

$ docker compose ps

# Output:
# NAME     STATE
# web      Up
# api      Up
# db       Up
# redis    Up

# Scale API to 3 instances:
$ docker compose up -d --scale api=3

# Output:
# api-1 running
# api-2 running
# api-3 running

# Scaling diagram:
# Web
#  │
#  ▼
# API-1
# API-2
# API-3
#  │
#  ▼
# Database

$ docker compose down
```

---

## 6.16 docker ps vs docker compose ps

```
┌─────────────────────────────────────────────────────────────┐
│              docker ps vs docker compose ps                  │
│                                                              │
│  docker ps                                                  │
│    → Shows ALL running containers on the machine            │
│    → From any project, any compose file, any docker run     │
│                                                              │
│  docker compose ps                                          │
│    → Shows ONLY containers from the current compose project │
│    → Scoped to the docker-compose.yml in current directory  │
│                                                              │
│  Example:                                                   │
│  You have 10 containers running from 3 different projects.  │
│                                                              │
│  $ docker ps              → shows all 10                    │
│  $ docker compose ps      → shows only 3 (current project) │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.17 Stop vs Down — Key Difference

```
┌─────────────────────────────────────────────────────────────┐
│              STOP vs DOWN                                    │
│                                                              │
│  docker compose stop                                        │
│    → Stops containers                                       │
│    → Containers REMAIN (can be started again)               │
│    → Network remains                                        │
│    → Volumes remain                                         │
│                                                              │
│  docker compose down                                        │
│    → Stops containers                                       │
│    → REMOVES containers                                     │
│    → REMOVES network                                        │
│    → Volumes remain (unless -v flag)                        │
│                                                              │
│  docker compose down -v                                     │
│    → Everything above + REMOVES volumes (DATA LOSS!)        │
│                                                              │
│  docker compose rm                                          │
│    → Removes STOPPED containers only                        │
│    → Must run docker compose stop first                     │
└─────────────────────────────────────────────────────────────┘
```

```bash
# Stop only (containers remain):
$ docker compose stop

# Output:
# [+] Stopping 2/2
#  ✔ Container example1-one-1  Stopped
#  ✔ Container example1-two-1  Stopped

# Start previously stopped containers:
$ docker compose start

# Output:
# [+] Starting 2/2
#  ✔ Container example1-one-1  Started
#  ✔ Container example1-two-1  Started

# Down (containers removed):
$ docker compose down

# Output:
# [+] Running 3/3
#  ✔ Container example1-one-1  Removed
#  ✔ Container example1-two-1  Removed
#  ✔ Network example1_default  Removed

# Remove stopped containers:
$ docker compose rm

# Output:
# ? Going to remove example1-one-1, example1-two-1. Are you sure? [yN] y
# [+] Removing 2/2
#  ✔ Container example1-one-1  Removed
#  ✔ Container example1-two-1  Removed
```

---

## 6.18 Using a Different Compose Filename (-f)

Docker Compose looks for `docker-compose.yml` (or `.yaml`) by default.

If your file has a different name, use `-f`:

```bash
# Use a custom filename
$ docker compose -f artifactory-oss.yml up -d

# Use a custom filename for any command
$ docker compose -f custom-compose.yml ps
$ docker compose -f custom-compose.yml down
$ docker compose -f custom-compose.yml logs

# Combine multiple files (base + override)
$ docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 6.19 When to Use Docker Compose

```
┌─────────────────────────────────────────────────────────────┐
│              WHEN TO USE DOCKER COMPOSE                       │
│                                                              │
│  1. Development Environment                                 │
│     → Bring up DB + backend + frontend quickly              │
│     → Consistent setup for all developers                   │
│     → New team member: clone repo → docker compose up       │
│                                                              │
│  2. CI/CD Pipeline Testing                                  │
│     → Spin up services for unit/integration/smoke tests     │
│     → Tear everything down cleanly after tests              │
│     → Reproducible test environment                         │
│                                                              │
│  3. Operational Convenience                                 │
│     → Instead of long docker run commands, define once      │
│     → Start/stop reliably with one command                  │
│     → Version-controlled infrastructure                     │
│                                                              │
│  4. Local Microservice Development                          │
│     → Run all microservices together locally                │
│     → Test service-to-service communication                 │
│     → Simulate production architecture                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.20 Production-Style Folder Structure

```
project/
│
├── docker-compose.yml              ← main compose file
├── docker-compose.override.yml     ← dev overrides (auto-loaded)
├── docker-compose.prod.yml         ← production overrides
│
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   └── package.json
│
├── backend/
│   ├── Dockerfile
│   ├── src/
│   └── requirements.txt
│
├── database/
│   └── init.sql                    ← DB initialization script
│
├── .env                            ← environment variables
├── .env.example                    ← template (committed to git)
└── .gitignore
```

```bash
# Development (auto-loads docker-compose.override.yml):
$ docker compose up -d

# Production (explicit file selection):
$ docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 6.21 Services — Every Option Explained

### image — Use a Pre-Built Image

```yaml
services:
  web:
    image: nginx:1.25-alpine
    # Uses the nginx:1.25-alpine image from Docker Hub
```

### build — Build from Dockerfile

```yaml
services:
  api:
    build: .
    # Builds from ./Dockerfile in current directory

  api-custom:
    build:
      context: ./backend           # Build context directory
      dockerfile: Dockerfile.prod  # Custom Dockerfile name
      args:                        # Build arguments
        NODE_ENV: production
        APP_VERSION: "2.0.0"
      target: production           # Multi-stage build target
```

### container_name — Custom Container Name

```yaml
services:
  web:
    image: nginx
    container_name: my_web_server
    # Container name becomes: my_web_server
    # Instead of auto-generated: project_web_1
```

```bash
# Without container_name:
$ docker compose ps
# NAME              STATE
# project-web-1     Up        ← auto-generated

# With container_name: my_web_server:
$ docker compose ps
# NAME              STATE
# my_web_server     Up        ← custom name
```

### ports — Port Mapping

```yaml
services:
  web:
    image: nginx
    ports:
      - "8080:80"           # HOST:CONTAINER
      - "8443:443"          # Multiple ports
      - "127.0.0.1:9090:80" # Bind to specific interface
      - "3000"              # Random host port → container 3000
```

### environment — Environment Variables

```yaml
services:
  api:
    image: my-api:1.0
    environment:
      # Map syntax
      NODE_ENV: production
      DB_HOST: database
      DB_PORT: "5432"        # Numbers should be quoted in YAML
      LOG_LEVEL: info

  api-alt:
    image: my-api:1.0
    environment:
      # List syntax
      - NODE_ENV=production
      - DB_HOST=database
      - DB_PORT=5432

  api-file:
    image: my-api:1.0
    env_file:
      - .env                 # Load from .env file
      - .env.production      # Multiple files (later overrides earlier)
```

```bash
# Equivalent docker run command:
$ docker run -e NODE_ENV=production -e DB_HOST=database -e DB_PORT=5432 my-api:1.0
```

### volumes — Data Persistence

```yaml
services:
  db:
    image: postgres:16
    volumes:
      # Named volume (Docker manages location)
      - db-data:/var/lib/postgresql/data

      # Bind mount (host directory)
      - ./init-scripts:/docker-entrypoint-initdb.d

      # Read-only bind mount
      - ./config/pg.conf:/etc/postgresql/postgresql.conf:ro

      # Anonymous volume
      - /var/log/postgresql

  frontend:
    image: my-frontend
    volumes:
      # Bind mount for development (live reload)
      - ./src:/app/src
      - ./public:/app/public
      # Prevent overwriting node_modules in container
      - /app/node_modules

# Declare named volumes at top level
volumes:
  db-data:                    # Default driver (local)
  
  backup-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/backup
```

### depends_on — Service Dependencies

```yaml
services:
  api:
    image: my-api:1.0
    depends_on:
      - db
      - redis
    # API starts AFTER db and redis containers start
    # NOTE: "start" doesn't mean "ready" — the database might still be initializing

  api-with-healthcheck:
    image: my-api:1.0
    depends_on:
      db:
        condition: service_healthy    # Wait until db health check passes
      redis:
        condition: service_started    # Just wait for container to start

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### networks — Container Communication

```yaml
services:
  frontend:
    image: my-frontend
    networks:
      - frontend-net
    # Can only talk to services on frontend-net

  api:
    image: my-api
    networks:
      - frontend-net
      - backend-net
    # Can talk to both frontend and backend services

  db:
    image: postgres:16
    networks:
      - backend-net
    # Can only talk to services on backend-net
    # Frontend CANNOT reach the database directly

networks:
  frontend-net:
  backend-net:
```

### restart — Restart Policy

```yaml
services:
  api:
    image: my-api:1.0
    restart: unless-stopped
    # Options: "no", "always", "on-failure", "unless-stopped"
```

### healthcheck — Health Monitoring

```yaml
services:
  api:
    image: my-api:1.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### deploy — Resource Limits

```yaml
services:
  api:
    image: my-api:1.0
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
      replicas: 3              # Run 3 instances
```

### command — Override CMD

```yaml
services:
  api:
    image: my-api:1.0
    command: ["node", "app.js", "--port", "8080"]
    # Overrides the CMD in the Dockerfile

  api-dev:
    image: my-api:1.0
    command: npx nodemon app.js
    # Shell form also works
```

### entrypoint — Override ENTRYPOINT

```yaml
services:
  api:
    image: my-api:1.0
    entrypoint: ["./custom-entrypoint.sh"]
    command: ["--debug"]
```

---

## 6.22 Docker Compose Commands — Complete Reference

### Starting Services

```bash
# Start all services in foreground
docker compose up

# Output:
# [+] Running 3/3
#  ✔ Network myapp_default    Created
#  ✔ Container myapp-db-1     Created
#  ✔ Container myapp-api-1    Created
# Attaching to myapp-api-1, myapp-db-1
# db-1   | PostgreSQL init process complete; ready for start up.
# api-1  | Server running on port 3000

# Start in background (detached)
docker compose up -d

# Output:
# [+] Running 3/3
#  ✔ Network myapp_default    Created
#  ✔ Container myapp-db-1     Started
#  ✔ Container myapp-api-1    Started

# Start specific services only
docker compose up -d api db
# Only starts api and db (and their dependencies)

# Rebuild images before starting
docker compose up -d --build

# Force recreate containers (even if config hasn't changed)
docker compose up -d --force-recreate

# Remove orphan containers (services removed from compose file)
docker compose up -d --remove-orphans

# Scale a service
docker compose up -d --scale api=3
# Runs 3 instances of the api service
```

### Stopping Services

```bash
# Stop all services (containers keep existing)
docker compose stop

# Output:
# [+] Stopping 2/2
#  ✔ Container myapp-api-1    Stopped
#  ✔ Container myapp-db-1     Stopped

# Stop and remove containers, networks
docker compose down

# Output:
# [+] Running 3/3
#  ✔ Container myapp-api-1    Removed
#  ✔ Container myapp-db-1     Removed
#  ✔ Network myapp_default    Removed

# Stop, remove containers, AND delete volumes (DATA LOSS!)
docker compose down -v

# Stop, remove containers, AND delete images
docker compose down --rmi all
```

### Viewing Status

```bash
# List running services
docker compose ps

# Output:
# NAME           IMAGE        COMMAND                  SERVICE   STATUS          PORTS
# myapp-api-1    my-api:1.0   "node app.js"            api       Up 2 minutes    0.0.0.0:3000->3000/tcp
# myapp-db-1     postgres:16  "docker-entrypoint.s…"   db        Up 2 minutes    5432/tcp

# List all services (including stopped)
docker compose ps -a

# View logs
docker compose logs

# Follow logs for specific service
docker compose logs -f api

# Last 50 lines with timestamps
docker compose logs --tail 50 -t api
```

### Executing Commands

```bash
# Run a command in a running service
docker compose exec api bash
# Opens shell in the running api container

# Output:
# root@container:/#

# Run a single command (without opening shell)
docker compose exec api ls -l

# Output:
# total 8
# -rwxr-xr-x 1 root root  120 script.sh

# Key concept: exec targets a SERVICE NAME, not a container ID
# docker compose exec <service> <command>

# Run a one-off command (creates a new container)
docker compose run --rm api npm test
# Creates a temporary container, runs tests, removes container

# Difference:
# exec → Runs in EXISTING container (must be running)
# run  → Creates a NEW container (service doesn't need to be running)
```

### Building

```bash
# Build all services that have "build:" config
docker compose build

# Build specific service
docker compose build api

# Build without cache
docker compose build --no-cache

# Build with build arguments
docker compose build --build-arg NODE_ENV=production
```

### Other Commands

```bash
# View the resolved compose configuration
docker compose config
# Shows the final YAML after variable substitution

# Pull latest images for all services
docker compose pull

# View resource usage
docker compose top

# Pause/unpause all services
docker compose pause
docker compose unpause

# List images used by services
docker compose images
```

---

## 6.23 Environment Variables and .env Files

### The .env File

```bash
# .env (automatically loaded by Docker Compose)
POSTGRES_USER=admin
POSTGRES_PASSWORD=supersecret
POSTGRES_DB=myapp
API_PORT=3000
NODE_ENV=production
```

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}

  api:
    image: my-api:1.0
    ports:
      - "${API_PORT}:3000"
    environment:
      NODE_ENV: ${NODE_ENV}
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
```

### Variable Substitution Syntax

```yaml
services:
  api:
    image: my-api:${VERSION:-latest}
    # ${VAR:-default}  → Use "default" if VAR is unset or empty
    # ${VAR-default}   → Use "default" if VAR is unset (empty is OK)
    # ${VAR:?error}    → Error if VAR is unset or empty
    # ${VAR?error}     → Error if VAR is unset
```

### Multiple Environment Files

```yaml
services:
  api:
    env_file:
      - .env              # Base config
      - .env.local         # Local overrides (gitignored)
      - .env.${ENV:-dev}   # Environment-specific
```

---

## 6.24 Docker Compose Profiles

Profiles let you selectively start services.

```yaml
services:
  api:
    image: my-api:1.0
    # No profile — always starts

  db:
    image: postgres:16
    # No profile — always starts

  redis:
    image: redis:7
    profiles:
      - cache
    # Only starts when "cache" profile is activated

  debug-tools:
    image: busybox
    profiles:
      - debug
    # Only starts when "debug" profile is activated

  monitoring:
    image: grafana/grafana
    profiles:
      - monitoring
      - debug
    # Starts when either "monitoring" or "debug" profile is activated
```

```bash
# Start default services only (api, db)
docker compose up -d

# Start with cache profile (api, db, redis)
docker compose --profile cache up -d

# Start with multiple profiles
docker compose --profile cache --profile debug up -d

# Using environment variable
COMPOSE_PROFILES=cache,debug docker compose up -d
```

---

## 6.25 Real-World Industry Example: Full-Stack E-Commerce Application

```yaml
# docker-compose.yml — Production-grade e-commerce stack

services:
  # ─── Frontend (React) ─────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        REACT_APP_API_URL: http://api.example.com
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
    networks:
      - frontend-net

  # ─── API (Node.js/Express) ────────────────────
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
      replicas: 2
    networks:
      - frontend-net
      - backend-net

  # ─── Database (PostgreSQL) ────────────────────
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"
    networks:
      - backend-net

  # ─── Cache (Redis) ────────────────────────────
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 300M
          cpus: "0.5"
    networks:
      - backend-net

  # ─── Background Worker ────────────────────────
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    command: ["node", "worker.js"]
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
    networks:
      - backend-net

  # ─── Monitoring (optional profile) ────────────
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    profiles:
      - monitoring
    networks:
      - backend-net

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    profiles:
      - monitoring
    networks:
      - backend-net

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  frontend-net:
  backend-net:
```

```bash
# .env file for the above
DB_USER=ecommerce
DB_PASSWORD=secure_password_here
DB_NAME=ecommerce_db
JWT_SECRET=your-jwt-secret-here
STRIPE_SECRET_KEY=sk_test_xxx
GRAFANA_PASSWORD=admin123
```

```bash
# Start the application
docker compose up -d

# Start with monitoring
docker compose --profile monitoring up -d

# View all services
docker compose ps

# View API logs
docker compose logs -f api

# Scale API to 3 instances
docker compose up -d --scale api=3

# Run database migrations
docker compose exec api npx prisma migrate deploy

# Access database shell
docker compose exec db psql -U ecommerce -d ecommerce_db

# Backup database
docker compose exec db pg_dump -U ecommerce ecommerce_db > backup.sql

# Full teardown
docker compose down -v
```

---

## 6.26 Development vs Production Compose Files

### Base File (docker-compose.yml)

```yaml
services:
  api:
    build:
      context: ./backend
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/myapp
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: pass
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

### Development Override (docker-compose.override.yml)

```yaml
# Automatically loaded when you run docker compose up
services:
  api:
    build:
      target: development
    ports:
      - "3000:3000"
      - "9229:9229"         # Node.js debugger port
    volumes:
      - ./backend/src:/app/src  # Live reload
    environment:
      NODE_ENV: development
      DEBUG: "app:*"
    command: npx nodemon --inspect=0.0.0.0:9229 app.js

  db:
    ports:
      - "5432:5432"         # Expose DB port for local tools
```

### Production Override (docker-compose.prod.yml)

```yaml
services:
  api:
    build:
      target: production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
      replicas: 2
    environment:
      NODE_ENV: production
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s

  db:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
```

```bash
# Development (uses docker-compose.yml + docker-compose.override.yml automatically)
docker compose up -d

# Production (explicit file selection)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify merged config
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

---

## 6.27 Common Errors and Troubleshooting

### Error 1: "Service 'x' depends on service 'y' which is undefined"
```yaml
# CAUSE: Typo in depends_on or service name

services:
  api:
    depends_on:
      - database    # ← Typo! Service is named "db"
  db:
    image: postgres

# Fix: Match the exact service name
    depends_on:
      - db
```

### Error 2: "Port is already allocated"
```bash
# CAUSE: Another container or process is using the port

# Fix Option 1: Change the host port
ports:
  - "8081:80"    # Use 8081 instead of 8080

# Fix Option 2: Find what's using the port
docker compose ps
sudo lsof -i :8080
```

### Error 3: Database Connection Refused on Startup
```bash
# CAUSE: API starts before database is ready to accept connections
# depends_on only waits for container start, not application readiness

# Fix: Use healthcheck condition
services:
  api:
    depends_on:
      db:
        condition: service_healthy
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 10
```

### Error 4: Volume Permission Denied
```bash
# CAUSE: Container user doesn't have permission to write to mounted volume

# Fix Option 1: Set ownership in Dockerfile
RUN chown -R node:node /app/data

# Fix Option 2: Set user in compose
services:
  api:
    user: "1000:1000"

# Fix Option 3: Fix host directory permissions
chmod -R 777 ./data    # Not recommended for production
```

### Error 5: Changes Not Reflected After Rebuild
```bash
# CAUSE: Docker Compose uses cached images

# Fix: Force rebuild
docker compose up -d --build --force-recreate

# Or remove old images first
docker compose down --rmi local
docker compose up -d --build
```

### Error 6: "yaml: line X: did not find expected key"
```bash
# CAUSE: YAML indentation error

# YAML is whitespace-sensitive. Use spaces, not tabs.
# All items at the same level must have the same indentation.

# BAD:
services:
  api:
    image: my-api
     ports:          # ← Extra space!
      - "3000:3000"

# GOOD:
services:
  api:
    image: my-api
    ports:
      - "3000:3000"

# Validate your compose file:
docker compose config
```

---

## 6.28 Complete Docker Compose Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER COMPOSE COMPLETE FLOW                     │
│                                                              │
│  docker-compose.yml                                         │
│          │                                                   │
│          ▼                                                   │
│  docker-compose up                                          │
│          │                                                   │
│          ▼                                                   │
│  Network created (project_default)                          │
│          │                                                   │
│          ▼                                                   │
│  Volumes created (if defined)                               │
│          │                                                   │
│          ▼                                                   │
│  Containers created and started                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ frontend   │  │ backend    │  │ database   │            │
│  │ :80        │  │ :5000      │  │ :3306      │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│          │                                                   │
│          ▼                                                   │
│  Application running                                        │
│  All containers connected via network                       │
│  Services communicate using names                           │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  docker-compose down                                        │
│          │                                                   │
│          ▼                                                   │
│  Containers stopped and removed                             │
│  Network removed                                            │
│  Volumes preserved (unless -v flag used)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.29 Docker Compose Interview Questions

```
┌──────────────────────────────────────────────────────────────┐
│  DOCKER COMPOSE INTERVIEW Q&A                                │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: Why is Docker Compose needed?                           │
│  A: To define and run multiple containers using a single    │
│     configuration file (docker-compose.yml) instead of      │
│     running many docker run commands manually.              │
│                                                              │
│  Q: What file does Docker Compose use?                      │
│  A: docker-compose.yml (or docker-compose.yaml).            │
│     It defines services, networks, and volumes in YAML.     │
│                                                              │
│  Q: How do containers communicate in Docker Compose?        │
│  A: Using service names as hostnames. Compose creates a     │
│     default network and enables DNS resolution — a service  │
│     named "database" is reachable at hostname "database".   │
│                                                              │
│  Q: How do you stop a Docker Compose application?           │
│  A: docker-compose down — stops and removes containers      │
│     and networks. Add -v to also remove volumes.            │
│                                                              │
│  Q: What is the difference between docker-compose up        │
│     and docker-compose up -d?                               │
│  A: Without -d, containers run in foreground (logs visible).│
│     With -d (detached), containers run in background.       │
│                                                              │
│  Q: How do you scale a service in Docker Compose?           │
│  A: docker-compose up --scale backend=3                     │
│     Creates 3 instances of the backend service.             │
│                                                              │
│  Q: Does Docker Compose create a network automatically?     │
│  A: Yes. It creates a default bridge network named          │
│     <project>_default. All services are connected to it.    │
│                                                              │
│  Q: What happens to volumes when you run                    │
│     docker-compose down?                                    │
│  A: Volumes are preserved (data safe). Only                 │
│     docker-compose down -v deletes volumes.                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 6.30 Hands-On: Example Voting Application

This is a classic multi-service application used in Docker's official demos. It ties together everything covered in this module: services, networking, ports, depends_on, and multi-container orchestration.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              VOTING APPLICATION ARCHITECTURE                 │
│                                                              │
│  User                          User                         │
│   │                             │                            │
│   ▼                             ▼                            │
│  ┌──────────┐              ┌──────────┐                     │
│  │  vote    │              │  result  │                     │
│  │ :5000→80 │              │ :5001→80 │                     │
│  │ Frontend │              │Dashboard │                     │
│  └────┬─────┘              └────┬─────┘                     │
│       │                         │                            │
│       ▼                         │                            │
│  ┌──────────┐              ┌────┴─────┐                     │
│  │  redis   │              │    db    │                     │
│  │  Queue   │◄────────────►│ Postgres │                     │
│  └────┬─────┘              └────┬─────┘                     │
│       │                         │                            │
│       └────────┐   ┌────────────┘                            │
│                ▼   ▼                                         │
│           ┌──────────┐                                      │
│           │  worker  │                                      │
│           │ Processor│                                      │
│           └──────────┘                                      │
│                                                              │
│  Flow:                                                      │
│    1. User votes on the vote frontend                       │
│    2. Vote is pushed to Redis queue                         │
│    3. Worker reads from Redis, writes to PostgreSQL         │
│    4. Result dashboard reads from PostgreSQL                │
└─────────────────────────────────────────────────────────────┘
```

### docker-compose.yml

```yaml
version: '3'
services:
  redis:
    image: redis

  db:
    image: postgres:9.4

  vote:
    image: voting-app
    ports:
      - "5000:80"
    depends_on:
      - redis

  worker:
    image: worker-app
    depends_on:
      - db
      - redis

  result:
    image: result-app
    ports:
      - "5001:80"
    depends_on:
      - db
```

### Service Breakdown

```
┌──────────┬────────────────┬─────────┬──────────────────────────────────┐
│ Service  │ Image          │ Ports   │ Role                             │
├──────────┼────────────────┼─────────┼──────────────────────────────────┤
│ redis    │ redis          │ —       │ In-memory queue for votes        │
│ db       │ postgres:9.4   │ —       │ Persistent storage for results   │
│ vote     │ voting-app     │ 5000→80 │ Frontend where users cast votes  │
│ worker   │ worker-app     │ —       │ Processes votes from Redis to DB │
│ result   │ result-app     │ 5001→80 │ Displays aggregated results      │
└──────────┴────────────────┴─────────┴──────────────────────────────────┘
```

### Deploy and Test

```bash
# Step 1: Deploy the stack
$ docker-compose up -d

# Output:
# Creating network "voting_default" with the default driver
# Creating voting_redis_1  ... done
# Creating voting_db_1     ... done
# Creating voting_vote_1   ... done
# Creating voting_worker_1 ... done
# Creating voting_result_1 ... done

# Step 2: Verify all containers are running
$ docker ps
# CONTAINER ID   IMAGE         STATUS    PORTS                  NAMES
# abc123         voting-app    Up        0.0.0.0:5000->80/tcp   voting_vote_1
# def456         result-app    Up        0.0.0.0:5001->80/tcp   voting_result_1
# ghi789         worker-app    Up                               voting_worker_1
# jkl012         redis         Up        6379/tcp               voting_redis_1
# mno345         postgres:9.4  Up        5432/tcp               voting_db_1

# Step 3: Access the application
# Voting interface:  http://localhost:5000
# Results dashboard: http://localhost:5001

# Step 4: Clean up
$ docker-compose down
# Stops containers and removes the network
# Volumes and images remain unless you add --volumes or --rmi all
```

### Key Concepts Demonstrated

```
┌─────────────────────────────────────────────────────────────┐
│  What this example teaches:                                 │
│                                                              │
│  1. Multi-service orchestration                             │
│     Five services defined in one YAML file                  │
│                                                              │
│  2. Service discovery                                       │
│     Services communicate by name (vote → redis, worker → db)│
│     Compose creates a default network automatically         │
│                                                              │
│  3. Port mapping                                            │
│     Only vote and result expose ports to the host           │
│     redis, db, worker are internal-only                     │
│                                                              │
│  4. depends_on                                              │
│     Ensures startup order (vote waits for redis, etc.)      │
│     ⚠️  Does NOT wait for the service to be "ready"        │
│     For production: use healthchecks with condition          │
│                                                              │
│  5. Separation of concerns                                  │
│     Each service has a single responsibility                │
│     Frontend, queue, processor, database, dashboard         │
└─────────────────────────────────────────────────────────────┘
```

### Production Improvement: Adding Health Checks

The basic `depends_on` only waits for the container to start, not for the service inside to be ready. For production, add health checks:

```yaml
version: '3.8'
services:
  redis:
    image: redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  db:
    image: postgres:9.4
    environment:
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 3

  vote:
    image: voting-app
    ports:
      - "5000:80"
    depends_on:
      redis:
        condition: service_healthy

  worker:
    image: worker-app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  result:
    image: result-app
    ports:
      - "5001:80"
    depends_on:
      db:
        condition: service_healthy
```

---

## Module 6 Summary

- **Microservices** need multiple containers — Compose manages them as a unit
- **Traditional deployment** (manual VM setup) vs **Docker deployment** (image packaging) — Docker is faster and consistent
- Compose manages **services**, not containers — a service can run 1 or many containers
- `docker-compose up -d` starts everything; `docker-compose down` stops and removes
- `docker compose stop` stops without removing; `docker compose start` resumes
- `docker compose rm` removes stopped containers
- Compose automatically creates a network — all services are connected
- **Service names are hostnames** — containers communicate by name, not IP
- `depends_on` with `condition: service_healthy` ensures proper startup order
- Volumes in Compose persist data; `docker-compose down -v` deletes them (data loss!)
- `build:` with `context:` and `dockerfile:` builds from custom Dockerfiles
- `container_name:` sets a fixed name instead of auto-generated
- `restart: always` auto-restarts crashed containers
- `docker-compose up --build` rebuilds images before starting
- `docker-compose up --scale backend=3` runs multiple instances
- `docker ps` shows ALL containers; `docker compose ps` shows only current project
- Use `-f` flag for custom compose filenames
- Use `.env` files for configuration; never commit secrets
- Profiles enable optional services (monitoring, debugging)
- Override files separate dev/prod configs: `docker-compose.override.yml`
- `docker compose exec` runs commands in existing containers (targets service name, not container ID)
- `docker compose run --rm` creates temporary containers for one-off tasks
- **Best use cases**: development environments, CI/CD testing, operational convenience

---

**Next Module: [Module 7 - Docker Networking](module-07-networking.md)**
