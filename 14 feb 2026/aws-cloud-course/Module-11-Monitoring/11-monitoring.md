# Module 11: Monitoring, Logging & Alerting

## 11.1 AWS Monitoring Stack

```
┌─────────────────────────────────────────────────────┐
│              AWS Monitoring Stack                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Metrics:     CloudWatch Metrics                     │
│  Logs:        CloudWatch Logs                        │
│  Alarms:      CloudWatch Alarms                      │
│  Dashboards:  CloudWatch Dashboards                  │
│  Tracing:     X-Ray                                  │
│  Audit:       CloudTrail                             │
│  Alerts:      SNS (Simple Notification Service)      │
│  Events:      EventBridge                            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 11.2 CloudWatch Metrics

CloudWatch collects metrics from all AWS services automatically.

### View EC2 Metrics

```bash
# List available metrics for EC2
aws cloudwatch list-metrics \
  --namespace AWS/EC2 \
  --dimensions Name=InstanceId,Value=i-0abcd1234 \
  --query 'Metrics[].MetricName' \
  --output table
```

**Common EC2 Metrics:**
| Metric | What It Measures | Unit |
|--------|-----------------|------|
| `CPUUtilization` | CPU usage | Percent |
| `NetworkIn` | Bytes received | Bytes |
| `NetworkOut` | Bytes sent | Bytes |
| `DiskReadOps` | Disk read operations | Count |
| `StatusCheckFailed` | Instance health | Count |

### Get Metric Data

```bash
# Get CPU utilization for last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abcd1234 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average Maximum \
  --output table
```

**Expected Output:**
```
------------------------------------------------------
|                GetMetricStatistics                  |
+---------------------+----------+-------------------+
|      Timestamp      | Average  |     Maximum       |
+---------------------+----------+-------------------+
| 2024-01-15T10:00:00 |  12.5    |      45.2         |
| 2024-01-15T10:05:00 |  15.3    |      52.1         |
| 2024-01-15T10:10:00 |  8.7     |      23.4         |
+---------------------+----------+-------------------+
```

### Custom Metrics

```bash
# Publish a custom metric
aws cloudwatch put-metric-data \
  --namespace "MyApp" \
  --metric-name "ActiveUsers" \
  --value 142 \
  --unit Count \
  --dimensions Environment=production,Service=web

# Publish with timestamp
aws cloudwatch put-metric-data \
  --namespace "MyApp" \
  --metric-data '[
    {
      "MetricName": "RequestLatency",
      "Value": 45.2,
      "Unit": "Milliseconds",
      "Dimensions": [
        {"Name": "Endpoint", "Value": "/api/users"},
        {"Name": "Method", "Value": "GET"}
      ]
    },
    {
      "MetricName": "ErrorCount",
      "Value": 3,
      "Unit": "Count",
      "Dimensions": [
        {"Name": "Endpoint", "Value": "/api/users"}
      ]
    }
  ]'
```

---

## 11.3 CloudWatch Alarms

### Create CPU Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "High-CPU-WebServer" \
  --alarm-description "CPU > 80% for 5 minutes" \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abcd1234 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts \
  --ok-actions arn:aws:sns:us-east-1:123456789012:alerts \
  --treat-missing-data notBreaching
```

**Command Breakdown:**
| Flag | Meaning |
|------|---------|
| `--period 300` | Check every 5 minutes |
| `--threshold 80` | Trigger at 80% |
| `--evaluation-periods 2` | Must breach 2 consecutive periods |
| `--alarm-actions` | SNS topic to notify when alarm triggers |
| `--ok-actions` | SNS topic to notify when alarm recovers |

### Create Billing Alarm

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "Monthly-Billing-Alert" \
  --alarm-description "Estimated charges exceed $50" \
  --namespace AWS/Billing \
  --metric-name EstimatedCharges \
  --dimensions Name=Currency,Value=USD \
  --statistic Maximum \
  --period 21600 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:billing-alerts \
  --region us-east-1
```

### List and Manage Alarms

```bash
# List all alarms
aws cloudwatch describe-alarms \
  --query 'MetricAlarms[].{Name:AlarmName,State:StateValue,Metric:MetricName}' \
  --output table

# Get alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name "High-CPU-WebServer" \
  --history-item-type StateUpdate

# Delete alarm
aws cloudwatch delete-alarms --alarm-names "High-CPU-WebServer"
```

---

## 11.4 CloudWatch Logs

### Log Concepts

```
CloudWatch Logs
├── Log Group: /aws/lambda/my-function     (container for streams)
│   ├── Log Stream: 2024/01/15/[$LATEST]abc123  (sequence of events)
│   │   ├── Log Event: "START RequestId: abc..."
│   │   ├── Log Event: "Processing user: alice"
│   │   └── Log Event: "END RequestId: abc..."
│   └── Log Stream: 2024/01/15/[$LATEST]def456
└── Log Group: /ecs/myapp-web
    └── Log Stream: ecs/web/task-id
```

### Create Log Group

```bash
aws logs create-log-group \
  --log-group-name /myapp/production \
  --retention-in-days 30

# Set retention (save costs)
aws logs put-retention-policy \
  --log-group-name /myapp/production \
  --retention-in-days 30
```

### Send Log Events

```bash
# Create log stream
aws logs create-log-stream \
  --log-group-name /myapp/production \
  --log-stream-name web-server-1

# Put log events
aws logs put-log-events \
  --log-group-name /myapp/production \
  --log-stream-name web-server-1 \
  --log-events \
    timestamp=$(date +%s000),message="Application started on port 3000" \
    timestamp=$(date +%s000),message="Connected to database successfully"
```

### Search Logs (Filter Patterns)

```bash
# Search for errors in last hour
aws logs filter-log-events \
  --log-group-name /myapp/production \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000) \
  --query 'events[].{Time:timestamp,Message:message}' \
  --output table

# Search for specific patterns
aws logs filter-log-events \
  --log-group-name /myapp/production \
  --filter-pattern '{ $.statusCode = 500 }'

# Search for slow requests (latency > 1000ms)
aws logs filter-log-events \
  --log-group-name /myapp/production \
  --filter-pattern '{ $.latency > 1000 }'
```

### CloudWatch Logs Insights (SQL-like queries)

```bash
aws logs start-query \
  --log-group-name /myapp/production \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string '
    fields @timestamp, @message
    | filter @message like /ERROR/
    | sort @timestamp desc
    | limit 20
  '
```

**More Insights queries:**
```sql
-- Top 10 most frequent errors
fields @message
| filter @message like /ERROR/
| stats count(*) as errorCount by @message
| sort errorCount desc
| limit 10

-- Average latency by endpoint
fields @timestamp, endpoint, latency
| stats avg(latency) as avgLatency, max(latency) as maxLatency by endpoint
| sort avgLatency desc

-- Request count per minute
fields @timestamp
| stats count(*) as requestCount by bin(1m)
| sort @timestamp desc
```

### Metric Filters (Create metrics from logs)

```bash
# Create a metric from log pattern (count 500 errors)
aws logs put-metric-filter \
  --log-group-name /myapp/production \
  --filter-name "500-errors" \
  --filter-pattern '{ $.statusCode = 500 }' \
  --metric-transformations \
    metricName=Http500Errors,metricNamespace=MyApp,metricValue=1,defaultValue=0
```

---

## 11.5 SNS (Simple Notification Service)

### Create Topic and Subscribe

```bash
# Create topic
TOPIC_ARN=$(aws sns create-topic --name alerts --query 'TopicArn' --output text)

# Subscribe email
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint ops-team@company.com

# Subscribe SMS
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol sms \
  --notification-endpoint "+1234567890"

# Subscribe Lambda
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:123456789012:function:alert-handler

# Publish a message
aws sns publish \
  --topic-arn $TOPIC_ARN \
  --subject "ALERT: High CPU" \
  --message "CPU utilization exceeded 80% on web-server-1"
```

---

## 11.6 CloudTrail (Audit Logging)

CloudTrail records every API call made in your AWS account.

### Enable CloudTrail

```bash
aws cloudtrail create-trail \
  --name management-trail \
  --s3-bucket-name mycompany-cloudtrail-logs \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --include-global-service-events

aws cloudtrail start-logging --name management-trail
```

### Search CloudTrail Events

```bash
# Who launched EC2 instances in the last 24 hours?
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --start-time $(date -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --query 'Events[].{Time:EventTime,User:Username,Event:EventName}' \
  --output table

# Who deleted an S3 bucket?
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteBucket \
  --output table

# All actions by a specific user
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=alice \
  --start-time $(date -d '7 days ago' +%Y-%m-%dT%H:%M:%S) \
  --output table
```

---

## 11.7 CloudWatch Dashboards

```bash
aws cloudwatch put-dashboard \
  --dashboard-name "Production-Overview" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0, "y": 0, "width": 12, "height": 6,
        "properties": {
          "title": "EC2 CPU Utilization",
          "metrics": [
            ["AWS/EC2", "CPUUtilization", "InstanceId", "i-0abcd1234"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1"
        }
      },
      {
        "type": "metric",
        "x": 12, "y": 0, "width": 12, "height": 6,
        "properties": {
          "title": "ALB Request Count",
          "metrics": [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/my-alb/1234"]
          ],
          "period": 60,
          "stat": "Sum"
        }
      },
      {
        "type": "log",
        "x": 0, "y": 6, "width": 24, "height": 6,
        "properties": {
          "title": "Recent Errors",
          "query": "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
          "region": "us-east-1",
          "stacked": false,
          "view": "table"
        }
      }
    ]
  }'
```

---

## 11.8 Industry Project: Complete Monitoring Setup

```bash
#!/bin/bash
# === Production Monitoring Setup ===

APP="myapp"
REGION="us-east-1"
ACCOUNT_ID="123456789012"

# --- SNS Topics ---
CRITICAL_TOPIC=$(aws sns create-topic --name ${APP}-critical --query 'TopicArn' --output text)
WARNING_TOPIC=$(aws sns create-topic --name ${APP}-warning --query 'TopicArn' --output text)

aws sns subscribe --topic-arn $CRITICAL_TOPIC --protocol email --notification-endpoint oncall@company.com
aws sns subscribe --topic-arn $WARNING_TOPIC --protocol email --notification-endpoint devops@company.com

# --- CloudWatch Alarms ---

# CPU > 90% for 10 minutes = CRITICAL
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP}-cpu-critical" \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abcd1234 \
  --statistic Average --period 300 --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $CRITICAL_TOPIC

# CPU > 70% for 15 minutes = WARNING
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP}-cpu-warning" \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abcd1234 \
  --statistic Average --period 300 --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions $WARNING_TOPIC

# RDS connections > 80% = WARNING
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP}-rds-connections" \
  --namespace AWS/RDS --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=${APP}-database \
  --statistic Average --period 300 --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $WARNING_TOPIC

# ALB 5xx errors > 10 in 5 minutes = CRITICAL
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP}-alb-5xx" \
  --namespace AWS/ApplicationELB --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/${APP}-alb/1234 \
  --statistic Sum --period 300 --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions $CRITICAL_TOPIC

# Billing > $100
aws cloudwatch put-metric-alarm \
  --alarm-name "${APP}-billing-100" \
  --namespace AWS/Billing --metric-name EstimatedCharges \
  --dimensions Name=Currency,Value=USD \
  --statistic Maximum --period 21600 --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions $CRITICAL_TOPIC \
  --region us-east-1

# --- Log Groups with Retention ---
for group in "/ecs/${APP}" "/${APP}/api" "/${APP}/errors"; do
  aws logs create-log-group --log-group-name $group 2>/dev/null
  aws logs put-retention-policy --log-group-name $group --retention-in-days 30
done

# --- Metric Filters ---
aws logs put-metric-filter \
  --log-group-name "/${APP}/api" \
  --filter-name "500-errors" \
  --filter-pattern '{ $.statusCode = 500 }' \
  --metric-transformations metricName=Http500Count,metricNamespace=${APP},metricValue=1,defaultValue=0

echo "Monitoring setup complete!"
echo "Critical alerts: $CRITICAL_TOPIC"
echo "Warning alerts: $WARNING_TOPIC"
```

---

## 11.9 Common Errors & Troubleshooting

### Error 1: "No data" in CloudWatch metrics
```bash
# Check if metric exists
aws cloudwatch list-metrics --namespace AWS/EC2 \
  --dimensions Name=InstanceId,Value=i-xxx

# Ensure correct time range and period
# Detailed monitoring (1-min) requires enabling:
aws ec2 monitor-instances --instance-ids i-xxx
```

### Error 2: CloudWatch Logs not appearing
```bash
# Check IAM role has CloudWatch Logs permissions
# Required policy: CloudWatchLogsFullAccess or custom:
# logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents

# Check CloudWatch agent is running (on EC2)
sudo systemctl status amazon-cloudwatch-agent
```

### Error 3: SNS email not received
```bash
# Check subscription is confirmed
aws sns list-subscriptions-by-topic --topic-arn $TOPIC_ARN

# Status should be "Confirmed", not "PendingConfirmation"
# Check spam folder for confirmation email
```

---

## 11.10 CloudWatch Unified Agent

The CloudWatch Unified Agent collects both logs and system-level metrics from EC2 instances and on-premises servers.

### Why Use It (vs. default CloudWatch)

- Default EC2 metrics: CPU, Network, Disk I/O, Status Checks (no RAM, no disk space)
- Unified Agent adds: **RAM usage, disk space, swap, netstat, processes**
- Also collects custom log files and sends them to CloudWatch Logs

```bash
# Install on Amazon Linux
sudo yum install -y amazon-cloudwatch-agent

# Run configuration wizard
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start the agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json -s
```

---

## 11.11 CloudWatch Logs Subscriptions

Stream log data in real-time to other services for processing.

```
CloudWatch Logs ──▶ Subscription Filter ──▶ Lambda (process)
                                         ──▶ Kinesis Data Streams
                                         ──▶ Kinesis Data Firehose ──▶ S3/OpenSearch
```

### Cross-Account Log Aggregation

```
Account A (CloudWatch Logs) ──▶ Subscription Filter ──▶ Kinesis (Account B)
Account C (CloudWatch Logs) ──▶ Subscription Filter ──▶ Kinesis (Account B)
                                                            └──▶ S3 (centralized)
```

---

## 11.12 CloudWatch Composite Alarms

Combine multiple alarms using AND/OR logic to reduce alarm noise.

```bash
aws cloudwatch put-composite-alarm \
  --alarm-name "HighCPU-AND-HighNetwork" \
  --alarm-rule 'ALARM("HighCPU") AND ALARM("HighNetworkIn")' \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts
```

Only triggers when BOTH CPU and network are high — avoids false positives.

---

## 11.13 Amazon EventBridge

EventBridge is a serverless event bus that connects applications using events from AWS services, SaaS apps, and custom sources.

### Event Sources

- **AWS Services**: EC2 state change, S3 upload, CodePipeline failure, GuardDuty finding
- **Custom Events**: Your application publishes events
- **SaaS Partners**: Zendesk, Datadog, Auth0

### EventBridge Rules

```bash
# Rule: trigger Lambda when EC2 instance is terminated
aws events put-rule \
  --name ec2-termination \
  --event-pattern '{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {"state": ["terminated"]}
  }'

aws events put-targets \
  --rule ec2-termination \
  --targets '[{"Id": "lambda-handler", "Arn": "arn:aws:lambda:us-east-1:123456789012:function:handle-termination"}]'
```

### EventBridge vs SNS

| Feature | EventBridge | SNS |
|---------|------------|-----|
| **Event filtering** | Advanced JSON pattern matching | Basic attribute filtering |
| **Sources** | AWS, SaaS, custom | AWS, custom |
| **Schema Registry** | Yes (discover event schemas) | No |
| **Archive & Replay** | Yes | No |
| **Best for** | Event-driven architectures | Simple pub/sub notifications |

---

## 11.14 CloudTrail Insights

CloudTrail Insights automatically detects unusual API activity in your account.

- Analyzes normal management events to create a baseline
- Alerts when write API calls deviate from the baseline
- Examples: sudden spike in S3 deletions, unusual IAM activity, burst of EC2 launches

```bash
aws cloudtrail put-insight-selectors \
  --trail-name my-trail \
  --insight-selectors '[{"InsightType": "ApiCallRateInsight"}, {"InsightType": "ApiErrorRateInsight"}]'
```

### CloudTrail Events Retention

- Management events: 90 days in Event History (free)
- For longer retention: create a Trail → deliver to S3 → query with Athena

---

## 11.15 AWS Config — Rules and Remediations

AWS Config continuously evaluates resource configurations against rules.

### Common Config Rules

| Rule | What It Checks |
|------|---------------|
| `restricted-ssh` | No security groups allow SSH from 0.0.0.0/0 |
| `s3-bucket-public-read-prohibited` | No S3 buckets are publicly readable |
| `rds-instance-public-access-check` | No RDS instances are publicly accessible |
| `encrypted-volumes` | All EBS volumes are encrypted |
| `iam-user-mfa-enabled` | All IAM users have MFA enabled |

### Auto-Remediation

```bash
# Create remediation: auto-enable S3 encryption
aws configservice put-remediation-configurations \
  --remediation-configurations '[{
    "ConfigRuleName": "s3-bucket-server-side-encryption-enabled",
    "TargetType": "SSM_DOCUMENT",
    "TargetId": "AWS-EnableS3BucketEncryption",
    "Parameters": {
      "BucketName": {"ResourceValue": {"Value": "RESOURCE_ID"}},
      "SSEAlgorithm": {"StaticValue": {"Values": ["AES256"]}}
    },
    "Automatic": true,
    "MaximumAutomaticAttempts": 3,
    "RetryAttemptSeconds": 60
  }]'
```

### CloudWatch vs CloudTrail vs Config

| Service | Purpose | Example |
|---------|---------|---------|
| **CloudWatch** | Performance monitoring, metrics, alarms | "CPU is at 90%" |
| **CloudTrail** | API audit logging (who did what) | "User X deleted bucket Y at 3pm" |
| **Config** | Resource compliance (is it configured correctly?) | "This SG allows SSH from 0.0.0.0/0" |

```bash
# CloudWatch: Check a metric
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abcdef1234567890 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Average

# CloudTrail: Look up recent API events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteBucket \
  --max-results 5

# Config: Check compliance status
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name restricted-ssh \
  --compliance-types NON_COMPLIANT
```

---

## 11.16 CloudWatch Insights & Operational Visibility

### CloudWatch Metric Streams

Near-real-time delivery of CloudWatch metrics to destinations like S3, Datadog, Splunk, New Relic via Kinesis Data Firehose.

```bash
# Create a metric stream to Datadog via Firehose
aws cloudwatch put-metric-stream \
  --name "all-metrics-to-datadog" \
  --firehose-arn arn:aws:firehose:us-east-1:123456789012:deliverystream/datadog-stream \
  --role-arn arn:aws:iam::123456789012:role/MetricStreamRole \
  --output-format opentelemetry0.7

# Expected output:
# {
#   "Arn": "arn:aws:cloudwatch:us-east-1:123456789012:metric-stream/all-metrics-to-datadog"
# }

# Filter to specific namespaces only
aws cloudwatch put-metric-stream \
  --name "ec2-rds-metrics" \
  --firehose-arn arn:aws:firehose:us-east-1:123456789012:deliverystream/datadog-stream \
  --role-arn arn:aws:iam::123456789012:role/MetricStreamRole \
  --output-format opentelemetry0.7 \
  --include-filters '[{"Namespace":"AWS/EC2"},{"Namespace":"AWS/RDS"}]'
```

### CloudWatch Container Insights

Collects, aggregates, and summarizes metrics and logs from containerized applications on ECS, EKS, Kubernetes on EC2, and Fargate. Provides per-container metrics (CPU, memory, network, disk).

```bash
# Enable Container Insights on an ECS cluster
aws ecs update-cluster-settings \
  --cluster my-cluster \
  --settings name=containerInsights,value=enabled

# Enable Container Insights on an EKS cluster
aws eks update-cluster-config \
  --name my-eks-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# Install CloudWatch agent on EKS (via Helm)
# helm install cwagent amazon-cloudwatch-observability/amazon-cloudwatch-observability \
#   --namespace amazon-cloudwatch --create-namespace \
#   --set clusterName=my-eks-cluster --set region=us-east-1

# Query Container Insights metrics
aws cloudwatch get-metric-statistics \
  --namespace ContainerInsights \
  --metric-name pod_cpu_utilization \
  --dimensions Name=ClusterName,Value=my-eks-cluster Name=Namespace,Value=production \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Average
```

### CloudWatch Lambda Insights

Detailed per-function metrics for Lambda: cold starts, duration, memory usage, CPU time, network. Runs as a Lambda Layer.

```bash
# Enable Lambda Insights by adding the layer
aws lambda update-function-configuration \
  --function-name my-function \
  --layers arn:aws:lambda:us-east-1:580247275435:layer:LambdaInsightsExtension:38

# Query Lambda Insights metrics
aws cloudwatch get-metric-statistics \
  --namespace LambdaInsights \
  --metric-name memory_utilization \
  --dimensions Name=function_name,Value=my-function \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Average

# Metrics available: cpu_total_time, memory_utilization, rx_bytes, tx_bytes,
# init_duration (cold start), used_memory_max, total_memory
```

### CloudWatch Contributor Insights

Analyze log data to identify top-N contributors. Example: find the top 10 IP addresses generating the most errors, or the top URLs consuming the most bandwidth.

```bash
# Create a Contributor Insights rule for VPC Flow Logs
aws cloudwatch put-insight-rule \
  --rule-name "top-talkers" \
  --rule-state ENABLED \
  --rule-definition '{
    "Schema": {"Name": "CloudWatchLogRule", "Version": 1},
    "LogGroupNames": ["/aws/vpc/flowlogs"],
    "LogFormat": "CLF",
    "Contribution": {
      "Keys": ["srcaddr"],
      "ValueOf": "bytes",
      "Filters": [{"Match": "action", "EqualTo": "ACCEPT"}]
    },
    "AggregateOn": "Sum"
  }'

# Get the top contributors
aws cloudwatch get-insight-rule-report \
  --rule-name "top-talkers" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 --max-contributor-count 10
```

### CloudWatch Application Insights

Automated dashboards for .NET and SQL Server applications. Detects common problems and correlates metrics, logs, and alarms.

```bash
# Create an Application Insights application
aws application-insights create-application \
  --resource-group-name my-app-resources \
  --ops-center-enabled \
  --auto-config-enabled

# List detected problems
aws application-insights list-problems \
  --resource-group-name my-app-resources \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S)
```

### Trusted Advisor

AWS account-level checks across 5 categories: cost optimization, performance, security, fault tolerance, service limits.

```bash
# List all available Trusted Advisor checks
aws support describe-trusted-advisor-checks --language en \
  --query 'checks[].{Id:id,Name:name,Category:category}' | head -30

# Run a specific check (e.g., Security Groups - Unrestricted Access)
aws support describe-trusted-advisor-check-result \
  --check-id "HCP4007jGY" \
  --query 'result.{Status:status,FlaggedResources:flaggedResources[0:3]}'

# Expected output:
# {
#   "Status": "warning",
#   "FlaggedResources": [
#     {"metadata": ["us-east-1", "sg-0abcdef", "launch-wizard-1", "tcp", "22", "0.0.0.0/0"]}
#   ]
# }

# Refresh a check
aws support refresh-trusted-advisor-check --check-id "HCP4007jGY"
```

**Free tier:** 7 core checks (S3 bucket permissions, SG unrestricted access, IAM use, MFA on root, EBS snapshots, RDS snapshots, service limits). **Business/Enterprise Support:** All 100+ checks.

### Infrastructure Composer (formerly Application Composer)

Visual designer for building serverless applications. Drag-and-drop AWS resources to generate CloudFormation/SAM templates.

```bash
# Infrastructure Composer is a visual tool in the AWS Console
# It generates SAM/CloudFormation templates like:

# template.yaml (generated by Infrastructure Composer)
# AWSTemplateFormatVersion: '2010-09-09'
# Transform: AWS::Serverless-2016-10-31
# Resources:
#   OrdersApi:
#     Type: AWS::Serverless::Api
#     Properties:
#       StageName: prod
#   ProcessOrderFunction:
#     Type: AWS::Serverless::Function
#     Properties:
#       Handler: index.handler
#       Runtime: nodejs18.x
#       Events:
#         ApiEvent:
#           Type: Api
#           Properties:
#             RestApiId: !Ref OrdersApi
#             Path: /orders
#             Method: POST
#   OrdersTable:
#     Type: AWS::DynamoDB::Table
#     Properties:
#       TableName: Orders
#       BillingMode: PAY_PER_REQUEST

# Deploy the generated template
sam deploy --template-file template.yaml --stack-name my-app --capabilities CAPABILITY_IAM
```

**Real-life use case:** A developer uses Infrastructure Composer to visually design an API Gateway → Lambda → DynamoDB architecture. The tool generates the SAM template, which is then committed to Git and deployed via CI/CD.

---

## 11.17 Key Takeaways

1. CloudWatch Metrics = numbers over time (CPU, memory, request count)
2. CloudWatch Logs = text log storage and search
3. CloudWatch Alarms = automated alerts based on metric thresholds
4. CloudTrail = audit log of every API call (who did what, when)
5. SNS = notification delivery (email, SMS, Lambda, SQS)
6. Set up billing alarms immediately to avoid surprise charges
7. Use Log Insights for SQL-like queries across log groups
8. CloudWatch Unified Agent for RAM, disk space, and custom metrics
9. EventBridge for event-driven architectures — richer filtering than SNS
10. CloudTrail Insights detects unusual API activity automatically
11. AWS Config for compliance — auto-remediate non-compliant resources
12. Composite Alarms reduce noise by combining multiple alarms with AND/OR logic
