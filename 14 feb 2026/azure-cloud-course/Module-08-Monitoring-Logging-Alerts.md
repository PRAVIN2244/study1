# Module 08: Monitoring, Logging & Alerts

## Certification Relevance: AZ-104 (10-15%)

---

## 8.1 Azure Monitor Overview

```
Azure Monitor Ecosystem:
┌─────────────────────────────────────────────────────────────┐
│                     AZURE MONITOR                           │
│                                                             │
│  Data Sources:          Data Stores:        Actions:        │
│  ├── Applications       ├── Metrics DB      ├── Alerts      │
│  ├── VMs/Containers     ├── Log Analytics   ├── Dashboards  │
│  ├── Azure Resources    │   Workspace       ├── Workbooks   │
│  ├── Subscriptions      │                   ├── Autoscale   │
│  └── Azure AD/Entra     │                   └── Export      │
│                                                             │
│  Key Services:                                              │
│  ├── Metrics        (numeric time-series data)              │
│  ├── Logs           (structured log data - KQL queries)     │
│  ├── Alerts         (notifications when conditions met)     │
│  ├── Application Insights (app performance monitoring)      │
│  └── Log Analytics  (query and analyze logs)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 8.2 Azure Metrics

### What are Metrics?
Numerical values collected at regular intervals describing some aspect of a resource (CPU %, memory, network bytes, etc.).

### Portal UI Walkthrough: View VM Metrics

```
PORTAL STEPS — View Metrics for a Virtual Machine:

Step 1: Navigate to Your VM
   → Virtual machines → Click your VM name (e.g., vm-web-01)

Step 2: View Overview Metrics
   → The Overview page shows basic charts:
     • CPU (average percentage)
     • Network (bytes in/out)
     • Disk (bytes read/write)
     • Operations/Sec

Step 3: Open Detailed Metrics
   → Left sidebar → "Metrics"
   → You'll see the Metrics Explorer

Step 4: Create a Custom Chart
   ┌─────────────────────────────────────────────────────────┐
   │ Scope:       vm-web-01                                   │
   │ Metric Namespace: Virtual Machine Host                   │
   │ Metric:      Percentage CPU                              │
   │ Aggregation: Avg                                         │
   │ Time range:  Last 1 hour (top right dropdown)            │
   └─────────────────────────────────────────────────────────┘
   → Click "Add metric" to overlay another metric:
     Metric: Network In Total
     Aggregation: Sum
   → Now you see CPU and Network on the same chart

Step 5: Pin to Dashboard
   → Click the pin icon (📌) at the top right of the chart
   → Select your dashboard
   → Click "Pin"
   → The chart is now on your dashboard for quick access

Step 6: Save as Shared Chart
   → Click "Save to dashboard" → "Pin to dashboard"
   → Or click "Share" → "Copy link" to share with team
```

```bash
# List available metrics for a VM
az monitor metrics list-definitions \
  --resource "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Compute/virtualMachines/vm-web-01" \
  --query "[].{Name:name.value, Unit:unit}" \
  --output table

# Output:
# Name                          Unit
# ----------------------------  --------
# Percentage CPU                Percent
# Network In Total              Bytes
# Network Out Total             Bytes
# Disk Read Bytes               Bytes
# Disk Write Bytes              Bytes
# Available Memory Bytes        Bytes

# Get CPU usage for last hour
az monitor metrics list \
  --resource "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Compute/virtualMachines/vm-web-01" \
  --metric "Percentage CPU" \
  --interval PT1M \
  --start-time 2024-01-15T09:00:00Z \
  --end-time 2024-01-15T10:00:00Z \
  --aggregation Average

# Meaning:
# --metric "Percentage CPU" : Which metric to query
# --interval PT1M           : Data points every 1 minute
# --aggregation Average     : Average value per interval

# Output (simplified):
# TimeStamp              Average
# ---------------------  -------
# 2024-01-15T09:00:00Z   12.5
# 2024-01-15T09:01:00Z   15.3
# 2024-01-15T09:02:00Z   45.8
# ...
```

---

## 8.3 Log Analytics Workspace

### What is Log Analytics?
A centralized store for log data from Azure resources, on-premises servers, and other clouds. You query logs using Kusto Query Language (KQL).

```bash
# Create a Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-demo-eastus \
  --workspace-name law-demo-2024 \
  --location eastus \
  --sku PerGB2018

# Meaning:
# --sku PerGB2018 : Pay per GB ingested (~$2.76/GB)
# Free tier: 500 MB/day, 7-day retention

# Output:
# {
#   "name": "law-demo-2024",
#   "customerId": "workspace-id-guid",
#   "retentionInDays": 30
# }

# Enable diagnostics for a resource (send logs to workspace)
az monitor diagnostic-settings create \
  --resource "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Compute/virtualMachines/vm-web-01" \
  --name "send-to-law" \
  --workspace law-demo-2024 \
  --logs '[{"category": "Administrative", "enabled": true}]' \
  --metrics '[{"category": "AllMetrics", "enabled": true}]'

# Query logs using KQL
az monitor log-analytics query \
  --workspace "WORKSPACE_ID" \
  --analytics-query "Heartbeat | summarize count() by Computer | sort by count_ desc" \
  --output table

# Output:
# Computer      count_
# -----------   ------
# vm-web-01     1440
# vm-app-01     1438
```

### KQL (Kusto Query Language) Examples

```kql
// Find all errors in the last 24 hours
AzureActivity
| where TimeGenerated > ago(24h)
| where Level == "Error"
| project TimeGenerated, OperationName, ResourceGroup, Caller
| order by TimeGenerated desc

// CPU usage over 80% in the last hour
Perf
| where TimeGenerated > ago(1h)
| where ObjectName == "Processor" and CounterName == "% Processor Time"
| where CounterValue > 80
| summarize AvgCPU = avg(CounterValue) by Computer, bin(TimeGenerated, 5m)
| order by AvgCPU desc

// Failed sign-ins
SigninLogs
| where ResultType != "0"  // 0 = success
| where TimeGenerated > ago(7d)
| summarize FailedAttempts = count() by UserPrincipalName, IPAddress
| where FailedAttempts > 5
| order by FailedAttempts desc

// Disk space usage
Perf
| where ObjectName == "LogicalDisk" and CounterName == "% Free Space"
| where CounterValue < 20
| summarize MinFreeSpace = min(CounterValue) by Computer, InstanceName
| order by MinFreeSpace asc

// Top 10 most common errors
Syslog
| where SeverityLevel == "err"
| summarize Count = count() by SyslogMessage
| top 10 by Count
```

### KQL Quick Reference

```
| where       - Filter rows
| project     - Select columns
| summarize   - Aggregate (count, avg, sum, min, max)
| order by    - Sort results
| top N by    - Get top N results
| extend      - Add calculated column
| join        - Join two tables
| render      - Visualize (timechart, barchart, piechart)
| bin()       - Group time into intervals
| ago()       - Relative time (ago(1h), ago(7d))
| between     - Range filter
| contains    - String contains
| startswith  - String starts with
```

---

## 8.4 Azure Alerts

### Alert Types

```
1. Metric Alerts:    Trigger when a metric crosses a threshold
                     Example: CPU > 80% for 5 minutes

2. Log Alerts:       Trigger based on log query results
                     Example: More than 10 errors in 15 minutes

3. Activity Log:     Trigger on Azure operations
                     Example: VM deleted, resource group created

4. Smart Detection:  AI-based anomaly detection (Application Insights)
                     Example: Unusual spike in response time
```

### Portal UI Walkthrough: Create a Metric Alert

```
PORTAL STEPS — Create an Alert When CPU Exceeds 80%:

Step 1: Navigate to Monitor
   → Search "Monitor" in the search bar
   → Click "Monitor" from results
   → Left sidebar → "Alerts"

Step 2: Create Alert Rule
   → Click "+ Create" → "Alert rule"

Step 3: Select Scope (What to Monitor)
   → Click "Select scope"
   → Filter by resource type: "Virtual machines"
   → Select your VM: vm-web-01
   → Click "Apply"

Step 4: Configure Condition (When to Alert)
   → Click "Add condition"
   → Search for signal: "Percentage CPU"
   → Click "Percentage CPU"
   ┌─ Configure Signal Logic ───────────────────────────────┐
   │ Threshold:           ● Static                           │
   │ Aggregation type:    Average                            │
   │ Operator:            Greater than                       │
   │ Threshold value:     80                                 │
   │ Check every:         1 minute                           │
   │ Lookback period:     5 minutes                          │
   │                                                         │
   │ Preview chart shows recent CPU data with threshold line │
   │ Click "Done"                                            │
   └────────────────────────────────────────────────────────┘

Step 5: Configure Actions (Who Gets Notified)
   → Click "Add action groups" → "+ Create action group"
   ┌─ Basics ───────────────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   │ Action group name:  ag-ops-team                         │
   │ Display name:       OpsTeam                             │
   └────────────────────────────────────────────────────────┘
   → Click "Next: Notifications >"
   ┌─ Notifications ────────────────────────────────────────┐
   │ Notification type:  Email/SMS message/Push/Voice        │
   │ Name:               ops-email                           │
   │ → Configure:                                            │
   │   ☑ Email: ops-team@company.com                         │
   │   ☑ SMS:   Country code: 1  Phone: 5551234567          │
   │   Click "OK"                                            │
   └────────────────────────────────────────────────────────┘
   → Click "Review + create" → "Create"

Step 6: Configure Details
   → Alert rule name:    alert-high-cpu
   → Severity:           2 - Warning
   → Description:        VM CPU usage exceeds 80%
   → Region:             East US

Step 7: Review + Create
   → Click "Review + create" → "Create"
   → Alert rule is now active

Step 8: Test and Verify
   → When CPU exceeds 80% for 5 minutes:
     • Email sent to ops-team@company.com
     • SMS sent to the configured phone number
   → View fired alerts: Monitor → Alerts → See active alerts
```

### Portal UI Walkthrough: Create a Log Analytics Workspace

```
PORTAL STEPS — Create a Log Analytics Workspace:

Step 1: Navigate to Log Analytics
   → Search "Log Analytics workspaces" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Name:               law-demo-2024                        │
   │ Region:             East US                              │
   └─────────────────────────────────────────────────────────┘
   → Click "Review + create" → "Create"

Step 3: Enable Diagnostics for a VM
   → Go to your VM → Left sidebar → "Diagnostic settings"
   → Click "+ Add diagnostic setting"
   ┌─────────────────────────────────────────────────────────┐
   │ Diagnostic setting name: send-to-law                    │
   │ Logs:                                                    │
   │   ☑ Administrative                                      │
   │   ☑ Security                                            │
   │   ☑ Alert                                               │
   │ Metrics:                                                 │
   │   ☑ AllMetrics                                          │
   │ Destination:                                             │
   │   ☑ Send to Log Analytics workspace                     │
   │   Workspace: law-demo-2024                              │
   │ Click "Save"                                             │
   └─────────────────────────────────────────────────────────┘

Step 4: Query Logs
   → Go to Log Analytics workspace → "Logs"
   → Close the query templates popup
   → Type a KQL query:
     Heartbeat
     | summarize count() by Computer
     | sort by count_ desc
   → Click "Run"
   → Results appear in a table below
   → Click "Chart" to visualize the results

Step 5: Save a Query
   → After running a query, click "Save" → "Save as query"
   → Name: "VM Heartbeat Count"
   → Category: "Virtual Machines"
   → Click "Save"
   → Access saved queries from the left panel
```

### Creating Alerts with CLI

```bash
# Create a metric alert (CPU > 80%)
az monitor metrics alert create \
  --resource-group rg-demo-eastus \
  --name "alert-high-cpu" \
  --scopes "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Compute/virtualMachines/vm-web-01" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "VM CPU usage exceeds 80%"

# Meaning:
# --condition "avg Percentage CPU > 80" : Average CPU > 80%
# --window-size 5m                      : Over a 5-minute window
# --evaluation-frequency 1m             : Check every 1 minute
# --severity 2                          : Sev 2 (Warning)
#   Severity levels: 0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose

# Create an action group (who gets notified)
az monitor action-group create \
  --resource-group rg-demo-eastus \
  --name "ag-ops-team" \
  --short-name "OpsTeam" \
  --action email ops-email ops-team@company.com \
  --action sms ops-sms 1 5551234567

# Meaning: When alert fires, send email AND SMS to ops team

# Link action group to alert
az monitor metrics alert update \
  --resource-group rg-demo-eastus \
  --name "alert-high-cpu" \
  --add-action ag-ops-team

# Create an activity log alert (notify when VM is deleted)
az monitor activity-log alert create \
  --resource-group rg-demo-eastus \
  --name "alert-vm-deleted" \
  --condition category=Administrative and operationName="Microsoft.Compute/virtualMachines/delete" \
  --action-group ag-ops-team \
  --description "Alert when any VM is deleted"

# List all alerts
az monitor metrics alert list \
  --resource-group rg-demo-eastus \
  --output table
```

---

## 8.5 Application Insights

### What is Application Insights?
An APM (Application Performance Management) service for monitoring live web applications. Detects performance anomalies, diagnoses issues, and understands user behavior.

```
What Application Insights tracks:
- Request rates, response times, failure rates
- Dependency calls (database, REST API, external services)
- Exceptions and stack traces
- Page views and load performance
- User sessions and custom events
- Performance counters (CPU, memory)

Real-World Example: An e-commerce site uses Application Insights:
- Discovers that checkout page takes 8 seconds (should be 2)
- Drill down: SQL query taking 6 seconds
- Fix: Add database index
- Result: Checkout drops to 1.5 seconds, conversion rate increases 15%
```

```bash
# Create Application Insights resource
az monitor app-insights component create \
  --app ai-webapp-demo \
  --location eastus \
  --resource-group rg-demo-eastus \
  --kind web \
  --application-type web

# Output:
# {
#   "instrumentationKey": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
#   "connectionString": "InstrumentationKey=aaaa...;IngestionEndpoint=https://eastus-1.in.applicationinsights.azure.com/"
# }
# → Add this connection string to your application

# Query Application Insights
az monitor app-insights query \
  --app ai-webapp-demo \
  --resource-group rg-demo-eastus \
  --analytics-query "requests | where resultCode >= 500 | summarize count() by name | top 5 by count_"
```

---

## 8.6 Azure Service Health

```
Three components:

1. Azure Status:     Global Azure service issues
                     URL: status.azure.com

2. Service Health:   Issues affecting YOUR services in YOUR regions
                     Personalized dashboard in Portal

3. Resource Health:  Health of YOUR specific resources
                     "Is my VM healthy?"

Set up Service Health alerts:
az monitor activity-log alert create \
  --resource-group rg-demo-eastus \
  --name "alert-service-health" \
  --condition category=ServiceHealth \
  --action-group ag-ops-team
```

---

## 8.7 Azure Advisor

```
Azure Advisor provides personalized recommendations in 5 categories:

1. Reliability:    "Enable soft delete for Key Vault"
2. Security:       "Enable MFA for admin accounts"
3. Performance:    "Right-size underutilized VMs"
4. Cost:           "Shut down unused VMs (saving $500/month)"
5. Operational:    "Set up Service Health alerts"

# View Advisor recommendations
az advisor recommendation list --output table

# Output:
# Category      Impact    Description
# -----------   ------    ------------------------------------------
# Cost          High      Shut down vm-dev-01 (idle for 30 days)
# Security      High      Enable MFA for 3 admin accounts
# Performance   Medium    Resize vm-web-01 from D4 to D2 (underutilized)
# Reliability   Medium    Enable backup for 2 VMs
```

---

## 8.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `No data in Log Analytics` | Diagnostic settings not configured | Enable diagnostics: `az monitor diagnostic-settings create` |
| `Alert not firing` | Wrong condition or window size | Verify metric name, threshold, and evaluation frequency |
| `KQL query returns empty` | Wrong table name or time range | Check table exists; extend time range with `ago()` |
| `Action group not sending emails` | Email in spam or action group misconfigured | Check spam folder; verify email in action group |
| `Application Insights no data` | Wrong instrumentation key | Verify connection string in app configuration |
| `Workspace data retention exceeded` | Data older than retention period | Increase retention: `az monitor log-analytics workspace update --retention-time 90` |
| `Query timeout` | Query too complex or too much data | Add time filters, reduce scope, optimize KQL |

---

## 8.9 Practice Questions

### Question 1
**Which query language is used in Log Analytics?**
- A) SQL
- B) KQL (Kusto Query Language) ✅
- C) GraphQL
- D) PowerShell

### Question 2
**What is the purpose of an Action Group?**
- A) To group Azure resources
- B) To define who gets notified when an alert fires ✅
- C) To organize users in Entra ID
- D) To manage RBAC roles

### Question 3
**Which Azure service provides personalized recommendations for cost, security, and performance?**
- A) Azure Monitor
- B) Azure Advisor ✅
- C) Azure Sentinel
- D) Azure Policy

### Question 4
**Application Insights is used for:**
- A) Managing virtual machines
- B) Monitoring application performance and diagnosing issues ✅
- C) Creating virtual networks
- D) Managing databases

### Question 5
**What severity level represents the most critical alert?**
- A) Sev 0 ✅
- B) Sev 1
- C) Sev 4
- D) Sev 5

---

[← Previous Module](./Module-07-Identity-and-Security.md) | [Next Module: DevOps & CI/CD →](./Module-09-DevOps-CICD.md)
