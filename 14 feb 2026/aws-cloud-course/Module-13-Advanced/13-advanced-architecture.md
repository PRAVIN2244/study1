# Module 13: Advanced Architecture & Industry Projects

## 13.1 AWS Well-Architected Framework

The Well-Architected Framework provides best practices across 6 pillars.

```
┌─────────────────────────────────────────────────────────┐
│           AWS Well-Architected Framework                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Operational Excellence                               │
│     └── Automate operations, learn from failures         │
│                                                          │
│  2. Security                                             │
│     └── Protect data, manage access, detect events       │
│                                                          │
│  3. Reliability                                          │
│     └── Recover from failures, scale to meet demand      │
│                                                          │
│  4. Performance Efficiency                               │
│     └── Use resources efficiently, right-size             │
│                                                          │
│  5. Cost Optimization                                    │
│     └── Eliminate waste, use pricing models               │
│                                                          │
│  6. Sustainability                                       │
│     └── Minimize environmental impact                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 13.2 Architecture Patterns

### Pattern 1: Three-Tier Web Application

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                               │
│                       │                                   │
│                  ┌────▼────┐                              │
│                  │ Route53 │  (DNS)                       │
│                  └────┬────┘                              │
│                       │                                   │
│                  ┌────▼────┐                              │
│                  │CloudFront│ (CDN)                       │
│                  └────┬────┘                              │
│                       │                                   │
│  ┌────────────────────▼────────────────────┐             │
│  │              ALB (Public Subnets)        │             │
│  └────────┬───────────────────┬────────────┘             │
│           │                   │                           │
│  ┌────────▼────────┐ ┌───────▼─────────┐                │
│  │  ECS/EC2 (AZ-a) │ │  ECS/EC2 (AZ-b) │  (Private)    │
│  │  App Tier        │ │  App Tier        │               │
│  └────────┬────────┘ └───────┬─────────┘                │
│           │                   │                           │
│  ┌────────▼───────────────────▼─────────┐                │
│  │     RDS Multi-AZ / Aurora             │  (Private)    │
│  │     ElastiCache (Redis)               │               │
│  └──────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### Pattern 2: Microservices Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   API Gateway                            │
│                       │                                   │
│         ┌─────────────┼─────────────┐                    │
│         │             │             │                    │
│    ┌────▼────┐  ┌─────▼────┐  ┌────▼────┐              │
│    │ User    │  │ Order    │  │ Payment │              │
│    │ Service │  │ Service  │  │ Service │              │
│    │ (ECS)   │  │ (ECS)    │  │ (Lambda)│              │
│    └────┬────┘  └────┬─────┘  └────┬────┘              │
│         │            │              │                    │
│    ┌────▼────┐  ┌────▼─────┐  ┌────▼────┐              │
│    │DynamoDB │  │   RDS    │  │DynamoDB │              │
│    │ Users   │  │  Orders  │  │Payments │              │
│    └─────────┘  └──────────┘  └─────────┘              │
│                                                          │
│    ┌──────────────────────────────────┐                  │
│    │         SQS / EventBridge        │  (Async comms)   │
│    └──────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Pattern 3: Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  S3 Upload ──▶ EventBridge ──▶ Lambda (Process)          │
│                    │                  │                   │
│                    ▼                  ▼                   │
│              SQS (Queue)        DynamoDB (Store)         │
│                    │                  │                   │
│                    ▼                  ▼                   │
│              Lambda (Worker)    SNS (Notify)             │
│                    │                                     │
│                    ▼                                     │
│              S3 (Output)                                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 13.3 Route 53 (DNS)

### Create a Hosted Zone

```bash
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference $(date +%s)
```

### Create DNS Records

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "www.example.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z35SXDOTRQ7X7K",
            "DNSName": "my-alb-1234.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": true
          }
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z1HUB23UULQXV",
            "DNSName": "abc123.execute-api.us-east-1.amazonaws.com",
            "EvaluateTargetHealth": false
          }
        }
      }
    ]
  }'
```

### Routing Policies

| Policy | Use Case |
|--------|----------|
| **Simple** | Single resource |
| **Weighted** | A/B testing (70% v1, 30% v2) |
| **Latency** | Route to lowest-latency region |
| **Failover** | Active-passive disaster recovery |
| **Geolocation** | Route by user's country |
| **Multi-value** | Return multiple healthy IPs |

---

## 13.4 CloudFront (CDN)

### Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "unique-ref-'$(date +%s)'",
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "S3-Website",
        "DomainName": "my-website-bucket.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3-Website",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
      "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
      "ForwardedValues": {
        "QueryString": false,
        "Cookies": {"Forward": "none"}
      },
      "MinTTL": 0,
      "DefaultTTL": 86400,
      "MaxTTL": 31536000,
      "Compress": true
    },
    "Enabled": true,
    "DefaultRootObject": "index.html",
    "Comment": "My website CDN"
  }'
```

### Invalidate Cache

```bash
aws cloudfront create-invalidation \
  --distribution-id E1234567890 \
  --paths "/*"
```

---

## 13.5 ElastiCache (Redis)

### Create Redis Cluster

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id myapp-cache \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1 \
  --cache-subnet-group-name myapp-cache-subnets \
  --security-group-ids sg-cache123

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id myapp-cache \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint'
```

### Use Redis in Application

```python
import redis
import json

r = redis.Redis(
    host='myapp-cache.abc123.0001.use1.cache.amazonaws.com',
    port=6379,
    decode_responses=True
)

# Cache API response
def get_user(user_id):
    cache_key = f"user:{user_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss — fetch from database
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    r.setex(cache_key, 3600, json.dumps(user))  # Cache for 1 hour
    return user
```

---

## 13.6 SQS (Simple Queue Service)

### Create and Use Queues

```bash
# Create standard queue
QUEUE_URL=$(aws sqs create-queue \
  --queue-name order-processing \
  --attributes '{
    "VisibilityTimeout": "60",
    "MessageRetentionPeriod": "345600",
    "ReceiveMessageWaitTimeSeconds": "20"
  }' \
  --query 'QueueUrl' --output text)

# Create dead-letter queue (for failed messages)
DLQ_URL=$(aws sqs create-queue --queue-name order-processing-dlq \
  --query 'QueueUrl' --output text)
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url $DLQ_URL \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

# Configure DLQ on main queue
aws sqs set-queue-attributes \
  --queue-url $QUEUE_URL \
  --attributes "{
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
  }"

# Send message
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"orderId": "ORD-001", "amount": 99.99}' \
  --message-attributes '{
    "OrderType": {"DataType": "String", "StringValue": "standard"}
  }'

# Receive message
aws sqs receive-message \
  --queue-url $QUEUE_URL \
  --max-number-of-messages 10 \
  --wait-time-seconds 20

# Delete message (after processing)
aws sqs delete-message \
  --queue-url $QUEUE_URL \
  --receipt-handle <receipt-handle>
```

---

## 13.7 Step Functions (Workflow Orchestration)

### Create a State Machine

```bash
cat > order-workflow.json << 'EOF'
{
  "Comment": "Order Processing Workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:validate-order",
      "Next": "CheckInventory",
      "Catch": [{
        "ErrorEquals": ["ValidationError"],
        "Next": "OrderFailed"
      }]
    },
    "CheckInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:check-inventory",
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:process-payment",
      "Next": "ShipOrder",
      "Retry": [{
        "ErrorEquals": ["PaymentRetryable"],
        "IntervalSeconds": 5,
        "MaxAttempts": 3,
        "BackoffRate": 2.0
      }],
      "Catch": [{
        "ErrorEquals": ["PaymentFailed"],
        "Next": "OrderFailed"
      }]
    },
    "ShipOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ship-order",
      "Next": "NotifyCustomer"
    },
    "NotifyCustomer": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:order-notifications",
        "Message.$": "$.orderConfirmation"
      },
      "End": true
    },
    "OrderFailed": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:handle-failure",
      "End": true
    }
  }
}
EOF

aws stepfunctions create-state-machine \
  --name order-processing \
  --definition file://order-workflow.json \
  --role-arn arn:aws:iam::123456789012:role/StepFunctionsRole
```

---

## 13.8 Industry Project 1: E-Commerce Platform

### Complete Architecture

```bash
#!/bin/bash
# === E-Commerce Platform on AWS ===
# Architecture: CloudFront → ALB → ECS (Fargate) → Aurora + ElastiCache + S3

PROJECT="ecommerce"
REGION="us-east-1"

echo "=== Deploying E-Commerce Platform ==="

# --- 1. VPC (from Module 5 template) ---
aws cloudformation create-stack \
  --stack-name ${PROJECT}-vpc \
  --template-body file://vpc-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=$PROJECT

aws cloudformation wait stack-create-complete --stack-name ${PROJECT}-vpc

# --- 2. Aurora Database ---
aws rds create-db-cluster \
  --db-cluster-identifier ${PROJECT}-db \
  --engine aurora-mysql \
  --master-username admin \
  --master-user-password "$(aws secretsmanager get-random-password --password-length 32 --query 'RandomPassword' --output text)" \
  --db-subnet-group-name ${PROJECT}-db-subnets \
  --storage-encrypted

# --- 3. ElastiCache (Redis) ---
aws elasticache create-replication-group \
  --replication-group-id ${PROJECT}-cache \
  --replication-group-description "Product catalog cache" \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-clusters 2

# --- 4. S3 Buckets ---
aws s3 mb s3://${PROJECT}-product-images
aws s3 mb s3://${PROJECT}-static-assets

# --- 5. ECS Cluster + Services ---
aws ecs create-cluster --cluster-name ${PROJECT}-cluster

# Services: API, Web Frontend, Order Processor
for service in api web worker; do
  echo "Deploying ${service} service..."
done

# --- 6. CloudFront ---
echo "Setting up CDN for static assets..."

# --- 7. SQS for Order Processing ---
aws sqs create-queue --queue-name ${PROJECT}-orders
aws sqs create-queue --queue-name ${PROJECT}-orders-dlq

# --- 8. SNS for Notifications ---
aws sns create-topic --name ${PROJECT}-order-notifications

echo "=== E-Commerce Platform Deployed ==="
```

---

## 13.9 Industry Project 2: Data Pipeline

```
┌──────────────────────────────────────────────────────────┐
│                   Data Pipeline                           │
│                                                           │
│  Data Sources                                             │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐                │
│  │ API Logs │  │ IoT Data │  │ DB Export │                │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│       │              │              │                     │
│       ▼              ▼              ▼                     │
│  ┌──────────────────────────────────────┐                │
│  │     Kinesis Data Firehose            │  (Ingest)      │
│  └──────────────────┬───────────────────┘                │
│                     │                                     │
│                     ▼                                     │
│  ┌──────────────────────────────────────┐                │
│  │     S3 Raw Data Lake                 │  (Store)       │
│  │     s3://company-data-lake/raw/      │                │
│  └──────────────────┬───────────────────┘                │
│                     │                                     │
│                     ▼                                     │
│  ┌──────────────────────────────────────┐                │
│  │     AWS Glue / Lambda                │  (Transform)   │
│  │     ETL Jobs                         │                │
│  └──────────────────┬───────────────────┘                │
│                     │                                     │
│                     ▼                                     │
│  ┌──────────────────────────────────────┐                │
│  │     S3 Processed Data                │  (Store)       │
│  │     s3://company-data-lake/processed/│                │
│  └──────────────────┬───────────────────┘                │
│                     │                                     │
│                     ▼                                     │
│  ┌──────────────────────────────────────┐                │
│  │     Athena / Redshift                │  (Query)       │
│  │     QuickSight                       │  (Visualize)   │
│  └──────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────┘
```

### Athena: Query S3 Data with SQL

```bash
# Create database
aws athena start-query-execution \
  --query-string "CREATE DATABASE IF NOT EXISTS analytics" \
  --result-configuration OutputLocation=s3://my-athena-results/

# Create table from S3 data
aws athena start-query-execution \
  --query-string "
    CREATE EXTERNAL TABLE analytics.web_logs (
      timestamp string,
      ip string,
      method string,
      path string,
      status int,
      latency double
    )
    ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
    LOCATION 's3://company-data-lake/processed/web-logs/'
  " \
  --result-configuration OutputLocation=s3://my-athena-results/

# Query the data
aws athena start-query-execution \
  --query-string "
    SELECT path, COUNT(*) as hits, AVG(latency) as avg_latency
    FROM analytics.web_logs
    WHERE status = 500
    GROUP BY path
    ORDER BY hits DESC
    LIMIT 10
  " \
  --result-configuration OutputLocation=s3://my-athena-results/
```

---

## 13.10 Industry Project 3: Multi-Region Disaster Recovery

### DR Strategies

```
┌─────────────────────────────────────────────────────────┐
│           Disaster Recovery Strategies                   │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Strategy │   RTO    │   RPO    │ Cost                   │
├──────────┼──────────┼──────────┼────────────────────────┤
│ Backup & │ Hours    │ Hours    │ $ (lowest)             │
│ Restore  │          │          │                        │
├──────────┼──────────┼──────────┼────────────────────────┤
│ Pilot    │ 10s min  │ Minutes  │ $$                     │
│ Light    │          │          │                        │
├──────────┼──────────┼──────────┼────────────────────────┤
│ Warm     │ Minutes  │ Seconds  │ $$$                    │
│ Standby  │          │          │                        │
├──────────┼──────────┼──────────┼────────────────────────┤
│ Multi-   │ Near     │ Near     │ $$$$ (highest)         │
│ Active   │ zero     │ zero     │                        │
└──────────┴──────────┴──────────┴────────────────────────┘

RTO = Recovery Time Objective (how fast you recover)
RPO = Recovery Point Objective (how much data you can lose)
```

### Warm Standby Setup

```bash
#!/bin/bash
# === Multi-Region Warm Standby ===

PRIMARY="us-east-1"
SECONDARY="us-west-2"

# --- Cross-region RDS read replica ---
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-dr-replica \
  --source-db-instance-identifier arn:aws:rds:${PRIMARY}:123456789012:db:myapp-database \
  --db-instance-class db.t3.medium \
  --region $SECONDARY

# --- S3 cross-region replication ---
aws s3api put-bucket-replication \
  --bucket myapp-data-${PRIMARY} \
  --replication-configuration '{
    "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
    "Rules": [{
      "Status": "Enabled",
      "Destination": {
        "Bucket": "arn:aws:s3:::myapp-data-'${SECONDARY}'"
      }
    }]
  }'

# --- Route 53 health check + failover ---
aws route53 create-health-check \
  --caller-reference $(date +%s) \
  --health-check-config '{
    "IPAddress": "54.1.2.3",
    "Port": 443,
    "Type": "HTTPS",
    "ResourcePath": "/health",
    "FailureThreshold": 3,
    "RequestInterval": 10
  }'

echo "DR setup complete: Primary=$PRIMARY, Secondary=$SECONDARY"
```

---

## 13.11 Cost Optimization

### AWS Cost Explorer

```bash
# Get last month's costs by service
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[?Metrics.BlendedCost.Amount > `1`].{Service:Keys[0],Cost:Metrics.BlendedCost.Amount}' \
  --output table
```

### Cost Optimization Checklist

```
Compute:
  ✅ Right-size instances (use AWS Compute Optimizer)
  ✅ Use Reserved Instances / Savings Plans for steady workloads
  ✅ Use Spot Instances for fault-tolerant workloads
  ✅ Stop dev/test instances outside business hours
  ✅ Use Graviton (ARM) instances (20% cheaper)

Storage:
  ✅ Use S3 lifecycle policies (Standard → IA → Glacier)
  ✅ Delete unused EBS volumes and snapshots
  ✅ Use gp3 instead of gp2 (20% cheaper)
  ✅ Enable S3 Intelligent-Tiering

Database:
  ✅ Use Aurora Serverless for variable workloads
  ✅ Use Reserved Instances for production RDS
  ✅ Delete unused RDS snapshots

Network:
  ✅ Use VPC endpoints instead of NAT Gateway where possible
  ✅ Use CloudFront to reduce data transfer costs
  ✅ Delete unused Elastic IPs

General:
  ✅ Set up billing alerts
  ✅ Use AWS Budgets for forecasting
  ✅ Review Cost Explorer monthly
  ✅ Tag all resources for cost allocation
```

---

## 13.12 Route 53 — Record Types and Routing Policies

### Record Types

| Type | Purpose | Example |
|------|---------|---------|
| **A** | Maps domain to IPv4 | example.com → 1.2.3.4 |
| **AAAA** | Maps domain to IPv6 | example.com → 2001:db8::1 |
| **CNAME** | Maps domain to another domain | www.example.com → example.com (cannot be used for zone apex) |
| **Alias** | Maps domain to AWS resource | example.com → ALB/CloudFront/S3 (can be used for zone apex) |
| **NS** | Name servers for hosted zone | |
| **MX** | Mail servers | |

### Alias vs CNAME

- **CNAME**: Cannot be used for the root domain (zone apex). example.com → NO, www.example.com → YES
- **Alias**: Can be used for root domain. Free. Points to AWS resources only (ALB, CloudFront, S3, API Gateway, etc.)

### Routing Policies

| Policy | Use Case | How It Works |
|--------|----------|-------------|
| **Simple** | Single resource | Returns one or more values randomly |
| **Weighted** | A/B testing, gradual migration | Route X% to resource A, Y% to resource B |
| **Latency** | Global users | Route to region with lowest latency |
| **Failover** | Active-passive DR | Primary + secondary with health check |
| **Geolocation** | Content localization | Route by user's country/continent |
| **Geoproximity** | Route by geographic distance | Shift traffic with bias values |
| **Multi-value** | Simple load balancing | Return multiple healthy IPs |

---

## 13.13 CloudFront — OAC and Advanced Features

### Origin Access Control (OAC)

OAC restricts S3 bucket access so content is only accessible through CloudFront (not directly via S3 URL). Replaces the older Origin Access Identity (OAI).

```bash
# Create OAC
aws cloudfront create-origin-access-control \
  --origin-access-control-config '{
    "Name": "my-oac",
    "OriginAccessControlOriginType": "s3",
    "SigningBehavior": "always",
    "SigningProtocol": "sigv4"
  }'
```

Then update the S3 bucket policy to allow only the CloudFront distribution.

### CloudFront Functions vs Lambda@Edge

| Feature | CloudFront Functions | Lambda@Edge |
|---------|---------------------|-------------|
| **Runtime** | JavaScript | Node.js, Python |
| **Execution** | < 1 ms | Up to 30 seconds |
| **Triggers** | Viewer request/response only | All 4 trigger points |
| **Use cases** | Header manipulation, URL rewrites, cache key normalization | Auth, A/B testing, dynamic content |

---

## 13.14 AWS Global Accelerator

Global Accelerator uses the AWS global network to route traffic to optimal endpoints. Unlike CloudFront (caches content), Global Accelerator proxies TCP/UDP traffic.

### CloudFront vs Global Accelerator

| Feature | CloudFront | Global Accelerator |
|---------|-----------|-------------------|
| **Type** | CDN (content caching) | Network layer proxy |
| **Protocol** | HTTP/HTTPS | TCP/UDP |
| **Caching** | Yes | No |
| **Static IP** | No (uses DNS) | Yes (2 anycast IPs) |
| **Use case** | Static content, APIs | Gaming, IoT, VoIP, non-HTTP |

---

## 13.15 AWS Storage Extras

### Snow Family (Offline Data Transfer)

| Device | Storage | Use Case |
|--------|---------|----------|
| **Snowcone** | 8 TB HDD / 14 TB SSD | Edge computing, small transfers |
| **Snowball Edge Storage** | 80 TB | Large data migrations |
| **Snowball Edge Compute** | 42 TB + 52 vCPUs | Edge computing + storage |
| **Snowmobile** | 100 PB (truck) | Exabyte-scale migrations |

### Amazon FSx

| Type | Compatible With | Use Case |
|------|----------------|----------|
| **FSx for Windows** | Windows (SMB) | Windows file shares, Active Directory |
| **FSx for Lustre** | Linux (POSIX) | HPC, ML training, video processing |
| **FSx for NetApp ONTAP** | Linux, Windows, macOS | Enterprise NAS |
| **FSx for OpenZFS** | Linux (NFS) | Workloads moving from ZFS |

```bash
# Create FSx for OpenZFS file system
aws fsx create-file-system \
  --file-system-type OPENZFS \
  --storage-capacity 256 \
  --subnet-ids subnet-0abcdef1234567890 \
  --security-group-ids sg-0abcdef1234567890 \
  --open-zfs-configuration '{
    "DeploymentType": "SINGLE_AZ_1",
    "ThroughputCapacity": 64,
    "RootVolumeConfiguration": {
      "DataCompressionType": "ZSTD",
      "NfsExports": [{"ClientConfigurations": [{"Clients": "*", "Options": ["rw","crossmnt"]}]}]
    }
  }'

# Expected output:
# {
#   "FileSystem": {
#     "FileSystemId": "fs-0abcdef1234567890",
#     "FileSystemType": "OPENZFS",
#     "StorageCapacity": 256,
#     "Lifecycle": "CREATING"
#   }
# }

# Mount on EC2 (NFS)
sudo mount -t nfs fs-0abcdef1234567890.fsx.us-east-1.amazonaws.com:/fsx /mnt/openzfs

# FSx for OpenZFS supports: snapshots, clones, compression (LZ4/ZSTD), up to 1M IOPS
# Key advantage: point-in-time snapshots are instant and space-efficient
```

**Real-life use case:** A media company migrating from on-premises ZFS storage uses FSx for OpenZFS. Their applications use NFS mounts and ZFS snapshots — FSx for OpenZFS provides the same interface with no code changes.

### AWS DataSync

Automated data transfer service for moving data between on-premises storage and AWS (S3, EFS, FSx). Uses a purpose-built protocol for speeds up to 10x faster than open-source tools.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ On-Premises  │────▶│  DataSync    │────▶│  S3 / EFS / FSx  │
│ NFS/SMB      │     │  Agent (VM)  │     │                  │
└──────────────┘     └──────────────┘     └──────────────────┘
                     (over internet or Direct Connect)
```

```bash
# Create a DataSync agent (after deploying the agent VM on-premises)
aws datasync create-agent \
  --activation-key ABCDE-FGHIJ-KLMNO-PQRST-12345 \
  --agent-name "onprem-agent-1"

# Create source location (on-premises NFS)
aws datasync create-location-nfs \
  --server-hostname 192.168.1.100 \
  --subdirectory /exports/data \
  --on-prem-config AgentArns=arn:aws:datasync:us-east-1:123456789012:agent/agent-0abcdef1234567890

# Create destination location (S3)
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::my-migration-bucket \
  --s3-config BucketAccessRoleArn=arn:aws:iam::123456789012:role/DataSyncS3Role

# Create and start a transfer task
aws datasync create-task \
  --source-location-arn arn:aws:datasync:us-east-1:123456789012:location/loc-src123 \
  --destination-location-arn arn:aws:datasync:us-east-1:123456789012:location/loc-dst456 \
  --name "nfs-to-s3-migration" \
  --options '{
    "VerifyMode": "POINT_IN_TIME_CONSISTENT",
    "TransferMode": "ALL",
    "PreserveDeletedFiles": "PRESERVE"
  }'

# Expected output:
# {
#   "TaskArn": "arn:aws:datasync:us-east-1:123456789012:task/task-0abcdef1234567890"
# }

# Start the task execution
aws datasync start-task-execution \
  --task-arn arn:aws:datasync:us-east-1:123456789012:task/task-0abcdef1234567890

# Monitor progress
aws datasync describe-task-execution \
  --task-execution-arn arn:aws:datasync:us-east-1:123456789012:task/task-0abcdef1234567890/execution/exec-0abcdef
```

**Real-life use case:** A hospital migrates 50 TB of medical imaging data from on-premises NFS to S3. DataSync agent runs on a VM in their data center, transfers data over Direct Connect with bandwidth throttling during business hours, and verifies data integrity automatically.

### AWS Transfer Family

Managed file transfer service supporting SFTP, FTPS, FTP, and AS2 protocols. Stores files directly in S3 or EFS.

```bash
# Create an SFTP server backed by S3
aws transfer create-server \
  --protocols SFTP \
  --identity-provider-type SERVICE_MANAGED \
  --endpoint-type PUBLIC \
  --tags Key=Name,Value=sftp-server

# Expected output:
# {
#   "ServerId": "s-0abcdef1234567890"
# }

# Create a user for the SFTP server
aws transfer create-user \
  --server-id s-0abcdef1234567890 \
  --user-name vendor-upload \
  --role arn:aws:iam::123456789012:role/TransferS3Role \
  --home-directory /my-bucket/vendor-uploads \
  --ssh-public-key-body "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."

# Expected output:
# {
#   "ServerId": "s-0abcdef1234567890",
#   "UserName": "vendor-upload"
# }

# Test SFTP connection
sftp vendor-upload@s-0abcdef1234567890.server.transfer.us-east-1.amazonaws.com
# sftp> put invoice.csv
# sftp> ls
# invoice.csv
```

**Real-life use case:** A retail company receives daily inventory files from 200 vendors via SFTP. Instead of managing an SFTP server on EC2, they use AWS Transfer Family. Files land directly in S3, triggering a Lambda function that processes them into a DynamoDB table.

### AWS Storage Gateway

Hybrid cloud storage — connects on-premises to AWS cloud storage.

| Type | Protocol | Backed By | Use Case |
|------|----------|-----------|----------|
| **S3 File Gateway** | NFS/SMB | S3 | File shares backed by S3 |
| **FSx File Gateway** | SMB | FSx for Windows | Windows file shares |
| **Volume Gateway** | iSCSI | S3 + EBS snapshots | Block storage (cached/stored) |
| **Tape Gateway** | iSCSI VTL | S3 Glacier | Backup (replace physical tapes) |

---

## 13.16 Kinesis — Deep Dive

### Kinesis Data Streams

Real-time data streaming. Producers send records, consumers process them.

```bash
# Put a record
aws kinesis put-record \
  --stream-name my-stream \
  --partition-key user1 \
  --data "user signup" \
  --cli-binary-format raw-in-base64-out

# Describe stream
aws kinesis describe-stream --stream-name my-stream

# Get shard iterator
SHARD_ITERATOR=$(aws kinesis get-shard-iterator \
  --stream-name my-stream \
  --shard-id shardId-000000000000 \
  --shard-iterator-type TRIM_HORIZON \
  --query 'ShardIterator' --output text)

# Get records
aws kinesis get-records --shard-iterator $SHARD_ITERATOR
```

### Capacity Modes

| Mode | How It Works |
|------|-------------|
| **Provisioned** | You choose number of shards (1 MB/s in, 2 MB/s out per shard) |
| **On-demand** | Auto-scales, pay per stream-hour + per GB |

### Amazon Data Firehose (formerly Kinesis Data Firehose)

Near-real-time delivery to destinations. No code needed.

```
Producers ──▶ Data Firehose ──▶ S3 / Redshift / OpenSearch / HTTP endpoint
                                 (buffered, batched, optionally transformed)
```

- Buffer interval: 0–900 seconds
- Can transform data with Lambda before delivery
- No real-time (near real-time with minimum ~60s latency)

### Kinesis Data Streams vs Data Firehose

| Feature | Data Streams | Data Firehose |
|---------|-------------|---------------|
| **Latency** | Real-time (~200ms) | Near real-time (~60s) |
| **Scaling** | Manual (shards) or on-demand | Automatic |
| **Consumer code** | You write it | No code needed |
| **Data storage** | 1–365 days retention | No storage (delivery only) |
| **Destinations** | Custom (Lambda, apps) | S3, Redshift, OpenSearch, HTTP |

---

## 13.17 CloudFront — Additional Features

### Cache Invalidation

Force CloudFront to remove cached objects before TTL expires.

```bash
aws cloudfront create-invalidation \
  --distribution-id E1ABCDEF \
  --paths "/*"           # Invalidate everything
  # or "/images/logo.png"  # Specific file
```

### Geo Restriction

Restrict access by country using allowlist or blocklist. Uses 3rd-party GeoIP database.

```bash
# Enable geo restriction (blocklist specific countries)
aws cloudfront update-distribution --id E1ABCDEF \
  --distribution-config '{
    ...
    "Restrictions": {
      "GeoRestriction": {
        "RestrictionType": "blacklist",
        "Quantity": 2,
        "Items": ["RU", "CN"]
      }
    }
  }'

# Allowlist mode (only allow specific countries)
# "RestrictionType": "whitelist", "Items": ["US", "CA", "GB"]

# Verify geo restriction
aws cloudfront get-distribution --id E1ABCDEF \
  --query 'Distribution.DistributionConfig.Restrictions.GeoRestriction'

# Expected output:
# {
#   "RestrictionType": "blacklist",
#   "Quantity": 2,
#   "Items": ["CN", "RU"]
# }
```

**Real-life use case:** A streaming service is licensed to operate only in the US and Canada. Geo restriction with an allowlist of `["US", "CA"]` blocks all other countries. Users from blocked countries see a 403 Forbidden error.

### Origin Groups

Provide high availability with primary and secondary origins. If the primary fails (5xx errors), CloudFront automatically fails over to the secondary.

```bash
# Create a distribution with an origin group (primary S3 + failover S3)
# In the distribution config:
# {
#   "Origins": {
#     "Items": [
#       {"Id": "primary-s3", "DomainName": "my-bucket-us-east-1.s3.amazonaws.com", ...},
#       {"Id": "failover-s3", "DomainName": "my-bucket-us-west-2.s3.amazonaws.com", ...}
#     ]
#   },
#   "OriginGroups": {
#     "Quantity": 1,
#     "Items": [{
#       "Id": "s3-origin-group",
#       "FailoverCriteria": {
#         "StatusCodes": {"Quantity": 4, "Items": [500, 502, 503, 504]}
#       },
#       "Members": {
#         "Quantity": 2,
#         "Items": [
#           {"OriginId": "primary-s3"},
#           {"OriginId": "failover-s3"}
#         ]
#       }
#     }]
#   }
# }
```

**Real-life use case:** An e-commerce site uses S3 in us-east-1 as primary origin and S3 in us-west-2 (with CRR) as failover. If us-east-1 has an outage, CloudFront automatically serves content from us-west-2 with no manual intervention.

### Multiple Origins

Route to different origins based on URL path pattern.

```
/api/*    ──▶ ALB origin
/images/* ──▶ S3 origin
/*        ──▶ Default origin
```

```bash
# Create cache behaviors for path-based routing
# In the distribution config:
# {
#   "CacheBehaviors": {
#     "Items": [
#       {
#         "PathPattern": "/api/*",
#         "TargetOriginId": "alb-origin",
#         "ViewerProtocolPolicy": "https-only",
#         "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",  # CachingDisabled
#         "AllowedMethods": {"Quantity": 7, "Items": ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"]}
#       },
#       {
#         "PathPattern": "/images/*",
#         "TargetOriginId": "s3-origin",
#         "ViewerProtocolPolicy": "redirect-to-https",
#         "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6"  # CachingOptimized
#       }
#     ]
#   },
#   "DefaultCacheBehavior": {
#     "TargetOriginId": "default-origin",
#     ...
#   }
# }
```

### Origin Custom Headers

Add custom headers to requests sent from CloudFront to the origin. The origin can verify these headers to ensure requests come only through CloudFront.

```bash
# Add a custom header to an origin (secret shared between CloudFront and ALB)
# In the distribution config origin:
# {
#   "CustomHeaders": {
#     "Quantity": 1,
#     "Items": [{
#       "HeaderName": "X-Custom-Secret",
#       "HeaderValue": "my-secret-value-12345"
#     }]
#   }
# }

# On the ALB, create a listener rule that checks for the header:
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/my-alb/abcdef/1234567890 \
  --priority 1 \
  --conditions '[{"Field":"http-header","HttpHeaderConfig":{"HttpHeaderName":"X-Custom-Secret","Values":["my-secret-value-12345"]}}]' \
  --actions '[{"Type":"forward","TargetGroupArn":"arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-tg/abcdef"}]'

# Default rule returns 403 (blocks direct ALB access)
```

**Real-life use case:** Prevent users from bypassing CloudFront and hitting the ALB directly. The ALB only forwards requests that contain the secret header, which only CloudFront adds.

### CloudFront vs S3 Cross-Region Replication

| Feature | CloudFront | S3 CRR |
|---------|-----------|--------|
| **Purpose** | Cache content at edge locations | Replicate objects to another region |
| **Latency** | Low (edge cache) | Depends on region |
| **Content** | Static + dynamic | Static objects only |
| **TTL** | Configurable (seconds to days) | Always up-to-date (near real-time) |
| **Setup** | Distribution + origin | Replication rule + destination bucket |
| **Cost** | Per request + data transfer | Storage + replication transfer |
| **Use case** | Global content delivery | Compliance, DR, cross-region access |

**When to use CloudFront:** Content is accessed globally and can tolerate TTL-based staleness. **When to use S3 CRR:** Content must be available in specific regions with real-time consistency (e.g., regulatory requirement to store data in EU).

### CloudFront and HTTPS

| Viewer ↔ CloudFront | CloudFront ↔ Origin | Configuration |
|---------------------|---------------------|---------------|
| HTTPS only | HTTPS only | Most secure |
| Redirect HTTP→HTTPS | HTTPS only | Recommended |
| HTTP and HTTPS | Match viewer | Flexible |

```bash
# Request an ACM certificate for CloudFront (MUST be in us-east-1)
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names "*.example.com" \
  --validation-method DNS \
  --region us-east-1

# Expected output:
# {
#   "CertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/abcd-1234"
# }

# Attach certificate to CloudFront distribution
# In the distribution config:
# {
#   "ViewerCertificate": {
#     "ACMCertificateArn": "arn:aws:acm:us-east-1:123456789012:certificate/abcd-1234",
#     "SSLSupportMethod": "sni-only",
#     "MinimumProtocolVersion": "TLSv1.2_2021"
#   }
# }
```

---

## 13.18 Route 53 — Advanced Features

### DNS Terminologies

| Term | Description |
|------|-------------|
| **Domain Registrar** | Where you register domain names (Route 53, GoDaddy, Namecheap) |
| **DNS Records** | A, AAAA, CNAME, NS, MX, TXT, SRV, SOA |
| **Zone File** | Contains DNS records for a domain |
| **Name Server (NS)** | Servers that resolve DNS queries |
| **Top Level Domain (TLD)** | .com, .org, .net, .gov |
| **Second Level Domain (SLD)** | amazon.com, google.com |
| **FQDN** | Fully Qualified Domain Name (e.g., api.example.com.) |
| **TTL** | Time To Live — how long DNS resolvers cache the record |

### CNAME vs Alias Records

| Feature | CNAME | Alias |
|---------|-------|-------|
| **Points to** | Any hostname | AWS resource only (ELB, CloudFront, S3, etc.) |
| **Zone apex** | ❌ Cannot use at zone apex | ✅ Works at zone apex (example.com) |
| **DNS query charge** | Standard charges | Free for Alias to AWS resources |
| **TTL** | You set it | Set by Route 53 automatically |
| **Health checks** | Not directly | ✅ Supports health checks |

```bash
# Create an Alias record pointing to an ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "my-alb-123456.us-east-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# Create a CNAME record (cannot be at zone apex)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "my-alb-123456.us-east-1.elb.amazonaws.com"}]
      }
    }]
  }'
```

**Alias targets:** ELB, CloudFront, API Gateway, S3 website, VPC Interface Endpoint, Global Accelerator, Route 53 record in same hosted zone. **Cannot alias to:** EC2 DNS name.

### Hosted Zones

| Type | Description | Cost |
|------|-------------|------|
| **Public** | Routes internet traffic | $0.50/month |
| **Private** | Routes traffic within VPCs | $0.50/month |

### Calculated Health Checks

Combine multiple health checks into one using OR, AND, or NOT logic. Monitor up to 256 child health checks.

```bash
# Create individual health checks for each endpoint
HC1=$(aws route53 create-health-check --caller-reference "hc1-$(date +%s)" \
  --health-check-config '{
    "IPAddress": "203.0.113.10",
    "Port": 80,
    "Type": "HTTP",
    "ResourcePath": "/health"
  }' --query 'HealthCheck.Id' --output text)

HC2=$(aws route53 create-health-check --caller-reference "hc2-$(date +%s)" \
  --health-check-config '{
    "IPAddress": "203.0.113.20",
    "Port": 80,
    "Type": "HTTP",
    "ResourcePath": "/health"
  }' --query 'HealthCheck.Id' --output text)

# Create a calculated health check (healthy if at least 1 of 2 children is healthy)
aws route53 create-health-check --caller-reference "calc-$(date +%s)" \
  --health-check-config '{
    "Type": "CALCULATED",
    "ChildHealthChecks": ["'"$HC1"'", "'"$HC2"'"],
    "HealthThreshold": 1
  }'

# HealthThreshold: minimum number of child checks that must be healthy
# Set to 0 = always healthy (OR with NOT), set to N = AND logic
```

### Private Hosted Zones Health Checks

Health checkers are outside the VPC — they can't access private endpoints. Solution: Create a CloudWatch Metric + Alarm, then create a health check that monitors the alarm.

```bash
# Step 1: Create a CloudWatch alarm for the private resource
aws cloudwatch put-metric-alarm \
  --alarm-name "private-db-health" \
  --namespace "Custom/Health" \
  --metric-name "DatabaseUp" \
  --dimensions Name=InstanceId,Value=i-0abcdef1234567890 \
  --statistic Average \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 1 \
  --comparison-operator LessThanThreshold

# Step 2: Create a Route 53 health check that monitors the CloudWatch alarm
aws route53 create-health-check --caller-reference "private-hc-$(date +%s)" \
  --health-check-config '{
    "Type": "CLOUDWATCH_METRIC",
    "AlarmIdentifier": {
      "Region": "us-east-1",
      "Name": "private-db-health"
    },
    "InsufficientDataHealthStatus": "Unhealthy"
  }'
```

### Route 53 Resolver Endpoints

Enable DNS resolution between on-premises networks and AWS VPCs.

```
On-Premises DNS ──▶ Inbound Endpoint ──▶ Route 53 Resolver (resolve AWS domains)
Route 53 Resolver ──▶ Outbound Endpoint ──▶ On-Premises DNS (resolve on-prem domains)
```

```bash
# Create an Inbound Resolver Endpoint (on-prem → AWS)
aws route53resolver create-resolver-endpoint \
  --creator-request-id "inbound-$(date +%s)" \
  --name "inbound-from-onprem" \
  --security-group-ids sg-0abcdef1234567890 \
  --direction INBOUND \
  --ip-addresses SubnetId=subnet-0abcdef1234567890,Ip=10.0.1.10 \
                 SubnetId=subnet-0fedcba0987654321,Ip=10.0.2.10

# Create an Outbound Resolver Endpoint (AWS → on-prem)
aws route53resolver create-resolver-endpoint \
  --creator-request-id "outbound-$(date +%s)" \
  --name "outbound-to-onprem" \
  --security-group-ids sg-0abcdef1234567890 \
  --direction OUTBOUND \
  --ip-addresses SubnetId=subnet-0abcdef1234567890 \
                 SubnetId=subnet-0fedcba0987654321

# Create a forwarding rule (forward corp.example.com to on-prem DNS)
aws route53resolver create-resolver-rule \
  --creator-request-id "rule-$(date +%s)" \
  --name "forward-corp-domain" \
  --rule-type FORWARD \
  --domain-name "corp.example.com" \
  --resolver-endpoint-id rslvr-out-0abcdef1234567890 \
  --target-ips "Ip=192.168.1.53,Port=53" "Ip=192.168.1.54,Port=53"

# Associate the rule with a VPC
aws route53resolver associate-resolver-rule \
  --resolver-rule-id rslvr-rr-0abcdef1234567890 \
  --vpc-id vpc-0abcdef1234567890
```

### Hybrid DNS

Combine Route 53 with on-premises DNS servers using Resolver Endpoints for seamless name resolution across hybrid environments.

```
┌──────────────────────┐                    ┌──────────────────────┐
│    On-Premises       │                    │       AWS VPC        │
│                      │                    │                      │
│  DNS Server          │◀── Inbound EP ─────│  Route 53 Resolver   │
│  (192.168.1.53)      │                    │                      │
│                      │── Outbound EP ────▶│  Private Hosted Zone │
│  corp.example.com    │                    │  aws.example.com     │
└──────────────────────┘                    └──────────────────────┘
         (via Direct Connect or VPN)
```

**Flow:** EC2 instance queries `db.corp.example.com` → Route 53 Resolver → Outbound Endpoint → On-premises DNS → returns `192.168.1.100`. On-premises server queries `api.aws.example.com` → On-premises DNS → Inbound Endpoint → Route 53 Resolver → returns `10.0.1.50`.

### DNSSEC (DNS Security Extensions)

Protects against DNS spoofing/poisoning by cryptographically signing DNS records. Route 53 supports DNSSEC for domain registration and hosted zones.

```bash
# Enable DNSSEC signing on a hosted zone
# Step 1: Create a KSK (Key Signing Key) using a KMS key
aws route53 create-key-signing-key \
  --hosted-zone-id Z1234567890 \
  --name "my-ksk" \
  --key-management-service-arn arn:aws:kms:us-east-1:123456789012:key/abcd-1234 \
  --status ACTIVE

# Step 2: Enable DNSSEC signing
aws route53 enable-hosted-zone-dnssec \
  --hosted-zone-id Z1234567890

# Step 3: Create a chain of trust (add DS record at registrar)
aws route53domains associate-delegation-signer-to-domain \
  --domain-name example.com \
  --signing-attributes '{
    "Algorithm": 13,
    "Flags": 257,
    "PublicKey": "base64-encoded-public-key"
  }'

# Verify DNSSEC is working
dig +dnssec example.com
# Look for RRSIG records in the response
```

### Route 53 Traffic Flow

Visual editor for creating complex routing configurations. Supports versioning of traffic policies.

```bash
# Create a traffic policy (JSON definition)
aws route53 create-traffic-policy \
  --name "geo-latency-policy" \
  --document '{
    "AWSPolicyFormatVersion": "2015-10-01",
    "RecordType": "A",
    "Endpoints": {
      "us-endpoint": {"Type": "elastic-load-balancer", "Value": "my-alb-us.us-east-1.elb.amazonaws.com"},
      "eu-endpoint": {"Type": "elastic-load-balancer", "Value": "my-alb-eu.eu-west-1.elb.amazonaws.com"}
    },
    "Rules": {
      "geo-rule": {
        "RuleType": "geo",
        "Locations": [
          {"EndpointReference": "us-endpoint", "IsDefault": true},
          {"EndpointReference": "eu-endpoint", "Continent": "EU"}
        ]
      }
    },
    "StartRule": "geo-rule"
  }'

# Create a traffic policy instance (apply to a hosted zone)
aws route53 create-traffic-policy-instance \
  --hosted-zone-id Z1234567890 \
  --name "app.example.com" \
  --ttl 60 \
  --traffic-policy-id abcdef-1234 \
  --traffic-policy-version 1
```

### Route 53 DNS Query Logging

Log all DNS queries made to a hosted zone. Logs are sent to CloudWatch Logs.

```bash
# Create a query logging configuration
aws route53 create-query-logging-config \
  --hosted-zone-id Z1234567890 \
  --cloud-watch-logs-log-group-arn arn:aws:logs:us-east-1:123456789012:log-group:/aws/route53/example.com

# Expected output:
# {
#   "QueryLoggingConfig": {
#     "Id": "abcdef-1234",
#     "HostedZoneId": "Z1234567890",
#     "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:/aws/route53/example.com"
#   }
# }

# View DNS query logs in CloudWatch
aws logs filter-log-events \
  --log-group-name /aws/route53/example.com \
  --limit 5

# Log format includes: timestamp, hosted zone ID, query name, query type,
# response code, protocol (UDP/TCP), edge location, client IP
```

### Route 53 Resolver DNS Firewall

Filter and block DNS queries to known malicious domains. Protects VPC resources from connecting to bad domains.

```bash
# Create a domain list (block list)
aws route53resolver create-firewall-domain-list \
  --name "blocked-domains" \
  --creator-request-id "block-$(date +%s)"

# Add domains to the block list
aws route53resolver update-firewall-domains \
  --firewall-domain-list-id rslvr-fdl-0abcdef1234567890 \
  --operation ADD \
  --domains "malware.example.com" "phishing.example.com" "*.badsite.com"

# Create a firewall rule group
aws route53resolver create-firewall-rule-group \
  --name "security-rules" \
  --creator-request-id "rules-$(date +%s)"

# Add a BLOCK rule
aws route53resolver create-firewall-rule \
  --firewall-rule-group-id rslvr-frg-0abcdef1234567890 \
  --firewall-domain-list-id rslvr-fdl-0abcdef1234567890 \
  --priority 100 \
  --action BLOCK \
  --block-response NXDOMAIN \
  --name "block-malicious"

# Associate with a VPC
aws route53resolver associate-firewall-rule-group \
  --firewall-rule-group-id rslvr-frg-0abcdef1234567890 \
  --vpc-id vpc-0abcdef1234567890 \
  --priority 101 \
  --name "protect-prod-vpc"
```

**Real-life use case:** Block EC2 instances from resolving cryptocurrency mining pool domains or known C2 (command and control) server domains. Use AWS-managed domain lists for automatic threat intelligence updates.

### Using a 3rd Party Registrar with Route 53

You can register a domain with any registrar (GoDaddy, Namecheap) and use Route 53 as the DNS service.

```bash
# Step 1: Create a hosted zone in Route 53
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "$(date +%s)"

# Expected output includes NS records:
# {
#   "DelegationSet": {
#     "NameServers": [
#       "ns-111.awsdns-11.com",
#       "ns-222.awsdns-22.net",
#       "ns-333.awsdns-33.org",
#       "ns-444.awsdns-44.co.uk"
#     ]
#   }
# }

# Step 2: Update the NS records at your 3rd party registrar
# Go to GoDaddy/Namecheap → Domain Settings → Custom Nameservers
# Enter the 4 NS records from the Route 53 hosted zone

# Step 3: Verify propagation (may take 24-48 hours)
dig NS example.com
# Should return the Route 53 nameservers
```

---

## 13.19 Key Takeaways

1. Follow the Well-Architected Framework's 6 pillars
2. Design for failure: multi-AZ, auto-scaling, health checks
3. Use the right architecture pattern for your use case
4. Implement DR based on your RTO/RPO requirements
5. Use CloudFront + Route 53 for global distribution
6. Decouple services with SQS, SNS, and EventBridge
7. Use Step Functions for complex workflows
8. Optimize costs continuously — cloud bills grow without attention
9. Route 53: Use Alias records for zone apex, Latency routing for global users
10. CloudFront OAC restricts S3 access to CloudFront only
11. Global Accelerator for non-HTTP traffic needing static IPs
12. Snow Family for offline data transfer; Storage Gateway for hybrid cloud
13. FSx: Windows (SMB), Lustre (HPC), NetApp ONTAP (enterprise NAS)
14. Kinesis Data Streams for real-time; Data Firehose for near-real-time delivery to S3/Redshift
