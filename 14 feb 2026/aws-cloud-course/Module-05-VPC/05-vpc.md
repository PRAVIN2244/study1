# Module 5: VPC - Virtual Private Cloud & Networking

## 5.1 What is a VPC?

A VPC is your own isolated network within AWS. Every resource you launch (EC2, RDS, Lambda) runs inside a VPC.

### Real-World Analogy
- **VPC** = Your office building
- **Subnets** = Floors in the building
- **Internet Gateway** = The main entrance (public access)
- **NAT Gateway** = A mail room (private floors can send mail out, but nobody can walk in)
- **Route Tables** = Hallway signs directing traffic
- **Security Groups** = Door locks on each room
- **NACLs** = Security guards at each floor entrance

### VPC Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  VPC: 10.0.0.0/16 (65,536 IPs)                              │
│                                                              │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │  Public Subnet        │  │  Public Subnet        │         │
│  │  10.0.1.0/24 (AZ-a)  │  │  10.0.2.0/24 (AZ-b)  │         │
│  │                       │  │                       │         │
│  │  ┌─────┐  ┌─────┐   │  │  ┌─────┐  ┌─────┐   │         │
│  │  │ EC2 │  │ NAT │   │  │  │ EC2 │  │ ALB │   │         │
│  │  │ Web │  │ GW  │   │  │  │ Web │  │     │   │         │
│  │  └─────┘  └─────┘   │  │  └─────┘  └─────┘   │         │
│  └──────────┬───────────┘  └──────────┬───────────┘         │
│             │                          │                     │
│  ┌──────────┴───────────┐  ┌──────────┴───────────┐         │
│  │  Private Subnet       │  │  Private Subnet       │         │
│  │  10.0.3.0/24 (AZ-a)  │  │  10.0.4.0/24 (AZ-b)  │         │
│  │                       │  │                       │         │
│  │  ┌─────┐  ┌─────┐   │  │  ┌─────┐  ┌─────┐   │         │
│  │  │ EC2 │  │ RDS │   │  │  │ EC2 │  │ RDS │   │         │
│  │  │ App │  │ Pri │   │  │  │ App │  │ Stby│   │         │
│  │  └─────┘  └─────┘   │  │  └─────┘  └─────┘   │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                              │
│  ┌──────────────┐                                           │
│  │ Internet GW  │◄──── Public Internet                      │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 5.2 Networking Fundamentals — IP Addresses and CIDR

### What is an IP Address?

Every device on a network needs a unique address. An IPv4 address is a 32-bit number written as 4 octets:

```
192.168.1.100
 │    │   │  │
 │    │   │  └── 4th octet (0-255)
 │    │   └── 3rd octet (0-255)
 │    └── 2nd octet (0-255)
 └── 1st octet (0-255)

In binary: 11000000.10101000.00000001.01100100
           (each octet = 8 bits, total = 32 bits)
```

### Private IP Ranges (RFC 1918)

These IP ranges are reserved for private networks (not routable on the internet):

```
┌──────────────────────────────────────────────────────────────┐
│              Private IP Address Ranges                        │
├──────────────────┬──────────────────┬────────────────────────┤
│  Class A         │  10.0.0.0/8      │  16,777,216 IPs        │
│                  │  10.0.0.0 -      │  Used by large orgs    │
│                  │  10.255.255.255  │                        │
├──────────────────┼──────────────────┼────────────────────────┤
│  Class B         │  172.16.0.0/12   │  1,048,576 IPs         │
│                  │  172.16.0.0 -    │  Used by medium orgs   │
│                  │  172.31.255.255  │                        │
├──────────────────┼──────────────────┼────────────────────────┤
│  Class C         │  192.168.0.0/16  │  65,536 IPs            │
│                  │  192.168.0.0 -   │  Used by home/small    │
│                  │  192.168.255.255 │  office networks       │
└──────────────────┴──────────────────┴────────────────────────┘

AWS VPCs use these private ranges. The most common choice is 10.0.0.0/16.
```

### CIDR Notation

CIDR (Classless Inter-Domain Routing) defines IP address ranges using a prefix length.

```
10.0.0.0/16
│        │
│        └── Prefix length: first 16 bits are the "network" part (fixed)
│            remaining 16 bits are for hosts (variable)
└── Network address

How to calculate IPs: 2^(32 - prefix) = number of IPs
  /16 → 2^(32-16) = 2^16 = 65,536 IPs
  /24 → 2^(32-24) = 2^8  = 256 IPs
  /28 → 2^(32-28) = 2^4  = 16 IPs
```

### Common CIDR Blocks

| CIDR | IPs Available | Binary Mask | Use Case |
|------|--------------|-------------|----------|
| `10.0.0.0/8` | 16,777,216 | 255.0.0.0 | Entire private range |
| `10.0.0.0/16` | 65,536 | 255.255.0.0 | Large VPC |
| `10.0.0.0/20` | 4,096 | 255.255.240.0 | Medium VPC |
| `10.0.0.0/24` | 256 | 255.255.255.0 | Single subnet |
| `10.0.0.0/28` | 16 | 255.255.255.240 | Small subnet |
| `10.0.0.0/32` | 1 | 255.255.255.255 | Single host |

### How Subnet Bifurcation (Splitting) Works

Bifurcation means dividing a large network into smaller subnets. You increase the prefix length by 1 to split a block in half.

```
Start: 10.0.0.0/16 (65,536 IPs)
       │
       ├── Split /16 into two /17s:
       │     10.0.0.0/17    (32,768 IPs: 10.0.0.0   - 10.0.127.255)
       │     10.0.128.0/17  (32,768 IPs: 10.0.128.0 - 10.0.255.255)
       │
       └── Or split /16 into 256 /24s:
             10.0.0.0/24    (256 IPs: 10.0.0.0   - 10.0.0.255)
             10.0.1.0/24    (256 IPs: 10.0.1.0   - 10.0.1.255)
             10.0.2.0/24    (256 IPs: 10.0.2.0   - 10.0.2.255)
             ...
             10.0.255.0/24  (256 IPs: 10.0.255.0 - 10.0.255.255)
```

**Real-world VPC subnet planning example:**

```
VPC: 10.0.0.0/16 (65,536 IPs)
│
├── Public Subnets (internet-facing resources)
│     10.0.1.0/24   → Public-Subnet-AZ-a  (251 usable IPs)
│     10.0.2.0/24   → Public-Subnet-AZ-b  (251 usable IPs)
│
├── Private Subnets (application servers)
│     10.0.3.0/24   → Private-Subnet-AZ-a (251 usable IPs)
│     10.0.4.0/24   → Private-Subnet-AZ-b (251 usable IPs)
│
├── Database Subnets (databases, no internet)
│     10.0.5.0/24   → DB-Subnet-AZ-a      (251 usable IPs)
│     10.0.6.0/24   → DB-Subnet-AZ-b      (251 usable IPs)
│
└── Reserved for future use
      10.0.7.0/24 - 10.0.255.0/24
```

### AWS Reserved IPs in Every Subnet

AWS reserves **5 IP addresses** in every subnet. You cannot use these.

For a subnet `10.0.1.0/24` (range: 10.0.1.0 - 10.0.1.255):

```
┌──────────────┬──────────────────────────────────────────────┐
│  IP Address  │  Reserved For                                │
├──────────────┼──────────────────────────────────────────────┤
│  10.0.1.0    │  Network address (identifies the subnet)     │
│  10.0.1.1    │  VPC router (AWS internal routing)           │
│  10.0.1.2    │  DNS server (Amazon-provided DNS)            │
│  10.0.1.3    │  Reserved by AWS for future use              │
│  10.0.1.255  │  Broadcast address (not supported in VPC)    │
├──────────────┼──────────────────────────────────────────────┤
│  Total       │  5 reserved, 251 usable out of 256           │
└──────────────┴──────────────────────────────────────────────┘

For a /28 subnet (16 IPs): 16 - 5 = 11 usable IPs
For a /24 subnet (256 IPs): 256 - 5 = 251 usable IPs
For a /20 subnet (4096 IPs): 4096 - 5 = 4091 usable IPs
```

⚠️ This is why very small subnets (/28 = 16 IPs) lose a large percentage to reserved addresses.

---

## 5.3 Create a VPC

### Manual Steps via AWS Console: Create a VPC

1. Go to **VPC → Your VPCs → Create VPC**
2. Select **VPC only** (not "VPC and more" — we'll create subnets manually to learn)
3. Name: `Production-VPC`
4. IPv4 CIDR block: `10.0.0.0/16`
5. Tenancy: `Default`
6. Click **Create VPC**
7. After creation, select the VPC → **Actions → Edit VPC settings**
8. Check **Enable DNS hostnames** and **Enable DNS resolution**
9. Click **Save**

### Create VPC (CLI)

```bash
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=Production-VPC}]' \
  --query 'Vpc.VpcId' \
  --output text)

echo "VPC created: $VPC_ID"
```

**Expected Output:**
```
VPC created: vpc-0abcd1234efgh5678
```

### Enable DNS Hostnames

```bash
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames '{"Value": true}'

aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-support '{"Value": true}'
```

---

## 5.4 Subnets — What They Are and How They Work

### What is a Subnet?

A subnet (sub-network) is a logical division of a VPC's IP address range. Each subnet lives in exactly one Availability Zone and holds a portion of the VPC's IP addresses.

```
Think of it this way:
  VPC        = An entire office building (10.0.0.0/16)
  Subnet     = A floor in the building (10.0.1.0/24)
  EC2/RDS    = Rooms on that floor (10.0.1.10, 10.0.1.11, ...)

Rules:
  - A subnet exists in exactly ONE Availability Zone
  - A subnet's CIDR must be a subset of the VPC's CIDR
  - Subnets within a VPC cannot have overlapping CIDRs
  - Resources (EC2, RDS, etc.) are launched INTO a subnet
```

### Public Subnet vs Private Subnet

A subnet is NOT inherently public or private. What makes it public or private is its **route table**:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  PUBLIC SUBNET                    PRIVATE SUBNET                 │
│  ─────────────                    ──────────────                 │
│                                                                  │
│  Route table has:                 Route table has:               │
│    0.0.0.0/0 → IGW                 0.0.0.0/0 → NAT Gateway     │
│    (Internet Gateway)               (or NO route to internet)    │
│                                                                  │
│  Instances CAN have               Instances CANNOT have          │
│  public IP addresses               public IP addresses           │
│                                                                  │
│  Directly reachable               NOT reachable from internet    │
│  from the internet                 (can reach OUT via NAT)       │
│                                                                  │
│  Use for:                         Use for:                       │
│    - Web servers                    - Application servers         │
│    - Load balancers                 - Databases                   │
│    - NAT Gateways                   - Internal microservices      │
│    - Bastion hosts                  - Background workers          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

The ONLY difference:
  Public subnet  → route table has 0.0.0.0/0 → Internet Gateway
  Private subnet → route table has 0.0.0.0/0 → NAT Gateway (or nothing)
```

### Manual Steps via AWS Console: Create Subnets

1. Go to **VPC → Subnets → Create subnet**
2. Select your VPC
3. Name: `Public-Subnet-A`
4. Availability Zone: `us-east-1a`
5. CIDR block: `10.0.1.0/24`
6. Click **Create subnet**
7. Repeat for each subnet (Public-B, Private-A, Private-B, DB-A, DB-B)
8. For public subnets: select the subnet → **Actions → Edit subnet settings** → check **Enable auto-assign public IPv4 address**

### Create Public Subnets (CLI)

```bash
# Public Subnet in AZ-a
PUB_SUB_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-Subnet-A}]' \
  --query 'Subnet.SubnetId' \
  --output text)

# Public Subnet in AZ-b
PUB_SUB_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Public-Subnet-B}]' \
  --query 'Subnet.SubnetId' \
  --output text)

echo "Public Subnets: $PUB_SUB_A, $PUB_SUB_B"
```

### Create Private Subnets

```bash
# Private Subnet in AZ-a
PRIV_SUB_A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.3.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-Subnet-A}]' \
  --query 'Subnet.SubnetId' \
  --output text)

# Private Subnet in AZ-b
PRIV_SUB_B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.4.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=Private-Subnet-B}]' \
  --query 'Subnet.SubnetId' \
  --output text)

echo "Private Subnets: $PRIV_SUB_A, $PRIV_SUB_B"
```

### Enable Auto-Assign Public IP for Public Subnets

```bash
aws ec2 modify-subnet-attribute \
  --subnet-id $PUB_SUB_A \
  --map-public-ip-on-launch

aws ec2 modify-subnet-attribute \
  --subnet-id $PUB_SUB_B \
  --map-public-ip-on-launch
```

---

## 5.5 Internet Gateway

An Internet Gateway (IGW) allows resources in public subnets to communicate with the internet. Without an IGW, nothing in your VPC can reach the internet.

```
Internet ←──→ Internet Gateway ←──→ Public Subnet (EC2 with public IP)

Key facts:
  - One IGW per VPC (1:1 relationship)
  - IGW is horizontally scaled, redundant, and highly available
  - No bandwidth constraints
  - Free (no hourly charge)
  - An IGW alone is not enough — you also need a route table entry pointing to it
```

### Manual Steps via AWS Console: Create Internet Gateway

1. Go to **VPC → Internet Gateways → Create internet gateway**
2. Name: `Production-IGW`
3. Click **Create internet gateway**
4. Select the new IGW → **Actions → Attach to VPC**
5. Select your VPC → Click **Attach internet gateway**

### Create Internet Gateway (CLI)

```bash
# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=Production-IGW}]' \
  --query 'InternetGateway.InternetGatewayId' \
  --output text)

# Attach to VPC
aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

echo "Internet Gateway: $IGW_ID"
```

---

## 5.6 Route Tables

Route tables contain rules (routes) that determine where network traffic is directed. Every subnet must be associated with a route table.

```
┌─────────────────────────────────────────────────────────────┐
│  Route Table: Public-RT                                      │
├─────────────────────┬───────────────────────────────────────┤
│  Destination        │  Target                                │
├─────────────────────┼───────────────────────────────────────┤
│  10.0.0.0/16        │  local (traffic stays within VPC)     │
│  0.0.0.0/0          │  igw-xxx (all other traffic → internet)│
└─────────────────────┴───────────────────────────────────────┘

│  Route Table: Private-RT                                     │
├─────────────────────┬───────────────────────────────────────┤
│  Destination        │  Target                                │
├─────────────────────┼───────────────────────────────────────┤
│  10.0.0.0/16        │  local (traffic stays within VPC)     │
│  0.0.0.0/0          │  nat-xxx (outbound only via NAT)      │
└─────────────────────┴───────────────────────────────────────┘

How routing works:
  1. Instance sends a packet to 54.231.10.5
  2. Route table checks: does 54.231.10.5 match 10.0.0.0/16? No.
  3. Route table checks: does 54.231.10.5 match 0.0.0.0/0? Yes.
  4. Send packet to the target (IGW or NAT Gateway)
  5. Most specific route wins (longest prefix match)
```

### Manual Steps via AWS Console: Create Route Tables

1. Go to **VPC → Route Tables → Create route table**
2. Name: `Public-RT`, select your VPC → **Create**
3. Select `Public-RT` → **Routes** tab → **Edit routes**
4. Click **Add route**: Destination `0.0.0.0/0`, Target: select your Internet Gateway
5. Click **Save changes**
6. Go to **Subnet associations** tab → **Edit subnet associations**
7. Check your public subnets → **Save associations**
8. Repeat for `Private-RT` but point `0.0.0.0/0` to your NAT Gateway instead

### Create Public Route Table (CLI)

```bash
# Create route table
PUB_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Public-RT}]' \
  --query 'RouteTable.RouteTableId' \
  --output text)

# Add route to Internet Gateway (all internet traffic)
aws ec2 create-route \
  --route-table-id $PUB_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

# Associate with public subnets
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_SUB_A
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_SUB_B
```

### View Route Table

```bash
aws ec2 describe-route-tables \
  --route-table-ids $PUB_RT \
  --query 'RouteTables[0].Routes' \
  --output table
```

**Expected Output:**
```
------------------------------------------------------
|                  DescribeRouteTables                |
+-------------------+----------------+----------------+
| DestinationCidr   | GatewayId      | State          |
+-------------------+----------------+----------------+
| 10.0.0.0/16       | local          | active         |
| 0.0.0.0/0         | igw-0abcd1234  | active         |
+-------------------+----------------+----------------+
```

**Route Explanation:**
- `10.0.0.0/16 → local` = Traffic within VPC stays local
- `0.0.0.0/0 → igw-xxx` = All other traffic goes to internet

---

## 5.7 NAT Gateway

NAT (Network Address Translation) Gateway allows private subnet resources to access the internet (for updates, API calls) without being directly accessible from the internet.

```
How NAT Gateway works:

  Private Instance (10.0.3.10)
       │
       │ "I need to download updates from the internet"
       ▼
  Private Route Table: 0.0.0.0/0 → NAT Gateway
       │
       ▼
  NAT Gateway (in PUBLIC subnet, has Elastic IP 54.x.x.x)
       │
       │ Translates: source 10.0.3.10 → 54.x.x.x
       ▼
  Internet Gateway → Internet
       │
       │ Response comes back to 54.x.x.x
       ▼
  NAT Gateway translates back: destination 54.x.x.x → 10.0.3.10
       │
       ▼
  Private Instance receives the response

Key facts:
  - NAT Gateway must be in a PUBLIC subnet
  - NAT Gateway needs an Elastic IP
  - Private instances can reach OUT but internet cannot reach IN
  - Costs ~$0.045/hour (~$32/month) + data processing charges
  - For HA: create one NAT Gateway per AZ
```

### Manual Steps via AWS Console: Create NAT Gateway

1. Go to **VPC → NAT Gateways → Create NAT gateway**
2. Name: `Production-NAT`
3. Subnet: select a **public** subnet (this is where the NAT GW lives)
4. Connectivity type: `Public`
5. Click **Allocate Elastic IP** (assigns a static public IP)
6. Click **Create NAT gateway**
7. Wait for status to change from `Pending` to `Available` (1-2 minutes)
8. Go to **Route Tables** → select your private route table
9. **Routes** tab → **Edit routes** → Add route: `0.0.0.0/0` → select the NAT Gateway
10. **Save changes**

### Create NAT Gateway (CLI)

```bash
# Allocate Elastic IP for NAT Gateway
EIP_ALLOC=$(aws ec2 allocate-address \
  --domain vpc \
  --query 'AllocationId' \
  --output text)

# Create NAT Gateway in public subnet
NAT_GW=$(aws ec2 create-nat-gateway \
  --subnet-id $PUB_SUB_A \
  --allocation-id $EIP_ALLOC \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=Production-NAT}]' \
  --query 'NatGateway.NatGatewayId' \
  --output text)

# Wait for NAT Gateway to be available
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW

# Create private route table
PRIV_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=Private-RT}]' \
  --query 'RouteTable.RouteTableId' \
  --output text)

# Route internet traffic through NAT Gateway
aws ec2 create-route \
  --route-table-id $PRIV_RT \
  --destination-cidr-block 0.0.0.0/0 \
  --nat-gateway-id $NAT_GW

# Associate with private subnets
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_SUB_A
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_SUB_B
```

⚠️ **NAT Gateways cost ~$0.045/hour (~$32/month). Delete when not needed.**

---

## 5.8 Network ACLs (NACLs)

NACLs are stateless firewalls at the subnet level. They evaluate traffic entering and leaving a subnet.

```
Traffic flow with both NACLs and Security Groups:

  Internet
     │
     ▼
  ┌──────────────────────────────────────┐
  │  NACL (subnet-level firewall)        │  ← Checks INBOUND rules
  │  Rule 100: Allow HTTP from 0.0.0.0/0│     Rules evaluated in ORDER
  │  Rule 200: Allow SSH from my-ip      │     First match wins
  │  Rule *:   Deny all (default)        │     STATELESS: must allow
  └──────────┬───────────────────────────┘     return traffic explicitly
             │
             ▼
  ┌──────────────────────────────────────┐
  │  Security Group (instance-level)     │  ← Checks INBOUND rules
  │  Allow HTTP from 0.0.0.0/0          │     All rules evaluated
  │  Allow SSH from my-ip               │     STATEFUL: return traffic
  └──────────┬───────────────────────────┘     automatically allowed
             │
             ▼
         EC2 Instance
```

### Manual Steps via AWS Console: Create NACL

1. Go to **VPC → Network ACLs → Create network ACL**
2. Name: `Private-NACL`, select your VPC → **Create**
3. Select the NACL → **Inbound rules** tab → **Edit inbound rules**
4. Add rules (rule number determines priority — lower = evaluated first):
   - Rule 100: HTTP (80), Source `10.0.0.0/16`, Allow
   - Rule 110: HTTPS (443), Source `10.0.0.0/16`, Allow
   - Rule 120: SSH (22), Source `10.0.1.0/24`, Allow
5. Click **Save changes**
6. Go to **Outbound rules** tab → **Edit outbound rules**
7. Add rules:
   - Rule 100: Custom TCP, Port 1024-65535, Destination `0.0.0.0/0`, Allow (ephemeral ports for responses)
8. Go to **Subnet associations** tab → **Edit subnet associations**
9. Select your private subnets → **Save changes**

### Security Groups vs NACLs

| Feature | Security Group | NACL |
|---------|---------------|------|
| Level | Instance | Subnet |
| State | Stateful | Stateless |
| Rules | Allow only | Allow and Deny |
| Evaluation | All rules | Rules in order (by number) |
| Default | Deny all inbound | Allow all |

### Create a Custom NACL

```bash
NACL_ID=$(aws ec2 create-network-acl \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=network-acl,Tags=[{Key=Name,Value=Private-NACL}]' \
  --query 'NetworkAcl.NetworkAclId' \
  --output text)

# Allow inbound HTTP from VPC
aws ec2 create-network-acl-entry \
  --network-acl-id $NACL_ID \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=80,To=80 \
  --cidr-block 10.0.0.0/16 \
  --rule-action allow \
  --ingress

# Allow inbound HTTPS from VPC
aws ec2 create-network-acl-entry \
  --network-acl-id $NACL_ID \
  --rule-number 110 \
  --protocol tcp \
  --port-range From=443,To=443 \
  --cidr-block 10.0.0.0/16 \
  --rule-action allow \
  --ingress

# Allow outbound ephemeral ports (for responses)
aws ec2 create-network-acl-entry \
  --network-acl-id $NACL_ID \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --egress
```

---

## 5.9 VPC Peering

Connect two VPCs so they can communicate using private IP addresses, as if they were on the same network.

```
VPC-A (10.0.0.0/16) ←── Peering Connection ──→ VPC-B (10.1.0.0/16)

  Instance in VPC-A (10.0.1.10) can ping Instance in VPC-B (10.1.1.20)
  using private IPs — traffic never goes over the public internet.

Rules:
  - VPC CIDRs must NOT overlap
  - Peering is NOT transitive (A↔B and B↔C does NOT mean A↔C)
  - Works across AWS accounts and regions
  - Both sides must accept the peering and add routes
```

### Manual Steps via AWS Console: Create VPC Peering

1. Go to **VPC → Peering Connections → Create peering connection**
2. Name: `Dev-to-Prod`
3. Select **Requester VPC** (your VPC-A)
4. Select **Accepter VPC**: same account/same region → select VPC-B
5. Click **Create peering connection**
6. Select the new peering → **Actions → Accept request** (if same account)
7. Go to **Route Tables** for VPC-A → **Edit routes**:
   - Add route: Destination `10.1.0.0/16` → Target: select the peering connection
8. Go to **Route Tables** for VPC-B → **Edit routes**:
   - Add route: Destination `10.0.0.0/16` → Target: select the peering connection
9. Update **Security Groups** in both VPCs to allow traffic from the other VPC's CIDR

### Create VPC Peering (CLI)

```bash
# Create peering connection
PEERING_ID=$(aws ec2 create-vpc-peering-connection \
  --vpc-id vpc-111111 \
  --peer-vpc-id vpc-222222 \
  --tag-specifications 'ResourceType=vpc-peering-connection,Tags=[{Key=Name,Value=Dev-to-Prod}]' \
  --query 'VpcPeeringConnection.VpcPeeringConnectionId' \
  --output text)

# Accept the peering (if same account)
aws ec2 accept-vpc-peering-connection \
  --vpc-peering-connection-id $PEERING_ID

# Add routes in both VPCs
# In VPC-1 route table: route to VPC-2 CIDR via peering
aws ec2 create-route \
  --route-table-id rtb-111111 \
  --destination-cidr-block 10.1.0.0/16 \
  --vpc-peering-connection-id $PEERING_ID

# In VPC-2 route table: route to VPC-1 CIDR via peering
aws ec2 create-route \
  --route-table-id rtb-222222 \
  --destination-cidr-block 10.0.0.0/16 \
  --vpc-peering-connection-id $PEERING_ID
```

⚠️ VPC Peering is NOT transitive. If A↔B and B↔C, A cannot reach C through B.

---

## 5.10 Transit Gateway

Transit Gateway solves the VPC Peering scalability problem. Instead of creating peer connections between every pair of VPCs (which grows exponentially), you connect all VPCs to a single Transit Gateway hub.

### VPC Peering vs Transit Gateway

```
VPC Peering (mesh — doesn't scale):        Transit Gateway (hub-and-spoke):

  VPC-A ──── VPC-B                            VPC-A ──┐
    │  \    / │                                        │
    │   \  /  │                               VPC-B ──┤
    │    \/   │                                        ├── Transit Gateway
    │    /\   │                               VPC-C ──┤
    │   /  \  │                                        │
    │  /    \ │                               VPC-D ──┘
  VPC-C ──── VPC-D
                                              Any VPC can reach any other VPC
  6 peering connections for 4 VPCs            through the Transit Gateway.
  N*(N-1)/2 connections needed                Only N connections needed.
```

### When to Use Transit Gateway

```
Use Transit Gateway when:
  ✓ You have more than 2-3 VPCs that need to communicate
  ✓ You need transitive routing (A→B→C)
  ✓ You need to connect VPCs to on-premises networks (VPN/Direct Connect)
  ✓ You want centralized network management

Use VPC Peering when:
  ✓ You only have 2 VPCs to connect
  ✓ You want no additional cost (peering is free, data transfer is charged)
  ✓ You need the lowest possible latency
```

### Manual Steps: Create a Transit Gateway

**Step 1: Create the Transit Gateway**

```bash
TGW_ID=$(aws ec2 create-transit-gateway \
  --description "Central hub for all VPCs" \
  --options '{
    "AmazonSideAsn": 64512,
    "AutoAcceptSharedAttachments": "enable",
    "DefaultRouteTableAssociation": "enable",
    "DefaultRouteTablePropagation": "enable",
    "DnsSupport": "enable"
  }' \
  --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=Central-TGW}]' \
  --query 'TransitGateway.TransitGatewayId' \
  --output text)

echo "Transit Gateway: $TGW_ID"

# Wait for it to become available (takes 1-2 minutes)
aws ec2 describe-transit-gateways \
  --transit-gateway-ids $TGW_ID \
  --query 'TransitGateways[0].State'
# Wait until: "available"
```

**Step 2: Attach VPCs to the Transit Gateway**

```bash
# Attach VPC-A
TGW_ATTACH_A=$(aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $TGW_ID \
  --vpc-id vpc-aaaa1111 \
  --subnet-ids subnet-a1 subnet-a2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=VPC-A-Attachment}]' \
  --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
  --output text)

# Attach VPC-B
TGW_ATTACH_B=$(aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $TGW_ID \
  --vpc-id vpc-bbbb2222 \
  --subnet-ids subnet-b1 subnet-b2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=VPC-B-Attachment}]' \
  --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
  --output text)

# Attach VPC-C
TGW_ATTACH_C=$(aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $TGW_ID \
  --vpc-id vpc-cccc3333 \
  --subnet-ids subnet-c1 subnet-c2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=VPC-C-Attachment}]' \
  --query 'TransitGatewayVpcAttachment.TransitGatewayAttachmentId' \
  --output text)

echo "Attachments: $TGW_ATTACH_A, $TGW_ATTACH_B, $TGW_ATTACH_C"
```

**Step 3: Update VPC Route Tables**

Each VPC needs a route pointing to the Transit Gateway for the other VPCs' CIDR blocks.

```bash
# In VPC-A route table: route to VPC-B and VPC-C via Transit Gateway
aws ec2 create-route \
  --route-table-id rtb-aaaa \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-id $TGW_ID

aws ec2 create-route \
  --route-table-id rtb-aaaa \
  --destination-cidr-block 10.2.0.0/16 \
  --transit-gateway-id $TGW_ID

# In VPC-B route table: route to VPC-A and VPC-C
aws ec2 create-route \
  --route-table-id rtb-bbbb \
  --destination-cidr-block 10.0.0.0/16 \
  --transit-gateway-id $TGW_ID

aws ec2 create-route \
  --route-table-id rtb-bbbb \
  --destination-cidr-block 10.2.0.0/16 \
  --transit-gateway-id $TGW_ID

# In VPC-C route table: route to VPC-A and VPC-B
aws ec2 create-route \
  --route-table-id rtb-cccc \
  --destination-cidr-block 10.0.0.0/16 \
  --transit-gateway-id $TGW_ID

aws ec2 create-route \
  --route-table-id rtb-cccc \
  --destination-cidr-block 10.1.0.0/16 \
  --transit-gateway-id $TGW_ID
```

**Step 4: Verify Connectivity**

```bash
# List all Transit Gateway attachments
aws ec2 describe-transit-gateway-attachments \
  --filters "Name=transit-gateway-id,Values=$TGW_ID" \
  --query 'TransitGatewayAttachments[].{ID:TransitGatewayAttachmentId,VPC:ResourceId,State:State}' \
  --output table

# Expected Output:
# -------------------------------------------------------
# |         DescribeTransitGatewayAttachments            |
# +------------------+----------------+------------------+
# |        ID        |     State      |       VPC        |
# +------------------+----------------+------------------+
# | tgw-attach-aaa   | available      | vpc-aaaa1111     |
# | tgw-attach-bbb   | available      | vpc-bbbb2222     |
# | tgw-attach-ccc   | available      | vpc-cccc3333     |
# +------------------+----------------+------------------+

# Check Transit Gateway route table
TGW_RT=$(aws ec2 describe-transit-gateway-route-tables \
  --filters "Name=transit-gateway-id,Values=$TGW_ID" \
  --query 'TransitGatewayRouteTables[0].TransitGatewayRouteTableId' \
  --output text)

aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id $TGW_RT \
  --filters "Name=state,Values=active" \
  --query 'Routes[].{CIDR:DestinationCidrBlock,Attachment:TransitGatewayAttachments[0].TransitGatewayAttachmentId}' \
  --output table

# Test from an instance in VPC-A: ping an instance in VPC-B
ssh -i key.pem ec2-user@<VPC-A-instance>
ping 10.1.0.50   # VPC-B instance private IP
```

### Manual Steps via AWS Console

1. Go to **VPC → Transit Gateways → Create Transit Gateway**
2. Name it, keep default ASN (64512), enable DNS support
3. Go to **Transit Gateway Attachments → Create Attachment**
4. Select the Transit Gateway, choose VPC, select subnets (one per AZ)
5. Repeat for each VPC you want to connect
6. Go to each VPC's **Route Tables** → Add routes pointing to the Transit Gateway for other VPCs' CIDR blocks
7. Verify: launch instances in each VPC and test connectivity with `ping`

### Delete Transit Gateway Resources

```bash
# Delete attachments first
aws ec2 delete-transit-gateway-vpc-attachment --transit-gateway-attachment-id $TGW_ATTACH_A
aws ec2 delete-transit-gateway-vpc-attachment --transit-gateway-attachment-id $TGW_ATTACH_B
aws ec2 delete-transit-gateway-vpc-attachment --transit-gateway-attachment-id $TGW_ATTACH_C

# Wait for attachments to be deleted, then delete Transit Gateway
aws ec2 delete-transit-gateway --transit-gateway-id $TGW_ID
```

---

## 5.11 AWS Direct Connect

Direct Connect provides a dedicated, private network connection from your on-premises data center to AWS. Traffic does NOT go over the public internet.

### How Direct Connect Works

```
┌──────────────────┐                              ┌──────────────────┐
│  Your Data Center │                              │  AWS Cloud        │
│                   │     Dedicated fiber link      │                   │
│  ┌─────────┐     │◄────────────────────────────▶│  ┌─────────────┐ │
│  │ Servers  │     │     (1 Gbps or 10 Gbps)      │  │  VPC         │ │
│  │ Databases│     │                              │  │  EC2, RDS    │ │
│  │ Apps     │     │     NOT over the internet     │  │  S3          │ │
│  └─────────┘     │                              │  └─────────────┘ │
│                   │                              │                   │
│  ┌─────────┐     │     ┌──────────────────┐     │  ┌─────────────┐ │
│  │ Your    │─────┼────▶│ Direct Connect   │────▶│──│ Virtual     │ │
│  │ Router  │     │     │ Location (coloc) │     │  │ Private GW  │ │
│  └─────────┘     │     └──────────────────┘     │  └─────────────┘ │
└──────────────────┘                              └──────────────────┘
```

### Direct Connect vs VPN

| Feature | Direct Connect | Site-to-Site VPN |
|---------|---------------|-----------------|
| **Connection** | Dedicated fiber | Encrypted tunnel over internet |
| **Bandwidth** | 1 Gbps, 10 Gbps, 100 Gbps | Up to 1.25 Gbps per tunnel |
| **Latency** | Consistent, low | Variable (depends on internet) |
| **Setup time** | Weeks to months | Minutes |
| **Cost** | Higher (port + data transfer) | Lower (~$0.05/hour per connection) |
| **Encryption** | Not encrypted by default | Encrypted (IPSec) |
| **Use case** | Large data transfers, hybrid apps | Quick setup, backup connection |

### Direct Connect Components

```
1. Direct Connect Location
   - A physical colocation facility where AWS has equipment
   - You (or your partner) place a router here
   - AWS provides a cross-connect to their router

2. Virtual Interface (VIF)
   - Private VIF → access VPC resources via private IPs
   - Public VIF  → access AWS public services (S3, DynamoDB)
   - Transit VIF → access multiple VPCs via Transit Gateway

3. Direct Connect Gateway
   - Connects your Direct Connect to VPCs in multiple regions
   - Without it, Direct Connect only reaches VPCs in the same region
```

### Manual Steps: Set Up Direct Connect

**Step 1: Request a Direct Connect Connection**

```bash
# Create a Direct Connect connection
aws directconnect create-connection \
  --location "EqDC2" \
  --bandwidth "1Gbps" \
  --connection-name "DC-to-AWS" \
  --tags key=Environment,value=production

# Expected Output:
# {
#     "connectionId": "dxcon-abc12345",
#     "connectionName": "DC-to-AWS",
#     "connectionState": "requested",
#     "region": "us-east-1",
#     "location": "EqDC2",
#     "bandwidth": "1Gbps"
# }
```

**Step 2: Create a Virtual Private Gateway and attach to VPC**

```bash
# Create Virtual Private Gateway
VGW_ID=$(aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512 \
  --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=DC-VGW}]' \
  --query 'VpnGateway.VpnGatewayId' \
  --output text)

# Attach to VPC
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id $VGW_ID \
  --vpc-id $VPC_ID

# Enable route propagation in your route table
aws ec2 enable-vgw-route-propagation \
  --route-table-id $PRIV_RT \
  --gateway-id $VGW_ID
```

**Step 3: Create a Private Virtual Interface**

```bash
aws directconnect create-private-virtual-interface \
  --connection-id dxcon-abc12345 \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "DC-Private-VIF",
    "vlan": 101,
    "asn": 65000,
    "authKey": "your-bgp-auth-key",
    "amazonAddress": "169.254.255.1/30",
    "customerAddress": "169.254.255.2/30",
    "virtualGatewayId": "'$VGW_ID'"
  }'
```

**Step 4: Verify the Connection**

```bash
# Check connection state
aws directconnect describe-connections \
  --connection-id dxcon-abc12345 \
  --query 'connections[0].{Name:connectionName,State:connectionState,Bandwidth:bandwidth}'

# Check virtual interface state
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[].{Name:virtualInterfaceName,State:virtualInterfaceState,VLAN:vlan}'
```

### Manual Steps via AWS Console: Set Up Direct Connect

1. Go to **Direct Connect → Connections → Create connection**
2. Choose connection type:
   - **Dedicated**: 1/10/100 Gbps, physical port at a Direct Connect location
   - **Hosted**: Sub-1 Gbps through an AWS Partner (easier to set up)
3. Select a **Direct Connect location** near your data center
4. Select bandwidth → **Create connection**
5. AWS sends a Letter of Authorization (LOA) — give this to your colocation provider to set up the cross-connect
6. Wait for connection state to change to `available` (can take days/weeks for physical setup)
7. Go to **Virtual Private Gateways → Create** → attach to your VPC
8. Go to **Direct Connect → Virtual Interfaces → Create**:
   - Type: Private Virtual Interface
   - Connection: select your DX connection
   - Virtual Private Gateway: select the one you created
   - VLAN: assign a VLAN ID
   - BGP ASN: your on-premises router's ASN
9. Configure BGP on your on-premises router with the provided Amazon peer IP
10. Verify: BGP state should show `up` in the console

### Direct Connect + VPN (Encrypted Direct Connect)

Direct Connect is NOT encrypted by default. For encryption, run a Site-to-Site VPN over the Direct Connect connection:

```bash
# Create a Customer Gateway (your on-premises router)
CGW_ID=$(aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --bgp-asn 65000 \
  --ip-address 203.0.113.50 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=OnPrem-Router}]' \
  --query 'CustomerGateway.CustomerGatewayId' \
  --output text)

# Create VPN connection over Direct Connect
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id $CGW_ID \
  --vpn-gateway-id $VGW_ID \
  --options '{"StaticRoutesOnly": false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=DX-VPN-Encrypted}]'
```

### Delete Direct Connect Resources

```bash
# Delete in reverse order
aws directconnect delete-virtual-interface --virtual-interface-id dxvif-abc123
aws ec2 detach-vpn-gateway --vpn-gateway-id $VGW_ID --vpc-id $VPC_ID
aws ec2 delete-vpn-gateway --vpn-gateway-id $VGW_ID
aws directconnect delete-connection --connection-id dxcon-abc12345
```

---

## 5.12 VPC Endpoints

Access AWS services (S3, DynamoDB) without going through the internet. Traffic stays on the AWS private network.

### Manual Steps via AWS Console: Create VPC Endpoint

**Gateway Endpoint (S3/DynamoDB):**
1. Go to **VPC → Endpoints → Create endpoint**
2. Name: `S3-Endpoint`
3. Service category: **AWS services**
4. Search for `s3` → select `com.amazonaws.us-east-1.s3` (Gateway type)
5. Select your VPC
6. Select route tables to add the endpoint route to (private route tables)
7. Click **Create endpoint**

**Interface Endpoint (other services):**
1. Go to **VPC → Endpoints → Create endpoint**
2. Name: `SecretsManager-Endpoint`
3. Search for `secretsmanager` → select the Interface type
4. Select your VPC, subnets, and security group
5. Click **Create endpoint**

### Gateway Endpoint (S3, DynamoDB — free)

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids $PRIV_RT \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=S3-Endpoint}]'
```

### Interface Endpoint (other services — charged)

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.us-east-1.secretsmanager \
  --subnet-ids $PRIV_SUB_A $PRIV_SUB_B \
  --security-group-ids sg-xxx \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=SecretsManager-Endpoint}]'
```

---

## 5.13 Application Load Balancer (ALB)

### Create ALB

```bash
# Create ALB security group
ALB_SG=$(aws ec2 create-security-group \
  --group-name alb-sg \
  --description "ALB Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name production-alb \
  --subnets $PUB_SUB_A $PUB_SUB_B \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create Target Group
TG_ARN=$(aws elbv2 create-target-group \
  --name web-servers \
  --protocol HTTP \
  --port 80 \
  --vpc-id $VPC_ID \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Register EC2 instances
aws elbv2 register-targets \
  --target-group-arn $TG_ARN \
  --targets Id=i-instance1 Id=i-instance2

# Create Listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN

# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' \
  --output text
```

**Expected Output:**
```
production-alb-1234567890.us-east-1.elb.amazonaws.com
```

---

## 5.14 Industry Project: Complete Production VPC

### Full VPC Setup Script

```bash
#!/bin/bash
set -e

REGION="us-east-1"
PROJECT="myapp"

echo "=== Creating Production VPC ==="

# VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT}-vpc}]" \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
echo "VPC: $VPC_ID"

# Subnets
PUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone ${REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-public-a}]" \
  --query 'Subnet.SubnetId' --output text)
PUB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 \
  --availability-zone ${REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-public-b}]" \
  --query 'Subnet.SubnetId' --output text)
PRIV_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 \
  --availability-zone ${REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-private-a}]" \
  --query 'Subnet.SubnetId' --output text)
PRIV_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.4.0/24 \
  --availability-zone ${REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-private-b}]" \
  --query 'Subnet.SubnetId' --output text)
DB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.5.0/24 \
  --availability-zone ${REGION}a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-db-a}]" \
  --query 'Subnet.SubnetId' --output text)
DB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.6.0/24 \
  --availability-zone ${REGION}b \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-db-b}]" \
  --query 'Subnet.SubnetId' --output text)

aws ec2 modify-subnet-attribute --subnet-id $PUB_A --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUB_B --map-public-ip-on-launch
echo "Subnets: Public($PUB_A, $PUB_B) Private($PRIV_A, $PRIV_B) DB($DB_A, $DB_B)"

# Internet Gateway
IGW=$(aws ec2 create-internet-gateway \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT}-igw}]" \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC_ID

# NAT Gateway
EIP=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
NAT=$(aws ec2 create-nat-gateway --subnet-id $PUB_A --allocation-id $EIP \
  --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=${PROJECT}-nat}]" \
  --query 'NatGateway.NatGatewayId' --output text)
echo "Waiting for NAT Gateway..."
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT

# Route Tables
PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT}-public-rt}]" \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_A > /dev/null
aws ec2 associate-route-table --route-table-id $PUB_RT --subnet-id $PUB_B > /dev/null

PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT}-private-rt}]" \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_A > /dev/null
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $PRIV_B > /dev/null
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $DB_A > /dev/null
aws ec2 associate-route-table --route-table-id $PRIV_RT --subnet-id $DB_B > /dev/null

# S3 Gateway Endpoint (free)
aws ec2 create-vpc-endpoint --vpc-id $VPC_ID \
  --service-name com.amazonaws.${REGION}.s3 \
  --route-table-ids $PRIV_RT > /dev/null

echo ""
echo "=== VPC Setup Complete ==="
echo "VPC:         $VPC_ID"
echo "Public:      $PUB_A, $PUB_B"
echo "Private:     $PRIV_A, $PRIV_B"
echo "Database:    $DB_A, $DB_B"
echo "IGW:         $IGW"
echo "NAT:         $NAT"
```

---

## 5.15 Common Errors & Troubleshooting

### Error 1: EC2 instance has no internet access
```bash
# Checklist:
# 1. Is it in a public subnet?
aws ec2 describe-subnets --subnet-ids subnet-xxx \
  --query 'Subnets[0].MapPublicIpOnLaunch'

# 2. Does the route table have 0.0.0.0/0 → igw?
aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=subnet-xxx" \
  --query 'RouteTables[0].Routes'

# 3. Does the instance have a public IP?
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# 4. Does the security group allow outbound traffic?
aws ec2 describe-security-groups --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissionsEgress'
```

### Error 2: "VpcLimitExceeded"
```
An error occurred (VpcLimitExceeded): The maximum number of VPCs has been reached.
```
**Fix:** Default limit is 5 VPCs per region. Request increase:
```bash
aws service-quotas request-service-quota-increase \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --desired-value 10
```

### Error 3: Private instance can't reach internet
**Fix:** Ensure NAT Gateway is in a public subnet with a route to IGW, and private subnet routes 0.0.0.0/0 to the NAT Gateway.

### Error 4: "SubnetNotFound" when launching EC2
**Fix:** Ensure the subnet is in the same AZ/region you're targeting:
```bash
aws ec2 describe-subnets --subnet-ids subnet-xxx \
  --query 'Subnets[0].{AZ:AvailabilityZone,VPC:VpcId}'
```

---

## 5.16 Bastion Hosts

A bastion host (jump box) is an EC2 instance in a public subnet that you SSH into, then SSH from there into private instances.

```
Internet ──▶ Bastion Host (public subnet) ──▶ Private EC2 (private subnet)
              SG: allow port 22 from your IP     SG: allow port 22 from Bastion SG
```

```bash
# Bastion security group: allow SSH from your IP only
aws ec2 authorize-security-group-ingress \
  --group-id sg-bastion \
  --protocol tcp --port 22 \
  --cidr 203.0.113.1/32

# Private instance SG: allow SSH from bastion SG only
aws ec2 authorize-security-group-ingress \
  --group-id sg-private \
  --protocol tcp --port 22 \
  --source-group sg-bastion
```

Alternative: Use **SSM Session Manager** instead of bastion hosts — no SSH keys, no open ports, full audit logging.

---

## 5.17 NAT Instance vs NAT Gateway

| Feature | NAT Instance | NAT Gateway |
|---------|-------------|-------------|
| **Managed** | You manage (patching, HA) | AWS managed |
| **Bandwidth** | Depends on instance type | Up to 100 Gbps |
| **Availability** | Single instance (use ASG for HA) | HA within AZ |
| **Cost** | Cheaper (t3.micro) | ~$0.045/hr + data |
| **Security Groups** | Yes | No (use NACLs) |
| **Source/Dest Check** | Must disable | N/A |
| **Best for** | Dev/test, cost savings | Production |

NAT Instance requires disabling source/destination check:

```bash
aws ec2 modify-instance-attribute \
  --instance-id i-0abc123 \
  --no-source-dest-check
```

---

## 5.18 Security Groups vs NACLs — Deep Comparison

| Feature | Security Group | NACL |
|---------|---------------|------|
| **Level** | Instance (ENI) | Subnet |
| **State** | Stateful (return traffic auto-allowed) | Stateless (must allow return traffic explicitly) |
| **Rules** | Allow rules only | Allow AND Deny rules |
| **Evaluation** | All rules evaluated | Rules evaluated in order (lowest number first) |
| **Default** | Deny all inbound, allow all outbound | Allow all inbound and outbound |
| **Association** | Instance can have multiple SGs | Subnet has exactly one NACL |

### NACL Rule Evaluation

Rules are evaluated in order by rule number. First match wins.

```
Rule 100: ALLOW TCP 80 from 0.0.0.0/0    ← Evaluated first
Rule 200: DENY  TCP 80 from 10.0.0.5/32  ← Never reached for port 80
Rule *:   DENY  all                       ← Default deny
```

### Ephemeral Ports

Clients use random high ports (1024-65535) for return traffic. NACLs must allow these:

```bash
# Allow ephemeral ports for return traffic
aws ec2 create-network-acl-entry \
  --network-acl-id acl-0abc123 \
  --rule-number 100 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 0.0.0.0/0 \
  --rule-action allow \
  --ingress
```

---

## 5.19 VPC Flow Logs

VPC Flow Logs capture IP traffic information for network interfaces in your VPC.

### Flow Log Levels

| Level | What It Captures |
|-------|-----------------|
| **VPC** | All ENIs in the VPC |
| **Subnet** | All ENIs in the subnet |
| **ENI** | Specific network interface |

### Flow Log Record Format

```
version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
2 123456789012 eni-0abc123 10.0.1.5 10.0.2.10 49152 3306 6 20 4000 1620140761 1620140821 ACCEPT OK
2 123456789012 eni-0abc123 203.0.113.5 10.0.1.5 0 0 1 4 336 1620140761 1620140821 REJECT OK
```

### Troubleshooting with Flow Logs

| Scenario | Inbound | Outbound | Cause |
|----------|---------|----------|-------|
| Request rejected | REJECT | — | Security Group or NACL blocking inbound |
| Request accepted, no response | ACCEPT | REJECT | NACL blocking outbound (stateless) |
| Request accepted, response OK | ACCEPT | ACCEPT | Working correctly |

```bash
# Create VPC Flow Log to CloudWatch
aws ec2 create-flow-log \
  --resource-type VPC \
  --resource-ids vpc-0abc123 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/VPCFlowLogsRole

# Create VPC Flow Log to S3
aws ec2 create-flow-log \
  --resource-type VPC \
  --resource-ids vpc-0abc123 \
  --traffic-type REJECT \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::my-flow-logs-bucket
```

---

## 5.20 VPN CloudHub

VPN CloudHub connects multiple on-premises sites through AWS. Each site has its own VPN connection to the same Virtual Private Gateway.

```
Site A (CGW) ──╲
                ╲
Site B (CGW) ────▶ Virtual Private Gateway ──▶ VPC
                ╱
Site C (CGW) ──╱

Sites can communicate with each other through the VGW (hub-and-spoke model)
```

- Low cost, uses public internet
- Traffic between sites goes through AWS (encrypted)
- Requires dynamic routing (BGP)

---

## 5.21 IPv6 in VPC

- All IPv6 addresses are public (no NAT needed)
- IPv4 cannot be disabled — dual-stack mode
- If an instance can't connect to the internet with IPv6, check:
  1. Route table has a route to `::/0` via IGW
  2. Security group allows IPv6 traffic
  3. NACL allows IPv6 traffic

### Egress-Only Internet Gateway

For IPv6 only — allows outbound traffic but blocks inbound (like NAT Gateway for IPv6).

```bash
aws ec2 create-egress-only-internet-gateway --vpc-id vpc-0abc123

# Add route for IPv6 outbound
aws ec2 create-route \
  --route-table-id rtb-0abc123 \
  --destination-ipv6-cidr-block ::/0 \
  --egress-only-internet-gateway-id eigw-0abc123
```

---

## 5.22 AWS Network Firewall

AWS Network Firewall provides fine-grained network traffic filtering at the VPC level.

- Operates at Layer 3 to Layer 7
- Supports domain name filtering, protocol detection, IPS/IDS
- Managed by AWS Firewall Manager across accounts
- Rules can filter by IP, port, protocol, domain name, and regex patterns

```
Internet ──▶ Network Firewall ──▶ ALB ──▶ EC2 instances
```

Use Network Firewall when you need more control than Security Groups and NACLs provide (e.g., block traffic to specific domains, deep packet inspection).

---

## 5.23 VPC — Additional Features

### DHCP Options Sets

Control DNS servers, domain names, NTP servers, and NetBIOS settings for instances in a VPC. You can create a new DHCP options set and associate it with a VPC, but you cannot modify an existing one.

```bash
# Create a custom DHCP options set (use your own DNS servers)
aws ec2 create-dhcp-options \
  --dhcp-configurations \
    "Key=domain-name,Values=corp.example.com" \
    "Key=domain-name-servers,Values=10.0.0.2,10.0.1.2" \
    "Key=ntp-servers,Values=169.254.169.123"

# Expected output:
# {
#   "DhcpOptions": {
#     "DhcpOptionsId": "dopt-0abcdef1234567890",
#     "DhcpConfigurations": [
#       {"Key": "domain-name", "Values": [{"Value": "corp.example.com"}]},
#       {"Key": "domain-name-servers", "Values": [{"Value": "10.0.0.2"}, {"Value": "10.0.1.2"}]},
#       {"Key": "ntp-servers", "Values": [{"Value": "169.254.169.123"}]}
#     ]
#   }
# }

# Associate with a VPC (replaces existing DHCP options)
aws ec2 associate-dhcp-options \
  --dhcp-options-id dopt-0abcdef1234567890 \
  --vpc-id vpc-0abcdef1234567890

# Revert to default (Amazon-provided DNS)
aws ec2 associate-dhcp-options --dhcp-options-id default --vpc-id vpc-0abcdef1234567890
```

**Real-life use case:** A company running Active Directory on EC2 sets custom DHCP options so all instances in the VPC use the AD DNS servers for name resolution, enabling domain-joined instances to resolve internal hostnames like `fileserver.corp.example.com`.

### Managed Prefix Lists

A set of CIDR blocks that you can reference in security groups and route tables. Simplifies management when the same IP ranges are used across multiple rules. AWS-managed prefix lists exist for S3, DynamoDB, CloudFront.

```bash
# Create a customer-managed prefix list
aws ec2 create-managed-prefix-list \
  --prefix-list-name "office-ips" \
  --max-entries 10 \
  --address-family IPv4 \
  --entries "Cidr=203.0.113.0/24,Description=NYC Office" \
            "Cidr=198.51.100.0/24,Description=London Office"

# Expected output:
# {
#   "PrefixList": {
#     "PrefixListId": "pl-0abcdef1234567890",
#     "PrefixListName": "office-ips",
#     "State": "create-complete",
#     "MaxEntries": 10
#   }
# }

# Use prefix list in a security group rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-0abcdef1234567890 \
  --ip-permissions "IpProtocol=tcp,FromPort=443,ToPort=443,PrefixListIds=[{PrefixListId=pl-0abcdef1234567890}]"

# View AWS-managed prefix lists (S3, DynamoDB)
aws ec2 describe-managed-prefix-lists \
  --filters Name=owner-id,Values=AWS \
  --query 'PrefixLists[].{Name:PrefixListName,Id:PrefixListId}'

# Expected output:
# [
#   {"Name": "com.amazonaws.us-east-1.s3", "Id": "pl-63a5400a"},
#   {"Name": "com.amazonaws.us-east-1.dynamodb", "Id": "pl-02cd2c6b"}
# ]

# Share prefix list across accounts via RAM
aws ram create-resource-share \
  --name "shared-office-ips" \
  --resource-arns arn:aws:ec2:us-east-1:123456789012:prefix-list/pl-0abcdef1234567890 \
  --principals 987654321098
```

### VPC Traffic Mirroring

Copy network traffic from ENIs to a target (another ENI or NLB) for inspection. Use for: content inspection, threat monitoring, troubleshooting. Source and target can be in different VPCs (via peering).

```bash
# Create a traffic mirror target (NLB for IDS/IPS)
aws ec2 create-traffic-mirror-target \
  --network-load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/net/ids-nlb/abcdef1234567890

# Expected output:
# {
#   "TrafficMirrorTarget": {
#     "TrafficMirrorTargetId": "tmt-0abcdef1234567890",
#     "Type": "network-load-balancer"
#   }
# }

# Create a traffic mirror filter (capture only HTTP/HTTPS)
aws ec2 create-traffic-mirror-filter \
  --description "http-traffic-only"

FILTER_ID="tmf-0abcdef1234567890"

aws ec2 create-traffic-mirror-filter-rule \
  --traffic-mirror-filter-id $FILTER_ID \
  --traffic-direction ingress \
  --rule-number 100 \
  --rule-action accept \
  --protocol 6 \
  --destination-port-range FromPort=80,ToPort=443

# Create a traffic mirror session (source ENI → target)
aws ec2 create-traffic-mirror-session \
  --network-interface-id eni-0abcdef1234567890 \
  --traffic-mirror-target-id tmt-0abcdef1234567890 \
  --traffic-mirror-filter-id $FILTER_ID \
  --session-number 1

# Expected output:
# {
#   "TrafficMirrorSession": {
#     "TrafficMirrorSessionId": "tms-0abcdef1234567890",
#     "VirtualNetworkId": 12345
#   }
# }
```

**Real-life use case:** A financial services company mirrors traffic from their payment processing ENIs to a Suricata IDS running behind an NLB. Security analysts inspect mirrored packets for anomalies without impacting production traffic.

### Network Access Analyzer

Identify unintended network access. Define access requirements, and the analyzer identifies paths that don't meet them. Example: find all resources accessible from the internet.

```bash
# Create a network access scope (find internet-accessible resources)
aws ec2 create-network-insights-access-scope \
  --match-paths '[{
    "Source": {"ResourceStatement": {"ResourceTypes": ["AWS::EC2::InternetGateway"]}},
    "Destination": {"ResourceStatement": {"ResourceTypes": ["AWS::EC2::NetworkInterface"]}}
  }]'

# Start analysis
aws ec2 start-network-insights-access-scope-analysis \
  --network-insights-access-scope-id nis-0abcdef1234567890

# Get findings
aws ec2 get-network-insights-access-scope-analysis-findings \
  --network-insights-access-scope-analysis-id nisa-0abcdef1234567890 \
  --query 'AnalysisFindings[].{Path:FindingComponents[0].Component.Id,Port:FindingComponents[-1].InboundHeader.DestinationPortRanges}'
```

### VPC Lattice

Application-layer networking service that connects services across VPCs and accounts. Replaces complex VPC peering and Transit Gateway setups for service-to-service communication.

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Service A    │────▶│   VPC Lattice    │────▶│ Service B    │
│ (VPC 1)      │     │  Service Network │     │ (VPC 2)      │
└──────────────┘     └──────────────────┘     └──────────────┘
```

```bash
# Create a service network
aws vpc-lattice create-service-network \
  --name my-service-network \
  --auth-type AWS_IAM

# Expected output:
# {
#   "arn": "arn:aws:vpc-lattice:us-east-1:123456789012:servicenetwork/sn-0abcdef",
#   "id": "sn-0abcdef",
#   "name": "my-service-network"
# }

# Associate a VPC with the service network
aws vpc-lattice create-service-network-vpc-association \
  --service-network-identifier sn-0abcdef \
  --vpc-identifier vpc-0abcdef1234567890

# Create a service
aws vpc-lattice create-service \
  --name order-service \
  --auth-type AWS_IAM

# Create a target group
aws vpc-lattice create-target-group \
  --name order-targets \
  --type INSTANCE \
  --config '{
    "Port": 8080,
    "Protocol": "HTTP",
    "VpcIdentifier": "vpc-0abcdef1234567890"
  }'
```

**Real-life use case:** A microservices architecture spans 5 VPCs across 3 AWS accounts. VPC Lattice creates a service network where any service can call any other service by DNS name, with IAM-based auth policies, without managing VPC peering or Transit Gateway routes.

### VPC Reachability Analyzer

Diagnostic tool that analyzes network paths between two resources in a VPC. Identifies configuration issues without sending actual traffic.

```bash
# Test if EC2 instance can reach RDS on port 3306
aws ec2 create-network-insights-path \
  --source eni-0abcdef1234567890 \
  --destination eni-0fedcba0987654321 \
  --protocol TCP \
  --destination-port 3306

# Expected output:
# {
#   "NetworkInsightsPath": {
#     "NetworkInsightsPathId": "nip-0abcdef1234567890"
#   }
# }

# Start the analysis
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-0abcdef1234567890

# Get results
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-0abcdef1234567890 \
  --query 'NetworkInsightsAnalyses[0].{Reachable:NetworkPathFound,Explanations:Explanations[].ExplanationCode}'

# Expected output (if blocked):
# {
#   "Reachable": false,
#   "Explanations": ["SECURITY_GROUP_MISSING_ALLOW_RULE"]
# }
```

### VPC Bandwidth Limits

VPC itself has no bandwidth limit, but individual components do:

| Component | Bandwidth Limit |
|-----------|----------------|
| Single EC2 instance | Depends on instance type (up to 200 Gbps for p4d.24xlarge) |
| NAT Gateway | 100 Gbps per gateway |
| VPC Peering | No limit (uses AWS backbone) |
| Transit Gateway | 50 Gbps per VPC attachment |
| VPN tunnel | 1.25 Gbps per tunnel |
| Direct Connect | 1/10/100 Gbps per connection |
| Internet Gateway | No limit (per-instance limits apply) |

```bash
# Check instance network performance
aws ec2 describe-instance-types --instance-types m5.xlarge \
  --query 'InstanceTypes[0].NetworkInfo.{Bandwidth:NetworkPerformance,ENA:EnaSupport}'

# Expected output:
# {
#   "Bandwidth": "Up to 10 Gigabit",
#   "ENA": "required"
# }
```

### AWS IP Ranges

AWS publishes all its IP ranges in a JSON file. Useful for firewall rules and security group configurations.

```bash
# Download AWS IP ranges
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | head -20

# Filter for a specific service and region
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | \
  jq '.prefixes[] | select(.service=="S3" and .region=="us-east-1") | .ip_prefix'

# Expected output:
# "3.5.0.0/19"
# "52.216.0.0/15"
# "54.231.0.0/16"

# Filter for EC2 Instance Connect ranges (for security groups)
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | \
  jq '.prefixes[] | select(.service=="EC2_INSTANCE_CONNECT" and .region=="us-east-1") | .ip_prefix'

# Expected output:
# "3.16.146.0/29"
```

### AWS Client VPN

Managed OpenVPN-based VPN for remote users to connect to AWS VPCs or on-premises networks.

```
Remote User ──▶ Client VPN Endpoint ──▶ VPC (private subnets)
                                    ──▶ On-premises (via Site-to-Site VPN)
```

```bash
# Create a Client VPN endpoint
aws ec2 create-client-vpn-endpoint \
  --client-cidr-block 10.100.0.0/16 \
  --server-certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/abcd-1234 \
  --authentication-options 'Type=certificate-authentication,MutualAuthentication={ClientRootCertificateChainArn=arn:aws:acm:us-east-1:123456789012:certificate/efgh-5678}' \
  --connection-log-options Enabled=true,CloudwatchLogGroup=/aws/clientvpn,CloudwatchLogStream=connections \
  --vpc-id vpc-0abcdef1234567890 \
  --split-tunnel

# Expected output:
# {
#   "ClientVpnEndpointId": "cvpn-endpoint-0abcdef1234567890",
#   "Status": {"Code": "pending-associate"},
#   "DnsName": "cvpn-endpoint-0abcdef1234567890.prod.clientvpn.us-east-1.amazonaws.com"
# }

# Associate with a subnet
aws ec2 associate-client-vpn-target-network \
  --client-vpn-endpoint-id cvpn-endpoint-0abcdef1234567890 \
  --subnet-id subnet-0abcdef1234567890

# Add authorization rule (allow access to VPC CIDR)
aws ec2 authorize-client-vpn-ingress \
  --client-vpn-endpoint-id cvpn-endpoint-0abcdef1234567890 \
  --target-network-cidr 10.0.0.0/16 \
  --authorize-all-groups

# Download client configuration
aws ec2 export-client-vpn-client-configuration \
  --client-vpn-endpoint-id cvpn-endpoint-0abcdef1234567890 \
  --output text > client-config.ovpn
```

**Real-life use case:** A company with 200 remote developers uses Client VPN with mutual certificate authentication. Split-tunnel mode routes only VPC-bound traffic through the VPN, keeping internet traffic local for better performance.

### Accelerated Site-to-Site VPN

Uses AWS Global Accelerator to route VPN traffic over the AWS global network instead of the public internet. Lower latency, more consistent performance.

```bash
# Create a VPN connection with acceleration enabled
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-0abcdef1234567890 \
  --transit-gateway-id tgw-0abcdef1234567890 \
  --options '{"EnableAcceleration": true}'

# Verify acceleration is enabled
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0abcdef1234567890 \
  --query 'VpnConnections[0].Options.EnableAcceleration'
# Expected output: true
```

**When to use:** On-premises site is geographically far from the AWS region. Example: office in Singapore connecting to us-east-1. Accelerated VPN routes traffic to the nearest AWS edge location, then uses the AWS backbone to reach the region.

### Transit Gateway — ECMP

Equal-Cost Multi-Path routing. Use multiple VPN tunnels simultaneously to increase bandwidth. Each VPN connection has 2 tunnels (1.25 Gbps each). With ECMP: 2 VPN connections = 4 tunnels = 5 Gbps.

```
                    ┌── VPN Connection 1 ── Tunnel A (1.25 Gbps)
                    │                    ── Tunnel B (1.25 Gbps)
On-Premises ────────┤
                    │                    ── Tunnel A (1.25 Gbps)
                    └── VPN Connection 2 ── Tunnel B (1.25 Gbps)
                                                    Total: 5 Gbps
```

```bash
# Enable ECMP on Transit Gateway
aws ec2 create-transit-gateway \
  --options '{"VpnEcmpSupport": "enable", "DefaultRouteTableAssociation": "enable"}'

# Create multiple VPN connections to the same TGW
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-0abcdef1234567890 \
  --transit-gateway-id tgw-0abcdef1234567890

aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-0abcdef1234567890 \
  --transit-gateway-id tgw-0abcdef1234567890

# Verify ECMP is enabled
aws ec2 describe-transit-gateways \
  --transit-gateway-ids tgw-0abcdef1234567890 \
  --query 'TransitGateways[0].Options.VpnEcmpSupport'
# Expected output: "enable"
```

### Direct Connect — Resiliency Levels

| Level | Configuration | SLA |
|-------|---------------|-----|
| **Maximum** | 2 locations, 2 connections each (4 total) | 99.99% |
| **High** | 2 locations, 1 connection each (2 total) | 99.9% |
| **Development** | 1 location, 1 connection | No SLA |

```bash
# Describe Direct Connect connections
aws directconnect describe-connections

# Expected output:
# {
#   "connections": [
#     {
#       "connectionId": "dxcon-abcdef12",
#       "connectionName": "primary-dc",
#       "connectionState": "available",
#       "location": "EqDC2",
#       "bandwidth": "10Gbps"
#     }
#   ]
# }

# Create a LAG (Link Aggregation Group) for bundling connections
aws directconnect create-lag \
  --number-of-connections 2 \
  --location EqDC2 \
  --connections-bandwidth 10Gbps \
  --lag-name "prod-lag"
```

### Jumbo Frames / MTU

- Default MTU: 1500 bytes
- Jumbo frames: 9001 bytes (supported within VPC, Direct Connect, Transit Gateway)
- Not supported over: internet, VPN, VPC peering across regions

```bash
# Check current MTU on a Linux instance
ip link show eth0 | grep mtu
# eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9001 qdisc mq state UP

# Set MTU to jumbo frames
sudo ip link set dev eth0 mtu 9001

# Test path MTU discovery
ping -M do -s 8972 10.0.1.50
# PING 10.0.1.50 (10.0.1.50) 8972(9000) bytes of data.
# 8980 bytes from 10.0.1.50: icmp_seq=1 ttl=64 time=0.3 ms

# If jumbo frames not supported on path, you'll see:
# ping: local error: message too long, mtu=1500

# Tracepath to discover MTU along the path
tracepath 10.0.1.50
# Resume: pmtu 9001 hops 1 back 1
```

**When to use jumbo frames:** High-throughput workloads within a VPC (e.g., HPC clusters, database replication). Reduces CPU overhead by sending fewer, larger packets.

### Private NAT Gateway

NAT Gateway in a private subnet (no internet access). Used for routing between overlapping CIDR ranges across VPCs or on-premises networks.

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ VPC A (10.0.0.0/16) │     │ Private NAT GW   │     │ VPC B (10.0.0.0/16) │
│ Instance: 10.0.1.5  │────▶│ Translates to    │────▶│ Instance: 10.0.1.5  │
│                     │     │ 100.64.x.x       │     │                     │
└─────────────────────┘     └──────────────────┘     └─────────────────────┘
                         (via Transit Gateway)
```

```bash
# Create a Private NAT Gateway (no Elastic IP needed)
aws ec2 create-nat-gateway \
  --subnet-id subnet-0abcdef1234567890 \
  --connectivity-type private

# Expected output:
# {
#   "NatGateway": {
#     "NatGatewayId": "nat-0abcdef1234567890",
#     "ConnectivityType": "private",
#     "NatGatewayAddresses": [{"PrivateIp": "100.64.0.10"}]
#   }
# }
```

### VPC Sharing (RAM)

Share subnets across accounts using AWS Resource Access Manager (RAM). The VPC owner shares subnets; participant accounts launch resources into shared subnets. Reduces VPC count and simplifies networking.

```bash
# Share a subnet with another account via RAM
aws ram create-resource-share \
  --name "shared-vpc-subnets" \
  --resource-arns arn:aws:ec2:us-east-1:123456789012:subnet/subnet-0abcdef1234567890 \
  --principals 987654321098

# Expected output:
# {
#   "resourceShare": {
#     "resourceShareArn": "arn:aws:ram:us-east-1:123456789012:resource-share/abcd-1234",
#     "name": "shared-vpc-subnets",
#     "status": "ACTIVE"
#   }
# }

# In the participant account: accept the share
aws ram accept-resource-share-invitation \
  --resource-share-invitation-arn arn:aws:ram:us-east-1:987654321098:resource-share-invitation/abcd-5678

# Participant can now launch resources in the shared subnet
aws ec2 run-instances \
  --subnet-id subnet-0abcdef1234567890 \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --min-count 1 --max-count 1
```

**Real-life use case:** A company with 10 AWS accounts shares a central VPC's subnets. Each team launches their resources in shared subnets, reducing the number of VPCs from 10 to 1 and eliminating the need for VPC peering between teams.

### VPCs with Overlapping CIDRs

When two VPCs or a VPC and on-premises network use the same CIDR range, direct routing is impossible. Solutions:

```bash
# Solution 1: Private NAT Gateway (translate addresses)
# See Private NAT Gateway section above

# Solution 2: AWS PrivateLink (expose specific services)
# Create an NLB in VPC B, then create a VPC Endpoint Service
aws ec2 create-vpc-endpoint-service-configuration \
  --network-load-balancer-arns arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/net/my-nlb/abcdef \
  --acceptance-required

# In VPC A, create an interface endpoint to the service
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0aaaa \
  --service-name com.amazonaws.vpce.us-east-1.vpce-svc-0abcdef \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0abcdef
```

---

## 5.24 Key Takeaways

1. Always use custom VPCs (not default) for production
2. Use at least 2 AZs for high availability
3. Public subnets = Internet Gateway route; Private subnets = NAT Gateway route
4. AWS reserves 5 IPs per subnet — plan CIDR sizes accordingly
5. Use VPC Endpoints for S3/DynamoDB to avoid NAT Gateway costs
6. Security Groups (stateful, instance-level) + NACLs (stateless, subnet-level) = defense in depth
7. Plan CIDR blocks carefully — they can't be changed after creation
8. NAT Gateways cost money — consider NAT instances for dev environments
9. Use VPC Peering for 2 VPCs; use Transit Gateway for 3+ VPCs
10. VPC Peering is NOT transitive — Transit Gateway solves this
11. Use Direct Connect for dedicated, low-latency hybrid connectivity; use VPN for quick/encrypted setup
12. Use SSM Session Manager instead of bastion hosts when possible
13. VPC Flow Logs: ACCEPT+REJECT = SG issue; ACCEPT on inbound + REJECT on outbound = NACL issue
14. NACLs are stateless — always allow ephemeral ports (1024-65535) for return traffic
15. VPN CloudHub connects multiple on-prem sites through a single VGW
