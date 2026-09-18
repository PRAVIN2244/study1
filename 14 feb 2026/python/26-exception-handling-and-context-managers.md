# Module 26 — Exception Handling and Context Managers

Errors happen. Servers go down, files are missing, APIs return unexpected data. Exception handling lets your code respond to errors gracefully instead of crashing. Context managers ensure resources (files, connections, locks) are properly cleaned up.

---

## What is an Exception?

An exception is Python's way of saying "something went wrong." When an error occurs, Python creates an exception object and stops normal execution:

```python
print(10 / 0)
```

**Output:**

```
Traceback (most recent call last):
  File "demo.py", line 1, in <module>
    print(10 / 0)
ZeroDivisionError: division by zero
```

**How to read this:**

1. `Traceback` — shows where the error happened (file, line number)
2. `ZeroDivisionError` — the type of error
3. `division by zero` — a human-readable description

Without exception handling, this crashes your program. With it, you can catch the error and decide what to do.

---

## try / except — Catching Errors

### Basic try/except

```python
try:
    result = 10 / 0
    print(result)
except ZeroDivisionError:
    print("Cannot divide by zero!")

print("Program continues normally.")
```

**Output:**

```
Cannot divide by zero!
Program continues normally.
```

**How this works:**

```
try block
    |
    +-- Python runs the code inside try
    |
    +-- If an error occurs:
    |       |
    |       v
    |   except block runs
    |       |
    |       v
    |   Program continues after except
    |
    +-- If NO error occurs:
            |
            v
        except block is SKIPPED
            |
            v
        Program continues after except
```

### Catching the Error Object

```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
```

**Output:**

```
Error type: ZeroDivisionError
Error message: division by zero
```

**Why `as e`:** It gives you access to the error object so you can log it, include it in a message, or make decisions based on it.

### Catching Multiple Exception Types

```python
def read_config(filepath):
    """Read a JSON config file with proper error handling."""
    import json
    
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {filepath}: {e}")
        return None
    except PermissionError:
        print(f"Permission denied: {filepath}")
        return None

config = read_config("config.json")
```

**Each `except` catches a different type of error.** Python checks them top to bottom and runs the first matching one.

**Catching multiple types in one line:**

```python
try:
    data = process_input(raw)
except (ValueError, TypeError) as e:
    print(f"Invalid input: {e}")
```

### The else Block — Runs Only on Success

```python
try:
    result = 10 / 2
except ZeroDivisionError:
    print("Division error!")
else:
    print(f"Result: {result}")    # Only runs if NO exception occurred
```

**Output:**

```
Result: 5.0
```

**Why use `else`:** It separates "code that might fail" (in `try`) from "code that should only run on success" (in `else`). This makes your intent clearer.

### The finally Block — Always Runs

```python
def connect_to_database():
    connection = None
    try:
        connection = open_connection("db.example.com")
        data = connection.query("SELECT * FROM users")
        return data
    except ConnectionError as e:
        print(f"Database error: {e}")
        return None
    finally:
        # This ALWAYS runs, even if an exception occurred
        if connection:
            connection.close()
            print("Connection closed.")
```

**Why `finally`:** It guarantees cleanup happens regardless of success or failure. Even if the function returns early or an exception is raised, `finally` still runs.

### Complete try/except/else/finally

```python
try:
    # Code that might fail
    result = risky_operation()
except SpecificError as e:
    # Handle the error
    log_error(e)
else:
    # Only runs if try succeeded (no exception)
    process_result(result)
finally:
    # Always runs, no matter what
    cleanup()
```

```
Execution Flow:
                try block
                    |
            +-------+-------+
            |               |
        Exception?       No exception
            |               |
            v               v
        except block    else block
            |               |
            +-------+-------+
                    |
                    v
              finally block
                    |
                    v
              Program continues
```

---

## Common Exception Types

| Exception | When It Happens | Example |
|-----------|----------------|---------|
| `FileNotFoundError` | File does not exist | `open("missing.txt")` |
| `PermissionError` | No access to file/resource | `open("/etc/shadow")` |
| `ValueError` | Wrong value type | `int("abc")` |
| `TypeError` | Wrong argument type | `len(42)` |
| `KeyError` | Dict key not found | `d["missing_key"]` |
| `IndexError` | List index out of range | `[1,2,3][10]` |
| `ConnectionError` | Network connection failed | `requests.get(bad_url)` |
| `TimeoutError` | Operation timed out | Network timeout |
| `ZeroDivisionError` | Division by zero | `10 / 0` |
| `ImportError` | Module not found | `import nonexistent` |
| `AttributeError` | Object has no attribute | `"hello".nonexistent()` |

---

## Raising Exceptions

You can raise exceptions yourself to signal errors:

```python
def deploy(version, environment):
    """Deploy with input validation."""
    if not version:
        raise ValueError("Version is required")
    
    if environment not in ("dev", "staging", "prod"):
        raise ValueError(f"Invalid environment: {environment}")
    
    if environment == "prod" and not version.startswith("v"):
        raise ValueError("Production versions must start with 'v'")
    
    print(f"Deploying {version} to {environment}")

# Usage:
try:
    deploy("", "staging")
except ValueError as e:
    print(f"Deployment error: {e}")
```

**Output:**

```
Deployment error: Version is required
```

### Custom Exceptions

```python
class DeploymentError(Exception):
    """Raised when a deployment fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

class ServiceUnavailableError(Exception):
    """Raised when a required service is not reachable."""
    def __init__(self, service_name, message="Service is unavailable"):
        self.service_name = service_name
        super().__init__(f"{message}: {service_name}")

# Usage:
try:
    raise ServiceUnavailableError("database")
except ServiceUnavailableError as e:
    print(f"Error: {e}")
    print(f"Service: {e.service_name}")
```

**Output:**

```
Error: Service is unavailable: database
Service: database
```

**Why custom exceptions:** They make error handling more specific. Instead of catching generic `Exception`, you can catch `DeploymentError` and handle it differently from `ConfigurationError`.

### Re-raising Exceptions

```python
import logging

logger = logging.getLogger("myapp")

def process_data(data):
    try:
        result = transform(data)
        return result
    except ValueError as e:
        logger.error(f"Data processing failed: {e}")
        raise    # Re-raise the same exception after logging it
```

**Why re-raise:** Sometimes you want to log an error but still let it propagate to the caller. `raise` without arguments re-raises the current exception.

---

## Context Managers — Automatic Resource Cleanup

### The Problem

Resources like files, database connections, and network sockets must be closed after use. Forgetting to close them causes resource leaks:

```python
# Bad — file might not be closed if an error occurs
f = open("data.txt")
data = f.read()
process(data)
f.close()    # What if process() raises an exception? f.close() never runs!
```

### The with Statement

```python
# Good — file is always closed, even if an error occurs
with open("data.txt") as f:
    data = f.read()
    process(data)
# f.close() is called automatically here
```

**How `with` works:**

```
with open("data.txt") as f:     # __enter__() is called → opens file
    data = f.read()              # Use the resource
    process(data)                # Even if this raises an exception...
                                 # __exit__() is called → closes file
```

The `with` statement guarantees that cleanup (`__exit__`) happens regardless of whether the block succeeds or fails.

### Writing Your Own Context Manager

**Method 1: Using a class**

```python
class Timer:
    """Context manager that measures execution time."""
    
    def __enter__(self):
        import time
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.elapsed = time.time() - self.start
        print(f"  Elapsed: {self.elapsed:.2f}s")
        return False    # Do not suppress exceptions

# Usage:
with Timer():
    import time
    time.sleep(1.5)
```

**Output:**

```
  Elapsed: 1.50s
```

**Method 2: Using `@contextmanager` (easier)**

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(label="Operation"):
    """Context manager that measures execution time."""
    start = time.time()
    try:
        yield    # Code inside the 'with' block runs here
    finally:
        elapsed = time.time() - start
        print(f"  {label}: {elapsed:.2f}s")

# Usage:
with timer("Database query"):
    time.sleep(0.5)

with timer("API call"):
    time.sleep(1.0)
```

**Output:**

```
  Database query: 0.50s
  API call: 1.00s
```

**How `@contextmanager` works:**

1. Code before `yield` runs when entering the `with` block (`__enter__`)
2. `yield` pauses the function — the code inside `with` runs
3. Code after `yield` (in `finally`) runs when exiting the `with` block (`__exit__`)

### Practical Context Manager: Deployment Lock

```python
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def deployment_lock(app_name):
    """Prevent concurrent deployments of the same app."""
    lock_file = Path(f"/tmp/{app_name}.deploy.lock")
    
    if lock_file.exists():
        pid = lock_file.read_text().strip()
        raise RuntimeError(
            f"Deployment already in progress for {app_name} (PID: {pid})"
        )
    
    # Create lock
    lock_file.write_text(str(os.getpid()))
    print(f"  Lock acquired for {app_name}")
    
    try:
        yield
    finally:
        # Always release lock
        lock_file.unlink(missing_ok=True)
        print(f"  Lock released for {app_name}")

# Usage:
with deployment_lock("myapp"):
    print("  Deploying...")
    # ... deployment logic ...
    print("  Deployment complete!")
```

**Output:**

```
  Lock acquired for myapp
  Deploying...
  Deployment complete!
  Lock released for myapp
```

Even if the deployment crashes, the lock file is removed in `finally`.

### Practical Context Manager: Temporary Directory

```python
from contextlib import contextmanager
from pathlib import Path
import tempfile
import shutil

@contextmanager
def temp_workspace(prefix="devops-"):
    """Create a temporary directory that is cleaned up automatically."""
    tmpdir = Path(tempfile.mkdtemp(prefix=prefix))
    print(f"  Created temp workspace: {tmpdir}")
    
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        print(f"  Cleaned up temp workspace: {tmpdir}")

# Usage:
with temp_workspace() as workspace:
    # Create files in the temp directory
    config = workspace / "config.json"
    config.write_text('{"version": "1.0"}')
    print(f"  Config written to: {config}")
    # ... do work ...

# Directory is automatically deleted here
```

### Nesting Context Managers

```python
with timer("Full deployment"):
    with deployment_lock("myapp"):
        with temp_workspace() as workspace:
            print(f"  Working in {workspace}")
            # ... deployment logic ...
```

**Cleaner with multiple `with`:**

```python
with (
    timer("Full deployment"),
    deployment_lock("myapp"),
    temp_workspace() as workspace
):
    print(f"  Working in {workspace}")
```

(Multiple `with` syntax requires Python 3.10+)

---

## Practical Example: Safe File Operations

```python
import json
import shutil
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def safe_file_write(filepath):
    """Write to a file safely using a temporary file.
    
    If writing fails, the original file is not corrupted.
    """
    path = Path(filepath)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    backup_path = path.with_suffix(path.suffix + ".bak")
    
    try:
        yield temp_path
        
        # Writing succeeded — replace original with temp
        if path.exists():
            shutil.copy2(path, backup_path)    # Backup original
        
        temp_path.rename(path)                  # Atomic replace
        
        if backup_path.exists():
            backup_path.unlink()                # Remove backup
        
    except Exception:
        # Writing failed — clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        raise

# Usage:
config = {"version": "2.0", "debug": False}

with safe_file_write("config.json") as temp_file:
    temp_file.write_text(json.dumps(config, indent=2))

print("Config updated safely!")
```

**Why this is better than direct writing:** If your script crashes while writing, the original file is not corrupted. The temp file is cleaned up, and the original remains intact.

---

## Exercises

**Exercise 1:** Write a function that reads a JSON file and returns its contents. Handle `FileNotFoundError`, `json.JSONDecodeError`, and `PermissionError` with appropriate messages.

**Exercise 2:** Create a custom exception `ValidationError` with a `field` attribute. Write a function `validate_config(config)` that raises `ValidationError` for missing required fields.

**Exercise 3:** Write a context manager `@contextmanager` called `log_block(name)` that logs when a block starts and ends, including the elapsed time and whether it succeeded or failed.

**Exercise 4:** Write a function that retries an operation up to 3 times, catching `ConnectionError` and `TimeoutError`, but letting other exceptions propagate immediately.

---

## Common Mistakes

### 1. Catching Too Broadly

```python
# Bad — catches everything, including bugs you should fix
try:
    result = process(data)
except Exception:
    pass    # Silently ignores ALL errors

# Good — catch specific exceptions
try:
    result = process(data)
except (ValueError, KeyError) as e:
    logger.error(f"Processing failed: {e}")
```

### 2. Using try/except for Flow Control

```python
# Bad — using exceptions for normal logic
try:
    value = my_dict["key"]
except KeyError:
    value = "default"

# Good — use .get() for dicts
value = my_dict.get("key", "default")
```

### 3. Not Cleaning Up Resources

```python
# Bad — connection leak if query fails
conn = open_connection()
data = conn.query("SELECT *")
conn.close()

# Good — context manager guarantees cleanup
with open_connection() as conn:
    data = conn.query("SELECT *")
```

### 4. Catching and Re-raising Wrong

```python
# Bad — loses the original traceback
try:
    risky()
except ValueError as e:
    raise ValueError(f"Failed: {e}")    # New exception, lost traceback

# Good — chain exceptions
try:
    risky()
except ValueError as e:
    raise ValueError(f"Failed: {e}") from e    # Preserves original traceback

# Or just re-raise
try:
    risky()
except ValueError:
    logger.error("Operation failed")
    raise    # Re-raises with original traceback
```

---

## Summary

| Concept | Syntax | Purpose |
|---------|--------|---------|
| `try/except` | `try: ... except Error:` | Catch and handle errors |
| `else` | `try: ... except: ... else:` | Run code only on success |
| `finally` | `try: ... finally:` | Always run cleanup code |
| `raise` | `raise ValueError("msg")` | Signal an error |
| Custom exception | `class MyError(Exception)` | Application-specific errors |
| `with` statement | `with resource as r:` | Automatic resource cleanup |
| `@contextmanager` | `yield` in a decorated function | Easy custom context managers |

---

[Previous: Module 25 — Generators and Decorators](25-generators-and-decorators.md) | [Next: Module 27 — Regex for Log Parsing and Text Processing](27-regex-for-log-parsing.md)
