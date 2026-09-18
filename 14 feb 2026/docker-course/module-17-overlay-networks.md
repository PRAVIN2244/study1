# Module 17: Overlay Network Internals

---

## 17.1 The Problem — Containers on Different Hosts

Bridge networks work on a single host. In a Swarm cluster, containers run on different machines. They need to communicate as if they were on the same network.

```
┌─────────────────────────────────────────────────────────────┐
│              THE MULTI-HOST PROBLEM                          │
│                                                              │
│  Host A (192.168.1.10)        Host B (192.168.1.20)        │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │ Container: web   │        │ Container: db    │          │
│  │ 172.17.0.2       │   ?    │ 172.17.0.2       │          │
│  └──────────────────┘        └──────────────────┘          │
│                                                              │
│  Problem:                                                   │
│  • Both containers have 172.17.0.2 (same subnet, diff host)│
│  • Bridge networks are local to each host                  │
│  • Containers can't reach each other directly              │
│                                                              │
│  Solution: Overlay network                                  │
│  • Creates a virtual network spanning multiple hosts       │
│  • Containers get unique IPs on the overlay subnet         │
│  • Traffic is encapsulated (VXLAN) and sent over host net  │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.2 What is an Overlay Network?

An overlay network creates a virtual Layer 2 network on top of the physical (underlay) network. Containers on different hosts appear to be on the same LAN.

```
┌─────────────────────────────────────────────────────────────┐
│              OVERLAY NETWORK ARCHITECTURE                    │
│                                                              │
│  Overlay Network (10.0.0.0/24) — virtual, spans hosts      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  Host A                      Host B                  │   │
│  │  ┌──────────┐               ┌──────────┐            │   │
│  │  │ web      │               │ db       │            │   │
│  │  │ 10.0.0.2 │               │ 10.0.0.3 │            │   │
│  │  └────┬─────┘               └────┬─────┘            │   │
│  │       │                          │                   │   │
│  └───────┼──────────────────────────┼───────────────────┘   │
│          │                          │                       │
│  ┌───────┴──────────────────────────┴───────────────────┐   │
│  │         Physical Network (192.168.1.0/24)            │   │
│  │    Host A: 192.168.1.10    Host B: 192.168.1.20      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  web (10.0.0.2) pings db (10.0.0.3):                       │
│    1. Packet created: src=10.0.0.2, dst=10.0.0.3           │
│    2. VXLAN encapsulates: outer src=192.168.1.10,           │
│       outer dst=192.168.1.20                                │
│    3. Sent over physical network                            │
│    4. Host B decapsulates, delivers to db container         │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.3 VXLAN — How Overlay Traffic Travels

VXLAN (Virtual Extensible LAN) is the encapsulation protocol used by Docker overlay networks.

```
┌─────────────────────────────────────────────────────────────┐
│              VXLAN ENCAPSULATION                             │
│                                                              │
│  Original packet (from container):                          │
│  ┌──────────────────────────────────────────┐               │
│  │ Ethernet │ IP: 10.0.0.2→10.0.0.3 │ Data │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  After VXLAN encapsulation:                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Outer    │ Outer IP:          │ UDP   │ VXLAN │ Orig │   │
│  │ Ethernet │ 192.168.1.10 →     │ :4789 │ Header│ Pkt  │   │
│  │          │ 192.168.1.20       │       │ VNI   │      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  VNI (VXLAN Network Identifier):                            │
│    Unique ID for each overlay network                       │
│    Allows multiple overlay networks on same infrastructure  │
│                                                              │
│  UDP Port 4789:                                             │
│    Standard VXLAN port                                      │
│    Must be open between Swarm nodes                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.4 Creating and Using Overlay Networks

### Prerequisites

```bash
# Overlay networks require Swarm mode
$ docker swarm init
# Swarm initialized: current node is now a manager.
```

### Create an Overlay Network

```bash
# Create overlay network
$ docker network create --driver overlay my-overlay

# Output:
# a1b2c3d4e5f6

# List networks
$ docker network ls
# NETWORK ID     NAME         DRIVER    SCOPE
# abc123         bridge       bridge    local
# def456         host         host      local
# ghi789         none         null      local
# jkl012         ingress      overlay   swarm    ← built-in
# a1b2c3         my-overlay   overlay   swarm    ← our network

# Inspect the overlay network
$ docker network inspect my-overlay
# [
#     {
#         "Name": "my-overlay",
#         "Driver": "overlay",
#         "Scope": "swarm",
#         "IPAM": {
#             "Config": [
#                 { "Subnet": "10.0.1.0/24", "Gateway": "10.0.1.1" }
#             ]
#         }
#     }
# ]
```

### Deploy Services on the Overlay

```bash
# Create two services on the same overlay network
$ docker service create --name web --network my-overlay --replicas 2 -p 8080:80 nginx
$ docker service create --name api --network my-overlay --replicas 2 myapp:1.0

# web and api containers can communicate by service name
# Even if they run on different hosts

# From inside a web container:
$ curl http://api:3000/health
# ✅ Works — DNS resolves "api" to overlay IP
# Traffic goes through VXLAN tunnel between hosts
```

---

## 17.5 Control Plane vs Data Plane

```
┌─────────────────────────────────────────────────────────────┐
│              OVERLAY NETWORK PLANES                          │
│                                                              │
│  Control Plane (Port 2377 TCP, 7946 TCP/UDP):               │
│    • Swarm management traffic                               │
│    • Service discovery and DNS                              │
│    • Network membership and topology                        │
│    • Encrypted by default (mutual TLS)                      │
│                                                              │
│  Data Plane (Port 4789 UDP):                                │
│    • Actual container-to-container traffic                  │
│    • VXLAN encapsulated packets                             │
│    • NOT encrypted by default                               │
│    • Can be encrypted with --opt encrypted                  │
│                                                              │
│  Ports that must be open between Swarm nodes:               │
│    TCP 2377  → Cluster management                           │
│    TCP/UDP 7946 → Node communication                        │
│    UDP 4789  → Overlay data traffic (VXLAN)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.6 Encrypting Overlay Traffic

By default, overlay data plane traffic is **not encrypted**. Enable encryption for sensitive workloads.

```bash
# Create encrypted overlay network
$ docker network create --driver overlay --opt encrypted secure-overlay

# All traffic on this network is encrypted using IPsec
# Performance impact: ~10-15% overhead due to encryption
```

```
┌─────────────────────────────────────────────────────────────┐
│              ENCRYPTION COMPARISON                           │
│                                                              │
│  Without --opt encrypted:                                   │
│    Control plane: ✅ Encrypted (mutual TLS, always)         │
│    Data plane:    ❌ Plaintext VXLAN                        │
│    Performance:   Faster                                    │
│    Use for:       Trusted networks, non-sensitive data      │
│                                                              │
│  With --opt encrypted:                                      │
│    Control plane: ✅ Encrypted (mutual TLS)                 │
│    Data plane:    ✅ Encrypted (IPsec ESP)                  │
│    Performance:   ~10-15% slower                            │
│    Use for:       Sensitive data, compliance requirements   │
│                                                              │
│  ⚠️  Encryption is per-network, not per-service            │
│  ⚠️  Windows nodes do not support overlay encryption       │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.7 The Ingress Network

Docker Swarm automatically creates a special overlay network called `ingress`. It handles the **routing mesh** for published ports.

```bash
$ docker network ls --filter driver=overlay
# NETWORK ID     NAME       DRIVER    SCOPE
# abc123         ingress    overlay   swarm

$ docker network inspect ingress
# Subnet: 10.0.0.0/24
# This network is used for routing mesh load balancing
```

```
┌─────────────────────────────────────────────────────────────┐
│              INGRESS NETWORK FLOW                            │
│                                                              │
│  External request → any-node:8080                           │
│       │                                                      │
│       ▼                                                      │
│  Ingress network (overlay)                                  │
│       │                                                      │
│       ▼                                                      │
│  IPVS load balancer (in kernel)                             │
│       │                                                      │
│       ▼                                                      │
│  Routes to a task on the service's overlay network          │
│                                                              │
│  The ingress network is separate from your custom overlays  │
│  It handles ONLY published port routing                     │
│  Your service-to-service traffic uses custom overlay nets   │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.8 Service Discovery on Overlay Networks

Docker provides built-in DNS for services on overlay networks.

```bash
# Create services on the same overlay
$ docker service create --name frontend --network app-net nginx
$ docker service create --name backend --network app-net myapi:1.0

# Inside frontend container:
$ nslookup backend
# Name:    backend
# Address: 10.0.1.5

# Docker maintains a virtual IP (VIP) for each service
# The VIP load-balances across all tasks of that service

# View the VIP
$ docker service inspect backend --format='{{.Endpoint.VirtualIPs}}'
# [{a1b2c3 10.0.1.5/24}]

# Individual task IPs
$ docker service inspect backend --format='{{json .Endpoint.Ports}}'
```

### DNS Round-Robin Mode

```bash
# By default, services use VIP-based load balancing
# For DNS round-robin instead:
$ docker service create \
    --name backend \
    --network app-net \
    --endpoint-mode dnsrr \
    myapi:1.0

# DNS returns ALL task IPs instead of a single VIP
# Client picks one (round-robin at DNS level)

# VIP mode (default): single stable IP, kernel-level LB
# DNSRR mode: multiple IPs, client-side LB
```

---

## 17.9 Overlay Network Internals — What Docker Creates

When you create an overlay network and deploy a service, Docker creates several components on each node:

```bash
# On a node running a task on the overlay:
$ ip link show
# ...
# 10: vxlan0: <BROADCAST,MULTICAST,UP> ...
# 12: br0: <BROADCAST,MULTICAST,UP> ...
# 14: veth1234@if13: <BROADCAST,MULTICAST,UP> master br0 ...

# Docker creates:
#   1. A VXLAN interface (vxlan0) — tunnel endpoint
#   2. A bridge (br0) — connects local containers
#   3. veth pairs — connect containers to the bridge
#   4. The bridge connects to the VXLAN interface
```

```
┌─────────────────────────────────────────────────────────────┐
│              PER-NODE OVERLAY INTERNALS                      │
│                                                              │
│  Container                                                  │
│  ┌──────────┐                                               │
│  │ eth0     │ (veth pair)                                   │
│  └────┬─────┘                                               │
│       │                                                      │
│  ┌────┴─────────────────────────────┐                       │
│  │  br0 (namespace bridge)          │                       │
│  └────┬─────────────────────────────┘                       │
│       │                                                      │
│  ┌────┴─────────────────────────────┐                       │
│  │  vxlan0 (VXLAN tunnel endpoint)  │                       │
│  │  VNI: 4097                       │                       │
│  │  UDP port: 4789                  │                       │
│  └────┬─────────────────────────────┘                       │
│       │                                                      │
│  ┌────┴─────────────────────────────┐                       │
│  │  eth0 (host physical interface)  │                       │
│  │  192.168.1.10                    │                       │
│  └──────────────────────────────────┘                       │
│                                                              │
│  All of this is inside a separate network namespace         │
│  created by Docker for the overlay network                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 17.10 Troubleshooting Overlay Networks

### Check Overlay Network Connectivity

```bash
# Verify the overlay network exists on all nodes
$ docker network inspect my-overlay
# Check "Peers" section — lists all nodes participating

# Test connectivity between services
$ docker service create --name debug --network my-overlay nicolaka/netshoot sleep 3600

# Exec into the debug container
$ docker exec -it $(docker ps -q -f name=debug) sh

# Test DNS resolution
$ nslookup backend
# Should return the VIP

# Test connectivity
$ ping backend
$ curl http://backend:3000/health

# Check routing
$ ip route
$ traceroute backend
```

### Common Issues

```
┌─────────────────────────────────────────────────────────────┐
│              OVERLAY TROUBLESHOOTING                         │
│                                                              │
│  Problem: Containers can't communicate across hosts         │
│                                                              │
│  Check 1: Firewall ports                                    │
│    TCP 2377 — Swarm management                              │
│    TCP/UDP 7946 — Node discovery                            │
│    UDP 4789 — VXLAN data                                    │
│    $ sudo ufw status                                        │
│    $ sudo iptables -L -n                                    │
│                                                              │
│  Check 2: IP protocol 50 (for encrypted overlays)           │
│    IPsec ESP uses IP protocol 50 (not a port)              │
│    Must be allowed by firewalls/security groups             │
│                                                              │
│  Check 3: Network exists on all nodes                       │
│    $ docker network ls (on each node)                       │
│    Overlay networks are lazily created on worker nodes      │
│    They appear only when a task is scheduled there          │
│                                                              │
│  Check 4: MTU issues                                        │
│    VXLAN adds 50 bytes overhead                             │
│    If underlay MTU is 1500, overlay MTU should be 1450     │
│    $ docker network create --driver overlay                 │
│      --opt com.docker.network.driver.mtu=1450 my-overlay   │
│                                                              │
│  Check 5: DNS resolution                                    │
│    $ docker exec <container> nslookup <service_name>        │
│    If DNS fails, check embedded DNS (127.0.0.11)           │
└─────────────────────────────────────────────────────────────┘
```

### Inspecting VXLAN Traffic

```bash
# Capture VXLAN traffic on the host
$ sudo tcpdump -i eth0 -n port 4789

# Output:
# 10:30:00 IP 192.168.1.10.45678 > 192.168.1.20.4789: VXLAN, ...
# Shows encapsulated overlay traffic between hosts

# Capture decapsulated traffic inside the overlay namespace
$ sudo nsenter --net=/var/run/docker/netns/1-abc123 tcpdump -i br0
# Shows the actual container-to-container packets
```

---

## 17.11 Overlay Network Options

```bash
# Create with custom subnet
$ docker network create --driver overlay \
    --subnet 10.10.0.0/16 \
    --gateway 10.10.0.1 \
    custom-overlay

# Create with encryption
$ docker network create --driver overlay \
    --opt encrypted \
    secure-overlay

# Create with custom MTU
$ docker network create --driver overlay \
    --opt com.docker.network.driver.mtu=1400 \
    mtu-overlay

# Create attachable overlay (allows docker run, not just services)
$ docker network create --driver overlay \
    --attachable \
    dev-overlay

# Now standalone containers can join:
$ docker run -d --network dev-overlay --name test nginx
```

---

## 17.12 Overlay vs Bridge — Comparison

```
┌──────────────────┬──────────────────────────────────────────┐
│ Feature          │ Bridge              │ Overlay             │
├──────────────────┼─────────────────────┼─────────────────────┤
│ Scope            │ Single host         │ Multi-host (Swarm)  │
│ Driver           │ bridge              │ overlay             │
│ Encapsulation    │ None                │ VXLAN (UDP 4789)    │
│ Encryption       │ N/A                 │ Optional (IPsec)    │
│ DNS              │ User-defined only   │ Always              │
│ Load balancing   │ None                │ VIP or DNSRR        │
│ Requires Swarm   │ No                  │ Yes (or attachable) │
│ Performance      │ Native speed        │ Slight overhead     │
│ Use case         │ Dev, single host    │ Production cluster  │
└──────────────────┴─────────────────────┴─────────────────────┘
```

---

## Module 17 Summary

- Overlay networks create virtual Layer 2 networks spanning multiple Docker hosts
- VXLAN encapsulates container traffic inside UDP packets (port 4789) for transport over the physical network
- Each overlay network gets a unique VNI (VXLAN Network Identifier)
- Control plane (management, DNS, topology) is always encrypted via mutual TLS
- Data plane (container traffic) is plaintext by default — use `--opt encrypted` for IPsec encryption
- Swarm ports: TCP 2377 (management), TCP/UDP 7946 (node communication), UDP 4789 (VXLAN)
- The `ingress` overlay network handles routing mesh for published ports
- Custom overlay networks handle service-to-service communication
- Docker provides VIP-based load balancing (default) or DNS round-robin (`--endpoint-mode dnsrr`)
- Overlay networks are lazily created on worker nodes — they appear only when a task is scheduled
- Use `--attachable` to allow standalone containers (not just services) to join an overlay
- VXLAN adds ~50 bytes overhead — adjust MTU if needed (underlay 1500 → overlay 1450)
- Troubleshoot with: firewall checks, `docker network inspect`, `nslookup`, `tcpdump port 4789`
- Each node gets a VXLAN interface, a bridge, and veth pairs inside a dedicated network namespace

---

**Previous Module: [Module 16 - Linux Network Namespaces](module-16-network-namespaces.md)**

**Next Module: [Module 18 - Storage Drivers](module-18-storage-drivers.md)**
