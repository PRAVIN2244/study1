# Module 02: Azure Account, Portal, CLI & PowerShell

## Certification Relevance: AZ-900, AZ-104

---

## 2.1 Creating an Azure Free Account

### Portal UI Walkthrough: Create a Free Azure Account (Step-by-Step)

```
PORTAL STEPS — Create Your Free Azure Account:

Step 1: Open the Azure Free Account Page
   → Open your browser
   → Go to https://azure.microsoft.com/free/
   → Click the "Start free" button (green button)

Step 2: Sign In or Create a Microsoft Account
   → If you already have a Microsoft account (Outlook, Hotmail, Xbox):
     → Enter your email → Click "Next" → Enter password → Click "Sign in"
   → If you DON'T have a Microsoft account:
     → Click "Create one!"
     → Enter a new email address (or use an existing one)
     → Create a password
     → Enter your name
     → Click "Next"

Step 3: Phone Verification
   → Country/region: Select your country
   → Phone number: Enter your mobile number
   → Click "Text me" or "Call me"
   → Enter the verification code you receive
   → Click "Verify code"

Step 4: Identity Verification (Credit Card)
   → ⚠️ Your card will NOT be charged
   → ⚠️ This is ONLY for identity verification
   → Enter:
     ┌─────────────────────────────────────────────────────┐
     │ Card number:     XXXX XXXX XXXX XXXX                │
     │ Expiry date:     MM/YY                               │
     │ CVV:             XXX                                  │
     │ Name on card:    Your Name                           │
     │ Address:         Your billing address                │
     └─────────────────────────────────────────────────────┘
   → ⚠️ After the $200 free credit runs out, Azure will NOT
     auto-charge you. You must manually upgrade to pay-as-you-go.

Step 5: Agreement
   → ☑ Check "I agree to the subscription agreement,
     offer details, and privacy statement"
   → Click "Sign up"

Step 6: Welcome to Azure!
   → You'll see "You're ready to start with Azure"
   → Click "Go to the Azure portal"
   → You're now at https://portal.azure.com
   → Your free account includes:
     ┌─────────────────────────────────────────────────────┐
     │ ✅ $200 free credit (valid for 30 days)              │
     │ ✅ 12 months of popular free services                │
     │ ✅ 55+ always-free services (no time limit)          │
     │ ✅ No automatic charges after free credit expires    │
     └─────────────────────────────────────────────────────┘

⚠️ IMPORTANT TIPS:
   → Set up a budget alert immediately (Cost Management → Budgets)
     to track your $200 credit usage
   → Deallocate (stop) VMs when not in use — they consume credit
   → Delete resources you're done experimenting with
   → After 30 days, unused free credit expires
   → Free-tier services (like 750 hrs B1s VM) continue for 12 months
```

### Free Tier Services (Always Free)

| Service | Free Amount |
|---------|-------------|
| Azure App Service | 10 web apps |
| Azure Functions | 1 million requests/month |
| Azure Cosmos DB | 1000 RU/s, 25 GB storage |
| Azure DevOps | 5 users, unlimited private repos |
| Azure Kubernetes Service | Free cluster management |
| Azure Active Directory (Entra ID) | 50,000 objects |
| Blob Storage | 5 GB LRS hot |
| Azure SQL Database | 250 GB (first 12 months) |

---

## 2.2 Azure Portal

### What is Azure Portal?
A web-based, unified console that provides an alternative to command-line tools. URL: **https://portal.azure.com**

### Portal Navigation

```
Azure Portal Layout:
┌──────────────────────────────────────────────────────────┐
│  ☰ Menu   🔍 Search    ⚡ Cloud Shell    🔔 Notifications │
├──────────┬───────────────────────────────────────────────┤
│          │                                               │
│ Favorites│           Dashboard                           │
│          │                                               │
│ • Home   │  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│ • All    │  │ Resource │  │  Cost   │  │ Service │     │
│   Services│  │  Groups  │  │ Summary │  │ Health  │     │
│ • VMs    │  └─────────┘  └─────────┘  └─────────┘     │
│ • SQL    │                                               │
│ • Storage│  ┌─────────────────────────────────┐         │
│ • App    │  │     Recent Resources             │         │
│   Service│  │     • my-vm-01                   │         │
│ • Monitor│  │     • my-storage-account         │         │
│          │  │     • my-sql-database             │         │
│          │  └─────────────────────────────────┘         │
└──────────┴───────────────────────────────────────────────┘
```

### Portal UI Walkthrough: Creating a Resource Group

```
PORTAL STEPS — Create a Resource Group:

Step 1: Open Azure Portal
   → Go to https://portal.azure.com
   → Sign in with your Microsoft account

Step 2: Navigate to Resource Groups
   → In the top search bar, type "Resource groups"
   → Click "Resource groups" from the dropdown results
   → You will see a list of existing resource groups (empty if new account)

Step 3: Click "+ Create"
   → Click the "+ Create" button at the top left of the Resource groups page

Step 4: Fill in the Basics tab
   → Subscription: Select your subscription (e.g., "Azure subscription 1")
   → Resource group: Type "rg-demo-eastus"
   → Region: Click the dropdown → Select "(US) East US"

Step 5: Tags tab (Optional but recommended)
   → Click "Next: Tags >"
   → Name: "Environment"    Value: "Demo"
   → Name: "Owner"          Value: "YourName"
   → Tags help you organize and track costs

Step 6: Review + Create
   → Click "Review + create"
   → Review the details:
     ┌─────────────────────────────────────┐
     │ Subscription:    Azure subscription 1│
     │ Resource group:  rg-demo-eastus      │
     │ Region:          East US             │
     │ Tags:            Environment=Demo    │
     └─────────────────────────────────────┘
   → Click "Create"

Step 7: Verify
   → You will see "Resource group created" notification (bell icon 🔔)
   → Click "Go to resource group" to open it
   → The resource group is empty — ready for you to add resources
```

### Portal UI Walkthrough: Customizing Your Dashboard

```
PORTAL STEPS — Create a Custom Dashboard:

Step 1: Go to Dashboard
   → Click "Dashboard" in the left sidebar (or Home → Dashboard)

Step 2: Create New Dashboard
   → Click "+ New dashboard" → "Blank dashboard"
   → Give it a name: "My Azure Lab Dashboard"

Step 3: Add Tiles
   → From the Tile Gallery on the right, drag and drop:
     • "All resources" — shows all your Azure resources
     • "Resource groups" — quick access to resource groups
     • "Clock" — shows current time
     • "Markdown" — add custom notes/instructions

Step 4: Add Resource-Specific Tiles
   → Click "Done customizing" to save
   → Later, from any resource page, click the pin icon (📌)
     to pin metrics or charts to your dashboard

Step 5: Save
   → Click "Save" at the top
   → Your custom dashboard is now the default view
```

---

## 2.3 Azure Cloud Shell

### What is Cloud Shell?
A browser-based shell experience built into Azure Portal. No local installation needed.

### Accessing Cloud Shell
```
Option 1: Click the Cloud Shell icon (>_) in the Azure Portal top bar
Option 2: Go to https://shell.azure.com
Option 3: Open it in VS Code with Azure extension
```

### First-Time Setup
```
When you first open Cloud Shell:
1. Choose Bash or PowerShell
2. It asks to create a storage account (for persisting files)
3. Click "Create storage"
4. Cloud Shell provisions:
   - A storage account
   - A file share (5 GB)
   - A small Linux container

Cost: ~$1/month for the storage account
```

### Cloud Shell Features
```
- Pre-installed tools: az CLI, PowerShell, terraform, kubectl, docker, git
- Persistent storage: 5 GB file share mounted at $HOME/clouddrive
- Integrated file editor: code . (opens Monaco editor)
- Auto-authenticated: Already logged in to your Azure account
- Timeout: 20 minutes of inactivity
```

---

## 2.4 Azure CLI (az)

### What is Azure CLI?
A cross-platform command-line tool to manage Azure resources. Available on Windows, macOS, Linux, and Cloud Shell.

### Installation

```bash
# On Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# On macOS
brew update && brew install azure-cli

# On Windows (PowerShell as Admin)
winget install -e --id Microsoft.AzureCLI

# Verify installation
az --version
# Output:
# azure-cli    2.61.0
# core         2.61.0
# telemetry    1.1.0
```

### Authentication

```bash
# Login to Azure (opens browser for authentication)
az login

# Output:
# A web browser has been opened at https://login.microsoftonline.com/...
# [
#   {
#     "cloudName": "AzureCloud",
#     "id": "12345678-1234-1234-1234-123456789012",
#     "isDefault": true,
#     "name": "Azure subscription 1",
#     "state": "Enabled",
#     "tenantId": "87654321-4321-4321-4321-210987654321",
#     "user": {
#       "name": "user@example.com",
#       "type": "user"
#     }
#   }
# ]

# Login without browser (for servers/CI)
az login --use-device-code
# Output:
# To sign in, use a web browser to open https://microsoft.com/devicelogin
# and enter the code ABCD1234 to authenticate.

# Login with service principal (for automation)
az login --service-principal \
  --username APP_ID \
  --password CLIENT_SECRET \
  --tenant TENANT_ID
```

### Account Management

```bash
# List all subscriptions
az account list --output table

# Output:
# Name                  CloudName    SubscriptionId                        TenantId                              State    IsDefault
# --------------------  -----------  ------------------------------------  ------------------------------------  -------  ---------
# Azure subscription 1  AzureCloud   12345678-1234-1234-1234-123456789012  87654321-4321-4321-4321-210987654321  Enabled  True
# Dev Subscription      AzureCloud   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee  87654321-4321-4321-4321-210987654321  Enabled  False

# Set active subscription
az account set --subscription "Dev Subscription"
# Meaning: All subsequent commands will use "Dev Subscription"

# Show current subscription
az account show --output table
# Output:
# Name              CloudName    SubscriptionId                        State    IsDefault
# ----------------  -----------  ------------------------------------  -------  ---------
# Dev Subscription  AzureCloud   aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee  Enabled  True
```

### Output Formats

```bash
# JSON (default) - detailed, machine-readable
az group list --output json

# Table - human-readable summary
az group list --output table
# Output:
# Name              Location    Status
# ----------------  ----------  ---------
# rg-demo-eastus    eastus      Succeeded
# rg-prod-westus    westus      Succeeded

# TSV - tab-separated, good for scripting
az group list --query "[].name" --output tsv
# Output:
# rg-demo-eastus
# rg-prod-westus

# YAML - structured, readable
az group list --output yaml
```

### Resource Group Commands

```bash
# Create a resource group
az group create \
  --name rg-demo-eastus \
  --location eastus

# Meaning: Create a logical container named "rg-demo-eastus" in the East US region
# Output:
# {
#   "id": "/subscriptions/.../resourceGroups/rg-demo-eastus",
#   "location": "eastus",
#   "name": "rg-demo-eastus",
#   "properties": {
#     "provisioningState": "Succeeded"
#   },
#   "type": "Microsoft.Resources/resourceGroups"
# }

# List all resource groups
az group list --output table

# Show details of a specific resource group
az group show --name rg-demo-eastus

# Delete a resource group (and ALL resources inside it)
az group delete --name rg-demo-eastus --yes --no-wait
# --yes: Skip confirmation prompt
# --no-wait: Don't wait for the operation to complete (runs in background)

# Check if a resource group exists
az group exists --name rg-demo-eastus
# Output: true or false

# List resources in a resource group
az resource list --resource-group rg-demo-eastus --output table
```

### JMESPath Queries (--query)

```bash
# Get only names of resource groups
az group list --query "[].name" --output tsv
# Output:
# rg-demo-eastus
# rg-prod-westus

# Filter resource groups by location
az group list --query "[?location=='eastus'].name" --output tsv
# Output:
# rg-demo-eastus

# Get specific fields
az group list --query "[].{Name:name, Location:location, State:properties.provisioningState}" --output table
# Output:
# Name              Location    State
# ----------------  ----------  ---------
# rg-demo-eastus    eastus      Succeeded

# Get the first resource group
az group list --query "[0]"

# Count resource groups
az group list --query "length(@)"
# Output: 2
```

### Useful CLI Tips

```bash
# Find commands (interactive)
az find "create vm"
# Shows relevant commands and examples

# Get help for any command
az vm create --help

# Enable auto-complete (Bash)
source /etc/bash_completion.d/azure-cli

# Set default resource group and location
az configure --defaults group=rg-demo-eastus location=eastus
# Now you don't need to specify --resource-group and --location every time

# Clear defaults
az configure --defaults group="" location=""

# Interactive mode (auto-complete, descriptions)
az interactive
```

---

## 2.5 Azure PowerShell

### What is Azure PowerShell?
A set of PowerShell cmdlets for managing Azure resources. Uses the Az module.

### Installation

```powershell
# Install Az module (PowerShell 7+ recommended)
Install-Module -Name Az -AllowClobber -Scope CurrentUser

# Output:
# Untrusted repository
# You are installing the modules from an untrusted repository...
# [Y] Yes  [A] Yes to All  [N] No  → Type 'A'

# Verify installation
Get-Module -Name Az -ListAvailable
# Output:
# ModuleType Version  Name
# ---------- -------  ----
# Script     12.0.0   Az

# Update Az module
Update-Module -Name Az
```

### Authentication

```powershell
# Login to Azure (opens browser)
Connect-AzAccount

# Output:
# Account          SubscriptionName       TenantId                             Environment
# -------          ----------------       --------                             -----------
# user@example.com Azure subscription 1   87654321-4321-4321-4321-210987654321 AzureCloud

# Login with device code
Connect-AzAccount -UseDeviceAuthentication

# Login with service principal
$credential = New-Object System.Management.Automation.PSCredential($appId, $securePassword)
Connect-AzAccount -ServicePrincipal -Credential $credential -Tenant $tenantId
```

### Common PowerShell Commands

```powershell
# List subscriptions
Get-AzSubscription

# Output:
# Name                 Id                                   TenantId                             State
# ----                 --                                   --------                             -----
# Azure subscription 1 12345678-1234-1234-1234-123456789012 87654321-4321-4321-4321-210987654321 Enabled

# Set active subscription
Set-AzContext -SubscriptionName "Azure subscription 1"

# Create resource group
New-AzResourceGroup -Name "rg-demo-eastus" -Location "East US"

# Output:
# ResourceGroupName : rg-demo-eastus
# Location          : eastus
# ProvisioningState : Succeeded
# Tags              :
# ResourceId        : /subscriptions/.../resourceGroups/rg-demo-eastus

# List resource groups
Get-AzResourceGroup | Format-Table

# Output:
# ResourceGroupName  Location  ProvisioningState
# -----------------  --------  -----------------
# rg-demo-eastus     eastus    Succeeded
# rg-prod-westus     westus    Succeeded

# Delete resource group
Remove-AzResourceGroup -Name "rg-demo-eastus" -Force
# -Force: Skip confirmation prompt

# List all resources in a resource group
Get-AzResource -ResourceGroupName "rg-demo-eastus" | Format-Table
```

### CLI vs PowerShell Comparison

| Task | Azure CLI | Azure PowerShell |
|------|-----------|-----------------|
| Login | `az login` | `Connect-AzAccount` |
| List subscriptions | `az account list` | `Get-AzSubscription` |
| Set subscription | `az account set -s NAME` | `Set-AzContext -Subscription NAME` |
| Create RG | `az group create -n NAME -l LOCATION` | `New-AzResourceGroup -Name NAME -Location LOCATION` |
| Delete RG | `az group delete -n NAME --yes` | `Remove-AzResourceGroup -Name NAME -Force` |
| Create VM | `az vm create ...` | `New-AzVM ...` |
| List VMs | `az vm list` | `Get-AzVM` |

### When to Use Which?

```
Azure CLI (az):
- Linux/macOS users
- Bash scripting
- Concise syntax
- CI/CD pipelines (GitHub Actions, Jenkins)

Azure PowerShell:
- Windows administrators
- Complex scripting with objects
- Integration with other PowerShell modules
- Existing PowerShell automation

Both work equally well. Choose based on your comfort level.
Exam tip: AZ-104 tests both. Know the equivalent commands.
```

---

## 2.6 Azure Resource Manager (ARM)

### What is ARM?
Azure Resource Manager is the deployment and management service for Azure. Every request to Azure (Portal, CLI, PowerShell, SDK, REST API) goes through ARM.

```
                    ┌──────────────┐
                    │   Azure      │
                    │   Resource   │
                    │   Manager    │
                    │   (ARM)      │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
    │  Azure    │   │  Azure    │   │  REST     │
    │  Portal   │   │  CLI /    │   │  API /    │
    │           │   │  PowerShell│   │  SDKs     │
    └───────────┘   └───────────┘   └───────────┘

All paths lead to ARM → ARM authenticates, authorizes, and processes the request
```

### ARM Benefits
```
1. Declarative templates (JSON/Bicep) - define WHAT you want, not HOW
2. Consistent management layer - same API regardless of tool used
3. Resource dependencies - ARM handles deployment order
4. Access control - RBAC applied at ARM level
5. Tagging - organize resources with metadata
6. Billing - group costs by tags or resource groups
```

---

## 2.7 Tags

### What are Tags?
Key-value pairs that you attach to Azure resources for organization, cost tracking, and automation.

```bash
# Add tags when creating a resource
az group create \
  --name rg-finance-prod \
  --location eastus \
  --tags Environment=Production Department=Finance CostCenter=CC1234

# Output includes:
# "tags": {
#   "CostCenter": "CC1234",
#   "Department": "Finance",
#   "Environment": "Production"
# }

# Add/update tags on existing resource
az group update \
  --name rg-finance-prod \
  --tags Environment=Production Department=Finance CostCenter=CC1234 Owner=john@company.com

# List resources with a specific tag
az resource list --tag Environment=Production --output table

# Remove all tags
az group update --name rg-finance-prod --tags ""
```

### Real-World Tagging Strategy

```
Industry Standard Tags:
┌──────────────────┬────────────────────┬──────────────────────────────┐
│ Tag Name         │ Example Value      │ Purpose                      │
├──────────────────┼────────────────────┼──────────────────────────────┤
│ Environment      │ Production         │ Identify deployment stage    │
│ Department       │ Finance            │ Cost allocation              │
│ CostCenter       │ CC-1234            │ Billing/chargeback           │
│ Owner            │ john@company.com   │ Contact for issues           │
│ Project          │ E-Commerce-v2      │ Project tracking             │
│ CreatedBy        │ Terraform          │ Track how resource was made  │
│ ExpirationDate   │ 2024-12-31         │ Temporary resource cleanup   │
│ Compliance       │ HIPAA              │ Regulatory requirements      │
└──────────────────┴────────────────────┴──────────────────────────────┘
```

### Exam Tip
```
AZ-104 question: "Tags are NOT inherited from resource groups to resources."
This is a common trick question. If you tag a resource group, the
resources inside do NOT automatically get those tags. You must apply
tags to each resource individually (or use Azure Policy to enforce).
```

---

## 2.8 Hands-On Lab: Your First Azure Resources

### Lab: Create and Manage Resources Using CLI

```bash
# Step 1: Login
az login

# Step 2: Create a resource group
az group create --name rg-lab-01 --location eastus
# Expected: "provisioningState": "Succeeded"

# Step 3: Create a storage account
az storage account create \
  --name stlab01$(date +%s) \
  --resource-group rg-lab-01 \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2
# Meaning:
#   --name: Globally unique name (we append timestamp)
#   --sku Standard_LRS: Locally redundant storage (cheapest)
#   --kind StorageV2: General-purpose v2 (recommended)

# Step 4: List resources in the group
az resource list --resource-group rg-lab-01 --output table
# Output:
# Name                  ResourceGroup    Location    Type                               Status
# --------------------  ---------------  ----------  ---------------------------------  --------
# stlab011706123456     rg-lab-01        eastus      Microsoft.Storage/storageAccounts

# Step 5: Add tags
az resource tag \
  --tags Environment=Lab Purpose=Learning \
  --resource-group rg-lab-01 \
  --name stlab011706123456 \
  --resource-type Microsoft.Storage/storageAccounts

# Step 6: View resource details
az storage account show \
  --name stlab011706123456 \
  --resource-group rg-lab-01 \
  --query "{Name:name, Location:location, SKU:sku.name, Kind:kind}" \
  --output table
# Output:
# Name                  Location    SKU            Kind
# --------------------  ----------  -------------  ---------
# stlab011706123456     eastus      Standard_LRS   StorageV2

# Step 7: Clean up (delete everything)
az group delete --name rg-lab-01 --yes --no-wait
# This deletes the resource group AND the storage account inside it
```

---

## 2.9 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `AADSTS50076: MFA required` | Multi-factor authentication needed | Complete MFA verification in browser |
| `The subscription 'xxx' could not be found` | Wrong subscription or not logged in | Run `az login` then `az account set -s "name"` |
| `az: command not found` | CLI not installed or not in PATH | Reinstall CLI or add to PATH |
| `The term 'Connect-AzAccount' is not recognized` | Az PowerShell module not installed | Run `Install-Module -Name Az` |
| `Storage account name already taken` | Names must be globally unique | Choose a different name (3-24 chars, lowercase + numbers only) |
| `InvalidResourceGroupName` | Invalid characters in name | Use only alphanumeric, underscores, hyphens, periods, parentheses |
| `Cloud Shell timed out` | 20 min inactivity | Reconnect; files in ~/clouddrive persist |
| `AuthorizationFailed` | Insufficient RBAC permissions | Request appropriate role from admin |

### Troubleshooting Steps

```bash
# Check if logged in
az account show
# If error → run az login

# Check current subscription
az account show --query name --output tsv

# List available locations
az account list-locations --query "[].name" --output tsv

# Check resource provider registration
az provider list --query "[?registrationState=='Registered'].namespace" --output tsv

# Register a resource provider
az provider register --namespace Microsoft.Storage
# Wait for registration
az provider show --namespace Microsoft.Storage --query "registrationState"

# Debug a command (verbose output)
az group create --name test --location eastus --debug

# Check Azure service health
az rest --method get --url "https://management.azure.com/providers/Microsoft.ResourceHealth/availabilityStatuses?api-version=2020-05-01"
```

---

## 2.10 Practice Questions

### Question 1
**Which tool is built into the Azure Portal and requires no local installation?**
- A) Azure CLI
- B) Azure PowerShell
- C) Azure Cloud Shell ✅
- D) Visual Studio Code

**Explanation**: Azure Cloud Shell is a browser-based shell accessible directly from the Azure Portal. It comes pre-installed with both Azure CLI and PowerShell.

### Question 2
**What is the purpose of Azure Resource Manager (ARM)?**
- A) To monitor Azure resources
- B) To provide a consistent management layer for all Azure operations ✅
- C) To store Azure resource templates
- D) To manage user authentication

**Explanation**: ARM is the deployment and management service for Azure. All requests (Portal, CLI, PowerShell, API) go through ARM for authentication, authorization, and processing.

### Question 3
**Which command sets the default subscription in Azure CLI?**
- A) `az subscription set`
- B) `az account set --subscription "name"` ✅
- C) `az default subscription "name"`
- D) `az config set subscription="name"`

### Question 4
**Are tags inherited from resource groups to resources?**
- A) Yes, always
- B) Yes, but only for new resources
- C) No, tags are not inherited ✅
- D) Only if Azure Policy enforces it

**Explanation**: Tags are NOT inherited. You must apply tags to each resource individually. However, you can use Azure Policy to enforce tag inheritance.

---

[← Previous Module](./Module-01-Cloud-Concepts-and-Azure-Fundamentals.md) | [Next Module: Compute Services →](./Module-03-Compute-Services.md)
