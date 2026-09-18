# Module 23 — Reusable Python Scripts

A collection of ready-to-use scripts for common DevOps tasks. Copy, modify, and integrate into your workflows.

---

## Script 1: Service Health Checker

```python
#!/usr/bin/env python3
"""Check health of multiple HTTP endpoints."""

import sys
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def check(endpoint):
    try:
        r = requests.get(endpoint["url"], timeout=endpoint.get("timeout", 5))
        return {**endpoint, "status": r.status_code,
                "healthy": r.status_code == endpoint.get("expected", 200),
                "time_ms": int(r.elapsed.total_seconds() * 1000)}
    except Exception as e:
        return {**endpoint, "status": str(e), "healthy": False, "time_ms": 0}

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "endpoints.json"
    endpoints = json.loads(Path(config_file).read_text())
    
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(check, endpoints))
    
    for r in results:
        status = "OK" if r["healthy"] else "FAIL"
        print(f"  [{status}] {r['name']}: {r['status']} ({r['time_ms']}ms)")
    
    failed = [r for r in results if not r["healthy"]]
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
```

---

## Script 2: Log Error Counter

```python
#!/usr/bin/env python3
"""Count errors in log files and show top error messages."""

import sys
import re
from collections import Counter
from pathlib import Path

def analyze_log(filepath):
    errors = Counter()
    total_lines = 0
    error_lines = 0
    
    with open(filepath) as f:
        for line in f:
            total_lines += 1
            if " ERROR " in line or " CRITICAL " in line:
                error_lines += 1
                # Extract the message part (after the log level)
                match = re.search(r"(ERROR|CRITICAL)\s+(.+)", line)
                if match:
                    errors[match.group(2).strip()[:80]] += 1
    
    return total_lines, error_lines, errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_errors.py <logfile> [logfile2 ...]")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        if not Path(filepath).exists():
            print(f"  File not found: {filepath}")
            continue
        
        total, errors, top_errors = analyze_log(filepath)
        error_rate = (errors / total * 100) if total > 0 else 0
        
        print(f"\n{filepath}:")
        print(f"  Total lines: {total:,}")
        print(f"  Error lines: {errors:,} ({error_rate:.1f}%)")
        
        if top_errors:
            print(f"  Top errors:")
            for msg, count in top_errors.most_common(5):
                print(f"    {count:>5}x  {msg}")

if __name__ == "__main__":
    main()
```

---

## Script 3: Environment Variable Checker

```python
#!/usr/bin/env python3
"""Verify that required environment variables are set."""

import os
import sys

REQUIRED = {
    "DB_HOST": "Database hostname",
    "DB_PASSWORD": "Database password",
    "API_KEY": "API authentication key",
    "ENVIRONMENT": "Deployment environment (dev/staging/prod)",
}

OPTIONAL = {
    "DB_PORT": ("Database port", "5432"),
    "LOG_LEVEL": ("Logging level", "INFO"),
    "WORKERS": ("Number of worker processes", "4"),
}

def check_env():
    missing = []
    
    print("Required variables:")
    for var, desc in REQUIRED.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            display = "****" if "PASSWORD" in var or "KEY" in var or "SECRET" in var else value
            print(f"  [OK] {var}={display}")
        else:
            print(f"  [!!] {var} — MISSING ({desc})")
            missing.append(var)
    
    print("\nOptional variables:")
    for var, (desc, default) in OPTIONAL.items():
        value = os.environ.get(var, default)
        source = "env" if os.environ.get(var) else "default"
        print(f"  [OK] {var}={value} ({source})")
    
    if missing:
        print(f"\nMissing {len(missing)} required variable(s): {', '.join(missing)}")
        return False
    
    print("\nAll required variables are set.")
    return True

if __name__ == "__main__":
    sys.exit(0 if check_env() else 1)
```

---

## Script 4: Quick File Backup

```python
#!/usr/bin/env python3
"""Create timestamped backups of files or directories."""

import shutil
import sys
from datetime import datetime
from pathlib import Path

def backup(source, backup_dir="backups"):
    source = Path(source)
    if not source.exists():
        print(f"Source not found: {source}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    dest_name = f"{source.stem}_{timestamp}{source.suffix}"
    dest = backup_path / dest_name
    
    if source.is_dir():
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)
    
    size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) if dest.is_dir() else dest.stat().st_size
    print(f"  Backed up: {source} -> {dest} ({size / 1024:.1f} KB)")
    return dest

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 backup.py <file_or_dir> [backup_dir]")
        sys.exit(1)
    
    backup_dir = sys.argv[2] if len(sys.argv) > 2 else "backups"
    backup(sys.argv[1], backup_dir)
```

---

## Script 5: Port Scanner

```python
#!/usr/bin/env python3
"""Scan common ports on a host."""

import socket
import sys
from concurrent.futures import ThreadPoolExecutor

COMMON_PORTS = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 3306: "MySQL",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 27017: "MongoDB", 9090: "Prometheus"
}

def scan_port(host, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return port, result == 0
    except socket.error:
        return port, False

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    
    print(f"Scanning {host}...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_port, host, port) for port in COMMON_PORTS]
        results = [f.result() for f in futures]
    
    open_ports = [(port, COMMON_PORTS[port]) for port, is_open in results if is_open]
    
    if open_ports:
        print(f"\nOpen ports:")
        for port, service in sorted(open_ports):
            print(f"  {port:>5}/tcp  {service}")
    else:
        print("No open ports found.")

if __name__ == "__main__":
    main()
```

---

## Script 6: JSON/YAML Converter

```python
#!/usr/bin/env python3
"""Convert between JSON and YAML formats."""

import sys
import json
import yaml
from pathlib import Path

def convert(input_file, output_file=None):
    path = Path(input_file)
    content = path.read_text()
    
    # Detect input format
    if path.suffix in (".yml", ".yaml"):
        data = yaml.safe_load(content)
        output_format = "json"
    elif path.suffix == ".json":
        data = json.loads(content)
        output_format = "yaml"
    else:
        print(f"Unknown format: {path.suffix}")
        sys.exit(1)
    
    # Convert
    if output_format == "json":
        output = json.dumps(data, indent=2)
        default_ext = ".json"
    else:
        output = yaml.dump(data, default_flow_style=False, sort_keys=False)
        default_ext = ".yaml"
    
    if output_file:
        Path(output_file).write_text(output)
        print(f"Converted: {input_file} -> {output_file}")
    else:
        print(output)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert.py <input_file> [output_file]")
        sys.exit(1)
    
    output = sys.argv[2] if len(sys.argv) > 2 else None
    convert(sys.argv[1], output)
```

---

## How to Use These Scripts

1. Save the script to a file (e.g., `health_check.py`)
2. Make it executable: `chmod +x health_check.py`
3. Run it: `python3 health_check.py` or `./health_check.py`
4. Add to your `PATH` or create aliases for frequent use

---

[Previous: Module 22 — Interview Tips](22-interview-tips.md) | [Next: Module 24 — Important Industry Tips](24-important-industry-tips.md)
