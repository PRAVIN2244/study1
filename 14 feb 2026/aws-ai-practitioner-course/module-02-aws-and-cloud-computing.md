# Module 2: Introduction to AWS and Cloud Computing

## 2.1 How Websites Work

Every interaction on the internet follows a client-server model:

```
┌──────────┐                    ┌──────────┐
│  Client  │◄──── Network ────►│  Server  │
│          │                    │          │
│ IP: x.x  │    Request ──►    │ IP: y.y  │
│          │    ◄── Response    │          │
└──────────┘                    └──────────┘
```

- **Client** — Your browser, mobile app, or any device making a request (has an IP address)
- **Server** — A computer that receives requests and sends back responses (has an IP address)
- **Network** — The infrastructure (cables, routers, switches) connecting them

> Think of it like sending postal mail: you write a letter (request), put the recipient's address (server IP), and the postal system (network) delivers it. The recipient sends a reply (response) back to your address (client IP).

---

## 2.2 What is a Server?

A server is a computer with four key components:

| Component | Purpose | Analogy |
|-----------|---------|---------|
| **CPU (Compute)** | Processes instructions and calculations | The "brain" |
| **RAM (Memory)** | Temporary fast-access storage for active tasks | The "desk" you work on |
| **Storage** | Permanent data storage (hard drives, SSDs) | The "filing cabinet" |
| **Database** | Stores data in a structured, queryable way | An organized "spreadsheet" |
| **Network** | Routers, switches, DNS servers for connectivity | The "postal system" |

### Key Networking Terms

| Term | What It Does |
|------|-------------|
| **Network** | Cables, routers, and servers connected to each other |
| **Router** | Forwards data packets between computer networks — knows where to send your data on the internet |
| **Switch** | Receives a packet and sends it to the correct server/client on your local network |

```
Internet ──► [Router] ──► [Switch] ──► Server 1
                                  ──► Server 2
                                  ──► Server 3
```

---

## 2.3 Traditional IT Infrastructure

### The Old Way: On-Premises Data Centers

Before cloud computing, companies built their own data centers:

```
Home/Garage ──► Office ──► Data Center
(startup)      (growing)   (enterprise)
```

### Problems with Traditional IT

| Problem | Impact |
|---------|--------|
| **Data center rent** | Fixed cost regardless of usage |
| **Power, cooling, maintenance** | Ongoing operational expenses |
| **Hardware procurement** | Adding/replacing hardware takes weeks or months |
| **Limited scaling** | Can't quickly add capacity for traffic spikes |
| **24/7 monitoring team** | Need staff around the clock |
| **Disaster recovery** | Earthquakes, power outages, fires can destroy everything |

> **The question:** Can we externalize all of this? **The answer:** Cloud Computing.

---

## 2.4 What is Cloud Computing?

Cloud computing is the **on-demand delivery** of compute power, database storage, applications, and other IT resources through a cloud services platform with **pay-as-you-go** pricing.

**Key characteristics:**
- Provision exactly the right type and size of computing resources you need
- Access as many resources as you need, almost instantly
- Simple way to access servers, storage, databases, and application services
- The cloud provider (e.g., AWS) owns and maintains the hardware; you use what you need via a web interface

### Real-Life Examples You Already Use

| Service | Type | How It's Cloud |
|---------|------|---------------|
| **Gmail** | Email cloud service | Pay only for storage used, no infrastructure to manage |
| **Dropbox** | Cloud storage | Originally built on AWS; stores your files in the cloud |
| **Netflix** | Video streaming | Built entirely on AWS; streams video on demand globally |

---

## 2.5 Cloud Deployment Models

| Model | Description | Best For |
|-------|-------------|----------|
| **Public Cloud** | Resources owned and operated by a third-party provider (AWS, Azure, GCP), delivered over the internet | Most workloads; cost-effective, scalable |
| **Private Cloud** | Cloud services used by a single organization, not exposed to the public | Sensitive data, regulatory compliance, full control |
| **Hybrid Cloud** | Combination of on-premises + public cloud | Gradual migration, sensitive assets on-prem with cloud flexibility |

### Real-Life Use Case

> **Example: Healthcare Hybrid Cloud**
> A hospital keeps patient medical records on a private cloud (for HIPAA compliance) but uses AWS public cloud for its patient-facing appointment booking website. This gives them security for sensitive data and scalability for public-facing services.

---

## 2.6 Five Characteristics of Cloud Computing

| Characteristic | What It Means |
|---------------|--------------|
| **On-demand self-service** | Provision resources without human interaction from the provider |
| **Broad network access** | Resources available over the network from any device |
| **Multi-tenancy & resource pooling** | Multiple customers share the same physical infrastructure securely |
| **Rapid elasticity & scalability** | Automatically acquire/release resources based on demand |
| **Measured service** | Usage is metered; you pay for exactly what you use |

---

## 2.7 Six Advantages of Cloud Computing

1. **Trade CAPEX for OPEX** — No upfront hardware purchases; pay on-demand
2. **Benefit from economies of scale** — AWS's massive scale means lower prices for everyone
3. **Stop guessing capacity** — Scale based on actual measured usage
4. **Increase speed and agility** — Provision resources in minutes, not months
5. **Stop spending money on data centers** — Focus on your business, not infrastructure
6. **Go global in minutes** — Deploy worldwide using AWS's global infrastructure

### Problems Solved by the Cloud

| Problem | Cloud Solution |
|---------|---------------|
| **Flexibility** | Change resource types when needed |
| **Cost-Effectiveness** | Pay as you go, for what you use |
| **Scalability** | Handle larger loads by scaling up or out |
| **Elasticity** | Automatically scale out and scale in |
| **High Availability** | Build across multiple data centers |
| **Agility** | Rapidly develop, test, and launch applications |

---

## 2.8 Types of Cloud Computing

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ On-Premises │    IaaS     │    PaaS     │    SaaS     │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Applications│ Applications│ Applications│ Applications│ ◄── Managed
│ Data        │ Data        │ Data        │ Data        │     by
│ Runtime     │ Runtime     │ Runtime     │ Runtime     │     Others
│ Middleware  │ Middleware  │ Middleware  │ Middleware  │     (SaaS)
│ O/S         │ O/S         │ O/S         │ O/S         │
│ Virtualizn  │ Virtualizn  │ Virtualizn  │ Virtualizn  │
│ Servers     │ Servers     │ Servers     │ Servers     │
│ Storage     │ Storage     │ Storage     │ Storage     │
│ Networking  │ Networking  │ Networking  │ Networking  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ You manage  │ You manage  │ You manage  │ Provider    │
│ EVERYTHING  │ Apps + Data │ Apps + Data │ manages ALL │
│             │ + Runtime   │ only        │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

| Type | What You Manage | AWS Example | Other Examples |
|------|----------------|-------------|----------------|
| **IaaS** (Infrastructure as a Service) | Applications, data, runtime, middleware, OS | Amazon EC2 | Azure VMs, GCP Compute Engine, DigitalOcean |
| **PaaS** (Platform as a Service) | Applications and data only | Elastic Beanstalk | Heroku, Google App Engine |
| **SaaS** (Software as a Service) | Nothing — just use it | AWS Rekognition | Gmail, Dropbox, Zoom |

### Real-Life Use Case

> **Example: Startup Choosing Cloud Type**
> - A startup building a custom ML pipeline needs full control → **IaaS (EC2)**: they install their own OS, libraries, and frameworks
> - A web developer deploying a Node.js app just wants it running → **PaaS (Elastic Beanstalk)**: upload code, platform handles the rest
> - A marketing team needs image recognition → **SaaS (Rekognition)**: call the API, get results, no infrastructure to manage

---

## 2.9 AWS Pricing Overview

AWS follows a **pay-as-you-go** model with three pricing fundamentals:

| What You Pay For | Details |
|-----------------|---------|
| **Compute** | Pay for compute time (per second/hour your servers run) |
| **Storage** | Pay for data stored in the cloud (per GB/month) |
| **Data Transfer OUT** | Pay for data leaving AWS (data IN is free) |

> **Key Exam Point:** Data transfer INTO AWS is always free. You only pay for data going OUT.

---

## 2.10 AWS Global Infrastructure

### Step-by-Step: Explore AWS Infrastructure (via UI)

1. **Open the AWS Infrastructure Map**
   - Go to [https://infrastructure.aws/](https://infrastructure.aws/)
   - You'll see a world map showing all AWS Regions, Availability Zones, and Edge Locations

2. **Understand the Hierarchy**

```
AWS Global Infrastructure
├── Regions (e.g., us-east-1, eu-west-3)
│   ├── Availability Zone a (one or more data centers)
│   ├── Availability Zone b
│   └── Availability Zone c
└── Edge Locations (400+ worldwide)
```

### AWS Regions

- AWS has Regions all around the world
- Named like: `us-east-1` (N. Virginia), `eu-west-3` (Paris), `ap-southeast-2` (Sydney)
- A Region is a **cluster of data centers**
- Most AWS services are **Region-scoped** (data stays in the Region you choose)

#### How to Choose a Region

| Factor | Consideration |
|--------|--------------|
| **Compliance** | Data governance and legal requirements — data never leaves a Region without your permission |
| **Proximity** | Choose a Region close to your customers for lower latency |
| **Available Services** | Not all services are available in every Region |
| **Pricing** | Pricing varies by Region (check the service pricing page) |

### Step-by-Step: Check Region Availability (via Console UI)

1. Go to [https://console.aws.amazon.com](https://console.aws.amazon.com)
2. Click the **Region dropdown** in the top-right corner of the console
3. You'll see a list of all available Regions
4. Select a Region to switch to it
5. To check which services are available in each Region, visit:
   [https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services)

### AWS Availability Zones (AZs)

Each Region has multiple Availability Zones (usually 3, minimum 3, maximum 6):

```
AWS Region: Sydney (ap-southeast-2)
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ ap-southeast-2a │  │ ap-southeast-2b │  │ ap-southeast-2c │
│                 │  │                 │  │                 │
│  Data Center(s) │  │  Data Center(s) │  │  Data Center(s) │
│  - Redundant    │  │  - Redundant    │  │  - Redundant    │
│    power        │  │    power        │  │    power        │
│  - Networking   │  │  - Networking   │  │  - Networking   │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────── High bandwidth, ultra-low ────────┘
                  latency networking
```

**Key points:**
- Each AZ is one or more discrete data centers
- Redundant power, networking, and connectivity
- Physically separate from each other (isolated from disasters)
- Connected with high bandwidth, ultra-low latency networking

### AWS Edge Locations (Points of Presence)

- **400+ Edge Locations** and **10+ Regional Caches** in **90+ cities** across **40+ countries**
- Used by services like **CloudFront** (CDN) to deliver content to end users with lower latency
- Think of them as mini-data-centers close to your users for faster content delivery

---

## 2.11 AWS Console Tour

### Global vs. Regional Services

| Global Services | Regional Services |
|----------------|-------------------|
| IAM (Identity and Access Management) | Amazon EC2 (IaaS) |
| Route 53 (DNS) | Elastic Beanstalk (PaaS) |
| CloudFront (CDN) | Lambda (FaaS) |
| WAF (Web Application Firewall) | Rekognition (SaaS) |

### Step-by-Step: Navigate the AWS Console (via UI)

1. **Sign in** to [https://console.aws.amazon.com](https://console.aws.amazon.com)
2. **Search bar** (top center) — Type any service name to find it quickly
3. **Region selector** (top right) — Switch between Regions
4. **Services menu** (top left "Services" dropdown) — Browse all AWS services by category
5. **Account menu** (top right, your name) — Access billing, security credentials, and account settings

---

## 2.12 Shared Responsibility Model

AWS and the customer share security responsibilities:

```
┌─────────────────────────────────────────────────┐
│              CUSTOMER RESPONSIBILITY             │
│         "Security IN the Cloud"                  │
│                                                  │
│  - Customer data                                 │
│  - Platform, applications, IAM                   │
│  - Operating system, network, firewall config    │
│  - Client-side & server-side encryption          │
│  - Network traffic protection                    │
├─────────────────────────────────────────────────┤
│              AWS RESPONSIBILITY                  │
│         "Security OF the Cloud"                  │
│                                                  │
│  - Hardware / AWS Global Infrastructure          │
│  - Regions, Availability Zones, Edge Locations   │
│  - Compute, Storage, Database, Networking        │
│  - Software (managed services)                   │
└─────────────────────────────────────────────────┘
```

> **Key Exam Point:** AWS is responsible for the security **OF** the cloud (infrastructure). You are responsible for security **IN** the cloud (your data, configurations, access controls).

### Real-Life Use Case

> **Example: S3 Bucket Security**
> AWS ensures the S3 service is available, durable, and the underlying infrastructure is secure (their responsibility). But if you accidentally make an S3 bucket public and expose customer data, that's YOUR responsibility — you configured the access controls.

---

## 2.13 AWS Acceptable Use Policy

AWS has rules about what you can and cannot do on their platform:

- **No illegal, harmful, or offensive use or content**
- **No security violations** (unauthorized access, port scanning without permission)
- **No network abuse** (DDoS attacks, traffic flooding)
- **No email or message abuse** (spam, phishing)

Full policy: [https://aws.amazon.com/aup/](https://aws.amazon.com/aup/)

---

## Module 2 Summary

| Concept | Key Takeaway |
|---------|-------------|
| Client-Server Model | Clients send requests, servers respond, connected via network |
| Traditional IT Problems | Expensive, slow to scale, disaster-prone |
| Cloud Computing | On-demand, pay-as-you-go, scalable IT resources |
| Deployment Models | Public, Private, Hybrid |
| Cloud Types | IaaS (EC2), PaaS (Beanstalk), SaaS (Rekognition) |
| AWS Pricing | Pay for Compute, Storage, Data Transfer OUT |
| AWS Infrastructure | Regions > Availability Zones > Edge Locations |
| Shared Responsibility | AWS = security OF the cloud; You = security IN the cloud |

---

*Previous: [Module 1 — Introduction to AI](module-01-introduction-to-ai.md)*
*Next: [Module 3 — Generative AI and Foundation Models](module-03-generative-ai-and-foundation-models.md)*
