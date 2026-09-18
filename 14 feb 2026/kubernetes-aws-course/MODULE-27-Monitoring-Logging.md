# MODULE 27: Monitoring & Logging — Metrics Server, Prometheus & EFK

---

## 27.1 Monitoring Cluster Components

### What to Monitor

Monitoring a Kubernetes cluster involves tracking metrics at both the node and pod levels.

**Node-level metrics:**
- Number of nodes in the cluster and their health status
- CPU, memory, network, and disk utilization per node

**Pod-level metrics:**
- Number of running pods
- CPU and memory consumption per pod

Kubernetes does not include a built-in monitoring solution. You must deploy an external tool. Options include:

| Tool | Type | Use Case |
|------|------|----------|
| Metrics Server | Open-source, lightweight | Basic real-time metrics (`kubectl top`) |
| Prometheus | Open-source, full-featured | Long-term storage, alerting, PromQL queries |
| Elastic Stack (ELK/EFK) | Open-source | Log aggregation and search |
| Datadog | Proprietary | Full observability platform |
| Dynatrace | Proprietary | AI-powered monitoring |

### From Heapster to Metrics Server

Heapster was the original monitoring and analysis tool for Kubernetes. It has been **deprecated** and replaced by **Metrics Server** — a streamlined, lightweight alternative.

Key characteristics of Metrics Server:
- **One per cluster** — a single Metrics Server instance serves the entire cluster
- **In-memory only** — metrics are stored in memory, not persisted to disk
- **No historical data** — only current resource usage is available; for historical metrics, use Prometheus or similar tools
- **Enables `kubectl top`** — the `kubectl top node` and `kubectl top pod` commands require Metrics Server

### How Metrics Are Collected

The metrics collection pipeline:

```
Container → cAdvisor (in Kubelet) → Kubelet API → Metrics Server → kubectl top
```

1. Every Kubernetes node runs a **kubelet**, which manages pod operations and communicates with the API server
2. The kubelet includes **cAdvisor** (Container Advisor) — an integrated component that collects performance metrics from running containers
3. cAdvisor exposes metrics via the **Kubelet API**
4. **Metrics Server** retrieves metrics from each node's Kubelet API and aggregates them

### Deploying Metrics Server

**On Minikube:**

```bash
minikube addons enable metrics-server
```

**On other clusters (including EKS):**

```bash
# Clone the metrics-server repository
git clone https://github.com/kubernetes-incubator/metrics-server.git

# Deploy using the manifests
kubectl create -f deploy/1.8+/
```

Or use the latest release directly:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

```
clusterrole.rbac.authorization.k8s.io/system:aggregated-metrics-reader created
clusterrolebinding.rbac.authorization.k8s.io/metrics-server:system:auth-delegator created
rolebinding.rbac.authorization.k8s.io/metrics-server-auth-reader created
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io created
serviceaccount/metrics-server created
deployment.apps/metrics-server created
service/metrics-server created
clusterrole.rbac.authorization.k8s.io/system:metrics-server created
clusterrolebinding.rbac.authorization.k8s.io/system:metrics-server created
```

Allow a few minutes for Metrics Server to start collecting data from the nodes.

### Viewing Metrics

**Node resource usage:**

```bash
kubectl top node
```

```
NAME         CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
kubemaster   166m         8%     1337Mi          70%
kubenode01   36m          1%     1046Mi          55%
kubenode02   39m          1%     1048Mi          55%
```

**Pod resource usage:**

```bash
kubectl top pod
```

```
NAME    CPU(cores)   MEMORY(bytes)
nginx   2m           5Mi
redis   36m          50Mi
```

```bash
# Sort by CPU usage
kubectl top pod --sort-by=cpu

# Sort by memory usage
kubectl top pod --sort-by=memory

# Show container-level metrics
kubectl top pod --containers

# Metrics for a specific namespace
kubectl top pod -n kube-system
```

If Metrics Server is not installed, you get:

```
error: Metrics API not available
```

> Metrics Server provides real-time snapshots only. For historical trends, alerting, and dashboards, deploy Prometheus (covered in the next section).

### Lab: Metrics Server Walkthrough

**Step 1: Verify workloads are running**

```bash
kubectl get pods
```

```
NAME       READY   STATUS    RESTARTS   AGE
elephant   1/1     Running   0          27s
lion       1/1     Running   0          27s
rabbit     1/1     Running   0          27s
```

**Step 2: Deploy Metrics Server**

```bash
# Clone the metrics-server repository
git clone https://github.com/kodekloudhub/kubernetes-metrics-server.git
```

```
Cloning into 'kubernetes-metrics-server'...
remote: Enumerating objects: 24, done.
remote: Counting objects: 100% (12/12), done.
remote: Compressing objects: 100% (12/12), done.
remote: Total 24 (delta 4), reused 0 (delta 0), pack-reused 12
Unpacking objects: 100% (24/24), done.
```

```bash
# Review the configuration files
cd kubernetes-metrics-server/
ls
```

```
README.md                       auth-metrics-reader.yaml
aggregated-metrics-reader.yaml  metrics-apiserver-deployment.yaml
auth-delegator.yaml             metrics-server-service.yaml
resource-reader.yaml            metrics-server-deployment.yaml
```

```bash
# Deploy all resources at once
kubectl create -f .
```

```
clusterrole.rbac.authorization.k8s.io/system:aggregated-metrics-reader created
clusterrolebinding.rbac.authorization.k8s.io/metrics-server:system:auth-delegator created
rolebinding.rbac.authorization.k8s.io/metrics-server-auth-reader created
apiservice.apiregistration.k8s.io/v1beta1.metrics.k8s.io created
serviceaccount/metrics-server created
deployment.apps/metrics-server created
service/metrics-server created
clusterrole.rbac.authorization.k8s.io/system:metrics-server created
```

Wait a few minutes for Metrics Server to start collecting data.

**Step 3: Identify the node with the highest CPU and memory usage**

```bash
kubectl top node
```

```
NAME           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
controlplane   478m         1%     1252Mi          0%
node01         57m          0%     349Mi           0%
```

The control plane node has the highest CPU (478m) and memory (1252Mi) — expected because it runs API server, etcd, scheduler, and controller manager.

**Step 4: Identify the pod consuming the most memory and least CPU**

```bash
kubectl top pod
```

```
NAME       CPU(cores)   MEMORY(bytes)
elephant   20m          32Mi
lion       1m           18Mi
rabbit     131m         252Mi
```

- **Most memory:** `rabbit` (252Mi) — likely a memory-intensive workload like RabbitMQ
- **Most CPU:** `rabbit` (131m)
- **Least CPU:** `lion` (1m) — minimal processing requirements

```bash
# Quick way to find the pod using the most memory
kubectl top pod --sort-by=memory | head -2
```

```
NAME       CPU(cores)   MEMORY(bytes)
rabbit     131m         252Mi
```

---

## 27.2 Monitoring with Prometheus & Grafana

### Install Prometheus Stack

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=gp3 \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.storageClassName=gp3 \
  --set grafana.persistence.size=10Gi

# Output:
# NAME: monitoring
# STATUS: deployed

# Verify installation
kubectl get pods -n monitoring

# Output:
# NAME                                                     READY   STATUS    RESTARTS   AGE
# alertmanager-monitoring-kube-prometheus-alertmanager-0    2/2     Running   0          2m
# monitoring-grafana-abc12                                 3/3     Running   0          2m
# monitoring-kube-prometheus-operator-def34                1/1     Running   0          2m
# monitoring-kube-state-metrics-ghi56                      1/1     Running   0          2m
# monitoring-prometheus-node-exporter-jkl78                1/1     Running   0          2m
# prometheus-monitoring-kube-prometheus-prometheus-0        2/2     Running   0          2m

# Access Grafana (port-forward for testing)
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80

# Or expose via LoadBalancer
kubectl patch svc monitoring-grafana -n monitoring -p '{"spec": {"type": "LoadBalancer"}}'
```

### Custom Prometheus Metrics

```yaml
# servicemonitor.yaml — Tell Prometheus to scrape your app
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: webapp-metrics
  namespace: monitoring
  labels:
    release: monitoring    # Must match Prometheus selector
spec:
  namespaceSelector:
    matchNames:
    - production
  selector:
    matchLabels:
      app: webapp
  endpoints:
  - port: metrics
    path: /metrics
    interval: 15s
```

### Alerting Rules

```yaml
# alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: webapp-alerts
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
  - name: webapp.rules
    rules:
    - alert: HighCPUUsage
      expr: |
        sum(rate(container_cpu_usage_seconds_total{namespace="production", container="webapp"}[5m])) 
        / sum(kube_pod_container_resource_requests{namespace="production", container="webapp", resource="cpu"}) 
        > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage detected"
        description: "CPU usage is above 90% for 5 minutes"

    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total{namespace="production"}[15m]) > 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Pod {{ $labels.pod }} is crash looping"
        description: "Pod has restarted {{ $value }} times in the last 15 minutes"

    - alert: HighMemoryUsage
      expr: |
        container_memory_working_set_bytes{namespace="production", container="webapp"} 
        / container_spec_memory_limit_bytes{namespace="production", container="webapp"} 
        > 0.85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage on {{ $labels.pod }}"

    - alert: PodNotReady
      expr: kube_pod_status_ready{namespace="production", condition="true"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Pod {{ $labels.pod }} is not ready"
```

### AlertManager Configuration (Slack/PagerDuty)

```yaml
# alertmanager-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-monitoring-kube-prometheus-alertmanager
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
      slack_api_url: 'https://hooks.slack.com/services/T00/B00/XXXX'

    route:
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'slack-notifications'
      routes:
      - match:
          severity: critical
        receiver: 'pagerduty-critical'
      - match:
          severity: warning
        receiver: 'slack-notifications'

    receivers:
    - name: 'slack-notifications'
      slack_configs:
      - channel: '#k8s-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

    - name: 'pagerduty-critical'
      pagerduty_configs:
      - service_key: '<pagerduty-service-key>'
```

---

## 27.3 Managing Application Logs

### Logging in Docker

Docker containers write logs to standard output (stdout). When you run a container in the foreground, logs appear directly in your terminal:

```bash
docker run kodekloud/event-simulator
```

```
2024-01-15 10:00:01,937 - root - INFO - USER1 logged in
2024-01-15 10:00:02,943 - root - INFO - USER2 logged out
2024-01-15 10:00:03,944 - root - INFO - USER3 is viewing page3
2024-01-15 10:00:04,951 - root - INFO - USER4 is viewing page1
2024-01-15 10:00:05,954 - root - INFO - USER1 logged out
```

In detached mode (`-d`), logs don't appear on the terminal. Stream them with `docker logs`:

```bash
docker run -d kodekloud/event-simulator

# Stream logs from the detached container
docker logs -f <container_id>
```

### Logging in Kubernetes

The same container image deployed as a Kubernetes pod uses `kubectl logs` instead of `docker logs`:

```yaml
# event-simulator.yaml
apiVersion: v1
kind: Pod
metadata:
  name: event-simulator-pod
spec:
  containers:
  - name: event-simulator
    image: kodekloud/event-simulator
```

```bash
kubectl create -f event-simulator.yaml

# Stream logs in real-time (like tail -f)
kubectl logs -f event-simulator-pod
```

```
2024-01-15 10:00:01,937 - root - INFO - USER1 logged in
2024-01-15 10:00:02,943 - root - INFO - USER2 logged out
2024-01-15 10:00:03,944 - root - INFO - USER2 is viewing page2
2024-01-15 10:00:04,951 - root - INFO - USER3 is viewing page3
2024-01-15 10:00:05,095 - root - INFO - USER4 is viewing page1
```

**Useful `kubectl logs` flags:**

```bash
# View logs without streaming
kubectl logs event-simulator-pod

# Last 50 lines only
kubectl logs event-simulator-pod --tail=50

# Logs from the last hour
kubectl logs event-simulator-pod --since=1h

# Logs from a previous container instance (after a crash/restart)
kubectl logs event-simulator-pod --previous
```

### Logging with Multiple Containers

When a pod has multiple containers, you must specify the container name with `-c`:

```yaml
# multi-container-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: event-simulator-pod
spec:
  containers:
  - name: event-simulator
    image: kodekloud/event-simulator
  - name: image-processor
    image: some-image-processor
```

```bash
# Without -c flag — error
kubectl logs event-simulator-pod
```

```
error: a container name must be specified for pod event-simulator-pod,
choose one of: [event-simulator image-processor]
```

```bash
# Specify the container name
kubectl logs -f event-simulator-pod -c event-simulator
```

```
2024-01-15 10:00:01,937 - root - INFO - USER1 logged in
2024-01-15 10:00:02,943 - root - INFO - USER2 logged out
2024-01-15 10:00:03,944 - root - INFO - USER2 is viewing page2
```

### Lab: Troubleshooting with Application Logs

**Scenario 1: Diagnosing a login issue**

A user reports they cannot log in. Check the application pod logs:

```bash
kubectl get pods
```

```
NAME       READY   STATUS    RESTARTS   AGE
webapp-1   1/1     Running   0          110s
```

```bash
kubectl logs webapp-1 | grep -i "fail\|error\|warning"
```

```
[2024-01-15 10:05:58,923] WARNING in event-simulator: USER5 Failed to Login as the account is locked due to MANY FAILED ATTEMPTS.
[2024-01-15 10:06:14,961] WARNING in event-simulator: USER5 Failed to Login as the account is locked due to MANY FAILED ATTEMPTS.
```

Root cause: USER5's account is locked due to too many failed login attempts.

**Scenario 2: Diagnosing an order failure in a multi-container pod**

A user reports a failed purchase. The application runs in a pod with two containers:

```bash
kubectl get pods
```

```
NAME       READY   STATUS    RESTARTS   AGE
webapp-1   1/1     Running   0          110s
webapp-2   2/2     Running   0          9s
```

```bash
# Must specify the container name for multi-container pods
kubectl logs webapp-2
```

```
error: a container name must be specified for pod webapp-2, choose one of: [simple-webapp db]
```

```bash
# Check the web application container logs, filtering for warnings
kubectl logs webapp-2 -c simple-webapp | grep -i warning
```

```
[2024-01-15 10:07:26,775] WARNING in event-simulator: USER5 Failed to Login as the account is locked due to MANY FAILED ATTEMPTS.
[2024-01-15 10:07:36,789] WARNING in event-simulator: USER3 Order failed as the item is OUT OF STOCK.
[2024-01-15 10:07:39,796] WARNING in event-simulator: USER5 Failed to Login as the account is locked due to MANY FAILED ATTEMPTS.
```

Root cause: The order failure is not an authentication issue — the item is out of stock. The login warnings are a separate issue (USER5's locked account).

**Key takeaway:** When troubleshooting multi-container pods, always specify `-c <container-name>`. Use `grep` to filter for relevant log levels (`WARNING`, `ERROR`, `FATAL`) to quickly find the root cause among potentially thousands of log lines.

---

## 27.4 Logging with EFK/ELK Stack

### Fluent Bit (Lightweight Log Collector)

```bash
# Install Fluent Bit
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit \
  --namespace logging \
  --create-namespace \
  --set config.outputs="[OUTPUT]\n    Name cloudwatch_logs\n    Match *\n    region us-east-1\n    log_group_name /eks/my-cluster\n    log_stream_prefix fluent-bit-\n    auto_create_group true"
```

### AWS CloudWatch Container Insights

```bash
# Install CloudWatch agent
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonSet/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | \
  sed "s/{{cluster_name}}/my-k8s-cluster/;s/{{region_name}}/us-east-1/" | \
  kubectl apply -f -

# Verify
kubectl get pods -n amazon-cloudwatch

# Output:
# NAME                     READY   STATUS    RESTARTS   AGE
# cloudwatch-agent-abc12   1/1     Running   0          2m
# fluent-bit-def34         1/1     Running   0          2m
```

---

## 27.5 Monitoring Common Mistakes & Troubleshooting

### Common Monitoring Mistakes

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| Too many alerts (alert fatigue) | Team ignores alerts, misses real incidents | Prioritize by severity; group related alerts; use `for:` duration to filter transient spikes |
| Logs not collected from all pods | Missing visibility into failures | Check Fluent Bit/Promtail label selectors and namespace filters |
| Metrics missing for some pods | Gaps in dashboards and HPA decisions | Verify Prometheus scrape configs and ServiceMonitor selectors |
| One dashboard per microservice | Information overload, hard to correlate | Consolidate into app-focused views with variables |
| Alerting on raw spikes instead of rates | False positives from momentary spikes | Use `rate()` or `avg_over_time()` in PromQL, not raw values |
| No resource requests set | `kubectl top` and HPA show no data | Always set `resources.requests` — metrics-server needs them |

### Monitoring Troubleshooting Cheatsheet

| Symptom | What to Check |
|---------|--------------|
| Grafana shows "No Data" | Prometheus data source URL correct? Prometheus pods running? Scrape config matches target labels? |
| Logs missing from new pods | Promtail/Fluent Bit DaemonSet running on the node? Label selectors match the new pods? |
| Pod metrics blank in dashboard | metrics-server installed? `kubectl top pods` works? kube-state-metrics running? |
| Alerts not firing | Alertmanager running? Receiver config correct? Check for silences: Alertmanager UI → Silences |
| HPA shows `<unknown>` for metrics | metrics-server not installed, or pod has no `resources.requests` defined |
| Prometheus scrape targets "DOWN" | Target pod not exposing `/metrics` endpoint, or NetworkPolicy blocking Prometheus |

```bash
# Quick diagnostic commands
# 1. Check if metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# 2. Check if Prometheus can scrape targets
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring
# Open http://localhost:9090/targets — look for DOWN targets

# 3. Check Alertmanager status
kubectl port-forward svc/alertmanager-operated 9093:9093 -n monitoring
# Open http://localhost:9093/#/alerts

# 4. Check Fluent Bit / Promtail logs
kubectl logs -l app=fluent-bit -n logging --tail=50
kubectl logs -l app=promtail -n monitoring --tail=50

# 5. Verify a pod exposes metrics
kubectl exec -it <pod> -n <ns> -- curl -s localhost:<port>/metrics | head -20
```

### Monitoring Best Practices

- Alert on rates and percentages, not absolute numbers (`rate(errors[5m]) > 0.05` not `errors > 10`)
- Export Grafana dashboards as JSON and store in Git for version control
- Include release/version labels in logs to correlate issues with deployments
- Use LogQL/PromQL filters in dashboards to show errors over time
- Enable dashboards per team/service, not per tool
- Set up a "golden signals" dashboard (latency, traffic, errors, saturation) for every service

---

## 27.6 Useful Prometheus Queries (PromQL)

```promql
# CPU usage by pod
sum(rate(container_cpu_usage_seconds_total{namespace="production"}[5m])) by (pod)

# Memory usage by pod (in MB)
sum(container_memory_working_set_bytes{namespace="production"}) by (pod) / 1024 / 1024

# Request rate per service
sum(rate(http_requests_total{namespace="production"}[5m])) by (service)

# Error rate (5xx responses)
sum(rate(http_requests_total{namespace="production", status=~"5.."}[5m])) 
/ sum(rate(http_requests_total{namespace="production"}[5m])) * 100

# Pod restart count
sum(kube_pod_container_status_restarts_total{namespace="production"}) by (pod)

# Node CPU utilization
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Disk usage percentage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100
```

---

## 27.7 Module 7 Exercises

### Exercise 1: Helm
```bash
# 1. Create a Helm chart
helm create my-chart
# 2. Modify values.yaml (change image, replicas)
# 3. Install it
helm install test-release ./my-chart
# 4. Upgrade with different values
helm upgrade test-release ./my-chart --set replicaCount=5
# 5. Rollback
helm rollback test-release 1
# 6. Uninstall
helm uninstall test-release
```

### Exercise 2: Monitoring
```bash
# 1. Install Prometheus stack
# 2. Access Grafana dashboard
# 3. Import dashboard ID 6417 (Kubernetes Cluster)
# 4. Create a custom alert rule
# 5. Trigger the alert with a stress test
```

---

## 27.8 Loki — Lightweight Log Aggregation

The EFK stack (Elasticsearch + Fluent Bit + Kibana) is powerful but resource-heavy. Loki is a lightweight alternative designed to work natively with Grafana.

**EFK vs Loki comparison:**

| Feature | EFK Stack | Loki + Promtail |
|---------|-----------|-----------------|
| **Storage** | Full-text index (expensive) | Stores only labels + compressed chunks |
| **Query language** | KQL (Kibana) | LogQL (Grafana) |
| **Resource usage** | High (Elasticsearch needs 4-8GB RAM) | Low (runs on 512MB) |
| **Best for** | Large-scale search, compliance | Cost-effective log aggregation |
| **Integration** | Separate Kibana UI | Built into Grafana |

### Install Loki Stack

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Loki + Promtail (log collector agent)
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set grafana.enabled=false    # Use existing Grafana from kube-prometheus-stack
```

### How Promtail Works

Promtail runs as a DaemonSet on every node. It discovers containers via the Kubernetes API, reads their log files from `/var/log/pods/`, and ships them to Loki with labels attached.

```
┌─────────────────────────────────────────────────┐
│  Node                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  Pod A   │  │  Pod B   │  │  Pod C   │      │
│  │ stdout → │  │ stdout → │  │ stdout → │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │            │
│       ▼              ▼              ▼            │
│  /var/log/pods/*/*.log                           │
│       │                                          │
│  ┌────┴──────────────────────────────┐           │
│  │  Promtail (DaemonSet)             │           │
│  │  - Discovers pods via K8s API     │           │
│  │  - Reads log files                │           │
│  │  - Attaches labels (namespace,    │           │
│  │    pod, container, app)           │           │
│  │  - Ships to Loki                  │           │
│  └────┬──────────────────────────────┘           │
└───────┼──────────────────────────────────────────┘
        │
        ▼
   ┌─────────┐      ┌──────────┐
   │  Loki   │ ◄──► │ Grafana  │
   └─────────┘      └──────────┘
```

### Add Loki as Grafana Data Source

In Grafana → Configuration → Data Sources → Add data source:
- Type: **Loki**
- URL: `http://loki:3100`

### LogQL Queries

LogQL is Loki's query language. It filters logs by labels and content.

```bash
# All logs from a specific app
{app="webapp"}

# Filter for errors
{app="webapp"} |= "ERROR"

# Regex match for 5xx status codes
{container="nginx"} |~ "5[0-9]{2}"

# Exclude health check noise
{app="webapp"} != "/healthz"

# Parse JSON logs and filter by field
{app="webapp"} | json | level="error"

# Count errors per minute (metric query)
rate({app="webapp"} |= "ERROR" [1m])

# Top 5 namespaces by log volume
topk(5, sum by (namespace) (rate({job="promtail"} [5m])))
```

**Sample output in Grafana Explore:**

```
2024-01-15 10:23:45  {app="webapp", namespace="prod", pod="webapp-7d8f9-abc12"}
  ERROR: Connection refused to database at postgres:5432

2024-01-15 10:23:46  {app="webapp", namespace="prod", pod="webapp-7d8f9-abc12"}
  ERROR: Retry 1/3 failed — connection timeout

2024-01-15 10:23:50  {app="webapp", namespace="prod", pod="webapp-7d8f9-abc12"}
  INFO: Database connection restored
```

### When to Use Loki vs EFK

| Scenario | Use Loki | Use EFK |
|----------|----------|---------|
| Small/medium clusters | ✅ | Overkill |
| Already using Grafana | ✅ | Separate UI |
| Full-text search across millions of logs | Limited | ✅ |
| Compliance requiring long-term indexed search | Limited | ✅ |
| Cost-sensitive environments | ✅ | Expensive |

---

## 27.9 SRE Practices — SLIs, SLOs, and Operational Readiness

### SLIs, SLOs, and SLAs

Site Reliability Engineering (SRE) uses measurable indicators to define and track service reliability.

| Term | Definition | Example |
|------|-----------|---------|
| **SLI** (Service Level Indicator) | A metric that measures service behavior | 99.2% of requests complete in <300ms |
| **SLO** (Service Level Objective) | A target value for an SLI | "99.9% of requests succeed within 500ms" |
| **SLA** (Service Level Agreement) | A contract with consequences if SLO is missed | "99.95% uptime or customer gets credits" |
| **Error Budget** | The allowed amount of unreliability (100% - SLO) | SLO = 99.9% → error budget = 0.1% downtime/month (~43 min) |

**Relationship:**

```
SLI (what you measure)
  → SLO (what you target)
    → SLA (what you promise)
      → Error Budget (how much failure you can tolerate)
```

### The Four Golden Signals

Google's SRE book defines four signals every service should monitor:

| Signal | What It Measures | Prometheus Metric Example |
|--------|-----------------|--------------------------|
| **Latency** | Time to serve a request | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| **Traffic** | Demand on the system | `sum(rate(http_requests_total[5m]))` |
| **Errors** | Rate of failed requests | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` |
| **Saturation** | How full the system is | `container_memory_usage_bytes / container_spec_memory_limit_bytes` |

### Defining SLOs in Prometheus

```yaml
# slo-alerting-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: slo-alerts
  namespace: monitoring
spec:
  groups:
  - name: slo.rules
    rules:
    # SLI: Error rate
    - record: sli:http_error_rate:ratio_rate5m
      expr: |
        sum(rate(http_requests_total{status=~"5.."}[5m]))
        /
        sum(rate(http_requests_total[5m]))

    # Alert when error budget is being consumed too fast
    # SLO: 99.9% success rate → error budget = 0.1%
    - alert: ErrorBudgetBurnRate
      expr: sli:http_error_rate:ratio_rate5m > 0.001
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Error rate exceeds SLO ({{ $value | humanizePercentage }})"
        description: "Error budget is being consumed. Current error rate: {{ $value }}"

    # SLI: Latency (p99 > 500ms)
    - alert: LatencySLOBreach
      expr: |
        histogram_quantile(0.99,
          sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
        ) > 0.5
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "P99 latency exceeds 500ms SLO"
```

### Error Budget Tracking

```
Monthly error budget calculation:
─────────────────────────────────
SLO = 99.9% availability
Month = 30 days = 43,200 minutes

Error budget = 0.1% × 43,200 = 43.2 minutes of downtime allowed

Week 1: 5 min downtime  → 38.2 min remaining
Week 2: 0 min downtime  → 38.2 min remaining
Week 3: 30 min downtime → 8.2 min remaining  ← slow down deployments
Week 4: 2 min downtime  → 6.2 min remaining  ✅ SLO met
```

When the error budget is nearly exhausted, teams should freeze feature deployments and focus on reliability work.

### Runbooks

A runbook is a documented procedure for handling a specific operational scenario. Every alert should link to a runbook.

**Runbook template:**

```markdown
## Runbook: High Pod Restart Count

**Alert:** PodCrashLooping
**Severity:** Warning → Critical (if >10 restarts in 30 min)
**Owner:** Platform team

### Symptoms
- Pod restart count increasing
- Alertmanager fires PodCrashLooping alert

### Diagnosis Steps
1. Check pod status:
   kubectl get pods -n <namespace> | grep <pod-name>

2. Check events:
   kubectl describe pod <pod-name> -n <namespace> | tail -20

3. Check previous container logs:
   kubectl logs <pod-name> -n <namespace> --previous

4. Check resource limits (OOMKilled?):
   kubectl describe pod <pod-name> | grep -A5 "Last State"

### Common Causes & Fixes
| Cause | Fix |
|-------|-----|
| OOMKilled | Increase memory limits |
| App crash on startup | Check logs for stack trace, fix code |
| Failed liveness probe | Increase initialDelaySeconds or timeoutSeconds |
| Missing ConfigMap/Secret | Verify ConfigMap/Secret exists in namespace |
| Image pull failure | Check image tag and pull secrets |

### Escalation
If not resolved in 30 minutes → page on-call SRE via PagerDuty
```

### Incident Response

**Incident lifecycle:**

```
Detection → Triage → Mitigation → Resolution → Postmortem
    │          │          │            │             │
 Alerts    Severity    Stop the     Fix root      Document
 fire      assigned    bleeding     cause         learnings
```

**Incident severity levels:**

| Level | Definition | Response Time | Example |
|-------|-----------|---------------|---------|
| **SEV1** | Service down, all users affected | Immediate (page on-call) | API returning 500 for all requests |
| **SEV2** | Degraded service, partial impact | 15 minutes | Latency spike, some requests failing |
| **SEV3** | Minor issue, workaround exists | 1 hour | One replica down, others serving traffic |
| **SEV4** | Cosmetic or non-urgent | Next business day | Dashboard metric not updating |

**Incident roles:**

| Role | Responsibility |
|------|---------------|
| **Incident Commander** | Coordinates response, makes decisions |
| **Communications Lead** | Updates stakeholders, status page |
| **Operations Lead** | Executes fixes, runs commands |
| **Scribe** | Timestamps all actions in incident channel |

### Blameless Postmortems

After every SEV1/SEV2 incident, write a postmortem. The goal is learning, not blame.

**Postmortem template:**

```markdown
## Postmortem: API Outage — 2024-01-15

**Duration:** 10:23 AM - 10:52 AM UTC (29 minutes)
**Impact:** 100% of API requests failed for 29 minutes
**Severity:** SEV1

### Timeline
- 10:23 — Alertmanager fires HighErrorRate alert
- 10:25 — On-call engineer acknowledges, begins investigation
- 10:28 — Root cause identified: database connection pool exhausted
- 10:35 — Mitigation: scaled database replicas from 2 to 5
- 10:42 — Connection pool recovered, error rate dropping
- 10:52 — All metrics normal, incident resolved

### Root Cause
A batch job ran during peak hours, consuming all available
database connections. The application had no connection timeout
configured, so requests queued indefinitely.

### What Went Well
- Alert fired within 2 minutes of impact
- On-call responded within 5 minutes
- Runbook for database issues was up to date

### What Went Wrong
- Batch job was not scheduled for off-peak hours
- No connection pool limit configured in the application
- No PodDisruptionBudget on database pods

### Action Items
| Action | Owner | Due Date |
|--------|-------|----------|
| Move batch job to 2 AM UTC | Backend team | 2024-01-22 |
| Add connection pool timeout (30s) | Backend team | 2024-01-19 |
| Add PDB for database StatefulSet | Platform team | 2024-01-19 |
| Add connection pool saturation alert | SRE team | 2024-01-22 |
```

### Cost Optimization

Kubernetes can waste resources if pods request more than they use.

**Tools for cost visibility:**

| Tool | Type | What It Shows |
|------|------|--------------|
| **OpenCost** | Open-source | Real-time cost per namespace, deployment, label |
| **Kubecost** | Commercial (free tier) | Cost allocation, savings recommendations |
| **kubectl top** | Built-in | Current CPU/memory usage vs requests |

**Install OpenCost:**

```bash
helm install opencost opencost/opencost \
  --namespace opencost \
  --create-namespace
```

**Common cost optimization techniques:**

```bash
# Find pods requesting more resources than they use
kubectl top pods -n production --sort-by=cpu

# Example output:
# NAME                      CPU(cores)   MEMORY(bytes)
# webapp-7d8f9-abc12        50m          128Mi      ← requests 500m CPU, 512Mi memory
# worker-5c6d7-def34        200m         256Mi      ← requests 250m CPU, 512Mi memory
```

| Technique | Savings | Risk |
|-----------|---------|------|
| Right-size pod requests/limits | 20-40% | Under-provisioning causes OOMKill |
| Use Spot/Preemptible instances for stateless workloads | Up to 90% | Pods can be evicted with 2-min warning |
| Cluster Autoscaler (scale down idle nodes) | 15-30% | Scale-up latency during traffic spikes |
| Delete unused PVCs and LoadBalancers | Variable | Data loss if PVC is still needed |
| Use HPA to scale down during off-peak | 10-25% | Cold start latency |

> **Cross-reference:** HPA/VPA/Cluster Autoscaler → MODULE-20; Spot Instances → MODULE-09

---

**Next Module: Real-World Industry Projects →**
