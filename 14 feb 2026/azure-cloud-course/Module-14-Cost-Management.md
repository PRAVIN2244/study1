# Module 14: Cost Management & Optimization

## Certification Relevance: AZ-900 (20-25%), AZ-104

---

## 14.1 Azure Pricing Models

```
1. Pay-As-You-Go (PAYG):
   - No upfront commitment
   - Pay per hour/second of usage
   - Most flexible, most expensive per unit
   - Best for: Dev/test, unpredictable workloads

2. Reserved Instances (RI):
   - 1-year or 3-year commitment
   - Up to 72% savings vs PAYG
   - Best for: Predictable, steady-state workloads
   - Example: D4s_v5 VM
     PAYG: ~$140/month
     1-year RI: ~$90/month (36% savings)
     3-year RI: ~$56/month (60% savings)

3. Spot VMs:
   - Use unused Azure capacity at deep discounts
   - Up to 90% savings
   - Can be evicted with 30-second notice
   - Best for: Batch processing, CI/CD, fault-tolerant workloads
   - NOT for: Production, databases, stateful apps

4. Azure Hybrid Benefit:
   - Use existing Windows Server or SQL Server licenses
   - Up to 40% savings on VMs
   - Up to 55% savings on Azure SQL
   - Requires Software Assurance

5. Dev/Test Pricing:
   - Discounted rates for dev/test workloads
   - No Windows license charges on VMs
   - Reduced rates on some PaaS services
   - Requires Visual Studio subscription
```

---

## 14.2 Azure Cost Management

```bash
# View current costs
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output table

# View cost by resource group
az cost query \
  --type ActualCost \
  --timeframe MonthToDate \
  --dataset-grouping name=ResourceGroup type=Dimension

# Create a budget
az consumption budget create \
  --budget-name "monthly-budget" \
  --amount 1000 \
  --category Cost \
  --time-grain Monthly \
  --start-date 2024-01-01 \
  --end-date 2024-12-31

# Budget alerts are configured in Portal:
# Cost Management → Budgets → Create
# Set thresholds: 50%, 75%, 90%, 100%
# Action: Email notification to finance team
```

### Portal UI Walkthrough: Analyze Costs and Create a Budget

```
PORTAL STEPS — View and Analyze Your Azure Costs:

Step 1: Navigate to Cost Management
   → Search "Cost Management" in the search bar
   → Click "Cost Management" from results

Step 2: Cost Analysis
   → Left sidebar → "Cost analysis"
   → You'll see a chart of your spending
   ┌─ Cost Analysis View ───────────────────────────────────┐
   │ Scope:       Your subscription                          │
   │ View:        Accumulated costs (default)                │
   │ Date range:  This month (change to custom range)        │
   │                                                         │
   │ Group by options (dropdown):                            │
   │   • Service name — see cost per Azure service           │
   │   • Resource group — see cost per resource group        │
   │   • Resource — see cost per individual resource         │
   │   • Tag — see cost by tag (e.g., Environment=Prod)     │
   │   • Location — see cost by region                       │
   │                                                         │
   │ Chart types: Area, Bar, Column, Table, Donut            │
   └────────────────────────────────────────────────────────┘
   → Click "Group by" → "Resource" to see which resources
     cost the most
   → Click any bar in the chart to drill down

Step 3: Create a Budget
   → Left sidebar → "Budgets"
   → Click "+ Add"
   ┌─ Create Budget ────────────────────────────────────────┐
   │ Name:               monthly-budget                      │
   │ Reset period:       Monthly                             │
   │ Creation date:      (auto-filled)                       │
   │ Expiration date:    2025-12-31                          │
   │ Budget amount:      $100                                │
   │ Click "Next"                                            │
   └────────────────────────────────────────────────────────┘

Step 4: Set Alert Conditions
   ┌─ Alert Conditions ─────────────────────────────────────┐
   │ Alert 1:                                                │
   │   Type:       Actual                                    │
   │   % of budget: 50                                       │
   │   Action group: ag-ops-team (or create new)             │
   │   Alert recipients: your-email@company.com              │
   │                                                         │
   │ Alert 2: Click "+ Add alert condition"                   │
   │   Type:       Actual                                    │
   │   % of budget: 75                                       │
   │   Alert recipients: your-email@company.com              │
   │                                                         │
   │ Alert 3: Click "+ Add alert condition"                   │
   │   Type:       Actual                                    │
   │   % of budget: 100                                      │
   │   Alert recipients: your-email@company.com              │
   │                     manager@company.com                  │
   │                                                         │
   │ Alert 4: Click "+ Add alert condition"                   │
   │   Type:       Forecasted                                │
   │   % of budget: 100                                      │
   │   (Alerts when Azure PREDICTS you'll exceed budget)     │
   └────────────────────────────────────────────────────────┘
   → Click "Create"

Step 5: View Azure Advisor Cost Recommendations
   → Search "Advisor" in the search bar
   → Click "Cost" tab
   → You'll see recommendations like:
     ┌─────────────────────────────────────────────────────┐
     │ ⚠️ Shut down vm-dev-01 (idle 30 days)               │
     │   Potential savings: $140/month                      │
     │                                                      │
     │ ⚠️ Right-size vm-web-01 from D4 to D2               │
     │   Potential savings: $70/month                       │
     │                                                      │
     │ ⚠️ Buy Reserved Instance for vm-prod-01             │
     │   Potential savings: $500/year (36% discount)       │
     └─────────────────────────────────────────────────────┘
   → Click each recommendation for details and action buttons
```

### Portal UI Walkthrough: Use the Azure Pricing Calculator

```
PORTAL STEPS — Estimate Costs Before Creating Resources:

Step 1: Open Pricing Calculator
   → Go to https://azure.microsoft.com/pricing/calculator/
   → (This is a separate website, not inside the Portal)

Step 2: Add Products
   → Click on products to add them to your estimate:
     Example: Click "Virtual Machines"
   ┌─ Configure VM ─────────────────────────────────────────┐
   │ Region:             East US                             │
   │ Operating System:   Linux                               │
   │ Type:               Standard_D2s_v5                     │
   │ Tier:               Standard                            │
   │ Instances:          2                                   │
   │ Hours per month:    730 (24/7)                          │
   │ Savings option:     Pay as you go                       │
   │                                                         │
   │ Estimated cost:     $140.16/month                       │
   └────────────────────────────────────────────────────────┘

Step 3: Add More Products
   → Click "Storage Accounts" → Configure:
     Type: Block Blob, LRS, Hot
     Storage: 100 GB
     Estimated: $1.80/month

   → Click "Azure SQL Database" → Configure:
     Type: Single Database, Standard S1
     Estimated: $30/month

Step 4: View Total Estimate
   → Scroll to bottom → See total monthly estimate
   → Example total: $171.96/month

Step 5: Export or Share
   → Click "Export" to download as Excel
   → Click "Save" to save the estimate (requires sign-in)
   → Click "Share" to get a shareable link
```

---

## 14.3 Cost Optimization Strategies

### Strategy 1: Right-Size Resources
```bash
# Check VM utilization
az monitor metrics list \
  --resource "/subscriptions/SUB_ID/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-web-01" \
  --metric "Percentage CPU" \
  --interval PT1H \
  --aggregation Average \
  --start-time 2024-01-01 \
  --end-time 2024-01-31

# If average CPU < 20% → downsize the VM
az vm resize --resource-group rg --name vm-web-01 --size Standard_B2s

# Savings example:
# D4s_v5 (4 vCPU, 16 GB) at 15% CPU → $140/month (wasted)
# B2s (2 vCPU, 4 GB) at 40% CPU → $30/month (right-sized)
# Savings: $110/month = $1,320/year
```

### Strategy 2: Auto-Shutdown Dev/Test VMs
```bash
# Enable auto-shutdown
az vm auto-shutdown \
  --resource-group rg-demo-eastus \
  --name vm-dev-01 \
  --time 1800 \
  --timezone "Eastern Standard Time"

# Meaning: Automatically shut down at 6:00 PM EST every day
# Savings: ~50% if VM runs only during business hours
```

### Strategy 3: Use Reserved Instances
```bash
# Check Advisor recommendations for RI
az advisor recommendation list \
  --filter "Category eq 'Cost'" \
  --output table

# Purchase RI via Portal:
# Reservations → Add → Virtual Machines
# Select: Region, VM size, Term (1 or 3 years)
# Scope: Shared (across subscriptions) or Single subscription
```

### Strategy 4: Use Spot VMs for Batch Jobs
```bash
# Create a Spot VM
az vm create \
  --resource-group rg-demo-eastus \
  --name vm-batch-spot \
  --image Ubuntu2204 \
  --size Standard_D4s_v5 \
  --priority Spot \
  --max-price 0.05 \
  --eviction-policy Deallocate

# --priority Spot     : Use spot pricing
# --max-price 0.05    : Maximum price per hour ($0.05 vs $0.19 PAYG)
# --eviction-policy   : Deallocate when evicted (can restart later)
```

### Strategy 5: Storage Tier Optimization
```
Move infrequently accessed data to cheaper tiers:
Hot  → Cool  (save ~45% on storage)
Cool → Cold  (save ~65% on storage)
Cold → Archive (save ~95% on storage)

Use lifecycle management policies to automate:
- After 30 days → Cool
- After 90 days → Cold
- After 180 days → Archive
- After 365 days → Delete
```

---

## 14.4 Azure Pricing Calculator

```
URL: https://azure.microsoft.com/pricing/calculator/

Steps:
1. Add products (VMs, Storage, SQL Database, etc.)
2. Configure each product (size, region, hours/month)
3. View estimated monthly cost
4. Export estimate as Excel or share link

Example Estimate:
┌────────────────────────────────────────────────────┐
│ Service                    │ Monthly Cost          │
├────────────────────────────┼───────────────────────┤
│ 2x D4s_v5 VMs (Linux)     │ $280                  │
│ Azure SQL Database (S2)    │ $150                  │
│ Storage (100 GB, LRS)      │ $2                    │
│ App Service (S1)           │ $70                   │
│ Load Balancer (Standard)   │ $18                   │
│ Bandwidth (100 GB outbound)│ $8                    │
├────────────────────────────┼───────────────────────┤
│ TOTAL                      │ $528/month            │
│ With 3-year RI on VMs      │ $368/month (30% less) │
└────────────────────────────┴───────────────────────┘
```

### TCO Calculator
```
URL: https://azure.microsoft.com/pricing/tco/calculator/

Compares on-premises costs vs Azure costs.
Input your current infrastructure → see potential savings.

Example:
On-premises: 10 servers, 5 TB storage, 2 DBAs
Annual cost: $250,000

Azure equivalent:
Compute: $50,000/year
Storage: $5,000/year
No hardware maintenance: -$30,000
No DBA for patching: -$40,000
Annual cost: $85,000

Savings: $165,000/year (66%)
```

---

## 14.5 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Unexpected high bill | Forgot to delete test resources | Set up budget alerts; use resource tags |
| `QuotaExceeded` | Subscription spending limit reached | Remove spending limit or increase quota |
| RI not applying | Wrong scope or VM size family | Check RI scope matches subscription/resource group |
| Spot VM evicted | Azure needs the capacity back | Use eviction-policy Deallocate; design for interruption |
| Bandwidth charges high | Large data egress | Use CDN, compress data, or use Private Peering |

### Cost Troubleshooting Checklist
```
1. Check Cost Analysis → filter by last 7 days → sort by cost
2. Look for:
   - VMs running 24/7 that should be dev/test (auto-shutdown)
   - Orphaned disks (VM deleted but disk remains)
   - Unused public IPs ($3.65/month each)
   - Over-provisioned resources (right-size)
   - Missing Reserved Instances for steady workloads
3. Set up budget alerts at 50%, 75%, 100%
4. Tag all resources with Owner and Environment
5. Review Azure Advisor cost recommendations weekly
```

---

## 14.6 Practice Questions

### Question 1
**Which pricing model offers the highest savings for predictable workloads?**
- A) Pay-As-You-Go
- B) Spot VMs
- C) Reserved Instances (3-year) ✅
- D) Dev/Test pricing

### Question 2
**Spot VMs can be evicted by Azure. True or False?**
- A) True ✅
- B) False

### Question 3
**Which tool compares on-premises costs to Azure costs?**
- A) Azure Pricing Calculator
- B) Azure TCO Calculator ✅
- C) Azure Cost Management
- D) Azure Advisor

### Question 4
**What is the Azure Hybrid Benefit?**
- A) Free Azure credits for students
- B) Using existing Windows/SQL licenses on Azure for savings ✅
- C) A discount for non-profit organizations
- D) Free tier services

### Question 5
**Data transfer INTO Azure is:**
- A) Always free ✅
- B) Charged per GB
- C) Free for the first 5 GB only
- D) Charged at a flat rate

**Explanation**: Inbound data transfer (ingress) is free. Outbound data transfer (egress) is charged after the first 100 GB/month.

---

[← Previous Module](./Module-13-High-Availability-DR.md) | [Next Module: Infrastructure as Code →](./Module-15-Infrastructure-as-Code.md)
