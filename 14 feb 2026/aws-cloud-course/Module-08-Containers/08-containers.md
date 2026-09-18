# Module 8: ECS, EKS & Containers

## 8.1 Containers on AWS

### What are Containers?
Containers package your application with all its dependencies into a single, portable unit.

### Real-World Analogy
- **VM** = A house (full OS, heavy, slow to start)
- **Container** = A shipping container (lightweight, standardized, portable)

### Container Services on AWS

```
┌─────────────────────────────────────────────────────┐
│              AWS Container Services                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Registry:    ECR (Elastic Container Registry)       │
│                                                      │
│  Orchestration:                                      │
│    ├── ECS (Elastic Container Service) — AWS native  │
│    └── EKS (Elastic Kubernetes Service) — Kubernetes │
│                                                      │
│  Compute:                                            │
│    ├── EC2 (you manage instances)                    │
│    └── Fargate (serverless, AWS manages infra)       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### ECS vs EKS Decision

| Factor | ECS | EKS |
|--------|-----|-----|
| Complexity | Simpler | More complex |
| Learning curve | Low | High (Kubernetes) |
| Portability | AWS-only | Multi-cloud |
| Cost | Lower | Higher ($0.10/hr for control plane) |
| Best for | AWS-native apps | K8s expertise, multi-cloud |

---

## 8.2 ECR (Elastic Container Registry)

ECR is AWS's Docker image registry (like Docker Hub, but private).

### Create a Repository

```bash
aws ecr create-repository \
  --repository-name myapp/web \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256
```

**Expected Output:**
```json
{
    "repository": {
        "repositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/myapp/web",
        "repositoryName": "myapp/web",
        "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web",
        "createdAt": "2024-01-15T10:00:00+00:00"
    }
}
```

### Build and Push a Docker Image

```bash
# Step 1: Create a sample application
mkdir myapp && cd myapp

cat > app.py << 'EOF'
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/')
def home():
    return jsonify({
        "message": "Hello from ECS!",
        "hostname": os.environ.get('HOSTNAME', 'unknown'),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

cat > requirements.txt << 'EOF'
flask==3.0.0
gunicorn==21.2.0
EOF

cat > Dockerfile << 'EOF'
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
EOF

# Step 2: Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Step 3: Build the image
docker build -t myapp/web:1.0.0 .

# Step 4: Tag for ECR
docker tag myapp/web:1.0.0 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:1.0.0
docker tag myapp/web:1.0.0 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:latest

# Step 5: Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:latest
```

### List Images

```bash
aws ecr describe-images \
  --repository-name myapp/web \
  --query 'imageDetails[].{Tags:imageTags,Size:imageSizeInBytes,Pushed:imagePushedAt}' \
  --output table
```

### ECR Lifecycle Policy (Auto-cleanup)

```bash
aws ecr put-lifecycle-policy \
  --repository-name myapp/web \
  --lifecycle-policy-text '{
    "rules": [{
      "rulePriority": 1,
      "description": "Keep only last 10 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {"type": "expire"}
    }]
  }'
```

---

## 8.3 ECS with Fargate (Serverless Containers)

### ECS Concepts

```
┌─────────────────────────────────────────────┐
│                ECS Cluster                   │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │          Service (desired: 3)          │ │
│  │                                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────┐│ │
│  │  │  Task 1  │ │  Task 2  │ │ Task 3 ││ │
│  │  │          │ │          │ │        ││ │
│  │  │┌────────┐│ │┌────────┐│ │┌──────┐││ │
│  │  ││Container││ ││Container││ ││Cont. │││ │
│  │  ││ (web)  ││ ││ (web)  ││ ││(web) │││ │
│  │  │└────────┘│ │└────────┘│ │└──────┘││ │
│  │  └──────────┘ └──────────┘ └────────┘│ │
│  └────────────────────────────────────────┘ │
│                                              │
│  Task Definition = Blueprint for containers  │
└─────────────────────────────────────────────┘
```

| Concept | Meaning |
|---------|---------|
| **Cluster** | Logical grouping of tasks/services |
| **Task Definition** | Blueprint (image, CPU, memory, ports, env vars) |
| **Task** | Running instance of a task definition |
| **Service** | Maintains desired number of tasks, integrates with ALB |

### Step 1: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name myapp-cluster
```

**Expected Output:**
```json
{
    "cluster": {
        "clusterArn": "arn:aws:ecs:us-east-1:123456789012:cluster/myapp-cluster",
        "clusterName": "myapp-cluster",
        "status": "ACTIVE"
    }
}
```

### Step 2: Create Task Execution Role

```bash
# This role allows ECS to pull images from ECR and write logs
cat > ecs-trust.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
EOF

aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://ecs-trust.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
```

### Step 3: Create Task Definition

```bash
cat > task-definition.json << 'EOF'
{
    "family": "myapp-web",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "web",
            "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:latest",
            "portMappings": [
                {
                    "containerPort": 8080,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "NODE_ENV", "value": "production"},
                {"name": "PORT", "value": "8080"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/myapp-web",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            },
            "essential": true
        }
    ]
}
EOF

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/myapp-web

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 4: Create ECS Service with ALB

```bash
# Create security group for ECS tasks
ECS_SG=$(aws ec2 create-security-group \
  --group-name ecs-tasks-sg \
  --description "ECS tasks" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $ECS_SG --protocol tcp --port 8080 --source-group $ALB_SG

# Create ECS service
aws ecs create-service \
  --cluster myapp-cluster \
  --service-name myapp-web-service \
  --task-definition myapp-web \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[$PRIV_SUB_A,$PRIV_SUB_B],
    securityGroups=[$ECS_SG],
    assignPublicIp=DISABLED
  }" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=web,containerPort=8080"
```

### Step 5: Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/myapp-cluster/myapp-web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/myapp-cluster/myapp-web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

### ECS Management Commands

```bash
# List services
aws ecs list-services --cluster myapp-cluster

# Describe service
aws ecs describe-services \
  --cluster myapp-cluster \
  --services myapp-web-service \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'

# List tasks
aws ecs list-tasks --cluster myapp-cluster --service-name myapp-web-service

# View task logs
aws logs get-log-events \
  --log-group-name /ecs/myapp-web \
  --log-stream-name ecs/web/<task-id>

# Update service (deploy new image)
aws ecs update-service \
  --cluster myapp-cluster \
  --service myapp-web-service \
  --force-new-deployment

# Scale service
aws ecs update-service \
  --cluster myapp-cluster \
  --service myapp-web-service \
  --desired-count 5

# Stop a task
aws ecs stop-task --cluster myapp-cluster --task <task-arn>
```

---

## 8.4 EKS (Elastic Kubernetes Service)

### Create EKS Cluster

```bash
# Install eksctl (EKS CLI tool)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Create EKS cluster with managed node group
eksctl create cluster \
  --name myapp-eks \
  --region us-east-1 \
  --version 1.29 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

**This takes 15-20 minutes.** It creates:
- EKS control plane
- VPC with subnets
- Managed node group (EC2 instances)
- IAM roles
- Security groups

### Verify Cluster

```bash
# Update kubeconfig
aws eks update-kubeconfig --name myapp-eks --region us-east-1

# Check nodes
kubectl get nodes
```

**Expected Output:**
```
NAME                             STATUS   ROLES    AGE   VERSION
ip-192-168-1-100.ec2.internal    Ready    <none>   5m    v1.29.0
ip-192-168-2-200.ec2.internal    Ready    <none>   5m    v1.29.0
ip-192-168-3-300.ec2.internal    Ready    <none>   5m    v1.29.0
```

### Deploy Application to EKS

```bash
# Create deployment
cat > k8s-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-web
  labels:
    app: myapp-web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp-web
  template:
    metadata:
      labels:
        app: myapp-web
    spec:
      containers:
      - name: web
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp/web:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "250m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        env:
        - name: NODE_ENV
          value: "production"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-web-service
spec:
  type: LoadBalancer
  selector:
    app: myapp-web
  ports:
  - port: 80
    targetPort: 8080
EOF

kubectl apply -f k8s-deployment.yaml

# Check deployment
kubectl get deployments
kubectl get pods
kubectl get services
```

**Expected Output:**
```
NAME               READY   UP-TO-DATE   AVAILABLE   AGE
myapp-web          3/3     3            3           2m

NAME                         READY   STATUS    RESTARTS   AGE
myapp-web-6d4f5b7c8-abc12    1/1     Running   0          2m
myapp-web-6d4f5b7c8-def34    1/1     Running   0          2m
myapp-web-6d4f5b7c8-ghi56    1/1     Running   0          2m

NAME                TYPE           CLUSTER-IP     EXTERNAL-IP                    PORT(S)
myapp-web-service   LoadBalancer   10.100.1.100   a1b2c3-1234.us-east-1.elb...   80:31234/TCP
```

### Horizontal Pod Autoscaler

```bash
kubectl autoscale deployment myapp-web \
  --cpu-percent=70 \
  --min=2 \
  --max=10

kubectl get hpa
```

### Delete EKS Cluster

```bash
eksctl delete cluster --name myapp-eks --region us-east-1
```

---

## 8.5 Common Errors & Troubleshooting

### Error 1: ECS task keeps stopping
```bash
# Check stopped task reason
aws ecs describe-tasks \
  --cluster myapp-cluster \
  --tasks <task-arn> \
  --query 'tasks[0].{Status:lastStatus,Reason:stoppedReason,Container:containers[0].reason}'

# Common reasons:
# - "OutOfMemoryError" → Increase task memory
# - "CannotPullContainerError" → Check ECR permissions / image exists
# - "HealthCheckFailure" → Fix health check endpoint
```

### Error 2: "CannotPullContainerError"
```bash
# Check ECR image exists
aws ecr describe-images --repository-name myapp/web

# Check task execution role has ECR permissions
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole

# Ensure VPC has NAT Gateway or VPC endpoint for ECR
```

### Error 3: EKS pods in CrashLoopBackOff
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --previous
```

### Error 4: ECR login expired
```bash
# Re-authenticate (token valid for 12 hours)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

---

## 8.6 ECS — IAM Roles

### Two Types of Roles in ECS

| Role | Purpose | Scope |
|------|---------|-------|
| **EC2 Instance Profile** (EC2 launch type only) | Used by the ECS agent to pull images, send logs, access secrets | Per EC2 instance |
| **ECS Task Role** | Used by the containers in the task to access AWS services | Per task definition |

```
EC2 Instance Profile ──▶ ECS Agent (pulls images from ECR, sends logs to CloudWatch)
ECS Task Role ──▶ Your Container (accesses S3, DynamoDB, etc.)
```

Each task can have a different role — one task accesses S3, another accesses DynamoDB.

---

## 8.7 ECS — Auto Scaling

### Service Auto Scaling (task level)

Scale the number of ECS tasks based on metrics.

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 --max-capacity 20

# Target tracking on CPU
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name ecs-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "TargetValue": 50.0
  }'
```

### EC2 Launch Type — Scaling EC2 Instances

For EC2 launch type, you also need to scale the underlying EC2 instances:
- **Auto Scaling Group**: Scale EC2 based on CPU/memory
- **ECS Cluster Capacity Provider** (recommended): Automatically scales EC2 to match task demand

---

## 8.8 ECS — Event-Driven Patterns

### ECS Tasks Invoked by EventBridge

```
S3 Upload ──▶ EventBridge Rule ──▶ Run ECS Task (Fargate)
                                    └── Process the uploaded file
```

### ECS Tasks Invoked by EventBridge Schedule

```
Cron Schedule ──▶ EventBridge Rule ──▶ Run ECS Task (Fargate)
(every hour)                            └── Batch processing job
```

### ECS + SQS Queue

```
SQS Queue ──▶ ECS Service (polls queue) ──▶ Process messages
              Auto-scales based on queue depth
```

```bash
# Create an ECS service that scales based on SQS queue depth
# Step 1: Create the SQS queue
aws sqs create-queue --queue-name image-processing

# Step 2: Create an ECS service with desired count 1
aws ecs create-service \
  --cluster my-cluster \
  --service-name queue-processor \
  --task-definition image-processor:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-0abcdef1234567890"],
      "securityGroups": ["sg-0abcdef1234567890"]
    }
  }'

# Step 3: Register a scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/queue-processor \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 --max-capacity 10

# Step 4: Create a scaling policy based on SQS queue depth
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/my-cluster/queue-processor \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name sqs-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 10,
    "CustomizedMetricSpecification": {
      "MetricName": "ApproximateNumberOfMessagesVisible",
      "Namespace": "AWS/SQS",
      "Dimensions": [{"Name": "QueueName", "Value": "image-processing"}],
      "Statistic": "Average"
    },
    "ScaleInCooldown": 60,
    "ScaleOutCooldown": 60
  }'
```

**Real-life use case:** An image processing pipeline receives upload events via SQS. ECS tasks poll the queue and resize images. When the queue grows to 100 messages, ECS scales to 10 tasks. When the queue is empty, it scales back to 1.

### Intercept Stopped Tasks

```
ECS Task Stopped ──▶ EventBridge ──▶ SNS (alert) or Lambda (auto-remediate)
```

---

## 8.9 EKS — Node Types and Data Volumes

### EKS Node Types

| Type | Description |
|------|-------------|
| **Managed Node Groups** | AWS manages EC2 instances, auto-scaling, updates |
| **Self-Managed Nodes** | You manage EC2 instances (use your own AMI) |
| **Fargate** | Serverless — no nodes to manage |

### Kubernetes Service Types

| Service Type | Description | AWS Integration |
|-------------|-------------|-----------------|
| **ClusterIP** | Internal-only, accessible within the cluster | No external access |
| **NodePort** | Exposes on each node's IP at a static port (30000-32767) | Direct node access |
| **LoadBalancer** | Provisions an AWS load balancer automatically | Creates CLB/NLB/ALB |

```yaml
# ClusterIP Service (internal only)
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8080

---
# NodePort Service
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080

---
# LoadBalancer Service (creates an NLB)
apiVersion: v1
kind: Service
metadata:
  name: public-api
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: external
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 443
    targetPort: 8443
```

```bash
# Apply and verify
kubectl apply -f service.yaml
kubectl get svc
# NAME          TYPE           CLUSTER-IP     EXTERNAL-IP                              PORT(S)
# backend-svc   ClusterIP      172.20.0.100   <none>                                   80/TCP
# web-svc       NodePort       172.20.0.101   <none>                                   80:30080/TCP
# public-api    LoadBalancer   172.20.0.102   abcdef-1234.us-east-1.elb.amazonaws.com  443:31234/TCP
```

### EKS Cluster Endpoint Access

Control how the Kubernetes API server is accessed.

| Mode | API Server Access | kubectl from |
|------|------------------|-------------|
| **Public** | Internet + VPC | Anywhere |
| **Public + Private** | Internet (restricted CIDRs) + VPC | Anywhere (with CIDR restriction) |
| **Private** | VPC only | Within VPC, VPN, or Direct Connect |

```bash
# Set cluster endpoint to private only
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPublicAccess=false,endpointPrivateAccess=true

# Set to public with CIDR restriction
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs='["203.0.113.0/24"]'

# Verify endpoint configuration
aws eks describe-cluster --name my-cluster \
  --query 'cluster.resourcesVpcConfig.{Public:endpointPublicAccess,Private:endpointPrivateAccess,CIDRs:publicAccessCidrs}'

# Expected output:
# {
#   "Public": true,
#   "Private": true,
#   "CIDRs": ["203.0.113.0/24"]
# }
```

### EKS Data Volumes

EKS supports Container Storage Interface (CSI) drivers:
- **EBS** — block storage (single AZ)
- **EFS** — shared file storage (multi-AZ)
- **FSx for Lustre** — high-performance computing
- **FSx for NetApp ONTAP** — enterprise storage

---

## 8.10 AWS App Runner

Fully managed service to deploy web apps and APIs from source code or container images. No infrastructure to manage.

```bash
aws apprunner create-service \
  --service-name my-api \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {"Port": "8080"}
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{"Cpu": "1024", "Memory": "2048"}'
```

**When to use App Runner vs ECS:**
- App Runner: Simple web apps, no infrastructure knowledge needed
- ECS: Complex architectures, fine-grained control, sidecar containers

---

## 8.11 Key Takeaways

1. Use ECR for private Docker image storage with vulnerability scanning
2. ECS + Fargate = simplest way to run containers (no servers to manage)
3. EKS = use when you need Kubernetes features or multi-cloud portability
4. Fargate pricing: pay per vCPU and memory per second
5. ECS Task Role = permissions for your container; Instance Profile = permissions for ECS agent
6. Use ECS Cluster Capacity Providers for automatic EC2 scaling
7. EventBridge + ECS Fargate for event-driven batch processing
8. EKS supports Managed Node Groups, Self-Managed, and Fargate
9. App Runner for simple web apps — zero infrastructure management
10. Use ECR lifecycle policies to control image storage costs
