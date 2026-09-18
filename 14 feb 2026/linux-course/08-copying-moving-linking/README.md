# Module 8: Copying, Moving, Deleting, and Linking Files

## 3.10 `cp` — Copy Files and Directories

### Copy a file

```bash
$ cp config.yaml config.yaml.bak
$ ls
config.yaml  config.yaml.bak
```

**Explanation**: Creates a copy named `config.yaml.bak`. The original remains unchanged. A common pattern for backing up config files before editing.

### Copy to a directory

```bash
$ cp deploy.sh /opt/scripts/
$ ls /opt/scripts/
deploy.sh
```

**Explanation**: Copies `deploy.sh` into the `/opt/scripts/` directory, keeping the same filename.

### Copy with a new name

```bash
$ cp deploy.sh /opt/scripts/deploy-v2.sh
```

### Copy a directory recursively (`-r`)

```bash
$ cp -r projects/ projects-backup/
$ ls
projects  projects-backup
```

**Explanation**: `-r` (recursive) is required for directories. Without it, `cp` refuses to copy directories.

### Preserve permissions and timestamps (`-p`)

```bash
$ cp -p deploy.sh deploy-copy.sh
$ ls -l deploy.sh deploy-copy.sh
-rwxr-xr-x 1 devops devops 245 Jan 20 10:00 deploy-copy.sh
-rwxr-xr-x 1 devops devops 245 Jan 20 10:00 deploy.sh
```

**Explanation**: `-p` preserves the original file's permissions, ownership, and timestamps. Without it, the copy gets the current timestamp and default permissions.

### Interactive mode — ask before overwriting (`-i`)

```bash
$ cp -i config.yaml config.yaml.bak
cp: overwrite 'config.yaml.bak'? y
```

**Explanation**: `-i` prompts before overwriting existing files. Prevents accidental data loss.

### Verbose mode (`-v`)

```bash
$ cp -rv projects/ /backup/
'projects/' -> '/backup/projects/'
'projects/api/server.js' -> '/backup/projects/api/server.js'
'projects/api/package.json' -> '/backup/projects/api/package.json'
'projects/webapp/index.html' -> '/backup/projects/webapp/index.html'
```

**Explanation**: `-v` (verbose) shows each file as it's copied. Useful for large copy operations.

---

## 3.11 `mv` — Move or Rename Files

### Rename a file

```bash
$ mv old_name.txt new_name.txt
$ ls
new_name.txt
```

**Explanation**: `mv` renames when source and destination are in the same directory.

### Move a file to another directory

```bash
$ mv deploy.sh /opt/scripts/
$ ls /opt/scripts/
deploy.sh
```

**Explanation**: Moves the file — it no longer exists in the original location.

### Move and rename simultaneously

```bash
$ mv config.yaml /etc/myapp/production.yaml
```

### Move multiple files to a directory

```bash
$ mv file1.txt file2.txt file3.txt /backup/
```

### Interactive mode (`-i`)

```bash
$ mv -i new_file.txt /backup/
mv: overwrite '/backup/new_file.txt'? n
```

**Explanation**: `-i` asks before overwriting. Always use this when moving files to directories that might contain files with the same name.

### Force move (`-f`)

```bash
$ mv -f config.yaml /etc/myapp/config.yaml
```

**Explanation**: `-f` overwrites without prompting. Use with caution.

### Create a backup by moving/renaming

```bash
$ mv /home/ubuntu/.bash_logout /home/ubuntu/.bash_logout.backup
$ ls -la /home/ubuntu/.bash_logout*
-rw-r--r-- 1 ubuntu ubuntu 220 Feb  5 10:00 /home/ubuntu/.bash_logout.backup

# Requested variant format
$ mv /home/ubuntu/logout /lo.backup
```

**Explanation**: A common pattern is to rename a file with a `.backup` extension before modifying or replacing it. The original file is preserved under the new name.

```bash
# Backup a config before editing
$ mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
$ vim /etc/nginx/nginx.conf

# Restore if something goes wrong
$ mv /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
```

**Industry use case**: Before making changes to config files on production servers, DevOps engineers create backups using `mv` or `cp`. If the new config breaks the service, the backup can be restored immediately.

**Real-life example**: You need to update the Nginx config on a production server. You run `mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak`, edit the config, test with `nginx -t`, and reload. If the test fails, you restore with `mv /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf`.

---

## 3.12 `rm` — Remove Files and Directories

### Remove a file

```bash
$ rm temp.txt
$ ls temp.txt
ls: cannot access 'temp.txt': No such file or directory
```

**Explanation**: Permanently deletes the file. There is **no trash/recycle bin** in Linux CLI. Deletion is permanent.

### Remove with confirmation (`-i`)

```bash
$ rm -i important.log
rm: remove regular file 'important.log'? y
```

### Force remove files matching a pattern (`-f` with wildcards)

```bash
$ ls
file1.txt  file2.txt  file3.log  notes.txt  deploy.sh

$ rm -f f*
$ ls
notes.txt  deploy.sh
```

**Explanation**: `rm -f f*` force-deletes all files starting with `f` without prompting. The shell expands `f*` to match `file1.txt`, `file2.txt`, and `file3.log` before passing them to `rm`. The `-f` flag suppresses errors for non-existent files and skips confirmation prompts.

> ⚠️ **WARNING**: Always run `ls f*` first to see what will be matched before running `rm -f f*`. Wildcard expansion happens in the shell, not in `rm`, so a typo like `rm -f *` deletes everything in the current directory.

```bash
# Safe workflow: preview before deleting
$ ls f*
file1.txt  file2.txt  file3.log

# Confirm these are the files you want to delete, then:
$ rm -f f*
```

**Real-life example**: After a build process generates temporary files like `fragment_001.tmp`, `fragment_002.tmp`, etc., you clean them up with `rm -f fragment_*.tmp`. Always verify with `ls` first in production environments.

### Remove a directory and its contents (`-r`)

```bash
$ rm -r old-project/
```

**Explanation**: `-r` (recursive) removes the directory and everything inside it.

### Force remove without prompts (`-rf`)

```bash
$ rm -rf build/
```

**Explanation**: `-rf` removes recursively and forcefully without any prompts. The most dangerous command in Linux.

> ⚠️ **WARNING**: `rm -rf /` or `rm -rf *` can destroy your entire system. Always double-check the path before running `rm -rf`. Use `ls` first to verify what you're about to delete.

### Safe practice: verify before deleting

```bash
$ ls build/           # First, see what's there
dist  node_modules  .cache

$ rm -rf build/       # Now delete with confidence
```

---

## 3.13 `file` — Determine File Type

```bash
$ file deploy.sh
deploy.sh: Bourne-Again shell script, ASCII text executable

$ file /usr/bin/python3
/usr/bin/python3: symbolic link to python3.11

$ file image.png
image.png: PNG image data, 1920 x 1080, 8-bit/color RGBA

$ file config.yaml
config.yaml: ASCII text

$ file /dev/null
/dev/null: character special (1/3)
```

**Explanation**: `file` examines file content (not the extension) to determine its type. Linux doesn't rely on file extensions — a file named `data` could be a script, binary, or image. This command tells you what it actually is.

---

## 3.14 `ln` — Create Links

### Symbolic (soft) link

```bash
$ ln -s source.txt link.txt
$ ls -l link.txt
lrwxrwxrwx 1 devops devops 10 Feb  5 15:00 link.txt -> source.txt

$ ln -s /etc/nginx/nginx.conf nginx-config
$ ls -l nginx-config
lrwxrwxrwx 1 devops devops 24 Feb  5 15:00 nginx-config -> /etc/nginx/nginx.conf
```

**Explanation**: A symbolic link is a pointer to another file (like a shortcut). The `l` at the start of permissions indicates a symlink. If the source is deleted, the symlink becomes broken (dangling).

### Hard link

```bash
$ ln source.txt hardlink.txt
$ ls -li source.txt hardlink.txt
1234567 -rw-r--r-- 2 devops devops 100 Feb  5 15:00 hardlink.txt
1234567 -rw-r--r-- 2 devops devops 100 Feb  5 15:00 source.txt
```

**Explanation**: Both files share the same **inode** (1234567) — they point to the same data on disk. The link count is `2`. Deleting one doesn't affect the other. Hard links cannot cross filesystem boundaries and cannot link to directories. Used in deployment patterns like current-release symlinks.

### Symlinks for zero-downtime deployments

```bash
# Application directory structure
$ tree -L 1 /opt/app/
/opt/app/
├── current -> /opt/app/releases/v2/
├── releases/
│   ├── v1/
│   └── v2/
└── shared/

# Deploy a new version
$ ln -sfn /opt/app/releases/v3 /opt/app/current
$ ls -l /opt/app/current
lrwxrwxrwx 1 deploy deploy 22 Feb  5 15:00 /opt/app/current -> /opt/app/releases/v3/
```

**Explanation**: `ln -sfn` creates (or updates) a symlink. `-s` = symbolic, `-f` = force overwrite existing link, `-n` = treat the link as a file (don't follow it if it's a directory link). The `current` symlink always points to the active release.

**Why this works for zero-downtime**: The web server or application is configured to serve from `/opt/app/current`. Switching the symlink is an atomic filesystem operation — there's no moment where the application is partially deployed. If the new version has issues, rollback is instant:

```bash
# Rollback to previous version
$ ln -sfn /opt/app/releases/v2 /opt/app/current

# Verify
$ readlink /opt/app/current
/opt/app/releases/v2/
```

**Real-life example**: Tools like Capistrano, Deployer, and custom deployment scripts use this pattern. Each deployment creates a new directory under `releases/`, then swings the `current` symlink. Old releases are kept for quick rollback and cleaned up after a retention period.

### Symbolic vs Hard Links

| Feature          | Symbolic Link          | Hard Link              |
|------------------|------------------------|------------------------|
| Cross filesystem | Yes                    | No                     |
| Link to directory| Yes                    | No                     |
| Target deleted   | Becomes broken         | Data still accessible  |
| Inode            | Different from target  | Same as target         |
| Common use       | Config shortcuts, bins | Backup, data safety    |

### `cpio` â€” Archive and Extract with File Lists

`cpio` is an archive tool often used with `find` output. It's common in low-level backup/restore workflows and initramfs image creation.

```bash
# Create a cpio archive from all files under current directory
$ find . -type f | cpio -ov > archive.cpio
./notes.txt
./scripts/deploy.sh
./config/app.yaml
3 blocks

# Extract a cpio archive
$ cpio -idv < archive.cpio
notes.txt
scripts/deploy.sh
config/app.yaml
3 blocks
```

**Explanation**:
- `-o` = create archive (copy-out mode)
- `-i` = extract archive (copy-in mode)
- `-v` = verbose output
- `-d` = create directories as needed while extracting

**Real-life example**: During recovery, you can rebuild a subset of files from an old `cpio` archive generated by automation without extracting a full tarball.

---


## 3.19 Wildcards (Globbing)

| Pattern  | Matches                              | Example                    |
|----------|--------------------------------------|----------------------------|
| `*`      | Any number of characters             | `*.log` → all .log files   |
| `?`      | Exactly one character                | `file?.txt` → file1.txt    |
| `[abc]`  | Any one character in the set         | `file[123].txt`            |
| `[a-z]`  | Any one character in the range       | `[a-z]*.conf`              |
| `[!abc]` | Any character NOT in the set         | `file[!0-9].txt`           |

```bash
$ ls *.sh
deploy.sh  backup.sh  monitor.sh

$ ls file?.txt
file1.txt  file2.txt  file3.txt

$ ls config.[yd]*
config.yaml  config.dev

$ rm *.tmp          # Delete all .tmp files
$ cp *.conf /backup/  # Copy all .conf files to backup
```


---

## 3.20 Troubleshooting File Operations

### Scenario: "rm: cannot remove — Directory not empty"

```bash
$ rmdir mydir/
rmdir: failed to remove 'mydir/': Directory not empty

# Check what's inside (including hidden files)
$ ls -la mydir/
.hidden_file  .cache

# Fix: use rm -r instead
$ rm -r mydir/
```

### Scenario: Accidentally deleted a file

```bash
# Linux has no recycle bin. But if the file is still open by a process:
$ sudo lsof | grep deleted | grep "myfile"
java  3456 myapp  5r  REG  8,1  50000  /opt/myapp/myfile.dat (deleted)

# Recover from /proc
$ sudo cp /proc/3456/fd/5 /opt/myapp/myfile.dat.recovered
```

### Scenario: "Argument list too long" with wildcards

```bash
$ rm /tmp/sessions/*
bash: /bin/rm: Argument list too long

# Fix: use find instead
$ find /tmp/sessions -type f -delete

# Or use xargs
$ ls /tmp/sessions | xargs rm -f
```

### Scenario: Find recently modified files (after a deployment)

```bash
# Files modified in the last 10 minutes
$ find /opt/myapp -type f -mmin -10
/opt/myapp/config/app.yaml
/opt/myapp/bin/server

# Files modified today
$ find /opt/myapp -type f -mtime 0 -ls
```

---

