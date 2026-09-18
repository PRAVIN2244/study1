# Module 25 — Generators and Decorators

Two intermediate Python features that appear frequently in DevOps automation. Generators handle large data efficiently. Decorators add behavior to functions without modifying them.

---

## Generators — Lazy Evaluation

### The Problem: Memory

Imagine you need to process a 10 GB log file. Loading it all into memory at once would crash your script:

```python
# Bad — loads entire file into memory
lines = open("huge.log").readlines()    # 10 GB in RAM!

# Good — processes one line at a time
for line in open("huge.log"):           # Only one line in RAM at a time
    process(line)
```

Generators work the same way — they produce values one at a time instead of creating the entire collection in memory.

### Your First Generator

A generator function uses `yield` instead of `return`:

```python
def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1

# Use it
for number in count_up_to(5):
    print(number)
```

**Output:**

```
1
2
3
4
5
```

**How this works:**

1. `count_up_to(5)` does not run the function — it creates a generator object
2. Each time the `for` loop asks for the next value, the function runs until it hits `yield`
3. `yield i` sends the value back and **pauses** the function
4. Next iteration, the function **resumes** from where it paused
5. When the function ends (no more `yield`), the loop stops

### yield vs return

```python
# return — function runs once, gives back one value, done
def get_numbers_return():
    return [1, 2, 3, 4, 5]    # Creates entire list in memory

# yield — function produces values one at a time
def get_numbers_yield():
    for i in range(1, 6):
        yield i                 # Produces one value, pauses, resumes
```

```python
result = get_numbers_return()
print(type(result))
print(result)

gen = get_numbers_yield()
print(type(gen))
print(list(gen))
```

**Output:**

```
<class 'list'>
[1, 2, 3, 4, 5]
<class 'generator'>
[1, 2, 3, 4, 5]
```

**Key difference:** The list version creates all 5 values in memory at once. The generator version creates them one at a time. For 5 values this does not matter. For 10 million values, it matters a lot.

### Generator Expressions

Like list comprehensions, but with parentheses instead of brackets:

```python
# List comprehension — creates entire list in memory
squares_list = [x ** 2 for x in range(1000000)]

# Generator expression — creates values on demand
squares_gen = (x ** 2 for x in range(1000000))

print(type(squares_list))
print(type(squares_gen))
```

**Output:**

```
<class 'list'>
<class 'generator'>
```

```python
# Memory comparison
import sys

squares_list = [x ** 2 for x in range(1000000)]
squares_gen = (x ** 2 for x in range(1000000))

print(f"List size: {sys.getsizeof(squares_list):,} bytes")
print(f"Generator size: {sys.getsizeof(squares_gen):,} bytes")
```

**Output:**

```
List size: 8,448,728 bytes
Generator size: 200 bytes
```

**Why:** The list stores all 1 million values. The generator stores only the logic to produce them.

### Practical Example: Log File Scanner

```python
def scan_log_lines(filepath, pattern):
    """Yield lines from a log file that match a pattern."""
    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            if pattern in line:
                yield line_num, line.strip()

# Process matches one at a time — works with any file size
for line_num, line in scan_log_lines("/var/log/syslog", "ERROR"):
    print(f"  Line {line_num}: {line}")
    
    # Stop after first 10 matches
    if line_num > 100:
        break
```

**Why this is better than loading the whole file:** The generator reads one line at a time. Even a 50 GB log file works because only one line is in memory at any moment.

### Practical Example: Paginated API Results

```python
import requests

def fetch_all_pages(base_url, per_page=100):
    """Yield items from a paginated API, one page at a time."""
    page = 1
    while True:
        response = requests.get(base_url, params={"page": page, "per_page": per_page})
        items = response.json()
        
        if not items:
            break
        
        for item in items:
            yield item
        
        page += 1

# Use it — processes items as they arrive
for repo in fetch_all_pages("https://api.github.com/users/octocat/repos"):
    print(f"  {repo['name']}")
```

### Generator Pipeline

Chain generators together to build processing pipelines:

```python
def read_lines(filepath):
    """Read lines from a file."""
    with open(filepath) as f:
        for line in f:
            yield line.strip()

def filter_errors(lines):
    """Keep only ERROR lines."""
    for line in lines:
        if "ERROR" in line:
            yield line

def extract_message(lines):
    """Extract the message part after the log level."""
    for line in lines:
        parts = line.split("ERROR", 1)
        if len(parts) > 1:
            yield parts[1].strip()

# Pipeline: read -> filter -> extract
lines = read_lines("app.log")
errors = filter_errors(lines)
messages = extract_message(errors)

for msg in messages:
    print(f"  {msg}")
```

**How the pipeline works:**

```
read_lines() --yields--> filter_errors() --yields--> extract_message()
     |                        |                           |
  all lines              ERROR lines only            message text only
```

Each generator pulls from the previous one. No intermediate lists are created. The entire file is processed with minimal memory.

---

## Decorators — Adding Behavior to Functions

### The Problem

You want to add timing, logging, or retry logic to many functions. Without decorators, you would copy-paste the same code into every function.

### Your First Decorator

```python
import time

def timer(func):
    """Decorator that measures how long a function takes."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "done"

result = slow_function()
print(result)
```

**Output:**

```
  slow_function took 1.00s
done
```

**How this works step by step:**

1. `@timer` above `slow_function` is syntactic sugar for `slow_function = timer(slow_function)`
2. `timer(func)` receives the original function and returns `wrapper`
3. When you call `slow_function()`, you are actually calling `wrapper()`
4. `wrapper` records the start time, calls the original function, records the end time, prints the duration, and returns the result

```
Without decorator:              With decorator:

slow_function()                 slow_function()
      |                               |
      v                               v
  runs directly                 wrapper() runs
                                      |
                                      +-- records start time
                                      +-- calls original slow_function()
                                      +-- records end time
                                      +-- prints duration
                                      +-- returns result
```

### Decorator with Arguments

```python
import functools
import time

def retry(max_attempts=3, delay=1):
    """Decorator that retries a function on failure."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    print(f"  Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def call_api():
    """Simulate an API call that might fail."""
    import random
    if random.random() < 0.7:
        raise ConnectionError("Server unavailable")
    return {"status": "ok"}

# result = call_api()
```

**What `@functools.wraps(func)` does:** It preserves the original function's name and docstring. Without it, `call_api.__name__` would return `"wrapper"` instead of `"call_api"`.

### Practical Decorator: Logging

```python
import functools
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("myapp")

def log_call(func):
    """Log function calls with arguments and return values."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_str = ", ".join([repr(a) for a in args])
        kwargs_str = ", ".join([f"{k}={v!r}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        
        logger.info(f"Calling {func.__name__}({all_args})")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} returned {result!r}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper

@log_call
def deploy(server, version, dry_run=False):
    if dry_run:
        return "dry-run"
    return "deployed"

deploy("web-01", "2.3.1", dry_run=True)
```

**Output:**

```
2024-01-15 14:30:00 [INFO] Calling deploy('web-01', '2.3.1', dry_run=True)
2024-01-15 14:30:00 [INFO] deploy returned 'dry-run'
```

### Practical Decorator: Require Environment Variable

```python
import os
import functools

def require_env(var_name):
    """Decorator that checks for a required environment variable."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not os.environ.get(var_name):
                raise EnvironmentError(
                    f"Environment variable {var_name} is required for {func.__name__}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_env("AWS_ACCESS_KEY_ID")
def list_s3_buckets():
    """List S3 buckets (requires AWS credentials)."""
    import boto3
    s3 = boto3.client("s3")
    return s3.list_buckets()
```

### Stacking Multiple Decorators

```python
@timer
@log_call
@retry(max_attempts=3)
def deploy_service(name, version):
    # ... deployment logic ...
    pass
```

**Execution order:** Decorators are applied bottom-up. The call goes through `timer` → `log_call` → `retry` → `deploy_service`.

---

## Exercises

**Exercise 1:** Write a generator `fibonacci(n)` that yields the first `n` Fibonacci numbers (1, 1, 2, 3, 5, 8, ...).

**Exercise 2:** Write a generator `tail(filepath, n=10)` that yields the last `n` lines of a file (like the `tail` command).

**Exercise 3:** Write a `@timer` decorator that logs the execution time of any function. Test it with a function that sleeps for a random duration.

**Exercise 4:** Write a `@cache` decorator that caches function results based on arguments (so calling `f(3)` twice only computes once). Test it with a function that computes factorials.

---

## Common Mistakes

### 1. Trying to Reuse a Generator

```python
gen = (x ** 2 for x in range(5))

print(list(gen))    # [0, 1, 4, 9, 16]
print(list(gen))    # [] — empty! Generator is exhausted
```

**Why:** A generator can only be iterated once. After it is exhausted, it produces no more values. Create a new generator if you need to iterate again.

### 2. Forgetting @functools.wraps

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def hello():
    """Say hello."""
    print("hello")

print(hello.__name__)    # 'wrapper' — wrong!
print(hello.__doc__)     # None — lost!
```

**Fix:** Add `@functools.wraps(func)` above `def wrapper`.

### 3. Confusing yield and return

```python
def bad_generator():
    return [1, 2, 3]    # This is NOT a generator — it returns a list

def good_generator():
    yield 1
    yield 2
    yield 3              # This IS a generator
```

---

## Summary

| Concept | What It Does | When to Use |
|---------|-------------|-------------|
| `yield` | Produce values one at a time | Large data, streaming, pipelines |
| Generator expression | `(x for x in items)` | Memory-efficient iteration |
| Generator pipeline | Chain generators | Multi-step data processing |
| `@decorator` | Wrap a function with extra behavior | Logging, timing, retry, auth |
| `functools.wraps` | Preserve original function metadata | Always use in decorators |

---

[Previous: Module 24 — Important Industry Tips](24-important-industry-tips.md) | [Next: Module 26 — Exception Handling and Context Managers](26-exception-handling-and-context-managers.md)
