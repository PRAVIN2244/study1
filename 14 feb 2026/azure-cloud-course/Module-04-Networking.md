# Module 04: Azure Networking

## Certification Relevance: AZ-104 (25-30%), AZ-900

---

## 4.1 Azure Virtual Network (VNet)

### What is a VNet?
A logically isolated network in Azure where you deploy resources. It's the foundation of Azure networking — similar to a traditional network in a data center.

### Real-World Analogy
```
Think of a VNet as your office building:
- The building = VNet (isolated from other buildings)
- Floors = Subnets (separate areas within the building)
- Security guards = NSGs (control who enters/exits)
- Reception desk = Load Balancer (directs visitors)
- Locked doors = Firewalls (block unauthorized access)
```

### Key Concepts

```
VNet: 10.0.0.0/16 (65,536 addresses)
├── Subnet: web-subnet     10.0.1.0/24 (256 addresses)
│   ├── VM: web-server-01  10.0.1.4
│   └── VM: web-server-02  10.0.1.5
├── Subnet: app-subnet     10.0.2.0/24 (256 addresses)
│   ├── VM: app-server-01  10.0.2.4
│   └── VM: app-server-02  10.0.2.5
├── Subnet: db-subnet      10.0.3.0/24 (256 addresses)
│   └── VM: db-server-01   10.0.3.4
└── Subnet: AzureBastionSubnet 10.0.4.0/26 (64 addresses)
    └── Bastion Host

Note: Azure reserves 5 IPs per subnet:
  .0 = Network address
  .1 = Default gateway
  .2 = DNS mapping
  .3 = DNS mapping
  .255 = Broadcast
So a /24 subnet has 251 usable IPs, not 256.
```

### Portal UI Walkthrough: Create a Virtual Network

```
PORTAL STEPS — Create a VNet with Subnets:

Step 1: Navigate to Virtual Networks
   → Search "Virtual networks" in the search bar
   → Click "Virtual networks" from results
   → Click "+ Create"

Step 2: Basics Tab
   ┌─ Project Details ──────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     Select "rg-demo-eastus"             │
   └────────────────────────────────────────────────────────┘
   ┌─ Instance Details ─────────────────────────────────────┐
   │ Virtual network name: vnet-main                         │
   │ Region:               (US) East US                      │
   └────────────────────────────────────────────────────────┘

Step 3: Security Tab
   → Click "Next: Security >"
   → Azure Bastion:    ☐ Disable (enable later if needed)
   → Azure Firewall:   ☐ Disable
   → Azure DDoS:       ☐ Disable
   → (Leave defaults for demo — enable for production)

Step 4: IP Addresses Tab
   → Click "Next: IP Addresses >"
   ┌─ Address Space ────────────────────────────────────────┐
   │ IPv4 address space: 10.0.0.0/16                        │
   │ (This gives you 65,536 IP addresses)                   │
   └────────────────────────────────────────────────────────┘
   → Delete the default subnet if one exists
   → Click "+ Add a subnet" to create subnets:

   Subnet 1:
   ┌─────────────────────────────────────────────────────────┐
   │ Subnet purpose:    Default                               │
   │ Name:              web-subnet                            │
   │ Starting address:  10.0.1.0                              │
   │ Subnet size:       /24 (256 addresses)                   │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

   Subnet 2: Click "+ Add a subnet" again
   ┌─────────────────────────────────────────────────────────┐
   │ Name:              app-subnet                            │
   │ Starting address:  10.0.2.0                              │
   │ Subnet size:       /24 (256 addresses)                   │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

   Subnet 3: Click "+ Add a subnet" again
   ┌─────────────────────────────────────────────────────────┐
   │ Name:              db-subnet                             │
   │ Starting address:  10.0.3.0                              │
   │ Subnet size:       /24 (256 addresses)                   │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 5: Tags → Review + Create
   → Add tags: Environment=Demo
   → Click "Review + create" → "Create"

Step 6: Verify
   → Click "Go to resource"
   → Left sidebar → "Subnets"
   → You'll see your 3 subnets listed with their address ranges
```

### Portal UI Walkthrough: Create and Configure an NSG

```
PORTAL STEPS — Create a Network Security Group:

Step 1: Navigate to NSGs
   → Search "Network security groups" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   → Subscription: Select your subscription
   → Resource group: rg-demo-eastus
   → Name: nsg-web
   → Region: East US
   → Click "Review + create" → "Create"

Step 3: Add Inbound Security Rules
   → Go to the NSG → Left sidebar → "Inbound security rules"
   → Click "+ Add"

   Rule 1 — Allow HTTP:
   ┌─────────────────────────────────────────────────────────┐
   │ Source:                    Any                           │
   │ Source port ranges:        *                             │
   │ Destination:               Any                           │
   │ Service:                   HTTP                          │
   │   (auto-fills port 80)                                   │
   │ Destination port ranges:   80                            │
   │ Protocol:                  TCP                           │
   │ Action:                    ● Allow                       │
   │ Priority:                  100                           │
   │ Name:                      AllowHTTP                     │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

   Rule 2 — Allow HTTPS: Click "+ Add" again
   ┌─────────────────────────────────────────────────────────┐
   │ Service:                   HTTPS                         │
   │ Destination port ranges:   443                           │
   │ Action:                    Allow                         │
   │ Priority:                  110                           │
   │ Name:                      AllowHTTPS                    │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

   Rule 3 — Allow SSH from your IP only: Click "+ Add"
   ┌─────────────────────────────────────────────────────────┐
   │ Source:                    IP Addresses                  │
   │ Source IP addresses:       <YOUR_PUBLIC_IP>              │
   │   (Google "what is my IP" to find yours)                │
   │ Destination port ranges:   22                            │
   │ Protocol:                  TCP                           │
   │ Action:                    Allow                         │
   │ Priority:                  120                           │
   │ Name:                      AllowSSH-MyIP                 │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 4: Associate NSG with a Subnet
   → Left sidebar → "Subnets"
   → Click "+ Associate"
   → Virtual network: vnet-main
   → Subnet: web-subnet
   → Click "OK"
   → Now all resources in web-subnet are protected by nsg-web

Step 5: Verify Rules
   → Left sidebar → "Inbound security rules"
   → You'll see your custom rules + default rules:
     Priority  Name              Port   Action
     100       AllowHTTP         80     Allow
     110       AllowHTTPS        443    Allow
     120       AllowSSH-MyIP     22     Allow
     65000     AllowVnetInBound  Any    Allow  (default)
     65500     DenyAllInBound    Any    Deny   (default)
```

### Portal UI Walkthrough: Create a Load Balancer

```
PORTAL STEPS — Create a Public Load Balancer:

Step 1: Navigate to Load Balancers
   → Search "Load balancers" in the search bar
   → Click "+ Create"

Step 2: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Name:               lb-web                               │
   │ Region:             East US                              │
   │ SKU:                Standard                             │
   │ Type:               ● Public  ○ Internal                 │
   │ Tier:               ● Regional                           │
   └─────────────────────────────────────────────────────────┘

Step 3: Frontend IP Configuration
   → Click "Next: Frontend IP configuration >"
   → Click "+ Add a frontend IP configuration"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               frontend-web                         │
   │ IP version:         IPv4                                 │
   │ IP type:            IP address                           │
   │ Public IP address:  Click "Create new"                   │
   │   Name:             pip-lb-web                           │
   │   SKU:              Standard                             │
   │   Assignment:       Static                               │
   │   Click "OK"                                             │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 4: Backend Pools
   → Click "Next: Backend pools >"
   → Click "+ Add a backend pool"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               backend-web                          │
   │ Virtual network:    vnet-main                            │
   │ Backend Pool        IP Address                           │
   │ Configuration:                                           │
   │ Click "+ Add" to add VMs:                                │
   │   ☑ vm-web-01                                            │
   │   ☑ vm-web-02                                            │
   │ Click "Add" → "Save"                                     │
   └─────────────────────────────────────────────────────────┘

Step 5: Inbound Rules
   → Click "Next: Inbound rules >"
   → Click "+ Add a load balancing rule"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               rule-http                            │
   │ IP Version:         IPv4                                 │
   │ Frontend IP:        frontend-web                         │
   │ Backend pool:       backend-web                          │
   │ Protocol:           TCP                                  │
   │ Port:               80                                   │
   │ Backend port:       80                                   │
   │ Health probe:       Click "Create new"                   │
   │   Name:             health-probe-http                    │
   │   Protocol:         HTTP                                 │
   │   Port:             80                                   │
   │   Path:             /                                    │
   │   Interval:         15 seconds                           │
   │   Click "OK"                                             │
   │ Session persistence: None                                │
   │ Idle timeout:       4 minutes                            │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 6: Review + Create
   → Click "Review + create" → "Create"

Step 7: Verify
   → Go to resource → "Backend pools" → Verify VMs are listed
   → Copy the Frontend IP address
   → Open browser → http://<FRONTEND_IP>
   → Traffic is now distributed across your VMs
```

### Creating a VNet with CLI

```bash
# Create a VNet with a subnet
az network vnet create \
  --resource-group rg-demo-eastus \
  --name vnet-main \
  --address-prefix 10.0.0.0/16 \
  --subnet-name web-subnet \
  --subnet-prefix 10.0.1.0/24 \
  --location eastus

# Meaning:
# --address-prefix 10.0.0.0/16 : VNet address space (65,536 IPs)
# --subnet-name web-subnet     : First subnet name
# --subnet-prefix 10.0.1.0/24  : Subnet range (251 usable IPs)

# Output:
# {
#   "newVNet": {
#     "name": "vnet-main",
#     "addressSpace": { "addressPrefixes": ["10.0.0.0/16"] },
#     "subnets": [
#       { "name": "web-subnet", "addressPrefix": "10.0.1.0/24" }
#     ]
#   }
# }

# Add more subnets
az network vnet subnet create \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name app-subnet \
  --address-prefix 10.0.2.0/24

az network vnet subnet create \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name db-subnet \
  --address-prefix 10.0.3.0/24

# List subnets
az network vnet subnet list \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --output table

# Output:
# Name          AddressPrefix    ProvisioningState
# -----------   ---------------  -----------------
# web-subnet    10.0.1.0/24      Succeeded
# app-subnet    10.0.2.0/24      Succeeded
# db-subnet     10.0.3.0/24      Succeeded

# Show VNet details
az network vnet show \
  --resource-group rg-demo-eastus \
  --name vnet-main \
  --output table
```

### CIDR Notation Quick Reference

```
/8   = 16,777,216 addresses  (255.0.0.0)
/16  = 65,536 addresses      (255.255.0.0)      ← Common for VNets
/24  = 256 addresses          (255.255.255.0)    ← Common for subnets
/25  = 128 addresses
/26  = 64 addresses           ← Minimum for some services (Bastion)
/27  = 32 addresses
/28  = 16 addresses
/29  = 8 addresses            ← Minimum for Gateway subnet
/32  = 1 address              (single host)
```

---

## 4.2 Network Security Groups (NSGs)

### What is an NSG?
A firewall that filters network traffic to and from Azure resources. Contains security rules that allow or deny inbound/outbound traffic.

### Default Rules (Cannot Be Deleted)

```
Inbound Default Rules:
Priority  Name                          Source          Dest    Port  Action
65000     AllowVnetInBound              VirtualNetwork  VNet    Any   Allow
65001     AllowAzureLoadBalancerInBound AzureLB         Any     Any   Allow
65500     DenyAllInBound                Any             Any     Any   Deny

Outbound Default Rules:
Priority  Name                          Source  Dest            Port  Action
65000     AllowVnetOutBound             VNet    VirtualNetwork  Any   Allow
65001     AllowInternetOutBound         Any     Internet        Any   Allow
65500     DenyAllOutBound               Any     Any             Any   Deny

Key: Lower priority number = higher priority (processed first)
Range: 100-4096 for custom rules
```

### Creating and Managing NSGs

```bash
# Create an NSG
az network nsg create \
  --resource-group rg-demo-eastus \
  --name nsg-web

# Add rule: Allow HTTP (port 80) from internet
az network nsg rule create \
  --resource-group rg-demo-eastus \
  --nsg-name nsg-web \
  --name AllowHTTP \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "*" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges 80

# Meaning:
# --priority 100        : Processed before rules with higher numbers
# --direction Inbound   : Controls incoming traffic
# --access Allow        : Permits the traffic
# --protocol Tcp        : Only TCP traffic
# --source "*"          : From any source
# --destination-port 80 : To port 80 (HTTP)

# Add rule: Allow HTTPS (port 443)
az network nsg rule create \
  --resource-group rg-demo-eastus \
  --nsg-name nsg-web \
  --name AllowHTTPS \
  --priority 110 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "*" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges 443

# Add rule: Allow SSH only from specific IP
az network nsg rule create \
  --resource-group rg-demo-eastus \
  --nsg-name nsg-web \
  --name AllowSSH \
  --priority 120 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes "203.0.113.50" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges 22

# Add rule: Deny all other inbound (explicit)
az network nsg rule create \
  --resource-group rg-demo-eastus \
  --nsg-name nsg-web \
  --name DenyAllInbound \
  --priority 4096 \
  --direction Inbound \
  --access Deny \
  --protocol "*" \
  --source-address-prefixes "*" \
  --source-port-ranges "*" \
  --destination-address-prefixes "*" \
  --destination-port-ranges "*"

# Associate NSG with a subnet
az network vnet subnet update \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name web-subnet \
  --network-security-group nsg-web

# Associate NSG with a NIC (network interface)
az network nic update \
  --resource-group rg-demo-eastus \
  --name vm-web-01VMNic \
  --network-security-group nsg-web

# List NSG rules
az network nsg rule list \
  --resource-group rg-demo-eastus \
  --nsg-name nsg-web \
  --output table

# Output:
# Name             Priority  Direction  Access  Protocol  SourceAddr  DestPort
# ---------------  --------  ---------  ------  --------  ----------  --------
# AllowHTTP        100       Inbound    Allow   Tcp       *           80
# AllowHTTPS       110       Inbound    Allow   Tcp       *           443
# AllowSSH         120       Inbound    Allow   Tcp       203.0.113.50 22
# DenyAllInbound   4096      Inbound    Deny    *         *           *
```

### NSG Best Practices
```
1. Apply NSGs at the subnet level (not NIC) for easier management
2. Use Application Security Groups (ASGs) to group VMs logically
3. Never open port 22 (SSH) or 3389 (RDP) to the internet
4. Use Azure Bastion for secure VM access instead
5. Log NSG flow logs for auditing and troubleshooting
```

---

## 4.3 Azure Load Balancer

### What is Azure Load Balancer?
Distributes incoming network traffic across multiple VMs to ensure no single VM is overwhelmed.

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  Load Balancer │
              │  (Public IP)   │
              └───────┬────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │  VM-1   │ │  VM-2   │ │  VM-3   │
     │ (healthy)│ │(healthy)│ │(healthy)│
     └─────────┘ └─────────┘ └─────────┘

If VM-2 fails health check:
          ┌───────────┼───────────┐
          ▼           ✗           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │  VM-1   │ │  VM-2   │ │  VM-3   │
     │ (healthy)│ │ (down)  │ │(healthy)│
     └─────────┘ └─────────┘ └─────────┘
     Traffic goes only to VM-1 and VM-3
```

### Types of Load Balancers

| Feature | Basic | Standard |
|---------|-------|----------|
| Backend pool size | Up to 300 | Up to 1,000 |
| Health probes | TCP, HTTP | TCP, HTTP, HTTPS |
| Availability Zones | No | Yes |
| SLA | None | 99.99% |
| NSG required | No | Yes (must explicitly allow) |
| Cost | Free | ~$18/month + data |

### Creating a Load Balancer

```bash
# Create a public IP for the load balancer
az network public-ip create \
  --resource-group rg-demo-eastus \
  --name pip-lb-web \
  --sku Standard \
  --allocation-method Static

# Create the load balancer
az network lb create \
  --resource-group rg-demo-eastus \
  --name lb-web \
  --sku Standard \
  --public-ip-address pip-lb-web \
  --frontend-ip-name frontend-web \
  --backend-pool-name backend-web

# Create a health probe
az network lb probe create \
  --resource-group rg-demo-eastus \
  --lb-name lb-web \
  --name health-probe-http \
  --protocol Http \
  --port 80 \
  --path "/"
# Meaning: Check port 80 with HTTP GET / every 15 seconds
# If 2 consecutive failures → mark VM as unhealthy

# Create a load balancing rule
az network lb rule create \
  --resource-group rg-demo-eastus \
  --lb-name lb-web \
  --name rule-http \
  --protocol Tcp \
  --frontend-port 80 \
  --backend-port 80 \
  --frontend-ip-name frontend-web \
  --backend-pool-name backend-web \
  --probe-name health-probe-http \
  --idle-timeout 4

# Meaning:
# Traffic arriving on frontend port 80 → distributed to backend port 80
# Uses health-probe-http to check VM health
# idle-timeout 4: Close idle connections after 4 minutes

# Add VMs to backend pool (via NIC)
az network nic ip-config address-pool add \
  --resource-group rg-demo-eastus \
  --nic-name vm-web-01VMNic \
  --ip-config-name ipconfig1 \
  --lb-name lb-web \
  --address-pool backend-web
```

### Internal Load Balancer
```bash
# For internal (private) traffic between tiers
az network lb create \
  --resource-group rg-demo-eastus \
  --name lb-internal \
  --sku Standard \
  --vnet-name vnet-main \
  --subnet app-subnet \
  --frontend-ip-name frontend-internal \
  --backend-pool-name backend-app \
  --private-ip-address 10.0.2.100

# Use case: Web tier → Internal LB → App tier
# The internal LB has a private IP (10.0.2.100), not accessible from internet
```

---

## 4.4 Azure Application Gateway

### What is Application Gateway?
A Layer 7 (HTTP/HTTPS) load balancer with advanced features like URL-based routing, SSL termination, and Web Application Firewall (WAF).

```
                    Internet
                       │
                       ▼
              ┌────────────────────┐
              │ Application Gateway│
              │ (Layer 7 - HTTP)   │
              │                    │
              │ URL Routing:       │
              │ /api/*  → Pool A   │
              │ /images/* → Pool B │
              │ /*      → Pool C   │
              └────────┬───────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     Pool A        Pool B       Pool C
     (API VMs)     (CDN/Storage) (Web VMs)
```

### Load Balancer vs Application Gateway

| Feature | Load Balancer | Application Gateway |
|---------|--------------|-------------------|
| OSI Layer | Layer 4 (TCP/UDP) | Layer 7 (HTTP/HTTPS) |
| URL routing | No | Yes |
| SSL termination | No | Yes |
| WAF | No | Yes |
| Cookie affinity | No | Yes |
| WebSocket | Yes | Yes |
| Cost | Lower | Higher |
| Use case | TCP/UDP traffic | Web applications |

---

## 4.5 Azure DNS

### What is Azure DNS?
A hosting service for DNS domains that provides name resolution using Microsoft Azure infrastructure.

```bash
# Create a DNS zone
az network dns zone create \
  --resource-group rg-demo-eastus \
  --name mycompany.com

# Output:
# {
#   "name": "mycompany.com",
#   "nameServers": [
#     "ns1-01.azure-dns.com.",
#     "ns2-01.azure-dns.net.",
#     "ns3-01.azure-dns.org.",
#     "ns4-01.azure-dns.info."
#   ]
# }
# → Update your domain registrar to use these name servers

# Add an A record (points domain to IP)
az network dns record-set a add-record \
  --resource-group rg-demo-eastus \
  --zone-name mycompany.com \
  --record-set-name www \
  --ipv4-address 20.185.100.50

# Meaning: www.mycompany.com → 20.185.100.50

# Add a CNAME record (alias)
az network dns record-set cname set-record \
  --resource-group rg-demo-eastus \
  --zone-name mycompany.com \
  --record-set-name blog \
  --cname myblog.azurewebsites.net

# Meaning: blog.mycompany.com → myblog.azurewebsites.net

# Add an MX record (email)
az network dns record-set mx add-record \
  --resource-group rg-demo-eastus \
  --zone-name mycompany.com \
  --record-set-name "@" \
  --exchange mail.mycompany.com \
  --preference 10

# List all records
az network dns record-set list \
  --resource-group rg-demo-eastus \
  --zone-name mycompany.com \
  --output table

# Private DNS Zone (for internal name resolution)
az network private-dns zone create \
  --resource-group rg-demo-eastus \
  --name internal.mycompany.com

# Link private DNS to VNet
az network private-dns link vnet create \
  --resource-group rg-demo-eastus \
  --zone-name internal.mycompany.com \
  --name link-vnet-main \
  --virtual-network vnet-main \
  --registration-enabled true
# --registration-enabled true: Auto-register VM DNS records
```

---

## 4.6 VNet Peering

### What is VNet Peering?
Connects two VNets so resources in both can communicate using private IP addresses. Traffic stays on the Microsoft backbone network (never goes to the internet).

```
Before Peering:
┌──────────────┐          ┌──────────────┐
│  VNet-A      │    ✗     │  VNet-B      │
│  10.0.0.0/16 │ No comm  │  10.1.0.0/16 │
└──────────────┘          └──────────────┘

After Peering:
┌──────────────┐  Peering  ┌──────────────┐
│  VNet-A      │◄────────►│  VNet-B      │
│  10.0.0.0/16 │  Private  │  10.1.0.0/16 │
└──────────────┘  Network  └──────────────┘
```

```bash
# Create VNet peering (must be done from BOTH sides)

# VNet-A → VNet-B
az network vnet peering create \
  --resource-group rg-demo-eastus \
  --name peer-a-to-b \
  --vnet-name vnet-a \
  --remote-vnet /subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Network/virtualNetworks/vnet-b \
  --allow-vnet-access

# VNet-B → VNet-A
az network vnet peering create \
  --resource-group rg-demo-eastus \
  --name peer-b-to-a \
  --vnet-name vnet-b \
  --remote-vnet /subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Network/virtualNetworks/vnet-a \
  --allow-vnet-access

# Check peering status
az network vnet peering list \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-a \
  --output table

# Output:
# Name          PeeringState    AllowVnetAccess
# -----------   --------------  ---------------
# peer-a-to-b   Connected       True
```

### Peering Rules
```
1. Address spaces MUST NOT overlap (10.0.0.0/16 and 10.0.0.0/16 = ERROR)
2. Peering is NOT transitive (A↔B and B↔C does NOT mean A↔C)
3. Can peer across regions (Global VNet Peering)
4. Can peer across subscriptions
5. Can peer across Azure AD tenants
```

---

## 4.7 Azure Bastion

### What is Azure Bastion?
A PaaS service that provides secure RDP/SSH access to VMs directly through the Azure Portal — without exposing VMs to the public internet.

```
Without Bastion (risky):
Internet → Public IP → VM (port 22/3389 open to internet)

With Bastion (secure):
User → Azure Portal → Bastion → Private IP → VM
(No public IP needed on VM, no ports exposed)
```

```bash
# Create Bastion subnet (must be named exactly "AzureBastionSubnet")
az network vnet subnet create \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name AzureBastionSubnet \
  --address-prefix 10.0.4.0/26

# Create public IP for Bastion
az network public-ip create \
  --resource-group rg-demo-eastus \
  --name pip-bastion \
  --sku Standard \
  --allocation-method Static

# Create Bastion host
az network bastion create \
  --resource-group rg-demo-eastus \
  --name bastion-main \
  --public-ip-address pip-bastion \
  --vnet-name vnet-main \
  --sku Standard

# Connect to VM via Bastion (from Portal):
# 1. Go to VM in Portal
# 2. Click "Connect" → "Bastion"
# 3. Enter username/password
# 4. Browser-based RDP/SSH session opens
```

---

## 4.8 Network Watcher

```bash
# Enable Network Watcher
az network watcher configure \
  --resource-group rg-demo-eastus \
  --locations eastus \
  --enabled true

# IP flow verify (test if traffic is allowed)
az network watcher test-ip-flow \
  --resource-group rg-demo-eastus \
  --vm vm-web-01 \
  --direction Inbound \
  --protocol Tcp \
  --local 10.0.1.4:80 \
  --remote 203.0.113.50:12345

# Output:
# {
#   "access": "Allow",
#   "ruleName": "AllowHTTP"
# }
# Meaning: Traffic from 203.0.113.50 to VM port 80 is ALLOWED by rule "AllowHTTP"

# Next hop (trace routing)
az network watcher show-next-hop \
  --resource-group rg-demo-eastus \
  --vm vm-web-01 \
  --source-ip 10.0.1.4 \
  --dest-ip 10.0.2.4

# Output:
# {
#   "nextHopType": "VnetLocal",
#   "nextHopIpAddress": null
# }
# Meaning: Traffic goes directly within the VNet (no extra hops)

# NSG flow logs (enable for auditing)
az network watcher flow-log create \
  --resource-group rg-demo-eastus \
  --name flowlog-nsg-web \
  --nsg nsg-web \
  --storage-account mystorageaccount \
  --enabled true \
  --retention 30
```

---

## 4.9 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `AddressSpaceOverlap` | VNet peering with overlapping CIDR | Use non-overlapping address spaces |
| `SubnetInUse` | Trying to delete subnet with resources | Remove all resources from subnet first |
| `NetworkSecurityGroupCannotBeAttached` | Wrong NSG SKU or region mismatch | Ensure NSG and resource are in same region |
| `InUseSubnetCannotBeUpdated` | Modifying subnet with active resources | Deallocate resources, modify, redeploy |
| VM can't reach internet | NSG blocking outbound or no route | Check NSG outbound rules and route tables |
| VMs in same VNet can't communicate | NSG blocking VNet traffic | Check NSG rules; ensure AllowVnetInBound exists |
| Bastion connection fails | Wrong subnet name or size | Subnet MUST be named "AzureBastionSubnet" with /26 or larger |
| DNS resolution fails | Private DNS zone not linked to VNet | Create VNet link to private DNS zone |

### Troubleshooting Connectivity

```bash
# Step 1: Check if VM is running
az vm get-instance-view --resource-group rg --name vm --query instanceView.statuses[1]

# Step 2: Check NSG rules
az network nsg rule list --resource-group rg --nsg-name nsg --output table

# Step 3: Test IP flow
az network watcher test-ip-flow --vm vm --direction Inbound --protocol Tcp --local 10.0.1.4:80 --remote 0.0.0.0:0

# Step 4: Check effective routes
az network nic show-effective-route-table --resource-group rg --name vmNic --output table

# Step 5: Check effective NSG rules
az network nic list-effective-nsg --resource-group rg --name vmNic
```

---

## 4.10 Practice Questions

### Question 1
**How many IP addresses does Azure reserve in each subnet?**
- A) 3
- B) 5 ✅
- C) 8
- D) 10

**Explanation**: Azure reserves 5 IPs: .0 (network), .1 (gateway), .2 and .3 (DNS), .255 (broadcast).

### Question 2
**VNet peering is transitive. True or False?**
- A) True
- B) False ✅

**Explanation**: Peering is NOT transitive. If VNet-A peers with VNet-B, and VNet-B peers with VNet-C, VNet-A cannot communicate with VNet-C unless directly peered.

### Question 3
**What is the required subnet name for Azure Bastion?**
- A) BastionSubnet
- B) AzureBastionSubnet ✅
- C) bastion-subnet
- D) Any name

### Question 4
**Which load balancer type supports URL-based routing?**
- A) Azure Load Balancer
- B) Azure Application Gateway ✅
- C) Azure Traffic Manager
- D) Azure Front Door

### Question 5
**A Standard Load Balancer requires which of the following?**
- A) Basic public IP
- B) NSG on backend VMs ✅
- C) VPN Gateway
- D) Application Gateway

---

[← Previous Module](./Module-03-Compute-Services.md) | [Next Module: Storage →](./Module-05-Storage.md)
