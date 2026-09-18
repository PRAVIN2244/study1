# Module 29: Production Deployment Patterns

Running containers in production requires restart policies, resource
governance, health checks, rolling updates, and deployment strategies
like blue-green and canary releases.

### Topics Covered

```
29.1  Production Readiness Checklist
29.2  Restart Policies
29.3  Resource Limits and Reservations
29.4  Health Checks — Deep Dive
29.5  Graceful Shutdown and Signal Handling
29.6  Rolling Updates in Docker Swarm
29.7  Blue-Green Deployments
29.8  Canary Deployments
29.9  Docker Compose in Production
29.10 Reverse Proxy Patterns (Nginx, Traefik)
29.11 Zero-Downtime Deployment Workflow
29.12 Common Errors and Troubleshooting
```

---

## 29.1 Production Readiness Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              PRODUCTION CONTAINER CHECKLIST                     │
│                                                                 │
│  Image                                                         │
│  ☐ Use specific tag (never :latest in production)              │
│  ☐ Minimal base image (alpine, distroless, scratch)            │
│  ☐ Non-root user (USER directive in Dockerfile)                │
│  ☐ No secrets baked into image                                 │
│  ☐ Vulnerability scan passed (0 critical)                      │
│  ☐ .dockerignore excludes dev files                            │
│                                                                 │
│  Runtime                                                       │
│  ☐ Restart policy set (unless-stopped or on-failure)           │
│  ☐ Memory limit set (--memory)                                 │
│  ☐ CPU limit set (--cpus)                                      │
│  ☐ PID limit set (--pids-limit)                                │
│  ☐ Read-only rootfs where possible (--read-only)               │
│  ☐ Capabilities dropped (--cap-drop=ALL + add only needed)     │
│  ☐ No --privileged flag                                        │
│                                                                 │
│  Observability                                                 │
│  ☐ Health check defined (HEALTHCHECK in Dockerfile)            │
│  ☐ Logs go to stdout/stderr                                    │
│  ☐ Log rotation configured (max-size, max-file)                │
│  ☐ Metrics endpoint exposed (/metrics)                         │
│                                                                 │
│  Data                                                          │
│  ☐ Persistent data on volumes (not container filesystem)       │
│  ☐ Secrets via Docker secrets or env vars (not files in image) │
│  ☐ Backup strategy for volumes                                 │
│                                                                 │
│  Networking                                                    │
│  ☐ User-defined bridge network (not default bridge)            │
│  ☐ Only necessary ports exposed                                │
│  ☐ TLS for external-facing services                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 29.2 Restart Policies

```bash
# Restart policies control what happens when a container exits

# never restart (default)
$ docker run --restart=no myapp

# restart only on non-zero exit code
$ docker run --restart=on-failure myapp

# restart on failure with max retry count
$ docker run --restart=on-failure:5 myapp
# Stops retrying after 5 consecutive failures

# always restart (even after daemon restart)
$ docker run --restart=always myapp
# WARNING: Also restarts containers you manually stopped

# restart unless explicitly stopped
$ docker run --restart=unless-stopped myapp
# Best for production — respects manual docker stop
```

### Restart Policy Comparison

```
┌──────────────────┬────────────┬────────────┬────────────────────┐
│ Policy           │ On crash   │ On daemon  │ After docker stop  │
│                  │ (exit ≠ 0) │ restart    │ + daemon restart   │
├──────────────────┼────────────┼────────────┼────────────────────┤
│ no               │ Stay dead  │ Stay dead  │ Stay dead          │
│ on-failure       │ Restart    │ Restart    │ Stay dead          │
│ on-failure:N     │ Restart    │ Restart    │ Stay dead          │
│                  │ (max N)    │            │                    │
│ always           │ Restart    │ Restart    │ Restart            │
│ unless-stopped   │ Restart    │ Restart    │ Stay dead          │
└──────────────────┴────────────┴────────────┴────────────────────┘
```

### Restart Policy in Docker Compose

```yaml
services:
  api:
    image: myapp:v1.0.0
    restart: unless-stopped
    # Options: "no", "always", "on-failure", "unless-stopped"

  worker:
    image: myworker:v1.0.0
    restart: on-failure
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

### Restart Backoff

```
# Docker uses exponential backoff for restarts:
#   1st restart: immediate
#   2nd restart: after 1 second
#   3rd restart: after 2 seconds
#   4th restart: after 4 seconds
#   ...up to a maximum of 1 minute between restarts
#
# The backoff resets after the container runs successfully for 10 seconds
#
# Check restart count:
$ docker inspect --format '{{.RestartCount}}' myapp
# 3
```

---

## 29.3 Resource Limits and Reservations

### Memory Limits

```bash
# Hard memory limit (container is OOM-killed if exceeded)
$ docker run -d --memory=512m myapp
# -m or --memory: maximum memory the container can use

# Memory + swap limit
$ docker run -d --memory=512m --memory-swap=1g myapp
# --memory-swap: total memory + swap allowed
# Swap available = memory-swap - memory = 512MB swap

# Disable swap entirely
$ docker run -d --memory=512m --memory-swap=512m myapp
# When memory-swap equals memory, no swap is available

# Soft limit (kernel reclaims memory under pressure)
$ docker run -d --memory=512m --memory-reservation=256m myapp
# --memory-reservation: soft limit, not enforced strictly

# OOM kill priority (-1000 to 1000, lower = less likely to be killed)
$ docker run -d --oom-score-adj=-500 myapp

# Disable OOM killer (container hangs instead of being killed)
$ docker run -d --oom-kill-disable --memory=512m myapp
# WARNING: Only use with --memory set, or it can hang the host
```

### CPU Limits

```bash
# Limit to 1.5 CPUs
$ docker run -d --cpus=1.5 myapp

# CPU shares (relative weight, default 1024)
$ docker run -d --cpu-shares=512 myapp
# Only matters when CPU is contested
# Container with 512 shares gets half the CPU of one with 1024

# Pin to specific CPU cores
$ docker run -d --cpuset-cpus="0,1" myapp
# Container can only use CPU cores 0 and 1

# CPU period and quota (fine-grained control)
$ docker run -d --cpu-period=100000 --cpu-quota=150000 myapp
# 150000/100000 = 1.5 CPUs (same as --cpus=1.5)
```

### Resource Limits in Docker Compose

```yaml
services:
  api:
    image: myapp:v1.0.0
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
          pids: 200
        reservations:
          cpus: '0.5'
          memory: 256M
    # limits: maximum the container can use
    # reservations: guaranteed minimum (for scheduling)
```

### Monitoring Resource Usage

```bash
# Real-time resource usage
$ docker stats
# CONTAINER   CPU %   MEM USAGE / LIMIT   MEM %   NET I/O   BLOCK I/O
# myapp       12.5%   256MiB / 512MiB     50%     1.2kB     0B

# Single container, no stream
$ docker stats --no-stream myapp

# JSON format for scripting
$ docker stats --no-stream --format '{{json .}}' myapp
```

---

## 29.4 Health Checks — Deep Dive

### Dockerfile HEALTHCHECK

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# TCP health check (for databases)
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD pg_isready -U postgres || exit 1

# File-based health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD test -f /tmp/healthy || exit 1

# Custom script health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /app/healthcheck.sh || exit 1
```

```
# Flag explanations:
#   --interval=30s      Time between health checks
#   --timeout=5s        Max time for a single check to complete
#   --start-period=15s  Grace period during startup (failures don't count)
#   --retries=3         Consecutive failures before marking "unhealthy"
#
# Health states:
#   starting   → within start-period, failures don't count
#   healthy    → last N checks passed
#   unhealthy  → N consecutive failures (N = retries)
#
# Exit codes:
#   0 = healthy
#   1 = unhealthy
#   2 = reserved (do not use)
```

### Health Check in docker run

```bash
# Override Dockerfile health check at runtime
$ docker run -d \
    --health-cmd="curl -f http://localhost:8080/health || exit 1" \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=3 \
    --health-start-period=30s \
    myapp

# Disable health check
$ docker run -d --no-healthcheck myapp
```

### Health Check Integration with Swarm

```
# In Docker Swarm, health checks drive:
#   1. Rolling update progression
#      - New task must be healthy before old task is stopped
#   2. Load balancer routing
#      - Unhealthy tasks are removed from the ingress network
#   3. Automatic restart
#      - Unhealthy tasks are killed and rescheduled
```

---

## 29.5 Graceful Shutdown and Signal Handling

```
# When docker stop is called:
#   1. Docker sends SIGTERM to PID 1 in the container
#   2. Waits for --stop-timeout (default 10 seconds)
#   3. If still running, sends SIGKILL (force kill)
#
# Your application MUST handle SIGTERM to shut down gracefully:
#   - Close database connections
#   - Finish processing current requests
#   - Flush logs and metrics
#   - Release file locks
```

### Signal Handling in Different Languages

```javascript
// Node.js — graceful shutdown
const server = app.listen(3000);

process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    server.close(() => {
        console.log('HTTP server closed');
        // Close DB connections
        db.end().then(() => process.exit(0));
    });
    // Force exit after 10 seconds
    setTimeout(() => process.exit(1), 10000);
});
```

```python
# Python — graceful shutdown
import signal, sys

def shutdown(signum, frame):
    print("Shutting down gracefully...")
    server.shutdown()
    db.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
```

```go
// Go — graceful shutdown
func main() {
    srv := &http.Server{Addr: ":8080"}
    go srv.ListenAndServe()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

### Shell Form vs Exec Form (PID 1 Problem)

```dockerfile
# WRONG — shell form wraps command in /bin/sh -c
# sh does NOT forward signals to child processes
CMD node server.js
# Process tree: sh(PID 1) → node(PID 2)
# SIGTERM goes to sh, node never receives it

# CORRECT — exec form, node IS PID 1
CMD ["node", "server.js"]
# Process tree: node(PID 1)
# SIGTERM goes directly to node
```

```bash
# Increase stop timeout for slow-shutting applications
$ docker stop --time=30 myapp
# Waits 30 seconds before SIGKILL

# Change default stop signal
$ docker run --stop-signal=SIGQUIT nginx
# nginx uses SIGQUIT for graceful shutdown
```

---

## 29.6 Rolling Updates in Docker Swarm

```bash
# Create a service
$ docker service create --name api \
    --replicas 6 \
    --update-parallelism 2 \
    --update-delay 10s \
    --update-failure-action rollback \
    --update-order start-first \
    --rollback-parallelism 2 \
    --rollback-delay 5s \
    myapp:v1.0.0

# Update the service image
$ docker service update --image myapp:v2.0.0 api
```

```
# Rolling update flags explained:
#
#   --update-parallelism 2
#     Update 2 tasks at a time (default: 1)
#
#   --update-delay 10s
#     Wait 10 seconds between batches
#
#   --update-failure-action rollback
#     If a task fails to start, automatically rollback
#     Options: pause (default), continue, rollback
#
#   --update-order start-first
#     Start new task BEFORE stopping old task (zero-downtime)
#     Options: stop-first (default), start-first
#
#   --rollback-parallelism 2
#     Rollback 2 tasks at a time
#
#   --rollback-delay 5s
#     Wait 5 seconds between rollback batches
```

### Rolling Update Flow (start-first)

```
┌─────────────────────────────────────────────────────────────────┐
│  ROLLING UPDATE: 6 replicas, parallelism=2, start-first        │
│                                                                 │
│  Step 1: Start 2 new v2 tasks                                  │
│    v1 v1 v1 v1 v1 v1 + v2 v2 (8 tasks temporarily)            │
│                                                                 │
│  Step 2: v2 tasks healthy → stop 2 old v1 tasks                │
│    v1 v1 v1 v1 v2 v2                                           │
│                                                                 │
│  Step 3: Wait 10s (update-delay)                               │
│                                                                 │
│  Step 4: Start 2 more v2 tasks                                 │
│    v1 v1 v1 v1 v2 v2 + v2 v2                                  │
│                                                                 │
│  Step 5: v2 healthy → stop 2 more v1                           │
│    v1 v1 v2 v2 v2 v2                                           │
│                                                                 │
│  Step 6: Wait 10s → start last 2 v2 → stop last 2 v1          │
│    v2 v2 v2 v2 v2 v2  ✓ Complete                               │
└─────────────────────────────────────────────────────────────────┘
```

### Manual Rollback

```bash
# Rollback to previous version
$ docker service rollback api

# Check rollback status
$ docker service ps api
# Shows both old and new tasks with their states
```

---

## 29.7 Blue-Green Deployments

```
# Blue-green: Run two identical environments (blue = current, green = new)
# Switch traffic atomically via load balancer
#
# Advantages:
#   - Instant rollback (switch back to blue)
#   - Zero downtime
#   - Full testing of green before switching
#
# Disadvantages:
#   - Requires 2x resources during deployment
#   - Database migrations need careful handling
```

### Blue-Green with Docker Compose + Nginx

```yaml
# docker-compose.yml
version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app-blue
      - app-green

  app-blue:
    image: myapp:v1.0.0
    deploy:
      replicas: 3

  app-green:
    image: myapp:v2.0.0
    deploy:
      replicas: 3
```

```nginx
# nginx.conf — point to blue (current)
upstream app {
    server app-blue:3000;
    # server app-green:3000;  # uncomment to switch
}

server {
    listen 80;
    location / {
        proxy_pass http://app;
    }
}
```

```bash
# Deployment workflow:
# 1. Deploy green with new version
$ docker compose up -d app-green

# 2. Test green directly
$ curl http://app-green:3000/health

# 3. Switch nginx to green
$ sed -i 's/app-blue/app-green/' nginx.conf
$ docker compose exec nginx nginx -s reload

# 4. Verify traffic goes to green
$ curl http://localhost/version
# v2.0.0

# 5. If problems, switch back to blue
$ sed -i 's/app-green/app-blue/' nginx.conf
$ docker compose exec nginx nginx -s reload

# 6. Once stable, remove blue
$ docker compose stop app-blue
```

---

## 29.8 Canary Deployments

```
# Canary: Route a small percentage of traffic to the new version
# Gradually increase if no errors detected
#
# Traffic split:
#   Phase 1: 95% v1, 5% v2
#   Phase 2: 80% v1, 20% v2
#   Phase 3: 50% v1, 50% v2
#   Phase 4: 0% v1, 100% v2
```

### Canary with Nginx Weighted Upstream

```nginx
# nginx.conf — 90% to v1, 10% to v2
upstream app {
    server app-v1:3000 weight=9;
    server app-v2:3000 weight=1;
}

server {
    listen 80;
    location / {
        proxy_pass http://app;
    }
}
```

### Canary with Docker Swarm

```bash
# Start with 10 replicas of v1
$ docker service create --name api --replicas 10 myapp:v1.0.0

# Canary: Update 1 replica to v2 (10% canary)
$ docker service update --image myapp:v2.0.0 \
    --update-parallelism 1 \
    --update-delay 0s \
    --update-failure-action pause \
    api

# After updating 1 task, pause and monitor
# Check error rates, latency, logs for the canary task

# If canary is healthy, continue the rollout
$ docker service update --image myapp:v2.0.0 api

# If canary fails, rollback
$ docker service rollback api
```

### Canary with Traefik

```yaml
# docker-compose.yml with Traefik canary
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  app-stable:
    image: myapp:v1.0.0
    deploy:
      replicas: 3
    labels:
      - "traefik.http.routers.app.rule=Host(`app.example.com`)"
      - "traefik.http.services.app-stable.loadbalancer.server.port=3000"
      - "traefik.http.services.app.weighted.services.app-stable.weight=90"

  app-canary:
    image: myapp:v2.0.0
    deploy:
      replicas: 1
    labels:
      - "traefik.http.services.app-canary.loadbalancer.server.port=3000"
      - "traefik.http.services.app.weighted.services.app-canary.weight=10"
```

---

## 29.9 Docker Compose in Production

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  api:
    image: registry.com/myapp:v1.2.3    # Specific tag, never :latest
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      api:
        condition: service_healthy
    networks:
      - frontend

volumes:
  db-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt

networks:
  frontend:
  backend:
    internal: true    # No external access to backend network
```

---

## 29.10 Reverse Proxy Patterns (Nginx, Traefik)

### Nginx as Reverse Proxy

```nginx
# nginx.conf — production reverse proxy
upstream api_servers {
    least_conn;                    # Load balancing algorithm
    server api:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name app.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://api_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    location /health {
        access_log off;
        proxy_pass http://api_servers/health;
    }
}
```

### Traefik as Reverse Proxy (Auto-Discovery)

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  api:
    image: myapp:v1.0.0
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.example.com`)"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=3000"
      - "traefik.http.services.api.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.api.loadbalancer.healthcheck.interval=10s"
```

---

## 29.11 Zero-Downtime Deployment Workflow

```bash
# Complete zero-downtime deployment script
#!/bin/bash
set -euo pipefail

IMAGE="registry.com/myapp"
NEW_TAG="$1"
SERVICE="api"

echo "1. Pull new image"
docker pull ${IMAGE}:${NEW_TAG}

echo "2. Run smoke tests against new image"
docker run --rm ${IMAGE}:${NEW_TAG} npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Aborting deployment."
    exit 1
fi

echo "3. Update service with rolling update"
docker service update \
    --image ${IMAGE}:${NEW_TAG} \
    --update-parallelism 1 \
    --update-delay 30s \
    --update-order start-first \
    --update-failure-action rollback \
    ${SERVICE}

echo "4. Wait for rollout to complete"
docker service ps ${SERVICE} --filter desired-state=running \
    --format '{{.CurrentState}}'

echo "5. Verify health"
sleep 10
HEALTHY=$(docker service ps ${SERVICE} --filter desired-state=running \
    --format '{{.CurrentState}}' | grep -c "Running")
TOTAL=$(docker service inspect ${SERVICE} --format '{{.Spec.Mode.Replicated.Replicas}}')

if [ "$HEALTHY" -eq "$TOTAL" ]; then
    echo "Deployment successful: ${HEALTHY}/${TOTAL} tasks healthy"
else
    echo "Deployment issue: ${HEALTHY}/${TOTAL} tasks healthy"
    echo "Rolling back..."
    docker service rollback ${SERVICE}
    exit 1
fi
```

---

## 29.12 Common Errors and Troubleshooting

### Error 1: Container keeps restarting (restart loop)

```bash
$ docker inspect --format '{{.RestartCount}}' myapp
# 47

# Check why it's crashing
$ docker logs --tail 50 myapp

# Common causes:
#   - Missing environment variable
#   - Database not ready (use depends_on + healthcheck)
#   - Port already in use
#   - Insufficient memory (OOM killed)
$ docker inspect --format '{{.State.OOMKilled}}' myapp
```

### Error 2: Rolling update stuck

```bash
$ docker service ps api
# Shows tasks in "Pending" or "Rejected" state

# Common causes:
#   - Image doesn't exist in registry
#   - Health check failing on new version
#   - Insufficient resources on nodes

# Force rollback
$ docker service rollback api
```

### Error 3: Health check always failing

```bash
# Debug: Run the health check command manually
$ docker exec myapp curl -f http://localhost:3000/health
# Check if the endpoint exists and responds

# Common causes:
#   - App not listening on expected port
#   - Health endpoint not implemented
#   - start-period too short (app not ready yet)
```

---

## Module 29 Summary

- Use the **production readiness checklist** before deploying any container
- **Restart policies**: use `unless-stopped` for production services
- Set **memory limits** (`--memory`), **CPU limits** (`--cpus`), and **PID limits** (`--pids-limit`)
- **Health checks** drive load balancer routing, rolling updates, and automatic restarts
- Applications must handle **SIGTERM** for graceful shutdown; use exec form CMD (not shell form)
- **Rolling updates** in Swarm: use `--update-order start-first` for zero-downtime
- **Blue-green**: run two environments, switch traffic atomically via load balancer
- **Canary**: route small percentage of traffic to new version, gradually increase
- Docker Compose in production: specific tags, resource limits, health checks, log rotation, read-only rootfs
- **Nginx** and **Traefik** are the standard reverse proxy patterns for containerized apps
- Traefik auto-discovers containers via Docker labels and handles TLS with Let's Encrypt

---

**Previous Module: [Module 28 - CI/CD with Docker](module-28-cicd-docker.md)**

**Next Module: [Module 30 - Debugging and Troubleshooting](module-30-debugging-troubleshooting.md)**
