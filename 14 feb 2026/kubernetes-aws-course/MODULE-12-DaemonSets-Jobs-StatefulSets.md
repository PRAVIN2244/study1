# MODULE 12: DaemonSets, StatefulSets, Jobs & CronJobs

---

## 12.1 Other Workload Types

### Workload Type Comparison

| Feature | Deployment | DaemonSet | StatefulSet |
|---|---|---|---|
| **Type** | Stateless apps | One replica per worker node | Stateful apps |
| **Example** | Frontend, API servers | Monitoring, logging, networking agents | Databases |
| **Replicas** | You specify replica count | Automatic (1 per node, no replica count needed) | You specify replica count |
| **Pod creation** | All pods created together | One per node, automatic | Created in order (0, 1, 2...) |
| **Scaling** | Manual or HPA | Cannot manually scale (tied to node count) | Manual or ordered scaling |
| **Service type** | LoadBalancer / ClusterIP | N/A (node-local) | Headless Service |
| **Volume** | 1 PV shared by all replicas | Per-node access | 1 PV per replica |

### DaemonSet — One Pod Per Node

Runs exactly one pod on every node. Used for monitoring agents, log collectors, network plugins.

**Key characteristics:**
- You do NOT specify a replica count — Kubernetes automatically runs one pod per node
- When a new node joins the cluster, a DaemonSet pod is automatically created on it
- When a node is removed, the DaemonSet pod is garbage collected
- You cannot manually scale a DaemonSet — it's tied to node count
- DaemonSets can use tolerations to run on tainted nodes (e.g., control plane nodes)

**Common use cases in production:** Datadog agent, Prometheus node-exporter, Fluentd/Fluent Bit log collector, Calico/Cilium network plugin, AWS VPC CNI plugin.

**How DaemonSets schedule pods:**

| Kubernetes Version | Scheduling Mechanism |
|---|---|
| Before v1.12 | DaemonSet controller set `nodeName` directly on each pod, bypassing the scheduler |
| v1.12+ (current) | DaemonSet uses the default scheduler with **node affinity** rules to place one pod per node |

The modern approach (v1.12+) is better because it integrates with the scheduler's taints, tolerations, and priority logic — ensuring DaemonSet pods follow the same scheduling rules as all other pods.

**DaemonSet YAML is nearly identical to ReplicaSet** — the only differences are `kind: DaemonSet` and no `replicas` field:

```yaml
# daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd-logging
  namespace: kube-system
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      containers:
      - name: fluentd
        image: fluent/fluentd:v1.16
        resources:
          limits:
            memory: "200Mi"
          requests:
            cpu: "100m"
            memory: "200Mi"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

```bash
kubectl apply -f daemonset.yaml
kubectl get daemonset -n kube-system fluentd-logging

# Output:
# NAME              DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   AGE
# fluentd-logging   3         3         3       3            3           30s
# (One pod per node — 3 nodes = 3 pods)

# List ALL DaemonSets across ALL namespaces
kubectl get ds -A

# Output:
# NAMESPACE     NAME                      DESIRED   CURRENT   READY   AGE
# kube-system   aws-node                  3         3         3       30d    ← VPC-CNI
# kube-system   kube-proxy                3         3         3       30d    ← kube-proxy
# kube-system   ebs-csi-node              3         3         3       5d     ← EBS CSI
# kube-system   fluentd-logging           3         3         3       30s    ← Our DaemonSet
# monitoring    node-exporter             3         3         3       10d    ← Prometheus

# Describe a DaemonSet for detailed info
kubectl describe ds fluentd-logging -n kube-system

# Output (key sections):
# Name:           fluentd-logging
# Selector:       app=fluentd
# Node-Selector:  <none>
# Labels:         app=fluentd
# Desired Number of Nodes Scheduled: 3
# Current Number of Nodes Scheduled: 3
# Number of Nodes Misscheduled: 0
# Pods Status:  3 Running / 0 Waiting / 0 Succeeded / 0 Failed
```

**DaemonSets are essential for cluster-level agents** — they run even when application workloads scale down to zero. Log collectors, monitoring agents, and CNI plugins must be present on every node regardless of application state.

**Industry example:** Datadog, New Relic, and Prometheus node-exporter all run as DaemonSets.

**DaemonSet Update Strategies:**

```yaml
# DaemonSet supports two update strategies:
spec:
  updateStrategy:
    type: RollingUpdate          # Default — updates pods one node at a time
    rollingUpdate:
      maxUnavailable: 1          # How many nodes can have unavailable pods during update
      maxSurge: 0                # (K8s 1.22+) How many extra pods can be created
```

| Strategy | Behavior | Use Case |
|---|---|---|
| `RollingUpdate` (default) | Updates pods one node at a time | Most DaemonSets |
| `OnDelete` | Only updates when you manually delete old pods | When you need manual control |

```bash
# Update a DaemonSet image
kubectl set image daemonset/fluentd-logging fluentd=fluent/fluentd:v1.17 -n kube-system

# Watch the rolling update
kubectl rollout status daemonset/fluentd-logging -n kube-system

# Output:
# Waiting for daemon set "fluentd-logging" rollout to finish: 1 out of 3 new pods have been updated...
# Waiting for daemon set "fluentd-logging" rollout to finish: 2 out of 3 new pods have been updated...
# daemon set "fluentd-logging" successfully rolled out

# Rollback
kubectl rollout undo daemonset/fluentd-logging -n kube-system
```

**Interview question: How does a DaemonSet differ from a Deployment with nodeAffinity?**
A DaemonSet guarantees exactly one pod per node and automatically adds/removes pods as nodes join/leave. A Deployment with nodeAffinity can schedule pods on specific nodes but doesn't guarantee one-per-node and doesn't react to node changes. DaemonSets also bypass the scheduler by default (they use the DaemonSet controller).

**Quick trick: Create a DaemonSet from a Deployment dry-run**

There's no `kubectl create daemonset` command. Generate a Deployment YAML and convert it:

```bash
# Generate a Deployment manifest without creating it
kubectl create deployment elasticsearch --image=k8s.gcr.io/fluentd-elasticsearch:1.20 \
  -n kube-system --dry-run=client -o yaml > fluentd-ds.yaml
```

Edit `fluentd-ds.yaml`:
1. Change `kind: Deployment` → `kind: DaemonSet`
2. Remove the `replicas` field
3. Remove the `strategy` field (DaemonSets use `updateStrategy` instead)

```yaml
# fluentd-ds.yaml (after editing)
apiVersion: apps/v1
kind: DaemonSet                    # Changed from Deployment
metadata:
  name: elasticsearch
  namespace: kube-system
  labels:
    app: elasticsearch
spec:
  # replicas: removed (DaemonSet doesn't use replicas)
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: fluentd-elasticsearch
        image: k8s.gcr.io/fluentd-elasticsearch:1.20
```

```bash
kubectl apply -f fluentd-ds.yaml

kubectl get ds -n kube-system
```

```
NAME                   DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   AGE
elasticsearch          3         3         3       3            3           10s
kube-flannel-ds        3         3         3       3            3           30d
kube-proxy             3         3         3       3            3           30d
```

### StatefulSet — For Stateful Applications

Provides stable network identities and persistent storage. Used for databases, message queues.

```yaml
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
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
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3
      resources:
        requests:
          storage: 20Gi
```

```bash
kubectl apply -f statefulset.yaml
kubectl get statefulset postgres

# Output:
# NAME       READY   AGE
# postgres   3/3     2m

kubectl get pods

# Output (predictable, ordered names):
# NAME         READY   STATUS    RESTARTS   AGE
# postgres-0   1/1     Running   0          2m    ← Created first
# postgres-1   1/1     Running   0          90s   ← Created second
# postgres-2   1/1     Running   0          60s   ← Created third

# Each pod gets a stable DNS name:
# postgres-0.postgres.default.svc.cluster.local
# postgres-1.postgres.default.svc.cluster.local
# postgres-2.postgres.default.svc.cluster.local
```

**Key differences from Deployment:**

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix (webapp-abc12) | Ordered (postgres-0, postgres-1) |
| Scaling | Parallel | Sequential (ordered) |
| Storage | Shared or none | Each pod gets its own PVC |
| DNS | Via Service only | Individual pod DNS names |
| Use case | Stateless apps | Databases, queues |

**Cross-pod communication in StatefulSets** uses the pattern `<podname>.<headless-servicename>`:

```bash
# Access a specific pod from another pod
kubectl exec webapp-1 -- curl webapp-0.nginx
kubectl exec webapp-0 -- curl webapp-1.nginx

# Write unique content to each pod
kubectl exec webapp-0 -- sh -c 'echo MASTER-POD-0 > /usr/share/nginx/html/index.html'
kubectl exec webapp-1 -- sh -c 'echo SECONDARY-POD-1 > /usr/share/nginx/html/index.html'

# List StatefulSets
kubectl get sts

# Clean up PVCs associated with a StatefulSet
kubectl delete pvc -l app=nginx
```

### StatefulSet Considerations — What to Think About

When deploying StatefulSets, several factors require careful planning:

**1. Headless Service is mandatory:**

```yaml
# StatefulSets REQUIRE a headless service for pod DNS
apiVersion: v1
kind: Service
metadata:
  name: postgres          # Must match spec.serviceName in StatefulSet
spec:
  clusterIP: None          # Headless — no ClusterIP, returns individual pod IPs
  selector:
    app: postgres
  ports:
  - port: 5432
```

Without a headless service, pods don't get stable DNS names (`postgres-0.postgres.svc.cluster.local`).

**2. Ordered deployment and scaling:**

```bash
# Pods are created in order: 0 → 1 → 2
# Pod N+1 is NOT created until Pod N is Running and Ready
# This matters for databases with primary/replica setup:
#   postgres-0 (primary) must be ready before postgres-1 (replica) starts

# Scaling down is reverse order: 2 → 1 → 0
kubectl scale statefulset postgres --replicas=1
# postgres-2 terminated first, then postgres-1
# postgres-0 (primary) is always the last to be removed
```

**`podManagementPolicy` — override ordered startup:**

By default, StatefulSets use `OrderedReady` — pods are created sequentially. Set `podManagementPolicy: Parallel` to launch all pods simultaneously while still retaining stable identities and per-pod storage:

```yaml
spec:
  podManagementPolicy: Parallel    # Default: OrderedReady
  replicas: 3
  serviceName: postgres
```

Use `Parallel` when pods don't depend on each other's startup order (e.g., a cache cluster where all nodes are equal). Keep `OrderedReady` for primary/replica databases where the primary must start first.

**3. Persistent storage survives pod deletion:**

```bash
# Each pod gets its own PVC via volumeClaimTemplates
kubectl get pvc

# Output:
# NAME                    STATUS   VOLUME         CAPACITY   STORAGECLASS
# postgres-data-postgres-0   Bound    pvc-abc123   20Gi       gp3
# postgres-data-postgres-1   Bound    pvc-def456   20Gi       gp3
# postgres-data-postgres-2   Bound    pvc-ghi789   20Gi       gp3

# Delete the StatefulSet — PVCs are NOT deleted (data preserved)
kubectl delete statefulset postgres

kubectl get pvc
# PVCs still exist! Data is safe.

# Re-create the StatefulSet — pods reattach to their original PVCs
kubectl apply -f statefulset.yaml
# postgres-0 gets postgres-data-postgres-0 (same data as before)

# To delete PVCs (and lose data), you must do it explicitly:
kubectl delete pvc -l app=postgres
```

**4. Update strategies:**

```yaml
spec:
  updateStrategy:
    type: RollingUpdate          # Default
    rollingUpdate:
      partition: 2               # Only update pods with ordinal >= 2
                                 # Useful for canary updates on databases
```

| Strategy | Behavior | Use Case |
|---|---|---|
| `RollingUpdate` | Updates pods in reverse order (N → N-1 → ... → 0) | Most StatefulSets |
| `OnDelete` | Only updates when you manually delete pods | Full control over update order |
| `partition: N` | Only updates pods with ordinal >= N | Canary testing on replicas |

**5. Data migration and upgrades:**

```bash
# Before upgrading a database StatefulSet:
# 1. Take a backup
kubectl exec postgres-0 -- pg_dumpall > backup.sql

# 2. Use partition to test on one replica first
kubectl patch statefulset postgres -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":2}}}}'

# 3. Update the image — only postgres-2 gets updated
kubectl set image statefulset/postgres postgres=postgres:16

# 4. Verify postgres-2 works with new version
kubectl exec postgres-2 -- psql -c "SELECT version();"

# 5. Remove partition to roll out to all pods
kubectl patch statefulset postgres -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":0}}}}'
```

**6. Resource sizing for stateful workloads:**

```yaml
# Databases need guaranteed resources — use Guaranteed QoS class
resources:
  requests:
    cpu: "2"              # Same as limits = Guaranteed QoS
    memory: "4Gi"
  limits:
    cpu: "2"
    memory: "4Gi"
# Guaranteed QoS prevents the pod from being evicted under memory pressure
```

**StatefulSet considerations checklist:**

| # | Consideration | Why It Matters |
|---|---|---|
| 1 | Create headless service first | Required for stable pod DNS |
| 2 | Plan pod ordering | Primary must be ready before replicas |
| 3 | Use `volumeClaimTemplates` | Each pod needs its own persistent storage |
| 4 | PVCs survive deletion | Must manually delete PVCs to free storage |
| 5 | Use `partition` for canary updates | Test database upgrades on one replica first |
| 6 | Backup before upgrades | StatefulSet updates are harder to rollback |
| 7 | Use Guaranteed QoS | Prevent database pods from being evicted |
| 8 | Choose the right storage performance tier | Use gp3/io2 (AWS) or Premium_LRS (Azure) for databases |
| 9 | Plan for data migration | Schema changes need careful coordination |

**Interview question: What are the key considerations for StatefulSets?**
StatefulSets require a headless service for stable DNS, use ordered pod creation (0→1→2) which matters for primary/replica databases, provide per-pod persistent storage via `volumeClaimTemplates` that survives pod deletion, and support partition-based canary updates. Always backup before upgrades, use Guaranteed QoS class for databases, and remember that PVCs must be manually deleted to free storage.

### Job — Run to Completion

```yaml
# job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 1
  backoffLimit: 3          # Retry up to 3 times on failure
  activeDeadlineSeconds: 600  # Timeout after 10 minutes
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: python:3.11
        command: ["python", "-c", "print('Migration complete!')"]
```

```bash
kubectl apply -f job.yaml
kubectl get jobs

# Output:
# NAME              COMPLETIONS   DURATION   AGE
# data-migration    1/1           5s         30s

kubectl logs job/data-migration

# Output:
# Migration complete!
```

**Multiple completions and parallelism:**

Use `completions` to require multiple successful runs and `parallelism` to run pods concurrently:

```yaml
# parallel-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: reporting-job
spec:
  completions: 3       # Job succeeds after 3 pods complete successfully
  parallelism: 3       # Run up to 3 pods at the same time
  backoffLimit: 4
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: reporting-tool
        image: reporting-tool
```

Without `parallelism`, pods run sequentially (one at a time). With `parallelism: 3`, all 3 pods start simultaneously.

```bash
kubectl apply -f parallel-job.yaml
kubectl get jobs

# Output:
# NAME            COMPLETIONS   DURATION   AGE
# reporting-job   0/3           5s         5s

kubectl get pods
# Output (all 3 pods start at the same time due to parallelism: 3):
# NAME                  READY   STATUS    RESTARTS   AGE
# reporting-job-abc12   1/1     Running   0          5s
# reporting-job-def34   1/1     Running   0          5s
# reporting-job-ghi56   1/1     Running   0          5s

# After completion:
kubectl get jobs
# NAME            COMPLETIONS   DURATION   AGE
# reporting-job   3/3           12s        30s
```

### CronJob — Scheduled Jobs

```yaml
# cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 2 * * *"        # Every day at 2 AM UTC
  concurrencyPolicy: Forbid     # Don't run if previous still running
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres-0.postgres -U admin mydb > /backup/db-$(date +%Y%m%d).sql
              echo "Backup completed at $(date)"
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
```

```bash
kubectl apply -f cronjob.yaml
kubectl get cronjobs

# Output:
# NAME        SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
# db-backup   0 2 * * *     False     0        <none>          30s

# Manually trigger a CronJob
kubectl create job --from=cronjob/db-backup manual-backup

# Output:
# job.batch/manual-backup created

# After the CronJob runs on schedule, child Jobs are created automatically:
kubectl get jobs
# NAME                     COMPLETIONS   DURATION   AGE
# db-backup-28451320       1/1           8s         2m
# db-backup-28451380       1/1           7s         1m
# db-backup-28451440       0/1           5s         5s    ← currently running

# View logs from the latest job
kubectl logs job/db-backup-28451440
# Backup completed at Mon Feb 24 02:00:05 UTC 2026
```

### Static Pods

Static pods are managed directly by the kubelet on a specific node, without the API server's involvement. The kubelet watches a designated directory for YAML manifests and automatically creates/deletes pods when files are added/removed.

**What if there's no cluster at all?**

The kubelet can operate independently — even without a kube-apiserver, kube-scheduler, or etcd. When only the kubelet and a container runtime (e.g., containerd) are installed on a host, the kubelet can still manage pods by reading definition files from a local directory. These are static pods.

Only pod-level resources can be created this way. Higher-level abstractions like ReplicaSets, Deployments, or Services depend on control plane controllers and cannot be managed via static pod manifests.

The kubelet periodically scans the manifest directory, reads available files, and creates the corresponding pods. It also:
- **Restarts** pods if the application crashes
- **Recreates** pods when a manifest file is updated
- **Deletes** pods when a manifest file is removed

**Configuring the static pod directory:**

The directory location is provided to the kubelet at startup. There are two methods:

Method 1 — `--pod-manifest-path` option directly in the kubelet service file:

```bash
# kubelet.service (excerpt)
ExecStart=/usr/local/bin/kubelet \
  --container-runtime=remote \
  --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock \
  --pod-manifest-path=/etc/kubernetes/manifests \
  --kubeconfig=/var/lib/kubelet/kubeconfig \
  --network-plugin=cni \
  --register-node=true \
  --v=2
```

Method 2 — `--config` option pointing to a configuration file with `staticPodPath`:

```bash
# kubelet.service (excerpt)
ExecStart=/usr/local/bin/kubelet \
  --container-runtime=remote \
  --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock \
  --config=kubeconfig.yaml \
  --kubeconfig=/var/lib/kubelet/kubeconfig \
  --network-plugin=cni \
  --register-node=true \
  --v=2
```

```yaml
# kubeconfig.yaml
staticPodPath: /etc/kubernetes/manifests
```

kubeadm clusters use Method 2. When inspecting an existing cluster, first check for `--pod-manifest-path` in the kubelet service. If absent, look for `--config` and check the referenced file's `staticPodPath`.

**Verifying static pods without a cluster (standalone):**

In a standalone scenario (no API server), use container runtime commands directly:

```bash
docker ps
```

```
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS          NAMES
8e5d4c4db7b6   busybox                "sh -c 'echo Hello…'"    20 seconds ago   Up 20 seconds   k8s_myapp-container_myapp-pod-host01_default_...
f6737e1149cb   k8s.gcr.io/pause:3.1   "/pause"                 24 seconds ago   Up 23 seconds   k8s_POD_myapp-pod-host01_default_...
```

`kubectl` commands won't work here because there's no API server to process requests.

**Behavior when part of a cluster (mirror pods):**

When the node is part of a cluster, the kubelet handles pod definitions from both the static pod directory and the API server. For each static pod, the kubelet creates a read-only **mirror object** in the kube-apiserver. This mirror pod:
- Is visible via `kubectl get pods`
- Cannot be edited or deleted through the API — changes must be made to the manifest file on the node
- Has the node name appended to the pod name (e.g., `static-web-node01`)

```bash
kubectl get pods
```

```
NAME                READY   STATUS              RESTARTS   AGE
static-web-node01   0/1     ContainerCreating   0          29s
```

**How static pods differ from regular pods:**

| Feature | Regular Pods | Static Pods |
|---------|-------------|-------------|
| Created by | API server (kubectl, controllers) | kubelet (from manifest files) |
| Visible in `kubectl get pods` | Yes | Yes (as read-only "mirror pods") |
| Can be deleted with `kubectl delete` | Yes (permanently) | No (kubelet recreates them) |
| ownerReferences | ReplicaSet, Deployment, etc. | `kind: Node` |
| Naming convention | `<name>-<random>` | `<name>-<node-name>` |
| Managed by scheduler | Yes | No (always on the node where the manifest lives) |

**Where are static pod manifests stored?**

The kubelet reads the manifest directory from its config:

```bash
cat /var/lib/kubelet/config.yaml | grep staticPodPath
```

```
staticPodPath: /etc/kubernetes/manifests
```

```bash
ls /etc/kubernetes/manifests/
```

```
etcd.yaml  kube-apiserver.yaml  kube-controller-manager.yaml  kube-scheduler.yaml
```

These are the control plane components — they are all static pods managed by the kubelet.

**Identifying static pods:**

Method 1 — naming convention (node name appended):

```bash
kubectl get pods -n kube-system
```

```
NAME                                   READY   STATUS    RESTARTS   AGE
etcd-controlplane                      1/1     Running   0          30d
kube-apiserver-controlplane            1/1     Running   0          30d
kube-controller-manager-controlplane   1/1     Running   0          30d
kube-scheduler-controlplane            1/1     Running   0          30d
coredns-64897985d-6qwf5                1/1     Running   0          30d
```

Pods ending in `-controlplane` are static pods. `coredns` is not (managed by a ReplicaSet).

Method 2 — check ownerReferences:

```bash
# Static pod — owned by Node
kubectl get pod kube-apiserver-controlplane -n kube-system -o jsonpath='{.metadata.ownerReferences[0].kind}'
```

```
Node
```

```bash
# Regular pod — owned by ReplicaSet
kubectl get pod coredns-64897985d-6qwf5 -n kube-system -o jsonpath='{.metadata.ownerReferences[0].kind}'
```

```
ReplicaSet
```

**Creating a static pod:**

```bash
# Generate the manifest
kubectl run static-busybox --image=busybox --restart=Never \
  --dry-run=client -o yaml --command -- sleep 1000 > static-busybox.yaml

# Place it in the manifests directory
sudo cp static-busybox.yaml /etc/kubernetes/manifests/

# The kubelet detects the file and creates the pod automatically
kubectl get pods
```

```
NAME                             READY   STATUS    RESTARTS   AGE
static-busybox-controlplane      1/1     Running   0          5s
```

**Editing a static pod:**

Edit the manifest file directly — the kubelet detects changes and recreates the pod:

```bash
sudo vi /etc/kubernetes/manifests/static-busybox.yaml
# Change image: busybox → busybox:1.28.4

# The kubelet automatically restarts the pod with the new image
kubectl get pods --watch
```

**Deleting a static pod permanently:**

`kubectl delete pod` only removes the mirror pod temporarily — the kubelet recreates it. To permanently delete:

```bash
# Remove the manifest file
sudo rm /etc/kubernetes/manifests/static-busybox.yaml

# The kubelet detects the removal and terminates the pod
kubectl get pods --watch
```

**Deleting a static pod on a different node:**

```bash
# SSH into the node
ssh node01

# Find the static pod manifest directory on that node
cat /var/lib/kubelet/config.yaml | grep staticPodPath
# staticPodPath: /etc/just-to-mess-with-you    (can be custom!)

# Remove the manifest
rm /etc/just-to-mess-with-you/greenbox.yaml

# Exit and verify
exit
kubectl get pods --watch
```

**Real-world use cases for static pods:**
- Control plane components on kubeadm clusters (API server, etcd, scheduler, controller manager)
- Running essential agents on nodes that must survive API server outages
- Bootstrap scenarios where the API server isn't available yet

**Static Pods vs DaemonSets:**

Both static pods and DaemonSets ensure pods run on nodes, but they work differently:

| Feature | Static Pods | DaemonSets |
|---------|-------------|------------|
| Created by | kubelet (from manifest files on the node) | DaemonSet controller via the kube-apiserver |
| Control plane required | No — works without API server | Yes — requires kube-apiserver |
| Typical use case | Control plane components (API server, etcd) | Monitoring agents, log collectors, network plugins |
| Scheduler involvement | Ignored by the kube-scheduler | Ignored by the kube-scheduler |
| Scope | Single node (where the manifest lives) | All nodes (or a subset via nodeSelector/affinity) |

Both are ignored by the kube-scheduler — static pods are managed entirely by the kubelet, and DaemonSets use the DaemonSet controller to place pods directly.

**Interview question: What are static pods and how do you manage them?**
Static pods are created by the kubelet directly from manifest files in a configured directory (typically `/etc/kubernetes/manifests`). They appear in `kubectl get pods` as read-only mirror pods but cannot be controlled through the API server. To create, edit, or delete static pods, you must manage the manifest files on the node. The kubelet watches the directory and automatically reconciles. Control plane components in kubeadm clusters are static pods.

---

## 12.2 Industry Example: E-Commerce Microservices

```yaml
# A typical e-commerce platform deployment structure:
#
# Deployments (stateless):
#   - frontend (React app, 3 replicas)
#   - api-gateway (3 replicas)
#   - product-service (3 replicas)
#   - order-service (3 replicas)
#   - payment-service (2 replicas)
#   - notification-service (2 replicas)
#
# StatefulSets (stateful):
#   - postgresql (3 replicas, primary + replicas)
#   - redis-cluster (6 replicas)
#   - elasticsearch (3 replicas)
#
# DaemonSets (per-node):
#   - fluentd (log collection)
#   - datadog-agent (monitoring)
#
# CronJobs:
#   - db-backup (daily at 2 AM)
#   - report-generator (weekly)
#   - cache-cleanup (hourly)

# Example: Product Service Deployment
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
        version: v2.1.0
    spec:
      serviceAccountName: product-service-sa
      containers:
      - name: product-service
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/product-service:v2.1.0
        ports:
        - containerPort: 8080
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
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 12.3 Module 3 Exercises

### Exercise 1: Pod Lifecycle
```bash
# 1. Create a pod that intentionally fails
kubectl run fail-pod --image=busybox --command -- /bin/sh -c "exit 1"
# 2. Watch it go into CrashLoopBackOff
kubectl get pods -w
# 3. Check events
kubectl describe pod fail-pod
# 4. Clean up
kubectl delete pod fail-pod
```

### Exercise 2: Deployment Rolling Update
```bash
# 1. Create deployment with nginx:1.24
kubectl create deployment web --image=nginx:1.24 --replicas=3
# 2. Update to nginx:1.25
kubectl set image deployment/web nginx=nginx:1.25
# 3. Watch the rollout
kubectl rollout status deployment/web
# 4. Check history
kubectl rollout history deployment/web
# 5. Rollback
kubectl rollout undo deployment/web
# 6. Verify
kubectl describe deployment web | grep Image
```

### Exercise 3: Create a CronJob
```bash
# Create a job that prints the date every minute
kubectl create cronjob date-printer --image=busybox --schedule="*/1 * * * *" -- /bin/sh -c "date; echo Hello from K8s CronJob"
# Watch jobs being created
kubectl get jobs -w
# Check logs
kubectl logs job/date-printer-<id>
```

---

**Next Module: Services, Networking & Ingress →**
