# MODULE 28: Kubernetes Version Upgrades

---

## 28.1 Kubernetes Version Upgrades

### Understanding Kubernetes Versions

Kubernetes follows semantic versioning: `v1.29.3` = `v<major>.<minor>.<patch>`

- **Minor releases** (1.28 → 1.29) — every ~4 months, contain new features and API changes
- **Patch releases** (1.29.2 → 1.29.3) — bug fixes and security patches
- **Support window** — each minor version is supported for ~14 months
- **Skew policy** — you can only upgrade one minor version at a time (1.28 → 1.29, NOT 1.28 → 1.30)

### Component Version Skew Policy

Not all components need to be at the same version. The **kube-apiserver** is the reference point — no other control plane component can be newer than it.

| Component | Allowed Versions (relative to kube-apiserver) | Example (API server at 1.30) |
|---|---|---|
| **kube-apiserver** | Reference (X) | 1.30 |
| **kube-controller-manager** | X or X-1 | 1.30 or 1.29 |
| **kube-scheduler** | X or X-1 | 1.30 or 1.29 |
| **kubelet** | X, X-1, or X-2 | 1.30, 1.29, or 1.28 |
| **kube-proxy** | X, X-1, or X-2 | 1.30, 1.29, or 1.28 |
| **kubectl** | X+1, X, or X-1 | 1.31, 1.30, or 1.29 |

This is why you **upgrade the control plane first, then workers** — workers (kubelet) can be older than the API server, but never newer.

**Example upgrade path from v1.28 to v1.30:**

```
Step 1: Upgrade control plane to v1.29
        API server: 1.29, Workers: 1.28 ← allowed (kubelet X-1)

Step 2: Upgrade workers to v1.29
        API server: 1.29, Workers: 1.29 ← all aligned

Step 3: Upgrade control plane to v1.30
        API server: 1.30, Workers: 1.29 ← allowed (kubelet X-1)

Step 4: Upgrade workers to v1.30
        API server: 1.30, Workers: 1.30 ← all aligned
```

### Cluster Maintenance — OS Upgrades

When you need to upgrade the operating system, apply kernel patches, or perform hardware maintenance on a node:

```
┌─────────────────────────────────────────────────────────────┐
│  OS Upgrade Workflow                                        │
│                                                             │
│  1. kubectl drain <node> --ignore-daemonsets                │
│     → Pods are evicted and rescheduled to other nodes       │
│                                                             │
│  2. Perform OS upgrade / reboot                             │
│     → apt upgrade, yum update, kernel patch, etc.           │
│                                                             │
│  3. kubectl uncordon <node>                                 │
│     → Node becomes schedulable again                        │
│     → New pods can be placed here                           │
│     → Previously evicted pods do NOT automatically return   │
└─────────────────────────────────────────────────────────────┘
```

**Pod eviction timeout:** If a node goes down unexpectedly (without drain), the controller-manager waits **5 minutes** (`--pod-eviction-timeout=5m0s`, the default) before considering the pods on that node as dead and rescheduling them. This means:

- If the node comes back within 5 minutes, pods resume normally
- If the node stays down beyond 5 minutes, pods are terminated and rescheduled
- Pods without a controller (standalone pods) are lost permanently

```bash
# Check the current pod eviction timeout
# (set on kube-controller-manager)
ps aux | grep kube-controller-manager | grep pod-eviction-timeout

# Quick maintenance (node comes back within 5 minutes):
# No drain needed — pods survive the reboot

# Planned maintenance (longer than 5 minutes):
# MUST drain first to safely move workloads
kubectl drain node01 --ignore-daemonsets --delete-emptydir-data
# ... perform maintenance ...
kubectl uncordon node01
```

**Removing a node permanently:**

```bash
# 1. Drain the node
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data

# 2. Delete the node from the cluster
kubectl delete node <node>

# 3. On the node itself, reset kubeadm
sudo kubeadm reset
```

### Before Upgrading — What to Check

```bash
# 1. Check current version
kubectl version
kubeadm version

# 2. Read the changelog for the target version
# https://github.com/kubernetes/kubernetes/blob/master/CHANGELOG/CHANGELOG-1.29.md

# 3. Check for deprecated APIs
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

# 4. Check API deprecation warnings in audit logs
kubectl get events --field-selector reason=DeprecatedAPI
```

**Changelog checklist before upgrading:**

| Check | Where to Look | Why |
|---|---|---|
| Deprecated APIs | Changelog "API Changes" section | Your manifests may use removed APIs |
| Feature gates | Changelog "Feature" section | New defaults may change behavior |
| Breaking changes | Changelog "Breaking Changes" section | May require manifest updates |
| Known issues | Changelog "Known Issues" section | Avoid versions with critical bugs |
| Storage changes | Changelog "Storage" section | PV/PVC behavior may change |
| Network changes | Changelog "Network" section | CNI compatibility |

**Tools for checking API compatibility:**

```bash
# Install pluto — detects deprecated APIs in your manifests
# https://github.com/FairwindsOps/pluto
pluto detect-files -d ./manifests/
pluto detect-helm -owide

# Install kubent — finds deprecated APIs in running cluster
# https://github.com/doitintl/kube-no-trouble
kubent
```

### Package Repository Migration

The legacy Kubernetes package repositories (`apt.kubernetes.io` and `yum.kubernetes.io`) have been deprecated. Packages are now hosted at [pkgs.k8s.io](https://pkgs.k8s.io). Before upgrading, ensure your nodes point to the new repository for the target version.

```bash
# Check your OS distribution (commands differ for Debian vs RHEL)
cat /etc/*release*

# For Debian/Ubuntu — update the repository to the target version
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Download the signing key (if not already present)
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

sudo apt-get update
```

⚠️ Update the version number in the repository URL (e.g., `v1.29` → `v1.30`) on **both** control plane and worker nodes before starting the upgrade.

### Upgrading with kubeadm (Self-Managed Clusters)

**Always upgrade control plane first, then workers. One minor version at a time.**

```bash
# === CONTROL PLANE NODE ===

# 1. Check available versions
sudo apt update
apt-cache madison kubeadm | head -5

# Output:
#    kubeadm | 1.30.3-1.1 | https://pkgs.k8s.io/core:/stable:/v1.30/deb Packages
#    kubeadm | 1.30.2-1.1 | https://pkgs.k8s.io/core:/stable:/v1.30/deb Packages
#    kubeadm | 1.30.1-1.1 | https://pkgs.k8s.io/core:/stable:/v1.30/deb Packages
#    kubeadm | 1.30.0-1.1 | https://pkgs.k8s.io/core:/stable:/v1.30/deb Packages

# 2. Upgrade kubeadm
sudo apt-mark unhold kubeadm
sudo apt install -y kubeadm=1.30.0-1.1
sudo apt-mark hold kubeadm

# 3. Verify upgrade plan
sudo kubeadm upgrade plan

# Output shows:
# Components that must be upgraded manually after you have upgraded the control plane:
# COMPONENT   CURRENT   TARGET
# kubelet     v1.29.0   v1.30.0
#
# Upgrade to the latest stable version:
# COMPONENT                 CURRENT   TARGET
# kube-apiserver            v1.29.0   v1.30.0
# kube-controller-manager   v1.29.0   v1.30.0
# kube-scheduler            v1.29.0   v1.30.0
# kube-proxy                v1.29.0   v1.30.0
# CoreDNS                   v1.11.1   v1.11.3
# etcd                      3.5.10    3.5.12

# 4. Apply the upgrade
sudo kubeadm upgrade apply v1.30.0

# Output (after upgrading static pod manifests, renewing certs, etc.):
# [upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.30.0". Enjoy!
# [upgrade/kubelet] Now that your control plane is upgraded, please proceed
#                   with upgrading your kubelets.

# Verify kubeadm version
kubeadm version
# kubeadm version: &version.Info{Major:"1", Minor:"30", GitVersion:"v1.30.0", ...}

# NOTE: kubectl get nodes still shows the OLD kubelet version at this point.
# The kubelet hasn't been upgraded yet — only the control plane components have.

# 5. Drain the control plane node
kubectl drain <control-plane-node> --ignore-daemonsets --delete-emptydir-data

# 6. Upgrade kubelet and kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt install -y kubelet=1.30.0-1.1 kubectl=1.30.0-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 7. Uncordon the node
kubectl uncordon <control-plane-node>
```

```bash
# === EACH WORKER NODE ===

# 1. Upgrade kubeadm on the worker
sudo apt-mark unhold kubeadm
sudo apt install -y kubeadm=1.30.0-1.1
sudo apt-mark hold kubeadm

# 2. Upgrade node config
sudo kubeadm upgrade node

# 3. Drain the worker (run from control plane)
kubectl drain <worker-node> --ignore-daemonsets --delete-emptydir-data

# 4. Upgrade kubelet and kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt install -y kubelet=1.30.0-1.1 kubectl=1.30.0-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 5. Uncordon the worker (run from control plane)
kubectl uncordon <worker-node>
```

```bash
# Verify upgrade
kubectl get nodes

# Output:
# NAME       STATUS   ROLES           AGE   VERSION
# master     Ready    control-plane   30d   v1.30.0
# worker-1   Ready    <none>          30d   v1.30.0
# worker-2   Ready    <none>          30d   v1.30.0
```

### Upgrading EKS

```bash
# Check available versions
aws eks describe-cluster --name my-cluster --query 'cluster.version'

# Upgrade control plane (AWS manages this)
eksctl upgrade cluster --name my-cluster --version 1.30 --approve

# Upgrade node groups
eksctl upgrade nodegroup --name workers --cluster my-cluster --kubernetes-version 1.30

# Or with managed node groups (rolling update)
aws eks update-nodegroup-version --cluster-name my-cluster --nodegroup-name workers
```

### Upgrade Best Practices

| Practice | Why |
|---|---|
| Upgrade one minor version at a time | Skew policy — skipping versions is unsupported |
| Upgrade control plane before workers | Workers must not be newer than control plane |
| Test in staging first | Catch breaking changes before production |
| Back up etcd before upgrading | Recovery point if upgrade fails |
| Check deprecated APIs before upgrading | Avoid broken deployments after upgrade |
| Drain nodes before upgrading kubelet | Prevents workload disruption |
| Monitor after upgrade | Watch for CrashLoopBackOff, OOM, or API errors |

### etcd Backup Before Upgrade

```bash
# Backup etcd (run on control plane node)
sudo ETCDCTL_API=3 etcdctl snapshot save /tmp/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify backup
sudo ETCDCTL_API=3 etcdctl snapshot status /tmp/etcd-backup.db --write-table

# Restore (disaster recovery only)
sudo ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-restored
```

### Lab: Cluster Upgrade with Zero Downtime

**Scenario:** A cluster running v1.19.0 has a production deployment ("blue" with 5 replicas). Upgrade to v1.20.0 with no application downtime.

```bash
# === PRE-UPGRADE INSPECTION ===

kubectl get nodes
# NAME           STATUS   ROLES    AGE    VERSION
# controlplane   Ready    master   147m   v1.19.0
# node01         Ready    <none>   146m   v1.19.0

# Check for taints that might prevent scheduling
kubectl describe node | grep Taints
# Taints:   <none>
# Taints:   <none>

# Verify running workloads
kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# blue   5/5     5            5           95s

# Check pod distribution across nodes
kubectl get pods -o wide
# Pods are spread across controlplane and node01
```

**Upgrade strategy:** Upgrade one node at a time. Drain the node, upgrade it, uncordon it. Workloads migrate to the remaining node during each step, so the application stays available throughout.

```bash
# === CONTROL PLANE UPGRADE ===

# 1. Drain the control plane
kubectl drain controlplane --ignore-daemonsets
# node/controlplane cordoned
# evicting pod default/blue-746c8756d-r8h27
# evicting pod default/blue-746c8756d-2c8rs
# node/controlplane drained

# Verify node is SchedulingDisabled
kubectl get nodes
# NAME           STATUS                     ROLES    AGE    VERSION
# controlplane   Ready,SchedulingDisabled   master   153m   v1.19.0
# node01         Ready                      <none>   152m   v1.19.0

# Verify all blue pods migrated to node01
kubectl get pods -o wide
# All 5 blue pods now running on node01

# 2. Upgrade kubeadm
apt-mark unhold kubeadm && \
apt-get update && apt-get install -y kubeadm=1.20.0-00 && \
apt-mark hold kubeadm

# 3. Verify and apply
kubeadm upgrade plan
sudo kubeadm upgrade apply v1.20.0
# [upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.20.0". Enjoy!

# 4. Upgrade kubelet and kubectl
apt-mark unhold kubelet kubectl && \
apt-get update && apt-get install -y kubelet=1.20.0-00 kubectl=1.20.0-00 && \
apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 5. Uncordon
kubectl uncordon controlplane
```

```bash
# === WORKER NODE UPGRADE ===

# 1. Drain the worker (from control plane)
kubectl drain node01 --ignore-daemonsets
# Pods migrate back to controlplane

# 2. SSH into the worker and upgrade
ssh node01

apt-mark unhold kubeadm && \
apt-get update && apt-get install -y kubeadm=1.20.0-00 && \
apt-mark hold kubeadm

sudo kubeadm upgrade node

apt-mark unhold kubelet kubectl && \
apt-get update && apt-get install -y kubelet=1.20.0-00 kubectl=1.20.0-00 && \
apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet

exit  # back to control plane
```

```bash
# === POST-UPGRADE VERIFICATION ===

kubectl uncordon node01

kubectl get nodes
# NAME           STATUS   ROLES                  AGE    VERSION
# controlplane   Ready    control-plane,master   165m   v1.20.0
# node01         Ready    <none>                 164m   v1.20.0

kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# blue   5/5     5            5           20m
# Application was available throughout the entire upgrade
```

---

