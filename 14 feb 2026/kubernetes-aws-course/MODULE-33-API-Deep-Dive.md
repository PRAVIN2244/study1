# MODULE 33: Kubernetes API Management — Deep Dive

---

## 33.1 Kubernetes API Management — Deep Dive

The API Server is the central management point for the entire cluster. Every `kubectl` command, every controller, every kubelet communicates through it. Managing API access is fundamental to cluster security and stability.

### API Groups

The Kubernetes API is organized into groups. Every endpoint on the API server belongs to a group:

```bash
# Query the cluster version via the API
curl https://kube-master:6443/version -k

# Output:
# {
#   "major": "1",
#   "minor": "29",
#   "gitVersion": "v1.29.0",
#   "buildDate": "2023-12-13T08:51:44Z",
#   "goVersion": "go1.21.5",
#   "platform": "linux/amd64"
# }
```

**Top-level API paths:**

```bash
curl https://kube-master:6443 -k --cert admin.crt --key admin.key --cacert ca.crt

# Output:
# {
#   "paths": [
#     "/api",          ← Core API group
#     "/api/v1",
#     "/apis",         ← Named API groups
#     "/apis/",
#     "/healthz",      ← Health check
#     "/metrics",      ← Prometheus metrics
#     "/logs",         ← Container logs
#     "/openapi/v2",
#     "/version"       ← Cluster version
#   ]
# }
```

**Two categories of API groups:**

| Category | Path | Contains | Example Resources |
|---|---|---|---|
| **Core group** | `/api/v1` | Essential resources (no group prefix in apiVersion) | Pods, Services, Namespaces, Nodes, ConfigMaps, Secrets, PVs, PVCs, Events |
| **Named groups** | `/apis/<group>/v1` | Organized by functionality | Deployments (`apps`), Ingress (`networking.k8s.io`), StorageClass (`storage.k8s.io`), CertificateSigningRequest (`certificates.k8s.io`) |

```
┌─────────────────────────────────────────────────────────────┐
│  /api (Core Group)                                          │
│  └── v1                                                     │
│      ├── pods          ├── services      ├── namespaces     │
│      ├── nodes         ├── configmaps    ├── secrets        │
│      ├── events        ├── endpoints     ├── pv / pvc       │
│      └── replicationcontrollers                             │
│                                                             │
│  /apis (Named Groups)                                       │
│  ├── apps/v1           → deployments, replicasets,          │
│  │                       statefulsets, daemonsets            │
│  ├── batch/v1          → jobs, cronjobs                     │
│  ├── networking.k8s.io/v1 → ingresses, networkpolicies     │
│  ├── storage.k8s.io/v1 → storageclasses, csinodes          │
│  ├── rbac.authorization.k8s.io/v1 → roles, rolebindings    │
│  ├── certificates.k8s.io/v1 → certificatesigningrequests   │
│  └── autoscaling/v2   → horizontalpodautoscalers            │
│                                                             │
│  Each resource supports verbs:                              │
│  list, get, create, update, patch, delete, watch            │
└─────────────────────────────────────────────────────────────┘
```

Every API resource has associated **verbs** (actions): `list`, `get`, `create`, `update`, `patch`, `delete`, `watch`. These verbs are what RBAC rules reference when granting permissions.

**Querying the API server directly:**

Without proper authentication, the API server returns 403 Forbidden:

```bash
curl https://kube-master:6443/apis -k

# Output:
# {
#   "kind": "Status",
#   "status": "Failure",
#   "message": "forbidden: User \"system:anonymous\" cannot get path \"/apis\"",
#   "reason": "Forbidden",
#   "code": 403
# }
```

Two ways to authenticate:

```bash
# Method 1: Pass certificate files directly
curl https://kube-master:6443/apis -k \
  --key admin.key \
  --cert admin.crt \
  --cacert ca.crt

# Method 2: Use kubectl proxy (recommended for exploration)
# Starts a local proxy on port 8001 using your kubeconfig credentials
kubectl proxy
# Starting to serve on 127.0.0.1:8001

# Now query without certificates
curl http://localhost:8001/apis
# Returns the full list of named API groups
```

⚠️ **`kube-proxy` ≠ `kubectl proxy`** — these are completely different:

| | `kube-proxy` | `kubectl proxy` |
|---|---|---|
| **Purpose** | Network proxy on every node for Service routing | Local HTTP proxy to the API server |
| **Runs on** | Every node (DaemonSet) | Your workstation |
| **Handles** | Pod-to-Service traffic (iptables/IPVS rules) | API server requests using kubeconfig creds |

### API Request Flow

```
┌──────────────────────────────────────────────────────────────┐
│  API Request Lifecycle                                       │
│                                                              │
│  kubectl / client                                            │
│       │                                                      │
│       ▼                                                      │
│  ┌─ Authentication ─┐  Who are you?                          │
│  │  • Client certs   │  • X.509 certificates                 │
│  │  • Bearer tokens  │  • ServiceAccount tokens              │
│  │  • OIDC           │  • AWS IAM (EKS)                      │
│  │  • Webhook        │  • Custom auth webhook                │
│  └───────┬───────────┘                                       │
│          ▼                                                   │
│  ┌─ Authorization ───┐  Are you allowed?                     │
│  │  • RBAC           │  Role/ClusterRole + Bindings          │
│  │  • ABAC           │  Attribute-based (legacy)             │
│  │  • Webhook        │  External authorization               │
│  │  • Node           │  kubelet-specific permissions         │
│  └───────┬───────────┘                                       │
│          ▼                                                   │
│  ┌─ Admission Control┐  Should this be modified/rejected?    │
│  │  • Mutating       │  Modify the request (inject sidecars) │
│  │  • Validating     │  Reject invalid requests              │
│  │  • OPA/Gatekeeper │  Policy enforcement                   │
│  └───────┬───────────┘                                       │
│          ▼                                                   │
│  ┌─ Persistence ─────┐                                       │
│  │  Write to etcd    │                                       │
│  └───────────────────┘                                       │
└──────────────────────────────────────────────────────────────┘
```

### API Server Security Configuration

```bash
# View API server configuration (kubeadm clusters)
cat /etc/kubernetes/manifests/kube-apiserver.yaml | grep -E "^\s+--"

# Key flags:
# --authorization-mode=Node,RBAC          ← Authorization modes
# --enable-admission-plugins=...          ← Active admission controllers
# --audit-log-path=/var/log/kubernetes/audit.log  ← Audit logging
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
# --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
# --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
# --client-ca-file=/etc/kubernetes/pki/ca.crt
# --etcd-servers=https://127.0.0.1:2379
# --service-account-key-file=/etc/kubernetes/pki/sa.pub
```

### API Audit Logging

Audit logs record every API request — who did what, when, and from where.

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all requests to secrets at Metadata level
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]

# Log pod creation/deletion at RequestResponse level
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods"]
  verbs: ["create", "delete"]

# Log everything else at Request level
- level: Request
  resources:
  - group: ""
    resources: ["*"]
```

```bash
# Audit log levels:
# None         → Don't log
# Metadata     → Log request metadata (user, timestamp, resource, verb)
# Request      → Log metadata + request body
# RequestResponse → Log metadata + request body + response body

# View audit logs
tail -f /var/log/kubernetes/audit.log | jq .

# Output:
# {
#   "kind": "Event",
#   "apiVersion": "audit.k8s.io/v1",
#   "level": "Metadata",
#   "stage": "ResponseComplete",
#   "requestURI": "/api/v1/namespaces/default/pods",
#   "verb": "list",
#   "user": {"username": "admin", "groups": ["system:masters"]},
#   "sourceIPs": ["10.0.1.50"],
#   "responseStatus": {"code": 200},
#   "requestReceivedTimestamp": "2024-01-15T10:00:00.000000Z"
# }

# On EKS, enable audit logging:
eksctl utils update-cluster-logging \
  --enable-types=audit,api,authenticator \
  --cluster=my-k8s-cluster --approve

# View in CloudWatch:
# Log group: /aws/eks/my-k8s-cluster/cluster
```

### API Rate Limiting (Priority and Fairness)

Kubernetes 1.20+ uses API Priority and Fairness (APF) to prevent any single client from overwhelming the API server. In multi-tenant clusters, APF ensures that API requests from critical namespaces are prioritized over less important traffic.

APF uses two objects:
- **PriorityLevelConfiguration** — defines how many concurrent requests a priority level can handle
- **FlowSchema** — maps requests (by user, namespace, or service account) to a priority level

```bash
# View flow schemas (rate limiting rules)
kubectl get flowschema

# Output:
# NAME                           PRIORITYLEVEL     MATCHINGPRECEDENCE   DISTINGUISHERMETHOD   AGE
# system-leader-election         leader-election   100                  ByUser                30d
# workload-leader-election       leader-election   200                  ByUser                30d
# system-nodes                   system            500                  ByUser                30d
# kube-system-service-accounts   workload-high     900                  ByNamespace           30d
# global-default                 global-default    9900                 ByUser                30d

# View priority levels
kubectl get prioritylevelconfiguration

# Output:
# NAME              TYPE      ASSUREDCONCURRENCYSHARES   QUEUES   HANDSIZE   QUEUELENGTHLIMIT
# system            Limited   30                         64       8          50
# leader-election   Limited   10                         16       4          50
# workload-high     Limited   40                         128      6          50
# workload-low      Limited   100                        128      6          50
# global-default    Limited   20                         128      6          50

# If you see 429 (Too Many Requests) errors:
# → Check which flow schema is throttling
kubectl get flowschema -o custom-columns=NAME:.metadata.name,REJECTED:.status.conditions
```

#### Configuring Custom Priority Levels

Define priority levels with different concurrency shares. Higher `assuredConcurrencyShares` means more API server capacity:

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: PriorityLevelConfiguration
metadata:
  name: high-priority
spec:
  type: Limited
  limited:
    assuredConcurrencyShares: 10    # Gets 10x the capacity of low-priority
    limitResponse:
      type: Queue
---
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: PriorityLevelConfiguration
metadata:
  name: low-priority
spec:
  type: Limited
  limited:
    assuredConcurrencyShares: 1
    limitResponse:
      type: Queue
```

#### Mapping Requests to Priority Levels with FlowSchemas

FlowSchemas match API requests by subject (user, group, service account) and route them to a priority level. Lower `matchingPrecedence` values are evaluated first:

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: high-priority-namespace-a
spec:
  priorityLevelConfiguration:
    name: high-priority
  matchingPrecedence: 1000          # Evaluated before precedence 2000
  rules:
  - subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: "system-account"
        namespace: "namespace-a"    # Critical tenant
    resourceRules:
    - verbs: ["*"]
      apiGroups: ["*"]
      resources: ["*"]
---
apiVersion: flowcontrol.apiserver.k8s.io/v1beta3
kind: FlowSchema
metadata:
  name: low-priority-namespace-b
spec:
  priorityLevelConfiguration:
    name: low-priority
  matchingPrecedence: 2000
  rules:
  - subjects:
    - kind: Group
      group:
        name: "regular-users"
    - kind: ServiceAccount
      serviceAccount:
        name: "default"
        namespace: "namespace-b"    # Non-critical tenant
    resourceRules:
    - verbs: ["*"]
      apiGroups: ["*"]
      resources: ["*"]
```

#### API Priority vs Pod Priority

These are distinct mechanisms that address different resource types:

| | API Priority and Fairness | Pod Priority and Preemption |
|---|---|---|
| **Scope** | API server request processing | Node-level resource allocation (CPU, memory) |
| **Controls** | Which API requests get processed first | Which pods get scheduled/evicted first |
| **Objects** | PriorityLevelConfiguration, FlowSchema | PriorityClass |
| **Effect** | Prevents API server overload from one tenant | Ensures critical pods get node resources |

Both are needed in multi-tenant clusters — APF protects the control plane, while PriorityClass protects workload scheduling. See [MODULE-19 §19.2](MODULE-19-Scheduling.md) for Pod Priority and Preemption configuration.

### API Versioning and Compatibility

```bash
# List all API resources and their versions
kubectl api-resources

# Output (partial):
# NAME          SHORTNAMES   APIVERSION   NAMESPACED   KIND
# pods          po           v1           true         Pod
# services      svc          v1           true         Service
# deployments   deploy       apps/v1      true         Deployment
# ingresses     ing          networking.k8s.io/v1   true   Ingress

# Check available API versions
kubectl api-versions

# Output:
# apps/v1
# autoscaling/v2
# batch/v1
# networking.k8s.io/v1
# v1

# Check for deprecated APIs in your manifests
kubectl get --raw /apis | jq '.groups[].preferredVersion'

# Detect deprecated API usage before upgrading
# Install pluto (deprecated API detector)
# pluto detect-all-in-cluster

# Output:
# NAME        KIND        VERSION              REPLACEMENT          DEPRECATED   REMOVED
# my-ingress  Ingress     extensions/v1beta1   networking.k8s.io/v1 true         true
```

**Interview question: How does Kubernetes API management work?**
Every API request goes through three stages: Authentication (who are you — certs, tokens, OIDC), Authorization (are you allowed — RBAC), and Admission Control (should this be modified/rejected — webhooks, OPA). The API server also supports audit logging to track all actions, rate limiting via Priority and Fairness to prevent overload, and API versioning for backward compatibility. On EKS, authentication integrates with AWS IAM.

---

---

