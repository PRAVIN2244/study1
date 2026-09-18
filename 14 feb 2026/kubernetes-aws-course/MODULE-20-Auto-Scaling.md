# MODULE 20: Auto-Scaling — HPA, VPA, Cluster Autoscaler & Karpenter

---

## 20.1 Auto-Scaling

### Scaling Concepts

Before Kubernetes, applications ran on physical servers with fixed CPU and memory. When load exceeded capacity, you had two options:

- **Vertical scaling** — shut down the server, add more CPU/memory, restart. Causes downtime.
- **Horizontal scaling** — add another server to distribute the load. No downtime if the application supports multiple instances.

In Kubernetes, these concepts apply at two levels:

| Level | Horizontal Scaling | Vertical Scaling |
|-------|-------------------|------------------|
| **Cluster infrastructure** | Add more nodes to the cluster | Increase CPU/memory on existing nodes |
| **Workloads** | Create more pods (replicas) | Increase resource requests/limits on existing pods |

**Manual scaling commands:**

```bash
# Cluster: add a new node
kubeadm join <control-plane-endpoint> --token <token> --discovery-token-ca-cert-hash <hash>

# Workload horizontal: add more pod replicas
kubectl scale deployment my-app --replicas=5

# Workload vertical: edit resource requests/limits (causes pod restart)
kubectl edit deployment my-app
```

**Automated scaling mechanisms:**

| What Scales | Manual Command | Automated Mechanism |
|-------------|---------------|---------------------|
| Pod replicas | `kubectl scale` | Horizontal Pod Autoscaler (HPA) |
| Pod resources (CPU/memory) | `kubectl edit` | Vertical Pod Autoscaler (VPA) |
| Cluster nodes | `kubeadm join` | Cluster Autoscaler / Karpenter |

Vertical scaling of nodes is uncommon in Kubernetes — it's easier to provision a new node with more resources, add it to the cluster, and drain the old one.

### Autoscaling Levels

Kubernetes provides three levels of autoscaling:

| Level | What scales | Mechanism |
|---|---|---|
| **Pod-level horizontal** | Number of pod replicas | HPA (Horizontal Pod Autoscaler) |
| **Pod-level vertical** | CPU/memory requests per pod | VPA (Vertical Pod Autoscaler) |
| **Node-level** | Number of worker nodes | Cluster Autoscaler / Karpenter |

**How they work together:**
1. HPA detects high CPU → scales pods from 3 to 8
2. Scheduler can't place new pods (no node capacity) → pods stay Pending
3. Cluster Autoscaler detects Pending pods → adds new nodes
4. Scheduler places pods on new nodes

**Important rules:**
- Do NOT use HPA and VPA together on the same metric (they conflict)
- HPA/VPA are typically not needed for QA/dev clusters
- Cluster Autoscaler should be used on ALL clusters (QA, staging, production)

### Horizontal Pod Autoscaler (HPA)

Scales the number of pod replicas based on CPU/memory or custom metrics. HPA has been a stable feature since Kubernetes v1.23 (autoscaling/v2).

**The problem HPA solves — manual scaling:**

Without HPA, you must monitor resource usage and scale manually:

```bash
# Check pod resource usage
kubectl top pod my-app-pod
```

```
NAME         CPU(cores)   MEMORY(bytes)
my-app-pod   450m         350Mi
```

When usage approaches the limit (e.g., 450m out of 500m limit), you manually scale:

```bash
kubectl scale deployment my-app --replicas=3
```

This requires continuous monitoring and is error-prone during traffic surges. HPA automates this.

**Sample deployment with resource requests/limits:**

```yaml
# my-app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: nginx
        resources:
          requests:
            cpu: "250m"
          limits:
            cpu: "500m"
```

HPA calculates utilization as a percentage of the **request** value (not the limit). If the request is 250m and current usage is 200m, utilization is 80%.

**Prerequisites — Metrics Server:**

```bash
# Prerequisites: Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify metrics-server
kubectl top nodes

# Output:
# NAME                          CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# ip-10-0-1-100.ec2.internal    250m         12%    1200Mi          30%
# ip-10-0-2-200.ec2.internal    180m         9%     980Mi           24%

kubectl top pods

# Output:
# NAME                     CPU(cores)   MEMORY(bytes)
# webapp-7bf8c77b5b-abc12  50m          128Mi
# webapp-7bf8c77b5b-def34  45m          125Mi
```

**Imperative HPA creation:**

```bash
# Create an HPA that targets 50% CPU utilization, scaling between 1 and 10 replicas
kubectl autoscale deployment my-app --cpu-percent=50 --min=1 --max=10
```

```
horizontalpodautoscaler.autoscaling/my-app autoscaled
```

```bash
# Check HPA status
kubectl get hpa
```

```
NAME     REFERENCE           TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
my-app   Deployment/my-app   30%/50%   1         10        1          30s
```

```bash
# Delete the HPA when no longer needed
kubectl delete hpa my-app
```

```
horizontalpodautoscaler.autoscaling "my-app" deleted
```

**Declarative HPA configuration:**

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70      # Scale up when CPU > 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80      # Scale up when memory > 80%
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60    # Wait 60s before scaling up
      policies:
      - type: Pods
        value: 4
        periodSeconds: 60               # Add max 4 pods per minute
    scaleDown:
      stabilizationWindowSeconds: 300   # Wait 5 min before scaling down
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60               # Remove max 25% pods per minute
```

```bash
kubectl apply -f hpa.yaml

kubectl get hpa

# Output:
# NAME         REFERENCE           TARGETS           MINPODS   MAXPODS   REPLICAS   AGE
# webapp-hpa   Deployment/webapp   12%/70%, 25%/80%  3         20        3          30s

# Load test to trigger scaling
kubectl run load-test --image=busybox --rm -it -- /bin/sh -c "while true; do wget -q -O- http://webapp-service; done"

# Watch HPA react
kubectl get hpa -w

# Output:
# NAME         REFERENCE           TARGETS           MINPODS   MAXPODS   REPLICAS   AGE
# webapp-hpa   Deployment/webapp   12%/70%, 25%/80%  3         20        3          1m
# webapp-hpa   Deployment/webapp   75%/70%, 45%/80%  3         20        3          2m    ← CPU exceeded!
# webapp-hpa   Deployment/webapp   75%/70%, 45%/80%  3         20        5          3m    ← Scaled to 5
# webapp-hpa   Deployment/webapp   55%/70%, 35%/80%  3         20        5          4m    ← Stabilized
```

**HPA metrics sources:**

HPA can consume metrics from three sources:

| Source | API | What It Provides | Example |
|--------|-----|------------------|---------|
| Metrics Server | `metrics.k8s.io` | CPU and memory usage per pod/node | Built-in, deployed in-cluster |
| Custom Metrics Adapter | `custom.metrics.k8s.io` | Application-specific metrics from inside the cluster | Prometheus Adapter exposing `http_requests_per_second` |
| External Metrics Adapter | `external.metrics.k8s.io` | Metrics from outside the cluster | Datadog, Dynatrace, CloudWatch queue depth |

Custom and external metrics adapters allow HPA to scale on business-relevant signals (e.g., queue length, request latency) rather than just CPU/memory.

**HPA with custom pod metrics:**

```yaml
# hpa-custom-metric.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-deployment
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

```bash
kubectl apply -f hpa-custom-metric.yaml
kubectl get hpa -n api
```

The `type: Pods` metric type reads per-pod metrics from the custom metrics API (`custom.metrics.k8s.io`). This requires a metrics adapter (e.g., Prometheus Adapter) that exposes the metric. The `AverageValue` target means HPA divides the total metric value across all pods and scales to keep each pod's average at the target.

**HPA with external metrics (e.g., SQS queue depth):**

```yaml
# hpa-external-metric.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: queue-worker
  minReplicas: 1
  maxReplicas: 50
  metrics:
  - type: External
    external:
      metric:
        name: sqs_messages_visible
        selector:
          matchLabels:
            queue: orders
      target:
        type: AverageValue
        averageValue: "5"
```

| Metric Type | Source | Use Case |
|---|---|---|
| `Resource` | Metrics Server (CPU/memory) | General workload scaling |
| `Pods` | Custom metrics API (per-pod) | App-specific metrics (RPS, latency) |
| `External` | External metrics API | Cloud services (SQS depth, Pub/Sub backlog) |
| `Object` | Custom metrics on K8s objects | Ingress RPS, Service latency |

### Vertical Pod Autoscaler (VPA)

Adjusts CPU/memory requests and limits automatically. Unlike HPA (which adds more pods), VPA changes the resource allocation of existing pods.

**The problem VPA solves — manual vertical scaling:**

Without VPA, you must monitor resource usage and manually edit the deployment:

```bash
kubectl top pod my-app-pod
```

```
NAME         CPU(cores)   MEMORY(bytes)
my-app-pod   450m         350Mi
```

When usage approaches the limit, you manually update the deployment:

```bash
kubectl edit deployment my-app
# Change resources.requests.cpu from "250m" to "500m"
# Save → Kubernetes deletes the old pod and creates a new one with updated resources
```

This is error-prone and requires continuous monitoring. VPA automates this.

**Installing VPA:**

VPA is **not included by default** in Kubernetes. Deploy it from the autoscaler GitHub repository:

```bash
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vertical-pod-autoscaler.yaml
```

Verify the three VPA components are running:

```bash
kubectl get pods -n kube-system | grep vpa
```

```
vpa-admission-controller-6cd5f5b6b7-abc12   1/1     Running   0          30s
vpa-recommender-7c8f9d4e5f-def34             1/1     Running   0          30s
vpa-updater-8b7c6d5e4f-ghi56                 1/1     Running   0          30s
```

**VPA components:**

| Component | Role |
|-----------|------|
| **Recommender** | Monitors resource usage via the metrics API, aggregates historical and live data, provides recommendations for optimal CPU/memory |
| **Updater** | Compares running pods against recommendations, evicts pods with suboptimal resource requests so they can be recreated |
| **Admission Controller** | Intercepts pod creation and mutates the pod spec with the recommender's suggested resources before the pod starts |

**VPA configuration:**

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: webapp-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webapp
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: webapp
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      maxAllowed:
        cpu: "2"
        memory: "4Gi"
      controlledResources: ["cpu", "memory"]  # Which resources VPA manages
```

**VPA update modes:**

| Mode | Behavior | Use Case |
|------|----------|----------|
| `Off` | Provides recommendations only — no changes applied | Start here to review what VPA would do |
| `Initial` | Applies recommendations only when pods are first created | Safe for production — existing pods untouched |
| `Recreate` | Evicts running pods to apply updated resource values (causes restarts) | When you need active right-sizing |
| `Auto` | Currently behaves like `Recreate`; in the future may support in-place updates | Default for most setups |

Best practice: start with `Off` to review recommendations, then switch to `Auto` once you trust the sizing.

**Viewing VPA recommendations:**

```bash
kubectl describe vpa webapp-vpa
```

```
Recommendation:
  Container Recommendations:
    Container Name:  webapp
    Lower Bound:
      Cpu:     100m
      Memory:  128Mi
    Target:
      Cpu:     1500m
      Memory:  512Mi
    Upper Bound:
      Cpu:     2
      Memory:  1Gi
```

The VPA recommends increasing CPU to 1.5 cores and memory to 512Mi based on observed usage patterns.

```bash
# Check current VPA status
kubectl get vpa
```

```
NAME         MODE   CPU    MEM     PROVIDED   AGE
webapp-vpa   Auto   1500m  512Mi   True       5m
```

**Memory-based HPA example:**

```yaml
# hpa-memory.yaml
apiVersion: autoscaling/v2beta1
kind: HorizontalPodAutoscaler
metadata:
  name: myhpamem
spec:
  maxReplicas: 5
  minReplicas: 1
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mydeploy
  metrics:
  - type: Resource
    resource:
      name: memory
      targetAverageUtilization: 20
```

**Stress testing to trigger HPA:**

```bash
# Exec into a pod and install stress tool
kubectl exec -it <pod-name> -- /bin/bash
  apt update
  apt install -y stress
  stress --vm 1 --vm-bytes 100M
```

**Enabling metrics-server on Minikube:**

```bash
minikube addons list
minikube addons enable metrics-server

# Verify metrics
kubectl top nodes
kubectl top pods
```

### In-Place Pod Resource Resizing

Traditionally, changing a pod's CPU or memory requests/limits in a Deployment causes Kubernetes to delete the existing pod and create a new one with the updated resources. This is disruptive — especially for stateful workloads.

**In-place pod vertical scaling** is a feature that allows updating CPU and memory resources on a running pod without restarting it. This is currently in **alpha** (since Kubernetes 1.27) and must be explicitly enabled.

**Enabling the feature:**

```bash
# Enable via feature gate on the kubelet and API server
--feature-gates=InPlacePodVerticalScaling=true
```

**Resize policy:**

When the feature is enabled, you can specify per-resource restart behavior using `resizePolicy`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: my-app
    image: nginx
    resources:
      requests:
        cpu: "250m"
        memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"
    resizePolicy:
    - resourceName: cpu
      restartPolicy: NotRequired    # CPU changes applied without restart
    - resourceName: memory
      restartPolicy: RestartContainer  # Memory changes require container restart
```

With this configuration:
- Increasing the CPU request from 250m to 500m takes effect immediately — no pod restart
- Changing the memory limit triggers a container restart (memory allocation requires re-initialization)

**In a Deployment:**

The same `resizePolicy` works in Deployment specs. When you update the CPU request, the running pod is updated in place instead of being deleted and recreated:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: nginx
        resizePolicy:
        - resourceName: cpu
          restartPolicy: NotRequired
        resources:
          requests:
            cpu: "250m"        # Change to "1" — applied without pod restart
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
```

Without the feature flag, changing `cpu: "250m"` to `cpu: "1"` would delete the pod and create a new one. With in-place resizing enabled, the change is applied to the running pod directly.

**Limitations:**

| Limitation | Detail |
|-----------|--------|
| Supported resources | Only CPU and memory can be resized in place |
| QoS class | Cannot be changed via in-place resize (e.g., Guaranteed → Burstable) |
| Init containers | Not eligible for resizing |
| Ephemeral containers | Not eligible for resizing |
| Memory reduction | Cannot reduce memory limit below current usage — resize stays in progress until usage drops |
| Windows pods | Not supported |
| Feature status | Alpha (v1.27+) — not enabled by default, not recommended for production |

**Real-world use case:** A database pod needs more CPU during a batch import. Instead of restarting the pod (which would interrupt active connections), you increase the CPU request in place. The pod continues serving traffic while receiving additional CPU allocation.

> This feature is expected to progress to beta and eventually stable. For automated resource adjustment, see the Vertical Pod Autoscaler (VPA) above.

### HPA vs VPA Comparison

| Feature | HPA | VPA |
|---|---|---|
| **Best for** | Stateless workloads (Deployments) | Stateful workloads (StatefulSets) |
| **Scaling method** | Creates new pod replicas | Recreates existing pods with adjusted resources |
| **Configuration** | Requires min/max replica count | No min/max replicas needed |
| **Cooldown** | Default 5-minute cooldown before scale-down | No cooldown period |
| **Combination** | Do not use HPA and VPA together on the same metric | — |

**When to use which:**
- Use HPA for stateless applications that can scale horizontally
- Use VPA for stateful applications or when horizontal scaling isn't practical
- Use Cluster Autoscaler for all clusters (QA, staging, production) to handle node-level scaling
- HPA/VPA are typically not needed for QA clusters

### Cluster Autoscaler (Node-level)

Scales the number of EC2 nodes based on pending pods.

```bash
# Install Cluster Autoscaler
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=my-k8s-cluster \
  --set awsRegion=us-east-1 \
  --set rbac.serviceAccount.name=cluster-autoscaler \
  --set rbac.serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::123456789012:role/ClusterAutoscalerRole

# Verify
kubectl get deployment -n kube-system cluster-autoscaler

# Output:
# NAME                 READY   UP-TO-DATE   AVAILABLE   AGE
# cluster-autoscaler   1/1     1            1           30s

# Check autoscaler logs
kubectl logs -n kube-system deployment/cluster-autoscaler | tail -5

# Output:
# I0115 10:00:00.000000       1 scale_up.go:300] Pod default/webapp-abc12 is unschedulable
# I0115 10:00:01.000000       1 scale_up.go:468] Best option to resize: eks-standard-workers
# I0115 10:00:02.000000       1 scale_up.go:532] Scale-up: setting group eks-standard-workers size to 4
```

### Karpenter (AWS-Native Alternative to Cluster Autoscaler)

Karpenter is faster and more flexible than Cluster Autoscaler.

```yaml
# karpenter-nodepool.yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: "karpenter.k8s.aws/instance-category"
        operator: In
        values: ["c", "m", "r"]
      - key: "karpenter.k8s.aws/instance-size"
        operator: In
        values: ["medium", "large", "xlarge"]
      - key: "topology.kubernetes.io/zone"
        operator: In
        values: ["us-east-1a", "us-east-1b", "us-east-1c"]
      - key: "karpenter.sh/capacity-type"
        operator: In
        values: ["spot", "on-demand"]
      nodeClassRef:
        name: default
  limits:
    cpu: 100
    memory: 400Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    expireAfter: 720h    # Replace nodes after 30 days
---
apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-k8s-cluster
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: my-k8s-cluster
```

### KEDA (Kubernetes Event-Driven Autoscaling)

KEDA extends HPA to scale based on external event sources (SQS queue depth, Kafka lag, Prometheus queries):

```yaml
# keda-scaledobject.yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-consumer-scaler
spec:
  scaleTargetRef:
    name: sqs-consumer
  minReplicaCount: 0          # Scale to zero when queue is empty
  maxReplicaCount: 50
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.us-east-1.amazonaws.com/123456789012/my-queue
      queueLength: "5"        # Scale up when > 5 messages per pod
      awsRegion: us-east-1
```

```bash
# Install KEDA
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda --namespace keda --create-namespace
```

### Complete Autoscaling Summary

| Autoscaler | What It Scales | Trigger | Best For |
|---|---|---|---|
| **HPA** | Pod replicas | CPU, memory, custom metrics | Stateless web apps, APIs |
| **VPA** | Pod resource requests | Historical usage | Stateful apps, right-sizing |
| **Cluster Autoscaler** | Worker nodes | Pending (unschedulable) pods | All clusters |
| **Karpenter** | Worker nodes (AWS) | Pending pods, consolidation | EKS (faster than CA) |
| **KEDA** | Pod replicas | External events (SQS, Kafka, Prometheus) | Event-driven workloads |
| **Virtual Nodes (ACI/Fargate)** | Serverless pods | Pending pods needing burst capacity | Burst workloads without provisioning nodes |

**Interview question: What autoscaling options are available in Kubernetes?**
Three levels: (1) HPA scales pod replicas based on CPU/memory/custom metrics, (2) VPA adjusts pod resource requests based on historical usage, (3) Cluster Autoscaler/Karpenter scales worker nodes when pods can't be scheduled. KEDA adds event-driven scaling from external sources. HPA and VPA should not target the same metric on the same deployment.

---

