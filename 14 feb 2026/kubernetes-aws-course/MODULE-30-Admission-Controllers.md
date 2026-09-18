# MODULE 30: Admission Controllers & Webhooks

---

## 30.1 Admission Controllers & Webhooks

### What Are Admission Controllers?

Every request to the Kubernetes API server passes through three stages before the object is persisted to etcd:

1. **Authentication** — Who are you? (certificates, tokens, OIDC, AWS IAM on EKS)
2. **Authorization** — Are you allowed? (RBAC, Node, Webhook)
3. **Admission Control** — Should this request be modified or rejected? (admission controllers)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Kubernetes API Request Flow                                  │
│                                                                                     │
│  kubectl apply ──► API Server                                                       │
│                       │                                                             │
│                       ▼                                                             │
│               ┌───────────────┐                                                     │
│               │Authentication │  Who are you?                                       │
│               │ (certs, OIDC, │  Verify identity via certificates, tokens,          │
│               │  AWS IAM)     │  or OIDC providers                                  │
│               └───────┬───────┘                                                     │
│                       │                                                             │
│                       ▼                                                             │
│               ┌───────────────┐                                                     │
│               │ Authorization │  Are you allowed?                                   │
│               │ (RBAC, Node,  │  Check roles, bindings, and policies                │
│               │  Webhook)     │                                                     │
│               └───────┬───────┘                                                     │
│                       │                                                             │
│                       ▼                                                             │
│               ┌───────────────────────────────────────────────────────────┐          │
│               │              Admission Control Phase                     │          │
│               │                                                          │          │
│               │  ┌──────────────────┐    ┌───────────────────┐           │          │
│               │  │ Mutating Plugins │───►│ Validating Plugins│           │          │
│               │  │ (modify request) │    │ (accept / reject) │           │          │
│               │  └──────────────────┘    └───────────────────┘           │          │
│               │         │                         │                      │          │
│               │         ▼                         ▼                      │          │
│               │  ┌──────────────────┐    ┌───────────────────┐           │          │
│               │  │ MutatingWebhook  │    │ValidatingWebhook  │           │          │
│               │  │ (external calls) │    │ (external calls)  │           │          │
│               │  └──────────────────┘    └───────────────────┘           │          │
│               └───────────────────────────┬───────────────────────────────┘          │
│                                           │                                         │
│                                           ▼                                         │
│                                   ┌───────────────┐                                 │
│                                   │  Object Schema│  Validate against OpenAPI       │
│                                   │  Validation   │  schema                         │
│                                   └───────┬───────┘                                 │
│                                           │                                         │
│                                           ▼                                         │
│                                   ┌───────────────┐                                 │
│                                   │     etcd      │  Persist the object             │
│                                   └───────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

Admission controllers intercept API requests **after** authentication and authorization but **before** the object is persisted to etcd. They can **validate** (accept/reject) or **mutate** (modify) requests.

**Key point:** Admission controllers do NOT handle authentication. They operate on already-authenticated and authorized requests.

### Why RBAC Alone Isn't Enough

RBAC controls **who** can perform **what operations** on **which resources**. For example, this role allows a developer to create pods:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
rules:
- apiGroups: [""]          # "" = core API group (pods, services, etc.)
  resources: ["pods"]      # Resource type this rule applies to
  verbs: ["list", "get", "create", "update", "delete"]  # Allowed operations
```

You can restrict which specific resource names are allowed:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["create"]
  resourceNames: ["blue", "orange"]  # Only pods named "blue" or "orange"
```

But RBAC **cannot inspect the contents** of a request. Consider this pod spec:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: web-pod
spec:
  containers:
  - name: ubuntu
    image: ubuntu:latest           # Using public registry + latest tag
    command: ["sleep", "3600"]
    securityContext:
      runAsUser: 0                 # Running as root
      capabilities:
        add: ["MAC_ADMIN"]         # Dangerous Linux capability
```

RBAC can confirm the user is allowed to create pods, but it **cannot**:

| Policy Requirement | RBAC Can Enforce? | Admission Controller Can Enforce? |
|---|---|---|
| Block images from public registries | ❌ No | ✅ Yes |
| Reject the `latest` tag | ❌ No | ✅ Yes |
| Prevent containers running as root | ❌ No | ✅ Yes |
| Disallow dangerous capabilities | ❌ No | ✅ Yes |
| Enforce resource requests/limits | ❌ No | ✅ Yes |
| Inject sidecar containers automatically | ❌ No | ✅ Yes |
| Add default labels/annotations | ❌ No | ✅ Yes |

These content-level policies require **admission controllers**.

**Real-world use cases for admission controllers:**

| Use Case | Controller Type | Example |
|---|---|---|
| Enforce private registry | Validating | Reject `docker.io/*` images, allow only `company.ecr.aws/*` |
| Inject sidecar containers | Mutating | Istio injects Envoy proxy into every pod |
| Add default labels | Mutating | Auto-add `team`, `environment`, `cost-center` labels |
| Enforce resource limits | Validating | Reject pods without `resources.limits` |
| Prevent privileged containers | Validating | Reject `securityContext.privileged: true` in production |
| Default storage class | Mutating | Add `storageClassName: gp3` to PVCs without one |
| Image pull policy | Mutating | Force `imagePullPolicy: Always` on all containers |

### Built-in Admission Controllers

Kubernetes ships with many built-in admission controllers. Some are enabled by default, others must be explicitly enabled:

| Controller | Type | Default? | Purpose |
|---|---|---|---|
| `NamespaceLifecycle` | Validating | ✅ | Rejects requests in non-existent namespaces; prevents deletion of system namespaces |
| `LimitRanger` | Mutating | ✅ | Applies default resource limits from LimitRange objects |
| `ResourceQuota` | Validating | ✅ | Enforces namespace resource quotas |
| `ServiceAccount` | Mutating | ✅ | Automatically mounts service account tokens into pods |
| `DefaultStorageClass` | Mutating | ✅ | Assigns default StorageClass to PVCs when none is specified |
| `DefaultTolerationSeconds` | Mutating | ✅ | Adds default tolerations for `node.kubernetes.io/not-ready` and `unreachable` taints |
| `PersistentVolumeClaimResize` | Validating | ✅ | Validates PVC resize requests against StorageClass `allowVolumeExpansion` |
| `MutatingAdmissionWebhook` | Mutating | ✅ | Calls external webhooks to modify requests |
| `ValidatingAdmissionWebhook` | Validating | ✅ | Calls external webhooks to accept/reject requests |
| `StorageObjectInUseProtection` | Validating | ✅ | Prevents deletion of PVs/PVCs that are in use |
| `Priority` | Mutating | ✅ | Assigns priority to pods based on PriorityClass |
| `TaintNodesByCondition` | Mutating | ✅ | Adds taints to nodes based on conditions |
| `NodeRestriction` | Validating | ❌ | Limits what kubelets can modify (only their own node/pods) |
| `AlwaysPullImages` | Mutating | ❌ | Forces `imagePullPolicy: Always` on every container |
| `PodSecurity` | Validating | ✅ (v1.25+) | Enforces Pod Security Standards (Baseline, Restricted) |
| `EventRateLimit` | Validating | ❌ | Limits the rate of API requests to prevent overload |
| `NamespaceAutoProvision` | Mutating | ❌ | Auto-creates namespaces (deprecated) |

### Mutating vs Validating — Execution Order

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Admission Controller Pipeline                    │
│                                                                     │
│  Request ──► Mutating Controllers ──► Validating Controllers ──► etcd│
│              (run FIRST)              (run SECOND)                   │
│              Can modify the object    Can only accept/reject         │
│                                                                     │
│  Why this order matters:                                            │
│  - Mutating controllers may add defaults (e.g., storage class)     │
│  - Validating controllers then check the FINAL state               │
│  - If mutating ran second, validators would check stale data       │
│                                                                     │
│  If ANY controller rejects ──► entire request is DENIED             │
│  Error returned to user immediately                                 │
└─────────────────────────────────────────────────────────────────────┘
```

- **Mutating** controllers run first — they can change the request (add defaults, inject sidecars, modify labels)
- **Validating** controllers run second — they can only accept or reject (no modifications)
- A controller can be both mutating and validating
- If **any** admission controller rejects a request, the entire request is denied and an error is returned to the user

**Example: DefaultStorageClass mutation in action**

When you create a PVC without specifying a storage class:

```yaml
# Original PVC request (no storageClassName)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  # Note: no storageClassName specified
```

The DefaultStorageClass admission controller intercepts the request and mutates it:

```yaml
# After mutation by DefaultStorageClass admission controller
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: gp3    # <-- Added by the admission controller
```

**Inspecting the mutated PVC:**

```bash
kubectl describe pvc myclaim
```

```
Name:           myclaim
Namespace:      default
StorageClass:   gp3              # <-- Admission controller added this
Status:         Pending
Volume:         <none>
Labels:         <none>
Annotations:    <none>
Finalizers:     [kubernetes.io/pvc-protection]
Capacity:
Access Modes:
VolumeMode:     Filesystem
Used By:        <none>
```

The `StorageClass: gp3` field confirms the admission controller mutated the request — the original PVC had no storage class specified.

### Namespace Admission Controllers

A practical example of how admission controllers work — namespace validation:

**Scenario 1: NamespaceLifecycle (default, enabled)**

If you try to create a pod in a namespace that doesn't exist:

```bash
kubectl run nginx --image nginx --namespace blue
```

```
Error from server (NotFound): namespaces "blue" not found
```

The NamespaceLifecycle admission controller checks whether the target namespace exists and rejects the request if it doesn't. It also prevents deletion of system namespaces (`default`, `kube-system`, `kube-public`).

**Scenario 2: NamespaceAutoProvision (deprecated, disabled by default)**

With the auto-provision controller enabled, the same command automatically creates the namespace:

```bash
kubectl run nginx --image nginx --namespace blue
```

```
pod/nginx created
```

```bash
kubectl get namespaces
```

```
NAME              STATUS   AGE
blue              Active   3m      # <-- Auto-created by the admission controller
default           Active   23m
kube-node-lease   Active   23m
kube-public       Active   24m
kube-system       Active   24m
```

⚠️ **Deprecation note:** Both `NamespaceExists` and `NamespaceAutoProvision` are deprecated. They have been replaced by `NamespaceLifecycle`, which rejects requests to non-existent namespaces AND protects default namespaces from deletion. The lab exercises still use `NamespaceAutoProvision` to demonstrate how mutating controllers work.

### Viewing Enabled Admission Controllers

**Method 1: Check the API server help text (shows all available plugins)**

```bash
# On a non-kubeadm cluster (direct binary access)
kube-apiserver -h | grep enable-admission-plugins
```

```
--enable-admission-plugins strings
    admission plugins that should be enabled in addition to default enabled ones
    (NamespaceLifecycle, LimitRanger, ServiceAccount, TaintNodesByCondition,
    Priority, DefaultTolerationSeconds, DefaultStorageClass,
    StorageObjectInUseProtection, PersistentVolumeClaimResize,
    RuntimeClass, CertificateApproval, CertificateSigning,
    ClusterTrustBundleAttest, DefaultIngressClass,
    MutatingAdmissionWebhook, ValidatingAdmissionPolicy,
    ValidatingAdmissionWebhook, ResourceQuota)
```

The plugins listed in parentheses are the **default enabled** ones. Any plugin not in this list must be explicitly enabled.

```bash
# On a kubeadm-based cluster (API server runs as a static pod)
kubectl exec -n kube-system kube-apiserver-controlplane -- \
  kube-apiserver -h | grep enable-admission-plugins
```

**Method 2: Check the running API server configuration**

```bash
# From the pod description (shows explicitly configured plugins)
kubectl -n kube-system describe pod kube-apiserver-controlplane | grep -i admission
```

```
      --enable-admission-plugins=NodeRestriction
```

This shows only **explicitly added** plugins. The default plugins are also active but not listed here.

**Method 3: Check the static pod manifest directly**

```bash
# On the control plane node
grep enable-admission-plugins /etc/kubernetes/manifests/kube-apiserver.yaml
```

```
    - --enable-admission-plugins=NodeRestriction
```

**Method 4: Check the running process**

```bash
ps -ef | grep kube-apiserver | grep admission
```

This shows the actual command-line arguments of the running kube-apiserver process, including both `--enable-admission-plugins` and `--disable-admission-plugins` flags.

### Enabling and Disabling Admission Controllers

**Method 1: Non-kubeadm setup (systemd service file)**

Edit the kube-apiserver service file and add the `--enable-admission-plugins` flag:

```bash
# /etc/systemd/system/kube-apiserver.service
ExecStart=/usr/local/bin/kube-apiserver \
  --advertise-address=${INTERNAL_IP} \
  --allow-privileged=true \
  --apiserver-count=3 \
  --authorization-mode=Node,RBAC \
  --bind-address=0.0.0.0 \
  --etcd-servers=https://127.0.0.1:2379 \
  --event-ttl=1h \
  --runtime-config=api/all \
  --service-cluster-ip-range=10.32.0.0/24 \
  --service-node-port-range=30000-32767 \
  --v=2 \
  --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
#                            ^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^
#                            already enabled   newly added plugin
```

```bash
# Reload and restart after editing
sudo systemctl daemon-reload       # Reload systemd unit files
sudo systemctl restart kube-apiserver  # Restart the API server
```

**Method 2: kubeadm setup (static pod manifest)**

Edit the API server manifest at `/etc/kubernetes/manifests/kube-apiserver.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  creationTimestamp: null
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-apiserver
    - --authorization-mode=Node,RBAC
    - --advertise-address=172.17.0.107
    - --allow-privileged=true
    - --enable-bootstrap-token-auth=true
    - --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
    #                            ^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^^^^^^
    #                            Comma-separated list of plugins to enable
    image: registry.k8s.io/kube-apiserver:v1.30.0
    name: kube-apiserver
```

The kubelet watches `/etc/kubernetes/manifests/` and automatically restarts the API server when the manifest changes. No manual restart needed.

**Disabling a specific plugin:**

Add the `--disable-admission-plugins` flag on a separate line:

```yaml
    - --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
    - --disable-admission-plugins=DefaultStorageClass
    #                             ^^^^^^^^^^^^^^^^^^^
    #                             This overrides the default-enabled status
```

**Verification after enabling NamespaceAutoProvision:**

```bash
# Create a pod in a non-existent namespace
kubectl run nginx --image nginx --namespace blue
```

```
pod/nginx created
```

```bash
kubectl get namespaces
```

```
NAME              STATUS   AGE
blue              Active   7s       # <-- Auto-created
default           Active   50m
kube-node-lease   Active   50m
kube-public       Active   50m
kube-system       Active   50m
```

The namespace was automatically created — demonstrating that admission controllers can perform backend operations, not just validate.

**Verification after disabling DefaultStorageClass:**

```bash
# Create a PVC without specifying a storage class
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
EOF
```

```bash
kubectl describe pvc test-pvc | grep StorageClass
```

```
StorageClass:                    # <-- Empty! No default was injected
```

Without the DefaultStorageClass controller, PVCs created without a `storageClassName` will remain without one.

⚠️ **Important:** After editing the static pod manifest, the API server restarts automatically. During restart (10-30 seconds), `kubectl` commands will fail with connection errors. Wait for the API server to come back:

```bash
# Wait for the API server to restart
kubectl get pods -n kube-system --watch
# Or check the process directly on the control plane node
crictl ps | grep kube-apiserver
```

### How External Admission Webhooks Work

Built-in admission controllers are compiled into the API server binary. For custom logic, Kubernetes supports **external admission webhooks** — your own servers that the API server calls during admission.

Webhook servers can run:
- **Inside the cluster** — as a Deployment + Service (most common)
- **Outside the cluster** — as an external HTTPS endpoint (use `url` instead of `service` in clientConfig)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    External Webhook Architecture                            │
│                                                                             │
│  API Server                                                                 │
│      │                                                                      │
│      ├──► Built-in Admission Controllers (compiled in binary)               │
│      │         │                                                            │
│      │         ▼                                                            │
│      ├──► MutatingAdmissionWebhook controller                               │
│      │         │                                                            │
│      │         │  HTTPS POST (AdmissionReview JSON)                         │
│      │         ▼                                                            │
│      │    ┌─────────────────────────────────────────┐                       │
│      │    │  Your Mutating Webhook Server            │                       │
│      │    │  (Deployment + ClusterIP Service)        │                       │
│      │    │                                          │                       │
│      │    │  Receives: AdmissionReview request       │                       │
│      │    │  Returns:  AdmissionReview response      │                       │
│      │    │            + optional JSON Patch          │                       │
│      │    └─────────────────────────────────────────┘                       │
│      │         │                                                            │
│      │         ▼                                                            │
│      ├──► ValidatingAdmissionWebhook controller                             │
│      │         │                                                            │
│      │         │  HTTPS POST (AdmissionReview JSON)                         │
│      │         ▼                                                            │
│      │    ┌─────────────────────────────────────────┐                       │
│      │    │  Your Validating Webhook Server          │                       │
│      │    │  (Deployment + ClusterIP Service)        │                       │
│      │    │                                          │                       │
│      │    │  Receives: AdmissionReview request       │                       │
│      │    │  Returns:  AdmissionReview response      │                       │
│      │    │            (allowed: true/false)          │                       │
│      │    └─────────────────────────────────────────┘                       │
│      │                                                                      │
│      ▼                                                                      │
│    etcd (persist object)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### AdmissionReview: The Webhook Protocol

The API server communicates with webhooks using `AdmissionReview` objects. It sends a request, and the webhook responds with allow/deny (and optional patches for mutation).

**Request sent by the API server to the webhook:**

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "request": {
    "uid": "705ab415-6393-11e7-b7cc-4201a8000002",
    // uid: unique identifier for this request — must be echoed back in the response
    "kind": {"group": "", "version": "v1", "kind": "Pod"},
    // kind: the type of object being created/modified
    "resource": {"group": "", "version": "v1", "resource": "pods"},
    // resource: the API resource being accessed
    "namespace": "default",
    // namespace: where the object is being created
    "operation": "CREATE",
    // operation: CREATE, UPDATE, DELETE, or CONNECT
    "userInfo": {
      "username": "admin",
      "groups": ["system:masters"]
    },
    // userInfo: who is making the request (already authenticated)
    "object": {
      "metadata": {"name": "nginx", "labels": {"app": "web"}},
      "spec": {
        "containers": [{"name": "nginx", "image": "nginx:1.25"}]
      }
    }
    // object: the full object being submitted
  }
}
```

**Response from the webhook (allowed):**

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "705ab415-6393-11e7-b7cc-4201a8000002",
    // uid: MUST match the request uid
    "allowed": true
    // allowed: true = permit the request, false = deny it
  }
}
```

**Response from the webhook (denied):**

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "705ab415-6393-11e7-b7cc-4201a8000002",
    "allowed": false,
    "status": {
      "message": "Images from public Docker Hub are not allowed"
      // message: human-readable reason shown to the user
    }
  }
}
```

**Response from a mutating webhook (allowed with patch):**

Mutating webhooks can modify the object using JSON Patch format (RFC 6902):

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "705ab415-6393-11e7-b7cc-4201a8000002",
    "allowed": true,
    "patchType": "JSONPatch",
    // patchType: must be "JSONPatch" — the only supported type
    "patch": "W3sib3AiOiAiYWRkIiwgInBhdGgiOiAiL21ldGFkYXRhL2xhYmVscy90ZWFtIiwgInZhbHVlIjogInBsYXRmb3JtIn1d"
    // patch: base64-encoded JSON Patch array
  }
}
```

The `patch` field is a base64-encoded JSON Patch array. Decoded:

```json
[{"op": "add", "path": "/metadata/labels/team", "value": "platform"}]
```

This adds a `team: platform` label to the object. Common patch operations:

| Operation | Description | Example |
|---|---|---|
| `add` | Add a new field | `{"op": "add", "path": "/metadata/labels/env", "value": "prod"}` |
| `replace` | Change an existing field | `{"op": "replace", "path": "/spec/containers/0/image", "value": "nginx:1.26"}` |
| `remove` | Delete a field | `{"op": "remove", "path": "/metadata/annotations/temp"}` |

#### Writing a Webhook Server

A webhook server is any HTTPS server that accepts `AdmissionReview` requests and returns `AdmissionReview` responses. Below are minimal examples in Go and Python.

**Go webhook server (validation):**

```go
package main

import (
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"

    admissionv1 "k8s.io/api/admission/v1"          // Kubernetes admission API types
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"   // Kubernetes metadata types
)

func validate(w http.ResponseWriter, r *http.Request) {
    body, _ := ioutil.ReadAll(r.Body)               // Read the incoming request body

    var review admissionv1.AdmissionReview
    json.Unmarshal(body, &review)                    // Deserialize the AdmissionReview

    // Business logic: reject pods named "forbidden"
    allowed := true
    message := ""
    if review.Request.Name == "forbidden" {
        allowed = false
        message = "Pods named 'forbidden' are not allowed"
    }

    // Build the response — uid MUST match the request
    response := admissionv1.AdmissionReview{
        Response: &admissionv1.AdmissionResponse{
            UID:     review.Request.UID,             // Echo back the request UID
            Allowed: allowed,                        // true = allow, false = deny
            Result:  &metav1.Status{Message: message},
        },
    }
    response.SetGroupVersionKind(review.GroupVersionKind())

    resp, _ := json.Marshal(response)
    w.Header().Set("Content-Type", "application/json")
    w.Write(resp)
}

func main() {
    http.HandleFunc("/validate", validate)
    fmt.Println("Webhook server listening on :443")
    // TLS is REQUIRED — the API server only calls webhooks over HTTPS
    http.ListenAndServeTLS(":443", "/tls/tls.crt", "/tls/tls.key", nil)
}
```

**Python webhook server (validation + mutation):**

```python
from flask import Flask, request, jsonify
import base64, json

app = Flask(__name__)

@app.route("/validate", methods=["POST"])
def validate():
    review = request.json
    obj_name = review["request"]["object"]["metadata"]["name"]
    user_name = review["request"]["userInfo"]["username"]

    allowed = True
    message = ""
    # Business logic: prevent users from creating objects with their own name
    if obj_name == user_name:
        allowed = False
        message = "You can't create objects with your own name"

    return jsonify({
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": review["request"]["uid"],    # Echo back the request UID
            "allowed": allowed,
            "status": {"message": message}
        }
    })

@app.route("/mutate", methods=["POST"])
def mutate():
    review = request.json
    user_name = review["request"]["userInfo"]["username"]

    # Mutation: add a label tracking who created this object
    patch = [{"op": "add", "path": "/metadata/labels/created-by", "value": user_name}]
    encoded_patch = base64.b64encode(json.dumps(patch).encode()).decode()

    return jsonify({
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": review["request"]["uid"],
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": encoded_patch              # Base64-encoded JSON Patch
        }
    })

if __name__ == "__main__":
    # TLS is mandatory — API server only calls webhooks over HTTPS
    app.run(host="0.0.0.0", port=443, ssl_context=("/tls/tls.crt", "/tls/tls.key"))
```

The webhook server is deployed as a regular Kubernetes Deployment, exposed via a ClusterIP Service, and referenced in the webhook configuration's `clientConfig.service` field.

### Webhook Configuration Objects

Two Kubernetes resources register your webhooks with the API server:

**ValidatingWebhookConfiguration — reject pods without resource limits:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: require-resource-limits
webhooks:
- name: require-limits.example.com
  # name: must be a fully-qualified domain name
  admissionReviewVersions: ["v1"]
  # admissionReviewVersions: API versions the webhook understands
  sideEffects: None
  # sideEffects: None = webhook has no side effects outside the response
  #              NoneOnDryRun = has side effects, but not during dry-run
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE"]
    # operations: which API operations trigger this webhook
    resources: ["pods"]
    scope: "Namespaced"
    # scope: Namespaced = only namespaced resources, Cluster = cluster-scoped
  clientConfig:
    service:
      name: webhook-service
      namespace: webhook-system
      path: "/validate"
      # path: the HTTP endpoint on your webhook server
    caBundle: <base64-encoded-CA>
    # caBundle: CA cert that signed the webhook server's TLS cert
  failurePolicy: Fail
  # failurePolicy: Fail = reject if webhook unavailable (safer)
  #                Ignore = allow if webhook unavailable (less safe)
  namespaceSelector:
    matchExpressions:
    - key: environment
      operator: NotIn
      values: ["kube-system"]
  # namespaceSelector: only trigger for objects in matching namespaces
  # This skips kube-system to avoid breaking system components
  timeoutSeconds: 10
  # timeoutSeconds: how long to wait for webhook response (default: 10)
```

**MutatingWebhookConfiguration — inject labels:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: add-labels
webhooks:
- name: add-labels.example.com
  admissionReviewVersions: ["v1"]
  sideEffects: None
  reinvocationPolicy: IfNeeded
  # reinvocationPolicy: IfNeeded = re-invoke if another mutating webhook
  #                     modified the object after this one ran
  #                     Never = only invoke once (default)
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  clientConfig:
    service:
      name: label-webhook
      namespace: webhook-system
      path: "/mutate"
    caBundle: <base64-encoded-CA>
  failurePolicy: Ignore
  # Ignore = if webhook is down, allow the request anyway
  # Use Ignore for non-critical mutations (labels, annotations)
  # Use Fail for security-critical validations
```

**Key configuration fields summary:**

| Field | Purpose | Values |
|---|---|---|
| `clientConfig.service` | In-cluster webhook Service reference | `name`, `namespace`, `path` |
| `clientConfig.url` | External webhook URL (alternative to service) | `https://external.example.com/validate` |
| `caBundle` | CA certificate for TLS verification | Base64-encoded PEM |
| `rules` | Which API operations trigger the webhook | `apiGroups`, `operations`, `resources` |
| `failurePolicy` | Behavior when webhook is unavailable | `Fail` (reject) or `Ignore` (allow) |
| `sideEffects` | Whether webhook has side effects | `None`, `NoneOnDryRun` |
| `timeoutSeconds` | Webhook response timeout | 1-30 (default: 10) |
| `namespaceSelector` | Filter by namespace labels | Label selector |
| `objectSelector` | Filter by object labels | Label selector |
| `reinvocationPolicy` | Re-invoke after other mutations | `Never` (default), `IfNeeded` |
| `matchPolicy` | How rules match API versions | `Exact`, `Equivalent` |

### Deploying a Mutating Webhook — Full Walkthrough

This walkthrough deploys a mutating admission webhook that enforces container security policies:
- Pods with no `securityContext` are mutated to set `runAsNonRoot: true` and `runAsUser: 1234`
- Pods that explicitly set `runAsNonRoot: false` are allowed to run as root
- Pods with conflicting settings (`runAsNonRoot: true` + `runAsUser: 0`) are rejected

```
┌──────────────────────────────────────────────────────────────────────┐
│                  Webhook Deployment Architecture                     │
│                                                                      │
│  ┌──────────────┐     HTTPS POST      ┌──────────────────────────┐  │
│  │  API Server   │ ──────────────────► │  Webhook Server Pod      │  │
│  │              │  AdmissionReview     │  (webhook-demo namespace)│  │
│  │              │ ◄────────────────── │                          │  │
│  └──────────────┘  Allow/Deny/Patch   │  Mounted TLS Secret:     │  │
│                                        │  /tls/tls.crt            │  │
│  Configured via:                       │  /tls/tls.key            │  │
│  MutatingWebhookConfiguration         │                          │  │
│  (cluster-scoped resource)            └──────────┬───────────────┘  │
│                                                   │                  │
│                                        ┌──────────▼───────────────┐  │
│                                        │  ClusterIP Service       │  │
│                                        │  webhook-server:443      │  │
│                                        └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

#### Step 1: Create the Namespace

```bash
kubectl create ns webhook-demo
```

```
namespace/webhook-demo created
```

```bash
kubectl get ns
```

```
NAME              STATUS   AGE
default           Active   37m
kube-node-lease   Active   37m
kube-public       Active   37m
kube-system       Active   37m
webhook-demo      Active   3s      # <-- New namespace for our webhook
```

#### Step 2: Create the TLS Secret

Webhooks communicate with the API server over HTTPS. A TLS secret is required:

```bash
kubectl -n webhook-demo create secret tls webhook-server-tls \
  --cert "/root/keys/webhook-server-tls.crt" \
  --key "/root/keys/webhook-server-tls.key"
```

```
secret/webhook-server-tls created
```

The certificate's Common Name (CN) or Subject Alternative Name (SAN) **must** match the service DNS name: `webhook-server.webhook-demo.svc`. If they don't match, the API server will reject the TLS connection.

**Generating self-signed certificates for testing:**

```bash
# Generate a CA key and certificate
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -days 365 -out ca.crt \
  -subj "/CN=webhook-ca"

# Generate the webhook server key and CSR
openssl genrsa -out tls.key 2048
openssl req -new -key tls.key -out tls.csr \
  -subj "/CN=webhook-server.webhook-demo.svc" \
  -config <(cat <<EOF
[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name
[req_distinguished_name]
[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = webhook-server
DNS.2 = webhook-server.webhook-demo
DNS.3 = webhook-server.webhook-demo.svc
DNS.4 = webhook-server.webhook-demo.svc.cluster.local
EOF
)

# Sign the certificate with the CA
openssl x509 -req -in tls.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out tls.crt -days 365 \
  -extensions v3_req \
  -extfile <(cat <<EOF
[v3_req]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
subjectAltName = DNS:webhook-server,DNS:webhook-server.webhook-demo,DNS:webhook-server.webhook-demo.svc,DNS:webhook-server.webhook-demo.svc.cluster.local
EOF
)

# Get the CA bundle for the webhook configuration
cat ca.crt | base64 | tr -d '\n'
# Use this output as the caBundle value in MutatingWebhookConfiguration
```

#### Step 3: Deploy the Webhook Server and Service

```bash
# Deploy the webhook server (a Go/Python app that handles admission reviews)
kubectl apply -f webhook-deployment.yaml

# Create the service to expose the webhook server
kubectl apply -f webhook-service.yaml
```

**Example webhook-service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: webhook-server
  namespace: webhook-demo
spec:
  selector:
    app: webhook-server          # Must match the Deployment's pod labels
  ports:
  - port: 443                   # The API server connects to port 443
    targetPort: 8443             # Your webhook server listens on 8443
    protocol: TCP
```

#### Step 4: Configure the MutatingWebhookConfiguration

This tells the API server to send pod CREATE requests to your webhook for mutation:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: demo-webhook
webhooks:
- name: webhook-server.webhook-demo.svc
  admissionReviewVersions: ["v1"]
  sideEffects: None
  clientConfig:
    service:
      name: webhook-server           # Service name in the cluster
      namespace: webhook-demo        # Namespace where the service lives
      path: "/mutate"                # HTTP path on the webhook server
    caBundle: LS0tLS1CRUdJTi...      # Base64-encoded CA certificate
  rules:
  - operations: ["CREATE"]           # Only intercept CREATE operations
    apiGroups: [""]                  # Core API group
    apiVersions: ["v1"]
    resources: ["pods"]              # Only pods
  failurePolicy: Fail               # Reject if webhook is unavailable
```

```bash
kubectl apply -f webhook-configuration.yaml
```

#### Step 5: Test the Webhook

**Test 1 — Pod with no security context (gets mutated):**

```yaml
# pod-with-defaults.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-defaults
  labels:
    app: pod-with-defaults
spec:
  restartPolicy: OnFailure
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "echo I am running as user $(id -u)"]
    # No securityContext specified — webhook will add one
```

```bash
kubectl apply -f pod-with-defaults.yaml
```

```
pod/pod-with-defaults created
```

Inspect the pod — the webhook mutated it to add security settings:

```bash
kubectl get pod pod-with-defaults -o yaml | grep -A5 securityContext
```

```yaml
  securityContext:
    runAsNonRoot: true       # <-- Added by the webhook
    runAsUser: 1234          # <-- Added by the webhook
```

The pod runs as user 1234 instead of root, even though the original YAML had no `securityContext`.

**Test 2 — Pod that explicitly allows root (permitted):**

```yaml
# pod-with-override.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-override
  labels:
    app: pod-with-override
spec:
  restartPolicy: OnFailure
  securityContext:
    runAsNonRoot: false      # Explicitly opting into root
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "echo I am running as user $(id -u)"]
```

```bash
kubectl apply -f pod-with-override.yaml
```

```
pod/pod-with-override created
```

The webhook allows this because the user explicitly opted into running as root (`runAsNonRoot: false`).

**Test 3 — Pod with conflicting settings (rejected):**

```yaml
# pod-with-conflict.yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-conflict
  labels:
    app: pod-with-conflict
spec:
  restartPolicy: OnFailure
  securityContext:
    runAsNonRoot: true       # Says "don't run as root"
    runAsUser: 0             # But sets user to root (UID 0) — contradiction!
  containers:
  - name: busybox
    image: busybox
    command: ["sh", "-c", "echo I am running as user $(id -u)"]
```

```bash
kubectl apply -f pod-with-conflict.yaml
```

```
Error from server: error when creating "pod-with-conflict.yaml": admission webhook
"webhook-server.webhook-demo.svc" denied the request: runAsNonRoot specified, but
runAsUser set to 0 (the root user)
```

The webhook validates the request and rejects it — you cannot claim `runAsNonRoot: true` while setting `runAsUser: 0`.

**Summary of webhook behavior:**

| Pod | securityContext | Webhook Action | Result |
|-----|----------------|----------------|--------|
| `pod-with-defaults` | None | **Mutates**: adds `runAsNonRoot: true`, `runAsUser: 1234` | Created (runs as 1234) |
| `pod-with-override` | `runAsNonRoot: false` | **Allows**: explicit opt-in to root | Created (runs as root) |
| `pod-with-conflict` | `runAsNonRoot: true`, `runAsUser: 0` | **Rejects**: contradictory settings | Denied |

### Admission Controllers on Amazon EKS

On EKS, the control plane is managed by AWS — you **cannot** SSH into control plane nodes or edit `/etc/kubernetes/manifests/kube-apiserver.yaml`. This changes how you work with admission controllers.

```
┌──────────────────────────────────────────────────────────────────────┐
│              EKS vs Self-Managed: Admission Controller Access        │
│                                                                      │
│  Self-Managed (kubeadm)              Amazon EKS                      │
│  ─────────────────────               ──────────                      │
│  ✅ Edit API server manifest          ❌ No access to API server      │
│  ✅ Enable/disable any plugin         ❌ Cannot change built-in       │
│  ✅ SSH to control plane              ❌ No SSH to control plane      │
│  ✅ View API server logs directly     ✅ CloudWatch control plane     │
│                                          logs (if enabled)           │
│                                                                      │
│  Both support:                                                       │
│  ✅ MutatingAdmissionWebhook                                         │
│  ✅ ValidatingAdmissionWebhook                                       │
│  ✅ ValidatingAdmissionPolicy (v1.30+)                               │
│  ✅ Pod Security Admission (v1.25+)                                  │
│  ✅ OPA Gatekeeper / Kyverno                                         │
└──────────────────────────────────────────────────────────────────────┘
```

**What EKS enables by default:**

EKS enables the standard set of admission controllers plus some EKS-specific ones. You cannot change this list. The key ones:

| Controller | Status on EKS | Notes |
|---|---|---|
| `NamespaceLifecycle` | ✅ Enabled | Cannot disable |
| `LimitRanger` | ✅ Enabled | Cannot disable |
| `ServiceAccount` | ✅ Enabled | Cannot disable |
| `DefaultStorageClass` | ✅ Enabled | Cannot disable |
| `ResourceQuota` | ✅ Enabled | Cannot disable |
| `MutatingAdmissionWebhook` | ✅ Enabled | Your primary extension point |
| `ValidatingAdmissionWebhook` | ✅ Enabled | Your primary extension point |
| `PodSecurity` | ✅ Enabled (v1.25+) | Configure via namespace labels |
| `NodeRestriction` | ✅ Enabled | Cannot disable |
| `AlwaysPullImages` | ❌ Not enabled | Cannot enable on EKS |

**EKS-specific considerations:**

```bash
# Check which Kubernetes version your EKS cluster runs
aws eks describe-cluster --name my-cluster --query 'cluster.version'
```

```
"1.30"
```

```bash
# Enable control plane logging to see admission controller activity
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
```

```bash
# View admission-related audit logs in CloudWatch
aws logs filter-log-events \
  --log-group-name /aws/eks/my-cluster/cluster \
  --filter-pattern '"admission"' \
  --limit 20
```

**Deploying webhooks on EKS — key differences:**

1. **TLS certificates**: Use AWS Certificate Manager (ACM) or cert-manager for automated certificate management
2. **Service mesh**: If using AWS App Mesh, the Envoy sidecar injector is itself a mutating admission webhook
3. **Fargate profiles**: Pods on Fargate go through an additional AWS-managed mutating webhook that modifies scheduling
4. **VPC CNI**: The VPC CNI plugin uses a mutating webhook to configure pod networking

```bash
# List all webhook configurations in your EKS cluster
kubectl get mutatingwebhookconfigurations
kubectl get validatingwebhookconfigurations
```

```
NAME                                    WEBHOOKS   AGE
vpc-resource-mutating-webhook           1          45d
pod-identity-webhook                    1          45d
aws-load-balancer-webhook               4          30d
```

These are AWS-managed webhooks that EKS installs automatically.

### Pod Security Admission (PSA)

Pod Security Admission replaced the deprecated PodSecurityPolicy (PSP) in Kubernetes v1.25. It is a built-in validating admission controller that enforces Pod Security Standards at the namespace level.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Pod Security Standards                             │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │   Privileged   │  │   Baseline     │  │     Restricted         │  │
│  │                │  │                │  │                        │  │
│  │  No            │  │  Prevents      │  │  Heavily restricted    │  │
│  │  restrictions  │  │  known         │  │  following hardening   │  │
│  │                │  │  privilege     │  │  best practices        │  │
│  │  For: system   │  │  escalations  │  │                        │  │
│  │  components,   │  │                │  │  For: security-        │  │
│  │  infrastructure│  │  For: most     │  │  sensitive workloads   │  │
│  │                │  │  workloads     │  │                        │  │
│  └────────────────┘  └────────────────┘  └────────────────────────┘  │
│                                                                      │
│  Least restrictive ◄──────────────────────► Most restrictive         │
└──────────────────────────────────────────────────────────────────────┘
```

**Three enforcement modes:**

| Mode | Behavior | Use Case |
|---|---|---|
| `enforce` | Rejects pods that violate the policy | Production enforcement |
| `audit` | Allows pods but logs violations in audit log | Migration/testing |
| `warn` | Allows pods but shows warnings to the user | Developer feedback |

**Configuring PSA via namespace labels:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce the "restricted" profile — reject non-compliant pods
    pod-security.kubernetes.io/enforce: restricted
    # Also enforce a specific Kubernetes version's definition of "restricted"
    pod-security.kubernetes.io/enforce-version: v1.30
    # Audit violations against "restricted" (logged but not blocked)
    pod-security.kubernetes.io/audit: restricted
    # Warn users about violations against "restricted"
    pod-security.kubernetes.io/warn: restricted
```

```bash
# Apply the labels to an existing namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted
```

**Testing PSA enforcement:**

```bash
# Try to create a privileged pod in the restricted namespace
kubectl -n production run test --image=nginx --overrides='{
  "spec": {
    "containers": [{
      "name": "test",
      "image": "nginx",
      "securityContext": {"privileged": true}
    }]
  }
}'
```

```
Error from server (Forbidden): pods "test" is forbidden: violates PodSecurity
"restricted:v1.30": privileged (container "test" must not set
securityContext.privileged=true)
```

**A compliant pod for the "restricted" profile:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true               # Required by restricted
    seccompProfile:
      type: RuntimeDefault           # Required by restricted (v1.25+)
  containers:
  - name: app
    image: nginx:1.25
    securityContext:
      allowPrivilegeEscalation: false  # Required by restricted
      capabilities:
        drop: ["ALL"]                  # Required by restricted
      runAsUser: 1000                  # Non-root user
    resources:
      limits:
        memory: "128Mi"
        cpu: "250m"
```

**What each profile restricts:**

| Check | Privileged | Baseline | Restricted |
|---|---|---|---|
| HostNetwork | ✅ Allowed | ❌ Blocked | ❌ Blocked |
| HostPID/HostIPC | ✅ Allowed | ❌ Blocked | ❌ Blocked |
| Privileged containers | ✅ Allowed | ❌ Blocked | ❌ Blocked |
| Capabilities (add) | ✅ Any | Limited set | ❌ Must drop ALL |
| HostPath volumes | ✅ Allowed | ✅ Allowed | ❌ Blocked |
| runAsNonRoot | Not required | Not required | ✅ Required |
| Seccomp profile | Not required | Not required | ✅ Required (RuntimeDefault/Localhost) |
| Privilege escalation | ✅ Allowed | ✅ Allowed | ❌ Must be false |

### ValidatingAdmissionPolicy (CEL-based, v1.30+ GA)

ValidatingAdmissionPolicy is a newer alternative to webhook-based validation. Instead of deploying an external webhook server, you write validation rules directly in the Kubernetes API using Common Expression Language (CEL).

```
┌──────────────────────────────────────────────────────────────────────┐
│         Webhook vs ValidatingAdmissionPolicy                         │
│                                                                      │
│  Webhook Approach:                                                   │
│  API Server ──HTTPS──► External Server ──► Response                  │
│  (network hop, TLS, deployment, scaling, monitoring)                 │
│                                                                      │
│  ValidatingAdmissionPolicy (CEL):                                    │
│  API Server ──► Evaluate CEL expression in-process ──► Result        │
│  (no network hop, no external server, no TLS management)             │
│                                                                      │
│  Trade-offs:                                                         │
│  ✅ CEL: No infrastructure to manage, faster, simpler                │
│  ❌ CEL: Limited to validation only (no mutation)                    │
│  ❌ CEL: Cannot call external services or databases                  │
│  ✅ Webhook: Full programming language, mutation support             │
│  ❌ Webhook: Requires deployment, TLS, monitoring, scaling           │
└──────────────────────────────────────────────────────────────────────┘
```

**Step 1: Define the policy (what to check):**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-resource-limits
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  validations:
  - expression: >
      object.spec.containers.all(c,
        has(c.resources) &&
        has(c.resources.limits) &&
        has(c.resources.limits.memory) &&
        has(c.resources.limits.cpu)
      )
    # CEL expression: checks that ALL containers have both memory and cpu limits
    message: "All containers must have CPU and memory limits set"
    reason: Invalid
```

**Step 2: Bind the policy (where to apply it):**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-resource-limits-binding
spec:
  policyName: require-resource-limits
  # policyName: references the ValidatingAdmissionPolicy above
  validationActions: ["Deny"]
  # validationActions: Deny = reject, Audit = log only, Warn = warn user
  matchResources:
    namespaceSelector:
      matchLabels:
        enforce-limits: "true"
    # Only apply to namespaces with this label
```

**Testing:**

```bash
# Label a namespace to enable the policy
kubectl label namespace default enforce-limits=true

# Try to create a pod without resource limits
kubectl run test --image=nginx
```

```
Error from server: admission webhook denied the request:
All containers must have CPU and memory limits set
```

```bash
# Create a pod WITH resource limits — succeeds
kubectl run test --image=nginx \
  --overrides='{"spec":{"containers":[{"name":"test","image":"nginx","resources":{"limits":{"cpu":"100m","memory":"128Mi"}}}]}}'
```

```
pod/test created
```

**Common CEL expressions for admission policies:**

```yaml
# Require specific image registry
- expression: >
    object.spec.containers.all(c,
      c.image.startsWith("123456789.dkr.ecr.us-east-1.amazonaws.com/")
    )
  message: "All images must come from the company ECR registry"

# Block latest tag
- expression: >
    object.spec.containers.all(c,
      !c.image.endsWith(":latest") && c.image.contains(":")
    )
  message: "Image tag 'latest' is not allowed; use a specific version"

# Require specific labels
- expression: >
    has(object.metadata.labels) &&
    has(object.metadata.labels.team) &&
    has(object.metadata.labels.environment)
  message: "Resources must have 'team' and 'environment' labels"

# Prevent privileged containers
- expression: >
    object.spec.containers.all(c,
      !has(c.securityContext) ||
      !has(c.securityContext.privileged) ||
      c.securityContext.privileged == false
    )
  message: "Privileged containers are not allowed"

# Enforce read-only root filesystem
- expression: >
    object.spec.containers.all(c,
      has(c.securityContext) &&
      has(c.securityContext.readOnlyRootFilesystem) &&
      c.securityContext.readOnlyRootFilesystem == true
    )
  message: "Containers must use a read-only root filesystem"
```

### OPA Gatekeeper & Kyverno (Policy Engines)

Two popular policy engines for Kubernetes admission control:

| Feature | OPA Gatekeeper | Kyverno |
|---|---|---|
| **Policy language** | Rego (custom language) | YAML (native K8s) |
| **Learning curve** | Steep (Rego is complex) | Low (just YAML) |
| **Mutation support** | Yes | Yes |
| **Validation support** | Yes | Yes |
| **Generate resources** | No | Yes (can auto-create resources) |
| **Image verification** | Via external data | Built-in (Cosign, Notary) |
| **Audit existing resources** | Yes | Yes |
| **Best for** | Complex policies, multi-platform (K8s + Terraform + CI) | K8s-native teams, simpler policies |

**OPA Gatekeeper example — require labels:**

```bash
# Install Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml
```

```bash
# Verify installation
kubectl get pods -n gatekeeper-system
```

```
NAME                                            READY   STATUS    RESTARTS   AGE
gatekeeper-audit-7c84869dbf-r2p4n               1/1     Running   0          30s
gatekeeper-controller-manager-ff58b6688-4qhzz   1/1     Running   0          30s
gatekeeper-controller-manager-ff58b6688-7t2xr   1/1     Running   0          30s
gatekeeper-controller-manager-ff58b6688-xvbmj   1/1     Running   0          30s
```

```yaml
# Step 1: Create a ConstraintTemplate (defines the policy logic in Rego)
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredlabels

      # Rego policy: check that all required labels are present
      violation[{"msg": msg}] {
        provided := {label | input.review.object.metadata.labels[label]}
        required := {label | label := input.parameters.labels[_]}
        missing := required - provided
        count(missing) > 0
        msg := sprintf("Missing required labels: %v", [missing])
      }
```

```yaml
# Step 2: Create a Constraint (applies the template with specific parameters)
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["default", "production"]
    # Only enforce in these namespaces
  parameters:
    labels: ["team", "environment"]
    # These labels are required on every pod
```

```bash
# Test: create a pod without required labels
kubectl run test --image=nginx
```

```
Error from server (Forbidden): admission webhook "validation.gatekeeper.sh"
denied the request: [require-team-label] Missing required labels: {"environment", "team"}
```

```bash
# Audit existing violations (resources created before the policy)
kubectl get k8srequiredlabels require-team-label -o yaml | grep -A20 violations
```

**Kyverno example — require labels (YAML-native):**

```bash
# Install Kyverno
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.11.0/install.yaml
```

```yaml
# Kyverno policy — same requirement, pure YAML
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce    # Enforce = reject, Audit = log only
  rules:
  - name: check-team-label
    match:
      any:
      - resources:
          kinds: ["Pod"]
    validate:
      message: "The label 'team' is required"
      pattern:
        metadata:
          labels:
            team: "?*"               # ?* means "any non-empty value"
            environment: "?*"
```

### Admission Controllers Lab Exercises

**Exercise 1: Identify enabled admission controllers**

```bash
# List control plane pods
kubectl get pods -n kube-system

# Check which admission plugins are enabled on the API server
kubectl -n kube-system describe pod kube-apiserver-controlplane | grep admission

# Check all available plugins (from inside the API server pod)
kubectl exec -it kube-apiserver-controlplane -n kube-system -- \
  kube-apiserver -h | grep "enable-admission-plugins"
```

**Exercise 2: Enable NamespaceAutoProvision**

1. Edit `/etc/kubernetes/manifests/kube-apiserver.yaml`
2. Add `NamespaceAutoProvision` to `--enable-admission-plugins`:

```yaml
    - --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
```

3. Wait for the API server to restart, then test:

```bash
kubectl run nginx --image nginx -n blue
```

```
pod/nginx created
```

```bash
kubectl get ns
```

```
NAME              STATUS   AGE
blue              Active   7s
default           Active   50m
kube-node-lease   Active   50m
kube-public       Active   50m
kube-system       Active   50m
```

**Exercise 3: Disable DefaultStorageClass**

Add the disable flag to the API server manifest:

```yaml
    - --enable-admission-plugins=NodeRestriction,NamespaceAutoProvision
    - --disable-admission-plugins=DefaultStorageClass
```

After the API server restarts, PVCs created without a `storageClassName` will no longer get a default StorageClass assigned.

**Exercise 4: Deploy and test a mutating webhook**

Follow the full walkthrough above (Steps 1-5). Verify:
- `pod-with-defaults` gets mutated with `runAsUser: 1234`
- `pod-with-override` is allowed to run as root
- `pod-with-conflict` is rejected with an error

### Troubleshooting Admission Controllers

**Problem 1: API server won't start after editing the manifest**

```bash
# Symptom: kubectl commands fail with connection refused
kubectl get pods
```

```
The connection to the server 10.0.0.1:6443 was refused - did you specify the right host or port?
```

```bash
# Diagnosis: check the API server container logs
crictl ps -a | grep kube-apiserver
# If the container is restarting, check its logs:
crictl logs <container-id>
```

Common causes:
- YAML syntax error in the manifest (wrong indentation, missing dash)
- Invalid plugin name in `--enable-admission-plugins` (case-sensitive)
- Typo in flag name (`--enable-admission-plugin` instead of `--enable-admission-plugins`)

```bash
# Fix: edit the manifest and correct the error
vi /etc/kubernetes/manifests/kube-apiserver.yaml

# Validate YAML syntax before saving
python3 -c "import yaml; yaml.safe_load(open('/etc/kubernetes/manifests/kube-apiserver.yaml'))"
```

**Problem 2: Webhook is rejecting all requests**

```bash
# Symptom: all pod creations fail
kubectl run test --image=nginx
```

```
Error from server (InternalError): Internal error occurred: failed calling webhook
"webhook-server.webhook-demo.svc": Post "https://webhook-server.webhook-demo.svc:443/mutate":
dial tcp 10.96.45.12:443: connect: connection refused
```

```bash
# Diagnosis steps:

# 1. Check if the webhook server pod is running
kubectl get pods -n webhook-demo
# Look for CrashLoopBackOff or ImagePullBackOff

# 2. Check webhook server logs
kubectl logs -n webhook-demo -l app=webhook-server

# 3. Check the webhook service endpoints
kubectl get endpoints -n webhook-demo webhook-server
# If ENDPOINTS is <none>, the service selector doesn't match the pod labels

# 4. Test connectivity from the API server
kubectl run debug --image=curlimages/curl --rm -it -- \
  curl -k https://webhook-server.webhook-demo.svc:443/health
```

```bash
# Quick fix: set failurePolicy to Ignore temporarily
kubectl edit mutatingwebhookconfiguration demo-webhook
# Change failurePolicy: Fail → failurePolicy: Ignore
```

**Problem 3: TLS certificate errors**

```bash
# Symptom:
kubectl run test --image=nginx
```

```
Error from server (InternalError): Internal error occurred: failed calling webhook
"webhook-server.webhook-demo.svc": Post "https://webhook-server.webhook-demo.svc:443/mutate":
x509: certificate signed by unknown authority
```

```bash
# Diagnosis: the caBundle in the webhook configuration doesn't match
# the CA that signed the webhook server's TLS certificate

# 1. Check the current caBundle
kubectl get mutatingwebhookconfiguration demo-webhook -o jsonpath='{.webhooks[0].clientConfig.caBundle}' | base64 -d | openssl x509 -text -noout

# 2. Check the webhook server's certificate
kubectl -n webhook-demo get secret webhook-server-tls -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout

# 3. Verify the CA matches
# The Issuer of the server cert should match the Subject of the CA cert
```

```bash
# Fix: update the caBundle with the correct CA certificate
CA_BUNDLE=$(cat ca.crt | base64 | tr -d '\n')
kubectl patch mutatingwebhookconfiguration demo-webhook \
  --type='json' \
  -p="[{\"op\":\"replace\",\"path\":\"/webhooks/0/clientConfig/caBundle\",\"value\":\"${CA_BUNDLE}\"}]"
```

**Problem 4: Webhook timeout**

```bash
# Symptom:
kubectl run test --image=nginx
```

```
Error from server (InternalError): Internal error occurred: failed calling webhook
"webhook-server.webhook-demo.svc": context deadline exceeded
```

```bash
# Diagnosis: webhook server is too slow to respond

# 1. Check webhook server resource usage
kubectl top pod -n webhook-demo

# 2. Increase the timeout (default is 10 seconds, max is 30)
kubectl patch mutatingwebhookconfiguration demo-webhook \
  --type='json' \
  -p='[{"op":"replace","path":"/webhooks/0/timeoutSeconds","value":30}]'

# 3. Check if the webhook server has enough replicas
kubectl get deployment -n webhook-demo
# Scale up if needed:
kubectl scale deployment webhook-server -n webhook-demo --replicas=3
```

**Problem 5: Webhook blocks kube-system operations**

```bash
# Symptom: system pods can't be created/updated, cluster becomes unstable

# Prevention: always exclude kube-system from webhook rules
# Add namespaceSelector to your webhook configuration:
```

```yaml
webhooks:
- name: webhook-server.webhook-demo.svc
  namespaceSelector:
    matchExpressions:
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system", "kube-public", "kube-node-lease"]
  # This prevents the webhook from intercepting system namespace operations
```

### Production Best Practices

#### Security

| Practice | Why | How |
|---|---|---|
| Use `failurePolicy: Fail` for security webhooks | Prevents bypass when webhook is down | Set in webhook configuration |
| Exclude system namespaces | Prevents breaking cluster operations | Use `namespaceSelector` |
| Rotate TLS certificates | Prevents expiry-related outages | Use cert-manager with auto-renewal |
| Use RBAC to protect webhook configs | Prevents unauthorized modification | Restrict `admissionregistration.k8s.io` access |
| Audit webhook decisions | Track what was allowed/denied | Enable API server audit logging |
| Use `matchPolicy: Equivalent` | Catches requests via alternative API versions | Set in webhook configuration |

```yaml
# cert-manager automated TLS for webhooks
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: webhook-server-cert
  namespace: webhook-system
spec:
  secretName: webhook-server-tls
  dnsNames:
  - webhook-server
  - webhook-server.webhook-system
  - webhook-server.webhook-system.svc
  - webhook-server.webhook-system.svc.cluster.local
  issuerRef:
    name: ca-issuer
    kind: ClusterIssuer
  duration: 8760h        # 1 year
  renewBefore: 720h      # Renew 30 days before expiry
```

#### Scaling & High Availability

```yaml
# Webhook server Deployment with HA configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-server
  namespace: webhook-system
spec:
  replicas: 3                          # Multiple replicas for HA
  selector:
    matchLabels:
      app: webhook-server
  template:
    metadata:
      labels:
        app: webhook-server
    spec:
      topologySpreadConstraints:       # Spread across nodes
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: webhook-server
      containers:
      - name: webhook
        image: company.ecr.aws/webhook-server:v1.2.0
        ports:
        - containerPort: 8443
        resources:
          requests:
            cpu: 100m                  # Guaranteed CPU
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        readinessProbe:                # Only receive traffic when ready
          httpGet:
            path: /health
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:                 # Restart if unhealthy
          httpGet:
            path: /health
            port: 8443
            scheme: HTTPS
          initialDelaySeconds: 15
          periodSeconds: 20
      priorityClassName: system-cluster-critical
      # High priority — don't evict webhook server during resource pressure
```

#### Monitoring & Observability

```bash
# Key metrics to monitor for admission webhooks:

# 1. API server admission webhook latency
# Prometheus metric: apiserver_admission_webhook_admission_duration_seconds
# Alert if p99 > 5 seconds

# 2. API server admission webhook rejection rate
# Prometheus metric: apiserver_admission_webhook_rejection_count
# Alert on sudden spikes

# 3. Webhook server availability
# Monitor the webhook Deployment's available replicas
# Alert if available < desired
```

```yaml
# Prometheus alerting rules for admission webhooks
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: admission-webhook-alerts
spec:
  groups:
  - name: admission-webhooks
    rules:
    - alert: WebhookHighLatency
      expr: |
        histogram_quantile(0.99,
          rate(apiserver_admission_webhook_admission_duration_seconds_bucket[5m])
        ) > 5
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Admission webhook latency is high (p99 > 5s)"

    - alert: WebhookHighRejectionRate
      expr: |
        rate(apiserver_admission_webhook_rejection_count[5m]) > 10
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Admission webhook rejection rate is elevated"

    - alert: WebhookServerDown
      expr: |
        kube_deployment_status_replicas_available{
          deployment="webhook-server",
          namespace="webhook-system"
        } == 0
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "Webhook server has no available replicas"
```

```bash
# On EKS: monitor via CloudWatch
# Enable control plane logging, then query:
aws logs filter-log-events \
  --log-group-name /aws/eks/my-cluster/cluster \
  --filter-pattern '{ $.verb = "create" && $.responseStatus.code >= 400 }' \
  --start-time $(date -d '1 hour ago' +%s000)
```

#### Decision Matrix: Which Admission Approach to Use

```
┌──────────────────────────────────────────────────────────────────────┐
│              Choosing the Right Admission Approach                    │
│                                                                      │
│  Need simple validation only?                                        │
│  ├── Yes ──► Is CEL expressive enough?                               │
│  │           ├── Yes ──► ValidatingAdmissionPolicy (no infra needed) │
│  │           └── No  ──► ValidatingWebhook or Kyverno                │
│  └── No (need mutation) ──► MutatingWebhook or Kyverno               │
│                                                                      │
│  Need to enforce Pod Security Standards?                             │
│  └── Yes ──► Pod Security Admission (built-in, namespace labels)     │
│                                                                      │
│  Need complex, organization-wide policies?                           │
│  ├── Team knows Rego ──► OPA Gatekeeper                              │
│  └── Prefer YAML ──► Kyverno                                        │
│                                                                      │
│  On EKS and can't modify API server flags?                           │
│  └── Use webhooks, PSA, VAP, Gatekeeper, or Kyverno                 │
└──────────────────────────────────────────────────────────────────────┘
```

### Interview Questions

**Q1: What are admission controllers and why are they needed?**

Admission controllers are plugins that intercept API requests after authentication and authorization but before persistence to etcd. They are needed because RBAC only controls who can perform what operations — it cannot inspect or modify the contents of a request. Admission controllers fill this gap by enforcing content-level policies: blocking images from untrusted registries, injecting sidecar containers, enforcing resource limits, and adding default labels. They come in two types — mutating (can modify requests) and validating (can only accept/reject). Mutating controllers run first, then validating controllers.

**Q2: What do admission controllers NOT do?**

Admission controllers do **not** handle user authentication. Authentication (certificates, tokens, OIDC) happens before admission controllers are invoked. The request flow is: Authentication → Authorization (RBAC) → Admission Control → etcd persistence.

**Q3: What is the difference between mutating and validating admission controllers?**

Mutating controllers can modify the incoming request (add labels, inject sidecars, set defaults). Validating controllers can only accept or reject — they cannot change the object. Mutating controllers run first so that validating controllers check the final state. If any controller rejects, the entire request fails.

**Q4: How do you deploy a custom admission webhook?**

1. Write a webhook server (any HTTPS server that handles `AdmissionReview` JSON)
2. Deploy it as a Deployment + ClusterIP Service in the cluster
3. Create a TLS certificate whose SAN matches the service DNS name
4. Create a `MutatingWebhookConfiguration` or `ValidatingWebhookConfiguration` that references the service, specifies the CA bundle, and defines which API operations trigger the webhook

**Q5: What happens if a webhook server is down and `failurePolicy` is set to `Fail`?**

All API requests matching the webhook's rules will be rejected. This is the safer option for security-critical webhooks (prevents bypass), but can cause cluster-wide outages if the webhook intercepts system-critical operations. Always exclude `kube-system` via `namespaceSelector` and run multiple webhook replicas.

**Q6: What is the difference between `failurePolicy: Fail` and `failurePolicy: Ignore`?**

| | `Fail` | `Ignore` |
|---|---|---|
| Webhook unavailable | Request is **rejected** | Request is **allowed** |
| Security | Safer — no bypass possible | Less safe — policies can be bypassed |
| Availability | Risk of blocking all operations | No impact on availability |
| Use case | Security-critical validations | Non-critical mutations (labels, annotations) |

**Q7: How does Pod Security Admission differ from PodSecurityPolicy?**

PodSecurityPolicy (PSP) was removed in Kubernetes v1.25. Pod Security Admission (PSA) replaced it with a simpler model: three predefined profiles (Privileged, Baseline, Restricted) applied via namespace labels. PSA is built into the API server — no CRDs or controllers to install. PSP required creating PSP objects, binding them via RBAC, and managing complex interactions between multiple policies.

**Q8: What is ValidatingAdmissionPolicy and when would you use it over webhooks?**

ValidatingAdmissionPolicy (GA in v1.30) lets you write validation rules using CEL (Common Expression Language) directly in the Kubernetes API. No external webhook server needed. Use it for simple validations (require labels, block latest tag, enforce resource limits). Use webhooks when you need mutation, external service calls, or complex logic that CEL cannot express.

**Q9: How do you handle admission controllers on EKS where you can't modify the API server?**

On EKS, the control plane is managed by AWS. You cannot enable/disable built-in admission controllers. Instead, use: (1) MutatingAdmissionWebhook and ValidatingAdmissionWebhook for custom logic, (2) Pod Security Admission via namespace labels, (3) ValidatingAdmissionPolicy for CEL-based validation, (4) OPA Gatekeeper or Kyverno for policy engines. Enable EKS control plane logging to CloudWatch for audit visibility.

**Q10: What is the `caBundle` field in a webhook configuration?**

The `caBundle` is the base64-encoded CA certificate that signed the webhook server's TLS certificate. The API server uses it to verify the webhook's identity during the TLS handshake. If the `caBundle` doesn't match the CA that signed the server cert, the API server will reject the connection with an `x509: certificate signed by unknown authority` error.

**Q11: How would you prevent a webhook from breaking the cluster?**

1. Exclude system namespaces (`kube-system`, `kube-public`) via `namespaceSelector`
2. Use `objectSelector` to limit which objects trigger the webhook
3. Set appropriate `timeoutSeconds` (default 10, max 30)
4. Run multiple webhook server replicas with `topologySpreadConstraints`
5. Use `failurePolicy: Ignore` for non-critical webhooks
6. Implement health checks (readiness/liveness probes) on the webhook server
7. Monitor webhook latency and rejection rates via Prometheus metrics

**Q12: Explain the AdmissionReview protocol.**

The API server sends an `AdmissionReview` JSON object to the webhook containing: the request UID, the operation type (CREATE/UPDATE/DELETE), the user info, and the full object being submitted. The webhook responds with an `AdmissionReview` containing: the same UID (must match), an `allowed` boolean, an optional status message (for denials), and an optional base64-encoded JSON Patch (for mutations). The webhook must respond over HTTPS.

### Admission Controllers Quick Reference

```bash
# ─── Viewing Admission Controllers ───────────────────────────────────

# View enabled admission plugins (from pod description)
kubectl -n kube-system describe pod kube-apiserver-controlplane | grep admission

# Quick check from the manifest file directly
grep enable-admission-plugins /etc/kubernetes/manifests/kube-apiserver.yaml

# Check all available plugins and their defaults
kube-apiserver -h | grep enable-admission-plugins

# Verify running config from the process
ps -ef | grep kube-apiserver | grep admission

# ─── Enabling / Disabling ────────────────────────────────────────────

# Enable a plugin (edit API server manifest)
# --enable-admission-plugins=NodeRestriction,AlwaysPullImages

# Disable a plugin
# --disable-admission-plugins=DefaultStorageClass

# ─── Webhook Operations ─────────────────────────────────────────────

# List all webhook configurations
kubectl get mutatingwebhookconfigurations
kubectl get validatingwebhookconfigurations

# Describe a specific webhook
kubectl describe mutatingwebhookconfiguration demo-webhook

# Temporarily disable a webhook (emergency)
kubectl delete mutatingwebhookconfiguration demo-webhook

# Check webhook server logs
kubectl logs -n webhook-system -l app=webhook-server --tail=100

# ─── Pod Security Admission ─────────────────────────────────────────

# Apply restricted profile to a namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted

# Check namespace PSA labels
kubectl get namespace production --show-labels

# Dry-run to check if a pod would be admitted
kubectl apply --dry-run=server -f pod.yaml

# ─── ValidatingAdmissionPolicy ──────────────────────────────────────

# List policies
kubectl get validatingadmissionpolicies
kubectl get validatingadmissionpolicybindings

# ─── OPA Gatekeeper ─────────────────────────────────────────────────

# List constraint templates
kubectl get constrainttemplates

# List constraints and their violations
kubectl get constraints

# Audit existing violations
kubectl get k8srequiredlabels -o yaml

# ─── EKS-Specific ───────────────────────────────────────────────────

# Enable control plane logging
aws eks update-cluster-config --name my-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit"],"enabled":true}]}'

# View admission-related audit logs
aws logs filter-log-events \
  --log-group-name /aws/eks/my-cluster/cluster \
  --filter-pattern '"admission"'

# ─── Troubleshooting ────────────────────────────────────────────────

# Check API server container (when kubectl doesn't work)
crictl ps -a | grep kube-apiserver
crictl logs <container-id>

# Validate manifest YAML syntax
python3 -c "import yaml; yaml.safe_load(open('/etc/kubernetes/manifests/kube-apiserver.yaml'))"

# Check webhook service endpoints
kubectl get endpoints -n webhook-system webhook-server

# Test webhook connectivity
kubectl run debug --image=curlimages/curl --rm -it -- \
  curl -k https://webhook-server.webhook-system.svc:443/health
```
---

