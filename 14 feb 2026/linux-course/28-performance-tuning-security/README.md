# Module 28: Performance Tuning and Security Hardening

## 13.13 Performance Tuning

### Kernel Parameter Tuning with sysctl

`sysctl` reads and modifies kernel parameters at runtime.

```bash
# View all parameters
sysctl -a

# View a specific parameter
sysctl vm.swappiness

# Change a parameter temporarily
sudo sysctl -w vm.swappiness=10

# Persist changes in /etc/sysctl.conf
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
echo "fs.file-max=1000000" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.all.rp_filter=1" | sudo tee -a /etc/sysctl.conf

# Apply changes from config file
sudo sysctl -p
```

Common tuning parameters:

| Parameter | Default | Tuned | Purpose |
|-----------|---------|-------|---------|
| `vm.swappiness` | 60 | 10 | Reduce swap usage (keep data in RAM) |
| `fs.file-max` | 65536 | 1000000 | Max open files system-wide |
| `net.core.somaxconn` | 128 | 65535 | Max socket connection backlog |
| `net.ipv4.tcp_tw_reuse` | 0 | 1 | Reuse TIME_WAIT sockets |

### Resource Limits with ulimit

`ulimit` controls per-user resource limits.

```bash
# View all limits
ulimit -a

# View specific limits
ulimit -n          # Max open files
ulimit -u          # Max user processes

# Set limits (current session only)
ulimit -n 65535    # Increase open files
ulimit -u 4096     # Increase max processes
```

For permanent limits, edit `/etc/security/limits.conf`:

```
# <user>    <type>    <item>    <value>
devops      soft      nofile    65535
devops      hard      nofile    65535
*           soft      nproc     4096
*           hard      nproc     8192
```

### Swap Management and Hugepages

```bash
# Check swap usage
swapon --show
free -h

# Create a swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Check which processes use swap
for f in /proc/*/status; do
  awk '/VmSwap|Name/{printf $2 " " $3}END{print ""}' "$f" 2>/dev/null
done | sort -k2 -n | tail -10
```

**Hugepages** reduce TLB misses for memory-intensive applications (databases, JVMs):

```bash
# Check current hugepage settings
cat /proc/meminfo | grep Huge

# Allocate hugepages
echo 512 | sudo tee /proc/sys/vm/nr_hugepages

# Persist
echo "vm.nr_hugepages=512" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Network Performance Monitoring

```bash
# nethogs — bandwidth per process
sudo apt install nethogs
sudo nethogs eth0

# iftop — live bandwidth per interface
sudo apt install iftop
sudo iftop -i eth0

# iperf3 — test network throughput between two hosts
# On server:
iperf3 -s
# On client:
iperf3 -c <server_ip>

# nload — real-time bandwidth
sudo apt install nload
nload eth0
```

### Advanced Performance Tools

```bash
# perf — low-level CPU performance analysis
sudo apt install linux-tools-common linux-tools-$(uname -r)
perf top                    # Live CPU profiling
perf stat ./my_program      # Execution statistics
perf record ./my_program    # Record for later analysis
perf report                 # Analyze recorded data

# strace — trace system calls
strace -p <PID>             # Attach to running process
strace -c ls /tmp           # Summarize syscall counts
strace -e openat ./app      # Trace specific syscalls

# lsof — list open files
lsof -p <PID>               # Files opened by a process
lsof -i :8080               # What process uses port 8080
lsof +L1                    # Deleted files still held open (disk full mystery)

# Process priority tuning
nice -n 10 ./script.sh      # Start with lower priority
renice -n -5 -p <PID>       # Increase priority of running process
taskset -c 0,1 ./script.sh  # Pin process to specific CPU cores
cpulimit -l 50 -p <PID>     # Limit CPU usage to 50%
```

### Detecting Bottlenecks — Quick Reference

| Symptom | Suspect Area | Tools |
|---------|-------------|-------|
| High load average | CPU or I/O wait | `top`, `uptime`, `iostat` |
| Slow app startup | Disk I/O | `iotop`, `iostat` |
| OOM errors | Memory | `dmesg`, `free`, `smem` |
| Dropped packets | Network | `netstat`, `ifconfig`, `dstat` |
| App unresponsive | Process scheduling | `ps`, `top`, `nice`, `strace` |

---

## 13.14 Advanced Memory Tools

### slabtop — Kernel Slab Allocator

Shows how the kernel allocates memory for internal data structures (inodes, dentries, buffers):

```bash
sudo slabtop

# Sample output:
#  OBJS ACTIVE  USE OBJ SIZE  SLABS OBJ/SLAB CACHE SIZE NAME
# 15360  15360 100%    0.19K    768       20      3072K dentry
#  8448   8448 100%    0.58K    528       16      4224K inode_cache
```

**Real-world**: If `dentry` or `inode_cache` is consuming excessive memory, it may indicate a filesystem with millions of small files (mail queues, cache directories).

### smem — Accurate Per-Process Memory

```bash
sudo apt install smem

# Show memory by process (sorted by PSS — proportional set size)
smem -r -k -t

# PSS accounts for shared memory proportionally,
# giving a more accurate picture than RSS
```

---

## 13.15 Filesystem Performance Tuning

### tune2fs — Ext4 Filesystem Tuning

```bash
# View filesystem parameters
sudo tune2fs -l /dev/sda1

# Reduce reserved blocks (default 5% reserved for root)
sudo tune2fs -m 1 /dev/sda1    # Reduce to 1%

# Set filesystem label
sudo tune2fs -L "data" /dev/sda1

# Set maximum mount count before fsck
sudo tune2fs -c 30 /dev/sda1
```

### Mount Options for Performance

```bash
# Use noatime to reduce unnecessary disk writes
# Every file read normally updates the access timestamp — noatime disables this
sudo mount -o noatime,nodiratime /dev/sda1 /data

# Add to /etc/fstab for persistence:
UUID=xxxx /data ext4 defaults,noatime,nodiratime 0 2
```

**Real-world**: Adding `noatime` to database and log partitions can improve I/O performance by 10-30% by eliminating unnecessary metadata writes.

---

## 13.16 Historical Monitoring and Dashboards

### atop — Advanced System Monitor with History

```bash
sudo apt install atop

# Real-time monitoring
atop

# Record data every 10 seconds
sudo atop -w /var/log/atop/atop_$(date +%Y%m%d) 10

# Replay historical data
atop -r /var/log/atop/atop_20240101
```

### nmon — Performance Monitor (IBM)

```bash
sudo apt install nmon

# Interactive mode
nmon
# Press: c=CPU, m=Memory, d=Disk, n=Network, t=Top processes

# Record to file for analysis
nmon -f -s 10 -c 360    # Every 10 sec for 1 hour
```

### Monitoring Stack for Production

| Component | Purpose |
|-----------|---------|
| **Prometheus** | Metrics collection and storage |
| **Node Exporter** | Exposes Linux system metrics to Prometheus |
| **Grafana** | Visualization dashboards |
| **Telegraf** | Metrics collection agent (alternative to Node Exporter) |
| **InfluxDB** | Time-series database (alternative to Prometheus) |
| **Alertmanager** | Alert routing and notification |

```bash
# Install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-*.tar.gz
cd node_exporter-*
./node_exporter &

# Metrics available at http://localhost:9100/metrics
# Prometheus scrapes these metrics automatically
```

**Real-world**: Every production environment should have monitoring. The Prometheus + Grafana stack is the industry standard for Linux server monitoring. Set up alerts for CPU > 80%, memory > 90%, disk > 85%, and swap usage > 0.

---

## 13.17 Custom Logging in Shell Scripts

```bash
#!/bin/bash
LOGFILE="/var/log/myapp.log"

log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOGFILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOGFILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

log_info "Starting backup process"
if tar -czf /backup/data.tar.gz /var/www; then
    log_info "Backup completed successfully"
else
    log_error "Backup failed with exit code $?"
fi
```

### logwatch — Automated Log Summary Reports

```bash
sudo apt install logwatch

# Generate daily summary
sudo logwatch --detail High --range today --output stdout

# Email daily report
sudo logwatch --detail Med --mailto admin@example.com --range yesterday

# Configure in /etc/logwatch/conf/logwatch.conf
```

**Real-world**: Schedule `logwatch` via cron to receive daily email summaries of SSH logins, failed attempts, disk usage, and service errors.

---

## 13.18 Interview Questions — Module 13

**Q1: How do you troubleshoot high CPU usage in production?**

```bash
top                                   # Identify top CPU process (press P)
ps aux --sort=-%cpu | head            # Top CPU consumers
strace -p <PID>                       # What syscalls is it making?
pidstat -p <PID> 1                    # Per-process CPU over time
perf top                              # Low-level CPU profiling
```

**Q2: What is load average and how do you interpret it?**

Load average shows the number of processes waiting for CPU over 1, 5, and 15 minutes. Compare against `nproc`: load 4.0 on a 4-core system = 100% utilized. Load 8.0 on 4 cores = 2x overloaded. Increasing trend (1min > 5min > 15min) indicates growing pressure.

**Q3: How do you tune kernel parameters with sysctl?**

```bash
sysctl -a                             # View all parameters
sysctl vm.swappiness                  # View specific parameter
sudo sysctl -w vm.swappiness=10       # Change temporarily
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf  # Persist
sudo sysctl -p                        # Apply from config
```

**Q4: What is the difference between RSS, VSZ, and PSS?**

- **RSS** (Resident Set Size) — physical memory used, includes shared libraries (overcounts)
- **VSZ** (Virtual Size) — total virtual memory allocated (includes unused)
- **PSS** (Proportional Set Size) — physical memory with shared pages divided proportionally (most accurate)

Use `smem` for PSS-based reporting.

**Q5: How do you set up monitoring for production Linux servers?**

Install Prometheus Node Exporter on each server, configure Prometheus to scrape metrics, build Grafana dashboards for CPU, memory, disk, and network. Set alerts for: CPU > 80%, memory > 90%, disk > 85%, swap usage > 0, load average > 2x cores.

---

## 12.2 Log Management

### Important log files

| Log File                    | Contents                              |
|-----------------------------|---------------------------------------|
| `/var/log/syslog`           | General system messages (Debian)      |
| `/var/log/messages`         | General system messages (RHEL)        |
| `/var/log/auth.log`         | Authentication events                 |
| `/var/log/secure`           | Authentication events (RHEL)          |
| `/var/log/kern.log`         | Kernel messages                       |
| `/var/log/dmesg`            | Boot and hardware messages            |
| `/var/log/nginx/access.log` | Nginx access log                      |
| `/var/log/nginx/error.log`  | Nginx error log                       |

### `journalctl` — systemd journal

```bash
# View all logs
$ sudo journalctl

# Follow logs in real-time
$ sudo journalctl -f

# Logs for a specific service
$ sudo journalctl -u nginx

# Logs since a time
$ sudo journalctl --since "2025-02-05 10:00:00"
$ sudo journalctl --since "1 hour ago"
$ sudo journalctl --since today

# Logs between times
$ sudo journalctl --since "2025-02-05 10:00" --until "2025-02-05 12:00"

# Kernel messages only
$ sudo journalctl -k

# Show only errors and above
$ sudo journalctl -p err
$ sudo journalctl -p crit

# Output as JSON
$ sudo journalctl -u nginx -o json-pretty | head -20

# Disk usage of journal
$ sudo journalctl --disk-usage
Archived and active journals take up 256.0M in the file system.

# Clean up old logs
$ sudo journalctl --vacuum-size=100M    # Keep only 100MB
$ sudo journalctl --vacuum-time=7d      # Keep only 7 days
```

### Log rotation with `logrotate`

```bash
$ cat /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily               # Rotate daily
    missingok           # Don't error if log is missing
    rotate 14           # Keep 14 rotated files
    compress            # Compress rotated files
    delaycompress       # Compress previous rotation, not current
    notifempty          # Don't rotate empty files
    create 0640 myapp myapp  # Permissions for new log file
    sharedscripts       # Run postrotate once for all logs
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
```

```bash
# Test logrotate config
$ sudo logrotate -d /etc/logrotate.d/myapp    # Dry run
$ sudo logrotate -f /etc/logrotate.d/myapp    # Force rotation
```

---

## 12.3 Performance Monitoring & Tuning

### System overview

```bash
# Quick health check
$ uptime
 15:00:00 up 45 days,  3:12,  2 users,  load average: 0.52, 0.38, 0.25

$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       3.1Gi       2.1Gi       120Mi       2.5Gi       4.3Gi
Swap:          2.0Gi          0B       2.0Gi

$ vmstat 1 5
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 2200000 210000 2400000  0    0     5    20  150  300  5  1 93  1  0
 0  0      0 2198000 210000 2400000  0    0     0    15  145  290  3  1 96  0  0
```

**Explanation** of `vmstat`:
- `r` — processes waiting for CPU (high = CPU bottleneck)
- `b` — processes in uninterruptible sleep (high = I/O bottleneck)
- `si/so` — swap in/out (non-zero = memory pressure)
- `wa` — CPU time waiting for I/O
- `st` — CPU stolen by hypervisor

### CPU analysis

```bash
# Per-CPU usage
$ mpstat -P ALL 1 3
CPU    %usr   %nice    %sys %iowait   %irq   %soft  %steal   %idle
all    5.20    0.00    1.30    0.50    0.00    0.20    0.00   92.80
  0    8.00    0.00    2.00    1.00    0.00    0.30    0.00   88.70
  1    2.40    0.00    0.60    0.00    0.00    0.10    0.00   96.90

# Top CPU-consuming processes
$ ps aux --sort=-%cpu | head -10
```

### Memory analysis

```bash
# Detailed memory info
$ cat /proc/meminfo | head -10
MemTotal:        8142848 kB
MemFree:         2197504 kB
MemAvailable:    4556800 kB
Buffers:          204800 kB
Cached:          2462720 kB
SwapTotal:       2097152 kB
SwapFree:        2097152 kB

# Top memory consumers
$ ps aux --sort=-%mem | head -10

# Clear page cache (emergency only)
$ sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### Network performance

```bash
# Connection statistics
$ ss -s
Total: 156
TCP:   12 (estab 3, closed 2, orphaned 0, timewait 2)

# Network throughput (requires nload or iftop)
$ sudo iftop -i eth0

# Check for dropped packets
$ ip -s link show eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    RX: bytes  packets  errors  dropped overrun mcast
    1234567890 9876543  0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    987654321  7654321  0       0       0       0
```

### Kernel parameter tuning (`sysctl`)

```bash
# View all parameters
$ sysctl -a | wc -l
1200

# View specific parameter
$ sysctl net.ipv4.ip_forward
net.ipv4.ip_forward = 0

# Set temporarily
$ sudo sysctl -w net.ipv4.ip_forward=1

# Set permanently
$ echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
$ sudo sysctl -p    # Reload
```

### Common sysctl tuning for servers

```bash
$ cat /etc/sysctl.d/99-performance.conf
# Network performance
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300

# Memory
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File descriptors
fs.file-max = 2097152

# Enable IP forwarding (for routing/containers)
net.ipv4.ip_forward = 1
```

### Ulimits — Resource limits

```bash
$ ulimit -a
core file size          (blocks, -c) 0
data seg size           (kbytes, -d) unlimited
file size               (blocks, -f) unlimited
max locked memory       (kbytes, -l) 65536
max memory size         (kbytes, -m) unlimited
open files                      (-n) 1024
pipe size            (512 bytes, -p) 8
stack size              (kbytes, -s) 8192
max user processes              (-u) 63304

# Increase open files limit for current session
$ ulimit -n 65535

# Permanent: edit /etc/security/limits.conf
$ cat /etc/security/limits.conf
devops  soft  nofile  65535
devops  hard  nofile  65535
*       soft  nproc   65535
*       hard  nproc   65535
```

---

## 12.4 Security Hardening

### Fail2ban — Brute force protection

```bash
$ sudo apt install -y fail2ban

$ cat /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

$ sudo systemctl enable --now fail2ban

# Check banned IPs
$ sudo fail2ban-client status sshd
Status for the jail: sshd
|- Filter
|  |- Currently failed: 2
|  |- Total failed:     45
|  `- File list:        /var/log/auth.log
`- Actions
   |- Currently banned: 3
   |- Total banned:     12
   `- Banned IP list:   203.0.113.50 198.51.100.20 192.0.2.100

# Unban an IP
$ sudo fail2ban-client set sshd unbanip 203.0.113.50
```

### Security auditing

```bash
# Find SUID/SGID files
$ sudo find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -l {} \; 2>/dev/null

# Find world-writable files
$ sudo find / -type f -perm -o=w -not -path "/proc/*" -not -path "/sys/*" 2>/dev/null

# Find files with no owner
$ sudo find / -nouser -o -nogroup 2>/dev/null

# Check for open ports
$ sudo ss -tlnp

# Check running services
$ systemctl list-units --type=service --state=running

# Check failed login attempts
$ sudo lastb | head -20

# Check sudo usage
$ sudo grep "sudo" /var/log/auth.log | tail -10
```

### Automatic security updates

```bash
# Debian/Ubuntu
$ sudo apt install -y unattended-upgrades
$ sudo dpkg-reconfigure -plow unattended-upgrades

# RHEL/CentOS
$ sudo dnf install -y dnf-automatic
$ sudo systemctl enable --now dnf-automatic-install.timer
```

---


## 12.12 Troubleshooting: Advanced Scenarios

### Scenario: SSH connection drops or hangs

```bash
# Add keepalive to SSH client config
$ cat >> ~/.ssh/config << 'EOF'
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
EOF

# Server-side: check sshd config
$ grep -E "ClientAlive|TCPKeep" /etc/ssh/sshd_config
ClientAliveInterval 120
ClientAliveCountMax 3

# Debug SSH connection
$ ssh -vvv user@server 2>&1 | tail -30
```

### Scenario: Docker container won't start

```bash
# Check container logs
$ docker logs mycontainer --tail 50

# Check if port is already in use
$ sudo ss -tlnp | grep :8080

# Check disk space (Docker needs space for layers)
$ df -h /var/lib/docker
$ docker system df

# Clean up Docker
$ docker system prune -af --volumes

# Run container interactively to debug
$ docker run -it --entrypoint /bin/sh myimage
```

### Scenario: System time is wrong

```bash
# Check current time
$ date
$ timedatectl

# Sync with NTP
$ sudo timedatectl set-ntp true
$ sudo systemctl restart systemd-timesyncd

# Check NTP sync status
$ timedatectl timesync-status
Server: 169.254.169.123
Poll interval: 32s
Leap: normal
```

### Scenario: Server unreachable after firewall change

```bash
# If you locked yourself out, use console access (cloud provider)
# Then fix the firewall:
$ sudo ufw disable
# Or
$ sudo iptables -F    # Flush all rules (allows everything)

# Re-add rules carefully
$ sudo ufw default deny incoming
$ sudo ufw default allow outgoing
$ sudo ufw allow 22/tcp    # SSH first!
$ sudo ufw enable
```

---

**Congratulations!** You've completed the Linux for DevOps course. Continue to [Module 13 - System Monitoring](../13-system-monitoring/README.md) and [Module 14 - Troubleshooting Playbooks](../14-troubleshooting-playbooks/README.md) for production-ready skills. Go back to the [Course Overview](../README.md) to review any module.

---
