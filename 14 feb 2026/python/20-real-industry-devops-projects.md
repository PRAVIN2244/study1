# Module 20 — Real Industry DevOps Projects

This module presents complete, production-style projects that combine multiple skills from the course. Each project solves a real problem that DevOps engineers face daily.

---

## Project 1: Multi-Cloud Health Dashboard

A tool that monitors services across AWS, GCP, and on-premise infrastructure from a single dashboard.

```python
#!/usr/bin/env python3
"""Multi-cloud health dashboard — monitor services across environments."""

import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")

@dataclass
class HealthResult:
    name: str
    url: str
    status: str
    response_ms: int
    healthy: bool
    cloud: str
    checked_at: str

def check_endpoint(endpoint: dict) -> HealthResult:
    """Check a single endpoint's health."""
    try:
        start = time.time()
        response = requests.get(
            endpoint["url"],
            timeout=endpoint.get("timeout", 5),
            headers=endpoint.get("headers", {})
        )
        elapsed_ms = int((time.time() - start) * 1000)
        expected = endpoint.get("expected_status", 200)
        
        return HealthResult(
            name=endpoint["name"],
            url=endpoint["url"],
            status=str(response.status_code),
            response_ms=elapsed_ms,
            healthy=response.status_code == expected,
            cloud=endpoint.get("cloud", "unknown"),
            checked_at=datetime.now().isoformat()
        )
    except requests.exceptions.Timeout:
        return HealthResult(
            name=endpoint["name"], url=endpoint["url"],
            status="TIMEOUT", response_ms=0, healthy=False,
            cloud=endpoint.get("cloud", "unknown"),
            checked_at=datetime.now().isoformat()
        )
    except requests.exceptions.ConnectionError:
        return HealthResult(
            name=endpoint["name"], url=endpoint["url"],
            status="UNREACHABLE", response_ms=0, healthy=False,
            cloud=endpoint.get("cloud", "unknown"),
            checked_at=datetime.now().isoformat()
        )

def run_dashboard(config_file: str, output_file: str = None):
    """Run health checks and display dashboard."""
    config = json.loads(Path(config_file).read_text())
    endpoints = config["endpoints"]
    
    # Check all endpoints in parallel
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_endpoint, ep): ep for ep in endpoints}
        for future in as_completed(futures):
            results.append(future.result())
    
    # Display dashboard
    print(f"\n{'='*70}")
    print(f"  Health Dashboard — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Group by cloud
    by_cloud = {}
    for r in results:
        by_cloud.setdefault(r.cloud, []).append(r)
    
    for cloud, cloud_results in sorted(by_cloud.items()):
        healthy = sum(1 for r in cloud_results if r.healthy)
        total = len(cloud_results)
        print(f"\n  [{cloud.upper()}] {healthy}/{total} healthy")
        print(f"  {'NAME':<25} {'STATUS':<12} {'TIME':<10} {'HEALTH'}")
        print(f"  {'-'*55}")
        
        for r in cloud_results:
            health = "OK" if r.healthy else "FAIL"
            print(f"  {r.name:<25} {r.status:<12} {r.response_ms:<10}ms {health}")
    
    # Overall summary
    total_healthy = sum(1 for r in results if r.healthy)
    print(f"\n{'='*70}")
    print(f"  Overall: {total_healthy}/{len(results)} healthy")
    
    # Save results
    if output_file:
        Path(output_file).write_text(
            json.dumps([asdict(r) for r in results], indent=2)
        )
        logger.info(f"Results saved to {output_file}")
    
    return all(r.healthy for r in results)
```

**Config file (`dashboard-config.json`):**

```json
{
  "endpoints": [
    {"name": "Web App", "url": "https://app.example.com/health", "cloud": "aws"},
    {"name": "API Gateway", "url": "https://api.example.com/status", "cloud": "aws"},
    {"name": "Auth Service", "url": "https://auth.example.com/ping", "cloud": "gcp"},
    {"name": "CDN", "url": "https://cdn.example.com/test", "cloud": "cloudflare"},
    {"name": "Internal API", "url": "http://10.0.1.50:8080/health", "cloud": "on-prem"}
  ]
}
```

---

## Project 2: Automated Incident Response System

A system that detects issues, creates incidents, and takes automated remediation actions.

```python
#!/usr/bin/env python3
"""Automated incident response — detect, alert, and remediate."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

import psutil
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("incident-response")

@dataclass
class Incident:
    id: str
    severity: str
    title: str
    description: str
    created_at: str
    status: str = "open"
    actions_taken: list = field(default_factory=list)

class IncidentResponder:
    """Detect and respond to infrastructure incidents."""
    
    def __init__(self, config_file: str):
        self.config = json.loads(Path(config_file).read_text())
        self.incidents: list[Incident] = []
        self.incident_counter = 0
    
    def check_system(self) -> list[Incident]:
        """Check system metrics and create incidents for anomalies."""
        new_incidents = []
        thresholds = self.config.get("thresholds", {})
        
        # CPU check
        cpu = psutil.cpu_percent(interval=1)
        cpu_threshold = thresholds.get("cpu_percent", 90)
        if cpu > cpu_threshold:
            incident = self._create_incident(
                severity="high" if cpu > 95 else "medium",
                title=f"High CPU usage: {cpu}%",
                description=f"CPU usage exceeded {cpu_threshold}% threshold"
            )
            new_incidents.append(incident)
        
        # Memory check
        mem = psutil.virtual_memory()
        mem_threshold = thresholds.get("memory_percent", 90)
        if mem.percent > mem_threshold:
            incident = self._create_incident(
                severity="high",
                title=f"High memory usage: {mem.percent}%",
                description=f"Memory usage exceeded {mem_threshold}% threshold"
            )
            new_incidents.append(incident)
        
        # Disk check
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_threshold = thresholds.get("disk_percent", 90)
                if usage.percent > disk_threshold:
                    incident = self._create_incident(
                        severity="critical" if usage.percent > 95 else "high",
                        title=f"Disk full: {partition.mountpoint} at {usage.percent}%",
                        description=f"Disk {partition.mountpoint} exceeded {disk_threshold}%"
                    )
                    new_incidents.append(incident)
            except PermissionError:
                continue
        
        return new_incidents
    
    def check_endpoints(self) -> list[Incident]:
        """Check HTTP endpoints and create incidents for failures."""
        new_incidents = []
        
        for endpoint in self.config.get("endpoints", []):
            try:
                response = requests.get(endpoint["url"], timeout=5)
                if response.status_code != endpoint.get("expected_status", 200):
                    incident = self._create_incident(
                        severity="high",
                        title=f"Endpoint unhealthy: {endpoint['name']}",
                        description=f"{endpoint['url']} returned {response.status_code}"
                    )
                    new_incidents.append(incident)
            except requests.exceptions.RequestException as e:
                incident = self._create_incident(
                    severity="critical",
                    title=f"Endpoint unreachable: {endpoint['name']}",
                    description=f"{endpoint['url']}: {e}"
                )
                new_incidents.append(incident)
        
        return new_incidents
    
    def remediate(self, incident: Incident):
        """Take automated remediation actions."""
        actions = self.config.get("remediation", {})
        
        if "High CPU" in incident.title:
            if actions.get("kill_high_cpu_processes", False):
                self._kill_high_cpu_processes(incident)
        
        if "Disk full" in incident.title:
            if actions.get("cleanup_temp_files", False):
                self._cleanup_temp_files(incident)
        
        if "Endpoint" in incident.title:
            if actions.get("restart_services", False):
                self._restart_service(incident)
    
    def _kill_high_cpu_processes(self, incident: Incident):
        """Kill processes using excessive CPU."""
        for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                if (proc.info["cpu_percent"] or 0) > 80:
                    logger.warning(f"Would kill process: {proc.info['name']} "
                                  f"(PID {proc.info['pid']}, CPU {proc.info['cpu_percent']}%)")
                    incident.actions_taken.append(
                        f"Identified high-CPU process: {proc.info['name']}"
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    def _cleanup_temp_files(self, incident: Incident):
        """Clean up temporary files to free disk space."""
        temp_dirs = ["/tmp", "/var/tmp"]
        for temp_dir in temp_dirs:
            path = Path(temp_dir)
            if path.exists():
                incident.actions_taken.append(f"Would clean up {temp_dir}")
    
    def _restart_service(self, incident: Incident):
        """Restart a failed service."""
        incident.actions_taken.append("Would restart the affected service")
    
    def _create_incident(self, severity: str, title: str, description: str) -> Incident:
        self.incident_counter += 1
        incident = Incident(
            id=f"INC-{self.incident_counter:04d}",
            severity=severity,
            title=title,
            description=description,
            created_at=datetime.now().isoformat()
        )
        self.incidents.append(incident)
        return incident
    
    def run_check(self):
        """Run all checks and remediation."""
        logger.info("Starting incident check...")
        
        incidents = []
        incidents.extend(self.check_system())
        incidents.extend(self.check_endpoints())
        
        if incidents:
            logger.warning(f"Found {len(incidents)} incident(s)")
            for incident in incidents:
                logger.info(f"  [{incident.severity.upper()}] {incident.title}")
                self.remediate(incident)
                if incident.actions_taken:
                    for action in incident.actions_taken:
                        logger.info(f"    Action: {action}")
        else:
            logger.info("No incidents detected")
        
        return incidents
```

**Config file (`incident-config.json`):**

```json
{
  "thresholds": {
    "cpu_percent": 90,
    "memory_percent": 85,
    "disk_percent": 90
  },
  "endpoints": [
    {"name": "Web App", "url": "https://app.example.com/health"},
    {"name": "API", "url": "https://api.example.com/status"}
  ],
  "remediation": {
    "kill_high_cpu_processes": false,
    "cleanup_temp_files": true,
    "restart_services": false
  }
}
```

---

## Project 3: Release Manager

A complete release management tool that handles versioning, changelogs, and deployment coordination.

```python
#!/usr/bin/env python3
"""Release manager — version, changelog, and deployment coordination."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class ReleaseManager:
    """Manage application releases."""
    
    def __init__(self, config_file="release.json"):
        self.config_path = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"version": "0.0.0", "releases": []}
    
    def _save_config(self):
        self.config_path.write_text(json.dumps(self.config, indent=2))
    
    def current_version(self) -> str:
        return self.config["version"]
    
    def bump_version(self, bump_type: str) -> str:
        """Bump the version number."""
        current = self.config["version"]
        major, minor, patch = map(int, current.split("."))
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
        
        new_version = f"{major}.{minor}.{patch}"
        self.config["version"] = new_version
        self._save_config()
        
        return new_version
    
    def generate_changelog(self, since_tag: str = None) -> str:
        """Generate changelog from git commits."""
        cmd = ["git", "log", "--oneline", "--no-merges"]
        
        if since_tag:
            cmd.append(f"{since_tag}..HEAD")
        else:
            cmd.extend(["-20"])    # Last 20 commits
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return "Could not generate changelog"
        
        # Categorize commits
        features = []
        fixes = []
        other = []
        
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            
            commit_hash, *message_parts = line.split(" ", 1)
            message = message_parts[0] if message_parts else ""
            
            if re.match(r"(feat|feature|add)", message, re.IGNORECASE):
                features.append(message)
            elif re.match(r"(fix|bug|patch)", message, re.IGNORECASE):
                fixes.append(message)
            else:
                other.append(message)
        
        changelog = f"## v{self.current_version()} — {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        if features:
            changelog += "### Features\n"
            for f in features:
                changelog += f"- {f}\n"
            changelog += "\n"
        
        if fixes:
            changelog += "### Bug Fixes\n"
            for f in fixes:
                changelog += f"- {f}\n"
            changelog += "\n"
        
        if other:
            changelog += "### Other Changes\n"
            for o in other:
                changelog += f"- {o}\n"
            changelog += "\n"
        
        return changelog
    
    def create_release(self, bump_type: str, dry_run: bool = False):
        """Create a new release."""
        old_version = self.current_version()
        new_version = self.bump_version(bump_type)
        
        print(f"\nCreating release: v{old_version} -> v{new_version}")
        print("-" * 40)
        
        # Generate changelog
        changelog = self.generate_changelog(f"v{old_version}")
        print(f"\nChangelog:\n{changelog}")
        
        if dry_run:
            print("[DRY RUN] No changes made")
            self.config["version"] = old_version
            self._save_config()
            return
        
        # Record release
        release = {
            "version": new_version,
            "previous": old_version,
            "date": datetime.now().isoformat(),
            "bump_type": bump_type
        }
        self.config["releases"].append(release)
        self._save_config()
        
        # Create git tag
        subprocess.run(["git", "tag", f"v{new_version}"], capture_output=True)
        
        print(f"\nRelease v{new_version} created!")
        print(f"  Git tag: v{new_version}")
        print(f"  Config updated: {self.config_path}")
    
    def show_history(self, limit: int = 10):
        """Show release history."""
        releases = self.config.get("releases", [])[-limit:]
        
        print(f"\nRelease History (last {limit}):")
        print(f"{'VERSION':<12} {'DATE':<22} {'TYPE'}")
        print("-" * 45)
        
        for r in reversed(releases):
            date = r["date"][:19]
            print(f"v{r['version']:<11} {date:<22} {r['bump_type']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Release manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # version command
    subparsers.add_parser("version", help="Show current version")
    
    # release command
    release_parser = subparsers.add_parser("release", help="Create a new release")
    release_parser.add_argument("type", choices=["major", "minor", "patch"])
    release_parser.add_argument("--dry-run", action="store_true")
    
    # changelog command
    changelog_parser = subparsers.add_parser("changelog", help="Generate changelog")
    changelog_parser.add_argument("--since", help="Since tag (e.g., v1.0.0)")
    
    # history command
    history_parser = subparsers.add_parser("history", help="Show release history")
    history_parser.add_argument("--limit", type=int, default=10)
    
    args = parser.parse_args()
    rm = ReleaseManager()
    
    if args.command == "version":
        print(f"v{rm.current_version()}")
    elif args.command == "release":
        rm.create_release(args.type, args.dry_run)
    elif args.command == "changelog":
        print(rm.generate_changelog(args.since))
    elif args.command == "history":
        rm.show_history(args.limit)
    else:
        parser.print_help()
```

---

## Project 4: Infrastructure Cost Reporter

A tool that analyzes AWS costs and generates reports:

```python
#!/usr/bin/env python3
"""Infrastructure cost reporter — analyze and report AWS spending."""

import json
from datetime import datetime, timedelta
from collections import defaultdict

# Note: Requires boto3 and AWS credentials
# import boto3

def generate_cost_report(days=30):
    """Generate a cost report for the last N days."""
    # In production, this would use boto3 Cost Explorer API:
    # ce = boto3.client("ce")
    # response = ce.get_cost_and_usage(...)
    
    # Simulated data for demonstration
    cost_data = {
        "EC2": {"current": 1250.00, "previous": 1180.00},
        "RDS": {"current": 450.00, "previous": 420.00},
        "S3": {"current": 85.00, "previous": 92.00},
        "Lambda": {"current": 32.00, "previous": 28.00},
        "CloudFront": {"current": 120.00, "previous": 115.00},
        "ELB": {"current": 95.00, "previous": 90.00},
    }
    
    print(f"\nAWS Cost Report — Last {days} Days")
    print("=" * 65)
    
    total_current = 0
    total_previous = 0
    
    print(f"\n{'SERVICE':<15} {'CURRENT':<12} {'PREVIOUS':<12} {'CHANGE':<12} {'TREND'}")
    print("-" * 60)
    
    for service, costs in sorted(cost_data.items(), 
                                  key=lambda x: x[1]["current"], reverse=True):
        current = costs["current"]
        previous = costs["previous"]
        change = current - previous
        change_pct = (change / previous * 100) if previous > 0 else 0
        
        trend = "↑" if change > 0 else "↓" if change < 0 else "→"
        
        total_current += current
        total_previous += previous
        
        print(f"{service:<15} ${current:<11,.2f} ${previous:<11,.2f} "
              f"{'+'if change>=0 else ''}{change_pct:<10.1f}% {trend}")
    
    print("-" * 60)
    total_change = total_current - total_previous
    total_pct = (total_change / total_previous * 100) if total_previous > 0 else 0
    print(f"{'TOTAL':<15} ${total_current:<11,.2f} ${total_previous:<11,.2f} "
          f"{'+'if total_change>=0 else ''}{total_pct:.1f}%")
    
    # Recommendations
    print(f"\nRecommendations:")
    for service, costs in cost_data.items():
        change_pct = ((costs["current"] - costs["previous"]) / costs["previous"] * 100)
        if change_pct > 10:
            print(f"  [!] {service}: costs increased {change_pct:.1f}% — investigate usage")
    
    return cost_data

# Usage:
# generate_cost_report(days=30)
```

---

## Project Ideas for Your Portfolio

These projects demonstrate real DevOps skills to potential employers:

1. **GitOps Controller** — Watch a Git repository for changes and automatically apply Kubernetes manifests when they change.

2. **Secret Rotation Tool** — Automatically rotate database passwords, API keys, and certificates before they expire.

3. **Capacity Planner** — Collect historical resource usage data and predict when you will need to scale up.

4. **Compliance Checker** — Audit infrastructure against security standards (CIS benchmarks) and generate compliance reports.

5. **Migration Assistant** — Help migrate applications between cloud providers by analyzing dependencies and generating equivalent configurations.

---

## Exercises

**Exercise 1:** Extend the Health Dashboard to store historical results and show uptime percentages over the last 24 hours.

**Exercise 2:** Add email notifications to the Incident Response System using Python's `smtplib`.

**Exercise 3:** Extend the Release Manager to automatically update a CHANGELOG.md file with each release.

**Exercise 4:** Build a "Service Catalog" tool that reads service definitions from YAML files and generates a status page showing all services, their owners, and current health.

---

[Previous: Module 19 — Production Grade Python](19-production-grade-python.md) | [Next: Module 21 — DevOps Automation Patterns](21-devops-automation-patterns.md)
