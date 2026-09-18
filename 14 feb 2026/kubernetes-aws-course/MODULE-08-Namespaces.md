# MODULE 8: Namespaces

---

## 8.1 Namespaces

Namespaces provide logical isolation within a cluster — like folders on your computer.

**Why namespaces matter:**
- **Resource isolation** — teams can work in separate namespaces without interfering
- **Access control** — RBAC roles can be scoped to a namespace
- **Resource quotas** — limit CPU/memory/pod count per namespace
- **Environment separation** — dev, staging, production in the same cluster

**What is NOT namespaced:** Nodes, PersistentVolumes, ClusterRoles, and Namespaces themselves are cluster-scoped resources.

```bash
# List all namespaces
kubectl get namespaces

# Output:
# NAME              STATUS   AGE
# default           Active   5d    ← Your resources go here by default
# kube-system       Active   5d    ← Kubernetes system components
# kube-public       Active   5d    ← Publicly accessible data
# kube-node-lease   Active   5d    ← Node heartbeat data

# Create a namespace
kubectl create namespace development

# Output:
# namespace/development created

# Or via YAML:
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    environment: staging
EOF

# Run a pod in a specific namespace
kubectl run nginx --image=nginx -n development

# Set default namespace for kubectl
kubectl config set-context --current --namespace=development

# Output:
# Context "arn:aws:eks:us-east-1:123456789:cluster/my-cluster" modified.

# Verify current namespace
kubectl config view --minify | grep namespace

# Output:
# namespace: development

# Apply a manifest to a specific namespace
kubectl apply -f pod1.yml -n development

# Delete a resource from a specific namespace
kubectl delete -f pod1.yml -n development

# View pods in a specific namespace
kubectl get pods -n development

# Alternative: check current namespace context
kubectl config view | grep namespace:
```

### Industry Example: Namespace Strategy at a Fintech Company

```yaml
# Typical namespace layout for a financial services company
Namespaces:
  - production          # Live customer-facing services
  - staging             # Pre-production testing
  - development         # Developer testing
  - monitoring          # Prometheus, Grafana, alerting
  - logging             # ELK stack / Fluentd
  - istio-system        # Service mesh components
  - cert-manager        # TLS certificate management
  - payment-processing  # Isolated PCI-DSS compliant workloads
```

### Namespaces — Imperative using kubectl

Namespaces are also called **virtual clusters** within a physical Kubernetes cluster. Use them in environments with many users spread across multiple teams or projects. Clusters with only a few users typically don't need namespaces.

**Benefits:**
- Creates isolation boundary from other Kubernetes objects
- Allows resource limits (CPU, Memory) on a per-namespace basis via ResourceQuota
- Enables environment separation (dev, staging, production) in one cluster

**Step 1: Create Namespaces**

```bash
# List existing namespaces
kubectl get ns

# Create namespaces for two environments
kubectl create namespace dev1
kubectl create namespace dev2

# Verify
kubectl get ns
```

**Step 2: Deploy to Multiple Namespaces**

Deploy the same manifests into both namespaces using `-n`:

```bash
# Deploy all manifests into dev1 and dev2
kubectl apply -f kube-manifests/ -n dev1
kubectl apply -f kube-manifests/ -n dev2

# List all objects from each namespace
kubectl get all -n dev1
kubectl get all -n dev2
```

⚠️ **NodePort conflict:** When deploying the same manifests to multiple namespaces, comment out any hardcoded `nodePort` values. Two services cannot bind the same worker node port. Let Kubernetes assign dynamic NodePorts instead:

```yaml
# In your Service manifest, comment out the fixed nodePort:
spec:
  type: NodePort
  ports:
    - port: 8095
      targetPort: 8095
      #nodePort: 31231    # Comment this out for multi-namespace deployments
```

If not commented, you get:
```
The Service "usermgmt-restapp-service" is invalid: spec.ports[0].nodePort: Invalid value: 31231: provided port is already allocated
```

**Step 3: Verify SC, PVC, and PV Namespace Scoping**

PVC is namespace-scoped. PV and StorageClass are cluster-scoped (no namespace).

```bash
# PVC is created per namespace
kubectl get pvc -n dev1
kubectl get pvc -n dev2

# StorageClass and PV are cluster-wide — no namespace flag needed
kubectl get sc,pv
```

| Resource | Scope | Namespace Flag Needed? |
|---|---|---|
| PersistentVolumeClaim (PVC) | Namespace | Yes (`-n dev1`) |
| PersistentVolume (PV) | Cluster | No |
| StorageClass (SC) | Cluster | No |

**Step 4: Access Application per Namespace**

Each namespace gets its own dynamically assigned NodePort:

```bash
# Dev1
kubectl get nodes -o wide                    # Get worker node public IP
kubectl get svc -n dev1                      # Get NodePort for dev1
# Access: http://<Worker-Node-Public-IP>:<Dev1-NodePort>/usermgmt/health-status

# Dev2
kubectl get svc -n dev2                      # Get NodePort for dev2
# Access: http://<Worker-Node-Public-IP>:<Dev2-NodePort>/usermgmt/health-status
```

**Step 5: Clean-Up**

Deleting a namespace deletes all resources inside it:

```bash
# Delete both namespaces (removes all objects inside them)
kubectl delete ns dev1
kubectl delete ns dev2

# Verify everything is gone
kubectl get all -n dev1
kubectl get all -n dev2
kubectl get ns

# Clean up cluster-scoped resources separately
kubectl get sc,pv
kubectl delete sc ebs-sc

# View all resources across all namespaces
kubectl get all --all-namespaces
```

### Namespaces — Declarative using YAML with LimitRange

Instead of specifying CPU and memory in every container spec, use a **LimitRange** to set default resource requests/limits for all containers in a namespace.

⚠️ **File naming tip:** Name the namespace manifest with a `00-` prefix so it gets created first when running `kubectl apply -f kube-manifests/`.

**Step 1: Create Namespace manifest**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dev3
```

**Step 2: Create LimitRange manifest**

```yaml
# 00-namespace-LimitRange-default.yml
apiVersion: v1
kind: Namespace
metadata:
  name: dev3
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-cpu-mem-limit-range
  namespace: dev3
spec:
  limits:
    - default:
        memory: "512Mi"   # Default memory limit per container (if not specified)
        cpu: "500m"        # Default CPU limit per container (if not specified, defaults to 1 vCPU)
      defaultRequest:
        memory: "256Mi"    # Default memory request (falls back to limits.default.memory if omitted)
        cpu: "300m"        # Default CPU request (falls back to limits.default.cpu if omitted)
      type: Container
```

**Step 3: Update all manifests with namespace**

Add `namespace: dev3` to the metadata section of every manifest (PVC, ConfigMap, Deployments, Services, Secrets):

```yaml
# Example — add namespace to PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-mysql-pv-claim
  namespace: dev3          # ← Add this to every manifest
```

**Step 4: Deploy and verify LimitRange**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# Watch pods come up
kubectl get pods -n dev3 -w

# View pod spec to confirm default CPU/memory was injected
kubectl get pod <pod-name> -o yaml -n dev3

# Check LimitRange
kubectl get limits -n dev3
kubectl describe limits default-cpu-mem-limit-range -n dev3

# Access application
kubectl get svc -n dev3
kubectl get nodes -o wide
# http://<WorkerNode-Public-IP>:<NodePort>/usermgmt/health-status
```

**Step 5: Clean-Up**

```bash
kubectl delete -f kube-manifests/
```

### Namespaces — Declarative using YAML with ResourceQuota

Use LimitRange and ResourceQuota together: LimitRange sets per-container defaults, ResourceQuota caps the namespace total.

```yaml
# Combined: Namespace + LimitRange + ResourceQuota
apiVersion: v1
kind: Namespace
metadata:
  name: dev3
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-cpu-mem-limit-range
  namespace: dev3
spec:
  limits:
    - default:
        memory: "512Mi"
        cpu: "500m"
      defaultRequest:
        memory: "256Mi"
        cpu: "300m"
      type: Container
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ns-resource-quota
  namespace: dev3
spec:
  hard:
    requests.cpu: "1"                  # Total CPU requests across all pods
    requests.memory: 1Gi               # Total memory requests across all pods
    limits.cpu: "2"                    # Total CPU limits across all pods
    limits.memory: 2Gi                 # Total memory limits across all pods
    pods: "5"                          # Max 5 pods in this namespace
    configmaps: "5"                    # Max 5 ConfigMaps
    persistentvolumeclaims: "5"        # Max 5 PVCs
    secrets: "5"                       # Max 5 Secrets
    services: "5"                      # Max 5 Services
```

**Deploy and verify ResourceQuota:**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# Watch pods come up
kubectl get pods -n dev3 -w

# View pod spec to confirm CPU/memory
kubectl get pod <pod-name> -o yaml -n dev3

# Check LimitRange
kubectl get limits -n dev3
kubectl describe limits default-cpu-mem-limit-range -n dev3

# Check ResourceQuota — shows used vs hard limits
kubectl get quota -n dev3
kubectl describe quota ns-resource-quota -n dev3

# Example output from describe quota:
# Name:                   ns-resource-quota
# Namespace:              dev3
# Resource                Used    Hard
# --------                ----    ----
# configmaps              1       5
# limits.cpu              1500m   2
# limits.memory           1Gi     2Gi
# persistentvolumeclaims  1       5
# pods                    2       5
# requests.cpu            800m    1
# requests.memory         384Mi   1Gi
# secrets                 2       5
# services                2       5

# Access application
kubectl get svc -n dev3
kubectl get nodes -o wide
# http://<WorkerNode-Public-IP>:<NodePort>/usermgmt/health-status

# Clean up
kubectl delete -f kube-manifests/
```

**LimitRange vs ResourceQuota — when each kicks in:**

| Aspect | LimitRange | ResourceQuota |
|---|---|---|
| Scope | Per container/pod | Entire namespace total |
| Purpose | Set defaults, enforce min/max per pod | Cap total consumption |
| Example | "Each container max 500m CPU" | "All pods combined max 2 CPU" |
| What happens on violation | Pod rejected at creation | Pod rejected when quota exceeded |
| Best practice | Use together — LimitRange sets defaults, ResourceQuota caps the total |

### Real-World Namespace Example — Multi-File Application

A complete namespaced application with MySQL + user management microservice. Each file includes `namespace: dev3`:

**StorageClass** (cluster-scoped — no namespace):

```yaml
# 01-storage-class.yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
```

**PVC** (namespace-scoped):

```yaml
# 02-persistent-volume-claim.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-mysql-pv-claim
  namespace: dev3
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
```

**ConfigMap** (namespace-scoped):

```yaml
# 03-UserManagement-ConfigMap.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: usermanagement-dbcreation-script
  namespace: dev3
data:
  mysql_usermgmt.sql: |-
    DROP DATABASE IF EXISTS usermgmt;
    CREATE DATABASE usermgmt;
```

**MySQL Deployment** (namespace-scoped):

```yaml
# 04-mysql-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  namespace: dev3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  strategy:
    type: Recreate
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:5.6
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-db-password
                  key: db-password
          ports:
            - containerPort: 3306
              name: mysql
          volumeMounts:
            - name: mysql-persistent-storage
              mountPath: /var/lib/mysql
            - name: usermanagement-dbcreation-script
              mountPath: /docker-entrypoint-initdb.d
      volumes:
        - name: mysql-persistent-storage
          persistentVolumeClaim:
            claimName: ebs-mysql-pv-claim
        - name: usermanagement-dbcreation-script
          configMap:
            name: usermanagement-dbcreation-script
```

**MySQL Headless Service** (ClusterIP: None for stable DNS):

```yaml
# 05-mysql-clusterip-service.yml
apiVersion: v1
kind: Service
metadata:
  name: mysql
  namespace: dev3
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
  clusterIP: None    # Headless — pods connect directly via Pod IP
```

**User Management Microservice** (with init container, probes, and resource limits):

```yaml
# 06-UserManagementMicroservice-Deployment-Service.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: usermgmt-microservice
  labels:
    app: usermgmt-restapp
  namespace: dev3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: usermgmt-restapp
  template:
    metadata:
      labels:
        app: usermgmt-restapp
    spec:
      initContainers:
        - name: init-db
          image: busybox:1.31
          command: ['sh', '-c', 'echo -e "Checking for the availability of MySQL Server deployment"; while ! nc -z mysql 3306; do sleep 1; printf "-"; done; echo -e "  >> MySQL DB Server has started";']
      containers:
        - name: usermgmt-restapp
          image: stacksimplify/kube-usermanagement-microservice:1.0.0
          ports:
            - containerPort: 8095
          env:
            - name: DB_HOSTNAME
              value: "mysql"
            - name: DB_PORT
              value: "3306"
            - name: DB_NAME
              value: "usermgmt"
            - name: DB_USERNAME
              value: "root"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-db-password
                  key: db-password
          livenessProbe:
            exec:
              command:
                - /bin/sh
                - -c
                - nc -z localhost 8095
            initialDelaySeconds: 60
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /usermgmt/health-status
              port: 8095
            initialDelaySeconds: 60
            periodSeconds: 10
          resources:
            requests:
              cpu: "500m"
              memory: "128Mi"
            limits:
              cpu: "1000m"
              memory: "500Mi"
```

**NodePort Service** (exposes the microservice externally):

```yaml
# 07-UserManagement-Service.yml
apiVersion: v1
kind: Service
metadata:
  name: usermgmt-restapp-service
  labels:
    app: usermgmt-restapp
  namespace: dev3
spec:
  type: NodePort
  selector:
    app: usermgmt-restapp
  ports:
    - port: 8095
      targetPort: 8095
      nodePort: 31231
```

**Secret** (stores the database password):

```yaml
# 08-Kubernetes-Secrets.yml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-db-password
  namespace: dev3
type: Opaque
data:
  db-password: ZGJwYXNzd29yZDEx    # base64 encoded "dbpassword11"
```

---

