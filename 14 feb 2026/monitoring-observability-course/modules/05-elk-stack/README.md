# Module 5 — ELK Stack (Elasticsearch, Logstash, Kibana)

**Levels:** Beginner → Intermediate → Advanced  
**Duration:** ~22 hours  
**Prerequisites:** Module 1 (Observability Foundations)

---

## Level 1: Beginner

### 5.1 Elasticsearch Cluster Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Elasticsearch Cluster                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Node 1  │  │  Node 2  │  │  Node 3  │              │
│  │ (master) │  │ (data)   │  │ (data)   │              │
│  │          │  │          │  │          │              │
│  │ Shard P0 │  │ Shard P1 │  │ Shard P2 │              │
│  │ Shard R1 │  │ Shard R2 │  │ Shard R0 │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                                         │
│  P = Primary shard    R = Replica shard                 │
└─────────────────────────────────────────────────────────┘
```

#### Node Roles

| Role | Responsibility |
|------|---------------|
| **Master** | Cluster state management, index creation/deletion, shard allocation |
| **Data** | Stores data, executes searches and aggregations |
| **Ingest** | Pre-processes documents before indexing (pipelines) |
| **Coordinating** | Routes requests, reduces search results (every node by default) |
| **ML** | Machine learning jobs (X-Pack) |

#### Index, Shard, Replica Concepts

| Concept | Description |
|---------|-------------|
| **Index** | A collection of documents (like a database table). Example: `logs-2024.01.15` |
| **Shard** | A subdivision of an index. Each shard is a Lucene index. Enables horizontal scaling. |
| **Primary shard** | The original shard. Write operations go here first. |
| **Replica shard** | A copy of a primary shard on a different node. Provides redundancy and read scaling. |
| **Document** | A single JSON record within an index. |

**Rules of thumb:**
- Each shard should be 10–50 GB.
- Avoid more than 20 shards per GB of heap.
- Replicas must be on different nodes than their primaries.

### 5.2 Installing the ELK Stack

#### Docker Compose

```yaml
version: "3.8"
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.12.0
    ports:
      - "5044:5044"    # Beats input
      - "5000:5000"    # TCP input
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  es-data:
```

#### Verify Installation

```bash
# Check Elasticsearch
curl http://localhost:9200

# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# Check Kibana
# Open http://localhost:5601
```

### 5.3 Logstash Pipeline

Logstash processes data through a pipeline: **Input → Filter → Output**.

#### Pipeline Configuration

```ruby
# /usr/share/logstash/pipeline/logstash.conf

input {
  # Receive logs from Filebeat
  beats {
    port => 5044
  }

  # Receive logs via TCP
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse syslog format
  if [type] == "syslog" {
    grok {
      match => { "message" => "%{SYSLOGTIMESTAMP:syslog_timestamp} %{SYSLOGHOST:syslog_hostname} %{DATA:syslog_program}(?:\[%{POSINT:syslog_pid}\])?: %{GREEDYDATA:syslog_message}" }
    }
    date {
      match => [ "syslog_timestamp", "MMM  d HH:mm:ss", "MMM dd HH:mm:ss" ]
    }
  }

  # Parse JSON logs
  if [type] == "json" {
    json {
      source => "message"
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "logs-%{+YYYY.MM.dd}"
  }

  # Debug output
  stdout {
    codec => rubydebug
  }
}
```

### 5.4 Grok Patterns

Grok uses named regex patterns to extract structured fields from unstructured log lines.

#### Common Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `%{IP:client_ip}` | IP address | `192.168.1.1` |
| `%{WORD:method}` | Single word | `GET` |
| `%{NUMBER:status:int}` | Number (cast to int) | `200` |
| `%{GREEDYDATA:message}` | Everything remaining | Any text |
| `%{TIMESTAMP_ISO8601:timestamp}` | ISO 8601 timestamp | `2024-01-15T10:30:00Z` |
| `%{COMBINEDAPACHELOG}` | Full Apache/Nginx log | Combined access log line |

#### Nginx Access Log Example

```ruby
# Log line:
# 192.168.1.1 - - [15/Jan/2024:10:30:00 +0000] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"

filter {
  grok {
    match => {
      "message" => '%{IPORHOST:client_ip} - - \[%{HTTPDATE:timestamp}\] "%{WORD:method} %{URIPATHPARAM:request} HTTP/%{NUMBER:http_version}" %{NUMBER:status:int} %{NUMBER:bytes:int} "%{DATA:referrer}" "%{DATA:user_agent}"'
    }
  }
  date {
    match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
    target => "@timestamp"
  }
  geoip {
    source => "client_ip"
  }
}
```

#### Testing Grok Patterns

Use Kibana's **Dev Tools → Grok Debugger** or the online tool at [grokdebugger.com](https://grokdebugger.com).

### 5.5 Kibana Basics

#### Data Views (Index Patterns)

1. **Stack Management → Data Views → Create data view**.
2. **Name:** `logs-*`.
3. **Timestamp field:** `@timestamp`.
4. This tells Kibana which Elasticsearch indices to query.

#### Discover Tab

- **Search bar:** Full-text search or KQL (Kibana Query Language).
- **Time picker:** Select time range.
- **Field list:** Available fields from the index.
- **Document table:** Individual log entries.

#### KQL Examples

```
# Simple text search
error

# Field-specific search
status: 500

# Wildcards
message: *timeout*

# Boolean operators
status: 500 AND service: api-gateway

# Range
response_time > 1000

# Exists
user_agent: *
```

#### Basic Dashboards

1. **Dashboard → Create dashboard → Add panel**.
2. **Lens:** Drag-and-drop visualization builder.
3. **Common visualizations:**
   - Line chart: Log volume over time.
   - Pie chart: Logs by status code.
   - Table: Top error messages.
   - Metric: Total error count.

### Beginner Exercises

1. **Install:** Deploy the ELK stack with Docker Compose. Verify all components are running.
2. **Logstash pipeline:** Create a pipeline that parses nginx access logs. Send test data via TCP.
3. **Grok:** Write grok patterns for 3 different log formats (syslog, Apache, custom application).
4. **Kibana:** Create a data view. Use Discover to search and filter logs.
5. **Dashboard:** Build a dashboard with 4 panels: log volume, status code distribution, top URLs, error log stream.

---

## Level 2: Intermediate

### 5.6 Beats

Beats are lightweight data shippers that send data to Logstash or Elasticsearch.

| Beat | Data Type | Use Case |
|------|-----------|----------|
| **Filebeat** | Log files | Ship application and system logs |
| **Metricbeat** | System and service metrics | Monitor infrastructure |
| **Packetbeat** | Network packets | Network traffic analysis |
| **Heartbeat** | Uptime data | Service availability monitoring |
| **Auditbeat** | Audit events | Security auditing |
| **Winlogbeat** | Windows event logs | Windows monitoring |

#### Filebeat Configuration

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/nginx/access.log
    fields:
      type: nginx-access
    fields_under_root: true

  - type: log
    enabled: true
    paths:
      - /var/log/app/*.log
    multiline:
      pattern: '^\d{4}-\d{2}-\d{2}'
      negate: true
      match: after
    fields:
      type: application

  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    processors:
      - add_docker_metadata: ~

output.logstash:
  hosts: ["logstash:5044"]

# Or send directly to Elasticsearch
# output.elasticsearch:
#   hosts: ["elasticsearch:9200"]
#   index: "filebeat-%{+yyyy.MM.dd}"
```

#### Metricbeat Configuration

```yaml
# metricbeat.yml
metricbeat.modules:
  - module: system
    metricsets: ["cpu", "memory", "network", "diskio", "filesystem"]
    period: 10s

  - module: docker
    metricsets: ["container", "cpu", "memory", "network"]
    hosts: ["unix:///var/run/docker.sock"]
    period: 10s

  - module: nginx
    metricsets: ["stubstatus"]
    hosts: ["http://nginx:80"]
    period: 10s

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

### 5.7 Index Lifecycle Management (ILM)

ILM automates index management through phases.

#### Lifecycle Phases

```
Hot → Warm → Cold → Frozen → Delete
```

| Phase | Purpose | Typical Duration |
|-------|---------|-----------------|
| **Hot** | Active indexing and search. Fast storage (SSD). | 0–7 days |
| **Warm** | Read-only. Reduced replicas. Slower storage acceptable. | 7–30 days |
| **Cold** | Infrequent access. Minimal resources. | 30–90 days |
| **Frozen** | Rarely accessed. Searchable snapshots. | 90–365 days |
| **Delete** | Remove index. | After retention period |

#### ILM Policy

```json
PUT _ilm/policy/logs-policy
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "1d"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "set_priority": {
            "priority": 0
          },
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

#### Apply ILM to Index Template

```json
PUT _index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "index.lifecycle.name": "logs-policy",
      "index.lifecycle.rollover_alias": "logs",
      "number_of_shards": 3,
      "number_of_replicas": 1
    }
  }
}
```

### 5.8 Log Parsing Strategies

#### Structured Logging (Preferred)

Application emits JSON logs — no parsing needed.

```json
{"timestamp":"2024-01-15T10:30:00Z","level":"ERROR","service":"payment-api","trace_id":"abc123","message":"Payment failed","error":"card_declined","user_id":"u-456"}
```

#### Ingest Pipelines (Elasticsearch-side parsing)

```json
PUT _ingest/pipeline/nginx-pipeline
{
  "description": "Parse nginx access logs",
  "processors": [
    {
      "grok": {
        "field": "message",
        "patterns": ["%{COMBINEDAPACHELOG}"]
      }
    },
    {
      "date": {
        "field": "timestamp",
        "formats": ["dd/MMM/yyyy:HH:mm:ss Z"]
      }
    },
    {
      "convert": {
        "field": "response",
        "type": "integer"
      }
    },
    {
      "geoip": {
        "field": "clientip"
      }
    },
    {
      "user_agent": {
        "field": "agent"
      }
    },
    {
      "remove": {
        "field": ["message", "agent"]
      }
    }
  ]
}
```

### 5.9 Scaling Elasticsearch

#### Horizontal Scaling

| Scenario | Action |
|----------|--------|
| More data | Add data nodes |
| More queries | Add replicas (read scaling) |
| Cluster stability | Add dedicated master nodes (3 minimum) |
| Heavy ingestion | Add dedicated ingest nodes |

#### Capacity Planning

```
Storage per day = (log volume per day) × (1 + number of replicas) × 1.1 (overhead)

Example:
- 100 GB logs/day
- 1 replica
- 100 × 2 × 1.1 = 220 GB/day
- 30-day retention = 6.6 TB
```

#### Shard Sizing

```
Target: 10-50 GB per shard

Example:
- 100 GB/day index
- 3 primary shards = ~33 GB per shard ✓
- Daily rollover keeps shard sizes manageable
```

### 5.10 Kibana Alerting

#### Rule Types

| Rule Type | Trigger |
|-----------|---------|
| **Log threshold** | Log count exceeds threshold |
| **Metric threshold** | Metric crosses threshold |
| **Anomaly detection** | ML job detects anomaly |
| **Inventory** | Infrastructure metric threshold |
| **Uptime** | Monitor goes down |

#### Example: Log Threshold Alert

1. **Observability → Alerts → Create rule**.
2. **Rule type:** Log threshold.
3. **Condition:** `status: 500` count > 10 in last 5 minutes.
4. **Group by:** `service.name`.
5. **Action:** Send to Slack webhook.

### Intermediate Exercises

1. **Filebeat:** Deploy Filebeat to ship logs from 3 different sources. Use multiline for stack traces.
2. **Metricbeat:** Set up Metricbeat for system and Docker metrics. Create a Kibana dashboard.
3. **ILM:** Create an ILM policy with hot/warm/cold/delete phases. Apply to a log index.
4. **Ingest pipeline:** Create an Elasticsearch ingest pipeline that parses, enriches, and transforms logs.
5. **Alerting:** Set up 3 Kibana alert rules: log threshold, metric threshold, and anomaly detection.

---

## Level 3: Advanced

### 5.11 Hot-Warm Architecture

Separate node types for different data tiers.

```
┌─────────────────────────────────────────────────────────┐
│                  Elasticsearch Cluster                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Hot Tier (SSD, high CPU/RAM)                   │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐            │    │
│  │  │ Node 1 │  │ Node 2 │  │ Node 3 │            │    │
│  │  │ today  │  │ today  │  │ today  │            │    │
│  │  └────────┘  └────────┘  └────────┘            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Warm Tier (HDD, moderate CPU/RAM)              │    │
│  │  ┌────────┐  ┌────────┐  ┌────────┐            │    │
│  │  │ Node 4 │  │ Node 5 │  │ Node 6 │            │    │
│  │  │ 7-30d  │  │ 7-30d  │  │ 7-30d  │            │    │
│  │  └────────┘  └────────┘  └────────┘            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Cold Tier (Object storage / minimal resources) │    │
│  │  ┌────────┐  ┌────────┐                         │    │
│  │  │ Node 7 │  │ Node 8 │  (searchable snapshots) │    │
│  │  │ 30d+   │  │ 30d+   │                         │    │
│  │  └────────┘  └────────┘                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

#### Node Configuration

```yaml
# Hot node (elasticsearch.yml)
node.roles: ["data_hot", "ingest"]
node.attr.data: hot

# Warm node
node.roles: ["data_warm"]
node.attr.data: warm

# Cold node
node.roles: ["data_cold"]
node.attr.data: cold
```

#### ILM with Data Tiers

```json
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": { "max_primary_shard_size": "50gb" }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "migrate": { "enabled": true },
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "migrate": { "enabled": true },
          "searchable_snapshot": {
            "snapshot_repository": "my-s3-repo"
          }
        }
      }
    }
  }
}
```

### 5.12 Performance Tuning

#### Indexing Performance

| Setting | Default | Tuned | Impact |
|---------|---------|-------|--------|
| `index.refresh_interval` | `1s` | `30s` | Reduces refresh overhead |
| `index.translog.durability` | `request` | `async` | Faster indexing, slight data loss risk |
| `index.number_of_replicas` | `1` | `0` (during bulk load) | Faster bulk indexing |
| Bulk size | - | 5–15 MB per request | Optimal throughput |

#### Search Performance

| Strategy | Description |
|----------|-------------|
| **Use filters over queries** | Filters are cached, queries are scored |
| **Avoid wildcards at start** | `*error` is expensive; `error*` is fast |
| **Use date ranges** | Limit search to relevant time windows |
| **Pre-aggregate** | Use transforms for common aggregations |
| **Shard routing** | Route queries to specific shards |

#### JVM Tuning

```yaml
# jvm.options
-Xms16g    # Set to 50% of available RAM (max 31g)
-Xmx16g   # Min and max must be equal
```

**Rules:**
- Heap should be ≤ 50% of available RAM (rest for OS file cache).
- Never exceed 31 GB (compressed oops threshold).
- Min heap = Max heap (avoid resizing).

#### Monitoring Elasticsearch

```bash
# Cluster health
GET _cluster/health

# Node stats
GET _nodes/stats

# Index stats
GET _cat/indices?v&s=store.size:desc

# Shard allocation
GET _cat/shards?v&s=store:desc

# Pending tasks
GET _cluster/pending_tasks

# Thread pool stats
GET _cat/thread_pool?v&h=node_name,name,active,rejected,completed
```

### 5.13 Query Optimization

#### Slow Query Log

```yaml
# Index settings
index.search.slowlog.threshold.query.warn: 10s
index.search.slowlog.threshold.query.info: 5s
index.search.slowlog.threshold.fetch.warn: 1s
index.indexing.slowlog.threshold.index.warn: 10s
```

#### Query Profiling

```json
GET logs-*/_search
{
  "profile": true,
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "error" } }
      ],
      "filter": [
        { "range": { "@timestamp": { "gte": "now-1h" } } },
        { "term": { "service.name": "api-gateway" } }
      ]
    }
  }
}
```

### 5.14 Securing Elasticsearch

#### Authentication and Authorization

```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: elastic-certificates.p12

xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: http.p12
```

#### Role-Based Access Control

```json
POST _security/role/log_reader
{
  "indices": [
    {
      "names": ["logs-*"],
      "privileges": ["read", "view_index_metadata"],
      "query": {
        "match": { "environment": "production" }
      }
    }
  ]
}

POST _security/user/analyst
{
  "password": "...",
  "roles": ["log_reader"],
  "full_name": "Log Analyst"
}
```

#### Field-Level Security

```json
POST _security/role/pii_restricted
{
  "indices": [
    {
      "names": ["logs-*"],
      "privileges": ["read"],
      "field_security": {
        "grant": ["*"],
        "except": ["user.email", "user.ip_address", "user.phone"]
      }
    }
  ]
}
```

### 5.15 Cross-Cluster Replication (CCR)

Replicate indices across clusters for disaster recovery or geo-distributed search.

```json
# On follower cluster
PUT _ccr/auto_follow/logs-pattern
{
  "remote_cluster": "cluster-us-east",
  "leader_index_patterns": ["logs-*"],
  "follow_index_pattern": "{{leader_index}}-replicated"
}
```

**Use cases:**
- Disaster recovery (active-passive).
- Geo-distributed search (read from nearest cluster).
- Centralized reporting from multiple clusters.

### 5.16 Log Cost Optimization

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| **Structured logging** | 30–50% storage | Requires application changes |
| **Drop unnecessary fields** | 10–30% storage | Less data for debugging |
| **Compress indices** | 20–40% storage | Slightly slower queries |
| **Hot-warm-cold architecture** | 50–70% infrastructure cost | Query latency for old data |
| **Searchable snapshots** | 80%+ storage cost | Higher query latency |
| **Sampling** | Proportional to sample rate | Incomplete data |
| **Shorter retention** | Proportional to reduction | Less historical data |
| **Index sorting** | Better compression | Slower indexing |

#### Data Stream Lifecycle

```json
PUT _data_stream/logs-production/_lifecycle
{
  "data_retention": "30d"
}
```

### Advanced Exercises

1. **Hot-warm:** Deploy a 6-node cluster with hot and warm tiers. Configure ILM to migrate indices.
2. **Performance:** Load 10M documents. Profile slow queries. Optimize index settings and queries.
3. **Security:** Enable TLS and RBAC. Create roles with field-level security. Test access restrictions.
4. **CCR:** Set up cross-cluster replication between two clusters. Test failover.
5. **Cost optimization:** Analyze an existing cluster. Implement 3 cost reduction strategies. Measure storage savings.

---

## Next Module

→ [Module 6 — AWS CloudWatch](../06-aws-cloudwatch/README.md)
