# MODULE 4: Kubernetes Architecture

---

## 4.1 Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER                       │
│                                                                 │
│  ┌──────────────────────── CONTROL PLANE ────────────────────┐  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │  │
│  │  │  API Server   │  │  Scheduler   │  │  Controller   │   │  │
│  │  │  (kube-api)   │  │              │  │  Manager      │   │  │
│  │  └──────────────┘  └──────────────┘  └───────────────┘   │  │
│  │                                                           │  │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐   │  │
│  │  │    etcd       │  │  Cloud Controller Manager (AWS) │   │  │
│  │  │  (key-value)  │  │                                  │   │  │
│  │  └──────────────┘  └──────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────── WORKER NODE 1 ──────────┐  ┌── WORKER NODE 2 ─┐ │
│  │                                      │  │                   │ │
│  │  ┌────────┐  ┌────────┐  ┌───────┐  │  │  ┌────────┐      │ │
│  │  │ kubelet│  │kube-   │  │Container│ │  │  │ kubelet│      │ │
│  │  │        │  │proxy   │  │Runtime │  │  │  │        │      │ │
│  │  └────────┘  └────────┘  └───────┘  │  │  └────────┘      │ │
│  │                                      │  │                   │ │
│  │  ┌─── Pod ──┐  ┌─── Pod ──┐         │  │  ┌─── Pod ──┐    │ │
│  │  │Container │  │Container │         │  │  │Container │    │ │
│  │  │Container │  │          │         │  │  │          │    │ │
│  │  └──────────┘  └──────────┘         │  │  └──────────┘    │ │
│  └──────────────────────────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Ship analogy:** Think of a Kubernetes cluster as a fleet of ships in a harbor. **Worker nodes** are cargo ships that carry containers (your applications). The **master node (control plane)** is the control ship that monitors and manages the cargo ships — deciding which cargo goes on which ship, tracking inventory, and replacing ships that break down. The kubelet on each worker node is the ship's captain, and the scheduler is like port cranes loading containers onto the right ships.

### Quick Reference: Component Summary

| Plane | Components |
|---|---|
| **Control Plane** | API Server, etcd, Controller Manager, Scheduler, CoreDNS |
| **Data Plane (Worker)** | kubelet, kube-proxy, Container Runtime (Docker/containerd) |

### Architecture Summary Table

| Component Category | Key Components | Description |
|---|---|---|
| **Master Node (Control Plane)** | etcd, Kube Scheduler, Controllers, Kube API Server, Cloud Controller Manager | Centralized control and management of the entire cluster |
| **Worker Node (Data Plane)** | Kubelet, Kube Proxy, Container Runtime | Lifecycle management of containers and network communication between services |

### Control Plane Components

#### 1. API Server (`kube-apiserver`)
The front door to Kubernetes. Every command you run goes through here.

```bash
# When you run any kubectl command, it talks to the API server
kubectl get pods

# You can directly query the API server
kubectl get --raw /api/v1/namespaces/default/pods
```

**What it does:**
- Receives and validates all REST requests (create, read, update, delete)
- Authenticates users and service accounts
- Authorizes requests via RBAC
- Writes state changes to etcd
- Acts as the communication hub — no component talks to another directly; everything goes through the API server

**Internal flow when you run `kubectl get pods`:**

```
kubectl → authenticates via kubeconfig → API Server → reads from etcd → returns response
```

**What happens if API Server goes down:** No new commands can be processed. Existing pods continue running (kubelet manages them locally), but you cannot create, delete, or modify any resources. The cluster is effectively unmanageable.

**Production note:** On EKS, AWS runs the API server in a managed, multi-AZ configuration. On self-managed clusters, you should run multiple API server replicas behind a load balancer.

##### Pod Creation Lifecycle Through the API Server

When you create a pod (via kubectl or a direct API call), the API Server orchestrates the entire process:

```
1. User sends POST request    →  curl -X POST /api/v1/namespaces/default/pods ...
2. API Server authenticates   →  Validates user identity (certificate, token, etc.)
3. API Server authorizes      →  Checks RBAC — does this user have permission?
4. Admission controllers run  →  Mutating/validating webhooks modify or reject the request
5. Pod object created in etcd →  Pod exists but has no node assignment yet
6. Scheduler detects new pod  →  Selects best node based on resources, taints, affinity
7. API Server updates etcd    →  Pod now has a node assignment
8. kubelet on target node     →  Pulls image, starts container, reports status back
```

##### API Server Service Configuration (Manual Setup)

On self-managed clusters, the API server runs as a systemd service with many configuration flags:

```bash
# Download the binary
wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kube-apiserver
```

Example service file (`/etc/systemd/system/kube-apiserver.service`):

```bash
[Service]
ExecStart=/usr/local/bin/kube-apiserver \
  --advertise-address=${INTERNAL_IP} \
  --allow-privileged=true \
  --apiserver-count=3 \
  --authorization-mode=Node,RBAC \
  --bind-address=0.0.0.0 \
  --client-ca-file=/var/lib/kubernetes/ca.pem \
  --enable-admission-plugins=NamespaceLifecycle,NodeRestriction,LimitRanger,ServiceAccount,DefaultStorageClass,ResourceQuota \
  --etcd-cafile=/var/lib/kubernetes/ca.pem \
  --etcd-certfile=/var/lib/kubernetes/kubernetes.pem \
  --etcd-keyfile=/var/lib/kubernetes/kubernetes-key.pem \
  --etcd-servers=https://127.0.0.1:2379 \
  --kubelet-certificate-authority=/var/lib/kubernetes/ca.pem \
  --kubelet-client-certificate=/var/lib/kubernetes/kubernetes.pem \
  --kubelet-client-key=/var/lib/kubernetes/kubernetes-key.pem \
  --service-account-key-file=/var/lib/kubernetes/service-account.pem \
  --service-cluster-ip-range=10.32.0.0/24 \
  --service-node-port-range=30000-32767 \
  --v=2
Restart=on-failure
RestartSec=5
```

Key flags explained:

| Flag | Purpose |
|---|---|
| `--authorization-mode=Node,RBAC` | Enables Node authorization and RBAC |
| `--enable-admission-plugins` | Plugins that intercept requests after auth (mutate/validate) |
| `--etcd-servers` | etcd endpoint(s) the API server connects to |
| `--service-cluster-ip-range` | CIDR range for ClusterIP Services (e.g., `10.32.0.0/24`) |
| `--service-node-port-range` | Port range for NodePort Services (default `30000-32767`) |
| `--client-ca-file` | CA certificate for authenticating client requests |
| `--apiserver-count` | Number of API server instances (for HA) |

##### API Server Pod Manifest (kubeadm Setup)

On kubeadm clusters, the API server runs as a static pod. Its manifest is at `/etc/kubernetes/manifests/kube-apiserver.yaml`:

```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml (excerpt)
spec:
  containers:
  - command:
    - kube-apiserver
    - --authorization-mode=Node,RBAC
    - --advertise-address=172.17.0.32
    - --allow-privileged=true
    - --client-ca-file=/etc/kubernetes/pki/ca.crt
    - --enable-admission-plugins=NodeRestriction
    - --enable-bootstrap-token-auth=true
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    - --etcd-servers=https://127.0.0.1:2379
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    - --service-cluster-ip-range=10.96.0.0/12
    - --service-node-port-range=30000-32767
```

##### Inspecting the API Server

```bash
# kubeadm: View the API server pod
kubectl get pods -n kube-system | grep apiserver

# Output:
# kube-apiserver-master   1/1   Running   0   15m

# View its full configuration
kubectl describe pod kube-apiserver-master -n kube-system

# Non-kubeadm: Check the running process
ps -aux | grep kube-apiserver

# Output:
# root  1994  2.7  5.1 154360 105024 ?  Ssl  06:45  1:25 kube-apiserver
#   --authorization-mode=Node,RBAC --advertise-address=172.17.0.32 ...

# Non-kubeadm: View the systemd service file
cat /etc/systemd/system/kube-apiserver.service
```

#### 2. etcd
A distributed key-value store that holds ALL cluster data — the "brain" of Kubernetes.

```bash
# Check etcd health (on control plane node)
sudo ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Output:
# https://127.0.0.1:2379 is healthy: successfully committed proposal: took = 1.234ms
```

**What it stores (everything):**
- Pod definitions and status
- Deployment specs
- Service configurations
- Secrets and ConfigMaps
- Node registration and status
- RBAC rules
- Namespace definitions

**Internal behavior:** When you run `kubectl apply -f pod.yml`, the pod spec is stored in etcd as a JSON object. Every component reads desired state from etcd and works to make actual state match.

**What happens if etcd is deleted:** The cluster is dead. All state is lost — pod definitions, deployments, secrets, everything. This is why etcd backups are essential in production.

**Production note:** Always run etcd with at least 3 replicas for high availability. On EKS, AWS manages etcd for you. On self-managed clusters, schedule regular etcd snapshots.

**Real-life analogy:** etcd is like the airport's central database — it knows which planes are at which gates, which runways are free, and the schedule for everything.

etcd uses a **quorum mechanism** (Raft consensus) to ensure reliable and consistent data across multiple control plane nodes. In a multi-master setup, a majority of etcd members must agree on a write before it's committed. For example, a 3-node etcd cluster tolerates 1 failure (quorum = 2).

##### Understanding Key-Value Stores

etcd is a **key-value store**, not a relational database. The difference matters:

| Feature | Relational DB (SQL) | Key-Value Store (etcd) |
|---|---|---|
| Data structure | Tables with fixed rows and columns | Independent documents/entries |
| Schema | Rigid — all rows must have same columns | Flexible — each entry can have different fields |
| Query language | SQL | Simple get/put by key |
| Best for | Complex queries, joins, transactions | Fast lookups, configuration data, state storage |

In a relational database, adding a new field means altering the entire table. In a key-value store, each entry is independent:

```json
// Entry 1: Pod definition
{
  "key": "/registry/pods/default/nginx-abc",
  "value": {
    "kind": "Pod",
    "metadata": { "name": "nginx-abc", "namespace": "default" },
    "spec": { "containers": [{ "name": "nginx", "image": "nginx:1.25" }] }
  }
}

// Entry 2: Service definition (different structure, same store)
{
  "key": "/registry/services/default/my-service",
  "value": {
    "kind": "Service",
    "metadata": { "name": "my-service" },
    "spec": { "type": "ClusterIP", "ports": [{ "port": 80 }] }
  }
}
```

Kubernetes stores all objects this way — each resource is a key-value entry in etcd, keyed by `/registry/<resource-type>/<namespace>/<name>`.

##### etcd Installation and Setup

etcd listens on **port 2379** by default. On self-managed clusters (kubeadm), you install etcd directly. On EKS, AWS manages it for you.

```bash
# Download etcd binary
curl -L https://github.com/etcd-io/etcd/releases/download/v3.5.9/etcd-v3.5.9-linux-amd64.tar.gz \
  -o etcd-v3.5.9-linux-amd64.tar.gz

# Extract
tar xzvf etcd-v3.5.9-linux-amd64.tar.gz

# Move binaries to PATH
sudo mv etcd-v3.5.9-linux-amd64/etcd* /usr/local/bin/

# Start etcd (foreground, for testing)
etcd

# Output (key lines):
# listening for peer traffic on http://localhost:2380
# listening for client traffic on http://localhost:2379
# ready to serve client requests
```

##### etcdctl — The etcd CLI Client

`etcdctl` is the command-line tool for interacting with etcd. It supports two API versions with different command syntax.

**Check version:**

```bash
etcdctl version

# Output:
# etcdctl version: 3.5.9
# API version: 3.5
```

**Store and retrieve data (API v3):**

```bash
# Set the API version (v3 is default in modern etcd)
export ETCDCTL_API=3

# Store a key-value pair
etcdctl put greeting "Hello from etcd"

# Output:
# OK

# Retrieve the value
etcdctl get greeting

# Output:
# greeting
# Hello from etcd

# List all keys
etcdctl get "" --prefix --keys-only

# Delete a key
etcdctl del greeting

# Output:
# 1
```

##### API v2 vs v3 — Command Differences

etcd has gone through major API changes. API v3 is the current standard, but older documentation may reference v2 commands.

| Operation | API v2 Command | API v3 Command |
|---|---|---|
| Store a value | `etcdctl set key1 value1` | `etcdctl put key1 value1` |
| Retrieve a value | `etcdctl get key1` | `etcdctl get key1` |
| Delete a key | `etcdctl rm key1` | `etcdctl del key1` |
| List keys | `etcdctl ls /` | `etcdctl get "" --prefix --keys-only` |
| Create directory | `etcdctl mkdir /dir1` | N/A (flat keyspace in v3) |
| Watch for changes | `etcdctl watch key1` | `etcdctl watch key1` |
| Check cluster health | `etcdctl cluster-health` | `etcdctl endpoint health` |
| Check version | `etcdctl --version` | `etcdctl version` |

**Switching between API versions:**

```bash
# Use API v2 (legacy)
ETCDCTL_API=2 etcdctl set mykey myvalue

# Use API v3 (current — recommended)
ETCDCTL_API=3 etcdctl put mykey myvalue

# Set for entire session
export ETCDCTL_API=3
```

> **Important:** In Kubernetes contexts, always use API v3. The `ETCDCTL_API=3` prefix is required when running etcdctl commands against a Kubernetes etcd cluster (as shown in the health check above).

##### etcd Version History

| Version | Date | Key Change |
|---|---|---|
| v0.1 | August 2013 | Initial release |
| v2.0 | February 2015 | Introduced Raft consensus algorithm |
| v3.0 | January 2017 | New API (put/get), flat keyspace, improved performance |
| v3.3+ | 2018 | CNCF incubation (November 2018) |
| v3.5+ | Current | Production standard for Kubernetes |

##### etcd in Kubernetes — Practical Commands

On a kubeadm cluster, etcd runs as a static pod. All etcdctl commands require TLS certificates:

```bash
# List all keys stored by Kubernetes in etcd
sudo ETCDCTL_API=3 etcdctl get "" --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Output (sample — shows Kubernetes registry structure):
# /registry/configmaps/default/kube-root-ca.crt
# /registry/deployments/default/nginx-deployment
# /registry/namespaces/default
# /registry/pods/default/nginx-abc
# /registry/secrets/default/my-secret
# /registry/services/default/kubernetes
# /registry/services/default/my-service

# Backup etcd (snapshot)
sudo ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Output:
# Snapshot saved at /tmp/etcd-backup.db

# Verify the backup
sudo ETCDCTL_API=3 etcdctl snapshot status /tmp/etcd-backup.db --write-table

# Output:
# +----------+----------+------------+------------+
# |   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
# +----------+----------+------------+------------+
# | 3e5e38a1 |    15847 |       1024 |     5.2 MB |
# +----------+----------+------------+------------+

# Restore from backup
sudo ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-restored
```

> **On EKS:** You cannot access etcd directly — AWS manages it. The commands above apply to kubeadm or self-managed clusters only.

##### etcd Deployment Methods

There are two ways to deploy etcd depending on your cluster setup:

| Method | How etcd Runs | When to Use |
|---|---|---|
| **kubeadm** | Static pod in `kube-system` namespace | Most common for learning and test clusters |
| **Manual (from scratch)** | Systemd service on master node | Full control, production self-managed clusters |

**Method 1: kubeadm (etcd as a static pod)**

kubeadm automatically deploys etcd as a pod. You can see it in the kube-system namespace:

```bash
kubectl get pods -n kube-system

# Output (etcd pod highlighted):
# NAMESPACE     NAME                                 READY   STATUS    RESTARTS   AGE
# kube-system   coredns-78fcdf6894-prwl              1/1     Running   0          1h
# kube-system   etcd-master                          1/1     Running   0          1h
# kube-system   kube-apiserver-master                1/1     Running   0          1h
# kube-system   kube-controller-manager-master       1/1     Running   0          1h
# kube-system   kube-scheduler-master                1/1     Running   0          1h
```

To list keys stored in etcd via the pod (without needing local etcdctl):

```bash
kubectl exec etcd-master -n kube-system -- etcdctl get / --prefix --keys-only

# Output (sample — shows Kubernetes registry structure):
# /registry/apiregistration.k8s.io/apiservices/v1
# /registry/apiregistration.k8s.io/apiservices/v1.apps
# /registry/apiregistration.k8s.io/apiservices/v1.authentication.k8s.io
# /registry/apiregistration.k8s.io/apiservices/v1.authorization.k8s.io
# /registry/apiregistration.k8s.io/apiservices/v1.batch
# /registry/apiregistration.k8s.io/apiservices/v1.networking.k8s.io
# /registry/apiregistration.k8s.io/apiservices/v1.rbac.authorization.k8s.io
```

The etcd root directory (`/registry/`) contains subdirectories for every Kubernetes resource type: nodes, pods, deployments, services, secrets, configmaps, etc.

**Method 2: Manual deployment (from scratch)**

When setting up a cluster manually, you download the etcd binary, configure TLS certificates, and run etcd as a systemd service:

```bash
# Download etcd binary
wget -q --https-only \
  "https://github.com/coreos/etcd/releases/download/v3.3.9/etcd-v3.3.9-linux-amd64.tar.gz"

tar xzvf etcd-v3.3.9-linux-amd64.tar.gz
sudo mv etcd-v3.3.9-linux-amd64/etcd* /usr/local/bin/
```

Example systemd service configuration (`/etc/systemd/system/etcd.service`):

```bash
# etcd.service
[Service]
ExecStart=/usr/local/bin/etcd \
  --name ${ETCD_NAME} \
  --cert-file=/etc/etcd/kubernetes.pem \
  --key-file=/etc/etcd/kubernetes-key.pem \
  --peer-cert-file=/etc/etcd/kubernetes.pem \
  --peer-key-file=/etc/etcd/kubernetes-key.pem \
  --trusted-ca-file=/etc/etcd/ca.pem \
  --peer-trusted-ca-file=/etc/etcd/ca.pem \
  --peer-client-cert-auth \
  --client-cert-auth \
  --initial-advertise-peer-urls https://${INTERNAL_IP}:2380 \
  --listen-peer-urls https://${INTERNAL_IP}:2380 \
  --listen-client-urls https://${INTERNAL_IP}:2379,https://127.0.0.1:2379 \
  --advertise-client-urls https://${INTERNAL_IP}:2379 \
  --initial-cluster-token etcd-cluster-0 \
  --initial-cluster controller-0=https://${CONTROLLER0_IP}:2380,controller-1=https://${CONTROLLER1_IP}:2380 \
  --initial-cluster-state new \
  --data-dir=/var/lib/etcd
Restart=on-failure
RestartSec=5
```

Key configuration flags:

| Flag | Purpose |
|---|---|
| `--advertise-client-urls` | URL the API server uses to reach etcd (port 2379) |
| `--listen-client-urls` | Addresses etcd listens on for client requests |
| `--listen-peer-urls` | Addresses for peer-to-peer communication (port 2380) |
| `--initial-cluster` | List of all etcd members for cluster bootstrapping |
| `--initial-cluster-token` | Unique token to distinguish this cluster |
| `--cert-file` / `--key-file` | TLS certificates for client communication |
| `--peer-cert-file` / `--peer-key-file` | TLS certificates for peer communication |
| `--data-dir` | Where etcd stores its data on disk |

##### etcd High Availability (HA) Configuration

In production, run multiple etcd instances across master nodes. Each instance must know about its peers via `--initial-cluster`:

```bash
# 3-node HA etcd cluster configuration
ExecStart=/usr/local/bin/etcd \
  --name ${ETCD_NAME} \
  --cert-file=/etc/etcd/kubernetes.pem \
  --key-file=/etc/etcd/kubernetes-key.pem \
  --peer-cert-file=/etc/etcd/kubernetes.pem \
  --peer-key-file=/etc/etcd/kubernetes-key.pem \
  --trusted-ca-file=/etc/etcd/ca.pem \
  --peer-trusted-ca-file=/etc/etcd/ca.pem \
  --peer-client-cert-auth \
  --client-cert-auth \
  --initial-advertise-peer-urls https://${INTERNAL_IP}:2380 \
  --listen-peer-urls https://${INTERNAL_IP}:2380 \
  --advertise-client-urls https://${INTERNAL_IP}:2379 \
  --initial-cluster-token etcd-cluster-0 \
  --initial-cluster master-0=https://10.240.0.10:2380,master-1=https://10.240.0.11:2380,master-2=https://10.240.0.12:2380 \
  --initial-cluster-state new \
  --data-dir=/var/lib/etcd
```

**How etcd writes work:**

Writes in an etcd cluster follow a leader-based replication model:

1. A client sends a write request to any etcd node
2. If the node is a follower, it forwards the request to the leader
3. The leader writes the entry to its log and replicates it to all followers
4. Once a majority (quorum) of nodes acknowledge the write, it is committed
5. The leader responds to the client with success

Reads can be served by any node since all nodes hold the same data.

**Leader election (Raft protocol):**

When an etcd cluster starts, all nodes begin as followers. Each node has a random election timeout. The first node whose timeout expires becomes a candidate, requests votes from peers, and becomes leader if it receives a majority. The leader sends periodic heartbeats to maintain authority. If followers stop receiving heartbeats (leader failure), a new election is triggered automatically.

**Quorum and fault tolerance:**

The quorum is calculated as: `quorum = (N / 2) + 1` (integer division)

| etcd Nodes | Quorum (majority) | Tolerates Failures |
|---|---|---|
| 1 | 1 | 0 |
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

> Always use an **odd number** of etcd nodes. Even numbers (e.g., 4) don't improve fault tolerance over the next lower odd number (3) but add network overhead.

**Why odd numbers matter — network partition scenario:**

If a 6-node cluster splits into two groups of 3, neither group has quorum (which requires 4). The entire cluster becomes read-only. A 5-node cluster splitting into groups of 3 and 2 allows the group of 3 to maintain quorum and continue operating.

#### 3. Scheduler (`kube-scheduler`)
Decides which node a new Pod should run on based on resource requirements, constraints, and policies.

```bash
# See scheduler events
kubectl get events --field-selector reason=Scheduled

# Output:
# LAST SEEN   TYPE     REASON      OBJECT          MESSAGE
# 2m          Normal   Scheduled   pod/nginx-abc   Successfully assigned default/nginx-abc to node-1

# See which node a pod was scheduled to
kubectl get pods -o wide

# Output:
# NAME       READY   STATUS    NODE
# testpod    1/1     Running   worker-node1
```

**What the scheduler checks (in order):**
1. **Filtering** — eliminates nodes that don't meet requirements (CPU, memory, taints, node selectors, affinity rules)
2. **Scoring** — ranks remaining nodes by preference (preferred affinity, resource balance, topology spread)
3. **Binding** — assigns the pod to the highest-scoring node

**What happens if scheduler goes down:** New pods stay in `Pending` state. Existing pods continue running. The scheduler does not manage running pods — it only makes initial placement decisions.

**Common mistake:** Pods stuck in `Pending` with event "0/3 nodes are available" usually means resource requests exceed available capacity, or taints/affinity rules are too restrictive.

**Real-life analogy:** Like an airport scheduler assigning gates to incoming flights based on gate availability and aircraft size.

##### Scoring Details

During the ranking phase, the scheduler uses a priority function to score candidate nodes on a scale of **0 to 10**. The node with the highest score wins. For example, if a pod requests 10 CPUs:

```
Node A: 12 CPUs total, 10 requested → 2 CPUs free after placement → Score: 2
Node B: 16 CPUs total, 10 requested → 6 CPUs free after placement → Score: 6
                                                                      ↑ Winner
```

The scheduler considers multiple scoring factors: resource balance, preferred affinity, topology spread, and inter-pod affinity. You can also write a **custom scheduler** if the default doesn't meet your needs — Kubernetes supports running multiple schedulers simultaneously.

##### Scheduler Installation and Configuration

**Download the binary (manual setup):**

```bash
wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kube-scheduler
```

**Systemd service configuration** (`/etc/systemd/system/kube-scheduler.service`):

```bash
[Service]
ExecStart=/usr/local/bin/kube-scheduler \
  --config=/etc/kubernetes/config/kube-scheduler.yaml \
  --v=2
Restart=on-failure
RestartSec=5
```

**kubeadm setup** — the scheduler runs as a static pod. View its manifest:

```bash
cat /etc/kubernetes/manifests/kube-scheduler.yaml
```

##### Inspecting the Scheduler

```bash
# kubeadm: View the scheduler pod
kubectl get pods -n kube-system | grep scheduler

# Output:
# kube-scheduler-master   1/1   Running   0   15m

# Verify the running process on the master node
ps -aux | grep kube-scheduler

# Output:
# root  2477  0.8  1.6  48524 34044 ?  Ssl  17:31  0:08 kube-scheduler
#   --address=127.0.0.1 --kubeconfig=/etc/kubernetes/scheduler.conf --leader-elect=true
```

The `--leader-elect=true` flag ensures that in a multi-master setup, only one scheduler instance is active at a time. The others remain on standby.

##### High Availability Control Plane

In a multi-master HA setup, control plane components run on multiple nodes with different availability modes:

| Component | HA Mode | Why |
|---|---|---|
| **API Server** | Active-Active | Stateless — all instances can process requests simultaneously. A load balancer (nginx, HAProxy) distributes traffic across them. |
| **Scheduler** | Active-Standby | Only one instance should schedule pods at a time to avoid duplicate scheduling. Leader election ensures this. |
| **Controller Manager** | Active-Standby | Only one instance should run controller loops to avoid duplicate actions (e.g., creating extra pods). Leader election ensures this. |
| **etcd** | Distributed (Raft) | All nodes hold data; writes go through the elected leader. |

**Load balancer for API servers:**

In HA, kubectl and all components must reach the API server through a load balancer rather than pointing to a single master:

```
kubectl / kubelet / kube-proxy
         │
         ▼
   ┌─────────────┐
   │ Load Balancer│  (nginx, HAProxy, cloud LB)
   │  :6443       │
   └──┬──────┬────┘
      │      │
      ▼      ▼
  API Server  API Server
  (master-1)  (master-2)
```

**Leader election parameters:**

```bash
kube-controller-manager \
  --leader-elect=true \
  --leader-elect-lease-duration=15s \    # How long the lock is held
  --leader-elect-renew-deadline=10s \    # How often the leader renews
  --leader-elect-retry-period=2s         # How often standbys check for leadership
```

**What happens when a master node fails:**

- Worker nodes and running pods continue operating normally
- Existing Services, Ingress, and networking rules remain active
- No new pods can be scheduled, no scaling, no rolling updates
- `kubectl` commands fail (if the failed master was the only one or the LB target)
- In HA: the load balancer routes to surviving API servers; standby scheduler/controller manager acquire leadership within seconds

#### 4. Controller Manager (`kube-controller-manager`)
Runs controller loops that watch the cluster state and make changes to move toward the desired state.

**How it works:** Each controller runs a continuous loop: read desired state from etcd → compare with actual state → take action to reconcile. This is the core of Kubernetes' declarative model.

**Example:** You define `replicas: 3` in a Deployment. If one pod crashes, the ReplicaSet controller detects only 2 pods running, and creates a new one to restore the count to 3.

Key controllers:
- **ReplicaSet Controller**: Responsible for maintaining the correct number of pods for every ReplicaSet object in the system
- **Deployment Controller**: Manages rolling updates and rollbacks
- **Node Controller**: Responsible for noticing and responding when nodes go down (marks nodes as `NotReady` after ~40s of no heartbeat)
- **Job Controller**: Manages batch jobs to completion
- **Endpoints Controller**: Populates the Endpoints object — joins Services and Pods so traffic can be routed
- **ServiceAccount & Token Controller**: Creates default accounts and API access tokens for new namespaces

```bash
# See controller manager status
kubectl get componentstatuses

# Output (deprecated but illustrative):
# NAME                 STATUS    MESSAGE             ERROR
# controller-manager   Healthy   ok
# scheduler            Healthy   ok
# etcd-0               Healthy   {"health":"true"}
```

**What happens if controller manager goes down:** No self-healing. If a pod crashes, no replacement is created. Deployments won't scale. Node failures won't be detected. Existing pods continue running but the cluster loses its ability to maintain desired state.

All controllers are bundled into a **single process** — the `kube-controller-manager`. When you start it, every controller starts together.

##### Node Controller — Detailed Timings

The Node Controller monitors node health through the API Server with specific timing parameters:

| Parameter | Value | Description |
|---|---|---|
| **Node Monitor Period** | 5 seconds | How often the controller checks node status |
| **Node Monitor Grace Period** | 40 seconds | Time to wait before marking a node as `NotReady` |
| **Pod Eviction Timeout** | 5 minutes | Time to wait before evicting pods from an unreachable node |

```bash
# Node is healthy
kubectl get nodes
# NAME       STATUS   ROLES    AGE   VERSION
# worker-1   Ready    <none>   8d    v1.13.0
# worker-2   Ready    <none>   8d    v1.13.0

# After worker-2 stops sending heartbeats (40s grace period passes):
kubectl get nodes
# NAME       STATUS     ROLES    AGE   VERSION
# worker-1   Ready      <none>   8d    v1.13.0
# worker-2   NotReady   <none>   8d    v1.13.0

# After 5 more minutes: pods on worker-2 are evicted and rescheduled
```

##### Controller Manager Installation and Configuration

**Download the binary (manual setup):**

```bash
wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kube-controller-manager
```

**Systemd service configuration** (`/etc/systemd/system/kube-controller-manager.service`):

```bash
[Service]
ExecStart=/usr/local/bin/kube-controller-manager \
  --address=0.0.0.0 \
  --cluster-cidr=10.200.0.0/16 \
  --cluster-name=kubernetes \
  --cluster-signing-cert-file=/var/lib/kubernetes/ca.pem \
  --cluster-signing-key-file=/var/lib/kubernetes/ca-key.pem \
  --kubeconfig=/var/lib/kubernetes/kube-controller-manager.kubeconfig \
  --leader-elect=true \
  --root-ca-file=/var/lib/kubernetes/ca.pem \
  --service-account-private-key-file=/var/lib/kubernetes/service-account-key.pem \
  --service-cluster-ip-range=10.32.0.0/24 \
  --use-service-account-credentials=true \
  --v=2
Restart=on-failure
RestartSec=5
```

Key flags:

| Flag | Purpose |
|---|---|
| `--leader-elect=true` | In multi-master HA, only one controller manager is active at a time |
| `--cluster-cidr` | CIDR range for pod IPs in the cluster |
| `--service-cluster-ip-range` | CIDR range for Service ClusterIPs |
| `--controllers` | Select which controllers to enable (default: all) |

##### Enabling/Disabling Specific Controllers

The `--controllers` flag lets you selectively enable or disable controllers:

```bash
# Default: all controllers enabled
--controllers=*

# Disable a specific controller
--controllers=*,-tokencleaner

# Enable only specific controllers
--controllers=deployment,replicaset,namespace
```

Full list of available controllers:

```
attachdetach, bootstrapsigner, clusterrole-aggregation, cronjob, csrapproving,
csrcleaner, csrsigning, daemonset, deployment, disruption, endpoint,
garbagecollector, horizontalpodautoscaling, job, namespace, nodeipam,
nodelifecycle, persistentvolume-binder, persistentvolume-expander, podgc,
pv-protection, pvc-protection, replicaset, replicationcontroller,
resourcequota, root-ca-cert-publisher, route, service, serviceaccount,
serviceaccount-token, statefulset, tokencleaner, ttl, ttl-after-finished
```

##### Inspecting the Controller Manager

```bash
# kubeadm: View the controller manager pod
kubectl get pods -n kube-system | grep controller-manager

# Output:
# kube-controller-manager-master   1/1   Running   0   15m

# kubeadm: View the pod manifest
cat /etc/kubernetes/manifests/kube-controller-manager.yaml

# Verify the running process on the master node
ps -aux | grep kube-controller-manager

# Output:
# root  1994  2.7  5.1 154360 105024 ?  Ssl  06:45  1:25 kube-controller-manager
#   --address=127.0.0.1 --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt
#   --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
#   --controllers=*,bootstrapsigner,tokencleaner
#   --kubeconfig=/etc/kubernetes/controller-manager.conf --leader-elect=true
#   --root-ca-file=/etc/kubernetes/pki/ca.crt
#   --service-account-private-key-file=/etc/kubernetes/pki/sa.key
#   --use-service-account-credentials=true
```

#### 5. Cloud Controller Manager (`cloud-controller-manager`)
A control plane component that embeds cloud-specific control logic. It only runs controllers specific to your cloud provider. On-premise Kubernetes clusters will not have this component.

**Sub-controllers:**

| Controller | What It Does |
|---|---|
| **Node Controller** | Checks the cloud provider to determine if a node has been deleted in the cloud after it stops responding |
| **Route Controller** | Sets up routes in the underlying cloud infrastructure (e.g., VPC route tables) |
| **Service Controller** | Creates, updates, and deletes cloud provider load balancers when you create `LoadBalancer` Services |

On AWS EKS, this handles:
- Creating AWS Load Balancers when you create a `LoadBalancer` Service
- Attaching EBS volumes when you create PersistentVolumes
- Managing EC2 node lifecycle (detecting terminated instances)

#### 6. CoreDNS
Provides DNS-based service discovery inside the cluster. Runs as a Deployment in the `kube-system` namespace.

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Output:
# NAME                       READY   STATUS    RESTARTS   AGE
# coredns-5d78c9869d-x1y2z   1/1     Running   0          5d
# coredns-5d78c9869d-a3b4c   1/1     Running   0          5d
```

**What it does:** When a pod needs to reach a Service, it queries CoreDNS. CoreDNS resolves the Service name to its ClusterIP.

```bash
# From inside any pod:
curl myservice.default.svc.cluster.local
# CoreDNS resolves "myservice.default.svc.cluster.local" → 172.20.45.123 (ClusterIP)
```

**DNS name format:** `<service-name>.<namespace>.svc.cluster.local`

**What happens if CoreDNS goes down:** Pods cannot resolve Service names. Direct IP access still works, but DNS-based service discovery fails. This breaks most inter-service communication.

### Worker Node Components

#### 1. kubelet
The "captain of the ship" — an agent running on every worker node. It registers the node with the Kubernetes cluster, ensures containers are running in Pods, and continuously reports status back to the API server.

```bash
# Check kubelet status on a node
systemctl status kubelet

# Output:
# ● kubelet.service - kubelet: The Kubernetes Node Agent
#    Loaded: loaded (/etc/systemd/system/kubelet.service; enabled)
#    Active: active (running) since Mon 2024-01-15 10:00:00 UTC
```

**What it does internally:**
- **Registers the node** with the Kubernetes cluster via the API server
- Receives pod specs from the API server
- Instructs the container runtime to create/start/stop containers
- Reports pod and node status back to the API server
- Runs liveness and readiness probes
- Manages volume mounts and secrets injection

**What happens if kubelet goes down on a node:** Pods on that node continue running (the container runtime keeps them alive), but no new pods can be scheduled there. The node is marked `NotReady` after ~40 seconds. If the node stays down, pods are rescheduled to other nodes (after a configurable timeout, default 5 minutes).

> **Important:** Unlike other control plane components, **kubeadm does not automatically deploy the kubelet**. You must install it manually on each worker node. kubeadm only configures it after installation.

##### Kubelet Installation and Configuration

**Download the binary:**

```bash
wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kubelet
chmod +x kubelet
sudo mv kubelet /usr/local/bin/
```

**Systemd service configuration** (`/etc/systemd/system/kubelet.service`):

```bash
[Service]
ExecStart=/usr/local/bin/kubelet \
  --config=/var/lib/kubelet/kubelet-config.yaml \
  --container-runtime=remote \
  --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock \
  --image-pull-progress-deadline=2m \
  --kubeconfig=/var/lib/kubelet/kubeconfig \
  --network-plugin=cni \
  --register-node=true \
  --v=2
Restart=on-failure
RestartSec=5
```

Key flags:

| Flag | Purpose |
|---|---|
| `--config` | Path to kubelet configuration file |
| `--container-runtime-endpoint` | Socket for the container runtime (containerd, CRI-O) |
| `--kubeconfig` | Credentials to authenticate with the API server |
| `--register-node=true` | Automatically register this node with the cluster |
| `--network-plugin=cni` | Use CNI for pod networking |

##### Verifying the Kubelet

```bash
# Check the running process
ps -aux | grep kubelet

# Output:
# root  2095  1.8  2.4 960676 98788 ?  Ssl  02:32  0:36 /usr/bin/kubelet
#   --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf
#   --kubeconfig=/etc/kubernetes/kubelet.conf
#   --config=/var/lib/kubelet/config.yaml
#   --container-runtime-endpoint=unix:///var/run/containerd/containerd.sock
#   --network-plugin=cni
```

#### 2. kube-proxy
A lightweight process running on every node that maintains network rules for Service communication. It ensures that traffic sent to a Service's ClusterIP is forwarded to the correct backend pod, regardless of which node the request originates from.

```bash
# Check kube-proxy mode
kubectl get configmap kube-proxy -n kube-system -o yaml | grep mode

# Output:
# mode: "iptables"   (or "ipvs" for better performance)
```

**What it does internally:**
- Watches the API server for Service and Endpoint changes
- Creates iptables rules (or IPVS rules) to route traffic from Service IPs to pod IPs
- Handles load balancing across pod replicas

**How Service IP forwarding works:**

A Service is a virtual entity — it has no container, no process, no network interface. It exists only as an IP address and a set of iptables/IPVS rules. When kube-proxy detects a new Service, it creates forwarding rules on every node:

```
Example:
  Service "db-service" created → ClusterIP: 10.96.0.12
  Backend pod running at      → Pod IP: 10.32.0.15

  kube-proxy creates iptables rule on every node:
    10.96.0.12:3306 → forward to → 10.32.0.15:3306

  Web app on Node 1 calls 10.96.0.12:3306
    → iptables intercepts → redirects to 10.32.0.15:3306 (pod on Node 2)
```

**Modes:**
- `iptables` (default) — uses Linux iptables rules. Works well for small-medium clusters.
- `ipvs` — uses Linux IPVS (IP Virtual Server). Better performance for large clusters (1000+ services).

##### Kube Proxy Installation

**Manual setup:**

```bash
wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kube-proxy
chmod +x kube-proxy
sudo mv kube-proxy /usr/local/bin/
```

**kubeadm setup** — kube-proxy is deployed as a **DaemonSet**, which guarantees one pod runs on every node:

```bash
# Verify kube-proxy DaemonSet
kubectl get daemonset kube-proxy -n kube-system

# Output:
# NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
# kube-proxy   3         3         3       3            3           <none>          25m

# Verify kube-proxy pods (one per node)
kubectl get pods -n kube-system -l k8s-app=kube-proxy

# Output:
# NAME               READY   STATUS    RESTARTS   AGE
# kube-proxy-abc12   1/1     Running   0          25m
# kube-proxy-def34   1/1     Running   0          25m
# kube-proxy-ghi56   1/1     Running   0          25m
```

#### 3. Container Runtime
The software that actually runs containers. It receives instructions from kubelet via the Container Runtime Interface (CRI).

Common options:
- **containerd** (default in EKS and most modern clusters)
- **CRI-O** (used in OpenShift)

**Docker is deprecated** as a container runtime in Kubernetes v1.24+. Docker images still work — only the Docker daemon as a runtime is removed. containerd (which Docker used internally) is now used directly.

```bash
# Check container runtime on a node
kubectl get nodes -o wide

# Output:
# NAME          STATUS   ROLES    AGE   VERSION   INTERNAL-IP   OS-IMAGE         KERNEL-VERSION   CONTAINER-RUNTIME
# ip-10-0-1-5   Ready    <none>   5d    v1.28.2   10.0.1.5      Amazon Linux 2   5.10.192         containerd://1.6.25
```

### End-to-End Flow: What Happens When You Apply a Deployment

```bash
kubectl apply -f deploy.yml
```

Step-by-step internal flow:

```
1. kubectl        → Sends request to API Server (authenticated via kubeconfig)
2. API Server     → Validates the manifest, checks RBAC permissions
3. API Server     → Writes the Deployment spec to etcd
4. Controller     → Deployment controller detects new Deployment, creates ReplicaSet
5. Controller     → ReplicaSet controller detects desired replicas, creates Pod objects
6. Scheduler      → Detects unscheduled Pods, evaluates nodes (resources, taints, affinity)
7. Scheduler      → Assigns each Pod to a node, writes binding to etcd
8. kubelet        → On assigned node, detects new Pod, pulls image via container runtime
9. kubelet        → Starts containers, sets up volumes, injects secrets/configmaps
10. kube-proxy    → Updates iptables/IPVS rules for any associated Services
11. kubelet       → Reports Pod status (Running) back to API Server → stored in etcd
```

### Verifying Cluster Health

```bash
# Check all control plane components
kubectl get componentstatuses

# Output:
# NAME                 STATUS    MESSAGE             ERROR
# scheduler            Healthy   ok
# controller-manager   Healthy   ok
# etcd-0               Healthy   {"health":"true"}

# Check node status
kubectl get nodes

# Check system pods
kubectl get pods -n kube-system
```

### Architecture Interview Questions

| Question | Key Points |
|---|---|
| What happens when you run `kubectl apply`? | kubectl → API Server → etcd → Controller → Scheduler → kubelet → container runtime |
| What if etcd goes down? | Cluster loses all state. No new operations possible. Existing pods keep running but cannot be managed. |
| What if the API Server goes down? | No commands can be processed. Existing pods continue running. Cluster is unmanageable. |
| How does the scheduler decide which node? | Filtering (eliminate unfit nodes) → Scoring (rank remaining) → Binding (assign to best) |
| Difference between controller and scheduler? | Controller maintains desired state (replicas, health). Scheduler only makes initial pod placement decisions. |
| Why is CoreDNS required? | Provides service discovery. Pods use DNS names like `myservice.default.svc.cluster.local` instead of tracking changing pod IPs. |
| What happens when you delete a pod managed by a Deployment? | Controller detects actual < desired replicas, creates a replacement pod. Scheduler assigns it to a node. |
| Why was Docker deprecated? | Kubernetes only needs a CRI-compliant runtime. Docker added unnecessary overhead. containerd (Docker's internal runtime) is used directly. |

### kube-system Namespace — What's Running Inside

`kubectl get all -n kube-system` shows all system components. Here's a typical EKS output and what each line means:

```bash
kubectl get all -n kube-system
```

**Sample output:**

```
NAME                                          READY   STATUS    RESTARTS      AGE
pod/aws-node-abcde                            1/1     Running   0             25m
pod/coredns-5644d7b6d9-xyz12                  1/1     Running   0             25m
pod/kube-proxy-mnopl                          1/1     Running   0             25m
pod/ebs-csi-controller-0                      5/5     Running   0             20m

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
service/kube-dns         ClusterIP   10.100.0.10     <none>        53/UDP,53/TCP   25m

NAME                                      DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
daemonset.apps/aws-node                   3         3         3       3            3           <none>          25m
daemonset.apps/kube-proxy                 3         3         3       3            3           <none>          25m

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/coredns                   2/2     2            2           25m
deployment.apps/ebs-csi-controller        1/1     1            1           20m

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/coredns-5644d7b6d9                    2         2         2       25m
replicaset.apps/ebs-csi-controller-6f7d5c8d44         1         1         1       20m
```

**Output breakdown:**

| Prefix | What It Shows |
|---|---|
| `pod/` | Running pods — system components like DNS, proxy, networking |
| `service/` | Services — `kube-dns` provides internal DNS resolution |
| `daemonset.apps/` | DaemonSets — deploy one pod on every node (e.g., `aws-node`, `kube-proxy`) |
| `deployment.apps/` | Deployments — ensure replicas are running (e.g., `coredns`) |
| `replicaset.apps/` | ReplicaSets — managed by Deployments, control pod replicas |

#### Component Deep Dive

**1. CoreDNS** (Deployment + Pods + ReplicaSet + Service)

| Aspect | Detail |
|---|---|
| Managed by | Deployment (usually 2 replicas for HA) |
| Service | `kube-dns` ClusterIP (usually `10.100.0.10:53`) |
| Role | Resolves DNS names like `my-service.my-namespace.svc.cluster.local` to ClusterIPs |
| Why it matters | All service discovery depends on it. If CoreDNS goes down, pods can't find each other by name |

**2. kube-proxy** (DaemonSet + Pods)

| Aspect | Detail |
|---|---|
| Managed by | DaemonSet (1 pod per node) |
| Role | Maintains iptables/IPVS rules for Service routing and load balancing |
| What it does | Routes traffic from Service ClusterIPs to actual pod IPs |

**3. aws-node** (DaemonSet + Pods — EKS specific)

| Aspect | Detail |
|---|---|
| Managed by | DaemonSet (1 pod per worker node) |
| Role | AWS VPC CNI plugin — allocates ENIs and IP addresses to pods |
| What it does | Ensures pods get IPs from your VPC, enabling direct communication with AWS services |

**4. ebs-csi-controller** (Deployment + Pods + ReplicaSet)

| Aspect | Detail |
|---|---|
| Managed by | Deployment |
| Role | AWS EBS CSI driver — handles dynamic volume provisioning |
| What it does | Provisions, attaches, and detaches EBS volumes when PVCs are created |

**5. kube-dns** (Service)

| Aspect | Detail |
|---|---|
| Type | ClusterIP Service |
| ClusterIP | Usually `10.100.0.10` |
| Role | Stable DNS endpoint — all pod DNS queries hit this service, which forwards to CoreDNS pods |

#### Inspecting System Components — describe & logs

```bash
# ── CoreDNS ──
kubectl describe deployment coredns -n kube-system
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl describe pod <coredns-pod-name> -n kube-system
kubectl logs <coredns-pod-name> -n kube-system

# ── kube-proxy ──
kubectl describe daemonset kube-proxy -n kube-system
kubectl get pods -n kube-system -l k8s-app=kube-proxy
kubectl describe pod <kube-proxy-pod-name> -n kube-system
kubectl logs <kube-proxy-pod-name> -n kube-system
# Logs show: iptables/IPVS rule updates, service/endpoint syncing

# ── aws-node (EKS only) ──
kubectl describe daemonset aws-node -n kube-system
kubectl get pods -n kube-system -l k8s-app=aws-node
kubectl describe pod <aws-node-pod-name> -n kube-system
kubectl logs <aws-node-pod-name> -n kube-system
# Logs show: IP allocation, ENI attachment, VPC CNI status, IP exhaustion issues

# ── ebs-csi-controller ──
kubectl describe deployment ebs-csi-controller -n kube-system
kubectl get pods -n kube-system -l app=ebs-csi-controller
kubectl describe pod <ebs-csi-pod-name> -n kube-system
kubectl logs <ebs-csi-pod-name> -n kube-system
# Logs show: volume attach/detach events, EBS provisioning errors

# ── kube-dns service ──
kubectl describe svc kube-dns -n kube-system
# Shows: ClusterIP, ports (53 UDP/TCP), endpoints (CoreDNS pod IPs)
```

**Quick reference — describe & logs for each component:**

| Component | Describe Command | Logs Command |
|---|---|---|
| CoreDNS | `kubectl describe deployment coredns -n kube-system` | `kubectl logs <coredns-pod> -n kube-system` |
| kube-proxy | `kubectl describe daemonset kube-proxy -n kube-system` | `kubectl logs <kube-proxy-pod> -n kube-system` |
| aws-node | `kubectl describe daemonset aws-node -n kube-system` | `kubectl logs <aws-node-pod> -n kube-system` |
| ebs-csi-controller | `kubectl describe deployment ebs-csi-controller -n kube-system` | `kubectl logs <ebs-csi-pod> -n kube-system` |
| kube-dns svc | `kubectl describe svc kube-dns -n kube-system` | N/A (service — logs are from CoreDNS pods) |

---

