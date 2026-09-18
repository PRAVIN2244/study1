# Module 32: Enterprise Architecture and Capstone Project

This final module covers enterprise-grade Docker architecture patterns,
compliance frameworks, cost optimization, VM-to-container migration,
and a capstone project that ties together everything from modules 1-31.

### Topics Covered

```
32.1  Enterprise Docker Architecture Patterns
32.2  High Availability Reference Architecture
32.3  Multi-Region and Disaster Recovery
32.4  Compliance and Regulatory Frameworks
32.5  CIS Docker Benchmark
32.6  Cost Optimization Strategies
32.7  VM-to-Container Migration Strategy
32.8  Microservices Decomposition Patterns
32.9  Service Mesh with Docker (Consul Connect, Linkerd)
32.10 Capstone Project: Production E-Commerce Platform
32.11 Capstone: Infrastructure and Deployment
32.12 Course Conclusion and Learning Path
```

---

## 32.1 Enterprise Docker Architecture Patterns

### Pattern 1: Single Host (Development / Small Apps)

```
┌─────────────────────────────────────────────────────────────────┐
│  Single Host                                                    │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │  nginx   │  │  app     │  │  db      │                     │
│  │  (proxy) │─▶│  (api)   │─▶│ (postgres)│                    │
│  └──────────┘  └──────────┘  └──────────┘                     │
│       │                            │                            │
│       ▼                            ▼                            │
│  Port 80/443                  Volume: db-data                  │
│                                                                 │
│  Tool: Docker Compose                                          │
│  Scale: 1-100 req/sec                                          │
│  HA: None (single point of failure)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern 2: Docker Swarm Cluster (Medium Scale)

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Swarm Cluster                                          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Manager 1   │  │ Manager 2   │  │ Manager 3   │            │
│  │ (leader)    │  │ (follower)  │  │ (follower)  │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐            │
│  │ Worker 1    │  │ Worker 2    │  │ Worker 3    │            │
│  │ app×3       │  │ app×3       │  │ app×3       │            │
│  │ worker×1    │  │ worker×1    │  │ worker×1    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  External: Load Balancer → Managers (ingress routing mesh)     │
│  Storage: Shared NFS or cloud volumes                          │
│  Registry: DTR or private registry                             │
│  Scale: 100-10,000 req/sec                                     │
│  HA: Raft consensus, automatic failover                        │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern 3: Kubernetes (Large Scale / Enterprise)

```
┌─────────────────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                            │
│                                                                 │
│  Control Plane (3 nodes)                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ API      │  │ etcd     │  │ scheduler│                     │
│  │ server   │  │ cluster  │  │ + ctrl   │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
│                                                                 │
│  Worker Nodes (auto-scaling group)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Node 1   │  │ Node 2   │  │ Node 3   │  │ Node N   │      │
│  │ pods×10  │  │ pods×10  │  │ pods×10  │  │ pods×10  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  Ingress: Nginx/Traefik/ALB Ingress Controller                │
│  Storage: CSI drivers (EBS, GCE PD, Azure Disk)               │
│  Registry: ECR, GCR, ACR, Harbor                              │
│  Service Mesh: Istio, Linkerd                                  │
│  Scale: 10,000-1,000,000+ req/sec                              │
│  HA: etcd consensus, pod anti-affinity, PDB                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 32.2 High Availability Reference Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  PRODUCTION HA ARCHITECTURE                                    │
│                                                                 │
│  Internet                                                      │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Cloud Load Balancer (ALB / NLB / HAProxy)          │      │
│  │  Health checks → removes unhealthy backends         │      │
│  └──────────────────────┬───────────────────────────────┘      │
│                         │                                       │
│         ┌───────────────┼───────────────┐                      │
│         ▼               ▼               ▼                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ App Node 1 │  │ App Node 2 │  │ App Node 3 │               │
│  │ nginx      │  │ nginx      │  │ nginx      │               │
│  │ api ×2     │  │ api ×2     │  │ api ×2     │               │
│  │ worker ×1  │  │ worker ×1  │  │ worker ×1  │               │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘               │
│        │               │               │                       │
│        └───────────────┬┘───────────────┘                      │
│                        │                                        │
│  ┌─────────────────────┼────────────────────────────────┐      │
│  │  Data Tier (managed services preferred)              │      │
│  │                                                      │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │      │
│  │  │ DB       │  │ Redis    │  │ Message  │          │      │
│  │  │ Primary  │  │ Cluster  │  │ Queue    │          │      │
│  │  │ + Replica│  │ (3 nodes)│  │ (RabbitMQ│          │      │
│  │  └──────────┘  └──────────┘  │  cluster)│          │      │
│  │                               └──────────┘          │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  Monitoring: Prometheus + Grafana + Alertmanager               │
│  Logging: EFK stack (Elasticsearch + Fluent Bit + Kibana)      │
│  CI/CD: GitHub Actions → Build → Scan → Push → Deploy         │
│  Secrets: Docker Secrets / Vault / AWS Secrets Manager         │
└─────────────────────────────────────────────────────────────────┘
```

### Key HA Principles

```
# 1. No single point of failure
#    - Multiple app instances across nodes
#    - Database replication (primary + replica)
#    - Load balancer with health checks
#
# 2. Stateless application tier
#    - Sessions stored in Redis, not in container memory
#    - File uploads go to object storage (S3), not local disk
#    - Any container can handle any request
#
# 3. Data tier separation
#    - Use managed database services when possible
#    - If self-hosted: run on dedicated nodes with volumes
#    - Regular automated backups
#
# 4. Health checks at every layer
#    - Load balancer → app health check
#    - Docker → container health check
#    - App → dependency health checks (DB, Redis, etc.)
```

---

## 32.3 Multi-Region and Disaster Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│  MULTI-REGION ARCHITECTURE                                     │
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │  Region A (Primary)  │    │  Region B (DR)       │          │
│  │                      │    │                      │          │
│  │  App Cluster         │    │  App Cluster         │          │
│  │  (3 nodes)           │    │  (3 nodes)           │          │
│  │                      │    │                      │          │
│  │  DB Primary ─────────┼───▶│  DB Replica          │          │
│  │  Registry (DTR) ─────┼───▶│  Registry (DTR)      │          │
│  │                      │    │                      │          │
│  └──────────────────────┘    └──────────────────────┘          │
│                                                                 │
│  DNS: Route53 / CloudFlare with health-based routing           │
│  RPO: < 1 minute (async replication)                           │
│  RTO: < 5 minutes (DNS failover)                               │
└─────────────────────────────────────────────────────────────────┘
```

### DR Runbook for Docker Swarm

```bash
# 1. Regular backups (automated, daily)
$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    -v /backup:/backup alpine tar czf /backup/swarm-$(date +%Y%m%d).tar.gz \
    /var/lib/docker/swarm

# 2. Registry replication
# DTR: Configure replication in DTR UI → System → Replication
# Harbor: Configure replication rules between registries

# 3. Failover procedure
#    a. Verify Region B cluster is healthy
#    b. Promote DB replica to primary
#    c. Update DNS to point to Region B
#    d. Verify all services are running
#    e. Monitor for errors

# 4. Failback procedure
#    a. Sync data from Region B back to Region A
#    b. Verify Region A cluster is healthy
#    c. Switch DNS back to Region A
#    d. Demote Region B DB back to replica
```

---

## 32.4 Compliance and Regulatory Frameworks

```
┌──────────────────┬──────────────────────────────────────────────┐
│ Framework        │ Docker-Relevant Requirements                 │
├──────────────────┼──────────────────────────────────────────────┤
│ SOC 2            │ Access controls, audit logging, encryption,  │
│                  │ change management, vulnerability scanning    │
├──────────────────┼──────────────────────────────────────────────┤
│ PCI DSS          │ Network segmentation, encryption at rest     │
│                  │ and in transit, access logging, patching     │
├──────────────────┼──────────────────────────────────────────────┤
│ HIPAA            │ PHI encryption, access controls, audit       │
│                  │ trails, BAA with cloud providers             │
├──────────────────┼──────────────────────────────────────────────┤
│ GDPR             │ Data residency, right to deletion,           │
│                  │ encryption, access logging                   │
├──────────────────┼──────────────────────────────────────────────┤
│ FedRAMP          │ FIPS 140-2 encryption, continuous            │
│                  │ monitoring, incident response                │
└──────────────────┴──────────────────────────────────────────────┘
```

### Docker Compliance Checklist

```
# Image Supply Chain
☐ Use signed images (Docker Content Trust)
☐ Scan all images for vulnerabilities before deployment
☐ Use private registry with access controls
☐ Generate SBOM for all production images
☐ Pin base image digests (not tags)

# Runtime Security
☐ Run containers as non-root
☐ Drop all capabilities, add only needed
☐ Use read-only root filesystem
☐ Set memory and CPU limits
☐ Enable seccomp and AppArmor/SELinux
☐ Use user namespaces (rootless Docker)

# Network Security
☐ Use encrypted overlay networks
☐ Segment networks (frontend/backend/data)
☐ TLS for all external communication
☐ No --net=host in production

# Audit and Logging
☐ Centralized logging (EFK/ELK)
☐ Docker event audit trail
☐ Registry access logs
☐ Container lifecycle logging

# Data Protection
☐ Encrypt volumes at rest
☐ Use Docker secrets for sensitive data
☐ Regular backup and restore testing
☐ Data retention policies
```

---

## 32.5 CIS Docker Benchmark

The Center for Internet Security (CIS) Docker Benchmark provides
security configuration guidelines.

### Running the CIS Benchmark

```bash
# Docker Bench for Security — automated CIS benchmark checker
$ docker run --rm --net host --pid host \
    --userns host --cap-add audit_control \
    -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
    -v /etc:/etc:ro \
    -v /usr/bin/containerd:/usr/bin/containerd:ro \
    -v /usr/bin/runc:/usr/bin/runc:ro \
    -v /usr/lib/systemd:/usr/lib/systemd:ro \
    -v /var/lib:/var/lib:ro \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    docker/docker-bench-security

# Output categories:
# [PASS] 1.1 - Ensure a separate partition for containers
# [WARN] 2.1 - Ensure network traffic is restricted
# [FAIL] 4.1 - Ensure a user for the container has been created
# [INFO] 5.1 - Ensure AppArmor Profile is enabled
```

### Key CIS Recommendations

```
# Host Configuration
1.1  Separate partition for /var/lib/docker
1.2  Harden the host OS
1.3  Keep Docker up to date
1.4  Only allow trusted users in the docker group

# Daemon Configuration
2.1  Restrict network traffic between containers
2.2  Set logging level to info
2.3  Allow Docker to make changes to iptables
2.4  Do not use insecure registries
2.5  Enable Docker Content Trust
2.6  Configure TLS authentication for Docker daemon

# Container Runtime
4.1  Create a user for the container (USER directive)
4.2  Use trusted base images
4.5  Enable Content Trust for image pulls
4.6  Add HEALTHCHECK instruction

# Container Runtime (Security)
5.1  Do not disable AppArmor
5.2  Set SELinux security options
5.3  Restrict Linux kernel capabilities
5.4  Do not use privileged containers
5.7  Do not map privileged ports
5.10 Limit memory for containers
5.11 Set CPU priority for containers
5.12 Mount container rootfs as read-only
5.25 Restrict container from acquiring additional privileges
```

---

## 32.6 Cost Optimization Strategies

```
┌──────────────────────────────────────────────────────────────────┐
│  DOCKER COST OPTIMIZATION                                       │
│                                                                  │
│  1. IMAGE SIZE REDUCTION                                        │
│     - Use alpine/distroless base images                         │
│     - Multi-stage builds (discard build tools)                  │
│     - Remove unnecessary packages and files                     │
│     Impact: 50-90% reduction in registry storage costs          │
│                                                                  │
│  2. RESOURCE RIGHT-SIZING                                       │
│     - Set memory limits based on actual usage (docker stats)    │
│     - Set CPU limits to prevent noisy neighbors                 │
│     - Use reservations for guaranteed resources                 │
│     Impact: 30-60% reduction in compute costs                   │
│                                                                  │
│  3. BUILD CACHE OPTIMIZATION                                    │
│     - Use BuildKit cache mounts                                 │
│     - Registry-based cache for CI/CD                            │
│     - Order Dockerfile layers by change frequency               │
│     Impact: 50-80% reduction in CI/CD build time and costs      │
│                                                                  │
│  4. REGISTRY MANAGEMENT                                         │
│     - Implement image retention policies                        │
│     - Run garbage collection on DTR/Harbor                      │
│     - Delete untagged and old images                            │
│     Impact: 40-70% reduction in registry storage costs          │
│                                                                  │
│  5. INFRASTRUCTURE OPTIMIZATION                                 │
│     - Use ARM instances (Graviton) — 20-40% cheaper            │
│     - Spot/preemptible instances for CI/CD                      │
│     - Auto-scaling based on actual load                         │
│     Impact: 30-60% reduction in infrastructure costs            │
└──────────────────────────────────────────────────────────────────┘
```

### Image Retention Policy Script

```bash
#!/bin/bash
# Delete images older than 30 days from registry
REGISTRY="registry.example.com"
REPO="myapp"
CUTOFF=$(date -d "30 days ago" +%s)

# List tags and their creation dates
for TAG in $(curl -s "https://${REGISTRY}/v2/${REPO}/tags/list" | jq -r '.tags[]'); do
    CREATED=$(curl -s "https://${REGISTRY}/v2/${REPO}/manifests/${TAG}" \
        | jq -r '.history[0].v1Compatibility' | jq -r '.created')
    CREATED_TS=$(date -d "$CREATED" +%s)

    if [ "$CREATED_TS" -lt "$CUTOFF" ]; then
        echo "Deleting ${REPO}:${TAG} (created: ${CREATED})"
        DIGEST=$(curl -sI -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
            "https://${REGISTRY}/v2/${REPO}/manifests/${TAG}" | grep Docker-Content-Digest | awk '{print $2}' | tr -d '\r')
        curl -X DELETE "https://${REGISTRY}/v2/${REPO}/manifests/${DIGEST}"
    fi
done
```

---

## 32.7 VM-to-Container Migration Strategy

### Migration Assessment Framework

```
┌──────────────────────────────────────────────────────────────────┐
│  VM-TO-CONTAINER MIGRATION DECISION MATRIX                      │
│                                                                  │
│  Good candidates for containerization:                          │
│  ✓ Stateless web applications                                  │
│  ✓ REST APIs and microservices                                  │
│  ✓ Background workers and queue processors                     │
│  ✓ Batch processing jobs                                       │
│  ✓ 12-factor apps                                              │
│                                                                  │
│  Challenging but possible:                                      │
│  ~ Stateful applications (need volume strategy)                │
│  ~ Legacy monoliths (may need refactoring)                     │
│  ~ Applications with specific OS dependencies                  │
│                                                                  │
│  Poor candidates (keep on VMs):                                │
│  ✗ Applications requiring GUI                                  │
│  ✗ Applications needing kernel modules                         │
│  ✗ Windows-only applications (limited Linux container support) │
│  ✗ Applications with hardware dependencies (USB, GPU*)         │
│  ✗ Real-time systems requiring deterministic scheduling        │
│                                                                  │
│  * GPU containers are possible with nvidia-docker              │
└──────────────────────────────────────────────────────────────────┘
```

### Migration Steps

```
# Phase 1: Assessment (1-2 weeks)
#   - Inventory all applications on VMs
#   - Classify each as: containerize / refactor / keep on VM
#   - Identify dependencies (databases, file shares, etc.)
#   - Map network connections between services

# Phase 2: Containerize (2-4 weeks per app)
#   1. Create Dockerfile
#      - Start with a base image matching the VM's OS
#      - Install dependencies (from VM's package list)
#      - Copy application code
#      - Set entrypoint
#   2. Externalize configuration
#      - Move config files to environment variables
#      - Move secrets to Docker secrets or Vault
#   3. Externalize state
#      - Move data to volumes
#      - Move sessions to Redis
#      - Move file uploads to object storage
#   4. Test in Docker Compose locally
#   5. Test in staging environment

# Phase 3: Deploy (1-2 weeks per app)
#   - Set up CI/CD pipeline
#   - Deploy to production (Docker Compose, Swarm, or K8s)
#   - Monitor for issues
#   - Decommission VM after validation period

# Phase 4: Optimize (ongoing)
#   - Reduce image sizes
#   - Implement health checks
#   - Set resource limits
#   - Add monitoring and alerting
```

### Example: Migrating a Java App from VM to Container

```bash
# On the VM, the app runs as:
#   java -jar /opt/myapp/app.jar \
#     --spring.datasource.url=jdbc:postgresql://db:5432/mydb \
#     --server.port=8080

# Step 1: Create Dockerfile
```

```dockerfile
FROM eclipse-temurin:17-jre-alpine
RUN addgroup -g 1001 app && adduser -u 1001 -G app -s /bin/sh -D app
WORKDIR /app
COPY target/app.jar ./app.jar
USER app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
```

```yaml
# Step 2: Docker Compose
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/mydb
      SPRING_DATASOURCE_USERNAME: myuser
      SPRING_DATASOURCE_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser"]
```

---

## 32.8 Microservices Decomposition Patterns

### Strangler Fig Pattern

```
# Gradually replace a monolith by routing requests to new services
#
# Phase 1: Monolith handles everything
#   nginx → monolith (all routes)
#
# Phase 2: Extract first service
#   nginx → /api/users → user-service (new)
#   nginx → /*         → monolith (everything else)
#
# Phase 3: Extract more services
#   nginx → /api/users    → user-service
#   nginx → /api/orders   → order-service
#   nginx → /api/payments → payment-service
#   nginx → /*            → monolith (shrinking)
#
# Phase 4: Monolith fully decomposed
#   nginx → all routes → individual microservices
```

```nginx
# nginx.conf — Strangler Fig routing
upstream monolith { server monolith:8080; }
upstream user_service { server user-service:3000; }
upstream order_service { server order-service:3001; }

server {
    listen 80;

    # New microservices
    location /api/users { proxy_pass http://user_service; }
    location /api/orders { proxy_pass http://order_service; }

    # Everything else goes to the monolith
    location / { proxy_pass http://monolith; }
}
```

### Database Per Service Pattern

```
# Each microservice owns its data — no shared databases
#
# ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
# │ User Service │  │ Order Service│  │ Payment Svc  │
# │              │  │              │  │              │
# │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
# │ │ Users DB │ │  │ │ Orders DB│ │  │ │Payments DB│ │
# │ │(Postgres)│ │  │ │ (MongoDB)│ │  │ │ (Postgres)│ │
# │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
# └──────────────┘  └──────────────┘  └──────────────┘
#
# Communication between services: REST API or message queue
# NOT direct database queries across services
```

---

## 32.9 Service Mesh with Docker

### What is a Service Mesh?

```
# A service mesh handles service-to-service communication:
#   - Mutual TLS (mTLS) — encrypted, authenticated connections
#   - Load balancing — intelligent request routing
#   - Circuit breaking — prevent cascade failures
#   - Observability — distributed tracing, metrics
#   - Retries and timeouts — automatic retry with backoff
#
# The mesh runs as sidecar proxies alongside each service:
#
# ┌──────────────────────────────────────────────────────┐
# │  Service A Container                                 │
# │  ┌──────────┐  ┌──────────────┐                     │
# │  │  App     │──│  Sidecar     │──── mTLS ────┐      │
# │  │  Process │  │  Proxy       │              │      │
# │  └──────────┘  └──────────────┘              │      │
# └──────────────────────────────────────────────│──────┘
#                                                │
# ┌──────────────────────────────────────────────│──────┐
# │  Service B Container                         │      │
# │  ┌──────────┐  ┌──────────────┐              │      │
# │  │  App     │──│  Sidecar     │──── mTLS ────┘      │
# │  │  Process │  │  Proxy       │                     │
# │  └──────────┘  └──────────────┘                     │
# └──────────────────────────────────────────────────────┘
```

### Service Mesh Options

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Mesh         │ Description                                      │
├──────────────┼──────────────────────────────────────────────────┤
│ Istio        │ Most feature-rich. Envoy sidecar proxy.          │
│              │ Complex setup. Best for large Kubernetes.         │
├──────────────┼──────────────────────────────────────────────────┤
│ Linkerd      │ Lightweight, simple. Rust-based proxy.           │
│              │ Easy to install. Good for getting started.       │
├──────────────┼──────────────────────────────────────────────────┤
│ Consul       │ HashiCorp. Works with Docker Swarm and K8s.      │
│ Connect      │ Built-in service discovery and KV store.         │
├──────────────┼──────────────────────────────────────────────────┤
│ Traefik      │ Not a full mesh, but handles routing, TLS,       │
│ Mesh         │ and load balancing. Simple for Docker Compose.   │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 32.10 Capstone Project: Production E-Commerce Platform

This capstone project ties together modules 1-31. You will build
and deploy a production-grade e-commerce platform.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  E-COMMERCE PLATFORM ARCHITECTURE                              │
│                                                                 │
│  Internet                                                      │
│      │                                                          │
│      ▼                                                          │
│  ┌──────────┐                                                  │
│  │  Traefik │  (TLS termination, routing, load balancing)      │
│  └────┬─────┘                                                  │
│       │                                                         │
│  ┌────┼──────────────────────────────────────────────────┐     │
│  │    ├──▶ Frontend (React SPA, nginx)                   │     │
│  │    ├──▶ API Gateway (Node.js, Express)                │     │
│  │    │       ├──▶ Product Service (Python, FastAPI)      │     │
│  │    │       ├──▶ Order Service (Go)                     │     │
│  │    │       ├──▶ User Service (Node.js)                 │     │
│  │    │       └──▶ Payment Service (Java, Spring Boot)    │     │
│  │    │                                                   │     │
│  │    ├──▶ Redis (session cache, product cache)           │     │
│  │    ├──▶ PostgreSQL (users, orders, payments)           │     │
│  │    ├──▶ MongoDB (product catalog)                      │     │
│  │    └──▶ RabbitMQ (order events, notifications)         │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  Monitoring: Prometheus + Grafana + Alertmanager               │
│  Logging: Fluent Bit → Elasticsearch → Kibana                  │
│  CI/CD: GitHub Actions → Build → Scan → Push → Deploy          │
└─────────────────────────────────────────────────────────────────┘
```

### Services Breakdown

```
┌──────────────────┬──────────┬──────────────────────────────────┐
│ Service          │ Language │ Responsibilities                 │
├──────────────────┼──────────┼──────────────────────────────────┤
│ Frontend         │ React    │ SPA served by nginx              │
│ API Gateway      │ Node.js  │ Auth, rate limiting, routing     │
│ Product Service  │ Python   │ CRUD products, search, catalog   │
│ Order Service    │ Go       │ Order lifecycle, inventory check │
│ User Service     │ Node.js  │ Registration, auth, profiles     │
│ Payment Service  │ Java     │ Payment processing, refunds      │
└──────────────────┴──────────┴──────────────────────────────────┘
```

### Project Directory Structure

```
ecommerce-platform/
├── docker-compose.yml          # Base compose file
├── docker-compose.prod.yml     # Production overrides
├── docker-compose.monitoring.yml  # Monitoring stack
├── .env.example                # Environment template
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions pipeline
├── services/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── src/
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   └── src/
│   ├── product-service/
│   │   ├── Dockerfile
│   │   └── app/
│   ├── order-service/
│   │   ├── Dockerfile
│   │   └── cmd/
│   ├── user-service/
│   │   ├── Dockerfile
│   │   └── src/
│   └── payment-service/
│       ├── Dockerfile
│       └── src/
├── infrastructure/
│   ├── traefik/
│   │   └── traefik.yml
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alert-rules.yml
│   ├── grafana/
│   │   └── dashboards/
│   ├── fluent-bit/
│   │   └── fluent-bit.conf
│   └── postgres/
│       └── init.sql
└── scripts/
    ├── deploy.sh
    ├── backup.sh
    └── healthcheck.sh
```

---

## 32.11 Capstone: Infrastructure and Deployment

### docker-compose.yml (Base)

```yaml
version: "3.8"

services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--metrics.prometheus=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - frontend

  frontend:
    build: ./services/frontend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`shop.example.com`)"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
    networks:
      - frontend

  api-gateway:
    build: ./services/api-gateway
    environment:
      - PRODUCT_SERVICE_URL=http://product-service:8000
      - ORDER_SERVICE_URL=http://order-service:8001
      - USER_SERVICE_URL=http://user-service:8002
      - REDIS_URL=redis://redis:6379
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`shop.example.com`) && PathPrefix(`/api`)"
      - "traefik.http.services.api.loadbalancer.server.port=3000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - frontend
      - backend

  product-service:
    build: ./services/product-service
    environment:
      - MONGODB_URI=mongodb://mongo:27017/products
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - backend

  order-service:
    build: ./services/order-service
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@postgres:5432/orders
      - RABBITMQ_URL=amqp://rabbitmq:5672
    healthcheck:
      test: ["CMD", "/app/healthcheck"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - backend

  user-service:
    build: ./services/user-service
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@postgres:5432/users
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
    secrets:
      - jwt_secret
    networks:
      - backend

  payment-service:
    build: ./services/payment-service
    environment:
      - DATABASE_URL=jdbc:postgresql://postgres:5432/payments
      - STRIPE_KEY_FILE=/run/secrets/stripe_key
    secrets:
      - stripe_key
    networks:
      - backend

  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
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

  mongo:
    image: mongo:7
    volumes:
      - mongo-data:/data/db
    networks:
      - backend

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - backend

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - backend

volumes:
  postgres-data:
  mongo-data:
  redis-data:
  rabbitmq-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  stripe_key:
    file: ./secrets/stripe_key.txt

networks:
  frontend:
  backend:
    internal: true
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: E-Commerce CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [frontend, api-gateway, product-service, order-service, user-service, payment-service]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and test ${{ matrix.service }}
        run: |
          docker buildx build \
            --target test \
            --cache-from type=gha,scope=${{ matrix.service }} \
            --cache-to type=gha,scope=${{ matrix.service }},mode=max \
            services/${{ matrix.service }}/

  scan:
    needs: build-and-test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [frontend, api-gateway, product-service, order-service, user-service, payment-service]
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t ${{ matrix.service }}:scan services/${{ matrix.service }}/
      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ matrix.service }}:scan
          exit-code: '1'
          severity: 'CRITICAL'

  deploy:
    needs: [build-and-test, scan]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          # Push all images and deploy
          echo "Deploying to production..."
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh
set -euo pipefail

TAG="${1:-latest}"
REGISTRY="registry.example.com"
SERVICES="frontend api-gateway product-service order-service user-service payment-service"

echo "=== Building and pushing images ==="
for SVC in $SERVICES; do
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t ${REGISTRY}/${SVC}:${TAG} \
        --push \
        services/${SVC}/
done

echo "=== Deploying stack ==="
export TAG
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml ecommerce

echo "=== Verifying deployment ==="
sleep 30
for SVC in $SERVICES; do
    STATUS=$(docker service ps ecommerce_${SVC} --format '{{.CurrentState}}' | head -1)
    echo "${SVC}: ${STATUS}"
done
```

---

## 32.12 Course Conclusion and Learning Path

### What You've Learned (Modules 1-32)

```
┌─────────────────────────────────────────────────────────────────┐
│  BEGINNER (Modules 1-6)                                        │
│  Docker fundamentals, installation, images, containers,        │
│  Dockerfiles, Docker Compose                                   │
├─────────────────────────────────────────────────────────────────┤
│  INTERMEDIATE (Modules 7-12)                                   │
│  Networking, volumes, full-stack projects, security basics,    │
│  orchestration with Swarm, image optimization                  │
├─────────────────────────────────────────────────────────────────┤
│  ADVANCED (Modules 13-24)                                      │
│  Daemon configuration, content trust, secrets, network         │
│  namespaces, overlay networks, storage drivers, Raft,          │
│  security deep dive, Docker Enterprise, disaster recovery,     │
│  Kubernetes fundamentals and storage/networking                 │
├─────────────────────────────────────────────────────────────────┤
│  EXPERT (Modules 25-32)                                        │
│  Docker internals (runc, containerd, OCI), BuildKit,           │
│  logging/monitoring/observability, CI/CD pipelines,            │
│  production deployment patterns, debugging/troubleshooting,    │
│  DinD/rootless/Podman/Wasm, enterprise architecture            │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Certifications

```
1. Docker Certified Associate (DCA)
   - Covered by: Modules 1-24
   - Focus: Installation, images, networking, storage,
     security, orchestration, Docker Enterprise

2. Certified Kubernetes Administrator (CKA)
   - Foundation: Modules 23-24
   - Additional study: Kubernetes-specific curriculum

3. AWS/GCP/Azure Container Certifications
   - Foundation: Modules 25-32
   - Additional study: Cloud-specific container services
```

### Next Steps After This Course

```
# 1. Practice
#    - Complete the capstone project (Module 32)
#    - Containerize your own applications
#    - Set up a home lab with Docker Swarm or K8s
#
# 2. Deepen Kubernetes knowledge
#    - CKA certification path
#    - Helm chart development
#    - Operators and custom controllers
#
# 3. Explore advanced topics
#    - eBPF for container observability (Cilium, Falco)
#    - GitOps with ArgoCD or Flux
#    - Policy engines (OPA/Gatekeeper, Kyverno)
#    - Supply chain security (Sigstore, cosign, in-toto)
#
# 4. Stay current
#    - Docker blog: https://www.docker.com/blog/
#    - CNCF landscape: https://landscape.cncf.io/
#    - Container security advisories
```

---

## Module 32 Summary

- Enterprise Docker architectures range from single-host Compose to multi-region Kubernetes
- **High availability** requires: no SPOF, stateless app tier, managed data tier, health checks everywhere
- **Multi-region DR** uses database replication, registry mirroring, and DNS-based failover
- **Compliance** (SOC 2, PCI DSS, HIPAA) requires signed images, scanning, encryption, audit logging
- **CIS Docker Benchmark** provides automated security configuration checks
- **Cost optimization**: smaller images, right-sized resources, build caching, image retention policies
- **VM-to-container migration**: assess → containerize → externalize state → deploy → optimize
- **Strangler Fig pattern** gradually replaces monoliths with microservices behind a reverse proxy
- **Service meshes** (Istio, Linkerd, Consul) handle mTLS, load balancing, and observability
- The **capstone project** demonstrates a production e-commerce platform with 6 microservices, 4 data stores, monitoring, logging, CI/CD, and security
- This course covers Docker from zero to Senior DevOps Architect level across 32 modules

---

**Previous Module: [Module 31 - Docker-in-Docker, Rootless Docker, and Edge Cases](module-31-dind-rootless-edge.md)**

**This is the final module of the course.**
