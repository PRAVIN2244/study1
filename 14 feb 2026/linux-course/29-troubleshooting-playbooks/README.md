# Module 14: Real-World Troubleshooting Playbooks

Step-by-step playbooks for the most common Linux issues you'll face in production. Each scenario includes how to **identify**, **diagnose**, and **fix** the problem.

---

## 14.1 Disk Usage — "No Space Left on Device"

### Symptoms

```bash
$ touch /var/log/app.log
touch: cannot touch '/var/log/app.log': No space left on device

$ docker pull nginx
Error: write /var/lib/docker/...: no space left on device
```

### Step 1: Confirm the problem

```bash
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   49G    0G  99% /
/dev/sdb1       100G   45G   50G  48% /data
tmpfs           3.9G     0  3.9G   0% /dev/shm
```

**What to look for**: Any filesystem at 90%+ is a concern. 99-100% is an emergency.

### Step 2: Find what's consuming space

```bash
# Top-level breakdown
$ sudo du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10
49G     /
25G     /var
15G     /home
5G      /opt
2G      /usr
1G      /tmp

# Drill into the biggest directory
$ sudo du -h --max-depth=1 /var | sort -hr | head -10
25G     /var
20G     /var/log
3G      /var/cache
1G      /var/lib
500M    /var/tmp

# Find the specific large files
$ sudo find /var/log -type f -size +100M -exec ls -lh {} \; 2>/dev/null
-rw-r--r-- 1 root root 15G Feb  5 15:00 /var/log/app-debug.log
-rw-r--r-- 1 root root 4G  Feb  5 14:00 /var/log/syslog.1
-rw-r--r-- 1 root root 800M Feb  4 23:59 /var/log/kern.log
```

### Step 3: Check for deleted files still held open

```bash
$ sudo lsof | grep '(deleted)' | awk '{print $7, $1, $2, $9}' | sort -rn | head -5
15000000000 java 3456 /var/log/myapp/huge.log
2000000000 nginx 890 /var/log/nginx/old-access.log
```

**Explanation**: A file was deleted with `rm` but a process still has it open. The disk space won't be freed until the process releases the file handle.

**Fix**: Restart the process or truncate the file descriptor:

```bash
# Option 1: Restart the service
$ sudo systemctl restart myapp

# Option 2: Truncate without restart
$ sudo truncate -s 0 /proc/3456/fd/1
```

### Step 4: Clean up

```bash
# Clear package manager cache
$ sudo apt clean                              # Debian/Ubuntu
$ sudo dnf clean all                          # RHEL/CentOS

# Trim systemd journal logs
$ sudo journalctl --vacuum-size=100M
$ sudo journalctl --vacuum-time=7d

# Remove old temp files
$ sudo find /tmp -type f -mtime +7 -delete

# Remove old compressed logs
$ sudo find /var/log -name "*.gz" -mtime +30 -delete

# Truncate a huge active log (keeps file open, clears content)
$ sudo truncate -s 0 /var/log/app-debug.log

# Remove old kernels (Ubuntu)
$ sudo apt autoremove --purge

# Clean Docker (if applicable)
$ docker system prune -af --volumes
```

### Step 5: Check inode exhaustion

```bash
$ df -i
Filesystem      Inodes  IUsed   IFree IUse% Mounted on
/dev/sda1      3276800 3276800      0  100% /
```

**Explanation**: Disk shows space available but you can't create files — you've run out of inodes. This happens with millions of tiny files (mail queues, session files, cache).

```bash
# Find directories with the most files
$ sudo find / -xdev -printf '%h\n' 2>/dev/null | sort | uniq -c | sort -rn | head -10
 2500000 /var/spool/mail/cache
  500000 /tmp/sessions
   50000 /var/lib/php/sessions

# Clean up
$ sudo find /var/spool/mail/cache -type f -mtime +1 -delete
$ sudo find /tmp/sessions -type f -mtime +1 -delete
```

### Prevention

```bash
# Set up log rotation
$ cat /etc/logrotate.d/myapp
/var/log/myapp/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    maxsize 500M
}

# Set up disk space monitoring (cron)
$ crontab -e
*/15 * * * * df -h / | awk 'NR==2 && $5+0 > 85 {print "ALERT: Disk " $5 " full"}' | mail -s "Disk Alert" admin@company.com
```

---

## 14.2 Memory Usage — "Out of Memory" / Slow System

### Symptoms

- System is extremely slow
- SSH sessions take long to connect
- Applications crash with "Cannot allocate memory"
- `dmesg` shows OOM killer messages

### Step 1: Check current memory state

```bash
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       7.2Gi       100Mi       120Mi       500Mi       200Mi
Swap:          2.0Gi       1.8Gi       200Mi
```

**What to look for**:
- `available` column < 10% of total = memory pressure
- `Swap used` > 50% of total = system is actively swapping (slow)
- `free` being low is NOT a problem if `available` is healthy (Linux uses free RAM for cache)

### Step 2: Find memory-hungry processes

```bash
# Top 10 by memory (RSS = actual physical memory)
$ ps aux --sort=-%mem | head -11
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
java      3456  5.2 45.0 6500000 3600000 ?     Sl   09:00  12:30 java -Xmx4g -jar app.jar
postgres  2345  2.1 12.0 1200000 960000 ?      Ss   Dec22   5:30 postgres
node      5678  1.5  8.0  800000 640000 ?      Sl   10:00   2:15 node server.js
redis     6789  0.5  5.0  500000 400000 ?      Ssl  Dec22   1:00 redis-server

# Memory summary by process name
$ ps aux --no-header | awk '{mem[$11] += $6/1024} END {for (p in mem) printf "%8.1f MB  %s\n", mem[p], p}' | sort -rn | head -10
3600.0 MB  java
 960.0 MB  postgres
 640.0 MB  node
 400.0 MB  redis-server
  42.0 MB  nginx
```

### Step 3: Check if OOM killer has been active

```bash
$ dmesg -T | grep -i "oom\|killed\|out of memory"
[Wed Feb  5 14:30:00 2025] Out of memory: Killed process 3456 (java) total-vm:6500000kB, anon-rss:3600000kB
[Wed Feb  5 14:30:00 2025] oom_reaper: reaped process 3456 (java), now anon-rss:0kB

# Check system log
$ sudo grep -i "oom\|killed" /var/log/syslog | tail -10
```

### Step 4: Check swap activity

```bash
$ vmstat 1 5
procs -----------memory---------- ---swap--
 r  b   swpd   free   buff  cache   si   so
 2  1 1800000  100000  50000 450000  500  800
 3  2 1850000   80000  50000 430000  600 1000
 4  3 1900000   60000  50000 410000  800 1200
```

**What to look for**: `si` (swap in) and `so` (swap out) > 0 means active swapping. High values = severe performance impact.

### Step 5: Fix the problem

```bash
# Option 1: Kill the offending process
$ kill 3456

# Option 2: Reduce application memory (e.g., Java heap)
# Edit the service file or startup script
$ sudo systemctl edit myapp
# Add: Environment="JAVA_OPTS=-Xmx2g"

# Option 3: Clear filesystem cache (temporary relief)
$ sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Option 4: Add swap space (emergency)
$ sudo fallocate -l 4G /swapfile
$ sudo chmod 600 /swapfile
$ sudo mkswap /swapfile
$ sudo swapon /swapfile
$ echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Option 5: Tune swappiness (prefer RAM over swap)
$ sudo sysctl vm.swappiness=10
$ echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### Step 6: Find memory leaks

```bash
# Watch a process memory over time
$ while true; do
    RSS=$(ps -p 3456 -o rss= 2>/dev/null)
    [ -z "$RSS" ] && break
    echo "$(date '+%H:%M:%S') RSS: $((RSS/1024)) MB"
    sleep 60
done
# If RSS keeps growing without stopping = memory leak

# Check with pmap
$ sudo pmap -x 3456 | tail -3
total kB         6500000  3600000  3200000
# Run again after 10 minutes — if numbers keep growing, it's a leak
```

### Prevention

```bash
#!/bin/bash
# /opt/scripts/memory_alert.sh
AVAILABLE=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
TOTAL=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
PERCENT_USED=$(( (TOTAL - AVAILABLE) * 100 / TOTAL ))

if [ "$PERCENT_USED" -gt 90 ]; then
    echo "CRITICAL: Memory at ${PERCENT_USED}% (${AVAILABLE}MB available of ${TOTAL}MB)"
    echo ""
    echo "Top memory consumers:"
    ps aux --sort=-%mem | head -6
fi
```

```bash
# Add to crontab
*/5 * * * * /opt/scripts/memory_alert.sh | mail -s "Memory Alert" admin@company.com
```

---

## 14.3 CPU Usage — High Load / Slow Response

### Symptoms

- Server responds slowly, SSH takes long to connect
- Load average is much higher than CPU count

### Step 1: Check load average vs CPU count

```bash
$ uptime
 15:00:00 up 45 days, load average: 12.50, 10.20, 8.10

$ nproc
4
# Load 12.50 on 4 CPUs = 3x overloaded
```

**Interpretation**: Load < CPU count = healthy. Load > 2x CPU count = severely overloaded. Increasing trend (8.10 -> 10.20 -> 12.50) = getting worse.

### Step 2: Identify CPU type

```bash
$ mpstat -P ALL 1 3
CPU    %usr   %nice    %sys %iowait   %steal   %idle
all    85.0    0.0     5.0    8.0       0.0      1.0
  0    95.0    0.0     3.0    0.0       0.0      2.0
  1    90.0    0.0     5.0    0.0       0.0      3.0
  2    75.0    0.0     5.0   18.0       0.0      2.0
  3    80.0    0.0     7.0   12.0       0.0      0.0
```

- `%usr` high = your applications consuming CPU
- `%iowait` high = CPU waiting for disk (disk is the bottleneck)
- `%steal` high = hypervisor stealing CPU (noisy neighbor on cloud)
- One CPU at 95% while others lower = single-threaded bottleneck

### Step 3: Find the guilty process

```bash
$ ps aux --sort=-%cpu | head -10
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
devops    9876 98.5  2.3 500000 180000 ?       R    14:00   5:30 python3 broken_script.py
java      3456 45.0  8.5 2500000 680000 ?      Sl   09:00  45:30 java -jar app.jar

# Per-process CPU over time
$ pidstat 1 5
15:00:01  UID  PID   %usr  %system  %CPU  Command
15:00:02 1000 9876  95.00     3.00 98.00  python3
15:00:02 1000 3456  40.00     5.00 45.00  java
```

### Step 4: Investigate the process

```bash
# What is the process doing?
$ sudo strace -c -p 9876
# Wait 10 seconds, then Ctrl+C
% time     seconds  usecs/call     calls  syscall
 85.00    5.000000        5000      1000  write
# Spending 85% time writing — likely a logging loop

# Check what files it has open
$ sudo lsof -p 9876
python3  9876 devops    1w   REG  500000000 /var/log/debug.log

# Check thread-level CPU
$ ps -eLf | grep 3456 | head -5
UID   PID  PPID   LWP  C NLWP CMD
myapp 3456    1  3457 80   25 java -jar app.jar
# Thread 3457 is consuming 80% CPU
```

### Step 5: Fix the problem

```bash
# Kill the runaway process
$ kill 9876                    # Graceful
$ kill -9 9876                 # Force

# Lower process priority
$ sudo renice 19 -p 9876      # Lowest CPU priority

# Limit CPU usage with systemd
$ sudo systemctl set-property myapp.service CPUQuota=50%
```

### Step 6: Check for fork bombs or zombies

```bash
# Count processes per user
$ ps aux | awk '{print $1}' | sort | uniq -c | sort -rn | head -5
    500 devops
# 500 processes = possible fork bomb

# Find zombie processes
$ ps aux | awk '$8 ~ /Z/ {print $2, $11}'
9999 [defunct]

# Kill the parent of zombies
$ ps -eo pid,ppid,stat,cmd | grep Z
 9999  5000 Z+   [broken_script] <defunct>
$ kill 5000
```

---

## 14.4 Server Down — Service Not Responding

### Symptoms

- Website returns 502/503/504 errors
- Application is unreachable
- Health checks failing

### Step 1: Check if the service is running

```bash
$ sudo systemctl status nginx
     Active: failed (Result: exit-code) since Wed 2025-02-05 14:30:00 UTC

$ sudo systemctl status myapp
     Active: active (running) since Wed 2025-02-05 10:00:00 UTC
# Service is running but not responding — different problem
```

### Step 2: Check the logs

```bash
$ sudo journalctl -u nginx -n 50 --no-pager
Feb 05 14:30:00 server nginx[789]: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)

$ sudo journalctl -u myapp -n 50 --no-pager
Feb 05 14:29:55 server myapp[3456]: FATAL: Cannot start without database

# Application-specific logs
$ sudo tail -50 /var/log/nginx/error.log
$ sudo tail -50 /var/log/myapp/error.log
```

### Step 3: Check if the port is listening

```bash
$ sudo ss -tlnp | grep -E ':80|:8080|:443'
LISTEN  0  128  0.0.0.0:8080  0.0.0.0:*  users:(("java",pid=3456,fd=18))
# Port 80 NOT listening — nginx is down
# Port 8080 IS listening — app is running

# Check if another process grabbed the port
$ sudo ss -tlnp | grep :80
LISTEN  0  128  0.0.0.0:80  0.0.0.0:*  users:(("apache2",pid=5678,fd=4))
# Apache is using port 80 — that's why nginx can't start

# Alternative with netstat
$ sudo netstat -tlnp | grep :80
tcp  0  0  0.0.0.0:80  0.0.0.0:*  LISTEN  5678/apache2
```

### Step 4: Check connectivity

```bash
# Can you reach the service locally?
$ curl -v http://localhost:8080/health

# Check firewall
$ sudo ufw status
$ sudo iptables -L -n | grep -E '80|8080|443'

# Check from outside
$ curl -s -o /dev/null -w "%{http_code}" http://server-ip:8080/health
```

### Step 5: Check dependencies

```bash
# Is the database up?
$ sudo systemctl status postgresql
$ nc -zv db-server 5432

# Is DNS working?
$ dig api.example.com +short

# Check disk space (services crash when disk is full)
$ df -h
```

### Step 6: Fix and restart

```bash
# Fix port conflict
$ sudo kill 5678
$ sudo systemctl start nginx

# If service keeps crashing (crash loop)
$ sudo journalctl -u myapp --since "5 minutes ago"

# Run manually to see errors in real-time
$ sudo systemctl stop myapp
$ sudo -u myapp /opt/myapp/bin/server --port 8080
```

### Common causes and fixes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Address already in use" | Port conflict | `ss -tlnp \| grep :PORT`, kill conflicting process |
| "Permission denied" | Wrong user/permissions | Check service user, file permissions |
| "Connection refused" to DB | Database down | `systemctl start postgresql` |
| "No space left on device" | Disk full | See Section 14.1 |
| "Cannot allocate memory" | OOM | See Section 14.2 |
| "Too many open files" | FD limit | `ulimit -n 65535`, edit limits.conf |

---

## 14.5 High Network Traffic

### Step 1: Check bandwidth

```bash
$ sar -n DEV 1 5
IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s
eth0    50000.0   45000.0   80000.0   60000.0

# Per-connection bandwidth
$ sudo iftop -i eth0 -n

# Per-process bandwidth
$ sudo nethogs eth0
  PID USER     PROGRAM                DEV        SENT      RECEIVED
 3456 myapp    java                   eth0      50.0 MB/s  80.0 MB/s
```

### Step 2: Check for packet drops

```bash
$ ip -s link show eth0
    RX:  errors  dropped
              0    15000
# 15000 dropped = receive buffer overflow

# Fix
$ sudo sysctl -w net.core.rmem_max=16777216
```

### Step 3: Check connection states

```bash
$ ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
   3000 ESTAB
    800 TIME-WAIT
    500 CLOSE-WAIT

# Top talkers by connection count
$ ss -tn | awk 'NR>1 {print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -5
   2000 203.0.113.50
# 2000 connections from one IP = possible attack
```

### Step 4: Fix

```bash
# Block abusive IP
$ sudo iptables -A INPUT -s 203.0.113.50 -j DROP

# Tune TCP for high traffic
$ sudo sysctl -w net.ipv4.tcp_tw_reuse=1
$ sudo sysctl -w net.ipv4.tcp_fin_timeout=15
$ sudo sysctl -w net.core.somaxconn=65535
```

---

## 14.6 Software Updates — Installing, Updating, and Seeing Changes

### Check what version is installed

```bash
# Debian/Ubuntu
$ apt list --installed 2>/dev/null | grep nginx
nginx/jammy-updates,now 1.18.0-6ubuntu14.4 amd64 [installed]

$ dpkg -l nginx
ii  nginx  1.18.0-6ubuntu14.4  amd64  small, powerful, scalable web/proxy server

# RHEL/CentOS
$ rpm -qa | grep nginx
nginx-1.20.1-14.el9.x86_64

$ dnf list installed nginx
```

### Check what version is available

```bash
# Debian/Ubuntu
$ apt policy nginx
  Installed: 1.18.0-6ubuntu14.4
  Candidate: 1.18.0-6ubuntu14.5

# RHEL/CentOS
$ dnf check-update nginx
nginx.x86_64    1:1.20.1-16.el9    appstream
```

### See what changed in an update (changelog)

```bash
# Debian/Ubuntu
$ apt changelog nginx
nginx (1.18.0-6ubuntu14.5) jammy-security; urgency=medium
  * SECURITY UPDATE: HTTP/2 rapid reset attack (CVE-2023-44487)

# RHEL/CentOS
$ dnf changelog nginx
* Wed Jan 15 2025 - Security fix for CVE-2023-44487
```

### Update a specific package

```bash
# Debian/Ubuntu
$ sudo apt update
$ sudo apt install --only-upgrade nginx
$ nginx -v
nginx version: nginx/1.18.0

# RHEL/CentOS
$ sudo dnf upgrade nginx
```

### Update all packages

```bash
# Debian/Ubuntu
$ sudo apt update && sudo apt upgrade -y

# Security updates only
$ sudo apt update && sudo apt upgrade -y --only-upgrade

# RHEL/CentOS
$ sudo dnf upgrade -y
$ sudo dnf upgrade --security -y    # Security only
```

### See what files a package installed

```bash
# Debian/Ubuntu
$ dpkg -L nginx
/.
/usr/sbin/nginx
/etc/nginx/nginx.conf
/etc/nginx/sites-available/default
/var/log/nginx

# RHEL/CentOS
$ rpm -ql nginx
```

### See what files were modified since installation

```bash
# Debian/Ubuntu
$ dpkg -V nginx
??5??????   /etc/nginx/nginx.conf
# 5 = MD5 checksum changed (config was modified)

# RHEL/CentOS
$ rpm -V nginx
S.5....T.  c /etc/nginx/nginx.conf
# S=size, 5=checksum, T=timestamp changed
```

### Check when packages were last updated

```bash
# Debian/Ubuntu
$ grep " upgrade " /var/log/dpkg.log | tail -10
2025-02-04 09:00:15 upgrade nginx:amd64 1.18.0-6ubuntu14.3 1.18.0-6ubuntu14.4
2025-02-04 09:00:16 upgrade openssl:amd64 3.0.2-0ubuntu1.12 3.0.2-0ubuntu1.13

# RHEL/CentOS
$ dnf history
ID | Command line          | Date and time    | Action   | Altered
 5 | upgrade nginx         | 2025-02-04 09:00 | Upgrade  |    1
```

### Rollback / Downgrade a package

```bash
# Debian/Ubuntu — install specific older version
$ apt list -a nginx
nginx/jammy-updates 1.18.0-6ubuntu14.5 amd64
nginx/jammy-updates 1.18.0-6ubuntu14.4 amd64
nginx/jammy 1.18.0-6ubuntu14 amd64

$ sudo apt install nginx=1.18.0-6ubuntu14.4

# RHEL/CentOS — undo last transaction
$ sudo dnf history undo 5

# Or downgrade
$ sudo dnf downgrade nginx
```

### Pin a package version (prevent auto-upgrade)

```bash
# Debian/Ubuntu
$ sudo apt-mark hold nginx
nginx set on hold.

$ apt-mark showhold
nginx

$ sudo apt-mark unhold nginx    # Remove hold

# RHEL/CentOS
$ sudo dnf versionlock add nginx
$ sudo dnf versionlock list
$ sudo dnf versionlock delete nginx
```

### Verify package integrity after update

```bash
# Check if the service still works after update
$ sudo systemctl restart nginx
$ sudo systemctl status nginx
$ curl -s -o /dev/null -w "%{http_code}" http://localhost
200

# Compare config with package default
$ diff /etc/nginx/nginx.conf /etc/nginx/nginx.conf.dpkg-dist 2>/dev/null
# If .dpkg-dist exists, the update shipped a new default config
```

---

## 14.7 "Too Many Open Files" — File Descriptor Limits

### Symptoms

```bash
$ curl http://localhost:8080
curl: (7) Failed to connect: Too many open files

# In application logs:
java.io.IOException: Too many open files
```

### Step 1: Check current limits

```bash
# System-wide limit
$ cat /proc/sys/fs/file-nr
5000    0    100000
# 5000 allocated, 0 unused, 100000 max

# Per-process limit
$ ulimit -n
1024

# Check limit for a running process
$ cat /proc/3456/limits | grep "open files"
Max open files            1024                 1024                 files
```

### Step 2: Check how many files the process has open

```bash
$ sudo ls /proc/3456/fd | wc -l
1020
# 1020 out of 1024 limit — almost exhausted!

$ sudo lsof -p 3456 | wc -l
1020
```

### Step 3: Fix — increase limits

```bash
# Temporary (current session)
$ ulimit -n 65535

# Permanent — edit limits.conf
$ sudo tee -a /etc/security/limits.conf << 'EOF'
*       soft    nofile  65535
*       hard    nofile  65535
root    soft    nofile  65535
root    hard    nofile  65535
EOF

# For systemd services
$ sudo systemctl edit myapp
# Add:
[Service]
LimitNOFILE=65535

$ sudo systemctl daemon-reload
$ sudo systemctl restart myapp

# System-wide max
$ sudo sysctl -w fs.file-max=200000
$ echo "fs.file-max=200000" | sudo tee -a /etc/sysctl.conf
```

---

## 14.8 Kernel Parameter Tuning — `sysctl`

### View all kernel parameters

```bash
$ sysctl -a | wc -l
1200

# Search for specific parameters
$ sysctl -a | grep tcp_keepalive
net.ipv4.tcp_keepalive_time = 7200
net.ipv4.tcp_keepalive_intvl = 75
net.ipv4.tcp_keepalive_probes = 9
```

### Common production tuning

```bash
# Network performance
$ sudo sysctl -w net.core.somaxconn=65535           # Max connection backlog
$ sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535 # SYN queue size
$ sudo sysctl -w net.ipv4.tcp_tw_reuse=1            # Reuse TIME_WAIT sockets
$ sudo sysctl -w net.ipv4.tcp_fin_timeout=15        # Faster FIN timeout

# Memory
$ sudo sysctl -w vm.swappiness=10                   # Prefer RAM over swap
$ sudo sysctl -w vm.overcommit_memory=0             # Don't overcommit

# File handles
$ sudo sysctl -w fs.file-max=200000

# Make persistent
$ sudo sysctl -p                                     # Reload from /etc/sysctl.conf
```

### Save all tuning permanently

```bash
$ sudo tee /etc/sysctl.d/99-production.conf << 'EOF'
# Network
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.ip_local_port_range = 1024 65535

# Memory
vm.swappiness = 10
vm.overcommit_memory = 0

# File handles
fs.file-max = 200000
EOF

$ sudo sysctl -p /etc/sysctl.d/99-production.conf
```

---

## 14.9 Quick Reference — First 60 Seconds on a Problem Server

Run these commands in order when you SSH into a problematic server:

```bash
# 1. What's the system state?
$ uptime                                    # Load average
$ nproc                                     # CPU count (compare with load)

# 2. Memory
$ free -h                                   # RAM and swap usage

# 3. Disk
$ df -h                                     # Filesystem usage

# 4. CPU consumers
$ ps aux --sort=-%cpu | head -5             # Top CPU processes

# 5. Memory consumers
$ ps aux --sort=-%mem | head -5             # Top memory processes

# 6. Listening ports
$ sudo ss -tlnp                             # What services are running

# 7. Failed services
$ systemctl --failed                        # Any crashed services

# 8. Recent errors
$ sudo journalctl -p err --since "1 hour ago" --no-pager | tail -20

# 9. Kernel errors (OOM, hardware)
$ dmesg -T | tail -20

# 10. Disk I/O
$ iostat -x 1 3 2>/dev/null || echo "Install sysstat: apt install sysstat"
```

---

## 14.10 Incident Evidence Files + Output Explanation

In real support cases, you usually attach command output files to tickets. This section shows a standard pattern.

### Sample Evidence Files

```bash
$ cat /tmp/incident_df.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   49G  500M  99% /
/dev/sdb1       200G   90G  100G  48% /data
```

```bash
$ cat /tmp/incident_ps.txt
USER       PID %CPU %MEM COMMAND
java      3456 95.0 40.0 java -jar app.jar
postgres  2345 12.0 10.0 postgres
```

### Commands, Output, and Meaning

```bash
$ awk 'NR==1 || $5+0 >= 90' /tmp/incident_df.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   49G  500M  99% /
```

**Explanation**: Confirms the root filesystem is critically full.

```bash
$ awk 'NR>1 {print $1, "PID=" $2, "CPU=" $3 "%", "MEM=" $4 "%"}' /tmp/incident_ps.txt
java PID=3456 CPU=95.0% MEM=40.0%
postgres PID=2345 CPU=12.0% MEM=10.0%
```

**Explanation**: Gives a compact summary of top offenders for the incident timeline.

```bash
$ paste /tmp/incident_df.txt /tmp/incident_ps.txt | head -2
Filesystem      Size  Used Avail Use% Mounted on  USER       PID %CPU %MEM COMMAND
/dev/sda1        50G   49G  500M  99% /           java      3456 95.0 40.0 java -jar app.jar
```

**Explanation**: Correlates disk pressure and process pressure in one view for escalation notes.

### Real-life use case

Use this format in incident channels, Jira, or postmortems so others can reproduce the exact findings from the same evidence files.

### Troubleshooting checklist

- Save raw outputs first (`df`, `free`, `ps`, `ss`, `journalctl`) before making changes
- Mark timestamps (`date`) in all notes
- Apply one fix at a time and re-run the same commands
- Attach before/after output in the incident ticket

---

## Summary

| Problem | Key Commands | Section |
|---------|-------------|---------|
| Disk full | `df -h`, `du -sh`, `find -size`, `lsof \| grep deleted` | 14.1 |
| Out of memory | `free -h`, `ps --sort=-%mem`, `dmesg \| grep oom` | 14.2 |
| High CPU | `uptime`, `nproc`, `mpstat`, `ps --sort=-%cpu`, `strace` | 14.3 |
| Server down | `systemctl status`, `journalctl -u`, `ss -tlnp` | 14.4 |
| High traffic | `sar -n DEV`, `iftop`, `nethogs`, `ss -ant` | 14.5 |
| Software updates | `apt policy`, `dpkg -V`, `apt changelog`, `dnf history` | 14.6 |

**Back to**: [Course Overview](../README.md)


---
## 14.11 Log Management with logrotate

`logrotate` manages log file size, compression, and cleanup to prevent `/var/log` from filling the disk.

### Configuration

- Global config: `/etc/logrotate.conf`
- Per-application configs: `/etc/logrotate.d/`

### Example: nginx log rotation

```
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    postrotate
        systemctl reload nginx > /dev/null 2>/dev/null || true
    endscript
}
```

| Directive | Meaning |
|-----------|---------|
| `daily` | Rotate every day |
| `rotate 14` | Keep 14 rotated copies |
| `compress` | Gzip old logs |
| `delaycompress` | Don't compress the most recent rotated file |
| `missingok` | Don't error if log file is missing |
| `notifempty` | Don't rotate if file is empty |
| `postrotate` | Run command after rotation (e.g., reload service) |

```bash
# Test logrotate config (dry run)
logrotate -d /etc/logrotate.conf

# Force rotation
sudo logrotate -f /etc/logrotate.conf

# Check logrotate status
cat /var/lib/logrotate/status
```

---

## 14.12 Audit Logging with auditd

`auditd` records security-relevant events: file access, permission changes, logins, and system calls.

### Setup

```bash
# Install
sudo apt install auditd        # Debian/Ubuntu
sudo yum install audit          # RHEL/CentOS

# Enable and start
sudo systemctl enable --now auditd
```

### Watch Files and Directories

```bash
# Watch /etc/passwd for writes and attribute changes
sudo auditctl -w /etc/passwd -p wa -k passwd_watch

# Watch SSH config directory
sudo auditctl -w /etc/ssh/ -p wa -k ssh_config_watch

# Watch for file deletions in /var/www
sudo auditctl -w /var/www -p w -k web_changes
```

### Search Audit Logs

```bash
# Search by key
ausearch -k passwd_watch

# Search by user
ausearch -ua 1001

# Search by time range
ausearch -ts today -te now

# View raw audit log
tail -f /var/log/audit/audit.log
```

### Persist Audit Rules

Add rules to `/etc/audit/rules.d/audit.rules`:

```
-w /etc/passwd -p wa -k passwd_watch
-w /etc/shadow -p wa -k shadow_watch
-w /etc/sudoers -p wa -k sudoers_watch
```

```bash
# Reload rules
sudo augenrules --load
```

---

## 14.13 Centralized Logging with rsyslog

`rsyslog` forwards logs to a central server for aggregation and analysis.

### Configure Log Forwarding (Client)

Edit `/etc/rsyslog.conf`:

```
# Forward all logs to central server via TCP
*.* @@logserver.example.com:514

# Or via UDP
*.* @logserver.example.com:514
```

### Configure Log Receiver (Server)

Edit `/etc/rsyslog.conf`:

```
# Enable TCP reception
module(load="imtcp")
input(type="imtcp" port="514")

# Store remote logs by hostname
template(name="RemoteLogs" type="string"
    string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
*.* ?RemoteLogs
```

```bash
# Restart rsyslog after changes
sudo systemctl restart rsyslog

# Test logging
logger "Test message from $(hostname)"

# Verify
tail /var/log/syslog
```

### Real-world use

In production, rsyslog feeds into centralized logging systems like:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Graylog**
- **Splunk**
- **Loki + Grafana**

---

## 14.14 Linux Security Troubleshooting

### SELinux Troubleshooting (RHEL/CentOS)

```bash
# Check SELinux status
getenforce
sestatus

# View SELinux denials
ausearch -m avc -ts recent
cat /var/log/audit/audit.log | grep denied

# Temporarily set to permissive (for debugging)
sudo setenforce 0

# Fix file context
sudo restorecon -Rv /var/www/html

# Change file context
sudo chcon -t httpd_sys_content_t /var/www/html/index.html
```

### AppArmor Troubleshooting (Ubuntu)

```bash
# Check status
sudo aa-status

# Set profile to complain mode (log but don't block)
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx

# Set profile to enforce mode
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx

# View AppArmor logs
dmesg | grep apparmor
journalctl | grep apparmor
```

### Firewall Troubleshooting

```bash
# iptables — list all rules
sudo iptables -L -v -n

# Check if a port is blocked
sudo iptables -L INPUT -v -n | grep 8080

# firewalld — check active zones and rules
sudo firewall-cmd --list-all
sudo firewall-cmd --get-active-zones

# ufw — check status
sudo ufw status verbose

# Allow a port
sudo ufw allow 8080/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp && sudo firewall-cmd --reload
```

### SSH Troubleshooting

```bash
# Check SSH service
systemctl status sshd

# View SSH logs
journalctl -u sshd
tail -f /var/log/auth.log       # Debian/Ubuntu
tail -f /var/log/secure          # RHEL/CentOS

# Test SSH connection with verbose output
ssh -vvv user@host

# Check SSH config syntax
sshd -t

# Common fixes
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_rsa
```

### Detecting Suspicious Activity

```bash
# Check for unusual listening ports
ss -tulnp

# Find executable files in /tmp (common malware location)
find /tmp /dev/shm -type f -executable

# Check for rootkits
sudo apt install rkhunter chkrootkit
sudo rkhunter --check
sudo chkrootkit

# Check for SUID binaries (potential privilege escalation)
find / -perm -4000 -type f 2>/dev/null

# Check for world-writable files
find / -type f -perm -o+w 2>/dev/null | head -20

# Monitor file integrity with AIDE
sudo apt install aide
sudo aideinit
sudo aide --check
```

### File Integrity and Access Tracking

```bash
# Track file access in real time with inotifywait
sudo apt install inotify-tools
inotifywait -m -r /etc/

# Check last access times
ls -ltu /etc/passwd

# Find files accessed in the last 10 minutes
find /etc -amin -10

# Check file attributes (immutable flag)
lsattr /etc/hosts
# Set immutable (prevents even root from modifying)
sudo chattr +i /etc/hosts
```

---

## 14.15 Interview Questions — Module 14

**Q1: Describe your systematic approach to troubleshooting a Linux server issue.**

1. **Gather symptoms** — What's failing? When did it start? What changed?
2. **Check system health** — `uptime`, `free -h`, `df -h`, `dmesg | tail`
3. **Check logs** — `journalctl -xe`, `/var/log/syslog`, application logs
4. **Check services** — `systemctl --failed`, `systemctl status <service>`
5. **Check network** — `ss -tulnp`, `ping`, `traceroute`
6. **Identify root cause** — correlate timestamps across logs and metrics
7. **Fix and verify** — apply fix, confirm resolution, document

**Q2: How do you recover a system that won't boot?**

1. Boot from GRUB recovery menu or live USB
2. Mount root filesystem: `mount /dev/sda1 /mnt`
3. Chroot: `chroot /mnt`
4. Check `/etc/fstab` for bad entries
5. Run `fsck` on corrupted filesystems
6. Check `journalctl -xb` for boot errors
7. Reinstall GRUB if needed: `grub-install /dev/sda && update-grub`

**Q3: How do you troubleshoot "Permission denied" errors?**

```bash
ls -la file                           # Check permissions
stat file                             # Detailed metadata
namei -l /path/to/file                # Check permissions along entire path
getfacl file                          # Check ACLs
getenforce                            # Check SELinux (RHEL)
ausearch -m avc -ts recent            # SELinux denials
```

**Q4: What is logrotate and why is it important?**

logrotate manages log file size by rotating, compressing, and deleting old logs. Without it, `/var/log` fills the disk. Configure per-application in `/etc/logrotate.d/`. Key directives: `daily`, `rotate 14`, `compress`, `missingok`, `postrotate` (reload service after rotation).

**Q5: How do you audit who changed a critical file?**

```bash
# Set up auditd watch
sudo auditctl -w /etc/passwd -p wa -k passwd_watch
# Search audit logs
ausearch -k passwd_watch
# Persist rules in /etc/audit/rules.d/audit.rules
```
