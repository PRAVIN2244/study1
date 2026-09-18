# Module 27: Docker Logging, Monitoring, and Observability

Production containers need structured logging, metrics collection,
and alerting. This module covers the full observability stack.

### Topics Covered

```
27.1  Docker Logging Architecture
27.2  Logging Drivers — Complete Reference
27.3  Log Rotation and Size Management
27.4  Centralized Logging with ELK/EFK Stack
27.5  Docker Metrics and the Prometheus Endpoint
27.6  cAdvisor — Container Resource Metrics
27.7  Full Monitoring Stack (Prometheus + Grafana + cAdvisor)
27.8  Alerting with Alertmanager
27.9  Docker Events and Audit Logging
27.10 Health Checks and Observability Integration
27.11 Distributed Tracing with Jaeger
27.12 Common Errors and Troubleshooting
```

---

## 27.1 Docker Logging Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  CONTAINER LOGGING FLOW                         │
│                                                                 │
│  Container Process (PID 1)                                     │
│    │                                                            │
│    ├── stdout ──┐                                               │
│    └── stderr ──┤                                               │
│                 ▼                                               │
│         containerd-shim                                         │
│                 │                                               │
│                 ▼                                               │
│         Logging Driver                                          │
│         ┌──────────────────────────────────────────┐            │
│         │ json-file (default) → /var/lib/docker/   │            │
│         │ journald            → systemd journal    │            │
│         │ syslog              → syslog daemon      │            │
│         │ fluentd             → Fluentd collector  │            │
│         │ gelf                → Graylog (GELF)     │            │
│         │ awslogs             → CloudWatch Logs    │            │
│         │ gcplogs             → Google Cloud Log   │            │
│         │ splunk              → Splunk HEC         │            │
│         │ none                → discard all logs   │            │
│         └──────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

```
# Key principle: Containers should log to stdout/stderr.
# The logging driver captures these streams and routes them.
#
# DO NOT write logs to files inside the container:
#   ✗ /var/log/app.log  — lost when container is removed
#   ✓ stdout/stderr     — captured by Docker logging driver
#
# Application frameworks should be configured for console output:
#   Node.js: console.log() / console.error()
#   Python:  logging.StreamHandler(sys.stdout)
#   Java:    logback ConsoleAppender
#   Go:      log.SetOutput(os.Stdout)
```

---

## 27.2 Logging Drivers — Complete Reference

### Checking the Current Logging Driver

```bash
# Default driver for the daemon
$ docker info --format '{{.LoggingDriver}}'
# json-file

# Driver for a specific container
$ docker inspect --format '{{.HostConfig.LogConfig.Type}}' <container>
# json-file
```

### All Logging Drivers

```
┌──────────────┬──────────────────────────────────────────────────┐
│ Driver       │ Description                                      │
├──────────────┼──────────────────────────────────────────────────┤
│ json-file    │ Default. JSON-formatted logs on local disk.      │
│              │ Supports docker logs command.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ local        │ Optimized local storage with compression.        │
│              │ Faster than json-file. Supports docker logs.     │
├──────────────┼──────────────────────────────────────────────────┤
│ journald     │ Sends to systemd journal. Supports docker logs.  │
│              │ Integrates with journalctl.                       │
├──────────────┼──────────────────────────────────────────────────┤
│ syslog       │ Sends to syslog daemon (rsyslog, syslog-ng).    │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ fluentd      │ Sends to Fluentd/Fluent Bit collector.           │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ gelf         │ Sends to Graylog Extended Log Format endpoint.   │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ awslogs      │ Sends to Amazon CloudWatch Logs.                 │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ gcplogs      │ Sends to Google Cloud Logging.                   │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ splunk       │ Sends to Splunk HTTP Event Collector.            │
│              │ Does NOT support docker logs.                     │
├──────────────┼──────────────────────────────────────────────────┤
│ none         │ Discard all logs. No docker logs support.        │
└──────────────┴──────────────────────────────────────────────────┘
```

### Setting the Default Logging Driver

```bash
# /etc/docker/daemon.json
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3",
        "labels": "app,environment",
        "tag": "{{.Name}}/{{.ID}}"
    }
}
$ sudo systemctl restart docker
```

### Per-Container Logging Driver

```bash
# Override the default driver for a specific container
$ docker run -d \
    --log-driver=fluentd \
    --log-opt fluentd-address=localhost:24224 \
    --log-opt tag="docker.{{.Name}}" \
    nginx

# Use journald for a specific container
$ docker run -d \
    --log-driver=journald \
    --log-opt tag="myapp" \
    myapp:latest

# View journald logs
$ journalctl CONTAINER_NAME=myapp --follow

# Disable logging for a noisy container
$ docker run -d --log-driver=none nginx
```

---

## 27.3 Log Rotation and Size Management

### The Problem: Unbounded Log Growth

```bash
# Without rotation, json-file logs grow indefinitely
# A busy container can fill a disk in hours

# Check log file sizes
$ sudo du -sh /var/lib/docker/containers/*/
# 2.3G  /var/lib/docker/containers/abc123.../
# 1.8G  /var/lib/docker/containers/def456.../

# Find the actual log file
$ sudo ls -lh /var/lib/docker/containers/<id>/<id>-json.log
# -rw-r----- 1 root root 2.3G  <id>-json.log
```

### Configuring Log Rotation

```bash
# Per-container rotation
$ docker run -d \
    --log-opt max-size=10m \
    --log-opt max-file=5 \
    nginx
# max-size: Maximum size of each log file (10m, 100k, 1g)
# max-file: Number of rotated files to keep
# Total max disk per container: max-size × max-file = 50MB

# Global rotation (daemon.json)
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}

# For the "local" driver (compressed, more efficient)
{
    "log-driver": "local",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    }
}
```

### Docker Compose Log Configuration

```yaml
# docker-compose.yml
version: "3.8"
services:
  api:
    image: myapp:latest
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        tag: "{{.Name}}"

  worker:
    image: myworker:latest
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "docker.worker"
```

---

## 27.4 Centralized Logging with ELK/EFK Stack

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EFK STACK                                    │
│                                                                 │
│  Containers ──► Fluent Bit ──► Elasticsearch ──► Kibana        │
│  (stdout)       (collect,      (store,           (visualize,   │
│                  parse,         index)            search,       │
│                  filter)                          dashboard)    │
│                                                                 │
│  Alternative: ELK Stack                                        │
│  Containers ──► Logstash ──► Elasticsearch ──► Kibana          │
│                                                                 │
│  Fluent Bit is preferred over Logstash:                         │
│    - 10x less memory (~5MB vs ~500MB)                          │
│    - Written in C (Logstash is JVM-based)                      │
│    - Better for container environments                          │
└─────────────────────────────────────────────────────────────────┘
```

### Complete EFK Stack with Docker Compose

```yaml
# docker-compose-efk.yml
version: "3.8"

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200"]
      interval: 10s
      timeout: 5s
      retries: 5

  fluent-bit:
    image: fluent/fluent-bit:2.2
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      elasticsearch:
        condition: service_healthy
    ports:
      - "24224:24224"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy

  # Example application that sends logs
  app:
    image: nginx
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "docker.nginx"

volumes:
  es-data:
```

### Fluent Bit Configuration

```ini
# fluent-bit.conf
[SERVICE]
    Flush        1
    Log_Level    info
    Parsers_File parsers.conf

[INPUT]
    Name         forward
    Listen       0.0.0.0
    Port         24224

[FILTER]
    Name         parser
    Match        docker.*
    Key_Name     log
    Parser       docker
    Reserve_Data On

[FILTER]
    Name         modify
    Match        *
    Add          hostname ${HOSTNAME}
    Add          environment production

[OUTPUT]
    Name         es
    Match        *
    Host         elasticsearch
    Port         9200
    Index        docker-logs
    Type         _doc
    Logstash_Format On
    Logstash_Prefix docker
    Retry_Limit  5
```

---

## 27.5 Docker Metrics and the Prometheus Endpoint

Docker daemon exposes metrics in Prometheus format.

### Enabling the Metrics Endpoint

```bash
# /etc/docker/daemon.json
{
    "metrics-addr": "0.0.0.0:9323",
    "experimental": true
}
$ sudo systemctl restart docker

# Verify metrics are exposed
$ curl -s http://localhost:9323/metrics | head -20
# # HELP engine_daemon_container_states_containers The count of containers
# # TYPE engine_daemon_container_states_containers gauge
# engine_daemon_container_states_containers{state="running"} 5
# engine_daemon_container_states_containers{state="paused"} 0
# engine_daemon_container_states_containers{state="stopped"} 12
```

### Key Docker Daemon Metrics

```
┌────────────────────────────────────────────┬─────────────────────┐
│ Metric                                     │ Description         │
├────────────────────────────────────────────┼─────────────────────┤
│ engine_daemon_container_states_containers  │ Container count     │
│                                            │ by state            │
├────────────────────────────────────────────┼─────────────────────┤
│ engine_daemon_image_actions_seconds        │ Image operation     │
│                                            │ duration            │
├────────────────────────────────────────────┼─────────────────────┤
│ engine_daemon_network_actions_seconds      │ Network operation   │
│                                            │ duration            │
├────────────────────────────────────────────┼─────────────────────┤
│ engine_daemon_engine_cpus_cpus            │ Available CPUs      │
├────────────────────────────────────────────┼─────────────────────┤
│ engine_daemon_engine_memory_bytes         │ Available memory    │
├────────────────────────────────────────────┼─────────────────────┤
│ builder_builds_triggered_total            │ Total builds        │
│ builder_builds_failed_total               │ Failed builds       │
└────────────────────────────────────────────┴─────────────────────┘
```

---

## 27.6 cAdvisor — Container Resource Metrics

cAdvisor (Container Advisor) collects per-container CPU, memory,
network, and filesystem metrics.

```bash
# Run cAdvisor as a container
$ docker run -d \
    --name cadvisor \
    --volume=/:/rootfs:ro \
    --volume=/var/run:/var/run:ro \
    --volume=/sys:/sys:ro \
    --volume=/var/lib/docker/:/var/lib/docker:ro \
    --volume=/dev/disk/:/dev/disk:ro \
    --privileged \
    --device=/dev/kmsg \
    -p 8080:8080 \
    gcr.io/cadvisor/cadvisor:v0.49.1

# View cAdvisor web UI
# http://localhost:8080

# Prometheus metrics endpoint
$ curl -s http://localhost:8080/metrics | grep container_cpu
# container_cpu_usage_seconds_total{name="nginx",...} 12.345
# container_cpu_system_seconds_total{name="nginx",...} 3.456
```

### Key cAdvisor Metrics

```
┌──────────────────────────────────────────┬──────────────────────┐
│ Metric                                   │ Description          │
├──────────────────────────────────────────┼──────────────────────┤
│ container_cpu_usage_seconds_total        │ Total CPU time used  │
│ container_memory_usage_bytes             │ Current memory usage │
│ container_memory_working_set_bytes       │ Memory actually used │
│ container_network_receive_bytes_total    │ Network bytes in     │
│ container_network_transmit_bytes_total   │ Network bytes out    │
│ container_fs_usage_bytes                 │ Filesystem usage     │
│ container_fs_reads_total                 │ Disk read ops        │
│ container_fs_writes_total                │ Disk write ops       │
│ container_last_seen                      │ Last time seen       │
└──────────────────────────────────────────┴──────────────────────┘
```

---

## 27.7 Full Monitoring Stack (Prometheus + Grafana + cAdvisor)

### Complete Docker Compose Stack

```yaml
# docker-compose-monitoring.yml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:v2.49.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:10.3.0
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg:/dev/kmsg
    ports:
      - "8080:8080"

  node-exporter:
    image: prom/node-exporter:v1.7.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
    ports:
      - "9100:9100"

volumes:
  prometheus-data:
  grafana-data:
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Docker daemon metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']

  # cAdvisor container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # Node (host) metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Application metrics (if your app exposes /metrics)
  - job_name: 'app'
    static_configs:
      - targets: ['app:8080']
    metrics_path: /metrics
```

### Useful PromQL Queries for Docker

```
# CPU usage per container (percentage)
rate(container_cpu_usage_seconds_total{name!=""}[5m]) * 100

# Memory usage per container (MB)
container_memory_working_set_bytes{name!=""} / 1024 / 1024

# Network receive rate per container (bytes/sec)
rate(container_network_receive_bytes_total{name!=""}[5m])

# Disk I/O rate per container
rate(container_fs_writes_total{name!=""}[5m])

# Container restart count
changes(container_last_seen{name!=""}[1h])

# Total running containers
engine_daemon_container_states_containers{state="running"}

# Container memory usage as percentage of limit
container_memory_working_set_bytes{name!=""}
  / container_spec_memory_limit_bytes{name!=""} * 100
```

---

## 27.8 Alerting with Alertmanager

### Alert Rules for Docker

```yaml
# alert-rules.yml (loaded by Prometheus)
groups:
  - name: docker-alerts
    rules:
      - alert: ContainerHighCPU
        expr: rate(container_cpu_usage_seconds_total{name!=""}[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} high CPU"
          description: "CPU usage above 80% for 5 minutes"

      - alert: ContainerHighMemory
        expr: >
          container_memory_working_set_bytes{name!=""}
          / container_spec_memory_limit_bytes{name!=""} > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} memory at 90%"

      - alert: ContainerRestarting
        expr: increase(container_last_seen{name!=""}[1h]) > 3
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} restarting frequently"

      - alert: ContainerDown
        expr: absent(container_last_seen{name="myapp"})
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container myapp is down"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'slack'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/T.../B.../xxx'
        channel: '#docker-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<pagerduty-key>'
```

---

## 27.9 Docker Events and Audit Logging

```bash
# Stream real-time Docker events
$ docker events
# 2024-01-15T10:30:00 container start abc123 (image=nginx, name=web)
# 2024-01-15T10:30:05 container die abc123 (exitCode=0)
# 2024-01-15T10:30:06 network connect bridge abc123

# Filter events by type
$ docker events --filter type=container
$ docker events --filter type=image
$ docker events --filter type=volume
$ docker events --filter type=network

# Filter by specific event
$ docker events --filter event=start
$ docker events --filter event=die
$ docker events --filter event=oom

# Filter by container
$ docker events --filter container=myapp

# Time range
$ docker events --since "2024-01-15T10:00:00" --until "2024-01-15T11:00:00"

# JSON output for parsing
$ docker events --format '{{json .}}'
```

### Audit Logging Script

```bash
#!/bin/bash
# docker-audit.sh — Log all Docker events to a file with rotation
docker events --format '{{json .}}' | while read event; do
    echo "$event" >> /var/log/docker-audit.json
    # Rotate at 100MB
    if [ $(stat -f%z /var/log/docker-audit.json 2>/dev/null || echo 0) -gt 104857600 ]; then
        mv /var/log/docker-audit.json /var/log/docker-audit.json.1
    fi
done
```

---

## 27.10 Health Checks and Observability Integration

```dockerfile
# Dockerfile with health check
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci --production

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "server.js"]
```

```bash
# Health check flags explained:
#   --interval=30s      Check every 30 seconds
#   --timeout=5s        Fail if check takes > 5 seconds
#   --start-period=10s  Grace period for container startup
#   --retries=3         Mark unhealthy after 3 consecutive failures

# View health status
$ docker inspect --format '{{.State.Health.Status}}' myapp
# healthy | unhealthy | starting

# View health check log
$ docker inspect --format '{{json .State.Health}}' myapp | python3 -m json.tool
# {
#   "Status": "healthy",
#   "FailingStreak": 0,
#   "Log": [
#     {"Start": "...", "End": "...", "ExitCode": 0, "Output": "OK"}
#   ]
# }
```

### Health Check in Docker Compose

```yaml
services:
  api:
    image: myapp:latest
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

---

## 27.11 Distributed Tracing with Jaeger

```yaml
# Add Jaeger to your monitoring stack
services:
  jaeger:
    image: jaegertracing/all-in-one:1.53
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"   # Jaeger UI
      - "4317:4317"     # OTLP gRPC
      - "4318:4318"     # OTLP HTTP
```

```javascript
// Node.js application with OpenTelemetry tracing
// npm install @opentelemetry/sdk-node @opentelemetry/exporter-trace-otlp-http

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
    traceExporter: new OTLPTraceExporter({
        url: 'http://jaeger:4318/v1/traces',
    }),
    serviceName: 'my-api',
});
sdk.start();
```

---

## 27.12 Common Errors and Troubleshooting

### Error 1: "docker logs" returns nothing

```bash
# Check the logging driver — only json-file, local, and journald
# support docker logs
$ docker inspect --format '{{.HostConfig.LogConfig.Type}}' <container>
# If it shows "fluentd", "syslog", etc. → docker logs won't work
# Fix: Use the appropriate tool (Kibana, Graylog, etc.)
```

### Error 2: Disk full from container logs

```bash
# Find the largest log files
$ sudo find /var/lib/docker/containers -name "*-json.log" -exec du -sh {} + | sort -rh | head
# Fix: Add log rotation to daemon.json
# Emergency: Truncate a specific log file
$ sudo truncate -s 0 /var/lib/docker/containers/<id>/<id>-json.log
```

### Error 3: Fluentd connection refused

```bash
# Container starts before Fluentd is ready
# Fix: Use fluentd-async and fluentd-buffer-limit
$ docker run -d \
    --log-driver=fluentd \
    --log-opt fluentd-async=true \
    --log-opt fluentd-buffer-limit=8388608 \
    myapp
```

### Error 4: Prometheus not scraping targets

```bash
# Check targets page: http://localhost:9090/targets
# Common issues:
#   - Wrong target address (use container name, not localhost)
#   - Firewall blocking port
#   - Metrics endpoint not exposed
$ curl -s http://cadvisor:8080/metrics | head -5
```

---

## Module 27 Summary

- Containers should log to **stdout/stderr** — never to files inside the container
- Docker supports 10+ **logging drivers**: json-file (default), local, journald, fluentd, awslogs, etc.
- Only json-file, local, and journald support `docker logs`; others require external tools
- **Always configure log rotation** (`max-size`, `max-file`) to prevent disk exhaustion
- **EFK stack** (Elasticsearch + Fluent Bit + Kibana) is the standard centralized logging solution
- Docker daemon exposes **Prometheus metrics** on port 9323 when configured
- **cAdvisor** provides per-container CPU, memory, network, and disk metrics
- Full monitoring stack: **Prometheus** (collect) + **Grafana** (visualize) + **Alertmanager** (alert)
- **Docker events** provide real-time audit trail of all daemon operations
- **Health checks** integrate with orchestrators for automatic restart and load balancer routing
- **Distributed tracing** (Jaeger/OpenTelemetry) tracks requests across containerized microservices

---

**Previous Module: [Module 26 - BuildKit and Advanced Build Patterns](module-26-buildkit-advanced-builds.md)**

**Next Module: [Module 28 - CI/CD with Docker](module-28-cicd-docker.md)**
