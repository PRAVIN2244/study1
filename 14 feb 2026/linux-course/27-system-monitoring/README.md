# Module 27: System Monitoring and Observability

## 13.1 The "First 60 Seconds" Checklist

When you SSH into a problematic server, run these commands in order:

```bash
# 1. System overview
$ uptime
 15:00:00 up 45 days, load average: 12.50, 10.20, 8.10

# 2. Kernel errors (OOM, hardware)
$ dmesg -T | tail -20

# 3. System-wide stats
$ vmstat 1 5

# 4. CPU usage per core
$ mpstat -P ALL 1 3

# 5. Disk I/O
$ iostat -xz 1 3

# 6. Memory
$ free -h

# 7. Network connections
$ ss -s

# 8. Per-process CPU
$ ps aux --sort=-%cpu | head -10

# 9. Per-process memory
$ ps aux --sort=-%mem | head -10

# 10. Disk space
$ df -h
```

---

## 13.2 CPU Monitoring

### Understanding Load Average

```bash
$ uptime
 15:00:00 up 45 days, load average: 4.50, 3.20, 2.10

$ nproc
4
```

**Interpretation**:
- Load average shows demand over 1, 5, and 15 minutes
- Compare against CPU count (`nproc`)
- Load 4.50 on 4 CPUs = 112% utilized (slightly overloaded)
- Load 8.00 on 4 CPUs = 200% utilized (severely overloaded)
- Load 2.00 on 4 CPUs = 50% utilized (healthy)
- Increasing trend (2.10 → 3.20 → 4.50) = problem is getting worse

### `mpstat` — Per-CPU Statistics

```bash
$ mpstat -P ALL 1 3
CPU    %usr   %nice    %sys %iowait   %irq   %soft  %steal   %idle
all    45.0    0.0     5.0    15.0    0.0     1.0     0.0    34.0
  0    90.0    0.0     5.0     0.0    0.0     0.0     0.0     5.0
  1    50.0    0.0     5.0     0.0    0.0     2.0     0.0    43.0
  2    20.0    0.0     5.0    30.0    0.0     0.0     0.0    45.0
  3    20.0    0.0     5.0    30.0    0.0     0.0     0.0    45.0
```

**Interpretation**:
- `%usr` — user-space CPU (your applications). CPU 0 at 90% = one process pinned to one core
- `%sys` — kernel CPU (system calls, drivers). High = too many context switches or I/O
- `%iowait` — CPU waiting for disk I/O. CPUs 2-3 at 30% = disk bottleneck
- `%steal` — CPU stolen by hypervisor. High = noisy neighbor on shared cloud instance
- `%idle` — unused CPU

### `sar` — Historical CPU Data

```bash
# CPU usage for today (collected every 10 minutes)
$ sar -u
12:00:01 AM     CPU     %user     %nice   %system   %iowait    %steal     %idle
12:10:01 AM     all      5.20      0.00      1.30      0.50      0.00     93.00
12:20:01 AM     all      4.80      0.00      1.10      0.30      0.00     93.80
...
02:30:01 PM     all     85.00      0.00     10.00      3.00      0.00      2.00
02:40:01 PM     all     90.00      0.00     8.00       1.00      0.00      1.00

# CPU usage for a specific date
$ sar -u -f /var/log/sysstat/sa04    # February 4th

# CPU usage for the last hour
$ sar -u -s 14:00:00 -e 15:00:00
```

**Explanation**: `sar` (System Activity Reporter) collects historical data via `sysstat` package. Install with `sudo apt install sysstat`. It's the only way to see what happened *before* you logged in.

```bash
# Install and enable
$ sudo apt install -y sysstat
$ sudo sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
$ sudo systemctl enable --now sysstat
```

### Find CPU-Hungry Processes

```bash
# Top 10 by CPU right now
$ ps aux --sort=-%cpu | head -11
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
java      3456 85.0  8.5 2500000 680000 ?      Rl   09:00  45:30 java -jar app.jar
python3   5678 12.0  2.3 500000 180000 ?       R    14:00   5:30 python3 worker.py

# CPU usage over time for a specific process
$ pidstat -p 3456 1 5
Linux 6.1.0 (server)    02/05/2025

03:00:01 PM   UID       PID    %usr %system  %guest   %wait    %CPU   CPU  Command
03:00:02 PM  1000      3456   80.00    5.00    0.00    2.00   85.00     0  java
03:00:03 PM  1000      3456   82.00    4.00    0.00    1.00   86.00     0  java
03:00:04 PM  1000      3456   78.00    6.00    0.00    3.00   84.00     1  java

# Check thread-level CPU usage
$ ps -eLf | grep 3456 | head -10
UID        PID  PPID   LWP  C NLWP STIME TTY      TIME CMD
myapp     3456     1  3456  2   25 09:00 ?        00:02:00 java -jar app.jar
myapp     3456     1  3457 80   25 09:00 ?        00:40:00 java -jar app.jar
myapp     3456     1  3458  3   25 09:00 ?        00:03:00 java -jar app.jar
```

**Explanation**: `LWP` = Light Weight Process (thread). Thread 3457 is consuming 80% CPU. Use `jstack 3456` (Java) or `strace -p 3457` to investigate.

---

## 13.3 Memory Monitoring

### Quick memory commands

```bash
$ free -m
               total        used        free      shared  buff/cache   available
Mem:            7953        3200        2145         120        2607        4450
Swap:           2048           0        2048

$ cat /proc/meminfo | head -5
MemTotal:        8142848 kB
MemFree:         2197504 kB
MemAvailable:    4556800 kB
Buffers:          204800 kB
Cached:          2462720 kB
```

**Explanation**: `free -m` is a quick MB view for dashboards and incident notes. `/proc/meminfo` provides raw kernel counters for deeper analysis.

### Detailed Memory Breakdown

```bash
$ cat /proc/meminfo | head -15
MemTotal:        8142848 kB
MemFree:         2197504 kB
MemAvailable:    4556800 kB
Buffers:          204800 kB
Cached:          2462720 kB
SwapCached:            0 kB
Active:          3500000 kB
Inactive:        1800000 kB
SwapTotal:       2097152 kB
SwapFree:        2097152 kB
Dirty:              1234 kB
Shmem:            122880 kB
```

**Key values**:
- `MemAvailable` — what's actually available (the number that matters)
- `Buffers` — kernel buffer cache (metadata, directory listings)
- `Cached` — page cache (file contents cached in RAM for speed)
- `Dirty` — cached data not yet written to disk
- `SwapFree` — if much less than `SwapTotal`, system is under memory pressure

### Memory Usage Per Process

```bash
# Top 10 memory consumers
$ ps aux --sort=-%mem | head -11
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
java      3456  5.2 45.0 6500000 3600000 ?     Sl   09:00  12:30 java -Xmx4g -jar app.jar
postgres  2345  2.1 12.0 1200000 960000 ?      Ss   Dec22   5:30 postgres

# Detailed memory map of a process
$ sudo pmap -x 3456 | tail -5
total kB         6500000  3600000  3200000
# VSZ=6.5G (virtual), RSS=3.6G (physical), Dirty=3.2G (modified)

# Memory usage summary by process name
$ ps aux --no-header | awk '{mem[$11] += $6/1024} END {for (p in mem) printf "%8.1f MB  %s\n", mem[p], p}' | sort -rn | head -10
3600.0 MB  java
 960.0 MB  postgres
  42.0 MB  nginx
  12.0 MB  sshd
```

### Swap Analysis

```bash
# Which processes are using swap?
$ for pid in $(ls /proc/ | grep -E '^[0-9]+$'); do
    swap=$(awk '/VmSwap/ {print $2}' /proc/$pid/status 2>/dev/null)
    if [ -n "$swap" ] && [ "$swap" -gt 0 ]; then
        name=$(cat /proc/$pid/comm 2>/dev/null)
        echo "${swap} kB  PID=$pid  $name"
    fi
done | sort -rn | head -10
524288 kB  PID=3456  java
102400 kB  PID=2345  postgres
  8192 kB  PID=890   nginx
```

**Explanation**: Shows which processes have been swapped out. If critical processes are in swap, they'll be slow. Solutions: add RAM, reduce memory usage, or tune `vm.swappiness`.

### Historical Memory Data

```bash
# Memory usage over time (sar)
$ sar -r
12:00:01 AM kbmemfree kbavail  kbmemused  %memused kbbuffers  kbcached  kbswpfree
12:10:01 AM   2197504  4556800    5945344     73.0    204800   2462720    2097152
...
02:30:01 PM    200000   300000    7942848     97.5     50000    250000     500000
```

---

## 13.4 Disk I/O Monitoring

### Disk space by filesystem and directory

```bash
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /

$ du -h -d 1 /
4.0K    /bin
2.1G    /var
1.3G    /usr
3.7G    /home
8.0G    /
```

**Explanation**: `df -h` shows free space by mounted filesystem. `du -h -d 1` shows which top-level directories are consuming space.

### `iostat` — Disk Performance

```bash
$ iostat -xh 1 5
Device      r/s     w/s   rkB/s   wkB/s  rrqm/s  wrqm/s  await r_await w_await  %util
sda        50.0   200.0  2000.0  50000.0    5.0    30.0   12.5    2.0    15.0   85.0
sdb         2.0     5.0   100.0    200.0    0.0     1.0    1.5    1.0     2.0    3.0
```

**Interpretation**:
- `r/s`, `w/s` — reads/writes per second
- `rkB/s`, `wkB/s` — throughput (sda writing 50 MB/s)
- `await` — average I/O latency in ms (12.5ms — acceptable for HDD, slow for SSD)
- `r_await`, `w_await` — read vs write latency (writes at 15ms are slower)
- `%util` — device utilization (85% = nearly saturated)
- `rrqm/s`, `wrqm/s` — merged requests (kernel combining adjacent I/O)

**Healthy vs Unhealthy**:
- SSD: await < 1ms, %util < 70%
- HDD: await < 20ms, %util < 80%
- If %util = 100% and await > 50ms = disk is the bottleneck

### Historical Disk I/O

```bash
$ sar -d
12:00:01 AM       DEV       tps     rkB/s     wkB/s   areq-sz    aqu-sz     await
12:10:01 AM    dev8-0     50.00   2000.00  50000.00    1040.00      2.50     12.50
...
02:30:01 PM    dev8-0    500.00  10000.00 200000.00     420.00     25.00     50.00
```

### Find I/O-Heavy Processes

```bash
$ sudo iotop -oP
Total DISK READ:       5.00 M/s | Total DISK WRITE:      50.00 M/s
  PID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
 2345 be/4 postgres    2.00 M/s   45.00 M/s  0.00 % 85.00 % postgres: writer
 3456 be/4 myapp       3.00 M/s    5.00 M/s  0.00 % 10.00 % java -jar app.jar

# -o = only show processes doing I/O
# -P = show processes (not threads)
```

---

## 13.5 Network Monitoring

### Bandwidth Usage

```bash
# Real-time bandwidth per interface
$ sar -n DEV 1 5
IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s
eth0    5000.00   4500.00   5000.00   3000.00
lo       100.00    100.00     50.00     50.00
```

**Explanation**: eth0 receiving 5 MB/s and transmitting 3 MB/s. On a 1 Gbps link (125 MB/s), this is 4% utilization — healthy.

```bash
# Check interface speed and errors
$ ip -s link show eth0
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP
    RX: bytes  packets  errors  dropped overrun mcast
    50000000000 40000000    0       15      0       0
    TX: bytes  packets  errors  dropped carrier collsns
    30000000000 25000000    0        0      0       0
```

**Explanation**: 15 dropped RX packets could indicate the receive buffer is too small:

```bash
# Increase network buffer
$ sudo sysctl -w net.core.rmem_max=16777216
$ sudo sysctl -w net.core.wmem_max=16777216
```

### Connection Monitoring

```bash
# Show listening ports (modern and legacy forms)
$ sudo ss -tulwn
Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port
tcp   LISTEN 0      128    0.0.0.0:22         0.0.0.0:*
tcp   LISTEN 0      511    0.0.0.0:80         0.0.0.0:*

$ sudo netstat -tulpn | grep LISTEN
tcp  0  0 0.0.0.0:22   0.0.0.0:*  LISTEN  456/sshd
tcp  0  0 0.0.0.0:80   0.0.0.0:*  LISTEN  789/nginx

# Count connections by state
$ ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn
    500 ESTAB
    150 TIME-WAIT
     30 CLOSE-WAIT
     10 LISTEN
      5 SYN-SENT

# Connections per remote IP
$ ss -tn | awk 'NR>1 {print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
    200 192.168.1.100
     50 192.168.1.101
     30 10.0.0.5

# Historical network data
$ sar -n SOCK
12:00:01 AM    totsck    tcpsck    udpsck    rawsck   ip-frag    tcp-tw
12:10:01 AM       156        12         2         0         0        45
...
02:30:01 PM       850       500         2         0         0       300
# tcp sockets jumped from 12 to 500 — traffic spike
```

---

## 13.6 All-in-One Monitoring Script

```bash
#!/bin/bash
# system_health.sh — Quick system health report

echo "=========================================="
echo "  System Health Report — $(date)"
echo "=========================================="

echo ""
echo "--- SYSTEM ---"
uptime
echo ""

echo "--- CPU ---"
echo "Cores: $(nproc)"
mpstat 1 1 | tail -1 | awk '{printf "User: %.1f%%  System: %.1f%%  IOWait: %.1f%%  Idle: %.1f%%\n", $4, $6, $7, $13}'
echo ""

echo "--- MEMORY ---"
free -h | grep -E "Mem|Swap"
echo ""

echo "--- TOP 5 CPU PROCESSES ---"
ps aux --sort=-%cpu --no-header | head -5 | awk '{printf "%-10s PID=%-6s CPU=%-5s MEM=%-5s %s\n", $1, $2, $3, $4, $11}'
echo ""

echo "--- TOP 5 MEMORY PROCESSES ---"
ps aux --sort=-%mem --no-header | head -5 | awk '{printf "%-10s PID=%-6s CPU=%-5s MEM=%-5s RSS=%-8s %s\n", $1, $2, $3, $4, $6, $11}'
echo ""

echo "--- DISK USAGE ---"
df -h | grep -vE "tmpfs|udev" | awk 'NR>1 {printf "%-20s %5s used of %5s (%s)\n", $6, $3, $2, $5}'
echo ""

echo "--- DISK I/O ---"
iostat -x 1 1 | awk 'NR>6 && $1 !~ /^$/ {printf "%-10s reads=%-8s writes=%-8s await=%-6s util=%s%%\n", $1, $4, $5, $10, $NF}'
echo ""

echo "--- NETWORK ---"
echo "Listening ports:"
ss -tlnp | awk 'NR>1 {printf "  %-25s %s\n", $4, $6}'
echo ""
echo "Connection states:"
ss -ant | awk 'NR>1 {print $1}' | sort | uniq -c | sort -rn | awk '{printf "  %-15s %s\n", $2, $1}'
echo ""

echo "--- FAILED SERVICES ---"
systemctl --failed --no-pager --no-legend 2>/dev/null || echo "  None"
echo ""

echo "=========================================="
```

---

## 13.7 Setting Up Alerts

### Simple disk space alert (cron)

```bash
#!/bin/bash
# /opt/scripts/disk_alert.sh
THRESHOLD=85

df -h | awk -v threshold="$THRESHOLD" 'NR>1 {
    gsub(/%/,"",$5)
    if ($5+0 > threshold) {
        printf "ALERT: %s is %s%% full (%s used of %s) on %s\n", $6, $5, $3, $2, $1
    }
}'
```

```bash
# Add to crontab
$ crontab -e
*/15 * * * * /opt/scripts/disk_alert.sh | mail -s "Disk Alert" admin@company.com
```

### Memory alert

```bash
#!/bin/bash
# /opt/scripts/memory_alert.sh
AVAILABLE=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
TOTAL=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
PERCENT_USED=$(( (TOTAL - AVAILABLE) * 100 / TOTAL ))

if [ "$PERCENT_USED" -gt 90 ]; then
    echo "CRITICAL: Memory usage at ${PERCENT_USED}% (${AVAILABLE}MB available of ${TOTAL}MB)"
    echo ""
    echo "Top memory consumers:"
    ps aux --sort=-%mem | head -6
fi
```

---

## 13.8 `sar` Deep Dive — Historical Performance Data

`sar` (System Activity Reporter) collects and reports system activity. Part of `sysstat` package.

### CPU history

```bash
# CPU usage for today (collected every 10 minutes by default)
$ sar -u
12:00:01 AM     CPU     %user     %nice   %system   %iowait    %steal     %idle
12:10:01 AM     all      5.00      0.00      1.00      0.50      0.00     93.50
12:20:01 AM     all      4.50      0.00      1.00      0.30      0.00     94.20
...
02:00:01 PM     all     85.00      0.00      5.00     8.00       0.00      2.00
02:10:01 PM     all     90.00      0.00      6.00     3.00       0.00      1.00
# CPU spiked at 2 PM

# CPU usage for a specific date
$ sar -u -f /var/log/sysstat/sa05    # sa05 = 5th of the month

# CPU usage between specific times
$ sar -u -s 14:00:00 -e 15:00:00
```

### Memory history

```bash
$ sar -r
12:00:01 AM kbmemfree kbmemused  %memused kbbuffers  kbcached  kbcommit   %commit
12:10:01 AM   2100000   5700000     73.08    204800   2400000   6500000     83.33
...
02:00:01 PM    100000   7700000     98.72    204800   2400000   8500000    108.97
# Memory nearly exhausted at 2 PM — correlates with CPU spike
```

### Disk I/O history

```bash
$ sar -d
12:00:01 AM       DEV       tps     rkB/s     wkB/s   areq-sz    aqu-sz     await
12:10:01 AM    dev8-0     50.00   2000.00    800.00     56.00      0.50      5.00
...
02:00:01 PM    dev8-0    500.00  50000.00  80000.00    260.00     15.00     50.00
# Disk I/O exploded at 2 PM — await 50ms is very high
```

### Network history

```bash
$ sar -n DEV
12:00:01 AM     IFACE   rxpck/s   txpck/s    rxkB/s    txkB/s
12:10:01 AM      eth0    500.00    400.00    200.00    150.00
...
02:00:01 PM      eth0  50000.00  45000.00  80000.00  60000.00
# Network traffic spiked 100x at 2 PM

# Network errors
$ sar -n EDEV
# Shows dropped packets, errors, collisions
```

### Enable sar data collection

```bash
# Install sysstat
$ sudo apt install sysstat

# Check sar/sysstat version
$ sar -V
sysstat version 12.5.2
(C) Sebastien Godard (sysstat <at> orange.fr)

# Enable collection
$ sudo sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
$ sudo systemctl enable sysstat
$ sudo systemctl start sysstat

# Data is collected every 10 minutes and stored in /var/log/sysstat/
```

---

## 13.9 `dstat` — All-in-One Resource Monitor

`dstat` combines `vmstat`, `iostat`, `netstat`, and `ifstat` into one tool. Install with `sudo apt install dstat`.

```bash
$ dstat -cdnm 1 5
--total-cpu-usage-- -dsk/total- -net/total- ------memory-usage-----
usr sys idl wai stl| read  writ| recv  send| used  free  buff  cach
  5   1  93   1   0| 200k  800k|  50k   30k|3200M 2100M  200M 2400M
  4   1  94   1   0| 100k  500k|  45k   25k|3200M 2100M  200M 2400M
 15   5  70  10   0|2000k   50M| 500k  300k|3500M 1800M  200M 2400M
 25   8  50  17   0|5000k  100M|  2M    1M |3800M 1500M  200M 2400M
 40  12  30  18   0|  10M  200M|  5M    3M |4200M 1100M  200M 2400M
```

**Explanation**: Shows CPU, disk, network, and memory in one view, updated every second. The example shows a system going from idle to heavily loaded.

### Useful `dstat` combinations

```bash
# Show top CPU and I/O consuming processes
$ dstat -c -d --top-cpu --top-io 1
--total-cpu-usage-- -dsk/total- -most-expensive- --most-expensive-
usr sys idl wai stl| read  writ|  cpu process   |  i/o process
 85   5   5   5   0|  10M  200M| java       85.0| postgres    200M

# Show all stats with timestamps
$ dstat -t -cdnm 1
----system---- --total-cpu-usage-- -dsk/total- -net/total- ------memory-usage-----
     time     |usr sys idl wai stl| read  writ| recv  send| used  free  buff  cach
05-02 15:00:01|  5   1  93   1   0| 200k  800k|  50k   30k|3200M 2100M  200M 2400M
```

---

## 13.10 `htop` — Interactive Process Viewer (Deep Dive)

`htop` provides a richer interface than `top`. Install with `sudo apt install htop`.

### Key features over `top`

```
  1  [||||||||||||||||||||||||||||||||||||||||  85.0%]   Tasks: 128, 45 thr; 1 running
  2  [||||||||||||||                            35.0%]   Load average: 4.50 3.20 2.10
  3  [||||||||||||||||||||                      50.0%]   Uptime: 45 days, 03:12:00
  4  [||||||                                    15.0%]
  Mem[||||||||||||||||||||||||||||||||||||  3.2G/7.8G]
  Swp[                                      0K/2.0G]

  PID USER      PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command
 3456 myapp      20   0 6500M 3600M  12M S 85.0 45.0 45:30.12 java -jar app.jar
 2345 postgres   20   0 1200M  960M   8M S  2.1 12.0  5:30.45 postgres
  890 www-data   20   0  145M   42M   6M S  1.0  0.5  0:45.30 nginx: worker
```

### Interactive shortcuts

| Key       | Action                                    |
|-----------|-------------------------------------------|
| `F1`      | Help                                      |
| `F2`      | Setup (customize columns, colors)         |
| `F3`      | Search for a process                      |
| `F4`      | Filter processes by name                  |
| `F5`      | Tree view (show parent-child hierarchy)   |
| `F6`      | Sort by column                            |
| `F9`      | Kill a process (select signal)            |
| `F10`     | Quit                                      |
| `t`       | Toggle tree view                          |
| `H`       | Toggle user threads                       |
| `K`       | Toggle kernel threads                     |
| `u`       | Filter by user                            |
| `Space`   | Tag a process (for batch operations)      |
| `l`       | Show open files for process (lsof)        |
| `s`       | Show system calls (strace)                |

### Run `htop` for a specific user

```bash
$ htop -u postgres
```

---

## 13.11 `free` — Memory Deep Dive

```bash
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       3.2Gi       2.1Gi       120Mi       2.5Gi       4.3Gi
Swap:          2.0Gi          0B       2.0Gi
```

**Common misconception**: "free" memory is NOT the only available memory. Linux uses free RAM for disk caching (`buff/cache`). The `available` column is what matters — it's the memory available for new applications (free + reclaimable cache).

### Watch memory over time

```bash
$ watch -n 1 free -h

# Or with vmstat (shows swap activity)
$ vmstat 1 10
procs -----------memory---------- ---swap--
 r  b   swpd   free   buff  cache   si   so
 2  0      0 2197504 204800 2462720   0    0
 2  0  50000 1900000 204800 2462720  100  500
```

**Explanation**: `si` (swap in) and `so` (swap out) are non-zero — the system is actively swapping. This causes severe performance degradation.

### Clear caches (for testing, not production)

```bash
# Drop page cache
$ sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Check effect
$ free -h
```

> ⚠️ Don't do this in production — the cache exists for performance. Only useful for benchmarking.

---

## 13.12 Sample File + Output Walkthrough

Save live command output to files and practice reading them like an incident report.

### Sample Files

```bash
$ cat /tmp/vmstat_sample.txt
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0  120000 180000  50000 420000  200  400   120   800  900 1400 12  6 52 30  0
 3  1  150000 140000  48000 400000  350  700   200  1200 1200 1800 15  8 40 37  0
```

```bash
$ cat /tmp/iostat_sample.txt
Device            r/s     w/s   rkB/s   wkB/s  await  %util
sda             20.00  180.00  800.00 42000.00  28.00  92.00
sdb              1.00    3.00   40.00   120.00   1.20   4.00
```

### Commands, Output, and Meaning

```bash
$ awk 'NR>2 {print "si=" $7, "so=" $8, "wa=" $16 "%"}' /tmp/vmstat_sample.txt
si=200 so=400 wa=30%
si=350 so=700 wa=37%
```

**Explanation**: Non-zero `si/so` plus high `wa` means memory pressure is pushing I/O wait up.

```bash
$ awk 'NR>1 && $7+0 > 20 {print $1, "await=" $6 "ms", "util=" $7 "%"}' /tmp/iostat_sample.txt
sda await=28.00ms util=92.00%
```

**Explanation**: `sda` is the bottleneck. High latency (`await`) and high busy time (`%util`) confirm disk saturation.

### Real-life use case

This workflow is used in post-incident RCA documents to prove whether the incident was CPU-bound, memory-bound, or I/O-bound.

### Troubleshooting checklist

- High load: compare `uptime` vs `nproc`
- High swap and wait: check `vmstat 1 5`
- Slow disk: check `iostat -x 1 5` and `iotop -oP`
- Socket growth: check `ss -s` and `ss -ant | awk ... | sort | uniq -c`

---

## Summary

| What to Monitor | Command                              | Alert Threshold          |
|-----------------|--------------------------------------|--------------------------|
| CPU load        | `uptime`, `mpstat`                   | Load > 2x CPU count      |
| CPU per process | `ps aux --sort=-%cpu`, `pidstat`     | Single process > 90%     |
| Memory          | `free -h`, `/proc/meminfo`           | Available < 10%          |
| Memory per proc | `ps aux --sort=-%mem`, `pmap`        | Single process > 80%     |
| Swap            | `free -h`, `vmstat`                  | Swap used > 50%          |
| Disk space      | `df -h`                              | Usage > 85%              |
| Disk inodes     | `df -i`                              | Usage > 85%              |
| Disk I/O        | `iostat -x`, `iotop`                 | %util > 80%, await > 20ms|
| Network traffic | `sar -n DEV`, `ip -s link`           | Errors/drops > 0         |
| Connections     | `ss -s`, `ss -ant`                   | TIME_WAIT > 1000         |
| Historical data | `sar -u`, `sar -r`, `sar -d`         | Trend analysis           |
| All-in-one      | `dstat -cdnm`, `htop`                | Visual overview          |

**Next Module**: [14 - Real-World Troubleshooting Playbooks](../14-troubleshooting-playbooks/README.md)

---
