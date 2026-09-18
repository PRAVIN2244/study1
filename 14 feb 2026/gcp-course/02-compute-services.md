# Module 2: Compute Services

---

## 2.1 Compute Engine (Virtual Machines)

Compute Engine lets you run VMs on Google's infrastructure. Equivalent to AWS EC2.

### Machine Types

| Category | Example | Use Case |
|----------|---------|----------|
| General Purpose | e2-medium, n2-standard-4 | Web servers, small DBs |
| Compute Optimized | c2-standard-8 | Batch processing, gaming |
| Memory Optimized | m2-megamem-416 | In-memory databases (SAP HANA) |
| Accelerator Optimized | a2-highgpu-1g | ML training, rendering |

**Naming convention:** `FAMILY-TYPE-vCPUs`
- `e2-standard-4` = E2 family, standard type, 4 vCPUs (16 GB RAM)

### Creating a VM

```bash
gcloud compute instances create my-web-server \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --tags=http-server,https-server \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y nginx
    systemctl start nginx'
```

**What each flag does:**
- `--zone`: Physical location of the VM
- `--machine-type`: CPU/RAM configuration (e2-medium = 2 vCPUs, 4 GB)
- `--image-family`: OS template (debian-12, ubuntu-2204-lts, centos-stream-9)
- `--boot-disk-size`: Root disk size
- `--tags`: Network tags for firewall rules
- `--metadata=startup-script`: Script that runs on first boot

**Output:**
```
Created [https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instances/my-web-server].
NAME           ZONE           MACHINE_TYPE  PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP    STATUS
my-web-server  us-central1-a  e2-medium                  10.128.0.2   35.192.xx.xx   RUNNING
```

### Listing VMs

```bash
gcloud compute instances list
```
**Output:**
```
NAME           ZONE           MACHINE_TYPE  PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP   STATUS
my-web-server  us-central1-a  e2-medium                  10.128.0.2   35.192.0.100  RUNNING
```

### SSH into a VM

```bash
gcloud compute ssh my-web-server --zone=us-central1-a
```
**What it does:** Creates SSH keys automatically (first time), then connects.

### Stop, Start, Delete

```bash
# Stop (you still pay for disk, not CPU/RAM)
gcloud compute instances stop my-web-server --zone=us-central1-a

# Start
gcloud compute instances start my-web-server --zone=us-central1-a

# Delete (removes everything)
gcloud compute instances delete my-web-server --zone=us-central1-a
```

### Firewall Rules

```bash
# Allow HTTP traffic to VMs tagged "http-server"
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:80 \
  --target-tags=http-server \
  --source-ranges=0.0.0.0/0
```

**Output:**
```
Created [https://www.googleapis.com/compute/v1/projects/my-project/global/firewalls/allow-http].
NAME        NETWORK  DIRECTION  PRIORITY  ALLOW   DENY  DISABLED
allow-http  default  INGRESS    1000      tcp:80        False
```

### Preemptible / Spot VMs (60-91% cheaper)

```bash
# Spot VM — can be terminated anytime, up to 91% discount
gcloud compute instances create batch-worker \
  --zone=us-central1-a \
  --machine-type=e2-standard-4 \
  --provisioning-model=SPOT \
  --instance-termination-action=STOP \
  --image-family=debian-12 \
  --image-project=debian-cloud
```

**Use case:** Batch processing, CI/CD runners, data pipelines where interruption is acceptable.

### Instance Templates and Managed Instance Groups (MIG)

```bash
# Create an instance template
gcloud compute instance-templates create web-template \
  --machine-type=e2-medium \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=http-server \
  --metadata=startup-script='#!/bin/bash
    apt-get update && apt-get install -y nginx
    echo "Host: $(hostname)" > /var/www/html/index.html'

# Create a managed instance group with autoscaling
gcloud compute instance-groups managed create web-group \
  --base-instance-name=web \
  --template=web-template \
  --size=2 \
  --zone=us-central1-a

# Set up autoscaling (2-10 instances, target 60% CPU)
gcloud compute instance-groups managed set-autoscaling web-group \
  --zone=us-central1-a \
  --min-num-replicas=2 \
  --max-num-replicas=10 \
  --target-cpu-utilization=0.6 \
  --cool-down-period=90
```

**Real-world Example — E-commerce Auto-scaling:**
During Black Friday, traffic spikes 10x. The MIG automatically scales from 2 to 10 instances, then scales back down after the sale ends.

---

## 2.2 App Engine

Fully managed platform for web apps. You deploy code, Google manages servers.

**Two modes:**
- **Standard**: Scales to zero, limited runtimes (Python, Java, Node, Go, PHP, Ruby)
- **Flexible**: Runs in Docker containers, any runtime, minimum 1 instance

### Deploying a Python App

```bash
# Create project structure
mkdir ~/my-app && cd ~/my-app

# Create main.py
cat > main.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from App Engine!'

@app.route('/api/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
Flask==3.0.0
gunicorn==21.2.0
EOF

# Create app.yaml (App Engine config)
cat > app.yaml << 'EOF'
runtime: python312
entrypoint: gunicorn -b :$PORT main:app

instance_class: F2

automatic_scaling:
  min_instances: 0
  max_instances: 5
  target_cpu_utilization: 0.65

env_variables:
  ENV: production
EOF

# Deploy
gcloud app deploy --quiet
```

**Output:**
```
Services to deploy:
  descriptor:      [/home/user/my-app/app.yaml]
  source:          [/home/user/my-app]
  target project:  [my-webapp-prod]
  target service:  [default]
  target version:  [20240115t103045]
  target url:      [https://my-webapp-prod.uc.r.appspot.com]

Beginning deployment of service [default]...
╔════════════════════════════════════════════════════════════╗
╠═ Uploading 3 files to Google Cloud Storage               ═╣
╚════════════════════════════════════════════════════════════╝
File upload done.
Deployed service [default] to [https://my-webapp-prod.uc.r.appspot.com]
```

```bash
# Open in browser
gcloud app browse

# View logs
gcloud app logs tail -s default

# List versions
gcloud app versions list
```

**Output of versions list:**
```
SERVICE  VERSION.ID          TRAFFIC_SPLIT  LAST_DEPLOYED              SERVING_STATUS
default  20240115t103045     1.00           2024-01-15T10:30:45+00:00  SERVING
default  20240110t091500     0.00           2024-01-10T09:15:00+00:00  STOPPED
```

### Traffic Splitting (Canary Deployments)

```bash
# Send 90% to old version, 10% to new version
gcloud app services set-traffic default \
  --splits=20240110t091500=0.9,20240115t103045=0.1
```

**⚠️ Key Limitation:** Only ONE App Engine app per project. You cannot delete it — only disable.

---

## 2.3 Cloud Functions (Serverless Functions)

Event-driven, pay-per-invocation. Equivalent to AWS Lambda.

### HTTP Function (Gen 2)

```bash
mkdir ~/my-function && cd ~/my-function

# Create function
cat > main.py << 'EOF'
import functions_framework
import json

@functions_framework.http
def hello_world(request):
    """HTTP Cloud Function."""
    name = request.args.get('name', 'World')
    return json.dumps({'message': f'Hello, {name}!'}), 200, {'Content-Type': 'application/json'}
EOF

cat > requirements.txt << 'EOF'
functions-framework==3.*
EOF

# Deploy (Gen 2)
gcloud functions deploy hello-function \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=hello_world \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --timeout=60s \
  --max-instances=10
```

**Output:**
```
Deploying function (may take a while - up to 2 minutes)...done.
availableMemoryMb: 256
entryPoint: hello_world
httpsTrigger:
  url: https://us-central1-my-project.cloudfunctions.net/hello-function
...
status: ACTIVE
```

```bash
# Test the function
curl "https://us-central1-my-project.cloudfunctions.net/hello-function?name=GCP"
```
**Output:**
```json
{"message": "Hello, GCP!"}
```

### Event-Triggered Function (Cloud Storage trigger)

```bash
cat > main.py << 'EOF'
import functions_framework
from google.cloud import storage

@functions_framework.cloud_event
def process_image(cloud_event):
    """Triggered when a file is uploaded to Cloud Storage."""
    data = cloud_event.data
    bucket = data["bucket"]
    name = data["name"]
    print(f"Processing file: gs://{bucket}/{name}")
    # Add image processing logic here
EOF

gcloud functions deploy process-image \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=. \
  --entry-point=process_image \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=my-image-bucket"
```

```bash
# View function logs
gcloud functions logs read hello-function --region=us-central1 --limit=20
```

---

## 2.4 Cloud Run (Containerized Serverless)

Run any container without managing infrastructure. Scales to zero.

### Deploy from Source Code

```bash
mkdir ~/my-cloudrun-app && cd ~/my-cloudrun-app

cat > main.py << 'EOF'
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'service': 'my-api',
        'version': '1.0.0',
        'revision': os.environ.get('K_REVISION', 'unknown')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
EOF

cat > requirements.txt << 'EOF'
Flask==3.0.0
gunicorn==21.2.0
EOF

cat > Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 main:app
EOF

# Deploy (builds container automatically)
gcloud run deploy my-api \
  --source=. \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --port=8080
```

**Output:**
```
Building using Dockerfile and deploying container to Cloud Run service [my-api] in project [my-project] region [us-central1]
✓ Building and deploying... Done.
  ✓ Uploading sources...
  ✓ Building Container...
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [my-api] revision [my-api-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://my-api-abc123-uc.a.run.app
```

### Traffic Splitting on Cloud Run

```bash
# Deploy new revision
gcloud run deploy my-api --source=. --region=us-central1 --no-traffic

# Split traffic: 80% old, 20% new
gcloud run services update-traffic my-api \
  --region=us-central1 \
  --to-revisions=my-api-00001-abc=80,my-api-00002-def=20
```

---

## 2.5 Google Kubernetes Engine (GKE)

Managed Kubernetes. Google handles the control plane; you manage workloads.

### Create a Cluster

```bash
# Standard cluster (you manage nodes)
gcloud container clusters create my-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --enable-autorepair \
  --enable-autoupgrade

# Autopilot cluster (Google manages nodes — recommended)
gcloud container clusters create-auto my-autopilot-cluster \
  --region=us-central1
```

**Output (takes 5-10 minutes):**
```
Creating cluster my-cluster in us-central1-a...done.
Created [https://container.googleapis.com/v1/projects/my-project/zones/us-central1-a/clusters/my-cluster].
kubeconfig entry generated for my-cluster.
NAME        LOCATION       MASTER_VERSION  NUM_NODES  STATUS
my-cluster  us-central1-a  1.28.3-gke.100  3          RUNNING
```

### Connect and Deploy

```bash
# Get credentials (configures kubectl)
gcloud container clusters get-credentials my-cluster --zone=us-central1-a

# Verify connection
kubectl get nodes
```
**Output:**
```
NAME                                        STATUS   ROLES    AGE   VERSION
gke-my-cluster-default-pool-abc123-0001     Ready    <none>   5m    v1.28.3-gke.100
gke-my-cluster-default-pool-abc123-0002     Ready    <none>   5m    v1.28.3-gke.100
gke-my-cluster-default-pool-abc123-0003     Ready    <none>   5m    v1.28.3-gke.100
```

```bash
# Deploy an nginx application
kubectl create deployment nginx --image=nginx:latest --replicas=3

# Expose it via a LoadBalancer
kubectl expose deployment nginx --type=LoadBalancer --port=80

# Check the external IP
kubectl get service nginx --watch
```
**Output:**
```
NAME    TYPE           CLUSTER-IP    EXTERNAL-IP    PORT(S)        AGE
nginx   LoadBalancer   10.48.0.100   34.72.xx.xx    80:31234/TCP   2m
```

### Delete Cluster

```bash
gcloud container clusters delete my-cluster --zone=us-central1-a --quiet
```

---

## 2.6 Compute Services Comparison

| Feature | Compute Engine | App Engine | Cloud Functions | Cloud Run | GKE |
|---------|---------------|------------|-----------------|-----------|-----|
| Abstraction | IaaS | PaaS | FaaS | CaaS | CaaS |
| Scale to zero | No | Yes (Standard) | Yes | Yes | No |
| Custom runtime | Yes | Limited | Limited | Yes (Docker) | Yes |
| Pricing | Per second | Per instance-hour | Per invocation | Per request | Per node |
| Best for | Full control, legacy apps | Simple web apps | Event handlers | Microservices | Complex multi-service apps |

---

## 2.7 Real-world Example: Deploying a Microservices E-commerce Backend

```bash
# Architecture:
# Cloud Run: API Gateway, Product Service, Order Service
# Cloud Functions: Image resizer (triggered by Storage upload)
# GKE: Payment processing (needs persistent connections)

# 1. Deploy Product Service to Cloud Run
gcloud run deploy product-service \
  --image=gcr.io/my-project/product-service:v1 \
  --region=us-central1 \
  --memory=1Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=20 \
  --set-env-vars="DB_HOST=10.0.0.5,CACHE_HOST=10.0.0.6" \
  --vpc-connector=my-vpc-connector \
  --allow-unauthenticated

# 2. Deploy Order Service to Cloud Run
gcloud run deploy order-service \
  --image=gcr.io/my-project/order-service:v1 \
  --region=us-central1 \
  --memory=512Mi \
  --min-instances=1 \
  --set-env-vars="PRODUCT_SERVICE_URL=https://product-service-abc.a.run.app" \
  --no-allow-unauthenticated  # Internal only

# 3. Deploy image resizer as Cloud Function
gcloud functions deploy resize-product-image \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=./image-resizer \
  --entry-point=resize \
  --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
  --trigger-event-filters="bucket=product-images" \
  --memory=1024MB
```

---

## Module 2 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ZONE_RESOURCE_POOL_EXHAUSTED` | No capacity in zone | Try a different zone |
| `QUOTA_EXCEEDED` | Hit CPU/IP quota | Request quota increase in Console |
| `RESOURCE_NOT_FOUND` | Wrong zone/region | Check `--zone` or `--region` flag |
| `PERMISSION_DENIED: Compute Engine API not enabled` | API disabled | `gcloud services enable compute.googleapis.com` |
| Cloud Run: `Container failed to start` | App not listening on PORT env var | Use `os.environ.get('PORT', 8080)` |
| GKE: `Unable to connect to the server` | Credentials expired | Re-run `gcloud container clusters get-credentials` |

**Next: Module 3 — Storage & Databases →**
