# Module 18: Storage Drivers

---

## 18.1 What Are Storage Drivers?

Storage drivers control how Docker stores image layers and the container's writable layer on disk. They implement the **copy-on-write (CoW)** mechanism that makes containers lightweight.

```
┌─────────────────────────────────────────────────────────────┐
│              STORAGE DRIVER ROLE                             │
│                                                              │
│  Container (writable layer)  ← Storage driver manages this │
│  ┌──────────────────────────┐                               │
│  │  Modified files          │  Copy-on-Write                │
│  │  New files               │                               │
│  └──────────────────────────┘                               │
│  Image Layer 3 (read-only)   ← Storage driver manages this │
│  Image Layer 2 (read-only)                                  │
│  Image Layer 1 (read-only)                                  │
│                                                              │
│  Storage driver responsibilities:                           │
│    • Stack image layers into a unified filesystem           │
│    • Implement copy-on-write for container changes          │
│    • Manage layer storage on the host filesystem            │
└─────────────────────────────────────────────────────────────┘
```

---

## 18.2 Copy-on-Write (CoW) Explained

When a container modifies a file from an image layer, the storage driver copies that file to the writable layer first. The original image layer is never modified.

```
┌─────────────────────────────────────────────────────────────┐
│              COPY-ON-WRITE FLOW                              │
│                                                              │
│  Container reads /etc/nginx/nginx.conf:                     │
│    1. Storage driver searches layers top-down               │
│    2. Finds file in Image Layer 2                           │
│    3. Returns the file — no copy needed                     │
│                                                              │
│  Container modifies /etc/nginx/nginx.conf:                  │
│    1. Storage driver finds file in Image Layer 2            │
│    2. COPIES the file to the writable layer                 │
│    3. Modification happens on the copy                      │
│    4. Original in Image Layer 2 is untouched               │
│                                                              │
│  Container creates /app/newfile.txt:                        │
│    1. File written directly to writable layer               │
│    2. No copy needed — file doesn't exist in image layers  │
│                                                              │
│  Container deletes /usr/bin/curl:                           │
│    1. A "whiteout" file is created in writable layer        │
│    2. Original file still exists in image layer             │
│    3. Union filesystem hides it from the container          │
└─────────────────────────────────────────────────────────────┘
```

---

## 18.3 Available Storage Drivers

```
┌──────────────────┬──────────────────────────────────────────┐
│ Driver           │ Description                              │
├──────────────────┼──────────────────────────────────────────┤
│ overlay2         │ Modern default. Uses OverlayFS.          │
│                  │ Best performance and stability.          │
│                  │ Recommended for all Linux distros.       │
├──────────────────┼──────────────────────────────────────────┤
│ aufs             │ Original Docker storage driver.          │
│                  │ Not in mainline kernel.                  │
│                  │ Deprecated — use overlay2 instead.       │
├──────────────────┼──────────────────────────────────────────┤
│ devicemapper     │ Uses device-mapper thin provisioning.    │
│                  │ Was default on CentOS/RHEL 7.            │
│                  │ Deprecated — use overlay2 instead.       │
├──────────────────┼──────────────────────────────────────────┤
│ btrfs            │ Uses Btrfs filesystem features.          │
│                  │ Requires Btrfs-formatted backing FS.     │
│                  │ Good for snapshot-heavy workloads.       │
├──────────────────┼──────────────────────────────────────────┤
│ zfs              │ Uses ZFS filesystem features.            │
│                  │ Requires ZFS on the host.                │
│                  │ Good for data integrity.                 │
├──────────────────┼──────────────────────────────────────────┤
│ vfs              │ No copy-on-write. Full copy per layer.   │
│                  │ Very slow, very large.                   │
│                  │ Used only for testing/debugging.         │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 18.4 overlay2 — The Modern Default

overlay2 uses the Linux kernel's OverlayFS to merge multiple directories (layers) into a single unified view.

```
┌─────────────────────────────────────────────────────────────┐
│              OVERLAYFS STRUCTURE                             │
│                                                              │
│  Container sees:  /merged (unified view)                    │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │  /merged  (what the container sees)      │               │
│  │  ┌─────────────────────────────────┐     │               │
│  │  │  upperdir (writable layer)      │     │               │
│  │  │  Container's changes go here    │     │               │
│  │  └─────────────────────────────────┘     │               │
│  │  ┌─────────────────────────────────┐     │               │
│  │  │  lowerdir (read-only layers)    │     │               │
│  │  │  Image layers stacked           │     │               │
│  │  └─────────────────────────────────┘     │               │
│  │  ┌─────────────────────────────────┐     │               │
│  │  │  workdir (internal bookkeeping) │     │               │
│  │  └─────────────────────────────────┘     │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  OverlayFS merges upperdir + lowerdir into merged           │
│  Reads: check upperdir first, then lowerdir                │
│  Writes: always go to upperdir (copy-up if needed)         │
└─────────────────────────────────────────────────────────────┘
```

### Inspecting overlay2 on Disk

```bash
# Check current storage driver
$ docker info | grep "Storage Driver"
# Storage Driver: overlay2

# Image layers on disk
$ ls /var/lib/docker/overlay2/
# abc123.../
# def456.../
# l/          ← shortened symlinks for layer IDs

# Inspect a specific layer
$ ls /var/lib/docker/overlay2/abc123/
# diff/       ← actual files in this layer
# link        ← shortened ID
# lower       ← reference to parent layers
# merged/     ← unified view (only for running containers)
# work/       ← OverlayFS internal

# View the layer contents
$ ls /var/lib/docker/overlay2/abc123/diff/
# etc/  usr/  var/  ← files added/modified by this layer
```

### Viewing Container's Mount

```bash
# Find a running container's mount info
$ docker inspect mycontainer --format='{{.GraphDriver.Data}}'
# map[
#   LowerDir:/var/lib/docker/overlay2/abc.../diff:...
#   MergedDir:/var/lib/docker/overlay2/xyz.../merged
#   UpperDir:/var/lib/docker/overlay2/xyz.../diff
#   WorkDir:/var/lib/docker/overlay2/xyz.../work
# ]

# Verify with mount command
$ mount | grep overlay
# overlay on /var/lib/docker/overlay2/xyz.../merged type overlay
#   (rw,lowerdir=...,upperdir=...,workdir=...)
```

---

## 18.5 aufs — The Original Driver

AUFS (Advanced Multi-Layered Unification Filesystem) was Docker's first storage driver. It's not in the mainline Linux kernel and requires a patched kernel.

```
┌─────────────────────────────────────────────────────────────┐
│              AUFS                                            │
│                                                              │
│  Status: Deprecated                                         │
│  Supported on: Ubuntu (with aufs kernel module)             │
│  NOT supported on: CentOS, RHEL, Fedora, modern kernels    │
│                                                              │
│  How it works:                                              │
│    Similar to overlay2 — union mount of directories         │
│    Each layer is a directory under /var/lib/docker/aufs/    │
│    Supports many layers (overlay2 limited to 128)           │
│                                                              │
│  Why deprecated:                                            │
│    Not in mainline kernel — requires patches                │
│    overlay2 is faster and better maintained                 │
│    No longer the default on any distribution                │
│                                                              │
│  Migration: Switch to overlay2                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 18.6 devicemapper — Block-Level Storage

devicemapper uses Linux's device-mapper framework with thin provisioning and snapshotting at the block level (not file level).

```
┌─────────────────────────────────────────────────────────────┐
│              DEVICEMAPPER                                    │
│                                                              │
│  Status: Deprecated (removed in Docker 25+)                 │
│  Was default on: CentOS 7, RHEL 7                          │
│                                                              │
│  Two modes:                                                 │
│    loop-lvm (default): Uses loopback files                  │
│      ⚠️  Terrible performance — never use in production    │
│                                                              │
│    direct-lvm: Uses raw block devices                       │
│      Better performance but complex setup                   │
│      Requires dedicated disk/partition                      │
│                                                              │
│  How it works:                                              │
│    Creates thin-provisioned virtual devices                 │
│    Each layer is a block device snapshot                    │
│    Copy-on-write at block level (not file level)           │
│                                                              │
│  Why deprecated:                                            │
│    Complex configuration (direct-lvm)                       │
│    Poor default performance (loop-lvm)                      │
│    overlay2 works on CentOS/RHEL with kernel 3.10.0-514+   │
└─────────────────────────────────────────────────────────────┘
```

---

## 18.7 btrfs and zfs — Filesystem-Native Drivers

### btrfs

```bash
# Requires Btrfs filesystem on /var/lib/docker
$ mkfs.btrfs /dev/sdb
$ mount /dev/sdb /var/lib/docker

# Configure Docker
# /etc/docker/daemon.json
{
  "storage-driver": "btrfs"
}
```

```
┌─────────────────────────────────────────────────────────────┐
│  Btrfs uses native subvolumes and snapshots for layers     │
│  ✅ Fast snapshots                                          │
│  ✅ Built-in compression                                   │
│  ❌ Requires Btrfs filesystem                              │
│  ❌ Less mature than ext4/xfs for production               │
└─────────────────────────────────────────────────────────────┘
```

### zfs

```bash
# Requires ZFS on the host
$ zpool create docker-pool /dev/sdb
$ zfs create -o mountpoint=/var/lib/docker docker-pool/docker

# Configure Docker
{
  "storage-driver": "zfs"
}
```

```
┌─────────────────────────────────────────────────────────────┐
│  ZFS uses native datasets and snapshots for layers         │
│  ✅ Data integrity (checksums)                              │
│  ✅ Compression and deduplication                          │
│  ✅ Snapshots and clones                                   │
│  ❌ High memory usage                                      │
│  ❌ Requires ZFS installation                              │
│  ❌ Not in mainline Linux kernel (CDDL license)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 18.8 Choosing the Right Storage Driver

```
┌──────────────────┬──────────────────────────────────────────┐
│ Distribution     │ Recommended Driver                       │
├──────────────────┼──────────────────────────────────────────┤
│ Ubuntu           │ overlay2 (default)                       │
│ Debian           │ overlay2 (default)                       │
│ CentOS/RHEL 8+   │ overlay2 (default)                       │
│ CentOS/RHEL 7    │ overlay2 (with kernel 3.10.0-514+)      │
│ Fedora           │ overlay2 (default)                       │
│ SLES 15          │ overlay2 (default)                       │
│ Amazon Linux 2   │ overlay2 (default)                       │
│ Any with Btrfs   │ btrfs (if Btrfs is the backing FS)      │
│ Any with ZFS     │ zfs (if ZFS is the backing FS)          │
└──────────────────┴──────────────────────────────────────────┘

Short answer: Use overlay2 unless you have a specific reason not to.
```

### Backing Filesystem Requirements

```
┌──────────────────┬──────────────────────────────────────────┐
│ Storage Driver   │ Supported Backing Filesystems            │
├──────────────────┼──────────────────────────────────────────┤
│ overlay2         │ ext4, xfs (with d_type=true)             │
│ aufs             │ ext4, xfs                                │
│ devicemapper     │ direct-lvm (block device)                │
│ btrfs            │ btrfs only                               │
│ zfs              │ zfs only                                 │
│ vfs              │ any filesystem                           │
└──────────────────┴──────────────────────────────────────────┘
```

### Check d_type Support (Required for overlay2 on xfs)

```bash
# xfs must be formatted with d_type=true (ftype=1)
$ xfs_info /var/lib/docker | grep ftype
# ftype=1   ← d_type supported ✅
# ftype=0   ← d_type NOT supported ❌ (reformat with mkfs.xfs -n ftype=1)
```

---

## 18.9 Changing the Storage Driver

```bash
# ⚠️  Changing storage driver removes ALL existing images and containers

# Step 1: Backup important data
$ docker save myapp:1.0 > myapp-backup.tar

# Step 2: Stop Docker
$ sudo systemctl stop docker

# Step 3: Backup existing data (optional)
$ sudo cp -au /var/lib/docker /var/lib/docker.bak

# Step 4: Configure new driver
$ sudo vi /etc/docker/daemon.json
```

```json
{
  "storage-driver": "overlay2"
}
```

```bash
# Step 5: Remove old data (if switching drivers)
$ sudo rm -rf /var/lib/docker

# Step 6: Start Docker
$ sudo systemctl start docker

# Step 7: Verify
$ docker info | grep "Storage Driver"
# Storage Driver: overlay2

# Step 8: Restore images
$ docker load < myapp-backup.tar
```

---

## 18.10 Inspecting Image Layers

```bash
# View layers of an image
$ docker history nginx:latest

# Output:
# IMAGE          CREATED       CREATED BY                                      SIZE
# a6bd71f48f68   2 weeks ago   CMD ["nginx" "-g" "daemon off;"]                0B
# <missing>      2 weeks ago   STOPSIGNAL SIGQUIT                              0B
# <missing>      2 weeks ago   EXPOSE 80                                       0B
# <missing>      2 weeks ago   ENTRYPOINT ["/docker-entrypoint.sh"]            0B
# <missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           4.62kB
# <missing>      2 weeks ago   COPY file:xxx in /docker-entrypoint.d           3.02kB
# <missing>      2 weeks ago   COPY file:xxx in /                              1.62kB
# <missing>      2 weeks ago   RUN /bin/sh -c set -x && ...                    61.1MB
# <missing>      2 weeks ago   /bin/sh -c #(nop) ADD file:xxx in /             77.8MB

# Show full commands (not truncated)
$ docker history --no-trunc nginx:latest

# View layer details with inspect
$ docker inspect nginx:latest --format='{{json .RootFS.Layers}}' | python3 -m json.tool
# [
#     "sha256:abc123...",
#     "sha256:def456...",
#     "sha256:ghi789..."
# ]
```

### Using dive to Analyze Layers

```bash
# Install dive
$ docker run --rm -it \
    -v /var/run/docker.sock:/var/run/docker.sock \
    wagoodman/dive nginx:latest

# dive shows:
#   Left panel: layer-by-layer breakdown
#   Right panel: filesystem tree at each layer
#   Wasted space analysis
#   Image efficiency score
```

---

## 18.11 Storage Driver Performance Comparison

```
┌──────────────────┬────────┬────────┬────────┬────────┬──────┐
│ Operation        │overlay2│ aufs   │ devmap │ btrfs  │ zfs  │
├──────────────────┼────────┼────────┼────────┼────────┼──────┤
│ Container start  │ Fast   │ Fast   │ Slow   │ Fast   │ Fast │
│ Layer sharing    │ Good   │ Good   │ Good   │ Good   │ Good │
│ Write perf       │ Good   │ Good   │ Good   │ Good   │ Med  │
│ Memory usage     │ Low    │ Low    │ Low    │ Low    │ High │
│ Stability        │ High   │ Med    │ Med    │ Med    │ High │
│ Max layers       │ 128    │ 127    │ N/A    │ N/A    │ N/A  │
│ CoW granularity  │ File   │ File   │ Block  │ File   │ Block│
│ Kernel support   │ 4.0+   │ Patch  │ 2.6+   │ 3.18+  │ N/A  │
└──────────────────┴────────┴────────┴────────┴────────┴──────┘

File-level CoW: Copies entire file on first write (even for 1 byte change)
Block-level CoW: Copies only the changed blocks (more efficient for large files)
```

---

## 18.12 Storage Drivers vs Volume Drivers

```
┌──────────────────────────────────────────────────────────────┐
│  Storage Drivers ≠ Volume Drivers                            │
│                                                              │
│  Storage Driver:                                            │
│    Manages image layers and container writable layer        │
│    Data is ephemeral — lost when container is removed       │
│    Examples: overlay2, aufs, devicemapper                   │
│                                                              │
│  Volume Driver:                                             │
│    Manages persistent data (volumes)                        │
│    Data survives container removal                          │
│    Examples: local, nfs, aws-ebs, azure-file               │
│                                                              │
│  Rule of thumb:                                             │
│    Storage driver → container filesystem (temporary)        │
│    Volume driver → persistent data (databases, uploads)     │
│                                                              │
│  For best performance:                                      │
│    Write-heavy workloads → use volumes (bypass CoW)         │
│    Read-heavy workloads → storage driver is fine            │
└──────────────────────────────────────────────────────────────┘
```

---

## 18.13 Common Errors and Troubleshooting

### Error 1: "overlay2: driver not supported"

```bash
# CAUSE: Kernel too old or backing filesystem doesn't support d_type
# Fix: Check kernel version
$ uname -r
# Needs 4.0+ for overlay2

# Check backing filesystem
$ df -T /var/lib/docker
# Filesystem     Type
# /dev/sda1      xfs     ← check ftype

$ xfs_info /var/lib/docker | grep ftype
# ftype=1 ✅  or  ftype=0 ❌
```

### Error 2: "no space left on device" During Build

```bash
# CAUSE: Too many layers or large images filling disk
# Fix: Clean up
$ docker system prune -a
$ docker builder prune

# Check disk usage
$ docker system df
$ df -h /var/lib/docker
```

### Error 3: Slow Container Startup with devicemapper

```bash
# CAUSE: Using loop-lvm mode (default devicemapper)
# Fix: Switch to overlay2
$ docker info | grep "Storage Driver"
# Storage Driver: devicemapper

# Check if using loop-lvm
$ docker info | grep "Data file"
# Data file: /dev/loop0   ← loop-lvm (bad)
# Data file: /dev/sdb     ← direct-lvm (better)

# Best fix: Switch to overlay2
```

---

## Module 18 Summary

- Storage drivers manage image layers and container writable layers using copy-on-write
- **overlay2** is the modern default and recommended for all Linux distributions
- overlay2 uses OverlayFS: lowerdir (read-only image layers) + upperdir (writable) = merged (container view)
- **aufs** was the original driver — deprecated, not in mainline kernel
- **devicemapper** uses block-level thin provisioning — deprecated, removed in Docker 25+
- **btrfs** and **zfs** use native filesystem features — require their respective filesystems
- **vfs** has no CoW — full copy per layer, used only for testing
- Copy-on-write: reads go to image layers, writes copy the file to the writable layer first
- File-level CoW (overlay2, aufs): copies entire file on first modification
- Block-level CoW (devicemapper, zfs): copies only changed blocks
- overlay2 on xfs requires `ftype=1` (d_type support)
- Changing storage driver removes all existing images and containers — backup first
- Use `docker history` and `dive` to inspect image layers
- Storage drivers manage ephemeral container data; volume drivers manage persistent data
- Write-heavy workloads should use volumes to bypass the CoW overhead
- Layer data is stored under `/var/lib/docker/<driver>/`

---

**Previous Module: [Module 17 - Overlay Network Internals](module-17-overlay-networks.md)**

**Next Module: [Module 19 - Raft Consensus & Swarm HA](module-19-raft-consensus.md)**
