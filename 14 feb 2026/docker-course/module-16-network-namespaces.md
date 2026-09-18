# Module 16: Linux Network Namespaces Deep Dive

---

## 16.1 What Are Network Namespaces?

A network namespace is a Linux kernel feature that provides an isolated network stack. Each namespace has its own interfaces, routing table, iptables rules, and ARP table.

Docker uses network namespaces to give each container its own isolated network environment.

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK NAMESPACE ISOLATION                     │
│                                                              │
│  Host (default namespace):                                  │
│    eth0: 192.168.1.10                                       │
│    Routing table, iptables, ARP table                       │
│                                                              │
│  Container A (namespace A):                                 │
│    eth0: 172.17.0.2                                         │
│    Its own routing table, iptables, ARP table               │
│                                                              │
│  Container B (namespace B):                                 │
│    eth0: 172.17.0.3                                         │
│    Its own routing table, iptables, ARP table               │
│                                                              │
│  Each namespace is completely isolated.                     │
│  Container A cannot see Container B's interfaces.           │
│  Neither can see the host's eth0 directly.                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 16.2 Creating and Managing Network Namespaces

```bash
# Create a network namespace
$ sudo ip netns add red
$ sudo ip netns add blue

# List all network namespaces
$ sudo ip netns list
# red
# blue

# Execute a command inside a namespace
$ sudo ip netns exec red ip link
# 1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN
#    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00

# Only loopback exists — no external interfaces
# The namespace is completely isolated

# Check interfaces on the host
$ ip link
# 1: lo: <LOOPBACK,UP> ...
# 2: eth0: <BROADCAST,MULTICAST,UP> ...
# Host has eth0, but the namespace does NOT
```

---

## 16.3 Connecting Two Namespaces with veth Pairs

A **veth pair** (virtual Ethernet pair) is like a virtual cable with two ends. Placing one end in each namespace connects them.

```
┌─────────────────────────────────────────────────────────────┐
│              VETH PAIR — VIRTUAL CABLE                       │
│                                                              │
│  Namespace: red              Namespace: blue                │
│  ┌──────────────┐            ┌──────────────┐              │
│  │  veth-red     │────────────│  veth-blue   │              │
│  │  192.168.15.1 │   cable    │  192.168.15.2│              │
│  └──────────────┘            └──────────────┘              │
│                                                              │
│  Packets sent to veth-red appear at veth-blue               │
│  and vice versa — like a direct Ethernet cable              │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step: Connect Two Namespaces

```bash
# Step 1: Create a veth pair
$ sudo ip link add veth-red type veth peer name veth-blue

# This creates TWO interfaces linked together:
#   veth-red  ←→  veth-blue

# Step 2: Move each end into its namespace
$ sudo ip link set veth-red netns red
$ sudo ip link set veth-blue netns blue

# Step 3: Assign IP addresses
$ sudo ip netns exec red ip addr add 192.168.15.1/24 dev veth-red
$ sudo ip netns exec blue ip addr add 192.168.15.2/24 dev veth-blue

# Step 4: Bring interfaces up
$ sudo ip netns exec red ip link set veth-red up
$ sudo ip netns exec blue ip link set veth-blue up

# Also bring up loopback in each namespace
$ sudo ip netns exec red ip link set lo up
$ sudo ip netns exec blue ip link set lo up

# Step 5: Test connectivity
$ sudo ip netns exec red ping 192.168.15.2
# PING 192.168.15.2 (192.168.15.2) 56(84) bytes of data.
# 64 bytes from 192.168.15.2: icmp_seq=1 ttl=64 time=0.035 ms
# ✅ red can reach blue!

$ sudo ip netns exec blue ping 192.168.15.1
# 64 bytes from 192.168.15.1: icmp_seq=1 ttl=64 time=0.028 ms
# ✅ blue can reach red!
```

### Verify from Each Namespace

```bash
# Check interfaces in red namespace
$ sudo ip netns exec red ip addr
# 1: lo: <LOOPBACK,UP> ...
#     inet 127.0.0.1/8 scope host lo
# 5: veth-red@if4: <BROADCAST,MULTICAST,UP> ...
#     inet 192.168.15.1/24 scope global veth-red

# Check ARP table in red namespace
$ sudo ip netns exec red arp
# Address          HWtype  HWaddress           Flags  Iface
# 192.168.15.2     ether   aa:bb:cc:dd:ee:ff   C      veth-red
```

---

## 16.4 Connecting Multiple Namespaces with a Bridge

With two namespaces, a veth pair works. With many namespaces, you need a **bridge** — a virtual switch.

```
┌─────────────────────────────────────────────────────────────┐
│              LINUX BRIDGE — VIRTUAL SWITCH                   │
│                                                              │
│  Namespace: red     Namespace: blue    Namespace: green     │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐        │
│  │ veth-red │       │veth-blue │       │veth-green│        │
│  │ .15.1    │       │ .15.2    │       │ .15.3    │        │
│  └────┬─────┘       └────┬─────┘       └────┬─────┘        │
│       │                  │                   │              │
│  ┌────┴──────────────────┴───────────────────┴────┐        │
│  │              br0 (Linux Bridge)                 │        │
│  │              192.168.15.0/24                    │        │
│  │              Acts as a virtual switch           │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  All namespaces can communicate through the bridge          │
│  This is exactly how Docker's bridge network works          │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step: Bridge with Multiple Namespaces

```bash
# Step 1: Create the bridge
$ sudo ip link add br0 type bridge
$ sudo ip link set br0 up

# Step 2: Create namespaces
$ sudo ip netns add red
$ sudo ip netns add blue
$ sudo ip netns add green

# Step 3: Create veth pairs (one per namespace)
$ sudo ip link add veth-red type veth peer name veth-red-br
$ sudo ip link add veth-blue type veth peer name veth-blue-br
$ sudo ip link add veth-green type veth peer name veth-green-br

# Step 4: Move one end into each namespace
$ sudo ip link set veth-red netns red
$ sudo ip link set veth-blue netns blue
$ sudo ip link set veth-green netns green

# Step 5: Attach the other end to the bridge
$ sudo ip link set veth-red-br master br0
$ sudo ip link set veth-blue-br master br0
$ sudo ip link set veth-green-br master br0

# Step 6: Assign IPs inside namespaces
$ sudo ip netns exec red ip addr add 192.168.15.1/24 dev veth-red
$ sudo ip netns exec blue ip addr add 192.168.15.2/24 dev veth-blue
$ sudo ip netns exec green ip addr add 192.168.15.3/24 dev veth-green

# Step 7: Bring everything up
$ sudo ip link set veth-red-br up
$ sudo ip link set veth-blue-br up
$ sudo ip link set veth-green-br up

$ sudo ip netns exec red ip link set veth-red up
$ sudo ip netns exec red ip link set lo up

$ sudo ip netns exec blue ip link set veth-blue up
$ sudo ip netns exec blue ip link set lo up

$ sudo ip netns exec green ip link set veth-green up
$ sudo ip netns exec green ip link set lo up

# Step 8: Test — all namespaces can reach each other
$ sudo ip netns exec red ping 192.168.15.2
# ✅ red → blue

$ sudo ip netns exec red ping 192.168.15.3
# ✅ red → green

$ sudo ip netns exec blue ping 192.168.15.3
# ✅ blue → green
```

---

## 16.5 Connecting Namespaces to the Host

The bridge exists on the host, so give it an IP to allow host ↔ namespace communication.

```bash
# Assign an IP to the bridge on the host
$ sudo ip addr add 192.168.15.10/24 dev br0

# Now the host can reach namespaces
$ ping 192.168.15.1
# ✅ Host → red namespace

# And namespaces can reach the host
$ sudo ip netns exec red ping 192.168.15.10
# ✅ red namespace → host
```

---

## 16.6 Connecting Namespaces to the Outside World (Internet)

Namespaces can't reach the internet by default. You need NAT (masquerading).

```bash
# Step 1: Add default route in namespace (via bridge)
$ sudo ip netns exec red ip route add default via 192.168.15.10

# Step 2: Enable IP forwarding on the host
$ sudo sysctl -w net.ipv4.ip_forward=1

# Step 3: Add NAT rule (masquerade)
$ sudo iptables -t nat -A POSTROUTING -s 192.168.15.0/24 -j MASQUERADE

# Step 4: Test internet access from namespace
$ sudo ip netns exec red ping 8.8.8.8
# ✅ Namespace can reach the internet

$ sudo ip netns exec red curl -s ifconfig.me
# Shows the host's public IP (traffic is NATed)
```

```
┌─────────────────────────────────────────────────────────────┐
│              NAT FLOW                                        │
│                                                              │
│  Namespace (192.168.15.1)                                   │
│       │                                                      │
│       ▼  default route → 192.168.15.10 (bridge)             │
│  Bridge (br0)                                               │
│       │                                                      │
│       ▼  IP forwarding enabled                              │
│  Host (eth0: public IP)                                     │
│       │                                                      │
│       ▼  iptables MASQUERADE (source NAT)                   │
│  Internet                                                   │
│                                                              │
│  This is exactly how Docker containers reach the internet   │
└─────────────────────────────────────────────────────────────┘
```

---

## 16.7 Port Forwarding into Namespaces

To allow external traffic to reach a service inside a namespace (like Docker's `-p` flag):

```bash
# Forward host port 8080 to namespace red port 80
$ sudo iptables -t nat -A PREROUTING \
    -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.15.1:80

# Also need to allow forwarded traffic
$ sudo iptables -A FORWARD -p tcp -d 192.168.15.1 --dport 80 -j ACCEPT

# Now external traffic to host:8080 reaches namespace red:80
# This is exactly what Docker does with -p 8080:80
```

---

## 16.8 How Docker Uses Network Namespaces

Docker automates everything we did manually above.

```bash
# Run a container
$ docker run -d --name web nginx

# Find the container's network namespace
$ docker inspect web --format='{{.State.Pid}}'
# 12345

# The namespace is at /proc/<pid>/ns/net
$ sudo ls -la /proc/12345/ns/net
# lrwxrwxrwx 1 root root 0 ... /proc/12345/ns/net -> net:[4026532456]

# Enter the container's namespace using nsenter
$ sudo nsenter --target 12345 --net ip addr
# 1: lo: <LOOPBACK,UP> ...
#     inet 127.0.0.1/8
# 15: eth0@if16: <BROADCAST,MULTICAST,UP> ...
#     inet 172.17.0.2/16

# Compare with host
$ ip addr | grep docker
# 3: docker0: <BROADCAST,MULTICAST,UP> ...
#     inet 172.17.0.1/16

# Docker created:
#   1. A network namespace for the container
#   2. A veth pair (eth0 inside, vethXXX on host)
#   3. Connected veth to docker0 bridge
#   4. Assigned IP from bridge subnet
#   5. Set up NAT for internet access
```

### Viewing Docker's veth Pairs

```bash
# On the host — see the veth interface connected to docker0
$ ip link show type veth
# 16: veth1234@if15: <BROADCAST,MULTICAST,UP> master docker0 ...

# The @if15 means it's paired with interface index 15
# Inside the container, eth0 has index 15

# Verify the bridge connection
$ bridge link show
# 16: veth1234 state UP : <BROADCAST,MULTICAST,UP> master docker0
```

---

## 16.9 Inspecting Docker Network Namespaces

```bash
# Docker doesn't create symlinks in /var/run/netns/ by default
# To use ip netns commands with Docker containers:

# Create a symlink
$ container_pid=$(docker inspect -f '{{.State.Pid}}' web)
$ sudo mkdir -p /var/run/netns
$ sudo ln -sf /proc/$container_pid/ns/net /var/run/netns/web

# Now you can use ip netns commands
$ sudo ip netns exec web ip addr
$ sudo ip netns exec web ip route
$ sudo ip netns exec web iptables -L

# Clean up
$ sudo rm /var/run/netns/web
```

---

## 16.10 Cleanup

```bash
# Delete namespaces
$ sudo ip netns del red
$ sudo ip netns del blue
$ sudo ip netns del green

# Delete bridge
$ sudo ip link del br0

# Deleting a namespace automatically removes its veth endpoints
# Deleting a bridge removes attached veth-br interfaces
```

---

## 16.11 Network Namespace Commands Reference

```
┌──────────────────────────────────────────────────────────────┐
│  COMMAND                                    │ PURPOSE        │
├─────────────────────────────────────────────┼────────────────┤
│  ip netns add <name>                        │ Create NS      │
│  ip netns list                              │ List all NS    │
│  ip netns del <name>                        │ Delete NS      │
│  ip netns exec <name> <cmd>                 │ Run cmd in NS  │
│  ip link add <a> type veth peer name <b>    │ Create veth    │
│  ip link set <iface> netns <name>           │ Move to NS     │
│  ip link set <iface> master <bridge>        │ Attach to br   │
│  ip link add <name> type bridge             │ Create bridge  │
│  ip addr add <ip/mask> dev <iface>          │ Assign IP      │
│  ip link set <iface> up                     │ Bring up       │
│  ip route add default via <gw>              │ Default route  │
│  nsenter --target <pid> --net <cmd>         │ Enter PID's NS │
└─────────────────────────────────────────────┴────────────────┘
```

---

## Module 16 Summary

- A network namespace provides a completely isolated network stack (interfaces, routes, iptables, ARP)
- `ip netns add/list/del/exec` manages namespaces
- A **veth pair** is a virtual cable connecting two namespaces — packets in one end come out the other
- A **Linux bridge** acts as a virtual switch connecting multiple namespaces — this is how Docker's bridge network works
- To connect namespaces: create veth pair → move ends into namespaces → assign IPs → bring up
- For multiple namespaces: create a bridge → attach veth pairs to the bridge
- Give the bridge an IP for host ↔ namespace communication
- For internet access: add default route in namespace → enable IP forwarding → add iptables MASQUERADE
- For inbound access: add iptables DNAT rule — this is what Docker's `-p` flag does
- Docker automates all of this: creates namespace per container, veth pair, bridge attachment, IP assignment, NAT
- Use `nsenter --target <pid> --net` to enter a container's network namespace
- Use `docker inspect` to find container PID, then `/proc/<pid>/ns/net` for the namespace
- Understanding namespaces explains why containers are isolated and how Docker networking works under the hood

---

**Previous Module: [Module 15 - Docker Secrets](module-15-secrets.md)**

**Next Module: [Module 17 - Overlay Network Internals](module-17-overlay-networks.md)**
