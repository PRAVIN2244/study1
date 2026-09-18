# Module 16: Governance & Compliance

## Certification Relevance: AZ-900 (30-35%), AZ-104

---

## 16.1 Azure Governance Overview

```
Governance = Rules and processes to manage Azure resources at scale

Why governance matters:
├── 500 developers creating resources → chaos without rules
├── Compliance requirements (HIPAA, PCI DSS, GDPR)
├── Cost control (prevent runaway spending)
├── Security standards (enforce encryption, network rules)
└── Consistency (naming conventions, tagging, regions)

Azure Governance Tools:
├── Management Groups    → Organize subscriptions
├── Azure Policy         → Enforce rules on resources
├── Azure Blueprints     → Package policies + templates
├── Resource Locks       → Prevent accidental deletion
├── RBAC                 → Control who can do what
└── Tags                 → Organize and track resources
```

---

## 16.2 Management Groups

### What are Management Groups?
Containers that help you manage access, policy, and compliance across multiple Azure subscriptions.

```
Root Management Group
├── IT Management Group
│   ├── Production Subscription
│   │   ├── rg-web-prod
│   │   └── rg-db-prod
│   └── Development Subscription
│       ├── rg-web-dev
│       └── rg-db-dev
├── Finance Management Group
│   └── Finance Subscription
│       └── rg-finance-app
└── Marketing Management Group
    └── Marketing Subscription
        └── rg-marketing-site

Key facts:
- 10,000 management groups per directory
- Up to 6 levels of depth (excluding root)
- Each group can have only ONE parent
- Each subscription can belong to only ONE management group
- Policies applied at MG level inherit to all subscriptions below
```

```bash
# Create a management group
az account management-group create \
  --name "mg-production" \
  --display-name "Production"

# Move a subscription into a management group
az account management-group subscription add \
  --name "mg-production" \
  --subscription "12345678-1234-1234-1234-123456789012"

# List management groups
az account management-group list --output table

# Apply policy at management group level
az policy assignment create \
  --name "require-tags" \
  --policy "require-tag-on-rg" \
  --scope "/providers/Microsoft.Management/managementGroups/mg-production"
# This policy applies to ALL subscriptions under mg-production
```

---

## 16.3 Azure Policy

### What is Azure Policy?
A service that creates, assigns, and manages policies to enforce rules on Azure resources. Policies evaluate resources and flag non-compliant ones.

### Policy Effects

```
Effect          Description                              Example
──────          ───────────                              ───────
Deny            Block the action                         Deny VMs without tags
Audit           Allow but log as non-compliant           Log unencrypted storage
AuditIfNotExists  Audit if related resource missing      Audit VMs without backup
DeployIfNotExists Auto-deploy if missing                 Auto-enable diagnostics
Modify          Add/update properties                    Add default tags
Append          Add fields to resource                   Add IP restrictions
Disabled        Policy exists but not enforced           Testing/disabled
```

### Common Built-in Policies

| Policy | Effect | Description |
|--------|--------|-------------|
| Allowed locations | Deny | Restrict which regions resources can be created in |
| Allowed VM SKUs | Deny | Restrict which VM sizes can be used |
| Require tag on resources | Deny | Resources must have specific tags |
| Inherit tag from RG | Modify | Auto-copy tags from resource group to resources |
| Storage HTTPS only | Deny | Storage accounts must use HTTPS |
| SQL TDE encryption | AuditIfNotExists | Audit SQL databases without encryption |
| Allowed storage SKUs | Deny | Restrict storage redundancy options |

### Portal UI Walkthrough: Assign an Azure Policy

```
PORTAL STEPS — Restrict Resources to Specific Regions:

Step 1: Navigate to Azure Policy
   → Search "Policy" in the search bar
   → Click "Policy" from results
   → You'll see the Policy dashboard with compliance overview

Step 2: Browse Policy Definitions
   → Left sidebar → "Definitions"
   → You'll see hundreds of built-in policies
   → Use the search bar: Type "Allowed locations"
   → Click "Allowed locations" from the list

Step 3: Assign the Policy
   → Click "Assign" at the top

Step 4: Configure the Assignment
   ┌─ Basics Tab ───────────────────────────────────────────┐
   │ Scope:              Click "..." to select               │
   │   → Select your Subscription                           │
   │   → (or a specific Resource Group)                     │
   │ Exclusions:         (optional — exclude specific RGs)   │
   │ Assignment name:    Restrict to East US and West US     │
   │ Policy enforcement: ● Enabled                           │
   └────────────────────────────────────────────────────────┘

Step 5: Configure Parameters
   → Click "Next: Parameters >"
   ┌─────────────────────────────────────────────────────────┐
   │ Allowed locations:                                       │
   │   ☑ East US                                              │
   │   ☑ West US                                              │
   │   ☑ East US 2                                            │
   │   ☐ West Europe (not selected — blocked)                │
   │   ☐ Southeast Asia (not selected — blocked)             │
   └─────────────────────────────────────────────────────────┘

Step 6: Review + Create
   → Click "Review + create" → "Create"

Step 7: Test the Policy
   → Try creating a resource in a blocked region:
     → Create a Storage Account → Region: "West Europe"
     → Click "Review + create"
     → ❌ ERROR: "Resource 'xxx' was disallowed by policy"
   → Try creating in an allowed region:
     → Region: "East US"
     → ✅ Succeeds!

Step 8: Check Compliance
   → Go to Policy → Left sidebar → "Compliance"
   → You'll see compliance percentage:
     ┌─────────────────────────────────────────────────────┐
     │ Policy: Restrict to East US and West US             │
     │ Compliance: 85% (17 of 20 resources compliant)     │
     │ Non-compliant: 3 resources in other regions         │
     │   (existing resources — policy doesn't delete them) │
     └─────────────────────────────────────────────────────┘
   → Click the policy to see which resources are non-compliant
```

### Portal UI Walkthrough: Add a Resource Lock

```
PORTAL STEPS — Prevent Accidental Deletion of a Resource Group:

Step 1: Go to Your Resource Group
   → Resource groups → Click "rg-demo-eastus"

Step 2: Open Locks
   → Left sidebar → "Locks"
   → Click "+ Add"

Step 3: Configure the Lock
   ┌─────────────────────────────────────────────────────────┐
   │ Lock name:          prevent-delete                       │
   │ Lock type:          ● Delete  ○ Read-only                │
   │   Delete = can modify but cannot delete                 │
   │   Read-only = cannot modify or delete                   │
   │ Notes:              Production resources - do not delete │
   │ Click "OK"                                               │
   └─────────────────────────────────────────────────────────┘

Step 4: Test the Lock
   → Try deleting the resource group:
     → Click "Delete resource group"
     → Type the name → Click "Delete"
     → ❌ ERROR: "Cannot delete because of lock 'prevent-delete'"
   → Try deleting a resource inside the group:
     → Go to any resource → Click "Delete"
     → ❌ Same error — lock is inherited by all resources

Step 5: Remove the Lock (When Needed)
   → Go to Resource group → "Locks"
   → Click the trash icon next to the lock
   → Click "OK" to confirm
   → ⚠️ Only Owner or User Access Administrator can remove locks
```

### Portal UI Walkthrough: Create an Azure Blueprint

```
PORTAL STEPS — Create a Blueprint for Standardized Environments:

Step 1: Navigate to Blueprints
   → Search "Blueprints" in the search bar
   → Click "Blueprints" from results

Step 2: Create a Blueprint Definition
   → Click "Create"
   → Blueprint name: bp-production-environment
   → Description: Standard production environment setup
   → Definition location: Select your Management Group or Subscription
   → Click "Next: Artifacts >"

Step 3: Add Artifacts
   → Click "+ Add artifact" and add each:

   Artifact 1: Resource Group
   → Type: Resource Group
   → Name: rg-web
   → Location: East US

   Artifact 2: Policy Assignment
   → Type: Policy Assignment
   → Policy: "Allowed locations"
   → Parameters: East US, West US

   Artifact 3: Role Assignment
   → Type: Role Assignment
   → Role: Contributor
   → Assign to: DevOps team group

   Artifact 4: ARM Template
   → Type: ARM Template
   → Paste your VNet + NSG template

Step 4: Save Draft
   → Click "Save Draft"

Step 5: Publish the Blueprint
   → Click the blueprint → "Publish blueprint"
   → Version: 1.0
   → Click "Publish"

Step 6: Assign the Blueprint
   → Click "Assign blueprint"
   → Select subscription to apply it to
   → Fill in parameters
   → Click "Assign"
   → All artifacts deploy automatically to the subscription
```

### Creating and Assigning Policies with CLI

```bash
# List built-in policy definitions
az policy definition list \
  --query "[?policyType=='BuiltIn'].{Name:displayName, Category:metadata.category}" \
  --output table | head -20

# Assign a built-in policy: "Allowed locations"
az policy assignment create \
  --name "allowed-locations" \
  --display-name "Restrict to East US and West US" \
  --policy "e56962a6-4747-49cd-b67b-bf8b01975c4c" \
  --scope "/subscriptions/SUB_ID" \
  --params '{"listOfAllowedLocations": {"value": ["eastus", "westus", "eastus2"]}}'

# Meaning: Resources can ONLY be created in East US, West US, or East US 2
# Any attempt to create in another region → DENIED

# Assign policy: "Require tag on resource groups"
az policy assignment create \
  --name "require-env-tag" \
  --display-name "Require Environment tag on RGs" \
  --policy "96670d01-0a4d-4649-9c89-2d3abc0a5025" \
  --scope "/subscriptions/SUB_ID" \
  --params '{"tagName": {"value": "Environment"}}'

# Test: Try creating RG without tag
az group create --name rg-test --location eastus
# Output: ERROR - Resource 'rg-test' was disallowed by policy

# Test: Create RG with required tag
az group create --name rg-test --location eastus --tags Environment=Dev
# Output: Succeeded

# Check compliance
az policy state list \
  --query "[?complianceState=='NonCompliant'].{Resource:resourceId, Policy:policyAssignmentName}" \
  --output table

# Create a custom policy definition
az policy definition create \
  --name "deny-public-ip" \
  --display-name "Deny Public IP creation" \
  --description "Prevents creation of public IP addresses" \
  --rules '{
    "if": {
      "field": "type",
      "equals": "Microsoft.Network/publicIPAddresses"
    },
    "then": {
      "effect": "deny"
    }
  }' \
  --mode All

# Assign the custom policy
az policy assignment create \
  --name "no-public-ips" \
  --policy "deny-public-ip" \
  --scope "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus"
```

### Policy Initiatives (Policy Sets)

```bash
# An initiative is a GROUP of policies applied together

# Example: "Security Baseline" initiative includes:
# - Require HTTPS on storage
# - Require encryption on SQL
# - Deny public IPs
# - Require NSG on subnets
# - Audit VMs without backup

# Assign a built-in initiative
az policy assignment create \
  --name "security-baseline" \
  --display-name "Security Baseline" \
  --policy-set-definition "1f3afdf9-d0c9-4c3d-847f-89da613e70a8" \
  --scope "/subscriptions/SUB_ID"
```

---

## 16.4 Resource Locks

### What are Resource Locks?
Prevent accidental deletion or modification of Azure resources.

```
Lock Types:
├── CanNotDelete (Delete lock)
│   - Can read and modify the resource
│   - CANNOT delete the resource
│   - Use for: Production databases, critical VMs
│
└── ReadOnly (Read-only lock)
    - Can ONLY read the resource
    - CANNOT modify or delete
    - Use for: Compliance resources, audit logs
    - ⚠️ Can break things (e.g., can't scale a VM)
```

```bash
# Create a Delete lock on a resource group
az lock create \
  --name "prevent-delete" \
  --lock-type CanNotDelete \
  --resource-group rg-prod-eastus \
  --notes "Production resources - do not delete"

# Create a ReadOnly lock on a storage account
az lock create \
  --name "readonly-lock" \
  --lock-type ReadOnly \
  --resource-group rg-prod-eastus \
  --resource-name stprodeastus2024 \
  --resource-type Microsoft.Storage/storageAccounts

# List locks
az lock list --resource-group rg-prod-eastus --output table
# Output:
# Name             Level          Notes
# ---------------  -------------  ----------------------------------
# prevent-delete   CanNotDelete   Production resources - do not delete

# Try to delete locked resource group
az group delete --name rg-prod-eastus --yes
# Output: ERROR - The scope 'rg-prod-eastus' cannot perform delete operation
#         because following scope(s) are locked: prevent-delete

# Remove a lock (requires Owner or User Access Administrator role)
az lock delete \
  --name "prevent-delete" \
  --resource-group rg-prod-eastus
```

### Lock Inheritance
```
Locks are inherited from parent scopes:

Subscription lock → applies to ALL resource groups and resources
Resource Group lock → applies to ALL resources in the group
Resource lock → applies to that specific resource only

Even Owners cannot delete a locked resource without first removing the lock.
```

---

## 16.5 Azure Blueprints

### What are Blueprints?
A package that combines ARM templates, policies, RBAC assignments, and resource groups into a single deployable definition. Used to set up new subscriptions/environments consistently.

```
Blueprint contains:
├── Resource Groups (create standard RGs)
├── ARM Templates (deploy standard resources)
├── Policy Assignments (enforce rules)
├── Role Assignments (set up access)
└── Version control (track changes)

Real-World Example: "Production Environment Blueprint"
├── Creates: rg-web, rg-app, rg-db, rg-monitoring
├── Deploys: VNet, NSGs, Log Analytics workspace
├── Assigns: "Allowed locations" policy (East US only)
├── Assigns: "Require tags" policy
├── Assigns: Contributor role to DevOps team
└── Assigns: Reader role to audit team

Result: Every new production subscription is identical and compliant
```

---

## 16.6 Microsoft Purview (Compliance)

```
Compliance offerings Azure supports:
├── HIPAA (Healthcare)
├── PCI DSS (Payment cards)
├── SOC 1, 2, 3 (Service organization controls)
├── ISO 27001 (Information security)
├── GDPR (EU data protection)
├── FedRAMP (US government)
├── NIST (Cybersecurity framework)
└── 90+ compliance certifications

Microsoft Purview Compliance Manager:
- Dashboard showing compliance score
- Pre-built assessments for common standards
- Recommended actions to improve compliance
- Evidence collection and documentation

Access: Portal → Microsoft Purview → Compliance Manager
```

---

## 16.7 Azure Arc

```
Azure Arc extends Azure management to:
├── On-premises servers (Windows/Linux)
├── Kubernetes clusters (anywhere)
├── SQL Server instances (on-premises)
└── VMware/SCVMM virtual machines

Benefits:
- Manage on-premises resources from Azure Portal
- Apply Azure Policy to on-premises servers
- Use Azure Monitor for on-premises monitoring
- Consistent management across hybrid environments

Example: A company has 100 on-premises Linux servers.
With Azure Arc, they can:
1. See all servers in Azure Portal
2. Apply security policies uniformly
3. Monitor with Azure Monitor
4. Deploy updates with Azure Update Manager
```

---

## 16.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `RequestDisallowedByPolicy` | Azure Policy blocking action | Check which policy: `az policy assignment list` |
| `ScopeLocked` | Resource lock preventing action | Remove lock, perform action, re-apply lock |
| `PolicyAssignmentNotFound` | Wrong policy ID or scope | Verify policy definition ID and scope |
| Non-compliant resources | Existing resources don't meet new policy | Remediate: Portal → Policy → Remediation |
| Blueprint deployment failed | Template error in blueprint | Check ARM template within blueprint for errors |
| Management group depth exceeded | More than 6 levels | Restructure hierarchy |

### Policy Troubleshooting

```bash
# Find which policy is blocking you
az policy assignment list \
  --scope "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus" \
  --output table

# Check compliance state
az policy state summarize \
  --resource-group rg-demo-eastus

# Trigger policy evaluation (normally runs every 24 hours)
az policy state trigger-scan \
  --resource-group rg-demo-eastus

# View non-compliant resources
az policy state list \
  --filter "complianceState eq 'NonCompliant'" \
  --output table
```

---

## 16.9 Practice Questions

### Question 1
**Which Azure Policy effect blocks resource creation?**
- A) Audit
- B) Deny ✅
- C) Append
- D) Disabled

### Question 2
**Resource locks are inherited from parent scopes. True or False?**
- A) True ✅
- B) False

### Question 3
**What is the maximum depth of management group hierarchy (excluding root)?**
- A) 3
- B) 6 ✅
- C) 10
- D) Unlimited

### Question 4
**Which lock type allows modifications but prevents deletion?**
- A) ReadOnly
- B) CanNotDelete ✅
- C) DoNotModify
- D) PreventDelete

### Question 5
**Azure Blueprints can include which of the following? (Select all that apply)**
- A) ARM Templates ✅
- B) Policy Assignments ✅
- C) Role Assignments ✅
- D) Resource Groups ✅
- E) All of the above ✅

---

[← Previous Module](./Module-15-Infrastructure-as-Code.md) | [Next Module: Real-World Projects →](./Module-17-Real-World-Projects.md)
