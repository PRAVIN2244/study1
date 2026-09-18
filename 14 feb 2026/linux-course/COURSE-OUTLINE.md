# Linux for DevOps Engineers — Course Outline

30 modules across 5 phases. Each module has a README with examples, commands, and interview questions.

---

## Phase 1: Beginner — "What is Linux?"

| # | Module | Key Topics |
|---|--------|------------|
| 01 | What is Linux | Kernel + GNU = OS, history, open source licensing, Linux vs Windows |
| 02 | Linux Architecture | Layers (hardware → kernel → shell → apps), kernel types, system calls, devices |
| 03 | Boot Process and Init Systems | BIOS/UEFI → GRUB → kernel → systemd, runlevels vs targets |
| 04 | Linux Distributions | Debian/RHEL/Arch families, choosing a distro for DevOps |
| 05 | First Day on the Terminal | Shell prompt, basic commands (whoami, uname, date, uptime), getting help (man, --help) |
| 06 | Navigating the Filesystem | FHS, pwd, ls, cd, mkdir, rmdir, tree, absolute vs relative paths |

---

## Phase 2: Comfortable User — "I can use the terminal"

| # | Module | Key Topics |
|---|--------|------------|
| 07 | Creating and Viewing Files | touch, cat, head, tail -f, less, wc, file types |
| 08 | Copying, Moving, Linking | cp, mv, rm, symbolic links, hard links, inodes, wildcards |
| 09 | Finding Files and Text | find, locate, grep, combining find + grep |
| 10 | Permissions and Ownership | rwx, chmod, chown, umask, SUID/SGID/sticky bit, ACLs |
| 11 | User and Group Management | /etc/passwd, useradd, usermod, sudo, visudo, PAM |
| 12 | Process Management | ps, top, htop, kill signals, bg/fg, nice, strace |

---

## Phase 3: System Administrator — "I manage servers"

| # | Module | Key Topics |
|---|--------|------------|
| 13 | Package Management | apt, yum/dnf, dpkg, rpm, apk, repos, building from source |
| 14 | Text Processing and Logs | sed, awk, pipes, redirection, tee, cut, sort, uniq, xargs, log analysis |
| 15 | Networking Fundamentals | IP/subnetting, TCP vs UDP, ip addr, ip route, ping, DNS (dig, nslookup) |
| 16 | Network Tools and Diagnostics | ss, curl, wget, scp, rsync, traceroute, tcpdump, nmap |
| 17 | Firewalls and Network Security | ufw, iptables, nftables, firewalld, netplan/nmcli |
| 18 | Disk Management | df, du, lsblk, fdisk, parted, mkfs, mount, /etc/fstab, filesystem types |
| 19 | LVM, RAID, Advanced Storage | PV/VG/LV, lvextend, RAID 0/1/5/10, mdadm, swap, iostat |
| 20 | Systemd and Services | systemctl, unit files, journalctl, timers, targets, boot analysis |

---

## Phase 4: DevOps Engineer — "I automate and deploy"

| # | Module | Key Topics |
|---|--------|------------|
| 21 | Shell Scripting Fundamentals | Variables, exit codes, read input, environment variables |
| 22 | Shell Scripting — Control Flow | if/elif/else, case, for/while/until loops, functions, getopts |
| 23 | Shell Scripting — Debugging and Cron | set -euo pipefail, trap, bash -x, shellcheck, cron, systemd timers |
| 24 | SSH and Remote Management | ssh-keygen, ssh-copy-id, SSH config, tunneling, hardening, SCP/SFTP |
| 25 | Containers and Virtualization | Namespaces, cgroups, Docker, Dockerfile, Podman, KVM, container security |
| 26 | Cloud, CI/CD, Automation | cloud-init, backup/recovery, Ansible, Terraform |

---

## Phase 5: Master — "I troubleshoot anything"

| # | Module | Key Topics |
|---|--------|------------|
| 27 | System Monitoring | top, free, vmstat, iostat, sar, iftop, nethogs, alerting scripts |
| 28 | Performance Tuning and Security | sysctl, ulimit, perf, fail2ban, auditd, hardening checklist |
| 29 | Troubleshooting Playbooks | Disk full, OOM, high CPU, service down, network slow, boot failure |
| 30 | Interview Prep and Reference | 118 interview Q&A, cheat sheets, 300 essential commands |
