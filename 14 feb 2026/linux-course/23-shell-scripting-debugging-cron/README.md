# Module 23: Shell Scripting — Error Handling, Debugging, and Cron

## 11.6 Error Handling

### Exit codes

```bash
#!/bin/bash

# Exit on any error
set -e

# Exit on undefined variables
set -u

# Fail on pipe errors
set -o pipefail

# Common combination
set -euo pipefail
```

**Explanation**:
- `set -e` — script exits immediately if any command fails (non-zero exit code)
- `set -u` — treat unset variables as errors
- `set -o pipefail` — a pipeline fails if any command in it fails (not just the last one)

### Trap errors

```bash
#!/bin/bash
set -euo pipefail

cleanup() {
    echo "Cleaning up temporary files..."
    rm -f /tmp/deploy_*.tmp
}

# Run cleanup on exit (success or failure)
trap cleanup EXIT

# Run on error specifically
trap 'echo "ERROR on line $LINENO"; exit 1' ERR

echo "Starting deployment..."
cp build.tar.gz /tmp/deploy_build.tmp
tar xzf /tmp/deploy_build.tmp -C /opt/myapp/
echo "Deployment complete!"
```

**Explanation**: `trap` registers a function to run when a signal is received. `EXIT` runs on any exit. `ERR` runs on errors. `$LINENO` gives the line number where the error occurred.

### Check command success

```bash
#!/bin/bash

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing..."
    sudo apt install -y docker.io
fi

if ! docker info &> /dev/null; then
    echo "Docker daemon is not running"
    exit 1
fi

echo "Docker is ready"
```

---


## 11.8 Cron — Scheduled Tasks

### Crontab format

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * * command_to_run
```

### Edit crontab

```bash
$ crontab -e
```

### Common cron schedules

```bash
# Every minute (with output redirected to log)
* * * * * /opt/scripts/hello.sh >> /var/log/hello.log 2>&1

# Every 5 minutes
*/5 * * * * /opt/scripts/monitor.sh

# Every hour at minute 0
0 * * * * /opt/scripts/hourly_report.sh

# Every day at 2:30 AM
30 2 * * * /opt/scripts/backup.sh

# Every Monday at 9:00 AM
0 9 * * 1 /opt/scripts/weekly_report.sh

# Every 1st of the month at midnight
0 0 1 * * /opt/scripts/monthly_cleanup.sh

# Every weekday at 6:00 PM
0 18 * * 1-5 /opt/scripts/daily_summary.sh

# Every 15 minutes during business hours
*/15 9-17 * * 1-5 /opt/scripts/business_check.sh
```

### View current crontab

```bash
$ crontab -l
*/5 * * * * /opt/scripts/monitor.sh >> /var/log/monitor.log 2>&1
30 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### Cron best practices

```bash
# Always redirect output to a log file
*/5 * * * * /opt/scripts/monitor.sh >> /var/log/monitor.log 2>&1

# Use full paths (cron has a minimal PATH)
0 2 * * * /usr/bin/python3 /opt/scripts/cleanup.py

# Use a lock file to prevent overlapping runs
* * * * * /usr/bin/flock -n /tmp/job.lock /opt/scripts/long_job.sh
```

### System-wide cron

```bash
$ ls /etc/cron.d/
$ ls /etc/cron.daily/
$ ls /etc/cron.hourly/
$ ls /etc/cron.weekly/
$ ls /etc/cron.monthly/
```

**Explanation**: Drop scripts into these directories for automatic scheduling. Scripts in `cron.daily/` run once per day, etc.

---

## 11.9 Practical Scripts

### Script 1: Server Health Check

```bash
#!/bin/bash
set -euo pipefail

LOG_FILE="/var/log/health_check.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_disk() {
    local USAGE
    USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$USAGE" -gt 90 ]; then
        log "CRITICAL: Disk usage at ${USAGE}%"
        return 1
    elif [ "$USAGE" -gt 70 ]; then
        log "WARNING: Disk usage at ${USAGE}%"
    else
        log "OK: Disk usage at ${USAGE}%"
    fi
}

check_memory() {
    local USAGE
    USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
    if [ "$USAGE" -gt 90 ]; then
        log "CRITICAL: Memory usage at ${USAGE}%"
        return 1
    else
        log "OK: Memory usage at ${USAGE}%"
    fi
}

check_service() {
    local SERVICE="$1"
    if systemctl is-active --quiet "$SERVICE"; then
        log "OK: $SERVICE is running"
    else
        log "CRITICAL: $SERVICE is NOT running"
        return 1
    fi
}

log "=== Health Check Started ==="
check_disk
check_memory
check_service nginx
check_service postgresql
log "=== Health Check Complete ==="
```

### Script 2: Log Rotation & Cleanup

```bash
#!/bin/bash
set -euo pipefail

LOG_DIR="/var/log/myapp"
MAX_AGE_DAYS=30
MAX_SIZE_MB=100

echo "Starting log cleanup at $(date)"

# Compress logs older than 1 day
find "$LOG_DIR" -name "*.log" -mtime +1 -exec gzip {} \;

# Delete compressed logs older than MAX_AGE_DAYS
find "$LOG_DIR" -name "*.log.gz" -mtime +$MAX_AGE_DAYS -delete

# Delete any single file larger than MAX_SIZE_MB
find "$LOG_DIR" -name "*.log" -size +${MAX_SIZE_MB}M -exec truncate -s 0 {} \;

echo "Cleanup complete. Current usage:"
du -sh "$LOG_DIR"
```

### Script 3: Deployment Script

```bash
#!/bin/bash
set -euo pipefail

APP_NAME="myapp"
DEPLOY_DIR="/opt/$APP_NAME"
BACKUP_DIR="/opt/backups"
ARTIFACT="$1"

log() { echo "[$(date '+%H:%M:%S')] $1"; }

# Validate input
if [ -z "${ARTIFACT:-}" ]; then
    echo "Usage: $0 <artifact.tar.gz>"
    exit 1
fi

if [ ! -f "$ARTIFACT" ]; then
    echo "Artifact not found: $ARTIFACT"
    exit 1
fi

# Backup current version
log "Backing up current version..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar czf "$BACKUP_DIR/${APP_NAME}_${TIMESTAMP}.tar.gz" -C "$DEPLOY_DIR" . 2>/dev/null || true

# Deploy new version
log "Deploying new version..."
tar xzf "$ARTIFACT" -C "$DEPLOY_DIR"

# Restart service
log "Restarting service..."
sudo systemctl restart "$APP_NAME"

# Health check
log "Running health check..."
sleep 5
if curl -sf http://localhost:8080/health > /dev/null; then
    log "Deployment successful!"
else
    log "Health check failed! Rolling back..."
    tar xzf "$BACKUP_DIR/${APP_NAME}_${TIMESTAMP}.tar.gz" -C "$DEPLOY_DIR"
    sudo systemctl restart "$APP_NAME"
    log "Rollback complete"
    exit 1
fi
```

---

## 11.10 Debugging Scripts

```bash
# Run with debug output
$ bash -x script.sh
+ echo 'Starting deployment...'
Starting deployment...
+ cp build.tar.gz /tmp/deploy_build.tmp
+ tar xzf /tmp/deploy_build.tmp -C /opt/myapp/

# Enable debug in specific sections
#!/bin/bash
set -x          # Enable debug
some_commands
set +x          # Disable debug

# Check syntax without running
$ bash -n script.sh
```

**Explanation**: `-x` prints each command before executing it (with `+` prefix). Invaluable for debugging. `-n` checks for syntax errors without executing.

---

## 11.11 Common Script Patterns

### Health check script

```bash
#!/bin/bash
# health_check.sh — Check if services are running and responding

SERVICES=("nginx" "postgresql" "redis-server")
ENDPOINTS=("http://localhost:80" "http://localhost:8080/health")
FAILED=0

echo "=== Service Status ==="
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc"; then
        echo "[OK]   $svc is running"
    else
        echo "[FAIL] $svc is NOT running"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== Endpoint Checks ==="
for url in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$url" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "[OK]   $url -> $HTTP_CODE"
    else
        echo "[FAIL] $url -> $HTTP_CODE"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== System Resources ==="
echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory:   $(free -h | awk '/Mem/ {printf "%s used / %s total (%s available)", $3, $2, $7}')"
echo "Disk:     $(df -h / | awk 'NR==2 {printf "%s used / %s total (%s)", $3, $2, $5}')"

exit $FAILED
```

### Log rotation script

```bash
#!/bin/bash
# rotate_logs.sh — Rotate application logs older than 7 days

LOG_DIR="/var/log/myapp"
MAX_AGE=7
ARCHIVE_DIR="/var/log/myapp/archive"

mkdir -p "$ARCHIVE_DIR"

find "$LOG_DIR" -maxdepth 1 -name "*.log" -mtime +$MAX_AGE | while read -r logfile; do
    BASENAME=$(basename "$logfile")
    DATESTAMP=$(date -r "$logfile" '+%Y%m%d')
    gzip -c "$logfile" > "$ARCHIVE_DIR/${BASENAME}.${DATESTAMP}.gz"
    truncate -s 0 "$logfile"
    echo "Rotated: $BASENAME"
done

# Clean archives older than 30 days
find "$ARCHIVE_DIR" -name "*.gz" -mtime +30 -delete

echo "Done. Archive size: $(du -sh "$ARCHIVE_DIR" | awk '{print $1}')"
```

### Disk space alert script

```bash
#!/bin/bash
# disk_alert.sh — Alert when any filesystem exceeds threshold

THRESHOLD=85
ALERT_EMAIL="admin@company.com"

df -h --output=pcent,target | tail -n +2 | while read -r usage mount; do
    PERCENT=${usage%\%}
    if [ "$PERCENT" -gt "$THRESHOLD" ]; then
        echo "WARNING: $mount is at ${PERCENT}% (threshold: ${THRESHOLD}%)"
        # Uncomment to send email:
        # echo "$mount is at ${PERCENT}%" | mail -s "Disk Alert: $mount" "$ALERT_EMAIL"
    fi
done
```

### Backup script with retention

```bash
#!/bin/bash
# backup.sh — Backup with date stamp and retention

set -euo pipefail

BACKUP_DIR="/backup"
SOURCE="/opt/myapp/data"
RETENTION_DAYS=14
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/myapp_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)"
tar czf "$BACKUP_FILE" -C "$(dirname "$SOURCE")" "$(basename "$SOURCE")"
echo "Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | awk '{print $1}'))"

# Clean old backups
DELETED=$(find "$BACKUP_DIR" -name "myapp_*.tar.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo "Cleaned $DELETED backups older than $RETENTION_DAYS days"
```

---

## 11.12 Troubleshooting Scripts

### Common error: "command not found" in cron

```bash
# Cron uses a minimal PATH. Always use full paths:
# BAD
* * * * * docker ps > /tmp/containers.log

# GOOD
* * * * * /usr/bin/docker ps > /tmp/containers.log 2>&1

# Or set PATH at the top of crontab
$ crontab -e
PATH=/usr/local/bin:/usr/bin:/bin
* * * * * docker ps > /tmp/containers.log 2>&1
```

### Common error: "unexpected end of file"

```bash
$ bash script.sh
script.sh: line 25: syntax error: unexpected end of file

# Usually means a missing `fi`, `done`, or `esac`
# Check with syntax check:
$ bash -n script.sh
script.sh: line 25: syntax error: unexpected end of file

# Count opening vs closing keywords:
$ grep -c "if\b" script.sh
3
$ grep -c "fi\b" script.sh
2
# Missing one `fi`
```

### Common error: "bad substitution"

```bash
$ bash script.sh
script.sh: line 5: ${}: bad substitution

# Usually caused by:
# 1. Running a bash script with sh: use `bash script.sh` not `sh script.sh`
# 2. Typo in variable name: ${VARAIBLE} instead of ${VARIABLE}
# 3. Missing variable name: ${} is empty
```

### Common error: script works manually but fails in cron

```bash
# Cron doesn't load your .bashrc or .profile
# Add environment setup to the script:
#!/bin/bash
source /home/devops/.bashrc
# Or export needed variables:
export PATH="/usr/local/bin:$PATH"
export HOME="/home/devops"

# Also redirect output to see errors:
* * * * * /opt/scripts/job.sh >> /var/log/job.log 2>&1
```

### Useful debugging one-liner

```bash
# Add to any script for instant debugging
trap 'echo "ERROR at line $LINENO: command \"$BASH_COMMAND\" failed with exit code $?"' ERR
```

---

## 11.13 Additional Shell Utility Commands (Requested Set)

### Session and command helpers

```bash
$ alias ll="ls -la"
$ unalias ll
$ watch ls
$ watch df -h
$ timeout 5 command
$ yes
$ yes | rm file
$ yes | apt install package
```

**Purpose**:
- `alias`/`unalias`: shortcuts for repetitive commands
- `watch`: rerun command at interval for live monitoring
- `timeout`: stop long-running command after N seconds
- `yes`: auto-answer prompts

### Arithmetic and sequence helpers

```bash
$ expr 1 + 1
2

$ seq 10
1
2
...
10

$ seq 1 2 10
1
3
5
7
9
```

### Input/output helpers

```bash
$ printf "hello\n"
hello

$ printf "%d\n" 10
10

$ read variable
hello
$ echo $variable
hello
```

### Test and shell builtins

```bash
$ test -f file
$ test -d directory
$ test -e file
$ true
$ false
$ :
```

**Purpose**: Conditional checks and no-op/boolean primitives for scripting logic.

### Flow-control builtins (inside scripts/loops)

```bash
break
continue
return
shift
```

**Use case**: Control loop/function behavior and positional argument handling.

### Environment inspection shortcuts

```bash
$ printenv
$ env | sort
$ env | grep HOME
HOME=/home/devops
```

### History shortcuts

```bash
$ history
$ history | grep ssh
$ !!
$ !100
```

**Use case**: Quickly rerun previous commands during troubleshooting/deployments.

## Summary

| Concept        | Key Syntax                                    |
|----------------|-----------------------------------------------|
| Variables      | `NAME="value"`, `$NAME`, `${NAME}`            |
| Arguments      | `$1`, `$2`, `$@`, `$#`, `$?`                  |
| If/else        | `if [[ condition ]]; then ... fi`             |
| For loop       | `for x in list; do ... done`                  |
| While loop     | `while [[ condition ]]; do ... done`          |
| Case           | `case "$var" in pattern) ... ;; esac`         |
| Functions      | `func_name() { ... }`, `local VAR`           |
| Arrays         | `ARR=("a" "b")`, `${ARR[@]}`, `${#ARR[@]}`   |
| Error handling | `set -euo pipefail`, `trap`                   |
| Cron           | `crontab -e`, `* * * * * command`             |
| Debugging      | `bash -x script.sh`, `set -x`                |

**Next Module**: [12 - Advanced DevOps Topics](../12-advanced-devops/README.md)

---

## 11.16 Script Debugging

### Debug modes

```bash
# Run entire script with trace (shows each command before execution)
bash -x script.sh

# Syntax check without executing
bash -n script.sh

# Verbose mode (print lines as read)
bash -v script.sh
```

### Enable debugging inside a script

```bash
#!/bin/bash
set -x          # Turn on debugging
echo "This will show step-by-step"
set +x          # Turn off debugging
echo "This won't show trace"
```

### Enhanced trace output with PS4

```bash
#!/bin/bash
export PS4='+ ${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]}() : '
set -x
echo "Debugging with file and line info"
```

### Using shellcheck for static analysis

```bash
# Install shellcheck
sudo apt install shellcheck

# Check a script for common issues
shellcheck script.sh

# Example issues shellcheck catches:
# - Unquoted variables
# - Missing shebang
# - Useless use of cat
# - Word splitting bugs
```

### Error trapping

```bash
#!/bin/bash
set -euo pipefail

trap 'echo "Error at line $LINENO: $BASH_COMMAND"' ERR
trap 'echo "Script exiting with code $?"' EXIT

echo "Running risky command..."
false    # This will trigger the ERR trap
echo "This line won't execute"
```

---


## 11.18 Real-World Script Examples

### Website Health Check

```bash
#!/bin/bash
set -euo pipefail

URL="https://example.com"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

if [ "$STATUS" -ne 200 ]; then
    echo "$(date): Website down! HTTP $STATUS" | mail -s "Site Down Alert" admin@example.com
    echo "ALERT: $URL returned $STATUS"
else
    echo "OK: $URL is healthy (HTTP $STATUS)"
fi
```

### Disk Usage Alert

```bash
#!/bin/bash
set -euo pipefail

THRESHOLD=80
USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "$(date): Disk usage at ${USAGE}% (threshold: ${THRESHOLD}%)" \
        | mail -s "Disk Alert" admin@example.com
fi
```

### Log Cleanup Script

```bash
#!/bin/bash
set -euo pipefail

LOG_DIR="/var/log"
DAYS=30

echo "$(date): Cleaning logs older than $DAYS days in $LOG_DIR"
find "$LOG_DIR" -name "*.gz" -mtime +$DAYS -delete
find "$LOG_DIR" -name "*.log.*" -mtime +$DAYS -delete
echo "$(date): Cleanup complete"
```

### S3 Backup with Rotation

```bash
#!/bin/bash
set -euo pipefail

DATE=$(date +%F)
BACKUP_FILE="/tmp/backup-${DATE}.tar.gz"

tar -czf "$BACKUP_FILE" /var/www /etc/nginx
aws s3 cp "$BACKUP_FILE" s3://mybucket/backups/
rm -f "$BACKUP_FILE"

# Remove backups older than 30 days from S3
aws s3 ls s3://mybucket/backups/ | while read -r line; do
    FILE_DATE=$(echo "$line" | awk '{print $1}')
    FILE_NAME=$(echo "$line" | awk '{print $4}')
    if [[ $(date -d "$FILE_DATE" +%s) -lt $(date -d "-30 days" +%s) ]]; then
        aws s3 rm "s3://mybucket/backups/$FILE_NAME"
    fi
done
```

---

## 11.19 Interview Questions — Module 11

**Q1: What does `set -euo pipefail` do and why is it important?**

- `set -e` — Exit immediately if any command fails
- `set -u` — Treat unset variables as errors
- `set -o pipefail` — Pipeline fails if any command in the pipe fails (not just the last)

Without these, scripts continue silently after errors, leading to corrupted state in production.

**Q2: What is the difference between `$@` and `$*`?**

Both expand to all positional parameters. `"$@"` preserves each argument as a separate word (correct for iteration). `"$*"` joins all arguments into a single string. Always use `"$@"` in loops.

**Q3: How do you handle errors and cleanup in shell scripts?**

```bash
#!/bin/bash
set -euo pipefail
trap 'echo "Error at line $LINENO"; cleanup' ERR
trap cleanup EXIT

cleanup() {
    rm -rf "$TMPDIR"
    echo "Cleaned up"
}

TMPDIR=$(mktemp -d)
```

**Q4: What is the difference between `source script.sh` and `./script.sh`?**

`source` (or `.`) runs the script in the current shell — variables and functions persist after execution. `./script.sh` runs in a subshell — changes don't affect the parent shell. Use `source` for loading environment variables (`.bashrc`, `.env`).

**Q5: How do you schedule a script to run periodically?**

```bash
# Cron (traditional)
crontab -e
# 0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1

# systemd timer (modern)
# Create .service and .timer unit files
sudo systemctl enable --now backup.timer
systemctl list-timers
```

---

## 12.6 Archiving & Compression

### `tar` — Archive files

```bash
# Classic uncompressed tar workflow
$ tar -cvf archive.tar files/
$ tar -tf archive.tar
$ tar -xvf archive.tar

# Create archive
$ tar cf archive.tar directory/
$ tar czf archive.tar.gz directory/     # With gzip compression
$ tar cjf archive.tar.bz2 directory/    # With bzip2 compression

# Extract archive
$ tar xf archive.tar
$ tar xzf archive.tar.gz
$ tar xjf archive.tar.bz2

# Extract to specific directory
$ tar xzf archive.tar.gz -C /opt/myapp/

# List contents without extracting
$ tar tzf archive.tar.gz
directory/
directory/file1.txt
directory/file2.txt

# Create with verbose output
$ tar czvf backup.tar.gz /opt/myapp/
/opt/myapp/
/opt/myapp/config.yaml
/opt/myapp/bin/server

# Common equivalent flag ordering
$ tar -czvf backup.tar.gz /etc/nginx
$ tar -xzvf backup.tar.gz -C /tmp

# Exclude patterns
$ tar czf backup.tar.gz --exclude='node_modules' --exclude='.git' /opt/myapp/
```

**Explanation**: `c`=create, `x`=extract, `t`=list, `z`=gzip, `j`=bzip2, `f`=filename, `v`=verbose.

### Other compression tools

```bash
# gzip (most common)
$ gzip file.txt           # Creates file.txt.gz, removes original
$ gunzip file.txt.gz      # Decompress
$ zcat file.txt.gz        # View without decompressing

# bzip2 (better compression, slower)
$ bzip2 file.txt
$ bunzip2 file.txt.bz2

# xz (best compression, slowest)
$ xz file.txt
$ unxz file.txt.xz

# zip (cross-platform)
$ zip -r archive.zip directory/
$ unzip archive.zip
$ unzip -l archive.zip    # List contents
```

---

