# Module 14 — CloudWatch Integrations

**Levels:** Beginner → Advanced  
**Duration:** ~15 hours  
**Prerequisites:** Module 6 (AWS CloudWatch)

---

## 14.A CloudWatch + Kubernetes (EKS)

### Setup: Container Insights

Container Insights provides metrics and logs for EKS clusters using the CloudWatch Agent and Fluent Bit.

```
┌─────────────────────────────────────────────────────────┐
│                      EKS Cluster                        │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  CloudWatch Agent (DaemonSet)                    │   │
│  │  - Collects node and pod metrics                 │   │
│  │  - Sends to CloudWatch Metrics                   │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────┼───────────────────────────┐   │
│  │  Fluent Bit (DaemonSet)                          │   │
│  │  - Collects container logs                       │   │
│  │  - Sends to CloudWatch Logs                      │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │
                 ┌────────▼────────┐
                 │   CloudWatch    │
                 │  Metrics + Logs │
                 │  + Insights     │
                 └─────────────────┘
```

#### Installation

```bash
# Using the EKS add-on (recommended)
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name amazon-cloudwatch-observability \
  --addon-version v1.5.0-eksbuild.1

# Or using the quick-start manifest
ClusterName=my-cluster
RegionName=us-east-1
FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'

curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonSet/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | \
  sed "s/{{cluster_name}}/${ClusterName}/g;s/{{region_name}}/${RegionName}/g;s/{{http_server_toggle}}/On/g;s/{{http_server_port}}/${FluentBitHttpPort}/g;s/{{read_from_head}}/${FluentBitReadFromHead}/g" | \
  kubectl apply -f -
```

#### IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "ec2:DescribeVolumes",
        "ec2:DescribeTags",
        "ecs:ListClusters",
        "ecs:ListContainerInstances",
        "ecs:DescribeContainerInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

### Container Insights Metrics

| Metric | Namespace | Description |
|--------|-----------|-------------|
| `node_cpu_utilization` | `ContainerInsights` | Node CPU % |
| `node_memory_utilization` | `ContainerInsights` | Node memory % |
| `node_filesystem_utilization` | `ContainerInsights` | Node disk % |
| `node_network_total_bytes` | `ContainerInsights` | Node network bytes |
| `pod_cpu_utilization` | `ContainerInsights` | Pod CPU % |
| `pod_memory_utilization` | `ContainerInsights` | Pod memory % |
| `pod_network_rx_bytes` | `ContainerInsights` | Pod network received |
| `pod_number_of_container_restarts` | `ContainerInsights` | Container restarts |
| `cluster_failed_node_count` | `ContainerInsights` | Failed nodes |
| `service_number_of_running_pods` | `ContainerInsights` | Running pods per service |

### Container Insights Log Groups

| Log Group | Content |
|-----------|---------|
| `/aws/containerinsights/<cluster>/application` | Container stdout/stderr |
| `/aws/containerinsights/<cluster>/host` | Node system logs |
| `/aws/containerinsights/<cluster>/dataplane` | kubelet, kube-proxy logs |
| `/aws/containerinsights/<cluster>/performance` | Performance metrics (JSON) |

### Control Plane Logging

```bash
# Enable EKS control plane logging
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{
    "clusterLogging": [
      {
        "types": ["api", "audit", "authenticator", "controllerManager", "scheduler"],
        "enabled": true
      }
    ]
  }'
```

| Log Type | Log Group | Content |
|----------|-----------|---------|
| `api` | `/aws/eks/<cluster>/cluster` | API server logs |
| `audit` | `/aws/eks/<cluster>/cluster` | API audit logs |
| `authenticator` | `/aws/eks/<cluster>/cluster` | Authentication logs |
| `controllerManager` | `/aws/eks/<cluster>/cluster` | Controller manager logs |
| `scheduler` | `/aws/eks/<cluster>/cluster` | Scheduler logs |

### Logs Insights Queries for EKS

```sql
-- Pod errors by namespace
fields @timestamp, kubernetes.namespace_name, kubernetes.pod_name, @message
| filter @message like /(?i)error/
| stats count(*) as errors by kubernetes.namespace_name, kubernetes.pod_name
| sort errors desc
| limit 20

-- Container restarts
fields @timestamp, kubernetes.pod_name, kubernetes.container_name
| filter @message like /Back-off restarting/
| stats count(*) as restarts by kubernetes.pod_name
| sort restarts desc

-- API server audit: who deleted what
fields @timestamp, user.username, verb, objectRef.resource, objectRef.name
| filter verb = "delete"
| sort @timestamp desc
| limit 50

-- Node resource pressure
fields @timestamp, @message
| filter @message like /(?i)(MemoryPressure|DiskPressure|PIDPressure)/
| sort @timestamp desc
```

### CloudWatch Alarms for EKS

```bash
# Pod restart alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "EKS-Pod-Restarts-High" \
  --namespace ContainerInsights \
  --metric-name pod_number_of_container_restarts \
  --dimensions Name=ClusterName,Value=my-cluster Name=Namespace,Value=production \
  --statistic Maximum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:eks-alerts

# Node CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "EKS-Node-CPU-High" \
  --namespace ContainerInsights \
  --metric-name node_cpu_utilization \
  --dimensions Name=ClusterName,Value=my-cluster \
  --statistic Average \
  --period 300 \
  --threshold 85 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:eks-alerts
```

---

## 14.B CloudWatch + AWS Services

### Native Monitoring (No Agent Required)

Every AWS service publishes metrics to CloudWatch automatically.

#### EC2

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `CPUUtilization` | CPU usage % | > 85% for 10 min |
| `StatusCheckFailed` | Instance health | > 0 |
| `NetworkIn/Out` | Network bytes | Anomaly detection |
| `EBSWriteOps` | Disk IOPS | Near provisioned limit |

**Note:** Memory and disk require CloudWatch Agent.

#### RDS

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `CPUUtilization` | Database CPU % | > 80% for 10 min |
| `DatabaseConnections` | Active connections | > 80% of max |
| `FreeStorageSpace` | Available storage | < 20% of total |
| `ReadLatency` / `WriteLatency` | I/O latency | > 20ms |
| `ReplicaLag` | Replication delay | > 30 seconds |
| `FreeableMemory` | Available memory | < 500MB |

#### Lambda

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `Invocations` | Function calls | Anomaly detection |
| `Errors` | Function errors | > 1% of invocations |
| `Duration` | Execution time | > 80% of timeout |
| `Throttles` | Throttled invocations | > 0 |
| `ConcurrentExecutions` | Concurrent runs | > 80% of limit |
| `IteratorAge` | Stream processing lag | > 60 seconds |

#### ELB / ALB

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `RequestCount` | Total requests | Anomaly detection |
| `HTTPCode_ELB_5XX_Count` | LB errors | > 0 sustained |
| `HTTPCode_Target_5XX_Count` | Backend errors | > 1% of requests |
| `TargetResponseTime` | Backend latency | P99 > 2 seconds |
| `HealthyHostCount` | Healthy targets | < desired count |
| `UnHealthyHostCount` | Unhealthy targets | > 0 |

#### DynamoDB

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `ConsumedReadCapacityUnits` | Read usage | > 80% of provisioned |
| `ConsumedWriteCapacityUnits` | Write usage | > 80% of provisioned |
| `ThrottledRequests` | Throttled requests | > 0 |
| `SystemErrors` | DynamoDB errors | > 0 |
| `SuccessfulRequestLatency` | Request latency | P99 > 50ms |

### CloudWatch Alarms Best Practices

```bash
# Composite alarm: alert only when BOTH conditions are true
aws cloudwatch put-composite-alarm \
  --alarm-name "Production-Service-Degraded" \
  --alarm-rule 'ALARM("High-Error-Rate") AND ALARM("High-Latency")' \
  --alarm-actions arn:aws:sns:us-east-1:123456789:critical-alerts
```

### Logs Insights for AWS Services

```sql
-- Lambda cold starts
fields @timestamp, @message
| filter @message like /REPORT/
| parse @message "REPORT RequestId: * Duration: * ms Billed Duration: * ms Memory Size: * MB Max Memory Used: * MB Init Duration: * ms" as requestId, duration, billedDuration, memorySize, maxMemory, initDuration
| filter ispresent(initDuration)
| stats count(*) as cold_starts, avg(initDuration) as avg_init_ms by bin(1h)

-- RDS slow queries
fields @timestamp, @message
| filter @message like /Query_time/
| parse @message "# Query_time: * Lock_time: * Rows_sent: * Rows_examined: *" as query_time, lock_time, rows_sent, rows_examined
| filter query_time > 1
| sort query_time desc
| limit 20

-- ALB 5xx errors
fields @timestamp, elb, target_status_code, request, target_processing_time
| filter target_status_code >= 500
| stats count(*) as errors by bin(5m)
```

### Anomaly Detection

```bash
# Create anomaly detector
aws cloudwatch put-anomaly-detector \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/my-alb/xxx \
  --stat Sum

# Alarm on anomaly
aws cloudwatch put-metric-alarm \
  --alarm-name "ALB-Traffic-Anomaly" \
  --metrics '[
    {"Id":"m1","MetricStat":{"Metric":{"Namespace":"AWS/ApplicationELB","MetricName":"RequestCount","Dimensions":[{"Name":"LoadBalancer","Value":"app/my-alb/xxx"}]},"Period":300,"Stat":"Sum"}},
    {"Id":"ad1","Expression":"ANOMALY_DETECTION_BAND(m1, 2)"}
  ]' \
  --threshold-metric-id ad1 \
  --comparison-operator LessThanLowerOrGreaterThanUpperThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:anomaly-alerts
```

### CloudWatch Dashboard: AWS Services Overview

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "EC2 CPU by Instance",
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-123", {"stat": "Average"}],
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-456", {"stat": "Average"}]
        ],
        "period": 300,
        "view": "timeSeries"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "RDS Connections",
        "metrics": [
          ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "prod-db", {"stat": "Sum"}]
        ],
        "period": 60
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Lambda Errors",
        "metrics": [
          ["AWS/Lambda", "Errors", "FunctionName", "payment-processor", {"stat": "Sum"}],
          ["AWS/Lambda", "Invocations", "FunctionName", "payment-processor", {"stat": "Sum"}]
        ],
        "period": 300
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "ALB Latency P99",
        "metrics": [
          ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/my-alb/xxx", {"stat": "p99"}]
        ],
        "period": 60
      }
    }
  ]
}
```

---

## 14.C CloudWatch + Jenkins

### When Jenkins Runs on EC2

#### Install CloudWatch Agent

```bash
sudo yum install amazon-cloudwatch-agent -y

# Configure
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

#### Agent Configuration for Jenkins

```json
{
  "metrics": {
    "namespace": "Jenkins",
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"],
        "totalcpu": true
      },
      "mem": {
        "measurement": ["mem_used_percent", "mem_available"]
      },
      "disk": {
        "measurement": ["disk_used_percent"],
        "resources": ["/", "/var/lib/jenkins"]
      },
      "diskio": {
        "measurement": ["reads", "writes", "read_bytes", "write_bytes"]
      }
    },
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}",
      "AutoScalingGroupName": "${aws:AutoScalingGroupName}"
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/jenkins/jenkins.log",
            "log_group_name": "/jenkins/system",
            "log_stream_name": "{instance_id}",
            "timestamp_format": "%Y-%m-%d %H:%M:%S",
            "multi_line_start_pattern": "^\\d{4}-\\d{2}-\\d{2}"
          },
          {
            "file_path": "/var/lib/jenkins/jobs/*/builds/*/log",
            "log_group_name": "/jenkins/builds",
            "log_stream_name": "{instance_id}/{file_name}",
            "timestamp_format": "%H:%M:%S"
          }
        ]
      }
    }
  }
}
```

### What You Monitor

#### Infrastructure Metrics

| Metric | Alert Condition | Action |
|--------|----------------|--------|
| CPU usage | > 85% for 10 min | Scale up or add agents |
| Memory usage | > 90% for 5 min | Increase instance size |
| Disk usage (`/var/lib/jenkins`) | > 80% | Clean old builds, increase volume |
| Disk I/O | High write latency | Switch to gp3/io2 EBS |

#### Jenkins System Logs

```sql
-- Jenkins errors
fields @timestamp, @message
| filter @message like /(?i)(error|exception|severe)/
| sort @timestamp desc
| limit 50

-- Plugin failures
fields @timestamp, @message
| filter @message like /(?i)plugin.*fail/
| sort @timestamp desc

-- Agent disconnections
fields @timestamp, @message
| filter @message like /(?i)(agent.*disconnect|node.*offline)/
| sort @timestamp desc

-- Out of memory
fields @timestamp, @message
| filter @message like /OutOfMemoryError/
| sort @timestamp desc
```

### CloudWatch Alarms for Jenkins

```bash
# Jenkins disk usage
aws cloudwatch put-metric-alarm \
  --alarm-name "Jenkins-Disk-High" \
  --namespace CWAgent \
  --metric-name disk_used_percent \
  --dimensions Name=InstanceId,Value=i-jenkins123 Name=path,Value=/var/lib/jenkins \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:jenkins-alerts

# Jenkins memory
aws cloudwatch put-metric-alarm \
  --alarm-name "Jenkins-Memory-High" \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value=i-jenkins123 \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:jenkins-alerts
```

### Custom Metrics from Jenkins Pipeline

```groovy
// Jenkinsfile — publish custom metrics to CloudWatch
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                script {
                    def startTime = System.currentTimeMillis()
                    sh 'make build'
                    def duration = System.currentTimeMillis() - startTime

                    // Publish build duration to CloudWatch
                    sh """
                    aws cloudwatch put-metric-data \
                      --namespace Jenkins/Builds \
                      --metric-name BuildDuration \
                      --value ${duration} \
                      --unit Milliseconds \
                      --dimensions JobName=${env.JOB_NAME},Result=success
                    """
                }
            }
        }
    }
    post {
        failure {
            sh """
            aws cloudwatch put-metric-data \
              --namespace Jenkins/Builds \
              --metric-name BuildFailures \
              --value 1 \
              --unit Count \
              --dimensions JobName=${env.JOB_NAME}
            """
        }
    }
}
```

---

## Exercises

### CloudWatch + Kubernetes (EKS)

1. Enable Container Insights on an EKS cluster. Verify metrics appear in CloudWatch.
2. Enable control plane logging. Query API audit logs with Logs Insights.
3. Create alarms for: pod restarts, node CPU, failed nodes.
4. Build a CloudWatch dashboard with node and pod metrics.
5. (Advanced) Use Logs Insights to investigate a pod crash: find the error, correlate with node metrics.

### CloudWatch + AWS Services

1. Create alarms for 5 AWS services (EC2, RDS, Lambda, ALB, DynamoDB).
2. Set up anomaly detection for ALB request count and Lambda invocations.
3. Write Logs Insights queries for: Lambda cold starts, RDS slow queries, ALB errors.
4. Build a composite alarm that fires only when both error rate AND latency are high.
5. Create a CloudWatch dashboard covering all production AWS services.

### CloudWatch + Jenkins

1. Install the CloudWatch Agent on a Jenkins EC2 instance. Verify CPU, memory, and disk metrics.
2. Configure log collection for Jenkins system logs and build logs.
3. Create alarms for Jenkins disk usage and memory.
4. Publish custom build metrics from a Jenkins pipeline to CloudWatch.
5. Write Logs Insights queries to find: build errors, plugin failures, agent disconnections.

---

## Next Module

→ [Module 15 — Real-World Architecture & Correlation](../15-real-world-architecture/README.md)
