# Module 07: Azure Identity & Security

## Certification Relevance: AZ-900 (25-30%), AZ-104 (15-20%)

---

## 7.1 Microsoft Entra ID (formerly Azure Active Directory)

### What is Entra ID?
Microsoft's cloud-based identity and access management service. It handles authentication (who are you?) and authorization (what can you do?).

```
On-Premises AD vs Entra ID:

Active Directory (AD DS)          Microsoft Entra ID
─────────────────────             ──────────────────
On-premises                       Cloud-based
Kerberos/NTLM authentication     OAuth 2.0 / OpenID Connect / SAML
Group Policy (GPO)                Conditional Access
Domain Controllers                No domain controllers
LDAP queries                      REST API (Microsoft Graph)
Organizational Units (OUs)        Flat structure (no OUs)
Forest/Domain trust               Tenant-based
```

### Key Concepts

```
Tenant:
  A dedicated instance of Entra ID for your organization.
  Every Azure subscription is associated with one tenant.
  Example: contoso.onmicrosoft.com

User:
  An identity in the directory (employee, contractor, etc.)
  Can be cloud-only or synced from on-premises AD.

Group:
  A collection of users for easier access management.
  Types: Security groups, Microsoft 365 groups

Service Principal:
  An identity for applications/services (like a "robot user").
  Used for automated deployments, CI/CD pipelines.

Managed Identity:
  Azure-managed service principal. No credentials to manage.
  System-assigned: Tied to one resource, deleted with it.
  User-assigned: Independent, can be shared across resources.

App Registration:
  Defines an application's identity in Entra ID.
  Used for SSO, API access, multi-tenant apps.
```

### Portal UI Walkthrough: Create a User in Entra ID

```
PORTAL STEPS — Create a New User:

Step 1: Navigate to Microsoft Entra ID
   → Search "Microsoft Entra ID" in the search bar
   → Click "Microsoft Entra ID" from results
   → You'll see your tenant overview (tenant name, tenant ID)

Step 2: Go to Users
   → Left sidebar → "Users"
   → You'll see a list of all users in your directory
   → Click "+ New user" → "Create new user"

Step 3: Fill in User Details
   ┌─ Identity ─────────────────────────────────────────────┐
   │ User principal name: john                               │
   │   @contoso.onmicrosoft.com (auto-filled domain)        │
   │ Display name:        John Doe                           │
   └────────────────────────────────────────────────────────┘
   ┌─ Password ─────────────────────────────────────────────┐
   │ ● Auto-generate password                                │
   │ ○ Let me create the password                            │
   │ ☑ Require password change at next sign-in               │
   │ → Copy the auto-generated password!                     │
   └────────────────────────────────────────────────────────┘
   ┌─ Properties (Optional) ────────────────────────────────┐
   │ First name:          John                               │
   │ Last name:           Doe                                │
   │ Job title:           Developer                          │
   │ Department:          Engineering                        │
   │ Usage location:      United States                      │
   │   (required for license assignment)                     │
   └────────────────────────────────────────────────────────┘

Step 4: Assignments (Optional)
   → Click "Next: Assignments >"
   → Click "+ Add group" to add user to groups
   → Select "Developers" group (if created)
   → Click "Select"

Step 5: Review + Create
   → Click "Review + create" → "Create"
   → User is created immediately
   → Share the username and temporary password with the user
```

### Portal UI Walkthrough: Create a Group

```
PORTAL STEPS — Create a Security Group:

Step 1: Navigate to Groups
   → Microsoft Entra ID → Left sidebar → "Groups"
   → Click "+ New group"

Step 2: Fill in Group Details
   ┌─────────────────────────────────────────────────────────┐
   │ Group type:         Security                             │
   │ Group name:         Developers                           │
   │ Group description:  Development team members             │
   │ Membership type:    Assigned                             │
   │   Options:                                               │
   │   • Assigned — manually add/remove members              │
   │   • Dynamic User — auto-add based on rules              │
   │     (e.g., department = "Engineering")                   │
   └─────────────────────────────────────────────────────────┘
   → Click "Members" → "+ Add members"
   → Search for users → Select them → Click "Select"
   → Click "Create"
```

### Portal UI Walkthrough: Assign RBAC Roles

```
PORTAL STEPS — Assign a Role to a User:

Step 1: Navigate to the Scope
   → Go to the resource where you want to assign the role:
     • Subscription level: Subscriptions → Click your subscription
     • Resource group level: Resource groups → Click "rg-demo-eastus"
     • Resource level: Go to the specific resource

Step 2: Open Access Control (IAM)
   → Left sidebar → "Access control (IAM)"
   → You'll see current role assignments

Step 3: Add Role Assignment
   → Click "+ Add" → "Add role assignment"

Step 4: Select Role
   → Search for the role you want to assign:
     ┌─────────────────────────────────────────────────────┐
     │ Search: "Contributor"                                │
     │                                                      │
     │ ☑ Contributor                                        │
     │   Full access to manage all resources, but cannot    │
     │   assign roles in Azure RBAC                         │
     │                                                      │
     │ Other common roles:                                  │
     │   Reader — View only                                 │
     │   Owner — Full access + can assign roles             │
     │   Virtual Machine Contributor — Manage VMs only      │
     │   Storage Blob Data Contributor — Manage blob data   │
     └─────────────────────────────────────────────────────┘
   → Select the role → Click "Next"

Step 5: Select Members
   → Assign access to: ● User, group, or service principal
   → Click "+ Select members"
   → Search for the user or group: "John Doe"
   → Click the user → Click "Select"

Step 6: Review + Assign
   → Click "Review + assign"
   → Review:
     ┌─────────────────────────────────────────────────────┐
     │ Role:    Contributor                                 │
     │ Scope:   rg-demo-eastus                             │
     │ Members: John Doe (john@contoso.onmicrosoft.com)    │
     └─────────────────────────────────────────────────────┘
   → Click "Review + assign" again to confirm

Step 7: Verify
   → Go to "Access control (IAM)" → "Role assignments" tab
   → You'll see:
     Name       Type   Role          Scope
     John Doe   User   Contributor   This resource group
```

### Portal UI Walkthrough: Create a Key Vault and Store Secrets

```
PORTAL STEPS — Create a Key Vault:

Step 1: Navigate to Key Vaults
   → Search "Key vaults" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Key vault name:     kv-demo-2024                         │
   │                     (globally unique)                    │
   │ Region:             East US                              │
   │ Pricing tier:       Standard                             │
   │   Standard = software-protected keys                    │
   │   Premium = HSM-protected keys                          │
   └─────────────────────────────────────────────────────────┘

Step 3: Access Configuration Tab
   → Click "Next: Access configuration >"
   ┌─────────────────────────────────────────────────────────┐
   │ Permission model:                                        │
   │   ● Azure role-based access control (recommended)       │
   │   ○ Vault access policy                                 │
   └─────────────────────────────────────────────────────────┘

Step 4: Review + Create
   → Click "Review + create" → "Create"

Step 5: Add a Secret
   → Go to resource → Left sidebar → "Secrets"
   → Click "+ Generate/Import"
   ┌─────────────────────────────────────────────────────────┐
   │ Upload options:     Manual                               │
   │ Name:               DatabasePassword                     │
   │ Secret value:       P@ssw0rd1234!                        │
   │ Content type:       password (optional label)            │
   │ Set activation date: ☐ (optional)                        │
   │ Set expiration date:  ☐ (optional)                       │
   │ Enabled:            ● Yes                                │
   │ Click "Create"                                           │
   └─────────────────────────────────────────────────────────┘

Step 6: View the Secret
   → Click "DatabasePassword" in the secrets list
   → Click the current version (GUID link)
   → Click "Show Secret Value" to reveal the password
   → Copy the "Secret Identifier" URL for use in applications:
     https://kv-demo-2024.vault.azure.net/secrets/DatabasePassword

Step 7: Add More Secrets
   → Repeat Step 5 for:
     Name: ApiKey           Value: abc123xyz
     Name: ConnectionString Value: Server=mydb.database.windows.net;...
```

### Managing Users with CLI

```bash
# Create a user
az ad user create \
  --display-name "John Doe" \
  --user-principal-name john@contoso.onmicrosoft.com \
  --password 'TempP@ss1234!' \
  --force-change-password-next-sign-in true

# Output:
# {
#   "displayName": "John Doe",
#   "id": "12345678-abcd-efgh-ijkl-123456789012",
#   "userPrincipalName": "john@contoso.onmicrosoft.com"
# }

# List all users
az ad user list --output table
# Output:
# DisplayName    UserPrincipalName                    ObjectId
# -----------    ---------------------------------    ------------------------------------
# John Doe       john@contoso.onmicrosoft.com         12345678-abcd-efgh-ijkl-123456789012
# Jane Smith     jane@contoso.onmicrosoft.com         87654321-dcba-hgfe-lkji-210987654321

# Show user details
az ad user show --id john@contoso.onmicrosoft.com

# Delete a user
az ad user delete --id john@contoso.onmicrosoft.com

# Update user properties
az ad user update \
  --id john@contoso.onmicrosoft.com \
  --display-name "John M. Doe" \
  --job-title "Senior Developer"
```

### Managing Groups

```bash
# Create a security group
az ad group create \
  --display-name "Developers" \
  --mail-nickname "developers"

# Add user to group
az ad group member add \
  --group "Developers" \
  --member-id "12345678-abcd-efgh-ijkl-123456789012"

# List group members
az ad group member list --group "Developers" --output table

# Check if user is in group
az ad group member check \
  --group "Developers" \
  --member-id "12345678-abcd-efgh-ijkl-123456789012"
# Output: { "value": true }

# Remove user from group
az ad group member remove \
  --group "Developers" \
  --member-id "12345678-abcd-efgh-ijkl-123456789012"
```

---

## 7.2 Role-Based Access Control (RBAC)

### What is RBAC?
A system for managing who has access to Azure resources, what they can do, and at what scope.

### RBAC Components

```
RBAC = Who (Security Principal) + What (Role) + Where (Scope)

Security Principal:     Role Definition:        Scope:
├── User               ├── Owner               ├── Management Group
├── Group              ├── Contributor          ├── Subscription
├── Service Principal  ├── Reader               ├── Resource Group
└── Managed Identity   ├── User Access Admin    └── Resource
                       └── Custom Roles
```

### Built-in Roles

| Role | Permissions | Use Case |
|------|------------|----------|
| **Owner** | Full access + can assign roles | Subscription admins |
| **Contributor** | Full access, CANNOT assign roles | Developers, DevOps |
| **Reader** | View only, no changes | Auditors, stakeholders |
| **User Access Administrator** | Manage user access only | Security team |
| **Storage Blob Data Contributor** | Read/write/delete blobs | App accessing storage |
| **Virtual Machine Contributor** | Manage VMs, not network/storage | VM administrators |
| **Network Contributor** | Manage networking resources | Network team |
| **SQL DB Contributor** | Manage SQL databases | Database admins |

### Assigning Roles

```bash
# Assign Reader role to a user at subscription scope
az role assignment create \
  --assignee john@contoso.onmicrosoft.com \
  --role "Reader" \
  --scope "/subscriptions/12345678-1234-1234-1234-123456789012"

# Meaning: John can VIEW all resources in the subscription but cannot modify anything

# Assign Contributor role at resource group scope
az role assignment create \
  --assignee john@contoso.onmicrosoft.com \
  --role "Contributor" \
  --resource-group rg-demo-eastus

# Meaning: John can create/modify/delete resources in rg-demo-eastus only

# Assign role to a group
az role assignment create \
  --assignee-object-id "GROUP_OBJECT_ID" \
  --assignee-principal-type Group \
  --role "Virtual Machine Contributor" \
  --resource-group rg-demo-eastus

# List role assignments
az role assignment list \
  --resource-group rg-demo-eastus \
  --output table

# Output:
# Principal          Role          Scope
# ----------------   -----------   ----------------------------------
# john@contoso...    Contributor   /subscriptions/.../rg-demo-eastus
# Developers         VM Contrib.   /subscriptions/.../rg-demo-eastus

# Remove a role assignment
az role assignment delete \
  --assignee john@contoso.onmicrosoft.com \
  --role "Contributor" \
  --resource-group rg-demo-eastus

# List all built-in roles
az role definition list --output table --query "[?roleType=='BuiltInRole'].{Name:roleName, Description:description}"
```

### RBAC Scope Hierarchy

```
Management Group (/providers/Microsoft.Management/managementGroups/mg1)
    │
    └── Subscription (/subscriptions/sub-id)
            │
            └── Resource Group (/subscriptions/sub-id/resourceGroups/rg-name)
                    │
                    └── Resource (/subscriptions/sub-id/resourceGroups/rg-name/providers/...)

Inheritance: Roles assigned at a higher scope are inherited by lower scopes.

Example: If John has "Reader" at Subscription level, he can read ALL
resource groups and ALL resources in that subscription.
```

### Custom Roles

```bash
# Create a custom role (JSON definition)
az role definition create --role-definition '{
  "Name": "VM Operator",
  "Description": "Can start, stop, and restart VMs but not create or delete them",
  "Actions": [
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Network/*/read",
    "Microsoft.Resources/subscriptions/resourceGroups/read"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/12345678-1234-1234-1234-123456789012"
  ]
}'

# Assign the custom role
az role assignment create \
  --assignee john@contoso.onmicrosoft.com \
  --role "VM Operator" \
  --resource-group rg-demo-eastus
```

### Exam Tip
```
AZ-104 question: "A user has Reader role at subscription level and
Contributor role at a resource group level. What can they do?"

Answer: At the resource group level, they have Contributor access
(most permissive role wins). At all other resource groups in the
subscription, they have Reader access.

RBAC is ADDITIVE — permissions are combined, never subtracted.
(Exception: Deny assignments override Allow)
```

---

## 7.3 Multi-Factor Authentication (MFA)

```
MFA = Something you KNOW (password)
    + Something you HAVE (phone, security key)
    + Something you ARE (fingerprint, face)

Methods:
1. Microsoft Authenticator app (push notification)
2. SMS verification code
3. Phone call
4. FIDO2 security key (hardware key)
5. Windows Hello for Business

Real-World Impact:
MFA blocks 99.9% of account compromise attacks.
Without MFA: Password stolen → Account compromised
With MFA: Password stolen → Attacker also needs your phone → Blocked
```

---

## 7.4 Conditional Access

### What is Conditional Access?
Policies that enforce access controls based on conditions (who, where, what device, risk level).

```
IF (condition) THEN (access control)

Examples:
IF user is outside corporate network
  THEN require MFA

IF user is accessing from unmanaged device
  THEN allow browser-only access (no downloads)

IF sign-in risk is HIGH
  THEN block access

IF user is an admin
  THEN always require MFA + compliant device
```

```
Real-World Example: A financial services company sets up:

Policy 1: "Require MFA for all users"
  - Assignments: All users
  - Conditions: All cloud apps
  - Grant: Require MFA

Policy 2: "Block legacy authentication"
  - Assignments: All users
  - Conditions: Client apps = Exchange ActiveSync, Other clients
  - Grant: Block access

Policy 3: "Require compliant device for sensitive apps"
  - Assignments: Finance team
  - Conditions: Finance applications
  - Grant: Require device compliance + MFA

Result: 95% reduction in security incidents
```

---

## 7.5 Azure Key Vault

### What is Key Vault?
A cloud service for securely storing and accessing secrets, keys, and certificates.

```
What Key Vault stores:
1. Secrets: Connection strings, passwords, API keys
2. Keys: Encryption keys (RSA, EC)
3. Certificates: SSL/TLS certificates

Why use Key Vault:
- Secrets are NOT in code or config files
- Centralized secret management
- Access logging and auditing
- Hardware Security Module (HSM) backed
- Automatic certificate renewal
```

### Creating and Using Key Vault

```bash
# Create a Key Vault
az keyvault create \
  --resource-group rg-demo-eastus \
  --name kv-demo-2024 \
  --location eastus \
  --sku standard

# Meaning:
# --sku standard : Software-protected keys (~$0.03/10K operations)
# --sku premium  : HSM-protected keys (~$1/key/month)

# Output:
# {
#   "name": "kv-demo-2024",
#   "vaultUri": "https://kv-demo-2024.vault.azure.net/"
# }

# --- SECRETS ---

# Store a secret
az keyvault secret set \
  --vault-name kv-demo-2024 \
  --name "DatabasePassword" \
  --value "P@ssw0rd1234!"

# Output:
# {
#   "name": "DatabasePassword",
#   "value": "P@ssw0rd1234!",
#   "id": "https://kv-demo-2024.vault.azure.net/secrets/DatabasePassword/abc123"
# }

# Retrieve a secret
az keyvault secret show \
  --vault-name kv-demo-2024 \
  --name "DatabasePassword" \
  --query value \
  --output tsv
# Output: P@ssw0rd1234!

# List all secrets
az keyvault secret list \
  --vault-name kv-demo-2024 \
  --output table

# Delete a secret (soft-delete, recoverable)
az keyvault secret delete \
  --vault-name kv-demo-2024 \
  --name "DatabasePassword"

# Recover a deleted secret
az keyvault secret recover \
  --vault-name kv-demo-2024 \
  --name "DatabasePassword"

# Purge a deleted secret (permanent, cannot recover)
az keyvault secret purge \
  --vault-name kv-demo-2024 \
  --name "DatabasePassword"

# --- KEYS ---

# Create an encryption key
az keyvault key create \
  --vault-name kv-demo-2024 \
  --name "EncryptionKey" \
  --kty RSA \
  --size 2048

# --- CERTIFICATES ---

# Create a self-signed certificate
az keyvault certificate create \
  --vault-name kv-demo-2024 \
  --name "WebCert" \
  --policy "$(az keyvault certificate get-default-policy)"
```

### Key Vault Access Policies

```bash
# Grant a user access to secrets
az keyvault set-policy \
  --name kv-demo-2024 \
  --upn john@contoso.onmicrosoft.com \
  --secret-permissions get list set delete

# Grant a managed identity access
az keyvault set-policy \
  --name kv-demo-2024 \
  --object-id "MANAGED_IDENTITY_OBJECT_ID" \
  --secret-permissions get list

# Grant an application access
az keyvault set-policy \
  --name kv-demo-2024 \
  --spn "APP_ID" \
  --secret-permissions get \
  --key-permissions encrypt decrypt

# Use RBAC instead of access policies (recommended)
az keyvault update \
  --name kv-demo-2024 \
  --resource-group rg-demo-eastus \
  --enable-rbac-authorization true

az role assignment create \
  --assignee john@contoso.onmicrosoft.com \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.KeyVault/vaults/kv-demo-2024"
```

### Real-World Example
```
Industry Example: A microservices application uses Key Vault:

1. Database connection string → stored in Key Vault
2. API keys for third-party services → stored in Key Vault
3. SSL certificates → managed by Key Vault (auto-renewal)
4. Each microservice has a Managed Identity
5. Each identity gets only the secrets it needs

Before Key Vault:
- Secrets in environment variables, config files, code
- Developers could see production passwords
- No audit trail of who accessed what

After Key Vault:
- Zero secrets in code
- Developers can't see production secrets
- Full audit log: "User X read secret Y at time Z"
- Automatic key rotation
```

---

## 7.6 Managed Identities

```bash
# Enable system-assigned managed identity on a VM
az vm identity assign \
  --resource-group rg-demo-eastus \
  --name vm-web-01

# Output:
# {
#   "systemAssignedIdentity": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
# }

# Grant the VM's identity access to Key Vault
az keyvault set-policy \
  --name kv-demo-2024 \
  --object-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
  --secret-permissions get list

# Now the VM can access Key Vault secrets WITHOUT any credentials
# The application on the VM uses the Azure SDK:
# Python: from azure.identity import DefaultAzureCredential
# Node.js: const { DefaultAzureCredential } = require("@azure/identity")

# Create a user-assigned managed identity (reusable)
az identity create \
  --resource-group rg-demo-eastus \
  --name id-webapp

# Assign to multiple resources
az webapp identity assign \
  --resource-group rg-demo-eastus \
  --name myapp-demo-12345 \
  --identities /subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-webapp
```

---

## 7.7 Microsoft Defender for Cloud

```
What it does:
1. Security posture management (Secure Score)
2. Threat protection for Azure resources
3. Compliance monitoring (PCI DSS, HIPAA, ISO 27001)
4. Vulnerability assessment
5. Just-in-time VM access

Secure Score:
- A percentage (0-100%) measuring your security posture
- Higher = more secure
- Recommendations to improve score
- Example: "Enable MFA for accounts with owner permissions" (+10 points)

Tiers:
- Free: Basic security recommendations, Secure Score
- Defender plans: Advanced threat protection per service (~$15/server/month)
```

---

## 7.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `AuthorizationFailed` | User lacks required RBAC role | Assign appropriate role at correct scope |
| `PrincipalNotFound` | User/group doesn't exist in Entra ID | Verify the principal exists: `az ad user show` |
| `RoleAssignmentExists` | Duplicate role assignment | Role already assigned; no action needed |
| `ForbiddenByPolicy` | Azure Policy blocking the action | Check policy assignments: `az policy assignment list` |
| `KeyVault: Access denied` | No access policy or RBAC role | Add access policy or assign Key Vault role |
| `SecretNotFound` | Wrong secret name or vault | Verify: `az keyvault secret list --vault-name NAME` |
| `Soft-delete enabled` | Can't purge vault immediately | Wait for retention period or purge: `az keyvault purge` |
| `MFA required` | Conditional Access policy enforcing MFA | Complete MFA verification |

---

## 7.9 Practice Questions

### Question 1
**Which RBAC role allows full access to resources but cannot assign roles to others?**
- A) Owner
- B) Contributor ✅
- C) Reader
- D) User Access Administrator

### Question 2
**What is a Managed Identity?**
- A) A user account managed by IT
- B) An Azure-managed identity for services that eliminates credential management ✅
- C) A group of users
- D) An encryption key

### Question 3
**RBAC role assignments are:**
- A) Subtractive (deny overrides allow)
- B) Additive (permissions combine) ✅
- C) Exclusive (only one role per user)
- D) Inherited downward only

### Question 4
**Which Key Vault object type stores connection strings and passwords?**
- A) Keys
- B) Secrets ✅
- C) Certificates
- D) Policies

### Question 5
**What does Conditional Access allow you to do?**
- A) Encrypt data at rest
- B) Enforce access controls based on conditions like location and device ✅
- C) Create virtual networks
- D) Monitor application performance

---

[← Previous Module](./Module-06-Databases.md) | [Next Module: Monitoring →](./Module-08-Monitoring-Logging-Alerts.md)
