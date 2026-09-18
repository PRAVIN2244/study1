# Complete Course Topic Index

Every concept covered across all 37 modules.

---

# MODULE 1: YAML Syntax

- **1.1 YAML Syntax Primer**
   - What is YAML?
   - YAML Core Concepts
   - Step 1: Comments & Key-Value Pairs
   - Step 2: Dictionary / Map
   - Step 3: Array / Lists
   - Step 4: Multiple Lists (List of Dictionaries)
   - Step 5: YAML Spaces & Indentation Rules
   - Step 6: Document Separator (`---`)
   - YAML Key Rules Summary
   - Kubernetes YAML Top-Level Objects
      - apiVersion
      - kind
      - metadata
      - spec
   - Sample Pod Template with YAML Type Annotations
   - Line-by-Line Pod Example
   - Common YAML Patterns in Kubernetes
      - Environment Variables
      - Container Ports
      - Resource Requests and Limits
      - Labels
      - nodeSelector
   - Validating YAML Before Applying
   - Common YAML Errors
   - Internal Flow When Applying YAML
   - Production YAML Best Practices

---

# MODULE 2: Docker & Container Fundamentals

- **2.1 Docker & Container Basics (Prerequisites)**
   - Building a Docker Image
   - Commands, Arguments, and ENTRYPOINT
   - Docker Service Configuration
      - Managing the Docker Service
      - Running the Docker Daemon in the Foreground
      - Docker Daemon Communication
      - Remote Access via TCP
      - Configuration File: /etc/docker/daemon.json
- **2.2 Docker Storage Fundamentals**
   - Docker File System
   - Image Layers and Caching
   - Container Writable Layer and Copy-on-Write
   - Docker Volumes and Bind Mounts
   - Storage Drivers vs Volume Drivers
- **2.3 Docker vs ContainerD**
   - The Evolution of Container Runtimes
   - Docker's Internal Architecture
   - Why Docker Was Deprecated (Kubernetes v1.24)
      - A Note on Docker's Continued Relevance
   - ContainerD as a Standalone Runtime
   - CLI Tools Comparison
      - ctr — ContainerD Debugging Tool
      - nerdctl — Docker-like CLI for ContainerD
      - crictl — Kubernetes CRI Debugging Tool
   - Docker CLI vs crictl Command Mapping
   - Kubernetes Runtime Endpoint Configuration
   - Summary Table

---

# MODULE 3: What is Kubernetes?

- **3.1 What is Kubernetes?**
   - Real-Life Analogy
   - Monolithic vs Microservices Architecture
   - Why Kubernetes?
   - Core Functions of Kubernetes
   - Kubernetes Versioning
   - Industry Example: Spotify

---

# MODULE 4: Kubernetes Architecture

- **4.1 Kubernetes Architecture**
   - Quick Reference: Component Summary
   - Architecture Summary Table
   - Control Plane Components
      - 1. API Server (`kube-apiserver`)
      - 2. etcd
      - 3. Scheduler (`kube-scheduler`)
      - 4. Controller Manager (`kube-controller-manager`)
      - 5. Cloud Controller Manager (`cloud-controller-manager`)
      - 6. CoreDNS
   - Worker Node Components
      - 1. kubelet
      - 2. kube-proxy
      - 3. Container Runtime
   - End-to-End Flow: What Happens When You Apply a Deployment
   - Verifying Cluster Health
   - Architecture Interview Questions
   - kube-system Namespace — What's Running Inside
      - Component Deep Dive
      - Inspecting System Components — describe & logs

---

# MODULE 5: Kubernetes Objects & YAML Manifests

- **5.1 Kubernetes Objects — The Building Blocks**
   - Core Objects Overview
   - Object Specification Pattern
   - Kubernetes Objects — Detailed Reference
      - 1. Workload Resources (Manage Applications)
      - 2. Service Resources (Networking & Communication)
      - 3. Storage Resources
      - 4. Config & Security Resources
      - 5. Policy & Security Resources
      - Kubernetes Objects Summary Table

---

# MODULE 6: Setting Up a Kubernetes Cluster

- **6.1 Local Kubernetes Setup with Minikube**
   - What is Minikube?
   - Step 1 — Install Docker
   - Step 2 — Install kubectl
   - Step 3 — Install Minikube
   - Step 4 — Install conntrack
   - Step 5 — Start Minikube
   - Step 6 — Verify the Cluster
   - Step 7 — Verify System Components
   - Understanding kubeconfig
   - Common Errors
   - Quick Verification Test
- **6.2 Local Multi-Node Cluster with Kind**
- **6.3 Production Cluster Setup with kubeadm**
   - Prerequisites
   - Step 1 — Install Container Runtime (All Nodes)
   - Step 2 — Install kubeadm, kubelet, kubectl (All Nodes)
   - Step 3 — Initialize Control Plane (Master Node Only)
   - Step 4 — Install CNI Plugin (Master Node)
   - Step 5 — Join Worker Nodes
   - Common kubeadm Errors
   - kubeadm vs Minikube vs Kind vs EKS
   - Designing a Kubernetes Cluster

---

# MODULE 7: kubectl — The Kubernetes CLI

- **7.1 kubectl — The Kubernetes CLI**
   - Installation
   - kubectl Command Structure
   - Essential kubectl Commands with Examples
      - Cluster Information
      - Working with Resources
      - Creating Resources
      - Additional Imperative Commands
      - Debugging & Inspection
      - Modifying & Deleting Resources
      - Labels and Selectors
      - Rollout Commands
      - kubectl explain — API Documentation
      - kubectl config — Context Management
      - kubectl top — Resource Usage (Requires Metrics Server)
      - kubectl auth — Permission Checks
      - API Resources and Events
      - REST API — How kubectl Talks to the API Server
   - kubectl create vs kubectl apply
   - How kubectl apply Works Internally
      - The last-applied-configuration Annotation
      - Step-by-Step Example: How the Three-Way Merge Works
      - How Removed Fields Are Handled
      - ⚠️ Warning: Don't Mix Imperative and Declarative
   - Common kubectl Errors
   - kubectl Command Summary

---

# MODULE 8: Namespaces

- **8.1 Namespaces**
   - Industry Example: Namespace Strategy at a Fintech Company
   - Namespaces — Imperative using kubectl
   - Namespaces — Declarative using YAML with LimitRange
   - Namespaces — Declarative using YAML with ResourceQuota
   - Real-World Namespace Example — Multi-File Application

---

# MODULE 9: Amazon EKS Setup

- **9.1 What is Amazon EKS?**
   - EKS vs Self-Managed Kubernetes
   - Node Types on EKS
- **9.2 Prerequisites Setup**
   - Install AWS CLI
      - Mac
      - Linux
      - Windows
      - Configure AWS Credentials
   - Install kubectl
      - Mac
      - Linux
      - Windows
   - Install eksctl
      - Mac (Homebrew)
      - Linux
      - Windows
   - Install Helm (Package Manager for K8s)
- **9.3 Creating an EKS Cluster**
   - Method 1: Using eksctl (Recommended for Learning)
   - Step-by-Step: Create EKS Cluster Without Node Group
   - Deleting EKS Cluster and Node Groups
   - Method 2: Using eksctl with Config File (Production)
   - Method 3: Using Terraform (Infrastructure as Code)
- **9.4 Connecting to Your EKS Cluster**
- **9.5 Understanding EKS Networking (VPC-CNI)**
- **9.6 EKS Add-ons**
- **9.7 IAM Integration with EKS**
   - IAM Roles for Service Accounts (IRSA)
   - How IRSA Works Internally
   - Accessing AWS Services from Kubernetes — Common Patterns
   - Service-to-Service Communication Using IAM Roles
- **9.8 Managing the Cluster**
   - Scaling Node Groups
   - Upgrading EKS
   - Deleting the Cluster
- **9.9 Cost Optimization Tips**
- **9.10 Common Errors & Troubleshooting**
   - Error: "Unable to connect to the server"
   - Error: "error: You must be logged in to the server (Unauthorized)"
   - Error: "No space left on device" on nodes
   - Error: "0/3 nodes are available: 3 Insufficient cpu"
- **9.11 EKS Deployment Using Terraform**
   - Why Terraform over eksctl?
   - Terraform EKS Configuration
   - Deploying with Terraform
   - Terraform vs eksctl Workflow
- **9.12 Module 2 Exercises**
   - Exercise 1: Create Your First EKS Cluster
   - Exercise 2: Explore the Cluster
   - Exercise 3: Clean Up (Save Money!)

---

# MODULE 10: Pods — The Smallest Deployable Unit

- **10.1 Pods — The Smallest Unit**
   - Single-Container Pod
   - Pod with Environment Variables
   - Pod with Port Exposure
   - Pod Labels and Selectors
   - Node Selectors
   - Multi-Container Pods
   - Sidecar Containers
   - Multi-Container Design Patterns
   - Container Lifecycle Hooks
   - Pod Lifecycle
   - Understanding Container Image Names
   - Init Containers
      - Init Containers — Key Rules
      - The `nc -z` Command (netcat)
      - Deploy and Test Init Containers
      - Lab: Init Containers Troubleshooting
   - Pulling Images from a Private Container Registry
   - Lab: Securing Images with a Private Registry
   - Pod Examples Walkthrough (pod1 → pod6)
      - Pod 1 — Basic Pod with Infinite Loop
      - Pod 2 — Environment Variables
      - Pod 3 — Multi-Container Pod
      - Pod 4 — Labels and Node Selector
      - Pod 5 — Port Exposure
      - Pod 6 — Resource Requests and Limits
   - Pod Examples Summary
   - Resource Requests vs Limits
   - Liveness & Readiness Probes
      - Probe Parameters Explained
      - Real-World Probe Example — Liveness (exec) + Readiness (httpGet)
      - How Kubernetes Self-Healing Actually Works (step-by-step flow)
      - Probe Best Practices
      - Common Probe Issues

---

# MODULE 11: ReplicaSets & Deployments

- **11.1 ReplicaSets — Ensuring Pod Count**
   - ReplicationController vs ReplicaSet
   - ReplicaSet Quick Reference
   - ReplicaSet Troubleshooting — Common Errors
      - Error 1: Wrong API version
      - Error 2: Selector does not match template labels
      - Error 3: Pods stuck in ImagePullBackOff (wrong image)
   - ReplicaSet Detailed Walkthrough
   - ReplicaSet with YAML — Declarative Example
- **11.2 Deployments — The Standard Workload**
   - Creating a Deployment
   - Rolling Updates
   - Rollbacks
   - Deployment Strategies
      - 1. RollingUpdate (Default)
      - 2. Recreate (All at once — causes downtime)
   - Scaling
   - Imperative Deployment Walkthrough (kubectl create deployment)
   - Updating a Deployment
      - Method 1: `kubectl set image` (change container image)
      - Method 2: `kubectl edit deployment` (edit YAML directly)
   - Rolling Back a Deployment
      - Rollback to Previous Version
      - Rollback to a Specific Revision
      - Rolling Restart (recreate all pods without changing the image)
   - Pausing and Resuming a Deployment
   - Revision History Limit (Clean Up Old ReplicaSets)
   - Canary Deployments
   - Deployment with YAML — Complete Example
   - Deployment Troubleshooting — Common Errors
      - Error 1: Case-sensitive `kind` field
      - Error 2: Deployment pods stuck in ImagePullBackOff
      - Quick CLI: Create a Deployment with replicas
   - Clean Up Imperative Deployment
   - Deployment Pitfalls & Best Practices
   - Argo Rollouts — Progressive Delivery
      - Canary Rollout (step-based traffic shifting)
      - Blue-Green Rollout (active/preview services)
      - Automated Analysis (AnalysisTemplate with Prometheus)

---

# MODULE 12: DaemonSets, StatefulSets, Jobs & CronJobs

- **12.1 Other Workload Types**
   - Workload Type Comparison
   - DaemonSet — One Pod Per Node
   - StatefulSet — For Stateful Applications
   - StatefulSet Considerations — What to Think About
   - Job — Run to Completion
   - CronJob — Scheduled Jobs
   - Static Pods
- **12.2 Industry Example: E-Commerce Microservices**
- **12.3 Module 3 Exercises**
   - Exercise 1: Pod Lifecycle
   - Exercise 2: Deployment Rolling Update
   - Exercise 3: Create a CronJob

---

# MODULE 13: Services & Service Discovery

- **13.1 Why Services?**
   - Inter-Pod Communication
- **13.2 Service Types**
   - ClusterIP (Default) — Internal Only
   - NodePort — External via Node IP
   - NodePort Cross-Node Routing — Pod on Node 2, Access via Node 1
   - LoadBalancer — AWS ELB Integration
   - ExternalName — DNS Alias
   - Service Types Comparison
   - The Default Kubernetes Service
   - Imperative Service Creation Commands
   - ClusterIP + NodePort Architecture — Frontend/Backend Walkthrough
      - Imperative Setup
      - Nginx Reverse Proxy Configuration
      - Declarative Setup (YAML Manifests)
   - How to Provide a Static IP Address to a Pod
- **13.3 Service Discovery & DNS**
   - Headless Service (for StatefulSets)
   - Cross-Namespace Service Access — Complete Walkthrough
   - CoreDNS Architecture
   - DNS Name Hierarchy
   - Pod DNS Records
   - Networking Debugging Checklist (problem → command → fix table)

---

# MODULE 14: Ingress & Gateway API

- **14.1 Ingress — HTTP/HTTPS Routing**
   - Install AWS Load Balancer Controller
   - Basic Ingress
   - Ingress with TLS
   - Nginx Ingress Controller (Alternative to ALB)
   - How an Ingress Controller Works Internally
   - Creating Ingress Resources Imperatively
   - Ingress Namespace Rules
   - Troubleshooting: rewrite-target Annotation
   - Default Backend for Unmatched Traffic
   - Troubleshooting: HTTP 308 Redirect Loop
   - Exposing the Ingress Controller
- **14.2 Gateway API — Next-Generation Ingress**
   - Why Gateway API?
   - Three-Object Model
   - GatewayClass
   - Gateway
   - HTTPRoute
   - TLS Termination
   - Traffic Splitting (Canary Deployments)
   - CORS via Filters
   - Gateway API vs Ingress
   - Route Types

---

# MODULE 15: Network Policies & Networking Deep Dive

- **15.1 Network Policies — Firewall Rules**
   - Understanding Ingress and Egress
   - Restrict a Service So Other Namespaces Can't Use It
   - Pod-to-Pod Restriction
   - Service-to-Service Restriction (Cross-Namespace)
   - Egress Restriction (Outbound Traffic)
   - Selector Logic: AND vs OR
   - ipBlock — Allow Traffic from External IPs
   - Real-World Example: Securing a Database Pod
   - Default Deny All (Zero Trust)
   - Industry Example: PCI-DSS Compliant Network
   - Lab: Network Policies — Inspecting and Creating
   - Hands-On: Network Policies with Calico
   - CNI (Container Network Interface) — Deep Comparison
      - CNI Plugin and Configuration Directories
      - CNI Bridge Configuration
      - Weave CNI Plugin
- **15.2 Endpoints & EndpointSlices**
- **15.3 Quick Service Reference**
- **15.4 Complete Networking Example**
- **15.5 Common Errors & Troubleshooting**
   - Error: Service has no endpoints
   - Error: Connection refused
   - Error: Pods stuck in ContainerCreating (CNI not installed)
   - Error: ALB not creating
- **15.6 Module 4 Exercises**
   - Exercise 1: Service Types
   - Exercise 2: DNS Resolution
- **15.7 Appendix: Kubernetes Networking Deep Dive**
   - Cluster Networking Prerequisites
   - Prerequisite — Switching, Routing, and Gateways
      - Switching — Hosts on the Same Network
      - Routing — Communication Between Networks
      - Default Gateway
      - Using a Linux Host as a Router
      - Key Linux Networking Commands
   - Prerequisite — Network Namespaces
      - Creating and Inspecting Namespaces
      - Connecting Two Namespaces with a veth Pair
      - Connecting Multiple Namespaces with a Bridge
      - Host-to-Namespace Communication
      - External Connectivity from Namespaces
      - Inbound Access to Namespaces
   - Prerequisite — Docker Networking
      - Docker Networking Modes
      - The docker0 Bridge
      - How Docker Connects Containers to the Bridge
      - Docker Port Mapping
   - How Pod Networking Works
      - Network Namespaces and veth Pairs
      - Same-Node Pod-to-Pod Communication
      - Cross-Node Pod-to-Pod Communication
      - NAT for External Traffic
   - CNI (Container Network Interface)
      - Why CNI Exists — The Bridge Program Pattern
      - The CNI Specification
      - CNI vs CNM (Docker's Container Network Model)
      - How Kubelet Invokes CNI
      - Kubelet CNI Configuration
      - CNI Plugin Comparison
      - Cluster Network Planning
   - Service Networking Internals
      - kube-proxy Deployment
      - kube-proxy Modes
      - How iptables Rules Work for Services
      - Verifying kube-proxy
   - Network Debugging
      - Identifying Your CNI Plugin
      - Inspecting Pod Networking on a Specific Node
      - Verifying CNI Plugin from Logs
   - Accessing Applications Running in Kubernetes
   - kubectl port-forward — Deep Dive

---

# MODULE 16: ConfigMaps, Secrets & Environment Variables

- **16.1 Environment Variables & ConfigMaps**
   - Setting Environment Variables in Pods
   - ConfigMaps — Centralizing Configuration
   - Creating ConfigMaps
   - Using ConfigMaps in Pods
   - Lab: Environment Variables and ConfigMaps
- **16.2 Secrets — Sensitive Data**
   - Creating Secrets
   - Using Secrets in Pods
   - Step-by-Step: Creating and Using a Secret for MySQL
   - Secret Types
   - Encrypting Secrets at Rest in etcd
   - AWS Secrets Manager Integration
   - Updating a Secret (Password Rotation)
   - Sealed Secrets — Encrypted Secrets for GitOps
   - Get Secrets at Runtime from HashiCorp Vault
   - External Secrets Operator (ESO) — Sync External Secrets to Kubernetes
      - SecretStore CRD (AWS, Vault, GCP providers)
      - ExternalSecret CRD (sync definition)
      - ESO vs Vault Agent Sidecar comparison
   - Lab: Working with Kubernetes Secrets
   - Real-World Secrets Example — MySQL + User Management Microservice

---

# MODULE 17: Storage — Volumes, PV/PVC & StorageClass

- **17.1 Storage in Kubernetes**
- **17.2 Volume Types**
   - Volume Sharing — Two Meanings (Common Interview Confusion)
   - emptyDir — Temporary Shared Storage
   - hostPath — Node's Filesystem
   - Example: Persisting Data with hostPath
   - Docker Volumes vs Kubernetes Volumes
   - Volume Storage Options
- **17.3 Persistent Volumes (PV) & Persistent Volume Claims (PVC)**
   - AWS EBS Storage Classes
   - Creating a PersistentVolumeClaim
   - Using PVC in a Pod
   - Static PersistentVolume (Manual Provisioning)
   - Access Modes
   - Volume Expansion
   - Lab: Persistent Volumes and Persistent Volume Claims
- **17.4 Amazon EFS (Elastic File System) — Shared Storage**
- **17.5 Container Storage Interface (CSI) — Deep Dive**
   - The Three Kubernetes Interfaces: CRI, CNI, CSI
   - What Problem Does CSI Solve?
   - CSI Architecture — How It Works Internally
   - What Happens When a PVC Is Created (CSI Flow)
   - Installing the AWS EBS CSI Driver
   - Alternative: Manual IAM Policy for EBS CSI Driver
   - CSI Driver Comparison
   - Secrets Store CSI Driver — Mount Secrets as Files
   - Azure Disk CSI Example (AKS)
   - CSI Volume Snapshots
   - CSI Real-Life Use Cases
   - Common CSI Errors
- **17.6 StorageClass & Dynamic Provisioning — Deep Dive**
   - Static vs Dynamic Provisioning
   - StorageClass YAML — Line by Line
   - Dynamic Provisioning in Action
   - Expanding a PVC (Volume Resize)
   - StorageClass Comparison for AWS
   - Default StorageClass
   - Tiered Storage Classes
   - No-Provisioner StorageClass (Local Storage)
   - Lab: Storage Classes
   - MySQL with AWS EBS — Complete Walkthrough
      - File 1: StorageClass
      - File 2: PersistentVolumeClaim
      - File 3: ConfigMap (Database Init Script)
      - File 4: MySQL Deployment
      - File 5: MySQL Headless Service
      - Deploy Everything and Verify
      - Connect to MySQL and Verify
      - Summary Table
      - File 6: User Management Microservice Deployment
      - File 7: User Management NodePort Service
      - Deploy and Test the Full Application
      - Test API Endpoints
      - Verify Users in MySQL Database
      - Clean Up
      - Complete Application Summary
- **17.7 Industry Example: WordPress on EKS with Persistent Storage**
- **17.8 Common Errors & Troubleshooting**
   - Error: PVC stuck in Pending
   - Error: Pod stuck in ContainerCreating (volume issue)
   - Error: Secret not found
- **17.9 Module 5 Exercises**
   - Exercise 1: ConfigMap and Secret
   - Exercise 2: Persistent Volume

---

# MODULE 18: Resource Management — Requests, Limits & Quotas

- **18.1 Resource Requests, Limits & Quotas**
   - Container-Level Requests & Limits
   - QoS Classes (Quality of Service)
   - Resource Quotas (Namespace-level limits)
   - LimitRange (Default limits for pods)

---

# MODULE 19: Scheduling — Taints, Affinity & Priority

- **19.1 Node Scheduling**
   - Manual Scheduling (nodeName)
   - Taints and Tolerations
   - Node Selectors
   - Node Affinity (Advanced Scheduling)
   - Taints and Tolerations vs Node Affinity
   - Pod Affinity & Anti-Affinity
   - Topology Spread Constraints
   - Scheduler Internals: Phases & Plugins
   - Multiple Schedulers (Deploying a Custom Scheduler)
      - Deploying a Custom Scheduler as a Pod
      - Deploying a Custom Scheduler as a Deployment (Production)
      - Using a Custom Scheduler in a Pod
      - Verifying Which Scheduler Was Used
      - Lab: Deploying a Custom Scheduler Step-by-Step
   - Scheduler Profiles (Recommended over Multiple Binaries)
      - KubeSchedulerConfiguration
      - Customizing Plugins Per Profile
      - Running the Scheduler with a Custom Config
- **19.2 Pod Priority, Preemption & Disruption Budgets**
   - Pod Priority & Preemption
   - Pod Disruption Budgets (PDB)

---

# MODULE 20: Auto-Scaling — HPA, VPA, Cluster Autoscaler & Karpenter

- **20.1 Auto-Scaling**
   - Scaling Concepts
   - Autoscaling Levels
   - Horizontal Pod Autoscaler (HPA)
   - Vertical Pod Autoscaler (VPA)
   - In-Place Pod Resource Resizing
   - HPA vs VPA Comparison
   - Cluster Autoscaler (Node-level)
   - Karpenter (AWS-Native Alternative to Cluster Autoscaler)
   - KEDA (Kubernetes Event-Driven Autoscaling)
   - Complete Autoscaling Summary

---

# MODULE 21: Pod Security — SecurityContext & Pod Security Standards

- **21.1 Pod Security**
   - Docker Security Fundamentals
   - Security Context
      - Pod-Level vs Container-Level Override
      - Adding Capabilities at Container Level
      - Lab: Security Contexts
   - Host Access Restrictions (hostPID, hostIPC, hostNetwork, hostPath, privileged)
   - Pod Security Standards (PSS)
   - Runtime Classes & Container Sandboxing
   - Seccomp (Secure Computing)
      - Seccomp Modes
      - Seccomp Profiles (JSON)
      - Docker's Default Seccomp Profile
      - Custom Seccomp Profiles with Docker
      - Seccomp in Kubernetes
   - AppArmor
      - Verifying AppArmor on Nodes
      - Profile Modes
      - Writing AppArmor Profiles
      - Generating Profiles with aa-genprof
      - Managing Profiles
      - AppArmor in Kubernetes

---

# MODULE 22: RBAC — Role-Based Access Control

- **22.1 RBAC — Role-Based Access Control**
   - Authorization Mechanisms
   - RBAC Deep Dive
   - Role & RoleBinding (Namespace-scoped)
   - Lab: Roles & RoleBindings
   - ClusterRole & ClusterRoleBinding (Cluster-wide)
   - Lab: ClusterRoles & ClusterRoleBindings
   - RBAC Imperative Commands (Quick Setup)
   - Service Accounts
   - RBAC Debugging CLI Reference
   - Common RBAC Mistakes
   - RBAC Auditing Tools (rakkess, who-can)

---

# MODULE 23: Authentication, TLS Certificates & KubeConfig

- **23.1 Authentication & Certificates**
   - OIDC Connector in Kubernetes — Authenticate Users via Identity Provider
   - TLS Fundamentals
      - One-Way SSL vs Mutual TLS (mTLS)
   - Creating Kubernetes TLS Certificates with OpenSSL
      - Step 1: Generate the CA Certificate
      - Step 2: Generate Client Certificates
      - Step 3: Generate the API Server Certificate with SANs
      - Step 4: ETCD Peer Certificates (HA Clusters)
   - Inspecting Certificates in an Existing Cluster
      - Identifying Certificate Files
      - Building a Certificate Inventory
      - Troubleshooting with Logs
   - Kubernetes Certificate Infrastructure
      - Inspecting Certificate Details with OpenSSL
      - API Server Certificate Flags
      - ETCD Server Certificate Flags
      - Lab: Troubleshooting Certificate Issues
   - Authenticating a User with Certificates
- **23.2 KubeConfig — Managing Cluster Access**

---

# MODULE 24: Service Accounts, API Groups & EKS IAM

- **24.1 Service Accounts — Deep Dive**
      - Token Evolution (v1.22 → v1.24)
      - Disabling Token Auto-Mounting
      - Service Account API Access in Practice
      - Lab: Service Accounts for a Dashboard Application
- **24.2 API Groups & API Access**
   - kubectl proxy — Accessing the API Without Certificates
- **24.3 EKS IAM Integration with RBAC**
   - Industry Example: Multi-Team RBAC
- **24.4 Common Errors & Troubleshooting**
   - Error: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"
   - Error: "forbidden: exceeded quota"
   - Error: "is forbidden: User cannot create resource"
   - Scenario: Admin Access but Cannot See Worker Nodes
- **24.5 Module 6 Exercises**
   - Exercise 1: Scheduling
   - Exercise 2: HPA
   - Exercise 3: RBAC

---

# MODULE 25: Helm — The Kubernetes Package Manager

- **25.1 Helm — The Kubernetes Package Manager**
   - Helm Concepts
   - Basic Helm Commands
   - Inspecting Releases and Finding Chart Versions
   - Creating Your Own Helm Chart
   - Validating and Testing Charts
   - Helm Diff Plugin
   - Helm --atomic and --wait Flags
   - Helm Best Practices

---

# MODULE 26: CI/CD — GitHub Actions, ArgoCD & Jenkins

- **26.1 CI/CD with Kubernetes on AWS**
   - GitHub Actions Pipeline
   - ArgoCD — GitOps Continuous Delivery
- **26.2 Jenkins on Kubernetes — Dynamic Slave Agents**
   - Architecture
   - Step 1 — Deploy Jenkins Master
   - Step 2 — Create RBAC for Jenkins
   - Step 3 — Configure Kubernetes Plugin in Jenkins
   - Step 4 — Create a Pipeline Using Dynamic Slaves
   - Alternative: Install via Helm
- **26.4 Environment Parity — Why Prod Works but Dev Doesn't**
   - The Problem (Configuration, Dependency, Data Disparity)
   - The Solution: Promote, Don't Rebuild
   - Achieving Parity with Containers
   - Configuration Management via Kubernetes (ConfigMaps per namespace)
   - Infrastructure Parity with Terraform
   - GitOps Enforcement with ArgoCD
   - Validating Parity (automated scripts)
   - Impact Metrics (DORA metrics, deployment success rate)

---

# MODULE 27: Monitoring & Logging — Metrics Server, Prometheus & EFK

- **27.1 Monitoring Cluster Components**
   - What to Monitor
   - From Heapster to Metrics Server
   - How Metrics Are Collected
   - Deploying Metrics Server
   - Viewing Metrics
   - Lab: Metrics Server Walkthrough
- **27.2 Monitoring with Prometheus & Grafana**
   - Install Prometheus Stack
   - Custom Prometheus Metrics
   - Alerting Rules
   - AlertManager Configuration (Slack/PagerDuty)
- **27.3 Managing Application Logs**
   - Logging in Docker
   - Logging in Kubernetes
   - Logging with Multiple Containers
   - Lab: Troubleshooting with Application Logs
- **27.4 Logging with EFK/ELK Stack**
   - Fluent Bit (Lightweight Log Collector)
   - AWS CloudWatch Container Insights
- **27.5 Monitoring Common Mistakes & Troubleshooting**
   - Common Monitoring Mistakes (table)
   - Monitoring Troubleshooting Cheatsheet (symptom → fix)
   - Quick Diagnostic Commands
   - Monitoring Best Practices
- **27.6 Useful Prometheus Queries (PromQL)**
- **27.7 Module 7 Exercises**
   - Exercise 1: Helm
   - Exercise 2: Monitoring
- **27.8 Loki — Lightweight Log Aggregation**
   - EFK vs Loki Comparison
   - Install Loki Stack (Helm)
   - How Promtail Works (DaemonSet architecture)
   - Add Loki as Grafana Data Source
   - LogQL Queries (label filters, regex, JSON parsing, rate queries)
   - When to Use Loki vs EFK
- **27.9 SRE Practices — SLIs, SLOs, and Operational Readiness**
   - SLIs, SLOs, SLAs, Error Budgets
   - The Four Golden Signals (Latency, Traffic, Errors, Saturation)
   - Defining SLOs in Prometheus (PrometheusRule YAML)
   - Error Budget Tracking
   - Runbooks (template, linking to alerts)
   - Incident Response (lifecycle, severity levels, roles)
   - Blameless Postmortems (template with timeline, root cause, action items)
   - Cost Optimization (OpenCost, right-sizing, Spot instances)

---

# MODULE 28: Kubernetes Version Upgrades

- **28.1 Kubernetes Version Upgrades**
   - Understanding Kubernetes Versions
   - Component Version Skew Policy
   - Cluster Maintenance — OS Upgrades
   - Before Upgrading — What to Check
   - Package Repository Migration
   - Upgrading with kubeadm (Self-Managed Clusters)
   - Upgrading EKS
   - Upgrade Best Practices
   - etcd Backup Before Upgrade
   - Lab: Cluster Upgrade with Zero Downtime

---

# MODULE 29: Troubleshooting

- **29.1 Troubleshooting Framework**
   - Essential Debugging Commands
   - Third-Party Debugging Tools (k9s, stern, kubtail, lens)
   - Runbook: My Pod Won't Start (step-by-step decision tree)
   - Application Failure Methodology
   - Common Application Failure Patterns
- **29.2 Pod Errors**
   - CrashLoopBackOff
   - ImagePullBackOff / ErrImagePull
   - Pending Pod
   - CreateContainerConfigError
   - Kubernetes Using Old Image / Updates Not Reflected in Browser
   - Pod Stuck in Terminating
   - Pods Stuck in ContainerCreating
   - Pods Stuck in Init State
   - Exit Code 137 (OOMKilled)
   - Failed to Create Pod Sandbox
   - Liveness & Readiness Probe Failures
- **29.3 Service & Networking Errors**
   - Service Has No Endpoints
   - DNS Resolution Failure
      - CoreDNS Error: SERVFAIL
      - CoreDNS Error: REFUSED
      - CoreDNS Troubleshooting Checklist
   - Troubleshooting kube-proxy
   - Troubleshooting aws-node (EKS VPC CNI)
   - Troubleshooting ebs-csi-controller
   - Inspecting kube-dns Service
   - Connection Refused / Connection Timeout
   - Service External-IP Pending
   - Ingress Returns 404
   - Ingress Returns 502 Bad Gateway
   - Ingress Redirect Loop
- **29.4 Storage Errors**
   - PVC Stuck in Pending
   - Multi-Attach Error
   - PersistentVolume Stuck in Released State
   - Volume Mount Permissions Denied
   - Resource Quota Exceeded
   - Namespace Deletion Stuck
- **29.5 Node Errors**
   - Node NotReady
   - Worker Node Failure — Detailed Troubleshooting
      - Kubelet Stopped
      - Wrong CA File in Kubelet Config
      - Wrong Control Plane Port in kubelet.conf
      - Validating Kubelet Certificates
   - Node Cordon, Drain & Uncordon
   - Node Not Registering with Cluster
   - Real-Life Troubleshooting Scenarios
      - Scenario 1: Application OOMKilled in Production
      - Scenario 2: Pods Stuck in CrashLoopBackOff After Deployment
      - Scenario 3: Node Disk Full — Pods Evicted
      - Scenario 4: Service Returns 503 — No Healthy Backends
   - Scenario: Node min=1 max=5, Pod Not Starting
   - Scenario: Pod CPU=2 & Memory=4Gi Keeps Increasing — Troubleshooting
- **29.6 Control Plane Failures**
   - Troubleshooting Flow
   - Scheduler Failure — Pods Stuck in Pending
   - Controller Manager Failure — Scaling/ReplicaSet Not Working
   - Common Control Plane Manifest Errors
   - Editing Static Pod Manifests
- **29.7 EKS-Specific Errors**
   - Error: "Unauthorized" when running kubectl
   - Error: ALB Ingress Not Creating
   - Error: Pods Can't Pull from ECR
- **29.8 Operational Errors**
   - Helm Release Stuck in PENDING_INSTALL
   - Job Failing to Complete
   - Deployment Not Updating (Image Tag Unchanged)
   - Pod Security Context Misconfiguration
- **29.9 Performance Troubleshooting**
   - High CPU/Memory Usage
   - Slow Pod Startup
- **29.10 Quick Reference: Error → Solution**
- **29.11 Debugging Toolkit**
   - Must-Have Debug Images
   - Useful One-Liners
   - JSONPath Queries with kubectl
- **29.12 Pod Log Storage & Centralized Logging — Deep Dive**
   - Where Are Pod Logs Stored?
   - kubectl logs — How It Works
   - Log Rotation Configuration
   - The Problem: Logs Are Ephemeral
   - Centralized Logging Architecture (EFK Stack)
   - Deploying Fluent Bit as a DaemonSet
   - AWS CloudWatch Logs (EKS Alternative)
   - Application Logs vs stdout
   - Sidecar Pattern for File-Based Logs
   - Log Storage Comparison
- **29.13 Module 9 Exercises**
   - Exercise 1: Debug a Broken Deployment
   - Exercise 2: Debug Networking
   - Exercise 3: Resource Pressure
- **29.14 Congratulations!**
   - Next Steps
- **29.15 Advanced Debug Commands Quick Reference**
   - Cluster Health (API liveness/readiness, leader election, API versions)
   - Node-Level Debugging (conditions, taints, CRI version, debug node)
   - Pod Advanced Debugging (state, QoS, owner, affinity, ephemeral containers)
   - Service & Network Debugging (endpoints, EndpointSlices, in-pod tools)
   - Deployment & Rollout Debugging (diff, dry-run, quarantine, restart)
   - Resource & Scheduling Debugging (requests/limits audit, evictions, image audit)
   - CRI-Level Debugging (crictl, journalctl, iptables)
   - Admission & Webhook Debugging
   - Cluster-Wide Health Snapshot
- **29.16 Additional Production Errors**
   - Context Deadline Exceeded (API timeout, etcd latency)
   - Kubelet Certificate Rotation Failing
   - Pod IP Conflict (CNI CIDR overlap)
   - ConfigMap Too Large (1MB limit, alternatives)
   - Pod Logs Truncated (log rotation, centralized logging)
   - Kube-proxy Failing (Service routing broken)
   - Cluster Autoscaler Scaling Too Slowly (tuning parameters)
   - CoreDNS Pods CrashLooping (loop detection, scaling)
   - API Server High Latency (etcd, Priority and Fairness)
   - PersistentVolume Not Resizing (allowVolumeExpansion)

---

# MODULE 30: Admission Controllers & Webhooks

- **30.1 Admission Controllers & Webhooks**
   - What Are Admission Controllers?
   - Why RBAC Alone Isn't Enough
   - Built-in Admission Controllers
   - Mutating vs Validating — Execution Order
   - Namespace Admission Controllers
   - Viewing Enabled Admission Controllers
   - Enabling and Disabling Admission Controllers
   - How External Admission Webhooks Work
      - AdmissionReview: The Webhook Protocol
      - Writing a Webhook Server
   - Webhook Configuration Objects
   - Deploying a Mutating Webhook — Full Walkthrough
      - Step 1: Create the Namespace
      - Step 2: Create the TLS Secret
      - Step 3: Deploy the Webhook Server and Service
      - Step 4: Configure the MutatingWebhookConfiguration
      - Step 5: Test the Webhook
   - Admission Controllers on Amazon EKS
   - Pod Security Admission (PSA)
   - ValidatingAdmissionPolicy (CEL-based, v1.30+ GA)
   - OPA Gatekeeper & Kyverno (Policy Engines)
   - Admission Controllers Lab Exercises
   - Troubleshooting Admission Controllers
   - Production Best Practices
      - Security
      - Scaling & High Availability
      - Monitoring & Observability
      - Decision Matrix: Which Admission Approach to Use
   - Interview Questions
   - Admission Controllers Quick Reference

---

# MODULE 31: Security Hardening & Network Security

- **31.1 Security Hardening**
   - Security Primitives Overview
   - Cluster Security Checklist
   - Securing Node Metadata
      - What Node Metadata Contains
      - Why This Data Is Sensitive
   - Pod Security Standards
   - Secure Pod Configuration
   - Minimizing Base Image Footprint
   - Image Scanning with Trivy
   - Static Analysis with kubesec
   - Software Bill of Materials (SBOM)
   - Cosign — Container Image Signing and Verification
      - Key-based signing (generate-key-pair, sign, verify)
      - Keyless signing with Sigstore
      - Kyverno policy to enforce signed images
      - CI/CD integration (GitHub Actions)
   - Runtime Syscall Tracing with Tracee
      - Running Tracee as a Docker Container
      - Tracing Modes
   - Docker Daemon Security
      - Host Hardening (Prerequisites)
      - Host Firewall with UFW
      - Exposing the Docker Daemon Remotely
      - Enabling TLS Encryption
      - Certificate-Based Client Authentication
   - Kubelet Security
      - Kubelet API Ports
      - 1. Disable Anonymous Authentication
      - 2. Enable Certificate-Based Authentication
      - 3. Set Authorization Mode to Webhook
      - 4. Disable the Read-Only Port
      - KubeletConfiguration vs Command-Line Flags
      - Kubelet Security Checklist
   - Verifying Platform Binaries
      - Why Verify?
      - Verification Steps
      - Verifying Individual Component Binaries
   - CIS Benchmarks & kube-bench
      - CIS-CAT (Configuration Assessment Tool)
      - What CIS Benchmarks Cover
      - Installing and Running kube-bench
      - Reading kube-bench Output
      - Common CIS Remediation Examples
      - Automating CIS Checks with a CronJob
   - Cluster Penetration Testing with Kube-hunter
   - Kubernetes Dashboard — Deployment & Security
      - Deploying the Dashboard
      - Accessing the Dashboard
      - Dashboard Authentication
      - Dashboard Security Checklist
- **31.2 Kubernetes Network Security — Deep Dive**
   - Network Security Layers
   - 1. Default-Deny NetworkPolicy (Foundation)
   - 2. Allow Only Required Traffic
   - 3. Encryption in Transit
   - 4. AWS Security Groups for Pods (EKS)
   - 5. API Server Access Control
   - Falco — Runtime Threat Detection
      - What Falco Detects (threat table)
      - Install Falco on Kubernetes (Helm)
      - How Falco Works (eBPF architecture diagram)
      - Custom Falco Rules (YAML)
      - Falco vs Other Runtime Security Tools
   - Network Security Checklist

---

# MODULE 32: etcd Operations & Disaster Recovery

- **32.1 etcd Operations & Disaster Recovery**
   - etcd Backup
   - etcd Restore
   - Automated Backup with CronJob
   - Backup Candidates — What to Back Up
   - Three Approaches to Backing Up Resource Configurations
   - Velero — Backup and Restore
   - Stacked vs External etcd Topology
   - Lab: Multi-Cluster etcd Backup and Restore
- **32.2 Backup & Disaster Recovery Strategy**
   - RTO and RPO
   - Backup Strategies (Full, Incremental, Differential, Snapshot)
   - Database Backup as Kubernetes CronJobs
   - Disaster Recovery Testing
   - Chaos Engineering for Kubernetes
   - Backup Security (Encryption, Immutable Backups, Retention)

---

# MODULE 33: Kubernetes API Management — Deep Dive

- **33.1 Kubernetes API Management — Deep Dive**
   - API Groups
   - API Request Flow
   - API Server Security Configuration
   - API Audit Logging
   - API Rate Limiting (Priority and Fairness)
      - Configuring Custom Priority Levels
      - Mapping Requests to Priority Levels with FlowSchemas
      - API Priority vs Pod Priority
   - API Versioning and Compatibility

---

# MODULE 34: Custom Resource Definitions (CRDs) & Operators

- **34.1 Custom Resource Definitions (CRDs) & Operators**
   - How Standard Resources Work
   - What Are CRDs?
   - CRD Structure
   - Creating Custom Resource Instances
   - Another CRD Example: Database
   - Custom Controllers
   - The Operator Pattern
   - Discovering and Installing Operators
   - Popular Operators
   - CRD vs Operator — When to Use What

---

# MODULE 35: Microservices Patterns & Service Mesh (Istio)

- **35.1 Microservices Patterns on Kubernetes**
   - Achieving Unity Between Microservices
      - Service Discovery
      - Communication Patterns
      - Health Checks for Microservices
      - Shared Configuration
      - Inter-Service Network Policies
      - Microservices Deployment Strategy
- **35.2 Service Mesh — Deep Dive (Istio)**
   - Why Use a Service Mesh?
   - Istio Architecture
   - Installing Istio
   - How Sidecar Injection Works
   - mTLS (Mutual TLS) — Encrypted Service-to-Service Communication
   - Traffic Management — Canary Deployments
   - Circuit Breaking — Prevent Cascade Failures
   - Observability — Built-in Metrics and Tracing
   - Service Mesh Comparison
   - Cilium — eBPF-Based Pod-to-Pod Encryption
   - Common Istio Errors
   - Service Mesh Real-Life Use Cases
- **35.3 Module 8 Exercises**
   - Exercise: Deploy the E-Commerce Platform

---

# MODULE 36: Industry Projects

- **Project 1: Production-Grade Microservices E-Commerce Platform**
   - Architecture
   - Step 1: Namespace Setup
   - Step 2: Product Service (Go Microservice)
   - Step 3: Frontend (React App)
   - Step 4: Ingress with Path-Based Routing
   - Step 5: Database (PostgreSQL StatefulSet)
   - Step 6: Network Policies
   - Deployment Commands
- **Project 2: CI/CD Pipeline with Blue-Green Deployment**
   - Architecture
- **Project 3: Multi-Tenant SaaS Platform**
   - Multi-Tenancy Models
   - Isolation Layers
   - Architecture for Tenant Isolation
   - DNS Isolation Between Tenants
   - Storage Isolation with Per-Tenant StorageClasses
- **Project 4: ML Model Serving Platform**
- **Project 5: AI Chatbot — Full DevOps Lifecycle**
   - Application (Python/Flask + OpenAI)
   - Multi-Stage Dockerfile
   - Kubernetes Manifests (Deployment, Service, Ingress)
   - Network Policy and RBAC
   - HPA Auto-Scaling
   - Terraform AWS Infrastructure (VPC, EKS, Secrets Manager)
   - CI/CD with GitHub Actions (CodeQL, Trivy, ECR, EKS deploy)
   - Monitoring with Prometheus ServiceMonitor
   - Cross-Module Integration Map (12 modules)

---

# MODULE 37: Performance Tuning, Multi-Cluster & Exam Preparation

- **37.1 Performance Tuning & Optimization**
   - Pod Resource Right-Sizing
   - NodeLocal DNSCache
   - Efficient Container Images
- **37.2 Multi-Cluster Management**
   - When to Use Multiple Clusters
   - Tools for Multi-Cluster
   - Kubernetes Federation
- **37.3 CKA/CKAD Exam Preparation**
   - Exam Environment
   - Exam Tips
   - Essential Speed Commands
   - Key Topics by Exam
- **37.4 Module 10 Exercises**
   - Exercise 1: etcd Backup and Restore
   - Exercise 2: Security Audit
   - Exercise 3: CKA Practice

---

