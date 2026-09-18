# MODULE 10: Pods — The Smallest Deployable Unit

---

## 10.1 Pods — The Smallest Unit

A Pod is the smallest deployable unit in Kubernetes. It wraps one or more containers that share networking and storage.

**Real-life analogy:** A Pod is like a hotel room — it can have one or more guests (containers) who share the same room number (IP address), bathroom (storage), and phone line (network).

**Key facts about Pods:**
- Each Pod gets its own IP address (assigned by the CNI plugin)
- Containers within a Pod share the same network namespace (they communicate via `localhost`)
- Containers within a Pod share the same storage volumes
- Pods are ephemeral — when a Pod dies, it gets a new IP address
- Pods are not self-healing — use Deployments/ReplicaSets for automatic restart
- The `restartPolicy` field controls what happens when a container exits: `Always` (default), `OnFailure`, or `Never`

**Scaling = more Pods, not more containers in a Pod:**

Scaling in Kubernetes means creating additional Pods, not adding more containers to an existing Pod. Each Pod runs one instance of your application:

```
Scaling UP:
  1 user  → 1 Pod (1 container)
  ↓ load increases
  100 users → 3 Pods (1 container each) across 2 nodes

Scaling DOWN:
  Load decreases → Kubernetes removes Pods (not containers within a Pod)
```

Multi-container Pods are for tightly coupled helper containers (sidecars), not for running multiple instances of the same application.

**Why Pods instead of raw containers?**

Without Pods, managing multi-container applications with Docker requires manual linking:

```bash
# Without Kubernetes — manual container management
docker run -d --name app1 python-app
docker run -d --name app2 python-app
docker run -d --name helper1 --link app1 log-collector
docker run -d --name helper2 --link app2 log-collector
# You must manually manage networks, volumes, restarts, and lifecycle
```

With Pods, containers that need to work together are grouped automatically — they share the same network namespace (localhost), storage volumes, and lifecycle. Kubernetes handles all the orchestration.

**What happens internally when a Pod is created:**
1. API Server receives the Pod spec and stores it in etcd
2. Scheduler assigns the Pod to a node
3. kubelet on that node detects the new Pod
4. kubelet instructs the container runtime to pull the image
5. Container runtime creates and starts the container(s)
6. kubelet reports Pod status back to the API Server

### Single-Container Pod

```yaml
# simple-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
    environment: dev
spec:
  containers:
  - name: nginx
    image: nginx:1.25
    ports:
    - containerPort: 80
    resources:
      requests:
        cpu: "100m"        # 0.1 CPU core
        memory: "128Mi"    # 128 MB RAM
      limits:
        cpu: "250m"        # 0.25 CPU core max
        memory: "256Mi"    # 256 MB RAM max
```

```bash
# Create the pod
kubectl apply -f simple-pod.yaml

# Output:
# pod/nginx-pod created

# Check pod status
kubectl get pod nginx-pod

# Output:
# NAME        READY   STATUS    RESTARTS   AGE
# nginx-pod   1/1     Running   0          30s

# Detailed pod info
kubectl describe pod nginx-pod

# Output (key sections):
# Name:         nginx-pod
# Namespace:    default
# Node:         ip-10-0-1-100.ec2.internal/10.0.1.100
# Status:       Running
# IP:           10.0.1.15
# Containers:
#   nginx:
#     Image:          nginx:1.25
#     Port:           80/TCP
#     State:          Running
#     Ready:          True
#     Requests:
#       cpu:        100m
#       memory:     128Mi
#     Limits:
#       cpu:        250m
#       memory:     256Mi
# Events:
#   Type    Reason     Age   Message
#   Normal  Scheduled  30s   Successfully assigned default/nginx-pod to ip-10-0-1-100
#   Normal  Pulled     28s   Container image "nginx:1.25" already present
#   Normal  Created    28s   Created container nginx
#   Normal  Started    27s   Started container nginx
```

### Pod with Environment Variables

```yaml
# env-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: environments
spec:
  containers:
  - name: c00
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do echo $ORG-$SESSION; sleep 5; done"]
    env:
    - name: ORG
      value: MYCOMPANY
    - name: SESSION
      value: PODS
```

```bash
kubectl apply -f env-pod.yaml

# Verify environment variables inside the pod
kubectl exec environments -- env

# Output (includes):
# ORG=MYCOMPANY
# SESSION=PODS
```

### Pod with Port Exposure

```yaml
# port-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: portexpose
spec:
  containers:
  - name: c00
    image: httpd
    ports:
    - containerPort: 80
```

```bash
kubectl apply -f port-pod.yaml

# Get the pod IP and test
kubectl get pod portexpose -o wide

# Output:
# NAME         READY   STATUS    RESTARTS   AGE   IP           NODE
# portexpose   1/1     Running   0          30s   10.0.1.20    ip-10-0-1-100

# Access from within the cluster
curl <podIP>:80
```

### Pod Labels and Selectors

Labels are key-value pairs attached to pods for organizing and selecting resources. They are the primary mechanism Kubernetes uses to connect objects together.

**Why labels matter:**
- Services use label selectors to find which pods to route traffic to
- Deployments use label selectors to manage which pods belong to them
- Network policies use labels to define traffic rules
- You can filter, group, and bulk-operate on resources by label

**Labels vs Annotations:**
- **Labels** — used for selection and grouping (e.g., `app: nginx`, `env: prod`)
- **Annotations** — used for non-identifying metadata (e.g., `description: "web server"`, `last-deployed-by: "CI"`)

**Common mistake:** If a Service's selector doesn't match any pod labels, the Service has no endpoints and traffic goes nowhere. Always verify labels match with `kubectl get pods --show-labels`.

```yaml
# labeled-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: labelspod
  labels:
    myname: ADAM
    myorg: WEZVATECH
spec:
  containers:
  - name: c00
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
```

```bash
kubectl apply -f labeled-pod.yaml

# Show labels on pods
kubectl get pods --show-labels

# Filter by label
kubectl get pods -l myname=ADAM

# Filter by label inequality
kubectl get pods -l myname!=ADAM

# Filter using set-based selectors
kubectl get pods -l 'myname in (ADAM, student)'
kubectl get pods -l 'myname notin (ADAM, student)'

# Add a label to an existing pod
kubectl label pods testpod myname=student

# Delete pods by label
kubectl delete pod -l 'myname in (ADAM, student)'

# Count pods matching a label (--no-headers removes the header row)
kubectl get pods --selector env=dev --no-headers | wc -l

# Filter with multiple labels (comma-separated = AND logic)
kubectl get pods --selector env=prod,bu=finance,tier=frontend

# Count ALL objects (pods, services, replicasets) matching a label
kubectl get all --selector env=prod --no-headers | wc -l
```

**Annotations — storing non-identifying metadata:**

Annotations attach metadata that Kubernetes does not use for selection. They store build info, tool versions, contact details, or any other context:

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: simple-webapp
  labels:
    app: App1
    function: Front-end
  annotations:
    buildversion: "1.34"
    last-deployed-by: "CI/CD pipeline"
    contact: "platform-team@company.com"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: App1
  template:
    metadata:
      labels:
        app: App1
        function: Front-end
    spec:
      containers:
      - name: simple-webapp
        image: simple-webapp:1.34
```

```bash
# View annotations on a resource
kubectl describe replicaset simple-webapp | grep -A3 Annotations

# Output:
# Annotations:  buildversion: 1.34
#               contact: platform-team@company.com
#               last-deployed-by: CI/CD pipeline

# Add an annotation imperatively
kubectl annotate pod labelspod description="web frontend pod"

# Remove an annotation (note the minus sign)
kubectl annotate pod labelspod description-
```

**Labels appear in two places in ReplicaSets/Deployments:**

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: webapp
  labels:
    app: webapp           # 1. Labels on the ReplicaSet ITSELF (for other objects to find it)
spec:
  selector:
    matchLabels:
      app: webapp         # Selector — must match template labels below
  template:
    metadata:
      labels:
        app: webapp       # 2. Labels on the PODS (used by selector to identify managed pods)
    spec:
      containers:
      - name: webapp
        image: webapp:latest
```

- **metadata.labels** — labels on the ReplicaSet object itself (used if another object needs to reference the ReplicaSet)
- **spec.template.metadata.labels** — labels on the pods created by the ReplicaSet
- **spec.selector.matchLabels** — must match the template labels; this is how the ReplicaSet knows which pods it owns

### Node Selectors

Schedule pods on specific nodes using labels.

```yaml
# nodeselector-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: nodelabels
  labels:
    env: dev
spec:
  containers:
  - name: c00
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
  nodeSelector:
    mynode: demonode
```

```bash
# First, label the target node
kubectl label nodes <node-name> mynode=demonode

# Then create the pod — it will only schedule on the labeled node
kubectl apply -f nodeselector-pod.yaml
kubectl get pod nodelabels -o wide
```

### Multi-Container Pods

When breaking a monolithic application into microservices, each service can be deployed and scaled independently. However, some services are tightly coupled — for example, a web server and its logging agent. These should run together in the same pod so they scale as a unit.

**What multi-container pods share:**
- **Lifecycle** — all containers are created and terminated together
- **Network** — containers share the same network namespace and communicate via `localhost` (no need for service discovery)
- **Storage** — containers can access the same volumes

This eliminates the complexity of inter-pod networking and volume sharing for tightly coupled components.

**Sidecar Pattern:**

```yaml
# multi-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-with-logging
  labels:
    app: web
spec:
  containers:
  # Main application container
  - name: web-app
    image: nginx:1.25
    ports:
    - containerPort: 80
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx

  # Sidecar: log collector
  - name: log-collector
    image: busybox:1.36
    command: ["sh", "-c", "tail -f /var/log/nginx/access.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/nginx

  volumes:
  - name: shared-logs
    emptyDir: {}
```

```bash
kubectl apply -f multi-container-pod.yaml

# View logs from specific container
kubectl logs web-with-logging -c log-collector

# Exec into specific container
kubectl exec -it web-with-logging -c web-app -- /bin/bash
```

### Sidecar Containers

A sidecar container runs alongside the main container in the same pod, performing supporting tasks. Its lifecycle starts and ends with the main container. When a pod starts, all containers start at the same time.

**Use cases:**
- Sync data from a remote source (config files, secrets, certificates)
- Log management and forwarding
- Proxy or service mesh agents

**Sidecar for log collection (Deployment):**

```yaml
# sidecar-log-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: logapp-sidecar
spec:
  replicas: 1
  selector:
    matchLabels:
      app: logapp
  template:
    metadata:
      labels:
        app: logapp
    spec:
      volumes:
      - name: log-volume
        emptyDir: {}
      containers:
      - name: log-generator
        image: busybox
        command: ["/bin/sh"]
        args: ["-c", "while true; do date >> /var/log/app.log; sleep 5; done"]
        volumeMounts:
        - name: log-volume
          mountPath: /var/log
      - name: log-reader
        image: busybox
        command: ["/bin/sh"]
        args: ["-c", "tail -f /var/log/app.log"]
        volumeMounts:
        - name: log-volume
          mountPath: /var/log
```

**Sidecar exposing logs via HTTP:**

```yaml
# sidecar-http.yaml
apiVersion: v1
kind: Pod
metadata:
  name: logapp-sidecar-http
  labels:
    sidecar: log
spec:
  volumes:
  - name: logs
    emptyDir: {}
  containers:
  - name: app
    image: ubuntu
    command: ["/bin/sh"]
    args: ["-c", "while true; do date >> /var/log/date.txt; sleep 10; done"]
    volumeMounts:
    - name: logs
      mountPath: /var/log
  - name: sidecar
    image: centos/httpd
    ports:
    - containerPort: 80
    volumeMounts:
    - name: logs
      mountPath: /var/www/html
---
apiVersion: v1
kind: Service
metadata:
  name: sidecar-service
spec:
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
  selector:
    sidecar: log
  type: NodePort
```

```bash
kubectl apply -f sidecar-http.yaml

# Access logs via HTTP
curl localhost:30080/date.txt
```

### Multi-Container Design Patterns

Beyond the sidecar pattern, two other multi-container patterns are commonly tested:

**Adapter Pattern — normalize data before sending it downstream:**

Different application instances may produce logs in different formats. An adapter container standardizes the format before forwarding to a central logging system.

```yaml
# adapter-pattern.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-adapter
spec:
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  - name: log-adapter
    image: log-normalizer
    command: ["sh", "-c", "tail -f /var/log/app/raw.log | normalize > /var/log/app/formatted.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  volumes:
  - name: logs
    emptyDir: {}
```

Use case: multiple microservices produce logs in different formats (JSON, plain text, CSV). The adapter converts them all to a standard format before shipping to Elasticsearch.

**Ambassador Pattern — proxy connections to external services:**

The application always connects to `localhost`, and an ambassador container proxies the request to the correct backend (dev, staging, or production database).

```yaml
# ambassador-pattern.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-ambassador
spec:
  containers:
  - name: app
    image: my-app
    env:
    - name: DB_HOST
      value: "localhost"    # App always connects to localhost
    - name: DB_PORT
      value: "3306"
  - name: db-ambassador
    image: haproxy:2.8
    ports:
    - containerPort: 3306
    # Ambassador proxies localhost:3306 → actual database endpoint
    # Configuration determines which DB (dev/staging/prod) based on environment
```

Use case: the application code doesn't need environment-specific connection logic. Swap the ambassador's config to point to a different database without changing the app.

**Pattern comparison:**

| Pattern | Purpose | Example |
|---|---|---|
| **Sidecar** | Extend/enhance the main container | Log collector, config reloader, TLS proxy |
| **Adapter** | Standardize output format | Log format normalizer, metrics converter |
| **Ambassador** | Proxy external connections | DB proxy, API gateway, service mesh proxy |

### Container Lifecycle Hooks

Kubernetes exposes two hooks for containers:

- **PostStart** — executed immediately after a container is created. The container status is not set to Running until the handler completes.
- **PreStop** — called immediately before a container is terminated (due to API request, liveness probe failure, etc.)

```yaml
# lifecycle-hooks.yaml
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo
spec:
  containers:
  - name: lifecycle-demo-container
    image: nginx
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo Hello from postStart > /usr/share/message"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "nginx -s quit; while killall -0 nginx; do sleep 1; done"]
```

```bash
kubectl apply -f lifecycle-hooks.yaml
kubectl describe pod lifecycle-demo

# Verify postStart ran
kubectl exec lifecycle-demo -- cat /usr/share/message
# Output: Hello from postStart
```

### Pod Lifecycle

```
Pending → Running → Succeeded/Failed
   │         │
   │         └── Container crashes → CrashLoopBackOff
   └── Image pull fails → ImagePullBackOff
```

**Pod phases explained:**

| Phase | Meaning | Common Causes |
|---|---|---|
| `Pending` | Pod accepted but not yet scheduled or image not pulled | No node has enough resources, image is being pulled, PVC not bound |
| `ContainerCreating` | Pod scheduled, containers being set up | Image pull in progress, volume mounting |
| `Running` | At least one container is running | Normal operation |
| `Succeeded` | All containers exited with code 0 | Jobs, init containers |
| `Failed` | All containers terminated, at least one exited non-zero | Application error, OOMKilled |
| `CrashLoopBackOff` | Container keeps crashing and restarting | Application bug, missing config, wrong command |
| `ImagePullBackOff` | Cannot pull the container image | Wrong image name, private registry without credentials, image doesn't exist |
| `OOMKilled` | Container exceeded memory limit | Memory limit too low, or application has a memory leak |

**Understanding the READY column (X/Y format):**

The `READY` column shows `X/Y` where X = containers ready, Y = total containers in the pod:

```bash
kubectl get pods

# NAME      READY   STATUS             RESTARTS   AGE
# app1      1/1     Running            0          5m    ← 1 container, 1 ready (healthy)
# webapp    1/2     ImagePullBackOff   0          15s   ← 2 containers, only 1 ready
# worker    0/1     CrashLoopBackOff   3          2m    ← 1 container, 0 ready (crashing)
```

| READY | Meaning |
|---|---|
| `1/1` | Single-container pod, container is ready |
| `2/2` | Multi-container pod, both containers ready |
| `1/2` | Multi-container pod, one container has a problem |
| `0/1` | Container is not ready (starting, crashing, or failing probes) |

```bash
# Watch pod lifecycle in real-time
kubectl get pods -w

# Output:
# NAME        READY   STATUS              RESTARTS   AGE
# nginx-pod   0/1     Pending             0          0s
# nginx-pod   0/1     ContainerCreating   0          1s
# nginx-pod   1/1     Running             0          3s

# Debugging a failed pod
kubectl describe pod <pod-name>     # Check Events section at the bottom
kubectl logs <pod-name>             # Check application logs
kubectl logs <pod-name> --previous  # Logs from the previous crashed container
```

**Troubleshooting: Fix a pod with the wrong image**

A common workflow — create a pod with a wrong image, then fix it:

```bash
# Step 1: Generate YAML with a wrong image (simulating a typo)
kubectl run redis --image=redis123 --dry-run=client -o yaml > redis.yaml

# Step 2: Create the pod
kubectl create -f redis.yaml

# Step 3: Check status — ErrImagePull because redis123 doesn't exist
kubectl get pods
# NAME    READY   STATUS         RESTARTS   AGE
# redis   0/1     ErrImagePull   0          10s

# Step 4: Fix the image in the YAML file (redis123 → redis)
# Edit redis.yaml and change image: redis123 to image: redis

# Step 5: Reapply
kubectl apply -f redis.yaml

# Step 6: Verify — pod is now running
kubectl get pods
# NAME    READY   STATUS    RESTARTS   AGE
# redis   1/1     Running   0          30s
```

### Understanding Container Image Names

When you specify `image: nginx` in a pod spec, Docker expands this to the full path:

```
nginx
  → library/nginx           (default account: "library" = Docker official images)
  → docker.io/library/nginx (default registry: docker.io = Docker Hub)
```

**Image name structure:** `registry/account/image:tag`

| You Write | Docker Resolves To | Registry | Account | Image |
|---|---|---|---|---|
| `nginx` | `docker.io/library/nginx:latest` | Docker Hub | library (official) | nginx |
| `myuser/myapp` | `docker.io/myuser/myapp:latest` | Docker Hub | myuser | myapp |
| `gcr.io/google-samples/hello-app:1.0` | (as written) | Google Container Registry | google-samples | hello-app |
| `123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:v2` | (as written) | AWS ECR | (account ID) | myapp |

The `library` account is Docker's official image repository — images there are reviewed and maintained by Docker. When you create your own Docker Hub account, your images use `your-account/image-name`.

### Init Containers

Init containers run before the main containers start. Used for setup tasks.

**How init containers work:**
1. Init containers run sequentially (one at a time, in order)
2. Each init container must complete successfully (exit code 0) before the next one starts
3. If an init container fails, Kubernetes restarts the Pod (subject to `restartPolicy`)
4. Only after ALL init containers succeed does the main container start
5. Init containers do NOT support liveness, readiness, or startup probes

**Common use cases:**
- **Wait for dependencies** — wait for a database or service to be available before starting the app
- **Clone a git repo** — download application code or config before the main container starts
- **Seed a database** — run migrations or seed data
- **Generate config files** — create configuration from templates

**Interview question: What's the difference between init containers and sidecar containers?**
- Init containers run to completion before the main container starts, then terminate
- Sidecar containers run alongside the main container for the entire Pod lifetime

```yaml
# init-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup postgres-service.default.svc.cluster.local; do echo "Waiting for DB..."; sleep 2; done']

  - name: init-schema
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Schema initialized" > /work-dir/status']
    volumeMounts:
    - name: workdir
      mountPath: /work-dir

  containers:
  - name: app
    image: nginx:1.25
    volumeMounts:
    - name: workdir
      mountPath: /usr/share/nginx/html

  volumes:
  - name: workdir
    emptyDir: {}
```

```bash
kubectl apply -f init-container-pod.yaml
kubectl get pod app-with-init

# Output (init containers run sequentially):
# NAME            READY   STATUS     RESTARTS   AGE
# app-with-init   0/1     Init:0/2   0          5s    ← First init running
# app-with-init   0/1     Init:1/2   0          10s   ← Second init running
# app-with-init   1/1     Running    0          15s   ← Main container running
```

**Init container with shared volume** — the init container writes data that the main container reads:

```yaml
# init-volume-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: initpod
spec:
  initContainers:
  - name: init
    image: centos
    command: ["/bin/sh", "-c", "echo KUBERNETES-INIT > /tmp/xchange/testfile; sleep 30"]
    volumeMounts:
    - name: xchange
      mountPath: "/tmp/xchange"
  containers:
  - name: main
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do cat /tmp/data/testfile; sleep 5; done"]
    volumeMounts:
    - name: xchange
      mountPath: "/tmp/data"
  volumes:
  - name: xchange
    emptyDir: {}
```

Key points about init containers:
- They run sequentially, each must complete before the next starts
- The main container only starts after all init containers succeed
- Init containers do not support health checks (liveness/readiness probes)
- The init container is terminated after its command completes
- If the Pod has `restartPolicy: Never`, Kubernetes does not restart the Pod when an init container fails

#### Init Containers — Key Rules

| Rule | Detail |
|---|---|
| Run before app containers | Init containers always execute first, before any main container starts |
| Run to completion | Each init container must exit successfully (exit code 0) |
| Sequential execution | Each init container must complete before the next one starts |
| Pod restart on failure | If an init container fails, Kubernetes restarts the Pod until it succeeds |
| `restartPolicy: Never` | Exception — Pod is NOT restarted if restartPolicy is Never |
| No probes | Init containers do not support liveness, readiness, or startup probes |
| Utilities/scripts | Init containers can contain utilities or setup scripts not present in the app image |

#### The `nc -z` Command (netcat)

Init containers commonly use `nc -z` to check if a dependency is available before starting the main container:

```bash
nc -z <host> <port>
```

| Flag | Meaning |
|---|---|
| `-z` | Zero I/O mode — scan for open ports without sending data |

`nc -z mysql 3306` checks if MySQL is listening on port 3306. Returns exit code 0 if the port is open, non-zero if not. Combined with a `while` loop, it waits until the dependency is ready:

```yaml
initContainers:
  - name: init-db
    image: busybox:1.31
    command: ['sh', '-c', 'echo -e "Checking for the availability of MySQL Server deployment"; while ! nc -z mysql 3306; do sleep 1; printf "-"; done; echo -e "  >> MySQL DB Server has started";']
```

**What this does step by step:**
1. Prints "Checking for the availability of MySQL Server deployment"
2. Runs `nc -z mysql 3306` — checks if MySQL service is reachable on port 3306
3. If not reachable (`!` negates the result), sleeps 1 second and prints `-`
4. Repeats until MySQL is available
5. Prints "MySQL DB Server has started" and exits with code 0
6. Main container starts

#### Deploy and Test Init Containers

```bash
# Create all objects
kubectl apply -f kube-manifests/

# List pods — watch the init container phase
kubectl get pods
kubectl get pods -w

# Output during startup:
# NAME                                    READY   STATUS     RESTARTS   AGE
# usermgmt-microservice-7b4d6f8c9-abc12   0/1     Init:0/1   0          5s    ← Init container running
# usermgmt-microservice-7b4d6f8c9-abc12   0/1     PodInitializing   0   30s   ← Init done, main starting
# usermgmt-microservice-7b4d6f8c9-abc12   1/1     Running    0          35s   ← Main container running

# Describe pod to see init container details
kubectl describe pod <usermgmt-microservice-xxxxxx>

# Look for the "Init Containers" section in the output:
#   Init Containers:
#     init-db:
#       Image:   busybox:1.31
#       Command: sh -c ...
#       State:   Terminated
#         Reason: Completed
#         Exit Code: 0

# Access application
# http://<WorkerNode-Public-IP>:31231/usermgmt/health-status

# Clean up
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

#### Lab: Init Containers Troubleshooting

**Exercise 1: Identify which pods have init containers**

```bash
kubectl get pods
```

```
NAME    READY   STATUS    RESTARTS   AGE
red     1/1     Running   0          23s
green   2/2     Running   0          23s
blue    1/1     Running   0          23s
```

Use `kubectl describe` to check for an "Init Containers" section:

```bash
kubectl describe pod blue | grep -A10 "Init Containers"
```

```
Init Containers:
  init-myservice:
    Image:         busybox
    Command:
      sh
      -c
      sleep 5
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
```

The blue pod has an init container. The red and green pods only have regular containers (no "Init Containers" section in their describe output).

**Exercise 2: Diagnose `Init:CrashLoopBackOff`**

```bash
kubectl get pod orange
```

```
NAME     READY   STATUS                  RESTARTS      AGE
orange   0/1     Init:CrashLoopBackOff   1 (12s ago)   15s
```

Check the init container logs:

```bash
kubectl logs orange -c init-myservice
```

```
sh: sleepee: not found
```

The command `sleepee` is misspelled. Fix it:

```yaml
# Corrected init container
initContainers:
- name: init-myservice
  image: busybox
  command:
  - sh
  - -c
  - sleep 2       # Fixed: was "sleepee 2"
```

```bash
kubectl replace --force -f /tmp/kubectl-edit-orange.yaml
```

```
pod "orange" deleted
pod/orange replaced
```

```bash
kubectl get pod orange
```

```
NAME     READY   STATUS    RESTARTS   AGE
orange   1/1     Running   0          27s
```

**Exercise 3: Add an init container to an existing pod**

Add a busybox init container that sleeps for 20 seconds before the main container starts:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: red
spec:
  initContainers:
  - name: init-warmup
    image: busybox
    command: ["sleep", "20"]
  containers:
  - name: red-container
    image: busybox:1.28
    command: ["sh", "-c", "echo The app is running! && sleep 3600"]
```

```bash
kubectl replace --force -f red-pod.yaml
kubectl get pod red -w
```

```
NAME   READY   STATUS     RESTARTS   AGE
red    0/1     Init:0/1   0          2s
red    0/1     PodInitializing   0   22s
red    1/1     Running    0          24s
```

The init container ran for 20 seconds, then the main container started.

### Pulling Images from a Private Container Registry

By default, Kubernetes pulls images from public registries (Docker Hub). For private registries (ECR, ACR, GCR, private Docker Hub), you need to configure authentication.

```bash
# Authenticate with a private registry (Docker CLI)
docker login private-registry.io
# Username: registry-user
# Password: ********
# Login Succeeded
```

**Method 1: AWS ECR with IRSA (recommended for EKS)**

```bash
# On EKS, the easiest approach is to use the ECR credential helper
# which is built into the VPC-CNI and kubelet

# Step 1: Ensure the node IAM role has ECR pull permissions
# The managed node group's IAM role needs:
# - AmazonEC2ContainerRegistryReadOnly policy

# Step 2: Use the full ECR image path in your deployment
# No imagePullSecrets needed — kubelet auto-authenticates via instance role
```

```yaml
# deployment-ecr.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.0.0
        #       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #       Full ECR image URI — kubelet authenticates via node IAM role
        ports:
        - containerPort: 8080
```

```bash
kubectl apply -f deployment-ecr.yaml

kubectl get pods

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# myapp-7b8c9d6e8-abc12    1/1     Running   0          30s

# If you see ImagePullBackOff, check the node's IAM role:
kubectl describe pod myapp-7b8c9d6e8-abc12 | grep -A5 "Events"

# Output (if IAM role is missing):
# Events:
#   Warning  Failed  kubelet  Failed to pull image: AccessDeniedException
```

**Method 2: imagePullSecrets (works with any registry)**

```bash
# Step 1: Create a docker-registry secret
kubectl create secret docker-registry ecr-secret \
  --docker-server=123456789012.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1)

# For Docker Hub private repos:
kubectl create secret docker-registry dockerhub-secret \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=myuser@example.com

# For Azure ACR:
kubectl create secret docker-registry acr-secret \
  --docker-server=myregistry.azurecr.io \
  --docker-username=<service-principal-id> \
  --docker-password=<service-principal-password>
```

```yaml
# pod-with-pull-secret.yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-app
spec:
  containers:
  - name: app
    image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.0.0
  imagePullSecrets:
  - name: ecr-secret          # References the docker-registry secret
```

```bash
kubectl apply -f pod-with-pull-secret.yaml

# Verify
kubectl get pod private-app

# Output:
# NAME          READY   STATUS    RESTARTS   AGE
# private-app   1/1     Running   0          15s
```

**Method 3: Attach imagePullSecrets to a ServiceAccount (avoid repeating in every pod)**

```bash
# Patch the default service account to always use the pull secret
kubectl patch serviceaccount default -p '{"imagePullSecrets": [{"name": "ecr-secret"}]}'

# Now ALL pods using the default service account automatically get the pull secret
# No need to add imagePullSecrets to every pod spec
```

**ECR token expiration problem:**

```bash
# ECR tokens expire after 12 hours!
# The kubectl create secret command creates a static token

# Solutions:
# 1. Use node IAM role (Method 1) — no token needed
# 2. Use a CronJob to refresh the secret every 6 hours:
kubectl create cronjob ecr-token-refresh \
  --image=amazon/aws-cli \
  --schedule="0 */6 * * *" \
  -- /bin/sh -c 'kubectl create secret docker-registry ecr-secret \
     --docker-server=$ECR_REGISTRY \
     --docker-username=AWS \
     --docker-password=$(aws ecr get-login-password) \
     --dry-run=client -o yaml | kubectl apply -f -'
```

**Method 4: AKS + Azure ACR (recommended for Azure)**

```bash
# Attach ACR to AKS using managed identity — no imagePullSecret needed
az aks update -g myResourceGroup -n myAKSCluster --attach-acr myACRName

# Output:
# ... "acrProfile": { "registries": [{ "name": "myACRName" }] } ...

# Now pods can pull from myACRName.azurecr.io without any secrets
# The AKS managed identity gets AcrPull role automatically
```

```yaml
# deployment-acr.yaml — no imagePullSecrets needed after attach-acr
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myACRName.azurecr.io/myapp:v1.0.0    # Full ACR image path
        ports:
        - containerPort: 8080
```

**Private registry comparison:**

| Registry | Auth Method | Token Expiry | Best Approach |
|---|---|---|---|
| **AWS ECR** | Node IAM role | N/A (auto) | IRSA or node role (no secret needed) |
| **AWS ECR** | imagePullSecrets | 12 hours | CronJob to refresh token |
| **Azure ACR** | AKS managed identity | N/A (auto) | `az aks update --attach-acr` |
| **Azure ACR** | Service principal | Configurable | imagePullSecrets |
| **Docker Hub** | imagePullSecrets | No expiry | Patch default ServiceAccount |
| **GCR** | Workload Identity | N/A (auto) | GKE Workload Identity |

**Interview question: How do you pull images from a private container registry in Kubernetes?**
Three approaches: (1) On EKS, use the node's IAM role with ECR pull permissions — kubelet authenticates automatically, no secrets needed. (2) Create a `docker-registry` Secret with `kubectl create secret docker-registry` and reference it in `imagePullSecrets` in the pod spec. (3) Patch the default ServiceAccount to include the pull secret so all pods get it automatically. For ECR, prefer the IAM role approach since ECR tokens expire after 12 hours.

**Kubernetes secret types for registries:**

| Secret Type | Command | Use Case |
|---|---|---|
| `docker-registry` | `kubectl create secret docker-registry` | Authenticating with container registries |
| `generic` | `kubectl create secret generic` | Arbitrary key-value data (env vars, config files) |
| `tls` | `kubectl create secret tls` | TLS certificates for Ingress or apps |

### Lab: Securing Images with a Private Registry

This lab walks through switching a deployment from a public image to a private registry, diagnosing the resulting `ImagePullBackOff`, and fixing it with a docker-registry secret.

**Step 1: Inspect the current deployment**

```bash
kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# web    2/2     2            2           48s

kubectl describe deploy web | grep Image
#     Image:  nginx:alpine
```

**Step 2: Update the image to use a private registry**

```bash
kubectl set image deployment/web nginx=myprivateregistry.com:5000/nginx:alpine
# deployment.apps/web image updated
```

**Step 3: Observe the failure**

```bash
kubectl get pods
# NAME                     READY   STATUS             RESTARTS   AGE
# web-85fcf65896-rbsmq     0/1     ImagePullBackOff   0          20s
# web-bd975bd87-jjbnx      1/1     Running            0          2m
# web-bd975bd87-mf9vg      1/1     Running            0          2m

kubectl describe pod web-85fcf65896-rbsmq | grep -A3 "Warning"
# Warning  Failed  kubelet  Failed to pull image
#   "myprivateregistry.com:5000/nginx:alpine": unauthorized: authentication required
```

The old pods keep running (rolling update strategy), but the new pod can't pull the image because no credentials are configured.

**Step 4: Create a docker-registry secret**

```bash
kubectl create secret docker-registry private-reg-cred \
  --docker-server=myprivateregistry.com:5000 \
  --docker-username=dock_user \
  --docker-password=dock_password \
  --docker-email=dock_user@myprivateregistry.com
# secret/private-reg-cred created
```

**Step 5: Add imagePullSecrets to the deployment**

```bash
kubectl edit deploy web
```

Add `imagePullSecrets` under `spec.template.spec`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: myprivateregistry.com:5000/nginx:alpine
      imagePullSecrets:
      - name: private-reg-cred
```

**Step 6: Verify the fix**

```bash
kubectl get pods
# NAME                     READY   STATUS    RESTARTS   AGE
# web-6d8f9c7b5-abc12      1/1     Running   0          15s
# web-6d8f9c7b5-def34      1/1     Running   0          12s

kubectl describe pod web-6d8f9c7b5-abc12 | grep "Successfully pulled"
# Normal  Pulled  kubelet  Successfully pulled image
#   "myprivateregistry.com:5000/nginx:alpine"
```

**Interview question: What happens when you delete a pod managed by a Deployment?**
The ReplicaSet controller detects that actual replicas < desired replicas, and immediately creates a replacement pod. The scheduler assigns it to a node, and kubelet starts it. The deleted pod's IP is released and the new pod gets a different IP.

**Lab: Multi-Container Pods**

**Exercise 1: Identify containers in a pod using the READY column**

```bash
kubectl get pods
```

```
NAME    READY   STATUS    RESTARTS   AGE
red     3/3     Running   0          23s
blue    2/2     Running   0          23s
```

The READY column shows `3/3` for red (3 containers) and `2/2` for blue (2 containers). Use `kubectl describe` to see container names:

```bash
kubectl describe pod red | grep -A2 "Containers:" | head -10
```

```
Containers:
  apple:
    Image:   busybox
  wine:
    Image:   busybox
  scarlet:
    Image:   busybox
```

**Exercise 2: Create a multi-container pod from dry-run**

```bash
# Generate a single-container pod YAML
kubectl run yellow --image=busybox --dry-run=client -o yaml > yellow.yaml
```

Edit `yellow.yaml` to rename the container and add a second one:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: yellow
spec:
  containers:
  - name: lemon
    image: busybox
    command: ["sleep", "1000"]
  - name: gold
    image: redis
```

```bash
kubectl apply -f yellow.yaml
kubectl get pod yellow
```

```
NAME     READY   STATUS    RESTARTS   AGE
yellow   2/2     Running   0          10s
```

**Exercise 3: Add a sidecar container for log shipping to Elasticsearch**

An application pod writes logs to `/log/app.log`. Add a Filebeat sidecar to ship logs to Elasticsearch:

```bash
# View logs inside the pod
kubectl -n elastic-stack exec -it app -- cat /log/app.log
```

```
[2024-01-15 10:00:01] INFO - USER1 logged in
[2024-01-15 10:00:02] INFO - USER2 is viewing page3
[2024-01-15 10:00:03] WARNING - USER5 Failed to Login as the account is locked
```

Edit the pod to add a sidecar sharing the same log volume:

```bash
kubectl edit pod app -n elastic-stack
```

```yaml
# Add sidecar container sharing the log volume
spec:
  containers:
  - name: app
    image: kodekloud/event-simulator
    volumeMounts:
    - name: log-volume
      mountPath: /log
  - name: sidecar
    image: kodekloud/filebeat-configured
    volumeMounts:
    - name: log-volume
      mountPath: /var/log/event-simulator/
  volumes:
  - name: log-volume
    emptyDir: {}
```

Since pods are immutable, force-replace:

```bash
kubectl replace --force -f /tmp/kubectl-edit-3922970489.yaml
```

```
pod "app" deleted
pod/app replaced
```

The sidecar reads logs from the shared volume and ships them to Elasticsearch. Verify in Kibana by creating a `filebeat-*` index pattern.

### Pod Examples Walkthrough (pod1 → pod6)

The following six pod patterns cover the most common use cases. Each builds on the previous one.

#### Pod 1 — Basic Pod with Infinite Loop

```yaml
# pod1.yml
kind: Pod
apiVersion: v1
metadata:
  name: testpod
spec:
  containers:
    - name: c00
      image: ubuntu
      command: ["/bin/bash", "-c", "while true; do echo Hello-Adam; sleep 8; done"]
  restartPolicy: Never
```

**Behavior:** Single container running an infinite loop, printing `Hello-Adam` every 8 seconds. `restartPolicy: Never` means the container will not restart if it exits or is stopped.

```bash
kubectl apply -f pod1.yml
kubectl get pods
kubectl logs -f testpod

# Output:
# Hello-Adam
# Hello-Adam
# Hello-Adam
# ...

# Check container details
kubectl describe pod testpod

# Delete the pod
kubectl delete -f pod1.yml
```

**Why `restartPolicy: Never`?** Useful for one-time tasks or debugging. In production, Pods managed by Deployments use `Always` (the default). `Never` is typically used with Jobs.

**What happens when the container exits with `Never`?** The pod moves to `Succeeded` (exit code 0) or `Failed` (non-zero exit code) and stays in that state permanently.

#### Pod 2 — Environment Variables

```yaml
# pod2.yml
kind: Pod
apiVersion: v1
metadata:
  name: envpod
spec:
  containers:
    - name: c01
      image: ubuntu
      command: ["/bin/bash", "-c", "while true; do echo $ORG-$SESSION; sleep 5; done"]
      env:
        - name: ORG
          value: WEZVATECH
        - name: SESSION
          value: PODS
```

**Behavior:** Container prints the values of `ORG` and `SESSION` environment variables every 5 seconds. `restartPolicy` defaults to `Always` (not specified = default).

```bash
kubectl apply -f pod2.yml

kubectl logs envpod
# Output:
# WEZVATECH-PODS
# WEZVATECH-PODS
# ...

# Verify all environment variables inside the container
kubectl exec envpod -- env
# Output includes:
# ORG=WEZVATECH
# SESSION=PODS
# PATH=/usr/local/sbin:/usr/local/bin:...
# HOSTNAME=envpod
# KUBERNETES_SERVICE_HOST=10.96.0.1
# ...
```

**Note:** Kubernetes automatically injects several environment variables into every container, including `KUBERNETES_SERVICE_HOST` and `KUBERNETES_SERVICE_PORT` for API server access.

**When to use env vars vs ConfigMaps:** Use `env` for simple, pod-specific values. Use ConfigMaps for shared configuration across multiple pods. Use Secrets for sensitive values.

#### Pod 3 — Multi-Container Pod

```yaml
# pod3.yml
kind: Pod
apiVersion: v1
metadata:
  name: multipod
spec:
  containers:
    - name: main
      image: ubuntu
      command: ["/bin/bash", "-c", "while true; do echo Hello-Main; sleep 10; done"]
    - name: sidecar
      image: centos
      command: ["/bin/bash", "-c", "while true; do echo Hello-Sidecar; sleep 10; done"]
```

**Behavior:** Two containers in the same pod. They share the same network namespace (same IP, can communicate via `localhost`) and can share volumes.

```bash
kubectl apply -f pod3.yml

# Must specify container name with -c for multi-container pods
kubectl logs -f multipod -c main
# Output:
# Hello-Main
# Hello-Main
# ...

kubectl logs -f multipod -c sidecar
# Output:
# Hello-Sidecar
# Hello-Sidecar
# ...

# Without -c flag, you get an error:
kubectl logs multipod
# error: a container name must be specified for pod multipod,
# choose one of: [main sidecar]

# Exec into a specific container
kubectl exec multipod -c main -it -- /bin/bash
```

**Key behavior:** Both containers start at the same time. If one container crashes, only that container is restarted (not the entire pod). The pod's `READY` column shows `2/2` when both containers are running.

**When to use multi-container pods:** When containers are tightly coupled and must share the same network/storage. Common patterns: sidecar (logging, monitoring), ambassador (proxy), adapter (format conversion).

#### Pod 4 — Labels and Node Selector

```yaml
# pod4.yml
kind: Pod
apiVersion: v1
metadata:
  name: labeledpod
  labels:
    myname: ADAM
    myorg: WEZVATECH
spec:
  nodeSelector:
    mynode: demonode
  containers:
    - name: c04
      image: ubuntu
      command: ["/bin/bash", "-c", "while true; do echo labeledpod; sleep 10; done"]
```

**Behavior:** Pod has two labels (`myname`, `myorg`) and a `nodeSelector` that restricts scheduling to nodes with label `mynode=demonode`.

```bash
# First, label the target node
kubectl label nodes <node-name> mynode=demonode

# Then create the pod
kubectl apply -f pod4.yml

# Pod stays Pending until a matching node exists
kubectl get pods
# Output (before labeling node):
# NAME         READY   STATUS    RESTARTS   AGE
# labeledpod   0/1     Pending   0          30s

# Output (after labeling node):
# NAME         READY   STATUS    RESTARTS   AGE
# labeledpod   1/1     Running   0          45s

# Filter pods by label
kubectl get pods -l myname=ADAM
kubectl get pods --show-labels

# Describe shows scheduling details
kubectl describe pod labeledpod
# Events:
#   Warning  FailedScheduling  ... 0/1 nodes are available: 1 node(s) didn't match Pod's node affinity/selector
#   Normal   Scheduled         ... Successfully assigned default/labeledpod to <node-name>
```

**Common mistake:** Creating a pod with `nodeSelector` before labeling any node. The pod stays `Pending` indefinitely. Always label the node first.

#### Pod 5 — Port Exposure

```yaml
# pod5.yml
kind: Pod
apiVersion: v1
metadata:
  name: portpod
spec:
  containers:
    - name: c05
      image: nginx
      ports:
        - containerPort: 80
```

**Behavior:** Runs Nginx listening on port 80. The `containerPort` field documents which port the container uses but does NOT expose it outside the cluster.

```bash
kubectl apply -f pod5.yml

# Get the pod IP
kubectl get pod portpod -o wide
# Output:
# NAME      READY   STATUS    IP           NODE
# portpod   1/1     Running   10.244.0.5   minikube

# Access from within the cluster (from another pod or node)
curl 10.244.0.5:80
# Output: Nginx welcome page HTML

# Access locally via port-forward
kubectl port-forward portpod 8080:80
# Now accessible at http://localhost:8080
```

**To expose externally:** Create a Service (ClusterIP, NodePort, or LoadBalancer) that selects this pod. `containerPort` alone is not sufficient for external access.

#### Pod 6 — Resource Requests and Limits

```yaml
# pod6.yml
kind: Pod
apiVersion: v1
metadata:
  name: resourcepod
spec:
  containers:
    - name: c06
      image: ubuntu
      command: ["/bin/bash", "-c", "while true; do echo resourcepod; sleep 10; done"]
      resources:
        requests:
          memory: "64Mi"
          cpu: "100m"
        limits:
          memory: "200Mi"
          cpu: "200m"
```

**Behavior:** Pod requests a minimum of 64Mi memory and 100m CPU. The scheduler only places it on a node with at least that much available capacity. The container cannot exceed 200Mi memory or 200m CPU.

```bash
kubectl apply -f pod6.yml

kubectl describe pod resourcepod
# Output includes:
#   Containers:
#     c06:
#       Requests:
#         cpu:     100m
#         memory:  64Mi
#       Limits:
#         cpu:     200m
#         memory:  200Mi

# Check actual resource usage (requires metrics-server)
kubectl top pod resourcepod
# Output:
# NAME          CPU(cores)   MEMORY(bytes)
# resourcepod   1m           5Mi
```

**What happens when limits are exceeded:**
- **Memory limit exceeded** → container is killed with `OOMKilled` status and restarted
- **CPU limit exceeded** → container is throttled (slowed down, not killed)

**Production rule:** Always set both `requests` and `limits`. Without `requests`, the scheduler cannot make informed decisions. Without `limits`, a single pod can consume all node resources and starve other pods.

### Pod Examples Summary

| Pod | Purpose | Containers | Key Feature | restartPolicy |
|---|---|---|---|---|
| pod1 | Basic loop | 1 | Infinite loop, logging | `Never` |
| pod2 | Environment variables | 1 | `env` field, config testing | `Always` (default) |
| pod3 | Multi-container | 2 | Sidecar pattern, shared network | `Always` (default) |
| pod4 | Labels & scheduling | 1 | `nodeSelector`, label filtering | `Always` (default) |
| pod5 | Port exposure | 1 | `containerPort`, port-forward | `Always` (default) |
| pod6 | Resource management | 1 | `requests` & `limits` | `Always` (default) |

**These six patterns cover the core Pod concepts:**
- **pod1** — basic pod creation, logging, restart policies
- **pod2** — injecting configuration via environment variables
- **pod3** — multi-container communication, sidecar pattern, `-c` flag for logs/exec
- **pod4** — organizing pods with labels, controlling placement with nodeSelector
- **pod5** — container ports, port-forwarding, why Services are needed
- **pod6** — resource management, scheduling guarantees, OOMKilled behavior

### Resource Requests vs Limits

```
┌─────────────────────────────────────────────────┐
│  Node Total: 2 CPU, 4Gi Memory                  │
│                                                  │
│  ┌─── Pod A ──────────────────────┐              │
│  │ Request: 250m CPU, 512Mi Mem   │ ← Guaranteed │
│  │ Limit:   500m CPU, 1Gi Mem     │ ← Maximum    │
│  └────────────────────────────────┘              │
│                                                  │
│  ┌─── Pod B ──────────────────────┐              │
│  │ Request: 500m CPU, 1Gi Mem     │              │
│  │ Limit:   1 CPU, 2Gi Mem        │              │
│  └────────────────────────────────┘              │
│                                                  │
│  Remaining allocatable:                          │
│  CPU: 2000m - 250m - 500m = 1250m               │
│  Mem: 4Gi - 512Mi - 1Gi = ~2.5Gi                │
└─────────────────────────────────────────────────┘
```

- **requests** — minimum capacity needed to start the container; used by the scheduler for placement decisions
- **limits** — maximum capacity the container can consume from the worker node

**Resource units:**
- CPU: split into 1000 milliCPU units (e.g., `100m` = 0.1 CPU core, `1000m` = 1 full core)
- Memory: specified in bytes with suffixes (e.g., `64Mi` = 64 mebibytes = 67,108,864 bytes)

```yaml
# resource-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: resources
spec:
  containers:
  - name: resource
    image: centos
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 5; done"]
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "200Mi"
        cpu: "200m"
```

### Liveness & Readiness Probes

Health checks tell Kubernetes whether your application is working correctly. Without probes, Kubernetes only knows if the container process is running — not if the application inside is healthy.

**Three types of probes:**

| Probe | Question it answers | Action on failure |
|---|---|---|
| **Liveness** | Is the container alive? | Container is restarted (killed and recreated) |
| **Readiness** | Is the container ready for traffic? | Pod is removed from Service endpoints (no traffic sent) |
| **Startup** | Is the container still starting up? | Protects slow-starting apps from being killed by liveness probe |

**When to use each:**
- **Liveness** — detect deadlocks, infinite loops, or hung processes. The container is restarted to recover.
- **Readiness** — detect temporary unavailability (loading cache, warming up, database connection lost). Traffic is diverted until the pod recovers.
- **Startup** — for applications that take a long time to start (e.g., Java apps with large classpath). Prevents liveness probe from killing the container during startup.

**Common mistake:** Setting `initialDelaySeconds` too low on liveness probes causes containers to be killed before they finish starting. Use startup probes for slow-starting apps instead.

```yaml
# probes-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-probes
spec:
  containers:
  - name: app
    image: nginx:1.25
    ports:
    - containerPort: 80

    # Liveness: Is the container alive? If not, restart it.
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
      initialDelaySeconds: 10    # Wait 10s before first check
      periodSeconds: 5           # Check every 5s
      failureThreshold: 3        # Restart after 3 failures

    # Readiness: Is the container ready for traffic? If not, remove from Service.
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 3

    # Startup: Is the container still starting? Protects slow-starting apps.
    startupProbe:
      httpGet:
        path: /healthz
        port: 80
      failureThreshold: 30
      periodSeconds: 10          # 30 * 10 = 300s max startup time
```

**Probe types:**

| Type | Method | Example |
|---|---|---|
| HTTP GET | HTTP request to endpoint | `httpGet: {path: /health, port: 8080}` |
| TCP Socket | TCP connection check | `tcpSocket: {port: 3306}` |
| Exec | Run command in container | `exec: {command: ["cat", "/tmp/healthy"]}` |
| gRPC | gRPC health check | `grpc: {port: 50051}` |

**Exec-based probe examples:**

Liveness probe — container gets restarted if the check fails:

```yaml
# liveness-exec.yaml (within a Deployment spec)
livenessProbe:
  exec:
    command:
    - ls
    - /tmp/lp
  initialDelaySeconds: 30    # Wait before first probe
  periodSeconds: 5           # Run every 5 seconds
  timeoutSeconds: 10         # Timeout for each probe
```

Readiness probe — pod is removed from Service endpoints if the check fails (no traffic sent):

```yaml
# readiness-exec.yaml (within a Deployment spec)
readinessProbe:
  exec:
    command:
    - ls
    - /tmp/rp
  initialDelaySeconds: 30
  periodSeconds: 5
  timeoutSeconds: 30
```

A return code of 0 indicates the container is healthy; non-zero indicates unhealthy.

#### Probe Parameters Explained

```
Container starts → [wait initialDelaySeconds] → Probe check → [wait periodSeconds] → Probe check → ...
```

| Parameter | Meaning | Default |
|---|---|---|
| `initialDelaySeconds` | Time to wait after container starts before running the first probe (one-time delay) | 0 |
| `periodSeconds` | Interval between probe checks (runs repeatedly after initial delay) | 10 |
| `timeoutSeconds` | How long to wait for a probe response before considering it failed | 1 |
| `failureThreshold` | Number of consecutive failures before taking action (restart or remove from endpoints) | 3 |
| `successThreshold` | Number of consecutive successes needed to mark the probe as passing (only for readiness) | 1 |

**Example:** With `initialDelaySeconds: 60` and `periodSeconds: 10`, Kubernetes waits 60 seconds after the container starts, runs the first probe, then checks every 10 seconds after that.

#### Real-World Probe Example — Liveness (exec) + Readiness (httpGet)

This pattern is common for microservices: use `nc -z` (netcat) to check if the port is open for liveness, and an HTTP health endpoint for readiness:

```yaml
# Liveness probe using exec command
livenessProbe:
  exec:
    command:
      - /bin/sh
      - -c
      - nc -z localhost 8095       # Check if port 8095 is listening
  initialDelaySeconds: 60          # App needs 60s to start
  periodSeconds: 10                # Check every 10s after that

# Readiness probe using HTTP GET
readinessProbe:
  httpGet:
    path: /usermgmt/health-status  # Application health endpoint
    port: 8095
  initialDelaySeconds: 60          # Wait for app to be fully ready
  periodSeconds: 10                # Check every 10s
```

**Why two different probe types?**
- **Liveness (exec `nc -z`)** — checks if the process is listening on the port. If the process crashes or hangs, `nc -z` fails and Kubernetes restarts the container.
- **Readiness (httpGet)** — checks if the application logic is ready (database connected, cache loaded). The pod won't receive traffic until this passes.

**Deploy and observe the probe behavior:**

```bash
# Create all objects
kubectl apply -f kube-manifests/

# Watch pods — notice the pod is NOT READY (0/1) for the first 60 seconds
kubectl get pods -w

# Output during startup:
# NAME                                    READY   STATUS    RESTARTS   AGE
# usermgmt-microservice-7b4d6f8c9-abc12   0/1     Running   0          30s   ← Not ready yet
# usermgmt-microservice-7b4d6f8c9-abc12   1/1     Running   0          65s   ← Ready after initialDelaySeconds

# Describe pod to see probe configuration and events
kubectl describe pod <usermgmt-microservice-xxxxxx>

# Look for these sections in the output:
#   Liveness:   exec [/bin/sh -c nc -z localhost 8095] delay=60s timeout=1s period=10s
#   Readiness:  http-get http://:8095/usermgmt/health-status delay=60s timeout=1s period=10s

# Access application (only works after readiness probe passes)
# http://<WorkerNode-Public-IP>:31231/usermgmt/health-status

# Clean up
kubectl delete -f kube-manifests/
kubectl get pods
kubectl get sc,pvc,pv
```

**Key observation:** The pod will not be in READY state (and won't receive traffic) until it completes the `initialDelaySeconds` (60 seconds) and the readiness probe passes. This prevents users from hitting a service that isn't fully started.

#### How Kubernetes Self-Healing Actually Works

The combination of probes, restart policies, ReplicaSets, and HPA creates a self-healing system. Here's the step-by-step flow:

```
1. App crashes or enters a bad state
       │
2. Liveness probe fails (3 consecutive failures)
       │
3. Kubernetes kills and restarts the container
       │
4. Readiness probe holds traffic (pod removed from Service endpoints)
       │
5. App starts up and initializes
       │
6. Readiness probe passes → pod added back to Service endpoints
       │
7. Traffic resumes to the pod
       │
8. If load increases → HPA adds more pods automatically
```

This entire flow happens without manual intervention. The user never sees the failure.

**What each component contributes:**

| Component | Role in Self-Healing |
|-----------|---------------------|
| **Liveness probe** | Detects when a container is broken and triggers restart |
| **Readiness probe** | Prevents traffic from reaching a pod that isn't ready |
| **Startup probe** | Protects slow-starting apps from being killed during initialization |
| **RestartPolicy: Always** | Ensures crashed containers are automatically restarted |
| **ReplicaSet** | Maintains the desired number of pods — replaces deleted/failed pods |
| **HPA** | Scales pods up/down based on CPU/memory or custom metrics |

#### Probe Best Practices

| Practice | Why |
|----------|-----|
| Always start with a readiness probe, then add liveness | Readiness prevents bad traffic routing; liveness without readiness can cause downtime during restarts |
| Use startup probes for apps that take >20s to initialize | Prevents liveness probe from killing slow-starting apps (Java, .NET) |
| Test probe endpoints locally before deploying | `curl localhost:<port>/healthz` inside the container to verify the endpoint works |
| Set resource requests and limits when using HPA | HPA calculates scaling based on resource utilization — without requests, it can't compute percentages |
| Don't use the same endpoint for liveness and readiness | Liveness should check "is the process alive?"; readiness should check "is the app ready to serve?" |
| Set `timeoutSeconds` appropriately | Default is 1s — too short for apps that query a database in their health check |

#### Common Probe Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| App receives traffic too early | Readiness probe missing or `initialDelaySeconds` too low | Add readiness probe with appropriate delay |
| Pod restarts frequently | Liveness probe failing due to short timeout or delay | Increase `initialDelaySeconds`, `timeoutSeconds`, or `failureThreshold` |
| HPA not scaling | Missing metrics-server, or no resource requests defined | Install metrics-server; add `resources.requests` to pod spec |
| Probes fail randomly | Application doesn't respond consistently under load | Increase `timeoutSeconds`; use a lightweight health endpoint that doesn't hit the database |
| Container killed during startup | Liveness probe runs before app is ready | Add a startup probe with high `failureThreshold` |

---

