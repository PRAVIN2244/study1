# Module 24: Kubernetes Storage & Networking

---

## 24.1 Kubernetes Storage — The Problem

Pods are ephemeral. When a pod dies, its filesystem is lost. Kubernetes needs a way to persist data across pod restarts and rescheduling — similar to Docker volumes but with cluster-level management.

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES STORAGE MODEL                        │
│                                                              │
│  Docker:                                                    │
│    docker run -v mydata:/data myapp                         │
│    Volume is local to the host                              │
│                                                              │
│  Kubernetes:                                                │
│    PersistentVolume (PV)   → the actual storage             │
│    PersistentVolumeClaim (PVC) → request for storage        │
│    StorageClass            → dynamic provisioning rules     │
│                                                              │
│  Pod → PVC → PV → Physical Storage                         │
│                                                              │
│  Why the extra abstraction?                                 │
│    Pods can move between nodes                              │
│    Storage must be accessible from any node                 │
│    Admins manage storage; developers request it             │
└─────────────────────────────────────────────────────────────┘
```

---

## 24.2 Persistent Volumes (PV)

A PV is a piece of storage provisioned by an administrator. It exists independently of any pod.

```yaml
# pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce        # Can be mounted read-write by one node
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:                # For single-node testing only
    path: /mnt/data
```

```bash
$ kubectl apply -f pv.yaml

$ kubectl get pv
# NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      STORAGECLASS
# my-pv   10Gi       RWO            Retain           Available   manual
```

### Access Modes

```
┌──────────────────────┬──────────────────────────────────────┐
│ Mode                 │ Description                          │
├──────────────────────┼──────────────────────────────────────┤
│ ReadWriteOnce (RWO)  │ Read-write by a single node          │
│                      │ Most common for databases            │
├──────────────────────┼──────────────────────────────────────┤
│ ReadOnlyMany (ROX)   │ Read-only by many nodes              │
│                      │ Shared config, static assets         │
├──────────────────────┼──────────────────────────────────────┤
│ ReadWriteMany (RWX)  │ Read-write by many nodes             │
│                      │ Shared storage (NFS, CephFS)         │
└──────────────────────┴──────────────────────────────────────┘
```

### Reclaim Policies

```
┌──────────────────────┬──────────────────────────────────────┐
│ Policy               │ What Happens When PVC is Deleted     │
├──────────────────────┼──────────────────────────────────────┤
│ Retain               │ PV and data are kept                 │
│                      │ Admin must manually clean up         │
├──────────────────────┼──────────────────────────────────────┤
│ Delete               │ PV and underlying storage deleted    │
│                      │ Used with dynamic provisioning       │
├──────────────────────┼──────────────────────────────────────┤
│ Recycle (deprecated) │ Basic scrub (rm -rf /volume/*)       │
│                      │ Use Delete instead                   │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 24.3 Persistent Volume Claims (PVC)

A PVC is a request for storage by a user/pod. Kubernetes binds a PVC to a matching PV.

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: manual
```

```bash
$ kubectl apply -f pvc.yaml

$ kubectl get pvc
# NAME     STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-pvc   Bound    my-pv    10Gi       RWO            manual

$ kubectl get pv
# NAME    CAPACITY   ACCESS MODES   STATUS   CLAIM            STORAGECLASS
# my-pv   10Gi       RWO            Bound    default/my-pvc   manual
```

### Using PVC in a Pod

```yaml
# pod-with-pvc.yaml
apiVersion: v1
kind: Pod
metadata:
  name: db
spec:
  containers:
    - name: postgres
      image: postgres:16
      env:
        - name: POSTGRES_PASSWORD
          value: "mysecret"
      volumeMounts:
        - name: db-storage
          mountPath: /var/lib/postgresql/data
  volumes:
    - name: db-storage
      persistentVolumeClaim:
        claimName: my-pvc
```

```bash
$ kubectl apply -f pod-with-pvc.yaml

# Data in /var/lib/postgresql/data persists across pod restarts
# If the pod is deleted and recreated, data is still there
```

```
┌─────────────────────────────────────────────────────────────┐
│              PV / PVC BINDING FLOW                           │
│                                                              │
│  1. Admin creates PV (10Gi, RWO, manual)                   │
│  2. Developer creates PVC (5Gi, RWO, manual)               │
│  3. K8s finds a matching PV and binds them                 │
│  4. Pod references PVC in its volume spec                  │
│  5. K8s mounts the PV into the pod's container             │
│                                                              │
│  Matching criteria:                                         │
│    • Access mode must match                                │
│    • Storage class must match                              │
│    • PV capacity >= PVC request                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 24.4 StorageClass — Dynamic Provisioning

Instead of pre-creating PVs, StorageClass automatically provisions storage when a PVC is created.

```yaml
# storageclass.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs    # Cloud-specific
parameters:
  type: gp3
  fsType: ext4
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

```yaml
# pvc-dynamic.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd    # References the StorageClass
```

```bash
$ kubectl apply -f storageclass.yaml
$ kubectl apply -f pvc-dynamic.yaml

$ kubectl get pvc
# NAME         STATUS   VOLUME                                     CAPACITY   STORAGECLASS
# db-storage   Bound    pvc-abc123-def456-ghi789                   20Gi       fast-ssd

# K8s automatically created a 20Gi EBS volume!
# No admin intervention needed
```

```
┌─────────────────────────────────────────────────────────────┐
│              STATIC vs DYNAMIC PROVISIONING                  │
│                                                              │
│  Static (Manual):                                           │
│    Admin creates PV → Developer creates PVC → K8s binds    │
│    Good for: on-prem, specific storage requirements         │
│                                                              │
│  Dynamic (StorageClass):                                    │
│    Admin creates StorageClass → Developer creates PVC       │
│    → K8s auto-creates PV and binds                         │
│    Good for: cloud, self-service, automation                │
└─────────────────────────────────────────────────────────────┘
```

### Common StorageClass Provisioners

```
┌──────────────────────────────┬──────────────────────────────┐
│ Provisioner                  │ Storage Type                 │
├──────────────────────────────┼──────────────────────────────┤
│ kubernetes.io/aws-ebs        │ AWS EBS volumes              │
│ kubernetes.io/gce-pd         │ Google Persistent Disk       │
│ kubernetes.io/azure-disk     │ Azure Managed Disk           │
│ kubernetes.io/azure-file     │ Azure File Share             │
│ kubernetes.io/no-provisioner │ Manual (no auto-provisioning)│
│ rancher.io/local-path        │ Local path (Rancher/K3s)     │
│ csi drivers                  │ Various (Ceph, NFS, etc.)    │
└──────────────────────────────┴──────────────────────────────┘
```

---

## 24.5 Kubernetes Networking Model

Every pod gets its own IP address. Pods can communicate with each other directly without NAT.

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES NETWORKING RULES                     │
│                                                              │
│  1. Every pod gets a unique IP address                      │
│  2. Pods on the same node can communicate directly          │
│  3. Pods on different nodes can communicate without NAT     │
│  4. Agents on a node can communicate with all pods on it   │
│                                                              │
│  Implementation: CNI plugins                                │
│    Calico    → Network policies, BGP routing                │
│    Flannel   → Simple overlay (VXLAN)                       │
│    Weave     → Mesh networking                              │
│    Cilium    → eBPF-based, advanced policies                │
│                                                              │
│  Docker comparison:                                         │
│    Docker bridge = single-host pod networking               │
│    Docker overlay = multi-host pod networking               │
│    K8s CNI = standardized interface for any network plugin  │
└─────────────────────────────────────────────────────────────┘
```

---

## 24.6 Ingress — HTTP/HTTPS Routing

An Ingress exposes HTTP/HTTPS routes from outside the cluster to Services inside the cluster. It provides URL-based routing, SSL termination, and virtual hosting.

```
┌─────────────────────────────────────────────────────────────┐
│              INGRESS FLOW                                    │
│                                                              │
│  Internet                                                   │
│       │                                                      │
│       ▼                                                      │
│  Ingress Controller (nginx, traefik, etc.)                  │
│       │                                                      │
│       ├── /api  → api-service:8080                          │
│       ├── /web  → web-service:80                            │
│       └── /docs → docs-service:3000                         │
│                                                              │
│  Swarm comparison:                                          │
│    Swarm has no built-in Ingress equivalent                 │
│    You'd use a reverse proxy (nginx/traefik) manually      │
│    K8s Ingress standardizes this pattern                    │
└─────────────────────────────────────────────────────────────┘
```

### Ingress Resource

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
  tls:
    - hosts:
        - myapp.example.com
      secretName: tls-secret
```

```bash
$ kubectl apply -f ingress.yaml

$ kubectl get ingress
# NAME          CLASS   HOSTS               ADDRESS        PORTS     AGE
# app-ingress   nginx   myapp.example.com   34.56.78.90    80, 443   30s

# Requires an Ingress Controller to be installed:
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/cloud/deploy.yaml
```

---

## 24.7 Network Policies — Firewall Rules for Pods

Network Policies control traffic flow between pods. By default, all pods can communicate with all other pods. Network Policies restrict this.

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: database        # Apply to pods with label app=database
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: api      # Only allow traffic from pods with app=api
      ports:
        - protocol: TCP
          port: 5432        # Only on PostgreSQL port
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: api
      ports:
        - protocol: TCP
          port: 5432
```

```bash
$ kubectl apply -f network-policy.yaml

# Now:
#   ✅ api pods can reach database pods on port 5432
#   ❌ web pods CANNOT reach database pods
#   ❌ No other traffic to/from database pods
```

```
┌─────────────────────────────────────────────────────────────┐
│              NETWORK POLICY RULES                            │
│                                                              │
│  Without NetworkPolicy:                                     │
│    All pods can talk to all pods (open by default)          │
│                                                              │
│  With NetworkPolicy:                                        │
│    Only explicitly allowed traffic is permitted             │
│    Similar to firewall rules                                │
│                                                              │
│  Docker comparison:                                         │
│    Docker uses separate networks for isolation              │
│    K8s uses NetworkPolicies on a flat network               │
│                                                              │
│  ⚠️  Requires a CNI plugin that supports NetworkPolicies   │
│    ✅ Calico, Cilium, Weave                                │
│    ❌ Flannel (does not enforce NetworkPolicies)            │
└─────────────────────────────────────────────────────────────┘
```

### Default Deny All Traffic

```yaml
# deny-all.yaml — Block all ingress traffic to pods in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}          # Apply to ALL pods
  policyTypes:
    - Ingress
  ingress: []              # No ingress rules = deny all
```

---

## 24.8 Horizontal Pod Autoscaler (HPA)

HPA automatically scales the number of pod replicas based on CPU/memory usage or custom metrics.

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70    # Scale up when CPU > 70%
```

```bash
# Or create imperatively
$ kubectl autoscale deployment web --min=2 --max=10 --cpu-percent=70

$ kubectl get hpa
# NAME      REFERENCE        TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# web-hpa   Deployment/web   45%/70%   2         10        3          5m

# Current CPU is 45%, target is 70% → no scaling needed
# If CPU rises above 70% → HPA adds more pods
# If CPU drops → HPA removes pods (down to minReplicas)
```

```
┌─────────────────────────────────────────────────────────────┐
│              HPA BEHAVIOR                                    │
│                                                              │
│  CPU at 45% (target 70%):                                   │
│    Replicas: 3 (no change)                                  │
│                                                              │
│  CPU spikes to 90%:                                         │
│    HPA calculates: ceil(3 * 90/70) = 4                     │
│    Scales to 4 replicas                                     │
│                                                              │
│  CPU drops to 20%:                                          │
│    HPA calculates: ceil(4 * 20/70) = 2                     │
│    Scales down to 2 (minReplicas)                           │
│                                                              │
│  ⚠️  Requires metrics-server installed in the cluster       │
│  $ kubectl apply -f https://github.com/kubernetes-sigs/     │
│    metrics-server/releases/latest/download/components.yaml  │
│                                                              │
│  Docker Swarm comparison:                                   │
│    Swarm has NO auto-scaling                                │
│    You must manually: docker service scale web=10           │
│    HPA is a major K8s advantage over Swarm                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 24.9 Liveness and Readiness Probes

Probes tell Kubernetes how to check if a container is healthy and ready to serve traffic.

### Liveness Probe — Is the Container Alive?

If the liveness probe fails, Kubernetes **restarts** the container.

```yaml
# deployment-with-probes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: app
          image: myapp:1.0
          ports:
            - containerPort: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 30    # Wait 30s before first check
            periodSeconds: 10          # Check every 10s
            failureThreshold: 3        # Restart after 3 failures
            timeoutSeconds: 5          # Timeout per check
```

### Readiness Probe — Is the Container Ready for Traffic?

If the readiness probe fails, Kubernetes **removes the pod from Service endpoints** (stops sending traffic) but does NOT restart it.

```yaml
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
```

### Startup Probe — For Slow-Starting Containers

Disables liveness/readiness checks until the startup probe succeeds. Prevents premature restarts for slow-starting apps.

```yaml
          startupProbe:
            httpGet:
              path: /healthz
              port: 8080
            failureThreshold: 30       # 30 * 10s = 300s max startup
            periodSeconds: 10
```

### Probe Types

```
┌──────────────────────┬──────────────────────────────────────┐
│ Probe Type           │ How It Works                         │
├──────────────────────┼──────────────────────────────────────┤
│ httpGet              │ HTTP GET to a path/port              │
│                      │ Success: 200-399 status code         │
├──────────────────────┼──────────────────────────────────────┤
│ tcpSocket            │ TCP connection to a port             │
│                      │ Success: connection established      │
├──────────────────────┼──────────────────────────────────────┤
│ exec                 │ Run a command inside container       │
│                      │ Success: exit code 0                 │
└──────────────────────┴──────────────────────────────────────┘
```

### Probe Comparison

```
┌──────────────────┬──────────────────────────────────────────┐
│ Probe            │ On Failure                               │
├──────────────────┼──────────────────────────────────────────┤
│ Liveness         │ Container is RESTARTED                   │
│                  │ "Is the process alive?"                  │
├──────────────────┼──────────────────────────────────────────┤
│ Readiness        │ Pod removed from Service endpoints       │
│                  │ "Is the app ready for traffic?"          │
│                  │ Container is NOT restarted               │
├──────────────────┼──────────────────────────────────────────┤
│ Startup          │ Liveness/readiness checks delayed        │
│                  │ "Has the app finished starting?"         │
│                  │ Container restarted if startup fails     │
└──────────────────┴──────────────────────────────────────────┘

Docker Swarm comparison:
  Swarm has HEALTHCHECK (similar to liveness probe)
  Swarm has NO readiness probe equivalent
  Swarm has start_period (similar to startup probe)
```

---

## 24.10 Kubernetes Secrets and ConfigMaps

### ConfigMap (Non-Sensitive Configuration)

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "db.example.com"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "info"
  app.conf: |
    server.port=8080
    server.host=0.0.0.0
```

### Kubernetes Secret (Sensitive Data)

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: YWRtaW4=          # base64 encoded "admin"
  password: UEBzc3cwcmQ=      # base64 encoded "P@ssw0rd"
```

```bash
# Create secret from command line
$ kubectl create secret generic db-credentials \
    --from-literal=username=admin \
    --from-literal=password='P@ssw0rd'

# Base64 encode/decode
$ echo -n "admin" | base64
# YWRtaW4=

$ echo "YWRtaW4=" | base64 -d
# admin
```

### Using in a Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0
      env:
        # From ConfigMap
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_HOST
        # From Secret
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
      volumeMounts:
        # Mount ConfigMap as file
        - name: config-volume
          mountPath: /etc/app/
        # Mount Secret as file
        - name: secret-volume
          mountPath: /etc/secrets/
          readOnly: true
  volumes:
    - name: config-volume
      configMap:
        name: app-config
    - name: secret-volume
      secret:
        secretName: db-credentials
```

```
┌──────────────────────┬──────────────────────────────────────┐
│ Docker Swarm         │ Kubernetes                           │
├──────────────────────┼──────────────────────────────────────┤
│ docker config        │ ConfigMap                            │
│ docker secret        │ Secret                               │
│ /run/secrets/<name>  │ Mounted as env var or file           │
│ Encrypted at rest    │ Base64 encoded (not encrypted        │
│                      │ by default — use encryption at rest) │
│ tmpfs mount          │ tmpfs mount for Secrets              │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 24.11 Common Errors and Troubleshooting

### Error 1: PVC Stuck in "Pending"

```bash
$ kubectl get pvc
# NAME     STATUS    VOLUME   CAPACITY   STORAGECLASS
# my-pvc   Pending                       fast-ssd

$ kubectl describe pvc my-pvc
# Events:
#   Warning  ProvisioningFailed  no persistent volumes available

# CAUSES:
#   No matching PV exists (static provisioning)
#   StorageClass provisioner not installed
#   Insufficient storage quota

# Fix: Create a matching PV or check StorageClass
$ kubectl get storageclass
$ kubectl get pv
```

### Error 2: NetworkPolicy Not Working

```bash
# CAUSE: CNI plugin doesn't support NetworkPolicies
# Check your CNI plugin
$ kubectl get pods -n kube-system | grep -E "calico|cilium|weave|flannel"

# Flannel does NOT enforce NetworkPolicies
# Switch to Calico or Cilium for policy enforcement
```

### Error 3: HPA Not Scaling

```bash
$ kubectl get hpa
# NAME      TARGETS         MINPODS   MAXPODS   REPLICAS
# web-hpa   <unknown>/70%   2         10        2

# <unknown> means metrics-server is not installed or not working
# Fix: Install metrics-server
$ kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
$ kubectl top pods
$ kubectl top nodes
```

---

## Module 24 Summary

- **PersistentVolume (PV)**: cluster-level storage resource provisioned by admin
- **PersistentVolumeClaim (PVC)**: request for storage by a pod — K8s binds PVC to matching PV
- **StorageClass**: enables dynamic provisioning — PVs created automatically when PVC is submitted
- Access modes: RWO (single node), ROX (read-only many), RWX (read-write many)
- Reclaim policies: Retain (keep data), Delete (remove storage), Recycle (deprecated)
- **Ingress**: HTTP/HTTPS routing from outside the cluster to internal Services
- Ingress provides URL-based routing, SSL termination, and virtual hosting
- Requires an Ingress Controller (nginx-ingress, traefik, etc.)
- **NetworkPolicies**: firewall rules for pod-to-pod traffic — default is allow-all
- NetworkPolicies require a supporting CNI plugin (Calico, Cilium — not Flannel)
- **HPA**: automatically scales pod replicas based on CPU/memory metrics
- HPA requires metrics-server; Swarm has no auto-scaling equivalent
- **Liveness probe**: restarts container if it fails — "is the process alive?"
- **Readiness probe**: removes pod from Service endpoints if it fails — "is the app ready?"
- **Startup probe**: delays liveness/readiness checks for slow-starting apps
- **ConfigMap**: non-sensitive configuration data (like Docker config)
- **Secret**: sensitive data, base64 encoded (like Docker secret, but less secure by default)
- K8s Secrets are base64 encoded, not encrypted — enable encryption at rest for production

---

**Previous Module: [Module 23 - Kubernetes Fundamentals](module-23-kubernetes-fundamentals.md)**
