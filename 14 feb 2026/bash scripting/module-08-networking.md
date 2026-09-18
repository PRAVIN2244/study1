## Module 8: Networking and Remote Operations

### 8.1 Network Diagnostics in Scripts

```bash
#!/bin/bash

# Check if a host is reachable
check_host() {
    local host="$1"
    local timeout="${2:-3}"

    if ping -c1 -W"$timeout" "$host" &>/dev/null; then
        echo "  $host: reachable"
        return 0
    else
        echo "  $host: unreachable"
        return 1
    fi
}

# Check if a port is open
check_port() {
    local host="$1"
    local port="$2"
    local timeout="${3:-3}"

    if timeout "$timeout" bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        echo "  $host:$port OPEN"
        return 0
    else
        echo "  $host:$port CLOSED"
        return 1
    fi
}

# DNS lookup
dig +short example.com
nslookup example.com
host example.com

# Network connections
ss -tlnp                    # Listening TCP ports
ss -tunap                   # All connections with process info
netstat -tlnp               # (older systems)

# Trace route
traceroute example.com
mtr example.com             # Better traceroute
```

### 8.2 Working with APIs (curl)

```bash
#!/bin/bash
# api-client.sh — Interact with REST APIs

API_BASE="https://api.example.com/v1"
API_TOKEN="Bearer ${API_TOKEN:?API_TOKEN not set}"

api_call() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local args=(
        -s                              # Silent
        -w "\n%{http_code}"             # Append status code
        -H "Authorization: $API_TOKEN"
        -H "Content-Type: application/json"
        -X "$method"
    )

    [ -n "$data" ] && args+=(-d "$data")

    local response
    response=$(curl "${args[@]}" "${API_BASE}${endpoint}")

    local status_code
    status_code=$(echo "$response" | tail -1)
    local body
    body=$(echo "$response" | sed '$d')

    if [[ "$status_code" =~ ^2 ]]; then
        echo "$body"
        return 0
    else
        echo "API Error (HTTP $status_code): $body" >&2
        return 1
    fi
}

# Usage
# GET
users=$(api_call GET "/users")
echo "$users" | jq '.[] | .name'

# POST
api_call POST "/deployments" '{
    "app": "myapp",
    "version": "2.1.0",
    "environment": "staging"
}'

# Working with jq for JSON parsing
echo '{"name":"web01","cpu":45.2,"memory":78.1}' | jq -r '.name'
echo '{"servers":[{"name":"web01"},{"name":"web02"}]}' | jq -r '.servers[].name'

# Practical: Check GitHub Actions status
check_ci_status() {
    local repo="$1"
    local branch="${2:-main}"

    local result
    result=$(curl -s \
        -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/${repo}/actions/runs?branch=${branch}&per_page=1")

    local status
    status=$(echo "$result" | jq -r '.workflow_runs[0].conclusion')
    local workflow
    workflow=$(echo "$result" | jq -r '.workflow_runs[0].name')

    echo "Latest CI run on $branch: $workflow = $status"
}
```

### 8.3 SSH Automation

```bash
#!/bin/bash
# remote-exec.sh — Execute commands on multiple remote servers

SERVERS_FILE="./servers.txt"
SSH_KEY="~/.ssh/deploy_key"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes"

# Execute command on a single server
remote_exec() {
    local server="$1"
    shift
    local cmd="$*"

    ssh $SSH_OPTS -i "$SSH_KEY" "deploy@${server}" "$cmd" 2>&1
}

# Execute on all servers
run_on_all() {
    local cmd="$*"
    echo "Executing: $cmd"
    echo "================================"

    while IFS= read -r server; do
        [[ "$server" =~ ^#.*$ || -z "$server" ]] && continue
        echo -n "[$server] "
        remote_exec "$server" "$cmd"
    done < "$SERVERS_FILE"
}

# Copy file to all servers
copy_to_all() {
    local src="$1"
    local dest="$2"

    while IFS= read -r server; do
        [[ "$server" =~ ^#.*$ || -z "$server" ]] && continue
        echo -n "[$server] "
        scp $SSH_OPTS -i "$SSH_KEY" "$src" "deploy@${server}:${dest}" && echo "OK" || echo "FAILED"
    done < "$SERVERS_FILE"
}

# Usage
run_on_all "uptime && df -h / | tail -1"
copy_to_all "./app.conf" "/etc/myapp/app.conf"
```

### 8.4 Real-Life Example: SSL Certificate Monitor

```bash
#!/bin/bash
# ssl-monitor.sh — Check SSL certificate expiry for multiple domains

DOMAINS=(
    "example.com"
    "api.example.com"
    "app.example.com"
    "admin.example.com"
)
WARN_DAYS=30
CRIT_DAYS=7

check_ssl() {
    local domain="$1"
    local port="${2:-443}"

    local expiry_date
    expiry_date=$(echo | openssl s_client -servername "$domain" \
        -connect "${domain}:${port}" 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | \
        cut -d= -f2)

    if [ -z "$expiry_date" ]; then
        echo "  [ERROR] $domain — Could not retrieve certificate"
        return 2
    fi

    local expiry_epoch
    expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
    local now_epoch
    now_epoch=$(date +%s)
    local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

    if [ $days_left -le $CRIT_DAYS ]; then
        echo "  [CRIT]  $domain — Expires in ${days_left} days ($expiry_date)"
        return 2
    elif [ $days_left -le $WARN_DAYS ]; then
        echo "  [WARN]  $domain — Expires in ${days_left} days ($expiry_date)"
        return 1
    else
        echo "  [OK]    $domain — Expires in ${days_left} days ($expiry_date)"
        return 0
    fi
}

echo "SSL Certificate Check — $(date)"
echo "================================="

exit_code=0
for domain in "${DOMAINS[@]}"; do
    check_ssl "$domain"
    result=$?
    [ $result -gt $exit_code ] && exit_code=$result
done

echo ""
case $exit_code in
    0) echo "All certificates are healthy." ;;
    1) echo "Some certificates expire soon. Renew them." ;;
    2) echo "ALERT: Certificates need immediate attention!" ;;
esac

exit $exit_code
```

### Exercises — Module 8
1. Write a script that checks if a list of ports are open on a server and reports the results.
2. Create a script that pulls data from a REST API, parses the JSON with `jq`, and generates a report.
3. Build an SSH-based script that collects disk usage from 5 servers and shows a combined summary.

---
