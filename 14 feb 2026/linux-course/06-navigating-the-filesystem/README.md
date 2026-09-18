# Module 2: Filesystem & Navigation

## 2.1 The Linux Filesystem Hierarchy

Linux organizes everything under a single root directory `/`. There are no drive letters (C:, D:) like Windows.

```
/                       ← Root of the entire filesystem
├── bin/                ← Essential user binaries (ls, cp, mv, cat)
├── sbin/               ← System binaries (iptables, fdisk, reboot)
├── etc/                ← Configuration files (nginx.conf, fstab, passwd)
├── home/               ← User home directories (/home/devops, /home/john)
├── root/               ← Home directory of the root user
├── var/                ← Variable data (logs, mail, spool, www)
│   ├── log/            ← System and application logs
│   ├── www/            ← Web server files
│   └── lib/            ← State information (databases, packages)
├── tmp/                ← Temporary files (cleared on reboot)
├── usr/                ← User programs and data
│   ├── bin/            ← User binaries (most commands live here)
│   ├── lib/            ← Libraries
│   ├── local/          ← Locally installed software
│   └── share/          ← Shared data (man pages, docs)
├── opt/                ← Optional/third-party software
├── dev/                ← Device files (disks, terminals, null)
├── proc/               ← Virtual filesystem for process/kernel info
├── sys/                ← Virtual filesystem for hardware/kernel info
├── mnt/                ← Temporary mount points
├── media/              ← Removable media mount points
├── boot/               ← Boot loader files (kernel, grub)
└── lib/                ← Essential shared libraries
```

### Key Directories for DevOps

| Directory   | What You'll Use It For                                    |
|-------------|-----------------------------------------------------------|
| `/etc`      | Editing config files (nginx, ssh, cron, network)          |
| `/var/log`  | Reading logs for troubleshooting                          |
| `/home`     | User workspaces, scripts, SSH keys                        |
| `/tmp`      | Temporary build artifacts, downloads                      |
| `/opt`      | Installing third-party tools (Prometheus, Grafana)        |
| `/proc`     | Inspecting running processes and kernel parameters        |
| `/dev`      | Accessing devices (`/dev/null`, `/dev/sda`)               |

---

## 2.2 `pwd` — Print Working Directory

Shows your current location in the filesystem.

```bash
$ pwd
/home/devops
```

**Explanation**: You are currently in the `devops` user's home directory. Every command you run operates relative to this location unless you specify an absolute path.

```bash
$ cd /var/log
$ pwd
/var/log
```

**Explanation**: After changing to `/var/log`, `pwd` confirms the new location.

---

## 2.3 `ls` — List Directory Contents

The most frequently used command. Lists files and directories.

### Basic usage

```bash
$ ls
Desktop  Documents  Downloads  scripts  projects
```

**Explanation**: Lists files and directories in the current directory. No details, just names.

### Long format (`-l`)

```bash
$ ls -l
total 20
drwxr-xr-x 2 devops devops 4096 Jan 15 10:30 Desktop
drwxr-xr-x 3 devops devops 4096 Jan 20 14:22 Documents
drwxr-xr-x 2 devops devops 4096 Feb  1 09:15 Downloads
-rwxr-xr-x 1 devops devops  245 Feb  5 11:00 deploy.sh
-rw-r--r-- 1 devops devops 1024 Feb  5 11:30 notes.txt
```

**Explanation**: Each column means:

```
-rwxr-xr-x  1  devops  devops  245  Feb 5 11:00  deploy.sh
│           │   │       │       │    │             │
│           │   │       │       │    │             └── Filename
│           │   │       │       │    └── Last modified date/time
│           │   │       │       └── File size in bytes
│           │   │       └── Group owner
│           │   └── User owner
│           └── Number of hard links
└── File type and permissions (d=directory, -=file, l=symlink)
```

### Show hidden files (`-a`)

```bash
$ ls -a
.  ..  .bashrc  .ssh  .profile  Desktop  Documents  deploy.sh
```

**Explanation**: Files starting with `.` are hidden. `-a` reveals them. `.` is the current directory, `..` is the parent directory. `.bashrc` and `.ssh` are important hidden config files.

### Show all with details (`-la`)

```bash
$ ls -la
total 48
drwxr-xr-x 6 devops devops 4096 Feb  5 11:30 .
drwxr-xr-x 4 root   root   4096 Jan 10 08:00 ..
-rw-r--r-- 1 devops devops  220 Jan 10 08:00 .bash_logout
-rw-r--r-- 1 devops devops 3771 Jan 10 08:00 .bashrc
drwx------ 2 devops devops 4096 Jan 12 09:00 .ssh
-rwxr-xr-x 1 devops devops  245 Feb  5 11:00 deploy.sh
-rw-r--r-- 1 devops devops 1024 Feb  5 11:30 notes.txt
```

**Explanation**: Combines `-l` (long format) and `-a` (show hidden). This is the most common way to inspect a directory fully.

### Human-readable sizes (`-lh`)

```bash
$ ls -lh /var/log/
total 12M
-rw-r--r-- 1 root root 2.3M Feb  5 12:00 syslog
-rw-r--r-- 1 root root 4.5M Feb  5 12:00 kern.log
-rw-r----- 1 root adm  1.2M Feb  5 11:55 auth.log
-rw-r--r-- 1 root root 890K Feb  4 23:59 dpkg.log
```

**Explanation**: `-h` converts byte sizes to human-readable format (K, M, G). Much easier to scan than raw byte counts.

### Sort by modification time (`-lt`)

```bash
$ ls -lt
total 20
-rw-r--r-- 1 devops devops 1024 Feb  5 11:30 notes.txt
-rwxr-xr-x 1 devops devops  245 Feb  5 11:00 deploy.sh
drwxr-xr-x 2 devops devops 4096 Feb  1 09:15 Downloads
drwxr-xr-x 3 devops devops 4096 Jan 20 14:22 Documents
drwxr-xr-x 2 devops devops 4096 Jan 15 10:30 Desktop
```

**Explanation**: `-t` sorts by modification time (newest first). Useful for finding recently changed files.

### Reverse sort (`-ltr`)

```bash
$ ls -ltr
total 20
drwxr-xr-x 2 devops devops 4096 Jan 15 10:30 Desktop
drwxr-xr-x 3 devops devops 4096 Jan 20 14:22 Documents
drwxr-xr-x 2 devops devops 4096 Feb  1 09:15 Downloads
-rwxr-xr-x 1 devops devops  245 Feb  5 11:00 deploy.sh
-rw-r--r-- 1 devops devops 1024 Feb  5 11:30 notes.txt
```

**Explanation**: `-r` reverses the sort. Combined with `-t`, the most recently modified file appears last — useful when scrolling through long listings.

### Recursive listing (`-R`)

```bash
$ ls -R projects/
projects/:
webapp  api

projects/webapp:
index.html  style.css

projects/api:
server.js  package.json
```

**Explanation**: `-R` lists all subdirectories recursively. Useful for seeing the full structure of a project.

### Sort by size (`-lS`)

```bash
$ ls -lSh /var/log/
total 12M
-rw-r--r-- 1 root root 4.5M Feb  5 12:00 kern.log
-rw-r--r-- 1 root root 2.3M Feb  5 12:00 syslog
-rw-r----- 1 root adm  1.2M Feb  5 11:55 auth.log
-rw-r--r-- 1 root root 890K Feb  4 23:59 dpkg.log
```

**Explanation**: `-S` sorts by file size (largest first). Combine with `-h` for readable sizes. Useful for finding large log files consuming disk space.

---

## 2.4 `cd` — Change Directory

Navigate between directories.

### Absolute path (starts with `/`)

```bash
$ cd /var/log
$ pwd
/var/log
```

**Explanation**: Absolute paths start from root `/` and work regardless of your current location.

### Relative path (from current location)

```bash
$ pwd
/home/devops
$ cd Documents
$ pwd
/home/devops/Documents
```

**Explanation**: Without a leading `/`, the path is relative to your current directory.

### Go to home directory

```bash
$ cd ~
$ pwd
/home/devops

$ cd
$ pwd
/home/devops
```

**Explanation**: Both `cd ~` and bare `cd` take you to your home directory. `~` is a shorthand for `$HOME`.

### Go up one level

```bash
$ pwd
/home/devops/Documents/projects
$ cd ..
$ pwd
/home/devops/Documents
```

**Explanation**: `..` refers to the parent directory. You can chain them:

```bash
$ cd ../../
$ pwd
/home
```

### Go to previous directory

```bash
$ pwd
/home/devops
$ cd /var/log
$ cd -
/home/devops
```

**Explanation**: `cd -` switches back to the previous directory. Extremely useful when toggling between two locations.

---

## 2.5 `mkdir` — Make Directories

### Create a single directory

```bash
$ mkdir scripts
$ ls
scripts
```

**Explanation**: Creates a directory named `scripts` in the current location.

### Create nested directories (`-p`)

```bash
$ mkdir -p projects/webapp/src/components
$ ls -R projects/
projects/:
webapp

projects/webapp:
src

projects/webapp/src:
components

projects/webapp/src/components:
```

**Explanation**: `-p` creates parent directories as needed. Without `-p`, this would fail because `projects/webapp/src` doesn't exist yet.

### Create multiple directories

```bash
$ mkdir -p {dev,staging,prod}/{logs,config,data}
$ ls -R dev/ staging/ prod/
dev/:
config  data  logs

staging/:
config  data  logs

prod/:
config  data  logs
```

**Explanation**: Brace expansion `{}` creates multiple directories in one command. This creates 3 environments, each with 3 subdirectories — 9 directories total.

---

## 2.6 `rmdir` — Remove Empty Directories

```bash
$ mkdir empty_dir
$ rmdir empty_dir
$ ls
(empty_dir is gone)
```

**Explanation**: `rmdir` only removes **empty** directories. For non-empty directories, use `rm -r` (covered in Module 3).

```bash
$ mkdir -p a/b/c
$ rmdir -p a/b/c
```

**Explanation**: `-p` removes the directory and its empty parents. Removes `c`, then `b`, then `a`.

---

## 2.7 `tree` — Display Directory Tree

```bash
$ tree projects/
projects/
├── api
│   ├── package.json
│   └── server.js
└── webapp
    ├── index.html
    └── style.css

2 directories, 4 files
```

**Explanation**: `tree` shows a visual tree structure. Much clearer than `ls -R` for understanding project layout.

### Limit depth (`-L`)

```bash
$ tree -L 2 /etc/
/etc/
├── apt
│   ├── sources.list
│   └── sources.list.d
├── nginx
│   ├── nginx.conf
│   └── sites-enabled
├── ssh
│   ├── ssh_config
│   └── sshd_config
...
```

**Explanation**: `-L 2` limits the display to 2 levels deep. Essential for large directory trees.

### Show only directories (`-d`)

```bash
$ tree -d -L 2 /var/
/var/
├── cache
│   └── apt
├── lib
│   ├── docker
│   └── dpkg
├── log
│   ├── apt
│   └── nginx
└── tmp

8 directories
```

**Explanation**: `-d` shows only directories, hiding files. Useful for understanding the structure without noise.

### Show hidden files (`-a`)

```bash
$ tree -a /home/devops/
/home/devops/
├── .bash_history
├── .bash_logout
├── .bashrc
├── .profile
├── .ssh
│   ├── authorized_keys
│   ├── id_ed25519
│   ├── id_ed25519.pub
│   └── known_hosts
├── deploy.sh
└── notes.txt

1 directory, 9 files
```

**Explanation**: `-a` shows hidden files and directories (those starting with `.`). Without `-a`, `tree` hides them — just like `ls` without `-a`. This is essential for inspecting user home directories, Git repositories (`.git/`), and config directories.

**Industry use case**: When debugging SSH issues, `tree -a ~/.ssh/` quickly shows all key files and their structure. For Git repos, `tree -a -L 1` reveals `.git/`, `.gitignore`, `.env`, and other hidden config files.

### Show hidden files with sizes

```bash
$ tree -ah --du projects/
projects/
├── [4.0K]  api
│   ├── [ 512]  package.json
│   └── [1.2K]  server.js
└── [4.0K]  webapp
    ├── [ 340]  index.html
    └── [ 890]  style.css

  6.9K used in 2 directories, 4 files
```

**Explanation**: `-a` shows hidden files, `-h` shows human-readable sizes, `--du` shows cumulative directory sizes.

### Install `tree` if missing

```bash
# Debian/Ubuntu
$ sudo apt install tree -y
Reading package lists... Done
Building dependency tree... Done
The following NEW packages will be installed:
  tree
0 upgraded, 1 newly installed, 0 to remove and 45 not upgraded.
Need to get 48.5 kB of archives.
Setting up tree (2.0.2-1) ...

# RHEL/CentOS
$ sudo yum install tree -y

# Verify installation
$ tree --version
tree v2.0.2 (c) 1996 - 2022 by Steve Baker
```

**Explanation**: `tree` is not installed by default on most minimal server installations. Install it with your distribution's package manager. The `-y` flag auto-confirms the installation.

**Real-life example**: You SSH into a new production server and need to understand the application layout. `tree` isn't installed, so you run `sudo apt install tree -y` first, then `tree -L 2 /opt/myapp/` to see the structure.

---

## 2.8 Absolute vs Relative Paths

```
Filesystem:
/
├── home/
│   └── devops/        ← You are here (pwd = /home/devops)
│       ├── scripts/
│       │   └── deploy.sh
│       └── docs/
│           └── readme.md
└── var/
    └── log/
        └── syslog
```

| Type     | Example                        | Description                          |
|----------|--------------------------------|--------------------------------------|
| Absolute | `/home/devops/scripts/deploy.sh` | Full path from root `/`            |
| Relative | `scripts/deploy.sh`            | Path from current directory          |
| Relative | `../docs/readme.md`            | Go up one level, then into `docs/`   |
| Absolute | `/var/log/syslog`              | Always works regardless of location  |

```bash
# These are equivalent when pwd is /home/devops:
$ cat /home/devops/scripts/deploy.sh    # Absolute
$ cat scripts/deploy.sh                  # Relative
$ cat ./scripts/deploy.sh               # Relative (explicit current dir)
```

---

## 2.9 Special Directory Symbols

| Symbol | Meaning                    | Example                    |
|--------|----------------------------|----------------------------|
| `/`    | Root directory             | `cd /`                     |
| `.`    | Current directory          | `./script.sh`              |
| `..`   | Parent directory           | `cd ..`                    |
| `~`    | Home directory             | `cd ~` or `cd ~/scripts`   |
| `-`    | Previous directory         | `cd -`                     |

---

## 2.10 Practical DevOps Scenarios

### Scenario 1: Set up a project structure

```bash
$ mkdir -p myapp/{src,tests,config,docs,scripts}
$ tree myapp/
myapp/
├── config
├── docs
├── scripts
├── src
└── tests

5 directories, 0 files
```

### Scenario 2: Navigate and inspect a server

```bash
$ cd /var/log && ls -lth | head -10     # Check recent log files
$ cd /etc/nginx && ls -la               # Inspect nginx config
$ cd - && pwd                           # Go back to previous location
```

### Scenario 3: Find where a command lives

```bash
$ which docker
/usr/bin/docker

$ ls -la /usr/bin/docker
-rwxr-xr-x 1 root root 89243648 Jan 15 10:00 /usr/bin/docker
```

---

## 2.11 `stat` — Detailed File Information

```bash
$ stat /etc/nginx/nginx.conf
  File: /etc/nginx/nginx.conf
  Size: 1482            Blocks: 8          IO Block: 4096   regular file
Access: (0644/-rw-r--r--)  Uid: (    0/    root)   Gid: (    0/    root)
Access: 2025-02-05 10:00:00.000000000 +0000
Modify: 2025-01-15 08:30:00.000000000 +0000
Change: 2025-01-15 08:30:00.000000000 +0000
 Birth: 2024-12-22 12:00:00.000000000 +0000
```

**Explanation**: `stat` shows everything about a file:
- **Size**: 1482 bytes
- **Access**: permissions in octal (0644) and symbolic (-rw-r--r--)
- **Access time**: last time the file was read
- **Modify time**: last time the file content changed
- **Change time**: last time metadata (permissions, owner) changed
- **Birth**: when the file was created

```bash
# Show only modification time
$ stat -c '%y' /etc/nginx/nginx.conf
2025-01-15 08:30:00.000000000 +0000

# Show only permissions in octal
$ stat -c '%a' /etc/nginx/nginx.conf
644

# Show owner and group
$ stat -c '%U:%G' /etc/nginx/nginx.conf
root:root
```

---

## 2.12 `basename` and `dirname` — Path Manipulation

```bash
$ basename /var/log/nginx/access.log
access.log

$ dirname /var/log/nginx/access.log
/var/log/nginx

$ basename /opt/myapp/deploy-v2.3.tar.gz .tar.gz
deploy-v2.3
```

**Explanation**: `basename` extracts the filename from a path. `dirname` extracts the directory. The second argument to `basename` strips a suffix. These are essential in shell scripts:

```bash
#!/bin/bash
for FILE in /var/log/*.log; do
    NAME=$(basename "$FILE" .log)
    echo "Compressing $NAME..."
    gzip -c "$FILE" > "/backup/${NAME}_$(date +%Y%m%d).log.gz"
done
```

---

## 2.13 `diff` — Compare Files

```bash
$ diff config.yaml config.yaml.bak
3c3
< host: 0.0.0.0
---
> host: localhost
```

**Explanation**: Line 3 changed (`c`). `<` shows the current file, `>` shows the backup. The host was changed from `localhost` to `0.0.0.0`.

```bash
# Side-by-side comparison
$ diff -y config.yaml config.yaml.bak
server:                                         server:
  port: 8080                                      port: 8080
  host: 0.0.0.0                               |    host: localhost
database:                                       database:
  port: 5432                                      port: 5432

# Unified diff (used in patches and git)
$ diff -u config.yaml.bak config.yaml
--- config.yaml.bak    2025-02-04 10:00:00
+++ config.yaml        2025-02-05 11:00:00
@@ -1,5 +1,5 @@
 server:
   port: 8080
-  host: localhost
+  host: 0.0.0.0
 database:
   port: 5432

# Compare directories
$ diff -rq /opt/myapp/v1/ /opt/myapp/v2/
Files /opt/myapp/v1/config.yaml and /opt/myapp/v2/config.yaml differ
Only in /opt/myapp/v2/: new_feature.py
Only in /opt/myapp/v1/: deprecated.py
```

**Explanation**: `-r` = recursive, `-q` = brief (only report whether files differ). `-u` = unified format (what `git diff` uses). Essential for comparing config changes before and after deployments.

---

## 2.14 Troubleshooting: Filesystem Issues

### Scenario 1: "Permission denied" when navigating

```bash
$ cd /root
bash: cd: /root: Permission denied

# Check permissions
$ ls -ld /root
drwx------ 5 root root 4096 Feb  5 10:00 /root

# Only root can enter. Use sudo:
$ sudo ls /root
.bashrc  .profile  scripts

# Or switch to root:
$ sudo -i
root@server:~# cd /root
root@server:~# pwd
/root
```

### Scenario 2: "No space left on device" when creating files

```bash
$ touch /var/log/newfile.log
touch: cannot touch '/var/log/newfile.log': No space left on device

# Step 1: Check disk space
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   50G     0 100% /

# Step 2: Find what's using space
$ sudo du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10
50G     /
25G     /var
15G     /home
8G      /opt

$ sudo du -h --max-depth=1 /var | sort -hr | head -5
25G     /var
20G     /var/log
3G      /var/cache

# Step 3: Find large files
$ sudo find /var/log -type f -size +100M -exec ls -lh {} \;
-rw-r--r-- 1 root root 15G Feb  5 15:00 /var/log/app-debug.log
-rw-r--r-- 1 root root 4G  Feb  5 14:00 /var/log/syslog.1

# Step 4: Clean up
$ sudo truncate -s 0 /var/log/app-debug.log    # Empty the file (keeps it open)
$ sudo apt clean                                 # Clear package cache
$ sudo journalctl --vacuum-size=100M             # Trim systemd logs
```

### Scenario 3: "No such file or directory" but the file exists

```bash
$ cat /var/log/My\ App/error.log
cat: '/var/log/My App/error.log': No such file or directory

# Check for hidden characters or encoding issues
$ ls -la /var/log/ | grep -i app
drwxr-xr-x 2 root root 4096 Feb  5 10:00 My App

# Use tab completion or quotes
$ cat "/var/log/My App/error.log"
# Or escape the space
$ cat /var/log/My\ App/error.log

# Check for broken symlinks
$ ls -la /var/log/app
lrwxrwxrwx 1 root root 20 Feb  5 10:00 /var/log/app -> /mnt/data/app/logs
$ ls -la /mnt/data/app/logs
ls: cannot access '/mnt/data/app/logs': No such file or directory
# The symlink target doesn't exist — mount may be missing

$ mount | grep /mnt/data
# (no output — the mount is missing)
$ sudo mount /dev/sdb1 /mnt/data
```

### Scenario 4: "Too many levels of symbolic links"

```bash
$ cat /etc/myapp/config
cat: /etc/myapp/config: Too many levels of symbolic links

# Circular symlink detected
$ ls -la /etc/myapp/config
lrwxrwxrwx 1 root root 18 Feb  5 10:00 /etc/myapp/config -> /etc/myapp/config.d/main
$ ls -la /etc/myapp/config.d/main
lrwxrwxrwx 1 root root 17 Feb  5 10:00 /etc/myapp/config.d/main -> /etc/myapp/config

# Fix: remove the circular link and create a proper file
$ sudo rm /etc/myapp/config.d/main
$ sudo cp /etc/myapp/config.default /etc/myapp/config.d/main
```

---

## 2.15 Addon Commands

### `ls` — More useful combinations

```bash
# List only directories
$ ls -d */
config/  docs/  scripts/  src/  tests/

# List only files (not directories)
$ ls -p | grep -v /
deploy.sh  notes.txt  config.yaml

# List with inode numbers (useful for hard link detection)
$ ls -i
1234567 deploy.sh  1234568 notes.txt

# One file per line (useful for scripting)
$ ls -1
deploy.sh
notes.txt
config.yaml

# List files sorted by extension
$ ls -X
config.yaml  deploy.sh  notes.txt  README.md
```

### `realpath` — Resolve full absolute path

```bash
$ realpath ../scripts/deploy.sh
/home/devops/scripts/deploy.sh

$ realpath ~/.ssh/config
/home/devops/.ssh/config

# Resolve symlinks
$ realpath /usr/bin/python3
/usr/bin/python3.11
```

### `readlink` — Show symlink target

```bash
$ readlink /usr/bin/python3
python3.11

$ readlink -f /usr/bin/python3    # Full resolved path
/usr/bin/python3.11
```

### `pushd` / `popd` — Directory stack

```bash
$ pwd
/home/devops

$ pushd /var/log
/var/log /home/devops

$ pushd /etc/nginx
/etc/nginx /var/log /home/devops

$ dirs
/etc/nginx /var/log /home/devops

$ popd
/var/log /home/devops

$ popd
/home/devops
```

**Explanation**: `pushd` changes directory and saves the previous one on a stack. `popd` goes back. Useful when jumping between multiple directories.

---

## 2.16 `file` — Identify File Types

The `file` command determines file type by examining content, not the extension:

```bash
$ file /etc/passwd
/etc/passwd: ASCII text

$ file /usr/bin/ls
/usr/bin/ls: ELF 64-bit LSB pie executable, x86-64

$ file image.png
image.png: PNG image data, 1920 x 1080, 8-bit/color RGBA

$ file /dev/sda
/dev/sda: block special (8/0)

$ file script.sh
script.sh: Bourne-Again shell script, ASCII text executable
```

**Flag reference**:

| Flag | Purpose |
|------|---------|
| `-i` | Output MIME type instead of description |
| `-s` | Read block/character special files |
| `-f <list>` | Read filenames from a list file |
| `-L` | Follow symlinks |

```bash
$ file -i document.pdf
document.pdf: application/pdf; charset=binary
```

### File Type Identifiers in `ls -l` Output

The first character of `ls -l` output indicates the file type:

| Symbol | Type | Example |
|--------|------|---------|
| `-` | Regular file | `-rw-r--r-- 1 root root 1234 file.txt` |
| `d` | Directory | `drwxr-xr-x 2 root root 4096 config/` |
| `l` | Symbolic link | `lrwxrwxrwx 1 root root 11 python3 -> python3.11` |
| `c` | Character device | `crw-rw-rw- 1 root root 1, 3 /dev/null` |
| `b` | Block device | `brw-rw---- 1 root disk 8, 0 /dev/sda` |
| `s` | Socket | `srwxrwxrwx 1 root root 0 /var/run/docker.sock` |
| `p` | Named pipe (FIFO) | `prw-r--r-- 1 root root 0 mypipe` |

---

## 2.17 Wildcard Characters (Globbing)

Wildcards allow pattern matching for file and directory names:

| Wildcard | Matches | Example |
|----------|---------|---------|
| `*` | Zero or more characters | `ls *.log` — all `.log` files |
| `?` | Exactly one character | `ls file?.txt` — `file1.txt`, `fileA.txt` |
| `[abc]` | Any one of the listed characters | `ls file[123].txt` — `file1.txt`, `file2.txt` |
| `[a-z]` | Any character in the range | `ls [a-z]*` — files starting with lowercase |
| `[!abc]` | Any character NOT listed | `ls file[!0-9].txt` — non-numeric suffix |
| `{a,b,c}` | Brace expansion (not a glob) | `mkdir {dev,staging,prod}` |

```bash
# List all .conf files in /etc
$ ls /etc/*.conf

# List files with exactly 3-character names
$ ls ???

# Copy all Python files
$ cp *.py /backup/

# Remove all .tmp files (with confirmation)
$ rm -i *.tmp

# Brace expansion — create multiple directories
$ mkdir -p /app/{logs,config,data}

# Combine wildcards
$ ls /var/log/syslog*
/var/log/syslog  /var/log/syslog.1  /var/log/syslog.2.gz
```

---

## 2.18 Command Chaining

### Semicolon (`;`) — Sequential execution

Commands run one after another regardless of success or failure:

```bash
$ who ; date ; whoami
```

### Logical AND (`&&`) — Run next only if previous succeeds

```bash
$ mkdir /app && cd /app && echo "Directory created"
# If mkdir fails, cd and echo do NOT run
```

### Logical OR (`||`) — Run next only if previous fails

```bash
$ cd /nonexistent || echo "Directory not found"
# echo runs because cd failed
```

### Combined pattern — common in production

```bash
$ sudo apt update && sudo apt upgrade -y || echo "Update failed"
```

**Real-world**: Always use `&&` in scripts and CI/CD pipelines. Using `;` masks failures — a command can fail silently and the script continues with corrupted state.

---

## 2.19 Interview Questions — Module 2

**Q1: What is the Filesystem Hierarchy Standard (FHS)?**

FHS defines the standard directory structure in Linux. Key directories: `/bin` (user binaries), `/etc` (configs), `/var` (variable data/logs), `/home` (user homes), `/tmp` (temporary files), `/proc` (virtual process info), `/dev` (device files).

**Q2: What is the difference between absolute and relative paths?**

Absolute paths start from root `/` (e.g., `/var/log/syslog`). Relative paths start from the current directory (e.g., `../log/syslog`). Absolute paths are unambiguous; relative paths depend on `pwd`.

**Q3: What does `ls -lah` show and what does each flag do?**

- `-l` — Long format (permissions, owner, size, date)
- `-a` — Show hidden files (starting with `.`)
- `-h` — Human-readable sizes (KB, MB, GB instead of bytes)

**Q4: How do you find what type a file is without relying on its extension?**

Use `file <filename>`. It examines the file's content (magic bytes) to determine type. Example: `file script` might output `Bourne-Again shell script, ASCII text executable` even without a `.sh` extension.

**Q5: What is the difference between `rmdir` and `rm -r`?**

`rmdir` removes only empty directories and fails if the directory contains files. `rm -r` removes directories and all their contents recursively. Use `rm -ri` for interactive confirmation on each file.

---

## Summary

| Command    | Purpose                          | Common Flags              |
|------------|----------------------------------|---------------------------|
| `pwd`      | Print current directory          | —                         |
| `ls`       | List directory contents          | `-la`, `-lh`, `-lt`, `-R` |
| `cd`       | Change directory                 | `~`, `..`, `-`            |
| `mkdir`    | Create directories               | `-p` (parents)            |
| `rmdir`    | Remove empty directories         | `-p`                      |
| `tree`     | Visual directory tree            | `-L`, `-d`, `-a`          |
| `stat`     | Detailed file info               | `-c` (custom format)      |
| `basename` | Extract filename from path       | —                         |
| `dirname`  | Extract directory from path      | —                         |
| `diff`     | Compare files/directories        | `-u`, `-y`, `-rq`         |

**Next Module**: [03 - File Operations](../03-file-operations/README.md)

---
