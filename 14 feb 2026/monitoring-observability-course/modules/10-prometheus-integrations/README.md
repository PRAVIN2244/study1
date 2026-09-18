# Module 10 — Prometheus Integrations

**Levels:** Beginner → Advanced  
**Duration:** ~18 hours  
**Prerequisites:** Module 2 (Prometheus), Module 9 (DORA Metrics)

---

## 10.A Prometheus + Kubernetes

### How It Works

Prometheus uses Kubernetes service discovery to auto-discover pods, services, and nodes. No static target configuration needed.

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ kube-state-  │  │ node-        │  │ cAdvisor     │  │
│  │ metrics      │  │ exporter     │  │ (kubelet)    │  │
│  │              │  │              │  │              │  │
│  │ K8s object   │  │ Node CPU,    │  │ Container    │  │
│  │ states       │  │ memory, disk │  │ CPU, memory  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│  ┌──────▼─────────────────▼─────────────────▼────────┐  │
│  │                  Prometheus                       │  │
│  │  (kubernetes_sd_config: node, pod, service,       │  │
│  │   endpoints, ingress)                             │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │                  Grafana                          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Deploying Prometheus with Helm

```bash
# Add Prometheus community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager + exporters)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=15d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi \
  --set grafana.adminPassword=admin \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=10Gi
```

This installs:
- **Prometheus Operator** — manages Prometheus instances via CRDs.
- **Prometheus** — metrics collection and alerting.
- **Alertmanager** — alert routing and notification.
- **Grafana** — dashboards (pre-configured with K8s dashboards).
- **kube-state-metrics** — Kubernetes object state metrics.
- **node-exporter** — node-level system metrics.

### Components in Detail

#### kube-state-metrics

Exposes the state of Kubernetes objects as Prometheus metrics.

| Metric | Description |
|--------|-------------|
| `kube_pod_status_phase` | Pod phase (Pending, Running, Failed, Succeeded) |
| `kube_pod_container_status_restarts_total` | Container restart count |
| `kube_deployment_spec_replicas` | Desired replicas |
| `kube_deployment_status_replicas_available` | Available replicas |
| `kube_node_status_condition` | Node conditions (Ready, MemoryPressure, DiskPressure) |
| `kube_hpa_status_current_replicas` | HPA current replicas |
| `kube_hpa_spec_max_replicas` | HPA max replicas |
| `kube_job_status_succeeded` | Job completion status |
| `kube_namespace_status_phase` | Namespace phase |

#### node-exporter

Runs as a DaemonSet on every node.

| Metric | Description |
|--------|-------------|
| `node_cpu_seconds_total` | CPU time per mode |
| `node_memory_MemAvailable_bytes` | Available memory |
| `node_filesystem_avail_bytes` | Available disk space |
| `node_network_receive_bytes_total` | Network bytes received |
| `node_disk_io_time_seconds_total` | Disk I/O time |

#### cAdvisor (built into kubelet)

| Metric | Description |
|--------|-------------|
| `container_cpu_usage_seconds_total` | Container CPU usage |
| `container_memory_usage_bytes` | Container memory usage |
| `container_memory_working_set_bytes` | Container memory working set (used for OOM decisions) |
| `container_network_receive_bytes_total` | Container network received |
| `container_fs_usage_bytes` | Container filesystem usage |

### ServiceMonitor and PodMonitor

The Prometheus Operator uses CRDs to configure scraping.

#### ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: payment-api
  namespace: monitoring
  labels:
    release: monitoring  # Must match Prometheus operator selector
spec:
  namespaceSelector:
    matchNames:
      - production
  selector:
    matchLabels:
      app: payment-api
  endpoints:
    - port: metrics        # Name of the Service port
      interval: 15s
      path: /metrics
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_label_version]
          targetLabel: version
```

#### PodMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: batch-jobs
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
      - batch
  selector:
    matchLabels:
      app: batch-processor
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
```

### RBAC Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources: ["nodes", "nodes/proxy", "nodes/metrics", "services", "endpoints", "pods"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions", "networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch"]
  - nonResourceURLs: ["/metrics", "/metrics/cadvisor"]
    verbs: ["get"]
```

### Key PromQL Queries for Kubernetes

```promql
# Pod CPU usage (cores)
sum(rate(container_cpu_usage_seconds_total{namespace="production", container!=""}[5m])) by (pod)

# Pod memory usage (bytes)
sum(container_memory_working_set_bytes{namespace="production", container!=""}) by (pod)

# Pod restart rate
increase(kube_pod_container_status_restarts_total{namespace="production"}[1h])

# Pods not ready
kube_pod_status_phase{phase=~"Pending|Failed|Unknown"} == 1

# Deployment rollout stuck
kube_deployment_status_replicas_available / kube_deployment_spec_replicas < 1

# Node CPU usage
100 - (avg by(node) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Node memory pressure
kube_node_status_condition{condition="MemoryPressure", status="true"} == 1

# HPA at max capacity
kube_hpa_status_current_replicas == kube_hpa_spec_max_replicas

# Container OOM kills
increase(kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}[1h])
```

### Advanced: Control Plane Monitoring

```yaml
# Monitor etcd
- job_name: "etcd"
  scheme: https
  tls_config:
    ca_file: /etc/kubernetes/pki/etcd/ca.crt
    cert_file: /etc/kubernetes/pki/etcd/server.crt
    key_file: /etc/kubernetes/pki/etcd/server.key
  static_configs:
    - targets: ["etcd-1:2379", "etcd-2:2379", "etcd-3:2379"]
```

| Component | Key Metrics |
|-----------|------------|
| **etcd** | `etcd_server_has_leader`, `etcd_disk_wal_fsync_duration_seconds`, `etcd_mvcc_db_total_size_in_bytes` |
| **API Server** | `apiserver_request_total`, `apiserver_request_duration_seconds`, `apiserver_current_inflight_requests` |
| **Scheduler** | `scheduler_schedule_attempts_total`, `scheduler_scheduling_duration_seconds` |
| **Controller Manager** | `workqueue_depth`, `workqueue_adds_total`, `workqueue_retries_total` |

### Remote Write to Thanos

```yaml
# Prometheus values for Helm
prometheus:
  prometheusSpec:
    externalLabels:
      cluster: production-us-east-1
    remoteWrite:
      - url: http://thanos-receive:19291/api/v1/receive
        writeRelabelConfigs:
          - sourceLabels: [__name__]
            regex: "go_.*"
            action: drop
```

---

## 10.B Prometheus + AWS

### Options for AWS Monitoring with Prometheus

| Approach | What It Monitors | How |
|----------|-----------------|-----|
| **node-exporter on EC2** | Host-level metrics | Agent on each instance |
| **CloudWatch Exporter** | Any CloudWatch metric | Polls CloudWatch API |
| **YACE (Yet Another CloudWatch Exporter)** | CloudWatch metrics (more efficient) | Polls CloudWatch API with auto-discovery |
| **EKS native** | Kubernetes + AWS | Prometheus in EKS cluster |

### CloudWatch Exporter Setup

```bash
docker run -d \
  --name cloudwatch-exporter \
  -p 9106:9106 \
  -v $(pwd)/cloudwatch-config.yml:/config/config.yml \
  -e AWS_ACCESS_KEY_ID=<key> \
  -e AWS_SECRET_ACCESS_KEY=<secret> \
  prom/cloudwatch-exporter
```

#### Configuration

```yaml
# cloudwatch-config.yml
region: us-east-1
metrics:
  # EC2 metrics
  - aws_namespace: AWS/EC2
    aws_metric_name: CPUUtilization
    aws_dimensions: [InstanceId]
    aws_statistics: [Average]
    period_seconds: 300

  # RDS metrics
  - aws_namespace: AWS/RDS
    aws_metric_name: CPUUtilization
    aws_dimensions: [DBInstanceIdentifier]
    aws_statistics: [Average]

  - aws_namespace: AWS/RDS
    aws_metric_name: DatabaseConnections
    aws_dimensions: [DBInstanceIdentifier]
    aws_statistics: [Sum]

  - aws_namespace: AWS/RDS
    aws_metric_name: FreeStorageSpace
    aws_dimensions: [DBInstanceIdentifier]
    aws_statistics: [Average]

  # ELB metrics
  - aws_namespace: AWS/ELB
    aws_metric_name: RequestCount
    aws_dimensions: [LoadBalancerName]
    aws_statistics: [Sum]

  - aws_namespace: AWS/ELB
    aws_metric_name: Latency
    aws_dimensions: [LoadBalancerName]
    aws_statistics: [Average, p99]

  # EBS metrics
  - aws_namespace: AWS/EBS
    aws_metric_name: VolumeReadOps
    aws_dimensions: [VolumeId]
    aws_statistics: [Sum]

  - aws_namespace: AWS/EBS
    aws_metric_name: VolumeWriteOps
    aws_dimensions: [VolumeId]
    aws_statistics: [Sum]
```

#### IAM Role for Prometheus

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "tag:GetResources",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: "cloudwatch"
    static_configs:
      - targets: ["cloudwatch-exporter:9106"]
    scrape_interval: 300s  # Match CloudWatch period
    scrape_timeout: 120s   # CloudWatch API can be slow
```

### YACE (Recommended for Production)

YACE is more efficient than the official CloudWatch exporter — it supports auto-discovery and parallel API calls.

```yaml
# yace-config.yml
discovery:
  jobs:
    - type: ec2
      regions: [us-east-1]
      period: 300
      length: 300
      metrics:
        - name: CPUUtilization
          statistics: [Average]
        - name: NetworkIn
          statistics: [Sum]
        - name: NetworkOut
          statistics: [Sum]

    - type: rds
      regions: [us-east-1]
      period: 300
      length: 300
      metrics:
        - name: CPUUtilization
          statistics: [Average]
        - name: DatabaseConnections
          statistics: [Sum]
        - name: ReadLatency
          statistics: [Average]
        - name: ReplicaLag
          statistics: [Maximum]
```

### Key PromQL Queries for AWS

```promql
# EC2 CPU utilization
aws_ec2_cpuutilization_average{instance_id=~"i-.*"}

# RDS connections approaching limit
aws_rds_database_connections_sum / aws_rds_max_connections * 100

# ELB error rate
rate(aws_elb_httpcode_backend_5xx_sum[5m]) / rate(aws_elb_request_count_sum[5m])

# EBS IOPS
rate(aws_ebs_volume_read_ops_sum[5m]) + rate(aws_ebs_volume_write_ops_sum[5m])
```

---

## 10.C Prometheus + Jenkins

### Setup

#### 1. Install Jenkins Prometheus Plugin

- **Manage Jenkins → Plugins → Available → Search "Prometheus"**.
- Install **Prometheus Metrics Plugin**.
- Restart Jenkins.

The plugin exposes metrics at `http://jenkins:8080/prometheus/`.

#### 2. Add Scrape Config

```yaml
scrape_configs:
  - job_name: "jenkins"
    metrics_path: /prometheus/
    static_configs:
      - targets: ["jenkins:8080"]
    # If Jenkins requires auth
    basic_auth:
      username: prometheus
      password: <token>
```

### Available Metrics

| Metric | Description |
|--------|-------------|
| `jenkins_builds_total` | Total builds by job and result |
| `jenkins_builds_duration_milliseconds_summary` | Build duration distribution |
| `jenkins_builds_last_build_duration_milliseconds` | Last build duration |
| `jenkins_builds_last_build_result` | Last build result (1=success, 0=failure) |
| `jenkins_builds_failed_total` | Failed builds count |
| `jenkins_builds_success_total` | Successful builds count |
| `jenkins_queue_size` | Build queue length |
| `jenkins_queue_waiting_duration_seconds` | Time jobs wait in queue |
| `jenkins_executors_available` | Available executors |
| `jenkins_executors_busy` | Busy executors |
| `jenkins_node_online` | Node online status |
| `jenkins_plugins_active` | Active plugin count |
| `jenkins_uptime` | Jenkins uptime (seconds) |

### Key PromQL Queries

```promql
# Build success rate (24h)
sum(increase(jenkins_builds_success_total[24h])) /
sum(increase(jenkins_builds_total[24h]))

# Average build duration by job
avg(jenkins_builds_duration_milliseconds_summary{quantile="0.5"}) by (jenkins_job)

# Queue wait time (P95)
histogram_quantile(0.95, rate(jenkins_queue_waiting_duration_seconds_bucket[1h]))

# Executor utilization
jenkins_executors_busy / (jenkins_executors_busy + jenkins_executors_available) * 100

# Failed builds in last hour
increase(jenkins_builds_failed_total[1h])

# Build frequency by job (per day)
increase(jenkins_builds_total[1d])
```

### Alert Rules for Jenkins

```yaml
groups:
  - name: jenkins_alerts
    rules:
      - alert: JenkinsBuildQueueHigh
        expr: jenkins_queue_size > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Jenkins build queue has {{ $value }} items"

      - alert: JenkinsExecutorSaturation
        expr: jenkins_executors_busy / (jenkins_executors_busy + jenkins_executors_available) > 0.9
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Jenkins executor utilization is {{ $value | humanizePercentage }}"

      - alert: JenkinsHighFailureRate
        expr: |
          sum(increase(jenkins_builds_failed_total[1h])) /
          sum(increase(jenkins_builds_total[1h])) > 0.3
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Jenkins build failure rate is {{ $value | humanizePercentage }}"

      - alert: JenkinsNodeOffline
        expr: jenkins_node_online == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Jenkins node {{ $labels.node }} is offline"
```

---

## Exercises

### Prometheus + Kubernetes

1. Deploy kube-prometheus-stack with Helm. Verify all components are running.
2. Create a ServiceMonitor for a custom application. Verify metrics appear in Prometheus.
3. Write PromQL queries for: pod restarts, deployment rollout status, node memory pressure, HPA utilization.
4. Set up alerts for: pod CrashLoopBackOff, node not ready, deployment replicas unavailable.
5. (Advanced) Monitor etcd and API server. Create a control plane health dashboard.

### Prometheus + AWS

1. Deploy the CloudWatch exporter. Configure it for EC2, RDS, and ELB metrics.
2. Create recording rules for AWS Golden Signals (latency, traffic, errors, saturation).
3. Set up alerts for: RDS CPU > 80%, ELB 5xx rate > 1%, EBS IOPS near limit.
4. (Advanced) Use YACE with auto-discovery. Compare API call costs with the standard exporter.

### Prometheus + Jenkins

1. Install the Prometheus plugin on Jenkins. Verify metrics at `/prometheus/`.
2. Create a Jenkins health dashboard: build success rate, queue time, executor utilization.
3. Set up alerts for: high queue size, executor saturation, high failure rate.
4. Integrate Jenkins metrics with DORA metrics from Module 9. Build a unified delivery performance dashboard.

---

## Next Module

→ [Module 11 — Grafana Integrations](../11-grafana-integrations/README.md)
