# MODULE 36: Industry Projects

---

## Project 1: Production-Grade Microservices E-Commerce Platform

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                                 │
│                                                                 │
│  ┌─── Route 53 ───┐                                            │
│  │ shop.example.com│                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│  ┌────────▼────────┐                                            │
│  │   AWS ALB       │  ← Ingress Controller                     │
│  │   (HTTPS/TLS)   │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│  ┌────────▼──────────────── EKS Cluster ──────────────────────┐ │
│  │                                                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │  │ Frontend │  │ Product  │  │  Order   │  │ Payment  │   │ │
│  │  │ (React)  │  │ Service  │  │ Service  │  │ Service  │   │ │
│  │  │ 3 pods   │  │ 3 pods   │  │ 3 pods   │  │ 2 pods   │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │ │
│  │                                                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │ │
│  │  │  Redis   │  │PostgreSQL│  │  Kafka   │                  │ │
│  │  │ (cache)  │  │ (primary │  │ (events) │                  │ │
│  │  │ 3 pods   │  │ +replica)│  │ 3 brokers│                  │ │
│  │  └──────────┘  └──────────┘  └──────────┘                  │ │
│  │                                                             │ │
│  │  ┌──────────────── Monitoring ──────────────────────────┐   │ │
│  │  │ Prometheus │ Grafana │ AlertManager │ Fluent Bit     │   │ │
│  │  └──────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌── External Services ──────────────────────────────────────┐  │
│  │ Amazon RDS (backup DB) │ S3 (images) │ SES (emails)       │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Namespace Setup

```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ecommerce
  labels:
    app: ecommerce
    pod-security.kubernetes.io/enforce: baseline
---
apiVersion: v1
kind: Namespace
metadata:
  name: ecommerce-data
  labels:
    app: ecommerce-data
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ecommerce-quota
  namespace: ecommerce
spec:
  hard:
    requests.cpu: "20"
    requests.memory: "40Gi"
    limits.cpu: "40"
    limits.memory: "80Gi"
    pods: "100"
```

### Step 2: Product Service (Go Microservice)

```yaml
# product-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: product-service
  namespace: ecommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: product-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: product-service
        version: v2.3.1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: product-service-sa
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: product-service
      containers:
      - name: product-service
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/product-service:v2.3.1
        ports:
        - name: http
          containerPort: 8080
        - name: metrics
          containerPort: 9090
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: db-config
              key: host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: REDIS_URL
          value: "redis-headless.ecommerce-data.svc.cluster.local:6379"
        - name: KAFKA_BROKERS
          value: "kafka-0.kafka-headless.ecommerce-data.svc.cluster.local:9092,kafka-1.kafka-headless.ecommerce-data.svc.cluster.local:9092"
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "500m"
            memory: "1Gi"
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
      volumes:
      - name: tmp
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: product-service
  namespace: ecommerce
spec:
  selector:
    app: product-service
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: product-service-hpa
  namespace: ecommerce
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: product-service
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Step 3: Frontend (React App)

```yaml
# frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: ecommerce
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/frontend:v1.5.0
        ports:
        - containerPort: 3000
        env:
        - name: REACT_APP_API_URL
          value: "https://api.shop.example.com"
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "200m"
            memory: "512Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: ecommerce
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
```

### Step 4: Ingress with Path-Based Routing

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ecommerce-ingress
  namespace: ecommerce
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789012:certificate/abc-123
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/group.name: ecommerce
spec:
  ingressClassName: alb
  rules:
  - host: shop.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.shop.example.com
    http:
      paths:
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 80
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /payments
        pathType: Prefix
        backend:
          service:
            name: payment-service
            port:
              number: 80
```

### Step 5: Database (PostgreSQL StatefulSet)

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ecommerce-data
spec:
  serviceName: postgres-headless
  replicas: 2
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15.4
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: ecommerce
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
        readinessProbe:
          exec:
            command: ["pg_isready", "-U", "$(POSTGRES_USER)"]
          initialDelaySeconds: 10
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: ecommerce-data
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
---
# CronJob for daily backups
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: ecommerce-data
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: backup-sa
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:15.4
            command:
            - /bin/sh
            - -c
            - |
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              pg_dump -h postgres-0.postgres-headless -U $PGUSER -d ecommerce | \
                gzip > /tmp/backup_${TIMESTAMP}.sql.gz
              aws s3 cp /tmp/backup_${TIMESTAMP}.sql.gz \
                s3://ecommerce-backups/postgres/backup_${TIMESTAMP}.sql.gz
              echo "Backup completed: backup_${TIMESTAMP}.sql.gz"
            env:
            - name: PGUSER
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: username
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-credentials
                  key: password
```

### Step 6: Network Policies

```yaml
# network-policies.yaml
# Default deny all in ecommerce namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: ecommerce
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow frontend to receive traffic from ALB
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-frontend
  namespace: ecommerce
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - ports:
    - port: 3000
---
# Allow product-service to talk to postgres and redis
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: product-service-egress
  namespace: ecommerce
spec:
  podSelector:
    matchLabels:
      app: product-service
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          app: ecommerce-data
    ports:
    - port: 5432    # PostgreSQL
    - port: 6379    # Redis
    - port: 9092    # Kafka
  - to:             # Allow DNS
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

### Deployment Commands

```bash
# Deploy everything
kubectl apply -f namespaces.yaml
kubectl apply -f secrets/
kubectl apply -f configmaps/
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f kafka.yaml
kubectl apply -f product-service.yaml
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml
kubectl apply -f frontend.yaml
kubectl apply -f ingress.yaml
kubectl apply -f network-policies.yaml

# Verify
kubectl get all -n ecommerce
kubectl get all -n ecommerce-data

# Test the application
curl -k https://shop.example.com
curl -k https://api.shop.example.com/products
```

---

## Project 2: CI/CD Pipeline with Blue-Green Deployment

### Architecture

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  GitHub Push → GitHub Actions → Build Image → ECR    │
│                                      │               │
│                                      ▼               │
│                              ArgoCD Sync             │
│                                      │               │
│                    ┌─────────────────┼──────────┐    │
│                    │                 │          │    │
│                    ▼                 ▼          │    │
│              ┌──────────┐    ┌──────────┐      │    │
│  Service ──→ │  Blue    │    │  Green   │      │    │
│  (active)    │  v1.0    │    │  v2.0    │      │    │
│              │  3 pods  │    │  3 pods  │      │    │
│              └──────────┘    └──────────┘      │    │
│                                                │    │
│              After testing, switch Service ──→  │    │
│              to Green, scale down Blue         │    │
│                                                │    │
└──────────────────────────────────────────────────────┘
```

```yaml
# blue-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-blue
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: blue
  template:
    metadata:
      labels:
        app: webapp
        version: blue
    spec:
      containers:
      - name: webapp
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/webapp:v1.0.0
        ports:
        - containerPort: 8080
---
# green-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-green
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: green
  template:
    metadata:
      labels:
        app: webapp
        version: green
    spec:
      containers:
      - name: webapp
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/webapp:v2.0.0
        ports:
        - containerPort: 8080
---
# service.yaml — Switch between blue and green
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
  namespace: production
spec:
  selector:
    app: webapp
    version: blue          # Change to "green" to switch
  ports:
  - port: 80
    targetPort: 8080
```

```bash
# Switch traffic from blue to green
kubectl patch service webapp-service -n production \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Output:
# service/webapp-service patched

# Verify traffic goes to green
kubectl describe service webapp-service -n production | grep Selector

# Output:
# Selector: app=webapp,version=green

# If issues, rollback to blue instantly
kubectl patch service webapp-service -n production \
  -p '{"spec":{"selector":{"version":"blue"}}}'

# Scale down old version after verification
kubectl scale deployment webapp-blue -n production --replicas=0
```

**How Blue-Green works step by step:**

```
1. Blue (v1.0) is running and serving traffic via the Service
2. Deploy Green (v2.0) alongside Blue — both run simultaneously
3. Test Green internally (port-forward, internal curl)
4. Switch the Service selector from blue → green (instant cutover)
5. All traffic now goes to Green
6. If problems: switch back to blue (instant rollback)
7. If stable: scale down Blue to 0 replicas
```

**Deployment strategy comparison:**

| Strategy | Downtime | Rollback Speed | Resource Cost | Risk |
|---|---|---|---|---|
| **Rolling Update** (default) | Zero | Slow (rollout undo) | 1x + surge | Gradual, mixed versions briefly |
| **Blue-Green** | Zero | Instant (switch selector) | 2x (both versions run) | All-or-nothing switch |
| **Canary** | Zero | Fast (shift traffic back) | 1x + canary pods | Gradual, % of users see new version |
| **Recreate** | Yes (brief) | Slow (redeploy old) | 1x | All pods killed before new ones start |

**Interview question: How does Blue-Green deployment work in Kubernetes?**
Run two identical deployments (Blue=current, Green=new) with different version labels. A Service selector points to Blue. Deploy Green alongside Blue, test it internally, then switch the Service selector to Green for instant cutover. Rollback is instant — just switch the selector back to Blue. The trade-off is 2x resource cost during the transition since both versions run simultaneously.

---

## Project 3: Multi-Tenant SaaS Platform

### Multi-Tenancy Models

Kubernetes supports two primary tenancy models with different isolation requirements:

| | Multi-Team | Multi-Customer |
|---|---|---|
| **Tenants** | Internal teams/departments | External customers/clients |
| **Access** | Direct cluster access (kubectl, GitOps) | No direct cluster access; managed behind the scenes |
| **Isolation** | Namespace-level with RBAC | Namespace-level with strict network, storage, and DNS isolation |
| **Compliance** | Internal policies | Regulatory (GDPR, HIPAA, SOC2) |
| **Security** | Trust boundary within organization | Zero-trust between tenants |
| **Example** | Dev, QA, and platform teams sharing a cluster | SaaS provider hosting multiple customer workloads |

Multi-team tenancy focuses on fair resource sharing and preventing accidental interference. Multi-customer tenancy demands stronger isolation — tenants must not be able to discover, access, or affect each other's workloads, data, or network traffic.

### Isolation Layers

Kubernetes provides isolation at multiple levels, each adding security at a different scope:

| Layer | Mechanism | What It Isolates | Module Reference |
|---|---|---|---|
| **Namespace** | Namespaces + RBAC | API resources, roles, quotas | [MODULE-08](MODULE-08-Namespaces.md), [MODULE-22](MODULE-22-RBAC.md) |
| **Pod** | SecurityContext, PSA | Process-level: user IDs, capabilities, filesystem | [MODULE-21](MODULE-21-Pod-Security.md) |
| **Network** | NetworkPolicy, mTLS | Pod-to-pod traffic, cross-namespace communication | [MODULE-15](MODULE-15-Network-Policies.md), [MODULE-35](MODULE-35-Service-Mesh.md) |
| **Storage** | Per-tenant StorageClasses | Persistent volume access, IOPS isolation | [MODULE-17](MODULE-17-Storage.md) |
| **Node** | Taints + tolerations, node affinity | Compute resources, kernel-level isolation | [MODULE-19](MODULE-19-Scheduling.md) |
| **DNS** | CoreDNS `fallthrough in-namespace` | Service name discovery across namespaces | See below |

**Hard vs Soft Isolation:**

| | Soft Isolation | Hard Isolation |
|---|---|---|
| **Infrastructure** | Shared nodes, shared control plane | Dedicated nodes per tenant (or separate clusters) |
| **Enforcement** | Namespaces, RBAC, NetworkPolicy, ResourceQuota | Taints/tolerations + node affinity to pin tenants to nodes |
| **Cost** | Lower — better resource utilization | Higher — dedicated resources per tenant |
| **Security** | Logical separation; kernel is shared | Physical separation; no shared kernel attack surface |
| **Use case** | Multi-team, low-risk workloads | Multi-customer, regulated industries, untrusted workloads |

Most clusters use soft isolation. Hard isolation (dedicated nodes) is needed when tenants run untrusted code or when compliance requires physical separation.

The architecture below implements multi-customer tenancy with namespace isolation, RBAC, network policies, DNS restrictions, and per-tenant storage classes.

### Architecture for Tenant Isolation

```yaml
# Each tenant gets their own namespace with resource quotas
# tenant-onboarding.yaml

# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-acme-corp
  labels:
    tenant: acme-corp
    tier: enterprise
---
# Resource Quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-quota
  namespace: tenant-acme-corp
spec:
  hard:
    requests.cpu: "8"
    requests.memory: "16Gi"
    limits.cpu: "16"
    limits.memory: "32Gi"
    pods: "30"
    services: "10"
    persistentvolumeclaims: "5"
---
# Network Policy — Isolate tenant
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: tenant-isolation
  namespace: tenant-acme-corp
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          tenant: acme-corp
    - namespaceSelector:
        matchLabels:
          name: ingress-system
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          tenant: acme-corp
  - to:
    - namespaceSelector: {}
    ports:
    - port: 53
      protocol: UDP
---
# RBAC — Tenant admin role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: tenant-admin
  namespace: tenant-acme-corp
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "services", "configmaps", "secrets", "jobs"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["persistentvolumeclaims"]
  verbs: ["get", "list", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-admin-binding
  namespace: tenant-acme-corp
subjects:
- kind: Group
  name: acme-corp-admins
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: tenant-admin
  apiGroup: rbac.authorization.k8s.io
```

### DNS Isolation Between Tenants

By default, any pod can resolve services in any namespace using FQDNs like `backend.namespace-a.svc.cluster.local`. In multi-tenant clusters, this allows tenants to discover each other's services even when network policies block actual traffic.

To restrict cross-namespace DNS resolution, configure CoreDNS with the `fallthrough in-namespace` directive:

```bash
kubectl edit configmap coredns -n kube-system
```

```yaml
# CoreDNS ConfigMap — restrict DNS to same namespace
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
            lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
            pods verified
            fallthrough in-namespace    # Only resolve names within the querying pod's namespace
        }
        prometheus :9153
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

CoreDNS reloads the Corefile automatically after the ConfigMap is updated.

**Testing DNS isolation:**

```bash
# From namespace-a, try to resolve a service in namespace-b
kubectl run test-pod --rm -i --tty --image=busybox --restart=Never \
  --namespace=namespace-a -- nslookup backend.namespace-b.svc.cluster.local

# With fallthrough in-namespace: this lookup should FAIL
# Without it: this lookup resolves normally
```

> ⚠️ Misconfiguring CoreDNS can break all service discovery. Test in a non-production cluster first. Network policies (shown above) block actual traffic; DNS isolation prevents service name discovery.

### Storage Isolation with Per-Tenant StorageClasses

Assign different StorageClasses to tenants based on their performance requirements. This prevents a noisy-neighbor tenant from consuming IOPS that a critical tenant needs:

```yaml
# High-performance storage for critical tenants
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tenant-critical
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iopsPerGB: "50"
  encrypted: "true"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
# Standard storage for regular tenants
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: tenant-standard
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

Enforce which StorageClass a tenant can use via ResourceQuota:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: tenant-acme-corp
spec:
  hard:
    tenant-critical.storageclass.storage.k8s.io/requests.storage: "100Gi"
    tenant-standard.storageclass.storage.k8s.io/requests.storage: "500Gi"
```

> See [MODULE-17 §17.6](MODULE-17-Storage.md) for StorageClass deep dive and provider comparison.

---

## Project 4: ML Model Serving Platform

```yaml
# ml-inference.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model-server
  namespace: ml-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-model-server
  template:
    metadata:
      labels:
        app: ml-model-server
    spec:
      nodeSelector:
        node.kubernetes.io/instance-type: g4dn.xlarge    # GPU instance
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: model-server
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/ml-model:v1.0
        ports:
        - containerPort: 8501
        resources:
          requests:
            cpu: "2"
            memory: "8Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "4"
            memory: "16Gi"
            nvidia.com/gpu: 1
        env:
        - name: MODEL_PATH
          value: "s3://ml-models/production/model-v1"
        readinessProbe:
          httpGet:
            path: /v1/models/default
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-model-hpa
  namespace: ml-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-model-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: inference_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

---

## Project 5: AI Chatbot — Full DevOps Lifecycle

**Why this project matters:** Unlike the previous projects that focus on specific patterns (microservices, blue-green, multi-tenancy, GPU scheduling), this project walks through the **complete lifecycle** of a single application — from code to infrastructure to CI/CD to monitoring to security — showing how every Kubernetes concept connects in practice.

**Stack:** Python/Flask + OpenAI API | Docker | Kubernetes | Terraform (AWS) | GitHub Actions | Prometheus/Grafana | Trivy/CodeQL/Dependabot

### 5.1 Application — Python Flask Chatbot API

```python
# app.py
from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}]
    )
    return jsonify({
        "reply": response.choices[0].message.content
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### 5.2 Dockerfile — Multi-Stage Build

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /install /usr/local
COPY app.py .

USER appuser
EXPOSE 5000
CMD ["python", "app.py"]
```

> **Cross-reference:** Multi-stage builds → MODULE-02 Section 2.7; non-root user → MODULE-21 Section 21.1

### 5.3 Kubernetes Manifests

```yaml
# chatbot-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot
  namespace: chatbot
  labels:
    app: chatbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot
  template:
    metadata:
      labels:
        app: chatbot
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: chatbot
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/chatbot:latest
        ports:
        - containerPort: 5000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: chatbot-secrets
              key: openai-api-key
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
```

> **Cross-reference:** SecurityContext → MODULE-21; Secrets → MODULE-16; Resource limits → MODULE-18; Probes → MODULE-10 Section 10.7

```yaml
# chatbot-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: chatbot
  namespace: chatbot
spec:
  selector:
    app: chatbot
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
---
# chatbot-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chatbot
  namespace: chatbot
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "10"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - chatbot.example.com
    secretName: chatbot-tls
  rules:
  - host: chatbot.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: chatbot
            port:
              number: 80
```

> **Cross-reference:** Services → MODULE-13; Ingress + TLS → MODULE-14

### 5.4 Network Policy and RBAC

```yaml
# chatbot-netpol.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chatbot-policy
  namespace: chatbot
spec:
  podSelector:
    matchLabels:
      app: chatbot
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx      # Only allow traffic from ingress controller
    ports:
    - port: 5000
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0           # Allow outbound to OpenAI API
    ports:
    - port: 443
  - to:
    - namespaceSelector: {}        # Allow DNS resolution
    ports:
    - port: 53
      protocol: UDP
---
# chatbot-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chatbot-sa
  namespace: chatbot
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: chatbot-role
  namespace: chatbot
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["chatbot-secrets"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: chatbot-binding
  namespace: chatbot
subjects:
- kind: ServiceAccount
  name: chatbot-sa
roleRef:
  kind: Role
  name: chatbot-role
  apiGroup: rbac.authorization.k8s.io
```

> **Cross-reference:** Network Policies → MODULE-15; RBAC → MODULE-22; Service Accounts → MODULE-24

### 5.5 HPA — Auto-Scaling

```yaml
# chatbot-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chatbot-hpa
  namespace: chatbot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chatbot
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300    # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60               # Remove max 25% of pods per minute
```

> **Cross-reference:** HPA → MODULE-18 Section 18.3

### 5.6 Terraform — AWS Infrastructure

```hcl
# main.tf — EKS cluster + supporting infrastructure
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0"

  name = "chatbot-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true    # Cost optimization for non-prod
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.0"

  cluster_name    = "chatbot-cluster"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  eks_managed_node_groups = {
    default = {
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 5
      desired_size   = 3
    }
  }
}

# Store OpenAI API key in AWS Secrets Manager
resource "aws_secretsmanager_secret" "openai_key" {
  name = "chatbot/openai-api-key"
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = "chatbot-terraform-state"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "aws:kms"
      }
    }
  }
}
```

### 5.7 CI/CD — GitHub Actions Pipeline

```yaml
# .github/workflows/deploy.yaml
name: Build, Scan, Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Run CodeQL Analysis
      uses: github/codeql-action/analyze@v2
      with:
        languages: python

    - name: Dependency Review (PRs only)
      if: github.event_name == 'pull_request'
      uses: actions/dependency-review-action@v3

  build-and-push:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: us-east-1

    - name: Login to ECR
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build Docker image
      run: docker build -t $ECR_REGISTRY/chatbot:${{ github.sha }} .

    - name: Trivy vulnerability scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.ECR_REGISTRY }}/chatbot:${{ github.sha }}
        severity: CRITICAL,HIGH
        exit-code: 1              # Fail pipeline on critical/high CVEs

    - name: Push to ECR
      run: docker push $ECR_REGISTRY/chatbot:${{ github.sha }}

  deploy:
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Configure kubectl
      uses: aws-actions/amazon-eks-update-kubeconfig@v1
      with:
        cluster-name: chatbot-cluster

    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/chatbot \
          chatbot=$ECR_REGISTRY/chatbot:${{ github.sha }} \
          -n chatbot
        kubectl rollout status deployment/chatbot -n chatbot --timeout=300s
```

**Pipeline flow:**

```
Push to main
  │
  ├─► CodeQL static analysis ──► Pass? ──► Build Docker image
  │                                              │
  │                                    Trivy scan (fail on HIGH/CRITICAL)
  │                                              │
  │                                    Push to ECR ──► Deploy to EKS
  │
  └─► Dependabot (automated PRs for vulnerable dependencies)
```

> **Cross-reference:** Trivy → MODULE-31 Section 31.5; CI/CD patterns → Project 2

### 5.8 Monitoring — Prometheus & Grafana

```yaml
# prometheus-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: chatbot-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: chatbot
  namespaceSelector:
    matchNames: ["chatbot"]
  endpoints:
  - port: http
    path: /metrics
    interval: 15s
```

Add a `/metrics` endpoint to the Flask app using `prometheus_flask_instrumentator`:

```python
# Add to app.py
from prometheus_flask_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

**Key metrics to monitor:**

| Metric | Alert Threshold | Why |
|--------|----------------|-----|
| `http_request_duration_seconds` | p99 > 5s | OpenAI API latency spikes |
| `http_requests_total{status="5xx"}` | > 5/min | Application errors |
| `container_memory_usage_bytes` | > 80% of limit | OOM risk |
| `kube_pod_container_status_restarts_total` | > 3 in 10min | Crash loop |

### 5.9 What This Project Ties Together

This project integrates concepts from **12 modules** in a single application:

| Concern | Module | Concept Used |
|---------|--------|-------------|
| Container build | MODULE-02 | Multi-stage Dockerfile, non-root user |
| Pod configuration | MODULE-10 | Probes, env vars from Secrets |
| Service exposure | MODULE-13, 14 | ClusterIP Service, Ingress with TLS |
| Network isolation | MODULE-15 | NetworkPolicy (ingress + egress) |
| Secrets management | MODULE-16 | Kubernetes Secrets, AWS Secrets Manager |
| Resource limits | MODULE-18 | Requests/limits, HPA |
| Pod security | MODULE-21 | SecurityContext, readOnlyRootFilesystem |
| RBAC | MODULE-22 | Role scoped to specific Secret |
| Service accounts | MODULE-24 | Dedicated SA with least privilege |
| Security scanning | MODULE-31 | Trivy image scan, pipeline integration |
| Monitoring | MODULE-35 | Prometheus ServiceMonitor |
| CI/CD | Project 2 | GitHub Actions, rolling deployment |

---


