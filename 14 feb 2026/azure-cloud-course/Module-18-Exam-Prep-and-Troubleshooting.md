# Module 18: Exam Prep, Common Errors & Troubleshooting

---

## 18.1 Certification Exam Overview

### AZ-900: Azure Fundamentals
```
Duration: 45 minutes
Questions: 40-60
Passing score: 700/1000
Cost: $99 USD
Format: Multiple choice, drag-and-drop, case studies

Domains:
├── Cloud Concepts (25-30%)
│   ├── Cloud models (IaaS, PaaS, SaaS)
│   ├── Benefits of cloud (HA, scalability, elasticity)
│   └── Cloud types (public, private, hybrid)
├── Azure Architecture & Services (35-40%)
│   ├── Core components (regions, zones, resource groups)
│   ├── Compute, networking, storage services
│   └── Azure solutions (IoT, AI, DevOps)
├── Management & Governance (30-35%)
│   ├── Cost management
│   ├── Governance (Policy, Locks, Blueprints)
│   └── Monitoring tools
└── Study time: 2-4 weeks
```

### AZ-104: Azure Administrator
```
Duration: 100 minutes
Questions: 40-60
Passing score: 700/1000
Cost: $165 USD
Format: Multiple choice, case studies, labs (hands-on)

Domains:
├── Manage Azure Identities & Governance (20-25%)
│   ├── Entra ID users, groups
│   ├── RBAC
│   ├── Subscriptions and governance
│   └── Azure Policy
├── Implement & Manage Storage (15-20%)
│   ├── Storage accounts
│   ├── Blob storage, Azure Files
│   ├── Storage security
│   └── Azure File Sync
├── Deploy & Manage Compute (20-25%)
│   ├── VMs, VMSS, availability
│   ├── App Service
│   ├── Containers (ACI, AKS)
│   └── Azure Functions
├── Implement & Manage Virtual Networking (15-20%)
│   ├── VNets, subnets, NSGs
│   ├── VPN, ExpressRoute
│   ├── Load balancing
│   └── DNS, Private Endpoints
├── Monitor & Maintain Azure Resources (10-15%)
│   ├── Azure Monitor, Log Analytics
│   ├── Alerts
│   ├── Backup and recovery
│   └── Azure Advisor
└── Study time: 6-10 weeks (with hands-on practice)
```

### AZ-204: Developing Solutions for Azure
```
Duration: 100 minutes
Questions: 40-60
Passing score: 700/1000
Cost: $165 USD

Domains:
├── Develop Azure Compute Solutions (25-30%)
│   ├── VMs, containers
│   ├── App Service
│   └── Azure Functions
├── Develop for Azure Storage (15-20%)
│   ├── Cosmos DB
│   ├── Blob Storage
│   └── Caching (Redis)
├── Implement Azure Security (20-25%)
│   ├── Authentication (Entra ID, MSAL)
│   ├── Managed Identities
│   └── Key Vault
├── Monitor, Troubleshoot & Optimize (15-20%)
│   ├── Application Insights
│   ├── Caching strategies
│   └── CDN
├── Connect to & Consume Azure Services (15-20%)
│   ├── API Management
│   ├── Event Grid, Service Bus
│   └── Logic Apps
└── Study time: 8-12 weeks (requires coding experience)
```

---

## 18.2 Exam Tips & Strategies

### General Tips
```
1. Read the ENTIRE question before looking at answers
2. Look for keywords: "MOST cost-effective", "MINIMUM effort", "BEST"
3. Eliminate obviously wrong answers first
4. "All of the above" is often correct when multiple answers seem right
5. Time management: ~1.5 minutes per question
6. Flag difficult questions and return to them
7. Don't change answers unless you're certain
8. Case studies: Read questions FIRST, then scan the case study
```

### Common Exam Traps

```
Trap 1: "Which is the CHEAPEST option?"
- They often list a technically correct but expensive option
- Look for: Consumption plan, Basic tier, LRS storage, B-series VMs

Trap 2: "Which provides the HIGHEST availability?"
- Availability Zones > Availability Sets > Single VM
- Multi-region > Single region
- 99.99% > 99.95% > 99.9%

Trap 3: "Tags are inherited from resource groups"
- FALSE. Tags are NOT inherited. This is a common trick question.

Trap 4: "stop vs deallocate"
- az vm stop = OS shutdown, STILL BILLED for compute
- az vm deallocate = releases compute, NOT billed
- Exam loves this distinction

Trap 5: "Which is a Platform as a Service?"
- Azure SQL Database = PaaS ✅
- SQL Server on Azure VM = IaaS ❌
- Azure App Service = PaaS ✅
- Azure Virtual Machine = IaaS ❌

Trap 6: "Peering is transitive"
- FALSE. VNet peering is NOT transitive.
- A↔B and B↔C does NOT mean A↔C

Trap 7: "NSG vs Azure Firewall"
- NSG = Layer 3/4, free, subnet/NIC level
- Azure Firewall = Layer 3/4/7, paid, VNet level, FQDN filtering
```

---

## 18.3 Quick Reference Cheat Sheet

### Service Comparison

```
COMPUTE:
VM              = IaaS, full control, you manage OS
App Service     = PaaS, managed hosting, you manage code
Functions       = Serverless, event-driven, pay per execution
ACI             = Container, no orchestration, quick start
AKS             = Container orchestration, managed Kubernetes

STORAGE:
Blob            = Unstructured (files, images, videos)
Files           = SMB/NFS file shares
Queue           = Message queuing
Table           = NoSQL key-value
Disk            = VM disks (managed)

DATABASE:
Azure SQL       = Managed SQL Server (PaaS)
SQL MI          = Near-100% SQL Server compatibility
Cosmos DB       = Global NoSQL, multi-model
MySQL/PostgreSQL = Managed open-source databases
Redis           = In-memory cache

NETWORKING:
VNet            = Virtual network (isolated)
NSG             = Firewall rules (L3/L4)
Load Balancer   = L4 load balancing
App Gateway     = L7 load balancing + WAF
VPN Gateway     = Encrypted tunnel over internet
ExpressRoute    = Private dedicated connection
Azure Firewall  = Managed firewall (L3/L4/L7)
Front Door      = Global load balancer + CDN + WAF
Traffic Manager = DNS-based routing
Bastion         = Secure RDP/SSH without public IP

IDENTITY:
Entra ID        = Cloud identity service
RBAC            = Role-based access control
MFA             = Multi-factor authentication
Key Vault       = Secret/key/certificate management
Managed Identity = Azure-managed service identity

MONITORING:
Azure Monitor   = Metrics and logs platform
Log Analytics   = Log storage and KQL queries
App Insights    = Application performance monitoring
Alerts          = Notifications on conditions
Advisor         = Recommendations (cost, security, perf)

GOVERNANCE:
Policy          = Enforce rules on resources
Blueprints      = Package policies + templates
Locks           = Prevent deletion/modification
Management Groups = Organize subscriptions
Tags            = Metadata for organization
```

### Key Numbers to Remember

```
Availability:
Single VM (Premium SSD):     99.9%   (43.8 min/month downtime)
Availability Set:            99.95%  (21.9 min/month)
Availability Zones:          99.99%  (4.38 min/month)
Cosmos DB:                   99.999% (26.3 sec/month)

Limits:
Azure AD objects per tenant:  50,000 (free) / unlimited (P1/P2)
Subscriptions per tenant:     Unlimited
Resource groups per sub:      980
Resources per resource group: 800 (per resource type)
Tags per resource:            50
Tag name length:              512 characters
Tag value length:             256 characters
VNets per subscription:       1,000
Subnets per VNet:             3,000
NSG rules per NSG:            1,000
Management group depth:       6 levels (excluding root)

Storage:
Storage account name:         3-24 chars, lowercase + numbers only
Blob max size (block):        190.7 TB
File share max size:          100 TB
Queue message max:            64 KB
Table entity max:             1 MB

Networking:
Azure reserves per subnet:    5 IPs
VNet peering:                 NOT transitive
GatewaySubnet minimum:        /29 (recommended /27)
AzureBastionSubnet minimum:   /26
AzureFirewallSubnet minimum:  /26
```

---

## 18.4 Master Troubleshooting Guide

### VM Troubleshooting

```bash
# VM won't start
az vm get-instance-view --resource-group rg --name vm \
  --query instanceView.statuses

# Check boot diagnostics
az vm boot-diagnostics get-boot-log --resource-group rg --name vm

# Can't SSH/RDP to VM
# 1. Check VM is running
az vm show --resource-group rg --name vm --query powerState

# 2. Check NSG rules
az network nsg rule list --resource-group rg --nsg-name nsg --output table

# 3. Check if port is open
az network watcher test-ip-flow --vm vm --direction Inbound \
  --protocol Tcp --local 10.0.1.4:22 --remote 0.0.0.0:0

# 4. Check route table
az network nic show-effective-route-table --resource-group rg --name vmNic

# VM performance issues
# 1. Check CPU
az monitor metrics list --resource VM_RESOURCE_ID \
  --metric "Percentage CPU" --interval PT1H --aggregation Average

# 2. Check disk IOPS
az monitor metrics list --resource VM_RESOURCE_ID \
  --metric "Disk Read Operations/Sec" --interval PT1H

# 3. Check memory (requires VM agent)
az vm run-command invoke --resource-group rg --name vm \
  --command-id RunShellScript --scripts "free -m"
```

### Networking Troubleshooting

```bash
# VMs can't communicate
# 1. Same VNet? Check subnets
az network vnet subnet list --resource-group rg --vnet-name vnet --output table

# 2. Check NSG (both subnet and NIC level)
az network nic list-effective-nsg --resource-group rg --name vmNic

# 3. Check effective routes
az network nic show-effective-route-table --resource-group rg --name vmNic

# DNS resolution failing
# 1. Check DNS settings on VNet
az network vnet show --resource-group rg --name vnet --query dhcpOptions

# 2. Test DNS from VM
az vm run-command invoke --resource-group rg --name vm \
  --command-id RunShellScript --scripts "nslookup myapp.azurewebsites.net"

# VPN not connecting
# 1. Check connection status
az network vpn-connection show --resource-group rg --name conn \
  --query connectionStatus

# 2. Verify shared key matches
az network vpn-connection shared-key show --resource-group rg --name conn

# 3. Check gateway status
az network vnet-gateway show --resource-group rg --name gw \
  --query provisioningState
```

### Storage Troubleshooting

```bash
# Can't access storage
# 1. Check firewall rules
az storage account show --name staccount --query networkRuleSet

# 2. Check if public access is enabled
az storage account show --name staccount --query publicNetworkAccess

# 3. Verify access key
az storage account keys list --account-name staccount --output table

# 4. Check SAS token expiry
# Decode the SAS token and check 'se' (expiry) parameter

# Blob upload failing
# 1. Check container exists
az storage container list --account-name staccount --output table

# 2. Check container access level
az storage container show --name container --account-name staccount \
  --query publicAccess

# 3. Check storage account capacity
az storage account show --name staccount --query "primaryEndpoints"
```

### Database Troubleshooting

```bash
# Can't connect to Azure SQL
# 1. Check firewall rules
az sql server firewall-rule list --resource-group rg --server sqlserver --output table

# 2. Check if Azure services are allowed
az sql server firewall-rule show --resource-group rg --server sqlserver \
  --name AllowAllWindowsAzureIps 2>/dev/null && echo "Allowed" || echo "Not allowed"

# 3. Test connectivity
az sql db show --resource-group rg --server sqlserver --name db \
  --query status

# Cosmos DB 429 errors (throttled)
# 1. Check current throughput
az cosmosdb sql container throughput show --resource-group rg \
  --account-name cosmos --database-name db --name container

# 2. Increase throughput
az cosmosdb sql container throughput update --resource-group rg \
  --account-name cosmos --database-name db --name container \
  --throughput 1000

# 3. Enable autoscale
az cosmosdb sql container throughput migrate --resource-group rg \
  --account-name cosmos --database-name db --name container \
  --throughput-type autoscale
```

### Identity & Access Troubleshooting

```bash
# AuthorizationFailed
# 1. Check user's role assignments
az role assignment list --assignee user@domain.com --output table

# 2. Check effective permissions at scope
az role assignment list --scope "/subscriptions/SUB_ID/resourceGroups/rg" --output table

# 3. Check if Azure Policy is blocking
az policy state list --filter "complianceState eq 'NonCompliant'" \
  --resource-group rg --output table

# Key Vault access denied
# 1. Check access policies
az keyvault show --name kv --query accessPolicies

# 2. Check if RBAC is enabled
az keyvault show --name kv --query enableRbacAuthorization

# 3. Check network rules
az keyvault show --name kv --query networkAcls
```

---

## 18.5 Common Error Codes Reference

| HTTP Code | Azure Error | Meaning | Action |
|-----------|-------------|---------|--------|
| 400 | BadRequest | Invalid request parameters | Check request body/parameters |
| 401 | Unauthorized | Authentication failed | Re-authenticate: `az login` |
| 403 | Forbidden | Insufficient permissions | Check RBAC roles and policies |
| 404 | NotFound | Resource doesn't exist | Verify resource name and group |
| 409 | Conflict | Resource already exists | Use different name or update existing |
| 429 | TooManyRequests | Rate limited/throttled | Retry with backoff; increase capacity |
| 500 | InternalServerError | Azure service error | Retry; check Azure Status page |
| 502 | BadGateway | Backend service unavailable | Check backend health; retry |
| 503 | ServiceUnavailable | Service temporarily unavailable | Retry with exponential backoff |

---

## 18.6 Study Plan

### AZ-900 (2-4 Weeks)

```
Week 1:
├── Module 01: Cloud Concepts (Day 1-2)
├── Module 02: Portal, CLI, PowerShell (Day 3-4)
└── Module 14: Cost Management (Day 5)

Week 2:
├── Module 03: Compute overview (Day 1)
├── Module 04: Networking overview (Day 2)
├── Module 05: Storage overview (Day 3)
├── Module 07: Identity & Security (Day 4)
└── Module 16: Governance (Day 5)

Week 3:
├── Review all modules (Day 1-2)
├── Practice exams (Day 3-4)
└── Final review of weak areas (Day 5)

Resources:
- Microsoft Learn: AZ-900 learning path (free)
- This course: Modules 01, 02, 07, 14, 16
- Practice exams: Microsoft official practice test
```

### AZ-104 (6-10 Weeks)

```
Weeks 1-2: Identity & Governance
├── Module 07: Entra ID, RBAC, Key Vault
├── Module 16: Policy, Locks, Management Groups
└── Hands-on: Create users, assign roles, create policies

Weeks 3-4: Compute & Networking
├── Module 03: VMs, VMSS, App Service
├── Module 04: VNet, NSG, Load Balancer
├── Module 12: VPN, ExpressRoute, Firewall
└── Hands-on: Deploy VMs, configure networking, set up VPN

Weeks 5-6: Storage & Databases
├── Module 05: Blob, Files, Queue, Table
├── Module 06: SQL, Cosmos DB
└── Hands-on: Create storage, configure security, manage databases

Weeks 7-8: Monitoring & Backup
├── Module 08: Monitor, Log Analytics, Alerts
├── Module 13: Backup, Site Recovery
└── Hands-on: Set up monitoring, create alerts, configure backup

Weeks 9-10: Review & Practice
├── Module 17: Real-world projects
├── Practice exams (aim for 80%+ before real exam)
└── Review weak areas

⚠️ AZ-104 may include hands-on labs in the exam.
Practice CLI commands and Portal navigation extensively.
```

### AZ-204 (8-12 Weeks)

```
Weeks 1-3: Compute Solutions
├── Module 03: App Service, deployment slots
├── Module 10: Containers, AKS, ACR
├── Module 11: Azure Functions
└── Hands-on: Deploy apps, create functions, run containers

Weeks 4-5: Storage & Data
├── Module 05: Blob Storage, SAS tokens
├── Module 06: Cosmos DB, Redis Cache
└── Hands-on: CRUD operations with SDKs

Weeks 6-7: Security
├── Module 07: Entra ID, Managed Identities, Key Vault
├── Implement authentication in code (MSAL)
└── Hands-on: Secure apps with Entra ID, use Key Vault in code

Weeks 8-9: Integration & Messaging
├── Module 09: DevOps, CI/CD
├── Module 11: Event Grid, Service Bus, Logic Apps
└── Hands-on: Build pipelines, create event-driven architectures

Weeks 10-12: Review & Practice
├── Module 17: Real-world projects
├── Practice exams
└── Code-along exercises with Azure SDKs
```

---

## 18.7 Final Practice Exam (30 Questions)

### Questions

**1.** Which cloud model provides the LEAST management overhead?
- A) IaaS  B) PaaS  C) SaaS ✅  D) On-premises

**2.** A company needs to run a legacy Windows application that requires specific OS configurations. Which service?
- A) App Service  B) Azure Functions  C) Azure VM ✅  D) ACI

**3.** Which storage redundancy replicates data to a paired region AND allows read access from the secondary?
- A) LRS  B) GRS  C) RA-GRS ✅  D) ZRS

**4.** What is the Azure CLI command to create a resource group?
- A) `az rg create`  B) `az group create` ✅  C) `az resource-group new`  D) `az create group`

**5.** Which service provides DNS-based traffic routing across regions?
- A) Load Balancer  B) Application Gateway  C) Traffic Manager ✅  D) Front Door

**6.** Tags applied to a resource group are automatically inherited by resources. True or False?
- A) True  B) False ✅

**7.** Which Cosmos DB consistency level is the default?
- A) Strong  B) Session ✅  C) Eventual  D) Bounded Staleness

**8.** What is the minimum subnet size for Azure Bastion?
- A) /28  B) /27  C) /26 ✅  D) /24

**9.** Which RBAC role can manage resources but CANNOT assign roles?
- A) Owner  B) Contributor ✅  C) Reader  D) User Access Admin

**10.** Azure Policy effect that blocks non-compliant resource creation:
- A) Audit  B) Deny ✅  C) Append  D) Modify

**11.** Which service auto-scales from zero and charges per execution?
- A) App Service  B) Azure Functions (Consumption) ✅  C) AKS  D) VM Scale Sets

**12.** VNet peering is transitive. True or False?
- A) True  B) False ✅

**13.** Which tool provides cost, security, and performance recommendations?
- A) Azure Monitor  B) Azure Advisor ✅  C) Azure Policy  D) Defender for Cloud

**14.** What does `az vm deallocate` do differently from `az vm stop`?
- A) Nothing, they're the same
- B) Deallocate releases compute resources and stops billing ✅
- C) Deallocate deletes the VM
- D) Stop releases compute resources

**15.** Which deployment mode DELETES resources not in the ARM template?
- A) Incremental  B) Complete ✅  C) Validate  D) What-If

**16.** How many IPs does Azure reserve per subnet?
- A) 3  B) 5 ✅  C) 8  D) 10

**17.** Which service provides a private, dedicated connection (not over internet)?
- A) VPN Gateway  B) ExpressRoute ✅  C) Azure Firewall  D) Bastion

**18.** What is the maximum management group hierarchy depth (excluding root)?
- A) 3  B) 6 ✅  C) 10  D) Unlimited

**19.** Which lock type prevents deletion but allows modification?
- A) ReadOnly  B) CanNotDelete ✅  C) NoDelete  D) PreventDelete

**20.** Managed Identities eliminate the need to manage:
- A) Resource groups  B) Credentials/secrets ✅  C) Subscriptions  D) Tags

**21.** Which Azure SQL purchasing model auto-pauses when idle?
- A) DTU  B) vCore  C) Serverless ✅  D) Elastic Pool

**22.** What query language does Log Analytics use?
- A) SQL  B) KQL ✅  C) GraphQL  D) LINQ

**23.** Which Kubernetes resource type creates an Azure Load Balancer?
- A) Deployment  B) Pod  C) Service (LoadBalancer) ✅  D) ConfigMap

**24.** Data transfer INTO Azure is:
- A) Free ✅  B) $0.05/GB  C) $0.087/GB  D) Varies by region

**25.** Which IaC tool works with multiple cloud providers?
- A) ARM Templates  B) Bicep  C) Terraform ✅  D) Azure PowerShell

**26.** What is RPO?
- A) Recovery Performance Objective
- B) Recovery Point Objective (max data loss) ✅
- C) Resource Provisioning Order
- D) Regional Pairing Option

**27.** Which messaging service supports Topics and Subscriptions (pub/sub)?
- A) Queue Storage  B) Service Bus ✅  C) Event Grid  D) Event Hub

**28.** Storage account names must be:
- A) Unique within resource group
- B) Unique within subscription
- C) Globally unique ✅
- D) Unique within region

**29.** Which Azure Firewall feature is NOT available in NSGs?
- A) Port filtering  B) IP filtering  C) FQDN filtering ✅  D) Protocol filtering

**30.** A single VM with Premium SSD has what SLA?
- A) 99%  B) 99.9% ✅  C) 99.95%  D) 99.99%

---

### Scoring
```
27-30 correct: Ready for the exam
22-26 correct: Almost ready, review weak areas
17-21 correct: Need more study, focus on missed topics
Below 17:      Review all modules thoroughly
```

---

## 18.8 Additional Resources

```
Official Microsoft Resources:
├── Microsoft Learn: https://learn.microsoft.com/training/azure/
├── Azure Documentation: https://learn.microsoft.com/azure/
├── Azure Architecture Center: https://learn.microsoft.com/azure/architecture/
├── Azure CLI Reference: https://learn.microsoft.com/cli/azure/
└── Practice Assessments: https://learn.microsoft.com/certifications/practice-assessments-for-microsoft-certifications

Hands-On Practice:
├── Azure Free Account: https://azure.microsoft.com/free/
├── Microsoft Learn Sandbox (free, no credit card)
├── Azure Pricing Calculator: https://azure.microsoft.com/pricing/calculator/
└── Azure Speed Test: https://azurespeedtest.azurewebsites.net/

Community:
├── Microsoft Q&A: https://learn.microsoft.com/answers/
├── Stack Overflow: azure tag
├── Reddit: r/azure
└── Azure Updates: https://azure.microsoft.com/updates/
```

---

**Congratulations on completing the Azure Cloud Course!**

Go back to [Course Home](./README.md) to review any module.

---

[← Previous Module](./Module-17-Real-World-Projects.md) | [Course Home →](./README.md)
