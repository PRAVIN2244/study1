# MODULE 15: Network Policies & Networking Deep Dive

---

## 15.1 Network Policies — Firewall Rules

Network Policies control traffic flow between Pods. By default, all pods can communicate with each other (Kubernetes uses an "all-allow" rule).

### Understanding Ingress and Egress

From any given pod's perspective:

- **Ingress** — incoming traffic TO the pod (someone connecting to it)
- **Egress** — outgoing traffic FROM the pod (it connecting to something else)
- **Response traffic** — automatically allowed in both directions; you don't need separate rules for responses

```
┌──────────────────────────────────────────────────────────┐
│  3-Tier Application Traffic Flow                         │
│                                                          │
│  User → [Web Pod :80] → [API Pod :5000] → [DB Pod :3306]│
│                                                          │
│  Web Pod:                                                │
│    Ingress: port 80 from users                           │
│    Egress:  port 5000 to API pod                         │
│                                                          │
│  API Pod:                                                │
│    Ingress: port 5000 from Web pod                       │
│    Egress:  port 3306 to DB pod                          │
│                                                          │
│  DB Pod:                                                 │
│    Ingress: port 3306 from API pod only                  │
│    Egress:  (none needed unless pushing backups)          │
└──────────────────────────────────────────────────────────┘
```

Without network policies, the Web pod can also reach the DB pod directly — which is a security risk. Network policies let you enforce that only the API pod can talk to the DB.

**Key concepts:**
- Network Policies are namespace-scoped
- They require a CNI plugin that supports them (Calico, Cilium, Weave — NOT Flannel)
- Policies are additive — if any policy allows traffic, it's allowed
- An empty `podSelector: {}` applies to ALL pods in the namespace
- Without any NetworkPolicy, all traffic is allowed (default allow)
- Once ANY NetworkPolicy selects a pod, all traffic not explicitly allowed is denied

**⚠️ CNI enforcement warning:** NetworkPolicies require a CNI plugin that enforces them. If your cluster uses a CNI that doesn't enforce policies (e.g., basic Flannel, kubenet), the NetworkPolicy objects are accepted but have **no effect** — traffic flows freely. Always verify your CNI supports enforcement:

| CNI | Enforces NetworkPolicy? |
|---|---|
| Calico | ✅ Yes |
| Cilium | ✅ Yes (+ L7 policies) |
| Weave Net | ✅ Yes |
| Kube-router | ✅ Yes |
| Romana | ✅ Yes |
| AWS VPC-CNI | ⚠️ Only with Calico addon |
| Flannel | ❌ No |
| Kubenet (AKS) | ❌ No (use Azure NPM or Calico addon) |

### Restrict a Service So Other Namespaces Can't Use It

Services are reachable cluster-wide by default. Even if a Service is in the `finance` namespace, any pod in any namespace can access it via `ledger-svc.finance.svc.cluster.local`. Use NetworkPolicy to block cross-namespace access:

```yaml
# Step 1: Deny all ingress to the ledger app
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-to-ledger
  namespace: finance
spec:
  podSelector:
    matchLabels:
      app: ledger
  policyTypes: ["Ingress"]
  # No ingress rules = deny all incoming traffic
```

```yaml
# Step 2: Allow only pods in the SAME namespace (finance) to access ledger
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: finance
spec:
  podSelector:
    matchLabels:
      app: ledger
  policyTypes: ["Ingress"]
  ingress:
  - from:
    - podSelector: {}        # Empty = all pods in THIS namespace (finance)
    ports:
    - protocol: TCP
      port: 8080
```

```bash
kubectl apply -f deny-all-to-ledger.yaml
kubectl apply -f allow-same-namespace.yaml

# Test: Pod in finance namespace → ledger works
kubectl run test -n finance --image=curlimages/curl --rm -it -- \
  curl -s --max-time 3 http://ledger-svc:8080/health
# Output: {"status":"ok"}

# Test: Pod in default namespace → ledger blocked
kubectl run test --image=curlimages/curl --rm -it -- \
  curl -s --max-time 3 http://ledger-svc.finance:8080/health
# Output: curl: (28) Connection timed out
# DNS resolves successfully (CoreDNS returns the ClusterIP),
# but the NetworkPolicy blocks the actual TCP connection.
# This is the key insight: DNS resolution ≠ network access.
```

**Key insight:** `podSelector: {}` (empty) in an ingress rule means "all pods in the same namespace as the NetworkPolicy." It does NOT mean "all pods in the cluster." This is how you restrict a service to same-namespace access only.

### Pod-to-Pod Restriction

Restrict which pods can communicate with each other within or across namespaces:

```yaml
# Only allow pods with label "role: frontend" to access pods with label "role: backend"
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-restrict
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: backend           # Apply to backend pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend      # Only allow from frontend pods
    ports:
    - protocol: TCP
      port: 8080
```

```bash
# Test: frontend → backend (allowed)
kubectl exec frontend-pod -- curl -s backend-service:8080
# Output: 200 OK

# Test: random-pod → backend (denied)
kubectl exec random-pod -- curl -s --connect-timeout 3 backend-service:8080
# Output: connection timed out
```

### Service-to-Service Restriction (Cross-Namespace)

```yaml
# Allow only the "monitoring" namespace to scrape metrics from "production" namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          purpose: monitoring     # Namespace must have this label
    ports:
    - port: 9090                  # Metrics port only
```

```bash
# Label the monitoring namespace
kubectl label namespace monitoring purpose=monitoring
```

### Egress Restriction (Outbound Traffic)

```yaml
# Pods can only connect to the database service, nothing else
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-egress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - port: 5432
  - to:                           # Allow DNS resolution
    ports:
    - port: 53
      protocol: UDP
    - port: 53
      protocol: TCP
```

**Important:** Always allow DNS (port 53) in egress policies, otherwise pods cannot resolve Service names.

### Selector Logic: AND vs OR

The way you structure `from` entries in ingress rules determines whether conditions are combined with AND or OR:

```yaml
# OR logic — two separate entries in the "from" array
# Traffic is allowed if it matches EITHER rule
ingress:
- from:
  - podSelector:          # Rule 1: any pod with name=api-pod
      matchLabels:
        name: api-pod
  - ipBlock:              # Rule 2: OR from this IP
      cidr: 192.168.5.10/32

# AND logic — both selectors in the SAME entry
# Traffic must match BOTH conditions
ingress:
- from:
  - podSelector:          # Must be api-pod AND in prod namespace
      matchLabels:
        name: api-pod
    namespaceSelector:
      matchLabels:
        name: prod
```

The difference is subtle but important: separate list items (`- podSelector` and `- ipBlock`) are OR. A single list item with both `podSelector` and `namespaceSelector` is AND.

⚠️ **Using `namespaceSelector` alone (without `podSelector`):** If you specify only a `namespaceSelector` in a `from` entry, **every pod** in the matching namespace is allowed access — not just a specific pod. Always combine with `podSelector` if you need to restrict to specific pods within a namespace.

### ipBlock — Allow Traffic from External IPs

Use `ipBlock` to allow traffic from IP addresses outside the cluster (e.g., backup servers, monitoring systems):

```yaml
ingress:
- from:
  - ipBlock:
      cidr: 192.168.5.10/32    # Single IP (/32 = exact match)
  ports:
  - protocol: TCP
    port: 3306
```

### Real-World Example: Securing a Database Pod

A common pattern: web pods talk to API pods, API pods talk to the database. Only the API pod should reach the database on port 3306. An external backup server at `192.168.5.10` also needs access.

```yaml
# db-policy.yaml — Combined ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:                # AND: must be api-pod in prod namespace
        matchLabels:
          name: api-pod
      namespaceSelector:
        matchLabels:
          name: prod
    - ipBlock:                    # OR: from backup server IP
        cidr: 192.168.5.10/32
    ports:
    - protocol: TCP
      port: 3306
  egress:
  - to:
    - ipBlock:                    # Allow DB to push backups to external server
        cidr: 192.168.5.10/32
    ports:
    - protocol: TCP
      port: 80
```

This policy:
- **Ingress**: Allows traffic to port 3306 from API pods in the prod namespace AND from the backup server IP
- **Egress**: Allows the database pod to send data to the backup server on port 80
- All other ingress and egress traffic to/from the database pod is denied

⚠️ **policyTypes isolation:** A NetworkPolicy only isolates the traffic types listed in `policyTypes`. If you specify `policyTypes: [Ingress]`, only ingress is restricted — egress remains fully open. If you specify `policyTypes: [Ingress, Egress]`, both directions are restricted to only what's explicitly allowed. Traffic types not listed in `policyTypes` are unaffected by the policy.

### Default Deny All (Zero Trust)

```yaml
# deny-all.yaml — Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}          # Applies to ALL pods in namespace
  policyTypes:
  - Ingress                # Block all incoming traffic
```

```yaml
# allow-frontend-to-backend.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend         # Apply to backend pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend    # Only allow traffic from frontend pods
    ports:
    - protocol: TCP
      port: 8080
```

```yaml
# allow-specific-namespace.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring    # Allow from monitoring namespace
    ports:
    - protocol: TCP
      port: 9090              # Prometheus metrics port
```

```bash
kubectl apply -f deny-all.yaml
kubectl apply -f allow-frontend-to-backend.yaml

kubectl get networkpolicies -n production

# Output:
# NAME                        POD-SELECTOR   AGE
# deny-all-ingress            <none>         30s
# allow-frontend-to-backend   app=backend    30s
```

### Industry Example: PCI-DSS Compliant Network

```
┌─────────────────────────────────────────────────────┐
│  Namespace: payment-zone (PCI-DSS)                   │
│                                                      │
│  NetworkPolicy: Only payment-gateway can talk to     │
│  payment-processor. No other namespace allowed.      │
│                                                      │
│  ┌──────────────┐     ┌───────────────────┐          │
│  │ payment-     │────→│ payment-          │          │
│  │ gateway      │     │ processor         │          │
│  └──────────────┘     └───────────────────┘          │
│        ↑                                             │
│        │ (only from api-gateway namespace)            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Lab: Network Policies — Inspecting and Creating

This lab walks through inspecting an environment with existing network policies, testing connectivity, and creating a new egress policy.

**Step 1: Inspect the environment**

```bash
kubectl get pods
# NAME       READY   STATUS    RESTARTS   AGE
# external   1/1     Running   0          2m
# internal   1/1     Running   0          2m
# mysql      1/1     Running   0          2m
# payroll    1/1     Running   0          2m

kubectl get svc
# NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
# db-service         ClusterIP   10.109.89.42    <none>        3306/TCP         2m
# external-service   NodePort    10.108.170.44   <none>        8080:30000/TCP   2m
# internal-service   NodePort    10.98.11.243    <none>        8080:30082/TCP   2m
# payroll-service    NodePort    10.110.165.31   <none>        8080:30083/TCP   2m
```

**Step 2: Check existing network policies**

```bash
kubectl get netpol
# NAME             POD-SELECTOR     AGE
# payroll-policy   name=payroll     3m

kubectl describe netpol payroll-policy
```

```
Name:         payroll-policy
Namespace:    default
Spec:
  PodSelector:     name=payroll
  Allowing ingress traffic:
    To Port: 8080/TCP
    From:
      PodSelector: name=internal
  Not affecting egress traffic
  Policy Types: Ingress
```

This policy allows ingress to the payroll pod on port 8080 only from pods labeled `name=internal`. Egress is unrestricted (not listed in `policyTypes`).

**Step 3: Test connectivity**

```bash
# From internal pod → payroll (allowed by policy)
kubectl exec internal -- curl -s --max-time 3 payroll-service:8080
# Output: success

# From external pod → payroll (blocked — not in the "from" selector)
kubectl exec external -- curl -s --max-time 3 payroll-service:8080
# Output: (timeout — connection blocked)
```

**Step 4: Create an egress policy for the internal pod**

Restrict the internal pod so it can only send traffic to payroll (port 8080) and mysql (port 3306):

```yaml
# internal-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: internal-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      name: internal
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          name: payroll
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector:
        matchLabels:
          name: mysql
    ports:
    - protocol: TCP
      port: 3306
```

```bash
kubectl apply -f internal-policy.yaml
# networkpolicy.networking.k8s.io/internal-policy created

kubectl describe netpol internal-policy
```

```
Name:         internal-policy
Namespace:    default
Spec:
  PodSelector:     name=internal
  Not affecting ingress traffic
  Allowing egress traffic:
    To Port: 8080/TCP
    To:
      PodSelector: name=payroll
    ----------
    To Port: 3306/TCP
    To:
      PodSelector: name=mysql
  Policy Types: Egress
```

The internal pod can now only reach payroll on 8080 and mysql on 3306. All other outbound connections from the internal pod are denied.

### Hands-On: Network Policies with Calico

### CNI (Container Network Interface) — Deep Comparison

CNI is the standard interface between Kubernetes and network plugins. The CNI plugin is responsible for assigning IP addresses to pods and enabling pod-to-pod communication across nodes.

#### CNI Plugin and Configuration Directories

Container runtimes (containerd, CRI-O) look for CNI plugins and configs in two directories:

```bash
# Plugin executables
ls /opt/cni/bin
# bridge  dhcp  flannel  host-local  ipvlan  loopback  macvlan
# portmap  ptp  tuning  vlan  weave-net  weave-ipam

# Configuration files — runtime picks the first file alphabetically
ls /etc/cni/net.d
# 10-bridge.conflist
```

#### CNI Bridge Configuration

A typical bridge config file:

```bash
cat /etc/cni/net.d/10-bridge.conf
```

```json
{
  "cniVersion": "0.2.0",
  "name": "mynet",
  "type": "bridge",
  "bridge": "cni0",
  "isGateway": true,
  "ipMasq": true,
  "ipam": {
    "type": "host-local",
    "subnet": "10.22.0.0/16",
    "routes": [
      { "dst": "0.0.0.0/0" }
    ]
  }
}
```

| Field | Purpose |
|---|---|
| `type: bridge` | Creates a Linux bridge on the node |
| `bridge: cni0` | Name of the bridge interface |
| `isGateway: true` | Bridge gets an IP address, acts as gateway for pods |
| `ipMasq: true` | Enables NAT (IP masquerading) for outbound traffic |
| `ipam.type: host-local` | IP allocation managed locally on each node |
| `ipam.subnet` | Pod IP range for this node |

#### Weave CNI Plugin

Weave deploys an agent (peer) on each node as a DaemonSet. Agents form a peer-to-peer mesh network and maintain a complete topology of all nodes and pods.

**How Weave routes packets:**

```
Pod A (Node 1)                                    Pod B (Node 2)
    │                                                  ▲
    ▼                                                  │
Weave Agent ──── encapsulate ────→ Network ────→ Weave Agent
 (Node 1)        (VXLAN)                          (Node 2)
                                               decapsulate
```

1. Pod A sends a packet to Pod B (on a different node)
2. Weave agent on Node 1 intercepts the packet
3. Agent encapsulates it in a new packet with Node 2's IP as destination
4. Packet travels across the network to Node 2
5. Weave agent on Node 2 decapsulates and delivers to Pod B

This eliminates the need for complex routing table management across hundreds of nodes.

**Deploying Weave:**

```bash
kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
# serviceaccount/weave-net created
# clusterrole.rbac.authorization.k8s.io/weave-net created
# daemonset.extensions/weave-net created

# Verify — one weave-net pod per node
kubectl get pods -n kube-system -l name=weave-net
# NAME              READY   STATUS    RESTARTS   AGE
# weave-net-abc12   2/2     Running   0          5m
# weave-net-def34   2/2     Running   0          5m
# weave-net-ghi56   2/2     Running   0          5m
```

```bash
# Inspect pod routing (Weave assigns the default route)
kubectl exec busybox -- ip route
# default via 10.244.1.1 dev eth0
```

Each pod may be connected to multiple bridges (Docker bridge + Weave bridge). Weave configures the pod's routing table so traffic to other pods goes through the Weave bridge.

**Weave IP Address Management (IPAM):**

By default, Weave allocates pod IPs from the range 10.32.0.0/12 (~1 million IPs). This range is **split equally among all nodes** — each node gets a portion and assigns IPs from its share to pods. This peer-based IPAM avoids a central allocator and prevents duplicate IPs.

To align Weave's range with your cluster's pod CIDR, set the `IPALLOC_RANGE` environment variable in the Weave DaemonSet:

```bash
# Download the manifest to customize it
wget https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml
```

Edit the container spec to add the `IPALLOC_RANGE` env var:

```yaml
containers:
  - name: weave
    env:
      - name: IPALLOC_RANGE
        value: "10.244.0.0/16"    # Must match your cluster's pod CIDR
```

```bash
# Apply the customized manifest
kubectl apply -f weave-daemonset-k8s.yaml
```

Verify the CIDR matches your kube-proxy configuration:

```bash
kubectl describe configmap kube-proxy -n kube-system | grep clusterCIDR
# clusterCIDR: 10.244.0.0/16
```

```
┌──────────────────────────────────────────────────────────────┐
│  What a CNI Plugin Does                                      │
│                                                              │
│  1. Assigns an IP address to each new pod                    │
│  2. Sets up network routes so pods on different nodes can    │
│     communicate                                              │
│  3. Implements NetworkPolicy rules (if supported)            │
│  4. Handles pod-to-external traffic (SNAT/masquerade)        │
│                                                              │
│  Without a CNI plugin → nodes stay NotReady, pods can't      │
│  communicate across nodes                                    │
└──────────────────────────────────────────────────────────────┘
```

**CNI Plugin Comparison:**

| Feature | **AWS VPC-CNI** | **Calico** | **Flannel** | **Cilium** | **Kubenet** |
|---|---|---|---|---|---|
| **IP assignment** | Real VPC IPs from subnet | Virtual IPs (overlay or BGP) | Virtual IPs (VXLAN overlay) | Virtual IPs (overlay or native) | Virtual IPs (bridge + NAT) |
| **Networking mode** | Native (no overlay) | Overlay (VXLAN) or BGP | Overlay (VXLAN) | Overlay or native | Bridge + NAT |
| **Performance** | Best (no encapsulation) | Good (BGP) / OK (VXLAN) | OK (VXLAN overhead) | Best (eBPF) | Basic |
| **NetworkPolicy** | Via Calico addon | Yes (full) | No | Yes (full + L7) | No |
| **Encryption** | No (use Istio) | WireGuard | No | WireGuard | No |
| **Max pods/node** | Limited by ENI/IP count | Unlimited | Unlimited | Unlimited | Unlimited |
| **Platform** | EKS only | Any K8s | Any K8s | Any K8s | AKS (default) |
| **Complexity** | Low (managed) | Medium | Low | Medium-High | Low |
| **Best for** | EKS production | On-prem, multi-cloud | Simple clusters | Advanced security, eBPF | AKS basic |

**AWS VPC-CNI (EKS default):**

```bash
# Each pod gets a real VPC IP address from the node's subnet
# No overlay network — pods communicate directly via VPC routing

kubectl get pods -o wide

# Output:
# NAME        READY   IP           NODE
# web-abc12   1/1     10.0.1.15    ip-10-0-1-100.ec2.internal
# web-def34   1/1     10.0.2.25    ip-10-0-2-200.ec2.internal
#                     ^^^^^^^^^^
#                     Real VPC IPs — routable within the VPC

# Limitation: Each EC2 instance type has a max number of ENIs and IPs
# t3.medium: 3 ENIs × 6 IPs = 17 pods max
# m5.large:  3 ENIs × 10 IPs = 29 pods max

# Check current ENI allocation
kubectl get node ip-10-0-1-100.ec2.internal -o jsonpath='{.status.allocatable.pods}'
# Output: 17

# Enable prefix delegation for more pods per node (110+ pods)
kubectl set env daemonset aws-node -n kube-system ENABLE_PREFIX_DELEGATION=true
```

**Calico (most popular for on-prem and multi-cloud):**

```bash
# Install Calico
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/calico.yaml

# Calico uses virtual IPs in a separate CIDR (e.g., 192.168.0.0/16)
# Pods get IPs like 192.168.1.5, 192.168.2.10 — NOT real VPC IPs

# Calico supports two modes:
# 1. VXLAN overlay (default) — encapsulates packets, works everywhere
# 2. BGP peering — no encapsulation, better performance, requires BGP support

# Check Calico status
kubectl get pods -n calico-system

# Output:
# NAME                                       READY   STATUS    RESTARTS   AGE
# calico-kube-controllers-5b8f4d7c9-abc12    1/1     Running   0          5m
# calico-node-def34                          1/1     Running   0          5m    ← DaemonSet
# calico-node-ghi56                          1/1     Running   0          5m
# calico-typha-jkl78                         1/1     Running   0          5m
```

**Flannel (simplest, but no NetworkPolicy):**

```bash
# Install Flannel
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# Flannel uses VXLAN overlay — simple but no NetworkPolicy support
# If you need NetworkPolicies with Flannel, add Calico as a policy-only addon
```

**Kubenet vs Azure CNI (AKS-specific):**

| Feature | Kubenet (AKS default) | Azure CNI |
|---|---|---|
| **Pod IPs** | From a separate CIDR, NATed to node IP | Real VNet IPs from subnet |
| **Performance** | Lower (NAT overhead) | Higher (no NAT) |
| **IP consumption** | Low (pods share node IP) | High (each pod uses a VNet IP) |
| **Max pods/node** | 110 (default) | 250 |
| **NetworkPolicy** | Calico addon required | Azure NPM or Calico |
| **VNet integration** | Pods not directly reachable from VNet | Pods are first-class VNet citizens |
| **NSG/UDR support** | Limited (NAT complicates routing) | Full (NSGs and UDRs apply directly to pod IPs) |
| **Best for** | Small clusters, IP conservation | Enterprise, VNet integration, NSG/UDR routing |

**Decision guide:** If you need pods to be first-class citizens on the VNet (directly reachable, NSG/UDR rules apply) → Azure CNI. If you need to save IP space and want simpler setup → Kubenet. Plan subnet size carefully with Azure CNI — each pod consumes a VNet IP.

**Interview question: What is a CNI plugin and what are the differences between them?**
CNI (Container Network Interface) is the standard for network plugins in Kubernetes. The CNI plugin assigns IPs to pods and enables cross-node communication. AWS VPC-CNI assigns real VPC IPs (best performance, limited by ENI count). Calico uses virtual IPs with VXLAN or BGP (supports NetworkPolicy, works anywhere). Flannel is simplest but doesn't support NetworkPolicy. Cilium uses eBPF for high performance and L7 policies. Choose based on your platform, performance needs, and NetworkPolicy requirements.

Kubernetes network policies require a CNI plugin that supports them. Calico is a popular choice.

**Setting up a Kind cluster with Calico:**

```yaml
# kind-calico.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30002
    hostPort: 30002
    listenAddress: "0.0.0.0"
    protocol: TCP
- role: worker
- role: worker
networking:
  disableDefaultCNI: true        # Disable default CNI so Calico can be installed
  podSubnet: "192.168.0.0/16"    # Calico's default CIDR
```

```bash
kind create cluster --config=kind-calico.yaml

# Install Calico
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/custom-resources.yaml
kubectl get pods -n calico-system --watch
kubectl get nodes
```

**Deploy demo apps and test policies:**

```bash
# Create demo namespaces and apps
kubectl create -f https://docs.tigera.io/files/00-namespace.yaml
kubectl create -f https://docs.tigera.io/files/01-management-ui.yaml
kubectl create -f https://docs.tigera.io/files/02-backend.yaml
kubectl create -f https://docs.tigera.io/files/03-frontend.yaml
kubectl create -f https://docs.tigera.io/files/04-client.yaml

kubectl get all -n management-ui
kubectl get all -n stars
kubectl get all -n client

# Access the Management UI at http://<node-ip>:30002
# All services can communicate (no policies yet)

# Apply default-deny policies
kubectl create -n stars -f https://docs.tigera.io/files/default-deny.yaml
kubectl create -n client -f https://docs.tigera.io/files/default-deny.yaml

# Allow the UI to access services
kubectl create -f https://docs.tigera.io/files/allow-ui.yaml
kubectl create -f https://docs.tigera.io/files/allow-ui-client.yaml

# Allow frontend → backend traffic
kubectl create -f https://docs.tigera.io/files/backend-policy.yaml

# Allow client → frontend traffic
kubectl create -f https://docs.tigera.io/files/frontend-policy.yaml

# Cleanup
kubectl delete ns client stars management-ui
```

By default, pods can communicate with each other by IP address regardless of namespace. A Service also has a DNS name in the format: `<service-name>.<namespace>.svc.cluster.local`.

---

## 15.2 Endpoints & EndpointSlices

Services use Endpoints to track which Pods are backing them.

```bash
# View endpoints for a service
kubectl get endpoints backend-service

# Output:
# NAME              ENDPOINTS                                AGE
# backend-service   10.0.1.15:8080,10.0.2.25:8080,10.0.3.35:8080   5m

# EndpointSlices (newer, more scalable)
kubectl get endpointslices -l kubernetes.io/service-name=backend-service

# Output:
# NAME                      ADDRESSTYPE   PORTS   ENDPOINTS                        AGE
# backend-service-abc12     IPv4          8080    10.0.1.15,10.0.2.25,10.0.3.35   5m
```

---

## 15.3 Quick Service Reference

Minimal Deployment + Service pattern for quick testing:

```yaml
# deploy-with-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mydeploy
spec:
  replicas: 2
  selector:
    matchLabels:
      name: deployment
  template:
    metadata:
      name: testpod
      labels:
        name: deployment
    spec:
      containers:
      - name: c00
        image: httpd
        ports:
        - containerPort: 80
---
# ClusterIP Service
apiVersion: v1
kind: Service
metadata:
  name: demoservice
spec:
  ports:
  - port: 80
    targetPort: 80
  selector:
    name: deployment
  type: ClusterIP
```

```bash
kubectl apply -f deploy-with-service.yaml

kubectl get svc
kubectl describe svc demoservice

# Write custom content to each pod for testing load balancing
kubectl exec mydeploy-<pod-hash-1> -it -- /bin/bash
  echo "I AM POD1" >> ./htdocs/index.html

# To expose externally, change type to NodePort:
# type: NodePort
# NodePort range: 30000-32767
```

---

## 15.4 Complete Networking Example

```yaml
# Full example: Deploy app with Service and Ingress

# 1. Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
  template:
    metadata:
      labels:
        app: webapp
    spec:
      containers:
      - name: webapp
        image: nginx:1.25
        ports:
        - containerPort: 80
---
# 2. ClusterIP Service
apiVersion: v1
kind: Service
metadata:
  name: webapp-service
spec:
  selector:
    app: webapp
  ports:
  - port: 80
    targetPort: 80
---
# 3. Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: webapp-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
  - host: webapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: webapp-service
            port:
              number: 80
```

```bash
kubectl apply -f complete-example.yaml

# Verify everything
kubectl get deployment,service,ingress

# Output:
# NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
# deployment.apps/webapp   3/3     3            3           2m
#
# NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
# service/webapp-service   ClusterIP   172.20.45.123   <none>        80/TCP    2m
#
# NAME                                CLASS   HOSTS                ADDRESS                                    PORTS   AGE
# ingress.networking.k8s.io/webapp-ingress   alb     webapp.example.com   k8s-default-...elb.amazonaws.com   80      2m
```

---

## 15.5 Common Errors & Troubleshooting

### Error: Service has no endpoints
```bash
# Cause: Selector doesn't match any pod labels
kubectl get endpoints my-service

# Output:
# NAME         ENDPOINTS   AGE
# my-service   <none>      5m    ← No endpoints!

# Fix: Check labels match
kubectl get pods --show-labels
kubectl describe service my-service | grep Selector
# Ensure pod labels match service selector
```

### Error: Connection refused
```bash
# Cause: targetPort doesn't match container port
# Fix: Verify ports
kubectl describe service my-service
kubectl describe pod <pod-name> | grep Port
```

### Error: Pods stuck in ContainerCreating (CNI not installed)

```bash
# Symptom: pods never start, stuck in ContainerCreating
kubectl get pods
# NAME   READY   STATUS              RESTARTS   AGE
# app    0/1     ContainerCreating   0          5m

# Diagnose: describe the pod and check events
kubectl describe pod app
# Events:
#   Warning  FailedCreatePodSandbox  kubelet  Failed to create pod sandbox:
#   ... plugin type="weave-net" failed (add): unable to allocate IP address:
#   ... dial tcp 127.0.0.1:6784: connect: connection refused

# This means no CNI plugin is running (or it crashed)

# Check if CNI pods exist
kubectl get pods -n kube-system | grep -E "weave|calico|flannel|cilium"

# Check node status (nodes stay NotReady without CNI)
kubectl get nodes

# Fix: install a CNI plugin (e.g., Weave, Calico, Flannel)
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml

# Verify CNI pods are running
kubectl get pods -n kube-system -l name=weave-net

# Check CNI pod logs if issues persist
kubectl logs -n kube-system -l name=weave-net
```

### Error: ALB not creating
```bash
# Cause: Missing AWS Load Balancer Controller or IAM permissions
# Fix:
kubectl get deployment -n kube-system aws-load-balancer-controller
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Check for subnet tags:
# Public subnets need: kubernetes.io/role/elb = 1
# Private subnets need: kubernetes.io/role/internal-elb = 1
```

---

## 15.6 Module 4 Exercises

### Exercise 1: Service Types
```bash
# 1. Create a deployment
kubectl create deployment web --image=nginx --replicas=3

# 2. Expose as ClusterIP
kubectl expose deployment web --port=80 --target-port=80 --type=ClusterIP --name=web-clusterip

# 3. Expose as NodePort
kubectl expose deployment web --port=80 --target-port=80 --type=NodePort --name=web-nodeport

# 4. Expose as LoadBalancer
kubectl expose deployment web --port=80 --target-port=80 --type=LoadBalancer --name=web-lb

# 5. Compare all three
kubectl get services

# 6. Test ClusterIP from within cluster
kubectl run test --image=busybox --rm -it -- wget -qO- http://web-clusterip

# 7. Clean up
kubectl delete deployment web
kubectl delete service web-clusterip web-nodeport web-lb
```

### Exercise 2: DNS Resolution
```bash
# 1. Create two namespaces with services
kubectl create namespace frontend
kubectl create namespace backend
kubectl create deployment web --image=nginx -n frontend
kubectl create deployment api --image=nginx -n backend
kubectl expose deployment web --port=80 -n frontend
kubectl expose deployment api --port=80 -n backend

# 2. Test cross-namespace DNS
kubectl run dns-test -n frontend --image=busybox --rm -it -- nslookup api.backend

# 3. Clean up
kubectl delete namespace frontend backend
```

---

**Next Module: Storage, ConfigMaps & Secrets →**
## 15.7 Appendix: Kubernetes Networking Deep Dive

### Cluster Networking Prerequisites

Each node must have at least one network interface with an IP address, a unique hostname, and a unique MAC address (important when cloning VMs).

**Required ports:**

| Port | Component | Direction | Purpose |
|---|---|---|---|
| 6443 | API Server | Inbound to control plane | kubectl, worker nodes, controller-manager, scheduler |
| 10250 | Kubelet | Inbound to all nodes | API server → kubelet communication |
| 10259 | Scheduler | Inbound to control plane | Scheduler health/metrics |
| 10257 | Controller Manager | Inbound to control plane | Controller manager health/metrics |
| 2379 | etcd | Inbound to control plane | etcd client API |
| 2380 | etcd | Inbound to control plane | etcd peer communication (multi-master) |
| 30000-32767 | NodePort Services | Inbound to worker nodes | External access to services |

Configure these in firewalls, security groups (AWS), or NSGs (Azure) before cluster setup.

**Network verification commands:**

```bash
# List network interfaces
ip link

# Show IP addresses
ip addr

# View routing table
ip route

# Check IP forwarding (must be 1 for Kubernetes)
cat /proc/sys/net/ipv4/ip_forward
# 1

# View listening ports
netstat -plnt
# tcp  0  0  0.0.0.0:6443   0.0.0.0:*  LISTEN  kube-apiserver
# tcp  0  0  0.0.0.0:10250  0.0.0.0:*  LISTEN  kubelet
# tcp  0  0  0.0.0.0:2379   0.0.0.0:*  LISTEN  etcd
```

### Prerequisite — Switching, Routing, and Gateways

These Linux networking fundamentals underpin how Kubernetes nodes and pods communicate.

#### Switching — Hosts on the Same Network

Two hosts on the same network (e.g., 192.168.1.0/24) communicate through a switch. Each host needs an interface with an IP on that subnet:

```bash
# List network interfaces
ip link
# eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...

# Assign an IP address to an interface
ip addr add 192.168.1.10/24 dev eth0

# Test connectivity to another host on the same network
ping 192.168.1.11
# Reply from 192.168.1.11: bytes=32 time=4ms TTL=117
```

A switch only enables communication within a single network. To reach hosts on a different network, you need a router.

#### Routing — Communication Between Networks

A router connects two or more networks. It has an IP address in each network it connects (e.g., 192.168.1.1 in the first network, 192.168.2.1 in the second).

```
  Network 192.168.1.0/24              Network 192.168.2.0/24
  ┌──────┐  ┌──────┐                  ┌──────┐  ┌──────┐
  │Host A│  │Host B│                  │Host C│  │Host D│
  │ .10  │  │ .11  │                  │ .10  │  │ .11  │
  └──┬───┘  └──┬───┘                  └──┬───┘  └──┬───┘
     │         │                         │         │
  ───┴─────────┴────┐            ┌───────┴─────────┴───
                    │  ┌──────┐  │
                    ├──│Router│──┤
                       │.1/.1 │
                       └──────┘
```

Each host must know where to send traffic for other networks. This is configured via routes:

```bash
# View the routing table
route
# (or: ip route)

# Add a route: to reach 192.168.2.0/24, go via the router at 192.168.1.1
ip route add 192.168.2.0/24 via 192.168.1.1

# Verify
route
# Destination     Gateway         Genmask         Flags  Iface
# 192.168.2.0     192.168.1.1     255.255.255.0   UG     eth0
```

#### Default Gateway

For internet access or any destination not explicitly in the routing table, configure a default gateway:

```bash
ip route add default via 192.168.2.1

# "default" is equivalent to 0.0.0.0 — matches any destination not in the table
route
# Destination     Gateway         Genmask         Flags  Iface
# default         192.168.2.1     0.0.0.0         UG     eth0
# 192.168.1.0     192.168.2.2     255.255.255.0   UG     eth0
```

If you have multiple routers (e.g., one for internet, one for internal networks), add specific routes for internal networks and use the default route for everything else.

#### Using a Linux Host as a Router

A Linux host with two network interfaces can act as a router between two subnets. For example, Host B has interfaces on both 192.168.1.0/24 and 192.168.2.0/24:

```bash
# On Host A (192.168.1.5): route to the other network via Host B
ip route add 192.168.2.0/24 via 192.168.1.6

# On Host C (192.168.2.5): route back via Host B
ip route add 192.168.1.0/24 via 192.168.2.6
```

By default, Linux does not forward packets between interfaces (security measure). You must enable IP forwarding:

```bash
# Check current setting (0 = disabled)
cat /proc/sys/net/ipv4/ip_forward
# 0

# Enable temporarily
echo 1 > /proc/sys/net/ipv4/ip_forward

# Enable permanently (survives reboot)
# Add to /etc/sysctl.conf:
#   net.ipv4.ip_forward = 1
```

This is why Kubernetes nodes require `ip_forward = 1` — nodes must forward pod traffic between interfaces.

#### Key Linux Networking Commands

| Operation | Command |
|---|---|
| List interfaces | `ip link` |
| View IP addresses | `ip addr` |
| Assign an IP | `ip addr add 192.168.1.10/24 dev eth0` |
| View routing table | `ip route` (or `route`) |
| Add a route | `ip route add 192.168.1.0/24 via 192.168.2.1` |
| Set default gateway | `ip route add default via 192.168.2.1` |
| Check IP forwarding | `cat /proc/sys/net/ipv4/ip_forward` |
| Enable IP forwarding | `echo 1 > /proc/sys/net/ipv4/ip_forward` |

> **Note:** Changes made with `ip` commands are temporary and lost on reboot. Use `/etc/sysctl.conf` for IP forwarding and network configuration files (e.g., `/etc/network/interfaces` or Netplan) for persistent IP/route settings.

---

### Prerequisite — Network Namespaces

Network namespaces are the foundation of container networking. They provide isolated network environments — each namespace has its own interfaces, routing table, and ARP cache, completely separate from the host and other namespaces.

Think of the host as a house and namespaces as rooms. Each room (container) only sees what's inside it, while the host can see into all rooms.

#### Creating and Inspecting Namespaces

```bash
# Create two network namespaces
ip netns add red
ip netns add blue

# List namespaces
ip netns
# red
# blue

# View interfaces inside the red namespace (only loopback exists)
ip netns exec red ip link
# 1: lo: <LOOPBACK> mtu 65536 ...

# Shorthand: -n flag
ip -n red link

# The host's eth0 is NOT visible inside the namespace
# Each namespace also has its own ARP and routing table:
ip netns exec red arp
ip netns exec red route
```

#### Connecting Two Namespaces with a veth Pair

To connect two namespaces directly, create a veth pair (virtual cable):

```bash
# Create a veth pair
ip link add veth-red type veth peer name veth-blue

# Move each end into its namespace
ip link set veth-red netns red
ip link set veth-blue netns blue

# Assign IP addresses
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n blue addr add 192.168.15.2/24 dev veth-blue

# Bring interfaces up
ip -n red link set veth-red up
ip -n blue link set veth-blue up

# Test connectivity
ip netns exec red ping 192.168.15.2
# PING 192.168.15.2: 64 bytes from 192.168.15.2 ...

# Check ARP — each namespace learns the other's MAC address
ip netns exec red arp
# Address          HWtype  HWaddress           Iface
# 192.168.15.2     ether   ba:b0:6d:68:09:e9   veth-red
```

These veth interfaces do not appear in the host's ARP table — they exist only within their namespaces.

#### Connecting Multiple Namespaces with a Bridge

Direct veth pairs don't scale beyond two namespaces. For multiple namespaces, create a **virtual bridge** (virtual switch) on the host:

```bash
# Create a bridge interface
ip link add v-net-0 type bridge
ip link set v-net-0 up

# Delete the old direct veth pair (no longer needed)
ip -n red link del veth-red

# Create new veth pairs: one end for the namespace, one for the bridge
ip link add veth-red type veth peer name veth-red-br
ip link add veth-blue type veth peer name veth-blue-br

# Attach namespace ends
ip link set veth-red netns red
ip link set veth-blue netns blue

# Attach bridge ends
ip link set veth-red-br master v-net-0
ip link set veth-blue-br master v-net-0

# Assign IPs and bring up
ip -n red addr add 192.168.15.1/24 dev veth-red
ip -n blue addr add 192.168.15.2/24 dev veth-blue
ip -n red link set veth-red up
ip -n blue link set veth-blue up
```

```
┌──────────────────────────────────────────────────────────────┐
│  Host                                                        │
│                                                              │
│  ┌──────────┐  veth pair  ┌──────────┐  veth pair  ┌──────────┐
│  │ red ns   │◄───────────►│  v-net-0 │◄───────────►│ blue ns  │
│  │ veth-red │             │ (bridge) │             │veth-blue │
│  │.15.1     │             │          │             │.15.2     │
│  └──────────┘             └────┬─────┘             └──────────┘
│                                │                              │
│                           eth0 │ (host interface)             │
└────────────────────────────────┼──────────────────────────────┘
```

#### Host-to-Namespace Communication

To let the host communicate with namespaces, assign an IP to the bridge:

```bash
ip addr add 192.168.15.5/24 dev v-net-0

# Now the host can reach namespaces
ping 192.168.15.1
```

#### External Connectivity from Namespaces

Namespaces are isolated from external networks by default. To let a namespace reach an external network (e.g., 192.168.1.0/24):

```bash
# Add a route inside the namespace — use the host (bridge IP) as gateway
ip netns exec blue ip route add 192.168.1.0/24 via 192.168.15.5

# The host forwards the traffic, but external hosts don't know about 192.168.15.x
# Enable NAT (masquerade) so packets appear to come from the host's external IP
iptables -t nat -A POSTROUTING -s 192.168.15.0/24 -j MASQUERADE
```

For internet access, add a default route in the namespace:

```bash
ip netns exec blue ip route add default via 192.168.15.5
```

#### Inbound Access to Namespaces

External hosts can't reach namespace IPs directly. Two options:

1. **Static route** on the external network pointing to the host
2. **Port forwarding** via iptables (preferred — no external routing changes needed):

```bash
# Forward host port 80 to the blue namespace's IP on port 80
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.15.2:80
```

This is the same mechanism Docker uses for `-p` port mapping and Kubernetes uses for NodePort services.

---

### Prerequisite — Docker Networking

Before understanding Kubernetes pod networking, it helps to know how Docker handles container networking. Docker provides three networking modes:

#### Docker Networking Modes

**None network** — the container has no network access at all. Completely isolated:

```bash
docker run --network none nginx
```

**Host network** — the container shares the host's network stack directly. No isolation — if the container listens on port 80, it binds to port 80 on the host. A second container on the same port will fail:

```bash
docker run --network host nginx
```

**Bridge network (default)** — Docker creates an internal private network. Each container gets its own IP from this subnet:

```bash
docker run nginx    # uses bridge by default

# List Docker networks
docker network ls
# NETWORK ID     NAME      DRIVER    SCOPE
# 2b6008726112   bridge    bridge    local
# 0beb4870b093   host      host      local
# 99035e02694f   none      null      local
```

#### The docker0 Bridge

When Docker is installed, it creates a virtual bridge interface called `docker0` on the host (the `bridge` network maps to this interface). It typically gets the IP `172.17.0.1` with a `/16` subnet:

```bash
# View the docker0 interface
ip link show docker0
# 4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...

ip addr show docker0
# inet 172.17.0.1/16 ...
```

#### How Docker Connects Containers to the Bridge

When a container starts, Docker:
1. Creates a new **network namespace** for the container
2. Creates a **veth pair** (virtual cable)
3. Attaches one end to the container namespace (appears as `eth0` inside the container)
4. Attaches the other end to the `docker0` bridge on the host
5. Assigns an IP address from the bridge subnet (e.g., 172.17.0.3)

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Host (192.168.1.10)                                 │
│                                                             │
│  ┌───────────┐  veth pair  ┌──────────┐  veth pair  ┌───────────┐
│  │ Container │◄───────────►│ docker0  │◄───────────►│ Container │
│  │ eth0      │             │ (bridge) │             │ eth0      │
│  │172.17.0.2 │             │172.17.0.1│             │172.17.0.3 │
│  └───────────┘             └────┬─────┘             └───────────┘
│                                 │                               │
│                            eth0 │ 192.168.1.10                  │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                             Local Network
```

You can inspect the veth pairs and container namespace:

```bash
# View veth interfaces on the host (attached to docker0)
ip link show
# 8: vethbb1c343@if7: ... master docker0 state UP ...

# View the container's network namespace
docker inspect <container_id> | grep -A3 SandboxKey
# "SandboxKey": "/var/run/docker/netns/b3165c10a92b"

# View the interface inside the container's namespace
ip -n b3165c10a92b link show
# 7: eth0@if8: ... state UP ...

# View the container's IP address
ip -n b3165c10a92b addr show eth0
# inet 172.17.0.3/16 ...
```

The veth pair numbers are always consecutive (e.g., 7 and 8, 9 and 10) — each pair forms one virtual cable.

#### Docker Port Mapping

Containers on the bridge network have private IPs (172.17.x.x) not reachable from outside the host. Docker uses **port mapping** to expose container ports:

```bash
# Map host port 8080 → container port 80
docker run -p 8080:80 nginx

# Now accessible from outside
curl http://192.168.1.10:8080
# Welcome to nginx!
```

Docker implements port mapping using **iptables NAT rules**. It adds a DNAT (Destination NAT) rule in the PREROUTING chain:

```bash
# Docker adds a rule like this:
iptables -t nat -A PREROUTING -j DNAT --dport 8080 --to-destination 172.17.0.2:80

# View the active NAT rules
iptables -nvL -t nat
# Chain DOCKER (2 references)
# target  prot  source       destination
# DNAT    tcp   anywhere     anywhere     tcp dpt:8080 to:172.17.0.2:80
```

This is the same iptables/NAT mechanism that Kubernetes uses for Services — kube-proxy creates similar DNAT rules to forward Service ClusterIP traffic to pod IPs.

---

### How Pod Networking Works

Every pod gets its own IP address. Kubernetes networking follows three rules:
1. **Pod-to-pod** — any pod can communicate with any other pod without NAT
2. **Node-to-pod** — any node can communicate with any pod without NAT
3. **Pod sees its own IP** — the IP a pod sees for itself is the same IP others see

Kubernetes does not implement networking itself — it defines the rules above and delegates to a CNI plugin. Understanding the underlying mechanics helps troubleshoot connectivity issues.

#### Network Namespaces and veth Pairs

Each pod runs in its own **network namespace**, which isolates its network stack (interfaces, routing table, iptables rules) from the host and other pods. Containers within the same pod share one network namespace, which is why they communicate over `localhost`.

To connect a pod's isolated namespace to the node's network, the kernel creates a **veth pair** — a virtual ethernet cable with one end inside the pod namespace and the other end attached to a **bridge network** on the node:

```
┌─────────────────────────────────────────────────────────────────┐
│  Node 1 (192.168.1.11)                                         │
│                                                                 │
│  ┌──────────┐   veth    ┌──────────┐   veth    ┌──────────┐    │
│  │ Pod A    │◄─────────►│          │◄─────────►│ Pod B    │    │
│  │ eth0     │           │ Bridge   │           │ eth0     │    │
│  │10.244.1.2│           │ v-net-0  │           │10.244.1.3│    │
│  │(namespace│           │10.244.1.1│           │(namespace│    │
│  │  A)      │           │          │           │  B)      │    │
│  └──────────┘           └────┬─────┘           └──────────┘    │
│                              │                                  │
│                         eth0 │ 192.168.1.11                     │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                          Physical Network
```

**What happens step-by-step when a pod is created:**

```bash
# 1. Create a network namespace for the pod
ip netns add <pod-namespace>

# 2. Create a veth pair (virtual cable)
ip link add veth-<pod> type veth peer name veth-<pod>-br

# 3. Attach one end to the pod namespace
ip link set veth-<pod> netns <pod-namespace>

# 4. Attach the other end to the bridge
ip link set veth-<pod>-br master v-net-0

# 5. Assign an IP address inside the pod namespace
ip -n <pod-namespace> addr add 10.244.1.2/24 dev veth-<pod>

# 6. Bring up both interfaces
ip -n <pod-namespace> link set veth-<pod> up
ip link set veth-<pod>-br up

# 7. Set default route inside the pod to the bridge
ip -n <pod-namespace> route add default via 10.244.1.1
```

In practice, you never run these commands manually — the CNI plugin does all of this automatically when kubelet creates a pod.

#### Same-Node Pod-to-Pod Communication

When Pod A (10.244.1.2) sends traffic to Pod B (10.244.1.3) on the same node, the packet travels through the bridge:

```
Pod A (10.244.1.2) → veth → Bridge (v-net-0) → veth → Pod B (10.244.1.3)
```

The bridge acts like a virtual switch — it learns MAC addresses and forwards frames between attached veth interfaces. No routing is needed for same-node traffic.

#### Cross-Node Pod-to-Pod Communication

When Pod A on Node 1 (10.244.1.2) needs to reach Pod C on Node 2 (10.244.2.2), the packet must leave the node. The bridge doesn't know about pods on other nodes, so a route must exist:

```bash
# On Node 1: route to Node 2's pod subnet via Node 2's IP
ip route add 10.244.2.0/24 via 192.168.1.12

# On Node 2: route to Node 1's pod subnet via Node 1's IP
ip route add 10.244.1.0/24 via 192.168.1.11
```

```
Pod A (Node 1)                                    Pod C (Node 2)
10.244.1.2                                        10.244.2.2
    │                                                 ▲
    ▼                                                 │
Bridge v-net-0 ──► eth0 ──► Network ──► eth0 ──► Bridge v-net-0
10.244.1.1     192.168.1.11       192.168.1.12    10.244.2.1
```

This manual routing approach works for small clusters but doesn't scale. In production, CNI plugins handle this using one of:
- **Overlay networks** (VXLAN/Geneve) — encapsulate pod traffic in node-to-node tunnels (Flannel, Calico VXLAN mode)
- **BGP routing** — advertise pod subnets via BGP so routers know where to send traffic (Calico BGP mode)
- **Cloud-native routing** — use the cloud provider's VPC routing (AWS VPC-CNI, Azure CNI)

#### NAT for External Traffic

Pods use private IPs (e.g., 10.244.x.x) that aren't routable on the internet. When a pod sends traffic outside the cluster, the node applies **IP masquerade** (SNAT) so the packet appears to come from the node's IP:

```bash
# iptables rule that NATs outbound pod traffic
iptables -t nat -A POSTROUTING -s 10.244.0.0/16 ! -o cni0 -j MASQUERADE
```

Return traffic is automatically de-NATed back to the pod's IP. This is why pods can reach the internet but external hosts can't directly reach pods without a Service or Ingress.

### CNI (Container Network Interface)

#### Why CNI Exists — The Bridge Program Pattern

Every container runtime faces the same networking problem: create a network namespace, attach it to a bridge via veth pairs, assign an IP, and configure routes. Docker, rkt, Mesos, and Kubernetes all solve this the same way — the only differences are naming conventions.

Rather than each runtime reimplementing this logic, a standalone **bridge program** was created to handle it:

```bash
# The bridge program automates all namespace-to-bridge wiring
bridge add <container-id> /var/run/netns/<container-id>
```

This program handles creating the veth pair, attaching to the bridge, assigning an IP, and bringing up interfaces — the same steps shown in the manual commands above. Any container runtime can call it instead of implementing networking itself.

The question then becomes: what interface should such programs follow? What arguments, commands, and output format? This is what CNI standardizes.

#### The CNI Specification

CNI is a **specification** that defines how network plugins integrate with container runtimes. It standardizes three operations:
- **ADD** — attach a container to a network (create namespace, veth pair, assign IP)
- **DEL** — detach a container from a network (clean up interfaces and IP allocation)
- **CHECK** — verify a container's networking is correctly configured

CNI plugins are simple executables that accept these commands along with the container ID and network namespace as parameters. The plugin manages IP assignment and routing, and returns results in a defined JSON format.

**Built-in CNI plugins** (shipped with the CNI project):

| Category | Plugins |
|---|---|
| **Interface** | bridge, ipvlan, macvlan, ptp, vlan, host-device, win-bridge, win-overlay |
| **IPAM** | host-local (allocates from a local range), dhcp, static |
| **Meta** | portmap, bandwidth, tuning, firewall, sbr |

**Third-party CNI plugins** (installed separately): Calico, Flannel, Weave, Cilium, VMware NSX, Infoblox

#### CNI vs CNM (Docker's Container Network Model)

Docker developed its own networking standard called CNM (Container Network Model), used by `docker network`. Kubernetes chose CNI instead because:
- CNI is simpler — a single binary that receives JSON config and performs ADD/DEL/CHECK
- CNI is runtime-agnostic — works with containerd, CRI-O, and any CRI-compliant runtime
- Docker's CNM is tightly coupled to the Docker daemon

Because Docker uses CNM (not CNI), Kubernetes historically worked around this by creating Docker containers with `--network=none` and then invoking the CNI plugin separately:

```bash
# Kubernetes creates the container with no network
docker run --network=none nginx

# Then calls the CNI plugin to set up networking
bridge add 2e34dcf34 /var/run/netns/2e34dcf34
```

This is no longer relevant since Kubernetes dropped Docker support in v1.24+ and uses containerd or CRI-O directly, both of which natively support CNI.

#### How Kubelet Invokes CNI

When kubelet creates a pod, it:
1. Creates the pod's network namespace via the container runtime
2. Reads the CNI configuration from `--cni-conf-dir` (default: `/etc/cni/net.d/`)
3. Executes the CNI plugin binary from `--cni-bin-dir` (default: `/opt/cni/bin/`)
4. Passes the network namespace path and configuration as JSON to the plugin

```bash
# View installed CNI plugin binaries
ls /opt/cni/bin/
# bandwidth  bridge  calico  dhcp  flannel  host-local  ipvlan
# loopback  macvlan  portmap  ptp  sbr  static  tuning  vlan  weave-net

# View CNI configuration (first file alphabetically is used)
ls /etc/cni/net.d/
# 10-calico.conflist

cat /etc/cni/net.d/10-calico.conflist
```

Example CNI configuration:

```json
{
  "name": "k8s-pod-network",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "calico",
      "datastore_type": "kubernetes",
      "ipam": {
        "type": "calico-ipam"
      },
      "policy": {
        "type": "k8s"
      }
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}
```

Key fields:
- **`type`** — name of the CNI binary to execute (must exist in `/opt/cni/bin/`)
- **`ipam`** — IP Address Management plugin (how IPs are allocated: `host-local`, `calico-ipam`, `dhcp`)
- **`plugins`** — chained plugins executed in order (e.g., calico sets up networking, then portmap handles port forwarding)

#### Kubelet CNI Configuration

```bash
# Check kubelet's CNI settings
ps aux | grep kubelet | grep -o '\-\-cni[^ ]*'
# --cni-bin-dir=/opt/cni/bin
# --cni-conf-dir=/etc/cni/net.d

# Or check the kubelet config file
cat /var/lib/kubelet/config.yaml | grep -A2 cni
```

If no CNI plugin is installed, pods stay in `ContainerCreating` state because the network namespace can't be configured.

#### CNI Plugin Comparison

| CNI Plugin | Used By | Key Feature |
|---|---|---|
| **Calico** | Self-managed, Kind | Network policies, BGP routing |
| **AWS VPC-CNI** | EKS | Pods get real VPC IPs (no overlay) |
| **Flannel** | Simple clusters | VXLAN overlay, easy setup |
| **Cilium** | Advanced clusters | eBPF-based, high performance |
| **Weave** | Self-managed | Encrypted overlay network |

#### Cluster Network Planning

Consider the following plan for a three-node cluster:

1. **Node network**: 192.168.1.0/24 — each node gets an IP (e.g., .11, .12, .13)
2. **Pod network**: 10.244.0.0/16 — each node gets a /24 subnet (10.244.1.0/24, 10.244.2.0/24, 10.244.3.0/24)
3. **Service network**: 10.96.0.0/12 — virtual IPs managed by kube-proxy (not assigned to interfaces)

```bash
# Verify pod CIDR allocation per node
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDR}{"\n"}{end}'
# node1   10.244.1.0/24
# node2   10.244.2.0/24
# node3   10.244.3.0/24

# Verify service CIDR
kubectl cluster-info dump | grep -m1 service-cluster-ip-range
# --service-cluster-ip-range=10.96.0.0/12
```

### Service Networking Internals

Unlike pods, **services are not processes or containers** — they are cluster-wide virtual objects. A Service has no network namespace, no interface, and no process listening on a port. It exists only as forwarding rules distributed across all nodes by kube-proxy.

When a Service is created:
1. The API server assigns it an IP from `--service-cluster-ip-range` (e.g., 10.96.0.0/12)
2. kube-proxy on every node detects the new Service via the API server
3. kube-proxy creates forwarding rules so traffic to the Service IP is redirected to backend pod IPs

The pod CIDR and service CIDR **must not overlap**:

```bash
# Check the service IP range (method 1: cluster-info dump)
kubectl cluster-info dump | grep -m1 service-cluster-ip-range
# --service-cluster-ip-range=10.96.0.0/12  (10.96.0.0 – 10.111.255.255)

# Check the service IP range (method 2: kube-apiserver manifest)
grep service-cluster-ip-range /etc/kubernetes/manifests/kube-apiserver.yaml
# - --service-cluster-ip-range=10.96.0.0/12

# Check the pod IP range
kubectl cluster-info dump | grep -m1 cluster-cidr
# --cluster-cidr=10.244.0.0/16  (10.244.0.0 – 10.244.255.255)
```

#### kube-proxy Deployment

kube-proxy runs as a **DaemonSet** — one pod per node, ensuring every node has the forwarding rules for all Services:

```bash
kubectl get daemonset -n kube-system
# NAME         DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE
# kube-proxy   3         3         3       3            3
# weave-net    3         3         3       3            3
```

#### kube-proxy Modes

kube-proxy supports three proxy modes:

| Mode | How it works | Pros | Cons |
|---|---|---|---|
| **userspace** | kube-proxy listens on a port, proxies traffic in user space | Simple, original implementation | Slow — every packet crosses user/kernel boundary |
| **iptables** (default) | Creates iptables NAT rules for each Service | Fast, no user-space overhead | Scales poorly with thousands of Services (linear rule scan) |
| **IPVS** | Uses kernel IPVS (IP Virtual Server) load balancer | Best performance at scale, supports multiple LB algorithms | Requires IPVS kernel modules |

```bash
# Check which mode kube-proxy is using
kubectl logs -n kube-system -l k8s-app=kube-proxy | grep "Using .* Proxier"
# I0215 12:00:00.000000  Using iptables Proxier.

# Or check the kube-proxy ConfigMap
kubectl get configmap kube-proxy -n kube-system -o yaml | grep mode
# mode: ""   ← empty means iptables (default)
```

#### How iptables Rules Work for Services

When you create a Service, kube-proxy creates a chain of iptables rules. Here's what happens for a ClusterIP service:

```bash
# Example: db-service (ClusterIP 10.103.132.104, port 3306) → pod 10.244.1.2:3306

# View the service's iptables rules
sudo iptables -t nat -L KUBE-SERVICES -n | grep db-service
# KUBE-SVC-XA5OGUC7  tcp  --  0.0.0.0/0  10.103.132.104  tcp dpt:3306

# The KUBE-SVC chain selects a backend pod (KUBE-SEP = Service EndPoint)
sudo iptables -t nat -L KUBE-SVC-XA5OGUC7 -n
# KUBE-SEP-JBWCWHHQ  all  --  0.0.0.0/0  0.0.0.0/0

# The KUBE-SEP chain performs DNAT to the actual pod IP
sudo iptables -t nat -L KUBE-SEP-JBWCWHHQ -n
# DNAT  tcp  --  0.0.0.0/0  0.0.0.0/0  tcp to:10.244.1.2:3306
```

The chain flow:

```
KUBE-SERVICES → KUBE-SVC-xxx (matches Service ClusterIP)
                    → KUBE-SEP-xxx (DNAT to pod IP:port)
```

For Services with multiple pods, the KUBE-SVC chain has multiple KUBE-SEP entries with `statistic mode random probability` rules to distribute traffic.

For NodePort services, kube-proxy adds an additional rule in the KUBE-NODEPORTS chain that catches traffic on the NodePort and redirects it to the same KUBE-SVC chain.

#### Verifying kube-proxy

```bash
# View kube-proxy logs
kubectl logs -n kube-system -l k8s-app=kube-proxy | tail -20

# View all NAT rules (can be very long in large clusters)
sudo iptables -t nat -L -n -v | head -50

# View IPVS rules (if using IPVS mode)
sudo ipvsadm -Ln
```

### Network Debugging

```bash
# 1. Test DNS resolution from inside a pod
kubectl run dns-test --image=busybox --rm -it -- nslookup kubernetes.default

# 2. Test connectivity between pods
kubectl run curl-test --image=curlimages/curl --rm -it -- curl -s http://<service-name>.<namespace>.svc.cluster.local

# 3. Check if a pod can reach external internet
kubectl run net-test --image=busybox --rm -it -- wget -qO- http://ifconfig.me

# 4. Debug DNS issues
kubectl run dns-debug --image=busybox --rm -it -- cat /etc/resolv.conf
# Output:
# nameserver 10.96.0.10        ← CoreDNS ClusterIP
# search default.svc.cluster.local svc.cluster.local cluster.local

# 5. Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# 6. Test port connectivity
kubectl run port-test --image=busybox --rm -it -- nc -zv <service-ip> <port>
```

#### Identifying Your CNI Plugin

```bash
# Check which CNI config file exists (first alphabetically is used)
ls /etc/cni/net.d/
# 10-weave.conflist    ← Weave
# 10-calico.conflist   ← Calico
# 10-flannel.conflist  ← Flannel

# Read the config to confirm
cat /etc/cni/net.d/10-weave.conflist
# { "name": "weave", "plugins": [{ "type": "weave-net" ... }] }

# Check which CNI pods are running
kubectl get pods -n kube-system | grep -E "weave|calico|flannel|cilium"
```

Different CNI plugins create different bridge interfaces:

| CNI Plugin | Bridge Interface | Default Pod CIDR |
|---|---|---|
| Flannel | `cni0` | 10.244.0.0/16 |
| Weave | `weave` | 10.32.0.0/12 (or custom) |
| Calico | `cali*` (no bridge, uses routes) | 192.168.0.0/16 |
| Cilium | `cilium_*` | 10.0.0.0/8 |

#### Inspecting Pod Networking on a Specific Node

To check the default gateway and routing for pods on a particular node, schedule a debug pod there:

```bash
# Create a busybox pod on a specific node
kubectl run debug-net --image=busybox --overrides='{"spec":{"nodeName":"node01"}}' -- sleep 3600

# Check the pod's routing table
kubectl exec debug-net -- ip route
# default via 10.244.192.0 dev eth0
# 10.244.0.0/16 dev eth0 scope link src 10.244.192.1

# Check the pod's network interfaces
kubectl exec debug-net -- ip addr

# Cleanup
kubectl delete pod debug-net
```

#### Verifying CNI Plugin from Logs

```bash
# Weave: check ipalloc-range in logs
kubectl logs -n kube-system -l name=weave-net -c weave | grep ipalloc-range
# INFO: Command line options: map[... ipalloc-range:10.244.0.0/16 ...]

# Calico: check CIDR
kubectl get ippools.crd.projectcalico.org -o yaml | grep cidr

# Flannel: check subnet config
kubectl get configmap kube-flannel-cfg -n kube-flannel -o jsonpath='{.data.net-conf\.json}'
```

### Accessing Applications Running in Kubernetes

| Method | Use Case | External Access | Command |
|---|---|---|---|
| `kubectl port-forward` | Local debugging | localhost only | `kubectl port-forward pod/my-app 8080:80` |
| `NodePort` Service | Development/testing | `<node-ip>:30000-32767` | Create Service with `type: NodePort` |
| `LoadBalancer` Service | Production | Cloud LB public IP | Create Service with `type: LoadBalancer` |
| `Ingress` | Production HTTP/HTTPS | Domain-based routing | Create Ingress resource |
| `kubectl exec` + `curl` | Internal testing | N/A | `kubectl exec <pod> -- curl localhost:80` |

### kubectl port-forward — Deep Dive

`kubectl port-forward` creates a tunnel from your local machine to a pod or service in the cluster. No Service or Ingress needed.

```
┌──────────────────────────────────────────────────────────────┐
│  How port-forward works internally                           │
│                                                              │
│  Your laptop                    Kubernetes Cluster           │
│  ┌──────────┐                   ┌──────────────────┐         │
│  │ Browser  │                   │  Pod: my-app     │         │
│  │ or curl  │                   │  Container :8080 │         │
│  │          │                   └────────▲─────────┘         │
│  └────┬─────┘                            │                   │
│       │ localhost:9090                    │ :8080             │
│       ▼                                  │                   │
│  ┌────────────┐    HTTPS tunnel    ┌─────┴──────┐            │
│  │  kubectl   │───────────────────►│ API Server │            │
│  │  process   │  (via kubeconfig)  │     │      │            │
│  └────────────┘                    │     ▼      │            │
│                                    │  kubelet   │            │
│                                    │  on node   │            │
│                                    └────────────┘            │
│                                                              │
│  kubectl opens a local TCP listener on port 9090             │
│  Every connection is tunneled through the API Server         │
│  to the kubelet, which forwards to the pod's container port  │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Forward to a specific pod
kubectl port-forward pod/my-app-7b8c9d6e8-abc12 9090:8080

# Output:
# Forwarding from 127.0.0.1:9090 -> 8080
# Forwarding from [::1]:9090 -> 8080

# Now access: http://localhost:9090

# Forward to a Service (picks a random pod behind the service)
kubectl port-forward svc/my-app 9090:80

# Output:
# Forwarding from 127.0.0.1:9090 -> 8080

# Forward to a Deployment (picks a random pod)
kubectl port-forward deployment/my-app 9090:8080

# Listen on all interfaces (not just localhost)
kubectl port-forward --address 0.0.0.0 pod/my-app 9090:8080

# Forward multiple ports
kubectl port-forward pod/my-app 9090:8080 9091:9090

# Run in background
kubectl port-forward svc/my-app 9090:80 &

# Forward to a pod in a specific namespace
kubectl port-forward -n database pod/postgres-0 5432:5432
```

**Common use cases:**

```bash
# 1. Debug a ClusterIP service without creating NodePort/LB
kubectl port-forward svc/backend-api 8080:80
curl http://localhost:8080/health

# 2. Access a database for local development
kubectl port-forward svc/postgres 5432:5432
psql -h localhost -p 5432 -U admin mydb

# 3. Access Kubernetes Dashboard
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443

# 4. Access Prometheus/Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

**Limitations:**
- Only accessible from your local machine (unless `--address 0.0.0.0`)
- Connection drops if kubectl process is killed
- Not for production traffic — use Services/Ingress instead
- Single TCP connection at a time per forwarded port

**Interview question: What is kubectl port-forward and how does it work?**
`kubectl port-forward` creates a TCP tunnel from a local port to a pod/service port via the API server. It's used for local debugging without exposing services externally. kubectl opens a local listener, and every connection is tunneled through the API server to the kubelet on the target node, which forwards to the container. It's not suitable for production — use Services or Ingress instead.

```bash
# Method 2: NodePort
kubectl expose deployment my-app --type=NodePort --port=80
kubectl get svc my-app
# Access at http://<node-ip>:<nodePort>

# Method 3: LoadBalancer (cloud only)
kubectl expose deployment my-app --type=LoadBalancer --port=80
kubectl get svc my-app --watch
# Wait for EXTERNAL-IP, then access at http://<external-ip>

# Method 4: Ingress (requires Ingress controller)
# See section 4.4 for Ingress configuration
```

---

