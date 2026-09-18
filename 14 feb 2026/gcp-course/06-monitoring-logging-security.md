# Module 6: Monitoring, Logging & Security

---

## 6.1 Cloud Monitoring (formerly Stackdriver)

Collects metrics, creates dashboards, and sends alerts.

### Enabling Monitoring

```bash
gcloud services enable monitoring.googleapis.com
```

### Viewing Metrics via CLI

```bash
# List available metric types for Compute Engine
gcloud monitoring metrics list --filter="metric.type = starts_with(\"compute.googleapis.com\")" --limit=10
```
**Output:**
```
TYPE                                                  DISPLAY_NAME
compute.googleapis.com/instance/cpu/utilization       CPU utilization
compute.googleapis.com/instance/disk/read_bytes_count Disk read bytes
compute.googleapis.com/instance/disk/write_bytes_count Disk write bytes
compute.googleapis.com/instance/network/received_bytes_count Network bytes received
compute.googleapis.com/instance/network/sent_bytes_count Network bytes sent
...
```

### Creating Alerting Policies

```bash
# Create an alert: CPU > 80% for 5 minutes
gcloud monitoring policies create \
  --display-name="High CPU Alert" \
  --condition-display-name="CPU above 80%" \
  --condition-filter='resource.type = "gce_instance" AND metric.type = "compute.googleapis.com/instance/cpu/utilization"' \
  --condition-threshold-value=0.8 \
  --condition-threshold-comparison=COMPARISON_GT \
  --condition-threshold-duration=300s \
  --notification-channels=CHANNEL_ID \
  --combiner=OR
```

### Creating Notification Channels

```bash
# Create an email notification channel
gcloud monitoring channels create \
  --display-name="DevOps Team Email" \
  --type=email \
  --channel-labels=email_address=devops@company.com

# List channels
gcloud monitoring channels list
```
**Output:**
```
NAME                                                    DISPLAY_NAME         TYPE   ENABLED
projects/my-project/notificationChannels/1234567890     DevOps Team Email    email  True
```

### Uptime Checks

```bash
# Create an uptime check for your website
gcloud monitoring uptime create \
  --display-name="Website Uptime" \
  --resource-type=uptime-url \
  --hostname=myapp.example.com \
  --path=/ \
  --protocol=HTTPS \
  --period=60 \
  --timeout=10s

# List uptime checks
gcloud monitoring uptime list-configs
```

### Custom Metrics (from your application)

```python
# Python example — send custom metrics
from google.cloud import monitoring_v3
import time

client = monitoring_v3.MetricServiceClient()
project_name = f"projects/my-project"

# Create a time series
series = monitoring_v3.TimeSeries()
series.metric.type = "custom.googleapis.com/orders/count"
series.resource.type = "global"

now = time.time()
interval = monitoring_v3.TimeInterval(
    {"end_time": {"seconds": int(now)}}
)
point = monitoring_v3.Point(
    {"interval": interval, "value": {"int64_value": 42}}
)
series.points = [point]

client.create_time_series(
    request={"name": project_name, "time_series": [series]}
)
print("Custom metric sent!")
```

---

## 6.2 Cloud Logging

Centralized log management. All GCP services automatically send logs here.

### Viewing Logs

```bash
# Read recent logs for a project
gcloud logging read --limit=20 --format=json

# Read logs for a specific resource
gcloud logging read 'resource.type="gce_instance" AND resource.labels.instance_id="1234567890"' \
  --limit=10

# Read Cloud Run logs
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="my-api"' \
  --limit=20 \
  --format='table(timestamp, textPayload)'
```

**Output:**
```
TIMESTAMP                    TEXT_PAYLOAD
2024-01-15T10:30:00.000Z     GET /api/health 200 12ms
2024-01-15T10:29:55.000Z     GET /api/users 200 45ms
2024-01-15T10:29:50.000Z     POST /api/orders 201 120ms
```

### Log Filters (Advanced)

```bash
# Errors only
gcloud logging read 'severity>=ERROR' --limit=10

# Specific time range
gcloud logging read 'timestamp>="2024-01-15T00:00:00Z" AND timestamp<="2024-01-15T23:59:59Z"' --limit=50

# JSON payload filtering
gcloud logging read 'jsonPayload.httpRequest.status>=500' --limit=10

# Combine filters
gcloud logging read '
  resource.type="cloud_run_revision"
  AND resource.labels.service_name="my-api"
  AND severity>=WARNING
  AND timestamp>="2024-01-15T00:00:00Z"
' --limit=20
```

### Writing Custom Logs

```python
# Python — structured logging to Cloud Logging
import google.cloud.logging
import logging

client = google.cloud.logging.Client()
client.setup_logging()

# Standard Python logging goes to Cloud Logging automatically
logging.info("User logged in", extra={
    "json_fields": {
        "user_id": "user123",
        "action": "login",
        "ip_address": "192.168.1.1"
    }
})

logging.error("Payment failed", extra={
    "json_fields": {
        "order_id": "order456",
        "error_code": "INSUFFICIENT_FUNDS",
        "amount": 99.99
    }
})
```

### Log-based Metrics

```bash
# Create a metric that counts 500 errors
gcloud logging metrics create server-errors \
  --description="Count of 5xx errors" \
  --log-filter='resource.type="cloud_run_revision" AND httpRequest.status>=500'

# List log-based metrics
gcloud logging metrics list
```

### Log Sinks (Export Logs)

```bash
# Export logs to Cloud Storage (for long-term archival)
gcloud logging sinks create archive-logs \
  storage.googleapis.com/my-logs-archive-bucket \
  --log-filter='severity>=WARNING'

# Export logs to BigQuery (for analysis)
gcloud logging sinks create logs-to-bq \
  bigquery.googleapis.com/projects/my-project/datasets/logs_dataset \
  --log-filter='resource.type="cloud_run_revision"'

# Export logs to Pub/Sub (for real-time processing)
gcloud logging sinks create logs-to-pubsub \
  pubsub.googleapis.com/projects/my-project/topics/log-events \
  --log-filter='severity>=ERROR'
```

---

## 6.3 Error Reporting

Automatically groups and tracks application errors.

```bash
# Enable Error Reporting
gcloud services enable clouderrorreporting.googleapis.com

# View errors
gcloud error-reporting events list --limit=10
```

Error Reporting works automatically when you:
1. Log exceptions with stack traces to Cloud Logging
2. Use supported languages (Python, Java, Node.js, Go, .NET, Ruby, PHP)

```python
# Python — errors are auto-reported when logged with stack traces
import logging
import traceback

try:
    result = 1 / 0
except Exception:
    logging.error(f"Unhandled exception: {traceback.format_exc()}")
```

---

## 6.4 Cloud Trace

Distributed tracing for microservices. Shows request latency across services.

```bash
gcloud services enable cloudtrace.googleapis.com
```

```python
# Python — automatic tracing with OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup
tracer_provider = TracerProvider()
cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

# Use in your code
with tracer.start_as_current_span("process-order") as span:
    span.set_attribute("order.id", "order-123")
    span.set_attribute("order.amount", 99.99)
    # ... process order
    with tracer.start_as_current_span("validate-payment"):
        # ... validate payment
        pass
    with tracer.start_as_current_span("update-inventory"):
        # ... update inventory
        pass
```

---

## 6.5 Cloud KMS (Key Management Service)

Manage encryption keys for data at rest and in transit.

### Creating Keys

```bash
# Enable KMS API
gcloud services enable cloudkms.googleapis.com

# Create a key ring (container for keys)
gcloud kms keyrings create my-keyring \
  --location=us-central1

# Create an encryption key
gcloud kms keys create my-encryption-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --purpose=encryption \
  --rotation-period=90d \
  --next-rotation-time=$(date -u -d "+90 days" +%Y-%m-%dT%H:%M:%SZ)
```

**Output:**
```
Created key [my-encryption-key].
```

### Encrypting and Decrypting Data

```bash
# Encrypt a file
gcloud kms encrypt \
  --key=my-encryption-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --plaintext-file=secret.txt \
  --ciphertext-file=secret.txt.enc

# Decrypt a file
gcloud kms decrypt \
  --key=my-encryption-key \
  --keyring=my-keyring \
  --location=us-central1 \
  --ciphertext-file=secret.txt.enc \
  --plaintext-file=secret-decrypted.txt
```

### Using KMS with Cloud Storage (CMEK)

```bash
# Create a bucket encrypted with your own key
gcloud storage buckets create gs://my-encrypted-bucket \
  --location=us-central1 \
  --default-encryption-key=projects/my-project/locations/us-central1/keyRings/my-keyring/cryptoKeys/my-encryption-key
```

---

## 6.6 Secret Manager

Store and manage API keys, passwords, certificates, and other secrets.

### Creating Secrets

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create a secret
echo -n "MyDatabaseP@ssw0rd!" | gcloud secrets create db-password \
  --data-file=- \
  --replication-policy=automatic

# Create from a file
gcloud secrets create tls-cert \
  --data-file=./server.crt \
  --replication-policy=automatic
```

**Output:**
```
Created secret [db-password].
Created version [1] of the secret [db-password].
```

### Accessing Secrets

```bash
# Access the latest version
gcloud secrets versions access latest --secret=db-password
```
**Output:**
```
MyDatabaseP@ssw0rd!
```

```bash
# Access a specific version
gcloud secrets versions access 1 --secret=db-password

# List all versions
gcloud secrets versions list db-password
```
**Output:**
```
NAME  STATE    CREATED
2     ENABLED  2024-01-15T10:30:00Z
1     ENABLED  2024-01-10T09:00:00Z
```

### Updating Secrets (New Version)

```bash
# Add a new version
echo -n "NewP@ssw0rd!2024" | gcloud secrets versions add db-password --data-file=-

# Disable old version
gcloud secrets versions disable 1 --secret=db-password

# Destroy old version (irreversible)
gcloud secrets versions destroy 1 --secret=db-password
```

### Using Secrets in Applications

```python
# Python — access secrets at runtime
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id, version="latest"):
    name = f"projects/my-project/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
db_password = get_secret("db-password")
api_key = get_secret("stripe-api-key")
```

### Using Secrets with Cloud Run

```bash
# Mount secret as environment variable
gcloud run deploy my-api \
  --image=us-central1-docker.pkg.dev/my-project/apps/my-api:latest \
  --region=us-central1 \
  --set-secrets=DB_PASSWORD=db-password:latest,API_KEY=stripe-api-key:latest

# Mount secret as a file
gcloud run deploy my-api \
  --image=us-central1-docker.pkg.dev/my-project/apps/my-api:latest \
  --region=us-central1 \
  --set-secrets=/secrets/tls/cert=tls-cert:latest
```

### Granting Access to Secrets

```bash
# Allow a service account to read a secret
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:my-app-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 6.7 Security Command Center (SCC)

Centralized security and risk management.

```bash
# Enable SCC
gcloud services enable securitycenter.googleapis.com

# List findings (vulnerabilities, misconfigurations)
gcloud scc findings list organizations/ORG_ID \
  --source="-" \
  --filter='state="ACTIVE" AND severity="HIGH"' \
  --limit=20
```

**Common findings SCC detects:**
- Public Cloud Storage buckets
- VMs with public IPs and no firewall
- Service account keys older than 90 days
- Disabled audit logging
- Overly permissive IAM roles

---

## 6.8 Audit Logs

Track who did what, when, and where.

```bash
# View admin activity logs (always on, free)
gcloud logging read 'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Factivity"' \
  --limit=10 \
  --format='table(timestamp, protoPayload.methodName, protoPayload.authenticationInfo.principalEmail)'
```

**Output:**
```
TIMESTAMP                    METHOD_NAME                                    PRINCIPAL_EMAIL
2024-01-15T10:30:00.000Z     google.cloud.sql.instances.create              admin@company.com
2024-01-15T10:25:00.000Z     v1.compute.instances.delete                    developer@company.com
2024-01-15T10:20:00.000Z     google.iam.admin.v1.CreateServiceAccount       admin@company.com
```

```bash
# Enable data access audit logs (costs money, but needed for compliance)
# Done via Console: IAM & Admin > Audit Logs
# Or via gcloud:
gcloud projects get-iam-policy my-project --format=json > policy.json
# Edit policy.json to add auditConfigs, then:
gcloud projects set-iam-policy my-project policy.json
```

---

## 6.9 Real-world Example: Production Monitoring Setup

**Scenario:** Set up monitoring for an e-commerce platform running on Cloud Run.

```bash
# 1. Create notification channels
gcloud monitoring channels create \
  --display-name="PagerDuty - Critical" \
  --type=pagerduty \
  --channel-labels=service_key=YOUR_PAGERDUTY_KEY

gcloud monitoring channels create \
  --display-name="Slack - Warnings" \
  --type=slack \
  --channel-labels=channel_name="#alerts"

# 2. Create uptime check
gcloud monitoring uptime create \
  --display-name="API Health Check" \
  --resource-type=uptime-url \
  --hostname=api.myecommerce.com \
  --path=/api/health \
  --protocol=HTTPS \
  --period=60

# 3. Export error logs to BigQuery for analysis
bq mk --dataset my-project:error_logs

gcloud logging sinks create errors-to-bq \
  bigquery.googleapis.com/projects/my-project/datasets/error_logs \
  --log-filter='resource.type="cloud_run_revision" AND severity>=ERROR'

# 4. Store all secrets in Secret Manager
echo -n "$DB_PASS" | gcloud secrets create prod-db-password --data-file=-
echo -n "$STRIPE_KEY" | gcloud secrets create prod-stripe-key --data-file=-
echo -n "$JWT_SECRET" | gcloud secrets create prod-jwt-secret --data-file=-

# 5. Grant Cloud Run service account access to secrets
SA="my-app-sa@my-project.iam.gserviceaccount.com"
for secret in prod-db-password prod-stripe-key prod-jwt-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SA" \
    --role="roles/secretmanager.secretAccessor"
done
```

---

## Module 6 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `PERMISSION_DENIED` on Secret Manager | Missing `secretAccessor` role | Grant `roles/secretmanager.secretAccessor` |
| Alert not firing | Threshold or duration too high | Lower threshold or reduce duration window |
| Logs not appearing | Wrong resource type filter | Check `resource.type` in log filter |
| KMS: `PERMISSION_DENIED` | Missing `cloudkms.cryptoKeyEncrypterDecrypter` | Grant the role to the service account |
| Audit logs missing | Data access logs not enabled | Enable in IAM & Admin > Audit Logs |
| Log sink not exporting | Sink service account missing permissions | Grant writer role to the sink's service account |

**Next: Module 7 — Advanced Topics & Real-world Projects →**
