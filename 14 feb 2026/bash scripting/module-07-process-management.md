## Module 7: Process Management and Job Control

### 7.1 Process Basics

```bash
# View processes
ps aux                              # All processes, detailed
ps aux | grep nginx                 # Find specific process
ps -ef --forest                     # Process tree
pstree -p                           # Visual process tree
top                                 # Interactive process viewer
htop                                # Better interactive viewer

# Process info
echo $$                             # Current shell PID
echo $!                             # Last background process PID
echo $PPID                          # Parent process PID

# /proc filesystem
cat /proc/cpuinfo                   # CPU info
cat /proc/meminfo                   # Memory info
cat /proc/<PID>/status              # Process details
ls -la /proc/<PID>/fd/             # Open file descriptors
```

### 7.2 Background Jobs and Job Control

```bash
# Run in background
long_running_command &
echo "PID: $!"

# Job control
jobs                                # List background jobs
fg %1                               # Bring job 1 to foreground
bg %1                               # Resume job 1 in background
# Ctrl+Z                            # Suspend current foreground job

# nohup — Survive terminal disconnect
nohup ./deploy.sh > deploy.log 2>&1 &

# disown — Detach from shell
./long-task.sh &
disown %1

# Wait for background processes
pid1=$!
command2 &
pid2=$!
wait $pid1 $pid2
echo "Both processes completed"
```

### 7.3 Signals and Traps

```bash
# Common signals
# SIGHUP  (1)  — Terminal closed
# SIGINT  (2)  — Ctrl+C
# SIGTERM (15) — Graceful termination
# SIGKILL (9)  — Force kill (cannot be caught)
# SIGUSR1 (10) — User-defined

# Send signals
kill <PID>                          # Send SIGTERM
kill -9 <PID>                       # Send SIGKILL (last resort)
kill -HUP <PID>                     # Send SIGHUP (reload config)
killall nginx                       # Kill by name
pkill -f "python app.py"           # Kill by pattern

# Trap signals in scripts
#!/bin/bash

cleanup() {
    echo "Caught signal! Cleaning up..."
    rm -f /tmp/myapp.lock
    kill $(jobs -p) 2>/dev/null     # Kill child processes
    exit 1
}

trap cleanup SIGINT SIGTERM SIGHUP
trap "echo 'Script finished'" EXIT   # Always runs on exit

echo "Running... (PID: $$)"
echo $$ > /tmp/myapp.lock

while true; do
    # Main work loop
    sleep 1
done
```

### 7.4 Parallel Execution

```bash
#!/bin/bash
# parallel-deploy.sh — Deploy to multiple servers in parallel

SERVERS=("web01" "web02" "web03" "web04" "web05")
MAX_PARALLEL=3

deploy_to_server() {
    local server="$1"
    echo "[$(date +%T)] Starting deploy to $server"
    ssh "$server" "cd /opt/app && git pull && systemctl restart app" 2>&1
    local status=$?
    if [ $status -eq 0 ]; then
        echo "[$(date +%T)] $server: SUCCESS"
    else
        echo "[$(date +%T)] $server: FAILED (exit code: $status)"
    fi
    return $status
}

# Method 1: Simple parallel with wait
pids=()
for server in "${SERVERS[@]}"; do
    deploy_to_server "$server" &
    pids+=($!)
done

# Wait for all and collect results
failures=0
for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
        ((failures++))
    fi
done
echo "Completed with $failures failure(s)"

# Method 2: Controlled parallelism (max N at a time)
running=0
for server in "${SERVERS[@]}"; do
    deploy_to_server "$server" &
    ((running++))

    if [ $running -ge $MAX_PARALLEL ]; then
        wait -n    # Wait for ANY one job to finish (bash 4.3+)
        ((running--))
    fi
done
wait    # Wait for remaining jobs
```

### 7.5 Real-Life Example: Process Monitor and Auto-Restart

```bash
#!/bin/bash
# process-watchdog.sh — Monitor a process and restart if it dies

set -euo pipefail

APP_NAME="myapp"
APP_CMD="/opt/myapp/bin/server --config /etc/myapp/config.yaml"
PID_FILE="/var/run/${APP_NAME}.pid"
LOG_FILE="/var/log/${APP_NAME}-watchdog.log"
CHECK_INTERVAL=10
MAX_RESTARTS=5
RESTART_WINDOW=300    # seconds

restart_count=0
window_start=$(date +%s)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

start_app() {
    log "Starting $APP_NAME..."
    $APP_CMD >> "/var/log/${APP_NAME}.log" 2>&1 &
    echo $! > "$PID_FILE"
    log "$APP_NAME started with PID $(cat "$PID_FILE")"
}

check_restart_limit() {
    local now
    now=$(date +%s)
    local elapsed=$((now - window_start))

    if [ $elapsed -gt $RESTART_WINDOW ]; then
        restart_count=0
        window_start=$now
    fi

    if [ $restart_count -ge $MAX_RESTARTS ]; then
        log "ALERT: $APP_NAME restarted $MAX_RESTARTS times in ${RESTART_WINDOW}s. Giving up."
        log "Manual intervention required!"
        exit 1
    fi
}

# Main loop
log "Watchdog started for $APP_NAME"

if ! is_running; then
    start_app
fi

while true; do
    sleep $CHECK_INTERVAL

    if ! is_running; then
        log "WARNING: $APP_NAME is not running!"
        check_restart_limit
        ((restart_count++))
        start_app
    fi
done
```

### Exercises — Module 7
1. Write a script that runs 5 tasks in parallel, waits for all to complete, and reports which succeeded/failed.
2. Create a watchdog script that monitors a process by name and restarts it with exponential backoff.
3. Write a script that gracefully shuts down multiple services in reverse dependency order.

---
