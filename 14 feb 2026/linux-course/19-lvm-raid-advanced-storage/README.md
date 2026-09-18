# Module 19: LVM, RAID, and Advanced Storage

## 9.6 LVM — Logical Volume Manager

LVM adds a layer of abstraction between physical disks and filesystems, allowing flexible resizing.

```
Physical Disks     →  Physical Volumes (PV)  →  Volume Group (VG)  →  Logical Volumes (LV)
┌──────┐ ┌──────┐    ┌──────┐ ┌──────┐         ┌──────────────┐      ┌──────┐ ┌──────┐
│ sdb  │ │ sdc  │ →  │ PV1  │ │ PV2  │    →    │   vg_data    │  →   │ lv_app│ │lv_db │
│ 100G │ │ 200G │    │ 100G │ │ 200G │         │    300G      │      │ 150G  │ │ 100G │
└──────┘ └──────┘    └──────┘ └──────┘         └──────────────┘      └──────┘ └──────┘
                                                                      50G free
```

### Create Physical Volumes

```bash
$ sudo pvcreate /dev/sdb /dev/sdc
  Physical volume "/dev/sdb" successfully created.
  Physical volume "/dev/sdc" successfully created.

$ sudo pvs
  PV         VG   Fmt  Attr PSize   PFree
  /dev/sdb        lvm2 ---  100.00g 100.00g
  /dev/sdc        lvm2 ---  200.00g 200.00g
```

### Create Volume Group

```bash
$ sudo vgcreate vg_data /dev/sdb /dev/sdc
  Volume group "vg_data" successfully created

$ sudo vgs
  VG      #PV #LV #SN Attr   VSize   VFree
  vg_data   2   0   0 wz--n- 299.99g 299.99g
```

### Create Logical Volumes

```bash
$ sudo lvcreate -L 150G -n lv_app vg_data
  Logical volume "lv_app" created.

$ sudo lvcreate -L 100G -n lv_db vg_data
  Logical volume "lv_db" created.

$ sudo lvs
  LV     VG      Attr       LSize   Pool
  lv_app vg_data -wi-a----- 150.00g
  lv_db  vg_data -wi-a-----  100.00g
```

### Format and mount

```bash
$ sudo mkfs.ext4 /dev/vg_data/lv_app
$ sudo mkfs.xfs /dev/vg_data/lv_db

$ sudo mkdir -p /opt/app /var/lib/postgresql
$ sudo mount /dev/vg_data/lv_app /opt/app
$ sudo mount /dev/vg_data/lv_db /var/lib/postgresql
```

### Extend a logical volume (the killer feature)

```bash
# Extend LV by 50G
$ sudo lvextend -L +50G /dev/vg_data/lv_app
  Size of logical volume vg_data/lv_app changed from 150.00 GiB to 200.00 GiB.

# Resize the filesystem to use the new space
$ sudo resize2fs /dev/vg_data/lv_app        # For ext4
$ sudo xfs_growfs /opt/app                   # For XFS

# Or do both in one command
$ sudo lvextend -L +50G --resizefs /dev/vg_data/lv_app
```

**Explanation**: This is why LVM is used in production. You can grow a filesystem without downtime. XFS can only grow (not shrink). ext4 can both grow and shrink.

### Add a new disk to existing VG

```bash
$ sudo pvcreate /dev/sdd
$ sudo vgextend vg_data /dev/sdd
  Volume group "vg_data" successfully extended
```

**Explanation**: Adding a new physical disk to the volume group makes more space available for logical volumes. No downtime required.

---

## 9.7 Swap Space

Swap is disk space used as overflow when RAM is full.

### Check current swap

```bash
$ free -h
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       3.1Gi       2.1Gi       120Mi       2.5Gi       4.3Gi
Swap:          2.0Gi          0B       2.0Gi

$ swapon --show
NAME      TYPE      SIZE USED PRIO
/dev/sda3 partition   2G   0B   -2
```

### Create a swap file

```bash
# Create a 4GB swap file
$ sudo fallocate -l 4G /swapfile
$ sudo chmod 600 /swapfile
$ sudo mkswap /swapfile
Setting up swapspace version 1, size = 4 GiB

$ sudo swapon /swapfile
$ free -h | grep Swap
Swap:          6.0Gi          0B       6.0Gi
```

### Make swap persistent

```bash
$ echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Adjust swappiness

```bash
$ cat /proc/sys/vm/swappiness
60

# Lower value = prefer RAM, higher = use swap more aggressively
$ sudo sysctl vm.swappiness=10

# Make persistent
$ echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

**Explanation**: Default swappiness is 60. For database servers, set to 10 or lower to keep data in RAM. For general servers, 30-40 is reasonable.

---

## 9.8 Monitoring Disk I/O

### `iostat` — I/O statistics

```bash
$ iostat -xh 1 3
Linux 6.1.0 (server)    02/05/2025

avg-cpu:  %user   %nice %system %iowait  %steal   %idle
           5.2     0.0     1.3     0.5     0.0    93.0

Device      r/s     w/s   rkB/s   wkB/s  await  %util
sda        12.5    25.3   200.0   800.0    2.1    3.5
sdb         5.2    45.8   100.0  1500.0    4.5   12.3
```

**Explanation**:
- `r/s`, `w/s` — reads/writes per second
- `rkB/s`, `wkB/s` — read/write throughput
- `await` — average I/O wait time in ms (high = slow disk)
- `%util` — how busy the device is (100% = saturated)
- `%iowait` in CPU section — percentage of time CPU waits for I/O (high = disk bottleneck)

### `iotop` — Real-time I/O monitor

```bash
$ sudo iotop
Total DISK READ:       5.00 M/s | Total DISK WRITE:      15.00 M/s
  PID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
 2345 be/4 postgres    3.00 M/s   10.00 M/s  0.00 %  8.00 % postgres
 3456 be/4 www-data    2.00 M/s    5.00 M/s  0.00 %  4.00 % nginx
```

**Explanation**: Shows which processes are performing the most disk I/O. Useful for identifying I/O-heavy processes.

---


## 9.17 Interview Questions — Module 9

**Q1: Explain the LVM hierarchy and how to extend a logical volume.**

LVM: Physical Volume (PV) → Volume Group (VG) → Logical Volume (LV). To extend:

```bash
lvextend -L +5G /dev/myvg/mydata     # Add 5GB
resize2fs /dev/myvg/mydata           # Resize ext4 filesystem
xfs_growfs /dev/myvg/mydata          # Resize XFS filesystem
```

**Q2: What is the difference between MBR and GPT partitioning?**

MBR supports max 4 primary partitions and 2TB disk size. GPT supports 128 partitions and disks up to 9.4 ZB. GPT is required for UEFI boot and modern systems. Use `gdisk` or `parted` for GPT, `fdisk` for MBR.

**Q3: How do you troubleshoot "No space left on device" when `df` shows free space?**

Check inode exhaustion: `df -i`. If inodes are 100% used, delete unnecessary small files. Also check for deleted files held open by processes: `lsof +L1` — restart the process to release the space.

**Q4: What is RAID and what are the common levels?**

| Level | Min Disks | Redundancy | Performance | Use Case |
|-------|-----------|------------|-------------|----------|
| RAID 0 | 2 | None | High read/write | Temp data |
| RAID 1 | 2 | Mirror | Good read | OS disks |
| RAID 5 | 3 | Single parity | Good read | General |
| RAID 10 | 4 | Mirror + stripe | Best | Databases |

**Q5: How do you make a mount persistent across reboots?**

Add an entry to `/etc/fstab` using the UUID (not device name, which can change):

```bash
sudo blkid /dev/sdb1                  # Get UUID
echo "UUID=xxxx /data ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab
sudo mount -a                         # Test without rebooting
```
