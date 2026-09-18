## Module 12: Capstone Projects and Production Patterns

### 12.1 Capstone Project 1: Automated Server Provisioning

```bash
#!/bin/bash
# provision-server.sh — Provision a new server from scratch
#
# Usage: ./provision-server.sh <hostname> <role>
# Roles: web, api, db, worker

set -euo pipefail

HOSTNAME="${1:?Usage: $0 <hostname> <role>}"
ROLE="${2:?Specify role: web|api|db|worker}"
LOG_FILE="/var/log/provision-${HOSTNAME}.log"

source "$(dirname "$0")/lib/common.sh"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ─── Base Setup ─────────────────────────────────────────
setup_base() {
    log "Setting hostname to $HOSTNAME"
    hostnamectl set-hostname "$HOSTNAME"

    log "Updating packages..."
    apt-get update -qq && apt-get upgrade -y -qq

    log "Installing base packages..."
    apt-get install -y -qq \
        curl wget git vim htop \
        net-tools dnsutils \
        unzip jq tree \
        fail2ban ufw

    log "Configuring firewall..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw --force enable

    log "Configuring SSH hardening..."
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    systemctl restart sshd

    log "Setting up automatic security updates..."
    apt-get install -y -qq unattended-upgrades
    dpkg-reconfigure -plow unattended-upgrades

    log "Creating deploy user..."
    useradd -m -s /bin/bash -G sudo deploy 2>/dev/null || true
    mkdir -p /home/deploy/.ssh
    cp /root/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
    chown -R deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
}

# ─── Role-Specific Setup ───────────────────────────────
setup_web() {
    log "Setting up web server role..."
    apt-get install -y -qq nginx certbot python3-certbot-nginx
    ufw allow 'Nginx Full'

    cat > /etc/nginx/conf.d/security.conf <<'NGINX'
server_tokens off;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
NGINX

    systemctl enable nginx
    systemctl start nginx
    log "Web server configured."
}

setup_api() {
    log "Setting up API server role..."
    # Install Node.js
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
    npm install -g pm2

    # Install Docker
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker deploy

    ufw allow 8080/tcp
    log "API server configured."
}

setup_db() {
    log "Setting up database server role..."
    apt-get install -y -qq postgresql postgresql-contrib

    # Configure for remote connections
    local pg_version
    pg_version=$(ls /etc/postgresql/)
    echo "listen_addresses = '*'" >> "/etc/postgresql/${pg_version}/main/postgresql.conf"
    echo "host all all 10.0.0.0/8 md5" >> "/etc/postgresql/${pg_version}/main/pg_hba.conf"

    systemctl restart postgresql
    ufw allow 5432/tcp
    log "Database server configured."
}

setup_worker() {
    log "Setting up worker role..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker deploy

    # Install Redis CLI for queue interaction
    apt-get install -y -qq redis-tools
    log "Worker configured."
}

# ─── Monitoring Setup ──────────────────────────────────
setup_monitoring() {
    log "Setting up monitoring agent..."

    # Install node_exporter for Prometheus
    local version="1.7.0"
    wget -q "https://github.com/prometheus/node_exporter/releases/download/v${version}/node_exporter-${version}.linux-amd64.tar.gz"
    tar xzf "node_exporter-${version}.linux-amd64.tar.gz"
    cp "node_exporter-${version}.linux-amd64/node_exporter" /usr/local/bin/
    rm -rf "node_exporter-${version}.linux-amd64"*

    cat > /etc/systemd/system/node_exporter.service <<'SERVICE'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=nobody
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

    systemctl daemon-reload
    systemctl enable node_exporter
    systemctl start node_exporter
    ufw allow 9100/tcp
    log "Monitoring agent installed."
}

# ─── Main ──────────────────────────────────────────────
main() {
    require_root
    log "Starting provisioning: $HOSTNAME (role: $ROLE)"

    setup_base

    case "$ROLE" in
        web)    setup_web ;;
        api)    setup_api ;;
        db)     setup_db ;;
        worker) setup_worker ;;
        *)      log "ERROR: Unknown role: $ROLE"; exit 1 ;;
    esac

    setup_monitoring

    log ""
    log "========================================="
    log "Provisioning complete!"
    log "  Hostname: $HOSTNAME"
    log "  Role:     $ROLE"
    log "  IP:       $(hostname -I | awk '{print $1}')"
    log "========================================="
}

main
```

### 12.2 Capstone Project 2: Complete Deployment Pipeline

```bash
#!/bin/bash
# full-deploy.sh — End-to-end deployment pipeline
#
# Stages: validate → build → test → deploy → verify → notify

set -euo pipefail

APP_NAME="myapp"
VERSION="${1:?Usage: $0 <version> [environment]}"
ENVIRONMENT="${2:-staging}"
REGISTRY="registry.company.com"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
DEPLOY_START=$(date +%s)

# ─── Helpers ────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "[$(date +%T)] $*"; }
ok()   { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

notify_slack() {
    local message="$1"
    local color="${2:-good}"
    [ -z "$SLACK_WEBHOOK" ] && return

    curl -s -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"Deployment: ${APP_NAME} v${VERSION}\",
                \"text\": \"$message\",
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                    {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true}
                ]
            }]
        }" > /dev/null
}

duration() {
    local end=$(date +%s)
    local elapsed=$((end - DEPLOY_START))
    echo "$((elapsed / 60))m $((elapsed % 60))s"
}

# ─── Stage 1: Validate ─────────────────────────────────
stage_validate() {
    log "Stage 1: Validate"

    # Check required tools
    for cmd in docker kubectl jq curl; do
        if command -v "$cmd" &>/dev/null; then
            ok "$cmd found"
        else
            fail "$cmd not found"
            exit 1
        fi
    done

    # Check kubectl context
    local context
    context=$(kubectl config current-context)
    if [[ "$context" == *"$ENVIRONMENT"* ]]; then
        ok "kubectl context: $context"
    else
        warn "kubectl context '$context' may not match environment '$ENVIRONMENT'"
        read -p "Continue? (y/n): " confirm
        [ "$confirm" = "y" ] || exit 1
    fi

    # Check git status
    if [ -n "$(git status --porcelain)" ]; then
        fail "Working directory is not clean"
        git status --short
        exit 1
    fi
    ok "Git working directory clean"

    # Verify version tag exists
    if git rev-parse "v${VERSION}" &>/dev/null; then
        ok "Git tag v${VERSION} exists"
    else
        fail "Git tag v${VERSION} not found"
        exit 1
    fi
}

# ─── Stage 2: Build ────────────────────────────────────
stage_build() {
    log "Stage 2: Build"

    git checkout "v${VERSION}"

    docker build \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        -t "${REGISTRY}/${APP_NAME}:${VERSION}" \
        .

    ok "Docker image built: ${APP_NAME}:${VERSION}"

    docker push "${REGISTRY}/${APP_NAME}:${VERSION}"
    ok "Image pushed to registry"
}

# ─── Stage 3: Test ──────────────────────────────────────
stage_test() {
    log "Stage 3: Test"

    # Run unit tests in container
    docker run --rm "${REGISTRY}/${APP_NAME}:${VERSION}" npm test
    ok "Unit tests passed"

    # Security scan
    trivy image --severity HIGH,CRITICAL \
        --exit-code 1 \
        "${REGISTRY}/${APP_NAME}:${VERSION}"
    ok "Security scan passed"
}

# ─── Stage 4: Deploy ───────────────────────────────────
stage_deploy() {
    log "Stage 4: Deploy to $ENVIRONMENT"

    notify_slack "Deployment started" "#439FE0"

    # Update Kubernetes deployment
    kubectl set image deployment/"$APP_NAME" \
        "$APP_NAME=${REGISTRY}/${APP_NAME}:${VERSION}" \
        -n "$ENVIRONMENT"

    # Wait for rollout
    if kubectl rollout status deployment/"$APP_NAME" \
        -n "$ENVIRONMENT" --timeout=300s; then
        ok "Rollout complete"
    else
        fail "Rollout failed"
        log "Initiating rollback..."
        kubectl rollout undo deployment/"$APP_NAME" -n "$ENVIRONMENT"
        notify_slack "Deployment FAILED and rolled back" "danger"
        exit 1
    fi
}

# ─── Stage 5: Verify ───────────────────────────────────
stage_verify() {
    log "Stage 5: Post-deploy verification"

    local health_url
    health_url=$(kubectl get svc "$APP_NAME" -n "$ENVIRONMENT" \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')/health

    local retries=5
    for ((i=1; i<=retries; i++)); do
        local status
        status=$(curl -s -o /dev/null -w "%{http_code}" "https://${health_url}" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            ok "Health check passed (HTTP $status)"
            return 0
        fi
        warn "Health check attempt $i/$retries: HTTP $status"
        sleep 10
    done

    fail "Health check failed after $retries attempts"
    log "Initiating rollback..."
    kubectl rollout undo deployment/"$APP_NAME" -n "$ENVIRONMENT"
    notify_slack "Deployment FAILED health checks and rolled back" "danger"
    exit 1
}

# ─── Main ──────────────────────────────────────────────
main() {
    echo "============================================"
    echo "  Deploying ${APP_NAME} v${VERSION}"
    echo "  Environment: ${ENVIRONMENT}"
    echo "  Time: $(date)"
    echo "============================================"
    echo ""

    stage_validate
    stage_build
    stage_test
    stage_deploy
    stage_verify

    echo ""
    echo "============================================"
    echo "  Deployment SUCCESSFUL"
    echo "  Duration: $(duration)"
    echo "============================================"

    notify_slack "Deployment successful ($(duration))" "good"
}

main
```

### 12.3 Capstone Project 3: System Monitoring Dashboard

```bash
#!/bin/bash
# monitor-dashboard.sh — Terminal-based system monitoring dashboard
# Refreshes every 5 seconds

REFRESH=5

draw_bar() {
    local percent=$1
    local width=30
    local filled=$((percent * width / 100))
    local empty=$((width - filled))
    local color

    if [ "$percent" -ge 90 ]; then color="\033[0;31m"     # Red
    elif [ "$percent" -ge 70 ]; then color="\033[1;33m"    # Yellow
    else color="\033[0;32m"                                 # Green
    fi

    printf "${color}"
    printf '%*s' "$filled" '' | tr ' ' '█'
    printf "\033[0m"
    printf '%*s' "$empty" '' | tr ' ' '░'
    printf " %3d%%" "$percent"
}

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          SYSTEM MONITOR — $(hostname)                   "
    echo "║          $(date '+%Y-%m-%d %H:%M:%S')                   "
    echo "╠══════════════════════════════════════════════════════════╣"

    # CPU
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print int($2 + $4)}')
    echo -n "║  CPU:    "
    draw_bar "$cpu_usage"
    echo ""

    # Memory
    mem_info=$(free | awk 'NR==2 {printf "%d %d %d", $3/$2*100, $3/1024, $2/1024}')
    mem_pct=$(echo "$mem_info" | awk '{print $1}')
    mem_used=$(echo "$mem_info" | awk '{print $2}')
    mem_total=$(echo "$mem_info" | awk '{print $3}')
    echo -n "║  Memory: "
    draw_bar "$mem_pct"
    echo "  (${mem_used}MB / ${mem_total}MB)"

    # Swap
    swap_info=$(free | awk 'NR==3 {if($2>0) printf "%d", $3/$2*100; else print 0}')
    echo -n "║  Swap:   "
    draw_bar "$swap_info"
    echo ""

    # Disks
    echo "║"
    echo "║  Disks:"
    df -h --output=target,pcent,size,used | grep -E "^/" | while read mount pct size used; do
        pct_num=${pct%\%}
        echo -n "║    $mount: "
        draw_bar "$pct_num"
        echo "  ($used / $size)"
    done

    # Load average
    echo "║"
    load=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
    cores=$(nproc)
    echo "║  Load Average: $load  (${cores} cores)"

    # Top processes
    echo "║"
    echo "║  Top Processes (by CPU):"
    echo "║  %-6s %-8s %-5s %-5s %s" "PID" "USER" "CPU%" "MEM%" "COMMAND"
    ps aux --sort=-%cpu | head -6 | tail -5 | \
        awk '{printf "║  %-6s %-8s %-5s %-5s %s\n", $2, $1, $3, $4, $11}'

    # Network
    echo "║"
    echo "║  Network Connections:"
    echo "║    Established: $(ss -t state established | wc -l)"
    echo "║    Listening:    $(ss -tln | tail -n +2 | wc -l) ports"

    # Docker (if available)
    if command -v docker &>/dev/null; then
        echo "║"
        echo "║  Docker:"
        echo "║    Running containers: $(docker ps -q 2>/dev/null | wc -l)"
        echo "║    Total images:       $(docker images -q 2>/dev/null | wc -l)"
    fi

    echo "║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo "  Refreshing every ${REFRESH}s... (Ctrl+C to exit)"

    sleep $REFRESH
done
```

### 12.4 Production Patterns Cheat Sheet

```bash
# ─── Pattern: Idempotent Scripts ────────────────────────
# Scripts should be safe to run multiple times

# BAD:
echo "export PATH=/opt/app/bin:$PATH" >> ~/.bashrc

# GOOD:
grep -q '/opt/app/bin' ~/.bashrc || echo "export PATH=/opt/app/bin:\$PATH" >> ~/.bashrc


# ─── Pattern: Atomic File Updates ───────────────────────
# Never write directly to config files in production

# BAD:
sed -i 's/old/new/' /etc/nginx/nginx.conf
nginx -s reload

# GOOD:
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
sed 's/old/new/' /etc/nginx/nginx.conf > /etc/nginx/nginx.conf.new
nginx -t -c /etc/nginx/nginx.conf.new    # Test first!
mv /etc/nginx/nginx.conf.new /etc/nginx/nginx.conf
nginx -s reload


# ─── Pattern: Graceful Degradation ──────────────────────
send_alert() {
    # Try Slack first, fall back to email, fall back to log
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -s -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"$1\"}" && return
    fi
    if command -v mail &>/dev/null; then
        echo "$1" | mail -s "Alert" "$ALERT_EMAIL" && return
    fi
    logger -t "myapp-alert" "$1"
}


# ─── Pattern: Feature Flags ────────────────────────────
ENABLE_NEW_FEATURE="${ENABLE_NEW_FEATURE:-false}"

if [ "$ENABLE_NEW_FEATURE" = "true" ]; then
    deploy_with_new_feature
else
    deploy_standard
fi


# ─── Pattern: Canary Deployment ────────────────────────
canary_deploy() {
    local version="$1"
    local canary_pct="${2:-10}"

    # Deploy to canary (small subset)
    kubectl set image deployment/myapp-canary myapp=myapp:$version
    kubectl scale deployment/myapp-canary --replicas=$((TOTAL_REPLICAS * canary_pct / 100))

    echo "Canary deployed. Monitoring for 5 minutes..."
    sleep 300

    # Check error rate
    local error_rate
    error_rate=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_errors_total[5m])" | jq '.data.result[0].value[1]')

    if (( $(echo "$error_rate < 0.01" | bc -l) )); then
        echo "Canary healthy. Proceeding with full rollout."
        kubectl set image deployment/myapp myapp=myapp:$version
    else
        echo "Canary unhealthy (error rate: $error_rate). Rolling back."
        kubectl rollout undo deployment/myapp-canary
    fi
}
```

### 12.5 Shell Scripting Best Practices Summary

```
1. ALWAYS use `set -euo pipefail` at the top of scripts
2. ALWAYS quote your variables: "$var" not $var
3. Use `local` for function variables
4. Use `readonly` for constants
5. Use `trap` for cleanup on exit
6. Use `mktemp` for temporary files
7. Use `[[ ]]` instead of `[ ]` for conditionals
8. Use `$(command)` instead of backticks
9. Use functions to organize code
10. Use meaningful exit codes (0=success, 1=general error, 2=usage error)
11. Log to stderr for errors, stdout for output
12. Use ShellCheck to lint your scripts: shellcheck script.sh
13. Test scripts with `bash -n script.sh` (syntax check)
14. Use `set -x` for debugging, `set +x` to disable
15. Never use `eval` with user input
16. Always validate inputs before using them
17. Use lock files to prevent concurrent execution
18. Make scripts idempotent (safe to run multiple times)
19. Include usage/help text with -h/--help
20. Add the shebang line: #!/bin/bash
```

### Exercises — Module 12
1. Build a complete server provisioning script for your preferred stack.
2. Create an end-to-end deployment pipeline script with rollback support.
3. Write a monitoring script that checks services, disk, memory, and sends alerts.
4. Combine everything: Build a CLI tool with subcommands that manages your infrastructure.

---
