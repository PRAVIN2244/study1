# Module 10: Containers & Kubernetes (ACI, AKS, ACR)

## Certification Relevance: AZ-104, AZ-204

---

## 10.1 Container Concepts

```
VM vs Container:

Virtual Machine:                    Container:
┌─────────────────────┐            ┌─────────────────────┐
│ App A    │ App B    │            │ App A    │ App B    │
├──────────┼──────────┤            ├──────────┼──────────┤
│ Bins/Libs│ Bins/Libs│            │ Bins/Libs│ Bins/Libs│
├──────────┼──────────┤            ├──────────┴──────────┤
│ Guest OS │ Guest OS │            │   Container Runtime  │
├──────────┴──────────┤            │   (Docker)           │
│    Hypervisor       │            ├──────────────────────┤
├─────────────────────┤            │   Host OS            │
│    Host OS          │            ├──────────────────────┤
├─────────────────────┤            │   Hardware           │
│    Hardware         │            └──────────────────────┘
└─────────────────────┘

VM: Minutes to start, GBs in size, full OS isolation
Container: Seconds to start, MBs in size, process-level isolation
```

### Real-World Analogy
```
VMs = Houses (each has its own foundation, plumbing, electricity)
Containers = Apartments (share building infrastructure, isolated units)

Shipping containers analogy:
- A shipping container works on any ship, truck, or train
- A Docker container works on any machine with Docker installed
- "It works on my machine" → "It works everywhere"
```

---

## 10.2 Azure Container Registry (ACR)

### What is ACR?
A private Docker registry for storing and managing container images.

```bash
# Create a container registry
az acr create \
  --resource-group rg-demo-eastus \
  --name acrdemo2024 \
  --sku Basic \
  --admin-enabled true

# SKU options:
# Basic:    10 GB storage, 2 webhooks           (~$5/month)
# Standard: 100 GB storage, 10 webhooks         (~$20/month)
# Premium:  500 GB storage, geo-replication, private link (~$50/month)

# Login to ACR
az acr login --name acrdemo2024
# Output: Login Succeeded

# Tag and push a local image
docker tag myapp:latest acrdemo2024.azurecr.io/myapp:v1.0
docker push acrdemo2024.azurecr.io/myapp:v1.0

# Build image directly in ACR (no local Docker needed)
az acr build \
  --registry acrdemo2024 \
  --image myapp:v1.0 \
  --file Dockerfile .

# List images in registry
az acr repository list --name acrdemo2024 --output table
# Output:
# Result
# --------
# myapp
# api-service
# web-frontend

# List tags for an image
az acr repository show-tags --name acrdemo2024 --repository myapp --output table
# Output:
# Result
# --------
# v1.0
# v1.1
# latest

# Delete an image
az acr repository delete --name acrdemo2024 --image myapp:v1.0 --yes

# Get ACR credentials
az acr credential show --name acrdemo2024
```

---

## 10.3 Azure Container Instances (ACI)

### What is ACI?
The fastest way to run a container in Azure. No VMs to manage, no orchestration needed. Pay per second of execution.

### Portal UI Walkthrough: Create a Container Instance

```
PORTAL STEPS — Run a Container in ACI:

Step 1: Navigate to Container Instances
   → Search "Container instances" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   └────────────────────────────────────────────────────────┘
   ┌─ Container Details ────────────────────────────────────┐
   │ Container name:     my-nginx                            │
   │ Region:             East US                             │
   │ Availability zones: None                                │
   │ SKU:                Standard                            │
   │ Image source:       ● Other registry                    │
   │                     ○ Azure Container Registry          │
   │                     ○ Quick start images                │
   │ Image type:         ● Public                            │
   │ Image:              nginx:latest                        │
   │ OS type:            ● Linux  ○ Windows                  │
   │ Size:               1 vCPU, 1.5 GiB memory             │
   │   (click "Change size" to adjust)                       │
   └────────────────────────────────────────────────────────┘

Step 3: Networking Tab
   → Click "Next: Networking >"
   ┌─────────────────────────────────────────────────────────┐
   │ Networking type:    ● Public                             │
   │ DNS name label:     my-nginx-demo                        │
   │   (becomes my-nginx-demo.eastus.azurecontainer.io)      │
   │ Ports:              80 (TCP)                             │
   │   Click "+ Add port" for additional ports               │
   └─────────────────────────────────────────────────────────┘

Step 4: Advanced Tab
   → Click "Next: Advanced >"
   ┌─ Environment Variables ────────────────────────────────┐
   │ Click "+ Add"                                           │
   │ Name:  NGINX_HOST    Value: localhost                   │
   │ ☐ Mark as secure (hides value — for secrets)            │
   └────────────────────────────────────────────────────────┘

Step 5: Tags → Review + Create
   → Click "Review + create" → "Create"
   → Deployment takes 30-60 seconds

Step 6: Verify
   → Click "Go to resource"
   → Note the FQDN: my-nginx-demo.eastus.azurecontainer.io
   → Open browser → http://my-nginx-demo.eastus.azurecontainer.io
   → You'll see the Nginx welcome page!
   → Left sidebar → "Containers" → "Logs" to see container output
```

### Portal UI Walkthrough: Create an AKS Cluster

```
PORTAL STEPS — Create a Kubernetes Cluster:

Step 1: Navigate to Kubernetes Services
   → Search "Kubernetes services" in the search bar
   → Click "+ Create" → "Kubernetes cluster"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   └────────────────────────────────────────────────────────┘
   ┌─ Cluster Details ──────────────────────────────────────┐
   │ Cluster preset:     Dev/Test (cheapest)                 │
   │   Options: Dev/Test, Standard, Production               │
   │ Kubernetes cluster name: aks-demo                       │
   │ Region:             East US                             │
   │ Availability zones: None (for demo)                     │
   │ AKS pricing tier:   Free                                │
   │ Kubernetes version:  1.28.x (latest stable)             │
   │ Automatic upgrade:   Enabled with patch                 │
   └────────────────────────────────────────────────────────┘
   ┌─ Node Pool ────────────────────────────────────────────┐
   │ Node size:           Standard_B2s (2 vCPUs, 4 GiB)     │
   │   Click "Change size" to select                        │
   │ Scale method:        ● Manual  ○ Autoscale              │
   │ Node count:          2                                  │
   └────────────────────────────────────────────────────────┘

Step 3: Node Pools Tab
   → Click "Next: Node pools >"
   → Default node pool is already configured
   → Click "+ Add node pool" for additional pools:
     Name: userpool
     Mode: User
     OS: Linux
     Size: Standard_D2s_v5
     Node count: 1-5 (autoscale)

Step 4: Networking Tab
   → Click "Next: Networking >"
   → Network configuration: ● Azure CNI (recommended)
   → (Leave defaults for demo)

Step 5: Integrations Tab
   → Click "Next: Integrations >"
   → Container registry: Select your ACR (if created)
   → Azure Monitor: ☑ Enable container monitoring
   → (This enables Container Insights for monitoring)

Step 6: Review + Create
   → Click "Review + create" → "Create"
   → ⚠️ Deployment takes 5-10 minutes

Step 7: Connect to Your Cluster
   → Click "Go to resource"
   → Click "Connect" at the top
   → Follow the instructions:
     az account set --subscription <SUB_ID>
     az aks get-credentials --resource-group rg-demo-eastus --name aks-demo
     kubectl get nodes
   → You'll see your 2 nodes listed
```

```bash
# Run a container (simplest example)
az container create \
  --resource-group rg-demo-eastus \
  --name my-nginx \
  --image nginx:latest \
  --ports 80 \
  --dns-name-label my-nginx-demo \
  --location eastus

# Meaning:
# --image nginx:latest     : Docker image to run
# --ports 80               : Expose port 80
# --dns-name-label         : Creates my-nginx-demo.eastus.azurecontainer.io

# Output:
# {
#   "ipAddress": {
#     "fqdn": "my-nginx-demo.eastus.azurecontainer.io",
#     "ip": "20.185.100.60",
#     "ports": [{ "port": 80, "protocol": "TCP" }]
#   },
#   "provisioningState": "Succeeded"
# }

# Run container from ACR
az container create \
  --resource-group rg-demo-eastus \
  --name my-api \
  --image acrdemo2024.azurecr.io/myapp:v1.0 \
  --registry-login-server acrdemo2024.azurecr.io \
  --registry-username acrdemo2024 \
  --registry-password "ACR_PASSWORD" \
  --ports 3000 \
  --cpu 1 \
  --memory 1.5 \
  --environment-variables NODE_ENV=production API_KEY=secret123

# Meaning:
# --cpu 1          : 1 CPU core
# --memory 1.5     : 1.5 GB RAM
# --environment-variables : Set env vars in the container

# Check container status
az container show \
  --resource-group rg-demo-eastus \
  --name my-nginx \
  --query "{Status:instanceView.state, IP:ipAddress.ip, FQDN:ipAddress.fqdn}" \
  --output table

# View container logs
az container logs \
  --resource-group rg-demo-eastus \
  --name my-nginx

# Attach to container (live log stream)
az container attach \
  --resource-group rg-demo-eastus \
  --name my-nginx

# Execute command in running container
az container exec \
  --resource-group rg-demo-eastus \
  --name my-nginx \
  --exec-command "/bin/bash"

# Restart container
az container restart \
  --resource-group rg-demo-eastus \
  --name my-nginx

# Delete container
az container delete \
  --resource-group rg-demo-eastus \
  --name my-nginx \
  --yes
```

### Container Groups (Multi-Container)

```yaml
# deploy-aci.yaml - Deploy multiple containers together
apiVersion: 2021-09-01
type: Microsoft.ContainerInstance/containerGroups
name: my-app-group
location: eastus
properties:
  containers:
    - name: web
      properties:
        image: nginx:latest
        ports:
          - port: 80
        resources:
          requests:
            cpu: 0.5
            memoryInGb: 0.5
    - name: sidecar-logger
      properties:
        image: fluentd:latest
        resources:
          requests:
            cpu: 0.25
            memoryInGb: 0.25
  osType: Linux
  ipAddress:
    type: Public
    ports:
      - port: 80
```

```bash
# Deploy container group from YAML
az container create \
  --resource-group rg-demo-eastus \
  --file deploy-aci.yaml
```

---

## 10.4 Azure Kubernetes Service (AKS)

### What is AKS?
A managed Kubernetes service. Azure manages the control plane (API server, etcd, scheduler); you manage the worker nodes.

```
AKS Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    AKS CLUSTER                              │
│                                                             │
│  Control Plane (Managed by Azure - FREE):                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │API Server│ │  etcd    │ │Scheduler │ │Controller│     │
│  │          │ │(key-value│ │          │ │ Manager  │     │
│  │          │ │  store)  │ │          │ │          │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                             │
│  Worker Nodes (Managed by YOU - you pay for VMs):           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Node 1 (VM)      │  │ Node 2 (VM)      │                │
│  │ ┌──────┐ ┌──────┐│  │ ┌──────┐ ┌──────┐│                │
│  │ │Pod A │ │Pod B ││  │ │Pod C │ │Pod D ││                │
│  │ │(nginx)│ │(api) ││  │ │(api) │ │(db)  ││                │
│  │ └──────┘ └──────┘│  │ └──────┘ └──────┘│                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Creating an AKS Cluster

```bash
# Create an AKS cluster
az aks create \
  --resource-group rg-demo-eastus \
  --name aks-demo \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --generate-ssh-keys \
  --enable-managed-identity \
  --network-plugin azure

# Meaning:
# --node-count 2           : 2 worker nodes (VMs)
# --node-vm-size Standard_B2s : Each node: 2 vCPUs, 4 GB RAM
# --enable-managed-identity : Use managed identity (no service principal)
# --network-plugin azure   : Azure CNI networking (VNet integration)

# Takes 5-10 minutes to create

# Get credentials (configure kubectl)
az aks get-credentials \
  --resource-group rg-demo-eastus \
  --name aks-demo

# Output: Merged "aks-demo" as current context in /home/user/.kube/config

# Verify connection
kubectl get nodes
# Output:
# NAME                                STATUS   ROLES   AGE   VERSION
# aks-nodepool1-12345678-vmss000000   Ready    agent   5m    v1.28.3
# aks-nodepool1-12345678-vmss000001   Ready    agent   5m    v1.28.3

# Check cluster info
kubectl cluster-info
# Output:
# Kubernetes control plane is running at https://aks-demo-dns-abc123.hcp.eastus.azmk8s.io:443
```

### Deploying Applications to AKS

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web
          image: acrdemo2024.azurecr.io/myapp:v1.0
          ports:
            - containerPort: 3000
          resources:
            requests:
              cpu: "250m"      # 0.25 CPU cores
              memory: "256Mi"  # 256 MB RAM
            limits:
              cpu: "500m"
              memory: "512Mi"
          env:
            - name: NODE_ENV
              value: "production"
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
spec:
  type: LoadBalancer  # Creates Azure Load Balancer with public IP
  ports:
    - port: 80
      targetPort: 3000
  selector:
    app: web-app
```

```bash
# Deploy the application
kubectl apply -f deployment.yaml

# Output:
# deployment.apps/web-app created
# service/web-app-service created

# Check deployment status
kubectl get deployments
# Output:
# NAME      READY   UP-TO-DATE   AVAILABLE   AGE
# web-app   3/3     3            3           2m

# Check pods
kubectl get pods
# Output:
# NAME                       READY   STATUS    RESTARTS   AGE
# web-app-6d8f9b7c4d-abc12   1/1     Running   0          2m
# web-app-6d8f9b7c4d-def34   1/1     Running   0          2m
# web-app-6d8f9b7c4d-ghi56   1/1     Running   0          2m

# Get service external IP
kubectl get service web-app-service
# Output:
# NAME              TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)
# web-app-service   LoadBalancer   10.0.100.50   20.185.100.70   80:31234/TCP

# Scale deployment
kubectl scale deployment web-app --replicas=5

# View pod logs
kubectl logs web-app-6d8f9b7c4d-abc12

# Execute command in pod
kubectl exec -it web-app-6d8f9b7c4d-abc12 -- /bin/sh

# Delete deployment
kubectl delete -f deployment.yaml
```

### AKS Scaling

```bash
# Manual node scaling
az aks scale \
  --resource-group rg-demo-eastus \
  --name aks-demo \
  --node-count 5

# Enable cluster autoscaler
az aks update \
  --resource-group rg-demo-eastus \
  --name aks-demo \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10

# Meaning: Automatically add/remove nodes based on pod demand
# If pods can't be scheduled (not enough resources) → add node
# If nodes are underutilized → remove node

# Horizontal Pod Autoscaler (scale pods, not nodes)
kubectl autoscale deployment web-app \
  --min=2 \
  --max=20 \
  --cpu-percent=70
# Meaning: Scale pods between 2-20 based on CPU usage (target 70%)
```

### Attach ACR to AKS

```bash
# Allow AKS to pull images from ACR
az aks update \
  --resource-group rg-demo-eastus \
  --name aks-demo \
  --attach-acr acrdemo2024

# Meaning: Grants AKS managed identity the AcrPull role on the registry
# No more image pull secrets needed
```

---

## 10.5 ACI vs AKS Decision Guide

```
Use ACI when:                        Use AKS when:
├── Simple, single-container apps    ├── Complex multi-container apps
├── Batch jobs / task runners        ├── Microservices architecture
├── Dev/test environments            ├── Need auto-scaling
├── Event-driven processing          ├── Service discovery needed
├── Quick prototyping                ├── Rolling updates required
└── Cost: Pay per second             └── Cost: Pay for VMs (nodes)

ACI: "I need to run a container quickly"
AKS: "I need to orchestrate many containers at scale"
```

---

## 10.6 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ImagePullBackOff` | Can't pull image from registry | Check image name, ACR credentials, or attach ACR to AKS |
| `CrashLoopBackOff` | Container keeps crashing | Check logs: `kubectl logs POD_NAME` |
| `Pending` pod | Not enough resources on nodes | Scale nodes or reduce resource requests |
| `ErrImagePull` | Image doesn't exist in registry | Verify image: `az acr repository list` |
| `Forbidden` kubectl | Wrong credentials | Re-run: `az aks get-credentials` |
| ACI `ContainerCreationFailed` | Invalid image or insufficient quota | Check image name; request quota increase |
| `NodeNotReady` | Node health issue | Check: `kubectl describe node NODE_NAME` |
| `OOMKilled` | Container exceeded memory limit | Increase memory limits in deployment spec |

```bash
# Debugging AKS pods
kubectl describe pod POD_NAME          # Detailed pod info
kubectl logs POD_NAME                  # Container logs
kubectl logs POD_NAME --previous       # Logs from crashed container
kubectl get events --sort-by='.lastTimestamp'  # Recent cluster events
kubectl top pods                       # CPU/memory usage per pod
kubectl top nodes                      # CPU/memory usage per node
```

---

## 10.7 Practice Questions

### Question 1
**Which service runs a single container without managing infrastructure?**
- A) AKS
- B) ACI ✅
- C) ACR
- D) App Service

### Question 2
**In AKS, who manages the control plane?**
- A) The customer
- B) Microsoft Azure ✅
- C) A third-party vendor
- D) No one, it's serverless

### Question 3
**What Kubernetes resource exposes pods to external traffic with a public IP?**
- A) Deployment
- B) Pod
- C) Service (type: LoadBalancer) ✅
- D) ConfigMap

### Question 4
**What does `az aks update --attach-acr` do?**
- A) Creates a new ACR
- B) Grants AKS permission to pull images from ACR ✅
- C) Pushes images to ACR
- D) Deletes ACR images

### Question 5
**A pod is in `CrashLoopBackOff` status. What should you check first?**
- A) Node status
- B) Container logs ✅
- C) Network policies
- D) Storage classes

---

[← Previous Module](./Module-09-DevOps-CICD.md) | [Next Module: Serverless →](./Module-11-Serverless.md)
