# Module 16: Network Tools and Diagnostics

## 8.5 `ss` — Socket Statistics (replaces `netstat`)

### Show listening TCP ports

```bash
$ ss -tlnp
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN  0       511     0.0.0.0:80            0.0.0.0:*          users:(("nginx",pid=789,fd=6))
LISTEN  0       128     0.0.0.0:22            0.0.0.0:*          users:(("sshd",pid=456,fd=3))
LISTEN  0       244     127.0.0.1:5432        0.0.0.0:*          users:(("postgres",pid=2345,fd=5))
LISTEN  0       128     0.0.0.0:443           0.0.0.0:*          users:(("nginx",pid=789,fd=7))
```

**Explanation**:
- `-t` — TCP sockets
- `-l` — listening (waiting for connections)
- `-n` — show port numbers (not service names)
- `-p` — show process using the socket

Key observations:
- Nginx listens on ports 80 and 443 on all interfaces (`0.0.0.0`)
- PostgreSQL listens on port 5432 only on localhost (`127.0.0.1`) — not accessible from outside
- SSH listens on port 22 on all interfaces

### Show all TCP connections

```bash
$ ss -tnp
State    Recv-Q  Send-Q  Local Address:Port    Peer Address:Port   Process
ESTAB    0       0       172.17.0.2:22         10.0.0.5:54321      users:(("sshd",pid=1234,fd=3))
ESTAB    0       0       172.17.0.2:80         192.168.1.100:45678 users:(("nginx",pid=890,fd=10))
TIME-WAIT 0      0       172.17.0.2:80         192.168.1.101:45679
```

**Explanation**: Shows active connections. `ESTAB` = established connection. `TIME-WAIT` = connection recently closed (waiting for cleanup).

### Show UDP sockets

```bash
$ ss -ulnp
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
UNCONN  0       0       127.0.0.53:53         0.0.0.0:*          users:(("systemd-resolve",pid=300,fd=12))
```

### Show socket summary

```bash
$ ss -s
Total: 156
TCP:   12 (estab 3, closed 2, orphaned 0, timewait 2)
Transport Total     IP        IPv6
RAW       0         0         0
UDP       2         2         0
TCP       10        8         2
INET      12        10        2
FRAG      0         0         0
```

### `netstat` (legacy, still widely used)

```bash
$ netstat -tlnp
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      789/nginx
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      456/sshd
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      2345/postgres
```

---

## 8.6 `curl` — Transfer Data

### Basic GET request

```bash
$ curl http://example.com
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
...
```

### Show response headers (`-I`)

```bash
$ curl -I https://api.github.com
HTTP/2 200
server: GitHub.com
date: Wed, 05 Feb 2025 15:00:00 GMT
content-type: application/json; charset=utf-8
x-ratelimit-limit: 60
x-ratelimit-remaining: 58
```

**Explanation**: `-I` sends a HEAD request, showing only headers. Useful for checking status codes, content types, and rate limits.

### Show headers AND body (`-i`)

```bash
$ curl -i https://api.github.com/zen
HTTP/2 200
content-type: text/plain;charset=utf-8

Responsive is better than fast.
```

### Verbose output (`-v`)

```bash
$ curl -v https://example.com 2>&1 | head -20
*   Trying 93.184.216.34:443...
* Connected to example.com (93.184.216.34) port 443
* TLS handshake completed
> GET / HTTP/2
> Host: example.com
> User-Agent: curl/7.81.0
> Accept: */*
>
< HTTP/2 200
< content-type: text/html; charset=UTF-8
```

**Explanation**: `-v` shows the full request/response cycle including TLS handshake. `>` lines are sent, `<` lines are received.

### POST request with JSON

```bash
$ curl -X POST https://api.example.com/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN123" \
  -d '{"name": "John", "email": "john@example.com"}'

{"id": 42, "name": "John", "email": "john@example.com", "created_at": "2025-02-05T15:00:00Z"}
```

**Explanation**:
- `-X POST` — HTTP method
- `-H` — add headers
- `-d` — request body data

### Download a file

```bash
$ curl -O http://example.com/file.tar.gz         # Save with original name
$ curl -o output.pdf https://example.com/a.pdf   # Save with custom name
$ curl -L -O https://example.com/redirect-file   # Follow redirects
```

**Explanation**: `-O` saves with the remote filename. `-o` specifies a local filename. `-L` follows HTTP redirects (301/302). Useful for downloading installers, artifacts, configs, and test files.

### Silent mode with status code

```bash
$ curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health
200
```

**Explanation**: `-s` suppresses progress bar, `-o /dev/null` discards body, `-w "%{http_code}"` prints only the status code. Perfect for health checks in scripts.

### POST form data

```bash
$ curl -X POST https://example.com/login \
  -d "username=admin&password=secret"
```

### Upload a file

```bash
$ curl -X POST https://api.example.com/upload \
  -F "file=@/path/to/document.pdf"
```

---

## 8.7 `wget` — Download Files

```bash
# Download a file
$ wget https://example.com/file.tar.gz
--2025-02-05 15:00:00--  https://example.com/file.tar.gz
Resolving example.com... 93.184.216.34
Connecting to example.com|93.184.216.34|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 15728640 (15M) [application/gzip]
Saving to: 'file.tar.gz'

file.tar.gz         100%[===================>]  15.00M  5.00MB/s    in 3.0s

2025-02-05 15:00:03 (5.00 MB/s) - 'file.tar.gz' saved [15728640/15728640]
```

### Common options

```bash
# Save with custom name
$ wget -O file.zip http://example.com/file.zip

# Download in background
$ wget -b https://example.com/large-file.iso

# Resume interrupted download
$ wget -c https://example.com/large-file.iso

# Quiet mode (for scripts)
$ wget -q https://example.com/file.tar.gz

# Download entire website (mirror)
$ wget --mirror --convert-links --page-requisites https://example.com
```

### `curl` vs `wget`

| Feature              | `curl`                    | `wget`                    |
|----------------------|---------------------------|---------------------------|
| Protocols            | HTTP, FTP, SMTP, and more | HTTP, FTP                 |
| API interaction      | Excellent                 | Limited                   |
| File download        | Good                      | Excellent                 |
| Resume downloads     | Manual                    | Built-in (`-c`)           |
| Recursive download   | No                        | Yes (`--mirror`)          |
| Scripting            | Preferred                 | Good                      |

---

## 8.8 `scp` and `rsync` — File Transfer

### `scp` — Secure Copy

```bash
# Copy file to remote server
$ scp -v file.pdf user@host:/tmp/
Executing: program /usr/bin/ssh host host, user user, command sftp
file.pdf                                      100%  245     1.2KB/s   00:00

# Copy file to remote server
$ scp file.pdf user@host:/tmp/
file.pdf                                      100%  245     1.2KB/s   00:00

# Copy directory recursively
$ scp -r documents user@host:.

# Copy file from remote to local
$ scp user@host:/var/log/app.log .

# Use specific SSH key
$ scp -i ~/.ssh/prod_key deploy.sh devops@server:/opt/
```

**Explanation**: `scp` copies files over SSH. The `:` separates the host from the remote path. `.` means current directory. `-r` copies directories recursively. Useful for pulling logs and moving artifacts between servers.

### `rsync` — Efficient file sync

```bash
# Sync local to remote
$ rsync -avz ./project/ devops@server:/opt/project/
sending incremental file list
./
src/app.js
src/config.yaml
sent 1,234 bytes  received 89 bytes  2,646.00 bytes/sec
total size is 5,678  speedup is 4.29
```

**Explanation**:
- `-a` — archive mode (preserves permissions, timestamps, symlinks)
- `-v` — verbose
- `-z` — compress during transfer
- rsync only transfers changed files, making it much faster than `scp` for repeated syncs

```bash
# Dry run (show what would change)
$ rsync -avzn ./project/ devops@server:/opt/project/

# Delete files on destination that don't exist on source
$ rsync -avz --delete ./project/ devops@server:/opt/project/

# Exclude patterns
$ rsync -avz --exclude='node_modules' --exclude='.git' ./project/ devops@server:/opt/project/

# Show progress
$ rsync -avz --progress ./large-file.tar.gz devops@server:/backup/
```

---


## 8.11 `netstat` — Network Statistics (Legacy but Common)

`netstat` is deprecated in favor of `ss`, but you'll still encounter it in older systems, scripts, and documentation. Install via `sudo apt install net-tools`.

### Show listening ports

```bash
$ netstat -tlnp
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      456/sshd
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      789/nginx
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      3456/java
tcp6       0      0 :::5432                 :::*                    LISTEN      2345/postgres
```

**Explanation**: `-t`=TCP, `-l`=listening, `-n`=numeric (don't resolve names), `-p`=show PID/program. Same info as `ss -tlnp` but in the older format.

### Show all connections with state

```bash
$ netstat -ant
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 172.17.0.2:8080         10.0.0.5:52340          ESTABLISHED
tcp        0      0 172.17.0.2:8080         10.0.0.5:52341          ESTABLISHED
tcp        0      0 172.17.0.2:8080         192.168.1.100:48920     TIME_WAIT
tcp        0      0 172.17.0.2:22           10.0.0.5:55123          ESTABLISHED
```

### Show network statistics

```bash
$ netstat -s | head -20
Ip:
    Forwarding: 1
    45678 total packets received
    0 forwarded
    0 incoming packets discarded
    45678 incoming packets delivered
    40000 requests sent out
Tcp:
    1234 active connection openings
    567 passive connection openings
    12 failed connection attempts
    5 connection resets received
    8 connections established
    35000 segments received
    32000 segments sent out
    100 segments retransmitted
```

**Explanation**: Retransmitted segments indicate network issues. High retransmission rate = packet loss or congestion.

### `netstat` vs `ss` quick reference

| Task                    | `netstat`          | `ss`              |
|-------------------------|--------------------|--------------------|
| Listening TCP ports     | `netstat -tlnp`    | `ss -tlnp`        |
| All connections         | `netstat -ant`     | `ss -ant`         |
| UDP ports               | `netstat -ulnp`    | `ss -ulnp`        |
| Statistics              | `netstat -s`       | `ss -s`           |
| Interface stats         | `netstat -i`       | `ip -s link`      |

---

## 8.12 `traceroute` and `mtr` — Trace Network Path

### `traceroute` — Show the route packets take

```bash
$ traceroute google.com
traceroute to google.com (142.250.80.46), 30 hops max, 60 byte packets
 1  gateway (172.17.0.1)  0.5 ms  0.4 ms  0.3 ms
 2  isp-router (10.0.0.1)  1.2 ms  1.1 ms  1.0 ms
 3  core-router.isp.net (203.0.113.1)  5.5 ms  5.3 ms  5.2 ms
 4  * * *
 5  edge-router.google.com (72.14.236.1)  10.2 ms  10.1 ms  10.0 ms
 6  google.com (142.250.80.46)  10.5 ms  10.3 ms  10.2 ms
```

**Explanation**: Each line is a "hop" (router) along the path. Three timing values show round-trip time. `* * *` means that router doesn't respond to traceroute probes (common for firewalled routers — not necessarily a problem).

### `traceroute` with TCP (bypasses firewalls)

```bash
$ sudo traceroute -T -p 443 google.com
```

**Explanation**: Some firewalls block ICMP/UDP traceroute. `-T` uses TCP SYN packets on port 443, which are rarely blocked.

### `mtr` — Continuous traceroute with statistics

```bash
$ mtr -r -c 10 google.com
                             My traceroute  [v0.95]
server (172.17.0.2) -> google.com (142.250.80.46)    2025-02-05T15:00:00+0000
Keys:  Host                                Loss%   Snt   Last   Avg  Best  Wrst StDev
  1.  gateway                               0.0%    10    0.5   0.4   0.3   0.6   0.1
  2.  isp-router                            0.0%    10    1.2   1.1   0.9   1.5   0.2
  3.  core-router.isp.net                  10.0%    10    5.5   5.8   5.0   8.2   1.0
  4.  ???                                  100.0%    10    0.0   0.0   0.0   0.0   0.0
  5.  edge-router.google.com                0.0%    10   10.2  10.3  10.0  10.8   0.3
  6.  google.com                            0.0%    10   10.5  10.4  10.1  10.9   0.3
```

**Explanation**: `-r` = report mode, `-c 10` = send 10 probes. `Loss%` shows packet loss at each hop. Hop 3 has 10% loss — this is where the network problem is. `mtr` combines `traceroute` and `ping` into one tool.

---

## 8.13 `nslookup` — DNS Lookup (Interactive)

```bash
$ nslookup google.com
Server:         8.8.8.8
Address:        8.8.8.8#53

Non-authoritative answer:
Name:   google.com
Address: 142.250.80.46
Name:   google.com
Address: 2607:f8b0:4004:800::200e
```

**Explanation**: Shows the DNS server used (8.8.8.8) and the resolved IP addresses (both IPv4 and IPv6). "Non-authoritative" means the answer came from a cache, not directly from Google's DNS servers.

### Query specific record types

```bash
# MX records (mail servers)
$ nslookup -type=MX gmail.com
gmail.com       mail exchanger = 5 gmail-smtp-in.l.google.com.
gmail.com       mail exchanger = 10 alt1.gmail-smtp-in.l.google.com.

# NS records (name servers)
$ nslookup -type=NS example.com
example.com     nameserver = a.iana-servers.net.
example.com     nameserver = b.iana-servers.net.

# TXT records (SPF, DKIM, verification)
$ nslookup -type=TXT example.com
example.com     text = "v=spf1 include:_spf.google.com ~all"
```

### Query a specific DNS server

```bash
$ nslookup example.com 1.1.1.1
Server:         1.1.1.1
Address:        1.1.1.1#53

Name:   example.com
Address: 93.184.216.34
```

**Explanation**: Useful for testing if a DNS change has propagated to different DNS providers.

### `nslookup` vs `dig`

| Feature          | `nslookup`              | `dig`                    |
|------------------|-------------------------|--------------------------|
| Output format    | Simple, human-readable  | Detailed, script-friendly|
| Default install  | Most systems            | May need `dnsutils`      |
| Scripting        | Limited                 | Preferred                |
| Detail level     | Basic                   | Full DNS response        |

---

## 8.14 `tcpdump` — Packet Capture

`tcpdump` captures raw network packets. The most powerful network debugging tool.

### Capture packets on an interface

```bash
$ sudo tcpdump -i eth0 -c 5
15:00:01.123456 IP 172.17.0.2.8080 > 10.0.0.5.52340: Flags [P.], seq 1:100, ack 1, length 99
15:00:01.123789 IP 10.0.0.5.52340 > 172.17.0.2.8080: Flags [.], ack 100, length 0
15:00:01.234567 IP 172.17.0.2.22 > 10.0.0.5.55123: Flags [P.], seq 1:50, ack 1, length 49
15:00:01.345678 ARP, Request who-has 172.17.0.1 tell 172.17.0.2, length 28
15:00:01.345890 ARP, Reply 172.17.0.1 is-at 02:42:ac:11:00:01, length 28
```

**Explanation**: `-i eth0` = capture on eth0, `-c 5` = stop after 5 packets. Shows source/destination IPs, ports, TCP flags, and packet sizes.

### Filter by host, port, or protocol

```bash
# Only traffic to/from a specific host
$ sudo tcpdump -i eth0 host 10.0.0.5

# Only traffic on port 80
$ sudo tcpdump -i eth0 port 80

# Only TCP SYN packets (new connections)
$ sudo tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'

# Only DNS traffic
$ sudo tcpdump -i eth0 port 53

# Combine filters
$ sudo tcpdump -i eth0 'host 10.0.0.5 and port 8080'
```

### Capture with readable output

```bash
# Show packet contents in ASCII
$ sudo tcpdump -i eth0 -A port 80 -c 3
15:00:01.123456 IP 10.0.0.5.52340 > 172.17.0.2.80: Flags [P.], length 120
GET /api/health HTTP/1.1
Host: server.example.com
User-Agent: curl/7.81.0
Accept: */*

# Show in hex and ASCII
$ sudo tcpdump -i eth0 -XX port 80 -c 1
```

### Save capture to file (for Wireshark analysis)

```bash
# Capture to file
$ sudo tcpdump -i eth0 -w /tmp/capture.pcap -c 1000

# Read from file
$ sudo tcpdump -r /tmp/capture.pcap | head -20

# Capture with rotation (10 files of 100MB each)
$ sudo tcpdump -i eth0 -w /tmp/capture.pcap -C 100 -W 10
```

**Explanation**: `.pcap` files can be opened in Wireshark for graphical analysis. `-C 100` rotates after 100MB, `-W 10` keeps max 10 files.

---

## 8.15 `nmap` — Network Scanner

`nmap` scans networks to discover hosts and open ports. Install with `sudo apt install nmap`.

### Scan open ports on a host

```bash
$ nmap 192.168.1.100
Starting Nmap 7.93 ( https://nmap.org )
Nmap scan report for 192.168.1.100
Host is up (0.001s latency).
Not shown: 997 closed ports
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
8080/tcp open  http-proxy

Nmap done: 1 IP address (1 host up) scanned in 1.23 seconds
```

### Scan specific ports

```bash
$ nmap -p 22,80,443,8080 192.168.1.100
$ nmap -p 1-1024 192.168.1.100          # Port range
$ nmap -p- 192.168.1.100                 # All 65535 ports
```

### Scan a subnet (discover hosts)

```bash
$ nmap -sn 192.168.1.0/24
Nmap scan report for 192.168.1.1
Host is up (0.001s latency).
Nmap scan report for 192.168.1.100
Host is up (0.002s latency).
Nmap scan report for 192.168.1.101
Host is up (0.003s latency).

Nmap done: 256 IP addresses (3 hosts up) scanned in 2.50 seconds
```

**Explanation**: `-sn` = ping scan only (no port scan). Discovers which hosts are alive on the network.

### Service version detection

```bash
$ nmap -sV 192.168.1.100
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.4
80/tcp   open  http    nginx 1.18.0
443/tcp  open  ssl/http nginx 1.18.0
8080/tcp open  http    Apache Tomcat 9.0.65
```

**Explanation**: `-sV` probes open ports to determine the service and version. Useful for security audits and inventory.

> ⚠️ **Warning**: Only scan networks you own or have permission to scan. Unauthorized port scanning may violate laws and policies.

---

## 8.16 `iftop` and `nload` — Real-Time Bandwidth Monitoring

### `iftop` — Per-connection bandwidth

```bash
$ sudo iftop -i eth0
                    12.5Kb          25.0Kb          37.5Kb          50.0Kb
└───────────────────┴───────────────┴───────────────┴───────────────┘
server              => 10.0.0.5                       5.00Kb  4.50Kb  4.20Kb
                    <=                                 2.50Kb  2.30Kb  2.10Kb
server              => db-server                      15.0Kb  12.0Kb  10.0Kb
                    <=                                 8.00Kb  7.50Kb  7.00Kb
────────────────────────────────────────────────────────────────────────────
TX:             cum:   500KB   peak:   50.0Kb  rates:   20.0Kb  16.5Kb  14.2Kb
RX:                    250KB           25.0Kb           10.5Kb   9.80Kb  9.10Kb
TOTAL:                 750KB           75.0Kb           30.5Kb  26.3Kb  23.3Kb
```

**Explanation**: Shows bandwidth usage per connection in real-time. `=>` is outgoing, `<=` is incoming. Three columns show 2s, 10s, and 40s averages. Install with `sudo apt install iftop`.

### `nload` — Per-interface bandwidth graph

```bash
$ nload eth0
Device eth0 [172.17.0.2] (1/1):
========================================================
Incoming:
                        ####
                        ####
                        ########
                        ########
Curr: 5.20 MBit/s
Avg:  3.80 MBit/s
Min:  0.50 MBit/s
Max:  12.5 MBit/s
Ttl:  45.0 GByte

Outgoing:
                   ##
                   ####
                   ####
Curr: 2.10 MBit/s
Avg:  1.50 MBit/s
Min:  0.20 MBit/s
Max:  8.00 MBit/s
Ttl:  20.0 GByte
```

**Explanation**: Visual ASCII graph of bandwidth usage. Install with `sudo apt install nload`.

---

## 8.17 `nc` (netcat) — Network Swiss Army Knife

### Test if a port is open

```bash
$ nc -zv db-server 5432
Connection to db-server 5432 port [tcp/postgresql] succeeded!

$ nc -zv db-server 5432 -w 3
# -w 3 = timeout after 3 seconds
```

### Scan a range of ports

```bash
$ nc -zv server 20-25
Connection to server 22 port [tcp/ssh] succeeded!
```

### Transfer a file

```bash
# On receiving end:
$ nc -l -p 9999 > received_file.tar.gz

# On sending end:
$ nc server 9999 < file.tar.gz
```

### Simple chat / test server

```bash
# Start a listener (simple server)
$ nc -l -p 8080

# Connect from another terminal
$ nc localhost 8080
Hello from client
# (appears on the server side)
```

**Explanation**: `nc` is useful for quick connectivity tests, file transfers, and debugging network services without installing additional tools.

---

## 8.18 `telnet` — Test TCP Connectivity (Legacy)

```bash
# Test if a port is open
$ telnet db-server 5432
Trying 192.168.1.50...
Connected to db-server.
Escape character is '^]'.
# Connection successful — press Ctrl+] then type 'quit'

$ telnet db-server 5433
Trying 192.168.1.50...
telnet: Unable to connect to remote host: Connection refused
# Port 5433 is not open
```

**Explanation**: `telnet` is deprecated for remote login but still useful for quick port testing. Use `nc -zv` as a modern alternative. Install with `sudo apt install telnet`.

---

## 8.19 `host` — Simple DNS Lookup

```bash
$ host google.com
google.com has address 142.250.80.46
google.com has IPv6 address 2607:f8b0:4004:800::200e
google.com mail is handled by 10 smtp.google.com.

$ host 142.250.80.46
46.80.250.142.in-addr.arpa domain name pointer lax17s55-in-f14.1e100.net.

# Query specific record type
$ host -t MX gmail.com
gmail.com mail is handled by 5 gmail-smtp-in.l.google.com.

$ host -t NS example.com
example.com name server a.iana-servers.net.
```

**Explanation**: `host` is simpler than `dig` and `nslookup`. Good for quick lookups. Reverse lookup (IP to hostname) works with just the IP address.

---

## 8.20 `ethtool` — Network Interface Details

```bash
$ sudo ethtool eth0
Settings for eth0:
        Supported link modes:   10baseT/Half 10baseT/Full
                                100baseT/Half 100baseT/Full
                                1000baseT/Full
        Speed: 1000Mb/s
        Duplex: Full
        Auto-negotiation: on
        Link detected: yes

# Check for errors
$ sudo ethtool -S eth0 | grep -i error
     rx_errors: 0
     tx_errors: 0
     rx_crc_errors: 0
     rx_frame_errors: 0
```

**Explanation**: `ethtool` shows physical network interface details — speed, duplex, link status. Useful for diagnosing hardware-level network issues. Install with `sudo apt install ethtool`.

---

## 8.21 More `curl` Examples

```bash
# Test response time
$ curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTotal: %{time_total}s\nHTTP Code: %{http_code}\n" https://api.example.com/health
DNS: 0.012s
Connect: 0.025s
TLS: 0.089s
Total: 0.105s
HTTP Code: 200

# Test with specific HTTP method and timeout
$ curl -X GET -m 5 http://localhost:8080/api/users
# -m 5 = timeout after 5 seconds

# Send JSON with authentication
$ curl -s https://api.example.com/data \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "status"}' | jq .

# Download with progress bar
$ curl -# -O https://example.com/large-file.tar.gz

# Test SSL certificate
$ curl -vI https://example.com 2>&1 | grep -E "expire|subject|issuer"
*  subject: CN=example.com
*  expire date: Mar 15 12:00:00 2026 GMT
*  issuer: C=US; O=Let's Encrypt; CN=R3

# Retry on failure
$ curl --retry 3 --retry-delay 5 http://api.example.com/health
```

---

## 8.22 More `ping` Examples

```bash
# Basic connectivity test (alt domain example)
$ ping google.co.in
# (runs continuously until Ctrl+C)

$ ping -c 4 google.co.in
PING google.co.in (142.250.190.99) 56(84) bytes of data.
64 bytes from 142.250.190.99: icmp_seq=1 ttl=116 time=11.1 ms

# Ping with specific packet size (test MTU)
$ ping -s 1472 -c 3 -M do 192.168.1.1
# -s 1472 = packet size, -M do = don't fragment
# If this fails, MTU is too large

# Flood ping (stress test, requires root)
$ sudo ping -f -c 1000 192.168.1.1
--- 192.168.1.1 ping statistics ---
1000 packets transmitted, 998 received, 0.2% packet loss

# Ping with timestamp
$ ping -c 5 -D google.com
[1738764000.123456] 64 bytes from 142.250.80.46: icmp_seq=1 ttl=118 time=10.5 ms

# Set TTL (useful for traceroute-like behavior)
$ ping -c 1 -t 5 google.com
```

---

## 8.23 Practical DevOps Scenarios

### Scenario 1: Debug connectivity issues

```bash
# 1. Check if interface is up
$ ip -br addr

# 2. Check default gateway
$ ip route

# 3. Ping gateway
$ ping -c 2 172.17.0.1

# 4. Ping external host
$ ping -c 2 8.8.8.8

# 5. Check DNS resolution
$ dig google.com +short

# 6. Trace the route
$ traceroute google.com

# 7. Check if port is open on remote host
$ curl -v telnet://db-server:5432
```

### Scenario 2: Check what's listening on a port

```bash
$ sudo ss -tlnp | grep :8080
LISTEN  0  128  0.0.0.0:8080  0.0.0.0:*  users:(("node",pid=3456,fd=18))

# If port is in use and you need to free it
$ sudo kill 3456
```

### Scenario 3: Health check script

```bash
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health)
if [ "$STATUS" -eq 200 ]; then
    echo "Service is healthy"
else
    echo "Service is DOWN (HTTP $STATUS)"
    # Send alert
fi
```

### Scenario 4: Transfer deployment artifacts

```bash
# Sync build artifacts to production servers
$ rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    ./dist/ devops@prod-server:/opt/myapp/current/
```

### Scenario 5: Debug high network traffic

```bash
# Step 1: Check overall bandwidth
$ sar -n DEV 1 3
IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s
eth0    50000.0   45000.0   50000.0   30000.0
# 50 MB/s incoming — unusually high

# Step 2: Find which connections are using bandwidth
$ sudo iftop -i eth0 -n
# Shows per-connection bandwidth in real-time

# Step 3: Find which process is responsible
$ sudo nethogs eth0
NetHogs version 0.8.7
  PID USER     PROGRAM                      DEV        SENT      RECEIVED
 3456 myapp    java                         eth0      30.0 MB/s  50.0 MB/s
  890 www-data nginx                        eth0       5.0 MB/s   2.0 MB/s

# Step 4: Capture packets for analysis
$ sudo tcpdump -i eth0 -w /tmp/traffic.pcap -c 10000
# Open in Wireshark for detailed analysis
```

### Scenario 6: DNS resolution failing

```bash
# Step 1: Check if DNS is configured
$ cat /etc/resolv.conf
nameserver 8.8.8.8
nameserver 8.8.4.4

# Step 2: Test DNS resolution
$ nslookup api.example.com
;; connection timed out; no servers could be reached

# Step 3: Try a different DNS server
$ nslookup api.example.com 1.1.1.1
Name:   api.example.com
Address: 93.184.216.34
# Works with Cloudflare DNS — your configured DNS server is down

# Step 4: Check if it's a network issue to the DNS server
$ ping -c 2 8.8.8.8
PING 8.8.8.8: 100% packet loss

# Step 5: Fix — update DNS servers
$ sudo sed -i 's/8.8.8.8/1.1.1.1/' /etc/resolv.conf

# Step 6: Verify
$ dig api.example.com +short
93.184.216.34
```

### Scenario 7: Too many connections in TIME_WAIT

```bash
# Step 1: Count connection states
$ ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
  15000 TIME-WAIT
    500 ESTAB
     10 LISTEN

# Step 2: TIME_WAIT is consuming ephemeral ports
# Tune kernel parameters
$ sudo sysctl -w net.ipv4.tcp_tw_reuse=1
$ sudo sysctl -w net.ipv4.tcp_fin_timeout=15

# Make persistent
$ echo "net.ipv4.tcp_tw_reuse=1" | sudo tee -a /etc/sysctl.conf
$ echo "net.ipv4.tcp_fin_timeout=15" | sudo tee -a /etc/sysctl.conf
$ sudo sysctl -p
```

---

## 8.24 Sample File + Output Walkthrough

Use a sample access log to practice command chaining used in real incidents.

### Sample File

```bash
$ cat /tmp/access.log
2026-02-20T10:00:01Z 10.0.0.10 GET /health 200 12ms
2026-02-20T10:00:02Z 10.0.0.11 GET /api/users 500 310ms
2026-02-20T10:00:03Z 10.0.0.10 GET /api/users 200 45ms
2026-02-20T10:00:04Z 10.0.0.12 GET /api/orders 504 1200ms
2026-02-20T10:00:05Z 10.0.0.11 GET /api/users 500 290ms
```

### Commands, Output, and Meaning

```bash
$ grep " 500 " /tmp/access.log
2026-02-20T10:00:02Z 10.0.0.11 GET /api/users 500 310ms
2026-02-20T10:00:05Z 10.0.0.11 GET /api/users 500 290ms
```

**Explanation**: Quickly isolates failed requests.

```bash
$ awk '{print $2}' /tmp/access.log | sort | uniq -c | sort -nr
      2 10.0.0.11
      2 10.0.0.10
      1 10.0.0.12
```

**Explanation**: Shows top client IPs by request count.

```bash
$ awk '$6 ~ /^5/ {print $2, $4, $6, $7}' /tmp/access.log
10.0.0.11 /api/users 500 310ms
10.0.0.12 /api/orders 504 1200ms
10.0.0.11 /api/users 500 290ms
```

**Explanation**: Extracts only 5xx failures with endpoint and latency.

### Real-life use case

During an API outage, this is the exact pattern to identify the failing endpoint, noisy client IP, and severity before you open packet captures.

### Troubleshooting checklist

- Confirm service is listening: `ss -tlnp | grep :PORT`
- Confirm DNS resolution: `dig +short service.domain`
- Confirm route and gateway: `ip route`
- Confirm packet path: `traceroute target`
- Confirm failures in logs: `grep " 5.. " /tmp/access.log`

---



## 8.26 Network Bandwidth Testing with iperf3

`iperf3` measures network throughput between two hosts.

```bash
# Install
sudo apt install iperf3        # Debian/Ubuntu
sudo yum install iperf3        # RHEL/CentOS

# On the server (listener)
iperf3 -s

# On the client (sender)
iperf3 -c <server_ip>

# Test UDP throughput
iperf3 -c <server_ip> -u -b 100M

# Reverse test (server sends to client)
iperf3 -c <server_ip> -R

# Run for 30 seconds
iperf3 -c <server_ip> -t 30
```

Sample output:
```
[ ID] Interval           Transfer     Bitrate
[  5]   0.00-10.00  sec  1.10 GBytes   943 Mbits/sec    sender
[  5]   0.00-10.00  sec  1.10 GBytes   942 Mbits/sec    receiver
```

**Real-world use**: Verify network capacity between application servers, test VPN throughput, or diagnose slow transfers between data centers.

---


---

## 12.8 Networking Tools for Troubleshooting

### `tcpdump` — Packet capture

```bash
# Capture packets on eth0
$ sudo tcpdump -i eth0 -c 10
15:00:00.000001 IP 192.168.1.100.45678 > web-server.80: Flags [S], seq 1234567890
15:00:00.000002 IP web-server.80 > 192.168.1.100.45678: Flags [S.], seq 987654321, ack 1234567891

# Filter by port
$ sudo tcpdump -i eth0 port 80 -c 20

# Filter by host
$ sudo tcpdump -i eth0 host 192.168.1.100

# Save to file for Wireshark analysis
$ sudo tcpdump -i eth0 -w capture.pcap -c 1000

# Read from file
$ sudo tcpdump -r capture.pcap
```

### `nc` (netcat) — Network Swiss Army knife

```bash
# Test if a port is open
$ nc -zv db-server 5432
Connection to db-server 5432 port [tcp/postgresql] succeeded!

# Port scan
$ nc -zv web-server 80-443
Connection to web-server 80 port [tcp/http] succeeded!
Connection to web-server 443 port [tcp/https] succeeded!

# Simple file transfer
# Receiver:
$ nc -l 9999 > received_file.tar.gz
# Sender:
$ nc receiver-host 9999 < file.tar.gz

# Simple chat / test connectivity
# Server:
$ nc -l 9999
# Client:
$ nc server-host 9999
```

### `nmap` — Network scanner

```bash
# Scan common ports
$ nmap 192.168.1.50
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
5432/tcp open  postgresql

# Scan specific ports
$ nmap -p 80,443,8080 192.168.1.50

# Scan a subnet
$ nmap -sn 192.168.1.0/24    # Ping scan (host discovery)

# Service version detection
$ nmap -sV 192.168.1.50
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1
80/tcp   open  http    nginx 1.18.0
```

---

