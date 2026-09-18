# MODULE 19: Scheduling — Taints, Affinity & Priority

---

## 19.1 Node Scheduling

Kubernetes provides multiple mechanisms to control where pods run. These range from simple (nodeSelector) to complex (affinity rules, taints). Understanding when to use each is important for production clusters.

**Scheduling mechanisms summary:**

| Mechanism | Level | Purpose |
|---|---|---|
| `nodeSelector` | Pod | Simple: schedule on nodes with specific labels |
| `nodeName` | Pod | Direct: schedule on a specific node by name (bypasses scheduler) |
| Taints/Tolerations | Node + Pod | Repel pods from nodes unless they tolerate the taint |
| Node Affinity | Pod | Advanced: required or preferred node selection with expressions |
| Pod Affinity | Pod | Schedule near (or away from) other pods |
| Topology Spread | Pod | Evenly distribute pods across zones/nodes |

**Interview question: What's the difference between taints/tolerations and node affinity?**
- Taints are set on **nodes** to repel pods (push away)
- Node affinity is set on **pods** to attract them to nodes (pull toward)
- Use both together for dedicated nodes: taint the node (repel others) + affinity on the pod (attract to it)

### Manual Scheduling (nodeName)

When no scheduler is running — or when you need direct control — you can manually assign a pod to a node using the `nodeName` field.

**How the default scheduler works:**
Every pod has a `nodeName` field that is empty by default. The scheduler watches for pods without a `nodeName`, selects a node, and sets this field by creating a Binding object. If no scheduler is running, pods stay in `Pending` state indefinitely.

**Method 1: Set nodeName at creation time**

```yaml
# manual-schedule.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    name: nginx
spec:
  nodeName: node02              # Bypasses the scheduler entirely
  containers:
  - name: nginx
    image: nginx
    ports:
    - containerPort: 8080
```

```bash
kubectl apply -f manual-schedule.yaml
kubectl get pods -o wide
```

```
NAME    READY   STATUS    RESTARTS   AGE   IP          NODE
nginx   1/1     Running   0          9s    10.40.0.4   node02
```

⚠️ `nodeName` can only be set at creation time. You cannot change it on a running pod.

**Method 2: Binding object (reassign a running pod)**

If a pod is already created without a `nodeName` (stuck in Pending), you can mimic the scheduler by creating a Binding object:

```yaml
# binding.yaml
apiVersion: v1
kind: Binding
metadata:
  name: nginx
target:
  apiVersion: v1
  kind: Node
  name: node02
```

Send the binding as a POST request to the API server:

```bash
# Convert to JSON and POST to the pod's binding API
curl --header "Content-Type: application/json" \
  --request POST \
  --data '{"apiVersion":"v1","kind":"Binding","metadata":{"name":"nginx"},"target":{"apiVersion":"v1","kind":"Node","name":"node02"}}' \
  https://$SERVER/api/v1/namespaces/default/pods/nginx/binding
```

**When to use manual scheduling:**

| Scenario | Recommended Approach |
|----------|---------------------|
| No scheduler running (broken cluster) | `nodeName` or Binding object |
| Debugging — force pod to specific node | `nodeName` (temporary) |
| Production workloads | Never — use nodeSelector, affinity, or taints instead |

**Interview question: What happens if no scheduler is running?**
Pods without a `nodeName` remain in `Pending` state forever. You can manually schedule them by setting `nodeName` in the pod spec (at creation time only) or by creating a Binding object via the API.

**Diagnosing an unscheduled pod:**

```bash
kubectl describe pod nginx | grep -E "Node:|Status:"
```

```
Node:           <none>
Status:         Pending
```

`Node: <none>` confirms no scheduler has assigned the pod.

**Replacing a running pod on a different node:**

Since `nodeName` cannot be changed on a running pod, use `kubectl replace --force` to delete and recreate in one step:

```bash
# Edit the YAML to change nodeName (e.g., from node01 to controlplane)
vi nginx.yaml

# Force replace — deletes the existing pod and creates a new one
kubectl replace --force -f nginx.yaml
```

```
pod "nginx" deleted
pod/nginx replaced
```

```bash
# Watch the pod transition to Running
kubectl get pods --watch
```

```
NAME    READY   STATUS              RESTARTS   AGE
nginx   0/1     ContainerCreating   0          2s
nginx   1/1     Running             0          5s
```

```bash
# Verify the pod is on the correct node
kubectl get pods -o wide
```

```
NAME    READY   STATUS    RESTARTS   AGE   IP           NODE           NOMINATED NODE
nginx   1/1     Running   0          15s   10.244.0.4   controlplane   <none>
```

### Taints and Tolerations

Taints are applied to nodes to repel pods. Tolerations are applied to pods to allow scheduling on tainted nodes.

**Real-life analogy:** A taint is like a "VIP Only" sign on a restaurant table. Only guests with a VIP pass (toleration) can sit there. Another way to think about it: a taint is like bug repellent sprayed on a person — only bugs (pods) that are tolerant to the repellent can land on them.

**How scheduling works with taints and tolerations:**

Consider a cluster with 3 worker nodes and 4 pods (A, B, C, D). Without any taints, the scheduler distributes pods evenly across all nodes.

Now suppose you want to dedicate Node 1 to a specific application:

1. Taint Node 1 with `app=blue:NoSchedule` — no pods can schedule there by default
2. Add a matching toleration to Pod D — only Pod D can tolerate the taint

Scheduling result:
- Pod A (no toleration) → scheduled on Node 2 or Node 3
- Pod B (no toleration) → scheduled on Node 2 or Node 3
- Pod C (no toleration) → scheduled on Node 2 or Node 3
- Pod D (has toleration) → can schedule on Node 1

> **Important:** Taints and tolerations do NOT guarantee that a pod will be placed on a specific node. Pod D *can* schedule on Node 1, but it might also end up on Node 2 or Node 3 if the scheduler decides so. Taints only repel — they don't attract. To guarantee placement on a specific node, combine taints with node affinity.

```bash
# Add a taint to a node
kubectl taint nodes ip-10-0-1-100.ec2.internal workload=gpu:NoSchedule

# Command breakdown:
# workload=gpu     → key=value
# NoSchedule       → effect (don't schedule new pods here)

# Output:
# node/ip-10-0-1-100.ec2.internal tainted

# View taints on a node
kubectl describe node ip-10-0-1-100.ec2.internal | grep -A5 Taints

# Output:
# Taints:             workload=gpu:NoSchedule

# Remove a taint (note the minus sign at the end)
kubectl taint nodes ip-10-0-1-100.ec2.internal workload=gpu:NoSchedule-

# Output:
# node/ip-10-0-1-100.ec2.internal untainted
```

**Taint Effects:**

| Effect | Behavior |
|---|---|
| `NoSchedule` | New pods won't be scheduled (existing pods stay) |
| `PreferNoSchedule` | Scheduler tries to avoid, but may schedule if needed. If the pod tolerates any one taint, it can be scheduled (soft constraint) |
| `NoExecute` | Immediately evicts existing pods without matching toleration AND prevents new scheduling |

**Use cases for taints:**
- **Dedicated nodes** — reserve nodes for specific teams or workloads
- **Nodes with special hardware** — GPUs, high-memory instances
- **Taint-based evictions** — remove pods from nodes during maintenance

**Step-by-step workflow:**

```yaml
# 1. Create a pod without toleration
# testpod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: demopod
spec:
  containers:
  - name: demopod
    image: nginx
```

```bash
kubectl apply -f testpod.yaml
kubectl describe pod demopod

# 2. Taint the node — demopod continues running (NoSchedule only affects new pods)
kubectl taint nodes <nodename> taint=true:NoSchedule
kubectl describe node <nodename> | grep -i Taint

# 3. Create a pod WITH toleration — it can schedule on the tainted node
```

```yaml
# taintpod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: demo-taint
spec:
  containers:
  - name: demotaint
    image: nginx
  tolerations:
  - key: "taint"
    value: "true"
    effect: "NoSchedule"
```

```bash
kubectl apply -f taintpod.yaml
kubectl describe pod demo-taint

# Remove a taint
kubectl taint nodes <nodename> taint=true:NoSchedule-

# NoExecute evicts existing pods without tolerations immediately
kubectl taint nodes <nodename> taint=true:NoExecute
```

**Understanding NoExecute in detail:**

`NoExecute` is the most aggressive taint effect. Unlike `NoSchedule` (which only affects future scheduling), `NoExecute` has an immediate impact on already-running pods:

- Pods **without** a matching toleration are **evicted immediately** from the node
- Pods **with** a matching toleration continue running
- New pods without a matching toleration are also prevented from scheduling

Example: Suppose pods A, C, and D are running on Node 1. You apply `app=blue:NoExecute` to Node 1. Pod D has a matching toleration, but pods A and C do not. Result: pods A and C are evicted and rescheduled elsewhere; Pod D stays on Node 1.

Without a taint on the node, tolerations have no effect — they are only evaluated when a matching taint exists.

```yaml
# Pod with toleration (GPU example)
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
  - key: "workload"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
  containers:
  - name: gpu-app
    image: nvidia/cuda:12.0-base
    resources:
      limits:
        nvidia.com/gpu: 1
```

**Lab: Taints and Tolerations Walkthrough**

**Step 1: Check existing taints on a node**

```bash
kubectl describe node node01 | grep Taints
```

```
Taints:             <none>
```

**Step 2: Apply a taint**

```bash
kubectl taint node node01 spray=mortein:NoSchedule
```

**Step 3: Create a pod without toleration — stays Pending**

```bash
kubectl run mosquito --image=nginx

kubectl get pods
```

```
NAME       READY   STATUS    RESTARTS   AGE
mosquito   0/1     Pending   0          30s
```

```bash
kubectl describe pod mosquito | grep -A3 Events
```

```
Events:
  Warning  FailedScheduling  10s  default-scheduler  0/2 nodes are available:
           1 node(s) had taint {node-role.kubernetes.io/master: }, that the pod didn't tolerate,
           1 node(s) had taint {spray: mortein}, that the pod didn't tolerate.
```

**Step 4: Create a pod with toleration — schedules on tainted node**

```bash
kubectl run bee --image=nginx --dry-run=client -o yaml > bee.yaml
```

Edit `bee.yaml` to add toleration:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: bee
spec:
  tolerations:
  - key: "spray"
    operator: "Equal"
    value: "mortein"
    effect: "NoSchedule"
  containers:
  - name: bee
    image: nginx
```

```bash
kubectl apply -f bee.yaml

kubectl get pods -o wide
```

```
NAME       READY   STATUS    RESTARTS   AGE   IP           NODE           NOMINATED NODE
bee        1/1     Running   0          10s   10.244.1.2   node01         <none>
mosquito   0/1     Pending   0          2m    <none>       <none>         <none>
```

`bee` schedules on node01 (tolerates the taint). `mosquito` stays Pending.

**Step 5: Remove the control plane taint to unblock mosquito**

```bash
# Check control plane taint
kubectl describe node controlplane | grep Taints
```

```
Taints:             node-role.kubernetes.io/master:NoSchedule
```

```bash
# Remove it (note the minus sign at the end)
kubectl taint node controlplane node-role.kubernetes.io/master:NoSchedule-
```

```
node/controlplane untainted
```

```bash
kubectl get pods -o wide
```

```
NAME       READY   STATUS    RESTARTS   AGE   IP           NODE           NOMINATED NODE
bee        1/1     Running   0          2m    10.244.1.2   node01         <none>
mosquito   1/1     Running   0          4m    10.244.0.4   controlplane   <none>
```

`mosquito` now runs on the control plane since its taint was removed.

### Node Selectors

Simple way to schedule pods on specific nodes using label matching.

**Real-world scenario:** You have a 3-node cluster — two nodes with limited resources and one large node with high CPU/memory. Data processing pods should run on the large node, not on the smaller ones.

**Step 1: Label the target node**

```bash
# Label a node
kubectl label nodes ip-10-0-1-100.ec2.internal size=Large

# Output:
# node/ip-10-0-1-100.ec2.internal labeled

# Verify the label
kubectl get nodes --show-labels | grep size

# Output:
# ip-10-0-1-100.ec2.internal   Ready   <none>   30d   v1.30.0   ...,size=Large
```

**Step 2: Use nodeSelector in the pod spec**

```yaml
# data-processor.yaml
apiVersion: v1
kind: Pod
metadata:
  name: data-processor
spec:
  nodeSelector:
    size: Large                # Only schedule on nodes labeled size=Large
  containers:
  - name: data-processor
    image: data-processor
    resources:
      requests:
        cpu: "4"
        memory: "8Gi"
```

```bash
kubectl apply -f data-processor.yaml

kubectl get pods -o wide
```

```
NAME             READY   STATUS    RESTARTS   AGE   IP          NODE
data-processor   1/1     Running   0          10s   10.40.0.5   ip-10-0-1-100.ec2.internal
```

⚠️ **Node must be labeled before creating the pod.** If no node matches the selector, the pod stays `Pending`.

**Limitations of nodeSelector:**
- Only supports exact key=value matching — cannot express "Large OR Medium"
- Cannot express "NOT Small"
- No soft/preferred rules — it's always a hard constraint
- For these cases, use **Node Affinity** (below)

### Node Affinity (Advanced Scheduling)

More expressive than nodeSelector — supports "preferred" and "required" rules with operators like `In`, `NotIn`, and `Exists`.

**Why node affinity over nodeSelector?**

| Feature | nodeSelector | Node Affinity |
|---------|-------------|---------------|
| Matching | Exact key=value only | `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt` |
| Multiple values | No | Yes (`In` with list of values) |
| Soft/hard rules | Hard only | Both `required` (hard) and `preferred` (soft) |
| Weight-based preference | No | Yes (weighted scoring) |

**Scheduling rule types:**
- `requiredDuringSchedulingIgnoredDuringExecution` — the scheduler can't schedule the Pod unless the rule is met (hard constraint)
- `preferredDuringSchedulingIgnoredDuringExecution` — the scheduler tries to find a matching node, but still schedules if none is available (soft constraint)
- `IgnoredDuringExecution` — if node labels change after scheduling, the Pod continues to run

**Available operators:**

| Operator | Meaning | Values Required? |
|----------|---------|-----------------|
| `In` | Label value must be one of the listed values | Yes |
| `NotIn` | Label value must NOT be any of the listed values | Yes |
| `Exists` | Label key must exist (any value) | No |
| `DoesNotExist` | Label key must NOT exist | No |
| `Gt` | Label value (parsed as integer) must be greater than | Yes (single value) |
| `Lt` | Label value (parsed as integer) must be less than | Yes (single value) |

```yaml
# node-affinity.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      affinity:
        nodeAffinity:
          # MUST be on nodes in us-east-1a or us-east-1b
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-east-1a
                - us-east-1b

          # PREFER nodes with instance type m5.large
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 80
            preference:
              matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values:
                - m5.large
                - m5.xlarge

      containers:
      - name: web-app
        image: nginx:1.25
```

**Hard affinity (required) example:**

```yaml
# node-affinity-hard.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-affinity-hard
spec:
  replicas: 1
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
        ports:
        - containerPort: 80
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: myname
                operator: In
                values:
                - nodeaffinity
```

```bash
kubectl apply -f node-affinity-hard.yaml

# Pod stays Pending until a node has the matching label
kubectl label nodes <node> myname=nodeaffinity

# Remove the label — pod continues running due to "IgnoredDuringExecution"
kubectl label nodes <node> myname-
```

**Soft affinity (preferred) example:**

```yaml
# node-affinity-soft.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-affinity-soft
spec:
  replicas: 1
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
        image: nginx:1.14.2
        ports:
        - containerPort: 80
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 1
            preference:
              matchExpressions:
              - key: myname
                operator: In
                values:
                - nodeaffinity
```

With `preferred`, the pod schedules even if no node matches — the scheduler just prefers matching nodes.

**NotIn operator — avoid specific nodes:**

```yaml
# Avoid nodes labeled size=Small
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: size
          operator: NotIn
          values:
          - Small
```

**Exists operator — check label presence only (no value needed):**

```yaml
# Schedule on any node that has the "size" label, regardless of its value
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: size
          operator: Exists
```

**Node affinity types — scheduling vs execution behavior:**

| Type | During Scheduling | During Execution |
|------|------------------|-----------------|
| `requiredDuringSchedulingIgnoredDuringExecution` | Must match (pod stays Pending if no match) | Ignored (pod keeps running even if labels change) |
| `preferredDuringSchedulingIgnoredDuringExecution` | Prefers match (schedules elsewhere if no match) | Ignored |
| `requiredDuringSchedulingRequiredDuringExecution` | Must match | **Evicts pod** if labels change (planned, not yet available) |

The third type is planned for a future Kubernetes release — it would evict running pods if node labels change and no longer satisfy the affinity rules.

**Combining taints/tolerations with node affinity:**

Taints repel pods; node affinity attracts pods. Used together, they ensure pods land on specific nodes and other pods stay away.

```yaml
# node-affinity-with-taint.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-affinity-with-taint
spec:
  replicas: 2
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
        ports:
        - containerPort: 80
      tolerations:
      - key: "taint"
        value: "true"
        effect: "NoSchedule"
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: myname
                operator: In
                values:
                - nodeaffinity
```

```bash
# Setup: label and taint only the target node
kubectl label nodes <node> myname=nodeaffinity
kubectl taint nodes <node> taint=true:NoSchedule

# The deployment's pods will only schedule on this node (affinity + toleration)
kubectl apply -f node-affinity-with-taint.yaml
```

**Lab: Node Affinity Exercises**

**Exercise 1: Inspect node labels**

```bash
kubectl describe node node01 | grep -A10 Labels
```

```
Labels:             beta.kubernetes.io/arch=amd64
                    beta.kubernetes.io/os=linux
                    kubernetes.io/arch=amd64
                    kubernetes.io/hostname=node01
                    kubernetes.io/os=linux
```

**Exercise 2: Label a node and deploy with affinity**

```bash
# Add a label
kubectl label node node01 color=blue

# Verify
kubectl get nodes --show-labels | grep color
```

```bash
# Create deployment with node affinity targeting color=blue
kubectl create deployment blue --image=nginx --replicas=3 --dry-run=client -o yaml > blue.yaml
```

Edit `blue.yaml` to add affinity under `template.spec`:

```yaml
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: color
                operator: In
                values:
                - blue
      containers:
      - name: nginx
        image: nginx
```

```bash
kubectl apply -f blue.yaml

kubectl get pods -o wide
```

All 3 pods should be on node01 (the node with `color=blue`).

**Exercise 3: Schedule on control plane using Exists operator**

The control plane node has the label `node-role.kubernetes.io/control-plane` (exists without a value). Use the `Exists` operator:

```bash
kubectl create deployment red --image=nginx --replicas=2 --dry-run=client -o yaml > red.yaml
```

Edit `red.yaml`:

```yaml
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: node-role.kubernetes.io/control-plane
                operator: Exists
      containers:
      - name: nginx
        image: nginx
```

```bash
kubectl apply -f red.yaml

kubectl get pods -o wide | grep red
```

```
red-7d4b8c6f9-abc12   1/1   Running   0   10s   10.244.0.5   controlplane   <none>
red-7d4b8c6f9-def34   1/1   Running   0   10s   10.244.0.6   controlplane   <none>
```

Both pods are on the control plane node.

### Taints and Tolerations vs Node Affinity

Each mechanism solves part of the pod placement problem, but neither is sufficient alone. Understanding their limitations is key to achieving exclusive node usage.

**Scenario:** 3 nodes (blue, red, green) and 3 pods (blue, red, green). Goal: each pod runs only on its matching node, and no other pods run on those nodes.

**Approach 1 — Taints and tolerations only:**

Taint each node with its color and add matching tolerations to each pod.

- Blue pod tolerates the blue taint → can schedule on the blue node ✅
- Red pod tolerates the red taint → can schedule on the red node ✅
- Green pod tolerates the green taint → can schedule on the green node ✅

**Limitation:** Tolerations allow a pod to schedule on a tainted node, but they don't *require* it. The red pod might still end up on an untainted node (e.g., a fourth "other" node) instead of the red node. Taints repel — they don't attract.

**Approach 2 — Node affinity only:**

Label each node with its color and add node affinity rules to each pod.

- Blue pod has affinity for `color=blue` → schedules on the blue node ✅
- Red pod has affinity for `color=red` → schedules on the red node ✅
- Green pod has affinity for `color=green` → schedules on the green node ✅

**Limitation:** Node affinity ensures the pod goes to the right node, but it doesn't prevent *other* pods from also scheduling there. An unrelated pod (e.g., Pod X with no affinity rules) could still land on the blue node.

**Approach 3 — Combine both (the correct solution):**

1. **Taint** each node → repels all pods that don't belong
2. **Toleration** on each pod → allows it past the taint
3. **Node affinity** on each pod → ensures it goes to the correct node

```bash
# Step 1: Taint nodes
kubectl taint nodes node-blue color=blue:NoSchedule
kubectl taint nodes node-red color=red:NoSchedule
kubectl taint nodes node-green color=green:NoSchedule

# Step 2: Label nodes
kubectl label nodes node-blue color=blue
kubectl label nodes node-red color=red
kubectl label nodes node-green color=green
```

```yaml
# blue-pod.yaml — toleration + node affinity
apiVersion: v1
kind: Pod
metadata:
  name: blue-pod
spec:
  tolerations:
  - key: "color"
    operator: "Equal"
    value: "blue"
    effect: "NoSchedule"
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: color
            operator: In
            values:
            - blue
  containers:
  - name: blue-app
    image: nginx
```

Result:
- Blue pod → goes to blue node (affinity) and is allowed (toleration) ✅
- Other pods → repelled from blue node (taint) ✅
- Blue pod → cannot go elsewhere (affinity requires blue node) ✅

This combined approach is essential in **multi-tenant clusters** where teams need dedicated nodes — taint the nodes to keep others out, and use affinity to ensure the right pods land on the right nodes.

### Pod Affinity & Anti-Affinity

Control pod placement relative to other pods.

```yaml
# pod-affinity.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-frontend
  template:
    metadata:
      labels:
        app: web-frontend
    spec:
      affinity:
        # Schedule NEAR cache pods (same node/zone)
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - redis-cache
            topologyKey: topology.kubernetes.io/zone

        # Schedule AWAY from other frontend pods (spread across nodes)
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-frontend
              topologyKey: kubernetes.io/hostname

      containers:
      - name: frontend
        image: nginx:1.25
```

**Pod affinity step-by-step example:**

`podAffinity` schedules pods on the same node as pods matching the expression. The `topologyKey` determines the scope (hostname = same node, zone = same AZ).

```yaml
# parent-pod.yaml — the pod that others will be attracted to
apiVersion: v1
kind: Pod
metadata:
  name: parent-pod-webapp
  labels:
    myname: parent
spec:
  containers:
  - name: parentpodwebapp
    image: nginx
```

```yaml
# pod-affinity-deploy.yaml — schedules on the same node as parent-pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pod-affinity
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-controller
  template:
    metadata:
      labels:
        app: nginx-controller
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
      affinity:
        podAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: myname
                operator: In
                values:
                - parent
            topologyKey: "kubernetes.io/hostname"
```

```bash
kubectl apply -f parent-pod.yaml
kubectl apply -f pod-affinity-deploy.yaml

# Verify both pods are on the same node
kubectl get pods -o wide
```

**Pod anti-affinity example:**

`podAntiAffinity` keeps pods away from nodes running pods that match the expression.

```yaml
# pod-anti-affinity-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pod-anti-affinity
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-controller
  template:
    metadata:
      labels:
        app: nginx-controller
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: myname
                operator: In
                values:
                - parent
            topologyKey: "kubernetes.io/hostname"
```

```bash
# If parent-pod is on node1, this deployment's pods will schedule on other nodes
kubectl apply -f pod-anti-affinity-deploy.yaml
kubectl get pods -o wide
```

### Topology Spread Constraints

Evenly distribute pods across zones/nodes.

```yaml
# topology-spread.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: balanced-app
spec:
  replicas: 6
  selector:
    matchLabels:
      app: balanced-app
  template:
    metadata:
      labels:
        app: balanced-app
    spec:
      topologySpreadConstraints:
      - maxSkew: 1                              # Max difference between zones
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: balanced-app
      containers:
      - name: app
        image: nginx:1.25
```

```bash
# Result: 2 pods per AZ (evenly spread)
kubectl get pods -l app=balanced-app -o wide

# Output:
# NAME                  NODE                          ZONE
# balanced-app-abc12    ip-10-0-1-100 (us-east-1a)    us-east-1a
# balanced-app-def34    ip-10-0-1-101 (us-east-1a)    us-east-1a
# balanced-app-ghi56    ip-10-0-2-200 (us-east-1b)    us-east-1b
# balanced-app-jkl78    ip-10-0-2-201 (us-east-1b)    us-east-1b
# balanced-app-mno90    ip-10-0-3-300 (us-east-1c)    us-east-1c
# balanced-app-pqr12    ip-10-0-3-301 (us-east-1c)    us-east-1c
```

### Scheduler Internals: Phases & Plugins

Understanding how the scheduler works internally helps when debugging scheduling issues or customizing behavior.

**The four scheduling phases:**

When a pod needs scheduling, it moves through four phases in order:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. QUEUE    │ →  │  2. FILTER   │ →  │  3. SCORE    │ →  │  4. BIND     │
│              │    │              │    │              │    │              │
│ Sort pods by │    │ Remove nodes │    │ Rank remain- │    │ Assign pod   │
│ priority     │    │ that can't   │    │ ing nodes    │    │ to highest-  │
│              │    │ run the pod  │    │              │    │ scoring node │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

**Step-by-step example:**

A pod requests 10 CPUs. The cluster has 4 nodes:

| Phase | Action | Result |
|-------|--------|--------|
| **Queue** | Pod enters scheduling queue, sorted by PriorityClass value | High-priority pods scheduled first |
| **Filter** | Nodes with < 10 available CPUs are removed | Node-1 (2 CPU) and Node-4 (4 CPU) eliminated |
| **Score** | Remaining nodes scored by available resources after reservation | Node-2 (16 CPU, score: 6) beats Node-3 (12 CPU, score: 2) |
| **Bind** | Pod assigned to highest-scoring node | Pod → Node-2 |

**Scheduler plugins at each phase:**

| Phase | Plugin | What It Does |
|-------|--------|-------------|
| Queue | `PrioritySort` | Sorts pods by PriorityClass value (higher value = scheduled first) |
| Filter | `NodeResourcesFit` | Removes nodes that lack sufficient CPU/memory |
| Filter | `NodeName` | If pod specifies `nodeName`, filters to only that node |
| Filter | `NodeUnschedulable` | Removes nodes marked unschedulable (cordoned/drained) |
| Filter | `TaintToleration` | Removes nodes with taints the pod doesn't tolerate |
| Score | `NodeResourcesFit` | Prefers nodes with more resources remaining after scheduling |
| Score | `ImageLocality` | Prefers nodes that already have the container image cached |
| Score | `TaintToleration` | Prefers nodes with fewer taints |
| Bind | `DefaultBinder` | Writes the binding (pod → node assignment) to the API server |

**Checking why a pod isn't scheduling:**

```bash
# See scheduler events for a pod
kubectl describe pod <pod-name> | grep -A5 Events

# Output when no nodes pass the filter phase:
# Events:
#   Type     Reason            Age   From               Message
#   ----     ------            ----  ----               -------
#   Warning  FailedScheduling  10s   default-scheduler  0/3 nodes are available:
#            1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
#            2 Insufficient cpu
```

**Extension points:**

Each phase has extension points where plugins can hook in:

```
Scheduling Queue    Filtering              Scoring              Binding
     │                 │                      │                    │
  queueSort      preFilter → filter     preScore → score      preBind → bind → postBind
```

This is how Kubernetes achieves extensibility — you can write custom plugins that hook into any extension point without modifying the scheduler itself.

### Multiple Schedulers (Deploying a Custom Scheduler)

Kubernetes supports running multiple schedulers simultaneously. You can deploy a custom scheduler alongside the default one and assign specific pods to it.

**Why use a custom scheduler?**
- Application needs custom placement logic (e.g., GPU-aware, data-locality-aware)
- Extra verification before pod placement
- Different scheduling algorithms for different workload types

Every custom scheduler must have a **unique name**. The default scheduler is named `default-scheduler`.

#### Deploying a Custom Scheduler as a Pod

The simplest approach — run the kube-scheduler binary with a custom config:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-custom-scheduler
  namespace: kube-system
spec:
  containers:
  - name: kube-scheduler
    image: registry.k8s.io/kube-scheduler:v1.30.0
    command:
    - kube-scheduler
    - --address=127.0.0.1
    - --kubeconfig=/etc/kubernetes/scheduler.conf
    - --config=/etc/kubernetes/my-scheduler-config.yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler.conf
      name: kubeconfig
    - mountPath: /etc/kubernetes/my-scheduler-config.yaml
      name: scheduler-config
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler.conf
    name: kubeconfig
  - hostPath:
      path: /etc/kubernetes/my-scheduler-config.yaml
    name: scheduler-config
```

```yaml
# /etc/kubernetes/my-scheduler-config.yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: my-custom-scheduler
leaderElection:
  leaderElect: false              # Disable if running a single instance
```

#### Deploying a Custom Scheduler as a Deployment (Production)

For production, deploy as a Deployment with proper RBAC:

**Step 1: ServiceAccount and RBAC**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-scheduler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: my-scheduler-as-kube-scheduler
subjects:
- kind: ServiceAccount
  name: my-scheduler
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: system:kube-scheduler
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: my-scheduler-as-volume-scheduler
subjects:
- kind: ServiceAccount
  name: my-scheduler
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: system:volume-scheduler
  apiGroup: rbac.authorization.k8s.io
```

**Step 2: ConfigMap for scheduler configuration**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-scheduler-config
  namespace: kube-system
data:
  my-scheduler-config.yaml: |
    apiVersion: kubescheduler.config.k8s.io/v1
    kind: KubeSchedulerConfiguration
    profiles:
    - schedulerName: my-scheduler
    leaderElection:
      leaderElect: false
```

**Step 3: Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-scheduler
  namespace: kube-system
  labels:
    component: scheduler
    tier: control-plane
spec:
  replicas: 1
  selector:
    matchLabels:
      component: my-scheduler
  template:
    metadata:
      labels:
        component: my-scheduler
    spec:
      serviceAccountName: my-scheduler
      containers:
      - name: kube-scheduler
        image: registry.k8s.io/kube-scheduler:v1.30.0
        command:
        - /usr/local/bin/kube-scheduler
        - --config=/etc/kubernetes/my-scheduler/my-scheduler-config.yaml
        livenessProbe:
          httpGet:
            path: /healthz
            port: 10259
            scheme: HTTPS
          initialDelaySeconds: 15
        readinessProbe:
          httpGet:
            path: /healthz
            port: 10259
            scheme: HTTPS
        volumeMounts:
        - name: config-volume
          mountPath: /etc/kubernetes/my-scheduler
      volumes:
      - name: config-volume
        configMap:
          name: my-scheduler-config
```

#### Using a Custom Scheduler in a Pod

Add `schedulerName` to the pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  schedulerName: my-custom-scheduler    # Use the custom scheduler
  containers:
  - name: nginx
    image: nginx
```

```bash
kubectl apply -f nginx-custom-scheduler.yaml
```

If the custom scheduler is misconfigured or not running, the pod stays in `Pending` state.

#### Verifying Which Scheduler Was Used

```bash
kubectl get events -o wide | grep Scheduled
```

```
LAST SEEN   COUNT   NAME        KIND   TYPE    REASON      SOURCE                  MESSAGE
9s          1       nginx.15    Pod    Normal  Scheduled   my-custom-scheduler     Successfully assigned default/nginx to node01
```

The `SOURCE` column shows which scheduler assigned the pod.

```bash
# View scheduler logs
kubectl logs my-custom-scheduler -n kube-system
```

```
I0204 09:42:25.819338   1 server.go:126] Version: v1.30.0
I0204 09:45:14.725407   1 controller_utils.go:1025] Waiting for caches to sync for scheduler controller
I0204 09:45:14.825634   1 controller_utils.go:1032] Caches are synced for scheduler controller
I0204 09:45:14.825814   1 leaderelection.go:185] attempting to acquire leader lease kube-system/my-custom-scheduler...
I0204 09:45:14.834953   1 leaderelection.go:194] successfully acquired lease kube-system/my-custom-scheduler
```

**Leader election:** In HA setups with multiple scheduler replicas, leader election ensures only one instance actively schedules pods. Set `leaderElect: true` and provide a unique `resourceName` per scheduler.

#### Lab: Deploying a Custom Scheduler Step-by-Step

**Step 1: Find the default scheduler image**

```bash
kubectl describe pod kube-scheduler-controlplane -n kube-system | grep Image
```

```
Image:         registry.k8s.io/kube-scheduler:v1.30.0
```

Use this same image for your custom scheduler.

**Step 2: Verify the ServiceAccount exists**

```bash
kubectl get sa my-scheduler -n kube-system
```

```
NAME           SECRETS   AGE
my-scheduler   1         26s
```

**Step 3: Create a ConfigMap from the scheduler config file**

```bash
# Create the config file
cat > /root/my-scheduler-config.yaml <<EOF
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: my-scheduler
leaderElection:
  leaderElect: false
EOF

# Create ConfigMap from the file
kubectl create configmap my-scheduler-config \
  --from-file=/root/my-scheduler-config.yaml -n kube-system
```

```
configmap/my-scheduler-config created
```

```bash
kubectl get configmap my-scheduler-config -n kube-system
```

```
NAME                  DATA   AGE
my-scheduler-config   1      17s
```

**Step 4: Deploy the custom scheduler pod**

```yaml
# my-scheduler.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-scheduler
  namespace: kube-system
  labels:
    run: my-scheduler
spec:
  serviceAccountName: my-scheduler
  hostNetwork: false
  hostPID: false
  containers:
  - name: kube-second-scheduler
    image: registry.k8s.io/kube-scheduler:v1.30.0
    command:
    - /usr/local/bin/kube-scheduler
    - --config=/etc/kubernetes/my-scheduler/my-scheduler-config.yaml
    livenessProbe:
      httpGet:
        path: /healthz
        port: 10259
        scheme: HTTPS
      initialDelaySeconds: 15
    readinessProbe:
      httpGet:
        path: /healthz
        port: 10259
        scheme: HTTPS
    resources:
      requests:
        cpu: "0.1"
    securityContext:
      privileged: false
    volumeMounts:
    - name: config-volume
      mountPath: /etc/kubernetes/my-scheduler
  volumes:
  - name: config-volume
    configMap:
      name: my-scheduler-config
```

```bash
kubectl apply -f my-scheduler.yaml

kubectl get pods -n kube-system | grep scheduler
```

```
kube-scheduler-controlplane   1/1     Running   0          11m
my-scheduler                  1/1     Running   0          7s
```

Both schedulers are now running side by side.

**Step 5: Schedule a pod using the custom scheduler**

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  schedulerName: my-scheduler
  containers:
  - name: nginx
    image: nginx
EOF
```

```bash
kubectl get pods
```

```
NAME    READY   STATUS    RESTARTS   AGE
nginx   1/1     Running   0          4s
```

### Scheduler Profiles (Recommended over Multiple Binaries)

By default, Kubernetes uses a single scheduler (`default-scheduler`). For specialized workloads, you might need different scheduling logic — for example, batch jobs that prioritize bin-packing vs web services that prioritize spreading.

**Before Kubernetes 1.18:** You had to run separate scheduler binaries (as shown above), each with its own configuration. This caused race conditions when multiple schedulers tried to claim the same node resources simultaneously.

**Kubernetes 1.18+:** A single scheduler binary supports **multiple profiles**. Each profile acts as an independent scheduler with its own name and plugin configuration, but they share a single process — eliminating race conditions. **Prefer profiles over separate binaries when possible.**

#### KubeSchedulerConfiguration

Scheduler profiles are defined in a `KubeSchedulerConfiguration` file:

```yaml
# scheduler-config.yaml — single profile (default behavior)
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: default-scheduler
```

```yaml
# multi-profile-scheduler.yaml — multiple profiles in one binary
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: default-scheduler
- schedulerName: batch-scheduler
- schedulerName: gpu-scheduler
```

#### Customizing Plugins Per Profile

Each profile can enable or disable specific plugins at any extension point:

```yaml
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
# Profile 1: Default scheduler (no changes)
- schedulerName: default-scheduler

# Profile 2: Batch scheduler — disable TaintToleration scoring, add custom plugins
- schedulerName: batch-scheduler
  plugins:
    score:
      disabled:
      - name: TaintToleration
      enabled:
      - name: MyBinPackingPlugin

# Profile 3: Minimal scheduler — disable all scoring (fastest scheduling)
- schedulerName: no-scoring-scheduler
  plugins:
    preScore:
      disabled:
      - name: '*'          # Wildcard: disable ALL preScore plugins
    score:
      disabled:
      - name: '*'          # Wildcard: disable ALL score plugins
```

**Using a specific scheduler profile in a pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: batch-job
spec:
  schedulerName: batch-scheduler    # Use the batch-scheduler profile
  containers:
  - name: worker
    image: batch-worker:latest
    resources:
      requests:
        cpu: "4"
        memory: "8Gi"
```

```bash
kubectl apply -f batch-job.yaml

# Verify which scheduler was used
kubectl get pod batch-job -o jsonpath='{.spec.schedulerName}'
```

```
batch-scheduler
```

If `schedulerName` is not specified, the pod uses `default-scheduler`.

#### Running the Scheduler with a Custom Config

```bash
# Start the scheduler with a custom configuration file
kube-scheduler --config=/etc/kubernetes/scheduler-config.yaml
```

For kubeadm clusters, the scheduler runs as a static pod. Edit `/etc/kubernetes/manifests/kube-scheduler.yaml` and mount the config file:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-scheduler
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-scheduler
    - --config=/etc/kubernetes/scheduler-config.yaml
    image: registry.k8s.io/kube-scheduler:v1.30.0
    name: kube-scheduler
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler-config.yaml
      name: scheduler-config
      readOnly: true
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler-config.yaml
      type: File
    name: scheduler-config
```

**Real-world use cases for scheduler profiles:**

| Profile | Use Case | Plugin Customization |
|---------|----------|---------------------|
| `default-scheduler` | General workloads | Default plugins, balanced scoring |
| `batch-scheduler` | Batch/ML jobs | Bin-packing scoring (pack nodes tightly to free others) |
| `gpu-scheduler` | GPU workloads | Custom GPU-aware scoring plugin |
| `no-scoring-scheduler` | High-throughput scheduling | All scoring disabled for fastest placement |

**Interview question: What are scheduler profiles and why were they introduced?**
Scheduler profiles allow running multiple scheduling configurations within a single `kube-scheduler` binary. Before Kubernetes 1.18, custom scheduling required running separate scheduler binaries, which caused race conditions when multiple schedulers competed for the same node resources. Profiles solve this by defining multiple named schedulers in one `KubeSchedulerConfiguration` file, each with its own plugin configuration. Pods select a profile via `spec.schedulerName`.

---

## 19.2 Pod Priority, Preemption & Disruption Budgets

These features control what happens when resources are scarce or nodes need maintenance.

**When to use each:**
- **PriorityClass** — ensure production pods get resources before dev/test pods
- **Preemption** — allow high-priority pods to evict lower-priority ones when resources are full
- **PDB** — prevent too many pods from being disrupted during node drains/upgrades

### Pod Priority & Preemption

Pods can have priority. When a high-priority pod cannot be scheduled due to insufficient resources, the scheduler can preempt (evict) lower-priority pods.

**How preemption works internally:**
1. High-priority pod is created but cannot be scheduled (no resources)
2. Scheduler identifies nodes where evicting lower-priority pods would free enough resources
3. Lower-priority pods are evicted (terminated with grace period)
4. High-priority pod is scheduled on the freed node

- PriorityClass is cluster-scoped (not namespaced)
- Default priority for pods without a PriorityClass is 0
- Higher value = higher priority
- User-defined values range from approximately **-2,147,483,648 to 1,000,000,000**
- Values above 1 billion are reserved for system-critical components

**Built-in system priority classes:**

```bash
kubectl get priorityclass
```

```
NAME                      VALUE          GLOBAL-DEFAULT   AGE     PREEMPTIONPOLICY
system-cluster-critical   2000000000     false            30d     PreemptLowerPriority
system-node-critical      2000010000     false            30d     PreemptLowerPriority
```

- `system-node-critical` — for pods that must run on every node (kubelet, kube-proxy)
- `system-cluster-critical` — for cluster-level components (API server, scheduler, controller manager)
- These use reserved values (>1B) that user-defined PriorityClasses cannot reach

**Creating custom priority classes:**

```yaml
# high-priority.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "For production-critical service pods."
```

```yaml
# low-priority.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 200000
globalDefault: false
description: "For non-critical service pods."
```

```bash
kubectl apply -f high-priority.yaml
kubectl apply -f low-priority.yaml
kubectl get pc
```

```
NAME                      VALUE          GLOBAL-DEFAULT   AGE
high-priority             1000000        false            10s
low-priority              200000         false            10s
system-cluster-critical   2000000000     false            30d
system-node-critical      2000010000     false            30d
```

**Setting a global default priority:**

To change the default priority for all pods that don't specify a `priorityClassName`, set `globalDefault: true`. Only one PriorityClass can be the global default:

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: default-priority
value: 100000
globalDefault: true           # All pods without priorityClassName get this value
description: "Default priority for all pods."
```

**Using PriorityClass in pods:**

```yaml
# app-low-priority.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app2
  labels:
    env: preprod
spec:
  containers:
  - name: app2
    image: nginx
    resources:
      requests:
        memory: "4Gi"
        cpu: "1"
      limits:
        memory: "4Gi"
        cpu: "2"
  priorityClassName: low-priority
```

```yaml
# app-high-priority.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app3
  labels:
    env: prod
spec:
  containers:
  - name: app3
    image: nginx
    resources:
      requests:
        memory: "4Gi"
        cpu: "2"
      limits:
        memory: "4Gi"
        cpu: "2"
  priorityClassName: high-priority
```

```bash
# When resources are exhausted, creating app3 (high-priority) will evict app2 (low-priority)
kubectl apply -f app-low-priority.yaml
kubectl apply -f app-high-priority.yaml
kubectl get pods --watch

kubectl describe pod app3 | grep -i priority
# Output: Priority: 1000000
```

**Preemption policy — prevent eviction:**

Setting `preemptionPolicy: Never` means the pod gets scheduling queue priority but cannot evict other pods:

```yaml
# high-priority-no-preempt.yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
preemptionPolicy: Never
globalDefault: false
description: "High priority but cannot preempt other pods."
```

### Pod Disruption Budgets (PDB)

PDBs limit the number of pods that can be down simultaneously during voluntary disruptions (node drains, upgrades, maintenance).

```yaml
# pdb.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pdb
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pdb
  template:
    metadata:
      labels:
        app: pdb
    spec:
      containers:
      - name: pdb
        image: nginx
        ports:
        - containerPort: 80
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: demo-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: pdb
```

```bash
kubectl apply -f pdb.yaml
kubectl get pdb

# Drain a node — PDB prevents eviction if it would violate minAvailable
kubectl drain --ignore-daemonsets <node-name>

# If drain is blocked, reduce minAvailable or use maxUnavailable instead
# kubectl edit pdb demo-pdb  → change minAvailable to 2

# Uncordon the node to make it schedulable again
kubectl uncordon <node-name>
```

**PDB vs PriorityClass:** PDB controls disruption during voluntary operations (drains, upgrades). PriorityClass controls scheduling order and preemption when resources are scarce.

---

