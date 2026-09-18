# MODULE 5: Kubernetes Objects & YAML Manifests

---

## 5.1 Kubernetes Objects — The Building Blocks

### Core Objects Overview

```
┌─────────────────────────────────────────────────────┐
│                  KUBERNETES OBJECTS                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  WORKLOADS          NETWORKING        STORAGE        │
│  ─────────          ──────────        ───────        │
│  • Pod              • Service         • PV           │
│  • ReplicaSet       • Ingress         • PVC          │
│  • Deployment       • NetworkPolicy   • StorageClass │
│  • StatefulSet      • Endpoints                      │
│  • DaemonSet                                         │
│  • Job / CronJob    CONFIG                           │
│                     ──────                            │
│  CLUSTER            • ConfigMap                      │
│  ───────            • Secret                         │
│  • Namespace        • ServiceAccount                 │
│  • Node             • RBAC (Role,                    │
│  • PersistentVolume   ClusterRole)                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Object Specification Pattern

Every Kubernetes object follows this YAML structure:

```yaml
apiVersion: v1              # API version for this object type
kind: Pod                   # Type of object
metadata:                   # Data that identifies the object
  name: my-app
  namespace: default
  labels:
    app: my-app
    environment: production
  annotations:
    description: "My application pod"
spec:                       # Desired state of the object
  containers:
  - name: my-app
    image: nginx:1.25
    ports:
    - containerPort: 80
```

**Key fields explained:**

| Field | Purpose | Example |
|---|---|---|
| `apiVersion` | Which API group/version to use | `v1`, `apps/v1`, `networking.k8s.io/v1` |
| `kind` | Type of resource | `Pod`, `Deployment`, `Service` |
| `metadata.name` | Unique name within namespace | `my-nginx-app` |
| `metadata.labels` | Key-value pairs for organizing/selecting | `app: nginx` |
| `metadata.annotations` | Non-identifying metadata | `description: "web server"` |
| `spec` | Desired state specification | Varies by resource type |

### Kubernetes Objects — Detailed Reference

Kubernetes objects are persistent entities in the Kubernetes system that represent the desired state of the cluster. These objects define what applications are running, their configurations, networking, storage, and policies.

#### 1. Workload Resources (Manage Applications)

These objects define how applications run inside the cluster.

**a. Pod** — Smallest and most basic deployable unit. Represents one or more containers running together.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
    - name: nginx-container
      image: nginx
```

**b. Deployment** — Manages replicas of Pods. Ensures the desired number of Pods are running. Allows rolling updates and rollback.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
```

**c. StatefulSet** — Used for stateful applications like databases (MySQL, MongoDB). Provides stable identities (persistent storage) for each Pod.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql-db
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mysql
  serviceName: "mysql"
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql
```

**d. DaemonSet** — Ensures one Pod per node (e.g., for logging or monitoring agents like Fluentd, Prometheus).

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-daemonset
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
        - name: fluentd
          image: fluentd
```

**e. Job** — Runs one-time tasks like batch processing.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pi-job
spec:
  template:
    spec:
      containers:
        - name: pi
          image: perl
          command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
      restartPolicy: Never
```

**f. CronJob** — Runs jobs at scheduled times. Example runs every 5 minutes:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: hello-cron
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: hello
              image: busybox
              args:
                - /bin/sh
                - -c
                - echo "Hello Kubernetes!"
          restartPolicy: OnFailure
```

#### 2. Service Resources (Networking & Communication)

These objects manage how applications communicate.

**a. Service** — Exposes a group of Pods as a network service.

Types:
- **ClusterIP** (default) — Internal access only
- **NodePort** — Exposes service on a static port on each node
- **LoadBalancer** — Uses a cloud provider's load balancer
- **ExternalName** — Maps a service to an external DNS name

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

**b. Ingress** — Manages external access to services (e.g., using an NGINX Ingress Controller).

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
    - host: example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

#### 3. Storage Resources

These objects handle persistent storage.

**a. PersistentVolume (PV)** — Represents physical storage (NFS, AWS EBS, etc.).

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-pv
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: "/mnt/data"
```

**b. PersistentVolumeClaim (PVC)** — Requests storage from a PersistentVolume.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

#### 4. Config & Security Resources

These objects manage configurations and security.

**a. ConfigMap** — Stores non-sensitive configuration data as key-value pairs.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  app_name: "My App"
  log_level: "INFO"
```

**b. Secret** — Stores sensitive data (passwords, tokens, etc.).

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
data:
  password: bXlwYXNzd29yZA==  # base64 encoded "mypassword"
```

**c. ServiceAccount** — Provides authentication for applications inside the cluster.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
```

#### 5. Policy & Security Resources

These objects manage access control and resource limits.

**a. NetworkPolicy** — Controls pod communication. Example allows only frontend pods to reach my-app:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-specific
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: frontend
```

**b. ResourceQuota** — Limits resource consumption per namespace.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: my-quota
spec:
  hard:
    cpu: "2"
    memory: "4Gi"
    pods: "10"
```

#### Kubernetes Objects Summary Table

| Category | Objects |
|---|---|
| Workloads | Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob |
| Networking | Service, Ingress |
| Storage | PersistentVolume (PV), PersistentVolumeClaim (PVC) |
| Config & Security | ConfigMap, Secret, ServiceAccount |
| Policies | NetworkPolicy, ResourceQuota |

---

