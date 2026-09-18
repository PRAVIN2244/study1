# MODULE 24: Service Accounts, API Groups & EKS IAM

---

## 24.1 Service Accounts — Deep Dive


**User Accounts vs Service Accounts:**

| | User Account | Service Account |
|---|---|---|
| **Used by** | Humans (admins, developers) | Machines (pods, applications) |
| **Scope** | Cluster-wide (not namespaced) | Namespaced |
| **Creation** | External (certificates, OIDC, etc.) | `kubectl create serviceaccount` |
| **Managed by** | Cluster admin | Kubernetes API |
| **Example** | Admin deploying apps | Prometheus querying the API |

**Every namespace gets a `default` service account automatically.** When you create a pod without specifying a service account, Kubernetes assigns the `default` service account and mounts its token into the pod.

```bash
kubectl get sa -n default
# Output:
# NAME      SECRETS   AGE
# default   0         30d

# Every new namespace also gets one
kubectl create ns test-ns
kubectl get sa -n test-ns
# Output:
# NAME      SECRETS   AGE
# default   0         5s
```

**Creating and using service accounts:**

```bash
# Create a service account
kubectl create sa demosa
kubectl get sa
# Output:
# NAME      SECRETS   AGE
# default   0         30d
# demosa    0         5s

# Pod with default service account
kubectl get pod testpod -o yaml | grep serviceAccount:
# Output: serviceAccount: default
```

```yaml
# Pod using a custom service account
apiVersion: v1
kind: Pod
metadata:
  name: testpodsa
spec:
  serviceAccountName: demosa    # Use serviceAccountName (not serviceAccount — deprecated)
  containers:
  - name: myapp
    image: ubuntu
    command: ["/bin/bash", "-c", "while true; do echo Hello; sleep 8; done"]
```

#### Token Evolution (v1.22 → v1.24)

Service account token handling changed significantly across Kubernetes versions:

**Before v1.22:** Creating a service account auto-created a Secret with a **non-expiring** token. This token was mounted into every pod using that service account.

```yaml
# Old behavior — auto-created secret (no longer happens in v1.24+)
apiVersion: v1
kind: Secret
metadata:
  name: demosa-token-abc12
  annotations:
    kubernetes.io/service-account.name: demosa
type: kubernetes.io/service-account-token
data:
  token: <base64-encoded-JWT>
  ca.crt: <base64-encoded-CA>
  namespace: ZGVmYXVsdA==
```

**v1.22+:** Introduced the **TokenRequest API**. Pods now receive **time-bound, audience-bound projected tokens** instead of the old non-expiring secrets. The token is mounted as a projected volume at `/var/run/secrets/kubernetes.io/serviceaccount/token`.

**v1.24+:** Auto-creation of Secret-based tokens was **removed entirely**. You must use the TokenRequest API or explicitly create a Secret if you need a long-lived token (not recommended).

```bash
# Generate a short-lived token via the TokenRequest API (v1.22+)
kubectl create token demosa
# Output:
# eyJhbGciOiJSUzI1NiIsImtpZCI6Ik...  (JWT, expires in 1 hour by default)

# Generate a token with custom expiration
kubectl create token demosa --duration=48h

# If you absolutely need a non-expiring token (avoid if possible):
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: demosa-manual-token
  annotations:
    kubernetes.io/service-account.name: demosa
type: kubernetes.io/service-account-token
EOF

kubectl describe secret demosa-manual-token
# The controller populates the token, ca.crt, and namespace fields
```

#### Disabling Token Auto-Mounting

For pods that don't need API access, disable the automatic token mount to reduce attack surface:

```yaml
# Disable at the service account level (affects all pods using this SA)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: build-sa
automountServiceAccountToken: false
```

```yaml
# Disable at the pod level (overrides the service account setting)
apiVersion: v1
kind: Pod
metadata:
  name: no-api-pod
spec:
  serviceAccountName: build-sa
  automountServiceAccountToken: false    # Pod-level takes precedence
  containers:
  - name: app
    image: nginx
```

```bash
# Verify — no token mounted
kubectl exec no-api-pod -- ls /var/run/secrets/kubernetes.io/serviceaccount/
# Output: ls: /var/run/secrets/kubernetes.io/serviceaccount/: No such file or directory
```

#### Service Account API Access in Practice

```bash
# Test API access from inside the pod
kubectl exec -it testpodsa -- /bin/bash
  apt update && apt install -y curl
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)

  # Without a role binding, this returns 403 Forbidden
  curl https://kubernetes/api/v1/namespaces/default/pods -k \
    --header "Authorization: Bearer $TOKEN"
```

```yaml
# Bind a role to the service account
# reader-role-binding-sa.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-access-sa
  namespace: default
subjects:
- kind: ServiceAccount
  name: demosa
roleRef:
  kind: Role
  name: reader-role       # Use the reader role created earlier
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f reader-role-binding-sa.yaml

# Now the API call succeeds for the default namespace
kubectl exec -it testpodsa -- /bin/bash
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  curl https://kubernetes/api/v1/namespaces/default/pods -k \
    --header "Authorization: Bearer $TOKEN"
  # Returns pod list

  # Cross-namespace access still denied (role is namespace-scoped)
  curl https://kubernetes/api/v1/namespaces/kube-system/pods -k \
    --header "Authorization: Bearer $TOKEN"
  # Returns 403 Forbidden
```

#### Lab: Service Accounts for a Dashboard Application

This lab walks through diagnosing a dashboard app that fails because the default SA lacks permissions, then creating a dedicated SA with RBAC access.

**Step 1: List service accounts and inspect the default SA**

```bash
kubectl get sa
# NAME      SECRETS   AGE
# default   0         20m
# dev       0         35s

kubectl describe sa default
# Name:                default
# Namespace:           default
# Labels:              <none>
# Annotations:         <none>
# Image pull secrets:  <none>
# Mountable secrets:   <none>
# Tokens:              <none>      ← No token secret (v1.24+ behavior)
```

**Step 2: Inspect the dashboard deployment**

```bash
kubectl get deploy
# NAME            READY   UP-TO-DATE   AVAILABLE   AGE
# web-dashboard   1/1     1            1           20s

kubectl describe deploy web-dashboard | grep -A2 "Service Account"
#   Service Account:  default
```

The dashboard uses the `default` service account. Checking the pod logs or events reveals:

```
pods is forbidden: User "system:serviceaccount:default:default"
  cannot list resource "pods" in API group "" in the namespace "default"
```

The `system:serviceaccount:default:default` identity means: service account named `default` in namespace `default`. It has no RBAC permissions.

**Step 3: Verify the token mount on the pod**

```bash
kubectl describe pod $(kubectl get pod -l app=web-dashboard -o name | head -1)
```

```
Mounts:
  /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-swjvh (ro)
```

The token is auto-mounted at `/var/run/secrets/kubernetes.io/serviceaccount/` — the app reads it to authenticate with the API server.

**Step 4: Create a new service account with RBAC permissions**

```bash
kubectl create serviceaccount dashboard-sa
# serviceaccount/dashboard-sa created
```

Create a Role and RoleBinding to grant pod-read access:

```yaml
# pod-reader-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
```

```yaml
# dashboard-sa-role-binding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dashboard-sa-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: dashboard-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f pod-reader-role.yaml
kubectl apply -f dashboard-sa-role-binding.yaml

# Verify permissions
kubectl auth can-i list pods --as=system:serviceaccount:default:dashboard-sa
# yes
```

**Step 5: Generate a token for manual testing**

```bash
kubectl create token dashboard-sa
# eyJhbGciOiJSUzI1NiIsImtpZCI6Ik...
```

Copy this token into the dashboard UI to verify it can now list pods.

**Step 6: Update the deployment to use the new SA**

Instead of manually entering tokens, update the deployment so the pod automatically mounts the `dashboard-sa` token:

```bash
kubectl get deploy web-dashboard -o yaml > dashboard.yaml
```

Edit `dashboard.yaml` — add `serviceAccountName` under `spec.template.spec`:

```yaml
spec:
  template:
    spec:
      serviceAccountName: dashboard-sa    # Add this line
      containers:
      - name: web-dashboard
        image: gcr.io/kodekloud/customimage/my-kubernetes-dashboard
```

```bash
kubectl apply -f dashboard.yaml
# deployment.apps/web-dashboard configured

# Verify the new pod uses dashboard-sa
kubectl describe pod $(kubectl get pod -l app=web-dashboard -o name | head -1) | grep "Service Account"
#   Service Account:  dashboard-sa

# The dashboard can now list pods without manual token entry
```

---

## 24.2 API Groups & API Access


Kubernetes organizes its API into two categories:

| Category | Path | Resources |
|---|---|---|
| **Core API** | `/api/v1` | pods, services, configmaps, secrets, namespaces, nodes, PVs, PVCs, events, endpoints |
| **Named API groups** | `/apis/<group>/<version>` | deployments (`apps`), replicasets (`apps`), statefulsets (`apps`), networkpolicies (`networking.k8s.io`), ingresses (`networking.k8s.io`), roles (`rbac.authorization.k8s.io`) |

Each resource supports verbs: `get`, `list`, `create`, `update`, `patch`, `delete`, `watch`. These verbs map directly to RBAC role rules.

```bash
# Explore available API groups
kubectl api-versions
# Output (partial):
# v1
# apps/v1
# batch/v1
# networking.k8s.io/v1
# rbac.authorization.k8s.io/v1
# storage.k8s.io/v1

# Find which API group a resource belongs to
kubectl api-resources | grep -i deployment
# NAME          SHORTNAMES   APIVERSION   NAMESPACED   KIND
# deployments   deploy       apps/v1      true         Deployment

# The apiGroup for RBAC rules comes from the APIVERSION column:
# "apps/v1" → apiGroups: ["apps"]
# "v1" (no prefix) → apiGroups: [""]  (core group)
```

### kubectl proxy — Accessing the API Without Certificates

`kubectl proxy` starts a local HTTP proxy that forwards requests to the API server using your kubeconfig credentials. This lets you explore the API with `curl` without passing certificates:

```bash
# Start the proxy (runs in foreground)
kubectl proxy
# Starting to serve on 127.0.0.1:8001

# In another terminal — access the API without certificates
curl http://localhost:8001/api/v1/namespaces
curl http://localhost:8001/apis/apps/v1/deployments
curl http://localhost:8001/version
# {"major": "1", "minor": "28", "gitVersion": "v1.28.0", ...}
```

⚠️ **`kubectl proxy` vs `kube-proxy`** — these are completely different:

| | `kubectl proxy` | `kube-proxy` |
|---|---|---|
| **Purpose** | HTTP proxy for API server access | Network proxy for Service routing |
| **Runs on** | Your workstation | Every cluster node |
| **Uses** | Kubeconfig credentials | iptables/IPVS rules |
| **Port** | 8001 (default) | N/A (kernel-level) |

---

## 24.3 EKS IAM Integration with RBAC


```bash
# Map IAM users/roles to Kubernetes RBAC
kubectl edit configmap aws-auth -n kube-system
```

```yaml
# aws-auth ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123456789012:role/EKSNodeRole
      username: system:node:{{EC2PrivateDNSName}}
      groups:
        - system:bootstrappers
        - system:nodes
    - rolearn: arn:aws:iam::123456789012:role/AdminRole
      username: admin
      groups:
        - system:masters
    - rolearn: arn:aws:iam::123456789012:role/DeveloperRole
      username: developer
      groups:
        - developers

  mapUsers: |
    - userarn: arn:aws:iam::123456789012:user/john
      username: john
      groups:
        - developers
    - userarn: arn:aws:iam::123456789012:user/jane
      username: jane
      groups:
        - system:masters
```

### Industry Example: Multi-Team RBAC

```yaml
# Team structure:
# - Platform team: Full cluster access
# - Backend team: Full access to backend namespace
# - Frontend team: Full access to frontend namespace
# - QA team: Read-only access to staging namespace
# - CI/CD: Deploy access to all namespaces

# Backend team role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: backend
  name: backend-admin
rules:
- apiGroups: ["", "apps", "batch", "networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-team-binding
  namespace: backend
subjects:
- kind: Group
  name: backend-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: backend-admin
  apiGroup: rbac.authorization.k8s.io
```

---

## 24.4 Common Errors & Troubleshooting

### Error: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"
```bash
# Cause: No nodes match the scheduling constraints
# Fix: Check node labels
kubectl get nodes --show-labels
# Adjust nodeSelector/affinity or label nodes appropriately
```

### Error: "forbidden: exceeded quota"
```bash
# Cause: ResourceQuota limit reached
kubectl describe resourcequota -n <namespace>
# Fix: Increase quota or reduce resource usage
```

### Error: "is forbidden: User cannot create resource"
```bash
# Cause: RBAC permission denied
kubectl auth can-i <verb> <resource> --as=<user> -n <namespace>
# Fix: Create/update Role and RoleBinding
```

### Scenario: Admin Access but Cannot See Worker Nodes

**Symptom:** A user has admin-level access to namespaces (can create/delete pods, deployments) but `kubectl get nodes` returns "Forbidden."

```bash
kubectl get nodes

# Output:
# Error from server (Forbidden): nodes is forbidden: User "dev-admin"
# cannot list resource "nodes" in API group "" at the cluster scope
```

**Root cause:** The user has a `Role` + `RoleBinding` (namespace-scoped), not a `ClusterRole` + `ClusterRoleBinding`. Nodes are cluster-scoped resources — they don't belong to any namespace.

```bash
# Step 1: Check what the user CAN do
kubectl auth can-i list pods --as=dev-admin -n default
# Output: yes

kubectl auth can-i list nodes --as=dev-admin
# Output: no    ← Cluster-scoped resource, no ClusterRole

# Step 2: Check existing bindings
kubectl get rolebindings -A | grep dev-admin
# Output:
# default   dev-admin-binding   Role/dev-admin-role   5d

kubectl get clusterrolebindings | grep dev-admin
# Output: (empty) ← No ClusterRoleBinding!

# Step 3: Fix — Grant cluster-level node read access
kubectl create clusterrole node-viewer \
  --verb=get,list,watch \
  --resource=nodes

kubectl create clusterrolebinding dev-admin-nodes \
  --clusterrole=node-viewer \
  --user=dev-admin

# Step 4: Verify
kubectl auth can-i list nodes --as=dev-admin
# Output: yes

kubectl get nodes --as=dev-admin
# Output:
# NAME                          STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal    Ready    <none>   30d   v1.29.1
```

**Cluster-scoped vs namespace-scoped resources:**

| Cluster-Scoped (need ClusterRole) | Namespace-Scoped (Role is enough) |
|---|---|
| Nodes | Pods |
| PersistentVolumes | Deployments |
| Namespaces | Services |
| ClusterRoles | ConfigMaps |
| StorageClasses | Secrets |
| IngressClasses | PVCs |

**Interview question: A user has admin access but can't see worker nodes. Why?**
Nodes are cluster-scoped resources. A namespace-scoped `Role` + `RoleBinding` only grants access within a namespace. To access nodes, the user needs a `ClusterRole` with `get,list,watch` on `nodes` and a `ClusterRoleBinding`. This is a common RBAC misconfiguration — always check whether the resource is cluster-scoped or namespace-scoped.

---

## 24.5 Module 6 Exercises

### Exercise 1: Scheduling
```bash
# 1. Label a node with tier=frontend
kubectl label nodes <node-name> tier=frontend
# 2. Create a pod with nodeSelector: tier=frontend
# 3. Verify it lands on the correct node
kubectl get pod -o wide
# 4. Taint the node and see what happens to new pods
kubectl taint nodes <node-name> dedicated=frontend:NoSchedule
```

### Exercise 2: HPA
```bash
# 1. Create a deployment with resource requests
kubectl create deployment stress --image=progrium/stress --replicas=1 -- --cpu 1 --timeout 600
# 2. Create an HPA
kubectl autoscale deployment stress --min=1 --max=5 --cpu-percent=50
# 3. Watch scaling
kubectl get hpa -w
```

### Exercise 3: RBAC
```bash
# 1. Create a service account
kubectl create serviceaccount viewer-sa
# 2. Create a role with read-only access
# 3. Bind the role
# 4. Test with: kubectl auth can-i list pods --as=system:serviceaccount:default:viewer-sa
```

---

**Next Module: Helm, CI/CD & Monitoring →**
