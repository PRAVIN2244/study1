# Module 16: Data & Analytics

## 16.1 Amazon Athena

Serverless query service that analyzes data in S3 using standard SQL. No infrastructure to manage.

- Pay per query: ~$5 per TB scanned
- Supports CSV, JSON, Parquet, ORC, Avro
- Built on Presto engine

### Performance Tips

- Use **columnar formats** (Parquet, ORC) — up to 90% cost savings
- **Partition** data by date/region (e.g., `s3://bucket/year=2024/month=06/`)
- **Compress** data (gzip, snappy, zstd)
- Use larger files (> 128 MB) to reduce overhead

### Federated Query

Athena can query data beyond S3 using Lambda-based connectors: RDS, DynamoDB, Redshift, CloudWatch Logs, on-premises databases.

```sql
-- Query S3 access logs (see Module 4 for table creation)
SELECT requesturi_operation, httpstatus, count(*)
FROM s3_access_logs_db.mybucket_logs
GROUP BY requesturi_operation, httpstatus;
```

---

## 16.2 Amazon Redshift

Petabyte-scale data warehouse based on PostgreSQL. Optimized for OLAP (Online Analytical Processing) and columnar storage.

- Not serverless (provision nodes) — Redshift Serverless is also available
- 10x better performance than other data warehouses
- Columnar storage with massively parallel query execution (MPP)

### Cluster Architecture

```
Leader Node (SQL parsing, query planning)
    │
    ├── Compute Node 1 (executes queries)
    ├── Compute Node 2
    └── Compute Node N
```

### Loading Data into Redshift

```
S3 ──▶ COPY command ──▶ Redshift (best method, parallel load)
Kinesis Data Firehose ──▶ Redshift (near real-time)
EC2/JDBC ──▶ INSERT (slow, avoid for bulk)
```

### Redshift Spectrum

Query data in S3 without loading it into Redshift. Processing happens on dedicated Spectrum nodes.

```bash
# Create an external schema pointing to S3 data via Glue Data Catalog
# (Run in Redshift SQL editor)
# CREATE EXTERNAL SCHEMA spectrum_schema
# FROM DATA CATALOG
# DATABASE 'my_glue_db'
# IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftSpectrumRole'
# CREATE EXTERNAL DATABASE IF NOT EXISTS;

# Create an external table pointing to S3 data
# CREATE EXTERNAL TABLE spectrum_schema.sales (
#   sale_id INT,
#   product VARCHAR(100),
#   amount DECIMAL(10,2),
#   sale_date DATE
# )
# ROW FORMAT DELIMITED
# FIELDS TERMINATED BY ','
# STORED AS TEXTFILE
# LOCATION 's3://my-data-lake/sales/';

# Query S3 data directly from Redshift (no loading needed)
# SELECT product, SUM(amount) as total_sales
# FROM spectrum_schema.sales
# WHERE sale_date >= '2024-01-01'
# GROUP BY product
# ORDER BY total_sales DESC
# LIMIT 10;

# Join S3 data with Redshift local tables
# SELECT r.customer_name, s.product, s.amount
# FROM local_schema.customers r
# JOIN spectrum_schema.sales s ON r.customer_id = s.customer_id;
```

**Real-life use case:** A company keeps hot data (last 3 months) in Redshift and cold data (historical) in S3 as Parquet files. Spectrum queries join both seamlessly, avoiding the cost of loading terabytes of historical data into Redshift.

### Snapshots & DR

- Automated snapshots every 8 hours or 5 GB (configurable)
- Can copy snapshots to another region for DR

---

## 16.3 Amazon OpenSearch Service (formerly Elasticsearch)

Search and analytics engine. Commonly used for log analytics, full-text search, and application monitoring.

### Common Patterns

```
DynamoDB ──▶ DynamoDB Stream ──▶ Lambda ──▶ OpenSearch (search index)
CloudWatch Logs ──▶ Subscription Filter ──▶ Lambda ──▶ OpenSearch
Kinesis Data Streams ──▶ Data Firehose ──▶ OpenSearch
```

- Not serverless (provision instances) — OpenSearch Serverless is available
- Comes with OpenSearch Dashboards (visualization)
- Supports SQL queries via SQL plugin

---

## 16.4 Amazon EMR (Elastic MapReduce)

Managed Hadoop/Spark cluster for big data processing.

### Node Types

| Node | Purpose |
|------|---------|
| **Master** | Manages cluster, coordinates tasks |
| **Core** | Runs tasks AND stores data (HDFS) |
| **Task** | Runs tasks only (no storage) — use Spot instances |

### Purchasing Options

- Master: On-Demand or Reserved (must be stable)
- Core: On-Demand or Reserved (data storage)
- Task: Spot instances (can be interrupted, no data loss)

Use cases: Machine learning, web indexing, big data processing, log analysis.

---

## 16.5 Amazon QuickSight

Serverless BI (Business Intelligence) service for creating dashboards and visualizations.

- Pay per session pricing
- Integrates with: RDS, Aurora, Redshift, Athena, S3, OpenSearch, Timestream
- Supports SPICE (in-memory computation engine)
- Row-level security for multi-tenant dashboards

---

## 16.6 AWS Glue

Serverless ETL (Extract, Transform, Load) service.

### Glue Components

| Component | Purpose |
|-----------|---------|
| **Glue Data Catalog** | Central metadata repository (databases, tables, schemas) |
| **Glue Crawlers** | Scan data sources and populate the Data Catalog |
| **Glue ETL Jobs** | Transform data (Python/Scala on Apache Spark) |
| **Glue Studio** | Visual ETL job editor |

### Common Pattern

```
S3 (raw data) ──▶ Glue Crawler ──▶ Glue Data Catalog
                                        │
                                   Glue ETL Job
                                        │
                                   S3 (Parquet) ──▶ Athena / Redshift
```

### Convert to Parquet

```
S3 (CSV) ──▶ Glue ETL ──▶ S3 (Parquet) ──▶ Athena (faster, cheaper queries)
```

---

## 16.7 AWS Lake Formation

Build a secure data lake in days instead of months. Built on top of Glue.

- Centralized permissions management (row/column-level security)
- Combines data from S3, RDS, NoSQL into a single data lake
- Built-in data deduplication (ML-powered)
- Fine-grained access control across Athena, Redshift, EMR

```
Data Sources ──▶ Lake Formation ──▶ S3 Data Lake ──▶ Athena / Redshift / EMR
(RDS, S3, NoSQL)   (ingest, clean,     (centralized)    (query, analyze)
                    catalog, secure)
```

```bash
# Register an S3 location as a data lake location
aws lakeformation register-resource \
  --resource-arn arn:aws:s3:::my-data-lake \
  --use-service-linked-role

# Grant permissions to a user (column-level access)
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::123456789012:role/AnalystRole \
  --resource '{
    "Table": {
      "DatabaseName": "sales_db",
      "Name": "transactions",
      "TableWildcard": {}
    }
  }' \
  --permissions SELECT \
  --permissions-with-grant-option []

# Grant column-level access (only specific columns)
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::123456789012:role/MarketingRole \
  --resource '{
    "TableWithColumns": {
      "DatabaseName": "sales_db",
      "Name": "customers",
      "ColumnNames": ["customer_id", "city", "state"]
    }
  }' \
  --permissions SELECT

# List permissions
aws lakeformation list-permissions \
  --query 'PrincipalResourcePermissions[].{Principal:Principal.DataLakePrincipalIdentifier,Resource:Resource,Permissions:Permissions}'
```

**Real-life use case:** A healthcare company has data from 5 sources (EHR, billing, labs, pharmacy, claims) in S3. Lake Formation catalogs all data, and fine-grained permissions ensure the billing team can only see billing columns, while researchers get anonymized patient data. All access is audited via CloudTrail.

---

## 16.8 Amazon MSK (Managed Streaming for Apache Kafka)

Fully managed Apache Kafka service.

### Kinesis Data Streams vs MSK

| Feature | Kinesis Data Streams | Amazon MSK |
|---------|---------------------|------------|
| **Protocol** | AWS proprietary | Apache Kafka |
| **Message size** | 1 MB | 1 MB default (configurable higher) |
| **Retention** | 1–365 days | As long as you want |
| **Scaling** | Shard splitting/merging | Add partitions to topics |
| **Consumers** | AWS SDK, Lambda, KCL | Any Kafka consumer |
| **Best for** | AWS-native streaming | Kafka migrations, Kafka ecosystem |

### MSK Consumers

- Kinesis Data Analytics for Apache Flink
- AWS Glue (Spark streaming)
- Lambda
- Custom Kafka consumers (EC2, ECS, EKS)

### Amazon Managed Service for Apache Flink (formerly Kinesis Data Analytics)

Process and analyze streaming data in real-time using Apache Flink (Java, Scala, Python, SQL).

```bash
# Create a Flink application
aws kinesisanalyticsv2 create-application \
  --application-name "real-time-analytics" \
  --runtime-environment FLINK-1_18 \
  --service-execution-role arn:aws:iam::123456789012:role/FlinkRole \
  --application-configuration '{
    "FlinkApplicationConfiguration": {
      "CheckpointConfiguration": {
        "ConfigurationType": "CUSTOM",
        "CheckpointingEnabled": true,
        "CheckpointInterval": 60000
      },
      "ParallelismConfiguration": {
        "ConfigurationType": "CUSTOM",
        "Parallelism": 4,
        "ParallelismPerKPU": 1,
        "AutoScalingEnabled": true
      }
    },
    "ApplicationCodeConfiguration": {
      "CodeContent": {
        "S3ContentLocation": {
          "BucketARN": "arn:aws:s3:::my-flink-apps",
          "FileKey": "flink-app-1.0.jar"
        }
      },
      "CodeContentType": "ZIPFILE"
    }
  }'

# Start the application
aws kinesisanalyticsv2 start-application \
  --application-name "real-time-analytics" \
  --run-configuration '{
    "SqlRunConfigurations": [],
    "FlinkRunConfiguration": {"AllowNonRestoredState": true}
  }'
```

**Sources:** Kinesis Data Streams, Amazon MSK. **Sinks:** S3, Kinesis Data Streams, Kinesis Data Firehose.

**Real-life use case:** A ride-sharing app processes GPS events from 100K drivers in real-time using Flink. The application calculates surge pricing zones, detects anomalous routes, and updates driver ETAs — all with sub-second latency.

---

## 16.9 Big Data Ingestion Pipeline

```
IoT Devices ──▶ IoT Core ──▶ Kinesis Data Streams ──▶ Data Firehose ──▶ S3 (raw)
                                                                            │
                                                                       SQS (trigger)
                                                                            │
                                                                       Lambda (ETL)
                                                                            │
                                                                       S3 (processed)
                                                                            │
                                                                       Athena (query)
                                                                            │
                                                                       QuickSight (dashboard)
```

All serverless. Scales automatically. Pay per use.

```bash
# Step 1: Create Kinesis Data Stream
aws kinesis create-stream --stream-name iot-data --shard-count 2

# Step 2: Create Firehose delivery stream (Kinesis → S3)
aws firehose create-delivery-stream \
  --delivery-stream-name iot-to-s3 \
  --delivery-stream-type KinesisStreamAsSource \
  --kinesis-stream-source-configuration '{
    "KinesisStreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/iot-data",
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseRole"
  }' \
  --s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseRole",
    "BucketARN": "arn:aws:s3:::my-data-lake",
    "Prefix": "raw/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
    "ErrorOutputPrefix": "errors/",
    "BufferingHints": {"SizeInMBs": 64, "IntervalInSeconds": 60},
    "CompressionFormat": "GZIP"
  }'

# Step 3: Create Glue Crawler to catalog the data
aws glue create-crawler \
  --name iot-data-crawler \
  --role arn:aws:iam::123456789012:role/GlueRole \
  --database-name iot_db \
  --targets '{"S3Targets": [{"Path": "s3://my-data-lake/raw/"}]}'

# Step 4: Query with Athena
# SELECT device_id, AVG(temperature) as avg_temp
# FROM iot_db.raw
# WHERE year='2024' AND month='01'
# GROUP BY device_id
# HAVING AVG(temperature) > 80;
```

**Real-life use case:** A smart building company ingests sensor data from 10K IoT devices. Data flows through Kinesis → Firehose → S3 (partitioned by date). Glue catalogs it, Athena queries it, and QuickSight dashboards show real-time energy consumption. Total cost: ~$200/month for millions of events.

---

## 16.10 Key Takeaways

1. Athena: Serverless SQL on S3. Use Parquet + partitioning for cost savings
2. Redshift: Data warehouse for OLAP. Use COPY from S3 for bulk loading
3. OpenSearch: Full-text search and log analytics. Pair with DynamoDB/CloudWatch
4. EMR: Managed Hadoop/Spark. Use Spot instances for Task nodes
5. QuickSight: Serverless BI dashboards. Pay per session
6. Glue: Serverless ETL + Data Catalog. Convert CSV to Parquet for Athena
7. Lake Formation: Secure data lake with fine-grained access control
8. MSK: Managed Kafka. Use when migrating from Kafka or need Kafka ecosystem
9. Kinesis for AWS-native streaming; MSK for Kafka-compatible streaming
