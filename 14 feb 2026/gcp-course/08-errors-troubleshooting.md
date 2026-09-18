# Module 8: Common Errors & Troubleshooting

---

## 8.1 Authentication & Permission Errors

### Error: `PERMISSION_DENIED: The caller does not have permission`

**Cause:** The authenticated user or service account lacks the required IAM role.

**Diagnosis:**
```bash
# Check who you're authenticated as
gcloud auth list

# Check what project you're targeting
gcloud config get-value project

# Check what roles the user has
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL" \
  --format="table(bindings.role)"
```

**Fix:**
```bash
# Grant the needed role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/NEEDED_ROLE"
```

**Common role mappings:**
| Action | Required Role |
|--------|--------------|
| Create/manage VMs | `roles/compute.admin` |
| View VMs | `roles/compute.viewer` |
| Deploy to Cloud Run | `roles/run.admin` + `roles/iam.serviceAccountUser` |
| Access Cloud SQL | `roles/cloudsql.client` |
| Read Cloud Storage | `roles/storage.objectViewer` |
| Write Cloud Storage | `roles/storage.objectCreator` |
| Manage secrets | `roles/secretmanager.admin` |
| Read secrets | `roles/secretmanager.secretAccessor` |

---

### Error: `UNAUTHENTICATED: Request had invalid authentication credentials`

**Cause:** Token expired or no valid credentials.

**Fix:**
```bash
# Re-authenticate
gcloud auth login

# For application default credentials
gcloud auth application-default login

# For service accounts
gcloud auth activate-service-account --key-file=sa-key.json

# Verify
gcloud auth list
```

---

### Error: `Could not load the default credentials`

**Cause:** Application can't find credentials. Common in local development.

**Fix:**
```bash
# Set application default credentials
gcloud auth application-default login

# Or set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa-key.json"

# Verify
gcloud auth application-default print-access-token
```

---

## 8.2 API & Service Errors

### Error: `API [xxx.googleapis.com] not enabled on project`

**Cause:** The required API hasn't been activated.

**Fix:**
```bash
# Enable the specific API
gcloud services enable APINAME.googleapis.com

# Common APIs to enable
gcloud services enable \
  compute.googleapis.com \
  storage.googleapis.com \
  sqladmin.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  pubsub.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

---

### Error: `Quota exceeded` or `QUOTA_EXCEEDED`

**Cause:** You've hit a resource limit (CPUs, IPs, API calls per minute).

**Diagnosis:**
```bash
# Check current quotas
gcloud compute project-info describe --format="table(quotas.metric,quotas.limit,quotas.usage)"
```
**Output:**
```
METRIC                  LIMIT    USAGE
CPUS                    24.0     16.0
DISKS_TOTAL_GB          10240.0  500.0
IN_USE_ADDRESSES        8.0      8.0     ← This is full!
INSTANCES               100.0    12.0
```

**Fix:**
```bash
# Request quota increase via Console:
# IAM & Admin > Quotas > Filter by metric > Edit Quotas

# Or release unused resources
gcloud compute addresses list  # Find unused static IPs
gcloud compute addresses delete UNUSED_IP --region=REGION
```

---

## 8.3 Compute Engine Errors

### Error: `ZONE_RESOURCE_POOL_EXHAUSTED`

**Cause:** The zone has no available capacity for the requested machine type.

**Fix:**
```bash
# Try a different zone
gcloud compute instances create my-vm \
  --zone=us-central1-b \  # Changed from us-central1-a
  --machine-type=e2-medium

# Or try a different machine type
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-standard-2  # Changed from n2-standard-2
```

---

### Error: `The resource 'projects/xxx/zones/xxx/instances/xxx' was not found`

**Cause:** Wrong zone specified, or the VM doesn't exist.

**Fix:**
```bash
# Find the VM's actual zone
gcloud compute instances list --filter="name=my-vm"

# Use the correct zone
gcloud compute instances describe my-vm --zone=CORRECT_ZONE
```

---

### Error: VM can't be SSH'd into

**Diagnosis:**
```bash
# Check if VM is running
gcloud compute instances describe my-vm --zone=ZONE --format="value(status)"

# Check firewall rules
gcloud compute firewall-rules list --filter="allowed[].ports:22"

# Check if SSH key is configured
gcloud compute instances describe my-vm --zone=ZONE \
  --format="value(metadata.items[key='ssh-keys'])"

# Try with troubleshooting flag
gcloud compute ssh my-vm --zone=ZONE --troubleshoot
```

**Common fixes:**
```bash
# Ensure SSH firewall rule exists
gcloud compute firewall-rules create allow-ssh \
  --direction=INGRESS --action=ALLOW --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 --target-tags=allow-ssh

# Use IAP tunnel (no public IP needed)
gcloud compute ssh my-vm --zone=ZONE --tunnel-through-iap
```

---

## 8.4 Cloud SQL Errors

### Error: `Connection timed out` or `could not connect to server`

**Diagnosis:**
```bash
# Check instance status
gcloud sql instances describe INSTANCE_NAME --format="value(state)"

# Check authorized networks
gcloud sql instances describe INSTANCE_NAME \
  --format="value(settings.ipConfiguration.authorizedNetworks)"
```

**Fix:**
```bash
# Option 1: Use Cloud SQL Auth Proxy (recommended)
./cloud-sql-proxy PROJECT:REGION:INSTANCE --port=5432

# Option 2: Authorize your IP
MY_IP=$(curl -s ifconfig.me)
gcloud sql instances patch INSTANCE_NAME \
  --authorized-networks=$MY_IP/32

# Option 3: Use private IP (for VMs in same VPC)
gcloud sql instances describe INSTANCE_NAME --format="value(ipAddresses)"
```

---

### Error: `too many connections`

**Cause:** Connection pool exhausted or connections not being closed.

**Fix:**
```bash
# Check current connections
gcloud sql connect INSTANCE_NAME --user=postgres
# Then run: SELECT count(*) FROM pg_stat_activity;

# Increase max connections (requires restart)
gcloud sql instances patch INSTANCE_NAME \
  --database-flags=max_connections=200

# Better fix: Use connection pooling
# - PgBouncer for PostgreSQL
# - ProxySQL for MySQL
# - Cloud SQL Auth Proxy with connection limits
```

---

## 8.5 Cloud Run Errors

### Error: `Container failed to start. Failed to start and then listen on the port defined by the PORT environment variable`

**Cause:** Your app isn't listening on the PORT environment variable.

**Fix:**
```python
# Python — correct way
import os
port = int(os.environ.get('PORT', 8080))
app.run(host='0.0.0.0', port=port)
```

```javascript
// Node.js — correct way
const port = process.env.PORT || 8080;
app.listen(port, '0.0.0.0', () => {
  console.log(`Listening on port ${port}`);
});
```

```go
// Go — correct way
port := os.Getenv("PORT")
if port == "" {
    port = "8080"
}
http.ListenAndServe(":"+port, nil)
```

---

### Error: Cloud Run returns `503 Service Unavailable`

**Diagnosis:**
```bash
# Check revision status
gcloud run revisions list --service=SERVICE_NAME --region=REGION

# Check logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="SERVICE_NAME" AND severity>=ERROR' \
  --limit=20
```

**Common causes:**
1. Container crashes on startup → Check logs for stack traces
2. Health check failing → Ensure `/` or health endpoint returns 200
3. Memory limit exceeded → Increase `--memory`
4. Cold start timeout → Increase `--timeout` or set `--min-instances=1`

---

## 8.6 GKE Errors

### Error: `Unable to connect to the server: dial tcp: lookup xxx: no such host`

**Fix:**
```bash
# Re-fetch credentials
gcloud container clusters get-credentials CLUSTER_NAME --zone=ZONE

# Verify context
kubectl config current-context
kubectl cluster-info
```

---

### Error: `pods "xxx" is forbidden: exceeded quota`

**Fix:**
```bash
# Check resource quotas
kubectl describe resourcequota -n NAMESPACE

# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# Scale up the node pool
gcloud container clusters resize CLUSTER_NAME \
  --node-pool=default-pool \
  --num-nodes=5 \
  --zone=ZONE
```

---

### Error: `ImagePullBackOff` or `ErrImagePull`

**Diagnosis:**
```bash
kubectl describe pod POD_NAME -n NAMESPACE
```

**Common causes and fixes:**
```bash
# 1. Image doesn't exist
docker pull IMAGE_NAME  # Test locally

# 2. Authentication issue with Artifact Registry
# Grant GKE service account access
gcloud artifacts repositories add-iam-policy-binding REPO \
  --location=REGION \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader"

# 3. Wrong image path
# Correct format: REGION-docker.pkg.dev/PROJECT/REPO/IMAGE:TAG
```

---

## 8.7 Cloud Storage Errors

### Error: `AccessDeniedException: 403 Caller does not have storage.objects.get access`

**Fix:**
```bash
# Grant access to the bucket
gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
  --member="user:EMAIL" \
  --role="roles/storage.objectViewer"

# Or for a service account
gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/storage.objectViewer"
```

---

### Error: `BucketAlreadyExists` or `409 Conflict`

**Cause:** Bucket names are globally unique across all of GCP.

**Fix:**
```bash
# Use a unique prefix
gcloud storage buckets create gs://YOUR-DOMAIN-NAME-purpose-env
# Example: gs://acme-corp-logs-prod
```

---

## 8.8 Networking Errors

### Error: VM can't reach the internet

**Diagnosis:**
```bash
# Check if VM has external IP
gcloud compute instances describe VM_NAME --zone=ZONE \
  --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

# If empty, check for Cloud NAT
gcloud compute routers nats list --router=ROUTER_NAME --region=REGION
```

**Fix:**
```bash
# Option 1: Add external IP
gcloud compute instances add-access-config VM_NAME --zone=ZONE

# Option 2: Set up Cloud NAT (preferred for production)
gcloud compute routers create my-router --network=VPC_NAME --region=REGION
gcloud compute routers nats create my-nat \
  --router=my-router --region=REGION \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
```

---

### Error: Load Balancer returns `502 Bad Gateway`

**Diagnosis:**
```bash
# Check backend health
gcloud compute backend-services get-health BACKEND_SERVICE --global

# Check health check configuration
gcloud compute health-checks describe HEALTH_CHECK_NAME
```

**Common fixes:**
1. Firewall rule missing for health check probes:
```bash
# Google health check IPs: 130.211.0.0/22 and 35.191.0.0/16
gcloud compute firewall-rules create allow-health-check \
  --network=VPC_NAME \
  --action=ALLOW \
  --rules=tcp:80 \
  --source-ranges=130.211.0.0/22,35.191.0.0/16 \
  --target-tags=web
```
2. Backend not listening on the expected port
3. Health check path returns non-200 status

---

## 8.9 Billing Errors

### Error: `BILLING_DISABLED: This API method requires billing to be enabled`

**Fix:**
```bash
# Check billing status
gcloud billing projects describe PROJECT_ID

# Link a billing account
gcloud billing accounts list
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

---

### Unexpected High Bills

**Diagnosis:**
```bash
# Check running resources
gcloud compute instances list --filter="status=RUNNING"
gcloud sql instances list
gcloud container clusters list
gcloud run services list --platform=managed

# Check for orphaned resources
gcloud compute disks list --filter="NOT users:*"  # Unattached disks
gcloud compute addresses list --filter="status=RESERVED"  # Unused static IPs
gcloud compute forwarding-rules list  # Load balancers
```

**Fix:**
```bash
# Delete unused resources
gcloud compute disks delete DISK_NAME --zone=ZONE
gcloud compute addresses delete IP_NAME --region=REGION

# Stop non-production instances
gcloud compute instances stop VM_NAME --zone=ZONE

# Set up budget alerts
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="Monthly Alert" \
  --budget-amount=100 \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0
```

---

## 8.10 General Debugging Workflow

When you encounter any GCP error, follow this systematic approach:

```
Step 1: Read the error message carefully
  └─ GCP errors usually include the exact issue and resource path

Step 2: Check authentication
  └─ gcloud auth list
  └─ gcloud config get-value project

Step 3: Check permissions
  └─ gcloud projects get-iam-policy PROJECT --flatten="bindings[].members" \
       --filter="bindings.members:IDENTITY"

Step 4: Check if API is enabled
  └─ gcloud services list --enabled --filter="name:SERVICE_NAME"

Step 5: Check quotas
  └─ Console > IAM & Admin > Quotas

Step 6: Check logs
  └─ gcloud logging read 'severity>=ERROR' --limit=20

Step 7: Check resource status
  └─ gcloud RESOURCE describe RESOURCE_NAME

Step 8: Search the error in Google Cloud documentation
  └─ https://cloud.google.com/docs

Step 9: Check Google Cloud Status Dashboard
  └─ https://status.cloud.google.com
```

---

## 8.11 Useful Debugging Commands Reference

```bash
# === Identity & Auth ===
gcloud auth list                              # Who am I?
gcloud config list                            # Current configuration
gcloud config get-value project               # Current project

# === Resource Discovery ===
gcloud compute instances list                 # All VMs
gcloud sql instances list                     # All Cloud SQL
gcloud run services list                      # All Cloud Run services
gcloud container clusters list                # All GKE clusters
gcloud storage ls                             # All buckets
gcloud functions list                         # All Cloud Functions

# === Logs ===
gcloud logging read --limit=20                # Recent logs
gcloud logging read 'severity>=ERROR' --limit=10  # Errors only

# === Networking ===
gcloud compute firewall-rules list            # All firewall rules
gcloud compute networks list                  # All VPCs
gcloud compute addresses list                 # All static IPs
gcloud compute forwarding-rules list          # All load balancers

# === Costs ===
gcloud compute disks list --filter="NOT users:*"     # Orphaned disks
gcloud compute addresses list --filter="status=RESERVED"  # Unused IPs

# === API & Quotas ===
gcloud services list --enabled                # Enabled APIs
gcloud compute project-info describe          # Quotas
```

---

## 8.12 GCP Support Tiers

| Tier | Response Time | Cost |
|------|--------------|------|
| Basic | Community forums | Free |
| Standard | P2: 4 hours, P3: 8 hours | $29/month |
| Enhanced | P1: 1 hour, P2: 4 hours | $500/month or 3% of spend |
| Premium | P1: 15 min, P2: 2 hours | $12,500/month or 4% of spend |

```bash
# Check your support level
# Console > Support > Overview
```

**End of Course**
