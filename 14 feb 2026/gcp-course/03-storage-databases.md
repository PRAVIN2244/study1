# Module 3: Storage & Databases

---

## 3.1 Cloud Storage (Object Storage)

Equivalent to AWS S3. Stores files (objects) in buckets.

### Storage Classes

| Class | Use Case | Availability | Min Duration | Cost (per GB/month) |
|-------|----------|-------------|--------------|---------------------|
| Standard | Frequently accessed | 99.95% | None | ~$0.020 |
| Nearline | Once a month | 99.9% | 30 days | ~$0.010 |
| Coldline | Once a quarter | 99.9% | 90 days | ~$0.004 |
| Archive | Once a year | 99.9% | 365 days | ~$0.0012 |

### Creating Buckets

```bash
# Create a bucket (name must be globally unique)
gcloud storage buckets create gs://my-company-data-2024 \
  --location=us-central1 \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access
```

**What each flag does:**
- `--location`: Region or multi-region (US, EU, ASIA)
- `--default-storage-class`: Default class for new objects
- `--uniform-bucket-level-access`: Use IAM only (no ACLs) — recommended

**Output:**
```
Creating gs://my-company-data-2024/...
```

**⚠️ Common Error:**
```
ERROR: (gcloud.storage.buckets.create) HTTPError 409: Your previous request to create the named bucket succeeded and you already own it.
```
**Fix:** Bucket names are globally unique. Use a unique prefix like your domain name.

### Uploading Files

```bash
# Upload a single file
gcloud storage cp myfile.txt gs://my-company-data-2024/

# Upload a directory recursively
gcloud storage cp -r ./my-folder gs://my-company-data-2024/backups/

# Upload with specific storage class
gcloud storage cp myfile.txt gs://my-company-data-2024/ --storage-class=NEARLINE
```

**Output:**
```
Copying file://myfile.txt to gs://my-company-data-2024/myfile.txt
  Completed files 1/1 | 15.2kiB/15.2kiB
```

### Downloading Files

```bash
# Download a file
gcloud storage cp gs://my-company-data-2024/myfile.txt ./local-copy.txt

# Download entire folder
gcloud storage cp -r gs://my-company-data-2024/backups/ ./local-backups/
```

### Listing Objects

```bash
gcloud storage ls gs://my-company-data-2024/
```
**Output:**
```
gs://my-company-data-2024/myfile.txt
gs://my-company-data-2024/backups/
```

```bash
# List with details (size, date)
gcloud storage ls -l gs://my-company-data-2024/
```
**Output:**
```
     15200  2024-01-15T10:30:00Z  gs://my-company-data-2024/myfile.txt
                                  gs://my-company-data-2024/backups/
TOTAL: 1 objects, 15200 bytes (14.84 KiB)
```

### Deleting Objects

```bash
# Delete a file
gcloud storage rm gs://my-company-data-2024/myfile.txt

# Delete a folder
gcloud storage rm -r gs://my-company-data-2024/backups/

# Delete a bucket (must be empty, or use --recursive)
gcloud storage rm -r gs://my-company-data-2024/
```

### Lifecycle Rules (Auto-delete, Auto-archive)

```bash
# Create lifecycle config
cat > lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
      "condition": {"age": 30, "matchesStorageClass": ["STANDARD"]}
    },
    {
      "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
      "condition": {"age": 90, "matchesStorageClass": ["NEARLINE"]}
    },
    {
      "action": {"type": "Delete"},
      "condition": {"age": 365}
    }
  ]
}
EOF

# Apply lifecycle rules
gcloud storage buckets update gs://my-company-data-2024 \
  --lifecycle-file=lifecycle.json
```

**Real-world Example:** Log files auto-transition: Standard (0-30 days) → Nearline (30-90 days) → Coldline (90-365 days) → Deleted (365+ days). Saves ~80% on storage costs.

### Signed URLs (Temporary Access)

```bash
# Generate a signed URL valid for 1 hour
gcloud storage sign-url gs://my-company-data-2024/report.pdf \
  --private-key-file=sa-key.json \
  --duration=1h
```
**Output:**
```
---
resource: gs://my-company-data-2024/report.pdf
signed_url: https://storage.googleapis.com/my-company-data-2024/report.pdf?X-Goog-Algorithm=...&X-Goog-Expires=3600&X-Goog-Signature=...
```

### Making a Bucket Public (Static Website Hosting)

```bash
# Make all objects publicly readable
gcloud storage buckets add-iam-policy-binding gs://my-website-bucket \
  --member=allUsers \
  --role=roles/storage.objectViewer

# Set website configuration
gcloud storage buckets update gs://my-website-bucket \
  --web-main-page-suffix=index.html \
  --web-not-found-page=404.html
```

---

## 3.2 Cloud SQL (Managed Relational Database)

Managed MySQL, PostgreSQL, or SQL Server. Google handles backups, replication, patching.

### Creating an Instance

```bash
# Create a PostgreSQL instance
gcloud sql instances create my-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --storage-size=50GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --availability-type=REGIONAL \
  --root-password=MyStr0ngP@ssw0rd!
```

**What each flag does:**
- `--tier=db-custom-2-8192`: 2 vCPUs, 8 GB RAM
- `--storage-auto-increase`: Disk grows automatically when full
- `--backup-start-time`: Daily backup window (UTC)
- `--availability-type=REGIONAL`: High availability with failover replica

**Output (takes 5-10 minutes):**
```
Creating Cloud SQL instance...done.
Created [https://sqladmin.googleapis.com/sql/v1beta4/projects/my-project/instances/my-postgres].
NAME         DATABASE_VERSION  LOCATION       TIER              PRIMARY_ADDRESS  PRIVATE_ADDRESS  STATUS
my-postgres  POSTGRES_15       us-central1-a  db-custom-2-8192  35.192.xx.xx     -                RUNNABLE
```

### Creating Databases and Users

```bash
# Create a database
gcloud sql databases create myapp_db --instance=my-postgres

# Create a user
gcloud sql users create appuser \
  --instance=my-postgres \
  --password=AppUs3rP@ss!
```

### Connecting to Cloud SQL

```bash
# Connect via Cloud SQL Auth Proxy (recommended)
# Install the proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# Start the proxy
./cloud-sql-proxy my-project:us-central1:my-postgres --port=5432 &

# Connect with psql
psql -h 127.0.0.1 -U appuser -d myapp_db
```

```bash
# Quick connect via gcloud (for admin tasks)
gcloud sql connect my-postgres --user=appuser --database=myapp_db
```
**Output:**
```
Allowlisting your IP for incoming connection for 5 minutes...done.
Connecting to database with SQL user [appuser].Password:
psql (15.4)
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384)
Type "help" for help.

myapp_db=>
```

### Backups and Restore

```bash
# Create an on-demand backup
gcloud sql backups create --instance=my-postgres

# List backups
gcloud sql backups list --instance=my-postgres

# Restore from backup
gcloud sql backups restore BACKUP_ID --restore-instance=my-postgres
```

### Read Replicas

```bash
# Create a read replica
gcloud sql instances create my-postgres-replica \
  --master-instance-name=my-postgres \
  --region=us-east1 \
  --tier=db-custom-2-8192
```

---

## 3.3 Firestore (NoSQL Document Database)

Serverless, scalable NoSQL database. Equivalent to AWS DynamoDB + MongoDB.

### Setup

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create Firestore database (Native mode)
gcloud firestore databases create --location=us-central1
```

### Using Firestore (Python Example)

```python
from google.cloud import firestore

db = firestore.Client()

# CREATE — Add a document
doc_ref = db.collection('users').document('user123')
doc_ref.set({
    'name': 'Alice Johnson',
    'email': 'alice@company.com',
    'age': 30,
    'roles': ['admin', 'developer'],
    'created_at': firestore.SERVER_TIMESTAMP
})

# READ — Get a document
doc = db.collection('users').document('user123').get()
if doc.exists:
    print(f"User: {doc.to_dict()}")
# Output: User: {'name': 'Alice Johnson', 'email': 'alice@company.com', ...}

# QUERY — Find documents
users = db.collection('users') \
    .where('age', '>=', 25) \
    .where('roles', 'array_contains', 'admin') \
    .order_by('age') \
    .limit(10) \
    .stream()

for user in users:
    print(f"{user.id} => {user.to_dict()}")

# UPDATE — Modify fields
doc_ref.update({
    'age': 31,
    'last_login': firestore.SERVER_TIMESTAMP
})

# DELETE
db.collection('users').document('user123').delete()
```

### Firestore Security Rules (for client-side access)

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth.uid == userId;
    }
    match /public/{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

---

## 3.4 BigQuery (Data Warehouse)

Serverless, petabyte-scale analytics. Run SQL on massive datasets in seconds.

### Basic Usage

```bash
# Query a public dataset
bq query --use_legacy_sql=false \
  'SELECT name, SUM(number) as total
   FROM `bigquery-public-data.usa_names.usa_1910_2013`
   WHERE state = "CA"
   GROUP BY name
   ORDER BY total DESC
   LIMIT 10'
```

**Output:**
```
+----------+---------+
|   name   |  total  |
+----------+---------+
| Michael  | 1234567 |
| David    | 1123456 |
| Robert   | 1098765 |
| James    |  987654 |
| John     |  876543 |
...
```

### Creating Datasets and Tables

```bash
# Create a dataset
bq mk --dataset my-project:analytics

# Create a table from schema
bq mk --table my-project:analytics.events \
  timestamp:TIMESTAMP,user_id:STRING,event_type:STRING,properties:JSON

# Load data from Cloud Storage
bq load --source_format=CSV \
  --autodetect \
  analytics.events \
  gs://my-data-bucket/events/*.csv
```

### Loading Data

```bash
# Load JSON data
bq load --source_format=NEWLINE_DELIMITED_JSON \
  analytics.events \
  gs://my-data-bucket/events.json

# Load from local file
bq load --source_format=CSV \
  --skip_leading_rows=1 \
  analytics.events \
  ./local-data.csv \
  timestamp:TIMESTAMP,user_id:STRING,event_type:STRING
```

### Querying

```bash
# Standard SQL query
bq query --use_legacy_sql=false '
  SELECT
    DATE(timestamp) as date,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users
  FROM `my-project.analytics.events`
  WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  GROUP BY date, event_type
  ORDER BY date DESC, event_count DESC
'
```

### Scheduled Queries

```bash
bq mk --transfer_config \
  --target_dataset=analytics \
  --display_name="Daily User Summary" \
  --data_source=scheduled_query \
  --schedule="every 24 hours" \
  --params='{
    "query": "INSERT INTO analytics.daily_summary SELECT DATE(timestamp), COUNT(*) FROM analytics.events WHERE DATE(timestamp) = CURRENT_DATE() - 1 GROUP BY 1"
  }'
```

**Real-world Example — E-commerce Analytics:**
```sql
-- Daily revenue report
SELECT
  DATE(order_date) as date,
  product_category,
  COUNT(DISTINCT order_id) as orders,
  SUM(total_amount) as revenue,
  AVG(total_amount) as avg_order_value,
  COUNT(DISTINCT customer_id) as unique_customers
FROM `ecommerce.orders`
WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date, product_category
ORDER BY date DESC, revenue DESC;
```

---

## 3.5 Cloud Spanner (Globally Distributed Relational DB)

Horizontally scalable relational database with strong consistency. Used by Google Ads, Google Play.

```bash
# Create a Spanner instance
gcloud spanner instances create my-spanner \
  --config=regional-us-central1 \
  --description="Production Spanner" \
  --processing-units=100

# Create a database
gcloud spanner databases create mydb --instance=my-spanner

# Execute DDL
gcloud spanner databases ddl update mydb --instance=my-spanner \
  --ddl='CREATE TABLE Users (
    UserId STRING(36) NOT NULL,
    Name STRING(100),
    Email STRING(255),
    CreatedAt TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true)
  ) PRIMARY KEY (UserId)'
```

**When to use Spanner vs Cloud SQL:**
- Cloud SQL: < 10 TB, single region, cost-sensitive
- Spanner: Global distribution needed, > 10 TB, 99.999% availability required

---

## 3.6 Memorystore (Managed Redis / Memcached)

```bash
# Create a Redis instance
gcloud redis instances create my-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=STANDARD_HA

# Get connection info
gcloud redis instances describe my-cache --region=us-central1 --format="value(host,port)"
```
**Output:**
```
10.0.0.3    6379
```

**Note:** Memorystore is only accessible from within the same VPC (not from the internet).

---

## 3.7 Storage Decision Matrix

| Need | Service | Why |
|------|---------|-----|
| File/image/video storage | Cloud Storage | Object storage, CDN-ready |
| Relational data, < 10 TB | Cloud SQL | Managed MySQL/PostgreSQL |
| Document/NoSQL data | Firestore | Serverless, real-time sync |
| Analytics on large datasets | BigQuery | Petabyte-scale SQL |
| Global relational, 99.999% | Cloud Spanner | Distributed SQL |
| Caching layer | Memorystore | Managed Redis |
| Time-series / IoT data | Bigtable | Wide-column, low latency |

---

## Module 3 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `BucketAlreadyExists` | Bucket name taken globally | Use unique prefix (e.g., company domain) |
| Cloud SQL: `Connection timed out` | IP not allowlisted | Use Cloud SQL Auth Proxy or add IP to authorized networks |
| Cloud SQL: `too many connections` | Connection pool exhausted | Use connection pooling (PgBouncer, HikariCP) |
| BigQuery: `Exceeded rate limits` | Too many queries/sec | Add retry with exponential backoff |
| BigQuery: `Not found: Table` | Wrong project/dataset reference | Use fully qualified name: `project.dataset.table` |
| Firestore: `PERMISSION_DENIED` | Missing IAM role | Grant `roles/datastore.user` to service account |

**Next: Module 4 — Networking →**
