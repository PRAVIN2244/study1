# Module 30: Debugging and Troubleshooting

When containers misbehave in production, you need advanced debugging
techniques: nsenter, strace, debug containers, network diagnostics,
and performance profiling.

### Topics Covered

```
30.1  Debugging Methodology for Containers
30.2  docker logs — Advanced Usage
30.3  docker exec — Interactive Debugging
30.4  nsenter — Enter Container Namespaces from Host
30.5  Debug Containers (Ephemeral Containers)
30.6  strace — Tracing System Calls
30.7  Network Debugging (tcpdump, nslookup, netstat)
30.8  Filesystem and Storage Debugging
30.9  Performance Profiling (CPU, Memory, I/O)
30.10 Core Dump Analysis
30.11 Common Production Issues and Solutions
30.12 Debugging Decision Tree
```

---

## 30.1 Debugging Methodology for Containers

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTAINER DEBUGGING WORKFLOW                       │
│                                                                 │
│  1. CHECK STATUS                                               │
│     docker ps -a                    Is it running?              │
│     docker inspect <container>      Exit code? OOM?             │
│                                                                 │
│  2. CHECK LOGS                                                 │
│     docker logs <container>         Application output          │
│     docker logs --tail 100 -f       Last 100 lines, follow     │
│                                                                 │
│  3. CHECK RESOURCES                                            │
│     docker stats <container>        CPU, memory, I/O            │
│     docker top <container>          Process list                │
│                                                                 │
│  4. CHECK CONFIGURATION                                        │
│     docker inspect <container>      Full config dump            │
│     docker diff <container>         Filesystem changes          │
│                                                                 │
│  5. INTERACTIVE DEBUG                                          │
│     docker exec -it <c> sh          Shell into container        │
│     nsenter --target <pid> ...      Enter from host             │
│     docker debug <container>        Ephemeral debug shell       │
│                                                                 │
│  6. DEEP ANALYSIS                                              │
│     strace -p <pid>                 Syscall tracing             │
│     tcpdump -i <iface>              Network capture             │
│     perf top -p <pid>               CPU profiling               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 30.2 docker logs — Advanced Usage

```bash
# Basic log viewing
$ docker logs myapp

# Last 50 lines
$ docker logs --tail 50 myapp

# Follow (stream) logs
$ docker logs -f myapp

# Logs with timestamps
$ docker logs -t myapp
# 2024-01-15T10:30:00.123456789Z  Server started on port 3000

# Logs since a specific time
$ docker logs --since "2024-01-15T10:00:00" myapp
$ docker logs --since 30m myapp    # Last 30 minutes
$ docker logs --since 2h myapp     # Last 2 hours

# Logs until a specific time
$ docker logs --until "2024-01-15T11:00:00" myapp

# Combine: logs from a specific time window
$ docker logs --since "2024-01-15T10:00:00" --until "2024-01-15T10:30:00" myapp

# Separate stdout and stderr
$ docker logs myapp 2>/dev/null     # stdout only
$ docker logs myapp 1>/dev/null     # stderr only

# Pipe to grep for filtering
$ docker logs myapp 2>&1 | grep -i error
$ docker logs myapp 2>&1 | grep -i "connection refused"

# Count errors in logs
$ docker logs myapp 2>&1 | grep -c "ERROR"

# View logs of a stopped container
$ docker logs $(docker ps -aq --filter "name=myapp" --filter "status=exited")
```

### Log Inspection for Crashed Containers

```bash
# Container exited — find out why
$ docker inspect --format '{{.State.ExitCode}}' myapp
# 0   = normal exit
# 1   = application error
# 137 = OOM killed (128 + 9 = SIGKILL)
# 143 = SIGTERM (128 + 15)
# 139 = segfault (128 + 11 = SIGSEGV)

$ docker inspect --format '{{.State.OOMKilled}}' myapp
# true = ran out of memory

$ docker inspect --format '{{.State.Error}}' myapp
# Shows error message if any
```

---

## 30.3 docker exec — Interactive Debugging

```bash
# Get a shell inside a running container
$ docker exec -it myapp /bin/sh
$ docker exec -it myapp /bin/bash

# Run a specific command
$ docker exec myapp cat /etc/resolv.conf
$ docker exec myapp env                    # View environment variables
$ docker exec myapp ps aux                 # View processes
$ docker exec myapp df -h                  # Disk usage
$ docker exec myapp free -m                # Memory usage
$ docker exec myapp cat /proc/1/status     # PID 1 details

# Run as a specific user
$ docker exec -u root myapp whoami
$ docker exec -u 0 myapp apt-get update    # UID 0 = root

# Set environment variables for the exec session
$ docker exec -e DEBUG=true myapp node debug-script.js

# Working directory
$ docker exec -w /app myapp ls -la
```

### When exec Isn't Available

```bash
# Minimal images (distroless, scratch) have no shell
$ docker exec myapp /bin/sh
# OCI runtime exec failed: exec failed: unable to start container
# process: exec: "/bin/sh": stat /bin/sh: no such file or directory

# Solutions:
# 1. Use docker debug (Docker Desktop 4.27+)
$ docker debug myapp

# 2. Use nsenter from the host
$ nsenter --target $(docker inspect --format '{{.State.Pid}}' myapp) \
    --mount --uts --ipc --net --pid

# 3. Copy files out for inspection
$ docker cp myapp:/app/config.json ./config.json
```

---

## 30.4 nsenter — Enter Container Namespaces from Host

nsenter lets you enter a container's namespaces from the host,
even if the container has no shell.

```bash
# Get the container's PID on the host
$ PID=$(docker inspect --format '{{.State.Pid}}' myapp)

# Enter all namespaces
$ sudo nsenter --target $PID --mount --uts --ipc --net --pid -- /bin/sh

# Enter only the network namespace (debug networking)
$ sudo nsenter --target $PID --net -- ip addr
$ sudo nsenter --target $PID --net -- ss -tlnp
$ sudo nsenter --target $PID --net -- ping 10.0.0.5

# Enter only the mount namespace (inspect filesystem)
$ sudo nsenter --target $PID --mount -- ls /app/
$ sudo nsenter --target $PID --mount -- cat /etc/resolv.conf

# Enter only the PID namespace (see container processes)
$ sudo nsenter --target $PID --pid -- ps aux

# Run tcpdump in the container's network namespace
$ sudo nsenter --target $PID --net -- tcpdump -i eth0 -n port 80

# Run strace on a process inside the container
$ sudo nsenter --target $PID --pid --mount -- strace -p 1
```

### nsenter Flags Reference

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Flag         │ Namespace Entered                                │
├──────────────┼──────────────────────────────────────────────────┤
│ --mount (-m) │ Mount namespace (filesystem view)                │
│ --uts (-u)   │ UTS namespace (hostname)                         │
│ --ipc (-i)   │ IPC namespace (shared memory, semaphores)        │
│ --net (-n)   │ Network namespace (interfaces, routes)           │
│ --pid (-p)   │ PID namespace (process IDs)                      │
│ --user (-U)  │ User namespace (UID/GID mapping)                 │
│ --cgroup (-C)│ Cgroup namespace                                 │
│ --target (-t)│ Target PID to get namespaces from                │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 30.5 Debug Containers (Ephemeral Containers)

### docker debug (Docker Desktop 4.27+)

```bash
# Attach a debug shell to any container, even distroless/scratch
$ docker debug myapp
# Installs a debug toolbox (busybox, curl, vim, etc.) temporarily
# Does NOT modify the original container image

# Use a custom debug image
$ docker debug --image nicolaka/netshoot myapp
# netshoot includes: tcpdump, curl, nslookup, iperf, strace, etc.
```

### Kubernetes Ephemeral Containers

```bash
# Add a debug container to a running pod (Kubernetes 1.23+)
$ kubectl debug -it myapp-pod --image=busybox --target=myapp
# --target: share the PID namespace with the target container
# You can see the target container's processes

$ kubectl debug -it myapp-pod --image=nicolaka/netshoot --target=myapp
# Full networking debug tools available
```

### Sidecar Debug Pattern

```bash
# Run a debug container sharing the target's namespaces
$ docker run -it --rm \
    --pid=container:myapp \
    --net=container:myapp \
    --volumes-from myapp \
    nicolaka/netshoot /bin/bash

# Inside the debug container:
$ ps aux          # See myapp's processes (shared PID namespace)
$ ss -tlnp        # See myapp's network sockets (shared net namespace)
$ ls /app/        # See myapp's files (shared volumes)
$ tcpdump -i eth0 # Capture myapp's network traffic
$ curl localhost:3000/health  # Test myapp's endpoints
```

---

## 30.6 strace — Tracing System Calls

```bash
# strace shows every system call a process makes
# Essential for debugging "it works on my machine" issues

# Trace a process inside a container (from host)
$ PID=$(docker inspect --format '{{.State.Pid}}' myapp)
$ sudo strace -p $PID
# Shows live syscalls: open(), read(), write(), connect(), etc.

# Trace with timestamps
$ sudo strace -t -p $PID

# Trace specific syscalls only
$ sudo strace -e trace=network -p $PID    # Network calls only
$ sudo strace -e trace=file -p $PID       # File operations only
$ sudo strace -e trace=open,read,write -p $PID

# Summary of syscalls (count and time)
$ sudo strace -c -p $PID
# Press Ctrl+C after a few seconds to see the summary:
# % time     seconds  usecs/call     calls    errors syscall
# ------ ----------- ----------- --------- --------- --------
#  45.23    0.012345          12      1028           read
#  30.12    0.008234           8      1028           write
#  15.67    0.004289          42       102         3 connect

# Trace a new process inside the container
$ docker exec myapp strace -c ls /app/
# Requires strace installed in the container

# Trace child processes too (-f flag)
$ sudo strace -f -p $PID

# Save trace to file
$ sudo strace -o /tmp/trace.log -p $PID
```

### Common strace Patterns

```bash
# Find why a process can't open a file
$ sudo strace -e trace=open,openat -p $PID 2>&1 | grep ENOENT
# openat(AT_FDCWD, "/app/config.json", O_RDONLY) = -1 ENOENT

# Find why a network connection fails
$ sudo strace -e trace=connect -p $PID 2>&1 | grep ECONNREFUSED
# connect(3, {sa_family=AF_INET, sin_port=htons(5432),
#   sin_addr=inet_addr("10.0.0.5")}, 16) = -1 ECONNREFUSED

# Find what files a process reads at startup
$ sudo strace -e trace=openat -f docker run --rm myapp 2>&1 | grep openat
```

---

## 30.7 Network Debugging (tcpdump, nslookup, netstat)

### DNS Resolution Issues

```bash
# Check DNS resolution inside the container
$ docker exec myapp nslookup db
# Server:    127.0.0.11   ← Docker's embedded DNS
# Name:      db
# Address:   172.18.0.3

# If nslookup isn't available, use getent
$ docker exec myapp getent hosts db

# Check /etc/resolv.conf
$ docker exec myapp cat /etc/resolv.conf
# nameserver 127.0.0.11
# options ndots:0

# Common DNS issues:
#   - Container on default bridge (no DNS resolution)
#     Fix: Use a user-defined network
#   - Service name typo
#   - Target container not on the same network
$ docker network inspect mynetwork | grep -A 5 Containers
```

### Port and Connection Debugging

```bash
# Check listening ports inside the container
$ docker exec myapp ss -tlnp
# State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port
# LISTEN 0       128     0.0.0.0:3000        0.0.0.0:*

# If ss isn't available
$ docker exec myapp netstat -tlnp
$ docker exec myapp cat /proc/net/tcp

# Test connectivity to another service
$ docker exec myapp curl -v http://db:5432
$ docker exec myapp wget -qO- http://api:3000/health
$ docker exec myapp nc -zv db 5432
# Connection to db 5432 port [tcp/postgresql] succeeded!

# Check if a port is reachable from the host
$ docker port myapp
# 3000/tcp -> 0.0.0.0:8080
$ curl -v http://localhost:8080
```

### Packet Capture with tcpdump

```bash
# Capture traffic inside the container's network namespace
$ PID=$(docker inspect --format '{{.State.Pid}}' myapp)
$ sudo nsenter --target $PID --net -- tcpdump -i eth0 -n

# Capture only HTTP traffic
$ sudo nsenter --target $PID --net -- tcpdump -i eth0 -n port 80

# Capture DNS queries
$ sudo nsenter --target $PID --net -- tcpdump -i eth0 -n port 53

# Save capture to file (analyze with Wireshark)
$ sudo nsenter --target $PID --net -- tcpdump -i eth0 -w /tmp/capture.pcap -c 1000

# Using netshoot sidecar for full network debugging
$ docker run -it --rm --net=container:myapp nicolaka/netshoot
$ tcpdump -i eth0 -n port 3000
$ iperf -c db -p 5001    # Bandwidth test
$ mtr db                 # Traceroute with statistics
```

---

## 30.8 Filesystem and Storage Debugging

```bash
# View filesystem changes made by the container
$ docker diff myapp
# A /app/logs/app.log        ← Added
# C /etc                     ← Changed
# D /tmp/old-file            ← Deleted

# Check disk usage inside the container
$ docker exec myapp df -h
$ docker exec myapp du -sh /app/*

# Check container size (writable layer)
$ docker ps -s --format "table {{.Names}}\t{{.Size}}"
# NAMES    SIZE
# myapp    25MB (virtual 150MB)
# 25MB = writable layer, 150MB = total including image

# Inspect overlay2 layers
$ docker inspect --format '{{.GraphDriver.Data.UpperDir}}' myapp
$ sudo ls -la $(docker inspect --format '{{.GraphDriver.Data.UpperDir}}' myapp)

# Copy files out of a container for inspection
$ docker cp myapp:/app/config.json ./config.json
$ docker cp myapp:/var/log/ ./container-logs/

# Check volume usage
$ docker system df -v
# Shows: images, containers, volumes, build cache sizes

# Inspect a volume
$ docker volume inspect mydata
# Shows mountpoint: /var/lib/docker/volumes/mydata/_data
$ sudo ls -la /var/lib/docker/volumes/mydata/_data
```

---

## 30.9 Performance Profiling (CPU, Memory, I/O)

### Real-Time Monitoring

```bash
# docker stats — live resource usage
$ docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
# NAME    CPU %   MEM USAGE / LIMIT   NET I/O         BLOCK I/O
# myapp   45.2%   256MiB / 512MiB     1.2MB / 500kB   50MB / 10MB

# Top processes in a container
$ docker top myapp
# PID   USER   TIME   COMMAND
# 1234  node   0:05   node server.js
# 1235  node   0:02   node worker.js
```

### CPU Profiling

```bash
# Find the container's PID
$ PID=$(docker inspect --format '{{.State.Pid}}' myapp)

# Use perf for CPU profiling (from host)
$ sudo perf top -p $PID
# Shows which functions consume the most CPU

# Record a CPU profile for 30 seconds
$ sudo perf record -p $PID -g -- sleep 30
$ sudo perf report
# Shows call graph with CPU time per function

# For Node.js: generate a CPU profile
$ docker exec myapp node --prof server.js
# Or use clinic.js
$ docker exec myapp npx clinic doctor -- node server.js
```

### Memory Profiling

```bash
# Check memory usage from cgroups
$ PID=$(docker inspect --format '{{.State.Pid}}' myapp)
$ CID=$(docker inspect --format '{{.Id}}' myapp)

# Current memory usage
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.current
# 268435456  (256 MB)

# Memory limit
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.max

# Memory events (OOM kills, high watermarks)
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/memory.events
# low 0
# high 0
# max 0
# oom 0
# oom_kill 0

# Process memory map
$ sudo cat /proc/$PID/smaps_rollup
# Shows RSS, PSS, shared/private memory

# For Java: heap dump
$ docker exec myapp jmap -dump:format=b,file=/tmp/heap.hprof 1
$ docker cp myapp:/tmp/heap.hprof ./heap.hprof
```

### I/O Profiling

```bash
# Block I/O statistics
$ cat /sys/fs/cgroup/system.slice/docker-${CID}.scope/io.stat
# 8:0 rbytes=1234567 wbytes=7654321 rios=100 wios=200

# Use iostat from the host
$ iostat -x 1
# Shows disk utilization per device

# Use iotop to find I/O-heavy processes
$ sudo iotop -p $PID
```

---

## 30.10 Core Dump Analysis

```bash
# Enable core dumps for containers
$ docker run -d \
    --ulimit core=-1 \
    --security-opt seccomp=unconfined \
    -v /tmp/cores:/cores \
    -e GOTRACEBACK=crash \
    myapp

# Set core dump pattern on the host
$ echo "/cores/core.%e.%p.%t" | sudo tee /proc/sys/kernel/core_pattern

# When the app crashes, a core dump is saved to /tmp/cores/
$ ls /tmp/cores/
# core.myapp.1234.1705312200

# Analyze with gdb
$ docker run --rm -v /tmp/cores:/cores -v $(which myapp):/app/myapp \
    ubuntu:22.04 bash -c "apt-get update && apt-get install -y gdb && \
    gdb /app/myapp /cores/core.myapp.1234.1705312200"

# For Go applications
$ docker run --rm -v /tmp/cores:/cores golang:1.22 \
    dlv core /app/myapp /cores/core.myapp.1234.1705312200
```

---

## 30.11 Common Production Issues and Solutions

### Issue 1: Container Exits Immediately

```bash
$ docker ps -a | grep myapp
# STATUS: Exited (1) 2 seconds ago

# Debug steps:
$ docker logs myapp                    # Check error output
$ docker inspect myapp | grep -A 5 State  # Check exit code
$ docker run -it myapp /bin/sh         # Start interactively
$ docker run -it myapp cat /app/config.json  # Check config
```

### Issue 2: Container Runs But App Unreachable

```bash
# Check port mapping
$ docker port myapp
# Check app is listening on 0.0.0.0, not 127.0.0.1
$ docker exec myapp ss -tlnp
# Check network connectivity
$ docker exec myapp curl -v http://localhost:3000
# Check firewall
$ sudo iptables -L -n | grep 3000
```

### Issue 3: Intermittent Connection Timeouts

```bash
# Check DNS resolution time
$ docker exec myapp time nslookup db

# Check connection pool exhaustion
$ docker exec myapp ss -s
# Shows: established, time-wait, close-wait counts

# Check for TCP connection limits
$ docker exec myapp cat /proc/sys/net/core/somaxconn
# Default: 128 — may need increasing for high-traffic apps

# Check for file descriptor limits
$ docker exec myapp cat /proc/1/limits | grep "open files"
```

### Issue 4: Slow Container Startup

```bash
# Profile startup time
$ time docker run --rm myapp echo "started"

# Check if image pull is slow
$ time docker pull myapp:latest

# Check if volume mounts are slow (NFS, EBS)
$ time docker run --rm -v mydata:/data myapp ls /data

# Check health check start-period
$ docker inspect --format '{{.Config.Healthcheck}}' myapp
```

---

## 30.12 Debugging Decision Tree

```
Container won't start?
├── docker logs → error message?
│   ├── "file not found" → check CMD/ENTRYPOINT path
│   ├── "permission denied" → check USER, file permissions
│   ├── "port already in use" → check port conflicts
│   └── "connection refused" → dependency not ready
├── Exit code 137? → OOM killed → increase --memory
├── Exit code 139? → segfault → enable core dumps
└── Exit code 1? → application error → check app logs

Container running but not working?
├── Can't reach from host?
│   ├── docker port → port mapping correct?
│   ├── ss -tlnp → app listening on 0.0.0.0?
│   └── iptables → firewall blocking?
├── Can't reach other containers?
│   ├── Same network? → docker network inspect
│   ├── DNS working? → nslookup <service>
│   └── Port open? → nc -zv <host> <port>
├── Slow performance?
│   ├── docker stats → CPU/memory usage?
│   ├── strace -c → which syscalls are slow?
│   └── perf top → which functions are hot?
└── Intermittent failures?
    ├── docker events → OOM? restarts?
    ├── tcpdump → packet loss? retransmits?
    └── ss -s → connection pool exhaustion?
```

---

## Module 30 Summary

- Follow the **debugging methodology**: status → logs → resources → config → interactive → deep analysis
- `docker logs` supports time filtering (`--since`, `--until`), tailing, and stream separation
- `docker exec` provides interactive access; use `-u root` for elevated permissions
- **nsenter** enters container namespaces from the host — works even on distroless images
- **Debug containers** (docker debug, Kubernetes ephemeral containers) add tools without modifying the image
- **Sidecar pattern**: run a debug container sharing the target's PID, network, and volumes
- **strace** traces syscalls — use `-e trace=network` for connection issues, `-c` for summaries
- **tcpdump** via nsenter captures container network traffic without installing tools in the container
- `docker diff` shows filesystem changes; `docker cp` extracts files for inspection
- **Performance profiling**: docker stats (overview), perf (CPU), cgroup files (memory), iostat (I/O)
- Exit code 137 = OOM killed, 139 = segfault, 143 = SIGTERM
- Use the **debugging decision tree** to systematically diagnose container issues

---

**Previous Module: [Module 29 - Production Deployment Patterns](module-29-production-patterns.md)**

**Next Module: [Module 31 - Docker-in-Docker, Rootless Docker, and Edge Cases](module-31-dind-rootless-edge.md)**
