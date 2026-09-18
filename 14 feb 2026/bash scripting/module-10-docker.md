## Module 10: Docker and Container Automation

### 10.1 Docker Management Scripts

```bash
#!/bin/bash
# docker-cleanup.sh — Clean up unused Docker resources

set -euo pipefail

echo "=== Docker Cleanup ==="
echo ""

# Stop all running containers (optional)
# docker stop $(docker ps -q) 2>/dev/null

# Remove stopped containers
stopped=$(docker ps -aq --filter status=exited | wc -l)
if [ "$stopped" -gt 0 ]; then
    echo "Removing $stopped stopped container(s)..."
    docker rm $(docker ps -aq --filter status=exited) 2>/dev/null
fi

# Remove dangling images
dangling=$(docker images -f "dangling=true" -q | wc -l)
if [ "$dangling" -gt 0 ]; then
    echo "Removing $dangling dangling image(s)..."
    docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null
fi

# Remove unused volumes
volumes=$(docker volume ls -qf dangling=true | wc -l)
if [ "$volumes" -gt 0 ]; then
    echo "Removing $volumes unused volume(s)..."
    docker volume rm $(docker volume ls -qf dangling=true) 2>/dev/null
fi

# Remove unused networks
docker network prune -f 2>/dev/null

# Show space reclaimed
echo ""
echo "Current disk usage:"
docker system df
```

### 10.2 Docker Build and Push Automation

```bash
#!/bin/bash
# docker-build.sh — Build, tag, and push Docker images

set -euo pipefail

APP_NAME="${1:?Usage: $0 <app-name> [version]}"
VERSION="${2:-$(git describe --tags --always 2>/dev/null || echo 'latest')}"
REGISTRY="${DOCKER_REGISTRY:-registry.company.com}"
IMAGE="${REGISTRY}/${APP_NAME}"

echo "Building ${IMAGE}:${VERSION}"

# Build with cache
docker build \
    --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --build-arg VERSION="$VERSION" \
    --build-arg GIT_COMMIT="$(git rev-parse --short HEAD)" \
    -t "${IMAGE}:${VERSION}" \
    -t "${IMAGE}:latest" \
    .

# Run tests inside container
echo "Running tests..."
docker run --rm "${IMAGE}:${VERSION}" /app/run-tests.sh

# Push
echo "Pushing to registry..."
docker push "${IMAGE}:${VERSION}"
docker push "${IMAGE}:latest"

echo "Done: ${IMAGE}:${VERSION}"
```

### 10.3 Real-Life Example: Docker Compose Environment Manager

```bash
#!/bin/bash
# env-manager.sh — Manage Docker Compose environments

set -euo pipefail

COMPOSE_DIR="./docker"
ENV="${1:-}"
ACTION="${2:-}"

usage() {
    echo "Usage: $0 <environment> <action>"
    echo ""
    echo "Environments: dev, test, staging"
    echo "Actions: up, down, restart, logs, status, reset"
    exit 1
}

[ -z "$ENV" ] || [ -z "$ACTION" ] && usage

COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.${ENV}.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Compose file not found: $COMPOSE_FILE"
    exit 1
fi

COMPOSE="docker compose -f ${COMPOSE_DIR}/docker-compose.yml -f ${COMPOSE_FILE} -p ${ENV}"

case "$ACTION" in
    up)
        echo "Starting $ENV environment..."
        $COMPOSE up -d --build
        echo ""
        $COMPOSE ps
        ;;
    down)
        echo "Stopping $ENV environment..."
        $COMPOSE down
        ;;
    restart)
        echo "Restarting $ENV environment..."
        $COMPOSE restart
        ;;
    logs)
        $COMPOSE logs -f --tail=100
        ;;
    status)
        $COMPOSE ps
        echo ""
        echo "Resource usage:"
        docker stats --no-stream $($COMPOSE ps -q) 2>/dev/null
        ;;
    reset)
        echo "Resetting $ENV environment (all data will be lost)..."
        read -p "Are you sure? (yes/no): " confirm
        [ "$confirm" = "yes" ] || exit 0
        $COMPOSE down -v --remove-orphans
        $COMPOSE up -d --build --force-recreate
        ;;
    *)
        usage
        ;;
esac
```

### Exercises — Module 10
1. Write a script that monitors Docker container resource usage and alerts when CPU or memory exceeds thresholds.
2. Create a script that backs up all Docker volumes to compressed archives.
3. Build a script that performs rolling updates of Docker Compose services with health checks.

---
