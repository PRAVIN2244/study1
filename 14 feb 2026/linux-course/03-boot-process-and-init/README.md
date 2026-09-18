# Module 03: The Boot Process and Init Systems

> **Level**: Absolute Beginner | **Prerequisites**: Module 02 | **Time**: 30 minutes

---

## 1.2b Init Systems: systemd vs SysVinit vs Upstart

| Feature | systemd | SysVinit | Upstart |
|---------|---------|----------|---------|
| Parallel startup | Yes | No | Yes |
| Socket activation | Yes | No | Yes |
| Service dependencies | Yes | No | Yes |
| Default in | RHEL 7+, Ubuntu 15+ | Old Debian/RHEL | Ubuntu 9-14 |
| Config format | Unit files (.service) | Shell scripts (/etc/init.d/) | Job files |

```bash
# Check which init system is running
ps -p 1 -o comm=
# Output: systemd

# systemd commands
systemctl list-units --type=service
systemctl status nginx
systemd-analyze                    # Total boot time
systemd-analyze blame              # Per-service boot time
systemd-analyze critical-chain     # Dependency chain
```

---

## 1.2c The Linux Boot Process

The boot process has 6 stages from power-on to login prompt:

```
1. BIOS/UEFI → 2. Bootloader (GRUB) → 3. Kernel → 4. Init (systemd) → 5. Services → 6. Login
```

| Stage | What Happens |
|-------|-------------|
| **BIOS/UEFI** | Power-On Self Test (POST), locates boot device |
| **Bootloader (GRUB)** | Loads the kernel image (`vmlinuz`) and initial RAM disk (`initrd`) |
| **Kernel** | Initializes hardware, mounts root filesystem, starts PID 1 |
| **Init System (systemd)** | Starts services, mounts partitions, reaches target state |
| **Services** | nginx, sshd, docker, etc. start based on dependencies |
| **Login** | TTY or GUI login prompt presented to user |

```bash
# Key boot files
ls /boot/vmlinuz-*          # Kernel binary
ls /boot/initrd.img-*       # Initial RAM disk
cat /etc/fstab              # Filesystem mount instructions
systemd-analyze             # Check boot duration
systemd-analyze blame       # Breakdown by service
```

### Runlevels vs systemd Targets

| Runlevel | systemd Target | Description |
|----------|---------------|-------------|
| 0 | `poweroff.target` | Halt/shutdown |
| 1 | `rescue.target` | Single-user mode |
| 3 | `multi-user.target` | Multi-user, CLI only |
| 5 | `graphical.target` | Multi-user with GUI |
| 6 | `reboot.target` | Reboot |

```bash
# Check current target
systemctl get-default

# Change default target
sudo systemctl set-default multi-user.target

# Switch target immediately
sudo systemctl isolate rescue.target
```

---


---

## Interview Questions

**Q1: Explain the Linux boot process step by step.**
1. BIOS/UEFI — POST, locates boot device
2. GRUB — Loads kernel (vmlinuz) and initial RAM disk (initrd)
3. Kernel — Initializes hardware, mounts root filesystem, starts PID 1
4. systemd — Starts services based on target dependencies
5. Services — nginx, sshd, docker start
6. Login — TTY or GUI prompt

**Q2: What is the difference between systemd and SysVinit?**
systemd starts services in parallel with dependency management, uses unit files, supports socket activation. SysVinit starts services sequentially using shell scripts in `/etc/init.d/`. systemd is the default on all modern distributions.

---

**Next Module**: [04 - Linux Distributions](../04-linux-distributions/README.md)
