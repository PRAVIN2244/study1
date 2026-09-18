# MODULE 6: Setting Up a Kubernetes Cluster

---

## 6.1 Local Kubernetes Setup with Minikube

### What is Minikube?

Minikube runs a single-node Kubernetes cluster on your local machine. It installs all control plane and worker components (API Server, etcd, Scheduler, Controller Manager, CoreDNS, kubelet, kube-proxy) inside one machine.

Minikube can run inside:
- A VM (VirtualBox, KVM)
- A Docker container
- Bare-metal (`--vm-driver=none`)

Requires a machine with at least 2 CPUs (e.g., AWS t2.medium).

**Minikube is for learning only — not for production.** For multi-node local clusters use Kind. For production use EKS, AKS, or GKE.

### Step 1 — Install Docker

```bash
sudo apt update
```

Updates the package list from Ubuntu repositories. You should see output like:

```
Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease
Reading package lists... Done
```

```bash
sudo apt -y install docker.io
```

Installs Docker and its dependencies (containerd, runc). The `-y` flag auto-confirms the installation prompt.

```
The following NEW packages will be installed:
  docker.io containerd runc
After this operation, 286 MB of additional disk space will be used.
Setting up docker.io (20.10.12-0ubuntu4) ...
```

**Verify Docker is running:**

```bash
docker --version

# Output:
# Docker version 20.10.12, build e91ed57

sudo systemctl status docker

# Output (key line):
# Active: active (running)
```

If Docker is not running: `sudo systemctl start docker`

### Step 2 — Install kubectl

```bash
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.23.7/bin/linux/amd64/kubectl
```

`curl -LO` downloads the kubectl binary. `-L` follows redirects, `-O` saves with the original filename.

```bash
chmod +x ./kubectl
```

Makes the downloaded file executable.

```bash
sudo mv ./kubectl /usr/local/bin/kubectl
```

Moves kubectl to a directory in the system PATH so it can be run from anywhere.

**Verify kubectl:**

```bash
kubectl version --client

# Output:
# Client Version: v1.23.7
```

At this point no cluster exists yet. If you run `kubectl get nodes`, you get:

```
The connection to the server localhost:8080 was refused
```

This is expected — kubectl has no cluster to connect to.

### Step 3 — Install Minikube

```bash
curl -Lo minikube https://storage.googleapis.com/minikube/releases/v1.23.2/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/
```

Same pattern as kubectl: download → make executable → move to PATH.

```bash
minikube version

# Output:
# minikube version: v1.23.2
```

### Step 4 — Install conntrack

```bash
sudo apt install conntrack
```

Kubernetes networking requires connection tracking (conntrack) to manage iptables rules for Service routing. Without it, Minikube fails with:

```
Error: conntrack not found
```

### Step 5 — Start Minikube

```bash
minikube start --vm-driver=none
```

`--vm-driver=none` runs Kubernetes directly on the host (no VM). This requires root privileges.

**What happens internally when Minikube starts:**

1. Pulls Kubernetes container images (API Server, etcd, etc.)
2. Generates TLS certificates for secure communication
3. Starts all control plane components as static pods
4. Starts kubelet as a systemd service
5. Configures `~/.kube/config` with cluster connection details
6. Sets the kubectl context to `minikube`

```
😄  minikube v1.23.2 on Ubuntu 22.04
✨  Using the none driver
🚀  Starting control plane node minikube
🔄  Pulling base image ...
📦  Preparing Kubernetes v1.22.3 on Docker
🔥  Creating kubernetes cluster
🌟  Done! kubectl is now configured
```

### Step 6 — Verify the Cluster

```bash
minikube status

# Output:
# host: Running
# kubelet: Running
# apiserver: Running
# kubeconfig: Configured
```

All four lines should show `Running` or `Configured`.

```bash
kubectl get nodes

# Output:
# NAME       STATUS   ROLES                  AGE   VERSION
# minikube   Ready    control-plane,master   2m    v1.22.3
```

- `Ready` — the node is healthy and can accept pods
- `control-plane,master` — this node runs both control plane and workloads (single-node cluster)

### Step 7 — Verify System Components

```bash
kubectl get pods -n kube-system

# Output:
# NAME                               READY   STATUS    RESTARTS   AGE
# coredns-64897985d-rxk7b            1/1     Running   0          2m
# etcd-minikube                      1/1     Running   0          2m
# kube-apiserver-minikube            1/1     Running   0          2m
# kube-controller-manager-minikube   1/1     Running   0          2m
# kube-scheduler-minikube            1/1     Running   0          2m
# kube-proxy-xxxxx                   1/1     Running   0          2m
```

These are the control plane components running as pods in the `kube-system` namespace.

### Understanding kubeconfig

kubectl reads connection details from `~/.kube/config`. This file contains:

```bash
cat ~/.kube/config
```

Key sections:
- **clusters** — API server URL and CA certificate
- **users** — client certificate and key for authentication
- **contexts** — maps a cluster + user + namespace together
- **current-context** — which context kubectl uses by default

```bash
kubectl config current-context

# Output:
# minikube
```

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | Docker service not running | `sudo systemctl start docker` |
| `Port 8443 is already allocated` | Previous Minikube instance still running | `minikube delete` then restart |
| `The requested memory allocation is higher than available` | Insufficient resources | `minikube start --memory=4096 --cpus=2` |
| `conntrack not found` | conntrack package not installed | `sudo apt install conntrack` |
| `The connection to the server localhost:8080 was refused` | No cluster running or kubeconfig not set | Start Minikube or check `~/.kube/config` |

### Quick Verification Test

```bash
# Create a test pod
kubectl run test --image=nginx

# Verify it's running
kubectl get pods

# Output:
# NAME   READY   STATUS    RESTARTS   AGE
# test   1/1     Running   0          10s

# Clean up
kubectl delete pod test
```

If the pod reaches `Running` status, the cluster is fully functional.

---


---

## 6.2 Local Multi-Node Cluster with Kind

Kind (Kubernetes IN Docker) runs multi-node clusters locally using Docker containers as nodes. Useful for testing multi-node scenarios without cloud costs. Requires a machine with at least 4 CPUs and 16GB RAM (e.g., AWS t3a.xlarge).

```bash
# Install Docker
sudo apt update && sudo apt -y install docker.io
sudo usermod -a -G docker ubuntu

# Install kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.23.7/bin/linux/amd64/kubectl \
  && chmod +x ./kubectl && sudo mv ./kubectl /usr/local/bin/kubectl

# Install Kind
sudo curl -L "https://kind.sigs.k8s.io/dl/v0.20.0/kind-$(uname)-amd64" -o /usr/local/bin/kind \
  && sudo chmod +x /usr/local/bin/kind
```

```yaml
# multi-node.yml — Kind cluster config with 1 control plane + 2 workers
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    listenAddress: "0.0.0.0"
    protocol: TCP
- role: worker
- role: worker
```

```bash
# Create the cluster
kind create cluster --name wezvatechdemo --config=multi-node.yml

# Verify
kubectl get nodes

# Output:
# NAME                          STATUS   ROLES           AGE   VERSION
# wezvatechdemo-control-plane   Ready    control-plane   1m    v1.27.3
# wezvatechdemo-worker          Ready    <none>          45s   v1.27.3
# wezvatechdemo-worker2         Ready    <none>          45s   v1.27.3

# Delete the cluster when done
kind delete cluster --name wezvatechdemo
```

The `extraPortMappings` configuration maps NodePort 30080 inside the cluster to port 30080 on the host, allowing access to NodePort services from outside the Docker network.

---


---

## 6.3 Production Cluster Setup with kubeadm

kubeadm is the official tool for bootstrapping production-grade Kubernetes clusters on your own infrastructure (VMs, bare-metal, cloud instances).

### Prerequisites

| Component | Control Plane | Worker Node |
|---|---|---|
| CPU | 2+ cores | 1+ core |
| RAM | 2+ GB | 1+ GB |
| OS | Ubuntu 20.04/22.04, CentOS 7/8 | Same |
| Network | Unique hostname, MAC, product_uuid per node | Same |
| Ports | 6443, 2379-2380, 10250-10252 | 10250, 30000-32767 |

### Step 1 — Install Container Runtime (All Nodes)

```bash
# Install containerd
sudo apt update
sudo apt install -y containerd

# Configure containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable SystemdCgroup (required for kubeadm)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd

# Disable swap (Kubernetes requirement)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load required kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# Set required sysctl params
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system
```

### Step 2 — Install kubeadm, kubelet, kubectl (All Nodes)

```bash
# Add Kubernetes apt repository
sudo apt install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install specific version
sudo apt update
sudo apt install -y kubelet=1.29.0-1.1 kubeadm=1.29.0-1.1 kubectl=1.29.0-1.1

# Prevent automatic upgrades
sudo apt-mark hold kubelet kubeadm kubectl
```

### Step 3 — Initialize Control Plane (Master Node Only)

```bash
sudo kubeadm init \
  --pod-network-cidr=192.168.0.0/16 \
  --kubernetes-version=v1.29.0

# Output includes:
# Your Kubernetes control-plane has initialized successfully!
#
# To start using your cluster, you need to run as a regular user:
#   mkdir -p $HOME/.kube
#   sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
#   sudo chown $(id -u):$(id -g) $HOME/.kube/config
#
# Then you can join any number of worker nodes by running:
#   kubeadm join 10.0.1.100:6443 --token abcdef.1234567890abcdef \
#     --discovery-token-ca-cert-hash sha256:abc123...

# Configure kubectl for the current user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### Step 4 — Install CNI Plugin (Master Node)

```bash
# Install Calico (most common for production)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.3/manifests/calico.yaml

# Verify nodes become Ready
kubectl get nodes --watch

# Output:
# NAME       STATUS   ROLES           AGE   VERSION
# master     Ready    control-plane   2m    v1.29.0
```

Without a CNI plugin, nodes stay in `NotReady` status because pod networking is not configured.

### Step 5 — Join Worker Nodes

Run the `kubeadm join` command from Step 3 output on each worker node:

```bash
# On each worker node (as root)
sudo kubeadm join 10.0.1.100:6443 \
  --token abcdef.1234567890abcdef \
  --discovery-token-ca-cert-hash sha256:abc123...

# If token expired, generate a new one on the master:
kubeadm token create --print-join-command
```

```bash
# Verify on master
kubectl get nodes

# Output:
# NAME       STATUS   ROLES           AGE   VERSION
# master     Ready    control-plane   5m    v1.29.0
# worker-1   Ready    <none>          1m    v1.29.0
# worker-2   Ready    <none>          1m    v1.29.0
```

### Common kubeadm Errors

| Error | Cause | Fix |
|---|---|---|
| `[ERROR Swap]: running with swap on is not supported` | Swap not disabled | `sudo swapoff -a` |
| `[ERROR Port-6443]: Port 6443 is in use` | Previous init not cleaned up | `sudo kubeadm reset` then retry |
| `[ERROR CRI]: container runtime is not running` | containerd not started | `sudo systemctl restart containerd` |
| `node not ready` after join | CNI plugin not installed | Install Calico/Flannel on master |
| `token expired` | Join token has 24h TTL | `kubeadm token create --print-join-command` |

### kubeadm vs Minikube vs Kind vs EKS

| Feature | kubeadm | Minikube | Kind | EKS |
|---|---|---|---|---|
| **Use case** | Production self-managed | Local learning | Local multi-node testing | Production AWS |
| **Nodes** | Multi-node | Single-node | Multi-node (Docker) | Multi-node |
| **Control plane** | You manage | Auto-managed | Auto-managed | AWS manages |
| **Networking** | You install CNI | Pre-configured | Pre-configured | VPC-CNI |
| **Upgrades** | Manual (kubeadm upgrade) | `minikube start --kubernetes-version` | Recreate cluster | `eksctl upgrade` |

### Designing a Kubernetes Cluster

Choose your cluster topology based on the use case:

| Purpose | Topology | Tools |
|---|---|---|
| **Learning** | Single-node | Minikube, Kind, Docker Desktop |
| **Development/Testing** | 1 master + 2-3 workers | kubeadm, Kind, managed cloud (EKS/GKE/AKS) |
| **Production** | 3+ masters (HA) + N workers | kubeadm with HA, EKS, GKE, AKS |

**Kubernetes cluster scale limits:**

| Resource | Maximum |
|---|---|
| Nodes per cluster | 5,000 |
| Total pods | 150,000 |
| Total containers | 300,000 |
| Pods per node | 100 |

**Production cluster design decisions:**

- **Control plane nodes** — dedicate them to control plane components only (API server, controller manager, scheduler, etcd). kubeadm taints master nodes by default to prevent workload scheduling.
- **etcd topology** — **stacked** (etcd runs on control plane nodes, simpler) vs **external** (etcd on dedicated nodes, better isolation and HA for large clusters).
- **Node sizing** — match instance types to workload profiles. CPU-intensive workloads need compute-optimized instances; memory-heavy workloads need memory-optimized instances.
- **Storage** — use SSD-backed storage for high-performance workloads (databases), network-based storage (EBS, EFS, NFS) for shared access across pods, and persistent volumes for stateful applications.

**Turnkey vs Hosted solutions:**

| Approach | You manage | Provider manages | Examples |
|---|---|---|---|
| **Self-managed** | Everything (VMs, K8s, networking, upgrades) | Nothing | kubeadm on bare-metal/VMs |
| **Turnkey** | VMs, OS patching, upgrades | Deployment automation | OpenShift, Rancher, kOps on AWS |
| **Hosted/Managed** | Application workloads only | VMs, control plane, upgrades, HA | EKS, GKE, AKS |

For most teams, managed services (EKS, GKE, AKS) are the right choice — they eliminate control plane management overhead. Use self-managed clusters when you need full control over the infrastructure (air-gapped environments, specific compliance requirements, on-premises).

---

