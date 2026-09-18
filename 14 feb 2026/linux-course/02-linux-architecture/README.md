# Module 2: Linux Architecture

## 1.2 Linux Architecture

```
┌─────────────────────────────────────┐
│         User Applications           │
│    (nginx, docker, your scripts)    │
├─────────────────────────────────────┤
│              Shell                  │
│         (bash, zsh, sh)            │
├─────────────────────────────────────┤
│         System Libraries            │
│            (glibc)                  │
├─────────────────────────────────────┤
│             Kernel                  │
│  (processes, memory, drivers, I/O)  │
├─────────────────────────────────────┤
│            Hardware                 │
│      (CPU, RAM, Disk, NIC)          │
└─────────────────────────────────────┘
```

**What each layer does:**

- **Hardware** — physical components
- **Kernel** — manages hardware, runs as PID 0. Applications never touch hardware directly — they ask the kernel via system calls
- **System Libraries** — `glibc` wraps system calls into functions like `open()`, `read()`, `write()`
- **Shell** — interprets your commands and calls the right programs
- **Applications** — everything you run (web servers, containers, scripts)

### Simple example: what happens when you run `cat /etc/hostname`

```
You type: cat /etc/hostname
  → Shell finds /usr/bin/cat, forks a child process
    → cat calls open("/etc/hostname") via glibc
      → glibc makes a system call to the kernel
        → Kernel checks permissions, reads from disk
      → Data flows back up: kernel → glibc → cat → terminal
    → You see the output
```

```bash
# Watch system calls in real time with strace
strace cat /etc/hostname 2>&1 | grep -E 'open|read|write'
# openat(AT_FDCWD, "/etc/hostname", O_RDONLY) = 3
# read(3, "my-server\n", 131072)              = 10
# write(1, "my-server\n", 10)                 = 10
```

### Kernel types

| Type | What's in kernel space | Example |
|------|----------------------|---------|
| **Monolithic** | Everything (drivers, filesystem, networking) | Linux |
| **Microkernel** | Only IPC, scheduler, memory — rest in user space | MINIX, QNX |
| **Hybrid** | Mix of both | Windows NT, macOS |

Linux is monolithic (fast — no message passing) but supports **loadable kernel modules** so you can add/remove drivers at runtime without rebooting.

**`lsmod`** — list currently loaded kernel modules:

```bash
$ lsmod
Module                  Size  Used by
vfat                   20480  1
fat                    86016  1 vfat
ext4                  831488  2
mbcache                16384  1 ext4
ip_tables              36864  0
```

Each row is a module loaded in kernel memory. `Used by` shows dependencies — `vfat` depends on `fat`, so you can't unload `fat` while `vfat` is loaded.

**`modprobe`** — load or unload a kernel module:

```bash
$ sudo modprobe vfat            # Load FAT32 filesystem support (also loads dependencies)
$ sudo modprobe -r vfat         # Unload it (fails if in use)
```

**`modinfo`** — show details about a module:

```bash
$ modinfo ext4
filename:       /lib/modules/5.15.0-91-generic/kernel/fs/ext4/ext4.ko
description:    Fourth Extended Filesystem
author:         Remy Card, Stephen Tweedie, Andrew Morton, and others
license:        GPL
depends:        mbcache,jbd2
```

| Command | What it does |
|---------|-------------|
| `lsmod` | List all loaded modules |
| `modprobe <module>` | Load a module + its dependencies |
| `modprobe -r <module>` | Unload a module |
| `modinfo <module>` | Show module details (file, author, dependencies) |
| `lsmod \| grep <name>` | Check if a specific module is loaded |

### Init system (systemd)

PID 1 is the first process the kernel starts. It launches everything else. On modern distros, PID 1 is **systemd**.

```bash
# Check what's running as PID 1
ps -p 1 -o comm=
# → systemd
```

**Essential `systemctl` commands:**

```bash
systemctl start nginx          # Start a service
systemctl stop nginx           # Stop it
systemctl restart nginx        # Restart
systemctl enable --now nginx   # Enable at boot + start now
systemctl status nginx         # Status, PID, recent logs
systemctl list-units --type=service --state=running   # All running services

# Logs
journalctl -u nginx            # All logs for nginx
journalctl -u nginx -f         # Follow in real-time
journalctl -u nginx --since "1 hour ago"
```

**Example unit file** (`/etc/systemd/system/myapp.service`):

```ini
[Unit]
Description=My App
After=network.target

[Service]
ExecStart=/usr/bin/myapp
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Boot process

```
Power on → BIOS/UEFI → GRUB (bootloader) → Kernel → systemd (PID 1) → Services → Login
```

```bash
systemd-analyze                # Total boot time
systemd-analyze blame          # Which service took longest
```

### System calls

System calls are how programs ask the kernel to do things (read files, create processes, send network packets).

| Category | Key calls | Example use |
|----------|-----------|-------------|
| File I/O | `open`, `read`, `write`, `close` | `cat file.txt` |
| Process | `fork`, `exec`, `wait`, `exit` | Shell running a command |
| Network | `socket`, `bind`, `connect` | `curl` making a request |

```bash
# Trace system calls of any command
strace ls /tmp
strace -e openat,read,write ls /tmp    # Filter specific calls
strace -p <PID>                         # Attach to running process
```

### Devices

Linux exposes hardware as files under `/dev/`:

```bash
/dev/sda       # First disk
/dev/null      # Discards all input (black hole)
/dev/random    # Random number generator
/dev/tty       # Current terminal
```

---

