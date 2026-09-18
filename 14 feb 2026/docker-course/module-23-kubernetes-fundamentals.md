# Module 23: Kubernetes Fundamentals

---

## 23.1 What is Kubernetes?

Kubernetes (K8s) is an open-source container orchestration platform. It automates deployment, scaling, and management of containerized applications.

```
┌─────────────────────────────────────────────────────────────┐
│              DOCKER SWARM vs KUBERNETES                      │
│                                                              │
│  Docker Swarm:                                              │
│    Built into Docker                                        │
│    Simpler to set up and use                                │
│    Fewer features                                           │
│    Smaller community                                        │
│                                                              │
│  Kubernetes:                                                │
│    Industry standard for orchestration                      │
│    More complex but more powerful                           │
│    Massive ecosystem (Helm, Istio, Prometheus, etc.)        │
│    Supported by all major cloud providers                   │
│    CNCF graduated project                                   │
│                                                              │
│  Both solve the same problem:                               │
│    Running containers across multiple machines              │
│    with scaling, self-healing, and load balancing           │
└─────────────────────────────────────────────────────────────┘
```

---

## 23.2 Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              KUBERNETES CLUSTER                              │
│                                                              │
│  Control Plane (Master):                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Server (kube-apiserver)                         │   │
│  │    Entry point for all K8s operations                │   │
│  │    kubectl → API Server → cluster                    │   │
│  │                                                      │   │
│  │  etcd                                                │   │
│  │    Key-value store for all cluster data              │   │
│  │    Similar to Swarm's Raft log                       │   │
│  │                                                      │   │
│  │  Scheduler (kube-scheduler)                          │   │
│  │    Assigns pods to nodes                             │   │
│  │    Similar to Swarm's task scheduler                 │   │
│  │                                                      │   │
│  │  Controller Manager (kube-controller-manager)        │   │
│  │    Maintains desired state (replicas, health)        │   │
│  │    Similar to Swarm's reconciliation loop            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Worker Nodes:                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  kubelet                                             │   │
│  │    Agent on each node, manages pods                  │   │
│  │                                                      │   │
│  │  kube-proxy                                          │   │
│  │    Network proxy, handles service routing            │   │
│  │                                                      │   │
│  │  Container Runtime (containerd, CRI-O)               │   │
│  │    Runs containers (Docker is one option)            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 23.3 Pods — The Smallest Deployable Unit

A Pod is one or more containers that share network and storage. It's the basic unit in Kubernetes (like a task in Swarm).

```
┌─────────────────────────────────────────────────────────────┐
│              POD                                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Pod: my-app                                         │   │
│  │  ┌────────────┐  ┌────────────┐                     │   │
│  │  │ Container 1│  │ Container 2│  (sidecar)          │   │
│  │  │ nginx      │  │ log-agent  │                     │   │
│  │  └────────────┘  └────────────┘                     │   │
│  │                                                      │   │
│  │  Shared:                                             │   │
│  │    • Network namespace (same IP, localhost)          │   │
│  │    • Storage volumes                                 │   │
│  │    • Pod IP: 10.244.1.5                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Most pods have ONE container                               │
│  Multi-container pods: sidecar, init, ambassador patterns  │
└─────────────────────────────────────────────────────────────┘
```

### Creating a Pod

```bash
# Imperative (command line)
$ kubectl run nginx --image=nginx --port=80

# Output:
# pod/nginx created

# Check pod status
$ kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          30s

# Detailed info
$ kubectl describe pod nginx
# Name:         nginx
# Namespace:    default
# Node:         worker-1/192.168.1.20
# Status:       Running
# IP:           10.244.1.5
# Containers:
#   nginx:
#     Image:    nginx
#     Port:     80/TCP
#     State:    Running
```

### Pod YAML (Declarative)

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: web
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
```

```bash
# Create from YAML
$ kubectl apply -f pod.yaml

# Delete a pod
$ kubectl delete pod nginx

# View pod logs
$ kubectl logs nginx

# Exec into a pod
$ kubectl exec -it nginx -- /bin/sh
```

---

## 23.4 ReplicaSets — Maintaining Pod Count

A ReplicaSet ensures a specified number of pod replicas are running at all times. Similar to Swarm's replica count.

```yaml
# replicaset.yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web-rs
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
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
```

```bash
$ kubectl apply -f replicaset.yaml

$ kubectl get replicaset
# NAME     DESIRED   CURRENT   READY   AGE
# web-rs   3         3         3       30s

$ kubectl get pods
# NAME           READY   STATUS    RESTARTS   AGE
# web-rs-abc12   1/1     Running   0          30s
# web-rs-def34   1/1     Running   0          30s
# web-rs-ghi56   1/1     Running   0          30s

# Delete a pod — ReplicaSet creates a replacement
$ kubectl delete pod web-rs-abc12
# pod "web-rs-abc12" deleted

$ kubectl get pods
# web-rs-def34   1/1     Running   0          2m
# web-rs-ghi56   1/1     Running   0          2m
# web-rs-jkl78   1/1     Running   0          5s    ← replacement
```

```
┌─────────────────────────────────────────────────────────────┐
│  ReplicaSet = Swarm's replica count                         │
│  "I want 3 pods running at all times"                       │
│  If one dies → ReplicaSet creates a new one                │
│  If there are too many → ReplicaSet deletes extras         │
│                                                              │
│  ⚠️  In practice, you rarely create ReplicaSets directly   │
│  Use Deployments instead (they manage ReplicaSets for you) │
└─────────────────────────────────────────────────────────────┘
```

---

## 23.5 Deployments — The Standard Way to Run Applications

A Deployment manages ReplicaSets and provides rolling updates and rollbacks. This is the primary way to run stateless applications in Kubernetes.

```
┌─────────────────────────────────────────────────────────────┐
│              DEPLOYMENT HIERARCHY                            │
│                                                              │
│  Deployment (manages)                                       │
│    └── ReplicaSet (maintains)                               │
│          ├── Pod 1                                          │
│          ├── Pod 2                                          │
│          └── Pod 3                                          │
│                                                              │
│  Swarm equivalent:                                          │
│    Service (manages)                                        │
│      ├── Task 1 → Container 1                              │
│      ├── Task 2 → Container 2                              │
│      └── Task 3 → Container 3                              │
└─────────────────────────────────────────────────────────────┘
```

### Creating a Deployment

```yaml
# deployment.yaml
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
        - name: nginx
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              memory: "64Mi"
              cpu: "250m"
            limits:
              memory: "128Mi"
              cpu: "500m"
```

```bash
# Create deployment
$ kubectl apply -f deployment.yaml

# Check deployment
$ kubectl get deployments
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# web    3/3     3            3           30s

# Check pods
$ kubectl get pods
# NAME                   READY   STATUS    RESTARTS   AGE
# web-6d8f9b7c4d-abc12   1/1     Running   0          30s
# web-6d8f9b7c4d-def34   1/1     Running   0          30s
# web-6d8f9b7c4d-ghi56   1/1     Running   0          30s

# Scale deployment
$ kubectl scale deployment web --replicas=5

# Or edit the YAML and apply
$ kubectl apply -f deployment.yaml
```

### Rolling Updates

```bash
# Update the image
$ kubectl set image deployment/web nginx=nginx:1.26

# Watch the rollout
$ kubectl rollout status deployment/web
# Waiting for deployment "web" rollout to finish:
#   1 out of 3 new replicas have been updated...
#   2 out of 3 new replicas have been updated...
#   3 out of 3 new replicas have been updated...
# deployment "web" successfully rolled out

# Check rollout history
$ kubectl rollout history deployment/web
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         <none>
```

### Rollback

```bash
# Rollback to previous version
$ kubectl rollout undo deployment/web

# Rollback to a specific revision
$ kubectl rollout undo deployment/web --to-revision=1

# Check current image
$ kubectl describe deployment web | grep Image
# Image: nginx:1.25   ← rolled back
```

---

## 23.6 Kubernetes Services — Exposing Applications

A Service provides a stable network endpoint for a set of pods. Pods are ephemeral (IPs change), but Services provide a fixed IP and DNS name.

```
┌─────────────────────────────────────────────────────────────┐
│              SERVICE TYPES                                    │
│                                                              │
│  ClusterIP (default):                                       │
│    Internal-only IP within the cluster                      │
│    Other pods can reach it, external traffic cannot         │
│    Like Docker's internal DNS resolution                    │
│                                                              │
│  NodePort:                                                  │
│    Exposes service on each node's IP at a static port       │
│    Range: 30000-32767                                       │
│    Like Swarm's published ports                             │
│                                                              │
│  LoadBalancer:                                              │
│    Creates an external load balancer (cloud provider)       │
│    Gets a public IP automatically                           │
│    Like Swarm's routing mesh + external LB                  │
│                                                              │
│  ExternalName:                                              │
│    Maps to an external DNS name                             │
│    No proxying, just DNS CNAME                              │
└─────────────────────────────────────────────────────────────┘
```

### ClusterIP Service

```yaml
# service-clusterip.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: ClusterIP
  selector:
    app: web          # Matches pods with label app=web
  ports:
    - port: 80        # Service port
      targetPort: 80  # Container port
```

```bash
$ kubectl apply -f service-clusterip.yaml

$ kubectl get services
# NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
# web-service   ClusterIP   10.96.45.123   <none>        80/TCP    30s

# Other pods can reach it at:
#   web-service:80
#   web-service.default.svc.cluster.local:80
#   10.96.45.123:80
```

### NodePort Service

```yaml
# service-nodeport.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30080    # Optional: auto-assigned if omitted
```

```bash
$ kubectl apply -f service-nodeport.yaml

$ kubectl get services
# NAME           TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# web-nodeport   NodePort   10.96.78.90    <none>        80:30080/TCP   30s

# Access from outside the cluster:
# http://<any-node-ip>:30080
# Similar to Swarm's routing mesh
```

### LoadBalancer Service

```yaml
# service-lb.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-lb
spec:
  type: LoadBalancer
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
```

```bash
$ kubectl apply -f service-lb.yaml

$ kubectl get services
# NAME     TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)        AGE
# web-lb   LoadBalancer   10.96.12.34    34.56.78.90    80:31234/TCP   2m

# Access from internet: http://34.56.78.90
# Cloud provider creates a load balancer automatically
```

---

## 23.7 Namespaces — Logical Cluster Partitioning

Namespaces divide a cluster into virtual sub-clusters. They provide scope for names and can have resource quotas.

```bash
# List namespaces
$ kubectl get namespaces
# NAME              STATUS   AGE
# default           Active   10d
# kube-system       Active   10d    ← K8s system components
# kube-public       Active   10d    ← Publicly readable
# kube-node-lease   Active   10d    ← Node heartbeats

# Create a namespace
$ kubectl create namespace staging

# Deploy to a specific namespace
$ kubectl apply -f deployment.yaml -n staging

# List pods in a namespace
$ kubectl get pods -n staging

# List pods in all namespaces
$ kubectl get pods --all-namespaces
```

---

## 23.8 Swarm vs Kubernetes — Concept Mapping

```
┌──────────────────────┬──────────────────────────────────────┐
│ Docker Swarm         │ Kubernetes                           │
├──────────────────────┼──────────────────────────────────────┤
│ Swarm cluster        │ Kubernetes cluster                   │
│ Manager node         │ Control plane (master)               │
│ Worker node          │ Worker node                          │
│ Service              │ Deployment                           │
│ Task                 │ Pod                                  │
│ Replicas             │ Replicas                             │
│ Stack (compose YAML) │ Helm chart / kubectl apply           │
│ docker service scale │ kubectl scale deployment             │
│ Rolling update       │ Rolling update                       │
│ docker service update│ kubectl set image / kubectl apply    │
│ --rollback           │ kubectl rollout undo                 │
│ Routing mesh         │ Service (NodePort/LoadBalancer)      │
│ Overlay network      │ CNI plugin (Calico, Flannel, etc.)   │
│ Docker secret        │ Kubernetes Secret                    │
│ Docker config        │ Kubernetes ConfigMap                 │
│ Drain                │ kubectl drain / cordon               │
│ docker node ls       │ kubectl get nodes                    │
│ docker service ls    │ kubectl get deployments              │
│ docker service ps    │ kubectl get pods                     │
│ Raft consensus       │ etcd                                 │
└──────────────────────┴──────────────────────────────────────┘
```

---

## 23.9 Essential kubectl Commands

```bash
# ─── CLUSTER INFO ────────────────────────────────────────
$ kubectl cluster-info
$ kubectl get nodes
$ kubectl get namespaces

# ─── PODS ────────────────────────────────────────────────
$ kubectl get pods                        # List pods
$ kubectl get pods -o wide                # Show node and IP
$ kubectl describe pod <name>             # Detailed info
$ kubectl logs <pod>                      # View logs
$ kubectl logs <pod> -f                   # Follow logs
$ kubectl exec -it <pod> -- /bin/sh       # Shell into pod
$ kubectl delete pod <name>               # Delete pod

# ─── DEPLOYMENTS ─────────────────────────────────────────
$ kubectl get deployments                 # List deployments
$ kubectl describe deployment <name>      # Detailed info
$ kubectl scale deployment <name> --replicas=5
$ kubectl set image deployment/<name> <container>=<image>
$ kubectl rollout status deployment/<name>
$ kubectl rollout history deployment/<name>
$ kubectl rollout undo deployment/<name>

# ─── SERVICES ────────────────────────────────────────────
$ kubectl get services                    # List services
$ kubectl describe service <name>         # Detailed info
$ kubectl expose deployment <name> --port=80 --type=NodePort

# ─── APPLY / DELETE ──────────────────────────────────────
$ kubectl apply -f <file.yaml>            # Create/update
$ kubectl delete -f <file.yaml>           # Delete
$ kubectl apply -f <directory>/           # Apply all YAMLs

# ─── DEBUGGING ───────────────────────────────────────────
$ kubectl get events                      # Cluster events
$ kubectl top nodes                       # Node resource usage
$ kubectl top pods                        # Pod resource usage
```

---

## 23.10 Common Errors and Troubleshooting

### Error 1: Pod Stuck in "Pending"

```bash
$ kubectl get pods
# NAME    READY   STATUS    AGE
# web-1   0/1     Pending   5m

$ kubectl describe pod web-1
# Events:
#   Warning  FailedScheduling  No nodes available to schedule pods

# CAUSES:
#   No nodes with enough resources (CPU/memory)
#   Node taints preventing scheduling
#   PersistentVolumeClaim not bound

# Fix: Check node resources
$ kubectl describe nodes | grep -A5 "Allocated resources"
```

### Error 2: Pod in "CrashLoopBackOff"

```bash
$ kubectl get pods
# NAME    READY   STATUS             RESTARTS   AGE
# web-1   0/1     CrashLoopBackOff   5          10m

# CAUSE: Container starts and immediately crashes
$ kubectl logs web-1
# Check application error messages

$ kubectl logs web-1 --previous
# Logs from the previous (crashed) container
```

### Error 3: Pod in "ImagePullBackOff"

```bash
$ kubectl get pods
# NAME    READY   STATUS             AGE
# web-1   0/1     ImagePullBackOff   5m

# CAUSE: Cannot pull the container image
# Fix: Check image name, tag, and registry credentials
$ kubectl describe pod web-1 | grep -A3 "Events"
```

---

## Module 23 Summary

- Kubernetes is the industry-standard container orchestration platform
- **Control plane** (master): API server, etcd, scheduler, controller manager
- **Worker nodes**: kubelet, kube-proxy, container runtime
- **Pod** is the smallest deployable unit — one or more containers sharing network and storage
- **ReplicaSet** maintains a desired number of pod replicas — rarely created directly
- **Deployment** manages ReplicaSets and provides rolling updates and rollbacks — the standard way to run apps
- **Services** provide stable network endpoints for pods: ClusterIP (internal), NodePort (external port), LoadBalancer (cloud LB)
- **Namespaces** partition a cluster into virtual sub-clusters with separate scope
- `kubectl apply -f` is the declarative way to create/update resources
- `kubectl scale`, `kubectl set image`, `kubectl rollout undo` manage deployments
- Swarm concepts map directly to K8s: Service→Deployment, Task→Pod, Stack→Helm chart
- Debugging: `kubectl describe`, `kubectl logs`, `kubectl get events`
- Common pod issues: Pending (scheduling), CrashLoopBackOff (app crash), ImagePullBackOff (image not found)

---

**Previous Module: [Module 22 - Disaster Recovery](module-22-disaster-recovery.md)**

**Next Module: [Module 24 - Kubernetes Storage & Networking](module-24-kubernetes-storage-networking.md)**
