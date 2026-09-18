# Module 22: Shell Scripting — Control Flow and Functions

## 11.3 Conditionals

### `if` statement

```bash
#!/bin/bash
FILE="/etc/nginx/nginx.conf"

if [ -f "$FILE" ]; then
    echo "Nginx config exists"
else
    echo "Nginx config NOT found"
fi
```

Output:
```
Nginx config exists
```

**Explanation**: `-f` tests if a file exists and is a regular file. Always quote variables inside `[ ]` to handle spaces.

### File test operators

| Operator | Test                                    |
|----------|-----------------------------------------|
| `-f`     | File exists and is a regular file       |
| `-d`     | Directory exists                        |
| `-e`     | File/directory exists (any type)        |
| `-r`     | File is readable                        |
| `-w`     | File is writable                        |
| `-x`     | File is executable                      |
| `-s`     | File exists and is not empty            |
| `-L`     | File is a symbolic link                 |

### String comparison

```bash
#!/bin/bash
ENV="production"

if [ "$ENV" = "production" ]; then
    echo "Running in PRODUCTION mode"
elif [ "$ENV" = "staging" ]; then
    echo "Running in STAGING mode"
else
    echo "Running in DEVELOPMENT mode"
fi
```

| Operator | Meaning                    |
|----------|----------------------------|
| `=`      | Strings are equal          |
| `!=`     | Strings are not equal      |
| `-z`     | String is empty            |
| `-n`     | String is not empty        |

### Numeric comparison

```bash
#!/bin/bash
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')

if [ "$DISK_USAGE" -gt 90 ]; then
    echo "CRITICAL: Disk usage is ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -gt 70 ]; then
    echo "WARNING: Disk usage is ${DISK_USAGE}%"
else
    echo "OK: Disk usage is ${DISK_USAGE}%"
fi
```

Output:
```
OK: Disk usage is 26%
```

| Operator | Meaning                  |
|----------|--------------------------|
| `-eq`    | Equal                    |
| `-ne`    | Not equal                |
| `-gt`    | Greater than             |
| `-ge`    | Greater than or equal    |
| `-lt`    | Less than                |
| `-le`    | Less than or equal       |

### Double brackets `[[ ]]` (bash-specific, preferred)

```bash
#!/bin/bash
FILE="/var/log/syslog"

if [[ -f "$FILE" && -r "$FILE" ]]; then
    echo "File exists and is readable"
fi

# Pattern matching
if [[ "$HOSTNAME" == web-* ]]; then
    echo "This is a web server"
fi

# Regex matching
if [[ "$EMAIL" =~ ^[a-zA-Z]+@[a-zA-Z]+\.[a-zA-Z]+$ ]]; then
    echo "Valid email format"
fi
```

**Explanation**: `[[ ]]` supports `&&`, `||`, pattern matching (`==` with wildcards), and regex (`=~`). Preferred over `[ ]` in bash scripts.

### `case` statement

```bash
#!/bin/bash
case "$1" in
    start)
        echo "Starting service..."
        systemctl start myapp
        ;;
    stop)
        echo "Stopping service..."
        systemctl stop myapp
        ;;
    restart)
        echo "Restarting service..."
        systemctl restart myapp
        ;;
    status)
        systemctl status myapp
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
```

```bash
$ ./service.sh start
Starting service...

$ ./service.sh invalid
Usage: ./service.sh {start|stop|restart|status}
```

**Explanation**: `case` is cleaner than multiple `if/elif` for matching a variable against several values. `*)` is the default case. `;;` terminates each case block.

---

## 11.4 Loops

### `for` loop

```bash
#!/bin/bash
# Loop over a list
for SERVER in web-01 web-02 web-03 db-01; do
    echo "Checking $SERVER..."
    ping -c 1 -W 2 "$SERVER" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  $SERVER is UP"
    else
        echo "  $SERVER is DOWN"
    fi
done
```

Output:
```
Checking web-01...
  web-01 is UP
Checking web-02...
  web-02 is UP
Checking web-03...
  web-03 is DOWN
Checking db-01...
  db-01 is UP
```

### C-style for loop

```bash
#!/bin/bash
for ((i=1; i<=5; i++)); do
    echo "Iteration $i"
done
```

### Loop over files

```bash
#!/bin/bash
for FILE in /var/log/*.log; do
    SIZE=$(du -sh "$FILE" | awk '{print $1}')
    echo "$FILE: $SIZE"
done
```

Output:
```
/var/log/syslog: 2.3M
/var/log/auth.log: 1.2M
/var/log/kern.log: 4.5M
```

### Loop over command output

```bash
#!/bin/bash
for USER in $(cut -d: -f1 /etc/passwd); do
    echo "User: $USER"
done
```

### `while` loop

```bash
#!/bin/bash
COUNT=1
while [ $COUNT -le 5 ]; do
    echo "Count: $COUNT"
    COUNT=$((COUNT + 1))
done
```

Output:
```
Count: 1
Count: 2
Count: 3
Count: 4
Count: 5
```

### Read file line by line

```bash
#!/bin/bash
while IFS= read -r LINE; do
    echo "Processing: $LINE"
done < /etc/hosts
```

Output:
```
Processing: 127.0.0.1       localhost
Processing: 172.17.0.2      devops-server
```

**Explanation**: `IFS=` prevents leading/trailing whitespace trimming. `-r` prevents backslash interpretation. `< file` feeds the file as input.

### Read CSV file

```bash
#!/bin/bash
while IFS=',' read -r NAME DEPT SALARY CITY; do
    if [ "$DEPT" = "Engineering" ]; then
        echo "$NAME earns $SALARY in $CITY"
    fi
done < <(tail -n +2 employees.csv)
```

Output:
```
Alice earns 95000 in New York
Charlie earns 105000 in San Francisco
Eve earns 88000 in Chicago
```

**Explanation**: `tail -n +2` skips the header line. `<(command)` is process substitution — treats command output as a file.

### Infinite loop with break

```bash
#!/bin/bash
while true; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
    if [ "$STATUS" -eq 200 ]; then
        echo "Service is healthy!"
        break
    fi
    echo "Waiting for service... (HTTP $STATUS)"
    sleep 5
done
```

---

## 11.5 Functions

```bash
#!/bin/bash

# Define a function
log_message() {
    local LEVEL="$1"
    local MESSAGE="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$LEVEL] $MESSAGE"
}

# Use the function
log_message "INFO" "Deployment started"
log_message "WARN" "Disk usage above 70%"
log_message "ERROR" "Connection refused"
```

Output:
```
[2025-02-05 15:00:00] [INFO] Deployment started
[2025-02-05 15:00:00] [WARN] Disk usage above 70%
[2025-02-05 15:00:00] [ERROR] Connection refused
```

**Explanation**: `local` makes variables scoped to the function. `$1`, `$2` are function arguments (not script arguments).

### Function with return value

```bash
#!/bin/bash

is_service_running() {
    systemctl is-active --quiet "$1"
    return $?
}

check_service() {
    local SERVICE="$1"
    if is_service_running "$SERVICE"; then
        echo "$SERVICE: RUNNING"
    else
        echo "$SERVICE: STOPPED"
    fi
}

check_service nginx
check_service postgresql
check_service redis
```

Output:
```
nginx: RUNNING
postgresql: RUNNING
redis: STOPPED
```

### Function returning a string

```bash
#!/bin/bash

get_disk_usage() {
    df / | awk 'NR==2 {print $5}' | tr -d '%'
}

USAGE=$(get_disk_usage)
echo "Disk usage: ${USAGE}%"
```

---


## 11.7 Arrays

```bash
#!/bin/bash

# Define an array
SERVERS=("web-01" "web-02" "web-03" "db-01")

# Access elements
echo "First server: ${SERVERS[0]}"
echo "All servers: ${SERVERS[@]}"
echo "Number of servers: ${#SERVERS[@]}"

# Loop over array
for SERVER in "${SERVERS[@]}"; do
    echo "Deploying to $SERVER..."
done

# Add element
SERVERS+=("cache-01")

# Remove element (by index)
unset SERVERS[2]
```

Output:
```
First server: web-01
All servers: web-01 web-02 web-03 db-01
Number of servers: 4
Deploying to web-01...
Deploying to web-02...
Deploying to web-03...
Deploying to db-01...
```

---


## 11.14 Until Loop

The `until` loop runs as long as the condition is **false** (opposite of `while`):

```bash
#!/bin/bash
counter=1
until [ $counter -gt 5 ]; do
    echo "Count: $counter"
    ((counter++))
done
```

### Real-world example: Wait for a service to be ready

```bash
#!/bin/bash
until curl -s http://localhost:8080/health > /dev/null 2>&1; do
    echo "Waiting for service to start..."
    sleep 2
done
echo "Service is up!"
```

### Wait for user confirmation

```bash
#!/bin/bash
input=""
until [ "$input" = "yes" ]; do
    read -p "Type 'yes' to continue: " input
done
echo "Proceeding..."
```

---

## 11.15 Select Menu

`select` creates an interactive numbered menu:

```bash
#!/bin/bash
echo "Choose an environment:"
select env in development staging production quit; do
    case $env in
        development) echo "Deploying to dev..."; break;;
        staging)     echo "Deploying to staging..."; break;;
        production)  echo "Deploying to production..."; break;;
        quit)        echo "Exiting."; exit 0;;
        *)           echo "Invalid option. Try again.";;
    esac
done
```

Sample output:
```
Choose an environment:
1) development
2) staging
3) production
4) quit
#? 2
Deploying to staging...
```

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


## 11.17 Parsing Command-Line Options with getopts

`getopts` processes flags and options passed to a script:

```bash
#!/bin/bash

usage() {
    echo "Usage: $0 [-e environment] [-v] [-h]"
    echo "  -e  Environment (dev, staging, prod)"
    echo "  -v  Verbose mode"
    echo "  -h  Show help"
    exit 1
}

VERBOSE=false
ENV="dev"

while getopts "e:vh" opt; do
    case $opt in
        e) ENV="$OPTARG";;
        v) VERBOSE=true;;
        h) usage;;
        *) usage;;
    esac
done

echo "Environment: $ENV"
echo "Verbose: $VERBOSE"

if $VERBOSE; then
    echo "Running in verbose mode..."
fi
```

Usage:
```bash
./deploy.sh -e production -v
# Output:
# Environment: production
# Verbose: true
# Running in verbose mode...
```

---

