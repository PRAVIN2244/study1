# MODULE 7: kubectl — The Kubernetes CLI

---

## 7.1 kubectl — The Kubernetes CLI

kubectl is the command-line tool for interacting with Kubernetes clusters. It reads connection details from `~/.kube/config` (the kubeconfig file), which contains:
- **Cluster** — API server URL and CA certificate
- **User** — authentication credentials (token, certificate, or AWS IAM)
- **Context** — a cluster + user + namespace combination

Every kubectl command follows this internal flow:
1. Reads `~/.kube/config` to find the current context
2. Authenticates with the API server (via certificate, token, or AWS IAM)
3. Sends a REST API request (GET, POST, PUT, DELETE)
4. API server validates, processes, and queries etcd
5. API server returns the response (JSON)
6. kubectl formats and prints human-readable output

```
kubectl get pods
   │
   ▼
~/.kube/config → finds API server URL + credentials
   │
   ▼
GET https://<api-server>/api/v1/namespaces/default/pods
   │
   ▼
API Server → authenticates → authorizes (RBAC) → reads from etcd
   │
   ▼
JSON response → kubectl formats → terminal output
```

**kubectl ONLY talks to the API Server.** It never communicates directly with etcd, kubelet, scheduler, or any other component.


### Installation

```bash
# On Linux/macOS
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify installation
kubectl version --client

# Output:
# Client Version: v1.28.2
# Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
```

### kubectl Command Structure

```
kubectl [COMMAND] [TYPE] [NAME] [FLAGS]
   │        │       │      │       │
   │        │       │      │       └── Options like -n namespace, -o output format
   │        │       │      └────────── Name of the specific resource
   │        │       └───────────────── Resource type (pod, service, deployment)
   │        └───────────────────────── Action (get, create, delete, apply, describe)
   └────────────────────────────────── The CLI tool
```


### Essential kubectl Commands with Examples

#### Cluster Information

```bash
# Get cluster info
kubectl cluster-info

# Output:
# Kubernetes control plane is running at https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com
# CoreDNS is running at https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

# Get all nodes in the cluster
kubectl get nodes

# Output:
# NAME                                       STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal                 Ready    <none>   5d    v1.28.2
# ip-10-0-2-200.ec2.internal                 Ready    <none>   5d    v1.28.2
# ip-10-0-3-300.ec2.internal                 Ready    <none>   5d    v1.28.2

# Get detailed node information
kubectl describe node ip-10-0-1-100.ec2.internal

# Output (truncated):
# Name:               ip-10-0-1-100.ec2.internal
# Roles:              <none>
# Labels:             beta.kubernetes.io/instance-type=t3.medium
#                     kubernetes.io/arch=amd64
#                     topology.kubernetes.io/zone=us-east-1a
# Capacity:
#   cpu:              2
#   memory:           4028Ki
#   pods:             17
# Allocatable:
#   cpu:              1930m
#   memory:           3532Ki
#   pods:             17
```

#### Working with Resources

```bash
# List all resources in default namespace
kubectl get all

# Output:
# NAME                         READY   STATUS    RESTARTS   AGE
# pod/nginx-7bf8c77b5b-abc12   1/1     Running   0          2h
#
# NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
# service/kubernetes   ClusterIP   172.20.0.1   <none>        443/TCP   5d
#
# NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
# deployment.apps/nginx   1/1     1            1           2h

# List pods in ALL namespaces
kubectl get pods --all-namespaces
# Short form:
kubectl get pods -A

# Output:
# NAMESPACE     NAME                       READY   STATUS    RESTARTS   AGE
# default       nginx-7bf8c77b5b-abc12     1/1     Running   0          2h
# kube-system   coredns-5d78c9869d-x1y2z   1/1     Running   0          5d
# kube-system   aws-node-abc12             1/1     Running   0          5d
# kube-system   kube-proxy-def34           1/1     Running   0          5d

# Get pods with more details
kubectl get pods -o wide

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE   IP           NODE                          NOMINATED NODE
# nginx-7bf8c77b5b-abc12   1/1     Running   0          2h    10.0.1.15    ip-10-0-1-100.ec2.internal    <none>

# Get output in YAML format (useful for debugging)
kubectl get pod nginx-7bf8c77b5b-abc12 -o yaml

# Get output in JSON format
kubectl get pod nginx-7bf8c77b5b-abc12 -o json

# Filter output with JSONPath
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
# Output: nginx-7bf8c77b5b-abc12

# Custom columns output
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP

# Output:
# NAME                     STATUS    IP
# nginx-7bf8c77b5b-abc12   Running   10.0.1.15
```

#### Creating Resources

```bash
# Imperative: Create a pod directly
kubectl run nginx --image=nginx:1.25 --port=80

# Output:
# pod/nginx created

# Imperative: Create a deployment
kubectl create deployment webapp --image=nginx:1.25 --replicas=3

# Output:
# deployment.apps/webapp created

# Declarative: Apply from a YAML file (PREFERRED method)
kubectl apply -f deployment.yaml

# Output:
# deployment.apps/webapp created

# Generate YAML without creating (dry-run) — great for learning
kubectl run nginx --image=nginx:1.25 --port=80 --dry-run=client -o yaml

# Output:
# apiVersion: v1
# kind: Pod
# metadata:
#   labels:
#     run: nginx
#   name: nginx
# spec:
#   containers:
#   - image: nginx:1.25
#     name: nginx
#     ports:
#     - containerPort: 80
```

#### Additional Imperative Commands

```bash
# Create a pod with custom labels
kubectl run redis --image=redis:alpine --labels="tier=db"
# pod/redis created

# Create a pod with multiple labels
kubectl run web --image=nginx --labels="app=web,env=prod,tier=frontend"

# Create a pod AND expose it as a ClusterIP service in one step
kubectl run httpd --image=httpd:alpine --port=80 --expose=true
# service/httpd created
# pod/httpd created

# Create a deployment in a specific namespace with replicas
kubectl create deployment redis-deploy --image=redis --replicas=2 -n dev-ns
# deployment.apps/redis-deploy created
```

**`kubectl expose` — all resource types:**

```bash
# Expose a pod
kubectl expose pod redis --port=6379 --name=redis-service

# Expose a deployment as NodePort
kubectl expose deployment webapp --type=NodePort --port=80 --target-port=8080

# Expose a ReplicaSet
kubectl expose rs nginx --port=80 --target-port=8000

# Expose with UDP protocol
kubectl expose rc streamer --port=4100 --protocol=UDP --name=video-stream

# Expose from a file
kubectl expose -f nginx-controller.yaml --port=80 --target-port=8000

# Expose a service under a new name (re-expose)
kubectl expose service nginx --port=443 --target-port=8443 --name=nginx-https
```

#### Debugging & Inspection

```bash
# Describe a resource (shows events, conditions, details)
kubectl describe pod nginx

# Output (truncated):
# Name:         nginx
# Namespace:    default
# Node:         ip-10-0-1-100.ec2.internal/10.0.1.100
# Status:       Running
# IP:           10.0.1.15
# Containers:
#   nginx:
#     Image:          nginx:1.25
#     Port:           80/TCP
#     State:          Running
#       Started:      Mon, 15 Jan 2024 10:00:00 +0000
#     Ready:          True
# Events:
#   Type    Reason     Age   From               Message
#   ----    ------     ----  ----               -------
#   Normal  Scheduled  2m    default-scheduler  Successfully assigned default/nginx to ip-10-0-1-100
#   Normal  Pulling    2m    kubelet            Pulling image "nginx:1.25"
#   Normal  Pulled     1m    kubelet            Successfully pulled image "nginx:1.25"
#   Normal  Created    1m    kubelet            Created container nginx
#   Normal  Started    1m    kubelet            Started container nginx

# View container logs
kubectl logs nginx

# Output:
# /docker-entrypoint.sh: Configuration complete; ready for start up
# 2024/01/15 10:00:01 [notice] 1#1: nginx/1.25.3
# 2024/01/15 10:00:01 [notice] 1#1: built by gcc 12.2.0

# Follow logs in real-time (like tail -f)
kubectl logs -f nginx

# View logs of a specific container in a multi-container pod
kubectl logs my-pod -c sidecar-container

# View previous container logs (after a crash)
kubectl logs nginx --previous

# Execute a command inside a running container
kubectl exec -it nginx -- /bin/bash

# Output:
# root@nginx:/#

# Execute a single command
kubectl exec nginx -- cat /etc/nginx/nginx.conf

# Port-forward to access a pod locally
kubectl port-forward pod/nginx 8080:80

# Output:
# Forwarding from 127.0.0.1:8080 -> 80
```

#### Modifying & Deleting Resources

```bash
# Edit a resource in your default editor
kubectl edit deployment webapp

# Scale a deployment
kubectl scale deployment webapp --replicas=5

# Output:
# deployment.apps/webapp scaled

# Delete a resource
kubectl delete pod nginx

# Output:
# pod "nginx" deleted

# Delete using a YAML file
kubectl delete -f deployment.yaml

# Delete all pods in a namespace
kubectl delete pods --all -n my-namespace

# Force delete a stuck pod
kubectl delete pod nginx --grace-period=0 --force
```

#### Labels and Selectors

```bash
# Add a label to a pod
kubectl label pod nginx environment=production

# Output:
# pod/nginx labeled

# Show labels
kubectl get pods --show-labels

# Output:
# NAME    READY   STATUS    RESTARTS   AGE   LABELS
# nginx   1/1     Running   0          2h    environment=production,run=nginx

# Filter by label
kubectl get pods -l environment=production

# Filter by multiple labels
kubectl get pods -l "environment=production,app=nginx"

# Remove a label (note the minus sign)
kubectl label pod nginx environment-
```

#### Rollout Commands

```bash
# Check rollout status of a deployment
kubectl rollout status deployment/mydeploy

# Output:
# deployment "mydeploy" successfully rolled out

# View rollout history (shows revisions)
kubectl rollout history deployment/mydeploy

# Output:
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>

# Rollback to a specific revision
kubectl rollout undo deployment/mydeploy --to-revision=1

# Output:
# deployment.apps/mydeploy rolled back
```

#### kubectl explain — API Documentation

`explain` shows the API schema for any resource. Very useful for learning field names without checking documentation.

```bash
kubectl explain pod

# Output:
# KIND:     Pod
# VERSION:  v1
# DESCRIPTION:
#      Pod is a collection of containers that can run on a host...

# Drill into nested fields
kubectl explain pod.spec.containers

# Output:
# KIND:     Pod
# VERSION:  v1
# RESOURCE: containers <[]Object>
# DESCRIPTION:
#      List of containers belonging to the pod...
# FIELDS:
#    args   <[]string>
#    command <[]string>
#    env    <[]Object>
#    image  <string>
#    name   <string> -required-
#    ports  <[]Object>
#    ...

# Go deeper
kubectl explain pod.spec.containers.resources
```

#### kubectl config — Context Management

```bash
# View all contexts
kubectl config get-contexts

# Output:
# CURRENT   NAME        CLUSTER     AUTHINFO    NAMESPACE
# *         minikube    minikube    minikube    default

# Switch to a different context
kubectl config use-context minikube

# View current context
kubectl config current-context

# Output:
# minikube

# Set default namespace for current context
kubectl config set-context --current --namespace=demo
```

#### kubectl top — Resource Usage (Requires Metrics Server)

```bash
# Node resource usage
kubectl top nodes

# Output:
# NAME       CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# minikube   250m         12%    900Mi            45%

# Pod resource usage
kubectl top pods

# Output:
# NAME        CPU(cores)   MEMORY(bytes)
# testpod     1m           10Mi
# nginx       2m           5Mi
```

If metrics-server is not installed, you get: `error: Metrics API not available`. Install it with:
```bash
# On Minikube
minikube addons enable metrics-server

# On other clusters
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

#### kubectl auth — Permission Checks

```bash
# Check if you can perform an action
kubectl auth can-i list pods

# Output:
# yes

# Check as another user
kubectl auth can-i list pods --as adam

# Output:
# no

# Check in a specific namespace
kubectl auth can-i create deployments -n production --as adam

# Output:
# no
```

#### API Resources and Events

```bash
# List all available API resources (shows short names)
kubectl api-resources

# Output (truncated):
# NAME          SHORTNAMES   APIVERSION   NAMESPACED   KIND
# pods          po           v1           true         Pod
# services      svc          v1           true         Service
# deployments   deploy       apps/v1      true         Deployment
# nodes         no           v1           false        Node
# namespaces    ns           v1           false        Namespace

# You can use short names:
kubectl get po        # same as kubectl get pods
kubectl get svc       # same as kubectl get services
kubectl get deploy    # same as kubectl get deployments

# View cluster events (important for debugging)
kubectl get events

# Output:
# LAST SEEN   TYPE      REASON      OBJECT          MESSAGE
# 2m          Normal    Scheduled   pod/nginx       Successfully assigned default/nginx to minikube
# 2m          Normal    Pulled      pod/nginx       Container image "nginx" already present
# 2m          Normal    Created     pod/nginx       Created container nginx
# 2m          Normal    Started     pod/nginx       Started container nginx

# Sort events by time
kubectl get events --sort-by='.lastTimestamp'
```

#### REST API — How kubectl Talks to the API Server

kubectl sends standard REST calls. You can see the raw API:

```bash
# View available API paths
kubectl get --raw /api

# Query pods directly via REST
kubectl get --raw /api/v1/namespaces/default/pods

# Common REST mappings:
# kubectl get pods        → GET  /api/v1/namespaces/default/pods
# kubectl create -f x.yml → POST /api/v1/namespaces/default/pods
# kubectl delete pod x    → DELETE /api/v1/namespaces/default/pods/x
# kubectl get deploy      → GET  /apis/apps/v1/namespaces/default/deployments
```


### kubectl create vs kubectl apply

These are the two main ways to create resources, and they behave differently:

```bash
# kubectl create — imperative, creates new resources only
kubectl create -f deployment.yaml

# Output (first time):
# deployment.apps/webapp created

# Run again:
# Error from server (AlreadyExists): deployments.apps "webapp" already exists
# ← Fails if resource already exists!

# kubectl apply — declarative, creates OR updates resources
kubectl apply -f deployment.yaml

# Output (first time):
# deployment.apps/webapp created

# Run again (after editing the file):
# deployment.apps/webapp configured
# ← Updates the existing resource with changes!

# Run again (no changes):
# deployment.apps/webapp unchanged
# ← No error, idempotent!
```

| Feature | `kubectl create` | `kubectl apply` |
|---|---|---|
| **Mode** | Imperative | Declarative |
| **If resource exists** | Error (AlreadyExists) | Updates it |
| **If resource doesn't exist** | Creates it | Creates it |
| **Tracks changes** | No | Yes (stores last-applied config as annotation) |
| **Use case** | Quick one-off creation, scripts | Production, GitOps, CI/CD |
| **Idempotent** | No | Yes |

```bash
# Other imperative commands:
kubectl create deployment webapp --image=nginx      # Create deployment
kubectl run test-pod --image=busybox                # Create pod
kubectl expose deployment webapp --port=80          # Create service
kubectl create namespace staging                    # Create namespace

# Declarative (always use in production):
kubectl apply -f deployment.yaml                    # Create or update
kubectl apply -f k8s/                               # Apply all files in directory
kubectl apply -f https://example.com/manifest.yaml  # Apply from URL

# Generate YAML without creating (dry-run) — useful for learning
kubectl create deployment webapp --image=nginx --dry-run=client -o yaml > deployment.yaml
kubectl run nginx --image=nginx --port=80 --dry-run=client -o yaml > pod.yaml
```

```bash
# Preview what would change before applying (like git diff)
kubectl diff -f deployment.yaml

# Output:
# -  replicas: 3
# +  replicas: 5
# Shows exactly what will change without applying
```

**Production rule:** Always use `kubectl apply` with version-controlled YAML files. Use `kubectl create` only for quick testing or generating YAML templates with `--dry-run=client -o yaml`.

**Interview question: What is the difference between kubectl create and kubectl apply?**
`kubectl create` is imperative — it creates a resource and fails if it already exists. `kubectl apply` is declarative — it creates the resource if it doesn't exist, or updates it if it does. `apply` also stores the last-applied configuration as an annotation, enabling three-way merge on subsequent updates. Always use `apply` in production for idempotent, repeatable deployments.

### How kubectl apply Works Internally

When you run `kubectl apply`, Kubernetes doesn't just overwrite the live object. It performs a **three-way merge** using three sources of truth:

| Source | What It Is | Where It Lives |
|--------|-----------|----------------|
| **Local file** | Your current YAML manifest on disk | Your filesystem |
| **Last-applied configuration** | A snapshot of what you last applied | Stored as an annotation on the live object |
| **Live object** | The actual current state in the cluster | etcd (via API server) |

**The three-way merge process:**

1. Compare the **local file** against the **last-applied configuration** to determine what you intentionally changed
2. Compare those changes against the **live object** to determine what needs updating
3. Apply only the differences — fields you added, modified, or removed

This is what makes `kubectl apply` safe for collaborative environments — it won't overwrite changes made by other tools (autoscalers, admission controllers, other users) unless you explicitly changed those same fields.

#### The last-applied-configuration Annotation

Every time you run `kubectl apply`, Kubernetes stores your entire local manifest as a JSON annotation on the live object:

```yaml
# After running: kubectl apply -f deployment.yaml
# View the annotation with: kubectl get deployment nginx -o yaml
metadata:
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: |
      {"apiVersion":"apps/v1","kind":"Deployment","metadata":{"name":"nginx",
      "labels":{"app":"nginx"}},"spec":{"replicas":3,"selector":{"matchLabels":
      {"app":"nginx"}},"template":{"metadata":{"labels":{"app":"nginx"}},
      "spec":{"containers":[{"name":"nginx","image":"nginx:1.25",
      "ports":[{"containerPort":80}]}]}}}}
```

You can inspect this annotation directly:

```bash
# View the full last-applied-configuration
kubectl get deployment nginx -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}' | python3 -m json.tool
```

```json
{
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "nginx",
        "labels": {
            "app": "nginx"
        }
    },
    "spec": {
        "replicas": 3,
        "selector": {
            "matchLabels": {
                "app": "nginx"
            }
        },
        "template": {
            "metadata": {
                "labels": {
                    "app": "nginx"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx:1.25",
                        "ports": [
                            {
                                "containerPort": 80
                            }
                        ]
                    }
                ]
            }
        }
    }
}
```

#### Step-by-Step Example: How the Three-Way Merge Works

**Step 1 — Initial apply:**

```yaml
# deployment.yaml (v1)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
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
        image: nginx:1.25
        ports:
        - containerPort: 80
```

```bash
kubectl apply -f deployment.yaml
```

After this:
- **Live object** = your YAML + Kubernetes defaults (e.g., `strategy: RollingUpdate`)
- **Last-applied annotation** = exact copy of your YAML (as JSON)

**Step 2 — Someone scales the deployment imperatively:**

```bash
kubectl scale deployment nginx --replicas=5
```

Now:
- **Live object** has `replicas: 5`
- **Last-applied annotation** still has `replicas: 3`
- **Your local file** still has `replicas: 3`

**Step 3 — You modify the image and apply again:**

```yaml
# deployment.yaml (v2) — changed image, kept replicas: 3
spec:
  replicas: 3
  ...
    spec:
      containers:
      - name: nginx
        image: nginx:1.26    # Changed from 1.25 to 1.26
```

```bash
kubectl apply -f deployment.yaml
```

**The three-way merge logic:**

| Field | Local File | Last-Applied | Live Object | Decision |
|-------|-----------|-------------|-------------|----------|
| `image` | `nginx:1.26` | `nginx:1.25` | `nginx:1.25` | **Update to 1.26** (you changed it) |
| `replicas` | `3` | `3` | `5` | **Keep 5** (you didn't change it; local = last-applied, so the live value is preserved) |

Result: Image updates to `nginx:1.26`, but replicas stays at `5`. The three-way merge detected that you didn't intentionally change replicas (your file still says 3, same as last-applied), so it respects the live value.

#### How Removed Fields Are Handled

The three-way merge also detects when you **remove** a field from your YAML:

```yaml
# deployment.yaml (v1) — has a type label
metadata:
  labels:
    app: nginx
    type: frontend    # Present in v1
```

```bash
kubectl apply -f deployment.yaml    # type: frontend is now in last-applied
```

```yaml
# deployment.yaml (v2) — type label removed
metadata:
  labels:
    app: nginx
    # type: frontend is GONE
```

```bash
kubectl apply -f deployment.yaml
```

**Merge logic for the `type` label:**
- Present in **last-applied**? Yes (`type: frontend`)
- Present in **local file**? No (removed)
- Decision: **Delete from live object** — you intentionally removed it

This is the key advantage over `kubectl replace`: `apply` knows the difference between "I never set this field" and "I removed this field."

#### ⚠️ Warning: Don't Mix Imperative and Declarative

```bash
# BAD: Mix of approaches causes confusion
kubectl apply -f deployment.yaml     # Declarative — sets last-applied annotation
kubectl edit deployment nginx        # Imperative — modifies live object, does NOT update last-applied
kubectl set image deployment/nginx nginx=nginx:1.27  # Imperative — same problem
kubectl apply -f deployment.yaml     # Next apply may undo imperative changes!
```

When you use imperative commands (`kubectl edit`, `kubectl set`, `kubectl scale`), they modify the **live object** but do NOT update the **last-applied annotation**. On the next `kubectl apply`, the three-way merge may produce unexpected results because the last-applied annotation is stale.

**Best practice:** Pick one approach and stick with it:
- **Declarative (recommended for production):** Always edit YAML files and run `kubectl apply`
- **Imperative (acceptable for debugging/testing):** Use `kubectl edit`, `kubectl set`, `kubectl scale` — but don't mix with `apply`

If you must recover after mixing approaches, you can force-update the last-applied annotation:

```bash
# Reset last-applied annotation to match the current local file
kubectl apply set-last-applied -f deployment.yaml
```

Or view what the current last-applied annotation contains:

```bash
kubectl apply view-last-applied deployment nginx
```


### Common kubectl Errors

| Error | Cause | Fix |
|---|---|---|
| `The connection to the server localhost:8080 was refused` | No cluster running or kubeconfig not configured | Start cluster or check `~/.kube/config` |
| `Error from server (Forbidden)` | RBAC denies access for this user/service account | Check role bindings with `kubectl auth can-i` |
| `Error from server (NotFound)` | Resource doesn't exist | Verify name and namespace with `kubectl get` |
| `error: a container name must be specified` | Multi-container pod without `-c` flag | Add `-c <container-name>` to logs/exec commands |
| `Unable to connect to the server: dial tcp: lookup ... no such host` | Wrong API server URL in kubeconfig | Check `kubectl config view` and fix server URL |
| `error: Metrics API not available` | metrics-server not installed | Install metrics-server (see kubectl top section) |

### kubectl Command Summary

| Category | Commands | Purpose |
|---|---|---|
| **View** | `get` | List resources |
| **Detail** | `describe` | Show detailed info + events |
| **Create** | `apply`, `create`, `run` | Create or update resources |
| **Delete** | `delete` | Remove resources |
| **Debug** | `logs`, `exec`, `port-forward` | Inspect running containers |
| **Scale** | `scale` | Change replica count |
| **Rollback** | `rollout status/history/undo` | Manage deployment rollouts |
| **Auth** | `auth can-i` | Check permissions |
| **Config** | `config get-contexts/use-context/set-context` | Manage cluster connections |
| **API Info** | `explain`, `api-resources` | Explore API schema |
| **Metrics** | `top` | View resource usage |
| **Events** | `get events` | Troubleshoot scheduling/startup issues |

---

