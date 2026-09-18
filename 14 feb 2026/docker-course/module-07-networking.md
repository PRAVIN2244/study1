# Module 7: Docker Networking In-Depth

---

## 7.1 Why Docker Networking Exists

Docker networking allows containers to communicate with the outside world and with each other.

```
┌─────────────────────────────────────────────────────────────┐
│              WHY DOCKER NETWORKING EXISTS                     │
│                                                              │
│  Without networking, containers would be completely          │
│  isolated — unable to serve web pages, connect to           │
│  databases, or talk to other services.                      │
│                                                              │
│  Docker networking enables 4 types of communication:        │
│                                                              │
│  1. Container ↔ Container                                   │
│     (e.g., web app talks to database)                       │
│                                                              │
│  2. Container → Internet                                    │
│     (e.g., container downloads packages, calls APIs)        │
│                                                              │
│  3. Host → Container                                        │
│     (e.g., you curl a web server running in a container)    │
│                                                              │
│  4. External Users → Container                              │
│     (e.g., users access your app via port mapping)          │
└─────────────────────────────────────────────────────────────┘
```

### Basic Network Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Internet                                │
│                         │                                    │
│                         │                                    │
│           ┌─────────────┴─────────────┐                     │
│           │       Host Machine         │                     │
│           │                            │                     │
│           │     Docker Engine          │                     │
│           │                            │                     │
│           │  ┌──────────────────────┐  │                     │
│           │  │  Bridge Network      │  │                     │
│           │  │  (docker0)           │  │                     │
│           │  │                      │  │                     │
│           │  │  ┌────────────────┐  │  │                     │
│           │  │  │ Container A    │  │  │                     │
│           │  │  │ IP: 172.17.0.2 │  │  │                     │
│           │  │  └────────────────┘  │  │                     │
│           │  │                      │  │                     │
│           │  │  ┌────────────────┐  │  │                     │
│           │  │  │ Container B    │  │  │                     │
│           │  │  │ IP: 172.17.0.3 │  │  │                     │
│           │  │  └────────────────┘  │  │                     │
│           │  │                      │  │                     │
│           │  └──────────────────────┘  │                     │
│           │                            │                     │
│           └────────────────────────────┘                     │
│                                                              │
│  Each container gets its own IP address on the Docker        │
│  bridge network. These IPs are internal — not reachable     │
│  from outside the host.                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.2 Docker Network Types

Docker provides several network drivers for different use cases:

```
┌──────────────┬────────────────────────────────────────────────────┐
│ Driver       │ Description                                        │
├──────────────┼────────────────────────────────────────────────────┤
│ bridge       │ Default. Isolated network on a single host.        │
│              │ Containers communicate via IP or DNS.              │
├──────────────┼────────────────────────────────────────────────────┤
│ host         │ Container shares the host's network stack.         │
│              │ No isolation. Best performance.                    │
├──────────────┼────────────────────────────────────────────────────┤
│ none         │ No networking. Container is completely isolated.   │
├──────────────┼────────────────────────────────────────────────────┤
│ overlay      │ Multi-host networking (Docker Swarm).              │
│              │ Containers on different hosts communicate.         │
├──────────────┼────────────────────────────────────────────────────┤
│ macvlan      │ Assigns a MAC address to the container.            │
│              │ Container appears as a physical device on network. │
├──────────────┼────────────────────────────────────────────────────┤
│ ipvlan       │ Similar to macvlan but shares host's MAC address.  │
└──────────────┴────────────────────────────────────────────────────┘
```

---

## 7.3 Bridge Network (Default)

When you install Docker, it creates a default bridge network called `bridge`.

```bash
# List all networks
docker network ls

# Output:
# NETWORK ID     NAME      DRIVER    SCOPE
# abc123def456   bridge    bridge    local
# def456ghi789   host      host      local
# ghi789jkl012   none      null      local

# MEANING:
# bridge → Default network for containers
# host   → Shares host network (no isolation)
# none   → No networking
```

### Default Bridge Network

```bash
# Containers on the default bridge can communicate via IP but NOT by name
docker run -d --name container1 nginx
docker run -d --name container2 nginx

# Get container1's IP
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container1
# Output: 172.17.0.2

# From container2, ping by IP works:
docker exec container2 ping -c 2 172.17.0.2
# PING 172.17.0.2: 64 bytes from 172.17.0.2: seq=0 ttl=64 time=0.1ms

# But ping by name FAILS on default bridge:
docker exec container2 ping -c 2 container1
# ping: bad address 'container1'

# Cleanup
docker rm -f container1 container2
```

### User-Defined Bridge Network (Recommended)

```bash
# Create a custom bridge network
docker network create my-network

# Output:
# sha256:abc123def456...

# MEANING: Creates an isolated network with DNS resolution enabled.

# Run containers on the custom network
docker run -d --name web --network my-network nginx
docker run -d --name api --network my-network my-api:1.0

# Now DNS resolution works — containers can reach each other by name:
docker exec api ping -c 2 web
# PING web (172.18.0.2): 56 data bytes
# 64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.1ms

# MEANING: On user-defined networks, Docker provides automatic DNS.
# Container name = hostname. No need to know IP addresses.
```

### Default vs User-Defined Bridge

```
┌─────────────────────┬──────────────────┬──────────────────────┐
│ Feature             │ Default Bridge   │ User-Defined Bridge  │
├─────────────────────┼──────────────────┼──────────────────────┤
│ DNS Resolution      │ ❌ No            │ ✅ Yes               │
│ Automatic Isolation │ ❌ All share one │ ✅ Per-network       │
│ Connect/Disconnect  │ ❌ Restart needed│ ✅ Live              │
│ Environment Sharing │ ✅ --link (old)  │ ❌ Not needed        │
│ Recommended         │ ❌ No            │ ✅ Yes               │
└─────────────────────┴──────────────────┴──────────────────────┘
```

---

## 7.4 Network Commands — Complete Reference

```bash
# Create a network
docker network create my-network

# Create with specific subnet
docker network create --subnet=172.20.0.0/16 --gateway=172.20.0.1 my-network

# Create with specific driver
docker network create --driver bridge my-bridge
docker network create --driver overlay my-overlay  # Swarm only

# List networks
docker network ls

# Output:
# NETWORK ID     NAME         DRIVER    SCOPE
# abc123def456   bridge       bridge    local
# def456ghi789   host         host      local
# ghi789jkl012   my-network   bridge    local
# jkl012mno345   none         null      local

# Inspect a network (see connected containers, subnet, etc.)
docker network inspect my-network

# Output (abbreviated):
# [
#     {
#         "Name": "my-network",
#         "Driver": "bridge",
#         "IPAM": {
#             "Config": [
#                 {
#                     "Subnet": "172.18.0.0/16",
#                     "Gateway": "172.18.0.1"
#                 }
#             ]
#         },
#         "Containers": {
#             "abc123...": {
#                 "Name": "web",
#                 "IPv4Address": "172.18.0.2/16"
#             },
#             "def456...": {
#                 "Name": "api",
#                 "IPv4Address": "172.18.0.3/16"
#             }
#         }
#     }
# ]

# Connect a running container to a network
docker network connect my-network existing-container

# Disconnect a container from a network
docker network disconnect my-network existing-container

# Remove a network
docker network rm my-network

# Remove all unused networks
docker network prune

# Output:
# WARNING! This will remove all custom networks not used by at least one container.
# Deleted Networks:
# my-old-network
# test-network
```

---

## 7.5 Host Network

The container shares the host's network stack directly. No port mapping needed.

```bash
# Run with host networking
docker run -d --network host --name web-host nginx

# Nginx is now accessible on host's port 80 directly
# No -p flag needed — container IS the host network
curl http://localhost:80

# Check — no port mapping shown
docker port web-host
# (empty — ports are directly on host)

# When to use host networking:
# - Maximum network performance (no NAT overhead)
# - Container needs to bind to many ports
# - Network monitoring tools (tcpdump, wireshark)
#
# When NOT to use:
# - Multiple containers need the same port (conflicts)
# - You need network isolation
# - Running on macOS/Windows (host networking works differently)

docker rm -f web-host
```

---

## 7.6 None Network

Complete network isolation — no network interfaces at all.

```bash
docker run -d --network none --name isolated alpine sleep infinity

# Check network interfaces
docker exec isolated ip addr
# Output:
# 1: lo: <LOOPBACK,UP,LOWER_UP>
#     inet 127.0.0.1/8 scope host lo
# Only loopback — no external connectivity

# Use cases:
# - Security-sensitive batch processing
# - Containers that only process local files
# - Cryptographic operations that shouldn't have network access

docker rm -f isolated
```

---

## 7.7 Container DNS and Service Discovery

```bash
# On user-defined networks, Docker runs an embedded DNS server at 127.0.0.11

docker network create app-net
docker run -d --name database --network app-net postgres:16 -e POSTGRES_PASSWORD=secret
docker run -d --name api --network app-net my-api:1.0

# Inside the api container:
docker exec api cat /etc/resolv.conf
# Output:
# nameserver 127.0.0.11
# options ndots:0

# DNS resolution:
docker exec api nslookup database
# Server:    127.0.0.11
# Address:   127.0.0.11:53
# Name:      database
# Address:   172.18.0.2

# MEANING: Docker's embedded DNS resolves container names to IPs.
# Your application code uses hostnames, not IPs:
# DATABASE_URL=postgresql://user:pass@database:5432/mydb
#                                      ^^^^^^^^
#                                      Container name as hostname
```

### Network Aliases

```bash
# Give a container multiple DNS names
docker run -d \
  --name postgres-primary \
  --network app-net \
  --network-alias db \
  --network-alias database \
  --network-alias postgres \
  postgres:16

# All these resolve to the same container:
docker exec api ping -c 1 db
docker exec api ping -c 1 database
docker exec api ping -c 1 postgres
docker exec api ping -c 1 postgres-primary

# Use case: Migration — old code uses "db", new code uses "database"
# Both work without changing the container name
```

---

## 7.8 Port Mapping — Why It's Required

### Traditional Server (No Docker) vs Docker

```
┌─────────────────────────────────────────────────────────────┐
│              TRADITIONAL (No Docker)                        │
│                                                              │
│  You install Apache/Jenkins directly on the machine.        │
│  They bind to the host's network directly.                  │
│                                                              │
│  Host Machine (IP: 10.0.0.5)                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Apache → listening on port 80                        │   │
│  │  Jenkins → listening on port 8080                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Users access directly:                                     │
│  http://10.0.0.5:80     → Apache                           │
│  http://10.0.0.5:8080   → Jenkins                          │
│                                                              │
│  No extra mapping needed — apps bind to host ports directly │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              WITH DOCKER                                    │
│                                                              │
│  Applications run INSIDE containers, not on the host.       │
│  Each container has its own isolated network namespace.      │
│  The app's port exists INSIDE the container only.           │
│                                                              │
│  Host Machine (IP: 10.0.0.5)                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────┐           │   │
│  │  │ Container A      │  │ Container B      │           │   │
│  │  │ Apache → :80     │  │ Jenkins → :8080  │           │   │
│  │  │ IP: 172.17.0.2   │  │ IP: 172.17.0.3   │           │   │
│  │  └─────────────────┘  └─────────────────┘           │   │
│  │                                                       │   │
│  │  External users CANNOT reach 172.17.0.2:80 directly  │   │
│  │  Container IPs are internal to the host only          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Docker needs a "bridge" between host port and container    │
│  port → this is PORT MAPPING                               │
└─────────────────────────────────────────────────────────────┘
```

### Why Container IP Is Not Reachable from Outside

```
┌─────────────────────────────────────────────────────────────┐
│  Container IP (e.g., 172.17.0.2) is from Docker's          │
│  INTERNAL bridge network.                                   │
│                                                              │
│  This IP is only reachable:                                 │
│  ✅ From the host machine itself                            │
│  ✅ From other containers on the same Docker network        │
│  ❌ NOT from external machines / the internet               │
│                                                              │
│  But container IP IS useful for:                            │
│  • Container-to-container communication (microservices)     │
│  • Frontend container talking to DB container               │
│  • Using Docker DNS (container names) instead of IPs       │
│                                                              │
│  For external access, you MUST use port mapping (-p)        │
└─────────────────────────────────────────────────────────────┘
```

### Port Mapping Syntax: -p HOST_PORT:CONTAINER_PORT

```
┌─────────────────────────────────────────────────────────────┐
│              -p HOST_PORT:CONTAINER_PORT                     │
│                                                              │
│  docker run -d -p 8081:80 nginx                             │
│                    │    │                                    │
│                    │    └── RIGHT side = port INSIDE         │
│                    │        container (app listens here)     │
│                    │                                         │
│                    └── LEFT side = port on HOST              │
│                        (user accesses this)                  │
│                                                              │
│  Traffic flow:                                              │
│  User → http://host-ip:8081 → Host port 8081               │
│       → forwarded to → Container port 80 → nginx           │
└─────────────────────────────────────────────────────────────┘
```

### Running Apache (httpd) with Port Mapping

```bash
# Run Apache in a container, map host port 80 to container port 80
$ docker run -d --name apache -p 80:80 httpd

# Output:
abc123def456...

# Check running containers
$ docker ps

CONTAINER ID   IMAGE   COMMAND              STATUS         PORTS                NAMES
abc123def456   httpd   "httpd-foreground"   Up 10 seconds  0.0.0.0:80->80/tcp   apache

# PORTS column explained:
# 0.0.0.0:80->80/tcp means:
#   0.0.0.0  = listening on ALL host interfaces
#   :80      = host port 80
#   ->80     = forwards to container port 80
#   /tcp     = TCP protocol

# Test access
$ curl http://localhost:80

<html><body><h1>It works!</h1></body></html>
```

### Host Port Conflict — Running nginx Alongside Apache

Apache already uses host port 80. nginx also listens on port 80 inside its container. You must map nginx to a **different host port**.

```bash
# Apache is already on host port 80
# Map nginx container port 80 to host port 8081
$ docker run -d --name nginx1 -p 8081:80 nginx

$ docker ps

CONTAINER ID   IMAGE   COMMAND                  STATUS         PORTS                  NAMES
abc123def456   httpd   "httpd-foreground"       Up 5 minutes   0.0.0.0:80->80/tcp     apache
bbb222ccc333   nginx   "/docker-entrypoint.…"   Up 10 seconds  0.0.0.0:8081->80/tcp   nginx1

# Access each service on its own host port:
$ curl http://localhost:80
<html><body><h1>It works!</h1></body></html>    ← Apache

$ curl http://localhost:8081
<!DOCTYPE html>... Welcome to nginx! ...         ← nginx
```

```
┌─────────────────────────────────────────────────────────────┐
│              HOST PORT CONFLICT RULES                        │
│                                                              │
│  Rule A: Host port must be FREE                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ✅ Apache on host:80, nginx on host:8081            │   │
│  │  ❌ Apache on host:80, nginx on host:80 → ERROR     │   │
│  │                                                       │   │
│  │  Error message:                                       │   │
│  │  "Bind for 0.0.0.0:80 failed: port is already       │   │
│  │   allocated"                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Rule B: Container port must be CORRECT                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker doesn't verify the app is listening on the   │   │
│  │  container port you specify.                          │   │
│  │                                                       │   │
│  │  ✅ -p 8081:80 httpd  → httpd listens on 80 → works │   │
│  │  ❌ -p 8081:9999 httpd → nothing on 9999 → fails    │   │
│  │     (connection refused — no app listening there)     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Multiple Instances of the Same App

You can run multiple containers from the same image — each must map to a different host port:

```bash
$ docker run -d --name nginx1 -p 8081:80 nginx
$ docker run -d --name nginx2 -p 8082:80 nginx
$ docker run -d --name nginx3 -p 8083:80 nginx

$ docker ps

CONTAINER ID   IMAGE   STATUS         PORTS                  NAMES
aaa111bbb222   nginx   Up 10 seconds  0.0.0.0:8081->80/tcp   nginx1
ccc333ddd444   nginx   Up 8 seconds   0.0.0.0:8082->80/tcp   nginx2
eee555fff666   nginx   Up 5 seconds   0.0.0.0:8083->80/tcp   nginx3

# All three containers run nginx on container port 80
# But each is accessible on a different host port:
$ curl http://localhost:8081    # → nginx1
$ curl http://localhost:8082    # → nginx2
$ curl http://localhost:8083    # → nginx3
```

```
┌─────────────────────────────────────────────────────────────┐
│              MULTIPLE INSTANCES — SAME IMAGE                │
│                                                              │
│  Host Machine                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Port 8081 ──→ ┌──────────┐                          │   │
│  │                │ nginx1   │ container:80              │   │
│  │                └──────────┘                          │   │
│  │                                                       │   │
│  │  Port 8082 ──→ ┌──────────┐                          │   │
│  │                │ nginx2   │ container:80              │   │
│  │                └──────────┘                          │   │
│  │                                                       │   │
│  │  Port 8083 ──→ ┌──────────┐                          │   │
│  │                │ nginx3   │ container:80              │   │
│  │                └──────────┘                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Same image, same container port, different host ports      │
└─────────────────────────────────────────────────────────────┘
```

### Load Balancing Across Multiple Containers

Docker alone on a single machine does NOT provide "one port → auto-route to multiple containers." Two practical options:

```
┌─────────────────────────────────────────────────────────────┐
│              LOAD BALANCING OPTIONS                          │
│                                                              │
│  Option 1: Reverse proxy (nginx/HAProxy) on the host        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  User → host:80 → nginx (reverse proxy)              │   │
│  │                    ├── → container1:80                │   │
│  │                    ├── → container2:80                │   │
│  │                    └── → container3:80                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Option 2: Orchestration (production)                       │
│  • Docker Swarm: docker service create --replicas 3 nginx  │
│  • Kubernetes: kubectl scale deployment nginx --replicas=3  │
│  Both provide built-in load balancing across replicas       │
└─────────────────────────────────────────────────────────────┘
```

### Firewall / Security Group Clarification

Port mapping does NOT bypass firewalls. If you're on a cloud VM (AWS, Azure, GCP), you still need inbound rules allowing the port.

```
┌─────────────────────────────────────────────────────────────┐
│              PORT MAPPING + FIREWALL                        │
│                                                              │
│  docker run -d -p 8081:80 nginx                             │
│                                                              │
│  For external access, ALL of these must be true:            │
│                                                              │
│  ✅ Container is running and app is listening on port 80    │
│  ✅ Docker mapped host:8081 → container:80                  │
│  ✅ Host firewall allows inbound on port 8081               │
│  ✅ Cloud security group allows inbound on port 8081        │
│                                                              │
│  If ANY of these is missing → external access fails         │
│                                                              │
│  Common mistake:                                            │
│  "I mapped the port but can't access from my browser"       │
│  → Check: cloud security group / firewall rules             │
└─────────────────────────────────────────────────────────────┘
```

### Verifying Port Mapping on the Host

```bash
# Check which ports Docker is listening on
$ ss -lntp | grep docker

LISTEN  0  4096  0.0.0.0:80    0.0.0.0:*  users:(("docker-proxy",pid=1234,fd=4))
LISTEN  0  4096  0.0.0.0:8081  0.0.0.0:*  users:(("docker-proxy",pid=1235,fd=4))
LISTEN  0  4096  0.0.0.0:8082  0.0.0.0:*  users:(("docker-proxy",pid=1236,fd=4))

# "docker-proxy" is the process that forwards traffic from host port to container

# Alternative: use docker port command
$ docker port nginx1

80/tcp -> 0.0.0.0:8081

# Meaning: container port 80 is mapped to host port 8081 on all interfaces

# Check from docker inspect
$ docker inspect nginx1 --format='{{json .NetworkSettings.Ports}}'

{"80/tcp":[{"HostIp":"0.0.0.0","HostPort":"8081"}]}

# Clean up demo containers
$ docker rm -f apache nginx1 nginx2 nginx3 2>/dev/null
```

---

## 7.9 Port Mapping — Technical Deep Dive

```bash
# Standard mapping: all interfaces
docker run -d -p 8080:80 nginx
# Accessible from: localhost:8080, 192.168.1.x:8080, any interface

# Bind to localhost only (more secure)
docker run -d -p 127.0.0.1:8080:80 nginx
# Accessible from: localhost:8080 ONLY
# NOT accessible from other machines on the network

# Bind to specific interface
docker run -d -p 192.168.1.100:8080:80 nginx
# Only accessible via 192.168.1.100:8080

# Random host port
docker run -d -p 80 nginx
docker port <container_id>
# 80/tcp -> 0.0.0.0:32768

# UDP port mapping
docker run -d -p 53:53/udp dns-server

# Both TCP and UDP
docker run -d -p 53:53/tcp -p 53:53/udp dns-server

# Port range
docker run -d -p 8000-8010:8000-8010 my-app
```

### How Port Mapping Works Internally

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  External Request → port 8080                            │
│         │                                                │
│         ▼                                                │
│  ┌─────────────────┐                                     │
│  │   iptables NAT  │  (Docker manages these rules)       │
│  │   DNAT rule:    │                                     │
│  │   8080 → 172.17.0.2:80                                │
│  └────────┬────────┘                                     │
│           │                                              │
│           ▼                                              │
│  ┌─────────────────┐                                     │
│  │  docker0 bridge  │  (virtual bridge interface)         │
│  │  172.17.0.1      │                                     │
│  └────────┬────────┘                                     │
│           │                                              │
│  ┌────────▼────────┐                                     │
│  │   Container      │                                     │
│  │   172.17.0.2:80  │                                     │
│  │   (nginx)        │                                     │
│  └─────────────────┘                                     │
└─────────────────────────────────────────────────────────┘

# View the iptables rules Docker creates:
sudo iptables -t nat -L -n | grep 8080
# DNAT tcp -- 0.0.0.0/0 0.0.0.0/0 tcp dpt:8080 to:172.17.0.2:80
```

---

## 7.10 Multi-Network Architecture

Real applications use multiple networks for security isolation.

```bash
# Create separate networks
docker network create frontend-net
docker network create backend-net

# Frontend: accessible from outside, can reach API
docker run -d --name frontend --network frontend-net -p 80:80 my-frontend

# API: bridges frontend and backend networks
docker run -d --name api --network frontend-net my-api
docker network connect backend-net api
# API is now on BOTH networks

# Database: only on backend network (not accessible from frontend)
docker run -d --name db --network backend-net postgres:16

# Test connectivity:
# frontend → api: ✅ (both on frontend-net)
docker exec frontend ping -c 1 api    # Works

# api → db: ✅ (both on backend-net)
docker exec api ping -c 1 db          # Works

# frontend → db: ❌ (different networks)
docker exec frontend ping -c 1 db     # Fails — network isolation!
```

```
┌─────────────────────────────────────────────────┐
│                                                  │
│  frontend-net                backend-net         │
│  ┌──────────┐               ┌──────────┐        │
│  │ Frontend │               │ Database │        │
│  │ :80      │               │ :5432    │        │
│  └────┬─────┘               └────┬─────┘        │
│       │                          │               │
│       │    ┌──────────┐          │               │
│       └────│   API    │──────────┘               │
│            │ :3000    │                          │
│            └──────────┘                          │
│            (on both networks)                    │
│                                                  │
│  Frontend can reach API ✅                       │
│  API can reach Database ✅                       │
│  Frontend CANNOT reach Database ❌               │
└─────────────────────────────────────────────────┘
```

---

## 7.11 Container-to-Container Communication Patterns

### Pattern 1: Direct Communication (Same Network)

```bash
# Both containers on the same network
docker network create app-net
docker run -d --name redis --network app-net redis:7
docker run -d --name api --network app-net -e REDIS_HOST=redis my-api

# In application code:
# const redis = new Redis({ host: 'redis', port: 6379 });
# Uses container name "redis" as hostname
```

### Pattern 2: Through a Reverse Proxy

```bash
# Nginx as reverse proxy
docker network create web-net

docker run -d --name app1 --network web-net my-app-1
docker run -d --name app2 --network web-net my-app-2

docker run -d --name proxy --network web-net -p 80:80 \
  -v ./nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx
```

```nginx
# nginx.conf
upstream app1 {
    server app1:3000;    # Container name as hostname
}

upstream app2 {
    server app2:3000;
}

server {
    listen 80;

    location /api/v1/ {
        proxy_pass http://app1/;
    }

    location /api/v2/ {
        proxy_pass http://app2/;
    }
}
```

### Pattern 3: Service Mesh (Docker Compose)

```yaml
# docker-compose.yml
services:
  gateway:
    image: nginx
    ports:
      - "80:80"
    networks:
      - public

  auth-service:
    image: auth-service:1.0
    networks:
      - public
      - internal

  user-service:
    image: user-service:1.0
    networks:
      - internal

  order-service:
    image: order-service:1.0
    networks:
      - internal

  db:
    image: postgres:16
    networks:
      - internal

networks:
  public:     # Gateway and auth-service
  internal:   # All backend services
```

---

## 7.12 Debugging Network Issues

```bash
# Tool 1: Check container's network settings
docker inspect --format='{{json .NetworkSettings.Networks}}' my-container | python3 -m json.tool

# Tool 2: Check DNS resolution
docker exec my-container nslookup other-container
# If this fails, containers are on different networks

# Tool 3: Check connectivity
docker exec my-container ping -c 3 other-container
docker exec my-container wget -qO- http://other-container:3000/health

# Tool 4: Check what ports are listening inside container
docker exec my-container netstat -tlnp
# or
docker exec my-container ss -tlnp

# Tool 5: Check iptables rules (port mapping issues)
sudo iptables -t nat -L -n --line-numbers

# Tool 6: Use a network debugging container
docker run -it --network my-network nicolaka/netshoot
# netshoot has: curl, ping, dig, nslookup, tcpdump, iperf, etc.

# Inside netshoot:
dig database                    # DNS lookup
curl http://api:3000/health     # HTTP test
tcpdump -i eth0 port 5432      # Capture traffic
iperf -c api -p 5001           # Bandwidth test

# Tool 7: Check which networks a container is on
docker inspect --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' my-container
# Output: frontend-net backend-net
```

---

## 7.13 Real-World Industry Example: Microservices Network Architecture

```yaml
# docker-compose.yml — Microservices with proper network isolation

services:
  # ─── Edge Layer ────────────────────────────────
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - edge
    restart: unless-stopped

  # ─── API Gateway ──────────────────────────────
  api-gateway:
    build: ./services/gateway
    networks:
      - edge
      - services
    environment:
      AUTH_SERVICE_URL: http://auth-service:3001
      USER_SERVICE_URL: http://user-service:3002
      ORDER_SERVICE_URL: http://order-service:3003
    restart: unless-stopped

  # ─── Microservices ────────────────────────────
  auth-service:
    build: ./services/auth
    networks:
      - services
      - data
    environment:
      REDIS_URL: redis://redis:6379
      DB_URL: postgresql://auth:pass@postgres:5432/auth_db
    restart: unless-stopped

  user-service:
    build: ./services/users
    networks:
      - services
      - data
    environment:
      DB_URL: postgresql://users:pass@postgres:5432/users_db
    restart: unless-stopped

  order-service:
    build: ./services/orders
    networks:
      - services
      - data
      - messaging
    environment:
      DB_URL: postgresql://orders:pass@postgres:5432/orders_db
      RABBITMQ_URL: amqp://rabbit:pass@rabbitmq:5672
    restart: unless-stopped

  notification-service:
    build: ./services/notifications
    networks:
      - messaging
    environment:
      RABBITMQ_URL: amqp://rabbit:pass@rabbitmq:5672
      SMTP_HOST: mailserver
    restart: unless-stopped

  # ─── Data Layer ───────────────────────────────
  postgres:
    image: postgres:16-alpine
    networks:
      - data
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    networks:
      - data
    restart: unless-stopped

  # ─── Messaging Layer ──────────────────────────
  rabbitmq:
    image: rabbitmq:3-management-alpine
    networks:
      - messaging
    restart: unless-stopped

networks:
  edge:        # nginx ↔ api-gateway
  services:    # api-gateway ↔ microservices
  data:        # microservices ↔ databases
  messaging:   # microservices ↔ message broker

volumes:
  postgres-data:
```

```
Network Isolation Diagram:

  Internet
     │
     ▼
┌─────────┐
│  nginx  │ ── edge network ──┐
└─────────┘                    │
                          ┌────▼──────┐
                          │ API       │
                          │ Gateway   │ ── services network ──┐
                          └───────────┘                        │
                     ┌──────────┬──────────┬──────────────────┤
                     ▼          ▼          ▼                   │
                ┌────────┐ ┌────────┐ ┌────────┐              │
                │ Auth   │ │ User   │ │ Order  │              │
                │Service │ │Service │ │Service │              │
                └───┬────┘ └───┬────┘ └──┬──┬──┘              │
                    │          │         │  │                  │
              data network ────┘─────────┘  │                 │
                    │                       │                  │
              ┌─────▼─────┐          ┌─────▼──────┐           │
              │ PostgreSQL│          │ RabbitMQ   │           │
              │ Redis     │          │            │           │
              └───────────┘          └─────┬──────┘           │
                                           │ messaging network│
                                     ┌─────▼──────┐           │
                                     │Notification│           │
                                     │ Service    │           │
                                     └────────────┘           │

Key: nginx CANNOT reach PostgreSQL (different networks)
     Notification service CANNOT reach PostgreSQL
     Only services on the "data" network can access databases
```

---

## 7.14 Common Errors and Troubleshooting

### Error 1: "Could not resolve host"
```bash
$ docker exec api curl http://database:5432
# curl: (6) Could not resolve host: database

# CAUSE: Containers are on different networks, or using default bridge

# Fix 1: Ensure both containers are on the same user-defined network
docker network inspect my-network
# Check if both containers are listed

# Fix 2: Connect container to the correct network
docker network connect my-network api
```

### Error 2: "Connection refused" Between Containers
```bash
# CAUSE 1: Target service isn't listening on the expected port
docker exec target-container ss -tlnp
# Check if the port is actually open

# CAUSE 2: Service is binding to 127.0.0.1 instead of 0.0.0.0
# Fix: Configure the service to listen on 0.0.0.0

# CAUSE 3: Firewall rules blocking traffic
sudo iptables -L -n | grep DROP
```

### Error 3: "Network not found"
```bash
$ docker run --network my-network nginx
# Error: network my-network not found

# Fix: Create the network first
docker network create my-network

# Or check for typos
docker network ls
```

### Error 4: "Address already in use" (IP Conflict)
```bash
# CAUSE: Two networks with overlapping subnets

# Fix: Create networks with specific, non-overlapping subnets
docker network create --subnet=172.20.0.0/16 network-a
docker network create --subnet=172.21.0.0/16 network-b
```

### Error 5: Container Can't Access Internet
```bash
# CAUSE: DNS or routing issue

# Fix 1: Check DNS
docker exec my-container cat /etc/resolv.conf
docker exec my-container nslookup google.com

# Fix 2: Check IP forwarding on host
sysctl net.ipv4.ip_forward
# Should be 1. If 0:
sudo sysctl -w net.ipv4.ip_forward=1

# Fix 3: Check Docker daemon DNS config
cat /etc/docker/daemon.json
# Add: { "dns": ["8.8.8.8", "8.8.4.4"] }
sudo systemctl restart docker
```

---

## 7.15 Host Network Restrictions Apply to Containers

A container's network traffic ultimately goes through the host networking stack. If the host can't access something, the container can't either.

```
┌─────────────────────────────────────────────────────────────┐
│                    THE RULE                                   │
│                                                              │
│  Container traffic → goes through → Host network stack      │
│                                                              │
│  If the HOST can't reach a destination,                     │
│  the CONTAINER can't reach it either.                       │
│                                                              │
│  The container doesn't have its own physical NIC.           │
│  It uses virtual interfaces that route through the host.    │
└─────────────────────────────────────────────────────────────┘
```

### Example Scenario: Database IP Allowlisting

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Database Server (db.example.com)                           │
│  Firewall allows inbound from: 10.0.0.50, 10.0.0.51       │
│                                                              │
│  Your Docker Host: 10.0.0.20                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Container A (172.17.0.2)                             │   │
│  │  Tries to connect to db.example.com:5432             │   │
│  │                                                       │   │
│  │  Traffic path:                                        │   │
│  │  Container (172.17.0.2)                              │   │
│  │    → docker0 bridge                                  │   │
│  │    → NAT (source IP becomes 10.0.0.20)               │   │
│  │    → Host eth0 (10.0.0.20)                           │   │
│  │    → Network → db.example.com                        │   │
│  │                                                       │   │
│  │  DB sees connection from: 10.0.0.20                  │   │
│  │  DB allowlist: 10.0.0.50, 10.0.0.51                  │   │
│  │  Result: ❌ CONNECTION REFUSED                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Fix: Add 10.0.0.20 to the DB firewall allowlist            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Demonstrating this with commands:**

```bash
# Check what IP the outside world sees from your container
$ docker run --rm alpine wget -qO- ifconfig.me
203.0.113.45    # ← This is the HOST's public IP, not the container's

# The container's internal IP (172.17.0.x) is never seen externally
$ docker run --rm alpine ip addr show eth0
    inet 172.17.0.2/16 scope global eth0
# This IP only exists inside the Docker network

# If the host can't reach a service, the container can't either:
$ docker run --rm alpine ping -c 2 unreachable-server.example.com
ping: bad address 'unreachable-server.example.com'
# Same result as running ping from the host
```

### The Windows Host + Linux Container + Database Question

A common question: "If my Docker host is Windows but my container is Linux, and the database only allows Linux connections, will it work?"

```
┌─────────────────────────────────────────────────────────────┐
│                    IMPORTANT NUANCE                          │
│                                                              │
│  Most databases DON'T check the client's OS.                │
│  They check:                                                │
│                                                              │
│  ✅ IP address / subnet / security group rules              │
│  ✅ Username and password authentication                    │
│  ✅ TLS certificate validation                              │
│  ✅ Network segmentation (VPC, VLAN)                        │
│                                                              │
│  ❌ They do NOT check "is this client running Linux?"       │
│                                                              │
│  With Docker Desktop on Windows:                            │
│  • Linux containers run behind WSL2/VM networking           │
│  • The DB sees traffic from the HOST's IP address           │
│  • The DB doesn't know or care about the container's OS     │
│                                                              │
│  Access control should be designed around:                   │
│  • IP / subnet / security group rules                       │
│  • Authentication credentials                               │
│  • Encryption (TLS/SSL)                                     │
│  • Network segmentation                                     │
│  — NOT the client OS.                                       │
└─────────────────────────────────────────────────────────────┘
```

**Practical example — verifying outbound IP:**

```bash
# On Windows with Docker Desktop (Linux containers via WSL2)
$ docker run --rm alpine wget -qO- ifconfig.me
203.0.113.45    # ← This is the Windows host's public IP

# The database sees 203.0.113.45, not "Linux" or "Windows"
# It doesn't matter what OS the container runs — the network
# identity is determined by the host's network configuration
```

---

## 7.16 Port Mapping Practice Lab

Run this lab to practice port mapping concepts hands-on.

```bash
# ─── Step 1: Run Apache on host port 80 ─────────────────
$ docker run -d --name apache -p 80:80 httpd

$ curl http://localhost:80
<html><body><h1>It works!</h1></body></html>

# ─── Step 2: Run nginx on host port 8081 ────────────────
$ docker run -d --name nginx1 -p 8081:80 nginx

$ curl http://localhost:8081
<!DOCTYPE html>... Welcome to nginx! ...

# ─── Step 3: Run second nginx on host port 8082 ─────────
$ docker run -d --name nginx2 -p 8082:80 nginx

$ curl http://localhost:8082
<!DOCTYPE html>... Welcome to nginx! ...

# ─── Step 4: Verify all port mappings ────────────────────
$ docker ps --format "table {{.Names}}\t{{.Ports}}"

NAMES    PORTS
apache   0.0.0.0:80->80/tcp
nginx1   0.0.0.0:8081->80/tcp
nginx2   0.0.0.0:8082->80/tcp

# ─── Step 5: Try a port conflict (expect error) ─────────
$ docker run -d --name nginx-fail -p 80:80 nginx

# Error:
# docker: Error response from daemon: driver failed programming external
# connectivity on endpoint nginx-fail: Bind for 0.0.0.0:80 failed:
# port is already allocated.

# Port 80 is already used by Apache — can't reuse it

# ─── Step 6: Verify with ss/netstat ─────────────────────
$ ss -lntp | grep -E "80|8081|8082"

LISTEN  0  4096  0.0.0.0:80    0.0.0.0:*  users:(("docker-proxy",...))
LISTEN  0  4096  0.0.0.0:8081  0.0.0.0:*  users:(("docker-proxy",...))
LISTEN  0  4096  0.0.0.0:8082  0.0.0.0:*  users:(("docker-proxy",...))

# ─── Cleanup ────────────────────────────────────────────
$ docker rm -f apache nginx1 nginx2
```

---

## 7.17 Concept Map: Port Mapping + Volumes

```
┌─────────────────────────────────────────────────────────────┐
│              CONCEPT MAP: EXTERNAL ACCESS + DATA             │
│                                                              │
│  Application inside container:                              │
│  • Listens on a container port (80, 8080, 3306, etc.)      │
│  • Writes data to container filesystem                      │
│                                                              │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  EXTERNAL ACCESS requires:                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Host IP is reachable from the network            │   │
│  │  2. Host port is open in firewall / security group   │   │
│  │  3. docker -p HOST:CONTAINER maps traffic            │   │
│  │  4. App is actually listening on CONTAINER port      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  PERSISTENT DATA requires:                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Volume maps container folder to persistent       │   │
│  │     storage (-v HOST_PATH:CONTAINER_PATH)            │   │
│  │  2. Data survives container removal/recreation       │   │
│  │  3. Host can access data directly (logs, backups)    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  COMBINED EXAMPLE (Jenkins):                                │
│  docker run -d \                                            │
│    -p 8080:8080 \           ← port mapping (access)        │
│    -v /data/jenkins:/var/jenkins_home \  ← volume (data)   │
│    --name jenkins jenkins/jenkins:lts                       │
│                                                              │
│  Result:                                                    │
│  • Users access Jenkins at http://host-ip:8080             │
│  • Jenkins data persists at /data/jenkins on the host      │
│  • Delete container → data still on host                   │
│  • Recreate container with same -v → data restored         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.18 Container-to-Container Communication Using IP

Containers on the same bridge network can communicate using IP addresses.

```bash
# Run two containers on the default bridge
$ docker run -d --name container1 alpine sleep infinity
$ docker run -d --name container2 alpine sleep infinity

# Find Container B's IP
$ docker inspect container2 --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
172.17.0.3

# From Container A, ping Container B using IP
$ docker exec container1 ping -c 3 172.17.0.3
PING 172.17.0.3 (172.17.0.3): 56 data bytes
64 bytes from 172.17.0.3: seq=0 ttl=64 time=0.1 ms
64 bytes from 172.17.0.3: seq=1 ttl=64 time=0.1 ms
64 bytes from 172.17.0.3: seq=2 ttl=64 time=0.1 ms

# ✅ Container A can talk to Container B using IP

# Cleanup
$ docker rm -f container1 container2
```

---

## 7.19 The Problem with Using IP Addresses

Container IPs are **dynamic** — they change when containers restart. This makes IP-based communication unreliable.

```bash
# Run a container
$ docker run -d --name myapp alpine sleep infinity

# Check its IP
$ docker inspect myapp --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
172.17.0.2

# Stop and restart
$ docker stop myapp
$ docker start myapp

# Check IP again — it may have changed!
$ docker inspect myapp --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
172.17.0.4
# ⚠️  IP changed from 172.17.0.2 to 172.17.0.4

$ docker rm -f myapp
```

```
┌─────────────────────────────────────────────────────────────┐
│              WHY IP-BASED COMMUNICATION IS BAD               │
│                                                              │
│  Problem:                                                   │
│  - Container IPs are assigned dynamically by Docker         │
│  - IPs change when containers restart                       │
│  - Hardcoding IPs in config files breaks on restart         │
│                                                              │
│  Solution:                                                  │
│  - Use a CUSTOM NETWORK with DNS name resolution            │
│  - Containers communicate using NAMES, not IPs             │
│  - Names don't change — even if IPs do                     │
│                                                              │
│  docker network create mynetwork                            │
│  docker run --network mynetwork --name db mysql             │
│  docker run --network mynetwork --name app myapp            │
│  → app connects to "db" by name, not by IP                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.20 How Port Mapping Works Internally — NAT Rules

Docker uses **iptables NAT rules** to forward traffic from host ports to container ports.

```
┌─────────────────────────────────────────────────────────────┐
│              PORT MAPPING INTERNAL FLOW (NAT)                │
│                                                              │
│  docker run -p 8080:80 nginx                                │
│                                                              │
│  Browser request: http://host-ip:8080                       │
│     │                                                        │
│     ▼                                                        │
│  Host receives traffic on port 8080                         │
│     │                                                        │
│     ▼                                                        │
│  Docker's iptables NAT rule:                                │
│  DNAT → redirect 8080 → 172.17.0.2:80                      │
│     │                                                        │
│     ▼                                                        │
│  Container receives traffic on port 80                      │
│     │                                                        │
│     ▼                                                        │
│  nginx serves the response                                  │
│     │                                                        │
│     ▼                                                        │
│  Response flows back through NAT → host → browser           │
│                                                              │
│  Traffic flow:                                              │
│  Browser → Host:8080 → Docker NAT → Container:80 → nginx   │
└─────────────────────────────────────────────────────────────┘
```

```bash
# View the actual iptables rules Docker creates
$ sudo iptables -t nat -L -n | grep 8080
DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80

# This rule says: any traffic to host port 8080 → forward to 172.17.0.2:80
```

---

## 7.21 Real-World Example: Web Application with Custom Network

A typical web application has frontend, backend, and database containers — all connected via a custom network.

```bash
# Step 1: Create a custom network
$ docker network create appnet

# Step 2: Run database container
$ docker run -d \
    --network appnet \
    --name database \
    -e MYSQL_ROOT_PASSWORD=secret \
    mysql

# Step 3: Run backend container
$ docker run -d \
    --network appnet \
    --name backend \
    -e DB_HOST=database \
    node:20-alpine sleep infinity

# Step 4: Run frontend container with port mapping
$ docker run -d \
    --network appnet \
    --name frontend \
    -p 80:80 \
    nginx

# Containers communicate using names:
# frontend → backend (by name "backend")
# backend → database (by name "database")

# Verify name resolution works
$ docker exec backend ping -c 2 database
PING database (172.18.0.2): 56 data bytes
64 bytes from 172.18.0.2: seq=0 ttl=64 time=0.1 ms

$ docker exec backend ping -c 2 frontend
PING frontend (172.18.0.4): 56 data bytes
64 bytes from 172.18.0.4: seq=0 ttl=64 time=0.1 ms

# Cleanup
$ docker rm -f frontend backend database
$ docker network rm appnet
```

```
┌─────────────────────────────────────────────────────────────┐
│              CUSTOM NETWORK: appnet                          │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │   frontend     │  │   backend      │  │  database     │  │
│  │   (nginx)      │  │   (node)       │  │  (mysql)      │  │
│  │   port 80      │  │                │  │  port 3306    │  │
│  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              │                              │
│                         appnet                              │
│                    (custom bridge)                           │
│                                                              │
│  DNS resolution:                                            │
│  frontend → resolves to 172.18.0.4                          │
│  backend  → resolves to 172.18.0.3                          │
│  database → resolves to 172.18.0.2                          │
│                                                              │
│  Port mapping: -p 80:80 on frontend only                    │
│  (only frontend needs external access)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.22 Complete Network Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              COMPLETE DOCKER NETWORK FLOW                     │
│                                                              │
│                      Internet                                │
│                         │                                    │
│                         │                                    │
│           ┌─────────────┴─────────────┐                     │
│           │       Host Machine         │                     │
│           │                            │                     │
│           │     Docker Engine          │                     │
│           │         │                  │                     │
│           │    ┌────┴────┐             │                     │
│           │    │ docker0 │ (bridge)    │                     │
│           │    └────┬────┘             │                     │
│           │         │                  │                     │
│           │    Custom Network          │                     │
│           │    (appnet)                │                     │
│           │         │                  │                     │
│           │    ┌────┼────────┐         │                     │
│           │    │    │        │         │                     │
│           │  ┌─┴──┐ ┌─┴──┐ ┌─┴──┐    │                     │
│           │  │ FE │ │ BE │ │ DB │    │                     │
│           │  │:80 │ │    │ │:3306│    │                     │
│           │  └────┘ └────┘ └────┘    │                     │
│           │                            │                     │
│           │  Port Mapping:             │                     │
│           │  Host:80 → FE:80           │                     │
│           │                            │                     │
│           └────────────────────────────┘                     │
│                                                              │
│  External user → Host:80 → NAT → Frontend:80               │
│  Frontend → Backend (by name, via custom network)           │
│  Backend → Database (by name, via custom network)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.23 Networking Command Summary

```bash
# ─── NETWORK MANAGEMENT ────────────────────────────────────

# List all networks
$ docker network ls

# Create a custom network
$ docker network create mynetwork

# Inspect a network (see containers, IPs, subnet)
$ docker network inspect mynetwork

# Remove a network
$ docker network rm mynetwork

# Remove all unused networks
$ docker network prune

# ─── CONNECTING CONTAINERS ─────────────────────────────────

# Run container in a specific network
$ docker run -d --network mynetwork --name myapp nginx

# Connect a running container to a network
$ docker network connect mynetwork container1

# Disconnect a container from a network
$ docker network disconnect mynetwork container1

# ─── PORT MAPPING ──────────────────────────────────────────

# Map host port to container port
$ docker run -d -p 8080:80 nginx

# Map to specific interface
$ docker run -d -p 127.0.0.1:8080:80 nginx

# Check port mappings
$ docker port container_name

# ─── DEBUGGING ─────────────────────────────────────────────

# Check container IP
$ docker inspect container_name --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

# Ping between containers
$ docker exec container1 ping -c 2 container2

# DNS lookup
$ docker exec container1 nslookup container2

# Check network interfaces inside container
$ docker exec container1 ip addr
```

---

## 7.24 Networking Interview Questions

```
┌──────────────────────────────────────────────────────────────┐
│  DOCKER NETWORKING INTERVIEW Q&A                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Q: How do containers communicate with each other?          │
│  A: Containers on the same Docker network can communicate   │
│     using IP addresses or container names. On custom        │
│     (user-defined) networks, Docker provides automatic      │
│     DNS resolution — containers use names, not IPs.         │
│                                                              │
│  Q: Why use a custom network instead of the default bridge? │
│  A: Custom networks provide automatic DNS resolution        │
│     (containers can reach each other by name). The default  │
│     bridge only supports IP-based communication, and IPs    │
│     change on restart.                                       │
│                                                              │
│  Q: Why is port mapping required?                           │
│  A: Container ports are isolated in their own network       │
│     namespace. Port mapping (-p HOST:CONTAINER) creates     │
│     a NAT rule that forwards traffic from a host port       │
│     to the container port, making the app accessible.       │
│                                                              │
│  Q: What is the difference between bridge, host, and none?  │
│  A: bridge = isolated network with NAT (default).           │
│     host = container shares host's network stack directly   │
│     (no isolation, no port mapping needed).                  │
│     none = no networking at all (complete isolation).        │
│                                                              │
│  Q: What happens to container IPs when containers restart?  │
│  A: Container IPs are dynamic — they can change on restart. │
│     That's why you should use container names (DNS) on      │
│     custom networks instead of hardcoding IPs.              │
│                                                              │
│  Q: How does Docker implement port mapping internally?      │
│  A: Docker creates iptables NAT (DNAT) rules that redirect │
│     traffic from the host port to the container's internal  │
│     IP and port.                                             │
│                                                              │
│  Q: Can two containers use the same host port?              │
│  A: No. Each host port can only be mapped to one container. │
│     Use different host ports for multiple instances.         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7.25 Macvlan Network — Container as Physical Device

Macvlan gives a container its own MAC address. The container behaves like a physical device on the LAN.

### Create Macvlan Network

```bash
$ docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    mymacvlan
```

### Run Container on Macvlan

```bash
$ docker run -d --name myserver --network mymacvlan --ip 192.168.1.100 nginx
```

### Use Cases

```
┌─────────────────────────────────────────────────────────────┐
│  When to use macvlan:                                       │
│                                                              │
│  ✅ Legacy applications that need direct LAN access         │
│  ✅ Applications that must appear as physical devices       │
│  ✅ When containers need routable IPs on the LAN            │
│                                                              │
│  ⚠️  Requires promiscuous mode on the host NIC              │
│  ⚠️  Not supported on all cloud providers                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.26 Overlay Network — Multi-Host Communication

Used with Docker Swarm. Allows containers across different machines to communicate securely.

```bash
# Create overlay network (requires Swarm mode)
$ docker network create -d overlay myoverlay

# Services on this network can communicate across hosts
$ docker service create --name web --network myoverlay nginx
```

```
┌─────────────────────────────────────────────────────────────┐
│  Overlay network:                                           │
│                                                              │
│  ✅ Multi-host container communication                      │
│  ✅ Encrypted traffic between nodes                         │
│  ✅ Built-in DNS resolution                                 │
│  ✅ Used in Docker Swarm and orchestration                  │
│                                                              │
│  Requires: Docker Swarm mode active                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.27 Network Security Considerations

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK SECURITY BEST PRACTICES                 │
│                                                              │
│  1. Avoid --net=host unless required                        │
│     Removes network isolation entirely                      │
│                                                              │
│  2. Use user-defined bridge networks                        │
│     Better isolation + DNS + control                        │
│                                                              │
│  3. Never expose database ports publicly                    │
│     DB should only be reachable from app containers         │
│     Use internal-only networks for backend services         │
│                                                              │
│  4. Limit published ports                                   │
│     Only expose what external users need (e.g., 80, 443)   │
│                                                              │
│  5. Bind to 127.0.0.1 for local-only access                │
│     docker run -p 127.0.0.1:8080:80 nginx                  │
│                                                              │
│  6. Use separate networks for frontend/backend              │
│     Frontend network: web + api                             │
│     Backend network: api + db                               │
│     Web cannot reach db directly                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 7.28 Network Driver Comparison Table

```
┌──────────────────┬──────────────┬──────────────┬──────────┬──────────┬──────────┐
│ Feature          │ Default      │ User-Defined │ Host     │ Overlay  │ Macvlan  │
│                  │ Bridge       │ Bridge       │          │          │          │
├──────────────────┼──────────────┼──────────────┼──────────┼──────────┼──────────┤
│ Auto DNS         │ ❌           │ ✅           │ N/A      │ ✅       │ ❌       │
│ Isolation        │ Medium       │ High         │ Low      │ High     │ Medium   │
│ Multi-host       │ ❌           │ ❌           │ ❌       │ ✅       │ ❌       │
│ Port mapping     │ ✅ required  │ ✅ required  │ ❌       │ ✅       │ ❌       │
│ Name resolution  │ ❌           │ ✅           │ N/A      │ ✅       │ ❌       │
│ Use case         │ Simple dev   │ Production   │ Perf/    │ Swarm    │ Legacy/  │
│                  │              │              │ monitor  │ cluster  │ LAN      │
└──────────────────┴──────────────┴──────────────┴──────────┴──────────┴──────────┘
```

---

## Module 7 Summary

- Docker networking enables container↔container, container↔host, and container↔internet communication
- Docker has 5 network drivers: bridge, host, none, overlay, macvlan
- Always use **user-defined bridge networks** (not the default bridge)
- User-defined networks provide automatic DNS resolution by container name
- Container IPs are dynamic — they change on restart; use names instead
- Use multiple networks for security isolation (frontend/backend separation)
- `docker network connect/disconnect` adds/removes containers from networks live
- Containers have isolated network namespaces — apps inside are not directly reachable externally
- Port mapping (`-p HOST:CONTAINER`) bridges host network to container network
- Docker implements port mapping using iptables NAT (DNAT) rules
- Left side of `-p` = host port (user accesses); right side = container port (app listens)
- Host port must be free — two containers cannot share the same host port
- Container port must match what the app actually listens on
- Multiple instances of the same app need different host ports
- Docker alone doesn't load-balance — use a reverse proxy or orchestration (Swarm/K8s)
- Port mapping does NOT bypass firewalls — cloud security groups must also allow the port
- Container IPs (172.17.x.x) are internal only — not reachable from outside the host
- Use `ss -lntp` or `docker port` to verify port mappings on the host
- Port mapping uses iptables NAT rules under the hood
- Bind to `127.0.0.1` for local-only access; `0.0.0.0` for all interfaces
- Use `nicolaka/netshoot` container for network debugging
- Services must bind to `0.0.0.0` inside containers (not `127.0.0.1`)
- Container traffic goes through the host network stack — host restrictions apply to containers
- **Macvlan** gives containers their own MAC address — used for legacy apps needing direct LAN access
- **Overlay** enables multi-host communication in Docker Swarm with encrypted traffic
- **Security**: avoid `--net=host`, don't expose DB ports, use separate frontend/backend networks, bind to `127.0.0.1` for local-only

---

**Next Module: [Module 8 - Docker Volumes and Data Persistence](module-08-volumes.md)**
