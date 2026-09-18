# Module 17 — Parallel and Async Automation

When you need to deploy to 50 servers, check 100 endpoints, or process thousands of log files, doing them one at a time is too slow. Python offers three approaches for running tasks concurrently: threading, multiprocessing, and asyncio.

---

## When to Use What

| Approach | Best For | How It Works |
|----------|---------|-------------|
| **Threading** | I/O-bound tasks (API calls, file reads, network) | Multiple threads share one process |
| **Multiprocessing** | CPU-bound tasks (data processing, calculations) | Multiple processes with separate memory |
| **asyncio** | Many I/O-bound tasks (hundreds of API calls) | Single thread, cooperative multitasking |

**Rule of thumb:**
- Waiting for network/disk? → Threading or asyncio
- Heavy computation? → Multiprocessing
- Hundreds of concurrent I/O operations? → asyncio

---

## Threading — Concurrent I/O Operations

### Basic Threading

```python
import threading
import time

def check_server(name, delay):
    """Simulate checking a server."""
    print(f"  Checking {name}...")
    time.sleep(delay)    # Simulate network delay
    print(f"  {name}: OK ({delay}s)")

# Sequential — one at a time
start = time.time()
check_server("web-01", 2)
check_server("web-02", 2)
check_server("api-01", 2)
print(f"Sequential: {time.time() - start:.1f}s\n")

# Threaded — all at once
start = time.time()
threads = []
for name, delay in [("web-01", 2), ("web-02", 2), ("api-01", 2)]:
    t = threading.Thread(target=check_server, args=(name, delay))
    threads.append(t)
    t.start()

for t in threads:
    t.join()    # Wait for all threads to finish

print(f"Threaded: {time.time() - start:.1f}s")
```

**Output:**

```
  Checking web-01...
  web-01: OK (2s)
  Checking web-02...
  web-02: OK (2s)
  Checking api-01...
  api-01: OK (2s)
Sequential: 6.0s

  Checking web-01...
  Checking web-02...
  Checking api-01...
  web-01: OK (2s)
  web-02: OK (2s)
  api-01: OK (2s)
Threaded: 2.0s
```

**Why 3x faster:** All three checks run simultaneously. The total time is the longest single check (2s), not the sum (6s).

### ThreadPoolExecutor — The Easier Way

`concurrent.futures` provides a higher-level interface:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time

def check_url(url):
    """Check if a URL is reachable."""
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        elapsed = time.time() - start
        return {"url": url, "status": response.status_code, "time": elapsed}
    except requests.exceptions.RequestException as e:
        return {"url": url, "status": "ERROR", "time": 0, "error": str(e)}

urls = [
    "https://httpbin.org/get",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/2",
    "https://api.github.com",
    "https://httpbin.org/status/200",
]

start = time.time()

# max_workers controls how many threads run simultaneously
with ThreadPoolExecutor(max_workers=5) as executor:
    # Submit all tasks
    futures = {executor.submit(check_url, url): url for url in urls}
    
    # Process results as they complete
    for future in as_completed(futures):
        result = future.result()
        print(f"  {result['url']}: {result['status']} ({result['time']:.2f}s)")

print(f"\nTotal: {time.time() - start:.1f}s (vs ~5s sequential)")
```

**Output (example):**

```
  https://httpbin.org/status/200: 200 (0.18s)
  https://httpbin.org/get: 200 (0.22s)
  https://api.github.com: 200 (0.35s)
  https://httpbin.org/delay/1: 200 (1.15s)
  https://httpbin.org/delay/2: 200 (2.20s)

Total: 2.2s (vs ~5s sequential)
```

**How `as_completed` works:** It yields futures as they finish, not in submission order. The fastest results come first.

### Collecting Results with map()

```python
from concurrent.futures import ThreadPoolExecutor

def deploy_to_server(server):
    """Simulate deploying to a server."""
    import time
    time.sleep(1)    # Simulate deployment
    return f"{server}: deployed"

servers = ["web-01", "web-02", "web-03", "api-01", "api-02"]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(deploy_to_server, servers))

for result in results:
    print(f"  {result}")
```

**How `map()` differs from `submit()`:** `map()` returns results in the same order as the input. `submit()` with `as_completed()` returns results in completion order.

---

## Multiprocessing — CPU-Bound Tasks

Threading does not speed up CPU-bound work in Python due to the GIL (Global Interpreter Lock). Use multiprocessing instead:

```python
from concurrent.futures import ProcessPoolExecutor
import time

def analyze_log_file(filename):
    """CPU-intensive log analysis (simulated)."""
    # Simulate heavy processing
    total = sum(i * i for i in range(1_000_000))
    return {"file": filename, "result": total}

log_files = [f"app-{i}.log" for i in range(8)]

# Sequential
start = time.time()
sequential_results = [analyze_log_file(f) for f in log_files]
print(f"Sequential: {time.time() - start:.1f}s")

# Parallel with multiprocessing
start = time.time()
with ProcessPoolExecutor(max_workers=4) as executor:
    parallel_results = list(executor.map(analyze_log_file, log_files))
print(f"Parallel (4 workers): {time.time() - start:.1f}s")
```

**Output (example):**

```
Sequential: 4.8s
Parallel (4 workers): 1.4s
```

**Why multiprocessing is faster for CPU work:** Each worker runs in a separate Python process with its own GIL. True parallel execution on multiple CPU cores.

---

## asyncio — High-Concurrency I/O

asyncio is ideal when you need hundreds or thousands of concurrent I/O operations:

```python
import asyncio
import aiohttp
import time

async def check_url(session, url):
    """Check a URL asynchronously."""
    try:
        start = time.time()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            elapsed = time.time() - start
            return {"url": url, "status": response.status, "time": elapsed}
    except Exception as e:
        return {"url": url, "status": "ERROR", "time": 0}

async def check_all_urls(urls):
    """Check all URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

urls = [
    "https://httpbin.org/get",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/2",
    "https://api.github.com",
    "https://httpbin.org/status/200",
]

start = time.time()
results = asyncio.run(check_all_urls(urls))

for r in results:
    print(f"  {r['url']}: {r['status']} ({r['time']:.2f}s)")

print(f"\nTotal: {time.time() - start:.1f}s")
```

**Key concepts:**

- `async def` — defines a coroutine (an async function)
- `await` — pauses the coroutine until the result is ready, letting other coroutines run
- `asyncio.gather()` — runs multiple coroutines concurrently
- `asyncio.run()` — starts the async event loop

**When to use asyncio over threading:** When you have hundreds of concurrent I/O operations. asyncio uses less memory than threads (no thread stack per task).

> **Note:** asyncio requires `aiohttp` for HTTP requests (`pip install aiohttp`). The standard `requests` library is synchronous and cannot be used with asyncio.

---

## Practical Example: Parallel Server Deployment

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def deploy_to_server(server, version, dry_run=False):
    """Deploy an application to a server."""
    if dry_run:
        time.sleep(0.5)
        return {"server": server, "status": "DRY_RUN", "duration": 0.5}
    
    # Simulate deployment steps
    time.sleep(2)    # Download
    time.sleep(1)    # Install
    time.sleep(0.5)  # Restart
    
    return {"server": server, "status": "SUCCESS", "duration": 3.5}

def parallel_deploy(servers, version, max_workers=5, dry_run=False):
    """Deploy to multiple servers in parallel."""
    print(f"\nDeploying v{version} to {len(servers)} servers "
          f"(workers: {max_workers})")
    print("-" * 50)
    
    start = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(deploy_to_server, server, version, dry_run): server
            for server in servers
        }
        
        for future in as_completed(futures):
            server = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(f"  {result['server']}: {result['status']} "
                      f"({result['duration']:.1f}s)")
            except Exception as e:
                results.append({"server": server, "status": "FAILED", "error": str(e)})
                print(f"  {server}: FAILED ({e})")
    
    total_time = time.time() - start
    succeeded = sum(1 for r in results if r["status"] in ("SUCCESS", "DRY_RUN"))
    failed = len(results) - succeeded
    
    print(f"\nResults: {succeeded} succeeded, {failed} failed")
    print(f"Total time: {total_time:.1f}s")
    
    return results

# Usage:
servers = [f"web-{i:02d}" for i in range(1, 11)]    # web-01 through web-10
parallel_deploy(servers, "2.3.1", max_workers=5, dry_run=True)
```

---

## Practical Example: Parallel Health Checker

```python
from concurrent.futures import ThreadPoolExecutor
import requests
import time

def health_check(endpoint):
    """Check a single endpoint."""
    try:
        start = time.time()
        response = requests.get(endpoint["url"], timeout=endpoint.get("timeout", 5))
        elapsed = (time.time() - start) * 1000
        
        healthy = response.status_code == endpoint.get("expected_status", 200)
        
        return {
            "name": endpoint["name"],
            "url": endpoint["url"],
            "status": response.status_code,
            "response_ms": round(elapsed),
            "healthy": healthy
        }
    except Exception as e:
        return {
            "name": endpoint["name"],
            "url": endpoint["url"],
            "status": "ERROR",
            "response_ms": 0,
            "healthy": False,
            "error": str(e)
        }

def parallel_health_check(endpoints, max_workers=10):
    """Check all endpoints in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(health_check, endpoints))
    
    print(f"\n{'NAME':<20} {'STATUS':<8} {'TIME':<10} {'HEALTH'}")
    print("-" * 50)
    
    for r in results:
        health = "OK" if r["healthy"] else "FAIL"
        print(f"{r['name']:<20} {str(r['status']):<8} {r['response_ms']:<10}ms {health}")
    
    healthy_count = sum(1 for r in results if r["healthy"])
    print(f"\n{healthy_count}/{len(results)} endpoints healthy")
    
    return results

# Usage:
endpoints = [
    {"name": "Website", "url": "https://example.com"},
    {"name": "API", "url": "https://api.github.com"},
    {"name": "CDN", "url": "https://httpbin.org/get"},
]

parallel_health_check(endpoints)
```

---

## Thread Safety

When multiple threads access shared data, you need synchronization:

```python
import threading
from concurrent.futures import ThreadPoolExecutor

# Bad — race condition
counter = 0

def increment_unsafe():
    global counter
    for _ in range(100000):
        counter += 1    # Not thread-safe!

# Good — use a lock
lock = threading.Lock()
safe_counter = 0

def increment_safe():
    global safe_counter
    for _ in range(100000):
        with lock:
            safe_counter += 1

# Demonstrate the problem
counter = 0
with ThreadPoolExecutor(max_workers=4) as executor:
    for _ in range(4):
        executor.submit(increment_unsafe)

print(f"Unsafe counter: {counter} (expected 400000)")

safe_counter = 0
with ThreadPoolExecutor(max_workers=4) as executor:
    for _ in range(4):
        executor.submit(increment_safe)

print(f"Safe counter: {safe_counter} (expected 400000)")
```

**Output (example):**

```
Unsafe counter: 287543 (expected 400000)
Safe counter: 400000 (expected 400000)
```

**Why the unsafe counter is wrong:** Multiple threads read and write `counter` simultaneously, causing lost updates. The `lock` ensures only one thread modifies the counter at a time.

> **Best practice:** Avoid shared mutable state when possible. Instead, have each thread return its result and combine them afterward.

---

## Exercises

**Exercise 1:** Write a script that downloads 10 web pages in parallel using ThreadPoolExecutor and measures the speedup vs sequential.

**Exercise 2:** Write a parallel file processor that reads all `.log` files in a directory, counts ERROR lines in each, and prints a summary.

**Exercise 3:** Build a parallel deployment tool that deploys to a list of servers (from a config file), with configurable concurrency and a progress indicator.

**Exercise 4:** Write an async health checker using asyncio that checks 50 URLs concurrently and reports results.

---

## Common Mistakes

### 1. Using Threading for CPU-Bound Work

```python
# Bad — threading does not speed up CPU work
with ThreadPoolExecutor() as executor:
    executor.map(cpu_heavy_function, data)

# Good — use multiprocessing for CPU work
with ProcessPoolExecutor() as executor:
    executor.map(cpu_heavy_function, data)
```

### 2. Too Many Workers

```python
# Bad — 1000 threads overwhelm the system
with ThreadPoolExecutor(max_workers=1000) as executor:
    ...

# Good — reasonable number
with ThreadPoolExecutor(max_workers=20) as executor:
    ...
```

### 3. Not Handling Exceptions in Threads

```python
# Bad — exception is silently swallowed
future = executor.submit(risky_function)

# Good — check for exceptions
future = executor.submit(risky_function)
try:
    result = future.result()
except Exception as e:
    print(f"Task failed: {e}")
```

### 4. Forgetting to Join Threads

```python
# Bad — program exits before threads finish
for t in threads:
    t.start()
# Missing: t.join()

# Good
for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## Summary

| Approach | Use Case | Key Class | Max Concurrency |
|----------|---------|-----------|----------------|
| Threading | I/O-bound (network, disk) | `ThreadPoolExecutor` | 10-50 workers |
| Multiprocessing | CPU-bound (computation) | `ProcessPoolExecutor` | Number of CPU cores |
| asyncio | High-concurrency I/O | `asyncio.gather()` | Hundreds to thousands |

---

[Previous: Module 16 — Monitoring Automation](16-monitoring-automation.md) | [Next: Module 18 — Building DevOps Utility Tools](18-building-devops-utility-tools.md)
