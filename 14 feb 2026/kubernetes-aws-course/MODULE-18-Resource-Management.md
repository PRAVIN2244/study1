# MODULE 18: Resource Management — Requests, Limits & Quotas

---

## 18.1 Resource Requests, Limits & Quotas

Kubernetes has three types of resource policies:

| Policy | Scope | Purpose |
|---|---|---|
| `ResourceQuota` | Namespace | Limits total resource consumption (CPU, memory, object count) |
| `LimitRange` | Namespace | Sets default/min/max for individual pods/containers |
| `NetworkPolicy` | Namespace | Controls network traffic between pods (covered in Module 4) |

**ResourceQuota vs LimitRange:**
- ResourceQuota limits the **total** across all pods in a namespace (e.g., "max 10 CPU total")
- LimitRange limits **individual** pods/containers (e.g., "each container max 2 CPU")
- Use both together: LimitRange sets per-pod defaults, ResourceQuota caps the namespace total

### Container-Level Requests & Limits

You can specify how much CPU and memory each container in a pod needs. The scheduler uses **requests** to decide which node to place the pod on. The kubelet enforces **limits** so the container cannot exceed the maximum.

- **requests** — minimum resources reserved for the container. The kubelet guarantees at least this amount.
- **limits** — maximum resources the container can use. If exceeded, CPU is throttled; if memory limit is exceeded, the container is OOMKilled.

**CPU units — what does "1 CPU" mean?**

| Cloud Provider | 1 CPU = |
|---|---|
| AWS | 1 vCPU |
| GCP | 1 Core |
| Azure | 1 vCore |
| Bare metal | 1 Hyperthread |

Fractional values are supported: `0.1` CPU = `100m` (100 milliCPU). The minimum is `1m`. You can use either decimal (`0.5`) or milliCPU (`500m`) notation.

```yaml
resources:
  requests:
    memory: "128Mi"    # 128 MebiByte = ~135 Megabyte (MB)
    cpu: "500m"        # 500 milliCPU = 0.5 vCPU core
  limits:
    memory: "500Mi"
    cpu: "1000m"       # 1000m = 1 full vCPU core
```

**Resource units:**

| Unit | Meaning | Example |
|---|---|---|
| `m` (milliCPU) | 1/1000 of a CPU core | `500m` = 0.5 CPU, `1000m` = 1 CPU |
| `Mi` (MebiByte) | 1,048,576 bytes | `128Mi` = ~134 MB |
| `Gi` (GibiByte) | 1,073,741,824 bytes | `1Gi` = ~1.07 GB |

**CPU behavior — four scenarios:**

| Scenario | Requests | Limits | Behavior |
|----------|----------|--------|----------|
| No requests, no limits | — | — | Container can consume all available CPU on the node, starving other pods |
| Limits only (no requests) | Auto-set = limit | Set | Kubernetes sets requests equal to limits. Container is guaranteed and capped at the same value |
| Both requests and limits | Set | Set | Container is guaranteed its request (e.g., 1 vCPU) and can burst up to the limit (e.g., 3 vCPU). CPU is **throttled** at the limit |
| Requests only (no limits) | Set | — | Container is guaranteed its request and can use any available idle CPU on the node. Best for efficient utilization |

**Memory behavior — four scenarios:**

| Scenario | Requests | Limits | Behavior |
|----------|----------|--------|----------|
| No requests, no limits | — | — | Container can consume all node memory, potentially causing OOM for other pods |
| Limits only (no requests) | Auto-set = limit | Set | Kubernetes sets requests equal to limits |
| Both requests and limits | Set | Set | Container is guaranteed its request and can burst up to the limit. If it exceeds the limit, the container is **OOMKilled** (terminated) |
| Requests only (no limits) | Set | — | Container is guaranteed its request but can consume more. If it uses too much, it may be OOMKilled when the node runs low on memory |

**Key difference:** CPU is **throttled** (slowed down) when the limit is reached. Memory causes **OOMKill** (container termination) when exceeded — memory cannot be throttled.

**What happens when no node has enough resources:**

```bash
kubectl describe pod nginx | tail -10
```

```
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  10s   default-scheduler  0/3 nodes are available:
           3 Insufficient cpu.
```

The pod stays in `Pending` state until a node with sufficient resources becomes available.

**Troubleshooting OOMKilled pods:**

```bash
kubectl get pods
```

```
NAME       READY   STATUS             RESTARTS   AGE
elephant   0/1     CrashLoopBackOff   3          2m
```

```bash
kubectl describe pod elephant | grep -A5 "Last State"
```

```
    Last State:   Terminated
      Reason:     OOMKilled
      Exit Code:  137
      Started:    Sat, 16 Apr 2024 18:00:40 +0000
      Finished:   Sat, 16 Apr 2024 18:00:44 +0000
```

The container exceeded its memory limit and was killed. To fix, increase the memory limit:

```bash
# Try editing the pod directly
kubectl edit pod elephant
```

```
error: pods "elephant" is invalid
A copy of your changes has been stored to "/tmp/kubectl-edit-3376288381.yaml"
```

⚠️ Resource limits cannot be changed on a running pod. The edited YAML is saved to a temp file. Use `kubectl replace --force` to delete and recreate:

```bash
kubectl replace --force -f /tmp/kubectl-edit-3376288381.yaml
```

```
pod "elephant" deleted
pod/elephant replaced
```

```bash
kubectl get pods
```

```
NAME       READY   STATUS    RESTARTS   AGE
elephant   1/1     Running   0          5s
```

**Deploy and test:**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# List pods
kubectl get pods

# Watch pods come up (init containers run first)
kubectl get pods -w

# Describe pod — see resource requests/limits and init container status
kubectl describe pod <usermgmt-microservice-xxxxxx>

# Access application
# http://<WorkerNode-Public-IP>:31231/usermgmt/health-status
```

**Check node resource allocation with `kubectl describe node`:**

```bash
# List nodes
kubectl get nodes

# Describe a node to see resource usage per pod
kubectl describe node <node-name>
```

The `Allocated resources` section in the output shows how much CPU and memory each pod is requesting/limiting on that node:

```
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests      Limits
  --------           --------      ------
  cpu                1050m (53%)   2200m (110%)
  memory             640Mi (17%)   1524Mi (41%)
  ephemeral-storage  0 (0%)        0 (0%)
```

This tells you:
- **Requests column** — how much capacity is reserved (scheduler won't place new pods if requests exceed node capacity)
- **Limits column** — maximum consumption (can exceed 100% because limits are not guaranteed — overcommit is allowed)
- Use this to identify nodes that are running hot or have room for more pods

```bash
# Clean up
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

### QoS Classes (Quality of Service)

Kubernetes assigns a QoS class to each pod based on its resource configuration. QoS determines eviction priority when a node runs low on resources:

| QoS Class | Condition | Eviction Priority | Use Case |
|---|---|---|---|
| **Guaranteed** | Every container has `requests == limits` for both CPU and memory | Last to be evicted | Production databases, critical services |
| **Burstable** | At least one container has `requests < limits` | Evicted after Best-Effort | General workloads that can tolerate variability |
| **Best-Effort** | No `requests` or `limits` set on any container | First to be evicted | Dev/test, batch jobs where resource guarantees aren't needed |

```yaml
# Guaranteed — requests equal limits
resources:
  requests:
    memory: "500Mi"
    cpu: "500m"
  limits:
    memory: "500Mi"
    cpu: "500m"

# Burstable — requests less than limits
resources:
  requests:
    memory: "200Mi"
    cpu: "200m"
  limits:
    memory: "1Gi"
    cpu: "1"

# Best-Effort — no resources specified
# (omit the resources section entirely)
```

```bash
# Check a pod's QoS class
kubectl get pod <pod-name> -o jsonpath='{.status.qosClass}'
# Output: Guaranteed | Burstable | BestEffort
```

**Eviction order under memory pressure:** Best-Effort pods are evicted first, then Burstable pods exceeding their requests, then Guaranteed pods (only if the node itself is unstable).

> **Multi-tenant relevance:** Assign Guaranteed QoS to critical tenant workloads and Burstable to development namespaces. Combine with ResourceQuota (below) to prevent any tenant from consuming all cluster resources.

### Resource Quotas (Namespace-level limits)

ResourceQuota constrains total resource consumption per namespace. It can limit both object counts and compute resources.

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"           # Total CPU requests
    requests.memory: "20Gi"      # Total memory requests
    limits.cpu: "20"             # Total CPU limits
    limits.memory: "40Gi"        # Total memory limits
    pods: "50"                   # Max pods
    services: "20"               # Max services
    persistentvolumeclaims: "10" # Max PVCs
    configmaps: "20"
    secrets: "20"
```

```bash
kubectl apply -f resource-quota.yaml

kubectl get resourcequota -n development

# Output:
# NAME         AGE   REQUEST                                          LIMIT
# team-quota   30s   pods: 5/50, requests.cpu: 500m/10, ...          limits.cpu: 1250m/20, ...

kubectl describe resourcequota team-quota -n development

# Output:
# Name:                   team-quota
# Namespace:              development
# Resource                Used    Hard
# --------                ----    ----
# configmaps              2       20
# limits.cpu              1250m   20
# limits.memory           2560Mi  40Gi
# persistentvolumeclaims  1       10
# pods                    5       50
# requests.cpu            500m    10
# requests.memory         1280Mi  20Gi
# secrets                 3       20
# services                2       20
```

**Object count quota example** — limit the number of pods in a namespace:

```yaml
# pod-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: pod-demo
  namespace: quota-pod
spec:
  hard:
    pods: "2"
```

```yaml
# pod-quota-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pod-quota-demo
  namespace: quota-pod
spec:
  selector:
    matchLabels:
      purpose: quota-demo
  replicas: 3
  template:
    metadata:
      labels:
        purpose: quota-demo
    spec:
      containers:
      - name: pod-quota-demo
        image: nginx
```

```bash
kubectl create namespace quota-pod
kubectl apply -f pod-quota.yaml
kubectl apply -f pod-quota-deploy.yaml

# Only 2 of 3 replicas will be created — quota limits to 2 pods
kubectl get pods -n quota-pod
kubectl get rs -n quota-pod
```

**Compute resource quota example:**

```yaml
# mem-cpu-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-cpu-demo
  namespace: quota-mem-cpu
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

```yaml
# mem-cpu-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memcpu-quota-demo
  namespace: quota-mem-cpu
spec:
  selector:
    matchLabels:
      purpose: quota-demo
  replicas: 1
  template:
    metadata:
      labels:
        purpose: quota-demo
    spec:
      containers:
      - name: memcpu-quota-demo
        image: nginx
        resources:
          limits:
            memory: "1Gi"
            cpu: "800m"
          requests:
            memory: "700Mi"
            cpu: "400m"
```

```bash
kubectl create namespace quota-mem-cpu
kubectl apply -f mem-cpu-quota.yaml
kubectl apply -f mem-cpu-deploy.yaml
```

### LimitRange (Default limits for pods)

LimitRange sets default resource requests/limits for pods in a namespace and enforces min/max constraints. Unlike ResourceQuota (which limits totals), LimitRange constrains individual pods/containers.

```yaml
# limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: development
spec:
  limits:
  - type: Container
    default:              # Default limits if not specified
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:       # Default requests if not specified
      cpu: "100m"
      memory: "128Mi"
    max:                  # Maximum allowed
      cpu: "2"
      memory: "4Gi"
    min:                  # Minimum allowed
      cpu: "50m"
      memory: "64Mi"
  - type: Pod
    max:
      cpu: "4"
      memory: "8Gi"
```

```bash
kubectl apply -f limitrange.yaml

# Now create a pod without resource specs
kubectl run test-pod --image=nginx -n development

# Check — default limits are applied automatically
kubectl describe pod test-pod -n development | grep -A4 Limits

# Output:
# Limits:
#   cpu:     500m
#   memory:  512Mi
# Requests:
#   cpu:     100m
#   memory:  128Mi
```

**LimitRange with min/max enforcement:**

```yaml
# limitrange-minmax.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: cpumem-resource-constraint
  namespace: limitrange-mem-cpu
spec:
  limits:
  - default:
      cpu: 500m
      memory: 500Mi
    defaultRequest:
      cpu: 500m
      memory: 500Mi
    max:
      cpu: "1"
      memory: 1Gi
    min:
      cpu: 100m
      memory: 500Mi
    type: Container
```

```bash
kubectl create namespace limitrange-mem-cpu
kubectl apply -f limitrange-minmax.yaml
```

A pod without resource specs gets the defaults. A pod requesting resources outside the min/max range is rejected:

```yaml
# Pod without resource specs — gets defaults (500m CPU, 500Mi memory)
apiVersion: v1
kind: Pod
metadata:
  name: limitrange-demo-1
  namespace: limitrange-mem-cpu
spec:
  containers:
  - name: constraints-demo-ctr
    image: nginx
```

```yaml
# Pod with explicit resources within range — accepted
apiVersion: v1
kind: Pod
metadata:
  name: limitrange-demo-2
  namespace: limitrange-mem-cpu
spec:
  containers:
  - name: constraints-demo-ctr
    image: nginx
    resources:
      limits:
        memory: "800Mi"
      requests:
        memory: "600Mi"
```

---

