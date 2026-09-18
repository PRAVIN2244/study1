# Module 6: Process Management

## 6.1 What is a Process?

A **process** is a running instance of a program. Every command you execute creates a process.

Key attributes:
- **PID** — Process ID (unique identifier)
- **PPID** — Parent Process ID (the process that spawned it)
- **UID** — User who owns the process
- **State** — Running, sleeping, stopped, zombie, etc.

### Process States

| State | Symbol | Meaning                                           |
|-------|--------|---------------------------------------------------|
| Running    | `R` | Actively using CPU or ready to run               |
| Sleeping   | `S` | Waiting for an event (I/O, signal, timer)        |
| Stopped    | `T` | Suspended (e.g., Ctrl+Z)                         |
| Zombie     | `Z` | Finished but parent hasn't collected exit status |
| Dead       | `X` | Process is being removed                         |

### Daemon, Zombie, and Orphan Processes

**Daemon**: A background service process with no controlling terminal. Examples: `sshd`, `nginx`, `cron`. Daemons typically start at boot and run continuously.

```bash
# Daemons show ? in the TTY column
$ ps aux | grep sshd
root       456  0.0  0.2  72300 18432 ?        Ss   Dec22   0:30 /usr/sbin/sshd
```

**Zombie**: A process that has finished execution but its parent hasn't collected its exit status (via `wait()`). Zombies consume no CPU or memory but hold a PID.

```bash
# Find zombie processes
$ ps aux | awk '$8 ~ /Z/ {print}'
devops    9876  0.0  0.0      0     0 pts/0    Z+   15:00   0:00 [defunct]

# Count zombies
$ ps aux | awk '$8 ~ /Z/' | wc -l
1
```

**Orphan**: A process whose parent has exited. The kernel re-parents orphans to PID 1 (`systemd`/`init`), which collects their exit status. Orphans are not harmful — they continue running normally.

**When to worry**: A few zombies are normal. Hundreds of zombies indicate a parent process that isn't calling `wait()` — find and fix (or restart) the parent. Zombies can exhaust the PID table if left unchecked.

```bash
# Find the parent of zombie processes
$ ps -eo pid,ppid,stat,comm | awk '$3 ~ /Z/ {print "Zombie PID:", $1, "Parent PID:", $2}'
Zombie PID: 9876 Parent PID: 9800
```

---

## 6.2 `ps` — Process Status

### Show your processes

```bash
$ ps
  PID TTY          TIME CMD
 1234 pts/0    00:00:00 bash
 5678 pts/0    00:00:00 ps
```

**Explanation**: Shows processes attached to your current terminal. `bash` is your shell, `ps` is the command you just ran.

### Show all processes (BSD style)

```bash
$ ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1 169344 11200 ?        Ss   Dec22   0:15 /sbin/init
root         2  0.0  0.0      0     0 ?        S    Dec22   0:00 [kthreadd]
root       456  0.0  0.2  72300 18432 ?        Ss   Dec22   0:30 /usr/sbin/sshd
www-data   890  0.1  0.5 145200 42000 ?        S    10:00   0:45 nginx: worker
devops    1234  0.0  0.0  10200  5120 pts/0    Ss   10:00   0:00 -bash
postgres  2345  0.3  1.2 320000 98000 ?        Ss   Dec22  12:30 postgres
```

**Explanation**: Column breakdown:
- `USER` — process owner
- `PID` — process ID
- `%CPU` / `%MEM` — CPU and memory usage percentage
- `VSZ` — virtual memory size (KB)
- `RSS` — resident set size (actual physical memory used, KB)
- `TTY` — terminal (`?` means no terminal — a daemon)
- `STAT` — state (`S`=sleeping, `s`=session leader, `R`=running)
- `COMMAND` — the command that started the process

### Show all processes (System V style)

```bash
$ ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 Dec22 ?        00:00:15 /sbin/init
root       456     1  0 Dec22 ?        00:00:30 /usr/sbin/sshd
devops    1234   456  0 10:00 pts/0    00:00:00 -bash
```

**Explanation**: `-e` shows all processes, `-f` shows full format. `PPID` shows the parent process — `bash` (1234) was spawned by `sshd` (456).

### Extra-full format (`-eF`)

```bash
$ ps -eF
UID        PID  PPID  C    SZ   RSS PSR STIME TTY          TIME CMD
root         1     0  0  42336 11200  0 Dec22 ?        00:00:15 /sbin/init
root       456     1  0  18075 18432  1 Dec22 ?        00:00:30 /usr/sbin/sshd
```

**Explanation**: `-eF` adds extra columns: `SZ` (size in pages), `RSS` (resident memory), `PSR` (processor/CPU core). Useful for identifying which CPU core a process runs on.

### Filter processes

```bash
# Find a specific process
$ ps aux | grep nginx
root       789  0.0  0.1  65432  8192 ?        Ss   10:00   0:00 nginx: master process
www-data   890  0.1  0.5 145200 42000 ?        S    10:00   0:45 nginx: worker process
devops    5678  0.0  0.0   6432   720 pts/0    S+   15:00   0:00 grep nginx
```

**Explanation**: The last line is the `grep` command itself. To exclude it:

```bash
$ ps aux | grep [n]ginx
root       789  0.0  0.1  65432  8192 ?        Ss   10:00   0:00 nginx: master process
www-data   890  0.1  0.5 145200 42000 ?        S    10:00   0:45 nginx: worker process
```

**Explanation**: `[n]ginx` is a regex trick — it matches "nginx" but the grep command itself shows as `grep [n]ginx`, which doesn't match.

### Show process tree

```bash
$ ps auxf
root         1  0.0  0.1 169344 11200 ?        Ss   Dec22   0:15 /sbin/init
root       456  0.0  0.2  72300 18432 ?        Ss   Dec22   0:30  \_ /usr/sbin/sshd
devops    1234  0.0  0.0  10200  5120 pts/0    Ss   10:00   0:00      \_ -bash
devops    5678  0.0  0.0   8900  3200 pts/0    R+   15:00   0:00          \_ ps auxf
root       789  0.0  0.1  65432  8192 ?        Ss   10:00   0:00  \_ nginx: master
www-data   890  0.1  0.5 145200 42000 ?        S    10:00   0:45      \_ nginx: worker
```

**Explanation**: `f` shows the process hierarchy as a tree. You can see that `bash` is a child of `sshd`, and `ps` is a child of `bash`.

### `pstree` — Visual process tree

```bash
$ pstree -p
systemd(1)─┬─sshd(456)───bash(1234)───pstree(5679)
            ├─nginx(789)───nginx(890)
            ├─postgres(2345)─┬─postgres(2346)
            │                └─postgres(2347)
            └─cron(500)
```

**Explanation**: `-p` shows PIDs. Cleaner than `ps auxf` for understanding parent-child relationships.

```bash
# Show command-line arguments in the tree
$ pstree -a
systemd
  ├─sshd
  │   └─bash
  │       └─pstree -a
  ├─nginx
  │   └─nginx
  ├─postgres -D /var/lib/postgresql/15/main
  │   ├─postgres: checkpointer
  │   └─postgres: walwriter
  └─cron -f
```

**Explanation**: `-a` shows the full command-line arguments for each process. Useful for identifying what flags a service was started with.

### Check PID 1 — The init system

```bash
$ ps -p 1
  PID TTY          TIME CMD
    1 ?        00:00:15 systemd
```

**Explanation**: `ps -p 1` shows the process with PID 1 — the first process started by the kernel at boot. On modern Linux distributions, this is `systemd`, which manages all other services. On older systems, it might be `init` or `upstart`.

```bash
# More detail about PID 1
$ ps -p 1 -o pid,comm,args
  PID COMMAND         COMMAND
    1 systemd         /sbin/init

# Verify with pstree — everything descends from PID 1
$ pstree -p | head -5
systemd(1)─┬─sshd(456)───bash(1234)
            ├─nginx(789)───nginx(890)
            ├─postgres(2345)
            └─cron(500)
```

**Why it matters**: PID 1 is the parent of all processes. If a service won't start, understanding the init system tells you which tool to use for management (`systemctl` for systemd, `service` for SysVinit). In Docker containers, PID 1 is the container's main process — if it exits, the container stops.

**Real-life example**: You SSH into a server and need to restart a service. Running `ps -p 1` confirms the init system is `systemd`, so you use `systemctl restart nginx` instead of the older `service nginx restart`.

### Filter by user

```bash
$ ps -u devops
  PID TTY          TIME CMD
 1234 pts/0    00:00:00 bash
 5678 pts/0    00:00:05 python3
 6789 pts/0    00:00:00 vim

# Count processes per user
$ ps aux --no-header | awk '{print $1}' | sort | uniq -c | sort -rn
     50 root
     15 devops
      8 www-data
      5 postgres
```

### Show specific columns only

```bash
$ ps -eo pid,ppid,user,%cpu,%mem,stat,start,time,comm --sort=-%cpu | head -10
  PID  PPID USER     %CPU %MEM STAT  STARTED     TIME COMMAND
 3456     1 myapp    85.0  8.5 Sl   09:00:00 00:45:30 java
 2345     1 postgres 15.0  1.2 Ss   Dec22    12:30:00 postgres
  890   789 www-data  2.0  0.5 S    10:00:00 00:00:45 nginx
```

**Explanation**: `-eo` lets you pick exactly which columns to show. Useful for scripting and monitoring.

### Show top CPU/memory consumers

```bash
# Top 5 CPU consumers
$ ps aux --sort=-%cpu | head -6
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
postgres  2345  5.2  1.2 320000 98000 ?        Ss   Dec22  12:30 postgres
www-data   890  2.1  0.5 145200 42000 ?        S    10:00   0:45 nginx: worker
java      3456  1.8  8.5 2500000 680000 ?      Sl   09:00   3:20 java -jar app.jar

# Top 5 memory consumers
$ ps aux --sort=-%mem | head -6
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
java      3456  1.8  8.5 2500000 680000 ?      Sl   09:00   3:20 java -jar app.jar
postgres  2345  5.2  1.2 320000 98000 ?        Ss   Dec22  12:30 postgres
```

---

## 6.3 `top` — Real-Time Process Monitor

```bash
$ top
top - 15:00:00 up 45 days,  3:12,  2 users,  load average: 0.52, 0.38, 0.25
Tasks: 128 total,   1 running, 126 sleeping,   0 stopped,   1 zombie
%Cpu(s):  5.2 us,  1.3 sy,  0.0 ni, 92.8 id,  0.5 wa,  0.0 hi,  0.2 si,  0.0 st
MiB Mem :   7953.4 total,   2145.6 free,   3200.8 used,   2607.0 buff/cache
MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   4450.2 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
 3456 java      20   0 2500000 680000  12000 S   5.2   8.5   3:20.45 java
 2345 postgres  20   0  320000  98000   8000 S   2.1   1.2  12:30.12 postgres
  890 www-data  20   0  145200  42000   6000 S   1.0   0.5   0:45.30 nginx
```

**Explanation** of the header:
- **Load average**: `0.52, 0.38, 0.25` — CPU demand over 1, 5, 15 minutes. On a 2-core system, values above 2.0 mean CPU saturation.
- **Tasks**: 1 running, 1 zombie (zombie = process finished but parent hasn't acknowledged)
- **%Cpu(s)**: `us`=user, `sy`=system/kernel, `id`=idle, `wa`=waiting for I/O (high `wa` = disk bottleneck), `st`=stolen by hypervisor (high `st` = noisy neighbor in cloud)
- **MiB Mem**: Total, free, used, buff/cache. Linux uses free RAM for caching — `avail Mem` is what's actually available for new processes.

### Interactive `top` commands

| Key   | Action                                    |
|-------|-------------------------------------------|
| `q`   | Quit                                      |
| `M`   | Sort by memory usage                      |
| `P`   | Sort by CPU usage                         |
| `k`   | Kill a process (enter PID)                |
| `r`   | Renice a process (change priority)        |
| `1`   | Show individual CPU cores                 |
| `c`   | Show full command path                    |
| `f`   | Choose which fields to display            |
| `H`   | Toggle threads view                       |
| `u`   | Filter by user                            |

### `htop` — Better interactive monitor

```bash
$ htop
```

**Explanation**: `htop` is an improved version of `top` with color coding, mouse support, and easier navigation. Install with `sudo apt install htop`.

---

## 6.4 Signals & `kill` — Terminate Processes

### Common signals

| Signal    | Number | Action                                          |
|-----------|--------|-------------------------------------------------|
| `SIGHUP`  | 1      | Hangup — often used to reload configuration     |
| `SIGINT`  | 2      | Interrupt (same as Ctrl+C)                      |
| `SIGKILL` | 9      | Force kill — cannot be caught or ignored         |
| `SIGTERM` | 15     | Graceful termination (default)                   |
| `SIGSTOP` | 19     | Pause process (same as Ctrl+Z)                  |
| `SIGCONT` | 18     | Resume a stopped process                         |

### List all available signals

```bash
$ kill -l
 1) SIGHUP   2) SIGINT   3) SIGQUIT  4) SIGILL   5) SIGTRAP
 6) SIGABRT  7) SIGBUS   8) SIGFPE   9) SIGKILL 10) SIGUSR1
11) SIGSEGV 12) SIGUSR2 13) SIGPIPE 14) SIGALRM 15) SIGTERM
...
```

**Explanation**: `kill -l` lists all signal names and numbers supported by your system. Use this when you know the number but not the name (or vice versa).

### Kill a process by PID

Syntax:

```bash
$ kill <PID>
```

**Explanation**: Replace `<PID>` with the process ID you want to terminate.

```bash
# Graceful termination (default, sends SIGTERM)
$ kill 3456
```

**Explanation**: Sends `SIGTERM` (signal 15). The process can catch this signal, clean up resources, and exit gracefully.

```bash
# Force kill (when SIGTERM doesn't work)
$ kill -9 3456
```

**Explanation**: `SIGKILL` cannot be caught or ignored. The kernel immediately terminates the process. Use as a last resort — the process can't clean up, which may cause data corruption.

```bash
# Reload configuration (common for daemons)
$ sudo kill -HUP 789
```

**Explanation**: Sends `SIGHUP` to nginx master process (PID 789). Nginx reloads its configuration without dropping connections.

### Kill by name

```bash
$ killall nginx
$ killall -9 python3
```

**Explanation**: `killall` sends a signal to all processes matching the name.

### `pkill` — Kill by pattern

```bash
$ pkill -f "python3 app.py"
```

**Explanation**: `-f` matches against the full command line, not just the process name. Useful when multiple Python scripts are running.

```bash
# Kill all processes of a user
$ sudo pkill -u john
```

### `pgrep` — Find PIDs by pattern

```bash
$ pgrep nginx
789
890

$ pgrep -la nginx
789 nginx: master process /usr/sbin/nginx
890 nginx: worker process
```

**Explanation**: `pgrep` finds PIDs without killing. `-l` shows the process name, `-a` shows the full command.

---

## 6.5 Job Control

### Run a command in the background (`&`)

```bash
$ sleep 300 &
[1] 6789
```

**Explanation**: `&` runs the command in the background. `[1]` is the job number, `6789` is the PID.

### List background jobs

```bash
$ jobs
[1]+  Running                 sleep 300 &
[2]-  Stopped                 vim config.yaml
```

**Explanation**: Shows all jobs in the current shell. `+` marks the current job, `-` marks the previous job.

### Suspend a foreground process (`Ctrl+Z`)

```bash
$ vim config.yaml
# Press Ctrl+Z
[2]+  Stopped                 vim config.yaml
```

**Explanation**: `Ctrl+Z` sends `SIGSTOP`, suspending the process. It's still in memory but not running.

### Resume in background (`bg`)

```bash
$ bg %2
[2]+ vim config.yaml &
```

**Explanation**: `bg %2` resumes job 2 in the background. `%2` refers to job number 2.

### Bring to foreground (`fg`)

```bash
$ fg %1
sleep 300
```

**Explanation**: `fg %1` brings job 1 back to the foreground. You can also use `fg` without a number to bring the most recent job.

---

## 6.6 `nohup` — Survive Logout

```bash
$ nohup python3 long_task.py &
[1] 7890
nohup: ignoring input and appending output to 'nohup.out'
```

**Explanation**: `nohup` prevents the process from being killed when you log out (ignores `SIGHUP`). Output goes to `nohup.out` by default.

### Redirect output

```bash
# Redirect output to a specific log file
$ nohup bash script.sh > out.log &
[1] 7891

# Redirect both stdout and stderr
$ nohup ./backup.sh > /var/log/backup.log 2>&1 &
[1] 7892

# Common production pattern
$ nohup bash script.sh > out.log 2>&1 &
```

**Explanation**: `> out.log` redirects stdout to a file. `2>&1` also captures stderr. The process continues running after you disconnect. Common for long migrations, backups, and remote jobs.

### `disown` — Detach a running job

```bash
$ python3 server.py &
[1] 8000

$ disown %1
```

**Explanation**: If you forgot `nohup`, `disown` removes the job from the shell's job table, preventing it from receiving `SIGHUP` on logout.

---

## 6.7 `systemctl` — Service Management (systemd)

`systemd` is the init system and service manager on modern Linux distributions.

### Check service status

```bash
$ sudo systemctl status nginx
● nginx.service - A high performance web server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Wed 2025-02-05 10:00:00 UTC; 5h ago
       Docs: man:nginx(8)
   Main PID: 789 (nginx)
      Tasks: 3 (limit: 4915)
     Memory: 12.5M
        CPU: 1.234s
     CGroup: /system.slice/nginx.service
             ├─789 "nginx: master process /usr/sbin/nginx"
             └─890 "nginx: worker process"

Feb 05 10:00:00 server systemd[1]: Starting A high performance web server...
Feb 05 10:00:00 server systemd[1]: Started A high performance web server.
```

**Explanation**:
- `Loaded: loaded (...; enabled)` — service is configured and will start on boot
- `Active: active (running)` — currently running
- `Main PID: 789` — the master process ID
- `Memory: 12.5M` — memory consumption
- The CGroup section shows all processes belonging to this service

### Start / Stop / Restart

```bash
$ sudo systemctl start nginx       # Start the service
$ sudo systemctl stop nginx        # Stop the service
$ sudo systemctl restart nginx     # Stop then start
$ sudo systemctl reload nginx      # Reload config without stopping
```

**Explanation**: `reload` is preferred over `restart` when possible — it applies config changes without dropping active connections.

### Enable / Disable (boot behavior)

```bash
$ sudo systemctl enable nginx      # Start on boot
Created symlink /etc/systemd/system/multi-user.target.wants/nginx.service

$ sudo systemctl disable nginx     # Don't start on boot
Removed /etc/systemd/system/multi-user.target.wants/nginx.service

$ sudo systemctl enable --now nginx  # Enable AND start immediately
```

### Check if a service is active/enabled

```bash
$ systemctl is-active nginx
active

$ systemctl is-enabled nginx
enabled
```

**Explanation**: Returns a single word — useful in scripts:

```bash
if systemctl is-active --quiet nginx; then
    echo "Nginx is running"
fi
```

### List all services

```bash
$ systemctl list-units --type=service --state=running
UNIT                     LOAD   ACTIVE SUB     DESCRIPTION
cron.service             loaded active running Regular background program processing
nginx.service            loaded active running A high performance web server
sshd.service             loaded active running OpenBSD Secure Shell server
postgresql.service       loaded active running PostgreSQL RDBMS
```

### List failed services

```bash
$ systemctl --failed
UNIT              LOAD   ACTIVE SUB    DESCRIPTION
myapp.service     loaded failed failed My Application
```

### View service logs

```bash
$ sudo journalctl -u nginx
Feb 05 10:00:00 server systemd[1]: Starting A high performance web server...
Feb 05 10:00:00 server nginx[789]: nginx: configuration file /etc/nginx/nginx.conf test is successful
Feb 05 10:00:00 server systemd[1]: Started A high performance web server.

# Follow logs in real-time
$ sudo journalctl -u nginx -f

# Show last 50 lines
$ sudo journalctl -u nginx -n 50

# Show logs since a specific time
$ sudo journalctl -u nginx --since "2025-02-05 10:00:00"

# Show logs from the last hour
$ sudo journalctl -u nginx --since "1 hour ago"
```

---

## 6.8 Creating a Custom systemd Service

### Create a service file

```bash
$ sudo cat > /etc/systemd/system/myapp.service << 'EOF'
[Unit]
Description=My Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/server --port 8080
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=NODE_ENV=production
EnvironmentFile=/opt/myapp/config/.env

[Install]
WantedBy=multi-user.target
EOF
```

**Explanation**:
- `[Unit]`: `After` ensures it starts after networking and postgres. `Wants` declares a soft dependency.
- `[Service]`: `Type=simple` means the process itself is the service. `Restart=on-failure` auto-restarts on crashes. `RestartSec=5` waits 5 seconds before restarting.
- `[Install]`: `WantedBy=multi-user.target` means it starts in normal multi-user mode (standard server boot).

### Activate the service

```bash
$ sudo systemctl daemon-reload      # Reload systemd to pick up new file
$ sudo systemctl enable --now myapp  # Enable and start
$ sudo systemctl status myapp       # Verify
```

---

## 6.9 `pidstat` — Per-Process Statistics

```bash
# CPU usage per process every 1 second, 5 samples
$ pidstat 1 5
15:00:01  UID  PID   %usr  %system  %guest  %wait  %CPU  CPU  Command
15:00:02 1000 3456  80.00     5.00    0.00   2.00 85.00    0  java
15:00:02   33  890   1.00     0.50    0.00   0.00  1.50    1  nginx

# Memory usage per process
$ pidstat -r 1 3
15:00:01  UID  PID  minflt/s  majflt/s     VSZ     RSS   %MEM  Command
15:00:02 1000 3456    100.00      0.00 6500000 3600000  45.00  java

# Disk I/O per process
$ pidstat -d 1 3
15:00:01  UID  PID   kB_rd/s   kB_wr/s  Command
15:00:02   26 2345   2000.00  45000.00  postgres
15:00:02 1000 3456   3000.00   5000.00  java

# All stats for a specific PID
$ pidstat -p 3456 -urd 1 5
```

**Explanation**: `pidstat` is part of the `sysstat` package. It gives per-process CPU, memory, and I/O stats over time — more detailed than `top` for specific process investigation.

---

## 6.10 `nice` / `renice` / `ionice` — Process Priority

### Start a process with lower priority

```bash
# Nice values: -20 (highest priority) to 19 (lowest priority)
# Default is 0

$ nice -n 10 ./heavy_computation.sh    # Lower priority
$ nice -n -5 ./important_task.sh       # Higher priority (needs root)
$ sudo nice -n -10 ./critical_job.sh   # Even higher priority
```

### Change priority of a running process

```bash
$ ps aux | grep heavy_computation
devops  9876  95.0  2.3  500000 180000 ?  R  14:00  5:30 ./heavy_computation.sh

# Lower its priority so other processes get more CPU
$ sudo renice 19 -p 9876
9876 (process ID) old priority 0, new priority 19

# Verify
$ ps -o pid,ni,comm -p 9876
  PID  NI COMMAND
 9876  19 heavy_computation
```

### Control I/O priority

```bash
# Set lowest I/O priority (idle — only uses disk when nothing else needs it)
$ sudo ionice -c 3 -p 9876

# Set best-effort with low priority
$ sudo ionice -c 2 -n 7 -p 9876

# Start a backup with low I/O priority
$ ionice -c 3 nice -n 19 tar czf /backup/full.tar.gz /opt/myapp/
```

**Explanation**: `ionice` classes: `1`=realtime, `2`=best-effort (default), `3`=idle. Use class 3 for backups and batch jobs so they don't slow down production services.

---

## 6.11 `lsof` — List Open Files

Every resource in Linux is a file — sockets, pipes, devices. `lsof` shows what files a process has open.

### Find what's using a port

```bash
$ sudo lsof -i :8080
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
java     3456  myapp   18u  IPv6  45678      0t0  TCP *:http-alt (LISTEN)
java     3456  myapp   25u  IPv6  56789      0t0  TCP server:8080->10.0.0.5:52340 (ESTABLISHED)
```

**Explanation**: Shows that Java process 3456 is listening on port 8080 and has one active connection from 10.0.0.5.

### Find all files opened by a process

```bash
$ sudo lsof -p 3456 | head -15
COMMAND  PID  USER   FD   TYPE DEVICE SIZE/OFF    NODE NAME
java    3456 myapp  cwd    DIR    8,1     4096  262145 /opt/myapp
java    3456 myapp  rtd    DIR    8,1     4096       2 /
java    3456 myapp  txt    REG    8,1  1234567  524289 /usr/bin/java
java    3456 myapp    0r   CHR    1,3      0t0       6 /dev/null
java    3456 myapp    1w   REG    8,1   500000  786433 /var/log/myapp/stdout.log
java    3456 myapp    2w   REG    8,1   120000  786434 /var/log/myapp/stderr.log
java    3456 myapp   10r   REG    8,1  5000000  655361 /opt/myapp/lib/app.jar
java    3456 myapp   18u  IPv6  45678      0t0     TCP *:8080 (LISTEN)
```

**Explanation**: `FD` column: `cwd`=current working directory, `txt`=program text, `0r`=stdin (read), `1w`=stdout (write), `18u`=socket (read/write). This tells you exactly what files and connections a process is using.

### Find who's using a file or directory

```bash
$ sudo lsof /var/log/syslog
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF   NODE NAME
rsyslogd  500 root    7w   REG    8,1  2300000 131073 /var/log/syslog

# Find processes using a mount point (before unmounting)
$ sudo lsof +D /mnt/data
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
bash     1234 devops  cwd    DIR    8,17     4096    2 /mnt/data
python3  5678 devops    3r   REG    8,17  1000000  100 /mnt/data/input.csv
```

**Explanation**: This is why `umount` says "device is busy" — processes have files open on that mount. Kill or redirect them first.

### Find all network connections for a user

```bash
$ sudo lsof -i -u devops
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
ssh      4567 devops    3u  IPv4  34567      0t0  TCP server:52340->10.0.0.5:22 (ESTABLISHED)
curl     5678 devops    5u  IPv4  45678      0t0  TCP server:52341->api.example.com:443 (ESTABLISHED)
```

### Find deleted files still held open (recovering disk space)

```bash
$ sudo lsof | grep '(deleted)'
java     3456 myapp   1w   REG    8,1 15000000000 786433 /var/log/myapp/huge.log (deleted)
```

**Explanation**: The file was deleted but the process still holds it open, so the disk space isn't freed. Restart the process or truncate the file descriptor:

```bash
$ sudo truncate -s 0 /proc/3456/fd/1
```

---

## 6.12 `strace` — Trace System Calls

`strace` shows every system call a process makes. Invaluable for debugging why a process hangs, crashes, or behaves unexpectedly.

### Trace a running command

```bash
$ strace ls /tmp
execve("/usr/bin/ls", ["ls", "/tmp"], ...) = 0
openat(AT_FDCWD, "/tmp", O_RDONLY|O_NONBLOCK|O_DIRECTORY) = 3
getdents64(3, /* 5 entries */, 32768)   = 160
write(1, "file1.txt  file2.txt  session_ab"..., 45) = 45
close(3)                                = 0
exit_group(0)                           = ?
```

**Explanation**: Shows `ls` opening `/tmp`, reading directory entries, writing output, and exiting. Each line is a system call with its return value.

### Trace a running process by PID

```bash
$ sudo strace -p 3456
strace: Process 3456 attached
read(18, 0x7f8a1c000000, 8192)         = ? ERESTARTSYS
--- SIGALRM {si_signo=SIGALRM, si_code=SI_KERNEL} ---
rt_sigreturn({mask=[]})                 = -1 EINTR
poll([{fd=18, events=POLLIN}], 1, 30000) = 0 (Timeout)
write(1, "Heartbeat check at 15:00:30\n", 28) = 28
```

**Explanation**: Attach to a running process to see what it's doing right now. Here the process is waiting for data on fd 18 (a socket), timing out, and writing a heartbeat.

### Trace only specific system calls

```bash
# Only file operations
$ strace -e trace=open,read,write,close ls /tmp

# Only network operations
$ sudo strace -e trace=network -p 3456

# Only file-related calls
$ strace -e trace=file ls /tmp
```

### Trace with timestamps

```bash
$ sudo strace -t -p 3456
15:00:30 poll([{fd=18, events=POLLIN}], 1, 30000) = 0 (Timeout)
15:00:30 write(1, "Heartbeat\n", 10)    = 10
15:01:00 poll([{fd=18, events=POLLIN}], 1, 30000) = 1 ([{fd=18, revents=POLLIN}])
15:01:00 read(18, "GET /api/users HTTP/1.1\r\n", 8192) = 24
```

### Count system calls (profiling)

```bash
$ strace -c ls /tmp
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 25.00    0.000050          10         5           openat
 20.00    0.000040           8         5           close
 15.00    0.000030           6         5           fstat
 10.00    0.000020           4         5           read
 10.00    0.000020          20         1           getdents64
 10.00    0.000020          20         1           write
 10.00    0.000020           4         5           mmap
------ ----------- ----------- --------- --------- ----------------
100.00    0.000200                    27           total
```

**Explanation**: `-c` summarizes system call usage. Useful for finding bottlenecks — if a process spends most time in `read` or `write`, it's I/O bound.

---

## 6.13 `vmstat` — Virtual Memory Statistics

```bash
$ vmstat 1 5
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2  0      0 2197504 204800 2462720   0    0    50   200  500  800  5  1 93  1  0
 1  0      0 2195000 204800 2464000   0    0    10   150  480  750  4  1 94  1  0
 3  1      0 2190000 204800 2465000   0    0   200  5000  600 1200 15  5 70 10  0
 5  2      0 2100000 204800 2466000   0    0   500 10000  800 2000 25  8 50 17  0
 8  3      0 2000000 204800 2467000   0    0  1000 20000 1200 3500 40 12 30 18  0
```

**Explanation**:
- `r` — processes waiting for CPU (run queue). High = CPU bottleneck
- `b` — processes blocked on I/O. High = disk bottleneck
- `swpd` — swap used. Increasing = memory pressure
- `si/so` — swap in/out. Non-zero = actively swapping (bad for performance)
- `bi/bo` — blocks read/written to disk
- `in` — interrupts per second
- `cs` — context switches per second. Very high = too many processes competing
- `us/sy/id/wa/st` — CPU breakdown (user/system/idle/iowait/steal)

The example shows a system going from healthy (line 1) to overloaded (line 5): run queue growing, I/O increasing, idle dropping.

---

## 6.14 `/proc` Filesystem

The `/proc` virtual filesystem exposes kernel and process information as files.

### Process information

```bash
$ cat /proc/789/status | head -10
Name:   nginx
State:  S (sleeping)
Tgid:   789
Pid:    789
PPid:   1
Uid:    0       0       0       0
Gid:    0       0       0       0
Threads:        1
VmPeak: 67000 kB
VmRSS:  8192 kB
```

**Explanation**: Every process has a directory `/proc/<PID>/` with detailed information. `VmRSS` is the actual physical memory used.

### System information from `/proc`

```bash
$ cat /proc/cpuinfo | grep "model name" | head -1
model name      : Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz

$ cat /proc/meminfo | head -5
MemTotal:        8142848 kB
MemFree:         2197504 kB
MemAvailable:    4556800 kB
Buffers:          204800 kB
Cached:          2462720 kB

$ cat /proc/loadavg
0.52 0.38 0.25 1/128 5680
```

**Explanation**: `/proc/cpuinfo` shows CPU details. `/proc/meminfo` shows memory stats. `/proc/loadavg` shows load averages and total processes.

---

## 6.15 Practical DevOps Scenarios

### Scenario 1: Find and kill a runaway process

```bash
# Find the process consuming the most CPU
$ ps aux --sort=-%cpu | head -5
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
devops    9876 98.5  2.3 500000 180000 ?       R    14:00   5:30 python3 broken_script.py

# Graceful kill first
$ kill 9876

# If it doesn't stop after a few seconds
$ kill -9 9876
```

### Scenario 2: Debug a failing service

```bash
# Check status
$ sudo systemctl status myapp
● myapp.service - My Application
     Active: failed (Result: exit-code) since ...

# Check logs
$ sudo journalctl -u myapp -n 30 --no-pager

# Check if port is in use
$ sudo ss -tlnp | grep 8080

# Try starting manually to see errors
$ sudo -u myapp /opt/myapp/bin/server --port 8080
```

### Scenario 3: Monitor system resources

```bash
# Quick system overview
$ uptime
$ free -h
$ df -h

# Real-time monitoring
$ top -bn1 | head -20    # Batch mode, 1 iteration (for scripts)

# Check for zombie processes
$ ps aux | awk '$8 ~ /Z/ {print}'
```

### Scenario 4: Process consuming too much memory (OOM risk)

```bash
# Step 1: Identify the process
$ ps aux --sort=-%mem | head -5
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
java      3456  5.2 85.0 6500000 6800000 ?     Sl   09:00  12:30 java -Xmx8g -jar app.jar

# Step 2: Check its memory map
$ sudo pmap -x 3456 | tail -3
total kB         6500000  6800000  6400000

# Step 3: Check if OOM killer has been active
$ dmesg -T | grep -i "oom\|killed"
[Wed Feb  5 14:30:00 2025] Out of memory: Killed process 3456 (java) total-vm:6500000kB

# Step 4: Check OOM score (higher = more likely to be killed)
$ cat /proc/3456/oom_score
850

# Step 5: Protect a process from OOM killer
$ echo -1000 | sudo tee /proc/3456/oom_score_adj
```

### Scenario 5: Find what's holding a deleted file open

```bash
# Disk is full but you can't find large files
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   49G    0G  99% /

$ du -sh / 2>/dev/null
35G     /
# Only 35G accounted for — 14G is in deleted-but-open files

# Find them
$ sudo lsof | grep '(deleted)' | sort -k7 -n -r | head -5
nginx    890  root   5w   REG  8,1 10000000000 786433 /var/log/nginx/access.log (deleted)

# Fix: restart the process to release the file handle
$ sudo systemctl restart nginx
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   39G    8G  83% /
```

### Scenario 6: Debug a process that hangs

```bash
# Step 1: Check what the process is doing
$ sudo strace -p 3456
poll([{fd=18, events=POLLIN}], 1, -1)   # Waiting forever on a socket

# Step 2: Check what connections it has
$ sudo lsof -p 3456 -i
java  3456 myapp  18u  IPv4  45678  TCP server:52340->db-server:5432 (ESTABLISHED)

# Step 3: The process is waiting on a database connection
# Check if the database is responding
$ nc -zv db-server 5432
Connection to db-server 5432 port [tcp/postgresql] succeeded!

# Step 4: Check for lock contention
$ sudo strace -e trace=futex -c -p 3456
# High futex calls = thread lock contention
```

---

## 6.16 Additional Process Commands (Requested Variants)

### More `ps` formats

```bash
$ ps -ely
$ ps -axu
$ ps -ax
$ ps -axjf
$ ps -ejH
$ ps axms
$ ps -aux
```

**Explanation**:
- These are alternate SysV/BSD formats used in different teams/scripts.
- `-axjf` and `-ejH` are useful for tree-style hierarchy views.
- `-eLf`/`axms` include thread-level information.

### `pstree -a <pid>`

```bash
$ pstree -a pid

$ pstree -a 1234
systemd
  `-sshd
      `-bash
          `-python3 app.py
```

**Purpose**: Show process ancestry for a specific PID with arguments.

### `tty` and `id -u username`

```bash
$ tty
/dev/pts/0

$ id -u devops
1000
```

**Use case**: Confirm terminal/session and numeric UID for permissions/debug scripts.

### `killall` and `pkill`

```bash
$ killall process_name
$ pkill process_name
```

**Purpose**: Terminate processes by name/pattern instead of PID.

### `exec vim` and `exec ls`

```bash
$ exec vim
# current shell is replaced by vim

$ exec ls
# current shell is replaced by ls and exits afterward
```

**Purpose**: Replace the current shell process with another program (no child process).

## Summary

| Command      | Purpose                      | Key Usage                           |
|--------------|------------------------------|-------------------------------------|
| `ps`         | List processes               | `ps aux`, `ps -ef`, `ps auxf`       |
| `top`/`htop` | Real-time monitor            | Interactive, sort by CPU/MEM        |
| `kill`       | Send signal to process       | `kill PID`, `kill -9 PID`           |
| `killall`    | Kill by name                 | `killall nginx`                     |
| `pkill`      | Kill by pattern              | `pkill -f "pattern"`               |
| `pgrep`      | Find PIDs by pattern         | `pgrep -la nginx`                   |
| `jobs`       | List background jobs         | —                                   |
| `bg` / `fg`  | Background / foreground      | `bg %1`, `fg %1`                    |
| `nohup`      | Survive logout               | `nohup cmd &`                       |
| `systemctl`  | Manage systemd services      | `start`, `stop`, `status`, `enable` |
| `journalctl` | View systemd logs            | `-u service`, `-f`, `--since`       |
| `lsof`       | List open files/ports        | `lsof -i :8080`, `lsof -p PID`     |
| `strace`     | Trace system calls           | `strace -p PID`, `strace -c cmd`   |
| `vmstat`     | Virtual memory stats         | `vmstat 1 5`                        |
| `pstree`     | Visual process tree          | `pstree -p`                         |

**Next Module**: [07 - Package Management](../07-package-management/README.md)

---

---

## 6.10 Interview Questions — Module 6

**Q1: What is the difference between a zombie and an orphan process?**

A **zombie** (defunct) process has completed execution but its parent hasn't called `wait()` to collect its exit status — it still occupies a PID. An **orphan** process's parent has terminated — it gets adopted by PID 1 (init/systemd). Zombies are harmless individually but can exhaust the PID table. Fix: restart the parent process.

```bash
ps aux | grep 'Z'                    # Find zombies
ps -eo pid,ppid,stat,cmd | grep Z    # Find zombie's parent
```

**Q2: How do you find and kill a process using a specific port?**

```bash
sudo ss -tlnp | grep :8080           # Find PID using port 8080
sudo lsof -i :8080                   # Alternative
kill -15 <PID>                        # Graceful termination (SIGTERM)
kill -9 <PID>                         # Force kill (SIGKILL) — last resort
sudo fuser -k 8080/tcp               # Kill process on port directly
```

**Q3: What is the difference between SIGTERM (15) and SIGKILL (9)?**

SIGTERM asks the process to terminate gracefully — it can catch the signal, clean up resources, and exit. SIGKILL forces immediate termination — the process cannot catch or ignore it. Always try SIGTERM first; use SIGKILL only when the process is unresponsive.

**Q4: How do nice and renice work?**

`nice` sets the priority when starting a process (-20 = highest, 19 = lowest). `renice` changes priority of a running process. Only root can set negative (higher) priority values.

```bash
nice -n 10 ./backup.sh               # Start with lower priority
sudo renice -5 -p <PID>              # Increase priority of running process
```

**Q5: What is `nohup` and when do you use it?**

`nohup` runs a command immune to hangup signals (SIGHUP) — the process continues running after you log out. Combined with `&` for background execution.

```bash
nohup ./long-running-script.sh > output.log 2>&1 &
```
