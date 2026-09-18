# Module 2 — Prometheus

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~20 hours  
**Prerequisites:** Module 1 (Observability Foundations)

---

## Level 1: Beginner

### 2.1 Prometheus Architecture

#### Components

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Targets     │────▶│  Prometheus  │────▶│  Alertmanager   │
│  (Exporters) │pull │  Server      │push │                 │
└─────────────┘     │              │     └────────┬────────┘
                    │  TSDB        │              │
                    │  Rule Engine │         Email/Slack/
                    │  HTTP Server │         PagerDuty
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Grafana    │
                    │  (query)     │
                    └──────────────┘
```

| Component | Role |
|-----------|------|
| **Prometheus Server** | Scrapes targets, stores time series, evaluates rules, serves queries |
| **Exporters** | Expose metrics from third-party systems in Prometheus format |
| **Pushgateway** | Accepts metrics pushed from short-lived jobs (batch, cron) |
| **Alertmanager** | Handles alert routing, deduplication, grouping, silencing |
| **Client Libraries** | Instrument your application code (Go, Java, Python, etc.) |

#### Pull Model vs Push Model

| Aspect | Pull (Prometheus default) | Push (Pushgateway / other systems) |
|--------|--------------------------|-------------------------------------|
| Direction | Prometheus scrapes targets | Targets push to a collector |
| Discovery | Prometheus knows all targets | Targets must know the collector |
| Health check | Failed scrape = target is down | No implicit health signal |
| Best for | Long-running services | Short-lived batch jobs |
| Scaling | Prometheus controls load | Risk of overwhelming collector |

### 2.2 Installing Prometheus

#### Docker (recommended for learning)

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

#### Minimal Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s      # How often to scrape targets
  evaluation_interval: 15s  # How often to evaluate rules

scrape_configs:
  - job_name: "prometheus"  # Prometheus monitors itself
    static_configs:
      - targets: ["localhost:9090"]
```

#### Verify Installation

1. Open `http://<host>:9090` — Prometheus UI.
2. Go to **Status → Targets** — should show `prometheus` target as UP.
3. Query `up` in the expression browser — should return `up{job="prometheus"} 1`.

### 2.3 Node Exporter Setup

Node Exporter exposes Linux host metrics (CPU, memory, disk, network).

```bash
docker run -d \
  --name node-exporter \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  prom/node-exporter \
  --path.rootfs=/host
```

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "node"
    static_configs:
      - targets: ["localhost:9100"]
```

#### Key Node Exporter Metrics

| Metric | What It Measures |
|--------|-----------------|
| `node_cpu_seconds_total` | CPU time per mode (user, system, idle, iowait) |
| `node_memory_MemAvailable_bytes` | Available memory |
| `node_filesystem_avail_bytes` | Available disk space |
| `node_network_receive_bytes_total` | Network bytes received |
| `node_load1` | 1-minute load average |

### 2.4 PromQL Basics

PromQL is Prometheus's query language for selecting and aggregating time series.

#### Data Types

| Type | Description | Example |
|------|-------------|---------|
| **Instant vector** | Set of time series, each with a single sample at the query time | `http_requests_total` |
| **Range vector** | Set of time series, each with a range of samples | `http_requests_total[5m]` |
| **Scalar** | Single numeric value | `42` |

#### Selectors and Matchers

```promql
# Exact match
http_requests_total{method="GET"}

# Regex match
http_requests_total{method=~"GET|POST"}

# Negative match
http_requests_total{status!="200"}

# Negative regex
http_requests_total{status!~"2.."}
```

#### Essential Functions

```promql
# Rate: per-second increase of a counter over a range
rate(http_requests_total[5m])

# Increase: total increase of a counter over a range
increase(http_requests_total[1h])

# Sum: aggregate across label dimensions
sum(rate(http_requests_total[5m])) by (method)

# Histogram quantile: calculate percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Average
avg(node_cpu_seconds_total{mode="idle"}) by (instance)

# Count
count(up == 1)
```

#### Common Patterns

```promql
# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# CPU usage percentage
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage percentage
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disk usage percentage
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

### 2.5 Understanding Time Series

#### Metric Types

| Type | Behavior | Example |
|------|----------|---------|
| **Counter** | Only goes up (resets to 0 on restart) | `http_requests_total` |
| **Gauge** | Goes up and down | `node_memory_MemAvailable_bytes` |
| **Histogram** | Counts observations in configurable buckets | `http_request_duration_seconds` |
| **Summary** | Like histogram but calculates quantiles client-side | `go_gc_duration_seconds` |

#### Labels

Labels are key-value pairs that create dimensions:

```
http_requests_total{method="GET", handler="/api/users", status="200"} 14523
http_requests_total{method="POST", handler="/api/users", status="201"} 342
```

Each unique combination of metric name + labels = one time series. High cardinality (too many unique label combinations) is the primary cause of Prometheus performance issues.

### Beginner Exercises

1. **Install and configure:** Set up Prometheus + Node Exporter. Verify both targets are UP.
2. **PromQL practice:** Write queries for:
   - Total HTTP requests in the last hour
   - CPU usage per core
   - Available memory in GB
   - Top 5 instances by disk usage
3. **Identify metric types:** For each metric below, state whether it's a counter, gauge, histogram, or summary:
   - `process_resident_memory_bytes`
   - `http_requests_total`
   - `http_request_duration_seconds_bucket`
   - `node_load1`

---

## Level 2: Intermediate

### 2.6 Service Discovery

Static targets don't scale. Prometheus supports dynamic service discovery.

#### Kubernetes SD

```yaml
scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: (.+)
        replacement: ${1}
```

#### EC2 SD

```yaml
scrape_configs:
  - job_name: "ec2"
    ec2_sd_configs:
      - region: us-east-1
        port: 9100
        filters:
          - name: tag:Environment
            values: ["production"]
    relabel_configs:
      - source_labels: [__meta_ec2_tag_Name]
        target_label: instance_name
```

#### Other SD Mechanisms

| Mechanism | Use Case |
|-----------|----------|
| `consul_sd_configs` | Consul service registry |
| `dns_sd_configs` | DNS SRV records |
| `file_sd_configs` | JSON/YAML files (updated externally) |
| `azure_sd_configs` | Azure VMs |
| `gce_sd_configs` | GCP instances |

### 2.7 Recording Rules

Recording rules precompute frequently used or expensive queries and save the result as a new time series.

```yaml
# rules/recording.yml
groups:
  - name: http_rules
    interval: 30s
    rules:
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)

      - record: job:http_errors:rate5m
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)

      - record: job:http_error_ratio:rate5m
        expr: job:http_errors:rate5m / job:http_requests:rate5m
```

**When to use recording rules:**
- Dashboard queries that run frequently.
- Queries used in alerts (alerts should reference simple expressions).
- Queries that aggregate across many time series.

**Naming convention:** `level:metric:operations` — e.g., `job:http_requests:rate5m`.

### 2.8 Alertmanager Setup

#### Prometheus Alert Rules

```yaml
# rules/alerts.yml
groups:
  - name: service_alerts
    rules:
      - alert: HighErrorRate
        expr: job:http_error_ratio:rate5m > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"
          runbook_url: "https://wiki.example.com/runbooks/high-error-rate"

      - alert: HighLatency
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency above 1s on {{ $labels.job }}"
```

#### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: "default"
  group_by: ["alertname", "job"]
  group_wait: 30s       # Wait before sending first notification
  group_interval: 5m    # Wait before sending updates
  repeat_interval: 4h   # Resend if not resolved
  routes:
    - match:
        severity: critical
      receiver: "pagerduty"
    - match:
        severity: warning
      receiver: "slack"

receivers:
  - name: "default"
    email_configs:
      - to: "team@example.com"

  - name: "pagerduty"
    pagerduty_configs:
      - service_key: "<key>"

  - name: "slack"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/..."
        channel: "#alerts"
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: ["alertname", "job"]
```

### 2.9 Relabeling

Relabeling transforms labels during scraping (`relabel_configs`) or before storage (`metric_relabel_configs`).

#### Common Actions

| Action | Effect |
|--------|--------|
| `keep` | Keep targets/metrics matching regex |
| `drop` | Drop targets/metrics matching regex |
| `replace` | Set target label from source labels |
| `labelmap` | Copy labels matching regex |
| `labeldrop` | Remove labels matching regex |
| `hashmod` | Hash source labels for sharding |

#### Examples

```yaml
relabel_configs:
  # Keep only targets with a specific annotation
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true

  # Rename a label
  - source_labels: [__meta_ec2_tag_Name]
    target_label: instance_name

  # Drop metrics with high cardinality
  metric_relabel_configs:
    - source_labels: [__name__]
      regex: "go_.*"
      action: drop
```

### 2.10 Federation

Federation allows one Prometheus server to scrape selected time series from another.

```yaml
# Global Prometheus scraping from regional instances
scrape_configs:
  - job_name: "federate"
    honor_labels: true
    metrics_path: "/federate"
    params:
      match[]:
        - '{job="api-server"}'
        - '{__name__=~"job:.*"}'
    static_configs:
      - targets:
          - "prometheus-us:9090"
          - "prometheus-eu:9090"
```

**Use cases:**
- Aggregating metrics from multiple clusters.
- Hierarchical collection (team → global).
- Cross-datacenter visibility.

### 2.11 Remote Write

Remote write sends samples to external long-term storage.

```yaml
remote_write:
  - url: "http://thanos-receive:19291/api/v1/receive"
    queue_config:
      max_samples_per_send: 5000
      batch_send_deadline: 5s
      max_shards: 30
```

**Compatible backends:** Thanos, Cortex, Mimir, VictoriaMetrics, Datadog, Grafana Cloud.

### 2.12 Scaling Prometheus

| Strategy | When to Use |
|----------|-------------|
| **Vertical scaling** | < 1M active time series — add more CPU/RAM |
| **Functional sharding** | Split by team/namespace — each Prometheus scrapes a subset |
| **Hashmod sharding** | Distribute targets across N Prometheus instances using `hashmod` relabeling |
| **Federation** | Aggregate pre-computed recording rules from multiple instances |
| **Remote write + long-term storage** | Offload storage to Thanos/Cortex/Mimir |

### Intermediate Exercises

1. **Service discovery:** Configure Prometheus to discover targets from a file-based SD. Add and remove targets dynamically.
2. **Recording rules:** Create recording rules for the four Golden Signals. Verify they produce new time series.
3. **Alertmanager:** Set up Alertmanager with Slack notifications. Create alerts for error rate and latency. Test with `amtool`.
4. **Relabeling:** Use `metric_relabel_configs` to drop all Go runtime metrics from a target.
5. **Federation:** Set up two Prometheus instances. Federate recording rules from one to the other.

---

## Level 3: Advanced

### 2.13 High Availability Prometheus

#### HA Pair

Run two identical Prometheus instances scraping the same targets. Both evaluate the same rules. Alertmanager deduplicates alerts.

```
┌──────────────┐     ┌──────────────┐
│ Prometheus A │     │ Prometheus B │
│ (primary)    │     │ (replica)    │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                │
       ┌────────▼────────┐
       │  Alertmanager   │
       │  (clustered)    │
       └─────────────────┘
```

- Both instances scrape independently — slight data differences are expected.
- Alertmanager cluster deduplicates notifications.
- Grafana can query either instance (or use a load balancer).

### 2.14 Thanos / Cortex / Mimir Architecture

These projects solve Prometheus's limitations: no global view, limited retention, no HA query layer.

#### Thanos Architecture

```
┌────────────┐  ┌────────────┐
│ Prometheus │  │ Prometheus │
│ + Sidecar  │  │ + Sidecar  │
└─────┬──────┘  └─────┬──────┘
      │               │
      └───────┬───────┘
              │
     ┌────────▼────────┐     ┌──────────────┐
     │  Thanos Query   │────▶│  Object Store │
     │  (global view)  │     │  (S3/GCS)     │
     └─────────────────┘     └──────────────┘
              │
     ┌────────▼────────┐
     │  Thanos Compact │  (downsampling + compaction)
     └─────────────────┘
```

| Component | Role |
|-----------|------|
| **Sidecar** | Uploads Prometheus blocks to object storage, serves as a Store API |
| **Query** | Global query layer — fans out to sidecars and store gateways |
| **Store Gateway** | Serves historical data from object storage |
| **Compactor** | Compacts and downsamples blocks in object storage |
| **Ruler** | Evaluates recording and alerting rules globally |
| **Receive** | Accepts remote write (alternative to sidecar) |

#### Cortex / Mimir

- Multi-tenant by design.
- Uses a hash ring for distribution.
- Components: Distributor → Ingester → Querier → Compactor → Store Gateway.
- Mimir is Grafana's fork of Cortex with performance improvements.

### 2.15 Custom Exporters

When no existing exporter covers your system, write a custom one.

#### Python Example

```python
from prometheus_client import start_http_server, Gauge, Counter
import time
import random

# Define metrics
queue_depth = Gauge("app_queue_depth", "Current queue depth", ["queue_name"])
jobs_processed = Counter("app_jobs_processed_total", "Total jobs processed", ["queue_name", "status"])

def collect_metrics():
    """Simulate collecting metrics from an application."""
    while True:
        queue_depth.labels(queue_name="orders").set(random.randint(0, 100))
        jobs_processed.labels(queue_name="orders", status="success").inc(random.randint(1, 10))
        jobs_processed.labels(queue_name="orders", status="failed").inc(random.randint(0, 2))
        time.sleep(5)

if __name__ == "__main__":
    start_http_server(8000)  # Expose metrics on :8000/metrics
    collect_metrics()
```

#### Go Example

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    queueDepth = prometheus.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "app_queue_depth",
            Help: "Current queue depth",
        },
        []string{"queue_name"},
    )
)

func init() {
    prometheus.MustRegister(queueDepth)
}

func main() {
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8000", nil)
}
```

### 2.16 Performance Tuning

| Area | Recommendation |
|------|---------------|
| **Cardinality** | Keep active time series < 2M per instance. Audit with `prometheus_tsdb_head_series`. |
| **Scrape interval** | 15s–30s for most targets. 60s for low-priority targets. |
| **Retention** | Default 15d. Increase only if not using remote storage. |
| **Memory** | ~2KB per active time series. 1M series ≈ 2GB RAM. |
| **Storage** | ~1.5 bytes per sample. 1M series at 15s interval ≈ 30GB/day. |
| **WAL** | Ensure WAL directory is on fast storage (SSD). |
| **Query limits** | Set `--query.max-samples` and `--query.timeout` to prevent runaway queries. |

#### Useful Self-Monitoring Queries

```promql
# Active time series count
prometheus_tsdb_head_series

# Scrape duration
prometheus_target_scrape_pool_sync_total

# Ingestion rate
rate(prometheus_tsdb_head_samples_appended_total[5m])

# Query duration
histogram_quantile(0.99, rate(prometheus_engine_query_duration_seconds_bucket[5m]))

# Memory usage
process_resident_memory_bytes{job="prometheus"}
```

### 2.17 Multi-Cluster Monitoring

#### Architecture Pattern

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Cluster A      │  │  Cluster B      │  │  Cluster C      │
│  Prometheus     │  │  Prometheus     │  │  Prometheus     │
│  + Thanos       │  │  + Thanos       │  │  + Thanos       │
│    Sidecar      │  │    Sidecar      │  │    Sidecar      │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────┬───────┴────────────────────┘
                      │
             ┌────────▼────────┐
             │  Thanos Query   │  (global view)
             │  + Store GW     │
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │  Grafana        │
             └─────────────────┘
```

**Key considerations:**
- Add `external_labels` to each Prometheus to identify the cluster: `cluster: "us-east-1"`.
- Use Thanos Query for cross-cluster queries.
- Use Thanos Ruler for global alerting rules.
- Object storage (S3/GCS) for long-term retention.

### 2.18 Cost Optimization

1. **Reduce cardinality:** Drop unused labels and metrics with `metric_relabel_configs`.
2. **Increase scrape intervals** for non-critical targets.
3. **Use recording rules** to pre-aggregate and drop raw high-cardinality series.
4. **Downsample** historical data with Thanos Compactor (5m and 1h resolutions).
5. **Set retention policies** — keep raw data for 15d, downsampled for 1y.
6. **Right-size instances** — monitor `prometheus_tsdb_head_series` and scale accordingly.

### Advanced Exercises

1. **HA setup:** Deploy a Prometheus HA pair with clustered Alertmanager. Verify alert deduplication.
2. **Thanos:** Deploy Thanos Sidecar, Query, and Store Gateway. Query across two Prometheus instances.
3. **Custom exporter:** Write an exporter for a database or message queue. Expose counter, gauge, and histogram metrics.
4. **Performance audit:** Analyze a Prometheus instance. Identify the top 10 metrics by cardinality. Propose and implement reductions.
5. **Multi-cluster:** Set up monitoring for two Kubernetes clusters with a global query layer.

---

## Next Module

→ [Module 3 — Grafana](../03-grafana/README.md)
