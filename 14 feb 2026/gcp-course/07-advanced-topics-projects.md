# Module 7: Advanced Topics & Real-world Projects

---

## 7.1 Pub/Sub (Messaging)

Asynchronous messaging service for decoupling microservices. Equivalent to AWS SNS + SQS.

### Core Concepts

- **Topic**: A named channel where publishers send messages
- **Subscription**: A named resource representing a stream of messages from a topic
- **Publisher**: Sends messages to a topic
- **Subscriber**: Receives messages from a subscription
- **Acknowledgment**: Subscriber confirms message processing

### Creating Topics and Subscriptions

```bash
# Enable Pub/Sub API
gcloud services enable pubsub.googleapis.com

# Create a topic
gcloud pubsub topics create order-events
```
**Output:**
```
Created topic [projects/my-project/topics/order-events].
```

```bash
# Create a pull subscription
gcloud pubsub subscriptions create order-processor \
  --topic=order-events \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --expiration-period=never
```

**What each flag does:**
- `--ack-deadline=60`: Subscriber has 60 seconds to acknowledge
- `--message-retention-duration=7d`: Unacknowledged messages kept for 7 days
- `--expiration-period=never`: Subscription never auto-deletes

```bash
# Create a push subscription (sends to an HTTP endpoint)
gcloud pubsub subscriptions create order-webhook \
  --topic=order-events \
  --push-endpoint=https://my-api-abc.a.run.app/webhook/orders
```

### Publishing Messages

```bash
# Publish a message
gcloud pubsub topics publish order-events \
  --message='{"order_id": "ORD-001", "amount": 99.99, "status": "created"}'

# Publish with attributes
gcloud pubsub topics publish order-events \
  --message='{"order_id": "ORD-002", "amount": 149.99}' \
  --attribute=event_type=order_created,priority=high
```
**Output:**
```
messageIds:
- '1234567890'
```

### Consuming Messages

```bash
# Pull messages (for testing)
gcloud pubsub subscriptions pull order-processor --limit=5 --auto-ack
```
**Output:**
```
DATA                                                          MESSAGE_ID   ORDERING_KEY  ATTRIBUTES
{"order_id": "ORD-001", "amount": 99.99, "status": "created"} 1234567890                 event_type=order_created
```

### Python Publisher and Subscriber

```python
# publisher.py
from google.cloud import pubsub_v1
import json

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("my-project", "order-events")

def publish_order_event(order_id, amount, event_type):
    data = json.dumps({
        "order_id": order_id,
        "amount": amount,
        "event_type": event_type
    }).encode("utf-8")

    future = publisher.publish(
        topic_path,
        data,
        event_type=event_type,  # attribute
        source="order-service"  # attribute
    )
    print(f"Published message ID: {future.result()}")

publish_order_event("ORD-100", 299.99, "order_created")
```

```python
# subscriber.py
from google.cloud import pubsub_v1
import json

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path("my-project", "order-processor")

def callback(message):
    data = json.loads(message.data.decode("utf-8"))
    print(f"Processing order: {data['order_id']}, amount: ${data['amount']}")

    # Process the order...
    # If successful:
    message.ack()
    # If failed (will be redelivered):
    # message.nack()

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}...")

try:
    streaming_pull_future.result()  # Block forever
except KeyboardInterrupt:
    streaming_pull_future.cancel()
    streaming_pull_future.result()
```

### Dead Letter Topics

```bash
# Create a dead letter topic for failed messages
gcloud pubsub topics create order-events-dlq

gcloud pubsub subscriptions create order-events-dlq-sub \
  --topic=order-events-dlq

# Update subscription to use dead letter topic
gcloud pubsub subscriptions update order-processor \
  --dead-letter-topic=order-events-dlq \
  --max-delivery-attempts=5
```

---

## 7.2 Dataflow (Stream & Batch Processing)

Managed Apache Beam service for ETL pipelines.

### Batch Pipeline Example

```python
# pipeline.py — Read from BigQuery, transform, write to Cloud Storage
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions([
    '--project=my-project',
    '--region=us-central1',
    '--runner=DataflowRunner',
    '--temp_location=gs://my-bucket/temp',
    '--staging_location=gs://my-bucket/staging',
    '--job_name=daily-export',
])

with beam.Pipeline(options=options) as p:
    (
        p
        | 'ReadFromBQ' >> beam.io.ReadFromBigQuery(
            query='SELECT user_id, event_type, timestamp FROM analytics.events WHERE DATE(timestamp) = CURRENT_DATE() - 1',
            use_standard_sql=True
        )
        | 'FilterPurchases' >> beam.Filter(lambda row: row['event_type'] == 'purchase')
        | 'FormatCSV' >> beam.Map(lambda row: f"{row['user_id']},{row['event_type']},{row['timestamp']}")
        | 'WriteToGCS' >> beam.io.WriteToText(
            'gs://my-bucket/exports/purchases',
            file_name_suffix='.csv',
            header='user_id,event_type,timestamp'
        )
    )
```

```bash
# Run the pipeline
python pipeline.py
```

### Streaming Pipeline Example

```python
# streaming_pipeline.py — Real-time processing from Pub/Sub to BigQuery
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
import json

options = PipelineOptions([
    '--project=my-project',
    '--region=us-central1',
    '--runner=DataflowRunner',
    '--temp_location=gs://my-bucket/temp',
    '--streaming',
])

with beam.Pipeline(options=options) as p:
    (
        p
        | 'ReadPubSub' >> beam.io.ReadFromPubSub(topic='projects/my-project/topics/order-events')
        | 'ParseJSON' >> beam.Map(lambda msg: json.loads(msg))
        | 'AddTimestamp' >> beam.Map(lambda x: {**x, 'processed_at': beam.utils.timestamp.Timestamp.now().to_rfc3339()})
        | 'WriteToBQ' >> beam.io.WriteToBigQuery(
            'my-project:analytics.processed_orders',
            schema='order_id:STRING,amount:FLOAT,event_type:STRING,processed_at:TIMESTAMP',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
        )
    )
```

```bash
# List running Dataflow jobs
gcloud dataflow jobs list --region=us-central1
```
**Output:**
```
JOB_ID                                JOB_NAME       TYPE       CREATION_TIME        STATE
2024-01-15_03_30_00-1234567890        daily-export   Batch      2024-01-15 10:30:00  Done
2024-01-15_03_25_00-0987654321        stream-orders  Streaming  2024-01-15 10:25:00  Running
```

---

## 7.3 AI/ML APIs (Pre-trained Models)

GCP offers ready-to-use ML APIs — no ML expertise needed.

### Vision API (Image Analysis)

```bash
gcloud services enable vision.googleapis.com

# Analyze an image
gcloud ml vision detect-labels gs://my-bucket/photo.jpg
```
**Output:**
```
{
  "responses": [
    {
      "labelAnnotations": [
        {"description": "Dog", "score": 0.98},
        {"description": "Pet", "score": 0.95},
        {"description": "Golden Retriever", "score": 0.92},
        {"description": "Outdoor", "score": 0.88}
      ]
    }
  ]
}
```

```bash
# OCR — Extract text from image
gcloud ml vision detect-text gs://my-bucket/receipt.jpg

# Detect faces
gcloud ml vision detect-faces gs://my-bucket/group-photo.jpg

# Safe search (detect explicit content)
gcloud ml vision detect-safe-search gs://my-bucket/uploaded-image.jpg
```

### Natural Language API (Text Analysis)

```bash
gcloud services enable language.googleapis.com

# Sentiment analysis
gcloud ml language analyze-sentiment --content="This product is amazing! Best purchase I've ever made."
```
**Output:**
```
{
  "documentSentiment": {
    "magnitude": 1.8,
    "score": 0.9
  },
  "sentences": [
    {
      "text": {"content": "This product is amazing!"},
      "sentiment": {"magnitude": 0.9, "score": 0.9}
    },
    {
      "text": {"content": "Best purchase I've ever made."},
      "sentiment": {"magnitude": 0.9, "score": 0.9}
    }
  ]
}
```

```bash
# Entity extraction
gcloud ml language analyze-entities --content="Google was founded by Larry Page and Sergey Brin in Menlo Park, California."
```
**Output:**
```
{
  "entities": [
    {"name": "Google", "type": "ORGANIZATION", "salience": 0.5},
    {"name": "Larry Page", "type": "PERSON", "salience": 0.2},
    {"name": "Sergey Brin", "type": "PERSON", "salience": 0.15},
    {"name": "Menlo Park", "type": "LOCATION", "salience": 0.1},
    {"name": "California", "type": "LOCATION", "salience": 0.05}
  ]
}
```

### Translation API

```bash
gcloud services enable translate.googleapis.com

# Translate text
gcloud ml translate translate-text \
  --target-language=es \
  --content="Hello, how are you today?"
```
**Output:**
```
{
  "translations": [
    {
      "translatedText": "Hola, ¿cómo estás hoy?",
      "detectedSourceLanguage": "en"
    }
  ]
}
```

### Speech-to-Text API

```bash
gcloud services enable speech.googleapis.com

gcloud ml speech recognize gs://my-bucket/audio.wav \
  --language-code=en-US
```
**Output:**
```
{
  "results": [
    {
      "alternatives": [
        {
          "transcript": "Hello and welcome to our product demo",
          "confidence": 0.96
        }
      ]
    }
  ]
}
```

### Vertex AI (Custom ML)

```bash
# Enable Vertex AI
gcloud services enable aiplatform.googleapis.com

# Create a dataset
gcloud ai datasets create \
  --display-name="product-images" \
  --metadata-schema-uri=gs://google-cloud-aiplatform/schema/dataset/metadata/image_1.0.0.yaml \
  --region=us-central1

# Train a custom model (AutoML)
gcloud ai custom-jobs create \
  --display-name="train-product-classifier" \
  --region=us-central1 \
  --worker-pool-spec=machine-type=n1-standard-4,replica-count=1,container-image-uri=gcr.io/cloud-aiplatform/training/tf-gpu.2-12:latest
```

---

## 7.4 Anthos (Hybrid & Multi-Cloud)

Run Kubernetes workloads across GCP, on-premises, AWS, and Azure from a single control plane.

```bash
# Register an external cluster with Anthos
gcloud container fleet memberships register my-on-prem-cluster \
  --context=my-k8s-context \
  --kubeconfig=~/.kube/config \
  --enable-workload-identity

# List registered clusters
gcloud container fleet memberships list
```

---

## 7.5 Real-world Project 1: E-commerce Platform

**Architecture:**
```
Users → Cloud CDN → Cloud Load Balancer
                         ↓
                    Cloud Run (API Gateway)
                    ↓           ↓           ↓
            Product Service  Order Service  User Service
            (Cloud Run)      (Cloud Run)    (Cloud Run)
                    ↓           ↓           ↓
            Cloud SQL       Pub/Sub →    Firestore
            (Products)      Order Events  (User Profiles)
                              ↓
                    Cloud Function
                    (Send Email via SendGrid)
                              ↓
                    BigQuery (Analytics)
```

```bash
# Infrastructure setup
PROJECT=ecommerce-prod

# 1. Create VPC
gcloud compute networks create ecom-vpc --subnet-mode=custom --project=$PROJECT
gcloud compute networks subnets create ecom-subnet \
  --network=ecom-vpc --region=us-central1 --range=10.0.0.0/20 --project=$PROJECT

# 2. Create Cloud SQL (Products database)
gcloud sql instances create ecom-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --storage-size=100GB \
  --storage-auto-increase \
  --backup-start-time=02:00 \
  --project=$PROJECT

gcloud sql databases create products --instance=ecom-db --project=$PROJECT
gcloud sql databases create orders --instance=ecom-db --project=$PROJECT

# 3. Create Pub/Sub topics
gcloud pubsub topics create order-created --project=$PROJECT
gcloud pubsub topics create order-completed --project=$PROJECT
gcloud pubsub topics create order-failed --project=$PROJECT

# 4. Create Cloud Storage for product images
gcloud storage buckets create gs://${PROJECT}-product-images \
  --location=us-central1 --uniform-bucket-level-access

# 5. Deploy services
gcloud run deploy product-service \
  --image=us-central1-docker.pkg.dev/$PROJECT/apps/product-service:v1 \
  --region=us-central1 \
  --memory=1Gi --cpu=2 \
  --min-instances=2 --max-instances=50 \
  --set-secrets=DB_PASSWORD=prod-db-password:latest \
  --set-env-vars="DB_HOST=/cloudsql/$PROJECT:us-central1:ecom-db" \
  --add-cloudsql-instances=$PROJECT:us-central1:ecom-db \
  --project=$PROJECT

gcloud run deploy order-service \
  --image=us-central1-docker.pkg.dev/$PROJECT/apps/order-service:v1 \
  --region=us-central1 \
  --memory=1Gi --cpu=2 \
  --min-instances=2 --max-instances=100 \
  --set-secrets=DB_PASSWORD=prod-db-password:latest,STRIPE_KEY=prod-stripe-key:latest \
  --project=$PROJECT

# 6. Deploy email notification function
gcloud functions deploy send-order-email \
  --gen2 --runtime=python312 --region=us-central1 \
  --source=./functions/email \
  --entry-point=send_email \
  --trigger-topic=order-completed \
  --set-secrets=SENDGRID_KEY=prod-sendgrid-key:latest \
  --project=$PROJECT

# 7. Set up monitoring
gcloud monitoring uptime create \
  --display-name="Product API Health" \
  --resource-type=uptime-url \
  --hostname=api.myecommerce.com \
  --path=/api/health \
  --protocol=HTTPS --period=60
```

---

## 7.6 Real-world Project 2: Data Analytics Pipeline

**Architecture:**
```
Data Sources → Pub/Sub → Dataflow → BigQuery → Looker Studio
                                        ↓
                                  Scheduled Queries
                                        ↓
                                  Cloud Storage (Reports)
                                        ↓
                                  Email via Cloud Functions
```

```bash
PROJECT=analytics-prod

# 1. Create BigQuery datasets
bq mk --dataset $PROJECT:raw_events
bq mk --dataset $PROJECT:processed
bq mk --dataset $PROJECT:reports

# 2. Create raw events table
bq mk --table $PROJECT:raw_events.clickstream \
  user_id:STRING,session_id:STRING,page_url:STRING,event_type:STRING,timestamp:TIMESTAMP,properties:JSON

# 3. Create Pub/Sub for real-time ingestion
gcloud pubsub topics create clickstream-events --project=$PROJECT
gcloud pubsub subscriptions create clickstream-to-dataflow \
  --topic=clickstream-events --project=$PROJECT

# 4. Create Cloud Storage for Dataflow temp files
gcloud storage buckets create gs://${PROJECT}-dataflow-temp --location=us-central1

# 5. Deploy Dataflow streaming job (using template)
gcloud dataflow jobs run clickstream-pipeline \
  --gcs-location=gs://dataflow-templates/latest/PubSub_to_BigQuery \
  --region=us-central1 \
  --parameters=\
inputTopic=projects/$PROJECT/topics/clickstream-events,\
outputTableSpec=$PROJECT:raw_events.clickstream \
  --project=$PROJECT

# 6. Create scheduled query for daily aggregation
bq mk --transfer_config \
  --target_dataset=processed \
  --display_name="Daily Page Views" \
  --data_source=scheduled_query \
  --schedule="every day 06:00" \
  --params='{
    "query": "INSERT INTO processed.daily_pageviews SELECT DATE(timestamp) as date, page_url, COUNT(*) as views, COUNT(DISTINCT user_id) as unique_visitors FROM raw_events.clickstream WHERE DATE(timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY) GROUP BY date, page_url"
  }'

# 7. Export weekly report to Cloud Storage
bq mk --transfer_config \
  --target_dataset=reports \
  --display_name="Weekly Report Export" \
  --data_source=scheduled_query \
  --schedule="every monday 08:00" \
  --params='{
    "query": "EXPORT DATA OPTIONS(uri=\"gs://analytics-prod-reports/weekly/*.csv\", format=\"CSV\", overwrite=true, header=true) AS SELECT * FROM processed.daily_pageviews WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)",
    "destination_table_name_template": "",
    "write_disposition": "WRITE_TRUNCATE"
  }'
```

---

## 7.7 Real-world Project 3: CI/CD Platform with GKE

**Architecture:**
```
GitHub → Cloud Build → Artifact Registry → Cloud Deploy
                                               ↓
                                    GKE Dev → GKE Staging → GKE Prod
                                    (auto)    (canary)      (manual approval)
```

```bash
PROJECT=platform-prod

# 1. Create GKE clusters
gcloud container clusters create-auto dev-cluster \
  --region=us-central1 --project=$PROJECT

gcloud container clusters create-auto staging-cluster \
  --region=us-central1 --project=$PROJECT

gcloud container clusters create-auto prod-cluster \
  --region=us-central1 --project=$PROJECT

# 2. Create Artifact Registry
gcloud artifacts repositories create apps \
  --repository-format=docker \
  --location=us-central1 \
  --project=$PROJECT

# 3. Create Kubernetes manifests
mkdir -p k8s/base k8s/overlays/{dev,staging,prod}

cat > k8s/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          image: my-app  # Replaced by Cloud Deploy
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: my-app
EOF

# 4. Create Cloud Deploy pipeline
cat > clouddeploy.yaml << 'EOF'
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata:
  name: my-app-pipeline
serialPipeline:
  stages:
    - targetId: dev
    - targetId: staging
      strategy:
        canary:
          runtimeConfig:
            kubernetes:
              serviceNetworking:
                service: my-app
                deployment: my-app
          canaryDeployment:
            percentages: [25, 50, 75]
    - targetId: prod
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: dev
gke:
  cluster: projects/platform-prod/locations/us-central1/clusters/dev-cluster
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: staging
gke:
  cluster: projects/platform-prod/locations/us-central1/clusters/staging-cluster
requireApproval: true
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata:
  name: prod
gke:
  cluster: projects/platform-prod/locations/us-central1/clusters/prod-cluster
requireApproval: true
EOF

gcloud deploy apply --file=clouddeploy.yaml --region=us-central1 --project=$PROJECT

# 5. Create Cloud Build trigger
gcloud builds triggers create github \
  --name="deploy-my-app" \
  --repo-name=my-app \
  --repo-owner=my-org \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml \
  --project=$PROJECT
```

---

## Module 7 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Pub/Sub: `NOT_FOUND: Topic not found` | Wrong project or topic name | Use full path: `projects/PROJECT/topics/TOPIC` |
| Pub/Sub: Messages redelivered | Not acknowledging within deadline | Increase `--ack-deadline` or ack faster |
| Dataflow: `ZONE_RESOURCE_POOL_EXHAUSTED` | No capacity | Change region or use `--workerMachineType` |
| Vision API: `INVALID_ARGUMENT` | Image too large or wrong format | Resize to < 20MB, use JPEG/PNG |
| BigQuery: `Quota exceeded: too many table update operations` | Too many streaming inserts | Batch inserts or use load jobs |
| Cloud Deploy: `PERMISSION_DENIED` | Missing deploy roles | Grant `roles/clouddeploy.releaser` |

**Next: Module 8 — Common Errors & Troubleshooting →**
