# Module 06: Azure Databases

## Certification Relevance: AZ-204, AZ-104

---

## 6.1 Azure Database Services Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  AZURE DATABASE SERVICES                    │
├──────────────────┬──────────────────────────────────────────┤
│ Relational (SQL) │ Non-Relational (NoSQL)                   │
│                  │                                          │
│ • Azure SQL DB   │ • Cosmos DB (multi-model)                │
│ • SQL Managed    │ • Table Storage (key-value)              │
│   Instance       │ • Redis Cache (in-memory)                │
│ • MySQL          │                                          │
│ • PostgreSQL     │                                          │
│ • MariaDB        │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

---

## 6.2 Azure SQL Database

### What is Azure SQL Database?
A fully managed relational database engine based on Microsoft SQL Server. PaaS — Microsoft handles patching, backups, and high availability.

### Purchasing Models

| Model | Description | Best For |
|-------|-------------|----------|
| **DTU** (Database Transaction Unit) | Bundled compute + storage | Simple, predictable workloads |
| **vCore** | Choose CPU, memory, storage independently | Granular control, hybrid benefit |
| **Serverless** | Auto-scales, auto-pauses | Intermittent, unpredictable usage |

### DTU Tiers

| Tier | DTUs | Storage | Cost/month* |
|------|------|---------|-------------|
| Basic | 5 | 2 GB | ~$5 |
| Standard S0 | 10 | 250 GB | ~$15 |
| Standard S1 | 20 | 250 GB | ~$30 |
| Standard S3 | 100 | 250 GB | ~$150 |
| Premium P1 | 125 | 500 GB | ~$465 |

### Portal UI Walkthrough: Create an Azure SQL Database

```
PORTAL STEPS — Create a SQL Server + Database:

Step 1: Navigate to SQL Databases
   → Search "SQL databases" in the search bar
   → Click "SQL databases" from results
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   └────────────────────────────────────────────────────────┘
   ┌─ Database Details ─────────────────────────────────────┐
   │ Database name:      db-ecommerce                        │
   │ Server:             Click "Create new"                  │
   │   ┌─ Create SQL Database Server ──────────────────────┐│
   │   │ Server name:    sql-server-demo-2024               ││
   │   │   (globally unique — becomes                       ││
   │   │    sql-server-demo-2024.database.windows.net)      ││
   │   │ Location:       East US                            ││
   │   │ Authentication: Use SQL authentication             ││
   │   │ Server admin:   sqladmin                           ││
   │   │ Password:       P@ssw0rd1234!                      ││
   │   │ Confirm:        P@ssw0rd1234!                      ││
   │   │ Click "OK"                                         ││
   │   └───────────────────────────────────────────────────┘│
   │ Want to use SQL elastic pool: No                        │
   │ Workload environment: Development (cheaper)             │
   │                       Production (better performance)   │
   └────────────────────────────────────────────────────────┘
   ┌─ Compute + Storage ────────────────────────────────────┐
   │ Click "Configure database"                              │
   │ Service tier: DTU-based → Basic ($5/month)              │
   │   OR                                                    │
   │ Service tier: General Purpose (Serverless)              │
   │   → Auto-pause delay: 60 minutes                       │
   │   → Min vCores: 0.5                                    │
   │   → Max vCores: 2                                      │
   │   → ⚠️ Serverless auto-pauses = $0 when idle!          │
   │ Click "Apply"                                           │
   └────────────────────────────────────────────────────────┘
   ┌─ Backup Storage Redundancy ────────────────────────────┐
   │ ● Locally-redundant backup storage (cheapest)           │
   │ ○ Zone-redundant backup storage                         │
   │ ○ Geo-redundant backup storage (most resilient)         │
   └────────────────────────────────────────────────────────┘

Step 3: Networking Tab
   → Click "Next: Networking >"
   ┌─ Network Connectivity ─────────────────────────────────┐
   │ Connectivity method:                                     │
   │   ● Public endpoint                                     │
   │   ○ Private endpoint                                    │
   │   ○ No access                                           │
   └────────────────────────────────────────────────────────┘
   ┌─ Firewall Rules ───────────────────────────────────────┐
   │ Allow Azure services and resources                      │
   │ to access this server:        ● Yes                     │
   │ Add current client IP address: ● Yes                    │
   │   (adds your current IP so you can connect immediately) │
   └────────────────────────────────────────────────────────┘

Step 4: Security Tab
   → Click "Next: Security >"
   → Enable Microsoft Defender for SQL: Free trial
   → (Leave defaults for demo)

Step 5: Additional Settings Tab
   → Click "Next: Additional settings >"
   ┌─ Data Source ──────────────────────────────────────────┐
   │ Use existing data:                                      │
   │   ● None (empty database)                               │
   │   ○ Sample (AdventureWorksLT — great for learning!)    │
   │   ○ Backup (restore from backup)                       │
   │ → Select "Sample" to get pre-loaded demo data          │
   └────────────────────────────────────────────────────────┘

Step 6: Tags → Review + Create
   → Add tags: Environment=Demo
   → Click "Review + create" → "Create"
   → Deployment takes 2-5 minutes

Step 7: Connect to Your Database
   → Click "Go to resource"
   → Click "Query editor (preview)" in the left sidebar
   → Login: sqladmin / P@ssw0rd1234!
   → Run a query:
     SELECT TOP 10 * FROM SalesLT.Customer;
   → You'll see customer data from the sample database!

Step 8: Connect from External Tools
   → Go to SQL database → "Overview"
   → Copy the "Server name":
     sql-server-demo-2024.database.windows.net
   → Use in Azure Data Studio, SSMS, or your application:
     Server:   sql-server-demo-2024.database.windows.net
     Database: db-ecommerce
     User:     sqladmin
     Password: P@ssw0rd1234!
```

### Portal UI Walkthrough: Create a Cosmos DB Account

```
PORTAL STEPS — Create a Cosmos DB Account:

Step 1: Navigate to Cosmos DB
   → Search "Azure Cosmos DB" in the search bar
   → Click "Azure Cosmos DB" from results
   → Click "+ Create"

Step 2: Select API
   → Choose your API:
     ┌─────────────────────────────────────────────────────┐
     │ Azure Cosmos DB for NoSQL    ← Recommended (default)│
     │ Azure Cosmos DB for MongoDB                          │
     │ Azure Cosmos DB for PostgreSQL                       │
     │ Azure Cosmos DB for Apache Cassandra                 │
     │ Azure Cosmos DB for Table                            │
     │ Azure Cosmos DB for Apache Gremlin                   │
     └─────────────────────────────────────────────────────┘
   → Click "Create" under "Azure Cosmos DB for NoSQL"

Step 3: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Account name:       cosmos-demo-2024                    │
   │                     (globally unique)                   │
   │ Location:           East US                             │
   │ Capacity mode:      ● Serverless (pay per operation)    │
   │                     ○ Provisioned throughput             │
   │   → Serverless is cheaper for dev/test                  │
   │   → Provisioned for production with predictable load    │
   └────────────────────────────────────────────────────────┘

Step 4: Global Distribution Tab
   → Click "Next: Global Distribution >"
   → Geo-Redundancy: Disable (for demo)
   → Multi-region Writes: Disable (for demo)
   → (Enable for production — adds regions for low latency)

Step 5: Review + Create
   → Click "Review + create" → "Create"
   → Deployment takes 3-5 minutes

Step 6: Create a Database and Container
   → Go to resource → Left sidebar → "Data Explorer"
   → Click "New Container"
   ┌─────────────────────────────────────────────────────────┐
   │ Database id:        ● Create new                        │
   │ Database name:      ecommerce-db                        │
   │ Container id:       products                            │
   │ Partition key:      /category                           │
   │   (choose a property with high cardinality)             │
   │ Click "OK"                                              │
   └─────────────────────────────────────────────────────────┘

Step 7: Add Data
   → In Data Explorer, expand: ecommerce-db → products → Items
   → Click "New Item"
   → Paste JSON:
     {
       "id": "1",
       "name": "Laptop",
       "category": "Electronics",
       "price": 999.99,
       "inStock": true
     }
   → Click "Save"
   → Add more items to practice

Step 8: Query Data
   → Click "New SQL Query"
   → Type: SELECT * FROM c WHERE c.category = "Electronics"
   → Click "Execute Query"
   → Results appear below with RU charge shown
```

### Creating Azure SQL Database with CLI

```bash
# Step 1: Create a SQL Server (logical server)
az sql server create \
  --resource-group rg-demo-eastus \
  --name sql-server-demo-2024 \
  --location eastus \
  --admin-user sqladmin \
  --admin-password 'P@ssw0rd1234!'

# Meaning:
# This creates a LOGICAL server (not a VM). It's an endpoint for databases.
# --name: Globally unique (becomes sql-server-demo-2024.database.windows.net)

# Output:
# {
#   "fullyQualifiedDomainName": "sql-server-demo-2024.database.windows.net",
#   "name": "sql-server-demo-2024",
#   "state": "Ready"
# }

# Step 2: Configure firewall (allow your IP)
az sql server firewall-rule create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name AllowMyIP \
  --start-ip-address 203.0.113.50 \
  --end-ip-address 203.0.113.50

# Allow Azure services to connect
az sql server firewall-rule create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Step 3: Create a database
az sql db create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce \
  --edition Standard \
  --capacity 10 \
  --max-size 250GB

# Meaning:
# --edition Standard : Standard tier
# --capacity 10      : 10 DTUs
# --max-size 250GB   : Maximum database size

# Create a serverless database (auto-pause, auto-scale)
az sql db create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-dev \
  --edition GeneralPurpose \
  --compute-model Serverless \
  --auto-pause-delay 60 \
  --min-capacity 0.5 \
  --max-capacity 2

# Meaning:
# --auto-pause-delay 60 : Pause after 60 minutes of inactivity ($0 compute cost)
# --min-capacity 0.5    : Minimum 0.5 vCores
# --max-capacity 2      : Maximum 2 vCores (scales automatically)

# List databases
az sql db list \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --output table

# Show database details
az sql db show \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce

# Scale up a database
az sql db update \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce \
  --edition Standard \
  --capacity 50
# Meaning: Scale from S0 (10 DTU) to S2 (50 DTU) — no downtime

# Delete a database
az sql db delete \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce \
  --yes
```

### Connecting to Azure SQL

```bash
# Using sqlcmd (command-line)
sqlcmd -S sql-server-demo-2024.database.windows.net \
  -d db-ecommerce \
  -U sqladmin \
  -P 'P@ssw0rd1234!'

# Connection string for applications:
# Server=tcp:sql-server-demo-2024.database.windows.net,1433;
# Initial Catalog=db-ecommerce;
# Persist Security Info=False;
# User ID=sqladmin;
# Password=P@ssw0rd1234!;
# MultipleActiveResultSets=False;
# Encrypt=True;
# TrustServerCertificate=False;
```

### Backups and Restore

```bash
# Azure SQL automatically backs up:
# - Full backup: Weekly
# - Differential: Every 12-24 hours
# - Transaction log: Every 5-10 minutes

# Retention periods:
# Basic: 7 days
# Standard: 35 days
# Premium: 35 days

# Point-in-time restore
az sql db restore \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce-restored \
  --dest-name db-ecommerce-restored \
  --time "2024-01-15T10:00:00Z"
# Meaning: Restore database to its state at Jan 15, 2024 10:00 AM UTC

# Long-term retention (keep backups for years)
az sql db ltr-policy set \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce \
  --weekly-retention P4W \
  --monthly-retention P12M \
  --yearly-retention P5Y \
  --week-of-year 1
# P4W = Keep weekly backups for 4 weeks
# P12M = Keep monthly backups for 12 months
# P5Y = Keep yearly backups for 5 years
```

---

## 6.3 Azure SQL Managed Instance

```
When to use SQL Managed Instance vs SQL Database:

SQL Database:
- New cloud-native applications
- Single database workloads
- Serverless option available
- Cheapest option

SQL Managed Instance:
- Migrating existing SQL Server applications
- Need SQL Server Agent, CLR, cross-database queries
- Near 100% compatibility with on-premises SQL Server
- VNet integration required
- More expensive but more compatible
```

---

## 6.4 Azure Cosmos DB

### What is Cosmos DB?
A globally distributed, multi-model NoSQL database. Designed for low-latency (single-digit millisecond) reads and writes at any scale.

### APIs Available

| API | Data Model | Use Case |
|-----|-----------|----------|
| NoSQL (Core) | JSON documents | Default, most features |
| MongoDB | BSON documents | MongoDB migration |
| Cassandra | Wide-column | Cassandra migration |
| Gremlin | Graph | Social networks, recommendations |
| Table | Key-value | Azure Table Storage migration |
| PostgreSQL | Relational | Distributed PostgreSQL |

### Real-World Example
```
Industry Example: A global gaming company uses Cosmos DB for player profiles.
- 50 million players worldwide
- Data replicated to 5 regions (US, Europe, Asia, Australia, Brazil)
- Players always connect to nearest region (<10ms latency)
- 99.999% availability SLA (26 seconds downtime/month)
- Auto-scales from 1,000 to 1,000,000 RU/s during tournaments
```

### Request Units (RU/s)
```
RU = Request Unit. A normalized measure of database throughput.

1 RU = Cost of reading a single 1 KB document by its ID

Examples:
- Read 1 KB document by ID:     1 RU
- Write 1 KB document:          5 RUs
- Query returning 5 documents:  ~10 RUs
- Complex query with filters:   ~50 RUs

Provisioned throughput: You set RU/s (e.g., 400 RU/s = ~$24/month)
Serverless: Pay per RU consumed (good for dev/test)
Autoscale: Set max RU/s, scales between 10% and max
```

### Creating Cosmos DB

```bash
# Create a Cosmos DB account (NoSQL API)
az cosmosdb create \
  --resource-group rg-demo-eastus \
  --name cosmos-demo-2024 \
  --kind GlobalDocumentDB \
  --locations regionName=eastus failoverPriority=0 \
  --locations regionName=westus failoverPriority=1 \
  --default-consistency-level Session

# Meaning:
# --kind GlobalDocumentDB : NoSQL (Core) API
# --locations             : Multi-region with automatic failover
# --default-consistency-level Session : Balance between consistency and performance

# Output:
# {
#   "documentEndpoint": "https://cosmos-demo-2024.documents.azure.com:443/",
#   "name": "cosmos-demo-2024",
#   "readLocations": [
#     { "locationName": "East US", "failoverPriority": 0 },
#     { "locationName": "West US", "failoverPriority": 1 }
#   ]
# }

# Create a database
az cosmosdb sql database create \
  --resource-group rg-demo-eastus \
  --account-name cosmos-demo-2024 \
  --name ecommerce-db

# Create a container (collection)
az cosmosdb sql container create \
  --resource-group rg-demo-eastus \
  --account-name cosmos-demo-2024 \
  --database-name ecommerce-db \
  --name products \
  --partition-key-path "/category" \
  --throughput 400

# Meaning:
# --partition-key-path "/category" : How data is distributed
#   All products with same category are stored together
#   Good partition key = high cardinality, even distribution
# --throughput 400 : 400 RU/s provisioned

# Get connection keys
az cosmosdb keys list \
  --resource-group rg-demo-eastus \
  --name cosmos-demo-2024

# Get connection string
az cosmosdb keys list \
  --resource-group rg-demo-eastus \
  --name cosmos-demo-2024 \
  --type connection-strings
```

### Consistency Levels

```
Strong ──────────────────────────────────── Eventual
(Most consistent)                    (Most performant)

1. Strong:    Read always returns most recent write
              Use: Financial transactions
              Cost: Highest RU consumption

2. Bounded Staleness: Reads lag behind writes by at most K versions or T time
              Use: Stock tickers, leaderboards

3. Session:   Within a session, reads are consistent with writes (DEFAULT)
              Use: User profiles, shopping carts
              Cost: Moderate

4. Consistent Prefix: Reads never see out-of-order writes
              Use: Social media feeds

5. Eventual:  No ordering guarantee, fastest reads
              Use: Like counts, view counts
              Cost: Lowest RU consumption
```

### Exam Tip
```
AZ-204 question: "Which Cosmos DB consistency level is the default?"
Answer: Session

"Which consistency level provides the lowest latency?"
Answer: Eventual

"What is a partition key?"
Answer: A property that determines how data is distributed across
physical partitions. Choose a key with high cardinality and even
distribution (e.g., userId, category, tenantId).
```

---

## 6.5 Azure Database for MySQL / PostgreSQL

```bash
# Create Azure Database for PostgreSQL (Flexible Server)
az postgres flexible-server create \
  --resource-group rg-demo-eastus \
  --name pg-demo-2024 \
  --location eastus \
  --admin-user pgadmin \
  --admin-password 'P@ssw0rd1234!' \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 16

# Meaning:
# --sku-name Standard_B1ms : 1 vCore, 2 GB RAM (burstable)
# --tier Burstable         : Cost-effective for dev/test
# --storage-size 32        : 32 GB storage
# --version 16             : PostgreSQL 16

# Connect
psql "host=pg-demo-2024.postgres.database.azure.com \
  port=5432 dbname=postgres user=pgadmin password=P@ssw0rd1234! sslmode=require"

# Create Azure Database for MySQL (Flexible Server)
az mysql flexible-server create \
  --resource-group rg-demo-eastus \
  --name mysql-demo-2024 \
  --location eastus \
  --admin-user mysqladmin \
  --admin-password 'P@ssw0rd1234!' \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 8.0.21

# Connect
mysql -h mysql-demo-2024.mysql.database.azure.com \
  -u mysqladmin -p --ssl-mode=REQUIRED
```

---

## 6.6 Azure Cache for Redis

```bash
# Create Redis Cache
az redis create \
  --resource-group rg-demo-eastus \
  --name redis-demo-2024 \
  --location eastus \
  --sku Basic \
  --vm-size c0

# Meaning:
# --sku Basic : Single node, no SLA (dev/test)
# --vm-size c0 : 250 MB cache, shared infrastructure

# Tiers:
# Basic:    Single node, no SLA, 250 MB - 53 GB     (~$16/month for C0)
# Standard: Replicated (2 nodes), 99.9% SLA          (~$40/month for C1)
# Premium:  Clustering, persistence, VNet, geo-rep    (~$225/month for P1)

# Get connection info
az redis list-keys \
  --resource-group rg-demo-eastus \
  --name redis-demo-2024

# Output:
# {
#   "primaryKey": "abc123...",
#   "secondaryKey": "def456..."
# }
# Connection: redis-demo-2024.redis.cache.windows.net:6380,password=abc123...,ssl=True
```

```
Real-World Example: An e-commerce site uses Redis to cache:
- Product catalog (avoid hitting database for every page view)
- User sessions (fast login state management)
- Shopping cart (sub-millisecond reads)

Result: Page load time drops from 500ms to 50ms
Database load reduced by 80%
```

---

## 6.7 Choosing the Right Database

```
Decision Tree:

Need relational (SQL)?
├── Yes → Migrating from SQL Server?
│         ├── Yes → Need full compatibility? → SQL Managed Instance
│         └── No  → New app? → Azure SQL Database
│
├── Need MySQL? → Azure Database for MySQL
├── Need PostgreSQL? → Azure Database for PostgreSQL
│
└── No (NoSQL) → What type of data?
    ├── Documents (JSON) → Cosmos DB (NoSQL API)
    ├── Key-Value → Cosmos DB (Table API) or Table Storage
    ├── Graph → Cosmos DB (Gremlin API)
    ├── Wide-column → Cosmos DB (Cassandra API)
    └── Caching → Azure Cache for Redis
```

---

## 6.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot connect to server` | Firewall not configured | Add client IP to server firewall rules |
| `Login failed for user` | Wrong credentials | Verify username format: `user@servername` for SQL |
| `DTU limit reached` | Database overloaded | Scale up DTUs or optimize queries |
| `Request rate too large (429)` | Cosmos DB RU/s exceeded | Increase throughput or optimize queries |
| `Partition key not found` | Missing partition key in document | Include partition key property in every document |
| `SSL connection required` | SSL not enabled in connection | Add `sslmode=require` to connection string |
| `Server name already exists` | Name not globally unique | Choose a different server name |
| `Firewall rule conflict` | Overlapping IP ranges | Remove conflicting rules |

### Cosmos DB Troubleshooting

```bash
# Check current RU consumption
az cosmosdb sql container throughput show \
  --resource-group rg-demo-eastus \
  --account-name cosmos-demo-2024 \
  --database-name ecommerce-db \
  --name products

# Enable autoscale (prevent 429 errors)
az cosmosdb sql container throughput migrate \
  --resource-group rg-demo-eastus \
  --account-name cosmos-demo-2024 \
  --database-name ecommerce-db \
  --name products \
  --throughput-type autoscale

# Check partition key statistics (in Portal)
# Cosmos DB → Data Explorer → Container → Settings → Partition Key Statistics
```

---

## 6.9 Practice Questions

### Question 1
**Which Azure SQL purchasing model allows the database to auto-pause when inactive?**
- A) DTU
- B) vCore
- C) Serverless ✅
- D) Elastic Pool

### Question 2
**What is the default consistency level in Cosmos DB?**
- A) Strong
- B) Bounded Staleness
- C) Session ✅
- D) Eventual

### Question 3
**Which Cosmos DB API should you use for a social network with complex relationships?**
- A) NoSQL
- B) MongoDB
- C) Gremlin (Graph) ✅
- D) Table

### Question 4
**Azure SQL Database automatic backups include:**
- A) Full backups only
- B) Full, differential, and transaction log backups ✅
- C) Only transaction log backups
- D) No automatic backups

### Question 5
**What is a Request Unit (RU) in Cosmos DB?**
- A) A billing unit for storage
- B) A normalized measure of database throughput ✅
- C) A unit of network bandwidth
- D) A measure of CPU usage

---

[← Previous Module](./Module-05-Storage.md) | [Next Module: Identity & Security →](./Module-07-Identity-and-Security.md)
