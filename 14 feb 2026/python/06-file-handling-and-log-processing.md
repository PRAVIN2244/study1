# Module 6 — File Handling and Log Processing

Programs need to read and write files. A calculator that loses all results when you close it is not useful. Files let you save data permanently, read input data, and process large amounts of information like log files and CSV data.

---

## Writing Files

Before we can read files, we need to create one. Let's start with writing:

```python
with open("greeting.txt", "w") as f:
    f.write("Hello, World!\n")
    f.write("Welcome to Python.\n")
    f.write("Let's learn file handling.\n")

print("File created!")
```

**Output:**

```
File created!
```

**What this does:**

1. `open("greeting.txt", "w")` — opens (or creates) a file named `greeting.txt` for **w**riting
2. `as f` — gives the file object the name `f`
3. `f.write(...)` — writes text to the file. `\n` adds a newline at the end of each line
4. The `with` block automatically closes the file when done

**The file `greeting.txt` now contains:**

```
Hello, World!
Welcome to Python.
Let's learn file handling.
```

### What "w" Mode Does

`"w"` means **write** — it creates the file if it does not exist, and **overwrites** it if it does:

```python
# First write
with open("data.txt", "w") as f:
    f.write("First version\n")

# Second write — REPLACES the file
with open("data.txt", "w") as f:
    f.write("Second version\n")

with open("data.txt", "r") as f:
    print(f.read())
```

**Output:**

```
Second version
```

**Why:** The second `open("data.txt", "w")` erased the first version. If you want to add to a file without erasing, use `"a"` (append) mode.

### Appending to a File

```python
with open("log.txt", "w") as f:
    f.write("Line 1\n")

with open("log.txt", "a") as f:
    f.write("Line 2\n")
    f.write("Line 3\n")

with open("log.txt", "r") as f:
    print(f.read())
```

**Output:**

```
Line 1
Line 2
Line 3
```

**Why:** `"a"` mode opens the file for **a**ppending — new content is added at the end without erasing existing content.

**File mode decision diagram:**

```
What do you want to do?
        |
   +----+----+----+
   |         |         |
   v         v         v
  Read     Write     Append
   |         |         |
   v         v         v
 "r"       "w"       "a"
   |         |         |
   v         v         v
 File must  Creates   Creates
 exist      or ERASES or adds
            file      to end
```

---

## Reading Files

### Reading the Entire File

```python
with open("greeting.txt", "r") as f:
    content = f.read()

print(content)
print(type(content))
```

**Output:**

```
Hello, World!
Welcome to Python.
Let's learn file handling.

<class 'str'>
```

**What this does:** `f.read()` reads the entire file into a single string. The `"r"` mode means **r**ead (this is the default, so `open("greeting.txt")` works too).

### Reading Line by Line

```python
with open("greeting.txt", "r") as f:
    for line in f:
        print(f">> {line}")
```

**Output:**

```
>> Hello, World!

>> Welcome to Python.

>> Let's learn file handling.

```

**Why the blank lines?** Each line in the file ends with `\n`. The `print()` function also adds a newline. So you get double spacing.

**Fix — strip the newline:**

```python
with open("greeting.txt", "r") as f:
    for line in f:
        print(f">> {line.strip()}")
```

**Output:**

```
>> Hello, World!
>> Welcome to Python.
>> Let's learn file handling.
```

**Why:** `.strip()` removes whitespace (including `\n`) from both ends of the string.

### Reading All Lines into a List

```python
with open("greeting.txt", "r") as f:
    lines = f.readlines()

print(lines)
print(f"Number of lines: {len(lines)}")
```

**Output:**

```
['Hello, World!\n', 'Welcome to Python.\n', "Let's learn file handling.\n"]
Number of lines: 3
```

**Why:** `f.readlines()` returns a list where each element is one line (including the `\n`).

### Checking if a File Exists

```python
import os

if os.path.exists("greeting.txt"):
    print("File exists!")
else:
    print("File not found.")
```

**Output:**

```
File exists!
```

**Why this matters:** If you try to open a file that does not exist for reading, you get an error:

```python
with open("nonexistent.txt", "r") as f:
    content = f.read()
```

**Error:**

```
FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent.txt'
```

Always check if a file exists before reading, or use `try/except` to handle the error.

---

## The with Statement — Why It Matters

You might wonder why we use `with open(...) as f:` instead of just `f = open(...)`. Here is why:

```python
# Without with — you must remember to close
f = open("greeting.txt", "r")
content = f.read()
f.close()    # Easy to forget!
```

```python
# With with — file is closed automatically
with open("greeting.txt", "r") as f:
    content = f.read()
# File is closed here, even if an error occurred
```

**Rule:** Always use `with` when working with files. It guarantees the file is closed properly, even if your code crashes.

---

## pathlib — Modern File Path Handling

The `pathlib` module provides a cleaner way to work with file paths:

```python
from pathlib import Path

# Create a Path object
file_path = Path("greeting.txt")

# Check if it exists
print(file_path.exists())

# Read the entire file
content = file_path.read_text()
print(content)

# Get file information
print(f"Name: {file_path.name}")
print(f"Suffix: {file_path.suffix}")
print(f"Parent: {file_path.parent}")
```

**Output:**

```
True
Hello, World!
Welcome to Python.
Let's learn file handling.

Name: greeting.txt
Suffix: .txt
Parent: .
```

**Why use pathlib:** It works the same on Windows, Mac, and Linux. No more worrying about `/` vs `\` in paths.

### Building Paths

```python
from pathlib import Path

# Join path parts — works on any OS
log_dir = Path("var") / "log" / "myapp"
log_file = log_dir / "app.log"

print(log_file)
```

**Output (Linux/Mac):**

```
var/log/myapp/app.log
```

**Output (Windows):**

```
var\log\myapp\app.log
```

**Why:** The `/` operator on Path objects joins path parts using the correct separator for your operating system.

### Creating Directories

```python
from pathlib import Path

output_dir = Path("output") / "reports"
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Created: {output_dir}")
```

**Output:**

```
Created: output/reports
```

**What the arguments do:**

- `parents=True` — create parent directories if they do not exist
- `exist_ok=True` — do not raise an error if the directory already exists

### Listing Files in a Directory

```python
from pathlib import Path

# List all .txt files in the current directory
for txt_file in Path(".").glob("*.txt"):
    print(txt_file)
```

**Output (depends on your files):**

```
greeting.txt
log.txt
data.txt
```

**Recursive search (including subdirectories):**

```python
from pathlib import Path

for py_file in Path(".").rglob("*.py"):
    print(py_file)
```

---

## Working with CSV Files

CSV (Comma-Separated Values) is a common format for tabular data:

```python
import csv

# Write a CSV file
with open("students.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Score", "Grade"])
    writer.writerow(["Alice", 95, "A"])
    writer.writerow(["Bob", 82, "B"])
    writer.writerow(["Charlie", 67, "D"])

print("CSV file created!")
```

**The file `students.csv` contains:**

```
Name,Score,Grade
Alice,95,A
Bob,82,B
Charlie,67,D
```

**Reading the CSV file:**

```python
import csv

with open("students.csv", "r") as f:
    reader = csv.reader(f)
    header = next(reader)    # Read the first row (header)
    print(f"Columns: {header}")
    
    for row in reader:
        name, score, grade = row
        print(f"  {name}: {score} ({grade})")
```

**Output:**

```
Columns: ['Name', 'Score', 'Grade']
  Alice: 95 (A)
  Bob: 82 (B)
  Charlie: 67 (D)
```

**How this works:**

1. `csv.reader(f)` creates a reader that parses each line into a list
2. `next(reader)` gets the first row (the header)
3. The `for` loop gets each remaining row as a list like `["Alice", "95", "A"]`
4. `name, score, grade = row` unpacks the list into variables

### CSV with DictReader — Easier to Work With

```python
import csv

with open("students.csv", "r") as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        print(f"  {row['Name']}: {row['Score']} ({row['Grade']})")
```

**Output:**

```
  Alice: 95 (A)
  Bob: 82 (B)
  Charlie: 67 (D)
```

**Why DictReader is better:** Each row is a dictionary with column names as keys. You access values by name (`row['Name']`) instead of position (`row[0]`). This is more readable and less error-prone.

---

## Working with JSON Files

JSON (JavaScript Object Notation) is the standard format for configuration files and API data:

```python
import json

# Python dictionary
server_config = {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": False,
    "allowed_origins": ["localhost", "example.com"],
    "database": {
        "host": "db.example.com",
        "port": 5432,
        "name": "myapp"
    }
}

# Write to JSON file
with open("config.json", "w") as f:
    json.dump(server_config, f, indent=2)

print("Config saved!")
```

**The file `config.json` contains:**

```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "debug": false,
  "allowed_origins": [
    "localhost",
    "example.com"
  ],
  "database": {
    "host": "db.example.com",
    "port": 5432,
    "name": "myapp"
  }
}
```

**Reading the JSON file:**

```python
import json

with open("config.json", "r") as f:
    config = json.load(f)

print(f"Host: {config['host']}")
print(f"Port: {config['port']}")
print(f"DB Host: {config['database']['host']}")
print(f"Origins: {config['allowed_origins']}")
```

**Output:**

```
Host: 0.0.0.0
Port: 8080
DB Host: db.example.com
Origins: ['localhost', 'example.com']
```

**Key functions:**

- `json.dump(data, file)` — write Python data to a JSON file
- `json.load(file)` — read a JSON file into Python data
- `json.dumps(data)` — convert Python data to a JSON string (no file)
- `json.loads(string)` — convert a JSON string to Python data (no file)

### Converting Between JSON Strings and Python

```python
import json

# Python dict → JSON string
data = {"name": "Alice", "age": 30}
json_string = json.dumps(data)
print(json_string)
print(type(json_string))

# JSON string → Python dict
parsed = json.loads(json_string)
print(parsed["name"])
print(type(parsed))
```

**Output:**

```
{"name": "Alice", "age": 30}
<class 'str'>
Alice
<class 'dict'>
```

---

## Working with YAML Files

YAML is popular for configuration files (Docker Compose, Kubernetes, Ansible). It requires the `pyyaml` package:

```bash
pip install pyyaml
```

```python
import yaml

# Python dictionary
config = {
    "app": {
        "name": "myapp",
        "version": "1.0.0",
        "ports": [8080, 8443],
    },
    "database": {
        "host": "localhost",
        "port": 5432,
    }
}

# Write to YAML file
with open("config.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False)

# Read from YAML file
with open("config.yaml", "r") as f:
    loaded = yaml.safe_load(f)

print(loaded["app"]["name"])
print(loaded["app"]["ports"])
```

**Output:**

```
myapp
[8080, 8443]
```

**The file `config.yaml` contains:**

```yaml
app:
  name: myapp
  ports:
  - 8080
  - 8443
  version: 1.0.0
database:
  host: localhost
  port: 5432
```

> **Security note:** Always use `yaml.safe_load()` instead of `yaml.load()`. The unsafe version can execute arbitrary code from the YAML file.

---

## Processing Log Files — A Practical Example

Log processing is one of the most common file tasks in DevOps. Here is a realistic example:

### Sample Log File

First, create a sample log file:

```python
log_content = """2024-01-15 08:23:01 INFO Server started on port 8080
2024-01-15 08:23:15 INFO User alice logged in
2024-01-15 08:24:02 WARNING High memory usage: 85%
2024-01-15 08:25:30 ERROR Database connection failed: timeout
2024-01-15 08:25:31 INFO Retrying database connection
2024-01-15 08:25:33 INFO Database connected
2024-01-15 08:30:00 WARNING Disk usage above 90%
2024-01-15 08:35:12 ERROR API endpoint /users returned 500
2024-01-15 08:35:13 INFO Auto-restart triggered for API service
2024-01-15 08:40:00 INFO Health check passed
"""

with open("app.log", "w") as f:
    f.write(log_content)
```

### Counting Log Levels

```python
def count_log_levels(log_file):
    """Count occurrences of each log level."""
    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}
    
    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            for level in counts:
                if f" {level} " in line:
                    counts[level] += 1
                    break
    
    return counts

counts = count_log_levels("app.log")
for level, count in counts.items():
    print(f"  {level}: {count}")
```

**Output:**

```
  INFO: 6
  WARNING: 2
  ERROR: 2
```

### Extracting Error Lines

```python
def get_errors(log_file):
    """Extract all ERROR lines from a log file."""
    errors = []
    
    with open(log_file, "r") as f:
        for line in f:
            if " ERROR " in line:
                errors.append(line.strip())
    
    return errors

errors = get_errors("app.log")
print(f"Found {len(errors)} errors:")
for error in errors:
    print(f"  {error}")
```

**Output:**

```
Found 2 errors:
  2024-01-15 08:25:30 ERROR Database connection failed: timeout
  2024-01-15 08:35:12 ERROR API endpoint /users returned 500
```

### Parsing Log Lines into Structured Data

```python
def parse_log_line(line):
    """Parse a log line into its components."""
    parts = line.strip().split(" ", 3)
    if len(parts) < 4:
        return None
    
    return {
        "date": parts[0],
        "time": parts[1],
        "level": parts[2],
        "message": parts[3],
    }

with open("app.log", "r") as f:
    for line in f:
        if not line.strip():
            continue
        parsed = parse_log_line(line)
        if parsed and parsed["level"] == "ERROR":
            print(f"  [{parsed['time']}] {parsed['message']}")
```

**Output:**

```
  [08:25:30] Database connection failed: timeout
  [08:35:12] API endpoint /users returned 500
```

**How `split(" ", 3)` works:** It splits the string by spaces, but only makes 3 splits (producing 4 parts). This keeps the message intact even if it contains spaces.

---

## Exercises

**Exercise 1:** Write a program that creates a file called `numbers.txt` with numbers 1 to 10 (one per line), then reads it back and prints the sum of all numbers.

**Exercise 2:** Write a function `word_count(filename)` that reads a text file and returns a dictionary of word frequencies. Test it with a file containing a few sentences.

**Exercise 3:** Create a JSON file with a list of 5 books (title, author, year). Write a program that reads the file and prints books published after 2000.

**Exercise 4:** Write a log analyzer that reads `app.log` and prints a summary: total lines, count per log level, and the timestamp of the first and last entry.

---

## Common Mistakes

### 1. Forgetting to Close Files

```python
f = open("data.txt", "w")
f.write("hello")
# Forgot f.close() — data might not be saved!
```

**Fix:** Always use `with open(...) as f:` — it closes the file automatically.

### 2. Reading a File That Does Not Exist

```python
with open("missing.txt", "r") as f:
    content = f.read()
```

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'missing.txt'`

**Fix:** Check with `os.path.exists()` or `Path.exists()` first, or use `try/except`.

### 3. Writing When You Meant to Append

```python
# This ERASES the file each time!
with open("log.txt", "w") as f:
    f.write("New entry\n")
```

**Fix:** Use `"a"` mode to append: `open("log.txt", "a")`

### 4. Forgetting newline Characters

```python
with open("data.txt", "w") as f:
    f.write("line 1")
    f.write("line 2")
    f.write("line 3")
```

**The file contains:** `line 1line 2line 3` (all on one line)

**Fix:** Add `\n` at the end of each write: `f.write("line 1\n")`

### 5. Hardcoding File Paths

```python
# Bad — breaks on different machines
with open("/home/alice/data/config.json") as f:
    config = json.load(f)

# Good — use relative paths or pathlib
from pathlib import Path
config_path = Path("data") / "config.json"
```

---

## Summary

| Operation | Code | Notes |
|-----------|------|-------|
| Write file | `open("f.txt", "w")` | Creates or overwrites |
| Append file | `open("f.txt", "a")` | Adds to end |
| Read file | `open("f.txt", "r")` | Read entire file |
| Read lines | `for line in f:` | Memory efficient |
| Check exists | `Path("f.txt").exists()` | Returns True/False |
| Create dirs | `Path("d").mkdir(parents=True)` | Creates parent dirs |
| List files | `Path(".").glob("*.txt")` | Pattern matching |
| Read CSV | `csv.reader(f)` | Returns lists |
| Read CSV dict | `csv.DictReader(f)` | Returns dicts |
| Write JSON | `json.dump(data, f)` | Python → JSON file |
| Read JSON | `json.load(f)` | JSON file → Python |
| Read YAML | `yaml.safe_load(f)` | YAML file → Python |

---

[Previous: Module 05 — Functions](05-functions-and-modular-automation.md) | [Next: Module 07 — CLI Tool Development](07-python-cli-tool-development.md)
