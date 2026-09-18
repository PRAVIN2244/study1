# MODULE 37: Performance Tuning, Multi-Cluster & Exam Preparation

---

## 37.1 Performance Tuning & Optimization

### Pod Resource Right-Sizing

```bash
# Check actual vs requested resources
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory

# Use VPA in recommendation mode to get suggestions
kubectl get vpa <vpa-name> -o yaml | grep -A20 recommendation
```

**Common performance issues:**

| Issue | Symptom | Fix |
|---|---|---|
| CPU throttling | Slow response times, high latency | Increase CPU limits or remove CPU limits |
| Memory pressure | OOMKilled, node evictions | Increase memory limits, fix memory leaks |
| Too many pods per node | Slow scheduling, network issues | Increase node count, use pod anti-affinity |
| Slow image pulls | Long pod startup times | Use image caching, pre-pull images, use smaller images |
| DNS bottleneck | Intermittent DNS failures | Scale CoreDNS, use NodeLocal DNSCache |

### NodeLocal DNSCache

Reduces DNS latency and CoreDNS load by running a DNS cache on each node:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/kubernetes/master/cluster/addons/dns/nodelocaldns/nodelocaldns.yaml
```

### Efficient Container Images

| Practice | Impact |
|---|---|
| Use multi-stage builds | Smaller images (100MB vs 1GB) |
| Use distroless/alpine base | Fewer vulnerabilities, faster pulls |
| Pin specific versions | Reproducible builds |
| Use `.dockerignore` | Faster builds, smaller context |

---

## 37.2 Multi-Cluster Management

### When to Use Multiple Clusters

| Reason | Example |
|---|---|
| **Environment isolation** | Separate clusters for dev, staging, production |
| **Regional availability** | Clusters in us-east-1 and eu-west-1 |
| **Compliance** | Data residency requirements (GDPR) |
| **Blast radius** | Limit impact of cluster-level failures |
| **Team isolation** | Different teams with different requirements |

### Tools for Multi-Cluster

| Tool | Purpose |
|---|---|
| **kubectx/kubens** | Fast context and namespace switching |
| **ArgoCD** | GitOps deployment across clusters |
| **Crossplane** | Manage infrastructure as Kubernetes resources |
| **Istio multi-cluster** | Service mesh across clusters |
| **Cluster API** | Declarative cluster lifecycle management |

```bash
# Install kubectx for fast context switching
# https://github.com/ahmetb/kubectx

kubectx                    # List all contexts
kubectx production         # Switch to production cluster
kubectx -                  # Switch to previous context

kubens                     # List all namespaces
kubens monitoring          # Switch default namespace
```

### Kubernetes Federation

Federation (KubeFed) allows managing multiple Kubernetes clusters as a single entity — deploying workloads, syncing resources, and distributing traffic across clusters in different regions or cloud providers.

**When to use Federation vs other multi-cluster tools:**

| Approach | Best For | Tool |
|---|---|---|
| **Federation (KubeFed)** | Syncing resources (Deployments, Services, ConfigMaps) across clusters | kubefed |
| **GitOps multi-cluster** | Deploying different configs to different clusters | ArgoCD, Flux |
| **Service mesh multi-cluster** | Cross-cluster service discovery and mTLS | Istio multi-cluster |
| **Cluster API** | Declarative cluster lifecycle (create/upgrade/delete clusters) | CAPI |

**How Federation works:**

```
┌─────────────────────────────────────────────────┐
│                 Federation Control Plane          │
│                                                   │
│  FederatedDeployment ──► Cluster A (us-east-1)   │
│                     ──► Cluster B (eu-west-1)    │
│                     ──► Cluster C (ap-south-1)   │
│                                                   │
│  Federated resources are templates that get       │
│  distributed to member clusters with overrides    │
└─────────────────────────────────────────────────┘
```

**Install KubeFed:**

```bash
# Add the KubeFed Helm repo
helm repo add kubefed-charts https://raw.githubusercontent.com/kubernetes-sigs/kubefed/master/charts

# Install KubeFed in the host cluster
helm install kubefed kubefed-charts/kubefed \
  --namespace kube-federation-system --create-namespace

# Join member clusters
kubefedctl join cluster-us --host-cluster-context=host \
  --cluster-context=cluster-us --v=2

kubefedctl join cluster-eu --host-cluster-context=host \
  --cluster-context=cluster-eu --v=2

# Verify joined clusters
kubectl get kubefedclusters -n kube-federation-system
# NAME         AGE   READY
# cluster-us   5m    True
# cluster-eu   3m    True
```

**Federated Deployment example — deploy nginx to both clusters:**

```yaml
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: nginx
  namespace: default
spec:
  template:
    metadata:
      labels:
        app: nginx
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: nginx
      template:
        metadata:
          labels:
            app: nginx
        spec:
          containers:
          - name: nginx
            image: nginx:1.25
  placement:
    clusters:
    - name: cluster-us
    - name: cluster-eu
  overrides:
  - clusterName: cluster-eu
    clusterOverrides:
    - path: "/spec/replicas"
      value: 5    # EU cluster gets more replicas
```

**Real-life use case — global application deployment:**

A SaaS company runs clusters in US, EU, and Asia. Federation syncs the base Deployment, Service, and ConfigMap to all clusters. Overrides set region-specific environment variables (API endpoints, database URLs). DNS-based global load balancing (Route 53, CloudFlare) routes users to the nearest cluster.

**Federation vs ArgoCD for multi-cluster:**

| Aspect | Federation (KubeFed) | ArgoCD Multi-Cluster |
|---|---|---|
| **Resource sync** | Automatic — federated resources propagate to member clusters | Git-driven — each cluster pulls from a Git repo |
| **Overrides** | Built-in per-cluster overrides in the federated resource | Kustomize overlays or Helm values per cluster |
| **Maturity** | Beta (v2) — limited community adoption | GA — widely adopted |
| **Complexity** | High — requires federation control plane | Lower — ArgoCD manages clusters as targets |
| **Recommendation** | Use for true multi-cluster resource sync | Preferred for most multi-cluster deployments |

> Federation (KubeFed v2) is still in beta and has limited adoption. For most production multi-cluster scenarios, ArgoCD with cluster-specific overlays or Istio multi-cluster for service mesh are more practical choices.

---

## 37.3 CKA/CKAD Exam Preparation

### Exam Environment

The Linux Foundation exam environment comes preconfigured with tools you don't need to set up:

| Preconfigured | Details |
|---|---|
| `kubectl` alias | `k` is aliased to `kubectl` with bash auto-completion enabled |
| Utilities | `jq`, `tmux`, `curl`, `wget`, `man` are preinstalled |
| Editor | `vim` and `nano` are available |
| Documentation | Access to `kubernetes.io/docs` is allowed during the exam |

You do **not** need to run `alias k=kubectl` or `source <(kubectl completion bash)` — these are already configured. Focus on the tasks, not environment setup.

### Exam Tips

| Tip | Detail |
|---|---|
| **Use aliases** | `alias k=kubectl`, `export do="--dry-run=client -o yaml"` |
| **Use kubectl explain** | Faster than searching documentation |
| **Use imperative commands** | `kubectl run`, `kubectl create`, `kubectl expose` for speed |
| **Practice with time limits** | CKA: 2 hours, 17 questions. CKAD: 2 hours, 16 questions |
| **Know vim basics** | `:set paste`, `dd`, `yy`, `p`, `:wq` |
| **Bookmark key docs** | Allowed to use kubernetes.io/docs during exam |

### Essential Speed Commands

```bash
# Aliases
alias k=kubectl
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgn='kubectl get nodes'
export do="--dry-run=client -o yaml"

# Generate YAML templates quickly
k run nginx --image=nginx $do > pod.yaml
k create deploy web --image=nginx --replicas=3 $do > deploy.yaml
k create svc clusterip my-svc --tcp=80:8080 $do > svc.yaml
k create configmap my-config --from-literal=key=value $do > cm.yaml
k create secret generic my-secret --from-literal=pass=secret $do > secret.yaml

# Quick expose
k expose deploy web --port=80 --target-port=8080 --type=NodePort

# Quick scale
k scale deploy web --replicas=5

# Quick rollback
k rollout undo deploy web

# Quick resource check
k top nodes
k top pods --sort-by=memory

# Quick context switch
k config set-context --current --namespace=my-ns
```

### Key Topics by Exam

| CKA Topics | CKAD Topics |
|---|---|
| Cluster installation (kubeadm) | Pod design (labels, selectors, annotations) |
| etcd backup/restore | Multi-container pods |
| Node maintenance (cordon, drain) | Probes (liveness, readiness, startup) |
| RBAC (roles, bindings) | Jobs and CronJobs |
| Network policies | ConfigMaps and Secrets |
| Persistent volumes | Resource limits |
| Troubleshooting (logs, events, describe) | Services and Ingress |
| Cluster upgrades | Deployments (rolling updates, rollbacks) |
| DNS and CoreDNS | Helm basics |

---

## 37.4 Module 10 Exercises

### Exercise 1: etcd Backup and Restore

**Scenario:** You have a running cluster with two deployments ("red" and "blue"). A maintenance window is scheduled. Back up etcd, simulate data loss, and restore.

```bash
# 1. Verify existing deployments
kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# blue   3/3     3            3           18s
# red    2/2     2            2           18s

# 2. Inspect the etcd pod to find version, endpoint, and certificate paths
kubectl describe pod etcd-controlplane -n kube-system | grep -A5 "Command:"
# Look for:
#   --advertise-client-urls=https://10.44.214.9:2379
#   --cert-file=/etc/kubernetes/pki/etcd/server.crt
#   --trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
#   --key-file=/etc/kubernetes/pki/etcd/server.key
#   --data-dir=/var/lib/etcd

# 3. Verify certificate and data paths exist on the host
ls /etc/kubernetes/pki/etcd
# ca.crt  ca.key  healthcheck-client.crt  healthcheck-client.key  peer.crt  peer.key  server.crt  server.key
ls /var/lib/etcd
# member

# 4. Take an etcd snapshot
ETCDCTL_API=3 etcdctl snapshot save /opt/snapshot-pre-boot.db \
  --endpoints=127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
# Snapshot saved at /opt/snapshot-pre-boot.db

# 5. Simulate data loss (maintenance gone wrong)
kubectl delete deploy blue red
kubectl get deploy
# No resources found in default namespace.

# 6. Restore from backup
ETCDCTL_API=3 etcdctl snapshot restore /opt/snapshot-pre-boot.db \
  --data-dir=/var/lib/etcd-from-backup

# 7. Update etcd static pod manifest to use restored data
# Edit /etc/kubernetes/manifests/etcd.yaml
# Change volumes.hostPath.path from /var/lib/etcd to /var/lib/etcd-from-backup
sudo vi /etc/kubernetes/manifests/etcd.yaml

# 8. Wait for etcd to restart with the restored data
kubectl get pods -n kube-system --watch
# Wait until etcd-controlplane shows 1/1 Running

# 9. Verify all resources are restored
kubectl get deploy
# NAME   READY   UP-TO-DATE   AVAILABLE   AGE
# blue   3/3     3            3           18s
# red    2/2     2            2           18s
```

### Exercise 2: Security Audit
```bash
# 1. Create a namespace with restricted Pod Security Standard
# 2. Try to create a privileged pod (should be rejected)
# 3. Create a properly secured pod
# 4. Apply a default-deny NetworkPolicy
# 5. Create allow rules for specific traffic
```

### Exercise 3: CKA Practice
```bash
# 1. Create a deployment with 3 replicas
# 2. Expose it as a NodePort service
# 3. Create a NetworkPolicy allowing only specific pods
# 4. Scale to 5 replicas
# 5. Perform a rolling update
# 6. Rollback to the previous version
# 7. Drain a node and verify pods are rescheduled
# Complete all tasks within 15 minutes
```

---

**This completes the Kubernetes course curriculum.**
