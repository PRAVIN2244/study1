# Module 11 — Grafana Integrations

**Levels:** Beginner → Advanced  
**Duration:** ~12 hours  
**Prerequisites:** Module 3 (Grafana), Module 10 (Prometheus Integrations)

---

## 11.A Grafana + Kubernetes

### Setup

When using kube-prometheus-stack (Module 10), Grafana is pre-configured with:
- Prometheus data source connected.
- 30+ Kubernetes dashboards pre-loaded.
- Alerting rules for common K8s failure modes.

#### Accessing Grafana in Kubernetes

```bash
# Port-forward (development)
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

# Or expose via Ingress
```

### Pre-Built Kubernetes Dashboards

| Dashboard | ID | What It Shows |
|-----------|----|--------------|
| Kubernetes / Compute Resources / Cluster | 3119 | Cluster-wide CPU, memory, network |
| Kubernetes / Compute Resources / Namespace | 12740 | Per-namespace resource usage |
| Kubernetes / Compute Resources / Pod | 6417 | Per-pod CPU, memory, network |
| Kubernetes / Networking / Cluster | 12124 | Cluster network traffic |
| Node Exporter Full | 1860 | Detailed node metrics |
| CoreDNS | 5926 | DNS query rate, latency, errors |
| etcd | 3070 | etcd cluster health |

#### Importing Dashboards

```bash
# Via Grafana UI
# Dashboards → Import → Enter dashboard ID → Load → Select data source → Import

# Via provisioning (recommended for GitOps)
```

### Custom Kubernetes Dashboard

Build a dashboard focused on application health:

```
┌─────────────────────────────────────────────────────────────┐
│  Application Health — $namespace / $deployment              │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Status                                              │
│  [Pods Ready]  [Restarts/hr]  [OOM Kills]  [HPA Status]    │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Resources                                           │
│  [CPU Usage vs Request vs Limit]  [Memory Usage vs Limit]   │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Application                                         │
│  [Request Rate]  [Error Rate]  [P99 Latency]               │
├─────────────────────────────────────────────────────────────┤
│  Row 4: Network                                             │
│  [Network Rx/Tx]  [TCP Connections]                         │
├─────────────────────────────────────────────────────────────┤
│  Row 5: Events                                              │
│  [Kubernetes Events Table: warnings, errors]                │
└─────────────────────────────────────────────────────────────┘
```

#### Variables

```
namespace: label_values(kube_pod_info, namespace)
deployment: label_values(kube_deployment_labels{namespace="$namespace"}, deployment)
pod: label_values(kube_pod_info{namespace="$namespace", created_by_name=~"$deployment.*"}, pod)
```

#### Key Panel Queries

```promql
# Pods ready vs desired
kube_deployment_status_replicas_available{namespace="$namespace", deployment="$deployment"}
/
kube_deployment_spec_replicas{namespace="$namespace", deployment="$deployment"}

# CPU usage vs request
sum(rate(container_cpu_usage_seconds_total{namespace="$namespace", pod=~"$deployment.*", container!=""}[5m])) by (pod)
# Overlay with:
sum(kube_pod_container_resource_requests{namespace="$namespace", pod=~"$deployment.*", resource="cpu"}) by (pod)

# Memory usage vs limit
sum(container_memory_working_set_bytes{namespace="$namespace", pod=~"$deployment.*", container!=""}) by (pod)
# Overlay with:
sum(kube_pod_container_resource_limits{namespace="$namespace", pod=~"$deployment.*", resource="memory"}) by (pod)
```

---

## 11.B Grafana + AWS

### Data Source Options

| Data Source | What It Queries | Setup |
|-------------|----------------|-------|
| **CloudWatch** | Native AWS metrics and logs | IAM role or access keys |
| **Prometheus** | AWS metrics via CloudWatch exporter | Prometheus data source |
| **Elasticsearch** | AWS logs in OpenSearch | Elasticsearch data source |
| **X-Ray** | AWS distributed traces | X-Ray data source plugin |

### CloudWatch Data Source Setup

#### IAM Role (Recommended)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarmsForMetric",
        "cloudwatch:DescribeAlarmHistory",
        "cloudwatch:DescribeAlarms",
        "cloudwatch:ListMetrics",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetInsightRuleReport",
        "logs:DescribeLogGroups",
        "logs:GetLogGroupFields",
        "logs:StartQuery",
        "logs:StopQuery",
        "logs:GetQueryResults",
        "logs:GetLogEvents",
        "ec2:DescribeTags",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "tag:GetResources"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Configuration in Grafana

1. **Configuration → Data Sources → Add → CloudWatch**.
2. **Authentication:** Select "AWS SDK Default" (uses IAM role) or enter access keys.
3. **Default Region:** `us-east-1`.
4. **Namespaces:** Leave empty to auto-discover.

### AWS Dashboard Examples

#### EC2 Overview

| Panel | Metric | Namespace | Statistic |
|-------|--------|-----------|-----------|
| CPU Utilization | `CPUUtilization` | `AWS/EC2` | Average |
| Network In/Out | `NetworkIn`, `NetworkOut` | `AWS/EC2` | Sum |
| Status Checks | `StatusCheckFailed` | `AWS/EC2` | Maximum |
| Disk IOPS | `DiskReadOps`, `DiskWriteOps` | `AWS/EC2` | Sum |

#### Lambda Overview

| Panel | Metric | Statistic |
|-------|--------|-----------|
| Invocations | `Invocations` | Sum |
| Errors | `Errors` | Sum |
| Duration | `Duration` | Average, p99 |
| Throttles | `Throttles` | Sum |
| Concurrent Executions | `ConcurrentExecutions` | Maximum |
| Cold Starts | `Duration` (filter first invocation) | Average |

#### RDS Overview

| Panel | Metric | Statistic |
|-------|--------|-----------|
| CPU | `CPUUtilization` | Average |
| Connections | `DatabaseConnections` | Sum |
| Free Storage | `FreeStorageSpace` | Average |
| Read/Write Latency | `ReadLatency`, `WriteLatency` | Average |
| Replica Lag | `ReplicaLag` | Maximum |
| IOPS | `ReadIOPS`, `WriteIOPS` | Average |

#### ALB Overview

| Panel | Metric | Statistic |
|-------|--------|-----------|
| Request Count | `RequestCount` | Sum |
| Target Response Time | `TargetResponseTime` | Average, p99 |
| HTTP 5xx | `HTTPCode_ELB_5XX_Count` | Sum |
| Healthy Hosts | `HealthyHostCount` | Minimum |
| Active Connections | `ActiveConnectionCount` | Sum |

### CloudWatch Logs in Grafana

```sql
-- Query CloudWatch Logs directly from Grafana
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) by bin(5m)
```

### Multi-Account AWS Dashboards

Use Grafana's CloudWatch data source with **Assume Role ARN** to query metrics from multiple AWS accounts:

```
Data Source 1: CloudWatch (Account A - Production)
  → Assume Role: arn:aws:iam::111111111111:role/GrafanaReadOnly

Data Source 2: CloudWatch (Account B - Staging)
  → Assume Role: arn:aws:iam::222222222222:role/GrafanaReadOnly
```

Use a variable to switch between accounts or show both on the same dashboard.

---

## 11.C Grafana + Jenkins

### Data Flow

```
Jenkins → Prometheus Plugin → Prometheus → Grafana
```

Grafana visualizes Jenkins metrics collected by Prometheus (configured in Module 10.C).

### Jenkins Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  Jenkins CI/CD — Overview                                   │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Health (Stat panels)                                │
│  [Build Success Rate]  [Queue Size]  [Executor Usage]       │
│  [24h]                 [current]     [current %]            │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Build Trends (Time Series)                          │
│  [Builds per Hour — success/failure]  [Build Duration P50]  │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Pipeline Performance (Time Series)                  │
│  [Queue Wait Time]  [Executor Utilization Over Time]        │
├─────────────────────────────────────────────────────────────┤
│  Row 4: DORA Metrics (from Module 9)                        │
│  [Deploy Frequency]  [Lead Time]  [Change Failure Rate]     │
├─────────────────────────────────────────────────────────────┤
│  Row 5: Job Details (Table)                                 │
│  [Job Name | Last Build | Duration | Result | Trend]        │
└─────────────────────────────────────────────────────────────┘
```

### Key Panel Queries

```promql
# Build success rate (24h) — Stat panel
sum(increase(jenkins_builds_success_total[24h])) /
sum(increase(jenkins_builds_total[24h]))

# Builds per hour — Time series (stacked)
sum(increase(jenkins_builds_success_total[1h]))  # Green
sum(increase(jenkins_builds_failed_total[1h]))   # Red

# Build duration trend — Time series
jenkins_builds_duration_milliseconds_summary{quantile="0.5"} / 1000

# Queue wait time — Time series
histogram_quantile(0.95, rate(jenkins_queue_waiting_duration_seconds_bucket[1h]))

# Executor utilization — Gauge
jenkins_executors_busy / (jenkins_executors_busy + jenkins_executors_available) * 100
```

### DORA Dashboard Integration

Combine Jenkins pipeline metrics with deployment and incident data:

```promql
# Deployment frequency (from Jenkins deploys)
sum(increase(jenkins_builds_success_total{jenkins_job=~".*deploy.*production.*"}[7d]))

# Lead time (from commit to deploy completion)
histogram_quantile(0.50, rate(dora_lead_time_seconds_bucket[7d]))

# Change failure rate
sum(increase(dora_deployment_outcomes_total{outcome="failure"}[30d])) /
sum(increase(dora_deployment_outcomes_total[30d]))
```

### Deployment Annotations

Mark deployments on all Grafana dashboards:

```bash
# Call from Jenkins post-deploy step
curl -X POST http://grafana:3000/api/annotations \
  -H "Authorization: Bearer <grafana-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "time": '"$(date +%s%3N)"',
    "tags": ["deployment", "'"${SERVICE_NAME}"'", "'"${BUILD_TAG}"'"],
    "text": "Deployed '"${SERVICE_NAME}"' v'"${VERSION}"' (Build #'"${BUILD_NUMBER}"')"
  }'
```

Annotations appear as vertical lines on time series panels, making it easy to correlate deployments with metric changes.

---

## Exercises

### Grafana + Kubernetes

1. Import 3 pre-built Kubernetes dashboards. Customize one with additional panels.
2. Build a custom application health dashboard with variables for namespace and deployment.
3. Create data links from the cluster overview dashboard to the pod detail dashboard.
4. Set up Grafana alerts for: pod restarts > 5/hour, deployment replicas < desired.

### Grafana + AWS

1. Configure the CloudWatch data source. Create dashboards for EC2, RDS, and Lambda.
2. Build a unified dashboard showing ALB metrics alongside application metrics from Prometheus.
3. Use CloudWatch Logs Insights queries in Grafana panels.
4. (Advanced) Set up multi-account dashboards using Assume Role.

### Grafana + Jenkins

1. Create a Jenkins CI/CD dashboard with build success rate, queue time, and executor utilization.
2. Add DORA metric panels to the Jenkins dashboard.
3. Set up deployment annotations from Jenkins pipeline. Verify they appear on application dashboards.
4. Create a data link from a deployment annotation to the Jenkins build page.

---

## Next Module

→ [Module 12 — Datadog Integrations](../12-datadog-integrations/README.md)
