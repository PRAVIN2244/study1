## Module 11: CI/CD, Cloud, and Infrastructure Automation

### 11.1 CI/CD Pipeline Helper Scripts

```bash
#!/bin/bash
# ci-pipeline.sh — Local CI pipeline runner (mirrors what runs in CI)

set -euo pipefail

STAGE="${1:-all}"

step() {
    echo ""
    echo "========================================"
    echo "  STAGE: $1"
    echo "========================================"
}

stage_lint() {
    step "LINT"
    shellcheck scripts/*.sh
    hadolint Dockerfile
    yamllint .github/workflows/*.yml
    echo "Lint passed."
}

stage_test() {
    step "TEST"
    docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
    docker compose -f docker-compose.test.yml down -v
    echo "Tests passed."
}

stage_build() {
    step "BUILD"
    local version
    version=$(git describe --tags --always)
    docker build -t "myapp:${version}" .
    echo "Build complete: myapp:${version}"
}

stage_security() {
    step "SECURITY SCAN"
    local version
    version=$(git describe --tags --always)
    # Scan for vulnerabilities
    trivy image "myapp:${version}" --severity HIGH,CRITICAL
    # Scan for secrets in code
    gitleaks detect --source . --verbose
    echo "Security scan passed."
}

case "$STAGE" in
    lint)     stage_lint ;;
    test)     stage_test ;;
    build)    stage_build ;;
    security) stage_security ;;
    all)
        stage_lint
        stage_test
        stage_build
        stage_security
        step "ALL STAGES PASSED"
        ;;
    *)
        echo "Usage: $0 {lint|test|build|security|all}"
        exit 1
        ;;
esac
```

### 11.2 AWS Automation

```bash
#!/bin/bash
# aws-ec2-manager.sh — Manage EC2 instances by tag

set -euo pipefail

ACTION="${1:?Usage: $0 <start|stop|status|list> [tag-value]}"
TAG_KEY="Environment"
TAG_VALUE="${2:-production}"

get_instances() {
    aws ec2 describe-instances \
        --filters "Name=tag:${TAG_KEY},Values=${TAG_VALUE}" \
        --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0],PrivateIpAddress]' \
        --output text
}

case "$ACTION" in
    list|status)
        echo "Instances tagged ${TAG_KEY}=${TAG_VALUE}:"
        echo "-------------------------------------------"
        printf "%-20s %-12s %-30s %-15s\n" "Instance ID" "State" "Name" "Private IP"
        echo "-------------------------------------------"
        get_instances | while read -r id state name ip; do
            printf "%-20s %-12s %-30s %-15s\n" "$id" "$state" "$name" "$ip"
        done
        ;;
    start)
        ids=$(get_instances | awk '$2=="stopped" {print $1}')
        if [ -z "$ids" ]; then
            echo "No stopped instances found."
            exit 0
        fi
        echo "Starting instances: $ids"
        aws ec2 start-instances --instance-ids $ids
        ;;
    stop)
        ids=$(get_instances | awk '$2=="running" {print $1}')
        if [ -z "$ids" ]; then
            echo "No running instances found."
            exit 0
        fi
        echo "Stopping instances: $ids"
        aws ec2 stop-instances --instance-ids $ids
        ;;
esac
```

### 11.3 Kubernetes Operations

```bash
#!/bin/bash
# k8s-ops.sh — Common Kubernetes operations

set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"

# Rolling restart all deployments in a namespace
rolling_restart() {
    local ns="${1:-$NAMESPACE}"
    echo "Rolling restart of all deployments in namespace: $ns"
    
    for deploy in $(kubectl get deployments -n "$ns" -o name); do
        echo "  Restarting $deploy..."
        kubectl rollout restart "$deploy" -n "$ns"
    done
    
    echo "Waiting for rollouts to complete..."
    for deploy in $(kubectl get deployments -n "$ns" -o name); do
        kubectl rollout status "$deploy" -n "$ns" --timeout=120s
    done
    echo "All deployments restarted."
}

# Get resource usage summary
resource_summary() {
    local ns="${1:-$NAMESPACE}"
    echo "Resource Summary for namespace: $ns"
    echo "======================================"
    
    echo ""
    echo "Pod Status:"
    kubectl get pods -n "$ns" --no-headers | awk '{print $3}' | sort | uniq -c | sort -rn
    
    echo ""
    echo "Top Pods by CPU:"
    kubectl top pods -n "$ns" --sort-by=cpu 2>/dev/null | head -10
    
    echo ""
    echo "Top Pods by Memory:"
    kubectl top pods -n "$ns" --sort-by=memory 2>/dev/null | head -10
}

# Find and delete evicted/failed pods
cleanup_pods() {
    local ns="${1:-$NAMESPACE}"
    local count
    
    count=$(kubectl get pods -n "$ns" --field-selector=status.phase=Failed -o name 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "Deleting $count failed pod(s) in $ns..."
        kubectl delete pods -n "$ns" --field-selector=status.phase=Failed
    fi
    
    count=$(kubectl get pods -n "$ns" | grep Evicted | wc -l)
    if [ "$count" -gt 0 ]; then
        echo "Deleting $count evicted pod(s) in $ns..."
        kubectl get pods -n "$ns" | grep Evicted | awk '{print $1}' | xargs kubectl delete pod -n "$ns"
    fi
    
    echo "Cleanup complete."
}

case "${1:-help}" in
    restart)  rolling_restart "${2:-}" ;;
    summary)  resource_summary "${2:-}" ;;
    cleanup)  cleanup_pods "${2:-}" ;;
    *)
        echo "Usage: $0 {restart|summary|cleanup} [namespace]"
        ;;
esac
```

### 11.4 Real-Life Example: Infrastructure Cost Reporter

```bash
#!/bin/bash
# cost-report.sh — Generate infrastructure cost awareness report

set -euo pipefail

echo "Infrastructure Cost Report — $(date +%Y-%m-%d)"
echo "================================================"

# EC2 instances running
echo ""
echo "--- Running EC2 Instances ---"
aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].[InstanceType,Tags[?Key==`Name`].Value|[0],LaunchTime]' \
    --output text | sort | while read -r type name launch; do
    printf "  %-12s %-30s (since %s)\n" "$type" "$name" "${launch%T*}"
done

running_count=$(aws ec2 describe-instances \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[].Instances[].InstanceId' --output text | wc -w)
echo "  Total: $running_count instances"

# Unattached EBS volumes (wasted money)
echo ""
echo "--- Unattached EBS Volumes (wasted cost) ---"
aws ec2 describe-volumes \
    --filters "Name=status,Values=available" \
    --query 'Volumes[].[VolumeId,Size,VolumeType,CreateTime]' \
    --output text | while read -r id size type created; do
    printf "  %s  %4dGB  %-6s  (created %s)\n" "$id" "$size" "$type" "${created%T*}"
done

# Old snapshots
echo ""
echo "--- EBS Snapshots older than 90 days ---"
cutoff=$(date -d '90 days ago' +%Y-%m-%d 2>/dev/null || date -v-90d +%Y-%m-%d)
aws ec2 describe-snapshots --owner-ids self \
    --query "Snapshots[?StartTime<='${cutoff}'].[SnapshotId,VolumeSize,StartTime,Description]" \
    --output text | wc -l | xargs -I{} echo "  {} snapshots older than 90 days"

# Elastic IPs not associated
echo ""
echo "--- Unassociated Elastic IPs (\$3.65/month each) ---"
aws ec2 describe-addresses \
    --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' \
    --output text | while read -r ip alloc; do
    echo "  $ip ($alloc)"
done

echo ""
echo "================================================"
echo "Review items above to reduce infrastructure costs."
```

### Exercises — Module 11
1. Write a CI helper script that runs linting, testing, and building in sequence, stopping on first failure.
2. Create a script that finds and reports unused AWS resources (unattached EBS, idle load balancers).
3. Build a Kubernetes namespace provisioning script that creates namespace, resource quotas, and RBAC.

---
