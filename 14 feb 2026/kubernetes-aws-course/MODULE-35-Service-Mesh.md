# MODULE 35: Microservices Patterns & Service Mesh (Istio)

---

## 35.1 Microservices Patterns on Kubernetes

### Achieving Unity Between Microservices

Microservices need to discover, communicate with, and depend on each other reliably. Kubernetes provides built-in mechanisms for this.

#### Service Discovery

Every Service gets a DNS name: `<service-name>.<namespace>.svc.cluster.local`

```yaml
# frontend connects to backend via DNS — no hardcoded IPs
env:
- name: BACKEND_URL
  value: "http://backend-service.default.svc.cluster.local:8080"
- name: DATABASE_URL
  value: "postgresql://postgres-service.database.svc.cluster.local:5432/mydb"
```

#### Communication Patterns

| Pattern | Mechanism | Use Case |
|---|---|---|
| **Synchronous (HTTP/gRPC)** | ClusterIP Service | API calls between services |
| **Asynchronous (messaging)** | RabbitMQ/Kafka as StatefulSet | Event-driven, decoupled services |
| **Service mesh** | Istio/Linkerd sidecar | mTLS, traffic management, observability |

#### Health Checks for Microservices

Every microservice should expose health endpoints:

```yaml
# Each microservice deployment should have:
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

The readiness probe ensures traffic is only sent to pods that have established database connections, loaded caches, etc.

#### Shared Configuration

```bash
# Create shared config for all microservices
kubectl create configmap shared-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=TRACING_ENABLED=true \
  --from-literal=METRICS_PORT=9090

# Each microservice references it
# envFrom:
# - configMapRef:
#     name: shared-config
```

#### Inter-Service Network Policies

Restrict which services can talk to each other:

```yaml
# Only allow frontend → backend, deny everything else
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-allow-frontend
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
```

#### Microservices Deployment Strategy

```yaml
# Deploy all microservices with consistent patterns:
# 1. Namespace per environment
# 2. Resource limits on every container
# 3. Readiness + liveness probes
# 4. HPA for auto-scaling
# 5. PDB for availability during updates
# 6. NetworkPolicy for security
# 7. ConfigMaps/Secrets for configuration
# 8. Ingress for external access
```

---

## 35.2 Service Mesh — Deep Dive (Istio)

A service mesh is an infrastructure layer that handles service-to-service communication. Instead of each microservice implementing its own retry logic, mTLS, and observability, the mesh handles it transparently via sidecar proxies.

### Why Use a Service Mesh?

Without a mesh, every microservice must implement:
- TLS certificate management for encrypted communication
- Retry logic with exponential backoff
- Circuit breaking to prevent cascade failures
- Distributed tracing headers
- Traffic splitting for canary deployments

A service mesh moves all of this out of application code into the infrastructure.

```
┌──────────────────────────────────────────────────────────────┐
│  Without Service Mesh                                        │
│                                                              │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │  Frontend    │──HTTP──►│  Backend    │                     │
│  │  (app code   │  plain  │  (app code  │                     │
│  │   handles    │  text   │   handles   │                     │
│  │   retries,   │         │   TLS,      │                     │
│  │   TLS, etc.) │         │   retries)  │                     │
│  └─────────────┘         └─────────────┘                     │
│                                                              │
│  With Service Mesh (Istio)                                   │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │  Frontend Pod     │    │  Backend Pod      │                │
│  │  ┌────────────┐  │    │  ┌────────────┐  │                │
│  │  │  App       │  │    │  │  App       │  │                │
│  │  │  Container │  │    │  │  Container │  │                │
│  │  └─────┬──────┘  │    │  └─────▲──────┘  │                │
│  │        │         │    │        │         │                │
│  │  ┌─────▼──────┐  │    │  ┌─────┴──────┐  │                │
│  │  │  Envoy     │──┼─mTLS──│  Envoy     │  │                │
│  │  │  Sidecar   │  │    │  │  Sidecar   │  │                │
│  │  │  (proxy)   │  │    │  │  (proxy)   │  │                │
│  │  └────────────┘  │    │  └────────────┘  │                │
│  └──────────────────┘    └──────────────────┘                │
│                                                              │
│  The sidecar handles: mTLS, retries, circuit breaking,       │
│  tracing, metrics — app code stays simple                    │
└──────────────────────────────────────────────────────────────┘
```

### Istio Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Istio Control Plane (istiod)                                │
│  ┌────────────────────────────────────────────────────┐      │
│  │  Pilot        → Configures Envoy proxies           │      │
│  │  Citadel      → Issues TLS certificates            │      │
│  │  Galley       → Validates configuration            │      │
│  │  (All merged into single "istiod" binary)          │      │
│  └────────────────────────────────────────────────────┘      │
│       │ pushes config                                        │
│       ▼                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Envoy   │  │ Envoy   │  │ Envoy   │  │ Envoy   │        │
│  │ sidecar │  │ sidecar │  │ sidecar │  │ sidecar │        │
│  │ (pod 1) │  │ (pod 2) │  │ (pod 3) │  │ (pod 4) │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│  Data Plane                                                  │
└──────────────────────────────────────────────────────────────┘
```

### Installing Istio

```bash
# Step 1: Download Istio CLI
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH

# Step 2: Install Istio with demo profile (includes all features)
istioctl install --set profile=demo -y

# Output:
# ✔ Istio core installed
# ✔ Istiod installed
# ✔ Egress gateways installed
# ✔ Ingress gateways installed
# ✔ Installation complete

# Step 3: Verify installation
kubectl get pods -n istio-system

# Output:
# NAME                                    READY   STATUS    RESTARTS   AGE
# istio-egressgateway-5c8f9f5d7-abc12     1/1     Running   0          2m
# istio-ingressgateway-7b8c9d6e8-def34    1/1     Running   0          2m
# istiod-6f7a8b9c0-ghi56                  1/1     Running   0          2m

# Step 4: Enable automatic sidecar injection for a namespace
kubectl label namespace default istio-injection=enabled

kubectl get namespace default --show-labels

# Output:
# NAME      STATUS   AGE   LABELS
# default   Active   30d   istio-injection=enabled,...
```

### How Sidecar Injection Works

When `istio-injection=enabled` is set on a namespace, Istio's admission webhook automatically injects an Envoy sidecar container into every new pod:

```bash
# Deploy a simple app
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
  template:
    metadata:
      labels:
        app: httpbin
    spec:
      containers:
      - name: httpbin
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
EOF

# Check the pod — it has 2 containers (app + sidecar)
kubectl get pods -l app=httpbin

# Output:
# NAME                      READY   STATUS    RESTARTS   AGE
# httpbin-7b8c9d6e8-abc12   2/2     Running   0          30s
#                           ^^^
#                           2 containers: httpbin + istio-proxy

# Describe to see the injected sidecar
kubectl describe pod -l app=httpbin | grep -A2 "Container ID"

# Output:
# Containers:
#   httpbin:
#     Image: kennethreitz/httpbin
#   istio-proxy:
#     Image: docker.io/istio/proxyv2:1.20.0
```

### mTLS (Mutual TLS) — Encrypted Service-to-Service Communication

Istio automatically encrypts all traffic between pods using mTLS. Each sidecar gets a certificate from istiod (Citadel).

```yaml
# strict-mtls.yaml — Enforce mTLS for all services in a namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: default
spec:
  mtls:
    mode: STRICT    # STRICT = only mTLS allowed, PERMISSIVE = both plain + mTLS
```

```bash
kubectl apply -f strict-mtls.yaml

# Verify mTLS is active
istioctl x describe pod httpbin-7b8c9d6e8-abc12

# Output:
# Pod: httpbin-7b8c9d6e8-abc12
#    Pod Revision: default
#    Pod Ports: 80 (httpbin), 15090 (istio-proxy)
# --------------------
# Service: httpbin.default
#    Port: http 80/HTTP targets pod port 80
# --------------------
# Effective PeerAuthentication:
#    default/default (STRICT)
# Applied PeerAuthentication:
#    default/default

# Test: Try to access from a pod WITHOUT a sidecar — it fails
kubectl run test --image=busybox --rm -it -- wget -qO- http://httpbin/get

# Output:
# wget: error getting response: Connection reset by peer
# (Plain HTTP rejected because STRICT mTLS is enforced)
```

### Traffic Management — Canary Deployments

Split traffic between two versions of a service:

```yaml
# virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews                    # Kubernetes service name
  http:
  - route:
    - destination:
        host: reviews
        subset: v1             # 90% to v1
      weight: 90
    - destination:
        host: reviews
        subset: v2             # 10% to v2 (canary)
      weight: 10
---
# destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

```bash
kubectl apply -f virtual-service.yaml
kubectl apply -f destination-rule.yaml

# Verify traffic split
kubectl get virtualservice reviews -o yaml | grep -A5 "route:"

# Output:
#   http:
#   - route:
#     - destination:
#         host: reviews
#         subset: v1
#       weight: 90
#     - destination:
#         host: reviews
#         subset: v2
#       weight: 10

# Gradually shift traffic: 90/10 → 70/30 → 50/50 → 0/100
```

### Circuit Breaking — Prevent Cascade Failures

```yaml
# circuit-breaker.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: backend
spec:
  host: backend-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100          # Max TCP connections
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 10   # Max queued requests
        http2MaxRequests: 100         # Max concurrent requests
    outlierDetection:
      consecutive5xxErrors: 5        # Eject after 5 consecutive 5xx errors
      interval: 30s                  # Check every 30 seconds
      baseEjectionTime: 30s          # Eject for 30 seconds
      maxEjectionPercent: 50         # Don't eject more than 50% of endpoints
```

### Observability — Built-in Metrics and Tracing

```bash
# Istio automatically collects metrics from every sidecar

# Install Kiali (service mesh dashboard)
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

# Install Prometheus (metrics)
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/prometheus.yaml

# Install Jaeger (distributed tracing)
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml

# Access Kiali dashboard
istioctl dashboard kiali

# Kiali shows:
# - Service graph (which services talk to each other)
# - Traffic rates and error rates
# - mTLS status per connection
# - Response time percentiles
```

### Service Mesh Comparison

| Feature | Istio | Linkerd | Cilium Service Mesh |
|---|---|---|---|
| **Sidecar proxy** | Envoy | linkerd2-proxy (Rust) | No sidecar (eBPF) |
| **Resource overhead** | ~50MB per sidecar | ~10MB per sidecar | Near zero |
| **mTLS** | Yes (automatic) | Yes (automatic) | Yes (via WireGuard) |
| **Traffic splitting** | VirtualService + DestinationRule | TrafficSplit (SMI) | CiliumEnvoyConfig |
| **Complexity** | High | Low | Medium |
| **Best for** | Large enterprises, complex routing | Simplicity, low overhead | Performance-sensitive |

### Cilium — eBPF-Based Pod-to-Pod Encryption

Cilium uses eBPF (Extended Berkeley Packet Filter) to enforce network security at the kernel level, avoiding sidecar overhead. For encryption, Cilium supports both WireGuard and IPsec:

```bash
# Install Cilium with WireGuard encryption enabled
helm install cilium cilium/cilium --namespace kube-system \
  --set encryption.enabled=true \
  --set encryption.type=wireguard

# Or enable on an existing installation
cilium config set enable-wireguard true

# Verify encryption status
cilium status | grep Encryption
# Encryption:    Wireguard   [NodeEncryption: Disabled, cilium_wg0 (Pubkey: <key>, Port 51871, Peers: 2)]

# Check encryption on specific nodes
cilium encrypt status
```

**Cilium encryption modes:**

| Mode | Protocol | Performance | Use Case |
|---|---|---|---|
| WireGuard | Modern crypto (ChaCha20) | High — kernel-level, ~5% overhead | Default choice for most clusters |
| IPsec | ESP (AES-GCM) | Moderate — higher CPU usage | Required by some compliance frameworks |

**Key differences from Istio mTLS:**

| | Istio mTLS | Cilium WireGuard |
|---|---|---|
| **Layer** | L7 (application) | L3/L4 (network) |
| **Mechanism** | Sidecar proxy per pod | eBPF in kernel, no sidecar |
| **Overhead** | ~50MB per pod + latency | Near zero memory, minimal latency |
| **Scope** | Per-service policies | Node-to-node tunnel (all pod traffic) |
| **Extras** | Traffic splitting, observability | Network policies, L7 visibility |

> Cilium encrypts all pod traffic between nodes transparently. Application code requires no changes. For L7 features (traffic splitting, retries), Cilium can optionally use an Envoy proxy.

### Common Istio Errors

| Error | Cause | Fix |
|---|---|---|
| Pod stuck at `Init:0/1` | Sidecar injection webhook failing | Check `kubectl logs -n istio-system deploy/istiod` |
| `upstream connect error or disconnect` | Destination pod not in mesh | Ensure namespace has `istio-injection=enabled` |
| `503 Service Unavailable` | Circuit breaker tripped | Check DestinationRule outlierDetection settings |
| mTLS handshake failure | Mixed STRICT/PERMISSIVE modes | Set consistent PeerAuthentication across namespaces |

### Service Mesh Real-Life Use Cases

| Use Case | What the Mesh Provides | Without Mesh |
|---|---|---|
| **Microservices with strict security** | Automatic mTLS between all services — no app code changes | Each service must implement TLS manually |
| **Canary/blue-green releases** | Traffic splitting (90/10) via VirtualService | Requires custom LB config or feature flags |
| **Debugging latency** | Distributed tracing (Jaeger/Zipkin) shows per-service latency | Manual log correlation across services |
| **Circuit breaking** | Automatic circuit breaker prevents cascade failures | Each service must implement retry/backoff logic |
| **Compliance (PCI/HIPAA)** | Prove all inter-service traffic is encrypted | Manual cert management per service |

**When NOT to use a service mesh:**
- Fewer than 5 microservices (overhead not justified)
- Simple request/response patterns without complex routing
- Team lacks operational experience with Istio/Linkerd
- Latency-sensitive workloads where sidecar overhead matters (~1-2ms per hop)

**Interview question: What is a service mesh and when would you use one?**
A service mesh is an infrastructure layer that handles service-to-service communication via sidecar proxies. Use it when you have many microservices and need: automatic mTLS encryption, traffic splitting for canary deployments, circuit breaking, distributed tracing, and consistent retry/timeout policies — without modifying application code. Don't use it for simple architectures (< 5 services) due to the operational overhead.

---

## 35.3 Module 8 Exercises

### Exercise: Deploy the E-Commerce Platform
```bash
# 1. Create the namespace structure
# 2. Deploy PostgreSQL with persistent storage
# 3. Deploy the product service
# 4. Deploy the frontend
# 5. Configure Ingress with TLS
# 6. Apply network policies
# 7. Set up monitoring with Prometheus
# 8. Configure HPA for auto-scaling
# 9. Test with load generator:
kubectl run load-gen --image=busybox --rm -it -- \
  /bin/sh -c "while true; do wget -q -O- http://product-service.ecommerce/products; done"
# 10. Observe scaling behavior in Grafana
```

---

**Next Module: Common Errors & Troubleshooting Guide →**
