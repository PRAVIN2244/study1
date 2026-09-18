# Module 7 — Python CLI Tool Development

A CLI (Command-Line Interface) tool is a program you run from the terminal with arguments and options. You already use CLI tools every day:

```bash
ls -la /home                    # ls is the tool, -la is an option, /home is an argument
git commit -m "fix bug"         # git is the tool, commit is a subcommand
docker run -p 8080:80 nginx     # docker is the tool, run is a subcommand
```

In this module, you will learn to build your own CLI tools in Python.

---

## sys.argv — The Simplest Way to Read Arguments

`sys.argv` is a list that contains the command-line arguments passed to your script:

```python
# save as: hello.py
import sys

print(f"All arguments: {sys.argv}")
print(f"Script name: {sys.argv[0]}")
print(f"Number of arguments: {len(sys.argv)}")
```

**Run it:**

```bash
python3 hello.py Alice 25 London
```

**Output:**

```
All arguments: ['hello.py', 'Alice', '25', 'London']
Script name: hello.py
Number of arguments: 4
```

**How this works:**

1. `sys.argv[0]` is always the script name (`hello.py`)
2. `sys.argv[1]` is the first argument (`Alice`)
3. `sys.argv[2]` is the second argument (`25`)
4. All arguments are **strings** — even `25` is the string `"25"`, not the number `25`

### Using Arguments in Your Script

```python
# save as: greet.py
import sys

if len(sys.argv) < 2:
    print("Usage: python3 greet.py <name>")
    sys.exit(1)

name = sys.argv[1]
print(f"Hello, {name}!")
```

**Run it without arguments:**

```bash
python3 greet.py
```

**Output:**

```
Usage: python3 greet.py <name>
```

**Run it with an argument:**

```bash
python3 greet.py Alice
```

**Output:**

```
Hello, Alice!
```

**What `sys.exit(1)` does:** It stops the program immediately and returns exit code `1` to the shell. Exit code `0` means success, any other number means failure. This is how CLI tools communicate success or failure to other programs and scripts.

### Why sys.argv Has Limitations

```python
# save as: calc.py
import sys

if len(sys.argv) != 4:
    print("Usage: python3 calc.py <num1> <operator> <num2>")
    sys.exit(1)

num1 = float(sys.argv[1])
operator = sys.argv[2]
num2 = float(sys.argv[3])

if operator == "+":
    print(num1 + num2)
elif operator == "-":
    print(num1 - num2)
else:
    print(f"Unknown operator: {operator}")
    sys.exit(1)
```

This works, but as your tool grows, you need to handle:
- Help messages (`--help`)
- Optional flags (`--verbose`, `--dry-run`)
- Type validation (is this really a number?)
- Default values

Doing all this with `sys.argv` becomes messy. That is where `argparse` comes in.

---

## argparse — Professional CLI Tools

`argparse` is Python's built-in library for building CLI tools. It handles argument parsing, help messages, type conversion, and error messages automatically.

### Basic Example

```python
# save as: greet_v2.py
import argparse

parser = argparse.ArgumentParser(description="A friendly greeting tool")
parser.add_argument("name", help="Name of the person to greet")

args = parser.parse_args()
print(f"Hello, {args.name}!")
```

**Run it:**

```bash
python3 greet_v2.py Alice
```

**Output:**

```
Hello, Alice!
```

**Run it with --help:**

```bash
python3 greet_v2.py --help
```

**Output:**

```
usage: greet_v2.py [-h] name

A friendly greeting tool

positional arguments:
  name        Name of the person to greet

options:
  -h, --help  show this help message and exit
```

**What happened:** `argparse` automatically generated a help message from the description and argument definitions. You get `--help` for free.

**Run it without arguments:**

```bash
python3 greet_v2.py
```

**Output:**

```
usage: greet_v2.py [-h] name
greet_v2.py: error: the following arguments are required: name
```

**Why:** `argparse` validates that required arguments are provided and shows a clear error message. You did not write any validation code — `argparse` handles it.

### Optional Arguments (Flags)

Optional arguments start with `--` (or `-` for short versions):

```python
# save as: greet_v3.py
import argparse

parser = argparse.ArgumentParser(description="A greeting tool with options")
parser.add_argument("name", help="Name of the person to greet")
parser.add_argument("--greeting", "-g", default="Hello", help="Greeting to use (default: Hello)")
parser.add_argument("--shout", action="store_true", help="Print in uppercase")

args = parser.parse_args()

message = f"{args.greeting}, {args.name}!"

if args.shout:
    message = message.upper()

print(message)
```

**Run it with defaults:**

```bash
python3 greet_v3.py Alice
```

**Output:**

```
Hello, Alice!
```

**Run it with options:**

```bash
python3 greet_v3.py Alice --greeting "Good morning" --shout
```

**Output:**

```
GOOD MORNING, ALICE!
```

**Run it with short flags:**

```bash
python3 greet_v3.py Bob -g Hey
```

**Output:**

```
Hey, Bob!
```

**How this works:**

- `"name"` (no dashes) — positional argument, required
- `"--greeting"` — optional argument with a default value
- `"-g"` — short version of `--greeting`
- `action="store_true"` — makes `--shout` a boolean flag (True if present, False if not)
- `default="Hello"` — value used when `--greeting` is not provided

### Type Conversion

By default, all arguments are strings. Use `type=` to convert automatically:

```python
# save as: repeat.py
import argparse

parser = argparse.ArgumentParser(description="Repeat a message")
parser.add_argument("message", help="Message to repeat")
parser.add_argument("--count", "-n", type=int, default=1, help="Number of times to repeat")

args = parser.parse_args()

for i in range(args.count):
    print(f"{i + 1}. {args.message}")
```

**Run it:**

```bash
python3 repeat.py "Hello World" -n 3
```

**Output:**

```
1. Hello World
2. Hello World
3. Hello World
```

**What happens with invalid input:**

```bash
python3 repeat.py "Hello" -n abc
```

**Output:**

```
usage: repeat.py [-h] [--count COUNT] message
repeat.py: error: argument --count/-n: invalid int value: 'abc'
```

**Why:** `argparse` tried to convert `"abc"` to `int` and failed. It shows a clear error message without you writing any validation code.

### Choices — Restricting Valid Values

```python
# save as: color.py
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--color", choices=["red", "green", "blue"], required=True)

args = parser.parse_args()
print(f"You chose: {args.color}")
```

**Run with valid choice:**

```bash
python3 color.py --color green
```

**Output:**

```
You chose: green
```

**Run with invalid choice:**

```bash
python3 color.py --color yellow
```

**Output:**

```
usage: color.py [-h] --color {red,green,blue}
color.py: error: argument --color: invalid choice: 'yellow' (choose from 'red', 'green', 'blue')
```

---

## Subcommands — Building Complex Tools

Real CLI tools like `git` and `docker` have subcommands (`git commit`, `docker run`). You can build the same pattern:

```python
# save as: todo.py
import argparse
import json
from pathlib import Path

TODO_FILE = Path("todos.json")

def load_todos():
    if TODO_FILE.exists():
        return json.loads(TODO_FILE.read_text())
    return []

def save_todos(todos):
    TODO_FILE.write_text(json.dumps(todos, indent=2))

def cmd_add(args):
    todos = load_todos()
    todos.append({"task": args.task, "done": False})
    save_todos(todos)
    print(f"Added: {args.task}")

def cmd_list(args):
    todos = load_todos()
    if not todos:
        print("No todos yet!")
        return
    for i, todo in enumerate(todos, 1):
        status = "x" if todo["done"] else " "
        print(f"  [{status}] {i}. {todo['task']}")

def cmd_done(args):
    todos = load_todos()
    if args.number < 1 or args.number > len(todos):
        print(f"Invalid todo number: {args.number}")
        return
    todos[args.number - 1]["done"] = True
    save_todos(todos)
    print(f"Marked #{args.number} as done!")

# Main parser
parser = argparse.ArgumentParser(description="Simple todo manager")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

# 'add' subcommand
add_parser = subparsers.add_parser("add", help="Add a new todo")
add_parser.add_argument("task", help="Task description")

# 'list' subcommand
subparsers.add_parser("list", help="List all todos")

# 'done' subcommand
done_parser = subparsers.add_parser("done", help="Mark a todo as done")
done_parser.add_argument("number", type=int, help="Todo number to mark as done")

args = parser.parse_args()

if args.command == "add":
    cmd_add(args)
elif args.command == "list":
    cmd_list(args)
elif args.command == "done":
    cmd_done(args)
else:
    parser.print_help()
```

**Usage:**

```bash
python3 todo.py add "Learn Python"
python3 todo.py add "Build CLI tool"
python3 todo.py list
python3 todo.py done 1
python3 todo.py list
```

**Output:**

```
Added: Learn Python
Added: Build CLI tool
  [ ] 1. Learn Python
  [ ] 2. Build CLI tool
Marked #1 as done!
  [x] 1. Learn Python
  [ ] 2. Build CLI tool
```

**How subcommands work:**

1. `parser.add_subparsers()` creates a container for subcommands
2. `subparsers.add_parser("add")` creates the `add` subcommand with its own arguments
3. `args.command` tells you which subcommand was used
4. Each subcommand has its own handler function

---

## Exit Codes — Communicating Success or Failure

Exit codes tell the shell (and other programs) whether your tool succeeded:

```python
# save as: check_file.py
import sys
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Check if a file exists")
parser.add_argument("filename", help="File to check")

args = parser.parse_args()

if Path(args.filename).exists():
    print(f"OK: {args.filename} exists")
    sys.exit(0)    # Success
else:
    print(f"ERROR: {args.filename} not found")
    sys.exit(1)    # Failure
```

**Run it:**

```bash
python3 check_file.py /etc/hostname
echo "Exit code: $?"
```

**Output:**

```
OK: /etc/hostname exists
Exit code: 0
```

```bash
python3 check_file.py /nonexistent
echo "Exit code: $?"
```

**Output:**

```
ERROR: /nonexistent not found
Exit code: 1
```

**Why exit codes matter:** Shell scripts use exit codes to make decisions:

```bash
if python3 check_file.py config.json; then
    echo "Config found, starting app..."
else
    echo "Config missing, cannot start!"
fi
```

**Convention:**

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Misuse of command (wrong arguments) |

---

## Colored Output — Making Tools User-Friendly

Terminal colors make output easier to scan:

```python
# save as: colors_demo.py

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"    # Reset to default color

print(f"{GREEN}SUCCESS:{RESET} Deployment complete")
print(f"{YELLOW}WARNING:{RESET} Disk usage at 85%")
print(f"{RED}ERROR:{RESET} Connection refused")
print(f"{BLUE}INFO:{RESET} Server started on port 8080")
```

**Output:** (with colors in the terminal)

```
SUCCESS: Deployment complete
WARNING: Disk usage at 85%
ERROR: Connection refused
INFO: Server started on port 8080
```

**How ANSI codes work:** `\033[91m` tells the terminal to switch to red text. `\033[0m` resets back to the default color. Everything between them is colored.

**Helper function for cleaner code:**

```python
def color(text, code):
    return f"\033[{code}m{text}\033[0m"

def success(msg): print(color(f"SUCCESS: {msg}", 92))
def warning(msg): print(color(f"WARNING: {msg}", 93))
def error(msg):   print(color(f"ERROR: {msg}", 91))
def info(msg):    print(color(f"INFO: {msg}", 94))

success("All tests passed")
warning("Deprecated function used")
error("File not found")
info("Processing 42 items")
```

---

## Practical Example: File Search Tool

A complete CLI tool that searches for text in files:

```python
# save as: search.py
import argparse
import sys
from pathlib import Path

def search_file(filepath, pattern, ignore_case=False):
    """Search for a pattern in a file. Returns matching lines."""
    matches = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                check_line = line.lower() if ignore_case else line
                check_pattern = pattern.lower() if ignore_case else pattern
                if check_pattern in check_line:
                    matches.append((line_num, line.rstrip()))
    except PermissionError:
        pass
    return matches

def main():
    parser = argparse.ArgumentParser(description="Search for text in files")
    parser.add_argument("pattern", help="Text to search for")
    parser.add_argument("path", help="File or directory to search")
    parser.add_argument("-i", "--ignore-case", action="store_true",
                        help="Case-insensitive search")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Search directories recursively")
    parser.add_argument("--ext", default="*",
                        help="File extension to filter (e.g., .py, .txt)")
    
    args = parser.parse_args()
    path = Path(args.path)
    total_matches = 0
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        pattern = f"**/*{args.ext}" if args.recursive else f"*{args.ext}"
        files = sorted(path.glob(pattern))
    else:
        print(f"Error: {args.path} not found")
        sys.exit(1)
    
    for filepath in files:
        if not filepath.is_file():
            continue
        matches = search_file(filepath, args.pattern, args.ignore_case)
        for line_num, line in matches:
            print(f"  {filepath}:{line_num}: {line}")
            total_matches += 1
    
    print(f"\n{total_matches} match(es) found.")
    sys.exit(0 if total_matches > 0 else 1)

if __name__ == "__main__":
    main()
```

**Usage:**

```bash
python3 search.py "ERROR" /var/log/app.log
python3 search.py "import" . -r --ext .py
python3 search.py "todo" . -r -i --ext .py
```

**What `if __name__ == "__main__":` means:** This line ensures `main()` only runs when the script is executed directly (`python3 search.py`), not when it is imported as a module by another script. It is a Python convention for scripts that can also be used as libraries.

---

## Exercises

**Exercise 1:** Build a CLI tool that takes a filename and prints the number of lines, words, and characters (like the `wc` command).

**Exercise 2:** Build a CLI tool with subcommands `encode` and `decode` that converts text to/from base64. Use Python's `base64` module.

**Exercise 3:** Build a CLI tool that takes a directory path and `--ext` flag, and lists all files with that extension, showing their sizes in human-readable format (KB, MB).

---

## Common Mistakes

### 1. Not Handling Missing Arguments

```python
import sys
name = sys.argv[1]    # Crashes if no argument provided!
```

**Error:** `IndexError: list index out of range`

**Fix:** Check `len(sys.argv)` first, or use `argparse` which handles this automatically.

### 2. Forgetting That sys.argv Values Are Strings

```python
import sys
count = sys.argv[1]
for i in range(count):    # TypeError!
    print(i)
```

**Error:** `TypeError: 'str' object cannot be interpreted as an integer`

**Fix:** `count = int(sys.argv[1])`

### 3. Not Using Exit Codes

```python
# Bad — always exits with 0 even on failure
if error:
    print("Something went wrong")

# Good — exit with non-zero on failure
if error:
    print("Something went wrong")
    sys.exit(1)
```

### 4. Hardcoding Values That Should Be Arguments

```python
# Bad — hardcoded filename
with open("data.csv") as f:
    process(f)

# Good — accept as argument
parser.add_argument("filename")
```

---

## Summary

| Approach | When to Use | Complexity |
|----------|------------|------------|
| `sys.argv` | Quick scripts, 1-2 arguments | Low |
| `argparse` | Real tools with options and help | Medium |
| Subcommands | Complex tools (like git, docker) | Higher |

| Concept | What It Does |
|---------|-------------|
| Positional args | Required, order matters |
| Optional args (`--flag`) | Optional, named |
| `action="store_true"` | Boolean flag |
| `type=int` | Auto-convert to int |
| `choices=[...]` | Restrict valid values |
| `default=...` | Value when not provided |
| `sys.exit(0)` | Exit with success |
| `sys.exit(1)` | Exit with failure |

---

[Previous: Module 06 — File Handling](06-file-handling-and-log-processing.md) | [Next: Module 08 — Working with APIs](08-working-with-apis.md)
