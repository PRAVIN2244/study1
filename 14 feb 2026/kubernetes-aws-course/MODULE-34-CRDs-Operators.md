# MODULE 34: Custom Resource Definitions (CRDs) & Operators

---

## 34.1 Custom Resource Definitions (CRDs) & Operators

### How Standard Resources Work

Kubernetes has built-in resources (Deployments, Services, ConfigMaps, etc.) and built-in controllers that manage them. When you create a Deployment, the deployment controller detects it, creates a ReplicaSet, which in turn creates Pods. This is the controller pattern: a loop that watches for changes and reconciles actual state with desired state.

```
┌──────────────────────────────────────────────────────────┐
│  Controller Pattern                                      │
│                                                          │
│  1. WATCH — monitor the API server for resource changes  │
│  2. DETECT — a new/modified/deleted object is found      │
│  3. RECONCILE — take action to match desired state       │
│  4. REPEAT — go back to step 1                           │
└──────────────────────────────────────────────────────────┘
```

CRDs let you define your own resource types. A custom controller watches those resources and acts on them — the same pattern Kubernetes uses internally.

### What Are CRDs?

A Custom Resource Definition (CRD) tells the Kubernetes API server about a new resource type. Once created, you can use `kubectl` to create, get, describe, and delete instances of that type — just like built-in resources.

**What happens without a CRD:**

```bash
kubectl create -f flightticket.yml
# error: no matches for kind "FlightTicket" in version "flights.com/v1"
```

Kubernetes doesn't know what a "FlightTicket" is. You must create the CRD first.

### CRD Structure

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: flighttickets.flights.com    # must be <plural>.<group>
spec:
  group: flights.com                 # API group (like apps, batch, etc.)
  scope: Namespaced                  # Namespaced or Cluster
  names:
    plural: flighttickets            # used in URLs: /apis/flights.com/v1/flighttickets
    singular: flightticket           # used in kubectl output
    kind: FlightTicket               # PascalCase, used in YAML manifests
    shortNames:
    - ft                             # kubectl get ft
  versions:
  - name: v1
    served: true                     # this version is enabled
    storage: true                    # this version is stored in etcd
    schema:
      openAPIV3Schema:               # validation schema
        type: object
        properties:
          spec:
            type: object
            properties:
              from:
                type: string
              to:
                type: string
              number:
                type: integer
                minimum: 1
```

**CRD fields explained:**

| Field | Purpose |
|---|---|
| `metadata.name` | Must be `<plural>.<group>` (e.g., `flighttickets.flights.com`) |
| `spec.group` | API group — appears in `apiVersion` of custom resources |
| `spec.scope` | `Namespaced` (per-namespace) or `Cluster` (cluster-wide) |
| `spec.names.plural` | Used in API URLs and `kubectl get <plural>` |
| `spec.names.singular` | Used in `kubectl` output and help text |
| `spec.names.kind` | The `kind` field in YAML manifests |
| `spec.names.shortNames` | Aliases for `kubectl` (e.g., `kubectl get ft`) |
| `spec.versions[].served` | Whether this version is available via the API |
| `spec.versions[].storage` | Which version is stored in etcd (exactly one must be true) |
| `spec.versions[].schema` | OpenAPI v3 validation schema for the resource |

```bash
# Create the CRD
kubectl create -f flightticket-crd.yaml
# customresourcedefinition.apiextensions.k8s.io/flighttickets.flights.com created

# Verify the CRD exists
kubectl get crd flighttickets.flights.com
# NAME                        CREATED AT
# flighttickets.flights.com   2024-01-15T10:00:00Z

# Verify it appears in api-resources with the short name
kubectl api-resources | grep flight
# NAME             SHORTNAMES   APIVERSION       NAMESPACED   KIND
# flighttickets    ft           flights.com/v1   true         FlightTicket
```

### Creating Custom Resource Instances

Once the CRD exists, you can create instances:

```yaml
# flightticket.yml
apiVersion: flights.com/v1
kind: FlightTicket
metadata:
  name: my-flight-ticket
spec:
  from: Mumbai
  to: London
  number: 2
```

```bash
kubectl create -f flightticket.yml
# flightticket.flights.com/my-flight-ticket created

kubectl get flighttickets
# NAME               AGE
# my-flight-ticket   5s

# Use the short name
kubectl get ft
# NAME               AGE
# my-flight-ticket   10s

kubectl describe ft my-flight-ticket

kubectl delete ft my-flight-ticket
# flightticket.flights.com "my-flight-ticket" deleted
```

At this point, the FlightTicket object is stored in etcd — but nothing happens. No flights are booked. The object is just data. To act on it, you need a **custom controller**.

Once a controller is running and processing FlightTicket events, it can set a status on the resource:

```bash
kubectl get flightticket
# NAME               STATUS
# my-flight-ticket   Pending
```

The `STATUS` column reflects the controller's reconciliation state — `Pending` means the controller has seen the object but hasn't completed the booking yet. The controller updates this to `Booked` or `Failed` after calling the external API.

### Another CRD Example: Database

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com
spec:
  group: example.com
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
                enum: ["postgres", "mysql"]
              version:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 5
              storage:
                type: string
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames:
    - db
```

```bash
kubectl apply -f database-crd.yaml

# Create a Database object
kubectl apply -f - <<EOF
apiVersion: example.com/v1
kind: Database
metadata:
  name: my-postgres
spec:
  engine: postgres
  version: "15"
  replicas: 3
  storage: "100Gi"
EOF

kubectl get databases
kubectl describe database my-postgres
```

### Custom Controllers

A custom controller is a process that watches for changes to your custom resources and takes action. Without it, CRD objects are passive data in etcd.

**Why Go over Python?** You could write a controller in Python, but you'd have to build your own queuing and caching mechanisms, and manage expensive API calls manually. The Kubernetes Go client (`client-go`) provides all of this out of the box:

- **Shared informers** — efficient watch mechanism with local caching (avoids hammering the API server)
- **Work queues** — built-in rate-limited queuing for processing events
- **Typed clients** — compile-time type safety for your custom resources

**Getting started with the sample controller:**

```bash
# Clone the official sample controller
git clone https://github.com/kubernetes/sample-controller.git
# Cloning into 'sample-controller'...
# Resolving deltas: 100% (15787/15787), done.

cd sample-controller

# Customize controller.go with your business logic
# (e.g., call a flight booking API when a FlightTicket is created)

# Build the controller
go build -o sample-controller .
# go: downloading k8s.io/client-go v0.0.0-20211001003700-dbfa30b9d908
# go: downloading golang.org/x/text v0.3.6

# Run the controller (connects to your cluster via kubeconfig)
# The controller authenticates with the API server using the kubeconfig file
./sample-controller -kubeconfig=$HOME/.kube/config
# I1013 02:11:07.489479  40117 controller.go:115] Setting up event handlers
# I1013 02:11:07.489701  40117 controller.go:156] Starting FlightTicket controller
```

**Controller code structure (Go):**

```go
package flightticket

import (
    apps "k8s.io/api/apps/v1"
)

var controllerKind = apps.SchemeGroupVersion.WithKind("FlightTicket")

// Run begins watching and syncing FlightTicket resources.
func (dc *FlightTicketController) Run(workers int, stopCh <-chan struct{}) {
    // 1. Set up informers to watch FlightTicket objects
    // 2. Add event handlers (Add, Update, Delete)
    // 3. Start worker goroutines to process the work queue
    // 4. Block until stopCh is closed
}

// callBookFlightAPI is called when a FlightTicket is created or updated.
func (dc *FlightTicketController) callBookFlightAPI(obj interface{}) {
    // 1. Extract FlightTicket spec (from, to, number)
    // 2. Call external booking API
    // 3. Update FlightTicket status (Booked/Failed)
}
```

**Deploying the controller in-cluster:**

Once verified locally, package the controller as a Docker image and deploy it as a Deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flightticket-controller
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: flightticket-controller
  template:
    metadata:
      labels:
        app: flightticket-controller
    spec:
      serviceAccountName: flightticket-controller
      containers:
      - name: controller
        image: myregistry/flightticket-controller:v1.0
        args:
        - --v=2
```

The controller uses a ServiceAccount with RBAC permissions to watch and update FlightTicket resources.

### The Operator Pattern

An **operator** packages a CRD and its controller into a single deployable unit. When you install an operator, it automatically:

1. Creates the CRD(s)
2. Deploys the controller as a Deployment
3. Sets up RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)

This eliminates the need to deploy CRDs and controllers separately.

For example, deploying the flight operator with a single command:

```bash
# Deploy the flight operator — creates CRD, controller Deployment, and RBAC automatically
kubectl create -f flight-operator.yaml
```

**What operators automate** (tasks that would otherwise require manual admin work):

| Task | Without Operator | With Operator |
|---|---|---|
| Installation | Manual YAML, helm charts | `kubectl create -f operator.yaml` |
| Scaling | Manual replica changes | Controller handles scaling logic |
| Backups | Cron scripts, manual snapshots | Create a Backup CR, operator handles it |
| Restores | Manual etcdctl/pg_restore | Create a Restore CR, operator handles it |
| Upgrades | Manual rolling update steps | Update CR version, operator orchestrates |
| Failure recovery | Manual intervention | Controller detects and self-heals |

**Example: etcd Operator**

The etcd operator manages etcd clusters using three CRDs:

```
┌─────────────────────────────────────────────────────────┐
│  etcd Operator                                          │
│                                                         │
│  CRDs:                    Controllers:                  │
│  ├── EtcdCluster    →     ETCD Controller               │
│  ├── EtcdBackup     →     Backup Operator               │
│  └── EtcdRestore    →     Restore Operator              │
│                                                         │
│  Create an EtcdCluster CR → operator deploys etcd pods  │
│  Create an EtcdBackup CR  → operator takes a snapshot   │
│  Create an EtcdRestore CR → operator restores from snap │
└─────────────────────────────────────────────────────────┘
```

### Discovering and Installing Operators

[OperatorHub.io](https://operatorhub.io/) is the central registry for Kubernetes operators. Popular operators include etcd, MySQL, Prometheus, Grafana, ArgoCD, and Istio.

**Installing an operator using OLM (Operator Lifecycle Manager):**

```bash
# 1. Install the Operator Lifecycle Manager
curl -sL https://github.com/operator-framework/operator-lifecycle-manager/releases/download/v0.19.1/install.sh \
  | bash -s v0.19.1

# 2. Deploy an operator (e.g., etcd)
kubectl create -f https://operatorhub.io/install/etcd.yaml

# 3. Verify the operator is installed
kubectl get csv -n my-etcd
# NAME                  DISPLAY   VERSION   REPLACES   PHASE
# etcdoperator.v0.9.4   etcd      0.9.4                Succeeded

# 4. Now you can create EtcdCluster resources
kubectl apply -f - <<EOF
apiVersion: etcd.database.coreos.com/v1beta2
kind: EtcdCluster
metadata:
  name: my-etcd-cluster
spec:
  size: 3
  version: "3.5.0"
EOF
```

### Popular Operators

| Operator | Purpose |
|---|---|
| **Prometheus Operator** | Manages Prometheus/Alertmanager instances |
| **Cert-Manager** | Automates TLS certificate management |
| **Strimzi** | Manages Apache Kafka clusters |
| **Zalando Postgres Operator** | Manages PostgreSQL clusters |
| **ArgoCD** | GitOps continuous delivery |
| **etcd Operator** | Manages etcd clusters with backup/restore |

### CRD vs Operator — When to Use What

| Scenario | Use |
|---|---|
| Store custom config data, no automation needed | CRD only |
| Need automated actions on custom resources | CRD + custom controller |
| Complex app lifecycle (install, upgrade, backup, restore) | Full operator |
| Using a well-known app (Prometheus, Kafka, etc.) | Install existing operator from OperatorHub |

> **CKA Exam Note:** CRD questions may ask you to create a CRD from a spec, create custom resource instances, or inspect existing CRDs and their objects. Operators are covered at a conceptual level — understand what they are and how CRDs + controllers work together. You won't need to write Go code, but you should know how to `kubectl get crd`, `kubectl get <custom-resource>`, and interpret CRD YAML.

---

