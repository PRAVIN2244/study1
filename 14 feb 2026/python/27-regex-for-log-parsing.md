# Module 27 — Regex for Log Parsing and Text Processing

Regular expressions (regex) are patterns for matching text. In DevOps, you use them to parse log files, validate input, extract data from command output, and search configuration files.

---

## The re Module

Python's built-in `re` module provides regex support:

```python
import re

text = "Server started on port 8080"
match = re.search(r"port (\d+)", text)

if match:
    print(f"Port: {match.group(1)}")
```

**Output:**

```
Port: 8080
```

**How this works:**

1. `r"port (\d+)"` — the pattern: literal "port ", then one or more digits captured in a group
2. `re.search()` — scans the string for the first match
3. `match.group(1)` — returns the text captured by the first `(...)` group

The `r` prefix means "raw string" — backslashes are treated literally, which is important for regex patterns.

---

## Essential Regex Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `.` | Any single character | `a.c` matches "abc", "a1c" |
| `\d` | Any digit (0-9) | `\d+` matches "123" |
| `\w` | Any word character (letter, digit, _) | `\w+` matches "hello_1" |
| `\s` | Any whitespace (space, tab, newline) | `\s+` matches "  " |
| `*` | Zero or more of previous | `ab*c` matches "ac", "abc", "abbc" |
| `+` | One or more of previous | `ab+c` matches "abc", "abbc" (not "ac") |
| `?` | Zero or one of previous | `colou?r` matches "color", "colour" |
| `^` | Start of string | `^Error` matches "Error: ..." |
| `$` | End of string | `\.log$` matches "app.log" |
| `[abc]` | Any character in set | `[aeiou]` matches any vowel |
| `[^abc]` | Any character NOT in set | `[^0-9]` matches non-digits |
| `(...)` | Capture group | `(\d+)` captures digits |
| `\|` | OR | `cat\|dog` matches "cat" or "dog" |
| `{n}` | Exactly n times | `\d{4}` matches "2024" |
| `{n,m}` | Between n and m times | `\d{1,3}` matches "1" to "999" |

---

## Core Functions

### re.search() — Find First Match

```python
import re

log_line = "2024-01-15 08:23:01 ERROR Database connection failed: timeout"

match = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) (\w+) (.+)", log_line)

if match:
    print(f"Date: {match.group(1)}")
    print(f"Time: {match.group(2)}")
    print(f"Level: {match.group(3)}")
    print(f"Message: {match.group(4)}")
```

**Output:**

```
Date: 2024-01-15
Time: 08:23:01
Level: ERROR
Message: Database connection failed: timeout
```

### re.findall() — Find All Matches

```python
import re

text = "Servers: 10.0.1.5, 10.0.1.6, 10.0.2.10, 192.168.1.1"

ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", text)
print(ips)
```

**Output:**

```
['10.0.1.5', '10.0.1.6', '10.0.2.10', '192.168.1.1']
```

**How the pattern works:** `\d{1,3}` matches 1-3 digits. `\.` matches a literal dot (`.` alone matches any character, so we escape it with `\`). The pattern repeats for all four octets.

### re.match() — Match at Start Only

```python
import re

# re.match() only checks the BEGINNING of the string
print(re.match(r"ERROR", "ERROR: something broke"))     # Match
print(re.match(r"ERROR", "INFO: ERROR happened"))       # None (ERROR is not at start)

# re.search() checks ANYWHERE in the string
print(re.search(r"ERROR", "INFO: ERROR happened"))      # Match
```

**Rule:** Use `re.search()` unless you specifically need to match only at the start.

### re.sub() — Search and Replace

```python
import re

# Mask sensitive data in logs
log = "User alice logged in with token=abc123secret from 10.0.1.5"

masked = re.sub(r"token=\S+", "token=***REDACTED***", log)
print(masked)
```

**Output:**

```
User alice logged in with token=***REDACTED*** from 10.0.1.5
```

```python
# Replace multiple spaces with a single space
messy = "Name:    Alice     Age:   30"
clean = re.sub(r"\s+", " ", messy)
print(clean)
```

**Output:**

```
Name: Alice Age: 30
```

### re.split() — Split by Pattern

```python
import re

# Split on any whitespace (spaces, tabs, multiple spaces)
line = "web-01   running    8080   healthy"
parts = re.split(r"\s+", line)
print(parts)
```

**Output:**

```
['web-01', 'running', '8080', 'healthy']
```

---

## Named Groups

Instead of `group(1)`, `group(2)`, use named groups for readability:

```python
import re

log_line = "2024-01-15 08:23:01 ERROR Database connection failed"

pattern = r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<level>\w+) (?P<message>.+)"
match = re.search(pattern, log_line)

if match:
    print(f"Date: {match.group('date')}")
    print(f"Level: {match.group('level')}")
    print(f"Message: {match.group('message')}")
```

**Output:**

```
Date: 2024-01-15
Level: ERROR
Message: Database connection failed
```

**Syntax:** `(?P<name>pattern)` creates a named group. Access it with `match.group('name')`.

---

## Compiled Patterns

If you use the same pattern many times, compile it for better performance:

```python
import re

# Compile once
log_pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2}) "
    r"(?P<level>\w+) "
    r"(?P<message>.+)"
)

# Use many times
log_lines = [
    "2024-01-15 08:23:01 INFO Server started",
    "2024-01-15 08:24:02 WARNING High memory",
    "2024-01-15 08:25:30 ERROR Connection failed",
]

for line in log_lines:
    match = log_pattern.search(line)
    if match:
        print(f"  [{match.group('level')}] {match.group('message')}")
```

**Output:**

```
  [INFO] Server started
  [WARNING] High memory
  [ERROR] Connection failed
```

---

## Practical Examples

### Parsing Nginx Access Logs

```python
import re
from collections import Counter

# Nginx combined log format
nginx_pattern = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<date>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d+) (?P<size>\d+)'
)

sample_logs = [
    '10.0.1.5 - - [15/Jan/2024:08:23:01 +0000] "GET /api/users HTTP/1.1" 200 1234',
    '10.0.1.6 - - [15/Jan/2024:08:23:02 +0000] "POST /api/login HTTP/1.1" 401 89',
    '10.0.1.5 - - [15/Jan/2024:08:23:03 +0000] "GET /api/users HTTP/1.1" 200 1234',
    '10.0.2.10 - - [15/Jan/2024:08:23:04 +0000] "GET /health HTTP/1.1" 200 2',
    '10.0.1.7 - - [15/Jan/2024:08:23:05 +0000] "GET /api/data HTTP/1.1" 500 45',
]

status_counts = Counter()
path_counts = Counter()

for line in sample_logs:
    match = nginx_pattern.search(line)
    if match:
        status_counts[match.group("status")] += 1
        path_counts[match.group("path")] += 1

print("Status codes:")
for status, count in status_counts.most_common():
    print(f"  {status}: {count}")

print("\nTop paths:")
for path, count in path_counts.most_common(3):
    print(f"  {path}: {count}")
```

**Output:**

```
Status codes:
  200: 3
  401: 1
  500: 1

Top paths:
  /api/users: 2
  /api/login: 1
  /health: 1
```

### Extracting IPs from Security Logs

```python
import re
from collections import Counter

def find_failed_logins(log_file):
    """Find IPs with failed SSH login attempts."""
    pattern = re.compile(r"Failed password.+from (\d+\.\d+\.\d+\.\d+)")
    
    ip_counts = Counter()
    
    with open(log_file) as f:
        for line in f:
            match = pattern.search(line)
            if match:
                ip_counts[match.group(1)] += 1
    
    print("Failed login attempts by IP:")
    for ip, count in ip_counts.most_common(10):
        flag = " [BLOCK]" if count > 5 else ""
        print(f"  {ip}: {count} attempts{flag}")

# Usage:
# find_failed_logins("/var/log/auth.log")
```

### Validating Configuration Values

```python
import re

def validate_config(config):
    """Validate configuration values using regex."""
    errors = []
    
    # Validate IP address
    ip = config.get("server_ip", "")
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        errors.append(f"Invalid IP address: {ip}")
    
    # Validate port number
    port = str(config.get("port", ""))
    if not re.match(r"^\d{1,5}$", port) or not (1 <= int(port) <= 65535):
        errors.append(f"Invalid port: {port}")
    
    # Validate email
    email = config.get("admin_email", "")
    if not re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email):
        errors.append(f"Invalid email: {email}")
    
    # Validate hostname
    hostname = config.get("hostname", "")
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$", hostname):
        errors.append(f"Invalid hostname: {hostname}")
    
    return errors

# Usage:
config = {
    "server_ip": "10.0.1.5",
    "port": 8080,
    "admin_email": "admin@example.com",
    "hostname": "web-01.example.com"
}

errors = validate_config(config)
if errors:
    for e in errors:
        print(f"  [!!] {e}")
else:
    print("  Config is valid!")
```

### Masking Sensitive Data

```python
import re

def mask_secrets(text):
    """Mask passwords, tokens, and keys in text."""
    patterns = [
        (r'(password["\s:=]+)\S+', r'\1***'),
        (r'(token["\s:=]+)\S+', r'\1***'),
        (r'(api[_-]?key["\s:=]+)\S+', r'\1***'),
        (r'(secret["\s:=]+)\S+', r'\1***'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

# Usage:
log = '''
Connecting with password=SuperSecret123
Using API_KEY="abc-123-def-456"
Token: bearer_xyz789
'''

print(mask_secrets(log))
```

**Output:**

```
Connecting with password=***
Using API_KEY=***
Token: ***
```

---

## Exercises

**Exercise 1:** Write a regex that extracts all email addresses from a text string. Test with: `"Contact admin@example.com or support@company.org for help"`.

**Exercise 2:** Write a log parser that reads an Nginx access log and reports the top 10 IPs by request count, and the percentage of 5xx errors.

**Exercise 3:** Write a function that validates a list of hostnames against the pattern `[a-z0-9-]+\.[a-z]{2,}` and reports which ones are invalid.

**Exercise 4:** Write a function that extracts all environment variable references (`${VAR_NAME}` or `$VAR_NAME`) from a configuration file.

---

## Common Mistakes

### 1. Not Using Raw Strings

```python
# Bad — \d is interpreted as an escape sequence
pattern = "\d+"

# Good — r prefix treats backslashes literally
pattern = r"\d+"
```

### 2. Using re.match() When You Mean re.search()

`re.match()` only matches at the start of the string. Use `re.search()` to find patterns anywhere.

### 3. Overly Complex Regex

```python
# Bad — unreadable
pattern = r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"

# Good — use simpler pattern and validate in code
pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
match = re.match(pattern, ip)
if match:
    valid = all(0 <= int(g) <= 255 for g in match.groups())
```

### 4. Not Compiling Patterns Used in Loops

```python
# Bad — recompiles pattern on every iteration
for line in million_lines:
    re.search(r"ERROR (\w+)", line)

# Good — compile once
pattern = re.compile(r"ERROR (\w+)")
for line in million_lines:
    pattern.search(line)
```

---

## Summary

| Function | Purpose | Returns |
|----------|---------|---------|
| `re.search(pattern, text)` | Find first match anywhere | Match object or None |
| `re.match(pattern, text)` | Match at start only | Match object or None |
| `re.findall(pattern, text)` | Find all matches | List of strings |
| `re.sub(pattern, repl, text)` | Search and replace | New string |
| `re.split(pattern, text)` | Split by pattern | List of strings |
| `re.compile(pattern)` | Pre-compile for reuse | Pattern object |

---

[Previous: Module 26 — Exception Handling and Context Managers](26-exception-handling-and-context-managers.md) | [Back to Course Index](README.md)
