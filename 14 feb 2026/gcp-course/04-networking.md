# Module 4: Networking

---

## 4.1 Virtual Private Cloud (VPC)

A VPC is a private, isolated network within GCP. All resources (VMs, databases, GKE clusters) live inside a VPC.

### Key Concepts

- **VPC**: A global resource spanning all regions
- **Subnet**: A regional resource with an IP range (CIDR block)
- **Firewall Rule**: Controls ingress/egress traffic
- **Route**: Determines where traffic is sent

### Default VPC

Every project gets a `default` VPC with one subnet per region. For production, create custom VPCs.

### Creating a Custom VPC

```bash
# Create a VPC (custom subnet mode — you define subnets manually)
gcloud compute networks create my-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=regional
```

**What each flag does:**
- `--subnet-mode=custom`: You manually create subnets (recommended for production)
- `--subnet-mode=auto`: Auto-creates one subnet per region (fine for dev)
- `--bgp-routing-mode=regional`: Routes advertised within region only

**Output:**
```
Created [https://www.googleapis.com/compute/v1/projects/my-project/global/networks/my-vpc].
NAME    SUBNET_MODE  BGP_ROUTING_MODE  IPV4_RANGE  GATEWAY_IPV4
my-vpc  CUSTOM       REGIONAL
```

### Creating Subnets

```bash
# Create a subnet for web servers
gcloud compute networks subnets create web-subnet \
  --network=my-vpc \
  --region=us-central1 \
  --range=10.0.1.0/24 \
  --enable-private-ip-google-access

# Create a subnet for databases
gcloud compute networks subnets create db-subnet \
  --network=my-vpc \
  --region=us-central1 \
  --range=10.0.2.0/24 \
  --enable-private-ip-google-access

# Create a subnet in another region
gcloud compute networks subnets create web-subnet-eu \
  --network=my-vpc \
  --region=europe-west1 \
  --range=10.1.1.0/24
```

**What `--enable-private-ip-google-access` does:** Allows VMs without external IPs to reach Google APIs (Cloud Storage, BigQuery, etc.) via internal networking.

**Output:**
```
Created [https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/subnetworks/web-subnet].
NAME        REGION       NETWORK  RANGE        STACK_TYPE  IPV6_ACCESS_TYPE
web-subnet  us-central1  my-vpc   10.0.1.0/24  IPV4_ONLY
```

### Listing Networks and Subnets

```bash
gcloud compute networks list
```
**Output:**
```
NAME     SUBNET_MODE  BGP_ROUTING_MODE  IPV4_RANGE  GATEWAY_IPV4
default  AUTO         REGIONAL
my-vpc   CUSTOM       REGIONAL
```

```bash
gcloud compute networks subnets list --network=my-vpc
```
**Output:**
```
NAME            REGION         NETWORK  RANGE         STACK_TYPE
web-subnet      us-central1    my-vpc   10.0.1.0/24   IPV4_ONLY
db-subnet       us-central1    my-vpc   10.0.2.0/24   IPV4_ONLY
web-subnet-eu   europe-west1   my-vpc   10.1.1.0/24   IPV4_ONLY
```

---

## 4.2 Firewall Rules

Firewall rules control traffic to/from VMs. They are applied at the VPC level.

### Rule Components

- **Direction**: INGRESS (incoming) or EGRESS (outgoing)
- **Priority**: 0-65535 (lower = higher priority)
- **Action**: ALLOW or DENY
- **Target**: Which VMs (by tag or service account)
- **Source/Destination**: IP ranges, tags, or service accounts
- **Protocol/Port**: tcp:80, udp:53, icmp

### Creating Firewall Rules

```bash
# Allow SSH from anywhere (for management)
gcloud compute firewall-rules create allow-ssh \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=allow-ssh

# Allow HTTP/HTTPS to web servers only
gcloud compute firewall-rules create allow-web \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web-server

# Allow internal communication between all VMs in VPC
gcloud compute firewall-rules create allow-internal \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=all \
  --source-ranges=10.0.0.0/8

# Allow database access only from web subnet
gcloud compute firewall-rules create allow-db \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:5432 \
  --source-ranges=10.0.1.0/24 \
  --target-tags=database

# Deny all other ingress (explicit deny-all)
gcloud compute firewall-rules create deny-all-ingress \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=65534 \
  --action=DENY \
  --rules=all \
  --source-ranges=0.0.0.0/0
```

### Listing Firewall Rules

```bash
gcloud compute firewall-rules list --filter="network=my-vpc"
```
**Output:**
```
NAME              NETWORK  DIRECTION  PRIORITY  ALLOW                  DENY  DISABLED
allow-db          my-vpc   INGRESS    1000      tcp:5432                     False
allow-internal    my-vpc   INGRESS    1000      all                          False
allow-ssh         my-vpc   INGRESS    1000      tcp:22                       False
allow-web         my-vpc   INGRESS    1000      tcp:80,tcp:443               False
deny-all-ingress  my-vpc   INGRESS    65534                            all   False
```

---

## 4.3 Static IP Addresses

```bash
# Reserve a static external IP
gcloud compute addresses create my-static-ip \
  --region=us-central1

# List reserved IPs
gcloud compute addresses list
```
**Output:**
```
NAME          ADDRESS/RANGE  TYPE      PURPOSE  NETWORK  REGION       SUBNET  STATUS
my-static-ip  35.192.xx.xx   EXTERNAL                    us-central1          RESERVED
```

```bash
# Assign to a VM
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --address=my-static-ip \
  --network=my-vpc \
  --subnet=web-subnet \
  --tags=web-server,allow-ssh
```

---

## 4.4 Cloud NAT (Network Address Translation)

Allows VMs without external IPs to access the internet (for updates, API calls).

```bash
# Create a Cloud Router (required for NAT)
gcloud compute routers create my-router \
  --network=my-vpc \
  --region=us-central1

# Create Cloud NAT
gcloud compute routers nats create my-nat \
  --router=my-router \
  --region=us-central1 \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges
```

**What it does:** VMs in `my-vpc` without external IPs can now reach the internet through NAT. Incoming connections from the internet are still blocked.

**Real-world Use Case:** Database servers and backend workers should not have public IPs. Cloud NAT lets them download packages and call external APIs without exposure.

---

## 4.5 Load Balancing

GCP offers several load balancer types:

| Type | Layer | Scope | Use Case |
|------|-------|-------|----------|
| HTTP(S) LB | L7 | Global | Web apps, API gateways |
| TCP/SSL Proxy LB | L4 | Global | Non-HTTP TCP traffic |
| Network LB | L4 | Regional | UDP, high-performance TCP |
| Internal HTTP(S) LB | L7 | Regional | Internal microservices |
| Internal TCP/UDP LB | L4 | Regional | Internal databases |

### HTTP(S) Load Balancer (Most Common)

```bash
# Step 1: Create instance template
gcloud compute instance-templates create web-template \
  --machine-type=e2-medium \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=web-server \
  --network=my-vpc \
  --subnet=web-subnet \
  --metadata=startup-script='#!/bin/bash
    apt-get update && apt-get install -y nginx
    echo "Server: $(hostname)" > /var/www/html/index.html'

# Step 2: Create managed instance group
gcloud compute instance-groups managed create web-mig \
  --template=web-template \
  --size=2 \
  --zone=us-central1-a

# Step 3: Create a named port
gcloud compute instance-groups managed set-named-ports web-mig \
  --named-ports=http:80 \
  --zone=us-central1-a

# Step 4: Create health check
gcloud compute health-checks create http http-health-check \
  --port=80 \
  --request-path=/ \
  --check-interval=10s \
  --timeout=5s \
  --healthy-threshold=2 \
  --unhealthy-threshold=3

# Step 5: Create backend service
gcloud compute backend-services create web-backend \
  --protocol=HTTP \
  --port-name=http \
  --health-checks=http-health-check \
  --global

# Step 6: Add instance group to backend
gcloud compute backend-services add-backend web-backend \
  --instance-group=web-mig \
  --instance-group-zone=us-central1-a \
  --global

# Step 7: Create URL map
gcloud compute url-maps create web-map \
  --default-service=web-backend

# Step 8: Create HTTP proxy
gcloud compute target-http-proxies create web-proxy \
  --url-map=web-map

# Step 9: Create forwarding rule (the actual LB IP)
gcloud compute forwarding-rules create web-lb \
  --global \
  --target-http-proxy=web-proxy \
  --ports=80

# Get the LB IP
gcloud compute forwarding-rules describe web-lb --global --format="value(IPAddress)"
```
**Output:**
```
34.120.xx.xx
```

### HTTPS with Managed SSL Certificate

```bash
# Create managed SSL certificate
gcloud compute ssl-certificates create my-cert \
  --domains=myapp.example.com \
  --global

# Create HTTPS proxy
gcloud compute target-https-proxies create web-https-proxy \
  --url-map=web-map \
  --ssl-certificates=my-cert

# Create HTTPS forwarding rule
gcloud compute forwarding-rules create web-https-lb \
  --global \
  --target-https-proxy=web-https-proxy \
  --ports=443
```

---

## 4.6 Cloud DNS

Managed DNS service.

```bash
# Create a DNS zone
gcloud dns managed-zones create my-zone \
  --dns-name=example.com. \
  --description="Production DNS zone"

# Add an A record
gcloud dns record-sets create myapp.example.com. \
  --zone=my-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=34.120.xx.xx

# Add a CNAME record
gcloud dns record-sets create www.example.com. \
  --zone=my-zone \
  --type=CNAME \
  --ttl=300 \
  --rrdatas=myapp.example.com.

# List records
gcloud dns record-sets list --zone=my-zone
```
**Output:**
```
NAME                    TYPE   TTL    DATA
example.com.            NS     21600  ns-cloud-a1.googledomains.com.,...
example.com.            SOA    21600  ns-cloud-a1.googledomains.com. ...
myapp.example.com.      A      300    34.120.xx.xx
www.example.com.        CNAME  300    myapp.example.com.
```

---

## 4.7 Cloud CDN

Content Delivery Network — caches content at Google's edge locations.

```bash
# Enable CDN on an existing backend service
gcloud compute backend-services update web-backend \
  --enable-cdn \
  --global

# Configure cache settings
gcloud compute backend-services update web-backend \
  --cache-mode=CACHE_ALL_STATIC \
  --default-ttl=3600 \
  --max-ttl=86400 \
  --global
```

---

## 4.8 VPC Peering

Connect two VPCs so resources can communicate using internal IPs.

```bash
# Peer VPC-A with VPC-B
gcloud compute networks peerings create peer-a-to-b \
  --network=vpc-a \
  --peer-network=vpc-b \
  --auto-create-routes

# Peer VPC-B with VPC-A (must be done from both sides)
gcloud compute networks peerings create peer-b-to-a \
  --network=vpc-b \
  --peer-network=vpc-a \
  --auto-create-routes
```

**Limitation:** VPC peering is non-transitive. If A peers with B and B peers with C, A cannot reach C through B.

---

## 4.9 Cloud VPN

Connect your on-premises network to GCP over encrypted IPsec tunnel.

```bash
# Create a VPN gateway
gcloud compute vpn-gateways create my-vpn-gw \
  --network=my-vpc \
  --region=us-central1

# Create a Cloud Router
gcloud compute routers create my-vpn-router \
  --network=my-vpc \
  --region=us-central1 \
  --asn=65001

# Create a peer VPN gateway (your on-prem device)
gcloud compute external-vpn-gateways create on-prem-gw \
  --interfaces=0=203.0.113.1  # Your on-prem VPN device IP

# Create VPN tunnel
gcloud compute vpn-tunnels create my-tunnel \
  --vpn-gateway=my-vpn-gw \
  --peer-external-gateway=on-prem-gw \
  --peer-external-gateway-interface=0 \
  --region=us-central1 \
  --ike-version=2 \
  --shared-secret=MySharedSecret123! \
  --router=my-vpn-router \
  --vpn-gateway-interface=0
```

---

## 4.10 Shared VPC

Allows multiple projects to share a single VPC. The VPC lives in a "host project," and "service projects" use its subnets.

```bash
# Enable Shared VPC on host project
gcloud compute shared-vpc enable host-project-id

# Attach a service project
gcloud compute shared-vpc associated-projects add service-project-id \
  --host-project=host-project-id
```

**Real-world Use Case:** A company has 10 microservices in separate projects. Shared VPC lets them all communicate over internal IPs through a centrally managed network.

---

## 4.11 Real-world Example: Production Network Architecture

```
                    Internet
                       |
                [Cloud CDN + LB]
                       |
              ┌────────┴────────┐
              │   web-subnet    │  10.0.1.0/24
              │  (web servers)  │
              └────────┬────────┘
                       │ Firewall: allow tcp:8080
              ┌────────┴────────┐
              │   app-subnet    │  10.0.2.0/24
              │  (app servers)  │
              └────────┬────────┘
                       │ Firewall: allow tcp:5432
              ┌────────┴────────┐
              │   db-subnet     │  10.0.3.0/24
              │  (Cloud SQL)    │  No external IP
              └─────────────────┘
                       │
                  [Cloud NAT]
                  (outbound only)
```

```bash
# Build this architecture
gcloud compute networks create prod-vpc --subnet-mode=custom

gcloud compute networks subnets create web-subnet \
  --network=prod-vpc --region=us-central1 --range=10.0.1.0/24

gcloud compute networks subnets create app-subnet \
  --network=prod-vpc --region=us-central1 --range=10.0.2.0/24 \
  --enable-private-ip-google-access

gcloud compute networks subnets create db-subnet \
  --network=prod-vpc --region=us-central1 --range=10.0.3.0/24 \
  --enable-private-ip-google-access

# Web tier: allow HTTP from internet
gcloud compute firewall-rules create prod-allow-web \
  --network=prod-vpc --direction=INGRESS --priority=1000 \
  --action=ALLOW --rules=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 --target-tags=web

# App tier: allow from web subnet only
gcloud compute firewall-rules create prod-allow-app \
  --network=prod-vpc --direction=INGRESS --priority=1000 \
  --action=ALLOW --rules=tcp:8080 \
  --source-ranges=10.0.1.0/24 --target-tags=app

# DB tier: allow from app subnet only
gcloud compute firewall-rules create prod-allow-db \
  --network=prod-vpc --direction=INGRESS --priority=1000 \
  --action=ALLOW --rules=tcp:5432 \
  --source-ranges=10.0.2.0/24 --target-tags=db

# NAT for outbound internet (updates, external APIs)
gcloud compute routers create prod-router \
  --network=prod-vpc --region=us-central1
gcloud compute routers nats create prod-nat \
  --router=prod-router --region=us-central1 \
  --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
```

---

## Module 4 — Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `IP_RANGE_OVERLAP` | Subnet CIDR overlaps with existing | Use non-overlapping ranges |
| `RESOURCE_IN_USE_BY_ANOTHER_RESOURCE` | Trying to delete VPC with resources | Delete all VMs, subnets, firewall rules first |
| VM can't reach internet | No external IP and no Cloud NAT | Add Cloud NAT or assign external IP |
| VM can't reach Google APIs | Private IP without Google Access | Enable `--enable-private-ip-google-access` on subnet |
| LB returns 502 | Backend unhealthy | Check health check config and firewall rules |
| SSL cert stuck in PROVISIONING | DNS not pointing to LB IP | Update DNS A record to LB IP, wait up to 24h |

**Next: Module 5 — DevOps & CI/CD →**
