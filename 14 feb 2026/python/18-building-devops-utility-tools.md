# Module 18 — Building DevOps Utility Tools

This module brings together everything you have learned to build complete, production-ready tools. Each tool is a standalone project you can use immediately and extend for your own needs.

---

## Tool 1: Infrastructure Audit Tool

A CLI tool that audits your infrastructure across multiple dimensions:

```python
#!/usr/bin/env python3
"""Infrastructure audit tool — checks servers, services, and security."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import requests
import psutil

# --- Color helpers ---
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def ok(msg):    return f"{GREEN}[OK]{RESET} {msg}"
def warn(msg):  return f"{YELLOW}[!!]{RESET} {msg}"
def fail(msg):  return f"{RED}[FAIL]{RESET} {msg}"

# --- Checks ---

def check_system():
    """Check local system health."""
    findings = []
    
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    
    findings.append(ok(f"CPU: {cpu}%") if cpu < 80 else warn(f"CPU: {cpu}%"))
    findings.append(ok(f"Memory: {mem.percent}%") if mem.percent < 85
                    else warn(f"Memory: {mem.percent}%"))
    
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            if usage.percent > 90:
                findings.append(fail(f"Disk {part.mountpoint}: {usage.percent}%"))
            elif usage.percent > 80:
                findings.append(warn(f"Disk {part.mountpoint}: {usage.percent}%"))
            else:
                findings.append(ok(f"Disk {part.mountpoint}: {usage.percent}%"))
        except PermissionError:
            continue
    
    return findings

def check_endpoints(endpoints):
    """Check HTTP endpoint health."""
    findings = []
    
    def check_one(ep):
        try:
            resp = requests.get(ep["url"], timeout=ep.get("timeout", 5))
            expected = ep.get("expected_status", 200)
            if resp.status_code == expected:
                return ok(f"{ep['name']}: {resp.status_code} ({resp.elapsed.total_seconds():.2f}s)")
            else:
                return fail(f"{ep['name']}: expected {expected}, got {resp.status_code}")
        except requests.exceptions.RequestException as e:
            return fail(f"{ep['name']}: {e}")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        findings = list(executor.map(check_one, endpoints))
    
    return findings

def check_files(required_files):
    """Check that required files exist."""
    findings = []
    for filepath in required_files:
        if Path(filepath).exists():
            findings.append(ok(f"File exists: {filepath}"))
        else:
            findings.append(fail(f"Missing file: {filepath}"))
    return findings

# --- Main ---

def run_audit(config_file):
    """Run the full audit."""
    with open(config_file) as f:
        config = json.load(f)
    
    print(f"\nInfrastructure Audit — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_findings = []
    
    # System checks
    if config.get("check_system", True):
        print("\n--- System Health ---")
        findings = check_system()
        for f in findings:
            print(f"  {f}")
        all_findings.extend(findings)
    
    # Endpoint checks
    if "endpoints" in config:
        print("\n--- Endpoint Health ---")
        findings = check_endpoints(config["endpoints"])
        for f in findings:
            print(f"  {f}")
        all_findings.extend(findings)
    
    # File checks
    if "required_files" in config:
        print("\n--- Required Files ---")
        findings = check_files(config["required_files"])
        for f in findings:
            print(f"  {f}")
        all_findings.extend(findings)
    
    # Summary
    fail_count = sum(1 for f in all_findings if "[FAIL]" in f)
    warn_count = sum(1 for f in all_findings if "[!!]" in f)
    
    print(f"\n{'='*60}")
    print(f"Total checks: {len(all_findings)}")
    print(f"Passed: {len(all_findings) - fail_count - warn_count}")
    print(f"Warnings: {warn_count}")
    print(f"Failures: {fail_count}")
    
    return fail_count == 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Infrastructure audit tool")
    parser.add_argument("config", help="Path to audit config JSON file")
    args = parser.parse_args()
    
    success = run_audit(args.config)
    sys.exit(0 if success else 1)
```

**Example config file (`audit-config.json`):**

```json
{
  "check_system": true,
  "endpoints": [
    {"name": "Website", "url": "https://example.com"},
    {"name": "API", "url": "https://api.example.com/health"},
    {"name": "CDN", "url": "https://cdn.example.com/test.txt"}
  ],
  "required_files": [
    "/etc/nginx/nginx.conf",
    "/opt/myapp/config.json",
    ".env"
  ]
}
```

---

## Tool 2: Repository Cleanup Tool

A tool that finds and cleans up stale branches, large files, and other repository issues:

```python
#!/usr/bin/env python3
"""Repository cleanup tool — find stale branches, large files, and issues."""

import argparse
import git
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

def find_stale_branches(repo, days=30):
    """Find branches with no commits in the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stale = []
    
    for branch in repo.branches:
        if branch.name in ("main", "master", "develop"):
            continue
        
        last_commit = branch.commit
        if last_commit.committed_datetime < cutoff:
            age = (datetime.now(timezone.utc) - last_commit.committed_datetime).days
            stale.append({
                "name": branch.name,
                "last_commit": last_commit.committed_datetime.strftime("%Y-%m-%d"),
                "age_days": age,
                "author": last_commit.author.name
            })
    
    return sorted(stale, key=lambda b: b["age_days"], reverse=True)

def find_large_files(repo_path, min_size_mb=10):
    """Find files larger than min_size_mb."""
    large_files = []
    
    for filepath in Path(repo_path).rglob("*"):
        if ".git" in filepath.parts:
            continue
        if filepath.is_file():
            size_mb = filepath.stat().st_size / 1024 / 1024
            if size_mb >= min_size_mb:
                large_files.append({
                    "path": str(filepath.relative_to(repo_path)),
                    "size_mb": round(size_mb, 1)
                })
    
    return sorted(large_files, key=lambda f: f["size_mb"], reverse=True)

def check_gitignore(repo_path):
    """Check for common files that should be in .gitignore."""
    issues = []
    patterns = {
        "node_modules": "JavaScript dependencies",
        "__pycache__": "Python bytecode cache",
        ".env": "Environment variables (may contain secrets)",
        "venv": "Python virtual environment",
        ".DS_Store": "macOS metadata",
        "*.pyc": "Python compiled files",
    }
    
    for pattern, description in patterns.items():
        matches = list(Path(repo_path).rglob(pattern))
        # Filter out .git directory
        matches = [m for m in matches if ".git" not in m.parts]
        if matches:
            issues.append({
                "pattern": pattern,
                "description": description,
                "count": len(matches)
            })
    
    return issues

def run_cleanup(repo_path, stale_days=30, large_file_mb=10, delete_branches=False):
    """Run the full cleanup analysis."""
    repo = git.Repo(repo_path)
    
    print(f"\nRepository Cleanup Report: {repo_path}")
    print("=" * 60)
    
    # Stale branches
    stale = find_stale_branches(repo, days=stale_days)
    print(f"\n--- Stale Branches (no commits in {stale_days}+ days) ---")
    if stale:
        for b in stale:
            print(f"  {b['name']}: {b['age_days']}d old "
                  f"(last: {b['last_commit']} by {b['author']})")
        
        if delete_branches:
            for b in stale:
                repo.delete_head(b["name"], force=True)
                print(f"  Deleted: {b['name']}")
    else:
        print("  None found.")
    
    # Large files
    large = find_large_files(repo_path, min_size_mb=large_file_mb)
    print(f"\n--- Large Files (>{large_file_mb} MB) ---")
    if large:
        for f in large:
            print(f"  {f['path']}: {f['size_mb']} MB")
    else:
        print("  None found.")
    
    # Gitignore issues
    issues = check_gitignore(repo_path)
    print(f"\n--- Gitignore Issues ---")
    if issues:
        for issue in issues:
            print(f"  {issue['pattern']}: {issue['count']} occurrence(s) "
                  f"— {issue['description']}")
    else:
        print("  None found.")
    
    print(f"\n{'='*60}")
    print(f"Stale branches: {len(stale)}")
    print(f"Large files: {len(large)}")
    print(f"Gitignore issues: {len(issues)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repository cleanup tool")
    parser.add_argument("path", nargs="?", default=".", help="Repository path")
    parser.add_argument("--stale-days", type=int, default=30,
                        help="Days without commits to consider stale")
    parser.add_argument("--large-file-mb", type=int, default=10,
                        help="Minimum file size in MB to report")
    parser.add_argument("--delete-branches", action="store_true",
                        help="Actually delete stale branches")
    args = parser.parse_args()
    
    run_cleanup(args.path, args.stale_days, args.large_file_mb, args.delete_branches)
```

---

## Tool 3: Deployment Manager

A complete deployment tool with environment management, rollback, and notifications:

```python
#!/usr/bin/env python3
"""Deployment manager — deploy, rollback, and track releases."""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

DEPLOY_LOG = Path("deployments.json")

def load_deploy_history():
    """Load deployment history."""
    if DEPLOY_LOG.exists():
        return json.loads(DEPLOY_LOG.read_text())
    return []

def save_deploy_history(history):
    """Save deployment history."""
    DEPLOY_LOG.write_text(json.dumps(history, indent=2, default=str))

def deploy(app, version, environment, dry_run=False):
    """Deploy an application version to an environment."""
    print(f"\nDeploying {app} v{version} to {environment}")
    print("-" * 40)
    
    steps = [
        ("Pulling latest code", 1),
        ("Running tests", 2),
        ("Building artifacts", 1.5),
        ("Deploying to servers", 2),
        ("Running health checks", 1),
    ]
    
    for step_name, duration in steps:
        if dry_run:
            print(f"  [DRY RUN] {step_name}")
        else:
            print(f"  {step_name}...", end=" ", flush=True)
            time.sleep(duration * 0.1)    # Shortened for demo
            print("done")
    
    # Record deployment
    record = {
        "app": app,
        "version": version,
        "environment": environment,
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "dry_run": dry_run
    }
    
    if not dry_run:
        history = load_deploy_history()
        history.append(record)
        save_deploy_history(history)
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Deployment complete!")
    return True

def rollback(app, environment):
    """Rollback to the previous version."""
    history = load_deploy_history()
    
    # Find the last two deployments for this app/environment
    relevant = [d for d in history
                if d["app"] == app and d["environment"] == environment
                and not d.get("dry_run")]
    
    if len(relevant) < 2:
        print(f"No previous version to rollback to for {app} in {environment}")
        return False
    
    current = relevant[-1]
    previous = relevant[-2]
    
    print(f"\nRollback: {app} in {environment}")
    print(f"  Current:  v{current['version']} (deployed {current['timestamp']})")
    print(f"  Rolling back to: v{previous['version']}")
    
    return deploy(app, previous["version"], environment)

def show_history(app=None, environment=None, limit=10):
    """Show deployment history."""
    history = load_deploy_history()
    
    if app:
        history = [d for d in history if d["app"] == app]
    if environment:
        history = [d for d in history if d["environment"] == environment]
    
    history = history[-limit:]
    
    print(f"\nDeployment History (last {limit}):")
    print(f"{'APP':<15} {'VERSION':<10} {'ENV':<12} {'STATUS':<10} {'TIME'}")
    print("-" * 65)
    
    for d in reversed(history):
        timestamp = d["timestamp"][:19]
        print(f"{d['app']:<15} {d['version']:<10} {d['environment']:<12} "
              f"{d['status']:<10} {timestamp}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deployment manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy an application")
    deploy_parser.add_argument("app", help="Application name")
    deploy_parser.add_argument("version", help="Version to deploy")
    deploy_parser.add_argument("--env", default="staging", help="Target environment")
    deploy_parser.add_argument("--dry-run", action="store_true")
    
    # rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to previous version")
    rollback_parser.add_argument("app", help="Application name")
    rollback_parser.add_argument("--env", default="staging")
    
    # history command
    history_parser = subparsers.add_parser("history", help="Show deployment history")
    history_parser.add_argument("--app", help="Filter by app")
    history_parser.add_argument("--env", help="Filter by environment")
    history_parser.add_argument("--limit", type=int, default=10)
    
    args = parser.parse_args()
    
    if args.command == "deploy":
        deploy(args.app, args.version, args.env, args.dry_run)
    elif args.command == "rollback":
        rollback(args.app, args.env)
    elif args.command == "history":
        show_history(args.app, args.env, args.limit)
    else:
        parser.print_help()
```

**Usage:**

```bash
python3 deploy_manager.py deploy myapp 2.3.1 --env staging
python3 deploy_manager.py deploy myapp 2.3.2 --env staging
python3 deploy_manager.py history --app myapp
python3 deploy_manager.py rollback myapp --env staging
```

---

## Tool 4: Environment Diff Tool

Compare configurations across environments:

```python
#!/usr/bin/env python3
"""Compare configuration files across environments."""

import argparse
import json
import yaml
from pathlib import Path

def load_config(filepath):
    """Load a config file (JSON or YAML)."""
    path = Path(filepath)
    content = path.read_text()
    
    if path.suffix in (".yml", ".yaml"):
        return yaml.safe_load(content)
    elif path.suffix == ".json":
        return json.loads(content)
    else:
        # Try JSON first, then YAML
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)

def diff_configs(config1, config2, path=""):
    """Recursively diff two config dictionaries."""
    diffs = []
    
    all_keys = set(list(config1.keys()) + list(config2.keys()))
    
    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        
        if key not in config1:
            diffs.append({"path": current_path, "type": "added",
                         "value": config2[key]})
        elif key not in config2:
            diffs.append({"path": current_path, "type": "removed",
                         "value": config1[key]})
        elif isinstance(config1[key], dict) and isinstance(config2[key], dict):
            diffs.extend(diff_configs(config1[key], config2[key], current_path))
        elif config1[key] != config2[key]:
            diffs.append({"path": current_path, "type": "changed",
                         "old": config1[key], "new": config2[key]})
    
    return diffs

def print_diff(diffs, env1_name, env2_name):
    """Print config differences."""
    if not diffs:
        print("  No differences found.")
        return
    
    for d in diffs:
        if d["type"] == "added":
            print(f"  + {d['path']}: {d['value']} (only in {env2_name})")
        elif d["type"] == "removed":
            print(f"  - {d['path']}: {d['value']} (only in {env1_name})")
        elif d["type"] == "changed":
            print(f"  ~ {d['path']}:")
            print(f"      {env1_name}: {d['old']}")
            print(f"      {env2_name}: {d['new']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare config files")
    parser.add_argument("file1", help="First config file")
    parser.add_argument("file2", help="Second config file")
    parser.add_argument("--name1", default="env1", help="Name for first environment")
    parser.add_argument("--name2", default="env2", help="Name for second environment")
    args = parser.parse_args()
    
    config1 = load_config(args.file1)
    config2 = load_config(args.file2)
    
    print(f"\nConfig Diff: {args.name1} vs {args.name2}")
    print("=" * 50)
    
    diffs = diff_configs(config1, config2)
    print_diff(diffs, args.name1, args.name2)
    
    print(f"\nTotal differences: {len(diffs)}")
```

---

## Exercises

**Exercise 1:** Extend the Infrastructure Audit Tool to check SSL certificate expiration dates for HTTPS endpoints.

**Exercise 2:** Add a `--format json` option to the Repository Cleanup Tool that outputs results as JSON instead of text.

**Exercise 3:** Add Slack notifications to the Deployment Manager — send a message when a deployment starts, succeeds, or fails.

**Exercise 4:** Build a "Service Dependency Checker" that reads a config file listing services and their dependencies, then checks if all dependencies are healthy before allowing a deployment.

---

## Design Principles for DevOps Tools

1. **Always support dry-run mode** — let users preview changes before applying them
2. **Use exit codes** — 0 for success, non-zero for failure, so scripts can chain tools
3. **Accept configuration from files** — do not hardcode URLs, thresholds, or server lists
4. **Log what you do** — print each step so users can follow along and debug issues
5. **Handle errors gracefully** — catch exceptions, print useful messages, clean up resources
6. **Make tools composable** — output structured data (JSON) that other tools can consume

---

[Previous: Module 17 — Parallel and Async Automation](17-parallel-and-async-automation.md) | [Next: Module 19 — Production Grade Python](19-production-grade-python.md)
