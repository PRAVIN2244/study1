# Module 7: Package Management

## 7.1 Overview

A **package manager** handles installing, updating, configuring, and removing software. It resolves dependencies automatically.

| Distro Family     | Low-Level Tool | High-Level Tool | Package Format |
|-------------------|----------------|-----------------|----------------|
| Debian/Ubuntu     | `dpkg`         | `apt`           | `.deb`         |
| RHEL/CentOS/Fedora| `rpm`          | `yum` / `dnf`   | `.rpm`         |
| Alpine            | —              | `apk`           | `.apk`         |
| Arch              | —              | `pacman`        | `.pkg.tar.zst` |

---

## 7.2 APT (Debian/Ubuntu)

### Update package index

```bash
$ sudo apt update
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Get:2 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]
Get:3 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [119 kB]
Fetched 229 kB in 2s (115 kB/s)
Reading package lists... Done
Building dependency tree... Done
45 packages can be upgraded. Run 'apt list --upgradable' to see them.
```

**Explanation**: `apt update` downloads the latest package lists from repositories. It does NOT install or upgrade anything — it just refreshes the local database of available packages. Always run this before installing.

### `apt` vs `apt-get`

```bash
# Modern syntax (recommended for interactive use)
$ sudo apt update

# Legacy syntax (still widely used in scripts and Dockerfiles)
$ sudo apt-get update -y
```

**Explanation**: `apt` and `apt-get` do the same thing. `apt` is newer, has a progress bar, and is more user-friendly. `apt-get` is the older command that's still used in scripts and Dockerfiles because its output format is stable and won't change between releases.

```bash
# apt-get with -y flag (auto-confirm all prompts)
$ sudo apt-get update -y
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Get:2 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]
Fetched 110 kB in 1s (110 kB/s)
Reading package lists... Done
```

**Explanation**: The `-y` flag answers "yes" to all prompts automatically. For `apt-get update`, there are no prompts, but `-y` is commonly included as a habit — especially when chaining commands in scripts.

```bash
# Common pattern in Dockerfiles and automation scripts
$ sudo apt-get update -y && sudo apt-get install -y nginx curl wget
```

**Industry use case**: In Dockerfiles, CI/CD pipelines, and automation scripts, `apt-get` with `-y` is preferred because it runs non-interactively. `apt` may show warnings when used in non-interactive contexts.

**Real-life example**: A Dockerfile uses `apt-get` to install dependencies:
```dockerfile
RUN apt-get update -y && apt-get install -y \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

### Install a package

```bash
$ sudo apt install nginx
Reading package lists... Done
Building dependency tree... Done
The following additional packages will be installed:
  libnginx-mod-http-geoip2 nginx-common nginx-core
The following NEW packages will be installed:
  libnginx-mod-http-geoip2 nginx nginx-common nginx-core
0 upgraded, 4 newly installed, 0 to remove and 45 not upgraded.
Need to get 592 kB of archives.
Do you want to continue? [Y/n] y
```

**Explanation**: APT resolves dependencies automatically. It shows what additional packages are needed and asks for confirmation.

```bash
# Install without prompts (for scripts)
$ sudo apt install -y nginx

# Install a specific version
$ sudo apt install nginx=1.18.0-6ubuntu14.4

# Install multiple packages
$ sudo apt install -y nginx curl wget git
```

### Upgrade packages

```bash
# Upgrade all installed packages
$ sudo apt upgrade -y
45 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.

# Upgrade with dependency changes (may install/remove packages)
$ sudo apt full-upgrade -y
```

**Explanation**: `upgrade` installs newer versions but won't remove packages. `full-upgrade` (formerly `dist-upgrade`) handles dependency changes that require installing or removing packages.

### Remove a package

```bash
# Remove package (keep config files)
$ sudo apt remove nginx
The following packages will be REMOVED:
  nginx nginx-core
Do you want to continue? [Y/n] y

# Remove package AND config files
$ sudo apt purge nginx

# Remove unused dependencies
$ sudo apt autoremove -y
```

**Explanation**: `remove` keeps configuration files in case you reinstall. `purge` removes everything. `autoremove` cleans up packages that were installed as dependencies but are no longer needed.

### Search for packages

```bash
$ apt search redis
Sorting... Done
Full Text Search... Done
redis-server/jammy 5:7.0.15-1 amd64
  Persistent key-value database with network interface
redis-tools/jammy 5:7.0.15-1 amd64
  Persistent key-value database - client and utilities
```

### Show package details

```bash
$ apt show nginx
Package: nginx
Version: 1.18.0-6ubuntu14.4
Priority: optional
Section: httpd
Maintainer: Ubuntu Developers
Installed-Size: 44.3 kB
Depends: nginx-core (<< 1.18.0-6ubuntu14.4.1~) | nginx-full ...
Description: small, powerful, scalable web/proxy server
```

### List installed packages

```bash
$ apt list --installed | head -10
Listing... Done
adduser/jammy,now 3.118ubuntu5 all [installed,automatic]
apt/jammy-updates,now 2.4.11 amd64 [installed]
base-files/jammy-updates,now 12ubuntu4.4 amd64 [installed]
bash/jammy,now 5.1-6ubuntu1 amd64 [installed]

# Check if a specific package is installed
$ apt list --installed | grep nginx
nginx/jammy-updates,now 1.18.0-6ubuntu14.4 amd64 [installed]

# List upgradable packages
$ apt list --upgradable
```

### Show package files

```bash
$ dpkg -L nginx
/.
/usr
/usr/sbin
/usr/sbin/nginx
/usr/share/doc/nginx
/etc/nginx
/etc/nginx/nginx.conf
```

**Explanation**: `dpkg -L` lists all files installed by a package. Useful for finding config file locations.

### Find which package owns a file

```bash
$ dpkg -S /usr/sbin/nginx
nginx-core: /usr/sbin/nginx
```

**Explanation**: `dpkg -S` tells you which package installed a specific file.

---

## 7.3 YUM / DNF (RHEL/CentOS/Fedora)

`dnf` is the successor to `yum`. On RHEL 8+ and Fedora, use `dnf`. On RHEL 7/CentOS 7, use `yum`. The syntax is nearly identical.

### Update package index and upgrade

```bash
# Check for updates
$ sudo dnf check-update
Last metadata expiration check: 0:30:00 ago
nginx.x86_64          1.20.1-14.el9          appstream

# Install updates
$ sudo dnf upgrade -y
```

### Install a package

```bash
$ sudo dnf install -y nginx
Dependencies resolved.
================================================================================
 Package          Arch       Version              Repository       Size
================================================================================
Installing:
 nginx            x86_64     1:1.20.1-14.el9      appstream       36 k
Installing dependencies:
 nginx-core       x86_64     1:1.20.1-14.el9      appstream      565 k
 nginx-filesystem noarch     1:1.20.1-14.el9      appstream       8.5 k

Transaction Summary
================================================================================
Install  3 Packages

Total download size: 610 k
Installed size: 1.8 M
Downloading Packages:
...
Complete!
```

### Remove a package

```bash
$ sudo dnf remove nginx
$ sudo dnf autoremove        # Clean unused dependencies
```

### Search and info

```bash
$ dnf search redis
redis.x86_64 : A persistent key-value database

$ dnf info nginx
Name         : nginx
Version      : 1.20.1
Release      : 14.el9
Architecture : x86_64
Size         : 36 k
Source        : nginx-1.20.1-14.el9.src.rpm
Repository   : appstream
Summary      : A high performance web server and reverse proxy server
```

### List installed packages

```bash
$ dnf list installed | head -10
$ dnf list installed | grep nginx
nginx.x86_64          1:1.20.1-14.el9          @appstream
```

### Manage repositories

```bash
# List enabled repos
$ dnf repolist
repo id                  repo name
appstream                Rocky Linux 9 - AppStream
baseos                   Rocky Linux 9 - BaseOS
extras                   Rocky Linux 9 - Extras

# Add a repository (e.g., EPEL)
$ sudo dnf install -y epel-release

# List all repos (including disabled)
$ dnf repolist all
```

### Package groups

```bash
# List available groups
$ dnf group list
Available Groups:
   Development Tools
   Server with GUI
   Minimal Install

# Install a group
$ sudo dnf group install -y "Development Tools"
```

**Explanation**: Package groups bundle related packages. "Development Tools" includes `gcc`, `make`, `git`, etc.

### History and rollback

```bash
$ dnf history
ID     | Command line             | Date and time    | Action(s)      | Altered
-------------------------------------------------------------------------------
     5 | install nginx            | 2025-02-05 10:00 | Install        |    3
     4 | upgrade                  | 2025-02-04 09:00 | Upgrade        |   12

# Undo a transaction
$ sudo dnf history undo 5
```

**Explanation**: `dnf history` tracks all package operations. You can undo any transaction by its ID.

---

## 7.4 `dpkg` and `rpm` — Low-Level Package Tools

### dpkg (Debian/Ubuntu)

```bash
# Install a .deb file
$ sudo dpkg -i package.deb

# List installed packages
$ dpkg -l | grep nginx
ii  nginx  1.18.0-6ubuntu14.4  amd64  small, powerful, scalable web/proxy server

# Show package info
$ dpkg -s nginx

# List files in a package
$ dpkg -L nginx

# Fix broken dependencies after dpkg install
$ sudo apt install -f
```

### rpm (RHEL/CentOS)

```bash
# Install an .rpm file
$ sudo rpm -ivh package.rpm

# List installed packages
$ rpm -qa | grep nginx
nginx-1.20.1-14.el9.x86_64

# Show package info
$ rpm -qi nginx

# List files in a package
$ rpm -ql nginx

# Find which package owns a file
$ rpm -qf /usr/sbin/nginx
nginx-core-1.20.1-14.el9.x86_64
```

---

## 7.5 APK (Alpine Linux)

Alpine is widely used for Docker containers due to its small size (~5 MB base image).

```bash
# Update package index
$ apk update

# Install a package
$ apk add nginx curl

# Remove a package
$ apk del nginx

# Search
$ apk search nginx

# List installed
$ apk info

# Show package info
$ apk info nginx

# Install without cache (for Docker)
$ apk add --no-cache nginx curl
```

**Explanation**: `--no-cache` avoids storing the package index locally, keeping Docker images small. This is the standard pattern in Dockerfiles:

```dockerfile
RUN apk add --no-cache nginx curl
```

---

## 7.6 Managing Repositories

### APT repositories (Debian/Ubuntu)

```bash
$ cat /etc/apt/sources.list
deb http://archive.ubuntu.com/ubuntu jammy main restricted
deb http://archive.ubuntu.com/ubuntu jammy-updates main restricted
deb http://security.ubuntu.com/ubuntu jammy-security main restricted

# Add a third-party repository (example: Docker)
$ sudo apt install -y ca-certificates curl gnupg
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
$ echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
$ sudo apt update
$ sudo apt install -y docker-ce
```

**Explanation**: Third-party repos require adding a GPG key (for package verification) and a sources list entry. Drop-in files in `/etc/apt/sources.list.d/` keep things organized.

### YUM/DNF repositories (RHEL/CentOS)

```bash
$ ls /etc/yum.repos.d/
rocky.repo  rocky-extras.repo  epel.repo

$ cat /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 9
metalink=https://mirrors.fedoraproject.org/metalink?repo=epel-9
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9
```

---

## 7.7 Practical DevOps Scenarios

### Scenario 1: Set up a web server

```bash
# Debian/Ubuntu
$ sudo apt update && sudo apt install -y nginx
$ sudo systemctl enable --now nginx
$ curl -s http://localhost | head -5

# RHEL/CentOS
$ sudo dnf install -y nginx
$ sudo systemctl enable --now nginx
$ sudo firewall-cmd --permanent --add-service=http
$ sudo firewall-cmd --reload
```

### Scenario 2: Install development tools

```bash
# Debian/Ubuntu
$ sudo apt install -y build-essential git curl wget unzip jq

# RHEL/CentOS
$ sudo dnf group install -y "Development Tools"
$ sudo dnf install -y git curl wget unzip jq
```

### Scenario 3: Security updates only

```bash
# Debian/Ubuntu
$ sudo apt update
$ sudo apt upgrade -y --only-upgrade

# RHEL/CentOS
$ sudo dnf upgrade --security -y
```

### Scenario 4: Check for vulnerabilities

```bash
# List packages with available security updates
$ sudo apt list --upgradable 2>/dev/null | grep -i security

# RHEL: check advisories
$ sudo dnf updateinfo list security
```

### Scenario 5: Clean up disk space

```bash
# Debian/Ubuntu
$ sudo apt autoremove -y          # Remove unused dependencies
$ sudo apt autoclean              # Remove old cached packages
$ sudo apt clean                  # Remove all cached packages

# RHEL/CentOS
$ sudo dnf autoremove -y
$ sudo dnf clean all
```

### Scenario 6: Pin a package version (prevent upgrades)

```bash
# Debian/Ubuntu
$ sudo apt-mark hold nginx
nginx set on hold.

$ sudo apt-mark unhold nginx      # Remove the hold

# RHEL/CentOS
$ sudo dnf versionlock add nginx
$ sudo dnf versionlock delete nginx
```

**Explanation**: Pinning prevents a package from being upgraded. Useful when a specific version is required for compatibility.

---


## 7.8 Software Update Lifecycle

### Check what version is installed vs available

```bash
# Debian/Ubuntu
$ apt list --installed 2>/dev/null | grep nginx
nginx/jammy-updates,now 1.18.0-6ubuntu14.4 amd64 [installed]

$ apt policy nginx
nginx:
  Installed: 1.18.0-6ubuntu14.4
  Candidate: 1.18.0-6ubuntu14.5
  Version table:
     1.18.0-6ubuntu14.5 500
        500 http://archive.ubuntu.com/ubuntu jammy-updates/main amd64 Packages
 *** 1.18.0-6ubuntu14.4 100
        100 /var/lib/dpkg/status

# RHEL/CentOS
$ dnf info nginx
Installed Packages
Name         : nginx
Version      : 1.20.1
Release      : 14.el9

Available Packages
Name         : nginx
Version      : 1.20.1
Release      : 16.el9
```

**Explanation**: `apt policy` shows installed vs candidate (available) versions. This tells you if an update is pending.

### See what changed in an update

```bash
# Debian/Ubuntu — view changelog
$ apt changelog nginx
nginx (1.18.0-6ubuntu14.5) jammy-security; urgency=medium
  * SECURITY UPDATE: HTTP/2 rapid reset attack (CVE-2023-44487)
  * debian/patches/CVE-2023-44487.patch: limit number of RST frames

# RHEL/CentOS — view changelog
$ dnf changelog nginx
Changelogs for nginx-1.20.1-16.el9.x86_64
* Wed Jan 15 2025 - Security fix for CVE-2023-44487
```

### Upgrade a single package

```bash
# Debian/Ubuntu
$ sudo apt update && sudo apt install --only-upgrade nginx

# RHEL/CentOS
$ sudo dnf upgrade nginx
```

### Downgrade a package

```bash
# Debian/Ubuntu
$ sudo apt install nginx=1.18.0-6ubuntu14.4

# RHEL/CentOS
$ sudo dnf downgrade nginx-1.20.1-14.el9
```

### Check when packages were last updated

```bash
# Debian/Ubuntu — check dpkg log
$ grep " install \| upgrade " /var/log/dpkg.log | tail -10
2025-02-04 09:00:15 upgrade nginx:amd64 1.18.0-6ubuntu14.3 1.18.0-6ubuntu14.4
2025-02-04 09:00:16 upgrade openssl:amd64 3.0.2-0ubuntu1.12 3.0.2-0ubuntu1.13

# RHEL/CentOS — check dnf history
$ dnf history
ID     | Command line             | Date and time    | Action(s)      | Altered
     5 | upgrade nginx            | 2025-02-04 09:00 | Upgrade        |    1
```

### Verify installed package integrity

```bash
# Debian/Ubuntu — check if files were modified
$ dpkg -V nginx
??5??????   /etc/nginx/nginx.conf

# RHEL/CentOS
$ rpm -V nginx
S.5....T.  c /etc/nginx/nginx.conf
```

**Explanation**: Shows files that differ from the original package. `5` = MD5 checksum changed, `S` = size changed, `T` = timestamp changed. The config file was modified (expected).

---

## 7.9 Troubleshooting Package Issues

### Scenario 1: "Unable to locate package"

```bash
$ sudo apt install mypackage
E: Unable to locate package mypackage

# Step 1: Update package index
$ sudo apt update

# Step 2: Search for the correct name
$ apt search mypackage
$ apt search --names-only mypackage

# Step 3: Check if it's in a different repository
$ apt-cache policy mypackage
# (no output = not in any configured repo)

# Step 4: Add the required repository
$ sudo add-apt-repository ppa:some/ppa
$ sudo apt update
$ sudo apt install mypackage
```

### Scenario 2: Broken dependencies

```bash
$ sudo apt install somepackage
The following packages have unmet dependencies:
 somepackage : Depends: libfoo (>= 2.0) but 1.5 is to be installed

# Fix 1: Let apt resolve it
$ sudo apt install -f

# Fix 2: Force install with dpkg then fix
$ sudo dpkg -i somepackage.deb
$ sudo apt install -f

# Fix 3: Nuclear option — reconfigure
$ sudo dpkg --configure -a
$ sudo apt update
$ sudo apt upgrade -y
```

### Scenario 3: Package lock — another process is using apt

```bash
$ sudo apt update
E: Could not get lock /var/lib/dpkg/lock-frontend

# Step 1: Check what's holding the lock
$ sudo lsof /var/lib/dpkg/lock-frontend
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
apt      5678 root    4uW  REG    8,1        0 1234 /var/lib/dpkg/lock-frontend

# Step 2: Wait for it to finish, or kill it
$ sudo kill 5678

# Step 3: If the process crashed, clean up locks
$ sudo rm /var/lib/dpkg/lock-frontend
$ sudo rm /var/lib/dpkg/lock
$ sudo dpkg --configure -a
```

### Scenario 4: Check what package provides a missing command

```bash
$ somecommand
bash: somecommand: command not found

# Debian/Ubuntu
$ apt-file search somecommand
somepackage: /usr/bin/somecommand

# Or use the command-not-found handler
$ sudo apt install command-not-found
$ update-command-not-found

# RHEL/CentOS
$ dnf provides somecommand
somepackage-1.0-1.el9.x86_64 : Description
Repo        : appstream
Matched from:
Filename    : /usr/bin/somecommand
```

---

## Summary

| Task                  | APT (Debian/Ubuntu)          | DNF/YUM (RHEL/CentOS)       |
|-----------------------|------------------------------|------------------------------|
| Update index          | `apt update`                 | `dnf check-update`          |
| Install               | `apt install -y pkg`         | `dnf install -y pkg`        |
| Remove                | `apt remove pkg`             | `dnf remove pkg`            |
| Purge (+ configs)     | `apt purge pkg`              | —                           |
| Upgrade all           | `apt upgrade -y`             | `dnf upgrade -y`            |
| Search                | `apt search pkg`             | `dnf search pkg`            |
| Info                  | `apt show pkg`               | `dnf info pkg`              |
| List installed        | `apt list --installed`       | `dnf list installed`        |
| Clean cache           | `apt clean`                  | `dnf clean all`             |
| Remove unused deps    | `apt autoremove`             | `dnf autoremove`            |
| Pin version           | `apt-mark hold pkg`          | `dnf versionlock add pkg`   |
| Find file owner       | `dpkg -S /path/file`         | `rpm -qf /path/file`        |

**Next Module**: [08 - Networking](../08-networking/README.md)

---
## 7.12 Building and Installing from Source

When a package isn't available in repositories or you need a custom build:

```bash
# 1. Install build tools
sudo apt install build-essential    # Debian/Ubuntu
sudo yum groupinstall "Development Tools"  # RHEL/CentOS

# 2. Download and extract source
wget https://example.com/tool-1.0.tar.gz
tar -xvzf tool-1.0.tar.gz
cd tool-1.0

# 3. Configure (checks dependencies, prepares Makefile)
./configure
# Or with custom options:
./configure --prefix=/usr/local --enable-ssl

# 4. Compile
make -j$(nproc)    # Use all CPU cores

# 5. Install
sudo make install
```

**Real-world use**: Building Nginx with custom modules, compiling Redis from source for the latest version, or building tools not yet packaged for your distro.

### checkinstall — Create a Package from Source

Instead of `make install`, use `checkinstall` to create a `.deb` or `.rpm` for easy uninstallation:

```bash
sudo apt install checkinstall    # Debian/Ubuntu

# Instead of: sudo make install
sudo checkinstall               # Creates .deb and installs it

# Now you can remove it cleanly:
sudo dpkg -r tool-1.0
```

---

## 7.13 Creating .deb and .rpm Packages

### Creating a .deb Package

```bash
# 1. Create directory structure
mkdir -p myapp/DEBIAN
mkdir -p myapp/usr/local/bin

# 2. Add your binary
cp myapp-binary myapp/usr/local/bin/myapp

# 3. Create control file
cat > myapp/DEBIAN/control << EOF
Package: myapp
Version: 1.0
Architecture: amd64
Maintainer: Your Name <you@example.com>
Description: My custom application
 A brief description of what myapp does.
EOF

# 4. Build the package
dpkg-deb --build myapp
# Creates myapp.deb

# 5. Install
sudo dpkg -i myapp.deb
```

### Creating an .rpm Package

```bash
# Install rpmbuild
sudo yum install rpm-build rpmdevtools

# Set up build tree
rpmdev-setuptree

# Create a .spec file in ~/rpmbuild/SPECS/myapp.spec
# Then build:
rpmbuild -ba ~/rpmbuild/SPECS/myapp.spec
```

### Converting Between Formats with alien

```bash
sudo apt install alien

# Convert .rpm to .deb
sudo alien --to-deb package.rpm

# Convert .deb to .rpm
sudo alien --to-rpm package.deb

# Install converted package
sudo dpkg -i package.deb
```

⚠️ Use `alien` with caution — converted packages may have dependency issues.

---

## 7.12 AppImage — Portable Linux Applications

AppImage files are standalone executables that run on any Linux distro without installation.

```bash
# Download an AppImage
wget https://example.com/myapp.AppImage

# Make it executable
chmod +x myapp.AppImage

# Run it
./myapp.AppImage
```

- No installation needed — just download and run
- No root required
- No dependency management
- Ideal for single-use or portable tools
- Popular for desktop apps (Krita, Kdenlive, etc.)

---

## 7.13 Dependency Troubleshooting

### Check shared library dependencies

```bash
# Show which shared libraries a binary needs
ldd /usr/bin/nginx

# Find missing libraries
ldd /usr/bin/myapp | grep "not found"

# Find which package provides a library
apt-file search libssl.so       # Debian/Ubuntu
yum provides libssl.so          # RHEL/CentOS
```

### Fix broken dependencies

```bash
# Debian/Ubuntu
sudo dpkg -i package.deb
sudo apt install -f              # Fix missing dependencies

# RHEL/CentOS
sudo rpm -ivh package.rpm
sudo yum install ./package.rpm   # Resolves dependencies automatically

# Check dependency tree
apt depends nginx
dnf deplist nginx
pactree nginx                    # Arch Linux
```

### Verify package integrity

```bash
# Debian
debsums nginx                    # Check file integrity (install debsums first)

# RHEL
rpm -V nginx                     # Verify installed files

# Check package signature
rpm --checksig package.rpm
```

**Real-world**: When deploying to production, always verify package signatures and use official repositories to prevent supply chain attacks.

---

## 7.14 Interview Questions — Module 7

**Q1: What is the difference between `apt` and `dpkg`?**

`apt` is a high-level package manager that resolves dependencies automatically, downloads from repositories, and handles upgrades. `dpkg` is the low-level tool that installs/removes individual `.deb` files without dependency resolution. `apt` uses `dpkg` internally.

**Q2: How do you roll back a package update?**

```bash
# Debian/Ubuntu — downgrade to specific version
apt list -a nginx                     # List available versions
sudo apt install nginx=1.18.0-0ubuntu1  # Install specific version
sudo apt-mark hold nginx              # Prevent future upgrades

# RHEL/CentOS — use dnf history
sudo dnf history list nginx
sudo dnf history undo <transaction_id>
```

**Q3: How do you add a third-party repository securely?**

Always verify the GPG key before adding a repository. Import the key, add the repo source, then install:

```bash
# Debian/Ubuntu
curl -fsSL https://example.com/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/example.gpg
echo "deb [signed-by=/usr/share/keyrings/example.gpg] https://repo.example.com stable main" | sudo tee /etc/apt/sources.list.d/example.list
sudo apt update
```

**Q4: What is dependency hell and how do you resolve it?**

Dependency hell occurs when packages require conflicting versions of shared libraries. Solutions: use `apt install -f` to fix broken dependencies, use containers to isolate environments, use Snap/Flatpak for sandboxed packages, or build from source with `checkinstall`.

**Q5: How do you verify package integrity?**

```bash
debsums nginx                         # Verify installed files (Debian)
rpm -V nginx                          # Verify installed files (RHEL)
rpm --checksig package.rpm            # Verify package signature
sha256sum package.deb                 # Manual checksum verification
```

## Summary

| Tool | Distro | Install | Remove | Search | Update |
|------|--------|---------|--------|--------|--------|
| `apt` | Debian/Ubuntu | `apt install` | `apt remove` | `apt search` | `apt update && apt upgrade` |
| `yum`/`dnf` | RHEL/CentOS | `dnf install` | `dnf remove` | `dnf search` | `dnf update` |
| `apk` | Alpine | `apk add` | `apk del` | `apk search` | `apk upgrade` |
| `dpkg` | Debian (low-level) | `dpkg -i` | `dpkg -r` | `dpkg -l` | — |
| `rpm` | RHEL (low-level) | `rpm -ivh` | `rpm -e` | `rpm -qa` | — |

**Next Module**: [08 - Networking](../08-networking/README.md)
