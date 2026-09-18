# MODULE 13: Services & Service Discovery

---

## 13.1 Why Services?

Pods are ephemeral — they get new IP addresses when recreated. Services provide a stable endpoint to access a group of Pods.

**The problem Services solve:**
- Pod IPs change every time a pod is recreated (after crash, scaling, update)
- You cannot hardcode pod IPs in your application configuration
- You need load balancing across multiple pod replicas
- You need a stable DNS name for service discovery

**How Services work internally:**
1. A Service gets a stable ClusterIP (virtual IP) that never changes
2. kube-proxy on each node creates iptables/IPVS rules to route traffic from the ClusterIP to actual pod IPs
3. The Endpoints controller watches for pods matching the Service's `selector` and updates the endpoint list
4. When a pod is added/removed, kube-proxy updates the routing rules automatically

**Key fields in a Service:**
- `selector` — label selector to find backing pods (must match pod labels exactly)
- `port` — the port the Service listens on (what clients connect to)
- `targetPort` — the port on the container (where the application listens)
- `type` — how the Service is exposed (ClusterIP, NodePort, LoadBalancer, ExternalName)

**Common mistake:** If `selector` labels don't match any pod labels, the Service has no endpoints. Use `kubectl get endpoints <service-name>` to verify.

**Real-life analogy:** A Service is like a company's phone number. Employees (Pods) come and go, but the company number (Service) stays the same. The receptionist (kube-proxy) routes calls to available employees.

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Client → Service (stable IP) → Pod 1 (10.0.1.15)   │
│                                 → Pod 2 (10.0.1.16)  │
│                                 → Pod 3 (10.0.2.25)  │
│                                                      │
│  If Pod 1 dies and is replaced by Pod 4 (10.0.3.30), │
│  the Service automatically routes to Pod 4.          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Why you can't access pods directly from outside:**

Pods run on an internal cluster network (e.g., `10.244.0.0/16`) that is not routable from external networks. Without a Service, the only way to reach a pod is to SSH into the node and curl the pod IP:

```bash
# From your laptop — this does NOT work:
curl http://10.244.0.2
# Connection refused — pod network is internal only

# SSH into the Kubernetes node first:
ssh user@192.168.1.2

# From inside the node — this works:
curl http://10.244.0.2
# Hello World!
```

A NodePort Service solves this by mapping a port on the node's external IP to the pod's internal port, making the application accessible without SSH.

**Load balancing across pods:**

When multiple pods match a Service's selector, Kubernetes distributes traffic using a **random/round-robin algorithm** — the Service acts as a built-in load balancer. No additional configuration is needed:

```bash
# 3 pods behind a Service — traffic is distributed automatically
kubectl get endpoints myapp-service

# NAME            ENDPOINTS                                      AGE
# myapp-service   10.244.0.2:80,10.244.0.3:80,10.244.1.4:80     5m

# Each curl request may hit a different pod
curl http://192.168.1.2:30008   # → Pod 1
curl http://192.168.1.2:30008   # → Pod 3
curl http://192.168.1.2:30008   # → Pod 2
```

### Inter-Pod Communication

Containers within the same pod share the same network namespace and can communicate via `localhost`:

```yaml
# multi-container-networking.yaml
apiVersion: v1
kind: Pod
metadata:
  name: microservice1
spec:
  containers:
  - name: app
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
  - name: web
    image: httpd
    ports:
    - containerPort: 80
```

```bash
kubectl apply -f multi-container-networking.yaml

# Access the web container from the app container via localhost
kubectl exec microservice1 -c app -it -- /bin/bash
  apt update && apt install -y curl
  curl localhost:80
```

Pods on different nodes communicate via their pod IPs (managed by the CNI plugin):

```yaml
# separate-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: microservice2
spec:
  containers:
  - name: web
    image: nginx
    ports:
    - containerPort: 80
```

```bash
# Get the pod IP and access it from another pod
kubectl get pod microservice2 -o wide
# curl <microservice2-pod-IP>:80
```

---

## 13.2 Service Types

### ClusterIP (Default) — Internal Only

Accessible only within the cluster. Used for internal service-to-service communication.

**Multi-tier architecture with ClusterIP:**

In a typical microservices application, each tier has its own set of pods and a ClusterIP Service:

```
┌─────────────────────────────────────────────────────────┐
│  Frontend Pods ──→ backend-service (ClusterIP) ──→ Backend Pods  │
│                                                         │
│  Backend Pods  ──→ redis-service (ClusterIP)   ──→ Redis Pods    │
│                                                         │
│  Backend Pods  ──→ mysql-service (ClusterIP)   ──→ MySQL Pods    │
└─────────────────────────────────────────────────────────┘
```

Each tier can scale independently — adding more backend pods doesn't affect the frontend or database tiers. The ClusterIP Service provides a stable endpoint regardless of how many pods are behind it.

```yaml
# clusterip-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP              # Default, can be omitted
  selector:
    app: backend               # Routes to pods with this label
  ports:
  - protocol: TCP
    port: 80                   # Service port (what clients connect to)
    targetPort: 8080           # Container port (where app listens)
```

```bash
kubectl apply -f clusterip-service.yaml

kubectl get service backend-service

# Output:
# NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
# backend-service   ClusterIP   172.20.45.123   <none>        80/TCP    30s

# Test from within the cluster (using busybox + wget)
kubectl run test-pod --image=busybox --rm -it -- wget -qO- http://backend-service

# Output:
# <!DOCTYPE html>
# <html>...

# Test using curl (more realistic for API testing)
kubectl run tmp --rm -it --image=curlimages/curl -- sh
# Inside the shell:
curl http://backend-service:80/health

# Output:
# {"status":"ok","uptime":"3600s"}

# One-liner curl test (no interactive shell)
kubectl run tmp --rm -it --image=curlimages/curl -- curl -s http://backend-service:80/health

# DNS resolution within the cluster:
# backend-service                              → same namespace
# backend-service.default                      → explicit namespace
# backend-service.default.svc.cluster.local    → fully qualified
```

### NodePort — External via Node IP

Exposes the service on each node's IP at a static port (30000-32767).

```yaml
# nodeport-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-nodeport
spec:
  type: NodePort
  selector:
    app: webapp
  ports:
  - protocol: TCP
    port: 80              # Service port
    targetPort: 8080      # Container port
    nodePort: 30080       # External port on each node (optional, auto-assigned if omitted)
```

```bash
kubectl apply -f nodeport-service.yaml

kubectl get service webapp-nodeport

# Output:
# NAME              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
# webapp-nodeport   NodePort   172.20.67.89    <none>        80:30080/TCP   30s

# Access via any node's IP:
# http://<node-ip>:30080

# Get node IPs
kubectl get nodes -o wide

# Output:
# NAME                          STATUS   INTERNAL-IP   EXTERNAL-IP
# ip-10-0-1-100.ec2.internal    Ready    10.0.1.100    54.123.45.67
# ip-10-0-2-200.ec2.internal    Ready    10.0.2.200    54.123.45.68

# Access: http://54.123.45.67:30080
```

```
┌─────────────────────────────────────────────────┐
│  External Traffic                                │
│       │                                          │
│       ▼ :30080                                   │
│  ┌─── Node 1 ───┐    ┌─── Node 2 ───┐          │
│  │   kube-proxy  │    │   kube-proxy  │          │
│  │       │       │    │       │       │          │
│  │       ▼       │    │       ▼       │          │
│  │  Service:80   │    │  Service:80   │          │
│  │       │       │    │       │       │          │
│  │   Pod:8080    │    │   Pod:8080    │          │
│  └───────────────┘    └───────────────┘          │
└─────────────────────────────────────────────────┘
```

### NodePort Cross-Node Routing — Pod on Node 2, Access via Node 1

A common interview question: "If a pod runs only on Node 2, can I access it via Node 1's IP on the NodePort?" **Yes.** kube-proxy on every node creates iptables/IPVS rules for every Service, regardless of where the pods are.

```
Scenario: Pod runs ONLY on Node 2, user hits Node 1:30080

┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  User → http://Node1-IP:30080                                │
│              │                                               │
│              ▼                                               │
│  ┌─── Node 1 ──────────────────┐                             │
│  │  kube-proxy (iptables)      │                             │
│  │  Rule: :30080 → Pod IPs     │                             │
│  │  Pod IP list: [10.0.2.15]   │  ← Only 1 pod, on Node 2   │
│  │       │                     │                             │
│  │       │ No local pod,       │                             │
│  │       │ forward to 10.0.2.15│                             │
│  └───────┼─────────────────────┘                             │
│          │                                                   │
│          │  CNI network (VXLAN/VPC routing)                   │
│          │                                                   │
│  ┌───────▼─────────────────────┐                             │
│  │  Node 2                     │                             │
│  │  Pod: 10.0.2.15:8080        │  ← Pod receives the request │
│  │       │                     │                             │
│  │       ▼                     │                             │
│  │  Response → back to user    │                             │
│  └─────────────────────────────┘                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Step-by-step what happens internally:**

```
1. User sends request to Node1-IP:30080
2. Node 1's kube-proxy has iptables rules for the NodePort Service
3. iptables looks up the Endpoints for the Service → [10.0.2.15:8080]
4. Since 10.0.2.15 is NOT on Node 1, the packet is routed via the CNI network
5. The CNI plugin (Calico/VPC-CNI/Flannel) routes the packet to Node 2
6. Node 2 delivers the packet to the pod at 10.0.2.15:8080
7. The pod responds, and the response follows the reverse path back to the user
```

```bash
# Verify: Create a deployment with 1 replica, then access via a different node

kubectl create deployment web --image=nginx --replicas=1
kubectl expose deployment web --port=80 --target-port=80 --type=NodePort

# Check which node the pod is on
kubectl get pods -o wide -l app=web

# Output:
# NAME                   READY   STATUS    NODE
# web-5d78c9869d-abc12   1/1     Running   ip-10-0-2-200.ec2.internal   ← Node 2 only

# Get the NodePort
kubectl get svc web

# Output:
# NAME   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
# web    NodePort   172.20.45.123   <none>        80:31234/TCP   10s

# Access via Node 1 (where the pod is NOT running) — it works!
curl http://54.123.45.67:31234    # Node 1 IP

# Output:
# <!DOCTYPE html>
# <html>
# <head><title>Welcome to nginx!</title></head>
# ...

# Access via Node 2 (where the pod IS running) — also works
curl http://54.123.45.68:31234    # Node 2 IP

# Both work because kube-proxy on EVERY node has the routing rules
```

**`externalTrafficPolicy` — Control cross-node behavior:**

```yaml
# By default: externalTrafficPolicy: Cluster
# Traffic can be forwarded to pods on any node (adds a network hop)

# To avoid the extra hop (and preserve client source IP):
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: NodePort
  externalTrafficPolicy: Local    # Only route to pods on THIS node
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
```

| Policy | Behavior | Pros | Cons |
|---|---|---|---|
| `Cluster` (default) | Forward to any pod on any node | Even load distribution | Extra network hop, loses client IP |
| `Local` | Only forward to pods on the same node | No extra hop, preserves client IP | Returns 503 if no pod on that node |

**Interview question: Can you access a NodePort service on a node where the pod isn't running?**
Yes. kube-proxy on every node creates iptables rules for every Service. When traffic hits a node without the pod, kube-proxy forwards it across the cluster network to a node that has the pod. This is the default `externalTrafficPolicy: Cluster` behavior. Set `Local` to restrict traffic to same-node pods only.

---

### LoadBalancer — AWS ELB Integration

**Why not just use NodePort in production?**

NodePort works but has limitations for end users:
- Users must remember IP:port combinations (e.g., `192.168.1.2:30080`, `192.168.1.3:30080`)
- No single URL — users prefer `myapp.example.com`, not `<node-ip>:30080`
- You'd need to set up an external load balancer (HAProxy, Nginx) yourself to provide a unified entry point

The LoadBalancer service type solves this — Kubernetes asks the cloud provider to provision a load balancer automatically, giving you a single DNS endpoint.

> **On unsupported environments** (VirtualBox, bare-metal, Minikube): `type: LoadBalancer` falls back to behaving like NodePort — it exposes the service on a high port but does not provision an external load balancer. Use MetalLB for bare-metal LoadBalancer support.

Creates an AWS Elastic Load Balancer automatically.

```yaml
# loadbalancer-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp-lb
  annotations:
    # Use NLB instead of Classic LB
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    # Internal LB (not internet-facing)
    # service.beta.kubernetes.io/aws-load-balancer-internal: "true"
    # Cross-zone load balancing
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: webapp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
```

```bash
kubectl apply -f loadbalancer-service.yaml

kubectl get service webapp-lb

# Output (takes 2-3 minutes for ELB to provision):
# NAME        TYPE           CLUSTER-IP      EXTERNAL-IP                                                              PORT(S)        AGE
# webapp-lb   LoadBalancer   172.20.89.123   a1b2c3d4e5f6g7h8i9j0.us-east-1.elb.amazonaws.com                        80:31234/TCP   3m

# Test the load balancer
curl http://a1b2c3d4e5f6g7h8i9j0.us-east-1.elb.amazonaws.com

# Output:
# <!DOCTYPE html>
# <html>...
```

```
┌──────────────────────────────────────────────────────┐
│  Internet                                             │
│      │                                                │
│      ▼                                                │
│  ┌── AWS NLB ──────────────────────────────────┐      │
│  │  a1b2c3...elb.amazonaws.com:80              │      │
│  └─────────────────────────────────────────────┘      │
│      │              │              │                   │
│      ▼              ▼              ▼                   │
│  Node 1:31234   Node 2:31234   Node 3:31234           │
│      │              │              │                   │
│      ▼              ▼              ▼                   │
│   Pod:8080       Pod:8080       Pod:8080               │
└──────────────────────────────────────────────────────┘
```

### ExternalName — DNS Alias

Maps a service to an external DNS name. No proxying.

```yaml
# externalname-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: mydb.abc123.us-east-1.rds.amazonaws.com
```

```bash
# Pods can now access the RDS database as:
# external-db.default.svc.cluster.local
# which resolves to mydb.abc123.us-east-1.rds.amazonaws.com
```

### Service Types Comparison

| Type | Scope | Use Case | AWS Resource |
|---|---|---|---|
| ClusterIP | Internal only | Service-to-service | None |
| NodePort | External via node port (30000-32767) | Development/testing | None |
| LoadBalancer | External via LB | Production web apps | ELB/NLB/ALB |
| ExternalName | DNS alias | External services (RDS) | None |
| Headless (`clusterIP: None`) | Direct pod IPs | StatefulSets, pod-level access | None |

**How to choose:**
- **ClusterIP** — default for all internal services. Backend APIs, databases, caches.
- **NodePort** — quick external access for testing. Not for production (exposes ports on all nodes).
- **LoadBalancer** — production external access. Creates a cloud load balancer automatically.
- **ExternalName** — when you need to reference an external service (e.g., RDS) by a Kubernetes DNS name.
- **Headless** — when you need to discover individual pod IPs (StatefulSets, peer-to-peer).

**Interview question: What's the difference between `port`, `targetPort`, and `nodePort`?**
- `port` — the port the Service listens on (ClusterIP:port)
- `targetPort` — the port on the container where the app listens
- `nodePort` — the port exposed on every node's IP (only for NodePort/LoadBalancer types, range 30000-32767)

### The Default Kubernetes Service

Every cluster has a built-in `kubernetes` service in the default namespace. It provides access to the API server:

```bash
kubectl get svc
# NAME         TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
# kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   16d

kubectl describe svc kubernetes
# Name:              kubernetes
# Namespace:         default
# Labels:            component=apiserver
#                    provider=kubernetes
# Type:              ClusterIP
# IP:                10.96.0.1
# Port:              <unset> 443/TCP
# TargetPort:        6443/TCP
# Endpoints:         10.0.1.5:6443
# Session Affinity:  None
```

This service has no selector — its endpoints are managed directly by Kubernetes to point at the API server (port 6443).

### Session Affinity (Sticky Sessions)

By default, Services distribute traffic randomly across pods. Session affinity routes all requests from the same client to the same pod.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: webapp
spec:
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: 8080
  sessionAffinity: ClientIP          # Route same client IP to same pod
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800          # 3 hours (default)
```

```bash
# Check session affinity on a service
kubectl get svc webapp -o jsonpath='{.spec.sessionAffinity}'
# ClientIP

# Without session affinity (default)
kubectl get svc webapp -o jsonpath='{.spec.sessionAffinity}'
# None
```

| Value | Behavior | Use Case |
|-------|----------|----------|
| `None` (default) | Random distribution across pods | Stateless APIs, microservices |
| `ClientIP` | Same client IP always hits same pod | WebSocket connections, shopping carts, file uploads |

> ⚠️ Session affinity only works with `ClusterIP` and `NodePort` services. For `LoadBalancer`, configure sticky sessions on the cloud load balancer instead (e.g., AWS ALB target group stickiness).

### Imperative Service Creation Commands

Instead of writing YAML, you can create services imperatively:

```bash
# Expose a pod as a ClusterIP service
kubectl expose pod redis --port=6379 --name=redis-service
# service/redis-service exposed

# Expose a deployment as a NodePort service
kubectl expose deployment webapp --type=NodePort --port=80 --target-port=8080 --name=webapp-service
# service/webapp-service exposed

# Generate service YAML without creating (for review/editing)
kubectl expose pod nginx --type=NodePort --port=80 --name=nginx-service --dry-run=client -o yaml

# Create a ClusterIP service directly
kubectl create service clusterip redis --tcp=6379:6379
# service/redis created

# Create a NodePort service directly
kubectl create service nodeport nginx --tcp=80:80 --node-port=30080
# service/nginx created
```

> **`kubectl expose` vs `kubectl create service`:** `expose` uses the pod/deployment's existing labels as the selector. `create service` generates a default selector (`app=<name>`) which may not match your pods. Prefer `kubectl expose` when the resource already exists.

### ClusterIP + NodePort Architecture — Frontend/Backend Walkthrough

A common pattern: backend exposed via ClusterIP (internal only), frontend exposed via NodePort (external access). The frontend Nginx acts as a reverse proxy, forwarding requests to the backend.

```
┌─────────────────────────────────────────────────────────┐
│  User Browser                                            │
│  http://<node-ip>:31234/hello                            │
│         │                                                │
│         ▼                                                │
│  ┌─── NodePort Service (port 31234) ───┐                │
│  │  frontend-service                    │                │
│  └──────────┬──────────────────────────┘                │
│             ▼                                            │
│  ┌─── Frontend Pod (Nginx) ────────────┐                │
│  │  proxy_pass http://my-backend-      │                │
│  │  service:8080                       │                │
│  └──────────┬──────────────────────────┘                │
│             ▼                                            │
│  ┌─── ClusterIP Service ───────────────┐                │
│  │  my-backend-service:8080            │                │
│  └──────────┬──────────────────────────┘                │
│             ▼                                            │
│  ┌─── Backend Pods (REST API) ─────────┐                │
│  │  Pod 1  │  Pod 2  │  Pod 3  │ ...   │                │
│  └─────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

#### Imperative Setup

**Step 1: Create backend deployment and ClusterIP service**

```bash
# Create backend deployment (Spring Boot REST API)
kubectl create deployment my-backend-rest-app --image=stacksimplify/kube-helloworld:1.0.0

# Expose as ClusterIP (default type — no --type flag needed)
kubectl expose deployment my-backend-rest-app --port=8080 --target-port=8080 --name=my-backend-service

# Verify
kubectl get deploy
# NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
# my-backend-rest-app   1/1     1            1           5s

kubectl get svc
# NAME                 TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
# my-backend-service   ClusterIP   10.100.1.100   <none>        8080/TCP   10s
```

ClusterIP is only accessible within the cluster — no external access.

**Step 2: Create frontend deployment and NodePort service**

The frontend Nginx image (`stacksimplify/kube-frontend-nginx:1.0.0`) has a built-in reverse proxy config that forwards requests to `my-backend-service:8080`.

```bash
# Create frontend deployment
kubectl create deployment my-frontend-nginx-app --image=stacksimplify/kube-frontend-nginx:1.0.0

# Expose as NodePort
kubectl expose deployment my-frontend-nginx-app --type=NodePort --port=80 --target-port=80 --name=my-frontend-service

# Verify all services
kubectl get svc
# NAME                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# my-backend-service    ClusterIP   10.100.1.100   <none>        8080/TCP       5m
# my-frontend-service   NodePort    10.100.2.150   <none>        80:31234/TCP   10s
```

**Step 3: Access the application**

```bash
# Get worker node public IP
kubectl get nodes -o wide

# Access frontend → Nginx forwards to backend
# http://<node-public-ip>:31234/hello

# Expected response (from backend via frontend):
# { "message": "Hello from Backend App" }
```

**Step 4: Scale backend for load balancing**

```bash
kubectl scale --replicas=10 deployment/my-backend-rest-app

# Verify 10 backend pods
kubectl get pods

# Access again — requests are distributed across 10 backend replicas
# http://<node-public-ip>:31234/hello
```

**Step 5: Clean up**

```bash
kubectl delete deployment my-backend-rest-app my-frontend-nginx-app
kubectl delete svc my-backend-service my-frontend-service
kubectl get all
```

#### Nginx Reverse Proxy Configuration

The frontend Nginx container uses this config to forward requests to the backend:

```nginx
server {
    listen       80;
    server_name  localhost;

    location / {
        # Forward all requests to the backend ClusterIP service
        proxy_pass http://my-backend-service:8080;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
```

| Directive | Purpose |
|---|---|
| `listen 80` | Nginx listens on port 80 |
| `proxy_pass http://my-backend-service:8080` | Forwards requests to the backend ClusterIP service |
| `error_page 500 502 503 504` | Custom error pages for server errors |

**Request flow:**
1. User accesses `http://<node-ip>:31234/hello`
2. NodePort routes to frontend Nginx pod on port 80
3. Nginx forwards to `http://my-backend-service:8080/hello` (ClusterIP)
4. Backend pod responds with JSON
5. Nginx returns the response to the user

**Dockerfile for the frontend image:**

```dockerfile
FROM nginx
COPY default.conf /etc/nginx/conf.d
```

**For backend in a custom namespace**, use the fully qualified domain name (FQDN):

```nginx
# Instead of:
proxy_pass http://my-backend-service:8080;

# Use FQDN when backend is in a different namespace:
proxy_pass http://my-backend-service.custom-namespace.svc.cluster.local:8080;
```

Format: `<service-name>.<namespace>.svc.cluster.local`

#### Declarative Setup (YAML Manifests)

**Backend Deployment:**

```yaml
# 01-backend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-restapp
  labels:
    app: backend-restapp
    tier: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-restapp
  template:
    metadata:
      labels:
        app: backend-restapp
        tier: backend
    spec:
      containers:
        - name: backend-restapp
          image: stacksimplify/kube-helloworld:1.0.0
          ports:
            - containerPort: 8080
```

**Backend ClusterIP Service:**

```yaml
# 02-backend-clusterip-service.yml
apiVersion: v1
kind: Service
metadata:
  name: my-backend-service    # Nginx proxy_pass uses this name
  labels:
    app: backend-restapp
    tier: backend
spec:
  selector:
    app: backend-restapp
  ports:
    - name: http
      port: 8080
      targetPort: 8080
```

**Frontend Deployment:**

```yaml
# 03-frontend-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-nginxapp
  labels:
    app: frontend-nginxapp
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend-nginxapp
  template:
    metadata:
      labels:
        app: frontend-nginxapp
        tier: frontend
    spec:
      containers:
        - name: frontend-nginxapp
          image: stacksimplify/kube-frontend-nginx:1.0.0
          ports:
            - containerPort: 80
```

**Frontend NodePort Service:**

```yaml
# 04-frontend-nodeport-service.yml
apiVersion: v1
kind: Service
metadata:
  name: frontend-nginxapp-nodeport-service
  labels:
    app: frontend-nginxapp
    tier: frontend
spec:
  type: NodePort
  selector:
    app: frontend-nginxapp
  ports:
    - name: http
      port: 80
      targetPort: 80
      nodePort: 31234
```

**Deploy and test:**

```bash
# Apply all manifests
kubectl apply -f 01-backend-deployment.yml -f 02-backend-clusterip-service.yml \
              -f 03-frontend-deployment.yml -f 04-frontend-nodeport-service.yml

# Or apply entire folder
kubectl apply -f kube-manifests/

# Verify
kubectl get all

# Access
kubectl get nodes -o wide
# http://<node-public-ip>:31234/hello

# Delete all
kubectl delete -f 01-backend-deployment.yml -f 02-backend-clusterip-service.yml \
               -f 03-frontend-deployment.yml -f 04-frontend-nodeport-service.yml
```

### How to Provide a Static IP Address to a Pod

Pods are ephemeral — their IPs change when they restart, reschedule, or scale. Kubernetes is designed this way intentionally. However, there are several approaches to achieve stable network identity:

**Approach 1: Use a Service (recommended)**

A Service provides a stable ClusterIP that never changes, even as pods behind it come and go:

```bash
# The Service IP (172.20.45.123) stays the same forever
# Pods behind it can change freely
kubectl get svc backend-service

# Output:
# NAME              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
# backend-service   ClusterIP   172.20.45.123   <none>        80/TCP    30d
#                               ^^^^^^^^^^^^^^
#                               This IP is stable for the lifetime of the Service
```

**Approach 2: StatefulSet + Headless Service (stable DNS per pod)**

Each pod gets a predictable DNS name that resolves to its current IP:

```bash
# StatefulSet pods get stable DNS names:
# postgres-0.postgres.default.svc.cluster.local → 10.0.1.15 (current IP)
# postgres-1.postgres.default.svc.cluster.local → 10.0.2.25 (current IP)

# The DNS name is stable even if the pod restarts and gets a new IP
# Applications should connect via DNS name, not IP
```

**Approach 3: hostNetwork (pod uses node's IP)**

```yaml
# pod-host-network.yaml
apiVersion: v1
kind: Pod
metadata:
  name: host-network-pod
spec:
  hostNetwork: true          # Pod uses the node's network namespace
  containers:                # Pod IP = Node IP
  - name: app
    image: nginx
    ports:
    - containerPort: 80      # Binds to port 80 on the NODE
```

```bash
kubectl apply -f pod-host-network.yaml

kubectl get pod host-network-pod -o wide

# Output:
# NAME               READY   STATUS    IP            NODE
# host-network-pod   1/1     Running   10.0.1.100    ip-10-0-1-100.ec2.internal
#                                      ^^^^^^^^^^
#                                      Same as the node's IP

# ⚠️ Risks:
# - Port conflicts with other pods or node services
# - Only one pod per node can use the same port
# - Pod is tied to the node's network (less portable)
# - Security concern: pod has full access to node's network
```

**Approach 4: Service with externalIPs (assign a specific IP)**

```yaml
# external-ip-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: static-ip-service
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
  externalIPs:
  - 203.0.113.50             # A specific IP you control
                              # Traffic to this IP:80 is routed to the pods
```

```bash
kubectl apply -f external-ip-service.yaml

kubectl get svc static-ip-service

# Output:
# NAME                TYPE        CLUSTER-IP      EXTERNAL-IP    PORT(S)   AGE
# static-ip-service   ClusterIP   172.20.45.200   203.0.113.50   80/TCP    10s

# ⚠️ The externalIP must be routable to the node — you must configure
# your network infrastructure to route this IP to a cluster node
```

**Approach 5: AWS Elastic IP with LoadBalancer**

```yaml
# For a truly static public IP on AWS:
apiVersion: v1
kind: Service
metadata:
  name: static-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-eip-allocations: "eipalloc-abc123,eipalloc-def456"
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

**Approach 6: AKS Static Public IP with LoadBalancer**

```yaml
# For a static public IP on Azure AKS:
# Step 1: Create a static public IP in Azure
# az network public-ip create -g MC_myRG_myAKS_eastus -n myStaticIP --sku Standard --allocation-method Static

# Step 2: Use it in the Service
apiVersion: v1
kind: Service
metadata:
  name: static-lb
spec:
  type: LoadBalancer
  loadBalancerIP: 20.50.100.200    # The static IP you created
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

**Comparison of approaches:**

| Approach | IP Stability | Use Case | Limitations |
|---|---|---|---|
| **Service (ClusterIP)** | Stable within cluster | Internal communication | Not accessible externally |
| **StatefulSet + Headless** | Stable DNS name | Databases, stateful apps | DNS name, not fixed IP |
| **hostNetwork** | Uses node IP | System-level pods, monitoring | Port conflicts, security risk |
| **externalIPs** | Fixed external IP | On-prem with static IPs | Requires network config |
| **NLB + Elastic IP** | Fixed public IP | Production external access | AWS-specific, costs money |

**Interview question: How do you provide a static IP to a pod?**
Pods are ephemeral and their IPs change by design. Instead of assigning static IPs, use a Service (stable ClusterIP), StatefulSet with headless service (stable DNS names), or `hostNetwork: true` (pod uses node's IP). For external static IPs, use a LoadBalancer Service with AWS Elastic IPs or `externalIPs` field. The recommended approach is always to use Services or DNS names rather than relying on pod IPs.

---

## 13.3 Service Discovery & DNS

Kubernetes runs CoreDNS for internal DNS resolution.

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Output:
# NAME                       READY   STATUS    RESTARTS   AGE
# coredns-5d78c9869d-abc12   1/1     Running   0          5d
# coredns-5d78c9869d-def34   1/1     Running   0          5d

# DNS resolution formats:
# <service-name>                                    → same namespace
# <service-name>.<namespace>                        → cross-namespace
# <service-name>.<namespace>.svc.cluster.local      → fully qualified

# Test DNS resolution
kubectl run dns-test --image=busybox --rm -it -- nslookup backend-service

# Output:
# Server:    172.20.0.10
# Address:   172.20.0.10:53
#
# Name:      backend-service.default.svc.cluster.local
# Address:   172.20.45.123

# Cross-namespace DNS
kubectl run dns-test --image=busybox --rm -it -- nslookup backend-service.production

# Output:
# Name:      backend-service.production.svc.cluster.local
# Address:   172.20.78.45
```

### Headless Service (for StatefulSets)

```yaml
# headless-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None          # Makes it headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

```bash
# Headless service returns individual pod IPs instead of a single ClusterIP
kubectl run dns-test --image=busybox --rm -it -- nslookup postgres

# Output:
# Name:      postgres.default.svc.cluster.local
# Address:   10.0.1.15    ← postgres-0
# Address:   10.0.2.25    ← postgres-1
# Address:   10.0.3.35    ← postgres-2

# Individual pod DNS:
# postgres-0.postgres.default.svc.cluster.local
# postgres-1.postgres.default.svc.cluster.local
```

**Pod-level DNS with `subdomain` and `hostname`:**

For standalone Pods (not in a StatefulSet), you can get headless service DNS records by setting `subdomain` (must match the headless service name) and `hostname` in the Pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp-pod
  labels:
    app: mysql
spec:
  subdomain: mysql-h       # Must match headless service name
  hostname: mysql-pod      # Becomes the DNS hostname
  containers:
  - name: mysql
    image: mysql
# DNS record: mysql-pod.mysql-h.default.svc.cluster.local
```

Without `hostname`, no A record is created for the pod. With Deployments, all pods in the template share the same `hostname` value, so they all get the same DNS record — making it useless for individual pod addressing. StatefulSets solve this by automatically assigning unique hostnames based on ordinal index (e.g., `mysql-0`, `mysql-1`), so you don't need `subdomain`/`hostname` fields.

### Cross-Namespace Service Access — Complete Walkthrough

Services are namespace-scoped, but any pod in the cluster can access a service in another namespace using its fully qualified DNS name.

```
┌──────────────────────────────────────────────────────────────┐
│  Cluster                                                     │
│                                                              │
│  ┌─── Namespace: frontend ──────┐                            │
│  │                              │                            │
│  │  Pod: webapp                 │                            │
│  │  curl http://api-svc.backend │──────────────┐             │
│  │                              │              │             │
│  └──────────────────────────────┘              │             │
│                                                │ DNS lookup  │
│                                                ▼             │
│  ┌─── Namespace: backend ───────┐    ┌──────────────┐        │
│  │                              │    │   CoreDNS    │        │
│  │  Service: api-svc            │◄───│   resolves   │        │
│  │  ClusterIP: 172.20.50.100    │    │   api-svc.   │        │
│  │       │                      │    │   backend.   │        │
│  │       ▼                      │    │   svc.cluster│        │
│  │  Pod: api-server             │    │   .local     │        │
│  │                              │    └──────────────┘        │
│  └──────────────────────────────┘                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Step 1: Create two namespaces
kubectl create namespace frontend
kubectl create namespace backend

# Step 2: Deploy a service in the backend namespace
kubectl apply -n backend -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: nginx
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: api-svc
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 80
EOF

# Step 3: Verify the service exists in backend namespace
kubectl get svc -n backend

# Output:
# NAME      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
# api-svc   ClusterIP   172.20.50.100    <none>        80/TCP    10s

# Step 4: Access from the frontend namespace using DNS
kubectl run test -n frontend --image=busybox --rm -it -- wget -qO- http://api-svc.backend

# Output:
# <!DOCTYPE html>
# <html>
# <head><title>Welcome to nginx!</title></head>
# ...

# Step 5: Also works with fully qualified domain name (FQDN)
kubectl run test -n frontend --image=busybox --rm -it -- wget -qO- http://api-svc.backend.svc.cluster.local

# Output:
# <!DOCTYPE html>
# ...

# Step 6: Verify DNS resolution
kubectl run test -n frontend --image=busybox --rm -it -- nslookup api-svc.backend

# Output:
# Server:    172.20.0.10
# Address:   172.20.0.10:53
#
# Name:      api-svc.backend.svc.cluster.local
# Address:   172.20.50.100
```

**DNS formats for cross-namespace access:**

| Format | Example | When to Use |
|---|---|---|
| `<service>` | `api-svc` | Same namespace only |
| `<service>.<namespace>` | `api-svc.backend` | Cross-namespace (most common) |
| `<service>.<namespace>.svc` | `api-svc.backend.svc` | Cross-namespace (explicit) |
| `<service>.<namespace>.svc.cluster.local` | `api-svc.backend.svc.cluster.local` | FQDN (use in config files for clarity) |

**Restricting cross-namespace access with NetworkPolicy:**

By default, any pod can access any service in any namespace. Use NetworkPolicy to restrict:

```yaml
# Only allow pods from namespace "frontend" to access api-svc in namespace "backend"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-only
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend       # Namespace must have this label
    ports:
    - port: 80
```

```bash
# Label the frontend namespace (required for namespaceSelector)
kubectl label namespace frontend name=frontend

kubectl apply -f allow-frontend-only.yaml

# Test: Access from frontend namespace — works
kubectl run test -n frontend --image=busybox --rm -it -- wget -qO- --timeout=3 http://api-svc.backend

# Output: HTML response (allowed)

# Test: Access from default namespace — blocked
kubectl run test --image=busybox --rm -it -- wget -qO- --timeout=3 http://api-svc.backend

# Output:
# wget: download timed out
# (Blocked by NetworkPolicy)
```

**Interview question: How do you access a service in another namespace?**
Use the DNS name `<service-name>.<namespace>` or the FQDN `<service-name>.<namespace>.svc.cluster.local`. CoreDNS resolves it to the service's ClusterIP. No special configuration needed — cross-namespace access works by default. Use NetworkPolicy with `namespaceSelector` to restrict it.

**Common pitfall — cross-namespace DB connection:**

A deployment in the default namespace connects to a MySQL database using `DB_Host: mysql`. If the MySQL service is in the `payroll` namespace, this fails:

```bash
# From a pod in the default namespace — NXDOMAIN because "mysql" only resolves
# within the payroll namespace
kubectl exec hr -- nslookup mysql
# Server:    10.96.0.10
# Address:   10.96.0.10#53
# ** server can't find mysql: NXDOMAIN

# Fix: use the namespace-qualified name
kubectl exec hr -- nslookup mysql.payroll
# Server:    10.96.0.10
# Address:   10.96.0.10#53
# Name:      mysql.payroll.svc.cluster.local
# Address:   10.98.149.84
```

Fix the deployment by updating the environment variable:

```bash
kubectl edit deploy webapp
```

```yaml
env:
  - name: DB_Host
    value: mysql.payroll    # was: mysql
```

Short names like `mysql` only resolve to services in the same namespace. For cross-namespace access, always use `<service>.<namespace>` or the full FQDN.

### CoreDNS Architecture

CoreDNS runs as a Deployment (2 replicas for HA) in `kube-system`. It watches the Kubernetes API for new services and pods, automatically creating DNS records.

**The kube-dns Service:**

```bash
kubectl get svc -n kube-system kube-dns
# NAME       TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
# kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   30d
```

Every pod's `/etc/resolv.conf` points to this service:

```bash
kubectl exec busybox -- cat /etc/resolv.conf
# nameserver 10.96.0.10
# search default.svc.cluster.local svc.cluster.local cluster.local
# ndots:5
```

The `search` entries allow short names to resolve: `web-service` → tries `web-service.default.svc.cluster.local` first.

**Kubelet configures this automatically:**

```bash
cat /var/lib/kubelet/config.yaml | grep -A2 cluster
# clusterDNS:
# - 10.96.0.10
# clusterDomain: cluster.local
```

**CoreDNS Corefile (stored as a ConfigMap):**

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

```
.:53 {
    errors
    health
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        upstream
        fallthrough in-addr.arpa ip6.arpa
    }
    prometheus :9153
    forward . /etc/resolv.conf
    cache 30
    reload
}
```

| Plugin | Purpose |
|---|---|
| `errors` | Logs errors to stdout |
| `health` | Health check endpoint at `:8080/health` |
| `kubernetes` | Watches K8s API, creates DNS records for services/pods |
| `prometheus` | Exposes metrics at `:9153/metrics` |
| `forward` | Forwards external queries (e.g., google.com) to upstream DNS |
| `cache 30` | Caches responses for 30 seconds |
| `reload` | Reloads Corefile on changes |

To modify CoreDNS behavior, edit the ConfigMap:

```bash
kubectl edit configmap coredns -n kube-system
```

### DNS Name Hierarchy

```
<hostname>.<namespace>.<type>.<root>

Services:  web-service.default.svc.cluster.local
Pods:      10-244-2-5.default.pod.cluster.local
```

| Component | Service Example | Pod Example |
|---|---|---|
| Hostname | `web-service` | `10-244-2-5` (IP with dots → dashes) |
| Namespace | `default` | `default` |
| Type | `svc` | `pod` |
| Root | `cluster.local` | `cluster.local` |

### Pod DNS Records

By default, Kubernetes creates DNS records for services but not for individual pods. When pod DNS is enabled (via the `pods insecure` option in the Corefile), pod IPs are converted to hostnames by replacing dots with dashes:

```bash
# Pod with IP 10.244.2.5 in the default namespace
host 10-244-2-5.default.pod.cluster.local
# 10-244-2-5.default.pod.cluster.local has address 10.244.2.5

# Service resolution (works with short names due to search entries)
host web-service
# web-service.default.svc.cluster.local has address 10.107.37.188

# Pod resolution requires the full FQDN (search entries don't cover .pod)
host 10-244-2-5
# Host 10-244-2-5 not found: 3(NXDOMAIN)

host 10-244-2-5.default.pod.cluster.local
# 10-244-2-5.default.pod.cluster.local has address 10.244.2.5
```

Services can use short names because the `search` entries in `/etc/resolv.conf` append `.default.svc.cluster.local`. Pod DNS records require the full FQDN because `.pod.cluster.local` is not in the search list.

### Networking Debugging Checklist

Use this checklist when debugging connectivity issues:

| Problem | What to Check | Command |
|---------|--------------|---------|
| Pod can't reach another pod | CNI plugin running? DNS working? | `kubectl exec <pod> -- nslookup <target>` |
| Service name doesn't resolve | Service exists? Selector labels match? | `kubectl get endpoints <svc>` — should show pod IPs |
| Service has no endpoints | Pod labels don't match service selector | `kubectl describe svc <svc>` — compare `Selector:` with pod labels |
| Ingress returns 404 | Host/path config correct? Ingress controller running? | `kubectl describe ingress <name>` — check rules and backend |
| NodePort works but LoadBalancer doesn't | Cloud LB controller running? Security groups allow traffic? | `kubectl get svc <svc>` — check `EXTERNAL-IP` status |
| DNS lookup fails inside pod | CoreDNS pods healthy? | `kubectl get pods -n kube-system -l k8s-app=kube-dns` |
| Connection timeout between pods | NetworkPolicy blocking traffic? | `kubectl get networkpolicy -n <ns>` — check ingress/egress rules |

**Step-by-step DNS and service debugging from inside a pod:**

```bash
# 1. Start a debug pod with networking tools
kubectl run debug --image=nicolaka/netshoot --rm -it -- bash

# 2. Check DNS resolution
nslookup myservice.default.svc.cluster.local
# Server:    10.96.0.10
# Address:   10.96.0.10#53
# Name:      myservice.default.svc.cluster.local
# Address:   10.100.200.50

# 3. Test HTTP connectivity
curl -sv http://myservice:80/health
# * Connected to myservice (10.100.200.50) port 80
# < HTTP/1.1 200 OK

# 4. Check DNS configuration
cat /etc/resolv.conf
# nameserver 10.96.0.10
# search default.svc.cluster.local svc.cluster.local cluster.local

# 5. Verify endpoints exist
# (from outside the debug pod)
kubectl get endpoints myservice
# NAME        ENDPOINTS                                AGE
# myservice   10.244.0.5:8080,10.244.1.3:8080          5m

# 6. If endpoints are empty, check selector match
kubectl get svc myservice -o jsonpath='{.spec.selector}'
# {"app":"webapp"}
kubectl get pods -l app=webapp
# Should show matching pods
```

> **Cross-reference:** Network Policies → MODULE-15; Ingress troubleshooting → MODULE-29 Section 29.3

---

