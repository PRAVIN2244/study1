# Module 5: First Day on the Terminal

## 1.4 Checking Your Linux System

### Check the kernel version

```bash
$ uname -r
6.1.0-18-amd64
```

**Explanation**: `uname -r` prints the running kernel's release version. Here, `6.1.0-18-amd64` means kernel version 6.1.0, patch 18, for 64-bit AMD/Intel architecture.

### Check full system info

```bash
$ uname -a
Linux devops-server 6.1.0-18-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1 (2024-02-01) x86_64 GNU/Linux
```

**Explanation**: `uname -a` shows all system information:
- `Linux` — kernel name
- `devops-server` — hostname
- `6.1.0-18-amd64` — kernel release
- `x86_64` — machine architecture
- `GNU/Linux` — operating system

### Check CPU architecture

```bash
$ uname -m
x86_64
```

**Explanation**: `uname -m` prints the machine's CPU architecture. Common values:
- `x86_64` — 64-bit Intel/AMD (most cloud servers)
- `aarch64` or `arm64` — ARM-based (AWS Graviton, Apple M-series, Raspberry Pi)
- `i686` — 32-bit Intel/AMD (legacy systems)

**Why it matters**: You need the correct architecture when downloading binaries, Docker images, or installing software. A binary compiled for `x86_64` won't run on `aarch64`.

```bash
# Download the correct binary based on architecture
$ ARCH=$(uname -m)
$ echo $ARCH
x86_64

# Example: downloading the right version of a tool
$ wget https://example.com/tool-${ARCH}.tar.gz
```

**Real-life example**: When installing Docker, kubectl, or Terraform on a server, the download URL includes the architecture. Running `uname -m` tells you whether to grab the `amd64` or `arm64` build.

---

### Check the distribution

```bash
$ cat /etc/os-release
NAME="Ubuntu"
VERSION="22.04.3 LTS (Jammy Jellyfish)"
ID=ubuntu
ID_LIKE=debian
VERSION_ID="22.04"
PRETTY_NAME="Ubuntu 22.04.3 LTS"
```

**Explanation**: `/etc/os-release` is a standard file containing distribution identity. `ID_LIKE=debian` tells you this distro is Debian-based (so it uses `apt`).

### Check system uptime

```bash
$ uptime
 14:23:07 up 45 days,  3:12,  2 users,  load average: 0.15, 0.10, 0.08
```

**Explanation**:
- `up 45 days, 3:12` — system has been running for 45 days
- `2 users` — two active login sessions
- `load average: 0.15, 0.10, 0.08` — CPU load over the last 1, 5, and 15 minutes (lower is better; values above the number of CPU cores indicate saturation)

### Check hostname

```bash
$ hostname
devops-server

$ hostnamectl
 Static hostname: devops-server
       Icon name: computer-vm
         Chassis: vm
      Machine ID: a1b2c3d4e5f6...
         Boot ID: f6e5d4c3b2a1...
  Virtualization: kvm
Operating System: Ubuntu 22.04.3 LTS
          Kernel: Linux 6.1.0-18-amd64
    Architecture: x86-64
```

**Explanation**: `hostname` prints the system name. `hostnamectl` gives detailed info including whether you're running in a VM (`Virtualization: kvm`), which is common in cloud/DevOps environments.

### Check CPU count — `nproc`

```bash
$ nproc
4
```

**Explanation**: `nproc` prints the number of processing units (CPU cores) available. This is one of the first things to check when diagnosing performance — you compare load average against this number.

```bash
# Load average vs CPU count
$ uptime
 15:00:00 up 45 days, load average: 8.50, 7.20, 5.10

$ nproc
4
# Load 8.50 on 4 CPUs = system is 2x overloaded
```

### Detailed CPU info — `lscpu`

```bash
$ lscpu
Architecture:            x86_64
CPU op-mode(s):          32-bit, 64-bit
CPU(s):                  4
On-line CPU(s) list:     0-3
Thread(s) per core:      2
Core(s) per socket:      2
Socket(s):               1
Model name:              Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz
CPU MHz:                 2300.000
L1d cache:               32K
L1i cache:               32K
L2 cache:                256K
L3 cache:                46080K
Virtualization:          VT-x
Hypervisor vendor:       Xen
Virtualization type:     full
```

**Explanation**:
- `CPU(s): 4` — total logical CPUs (same as `nproc`)
- `Thread(s) per core: 2` — hyperthreading is enabled (2 threads per physical core)
- `Core(s) per socket: 2` — 2 physical cores per CPU chip
- `Socket(s): 1` — 1 physical CPU chip
- So: 1 socket × 2 cores × 2 threads = 4 logical CPUs
- `Hypervisor vendor: Xen` — running on AWS (Xen-based virtualization)

### Raw CPU info from `/proc/cpuinfo`

```bash
# Count physical CPUs
$ grep -c "processor" /proc/cpuinfo
4

# Get CPU model
$ grep "model name" /proc/cpuinfo | head -1
model name      : Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz

# Get CPU speed
$ grep "cpu MHz" /proc/cpuinfo | head -1
cpu MHz         : 2300.000

# Get cache size
$ grep "cache size" /proc/cpuinfo | head -1
cache size      : 46080 KB
```

**Explanation**: `/proc/cpuinfo` is the raw kernel file with all CPU details. `nproc` and `lscpu` are easier to use, but `/proc/cpuinfo` is always available and works in minimal containers where other tools may not be installed.

### Quick system resource summary

```bash
# One-liner: CPUs, RAM, Disk
$ echo "CPUs: $(nproc) | RAM: $(free -h | awk '/Mem/ {print $2}') | Disk: $(df -h / | awk 'NR==2 {print $2}')"
CPUs: 4 | RAM: 7.8Gi | Disk: 50G
```

### 32-bit vs 64-bit Architecture

| Feature | 32-bit | 64-bit |
|---------|--------|--------|
| Max addressable RAM | ~4 GB | 16 exabytes (theoretical) |
| Performance | Slower, limited registers | Faster, wider data paths |
| Software compatibility | 32-bit only | Runs both 32-bit and 64-bit |
| Architecture identifiers | i386, i486, i586, i686 | x86_64, amd64 |

```bash
# Check architecture
$ arch
x86_64

$ uname -m
x86_64

# getconf for detailed info
$ getconf LONG_BIT
64
```

**Real-world**: All modern cloud instances are 64-bit. You only encounter 32-bit on legacy embedded systems or very old hardware.

### `dmidecode` — Hardware Information from BIOS/UEFI

`dmidecode` reads the DMI (Desktop Management Interface) table to report hardware details without opening the physical machine.

```bash
# All hardware info (requires root)
$ sudo dmidecode | more

# Filter by type
$ sudo dmidecode -t 0      # BIOS information
$ sudo dmidecode -t 1      # System manufacturer, model, serial
$ sudo dmidecode -t 2      # Baseboard (motherboard) info
$ sudo dmidecode -t 4      # Processor details
$ sudo dmidecode -t 17     # Memory module details
```

**Flag breakdown**:
- `-t <type>` — Filter output by DMI type number

| Type | Information |
|------|-------------|
| 0 | BIOS vendor, version, release date |
| 1 | System manufacturer, product name, serial number |
| 2 | Baseboard manufacturer, product name |
| 4 | Processor family, speed, core count |
| 17 | Memory device size, type, speed |

**Real-world**: Used in data centers to identify hardware models, check BIOS versions before firmware updates, and inventory physical servers. On cloud VMs, it shows the hypervisor details.

### `uname` — Flag Reference

| Flag | Output | Example |
|------|--------|---------|
| `-s` | Kernel name | `Linux` |
| `-n` | Network hostname | `devops-server` |
| `-r` | Kernel release | `6.1.0-18-amd64` |
| `-v` | Kernel version (build info) | `#1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1` |
| `-m` | Machine hardware name | `x86_64` |
| `-p` | Processor type | `x86_64` |
| `-o` | Operating system | `GNU/Linux` |
| `-a` | All of the above combined | Full system string |

---

## 1.5 The Shell

The **shell** is the command-line interface between you and the kernel.

### Check your current shell

```bash
$ echo $SHELL
/bin/bash

$ echo $0
-bash
```

**Explanation**: `$SHELL` shows the default login shell. `$0` shows the currently running shell. `bash` (Bourne Again Shell) is the most common default.

### List available shells

```bash
$ cat /etc/shells
/bin/sh
/bin/bash
/usr/bin/bash
/bin/zsh
/usr/bin/zsh
```

**Explanation**: `/etc/shells` lists all valid login shells installed on the system.

### Shell prompt anatomy

```
username@hostname:current_directory$
```

- `$` — regular user prompt
- `#` — root user prompt

```bash
devops@server:~$          # Regular user, in home directory (~)
root@server:/etc#         # Root user, in /etc directory
```

### Command Line Structure

All Linux commands follow a common format:

```
$ command [options] [arguments]
```

- **Command**: The program to execute (case-sensitive)
- **Options**: Modify behavior, preceded by `-` (short) or `--` (long). Can be combined: `-la` = `-l -a`
- **Arguments**: What the command acts on (files, directories, text)

```bash
$ ls -la /home
#  ^   ^   ^
#  |   |   argument (target directory)
#  |   options (-l = long format, -a = show hidden)
#  command
```

### Tab Completion

Tab completion auto-completes file names, directory names, and commands:

```bash
$ cd /e<Tab>               # Autocompletes to /etc/
$ cd /c<Tab><Tab>          # Lists all directories starting with /c
$ pas<Tab>                 # Autocompletes to passwd
$ systemc<Tab>             # Autocompletes to systemctl
```

- **Tab once** — autocomplete if there is a single match
- **Tab twice** — list all possible matches if multiple exist
- Works with files, directories, commands, and even options (with `bash-completion` installed)

```bash
# Install enhanced tab completion
$ sudo apt install bash-completion    # Debian/Ubuntu
$ sudo yum install bash-completion    # RHEL/CentOS
```

**Real-world**: Tab completion prevents typos and speeds up CLI work. Install `bash-completion` on every server — it adds tab completion for `systemctl`, `docker`, `kubectl`, and hundreds of other commands.

### `clear` — Clear the Terminal Screen

```bash
$ clear
```

**Explanation**: `clear` removes all previous output from the terminal, giving you a clean screen. The command history is not affected — only the visible display is cleared.

**Keyboard shortcut**: Press `Ctrl+L` for the same effect without typing a command.

```bash
# Equivalent alternatives:
$ clear           # Standard command
$ reset           # Resets the terminal completely (fixes garbled display)
$ tput clear      # Uses terminal capabilities
# Or press Ctrl+L # Fastest method
```

**When to use**:
- After running commands with long output (e.g., `cat` on a large file)
- Before a demo or presentation to start with a clean screen
- When the terminal display is garbled (use `reset` instead)

> **Note**: `clear` is equivalent to `cls` in Windows CMD/PowerShell.

---

## 1.6 Getting Help

### The `man` command (manual pages)

```bash
$ man ls
LS(1)                        User Commands                       LS(1)

NAME
       ls - list directory contents

SYNOPSIS
       ls [OPTION]... [FILE]...

DESCRIPTION
       List information about the FILEs (the current directory by default).
       ...
```

**Explanation**: `man <command>` opens the manual page. Navigate with arrow keys, search with `/keyword`, quit with `q`.

### Quick help with `--help`

```bash
$ ls --help
Usage: ls [OPTION]... [FILE]...
List information about the FILEs (the current directory by default).
Sort entries alphabetically if none of -cftuvSUX nor --sort is specified.
  -a, --all                  do not ignore entries starting with .
  -l                         use a long listing format
  -h, --human-readable       with -l, print sizes in human readable format
```

**Explanation**: Most commands support `--help` for a quick summary of options without opening the full manual.

### The `whatis` command

```bash
$ whatis ls
ls (1)               - list directory contents

$ whatis grep
grep (1)             - print lines that match patterns
```

**Explanation**: `whatis` gives a one-line description of a command. The `(1)` means it's in section 1 (user commands) of the manual.

### Manual Page Sections

| Section | Content |
|---------|---------|
| 1 | User commands (`ls`, `grep`, `cat`) |
| 2 | System calls (`fork`, `open`, `read`) |
| 3 | Library functions (`printf`, `malloc`) |
| 5 | File formats (`/etc/passwd`, `/etc/fstab`) |
| 8 | System administration commands (`mount`, `fdisk`) |

```bash
# Access a specific section
$ man 5 passwd          # File format of /etc/passwd (not the command)
$ man 8 mount           # Admin usage of mount
```

### The `apropos` command — Search by keyword

```bash
$ apropos passwd
passwd          (1)  - change user password
gpasswd         (1)  - administer /etc/group
makepasswd      (1)  - generate random passwords

# Equivalent:
$ man -k passwd
```

**Explanation**: `apropos` searches all manual page descriptions for a keyword. Use it when you know what you want to do but not which command does it.

### The `info` command — Detailed documentation

```bash
$ info ls
$ info bash
```

**Explanation**: `info` pages are more detailed and structured than `man` pages, with hyperlinked navigation. Navigate with arrow keys, press `Enter` to follow links, `q` to quit.

### The `which` and `type` commands

```bash
$ which python3
/usr/bin/python3

$ which ls
/usr/bin/ls

$ which java
/usr/bin/java

$ type cd
cd is a shell builtin

$ type ls
ls is aliased to 'ls --color=auto'
```

**Explanation**: `which` finds the full path of an executable by searching your `PATH`. This is useful for confirming which version of a binary is being used, debugging PATH issues, or verifying that a tool is installed. `type` goes further — it tells you whether something is a shell builtin, alias, function, or external command.

### The `whereis` command

```bash
$ whereis ls
ls: /usr/bin/ls /usr/share/man/man1/ls.1.gz

$ whereis python3
python3: /usr/bin/python3 /usr/lib/python3 /usr/share/man/man1/python3.1.gz

$ whereis nginx
nginx: /usr/sbin/nginx /usr/lib/nginx /etc/nginx /usr/share/nginx /usr/share/man/man8/nginx.8.gz
```

**Explanation**: `whereis` locates the binary, source, and manual page files for a command. Unlike `which` (which only searches `PATH`), `whereis` searches standard system directories. Useful for debugging PATH issues or finding where a program's config and docs are located when multiple installations exist.

---

## 1.7 Key Concepts for DevOps

| Concept              | Why It Matters                                              |
|----------------------|-------------------------------------------------------------|
| Everything is a file | Devices, processes, sockets — all represented as files      |
| Case sensitivity     | `File.txt` and `file.txt` are different files               |
| No file extensions   | Linux doesn't rely on extensions to determine file type     |
| Root (`/`)           | The top of the filesystem hierarchy (not to be confused with the root user) |
| Root user            | The superuser with UID 0, has unrestricted access           |
| Permissions          | Every file has owner, group, and other permission bits      |
| Processes            | Every running program is a process with a PID               |

---

## 1.8 `date` — Date and Time

### Display current date and time

```bash
$ date
Wed Feb  5 15:00:00 UTC 2025
```

### Show only the time

```bash
$ date +%T
15:00:00
```

**Explanation**: `%T` is a shorthand for `%H:%M:%S` (24-hour time format). Useful in scripts when you only need the current time without the date.

```bash
# Use in log messages
$ echo "[$(date +%T)] Starting backup..."
[15:00:00] Starting backup...

# Compare with full timestamp
$ echo "Time: $(date +%T) | Full: $(date '+%Y-%m-%d %H:%M:%S')"
Time: 15:00:00 | Full: 2025-02-05 15:00:00
```

**Real-life example**: Monitoring scripts use `date +%T` to log timestamps in cron job output, keeping logs concise when the date is already known from the log file name.

### Custom format

```bash
$ date '+%Y-%m-%d %H:%M:%S'
2025-02-05 15:00:00

$ date '+%d/%m/%Y'
05/02/2025

$ date '+%A, %B %d, %Y'
Wednesday, February 05, 2025
```

**Explanation**: Format codes: `%Y`=year, `%m`=month, `%d`=day, `%H`=hour(24h), `%M`=minute, `%S`=second, `%T`=time(`%H:%M:%S`), `%A`=weekday name, `%B`=month name.

### Date arithmetic

```bash
$ date -d "yesterday"
Tue Feb  4 15:00:00 UTC 2025

$ date -d "3 days ago" '+%Y-%m-%d'
2025-02-02

$ date -d "next friday" '+%Y-%m-%d'
2025-02-07

$ date -d "+2 hours" '+%H:%M:%S'
17:00:00
```

**Explanation**: `-d` lets you compute relative dates. Extremely useful in backup scripts for naming files:

```bash
$ BACKUP_NAME="backup_$(date '+%Y%m%d_%H%M%S').tar.gz"
$ echo $BACKUP_NAME
backup_20250205_150000.tar.gz
```

### Compare two dates (useful in scripts)

```bash
# How many days since a file was modified?

$ stat -c %Y /etc/nginx/nginx.conf     # File's last modified time as epoch seconds
1743984000

$ date +%s                              # Current time as epoch seconds
1745812047

# Subtract and divide by 86400 (seconds in a day: 60 × 60 × 24)
$ FILE_DATE=$(stat -c %Y /etc/nginx/nginx.conf)
$ NOW=$(date +%s)
$ DAYS_AGO=$(( (NOW - FILE_DATE) / 86400 ))
$ echo "Config last modified $DAYS_AGO days ago"
Config last modified 21 days ago
```

| Part | What it does |
|------|-------------|
| `stat -c %Y file` | File's last modified time as Unix timestamp (seconds since 1970-01-01) |
| `date +%s` | Current time as Unix timestamp |
| `$(( ))` | Bash arithmetic (integer math) |
| `/ 86400` | Converts seconds to days |

```bash
# Verify: convert epoch timestamp back to human-readable
$ date -d @1743984000
Sun Apr  6 00:00:00 UTC 2025
```

### Set system date (requires root)

```bash
$ sudo date -s "2025-02-05 15:00:00"
$ sudo timedatectl set-time "2025-02-05 15:00:00"

# Check timezone
$ timedatectl
               Local time: Wed 2025-02-05 15:00:00 UTC
           Universal time: Wed 2025-02-05 15:00:00 UTC
                 Time zone: UTC (UTC, +0000)

# Change timezone
$ sudo timedatectl set-timezone America/New_York
```

### NTP Time Synchronization

```bash
# Check current time sync status
$ timedatectl status
               Local time: Wed 2025-02-05 15:00:00 UTC
           Universal time: Wed 2025-02-05 15:00:00 UTC
                 RTC time: Wed 2025-02-05 15:00:00
                Time zone: UTC (UTC, +0000)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

**Explanation**: `timedatectl status` shows whether the system clock is synchronized and whether the NTP service is active. The key fields are `System clock synchronized: yes` and `NTP service: active`.

```bash
# Enable NTP time synchronization
$ sudo timedatectl set-ntp true

# Verify NTP is now active
$ timedatectl status | grep -E "NTP|synchronized"
System clock synchronized: yes
              NTP service: active
```

**Explanation**: `timedatectl set-ntp true` enables automatic time synchronization via NTP (Network Time Protocol). The system contacts time servers periodically to keep the clock accurate.

**Why it matters**: Correct time is essential for:
- **TLS/SSL certificates** — expired or future-dated certs cause connection failures
- **Log correlation** — timestamps must match across servers to trace distributed requests
- **Authentication** — Kerberos, TOTP (2FA), and JWT tokens are time-sensitive
- **Distributed systems** — databases like Cassandra and CockroachDB rely on synchronized clocks

**Real-life example**: A production server's TLS certificate suddenly stops working. Investigation reveals the server clock drifted 10 minutes ahead, causing certificate validation to fail. Running `sudo timedatectl set-ntp true` fixes the clock and restores service.

### Epoch time (seconds since Jan 1, 1970)

```bash
$ date +%s
1738764000

$ date -d @1738764000
Wed Feb  5 15:00:00 UTC 2025
```

**Explanation**: Epoch timestamps are used in logs, APIs, and databases. Convert between human-readable and epoch with `date`.

---

## 1.9 `time` — Measure Command Execution Duration

### Basic usage

```bash
$ time ls /var/log
auth.log  kern.log  syslog  dpkg.log  nginx/

real    0m0.003s
user    0m0.001s
sys     0m0.002s
```

**Explanation**: `time` measures how long a command takes to execute. The output has three values:
- **real** — total elapsed wall-clock time (what you'd measure with a stopwatch)
- **user** — CPU time spent in user-space (running your code)
- **sys** — CPU time spent in kernel-space (system calls, I/O)

### Measure a slow command

```bash
$ time find / -name "nginx.conf" 2>/dev/null
/etc/nginx/nginx.conf

real    0m2.345s
user    0m0.150s
sys     0m0.890s
```

**Explanation**: The `find` command took 2.3 seconds total. Most time was spent in system calls (`sys`) because `find` reads many directories from disk.

### Measure a script

```bash
$ time bash deploy.sh
Deploying application...
Deployment complete.

real    0m45.230s
user    0m2.100s
sys     0m1.500s
```

**Explanation**: The deployment script took 45 seconds. The large gap between `real` (45s) and `user+sys` (3.6s) means the script spent most time waiting — likely for network operations (downloading packages, pulling Docker images).

### Compare command performance

```bash
$ time grep -r "ERROR" /var/log/ 2>/dev/null
real    0m1.200s
user    0m0.300s
sys     0m0.400s

$ time grep -r "ERROR" /var/log/ --include="*.log" 2>/dev/null
real    0m0.150s
user    0m0.050s
sys     0m0.060s
```

**Explanation**: Adding `--include="*.log"` reduced execution time from 1.2s to 0.15s by skipping non-log files. `time` helps you optimize commands and scripts.

**Industry use case**: DevOps engineers use `time` to benchmark build times, measure deployment durations, compare backup strategies, and identify slow scripts. In CI/CD pipelines, timing each step helps find bottlenecks.

**Real-life example**: Your nightly backup script is taking too long. You run `time ./backup.sh` and discover it takes 3 hours. By timing individual steps inside the script, you find that compressing logs takes 2 hours — switching from `gzip` to `pigz` (parallel gzip) cuts it to 20 minutes.

---

## 1.10 `history` — Command History

```bash
$ history | tail -10
  995  ls -la /var/log
  996  cat /etc/passwd
  997  sudo systemctl status nginx
  998  df -h
  999  top
 1000  history | tail -10
```

**Explanation**: Bash stores your command history (default: 1000 commands) in `~/.bash_history`.

### Search history

```bash
# Search with grep
$ history | grep "docker"
  450  docker ps
  451  docker logs web
  789  docker compose up -d

# Interactive reverse search: press Ctrl+R, then type
(reverse-i-search)`docker': docker compose up -d
```

**Explanation**: `Ctrl+R` is the fastest way to find and re-run previous commands. Press `Ctrl+R` again to cycle through matches. Press `Enter` to execute, `Esc` to edit first.

### Re-run commands

```bash
$ !!                  # Re-run the last command
$ !995                # Re-run command number 995
$ !docker             # Re-run the last command starting with "docker"
$ sudo !!             # Re-run last command with sudo (very common)
```

**Explanation**: `sudo !!` is one of the most useful shortcuts — when you forget to type `sudo`, just run `sudo !!` instead of retyping the whole command.

### History with timestamps

```bash
# Enable timestamps in history
$ export HISTTIMEFORMAT="%F %T  "
$ history | tail -5
  996  2025-02-05 14:50:00  cat /etc/passwd
  997  2025-02-05 14:55:00  sudo systemctl status nginx
  998  2025-02-05 15:00:00  df -h
```

### Increase history size

Bash keeps history in two places:

```
Terminal session (RAM)              ~/.bash_history (disk file)
┌──────────────────┐    on exit     ┌──────────────────┐
│  HISTSIZE=10000  │ ──────────►    │ HISTFILESIZE=20000│
│  commands in     │    on login    │  commands saved   │
│  current memory  │ ◄──────────    │  to disk          │
└──────────────────┘                └──────────────────┘
```

| Variable | Default | What it controls |
|----------|---------|-----------------|
| `HISTSIZE` | 500 | Max commands kept in memory during current session |
| `HISTFILESIZE` | 500 | Max commands saved to `~/.bash_history` on disk |
| `HISTCONTROL` | (empty) | Controls which commands get saved |

```bash
# Add to ~/.bashrc to make persistent
$ echo 'HISTSIZE=10000' >> ~/.bashrc
$ echo 'HISTFILESIZE=20000' >> ~/.bashrc
$ echo 'HISTCONTROL=ignoredups:erasedups' >> ~/.bashrc
$ source ~/.bashrc       # Apply changes to current session
```

**`HISTCONTROL` values:**

| Value | What it does |
|-------|-------------|
| `ignoredups` | Skip saving a command if it's the same as the previous one |
| `erasedups` | Remove all older duplicates when a new command is saved |
| `ignorespace` | Skip commands that start with a space (useful for passwords) |

```bash
# Without HISTCONTROL — duplicates fill up history:
$ ls
$ ls
$ ls
$ history
  1  ls
  2  ls        ← wasted
  3  ls        ← wasted

# With ignoredups:erasedups — only one copy kept:
$ ls
$ ls
$ ls
$ history
  1  ls        ← clean
```

### Clear history

```bash
$ history -c          # Clear history in current session (RAM only)
$ > ~/.bash_history   # Empty the history file on disk
                      # > file is a bash shortcut that truncates a file to 0 bytes
```

**Why clear history?** If you accidentally typed a password in the terminal:

```bash
$ mysql -u root -pMySecret123       # Oops, password is now in history
$ history -c && > ~/.bash_history   # Remove all traces
```

---

## 1.11 `alias` — Command Shortcuts

```bash
# Create an alias
$ alias ll='ls -la'
$ alias gs='git status'
$ alias update='sudo apt update && sudo apt upgrade -y'

# Use it
$ ll
total 48
drwxr-xr-x 6 devops devops 4096 Feb  5 11:30 .
...

# List all aliases
$ alias
alias ll='ls -la'
alias gs='git status'
alias update='sudo apt update && sudo apt upgrade -y'

# Remove an alias
$ unalias ll
```

**Explanation**: Aliases are temporary (current session only). To make them permanent, add them to `~/.bashrc`:

```bash
$ echo "alias ll='ls -la'" >> ~/.bashrc
$ source ~/.bashrc    # Reload to apply
```

### Useful DevOps aliases

Add these to `~/.bashrc` to make them permanent. Run `source ~/.bashrc` after editing.

**Navigation shortcuts:**

```bash
alias ll='ls -la'           # Long listing with hidden files
alias la='ls -A'            # List all except . and ..
alias ..='cd ..'            # Go up one directory
alias ...='cd ../..'        # Go up two directories

$ ll
total 32
drwxr-xr-x  5 devops devops 4096 Apr 26 10:00 .
drwxr-xr-x  3 root   root   4096 Apr 20 08:00 ..
-rw-r--r--  1 devops devops  220 Apr 20 08:00 .bashrc
drwxr-xr-x  2 devops devops 4096 Apr 26 09:00 scripts
-rw-r--r--  1 devops devops 1024 Apr 25 14:00 deploy.sh
```

**Git shortcuts:**

```bash
alias gs='git status'       # Check repo status
alias gp='git pull'         # Pull latest changes

$ gs
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

**Docker shortcuts:**

```bash
alias dc='docker compose'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'

$ dps
NAMES          STATUS          PORTS
nginx          Up 2 hours      0.0.0.0:80->80/tcp
redis          Up 2 hours      6379/tcp
postgres       Up 2 hours      5432/tcp
```

**System monitoring shortcuts:**

```bash
alias ports='sudo ss -tlnp'        # Show all listening TCP ports with process names
alias myip='curl -s ifconfig.me'   # Show your public IP
alias meminfo='free -h'            # Memory usage in human-readable format
alias diskinfo='df -h | grep -v tmpfs'   # Disk usage (skip tmpfs)
alias topcpu='ps aux --sort=-%cpu | head -10'   # Top 10 CPU-consuming processes
alias topmem='ps aux --sort=-%mem | head -10'   # Top 10 memory-consuming processes

$ ports
State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port  Process
LISTEN  0       511     0.0.0.0:80            0.0.0.0:*          users:(("nginx",pid=1234))
LISTEN  0       128     0.0.0.0:22            0.0.0.0:*          users:(("sshd",pid=567))

$ myip
203.0.113.42

$ meminfo
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       2.1Gi       3.2Gi       256Mi       2.5Gi       5.2Gi
Swap:          2.0Gi          0B       2.0Gi

$ topcpu
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
www-data  1234 12.5  3.2 456000 25600 ?        S    09:00   1:30 nginx: worker
postgres  5678  8.3  5.1 320000 40960 ?        S    08:00   2:15 postgres
```

**Safety aliases — ask before overwriting/deleting:**

```bash
alias rm='rm -i'       # Prompt before every removal
alias cp='cp -i'       # Prompt before overwriting
alias mv='mv -i'       # Prompt before overwriting

$ rm important.conf
rm: remove regular file 'important.conf'? n     # Saved!
```

### Check what an alias resolves to

```bash
$ type ll                   # See what an alias expands to
ll is aliased to 'ls -la'

$ type -a python3           # Find all locations of a command
python3 is /usr/bin/python3

# Bypass an alias (run the real command without -i prompt)
$ \rm file.txt              # Backslash bypasses the alias
$ command rm file.txt       # 'command' also bypasses aliases
```

---

## 1.12 `watch` — Repeat a Command Periodically

```bash
$ watch -n 2 df -h
Every 2.0s: df -h                              server: Wed Feb  5 15:00:00 2025

Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
```

**Explanation**: `watch -n 2` runs `df -h` every 2 seconds and refreshes the display. Press `Ctrl+C` to stop.

```bash
# Highlight changes between refreshes
$ watch -d -n 5 'ps aux | head -15'

# Watch a log file grow
$ watch -n 1 'wc -l /var/log/syslog'

# Monitor disk usage during a large copy
$ watch -n 5 'du -sh /backup/'
```

**Explanation**: `-d` highlights differences between updates. Invaluable for monitoring changes in real-time during deployments or troubleshooting.

---

## 1.13 `screen` and `tmux` — Terminal Multiplexers

### `tmux` (recommended)

```bash
# Start a new session
$ tmux new -s deploy

# Detach from session: press Ctrl+B, then D

# List sessions
$ tmux ls
deploy: 1 windows (created Wed Feb  5 15:00:00 2025)

# Reattach to session
$ tmux attach -t deploy

# Kill a session
$ tmux kill-session -t deploy
```

**Explanation**: `tmux` lets you run processes that survive SSH disconnections. Start a long deployment in tmux, detach, close your laptop, reconnect later — the process is still running.

### Key tmux shortcuts (after pressing Ctrl+B)

| Keys       | Action                    |
|------------|---------------------------|
| `d`        | Detach from session       |
| `c`        | Create new window         |
| `n` / `p`  | Next / previous window    |
| `%`        | Split pane vertically     |
| `"`        | Split pane horizontally   |
| Arrow keys | Switch between panes      |
| `x`        | Close current pane        |

### `screen` (older alternative)

```bash
$ screen -S deploy        # Start named session
# Press Ctrl+A, then D to detach
$ screen -ls              # List sessions
$ screen -r deploy        # Reattach
```

---

## 1.14 Troubleshooting: Basic System Issues

### Scenario 1: "What version of Linux am I running?"

```bash
$ cat /etc/os-release | grep -E "^(NAME|VERSION)="
NAME="Ubuntu"
VERSION="22.04.3 LTS (Jammy Jellyfish)"

$ uname -r
6.1.0-18-amd64

$ arch
x86_64
```

### Scenario 2: "The server feels slow, what's happening?"

```bash
# Step 1: Check load average
$ uptime
 15:00:00 up 45 days, load average: 8.50, 7.20, 5.10
# Load average > number of CPUs = overloaded

# Step 2: How many CPUs?
$ nproc
4
# Load 8.50 on 4 CPUs = 2x overloaded

# Step 3: Check memory
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       7.2Gi       100Mi       120Mi       500Mi       200Mi
# available = 200Mi — very low, system is memory-starved

# Step 4: Check disk
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   48G    0G  98% /
# 98% full — critical!
```

### Scenario 3: "I can't find a command I just installed"

```bash
$ mycommand
bash: mycommand: command not found

# Check if it's installed
$ which mycommand
# (no output = not in PATH)

$ dpkg -l | grep mycommand    # Debian/Ubuntu
$ rpm -qa | grep mycommand    # RHEL/CentOS

# Find where it is
$ find / -name "mycommand" -type f 2>/dev/null
/opt/mycommand/bin/mycommand

# Add to PATH
$ export PATH="$PATH:/opt/mycommand/bin"
$ echo 'export PATH="$PATH:/opt/mycommand/bin"' >> ~/.bashrc
```

### Scenario 4: "What's using port 8080?"

```bash
$ sudo ss -tlnp | grep 8080
LISTEN  0  128  0.0.0.0:8080  0.0.0.0:*  users:(("java",pid=3456,fd=18))

# Java process 3456 is using port 8080
$ ps aux | grep 3456
java  3456  1.8  8.5 2500000 680000 ?  Sl  09:00  3:20 java -jar app.jar
```

---

## 1.15 Additional System/Session Commands

### User/session visibility

**`whoami`** — prints the current username:

```bash
$ whoami
vscode
```

**`who`** — shows who is currently logged in, on which terminal, and when:

```bash
$ who
devops   pts/0        2026-04-26 09:15 (192.168.1.10)
admin    pts/1        2026-04-26 10:30 (10.0.0.5)
```

**`w`** — like `who` but also shows what each user is doing and system load:

```bash
$ w
 10:45:08 up 2 days,  3 users,  load average: 0.55, 0.72, 0.54
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU  WHAT
devops   pts/0    192.168.1.10     09:15    0.00s  0.05s  0.01s  w
admin    pts/1    10.0.0.5         10:30    15:00  0.02s  0.02s  vim config.yaml
```

**`groups`** — shows which groups the current user belongs to:

```bash
$ groups
devops sudo docker

$ groups admin          # Check another user's groups
admin : admin wheel
```

**`last`** — shows recent login history (reads from `/var/log/wtmp`):

```bash
$ last -5
devops   pts/0    192.168.1.10     Sun Apr 26 09:15   still logged in
admin    pts/1    10.0.0.5         Sat Apr 25 14:00 - 18:30  (04:30)
root     tty1                      Fri Apr 24 08:00 - 08:05  (00:05)
reboot   system boot  5.15.0-91    Fri Apr 24 07:59   still running

wtmp begins Fri Apr 24 07:59:00 2026
```

**`lastlog`** — shows the most recent login for every user account:

```bash
$ lastlog
Username         Port     From                       Latest
root                                                 **Never logged in**
devops           pts/0    192.168.1.10               Sun Apr 26 09:15:00 +0000 2026
nginx                                                **Never logged in**
```

> **DevOps use**: `who` and `w` to check active sessions on a server. `last` to audit login history. `lastlog` to find unused accounts.

---

### Host/time utilities

**`hostname`** — shows or sets the system hostname:

```bash
$ hostname
web-server-01
```

**`hostnamectl`** — shows detailed host info and sets hostname persistently:

```bash
$ hostnamectl
 Static hostname: web-server-01
       Icon name: computer-vm
         Chassis: vm
      Machine ID: a1b2c3d4e5f6...
         Boot ID: f6e5d4c3b2a1...
  Operating System: Ubuntu 24.04 LTS
            Kernel: Linux 5.15.0-91-generic
      Architecture: x86-64

$ sudo hostnamectl set-hostname prod-api-01    # Change hostname (persists after reboot)
```

**`cal`** — displays a calendar:

```bash
$ cal
     April 2026
Su Mo Tu We Th Fr Sa
          1  2  3  4
 5  6  7  8  9 10 11
12 13 14 15 16 17 18
19 20 21 22 23 24 25
26 27 28 29 30

$ cal 12 2026          # Show December 2026
$ cal -3               # Show previous, current, and next month
```

**`date`** — shows or sets the system date and time:

```bash
$ date
Sun Apr 26 04:47:27 UTC 2026

$ date +%Y-%m-%d           # Custom format
2026-04-26

$ date +%A                 # Day of week
Sunday

$ date +"%Y-%m-%d %H:%M:%S"   # Full timestamp (useful in scripts)
2026-04-26 04:47:27

$ date -d "2 days ago"     # Relative date
Thu Apr 24 04:47:27 UTC 2026

$ date -d "next friday"    # Future date
Fri May  1 00:00:00 UTC 2026
```

Common format codes:

| Code | Meaning | Example |
|------|---------|---------|
| `%Y` | Year (4 digit) | 2026 |
| `%m` | Month (01-12) | 04 |
| `%d` | Day (01-31) | 26 |
| `%H` | Hour (00-23) | 04 |
| `%M` | Minute (00-59) | 47 |
| `%S` | Second (00-59) | 27 |
| `%A` | Day name | Sunday |
| `%B` | Month name | April |
| `%Z` | Timezone | UTC |

**`timedatectl`** — shows time, timezone, and NTP sync status:

```bash
$ timedatectl
               Local time: Sun 2026-04-26 04:47:27 UTC
           Universal time: Sun 2026-04-26 04:47:27 UTC
                 RTC time: Sun 2026-04-26 04:47:27
                Time zone: UTC (UTC, +0000)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no

$ timedatectl set-timezone Asia/Kolkata       # Change timezone
$ timedatectl list-timezones | grep Asia      # List available timezones
$ timedatectl set-ntp true                    # Enable NTP sync
```

> **DevOps use**: `date` for timestamps in scripts and log filenames. `timedatectl` to verify NTP sync (clock drift breaks TLS, Kerberos, and log correlation).

---

### Messaging and terminal tools

**`wall`** — broadcasts a message to all logged-in users:

```bash
$ wall "Server rebooting in 5 minutes"
# All users see:
# Broadcast message from devops@web-server-01 (pts/0) (Sun Apr 26 10:55:00 2026):
# Server rebooting in 5 minutes
```

**`write`** — sends a message to a specific logged-in user:

```bash
$ write admin pts/1
Hey, I'm restarting nginx in 2 minutes
^D                                        # Ctrl+D to end message
```

**`mesg`** — controls whether other users can send you messages:

```bash
$ mesg            # Check current status
is y              # "y" = messages allowed, "n" = blocked

$ mesg n          # Block incoming messages
$ mesg y          # Allow messages again
```

**`script`** — records everything in your terminal session to a file:

```bash
$ script session.log          # Start recording
Script started, file is session.log

$ whoami                      # Commands and output are captured
devops
$ ls /etc
...

$ exit                        # Stop recording
Script done, file is session.log

$ cat session.log             # Replay the session
```

> **DevOps use**: `wall` before maintenance windows. `script` to record troubleshooting sessions for documentation or audits.


---

## 1.16 Interview Questions — Module 1

**Q1: What is Linux? How is it different from Unix?**

Linux is a free, open-source Unix-like kernel created by Linus Torvalds in 1991. Combined with GNU tools, it forms a complete OS (GNU/Linux). Unix is proprietary (AIX, HP-UX, Solaris) and typically tied to specific hardware. Linux runs on commodity hardware, is community-driven, and is free under the GPL.

**Q2: Explain the Linux boot process.**

1. **BIOS/UEFI** — POST, locates boot device
2. **GRUB** — Loads kernel (`vmlinuz`) and initial RAM disk (`initrd`)
3. **Kernel** — Initializes hardware, mounts root filesystem, starts PID 1
4. **systemd** — Starts services based on target dependencies
5. **Services** — nginx, sshd, docker start
6. **Login** — TTY or GUI prompt

Verify with: `systemd-analyze blame`

**Q3: What is the difference between a monolithic kernel and a microkernel?**

A monolithic kernel (Linux) runs all OS services (drivers, memory management, scheduling) in kernel space as one binary. A microkernel (MINIX, QNX) runs only essential services in kernel space and moves drivers/filesystems to user space. Linux compensates with loadable kernel modules (`lsmod`, `modprobe`) for flexibility.

**Q4: What does "Everything is a File" mean?**

In Linux, hardware devices (`/dev/sda`), processes (`/proc/<PID>`), kernel parameters (`/sys`), and even network sockets are represented as files. This allows uniform access using standard file operations (`read`, `write`, `cat`).

**Q5: How do you check system information on a Linux server?**

```bash
uname -a                    # Kernel and architecture
cat /etc/os-release         # Distribution
hostnamectl                 # Hostname, OS, virtualization
nproc                       # CPU count
free -h                     # Memory
df -h                       # Disk space
uptime                      # Uptime and load average
lscpu                       # Detailed CPU info
sudo dmidecode -t 1         # Hardware manufacturer/model
```

**Q6: What is the difference between `uname -r` and `uname -a`?**

`uname -r` prints only the kernel release version (e.g., `6.1.0-18-amd64`). `uname -a` prints all system information: kernel name, hostname, kernel release, kernel version, machine architecture, and OS name.

**Q7: What is the purpose of `/proc` and `/sys`?**

`/proc` is a virtual filesystem exposing kernel and process information as files (`/proc/cpuinfo`, `/proc/meminfo`, `/proc/<PID>/status`). `/sys` exposes kernel objects, device attributes, and driver parameters. Neither consumes disk space — they are generated dynamically by the kernel.

**Q8: What is the difference between systemd and SysVinit?**

systemd starts services in parallel with dependency management, uses unit files, supports socket activation, and provides `journalctl` for logging. SysVinit starts services sequentially using shell scripts in `/etc/init.d/`, is simpler but slower. systemd is the default on all modern distributions (RHEL 7+, Ubuntu 15+).

---

## Summary

After this module, you should understand:
- What Linux is and why it dominates server/cloud infrastructure
- History, GNU/POSIX, GPL licensing, and the Linux philosophy
- Key differences between Windows and Linux
- The layered architecture (hardware → kernel → shell → applications)
- Kernel types, boot process, system calls, kernel modules, and scheduling
- Virtual memory, VFS, and device management (udev)
- Major distribution families and which to use for DevOps
- How to check system information (`uname`, `lscpu`, `dmidecode`, `/etc/os-release`)
- How to use the shell, tab completion, and navigate the prompt
- How to get help (`man`, `--help`, `whatis`, `apropos`, `info`, `which`)
- Date formatting, command history, aliases, `watch`, and `tmux`
- Basic troubleshooting: slow server, missing commands, port conflicts

**Next Module**: [02 - Filesystem & Navigation](../02-filesystem-and-navigation/README.md)
