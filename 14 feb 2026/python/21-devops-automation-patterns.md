# Module 21 — DevOps Automation Patterns

These patterns appear repeatedly in DevOps automation. Learn them once, apply them everywhere.

---

## Pattern 1: Retry with Exponential Backoff

When a service is temporarily unavailable, retry with increasing delays:

```python
import time
import random

def retry_with_backoff(func, max_retries=5, base_delay=1, max_delay=60):
    """Retry a function with exponential backoff and jitter."""
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise
            
            # Exponential backoff: 1s, 2s, 4s, 8s, 16s...
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            
            # Add jitter (randomness) to prevent thundering herd
            delay = delay * (0.5 + random.random())
            
            print(f"  Attempt {attempt}/{max_retries} failed: {e}")
            print(f"  Retrying in {delay:.1f}s...")
            time.sleep(delay)

# Usage:
import requests

def call_api():
    response = requests.get("https://api.example.com/data", timeout=5)
    response.raise_for_status()
    return response.json()

# result = retry_with_backoff(call_api)
```

**Why exponential backoff:** If a service is overloaded, retrying immediately makes it worse. Increasing delays give the service time to recover.

**Why jitter:** If 100 clients all retry at exactly the same intervals, they hit the service simultaneously. Random jitter spreads the load.

---

## Pattern 2: Circuit Breaker

Stop calling a service that is clearly down, and periodically check if it has recovered:

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Service is down, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Prevent cascading failures by stopping calls to failing services."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                print("  Circuit: HALF_OPEN (testing recovery)")
            else:
                raise RuntimeError("Circuit breaker is OPEN — service unavailable")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                print("  Circuit: CLOSED (service recovered)")
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                print(f"  Circuit: OPEN (after {self.failure_count} failures)")
            
            raise

# Usage:
# breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
# try:
#     result = breaker.call(requests.get, "https://api.example.com/data")
# except RuntimeError:
#     print("Service unavailable, using cached data")
```

---

## Pattern 3: Idempotency

An operation is idempotent if running it multiple times produces the same result as running it once:

```python
import json
from pathlib import Path

def ensure_directory(path):
    """Create a directory if it does not exist (idempotent)."""
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_config(filepath, default_config):
    """Create a config file only if it does not exist (idempotent)."""
    path = Path(filepath)
    if not path.exists():
        path.write_text(json.dumps(default_config, indent=2))
        print(f"  Created: {filepath}")
    else:
        print(f"  Already exists: {filepath}")

def ensure_user_exists(username):
    """Create a system user if they do not exist (idempotent)."""
    import subprocess
    result = subprocess.run(["id", username], capture_output=True)
    if result.returncode != 0:
        subprocess.run(["useradd", username])
        print(f"  Created user: {username}")
    else:
        print(f"  User exists: {username}")
```

**Why idempotency matters:** Automation scripts may run multiple times (retries, cron jobs, CI/CD reruns). If your script is not idempotent, running it twice might create duplicate resources, corrupt data, or fail.

**Rule:** Before creating something, check if it already exists. Before deleting something, check if it is already gone.

---

## Pattern 4: Dry Run

Always let users preview changes before applying them:

```python
def deploy(servers, version, dry_run=False):
    """Deploy to servers with optional dry-run mode."""
    for server in servers:
        if dry_run:
            print(f"  [DRY RUN] Would deploy v{version} to {server}")
        else:
            print(f"  Deploying v{version} to {server}...")
            # actual deployment logic

# Usage:
# deploy(servers, "2.3.1", dry_run=True)    # Preview
# deploy(servers, "2.3.1", dry_run=False)   # Execute
```

**Rule:** Every destructive operation (delete, deploy, modify) should support `dry_run=True`.

---

## Pattern 5: Configuration as Code

Store configuration in files, not in code:

```python
import json
import yaml
from pathlib import Path

def load_config(config_file, environment=None):
    """Load configuration from a file with optional environment override."""
    path = Path(config_file)
    
    if path.suffix in (".yml", ".yaml"):
        config = yaml.safe_load(path.read_text())
    else:
        config = json.loads(path.read_text())
    
    # Apply environment-specific overrides
    if environment and environment in config.get("environments", {}):
        env_config = config["environments"][environment]
        config.update(env_config)
    
    return config

# Config file (config.yaml):
# defaults:
#   timeout: 30
#   retries: 3
# environments:
#   production:
#     timeout: 60
#     retries: 5
#   staging:
#     timeout: 15
#     retries: 2
```

---

## Pattern 6: Health Check Before and After

Always verify the state before and after making changes:

```python
def safe_deploy(app, version, servers):
    """Deploy with pre and post health checks."""
    
    # Pre-check
    print("Pre-deployment health check...")
    if not check_health(servers):
        print("Pre-check FAILED — aborting deployment")
        return False
    
    # Deploy
    print(f"Deploying {app} v{version}...")
    deploy(app, version, servers)
    
    # Post-check
    print("Post-deployment health check...")
    if not check_health(servers):
        print("Post-check FAILED — rolling back")
        rollback(app, servers)
        return False
    
    print("Deployment successful!")
    return True
```

---

## Pattern 7: Graceful Shutdown

Handle interrupts and clean up resources:

```python
import signal
import sys

class GracefulShutdown:
    """Handle shutdown signals gracefully."""
    
    def __init__(self):
        self.should_stop = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)
    
    def _handler(self, signum, frame):
        print("\nShutdown signal received. Cleaning up...")
        self.should_stop = True

# Usage in a monitoring loop:
shutdown = GracefulShutdown()

while not shutdown.should_stop:
    # do work
    time.sleep(1)

print("Cleanup complete. Exiting.")
```

---

## Pattern Summary

| Pattern | When to Use | Key Benefit |
|---------|------------|-------------|
| Retry with backoff | Transient failures | Automatic recovery |
| Circuit breaker | Persistent failures | Prevent cascading failures |
| Idempotency | Repeated operations | Safe to re-run |
| Dry run | Destructive operations | Preview before apply |
| Config as code | Environment settings | No hardcoded values |
| Health checks | Deployments | Catch problems early |
| Graceful shutdown | Long-running processes | Clean resource cleanup |

---

[Previous: Module 20 — Real Industry DevOps Projects](20-real-industry-devops-projects.md) | [Next: Module 22 — Interview Tips](22-interview-tips.md)
