# MODULE 3: What is Kubernetes?

---

## 3.1 What is Kubernetes?

Kubernetes (K8s) is an open-source container orchestration platform originally developed by Google, now maintained by the Cloud Native Computing Foundation (CNCF). It automates the deployment, scaling, and management of containerized applications.

### Real-Life Analogy

Think of Kubernetes as an **airport control tower**:
- **Containers** = Individual airplanes (your applications)
- **Pods** = Runways assigned to airplanes
- **Nodes** = Terminals in the airport
- **Cluster** = The entire airport
- **Control Plane** = The control tower managing everything

### Monolithic vs Microservices Architecture

Understanding why Kubernetes exists requires understanding the architectural shift that created the need for container orchestration.

**Monolithic architecture** — the entire application is a single deployable unit. All components (UI, business logic, database access) share one codebase, one process, one deployment.

**Microservices architecture** — the application is split into small, independent services. Each service owns a specific function, deploys independently, and communicates via APIs (HTTP/gRPC) or messaging (Kafka/RabbitMQ).

| Aspect | Monolithic | Microservices |
|---|---|---|
| **Deployment** | Entire app redeployed for any change | Each service deployed independently |
| **Scaling** | Scale the whole application | Scale individual services based on demand |
| **Fault isolation** | One bug can crash the entire app | Failure in one service doesn't take down others |
| **Tech stack** | Single language/framework | Each service can use different languages/tools |
| **Team structure** | One team owns everything | Small teams own individual services |
| **Complexity** | Simple to start, hard to maintain at scale | Complex infrastructure, simple individual services |
| **Testing** | Full app must be tested together | Services tested independently |
| **Communication** | In-process function calls | Network calls (HTTP, gRPC, message queues) |

**When monoliths make sense:** Small applications, early-stage projects, small teams. A monolith is faster to build and simpler to operate when you have fewer than ~5 developers.

**When microservices make sense:** Large-scale systems with multiple teams, high traffic requiring independent scaling, and frequent releases across different components.

**The connection to Kubernetes:** Microservices generate dozens to hundreds of containers that need to be deployed, scaled, discovered, load-balanced, and healed automatically. This is the problem Kubernetes solves. Without orchestration, managing microservices at scale is operationally unsustainable.

### Why Kubernetes?

| Problem Without K8s | Solution With K8s |
|---|---|
| Manual deployment of containers | Automated deployment & rollbacks |
| No auto-healing when containers crash | Self-healing: restarts failed containers |
| Manual scaling during traffic spikes | Auto-scaling based on CPU/memory |
| Downtime during updates | Rolling updates with zero downtime |
| No service discovery | Built-in DNS and service discovery |
| Complex load balancing | Automatic load balancing |

### Core Functions of Kubernetes

| Function | What It Does | Example |
|---|---|---|
| **Container Orchestration** | Manages containerized apps across multiple nodes | Schedule 50 pods across 10 nodes |
| **Automated Deployment** | Defines desired state, K8s makes it happen | `kubectl apply -f deployment.yaml` |
| **Scaling & Load Balancing** | Adjusts replicas based on demand, distributes traffic | HPA scales from 3 to 10 pods at 70% CPU |
| **Service Discovery** | DNS-based discovery of services within the cluster | `backend-service.default.svc.cluster.local` |
| **Resource Management** | Allocates CPU/memory to containers | `requests: cpu: 100m, memory: 128Mi` |
| **Self-Healing** | Restarts crashed containers, replaces unresponsive pods | Pod OOMKilled → auto-restarted by kubelet |
| **Rolling Updates** | Zero-downtime deployments with rollback capability | `kubectl rollout undo deployment/web` |
| **Storage Orchestration** | Automatically mounts storage (EBS, EFS, NFS) to pods | PVC + StorageClass → dynamic provisioning |
| **Secret & Config Management** | Manages sensitive data and configuration separately | Secrets, ConfigMaps mounted into pods |

### Kubernetes Versioning

Kubernetes follows a `major.minor.patch` release format:

```
v1.29.2
│  │  └── Patch: bug fixes, security patches (e.g., 1.29.0 → 1.29.1 → 1.29.2)
│  └───── Minor: new features, API changes (released ~every 4 months)
└──────── Major: breaking changes (has been v1 since 2015)
```

```bash
# Check your cluster version
kubectl version --short

# Output:
# Client Version: v1.29.2
# Server Version: v1.29.1

# Check node versions
kubectl get nodes

# Output:
# NAME                          STATUS   ROLES    AGE   VERSION
# ip-10-0-1-100.ec2.internal    Ready    <none>   30d   v1.29.1
# ip-10-0-2-200.ec2.internal    Ready    <none>   30d   v1.29.1
```

**Release cycle:** 3 minor releases per year (~every 4 months). Each minor version is supported for ~14 months. Always keep your cluster within the supported version window.

**Release lifecycle — alpha, beta, stable:**

| Phase | Features | Stability | Default |
|---|---|---|---|
| **Alpha** (e.g., v1.30.0-alpha.1) | New, experimental features | May be buggy, may be removed | Disabled by default (feature gate) |
| **Beta** (e.g., v1.30.0-beta.1) | Well-tested features | API may still change | Enabled by default |
| **Stable** (e.g., v1.30.0) | Production-ready | Backward-compatible | Enabled, fully supported |

**Release artifacts:** All Kubernetes releases are published on the [GitHub releases page](https://github.com/kubernetes/kubernetes/releases). The downloadable `kubernetes.tar.gz` contains binaries for all control plane components. Note that while control plane components (kube-apiserver, kube-controller-manager, kube-scheduler, kube-proxy) all share the same version number, **etcd and CoreDNS have their own independent version numbers** — they are separate projects bundled with Kubernetes.

**Version skew policy:** kubelet can be up to 2 minor versions behind the API server. kubectl can be 1 minor version ahead or behind the API server.

### Industry Example: Spotify

Spotify migrated from their custom orchestration to Kubernetes to manage 1,800+ microservices. This reduced their deployment time from hours to minutes and allowed teams to independently deploy services.

---

