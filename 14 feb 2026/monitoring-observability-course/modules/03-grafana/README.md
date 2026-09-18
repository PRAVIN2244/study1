# Module 3 — Grafana

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~15 hours  
**Prerequisites:** Module 2 (Prometheus)

---

## Level 1: Beginner

### 3.1 Connecting Grafana to Prometheus

#### Installation

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  grafana/grafana
```

#### Adding Prometheus as a Data Source

1. Navigate to **Configuration → Data Sources → Add data source**.
2. Select **Prometheus**.
3. Set URL: `http://prometheus:9090` (or host IP if not using Docker network).
4. Click **Save & Test** — should show "Data source is working".

#### Verify

- Go to **Explore** tab.
- Select the Prometheus data source.
- Run `up` — should return results.

### 3.2 Creating Dashboards

#### Dashboard Structure

```
Dashboard
├── Row 1: "Overview"
│   ├── Panel: Request Rate (Graph)
│   ├── Panel: Error Rate (Stat)
│   └── Panel: Uptime (Gauge)
├── Row 2: "Infrastructure"
│   ├── Panel: CPU Usage (Time Series)
│   ├── Panel: Memory Usage (Time Series)
│   └── Panel: Disk Usage (Bar Gauge)
└── Row 3: "Latency"
    ├── Panel: P50 Latency (Time Series)
    └── Panel: P99 Latency (Time Series)
```

#### Creating Your First Dashboard

1. Click **+ → Dashboard → Add new panel**.
2. Select data source: Prometheus.
3. Enter query: `rate(http_requests_total[5m])`.
4. Set visualization type (top right).
5. Configure panel title, description, and legend.
6. Click **Apply**.
7. Click **Save dashboard** (disk icon).

#### Dashboard JSON

Dashboards are stored as JSON. Export via **Dashboard settings → JSON Model**. This enables version control and sharing.

### 3.3 Panels & Visualization Types

| Visualization | Best For | Example Metric |
|--------------|----------|----------------|
| **Time Series** | Trends over time | `rate(http_requests_total[5m])` |
| **Stat** | Single current value | `up` |
| **Gauge** | Value against min/max | Memory usage % |
| **Bar Gauge** | Comparing values | Disk usage per mount |
| **Table** | Tabular data | Top endpoints by request count |
| **Heatmap** | Distribution over time | Request duration histogram |
| **Pie Chart** | Proportions | Traffic by HTTP method |
| **Logs** | Log entries | Loki/Elasticsearch logs |
| **Node Graph** | Service topology | Trace data |

#### Panel Configuration

Each panel has:
- **Query:** The data source query (PromQL, LogQL, etc.).
- **Transform:** Post-query data manipulation (join, filter, calculate).
- **Overrides:** Per-series styling (color, axis, display name).
- **Thresholds:** Color changes at specific values (green/yellow/red).
- **Value mappings:** Map numeric values to text labels.

### 3.4 Variables

Variables make dashboards dynamic and reusable.

#### Creating a Variable

1. **Dashboard settings → Variables → New variable**.
2. **Type:** Query.
3. **Data source:** Prometheus.
4. **Query:** `label_values(up, job)` — returns all unique `job` label values.
5. **Name:** `job`.

#### Using Variables in Queries

```promql
rate(http_requests_total{job="$job"}[5m])
```

#### Variable Types

| Type | Source | Example |
|------|--------|---------|
| **Query** | Data source query | `label_values(node_cpu_seconds_total, instance)` |
| **Custom** | Comma-separated list | `production, staging, development` |
| **Constant** | Fixed value | `us-east-1` |
| **Interval** | Time intervals | `1m, 5m, 15m, 1h` |
| **Text box** | Free-form input | User-entered filter |

#### Chained Variables

Variables can depend on each other:
- Variable `environment`: `label_values(up, environment)`
- Variable `instance`: `label_values(up{environment="$environment"}, instance)`

Selecting an environment filters the instance dropdown.

### 3.5 Alerts Basics

Grafana can evaluate alert rules and send notifications.

#### Creating an Alert Rule

1. Edit a panel → **Alert** tab.
2. Set condition: `WHEN avg() OF query(A, 5m, now) IS ABOVE 0.01`.
3. Set evaluation interval: `1m`.
4. Set "for" duration: `5m` (must be true for 5 minutes before firing).
5. Add notification channel.

#### Notification Channels

- Email
- Slack
- PagerDuty
- Webhook
- Microsoft Teams
- OpsGenie

### Beginner Exercises

1. **Setup:** Install Grafana and connect it to Prometheus.
2. **Dashboard:** Create a dashboard with 6 panels covering the four Golden Signals.
3. **Variables:** Add a `job` variable and use it in all panel queries.
4. **Alert:** Create an alert for high error rate. Configure a notification channel.

---

## Level 2: Intermediate

### 3.6 Advanced Dashboards

#### Transformations

Transformations process query results before visualization:

| Transform | Use Case |
|-----------|----------|
| **Merge** | Combine results from multiple queries |
| **Filter by name** | Show only specific series |
| **Organize fields** | Rename, reorder, hide columns |
| **Calculate field** | Add computed columns (e.g., percentage) |
| **Group by** | Aggregate rows |
| **Join by field** | SQL-like join across queries |

#### Repeating Panels and Rows

- Set a variable with multi-select enabled.
- In panel settings: **Repeat → Select variable**.
- Grafana creates one panel per variable value.
- Rows can also repeat, creating entire sections per value.

#### Dashboard Links

- **Dashboard links:** Navigate between related dashboards.
- **Data links:** Click a data point to drill down (e.g., from overview to detail dashboard).
- **URL parameters:** Pass variable values between dashboards via URL.

### 3.7 Alert Rules (Unified Alerting)

Grafana 8+ uses unified alerting, replacing legacy panel-based alerts.

#### Alert Rule Structure

```yaml
# Conceptual structure
alert_rule:
  name: "High Error Rate"
  folder: "Production Alerts"
  group: "API Alerts"
  condition: C  # Reference to a query/expression
  queries:
    - refId: A
      datasource: Prometheus
      expr: "sum(rate(http_requests_total{status=~'5..'}[5m]))"
    - refId: B
      datasource: Prometheus
      expr: "sum(rate(http_requests_total[5m]))"
    - refId: C
      datasource: __expr__
      type: math
      expression: "$A / $B"
  condition_threshold: "> 0.01"
  for: 5m
  labels:
    severity: critical
    team: platform
  annotations:
    summary: "Error rate is {{ $value | humanizePercentage }}"
    runbook_url: "https://wiki.example.com/runbooks/high-error-rate"
```

#### Contact Points

Replace notification channels in unified alerting:

| Contact Point | Configuration |
|--------------|---------------|
| Slack | Webhook URL, channel, message template |
| PagerDuty | Integration key, severity mapping |
| Email | SMTP settings, recipients |
| Webhook | URL, HTTP method, headers |

#### Notification Policies

Route alerts to contact points based on labels:

```
Root policy (default contact point)
├── severity=critical → PagerDuty
├── severity=warning → Slack #alerts-warning
├── team=platform → Slack #platform-alerts
└── everything else → Email
```

### 3.8 Annotations

Annotations mark events on graphs (deployments, incidents, config changes).

#### Manual Annotations

- Click on a graph → **Add annotation**.
- Add text, tags, and optional end time (for ranges).

#### API Annotations

```bash
curl -X POST http://grafana:3000/api/annotations \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboardUID": "abc123",
    "time": 1609459200000,
    "text": "Deployed v2.3.1",
    "tags": ["deployment", "api"]
  }'
```

#### Query-Based Annotations

- Add annotation query to dashboard settings.
- Source: Prometheus query that returns events (e.g., `changes(deployment_timestamp[1m])`).

### 3.9 Role-Based Access Control

| Role | Permissions |
|------|------------|
| **Viewer** | View dashboards and panels |
| **Editor** | Create and edit dashboards, create alerts |
| **Admin** | Manage data sources, users, teams, plugins |

#### Organization-Level Access

- Users belong to organizations.
- Each org has its own dashboards, data sources, and users.
- Useful for multi-tenant setups.

#### Folder Permissions

- Dashboards are organized in folders.
- Permissions can be set per folder.
- Teams can be granted access to specific folders.

### 3.10 Multi-Data Source Dashboards

A single dashboard can query multiple data sources:

- **Mixed data source:** Select "Mixed" as the panel data source, then choose per-query.
- **Use cases:**
  - Prometheus metrics + Elasticsearch logs on the same dashboard.
  - CloudWatch + Prometheus for hybrid cloud monitoring.
  - Correlate application metrics with infrastructure metrics from different sources.

#### Cross-Data Source Correlation

- Use consistent labels/tags across data sources.
- Use variables that work across data sources.
- Data links to jump from metrics (Prometheus) to logs (Loki/Elasticsearch) to traces (Jaeger/Tempo).

### Intermediate Exercises

1. **Transformations:** Create a table panel that joins data from two queries and calculates a derived field.
2. **Repeating panels:** Build a dashboard that auto-generates panels for each Kubernetes namespace.
3. **Unified alerting:** Migrate a legacy alert to unified alerting with notification policies.
4. **Annotations:** Set up deployment annotations via CI/CD pipeline webhook.
5. **Multi-source:** Create a dashboard with Prometheus metrics and Elasticsearch logs side by side.

---

## Level 3: Advanced

### 3.11 Grafana as Code

#### Provisioning

Manage dashboards and data sources as code via YAML provisioning files.

```yaml
# provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

```yaml
# provisioning/dashboards/default.yml
apiVersion: 1
providers:
  - name: "default"
    orgId: 1
    folder: "Provisioned"
    type: file
    disableDeletion: true
    editable: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

#### Terraform Provider

```hcl
resource "grafana_dashboard" "api_overview" {
  config_json = file("dashboards/api-overview.json")
  folder      = grafana_folder.production.id
}

resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  url  = "http://prometheus:9090"
}

resource "grafana_alert_rule_group" "api_alerts" {
  name             = "API Alerts"
  folder_uid       = grafana_folder.production.uid
  interval_seconds = 60

  rule {
    name      = "High Error Rate"
    condition = "C"
    # ... query and threshold configuration
  }
}
```

#### Grafonnet (Jsonnet Library)

```jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;

dashboard.new(
  'API Overview',
  schemaVersion=27,
  tags=['api', 'production'],
)
.addPanel(
  graphPanel.new(
    'Request Rate',
    datasource='Prometheus',
  )
  .addTarget(
    prometheus.target(
      'sum(rate(http_requests_total[5m])) by (method)',
      legendFormat='{{ method }}',
    )
  ),
  gridPos={ x: 0, y: 0, w: 12, h: 8 },
)
```

### 3.12 Grafana at Scale

#### Performance Optimization

| Area | Strategy |
|------|----------|
| **Query caching** | Enable query caching in data source settings |
| **Dashboard load time** | Limit panels per dashboard (< 20), use recording rules |
| **Database** | Use PostgreSQL or MySQL instead of SQLite for multi-instance |
| **Session storage** | Use Redis for session storage in HA setups |
| **Image rendering** | Use Grafana Image Renderer plugin for PDF reports |

#### High Availability

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Grafana  │  │ Grafana  │  │ Grafana  │
│ Instance │  │ Instance │  │ Instance │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └──────┬──────┴─────────────┘
            │
   ┌────────▼────────┐
   │  Load Balancer  │
   └────────┬────────┘
            │
   ┌────────▼────────┐    ┌──────────┐
   │  PostgreSQL     │    │  Redis   │
   │  (shared DB)    │    │ (sessions│
   └─────────────────┘    │  cache)  │
                          └──────────┘
```

### 3.13 Plugin Development

#### Types of Plugins

| Type | Purpose | Example |
|------|---------|---------|
| **Data source** | Connect to new data backends | Custom API, proprietary database |
| **Panel** | New visualization types | Custom chart, map, diagram |
| **App** | Full applications within Grafana | Kubernetes app, synthetic monitoring |

#### Plugin Scaffold

```bash
npx @grafana/create-plugin@latest
```

This generates a plugin project with:
- React-based frontend
- Go-based backend (for data source plugins)
- Build tooling and test setup
- Docker Compose for local development

### Advanced Exercises

1. **Provisioning:** Set up Grafana with all dashboards and data sources provisioned from files. No manual configuration.
2. **Terraform:** Manage Grafana resources (dashboards, alerts, data sources) with Terraform.
3. **Grafonnet:** Build a dashboard library using Jsonnet. Generate dashboards for multiple services from a template.
4. **HA deployment:** Deploy Grafana in HA mode with PostgreSQL and Redis. Verify failover.
5. **Plugin:** Create a simple panel plugin that renders a custom visualization.

---

## Next Module

→ [Module 4 — Datadog](../04-datadog/README.md)
