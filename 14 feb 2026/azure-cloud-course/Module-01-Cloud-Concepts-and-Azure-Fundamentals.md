# Module 01: Cloud Concepts & Azure Fundamentals

## Certification Relevance: AZ-900 (25-30% of exam)

---

## 1.1 What is a Data Center?

A data center is a physical facility that organizations use to house their servers, networking equipment, storage systems, and other IT infrastructure. It is the backbone of traditional IT operations.

### Components of a Data Center

```
Physical Data Center Layout:
┌─────────────────────────────────────────────────────────────┐
│                     DATA CENTER FACILITY                     │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   SERVER     │   NETWORK    │   STORAGE    │   SUPPORT     │
│   ROOM       │   ROOM       │   AREA       │   SYSTEMS     │
│              │              │              │               │
│ • Server     │ • Routers    │ • SAN/NAS    │ • UPS (Power  │
│   Racks      │ • Switches   │ • Tape       │   Backup)     │
│ • Blade      │ • Firewalls  │   Backups    │ • Generators  │
│   Servers    │ • Load       │ • RAID       │ • HVAC        │
│ • Tower      │   Balancers  │   Arrays     │   (Cooling)   │
│   Servers    │ • Cables     │ • Disk       │ • Fire        │
│ • Rack-mount │   (Fiber,    │   Shelves    │   Suppression │
│   Servers    │   Ethernet)  │              │ • Physical    │
│              │              │              │   Security    │
│              │              │              │ • CCTV        │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### Key Data Center Components Explained

| Component | Purpose | Cost Range |
|-----------|---------|------------|
| **Servers** | Run applications, databases, websites | $5,000 - $50,000+ per server |
| **Networking** | Connect servers to each other and the internet | $10,000 - $100,000+ |
| **Storage** | Store data (SAN, NAS, disk arrays) | $20,000 - $500,000+ |
| **Power (UPS + Generators)** | Ensure uninterrupted power supply | $50,000 - $500,000+ |
| **Cooling (HVAC)** | Prevent overheating — servers generate massive heat | $100,000 - $1,000,000+ |
| **Physical Security** | Biometric access, CCTV, security guards | $50,000+ per year |
| **Fire Suppression** | Protect equipment from fire damage | $20,000 - $100,000 |
| **Redundant Internet** | Multiple ISP connections for reliability | $5,000 - $50,000/month |

### Real-World Example
```
A mid-size company running their own data center:
- Rents 2,000 sq ft of space: $15,000/month
- 20 servers: $200,000 upfront
- Networking equipment: $50,000
- Cooling system: $100,000
- Power backup (UPS + generator): $75,000
- 3 IT staff to manage 24/7: $300,000/year in salaries
- Electricity bill: $10,000/month

Total Year 1 Cost: ~$900,000+
And this is BEFORE any software licenses!
```

---

## 1.2 How to Set Up a Server in a Traditional Data Center

Setting up a single server in a traditional data center is a lengthy, multi-step process involving multiple teams and weeks of lead time.

### The Traditional Server Setup Process

```
Step-by-Step: Setting Up a New Server in a Data Center

Week 1-2: PLANNING & PROCUREMENT
├── 1. Business team submits a request for a new server
├── 2. IT team evaluates requirements (CPU, RAM, storage, OS)
├── 3. Finance approves the budget ($5,000 - $50,000+)
├── 4. Procurement team orders the hardware from vendor (Dell, HP, Lenovo)
└── 5. Wait for delivery (1-4 weeks depending on supply chain)

Week 3-4: PHYSICAL SETUP
├── 6. Receive hardware and verify against purchase order
├── 7. Transport server to data center
├── 8. Mount server in rack (racking and stacking)
│   ├── Attach rail kits to the rack
│   ├── Slide server into position
│   └── Secure with screws
├── 9. Connect power cables (primary + redundant)
├── 10. Connect network cables (Ethernet/Fiber)
│   ├── Connect to Top-of-Rack (ToR) switch
│   ├── Assign VLAN and IP address
│   └── Configure firewall rules
└── 11. Connect to KVM (Keyboard, Video, Mouse) or iLO/iDRAC for remote management

Week 4-5: SOFTWARE & CONFIGURATION
├── 12. Install operating system (Windows Server / Linux)
│   ├── Boot from USB/DVD/PXE
│   ├── Partition disks
│   └── Configure RAID (if applicable)
├── 13. Install drivers and firmware updates
├── 14. Configure networking (static IP, DNS, gateway)
├── 15. Join domain (Active Directory)
├── 16. Install security patches and updates
├── 17. Install monitoring agents (Nagios, Zabbix, SCOM)
├── 18. Configure backup schedule
├── 19. Install application software
└── 20. Security hardening (disable unused ports, set firewall rules)

Week 5-6: TESTING & HANDOVER
├── 21. Run hardware diagnostics
├── 22. Performance testing (stress test CPU, RAM, disk I/O)
├── 23. Network connectivity testing
├── 24. Security scan and vulnerability assessment
├── 25. Documentation (IP address, credentials, config details)
└── 26. Hand over to application team

TOTAL TIME: 4-6 weeks (sometimes months)
PEOPLE INVOLVED: 5-10 (business, finance, procurement, network, server, security, app teams)
```

### The Same Server on Azure Cloud

```
Step-by-Step: Setting Up a New Server on Azure

Minute 1-2: PLANNING
├── 1. Choose VM size (e.g., Standard_D2s_v3: 2 vCPUs, 8 GB RAM)
└── 2. Choose region (e.g., East US)

Minute 2-5: CREATION
├── 3. Log into Azure Portal (portal.azure.com)
├── 4. Click "Create a resource" → "Virtual Machine"
├── 5. Fill in details:
│   ├── Resource Group: my-project-rg
│   ├── VM Name: web-server-01
│   ├── Region: East US
│   ├── Image: Ubuntu 22.04 LTS
│   ├── Size: Standard_D2s_v3
│   └── Authentication: SSH key
└── 6. Click "Review + Create" → "Create"

Minute 5-10: READY
├── 7. VM is provisioned and running
├── 8. Public IP assigned automatically
├── 9. SSH into the server immediately
└── 10. Install your application

TOTAL TIME: 5-10 minutes
PEOPLE INVOLVED: 1 (developer or IT admin)
COST: ~$70/month (pay-as-you-go, turn off when not needed)
```

---

## 1.3 Challenges of Traditional Data Centers

### Why Companies Struggled with Data Centers

```
┌─────────────────────────────────────────────────────────────┐
│              TRADITIONAL DATA CENTER CHALLENGES              │
├─────────────────────┬───────────────────────────────────────┤
│ CHALLENGE           │ IMPACT                                │
├─────────────────────┼───────────────────────────────────────┤
│ High Upfront Cost   │ $500K-$5M+ to build a data center    │
│ (CapEx)             │ Must pay before earning any revenue   │
├─────────────────────┼───────────────────────────────────────┤
│ Capacity Planning   │ Must guess future needs 3-5 years    │
│                     │ ahead. Over-provision = waste money.  │
│                     │ Under-provision = can't handle growth │
├─────────────────────┼───────────────────────────────────────┤
│ Slow Provisioning   │ 4-6 weeks to get a new server ready  │
│                     │ Slows down product launches           │
├─────────────────────┼───────────────────────────────────────┤
│ Hardware Failures   │ Servers fail, disks crash, power      │
│                     │ outages happen. Need 24/7 staff       │
├─────────────────────┼───────────────────────────────────────┤
│ Scaling Difficulty  │ Traffic spike? Buy more servers,      │
│                     │ wait weeks. Traffic drops? Servers     │
│                     │ sit idle, still costing money         │
├─────────────────────┼───────────────────────────────────────┤
│ Maintenance Burden  │ OS patches, firmware updates,         │
│                     │ hardware replacements, cooling        │
│                     │ maintenance — all on your team        │
├─────────────────────┼───────────────────────────────────────┤
│ Limited Geographic  │ Your data center is in one location.  │
│ Reach               │ Users far away experience latency     │
├─────────────────────┼───────────────────────────────────────┤
│ Disaster Recovery   │ Need a second data center for DR.     │
│                     │ Double the cost, double the effort    │
├─────────────────────┼───────────────────────────────────────┤
│ Security Costs      │ Physical security, compliance audits, │
│                     │ penetration testing — all expensive   │
├─────────────────────┼───────────────────────────────────────┤
│ Talent Shortage     │ Need specialized staff: network       │
│                     │ engineers, sysadmins, security        │
│                     │ experts, facilities managers          │
└─────────────────────┴───────────────────────────────────────┘
```

### Real-World Failure Stories
```
Example 1: The Startup That Over-Provisioned
A startup bought $200,000 worth of servers expecting rapid growth.
Growth didn't happen as fast as expected. Servers sat idle for 2 years.
Company ran out of money partly due to infrastructure costs.
On cloud: Would have cost $500/month, scaling up only when needed.

Example 2: The E-Commerce Site That Under-Provisioned
An online store had 10 servers. Black Friday traffic was 50x normal.
Site crashed for 6 hours. Lost $2 million in sales.
On cloud: Auto-scaling would have added 500 servers in minutes,
then scaled back down after the rush.

Example 3: The Company That Lost Data
A company's data center flooded. Backup tapes were stored in the
same building. Lost 5 years of customer data.
On cloud: Data automatically replicated across multiple regions.
Even if an entire region goes down, data is safe.
```

---

## 1.4 Why Cloud Computing Came Into Existence

### The Evolution: From Mainframes to Cloud

```
Timeline of Computing Infrastructure:

1960s-1970s: MAINFRAME ERA
├── Giant computers shared by multiple users (time-sharing)
├── Only large corporations and governments could afford them
└── Users accessed via dumb terminals

1980s-1990s: CLIENT-SERVER ERA
├── Personal computers became affordable
├── Companies built their own server rooms
├── Each department had its own servers
└── IT teams managed everything in-house

1990s-2000s: VIRTUALIZATION ERA
├── VMware introduced virtualization (1999)
├── One physical server could run multiple virtual servers
├── Better hardware utilization (from 10% to 60-70%)
└── Still required owning and managing physical hardware

2006: BIRTH OF CLOUD COMPUTING
├── Amazon launched AWS (S3 in March 2006, EC2 in August 2006)
├── Key insight: Amazon had massive infrastructure for peak
│   shopping (Black Friday). Rest of the year, it sat idle.
│   Why not rent it out to others?
└── This changed everything.

2008-2010: CLOUD GOES MAINSTREAM
├── Google launched App Engine (2008)
├── Microsoft launched Azure (February 2010)
└── Companies started migrating to cloud

2010-Present: CLOUD-FIRST WORLD
├── 94% of enterprises use cloud services (2024)
├── Global cloud market: $600+ billion (2024)
├── Cloud-native technologies: containers, Kubernetes, serverless
└── AI/ML services available on-demand via cloud
```

### Why Cloud Emerged — The Core Drivers

| Driver | Problem | Cloud Solution |
|--------|---------|----------------|
| **Cost** | Millions in upfront CapEx for data centers | Pay-as-you-go, no upfront cost |
| **Speed** | Weeks to provision new servers | Minutes to deploy globally |
| **Scale** | Fixed capacity, hard to scale | Virtually unlimited, elastic scaling |
| **Innovation** | IT teams spent 80% of time on maintenance | Focus on building products, not managing servers |
| **Globalization** | Single-location data centers | Deploy to 60+ regions worldwide instantly |
| **Reliability** | Single points of failure | Built-in redundancy across zones and regions |
| **Security** | Each company builds its own security | Cloud providers invest billions in security |

---

## 1.5 Cloud vs. Traditional Data Center — Full Comparison

| Aspect | Traditional Data Center | Cloud Computing |
|--------|------------------------|-----------------|
| **Upfront Cost** | $500K - $5M+ | $0 (pay-as-you-go) |
| **Time to Deploy** | 4-6 weeks | 5-10 minutes |
| **Scaling** | Buy hardware, wait weeks | Click a button, scale in minutes |
| **Scaling Down** | Hardware sits idle | Turn off resources, stop paying |
| **Geographic Reach** | 1-2 locations | 60+ regions worldwide |
| **Maintenance** | Your team (24/7 staff) | Cloud provider handles it |
| **Hardware Refresh** | Every 3-5 years (your cost) | Provider upgrades continuously |
| **Disaster Recovery** | Build a second data center | Enable replication to another region |
| **Security** | Your responsibility entirely | Shared responsibility model |
| **Compliance** | You handle audits and certifications | Provider holds 90+ compliance certifications |
| **Power & Cooling** | Your electricity bill | Included in service cost |
| **Innovation** | Limited by your hardware | Access to AI, ML, IoT, analytics on-demand |
| **Staffing** | Need 5-20+ specialized IT staff | 1-2 cloud engineers can manage |
| **Risk** | You bear all risk | Risk shared with provider |

### When Data Centers Still Make Sense
```
Not everything should move to cloud. Data centers are still used when:

1. Regulatory Requirements: Some industries (defense, government)
   require data to stay on-premises
2. Legacy Applications: Old applications that can't be easily migrated
3. Predictable Workloads: If usage is constant 24/7, owning hardware
   can be cheaper than cloud (rare, but possible)
4. Data Sovereignty: Laws requiring data to stay in a specific country
   where cloud providers don't have regions
5. Ultra-Low Latency: Applications needing sub-millisecond latency
   (high-frequency trading, some manufacturing)
```

---

## 1.6 What is Cloud Computing?

Cloud computing is the delivery of computing services (servers, storage, databases, networking, software, analytics, intelligence) over the internet ("the cloud") to offer faster innovation, flexible resources, and economies of scale.

### Real-Life Analogy
Think of cloud computing like electricity. Instead of every home having its own generator (on-premises server), you plug into the power grid (cloud) and pay for what you use. The power company (Microsoft Azure) manages the infrastructure.

### Key Cloud Benefits Over Traditional Data Centers

| Benefit | Data Center Problem | Cloud Solution | Example |
|---------|-------------------|----------------|---------|
| **No Upfront Cost** | $500K+ to start | $0 to start, pay monthly | Startup launches with $50/month |
| **Speed** | Weeks to deploy | Minutes to deploy | New server in 5 minutes |
| **Elasticity** | Fixed capacity | Auto-scale up and down | Handle 10x traffic spike automatically |
| **Global Reach** | One location | 60+ Azure regions | Serve users in US, Europe, Asia |
| **Reliability** | Single point of failure | Built-in redundancy | 99.99% uptime SLA |
| **Security** | Build your own | Microsoft invests $1B+/year in security | 3,500+ security experts |
| **Innovation** | Limited by hardware | Access to AI, ML, IoT | Add AI to your app in hours |

---

## 1.7 Cloud Service Models (IaaS vs PaaS vs SaaS)

### The Pizza Analogy — Understanding Service Models

```
Think of it like pizza:

ON-PREMISES (Traditional Data Center):
  You make everything yourself — grow tomatoes, make dough,
  build the oven, cook the pizza, set the table, eat at home.
  = You manage EVERYTHING

IaaS (Infrastructure as a Service):
  You buy a kitchen with an oven (rented infrastructure).
  You still make the dough, add toppings, and cook.
  = You manage the application, data, and OS

PaaS (Platform as a Service):
  You order a "make your own pizza" kit — dough and oven provided.
  You just add your toppings and it's cooked for you.
  = You manage only your application and data

SaaS (Software as a Service):
  You order pizza delivery. It arrives ready to eat.
  = You just consume it. Provider manages everything.
```

### IaaS (Infrastructure as a Service)
**What it is**: You rent IT infrastructure — servers, virtual machines, storage, networks — from a cloud provider on a pay-as-you-go basis.

**You manage**: OS, middleware, runtime, data, applications
**Provider manages**: Servers, storage, networking, virtualization

**Azure Examples**: Azure Virtual Machines, Azure Virtual Network, Azure Storage

**Real-World Example**: A startup needs servers for their web application but doesn't want to buy physical hardware.
```
Industry Example: Netflix uses IaaS to run thousands of virtual machines
for video encoding and streaming. They scale up during peak hours
(evenings, weekends) and scale down during off-peak times.
```

### PaaS (Platform as a Service)
**What it is**: A complete development and deployment environment in the cloud. You focus on building your application; the provider manages everything else.

**You manage**: Data, applications
**Provider manages**: OS, middleware, runtime, servers, storage, networking

**Azure Examples**: Azure App Service, Azure SQL Database, Azure Functions

**Real-World Example**: A development team wants to deploy a web app without managing servers.
```
Industry Example: A banking company deploys their mobile banking API
on Azure App Service. They write code, push to Git, and Azure handles
OS patches, load balancing, and scaling automatically.
```

### SaaS (Software as a Service)
**What it is**: Complete software solutions delivered over the internet. You use the application; the provider manages everything.

**You manage**: Data input, user configuration
**Provider manages**: Everything else

**Azure Examples**: Microsoft 365, Dynamics 365, Azure DevOps

**Real-World Example**:
```
Industry Example: A company uses Microsoft 365 for email, documents,
and collaboration. No servers to manage, no software to install —
just log in and use it.
```

### Comparison Table

| Aspect | On-Premises | IaaS | PaaS | SaaS |
|--------|------------|------|------|------|
| Applications | You | You | You | Provider |
| Data | You | You | You | Provider |
| Runtime | You | You | Provider | Provider |
| Middleware | You | You | Provider | Provider |
| OS | You | You | Provider | Provider |
| Virtualization | You | Provider | Provider | Provider |
| Servers | You | Provider | Provider | Provider |
| Storage | You | Provider | Provider | Provider |
| Networking | You | Provider | Provider | Provider |

### Exam Tip
```
AZ-900 frequently asks: "Which cloud model should you use when you need
full control over the operating system?" Answer: IaaS

"Which model allows developers to focus only on code?"
Answer: PaaS
```

---

## 1.8 Cloud Deployment Models (Public, Private, Hybrid)

### Public Cloud
- Resources owned and operated by a third-party cloud provider (Microsoft Azure, AWS, GCP)
- Delivered over the public internet
- Available to anyone who wants to purchase them

```
Advantages:
- No capital expenditure (CapEx)
- Pay only for what you use
- No maintenance of hardware
- Near-unlimited scalability

Disadvantages:
- Less control over security
- May not meet specific compliance requirements
- Dependent on internet connectivity
```

**Real-World Example**: An e-commerce startup uses Azure to host their website. During Black Friday, they scale to 100 servers. On normal days, they use 5 servers.

### Private Cloud
- Cloud resources used exclusively by one business or organization
- Can be physically located at the organization's on-site data center or hosted by a third party
- Hardware and software dedicated solely to your organization

```
Advantages:
- Full control over resources and security
- Meets strict regulatory/compliance requirements
- Customizable to specific business needs

Disadvantages:
- Higher costs (CapEx + OpEx)
- Limited scalability compared to public cloud
- Requires IT expertise to manage
```

**Real-World Example**: A government defense agency runs a private cloud in their own data center because classified data cannot leave their premises.

### Hybrid Cloud
- Combines public and private clouds, allowing data and applications to be shared between them
- Gives businesses greater flexibility and more deployment options

```
Advantages:
- Flexibility to choose where to run workloads
- Keep sensitive data on-premises, burst to cloud for extra capacity
- Gradual cloud migration path

Disadvantages:
- More complex to manage
- Requires integration between environments
- Potential compatibility issues
```

**Real-World Example**:
```
Industry Example: A hospital keeps patient records (HIPAA-compliant data)
in their private cloud but uses Azure public cloud for their
patient-facing appointment booking website. Azure Arc connects both
environments seamlessly.
```

### Exam Tip
```
AZ-900 question pattern: "A company wants to keep sensitive financial
data on-premises but use cloud for their public website. Which
deployment model should they use?"
Answer: Hybrid Cloud
```

---

## 1.9 Cloud Benefits (CapEx vs OpEx)

### Capital Expenditure (CapEx)
- Upfront spending on physical infrastructure
- Costs reduce over time (depreciation)
- Examples: Buying servers, building data centers

### Operational Expenditure (OpEx)
- Spending on products and services as needed
- Pay-as-you-go model
- Examples: Azure monthly bill, subscription services

```
CapEx Example:
- Buy a server: $10,000 upfront
- Useful life: 5 years
- Annual depreciation: $2,000/year
- You pay whether you use it or not

OpEx Example (Azure VM):
- Standard_B2s VM: ~$30/month
- Use it for 3 months: $90 total
- Turn it off when not needed: $0
- Scale up when needed: adjust monthly cost
```

### Key Cloud Benefits for Exam

| Benefit | Description | Example |
|---------|-------------|---------|
| **High Availability** | Systems remain operational with minimal downtime | Azure guarantees 99.99% uptime SLA for VMs in Availability Zones |
| **Scalability** | Ability to increase/decrease resources | Add more VMs during holiday sales |
| **Elasticity** | Automatic scaling based on demand | Auto-scale web servers from 2 to 20 during traffic spike |
| **Agility** | Quickly deploy and configure resources | Spin up a new environment in minutes |
| **Geo-distribution** | Deploy to regions worldwide | Host app in US, Europe, and Asia simultaneously |
| **Disaster Recovery** | Recover from failures | Replicate data to another region automatically |
| **Fault Tolerance** | Continue operating despite component failure | If one server fails, traffic routes to healthy servers |

---

## 1.10 What is Microsoft Azure?

Microsoft Azure is a cloud computing platform with 200+ products and services designed to help you build, run, and manage applications across multiple clouds, on-premises, and at the edge.

### Azure Global Infrastructure

```
Azure Geography → Contains Regions → Contains Availability Zones → Contains Data Centers

Example:
Geography: United States
├── Region: East US (Virginia)
│   ├── Availability Zone 1 → Data Center(s)
│   ├── Availability Zone 2 → Data Center(s)
│   └── Availability Zone 3 → Data Center(s)
├── Region: West US (California)
│   ├── Availability Zone 1
│   ├── Availability Zone 2
│   └── Availability Zone 3
└── Region: Central US (Iowa)
    └── ...
```

### Azure Regions
- **60+ regions** worldwide (more than any other cloud provider)
- Each region is a set of data centers deployed within a latency-defined perimeter
- Connected through a dedicated regional low-latency network

### Availability Zones
- Physically separate locations within an Azure region
- Each zone has independent power, cooling, and networking
- Minimum of 3 separate zones in enabled regions
- Connected with high-speed private fiber-optic networks

```
Why Availability Zones matter:

Without Zones: If the data center catches fire, your app goes down
With Zones: Your app runs in 3 separate buildings. If one burns down,
            the other two keep serving traffic. Users never notice.

Real-World Example: A banking application deploys across 3 availability
zones in East US. When Zone 1 had a cooling failure in 2023, the app
continued running on Zones 2 and 3 with zero customer impact.
```

### Region Pairs
- Each Azure region is paired with another region within the same geography
- At least 300 miles of separation
- If one region goes down, services automatically failover to the paired region

```
Region Pair Examples:
East US        ↔  West US
North Europe   ↔  West Europe
Southeast Asia ↔  East Asia
Brazil South   ↔  South Central US
```

### Exam Tip
```
AZ-900 question: "What is the minimum number of availability zones
in an Azure region that supports them?"
Answer: 3

"Why are Azure regions paired?"
Answer: To provide disaster recovery and data residency within
the same geography
```

---

## 1.11 Azure Resource Hierarchy

```
Management Groups (top level - organize subscriptions)
└── Subscriptions (billing boundary)
    └── Resource Groups (logical container)
        └── Resources (VMs, databases, storage, etc.)
```

### What is a Subscription?

A Subscription is the **billing boundary** in Azure. Every resource you create lives inside a subscription, and all costs are billed to that subscription.

```
Think of it like a mobile phone plan:
- Your phone plan (Subscription) has a billing account (credit card)
- Everything you use (calls, data, SMS) is charged to that plan
- You can have multiple phone plans (multiple Subscriptions)
  for different purposes

Azure Subscription:
- Has a unique Subscription ID
- Linked to one billing account (credit card or enterprise agreement)
- Has spending limits and budgets
- All resources inside it generate costs on its bill
- You can have multiple subscriptions to separate billing:
  → Subscription 1: "Production" (billed to company)
  → Subscription 2: "Development" (billed to dev budget)
  → Subscription 3: "Personal Learning" (billed to your card)
```

### What is a Resource Group?

A Resource Group is a **logical container** that holds related Azure resources for a project, application, or environment. Think of it as a folder for your Azure resources.

```
Real-World Example — E-Commerce Project:

Resource Group: rg-ecommerce-prod
├── VM: vm-web-server        ($140/month)  ← Billable
├── SQL Database: db-orders  ($30/month)   ← Billable
├── Storage Account: stfiles ($5/month)    ← Billable
├── Load Balancer: lb-web    ($18/month)   ← Billable
├── Public IP: pip-web       ($4/month)    ← Billable
└── VNet: vnet-ecommerce     ($0/month)    ← Free (VNets are free)

Total monthly cost for this Resource Group: ~$197/month

⚠️ IMPORTANT: Every resource deployed inside a Resource Group
   is potentially billable. When you create a VM, storage account,
   or database — Azure starts charging you for it.

⚠️ To stop charges: Either DELETE the resource or DEALLOCATE it
   (for VMs). Simply "stopping" a VM from inside the OS does NOT
   stop billing — you must deallocate from Azure Portal.
```

### How Projects Map to Resource Groups

```
Best Practice: ONE Resource Group per project/environment

Project: "Company Website"
├── rg-website-dev        (Development environment)
│   ├── VM (B1s - cheap)
│   ├── SQL Database (Basic - $5/month)
│   └── Storage Account
│
├── rg-website-staging    (Staging/Testing environment)
│   ├── VM (B2s - medium)
│   ├── SQL Database (Standard S0)
│   └── Storage Account
│
└── rg-website-prod       (Production environment)
    ├── VM Scale Set (D2s_v5 - powerful)
    ├── SQL Database (Standard S3)
    ├── Storage Account (GRS)
    └── Load Balancer

Why separate Resource Groups per environment?
→ You can see costs per environment separately
→ You can delete the entire dev environment in one click
→ You can apply different access controls (devs can access dev, not prod)
→ You can apply different policies per environment
```

### Advantages of Resource Groups

```
┌─────────────────────────────────────────────────────────────┐
│              ADVANTAGES OF RESOURCE GROUPS                   │
├─────────────────────┬───────────────────────────────────────┤
│ ADVANTAGE           │ EXPLANATION                           │
├─────────────────────┼───────────────────────────────────────┤
│ Organized Billing   │ See costs per project/environment.    │
│                     │ Filter Cost Management by RG to see   │
│                     │ exactly how much each project costs.  │
├─────────────────────┼───────────────────────────────────────┤
│ Lifecycle Mgmt      │ Delete a Resource Group = delete ALL  │
│                     │ resources inside it. Perfect for      │
│                     │ cleaning up demo/test environments.   │
├─────────────────────┼───────────────────────────────────────┤
│ Access Control      │ Apply RBAC at the RG level. Give      │
│ (RBAC)              │ developers access to dev RG only,     │
│                     │ not production RG.                    │
├─────────────────────┼───────────────────────────────────────┤
│ Policy Enforcement  │ Apply Azure Policies per RG.          │
│                     │ Example: "No GPU VMs in dev RG"       │
├─────────────────────┼───────────────────────────────────────┤
│ Tagging             │ Tag the RG and all resources inherit  │
│                     │ context. Tag: Project=Website,        │
│                     │ Environment=Prod, Owner=TeamA         │
├─────────────────────┼───────────────────────────────────────┤
│ Deployment          │ Deploy ARM/Bicep templates to a       │
│                     │ specific RG. Redeploy entire          │
│                     │ infrastructure in one command.        │
├─────────────────────┼───────────────────────────────────────┤
│ Resource Grouping   │ See all related resources in one      │
│                     │ place. No hunting across the portal.  │
├─────────────────────┼───────────────────────────────────────┤
│ Cost Tracking       │ In Cost Management → Cost Analysis,   │
│                     │ group by "Resource Group" to see      │
│                     │ spending per project instantly.       │
└─────────────────────┴───────────────────────────────────────┘
```

### Resource Hierarchy — Full Enterprise Example

```
Root Management Group
├── Production Management Group
│   ├── Subscription: Prod-Finance (Budget: $50,000/month)
│   │   ├── RG: rg-finance-web (Web servers, Load Balancer)
│   │   ├── RG: rg-finance-db (SQL Database, Cosmos DB)
│   │   └── RG: rg-finance-storage (Blob Storage, File Shares)
│   └── Subscription: Prod-HR (Budget: $20,000/month)
│       ├── RG: rg-hr-app
│       └── RG: rg-hr-data
├── Development Management Group
│   └── Subscription: Dev-All (Budget: $5,000/month)
│       ├── RG: rg-dev-team1
│       └── RG: rg-dev-team2
└── Testing Management Group
    └── Subscription: Test-All (Budget: $3,000/month)
        └── RG: rg-test-staging
```

### Resource Groups - Key Rules
1. Every resource MUST belong to exactly ONE resource group
2. A resource group can contain resources from different regions
3. Resource groups CANNOT be nested
4. Deleting a resource group deletes ALL resources inside it
5. Resources can be moved between resource groups
6. Resource groups are a scope for applying access control (RBAC)
7. The resource group itself is FREE — you only pay for resources inside it

### Exam Tip
```
AZ-900 question: "Can a resource belong to multiple resource groups?"
Answer: No. A resource can only be in one resource group at a time.

"Can a resource group contain resources from multiple regions?"
Answer: Yes. The resource group has a location (for metadata), but
resources inside can be in any region.

"What happens to billing when you delete a resource group?"
Answer: All resources inside are deleted, and billing stops for
those resources immediately.
```

---

## 1.12 Azure Services Overview

### Core Azure Services Map

```
┌─────────────────────────────────────────────────────────────┐
│                    AZURE SERVICES                           │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   COMPUTE    │  NETWORKING  │   STORAGE    │  DATABASES    │
│              │              │              │               │
│ • VMs        │ • VNet       │ • Blob       │ • SQL DB      │
│ • App Service│ • Load       │ • File       │ • Cosmos DB   │
│ • Functions  │   Balancer   │ • Queue      │ • MySQL       │
│ • AKS        │ • VPN Gateway│ • Table      │ • PostgreSQL  │
│ • Container  │ • App Gateway│ • Disk       │ • Redis Cache │
│   Instances  │ • CDN        │              │               │
│ • VMSS       │ • DNS        │              │               │
├──────────────┼──────────────┼──────────────┼───────────────┤
│   IDENTITY   │  SECURITY    │  MONITORING  │  DEVOPS       │
│              │              │              │               │
│ • Entra ID   │ • Key Vault  │ • Monitor    │ • DevOps      │
│ • B2C        │ • DDoS       │ • Log        │ • Repos       │
│ • MFA        │   Protection │   Analytics  │ • Pipelines   │
│ • RBAC       │ • Firewall   │ • App        │ • Artifacts   │
│ • PIM        │ • Sentinel   │   Insights   │ • Boards      │
│              │ • Defender   │ • Alerts     │ • Test Plans  │
├──────────────┼──────────────┼──────────────┼───────────────┤
│     AI       │    IoT       │ INTEGRATION  │  MANAGEMENT   │
│              │              │              │               │
│ • OpenAI     │ • IoT Hub    │ • Logic Apps │ • Policy      │
│ • Cognitive  │ • IoT Central│ • Service Bus│ • Blueprints  │
│   Services   │ • Sphere     │ • Event Grid │ • Advisor     │
│ • ML Studio  │ • Digital    │ • API Mgmt   │ • ARM         │
│ • Bot Service│   Twins      │              │ • Bicep       │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

---

## 1.13 Shared Responsibility Model

```
                    On-Prem    IaaS      PaaS      SaaS
                    ────────   ────────  ────────  ────────
Information/Data    Customer   Customer  Customer  Customer
Devices             Customer   Customer  Customer  Customer
Accounts/Identities Customer   Customer  Customer  Customer
Identity Infra      Customer   Customer  Shared    Provider
Applications        Customer   Customer  Customer  Provider
Network Controls    Customer   Customer  Shared    Provider
Operating System    Customer   Customer  Provider  Provider
Physical Hosts      Customer   Provider  Provider  Provider
Physical Network    Customer   Provider  Provider  Provider
Physical Datacenter Customer   Provider  Provider  Provider

Customer = Your responsibility
Provider = Microsoft's responsibility
Shared   = Both share responsibility
```

### Real-World Example
```
Scenario: A company hosts a web application on Azure App Service (PaaS)

Microsoft is responsible for:
- Physical security of data centers
- Hardware maintenance and replacement
- Operating system patches
- Network infrastructure
- Power and cooling

The company is responsible for:
- Application code security
- User authentication and authorization
- Data encryption
- Compliance with regulations
- Access management
```

---

## 1.14 Azure Service Level Agreements (SLAs)

### What is an SLA?
A formal document that defines the performance standards Microsoft commits to for Azure services.

### Common Azure SLAs

| Service | SLA | Monthly Downtime Allowed |
|---------|-----|------------------------|
| Single VM (Premium SSD) | 99.9% | 43.8 minutes |
| VMs in Availability Set | 99.95% | 21.9 minutes |
| VMs in Availability Zones | 99.99% | 4.38 minutes |
| Azure App Service | 99.95% | 21.9 minutes |
| Azure SQL Database | 99.99% | 4.38 minutes |
| Azure Cosmos DB | 99.999% | 26.3 seconds |
| Azure Storage (RA-GRS) | 99.99% | 4.38 minutes |

### Calculating Composite SLAs
```
Scenario: Web App (99.95%) → SQL Database (99.99%)

Composite SLA = 99.95% × 99.99% = 99.94%

This means: Up to 26.3 minutes of downtime per month

To improve: Add redundancy
Web App (99.95%) with Queue (99.9%) fallback:
= 1 - (1 - 0.9995) × (1 - 0.999)
= 1 - 0.0005 × 0.001
= 1 - 0.0000005
= 99.99995%
```

### Exam Tip
```
AZ-900 question: "How do you increase the SLA of a solution?"
Answer: Add redundancy (availability zones, multiple regions,
failover mechanisms)

"What happens if Microsoft fails to meet the SLA?"
Answer: You receive service credits (financial compensation),
NOT a refund. You must file a claim.
```

---

## 1.15 Practice Questions

### Question 1
**Which cloud model provides the most control over hardware?**
- A) SaaS
- B) PaaS
- C) IaaS ✅
- D) Public Cloud

**Explanation**: IaaS gives you the most control. You manage the OS, middleware, runtime, data, and applications. The provider only manages the physical infrastructure.

### Question 2
**A company wants to minimize upfront costs and pay only for what they use. Which expenditure model describes this?**
- A) CapEx
- B) OpEx ✅
- C) Fixed Cost
- D) Reserved Cost

**Explanation**: OpEx (Operational Expenditure) is the pay-as-you-go model where you pay for services as you consume them, with no upfront costs.

### Question 3
**What is the minimum number of Availability Zones in a supported Azure region?**
- A) 1
- B) 2
- C) 3 ✅
- D) 5

**Explanation**: Azure requires a minimum of 3 availability zones in regions that support them, ensuring redundancy.

### Question 4
**Which of the following is true about Resource Groups?**
- A) A resource can belong to multiple resource groups
- B) Resource groups can be nested inside other resource groups
- C) Deleting a resource group deletes all resources within it ✅
- D) Resources in a resource group must be in the same region

**Explanation**: When you delete a resource group, all resources inside it are also deleted. Resources can be in different regions, and a resource can only belong to one resource group.

### Question 5
**A company deploys VMs across three Availability Zones. What SLA can they expect?**
- A) 99.9%
- B) 99.95%
- C) 99.99% ✅
- D) 99.999%

**Explanation**: VMs deployed across Availability Zones have a 99.99% SLA, which is the highest SLA for Azure VMs.

---

## 1.16 Common Errors & Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "No registered resource provider found" | Resource provider not registered for subscription | Register the provider: `az provider register --namespace Microsoft.Compute` |
| "The subscription is not registered to use namespace" | Service not enabled | Go to Subscription → Resource Providers → Register |
| "Location is not available for resource type" | Service not available in chosen region | Check service availability by region at azure.microsoft.com/regions/services |
| "Subscription not found" | Wrong subscription selected | Use `az account set --subscription "correct-name"` |
| "AuthorizationFailed" | Insufficient permissions | Contact subscription admin for proper RBAC role assignment |

---

[Next Module: Azure Account, Portal, CLI & PowerShell →](./Module-02-Azure-Account-Portal-CLI-PowerShell.md)
