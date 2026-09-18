# Module 16 — Monitoring Automation with Python

Monitoring tells you when something is wrong before your users notice. Python can collect system metrics, check service health, send alerts, and integrate with monitoring platforms like Prometheus, Grafana, and PagerDuty.

---

## Prerequisites

```bash
pip install psutil requests
```

---

## System Monitoring with psutil

`psutil` provides cross-platform access to system metrics — CPU, memory, disk, network, and processes.

### CPU Monitoring

```python
import psutil

# Current CPU usage (percentage)
cpu_percent = psutil.cpu_percent(interval=1)
print(f"CPU Usage: {cpu_percent}%")

# Per-core usage
per_core = psutil.cpu_percent(interval=1, percpu=True)
for i, usage in enumerate(per_core):
    bar = "#" * int(usage / 5)
    print(f"  Core {i}: {usage:5.1f}% {bar}")

# CPU count
print(f"\nPhysical cores: {psutil.cpu_count(logical=False)}")
print(f"Logical cores: {psutil.cpu_count(logical=True)}")
```

**Output (example):**

```
CPU Usage: 23.5%
  Core 0: 35.0% #######
  Core 1: 12.0% ##
  Core 2: 28.0% #####
  Core 3: 19.0% ###

Physical cores: 4
Logical cores: 8
```

### Memory Monitoring

```python
import psutil

mem = psutil.virtual_memory()

print(f"Total:     {mem.total / 1024 / 1024 / 1024:.1f} GB")
print(f"Used:      {mem.used / 1024 / 1024 / 1024:.1f} GB")
print(f"Available: {mem.available / 1024 / 1024 / 1024:.1f} GB")
print(f"Usage:     {mem.percent}%")

# Visual bar
bar_length = 40
filled = int(bar_length * mem.percent / 100)
bar = "#" * filled + "-" * (bar_length - filled)
print(f"[{bar}] {mem.percent}%")
```

**Output (example):**

```
Total:     16.0 GB
Used:      8.5 GB
Available: 7.5 GB
Usage:     53.1%
[#####################-------------------] 53.1%
```

### Disk Monitoring

```python
import psutil

print(f"{'MOUNT':<20} {'TOTAL':<10} {'USED':<10} {'FREE':<10} {'USE%'}")
print("-" * 55)

for partition in psutil.disk_partitions():
    try:
        usage = psutil.disk_usage(partition.mountpoint)
        total_gb = usage.total / 1024 / 1024 / 1024
        used_gb = usage.used / 1024 / 1024 / 1024
        free_gb = usage.free / 1024 / 1024 / 1024
        print(f"{partition.mountpoint:<20} {total_gb:<10.1f} {used_gb:<10.1f} "
              f"{free_gb:<10.1f} {usage.percent}%")
    except PermissionError:
        continue
```

### Network Monitoring

```python
import psutil
import time

# Get network I/O counters
net1 = psutil.net_io_counters()
time.sleep(1)
net2 = psutil.net_io_counters()

bytes_sent = net2.bytes_sent - net1.bytes_sent
bytes_recv = net2.bytes_recv - net1.bytes_recv

print(f"Network (last 1s):")
print(f"  Sent:     {bytes_sent / 1024:.1f} KB/s")
print(f"  Received: {bytes_recv / 1024:.1f} KB/s")

# Active connections
connections = psutil.net_connections(kind="inet")
listening = [c for c in connections if c.status == "LISTEN"]
established = [c for c in connections if c.status == "ESTABLISHED"]

print(f"\nConnections:")
print(f"  Listening: {len(listening)}")
print(f"  Established: {len(established)}")
```

### Process Monitoring

```python
import psutil

# Top 5 processes by CPU usage
processes = []
for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
    try:
        processes.append(proc.info)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue

# Sort by CPU usage
top_cpu = sorted(processes, key=lambda p: p["cpu_percent"] or 0, reverse=True)[:5]

print(f"{'PID':<8} {'NAME':<25} {'CPU%':<8} {'MEM%'}")
print("-" * 50)
for p in top_cpu:
    print(f"{p['pid']:<8} {p['name']:<25} {p['cpu_percent'] or 0:<8.1f} "
          f"{p['memory_percent'] or 0:.1f}%")
```

---

## System Health Dashboard

A complete system health check that combines all metrics:

```python
import psutil
from datetime import datetime

def system_health_check():
    """Run a complete system health check."""
    print(f"\nSystem Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    alerts = []
    
    # CPU
    cpu = psutil.cpu_percent(interval=1)
    print(f"\nCPU: {cpu}%")
    if cpu > 80:
        alerts.append(f"HIGH CPU: {cpu}%")
    
    # Memory
    mem = psutil.virtual_memory()
    print(f"Memory: {mem.percent}% ({mem.used / 1024**3:.1f}/{mem.total / 1024**3:.1f} GB)")
    if mem.percent > 85:
        alerts.append(f"HIGH MEMORY: {mem.percent}%")
    
    # Disk
    print(f"\nDisk:")
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            print(f"  {partition.mountpoint}: {usage.percent}% "
                  f"({usage.free / 1024**3:.1f} GB free)")
            if usage.percent > 90:
                alerts.append(f"HIGH DISK on {partition.mountpoint}: {usage.percent}%")
        except PermissionError:
            continue
    
    # Load average (Unix only)
    try:
        load1, load5, load15 = psutil.getloadavg()
        cores = psutil.cpu_count()
        print(f"\nLoad Average: {load1:.2f} / {load5:.2f} / {load15:.2f} "
              f"(cores: {cores})")
        if load1 > cores * 2:
            alerts.append(f"HIGH LOAD: {load1:.2f} (cores: {cores})")
    except AttributeError:
        pass    # Windows does not have load average
    
    # Uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    print(f"Uptime: {uptime.days}d {uptime.seconds // 3600}h")
    
    # Alerts
    if alerts:
        print(f"\n{'!'*60}")
        print(f"ALERTS ({len(alerts)}):")
        for alert in alerts:
            print(f"  [!!] {alert}")
    else:
        print(f"\n[OK] All systems healthy")
    
    return len(alerts) == 0

# Usage:
is_healthy = system_health_check()
```

---

## HTTP Health Checks

Monitor web services and APIs:

```python
import requests
import time
from datetime import datetime

def check_endpoint(url, timeout=5, expected_status=200):
    """Check if an HTTP endpoint is healthy."""
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = (time.time() - start) * 1000    # milliseconds
        
        return {
            "url": url,
            "status": response.status_code,
            "response_time_ms": round(response_time),
            "healthy": response.status_code == expected_status
        }
    except requests.exceptions.Timeout:
        return {"url": url, "status": "TIMEOUT", "response_time_ms": timeout * 1000, "healthy": False}
    except requests.exceptions.ConnectionError:
        return {"url": url, "status": "CONNECTION_ERROR", "response_time_ms": 0, "healthy": False}
    except requests.exceptions.RequestException as e:
        return {"url": url, "status": str(e), "response_time_ms": 0, "healthy": False}

def check_all_endpoints(endpoints):
    """Check multiple endpoints and print a report."""
    print(f"\nHealth Check — {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'URL':<40} {'STATUS':<8} {'TIME':<10} {'HEALTH'}")
    print("-" * 70)
    
    all_healthy = True
    
    for url in endpoints:
        result = check_endpoint(url)
        health = "OK" if result["healthy"] else "FAIL"
        
        if not result["healthy"]:
            all_healthy = False
        
        print(f"{result['url']:<40} {str(result['status']):<8} "
              f"{result['response_time_ms']:<10}ms {health}")
    
    return all_healthy

# Usage:
endpoints = [
    "https://httpbin.org/get",
    "https://httpbin.org/status/200",
    "https://httpbin.org/delay/10",    # Will timeout
]

check_all_endpoints(endpoints)
```

**Output (example):**

```
Health Check — 14:30:00
URL                                      STATUS   TIME       HEALTH
----------------------------------------------------------------------
https://httpbin.org/get                  200      245       ms OK
https://httpbin.org/status/200           200      180       ms OK
https://httpbin.org/delay/10             TIMEOUT  5000      ms FAIL
```

---

## Continuous Monitoring Loop

```python
import time
from datetime import datetime

def monitoring_loop(endpoints, interval=60, alert_func=None):
    """Continuously monitor endpoints at a given interval."""
    print(f"Starting monitoring (interval: {interval}s)")
    print("Press Ctrl+C to stop.\n")
    
    consecutive_failures = {}
    
    try:
        while True:
            for url in endpoints:
                result = check_endpoint(url)
                
                if result["healthy"]:
                    consecutive_failures[url] = 0
                    status = "OK"
                else:
                    consecutive_failures[url] = consecutive_failures.get(url, 0) + 1
                    status = f"FAIL (x{consecutive_failures[url]})"
                    
                    # Alert after 3 consecutive failures
                    if consecutive_failures[url] == 3 and alert_func:
                        alert_func(url, result)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"  [{timestamp}] {url}: {status} ({result['response_time_ms']}ms)")
            
            print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

# Usage:
# monitoring_loop(["https://example.com", "https://api.example.com/health"], interval=30)
```

---

## Alerting — Slack Notifications

```python
import requests
import os
from datetime import datetime

def send_alert(webhook_url, title, message, severity="warning"):
    """Send an alert to Slack."""
    colors = {
        "info": "#36a64f",
        "warning": "#ff9900",
        "critical": "#ff0000"
    }
    
    payload = {
        "attachments": [{
            "color": colors.get(severity, "#ff9900"),
            "title": title,
            "text": message,
            "footer": f"Monitoring Alert | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }]
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200

class AlertManager:
    """Manage alerts with deduplication and cooldown."""
    
    def __init__(self, webhook_url, cooldown_minutes=15):
        self.webhook_url = webhook_url
        self.cooldown = cooldown_minutes * 60
        self.last_alert = {}    # Track when each alert was last sent
    
    def alert(self, alert_id, title, message, severity="warning"):
        """Send an alert if not in cooldown period."""
        now = time.time()
        last = self.last_alert.get(alert_id, 0)
        
        if now - last < self.cooldown:
            return False    # Still in cooldown
        
        if send_alert(self.webhook_url, title, message, severity):
            self.last_alert[alert_id] = now
            return True
        return False

# Usage:
# alerter = AlertManager(os.environ.get("SLACK_WEBHOOK_URL"))
# alerter.alert("high-cpu", "High CPU Alert", "CPU usage at 95%", "critical")
```

---

## Log Monitoring

Watch log files for patterns and alert on matches:

```python
import time
import re
from pathlib import Path

def tail_log(log_file, patterns, callback=None):
    """Monitor a log file for specific patterns (like tail -f with grep)."""
    path = Path(log_file)
    
    if not path.exists():
        print(f"File not found: {log_file}")
        return
    
    # Start at the end of the file
    with open(log_file, "r") as f:
        f.seek(0, 2)    # Seek to end
        
        print(f"Monitoring {log_file} for patterns: {patterns}")
        print("Press Ctrl+C to stop.\n")
        
        try:
            while True:
                line = f.readline()
                
                if not line:
                    time.sleep(0.5)
                    continue
                
                line = line.strip()
                
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        print(f"  MATCH [{pattern}]: {line}")
                        if callback:
                            callback(pattern, line)
        except KeyboardInterrupt:
            print("\nLog monitoring stopped.")

# Usage:
# tail_log("/var/log/app.log", ["ERROR", "CRITICAL", "OutOfMemory"])
```

---

## Prometheus Metrics Exporter

Expose custom metrics for Prometheus to scrape:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import psutil
import json

class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves Prometheus-format metrics."""
    
    def do_GET(self):
        if self.path == "/metrics":
            metrics = self.collect_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(metrics.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def collect_metrics(self):
        """Collect system metrics in Prometheus format."""
        lines = []
        
        # CPU
        cpu = psutil.cpu_percent()
        lines.append(f"# HELP system_cpu_percent Current CPU usage percentage")
        lines.append(f"# TYPE system_cpu_percent gauge")
        lines.append(f"system_cpu_percent {cpu}")
        
        # Memory
        mem = psutil.virtual_memory()
        lines.append(f"# HELP system_memory_percent Memory usage percentage")
        lines.append(f"# TYPE system_memory_percent gauge")
        lines.append(f"system_memory_percent {mem.percent}")
        lines.append(f"# HELP system_memory_bytes_total Total memory in bytes")
        lines.append(f"# TYPE system_memory_bytes_total gauge")
        lines.append(f"system_memory_bytes_total {mem.total}")
        
        # Disk
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                mount = partition.mountpoint.replace("/", "_").strip("_") or "root"
                lines.append(f'system_disk_percent{{mount="{partition.mountpoint}"}} {usage.percent}')
            except PermissionError:
                continue
        
        return "\n".join(lines) + "\n"
    
    def log_message(self, format, *args):
        pass    # Suppress default logging

def start_metrics_server(port=9100):
    """Start a Prometheus metrics exporter."""
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    print(f"Metrics server running on port {port}")
    print(f"Scrape URL: http://localhost:{port}/metrics")
    server.serve_forever()

# Usage:
# start_metrics_server(9100)
```

---

## Exercises

**Exercise 1:** Write a system monitor that checks CPU, memory, and disk every 30 seconds and prints a warning if any metric exceeds a threshold.

**Exercise 2:** Write an HTTP health checker that monitors a list of URLs from a JSON config file and sends a Slack alert when any endpoint goes down.

**Exercise 3:** Write a log monitor that watches a log file for ERROR lines and counts errors per minute. Alert if the error rate exceeds 10 per minute.

**Exercise 4:** Build a simple metrics dashboard that collects system metrics every 5 seconds and writes them to a CSV file for later analysis.

---

## Common Mistakes

### 1. Monitoring Too Frequently

Checking every second wastes resources. Use appropriate intervals: 10-60 seconds for system metrics, 1-5 minutes for HTTP checks.

### 2. Alert Fatigue

Sending too many alerts causes people to ignore them. Use cooldown periods and only alert on actionable issues.

### 3. Not Handling Monitoring Failures

Your monitoring script itself can crash. Use try/except around metric collection and log monitoring errors.

### 4. Hardcoding Thresholds

```python
# Bad
if cpu > 80:
    alert()

# Good — configurable thresholds
thresholds = {"cpu": 80, "memory": 85, "disk": 90}
if cpu > thresholds["cpu"]:
    alert()
```

---

## Summary

| Task | Tool/Library | Key Function |
|------|-------------|-------------|
| CPU/Memory/Disk | `psutil` | `cpu_percent()`, `virtual_memory()`, `disk_usage()` |
| Process monitoring | `psutil` | `process_iter()` |
| HTTP health checks | `requests` | `requests.get(url, timeout=5)` |
| Log monitoring | Built-in `open()` | `f.readline()` with seek to end |
| Slack alerts | `requests` | POST to webhook URL |
| Prometheus metrics | `http.server` | Custom HTTP handler |

---

[Previous: Module 15 — CI/CD Automation](15-cicd-automation.md) | [Next: Module 17 — Parallel and Async Automation](17-parallel-and-async-automation.md)
