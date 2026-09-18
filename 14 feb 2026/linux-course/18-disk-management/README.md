# Module 18: Disk Management and Storage

## 9.1 `df` — Disk Free Space

### Show filesystem usage

```bash
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
/dev/sdb1       100G   45G   50G  48% /data
tmpfs           798M  1.2M  797M   1% /run
/dev/sda2       500M  120M  344M  26% /boot
```

**Explanation**:
- `-h` — human-readable sizes (G, M, K)
- `Filesystem` — the device or partition
- `Mounted on` — where in the directory tree this filesystem is accessible
- `Use%` — percentage used. Alert when above 80-90%.
- `tmpfs` — temporary filesystem in RAM (not on disk)

### Show specific filesystem type

```bash
$ df -hT
Filesystem     Type      Size  Used Avail Use% Mounted on
/dev/sda1      ext4       50G   12G   35G  26% /
/dev/sdb1      xfs       100G   45G   50G  48% /data
tmpfs          tmpfs     3.9G     0  3.9G   0% /dev/shm
```

**Explanation**: `-T` shows the filesystem type. `ext4` and `xfs` are the most common Linux filesystems.

### Show inode usage

```bash
$ df -i
Filesystem      Inodes  IUsed   IFree IUse% Mounted on
/dev/sda1      3276800 245000 3031800    8% /
/dev/sdb1      6553600  12000 6541600    1% /data
```

**Explanation**: Each file uses one inode. You can run out of inodes before running out of disk space if you have millions of tiny files (common with mail servers or package caches). If disk has space but you cannot create files, inode exhaustion is the likely cause.

### View inode number of a file

```bash
# Show inode numbers with ls
$ ls -i /etc/passwd
1048577 /etc/passwd

# Long listing with inodes and hidden files
$ ls -lia /home/devops/
total 32
1048577 drwxr-xr-x  5 devops devops 4096 Feb  5 10:00 .
1048576 drwxr-xr-x  3 root   root   4096 Jan  1 00:00 ..
1048580 -rw-------  1 devops devops  500 Feb  5 10:00 .bash_history
1048581 -rw-r--r--  1 devops devops  220 Jan  1 00:00 .bashrc
1048590 -rw-r--r--  1 devops devops  100 Feb  5 09:00 notes.txt

# Detailed inode info with stat
$ stat /etc/passwd
  File: /etc/passwd
  Size: 1890            Blocks: 8          IO Block: 4096   regular file
Device: 801h/2049d      Inode: 1048577     Links: 1
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2025-02-05 10:00:00.000000000 +0000
Modify: 2025-02-01 08:30:00.000000000 +0000
Change: 2025-02-01 08:30:00.000000000 +0000
```

**Explanation**: `ls -i` shows the inode number. `stat` shows full metadata including inode, link count, permissions, and timestamps. Two files with the same inode number are hard links to the same data.

---

## 9.2 `du` — Disk Usage

### Check directory size

```bash
$ du -sh /var/log/
245M    /var/log/
```

**Explanation**: `-s` = summary (total only), `-h` = human-readable. Shows the total size of `/var/log/` and all its contents.

### Show subdirectory sizes

```bash
$ du -h --max-depth=1 /var/
4.0K    /var/tmp
245M    /var/log
120M    /var/cache
35M     /var/lib
1.2G    /var/www
1.6G    /var/
```

**Explanation**: `--max-depth=1` shows sizes one level deep. Quickly identifies which subdirectory is consuming the most space.

### Find largest directories

```bash
$ du -h --max-depth=1 /var/ | sort -hr | head -10
1.6G    /var/
1.2G    /var/www
245M    /var/log
120M    /var/cache
35M     /var/lib
4.0K    /var/tmp
```

**Explanation**: `sort -hr` sorts by human-readable sizes in reverse (largest first). This is the go-to command for finding what's eating disk space.

### Check file sizes in current directory

```bash
$ du -sh * | sort -hr
500M    node_modules
120M    dist
45M     src
2.0M    package-lock.json
4.0K    package.json
```

### Exclude patterns

```bash
$ du -sh --exclude='node_modules' --exclude='.git' /opt/myapp/
15M     /opt/myapp/
```

---

## 9.3 `lsblk` — List Block Devices

```bash
$ lsblk
NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
sda      8:0    0    50G  0 disk
├─sda1   8:1    0  49.5G  0 part /
└─sda2   8:2    0   500M  0 part /boot
sdb      8:16   0   100G  0 disk
└─sdb1   8:17   0   100G  0 part /data
sr0     11:0    1  1024M  0 rom
```

**Explanation**:
- `sda` — first disk, `sdb` — second disk
- `sda1`, `sda2` — partitions on the first disk
- `TYPE`: `disk` = whole disk, `part` = partition, `rom` = CD/DVD
- `RO` = read-only (0 = read-write)
- `MOUNTPOINT` — where the partition is mounted

### Show filesystem info

```bash
$ lsblk -f
NAME   FSTYPE LABEL UUID                                 MOUNTPOINT
sda
├─sda1 ext4         a1b2c3d4-e5f6-7890-abcd-ef1234567890 /
└─sda2 ext4         f6e5d4c3-b2a1-0987-fedc-ba9876543210 /boot
sdb
└─sdb1 xfs          12345678-abcd-ef01-2345-678901234567 /data
```

**Explanation**: Shows filesystem type, UUID (universally unique identifier used in `/etc/fstab`), and mount points.

---

## 9.4 `fdisk` — Partition Management

### List all partitions

```bash
$ sudo fdisk -l
Disk /dev/sda: 50 GiB, 53687091200 bytes, 104857600 sectors
Disklabel type: gpt

Device       Start       End   Sectors  Size Type
/dev/sda1     2048 103809023 103806976 49.5G Linux filesystem
/dev/sda2 103809024 104857566   1048543  500M Linux filesystem

Disk /dev/sdb: 100 GiB, 107374182400 bytes, 209715200 sectors
Device     Start       End   Sectors  Size Type
/dev/sdb1   2048 209715166 209713119  100G Linux filesystem
```

### Create a partition (interactive)

```bash
$ sudo fdisk /dev/sdc
Command (m for help): n          # New partition
Partition type: p                # Primary
Partition number: 1
First sector: (default)
Last sector: (default, uses all space)

Command (m for help): w          # Write changes and exit
```

**Explanation**: `fdisk` is interactive. `n` creates a new partition, `w` writes changes to disk. Changes are not applied until you press `w`.

---

## 9.5 Filesystem Creation & Mounting

### Create a filesystem

```bash
# Create ext4 filesystem
$ sudo mkfs.ext4 /dev/sdc1
mke2fs 1.46.5 (30-Dec-2021)
Creating filesystem with 26214144 4k blocks and 6553600 inodes
Filesystem UUID: abcdef12-3456-7890-abcd-ef1234567890

# Create XFS filesystem
$ sudo mkfs.xfs /dev/sdc1
```

### Mount a filesystem

```bash
# Create mount point
$ sudo mkdir /mnt/data

# Mount
$ sudo mount /dev/sdc1 /mnt/data

# Verify
$ df -h /mnt/data
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdc1       100G   60M   95G   1% /mnt/data

$ mount | grep sdc1
/dev/sdc1 on /mnt/data type ext4 (rw,relatime)
```

### Unmount

```bash
$ sudo umount /mnt/data

# If "device is busy"
$ sudo umount -l /mnt/data    # Lazy unmount (detach now, cleanup later)
$ sudo fuser -mv /mnt/data    # Find who's using it
```

### Persistent mount (`/etc/fstab`)

```bash
$ cat /etc/fstab
# <device>                                <mount>    <type> <options>        <dump> <pass>
UUID=a1b2c3d4-e5f6-7890-abcd-ef1234567890 /          ext4   defaults         0      1
UUID=f6e5d4c3-b2a1-0987-fedc-ba9876543210 /boot      ext4   defaults         0      2
UUID=abcdef12-3456-7890-abcd-ef1234567890 /mnt/data  ext4   defaults,noatime 0      2
```

**Explanation**: `/etc/fstab` defines filesystems to mount at boot. Fields:
- `UUID` — device identifier (more reliable than `/dev/sdX` which can change)
- `mount point` — where to mount
- `type` — filesystem type
- `options` — `defaults` = rw,suid,dev,exec,auto,nouser,async. `noatime` = don't update access time (improves performance)
- `dump` — backup flag (0 = skip)
- `pass` — fsck order (1 = root first, 2 = others, 0 = skip)

### Add a new entry and mount

```bash
# Get UUID
$ sudo blkid /dev/sdc1
/dev/sdc1: UUID="abcdef12-3456-7890-abcd-ef1234567890" TYPE="ext4"

# Add to fstab
$ echo 'UUID=abcdef12-3456-7890-abcd-ef1234567890 /mnt/data ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab

# Mount all entries in fstab
$ sudo mount -a

# Verify
$ df -h /mnt/data
```

---


## 9.9 Practical DevOps Scenarios

### Scenario 1: Disk space emergency

```bash
# 1. Check overall usage
$ df -h

# 2. Find largest directories
$ sudo du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10

# 3. Find large files
$ sudo find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -10

# 4. Clean up common space hogs
$ sudo apt clean                          # Package cache
$ sudo journalctl --vacuum-size=100M      # Systemd logs
$ sudo find /tmp -type f -mtime +7 -delete # Old temp files
$ sudo find /var/log -name "*.gz" -mtime +30 -delete  # Old compressed logs
```

### Scenario 2: Add storage to a running server

```bash
# 1. Identify new disk
$ lsblk

# 2. Create PV, extend VG, extend LV
$ sudo pvcreate /dev/sdd
$ sudo vgextend vg_data /dev/sdd
$ sudo lvextend -l +100%FREE --resizefs /dev/vg_data/lv_app

# 3. Verify
$ df -h /opt/app
```

### Scenario 3: Monitor disk health

```bash
# Check SMART data (requires smartmontools)
$ sudo smartctl -a /dev/sda
SMART overall-health self-assessment test result: PASSED

# Check filesystem for errors
$ sudo fsck -n /dev/sda1    # -n = no changes, just check
```

### Scenario 4: Disk full but can't find large files (deleted files held open)

```bash
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   49G    0G  99% /

$ sudo du -sh / 2>/dev/null
35G     /
# Only 35G accounted for — 14G is in deleted-but-open files!

# Find deleted files still held open
$ sudo lsof | grep '(deleted)' | awk '{print $7, $1, $2, $9}' | sort -rn | head -5
10000000000 nginx 890 /var/log/nginx/access.log
 4000000000 java 3456 /var/log/myapp/debug.log

# Fix: restart the process to release the file handle
$ sudo systemctl restart nginx
$ sudo systemctl restart myapp

# Verify space is freed
$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   35G   12G  75% /
```

### Scenario 5: Inode exhaustion (disk has space but can't create files)

```bash
$ touch /tmp/test
touch: cannot touch '/tmp/test': No space left on device

$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   30G   17G  64% /
# Disk has space!

$ df -i /
Filesystem      Inodes  IUsed   IFree IUse% Mounted on
/dev/sda1      3276800 3276800      0  100% /
# Inodes are exhausted — millions of tiny files

# Find directories with the most files
$ sudo find / -xdev -printf '%h\n' 2>/dev/null | sort | uniq -c | sort -rn | head -5
 2500000 /var/spool/postfix/maildrop
  500000 /tmp/php-sessions

# Clean up
$ sudo find /var/spool/postfix/maildrop -type f -delete
$ sudo find /tmp/php-sessions -type f -mtime +1 -delete
```

### Scenario 6: Check disk I/O performance

```bash
# Real-time I/O stats
$ iostat -xh 1 5
Device      r/s     w/s   rkB/s   wkB/s  await  %util
sda        50.0   200.0  2000.0  50000.0   12.5   85.0

# await > 20ms on SSD = problem
# %util > 80% = disk is saturated

# Find which process is doing the I/O
$ sudo iotop -oP
  PID  PRIO  USER     DISK READ  DISK WRITE  COMMAND
 2345 be/4 postgres    2.00 M/s   45.00 M/s  postgres: writer

# Check for I/O wait in CPU stats
$ mpstat 1 3
CPU    %usr   %sys   %iowait   %idle
all     5.0    2.0      40.0    53.0
# 40% iowait = CPU is spending 40% of time waiting for disk
```

---

## 9.10 Addon Commands

### `ncdu` — Interactive disk usage viewer

```bash
$ sudo ncdu /var
ncdu 1.17 ~ Use the arrow keys to navigate, press ? for help
--- /var -------------------------------------------------------
   20.0 GiB [##########] /log
    3.0 GiB [#         ] /cache
    1.0 GiB [          ] /lib
  500.0 MiB [          ] /www
    4.0 KiB [          ] /tmp
 Total disk usage:  24.5 GiB  Apparent size:  24.3 GiB  Items: 45000
```

**Explanation**: `ncdu` is an interactive `du`. Navigate with arrow keys, press `d` to delete, `q` to quit. Install with `sudo apt install ncdu`.

### `lsof +D` — Find what's using a mount point

```bash
# Before unmounting, find who's using it
$ sudo lsof +D /mnt/data
COMMAND   PID   USER   FD   TYPE NAME
bash     1234 devops  cwd    DIR /mnt/data
python3  5678 devops    3r   REG /mnt/data/input.csv

# Kill those processes, then unmount
$ sudo kill 1234 5678
$ sudo umount /mnt/data
```

### `tune2fs` — Tune ext4 filesystem parameters

```bash
# Show filesystem info
$ sudo tune2fs -l /dev/sda1 | head -20
Filesystem volume name:   <none>
Last mounted on:          /
Filesystem UUID:          a1b2c3d4-e5f6-7890-abcd-ef1234567890
Filesystem state:         clean
Errors behavior:          Continue
Filesystem OS type:       Linux
Inode count:              3276800
Block count:              13107200
Free blocks:              9000000
Free inodes:              3031800
Block size:               4096
Filesystem created:       Mon Dec 22 12:00:00 2024
Last mount time:          Mon Dec 22 12:00:00 2024
Maximum mount count:      -1

# Set filesystem label
$ sudo tune2fs -L "root-disk" /dev/sda1

# Set reserved blocks percentage (default 5% reserved for root)
$ sudo tune2fs -m 1 /dev/sda1
# Reduces reserved space from 5% to 1% — frees ~2GB on a 50GB disk

# Disable filesystem check on boot
$ sudo tune2fs -c 0 -i 0 /dev/sda1
```

### `e2fsck` / `fsck` — Check and repair filesystems

```bash
# Check filesystem (must be unmounted or read-only)
$ sudo e2fsck -n /dev/sda2          # Check only, no changes
$ sudo fsck -n /dev/sda2            # Generic wrapper

# Repair filesystem (DANGEROUS — unmount first!)
$ sudo umount /dev/sda2
$ sudo e2fsck -y /dev/sda2          # Auto-fix all errors
$ sudo mount /dev/sda2 /data

# Force check on next boot
$ sudo touch /forcefsck
$ sudo reboot
```

> ⚠️ Never run `fsck` on a mounted filesystem — it can cause data corruption.

### `xfs_info` / `xfs_growfs` — XFS filesystem tools

```bash
# Show XFS filesystem info
$ sudo xfs_info /data
meta-data=/dev/sdb1              isize=512    agcount=4, agsize=6553600 blks
data     =                       bsize=4096   blocks=26214400
naming   =version 2              bsize=4096
log      =internal               bsize=4096   blocks=12800
realtime =none                   extsz=4096

# Grow XFS filesystem (after extending the partition/LV)
$ sudo xfs_growfs /data

# Repair XFS
$ sudo xfs_repair /dev/sdb1
```

### `fallocate` — Quickly create files of specific size (for testing)

```bash
$ fallocate -l 1G /tmp/testfile
$ ls -lh /tmp/testfile
-rw-r--r-- 1 devops devops 1.0G Feb  5 15:00 /tmp/testfile

# Clean up
$ rm /tmp/testfile
```

---


## 9.12 Additional Admin Commands (Requested Set)

```bash
$ mount
$ umount /dev/sda1
$ lsblk
$ fdisk -l
```

**Purpose**: Inspect block devices, mounts, and partition layouts.

### Power/restart controls

```bash
$ reboot
$ shutdown now
$ shutdown -r now
$ shutdown -h now
```

**Use case**: Controlled reboot/halt during maintenance windows.

---

## 9.13 Sample File + Output Walkthrough

Use a sample disk report file to practice reading command output.

### Sample File

```bash
$ cat /tmp/df_sample.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   44G  4.0G  92% /
/dev/sdb1       200G   80G  110G  43% /data
tmpfs           3.9G     0  3.9G   0% /run/user/1000
```

### Commands, Output, and Meaning

```bash
$ awk 'NR==1 || $5+0 >= 85' /tmp/df_sample.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   44G  4.0G  92% /
```

**Explanation**: Filters only critical filesystems (>=85% full).

```bash
$ awk 'NR>1 {print $6, $5}' /tmp/df_sample.txt
/ 92%
/data 43%
/run/user/1000 0%
```

**Explanation**: Prints mount point and usage percentage for quick alert summaries.

```bash
$ awk 'NR>1 && $6=="/" {print "Root free space:", $4}' /tmp/df_sample.txt
Root free space: 4.0G
```

**Explanation**: Extracts root filesystem free space for incident notes.

### Real-life use case

On-call engineers often paste `df -h` output into tickets. These filters speed up triage and reduce noisy data.

### Troubleshooting checklist

- If `%Use` is high: run `du -h --max-depth=1 / | sort -hr | head`
- If disk space looks fine but writes fail: run `df -i` for inode exhaustion
- If space is not reclaimed after delete: run `lsof | grep '(deleted)'`
- If mount fails: check `lsblk -f`, `blkid`, and `/etc/fstab`

## Summary

| Command     | Purpose                      | Key Usage                           |
|-------------|------------------------------|-------------------------------------|
| `df`        | Filesystem free space        | `df -h`, `df -i` (inodes)          |
| `du`        | Directory disk usage         | `du -sh`, `du -h --max-depth=1`    |
| `lsblk`     | List block devices           | `lsblk -f` (with filesystem info)  |
| `fdisk`     | Partition management         | `fdisk -l`, `fdisk /dev/sdX`       |
| `mkfs`      | Create filesystem            | `mkfs.ext4`, `mkfs.xfs`            |
| `mount`     | Mount filesystem             | `mount /dev/sdX /mnt/point`        |
| `umount`    | Unmount filesystem           | `umount /mnt/point`                |
| `blkid`     | Show block device UUIDs      | `blkid /dev/sdX`                   |
| `pvcreate`  | Create LVM physical volume   | `pvcreate /dev/sdX`                |
| `vgcreate`  | Create LVM volume group      | `vgcreate vg_name /dev/sdX`        |
| `lvcreate`  | Create LVM logical volume    | `lvcreate -L 50G -n lv_name vg`   |
| `lvextend`  | Extend logical volume        | `lvextend -L +50G --resizefs`      |
| `free`      | Show RAM and swap usage      | `free -h`                          |
| `iostat`    | Disk I/O statistics          | `iostat -xh 1`                     |

**Next Module**: [10 - Text Processing](../10-text-processing/README.md)

---

## 9.14 Filesystem Types Comparison

| Filesystem | Description | Max File Size | Default In |
|-----------|-------------|---------------|------------|
| **ext4** | Most common Linux FS, journaling, stable | 16 TB | Ubuntu, Debian |
| **xfs** | High-performance, great for large files | 8 EB | RHEL, CentOS |
| **btrfs** | Modern, copy-on-write, snapshots, compression | 16 EB | openSUSE, Fedora |
| **ntfs** | Windows filesystem (read-write via ntfs-3g) | 16 TB | Windows |
| **vfat** | FAT32, USB/SD card compatibility | 4 GB | Removable media |

### btrfs — Modern Copy-on-Write Filesystem

```bash
# Create btrfs filesystem
sudo mkfs.btrfs /dev/sdb1

# Mount
sudo mount /dev/sdb1 /mnt/data

# Create a subvolume
sudo btrfs subvolume create /mnt/data/mysubvol

# Create a snapshot
sudo btrfs subvolume snapshot /mnt/data /mnt/data/snapshot-$(date +%F)

# List subvolumes
sudo btrfs subvolume list /mnt/data

# Check filesystem usage
sudo btrfs filesystem usage /mnt/data

# Enable compression
sudo mount -o compress=zstd /dev/sdb1 /mnt/data

# Scrub (check integrity)
sudo btrfs scrub start /mnt/data
sudo btrfs scrub status /mnt/data
```

**Use cases**: Snapshots before upgrades, backup-friendly environments, container storage.

---

## 9.15 Automounting with systemd Mount Units

Instead of `/etc/fstab`, you can use systemd `.mount` units for more control.

Create `/etc/systemd/system/data.mount`:

```ini
[Unit]
Description=Mount Data Volume

[Mount]
What=/dev/datavg/datalv
Where=/data
Type=ext4
Options=defaults

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now data.mount

# Check status
systemctl status data.mount

# View all mount units
systemctl list-units --type=mount
```

> The filename must match the mount path: `/data` → `data.mount`, `/mnt/backup` → `mnt-backup.mount`.

---

## 9.16 Filesystem Check and Repair

```bash
# Check filesystem (must be unmounted)
sudo umount /dev/sdb1
sudo fsck /dev/sdb1

# Auto-fix errors
sudo fsck -y /dev/sdb1

# Check ext4 specifically
sudo e2fsck -f /dev/sdb1

# Check XFS (cannot be unmounted — runs online)
sudo xfs_repair -n /dev/sdb1    # Dry run
sudo xfs_repair /dev/sdb1       # Actual repair

# Schedule fsck on next boot (for root filesystem)
sudo touch /forcefsck
sudo reboot
```

### Disk Health Monitoring

```bash
# Install smartmontools
sudo apt install smartmontools

# Check disk health
sudo smartctl -a /dev/sda

# Run a short self-test
sudo smartctl -t short /dev/sda

# Check test results
sudo smartctl -l selftest /dev/sda

# Test read/write speed
sudo hdparm -Tt /dev/sda
```

---

