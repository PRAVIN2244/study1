# Module 13: High Availability & Disaster Recovery

## Certification Relevance: AZ-104

---

## 13.1 HA vs DR Concepts

```
High Availability (HA):                Disaster Recovery (DR):
├── Prevent downtime                   ├── Recover from disasters
├── Redundancy within a region         ├── Redundancy across regions
├── Automatic failover                 ├── May require manual failover
├── Minutes of RTO                     ├── Hours of RTO
├── Examples:                          ├── Examples:
│   ├── Availability Zones             │   ├── Azure Site Recovery
│   ├── Load Balancers                 │   ├── Geo-redundant storage
│   └── VM Scale Sets                  │   └── Cross-region replication
└── Cost: Moderate                     └── Cost: Higher (duplicate infra)

Key Metrics:
RTO (Recovery Time Objective): How long until service is restored
RPO (Recovery Point Objective): How much data loss is acceptable

Example:
RTO = 1 hour → Service must be back within 1 hour of failure
RPO = 15 minutes → Maximum 15 minutes of data can be lost
```

---

## 13.2 Availability Options Summary

```
┌─────────────────────────────────────────────────────────────┐
│              AVAILABILITY OPTIONS                           │
├──────────────────┬──────────┬───────────────────────────────┤
│ Option           │ SLA      │ Protects Against              │
├──────────────────┼──────────┼───────────────────────────────┤
│ Single VM        │ 99.9%    │ Nothing (single point of      │
│ (Premium SSD)    │          │ failure)                      │
├──────────────────┼──────────┼───────────────────────────────┤
│ Availability Set │ 99.95%   │ Hardware failure within       │
│                  │          │ a data center                 │
├──────────────────┼──────────┼───────────────────────────────┤
│ Availability     │ 99.99%   │ Data center failure           │
│ Zones            │          │ within a region               │
├──────────────────┼──────────┼───────────────────────────────┤
│ Multi-Region     │ 99.999%+ │ Entire region failure         │
│ (with Traffic    │          │                               │
│  Manager/Front   │          │                               │
│  Door)           │          │                               │
└──────────────────┴──────────┴───────────────────────────────┘
```

---

## 13.3 Azure Backup

### What is Azure Backup?
A service that provides backup and restore for Azure resources and on-premises workloads.

```
What can be backed up:
├── Azure VMs (full VM backup)
├── Azure Files (file share backup)
├── SQL Server in Azure VMs
├── Azure SQL Database
├── Azure Blob Storage
├── Azure Managed Disks
├── On-premises (via MARS agent or Azure Backup Server)
└── SAP HANA databases
```

### Portal UI Walkthrough: Set Up VM Backup

```
PORTAL STEPS — Back Up a Virtual Machine:

Step 1: Navigate to Your VM
   → Virtual machines → Click your VM name (e.g., vm-web-01)

Step 2: Enable Backup
   → Left sidebar → "Backup"
   ┌─ Backup Configuration ─────────────────────────────────┐
   │ Recovery Services vault:                                 │
   │   ● Create new                                          │
   │   Vault name:       rsv-demo-2024                       │
   │   Resource group:   rg-demo-eastus                      │
   │                                                         │
   │ Backup policy:                                          │
   │   ● DefaultPolicy                                      │
   │     (Daily backup at 12:00 AM UTC, 30-day retention)   │
   │   ○ Create a new policy                                │
   │     → Backup frequency: Daily / Weekly                  │
   │     → Retention: 30 days / 1 year / custom             │
   │                                                         │
   │ Click "Enable Backup"                                   │
   └─────────────────────────────────────────────────────────┘

Step 3: Trigger an On-Demand Backup
   → After backup is enabled, go to VM → "Backup"
   → Click "Backup now"
   → Retain backup until: Select a date (e.g., 30 days from now)
   → Click "OK"
   → Backup starts immediately (takes 15-60 minutes)

Step 4: Monitor Backup Status
   → VM → "Backup" → See backup status:
     Last backup: Completed at 2024-01-15 12:05 AM
     Backup items: 1 VM
     Recovery points: 5

Step 5: Restore a VM from Backup
   → VM → "Backup" → Click "Restore VM"
   → Select a restore point (date/time)
   → Restore type:
     ● Create new VM
       VM name: vm-web-01-restored
       Resource group: rg-demo-eastus
     ○ Replace existing (overwrites current VM)
   → Click "Restore"
   → Restoration takes 15-60 minutes
```

### Portal UI Walkthrough: Create a Recovery Services Vault

```
PORTAL STEPS — Create a Recovery Services Vault:

Step 1: Navigate to Recovery Services Vaults
   → Search "Recovery Services vaults" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Vault name:         rsv-demo-2024                        │
   │ Region:             East US                              │
   └─────────────────────────────────────────────────────────┘
   → Click "Review + create" → "Create"

Step 3: Configure Backup for Multiple VMs
   → Go to vault → Left sidebar → "Backup"
   → Where is your workload running? Azure
   → What do you want to back up? Virtual machine
   → Click "Backup"
   → Select VMs to back up:
     ☑ vm-web-01
     ☑ vm-web-02
     ☑ vm-app-01
   → Click "OK" → "Enable Backup"

Step 4: View Backup Dashboard
   → Vault → "Overview"
   → See: Backup items, alerts, jobs, storage usage
   → Left sidebar → "Backup Jobs" to see all backup activity
```

```bash
# Step 1: Create a Recovery Services Vault
az backup vault create \
  --resource-group rg-demo-eastus \
  --name rsv-demo-2024 \
  --location eastus

# Step 2: Set backup policy (how often, how long to keep)
# Default policy: Daily backup, 30-day retention

# Step 3: Enable backup for a VM
az backup protection enable-for-vm \
  --resource-group rg-demo-eastus \
  --vault-name rsv-demo-2024 \
  --vm vm-web-01 \
  --policy-name DefaultPolicy

# Trigger an on-demand backup
az backup protection backup-now \
  --resource-group rg-demo-eastus \
  --vault-name rsv-demo-2024 \
  --container-name "IaasVMContainer;iaasvmcontainerv2;rg-demo-eastus;vm-web-01" \
  --item-name "VM;iaasvmcontainerv2;rg-demo-eastus;vm-web-01" \
  --retain-until 2024-12-31

# List backup items
az backup item list \
  --resource-group rg-demo-eastus \
  --vault-name rsv-demo-2024 \
  --output table

# List recovery points
az backup recoverypoint list \
  --resource-group rg-demo-eastus \
  --vault-name rsv-demo-2024 \
  --container-name "IaasVMContainer;..." \
  --item-name "VM;..." \
  --output table

# Restore a VM
az backup restore restore-disks \
  --resource-group rg-demo-eastus \
  --vault-name rsv-demo-2024 \
  --container-name "IaasVMContainer;..." \
  --item-name "VM;..." \
  --rp-name "RECOVERY_POINT_NAME" \
  --storage-account stprodeastus2024
```

### Backup Policies

```
Policy defines:
├── Frequency: Daily, Weekly, Monthly, Yearly
├── Time: When to run (e.g., 2:00 AM UTC)
├── Retention:
│   ├── Daily: Keep for 30 days
│   ├── Weekly: Keep for 12 weeks
│   ├── Monthly: Keep for 12 months
│   └── Yearly: Keep for 10 years
└── Snapshot retention: 2-5 days (instant restore)

Real-World Example:
A company's backup policy for production databases:
- Daily backup at 1:00 AM → retain 30 days
- Weekly backup (Sunday) → retain 12 weeks
- Monthly backup (1st) → retain 24 months
- Yearly backup (Jan 1) → retain 7 years (compliance)
```

---

## 13.4 Azure Site Recovery (ASR)

### What is ASR?
A disaster recovery service that replicates VMs from one Azure region to another (or from on-premises to Azure).

```
Normal Operation:
┌──────────────┐                    ┌──────────────┐
│  East US     │    Replication     │  West US     │
│  (Primary)   │ ──────────────►   │  (Secondary) │
│              │    Continuous      │              │
│  VM-Web-01   │                    │  VM-Web-01   │
│  VM-App-01   │                    │  VM-App-01   │
│  VM-DB-01    │                    │  VM-DB-01    │
│  ✅ Active    │                    │  💤 Standby   │
└──────────────┘                    └──────────────┘

After Failover (East US disaster):
┌──────────────┐                    ┌──────────────┐
│  East US     │                    │  West US     │
│  (Down)      │                    │  (Active)    │
│              │                    │              │
│  ❌ Offline   │                    │  VM-Web-01   │
│              │                    │  VM-App-01   │
│              │                    │  VM-DB-01    │
│              │                    │  ✅ Active    │
└──────────────┘                    └──────────────┘
```

### Portal UI Walkthrough: Set Up Azure Site Recovery (VM Replication)

```
PORTAL STEPS — Replicate a VM to Another Region:

Step 1: Create a Recovery Services Vault in the Target Region
   → Search "Recovery Services vaults" → Click "+ Create"
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-dr-westus (create new)            │
   │ Vault name:         rsv-dr-westus                        │
   │ Region:             West US  ← target/DR region          │
   │ Click "Review + create" → "Create"                       │
   └─────────────────────────────────────────────────────────┘

Step 2: Enable Site Recovery
   → Go to the vault → Left sidebar → "Site Recovery"
   → Under "Azure virtual machines", click "Enable replication"

Step 3: Select Source
   ┌─ Source Settings ──────────────────────────────────────┐
   │ Source region:      East US (where your VMs are now)    │
   │ Subscription:      Select your subscription             │
   │ Resource group:    rg-demo-eastus                       │
   │ VM deployment model: Resource Manager                   │
   │ Click "Next"                                            │
   └────────────────────────────────────────────────────────┘

Step 4: Select Virtual Machines
   → Check the VMs you want to replicate:
     ☑ vm-web-01
     ☑ vm-app-01
   → Click "Next"

Step 5: Configure Replication Settings
   ┌─ Target Settings ─────────────────────────────────────┐
   │ Target region:          West US                        │
   │ Target resource group:  rg-demo-eastus-asr (auto)      │
   │ Target virtual network: vnet-main-asr (auto-created)   │
   │ Target storage:         Auto-configured                │
   │ Replication policy:     24-hour-retention-policy        │
   │   (recovery point retention: 24 hours)                 │
   │   (app-consistent snapshot frequency: 4 hours)         │
   └────────────────────────────────────────────────────────┘
   → Click "Next" → "Enable replication"
   → ⚠️ Initial replication takes 30-60 minutes

Step 6: Monitor Replication
   → Vault → "Replicated items"
   → Status shows:
     vm-web-01    Protected    100% synchronized
     vm-app-01    Protected    100% synchronized

Step 7: Test Failover (Non-Disruptive)
   → Click a replicated VM → Click "Test Failover"
   ┌─────────────────────────────────────────────────────────┐
   │ Recovery point:     Latest processed                     │
   │ Azure virtual network: Select a test VNet               │
   │   (use a separate VNet to avoid conflicts)              │
   │ Click "OK"                                               │
   └─────────────────────────────────────────────────────────┘
   → A test VM spins up in West US
   → Verify the test VM works correctly
   → Click "Cleanup test failover" when done

Step 8: Actual Failover (During a Real Disaster)
   → Click replicated VM → "Failover"
   → Recovery point: Latest processed
   → ☑ Shut down machine before beginning failover
   → Click "OK"
   → VM starts running in West US
   → Update DNS/load balancer to point to new region

Step 9: Failback (After Primary Region Recovers)
   → Click "Re-protect" to reverse replication
   → Then "Failover" back to East US when ready
```

```bash
# CLI reference for Site Recovery:

# Create Recovery Services Vault in target region
az backup vault create \
  --resource-group rg-dr-westus \
  --name rsv-dr-westus \
  --location westus

# ⚠️ ASR setup is best done via Portal (as shown above)
# The Portal provides a guided wizard that handles:
# - Network mapping
# - Storage account creation
# - Replication policy configuration
# - DNS and IP address management

# Test failover (non-disruptive)
# Portal: Recovery Services Vault → Replicated Items → VM → Test Failover
# This creates a test VM in the target region without affecting production

# Actual failover
# Portal: Recovery Services Vault → Replicated Items → VM → Failover
# This activates the replica VM in the target region
```

### Real-World Example
```
Industry Example: E-commerce platform DR strategy

Primary: East US
DR: West US

Components:
1. VMs: Replicated via Azure Site Recovery (RPO: 5 min)
2. SQL Database: Active geo-replication (RPO: 5 sec)
3. Storage: RA-GRS (RPO: ~15 min)
4. DNS: Azure Traffic Manager (automatic failover)

DR Test: Quarterly (test failover without affecting production)
RTO: 30 minutes
RPO: 5 minutes
Annual DR cost: ~$2,000/month (replica VMs in standby)

Without DR: A regional outage could mean hours/days of downtime
            and potential data loss → millions in lost revenue
```

---

## 13.5 Database HA & DR

```bash
# Azure SQL: Active Geo-Replication
az sql db replica create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name db-ecommerce \
  --partner-server sql-server-westus \
  --partner-resource-group rg-dr-westus

# Meaning: Creates a readable replica in West US
# Automatic async replication, RPO ~5 seconds

# Failover to replica
az sql db replica set-primary \
  --resource-group rg-dr-westus \
  --server sql-server-westus \
  --name db-ecommerce

# Azure SQL: Auto-failover groups (automatic failover)
az sql failover-group create \
  --resource-group rg-demo-eastus \
  --server sql-server-demo-2024 \
  --name fg-ecommerce \
  --partner-server sql-server-westus \
  --partner-resource-group rg-dr-westus \
  --failover-policy Automatic \
  --grace-period 60

# Connection string uses failover group name:
# fg-ecommerce.database.windows.net (auto-routes to primary)
```

---

## 13.6 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Backup `UserErrorVmNotFound` | VM deleted or moved | Re-configure backup for the VM |
| `BackupOperationInProgress` | Another backup running | Wait for current backup to complete |
| ASR replication `Critical` | Network or storage issue | Check connectivity between regions |
| `FailoverFailed` | Target region capacity issue | Try different VM size or zone |
| `RPO exceeded` | Replication lag too high | Check network bandwidth; reduce data change rate |
| Geo-replication lag | High transaction volume | Monitor with `sys.dm_geo_replication_link_status` |

---

## 13.7 Practice Questions

### Question 1
**What is RPO?**
- A) Recovery Performance Objective
- B) Recovery Point Objective — maximum acceptable data loss ✅
- C) Recovery Process Outline
- D) Resource Provisioning Order

### Question 2
**Which service replicates VMs between Azure regions for disaster recovery?**
- A) Azure Backup
- B) Azure Site Recovery ✅
- C) Azure Traffic Manager
- D) Azure Load Balancer

### Question 3
**Azure Backup stores backups in:**
- A) Blob Storage
- B) Recovery Services Vault ✅
- C) Key Vault
- D) Log Analytics Workspace

### Question 4
**What SLA do VMs in Availability Zones provide?**
- A) 99.9%
- B) 99.95%
- C) 99.99% ✅
- D) 99.999%

### Question 5
**SQL Auto-failover groups provide:**
- A) Manual failover only
- B) Automatic failover with a grace period ✅
- C) Backup only, no failover
- D) Read-only access to primary

---

[← Previous Module](./Module-12-Advanced-Networking.md) | [Next Module: Cost Management →](./Module-14-Cost-Management.md)
