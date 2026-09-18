# Module 12 — Datadog Integrations

**Levels:** Beginner → Advanced  
**Duration:** ~18 hours  
**Prerequisites:** Module 4 (Datadog), Module 8 (Datadog + AWS Integration)

---

## 12.A Datadog + Kubernetes

### Setup with Helm

```bash
helm repo add datadog https://helm.datadoghq.com
helm repo update

helm install datadog datadog/datadog \
  --namespace datadog \
  --create-namespace \
  --set datadog.apiKey=<DD_API_KEY> \
  --set datadog.appKey=<DD_APP_KEY> \
  --set datadog.site=datadoghq.com \
  --set datadog.clusterName=production-us-east-1 \
  --set datadog.logs.enabled=true \
  --set datadog.logs.containerCollectAll=true \
  --set datadog.apm.portEnabled=true \
  --set datadog.processAgent.enabled=true \
  --set datadog.networkMonitoring.enabled=true \
  --set datadog.clusterAgent.enabled=true \
  --set datadog.clusterAgent.metricsProvider.enabled=true
```

### Architecture in Kubernetes

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Datadog Cluster Agent (Deployment)              │   │
│  │  - Cluster-level metrics                         │   │
│  │  - External metrics for HPA                      │   │
│  │  - Orchestrator Explorer                         │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Datadog Agent (DaemonSet — one per node)        │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │   │
│  │  │ Metrics │  │  Logs   │  │  APM (Traces)   │  │   │
│  │  │ Agent   │  │  Agent  │  │  Agent          │  │   │
│  │  └─────────┘  └─────────┘  └─────────────────┘  │   │
│  │  ┌─────────────────┐  ┌──────────────────────┐   │   │
│  │  │ Process Agent   │  │ Network Agent (NPM)  │   │   │
│  │  └─────────────────┘  └──────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### What You Get

#### Pod Metrics

| Metric | Description |
|--------|-------------|
| `kubernetes.cpu.usage.total` | Pod CPU usage (nanocores) |
| `kubernetes.memory.usage` | Pod memory usage (bytes) |
| `kubernetes.memory.limits` | Pod memory limit |
| `kubernetes.cpu.requests` | Pod CPU request |
| `kubernetes.network.rx_bytes` | Pod network received |
| `kubernetes.containers.restarts` | Container restart count |
| `kubernetes.containers.state.running` | Running containers |

#### Cluster Metrics

| Metric | Description |
|--------|-------------|
| `kubernetes.pods.running` | Running pods per node |
| `kubernetes.nodes.count` | Total node count |
| `kubernetes.cpu.capacity` | Node CPU capacity |
| `kubernetes.memory.capacity` | Node memory capacity |

### Distributed Tracing in Kubernetes

#### Auto-Instrumentation with Admission Controller

```yaml
# Datadog Helm values
datadog:
  apm:
    portEnabled: true
  admissionController:
    enabled: true
    mutateUnlabelled: false  # Only instrument labeled pods
```

```yaml
# Application deployment — add label to enable auto-instrumentation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-api
spec:
  template:
    metadata:
      labels:
        admission.datadoghq.com/enabled: "true"
      annotations:
        admission.datadoghq.com/java-lib.version: "latest"
    spec:
      containers:
        - name: payment-api
          env:
            - name: DD_SERVICE
              value: payment-api
            - name: DD_ENV
              value: production
            - name: DD_VERSION
              value: "2.3.1"
```

### Container Log Collection

```yaml
# Collect logs from all containers
datadog:
  logs:
    enabled: true
    containerCollectAll: true

# Or selectively via pod annotations
# In your deployment:
metadata:
  annotations:
    ad.datadoghq.com/payment-api.logs: |
      [{
        "source": "java",
        "service": "payment-api",
        "log_processing_rules": [{
          "type": "multi_line",
          "name": "java_stacktrace",
          "pattern": "\\d{4}-\\d{2}-\\d{2}"
        }]
      }]
```

### Network Performance Monitoring (NPM)

```yaml
datadog:
  networkMonitoring:
    enabled: true
```

NPM provides:
- Service-to-service network flows.
- DNS query metrics.
- TCP retransmits and latency.
- Network topology map.

### Orchestrator Explorer

Live view of Kubernetes resources:
- Pods, Deployments, ReplicaSets, DaemonSets, StatefulSets.
- Events, CronJobs, Jobs.
- Resource YAML with live status.
- Correlate with metrics, logs, and traces.

---

## 12.B Datadog + AWS

### Setup (Recap from Module 8)

```
1. Create IAM Role with cross-account trust to Datadog.
2. Attach CloudWatch read permissions.
3. Configure in Datadog: Integrations → AWS → Add Account.
4. Deploy Datadog Forwarder Lambda for logs.
```

### Enabling AWS Integrations

| Integration | What to Enable | Key Metrics |
|-------------|---------------|-------------|
| **EC2** | Auto-enabled with AWS integration | `aws.ec2.cpuutilization`, `aws.ec2.network_in` |
| **RDS** | Enable in integration tile | `aws.rds.cpuutilization`, `aws.rds.database_connections` |
| **Lambda** | Enable + deploy Forwarder | `aws.lambda.enhanced.*` (via Forwarder) |
| **ECS** | Enable + deploy Agent | `ecs.fargate.cpu.user`, `ecs.fargate.mem.usage` |
| **EKS** | Deploy Agent via Helm | `kubernetes.*` metrics |
| **ALB/NLB** | Enable in integration tile | `aws.applicationelb.*` |
| **S3** | Enable in integration tile | `aws.s3.bucket_size_bytes` |
| **SQS** | Enable in integration tile | `aws.sqs.approximate_number_of_messages_visible` |
| **DynamoDB** | Enable in integration tile | `aws.dynamodb.consumed_read_capacity_units` |
| **ElastiCache** | Enable in integration tile | `aws.elasticache.cpuutilization` |

### CloudTrail Log Ingestion

```
CloudTrail → S3 Bucket → S3 Event → Forwarder Lambda → Datadog Logs
```

Enable for:
- Security monitoring (Cloud SIEM).
- IAM change tracking.
- API audit trail.
- Compliance requirements.

### VPC Flow Log Ingestion

```
VPC Flow Logs → CloudWatch Logs → Subscription Filter → Forwarder Lambda → Datadog Logs
```

Use for:
- Network traffic analysis.
- Security investigation.
- Rejected connection debugging.

### Unified AWS Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  AWS Infrastructure — $account / $region                    │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Compute                                             │
│  [EC2 CPU by Instance]  [ECS Task Count]  [Lambda Errors]   │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Database                                            │
│  [RDS CPU]  [RDS Connections]  [DynamoDB Throttles]         │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Networking                                          │
│  [ALB Request Rate]  [ALB 5xx]  [ALB Latency P99]          │
├─────────────────────────────────────────────────────────────┤
│  Row 4: Storage & Messaging                                 │
│  [S3 Bucket Size]  [SQS Queue Depth]  [SQS Age of Oldest]  │
├─────────────────────────────────────────────────────────────┤
│  Row 5: Cost                                                │
│  [Estimated Daily Cost]  [Cost by Service]                  │
└─────────────────────────────────────────────────────────────┘
```

### Monitors for AWS

```python
# Terraform examples
resource "datadog_monitor" "rds_cpu" {
  name    = "RDS CPU High - {{dbinstanceidentifier.name}}"
  type    = "metric alert"
  query   = "avg(last_10m):avg:aws.rds.cpuutilization{env:production} by {dbinstanceidentifier} > 85"
  message = <<-EOT
    RDS instance {{dbinstanceidentifier.name}} CPU at {{value}}%.
    @slack-aws-alerts
  EOT
  monitor_thresholds {
    critical = 85
    warning  = 70
  }
}

resource "datadog_monitor" "lambda_errors" {
  name    = "Lambda Error Rate High - {{functionname.name}}"
  type    = "metric alert"
  query   = "sum(last_5m):sum:aws.lambda.errors{env:production} by {functionname}.as_count() > 10"
  message = <<-EOT
    Lambda {{functionname.name}} has {{value}} errors in 5 minutes.
    @pagerduty-platform
  EOT
}

resource "datadog_monitor" "sqs_queue_depth" {
  name    = "SQS Queue Depth High - {{queuename.name}}"
  type    = "metric alert"
  query   = "avg(last_15m):avg:aws.sqs.approximate_number_of_messages_visible{env:production} by {queuename} > 1000"
  message = <<-EOT
    SQS queue {{queuename.name}} has {{value}} messages.
    Consumers may be falling behind.
    @slack-aws-alerts
  EOT
}
```

---

## 12.C Datadog + Jenkins

### Setup

#### Install Datadog Jenkins Plugin

1. **Manage Jenkins → Plugins → Available → Search "Datadog"**.
2. Install **Datadog Plugin**.
3. **Manage Jenkins → System → Datadog Plugin**:
   - Report with: Datadog API URL.
   - API Key: `<DD_API_KEY>`.
   - Hostname: Jenkins controller hostname.

#### Enable CI Visibility

```groovy
// Jenkinsfile — enable tracing
pipeline {
    agent any
    options {
        // Datadog CI Visibility
        datadog(collectLogs: true, tags: ["team:platform"])
    }
    stages {
        stage('Build') {
            steps { sh 'make build' }
        }
        stage('Test') {
            steps { sh 'make test' }
        }
        stage('Deploy') {
            steps { sh 'make deploy' }
        }
    }
}
```

### What You Get

#### CI Visibility

| Feature | Description |
|---------|-------------|
| **Pipeline Executions** | Every pipeline run with duration, result, stages |
| **Pipeline Traces** | Distributed trace of the entire pipeline (stages as spans) |
| **Test Visibility** | Individual test results, flaky test detection |
| **Code Coverage** | Coverage metrics per pipeline |
| **Git metadata** | Commit, branch, author linked to each execution |

#### Metrics

| Metric | Description |
|--------|-------------|
| `jenkins.job.duration` | Job execution time |
| `jenkins.job.completed` | Completed jobs (tagged with result) |
| `jenkins.job.waiting` | Time spent waiting in queue |
| `jenkins.executor.count` | Total executors |
| `jenkins.executor.in_use` | Busy executors |
| `jenkins.queue.size` | Queue length |
| `jenkins.node.count` | Agent node count |
| `jenkins.node.online` | Online agent nodes |

### CI Visibility Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  CI/CD Pipeline — Jenkins                                   │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Overview                                            │
│  [Pipeline Success Rate]  [Avg Duration]  [Queue Wait]      │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Pipeline Trends                                     │
│  [Executions Over Time — pass/fail]  [Duration Trend]       │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Test Performance                                    │
│  [Test Pass Rate]  [Flaky Tests]  [Slowest Tests]           │
├─────────────────────────────────────────────────────────────┤
│  Row 4: Infrastructure                                      │
│  [Executor Utilization]  [Node Status]  [Queue Depth]       │
├─────────────────────────────────────────────────────────────┤
│  Row 5: Failure Analysis                                    │
│  [Top Failing Pipelines]  [Failure Root Causes]             │
└─────────────────────────────────────────────────────────────┘
```

### Monitors for Jenkins

```python
# Pipeline failure rate
resource "datadog_monitor" "jenkins_failure_rate" {
  name    = "Jenkins Pipeline Failure Rate High"
  type    = "metric alert"
  query   = <<-EOT
    sum(last_1h):sum:jenkins.job.completed{result:failure}.as_count() /
    sum:jenkins.job.completed{*}.as_count() > 0.3
  EOT
  message = <<-EOT
    Jenkins pipeline failure rate is {{value | humanize_percentage}}.
    Check recent commits and test results.
    @slack-ci-alerts
  EOT
}

# Queue wait time
resource "datadog_monitor" "jenkins_queue" {
  name    = "Jenkins Queue Wait Time High"
  type    = "metric alert"
  query   = "avg(last_15m):avg:jenkins.job.waiting{*} > 300000"
  message = <<-EOT
    Jenkins jobs waiting {{value}}ms in queue.
    Consider adding more executors.
    @slack-ci-alerts
  EOT
}
```

### Correlating Deployments with Application Performance

```
Jenkins Deploy → Datadog Event → Overlay on APM Dashboard
```

```groovy
// Post-deploy step in Jenkinsfile
post {
    success {
        script {
            sh """
            curl -X POST "https://api.datadoghq.com/api/v1/events" \
              -H "DD-API-KEY: ${DD_API_KEY}" \
              -d '{
                "title": "Deployment: ${SERVICE_NAME} v${VERSION}",
                "text": "Build #${BUILD_NUMBER} deployed to production",
                "alert_type": "info",
                "tags": [
                  "service:${SERVICE_NAME}",
                  "env:production",
                  "version:${VERSION}",
                  "event:deployment"
                ]
              }'
            """
        }
    }
}
```

---

## Exercises

### Datadog + Kubernetes

1. Deploy the Datadog Agent via Helm with APM, logs, and NPM enabled.
2. Instrument an application with auto-instrumentation. View traces in APM.
3. Use Orchestrator Explorer to inspect live pod state. Correlate with metrics.
4. Create monitors for: pod restarts, deployment replicas unavailable, node CPU > 80%.
5. (Advanced) Set up NPM. Identify service-to-service network flows and DNS query patterns.

### Datadog + AWS

1. Enable 5 AWS integrations (EC2, RDS, Lambda, ALB, SQS). Verify metrics appear.
2. Deploy the Forwarder Lambda. Ingest CloudTrail and VPC Flow Logs.
3. Build a unified AWS dashboard with compute, database, networking, and cost panels.
4. Create monitors for: RDS CPU, Lambda errors, SQS queue depth, ALB 5xx rate.
5. (Advanced) Set up Cloud SIEM with CloudTrail logs. Create a detection rule for unauthorized API calls.

### Datadog + Jenkins

1. Install the Datadog Jenkins plugin. Enable CI Visibility.
2. Run 10 pipeline executions. Analyze success rate, duration, and test results in CI Visibility.
3. Create monitors for pipeline failure rate and queue wait time.
4. Send deployment events from Jenkins. Verify they appear as overlays on APM dashboards.
5. Build a DORA metrics dashboard combining Jenkins CI data with production incident data.

---

## Next Module

→ [Module 13 — ELK Stack Integrations](../13-elk-integrations/README.md)
