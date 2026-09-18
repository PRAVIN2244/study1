# Module 4 — Datadog

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~25 hours  
**Prerequisites:** Module 1 (Observability Foundations)

---

## Level 1: Beginner

### 4.1 Datadog Agent Architecture

```
┌─────────────────────────────────────────────┐
│                Datadog Agent                │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ Collector │  │ DogStatsD│  │ APM Agent │ │
│  │ (checks) │  │ (custom  │  │ (traces)  │ │
│  │          │  │  metrics)│  │           │ │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │
│       │             │              │        │
│  ┌────▼─────────────▼──────────────▼─────┐  │
│  │            Forwarder                  │  │
│  │  (batches, compresses, sends to DD)   │  │
│  └───────────────────┬───────────────────┘  │
└──────────────────────┼──────────────────────┘
                       │ HTTPS
              ┌────────▼────────┐
              │  Datadog Cloud  │
              │  (intake API)   │
              └─────────────────┘
```

| Component | Role |
|-----------|------|
| **Collector** | Runs integration checks (system, Docker, Kubernetes, databases) |
| **DogStatsD** | UDP/UDS server for custom metrics from application code |
| **APM Agent** | Receives traces from instrumented applications |
| **Process Agent** | Collects live process and container data |
| **Security Agent** | Runtime security monitoring and compliance |
| **Forwarder** | Batches and sends all data to Datadog's intake API |

### 4.2 Installing the Agent

#### Linux (VM)

```bash
DD_API_KEY=<YOUR_API_KEY> DD_SITE="datadoghq.com" \
  bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"
```

#### Docker

```bash
docker run -d \
  --name datadog-agent \
  -e DD_API_KEY=<YOUR_API_KEY> \
  -e DD_SITE="datadoghq.com" \
  -e DD_LOGS_ENABLED=true \
  -e DD_APM_ENABLED=true \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  gcr.io/datadoghq/agent:7
```

#### Kubernetes (Helm)

```bash
helm repo add datadog https://helm.datadoghq.com
helm install datadog datadog/datadog \
  --set datadog.apiKey=<YOUR_API_KEY> \
  --set datadog.site="datadoghq.com" \
  --set datadog.logs.enabled=true \
  --set datadog.apm.portEnabled=true \
  --set datadog.processAgent.enabled=true
```

#### Verify Installation

```bash
# Check agent status
datadog-agent status

# Check connectivity
datadog-agent diagnose
```

### 4.3 Infrastructure Monitoring

#### Host Map

The host map provides a visual overview of all monitored hosts:
- Color by metric (CPU, memory, load).
- Group by tag (environment, region, service).
- Filter by tag or search.

#### Infrastructure List

- All hosts with agent installed.
- Shows: hostname, OS, agent version, tags, integrations, apps.
- Click a host to see detailed metrics.

#### Key Default Metrics

| Metric | Description |
|--------|-------------|
| `system.cpu.user` | CPU time in user mode (%) |
| `system.cpu.system` | CPU time in kernel mode (%) |
| `system.mem.used` | Memory used (bytes) |
| `system.disk.used` | Disk space used (bytes) |
| `system.net.bytes_rcvd` | Network bytes received |
| `system.load.1` | 1-minute load average |

### 4.4 Metrics Explorer

The Metrics Explorer allows ad-hoc metric exploration:

1. **Select metric:** Type or browse metric names.
2. **Filter:** Add tag filters (e.g., `env:production`, `service:api`).
3. **Aggregate:** Choose aggregation (avg, sum, min, max, count).
4. **Group by:** Split by tag dimensions.
5. **Visualize:** Line, bar, area, or top list.

#### Metric Query Syntax

```
avg:system.cpu.user{env:production} by {host}
sum:http.requests{service:api,status:5xx}.as_rate()
top(avg:system.cpu.user{*} by {host}, 10, 'mean', 'desc')
```

### 4.5 Creating Monitors

Monitors are Datadog's alerting mechanism.

#### Monitor Types

| Type | Use Case |
|------|----------|
| **Metric** | Threshold on any metric |
| **Anomaly** | Deviation from historical pattern |
| **Outlier** | One member of a group behaves differently |
| **Forecast** | Metric predicted to cross threshold |
| **Log** | Log volume or pattern matching |
| **APM** | Trace metrics (error rate, latency) |
| **Process** | Process up/down, resource usage |
| **Network** | TCP/HTTP check results |
| **Composite** | Combine multiple monitors with boolean logic |

#### Creating a Metric Monitor

1. **Monitors → New Monitor → Metric**.
2. **Define the metric:** `avg:system.cpu.user{env:production} by {host}`.
3. **Set conditions:**
   - Alert threshold: `> 90` for the last `5 minutes`.
   - Warning threshold: `> 80` for the last `5 minutes`.
4. **Configure notifications:**
   ```
   {{#is_alert}}
   CPU usage on {{host.name}} is {{value}}%.
   @slack-ops-alerts @pagerduty-platform
   {{/is_alert}}

   {{#is_warning}}
   CPU usage on {{host.name}} is {{value}}%.
   @slack-ops-warnings
   {{/is_warning}}
   ```
5. **Set tags:** `env:production`, `team:platform`.

### 4.6 Log Ingestion Basics

#### Enable Log Collection

```yaml
# /etc/datadog-agent/datadog.yaml
logs_enabled: true
```

#### Configure Log Source

```yaml
# /etc/datadog-agent/conf.d/myapp.d/conf.yaml
logs:
  - type: file
    path: /var/log/myapp/*.log
    service: myapp
    source: python
    tags:
      - env:production
```

#### Docker Log Collection

```bash
docker run -d \
  --name myapp \
  --label com.datadoghq.ad.logs='[{"source": "python", "service": "myapp"}]' \
  myapp:latest
```

#### Log Explorer

- **Search:** Full-text search with facets.
- **Filters:** Filter by status, service, source, tags.
- **Patterns:** Auto-detected log patterns.
- **Analytics:** Aggregate logs into metrics (count, unique count).

### Beginner Exercises

1. **Install agent:** Deploy the Datadog agent on a VM or in Docker. Verify it reports to Datadog.
2. **Host map:** Explore the host map. Group hosts by a custom tag.
3. **Metrics explorer:** Find the top 5 hosts by CPU usage. Create a graph of memory usage over 24 hours.
4. **Monitor:** Create a metric monitor for disk usage > 80%. Configure Slack notification.
5. **Logs:** Enable log collection for a sample application. Search and filter logs in the Log Explorer.

---

## Level 2: Intermediate

### 4.7 APM Setup

#### Auto-Instrumentation (Python Example)

```bash
pip install ddtrace
ddtrace-run python app.py
```

#### Manual Instrumentation

```python
from ddtrace import tracer

@tracer.wrap(service="payment-service", resource="process_payment")
def process_payment(order_id):
    with tracer.trace("validate_card") as span:
        span.set_tag("order_id", order_id)
        validate_card(order_id)

    with tracer.trace("charge_card"):
        charge_card(order_id)
```

#### Supported Languages

| Language | Library | Auto-Instrumentation |
|----------|---------|---------------------|
| Python | `ddtrace` | `ddtrace-run` |
| Java | `dd-java-agent` | `-javaagent:dd-java-agent.jar` |
| Node.js | `dd-trace` | `--require dd-trace/init` |
| Go | `dd-trace-go` | Manual only |
| Ruby | `ddtrace` | `Datadog.configure` |
| .NET | `dd-trace-dotnet` | Environment variables |

#### APM Configuration

```yaml
# /etc/datadog-agent/datadog.yaml
apm_config:
  enabled: true
  env: production
  max_traces_per_second: 200  # Sampling rate
```

### 4.8 Distributed Tracing

#### Trace View

A trace shows the full request lifecycle across services:

```
[API Gateway] ──▶ [Auth Service] ──▶ [User DB]
      │
      └──▶ [Order Service] ──▶ [Payment Service] ──▶ [Payment Gateway]
                  │
                  └──▶ [Inventory Service] ──▶ [Inventory DB]
```

Each box is a **span**. The full tree is a **trace**.

#### Key APM Metrics

| Metric | Description |
|--------|-------------|
| `trace.http.request.hits` | Request count |
| `trace.http.request.errors` | Error count |
| `trace.http.request.duration` | Request duration |
| `trace.http.request.apdex` | Apdex score |

#### Service Map

- Auto-generated topology of services and their dependencies.
- Shows request rate, error rate, and latency between services.
- Click a service to drill into its traces.

#### Trace Search

- Search traces by service, resource, status, duration, tags.
- Filter: `service:api-gateway AND @http.status_code:500 AND @duration:>1s`.
- Correlate traces with logs using `trace_id`.

### 4.9 Custom Metrics

#### DogStatsD (Application Code)

```python
from datadog import statsd

# Counter
statsd.increment("orders.processed", tags=["env:production", "region:us-east"])

# Gauge
statsd.gauge("queue.depth", 42, tags=["queue:orders"])

# Histogram (distribution of values)
statsd.histogram("payment.duration", 0.234, tags=["provider:stripe"])

# Distribution (global percentiles)
statsd.distribution("request.duration", 0.150, tags=["service:api"])

# Set (unique values)
statsd.set("users.active", user_id, tags=["env:production"])
```

#### Custom Metrics via API

```bash
curl -X POST "https://api.datadoghq.com/api/v1/series" \
  -H "DD-API-KEY: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "series": [{
      "metric": "custom.deployments",
      "points": [['"$(date +%s)"', 1]],
      "type": "count",
      "tags": ["service:api", "env:production", "version:2.3.1"]
    }]
  }'
```

### 4.10 Log Pipelines

Log pipelines process and enrich logs before indexing.

#### Pipeline Structure

```
Raw Log → Pipeline → Processor 1 → Processor 2 → ... → Indexed Log
```

#### Common Processors

| Processor | Purpose | Example |
|-----------|---------|---------|
| **Grok Parser** | Extract structured fields from unstructured logs | Parse nginx access logs |
| **Date Remapper** | Set the official log timestamp | Map `@timestamp` field |
| **Status Remapper** | Set log severity | Map `level` to status |
| **Service Remapper** | Set the service name | Map `app_name` to service |
| **Attribute Remapper** | Rename or copy attributes | Rename `user_id` to `usr.id` |
| **Category Processor** | Add categories based on conditions | Classify by URL pattern |
| **Lookup Processor** | Enrich with reference data | Map error codes to descriptions |

#### Grok Parser Example

```
# Log line:
# 192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] "GET /api/users HTTP/1.1" 200 2326

# Grok pattern:
%{ip:network.client.ip} - - \[%{date("dd/MMM/yyyy:HH:mm:ss Z"):date}\] "%{word:http.method} %{notSpace:http.url} HTTP/%{number:http.version}" %{integer:http.status_code} %{integer:network.bytes_written}
```

### 4.11 Dashboards with Template Variables

#### Creating Template Variables

1. **Dashboard → Edit → Add Variable**.
2. **Variable type:** Tag/Attribute.
3. **Tag group:** `env` → values auto-populated from tags.
4. **Default:** `production`.

#### Using Variables

```
avg:system.cpu.user{env:$env, service:$service} by {host}
```

#### Dashboard Widgets

| Widget | Use Case |
|--------|----------|
| **Timeseries** | Metrics over time |
| **Query Value** | Single number (current value) |
| **Top List** | Ranked list of values |
| **Change** | Metric change over time period |
| **Distribution** | Histogram of values |
| **Geomap** | Geographic distribution |
| **Service Map** | Service topology |
| **SLO** | SLO status and error budget |
| **Log Stream** | Live log feed |
| **Trace Map** | Trace flame graph |

### 4.12 Synthetic Monitoring

Proactive monitoring — test endpoints before users hit them.

#### API Tests

```yaml
# Conceptual configuration
name: "Checkout API Health"
type: api
request:
  method: POST
  url: "https://api.example.com/v1/checkout"
  headers:
    Content-Type: application/json
  body: '{"item_id": "test-123", "quantity": 1}'
assertions:
  - type: statusCode
    operator: is
    target: 200
  - type: responseTime
    operator: lessThan
    target: 2000  # ms
  - type: body
    operator: contains
    target: "order_id"
locations:
  - aws:us-east-1
  - aws:eu-west-1
frequency: 60  # seconds
```

#### Browser Tests

- Record user flows (login, checkout, search).
- Replay from multiple global locations.
- Assert on page load time, element presence, JavaScript errors.
- Screenshot on failure.

### 4.13 RUM (Real User Monitoring)

#### Setup

```html
<script>
  (function(h,o,u,n,d) {
    h=h[d]=h[d]||{q:[],onReady:function(c){h.q.push(c)}}
    d=o.createElement(u);d.async=1;d.src=n
    n=o.getElementsByTagName(u)[0];n.parentNode.insertBefore(d,n)
  })(window,document,'script','https://www.datadoghq-browser-agent.com/datadog-rum-v4.js','DD_RUM')
  DD_RUM.onReady(function() {
    DD_RUM.init({
      clientToken: '<CLIENT_TOKEN>',
      applicationId: '<APPLICATION_ID>',
      site: 'datadoghq.com',
      service: 'my-web-app',
      env: 'production',
      version: '1.0.0',
      sessionSampleRate: 100,
      sessionReplaySampleRate: 20,
      trackUserInteractions: true,
      trackResources: true,
      trackLongTasks: true,
    })
  })
</script>
```

#### RUM Data

| Data Type | What It Captures |
|-----------|-----------------|
| **Views** | Page loads, route changes, load time, LCP, FID, CLS |
| **Actions** | User clicks, form submissions |
| **Resources** | XHR/Fetch calls, images, scripts, stylesheets |
| **Long Tasks** | JavaScript tasks blocking the main thread > 50ms |
| **Errors** | JavaScript errors, network errors |
| **Sessions** | User session with full replay capability |

### Intermediate Exercises

1. **APM:** Instrument a multi-service application. View the service map and trace waterfall.
2. **Custom metrics:** Send custom business metrics via DogStatsD. Create a dashboard.
3. **Log pipeline:** Create a pipeline that parses nginx access logs, extracts fields, and sets status.
4. **Synthetic test:** Create an API test for a public endpoint. Set up alerting on failure.
5. **RUM:** Add RUM to a web application. Analyze Core Web Vitals.

---

## Level 3: Advanced

### 4.14 Datadog SLO Management

#### Creating an SLO

1. **SLOs → New SLO**.
2. **Type:**
   - **Metric-based:** Define good events / total events using metrics.
   - **Monitor-based:** SLO based on monitor uptime.
3. **Target:** e.g., 99.9% over 30 days.
4. **Error budget:** Auto-calculated.

#### Metric-Based SLO Example

```
Good events: sum:http.requests{service:api, NOT status:5xx}
Total events: sum:http.requests{service:api}
Target: 99.9% over 30 days
```

#### SLO Alerts

- Alert when error budget consumption rate predicts exhaustion.
- Burn rate alerts: "At the current rate, the error budget will be exhausted in X hours."

### 4.15 Anomaly Detection

Datadog uses machine learning to detect anomalies.

#### Anomaly Monitor

```
Monitor: avg:system.cpu.user{env:production} by {host}
Algorithm: agile (adapts quickly to changes)
Bounds: 3 standard deviations
Seasonality: weekly
```

#### Algorithms

| Algorithm | Behavior | Best For |
|-----------|----------|----------|
| **Basic** | Simple rolling quantiles | Metrics without seasonality |
| **Agile** | Adapts quickly to level shifts | Metrics that change behavior |
| **Robust** | Ignores recent anomalies when calculating bounds | Metrics with occasional spikes |

### 4.16 Watchdog AI

Watchdog automatically detects anomalies across your infrastructure and applications without configuration.

- **Application performance:** Detects latency increases, error rate spikes.
- **Infrastructure:** Detects unusual resource consumption patterns.
- **Log anomalies:** Detects new error patterns in logs.
- **Root cause analysis:** Correlates anomalies across metrics, traces, and logs.

### 4.17 Security Monitoring

#### Cloud SIEM

- Ingest security logs (AWS CloudTrail, auth logs, firewall logs).
- Detection rules match log patterns to known threats.
- Security signals group related detections into investigations.

#### Cloud Security Posture Management (CSPM)

- Scan cloud resources against compliance frameworks (CIS, PCI-DSS, SOC 2).
- Identify misconfigurations (open S3 buckets, overly permissive IAM).
- Track compliance score over time.

#### Cloud Workload Security (CWS)

- Runtime threat detection on hosts and containers.
- File integrity monitoring.
- Process-level activity monitoring.
- Kernel-level detection using eBPF.

### 4.18 Cost Management

#### Metric Cardinality

```
# Check custom metric volume
Metrics → Summary → sort by "Distinct Tag Value Combinations"
```

#### Cost Optimization Strategies

| Area | Strategy |
|------|----------|
| **Custom metrics** | Reduce tag cardinality. Use distributions instead of histograms. |
| **Logs** | Use exclusion filters to drop noisy logs before indexing. Use log archives for compliance. |
| **APM** | Tune sampling rates. Use Ingestion Controls to set per-service rates. |
| **Synthetics** | Reduce test frequency for non-critical endpoints. |
| **RUM** | Set appropriate session sample rates. |
| **Infrastructure** | Remove agents from decommissioned hosts. |

#### Estimated Usage Metrics

Datadog provides `datadog.estimated_usage.*` metrics:
- `datadog.estimated_usage.logs.ingested_bytes`
- `datadog.estimated_usage.apm.ingested_spans`
- `datadog.estimated_usage.custom_metrics.avg`
- `datadog.estimated_usage.rum.sessions`

### 4.19 Cross-Org Visibility

For enterprises with multiple Datadog organizations:

- **Cross-Organization Viewer:** View dashboards from child orgs in a parent org.
- **Metrics forwarding:** Forward metrics from child to parent org.
- **Centralized billing:** Manage usage across all orgs.

### 4.20 Advanced Tagging Strategy

Tags are the foundation of Datadog's data model. A consistent strategy is essential.

#### Recommended Tag Schema

| Tag | Purpose | Example |
|-----|---------|---------|
| `env` | Environment | `env:production` |
| `service` | Service name | `service:payment-api` |
| `version` | Application version | `version:2.3.1` |
| `team` | Owning team | `team:platform` |
| `region` | Cloud region | `region:us-east-1` |
| `availability-zone` | AZ | `availability-zone:us-east-1a` |
| `instance-type` | Instance size | `instance-type:m5.xlarge` |
| `cost-center` | Billing allocation | `cost-center:engineering` |

#### Unified Service Tagging

Apply `env`, `service`, and `version` consistently across metrics, logs, and traces. This enables seamless correlation.

```yaml
# Kubernetes pod labels
labels:
  tags.datadoghq.com/env: production
  tags.datadoghq.com/service: payment-api
  tags.datadoghq.com/version: "2.3.1"
```

### Advanced Exercises

1. **SLO:** Define SLOs for a service. Set up burn rate alerts. Create an SLO dashboard.
2. **Anomaly detection:** Configure anomaly monitors for CPU and request latency. Compare algorithms.
3. **Security:** Enable Cloud SIEM. Create a custom detection rule for failed SSH logins.
4. **Cost audit:** Analyze custom metric usage. Identify and reduce the top 5 high-cardinality metrics.
5. **Tagging:** Implement unified service tagging across a multi-service application. Verify correlation in APM.

---

## Next Module

→ [Module 5 — ELK Stack](../05-elk-stack/README.md)
