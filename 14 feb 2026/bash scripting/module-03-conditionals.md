## Module 3: Conditionals and Control Flow

### 3.1 if / else

The most basic conditional. Runs a block of code only if a condition is true.

```bash
#!/bin/bash
# if-else.sh

age=25

if [ $age -ge 18 ]; then
    echo "You are an adult"
else
    echo "You are a minor"
fi
```

**Output:**
```
You are an adult
```

**Explanation:** `[ $age -ge 18 ]` tests if `age` is **g**reater than or **e**qual to 18. If true, the first block runs. Otherwise, the `else` block runs.

```bash
# ─── Practical: Check if a file exists ──────────────────
FILE="/etc/hosts"

if [ -f "$FILE" ]; then
    echo "$FILE exists and is a regular file"
    echo "It has $(wc -l < "$FILE") lines"
else
    echo "$FILE does not exist"
fi
```

**Output:**
```
/etc/hosts exists and is a regular file
It has 7 lines
```

```bash
# ─── Practical: Check if a command succeeded ────────────
if ping -c1 -W2 google.com &>/dev/null; then
    echo "Internet is reachable"
else
    echo "No internet connection"
fi
```

**Output (with internet):**
```
Internet is reachable
```

---

### 3.2 if / elif / else

When you have more than two conditions, use `elif` (else if) to chain them.

```bash
#!/bin/bash
# grade.sh

score=75

if [ $score -ge 90 ]; then
    grade="A"
elif [ $score -ge 80 ]; then
    grade="B"
elif [ $score -ge 70 ]; then
    grade="C"
elif [ $score -ge 60 ]; then
    grade="D"
else
    grade="F"
fi

echo "Score: $score → Grade: $grade"
```

**Output:**
```
Score: 75 → Grade: C
```

**Explanation:** Bash checks each condition top-to-bottom. The first one that is true runs its block, and the rest are skipped. If none match, `else` runs.

```bash
# ─── Practical: Check disk usage level ──────────────────
#!/bin/bash
usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

echo "Disk usage: ${usage}%"

if [ "$usage" -ge 90 ]; then
    echo "CRITICAL: Disk almost full! Immediate action needed."
elif [ "$usage" -ge 75 ]; then
    echo "WARNING: Disk usage is high. Plan cleanup soon."
elif [ "$usage" -ge 50 ]; then
    echo "INFO: Disk usage is moderate."
else
    echo "OK: Disk usage is healthy."
fi
```

**Output (example):**
```
Disk usage: 45%
OK: Disk usage is healthy.
```

```bash
# ─── Practical: Check server role and configure ─────────
#!/bin/bash
ROLE="web"

if [ "$ROLE" = "web" ]; then
    echo "Installing nginx..."
    echo "Opening ports 80 and 443..."
elif [ "$ROLE" = "db" ]; then
    echo "Installing PostgreSQL..."
    echo "Opening port 5432..."
elif [ "$ROLE" = "cache" ]; then
    echo "Installing Redis..."
    echo "Opening port 6379..."
else
    echo "ERROR: Unknown role '$ROLE'"
    echo "Valid roles: web, db, cache"
    exit 1
fi
```

**Output:**
```
Installing nginx...
Opening ports 80 and 443...
```

---

### 3.3 Test Operators — Complete Reference

```bash
#!/bin/bash

# ─── String comparisons ────────────────────────────────
a="hello"
b="world"
c=""

[ "$a" = "$b" ]  && echo "equal" || echo "not equal"
[ "$a" != "$b" ] && echo "different" || echo "same"
[ -z "$c" ]      && echo "c is empty" || echo "c is not empty"
[ -n "$a" ]      && echo "a is not empty" || echo "a is empty"
```

**Output:**
```
not equal
different
c is empty
a is not empty
```

```bash
# ─── Numeric comparisons ───────────────────────────────
x=10
y=20

[ "$x" -eq "$y" ] && echo "equal"     || echo "$x != $y"
[ "$x" -ne "$y" ] && echo "not equal" || echo "equal"
[ "$x" -gt "$y" ] && echo "greater"   || echo "$x is not > $y"
[ "$x" -lt "$y" ] && echo "less"      || echo "$x is not < $y"
[ "$x" -ge 10 ]   && echo "x >= 10"   || echo "x < 10"
[ "$x" -le 10 ]   && echo "x <= 10"   || echo "x > 10"
```

**Output:**
```
10 != 20
not equal
10 is not > 20
less
x >= 10
x <= 10
```

| Operator | Meaning | Example |
|----------|---------|---------|
| `-eq` | Equal | `[ 5 -eq 5 ]` → true |
| `-ne` | Not equal | `[ 5 -ne 3 ]` → true |
| `-gt` | Greater than | `[ 10 -gt 5 ]` → true |
| `-ge` | Greater or equal | `[ 10 -ge 10 ]` → true |
| `-lt` | Less than | `[ 3 -lt 5 ]` → true |
| `-le` | Less or equal | `[ 3 -le 5 ]` → true |

```bash
# ─── File tests ────────────────────────────────────────
[ -f "/etc/hosts" ]    && echo "/etc/hosts is a file"
[ -d "/tmp" ]          && echo "/tmp is a directory"
[ -e "/etc/passwd" ]   && echo "/etc/passwd exists"
[ -r "/etc/hosts" ]    && echo "/etc/hosts is readable"
[ -w "/tmp" ]          && echo "/tmp is writable"
[ -x "/bin/bash" ]     && echo "/bin/bash is executable"
[ -s "/etc/hosts" ]    && echo "/etc/hosts is not empty"
```

**Output:**
```
/etc/hosts is a file
/tmp is a directory
/etc/passwd exists
/etc/hosts is readable
/tmp is writable
/bin/bash is executable
/etc/hosts is not empty
```

```bash
# ─── Logical operators ─────────────────────────────────
age=25
name="admin"

# AND — both must be true
if [ "$age" -ge 18 ] && [ "$name" = "admin" ]; then
    echo "Adult admin"
fi

# OR — at least one must be true
if [ "$name" = "admin" ] || [ "$name" = "root" ]; then
    echo "Privileged user"
fi

# NOT — inverts the condition
if [ ! -f "/tmp/lockfile" ]; then
    echo "No lock file found"
fi
```

**Output:**
```
Adult admin
Privileged user
No lock file found
```

```bash
# ─── [[ ]] vs [ ] — Modern bash test ───────────────────
# [[ ]] is preferred in bash — handles spaces, supports regex and patterns

filename="deploy_v2.1.sh"

# Pattern matching (glob)
if [[ "$filename" == deploy_* ]]; then
    echo "$filename is a deploy script"
fi

# Regex matching
ip="192.168.1.100"
if [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "$ip looks like a valid IP"
fi

# Safe with spaces (no need to quote inside [[ ]])
name="John Doe"
if [[ $name == *Doe* ]]; then
    echo "Found Doe in name"
fi
```

**Output:**
```
deploy_v2.1.sh is a deploy script
192.168.1.100 looks like a valid IP
Found Doe in name
```

---

### 3.4 Case Statement

`case` is cleaner than long `if/elif/elif/else` chains. It matches a value against patterns.

```bash
#!/bin/bash
# case-basic.sh

fruit="banana"

case "$fruit" in
    apple)
        echo "It's an apple — red fruit"
        ;;
    banana)
        echo "It's a banana — yellow fruit"
        ;;
    grape|cherry)
        echo "It's a small fruit"
        ;;
    *)
        echo "Unknown fruit: $fruit"
        ;;
esac
```

**Output:**
```
It's a banana — yellow fruit
```

**Explanation:** `case` matches `$fruit` against each pattern. `|` means OR (grape or cherry). `*` is the default/catch-all (like `else`). `;;` ends each block. `esac` closes the case (it's "case" backwards).

```bash
# ─── Practical: Service management script ───────────────
#!/bin/bash
# service-ctl.sh

SERVICE="nginx"
ACTION="${1:-status}"

case "$ACTION" in
    start)
        echo "Starting $SERVICE..."
        sudo systemctl start "$SERVICE"
        echo "$SERVICE started"
        ;;
    stop)
        echo "Stopping $SERVICE..."
        sudo systemctl stop "$SERVICE"
        echo "$SERVICE stopped"
        ;;
    restart)
        echo "Restarting $SERVICE..."
        sudo systemctl restart "$SERVICE"
        echo "$SERVICE restarted"
        ;;
    status)
        systemctl status "$SERVICE" --no-pager
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
```

Run it:
```bash
$ bash service-ctl.sh restart
```

**Output:**
```
Restarting nginx...
nginx restarted
```

```bash
$ bash service-ctl.sh backup
```

**Output:**
```
Usage: ./service-ctl.sh {start|stop|restart|status}
```

```bash
# ─── Practical: Deploy to different environments ────────
#!/bin/bash
environment="$1"

case "$environment" in
    dev|development)
        SERVER="dev.example.com"
        BRANCH="develop"
        ;;
    staging|stg)
        SERVER="staging.example.com"
        BRANCH="release"
        ;;
    prod|production)
        SERVER="prod.example.com"
        BRANCH="main"
        ;;
    *)
        echo "Unknown environment: $environment"
        echo "Usage: $0 {dev|staging|prod}"
        exit 1
        ;;
esac

echo "Deploying branch '$BRANCH' to $SERVER..."
```

Run it:
```bash
$ bash deploy.sh staging
```

**Output:**
```
Deploying branch 'release' to staging.example.com...
```

```bash
$ bash deploy.sh stg
```

**Output (same — because of the | pattern):**
```
Deploying branch 'release' to staging.example.com...
```

---

### 3.5 For Loop

```bash
#!/bin/bash

# ─── Iterate over a list ───────────────────────────────
for server in web01 web02 web03; do
    echo "Deploying to $server..."
done
```

**Output:**
```
Deploying to web01...
Deploying to web02...
Deploying to web03...
```

```bash
# ─── C-style for loop ──────────────────────────────────
for ((i=1; i<=5; i++)); do
    echo "Attempt $i"
done
```

**Output:**
```
Attempt 1
Attempt 2
Attempt 3
Attempt 4
Attempt 5
```

```bash
# ─── Range with {start..end} ───────────────────────────
for i in {1..5}; do
    echo -n "$i "
done
echo ""
```

**Output:**
```
1 2 3 4 5
```

```bash
# ─── Loop over command output ──────────────────────────
for user in $(head -3 /etc/passwd | cut -d: -f1); do
    echo "User: $user"
done
```

**Output:**
```
User: root
User: daemon
User: bin
```

---

### 3.6 While Loop

`while` runs as long as the condition is **true**. Use it when you don't know how many iterations you need.

```bash
#!/bin/bash
# while-basic.sh

count=0
while [ $count -lt 5 ]; do
    echo "Count: $count"
    ((count++))
done
echo "Loop finished. Final count: $count"
```

**Output:**
```
Count: 0
Count: 1
Count: 2
Count: 3
Count: 4
Loop finished. Final count: 5
```

**Explanation:** The loop checks `count < 5` before each iteration. When `count` reaches 5, the condition is false and the loop exits.

```bash
# ─── Read a file line by line ───────────────────────────
#!/bin/bash
# Create a test file
echo -e "web01\nweb02\ndb01" > /tmp/servers.txt

echo "Servers:"
while IFS= read -r line; do
    echo "  - $line"
done < /tmp/servers.txt
```

**Output:**
```
Servers:
  - web01
  - web02
  - db01
```

**Explanation:** `IFS=` prevents leading/trailing whitespace from being trimmed. `-r` prevents backslash interpretation. `< /tmp/servers.txt` feeds the file into the loop.

```bash
# ─── Practical: Retry until a service is ready ──────────
#!/bin/bash
MAX_RETRIES=5
attempt=1

while [ $attempt -le $MAX_RETRIES ]; do
    echo "Attempt $attempt: Checking if service is ready..."

    # Simulate: service becomes ready on attempt 3
    if [ $attempt -ge 3 ]; then
        echo "Service is ready!"
        break
    fi

    echo "Not ready yet. Waiting 2 seconds..."
    sleep 2
    ((attempt++))
done

if [ $attempt -gt $MAX_RETRIES ]; then
    echo "Service failed to start after $MAX_RETRIES attempts"
fi
```

**Output:**
```
Attempt 1: Checking if service is ready...
Not ready yet. Waiting 2 seconds...
Attempt 2: Checking if service is ready...
Not ready yet. Waiting 2 seconds...
Attempt 3: Checking if service is ready...
Service is ready!
```

```bash
# ─── Infinite while loop (common in DevOps for monitoring) ─
#!/bin/bash
# monitor.sh — runs until you press Ctrl+C

iteration=0
while true; do
    ((iteration++))
    echo "[$(date +%T)] Check #$iteration — System OK"

    if [ $iteration -ge 3 ]; then
        echo "Stopping after 3 checks (demo)"
        break
    fi
    sleep 1
done
```

**Output:**
```
[14:30:01] Check #1 — System OK
[14:30:02] Check #2 — System OK
[14:30:03] Check #3 — System OK
Stopping after 3 checks (demo)
```

---

### 3.7 Until Loop

`until` is the opposite of `while` — it runs as long as the condition is **false**, and stops when it becomes **true**.

```bash
#!/bin/bash
# until-basic.sh

count=0
until [ $count -ge 5 ]; do
    echo "Count: $count"
    ((count++))
done
echo "Loop finished. Final count: $count"
```

**Output:**
```
Count: 0
Count: 1
Count: 2
Count: 3
Count: 4
Loop finished. Final count: 5
```

**Explanation:** `until [ $count -ge 5 ]` means "keep running until count >= 5". It's equivalent to `while [ $count -lt 5 ]`.

```bash
# ─── Practical: Wait for a server to come online ────────
#!/bin/bash
HOST="google.com"
echo "Waiting for $HOST to become reachable..."

attempt=0
until ping -c1 -W1 "$HOST" &>/dev/null; do
    ((attempt++))
    echo "  Attempt $attempt: $HOST is not reachable. Retrying..."
    sleep 2
done

echo "$HOST is now reachable! (after $attempt failed attempts)"
```

**Output (if host is already reachable):**
```
Waiting for google.com to become reachable...
google.com is now reachable! (after 0 failed attempts)
```

**Output (if host was down for 2 attempts):**
```
Waiting for google.com to become reachable...
  Attempt 1: google.com is not reachable. Retrying...
  Attempt 2: google.com is not reachable. Retrying...
google.com is now reachable! (after 2 failed attempts)
```

**When to use `while` vs `until`:**

| Use `while` when... | Use `until` when... |
|---------------------|---------------------|
| You want to loop **while** something is true | You want to loop **until** something becomes true |
| `while service_is_running; do monitor; done` | `until service_is_ready; do wait; done` |
| `while [ $count -lt 10 ]` | `until [ $count -ge 10 ]` |

---

### 3.8 Loop Control — break and continue

```bash
#!/bin/bash

echo "=== break example ==="
for i in {1..10}; do
    if [ $i -eq 6 ]; then
        echo "  Breaking at $i"
        break    # Exit the loop entirely
    fi
    echo "  i = $i"
done

echo ""
echo "=== continue example ==="
for i in {1..7}; do
    if [ $i -eq 3 ] || [ $i -eq 5 ]; then
        echo "  Skipping $i"
        continue    # Skip to next iteration
    fi
    echo "  Processing $i"
done
```

**Output:**
```
=== break example ===
  i = 1
  i = 2
  i = 3
  i = 4
  i = 5
  Breaking at 6

=== continue example ===
  Processing 1
  Processing 2
  Skipping 3
  Processing 4
  Skipping 5
  Processing 6
  Processing 7
```

**Explanation:** `break` exits the loop immediately. `continue` skips the rest of the current iteration and jumps to the next one.

### 3.9 Real-Life Example: Health Check Script

```bash
#!/bin/bash
# health-check.sh — Check multiple services and alert on failures

# Configuration
SERVICES=("nginx" "docker" "postgresql" "redis-server")
ENDPOINTS=("http://localhost:80" "http://localhost:8080/api/health")
DISK_THRESHOLD=80
MEM_THRESHOLD=90
ALERT_EMAIL="devops@company.com"

FAILURES=()

echo "=== Health Check: $(date) ==="

# Check systemd services
echo -e "\n--- Services ---"
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        echo "  [OK]   $svc"
    else
        echo "  [FAIL] $svc"
        FAILURES+=("Service '$svc' is down")
    fi
done

# Check HTTP endpoints
echo -e "\n--- Endpoints ---"
for url in "${ENDPOINTS[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
    if [[ "$status" =~ ^2 ]]; then
        echo "  [OK]   $url (HTTP $status)"
    else
        echo "  [FAIL] $url (HTTP $status)"
        FAILURES+=("Endpoint '$url' returned HTTP $status")
    fi
done

# Check disk usage
echo -e "\n--- Disk Usage ---"
while read -r usage mount; do
    usage_num=${usage%\%}
    if [ "$usage_num" -ge "$DISK_THRESHOLD" ]; then
        echo "  [WARN] $mount at ${usage} (threshold: ${DISK_THRESHOLD}%)"
        FAILURES+=("Disk '$mount' at ${usage}")
    else
        echo "  [OK]   $mount at ${usage}"
    fi
done < <(df -h --output=pcent,target | tail -n +2 | grep -v tmpfs)

# Check memory
echo -e "\n--- Memory ---"
mem_used=$(free | awk 'NR==2 {printf "%.0f", $3/$2*100}')
if [ "$mem_used" -ge "$MEM_THRESHOLD" ]; then
    echo "  [WARN] Memory at ${mem_used}% (threshold: ${MEM_THRESHOLD}%)"
    FAILURES+=("Memory at ${mem_used}%")
else
    echo "  [OK]   Memory at ${mem_used}%"
fi

# Summary
echo -e "\n--- Summary ---"
if [ ${#FAILURES[@]} -eq 0 ]; then
    echo "All checks passed."
else
    echo "${#FAILURES[@]} issue(s) found:"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
    # In production, send alert:
    # echo "${FAILURES[*]}" | mail -s "Health Check Alert: $(hostname)" "$ALERT_EMAIL"
fi
```

### 3.10 Real-Life Example: Log Analyzer

```bash
#!/bin/bash
# log-analyzer.sh — Analyze nginx access logs for common patterns

LOGFILE="${1:-/var/log/nginx/access.log}"

if [ ! -f "$LOGFILE" ]; then
    echo "Log file not found: $LOGFILE"
    exit 1
fi

TOTAL=$(wc -l < "$LOGFILE")
echo "Analyzing $LOGFILE ($TOTAL requests)"
echo "========================================="

echo -e "\nTop 10 IP Addresses:"
awk '{print $1}' "$LOGFILE" | sort | uniq -c | sort -rn | head -10 | \
    while read count ip; do
        printf "  %-15s %6d requests (%.1f%%)\n" "$ip" "$count" "$(echo "scale=1; $count*100/$TOTAL" | bc)"
    done

echo -e "\nHTTP Status Code Distribution:"
awk '{print $9}' "$LOGFILE" | sort | uniq -c | sort -rn | \
    while read count code; do
        bar=$(printf '%*s' $((count * 40 / TOTAL)) '' | tr ' ' '#')
        printf "  %s: %6d  %s\n" "$code" "$count" "$bar"
    done

echo -e "\nTop 10 Requested URLs:"
awk '{print $7}' "$LOGFILE" | sort | uniq -c | sort -rn | head -10 | \
    while read count url; do
        printf "  %6d  %s\n" "$count" "$url"
    done

echo -e "\nRequests per Hour (last 24h):"
awk -F'[/: ]' '{print $5}' "$LOGFILE" | sort | uniq -c | \
    while read count hour; do
        bar=$(printf '%*s' $((count * 50 / TOTAL)) '' | tr ' ' '=')
        printf "  %s:00  %5d  %s\n" "$hour" "$count" "$bar"
    done

echo -e "\n4xx/5xx Errors:"
awk '$9 ~ /^[45]/ {print $9, $7}' "$LOGFILE" | sort | uniq -c | sort -rn | head -10 | \
    while read count code url; do
        printf "  %s %s (%d times)\n" "$code" "$url" "$count"
    done
```

### Exercises — Module 3
1. Write a script that checks if Docker is installed, running, and has at least one container active.
2. Create a script that monitors a log file and alerts when "ERROR" appears more than 10 times in 5 minutes.
3. Write a script that takes a list of URLs from a file and checks each one, reporting status codes.

---
