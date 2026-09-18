# Module 7: Creating, Viewing, and Managing Files

## 3.1 `touch` — Create Files & Update Timestamps

### Create a new empty file

```bash
$ touch server.log
$ ls -l server.log
-rw-r--r-- 1 devops devops 0 Feb  5 14:00 server.log
```

**Explanation**: `touch` creates an empty file if it doesn't exist. Notice the size is `0` bytes. If the file already exists, it updates the modification timestamp without changing content.

### Create multiple files

```bash
$ touch file1.txt file2.txt file3.txt
$ ls
file1.txt  file2.txt  file3.txt
```

### Update timestamp of existing file

```bash
$ ls -l deploy.sh
-rwxr-xr-x 1 devops devops 245 Jan 20 10:00 deploy.sh

$ touch deploy.sh
$ ls -l deploy.sh
-rwxr-xr-x 1 devops devops 245 Feb  5 14:05 deploy.sh
```

**Explanation**: The file content (245 bytes) didn't change, but the timestamp updated to the current time. Useful for triggering build systems that watch file modification times.

### Set a specific timestamp (`-d`)

```bash
$ touch -d "2026-02-19 10:30:00" report.txt
$ ls -l report.txt
-rw-r--r-- 1 devops devops 0 Feb 19  2026 report.txt

$ stat report.txt | grep Modify
Modify: 2026-02-19 10:30:00.000000000 +0000
```

**Explanation**: `touch -d "YYYY-MM-DD HH:MM:SS"` sets the file's modification timestamp to a specific date and time instead of the current time. The file is created if it doesn't exist.

```bash
# Set to a relative date
$ touch -d "yesterday" file.txt
$ touch -d "2 days ago" file.txt

# Set only the date (time defaults to 00:00:00)
$ touch -d "2026-01-01" new_year.txt
```

**Industry use case**: Testing automation that triggers based on file modification times. For example, a cleanup script deletes files older than 30 days — you can create test files with old timestamps to verify the script works correctly.

**Real-life example**: A log rotation script archives files modified more than 7 days ago. To test it without waiting a week, you create files with backdated timestamps: `touch -d "2025-01-01 00:00:00" test_old.log`, then run the rotation script to confirm it picks up the file.

### Create a file with spaces in the name

```bash
$ touch abc\ def.txt
$ ls -l abc\ def.txt
-rw-r--r-- 1 devops devops 0 Feb  5 14:10 abc def.txt

# Alternative: use quotes
$ touch "abc def.txt"
$ ls
abc def.txt
```

**Explanation**: The backslash `\` escapes the space character, telling the shell to treat it as part of the filename rather than a separator between two arguments. You can also wrap the name in quotes (single or double).

```bash
# Without escaping, touch creates TWO files:
$ touch abc def.txt
$ ls
abc  def.txt

# With escaping, touch creates ONE file:
$ touch abc\ def.txt
$ ls
abc def.txt
```

> **Best practice**: Avoid spaces in filenames on servers. Use hyphens (`-`) or underscores (`_`) instead. Spaces cause issues in scripts and require constant escaping. If you must work with files that have spaces (e.g., files uploaded by users), always quote the filename: `"abc def.txt"`.

**Real-life example**: A user uploads a file called `Q4 Report Final.pdf` to a web server. When writing a script to process uploads, you must handle spaces: `for f in /uploads/*; do process "$f"; done` — the quotes around `$f` are essential.

---

## 3.2 `cat` — Concatenate & Display Files

### Display file contents

```bash
$ cat /etc/hostname
devops-server
```

**Explanation**: `cat` prints the entire file to the terminal. Best for small files.

### Display with line numbers (`-n`)

```bash
$ cat -n /etc/passwd | head -5
     1  root:x:0:0:root:/root:/bin/bash
     2  daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
     3  bin:x:2:2:bin:/bin:/usr/sbin/nologin
     4  sys:x:3:3:sys:/dev:/usr/sbin/nologin
     5  sync:x:4:65534:sync:/bin:/bin/sync
```

**Explanation**: `-n` adds line numbers. Piped to `head -5` to show only the first 5 lines. Each line in `/etc/passwd` represents a user account.

### Concatenate multiple files

```bash
$ cat header.txt body.txt footer.txt > page.html
```

**Explanation**: `cat` reads all three files in order and `>` redirects the combined output into `page.html`. This is the original purpose of `cat` (concatenate).

### Create a file with content (heredoc)

```bash
$ cat > config.yaml << EOF
server:
  port: 8080
  host: 0.0.0.0
database:
  host: localhost
  port: 5432
EOF

$ cat config.yaml
server:
  port: 8080
  host: 0.0.0.0
database:
  host: localhost
  port: 5432
```

**Explanation**: `cat > file << EOF` writes everything until `EOF` into the file. This is a **heredoc** — very common in shell scripts for creating config files.

---

## 3.3 `head` — View Beginning of Files

### Default: first 10 lines

```bash
$ head /var/log/syslog
Feb  5 00:00:01 server CRON[1234]: (root) CMD (test -x /usr/sbin/anacron)
Feb  5 00:05:01 server CRON[1235]: (root) CMD (command -v debian-sa1)
Feb  5 00:10:01 server systemd[1]: Starting Daily apt download activities...
...
```

**Explanation**: `head` shows the first 10 lines by default. Useful for quickly checking log files or CSV headers.

### Specify number of lines (`-n`)

```bash
$ head -n 3 /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
```

**Explanation**: `-n 3` shows only the first 3 lines.

```bash
# Show first 6 lines of a file
$ head -6 /var/log/syslog
Feb  5 00:00:01 server CRON[1234]: (root) CMD (test -x /usr/sbin/anacron)
Feb  5 00:05:01 server CRON[1235]: (root) CMD (command -v debian-sa1)
Feb  5 00:10:01 server systemd[1]: Starting Daily apt download activities...
Feb  5 00:15:01 server CRON[1236]: (root) CMD (command -v debian-sa1)
Feb  5 00:20:01 server systemd[1]: Finished Daily apt download activities.
Feb  5 00:25:01 server CRON[1237]: (root) CMD (command -v debian-sa1)
```

**Explanation**: `head -6` is a shorthand for `head -n 6`. Both show the first 6 lines. The shorthand form is commonly used for quick inspection.

**Industry use case**: `head -6` is used to quickly check CSV headers and the first few data rows, inspect the beginning of log files, or preview config files before editing.

### Show first N bytes (`-c`)

```bash
$ head -c 50 /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:da
```

**Explanation**: `-c 50` shows the first 50 bytes. Useful for inspecting binary file headers or checking file encoding.

---

## 3.4 `tail` — View End of Files

### Default: last 10 lines

```bash
$ tail /var/log/syslog
Feb  5 14:50:01 server systemd[1]: Started Session 45 of user devops.
Feb  5 14:55:01 server CRON[5678]: (root) CMD (command -v debian-sa1)
Feb  5 15:00:01 server nginx[890]: 192.168.1.100 - GET /api/health 200
...
```

**Explanation**: `tail` shows the last 10 lines. The go-to command for checking recent log entries.

### Specify number of lines

```bash
$ tail -n 5 /var/log/auth.log
Feb  5 14:30:22 server sshd[4567]: Accepted publickey for devops from 10.0.0.5
Feb  5 14:30:22 server sshd[4567]: pam_unix(sshd:session): session opened
Feb  5 14:45:10 server sudo: devops : TTY=pts/0 ; PWD=/home/devops ; COMMAND=/bin/systemctl restart nginx
Feb  5 14:45:10 server sudo: pam_unix(sudo:session): session opened
Feb  5 14:50:01 server sshd[4890]: Failed password for invalid user admin from 203.0.113.50
```

**Explanation**: Shows the last 5 authentication log entries. The last line shows a failed login attempt — something you'd investigate in a security audit.

### Show only the last line (`-1`)

```bash
$ tail -1 /var/log/syslog
Feb  5 15:00:01 server nginx[890]: 192.168.1.100 - GET /api/health 200
```

**Explanation**: `tail -1` (shorthand for `tail -n 1`) shows only the very last line of a file. Useful for checking the most recent log entry or the last line of a data file.

```bash
# Get the last line of a CSV (most recent record)
$ tail -1 transactions.csv
2025-02-05,14:59:00,user42,purchase,49.99

# Check the last command in a user's history
$ tail -1 ~/.bash_history
sudo systemctl restart nginx

# Get the latest entry from a sorted file
$ tail -1 /var/log/deploy.log
[2025-02-05 14:45:00] Deployment v2.3.1 completed successfully
```

**Industry use case**: `tail -1` is used in monitoring scripts to check the most recent log entry, in data pipelines to verify the last processed record, and in deployment scripts to confirm the latest deployment status.

**Real-life example**: A health check script runs `tail -1 /var/log/app/health.log` every minute to verify the application is still writing heartbeat entries. If the timestamp is older than 5 minutes, it triggers an alert.

### Follow a file in real-time (`-f`)

```bash
$ tail -f /var/log/nginx/access.log
192.168.1.100 - - [05/Feb/2025:15:01:23 +0000] "GET /api/users HTTP/1.1" 200 1234
192.168.1.101 - - [05/Feb/2025:15:01:24 +0000] "POST /api/login HTTP/1.1" 401 89
192.168.1.100 - - [05/Feb/2025:15:01:25 +0000] "GET /api/health HTTP/1.1" 200 15
^C
```

**Explanation**: `-f` (follow) keeps the file open and displays new lines as they're written. Press `Ctrl+C` to stop. This is one of the most important commands for DevOps — you'll use it constantly to monitor logs during deployments and debugging.

### Follow with retry (`-F`)

```bash
$ tail -F /var/log/app/service.log
```

**Explanation**: `-F` is like `-f` but keeps retrying if the file is rotated (renamed/recreated). Use `-F` for log files that get rotated by `logrotate`.

---

## 3.5 `less` — View Files with Scrolling

`less` is the standard pager for viewing large files. Unlike `cat`, it doesn't dump the entire file at once.

```bash
$ less /var/log/syslog
```

### Navigation shortcuts

| Key | Action |
|-----|--------|
| `Space` / `f` | Page forward |
| `b` | Page backward |
| `g` | Go to beginning |
| `G` | Go to end |
| `/pattern` | Search forward |
| `?pattern` | Search backward |
| `n` | Next search match |
| `N` | Previous search match |
| `q` | Quit |
| `F` | Follow mode (like `tail -f`) |

```bash
# View with line numbers
$ less -N /var/log/syslog

# Search for a pattern immediately
$ less +/ERROR /var/log/syslog

# View multiple files
$ less file1.txt file2.txt
# Use :n for next file, :p for previous file

# Pipe command output to less
$ ps aux | less
$ journalctl | less
```

**Explanation**: `less` is preferred over `more` because it supports backward scrolling. The saying goes: "less is more."

---

## 3.6 `more` — Simple File Pager (Legacy)

```bash
$ more /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
--More--(15%)
```

**Explanation**: `more` only scrolls forward (Space to advance, `q` to quit). Use `less` instead — it does everything `more` does plus backward scrolling and search.

---

## 3.7 `tac` — Reverse File (Last Line First)

```bash
$ cat numbers.txt
1
2
3
4
5

$ tac numbers.txt
5
4
3
2
1
```

### Practical use: view most recent log entries first

```bash
$ tac /var/log/syslog | head -20
# Shows the last 20 lines in reverse order (newest first)

# Reverse a CSV (keep header at top)
$ head -1 data.csv && tac data.csv | head -20
```

---

## 3.8 `rev` — Reverse Characters in Each Line

```bash
$ echo "Hello World" | rev
dlroW olleH

$ echo "/var/log/nginx/access.log" | rev | cut -d/ -f1 | rev
access.log
```

**Explanation**: `rev` reverses each line character by character. The second example is a trick to extract the filename from a path (though `basename` is cleaner).

---

## 3.9 `strings` — Extract Text from Binary Files

```bash
$ strings /usr/bin/ls | head -10
/lib64/ld-linux-x86-64.so.2
libc.so.6
__ctype_toupper_loc
__ctype_tolower_loc

# Find version info in a binary
$ strings /usr/bin/nginx | grep -i version
nginx version: nginx/1.18.0

# Search for URLs or IPs in a binary
$ strings suspicious_file | grep -E "http|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
```

**Explanation**: `strings` extracts printable text from binary files. Useful for finding version info, embedded URLs, or debugging compiled programs.

---


## 3.17 `echo` — Print Text to Terminal

### Basic usage

```bash
$ echo Hello World
Hello World

$ echo "Welcome to Linux"
Welcome to Linux
```

**Explanation**: `echo` prints text (arguments) to the terminal (standard output). It's one of the most frequently used commands — for displaying messages, writing to files, and debugging scripts.

### Print variable values

```bash
$ echo $HOME
/home/devops

$ echo "Current user: $USER on host: $HOSTNAME"
Current user: devops on host: web-server

$ echo "Shell: $SHELL | Path: $PATH"
Shell: /bin/bash | Path: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin
```

**Explanation**: `echo` expands variables inside double quotes. This is how you inspect environment variables and debug scripts.

### Suppress trailing newline (`-n`)

```bash
$ echo -n "Loading..."
Loading...$
```

**Explanation**: `-n` prevents `echo` from adding a newline at the end. Useful in scripts for progress indicators or prompts that stay on the same line.

### Enable escape sequences (`-e`)

```bash
$ echo -e "Line1\nLine2\nLine3"
Line1
Line2
Line3

$ echo -e "Column1\tColumn2\tColumn3"
Column1    Column2    Column3

$ echo -e "\033[32mSUCCESS\033[0m: Deployment complete"
SUCCESS: Deployment complete
```

**Explanation**: `-e` enables interpretation of backslash escapes: `\n` = newline, `\t` = tab, `\033[32m` = green color. Without `-e`, these are printed literally.

### Write text to a file

```bash
$ echo "server_name=production" > config.txt
$ cat config.txt
server_name=production

$ echo "port=8080" >> config.txt
$ cat config.txt
server_name=production
port=8080
```

**Explanation**: `>` creates/overwrites the file, `>>` appends. This is the simplest way to create config files or add lines to existing files from the command line.

**Industry use case**: `echo` is used in shell scripts for logging, user feedback, generating config files, and writing to system files. In CI/CD pipelines, `echo` prints build status, exports variables, and creates deployment manifests.

**Real-life example**: A deployment script uses `echo` to log each step:
```bash
echo "[$(date)] Starting deployment..."
echo "[$(date)] Pulling latest image..."
docker pull myapp:latest
echo "[$(date)] Deployment complete" >> /var/log/deploy.log
```

---

## 3.18 I/O Redirection & Pipes

### Output redirection (`>` and `>>`)

```bash
$ echo "Hello World" > greeting.txt       # Create/overwrite
$ cat greeting.txt
Hello World

$ echo "Welcome to Linux" >> greeting.txt  # Append
$ cat greeting.txt
Hello World
Welcome to Linux
```

**Explanation**: `>` creates or overwrites the file. `>>` appends to the file without erasing existing content.

### Redirect command output to a file

```bash
$ who > users
$ cat users
devops   pts/0        2025-02-05 10:00 (10.0.0.5)
john     pts/1        2025-02-05 11:30 (10.0.0.10)
```

**Explanation**: `who > users` runs the `who` command (which lists logged-in users) and redirects its output into a file called `users` instead of displaying it on screen. If `users` already exists, it is overwritten.

```bash
# Append to the file instead of overwriting
$ who >> users

# Save process list to a file
$ ps aux > running_processes.txt

# Save disk usage to a file
$ df -h > disk_report.txt
```

**Industry use case**: Redirecting command output to files is used for generating reports, creating audit logs, and capturing system state for later analysis. Cron jobs often redirect output to log files for monitoring.

**Real-life example**: A nightly cron job captures who is logged in and saves it for security auditing:
```bash
# In crontab: save logged-in users every hour
0 * * * * who >> /var/log/user_sessions.log
```

### Input redirection (`<`)

```bash
$ wc -l < /etc/passwd
35
```

**Explanation**: `<` feeds the file as input to the command. `wc -l` counts lines — there are 35 user accounts.

### File Descriptors: STDIN, STDOUT, STDERR

Every process in Linux has three standard I/O streams, each identified by a **file descriptor** number:

| FD | Name   | Description                        | Default Destination |
|----|--------|------------------------------------|---------------------|
| `0` | stdin  | Standard input (keyboard input)   | Terminal            |
| `1` | stdout | Standard output (normal output)   | Terminal            |
| `2` | stderr | Standard error (error messages)   | Terminal            |

```bash
# Redirect stdout (fd 1) to a file
$ ls /etc/passwd 1> output.txt
$ cat output.txt
/etc/passwd

# Redirect stderr (fd 2) to a file
$ ls /nonexistent 2> errors.txt
$ cat errors.txt
ls: cannot access '/nonexistent': No such file or directory

# Redirect stdout and stderr to separate files
$ find /etc -name "*.conf" > results.log 2> errors.log
$ cat results.log
/etc/nginx/nginx.conf
/etc/resolv.conf
$ cat errors.log
find: '/etc/ssl/private': Permission denied
```

**Explanation**: By default, both stdout and stderr print to the terminal, which mixes normal output with errors. Separating them lets you process results cleanly while capturing errors for debugging.

### Send error messages to stderr in scripts

```bash
$ echo "Something went wrong" 1>&2
```

**Explanation**: `1>&2` redirects stdout (fd 1) to stderr (fd 2). This is how you write error messages in shell scripts — they go to stderr so they don't pollute normal output that might be piped to another command.

```bash
#!/bin/bash
if [ ! -f "$1" ]; then
    echo "ERROR: File '$1' not found" 1>&2
    exit 1
fi
echo "Processing $1..."    # Normal output goes to stdout
```

**Real-life example**: A deployment script outputs progress to stdout and errors to stderr. The CI/CD system captures them separately — stdout goes to the build log, stderr triggers alerts.

### Error redirection (`2>`)

```bash
$ find /etc -name "*.conf" 2>/dev/null
/etc/nginx/nginx.conf
/etc/resolv.conf
```

**Explanation**: `2>` redirects error messages (stderr) to `/dev/null` (a black hole that discards data). This suppresses "Permission denied" errors that clutter output.

### `/dev/null` — Discard output

```bash
# Discard all output (stdout)
$ ls > /dev/null

# Discard both stdout and stderr
$ command > /dev/null 2>&1
```

**Explanation**: `/dev/null` is a special file that discards everything written to it. `> /dev/null 2>&1` first redirects stdout to `/dev/null`, then redirects stderr (`2>`) to wherever stdout is going (`&1`), which is also `/dev/null`.

**Industry use case**: Cron jobs use this pattern to suppress normal output and only receive email alerts on failures:

```bash
# Crontab entry — discard stdout, only get emailed on errors
0 * * * * /opt/scripts/backup.sh > /dev/null 2>&1

# Or: discard stdout but keep errors
0 * * * * /opt/scripts/backup.sh > /dev/null
```

### Redirect both stdout and stderr

```bash
$ command > output.log 2>&1              # Both to same file
$ command > output.log 2> error.log      # Separate files
$ command &> all.log                     # Shorthand: both to same file
$ command &>> all.log                    # Shorthand: append both to same file
```

**Industry use case**: Production automation separates stdout and stderr into different log files for clean monitoring:

```bash
# Separate normal logs from error logs
$ ./deploy.sh > /var/log/deploy.log 2> /var/log/deploy-errors.log

# Combine everything into one log
$ ./deploy.sh > /var/log/deploy-all.log 2>&1

# Append both stdout and stderr to the same log file
$ ./deploy.sh &>> /var/log/deploy-all.log
```

### Pipes (`|`)

The pipe operator `|` sends the standard output of one command as standard input to the next command. This lets you chain tools together to build powerful one-liners.

```bash
# Count number of files in a directory
$ ls | wc -l
12

# Search for a user in /etc/passwd
$ cat /etc/passwd | grep "devops"
devops:x:1000:1000:DevOps User:/home/devops:/bin/bash

# Chain multiple commands: list → sort → limit
$ ls -la /var/log | sort -k5 -n -r | head -5
-rw-r--r-- 1 root root 4500000 Feb  5 12:00 kern.log
-rw-r--r-- 1 root root 2300000 Feb  5 12:00 syslog
-rw-r----- 1 root adm  1200000 Feb  5 11:55 auth.log
-rw-r--r-- 1 root root  890000 Feb  4 23:59 dpkg.log
-rw-r--r-- 1 root root  450000 Feb  3 23:59 alternatives.log
```

**Explanation**: `|` (pipe) sends the output of one command as input to the next. The first example counts files by piping `ls` output into `wc -l`. The last example lists log files, sorts by size (column 5, numeric, reverse), and shows the top 5 largest. Pipes are fundamental for quick metrics, chaining tools, and filtering logs.

### `tee` — Write to file AND screen

```bash
$ df -h | tee disk_report.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /
tmpfs           3.9G     0  3.9G   0% /dev/shm

$ cat disk_report.txt
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   35G  26% /
tmpfs           3.9G     0  3.9G   0% /dev/shm
```

**Explanation**: `tee` splits output — it displays on screen AND writes to a file simultaneously. Use `tee -a` to append instead of overwrite.

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


## 3.21 `vi` / `vim` — Terminal Text Editor

`vi` is available on virtually every Linux system. `vim` (Vi IMproved) adds syntax highlighting and more features. On servers without a GUI, `vi` is often the only editor available.

### Open a file

```bash
$ vi file.txt
$ vi config.yaml
$ vim /etc/nginx/nginx.conf
```

### Modes

| Mode    | Purpose                | How to Enter           |
|---------|------------------------|------------------------|
| Normal  | Navigate, delete, copy | Press `Esc`            |
| Insert  | Type text              | Press `i`, `a`, or `o` |
| Command | Save, quit, search     | Press `:` from Normal  |

### Essential commands

| Action                  | Keys                |
|-------------------------|---------------------|
| Enter insert mode       | `i`                 |
| Return to normal mode   | `Esc`               |
| Save (write)            | `:w`                |
| Quit                    | `:q`                |
| Save and quit           | `:wq`               |
| Force quit (no save)    | `:q!`               |
| Delete a line           | `dd` (normal mode)  |
| Undo                    | `u` (normal mode)   |
| Search forward          | `/pattern`          |
| Go to line N            | `:N` (e.g., `:25`)  |

### Typical workflow

```bash
$ vim /etc/ssh/sshd_config
# 1. Press i to enter insert mode
# 2. Make your edits
# 3. Press Esc to return to normal mode
# 4. Type :wq and press Enter to save and quit
```

**Explanation**: The key concept is switching between modes. New users often get stuck because pressing keys in normal mode executes commands instead of typing text. Always press `Esc` first if unsure which mode you're in, then `i` to start typing. `vi` is essential for editing configs on servers without a GUI.

---

