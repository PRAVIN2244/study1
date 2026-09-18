# Module 17: Real-World Industry Projects

## Apply Everything You've Learned

---

## Project 1: E-Commerce Platform (Beginner-Intermediate)

### Architecture

```
                         Internet
                            │
                     ┌──────┴──────┐
                     │ Azure Front  │
                     │ Door + WAF   │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              ▼                           ▼
     ┌────────────────┐          ┌────────────────┐
     │  East US       │          │  West Europe   │
     │  App Service   │          │  App Service   │
     │  (Node.js API) │          │  (Node.js API) │
     └───────┬────────┘          └───────┬────────┘
             │                           │
     ┌───────┴────────┐          ┌───────┴────────┐
     │  Azure SQL     │◄────────►│  Azure SQL     │
     │  (Primary)     │  Geo-Rep  │  (Secondary)   │
     └───────┬────────┘          └────────────────┘
             │
     ┌───────┴────────┐
     │  Redis Cache   │
     │  (Sessions +   │
     │   Product Cache)│
     └────────────────┘
             │
     ┌───────┴────────┐
     │  Blob Storage  │
     │  (Product      │
     │   Images)      │
     └────────────────┘
```

### Portal UI Walkthrough: Build the E-Commerce Platform Step-by-Step

```
PORTAL STEPS — Build the Entire E-Commerce Platform via Azure Portal:

This walkthrough creates every resource from the architecture above
using only the Azure Portal UI. Follow each step in order.

═══════════════════════════════════════════════════════════════
STEP 1: Create the Resource Group
═══════════════════════════════════════════════════════════════
   → Search "Resource groups" → Click "+ Create"
   → Subscription: Your subscription
   → Resource group: rg-ecom-prod
   → Region: East US
   → Tags: Environment=Production, Project=E-Commerce
   → Click "Review + create" → "Create"

═══════════════════════════════════════════════════════════════
STEP 2: Create the SQL Database
═══════════════════════════════════════════════════════════════
   → Search "SQL databases" → Click "+ Create"
   → Resource group: rg-ecom-prod
   → Database name: db-ecommerce
   → Server: Click "Create new"
     → Server name: sql-ecom-prod
     → Location: East US
     → Admin login: sqladmin
     → Password: Str0ngP@ss2024!
     → Click "OK"
   → Compute + storage: Click "Configure database"
     → Service tier: Standard (S1, 20 DTUs)
     → Click "Apply"
   → Networking tab:
     → Allow Azure services: Yes
     → Add current client IP: Yes
   → Additional settings:
     → Data source: Sample (AdventureWorksLT)
   → Click "Review + create" → "Create"
   → ⏱️ Wait 2-3 minutes

═══════════════════════════════════════════════════════════════
STEP 3: Create the Redis Cache
═══════════════════════════════════════════════════════════════
   → Search "Azure Cache for Redis" → Click "+ Create"
   → Resource group: rg-ecom-prod
   → DNS name: redis-ecom-prod
   → Location: East US
   → Cache SKU: Standard C1 (1 GB, replicated)
   → Click "Review + create" → "Create"
   → ⏱️ Wait 10-15 minutes (Redis takes longer to provision)

═══════════════════════════════════════════════════════════════
STEP 4: Create the Storage Account for Product Images
═══════════════════════════════════════════════════════════════
   → Search "Storage accounts" → Click "+ Create"
   → Resource group: rg-ecom-prod
   → Name: stecomprod2024
   → Region: East US
   → Performance: Standard
   → Redundancy: GRS (Geo-redundant)
   → Click "Review + create" → "Create"

   After creation:
   → Go to storage account → "Containers" → "+ Container"
   → Name: product-images
   → Access level: Blob (anonymous read for blobs)
   → Click "Create"

═══════════════════════════════════════════════════════════════
STEP 5: Create the App Service (Web API)
═══════════════════════════════════════════════════════════════
   → Search "App Services" → Click "+ Create" → "Web App"
   → Resource group: rg-ecom-prod
   → Name: ecom-api-prod
   → Publish: Code
   → Runtime stack: Node 18 LTS
   → Operating System: Linux
   → Region: East US
   → App Service Plan: Click "Create new"
     → Name: plan-ecom-prod
     → Pricing plan: Standard S1
   → Monitoring tab:
     → Enable Application Insights: Yes
     → Name: ai-ecom-prod
   → Click "Review + create" → "Create"

═══════════════════════════════════════════════════════════════
STEP 6: Configure App Settings (Connection Strings)
═══════════════════════════════════════════════════════════════
   → Go to App Service → Left sidebar → "Configuration"
   → Click "+ New application setting" for each:

   Setting 1:
     Name:  NODE_ENV          Value: production
   Setting 2:
     Name:  DB_HOST           Value: sql-ecom-prod.database.windows.net
   Setting 3:
     Name:  DB_NAME           Value: db-ecommerce
   Setting 4:
     Name:  REDIS_HOST        Value: redis-ecom-prod.redis.cache.windows.net
   Setting 5:
     Name:  STORAGE_ACCOUNT   Value: stecomprod2024

   → Click "Save" at the top → "Continue"

═══════════════════════════════════════════════════════════════
STEP 7: Create a Staging Deployment Slot
═══════════════════════════════════════════════════════════════
   → App Service → Left sidebar → "Deployment slots"
   → Click "+ Add Slot"
   → Name: staging
   → Clone settings from: ecom-api-prod
   → Click "Add"
   → Staging URL: https://ecom-api-prod-staging.azurewebsites.net

═══════════════════════════════════════════════════════════════
STEP 8: Set Up Monitoring and Alerts
═══════════════════════════════════════════════════════════════
   → Search "Monitor" → "Alerts" → "+ Create" → "Alert rule"
   → Scope: Select ecom-api-prod (App Service)
   → Condition: "Http Server Errors" > 10 in 5 minutes
   → Action group: Create new
     → Name: ag-ecom-ops
     → Email: ops-team@company.com
   → Alert name: alert-server-errors
   → Click "Create"

═══════════════════════════════════════════════════════════════
STEP 9: Enable Backup
═══════════════════════════════════════════════════════════════
   → App Service → Left sidebar → "Backups"
   → Click "Configure"
   → Storage account: stecomprod2024
   → Container: Click "Create new" → Name: backups
   → Scheduled backup: On
   → Frequency: Every 1 day
   → Retention: 30 days
   → Include database: Yes
     → Connection string: From SQL Database overview page
     → Database type: SQL Azure
   → Click "Save"

═══════════════════════════════════════════════════════════════
STEP 10: Verify Everything Works
═══════════════════════════════════════════════════════════════
   → Open https://ecom-api-prod.azurewebsites.net
   → Check SQL Database: Query editor → Run a test query
   → Check Storage: Upload a test image to product-images
   → Check Redis: Overview → Connected clients should show 0
   → Check Monitoring: Application Insights → Live Metrics
   → Check Alerts: Monitor → Alerts → Verify rule is active

   ✅ Your e-commerce platform infrastructure is ready!
   → Next: Deploy your application code via Deployment Center
```

### CLI Implementation (Same Steps via Command Line)

```bash
# === STEP 1: Create Resource Groups ===
az group create --name rg-ecom-prod --location eastus \
  --tags Environment=Production Project=E-Commerce

# === STEP 2: Create Azure SQL Database ===
az sql server create \
  --resource-group rg-ecom-prod \
  --name sql-ecom-prod \
  --location eastus \
  --admin-user sqladmin \
  --admin-password 'Str0ngP@ss2024!'

az sql db create \
  --resource-group rg-ecom-prod \
  --server sql-ecom-prod \
  --name db-ecommerce \
  --edition Standard \
  --capacity 20

# === STEP 3: Create Redis Cache ===
az redis create \
  --resource-group rg-ecom-prod \
  --name redis-ecom-prod \
  --location eastus \
  --sku Standard \
  --vm-size c1

# === STEP 4: Create Storage Account for Images ===
az storage account create \
  --name stecomprod2024 \
  --resource-group rg-ecom-prod \
  --location eastus \
  --sku Standard_GRS \
  --kind StorageV2

az storage container create \
  --name product-images \
  --account-name stecomprod2024 \
  --public-access blob

# === STEP 5: Create App Service ===
az appservice plan create \
  --resource-group rg-ecom-prod \
  --name plan-ecom-prod \
  --sku S1 \
  --is-linux

az webapp create \
  --resource-group rg-ecom-prod \
  --plan plan-ecom-prod \
  --name ecom-api-prod \
  --runtime "NODE:18-lts"

# === STEP 6: Configure App Settings ===
az webapp config appsettings set \
  --resource-group rg-ecom-prod \
  --name ecom-api-prod \
  --settings \
    NODE_ENV=production \
    DB_HOST=sql-ecom-prod.database.windows.net \
    DB_NAME=db-ecommerce \
    REDIS_HOST=redis-ecom-prod.redis.cache.windows.net \
    STORAGE_ACCOUNT=stecomprod2024

# === STEP 7: Create Staging Slot ===
az webapp deployment slot create \
  --resource-group rg-ecom-prod \
  --name ecom-api-prod \
  --slot staging

# === STEP 8: Set Up Monitoring ===
az monitor app-insights component create \
  --app ai-ecom-prod \
  --location eastus \
  --resource-group rg-ecom-prod \
  --kind web \
  --application-type web

# === STEP 9: Create Alerts ===
az monitor metrics alert create \
  --resource-group rg-ecom-prod \
  --name "alert-high-response-time" \
  --scopes "/subscriptions/SUB_ID/resourceGroups/rg-ecom-prod/providers/Microsoft.Web/sites/ecom-api-prod" \
  --condition "avg HttpResponseTime > 3" \
  --window-size 5m \
  --severity 2

# === STEP 10: Enable Backup ===
az webapp config backup create \
  --resource-group rg-ecom-prod \
  --webapp-name ecom-api-prod \
  --backup-name "daily-backup" \
  --container-url "https://stecomprod2024.blob.core.windows.net/backups?SAS_TOKEN" \
  --db-connection-string "Server=sql-ecom-prod.database.windows.net;..." \
  --db-name db-ecommerce \
  --db-type SqlAzure \
  --frequency 24h \
  --retain-one true \
  --retention 30
```

### Cost Estimate
```
App Service (S1):        $70/month
Azure SQL (S1, 20 DTU):  $30/month
Redis Cache (C1):        $40/month
Storage (50 GB, GRS):    $5/month
App Insights:            $5/month
Front Door:              $35/month
─────────────────────────────────
Total:                   ~$185/month
```

---

## Project 2: Microservices with AKS (Intermediate-Advanced)

### Architecture

```
                    Internet
                       │
                ┌──────┴──────┐
                │  Ingress    │
                │  Controller │
                └──────┬──────┘
                       │
    ┌──────────────────┼──────────────────┐
    ▼                  ▼                  ▼
┌────────┐      ┌────────────┐     ┌──────────┐
│ User   │      │  Product   │     │  Order   │
│ Service│      │  Service   │     │  Service │
│ (3 pods)│      │  (3 pods)  │     │  (3 pods)│
└───┬────┘      └─────┬──────┘     └────┬─────┘
    │                 │                  │
    ▼                 ▼                  ▼
┌────────┐      ┌────────────┐     ┌──────────┐
│ User DB│      │ Product DB │     │ Order DB │
│(Cosmos)│      │ (Cosmos)   │     │ (SQL)    │
└────────┘      └────────────┘     └──────────┘
                       │
                ┌──────┴──────┐
                │ Service Bus │
                │ (Events)    │
                └─────────────┘
```

### Implementation

```bash
# === Create AKS Cluster ===
az group create --name rg-microservices --location eastus

az aks create \
  --resource-group rg-microservices \
  --name aks-microservices \
  --node-count 3 \
  --node-vm-size Standard_D2s_v5 \
  --enable-managed-identity \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 10 \
  --network-plugin azure \
  --generate-ssh-keys

# === Create ACR ===
az acr create \
  --resource-group rg-microservices \
  --name acrmicroservices2024 \
  --sku Standard

az aks update \
  --resource-group rg-microservices \
  --name aks-microservices \
  --attach-acr acrmicroservices2024

# === Create Cosmos DB ===
az cosmosdb create \
  --resource-group rg-microservices \
  --name cosmos-microservices \
  --kind GlobalDocumentDB \
  --locations regionName=eastus failoverPriority=0

# === Create Service Bus ===
az servicebus namespace create \
  --resource-group rg-microservices \
  --name sb-microservices \
  --sku Standard

az servicebus topic create \
  --resource-group rg-microservices \
  --namespace-name sb-microservices \
  --name order-events

# === Build and Push Services ===
az acr build --registry acrmicroservices2024 --image user-service:v1 ./user-service/
az acr build --registry acrmicroservices2024 --image product-service:v1 ./product-service/
az acr build --registry acrmicroservices2024 --image order-service:v1 ./order-service/

# === Deploy to AKS ===
az aks get-credentials --resource-group rg-microservices --name aks-microservices
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/product-service.yaml
kubectl apply -f k8s/order-service.yaml
kubectl apply -f k8s/ingress.yaml
```

---

## Project 3: Serverless Data Pipeline (Intermediate)

### Architecture

```
Data Sources → Event Grid → Azure Functions → Cosmos DB → Power BI

Detailed Flow:
1. CSV files uploaded to Blob Storage
2. Event Grid detects new blob
3. Azure Function triggered
4. Function parses CSV, validates data
5. Clean data written to Cosmos DB
6. Another Function aggregates data
7. Results available via API (HTTP Function)
8. Power BI dashboard reads from Cosmos DB
```

```bash
# === Create Resources ===
az group create --name rg-data-pipeline --location eastus

# Storage for incoming data
az storage account create \
  --name stincomingdata2024 \
  --resource-group rg-data-pipeline \
  --sku Standard_LRS

az storage container create \
  --name incoming-csv \
  --account-name stincomingdata2024

# Cosmos DB for processed data
az cosmosdb create \
  --resource-group rg-data-pipeline \
  --name cosmos-analytics \
  --kind GlobalDocumentDB

az cosmosdb sql database create \
  --resource-group rg-data-pipeline \
  --account-name cosmos-analytics \
  --name analytics-db

az cosmosdb sql container create \
  --resource-group rg-data-pipeline \
  --account-name cosmos-analytics \
  --database-name analytics-db \
  --name processed-data \
  --partition-key-path "/category" \
  --throughput 400

# Function App
az functionapp create \
  --resource-group rg-data-pipeline \
  --name func-data-processor \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --storage-account stincomingdata2024

# Event Grid subscription
az eventgrid event-subscription create \
  --name sub-csv-uploaded \
  --source-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-data-pipeline/providers/Microsoft.Storage/storageAccounts/stincomingdata2024" \
  --endpoint "https://func-data-processor.azurewebsites.net/api/ProcessCSV" \
  --included-event-types Microsoft.Storage.BlobCreated \
  --subject-begins-with "/blobServices/default/containers/incoming-csv"
```

---

## Project 4: Hybrid Cloud Setup (Advanced)

### Scenario
A manufacturing company connects their factory floor systems to Azure for IoT analytics.

```
Factory Floor (On-Premises)          Azure Cloud
┌─────────────────────┐    VPN     ┌─────────────────────┐
│ IoT Sensors         │◄─────────►│ IoT Hub             │
│ SCADA Systems       │  Gateway   │ Stream Analytics    │
│ Local SQL Server    │           │ Cosmos DB           │
│ File Server         │           │ Power BI Dashboard  │
│ Azure Arc Agent     │           │ Azure Monitor       │
└─────────────────────┘           └─────────────────────┘

Components:
1. VPN Gateway: Secure connection between factory and Azure
2. Azure Arc: Manage on-premises servers from Azure Portal
3. IoT Hub: Ingest sensor data (temperature, pressure, vibration)
4. Stream Analytics: Real-time data processing
5. Cosmos DB: Store processed IoT data
6. Power BI: Real-time dashboards for factory managers
7. Azure Functions: Alert when sensor readings are abnormal
8. Azure Monitor: Monitor both cloud and on-premises resources
```

---

## Project 5: CI/CD Pipeline for Multi-Environment (Advanced)

### Architecture

```
Developer → Git Push → Azure DevOps Pipeline
                            │
                    ┌───────┼───────┐
                    ▼       ▼       ▼
                  Build   Test    Security
                  Stage   Stage   Scan
                    │
              ┌─────┼─────┐
              ▼           ▼
          Deploy to    Deploy to
          Staging      Production
          (auto)       (manual approval)
              │           │
              ▼           ▼
          ┌────────┐  ┌────────┐
          │Staging │  │  Prod  │
          │ Slot   │  │  Slot  │
          └────────┘  └────────┘
              │
          Smoke Tests
              │
          Swap Slots
          (zero downtime)
```

```yaml
# azure-pipelines.yml for multi-environment deployment

trigger:
  branches:
    include: [main]

variables:
  azureSubscription: 'Azure-Production'
  appName: 'ecom-api-prod'

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '18.x'
          - script: |
              npm ci
              npm run lint
              npm test
              npm run build
          - publish: $(System.DefaultWorkingDirectory)/dist
            artifact: webapp

  - stage: DeployStaging
    dependsOn: Build
    jobs:
      - deployment: Staging
        environment: 'staging'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: $(azureSubscription)
                    appName: $(appName)
                    slotName: 'staging'
                    package: '$(Pipeline.Workspace)/webapp'
                - script: |
                    # Smoke test
                    response=$(curl -s -o /dev/null -w "%{http_code}" https://$(appName)-staging.azurewebsites.net/health)
                    if [ "$response" != "200" ]; then exit 1; fi

  - stage: DeployProduction
    dependsOn: DeployStaging
    jobs:
      - deployment: Production
        environment: 'production'  # Requires approval
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureAppServiceManage@0
                  inputs:
                    azureSubscription: $(azureSubscription)
                    action: 'Swap Slots'
                    webAppName: $(appName)
                    sourceSlot: 'staging'
                    targetSlot: 'production'
```

---

## Project Cost Comparison

```
┌──────────────────────┬──────────────┬────────────────────┐
│ Project              │ Monthly Cost │ Annual Cost        │
├──────────────────────┼──────────────┼────────────────────┤
│ E-Commerce (PaaS)    │ ~$185        │ ~$2,220            │
│ Microservices (AKS)  │ ~$450        │ ~$5,400            │
│ Serverless Pipeline  │ ~$50         │ ~$600              │
│ Hybrid Cloud         │ ~$800        │ ~$9,600            │
│ CI/CD Pipeline       │ ~$100        │ ~$1,200            │
└──────────────────────┴──────────────┴────────────────────┘

Note: Costs are approximate and vary by usage, region, and pricing tier.
Use Azure Pricing Calculator for accurate estimates.
```

---

[← Previous Module](./Module-16-Governance-and-Compliance.md) | [Next Module: Exam Prep & Troubleshooting →](./Module-18-Exam-Prep-and-Troubleshooting.md)
