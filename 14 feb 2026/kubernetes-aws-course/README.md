# Kubernetes on AWS — Complete Course

A hands-on course covering Kubernetes from zero to production on Amazon EKS. Every concept includes commands with explanations, expected outputs, real-world examples, and troubleshooting steps. 37 modules, each focused on a single topic.

---

## Course Structure

### Phase 1: Prerequisites

| # | Module | File | Topics |
|---|---|---|---|
| 01 | **YAML Syntax** | [MODULE-01](MODULE-01-YAML-Syntax.md) | Key-value pairs, dictionaries, lists, indentation, document separators, Kubernetes YAML patterns |
| 02 | **Docker & Containers** | [MODULE-02](MODULE-02-Docker-Fundamentals.md) | Dockerfile, image layers, copy-on-write, volumes, bind mounts, storage drivers, Docker service configuration, Docker vs ContainerD |

### Phase 2: Kubernetes Core

| # | Module | File | Topics |
|---|---|---|---|
| 03 | **What is Kubernetes?** | [MODULE-03](MODULE-03-What-is-Kubernetes.md) | Why Kubernetes, core functions, versioning, industry examples |
| 04 | **Architecture** | [MODULE-04](MODULE-04-Architecture.md) | Control plane (API server, scheduler, controller manager, etcd), worker nodes (kubelet, kube-proxy), end-to-end flow |
| 05 | **Objects & Manifests** | [MODULE-05](MODULE-05-Objects.md) | Pods, Services, Deployments, ConfigMaps — the building blocks and YAML specification pattern |
| 06 | **Cluster Setup** | [MODULE-06](MODULE-06-Cluster-Setup.md) | Minikube, Kind (multi-node), kubeadm (production) |
| 07 | **kubectl CLI** | [MODULE-07](MODULE-07-kubectl.md) | Installation, command structure, essential commands, create vs apply, apply internals |
| 08 | **Namespaces** | [MODULE-08](MODULE-08-Namespaces.md) | Namespace strategy, LimitRange, ResourceQuota, cross-namespace access |

### Phase 3: Cloud Setup

| # | Module | File | Topics |
|---|---|---|---|
| 09 | **Amazon EKS Setup** | [MODULE-09](MODULE-09-EKS-Setup.md) | AWS CLI, eksctl, VPC-CNI, IAM/IRSA, add-ons, Terraform, cost optimization |

### Phase 4: Workloads

| # | Module | File | Topics |
|---|---|---|---|
| 10 | **Pods** | [MODULE-10](MODULE-10-Pods.md) | Single/multi-container, sidecar, init containers, lifecycle hooks, probes, labels, selectors, private registries |
| 11 | **ReplicaSets & Deployments** | [MODULE-11](MODULE-11-ReplicaSets-Deployments.md) | ReplicaSets, Deployments, rolling updates, rollbacks, canary, scaling |
| 12 | **DaemonSets, Jobs & StatefulSets** | [MODULE-12](MODULE-12-DaemonSets-Jobs-StatefulSets.md) | DaemonSet, StatefulSet, Job, CronJob, static pods |

### Phase 5: Networking

| # | Module | File | Topics |
|---|---|---|---|
| 13 | **Services & DNS** | [MODULE-13](MODULE-13-Services.md) | ClusterIP, NodePort, LoadBalancer, ExternalName, headless services, CoreDNS |
| 14 | **Ingress & Gateway API** | [MODULE-14](MODULE-14-Ingress.md) | NGINX/ALB ingress controllers, path/host routing, TLS, rewrite-target, Gateway API |
| 15 | **Network Policies** | [MODULE-15](MODULE-15-Network-Policies.md) | Ingress/egress rules, selectors, AND/OR logic, CNI deep dive, switching/routing/namespaces |

### Phase 6: Configuration & Storage

| # | Module | File | Topics |
|---|---|---|---|
| 16 | **ConfigMaps & Secrets** | [MODULE-16](MODULE-16-ConfigMaps-Secrets.md) | Environment variables, ConfigMaps, Secrets, encryption at rest, AWS Secrets Manager, Vault |
| 17 | **Storage** | [MODULE-17](MODULE-17-Storage.md) | Volumes, PV/PVC, StorageClass, EFS, CSI drivers, dynamic provisioning |

### Phase 7: Resource Management & Scheduling

| # | Module | File | Topics |
|---|---|---|---|
| 18 | **Resource Management** | [MODULE-18](MODULE-18-Resource-Management.md) | Requests, limits, LimitRange, ResourceQuota, QoS classes |
| 19 | **Scheduling** | [MODULE-19](MODULE-19-Scheduling.md) | nodeName, nodeSelector, taints/tolerations, node affinity, pod affinity, topology spread, custom schedulers, priority/preemption, PDB |
| 20 | **Auto-Scaling** | [MODULE-20](MODULE-20-Auto-Scaling.md) | HPA, VPA, Cluster Autoscaler, Karpenter, KEDA |

### Phase 8: Security

| # | Module | File | Topics |
|---|---|---|---|
| 21 | **Pod Security** | [MODULE-21](MODULE-21-Pod-Security.md) | Docker security fundamentals, SecurityContext, Pod Security Standards |
| 22 | **RBAC** | [MODULE-22](MODULE-22-RBAC.md) | Roles, RoleBindings, ClusterRoles, ClusterRoleBindings, authorization mechanisms |
| 23 | **Authentication & Certificates** | [MODULE-23](MODULE-23-Authentication-Certificates.md) | OIDC, TLS fundamentals, Kubernetes PKI, certificate creation/inspection, KubeConfig |
| 24 | **Service Accounts & API Access** | [MODULE-24](MODULE-24-Service-Accounts-API.md) | Service accounts, API groups, kubectl proxy, EKS IAM integration |

### Phase 9: DevOps & Operations

| # | Module | File | Topics |
|---|---|---|---|
| 25 | **Helm** | [MODULE-25](MODULE-25-Helm.md) | Charts, releases, values, templating, creating custom charts |
| 26 | **CI/CD** | [MODULE-26](MODULE-26-CICD.md) | GitHub Actions, ArgoCD GitOps, Jenkins on Kubernetes |
| 27 | **Monitoring & Logging** | [MODULE-27](MODULE-27-Monitoring-Logging.md) | Metrics Server, Prometheus, Grafana, AlertManager, Fluent Bit, CloudWatch |
| 28 | **Version Upgrades** | [MODULE-28](MODULE-28-Version-Upgrades.md) | Version skew policy, kubeadm upgrades, EKS upgrades, drain/uncordon |
| 29 | **Troubleshooting** | [MODULE-29](MODULE-29-Troubleshooting.md) | Pod errors, networking issues, storage problems, node failures, control plane, EKS-specific, debugging toolkit |

### Phase 10: Advanced & Specialist

| # | Module | File | Topics |
|---|---|---|---|
| 30 | **Admission Controllers** | [MODULE-30](MODULE-30-Admission-Controllers.md) | Built-in controllers, mutating/validating webhooks, PSA, ValidatingAdmissionPolicy, OPA/Kyverno |
| 31 | **Security Hardening** | [MODULE-31](MODULE-31-Security-Hardening.md) | Docker daemon security, kubelet security, CIS benchmarks/kube-bench, Kubernetes Dashboard, network security |
| 32 | **etcd Operations** | [MODULE-32](MODULE-32-etcd.md) | Backup, restore, stacked vs external topology, Velero |
| 33 | **API Deep Dive** | [MODULE-33](MODULE-33-API-Deep-Dive.md) | API groups, request flow, audit logging, rate limiting, versioning |
| 34 | **CRDs & Operators** | [MODULE-34](MODULE-34-CRDs-Operators.md) | Custom Resource Definitions, custom controllers, operator pattern |
| 35 | **Service Mesh** | [MODULE-35](MODULE-35-Service-Mesh.md) | Microservices patterns, Istio architecture, mTLS, traffic management, circuit breaking |
| 36 | **Industry Projects** | [MODULE-36](MODULE-36-Industry-Projects.md) | E-commerce platform, blue-green deployment, multi-tenant SaaS, ML model serving |
| 37 | **Exam Preparation** | [MODULE-37](MODULE-37-Advanced-Exam-Prep.md) | Performance tuning, multi-cluster, CKA/CKAD exam tips, speed commands |

---

## Learning Path

```
PREREQUISITES           KUBERNETES CORE              WORKLOADS
┌────────────┐    ┌───────────────────────┐    ┌──────────────────┐
│ 01 YAML    │───►│ 03 What is K8s?       │───►│ 10 Pods          │
│ 02 Docker  │    │ 04 Architecture       │    │ 11 Deployments   │
└────────────┘    │ 05 Objects            │    │ 12 Jobs/SS/DS    │
                  │ 06 Cluster Setup      │    └────────┬─────────┘
                  │ 07 kubectl            │             │
                  │ 08 Namespaces         │             ▼
                  └───────────────────────┘    NETWORKING
                                              ┌──────────────────┐
  CLOUD SETUP                                 │ 13 Services/DNS  │
  ┌────────────┐                              │ 14 Ingress       │
  │ 09 EKS     │                              │ 15 NetPolicies   │
  └────────────┘                              └────────┬─────────┘
                                                       │
CONFIG & STORAGE        SCHEDULING & SCALING           ▼
┌──────────────────┐    ┌──────────────────┐    SECURITY
│ 16 ConfigMaps    │    │ 18 Resources     │    ┌──────────────────┐
│ 17 Storage       │    │ 19 Scheduling    │    │ 21 Pod Security  │
└──────────────────┘    │ 20 Auto-Scaling  │    │ 22 RBAC          │
                        └──────────────────┘    │ 23 Auth/Certs    │
                                                │ 24 Service Accts │
DEVOPS & OPS            ADVANCED                └──────────────────┘
┌──────────────────┐    ┌──────────────────┐
│ 25 Helm          │    │ 30 Admission Ctl │
│ 26 CI/CD         │    │ 31 Hardening     │
│ 27 Monitoring    │    │ 32 etcd          │
│ 28 Upgrades      │    │ 33 API Deep Dive │
│ 29 Troubleshoot  │    │ 34 CRDs          │
└──────────────────┘    │ 35 Service Mesh  │
                        │ 36 Projects      │
                        │ 37 Exam Prep     │
                        └──────────────────┘
```

## Recommended Schedule

```
Week 1:  Modules 01-08  (Prerequisites + Core)
Week 2:  Modules 09-12  (EKS + Workloads)
Week 3:  Modules 13-17  (Networking + Config + Storage)
Week 4:  Modules 18-24  (Scheduling + Security)
Week 5:  Modules 25-29  (DevOps + Operations)
Week 6:  Modules 30-37  (Advanced + Projects)
```

## Prerequisites

- AWS account with admin access
- Basic Linux command-line knowledge

## Tools Required

| Tool | Purpose |
|---|---|
| `aws` CLI | AWS resource management |
| `eksctl` | EKS cluster lifecycle |
| `kubectl` | Kubernetes cluster interaction |
| `helm` | Package management |
| `docker` | Container building |
