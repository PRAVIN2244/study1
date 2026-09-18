## Module 4: Functions and Script Organization

### 4.1 Defining Functions

Two syntax options — both work identically:

```bash
#!/bin/bash

# Syntax option 1 (preferred — POSIX compatible)
greet() {
    echo "Hello, $1!"
}

# Syntax option 2 (bash-specific)
function greet_formal {
    echo "Good day, $1. Welcome to $2."
}

# Call them
greet "DevOps Engineer"
greet_formal "Alice" "Production"
```

**Output:**
```
Hello, DevOps Engineer!
Good day, Alice. Welcome to Production.
```

**Explanation:** `$1`, `$2` etc. are positional parameters — the arguments passed to the function. Functions must be defined before they are called.

---

### 4.2 Function Arguments and Return Values

```bash
#!/bin/bash

# ─── Function arguments ────────────────────────────────
show_args() {
    echo "Function name:      $0"       # Still the script name, NOT function name
    echo "First argument:     $1"
    echo "Second argument:    $2"
    echo "All arguments:      $@"
    echo "Number of arguments:$#"
}

show_args "hello" "world" "foo"
```

**Output:**
```
Function name:      ./script.sh
First argument:     hello
Second argument:    world
All arguments:      hello world foo
Number of arguments:3
```

```bash
# ─── Return values ──────────────────────────────────────
# 'return' sets an exit code (0-255). It does NOT return data.
# Use 'echo' to return data, and capture with $( )

# Return exit code (success/failure)
is_even() {
    if [ $(($1 % 2)) -eq 0 ]; then
        return 0    # Success = true
    else
        return 1    # Failure = false
    fi
}

is_even 4 && echo "4 is even" || echo "4 is odd"
is_even 7 && echo "7 is even" || echo "7 is odd"
```

**Output:**
```
4 is even
7 is odd
```

```bash
# Return data (use echo + command substitution)
get_disk_usage() {
    df -h / | awk 'NR==2 {print $5}'
}

usage=$(get_disk_usage)
echo "Disk usage: $usage"
```

**Output:**
```
Disk usage: 45%
```

```bash
# ─── Default parameter values ──────────────────────────
deploy() {
    local app="$1"
    local env="${2:-staging}"        # Default to "staging"
    local version="${3:-latest}"     # Default to "latest"

    echo "Deploying $app v$version to $env"
}

deploy "myapp"
deploy "myapp" "production" "2.1.0"
```

**Output:**
```
Deploying myapp vlatest to staging
Deploying myapp v2.1.0 to production
```

---

### 4.3 Variable Scope in Functions

```bash
#!/bin/bash

# ─── Without 'local' — variables LEAK out of functions ─
bad_function() {
    result="I leaked!"       # No 'local' — becomes global
    temp_file="/tmp/bad"     # This also leaks
}

bad_function
echo "result = $result"      # Accessible outside!
echo "temp_file = $temp_file"

# ─── With 'local' — variables stay INSIDE the function ─
good_function() {
    local result="I stay inside"
    local temp_file="/tmp/good"
    echo "Inside: result = $result"
}

good_function
echo "Outside: result = $result"   # Still "I leaked!" from bad_function
```

**Output:**
```
result = I leaked!
temp_file = /tmp/bad
Inside: result = I stay inside
Outside: result = I leaked!
```

**Explanation:** Without `local`, variables defined inside a function pollute the global scope. Always use `local` for variables that should stay inside the function.

```bash
# ─── Nested function scope ──────────────────────────────
outer() {
    local x="outer_value"
    echo "outer: x=$x"

    inner() {
        echo "inner: x=$x"      # Can see parent's local variable
        local x="inner_value"   # Shadows the outer x
        echo "inner after local: x=$x"
    }

    inner
    echo "outer after inner: x=$x"   # Unchanged — inner had its own local
}

outer
```

**Output:**
```
outer: x=outer_value
inner: x=outer_value
inner after local: x=inner_value
outer after inner: x=outer_value
```

```bash
# ─── Practical example: why scope matters ───────────────
count=0    # Global counter

process_file() {
    local count=0    # Local counter — doesn't affect global
    local file="$1"
    while IFS= read -r line; do
        ((count++))
    done < "$file"
    echo "$file: $count lines"
}

process_file /etc/hostname
process_file /etc/shells
echo "Global count is still: $count"
```

**Output:**
```
/etc/hostname: 1 lines
/etc/shells: 7 lines
Global count is still: 0
```

### 4.4 Script Organization Pattern

```bash
#!/bin/bash
# well-organized-script.sh
#
# Description: Template for a well-structured shell script
# Usage: ./well-organized-script.sh [options] <arguments>

set -euo pipefail    # Exit on error, undefined vars, pipe failures

# ─── Constants ──────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="/var/log/${SCRIPT_NAME%.sh}.log"

# ─── Configuration ──────────────────────────────────────
VERBOSE=false
DRY_RUN=false
ENVIRONMENT="staging"

# ─── Functions ──────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $SCRIPT_NAME [OPTIONS] <command>

Options:
    -e, --env ENV       Target environment (default: staging)
    -v, --verbose       Enable verbose output
    -n, --dry-run       Show what would be done
    -h, --help          Show this help

Commands:
    deploy              Deploy the application
    rollback            Rollback to previous version
    status              Show current status
EOF
}

log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $msg" | tee -a "$LOG_FILE"
}

info()  { log "INFO"  "$@"; }
warn()  { log "WARN"  "$@"; }
error() { log "ERROR" "$@"; }

die() {
    error "$@"
    exit 1
}

cleanup() {
    # Runs on script exit (success or failure)
    info "Cleaning up temporary files..."
    rm -f /tmp/${SCRIPT_NAME}.*
}

# ─── Argument Parsing ──────────────────────────────────
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done
}

# ─── Command Implementations ───────────────────────────
cmd_deploy() {
    info "Deploying to $ENVIRONMENT..."
    if $DRY_RUN; then
        info "[DRY RUN] Would deploy to $ENVIRONMENT"
        return 0
    fi
    # actual deployment logic
}

cmd_status() {
    info "Checking status of $ENVIRONMENT..."
    # status check logic
}

# ─── Main ──────────────────────────────────────────────
main() {
    trap cleanup EXIT    # Always run cleanup on exit

    parse_args "$@"

    case "${COMMAND:-}" in
        deploy)   cmd_deploy ;;
        rollback) cmd_rollback ;;
        status)   cmd_status ;;
        "")       die "No command specified. Use -h for help." ;;
        *)        die "Unknown command: $COMMAND" ;;
    esac
}

main "$@"
```

### 4.5 Sourcing and Libraries

```bash
# lib/common.sh — Reusable library
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'    # No Color

print_ok()   { echo -e "${GREEN}[OK]${NC}   $*"; }
print_fail() { echo -e "${RED}[FAIL]${NC} $*"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        print_fail "This script must be run as root"
        exit 1
    fi
}

require_command() {
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            print_fail "Required command not found: $cmd"
            exit 1
        fi
    done
}
```

```bash
# deploy.sh — Uses the library
#!/bin/bash
source "$(dirname "$0")/lib/common.sh"

require_command docker kubectl helm
print_ok "All dependencies found"
```

### 4.6 Real-Life Example: Multi-Service Deployment Script

```bash
#!/bin/bash
# deploy-services.sh — Deploy multiple microservices with rollback support

set -euo pipefail

SERVICES=("api-gateway" "user-service" "order-service" "notification-service")
REGISTRY="registry.company.com"
NAMESPACE="production"
DEPLOY_LOG="/tmp/deploy-$(date +%s).log"

deploy_service() {
    local service="$1"
    local version="$2"
    local image="${REGISTRY}/${service}:${version}"

    echo -n "  Deploying ${service}:${version}... "

    # Save current version for rollback
    local current
    current=$(kubectl get deployment "$service" -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none")
    echo "$service=$current" >> "$DEPLOY_LOG"

    # Update image
    if kubectl set image deployment/"$service" \
        "$service=$image" -n "$NAMESPACE" &>/dev/null; then

        # Wait for rollout
        if kubectl rollout status deployment/"$service" \
            -n "$NAMESPACE" --timeout=120s &>/dev/null; then
            echo "OK"
            return 0
        fi
    fi

    echo "FAILED"
    return 1
}

rollback_all() {
    echo "Rolling back all deployments..."
    while IFS='=' read -r service image; do
        if [ "$image" != "none" ]; then
            echo "  Reverting $service to $image"
            kubectl set image deployment/"$service" \
                "$service=$image" -n "$NAMESPACE" &>/dev/null
        fi
    done < "$DEPLOY_LOG"
}

main() {
    local version="${1:?Usage: $0 <version>}"
    local failed=false

    echo "Deploying version $version to $NAMESPACE"
    echo "========================================="

    for service in "${SERVICES[@]}"; do
        if ! deploy_service "$service" "$version"; then
            failed=true
            break
        fi
    done

    if $failed; then
        echo ""
        echo "Deployment failed! Initiating rollback..."
        rollback_all
        rm -f "$DEPLOY_LOG"
        exit 1
    fi

    echo ""
    echo "All services deployed successfully!"
    rm -f "$DEPLOY_LOG"
}

main "$@"
```

### Exercises — Module 4
1. Create a library file with functions for logging (info, warn, error, debug) with timestamps and colors.
2. Write a script with proper argument parsing that accepts `--env`, `--version`, and `--dry-run` flags.
3. Build a script that sources a config file and deploys based on the config values.

---
