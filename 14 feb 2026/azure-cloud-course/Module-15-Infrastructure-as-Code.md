# Module 15: Infrastructure as Code (ARM, Bicep, Terraform)

## Certification Relevance: AZ-104, AZ-204

---

## 15.1 What is Infrastructure as Code (IaC)?

```
Manual (Portal/CLI):              Infrastructure as Code:
├── Click through Portal          ├── Write a template file
├── Run CLI commands              ├── Deploy template
├── Hard to reproduce             ├── Reproducible every time
├── No version control            ├── Stored in Git
├── Error-prone                   ├── Consistent
├── No audit trail                ├── Full change history
└── "It worked on my machine"     └── "It works everywhere"

IaC Tools for Azure:
├── ARM Templates (JSON) — Azure native, verbose
├── Bicep — Azure native, concise (compiles to ARM)
├── Terraform — Multi-cloud, HCL language
└── Pulumi — Multi-cloud, general-purpose languages
```

---

## 15.2 ARM Templates

### What is an ARM Template?
A JSON file that defines the infrastructure and configuration for your Azure deployment. Declarative — you describe WHAT you want, Azure figures out HOW.

### ARM Template Structure

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "storageAccountName": {
      "type": "string",
      "metadata": { "description": "Name of the storage account" }
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    },
    "sku": {
      "type": "string",
      "defaultValue": "Standard_LRS",
      "allowedValues": ["Standard_LRS", "Standard_GRS", "Standard_ZRS"]
    }
  },
  "variables": {
    "storageAccountFullName": "[concat(parameters('storageAccountName'), uniqueString(resourceGroup().id))]"
  },
  "resources": [
    {
      "type": "Microsoft.Storage/storageAccounts",
      "apiVersion": "2023-01-01",
      "name": "[variables('storageAccountFullName')]",
      "location": "[parameters('location')]",
      "sku": { "name": "[parameters('sku')]" },
      "kind": "StorageV2",
      "properties": {
        "supportsHttpsTrafficOnly": true,
        "minimumTlsVersion": "TLS1_2"
      }
    }
  ],
  "outputs": {
    "storageAccountId": {
      "type": "string",
      "value": "[resourceId('Microsoft.Storage/storageAccounts', variables('storageAccountFullName'))]"
    },
    "primaryEndpoint": {
      "type": "string",
      "value": "[reference(variables('storageAccountFullName')).primaryEndpoints.blob]"
    }
  }
}
```

### Deploying ARM Templates

```bash
# Deploy a template
az deployment group create \
  --resource-group rg-demo-eastus \
  --template-file main.json \
  --parameters storageAccountName=stprod sku=Standard_GRS

# Meaning:
# --template-file : Path to the ARM template
# --parameters    : Override parameter values

# Output:
# {
#   "properties": {
#     "provisioningState": "Succeeded",
#     "outputs": {
#       "storageAccountId": { "value": "/subscriptions/.../storageAccounts/stprodabc123" },
#       "primaryEndpoint": { "value": "https://stprodabc123.blob.core.windows.net/" }
#     }
#   }
# }

# Validate template (dry run, no deployment)
az deployment group validate \
  --resource-group rg-demo-eastus \
  --template-file main.json \
  --parameters storageAccountName=stprod

# What-if (preview changes)
az deployment group what-if \
  --resource-group rg-demo-eastus \
  --template-file main.json \
  --parameters storageAccountName=stprod

# Output shows what will be created/modified/deleted:
# Resource changes:
#   + Microsoft.Storage/storageAccounts/stprodabc123 [CREATE]

# Deploy from URL
az deployment group create \
  --resource-group rg-demo-eastus \
  --template-uri "https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/quickstarts/microsoft.storage/storage-account-create/azuredeploy.json"

# Export existing resource group as template
az group export --name rg-demo-eastus > exported-template.json
```

### Portal UI Walkthrough: Deploy an ARM Template from Azure Portal

```
PORTAL STEPS — Deploy a Custom ARM Template:

Step 1: Navigate to Custom Deployment
   → Search "Deploy a custom template" in the search bar
   → Click "Deploy a custom template"

Step 2: Choose a Template
   → Options:
     ● Build your own template in the editor
     ○ Select a quickstart template (pre-built examples)
     ○ Load a file (upload your .json template)
   → Click "Build your own template in the editor"

Step 3: Paste Your Template
   → Delete the default content
   → Paste your ARM template JSON (e.g., storage account template)
   → Click "Save"

Step 4: Fill in Parameters
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:         Select your subscription           │
   │ Resource group:       rg-demo-eastus (or create new)     │
   │ Region:               East US                            │
   │ Storage Account Name: stfromtemplate2024                  │
   │ SKU:                  Standard_LRS                       │
   │ (These fields come from the "parameters" in your template)│
   └─────────────────────────────────────────────────────────┘

Step 5: Review + Create
   → Click "Review + create"
   → Azure validates the template (checks for errors)
   → Click "Create"
   → Deployment starts — you can watch progress in real-time

Step 6: View Deployment History
   → Go to Resource group → Left sidebar → "Deployments"
   → You'll see all template deployments with status:
     ┌─────────────────────────────────────────────────────┐
     │ Name                  Status      Duration          │
     │ Microsoft.Template    Succeeded   45 seconds        │
     │ Microsoft.Template    Succeeded   1 minute          │
     └─────────────────────────────────────────────────────┘
   → Click a deployment to see inputs, outputs, and template used
```

### Portal UI Walkthrough: Export a Template from an Existing Resource

```
PORTAL STEPS — Export ARM Template from Existing Resources:

Step 1: Go to Any Resource
   → Go to any resource (e.g., a Storage Account, VM, etc.)

Step 2: Export Template
   → Left sidebar → "Export template"
   → Azure generates the ARM JSON template for that resource
   → You'll see the full JSON with all current settings

Step 3: Download or Deploy
   → Click "Download" to save the .json file
   → Click "Deploy" to redeploy with modifications
   → Click "Add to library" to save as a reusable template

Step 4: Export Entire Resource Group
   → Go to Resource group → Left sidebar → "Export template"
   → Azure generates a template for ALL resources in the group
   → Download and use to recreate the entire environment
   → ⚠️ Some resources may not export perfectly — review the template
```

### Portal UI Walkthrough: Use Quickstart Templates

```
PORTAL STEPS — Deploy from Azure Quickstart Templates:

Step 1: Browse Templates
   → Go to https://azure.microsoft.com/resources/templates/
   → Or search "Deploy a custom template" in Portal
   → Click "Select a quickstart template"

Step 2: Choose a Template
   → Browse categories or search:
     • "101-vm-simple-linux" — Simple Linux VM
     • "101-webapp-basic-linux" — Basic Web App
     • "101-sql-database" — SQL Database
     • "201-2-vms-loadbalancer" — 2 VMs with Load Balancer
   → Select a template → Click "Select template"

Step 3: Fill in Parameters and Deploy
   → Fill in the required parameters
   → Click "Review + create" → "Create"
   → The entire infrastructure deploys automatically
```

### Deployment Modes

```
Incremental (default):
- Adds new resources
- Leaves existing resources unchanged
- Does NOT delete resources not in template
- Safe for production

Complete:
- Adds new resources
- Modifies existing resources
- DELETES resources not in template
- ⚠️ Dangerous — can delete resources accidentally

az deployment group create \
  --resource-group rg-demo-eastus \
  --template-file main.json \
  --mode Complete    # Use with caution!
```

---

## 15.3 Bicep

### What is Bicep?
A domain-specific language (DSL) for deploying Azure resources. It compiles to ARM JSON but is much more readable and concise.

### Bicep vs ARM JSON

```
ARM JSON: ~30 lines for a storage account
Bicep:    ~10 lines for the same storage account

Bicep advantages:
├── Cleaner syntax (no JSON noise)
├── Type safety and IntelliSense in VS Code
├── Automatic dependency management
├── Modules for reusability
├── No state file needed (unlike Terraform)
└── First-class Azure support
```

### Bicep Examples

```bicep
// main.bicep - Storage Account

@description('Name of the storage account')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Location for the storage account')
param location string = resourceGroup().location

@allowed(['Standard_LRS', 'Standard_GRS', 'Standard_ZRS'])
param sku string = 'Standard_LRS'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: sku
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

output storageAccountId string = storageAccount.id
output primaryEndpoint string = storageAccount.properties.primaryEndpoints.blob
```

```bicep
// Complete web application infrastructure

param appName string
param location string = resourceGroup().location

// App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: '${appName}-plan'
  location: location
  sku: {
    name: 'S1'
    tier: 'Standard'
  }
  kind: 'linux'
  properties: {
    reserved: true  // Required for Linux
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: appName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'NODE|18-lts'
      alwaysOn: true
      httpsOnly: true
    }
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${appName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

// Connect App Insights to Web App
resource webAppSettings 'Microsoft.Web/sites/config@2023-01-01' = {
  parent: webApp
  name: 'appsettings'
  properties: {
    APPLICATIONINSIGHTS_CONNECTION_STRING: appInsights.properties.ConnectionString
  }
}

output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
```

### Deploying Bicep

```bash
# Deploy Bicep file (same command as ARM)
az deployment group create \
  --resource-group rg-demo-eastus \
  --template-file main.bicep \
  --parameters appName=mywebapp-2024

# What-if preview
az deployment group what-if \
  --resource-group rg-demo-eastus \
  --template-file main.bicep \
  --parameters appName=mywebapp-2024

# Compile Bicep to ARM JSON (for inspection)
az bicep build --file main.bicep
# Output: main.json

# Decompile ARM JSON to Bicep
az bicep decompile --file main.json
# Output: main.bicep
```

### Bicep Modules

```bicep
// modules/storage.bicep
param name string
param location string
param sku string = 'Standard_LRS'

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  sku: { name: sku }
  kind: 'StorageV2'
}

output id string = storage.id
output name string = storage.name
```

```bicep
// main.bicep - Using modules
param location string = resourceGroup().location

module storage 'modules/storage.bicep' = {
  name: 'storageDeployment'
  params: {
    name: 'stprod2024'
    location: location
    sku: 'Standard_GRS'
  }
}

output storageId string = storage.outputs.id
```

---

## 15.4 Terraform for Azure

### What is Terraform?
An open-source IaC tool by HashiCorp. Uses HCL (HashiCorp Configuration Language). Works with Azure, AWS, GCP, and many other providers.

```
Terraform vs Bicep:

Terraform:                          Bicep:
├── Multi-cloud                     ├── Azure only
├── State file required             ├── No state file
├── HCL language                    ├── Bicep language
├── Large community                 ├── Microsoft supported
├── Plan → Apply workflow           ├── What-if → Deploy
└── Provider updates needed         └── Always up-to-date with Azure
```

### Terraform Example

```hcl
# main.tf

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-terraform-demo"
  location = "East US"

  tags = {
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "stterraformdemo2024"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = {
    Environment = "Production"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "vnet-main"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

# Subnet
resource "azurerm_subnet" "web" {
  name                 = "web-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Output
output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "resource_group_id" {
  value = azurerm_resource_group.main.id
}
```

### Terraform Commands

```bash
# Initialize (download providers)
terraform init
# Output: Initializing provider plugins...
#         - Installing hashicorp/azurerm v3.85.0...

# Format code
terraform fmt

# Validate configuration
terraform validate
# Output: Success! The configuration is valid.

# Plan (preview changes)
terraform plan
# Output:
# Terraform will perform the following actions:
#   + azurerm_resource_group.main will be created
#   + azurerm_storage_account.main will be created
# Plan: 2 to add, 0 to change, 0 to destroy.

# Apply (deploy)
terraform apply
# Shows plan, asks for confirmation
# Type "yes" to proceed

# Apply without confirmation (CI/CD)
terraform apply -auto-approve

# Show current state
terraform show

# Destroy all resources
terraform destroy

# Import existing resource into state
terraform import azurerm_resource_group.main /subscriptions/SUB_ID/resourceGroups/rg-terraform-demo
```

### Terraform State

```
Terraform tracks deployed resources in a state file (terraform.tfstate).

Local state (default): terraform.tfstate in project directory
Remote state (recommended): Azure Storage Account

# Configure remote state
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}

⚠️ NEVER commit terraform.tfstate to Git (contains secrets)
⚠️ ALWAYS use remote state for team collaboration
```

---

## 15.5 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| ARM `InvalidTemplate` | JSON syntax error | Validate: `az deployment group validate` |
| Bicep `BCP001` | Syntax error in Bicep | Check VS Code Bicep extension for errors |
| `DeploymentFailed` | Resource creation error | Check inner error message for details |
| Terraform `state lock` | Another user running terraform | Wait or force unlock: `terraform force-unlock LOCK_ID` |
| Terraform `provider not found` | Missing `terraform init` | Run `terraform init` |
| `ResourceExistsError` | Resource already exists | Import into state or use `existing` keyword (Bicep) |
| ARM `InvalidParameterValue` | Parameter doesn't match allowed values | Check `allowedValues` in template |
| Bicep module not found | Wrong module path | Verify relative path to module file |

---

## 15.6 Practice Questions

### Question 1
**What language does Bicep compile to?**
- A) YAML
- B) ARM JSON ✅
- C) HCL
- D) PowerShell

### Question 2
**What is the default deployment mode for ARM templates?**
- A) Complete
- B) Incremental ✅
- C) Validate
- D) What-If

### Question 3
**Terraform requires a state file. Where should it be stored for team use?**
- A) Local filesystem
- B) Git repository
- C) Azure Storage Account (remote backend) ✅
- D) Azure Key Vault

### Question 4
**Which command previews ARM/Bicep changes without deploying?**
- A) `az deployment group validate`
- B) `az deployment group what-if` ✅
- C) `az deployment group create --dry-run`
- D) `az deployment group preview`

### Question 5
**Which IaC tool works with multiple cloud providers?**
- A) ARM Templates
- B) Bicep
- C) Terraform ✅
- D) Azure PowerShell

---

[← Previous Module](./Module-14-Cost-Management.md) | [Next Module: Governance & Compliance →](./Module-16-Governance-and-Compliance.md)
