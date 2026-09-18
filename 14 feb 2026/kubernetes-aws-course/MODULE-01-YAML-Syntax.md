# MODULE 1: YAML Syntax

---

## 1.1 YAML Syntax Primer

All Kubernetes manifests use YAML. Understanding YAML is essential because every Kubernetes resource is defined in YAML.

### What is YAML?

- **YAML** = "YAML Ain't Markup Language" — it is NOT a markup language (unlike HTML/XML)
- YAML is a data serialization format used to store information (configuration, data structures)
- YAML is very similar to JSON (JavaScript Object Notation) — Kubernetes converts YAML to JSON internally
- YAML focuses on **readability and user friendliness** — designed to be clean and easy to read
- YAML files use two valid extensions: `abc.yml` or `abc.yaml` (both are identical)

### YAML Core Concepts

YAML supports these data types:

| Concept | YAML Term | Description |
|---|---|---|
| **Key-Value Pairs** | Scalars | Simple `key: value` assignments |
| **Dictionary / Map** | Mapping | Set of properties grouped under an item |
| **Array / List** | Sequence | Ordered collection using `-` prefix |
| **Comments** | `#` | Everything after `#` is ignored |
| **Document Separator** | `---` | Separates multiple YAML documents in one file |

### Step 1: Comments & Key-Value Pairs

Space after colon is **mandatory** to differentiate key and value.

```yaml
# This is a comment — ignored by the parser

# Defining simple key value pairs
name: kalyan          # String value
age: 23               # Integer value
city: Hyderabad       # String value
active: true          # Boolean value
score: null           # Null value (or use ~)
```

```
⚠️ Common mistake:
   name:kalyan     ← INVALID (no space after colon)
   name: kalyan    ← VALID
```

### Step 2: Dictionary / Map

A set of properties grouped together after an item. All items under a dictionary must have **equal indentation** (typically 2 spaces).

```yaml
# Dictionary (also called Map or Mapping)
person:
  name: kalyan        # 2 spaces indent — child of "person"
  age: 23             # Same indent level — sibling
  city: Hyderabad     # Same indent level — sibling
```

### Step 3: Array / Lists

Dash (`-`) indicates an element of an array. Two notations are supported:

```yaml
person:               # Dictionary
  name: kalyan
  age: 23
  city: Hyderabad
  hobbies:            # List (block notation)
    - cycling
    - cooking
  hobbies: [cycling, cooking]   # List (inline/flow notation — same result)
```

### Step 4: Multiple Lists (List of Dictionaries)

Each `-` starts a new dictionary in the list:

```yaml
person:               # Dictionary
  name: kalyan
  age: 23
  city: Hyderabad
  hobbies:            # List of strings
    - cycling
    - cooking
  friends:            # List of dictionaries
    - name: friend1   # First dictionary in the list
      age: 22
    - name: friend2   # Second dictionary in the list
      age: 25
```

### Step 5: YAML Spaces & Indentation Rules

```
✅ Use SPACES (2 spaces per level is standard in Kubernetes)
❌ NEVER use TABS (causes parse errors)

Level 0: Top-level keys (no indent)
  Level 1: 2 spaces
    Level 2: 4 spaces
      Level 3: 6 spaces

All siblings must be at the same indent level.
```

### Step 6: Document Separator (`---`)

Separates multiple YAML documents in a single file:

```yaml
# Simple key value pairs
person:               # Dictionary
  name: kalyan
  age: 23
  city: Hyderabad
  hobbies:            # List
    - cooking
    - cycling
  friends:            # Multiple lists
    - name: friend1
      age: 23
    - name: friend2
      age: 22
---                   # YAML Document Separator
apiVersion: v1        # String
kind: Pod             # String
metadata:             # Dictionary
  name: myapp-pod
  labels:             # Dictionary
    app: myapp
    tier: frontend
spec:
  containers:         # List
    - name: myapp
      image: stacksimplify/kubenginx:1.0.0
      ports:          # List of dictionaries
        - containerPort: 80
          protocol: "TCP"
        - containerPort: 81
          protocol: "TCP"
```

Applying a multi-document file creates all resources at once:

```bash
kubectl apply -f file.yml

# Output:
# pod/myapp-pod created
# service/my-service created
```

### YAML Key Rules Summary

| Rule | Example | Note |
|---|---|---|
| Space after colon | `name: kalyan` | Mandatory |
| Indentation | 2 spaces per level | Never use tabs |
| Comments | `# This is a comment` | Ignored by parser |
| Lists | `- item` | Dash + space |
| Inline lists | `[item1, item2]` | Flow notation |
| Document separator | `---` | Multiple docs in one file |
| Strings | `name: kalyan` | Quotes optional unless special chars |
| Booleans | `active: true` | Lowercase true/false |
| Null | `value: null` or `value: ~` | Both work |

**Common YAML errors:**

| Error | Cause | Fix |
|---|---|---|
| `mapping values are not allowed here` | Tab used instead of spaces | Replace tabs with spaces |
| `could not find expected ':'` | Missing space after colon | Add space: `key: value` |
| `did not find expected key` | Inconsistent indentation | Align siblings at same level |
| `found character that cannot start any token` | Tab character in file | Use `cat -A file.yaml` to find tabs (shown as `^I`) |

### Kubernetes YAML Top-Level Objects

Every Kubernetes YAML manifest consists of the same **four top-level fields**:

```yaml
apiVersion:    # Specifies the Kubernetes API version
kind:          # Defines the type of object (Pod, Service, Deployment, etc.)
metadata:      # Contains object details (name, labels, namespace)
spec:          # Specifies the object's configuration (containers, ports, selectors)
```

**Base definition template** — start every manifest from this skeleton:

```yaml
# kube-base-definition.yml
apiVersion: 
kind: 
metadata:
 
spec:

# Types of Kubernetes Objects:
# Pod, ReplicaSet, Deployment, Service, ConfigMap, Secret,
# StatefulSet, DaemonSet, Job, CronJob, Ingress, and many more

# apiVersion: version of the Kubernetes API for this object
# kind:       the type of Kubernetes object to create
# metadata:   name, labels, annotations for the object
# spec:       the actual specification / desired state of the object
```

Kubernetes reads YAML → converts to JSON → stores in etcd. You write YAML for readability, but internally everything is JSON.

#### apiVersion

Defines which API group and version to use. Different resources belong to different API groups.

| Resource | apiVersion | API Group |
|---|---|---|
| Pod | `v1` | core (no group prefix) |
| Service | `v1` | core |
| ConfigMap | `v1` | core |
| Secret | `v1` | core |
| Namespace | `v1` | core |
| Deployment | `apps/v1` | apps |
| StatefulSet | `apps/v1` | apps |
| DaemonSet | `apps/v1` | apps |
| ReplicaSet | `apps/v1` | apps |
| HPA | `autoscaling/v2` | autoscaling |
| Ingress | `networking.k8s.io/v1` | networking |
| NetworkPolicy | `networking.k8s.io/v1` | networking |
| PriorityClass | `scheduling.k8s.io/v1` | scheduling |

Find the correct apiVersion for any resource:

```bash
kubectl api-resources

# Output (truncated):
# NAME          SHORTNAMES   APIVERSION                  NAMESPACED   KIND
# pods          po           v1                          true         Pod
# services      svc          v1                          true         Service
# deployments   deploy       apps/v1                     true         Deployment
```

**Common mistake:** Using the wrong apiVersion causes: `error: no matches for kind "Deployment" in version "v1"`. Deployments use `apps/v1`, not `v1`.

#### kind

The type of Kubernetes object to create. Must match a valid resource type for the given apiVersion.

```yaml
kind: Pod
kind: Service
kind: Deployment
kind: ConfigMap
kind: Secret
kind: Namespace
```

#### metadata

Identity information about the object. The `name` field is required.

```yaml
metadata:
  name: testpod              # Required — unique within the namespace
  namespace: default          # Optional — defaults to "default"
  labels:                     # Optional — key-value pairs for selection
    app: frontend
    env: production
  annotations:                # Optional — non-identifying metadata
    description: "Web frontend pod"
```

| Field | Required | Purpose |
|---|---|---|
| `name` | Yes | Unique identifier within the namespace |
| `namespace` | No | Which namespace (defaults to `default`) |
| `labels` | No | Used by selectors (Services, Deployments, etc.) |
| `annotations` | No | Arbitrary metadata (not used for selection) |

#### spec

The desired state of the object. This is the most important section and is different for every resource type.

```yaml
# Pod spec — defines containers
spec:
  containers:
  - name: c00
    image: ubuntu

# Deployment spec — defines replicas + pod template
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
      - name: web
        image: nginx

# Service spec — defines ports and selector
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

Use `kubectl explain` to see all available fields for any spec:

```bash
kubectl explain pod.spec
kubectl explain deployment.spec
kubectl explain deployment.spec.template.spec.containers
```

### Sample Pod Template with YAML Type Annotations

This template shows every YAML data type in action. The inline comments mark each type so you can see how Kubernetes uses strings, dictionaries, and lists together:

```yaml
# 01-kube-base-definition.yml — Pod with dual ports
apiVersion: v1                        # String
kind: Pod                             # String
metadata:                             # Dictionary
  name: myapp-pod                     # String
  labels:                             # Dictionary
    app: myapp                        # String
spec:                                 # Dictionary
  containers:                         # List
    - name: myapp                     # String
      image: stacksimplify/kubenginx:1.0.0   # String
      ports:                          # List
        - containerPort: 80           # Integer
        - containerPort: 81           # Integer
```

**Type breakdown:**

| YAML Type | Fields in this Pod | Purpose |
|---|---|---|
| String | `apiVersion`, `kind`, `name`, `app`, `image` | Simple scalar values |
| Dictionary (Map) | `metadata`, `labels`, `spec` | Key-value groupings (nested objects) |
| List (Array) | `containers`, `ports` | Ordered collections (items start with `-`) |
| Integer | `containerPort` | Numeric values (no quotes) |

Deploy and verify:

```bash
kubectl apply -f 01-kube-base-definition.yml
kubectl get pod myapp-pod -o wide
kubectl describe pod myapp-pod    # Check both ports under "Ports: 80/TCP, 81/TCP"
```

### Line-by-Line Pod Example

```yaml
kind: Pod                         # Object type: Pod
apiVersion: v1                    # Core API group, version 1
metadata:                         # Identity section
  name: testpod                   # Pod name (must be unique in namespace)
spec:                             # Desired state section
  containers:                     # List of containers (at least one required)
    - name: c00                   # Container name (used in logs/exec -c)
      image: ubuntu               # Image from Docker Hub (or private registry)
      command: ["/bin/bash", "-c", "while true; do echo Hello-Adam; sleep 8; done"]
                                  # Overrides the image's default entrypoint
  restartPolicy: Never            # Do not restart container when it exits
```

**Field details:**

`command` overrides the container image's default entrypoint. Equivalent to Docker's:
```bash
docker run ubuntu /bin/bash -c "while true; do echo Hello-Adam; sleep 8; done"
```

`restartPolicy` controls what happens when a container exits:

| Value | Behavior | Typical Use |
|---|---|---|
| `Always` | Always restart (default) | Long-running services (web servers, APIs) |
| `OnFailure` | Restart only on non-zero exit code | Jobs, batch processing |
| `Never` | Never restart | One-time tasks, debugging |

### Common YAML Patterns in Kubernetes

#### Environment Variables

```yaml
env:
  - name: ORG
    value: WEZVATECH
  - name: SESSION
    value: PODS
```

Verify inside the container:

```bash
kubectl exec <pod-name> -- env

# Output includes:
# ORG=WEZVATECH
# SESSION=PODS
```

#### Container Ports

```yaml
ports:
  - containerPort: 80
```

`containerPort` documents which port the container listens on. It does NOT expose the port outside the cluster — you need a Service for that. However, it is required for Services to route traffic correctly.

#### Resource Requests and Limits

```yaml
resources:
  requests:
    memory: "64Mi"       # Minimum guaranteed — scheduler uses this for placement
    cpu: "100m"          # 100 milliCPU = 0.1 CPU core
  limits:
    memory: "200Mi"      # Maximum allowed — container is OOMKilled if exceeded
    cpu: "200m"          # Maximum CPU — container is throttled if exceeded
```

| Field | What Happens |
|---|---|
| `requests` | Scheduler uses this to find a node with enough capacity. Guaranteed minimum. |
| `limits` | If memory limit exceeded → container is killed (OOMKilled). If CPU limit exceeded → container is throttled (slowed down, not killed). |

**Production tip:** Always set both requests and limits. Without requests, the scheduler cannot make informed placement decisions. Without limits, a single pod can consume all node resources.

#### Labels

```yaml
labels:
  myname: ADAM
  myorg: WEZVATECH
```

Labels are used by selectors to connect objects:

```bash
# Filter pods by label
kubectl get pods -l myname=ADAM

# Services use selectors to find pods
# spec.selector.app: frontend → routes to pods with label app: frontend
```

#### nodeSelector

```yaml
nodeSelector:
  mynode: demonode
```

The pod will only schedule on nodes with the matching label. The node must be labeled first:

```bash
kubectl label nodes <node-name> mynode=demonode
```

### Validating YAML Before Applying

```bash
# Client-side validation (no API server contact)
kubectl apply -f pod.yml --dry-run=client

# Output:
# pod/testpod created (dry run)

# Server-side validation (API server validates but doesn't create)
kubectl apply -f pod.yml --dry-run=server

# Output:
# pod/testpod created (server dry run)
```

Use `--dry-run=client -o yaml` to generate YAML templates:

```bash
kubectl run nginx --image=nginx --dry-run=client -o yaml > pod.yaml
```

### Common YAML Errors

| Error Message | Cause | Fix |
|---|---|---|
| `error converting YAML to JSON` | Wrong indentation (tabs or misaligned spaces) | Use spaces only, check alignment |
| `error: strict decoding error: unknown field` | Typo in field name or field doesn't exist for this resource | Check with `kubectl explain <resource>` |
| `no matches for kind "X" in version "Y"` | Wrong apiVersion for the resource type | Check `kubectl api-resources` for correct version |
| `metadata.name: Required value` | Missing `name` in metadata | Add `name` field |
| `spec.containers: Required value` | Pod spec missing containers list | Add at least one container |

### Internal Flow When Applying YAML

```bash
kubectl apply -f file.yml
```

```
1. kubectl reads the YAML file from disk
2. kubectl converts YAML to JSON
3. kubectl sends a POST request to the API server
4. API server validates the JSON against the resource schema
5. API server checks RBAC permissions
6. If valid, the object is stored in etcd
7. Controllers detect the new object and take action
   (e.g., Scheduler assigns a node, kubelet creates containers)
```

### Production YAML Best Practices

| Practice | Why |
|---|---|
| Always define `resources.requests` and `resources.limits` | Prevents resource starvation and enables proper scheduling |
| Always use `labels` | Required for Services, selectors, and operational filtering |
| Always specify `namespace` | Avoids accidentally deploying to the wrong namespace |
| Never use `latest` image tag | `latest` is mutable — you can't track which version is deployed |
| Use specific image tags (e.g., `nginx:1.25.3`) | Ensures reproducible deployments |
| Use `kubectl apply` (declarative), not `kubectl run` (imperative) | Declarative manifests are version-controlled and reproducible |
| Validate with `--dry-run=client` before applying | Catches syntax errors before they reach the cluster |

---

