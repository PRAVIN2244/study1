# Module 19 — Production Grade Python

Writing code that works is step one. Writing code that works reliably in production — handling errors, logging properly, managing secrets, and being maintainable — is what separates scripts from tools your team can depend on.

---

## Structured Logging

### Why Not Just print()?

`print()` works for debugging but fails in production:
- No timestamps
- No severity levels
- Cannot be filtered or routed
- Cannot be sent to log aggregation systems

### Python's logging Module

```python
import logging

# Basic setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("myapp")

logger.debug("Detailed debugging info")      # Not shown (level is INFO)
logger.info("Application started")           # Shown
logger.warning("Disk usage at 85%")          # Shown
logger.error("Database connection failed")   # Shown
logger.critical("System out of memory")      # Shown
```

**Output:**

```
2024-01-15 14:30:00 [INFO] myapp: Application started
2024-01-15 14:30:00 [WARNING] myapp: Disk usage at 85%
2024-01-15 14:30:00 [ERROR] myapp: Database connection failed
2024-01-15 14:30:00 [CRITICAL] myapp: System out of memory
```

### Logging to a File

```python
import logging

def setup_logging(log_file="app.log", level=logging.INFO):
    """Configure logging to both console and file."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    
    logger.addHandler(console)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging("deploy.log")
logger.info("Deployment started")
```

### JSON Logging

For log aggregation systems (ELK, Datadog, CloudWatch):

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields
        for key in ("server", "version", "environment"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        
        return json.dumps(log_entry)

# Setup
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("myapp")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Deployment started", extra={"server": "web-01", "version": "2.3.1"})
```

**Output:**

```json
{"timestamp": "2024-01-15T14:30:00.000000", "level": "INFO", "logger": "myapp", "message": "Deployment started", "server": "web-01", "version": "2.3.1"}
```

---

## Error Handling

### The try/except Pattern

```python
import logging

logger = logging.getLogger("myapp")

def connect_to_database(host, port):
    """Connect to a database with proper error handling."""
    try:
        # Simulate connection
        if host == "bad-host":
            raise ConnectionError(f"Cannot connect to {host}:{port}")
        
        logger.info(f"Connected to database at {host}:{port}")
        return True
    
    except ConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    
    except Exception as e:
        # Catch unexpected errors
        logger.exception(f"Unexpected error connecting to database: {e}")
        return False
    
    finally:
        # This always runs, even if an exception occurred
        logger.debug("Connection attempt completed")
```

**Key rules:**

1. **Catch specific exceptions** — `except ConnectionError` is better than bare `except`
2. **Use `logger.exception()`** — it includes the full traceback in the log
3. **Use `finally`** — for cleanup that must happen regardless of success or failure
4. **Never silently swallow exceptions** — always log or re-raise

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
    pass

def deploy(app, version, environment):
    """Deploy with custom exceptions."""
    if not app:
        raise ConfigurationError("Application name is required")
    
    if environment not in ("dev", "staging", "prod"):
        raise ConfigurationError(f"Invalid environment: {environment}")
    
    try:
        # ... deployment logic ...
        pass
    except ConnectionError:
        raise ServiceUnavailableError(f"Cannot reach deployment target")

# Usage:
try:
    deploy("myapp", "2.3.1", "staging")
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(2)
except ServiceUnavailableError as e:
    logger.error(f"Service unavailable: {e}")
    sys.exit(3)
except DeploymentError as e:
    logger.error(f"Deployment failed: {e}")
    sys.exit(1)
```

---

## Secrets Management

### Environment Variables

```python
import os
import sys

def get_required_env(name):
    """Get a required environment variable or exit."""
    value = os.environ.get(name)
    if not value:
        print(f"Error: {name} environment variable is required")
        sys.exit(1)
    return value

# Usage:
db_password = get_required_env("DB_PASSWORD")
api_key = get_required_env("API_KEY")
```

### .env Files with python-dotenv

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

db_host = os.getenv("DB_HOST", "localhost")
db_port = int(os.getenv("DB_PORT", "5432"))
db_password = os.getenv("DB_PASSWORD")
```

**.env file:**

```
DB_HOST=db.example.com
DB_PORT=5432
DB_PASSWORD=supersecret
API_KEY=key-12345
```

> **Security rules:**
> - Never commit `.env` files to version control
> - Add `.env` to `.gitignore`
> - Never log or print secret values
> - Use different secrets for each environment

### Configuration Class

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration from environment variables."""
    db_host: str
    db_port: int
    db_name: str
    db_password: str
    api_key: str
    environment: str
    debug: bool
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "myapp"),
            db_password=os.environ["DB_PASSWORD"],    # Required — raises KeyError
            api_key=os.environ["API_KEY"],
            environment=os.getenv("ENVIRONMENT", "dev"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )

# Usage:
try:
    config = Config.from_env()
    print(f"Environment: {config.environment}")
    print(f"Database: {config.db_host}:{config.db_port}/{config.db_name}")
    print(f"Debug: {config.debug}")
except KeyError as e:
    print(f"Missing required environment variable: {e}")
    sys.exit(1)
```

---

## Testing

### Writing Tests with pytest

```bash
pip install pytest
```

```python
# file: calculator.py
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

```python
# file: test_calculator.py
import pytest
from calculator import add, divide

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_divide():
    assert divide(10, 2) == 5
    assert divide(7, 2) == 3.5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
```

**Run tests:**

```bash
pytest -v
```

**Output:**

```
test_calculator.py::test_add PASSED
test_calculator.py::test_divide PASSED
test_calculator.py::test_divide_by_zero PASSED

3 passed in 0.02s
```

### Testing with Fixtures

```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def sample_config(tmp_path):
    """Create a temporary config file for testing."""
    config = {
        "app_name": "test-app",
        "port": 8080,
        "debug": True
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    return config_file

def test_load_config(sample_config):
    """Test that config loading works."""
    config = json.loads(sample_config.read_text())
    assert config["app_name"] == "test-app"
    assert config["port"] == 8080

@pytest.fixture
def mock_server_list():
    """Provide a list of test servers."""
    return [
        {"name": "web-01", "ip": "10.0.1.1", "status": "running"},
        {"name": "web-02", "ip": "10.0.1.2", "status": "stopped"},
    ]

def test_count_running_servers(mock_server_list):
    running = [s for s in mock_server_list if s["status"] == "running"]
    assert len(running) == 1
```

### Parametrized Tests — Test Many Inputs at Once

```python
import pytest

def calculate_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    else: return "F"

@pytest.mark.parametrize("score, expected", [
    (95, "A"),
    (90, "A"),
    (85, "B"),
    (80, "B"),
    (75, "C"),
    (65, "D"),
    (50, "F"),
    (0, "F"),
])
def test_calculate_grade(score, expected):
    assert calculate_grade(score) == expected
```

**Output:**

```
test_grades.py::test_calculate_grade[95-A] PASSED
test_grades.py::test_calculate_grade[90-A] PASSED
test_grades.py::test_calculate_grade[85-B] PASSED
...
8 passed in 0.01s
```

**Why parametrize:** Instead of writing 8 separate test functions, you write one and provide the test data as parameters.

### Mocking — Testing Without Real Dependencies

When your code calls an API, database, or external service, you do not want tests to depend on those services being available:

```python
from unittest.mock import patch, MagicMock
import requests

def check_server(url):
    """Check if a server is healthy."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Test WITHOUT actually making HTTP requests
@patch("requests.get")
def test_check_server_healthy(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    assert check_server("https://example.com") is True

@patch("requests.get")
def test_check_server_down(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError()
    assert check_server("https://example.com") is False
```

**How mocking works:**

```
Without mock:                    With mock:

check_server()                   check_server()
      |                                |
      v                                v
  requests.get() -----> Internet   mock_get() -----> Returns fake response
      |                                |
      v                                v
  Real response                  Controlled response
  (slow, unreliable)             (fast, predictable)
```

### Test Coverage

Measure how much of your code is tested:

```bash
pip install pytest-cov
pytest --cov=myapp --cov-report=term-missing
```

**Output:**

```
---------- coverage: ----------
Name                 Stmts   Miss  Cover   Missing
----------------------------------------------------
myapp/deploy.py         45      8    82%   34-41
myapp/monitor.py        30      2    93%   28-29
myapp/utils.py          20      0   100%
----------------------------------------------------
TOTAL                   95     10    89%
```

**What the numbers mean:**

- `Stmts` — total lines of code
- `Miss` — lines not covered by any test
- `Cover` — percentage of lines tested
- `Missing` — specific line numbers not tested

**Target:** Aim for 80%+ coverage on production code. 100% is not always practical or necessary.

### Test Organization

```
myproject/
├── src/
│   ├── deploy.py
│   ├── monitor.py
│   └── utils.py
├── tests/
│   ├── test_deploy.py
│   ├── test_monitor.py
│   └── test_utils.py
├── requirements.txt
└── pytest.ini
```

**pytest.ini:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

### Testing Workflow

```
Write code
    |
    v
Write tests
    |
    v
Run tests (pytest -v)
    |
    +---- All pass? -----> Commit
    |
    +---- Failures? -----> Fix code or tests
    |
    v
Check coverage (pytest --cov)
    |
    v
Add to CI/CD pipeline
```

---

## Code Organization

### Project Structure

```
myapp/
├── myapp/
│   ├── __init__.py
│   ├── cli.py           # CLI entry point
│   ├── config.py         # Configuration management
│   ├── deploy.py         # Deployment logic
│   ├── monitor.py        # Monitoring logic
│   └── utils.py          # Shared utilities
├── tests/
│   ├── test_deploy.py
│   └── test_monitor.py
├── .env.example          # Example environment variables
├── .gitignore
├── Makefile
├── README.md
├── requirements.txt
└── setup.py
```

### Makefile for Common Tasks

```makefile
.PHONY: install test lint run clean

install:
	pip install -r requirements.txt

test:
	pytest -v --tb=short

lint:
	flake8 myapp/ tests/
	
run:
	python -m myapp.cli

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
```

### requirements.txt Best Practices

```
# Pin exact versions for reproducibility
requests==2.31.0
psutil==5.9.7
pyyaml==6.0.1
python-dotenv==1.0.0

# Development dependencies (separate file: requirements-dev.txt)
# pytest==7.4.4
# flake8==7.0.0
```

---

## Type Hints

Type hints make code self-documenting and enable IDE autocompletion. They do not affect runtime behavior — Python does not enforce them. They are for humans and tools.

### Basic Type Hints

```python
# Variables
name: str = "web-01"
port: int = 8080
is_running: bool = True
cpu_usage: float = 45.5

# Functions
def greet(name: str) -> str:
    return f"Hello, {name}"

def deploy(
    app_name: str,
    version: str,
    environment: str = "staging",
    dry_run: bool = False,
    timeout: int = 300
) -> bool:
    """Deploy an application. Returns True if succeeded."""
    ...
```

**How to read `-> bool`:** The function returns a boolean value.

### Common Types from the typing Module

```python
from typing import Optional, Union

# Optional — value can be the type OR None
def get_server_status(host: str) -> Optional[dict]:
    """Returns server info dict, or None if unreachable."""
    ...

# Union — value can be one of several types
def parse_port(value: Union[str, int]) -> int:
    """Accept port as string or int."""
    return int(value)
```

### Collection Types

```python
# Python 3.9+ — use built-in types directly
def process_servers(servers: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {"running": 0, "stopped": 0}
    for server in servers:
        status = server.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts

def get_endpoints() -> list[str]:
    return ["https://api.example.com", "https://web.example.com"]

def get_config() -> dict[str, str | int | bool]:
    return {"host": "localhost", "port": 8080, "debug": True}
```

### Type Checking with mypy

Type hints are not enforced at runtime. Use `mypy` to check them statically:

```bash
pip install mypy
mypy your_script.py
```

```python
# file: demo.py
def add(a: int, b: int) -> int:
    return a + b

result = add("hello", "world")    # Bug! Passing strings to int function
```

```bash
mypy demo.py
```

**Output:**

```
demo.py:4: error: Argument 1 to "add" has incompatible type "str"; expected "int"
demo.py:4: error: Argument 2 to "add" has incompatible type "str"; expected "int"
```

**Why use mypy:** It catches type errors before your code runs in production. Add it to your CI/CD pipeline.

### When to Use Type Hints

- **Always:** Function signatures (parameters and return types)
- **Often:** Class attributes and important variables
- **Skip:** Obvious local variables where the type is clear from context

```python
# Good — type hints on function signature
def check_health(url: str, timeout: int = 5) -> bool:
    response = requests.get(url, timeout=timeout)    # No hint needed — obvious
    return response.status_code == 200
```

---

## Context Managers

Use context managers for resource cleanup:

```python
import time
import logging
from contextlib import contextmanager

logger = logging.getLogger("myapp")

@contextmanager
def timer(label):
    """Measure and log execution time."""
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.info(f"{label}: {elapsed:.2f}s")

@contextmanager
def deployment_lock(app_name):
    """Prevent concurrent deployments of the same app."""
    lock_file = Path(f"/tmp/{app_name}.lock")
    
    if lock_file.exists():
        raise RuntimeError(f"Deployment already in progress for {app_name}")
    
    lock_file.write_text(str(os.getpid()))
    try:
        yield
    finally:
        lock_file.unlink(missing_ok=True)

# Usage:
with timer("Database migration"):
    # ... migration code ...
    pass

with deployment_lock("myapp"):
    # ... deployment code ...
    pass
```

---

## Exercises

**Exercise 1:** Add structured logging (with JSON output) to one of the tools from Module 18.

**Exercise 2:** Write tests for the `diff_configs` function from Module 18's Environment Diff Tool.

**Exercise 3:** Create a configuration class that loads settings from environment variables with validation (required fields, type checking, value ranges).

**Exercise 4:** Refactor one of your earlier scripts to follow the project structure shown above, with proper error handling, logging, and a Makefile.

---

## Common Mistakes

### 1. Bare except Clauses

```python
# Bad — catches everything, including KeyboardInterrupt
try:
    do_something()
except:
    pass

# Good — catch specific exceptions
try:
    do_something()
except (ConnectionError, TimeoutError) as e:
    logger.error(f"Connection failed: {e}")
```

### 2. Logging Secrets

```python
# Bad
logger.info(f"Connecting with password: {password}")

# Good
logger.info(f"Connecting to {host}:{port} as {username}")
```

### 3. No Tests

If you do not test it, it will break in production. Start with the most important functions and add tests incrementally.

### 4. Monolithic Scripts

```python
# Bad — 500-line script with everything in one file

# Good — split into modules
from myapp.config import Config
from myapp.deploy import deploy
from myapp.monitor import check_health
```

---

## Summary

| Practice | Tool/Pattern | Why |
|----------|-------------|-----|
| Logging | `logging` module | Timestamps, levels, file output |
| Error handling | `try/except/finally` | Graceful failure, cleanup |
| Secrets | Environment variables, `.env` | Keep secrets out of code |
| Testing | `pytest` | Catch bugs before production |
| Type hints | `typing` module | Self-documenting, IDE support |
| Project structure | Packages, Makefile | Maintainability |
| Context managers | `with` statement | Resource cleanup |

---

[Previous: Module 18 — Building DevOps Utility Tools](18-building-devops-utility-tools.md) | [Next: Module 20 — Real Industry DevOps Projects](20-real-industry-devops-projects.md)
