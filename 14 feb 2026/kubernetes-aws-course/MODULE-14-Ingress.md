# MODULE 14: Ingress & Gateway API

---

## 14.1 Ingress — HTTP/HTTPS Routing

Ingress provides HTTP/HTTPS routing, SSL termination, and name-based virtual hosting. It's the standard way to expose web applications.

**Why Ingress instead of multiple LoadBalancer services?** Each LoadBalancer service provisions a separate cloud load balancer — with multiple services, you pay for multiple load balancers and manage separate SSL certificates, firewall rules, and DNS entries. Ingress consolidates all routing behind a single load balancer, reducing cost and administrative overhead.

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Internet                                                │
│      │                                                   │
│      ▼                                                   │
│  ┌── AWS ALB (Ingress Controller) ──────────────────┐    │
│  │                                                   │    │
│  │  api.example.com/users  → user-service:80         │    │
│  │  api.example.com/orders → order-service:80        │    │
│  │  app.example.com        → frontend-service:80     │    │
│  │                                                   │    │
│  └───────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Install AWS Load Balancer Controller

```bash
# Create IAM policy
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.2/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Create service account
eksctl create iamserviceaccount \
  --cluster=my-k8s-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::123456789012:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install via Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-k8s-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify
kubectl get deployment -n kube-system aws-load-balancer-controller

# Output:
# NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
# aws-load-balancer-controller   2/2     2            2           30s
```

### Basic Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/abc-123
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/healthcheck-path: /health
spec:
  ingressClassName: alb
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 80
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80

  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

```bash
kubectl apply -f ingress.yaml

kubectl get ingress

# Output:
# NAME          CLASS   HOSTS                              ADDRESS                                                    PORTS   AGE
# app-ingress   alb     api.example.com,app.example.com    k8s-default-appingre-abc123-456789.us-east-1.elb.amazonaws.com   80      2m

# Check ALB details
kubectl describe ingress app-ingress

# Output:
# Name:             app-ingress
# Namespace:        default
# Address:          k8s-default-appingre-abc123-456789.us-east-1.elb.amazonaws.com
# Rules:
#   Host              Path  Backends
#   ----              ----  --------
#   api.example.com
#                     /users    user-service:80 (10.0.1.15:8080,10.0.2.25:8080)
#                     /orders   order-service:80 (10.0.1.16:8080,10.0.2.26:8080)
#   app.example.com
#                     /         frontend-service:80 (10.0.1.17:3000,10.0.2.27:3000)
```

**`pathType` values:**

| pathType | Behavior | Example |
|---|---|---|
| `Prefix` | Matches the URL path prefix split by `/` | `/wear` matches `/wear`, `/wear/`, `/wear/shirts` |
| `Exact` | Matches the URL path exactly | `/wear` matches only `/wear`, not `/wear/` or `/wear/shirts` |

Use `Prefix` for most cases. Use `Exact` when you need strict path matching (e.g., distinguishing `/api` from `/api/v2`).

```bash
# Test pathType behavior:

# With pathType: Prefix and path: /wear
curl http://myapp.example.com/wear          # ✅ matches
curl http://myapp.example.com/wear/         # ✅ matches
curl http://myapp.example.com/wear/shirts   # ✅ matches
curl http://myapp.example.com/wearable      # ❌ does NOT match (Prefix splits on /)

# With pathType: Exact and path: /wear
curl http://myapp.example.com/wear          # ✅ matches
curl http://myapp.example.com/wear/         # ❌ does NOT match
curl http://myapp.example.com/wear/shirts   # ❌ does NOT match
```

### Ingress with TLS

```yaml
# tls-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: secure-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/abc-123
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
spec:
  ingressClassName: alb
  tls:
  - hosts:
    - app.example.com
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp
            port:
              number: 80
```

### Nginx Ingress Controller (Alternative to ALB)

For non-AWS or multi-cloud environments, nginx-ingress is the most popular Ingress controller:

```bash
# Install nginx-ingress via Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Verify
kubectl get pods -n ingress-nginx

# Output:
# NAME                                        READY   STATUS    RESTARTS   AGE
# ingress-nginx-controller-5b8f4d7c9-abc12    1/1     Running   0          30s

kubectl get svc -n ingress-nginx

# Output:
# NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP                          PORT(S)
# ingress-nginx-controller             LoadBalancer   172.20.89.123   a1b2c3.elb.amazonaws.com             80:31234/TCP,443:31235/TCP
```

```yaml
# nginx-ingress.yaml — uses nginx instead of ALB
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx          # Use nginx instead of alb
  tls:
  - hosts:
    - app.example.com
    secretName: tls-secret         # TLS cert stored as K8s Secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

**Ingress Controller Comparison:**

| Controller | Provider | L7 Features | Best For |
|---|---|---|---|
| **AWS ALB** | AWS | Path/host routing, WAF, Cognito auth | EKS production |
| **nginx-ingress** | Community | Rewrite, rate limiting, basic auth | Multi-cloud, on-prem |
| **Traefik** | Traefik Labs | Auto-discovery, Let's Encrypt | Docker/K8s hybrid |
| **Istio Gateway** | Istio | Full mesh integration, mTLS | Service mesh users |

### How an Ingress Controller Works Internally

```
┌──────────────────────────────────────────────────────────────┐
│  Ingress Controller Internal Flow                            │
│                                                              │
│  Step 1: Controller pod starts and watches the API Server    │
│          for Ingress, Service, and Endpoint changes          │
│                                                              │
│  Step 2: User creates/updates an Ingress resource            │
│          kubectl apply -f ingress.yaml                       │
│                                                              │
│  Step 3: API Server notifies the controller (watch event)    │
│                                                              │
│  Step 4: Controller reads the Ingress rules:                 │
│          - host: api.example.com, path: /users → user-svc    │
│          - host: app.example.com, path: /     → frontend-svc │
│                                                              │
│  Step 5: Controller looks up Service endpoints               │
│          user-svc → [10.0.1.15:8080, 10.0.2.25:8080]        │
│          frontend-svc → [10.0.1.16:3000, 10.0.2.26:3000]    │
│                                                              │
│  Step 6: Controller generates/updates its config:            │
│          - nginx: generates nginx.conf, reloads nginx        │
│          - ALB: calls AWS API to update ALB target groups    │
│          - Traefik: updates in-memory routing table          │
│                                                              │
│  Step 7: External traffic arrives:                           │
│          Client → DNS → Load Balancer → Ingress Controller   │
│          Controller matches Host + Path → routes to pod IP   │
│                                                              │
│  Step 8: Controller continuously watches for changes         │
│          (new Ingress, Service scaling, pod IP changes)       │
│          and updates its config automatically                │
└──────────────────────────────────────────────────────────────┘
```

```bash
# See what the nginx-ingress controller generated
kubectl exec -n ingress-nginx deploy/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A5 "location /users"

# Output:
# location /users {
#     proxy_pass http://upstream_user_service;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
# }

# Watch the controller's logs to see config reloads
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller -f

# Output (when Ingress is created/updated):
# I0115 10:00:00.000000 Configuration changes detected, backend reload required
# I0115 10:00:00.100000 Backend successfully reloaded
```

**Key points:**
- The Ingress resource is just data — it does nothing by itself
- The Ingress Controller is the actual reverse proxy that reads Ingress resources and implements routing
- The controller runs as a pod (Deployment) inside the cluster
- It continuously watches the API Server for changes and auto-updates its config
- For nginx-ingress: generates `nginx.conf` and reloads nginx
- For AWS ALB: calls AWS APIs to create/update ALB rules and target groups

**Interview question: What is an Ingress Controller and why is it needed?**
An Ingress resource is just a configuration object — it defines routing rules. An Ingress Controller is the actual reverse proxy (nginx, ALB, Traefik) that reads Ingress resources and implements the routing. The controller watches the API Server for Ingress changes, looks up Service endpoints, generates its routing config (e.g., nginx.conf), and routes incoming traffic to the correct pod IPs. Without a controller, Ingress resources do nothing. On EKS, the AWS Load Balancer Controller creates ALBs; on other platforms, nginx-ingress is the standard choice.

### Creating Ingress Resources Imperatively

Use `kubectl create ingress` to quickly create Ingress resources without writing YAML:

```bash
# Create an Ingress with a single path rule
kubectl create ingress my-ingress --rule="/api=api-service:8080"

# Create with multiple path rules
kubectl create ingress app-ingress \
  --rule="/wear=wear-service:8080" \
  --rule="/watch=video-service:8080"

# Create in a specific namespace
kubectl create ingress ingress-pay -n critical-space \
  --rule="/pay=pay-service:8282"

# Add annotations (e.g., rewrite-target) after creation
kubectl annotate ingress ingress-pay -n critical-space \
  nginx.ingress.kubernetes.io/rewrite-target=/
```

To modify paths on an existing Ingress, use `kubectl edit`:

```bash
kubectl edit ingress app-ingress -n app-space
# Change path: /watch → path: /stream
# Add new path entries as needed
```

### Ingress Namespace Rules

An Ingress resource must be created in the **same namespace** as the backend services it references. An Ingress in namespace `A` cannot route to a Service in namespace `B`.

```bash
# App and Ingress in the same namespace — works
kubectl get deploy -n app-space
# webapp-wear, webapp-video

kubectl get ingress -n app-space
# ingress-wear-watch → routes to wear-service, video-service (both in app-space)

# Payment app in its own namespace — needs its own Ingress
kubectl get deploy -n critical-space
# webapp-pay

kubectl create ingress ingress-pay -n critical-space \
  --rule="/pay=pay-service:8282"
```

### Troubleshooting: rewrite-target Annotation

When an app serves content at `/` but the Ingress routes to it via a sub-path like `/pay`, the app receives requests at `/pay` and returns 404 because it doesn't have that route.

```bash
# Without rewrite-target:
# Client → /pay → Ingress → forwards /pay to pay-service → app gets /pay → 404

# Check the app logs to confirm
kubectl logs -n critical-space deploy/webapp-pay
# 10.244.0.9 - - "GET /pay HTTP/1.1" 404 -
```

Fix by adding the `rewrite-target` annotation, which strips the path prefix before forwarding:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

```bash
# With rewrite-target: /
# Client → /pay → Ingress → rewrites to / → forwards / to pay-service → app gets / → 200
```

This is needed whenever the Ingress path doesn't match the app's internal routes. Common examples: `/pay` → `/`, `/api/v1` → `/`, `/app` → `/`.

### Default Backend for Unmatched Traffic

When a request doesn't match any Ingress rule (e.g., a user visits `/listen` but only `/wear` and `/watch` are defined), the Ingress controller returns a 404. Use `defaultBackend` to route unmatched traffic to a custom service (e.g., a custom 404 page):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  defaultBackend:
    service:
      name: custom-404-service
      port:
        number: 80
  rules:
  - http:
      paths:
      - path: /wear
        pathType: Prefix
        backend:
          service:
            name: wear-service
            port:
              number: 80
```

If no `defaultBackend` is specified, the Ingress controller uses its own default (typically a built-in 404 page).

```bash
kubectl apply -f app-ingress.yaml
kubectl describe ingress app-ingress

# Output:
# Name:             app-ingress
# Default backend:  custom-404-service:80 (10.0.1.50:8080)
# Rules:
#   Host        Path  Backends
#   ----        ----  --------
#   *
#               /wear   wear-service:80 (10.0.1.15:8080)
# Annotations:  <none>
#
# Any request not matching /wear goes to custom-404-service
```

### Troubleshooting: HTTP 308 Redirect Loop

nginx-ingress redirects HTTP to HTTPS by default. If TLS is not configured, this causes an infinite 308 redirect loop:

```bash
# Check the Ingress controller logs
kubectl logs -n ingress-nginx deploy/ingress-nginx-controller | grep 308
# 10.244.0.9 - - "GET /watch HTTP/1.1" 308 171 "-" "Mozilla/5.0 ..."
```

Fix by disabling SSL redirect on the Ingress resource:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
```

Or via `kubectl annotate`:

```bash
kubectl annotate ingress my-ingress -n app-space \
  nginx.ingress.kubernetes.io/ssl-redirect="false"
```

### Exposing the Ingress Controller

On bare-metal or self-managed clusters (no cloud LoadBalancer), expose the Ingress controller via NodePort:

```bash
# Expose the controller deployment as a NodePort service
kubectl expose deploy ingress-controller -n ingress-space \
  --name ingress --port=80 --target-port=80 --type NodePort

# Verify
kubectl get svc -n ingress-space
# NAME      TYPE       CLUSTER-IP      PORT(S)        AGE
# ingress   NodePort   10.109.33.190   80:30080/TCP   9s

# Edit to set a specific NodePort if needed
kubectl edit svc ingress -n ingress-space
```

On cloud providers, the Ingress controller service is typically `type: LoadBalancer`, which provisions a cloud load balancer automatically.

---

## 14.2 Gateway API — Next-Generation Ingress

Gateway API is the successor to Ingress, addressing its key limitations: multi-tenancy, annotation-dependent configuration, and HTTP-only routing.

### Why Gateway API?

**Ingress limitations:**
- Single resource controlled by one team — coordination issues in multi-tenant environments
- Advanced features (TLS redirect, CORS, rate limiting) require controller-specific annotations
- Annotations are not validated by Kubernetes — different controllers use different syntax
- HTTP-only — no native TCP, UDP, or gRPC support

**The annotation problem — same feature, different syntax per controller:**

```yaml
# NGINX: CORS via annotations
metadata:
  annotations:
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, PUT, POST"
    nginx.ingress.kubernetes.io/cors-allow-origin: "https://allowed-origin.com"
```

```yaml
# Traefik: CORS via completely different annotations
metadata:
  annotations:
    traefik.ingress.kubernetes.io/headers.customresponseheaders: |
      Access-Control-Allow-Origin: '*'
      Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

```yaml
# NGINX: Canary deployment via annotations
metadata:
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "20"
```

Switching controllers means rewriting all annotations. Gateway API eliminates this by using standardized, validated fields (`filters`, `weight`, `tls`) that work identically across all implementations.

### Three-Object Model

Gateway API splits responsibilities across three personas:

```
Infrastructure Provider          Cluster Operator           App Developer
       │                              │                          │
       ▼                              ▼                          ▼
  GatewayClass ──────────────→  Gateway ──────────────→  HTTPRoute
  (defines controller)      (creates listener)       (defines routing rules)
```

| Object | Who Manages | Purpose |
|---|---|---|
| `GatewayClass` | Infrastructure provider | Defines the controller (NGINX, Envoy, AWS ALB) |
| `Gateway` | Cluster operator | Creates listeners (ports, protocols, TLS) |
| `HTTPRoute` | App developer | Defines routing rules (paths, headers, backends) |

### GatewayClass

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: example-class
spec:
  controllerName: example.com/gateway-controller
```

### Gateway

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-gateway
spec:
  gatewayClassName: example-class
  listeners:
  - name: http
    protocol: HTTP
    port: 80
```

### HTTPRoute

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: example-httproute
spec:
  parentRefs:
  - name: example-gateway
  hostnames:
  - "www.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /login
    backendRefs:
    - name: example-svc
      port: 8080
```

### TLS Termination

Ingress requires annotations for SSL redirect. Gateway API handles TLS natively:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: secure-gateway
spec:
  gatewayClassName: example-gc
  listeners:
  - name: https
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs:
      - kind: Secret
        name: tls-secret
    allowedRoutes:
      kinds:
      - kind: HTTPRoute
```

### Traffic Splitting (Canary Deployments)

Ingress requires controller-specific annotations for canary. Gateway API declares weights directly:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: split-traffic
spec:
  parentRefs:
  - name: app-gateway
  rules:
  - backendRefs:
    - name: app-v1
      port: 80
      weight: 80
    - name: app-v2
      port: 80
      weight: 20
```

80% of traffic goes to `app-v1`, 20% to `app-v2` — no annotations needed, works across all Gateway API implementations.

### CORS via Filters

Instead of controller-specific annotations, Gateway API uses standardized filters:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: cors-route
spec:
  parentRefs:
  - name: my-gateway
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    filters:
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        add:
        - name: Access-Control-Allow-Origin
          value: "*"
        - name: Access-Control-Allow-Methods
          value: "GET, POST, PUT, DELETE, OPTIONS"
    backendRefs:
    - name: api-service
      port: 8080
```

### Gateway API vs Ingress

| Feature | Ingress | Gateway API |
|---|---|---|
| Multi-tenancy | Single resource, one owner | Split across GatewayClass/Gateway/HTTPRoute |
| Protocols | HTTP/HTTPS only | HTTP, HTTPS, TCP, UDP, gRPC |
| TLS config | Annotations + `spec.tls` | Native `tls` block in Gateway listener |
| Traffic splitting | Controller-specific annotations | `weight` field in backendRefs |
| CORS/headers | Controller-specific annotations | Standardized filters |
| Validation | Annotations not validated | Full CRD validation |
| Controller support | NGINX, Traefik, HAProxy, etc. | NGINX, Envoy, Istio, Kong, AWS ALB, GKE, Azure, etc. |

### Route Types

| Route | Protocol | Example |
|---|---|---|
| `HTTPRoute` | HTTP/HTTPS | Web apps, REST APIs |
| `TCPRoute` | TCP | Databases, custom TCP services |
| `TLSRoute` | TLS passthrough | End-to-end encryption |
| `UDPRoute` | UDP | DNS, gaming servers |
| `GRPCRoute` | gRPC | Microservice communication |

---

