# Module 13 — ELK Stack Integrations

**Levels:** Beginner → Advanced  
**Duration:** ~15 hours  
**Prerequisites:** Module 5 (ELK Stack)

---

## 13.A ELK + Kubernetes

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Filebeat (DaemonSet — one per node)             │   │
│  │  - Reads container logs from /var/log/containers │   │
│  │  - Adds Kubernetes metadata                      │   │
│  │  - Ships to Elasticsearch or Logstash            │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Logstash (optional — for complex parsing)       │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Elasticsearch (StatefulSet or external)         │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Kibana (Deployment)                             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Deploying Filebeat as DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: filebeat
  namespace: logging
spec:
  selector:
    matchLabels:
      app: filebeat
  template:
    metadata:
      labels:
        app: filebeat
    spec:
      serviceAccountName: filebeat
      containers:
        - name: filebeat
          image: docker.elastic.co/beats/filebeat:8.12.0
          args: ["-c", "/etc/filebeat/filebeat.yml", "-e"]
          env:
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          volumeMounts:
            - name: config
              mountPath: /etc/filebeat
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: filebeat-config
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
```

### Filebeat Configuration for Kubernetes

```yaml
# filebeat.yml (ConfigMap)
filebeat.inputs:
  - type: container
    paths:
      - /var/log/containers/*.log
    processors:
      - add_kubernetes_metadata:
          host: ${NODE_NAME}
          matchers:
            - logs_path:
                logs_path: "/var/log/containers/"

filebeat.autodiscover:
  providers:
    - type: kubernetes
      node: ${NODE_NAME}
      hints.enabled: true
      hints.default_config:
        type: container
        paths:
          - /var/log/containers/*${data.kubernetes.container.id}.log

processors:
  - drop_event:
      when:
        or:
          - equals:
              kubernetes.namespace: kube-system
          - equals:
              kubernetes.namespace: logging

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "k8s-logs-%{+yyyy.MM.dd}"

setup.template:
  name: "k8s-logs"
  pattern: "k8s-logs-*"
```

### What You Collect

| Log Source | How | Index Pattern |
|-----------|-----|---------------|
| **Pod stdout/stderr** | Container log files via Filebeat | `k8s-logs-*` |
| **API server audit logs** | Audit log file or webhook | `k8s-audit-*` |
| **Kubernetes events** | kube-events-exporter or Metricbeat | `k8s-events-*` |
| **Ingress controller logs** | Filebeat with nginx/traefik module | `k8s-ingress-*` |

### Kubernetes Metadata Enrichment

Filebeat's `add_kubernetes_metadata` processor adds:

| Field | Example |
|-------|---------|
| `kubernetes.pod.name` | `payment-api-7d8f9c6b4-x2k9l` |
| `kubernetes.namespace` | `production` |
| `kubernetes.container.name` | `payment-api` |
| `kubernetes.node.name` | `ip-10-0-1-42` |
| `kubernetes.labels.app` | `payment-api` |
| `kubernetes.labels.version` | `2.3.1` |
| `kubernetes.deployment.name` | `payment-api` |

### Kibana Dashboards for Kubernetes

#### Log Volume by Namespace

```json
{
  "visualization": "lens",
  "query": "*",
  "breakdown": "kubernetes.namespace",
  "metric": "count",
  "time_interval": "auto"
}
```

#### Error Logs by Pod

```
kubernetes.namespace: "production" AND (level: "ERROR" OR level: "FATAL")
| Group by: kubernetes.pod.name
| Metric: Count
```

#### Pod Restart Correlation

Search for OOMKilled or CrashLoopBackOff events alongside application error logs to find root causes.

---

## 13.B ELK + AWS

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      AWS Account                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │CloudTrail│  │VPC Flow  │  │ CloudWatch Logs      │  │
│  │  Logs    │  │  Logs    │  │ (Lambda, RDS, etc.)  │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │             │                   │               │
│       ▼             ▼                   ▼               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  S3 Bucket / CloudWatch Logs                     │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                   │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Logstash (with S3 input / CloudWatch input)     │   │
│  │  OR                                              │   │
│  │  Lambda → Elasticsearch                          │   │
│  │  OR                                              │   │
│  │  Kinesis Firehose → Elasticsearch                │   │
│  └──────────────────┬───────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │
             ┌────────▼────────┐
             │  Elasticsearch  │
             │  (self-hosted   │
             │   or OpenSearch)│
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │     Kibana      │
             └─────────────────┘
```

### CloudWatch Logs → Logstash

```ruby
# logstash-aws.conf
input {
  cloudwatch_logs {
    log_group: ["/aws/lambda/payment-processor", "/aws/rds/instance/prod-db/slowquery"]
    region: "us-east-1"
    start_position: "end"
    interval: 60
    codec: "plain"
  }
}

filter {
  # Parse Lambda logs
  if [log_group] =~ /lambda/ {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp}\t%{UUID:request_id}\t%{LOGLEVEL:level}\t%{GREEDYDATA:log_message}" }
    }
    mutate {
      add_field => { "source" => "lambda" }
    }
  }

  # Parse RDS slow query logs
  if [log_group] =~ /slowquery/ {
    grok {
      match => { "message" => "# Time: %{TIMESTAMP_ISO8601:query_time}\n# User@Host: %{DATA:user}\n# Query_time: %{NUMBER:query_duration:float}" }
    }
    mutate {
      add_field => { "source" => "rds" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "aws-logs-%{source}-%{+YYYY.MM.dd}"
  }
}
```

### CloudTrail Logs → Elasticsearch

```ruby
# logstash-cloudtrail.conf
input {
  s3 {
    bucket: "my-cloudtrail-bucket"
    region: "us-east-1"
    prefix: "AWSLogs/"
    codec: "json"
    type: "cloudtrail"
  }
}

filter {
  json {
    source => "message"
  }

  # CloudTrail logs contain a Records array
  split {
    field => "Records"
  }

  mutate {
    rename => { "[Records]" => "cloudtrail" }
  }

  date {
    match => ["[cloudtrail][eventTime]", "ISO8601"]
  }

  # Tag security-relevant events
  if [cloudtrail][eventName] in ["ConsoleLogin", "CreateUser", "AttachUserPolicy", "PutBucketPolicy", "AuthorizeSecurityGroupIngress"] {
    mutate {
      add_tag => ["security_event"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "cloudtrail-%{+YYYY.MM.dd}"
  }
}
```

### VPC Flow Logs → Elasticsearch

```ruby
# logstash-vpc-flow.conf
input {
  cloudwatch_logs {
    log_group: ["/vpc/flow-logs"]
    region: "us-east-1"
  }
}

filter {
  grok {
    match => {
      "message" => "%{NUMBER:version} %{NUMBER:account_id} %{DATA:interface_id} %{IP:src_addr} %{IP:dst_addr} %{NUMBER:src_port:int} %{NUMBER:dst_port:int} %{NUMBER:protocol:int} %{NUMBER:packets:int} %{NUMBER:bytes:int} %{NUMBER:start:int} %{NUMBER:end:int} %{WORD:action} %{WORD:log_status}"
    }
  }

  # Map protocol numbers to names
  translate {
    field => "protocol"
    destination => "protocol_name"
    dictionary => {
      "6"  => "TCP"
      "17" => "UDP"
      "1"  => "ICMP"
    }
  }

  # GeoIP for external IPs
  if [src_addr] !~ /^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)/ {
    geoip {
      source => "src_addr"
    }
  }

  date {
    match => ["start", "UNIX"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "vpc-flow-%{+YYYY.MM.dd}"
  }
}
```

### Security Monitoring with Kibana

#### Security Event Queries

```
# Failed console logins
cloudtrail.eventName: "ConsoleLogin" AND cloudtrail.responseElements.ConsoleLogin: "Failure"

# Root account usage
cloudtrail.userIdentity.type: "Root"

# Security group changes
cloudtrail.eventName: ("AuthorizeSecurityGroupIngress" OR "RevokeSecurityGroupIngress")

# IAM policy changes
cloudtrail.eventName: ("AttachUserPolicy" OR "DetachUserPolicy" OR "PutUserPolicy")

# S3 bucket policy changes
cloudtrail.eventName: "PutBucketPolicy"

# Rejected VPC traffic
action: "REJECT"
```

#### Kibana Alert Rules

| Rule | Query | Threshold |
|------|-------|-----------|
| Failed logins | `cloudtrail.eventName: ConsoleLogin AND responseElements.ConsoleLogin: Failure` | > 5 in 10 min |
| Root account usage | `cloudtrail.userIdentity.type: Root` | > 0 in 1 hour |
| SG opened to 0.0.0.0/0 | `cloudtrail.eventName: AuthorizeSecurityGroupIngress AND requestParameters.cidrIp: "0.0.0.0/0"` | > 0 |
| Rejected traffic spike | `action: REJECT` | > 1000 in 5 min |

---

## 13.C ELK + Jenkins

### Setup

#### Send Jenkins Logs to Logstash

**Option 1: Logstash Plugin for Jenkins**

1. Install **Logstash Plugin** in Jenkins.
2. Configure: **Manage Jenkins → System → Logstash**:
   - Indexer type: Logstash TCP.
   - Host: `logstash`.
   - Port: `5000`.

**Option 2: Filebeat on Jenkins Server**

```yaml
# filebeat.yml on Jenkins server
filebeat.inputs:
  - type: log
    paths:
      - /var/log/jenkins/jenkins.log
    fields:
      type: jenkins-system
    multiline:
      pattern: '^\d{4}-\d{2}-\d{2}'
      negate: true
      match: after

  - type: log
    paths:
      - /var/lib/jenkins/jobs/*/builds/*/log
    fields:
      type: jenkins-build
    multiline:
      pattern: '^\[Pipeline\]|^\+'
      negate: true
      match: after

output.logstash:
  hosts: ["logstash:5044"]
```

### Logstash Pipeline for Jenkins

```ruby
# logstash-jenkins.conf
input {
  beats {
    port => 5044
  }
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [fields][type] == "jenkins-build" {
    # Extract job name and build number from file path
    grok {
      match => {
        "log.file.path" => "/var/lib/jenkins/jobs/%{DATA:job_name}/builds/%{NUMBER:build_number}/log"
      }
    }

    # Detect build errors
    if [message] =~ /(?i)(error|exception|failed|failure)/ {
      mutate {
        add_tag => ["build_error"]
        add_field => { "log_level" => "ERROR" }
      }
    }

    # Detect test failures
    if [message] =~ /Tests run:.*Failures: [1-9]/ {
      mutate {
        add_tag => ["test_failure"]
      }
      grok {
        match => {
          "message" => "Tests run: %{NUMBER:tests_run:int}, Failures: %{NUMBER:tests_failed:int}, Errors: %{NUMBER:tests_errors:int}"
        }
      }
    }

    # Detect deployment events
    if [message] =~ /(?i)(deploying|deployed|deployment)/ {
      mutate {
        add_tag => ["deployment"]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "jenkins-%{[fields][type]}-%{+YYYY.MM.dd}"
  }
}
```

### What You Monitor

| Log Type | What to Look For |
|----------|-----------------|
| **Build logs** | Compilation errors, dependency failures, timeout |
| **Test logs** | Test failures, flaky tests, coverage drops |
| **Deployment logs** | Deploy errors, rollback events, health check failures |
| **System logs** | Jenkins OOM, plugin errors, agent disconnects |
| **Script errors** | Groovy exceptions, pipeline syntax errors |

### Kibana Dashboards for Jenkins

#### Build Failure Analysis

```
# KQL queries for Kibana

# All build errors
tags: "build_error"

# Test failures
tags: "test_failure"

# Deployment events
tags: "deployment"

# Errors by job
tags: "build_error" | Group by: job_name | Metric: Count | Sort: desc

# Build errors over time
tags: "build_error" | Date histogram: @timestamp | Interval: 1h
```

#### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Jenkins Log Analysis                                       │
├─────────────────────────────────────────────────────────────┤
│  Row 1: Overview                                            │
│  [Total Builds]  [Build Errors]  [Test Failures]            │
├─────────────────────────────────────────────────────────────┤
│  Row 2: Trends                                              │
│  [Build Errors Over Time]  [Test Failures Over Time]        │
├─────────────────────────────────────────────────────────────┤
│  Row 3: Analysis                                            │
│  [Top Failing Jobs]  [Most Common Error Messages]           │
├─────────────────────────────────────────────────────────────┤
│  Row 4: Log Stream                                          │
│  [Recent Error Logs — filterable by job, type]              │
└─────────────────────────────────────────────────────────────┘
```

---

## Exercises

### ELK + Kubernetes

1. Deploy Filebeat as a DaemonSet. Verify pod logs appear in Elasticsearch.
2. Create a Kibana data view for `k8s-logs-*`. Search for errors by namespace and pod.
3. Build a dashboard: log volume by namespace, error rate by service, recent error log stream.
4. Set up an alert for error log count > 50 in 5 minutes for any pod.
5. (Advanced) Collect API server audit logs. Create security dashboards for RBAC violations.

### ELK + AWS

1. Ingest CloudTrail logs via S3 → Logstash. Create a data view and explore events.
2. Ingest VPC Flow Logs. Build a dashboard showing rejected traffic by source IP and port.
3. Create Kibana alerts for: root account usage, security group changes, failed console logins.
4. (Advanced) Build a security operations dashboard combining CloudTrail, VPC Flow Logs, and application logs.

### ELK + Jenkins

1. Configure Filebeat or Logstash plugin to ship Jenkins build logs.
2. Create a Logstash pipeline that tags build errors, test failures, and deployment events.
3. Build a Kibana dashboard for build failure analysis.
4. Set up alerts for: build error spike, test failure in production pipeline.
5. Correlate a Jenkins deployment log with application error logs in Kibana using timestamps.

---

## Next Module

→ [Module 14 — CloudWatch Integrations](../14-cloudwatch-integrations/README.md)
