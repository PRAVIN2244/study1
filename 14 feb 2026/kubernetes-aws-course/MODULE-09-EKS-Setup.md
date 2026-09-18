# MODULE 9: Amazon EKS Setup

---

## 9.1 What is Amazon EKS?

Amazon Elastic Kubernetes Service (EKS) is a managed Kubernetes service that runs the Kubernetes control plane across multiple AWS Availability Zones. AWS manages the control plane (API server, etcd, scheduler, controller manager) — you manage the worker nodes.

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS MANAGES (EKS)                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              CONTROL PLANE (Multi-AZ)                │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │    │
│  │  │API Server│ │Scheduler │ │Controller│            │    │
│  │  │  (HA)    │ │  (HA)    │ │Manager   │            │    │
│  │  └──────────┘ └──────────┘ └──────────┘            │    │
│  │  ┌──────────────────────────────────────┐           │    │
│  │  │     etcd (3 nodes, encrypted)        │           │    │
│  │  └──────────────────────────────────────┘           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│                     YOU MANAGE                               │
│  ┌──────────── AZ-1a ──────┐  ┌──────── AZ-1b ──────────┐  │
│  │  Worker Node (EC2)       │  │  Worker Node (EC2)       │  │
│  │  ┌─Pod─┐ ┌─Pod─┐       │  │  ┌─Pod─┐ ┌─Pod─┐       │  │
│  │  └─────┘ └─────┘       │  │  └─────┘ └─────┘       │  │
│  └──────────────────────────┘  └──────────────────────────┘  │
│                                                             │
│  ┌──────── AZ-1c ──────────┐                                │
│  │  Worker Node (EC2)       │   OR: AWS Fargate (Serverless) │
│  │  ┌─Pod─┐ ┌─Pod─┐       │                                │
│  │  └─────┘ └─────┘       │                                │
│  └──────────────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### EKS vs Self-Managed Kubernetes

| Feature | EKS | Self-Managed (kubeadm) |
|---|---|---|
| Control plane management | AWS managed | You manage |
| Upgrades | Automated | Manual |
| High availability | Built-in (multi-AZ) | You configure |
| Cost | $0.10/hr (~$73/month) + nodes | Only node costs |
| IAM integration | Native | Manual setup |
| Monitoring | CloudWatch integration | Self-configured |
| Best for | Production workloads | Learning, cost-sensitive |

### Node Types on EKS

| Type | Description | Best For |
|---|---|---|
| **Managed Node Groups** | AWS manages EC2 instances | Most workloads |
| **Self-Managed Nodes** | You manage EC2 instances | Custom AMIs, GPU |
| **Fargate** | Serverless, no EC2 to manage | Batch jobs, microservices |

---

## 9.2 Prerequisites Setup

Three CLIs are needed to manage EKS: **AWS CLI** (manage AWS resources), **kubectl** (manage Kubernetes clusters), and **eksctl** (create/manage EKS clusters).

### Install AWS CLI

Reference: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html

#### Mac

```bash
# Download the binary
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# Install
sudo installer -pkg ./AWSCLIV2.pkg -target /

# Verify
aws --version
# Output: aws-cli/2.0.7 Python/3.7.4 Darwin/19.4.0 botocore/2.0.0dev11

which aws
```

#### Linux

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
# Output: aws-cli/2.15.0 Python/3.11.6 Linux/5.10.192 exe/x86_64.amzn.2
```

#### Windows

Download and run the MSI installer: https://awscli.amazonaws.com/AWSCLIV2.msi

```bash
# Verify after install
aws --version
# Output: aws-cli/2.0.8 Python/3.7.5 Windows/10 botocore/2.0.0dev12
```

#### Configure AWS Credentials

⚠️ Use only an IAM user to generate security credentials. Never use the Root User (highly not recommended).

1. Go to AWS Console → IAM → Select your IAM user → Security credentials → Create access key
2. Copy the Access Key ID and Secret Access Key
3. Run:

```bash
aws configure
# AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# Default region name [None]: us-east-1
# Default output format [None]: json

# Verify credentials work
aws sts get-caller-identity

# Output:
# {
#     "UserId": "AIDAIOSFODNN7EXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/k8s-admin"
# }

# Test with a real API call
aws ec2 describe-vpcs
```

### Install kubectl

⚠️ For EKS, prefer the **Amazon EKS-vended kubectl binary**. This ensures the kubectl client version matches your EKS cluster version.

Reference: https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html

#### Mac

```bash
# Create a directory for the binary
mkdir kubectlbinary && cd kubectlbinary

# Download the EKS-vended kubectl (version should match your EKS cluster)
curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.16.8/2020-04-16/bin/darwin/amd64/kubectl

# Make it executable
chmod +x ./kubectl

# Set up PATH by copying to user home bin directory
mkdir -p $HOME/bin && cp ./kubectl $HOME/bin/kubectl && export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bash_profile

# Verify
kubectl version --short --client
# Output: Client Version: v1.16.8-eks-e16311
```

**PATH setup explained:**

| Command | What It Does |
|---|---|
| `mkdir -p $HOME/bin` | Creates `~/bin` directory if it doesn't exist |
| `cp ./kubectl $HOME/bin/kubectl` | Copies the kubectl binary to `~/bin` |
| `export PATH=$PATH:$HOME/bin` | Adds `~/bin` to PATH for the current session |
| `echo '...' >> ~/.bash_profile` | Persists the PATH change across sessions |

To apply changes immediately without restarting the terminal:

```bash
source ~/.bash_profile
```

⚠️ On Ubuntu/Debian, use `~/.bashrc` instead of `~/.bash_profile`:

```bash
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
source ~/.bashrc
```

#### Linux

```bash
# Install kubectl (latest stable)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client --short
# Output: Client Version: v1.28.2
```

#### Windows

```bash
# Create directory and download
mkdir kubectlbinary
cd kubectlbinary
curl -o kubectl.exe https://amazon-eks.s3.us-west-2.amazonaws.com/1.16.8/2020-04-16/bin/windows/amd64/kubectl.exe

# Add the directory to your system PATH environment variable
# Example: C:\Users\YOURNAME\Documents\kubectlbinary

# Verify
kubectl version --short --client
kubectl version --client
```

### Install eksctl

`eksctl` is the official CLI tool for creating and managing EKS clusters.

Reference: https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html

#### Mac (Homebrew)

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

# Install the Weaveworks Homebrew tap
brew tap weaveworks/tap

# Install eksctl
brew install weaveworks/tap/eksctl

# Verify
eksctl version
```

#### Linux

```bash
# Install eksctl
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify
eksctl version
# Output: 0.167.0
```

#### Windows

For Windows, refer to the official documentation: https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html#installing-eksctl

### Install Helm (Package Manager for K8s)

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify
helm version

# Output:
# version.BuildInfo{Version:"v3.13.2", GitCommit:"...", GoVersion:"go1.21.4"}
```

---

## 9.3 Creating an EKS Cluster

### Method 1: Using eksctl (Recommended for Learning)

```bash
# Simple cluster creation
eksctl create cluster \
  --name my-k8s-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed

# Command breakdown:
# --name              : Cluster name
# --region            : AWS region
# --version           : Kubernetes version
# --nodegroup-name    : Name for the worker node group
# --node-type         : EC2 instance type (t3.medium = 2 vCPU, 4GB RAM)
# --nodes             : Desired number of nodes
# --nodes-min/max     : Auto-scaling range
# --managed           : Use EKS managed node groups

# Output (takes 15-20 minutes):
# 2024-01-15 10:00:00 [ℹ]  eksctl version 0.167.0
# 2024-01-15 10:00:00 [ℹ]  using region us-east-1
# 2024-01-15 10:00:01 [ℹ]  setting availability zones to [us-east-1a us-east-1b us-east-1c]
# 2024-01-15 10:00:01 [ℹ]  subnets for us-east-1a - public:10.0.0.0/19 private:10.0.96.0/19
# 2024-01-15 10:00:01 [ℹ]  subnets for us-east-1b - public:10.0.32.0/19 private:10.0.128.0/19
# 2024-01-15 10:00:01 [ℹ]  subnets for us-east-1c - public:10.0.64.0/19 private:10.0.160.0/19
# 2024-01-15 10:00:02 [ℹ]  using Kubernetes version 1.28
# 2024-01-15 10:00:02 [ℹ]  creating EKS cluster "my-k8s-cluster" in "us-east-1" region
# ...
# 2024-01-15 10:15:30 [ℹ]  node "ip-10-0-1-100.ec2.internal" is ready
# 2024-01-15 10:15:30 [ℹ]  node "ip-10-0-2-200.ec2.internal" is ready
# 2024-01-15 10:15:30 [ℹ]  node "ip-10-0-3-300.ec2.internal" is ready
# 2024-01-15 10:15:31 [✔]  EKS cluster "my-k8s-cluster" in "us-east-1" region is ready
```

### Step-by-Step: Create EKS Cluster Without Node Group

This approach creates the control plane first, then adds node groups separately. This gives you more control over node group configuration and IAM policies.

**Step 1: Create the EKS cluster (control plane only)**

Takes 15–20 minutes to provision the control plane.

```bash
eksctl create cluster --name=eksdemo1 \
                      --region=us-east-1 \
                      --zones=us-east-1a,us-east-1b \
                      --without-nodegroup
```

| Flag | Purpose |
|---|---|
| `--name=eksdemo1` | Name of the EKS cluster |
| `--region=us-east-1` | AWS region for deployment |
| `--zones=us-east-1a,us-east-1b` | Availability zones for the control plane |
| `--without-nodegroup` | Creates cluster without worker nodes — add them separately |

**What happens after running this:**
- EKS control plane is provisioned (API server, managed Kubernetes components)
- Cluster is created in the specified availability zones
- No worker nodes (EC2 instances) are attached — you add a node group next
- The API endpoint is accessible via internet (`PublicAccess=true` by default)
- kubeconfig is automatically updated in `~/.kube/config`

```bash
# Verify the cluster was created
eksctl get cluster
```

**Step 2: Create and associate IAM OIDC Provider**

To use AWS IAM roles with Kubernetes service accounts (IRSA), you must create and associate an OIDC identity provider with the cluster.

```bash
# Template
eksctl utils associate-iam-oidc-provider \
    --region region-code \
    --cluster <cluster-name> \
    --approve

# For our cluster
eksctl utils associate-iam-oidc-provider \
    --region us-east-1 \
    --cluster eksdemo1 \
    --approve
```

This single command replaces multiple manual steps in the AWS Management Console. Without OIDC, pods cannot assume IAM roles via service accounts.

**Step 3: Create EC2 Keypair**

Create a new EC2 keypair named `kube-demo` in the AWS Console (EC2 → Key Pairs → Create key pair). This keypair is used when creating the node group, allowing SSH access to worker nodes for troubleshooting.

**Step 4: Create Node Group with Add-On IAM Policies**

The add-on flags automatically create the required IAM policies in the node group's IAM role.

```bash
eksctl create nodegroup --cluster=eksdemo1 \
                       --region=us-east-1 \
                       --name=eksdemo1-ng-public1 \
                       --node-type=t3.medium \
                       --nodes=2 \
                       --nodes-min=2 \
                       --nodes-max=4 \
                       --node-volume-size=20 \
                       --ssh-access \
                       --ssh-public-key=kube-demo \
                       --managed \
                       --asg-access \
                       --external-dns-access \
                       --full-ecr-access \
                       --appmesh-access \
                       --alb-ingress-access
```

**Node Group parameters:**

| Option | Description |
|---|---|
| `--cluster=eksdemo1` | Associates the node group with the eksdemo1 cluster |
| `--region=us-east-1` | AWS region |
| `--name=eksdemo1-ng-public1` | Name of the node group |
| `--node-type=t3.medium` | EC2 instance type (2 vCPU, 4GB RAM) |
| `--nodes=2` | Initial number of worker nodes |
| `--nodes-min=2` | Minimum nodes (auto-scaling lower bound) |
| `--nodes-max=4` | Maximum nodes (auto-scaling upper bound) |
| `--node-volume-size=20` | 20GB EBS disk per node |
| `--ssh-access` | Enables SSH access to worker nodes |
| `--ssh-public-key=kube-demo` | EC2 keypair name for SSH |
| `--managed` | AWS manages lifecycle, patching, and auto-upgrading |
| `--asg-access` | IAM policy for Cluster Autoscaler (Auto Scaling Group access) |
| `--external-dns-access` | IAM policy for ExternalDNS (Route 53 DNS registration with Ingress/LB) |
| `--full-ecr-access` | IAM policy for full Amazon ECR access (pull/push images) |
| `--appmesh-access` | IAM policy for AWS App Mesh (service-to-service communication) |
| `--alb-ingress-access` | IAM policy for AWS ALB Ingress Controller |

```bash
# See all available options
eksctl create nodegroup --help
```

**Two ways to grant AWS access to pods:**
1. **IRSA (recommended)** — Create a Kubernetes ServiceAccount, create an IAM role, associate them together, and set `serviceAccountName` in the pod spec. Each pod gets least-privilege access.
2. **Node IAM role** — Add policies directly to the worker node IAM role. All pods on that node inherit the same permissions. Less secure but simpler.

**Step 5: Verify Cluster and Nodes**

```bash
# List EKS clusters
eksctl get cluster

# List node groups in the cluster
eksctl get nodegroup --cluster=eksdemo1

# List worker nodes
kubectl get nodes -o wide

# Verify kubectl context was automatically set to the new cluster
kubectl config view --minify
```

**Verify node group subnets (confirm public subnet):**

1. Go to AWS Console → EKS → eksdemo1 → eksdemo1-ng-public1
2. Click "Associated subnet" in the Details tab
3. Click "Route Table" tab
4. Confirm internet route: `0.0.0.0/0 → igw-xxxxxxxx` (Internet Gateway = public subnet)

**Public vs Private subnet routing:**

| Subnet Type | Route for `0.0.0.0/0` | Internet Access |
|---|---|---|
| Public | `→ igw-xxxxxxxx` (Internet Gateway) | Direct internet access |
| Private | `→ nat-xxxxxxxx` (NAT Gateway) | Outbound only via NAT |

**Verify Worker Node IAM Role:**

1. Go to AWS Console → EC2 → select a worker node instance
2. Click the IAM Role associated with the instance
3. Verify the attached policies (created by the add-on flags):
   - Auto Scaling Group policy (`--asg-access`)
   - ExternalDNS policy (`--external-dns-access`)
   - ECR full access policy (`--full-ecr-access`)
   - App Mesh policy (`--appmesh-access`)
   - ALB Ingress policy (`--alb-ingress-access`)

**Verify Security Group:**

1. Go to AWS Console → EC2 → select a worker node
2. Click the Security Group that contains "remote" in the name
3. This controls SSH and inter-node communication

**Verify CloudFormation Stacks:**

eksctl uses CloudFormation under the hood. Check both stacks:
- Control Plane stack — `eksctl-eksdemo1-cluster`
- Node Group stack — `eksctl-eksdemo1-nodegroup-eksdemo1-ng-public1`

**SSH into a Worker Node:**

```bash
# Mac / Linux / Windows 10
ssh -i kube-demo.pem ec2-user@<Public-IP-of-Worker-Node>

# For Windows 7 — use PuTTY
```

**Step 6: Update Worker Node Security Group**

Allow all traffic on the worker node security group. NodePort services use dynamic ports in the range 30000–32767, which need to be accessible:

1. Go to AWS Console → EC2 → Security Groups
2. Find the security group associated with worker nodes
3. Add inbound rule: All Traffic from your IP (or 0.0.0.0/0 for testing)

### Deleting EKS Cluster and Node Groups

**Step 1: Delete Node Group first**

```bash
# List clusters
eksctl get clusters

# List node groups
eksctl get nodegroup --cluster=eksdemo1

# Delete the node group
eksctl delete nodegroup --cluster=eksdemo1 --name=eksdemo1-ng-public1
```

**Step 2: Delete the Cluster**

```bash
eksctl delete cluster eksdemo1
```

⚠️ **Before deleting — rollback these changes to avoid deletion failures:**

| What to Rollback | Why |
|---|---|
| **Security Group changes** | eksctl creates worker node SG with only port 22. If you added NodePort rules (30000–32767), remove them before deletion. Otherwise CloudFormation stack deletion may fail. |
| **Worker Node IAM Role policy changes** | If you added custom policies (e.g., EBS CSI Driver policy) to the worker node IAM role, remove them first. Otherwise the IAM role can't be deleted and the stack hangs. |

If deletion fails, check CloudFormation events in the AWS Console and manually delete stuck resources.

### Method 2: Using eksctl with Config File (Production)

```yaml
# cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: production-cluster
  region: us-east-1
  version: "1.28"

# VPC Configuration
vpc:
  cidr: 10.0.0.0/16
  nat:
    gateway: HighlyAvailable  # One NAT gateway per AZ

# IAM OIDC provider for service accounts
iam:
  withOIDC: true

# Managed Node Groups
managedNodeGroups:
  - name: general-purpose
    instanceType: t3.large
    desiredCapacity: 3
    minSize: 2
    maxSize: 10
    volumeSize: 50
    volumeType: gp3
    labels:
      role: general
    tags:
      Environment: production
      Team: platform
    iam:
      withAddonPolicies:
        albIngress: true
        cloudWatch: true
        ebs: true

  - name: compute-intensive
    instanceType: c5.2xlarge
    desiredCapacity: 2
    minSize: 0
    maxSize: 5
    volumeSize: 100
    labels:
      role: compute
    taints:
      - key: workload
        value: compute
        effect: NoSchedule

# Fargate Profiles (serverless pods)
fargateProfiles:
  - name: batch-jobs
    selectors:
      - namespace: batch
        labels:
          compute: fargate

# CloudWatch Logging
cloudWatch:
  clusterLogging:
    enableTypes:
      - api
      - audit
      - authenticator
      - controllerManager
      - scheduler

# Addons
addons:
  - name: vpc-cni
    version: latest
  - name: coredns
    version: latest
  - name: kube-proxy
    version: latest
  - name: aws-ebs-csi-driver
    version: latest
```

```bash
# Create cluster from config file
eksctl create cluster -f cluster-config.yaml

# Output:
# 2024-01-15 10:00:00 [ℹ]  eksctl version 0.167.0
# 2024-01-15 10:00:00 [ℹ]  using region us-east-1
# 2024-01-15 10:00:01 [ℹ]  will create 2 managed nodegroup(s)
# 2024-01-15 10:00:01 [ℹ]  will create 1 Fargate profile(s)
# ...
# 2024-01-15 10:20:00 [✔]  EKS cluster "production-cluster" in "us-east-1" region is ready
```

### Method 3: Using Terraform (Infrastructure as Code)

```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "my-eks-cluster"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 2
      max_size     = 5

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      labels = {
        Environment = "production"
      }
    }
  }

  tags = {
    Environment = "production"
    Terraform   = "true"
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}
```

```bash
# Initialize and apply Terraform
terraform init
terraform plan
terraform apply -auto-approve

# Output:
# Apply complete! Resources: 52 added, 0 changed, 0 destroyed.
#
# Outputs:
# cluster_endpoint = "https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com"
# cluster_name = "my-eks-cluster"
```

---

## 9.4 Connecting to Your EKS Cluster

```bash
# Update kubeconfig to connect to your cluster
aws eks update-kubeconfig --name my-k8s-cluster --region us-east-1

# Output:
# Added new context arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster to /home/user/.kube/config

# Verify connection
kubectl get nodes

# Output:
# NAME                                       STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal                 Ready    <none>   5m    v1.28.2
# ip-10-0-2-200.ec2.internal                 Ready    <none>   5m    v1.28.2
# ip-10-0-3-300.ec2.internal                 Ready    <none>   5m    v1.28.2

# Check cluster info
kubectl cluster-info

# Output:
# Kubernetes control plane is running at https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com
# CoreDNS is running at https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com/api/v1/...

# View kubeconfig
kubectl config view

# Output:
# apiVersion: v1
# clusters:
# - cluster:
#     certificate-authority-data: DATA+OMITTED
#     server: https://ABCDEF1234.gr7.us-east-1.eks.amazonaws.com
#   name: arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster
# contexts:
# - context:
#     cluster: arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster
#     user: arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster
#   name: arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster
# current-context: arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster

# Switch between multiple clusters
kubectl config get-contexts

# Output:
# CURRENT   NAME                                                          CLUSTER                                                       AUTHINFO
# *         arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster     arn:aws:eks:us-east-1:123456789012:cluster/my-k8s-cluster     arn:aws:eks:...

kubectl config use-context <context-name>
```

---

## 9.5 Understanding EKS Networking (VPC-CNI)

EKS uses the **Amazon VPC CNI plugin** which assigns real VPC IP addresses to each Pod.

```
┌────────────────── VPC (10.0.0.0/16) ──────────────────┐
│                                                        │
│  ┌─── Subnet 10.0.1.0/24 (AZ-1a) ───┐                │
│  │                                    │                │
│  │  Node: 10.0.1.100                 │                │
│  │  ├── Pod: 10.0.1.15               │                │
│  │  ├── Pod: 10.0.1.16               │                │
│  │  └── Pod: 10.0.1.17               │                │
│  │                                    │                │
│  └────────────────────────────────────┘                │
│                                                        │
│  ┌─── Subnet 10.0.2.0/24 (AZ-1b) ───┐                │
│  │                                    │                │
│  │  Node: 10.0.2.200                 │                │
│  │  ├── Pod: 10.0.2.25               │                │
│  │  └── Pod: 10.0.2.26               │                │
│  │                                    │                │
│  └────────────────────────────────────┘                │
└────────────────────────────────────────────────────────┘
```

```bash
# Check VPC CNI version
kubectl describe daemonset aws-node -n kube-system | grep Image

# Output:
# Image: 602401143452.dkr.ecr.us-east-1.amazonaws.com/amazon-k8s-cni:v1.15.1

# Check pod IP addresses (they're real VPC IPs)
kubectl get pods -o wide

# Output:
# NAME      READY   STATUS    IP           NODE
# nginx-1   1/1     Running   10.0.1.15    ip-10-0-1-100.ec2.internal
# nginx-2   1/1     Running   10.0.2.25    ip-10-0-2-200.ec2.internal

# Max pods per node depends on instance type (ENI limits)
# t3.medium: 17 pods max
# t3.large: 35 pods max
# m5.xlarge: 58 pods max

# Check max pods for your nodes
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.pods}{"\n"}{end}'

# Output:
# ip-10-0-1-100.ec2.internal    17
# ip-10-0-2-200.ec2.internal    17
```

---

## 9.6 EKS Add-ons

```bash
# List available add-ons
aws eks describe-addon-versions --kubernetes-version 1.28 --query 'addons[].addonName'

# Output:
# [
#     "vpc-cni",
#     "coredns",
#     "kube-proxy",
#     "aws-ebs-csi-driver",
#     "aws-efs-csi-driver",
#     "adot",
#     "aws-guardduty-agent",
#     "amazon-cloudwatch-observability"
# ]

# Check installed add-ons
aws eks list-addons --cluster-name my-k8s-cluster

# Output:
# {
#     "addons": [
#         "coredns",
#         "kube-proxy",
#         "vpc-cni"
#     ]
# }

# Install EBS CSI Driver (needed for persistent volumes)
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster my-k8s-cluster \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve

aws eks create-addon \
  --cluster-name my-k8s-cluster \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole

# Output:
# {
#     "addon": {
#         "addonName": "aws-ebs-csi-driver",
#         "clusterName": "my-k8s-cluster",
#         "status": "CREATING"
#     }
# }
```

---

## 9.7 IAM Integration with EKS

### IAM Roles for Service Accounts (IRSA)

IRSA allows Kubernetes pods to assume AWS IAM roles — no hardcoded credentials needed.

```bash
# Enable OIDC provider (if not already done)
eksctl utils associate-iam-oidc-provider --cluster my-k8s-cluster --approve

# Output:
# 2024-01-15 [ℹ]  will create IAM Open ID Connect provider for cluster "my-k8s-cluster"
# 2024-01-15 [✔]  created IAM Open ID Connect provider for cluster "my-k8s-cluster"

# Create an IAM service account for S3 access
eksctl create iamserviceaccount \
  --name s3-reader \
  --namespace default \
  --cluster my-k8s-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve

# Output:
# 2024-01-15 [ℹ]  1 iamserviceaccount (default/s3-reader) was included
# 2024-01-15 [ℹ]  created serviceaccount "default/s3-reader"

# Verify the service account
kubectl describe serviceaccount s3-reader

# Output:
# Name:                s3-reader
# Namespace:           default
# Annotations:         eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/eksctl-my-k8s-cluster-addon-iamserviceac-Role1-ABC123
```

```yaml
# Use the service account in a Pod
apiVersion: v1
kind: Pod
metadata:
  name: s3-reader-pod
spec:
  serviceAccountName: s3-reader    # Pod assumes this IAM role
  containers:
  - name: aws-cli
    image: amazon/aws-cli
    command: ["sleep", "3600"]
```

```bash
# Test IAM role from inside the pod
kubectl exec -it s3-reader-pod -- aws s3 ls

# Output:
# 2024-01-10 my-bucket-1
# 2024-01-12 my-bucket-2
# No credentials needed — IRSA handles it!
```

### How IRSA Works Internally

```
┌──────────────────────────────────────────────────────────────┐
│  IRSA Internal Flow                                          │
│                                                              │
│  1. eksctl creates an IAM Role with a trust policy that      │
│     trusts the EKS OIDC provider                             │
│                                                              │
│  2. eksctl annotates the K8s ServiceAccount with the         │
│     IAM Role ARN                                             │
│                                                              │
│  3. When a pod starts with that ServiceAccount:              │
│     a. EKS mutating webhook injects a projected token        │
│        volume into the pod                                   │
│     b. AWS_WEB_IDENTITY_TOKEN_FILE env var is set             │
│     c. AWS_ROLE_ARN env var is set                           │
│                                                              │
│  4. When the pod calls an AWS API (e.g., S3):                │
│     a. AWS SDK reads the projected token                     │
│     b. SDK calls STS AssumeRoleWithWebIdentity               │
│     c. STS validates the token against EKS OIDC provider     │
│     d. STS returns temporary credentials                     │
│     e. SDK uses temp credentials to call S3                  │
│                                                              │
│  Pod ──► AWS SDK ──► STS (AssumeRole) ──► S3/DynamoDB/SQS    │
│              ▲                                               │
│              │ reads token from                               │
│              └── /var/run/secrets/eks.amazonaws.com/          │
│                  serviceaccount/token                         │
└──────────────────────────────────────────────────────────────┘
```

### Accessing AWS Services from Kubernetes — Common Patterns

```yaml
# Pattern 1: Pod accessing S3 (already shown above)
# Pattern 2: Pod accessing DynamoDB
# Pattern 3: Pod accessing SQS
# Pattern 4: Pod accessing Secrets Manager

# All follow the same pattern:
# 1. Create IAM policy with required permissions
# 2. Create IRSA service account with that policy
# 3. Use the service account in the pod spec
```

```bash
# Example: Pod that reads from DynamoDB
eksctl create iamserviceaccount \
  --name dynamodb-reader \
  --namespace default \
  --cluster my-k8s-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess \
  --approve
```

```yaml
# dynamodb-app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      serviceAccountName: dynamodb-reader    # IRSA — pod gets DynamoDB access
      containers:
      - name: app
        image: myapp:v1.0
        env:
        - name: AWS_REGION
          value: us-east-1
        - name: DYNAMODB_TABLE
          value: orders
```

### Service-to-Service Communication Using IAM Roles

When one Kubernetes service needs to call another AWS service (or another microservice that validates IAM identity):

```
┌──────────────────────────────────────────────────────────────┐
│  Service-to-Service via IAM                                  │
│                                                              │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │  Order Service   │         │  Payment Service │            │
│  │  (K8s Pod)       │         │  (Lambda/ECS)    │            │
│  │                  │         │                  │            │
│  │  SA: order-sa    │──SQS──►│  Reads from SQS  │            │
│  │  IAM: OrderRole  │         │  IAM: PaymentRole│            │
│  └─────────────────┘         └─────────────────┘            │
│                                                              │
│  OrderRole policy:                                           │
│  - sqs:SendMessage to payment-queue                          │
│                                                              │
│  PaymentRole policy:                                         │
│  - sqs:ReceiveMessage from payment-queue                     │
│                                                              │
│  No shared credentials — each service has its own IAM role   │
└──────────────────────────────────────────────────────────────┘
```

```bash
# Create custom IAM policy for the order service
cat > order-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sqs:SendMessage"],
      "Resource": "arn:aws:sqs:us-east-1:123456789012:payment-queue"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem", "dynamodb:GetItem"],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/orders"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name OrderServicePolicy \
  --policy-document file://order-policy.json

# Create IRSA with custom policy
eksctl create iamserviceaccount \
  --name order-sa \
  --namespace production \
  --cluster my-k8s-cluster \
  --attach-policy-arn arn:aws:iam::123456789012:policy/OrderServicePolicy \
  --approve
```

**Interview question: How do you access AWS services from Kubernetes pods?**
Use IRSA (IAM Roles for Service Accounts). Create an IAM role with the required permissions, associate it with a Kubernetes ServiceAccount via `eksctl create iamserviceaccount`, and set `serviceAccountName` in the pod spec. The EKS webhook injects a projected token that the AWS SDK uses to call STS AssumeRoleWithWebIdentity for temporary credentials. No hardcoded secrets needed — each pod gets least-privilege access to only the AWS services it needs.

---

## 9.8 Managing the Cluster

### Scaling Node Groups

```bash
# Scale node group
eksctl scale nodegroup \
  --cluster my-k8s-cluster \
  --name standard-workers \
  --nodes 5 \
  --nodes-min 3 \
  --nodes-max 10

# Output:
# 2024-01-15 [ℹ]  scaling nodegroup "standard-workers" in cluster "my-k8s-cluster"
# 2024-01-15 [✔]  waiting for scaling of nodegroup "standard-workers" to complete

# Check node group status
eksctl get nodegroup --cluster my-k8s-cluster

# Output:
# CLUSTER          NODEGROUP          STATUS   CREATED                 MIN SIZE   MAX SIZE   DESIRED   INSTANCE TYPE   IMAGE ID
# my-k8s-cluster   standard-workers   ACTIVE   2024-01-15T10:00:00Z    3          10         5         t3.medium       AL2_x86_64
```

### Upgrading EKS

```bash
# Check current version
kubectl version --short

# Upgrade control plane
eksctl upgrade cluster --name my-k8s-cluster --version 1.29 --approve

# Upgrade node group
eksctl upgrade nodegroup \
  --name standard-workers \
  --cluster my-k8s-cluster \
  --kubernetes-version 1.29

# Update add-ons after upgrade
aws eks update-addon --cluster-name my-k8s-cluster --addon-name vpc-cni --resolve-conflicts OVERWRITE
aws eks update-addon --cluster-name my-k8s-cluster --addon-name coredns --resolve-conflicts OVERWRITE
aws eks update-addon --cluster-name my-k8s-cluster --addon-name kube-proxy --resolve-conflicts OVERWRITE
```

### Deleting the Cluster

```bash
# Delete cluster (removes everything)
eksctl delete cluster --name my-k8s-cluster --region us-east-1

# Output:
# 2024-01-15 [ℹ]  deleting EKS cluster "my-k8s-cluster"
# 2024-01-15 [ℹ]  deleted 1 nodegroup(s) from cluster "my-k8s-cluster"
# 2024-01-15 [✔]  all cluster resources were deleted

# ⚠️ WARNING: This deletes ALL resources in the cluster!
# Make sure to backup any important data first.
```

---

## 9.9 Cost Optimization Tips

| Strategy | Savings | How |
|---|---|---|
| **Spot Instances** | Up to 90% | Use for stateless workloads |
| **Right-sizing** | 30-50% | Match instance types to workload needs |
| **Cluster Autoscaler** | Variable | Scale nodes down when idle |
| **Fargate** | Variable | Pay only for pod resources used |
| **Reserved Instances** | Up to 72% | Commit to 1-3 year terms |

```yaml
# Spot instance node group example
managedNodeGroups:
  - name: spot-workers
    instanceTypes:
      - t3.medium
      - t3.large
      - t3a.medium
      - t3a.large
    spot: true
    desiredCapacity: 3
    minSize: 1
    maxSize: 10
    labels:
      lifecycle: spot
```

---

## 9.10 Common Errors & Troubleshooting

### Error: "Unable to connect to the server"
```bash
# Cause: kubeconfig not configured or expired token
# Fix:
aws eks update-kubeconfig --name my-k8s-cluster --region us-east-1
```

### Error: "error: You must be logged in to the server (Unauthorized)"
```bash
# Cause: IAM user/role not in aws-auth ConfigMap
# Fix: Add your IAM entity
kubectl edit configmap aws-auth -n kube-system

# Add under mapUsers:
# - userarn: arn:aws:iam::123456789012:user/your-user
#   username: your-user
#   groups:
#     - system:masters
```

### Error: "No space left on device" on nodes
```bash
# Cause: Node disk full (container images, logs)
# Fix: Increase volume size or clean up
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="DiskPressure")].status}{"\n"}{end}'

# Output:
# ip-10-0-1-100.ec2.internal    False   ← Healthy
# ip-10-0-2-200.ec2.internal    True    ← Disk pressure!
```

### Error: "0/3 nodes are available: 3 Insufficient cpu"
```bash
# Cause: Not enough resources on any node
# Fix: Scale up nodes or reduce resource requests
eksctl scale nodegroup --cluster my-k8s-cluster --name standard-workers --nodes 5
```

---


---

## 9.11 EKS Deployment Using Terraform

Terraform provides Infrastructure as Code (IaC) for creating EKS clusters reproducibly. This is the production-standard approach.

### Why Terraform over eksctl?

| Feature | eksctl | Terraform |
|---|---|---|
| **Learning curve** | Low (CLI tool) | Medium (HCL language) |
| **State management** | None (imperative) | State file (declarative) |
| **Drift detection** | No | Yes (`terraform plan`) |
| **Multi-resource** | EKS only | VPC + EKS + IAM + RDS + everything |
| **Team collaboration** | Difficult | Remote state + locking |
| **Best for** | Quick setup, learning | Production, GitOps, compliance |

### Terraform EKS Configuration

```hcl
# providers.tf
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "eks/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}
```

```hcl
# vpc.tf — Create VPC for EKS
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.0"

  name = "eks-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true    # Cost saving for non-prod
  enable_dns_hostnames = true

  # Tags required for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}
```

```hcl
# eks.tf — Create EKS cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.0"

  cluster_name    = "my-k8s-cluster"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Public access to API server (restrict in production)
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  # Enable IRSA
  enable_irsa = true

  # Managed node groups
  eks_managed_node_groups = {
    general = {
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 5
      desired_size   = 2

      labels = {
        role = "general"
      }
    }

    compute = {
      instance_types = ["m5.xlarge"]
      min_size       = 0
      max_size       = 10
      desired_size   = 0

      labels = {
        role = "compute"
      }

      taints = [{
        key    = "dedicated"
        value  = "compute"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # Cluster add-ons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
    }
  }
}

# IRSA for EBS CSI Driver
module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.30"

  role_name             = "ebs-csi-controller"
  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}
```

```hcl
# outputs.tf
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "configure_kubectl" {
  value = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region us-east-1"
}
```

### Deploying with Terraform

```bash
# Step 1: Initialize Terraform
terraform init

# Output:
# Initializing modules...
# Initializing provider plugins...
# Terraform has been successfully initialized!

# Step 2: Preview changes
terraform plan

# Output:
# Plan: 52 to add, 0 to change, 0 to destroy.
# (VPC, subnets, NAT gateway, EKS cluster, node groups, IAM roles, etc.)

# Step 3: Apply
terraform apply -auto-approve

# Output (after ~15 minutes):
# Apply complete! Resources: 52 added, 0 changed, 0 destroyed.
#
# Outputs:
# cluster_endpoint = "https://ABC123.gr7.us-east-1.eks.amazonaws.com"
# cluster_name = "my-k8s-cluster"
# configure_kubectl = "aws eks update-kubeconfig --name my-k8s-cluster --region us-east-1"

# Step 4: Configure kubectl
aws eks update-kubeconfig --name my-k8s-cluster --region us-east-1

kubectl get nodes

# Output:
# NAME                          STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal    Ready    <none>   5m    v1.29.1
# ip-10-0-2-200.ec2.internal    Ready    <none>   5m    v1.29.1

# Step 5: Destroy when done (saves cost)
terraform destroy -auto-approve
```

### Terraform vs eksctl Workflow

```bash
# eksctl (imperative — run once)
eksctl create cluster --name my-cluster --region us-east-1 --nodes 2

# Terraform (declarative — version controlled, repeatable)
git add *.tf
git commit -m "Add EKS cluster configuration"
terraform plan    # Preview
terraform apply   # Create/update
terraform destroy # Clean up
```

**Interview question: How do you deploy EKS using Terraform?**
Use the `terraform-aws-modules/eks/aws` module along with the VPC module. Define the cluster version, VPC/subnets, managed node groups (instance types, min/max/desired), and add-ons (CoreDNS, kube-proxy, VPC-CNI, EBS CSI). Run `terraform plan` to preview, `terraform apply` to create. Terraform manages state, detects drift, and enables GitOps workflows. For production, store state in S3 with DynamoDB locking.

---

## 9.12 Module 2 Exercises

### Exercise 1: Create Your First EKS Cluster
```bash
# Create a minimal cluster for learning
eksctl create cluster \
  --name learning-cluster \
  --region us-east-1 \
  --version 1.28 \
  --nodegroup-name learners \
  --node-type t3.small \
  --nodes 2 \
  --managed

# Verify
kubectl get nodes
kubectl get pods -A
```

### Exercise 2: Explore the Cluster
```bash
# 1. List all namespaces and their pods
kubectl get pods -A

# 2. Check node resources
kubectl top nodes    # (requires metrics-server)

# 3. Examine a system pod
kubectl describe pod -n kube-system -l k8s-app=kube-dns
```

### Exercise 3: Clean Up (Save Money!)
```bash
# Always delete clusters when not in use
eksctl delete cluster --name learning-cluster
```

---

**Next Module: Pods, ReplicaSets & Deployments →**
