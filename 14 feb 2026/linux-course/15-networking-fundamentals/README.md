# Module 15: Networking Fundamentals

## 8.1 Network Interfaces

### View IP addresses (`ip addr`)

```bash
$ ip addr show
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    link/loopback 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
    inet6 ::1/128 scope host
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 02:42:ac:11:00:02
    inet 172.17.0.2/16 brd 172.17.255.255 scope global eth0
    inet6 fe80::42:acff:fe11:2/64 scope link
```

**Explanation**:
- `lo` — loopback interface (localhost, `127.0.0.1`)
- `eth0` — primary network interface with IP `172.17.0.2`, subnet mask `/16` (255.255.0.0)
- `link/ether` — MAC address
- `mtu 1500` — Maximum Transmission Unit (largest packet size in bytes)

### Short form

```bash
$ ip -br addr
lo               UNKNOWN        127.0.0.1/8 ::1/128
eth0             UP             172.17.0.2/16 fe80::42:acff:fe11:2/64
```

**Explanation**: `-br` (brief) gives a compact view. `UP` means the interface is active.

### View routing table

```bash
$ ip route
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2
```

**Explanation**: `default via 172.17.0.1` means all traffic not matching a specific route goes through the gateway `172.17.0.1` via `eth0`.

### Add/remove IP address

```bash
# Add an IP
$ sudo ip addr add 192.168.1.100/24 dev eth0

# Remove an IP
$ sudo ip addr del 192.168.1.100/24 dev eth0

# Bring interface up/down
$ sudo ip link set eth0 up
$ sudo ip link set eth0 down
```

> Note: `ip` changes are temporary (lost on reboot). For persistent config, edit `/etc/netplan/` (Ubuntu) or `/etc/sysconfig/network-scripts/` (RHEL).

### `ifconfig` — Legacy Network Configuration

`ifconfig` is the older tool for viewing and configuring network interfaces. It's been replaced by `ip` on modern systems but is still widely used and referenced.

```bash
$ ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.17.0.2  netmask 255.255.0.0  broadcast 172.17.255.255
        inet6 fe80::42:acff:fe11:2  prefixlen 64  scopeid 0x20<link>
        ether 02:42:ac:11:00:02  txqueuelen 0  (Ethernet)
        RX packets 45000  bytes 50000000 (50.0 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 30000  bytes 25000000 (25.0 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
```

**Explanation**:
- `inet 172.17.0.2` — IPv4 address
- `netmask 255.255.0.0` — subnet mask
- `ether 02:42:ac:11:00:02` — MAC address
- `RX/TX packets` — received/transmitted packet counts
- `lo` — loopback interface (localhost)

```bash
# View a specific interface
$ ifconfig eth0

# View all interfaces (including down)
$ ifconfig -a

# Assign an IP address
$ sudo ifconfig eth0 192.168.1.100 netmask 255.255.255.0

# Bring interface up/down
$ sudo ifconfig eth0 up
$ sudo ifconfig eth0 down
```

> **Install if missing**: `ifconfig` is part of the `net-tools` package.
> ```bash
> $ sudo apt install -y net-tools      # Debian/Ubuntu
> $ sudo dnf install -y net-tools      # RHEL/CentOS
> ```

### `ifconfig` vs `ip` — Comparison

| Task                    | `ifconfig` (legacy)                        | `ip` (modern)                          |
|-------------------------|--------------------------------------------|----------------------------------------|
| Show all interfaces     | `ifconfig`                                 | `ip addr show`                         |
| Show one interface      | `ifconfig eth0`                            | `ip addr show eth0`                    |
| Assign IP               | `ifconfig eth0 192.168.1.100`              | `ip addr add 192.168.1.100/24 dev eth0`|
| Remove IP               | —                                          | `ip addr del 192.168.1.100/24 dev eth0`|
| Interface up            | `ifconfig eth0 up`                         | `ip link set eth0 up`                  |
| Interface down          | `ifconfig eth0 down`                       | `ip link set eth0 down`               |
| Show routing table      | `route -n`                                 | `ip route show`                        |

> **Recommendation**: Use `ip` for new work — it's more capable and is the standard on all modern distributions. Learn `ifconfig` because you'll encounter it in older systems, scripts, and documentation.

---

## 8.2 `ping` — Test Connectivity

```bash
$ ping -c 4 google.com
PING google.com (142.250.80.46) 56(84) bytes of data.
64 bytes from lax17s55-in-f14.1e100.net (142.250.80.46): icmp_seq=1 ttl=115 time=1.23 ms
64 bytes from lax17s55-in-f14.1e100.net (142.250.80.46): icmp_seq=2 ttl=115 time=1.18 ms
64 bytes from lax17s55-in-f14.1e100.net (142.250.80.46): icmp_seq=3 ttl=115 time=1.21 ms
64 bytes from lax17s55-in-f14.1e100.net (142.250.80.46): icmp_seq=4 ttl=115 time=1.19 ms

--- google.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 1.180/1.202/1.230/0.018 ms
```

**Explanation**:
- `-c 4` — send 4 packets (without `-c`, ping runs forever on Linux)
- `ttl=115` — Time To Live (hops remaining before packet is discarded)
- `time=1.23 ms` — round-trip time
- `0% packet loss` — all packets received (healthy connection)
- `rtt` — round-trip time statistics (min/avg/max/standard deviation)

### Ping failure examples

```bash
# Host unreachable
$ ping -c 2 192.168.1.254
From 172.17.0.1 icmp_seq=1 Destination Host Unreachable

# DNS resolution failure
$ ping -c 2 nonexistent.example.com
ping: nonexistent.example.com: Name or service not known
```

---

## 8.3 `traceroute` / `tracepath` — Trace Network Path

```bash
$ traceroute google.com
traceroute to google.com (142.250.80.46), 30 hops max, 60 byte packets
 1  gateway (172.17.0.1)  0.123 ms  0.098 ms  0.087 ms
 2  isp-router (10.0.0.1)  1.234 ms  1.198 ms  1.210 ms
 3  core-router (203.0.113.1)  5.456 ms  5.432 ms  5.445 ms
 4  * * *
 5  lax17s55-in-f14.1e100.net (142.250.80.46)  8.789 ms  8.765 ms  8.778 ms
```

**Explanation**: Shows every router (hop) between you and the destination. Each hop shows 3 round-trip times. `* * *` means that hop didn't respond (firewalled). Useful for diagnosing where network slowness or failures occur.

```bash
# Alternative (doesn't require root)
$ tracepath google.com
```

---

## 8.4 DNS Tools

### `nslookup` — Query DNS

```bash
$ nslookup google.com
Server:         127.0.0.53
Address:        127.0.0.53#53

Non-authoritative answer:
Name:   google.com
Address: 142.250.80.46
Name:   google.com
Address: 2607:f8b0:4004:800::200e
```

**Explanation**: Queries the DNS server (`127.0.0.53` — local resolver) for google.com's IP. Shows both IPv4 and IPv6 addresses. "Non-authoritative" means the answer came from a cache, not directly from Google's DNS servers.

### `dig` — Detailed DNS queries

```bash
$ dig google.com
;; ANSWER SECTION:
google.com.             300     IN      A       142.250.80.46

;; Query time: 12 msec
;; SERVER: 127.0.0.53#53(127.0.0.53)
;; MSG SIZE  rcvd: 55
```

**Explanation**: `dig` provides more detail than `nslookup`. The `300` is the TTL (time-to-live in seconds — how long the result is cached).

```bash
# Query specific record types
$ dig google.com MX          # Mail servers
;; ANSWER SECTION:
google.com.     300  IN  MX  10 smtp.google.com.

$ dig google.com NS          # Name servers
;; ANSWER SECTION:
google.com.     300  IN  NS  ns1.google.com.

$ dig google.com TXT         # TXT records (SPF, verification)

# Query a specific DNS server
$ dig @8.8.8.8 google.com

# Short output
$ dig +short google.com
142.250.80.46
```

### `host` — Simple DNS lookup

```bash
$ host google.com
google.com has address 142.250.80.46
google.com has IPv6 address 2607:f8b0:4004:800::200e
google.com mail is handled by 10 smtp.google.com.

# Reverse lookup (IP to hostname)
$ host 8.8.8.8
8.8.8.8.in-addr.arpa domain name pointer dns.google.
```

### DNS configuration files

```bash
$ cat /etc/resolv.conf
nameserver 127.0.0.53
options edns0 trust-ad
search example.com

$ cat /etc/hosts
127.0.0.1       localhost
172.17.0.2      devops-server
192.168.1.50    db-server
```

**Explanation**: `/etc/resolv.conf` configures DNS servers. `/etc/hosts` provides local hostname-to-IP mappings (checked before DNS). Adding entries to `/etc/hosts` is useful for testing without modifying DNS.

---


## 8.10 Network Configuration Files

### Hostname

```bash
$ hostname
web-server-01

# Show all IP addresses assigned to this host
$ hostname -I
192.168.1.100 172.17.0.1

$ hostnamectl set-hostname web-server-01
$ cat /etc/hostname
web-server-01
```

**Explanation**: `hostname` shows the system's hostname. `hostname -I` shows all assigned IP addresses (useful for verifying which IPs a server is reachable on). `hostnamectl` is the systemd way to set the hostname persistently.

### Static IP (Ubuntu/Netplan)

```bash
$ cat /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4

$ sudo netplan apply
```

### Static IP (RHEL/CentOS)

```bash
$ cat /etc/sysconfig/network-scripts/ifcfg-eth0
TYPE=Ethernet
BOOTPROTO=static
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=8.8.4.4
ONBOOT=yes

$ sudo systemctl restart NetworkManager
```

---


## 8.27 TCP/UDP and Network Concepts

### TCP vs UDP

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Connection-oriented (3-way handshake) | Connectionless |
| Reliability | Guaranteed delivery, ordered | Best-effort, no ordering |
| Speed | Slower (overhead) | Faster (lightweight) |
| Use cases | SSH, HTTP, Git, databases | DNS, streaming, gaming, VoIP |

### IP Addressing and Subnetting

```bash
# CIDR notation: IP/prefix
# 192.168.1.0/24 = 256 addresses (254 usable)
# 10.0.0.0/8 = 16 million addresses

# Calculate subnet details
ipcalc 192.168.1.10/24
# Output: Network, Broadcast, HostMin, HostMax, Hosts/Net

# Common subnet masks
# /8  = 255.0.0.0       (16M hosts)
# /16 = 255.255.0.0     (65K hosts)
# /24 = 255.255.255.0   (254 hosts)
# /28 = 255.255.255.240 (14 hosts)
# /32 = 255.255.255.255 (1 host — single IP)
```

### ARP — Address Resolution Protocol

ARP maps IP addresses to MAC addresses on the local network.

```bash
# View ARP cache
ip neigh
arp -n

# Clear ARP cache
sudo ip neigh flush all

# Add static ARP entry
sudo arp -s 192.168.1.100 aa:bb:cc:dd:ee:ff
```

### Key Network Configuration Files

| File | Purpose |
|------|---------|
| `/etc/hosts` | Local hostname-to-IP mapping |
| `/etc/resolv.conf` | DNS server configuration |
| `/etc/hostname` | System hostname |
| `/etc/network/interfaces` | Network config (Debian, older) |
| `/etc/netplan/*.yaml` | Network config (Ubuntu 18+) |
| `/etc/sysconfig/network-scripts/ifcfg-*` | Network config (RHEL/CentOS) |

---

