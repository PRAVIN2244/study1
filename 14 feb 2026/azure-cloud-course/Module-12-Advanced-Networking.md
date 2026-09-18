# Module 12: Advanced Networking

## Certification Relevance: AZ-104 (25-30%)

---

## 12.1 VPN Gateway

### What is VPN Gateway?
A virtual network gateway that sends encrypted traffic between an Azure VNet and on-premises networks (or other VNets) over the public internet.

```
Site-to-Site VPN (S2S):
┌──────────────┐    Encrypted IPsec Tunnel    ┌──────────────┐
│  On-Premises │◄────────────────────────────►│  Azure VNet  │
│  Network     │    Over Public Internet       │  10.0.0.0/16 │
│  192.168.0.0 │                               │              │
│              │    VPN Device ←→ VPN Gateway   │              │
└──────────────┘                               └──────────────┘

Point-to-Site VPN (P2S):
┌──────────────┐    Encrypted Tunnel           ┌──────────────┐
│  Individual  │◄────────────────────────────►│  Azure VNet  │
│  Laptop/PC   │    VPN Client ←→ VPN Gateway  │              │
└──────────────┘                               └──────────────┘
```

### VPN Gateway SKUs

| SKU | Tunnels | Throughput | Use Case | Cost/month* |
|-----|---------|-----------|----------|-------------|
| VpnGw1 | 30 S2S | 650 Mbps | Small office | ~$140 |
| VpnGw2 | 30 S2S | 1 Gbps | Medium business | ~$360 |
| VpnGw3 | 30 S2S | 1.25 Gbps | Large enterprise | ~$950 |
| VpnGw4 | 100 S2S | 5 Gbps | High performance | ~$1,700 |
| VpnGw5 | 100 S2S | 10 Gbps | Maximum throughput | ~$3,400 |

### Portal UI Walkthrough: Create a VPN Gateway

```
PORTAL STEPS — Create a VPN Gateway (Site-to-Site):

Step 1: Create the Gateway Subnet
   → Go to Virtual networks → Click "vnet-main"
   → Left sidebar → "Subnets"
   → Click "+ Gateway subnet"
   ┌─────────────────────────────────────────────────────────┐
   │ ⚠️ Name is auto-filled as "GatewaySubnet" (cannot      │
   │    change — Azure requires this exact name)             │
   │ Subnet address range: 10.0.255.0/27                     │
   │   (minimum /27 — 32 addresses)                          │
   │ Click "Save"                                            │
   └─────────────────────────────────────────────────────────┘

Step 2: Create the VPN Gateway
   → Search "Virtual network gateways" in the search bar
   → Click "+ Create"
   ┌─ Basics Tab ───────────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Name:               vpn-gw-main                         │
   │ Region:             East US                             │
   │ Gateway type:       ● VPN  ○ ExpressRoute               │
   │ SKU:                VpnGw1 (~$140/month)                │
   │ Generation:         Generation 2                        │
   │ Virtual network:    vnet-main                           │
   │ Subnet:             GatewaySubnet (auto-selected)       │
   │ Public IP address:  Create new                          │
   │   Name:             pip-vpn-gateway                     │
   │ Enable active-active: ○ Disabled                        │
   │ Click "Review + create" → "Create"                      │
   └─────────────────────────────────────────────────────────┘
   → ⚠️ VPN Gateway takes 30-45 minutes to deploy!

Step 3: Create a Local Network Gateway (Your On-Premises)
   → Search "Local network gateways" → Click "+ Create"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               lng-onprem-office                    │
   │ IP address:         203.0.113.100                        │
   │   (your on-premises VPN device's public IP)             │
   │ Address space:      192.168.0.0/16                       │
   │   (your on-premises network range)                      │
   │ Click "Review + create" → "Create"                      │
   └─────────────────────────────────────────────────────────┘

Step 4: Create the VPN Connection
   → Go to your VPN Gateway → Left sidebar → "Connections"
   → Click "+ Add"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               conn-to-office                       │
   │ Connection type:    Site-to-site (IPsec)                 │
   │ Local network gateway: lng-onprem-office                 │
   │ Shared key (PSK):   MySecretKey123!                      │
   │   (must match on your on-premises VPN device)           │
   │ Click "OK"                                               │
   └─────────────────────────────────────────────────────────┘

Step 5: Verify Connection
   → Go to VPN Gateway → "Connections"
   → Status should show "Connected" (may take a few minutes)
   → If "NotConnected": Check shared key and on-prem device config
```

### Portal UI Walkthrough: Create an Azure Firewall

```
PORTAL STEPS — Create and Configure Azure Firewall:

Step 1: Create the Firewall Subnet
   → Go to Virtual networks → vnet-main → Subnets
   → Click "+ Subnet"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               AzureFirewallSubnet                  │
   │   ⚠️ Must be exactly this name                          │
   │ Subnet address range: 10.0.5.0/26                       │
   │   (minimum /26 — 64 addresses)                          │
   │ Click "Save"                                            │
   └─────────────────────────────────────────────────────────┘

Step 2: Create the Firewall
   → Search "Firewalls" in the search bar
   → Click "+ Create"
   ┌─ Basics Tab ───────────────────────────────────────────┐
   │ Subscription:       Select your subscription            │
   │ Resource group:     rg-demo-eastus                      │
   │ Name:               fw-main                             │
   │ Region:             East US                             │
   │ Firewall SKU:       Standard                            │
   │ Firewall management: Use Firewall rules (classic)       │
   │ Virtual network:    Use existing → vnet-main            │
   │ Public IP address:  Add new → pip-firewall              │
   │ Click "Review + create" → "Create"                      │
   └─────────────────────────────────────────────────────────┘
   → Deployment takes 5-10 minutes

Step 3: Add Application Rules (Allow Web Traffic)
   → Go to Firewall → Left sidebar → "Rules (classic)"
   → Click "Application rule collection" tab → "+ Add"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               AllowWeb                             │
   │ Priority:           100                                  │
   │ Action:             Allow                                │
   │ Rules:                                                   │
   │   Name:             AllowGoogle                          │
   │   Source:           10.0.0.0/16                          │
   │   Protocol:Port:    https:443                            │
   │   Target FQDNs:     *.google.com, *.microsoft.com       │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 4: Add Network Rules (Allow DNS)
   → Click "Network rule collection" tab → "+ Add"
   ┌─────────────────────────────────────────────────────────┐
   │ Name:               AllowDNS                             │
   │ Priority:           200                                  │
   │ Action:             Allow                                │
   │ Rules:                                                   │
   │   Name:             DNS                                  │
   │   Protocol:         UDP                                  │
   │   Source:           10.0.0.0/16                          │
   │   Destination:      8.8.8.8, 8.8.4.4                    │
   │   Destination Ports: 53                                  │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘

Step 5: Route Traffic Through Firewall
   → Search "Route tables" → Click "+ Create"
   → Name: rt-firewall, Region: East US → Create
   → Go to route table → "Routes" → "+ Add"
   ┌─────────────────────────────────────────────────────────┐
   │ Route name:         default-to-firewall                  │
   │ Destination type:   IP Addresses                         │
   │ Destination:        0.0.0.0/0                            │
   │ Next hop type:      Virtual appliance                    │
   │ Next hop address:   10.0.5.4 (Firewall private IP)      │
   │ Click "Add"                                              │
   └─────────────────────────────────────────────────────────┘
   → Go to "Subnets" → "+ Associate"
   → VNet: vnet-main, Subnet: web-subnet → Click "OK"
   → Now all web-subnet traffic goes through the firewall
```

### Portal UI Walkthrough: Create a Private Endpoint

```
PORTAL STEPS — Create a Private Endpoint for a Storage Account:

Step 1: Go to Your Storage Account
   → Storage accounts → Click your storage account

Step 2: Open Networking Settings
   → Left sidebar → "Networking"
   → Click "Private endpoint connections" tab
   → Click "+ Private endpoint"

Step 3: Basics Tab
   ┌─────────────────────────────────────────────────────────┐
   │ Subscription:       Select your subscription             │
   │ Resource group:     rg-demo-eastus                       │
   │ Name:               pe-storage-blob                      │
   │ Network Interface Name: pe-storage-blob-nic              │
   │ Region:             East US                              │
   └─────────────────────────────────────────────────────────┘

Step 4: Resource Tab
   → Click "Next: Resource >"
   ┌─────────────────────────────────────────────────────────┐
   │ Target sub-resource: blob                                │
   │   (Options: blob, file, queue, table, web, dfs)         │
   └─────────────────────────────────────────────────────────┘

Step 5: Virtual Network Tab
   → Click "Next: Virtual Network >"
   ┌─────────────────────────────────────────────────────────┐
   │ Virtual network:    vnet-main                            │
   │ Subnet:             db-subnet                            │
   │ Private IP:         Dynamic (auto-assigned, e.g. 10.0.3.10)│
   └─────────────────────────────────────────────────────────┘

Step 6: DNS Tab
   → Click "Next: DNS >"
   → Integrate with private DNS zone: ● Yes
   → Private DNS zone: privatelink.blob.core.windows.net
   → (Azure auto-creates DNS so VMs resolve the storage
      account name to the private IP)

Step 7: Review + Create
   → Click "Review + create" → "Create"

Step 8: Disable Public Access (Optional but Recommended)
   → Go to Storage account → Networking
   → Public network access: ● Disabled
   → Now the storage account is ONLY accessible via private endpoint
   → VMs in vnet-main can access it; internet cannot

Step 9: Verify
   → SSH into a VM in vnet-main
   → nslookup stprodeastus2024.blob.core.windows.net
   → Should resolve to 10.0.3.10 (private IP), not a public IP
```

```bash
# Step 1: Create Gateway Subnet (must be named "GatewaySubnet")
az network vnet subnet create \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name GatewaySubnet \
  --address-prefix 10.0.255.0/27

# Step 2: Create Public IP for VPN Gateway
az network public-ip create \
  --resource-group rg-demo-eastus \
  --name pip-vpn-gateway \
  --allocation-method Static \
  --sku Standard

# Step 3: Create VPN Gateway (takes 30-45 minutes)
az network vnet-gateway create \
  --resource-group rg-demo-eastus \
  --name vpn-gateway-main \
  --vnet vnet-main \
  --gateway-type Vpn \
  --vpn-type RouteBased \
  --sku VpnGw1 \
  --public-ip-address pip-vpn-gateway \
  --no-wait

# Step 4: Create Local Network Gateway (represents on-premises)
az network local-gateway create \
  --resource-group rg-demo-eastus \
  --name lng-onprem \
  --gateway-ip-address 203.0.113.100 \
  --local-address-prefixes 192.168.0.0/16

# Meaning:
# --gateway-ip-address : Public IP of on-premises VPN device
# --local-address-prefixes : On-premises network ranges

# Step 5: Create VPN Connection
az network vpn-connection create \
  --resource-group rg-demo-eastus \
  --name conn-to-onprem \
  --vnet-gateway1 vpn-gateway-main \
  --local-gateway2 lng-onprem \
  --shared-key "MySharedKey123!" \
  --connection-protocol IKEv2

# Check connection status
az network vpn-connection show \
  --resource-group rg-demo-eastus \
  --name conn-to-onprem \
  --query connectionStatus
# Output: "Connected" or "Connecting"
```

---

## 12.2 ExpressRoute

### What is ExpressRoute?
A private, dedicated connection between your on-premises network and Azure. Traffic does NOT go over the public internet.

```
VPN Gateway:
On-Premises ──── Public Internet (encrypted) ──── Azure
                 Shared bandwidth, variable latency

ExpressRoute:
On-Premises ──── Private Connection (dedicated) ──── Azure
                 via connectivity provider (AT&T, Equinix, etc.)
                 Guaranteed bandwidth, consistent latency
```

### VPN vs ExpressRoute

| Feature | VPN Gateway | ExpressRoute |
|---------|------------|-------------|
| Connection | Over internet | Private dedicated |
| Encryption | IPsec encrypted | Not encrypted by default |
| Bandwidth | Up to 10 Gbps | Up to 100 Gbps |
| Latency | Variable | Consistent, low |
| Cost | ~$140-3,400/month | ~$55-16,000/month + provider fees |
| Setup time | Minutes | Weeks (provider provisioning) |
| Redundancy | Active-passive | Built-in redundancy |
| Use case | Small/medium, dev/test | Enterprise, compliance, high bandwidth |

```
Real-World Example: A bank with strict compliance requirements:
- Cannot send financial data over the public internet
- Needs 10 Gbps bandwidth for database replication
- Requires <5ms latency for trading applications
- Solution: ExpressRoute Premium with 10 Gbps circuit
- Cost: ~$5,000/month + provider fees
- Result: Consistent 3ms latency, private connection
```

---

## 12.3 Azure Firewall

### What is Azure Firewall?
A managed, cloud-based network security service that protects Azure VNet resources. Stateful firewall with built-in high availability.

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │ Azure Firewall │
              │ (inspects all  │
              │  traffic)      │
              └───────┬────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │Web Subnet│ │App Subnet│ │DB Subnet│
     └─────────┘ └─────────┘ └─────────┘
```

### NSG vs Azure Firewall

| Feature | NSG | Azure Firewall |
|---------|-----|---------------|
| Layer | L3/L4 (IP, port) | L3/L4/L7 (IP, port, FQDN, URL) |
| Scope | Subnet or NIC | Entire VNet |
| FQDN filtering | No | Yes (e.g., allow *.microsoft.com) |
| Threat intelligence | No | Yes (block known malicious IPs) |
| TLS inspection | No | Yes (Premium) |
| Cost | Free | ~$900/month + data processing |
| Use case | Basic traffic filtering | Enterprise network security |

```bash
# Create Azure Firewall subnet (must be "AzureFirewallSubnet")
az network vnet subnet create \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name AzureFirewallSubnet \
  --address-prefix 10.0.5.0/26

# Create public IP
az network public-ip create \
  --resource-group rg-demo-eastus \
  --name pip-firewall \
  --sku Standard \
  --allocation-method Static

# Create Azure Firewall
az network firewall create \
  --resource-group rg-demo-eastus \
  --name fw-main \
  --location eastus \
  --vnet-name vnet-main \
  --public-ip pip-firewall

# Create application rule (allow web browsing)
az network firewall application-rule create \
  --resource-group rg-demo-eastus \
  --firewall-name fw-main \
  --collection-name "AllowWeb" \
  --priority 100 \
  --action Allow \
  --name "AllowGoogle" \
  --protocols Http=80 Https=443 \
  --source-addresses "10.0.0.0/16" \
  --fqdn-tags "" \
  --target-fqdns "*.google.com" "*.microsoft.com"

# Create network rule (allow DNS)
az network firewall network-rule create \
  --resource-group rg-demo-eastus \
  --firewall-name fw-main \
  --collection-name "AllowDNS" \
  --priority 200 \
  --action Allow \
  --name "AllowDNS" \
  --protocols UDP \
  --source-addresses "10.0.0.0/16" \
  --destination-addresses "8.8.8.8" "8.8.4.4" \
  --destination-ports 53

# Create route table to force traffic through firewall
az network route-table create \
  --resource-group rg-demo-eastus \
  --name rt-firewall

az network route-table route create \
  --resource-group rg-demo-eastus \
  --route-table-name rt-firewall \
  --name default-route \
  --address-prefix 0.0.0.0/0 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.5.4  # Firewall private IP

# Associate route table with subnet
az network vnet subnet update \
  --resource-group rg-demo-eastus \
  --vnet-name vnet-main \
  --name web-subnet \
  --route-table rt-firewall
```

---

## 12.4 Azure Front Door & CDN

### Azure Front Door
Global load balancer and CDN with WAF, SSL offloading, and URL-based routing.

```
Users worldwide → Azure Front Door (edge locations) → Backend pools

User in Tokyo → Edge in Tokyo → Backend in East Asia (low latency)
User in London → Edge in London → Backend in West Europe (low latency)
User in New York → Edge in Virginia → Backend in East US (low latency)
```

### Azure CDN
Content Delivery Network — caches static content at edge locations worldwide.

```bash
# Create CDN profile
az cdn profile create \
  --resource-group rg-demo-eastus \
  --name cdn-demo \
  --sku Standard_Microsoft

# Create CDN endpoint
az cdn endpoint create \
  --resource-group rg-demo-eastus \
  --profile-name cdn-demo \
  --name cdn-endpoint-demo \
  --origin stprodeastus2024.blob.core.windows.net \
  --origin-host-header stprodeastus2024.blob.core.windows.net

# URL: https://cdn-endpoint-demo.azureedge.net/images/photo.jpg
# First request: Fetched from origin (storage account)
# Subsequent requests: Served from nearest edge location (fast!)

# Purge CDN cache
az cdn endpoint purge \
  --resource-group rg-demo-eastus \
  --profile-name cdn-demo \
  --name cdn-endpoint-demo \
  --content-paths "/images/*"
```

---

## 12.5 Azure Traffic Manager

```
DNS-based traffic routing across regions:

Routing Methods:
├── Priority:     Primary/failover (Region A primary, Region B backup)
├── Weighted:     Distribute by weight (80% to A, 20% to B)
├── Performance:  Route to closest region (lowest latency)
├── Geographic:   Route by user location (EU users → EU region)
├── MultiValue:   Return multiple healthy endpoints
└── Subnet:       Route by client IP range
```

```bash
# Create Traffic Manager profile
az network traffic-manager profile create \
  --resource-group rg-demo-eastus \
  --name tm-webapp \
  --routing-method Performance \
  --unique-dns-name tm-webapp-demo

# Add endpoints
az network traffic-manager endpoint create \
  --resource-group rg-demo-eastus \
  --profile-name tm-webapp \
  --name endpoint-eastus \
  --type azureEndpoints \
  --target-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-eastus/providers/Microsoft.Web/sites/webapp-eastus" \
  --endpoint-status Enabled

az network traffic-manager endpoint create \
  --resource-group rg-demo-eastus \
  --profile-name tm-webapp \
  --name endpoint-westeurope \
  --type azureEndpoints \
  --target-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-westeurope/providers/Microsoft.Web/sites/webapp-westeurope" \
  --endpoint-status Enabled

# DNS: tm-webapp-demo.trafficmanager.net
# Users automatically routed to nearest healthy endpoint
```

---

## 12.6 Web Application Firewall (WAF)

```
WAF protects web applications from common attacks:
├── SQL Injection
├── Cross-Site Scripting (XSS)
├── Command Injection
├── HTTP Protocol Violations
├── Bot protection
└── OWASP Top 10

WAF can be deployed on:
├── Azure Application Gateway
├── Azure Front Door
└── Azure CDN
```

---

## 12.7 Private Endpoints & Service Endpoints

```
Service Endpoint:
- Extends VNet identity to Azure services
- Traffic stays on Azure backbone (not internet)
- Service still has a public IP
- Free

Private Endpoint:
- Brings the service INTO your VNet with a private IP
- No public IP needed on the service
- Uses Azure Private Link
- Cost: ~$7.50/month per endpoint

Example:
Without: VM (10.0.1.4) → Internet → Storage (public IP)
Service Endpoint: VM (10.0.1.4) → Azure backbone → Storage (public IP, restricted)
Private Endpoint: VM (10.0.1.4) → VNet → Storage (10.0.3.10, private IP)
```

```bash
# Create a Private Endpoint for Storage
az network private-endpoint create \
  --resource-group rg-demo-eastus \
  --name pe-storage \
  --vnet-name vnet-main \
  --subnet db-subnet \
  --private-connection-resource-id "/subscriptions/SUB_ID/resourceGroups/rg-demo-eastus/providers/Microsoft.Storage/storageAccounts/stprodeastus2024" \
  --group-id blob \
  --connection-name pe-storage-connection

# Now storage is accessible via private IP within the VNet
```

---

## 12.8 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| VPN `NotConnected` | Shared key mismatch or on-prem device misconfigured | Verify shared key matches on both sides |
| `GatewaySubnet too small` | Subnet needs at least /27 | Recreate with /27 or larger |
| Firewall blocking all traffic | No allow rules or wrong route table | Add application/network rules; verify UDR |
| CDN serving stale content | Cache not purged | Purge CDN cache: `az cdn endpoint purge` |
| Private Endpoint DNS not resolving | Private DNS zone not linked | Create private DNS zone and link to VNet |
| Traffic Manager not routing | Endpoint health check failing | Verify health probe path and endpoint health |
| ExpressRoute `NotProvisioned` | Provider hasn't completed setup | Contact connectivity provider |

---

## 12.9 Practice Questions

### Question 1
**What is the required subnet name for VPN Gateway?**
- A) VPNSubnet
- B) GatewaySubnet ✅
- C) AzureGatewaySubnet
- D) Any name

### Question 2
**Which service provides a private, dedicated connection to Azure (not over internet)?**
- A) VPN Gateway
- B) ExpressRoute ✅
- C) Azure Firewall
- D) Traffic Manager

### Question 3
**Azure Firewall can filter traffic by FQDN (domain name). True or False?**
- A) True ✅
- B) False

### Question 4
**Which Traffic Manager routing method sends users to the closest region?**
- A) Priority
- B) Weighted
- C) Performance ✅
- D) Geographic

### Question 5
**What is the difference between a Service Endpoint and a Private Endpoint?**
- A) They are the same
- B) Service Endpoint keeps the public IP; Private Endpoint assigns a private IP ✅
- C) Private Endpoint is free; Service Endpoint costs money
- D) Service Endpoint requires ExpressRoute

---

[← Previous Module](./Module-11-Serverless.md) | [Next Module: High Availability & DR →](./Module-13-High-Availability-DR.md)
