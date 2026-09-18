# Module 05: Azure Storage

## Certification Relevance: AZ-104 (15-20%), AZ-204

---

## 5.1 Azure Storage Overview

### Storage Account Types

| Type | Services | Use Case |
|------|----------|----------|
| **Blob Storage** | Unstructured data (files, images, videos) | Media storage, backups, data lakes |
| **File Storage** | Managed file shares (SMB/NFS) | Replace on-premises file servers |
| **Queue Storage** | Message queuing | Decouple application components |
| **Table Storage** | NoSQL key-value store | IoT data, user profiles |
| **Disk Storage** | Managed disks for VMs | OS disks, data disks |

### Storage Account Naming Rules
```
- Globally unique across all of Azure
- 3-24 characters
- Lowercase letters and numbers ONLY
- No hyphens, underscores, or special characters

Valid:   mystorageaccount01, stprodeastus2024
Invalid: my-storage, MyStorage, st_prod, st
```

### Redundancy Options

```
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE REDUNDANCY                           │
├──────────┬──────────┬──────────────────┬───────────────────────┤
│ Option   │ Copies   │ Protection       │ Cost (relative)       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ LRS      │ 3 copies │ Single data      │ $ (cheapest)          │
│          │ in 1 DC  │ center failure   │                       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ ZRS      │ 3 copies │ Data center      │ $$                    │
│          │ in 3 AZs │ failure          │                       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ GRS      │ 6 copies │ Regional failure │ $$$                   │
│          │ 2 regions│ (read from       │                       │
│          │          │ primary only)    │                       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ RA-GRS   │ 6 copies │ Regional failure │ $$$$ (most expensive) │
│          │ 2 regions│ (read from       │                       │
│          │          │ both regions)    │                       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ GZRS     │ 6 copies │ Zone + regional  │ $$$$                  │
│          │ 3 AZs +  │ failure          │                       │
│          │ 1 region │                  │                       │
├──────────┼──────────┼──────────────────┼───────────────────────┤
│ RA-GZRS  │ 6 copies │ Zone + regional  │ $$$$$ (highest)       │
│          │ 3 AZs +  │ (read from both) │                       │
│          │ 1 region │                  │                       │
└──────────┴──────────┴──────────────────┴───────────────────────┘

LRS  = Locally Redundant Storage
ZRS  = Zone-Redundant Storage
GRS  = Geo-Redundant Storage
RA-GRS = Read-Access Geo-Redundant Storage
GZRS = Geo-Zone-Redundant Storage
RA-GZRS = Read-Access Geo-Zone-Redundant Storage
```

### Real-World Example
```
Industry Example: A healthcare company stores patient X-ray images.
- Compliance requires data to survive a regional disaster
- They choose RA-GRS: 3 copies in East US + 3 copies in West US
- If East US goes down, they can still READ images from West US
- Cost: ~$0.05/GB/month for RA-GRS vs $0.018/GB for LRS
- For 10 TB of images: ~$500/month (RA-GRS) vs ~$180/month (LRS)
```

---

## 5.2 Creating a Storage Account

### Portal UI Walkthrough: Create a Storage Account

```
PORTAL STEPS — Create a Storage Account:

Step 1: Navigate to Storage Accounts
   → Search "Storage accounts" in the search bar
   → Click "Storage accounts" from results
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Storage account name: stprodeastus2024                  │
   │   ⚠️ Rules: 3-24 chars, lowercase + numbers ONLY       │
   │   ⚠️ Must be globally unique across ALL of Azure       │
   │ Region:               (US) East US                      │
   │ Performance:          ● Standard (HDD-backed, cheaper)  │
   │                       ○ Premium (SSD-backed, faster)    │
   │ Redundancy:           Locally-redundant storage (LRS)   │
   │   Options:                                              │
   │   • LRS  — 3 copies in 1 data center ($)               │
   │   • ZRS  — 3 copies across 3 zones ($$)                │
   │   • GRS  — 6 copies across 2 regions ($$$)             │
   │   • RA-GRS — GRS + read from secondary ($$$$)          │
   └────────────────────────────────────────────────────────┘

Step 3: Advanced Tab
   → Click "Next: Advanced >"
   ┌─ Security ─────────────────────────────────────────────┐
   │ Require secure transfer (HTTPS): ☑ Enabled              │
   │ Allow Blob anonymous access:     ☐ Disabled             │
   │   (keep disabled for security)                          │
   │ Enable storage account key access: ☑ Enabled            │
   │ Minimum TLS version:             TLS 1.2                │
   └────────────────────────────────────────────────────────┘
   ┌─ Blob Storage ─────────────────────────────────────────┐
   │ Access tier (default): ● Hot  ○ Cool                    │
   │   Hot = frequent access, higher storage cost            │
   │   Cool = infrequent access, lower storage cost          │
   │ Enable soft delete for blobs: ☑ Enabled                 │
   │ Retention days: 7                                       │
   └────────────────────────────────────────────────────────┘

Step 4: Networking Tab
   → Click "Next: Networking >"
   ┌─ Network Access ───────────────────────────────────────┐
   │ Network access:  ● Enable public access from all       │
   │                    networks                             │
   │                  ○ Enable public access from selected   │
   │                    virtual networks and IP addresses    │
   │                  ○ Disable public access                │
   │                                                         │
   │ For production: Choose "selected networks" and add      │
   │ your VNet/subnet for security                           │
   └────────────────────────────────────────────────────────┘

Step 5: Data Protection Tab
   → Click "Next: Data protection >"
   ┌─ Recovery ─────────────────────────────────────────────┐
   │ Enable soft delete for blobs:      ☑ 7 days             │
   │ Enable soft delete for containers: ☑ 7 days             │
   │ Enable soft delete for file shares:☑ 7 days             │
   │ Enable versioning for blobs:       ☑ Enabled            │
   │ Enable blob change feed:           ☐ Disabled           │
   └────────────────────────────────────────────────────────┘

Step 6: Encryption Tab
   → Click "Next: Encryption >"
   → Encryption type: Microsoft-managed keys (default)
   → (Use customer-managed keys for compliance requirements)

Step 7: Tags → Review + Create
   → Add tags: Environment=Demo
   → Click "Review + create"
   → Review the summary:
     ┌─────────────────────────────────────────┐
     │ Name:        stprodeastus2024           │
     │ Region:      East US                    │
     │ Performance: Standard                   │
     │ Redundancy:  LRS                        │
     │ Access tier: Hot                        │
     └─────────────────────────────────────────┘
   → Click "Create"
```

### Portal UI Walkthrough: Upload Files to Blob Storage

```
PORTAL STEPS — Create a Container and Upload Files:

Step 1: Go to Your Storage Account
   → Storage accounts → Click "stprodeastus2024"

Step 2: Create a Blob Container
   → Left sidebar → "Containers" (under Data storage)
   → Click "+ Container"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:                  images                            │
   │ Anonymous access level: Private (no anonymous access)    │
   │   Options:                                               │
   │   • Private — no anonymous access (most secure)         │
   │   • Blob — anonymous read for blobs only                │
   │   • Container — anonymous read for container + blobs    │
   │ Click "Create"                                           │
   └─────────────────────────────────────────────────────────┘

Step 3: Upload a File
   → Click the "images" container to open it
   → Click "Upload" button at the top
   → Click "Browse for files" → Select a file from your computer
   → Advanced options (expand):
     → Blob type: Block blob (default)
     → Access tier: Hot
     → Upload to folder: (leave empty or type "photos/")
   → Click "Upload"

Step 4: View the Uploaded File
   → Click the file name in the container
   → You'll see file properties:
     ┌─────────────────────────────────────────────────────┐
     │ Name:         photo.jpg                              │
     │ URL:          https://stprodeastus2024.blob.core.    │
     │               windows.net/images/photo.jpg           │
     │ Blob type:    Block blob                             │
     │ Access tier:  Hot                                    │
     │ Size:         2.5 MB                                 │
     │ Last modified: 2024-01-15 10:30:00                   │
     └─────────────────────────────────────────────────────┘
   → Click "Download" to download the file
   → Click "Generate SAS" to create a temporary access URL

Step 5: Generate a SAS Token (Temporary Access URL)
   → Click the file → Click "Generate SAS" tab
   ┌─────────────────────────────────────────────────────────┐
   │ Signing method:    Account key                           │
   │ Signing key:       Key 1                                 │
   │ Permissions:       ☑ Read                                │
   │ Start date/time:   (current time)                        │
   │ Expiry date/time:  (set to tomorrow or desired expiry)  │
   │ Allowed protocols: HTTPS only                            │
   │ Click "Generate SAS token and URL"                       │
   └─────────────────────────────────────────────────────────┘
   → Copy the "Blob SAS URL"
   → Share this URL — anyone with it can access the file
     until the expiry date
```

### Portal UI Walkthrough: Set Up Lifecycle Management

```
PORTAL STEPS — Auto-tier Blobs Based on Age:

Step 1: Go to Your Storage Account
   → Storage accounts → Click your account

Step 2: Open Lifecycle Management
   → Left sidebar → "Lifecycle management" (under Data management)
   → Click "+ Add a rule"

Step 3: Configure Rule
   ┌─ Details ──────────────────────────────────────────────┐
   │ Rule name:          move-to-cool-after-30-days          │
   │ Rule scope:         Apply rule to all blobs             │
   │ Blob type:          ☑ Block blobs                       │
   │ Blob subtype:       ☑ Base blobs                        │
   └────────────────────────────────────────────────────────┘
   → Click "Next"

   ┌─ Base Blobs ───────────────────────────────────────────┐
   │ IF base blob was last modified more than 30 days ago:   │
   │   THEN → Move to cool storage                          │
   │                                                         │
   │ IF base blob was last modified more than 180 days ago:  │
   │   THEN → Move to archive storage                       │
   │                                                         │
   │ IF base blob was last modified more than 365 days ago:  │
   │   THEN → Delete the blob                               │
   └────────────────────────────────────────────────────────┘
   → Click "Add"

Step 4: Verify
   → You'll see the rule listed in Lifecycle management
   → Azure runs this rule once per day automatically
   → Saves money by moving old data to cheaper tiers
```

### Creating a Storage Account with CLI

```bash
# Create a storage account
az storage account create \
  --name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot

# Meaning:
# --name             : Globally unique name
# --sku Standard_LRS : Standard performance, LRS redundancy
# --kind StorageV2   : General-purpose v2 (recommended)
# --access-tier Hot  : Optimized for frequent access

# Output:
# {
#   "name": "stprodeastus2024",
#   "primaryEndpoints": {
#     "blob": "https://stprodeastus2024.blob.core.windows.net/",
#     "file": "https://stprodeastus2024.file.core.windows.net/",
#     "queue": "https://stprodeastus2024.queue.core.windows.net/",
#     "table": "https://stprodeastus2024.table.core.windows.net/"
#   },
#   "sku": { "name": "Standard_LRS" },
#   "kind": "StorageV2"
# }

# Get storage account keys
az storage account keys list \
  --account-name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --output table

# Output:
# KeyName    Value                                    Permissions
# ---------  ---------------------------------------  -----------
# key1       abc123...xyz789                          FULL
# key2       def456...uvw012                          FULL

# Get connection string
az storage account show-connection-string \
  --name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --output tsv

# Output:
# DefaultEndpointsProtocol=https;AccountName=stprodeastus2024;AccountKey=abc123...;EndpointSuffix=core.windows.net
```

---

## 5.3 Blob Storage

### What is Blob Storage?
Object storage for unstructured data. "Blob" = Binary Large Object.

### Blob Types

| Type | Use Case | Max Size |
|------|----------|----------|
| **Block Blob** | Files, images, videos, documents | 190.7 TB |
| **Append Blob** | Log files (append-only operations) | 195 GB |
| **Page Blob** | VM disks, random read/write | 8 TB |

### Access Tiers

```
Hot    → Frequent access. Higher storage cost, lower access cost.
         Use for: Active data, frequently accessed files
         Cost: ~$0.018/GB/month storage, $0.004/10K reads

Cool   → Infrequent access (30+ days). Lower storage, higher access.
         Use for: Short-term backups, older data still needed
         Cost: ~$0.01/GB/month storage, $0.01/10K reads

Cold   → Rarely accessed (90+ days). Even lower storage cost.
         Use for: Compliance data, long-term backups
         Cost: ~$0.0036/GB/month storage, $0.01/10K reads

Archive → Offline storage (180+ days). Cheapest storage, expensive access.
          Use for: Regulatory archives, historical data
          Cost: ~$0.00099/GB/month storage, $0.02/10K reads
          ⚠️ Rehydration takes hours (up to 15 hours for Standard)
```

### Working with Blobs

```bash
# Create a container (like a folder for blobs)
az storage container create \
  --name images \
  --account-name stprodeastus2024 \
  --public-access off

# Meaning:
# --name images       : Container name
# --public-access off : No anonymous access (private)
# Options: off (private), blob (anonymous read for blobs), container (anonymous read for container + blobs)

# Upload a file
az storage blob upload \
  --account-name stprodeastus2024 \
  --container-name images \
  --name photo.jpg \
  --file ./photo.jpg \
  --tier Hot

# Output:
# {
#   "etag": "\"0x8DC1234567890\"",
#   "lastModified": "2024-01-15T10:30:00+00:00",
#   "url": "https://stprodeastus2024.blob.core.windows.net/images/photo.jpg"
# }

# Upload multiple files
az storage blob upload-batch \
  --account-name stprodeastus2024 \
  --destination images \
  --source ./local-images/ \
  --pattern "*.jpg"

# List blobs in a container
az storage blob list \
  --account-name stprodeastus2024 \
  --container-name images \
  --output table

# Output:
# Name          Blob Type    Blob Tier    Length     Last Modified
# -----------   ----------   ---------    --------   -------------------------
# photo.jpg     BlockBlob    Hot          2048576    2024-01-15T10:30:00+00:00
# logo.png      BlockBlob    Hot          51200      2024-01-15T10:31:00+00:00

# Download a blob
az storage blob download \
  --account-name stprodeastus2024 \
  --container-name images \
  --name photo.jpg \
  --file ./downloaded-photo.jpg

# Delete a blob
az storage blob delete \
  --account-name stprodeastus2024 \
  --container-name images \
  --name photo.jpg

# Change blob tier
az storage blob set-tier \
  --account-name stprodeastus2024 \
  --container-name images \
  --name old-photo.jpg \
  --tier Archive
# Meaning: Move blob to Archive tier (cheapest storage)

# Generate SAS token (temporary access URL)
az storage blob generate-sas \
  --account-name stprodeastus2024 \
  --container-name images \
  --name photo.jpg \
  --permissions r \
  --expiry 2024-12-31T23:59:59Z \
  --output tsv

# Output: se=2024-12-31T23%3A59%3A59Z&sp=r&sv=2022-11-02&sr=b&sig=abc123...
# Full URL: https://stprodeastus2024.blob.core.windows.net/images/photo.jpg?<SAS_TOKEN>
# Meaning: Anyone with this URL can READ the blob until Dec 31, 2024
```

### Lifecycle Management

```bash
# Create a lifecycle policy (auto-tier blobs based on age)
az storage account management-policy create \
  --account-name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --policy '{
    "rules": [
      {
        "name": "move-to-cool",
        "type": "Lifecycle",
        "definition": {
          "filters": { "blobTypes": ["blockBlob"] },
          "actions": {
            "baseBlob": {
              "tierToCool": { "daysAfterModificationGreaterThan": 30 },
              "tierToArchive": { "daysAfterModificationGreaterThan": 180 },
              "delete": { "daysAfterModificationGreaterThan": 365 }
            }
          }
        }
      }
    ]
  }'

# This policy:
# After 30 days  → Move to Cool tier (save ~45% on storage)
# After 180 days → Move to Archive tier (save ~95% on storage)
# After 365 days → Delete the blob
```

---

## 5.4 Azure File Storage

### What is Azure Files?
Fully managed file shares in the cloud, accessible via SMB (Server Message Block) or NFS protocols.

```
Real-World Example: A company has 50 employees sharing files on a
Windows file server. They migrate to Azure Files:
- Mount the share as Z: drive on all workstations
- No file server to maintain
- Accessible from anywhere
- Automatic backups with Azure Backup
- Cost: ~$0.06/GB/month (Hot tier)
```

```bash
# Create a file share
az storage share create \
  --name company-files \
  --account-name stprodeastus2024 \
  --quota 100
# --quota 100: Maximum size in GB

# Upload a file
az storage file upload \
  --share-name company-files \
  --source ./report.pdf \
  --path reports/report.pdf \
  --account-name stprodeastus2024

# Create a directory
az storage directory create \
  --share-name company-files \
  --name reports \
  --account-name stprodeastus2024

# List files
az storage file list \
  --share-name company-files \
  --path reports \
  --account-name stprodeastus2024 \
  --output table

# Mount on Windows (PowerShell)
# $connectTestResult = Test-NetConnection -ComputerName stprodeastus2024.file.core.windows.net -Port 445
# net use Z: \\stprodeastus2024.file.core.windows.net\company-files /u:stprodeastus2024 <ACCESS_KEY>

# Mount on Linux
# sudo mount -t cifs //stprodeastus2024.file.core.windows.net/company-files /mnt/files \
#   -o vers=3.0,username=stprodeastus2024,password=<ACCESS_KEY>,dir_mode=0777,file_mode=0777
```

### Azure File Sync
```
Syncs Azure Files with on-premises Windows file servers.

On-Premises Server ←→ Azure File Sync ←→ Azure Files
                        (Cloud tiering: keeps frequently
                         accessed files local, moves
                         cold files to cloud)

Use case: Branch offices with local file servers that need
central cloud backup and cross-office file sharing.
```

---

## 5.5 Queue Storage

```bash
# Create a queue
az storage queue create \
  --name order-processing \
  --account-name stprodeastus2024

# Add a message to the queue
az storage message put \
  --queue-name order-processing \
  --content '{"orderId": "12345", "product": "Widget", "quantity": 5}' \
  --account-name stprodeastus2024

# Peek at messages (view without removing)
az storage message peek \
  --queue-name order-processing \
  --num-messages 5 \
  --account-name stprodeastus2024

# Get messages (makes them invisible for processing)
az storage message get \
  --queue-name order-processing \
  --num-messages 1 \
  --account-name stprodeastus2024

# Delete a processed message
az storage message delete \
  --queue-name order-processing \
  --id MESSAGE_ID \
  --pop-receipt POP_RECEIPT \
  --account-name stprodeastus2024
```

```
Real-World Example: E-commerce order processing
1. Customer places order → message added to queue
2. Order processor picks up message → processes payment
3. If processing fails → message reappears after visibility timeout
4. If processing succeeds → message deleted

This decouples the web frontend from the order processing backend.
If the backend is down, orders queue up and are processed when it recovers.
```

---

## 5.6 Table Storage

```bash
# Create a table
az storage table create \
  --name Customers \
  --account-name stprodeastus2024

# Insert an entity
az storage entity insert \
  --table-name Customers \
  --entity PartitionKey=US RowKey=CUST001 Name="John Doe" Email=john@example.com \
  --account-name stprodeastus2024

# Query entities
az storage entity query \
  --table-name Customers \
  --filter "PartitionKey eq 'US'" \
  --account-name stprodeastus2024 \
  --output table

# Output:
# PartitionKey    RowKey     Name        Email
# -------------   --------   ---------   -----------------
# US              CUST001    John Doe    john@example.com
```

---

## 5.7 Managed Disks

### Disk Types

| Type | IOPS | Throughput | Use Case | Cost/month (128 GB) |
|------|------|-----------|----------|-------------------|
| Standard HDD | 500 | 60 MB/s | Backups, dev/test | ~$5 |
| Standard SSD | 500 | 60 MB/s | Web servers, light workloads | ~$10 |
| Premium SSD | 5,000 | 200 MB/s | Production databases, enterprise apps | ~$20 |
| Ultra Disk | 160,000 | 4,000 MB/s | SAP HANA, top-tier databases | ~$100+ |

```bash
# Create a managed disk
az disk create \
  --resource-group rg-demo-eastus \
  --name disk-data-01 \
  --size-gb 128 \
  --sku Premium_LRS

# Attach disk to VM
az vm disk attach \
  --resource-group rg-demo-eastus \
  --vm-name vm-web-01 \
  --name disk-data-01

# Detach disk from VM
az vm disk detach \
  --resource-group rg-demo-eastus \
  --vm-name vm-web-01 \
  --name disk-data-01

# Create a snapshot (point-in-time backup)
az snapshot create \
  --resource-group rg-demo-eastus \
  --name snap-disk-data-01 \
  --source disk-data-01

# Create disk from snapshot
az disk create \
  --resource-group rg-demo-eastus \
  --name disk-restored \
  --source snap-disk-data-01 \
  --size-gb 128 \
  --sku Premium_LRS
```

---

## 5.8 Storage Security

### Access Keys vs SAS vs Azure AD

```
1. Access Keys (full access)
   - 2 keys per storage account
   - Full read/write/delete access to everything
   - Rotate regularly
   - ⚠️ Never share or commit to code

2. Shared Access Signatures (SAS) - granular, time-limited
   - Service SAS: Access to specific service (blob, file, queue, table)
   - Account SAS: Access to one or more services
   - User Delegation SAS: Secured with Azure AD (most secure SAS)

3. Azure AD Authentication (recommended)
   - RBAC roles: Storage Blob Data Reader, Storage Blob Data Contributor
   - No keys to manage
   - Audit trail via Azure AD logs
```

```bash
# Regenerate access key
az storage account keys renew \
  --account-name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --key primary

# Enable Azure AD authentication
az storage account update \
  --name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --default-action Deny

# Add network rule (allow specific VNet)
az storage account network-rule add \
  --account-name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --subnet web-subnet

# Enable soft delete (recover deleted blobs)
az storage blob service-properties delete-policy update \
  --account-name stprodeastus2024 \
  --enable true \
  --days-retained 30
# Meaning: Deleted blobs can be recovered within 30 days

# Enable versioning
az storage account blob-service-properties update \
  --account-name stprodeastus2024 \
  --resource-group rg-demo-eastus \
  --enable-versioning true
```

---

## 5.9 AzCopy Tool

```bash
# Download AzCopy
# https://aka.ms/downloadazcopy-v10-linux

# Login with Azure AD
azcopy login

# Copy local file to blob
azcopy copy './data.csv' 'https://stprodeastus2024.blob.core.windows.net/data/data.csv?SAS_TOKEN'

# Copy entire directory
azcopy copy './local-folder' 'https://stprodeastus2024.blob.core.windows.net/backup?SAS_TOKEN' --recursive

# Sync (like rsync - only copies changed files)
azcopy sync './local-folder' 'https://stprodeastus2024.blob.core.windows.net/backup?SAS_TOKEN'

# Copy between storage accounts
azcopy copy \
  'https://source.blob.core.windows.net/data?SAS' \
  'https://dest.blob.core.windows.net/data?SAS' \
  --recursive

# Real-World: Migrate 5 TB of data between storage accounts
# AzCopy uses server-to-server copy (data doesn't flow through your machine)
# Speed: ~10 GB/minute for server-to-server copies
```

---

## 5.10 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `StorageAccountAlreadyTaken` | Name not globally unique | Choose a different name |
| `AccountNameInvalid` | Invalid characters (hyphens, uppercase) | Use only lowercase letters and numbers, 3-24 chars |
| `AuthorizationPermissionMismatch` | Wrong RBAC role | Assign Storage Blob Data Contributor role |
| `BlobNotFound` | Blob doesn't exist or wrong path | Check container name and blob path |
| `ContainerAlreadyExists` | Container with same name exists | Use a different name or check existing containers |
| `InsufficientAccountPermissions` | Using Azure AD but no data role | Assign Storage Blob Data Reader/Contributor |
| `This request is not authorized` | Firewall blocking access | Add your IP or VNet to storage firewall rules |
| `The specified resource does not exist` | Wrong account name or key | Verify account name and regenerate keys |
| SAS token expired | Token past expiry date | Generate a new SAS token with future expiry |

---

## 5.11 Practice Questions

### Question 1
**Which redundancy option provides read access from a secondary region?**
- A) LRS
- B) GRS
- C) RA-GRS ✅
- D) ZRS

### Question 2
**What is the cheapest blob access tier?**
- A) Hot
- B) Cool
- C) Cold
- D) Archive ✅

**Explanation**: Archive is the cheapest for storage but most expensive for access. Data must be rehydrated before reading.

### Question 3
**A storage account name must be:**
- A) Unique within the resource group
- B) Unique within the subscription
- C) Globally unique across all of Azure ✅
- D) Unique within the region

### Question 4
**Which tool is best for copying large amounts of data between storage accounts?**
- A) Azure Portal
- B) Azure CLI
- C) AzCopy ✅
- D) PowerShell

### Question 5
**How many copies of data does ZRS maintain?**
- A) 1
- B) 2
- C) 3 ✅
- D) 6

**Explanation**: ZRS stores 3 copies across 3 availability zones in a single region.

---

[← Previous Module](./Module-04-Networking.md) | [Next Module: Databases →](./Module-06-Databases.md)
