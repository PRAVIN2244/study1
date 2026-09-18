# MODULE 11: ReplicaSets & Deployments

---

## 11.1 ReplicaSets — Ensuring Pod Count

A ReplicaSet ensures a specified number of pod replicas are running at all times. It provides:
- **High availability** — if a pod crashes, the ReplicaSet creates a replacement
- **Load balancing** — multiple pods distribute traffic across the cluster
- **Scaling** — increase or decrease replicas to match demand

**How it works internally:**
1. The ReplicaSet controller watches the API server for pods matching its `selector`
2. It compares the actual count with the desired `replicas` count
3. If actual < desired → creates new pods using the `template`
4. If actual > desired → deletes excess pods

**Three required fields:**
- `replicas` — how many pods to maintain
- `selector` — which pods belong to this ReplicaSet (must match template labels)
- `template` — the pod spec used to create new pods

**Why is the template section required?** Even if pods with matching labels already exist in the cluster, the template is needed as a blueprint for creating replacement pods when existing ones fail. Without it, the ReplicaSet wouldn't know how to recreate pods.

**Why you rarely create ReplicaSets directly:** Deployments create and manage ReplicaSets for you, adding rolling updates and rollback capabilities. Use Deployments instead of bare ReplicaSets in production.

### ReplicationController vs ReplicaSet

The ReplicationController is the older technology, now replaced by ReplicaSet:

| Feature | ReplicationController | ReplicaSet |
|---|---|---|
| API version | `v1` | `apps/v1` |
| Selector | Implicit (matches template labels) | Explicit (`selector.matchLabels` required) |
| Set-based selectors | ❌ Not supported | ✅ Supported (`matchExpressions`) |
| Status | Deprecated | Current standard |

**ReplicationController example (for reference only — use ReplicaSet instead):**

```yaml
# rc-definition.yml — DEPRECATED, shown for exam reference
apiVersion: v1
kind: ReplicationController
metadata:
  name: myapp-rc
  labels:
    app: myapp
    type: front-end
spec:
  replicas: 3
  template:
    metadata:
      name: myapp-pod
      labels:
        app: myapp
        type: front-end
    spec:
      containers:
      - name: nginx-container
        image: nginx
```

```bash
kubectl create -f rc-definition.yml
# Output: replicationcontroller/myapp-rc created

kubectl get replicationcontroller
# NAME       DESIRED   CURRENT   READY   AGE
# myapp-rc   3         3         3       19s

kubectl get pods
# NAME             READY   STATUS    RESTARTS   AGE
# myapp-rc-4lvk9   1/1     Running   0          20s
# myapp-rc-mc2mf   1/1     Running   0          20s
# myapp-rc-px9pz   1/1     Running   0          20s
```

Notice the ReplicationController has no `selector` field — it implicitly uses the template's labels. The ReplicaSet requires an explicit `selector.matchLabels`.

### ReplicaSet Quick Reference

| Operation | Command |
|---|---|
| Create from file | `kubectl create -f replicaset.yaml` |
| List ReplicaSets | `kubectl get replicaset` or `kubectl get rs` |
| Describe | `kubectl describe rs <name>` |
| Delete (and its pods) | `kubectl delete rs <name>` |
| Scale imperatively | `kubectl scale rs <name> --replicas=<n>` |
| Scale declaratively | Edit YAML, then `kubectl replace -f <file>` |
| Edit live | `kubectl edit rs <name>` |

### ReplicaSet Troubleshooting — Common Errors

These are frequent errors encountered when working with ReplicaSets (and common CKA exam scenarios).

#### Error 1: Wrong API version

```bash
kubectl create -f replicaset-definition.yaml

# Error:
# error: unable to recognize "replicaset-definition.yaml":
# no matches for kind "ReplicaSet" in version "v1"
```

**Cause:** The YAML file uses `apiVersion: v1` instead of `apiVersion: apps/v1`.

**Fix:** Change `apiVersion: v1` to `apiVersion: apps/v1`. You can verify the correct API version with:

```bash
kubectl explain replicaset

# Output:
# KIND:     ReplicaSet
# VERSION:  apps/v1
# ...
```

#### Error 2: Selector does not match template labels

```bash
kubectl create -f replicaset-definition-2.yaml

# Error:
# The ReplicaSet "replicaset-2" is invalid:
# spec.template.metadata.labels: Invalid value:
# map[string]string{"tier":"nginx"}: selector does not match template labels
```

**Cause:** The `spec.selector.matchLabels` and `spec.template.metadata.labels` don't match.

**Fix:** Ensure both sections use identical labels:

```yaml
spec:
  selector:
    matchLabels:
      tier: nginx        # ← These must match
  template:
    metadata:
      labels:
        tier: nginx      # ← These must match
```

#### Error 3: Pods stuck in ImagePullBackOff (wrong image)

```bash
kubectl get rs
# NAME              DESIRED   CURRENT   READY   AGE
# new-replica-set   4         4         0       9s    ← 0 READY

kubectl get pods
# NAME                      READY   STATUS             RESTARTS   AGE
# new-replica-set-7r2qw     0/1     ImagePullBackOff   0          2m
# new-replica-set-wkzjh     0/1     ImagePullBackOff   0          2m
# new-replica-set-tn2mp     0/1     ImagePullBackOff   0          2m
# new-replica-set-vpkh8     0/1     ImagePullBackOff   0          2m

kubectl describe pod new-replica-set-7r2qw
# Events:
#   Warning  Failed  kubelet  Failed to pull image "busybox777":
#   pull access denied, repository does not exist
```

**Fix:** Edit the ReplicaSet to correct the image, then delete existing pods so the RS recreates them:

```bash
# Step 1: Edit the ReplicaSet image
kubectl edit rs new-replica-set
# Change image: busybox777 → image: busybox
# Save and exit

# Step 2: Delete existing pods (editing RS does NOT update running pods)
kubectl delete pod new-replica-set-7r2qw new-replica-set-wkzjh new-replica-set-tn2mp new-replica-set-vpkh8

# Step 3: Verify — new pods are created with the correct image
kubectl get pods
# NAME                      READY   STATUS    RESTARTS   AGE
# new-replica-set-abc12     1/1     Running   0          5s
# new-replica-set-def34     1/1     Running   0          5s
# new-replica-set-ghi56     1/1     Running   0          5s
# new-replica-set-hij78     1/1     Running   0          5s
```

> **Key gotcha:** Editing a ReplicaSet (`kubectl edit rs`) updates the template for **future** pods only. Existing pods continue running with the old configuration. You must delete the old pods to trigger recreation with the updated template.

```yaml
# replicaset.yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-replicaset
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx          # Must match pod template labels
  template:
    metadata:
      labels:
        app: nginx        # Must match selector
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
```

```bash
kubectl apply -f replicaset.yaml

# Output:
# replicaset.apps/nginx-replicaset created

kubectl get replicaset

# Output:
# NAME               DESIRED   CURRENT   READY   AGE
# nginx-replicaset   3         3         3       30s

kubectl get pods

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# nginx-replicaset-abc12   1/1     Running   0          30s
# nginx-replicaset-def34   1/1     Running   0          30s
# nginx-replicaset-ghi56   1/1     Running   0          30s

# Self-healing: Delete a pod and watch it recreate
kubectl delete pod nginx-replicaset-abc12

kubectl get pods

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# nginx-replicaset-def34   1/1     Running   0          2m
# nginx-replicaset-ghi56   1/1     Running   0          2m
# nginx-replicaset-xyz99   1/1     Running   0          5s   ← New pod!

# Scale the ReplicaSet
kubectl scale replicaset nginx-replicaset --replicas=5

# Output:
# replicaset.apps/nginx-replicaset scaled
```

### ReplicaSet Detailed Walkthrough

**ReplicaSet YAML:**

```yaml
# replicaset-demo.yml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: my-helloworld-rs
  labels:
    app: my-helloworld
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-helloworld
  template:
    metadata:
      labels:
        app: my-helloworld
    spec:
      containers:
      - name: my-helloworld-app
        image: stacksimplify/kube-helloworld:1.0.0
```

**Step 1: Create the ReplicaSet**

```bash
kubectl create -f replicaset-demo.yml
# Output: replicaset.apps/my-helloworld-rs created
```

**Step 2: Verify ReplicaSet**

```bash
kubectl get rs
# NAME               DESIRED   CURRENT   READY   AGE
# my-helloworld-rs   3         3         3       10s
```

| Column | Meaning |
|---|---|
| `DESIRED` | Number of replicas specified in YAML (`replicas: 3`) |
| `CURRENT` | Number of pods currently running |
| `READY` | Number of pods ready to serve traffic |
| `AGE` | How long ago the ReplicaSet was created |

**Step 3: Describe ReplicaSet**

```bash
kubectl describe rs my-helloworld-rs

# Output:
# Name:         my-helloworld-rs
# Namespace:    default
# Selector:     app=my-helloworld
# Labels:       app=my-helloworld
# Replicas:     3 desired | 3 current
# Pods Status:  3 Running / 0 Failed
# Pod Template:
#   Labels:  app=my-helloworld
#   Containers:
#    my-helloworld-app:
#     Image:  stacksimplify/kube-helloworld:1.0.0
# Events:
#   Type    Reason            Age   From                   Message
#   Normal  SuccessfulCreate  10s   replicaset-controller  Created pod: my-helloworld-rs-xyz123
#   Normal  SuccessfulCreate  10s   replicaset-controller  Created pod: my-helloworld-rs-abc456
#   Normal  SuccessfulCreate  10s   replicaset-controller  Created pod: my-helloworld-rs-def789
```

**Step 4: Get pods with node and IP details**

```bash
kubectl get pods -o wide
# NAME                       READY   STATUS    RESTARTS   AGE   IP           NODE
# my-helloworld-rs-xyz123    1/1     Running   0          30s   10.244.1.10  worker-node1
# my-helloworld-rs-abc456    1/1     Running   0          30s   10.244.1.11  worker-node2
# my-helloworld-rs-def789    1/1     Running   0          30s   10.244.1.12  worker-node3
```

Pod names follow the pattern `<replicaset-name>-<random-string>`.

**Step 5: Verify pod ownership**

Check the `ownerReferences` field to confirm which ReplicaSet owns a pod:

```bash
kubectl get pods my-helloworld-rs-xyz123 -o yaml | grep ownerReferences -A 5

# ownerReferences:
# - apiVersion: apps/v1
#   kind: ReplicaSet
#   name: my-helloworld-rs
#   uid: 1234abcd-5678-efgh-9101-ijklmnopqrstu
#   controller: true
```

This confirms the pod belongs to the `my-helloworld-rs` ReplicaSet. If you delete the ReplicaSet, all owned pods are deleted too.

**Step 6: Expose ReplicaSet as a NodePort Service**

```bash
kubectl expose rs my-helloworld-rs --type=NodePort --port=80 --target-port=8080 --name=my-helloworld-rs-service
# Output: service/my-helloworld-rs-service exposed

kubectl get svc
# NAME                       TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# my-helloworld-rs-service   NodePort   10.100.200.1   <none>        80:31567/TCP   30s
```

**Port mapping flow:**

```
User → http://<node-ip>:31567 → NodePort (31567) → Service port (80) → Pod port (8080)
```

| Port | What It Is |
|---|---|
| `31567` | NodePort — externally accessible on every worker node |
| `80` | Service port — internal cluster port |
| `8080` | Target port — the container port where the app listens |

**Step 7: Access the application**

```bash
# Get worker node public IP
kubectl get nodes -o wide
# NAME           STATUS   ROLES    AGE   VERSION   INTERNAL-IP     EXTERNAL-IP
# worker-node1   Ready    <none>   1d    v1.24.0   192.168.1.100   34.201.12.45

# Access the application
# http://34.201.12.45:31567/hello
```

**Step 8: Test ReplicaSet self-healing (reliability)**

Delete a pod and watch the ReplicaSet automatically create a replacement:

```bash
# Get current pods
kubectl get pods

# Delete one pod
kubectl delete pod my-helloworld-rs-xyz123
# Output: pod "my-helloworld-rs-xyz123" deleted

# Verify — a new pod is created automatically to maintain 3 replicas
kubectl get pods
# NAME                       READY   STATUS    RESTARTS   AGE
# my-helloworld-rs-abc456    1/1     Running   0          5m    ← existing
# my-helloworld-rs-def789    1/1     Running   0          5m    ← existing
# my-helloworld-rs-new123    1/1     Running   0          5s    ← new (notice AGE)
```

The new pod has a different name and a younger AGE — the ReplicaSet controller detected the pod count dropped below the desired 3 and created a replacement.

**Step 9: Test ReplicaSet scalability**

**Method 1: Scale imperatively with `kubectl scale`**

```bash
# Scale up to 6 replicas
kubectl scale rs my-helloworld-rs --replicas=6
# Output: replicaset.apps/my-helloworld-rs scaled

# Verify — 6 pods running
kubectl get pods
```

**Method 2: Scale declaratively by editing the YAML**

Update `replicas` in `replicaset-demo.yml`:

```yaml
# Before
spec:
  replicas: 3

# After
spec:
  replicas: 6
```

Apply the change:

```bash
kubectl replace -f replicaset-demo.yml
# Output: replicaset.apps/my-helloworld-rs replaced

# Verify
kubectl get pods -o wide
```

`kubectl replace` updates the existing resource with the new YAML definition. Unlike `kubectl apply`, it requires the resource to already exist.

**Step 10: Delete ReplicaSet and Service**

```bash
# Delete ReplicaSet (also deletes all owned pods)
kubectl delete rs my-helloworld-rs
# or
kubectl delete rs/my-helloworld-rs

# Verify
kubectl get rs

# Delete the Service
kubectl delete svc my-helloworld-rs-service
# or
kubectl delete svc/my-helloworld-rs-service

# Verify
kubectl get svc
```

**Labels & Selectors note:** The ReplicaSet uses `selector.matchLabels` to find which pods it owns. The labels in `template.metadata.labels` must match the selector. This is how the ReplicaSet knows which pods to count toward the desired replica count.

### ReplicaSet with YAML — Declarative Example

**ReplicaSet manifest:**

```yaml
# replicaset-definition.yml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: myapp2-rs
spec:
  replicas: 3                    # Ensures 3 pods running at all times
  selector:
    matchLabels:
      app: myapp2                # Selects pods with this label
  template:                      # Pod template used to create replicas
    metadata:
      name: myapp2-pod
      labels:
        app: myapp2              # Must match selector.matchLabels
    spec:
      containers:
      - name: myapp2
        image: stacksimplify/kubenginx:2.0.0
        ports:
          - containerPort: 80
```

**NodePort Service manifest:**

```yaml
# replicaset-nodeport-service.yml
apiVersion: v1
kind: Service
metadata:
  name: replicaset-nodeport-service
spec:
  type: NodePort
  selector:
    app: myapp2                  # Matches pods from the ReplicaSet
  ports:
    - name: http
      port: 80                   # Internal cluster service port
      targetPort: 80             # Container port
      nodePort: 31232            # External access port
```

**Deploy and verify:**

```bash
# Apply ReplicaSet
kubectl apply -f replicaset-definition.yml

# Verify ReplicaSet
kubectl get rs
# NAME        DESIRED   CURRENT   READY   AGE
# myapp2-rs   3         3         3       10s

# Verify pods
kubectl get pods
# NAME               READY   STATUS    RESTARTS   AGE
# myapp2-rs-xyz123   1/1     Running   0          5s
# myapp2-rs-abc456   1/1     Running   0          5s
# myapp2-rs-pqr789   1/1     Running   0          5s

# Test self-healing — delete a pod
kubectl delete pod myapp2-rs-xyz123
kubectl get pods
# A new pod with a different name is created to maintain 3 replicas

# Apply NodePort Service
kubectl apply -f replicaset-nodeport-service.yml

# Verify service
kubectl get svc
# NAME                          TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# replicaset-nodeport-service   NodePort   10.104.56.89   <none>        80:31232/TCP   10s

# Get worker node public IP
kubectl get nodes -o wide

# Access the application
# http://<node-public-ip>:31232
# curl http://<node-public-ip>:31232
```

**Clean up:**

```bash
kubectl delete rs myapp2-rs
kubectl delete svc replicaset-nodeport-service
```

⚠️ **In practice, you rarely create ReplicaSets directly. Use Deployments instead — they manage ReplicaSets for you and add rolling update capabilities.**

---


## 11.2 Deployments — The Standard Workload

A Deployment manages ReplicaSets and provides declarative updates, rollbacks, and scaling. It is the most commonly used workload type for stateless applications.

```
Deployment
  └── ReplicaSet (managed automatically)
       ├── Pod 1
       ├── Pod 2
       └── Pod 3
```

**What Deployments add over ReplicaSets:**
- **Rolling updates** — gradually replace old pods with new ones (zero downtime)
- **Rollbacks** — revert to a previous version if something goes wrong
- **Revision history** — keeps track of previous ReplicaSets for rollback
- **Pause/Resume** — pause a rollout for canary-style testing

**How rolling updates work internally:**
1. You update the image version (e.g., `nginx:1.24` → `nginx:1.25`)
2. Deployment creates a new ReplicaSet with the new image
3. New ReplicaSet scales up while old ReplicaSet scales down (controlled by `maxSurge` and `maxUnavailable`)
4. Once all new pods are ready, old ReplicaSet is scaled to 0 (but kept for rollback)

**Production note:** Always set `readinessProbe` on Deployment pods. Without it, Kubernetes considers a pod "ready" as soon as the container starts, which can route traffic to pods that haven't finished initializing.

### Creating a Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
  labels:
    app: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1            # Max extra pods during update
      maxUnavailable: 0      # Zero downtime
  template:
    metadata:
      labels:
        app: webapp
        version: v1
    spec:
      containers:
      - name: webapp
        image: nginx:1.24
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "250m"
            memory: "256Mi"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
```

```bash
kubectl apply -f deployment.yaml

# Output:
# deployment.apps/webapp created

kubectl get deployment webapp

# Output:
# NAME     READY   UP-TO-DATE   AVAILABLE   AGE
# webapp   3/3     3            3           45s

# See the ReplicaSet created by the Deployment
kubectl get replicaset

# Output:
# NAME                DESIRED   CURRENT   READY   AGE
# webapp-7bf8c77b5b   3         3         3       45s

# See all related resources
kubectl get all -l app=webapp

# Output:
# NAME                          READY   STATUS    RESTARTS   AGE
# pod/webapp-7bf8c77b5b-abc12   1/1     Running   0          45s
# pod/webapp-7bf8c77b5b-def34   1/1     Running   0          45s
# pod/webapp-7bf8c77b5b-ghi56   1/1     Running   0          45s
#
# NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
# deployment.apps/webapp   3/3     3            3           45s
#
# NAME                                DESIRED   CURRENT   READY   AGE
# replicaset.apps/webapp-7bf8c77b5b   3         3         3       45s
```

### Rolling Updates

```bash
# Update the image version
kubectl set image deployment/webapp webapp=nginx:1.25

# Output:
# deployment.apps/webapp image updated

# Watch the rolling update
kubectl rollout status deployment/webapp

# Output:
# Waiting for deployment "webapp" rollout to finish: 1 out of 3 new replicas have been updated...
# Waiting for deployment "webapp" rollout to finish: 2 out of 3 new replicas have been updated...
# Waiting for deployment "webapp" rollout to finish: 3 out of 3 new replicas have been updated...
# Waiting for deployment "webapp" rollout to finish: 1 old replicas are pending termination...
# deployment "webapp" successfully rolled out

# See both ReplicaSets (old scaled to 0, new scaled to 3)
kubectl get replicaset

# Output:
# NAME                DESIRED   CURRENT   READY   AGE
# webapp-7bf8c77b5b   0         0         0       5m    ← Old (nginx:1.24)
# webapp-5d9f8c6a2e   3         3         3       30s   ← New (nginx:1.25)
```

### Rollbacks

```bash
# View rollout history
kubectl rollout history deployment/webapp

# Output:
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

# See details of a specific revision
kubectl rollout history deployment/webapp --revision=1

# Rollback to previous version
kubectl rollout undo deployment/webapp

# Output:
# deployment.apps/webapp rolled back

# Rollback to a specific revision
kubectl rollout undo deployment/webapp --to-revision=1

# Pause and resume rollouts (for canary-style updates)
kubectl rollout pause deployment/webapp
# ... make changes ...
kubectl rollout resume deployment/webapp
```

### Deployment Strategies

#### 1. RollingUpdate (Default)
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%          # 25% extra pods allowed
    maxUnavailable: 25%    # 25% can be unavailable
```

#### 2. Recreate (All at once — causes downtime)
```yaml
strategy:
  type: Recreate
  # All old pods killed before new ones created
```

**Viewing strategy events with `kubectl describe`:**

The events section of `kubectl describe deployment` shows the difference between strategies:

Recreate strategy — old ReplicaSet scaled to 0 first, then new ReplicaSet scaled up:

```bash
kubectl describe deployment myapp-deployment
```

```
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  11m   deployment-controller  Scaled up replica set myapp-deployment-6795844b58 to 5
  Normal  ScalingReplicaSet  11m   deployment-controller  Scaled down replica set myapp-deployment-6795844b58 to 0
  Normal  ScalingReplicaSet  56s   deployment-controller  Scaled up replica set myapp-deployment-54c7d6ccc to 5
```

RollingUpdate strategy — gradual scale-down of old and scale-up of new:

```
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  1m    deployment-controller  Scaled up replica set myapp-deployment-67c749c58c to 5
  Normal  ScalingReplicaSet  1m    deployment-controller  Scaled up replica set myapp-deployment-75d7bdbd8d to 2
  Normal  ScalingReplicaSet  1m    deployment-controller  Scaled down replica set myapp-deployment-67c749c58c to 4
  Normal  ScalingReplicaSet  1m    deployment-controller  Scaled up replica set myapp-deployment-75d7bdbd8d to 3
  Normal  ScalingReplicaSet  0s    deployment-controller  Scaled down replica set myapp-deployment-67c749c58c to 0
```

**Quick reference — deployment commands:**

| Action | Command |
|--------|---------|
| Create | `kubectl create -f deployment-definition.yml` |
| List | `kubectl get deployments` |
| Update (declarative) | `kubectl apply -f deployment-definition.yml` |
| Update image | `kubectl set image deployment/myapp nginx=nginx:1.9.1` |
| Rollout status | `kubectl rollout status deployment/myapp` |
| Rollout history | `kubectl rollout history deployment/myapp` |
| Rollback | `kubectl rollout undo deployment/myapp` |

**Lab: Rolling Updates and Strategy Changes**

**Step 1: Deploy and verify the application**

```bash
kubectl get deploy
```

```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
frontend   4/4     4            4           55s
```

```bash
kubectl describe deploy frontend | grep -E "Image:|StrategyType:|RollingUpdateStrategy:"
```

```
    Image:              kodekloud/webapp-color:v1
StrategyType:           RollingUpdate
RollingUpdateStrategy:  25% max unavailable, 25% max surge
```

Application is running v1 (blue) with RollingUpdate strategy.

**Step 2: Rolling update from v1 to v2**

```bash
kubectl set image deploy frontend simple-webapp=kodekloud/webapp-color:v2
```

During the update, responses show a mix of old and new versions:

```
Hello, Application Version: v1 ; Color: blue OK
Hello, Application Version: v1 ; Color: blue OK
Hello, Application Version: v2 ; Color: green OK
Hello, Application Version: v1 ; Color: blue OK
Hello, Application Version: v2 ; Color: green OK
Hello, Application Version: v2 ; Color: green OK
```

This is the rolling update in action — pods are replaced one at a time (25% max unavailable). No downtime, but mixed responses during transition. Once complete, all responses show v2 green.

**Step 3: Change strategy to Recreate**

```bash
kubectl edit deployment frontend
```

Change the strategy section:

```yaml
# Before
strategy:
  rollingUpdate:
    maxSurge: 25%
    maxUnavailable: 25%
  type: RollingUpdate

# After
strategy:
  type: Recreate
```

```bash
kubectl describe deploy frontend | grep StrategyType
```

```
StrategyType:           Recreate
```

**Step 4: Upgrade with Recreate strategy — observe downtime**

```bash
kubectl set image deploy frontend simple-webapp=kodekloud/webapp-color:v3
```

During the upgrade, all pods are terminated before new ones are created:

```
Failed
Failed
Failed
Failed
Failed
```

After the new pods start:

```
Hello, Application Version: v3 ; Color: red OK
Hello, Application Version: v3 ; Color: red OK
Hello, Application Version: v3 ; Color: red OK
```

This demonstrates the key difference: RollingUpdate has zero downtime but mixed responses; Recreate has downtime but no mixed versions.

### Scaling

```bash
# Manual scaling
kubectl scale deployment webapp --replicas=5

# Output:
# deployment.apps/webapp scaled

# Autoscaling (HPA - Horizontal Pod Autoscaler)
kubectl autoscale deployment webapp --min=3 --max=10 --cpu-percent=70

# Output:
# horizontalpodautoscaler.autoscaling/webapp autoscaled

# Check HPA status
kubectl get hpa

# Output:
# NAME     REFERENCE           TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# webapp   Deployment/webapp   12%/70%   3         10        3          30s
```

### Imperative Deployment Walkthrough (kubectl create deployment)

**Step 1: Create a Deployment imperatively**

```bash
kubectl create deployment my-first-deployment --image=stacksimplify/kubenginx:1.0.0

# Output:
# deployment.apps/my-first-deployment created
```

**Step 2: Verify Deployment, ReplicaSet, and Pods**

```bash
# List deployments
kubectl get deploy

# Output:
# NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
# my-first-deployment   1/1     1            1           10s

# List ReplicaSets (auto-created by the Deployment)
kubectl get rs

# Output:
# NAME                             DESIRED   CURRENT   READY   AGE
# my-first-deployment-6d4c8b4f9    1         1         1       10s

# List Pods
kubectl get po

# Output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# my-first-deployment-6d4c8b4f9-xyz123   1/1     Running   0          15s
```

**Step 3: Describe Deployment (detailed output)**

```bash
kubectl describe deployment my-first-deployment
```

Key fields in the output:

| Field | Meaning |
|---|---|
| `Replicas: 3 desired | 3 updated | 3 total | 3 available` | Current state of pod replicas |
| `StrategyType: RollingUpdate` | Update strategy (RollingUpdate or Recreate) |
| `RollingUpdateStrategy: 25% max unavailable, 25% max surge` | How many pods can be down/extra during updates |
| `NewReplicaSet` | The current active ReplicaSet |
| `OldReplicaSets` | Previous ReplicaSets (kept for rollback) |
| `Events` | History of scaling and rollout actions |

**RollingUpdateStrategy breakdown (with 4 replicas):**

| Parameter | Value | Meaning |
|---|---|---|
| `maxUnavailable: 25%` | 1 pod (25% of 4) | Up to 1 pod can be temporarily unavailable during update. At least 75% remain available. |
| `maxSurge: 25%` | 1 pod (25% of 4) | Up to 1 extra pod can be created above desired count to speed up rollout. |

**Step 4: Scale the Deployment**

```bash
# Scale up to 20 replicas
kubectl scale --replicas=20 deployment/my-first-deployment

# Output:
# deployment.apps/my-first-deployment scaled

# Verify
kubectl get deploy
# NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
# my-first-deployment   20/20   20           20          5m

kubectl get rs
# NAME                             DESIRED   CURRENT   READY   AGE
# my-first-deployment-6d4c8b4f9    20        20        20      5m

# Scale down to 10
kubectl scale --replicas=10 deployment/my-first-deployment
```

**Step 5: Expose Deployment as a NodePort Service**

```bash
kubectl expose deployment my-first-deployment \
  --type=NodePort \
  --port=80 \
  --target-port=80 \
  --name=my-first-deployment-service

# Output:
# service/my-first-deployment-service exposed

# Get service info
kubectl get svc
# NAME                          TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
# my-first-deployment-service   NodePort   10.100.100.200   <none>        80:31234/TCP   2m

# Get worker node public IP
kubectl get nodes -o wide

# Access the application:
# http://<worker-node-public-ip>:31234
```

### Updating a Deployment

Two methods to update a Deployment:

#### Method 1: `kubectl set image` (change container image)

```bash
# First, get the container name from the deployment
kubectl get deployment my-first-deployment -o yaml | grep -A2 "containers:"
# Output:
#   containers:
#   - name: kubenginx
#     image: stacksimplify/kubenginx:1.0.0

# Update from V1 to V2
kubectl set image deployment/my-first-deployment kubenginx=stacksimplify/kubenginx:2.0.0 --record=true

# Verify rollout status
kubectl rollout status deployment/my-first-deployment
# Output: deployment "my-first-deployment" successfully rolled out

# Check ReplicaSets — old one scaled to 0, new one active
kubectl get rs
# NAME                             DESIRED   CURRENT   READY   AGE
# my-first-deployment-6df9f4d59c   0         0         0       10m   ← V1 (scaled to 0)
# my-first-deployment-7c9c5d9c8b   1         1         1       1m    ← V2 (active)

# Verify rollout history
kubectl rollout history deployment/my-first-deployment
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         kubectl set image deployment/my-first-deployment kubenginx=stacksimplify/kubenginx:2.0.0 --record=true
```

The `--record=true` flag saves the command in the rollout history's `CHANGE-CAUSE` column, making it easy to see what changed in each revision.

#### Method 2: `kubectl edit deployment` (edit YAML directly)

```bash
# Opens the deployment YAML in your default editor
kubectl edit deployment/my-first-deployment --record=true

# Change the image field:
#   image: stacksimplify/kubenginx:2.0.0
# To:
#   image: stacksimplify/kubenginx:3.0.0
# Save and exit.

# Verify
kubectl rollout status deployment/my-first-deployment
kubectl get rs
# NAME                             DESIRED   CURRENT   READY   AGE
# my-first-deployment-6df9f4d59c   0         0         0       10m  ← V1
# my-first-deployment-7c9c5d9c8b   0         0         0       5m   ← V2
# my-first-deployment-8a7b5f9a4c   1         1         1       1m   ← V3 (active)

kubectl rollout history deployment/my-first-deployment
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         kubectl set image ... --record=true
# 3         kubectl edit deployment/my-first-deployment --record=true
```

### Rolling Back a Deployment

#### Rollback to Previous Version

```bash
# Check rollout history
kubectl rollout history deployment/my-first-deployment
# REVISION  CHANGE-CAUSE
# 1         kubectl set image ... kubenginx:1.0.0 --record=true
# 2         kubectl set image ... kubenginx:2.0.0 --record=true
# 3         kubectl set image ... kubenginx:3.0.0 --record=true

# View details of a specific revision
kubectl rollout history deployment/my-first-deployment --revision=2
# Containers:
#   kubenginx:
#     Image: stacksimplify/kubenginx:2.0.0

# Rollback to previous version (V3 → V2)
kubectl rollout undo deployment/my-first-deployment
# Output: deployment.apps/my-first-deployment rolled back

# Verify
kubectl get deploy
kubectl get rs
kubectl get po
kubectl describe deployment my-first-deployment
```

⚠️ **Revision numbering:** When you rollback, the rolled-back revision gets a new number. For example, if you rollback from revision 3 to revision 2, the current state becomes revision 4 (not revision 2).

#### Rollback to a Specific Revision

```bash
kubectl rollout undo deployment/my-first-deployment --to-revision=3
# Output: deployment.apps/my-first-deployment rolled back to revision 3

# Check history — rollback creates a new revision number
kubectl rollout history deployment/my-first-deployment
```

#### Rolling Restart (recreate all pods without changing the image)

```bash
kubectl rollout restart deployment/my-first-deployment
# Output: deployment.apps/my-first-deployment restarted

# Old pods terminate one by one, new pods are created — zero downtime
kubectl get po
```

### Pausing and Resuming a Deployment

Use pause/resume when you need to make multiple changes and apply them all at once as a single rollout.

```bash
# Step 1: Pause the deployment
kubectl rollout pause deployment/my-first-deployment
# Output: deployment.apps/my-first-deployment paused

# Step 2: Make Change #1 — update image to V4
kubectl set image deployment/my-first-deployment kubenginx=stacksimplify/kubenginx:4.0.0 --record=true
# Output: deployment.apps/my-first-deployment image updated
# No rollout happens yet — deployment is paused

# Verify no new ReplicaSet was created
kubectl get rs
kubectl rollout history deployment/my-first-deployment
# Revision number unchanged — changes are queued

# Step 3: Make Change #2 — set resource limits
kubectl set resources deployment/my-first-deployment -c=kubenginx --limits=cpu=20m,memory=30Mi
# Output: deployment.apps/my-first-deployment resource requirements updated
# Still no rollout — deployment is still paused

# Step 4: Resume the deployment — applies all changes as one rollout
kubectl rollout resume deployment/my-first-deployment
# Output: deployment.apps/my-first-deployment resumed

# Verify — new ReplicaSet created with both changes
kubectl get rs
kubectl rollout history deployment/my-first-deployment
# A single new revision appears with both the image update and resource limits
```

### Revision History Limit (Clean Up Old ReplicaSets)

By default, Kubernetes keeps 10 old ReplicaSets for rollback. To limit this:

```yaml
spec:
  revisionHistoryLimit: 2    # Keep only 2 old ReplicaSets
```

This removes old ReplicaSets beyond the limit, reducing clutter in `kubectl get rs` output.

### Canary Deployments

Run a canary version alongside the stable version with minimal replicas to test before full rollout:

```yaml
# canary-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp-canary
spec:
  replicas: 1              # Canary runs with only 1 replica
  selector:
    matchLabels:
      app: webapp          # Same label as stable deployment — shares the Service
  template:
    metadata:
      labels:
        app: webapp
        version: canary
    spec:
      containers:
      - name: webapp
        image: stacksimplify/kubenginx:4.0.0    # New version to test
        ports:
        - containerPort: 80
```

The canary Deployment uses the same `app: webapp` label as the stable Deployment, so the Service routes traffic to both. With 3 stable replicas and 1 canary replica, ~25% of traffic goes to the canary version.

**Adjusting canary traffic percentage:**

Traffic percentage is controlled by the replica ratio. Scale the canary deployment to shift traffic:

```bash
# With 5 stable + 2 canary = 7 pods → canary gets ~28% traffic (too high)
kubectl scale deployment webapp-canary --replicas=2

# Scale down to 1 canary → 5 stable + 1 canary = 6 pods → canary gets ~17%
kubectl scale deployment webapp-canary --replicas=1
```

**Full cutover to the new version:**

Once the canary is validated, shift all traffic to the new version:

```bash
# 1. Scale down the original deployment
kubectl scale deployment webapp --replicas=0

# 2. Scale up the canary to handle all traffic
kubectl scale deployment webapp-canary --replicas=5

# 3. Verify
kubectl get deployments
# NAME            READY   UP-TO-DATE   AVAILABLE   AGE
# webapp          0/0     0            0           10m
# webapp-canary   5/5     5            5           5m

# 4. Remove the old deployment
kubectl delete deployment webapp
```

### Deployment with YAML — Complete Example

**Deployment manifest:**

```yaml
# deployment-definition.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp3-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp3
  template:
    metadata:
      name: myapp3-pod
      labels:
        app: myapp3
    spec:
      containers:
        - name: myapp3-container
          image: stacksimplify/kubenginx:3.0.0
          ports:
            - containerPort: 80
```

**NodePort Service manifest:**

```yaml
# deployment-nodeport-service.yml
apiVersion: v1
kind: Service
metadata:
  name: deployment-nodeport-service
spec:
  type: NodePort
  selector:
    app: myapp3
  ports:
    - name: http
      port: 80
      targetPort: 80
      nodePort: 31233
```

**Deploy, test, and clean up:**

```bash
# Deploy
kubectl apply -f deployment-definition.yml
kubectl apply -f deployment-nodeport-service.yml

# Verify
kubectl get deploy
kubectl get rs
kubectl get pods
kubectl get svc

# Access application
kubectl get nodes -o wide
# http://<worker-node-public-ip>:31233

# Test rolling update
kubectl set image deployment/myapp3-deployment myapp3-container=stacksimplify/kubenginx:3.0.1
kubectl rollout status deployment/myapp3-deployment

# Rollback if needed
kubectl rollout undo deployment/myapp3-deployment

# Clean up
kubectl delete deployment myapp3-deployment
kubectl delete svc deployment-nodeport-service
```

### Deployment Troubleshooting — Common Errors

#### Error 1: Case-sensitive `kind` field

```bash
kubectl create -f deployment-definition.yaml

# Error:
# error when creating "deployment-definition.yaml":
# no kind "deployment" is registered for version "apps/v1"
```

**Cause:** The `kind` field is case-sensitive. `deployment` (lowercase) is invalid — it must be `Deployment` (capital D).

```yaml
# Wrong:
kind: deployment    # ← lowercase 'd'

# Correct:
kind: Deployment    # ← capital 'D'
```

This applies to all Kubernetes objects: `Pod`, `Service`, `ReplicaSet`, `Deployment`, `ConfigMap`, `Secret`, etc.

#### Error 2: Deployment pods stuck in ImagePullBackOff

```bash
kubectl get deployments
# NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
# frontend-deployment     0/4     4            0           10s   ← 0 READY

kubectl get pods
# NAME                                    READY   STATUS             RESTARTS   AGE
# frontend-deployment-7f8dcd896-stmbx     0/1     ImagePullBackOff   0          59s
# frontend-deployment-7f8dcd896-zc6wc     0/1     ErrImagePull       0          59s
# frontend-deployment-7f8dcd896-jgcbx     0/1     ErrImagePull       0          59s
# frontend-deployment-7f8dcd896-jbr44     0/1     ErrImagePull       0          59s
```

**Diagnose:** Describe a pod to find the wrong image:

```bash
kubectl describe pod frontend-deployment-7f8dcd896-stmbx

# Events:
#   Warning  Failed  kubelet  Failed to pull image "busybox888":
#   repository does not exist or may require authorization
```

**Fix:** Edit the deployment (unlike ReplicaSets, editing a Deployment **does** trigger a new rollout):

```bash
# Edit the deployment to fix the image
kubectl edit deployment frontend-deployment
# Change image: busybox888 → image: busybox
# Save and exit

# The deployment automatically creates new pods with the correct image
kubectl rollout status deployment/frontend-deployment
# deployment "frontend-deployment" successfully rolled out

kubectl get pods
# NAME                                    READY   STATUS    RESTARTS   AGE
# frontend-deployment-5d9f8c6a2e-abc12    1/1     Running   0          10s
# frontend-deployment-5d9f8c6a2e-def34    1/1     Running   0          10s
# frontend-deployment-5d9f8c6a2e-ghi56    1/1     Running   0          10s
# frontend-deployment-5d9f8c6a2e-hij78    1/1     Running   0          10s
```

> **Key difference from ReplicaSets:** When you `kubectl edit` a Deployment, it triggers a rolling update — new pods are created automatically. With a ReplicaSet, you must manually delete old pods.

#### Quick CLI: Create a Deployment with replicas

```bash
# Create a deployment with 3 replicas directly from CLI
kubectl create deployment http-frontend --image=httpd:2.4-alpine --replicas=3

# Verify
kubectl get deploy http-frontend
# NAME            READY   UP-TO-DATE   AVAILABLE   AGE
# http-frontend   3/3     3            3           10s
```

### Clean Up Imperative Deployment

```bash
# Delete the deployment
kubectl delete deployment my-first-deployment
# Output: deployment.apps "my-first-deployment" deleted

# Delete the service
kubectl delete svc my-first-deployment-service
# Output: service "my-first-deployment-service" deleted

# Verify
kubectl get all
# Only default Kubernetes objects should remain
```

### Deployment Pitfalls & Best Practices

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| No readiness probe | Users hit broken pods during rollout | Always add `readinessProbe` — Kubernetes won't send traffic until it passes |
| Using `:latest` image tag | Untraceable rollouts — can't tell which version is running | Pin image versions (`myapp:1.2.3`) and use Git SHA tags in CI/CD |
| No rollback plan | Manual recovery needed when deployment fails | Use `kubectl rollout undo` or `helm rollback`; keep `revisionHistoryLimit` > 0 |
| ConfigMap/Secret updated without pod restart | App runs with stale configuration | Version ConfigMaps (e.g., `app-config-v2`) or use `kubectl rollout restart` |
| `maxUnavailable: 0` + `maxSurge: 0` | Deadlock — no pods can be created or removed | Set at least one of `maxSurge` or `maxUnavailable` to > 0 |
| No resource requests/limits | Pods compete for resources, OOMKilled under load | Always set `resources.requests` and `resources.limits` |
| Deploying without `kubectl diff` | Unexpected changes applied blindly | Run `kubectl diff -f deployment.yaml` or `helm diff` before applying |

**Deployment best practices:**

- Treat every deployment as a risk — design for rollback
- Use labels and annotations for Git tracking (`app.kubernetes.io/version: "v1.2.3"`)
- Validate config changes with `kubectl diff` or `helm diff` before applying
- Monitor rollout events live: `kubectl rollout status deployment/myapp`
- For zero-downtime progressive rollout, use Argo Rollouts for canary and blue/green strategies
- Use `--atomic` flag with Helm to auto-rollback on failure: `helm upgrade --install myapp ./chart --atomic`

### Argo Rollouts — Progressive Delivery

Standard Kubernetes Deployments only support `RollingUpdate` and `Recreate` strategies. Argo Rollouts extends this with canary and blue-green deployments that include automated analysis and traffic management.

**Why Argo Rollouts over standard Deployments:**

| Feature | Standard Deployment | Argo Rollouts |
|---------|-------------------|---------------|
| Rolling update | ✅ | ✅ |
| Canary with traffic splitting | ❌ | ✅ (weighted traffic via Ingress/Service Mesh) |
| Blue-green with instant switch | ❌ | ✅ (active/preview services) |
| Automated rollback on metric failure | ❌ | ✅ (AnalysisRun with Prometheus) |
| Pause/resume at specific steps | Limited | ✅ (step-based promotion) |

**Install Argo Rollouts:**

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin for rollout management
brew install argoproj/tap/kubectl-argo-rollouts
# or
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

**Canary Rollout — gradually shift traffic:**

```yaml
# canary-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: webapp
spec:
  replicas: 5
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: myapp:v2.0.0
        ports:
        - containerPort: 8080
  strategy:
    canary:
      steps:
      - setWeight: 20          # Send 20% of traffic to new version
      - pause: {duration: 5m}  # Wait 5 minutes, observe metrics
      - setWeight: 50          # Increase to 50%
      - pause: {duration: 5m}
      - setWeight: 80          # Increase to 80%
      - pause: {duration: 2m}
      # After all steps complete, 100% traffic goes to new version
```

```bash
# Apply the rollout
kubectl apply -f canary-rollout.yaml

# Watch the rollout progress
kubectl argo rollouts get rollout webapp --watch

# Output:
# Name:            webapp
# Namespace:       default
# Status:          ◑ Progressing
# Strategy:        Canary
#   Step:          1/6
#   SetWeight:     20
#   ActualWeight:  20
# Images:          myapp:v1.0.0 (stable)
#                  myapp:v2.0.0 (canary)
# Replicas:
#   Desired:       5
#   Current:       5
#   Updated:       1
#   Ready:         5
#   Available:     5

# Manually promote to next step (if pause has no duration)
kubectl argo rollouts promote webapp

# Abort and rollback if something goes wrong
kubectl argo rollouts abort webapp
```

**Blue-Green Rollout — instant traffic switch:**

```yaml
# blue-green-rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: myapp:v2.0.0
        ports:
        - containerPort: 8080
  strategy:
    blueGreen:
      activeService: webapp-active       # Production traffic
      previewService: webapp-preview     # Preview/test traffic
      autoPromotionEnabled: false        # Require manual promotion
      scaleDownDelaySeconds: 30          # Keep old version for 30s after switch
```

```bash
# Two services needed:
kubectl create svc clusterip webapp-active --tcp=80:8080
kubectl create svc clusterip webapp-preview --tcp=80:8080

# After deploying, the new version is accessible via webapp-preview
# Test it, then promote:
kubectl argo rollouts promote webapp

# The active service now points to the new version
# Old version is scaled down after scaleDownDelaySeconds
```

**Automated Analysis — rollback on bad metrics:**

```yaml
# analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    interval: 60s
    successCondition: result[0] >= 0.95    # 95% success rate required
    failureLimit: 3                         # Abort after 3 failures
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(http_requests_total{status=~"2.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
```

Add the analysis to the canary strategy:

```yaml
strategy:
  canary:
    steps:
    - setWeight: 20
    - pause: {duration: 5m}
    - setWeight: 50
    - pause: {duration: 5m}
    analysis:
      templates:
      - templateName: success-rate
      startingStep: 1    # Start analysis from step 1
```

If the success rate drops below 95%, Argo Rollouts automatically aborts the rollout and reverts to the stable version.

> **Cross-reference:** Prometheus metrics → MODULE-27; Ingress traffic splitting → MODULE-14

---

