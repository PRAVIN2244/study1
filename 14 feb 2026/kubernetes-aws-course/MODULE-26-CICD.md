# MODULE 26: CI/CD — GitHub Actions, ArgoCD & Jenkins

---

## 26.1 CI/CD with Kubernetes on AWS

### GitHub Actions Pipeline

```yaml
# .github/workflows/deploy.yaml
name: Build and Deploy to EKS

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: my-webapp
  EKS_CLUSTER: production-cluster

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build, tag, and push image to ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

    - name: Update kubeconfig
      run: |
        aws eks update-kubeconfig --name $EKS_CLUSTER --region $AWS_REGION

    - name: Deploy to EKS
      env:
        IMAGE_TAG: ${{ github.sha }}
      run: |
        helm upgrade --install my-webapp ./helm/my-webapp \
          --namespace production \
          --set image.tag=$IMAGE_TAG \
          --set image.repository=${{ steps.login-ecr.outputs.registry }}/$ECR_REPOSITORY \
          --wait \
          --timeout 300s

    - name: Verify deployment
      run: |
        kubectl rollout status deployment/my-webapp -n production --timeout=120s
        kubectl get pods -n production -l app.kubernetes.io/name=my-webapp
```

### ArgoCD — GitOps Continuous Delivery

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Expose ArgoCD UI
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Output:
# aB3cD4eF5gH6

# Install ArgoCD CLI
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login
argocd login <argocd-server-url> --username admin --password <password>
```

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-webapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-manifests.git
    targetRevision: main
    path: apps/my-webapp
    helm:
      valueFiles:
      - values-production.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true           # Delete resources removed from Git
      selfHeal: true        # Revert manual changes
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```bash
kubectl apply -f argocd-application.yaml

# Check sync status
argocd app get my-webapp

# Output:
# Name:               my-webapp
# Project:            default
# Server:             https://kubernetes.default.svc
# Namespace:          production
# URL:                https://argocd.example.com/applications/my-webapp
# Repo:               https://github.com/company/k8s-manifests.git
# Target:             main
# Path:               apps/my-webapp
# SyncWindow:         Sync Allowed
# Sync Policy:        Automated (Prune)
# Sync Status:        Synced to main (abc1234)
# Health Status:      Healthy
```

---

## 26.2 Jenkins on Kubernetes — Dynamic Slave Agents

### Architecture

Jenkins master runs as a Deployment in Kubernetes. For each build job, a new slave pod is dynamically created, registers with the master, runs the job, and is destroyed after completion.

```
Jenkins Master (Deployment + PVC)
    │
    ├── Job triggered
    │   └── Kubernetes plugin creates slave Pod
    │       └── Slave registers with master via JNLP
    │       └── Slave runs build steps
    │       └── Slave pod deleted after job completes
    │
    └── Next job → new slave Pod created
```

### Step 1 — Deploy Jenkins Master

```yaml
# jenkins-master.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins-master
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      serviceAccountName: jenkins
      containers:
      - name: jenkins
        image: jenkins/jenkins:lts
        ports:
        - containerPort: 8080      # Web UI
        - containerPort: 50000     # JNLP agent port
        volumeMounts:
        - name: jenkins-home
          mountPath: /var/jenkins_home
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
      volumes:
      - name: jenkins-home
        persistentVolumeClaim:
          claimName: jenkins-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jenkins-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
# Service for Web UI
apiVersion: v1
kind: Service
metadata:
  name: jenkins-service
spec:
  type: NodePort
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30080
    name: http
  - port: 50000
    targetPort: 50000
    name: jnlp
  selector:
    app: jenkins
```

### Step 2 — Create RBAC for Jenkins

Jenkins needs permissions to create/delete pods for slave agents:

```yaml
# jenkins-rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: jenkins
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: jenkins
rules:
- apiGroups: [""]
  resources: ["pods", "pods/exec", "pods/log", "secrets", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: [""]
  resources: ["persistentvolumeclaims"]
  verbs: ["get", "list", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jenkins
subjects:
- kind: ServiceAccount
  name: jenkins
  namespace: default
roleRef:
  kind: ClusterRole
  name: jenkins
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f jenkins-rbac.yaml
kubectl apply -f jenkins-master.yaml
```

### Step 3 — Configure Kubernetes Plugin in Jenkins

1. Access Jenkins UI at `http://<node-ip>:30080`
2. Install the **Kubernetes** plugin (Manage Jenkins → Plugins → Available → "Kubernetes")
3. Configure the cloud (Manage Jenkins → Clouds → New Cloud → Kubernetes):

| Setting | Value |
|---|---|
| Kubernetes URL | `https://kubernetes.default.svc.cluster.local` |
| Kubernetes Namespace | `default` |
| Jenkins URL | `http://jenkins-service.default.svc.cluster.local:8080` |
| Jenkins tunnel | `jenkins-service.default.svc.cluster.local:50000` |
| Pod Label: key | `jenkins` |
| Pod Label: value | `slave` |

4. Add a Pod Template:

| Setting | Value |
|---|---|
| Name | `jenkins-slave` |
| Labels | `jenkins-slave` |
| Container name | `jnlp` |
| Docker image | `jenkins/inbound-agent:latest` |
| Working directory | `/home/jenkins/agent` |

### Step 4 — Create a Pipeline Using Dynamic Slaves

```groovy
// Jenkinsfile
pipeline {
    agent {
        kubernetes {
            label 'jenkins-slave'
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: maven
    image: maven:3.9-eclipse-temurin-17
    command: ["sleep"]
    args: ["infinity"]
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
'''
        }
    }
    stages {
        stage('Build') {
            steps {
                container('maven') {
                    sh 'mvn --version'
                    sh 'echo "Building application..."'
                }
            }
        }
        stage('Docker Build') {
            steps {
                container('docker') {
                    sh 'docker build -t my-app:latest .'
                }
            }
        }
    }
}
```

**How it works:**
1. Jenkins job is triggered
2. Kubernetes plugin creates a new Pod with the specified containers
3. The JNLP agent container automatically registers with Jenkins master
4. Build steps run inside the specified containers
5. After the job completes, the Pod is automatically deleted

**Benefits over static slaves:**
- No idle resources — slaves only exist during builds
- Each job gets a clean environment
- Scale to hundreds of concurrent builds
- Different container images per job (Maven, Node, Python, etc.)

### Alternative: Install via Helm

```bash
helm repo add jenkins https://charts.jenkins.io
helm repo update

helm install jenkins jenkins/jenkins \
  --set controller.serviceType=NodePort \
  --set controller.nodePort=30080 \
  --set persistence.size=20Gi

# Get admin password
kubectl exec -it svc/jenkins -c jenkins -- cat /run/secrets/additional/chart-admin-password
```

---

## 26.4 Environment Parity — Why Prod Works but Dev Doesn't

### The Problem

The most common deployment failure isn't bad code — it's environment inconsistency. When dev, test, staging, and production environments differ in configuration, dependencies, or infrastructure, bugs slip through testing and surface only in production.

**Three dimensions of environment disparity:**

| Dimension | Example | Impact |
|-----------|---------|--------|
| **Configuration** | Dev has `DEBUG=true`, prod has `DEBUG=false` | Different error handling, logging behavior |
| **Dependencies** | Dev uses `python:3.10`, prod uses `python:3.9` | Library incompatibilities, syntax errors |
| **Data** | Tests use mock DB, prod uses PostgreSQL | Query behavior differences, missing constraints |

**Real-world scenario:**

```
Developer's laptop          CI Pipeline              Staging              Production
─────────────────          ──────────              ───────              ──────────
Node.js 18                 Node.js 20              Node.js 20           Node.js 20
.env with fake keys        Mock secrets            Real secrets         Real secrets
SQLite                     Mock DB                 PostgreSQL           PostgreSQL (5 replicas)
DEBUG=true                 DEBUG=true              DEBUG=false          DEBUG=false
1 instance                 1 container             1 replica            10 replicas + HPA

Result: "It works on my machine" → crashes in production
```

### The Solution: Promote, Don't Rebuild

The golden rule of environment parity:

> Build the artifact once. Test it. Promote the same artifact through all environments unchanged.

Every rebuild introduces risk — dependency updates, image tag drift, build context differences.

**Anti-pattern (rebuild at each stage):**

```
Dev → Build image → Test → Rebuild image → Stage → Rebuild image → Prod
                    ↑ different base image    ↑ different deps      ↑ different build context
```

**Correct pattern (promote same artifact):**

```
Build image (tag: myapp:abc123)
  → Push to registry
    → Deploy to test (same image)
      → Deploy to staging (same image)
        → Deploy to production (same image)
```

### Achieving Parity with Containers

Docker images are the foundation of environment parity — they freeze your application code, dependencies, and runtime into an immutable artifact.

```dockerfile
# Pin the base image version — never use :latest
FROM python:3.10.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Configuration injected at runtime, not baked in
ENV APP_ENV=dev \
    PORT=8080

CMD ["python", "app.py"]
```

**Key practices:**

- Pin base image versions (`python:3.10.13-slim`, not `python:latest`)
- Never hardcode secrets or environment-specific config
- Build once, tag with Git SHA: `myapp:$(git rev-parse --short HEAD)`

**Jenkins pipeline — build once, promote everywhere:**

```groovy
pipeline {
    agent any
    environment {
        IMAGE_NAME = "myapp"
        IMAGE_TAG  = "${BUILD_NUMBER}"
        REGISTRY   = "123456789.dkr.ecr.us-east-1.amazonaws.com"
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG .'
            }
        }
        stage('Run Unit Tests') {
            steps {
                // Test the SAME image that will go to production
                sh 'docker run --rm $REGISTRY/$IMAGE_NAME:$IMAGE_TAG pytest tests/'
            }
        }
        stage('Push to Registry') {
            steps {
                sh 'docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG'
            }
        }
        stage('Deploy to Staging') {
            steps {
                // Same image deployed to staging
                sh 'kubectl set image deployment/myapp myapp=$REGISTRY/$IMAGE_NAME:$IMAGE_TAG -n staging'
                sh 'kubectl rollout status deployment/myapp -n staging --timeout=120s'
            }
        }
        stage('Promote to Production') {
            steps {
                // Manual approval gate
                input message: "Promote image $IMAGE_TAG to production?"
                // SAME image promoted to production — no rebuild
                sh 'kubectl set image deployment/myapp myapp=$REGISTRY/$IMAGE_NAME:$IMAGE_TAG -n prod'
                sh 'kubectl rollout status deployment/myapp -n prod --timeout=300s'
            }
        }
    }
    post {
        success { echo "Build $BUILD_NUMBER promoted successfully!" }
        failure { echo "Build $BUILD_NUMBER failed — no promotion." }
    }
}
```

The same `$REGISTRY/$IMAGE_NAME:$IMAGE_TAG` is used in every stage. No rebuild occurs after the test stage.

### Configuration Management via Kubernetes

The same Docker image runs everywhere. Only the configuration differs — injected via ConfigMaps and Secrets per namespace.

```yaml
# configmap-dev.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: dev
data:
  APP_ENV: "development"
  LOG_LEVEL: "debug"
  DATABASE_URL: "postgres://devuser:devpass@dev-db:5432/devdb"
---
# configmap-prod.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: prod
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  DATABASE_URL: "postgres://produser:prodpass@prod-db:5432/proddb"
```

**Deployment references the same ConfigMap name in every namespace:**

```yaml
envFrom:
- configMapRef:
    name: app-config
- secretRef:
    name: app-secrets
```

One deployment manifest, multiple environments — only the namespace-scoped ConfigMap/Secret differs.

> **Cross-reference:** ConfigMaps and Secrets → MODULE-16

### Infrastructure Parity with Terraform

Even with identical containers, parity breaks if the underlying infrastructure differs. Use the same Terraform module for all environments:

```hcl
variable "environment" {}

module "eks_cluster" {
  source       = "./modules/eks"
  cluster_name = "myapp-${var.environment}"
  node_count   = var.environment == "prod" ? 6 : 3
}
```

```bash
# Same module, different variables
terraform apply -var-file=staging.tfvars
terraform apply -var-file=prod.tfvars
```

> **Cross-reference:** Terraform EKS setup → MODULE-09

### GitOps Enforcement with ArgoCD

Manual fixes and emergency patches cause environments to drift over time. ArgoCD ensures your cluster state always matches Git.

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-staging
spec:
  project: default
  source:
    repoURL: 'https://github.com/org/myapp-configs.git'
    targetRevision: main
    path: environments/staging
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: staging
  syncPolicy:
    automated:
      prune: true
      selfHeal: true    # Auto-correct manual drift
```

If someone manually edits a resource in the cluster, ArgoCD detects the drift and reverts it to match Git.

> **Cross-reference:** ArgoCD setup → Section 26.1

### Validating Parity

Add a validation step to your CI/CD pipeline:

```bash
#!/bin/bash
# Compare deployed images across environments
STAGING_IMAGE=$(kubectl get deploy myapp -n staging \
  -o jsonpath='{.spec.template.spec.containers[0].image}')
PROD_IMAGE=$(kubectl get deploy myapp -n prod \
  -o jsonpath='{.spec.template.spec.containers[0].image}')

if [ "$STAGING_IMAGE" = "$PROD_IMAGE" ]; then
  echo "Environment parity confirmed"
else
  echo "PARITY MISMATCH: staging=$STAGING_IMAGE prod=$PROD_IMAGE"
  exit 1
fi
```

### Parity Checklist

| Layer | Without Parity | With Parity |
|-------|---------------|-------------|
| **Build** | Rebuild at each stage | Build once, promote everywhere |
| **Config** | Hardcoded .env files | ConfigMaps/Secrets per namespace |
| **Infrastructure** | Manual server setup | Terraform modules with var files |
| **Deployment** | `kubectl apply` ad-hoc | ArgoCD GitOps with self-heal |
| **Validation** | Hope it works | Automated parity checks in pipeline |

### Impact Metrics

| Metric | Before Parity | After Parity |
|--------|--------------|-------------|
| Deployment success rate | ~70-80% | ~95-99% |
| Mean Time to Recovery | Hours/days | Minutes |
| Change lead time | 3-5 days | <24 hours |
| Rollback frequency | High | Low |
| "Works on my machine" incidents | Weekly | Rare |

---

