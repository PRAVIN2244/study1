# Module 6: RDS & DynamoDB - Databases

## 6.1 AWS Database Services Overview

```
┌─────────────────────────────────────────────────────────┐
│                 AWS Database Services                    │
├──────────────┬──────────────┬───────────────────────────┤
│  Relational  │   NoSQL      │   Specialized             │
├──────────────┼──────────────┼───────────────────────────┤
│ RDS          │ DynamoDB     │ ElastiCache (Redis/Memc.) │
│ Aurora       │ DocumentDB   │ Neptune (Graph)           │
│              │ Keyspaces    │ Timestream (Time-series)  │
│              │              │ QLDB (Ledger)             │
└──────────────┴──────────────┴───────────────────────────┘
```

### When to Use What

| Requirement | Service | Example |
|------------|---------|---------|
| Traditional SQL, joins, transactions | **RDS** | E-commerce orders |
| High-performance SQL, auto-scaling | **Aurora** | SaaS platform |
| Key-value, millisecond latency | **DynamoDB** | Session store, gaming leaderboard |
| In-memory caching | **ElastiCache** | API response caching |
| Graph relationships | **Neptune** | Social network, fraud detection |

---

## 6.2 Relational vs Non-Relational Databases

Before diving into AWS services, understand the two fundamental database types:

```
┌─────────────────────────────────────────────────────────────────────┐
│  RELATIONAL (SQL)                  NON-RELATIONAL (NoSQL)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Data stored in TABLES             Data stored in DOCUMENTS,         │
│  with rows and columns             KEY-VALUE pairs, or GRAPHS       │
│                                                                      │
│  ┌────┬───────┬────────┐          ┌──────────────────────────┐     │
│  │ ID │ Name  │ Email  │          │ {                        │     │
│  ├────┼───────┼────────┤          │   "id": 1,              │     │
│  │ 1  │ Alice │ a@x.co │          │   "name": "Alice",      │     │
│  │ 2  │ Bob   │ b@x.co │          │   "email": "a@x.co",    │     │
│  └────┴───────┴────────┘          │   "orders": [...]       │     │
│                                    │ }                        │     │
│  Fixed schema (all rows            └──────────────────────────┘     │
│  have same columns)               Flexible schema (each document    │
│                                    can have different fields)        │
│  JOINS between tables              No joins — data is denormalized  │
│  ACID transactions                 Eventually consistent (usually)  │
│                                                                      │
│  Best for:                         Best for:                         │
│  ✓ Complex queries with joins      ✓ High-speed reads/writes        │
│  ✓ Financial transactions          ✓ Flexible/changing data models  │
│  ✓ Reporting and analytics         ✓ Massive scale (millions req/s) │
│  ✓ Data integrity is critical      ✓ Real-time apps, gaming, IoT    │
│                                                                      │
│  AWS Services:                     AWS Services:                     │
│    RDS, Aurora                       DynamoDB, DocumentDB            │
│    (MySQL, PostgreSQL,               ElastiCache (Redis)             │
│     Oracle, SQL Server)              Neptune (Graph)                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Quick Decision Guide

```
Do you need complex JOINs between tables?
  ├── YES → Relational (RDS/Aurora)
  └── NO
       │
       Do you need millisecond latency at massive scale?
         ├── YES → DynamoDB
         └── NO
              │
              Do you need flexible document storage?
                ├── YES → DocumentDB
                └── NO → Start with RDS (most versatile)
```

---

## 6.3 RDS (Relational Database Service)

RDS manages relational databases — AWS handles patching, backups, failover.

### Supported Engines

| Engine | Free Tier | Use Case |
|--------|-----------|----------|
| MySQL | Yes | General purpose, WordPress |
| PostgreSQL | Yes | Complex queries, GIS data |
| MariaDB | Yes | MySQL alternative |
| Oracle | No | Enterprise legacy apps |
| SQL Server | No | .NET applications |
| Aurora (MySQL/PostgreSQL) | No | High-performance production |

### Manual Steps via AWS Console: Create an RDS Database

**Step 1: Create a DB Subnet Group**
1. Go to **RDS → Subnet groups → Create DB subnet group**
2. Name: `myapp-db-subnets`
3. Description: `Subnets for application database`
4. VPC: select your VPC
5. Add subnets: select private subnets in at least 2 AZs
6. Click **Create**

**Step 2: Create the RDS Instance**
1. Go to **RDS → Databases → Create database**
2. Choose **Standard create**
3. Engine: `MySQL` (or PostgreSQL)
4. Version: latest available
5. Templates: `Free tier` (for learning) or `Production`
6. DB instance identifier: `myapp-db`
7. Master username: `admin`
8. Master password: set a strong password
9. Instance class: `db.t3.micro` (Free Tier)
10. Storage: 20 GiB, gp3, enable auto-scaling (max 100 GiB)
11. Connectivity:
    - VPC: select your VPC
    - Subnet group: `myapp-db-subnets`
    - Public access: **No** (database should be in private subnet)
    - Security group: create new or select existing (allow port 3306 from app subnet)
12. Database name: `myappdb`
13. Backup retention: 7 days
14. Click **Create database** (takes 5-10 minutes)

**Step 3: Connect to the Database**
1. Go to **RDS → Databases** → click on your DB
2. Copy the **Endpoint** (e.g., `myapp-db.abc123.us-east-1.rds.amazonaws.com`)
3. From an EC2 instance in the same VPC:
   ```bash
   mysql -h myapp-db.abc123.us-east-1.rds.amazonaws.com -u admin -p myappdb
   ```

**Step 4: Create a Snapshot (Backup)**
1. Select the database → **Actions → Take snapshot**
2. Name: `myapp-db-backup-2024-01-15`
3. Click **Take snapshot**

**Step 5: Create a Read Replica**
1. Select the database → **Actions → Create read replica**
2. DB instance identifier: `myapp-db-read`
3. Instance class: `db.t3.micro`
4. Region: same or different region
5. Click **Create read replica**

**Step 6: Delete the Database**
1. Select the database → **Actions → Delete**
2. Uncheck "Create final snapshot" (for dev/test only)
3. Check "I acknowledge..."
4. Type `delete me` → **Delete**

### Create an RDS Subnet Group (CLI)

```bash
# RDS requires subnets in at least 2 AZs
aws rds create-db-subnet-group \
  --db-subnet-group-name myapp-db-subnets \
  --db-subnet-group-description "Database subnets for myapp" \
  --subnet-ids subnet-aaa111 subnet-bbb222
```

**Expected Output:**
```json
{
    "DBSubnetGroup": {
        "DBSubnetGroupName": "myapp-db-subnets",
        "DBSubnetGroupDescription": "Database subnets for myapp",
        "VpcId": "vpc-0abcd1234",
        "SubnetGroupStatus": "Complete",
        "Subnets": [
            {"SubnetIdentifier": "subnet-aaa111", "SubnetAvailabilityZone": {"Name": "us-east-1a"}},
            {"SubnetIdentifier": "subnet-bbb222", "SubnetAvailabilityZone": {"Name": "us-east-1b"}}
        ]
    }
}
```

### Create a Security Group for RDS

```bash
DB_SG=$(aws ec2 create-security-group \
  --group-name rds-sg \
  --description "Allow MySQL from app servers" \
  --vpc-id vpc-0abcd1234 \
  --query 'GroupId' --output text)

# Allow MySQL (3306) from app security group only
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG \
  --protocol tcp \
  --port 3306 \
  --source-group sg-app-servers
```

### Create an RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier myapp-database \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --engine-version 8.0 \
  --master-username admin \
  --master-user-password 'MyStr0ng!DbPass#2024' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name myapp-db-subnets \
  --vpc-security-group-ids $DB_SG \
  --backup-retention-period 7 \
  --multi-az \
  --storage-encrypted \
  --no-publicly-accessible \
  --tags Key=Name,Value=myapp-database Key=Environment,Value=production
```

**Command Breakdown:**
| Flag | Meaning |
|------|---------|
| `--db-instance-identifier` | Unique name for the instance |
| `--db-instance-class` | Hardware (db.t3.micro = Free Tier) |
| `--engine mysql` | Database engine |
| `--master-username` | Admin username |
| `--allocated-storage 20` | 20 GB disk |
| `--storage-type gp3` | SSD storage |
| `--multi-az` | Standby replica in another AZ |
| `--storage-encrypted` | Encrypt data at rest |
| `--no-publicly-accessible` | No public IP (private only) |
| `--backup-retention-period 7` | Keep backups for 7 days |

**Expected Output (truncated):**
```json
{
    "DBInstance": {
        "DBInstanceIdentifier": "myapp-database",
        "DBInstanceClass": "db.t3.micro",
        "Engine": "mysql",
        "DBInstanceStatus": "creating",
        "Endpoint": null,
        "MultiAZ": true,
        "StorageEncrypted": true
    }
}
```

### Wait and Get Endpoint

```bash
# Wait for instance to be available (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier myapp-database

# Get connection endpoint
aws rds describe-db-instances \
  --db-instance-identifier myapp-database \
  --query 'DBInstances[0].Endpoint' \
  --output table
```

**Expected Output:**
```
--------------------------------------------------------------
|                    Endpoint                                 |
+-------------------+----------------------------------------+
|  Address          | myapp-database.c9abc123.us-east-1.rds.amazonaws.com |
|  Port             | 3306                                   |
+-------------------+----------------------------------------+
```

### Connect to RDS

```bash
# From an EC2 instance in the same VPC:
mysql -h myapp-database.c9abc123.us-east-1.rds.amazonaws.com \
      -u admin -p

# Test connection
mysql> SHOW DATABASES;
mysql> CREATE DATABASE myapp;
mysql> USE myapp;
mysql> CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
mysql> INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
mysql> SELECT * FROM users;
```

### RDS Snapshots (Backups)

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier myapp-database \
  --db-snapshot-identifier myapp-backup-2024-01-15

# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier myapp-database \
  --query 'DBSnapshots[].{ID:DBSnapshotIdentifier,Status:Status,Created:SnapshotCreateTime}' \
  --output table

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier myapp-restored \
  --db-snapshot-identifier myapp-backup-2024-01-15
```

### Read Replicas

```bash
# Create a read replica (for read-heavy workloads)
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-read-replica \
  --source-db-instance-identifier myapp-database \
  --db-instance-class db.t3.micro

# Cross-region read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier myapp-eu-replica \
  --source-db-instance-identifier myapp-database \
  --db-instance-class db.t3.micro \
  --region eu-west-1
```

### Modify RDS Instance

```bash
# Scale up (applied during maintenance window)
aws rds modify-db-instance \
  --db-instance-identifier myapp-database \
  --db-instance-class db.t3.medium \
  --apply-immediately

# Increase storage
aws rds modify-db-instance \
  --db-instance-identifier myapp-database \
  --allocated-storage 50
```

### Delete RDS Instance

```bash
# Delete with final snapshot
aws rds delete-db-instance \
  --db-instance-identifier myapp-database \
  --final-db-snapshot-identifier myapp-final-snapshot

# Delete without snapshot (dev only!)
aws rds delete-db-instance \
  --db-instance-identifier myapp-database \
  --skip-final-snapshot
```

---

## 6.4 Aurora

Aurora is AWS's cloud-native database — 5x faster than MySQL, 3x faster than PostgreSQL.

### Aurora Architecture

```
┌─────────────────────────────────────────────┐
│              Aurora Cluster                  │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Writer   │  │ Reader 1 │  │ Reader 2 │  │
│  │ Instance │  │ Instance │  │ Instance │  │
│  │ (AZ-a)   │  │ (AZ-b)   │  │ (AZ-c)   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
│  ┌────▼──────────────▼──────────────▼────┐  │
│  │     Shared Storage (6 copies, 3 AZs)  │  │
│  │     Auto-scales up to 128 TB          │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Create Aurora Cluster

```bash
# Create cluster
aws rds create-db-cluster \
  --db-cluster-identifier myapp-aurora \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password 'AuroraPass!2024' \
  --db-subnet-group-name myapp-db-subnets \
  --vpc-security-group-ids $DB_SG \
  --storage-encrypted \
  --backup-retention-period 7

# Create writer instance
aws rds create-db-instance \
  --db-instance-identifier myapp-aurora-writer \
  --db-cluster-identifier myapp-aurora \
  --db-instance-class db.r6g.large \
  --engine aurora-mysql

# Create reader instance
aws rds create-db-instance \
  --db-instance-identifier myapp-aurora-reader \
  --db-cluster-identifier myapp-aurora \
  --db-instance-class db.r6g.large \
  --engine aurora-mysql
```

### Aurora Serverless v2

```bash
# Create serverless cluster (auto-scales 0.5 to 128 ACUs)
aws rds create-db-cluster \
  --db-cluster-identifier myapp-serverless \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password 'ServerlessPass!2024' \
  --db-subnet-group-name myapp-db-subnets \
  --vpc-security-group-ids $DB_SG \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=16
```

---

## 6.5 DynamoDB

DynamoDB is a fully managed NoSQL key-value and document database with single-digit millisecond latency.

### Real-World Analogy
- **RDS** = A library with organized shelves (structured, relationships between books)
- **DynamoDB** = A warehouse with labeled boxes (fast retrieval by label, no relationships)

### Manual Steps via AWS Console: Create and Use DynamoDB Table

**Create a table:**
1. Go to **DynamoDB → Tables → Create table**
2. Table name: `Users`
3. Partition key: `user_id` (String)
4. Sort key: leave empty (or add `created_at` for composite key)
5. Table settings: `Default settings` (on-demand billing)
6. Click **Create table**

**Add an item:**
1. Click on the table → **Explore table items**
2. Click **Create item**
3. Add attributes:
   - `user_id`: `user-001`
   - Click **Add new attribute** → String → `name`: `Alice`
   - Click **Add new attribute** → String → `email`: `alice@example.com`
4. Click **Create item**

**Query items:**
1. Go to **Explore table items**
2. Select **Query** (not Scan)
3. Partition key: `user_id` = `user-001`
4. Click **Run**

**Delete a table:**
1. Select the table → **Actions → Delete table**
2. Type `confirm` → **Delete**

### DynamoDB Concepts

| Concept | Meaning | Example |
|---------|---------|---------|
| **Table** | Collection of items | `Users` |
| **Item** | A single record (row) | `{userId: "123", name: "Alice"}` |
| **Attribute** | A field (column) | `name`, `email` |
| **Partition Key** | Primary key (hash) | `userId` |
| **Sort Key** | Optional secondary key | `createdAt` |
| **RCU** | Read Capacity Unit | 1 strongly consistent read/sec (4KB) |
| **WCU** | Write Capacity Unit | 1 write/sec (1KB) |

### Create a DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name Users \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Environment,Value=production
```

**Command Breakdown:**
| Flag | Meaning |
|------|---------|
| `--attribute-definitions` | Define attribute names and types (S=String, N=Number, B=Binary) |
| `--key-schema` | Define primary key (HASH=partition key, RANGE=sort key) |
| `--billing-mode PAY_PER_REQUEST` | On-demand pricing (no capacity planning) |

**Expected Output:**
```json
{
    "TableDescription": {
        "TableName": "Users",
        "TableStatus": "CREATING",
        "KeySchema": [
            {"AttributeName": "userId", "KeyType": "HASH"}
        ],
        "BillingModeSummary": {
            "BillingMode": "PAY_PER_REQUEST"
        }
    }
}
```

### Table with Sort Key (Composite Key)

```bash
aws dynamodb create-table \
  --table-name Orders \
  --attribute-definitions \
    AttributeName=customerId,AttributeType=S \
    AttributeName=orderDate,AttributeType=S \
  --key-schema \
    AttributeName=customerId,KeyType=HASH \
    AttributeName=orderDate,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

### Put Item (Insert)

```bash
aws dynamodb put-item \
  --table-name Users \
  --item '{
    "userId": {"S": "user-001"},
    "name": {"S": "Alice Johnson"},
    "email": {"S": "alice@example.com"},
    "age": {"N": "30"},
    "active": {"BOOL": true},
    "tags": {"L": [{"S": "admin"}, {"S": "developer"}]},
    "address": {"M": {
      "city": {"S": "New York"},
      "zip": {"S": "10001"}
    }}
  }'
```

**DynamoDB Data Types:**
| Type | Code | Example |
|------|------|---------|
| String | `S` | `{"S": "hello"}` |
| Number | `N` | `{"N": "42"}` |
| Boolean | `BOOL` | `{"BOOL": true}` |
| List | `L` | `{"L": [{"S": "a"}, {"S": "b"}]}` |
| Map | `M` | `{"M": {"key": {"S": "value"}}}` |
| Null | `NULL` | `{"NULL": true}` |
| Binary | `B` | `{"B": "base64data"}` |
| String Set | `SS` | `{"SS": ["a", "b"]}` |
| Number Set | `NS` | `{"NS": ["1", "2"]}` |

### Get Item (Read by Primary Key)

```bash
aws dynamodb get-item \
  --table-name Users \
  --key '{"userId": {"S": "user-001"}}'
```

**Expected Output:**
```json
{
    "Item": {
        "userId": {"S": "user-001"},
        "name": {"S": "Alice Johnson"},
        "email": {"S": "alice@example.com"},
        "age": {"N": "30"},
        "active": {"BOOL": true}
    }
}
```

### Query (Search by Partition Key)

```bash
# Get all orders for a customer
aws dynamodb query \
  --table-name Orders \
  --key-condition-expression "customerId = :cid AND orderDate BETWEEN :start AND :end" \
  --expression-attribute-values '{
    ":cid": {"S": "customer-001"},
    ":start": {"S": "2024-01-01"},
    ":end": {"S": "2024-12-31"}
  }'
```

### Scan (Full Table Scan — avoid in production)

```bash
aws dynamodb scan \
  --table-name Users \
  --filter-expression "age > :min_age" \
  --expression-attribute-values '{":min_age": {"N": "25"}}' \
  --select COUNT
```

### Update Item

```bash
aws dynamodb update-item \
  --table-name Users \
  --key '{"userId": {"S": "user-001"}}' \
  --update-expression "SET #n = :name, age = :age, updatedAt = :ts" \
  --expression-attribute-names '{"#n": "name"}' \
  --expression-attribute-values '{
    ":name": {"S": "Alice Smith"},
    ":age": {"N": "31"},
    ":ts": {"S": "2024-01-15T12:00:00Z"}
  }' \
  --return-values ALL_NEW
```

**Note:** `#n` is used because `name` is a reserved word in DynamoDB.

### Delete Item

```bash
aws dynamodb delete-item \
  --table-name Users \
  --key '{"userId": {"S": "user-001"}}'
```

### Batch Operations

```bash
# Batch write (up to 25 items)
aws dynamodb batch-write-item --request-items '{
  "Users": [
    {"PutRequest": {"Item": {"userId": {"S": "user-002"}, "name": {"S": "Bob"}}}},
    {"PutRequest": {"Item": {"userId": {"S": "user-003"}, "name": {"S": "Charlie"}}}},
    {"DeleteRequest": {"Key": {"userId": {"S": "user-old"}}}}
  ]
}'

# Batch get (up to 100 items)
aws dynamodb batch-get-item --request-items '{
  "Users": {
    "Keys": [
      {"userId": {"S": "user-002"}},
      {"userId": {"S": "user-003"}}
    ]
  }
}'
```

### Global Secondary Index (GSI)

```bash
# Add GSI to query by email
aws dynamodb update-table \
  --table-name Users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --global-secondary-index-updates '[{
    "Create": {
      "IndexName": "email-index",
      "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
      "Projection": {"ProjectionType": "ALL"}
    }
  }]'

# Query using GSI
aws dynamodb query \
  --table-name Users \
  --index-name email-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email": {"S": "alice@example.com"}}'
```

### DynamoDB Streams

```bash
# Enable streams (for change data capture)
aws dynamodb update-table \
  --table-name Users \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### Delete Table

```bash
aws dynamodb delete-table --table-name Users
```

---

## 6.6 DynamoDB vs RDS Decision Matrix

```
Choose RDS when:                    Choose DynamoDB when:
├── Complex joins needed            ├── Simple key-value lookups
├── ACID transactions               ├── Massive scale (millions of req/sec)
├── Complex queries (GROUP BY)      ├── Single-digit ms latency required
├── Existing SQL expertise          ├── Schema flexibility needed
├── Data < 64 TB                    ├── Serverless architecture
└── Relational data model           └── Event-driven (streams)
```

---

## 6.7 Industry Project: E-Commerce Database Design

### RDS for Orders + DynamoDB for Product Catalog

```bash
#!/bin/bash
# === E-Commerce Database Setup ===

# --- DynamoDB: Product Catalog (high-read, flexible schema) ---
aws dynamodb create-table \
  --table-name Products \
  --attribute-definitions \
    AttributeName=productId,AttributeType=S \
    AttributeName=category,AttributeType=S \
    AttributeName=price,AttributeType=N \
  --key-schema \
    AttributeName=productId,KeyType=HASH \
  --global-secondary-indexes '[
    {
      "IndexName": "category-price-index",
      "KeySchema": [
        {"AttributeName": "category", "KeyType": "HASH"},
        {"AttributeName": "price", "KeyType": "RANGE"}
      ],
      "Projection": {"ProjectionType": "ALL"}
    }
  ]' \
  --billing-mode PAY_PER_REQUEST

# Insert sample products
aws dynamodb put-item --table-name Products --item '{
  "productId": {"S": "PROD-001"},
  "name": {"S": "Wireless Mouse"},
  "category": {"S": "Electronics"},
  "price": {"N": "29.99"},
  "stock": {"N": "150"},
  "specs": {"M": {
    "color": {"S": "Black"},
    "wireless": {"BOOL": true},
    "battery": {"S": "AA"}
  }}
}'

# Query: Get all electronics under $50
aws dynamodb query \
  --table-name Products \
  --index-name category-price-index \
  --key-condition-expression "category = :cat AND price < :max" \
  --expression-attribute-values '{
    ":cat": {"S": "Electronics"},
    ":max": {"N": "50"}
  }'

# --- DynamoDB: Shopping Cart (session-based, TTL) ---
aws dynamodb create-table \
  --table-name ShoppingCart \
  --attribute-definitions \
    AttributeName=sessionId,AttributeType=S \
  --key-schema \
    AttributeName=sessionId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL (auto-delete expired carts)
aws dynamodb update-time-to-live \
  --table-name ShoppingCart \
  --time-to-live-specification Enabled=true,AttributeName=expiresAt

echo "E-Commerce databases created!"
```

---

## 6.8 Common Errors & Troubleshooting

### RDS Errors

**Error 1: "Cannot connect to RDS"**
```bash
# Checklist:
# 1. Security group allows your source
aws ec2 describe-security-groups --group-ids sg-xxx

# 2. RDS is not publicly accessible (connect from EC2 in same VPC)
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].PubliclyAccessible'

# 3. Correct endpoint
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].Endpoint'

# 4. Instance is available
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].DBInstanceStatus'
```

**Error 2: "Storage full"**
```bash
# Check current storage
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].{Allocated:AllocatedStorage,Used:AllocatedStorage}'

# Increase storage
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --allocated-storage 50 \
  --apply-immediately
```

### DynamoDB Errors

**Error 1: "ProvisionedThroughputExceededException"**
```
An error occurred (ProvisionedThroughputExceededException)
```
**Fix:** Switch to on-demand or increase provisioned capacity:
```bash
aws dynamodb update-table \
  --table-name MyTable \
  --billing-mode PAY_PER_REQUEST
```

**Error 2: "ValidationException: The number of attributes in key schema must match"**
**Fix:** Ensure `--attribute-definitions` includes all attributes used in `--key-schema` and GSIs.

**Error 3: "ResourceNotFoundException: Requested resource not found"**
```bash
# Check table exists
aws dynamodb list-tables
# Check region
aws dynamodb describe-table --table-name MyTable --region us-east-1
```

---

## 6.9 Aurora — Advanced Features

### Aurora Serverless v2

Automatically scales compute capacity based on demand. No capacity planning needed.

```bash
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora-serverless \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=16 \
  --master-username admin \
  --master-user-password "SecurePass123!"

aws rds create-db-instance \
  --db-instance-identifier my-aurora-serverless-instance \
  --db-cluster-identifier my-aurora-serverless \
  --db-instance-class db.serverless \
  --engine aurora-mysql
```

**When to use:** Infrequent, intermittent, or unpredictable workloads.

### Aurora Global Database

Replicates data across regions with < 1 second replication lag. Up to 5 secondary regions with 16 read replicas each.

- **RPO < 1 second** (data loss)
- **RTO < 1 minute** (recovery time)
- Promoting a secondary region takes < 1 minute

```bash
aws rds create-global-cluster \
  --global-cluster-identifier my-global-db \
  --source-db-cluster-identifier arn:aws:rds:us-east-1:123456789012:cluster:my-primary \
  --engine aurora-mysql
```

### Aurora Custom Endpoints

Route traffic to specific subsets of Aurora instances (e.g., larger instances for analytics queries).

```bash
aws rds create-db-cluster-endpoint \
  --db-cluster-identifier my-aurora \
  --db-cluster-endpoint-identifier analytics-endpoint \
  --endpoint-type READER \
  --static-members my-aurora-reader-large-1 my-aurora-reader-large-2
```

### Aurora Machine Learning

Run ML predictions directly from SQL queries using SageMaker or Comprehend. No ML experience needed — Aurora handles the integration.

```sql
-- Sentiment analysis using Amazon Comprehend
SELECT review_id, review_text,
  aws_comprehend_detect_sentiment(review_text, 'en') AS sentiment
FROM product_reviews
WHERE sentiment->>'sentiment' = 'NEGATIVE';

-- Fraud detection using SageMaker endpoint
SELECT transaction_id, amount,
  aws_sagemaker_invoke_endpoint('fraud-detection-endpoint',
    customer_id, amount, merchant_category, transaction_time
  ) AS fraud_score
FROM transactions
WHERE fraud_score > 0.8;
```

```bash
# Set up Aurora ML integration with SageMaker
# 1. Create an IAM role for Aurora to call SageMaker
aws iam create-role --role-name AuroraMLRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "rds.amazonaws.com"}, "Action": "sts:AssumeRole"}]
  }'

aws iam attach-role-policy --role-name AuroraMLRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerReadOnly

# 2. Associate the role with the Aurora cluster
aws rds add-role-to-db-cluster \
  --db-cluster-identifier my-aurora-cluster \
  --role-arn arn:aws:iam::123456789012:role/AuroraMLRole \
  --feature-name SageMaker
```

**Real-life use case:** An e-commerce platform runs fraud detection on every order. Instead of building a separate ML pipeline, they call a SageMaker endpoint directly from a SQL trigger in Aurora, blocking suspicious orders in real-time.

---

## 6.10 Amazon RDS Proxy

RDS Proxy pools and shares database connections. Reduces failover time by 66% and handles connection surges.

```
Lambda functions ──▶ RDS Proxy ──▶ RDS/Aurora
(100s of connections)  (connection pool)  (limited connections)
```

**Why use it:**
- Lambda functions open many short-lived connections — RDS Proxy pools them
- Reduces failover time from ~60s to ~30s
- Enforces IAM authentication to the database
- Never publicly accessible — must be accessed from within VPC

---

## 6.11 ElastiCache — Caching Patterns

### Lazy Loading (Cache-Aside)

```
App ──▶ Cache? ──Hit──▶ Return cached data
              └──Miss──▶ Query DB ──▶ Store in cache ──▶ Return data
```

- Only requested data is cached (no wasted space)
- Cache miss = 3 round trips (cache check + DB query + cache write)
- Data can become stale

### Write-Through

```
App ──▶ Write to DB ──▶ Write to Cache
```

- Data is never stale
- Every write = 2 operations (DB + cache)
- Missing data until it's written (combine with Lazy Loading)

### Redis vs Memcached

| Feature | Redis | Memcached |
|---------|-------|-----------|
| **Data structures** | Strings, lists, sets, sorted sets, hashes | Simple key-value |
| **Persistence** | Yes (snapshots, AOF) | No |
| **Replication** | Multi-AZ with failover | No |
| **Pub/Sub** | Yes | No |
| **Backup/Restore** | Yes | No |
| **Multi-threaded** | No (single-threaded) | Yes |
| **Best for** | Complex data, HA, persistence | Simple caching, multi-threaded |

---

## 6.12 Purpose-Built Databases

### DocumentDB (MongoDB compatible)

- Fully managed MongoDB-compatible document database
- Storage auto-scales up to 128 TiB
- Replicates 6 copies across 3 AZs

### Amazon Neptune (Graph database)

- Fully managed graph database
- Supports Property Graph and RDF/SPARQL
- Use cases: social networks, knowledge graphs, fraud detection, recommendation engines
- Up to 15 read replicas

### Amazon Keyspaces (Apache Cassandra compatible)

- Serverless, fully managed Cassandra-compatible database
- Tables auto-scale based on traffic
- Use cases: IoT device data, time-series data
- Compatible with CQL (Cassandra Query Language)

```bash
# Connect to Keyspaces using cqlsh (with TLS)
cqlsh cassandra.us-east-1.amazonaws.com 9142 \
  --ssl \
  -u "keyspaces-user" \
  -p "generated-password"

# Create a keyspace and table
# cqlsh> CREATE KEYSPACE my_app WITH replication = {'class': 'SingleRegionStrategy'};
# cqlsh> CREATE TABLE my_app.sensor_data (
#   device_id text,
#   timestamp timestamp,
#   temperature double,
#   humidity double,
#   PRIMARY KEY (device_id, timestamp)
# ) WITH CLUSTERING ORDER BY (timestamp DESC);

# Insert data
# cqlsh> INSERT INTO my_app.sensor_data (device_id, timestamp, temperature, humidity)
#   VALUES ('sensor-001', toTimestamp(now()), 23.5, 65.2);

# Query data
# cqlsh> SELECT * FROM my_app.sensor_data WHERE device_id = 'sensor-001' LIMIT 10;
#
#  device_id  | timestamp                       | temperature | humidity
# ------------+---------------------------------+-------------+----------
#  sensor-001 | 2024-01-15 10:30:00.000000+0000 |        23.5 |     65.2
```

**Real-life use case:** An IoT platform with 100K sensors writes millions of data points per second. Keyspaces handles the write throughput with on-demand capacity, and the CQL-compatible interface means existing Cassandra applications work without code changes.

### Amazon Timestream

- Serverless time-series database
- 1000x faster and 1/10th the cost of relational databases for time-series data
- Built-in analytics functions (smoothing, approximation, interpolation)
- Use cases: IoT sensor data, DevOps metrics, application telemetry

### Amazon QLDB (Quantum Ledger Database)

- Immutable, cryptographically verifiable transaction log
- Central authority model (unlike blockchain which is decentralized)
- Use cases: financial transactions, supply chain, registration systems

```bash
# Create a QLDB ledger
aws qldb create-ledger \
  --name vehicle-registration \
  --permissions-mode STANDARD \
  --deletion-protection

# Expected output:
# {
#   "Name": "vehicle-registration",
#   "Arn": "arn:aws:qldb:us-east-1:123456789012:ledger/vehicle-registration",
#   "State": "CREATING",
#   "DeletionProtection": true
# }

# Use PartiQL to interact with QLDB
# Example: Create a table and insert a record
aws qldb-session send-command \
  --ledger-name vehicle-registration \
  --start-session '{"LedgerName": "vehicle-registration"}'

# PartiQL statements:
# CREATE TABLE VehicleRegistration
# INSERT INTO VehicleRegistration VALUE {
#   'VIN': '1HGBH41JXMN109186',
#   'Owner': 'John Doe',
#   'State': 'CA',
#   'RegisteredDate': `2024-01-15`
# }

# Query the revision history (immutable audit trail)
# SELECT * FROM history(VehicleRegistration) WHERE metadata.id = 'doc-id-123'

# Export ledger data for verification
aws qldb export-journal-to-s3 \
  --name vehicle-registration \
  --inclusive-start-time 2024-01-01T00:00:00Z \
  --exclusive-end-time 2024-02-01T00:00:00Z \
  --s3-export-configuration '{
    "Bucket": "my-qldb-exports",
    "Prefix": "vehicle-reg/",
    "EncryptionConfiguration": {"ObjectEncryptionType": "SSE_S3"}
  }'
```

**Real-life use case:** A DMV uses QLDB to track vehicle registrations. Every title transfer, registration renewal, and ownership change is recorded immutably. Auditors can cryptographically verify that no records were tampered with.

---

## 6.13 Database Selection Guide

| Requirement | Service |
|------------|---------|
| Relational, SQL, joins | RDS, Aurora |
| Relational, auto-scaling, HA | Aurora Serverless v2 |
| Key-value, millisecond latency | DynamoDB |
| In-memory caching | ElastiCache (Redis/Memcached) |
| Document (MongoDB) | DocumentDB |
| Graph (relationships) | Neptune |
| Wide-column (Cassandra) | Keyspaces |
| Time-series (IoT, metrics) | Timestream |
| Ledger (immutable log) | QLDB |
| Data warehouse (analytics) | Redshift |
| Search | OpenSearch |

---

## 6.14 RDS — Additional Features

### RDS Storage Auto Scaling

Automatically increases storage when running low. Set a Maximum Storage Threshold. Triggers when: free storage < 10%, low-storage lasts 5+ minutes, 6+ hours since last modification. Useful for unpredictable workloads.

```bash
# Enable storage auto scaling on an existing RDS instance
aws rds modify-db-instance \
  --db-instance-identifier my-database \
  --max-allocated-storage 1000 \
  --apply-immediately

# Expected output:
# {
#   "DBInstance": {
#     "DBInstanceIdentifier": "my-database",
#     "AllocatedStorage": 100,
#     "MaxAllocatedStorage": 1000
#   }
# }

# Create a new instance with auto scaling enabled
aws rds create-db-instance \
  --db-instance-identifier my-new-db \
  --db-instance-class db.t3.medium \
  --engine mysql \
  --master-username admin \
  --master-user-password MyPassword123 \
  --allocated-storage 20 \
  --max-allocated-storage 100

# Check current storage usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name FreeStorageSpace \
  --dimensions Name=DBInstanceIdentifier,Value=my-database \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Average
```

### RDS Event Notifications

Subscribe to RDS events (instance state changes, backups, failovers) via SNS. Events are at the DB instance level, not data level. For data-level events, use native database features or DynamoDB Streams.

```bash
# Create an SNS topic for RDS events
aws sns create-topic --name rds-events
# arn:aws:sns:us-east-1:123456789012:rds-events

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:rds-events \
  --protocol email \
  --notification-endpoint dba@example.com

# Create an RDS event subscription
aws rds create-event-subscription \
  --subscription-name "prod-db-events" \
  --sns-topic-arn arn:aws:sns:us-east-1:123456789012:rds-events \
  --source-type db-instance \
  --source-ids my-database \
  --event-categories "availability" "failover" "failure" "maintenance"

# Expected output:
# {
#   "EventSubscription": {
#     "CustSubscriptionId": "prod-db-events",
#     "Status": "active",
#     "EventCategoriesList": ["availability", "failover", "failure", "maintenance"]
#   }
# }

# List available event categories
aws rds describe-event-categories --source-type db-instance
```

### RDS Custom

Managed RDS with OS and database customization access. Available for Oracle and SQL Server. You can SSH into the instance, install custom patches, configure OS settings. Deactivate automation mode before customizing.

```bash
# Create an RDS Custom instance (Oracle)
aws rds create-db-instance \
  --db-instance-identifier my-custom-oracle \
  --db-instance-class db.m5.xlarge \
  --engine custom-oracle-ee \
  --engine-version 19.custom_oracle_ee \
  --master-username admin \
  --master-user-password MyPassword123 \
  --custom-iam-instance-profile AWSRDSCustomInstanceProfile

# Pause RDS automation before making OS changes
aws rds modify-db-instance \
  --db-instance-identifier my-custom-oracle \
  --automation-mode all-paused \
  --resume-full-automation-mode-minutes 60

# SSH into the instance (via SSM Session Manager)
aws ssm start-session --target i-0abcdef1234567890

# After making changes, resume automation
aws rds modify-db-instance \
  --db-instance-identifier my-custom-oracle \
  --automation-mode full
```

**Real-life use case:** A company running Oracle with custom patches and OS-level tuning (kernel parameters, custom audit scripts) uses RDS Custom. They get the managed backup/patching benefits of RDS while retaining the OS access they need.

### Aurora Database Cloning

Create a new Aurora cluster from an existing one using copy-on-write protocol. Faster and more cost-effective than snapshot + restore. Useful for creating staging environments from production.

```bash
# Clone an Aurora cluster (takes seconds, regardless of data size)
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier prod-aurora-cluster \
  --db-cluster-identifier staging-aurora-cluster \
  --restore-type copy-on-write \
  --use-latest-restorable-time

# Expected output:
# {
#   "DBCluster": {
#     "DBClusterIdentifier": "staging-aurora-cluster",
#     "Status": "creating",
#     "CloneGroupId": "clone-group-abcdef"
#   }
# }

# Add an instance to the cloned cluster
aws rds create-db-instance \
  --db-instance-identifier staging-instance-1 \
  --db-cluster-identifier staging-aurora-cluster \
  --db-instance-class db.r5.large \
  --engine aurora-mysql
```

**How copy-on-write works:** The clone initially shares the same data pages as the source. Only when data is modified in either the source or clone are new pages allocated. A 1 TB database clone starts in seconds and initially uses almost no additional storage.

### Aurora Backups & Backtrack

- Automated: 1–35 day retention, point-in-time restore, cannot be disabled
- Manual snapshots: retained until you delete them
- Backtrack: rewind the cluster to a point in time without restoring (Aurora MySQL only)

```bash
# Enable backtrack on an Aurora MySQL cluster (must be set at creation)
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora-cluster \
  --engine aurora-mysql \
  --master-username admin \
  --master-user-password MyPassword123 \
  --backtrack-window 86400

# Backtrack to a specific time (e.g., before a bad DELETE statement)
aws rds backtrack-db-cluster \
  --db-cluster-identifier my-aurora-cluster \
  --backtrack-to "2024-01-15T14:30:00Z"

# Expected output:
# {
#   "DBClusterIdentifier": "my-aurora-cluster",
#   "BacktrackTo": "2024-01-15T14:30:00Z",
#   "Status": "backtracking"
# }

# Check backtrack status
aws rds describe-db-cluster-backtracks \
  --db-cluster-identifier my-aurora-cluster

# Point-in-time restore (creates a NEW cluster)
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier my-aurora-cluster \
  --db-cluster-identifier restored-cluster \
  --restore-to-time "2024-01-15T14:30:00Z"
```

**Backtrack vs Point-in-Time Restore:** Backtrack rewinds the existing cluster in-place (seconds). PITR creates a new cluster (minutes to hours). Backtrack is faster but only available for Aurora MySQL with a max window of 72 hours.

### Babelfish for Aurora PostgreSQL

Run SQL Server applications on Aurora PostgreSQL with minimal code changes. Understands T-SQL and SQL Server wire protocol (TDS).

```bash
# Create an Aurora PostgreSQL cluster with Babelfish enabled
aws rds create-db-cluster \
  --db-cluster-identifier my-babelfish-cluster \
  --engine aurora-postgresql \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password MyPassword123 \
  --enable-babelfish

# Connect using SQL Server tools (port 1433)
sqlcmd -S my-babelfish-cluster.cluster-abcdef.us-east-1.rds.amazonaws.com,1433 \
  -U admin -P MyPassword123

# Run T-SQL queries as-is
# 1> SELECT @@VERSION
# 2> GO
# Babelfish for Aurora PostgreSQL with SQL Server Compatibility

# 1> CREATE DATABASE myapp
# 2> GO
# 1> USE myapp
# 2> CREATE TABLE orders (id INT IDENTITY PRIMARY KEY, customer_name NVARCHAR(100))
# 3> GO
```

**Real-life use case:** A company migrating from SQL Server to reduce licensing costs. Babelfish lets their .NET applications connect to Aurora PostgreSQL using the same T-SQL queries and TDS protocol, avoiding a full application rewrite.

### RDS Read Replicas — Network Cost

- Same Region, different AZ: **free** (no data transfer charge)
- Cross-Region: data transfer charges apply

---

## 6.15 Key Takeaways

1. Use RDS for relational data with complex queries; DynamoDB for high-scale key-value access
2. Always put RDS in private subnets with no public access
3. Enable Multi-AZ for production RDS instances
4. Use read replicas to offload read traffic
5. DynamoDB: Design tables around access patterns, not data relationships
6. Use DynamoDB on-demand billing for unpredictable workloads
7. Enable encryption at rest for all databases
8. Automate backups and test restore procedures regularly
9. Aurora Serverless v2 for unpredictable workloads — scales to zero
10. Aurora Global for cross-region DR with < 1s replication lag
11. RDS Proxy for Lambda → RDS connections (connection pooling, faster failover)
12. ElastiCache: Use Lazy Loading + Write-Through together for best results
13. Redis for complex data structures and HA; Memcached for simple multi-threaded caching
14. Choose purpose-built databases: Neptune for graphs, Timestream for time-series, DocumentDB for documents
