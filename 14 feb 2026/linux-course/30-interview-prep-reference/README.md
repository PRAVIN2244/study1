# Module 15: Linux Command Cheat Sheet (Quick Revision)

This module is a fast-reference sheet with command and meaning only.

## 15.1 Navigation and Files

- `pwd` - Print current working directory.
- `ls` - List files and directories.
- `ls -la` - List all files including hidden with details.
- `ls -lh` - List sizes in human-readable format.
- `cd /path` - Change directory.
- `cd ~` - Go to home directory.
- `cd -` - Go to previous directory.
- `mkdir dir` - Create a directory.
- `mkdir -p a/b/c` - Create nested directories.
- `rmdir dir` - Remove empty directory.
- `touch file` - Create empty file or update timestamp.
- `stat file` - Show detailed file metadata.
- `file name` - Detect file type.
- `realpath file` - Show absolute path.
- `readlink link` - Show target of symbolic link.

## 15.2 File Operations

- `cp src dst` - Copy file.
- `cp -r src_dir dst_dir` - Copy directory recursively.
- `mv src dst` - Move or rename file/directory.
- `rm file` - Remove file.
- `rm -r dir` - Remove directory recursively.
- `rm -rf dir` - Force remove recursively.
- `cat file` - Print file content.
- `less file` - View file with scroll/search.
- `more file` - View file page by page.
- `head file` - Show first 10 lines.
- `head -n 20 file` - Show first 20 lines.
- `tail file` - Show last 10 lines.
- `tail -n 20 file` - Show last 20 lines.
- `tail -f log` - Follow log in real time.
- `ln src hardlink` - Create hard link.
- `ln -s src symlink` - Create symbolic link.

## 15.3 Permissions and Ownership

- `chmod 755 file` - Set rwx for owner, rx for group/others.
- `chmod 644 file` - Set rw for owner, r for group/others.
- `chmod +x script.sh` - Add execute permission.
- `chown user file` - Change file owner.
- `chown user:group file` - Change owner and group.
- `chown -R user:group dir` - Change recursively.
- `chgrp group file` - Change group ownership.
- `umask` - Show default permission mask.
- `umask 022` - Set permission mask.
- `ls -ld /tmp` - Check sticky bit on shared temp directory.
- `chmod +t dir` - Set sticky bit.

## 15.4 Users and Groups

- `id` - Show current user and groups.
- `id username` - Show user identity details.
- `whoami` - Print current username.
- `who` - Show logged-in users.
- `w` - Show logged-in users and activity.
- `groups` - Show group membership.
- `useradd username` - Create a user.
- `userdel username` - Delete a user.
- `passwd username` - Set or reset user password.
- `groupadd groupname` - Create group.
- `groupdel groupname` - Delete group.
- `usermod -aG group user` - Add user to supplementary group.
- `su user` - Switch to another user.
- `su -` - Switch to root login shell.
- `sudo command` - Run one command as privileged user.
- `sudo -i` - Open root login shell via sudo.

## 15.5 SSH and Remote Access

- `ssh user@host` - Connect to remote host over SSH.
- `ssh -l user host` - Connect with explicit login user option.
- `ssh -p 2222 user@host` - Connect on custom port.
- `ssh -i key.pem user@host` - Connect using private key.
- `ssh-keygen -t rsa -b 4096` - Generate RSA SSH key pair.
- `ssh-copy-id user@host` - Copy public key for passwordless login.
- `scp file user@host:/path` - Copy local file to remote host.
- `scp user@host:/path/file .` - Copy remote file to local host.
- `rsync -av dir/ user@host:/path/` - Efficient directory sync.

## 15.6 Process and Job Control

- `ps` - List processes for current shell context.
- `ps -ef` - Full process list.
- `ps aux` - BSD-style full process list with resource columns.
- `top` - Live process and CPU/memory view.
- `htop` - Interactive process viewer.
- `kill PID` - Send default TERM signal.
- `kill -9 PID` - Force kill with SIGKILL.
- `killall name` - Kill processes by name.
- `pkill pattern` - Kill processes matching pattern.
- `jobs` - List jobs in current shell.
- `bg` - Resume job in background.
- `fg` - Bring job to foreground.
- `command &` - Run command in background.
- `nohup command &` - Run command immune to hangup/logout.
- `disown` - Remove job from shell job table.
- `wait` - Wait for background job completion.
- `nice -n 10 command` - Start process with lower priority.
- `renice 10 PID` - Change running process priority.

## 15.7 Text Processing and Search

- `grep pattern file` - Search pattern in file.
- `grep -n pattern file` - Show line numbers for matches.
- `grep -r pattern dir` - Recursive search in directory.
- `grep -i pattern file` - Case-insensitive search.
- `grep -v pattern file` - Invert match.
- `sort file` - Sort lines alphabetically.
- `sort -n file` - Numeric sort.
- `sort -u file` - Sort and deduplicate.
- `uniq file` - Remove adjacent duplicate lines.
- `uniq -c file` - Count adjacent duplicates.
- `cut -d: -f1 /etc/passwd` - Extract first field by delimiter.
- `tr a-z A-Z` - Translate lowercase to uppercase.
- `tr -d '\n'` - Delete newline characters.
- `tr -s ' '` - Squeeze repeated spaces.
- `wc file` - Count lines, words, bytes.
- `wc -l file` - Count lines.
- `sed 's/a/b/' file` - Replace first match per line.
- `sed 's/a/b/g' file` - Replace all matches per line.
- `sed -n '1,10p' file` - Print line range.
- `awk '{print $1}' file` - Print first column.
- `awk -F: '{print $1}' /etc/passwd` - Use custom delimiter.
- `awk 'END {print NR}' file` - Print total line count.
- `xargs command` - Build command arguments from stdin.
- `tee file` - Write stdin to screen and file.
- `tee -a file` - Append stdin to file and screen.

## 15.8 Redirection and Pipes

- `cmd > file` - Redirect stdout (overwrite).
- `cmd >> file` - Redirect stdout (append).
- `cmd 2> file` - Redirect stderr.
- `cmd > file 2>&1` - Redirect stdout and stderr to same file.
- `cmd > /dev/null` - Discard stdout.
- `cmd > /dev/null 2>&1` - Discard stdout and stderr.
- `echo message 1>&2` - Write to stderr.
- `cmd1 | cmd2` - Pipe stdout of first command into second.
- `echo $?` - Show exit code of previous command.

## 15.9 System Information and Monitoring

- `uname -a` - Show kernel and system information.
- `uname -r` - Show kernel release.
- `cat /etc/os-release` - Show OS distribution details.
- `hostname` - Show host name.
- `hostnamectl` - Show or set host information.
- `uptime` - Show uptime and load average.
- `date` - Show current date and time.
- `date +%T` - Show current time only.
- `timedatectl` - Show/set time and timezone config.
- `free -h` - Show memory and swap usage.
- `vmstat` - Show process, memory, swap, I/O stats.
- `iostat` - Show CPU and disk I/O stats.
- `sar -u` - Show historical CPU stats.
- `sar -r` - Show historical memory stats.
- `lscpu` - Show CPU architecture details.
- `df -h` - Show filesystem free space.
- `df -i` - Show inode usage.
- `du -sh dir` - Show total directory size.
- `du -h -d 1` - Show one-level directory usage.
- `lsblk` - List block devices.
- `mount` - Show mounted filesystems.
- `umount /dev/sdX` - Unmount filesystem.

## 15.10 Networking Commands

- `ip addr` - Show IP addresses and interfaces.
- `ip route` - Show routing table.
- `ping host` - Test ICMP connectivity.
- `traceroute host` - Show network hop path.
- `nslookup host` - Query DNS records.
- `dig host` - Detailed DNS query.
- `ss -tulnp` - Show listening TCP/UDP sockets with process.
- `netstat -tulnp` - Legacy socket/port listing.
- `curl URL` - Transfer data from URL.
- `wget URL` - Download file from URL.
- `ifconfig` - Legacy network interface view.

## 15.11 Package and Service Management

- `apt-get update -y` - Refresh package index.
- `apt install pkg` - Install package on Debian/Ubuntu.
- `dnf install pkg` - Install package on RHEL family.
- `yum install pkg` - Legacy RHEL/CentOS install command.
- `dpkg -l` - List installed Debian packages.
- `rpm -qa` - List installed RPM packages.
- `systemctl status service` - Show service status.
- `systemctl start service` - Start service.
- `systemctl stop service` - Stop service.
- `systemctl restart service` - Restart service.
- `systemctl enable service` - Enable auto-start at boot.
- `systemctl disable service` - Disable auto-start.
- `service sshd restart` - Legacy service restart command.
- `journalctl` - View systemd journal logs.
- `journalctl -u ssh` - Show logs for one service.
- `dmesg` - Show kernel ring buffer messages.

## 15.12 Archives, Scheduling, and Shell

- `tar -cvf archive.tar dir` - Create tar archive.
- `tar -xvf archive.tar` - Extract tar archive.
- `tar -czvf archive.tar.gz dir` - Create gzip-compressed tar archive.
- `tar -xzvf archive.tar.gz` - Extract gzip tar archive.
- `zip archive.zip file` - Create zip archive.
- `unzip archive.zip` - Extract zip archive.
- `crontab -l` - List current user cron jobs.
- `crontab -e` - Edit current user cron jobs.
- `crontab -r` - Remove current user cron jobs.
- `source file.sh` - Execute script in current shell.
- `bash script.sh` - Run script with bash interpreter.
- `sh script.sh` - Run script with sh interpreter.
- `chmod +x script.sh` - Make script executable.
- `./script.sh` - Run executable script from current directory.
- `history` - Show shell command history.
- `history | grep ssh` - Filter history for SSH commands.
- `alias ll='ls -la'` - Create command alias.
- `unalias ll` - Remove alias.
- `export VAR=value` - Set environment variable.
- `printenv` - Show environment variables.
- `env` - Show environment for current process.
- `unset VAR` - Remove environment variable.


---

1-a, 2-b, 3-a

---

# Linux Interview Questions & Answers

## Section 1: Linux Basics

**Q1: What is Linux and how is it different from Unix?**

Linux is a free, open-source Unix-like OS kernel created by Linus Torvalds in 1991. Key differences:
- **Source code**: Linux is open source; Unix is mostly proprietary (AIX, HP-UX, Solaris)
- **Cost**: Linux is free; Unix often requires commercial licenses
- **Hardware**: Linux supports wide hardware range; Unix is typically hardware-specific
- **Community**: Linux is community-driven; Unix is enterprise-focused

**Q2: Explain the Linux boot process step-by-step.**

1. **BIOS/UEFI** — POST, locates boot device
2. **MBR/GPT** — Bootloader location on disk
3. **GRUB** — Loads kernel into memory, shows boot menu
4. **Kernel** — Initializes hardware, mounts root filesystem, starts PID 1
5. **systemd/init** — Starts services based on targets/runlevels
6. **Login** — TTY or GUI login prompt

```bash
# Check boot time
systemd-analyze
systemd-analyze blame
```

**Q3: What are runlevels and how do they map to systemd targets?**

| Runlevel | systemd Target | Description |
|----------|---------------|-------------|
| 0 | poweroff.target | Halt |
| 1 | rescue.target | Single-user |
| 3 | multi-user.target | CLI multi-user |
| 5 | graphical.target | GUI |
| 6 | reboot.target | Reboot |

```bash
systemctl get-default
sudo systemctl set-default multi-user.target
```

**Q4: What are the major components of the Linux OS?**

1. **Kernel** — Manages hardware, memory, processes, I/O
2. **System Libraries** — glibc, libssl — interfaces for apps to talk to kernel
3. **System Utilities** — ls, cp, grep, awk — user-level tools
4. **User Interface** — CLI (bash, zsh) or GUI (GNOME, KDE)

**Q5: What is the difference between a process and a thread?**

| Feature | Process | Thread |
|---------|---------|--------|
| Memory | Own address space | Shared with parent |
| Creation | `fork()` | `clone()` / `pthread_create()` |
| Overhead | Higher | Lower |
| Isolation | Full | Partial |

```bash
ps -eLf | grep nginx    # View threads
ps aux                   # View processes
```

## Section 2: Filesystem

**Q6: What is an inode?**

An inode stores file metadata (permissions, size, timestamps, data block pointers) but NOT the filename. Filenames map to inodes via directory entries.

```bash
ls -li                   # Show inode numbers
df -i                    # Check inode usage
stat file.txt            # Detailed inode info
```

Running out of inodes (even with free disk space) prevents creating new files.

**Q7: What are hard links and soft links?**

| Feature | Hard Link | Soft Link (Symlink) |
|---------|-----------|-------------------|
| Points to | Same inode | Filename/path |
| Cross filesystem | No | Yes |
| Link to directory | No | Yes |
| Original deleted | Data survives | Broken (dangling) |

```bash
ln original.txt hardlink.txt       # Hard link
ln -s /path/to/original symlink    # Soft link
ls -li                              # Compare inodes
```

**Q8: What is the difference between find and locate?**

- `find` searches the filesystem in real time — accurate but slower
- `locate` uses a prebuilt database (`updatedb`) — fast but may be stale

```bash
find /etc -name "nginx.conf"           # Real-time search
find /var -type f -size +100M          # Find large files
find /tmp -name "*.tmp" -mtime +7 -delete  # Delete old temp files

locate nginx.conf                       # Fast database search
sudo updatedb                           # Update locate database
```

## Section 3: Permissions & Security

**Q9: Explain SUID, SGID, and Sticky Bit.**

| Bit | On Files | On Directories | Example |
|-----|----------|---------------|---------|
| SUID | Runs with owner's privileges | — | `/usr/bin/passwd` |
| SGID | Runs with group's privileges | New files inherit directory's group | Shared project dirs |
| Sticky | — | Only owner can delete their files | `/tmp` |

```bash
chmod u+s /usr/bin/myapp    # Set SUID
chmod g+s /shared           # Set SGID
chmod +t /shared/tmp        # Set Sticky Bit

# Find SUID binaries (security audit)
find / -perm -4000 -type f 2>/dev/null
```

**Q10: What are cgroups and how do they help?**

cgroups (control groups) limit, account for, and isolate resource usage (CPU, memory, I/O) of process groups.

```bash
cat /proc/self/cgroup                    # Current cgroup
systemd-cgls                             # View hierarchy
systemd-run --scope -p MemoryMax=100M ./app  # Run with memory limit
```

Used by Docker and Kubernetes to enforce container resource limits. OOMKilled errors in containers are cgroup-enforced.

## Section 4: Networking

**Q11: How does Linux firewall (iptables/firewalld) work?**

iptables uses chains (INPUT, OUTPUT, FORWARD) to filter packets by rules.

```bash
# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Block an IP
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# Default deny
sudo iptables -P INPUT DROP

# Save rules
sudo iptables-save > /etc/iptables.rules

# firewalld (zone-based, RHEL/Fedora)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

**Q12: What is the difference between TCP and UDP?**

TCP is connection-oriented, reliable, ordered — used for SSH, HTTP, databases.
UDP is connectionless, fast, lightweight — used for DNS, streaming, gaming.

## Section 5: Process Management

**Q13: How do you trace zombie and orphan processes?**

```bash
# Find zombies
ps aux | grep 'Z'

# Find parent of zombie
ps -eo pid,ppid,stat,cmd | grep Z

# Orphan processes (PPID = 1, adopted by init)
ps -eo pid,ppid,cmd | awk '$2 == 1'
```

Fix: Restart the parent process or use `wait()` in scripts to collect child exit statuses.

**Q14: What is strace and how do you debug with it?**

```bash
strace ls /tmp                          # Trace a command
strace -p <PID>                         # Attach to running process
strace -e openat,read ./app             # Trace specific syscalls
strace ./app 2>&1 | grep ENOENT         # Find missing files
strace -c ./app                         # Summarize syscall counts
```

## Section 6: Systemd & Services

**Q15: How to create a custom systemd service?**

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
ExecStart=/usr/local/bin/myapp
Restart=on-failure
User=appuser

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myapp
systemctl status myapp
journalctl -u myapp -f
```

**Q16: How to troubleshoot boot failures?**

1. Check GRUB — if `grub rescue>` appears, reinstall: `grub-install /dev/sda && update-grub`
2. Enter rescue mode: `systemctl isolate rescue.target`
3. Check logs: `journalctl -xb`
4. Check failed services: `systemctl --failed`
5. Check `/etc/fstab` for bad entries
6. Run `fsck` on corrupted filesystems

## Section 7: Disk & Storage

**Q17: Explain LVM in detail.**

LVM hierarchy: Physical Volume (PV) → Volume Group (VG) → Logical Volume (LV)

```bash
# Create
pvcreate /dev/sdb1 /dev/sdc1
vgcreate myvg /dev/sdb1 /dev/sdc1
lvcreate -L 10G -n mydata myvg
mkfs.ext4 /dev/myvg/mydata
mount /dev/myvg/mydata /data

# Extend
lvextend -L +5G /dev/myvg/mydata
resize2fs /dev/myvg/mydata

# Snapshot
lvcreate -s -L 1G -n snap /dev/myvg/mydata
```

**Q18: What is the difference between ext4, xfs, and btrfs?**

| Feature | ext4 | xfs | btrfs |
|---------|------|-----|-------|
| Default in | Ubuntu/Debian | RHEL/CentOS | openSUSE |
| Shrink support | Yes | No | Yes |
| Snapshots | No | No | Yes |
| Performance | Good general | Great for large files | Good with compression |

## Section 8: Shell Scripting

**Q19: What is the significance of `#!/bin/bash`?**

The shebang (`#!`) tells the kernel which interpreter to use. Without it, the script runs in the current shell, which may not be bash.

```bash
#!/bin/bash          # Use bash
#!/bin/sh            # POSIX-compliant shell
#!/usr/bin/env bash  # Portable (finds bash in PATH)
#!/usr/bin/python3   # Python script
```

**Q20: How do you handle errors in shell scripts?**

```bash
#!/bin/bash
set -euo pipefail    # Exit on error, undefined vars, pipe failures

trap 'echo "Error at line $LINENO"' ERR
trap 'cleanup' EXIT

cleanup() {
    rm -f /tmp/tempfile
    echo "Cleaned up"
}
```

## Section 9: Cloud & Containers

**Q21: How do containers differ from VMs?**

| Feature | Container | VM |
|---------|-----------|-----|
| Isolation | Kernel-level (namespaces, cgroups) | Hardware-level (hypervisor) |
| Boot time | Milliseconds | Minutes |
| Size | MBs | GBs |
| Kernel | Shared with host | Own kernel |
| Use case | Microservices, CI/CD | Legacy apps, multi-OS |

**Q22: What is cloud-init?**

cloud-init initializes cloud VMs on first boot — sets hostname, users, SSH keys, installs packages, runs commands.

```yaml
#cloud-config
hostname: webserver
packages: [nginx, git]
runcmd:
  - systemctl start nginx
```

## Section 10: Troubleshooting

**Q23: How to troubleshoot high CPU usage?**

```bash
top                              # Find top CPU process (press P to sort)
ps aux --sort=-%cpu | head       # Top CPU consumers
strace -p <PID>                  # What syscalls is it making?
pidstat -p <PID> 1               # Per-process CPU over time
```

**Q24: How to troubleshoot "No space left on device"?**

```bash
df -h                            # Check filesystem usage
du -sh /* 2>/dev/null | sort -h  # Find largest directories
lsof +L1                         # Deleted files still held open
df -i                            # Check inode exhaustion
```

**Q25: How to perform root cause analysis?**

1. **Timeline** — When did it start? Correlate logs, metrics, alerts
2. **Symptoms** — Downtime, slowness, data loss?
3. **Scope** — One host, one service, or system-wide?
4. **Immediate cause** — Process crash, config error, resource exhaustion?
5. **Root cause** — Why did the safeguard fail?
6. **Fix** — Add validation, monitoring, or automation to prevent recurrence

---

# Top 100 Linux Debug Commands — Quick Reference

## System Information
```bash
uname -a                    # Kernel version, architecture
hostnamectl                 # Hostname, OS, kernel
cat /etc/os-release         # Distro info
uptime                      # Uptime + load averages
whoami                      # Current user
id                          # UID, GID, groups
dmesg -T | grep error       # Kernel errors with timestamps
hostname -I                 # System IPs
```

## CPU, Memory & Process
```bash
top                         # Live process monitor
htop                        # Enhanced process monitor
vmstat 1                    # CPU/memory/swap every 1 sec
free -h                     # Memory and swap usage
ps aux --sort=-%cpu | head  # Top CPU consumers
ps aux --sort=-%mem | head  # Top memory consumers
pidstat -p <PID> 1          # Per-process stats
pstree -pa                  # Process hierarchy
kill -9 <PID>               # Force kill
ulimit -a                   # Resource limits
journalctl -k | grep oom    # OOM kill events
lsof -p <PID>               # Open files by process
```

## Disk & Filesystem
```bash
df -hT                      # Filesystem usage with types
du -sh /var/* | sort -h     # Directory sizes
lsblk -f                    # Block devices with FS info
blkid                       # UUIDs and labels
mount | column -t           # Mounted filesystems
iostat -xz 1                # Disk I/O performance
iotop -oPa                  # Per-process disk usage
smartctl -a /dev/sda        # Disk health
lsof +D /var/log            # Open files in directory
fuser -vm /mnt/data         # Process using a mount
```

## Network
```bash
ip addr                     # Network interfaces
ip route                    # Routing table
ss -tulpn                   # Listening ports with PIDs
ping -c 4 8.8.8.8           # Connectivity test
traceroute google.com       # Route tracing
dig +short example.com      # DNS resolution
curl -v https://example.com # HTTP debug
nc -vz host 22              # TCP port check
tcpdump -i eth0 port 80     # Packet capture
nmap -sT -p 22,80 localhost # Port scan
ethtool eth0                # NIC link speed
ip neigh                    # ARP table
```

## Logs & Services
```bash
journalctl -xe              # System logs with errors
journalctl -u nginx         # Service-specific logs
systemctl status nginx      # Service health
systemctl --failed          # Failed services
systemd-analyze blame       # Boot time breakdown
last -10                    # Recent logins
who                         # Currently logged in
lsmod                       # Loaded kernel modules
modinfo <module>            # Module details
```

## Files & Permissions
```bash
find /var/log -type f -mtime -1   # Files changed today
grep -Rin "error" /var/log        # Recursive log search
diff file1 file2                  # Compare files
stat file                         # File timestamps, inode
md5sum file                       # Verify integrity
lsof +L1                          # Deleted files still open
lsattr file                       # Extended attributes
```

## Advanced Debugging
```bash
strace -f -p <PID>          # Trace syscalls
ltrace ./binary             # Trace library calls
perf top                    # CPU profiling
perf stat ./program         # Execution statistics
time ./script.sh            # Measure execution time
sar -n DEV 1 3              # Network throughput stats
```

---

# Additional Interview Questions & Answers

## Package Management Deep Dive

**Q26: How to build and install packages from source?**

```bash
# Install build tools
sudo apt install build-essential    # Debian
sudo yum groupinstall "Development Tools"  # RHEL

# Standard build flow
wget https://example.com/tool.tar.gz
tar -xvzf tool.tar.gz && cd tool
./configure                 # Check dependencies, create Makefile
make -j$(nproc)             # Compile using all CPU cores
sudo make install           # Install to /usr/local/bin

# Better: use checkinstall to create a .deb for clean removal
sudo checkinstall           # Creates .deb and installs
sudo dpkg -r tool           # Clean uninstall later
```

**Real-world**: Building Nginx with custom modules, compiling the latest Redis, or tools not yet in your distro's repos.

**Q27: How to create a .deb or .rpm package?**

```bash
# .deb package
mkdir -p myapp/DEBIAN myapp/usr/local/bin
cp mybinary myapp/usr/local/bin/myapp
cat > myapp/DEBIAN/control << EOF
Package: myapp
Version: 1.0
Architecture: amd64
Maintainer: You <you@example.com>
Description: My application
EOF
dpkg-deb --build myapp      # Creates myapp.deb

# .rpm package
sudo yum install rpm-build rpmdevtools
rpmdev-setuptree
# Create .spec file, then:
rpmbuild -ba ~/rpmbuild/SPECS/myapp.spec
```

## SSH and Security Deep Dive

**Q28: What is SSH hardening? How do you secure remote access?**

Edit `/etc/ssh/sshd_config`:

```bash
PermitRootLogin no              # 1. Disable root SSH login
PasswordAuthentication no       # 2. Key-based auth only
Port 2222                       # 3. Non-standard port
AllowUsers alice bob deploy     # 4. Restrict who can SSH
MaxAuthTries 3                  # 5. Limit login attempts
ClientAliveInterval 300         # 6. Timeout idle sessions
ClientAliveCountMax 2
```

```bash
# Apply changes
sudo systemctl restart sshd

# Install fail2ban for brute-force protection
sudo apt install fail2ban
sudo systemctl enable --now fail2ban

# Enable 2FA with Google Authenticator
sudo apt install libpam-google-authenticator
google-authenticator           # Run as user to set up
```

**Real-world**: SSH is the #1 attack vector on Linux servers. Every production server should have root login disabled, key-only auth, and fail2ban running.

## Kernel Deep Dive

**Q29: How do you update the kernel safely?**

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install --install-recommends linux-generic
sudo reboot
uname -r                       # Verify new kernel

# RHEL/CentOS
sudo yum update kernel
rpm -q kernel                  # List installed kernels
sudo reboot
```

If the new kernel fails to boot, select an older kernel from the GRUB menu.

**Q30: How do you compile a custom kernel?**

```bash
# 1. Install dependencies
sudo apt install build-essential libncurses-dev bison flex libssl-dev libelf-dev

# 2. Download kernel source
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.x.y.tar.xz
tar -xf linux-6.x.y.tar.xz && cd linux-6.x.y

# 3. Configure
make menuconfig                # Interactive menu to select features

# 4. Compile
make -j$(nproc)                # Takes 15-60 minutes

# 5. Install
sudo make modules_install
sudo make install
sudo update-grub

# 6. Reboot into new kernel
sudo reboot
uname -r                      # Verify
```

**Real-world**: Custom kernels are used in embedded systems, performance-critical servers, and kernel development. Always keep the old kernel as a fallback.

## Backup and Recovery

**Q31: How to use rsync, tar, dd, and scp for backups?**

```bash
# rsync — incremental sync (only copies changes)
rsync -avz /source/ /backup/                    # Local
rsync -avz -e ssh /etc/ user@remote:/backup/    # Remote
rsync -avn /source/ /backup/                    # Dry run (preview)

# tar — archive and compress
tar -czvf backup-$(date +%F).tar.gz /etc /var/www
tar -xzvf backup.tar.gz                         # Extract
tar -tzvf backup.tar.gz                         # List contents

# dd — block-level disk image
sudo dd if=/dev/sda of=/mnt/backup/sda.img bs=4M status=progress
sudo dd if=/mnt/backup/sda.img of=/dev/sda bs=4M  # Restore

# scp — secure copy over SSH
scp backup.tar.gz user@remote:/backups/
scp -r /etc user@remote:/backups/etc
```

**Q32: How to automate backups in production?**

```bash
#!/bin/bash
set -euo pipefail
DATE=$(date +%F)
tar -czf /backups/backup-${DATE}.tar.gz /etc /var/www
aws s3 cp /backups/backup-${DATE}.tar.gz s3://mybucket/backups/
find /backups -name "*.tar.gz" -mtime +30 -delete
```

Schedule: `0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1`

**Q33: How to restore deleted files from snapshots?**

```bash
# LVM snapshot
lvcreate --size 1G --snapshot --name snap /dev/vg0/root
mount /dev/vg0/snap /mnt/snap
cp /mnt/snap/etc/important.conf /etc/

# Btrfs snapshot
btrfs subvolume snapshot /data /data/snap-$(date +%F)
btrfs subvolume list /data

# ZFS snapshot
zfs snapshot pool/data@backup1
zfs rollback pool/data@backup1
```

**Q34: How to manage offsite backups securely?**

```bash
# Encrypted transfer
rsync -avz -e ssh /backups/ user@remote:/safe-storage/

# Encrypt before upload
gpg --symmetric --cipher-algo AES256 backup.tar.gz
aws s3 cp backup.tar.gz.gpg s3://mybucket/ --sse

# Verify integrity
md5sum backup.tar.gz > backup.md5
# After download:
md5sum -c backup.md5
```

## Containers and Virtualization

**Q35: How do containers differ from VMs?**

| Feature | Container | VM |
|---------|-----------|-----|
| Isolation | Kernel-level (namespaces, cgroups) | Hardware-level (hypervisor) |
| Boot time | Milliseconds | Minutes |
| Size | MBs | GBs |
| Kernel | Shared with host | Own kernel |
| Overhead | Minimal | Significant |
| Use case | Microservices, CI/CD | Legacy apps, multi-OS |

**Q36: What is KVM and how to set up a VM?**

```bash
# Check CPU virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo

# Install KVM
sudo apt install qemu-kvm libvirt-daemon-system virtinst

# Create VM
sudo virt-install --name myvm --ram 2048 --vcpus 2 \
  --disk size=20 --os-variant ubuntu22.04 \
  --cdrom /path/to/ubuntu.iso

# Manage VMs
virsh list --all
virsh start myvm
virsh shutdown myvm
```

**Q37: How does container networking work?**

```bash
# Docker creates a bridge network (docker0)
ip addr show docker0

# Each container gets its own network namespace
docker inspect --format='{{.NetworkSettings.IPAddress}}' container_name

# View iptables rules added by Docker
sudo iptables -t nat -L -n

# Kubernetes uses CNI plugins (Calico, Flannel, Cilium)
# Each pod gets its own IP address
kubectl get pods -o wide
```

## Automation and Configuration Management

**Q38: What is Ansible and how does it manage Linux servers?**

```bash
# Install
sudo apt install ansible

# Ad-hoc command
ansible all -i hosts -m ping
ansible webservers -m shell -a "uptime"

# Playbook
ansible-playbook -i hosts deploy.yml
```

Ansible is agentless (uses SSH), uses YAML playbooks, and is the most popular tool for Linux configuration management.

**Q39: What is Infrastructure as Code (IaC)?**

IaC treats infrastructure configuration as version-controlled code:
- **Terraform**: Provisions cloud resources (VMs, networks, storage)
- **Ansible**: Configures servers (packages, services, files)
- **Packer**: Builds machine images (AMIs, VM images)

```bash
# Terraform workflow
terraform init      # Initialize
terraform plan      # Preview changes
terraform apply     # Create infrastructure
terraform destroy   # Tear down
```

**Q40: How to automate Linux patching?**

```bash
# Debian/Ubuntu — unattended upgrades
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# RHEL/CentOS — automatic updates
sudo yum install yum-cron
sudo systemctl enable --now yum-cron

# Ansible playbook for patching
# patch.yml
---
- hosts: all
  become: yes
  tasks:
    - name: Update all packages
      apt:
        upgrade: dist
        update_cache: yes
      when: ansible_os_family == "Debian"
```

## Scenario-Based Questions

**Q41: Describe how you would troubleshoot a production server that's unresponsive.**

```bash
# 1. Check if you can SSH in
ssh user@server

# 2. If yes — first 60 seconds checklist:
uptime                          # Load average
dmesg | tail                    # Kernel errors
vmstat 1 5                      # CPU/memory/swap
free -h                         # Memory state
df -h                           # Disk space
ps aux --sort=-%cpu | head      # Top CPU processes
ps aux --sort=-%mem | head      # Top memory processes
ss -tulnp                       # Listening ports
journalctl -xe                  # Recent errors

# 3. If SSH fails — check from cloud console
# Check security groups, network ACLs
# Use cloud serial console
# Check if instance is running
```

**Q42: How do you prioritize multiple system alerts?**

Priority order:
1. **Data loss risk** — disk full, database corruption → immediate
2. **Service down** — application unreachable → high priority
3. **Performance degradation** — high CPU/memory → medium priority
4. **Security alerts** — failed logins, suspicious activity → investigate
5. **Warnings** — disk approaching threshold → schedule fix

**Q43: How do you manage Linux systems at scale?**

- **Configuration management**: Ansible/Puppet for consistent state
- **Monitoring**: Prometheus + Grafana for metrics and alerts
- **Centralized logging**: ELK/Loki for log aggregation
- **SSH key management**: HashiCorp Vault or AWS SSM
- **Patching**: Automated via unattended-upgrades or Ansible
- **Immutable infrastructure**: Packer images + Terraform
- **Inventory**: Dynamic inventory from cloud APIs

**Q44: What would you include in a Linux hardening checklist?**

```bash
# 1. SSH hardening
PermitRootLogin no
PasswordAuthentication no

# 2. Firewall
sudo ufw enable
sudo ufw default deny incoming

# 3. Remove unused services
systemctl list-units --type=service
sudo systemctl disable <unused_service>

# 4. Security updates
sudo apt update && sudo apt upgrade -y

# 5. Monitoring
sudo apt install fail2ban auditd
sudo systemctl enable --now fail2ban auditd

# 6. File permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 7. Kernel hardening
echo "net.ipv4.conf.all.rp_filter = 1" >> /etc/sysctl.conf
sysctl -p

# 8. Password policies
chage -M 90 -W 10 username

# 9. Audit critical files
auditctl -w /etc/passwd -p wa -k passwd_watch
auditctl -w /etc/shadow -p wa -k shadow_watch
```

---

# Top 200 Shell Scripting Debug Commands — Quick Reference

## 1. Debugging Fundamentals
```bash
set -x                          # Enable trace (print each command)
set -e                          # Exit on any error
set -u                          # Error on unset variables
set -o pipefail                 # Fail pipeline if any command fails
set -Eeuo pipefail              # Combine all safety flags
bash -x script.sh               # Run with trace
bash -n script.sh               # Syntax check only
bash -v script.sh               # Verbose (print lines as read)
```

## 2. Error Trapping
```bash
trap 'echo "Error at line $LINENO"' ERR
trap 'echo "Exiting..."' EXIT
trap 'echo "Running: $BASH_COMMAND"' DEBUG
trap 'pkill -P $$' EXIT         # Kill child processes on exit
trap 'rm -rf "$TMPDIR"' EXIT    # Cleanup temp files
```

## 3. Enhanced Trace Output
```bash
export PS4='+ ${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}() : '
set -x                          # Now trace shows file:line:function
```

## 4. Variable Inspection
```bash
declare -p var                  # Show value and type
export -p                       # List exported variables
readonly -p                     # List readonly variables
type echo                       # Is it builtin, alias, or external?
command -V ls                   # POSIX "where" for command
alias                           # List all aliases
```

## 5. File and Path Checks
```bash
stat file                       # File metadata
readlink -f file                # Resolve symlinks
realpath .                      # Canonical absolute path
file binary                     # Identify file type
lsattr file                     # Extended attributes
getfacl file                    # ACL attributes
```

## 6. Process Debugging
```bash
ps -ef | grep process           # Find process
pgrep -a name                   # PID and full command
pstree -ap $$                   # Process tree from current shell
jobs -l                         # Background jobs
strace -f -o trace.log ./cmd    # Trace syscalls
ltrace ./cmd                    # Trace library calls
lsof -p PID                     # Open files by process
```

## 7. I/O and Buffer Control
```bash
tee file.log                    # Display and log simultaneously
stdbuf -oL cmd                  # Line-buffered output
timeout 10s cmd                 # Kill hung commands
xargs -t                        # Print command before execution
```

## 8. Safety Patterns
```bash
set -m                          # Enable job control
wait                            # Wait for background jobs
ulimit -t 60                    # Limit CPU time
ionice -c3 cmd                  # Lower I/O priority
nice -n 10 cmd                  # Lower CPU priority
mktemp -d                       # Safe temporary directory
```

## 9. Text Processing Debug
```bash
grep -nR pattern path           # Recursive search with line numbers
grep -oE 'regex' file           # Print only matching parts
awk '{print NR, $0}' file       # Print with line numbers
sed -n 'l' file                 # Show hidden non-printable chars
sort | uniq -c | sort -nr       # Find most frequent lines
```

## 10. Container Debug
```bash
docker ps -a                    # All containers
docker logs name                # Container logs
docker exec -it name bash       # Enter container
docker inspect name             # Full metadata
docker top name                 # Running processes
docker stats                    # Live resource usage
docker system df                # Space usage
docker events                   # Real-time events
```

## 11. Network Debug
```bash
curl -v URL                     # Verbose HTTP debug
openssl s_client -connect h:443 # SSL handshake test
nc -vz host port                # TCP port check
dig +trace domain.com           # Full DNS resolution path
```

## 12. Common Patterns
```bash
# Retry with exponential backoff
retry() {
    local n=0
    until "$@"; do
        ((n++))
        sleep $((2**n))
        [ $n -ge 5 ] && return 1
    done
}

# Safe temp directory with cleanup
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Redirect trace to file
BASH_XTRACEFD=9
exec 9>trace.log
set -x

# Always end with explicit status
exit 0
```

---

# 300 Essential Linux Commands — Quick Reference

## System
```bash
uname -a                    # Kernel info
hostnamectl                 # Hostname and OS
cat /etc/os-release         # Distro details
uptime                      # Uptime + load
whoami                      # Current user
id                          # UID/GID/groups
date                        # Current date/time
cal                         # Calendar
timedatectl                 # Timezone info
reboot                      # Restart system
shutdown -h now             # Halt immediately
shutdown -r +10             # Reboot in 10 min
wall "message"              # Broadcast to all users
```

## Files and Directories
```bash
ls -lah                     # List with details
cd /path                    # Change directory
pwd                         # Current directory
mkdir -p dir/sub            # Create nested dirs
rm -rf dir                  # Remove recursively
cp -r src dst               # Copy recursively
mv old new                  # Move/rename
touch file                  # Create/update timestamp
find / -name "*.log"        # Search files
locate filename             # Fast search (needs updatedb)
which command               # Find command path
file myfile                 # Detect file type
stat file                   # File metadata
```

## Text Processing
```bash
cat file                    # Display file
head -n 20 file             # First 20 lines
tail -f file                # Follow file changes
less file                   # Scrollable viewer
grep -rni "pattern" dir     # Recursive search
sed 's/old/new/g' file      # Replace text
awk '{print $1}' file       # Print first column
cut -d: -f1 /etc/passwd     # Cut by delimiter
sort file                   # Sort lines
uniq -c                     # Count duplicates
wc -l file                  # Count lines
diff file1 file2            # Compare files
tr 'a-z' 'A-Z'             # Translate characters
tee output.log              # Display and save
xargs                       # Build commands from input
```

## Users and Permissions
```bash
useradd -m user             # Create user
passwd user                 # Set password
usermod -aG group user      # Add to group
userdel -r user             # Delete user + home
groupadd group              # Create group
chmod 755 file              # Change permissions
chown user:group file       # Change ownership
chage -l user               # Password policy
sudo -l                     # List sudo privileges
visudo                      # Edit sudoers safely
```

## Networking
```bash
ip addr                     # Show interfaces
ip route                    # Routing table
ss -tulnp                   # Listening ports
ping -c 4 host              # Test connectivity
traceroute host             # Trace route
dig domain                  # DNS lookup
curl -I URL                 # HTTP headers
wget URL                    # Download file
scp file user@host:/path    # Secure copy
rsync -avz src dst          # Sync files
iptables -L -n              # Firewall rules
```

## Disk and Storage
```bash
df -hT                      # Filesystem usage
du -sh dir                  # Directory size
lsblk                       # Block devices
fdisk -l                    # Partition table
mount /dev/sdb1 /mnt        # Mount filesystem
umount /mnt                 # Unmount
mkfs.ext4 /dev/sdb1         # Create filesystem
blkid                       # Show UUIDs
pvs / vgs / lvs             # LVM status
```

## Process Management
```bash
ps aux                      # All processes
top                         # Live monitor
htop                        # Enhanced monitor
kill -9 PID                 # Force kill
pkill name                  # Kill by name
nice -n 10 cmd              # Set priority
renice -5 -p PID            # Change priority
bg / fg                     # Background/foreground
jobs                        # List jobs
nohup cmd &                 # Run after logout
```

## Services and Boot
```bash
systemctl start svc         # Start service
systemctl stop svc          # Stop service
systemctl restart svc       # Restart service
systemctl enable svc        # Enable on boot
systemctl status svc        # Check status
systemctl --failed          # Failed services
journalctl -u svc           # Service logs
journalctl -f               # Follow all logs
systemd-analyze blame       # Boot time breakdown
```

## Archives and Compression
```bash
tar -czvf archive.tar.gz dir    # Create archive
tar -xzvf archive.tar.gz       # Extract archive
zip -r archive.zip dir          # Create zip
unzip archive.zip               # Extract zip
gzip file                       # Compress
gunzip file.gz                  # Decompress
```

## SSH and Remote
```bash
ssh user@host               # Connect
ssh -i key.pem user@host    # Connect with key
ssh-keygen -t ed25519       # Generate key
ssh-copy-id user@host       # Copy key to server
scp file user@host:/path    # Copy file
rsync -avz src user@host:dst  # Sync remotely
```

---

## 12.10 Quick Reference — DevOps Troubleshooting Checklist

```bash
# === System Health ===
uptime                              # Load average
free -h                             # Memory
df -h                               # Disk space
top -bn1 | head -20                 # CPU/process overview

# === Networking ===
ip -br addr                         # IP addresses
ss -tlnp                            # Listening ports
ping -c 3 gateway_ip                # Gateway connectivity
dig google.com +short               # DNS resolution
curl -sI https://service/health     # HTTP health check

# === Services ===
systemctl --failed                  # Failed services
journalctl -u service -n 50         # Recent service logs
systemctl status service            # Service status

# === Security ===
sudo lastb | head -10               # Failed logins
sudo journalctl -u sshd -n 20      # SSH logs
sudo ss -tlnp                       # Unexpected listeners

# === Disk ===
df -h                               # Filesystem usage
du -h --max-depth=1 / | sort -hr    # Space by directory
find / -size +100M -type f 2>/dev/null  # Large files

# === Processes ===
ps aux --sort=-%cpu | head -10      # Top CPU
ps aux --sort=-%mem | head -10      # Top memory
```

---

