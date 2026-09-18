# Module 22 — Interview Tips for DevOps Engineers

This module covers what interviewers look for when hiring DevOps engineers who use Python.

---

## What Interviewers Expect

DevOps interviews test three things:

1. **Can you write working Python code?** — Solve problems on a whiteboard or in a shared editor
2. **Do you understand DevOps concepts?** — Infrastructure, CI/CD, monitoring, security
3. **Can you automate real tasks?** — Not just theory, but practical automation

---

## Common Interview Questions

### Python Fundamentals

**Q: What is the difference between a list and a tuple?**

A list is mutable (can be changed after creation). A tuple is immutable (cannot be changed). Use tuples for data that should not change, like configuration values or database records.

```python
servers = ["web-01", "web-02"]    # List — can add/remove
config = ("prod", 8080, True)     # Tuple — fixed values
```

**Q: What is a decorator?**

A decorator wraps a function to add behavior without modifying the function itself:

```python
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper

@timer
def deploy(server):
    time.sleep(1)
    return f"Deployed to {server}"
```

**Q: Explain the difference between `==` and `is`.**

`==` checks if values are equal. `is` checks if two variables point to the same object in memory:

```python
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)    # True — same values
print(a is b)    # False — different objects

c = None
print(c is None)    # True — always use 'is' for None
```

### DevOps-Specific Questions

**Q: Write a script that checks if a list of servers are reachable.**

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def check_server(url):
    try:
        r = requests.get(url, timeout=5)
        return {"url": url, "status": r.status_code, "healthy": r.status_code == 200}
    except requests.exceptions.RequestException:
        return {"url": url, "status": "unreachable", "healthy": False}

servers = ["https://google.com", "https://github.com", "https://nonexistent.example.com"]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(check_server, servers))

for r in results:
    status = "OK" if r["healthy"] else "FAIL"
    print(f"  {r['url']}: {status}")
```

**Q: How would you handle secrets in a Python application?**

- Environment variables for runtime secrets
- `.env` files for local development (never committed)
- AWS Secrets Manager / HashiCorp Vault for production
- Never hardcode secrets in source code
- Never log secret values

**Q: Write a retry decorator with exponential backoff.**

```python
import time
import functools

def retry(max_attempts=3, base_delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, base_delay=2)
def call_api():
    # ... API call that might fail
    pass
```

---

## Coding Exercise Tips

1. **Clarify requirements** before writing code. Ask about edge cases, expected input/output, and constraints.

2. **Start with the simplest solution** that works. Optimize later if asked.

3. **Think out loud** — explain your approach as you code. Interviewers want to see your thought process.

4. **Handle errors** — production code needs error handling. Show that you think about failure cases.

5. **Use meaningful variable names** — `server_name` not `s`, `retry_count` not `rc`.

6. **Know the standard library** — `os`, `sys`, `json`, `pathlib`, `subprocess`, `logging`, `argparse`, `collections`, `datetime`.

---

## Portfolio Projects That Impress

1. **Infrastructure monitoring tool** with alerting
2. **CI/CD pipeline automation** (GitHub Actions + Python)
3. **Cloud resource auditor** (AWS/GCP cost and security)
4. **Log analysis tool** with pattern detection
5. **Deployment automation** with rollback support

Put these on GitHub with clear READMEs, tests, and documentation.

---

## Key Concepts to Know

| Topic | What to Know |
|-------|-------------|
| Data structures | Lists, dicts, sets, tuples — when to use each |
| File handling | Read/write files, JSON, YAML, CSV |
| Error handling | try/except, custom exceptions, logging |
| APIs | requests library, authentication, pagination |
| CLI tools | argparse, exit codes, subcommands |
| Concurrency | Threading vs multiprocessing vs asyncio |
| Testing | pytest basics, fixtures, assertions |
| Security | Secrets management, input validation |

---

[Previous: Module 21 — DevOps Automation Patterns](21-devops-automation-patterns.md) | [Next: Module 23 — Reusable Python Scripts](23-reusable-python-scripts.md)
