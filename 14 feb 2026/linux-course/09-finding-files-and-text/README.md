# Module 9: Finding Files and Text

## 3.15 `find` — Search for Files

The most powerful file search command. Searches the filesystem in real-time.

### Basic syntax

```bash
find <path> -type <f/d> -name "pattern" -print
```

**Explanation**:
- `<path>` = where to search (e.g., `.`, `/home`, `/etc`)
- `-type f` = files, `-type d` = directories
- `-name` = match by name (case-sensitive)
- `-print` = print matching paths

### Find by name

```bash
$ find /home -name "deploy.sh"
/home/devops/scripts/deploy.sh
/home/devops/projects/deploy.sh

# Find a specific file in current directory
$ find . -type f -name "sample.txt"
./projects/sample.txt
```

**Explanation**: Searches recursively for files matching the name. `.` means current directory.

### Case-insensitive search

```bash
$ find /etc -iname "*.conf"
/etc/nginx/nginx.conf
/etc/ssh/sshd_config
/etc/resolv.conf
/etc/sysctl.conf

# Case-insensitive with type filter
$ find . -iname "sample.txt" -type f
./projects/Sample.txt
./docs/SAMPLE.TXT
```

**Explanation**: `-iname` ignores case. Useful when you're unsure of the exact casing.

### Find by type

```bash
$ find /var/log -type f -name "*.log"     # Files only
/var/log/syslog
/var/log/auth.log
/var/log/kern.log

# Find directories by name
$ find /home/ubuntu -type d -name "demo2"
/home/ubuntu/projects/demo2

$ find /etc -type d -name "nginx"
/etc/nginx
```

**Explanation**: `-type f` = regular files, `-type d` = directories, `-type l` = symbolic links.

### Find by size

```bash
$ find /var/log -type f -size +10M
/var/log/kern.log
/var/log/syslog.1

$ find /tmp -type f -size -1k
/tmp/lock
/tmp/.X0-lock
```

**Explanation**: `+10M` = larger than 10 MB, `-1k` = smaller than 1 KB. Also supports `c` (bytes), `k` (KB), `M` (MB), `G` (GB).

### Find by modification time

```bash
$ find /var/log -type f -mtime -1          # Modified in last 24 hours
/var/log/syslog
/var/log/auth.log

$ find /home -type f -mtime +30            # Modified more than 30 days ago
/home/devops/old-report.txt

$ find /tmp -type f -mmin -60              # Modified in last 60 minutes
/tmp/session_abc123
```

**Explanation**: `-mtime -1` = modified within the last 1 day. `-mtime +30` = modified more than 30 days ago. `-mmin` works in minutes.

### Find by permissions

```bash
$ find /home -type f -perm 777
/home/devops/tmp/insecure_script.sh
```

**Explanation**: Finds files with `777` (read/write/execute for everyone) permissions — a security risk.

### Find empty files and directories

```bash
# Find empty files
$ find /tmp -type f -empty
/tmp/placeholder.txt
/tmp/session_lock
/tmp/.empty_marker

# Find empty directories
$ find /tmp -type d -empty
/tmp/old_cache
/tmp/unused_dir
/tmp/build/artifacts
```

**Explanation**: `-empty` matches files with zero bytes or directories with no contents. Useful for cleanup tasks.

```bash
# Delete all empty files in /tmp
$ find /tmp -type f -empty -delete

# Delete all empty directories in a project
$ find /opt/myapp -type d -empty -delete

# List empty files with details
$ find /home -type f -empty -exec ls -l {} \;
-rw-r--r-- 1 devops devops 0 Feb  5 10:00 /home/devops/placeholder.txt
```

### Find directories modified in last 7 days

```bash
$ find . -mtime -7 -type d
./new-project
./.cache
./downloads
```

### Find files with specific permissions

```bash
$ find ./GFG -perm 664
./GFG/config/settings.yaml
./GFG/data/report.csv
```

**Explanation**: Finds files with exact permission `664` (rw-rw-r--). Useful for auditing file permissions across a project.

### Find and execute a command

```bash
$ find /var/log -name "*.log" -size +5M -exec ls -lh {} \;
-rw-r--r-- 1 root root 12M Feb  5 12:00 /var/log/kern.log
-rw-r--r-- 1 root root 8.5M Feb  5 12:00 /var/log/syslog.1
```

**Explanation**: `-exec` runs a command on each found file. `{}` is replaced by the filename. `\;` terminates the command. This finds log files over 5 MB and shows their details.

```bash
# Find .txt files and search for a pattern inside them (case-insensitive, list filenames)
$ find . -type f -name "*.txt" -exec grep -il "unix" {} \;
./docs/guide.txt
./notes/setup.txt

# Find .txt files and change permissions
$ find /home/ubuntu -type f -name "*.txt" -exec chmod 755 {} \;
```

**Explanation**: Combining `find` with `-exec grep` searches inside found files. Combining with `-exec chmod` applies permission changes in bulk. These patterns are common for locating config files, hunting for secrets, and rotating permissions.

### Find and delete

```bash
# Delete using -exec rm
$ find ./wezva -name "*.txt" -exec rm -rf {} \;

# Delete using -delete (simpler)
$ find /tmp -type f -name "*.tmp" -mtime +7 -delete
```

**Best practice**: Always preview first before deleting:

```bash
# Preview what will be deleted
$ find ./wezva -name "*.txt" -print
./wezva/old_report.txt
./wezva/temp_data.txt

# Then delete once confirmed
$ find ./wezva -name "*.txt" -exec rm -rf {} \;
```

**Explanation**: `-print` shows what `find` matched without modifying anything. Always run with `-print` first to verify the results before using `-exec rm` or `-delete`. This prevents accidental data loss — especially when using wildcards.

### Find with multiple conditions

```bash
$ find /home -type f \( -name "*.log" -o -name "*.tmp" \) -size +1M
/home/devops/app.log
/home/devops/cache.tmp
```

**Explanation**: `-o` means OR. Finds files ending in `.log` OR `.tmp` that are larger than 1 MB. Parentheses must be escaped with `\`.

---

## 3.16 `locate` — Fast File Search (Database-Based)

```bash
$ locate java
/usr/bin/java
/usr/lib/jvm/java-17-openjdk-amd64/bin/java
/usr/share/man/man1/java.1.gz

$ locate nginx.conf
/etc/nginx/nginx.conf
/usr/share/doc/nginx/nginx.conf.example
```

**Explanation**: `locate` searches a pre-built database, making it much faster than `find`. However, newly created files may not appear until the database is updated. Not reliable for real-time searches, but excellent for quick lookups on large systems.

### Update the database

```bash
$ sudo updatedb
```

**Explanation**: Rebuilds the file database. Run this after creating new files if `locate` can't find them.

### `locate` vs `find`

| Feature    | `locate`                    | `find`                      |
|------------|-----------------------------|-----------------------------|
| Speed      | Very fast (database lookup) | Slower (real-time search)   |
| Freshness  | May miss new files          | Always current              |
| Filters    | Name only                   | Name, size, time, perms, etc|
| Install    | May need `mlocate` package  | Always available            |

---

