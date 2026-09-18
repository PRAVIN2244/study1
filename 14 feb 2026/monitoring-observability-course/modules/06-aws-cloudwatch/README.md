# Module 6 — Amazon CloudWatch

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~20 hours  
**Prerequisites:** Module 1 (Observability Foundations), AWS account

---

## Level 1: Beginner

### 6.1 CloudWatch Metrics

#### How Metrics Work

```
AWS Service → CloudWatch Metrics → Alarms → SNS → Email/Slack/PagerDuty
                    │
                    └──→ Dashboards
```

Every AWS service publishes metrics to CloudWatch automatically. No agent required for AWS-native metrics.

#### Metric Dimensions

| Concept | Description | Example |
|---------|-------------|---------|
| **Namespace** | Category grouping | `AWS/EC2`, `AWS/RDS`, `AWS/Lambda` |
| **Metric name** | What is measured | `CPUUtilization`, `NetworkIn` |
| **Dimension** | Key-value filter | `InstanceId=i-1234567890abcdef0` |
| **Statistic** | Aggregation function | `Average`, `Sum`, `Maximum`, `p99` |
| **Period** | Aggregation window | `60` (seconds), `300`, `3600` |

#### Key EC2 Metrics

| Metric | Description | Statistic |
|--------|-------------|-----------|
| `CPUUtilization` | CPU usage % | Average |
| `NetworkIn` / `NetworkOut` | Network bytes | Sum |
| `DiskReadOps` / `DiskWriteOps` | Disk IOPS | Sum |
| `StatusCheckFailed` | Instance health | Maximum |
| `StatusCheckFailed_Instance` | Instance-level check | Maximum |
| `StatusCheckFailed_System` | AWS infrastructure check | Maximum |

**Note:** Memory and disk usage are NOT available by default. They require the CloudWatch Agent.

### 6.2 CloudWatch Logs

#### Concepts

```
Log Event → Log Stream → Log Group
```

| Concept | Description | Example |
|---------|-------------|---------|
| **Log event** | Single log entry with timestamp and message | One line of application output |
| **Log stream** | Sequence of events from the same source | Logs from one EC2 instance |
| **Log group** | Collection of log streams with shared settings | `/aws/lambda/my-function` |

#### Sending Logs

**Lambda:** Automatic — logs go to `/aws/lambda/<function-name>`.

**EC2/ECS:** Requires CloudWatch Agent or SDK.

```json
// CloudWatch Agent config (amazon-cloudwatch-agent.json)
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/app/application.log",
            "log_group_name": "/app/production/application",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%dT%H:%M:%S"
          },
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/app/production/nginx-access",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

### 6.3 CloudWatch Agent

The CloudWatch Agent collects system-level metrics and logs from EC2 instances.

#### Installation

```bash
# Amazon Linux / RHEL
sudo yum install amazon-cloudwatch-agent

# Ubuntu / Debian
sudo apt-get install amazon-cloudwatch-agent

# Configure
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

#### Agent Metrics (Not Available Without Agent)

| Metric | Namespace | Description |
|--------|-----------|-------------|
| `mem_used_percent` | `CWAgent` | Memory usage % |
| `disk_used_percent` | `CWAgent` | Disk usage % |
| `swap_used_percent` | `CWAgent` | Swap usage % |
| `netstat_tcp_established` | `CWAgent` | TCP connections |
| `processes_total` | `CWAgent` | Total processes |

### 6.4 Basic Alarms

#### Creating a Metric Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "High-CPU-Production" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:ops-alerts \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --treat-missing-data missing
```

#### Alarm States

| State | Meaning |
|-------|---------|
| **OK** | Metric is within threshold |
| **ALARM** | Metric has breached threshold for the evaluation period |
| **INSUFFICIENT_DATA** | Not enough data to evaluate |

#### Alarm Actions

| Action | Trigger |
|--------|---------|
| **SNS notification** | Send email, SMS, or trigger Lambda |
| **Auto Scaling** | Scale in/out EC2 instances |
| **EC2 action** | Stop, terminate, reboot, or recover instance |
| **Systems Manager** | Run automation document |

### 6.5 Log Groups

#### Configuration

| Setting | Description | Recommendation |
|---------|-------------|---------------|
| **Retention** | How long to keep logs | 30 days for production, 7 days for dev |
| **KMS encryption** | Encrypt logs at rest | Enable for sensitive data |
| **Metric filters** | Extract metrics from log patterns | Use for error counting |
| **Subscription filters** | Stream logs to Lambda, Kinesis, or Elasticsearch | Use for real-time processing |

#### Log Group Management

```bash
# Create log group
aws logs create-log-group --log-group-name /app/production/api

# Set retention
aws logs put-retention-policy \
  --log-group-name /app/production/api \
  --retention-in-days 30

# Delete old log groups
aws logs delete-log-group --log-group-name /app/old-service
```

### Beginner Exercises

1. **Metrics:** Explore CloudWatch metrics for an EC2 instance. Graph CPU, network, and disk metrics.
2. **Agent:** Install the CloudWatch Agent on an EC2 instance. Verify memory and disk metrics appear.
3. **Logs:** Configure log collection for an application. View logs in the CloudWatch console.
4. **Alarm:** Create an alarm for CPU > 80%. Configure SNS email notification. Trigger the alarm with a stress test.
5. **Log groups:** Set retention policies for 3 log groups. Calculate storage cost savings.

---

## Level 2: Intermediate

### 6.6 CloudWatch Logs Insights

A query language for searching and analyzing log data.

#### Query Syntax

```sql
-- Count errors per service in the last hour
fields @timestamp, @message
| filter @message like /ERROR/
| stats count(*) as error_count by service
| sort error_count desc
| limit 20

-- P99 latency by endpoint
fields @timestamp, endpoint, duration
| stats percentile(duration, 99) as p99,
        percentile(duration, 95) as p95,
        avg(duration) as avg_duration
  by endpoint
| sort p99 desc

-- Find slow requests
fields @timestamp, @message, duration, trace_id
| filter duration > 5000
| sort duration desc
| limit 50

-- Error rate over time (5-minute bins)
fields @timestamp
| filter @message like /ERROR/
| stats count(*) as errors by bin(5m)

-- Parse unstructured logs
fields @timestamp, @message
| parse @message "* - - [*] \"* * *\" * *" as ip, timestamp, method, path, protocol, status, bytes
| filter status = "500"
| stats count(*) by path
```

#### Saved Queries

Save frequently used queries for reuse across the team.

### 6.7 Custom Metrics

#### Publishing Custom Metrics

```bash
# CLI
aws cloudwatch put-metric-data \
  --namespace "MyApp" \
  --metric-name "OrdersProcessed" \
  --value 42 \
  --unit Count \
  --dimensions Service=payment-api,Environment=production

# High-resolution metric (1-second granularity)
aws cloudwatch put-metric-data \
  --namespace "MyApp" \
  --metric-name "QueueDepth" \
  --value 15 \
  --storage-resolution 1
```

#### SDK (Python)

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='MyApp',
    MetricData=[
        {
            'MetricName': 'OrdersProcessed',
            'Timestamp': datetime.utcnow(),
            'Value': 42,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'Service', 'Value': 'payment-api'},
                {'Name': 'Environment', 'Value': 'production'}
            ]
        },
        {
            'MetricName': 'PaymentLatency',
            'Timestamp': datetime.utcnow(),
            'StatisticValues': {
                'SampleCount': 100,
                'Sum': 23456,
                'Minimum': 50,
                'Maximum': 1200
            },
            'Unit': 'Milliseconds'
        }
    ]
)
```

#### Embedded Metric Format (EMF)

Emit metrics from logs without API calls:

```python
import json

# Print structured log — CloudWatch automatically extracts metrics
print(json.dumps({
    "_aws": {
        "Timestamp": 1609459200000,
        "CloudWatchMetrics": [{
            "Namespace": "MyApp",
            "Dimensions": [["Service", "Environment"]],
            "Metrics": [
                {"Name": "ProcessingTime", "Unit": "Milliseconds"},
                {"Name": "ItemsProcessed", "Unit": "Count"}
            ]
        }]
    },
    "Service": "order-processor",
    "Environment": "production",
    "ProcessingTime": 234,
    "ItemsProcessed": 15
}))
```

### 6.8 EventBridge Integration

EventBridge (formerly CloudWatch Events) routes events between AWS services.

#### CloudWatch Alarm → EventBridge → Lambda

```json
{
  "source": ["aws.cloudwatch"],
  "detail-type": ["CloudWatch Alarm State Change"],
  "detail": {
    "alarmName": ["High-CPU-Production"],
    "state": {
      "value": ["ALARM"]
    }
  }
}
```

#### Scheduled Rules

```bash
# Run Lambda every 5 minutes
aws events put-rule \
  --name "health-check" \
  --schedule-expression "rate(5 minutes)"

# Run at specific time (cron)
aws events put-rule \
  --name "daily-report" \
  --schedule-expression "cron(0 9 * * ? *)"
```

### 6.9 Container Insights (EKS/ECS)

Container Insights provides metrics and logs for containerized workloads.

#### EKS Setup

```bash
# Install CloudWatch Agent as DaemonSet
ClusterName=my-cluster
RegionName=us-east-1
FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'

curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonSet/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | \
  sed "s/{{cluster_name}}/${ClusterName}/g" | \
  sed "s/{{region_name}}/${RegionName}/g" | \
  sed "s/{{http_server_toggle}}/On/g" | \
  sed "s/{{http_server_port}}/${FluentBitHttpPort}/g" | \
  sed "s/{{read_from_head}}/${FluentBitReadFromHead}/g" | \
  kubectl apply -f -
```

#### Container Insights Metrics

| Metric | Description |
|--------|-------------|
| `pod_cpu_utilization` | Pod CPU usage |
| `pod_memory_utilization` | Pod memory usage |
| `node_cpu_utilization` | Node CPU usage |
| `node_filesystem_utilization` | Node disk usage |
| `cluster_failed_node_count` | Failed nodes |
| `service_number_of_running_pods` | Running pods per service |

### 6.10 CloudWatch Dashboards

#### Creating Dashboards

```bash
aws cloudwatch put-dashboard \
  --dashboard-name "Production-Overview" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0, "y": 0, "width": 12, "height": 6,
        "properties": {
          "metrics": [
            ["AWS/EC2", "CPUUtilization", "InstanceId", "i-123", {"stat": "Average"}]
          ],
          "period": 300,
          "title": "EC2 CPU Utilization"
        }
      },
      {
        "type": "log",
        "x": 0, "y": 6, "width": 24, "height": 6,
        "properties": {
          "query": "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
          "region": "us-east-1",
          "title": "Recent Errors",
          "view": "table"
        }
      }
    ]
  }'
```

### 6.11 Metric Filters

Extract CloudWatch metrics from log data.

```bash
# Count HTTP 500 errors from application logs
aws logs put-metric-filter \
  --log-group-name /app/production/api \
  --filter-name "HTTP500Errors" \
  --filter-pattern '{ $.status = 500 }' \
  --metric-transformations \
    metricName=HTTP500Count,metricNamespace=MyApp,metricValue=1,defaultValue=0

# Count specific error messages
aws logs put-metric-filter \
  --log-group-name /app/production/api \
  --filter-name "PaymentFailures" \
  --filter-pattern '"payment_failed"' \
  --metric-transformations \
    metricName=PaymentFailures,metricNamespace=MyApp,metricValue=1
```

### Intermediate Exercises

1. **Logs Insights:** Write 5 queries: error count by service, P99 latency, slow requests, error rate over time, top error messages.
2. **Custom metrics:** Publish custom business metrics from an application. Create alarms on them.
3. **EMF:** Implement Embedded Metric Format in a Lambda function. Verify metrics appear without API calls.
4. **Container Insights:** Enable Container Insights for an EKS cluster. Create a dashboard with pod and node metrics.
5. **Metric filters:** Create metric filters to extract error counts from application logs. Set up alarms.

---

## Level 3: Advanced

### 6.12 Cross-Account Monitoring

#### Architecture

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Account A       │  │  Account B       │  │  Account C       │
│  (Production)    │  │  (Staging)       │  │  (Dev)           │
│                  │  │                  │  │                  │
│  CloudWatch      │  │  CloudWatch      │  │  CloudWatch      │
│  Metrics & Logs  │  │  Metrics & Logs  │  │  Metrics & Logs  │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                    │                    │
         └────────────┬───────┴────────────────────┘
                      │ Cross-account sharing
             ┌────────▼────────┐
             │  Monitoring     │
             │  Account        │
             │  (Dashboards,   │
             │   Alarms)       │
             └─────────────────┘
```

#### Setup

```bash
# In source account: Create sharing role
aws cloudwatch put-metric-stream \
  --name cross-account-stream \
  --firehose-arn arn:aws:firehose:us-east-1:MONITORING_ACCOUNT:deliverystream/metrics \
  --role-arn arn:aws:iam::SOURCE_ACCOUNT:role/CloudWatch-CrossAccount \
  --output-format opentelemetry0.7

# In monitoring account: Create cross-account dashboard
# Use account ID in metric widget source
```

#### CloudWatch Observability Access Manager (OAM)

```bash
# Create sink in monitoring account
aws oam create-sink \
  --name "central-monitoring" \
  --tags Environment=monitoring

# Create link in source account
aws oam create-link \
  --label-template "account-$AccountName" \
  --resource-types "AWS::CloudWatch::Metric" "AWS::Logs::LogGroup" "AWS::XRay::Trace" \
  --sink-identifier arn:aws:oam:us-east-1:MONITORING_ACCOUNT:sink/sink-id
```

### 6.13 Contributor Insights

Identify top contributors to a metric (e.g., top IP addresses, top error-producing endpoints).

```json
{
  "Schema": {
    "Name": "CloudWatchLogRule",
    "Version": 1
  },
  "LogGroupNames": ["/app/production/api"],
  "LogFormat": "JSON",
  "Contribution": {
    "Keys": ["$.client_ip"],
    "ValueOf": "$.bytes",
    "Filters": [
      {
        "Match": "$.status",
        "EqualTo": 500
      }
    ]
  },
  "AggregateOn": "Sum"
}
```

### 6.14 CloudWatch Synthetics

Canary functions that run on a schedule to monitor endpoints and workflows.

#### API Canary

```python
# Synthetics canary (Python)
from aws_synthetics.selenium import synthetics_webdriver as syn_webdriver
from aws_synthetics.common import synthetics_logger as logger

def api_canary():
    url = "https://api.example.com/v1/health"
    response = syn_webdriver.execute_http_request(url)

    if response.status_code != 200:
        raise Exception(f"Health check failed: {response.status_code}")

    body = response.json()
    if body.get("status") != "healthy":
        raise Exception(f"Service unhealthy: {body}")

    logger.info(f"Health check passed: {body}")

def handler(event, context):
    return api_canary()
```

#### Browser Canary

```python
from aws_synthetics.selenium import synthetics_webdriver as syn_webdriver
from selenium.webdriver.common.by import By

def browser_canary():
    browser = syn_webdriver.Chrome()
    browser.get("https://www.example.com")

    # Check page title
    assert "Example" in browser.title

    # Check login form exists
    login_button = browser.find_element(By.ID, "login-button")
    assert login_button.is_displayed()

    # Check page load time
    performance = browser.execute_script("return window.performance.timing")
    load_time = performance["loadEventEnd"] - performance["navigationStart"]
    assert load_time < 5000, f"Page load too slow: {load_time}ms"

def handler(event, context):
    return browser_canary()
```

### 6.15 Anomaly Detection

CloudWatch can create anomaly detection bands based on historical patterns.

```bash
aws cloudwatch put-anomaly-detector \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --stat Average

# Create alarm based on anomaly
aws cloudwatch put-metric-alarm \
  --alarm-name "CPU-Anomaly" \
  --metrics '[
    {
      "Id": "m1",
      "MetricStat": {
        "Metric": {
          "Namespace": "AWS/EC2",
          "MetricName": "CPUUtilization",
          "Dimensions": [{"Name": "InstanceId", "Value": "i-123"}]
        },
        "Period": 300,
        "Stat": "Average"
      }
    },
    {
      "Id": "ad1",
      "Expression": "ANOMALY_DETECTION_BAND(m1, 2)"
    }
  ]' \
  --threshold-metric-id ad1 \
  --comparison-operator LessThanLowerOrGreaterThanUpperThreshold \
  --evaluation-periods 3
```

### 6.16 Cost Optimization

#### CloudWatch Pricing Components

| Component | Cost Driver |
|-----------|------------|
| **Metrics** | $0.30/metric/month (first 10K), custom metrics add up fast |
| **Dashboards** | $3/dashboard/month |
| **Alarms** | $0.10/alarm/month (standard), $0.30 (high-resolution) |
| **Logs ingestion** | $0.50/GB ingested |
| **Logs storage** | $0.03/GB/month |
| **Logs Insights** | $0.005/GB scanned |
| **API calls** | $0.01/1000 GetMetricData calls |

#### Cost Reduction Strategies

| Strategy | Savings |
|----------|---------|
| Reduce log retention periods | Direct storage savings |
| Use log class: Infrequent Access | 50% cheaper ingestion |
| Filter logs before ingestion | Reduce ingestion volume |
| Use metric math instead of custom metrics | Avoid per-metric charges |
| Consolidate dashboards | $3/dashboard/month |
| Delete unused alarms | $0.10–0.30/alarm/month |
| Use EMF instead of PutMetricData API | Reduce API call costs |

### 6.17 Automation with Lambda

#### Auto-Remediation Pattern

```
CloudWatch Alarm → SNS → Lambda → Remediation Action
```

```python
import boto3

def handler(event, context):
    """Auto-restart unhealthy ECS tasks."""
    message = event['Records'][0]['Sns']['Message']
    alarm = json.loads(message)

    if alarm['NewStateValue'] != 'ALARM':
        return

    ecs = boto3.client('ecs')

    # Find and restart unhealthy tasks
    tasks = ecs.list_tasks(
        cluster='production',
        serviceName='api-service',
        desiredStatus='RUNNING'
    )

    for task_arn in tasks['taskArns']:
        ecs.stop_task(
            cluster='production',
            task=task_arn,
            reason='Auto-remediation: health check failed'
        )

    return {'statusCode': 200, 'body': f'Restarted {len(tasks["taskArns"])} tasks'}
```

### Advanced Exercises

1. **Cross-account:** Set up CloudWatch Observability Access Manager across 2 accounts. Create a unified dashboard.
2. **Contributor Insights:** Create rules to identify top error-producing endpoints and IP addresses.
3. **Synthetics:** Create API and browser canaries for a web application. Set up alarms on canary failures.
4. **Anomaly detection:** Enable anomaly detection for 3 metrics. Create anomaly-based alarms.
5. **Automation:** Build a Lambda-based auto-remediation for a common failure scenario.
6. **Cost audit:** Analyze CloudWatch costs. Implement 3 cost reduction strategies. Measure savings.

---

## Next Module

→ [Module 7 — AWS Network Analyzer](../07-aws-network-analyzer/README.md)
