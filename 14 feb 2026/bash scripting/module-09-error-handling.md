## Module 9: Error Handling, Debugging, and Security

### 9.1 Strict Mode

```bash
#!/bin/bash
set -euo pipefail

# set -e    → Exit immediately on any command failure
# set -u    → Treat unset variables as errors
# set -o pipefail → Pipe fails if ANY command in the pipe fails

# Without pipefail:
#   curl http://bad-url | grep "data"  → exit code 0 (grep's code)
# With pipefail:
#   curl http://bad-url | grep "data"  → exit code from curl (failure)

# IFS for safe word splitting
IFS=$'\n\t'
```

### 9.2 Error Handling Patterns

```bash
#!/bin/bash
set -euo pipefail

# Pattern 1: || operator for fallback
cd /opt/app || { echo "Directory not found"; exit 1; }

# Pattern 2: Custom error handler
on_error() {
    local line=$1
    local cmd=$2
    local code=$3
    echo "ERROR on line $line: command '$cmd' exited with code $code" >&2
}
trap 'on_error ${LINENO} "$BASH_COMMAND" $?' ERR

# Pattern 3: Retry logic
retry() {
    local max_attempts="$1"
    local delay="$2"
    shift 2
    local cmd="$*"

    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt/$max_attempts: $cmd"
        if eval "$cmd"; then
            return 0
        fi
        echo "Failed. Retrying in ${delay}s..."
        sleep "$delay"
        ((attempt++))
    done

    echo "All $max_attempts attempts failed."
    return 1
}

# Usage
retry 3 5 curl -sf "https://api.example.com/health"
retry 5 10 docker pull registry.example.com/myapp:latest

# Pattern 4: Timeout wrapper
run_with_timeout() {
    local timeout="$1"
    shift
    timeout "$timeout" "$@"
    local status=$?
    if [ $status -eq 124 ]; then
        echo "Command timed out after ${timeout}s"
    fi
    return $status
}

# Pattern 5: Lock file to prevent concurrent execution
LOCK_FILE="/var/run/deploy.lock"

acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid
        pid=$(cat "$LOCK_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Another instance is running (PID: $pid)"
            exit 1
        else
            echo "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT
}

acquire_lock
```

### 9.3 Debugging Techniques

```bash
# Enable debug mode (prints every command before execution)
bash -x script.sh                    # From command line
set -x                               # Inside script (enable)
set +x                               # Inside script (disable)

# Debug specific sections
echo "Before critical section"
set -x
# ... commands to debug ...
set +x
echo "After critical section"

# Verbose mode (prints lines as they're read)
set -v

# Custom debug function
DEBUG=${DEBUG:-false}
debug() {
    if $DEBUG; then
        echo "[DEBUG $(date +%T)] $*" >&2
    fi
}

debug "Variable x = $x"
debug "Entering function deploy()"

# Run with: DEBUG=true ./script.sh

# Trace function calls
PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
set -x
# Now debug output shows file, line number, and function name

# Validate inputs
validate_ip() {
    local ip="$1"
    if [[ ! "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "Invalid IP: $ip"
        return 1
    fi
    IFS='.' read -ra octets <<< "$ip"
    for octet in "${octets[@]}"; do
        if [ "$octet" -gt 255 ]; then
            echo "Invalid IP: $ip (octet $octet > 255)"
            return 1
        fi
    done
    return 0
}
```

### 9.4 Security Best Practices

```bash
#!/bin/bash

# 1. Never store secrets in scripts
# BAD:  DB_PASSWORD="supersecret123"
# GOOD:
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD environment variable not set}"
# Or read from a secrets manager:
# DB_PASSWORD=$(vault kv get -field=password secret/db)
# DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id db-password --query SecretString --output text)

# 2. Validate all inputs
sanitize_input() {
    local input="$1"
    echo "$input" | tr -cd 'a-zA-Z0-9._-'
}
user_input=$(sanitize_input "$1")

# 3. Use full paths for commands in cron/automated scripts
/usr/bin/rsync -avz /data/ /backup/
/usr/bin/find /tmp -mtime +7 -delete

# 4. Set restrictive umask
umask 077    # New files: owner-only access

# 5. Secure temp files
TMPFILE=$(mktemp /tmp/myapp.XXXXXX)
chmod 600 "$TMPFILE"
trap "rm -f $TMPFILE" EXIT

# 6. Avoid eval with user input
# BAD:  eval "$user_command"
# GOOD:
case "$user_command" in
    start|stop|restart) systemctl "$user_command" myapp ;;
    *) echo "Invalid command" ;;
esac

# 7. Quote everything
# BAD:  rm -rf $DIR/$FILE
# GOOD:
rm -rf "${DIR}/${FILE}"
```

### 9.5 Real-Life Example: Safe Database Migration Script

```bash
#!/bin/bash
# db-migrate.sh — Run database migrations with safety checks

set -euo pipefail

DB_HOST="${DB_HOST:?}"
DB_NAME="${DB_NAME:?}"
DB_USER="${DB_USER:?}"
DB_PASSWORD="${DB_PASSWORD:?}"
MIGRATIONS_DIR="${MIGRATIONS_DIR:-./migrations}"
BACKUP_DIR="${BACKUP_DIR:-/backups/db}"

LOCK_FILE="/var/run/db-migrate.lock"
LOG_FILE="/var/log/db-migrate.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    pid=$(cat "$LOCK_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        log "ERROR: Migration already running (PID: $pid)"
        exit 1
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# Pre-flight checks
log "Pre-flight checks..."

if ! command -v pg_dump &>/dev/null; then
    log "ERROR: pg_dump not found"
    exit 1
fi

if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
    log "ERROR: Cannot connect to database"
    exit 1
fi

# Count pending migrations
pending=$(find "$MIGRATIONS_DIR" -name "*.sql" -newer "$MIGRATIONS_DIR/.last_run" 2>/dev/null | sort | wc -l)
if [ "$pending" -eq 0 ]; then
    log "No pending migrations"
    exit 0
fi
log "Found $pending pending migration(s)"

# Create backup before migration
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"
mkdir -p "$BACKUP_DIR"
log "Creating backup: $BACKUP_FILE"

if ! PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    log "ERROR: Backup failed. Aborting migration."
    exit 1
fi
log "Backup created ($(du -h "$BACKUP_FILE" | cut -f1))"

# Run migrations
log "Running migrations..."

find "$MIGRATIONS_DIR" -name "*.sql" -newer "$MIGRATIONS_DIR/.last_run" 2>/dev/null | sort | \
while IFS= read -r migration; do
    migration_name=$(basename "$migration")
    log "  Applying: $migration_name"

    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        -v ON_ERROR_STOP=1 -f "$migration" >> "$LOG_FILE" 2>&1; then
        log "  Applied: $migration_name"
    else
        log "  FAILED: $migration_name"
        log "Restoring from backup..."
        gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" >> "$LOG_FILE" 2>&1
        log "Database restored to pre-migration state"
        exit 1
    fi
done

touch "$MIGRATIONS_DIR/.last_run"
log "All migrations applied successfully"
```

### Exercises — Module 9
1. Add retry logic with exponential backoff to an API call script.
2. Write a script with a custom error handler that logs errors with file, line number, and stack trace.
3. Create a script that validates all inputs (IP addresses, ports, hostnames) before executing.

---
