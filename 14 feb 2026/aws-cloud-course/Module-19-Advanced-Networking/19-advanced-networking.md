# Module 19: Advanced Networking (Networking Specialty Topics)

## 19.1 Enhanced Networking

Higher bandwidth, higher PPS (packets per second), lower latency using SR-IOV (Single Root I/O Virtualization).

### Elastic Network Adapter (ENA)

- Up to 100 Gbps
- Supported on most modern instance types
- Required for Nitro-based instances

### Intel 82599 VF (legacy)

- Up to 10 Gbps
- Older instance types only

```bash
# Check if ENA is enabled
aws ec2 describe-instances --instance-ids i-0abc123 \
  --query 'Reservations[0].Instances[0].EnaSupport'
# Output: true

# Enable ENA on an AMI
aws ec2 modify-instance-attribute --instance-id i-0abc123 --ena-support
```

---

## 19.2 Elastic Fabric Adapter (EFA)

Improved ENA for HPC workloads. Provides OS-bypass capability for inter-node communication (MPI).

- Only works on Linux
- Bypasses the OS kernel for lower latency
- Use with Cluster Placement Groups for best performance
- Use cases: tightly coupled HPC workloads, distributed ML training

---

## 19.3 Network Performance & I/O Credits

### EC2 Network Bandwidth

- Each instance type has a baseline and burst network bandwidth
- Instances earn network I/O credits when below baseline
- Credits are consumed during burst periods
- Exceeding credits = throttled to baseline

```bash
# Check instance network performance
aws ec2 describe-instance-types --instance-types m5.xlarge \
  --query 'InstanceTypes[0].NetworkInfo.{
    Bandwidth:NetworkPerformance,
    BaselineBandwidth:NetworkInfo.NetworkCards[0].BaselineBandwidthInGbps,
    PeakBandwidth:NetworkInfo.NetworkCards[0].PeakBandwidthInGbps
  }'

# Monitor network credit balance (similar to CPU credits for T instances)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkBandwidthInAllowanceExceeded \
  --dimensions Name=InstanceId,Value=i-0abcdef1234567890 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Sum

# If NetworkBandwidthInAllowanceExceeded > 0, you're being throttled
# Solution: upgrade to a larger instance type or use placement groups
```

**Real-life use case:** A data processing application on m5.xlarge (up to 10 Gbps burst) transfers large files between instances. During peak hours, it exceeds the baseline bandwidth and gets throttled. Monitoring `NetworkBandwidthInAllowanceExceeded` reveals the issue, and upgrading to m5.2xlarge (up to 10 Gbps baseline) resolves it.

### DPDK (Data Plane Development Kit)

Framework for fast packet processing that bypasses the kernel. Used by network appliances, firewalls, and high-performance applications running on EC2.

---

## 19.4 Proxy Protocol & X-Forwarded Headers

### Proxy Protocol (Layer 4 — NLB, CLB)

Adds a header with the client's source IP when using TCP/SSL listeners. Required because NLB operates at Layer 4 and doesn't modify HTTP headers.

```
PROXY TCP4 203.0.113.1 10.0.1.5 12345 80
```

Enable on NLB target group:
```bash
aws elbv2 modify-target-group-attributes \
  --target-group-arn $TG_ARN \
  --attributes Key=proxy_protocol_v2.enabled,Value=true
```

### X-Forwarded Headers (Layer 7 — ALB)

ALB adds HTTP headers with client information:

| Header | Content |
|--------|---------|
| `X-Forwarded-For` | Client IP address |
| `X-Forwarded-Proto` | Protocol (HTTP/HTTPS) |
| `X-Forwarded-Port` | Port number |

Configure Apache to log these:
```
LogFormat "%{X-Forwarded-For}i %{X-Forwarded-Proto}i %{X-Forwarded-Port}i ..."
```

---

## 19.5 BGP (Border Gateway Protocol)

BGP is the routing protocol used by Direct Connect and Site-to-Site VPN (dynamic routing).

### Key Concepts

| Term | Description |
|------|-------------|
| **ASN** | Autonomous System Number — unique identifier for a network |
| **eBGP** | External BGP — between different ASNs (AWS ↔ customer) |
| **iBGP** | Internal BGP — within the same ASN |
| **Prefix** | Network route advertised (e.g., 10.0.0.0/16) |
| **AS_PATH** | List of ASNs a route has traversed (shorter = preferred) |
| **Local Preference** | Higher value = preferred route (within your AS) |
| **MED** | Multi-Exit Discriminator — suggest preferred entry point to your AS |

### BGP Route Selection Order

1. Longest prefix match
2. Highest local preference
3. Shortest AS_PATH
4. Lowest MED
5. eBGP over iBGP

### BFD (Bidirectional Forwarding Detection)

Fast failure detection protocol. Detects link failures in milliseconds (vs. BGP's default 90-second timeout). Enable on Direct Connect for faster failover.

```bash
# BFD is configured on your on-premises router, not via AWS CLI
# Example Cisco router configuration:
# router bgp 65000
#   neighbor 169.254.255.1 remote-as 7224
#   neighbor 169.254.255.1 fall-over bfd
#
# interface GigabitEthernet0/0
#   bfd interval 300 min_rx 300 multiplier 3

# Verify BFD status on Direct Connect virtual interface
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-0abcdef1234567890 \
  --query 'virtualInterfaces[0].{BGPPeers:bgpPeers[].{ASN:asn,State:bgpPeerState,BFD:bfdStatus}}'

# Expected output:
# {
#   "BGPPeers": [{
#     "ASN": 65000,
#     "State": "up",
#     "BFD": "up"
#   }]
# }
```

**Without BFD:** BGP detects failure in ~90 seconds (3 missed keepalives × 30s interval). **With BFD:** Failure detected in ~900ms (3 × 300ms). This is the difference between a 90-second outage and a sub-second failover.

---

## 19.6 Direct Connect — Virtual Interfaces & LAG

### Virtual Interface Types

| Type | Purpose | Access |
|------|---------|--------|
| **Private VIF** | Access VPC resources via Direct Connect Gateway | Private IPs in VPC |
| **Public VIF** | Access AWS public services (S3, DynamoDB, etc.) | Public endpoints |
| **Transit VIF** | Access VPCs via Transit Gateway | Multiple VPCs |

### Link Aggregation Groups (LAG)

Bundle multiple Direct Connect connections into a single logical connection for increased bandwidth and redundancy.

- All connections must be the same bandwidth
- Maximum 4 connections per LAG (for 1/10 Gbps) or 2 (for 100 Gbps)
- If minimum links threshold is not met, the entire LAG goes down

### Direct Connect SiteLink

Enable direct communication between Direct Connect locations without routing through a VPC. Traffic stays on the AWS backbone.

```
┌──────────────┐                                    ┌──────────────┐
│ Data Center A │──DX──▶ AWS Backbone ◀──DX──│ Data Center B │
│ (New York)    │       (SiteLink)            │ (London)       │
└──────────────┘                                    └──────────────┘
```

```bash
# Enable SiteLink on a Direct Connect Gateway association
aws directconnect update-virtual-interface-attributes \
  --virtual-interface-id dxvif-0abcdef1234567890 \
  --enable-site-link

# Verify SiteLink is enabled
aws directconnect describe-virtual-interfaces \
  --virtual-interface-id dxvif-0abcdef1234567890 \
  --query 'virtualInterfaces[0].siteLinkEnabled'
# Expected output: true
```

**Real-life use case:** A company with data centers in New York and London uses SiteLink to route traffic between them over the AWS backbone instead of the public internet. Lower latency, more consistent performance, and no need for a separate MPLS circuit.

### MACSec (802.1AE)

Layer 2 encryption for Direct Connect. Provides point-to-point encryption between your router and the AWS Direct Connect device. Available on 10 Gbps and 100 Gbps dedicated connections.

```bash
# Associate a MACSec key with a Direct Connect connection
aws directconnect associate-mac-sec-key \
  --connection-id dxcon-abcdef12 \
  --secret-arn arn:aws:secretsmanager:us-east-1:123456789012:secret:macsec-key-AbCdEf

# Verify MACSec status
aws directconnect describe-connections \
  --connection-id dxcon-abcdef12 \
  --query 'connections[0].{MacSecCapable:macSecCapable,MacSecKeys:macSecKeys,EncryptionMode:encryptionMode}'

# Expected output:
# {
#   "MacSecCapable": true,
#   "MacSecKeys": [{"SecretARN": "arn:aws:secretsmanager:...", "State": "associated"}],
#   "EncryptionMode": "must_encrypt"
# }
```

**When to use:** Compliance requirements mandate encryption at Layer 2 (e.g., financial services, government). MACSec encrypts all traffic on the physical link, including control plane traffic that IPsec VPN doesn't cover.

---

## 19.7 AWS Cloud WAN

Global wide area network service that connects branch offices, data centers, and VPCs.

```
Branch Office ──▶ Cloud WAN ──▶ VPCs (multiple regions)
Data Center ──▶ Cloud WAN ──▶ VPCs
```

- Uses a Network Policy (JSON) to define network topology
- Supports segments (isolate traffic between departments)
- Integrates with Transit Gateway and Direct Connect
- Replaces complex Transit Gateway peering setups

---

## 19.8 AWS IPAM (IP Address Management)

Plan, track, and monitor IP addresses across AWS accounts and regions.

- Organize IP space into pools
- Enforce allocation rules (CIDR size, region)
- Detect overlapping CIDRs
- Integrates with AWS Organizations
- Monitor IP usage with CloudWatch

```bash
# Create an IPAM
aws ec2 create-ipam \
  --operating-regions RegionName=us-east-1 RegionName=eu-west-1

# Expected output:
# {
#   "Ipam": {
#     "IpamId": "ipam-0abcdef1234567890",
#     "PublicDefaultScopeId": "ipam-scope-pub-0abcdef",
#     "PrivateDefaultScopeId": "ipam-scope-priv-0abcdef"
#   }
# }

# Create a top-level pool
aws ec2 create-ipam-pool \
  --ipam-scope-id ipam-scope-priv-0abcdef \
  --address-family ipv4 \
  --locale us-east-1

# Provision a CIDR to the pool
aws ec2 provision-ipam-pool-cidr \
  --ipam-pool-id ipam-pool-0abcdef1234567890 \
  --cidr 10.0.0.0/8

# Allocate a CIDR from the pool (for a new VPC)
aws ec2 allocate-ipam-pool-cidr \
  --ipam-pool-id ipam-pool-0abcdef1234567890 \
  --netmask-length 16

# Expected output:
# {
#   "IpamPoolAllocation": {
#     "Cidr": "10.1.0.0/16",
#     "IpamPoolAllocationId": "ipam-pool-alloc-0abcdef"
#   }
# }

# Create a VPC using the IPAM pool
aws ec2 create-vpc \
  --ipv4-ipam-pool-id ipam-pool-0abcdef1234567890 \
  --ipv4-netmask-length 16
```

**Real-life use case:** An organization with 100 AWS accounts uses IPAM to prevent CIDR overlaps. Each team requests a /16 from the IPAM pool, and IPAM automatically assigns non-overlapping ranges. This prevents the "we can't peer these VPCs because they overlap" problem.

---

## 19.9 BYOIP (Bring Your Own IP)

Use your own public IPv4 or IPv6 address ranges in AWS.

- Must own the IP range (registered in RIR: ARIN, RIPE, APNIC)
- Create ROA (Route Origin Authorization) to authorize AWS to advertise your IPs
- Can use with EC2, NLB, Global Accelerator

```bash
# Step 1: Create ROA at your RIR (ARIN/RIPE/APNIC)
# Authorize AWS ASN 16509 to advertise your prefix

# Step 2: Provision the address range in AWS
aws ec2 provision-byoip-cidr \
  --cidr 203.0.113.0/24 \
  --cidr-authorization-context Message="1|aws|123456789012|203.0.113.0/24|20250101|20260101",Signature="base64-signature"

# Step 3: Advertise the range
aws ec2 advertise-byoip-cidr --cidr 203.0.113.0/24

# Step 4: Allocate an Elastic IP from your range
aws ec2 allocate-address \
  --domain vpc \
  --address 203.0.113.10

# Check status
aws ec2 describe-byoip-cidrs --max-results 10
# Expected output:
# {
#   "ByoipCidrs": [{
#     "Cidr": "203.0.113.0/24",
#     "State": "provisioned"
#   }]
# }
```

**Real-life use case:** A company migrating to AWS wants to keep their existing public IP addresses to avoid updating DNS records, firewall rules, and IP allowlists at partner organizations.

---

## 19.10 VPC Multicast

Transit Gateway supports multicast traffic between VPCs.

- Create multicast domains on Transit Gateway
- Associate subnets and register sources/members
- Supports IGMP (Internet Group Management Protocol)
- Use cases: media streaming, financial data distribution, software updates

```bash
# Enable multicast on Transit Gateway
aws ec2 create-transit-gateway \
  --options '{"MulticastSupport": "enable"}'

# Create a multicast domain
aws ec2 create-transit-gateway-multicast-domain \
  --transit-gateway-id tgw-0abcdef1234567890 \
  --options '{"Igmpv2Support": "enable", "StaticSourcesSupport": "enable"}'

# Associate a subnet
aws ec2 associate-transit-gateway-multicast-domain \
  --transit-gateway-multicast-domain-id tgw-mcast-domain-0abcdef \
  --transit-gateway-attachment-id tgw-attach-0abcdef \
  --subnet-ids subnet-0abcdef1234567890

# Register a multicast source
aws ec2 register-transit-gateway-multicast-group-sources \
  --transit-gateway-multicast-domain-id tgw-mcast-domain-0abcdef \
  --group-ip-address 239.1.1.1 \
  --network-interface-ids eni-0abcdef1234567890

# Register multicast members (receivers)
aws ec2 register-transit-gateway-multicast-group-members \
  --transit-gateway-multicast-domain-id tgw-mcast-domain-0abcdef \
  --group-ip-address 239.1.1.1 \
  --network-interface-ids eni-0fedcba0987654321
```

---

## 19.11 EKS Networking

### VPC CNI Plugin

Amazon VPC CNI assigns VPC IP addresses directly to pods. Each pod gets a real VPC IP — no overlay network.

### Pod Networking

- Pods communicate using VPC IPs
- Security groups can be applied to individual pods
- Custom networking: use different subnets/CIDRs for pods vs. nodes

### EKS Cluster Endpoint Access

| Mode | API Server Access |
|------|------------------|
| **Public** (default) | Accessible from internet |
| **Public + Private** | Internet + within VPC |
| **Private** | Only from within VPC |

### Kubernetes Service Types

| Type | Description |
|------|-------------|
| **ClusterIP** | Internal only (default) |
| **NodePort** | Exposes on each node's IP at a static port |
| **LoadBalancer** | Creates AWS NLB/ALB |

---

## 19.12 SD-WAN with Transit Gateway Connect

Integrate third-party SD-WAN appliances with Transit Gateway using GRE tunnels and BGP.

- Transit Gateway Connect attachment
- GRE tunnel for data plane
- BGP for control plane
- Supports up to 5 Gbps per Connect peer

```bash
# Create a Transit Gateway Connect attachment
aws ec2 create-transit-gateway-connect \
  --transport-transit-gateway-attachment-id tgw-attach-0abcdef1234567890 \
  --options Protocol=gre

# Expected output:
# {
#   "TransitGatewayConnect": {
#     "TransitGatewayAttachmentId": "tgw-attach-connect-0abcdef",
#     "Options": {"Protocol": "gre"}
#   }
# }

# Create a Connect peer (GRE tunnel + BGP session)
aws ec2 create-transit-gateway-connect-peer \
  --transit-gateway-attachment-id tgw-attach-connect-0abcdef \
  --peer-address 10.0.1.100 \
  --transit-gateway-address 10.0.1.200 \
  --inside-cidr-blocks 169.254.100.0/29 \
  --bgp-options PeerAsn=65000
```

**SD-WAN vendors supported:** Cisco SD-WAN, VMware SD-WAN, Aruba EdgeConnect, Silver Peak, Fortinet. The SD-WAN appliance runs on EC2 and connects to Transit Gateway via GRE tunnel.

### Transit Gateway Peering

Connect Transit Gateways across regions for inter-region routing.

```bash
# Create a peering attachment between TGWs in different regions
aws ec2 create-transit-gateway-peering-attachment \
  --transit-gateway-id tgw-0abcdef1234567890 \
  --peer-transit-gateway-id tgw-0fedcba0987654321 \
  --peer-region eu-west-1 \
  --peer-account-id 123456789012

# Accept the peering in the peer region
aws ec2 accept-transit-gateway-peering-attachment \
  --transit-gateway-attachment-id tgw-attach-peer-0abcdef \
  --region eu-west-1

# Add routes to the peering attachment
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-0abcdef \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-attachment-id tgw-attach-peer-0abcdef
```

**Note:** Transit Gateway peering uses static routes only (no dynamic BGP). Data is encrypted and stays on the AWS backbone.

### Transit Gateway AZ Affinity

Transit Gateway prefers to route traffic to attachments in the same AZ to minimize cross-AZ data transfer costs.

```
┌─────────────────────────────────────────────────┐
│                Transit Gateway                   │
│                                                  │
│  AZ-a: VPC-A attachment ←→ VPC-B attachment     │  ← Same AZ = preferred
│  AZ-b: VPC-A attachment ←→ VPC-B attachment     │
└─────────────────────────────────────────────────┘
```

**Behavior:** If a packet enters TGW from VPC-A in AZ-a, TGW routes it to VPC-B's attachment in AZ-a (if available). This avoids cross-AZ charges. If the destination AZ attachment doesn't exist, TGW routes cross-AZ.

**Best practice:** Enable the same AZs for all VPC attachments to Transit Gateway to benefit from AZ affinity and reduce cross-AZ data transfer costs.

---

## 19.13 VPN Advanced Topics

### VPN NAT Traversal (NAT-T)

Allows IPsec VPN traffic to pass through NAT devices. AWS Site-to-Site VPN supports NAT-T by default (UDP port 4500).

```
On-Premises Router ──▶ NAT Device ──▶ Internet ──▶ AWS VPN Endpoint
                    (IPsec encapsulated in UDP:4500)
```

**When needed:** Your customer gateway is behind a NAT device (common in small offices). NAT-T encapsulates ESP packets inside UDP to traverse the NAT.

### VPN CloudHub

Connect multiple on-premises sites through a single Virtual Private Gateway. Sites can communicate with each other through the VGW.

```
┌──────────────┐
│   Site A      │──VPN──┐
│ (New York)    │       │
└──────────────┘       │
                    ┌───▼───┐
┌──────────────┐   │  VGW  │   ┌──────────┐
│   Site B      │──▶│       │──▶│   VPC    │
│ (Chicago)     │   │       │   └──────────┘
└──────────────┘   └───▲───┘
                       │
┌──────────────┐       │
│   Site C      │──VPN──┘
│ (Dallas)      │
└──────────────┘
```

```bash
# VPN CloudHub setup:
# 1. Create a VGW and attach to VPC
aws ec2 create-vpn-gateway --type ipsec.1
aws ec2 attach-vpn-gateway --vpn-gateway-id vgw-0abcdef --vpc-id vpc-0abcdef

# 2. Create customer gateways for each site
aws ec2 create-customer-gateway --type ipsec.1 --bgp-asn 65001 --public-ip 203.0.113.10
aws ec2 create-customer-gateway --type ipsec.1 --bgp-asn 65002 --public-ip 198.51.100.10
aws ec2 create-customer-gateway --type ipsec.1 --bgp-asn 65003 --public-ip 192.0.2.10

# 3. Create VPN connections (each site to the same VGW)
aws ec2 create-vpn-connection --type ipsec.1 --customer-gateway-id cgw-site-a --vpn-gateway-id vgw-0abcdef
aws ec2 create-vpn-connection --type ipsec.1 --customer-gateway-id cgw-site-b --vpn-gateway-id vgw-0abcdef
aws ec2 create-vpn-connection --type ipsec.1 --customer-gateway-id cgw-site-c --vpn-gateway-id vgw-0abcdef

# 4. Enable route propagation — each site advertises its CIDR via BGP
# Sites can now communicate with each other through the VGW
```

**Key requirement:** Each site must use a unique BGP ASN. Dynamic routing (BGP) is required for site-to-site communication through CloudHub.

---

## 19.14 VPC Endpoints — Advanced

### VPC Endpoint Policy

Restrict which AWS resources can be accessed through a VPC endpoint. By default, endpoints allow full access.

```bash
# Create a restrictive S3 endpoint policy (only allow access to specific bucket)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0abcdef1234567890 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-0abcdef1234567890 \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-approved-bucket/*"
    }]
  }'

# Modify an existing endpoint policy
aws ec2 modify-vpc-endpoint \
  --vpc-endpoint-id vpce-0abcdef1234567890 \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {"aws:PrincipalOrgID": "o-abcdef1234"}
      }
    }]
  }'
```

**Real-life use case:** Prevent data exfiltration by restricting the S3 VPC endpoint to only allow access to company-owned buckets. Even if an attacker compromises an EC2 instance, they can't upload data to their own S3 bucket.

### VPC Endpoint DNS

Interface endpoints create ENIs with private IPs. Private DNS associates the service's public DNS name with the endpoint's private IP.

```bash
# Create an interface endpoint with private DNS enabled
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0abcdef1234567890 \
  --service-name com.amazonaws.us-east-1.sqs \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0abcdef1234567890 \
  --private-dns-enabled

# With private DNS enabled:
# sqs.us-east-1.amazonaws.com → resolves to endpoint's private IP (10.0.1.50)
# Without private DNS:
# sqs.us-east-1.amazonaws.com → resolves to public IP
# vpce-0abcdef.sqs.us-east-1.vpce.amazonaws.com → resolves to private IP

# Verify DNS resolution from within the VPC
# dig sqs.us-east-1.amazonaws.com
# ;; ANSWER SECTION:
# sqs.us-east-1.amazonaws.com. 60 IN A 10.0.1.50  (private IP of endpoint ENI)
```

### Centralized VPC Endpoints

Share VPC endpoints across multiple VPCs using a hub-and-spoke model with Transit Gateway or VPC peering.

```
┌──────────┐     ┌──────────────────┐     ┌──────────┐
│  VPC A   │────▶│  Shared Services │◀────│  VPC B   │
│ (spoke)  │     │  VPC (hub)       │     │ (spoke)  │
└──────────┘     │                  │     └──────────┘
                 │  S3 Endpoint     │
                 │  SQS Endpoint    │
                 │  KMS Endpoint    │
                 └──────────────────┘
```

**Setup:** Create interface endpoints in the shared services VPC. Use Transit Gateway or VPC peering to route traffic from spoke VPCs to the hub. Disable private DNS on the endpoints and use Route 53 Private Hosted Zones to resolve service DNS names to the endpoint IPs.

```bash
# In the hub VPC: create endpoint WITHOUT private DNS
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-hub \
  --service-name com.amazonaws.us-east-1.sqs \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-hub-a subnet-hub-b \
  --no-private-dns-enabled

# Create a Route 53 Private Hosted Zone for the service
aws route53 create-hosted-zone \
  --name sqs.us-east-1.amazonaws.com \
  --vpc VPCRegion=us-east-1,VPCId=vpc-hub \
  --caller-reference "centralized-sqs-$(date +%s)"

# Associate spoke VPCs with the hosted zone
aws route53 associate-vpc-with-hosted-zone \
  --hosted-zone-id Z1234567890 \
  --vpc VPCRegion=us-east-1,VPCId=vpc-spoke-a

# Create an alias record pointing to the endpoint
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "sqs.us-east-1.amazonaws.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "vpce-0abcdef.sqs.us-east-1.vpce.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

### PrivateLink vs VPC Peering

| Feature | PrivateLink | VPC Peering |
|---------|-------------|-------------|
| **Scope** | Expose specific services | Full network connectivity |
| **Direction** | Unidirectional (consumer → provider) | Bidirectional |
| **Overlapping CIDRs** | ✅ Works | ❌ Doesn't work |
| **Transitive** | No | No |
| **Scale** | Thousands of consumers | Limited by route table entries |
| **Use case** | SaaS, microservices | Full VPC-to-VPC connectivity |

**Use PrivateLink when:** You want to expose a specific service (not the entire VPC), CIDRs overlap, or you're a SaaS provider serving multiple customers.

**Use VPC Peering when:** Two VPCs need full bidirectional connectivity and CIDRs don't overlap.

---

## 19.15 Centralized Network Architectures

### Centralized Inspection (Firewall)

Route all inter-VPC and internet-bound traffic through a centralized inspection VPC with firewalls.

```
┌──────────┐     ┌──────────────────────┐     ┌──────────┐
│  VPC A   │────▶│  Inspection VPC      │◀────│  VPC B   │
│          │     │                      │     │          │
└──────────┘     │  ┌────────────────┐  │     └──────────┘
                 │  │ AWS Network    │  │
      ┌──────────│  │ Firewall /     │  │──────────┐
      │          │  │ GWLB + FW      │  │          │
      ▼          │  └────────────────┘  │          ▼
  Internet       └──────────────────────┘      On-Premises
```

```bash
# Create AWS Network Firewall in the inspection VPC
aws network-firewall create-firewall \
  --firewall-name central-firewall \
  --firewall-policy-arn arn:aws:network-firewall:us-east-1:123456789012:firewall-policy/block-malicious \
  --vpc-id vpc-inspection \
  --subnet-mappings SubnetId=subnet-fw-a SubnetId=subnet-fw-b

# Configure Transit Gateway route tables to route through the inspection VPC
# Spoke VPCs → TGW → Inspection VPC → Firewall → TGW → Destination VPC

# Create a TGW route table for spoke VPCs (default route to inspection VPC)
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-spoke \
  --destination-cidr-block 0.0.0.0/0 \
  --transit-gateway-attachment-id tgw-attach-inspection-vpc
```

### AWS Network Manager

Centralized management and monitoring of your global network (Transit Gateways, VPNs, Direct Connect, SD-WAN).

```bash
# Create a global network
aws networkmanager create-global-network \
  --description "Production Global Network"

# Register a Transit Gateway
aws networkmanager register-transit-gateway \
  --global-network-id global-network-0abcdef \
  --transit-gateway-arn arn:aws:ec2:us-east-1:123456789012:transit-gateway/tgw-0abcdef

# Create a site (represents a physical location)
aws networkmanager create-site \
  --global-network-id global-network-0abcdef \
  --location '{"Address":"123 Main St, New York, NY","Latitude":"40.7128","Longitude":"-74.0060"}' \
  --description "NYC Data Center"

# View network topology and events in the Network Manager console
# Provides: topology map, route analysis, events, metrics
```

### VPC Ingress Routing

Route inbound traffic from an Internet Gateway or Virtual Private Gateway to a network appliance (firewall) before it reaches the destination.

```bash
# Create a route table associated with the Internet Gateway
aws ec2 create-route-table --vpc-id vpc-0abcdef1234567890

# Associate the route table with the Internet Gateway (ingress routing)
aws ec2 associate-route-table \
  --route-table-id rtb-ingress \
  --gateway-id igw-0abcdef1234567890

# Add a route: traffic destined for the web subnet goes to the firewall ENI first
aws ec2 create-route \
  --route-table-id rtb-ingress \
  --destination-cidr-block 10.0.1.0/24 \
  --network-interface-id eni-firewall-0abcdef

# Flow: Internet → IGW → Firewall ENI (inspect) → Web Server
```

**Real-life use case:** All inbound traffic from the internet is routed through an IDS/IPS appliance before reaching web servers. Without ingress routing, traffic goes directly from the IGW to the instance, bypassing inspection.

---

## 19.16 Key Takeaways

1. Enhanced Networking (ENA) for up to 100 Gbps; EFA for HPC with OS-bypass
2. Proxy Protocol for client IP at Layer 4 (NLB); X-Forwarded headers at Layer 7 (ALB)
3. BGP is the routing protocol for Direct Connect and dynamic VPN; BFD for fast failover
4. Direct Connect VIFs: Private (VPC), Public (AWS services), Transit (via TGW)
5. LAG bundles multiple DX connections; MACSec for Layer 2 encryption
6. Cloud WAN for global network management across regions
7. IPAM for centralized IP address planning and monitoring
8. BYOIP to use your own public IPs in AWS
9. EKS uses VPC CNI — pods get real VPC IPs, no overlay
10. SD-WAN integrates with Transit Gateway Connect via GRE + BGP
