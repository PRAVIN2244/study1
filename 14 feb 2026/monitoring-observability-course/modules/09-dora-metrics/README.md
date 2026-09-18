# Module 9 — DORA Metrics & Pipeline Observability

**Level:** Intermediate  
**Duration:** ~10 hours  
**Prerequisites:** Module 1 (Observability Foundations)

---

## Learning Objectives

By the end of this module you will be able to:

- Define and measure the four DORA metrics.
- Instrument CI/CD pipelines to emit deployment and failure data.
- Distinguish pipeline failures from application failures and handle each appropriately.
- Build dashboards and alerts around software delivery performance.

---

## 9.1 The Four DORA Metrics

DORA (DevOps Research and Assessment) identified four key metrics that predict software delivery performance and organizational outcomes.

### Metric Definitions

| Metric | Definition | What It Measures |
|--------|-----------|-----------------|
| **Deployment Frequency** | How often code is deployed to production | Team velocity and batch size |
| **Lead Time for Changes** | Time from code commit to running in production | Pipeline efficiency |
| **Mean Time to Restore (MTTR)** | Time from production incident to service restoration | Recovery capability |
| **Change Failure Rate** | Percentage of deployments that cause a failure in production | Release quality |

### Performance Benchmarks

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| **Deployment Frequency** | On-demand (multiple/day) | Weekly–Monthly | Monthly–Biannually | Biannually+ |
| **Lead Time** | < 1 hour | 1 day–1 week | 1 week–1 month | 1–6 months |
| **MTTR** | < 1 hour | < 1 day | < 1 week | 1–6 months |
| **Change Failure Rate** | 0–15% | 16–30% | 16–30% | 46–60% |

### Why These Metrics Matter

- They are **outcome-based**, not activity-based — they measure what matters to the business.
- They are **correlated** — teams that deploy frequently also have lower failure rates (smaller batches = less risk).
- They are **non-zero-sum** — speed and stability improve together, not at each other's expense.

---

## 9.2 Measuring Deployment Frequency

### Data Sources

| Source | How to Collect |
|--------|---------------|
| CI/CD pipeline (Jenkins, GitLab CI, GitHub Actions) | Count successful production deployment jobs |
| Kubernetes | Count rollout events (`kubectl rollout history`) |
| Container registry | Count image pushes tagged for production |
| Deployment tool (ArgoCD, Spinnaker) | Count sync/deploy events |
| Custom webhook | Emit event on each deployment |

### Prometheus Metric

```python
# In your deployment pipeline or webhook
from prometheus_client import Counter

deployments_total = Counter(
    'deployments_total',
    'Total production deployments',
    ['service', 'environment', 'result']
)

# On successful deployment
deployments_total.labels(
    service='payment-api',
    environment='production',
    result='success'
).inc()
```

### PromQL Queries

```promql
# Deployments per day
increase(deployments_total{environment="production", result="success"}[1d])

# Deployments per week by service
sum(increase(deployments_total{environment="production"}[7d])) by (service)

# Deployment frequency trend (7-day rolling)
sum(increase(deployments_total{environment="production"}[7d])) / 7
```

### Datadog Custom Metric

```bash
curl -X POST "https://api.datadoghq.com/api/v1/series" \
  -H "DD-API-KEY: <API_KEY>" \
  -d '{
    "series": [{
      "metric": "dora.deployments",
      "points": [['"$(date +%s)"', 1]],
      "type": "count",
      "tags": ["service:payment-api", "env:production", "result:success", "team:payments"]
    }]
  }'
```

---

## 9.3 Measuring Lead Time for Changes

### The Lead Time Pipeline

```
Commit → Build → Test → Staging Deploy → Approval → Production Deploy
  t0      t1      t2        t3              t4            t5

Lead Time = t5 - t0
```

### Data Sources

| Stage | Source |
|-------|--------|
| Commit time | Git (`git log --format=%ct`) |
| Build start/end | CI/CD pipeline timestamps |
| Test start/end | CI/CD pipeline timestamps |
| Deploy time | Deployment tool or webhook |

### Implementation

```python
# Record commit timestamp as a label or metric
import time
import subprocess

# Get commit timestamp
commit_ts = int(subprocess.check_output(
    ['git', 'log', '-1', '--format=%ct']
).strip())

deploy_ts = int(time.time())
lead_time_seconds = deploy_ts - commit_ts

# Emit as histogram for percentile analysis
from prometheus_client import Histogram

lead_time = Histogram(
    'dora_lead_time_seconds',
    'Lead time from commit to production deploy',
    ['service'],
    buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400, 604800]
)

lead_time.labels(service='payment-api').observe(lead_time_seconds)
```

### PromQL Queries

```promql
# Median lead time
histogram_quantile(0.50, rate(dora_lead_time_seconds_bucket[7d]))

# P90 lead time
histogram_quantile(0.90, rate(dora_lead_time_seconds_bucket[7d]))

# Lead time trend (weekly P50)
histogram_quantile(0.50, sum(rate(dora_lead_time_seconds_bucket[7d])) by (le, service))
```

---

## 9.4 Measuring MTTR (Mean Time to Restore)

### Data Sources

| Source | How |
|--------|-----|
| Incident management (PagerDuty, OpsGenie) | Time from incident creation to resolution |
| Monitoring alerts | Time from alert firing to alert resolving |
| Status page | Time from incident posted to resolved |
| Deployment pipeline | Time from rollback trigger to rollback complete |

### Implementation

```python
from prometheus_client import Histogram
import time

restore_time = Histogram(
    'dora_restore_time_seconds',
    'Time to restore service after incident',
    ['service', 'severity'],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800, 86400]
)

# When incident resolves
incident_start = 1609459200  # from incident management system
incident_end = int(time.time())
duration = incident_end - incident_start

restore_time.labels(
    service='payment-api',
    severity='critical'
).observe(duration)
```

### PromQL Queries

```promql
# Average MTTR over 30 days
avg(rate(dora_restore_time_seconds_sum[30d]) / rate(dora_restore_time_seconds_count[30d]))

# P90 MTTR by service
histogram_quantile(0.90, sum(rate(dora_restore_time_seconds_bucket[30d])) by (le, service))
```

### Automated MTTR from Alertmanager

```python
# Webhook receiver that calculates MTTR from Alertmanager
from flask import Flask, request
import time

app = Flask(__name__)
active_alerts = {}

@app.route('/webhook', methods=['POST'])
def alertmanager_webhook():
    data = request.json
    for alert in data['alerts']:
        alert_id = alert['fingerprint']

        if alert['status'] == 'firing':
            active_alerts[alert_id] = time.time()

        elif alert['status'] == 'resolved' and alert_id in active_alerts:
            duration = time.time() - active_alerts.pop(alert_id)
            service = alert['labels'].get('service', 'unknown')
            restore_time.labels(
                service=service,
                severity=alert['labels'].get('severity', 'unknown')
            ).observe(duration)

    return '', 200
```

---

## 9.5 Measuring Change Failure Rate

### Definition

```
Change Failure Rate = (Failed Deployments / Total Deployments) × 100
```

A "failed deployment" is one that results in:
- A rollback.
- A hotfix deployment.
- A production incident within a defined window (e.g., 1 hour after deploy).
- A degraded service (SLO breach after deploy).

### Data Sources

| Signal | Source |
|--------|--------|
| Rollback events | Deployment tool, Kubernetes rollout undo |
| Hotfix deployments | Git branch naming convention (`hotfix/*`) |
| Post-deploy incidents | Incident management correlated with deploy time |
| SLO breach after deploy | Monitoring system (Prometheus, Datadog) |

### Implementation

```python
from prometheus_client import Counter

deployment_outcomes = Counter(
    'dora_deployment_outcomes_total',
    'Deployment outcomes for change failure rate',
    ['service', 'outcome']  # outcome: success, failure, rollback
)

# On successful deployment (no issues within 1 hour)
deployment_outcomes.labels(service='payment-api', outcome='success').inc()

# On failed deployment (rollback or incident)
deployment_outcomes.labels(service='payment-api', outcome='failure').inc()
```

### PromQL Queries

```promql
# Change failure rate (30-day window)
sum(increase(dora_deployment_outcomes_total{outcome="failure"}[30d])) by (service) /
sum(increase(dora_deployment_outcomes_total[30d])) by (service)

# Change failure rate trend (weekly)
sum(increase(dora_deployment_outcomes_total{outcome="failure"}[7d])) by (service) /
sum(increase(dora_deployment_outcomes_total[7d])) by (service)
```

---

## 9.6 Pipeline Failures vs Application Failures

Understanding the difference is essential for routing alerts and measuring DORA metrics correctly.

### Classification

| Type | Definition | Examples | Impact on DORA |
|------|-----------|----------|---------------|
| **Pipeline Failure** | CI/CD pipeline fails before code reaches production | Build error, test failure, lint failure, infra provisioning error, approval timeout | Increases **lead time** (delays delivery). Does NOT affect **change failure rate** (code never reached production). |
| **Application Failure** | Deployed code causes issues in production | Runtime error, performance degradation, data corruption, SLO breach | Increases **change failure rate** and **MTTR**. |

### Pipeline Failure Categories

```
Pipeline Failure
├── Build Failures
│   ├── Compilation error
│   ├── Dependency resolution failure
│   └── Docker build failure
├── Test Failures
│   ├── Unit test failure
│   ├── Integration test failure
│   └── E2E test failure
├── Infrastructure Failures
│   ├── Runner/agent unavailable
│   ├── Registry push failure
│   └── Terraform apply failure
├── Policy Failures
│   ├── Security scan violation
│   ├── License compliance failure
│   └── Approval timeout
└── Deployment Failures
    ├── Kubernetes rollout failure
    ├── Health check failure during deploy
    └── Canary analysis failure
```

### Application Failure Categories

```
Application Failure
├── Functional Failures
│   ├── HTTP 5xx errors
│   ├── Business logic errors
│   └── Data integrity issues
├── Performance Failures
│   ├── Latency SLO breach
│   ├── Throughput degradation
│   └── Resource exhaustion (OOM, CPU)
├── Availability Failures
│   ├── Service crash/restart loop
│   ├── Dependency failure cascade
│   └── DNS/network issues
└── Security Failures
    ├── Vulnerability exploited
    ├── Data breach
    └── Authentication/authorization bypass
```

### Monitoring Each Type

#### Pipeline Failure Metrics

```python
pipeline_failures = Counter(
    'pipeline_failures_total',
    'CI/CD pipeline failures',
    ['service', 'stage', 'failure_type']
)

# Examples
pipeline_failures.labels(service='api', stage='build', failure_type='compilation').inc()
pipeline_failures.labels(service='api', stage='test', failure_type='unit_test').inc()
pipeline_failures.labels(service='api', stage='deploy', failure_type='health_check').inc()
```

#### Application Failure Metrics

```python
app_failures = Counter(
    'application_failures_total',
    'Production application failures',
    ['service', 'failure_type', 'triggered_by']
)

# triggered_by: deployment, dependency, infrastructure, unknown
app_failures.labels(
    service='api',
    failure_type='http_5xx',
    triggered_by='deployment'
).inc()
```

### Correlation: Deployment → Failure

```promql
# Detect error rate spike within 30 minutes of deployment
(
  rate(http_requests_total{status=~"5.."}[5m]) /
  rate(http_requests_total[5m])
)
and on(service)
(increase(deployments_total{result="success"}[30m]) > 0)
```

### Alert Routing

| Failure Type | Alert Channel | Responder |
|-------------|---------------|-----------|
| Build failure | Slack #ci-failures | Developer who committed |
| Test failure | Slack #ci-failures | Developer who committed |
| Deploy failure (pre-prod) | Slack #ci-failures | DevOps/Platform team |
| Deploy failure (prod) | PagerDuty | On-call engineer |
| Application failure (post-deploy) | PagerDuty | On-call engineer + deployer |
| Application failure (no recent deploy) | PagerDuty | On-call engineer |

---

## 9.7 DORA Dashboard

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  DORA Metrics — $team / $service                            │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Summary (Stat panels)                               │
│  [Deploy Freq]  [Lead Time P50]  [MTTR P50]  [CFR %]       │
│  [this week]    [this week]      [30 days]   [30 days]      │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Trends (Time Series)                                │
│  [Deploy Frequency — weekly]  [Lead Time — weekly P50/P90]  │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Trends (Time Series)                                │
│  [MTTR — monthly]             [Change Failure Rate — weekly]│
├─────────────────────────────────────────────────────────────┤
│  Row 4: Pipeline Health                                     │
│  [Pipeline Success Rate]  [Failures by Stage]  [Queue Time] │
├─────────────────────────────────────────────────────────────┤
│  Row 5: Deployments (Table)                                 │
│  [Recent Deployments: service, version, time, result, CFR]  │
├─────────────────────────────────────────────────────────────┤
│  Row 6: Incidents (Table)                                   │
│  [Recent Incidents: service, severity, MTTD, MTTR, cause]   │
└─────────────────────────────────────────────────────────────┘
```

### Grafana Dashboard JSON (Key Panels)

```json
{
  "panels": [
    {
      "title": "Deployment Frequency (this week)",
      "type": "stat",
      "targets": [{
        "expr": "sum(increase(deployments_total{environment='production', service=~'$service'}[7d]))"
      }],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "steps": [
              {"color": "red", "value": 0},
              {"color": "yellow", "value": 1},
              {"color": "green", "value": 5}
            ]
          }
        }
      }
    },
    {
      "title": "Lead Time P50 (this week)",
      "type": "stat",
      "targets": [{
        "expr": "histogram_quantile(0.50, sum(rate(dora_lead_time_seconds_bucket{service=~'$service'}[7d])) by (le))"
      }],
      "fieldConfig": {
        "defaults": {
          "unit": "s",
          "thresholds": {
            "steps": [
              {"color": "green", "value": 0},
              {"color": "yellow", "value": 3600},
              {"color": "red", "value": 86400}
            ]
          }
        }
      }
    },
    {
      "title": "Change Failure Rate (30d)",
      "type": "stat",
      "targets": [{
        "expr": "sum(increase(dora_deployment_outcomes_total{outcome='failure', service=~'$service'}[30d])) / sum(increase(dora_deployment_outcomes_total{service=~'$service'}[30d]))"
      }],
      "fieldConfig": {
        "defaults": {
          "unit": "percentunit",
          "thresholds": {
            "steps": [
              {"color": "green", "value": 0},
              {"color": "yellow", "value": 0.15},
              {"color": "red", "value": 0.30}
            ]
          }
        }
      }
    }
  ]
}
```

---

## 9.8 Automating DORA Data Collection

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Record commit timestamp
        run: echo "COMMIT_TS=$(git log -1 --format=%ct)" >> $GITHUB_ENV

      - name: Build and test
        run: |
          make build
          make test

      - name: Deploy
        run: make deploy-production

      - name: Record DORA metrics
        if: always()
        run: |
          DEPLOY_TS=$(date +%s)
          LEAD_TIME=$((DEPLOY_TS - COMMIT_TS))
          RESULT=${{ job.status == 'success' && 'success' || 'failure' }}

          # Push to Prometheus Pushgateway
          cat <<EOF | curl --data-binary @- http://pushgateway:9091/metrics/job/dora/service/payment-api
          dora_lead_time_seconds{service="payment-api"} ${LEAD_TIME}
          deployments_total{service="payment-api",environment="production",result="${RESULT}"} 1
          EOF
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    environment {
        COMMIT_TS = sh(script: 'git log -1 --format=%ct', returnStdout: true).trim()
    }
    stages {
        stage('Build') { steps { sh 'make build' } }
        stage('Test')  { steps { sh 'make test' } }
        stage('Deploy') { steps { sh 'make deploy-production' } }
    }
    post {
        always {
            script {
                def deployTs = System.currentTimeMillis() / 1000 as long
                def leadTime = deployTs - env.COMMIT_TS.toLong()
                def result = currentBuild.result == 'SUCCESS' ? 'success' : 'failure'

                // Send to Datadog
                sh """
                curl -X POST "https://api.datadoghq.com/api/v1/series" \
                  -H "DD-API-KEY: ${DD_API_KEY}" \
                  -d '{
                    "series": [
                      {"metric":"dora.lead_time","points":[[${deployTs},${leadTime}]],"type":"gauge","tags":["service:payment-api"]},
                      {"metric":"dora.deployments","points":[[${deployTs},1]],"type":"count","tags":["service:payment-api","result:${result}"]}
                    ]
                  }'
                """
            }
        }
    }
}
```

---

## 9.9 Exercises

### Knowledge Check

1. A team deploys 3 times per week with a 12% failure rate. What DORA performance level are they at for each metric?
2. A build fails due to a flaky test. Is this a pipeline failure or application failure? Does it affect change failure rate?
3. A deployment succeeds but causes a latency SLO breach 20 minutes later. How does this affect each DORA metric?
4. Why do elite teams have both high deployment frequency AND low change failure rate?

### Hands-On Projects

1. **Instrument a pipeline:** Add DORA metric collection to a CI/CD pipeline (Jenkins or GitHub Actions). Emit deployment frequency and lead time.
2. **Build a DORA dashboard:** Create a Grafana dashboard with all four DORA metrics, trends, and benchmarks.
3. **Classify failures:** Given 20 sample incidents, classify each as pipeline failure or application failure. Determine which affect change failure rate.
4. **Automate MTTR:** Set up an Alertmanager webhook that automatically calculates MTTR from alert firing/resolving events.
5. **Correlation:** Deploy a change that introduces errors. Show how deployment annotations on Grafana dashboards help correlate the deployment with the error spike.

---

## Next Module

→ [Module 10 — Prometheus Integrations](../10-prometheus-integrations/README.md)
