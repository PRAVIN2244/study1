# MODULE 22: RBAC — Role-Based Access Control

---

## 22.1 RBAC — Role-Based Access Control

RBAC controls who can do what in the cluster. It answers three questions:
1. **Who** — User, Group, or ServiceAccount (the subject)
2. **What** — Which actions (verbs: get, list, create, update, delete, watch, patch)
3. **Where** — Which resources in which namespace (or cluster-wide)

**Authentication vs Authorization — Two Different Things:**

| Concept | Question | Mechanisms |
|---|---|---|
| **Authentication (authn)** | "Who are you?" | Client certificates, bearer tokens, OIDC, AWS IAM |
| **Authorization (authz)** | "What can you do?" | RBAC (primary), ABAC, Webhook |

Certificates are used for **authentication** (proving identity via TLS client certs). **Authorization** is handled by RBAC policies (Roles + RoleBindings). Don't confuse the two — a valid certificate proves who you are, but RBAC determines what you're allowed to do.

### Authorization Mechanisms

Kubernetes supports multiple authorization modes. The API server evaluates them in the order specified by `--authorization-mode`:

| Mode | How It Works | Use Case |
|---|---|---|
| **Node** | Authorizes kubelet requests (users in `system:nodes` group with `system:node:` prefix) | Built-in; always used for kubelet-to-API communication |
| **RBAC** | Role/ClusterRole + RoleBinding/ClusterRoleBinding | Standard for all clusters (recommended) |
| **ABAC** | JSON policy file mapping users/groups to permissions | Legacy; requires API server restart on every change |
| **Webhook** | Sends authorization decisions to an external service (e.g., OPA) | When you need external policy engines |
| **AlwaysAllow** | Permits all requests without checks | Default if no mode is specified; never use in production |
| **AlwaysDeny** | Denies all requests | Testing only |

**Configuring authorization modes on the API server:**

```bash
# View current authorization mode
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep authorization-mode
# --authorization-mode=Node,RBAC

# Multiple modes are evaluated sequentially:
# --authorization-mode=Node,RBAC,Webhook
#
# 1. Node authorizer checks → if it's a kubelet request, approve/deny here
# 2. If Node denies (not a node request), pass to RBAC
# 3. If RBAC approves → access granted (skip Webhook)
# 4. If RBAC denies → pass to Webhook
# 5. If Webhook approves → access granted
# 6. If all deny → request is rejected
```

**Node Authorization:** Kubelets authenticate with certificates that have usernames like `system:node:worker-1` and belong to the `system:nodes` group. The node authorizer grants them access to read Services, Endpoints, Nodes, and Pods, and to write Node status and Pod status — the minimum needed for a kubelet to function.

**ABAC (Attribute-Based Access Control):** Permissions are defined in a JSON policy file passed to the API server. Each line maps a user or group to allowed resources:

```json
{"kind": "Policy", "spec": {"user": "dev-user", "namespace": "*", "resource": "pods", "apiGroup": "*"}}
{"kind": "Policy", "spec": {"user": "dev-user-2", "namespace": "*", "resource": "pods", "apiGroup": "*"}}
{"kind": "Policy", "spec": {"group": "dev-users", "namespace": "*", "resource": "pods", "apiGroup": "*"}}
{"kind": "Policy", "spec": {"user": "security-1", "namespace": "*", "resource": "csr", "apiGroup": "*"}}
```

ABAC is difficult to manage — every change requires editing the policy file and restarting the API server. RBAC replaced it as the standard approach.

**Webhook Authorization:** Delegates authorization decisions to an external service. The API server sends the user's request details to the webhook, which responds with allow or deny. [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) is a common choice for this.

**Configuring authorization mode (systemd service — non-kubeadm clusters):**

On clusters set up manually (not with kubeadm), the API server runs as a systemd service. The `--authorization-mode` flag is set in the ExecStart block:

```bash
# /etc/systemd/system/kube-apiserver.service
# Default (if not specified): AlwaysAllow — permits all requests
ExecStart=/usr/local/bin/kube-apiserver \
  --advertise-address=${INTERNAL_IP} \
  --allow-privileged=true \
  --authorization-mode=AlwaysAllow \
  --etcd-servers=https://127.0.0.1:2379 \
  --tls-cert-file=/var/lib/kubernetes/apiserver.crt \
  --tls-private-key-file=/var/lib/kubernetes/apiserver.key \
  --client-ca-file=/var/lib/kubernetes/ca.pem \
  --v=2
```

```bash
# Production configuration with multiple modes (evaluated sequentially):
ExecStart=/usr/local/bin/kube-apiserver \
  --advertise-address=${INTERNAL_IP} \
  --allow-privileged=true \
  --authorization-mode=Node,RBAC,Webhook \
  --etcd-servers=https://127.0.0.1:2379 \
  --tls-cert-file=/var/lib/kubernetes/apiserver.crt \
  --tls-private-key-file=/var/lib/kubernetes/apiserver.key \
  --client-ca-file=/var/lib/kubernetes/ca.pem \
  --v=2
```

### RBAC Deep Dive

**RBAC has four objects:**

| Object | Scope | Purpose |
|---|---|---|
| `Role` | Namespace | Defines permissions within a namespace |
| `RoleBinding` | Namespace | Grants a Role to a subject within a namespace |
| `ClusterRole` | Cluster | Defines permissions cluster-wide |
| `ClusterRoleBinding` | Cluster | Grants a ClusterRole to a subject cluster-wide |

**Key concepts:**
- Kubernetes has no "User" object — users are authenticated externally (certificates, OIDC, AWS IAM)
- ServiceAccounts are Kubernetes-native identities for pods
- RBAC is additive — there are no "deny" rules. If no rule grants access, access is denied by default.
- A ClusterRole can be bound with a RoleBinding to grant cluster-level permissions within a single namespace

**Interview question: What's the difference between Role and ClusterRole?**
- Role is namespace-scoped — permissions only apply within one namespace
- ClusterRole is cluster-scoped — permissions apply across all namespaces, and can also cover cluster-level resources (nodes, namespaces, PVs)

```
┌──────────────────────────────────────────────────────┐
│  RBAC Components                                      │
│                                                      │
│  WHO?                    WHAT?                        │
│  ─────                   ─────                        │
│  User/Group/SA  ──bind── Role/ClusterRole             │
│                                                      │
│  Namespace-scoped:                                    │
│    ServiceAccount + Role + RoleBinding                │
│                                                      │
│  Cluster-scoped:                                      │
│    User/Group + ClusterRole + ClusterRoleBinding      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Role & RoleBinding (Namespace-scoped)

```yaml
# role.yaml — What actions are allowed
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: development
  name: pod-reader
rules:
- apiGroups: [""]              # "" = core API group (pods, services, etc.)
  resources: ["pods"]
  verbs: ["get", "watch", "list"]

- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

- apiGroups: ["apps"]          # apps API group (deployments, replicasets)
  resources: ["deployments"]
  verbs: ["get", "list"]
```

```yaml
# rolebinding.yaml — Who gets the role
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: development
subjects:
- kind: User
  name: developer@company.com
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: ci-pipeline
  namespace: development
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f role.yaml
kubectl apply -f rolebinding.yaml

# Verify permissions
kubectl auth can-i get pods --namespace=development --as=developer@company.com

# Output:
# yes

kubectl auth can-i delete pods --namespace=development --as=developer@company.com

# Output:
# no

kubectl auth can-i get pods --namespace=production --as=developer@company.com

# Output:
# no (role only applies to development namespace)
```

**Inspecting Roles and RoleBindings:**

```bash
# List roles in the current namespace
kubectl get roles
# NAME         CREATED AT
# pod-reader   2024-01-15T10:00:00Z
# developer    2024-01-15T10:00:05Z

# List role bindings
kubectl get rolebindings
# NAME                        ROLE              AGE
# devuser-developer-binding   Role/developer    24s

# Detailed view of a role — shows resources and verbs
kubectl describe role developer
# Name:         developer
# PolicyRule:
#   Resources   Non-Resource URLs   Resource Names   Verbs
#   ---------   -----------------   --------------   -----
#   pods        []                  []               [list get create update delete]
#   ConfigMap   []                  []               [create]

# Detailed view of a role binding — shows subjects
kubectl describe rolebinding devuser-developer-binding
# Name:         devuser-developer-binding
# Role:
#   Kind:  Role
#   Name:  developer
# Subjects:
#   Kind   Name       Namespace
#   ----   ----       ---------
#   User   dev-user
```

**Restricting access to specific resource instances with `resourceNames`:**

By default, a Role grants access to all instances of a resource. Use `resourceNames` to limit access to specific named resources:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: limited-pod-access
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "update"]
  resourceNames: ["blue", "orange"]    # Only these two pods
```

With this role, the user can `get` and `update` pods named "blue" and "orange", but cannot access any other pods in the namespace.

### Lab: Roles & RoleBindings

This lab walks through inspecting authorization modes, creating roles for a user, adjusting permissions across namespaces, and adding API group permissions.

**Step 1: Verify authorization modes**

```bash
# From the API server manifest
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep authorization-mode
#   --authorization-mode=Node,RBAC

# Or from running processes
ps aux | grep authorization
# kube-apiserver --authorization-mode=Node,RBAC ...
```

**Step 2: Count and inspect existing roles**

```bash
kubectl get roles -A --no-headers | wc -l
# 12

kubectl get roles -A --no-headers
# NAMESPACE     NAME
# blue          developer
# kube-system   kube-proxy
# kube-system   kubeadm:kubelet-config-1.23
# ...
```

Inspect the `kube-proxy` role — it only allows `get` on a specific ConfigMap:

```bash
kubectl describe role kube-proxy -n kube-system
```

```
Name:         kube-proxy
PolicyRule:
  Resources   Non-Resource URLs  Resource Names  Verbs
  ---------   -----------------  --------------  -----
  configmaps  []                 [kube-proxy]    [get]
```

This uses `resourceNames` to restrict access to only the ConfigMap named `kube-proxy`.

**Step 3: Test a user's permissions**

```bash
kubectl get pods --as dev-user
# Error from server (Forbidden): pods is forbidden:
#   User "dev-user" cannot list resource "pods" in API group "" in the namespace "default"
```

**Step 4: Create a role and binding for dev-user**

```bash
kubectl create role developer --verb=list,create,delete --resource=pods
# role.rbac.authorization.k8s.io/developer created

kubectl describe role developer
```

```
Name:         developer
PolicyRule:
  Resources  Non-Resource URLs  Resource Names  Verbs
  ---------  -----------------  --------------  -----
  pods       []                 []              [list create delete]
```

```bash
kubectl create rolebinding dev-user-binding --role=developer --user=dev-user
# rolebinding.rbac.authorization.k8s.io/dev-user-binding created

kubectl describe rolebinding dev-user-binding
```

```
Name:         dev-user-binding
Role:
  Kind:  Role
  Name:  developer
Subjects:
  Kind  Name      Namespace
  ----  ----      ---------
  User  dev-user
```

```bash
# Now dev-user can list pods
kubectl get pods --as dev-user
# NAME        READY   STATUS    RESTARTS   AGE
# nginx-pod   1/1     Running   0          5m
```

**Step 5: Fix permissions in another namespace**

The `blue` namespace has a `developer` role with `resourceNames` restricting access to `blue-app`, but dev-user needs access to `dark-blue-app`:

```bash
kubectl describe role developer -n blue
```

```
Name:         developer
PolicyRule:
  Resources  Non-Resource URLs  Resource Names  Verbs
  ---------  -----------------  --------------  -----
  pods       []                 [blue-app]      [get watch create delete]
```

```bash
# dev-user can't access dark-blue-app
kubectl get pod dark-blue-app -n blue --as dev-user
# Error from server (Forbidden)

# Edit the role to add dark-blue-app to resourceNames
kubectl edit role developer -n blue
```

Update `resourceNames` to include both pods:

```yaml
rules:
- apiGroups: [""]
  resources: ["pods"]
  resourceNames: ["blue-app", "dark-blue-app"]
  verbs: ["get", "watch", "create", "delete"]
```

```bash
kubectl get pod dark-blue-app -n blue --as dev-user
# NAME            READY   STATUS    RESTARTS   AGE
# dark-blue-app   1/1     Running   0          25m
```

**Step 6: Add deployment permissions (different API group)**

```bash
kubectl create deployment nginx --image=nginx -n blue --as dev-user
# error: deployments.apps is forbidden: User "dev-user" cannot create
#   resource "deployments" in API group "apps" in the namespace "blue"
```

Edit the role to add a second rule for the `apps` API group:

```bash
kubectl edit role developer -n blue
```

```yaml
rules:
- apiGroups: [""]
  resources: ["pods"]
  resourceNames: ["blue-app", "dark-blue-app"]
  verbs: ["get", "watch", "create", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "watch", "create", "delete"]
```

```bash
kubectl describe role developer -n blue
```

```
Name:         developer
PolicyRule:
  Resources          Non-Resource URLs  Resource Names             Verbs
  ---------          -----------------  --------------             -----
  pods               []                 [blue-app dark-blue-app]   [get watch create delete]
  deployments.apps   []                 []                         [get watch create delete]
```

```bash
kubectl create deployment nginx --image=nginx -n blue --as dev-user
# deployment.apps/nginx created
```

### ClusterRole & ClusterRoleBinding (Cluster-wide)

**Namespaced vs cluster-scoped resources:**

Most resources (pods, deployments, services, secrets, configmaps) are namespaced — they exist within a namespace. Some resources (nodes, persistent volumes, namespaces themselves, cluster roles) are cluster-scoped — they don't belong to any namespace.

```bash
# List namespaced resources
kubectl api-resources --namespaced=true
# NAME          SHORTNAMES   APIVERSION   NAMESPACED   KIND
# pods          po           v1           true         Pod
# services      svc          v1           true         Service
# deployments   deploy       apps/v1      true         Deployment
# secrets                    v1           true         Secret
# ...

# List cluster-scoped resources
kubectl api-resources --namespaced=false
# NAME                  SHORTNAMES   APIVERSION                        NAMESPACED   KIND
# nodes                 no           v1                                false        Node
# namespaces            ns           v1                                false        Namespace
# persistentvolumes     pv           v1                                false        PersistentVolume
# clusterroles                       rbac.authorization.k8s.io/v1      false        ClusterRole
# clusterrolebindings                rbac.authorization.k8s.io/v1      false        ClusterRoleBinding
# ...
```

A namespace-scoped `Role` cannot grant access to cluster-scoped resources like nodes or PVs. You need a `ClusterRole` for that.

**Example: Cluster administrator role (nodes):**

```yaml
# cluster-admin-role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-administrator
rules:
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["list", "get", "create", "delete"]
```

```yaml
# cluster-admin-binding.yaml — bind to a specific user
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-role-binding
subjects:
- kind: User
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-administrator
  apiGroup: rbac.authorization.k8s.io
```

**Example: Storage administrator role (PVs and PVCs):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: storage-administrator
rules:
- apiGroups: [""]
  resources: ["persistentvolumes"]
  verbs: ["list", "get", "create", "delete", "watch"]
- apiGroups: [""]
  resources: ["persistentvolumeclaims"]
  verbs: ["list", "get", "create", "delete", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses"]
  verbs: ["list", "get", "create", "delete", "watch"]
```

**Example: Read-only viewer (cluster-wide):**

```yaml
# clusterrole.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-viewer
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces", "pods", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
```

```yaml
# clusterrolebinding.yaml — bind to a group
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-viewer-binding
subjects:
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-viewer
  apiGroup: rbac.authorization.k8s.io
```

⚠️ A ClusterRole bound with a ClusterRoleBinding grants access across **all namespaces**. If you bind a ClusterRole that allows pod access, the user can see pods in every namespace — unlike a namespace-scoped Role.

**Default ClusterRoles:** Kubernetes creates several ClusterRoles at cluster initialization:

```bash
kubectl get clusterroles | head -10
# NAME                                                   CREATED AT
# cluster-admin                                          2024-01-01T00:00:00Z
# admin                                                  2024-01-01T00:00:00Z
# edit                                                   2024-01-01T00:00:00Z
# view                                                   2024-01-01T00:00:00Z
# system:node                                            2024-01-01T00:00:00Z
# ...
```

| Default ClusterRole | Permissions |
|---|---|
| `cluster-admin` | Full access to all resources (superuser) |
| `admin` | Full access within a namespace (when bound with RoleBinding) |
| `edit` | Read/write to most resources in a namespace, no RBAC changes |
| `view` | Read-only access to most resources in a namespace |

### Lab: ClusterRoles & ClusterRoleBindings

This lab walks through inspecting existing cluster roles, then incrementally granting a user access to cluster-scoped resources.

**Step 1: Count existing cluster roles and bindings**

```bash
kubectl get clusterroles --no-headers | wc -l
# Output: 69

kubectl get clusterrolebindings --no-headers | wc -l
# Output: 54
```

**Step 2: Inspect the built-in `cluster-admin` role**

```bash
kubectl describe clusterrolebinding cluster-admin
```

```
Name:         cluster-admin
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:    ClusterRole
  Name:    cluster-admin
Subjects:
  Kind    Name              Namespace
  ----    ----              ---------
  Group   system:masters
```

The `cluster-admin` role is bound to the `system:masters` group — any user in this group has full cluster access.

```bash
kubectl describe clusterrole cluster-admin
```

```
Name:         cluster-admin
Labels:       kubernetes.io/bootstrapping=rbac-defaults
PolicyRule:
  Resources  Non-Resource URLs  Resource Names  Verbs
  ---------  -----------------  --------------  -----
  *.*        []                 []              [*]
  *          [*]                []              [*]
```

The wildcard `*.*` with verb `[*]` means this role can perform any action on any resource — it's the superuser role.

**Step 3: Grant a user node access**

Create a ClusterRole with read-only access to nodes, then bind it to a user:

```bash
kubectl create clusterrole michelle-role --verb=get,list,watch --resource=nodes
# clusterrole.rbac.authorization.k8s.io/michelle-role created

kubectl create clusterrolebinding michelle-role-binding \
  --clusterrole=michelle-role --user=michelle
# clusterrolebinding.rbac.authorization.k8s.io/michelle-role-binding created

# Verify the binding
kubectl describe clusterrolebinding michelle-role-binding
```

```
Name:         michelle-role-binding
Role:
  Kind:    ClusterRole
  Name:    michelle-role
Subjects:
  Kind    Name       Namespace
  ----    ----       ---------
  User    michelle
```

```bash
# Test access using --as impersonation
kubectl get nodes --as michelle
# Output: lists nodes successfully

kubectl auth can-i list nodes --as michelle
# yes

kubectl auth can-i create deployments --as michelle
# no
```

**Step 4: Extend permissions to storage resources**

As responsibilities grow, add a new ClusterRole for persistent volumes and storage classes:

```bash
# Check which API group storageclasses belong to
kubectl api-resources | grep -E "persistentvolume|storageclass"
# persistentvolumes       pv     v1                         false   PersistentVolume
# storageclasses          sc     storage.k8s.io/v1          false   StorageClass
# persistentvolumeclaims  pvc    v1                         true    PersistentVolumeClaim

kubectl create clusterrole storage-admin \
  --resource=persistentvolumes,storageclasses --verb=list,create,get,watch
# clusterrole.rbac.authorization.k8s.io/storage-admin created

kubectl describe clusterrole storage-admin
```

```
Name:         storage-admin
PolicyRule:
  Resources                      Non-Resource URLs  Resource Names  Verbs
  ---------                      -----------------  --------------  -----
  persistentvolumes              []                 []              [list create get watch]
  storageclasses.storage.k8s.io  []                 []              [list create get watch]
```

```bash
kubectl create clusterrolebinding michelle-storage-admin \
  --user=michelle --clusterrole=storage-admin
# clusterrolebinding.rbac.authorization.k8s.io/michelle-storage-admin created

# Verify
kubectl auth can-i list persistentvolumes --as michelle
# yes

kubectl auth can-i list storageclasses --as michelle
# yes
```

### RBAC Imperative Commands (Quick Setup)

```bash
# Create a Role using kubectl (instead of YAML)
kubectl create role pod-reader \
  --verb=get,list,watch \
  --resource=pods \
  -n dev

# Output:
# role.rbac.authorization.k8s.io/pod-reader created

# Create a RoleBinding to grant the role to a service account
kubectl create rolebinding read-pods \
  --role=pod-reader \
  --serviceaccount=dev:sa1 \
  -n dev

# Output:
# rolebinding.rbac.authorization.k8s.io/read-pods created

# Create a ClusterRole (cluster-wide)
kubectl create clusterrole node-viewer \
  --verb=get,list,watch \
  --resource=nodes

# Bind it to a user
kubectl create clusterrolebinding admin-node-viewer \
  --clusterrole=node-viewer \
  --user=admin

# Verify permissions
kubectl auth can-i list pods -n dev --as=system:serviceaccount:dev:sa1
# Output: yes

kubectl auth can-i delete pods -n dev --as=system:serviceaccount:dev:sa1
# Output: no
```

### Service Accounts

```bash
# Create a service account
kubectl create serviceaccount ci-deployer -n production

# Output:
# serviceaccount/ci-deployer created

# Create a role for CI/CD deployments
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: deployer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["services"]
  verbs: ["get", "list"]
EOF

# Bind the role to the service account
kubectl create rolebinding ci-deployer-binding \
  --role=deployer \
  --serviceaccount=production:ci-deployer \
  -n production

# Test permissions
kubectl auth can-i update deployments -n production --as=system:serviceaccount:production:ci-deployer

# Output:
# yes

kubectl auth can-i delete deployments -n production --as=system:serviceaccount:production:ci-deployer

# Output:
# no
```

### RBAC Debugging CLI Reference

| Command | What It Does |
|---------|-------------|
| `kubectl auth can-i <verb> <resource> -n <ns>` | Check if current user can perform an action |
| `kubectl auth can-i <verb> <resource> --as=<user>` | Simulate permissions for another user/SA |
| `kubectl auth can-i --list -n <ns>` | List all permissions in a namespace |
| `kubectl get roles -n <ns>` | List namespace-scoped roles |
| `kubectl get clusterroles` | List cluster-wide roles |
| `kubectl get rolebindings -n <ns>` | List who is bound to which role in a namespace |
| `kubectl get clusterrolebindings` | List cluster-wide bindings |
| `kubectl describe rolebinding <name> -n <ns>` | Show subjects and role details |
| `kubectl auth reconcile -f rbac.yaml --dry-run=client` | Validate RBAC changes before applying |

**Example — debugging a "Forbidden" error:**

```bash
# 1. Identify the service account the pod uses
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.serviceAccountName}'
# deploy-bot

# 2. Check what it can do
kubectl auth can-i --list -n <ns> --as=system:serviceaccount:<ns>:deploy-bot
# Resources   Verbs
# pods        [get list]
# deployments []          ← no permissions on deployments!

# 3. Check existing bindings
kubectl get rolebindings -n <ns> -o wide
# NAME         ROLE              SUBJECTS
# read-pods    Role/pod-reader   ServiceAccount:deploy-bot

# 4. Fix: create a role and binding for deployments
kubectl create role deploy-manager --verb=get,list,create,update \
  --resource=deployments -n <ns>
kubectl create rolebinding deploy-access --role=deploy-manager \
  --serviceaccount=<ns>:deploy-bot -n <ns>

# 5. Verify
kubectl auth can-i create deployments -n <ns> --as=system:serviceaccount:<ns>:deploy-bot
# yes
```

### Common RBAC Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Pods use the `default` ServiceAccount | Default SA may have no permissions or too many | Always create a dedicated SA for each workload |
| Using ClusterRole when Role is sufficient | Grants permissions across all namespaces | Start with namespace-scoped Role; only use ClusterRole when truly needed |
| No namespace set in RoleBinding metadata | RBAC fails silently — binding applies to wrong namespace | Always verify `metadata.namespace` matches the target namespace |
| Forgetting to set `serviceAccountName` in pod spec | Pod uses `default` SA and won't have the intended permissions | Explicitly set `serviceAccountName` in the Deployment/Pod spec |
| Granting `*` verbs or `*` resources | Violates least privilege — equivalent to admin access | List only the specific verbs and resources needed |
| Not testing with `kubectl auth can-i` | Permissions issues discovered only at runtime | Always test with `--as=` flag before deploying |

### RBAC Auditing Tools

| Tool | What It Does | Install |
|------|-------------|---------|
| **rakkess** | Shows access matrix — who can do what in a namespace | `kubectl krew install access-matrix` |
| **who-can** | Reverse lookup — who can perform a specific action | `kubectl krew install who-can` |
| **kubectl auth can-i** | Built-in — check if a user/SA can perform an action | Built into kubectl |

```bash
# rakkess — show all permissions for current user in a namespace
kubectl access-matrix -n production
# NAME          GET  LIST  CREATE  UPDATE  DELETE
# pods          ✔    ✔     ✔       ✔       ✔
# deployments   ✔    ✔     ✔       ✔       ✖
# secrets       ✖    ✖     ✖       ✖       ✖

# who-can — find all subjects that can delete pods
kubectl who-can delete pods -n production
# ROLEBINDING    NAMESPACE    SUBJECT             TYPE
# admin-binding  production   admin-user          User
# ci-binding     production   ci-deployer         ServiceAccount
```

---

