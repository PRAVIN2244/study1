# MODULE 29: Troubleshooting

---

## 29.1 Troubleshooting Framework

Always follow this systematic approach:

```
┌─────────────────────────────────────────────────────────┐
│              TROUBLESHOOTING WORKFLOW                     │
│                                                         │
│  1. IDENTIFY    → What's the symptom?                   │
│  2. GATHER      → Collect logs, events, describe        │
│  3. ISOLATE     → Narrow down the component             │
│  4. DIAGNOSE    → Find root cause                       │
│  5. FIX         → Apply the solution                    │
│  6. VERIFY      → Confirm the fix works                 │
│  7. DOCUMENT    → Record for future reference           │
└─────────────────────────────────────────────────────────┘
```

### Essential Debugging Commands

```bash
# 1. Check pod status
kubectl get pods -o wide

# 2. Describe the resource (shows events)
kubectl describe pod <pod-name>

# 3. Check logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous    # Previous container (after crash)
kubectl logs <pod-name> -c <container>  # Specific container

# 4. Check events (cluster-wide)
kubectl get events --sort-by='.lastTimestamp'
kubectl get events -n <namespace> --field-selector type=Warning

# 5. Check node status
kubectl get nodes
kubectl describe node <node-name>

# 6. Check resource usage
kubectl top pods
kubectl top nodes

# 7. Exec into a pod for debugging
kubectl exec -it <pod-name> -- /bin/sh

# 8. Run a debug pod
kubectl run debug --image=busybox --rm -it -- /bin/sh
kubectl run debug --image=nicolaka/netshoot --rm -it -- /bin/bash

# 9. Check API server connectivity
kubectl cluster-info
kubectl get componentstatuses
```

### Third-Party Debugging Tools

Beyond `kubectl`, these tools speed up troubleshooting:

| Tool | What It Does | Install | Best For |
|------|-------------|---------|----------|
| **k9s** | Terminal UI for exploring pods, logs, events in real-time | `brew install derailed/k9s/k9s` | Interactive cluster exploration — faster than typing kubectl commands |
| **stern** | Multi-pod log tailer with color-coded output and regex filters | `brew install stern` | Tailing logs from multiple pods simultaneously (e.g., all replicas of a deployment) |
| **kubtail** | Tail logs of multiple pods matching a label selector | `brew install johanhaleby/kubetail/kubetail` | Quick multi-pod log aggregation |
| **lens** | GUI-based cluster explorer with metrics, logs, and shell access | [k8slens.dev](https://k8slens.dev) | Visual cluster management for teams who prefer GUIs |

**stern example — tail all pods matching a label:**

```bash
# Tail logs from all pods with app=webapp label
stern -l app=webapp -n production

# Output (color-coded by pod):
# webapp-7d8f9-abc12 │ 2024-01-15 10:23:45 INFO  Request received: GET /api/users
# webapp-7d8f9-def34 │ 2024-01-15 10:23:46 ERROR Connection refused: database at postgres:5432
# webapp-7d8f9-ghi56 │ 2024-01-15 10:23:46 INFO  Request received: GET /api/health

# Filter for errors only
stern -l app=webapp -n production --include "ERROR|WARN"
```

**k9s — keyboard shortcuts:**

```
:pods          → List pods
:deploy        → List deployments
:svc           → List services
:events        → List events
/              → Filter/search
l              → View logs
d              → Describe resource
s              → Shell into pod
ctrl-d         → Delete resource
```

### Runbook: My Pod Won't Start

A runbook is a step-by-step procedure for diagnosing a specific problem. This one covers the most common pod startup failures:

```
Step 1: Check pod status
─────────────────────────
kubectl get pods -n <namespace>

  STATUS = CrashLoopBackOff?  → Go to Step 3
  STATUS = Pending?           → Go to Step 4
  STATUS = ImagePullBackOff?  → Go to Step 5
  STATUS = Running but 0/1?   → Go to Step 6

Step 2: Check events
─────────────────────
kubectl describe pod <name> -n <namespace>
  → Scroll to "Events:" section at the bottom
  → Look for Warning events

Step 3: CrashLoopBackOff
────────────────────────
kubectl logs <pod> -n <namespace> --previous
  → Check for application exceptions/stack traces
  → Check readiness/liveness probe configuration
  → Increase initialDelaySeconds if app is slow to start
  → Verify environment variables and ConfigMaps exist

Step 4: Pending
───────────────
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod>
  → "Insufficient cpu/memory" → Scale up nodes or reduce requests
  → "No nodes match" → Check nodeSelector, taints, tolerations
  → "PVC not bound" → Check StorageClass and PVC status
  → "FailedScheduling" → Check resource quotas

Step 5: ImagePullBackOff
────────────────────────
kubectl describe pod <pod> | grep -A5 "Events:"
  → Typo in image name? → Fix image tag
  → Private registry? → Add imagePullSecrets
  → DockerHub rate limit? → Use authenticated pull or mirror

Step 6: Running but Not Ready (0/1)
────────────────────────────────────
kubectl describe pod <pod> | grep -A10 "Conditions:"
  → Readiness probe failing? → Test endpoint: kubectl exec <pod> -- curl localhost:<port>/health
  → Check readiness probe path, port, and timing

Step 7: Fix and verify
──────────────────────
kubectl apply -f <fixed-yaml>
kubectl get pods -w    # Watch until Running and Ready (1/1)
```

### Application Failure Methodology

For multi-tier applications (e.g., web frontend + database backend), troubleshoot from the user-facing end inward:

```
User → Web Service → Web Pod → DB Service → DB Pod
```

At each layer, check:

```bash
# 1. Test the service from outside
curl http://<node-ip>:<node-port>

# 2. Check the service has endpoints
kubectl describe svc web-service
# Look for: Endpoints: 10.244.0.5:8080 (should NOT be <none>)

# 3. Check the pod is running
kubectl get pods
kubectl describe pod <pod-name>

# 4. Check application logs
kubectl logs <pod-name>
kubectl logs <pod-name> -f    # stream live logs

# 5. Check the dependent service (e.g., database)
kubectl describe svc mysql-service
kubectl logs <db-pod-name>

# 6. Verify environment variables in the deployment
kubectl describe deploy webapp-mysql
# Check: DB_Host, DB_User, DB_Password values
```

### Common Application Failure Patterns

| Failure | Symptom | Diagnosis | Fix |
|---|---|---|---|
| **Service name mismatch** | `Name does not resolve` | App expects `mysql-service` but service is named `mysql` | Rename the service or update the app's `DB_Host` env var |
| **targetPort mismatch** | `Connection refused` | Service targetPort is 8080 but app listens on 3306 | `kubectl edit svc` — fix `targetPort` to match the container port |
| **Selector mismatch** | Service has no endpoints | Service selector `name=webapp` but pod label is `app=webapp` | Fix the service selector or pod labels to match |
| **Wrong credentials** | `Access denied for user` | Deployment sets `DB_User=sql-user` instead of `root` | `kubectl edit deploy` — fix the env var |
| **Wrong NodePort** | `Bad Gateway` or timeout | NodePort is 30088 but user accesses 30081 | `kubectl edit svc` — fix `nodePort` |
| **DB password mismatch** | `Access denied (using password: YES)` | App password doesn't match `MYSQL_ROOT_PASSWORD` on the DB pod | Update the DB pod or app deployment to use matching passwords |

```bash
# Quick check: does the service selector match pod labels?
kubectl get svc my-service -o jsonpath='{.spec.selector}' && echo
kubectl get pods --show-labels | grep <expected-label>

# Quick check: does targetPort match the container port?
kubectl get svc my-service -o jsonpath='{.spec.ports[0].targetPort}' && echo
kubectl get pod <pod> -o jsonpath='{.spec.containers[0].ports[0].containerPort}' && echo
```

---

## 29.2 Pod Errors

### CrashLoopBackOff

**Symptom:** Pod keeps restarting.

```bash
kubectl get pods

# Output:
# NAME        READY   STATUS             RESTARTS      AGE
# my-app      0/1     CrashLoopBackOff   5 (30s ago)   3m
```

**Diagnosis:**
```bash
# Check logs
kubectl logs my-app
kubectl logs my-app --previous

# Check events
kubectl describe pod my-app | tail -20
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Application error/exception | Fix the application code, check logs |
| Missing environment variable | Add the env var to the pod spec |
| Missing config file | Mount ConfigMap or Secret |
| Wrong command/entrypoint | Fix the `command` or `args` in pod spec |
| Insufficient memory (OOMKilled) | Increase memory limits |
| Liveness probe failing | Fix probe path/port or increase `initialDelaySeconds` |

```bash
# Check if OOMKilled
kubectl describe pod my-app | grep -A5 "Last State"

# Output:
# Last State:     Terminated
#   Reason:       OOMKilled        ← Out of memory!
#   Exit Code:    137
#   Started:      Mon, 15 Jan 2024 10:00:00 +0000
#   Finished:     Mon, 15 Jan 2024 10:00:30 +0000

# Fix: Increase memory limit
kubectl patch deployment my-app -p '{"spec":{"template":{"spec":{"containers":[{"name":"my-app","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

---

### ImagePullBackOff / ErrImagePull

**Symptom:** Pod can't pull the container image.

```bash
kubectl get pods

# Output:
# NAME        READY   STATUS             RESTARTS   AGE
# my-app      0/1     ImagePullBackOff   0          2m
```

**Diagnosis:**
```bash
kubectl describe pod my-app | grep -A10 Events

# Output:
# Events:
#   Type     Reason     Age   Message
#   Warning  Failed     30s   Failed to pull image "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v99":
#                              rpc error: code = NotFound desc = failed to pull and unpack image: manifest for
#                              123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v99 not found
```

**Common Causes & Fixes:**

| Cause | Diagnosis | Fix |
|---|---|---|
| Wrong image name/tag | Check the image field | Fix image name or tag |
| Private registry, no credentials | Check for imagePullSecrets | Create and attach pull secret |
| ECR token expired | Check node IAM role | Ensure nodes have ECR pull permissions |
| Image doesn't exist | Check ECR/registry | Build and push the image |

```bash
# Fix: Create ECR pull secret (if needed)
kubectl create secret docker-registry ecr-secret \
  --docker-server=123456789.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region us-east-1)

# Fix: Check if image exists in ECR
aws ecr describe-images --repository-name my-app --image-ids imageTag=v99

# Fix: Verify node IAM role has ECR permissions
# Node role needs: AmazonEC2ContainerRegistryReadOnly policy
```

---

### Pending Pod

**Symptom:** Pod stays in Pending state.

```bash
kubectl get pods

# Output:
# NAME        READY   STATUS    RESTARTS   AGE
# my-app      0/1     Pending   0          5m
```

**Diagnosis:**
```bash
kubectl describe pod my-app | grep -A10 Events

# Possible outputs:
# "0/3 nodes are available: 3 Insufficient cpu"
# "0/3 nodes are available: 3 Insufficient memory"
# "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"
# "no persistent volumes available for this claim"
# "pod has unbound immediate PersistentVolumeClaims"
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Insufficient CPU/memory | Scale up nodes or reduce resource requests |
| No matching nodes (affinity/selector) | Fix nodeSelector/affinity or label nodes |
| PVC not bound | Check StorageClass, create PV, or fix PVC |
| Taints preventing scheduling | Add tolerations to pod spec |
| ResourceQuota exceeded | Increase quota or reduce usage |

```bash
# Check node resources
kubectl describe nodes | grep -A5 "Allocated resources"

# Output:
# Allocated resources:
#   Resource           Requests     Limits
#   --------           --------     ------
#   cpu                1800m (90%)  3500m (175%)
#   memory             3200Mi (80%) 6400Mi (160%)
#   ← Node is almost full!

# Fix: Scale up the node group
eksctl scale nodegroup --cluster my-k8s-cluster --name standard-workers --nodes 5
```

---

### CreateContainerConfigError

**Symptom:** Pod can't start due to missing ConfigMap or Secret.

```bash
kubectl get pods

# Output:
# NAME        READY   STATUS                       RESTARTS   AGE
# my-app      0/1     CreateContainerConfigError   0          2m
```

```bash
kubectl describe pod my-app | grep -A5 "Warning"

# Output:
# Warning  Failed  30s  kubelet  Error: configmap "app-config" not found
# OR
# Warning  Failed  30s  kubelet  Error: secret "db-credentials" not found
```

**Fix:**
```bash
# Create the missing ConfigMap
kubectl create configmap app-config --from-literal=KEY=value

# Create the missing Secret
kubectl create secret generic db-credentials --from-literal=password=secret123
```

### Kubernetes Using Old Image / Updates Not Reflected in Browser

**Symptom:** You updated your application code, pushed a new image, but the browser still shows the old version.

**Root cause checklist:**

```bash
# Step 1: Check which image the pods are actually running
kubectl get deployment myapp -o jsonpath='{.spec.template.spec.containers[0].image}'

# Output:
# myapp:latest    ← Problem! "latest" is mutable — might be cached

# Step 2: Check imagePullPolicy
kubectl get deployment myapp -o jsonpath='{.spec.template.spec.containers[0].imagePullPolicy}'

# Output:
# IfNotPresent    ← Problem! Won't pull if image exists locally
```

**The `imagePullPolicy` problem:**

| Policy | Behavior | When Used |
|---|---|---|
| `Always` | Pull image every time a pod starts | Tags like `latest`, or when you need guaranteed freshness |
| `IfNotPresent` | Only pull if image doesn't exist on node | Default for tagged images (e.g., `nginx:1.25`) |
| `Never` | Never pull — image must exist locally | Pre-loaded images, air-gapped environments |

**Default behavior:** If you use `latest` tag, Kubernetes defaults to `Always`. For any other tag (e.g., `v1.0`), it defaults to `IfNotPresent`.

**The `latest` tag trap:**

```
Problem scenario:
1. You build myapp:latest (version 1.0) and push to registry
2. Deploy to K8s — pod pulls myapp:latest, runs version 1.0
3. You build myapp:latest (version 2.0) and push to registry
4. Pod crashes and restarts — pulls myapp:latest, gets version 2.0 ✓
5. But other pods still running version 1.0 — they never restarted!

Solution: NEVER use "latest" in production. Use specific tags.
```

**Fix 1: Use specific image tags**

```bash
# Bad — mutable tag
image: myapp:latest

# Good — immutable tag
image: myapp:v2.0.1

# Best — pin by digest (completely immutable)
image: myapp@sha256:abc123def456...

# Update the deployment with the new tag
kubectl set image deployment/myapp myapp=myapp:v2.0.1

# Verify rollout
kubectl rollout status deployment/myapp

# Output:
# deployment "myapp" successfully rolled out
```

**Fix 2: Force image pull with `imagePullPolicy: Always`**

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:latest
    imagePullPolicy: Always    # Always pull, even if image exists locally
```

**Fix 3: Force a rollout restart (re-pulls images)**

```bash
# Restart all pods in the deployment (triggers new image pull)
kubectl rollout restart deployment/myapp

# Output:
# deployment.apps/myapp restarted

# Watch new pods come up
kubectl get pods -w -l app=myapp

# Output:
# NAME                     READY   STATUS              RESTARTS   AGE
# myapp-7b8c9d6e8-abc12    1/1     Running             0          5m    ← old pod
# myapp-5f6a7b8c9-def34    0/1     ContainerCreating   0          5s    ← new pod
# myapp-5f6a7b8c9-def34    1/1     Running             0          10s
# myapp-7b8c9d6e8-abc12    1/1     Terminating         0          5m
```

**Fix 4: Check ReplicaSets — old RS still active?**

```bash
# ReplicaSets show if the rollout actually created new pods
kubectl get rs -l app=myapp

# Output:
# NAME               DESIRED   CURRENT   READY   AGE
# myapp-7b8c9d6e8    0         0         0       1h    ← Old RS (scaled to 0 = good)
# myapp-5f6a7b8c9    3         3         3       5m    ← New RS (active)

# If old RS still has DESIRED > 0, the rollout didn't complete
# Check rollout status:
kubectl rollout status deployment/myapp
```

**Fix 5: Check if the issue is browser/CDN caching, not Kubernetes**

```bash
# Verify the pod is actually serving new content
kubectl exec deploy/myapp -- cat /usr/share/nginx/html/index.html

# Or curl from inside the cluster (bypasses browser/CDN)
kubectl run test --image=busybox --rm -it -- wget -qO- http://myapp-service

# If the response is correct but browser shows old content:
# → Browser cache: Hard refresh with Ctrl+Shift+R (Cmd+Shift+R on Mac)
# → CDN cache: Invalidate CDN cache (CloudFront, CloudFlare, etc.)
# → Check response headers for caching:
kubectl run tmp --rm -it --image=curlimages/curl -- curl -sI http://myapp-service

# Output:
# HTTP/1.1 200 OK
# Cache-Control: max-age=3600    ← Browser caches for 1 hour!
# ETag: "abc123"
#
# Fix: Set Cache-Control: no-cache or use versioned asset URLs
```

**Fix 6: Secret/ConfigMap updated but pods not restarted**

```bash
# If you updated a Secret/ConfigMap used as env vars, pods won't pick it up
# until restarted:
kubectl rollout restart deploy/myapp
```

**Complete debugging checklist:**

| # | Check | Command |
|---|---|---|
| 1 | Is the deployment updated? | `kubectl describe deployment myapp \| grep Image` |
| 2 | Are new pods running? | `kubectl get pods -l app=myapp` |
| 3 | Is the rollout complete? | `kubectl rollout status deployment/myapp` |
| 4 | Are old ReplicaSets scaled down? | `kubectl get rs -l app=myapp` |
| 5 | Is the image correct? | `kubectl get pod <pod> -o jsonpath='{.spec.containers[0].image}'` |
| 6 | Is imagePullPolicy correct? | `kubectl get pod <pod> -o jsonpath='{.spec.containers[0].imagePullPolicy}'` |
| 7 | Are there image pull errors? | `kubectl describe pod <pod> \| grep -A5 Events` |
| 8 | Is the Service routing to new pods? | `kubectl get endpoints myapp-service` |
| 9 | Is Ingress updated? | `kubectl describe ingress \| grep Backends` |
| 10 | Is it browser/CDN cache? | `curl -sI` from inside cluster, check Cache-Control headers |
| 11 | Was Secret/ConfigMap updated? | `kubectl rollout restart deploy/myapp` |

**Interview question: Why is Kubernetes using an old image after I pushed a new one?**
Most likely cause: using the `latest` tag with `imagePullPolicy: IfNotPresent`. The node already has the old `latest` image cached, so it doesn't pull the new one. Fix: use specific image tags (e.g., `v2.0.1`), set `imagePullPolicy: Always`, or run `kubectl rollout restart deployment/<name>` to force new pods with fresh image pulls.

### Pod Stuck in Terminating

**Symptom:** Pod stays in `Terminating` state indefinitely.

```bash
kubectl get pods
# NAME        READY   STATUS        RESTARTS   AGE
# my-app      1/1     Terminating   0          45m
```

**Diagnosis:**

```bash
# Check for finalizers blocking deletion
kubectl get pod my-app -o jsonpath='{.metadata.finalizers}'
# ["some-controller/finalizer"]

# Check if the node is unreachable (pod can't receive SIGTERM)
kubectl get nodes
# NAME      STATUS     ROLES    AGE   VERSION
# worker-1  NotReady   <none>   30d   v1.29.2
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Process ignoring SIGTERM | Fix app to handle SIGTERM gracefully, or reduce `terminationGracePeriodSeconds` |
| Finalizer blocking deletion | Remove the finalizer: `kubectl patch pod my-app -p '{"metadata":{"finalizers":null}}'` |
| Node unreachable | Force delete: `kubectl delete pod my-app --grace-period=0 --force` |
| Volume unmount hanging | Check `kubectl describe pod` for volume detach events |

```bash
# Force delete a stuck pod
kubectl delete pod my-app --grace-period=0 --force
# warning: Immediate deletion does not wait for confirmation that the running resource has been terminated.

# If the pod reappears (managed by a Deployment), delete the Deployment instead
kubectl delete deployment my-app-deployment
```

> Force deletion skips the graceful shutdown period. The container may still be running on the node — kubelet will clean it up eventually. Use only when the pod is genuinely stuck.

---

### Pods Stuck in ContainerCreating

**Symptom:** Pod stays in `ContainerCreating` and never reaches `Running`.

```bash
kubectl get pods
# NAME        READY   STATUS              RESTARTS   AGE
# my-app      0/1     ContainerCreating   0          10m
```

**Diagnosis:**

```bash
kubectl describe pod my-app | tail -20
# Events:
#   Warning  FailedMount  2m  kubelet  Unable to attach or mount volumes: timed out
#   Warning  FailedCreatePodSandBox  1m  kubelet  Failed to create pod sandbox
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Volume not available (EBS in wrong AZ) | Ensure PV and pod are in the same AZ, or use EFS (multi-AZ) |
| CNI plugin not ready (aws-node) | `kubectl get ds aws-node -n kube-system` — restart if needed |
| Subnet IP exhaustion (EKS) | Use larger subnets or enable VPC CNI prefix delegation |
| Secret/ConfigMap referenced but missing | Create the missing resource |
| Image pull taking long (large image) | Wait, or use smaller images. Check `kubectl describe pod` for pull progress |

```bash
# Check CNI plugin status
kubectl get pods -n kube-system -l k8s-app=aws-node

# Check IP availability (EKS)
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.allocatable.pods}{"\n"}{end}'

# Check volume events
kubectl describe pod my-app | grep -A5 "FailedMount\|FailedAttach"
```

---

### Pods Stuck in Init State

**Symptom:** Pod shows `Init:0/1` or `Init:CrashLoopBackOff` and never starts the main container.

```bash
kubectl get pods
# NAME        READY   STATUS     RESTARTS   AGE
# my-app      0/1     Init:0/1   0          8m
```

**Diagnosis:**

```bash
# Check init container logs
kubectl logs my-app -c init-db
# Error: could not connect to database at db-service:5432

# Check init container status
kubectl describe pod my-app | grep -A10 "Init Containers"
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Init container waiting for a service that doesn't exist | Create the dependency service first |
| Init container command failing | Fix the command/script in the init container |
| DNS not resolving the dependency | Check CoreDNS is running, verify service name |
| Init container image pull failing | Check image name and registry credentials |

```yaml
# Example: Init container that waits for a database
initContainers:
- name: init-db
  image: busybox:1.36
  command: ['sh', '-c', 'until nslookup db-service.default.svc.cluster.local; do echo waiting for db; sleep 2; done']
```

```bash
# Replicate: Deploy a pod with an init container that depends on a non-existent service
kubectl run init-test --image=nginx --dry-run=client -o yaml > init-test.yaml
# Add an initContainer that waits for "nonexistent-service" — pod will stay in Init:0/1
```

---

### Exit Code 137 (OOMKilled)

**Symptom:** Container terminates with exit code 137. Pod may show `CrashLoopBackOff` or `OOMKilled` in the last state.

```bash
kubectl describe pod my-app | grep -A5 "Last State"
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
```

**What exit code 137 means:** The process received SIGKILL (signal 9). In Kubernetes, this almost always means the container exceeded its memory limit and the kernel's OOM killer terminated it. `137 = 128 + 9 (SIGKILL)`.

**Diagnosis:**

```bash
# Check current memory limits
kubectl get pod my-app -o jsonpath='{.spec.containers[0].resources.limits.memory}'
# 128Mi    ← too low

# Check actual memory usage (requires metrics-server)
kubectl top pod my-app
# NAME     CPU(cores)   MEMORY(bytes)
# my-app   50m          245Mi          ← exceeds 128Mi limit
```

**Fixes:**

```yaml
# Increase memory limit
resources:
  requests:
    memory: "256Mi"
  limits:
    memory: "512Mi"    # Set higher than peak usage
```

```bash
# Quick patch
kubectl patch deployment my-app -p '{"spec":{"template":{"spec":{"containers":[{"name":"my-app","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

> If the application's memory usage keeps growing over time (memory leak), increasing limits only delays the crash. Profile the application to find the leak. Common causes: unbounded caches, connection pools not closing, event listeners not being removed.

---

### Failed to Create Pod Sandbox

**Symptom:** Pod stays in `ContainerCreating` with sandbox creation errors.

```bash
kubectl describe pod my-app | grep -A3 "Failed"
# Warning  FailedCreatePodSandBox  kubelet  Failed to create pod sandbox:
#   rpc error: code = Unknown desc = failed to setup network for sandbox
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| CNI plugin not installed or crashed | Reinstall CNI: `kubectl apply -f <cni-manifest>` |
| CNI binary missing on node | SSH to node, check `/opt/cni/bin/` |
| IP address exhaustion | Check subnet CIDR, enable prefix delegation (EKS) |
| Container runtime issue | SSH to node: `systemctl status containerd` → restart if needed |

```bash
# Check CNI pods
kubectl get pods -n kube-system | grep -E "aws-node|calico|flannel|cilium"

# Check container runtime on the node
ssh node-1 "systemctl status containerd"
ssh node-1 "journalctl -u containerd --since '10 minutes ago'"
```

---

### Liveness & Readiness Probe Failures

**Symptom:** Pod keeps restarting (liveness) or Service has no endpoints (readiness).

```bash
# Liveness failure — pod restarts
kubectl describe pod my-app | grep -A5 "Liveness"
# Liveness probe failed: HTTP probe failed with statuscode: 503
# Container my-app restarted 4 times

# Readiness failure — pod not in Service endpoints
kubectl get endpoints my-service
# NAME         ENDPOINTS
# my-service   <none>        ← no ready pods
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Wrong probe path (e.g., `/healthz` vs `/health`) | Match the path your app actually serves |
| Wrong probe port | Match `containerPort` or the port your app listens on |
| App takes long to start | Increase `initialDelaySeconds` or use a `startupProbe` |
| App returns non-200 status | Fix the health endpoint to return 200 when healthy |
| Probe timeout too short | Increase `timeoutSeconds` (default is 1s) |

```yaml
# Recommended probe configuration
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15     # Wait before first check
  periodSeconds: 10           # Check every 10s
  timeoutSeconds: 3           # Fail if no response in 3s
  failureThreshold: 3         # Restart after 3 consecutive failures
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3
startupProbe:                 # For slow-starting apps (Java, .NET)
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30        # 30 × 10s = 5 minutes to start
  periodSeconds: 10
```

```bash
# Test the probe endpoint manually from inside the cluster
kubectl exec my-app -- curl -s http://localhost:8080/health
# {"status":"ok"}    ← should return 200

# If the endpoint doesn't exist, the probe will always fail
kubectl exec my-app -- curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/healthz
# 404    ← wrong path!
```

---

## 29.3 Service & Networking Errors

### Service Has No Endpoints

**Symptom:** Service exists but doesn't route traffic.

```bash
kubectl get endpoints my-service

# Output:
# NAME         ENDPOINTS   AGE
# my-service   <none>      5m    ← No endpoints!
```

**Diagnosis:**
```bash
# Check service selector
kubectl describe service my-service | grep Selector

# Output:
# Selector: app=my-app

# Check pod labels
kubectl get pods --show-labels

# Output:
# NAME        READY   STATUS    LABELS
# my-app-1    1/1     Running   app=myapp    ← "myapp" != "my-app"!
```

**Fix:** Ensure service selector matches pod labels exactly.

---

### DNS Resolution Failure

**Symptom:** Pods can't resolve service names.

```bash
kubectl exec -it my-pod -- nslookup my-service

# Output:
# ;; connection timed out; no servers could be reached
```

**Diagnosis:**
```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Output:
# NAME                       READY   STATUS    RESTARTS   AGE
# coredns-5d78c9869d-abc12   0/1     Error     5          1h    ← CoreDNS is down!

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Check if DNS service exists
kubectl get svc -n kube-system kube-dns
```

**Fix:**
```bash
# Restart CoreDNS
kubectl rollout restart deployment coredns -n kube-system

# If CoreDNS is missing, reinstall
kubectl apply -f https://raw.githubusercontent.com/coredns/deployment/master/kubernetes/coredns.yaml
```

#### CoreDNS Error: SERVFAIL

CoreDNS tried to resolve a DNS query but failed to get a valid response. Common causes: misconfigured upstream DNS servers, network connectivity issues, bad CoreDNS configuration.

**Step 1: Check CoreDNS logs**

```bash
kubectl logs <coredns-pod-name> -n kube-system

# Example error:
# [ERROR] plugin/errors: 2 kube-dns.default.svc.cluster.local. A: SERVFAIL
```

**Step 2: Check CoreDNS ConfigMap**

```bash
kubectl get configmap coredns -n kube-system -o yaml
```

Default Corefile:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

The `forward . /etc/resolv.conf` line forwards external DNS queries to the node's resolvers. If those are unreachable, you get SERVFAIL.

**Step 3: Check upstream DNS inside the CoreDNS pod**

```bash
kubectl exec -it <coredns-pod-name> -n kube-system -- cat /etc/resolv.conf
```

**Step 4: Fix — point to known-good upstream DNS**

```bash
kubectl edit configmap coredns -n kube-system
```

Change:
```
forward . /etc/resolv.conf
```
To:
```
forward . 8.8.8.8 1.1.1.1
```

Then restart CoreDNS:

```bash
kubectl rollout restart deployment coredns -n kube-system

# Verify
kubectl exec -it <any-pod> -- nslookup kubernetes.default
```

#### CoreDNS Error: REFUSED

CoreDNS refused to answer the query. Usually caused by a domain not matching any configured zone.

```bash
# Example log:
# [INFO] 10.244.0.12:59245 - 63754 "A IN unknown.com. udp 33 false 512" REFUSED
```

**Fix: Ensure `fallthrough` and external forwarding are configured**

```yaml
# Correct Corefile with fallthrough and external DNS
.:53 {
    errors
    health
    kubernetes cluster.local in-addr.arpa ip6.arpa {
      pods insecure
      fallthrough in-addr.arpa ip6.arpa
    }
    forward . 8.8.8.8
    cache 30
    loop
    reload
}
```

`fallthrough` ensures unresolved internal queries are forwarded to the external DNS server. Without it, queries for domains outside `cluster.local` get REFUSED.

```bash
kubectl rollout restart deployment coredns -n kube-system
```

#### CoreDNS Troubleshooting Checklist

| Check | Command | What to Look For |
|---|---|---|
| CoreDNS logs | `kubectl logs <coredns-pod> -n kube-system` | Errors like SERVFAIL, REFUSED |
| ConfigMap | `kubectl get configmap coredns -n kube-system -o yaml` | Forwarding IPs, fallthrough, correct zones |
| `/etc/resolv.conf` inside pod | `kubectl exec -it <coredns-pod> -n kube-system -- cat /etc/resolv.conf` | Valid nameservers |
| Pod DNS resolution | `kubectl exec -it <pod> -- nslookup kubernetes.default` | Should resolve correctly |

### Troubleshooting kube-proxy

kube-proxy maintains iptables/IPVS rules for Service routing. Issues here cause Service connectivity failures.

```bash
# Check kube-proxy pods
kubectl get pods -n kube-system -l k8s-app=kube-proxy

# Describe for scheduling/image issues
kubectl describe daemonset kube-proxy -n kube-system

# Check logs for rule sync errors
kubectl logs <kube-proxy-pod-name> -n kube-system
# Look for: iptables/IPVS rule updates, service/endpoint syncing errors
```

**Common symptoms:** Services unreachable by ClusterIP, NodePort not responding, load balancing not working across pod replicas.

### Troubleshooting aws-node (EKS VPC CNI)

aws-node handles pod IP allocation from your VPC. Issues cause pods to stay in `ContainerCreating` or `NetworkUnavailable`.

```bash
# Check aws-node pods
kubectl get pods -n kube-system -l k8s-app=aws-node

# Describe for ENI/IP issues
kubectl describe daemonset aws-node -n kube-system
kubectl describe pod <aws-node-pod-name> -n kube-system

# Check logs for IP exhaustion
kubectl logs <aws-node-pod-name> -n kube-system
# Look for: IP allocation failures, ENI attachment errors, VPC CNI status
```

**Common symptoms:** Pods stuck in `ContainerCreating`, node shows `NetworkUnavailable`, IP address exhaustion in subnet.

| Symptom | Cause | Fix |
|---|---|---|
| Pods stuck in ContainerCreating | Subnet IP exhaustion | Use larger subnet or enable prefix delegation |
| NetworkUnavailable on node | aws-node pod crashed | Restart: `kubectl delete pod <aws-node-pod> -n kube-system` |
| ENI attachment errors | EC2 ENI limit reached | Use smaller instance or enable prefix delegation |

### Troubleshooting ebs-csi-controller

ebs-csi-controller handles EBS volume provisioning. Issues cause PVCs to stay in `Pending`.

```bash
# Check ebs-csi pods
kubectl get pods -n kube-system -l app=ebs-csi-controller

# Describe for provisioning errors
kubectl describe deployment ebs-csi-controller -n kube-system
kubectl describe pod <ebs-csi-pod-name> -n kube-system

# Check logs for volume attach/detach errors
kubectl logs <ebs-csi-pod-name> -n kube-system
# Look for: volume attach/detach events, EBS API errors, IAM permission denied
```

**Common symptoms:** PVC stuck in Pending, volume not attaching, Multi-Attach errors.

### Inspecting kube-dns Service

```bash
# Check the DNS service endpoint
kubectl describe svc kube-dns -n kube-system
# Shows: ClusterIP (usually 10.100.0.10), ports (53 UDP/TCP), endpoints (CoreDNS pod IPs)
# Note: kube-dns is a Service — its logs come from the CoreDNS pods it routes to
```

---

### Connection Refused / Connection Timeout

```bash
# Debug network connectivity
kubectl run netshoot --image=nicolaka/netshoot --rm -it -- /bin/bash

# Inside the debug pod:
# Test DNS
nslookup my-service.default.svc.cluster.local

# Test connectivity
curl -v http://my-service:80

# Test TCP connection
nc -zv my-service 80

# Trace route
traceroute my-service

# Check if port is open
nmap -p 80 my-service
```

**Common Causes:**

| Symptom | Cause | Fix |
|---|---|---|
| Connection refused | App not listening on expected port | Check `targetPort` matches container port |
| Connection timeout | NetworkPolicy blocking traffic | Check/update NetworkPolicy |
| Connection timeout | Pod not ready | Check readiness probe |
| Intermittent failures | Pod is being evicted/restarted | Check resource limits, node health |

### Service External-IP Pending

**Symptom:** LoadBalancer Service stays in `<pending>` state for External-IP.

```bash
kubectl get svc my-service
# NAME         TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
# my-service   LoadBalancer   10.100.45.12   <pending>     80:31234/TCP   15m
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| No cloud provider integration (bare metal / minikube) | Use `NodePort` instead, or install MetalLB for bare-metal LB |
| AWS LB controller not installed (EKS) | Install AWS Load Balancer Controller |
| Subnet not tagged correctly (EKS) | Tag subnets: `kubernetes.io/role/elb=1` (public) or `kubernetes.io/role/internal-elb=1` (private) |
| IAM permissions missing | Check LB controller service account has correct IAM policy |
| Quota exceeded | Check AWS service quotas for ELBs in the region |

```bash
# Check LB controller logs (EKS)
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=50

# Check AWS subnet tags
aws ec2 describe-subnets --subnet-ids subnet-abc123 --query 'Subnets[].Tags'
```

### Ingress Returns 404

**Symptom:** Ingress is created but all requests return 404 Not Found.

```bash
curl -H "Host: myapp.example.com" http://<ingress-ip>/api
# 404 Not Found
```

**Diagnosis:**

```bash
kubectl describe ingress my-ingress
# Rules:
#   Host              Path  Backends
#   ----              ----  --------
#   myapp.example.com
#                     /api   my-service:8080 (0 endpoints)    ← no endpoints!

kubectl get endpoints my-service
# NAME         ENDPOINTS
# my-service   <none>
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Backend service has no endpoints | Fix service selector to match pod labels |
| Wrong service port in Ingress | Match `service.port.number` to the Service's `port` (not `targetPort`) |
| Path mismatch (missing `rewrite-target`) | Add `nginx.ingress.kubernetes.io/rewrite-target: /` annotation |
| Ingress class not matching controller | Set `ingressClassName: nginx` (or `alb` for AWS) |
| Host header not matching | Ensure the `Host` header matches the Ingress rule, or remove the host restriction |

```bash
# Verify service selector matches pod labels
kubectl get svc my-service -o jsonpath='{.spec.selector}'
# {"app":"my-app"}

kubectl get pods -l app=my-app
# No resources found    ← labels don't match!
```

### Ingress Returns 502 Bad Gateway

**Symptom:** Ingress returns 502 for some or all requests.

```bash
curl -H "Host: myapp.example.com" http://<ingress-ip>/
# 502 Bad Gateway
```

**What 502 means:** The ingress controller reached the backend service, but the backend pod returned an error or didn't respond.

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Backend pod is crashing | Check `kubectl logs` and `kubectl describe pod` |
| Backend pod not ready (readiness probe failing) | Fix readiness probe or increase `initialDelaySeconds` |
| Wrong `targetPort` on Service | Match Service `targetPort` to the port the app listens on |
| Backend pod is overloaded | Scale up replicas, increase resource limits |
| Connection timeout to backend | Increase ingress timeout annotations |

```bash
# Check if backend pods are healthy
kubectl get pods -l app=my-app
# NAME                     READY   STATUS    RESTARTS   AGE
# my-app-abc12             0/1     Running   0          5m    ← 0/1 = not ready

# Check what port the app actually listens on
kubectl exec my-app-abc12 -- netstat -tlnp
# tcp  0  0  0.0.0.0:3000  0.0.0.0:*  LISTEN    ← app listens on 3000

kubectl get svc my-service -o jsonpath='{.spec.ports[0].targetPort}'
# 8080    ← mismatch! Should be 3000
```

### Ingress Redirect Loop

**Symptom:** Browser shows "too many redirects" or `ERR_TOO_MANY_REDIRECTS`. Curl shows repeated 308/301 redirects.

```bash
curl -I http://myapp.example.com/
# HTTP/1.1 308 Permanent Redirect
# Location: https://myapp.example.com/
# (which redirects back to http://... → infinite loop)
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| SSL termination at LB + app also redirects to HTTPS | Disable app-level HTTPS redirect, or pass `X-Forwarded-Proto` header |
| NGINX `ssl-redirect` annotation with external TLS termination | Set `nginx.ingress.kubernetes.io/ssl-redirect: "false"` |
| ALB + backend expects HTTPS | Set ALB target group protocol to HTTPS, or disable app redirect |

```yaml
# Fix for NGINX Ingress with external TLS termination (e.g., CloudFront, ALB)
metadata:
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "false"
```

```yaml
# Fix for ALB Ingress — use the correct backend protocol
metadata:
  annotations:
    alb.ingress.kubernetes.io/backend-protocol: HTTP
    alb.ingress.kubernetes.io/ssl-redirect: "443"
```

---

## 29.4 Storage Errors

### PVC Stuck in Pending

```bash
kubectl get pvc

# Output:
# NAME       STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# my-pvc     Pending                                      gp3            5m

kubectl describe pvc my-pvc | grep -A5 Events

# Possible outputs:
# "waiting for first consumer to be created before binding"
# "no persistent volumes available for this claim"
# "storageclass.storage.k8s.io "gp3" not found"
```

**Fixes:**

```bash
# 1. StorageClass not found
kubectl get storageclass
# Fix: Create the StorageClass or use an existing one

# 2. WaitForFirstConsumer — Normal behavior, create a pod that uses the PVC

# 3. EBS CSI driver not installed
kubectl get pods -n kube-system | grep ebs
# Fix: Install aws-ebs-csi-driver addon

# 4. IAM permissions missing
# Fix: Ensure EBS CSI driver service account has proper IAM role
```

### Multi-Attach Error

```bash
kubectl describe pod my-pod | grep -A3 "Warning"

# Output:
# Warning  FailedAttachVolume  30s  attachdetach-controller
#   Multi-Attach error for volume "pvc-abc123": Volume is already exclusively attached to one node
#   and can't be attached to another
```

**Cause:** EBS volumes (RWO) can only attach to one node. If a pod moves to a different node, the old attachment must be released first.

**Fix:**
```bash
# Delete the old pod stuck on the previous node
kubectl delete pod <old-pod-name> --force --grace-period=0

# Or use EFS (RWX) for multi-node access
```

### PersistentVolume Stuck in Released State

**Symptom:** PV shows `Released` status after the PVC that was bound to it is deleted. New PVCs won't bind to it.

```bash
kubectl get pv
# NAME     CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM
# my-pv    10Gi       RWO            Retain           Released   default/my-pvc
```

**Why this happens:** When `reclaimPolicy: Retain` is set, deleting the PVC releases the PV but keeps the data. The PV stays in `Released` and won't bind to new PVCs because it still references the old claim.

**Fix — make the PV available again:**

```bash
# Remove the old claimRef so the PV becomes Available
kubectl patch pv my-pv -p '{"spec":{"claimRef": null}}'

kubectl get pv my-pv
# NAME     CAPACITY   STATUS      RECLAIM POLICY
# my-pv    10Gi       Available   Retain          ← now bindable
```

> Data on the volume is preserved. If you want automatic cleanup, use `reclaimPolicy: Delete` instead — but the underlying storage (EBS volume) will be deleted when the PVC is removed.

### Volume Mount Permissions Denied

**Symptom:** Container can't write to a mounted volume — `Permission denied` errors in logs.

```bash
kubectl logs my-app
# Error: EACCES: permission denied, open '/data/output.log'
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Container runs as non-root but volume is owned by root | Set `fsGroup` in pod securityContext |
| Volume has restrictive permissions | Use an init container to `chmod`/`chown` the mount |
| ReadOnly mount | Check `readOnly: true` in volumeMount — remove if writes needed |

```yaml
# Fix with fsGroup — Kubernetes changes volume ownership to this GID
spec:
  securityContext:
    runAsUser: 1000
    fsGroup: 2000       # All files on mounted volumes get group ID 2000
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - name: data
      mountPath: /data
```

```yaml
# Fix with init container — for cases where fsGroup doesn't work (e.g., NFS)
initContainers:
- name: fix-permissions
  image: busybox:1.36
  command: ['sh', '-c', 'chown -R 1000:2000 /data']
  volumeMounts:
  - name: data
    mountPath: /data
```

### Resource Quota Exceeded

**Symptom:** Pod creation fails with `forbidden: exceeded quota` error.

```bash
kubectl apply -f my-pod.yaml
# Error from server (Forbidden): pods "my-pod" is forbidden:
#   exceeded quota: compute-quota, requested: cpu=500m, used: cpu=1800m, limited: cpu=2
```

**Diagnosis:**

```bash
# Check namespace quotas
kubectl describe resourcequota -n my-namespace
# Name:       compute-quota
# Resource    Used    Hard
# --------    ----    ----
# cpu         1800m   2
# memory      3Gi     4Gi
# pods        9       10
```

**Fixes:**

```bash
# Option 1: Reduce resource requests in the pod spec
# Option 2: Increase the quota
kubectl patch resourcequota compute-quota -n my-namespace \
  -p '{"spec":{"hard":{"cpu":"4","memory":"8Gi","pods":"20"}}}'

# Option 3: Delete unused pods to free quota
kubectl delete pod unused-pod -n my-namespace
```

> Every pod in a quota-enforced namespace must specify `resources.requests`. Pods without requests will be rejected. Set LimitRange defaults to avoid this.

### Namespace Deletion Stuck

**Symptom:** Namespace stays in `Terminating` state indefinitely.

```bash
kubectl get namespace old-ns
# NAME     STATUS        AGE
# old-ns   Terminating   2h
```

**Why this happens:** Kubernetes waits for all resources in the namespace to be deleted. Finalizers on resources (CRDs, PVCs, webhooks) can block deletion.

**Diagnosis:**

```bash
# Check what's blocking
kubectl get all -n old-ns
kubectl get apiservices | grep False
# v1beta1.metrics.k8s.io   kube-system/metrics-server   False (MissingEndpoints)

# Check namespace finalizers
kubectl get namespace old-ns -o jsonpath='{.spec.finalizers}'
# ["kubernetes"]
```

**Fixes:**

```bash
# Fix 1: Delete remaining resources
kubectl delete all --all -n old-ns
kubectl delete pvc --all -n old-ns

# Fix 2: Fix broken API services (common cause)
kubectl delete apiservice v1beta1.metrics.k8s.io

# Fix 3: Force remove finalizers (last resort)
kubectl get namespace old-ns -o json | \
  jq '.spec.finalizers = []' | \
  kubectl replace --raw "/api/v1/namespaces/old-ns/finalize" -f -
```

> Forcing finalizer removal can leave orphaned resources (cloud load balancers, volumes). Always try to fix the root cause first.

---

## 29.5 Node Errors

### Node NotReady

```bash
kubectl get nodes

# Output:
# NAME                          STATUS     ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal    Ready      <none>   5d    v1.28.2
# ip-10-0-2-200.ec2.internal    NotReady   <none>   5d    v1.28.2    ← Problem!
```

**Diagnosis:**
```bash
kubectl describe node ip-10-0-2-200.ec2.internal

# Check Conditions section:
# Type                 Status    Reason
# ----                 ------    ------
# MemoryPressure       False     KubeletHasSufficientMemory
# DiskPressure         True      KubeletHasDiskPressure        ← Disk full!
# PIDPressure          False     KubeletHasSufficientPID
# Ready                False     KubeletNotReady
```

**Common Causes & Fixes:**

| Condition | Cause | Fix |
|---|---|---|
| DiskPressure | Node disk full | Clean up images: `docker system prune` |
| MemoryPressure | Node memory exhausted | Reduce pod memory or add nodes |
| PIDPressure | Too many processes | Check for fork bombs, reduce pods |
| NetworkUnavailable | CNI plugin issue | Restart aws-node DaemonSet |
| KubeletNotReady | kubelet crashed | SSH to node, `systemctl restart kubelet` |

```bash
# Check kubelet logs on the node (SSH required)
ssh ec2-user@<node-ip>
sudo journalctl -u kubelet -f

# Drain a problematic node (move pods to other nodes)
kubectl drain ip-10-0-2-200.ec2.internal --ignore-daemonsets --delete-emptydir-data

# Output:
# node/ip-10-0-2-200.ec2.internal cordoned
# evicting pod default/my-app-abc12
# pod/my-app-abc12 evicted
# node/ip-10-0-2-200.ec2.internal drained

# After fixing, uncordon the node
kubectl uncordon ip-10-0-2-200.ec2.internal
```

### Worker Node Failure — Detailed Troubleshooting

When a node is NotReady, SSH into it and follow this systematic flow:

```bash
# 1. Check kubelet service status
service kubelet status
# Active: inactive (dead)    ← kubelet stopped
# Active: activating (auto-restart) (Result: exit-code) status=255  ← kubelet crashing

# 2. If stopped, start it
service kubelet start

# 3. If crashing, check logs for the cause
journalctl -u kubelet -f
```

**Common worker node failure scenarios:**

#### Kubelet Stopped

```bash
service kubelet status
# Active: inactive (dead)

# Fix: start the service
service kubelet start

# Verify
service kubelet status
# Active: active (running)
```

#### Wrong CA File in Kubelet Config

```bash
journalctl -u kubelet | tail -20
# failed to load Kubelet config file /var/lib/kubelet/config.yaml

cat /var/lib/kubelet/config.yaml | grep clientCAFile
# clientCAFile: /etc/kubernetes/pki/WONG-CA-FILE.crt    ← wrong file!

# Fix: correct the CA file path
vi /var/lib/kubelet/config.yaml
# Change to: clientCAFile: /etc/kubernetes/pki/ca.crt

service kubelet restart
```

#### Wrong Control Plane Port in kubelet.conf

```bash
journalctl -u kubelet | tail -20
# dial tcp 10.54.130.2:6553: connect: connection refused

cat /etc/kubernetes/kubelet.conf | grep server
# server: https://controlplane:6553    ← wrong port!

# Fix: correct the port to 6443
vi /etc/kubernetes/kubelet.conf
# Change to: server: https://controlplane:6443

service kubelet restart
```

#### Validating Kubelet Certificates

```bash
# Check the kubelet's client certificate
openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -text -noout | head -15
# Issuer: CN = kubernetes
# Validity
#     Not Before: Mar 20 08:09:29 2024 GMT
#     Not After : Mar 20 08:09:29 2025 GMT
# Subject: O = system:nodes, CN = system:node:worker-1

# Verify: Issuer should be the cluster CA, Subject should match the node name,
# and the certificate should not be expired
```

**Worker node troubleshooting summary:**

| Symptom | Cause | Fix |
|---|---|---|
| kubelet `inactive (dead)` | Service stopped | `service kubelet start` |
| kubelet exit code 255, auto-restart | Config error | Check `journalctl -u kubelet` for specific error |
| `failed to load Kubelet config` | Wrong CA file path | Fix `clientCAFile` in `/var/lib/kubelet/config.yaml` |
| `connection refused` to control plane | Wrong port in kubelet.conf | Fix `server:` URL port to 6443 in `/etc/kubernetes/kubelet.conf` |
| Certificate expired | Kubelet cert past validity | Renew with `kubeadm certs renew` or re-join node |

### Node Cordon, Drain & Uncordon

Node maintenance operations for upgrades, patching, or decommissioning.

**How kubectl drain works in the background (step by step):**

```
┌──────────────────────────────────────────────────────────────┐
│  kubectl drain <node> --ignore-daemonsets --delete-emptydir-data │
│                                                              │
│  Step 1: CORDON the node                                     │
│          → Marks node as SchedulingDisabled                  │
│          → No new pods will be scheduled here                │
│                                                              │
│  Step 2: LIST all pods on the node                           │
│          → Identifies which pods need to be evicted          │
│          → Skips DaemonSet pods (--ignore-daemonsets)         │
│          → Skips mirror pods (static pods)                   │
│                                                              │
│  Step 3: CHECK PodDisruptionBudgets (PDBs)                   │
│          → If evicting a pod would violate a PDB             │
│            (e.g., minAvailable not met), drain waits/fails   │
│                                                              │
│  Step 4: EVICT each pod via the Eviction API                 │
│          → Sends DELETE request with eviction subresource     │
│          → Pod receives SIGTERM signal                       │
│          → Pod has gracePeriodSeconds (default 30s) to       │
│            shut down cleanly                                 │
│          → After grace period, SIGKILL is sent               │
│                                                              │
│  Step 5: WAIT for pods to terminate                          │
│          → Drain blocks until all pods are gone              │
│          → Default timeout: no limit (waits forever)         │
│          → Use --timeout=300s to set a deadline              │
│                                                              │
│  Step 6: RESCHEDULE                                          │
│          → Pods owned by Deployments/ReplicaSets are         │
│            automatically recreated on other nodes            │
│          → Standalone pods (no controller) are NOT           │
│            recreated — they're just deleted                  │
│          → StatefulSet pods are recreated in order           │
│                                                              │
│  Step 7: Node is now empty (except DaemonSets)               │
│          → Safe to perform maintenance                       │
│          → Run kubectl uncordon <node> when done             │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Full drain with verbose output
kubectl drain worker-1 --ignore-daemonsets --delete-emptydir-data -v=4

# Output:
# node/worker-1 cordoned
# evicting pod default/webapp-7b8c9d6e8-abc12
# evicting pod default/backend-5f6a7b8c9-def34
# evicting pod monitoring/prometheus-node-exporter-ghi56    ← skipped (DaemonSet)
# pod/webapp-7b8c9d6e8-abc12 evicted
# pod/backend-5f6a7b8c9-def34 evicted
# node/worker-1 drained

# What happens to the evicted pods:
kubectl get pods -o wide

# Output:
# NAME                      READY   STATUS    NODE
# webapp-7b8c9d6e8-jkl78    1/1     Running   worker-2    ← Recreated on worker-2
# backend-5f6a7b8c9-mno90   1/1     Running   worker-3    ← Recreated on worker-3
```

**Drain flags explained:**

| Flag | Purpose | When to Use |
|---|---|---|
| `--ignore-daemonsets` | Skip DaemonSet pods (they can't be rescheduled) | Always |
| `--delete-emptydir-data` | Acknowledge that emptyDir data will be lost | When pods use emptyDir volumes |
| `--force` | Delete standalone pods (no controller) | When pods aren't managed by Deployment/RS |
| `--timeout=300s` | Fail if drain takes longer than 5 minutes | Automated maintenance scripts |
| `--grace-period=60` | Override pod's terminationGracePeriodSeconds | When you need faster drain |
| `--disable-eviction` | Use DELETE instead of Eviction API (ignores PDBs) | Emergency maintenance only |

```bash
# CORDON — mark node as unschedulable (no new pods, existing pods stay)
kubectl cordon <node-name>
kubectl get nodes
# Output:
# NAME       STATUS                     ROLES    AGE   VERSION
# worker-1   Ready,SchedulingDisabled   <none>   30d   v1.29.0

# DRAIN — evict all pods from node (respects PDBs)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# Pods are rescheduled to other nodes
# DaemonSet pods are ignored (they must run on every node)
# emptyDir data is lost (--delete-emptydir-data acknowledges this)

# UNCORDON — make node schedulable again
kubectl uncordon <node-name>
```

**Drain vs Cordon:**
- `cordon` — only prevents NEW pods from scheduling. Existing pods keep running.
- `drain` — cordons the node AND evicts all pods (except DaemonSets).

**When drain gets stuck:**
```bash
# PDB prevents eviction (minAvailable not met)
# Error: Cannot evict pod as it would violate the pod's disruption budget

# Options:
# 1. Scale up the deployment first so PDB is satisfied
kubectl scale deployment my-app --replicas=4
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 2. Force drain (DANGEROUS — ignores PDBs)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --force

# 3. Delete the PDB temporarily
kubectl delete pdb <pdb-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

### Node Not Registering with Cluster

**Symptom:** Worker node doesn't appear in `kubectl get nodes` after `kubeadm join`.

**Diagnosis:**

```bash
# On the worker node — check kubelet status
sudo systemctl status kubelet
sudo journalctl -u kubelet -f --no-pager | tail -50
```

**Common causes and fixes:**

| Cause | Symptom in kubelet logs | Fix |
|---|---|---|
| Token expired | `token has expired` | Generate new token: `kubeadm token create --print-join-command` |
| Wrong CA hash | `certificate signed by unknown authority` | Get correct hash from master: `openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt` |
| Firewall blocking port 6443 | `connection refused` or `timeout` | Open port 6443 on master's security group/firewall |
| Swap enabled | `Running with swap on is not supported` | `sudo swapoff -a` |
| containerd not running | `container runtime is not running` | `sudo systemctl restart containerd` |
| DNS resolution failure | `lookup master: no such host` | Use IP address instead of hostname, or fix DNS |
| kubelet not started | `kubelet.service: Failed` | Check `journalctl -u kubelet` for specific error |

```bash
# Reset and retry join
sudo kubeadm reset
sudo kubeadm join <master-ip>:6443 --token <new-token> --discovery-token-ca-cert-hash sha256:<hash>
```

### Real-Life Troubleshooting Scenarios

#### Scenario 1: Application OOMKilled in Production

**Situation:** Production pods keep getting OOMKilled during peak traffic.

```bash
# Identify OOMKilled pods
kubectl get pods | grep OOMKilled
kubectl describe pod <pod-name> | grep -A5 "Last State"

# Output:
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137

# Check actual memory usage vs limits
kubectl top pods --sort-by=memory

# Check node memory pressure
kubectl describe node <node-name> | grep -A5 "Conditions"
```

**Resolution steps:**
1. Check if the memory limit is too low for the application's actual needs
2. Profile the application to find memory leaks (heap dumps, profiling tools)
3. Increase memory limits: `kubectl set resources deployment/my-app --limits=memory=1Gi`
4. Add HPA to scale horizontally instead of vertically
5. If the application has a memory leak, fix the code — increasing limits only delays the crash

#### Scenario 2: Pods Stuck in CrashLoopBackOff After Deployment

**Situation:** New deployment version causes all pods to crash.

```bash
# Check what changed
kubectl rollout history deployment/my-app

# Check logs of crashing pod
kubectl logs <pod-name> --previous

# Common causes:
# - Missing environment variable that new version requires
# - Database migration not run
# - Config file format changed
# - New dependency not available (external service down)

# Immediate fix: rollback
kubectl rollout undo deployment/my-app

# Verify rollback
kubectl rollout status deployment/my-app
kubectl get pods
```

#### Scenario 3: Node Disk Full — Pods Evicted

**Situation:** Kubernetes starts evicting pods because node disk is full.

```bash
# Check node conditions
kubectl describe node <node-name> | grep DiskPressure
# DiskPressure   True   KubeletHasDiskPressure

# Check disk usage on node
ssh <node-ip>
df -h
du -sh /var/lib/docker/*
du -sh /var/lib/containerd/*

# Clean up unused images and containers
sudo crictl rmi --prune
sudo docker system prune -af    # if using Docker

# Clean up old logs
sudo find /var/log -name "*.log" -mtime +7 -delete
```

**Prevention:** Set image garbage collection thresholds in kubelet config, use log rotation, monitor disk usage with Prometheus alerts.

#### Scenario 4: Service Returns 503 — No Healthy Backends

**Situation:** Application returns 503 errors. Service has no ready endpoints.

```bash
# Check endpoints
kubectl get endpoints <service-name>
# Output: <none>  ← No pods matching selector

# Check if pods exist and are ready
kubectl get pods -l <selector-labels>

# Common causes:
# 1. Selector mismatch between Service and Pod labels
kubectl get svc <service-name> -o yaml | grep -A3 selector
kubectl get pods --show-labels

# 2. Readiness probe failing
kubectl describe pod <pod-name> | grep -A10 "Readiness"

# 3. All pods in CrashLoopBackOff
kubectl get pods

# Fix readiness probe
kubectl edit deployment <deployment-name>
# Adjust readinessProbe path, port, or initialDelaySeconds
```

---

### Scenario: Node min=1 max=5, Pod Not Starting

**Symptom:** Cluster Autoscaler is configured with min=1, max=5 nodes. A new pod stays in `Pending` state and no new nodes are added.

```bash
kubectl get pods

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# myapp-7b8c9d6e8-abc12    0/1     Pending   0          5m

kubectl describe pod myapp-7b8c9d6e8-abc12

# Events:
# Warning  FailedScheduling  default-scheduler  0/1 nodes are available:
# 1 Insufficient cpu, 1 Insufficient memory.
```

**Debugging checklist:**

```bash
# Step 1: Check if Cluster Autoscaler is running
kubectl get pods -n kube-system -l app.kubernetes.io/name=cluster-autoscaler

# Output:
# NAME                                  READY   STATUS    RESTARTS   AGE
# cluster-autoscaler-5b8f4d7c9-abc12    1/1     Running   0          5d

# Step 2: Check Cluster Autoscaler logs
kubectl logs -n kube-system deploy/cluster-autoscaler --tail=50 | grep -i "scale\|error\|unschedulable"

# Possible outputs:
# "Pod myapp-7b8c9d6e8-abc12 is unschedulable"
# "Scale-up: setting group size to 2"                    ← Working correctly
# "Max node group size reached"                          ← Already at max=5
# "Pod didn't trigger scale-up: no matching node group"  ← Instance type mismatch

# Step 3: Check node group configuration
eksctl get nodegroup --cluster my-k8s-cluster

# Output:
# NAME        MIN   MAX   DESIRED   INSTANCE TYPE   STATUS
# ng-default  1     5     1         t3.medium       ACTIVE

# Step 4: Check if the pod's resource request exceeds instance capacity
kubectl get pod myapp-7b8c9d6e8-abc12 -o jsonpath='{.spec.containers[0].resources}'

# Output:
# {"requests":{"cpu":"4","memory":"8Gi"}}
# t3.medium has only 2 vCPU and 4GB RAM → pod can NEVER fit!
```

**Common causes and fixes:**

| Cause | Symptom | Fix |
|---|---|---|
| Pod requests > instance capacity | "Insufficient cpu/memory" even with max nodes | Use larger instance type or reduce pod requests |
| Already at max nodes | CA logs: "Max node group size reached" | Increase max in node group config |
| CA not installed/running | No scale-up activity in logs | Install/restart Cluster Autoscaler |
| Node group in wrong AZ | "no matching node group" | Ensure node group spans required AZs |
| Taints on nodes | Pod doesn't tolerate node taints | Add tolerations to pod spec |
| PDB blocking scale-down | Nodes can't be removed to rebalance | Review PDB settings |
| Pod has nodeSelector/affinity | No nodes match the selector | Fix labels or add matching nodes |

```bash
# Fix 1: Increase max nodes
eksctl scale nodegroup --cluster my-k8s-cluster --name ng-default --nodes-max 10

# Fix 2: Use a larger instance type (add a new node group)
eksctl create nodegroup \
  --cluster my-k8s-cluster \
  --name ng-large \
  --node-type m5.xlarge \
  --nodes-min 0 --nodes-max 5

# Fix 3: Reduce pod resource requests
kubectl patch deployment myapp -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"500m","memory":"1Gi"}}}]}}}}'
```

**Interview question: Node autoscaler is set to min=1 max=5 but pods aren't starting. What do you check?**
First check if the pod's resource requests exceed the instance type capacity (e.g., requesting 4 CPU on a t3.medium with 2 vCPU). Then check Cluster Autoscaler logs for errors — it might already be at max nodes, or the pod might have nodeSelector/taints that don't match any node group. Common fixes: use a larger instance type, increase max nodes, or reduce pod resource requests.

### Scenario: Pod CPU=2 & Memory=4Gi Keeps Increasing — Troubleshooting

**Symptom:** A pod with `requests: cpu: 2, memory: 4Gi` is consuming more and more resources over time. Eventually it gets OOMKilled or causes node pressure.

```bash
# Step 1: Check current resource usage
kubectl top pod myapp-7b8c9d6e8-abc12

# Output:
# NAME                     CPU(cores)   MEMORY(bytes)
# myapp-7b8c9d6e8-abc12    1800m        3800Mi         ← Near limits!

# Watch over time
kubectl top pod myapp-7b8c9d6e8-abc12 --containers

# Output:
# POD                      NAME   CPU(cores)   MEMORY(bytes)
# myapp-7b8c9d6e8-abc12    app    1800m        3800Mi

# Step 2: Check resource limits
kubectl get pod myapp-7b8c9d6e8-abc12 -o jsonpath='{.spec.containers[0].resources}'

# Output:
# {"limits":{"cpu":"2","memory":"4Gi"},"requests":{"cpu":"2","memory":"4Gi"}}

# Step 3: Check if pod was OOMKilled
kubectl describe pod myapp-7b8c9d6e8-abc12 | grep -A5 "Last State"

# Output:
# Last State:     Terminated
#   Reason:       OOMKilled        ← Memory exceeded limit
#   Exit Code:    137              ← 128 + 9 (SIGKILL)
#   Started:      Mon, 15 Jan 2024 10:00:00 +0000
#   Finished:     Mon, 15 Jan 2024 14:30:00 +0000

# Step 4: Check node-level pressure
kubectl describe node ip-10-0-1-100.ec2.internal | grep -A5 "Conditions"

# Output:
# Conditions:
#   MemoryPressure   True    KubeletHasInsufficientMemory
#   DiskPressure     False
#   PIDPressure      False
```

**Root cause analysis:**

| Symptom | Likely Cause | Investigation |
|---|---|---|
| Memory grows linearly | Memory leak in application | Profile the app, check heap dumps |
| Memory grows then OOMKilled | No memory limit or limit too low | Set appropriate limits |
| CPU stays at limit | CPU-intensive workload or infinite loop | Profile the app, check thread dumps |
| CPU spikes periodically | Cron-like processing or GC pauses | Check application logs for patterns |
| Both CPU and memory grow | Connection/thread leak | Check open connections, thread count |

**Fixes:**

```bash
# Fix 1: Set proper resource limits (if not set)
kubectl patch deployment myapp -p '{
  "spec":{"template":{"spec":{"containers":[{
    "name":"app",
    "resources":{
      "requests":{"cpu":"500m","memory":"1Gi"},
      "limits":{"cpu":"2","memory":"4Gi"}
    }
  }]}}}
}'

# Fix 2: Add liveness probe to restart leaking pods
kubectl patch deployment myapp -p '{
  "spec":{"template":{"spec":{"containers":[{
    "name":"app",
    "livenessProbe":{
      "httpGet":{"path":"/health","port":8080},
      "periodSeconds":30,
      "failureThreshold":3
    }
  }]}}}
}'

# Fix 3: Use VPA to right-size resources
kubectl apply -f - <<EOF
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Off"    # Recommendation only — review before applying
EOF

kubectl get vpa myapp-vpa -o yaml | grep -A10 "recommendation"

# Output:
# recommendation:
#   containerRecommendations:
#   - containerName: app
#     lowerBound:  {cpu: 200m, memory: 512Mi}
#     target:      {cpu: 800m, memory: 2Gi}     ← Recommended
#     upperBound:  {cpu: 2, memory: 4Gi}

# Fix 4: Use HPA to distribute load across more pods
kubectl autoscale deployment myapp --min=2 --max=10 --cpu-percent=60
```

**Interview question: A pod with CPU=2 and Memory=4Gi keeps increasing resource usage. How do you troubleshoot?**
Use `kubectl top pod` to check current usage, `kubectl describe pod` to check for OOMKilled events (exit code 137). Check if resource limits are set — without limits, a pod can consume all node resources. Common causes: memory leak (linear growth), connection leak (growing thread/connection count), or undersized limits. Fixes: set proper limits, add liveness probes to restart leaking pods, use VPA for right-sizing recommendations, or HPA to distribute load.

---

## 29.6 Control Plane Failures

Control plane components (API server, scheduler, controller manager, etcd) can fail due to misconfiguration, resource exhaustion, or certificate issues. On kubeadm clusters, they run as static pods managed by kubelet from manifests in `/etc/kubernetes/manifests/`.

### Troubleshooting Flow

```bash
# 1. Check node health
kubectl get nodes

# 2. Check control plane pods (kubeadm setup)
kubectl get pods -n kube-system

# 3. Check control plane services (native service setup)
service kube-apiserver status
service kube-controller-manager status
service kube-scheduler status

# 4. Check logs (kubeadm — pod logs)
kubectl logs kube-apiserver-controlplane -n kube-system
kubectl logs kube-scheduler-controlplane -n kube-system
kubectl logs kube-controller-manager-controlplane -n kube-system

# 5. Check logs (native services — journalctl)
sudo journalctl -u kube-apiserver
sudo journalctl -u kube-controller-manager
sudo journalctl -u kube-scheduler
```

### Scheduler Failure — Pods Stuck in Pending

**Symptom:** Pods stay in `Pending` with no events (no node assigned).

```bash
kubectl get pods
# NAME                   READY   STATUS    AGE
# app-586bddbc54-hc779   0/1     Pending   5m

kubectl describe pod app-586bddbc54-hc779
# Node: <none>       ← no node assigned
# Events: <none>     ← no scheduling events at all
```

**Diagnosis:** The scheduler is not running.

```bash
kubectl get pods -n kube-system | grep scheduler
# kube-scheduler-controlplane   0/1   CrashLoopBackOff   6   6m

kubectl logs kube-scheduler-controlplane -n kube-system
# or
kubectl describe pod kube-scheduler-controlplane -n kube-system
# Command: kube-schedulerrrr    ← typo in the command!
# Message: exec: "kube-schedulerrrr": executable file not found in $PATH
```

**Fix:** Edit the static pod manifest:

```bash
vi /etc/kubernetes/manifests/kube-scheduler.yaml
# Fix the command from "kube-schedulerrrr" to "kube-scheduler"
# kubelet automatically restarts the pod when the manifest changes
```

### Controller Manager Failure — Scaling/ReplicaSet Not Working

**Symptom:** `kubectl scale` succeeds but new pods never appear. ReplicaSet shows desired > ready but no new pods are created.

```bash
kubectl scale deploy app --replicas=3
kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# app    1/3     1            1           10m    ← stuck at 1/3
```

**Diagnosis:** The controller manager is not running.

```bash
kubectl get pods -n kube-system | grep controller
# kube-controller-manager-controlplane   0/1   CrashLoopBackOff   4   2m

kubectl logs kube-controller-manager-controlplane -n kube-system
# stat /etc/kubernetes/controller-manager-XXXX.conf: no such file or directory
```

**Fix:** Edit the static pod manifest to correct the kubeconfig path:

```bash
vi /etc/kubernetes/manifests/kube-controller-manager.yaml
# Fix: --kubeconfig=/etc/kubernetes/controller-manager.conf
# (remove the extra characters "XXXX")
```

### Common Control Plane Manifest Errors

| Error | Symptom | Where to look |
|---|---|---|
| **Typo in command** | `CrashLoopBackOff`, exit code 127 | `spec.containers[0].command` in manifest |
| **Wrong kubeconfig path** | `no such file or directory` | `--kubeconfig=` flag in manifest |
| **Wrong certificate path** | `certificate signed by unknown authority` | `--tls-cert-file`, `--client-ca-file` flags |
| **Wrong image tag** | `ImagePullBackOff` | `spec.containers[0].image` in manifest |
| **Port conflict** | `bind: address already in use` | `--secure-port` or `--bind-address` flags |

### Editing Static Pod Manifests

Static pods are managed directly by kubelet, not the API server. Their manifests live in `/etc/kubernetes/manifests/`:

```bash
ls /etc/kubernetes/manifests/
# etcd.yaml
# kube-apiserver.yaml
# kube-controller-manager.yaml
# kube-scheduler.yaml

# Edit a manifest — kubelet detects the change and restarts the pod
vi /etc/kubernetes/manifests/kube-scheduler.yaml

# Watch the pod restart
kubectl get pods -n kube-system --watch
```

> **Note:** If the API server itself is down, `kubectl` won't work. Use `docker ps` or `crictl ps` to check container status, and inspect logs with `crictl logs <container-id>` or `journalctl -u kubelet`.

---

## 29.7 EKS-Specific Errors

### Error: "Unauthorized" when running kubectl

```bash
kubectl get pods

# Output:
# error: You must be logged in to the server (Unauthorized)
```

**Fixes:**
```bash
# 1. Refresh kubeconfig
aws eks update-kubeconfig --name my-k8s-cluster --region us-east-1

# 2. Check AWS identity
aws sts get-caller-identity

# 3. Verify you're in aws-auth ConfigMap
kubectl get configmap aws-auth -n kube-system -o yaml

# 4. Check if using correct AWS profile
export AWS_PROFILE=my-profile
aws eks update-kubeconfig --name my-k8s-cluster
```

### Error: ALB Ingress Not Creating

```bash
kubectl get ingress

# Output:
# NAME          CLASS   HOSTS              ADDRESS   PORTS   AGE
# my-ingress    alb     app.example.com              80      10m
#                                          ↑ No address!
```

**Diagnosis:**
```bash
# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Common errors:
# "failed to build model due to ingress: default/my-ingress: unable to resolve subnet"
# "WebIdentityErr: failed to retrieve credentials"
```

**Fixes:**
```bash
# 1. Check subnet tags
aws ec2 describe-subnets --filters "Name=tag:kubernetes.io/role/elb,Values=1" --query 'Subnets[].SubnetId'
# Public subnets need: kubernetes.io/role/elb = 1
# Private subnets need: kubernetes.io/role/internal-elb = 1

# 2. Check ALB controller is running
kubectl get deployment -n kube-system aws-load-balancer-controller

# 3. Check IAM permissions
# ALB controller service account needs AWSLoadBalancerControllerIAMPolicy

# 4. Check ingress annotations
kubectl describe ingress my-ingress
```

### Error: Pods Can't Pull from ECR

```bash
kubectl describe pod my-pod | grep "Failed to pull image"

# Output:
# Failed to pull image "123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:v1":
# no basic auth credentials
```

**Fix:**
```bash
# Check node IAM role has ECR permissions
# Node role needs: AmazonEC2ContainerRegistryReadOnly

# Or create a pull secret
kubectl create secret docker-registry ecr-cred \
  --docker-server=123456789.dkr.ecr.us-east-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password)

# Add to pod spec:
# spec:
#   imagePullSecrets:
#   - name: ecr-cred
```

---

## 29.8 Operational Errors

### Helm Release Stuck in PENDING_INSTALL

**Symptom:** `helm install` failed partway through, and now the release is stuck. Re-running `helm install` fails with "cannot re-use a name that is still in use."

```bash
helm list --all
# NAME        NAMESPACE   REVISION   STATUS           CHART
# my-release  default     1          pending-install  my-chart-1.0.0

helm install my-release ./my-chart
# Error: cannot re-use a name that is still in use
```

**Fix:**

```bash
# Delete the failed release
helm delete my-release
# or for older Helm versions:
helm delete --purge my-release

# If helm delete also fails, remove the secret directly
kubectl delete secret -l name=my-release,owner=helm

# Now reinstall
helm install my-release ./my-chart
```

**Other stuck states:** `pending-upgrade`, `pending-rollback` — same fix applies. Delete the release and reinstall, or use `helm rollback my-release 0` to roll back to the last successful revision.

### Job Failing to Complete

**Symptom:** Job pods keep failing and restarting, or Job stays incomplete.

```bash
kubectl get jobs
# NAME       COMPLETIONS   DURATION   AGE
# my-job     0/1           10m        10m

kubectl get pods -l job-name=my-job
# NAME             READY   STATUS    RESTARTS   AGE
# my-job-abc12     0/1     Error     0          2m
# my-job-def34     0/1     Error     0          4m
# my-job-ghi56     0/1     Error     0          6m
```

**Diagnosis:**

```bash
kubectl logs my-job-abc12
# Error: database connection refused

kubectl describe job my-job | grep -A5 "Pods Statuses"
# Pods Statuses:    0 Active / 0 Succeeded / 6 Failed
```

**Common Causes & Fixes:**

| Cause | Fix |
|---|---|
| Application error in the job | Fix the command/script, check logs |
| Dependency not available | Ensure databases/services are running before the job |
| `backoffLimit` reached | Job stops retrying after `backoffLimit` failures (default: 6). Fix the error and recreate the job |
| `activeDeadlineSeconds` exceeded | Increase the deadline or optimize the job |

```bash
# Delete and recreate the job (jobs are immutable)
kubectl delete job my-job
kubectl apply -f my-job.yaml

# Check job configuration
kubectl get job my-job -o jsonpath='{.spec.backoffLimit}'
# 6    ← stops after 6 failures
```

### Deployment Not Updating (Image Tag Unchanged)

**Symptom:** You pushed a new image with the same tag (e.g., `latest`), but pods still run the old version.

```bash
kubectl rollout restart deployment/my-app
# This forces new pods to pull the image
```

**Why this happens:** When using `imagePullPolicy: IfNotPresent` (default for non-`latest` tags), the node uses its cached image. Even with `latest`, if the image is already cached, it won't be re-pulled.

**Fixes:**

```yaml
# Fix 1: Use specific image tags (recommended)
image: my-app:v2.0.1    # Not "latest"

# Fix 2: Force pull on every pod start
imagePullPolicy: Always

# Fix 3: Force restart to pull new image
# kubectl rollout restart deployment/my-app
```

> Use immutable image tags (e.g., git SHA, semantic version) in production. The `latest` tag is mutable and causes exactly this problem.

### Pod Security Context Misconfiguration

**Symptom:** Pod rejected by admission controller, or container can't perform expected operations.

```bash
kubectl apply -f my-pod.yaml
# Error from server (Forbidden): pods "my-pod" is forbidden:
#   violates PodSecurity "restricted:latest":
#   allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true
```

**Common Causes & Fixes:**

| Error | Cause | Fix |
|---|---|---|
| `allowPrivilegeEscalation != false` | PSA restricted requires this | Add `securityContext.allowPrivilegeEscalation: false` |
| `runAsNonRoot != true` | Container runs as root | Add `runAsNonRoot: true` and `runAsUser: 1000` |
| `unrestricted capabilities` | Capabilities not dropped | Add `capabilities.drop: ["ALL"]` |
| `seccompProfile` required | Missing Seccomp profile | Add `seccompProfile.type: RuntimeDefault` |
| `privileged` not allowed | Container is privileged | Remove `privileged: true` |

```yaml
# Minimal pod spec that passes PSA "restricted" level
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:1.0
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

```bash
# Check which PSA level a namespace enforces
kubectl get namespace production --show-labels | grep pod-security
# pod-security.kubernetes.io/enforce=restricted

# Test if a pod would be admitted (dry-run)
kubectl apply -f my-pod.yaml --dry-run=server
```

---

## 29.9 Performance Troubleshooting

### High CPU/Memory Usage

```bash
# Check pod resource usage
kubectl top pods --sort-by=cpu

# Output:
# NAME                     CPU(cores)   MEMORY(bytes)
# webapp-abc12             450m         890Mi          ← High!
# webapp-def34             120m         256Mi
# webapp-ghi56             100m         230Mi

# Check node resource usage
kubectl top nodes

# Output:
# NAME                          CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# ip-10-0-1-100.ec2.internal    1800m        90%    3500Mi          87%    ← Overloaded!

# Find resource-hungry pods
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.namespace + "/" + .metadata.name'
# Lists pods without resource limits (dangerous!)
```

### Slow Pod Startup

```bash
# Check events for scheduling delays
kubectl describe pod slow-pod | grep -A20 Events

# Common causes:
# 1. Large image size → Use smaller base images (alpine)
# 2. Image not cached → Use imagePullPolicy: IfNotPresent
# 3. Init containers taking long → Optimize init logic
# 4. Slow readiness probe → Reduce initialDelaySeconds
# 5. Resource contention → Check node capacity
```

---

## 29.10 Quick Reference: Error → Solution

| Error | Quick Fix |
|---|---|
| `CrashLoopBackOff` | `kubectl logs <pod> --previous` → fix app error |
| `ImagePullBackOff` | Check image name, tag, and registry credentials |
| `Pending` | Check resources: `kubectl describe pod` → scale nodes |
| `OOMKilled` (exit code 137) | Increase `resources.limits.memory` |
| `CreateContainerConfigError` | Create missing ConfigMap/Secret |
| `Evicted` | Node disk/memory pressure → clean up or add nodes |
| `NodeNotReady` | `kubectl describe node` → check conditions |
| `Unauthorized` | `aws eks update-kubeconfig --name <cluster>` |
| `No endpoints` | Fix service selector to match pod labels |
| `DNS failure` | Check CoreDNS: `kubectl get pods -n kube-system` |
| `PVC Pending` | Check StorageClass, EBS CSI driver, IAM |
| `Multi-Attach error` | Delete old pod or use EFS (RWX) |
| `ALB not creating` | Check subnet tags, ALB controller, IAM |
| `Forbidden (RBAC)` | `kubectl auth can-i` → create Role/RoleBinding |
| `Terminating` (stuck) | Remove finalizers or force delete: `kubectl delete pod --force --grace-period=0` |
| `ContainerCreating` (stuck) | Check CNI plugin, volume mounts, subnet IPs |
| `Init:0/1` (stuck) | Check init container logs: `kubectl logs <pod> -c <init-container>` |
| `FailedCreatePodSandBox` | Check CNI plugin, container runtime: `systemctl status containerd` |
| `External-IP <pending>` | Check cloud LB controller, subnet tags, IAM |
| Ingress 404 | Check backend endpoints, service port, path rewrite |
| Ingress 502 | Check backend pod health, targetPort mismatch |
| Ingress redirect loop | Disable `ssl-redirect` annotation when TLS terminates externally |
| `PV Released` (won't rebind) | Remove claimRef: `kubectl patch pv <pv> -p '{"spec":{"claimRef":null}}'` |
| Volume permission denied | Set `fsGroup` in securityContext or use init container to fix permissions |
| `exceeded quota` | Increase ResourceQuota or reduce pod resource requests |
| Namespace stuck `Terminating` | Fix broken API services, or remove finalizers as last resort |
| Helm `pending-install` | `helm delete <release>` then reinstall |
| Job not completing | Check logs, fix errors, delete and recreate (jobs are immutable) |
| Image not updating | Use specific tags, not `latest`. Force: `kubectl rollout restart` |
| PSA violation | Add required securityContext fields for the namespace's PSA level |
| Probe failures (liveness) | Fix probe path/port, increase `initialDelaySeconds` |
| Probe failures (readiness) | Fix probe, or pods won't receive traffic via Service |

---

## 29.11 Debugging Toolkit

### Must-Have Debug Images

```bash
# Network debugging
kubectl run netshoot --image=nicolaka/netshoot --rm -it -- /bin/bash
# Tools: curl, wget, nslookup, dig, traceroute, tcpdump, nmap, iperf

# AWS CLI debugging
kubectl run aws-debug --image=amazon/aws-cli --rm -it -- /bin/bash
# Tools: aws cli for testing IAM, S3, ECR access

# General debugging
kubectl run debug --image=busybox --rm -it -- /bin/sh
# Tools: wget, nslookup, basic unix tools

# Kubernetes debug containers (ephemeral containers)
kubectl debug -it <pod-name> --image=busybox --target=<container-name>
```

### Useful One-Liners

```bash
# Find all pods not in Running state
kubectl get pods -A --field-selector status.phase!=Running

# Find pods with high restart counts
kubectl get pods -A -o json | jq -r '.items[] | select(.status.containerStatuses[]?.restartCount > 5) | .metadata.namespace + "/" + .metadata.name + " restarts=" + (.status.containerStatuses[0].restartCount | tostring)'

# Get all events sorted by time
kubectl get events -A --sort-by='.lastTimestamp' | tail -20

# Find pods without resource limits
kubectl get pods -A -o json | jq -r '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.namespace + "/" + .metadata.name'

# Check certificate expiry
kubectl get secret -A -o json | jq -r '.items[] | select(.type=="kubernetes.io/tls") | .metadata.namespace + "/" + .metadata.name'

# Force delete stuck namespace
kubectl get namespace stuck-ns -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/stuck-ns/finalize" -f -

# Get pod resource usage vs requests
kubectl top pods --containers | sort -k3 -rn | head -10
```

### JSONPath Queries with kubectl

JSONPath lets you extract and format specific fields from Kubernetes JSON output. Essential for CKA exam questions and production reporting.

**Basic queries:**

```bash
# Get all node names
kubectl get nodes -o=jsonpath='{.items[*].metadata.name}'
# master node01

# Get CPU capacity per node
kubectl get nodes -o=jsonpath='{.items[*].status.capacity.cpu}'
# 4 4

# Get hardware architecture
kubectl get nodes -o=jsonpath='{.items[*].status.nodeInfo.architecture}'
# amd64 amd64

# Get a specific pod's container image
kubectl get pods -o=jsonpath='{.items[0].spec.containers[0].image}'
# nginx:alpine
```

**Combining multiple expressions:**

```bash
# Node names on line 1, CPU counts on line 2
kubectl get nodes -o=jsonpath='{.items[*].metadata.name}{"\n"}{.items[*].status.capacity.cpu}'
# master node01
# 4 4
```

**Range loops — iterate and format as a table:**

```bash
# Print each node's name and CPU on its own line
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
# master   4
# node01   4

# Print pod name, namespace, and status
kubectl get pods -A -o=jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

**Custom columns — simpler alternative to range loops:**

```bash
# No need for .items — kubectl iterates automatically
kubectl get nodes -o=custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu
# NODE     CPU
# master   4
# node01   4

kubectl get pods -o=custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,NODE:.spec.nodeName
```

**Sorting:**

```bash
kubectl get nodes --sort-by=.metadata.name
kubectl get nodes --sort-by=.status.capacity.cpu
kubectl get pods -A --sort-by=.metadata.creationTimestamp
```

**Filter expressions — selecting items by field value:**

JSONPath supports filter expressions with `?()` to select array elements matching a condition. The `@` symbol refers to the current element being evaluated.

```bash
# Get InternalIP of all nodes (filter by address type)
kubectl get nodes -o=jsonpath='{range .items[*]}{.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}'

# Get only Ready nodes
kubectl get nodes -o=jsonpath='{range .items[*]}{.status.conditions[?(@.type=="Ready")].status}{"\t"}{.metadata.name}{"\n"}{end}'

# Get pods in CrashLoopBackOff
kubectl get pods -A -o=jsonpath='{range .items[*]}{range .status.containerStatuses[*]}{?(@.state.waiting.reason=="CrashLoopBackOff")}{.name}{"\n"}{end}{end}'
```

| Filter Pattern | What it does |
|---|---|
| `[?(@.type=="InternalIP")]` | Select elements where `type` equals `InternalIP` |
| `[?(@.status=="True")]` | Select elements where `status` equals `True` |
| `[?(@.key=="env")]` | Select elements where `key` equals `env` |

**Useful JSONPath examples for troubleshooting:**

```bash
# Get pod CIDR per node
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'

# Get InternalIP of all nodes (save to file — common exam task)
kubectl get nodes -o=jsonpath='{range .items[*]}{.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}' > /root/node_ips

# Get all container images in the cluster
kubectl get pods -A -o=jsonpath='{range .items[*]}{range .spec.containers[*]}{.image}{"\n"}{end}{end}' | sort -u

# Get nodes with taints
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints[*].effect}{"\n"}{end}'

# Get PV sorted by capacity
kubectl get pv --sort-by=.spec.capacity.storage -o=custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase
```

---

## 29.12 Pod Log Storage & Centralized Logging — Deep Dive

### Where Are Pod Logs Stored?

When a container writes to `stdout` or `stderr`, the container runtime (containerd) captures the output and stores it as log files on the node's filesystem.

```
┌──────────────────────────────────────────────────────────────┐
│  Pod Log Lifecycle                                           │
│                                                              │
│  Container (stdout/stderr)                                   │
│       │                                                      │
│       ▼                                                      │
│  Container Runtime (containerd)                              │
│       │                                                      │
│       ▼                                                      │
│  Node Filesystem:                                            │
│  /var/log/pods/<namespace>_<pod-name>_<pod-uid>/<container>/ │
│       │                                                      │
│  Symlinked from:                                             │
│  /var/log/containers/<pod>_<ns>_<container>-<id>.log         │
│       │                                                      │
│       ▼                                                      │
│  kubectl logs <pod> reads from here via kubelet API          │
│                                                              │
│  ⚠️  Logs are EPHEMERAL:                                     │
│  - Pod deleted → logs deleted                                │
│  - Node dies → logs lost                                     │
│  - Log rotation: default 10MB per file, 5 files max          │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Where logs are stored on the node
# SSH into a node or use a debug container:
kubectl debug node/ip-10-0-1-100.ec2.internal -it --image=busybox

# Log directory structure:
ls /host/var/log/pods/

# Output:
# default_nginx-7b8c9d6e8-abc12_a1b2c3d4-e5f6-7890/
# kube-system_coredns-5d78c9869d-def34_f1g2h3i4-j5k6/

ls /host/var/log/pods/default_nginx-7b8c9d6e8-abc12_a1b2c3d4-e5f6-7890/nginx/

# Output:
# 0.log        ← Current log file
# 0.log.20240115-120000.gz   ← Rotated log (compressed)

# View the raw log file
cat /host/var/log/pods/default_nginx-7b8c9d6e8-abc12_a1b2c3d4-e5f6-7890/nginx/0.log

# Output (CRI log format):
# 2024-01-15T12:00:00.123456789Z stdout F 10.0.1.5 - - [15/Jan/2024:12:00:00 +0000] "GET / HTTP/1.1" 200 615
# 2024-01-15T12:00:01.234567890Z stderr F 2024/01/15 12:00:01 [error] open() "/usr/share/nginx/html/favicon.ico" failed
```

**Symlink structure explained:**

```bash
# /var/log/containers/ contains symlinks pointing to /var/log/pods/
ls -la /host/var/log/containers/

# Output:
# nginx-7b8c9d6e8-abc12_default_nginx-a1b2c3d4.log -> /var/log/pods/default_nginx-7b8c9d6e8-abc12_uid/nginx/0.log
# coredns-5d78c9869d-def34_kube-system_coredns-f1g2h3.log -> /var/log/pods/kube-system_coredns-5d78c9869d-def34_uid/coredns/0.log

# Why symlinks?
# - /var/log/containers/ provides a flat, easy-to-glob directory for log collectors
# - /var/log/pods/ is the actual storage location organized by pod
# - Log collectors (Fluent Bit) typically read from /var/log/containers/*.log
#   or /var/log/pods/*/*/*.log

# containerd stores logs here and kubelet manages rotation
# The CRI log format is: <timestamp> <stream> <tag> <message>
# stream = stdout or stderr
# tag = F (full line) or P (partial line, for very long log lines)
```

### kubectl logs — How It Works

```bash
# Basic log commands
kubectl logs nginx-pod                    # Current logs
kubectl logs nginx-pod --previous         # Logs from previous crashed container
kubectl logs nginx-pod -c sidecar         # Specific container in multi-container pod
kubectl logs nginx-pod --tail=100         # Last 100 lines
kubectl logs nginx-pod --since=1h         # Logs from last hour
kubectl logs nginx-pod -f                 # Stream logs (follow)
kubectl logs -l app=web --all-containers  # All pods with label app=web

# What happens internally:
# 1. kubectl sends request to API Server
# 2. API Server proxies to kubelet on the node
# 3. kubelet reads /var/log/pods/<pod>/<container>/0.log
# 4. Returns the content to kubectl
```

### Log Rotation Configuration

```bash
# kubelet controls log rotation via these flags:
# --container-log-max-size=10Mi    (default: 10MB per log file)
# --container-log-max-files=5     (default: 5 rotated files)

# On EKS, check kubelet config:
kubectl get configmap kubelet-config -n kube-system -o yaml | grep -A2 containerLog

# Total log storage per container = max-size × max-files = 50MB by default
# For a node with 30 pods, that's up to 1.5GB of logs

# To change on EKS, use a launch template with custom kubelet config:
# --container-log-max-size=50Mi
# --container-log-max-files=3
```

### The Problem: Logs Are Ephemeral

```
Pod deleted     → Logs gone immediately
Node terminated → Logs gone
Log rotated     → Old logs overwritten
CrashLoopBackOff → Only --previous shows last crash, earlier crashes lost

Solution: Ship logs to a centralized system BEFORE they're lost
```

### Centralized Logging Architecture (EFK Stack)

```
┌──────────────────────────────────────────────────────────────┐
│  EFK Stack (Elasticsearch + Fluentd/Fluent Bit + Kibana)     │
│                                                              │
│  ┌─── Node 1 ──────────┐  ┌─── Node 2 ──────────┐          │
│  │  Pod A  Pod B        │  │  Pod C  Pod D        │          │
│  │    │      │          │  │    │      │          │          │
│  │    ▼      ▼          │  │    ▼      ▼          │          │
│  │  /var/log/pods/      │  │  /var/log/pods/      │          │
│  │         │            │  │         │            │          │
│  │  ┌──────▼──────┐     │  │  ┌──────▼──────┐     │          │
│  │  │ Fluent Bit  │     │  │  │ Fluent Bit  │     │          │
│  │  │ (DaemonSet) │     │  │  │ (DaemonSet) │     │          │
│  │  └──────┬──────┘     │  │  └──────┬──────┘     │          │
│  └─────────┼────────────┘  └─────────┼────────────┘          │
│            │                         │                       │
│            └────────┬────────────────┘                       │
│                     ▼                                        │
│            ┌────────────────┐                                │
│            │ Elasticsearch  │  (or CloudWatch / OpenSearch)   │
│            │ (StatefulSet)  │                                │
│            └───────┬────────┘                                │
│                    │                                         │
│                    ▼                                         │
│            ┌────────────────┐                                │
│            │    Kibana      │  (Dashboard for searching logs) │
│            │  (Deployment)  │                                │
│            └────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

### Deploying Fluent Bit as a DaemonSet

```yaml
# fluent-bit-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
  labels:
    app: fluent-bit
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2
        resources:
          limits:
            memory: 200Mi
          requests:
            cpu: 100m
            memory: 100Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlogpods
          mountPath: /var/log/pods
          readOnly: true
        - name: config
          mountPath: /fluent-bit/etc/
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlogpods
        hostPath:
          path: /var/log/pods
      - name: config
        configMap:
          name: fluent-bit-config
```

```yaml
# fluent-bit-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/pods/*/*/*.log
        Parser            cri
        Tag               kube.*
        Refresh_Interval  10
        Mem_Buf_Limit     5MB
        Skip_Long_Lines   On

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_Tag_Prefix     kube.var.log.pods.
        Merge_Log           On
        K8S-Logging.Parser  On

    [OUTPUT]
        Name            es
        Match           *
        Host            elasticsearch.logging.svc.cluster.local
        Port            9200
        Index           k8s-logs
        Type            _doc

  parsers.conf: |
    [PARSER]
        Name        cri
        Format      regex
        Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<log>.*)$
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

```bash
kubectl create namespace logging
kubectl apply -f fluent-bit-config.yaml
kubectl apply -f fluent-bit-daemonset.yaml

kubectl get daemonset -n logging

# Output:
# NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   AGE
# fluent-bit   3         3         3       3            3           30s
```

### AWS CloudWatch Logs (EKS Alternative)

For EKS, you can use the AWS-managed Fluent Bit integration instead of self-managed EFK:

```bash
# Enable CloudWatch logging on EKS
eksctl utils update-cluster-logging \
  --enable-types=all \
  --cluster=my-k8s-cluster \
  --approve

# Install Fluent Bit for CloudWatch (AWS-managed)
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonSet/container-insights-monitoring/fluent-bit/fluent-bit.yaml

# Logs appear in CloudWatch under:
# /aws/containerinsights/<cluster-name>/application
# /aws/containerinsights/<cluster-name>/host
# /aws/containerinsights/<cluster-name>/dataplane
```

### Application Logs vs stdout

```
Best practice: Applications should log to stdout/stderr, NOT to files.

Why?
- stdout/stderr is captured by the container runtime automatically
- kubectl logs works out of the box
- Log collectors (Fluent Bit) pick them up without extra config
- No risk of filling up container filesystem

If your app writes to files (e.g., /var/log/app.log):
- Use a sidecar container to tail the file and output to stdout
- Or configure Fluent Bit to read the file directly via hostPath
```

### Sidecar Pattern for File-Based Logs

```yaml
# When an app writes logs to a file instead of stdout
apiVersion: v1
kind: Pod
metadata:
  name: legacy-app
spec:
  containers:
  - name: app
    image: legacy-app:1.0
    # App writes to /var/log/app.log (not stdout)
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  - name: log-streamer
    image: busybox
    command: ["sh", "-c", "tail -f /var/log/app.log"]
    # Now "kubectl logs legacy-app -c log-streamer" shows the logs
    volumeMounts:
    - name: log-volume
      mountPath: /var/log
  volumes:
  - name: log-volume
    emptyDir: {}
```

### Log Storage Comparison

| Method | Persistence | Search | Cost | Best For |
|---|---|---|---|---|
| `kubectl logs` | Ephemeral (pod lifetime) | No | Free | Quick debugging |
| Node filesystem | Until node dies or rotation | No | Free | Short-term |
| CloudWatch Logs | Configurable retention | Yes (Insights) | Per GB ingested | EKS production |
| EFK/ELK Stack | Configurable retention | Yes (Kibana) | Self-managed | On-prem / multi-cloud |
| Grafana Loki | Configurable retention | Yes (Grafana) | Self-managed | Lightweight alternative to EFK |
| Datadog/Splunk | Configurable retention | Yes | SaaS pricing | Enterprise |

**Interview question: Where are pod logs stored and what happens when a pod is deleted?**
Container logs are written to `/var/log/pods/<namespace>_<pod-name>_<uid>/<container>/` on the node. When a pod is deleted, kubelet garbage-collects the log files. When a node is terminated, all logs on it are lost. This is why production clusters use a DaemonSet (Fluent Bit/Fluentd) to ship logs to a centralized system (CloudWatch, Elasticsearch) before they're lost.

---

## 29.13 Module 9 Exercises

### Exercise 1: Debug a Broken Deployment
```bash
# Create a deliberately broken deployment
kubectl create deployment broken --image=nginx:nonexistent
# Diagnose and fix it
kubectl describe pod -l app=broken
kubectl set image deployment/broken nginx=nginx:1.25
kubectl rollout status deployment/broken
```

### Exercise 2: Debug Networking
```bash
# 1. Create a deployment and service with mismatched labels
kubectl create deployment web --image=nginx
kubectl expose deployment web --port=80 --selector=app=wrong-label
# 2. Debug why the service has no endpoints
kubectl get endpoints web
# 3. Fix the service selector
kubectl patch service web -p '{"spec":{"selector":{"app":"web"}}}'
```

### Exercise 3: Resource Pressure
```bash
# 1. Create a pod that consumes too much memory
kubectl run memory-hog --image=polinux/stress --command -- stress --vm 1 --vm-bytes 2G
# 2. Watch it get OOMKilled
kubectl get pods -w
# 3. Fix with proper resource limits
```

---

## 29.14 Congratulations!

You have completed the Kubernetes on AWS course. Here's a summary of what you've learned:

| Module | Topics Covered |
|---|---|
| 1. Fundamentals | Architecture, kubectl, namespaces, objects |
| 2. EKS Setup | eksctl, Terraform, VPC-CNI, IAM integration |
| 3. Workloads | Pods, ReplicaSets, Deployments, StatefulSets, Jobs |
| 4. Networking | Services, Ingress, ALB, NetworkPolicies, DNS |
| 5. Storage | PV/PVC, EBS, EFS, ConfigMaps, Secrets |
| 6. Advanced | Scheduling, HPA/VPA/CA, RBAC, Security |
| 7. DevOps | Helm, CI/CD, ArgoCD, Prometheus, Grafana |
| 8. Projects | E-Commerce, Blue-Green, Multi-Tenant, ML Serving |
| 9. Troubleshooting | Error diagnosis, debugging tools, quick fixes |

### Next Steps
1. Get **CKA** (Certified Kubernetes Administrator) certification
2. Explore **service mesh** (Istio, Linkerd)
3. Learn **GitOps** with ArgoCD or Flux
4. Study **eBPF** for advanced networking (Cilium)
5. Practice on [killer.sh](https://killer.sh) for exam preparation

---

## 29.15 Advanced Debug Commands Quick Reference

Commands organized by debugging scenario. These go beyond basic `kubectl get/describe/logs` for production-level troubleshooting.

### Cluster Health

```bash
# API server liveness and readiness probes
kubectl get --raw='/livez'
# ok

kubectl get --raw='/readyz?verbose'
# [+]ping ok
# [+]log ok
# [+]etcd ok
# [+]poststarthook/start-kube-apiserver-admission-initializer ok
# ...
# readyz check passed

# Check supported API versions (find deprecations)
kubectl api-versions | sort

# Check available resource types (verify CRDs exist)
kubectl api-resources | grep <resource-type>

# Default namespace sanity check
kubectl config view --minify -o jsonpath='{.contexts[0].context.namespace}'

# Leader election status (controller-manager, scheduler)
kubectl get lease -n kube-system
# NAME                                  HOLDER                                          AGE
# kube-controller-manager               ip-10-0-1-50_abc123                             5d
# kube-scheduler                        ip-10-0-1-50_def456                             5d
```

### Node-Level Debugging

```bash
# Node conditions (scriptable)
kubectl get node <node> -o json | jq '.status.conditions'
# [
#   { "type": "MemoryPressure", "status": "False" },
#   { "type": "DiskPressure",   "status": "False" },
#   { "type": "PIDPressure",    "status": "False" },
#   { "type": "Ready",          "status": "True"  }
# ]

# See all taints quickly
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints}{"\n"}{end}'

# What pods are on a specific node
kubectl get pods -A --field-selector spec.nodeName=<node>

# Node IPs and hostnames
kubectl get node <node> -o jsonpath='{.status.addresses[*].address}'

# Container runtime version
kubectl get node <node> -o jsonpath='{.status.nodeInfo.containerRuntimeVersion}'
# containerd://1.7.2

# Debug a node's network namespace directly
kubectl debug node/<node> -it --image=nicolaka/netshoot -- bash
```

### Pod Advanced Debugging

```bash
# Container state details (Waiting/Running/Terminated with reasons)
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.containerStatuses[*].state}'

# QoS class (determines eviction priority)
kubectl get pod <pod> -n <ns> -o jsonpath='{.status.qosClass}'
# Guaranteed | Burstable | BestEffort

# Who owns this pod (ReplicaSet, Job, DaemonSet)
kubectl get pod <pod> -n <ns> -o jsonpath='{.metadata.ownerReferences}'

# Which node hosts this pod
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.nodeName}'

# Affinity/anti-affinity rules
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.affinity}'

# Tolerations
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.tolerations}'

# Pod-scoped events only
kubectl get events -n <ns> --field-selector involvedObject.name=<pod>

# Ephemeral debug container (attach to running pod without modifying it)
kubectl debug -it <pod> -n <ns> --image=busybox --target=<container>

# Copy pod for debugging with shared PID namespace
kubectl debug -it --image=busybox --share-processes --copy-to=dbg-<pod> pod/<pod> -n <ns>

# View ephemeral containers attached to a pod
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.ephemeralContainers}'

# Process tree inside container
kubectl exec -it <pod> -n <ns> -- pstree -al
```

### Service & Network Debugging

```bash
# Verify service-to-pod link
kubectl get endpoints <svc> -n <ns>

# Pod names behind a service
kubectl get endpoints <svc> -n <ns> -o jsonpath='{.subsets[*].addresses[*].targetRef.name}'

# Service type
kubectl get svc <svc> -n <ns> -o jsonpath='{.spec.type}'

# External traffic policy (source IP preservation)
kubectl get svc <svc> -n <ns> -o jsonpath='{.spec.externalTrafficPolicy}'

# Load balancer hostname (cloud)
kubectl get svc <svc> -n <ns> -o jsonpath='{.status.loadBalancer.ingress[*].hostname}'

# Ingress class present?
kubectl get ingressclass

# EndpointSlice health (modern service discovery)
kubectl get endpointslices -n <ns> -o wide

# In-pod network debugging
kubectl exec -it <pod> -n <ns> -- nslookup <svc>
kubectl exec -it <pod> -n <ns> -- curl -sv http://<svc>:<port>/health
kubectl exec -it <pod> -n <ns> -- ss -tulpn          # Socket listeners
kubectl exec -it <pod> -n <ns> -- ip route            # Routing table
kubectl exec -it <pod> -n <ns> -- cat /etc/resolv.conf # DNS config
```

### Deployment & Rollout Debugging

```bash
# Server-side diff (live vs desired)
kubectl diff -f deploy.yaml

# Validate change without applying
kubectl apply -f deploy.yaml --server-side --dry-run=server -o yaml

# Blocked rollout reason
kubectl get deploy/<dep> -n <ns> -o jsonpath='{.status.conditions}'

# Hot-fix image tag
kubectl set image deploy/<dep> <container>=<image>:<tag> -n <ns>

# Quarantine noisy workload (scale to 0)
kubectl scale deploy/<dep> --replicas=0 -n <ns>

# Flip environment variable
kubectl set env deploy/<dep> KEY=VALUE -n <ns>

# Annotate rollout for history
kubectl annotate deploy/<dep> kubernetes.io/change-cause='hotfix: fix db timeout' -n <ns>

# Restart deployment to pick up ConfigMap/Secret changes
kubectl rollout restart deploy/<dep> -n <ns>

# Block until deployment is ready
kubectl wait --for=condition=Available deploy/<dep> -n <ns> --timeout=90s
```

### Resource & Scheduling Debugging

```bash
# Requests/limits audit across all pods in namespace
kubectl get pods -n <ns> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'

# OOMKilled traces
kubectl describe pod <pod> -n <ns> | grep -i oom

# Node pressure evictions
kubectl get events -A --field-selector reason=Evicted

# Scheduling failures
kubectl get events --field-selector reason=FailedScheduling -A

# CrashLoop storms
kubectl get events -A --field-selector reason=BackOff

# Image audit across all deployments
kubectl get deploy -A -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.template.spec.containers[*].image}{"\n"}{end}'

# Hot-adjust resources without redeploying
kubectl set resources deploy/<dep> -n <ns> --limits=cpu=500m,memory=512Mi --requests=cpu=250m,memory=256Mi
```

### CRI-Level Debugging (on the node)

When `kubectl` can't reach the API server, use CRI tools directly on the node:

```bash
# List all containers (including stopped)
crictl ps -a

# Container logs via CRI
crictl logs <container-id>

# Exit code and reason
crictl inspect <container-id> | jq '.status.exitCode,.status.reason'

# Kubelet logs
journalctl -u kubelet --since '1 hour ago'

# Container log files on disk
ls /var/log/containers | grep <pod>

# Cached images
crictl images | grep <repo>

# kube-proxy listening
sudo ss -plnt | grep kube-proxy

# iptables rules (kube-proxy iptables mode)
iptables -S | grep KUBE-
```

### Admission & Webhook Debugging

```bash
# List all admission webhooks
kubectl get mutatingwebhookconfigurations,validatingwebhookconfigurations

# Inspect webhook rules, failure policy, timeouts
kubectl describe validatingwebhookconfiguration <name>

# Check if CRDs exist
kubectl get crd | head

# Inspect CRD instance
kubectl describe <crd-kind> <name> -n <ns>
```

### Cluster-Wide Health Snapshot

```bash
# One-liner: all pods with phase and restart count
kubectl get pods -A -o custom-columns=\
NS:.metadata.namespace,\
POD:.metadata.name,\
PHASE:.status.phase,\
RESTARTS:.status.containerStatuses[*].restartCount | column -t

# Failed pods cluster-wide
kubectl get pods -A --field-selector status.phase=Failed

# Pending pods (scheduling backlog)
kubectl get pods -A --field-selector status.phase=Pending

# Recent cluster events (last 50)
kubectl get events -A --sort-by=.lastTimestamp | tail -n 50
```

---

## 29.16 Additional Production Errors

### Context Deadline Exceeded

**Cause:** A Kubernetes API request times out — the API server is overloaded, network is slow, or etcd is unresponsive.

```bash
# Symptom
kubectl get pods
# error: context deadline exceeded

# Diagnosis
# 1. Check API server health
kubectl get --raw='/readyz?verbose' 2>/dev/null || echo "API server unreachable"

# 2. Check API server pod logs (if accessible)
kubectl logs -n kube-system kube-apiserver-<node> --tail=50

# 3. Increase timeout for the command
kubectl get pods --request-timeout=60s

# 4. Check etcd health (etcd latency causes API timeouts)
kubectl -n kube-system exec etcd-<node> -- etcdctl endpoint health \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 5. Check API server resource usage
kubectl top pods -n kube-system | grep apiserver
```

**Fixes:**
- Reduce API call volume (optimize controllers, reduce watch connections)
- Scale API server replicas (multi-master setup)
- Check etcd disk I/O — etcd needs fast SSDs
- Verify network connectivity between nodes and control plane

---

### Kubelet Certificate Rotation Failing

**Cause:** The kubelet cannot rotate its client certificate, causing node authentication failures.

```bash
# Symptom — node goes NotReady after certificate expires
kubectl get nodes
# NAME       STATUS     ROLES    AGE    VERSION
# worker-1   NotReady   <none>   365d   v1.28.0

# Diagnosis
# 1. Check certificate expiration
sudo openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -dates
# notAfter=Jan 15 10:00:00 2024 GMT

# 2. Check kubelet logs for rotation errors
journalctl -u kubelet | grep -i "certificate\|rotate\|expired"

# 3. Check if auto-rotation is enabled
cat /var/lib/kubelet/config.yaml | grep rotateCertificates
# rotateCertificates: true

# Fix: Manually renew certificates
sudo kubeadm certs renew all

# Restart kubelet
sudo systemctl restart kubelet

# Verify node is Ready again
kubectl get nodes
```

**Prevention:** Ensure `rotateCertificates: true` in kubelet config. Monitor certificate expiration with alerts.

---

### Pod IP Conflict

**Cause:** Two pods are assigned the same IP due to CNI plugin misconfiguration or CIDR overlap.

```bash
# Symptom — intermittent connectivity, wrong pod responds
kubectl get pods -o wide
# NAME       READY   STATUS    IP            NODE
# pod-a      1/1     Running   10.244.1.5    worker-1
# pod-b      1/1     Running   10.244.1.5    worker-2   ← same IP!

# Diagnosis
# 1. Check CNI plugin logs
kubectl logs -n kube-system -l k8s-app=calico-node --tail=50

# 2. Check pod CIDR allocation per node
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
# worker-1   10.244.1.0/24
# worker-2   10.244.1.0/24   ← OVERLAP! Both nodes have same CIDR

# 3. Check cluster CIDR configuration
kubectl cluster-info dump | grep -i cidr

# Fix: Restart CNI plugin to reassign IPs
kubectl rollout restart daemonset calico-node -n kube-system

# If CIDR overlap: reconfigure the CNI plugin with non-overlapping ranges
# or reinstall the CNI with correct podCIDR settings
```

---

### ConfigMap Too Large

**Cause:** ConfigMaps have a hard limit of 1 MB. Exceeding this causes creation/update failures.

```bash
# Symptom
kubectl create configmap large-config --from-file=big-file.json
# error: ConfigMap "large-config" is invalid: data: Too long: must have at most 1048576 bytes

# Check current ConfigMap size
kubectl get configmap my-config -o json | wc -c
# 1234567   ← exceeds 1MB

# Solutions:
# 1. Split into multiple ConfigMaps
kubectl create configmap config-part1 --from-file=part1.json
kubectl create configmap config-part2 --from-file=part2.json

# 2. Use a PersistentVolume for large config files
# Mount a PVC with the config file instead of a ConfigMap

# 3. Use an init container to download config from S3/GCS
# initContainers:
# - name: config-downloader
#   image: amazon/aws-cli
#   command: ["aws", "s3", "cp", "s3://bucket/config.json", "/config/"]
#   volumeMounts:
#   - name: config-vol
#     mountPath: /config
```

---

### Pod Logs Truncated

**Cause:** Container runtime log rotation removes old log entries, or the log buffer is too small.

```bash
# Symptom — logs are incomplete or missing older entries
kubectl logs my-pod --tail=1000
# Only shows recent logs, older entries are gone

# Diagnosis
# 1. Check container runtime log settings on the node
cat /etc/containerd/config.toml | grep -A5 "max-size\|max-file"

# 2. Check log file size on disk
ls -lh /var/log/containers/ | grep my-pod
# -rw-r----- 1 root root 10M Jan 15 10:00 my-pod_default_app-abc123.log

# 3. Check kubelet log rotation config
cat /var/lib/kubelet/config.yaml | grep -A3 "containerLog"
# containerLogMaxSize: "10Mi"    ← max 10MB per log file
# containerLogMaxFiles: 5        ← keep 5 rotated files

# Fix: Increase log retention
# Edit /var/lib/kubelet/config.yaml:
# containerLogMaxSize: "100Mi"
# containerLogMaxFiles: 10
# Then restart kubelet: sudo systemctl restart kubelet

# Long-term fix: Use centralized logging (Loki, EFK)
# so logs are preserved beyond container lifecycle
```

> **Cross-reference:** Centralized logging → MODULE-27 Sections 27.4, 27.8

---

### Kube-proxy Failing

**Cause:** kube-proxy is not functioning, breaking Service routing (ClusterIP, NodePort, LoadBalancer all stop working).

```bash
# Symptom — services don't route traffic, curl to ClusterIP hangs
kubectl exec debug-pod -- curl -s --max-time 5 http://my-service:80
# curl: (28) Connection timed out

# Diagnosis
# 1. Check kube-proxy pods
kubectl get pods -n kube-system -l k8s-app=kube-proxy
# NAME               READY   STATUS             RESTARTS   AGE
# kube-proxy-abc12   0/1     CrashLoopBackOff   5          10m

# 2. Check kube-proxy logs
kubectl logs -n kube-system -l k8s-app=kube-proxy --tail=20

# 3. Check iptables rules (kube-proxy iptables mode)
sudo iptables -t nat -L KUBE-SERVICES | head -20

# Fix: Restart kube-proxy
kubectl rollout restart daemonset kube-proxy -n kube-system

# If config is wrong, check the ConfigMap
kubectl get configmap kube-proxy -n kube-system -o yaml
```

---

### Cluster Autoscaler Scaling Too Slowly

**Cause:** The Cluster Autoscaler has conservative default settings or the cloud provider is slow to provision nodes.

```bash
# Symptom — pods stay Pending for minutes even though autoscaler is enabled
kubectl get pods | grep Pending
# my-pod-abc12   0/1   Pending   0   5m

# Diagnosis
# 1. Check autoscaler logs
kubectl logs -n kube-system -l app=cluster-autoscaler --tail=30

# 2. Check autoscaler status
kubectl get configmap cluster-autoscaler-status -n kube-system -o yaml

# Fix: Tune autoscaler parameters
# --scale-down-delay-after-add=5m     (default: 10m — reduce for faster scale-down)
# --scale-down-unneeded-time=5m       (default: 10m)
# --max-node-provision-time=10m       (default: 15m)
# --scan-interval=10s                 (default: 10s — already fast)

# For EKS: ensure the node group max size is high enough
eksctl get nodegroup --cluster my-cluster
# NAME      MIN   MAX   DESIRED
# workers   2     5     3       ← max=5 may be too low
```

> **Cross-reference:** Cluster Autoscaler / Karpenter → MODULE-20

---

### CoreDNS Pods CrashLooping

**Cause:** CoreDNS configuration errors, resource exhaustion, or loop detection in DNS forwarding.

```bash
# Symptom — DNS resolution fails cluster-wide
kubectl exec debug-pod -- nslookup kubernetes.default
# ;; connection timed out; no servers could be reached

# Diagnosis
# 1. Check CoreDNS pod status
kubectl get pods -n kube-system -l k8s-app=kube-dns
# NAME                       READY   STATUS             RESTARTS
# coredns-5d78c9869d-abc12   0/1     CrashLoopBackOff   8

# 2. Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=20
# [FATAL] plugin/loop: Loop detected, stopping

# 3. Check CoreDNS ConfigMap
kubectl get configmap coredns -n kube-system -o yaml

# Fix for "loop detected":
# The node's /etc/resolv.conf points to 127.0.0.1 (systemd-resolved),
# causing CoreDNS to forward to itself in a loop.
# Edit the CoreDNS ConfigMap:
kubectl edit configmap coredns -n kube-system
# Change:
#   forward . /etc/resolv.conf
# To:
#   forward . 8.8.8.8 8.8.4.4    # Use external DNS directly

# Fix for resource exhaustion: scale up CoreDNS
kubectl scale deployment coredns -n kube-system --replicas=3

# Restart CoreDNS
kubectl rollout restart deployment coredns -n kube-system
```

---

### API Server High Latency

**Cause:** The API server is under heavy load from too many watchers, large list requests, or etcd slowness.

```bash
# Symptom — kubectl commands are slow (>5 seconds)
time kubectl get pods
# real    0m8.234s   ← should be <1s

# Diagnosis
# 1. Check API server metrics
kubectl get --raw='/metrics' | grep apiserver_request_duration_seconds

# 2. Check etcd latency (most common cause)
kubectl -n kube-system exec etcd-<node> -- etcdctl endpoint status \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key -w table

# 3. Check for expensive API calls
kubectl get --raw='/metrics' | grep 'apiserver_request_total' | sort -t'"' -k4 -rn | head -10

# 4. Check API Priority and Fairness (throttling)
kubectl get flowschemas
kubectl get prioritylevelconfigurations

# Fixes:
# - Move etcd to SSD storage (etcd is I/O bound)
# - Reduce watch connections (optimize controllers)
# - Use API Priority and Fairness to throttle noisy clients
# - Scale to multi-master setup (3+ API servers)
# - Use resource quotas to limit list requests per namespace
```

> **Cross-reference:** API Priority and Fairness → MODULE-33

---

### PersistentVolume Not Resizing

**Cause:** The StorageClass doesn't allow volume expansion, or the filesystem resize hasn't been triggered.

```bash
# Symptom — PVC edit accepted but capacity unchanged
kubectl get pvc my-pvc
# NAME     STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# my-pvc   Bound    pv-123   10Gi       RWO            gp2

# After editing to 20Gi:
kubectl get pvc my-pvc
# CAPACITY still shows 10Gi

# Diagnosis
# 1. Check if StorageClass allows expansion
kubectl get storageclass gp2 -o jsonpath='{.allowVolumeExpansion}'
# false   ← expansion not allowed!

# 2. Check PVC conditions
kubectl describe pvc my-pvc | grep -A5 "Conditions"
# Type                      Status
# FileSystemResizePending   True    ← waiting for pod restart

# Fix 1: Enable volume expansion on StorageClass
kubectl patch storageclass gp2 -p '{"allowVolumeExpansion": true}'

# Fix 2: Edit PVC to request more storage
kubectl edit pvc my-pvc
# Change spec.resources.requests.storage to 20Gi

# Fix 3: Restart the pod to trigger filesystem resize
kubectl delete pod <pod-using-pvc>
# The new pod triggers the filesystem resize on mount

# Verify
kubectl get pvc my-pvc
# CAPACITY   20Gi   ← resized
```

> **Cross-reference:** StorageClass and PVC → MODULE-17

---

**Next Module: Advanced Specialist Topics →**
