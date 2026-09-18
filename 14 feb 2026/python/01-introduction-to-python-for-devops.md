# Module 1 — Introduction to Python for DevOps

## What is Python?

Python is a programming language created by Guido van Rossum in 1991. It was designed to be easy to read and write — almost like writing instructions in plain English.

Here is your first Python program:

```python
print("Hello, World!")
```

**Output:**

```
Hello, World!
```

That is it. One line. No boilerplate, no compilation step, no complex setup. You write it, you run it, it works.

Compare this to other languages:

**Java (same thing):**

```java
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
```

**Go (same thing):**

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```

Python removes the ceremony and lets you focus on what you want to do.

---

## Why Python for DevOps?

As a DevOps engineer, your job is to automate things — deployments, monitoring, infrastructure management, CI/CD pipelines. You need a language that:

1. **Readability and Simplicity** — Python reads like English. You are not a full-time developer. You need to pick up the language quickly and start automating. Python's clean syntax means less time deciphering code and more time solving problems.

2. **Large Ecosystem of Third-Party Libraries (PyPI)** — The Python Package Index (PyPI) hosts over 400,000 packages. AWS (`boto3`), Docker (`docker-py`), Kubernetes (`kubernetes`), GitHub (`PyGithub`), Jenkins, Ansible — all have Python libraries ready to use. You do not need to build from scratch.

3. **Cross-Platform Compatibility** — Python runs on Linux, macOS, and Windows. Your automation scripts work on your laptop, on Ubuntu servers, in Docker containers, on CI/CD runners, and in AWS Lambda functions — without modification.

4. **Automation-Friendly** — Python excels at the tasks DevOps engineers do daily: parsing log files, calling REST APIs, managing infrastructure, processing JSON/YAML, and orchestrating deployments. It handles these better than Bash and with less boilerplate than Go or Java.

5. **Extensive Standard Library** — Python comes with built-in modules for common tasks — no installation needed:

    ```python
    import os           # File system operations, environment variables
    import sys          # System-specific parameters
    import subprocess   # Run shell commands
    import json         # Parse and create JSON
    import csv          # Read and write CSV files
    import pathlib      # Modern file path handling
    import logging      # Structured logging
    import argparse     # CLI argument parsing
    ```

    These are available in every Python installation. You can start automating immediately.

6. **Python as Glue Code** — Python integrates easily with other tools, languages, and APIs. You can call shell commands with `subprocess`, parse output from any CLI tool, call REST APIs, and connect to databases — all in one script. This makes Python ideal for tying together different parts of your infrastructure.

7. **Community and Job Market** — Python is consistently one of the top 3 most popular programming languages. Most DevOps job postings list Python as a required or preferred skill. The large community means tutorials, Stack Overflow answers, and pre-built solutions are always available.

### Python vs Bash vs Go — When to Use What

You do not need to choose only one. Each tool has its place:

| Criteria | Python | Bash | Go |
|----------|--------|------|----|
| Quick file operations | Good | Best | Verbose |
| API integrations | Best | Painful | Good |
| Complex logic | Best | Fragile | Good |
| System commands | Good | Best | Good |
| Distributing as a binary | Needs runtime | Needs shell | Best |
| Learning curve | Low | Low | Moderate |

**Simple rule of thumb:**

- **Use Bash** when you are chaining 2-5 shell commands and the logic is straightforward.
- **Use Python** when you need conditionals, loops, API calls, error handling, or the script exceeds ~50 lines.
- **Use Go** when you need to distribute a single compiled binary.

---

## What Python Can Do for DevOps — A Preview

You do not need to understand any of this code yet. This is just a preview of where this course will take you. By the end, you will be able to write scripts like these:

| Problem | What Python Does |
|---------|-----------------|
| Check if 200 servers are online | Loop through a list and ping each one |
| Parse a 10GB log file for errors | Read the file line by line and filter |
| Create a GitHub pull request | Call the GitHub API |
| Launch an AWS EC2 instance | Use the `boto3` library |
| Deploy to Kubernetes | Use the `kubernetes` library |
| Send a Slack alert when something breaks | Send an HTTP request to a webhook |
| Clean up old Docker images | Use the `docker` library |
| Trigger a Jenkins build | Call the Jenkins API |

All of these are covered in later modules. For now, let us start with the basics.

---

## The Python Ecosystem for DevOps

Python has a massive collection of libraries (pre-written code you can use). Here are the ones relevant to DevOps:

```
┌──────────────────────────────────────────────────────────────┐
│                  Python DevOps Ecosystem                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Cloud SDKs          Container/Orchestration    CI/CD        │
│  ┌──────────┐        ┌──────────────┐          ┌─────────┐  │
│  │ boto3    │        │ docker-py    │          │ jenkins  │  │
│  │ azure    │        │ kubernetes   │          │ python   │  │
│  │ gcloud   │        │              │          │ gitlab   │  │
│  └──────────┘        └──────────────┘          └─────────┘  │
│                                                              │
│  IaC                  Monitoring         Config Mgmt         │
│  ┌──────────┐        ┌──────────┐       ┌──────────┐        │
│  │ python-  │        │ psutil   │       │ ansible  │        │
│  │ terraform│        │ prometheus│       │ fabric   │        │
│  │ pulumi   │        │ datadog  │       │          │        │
│  └──────────┘        └──────────┘       └──────────┘        │
│                                                              │
│  Utilities                                                   │
│  ┌──────────────────────────────────────────────┐            │
│  │ requests · paramiko · pyyaml · jinja2 · click│            │
│  └──────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

You will learn to use many of these throughout the course. Do not worry about memorizing them now.

---

## How to Run Python Code

There are two ways to run Python:

### 1. Interactive Mode (Python Shell)

Open your terminal and type `python3`:

```bash
$ python3
Python 3.11.6 (main, Oct  2 2023, 13:45:54)
>>> print("Hello!")
Hello!
>>> 2 + 3
5
>>> exit()
```

The `>>>` prompt means Python is waiting for your input. This is great for quick experiments.

### 2. Script Mode (Writing .py Files)

Create a file called `hello.py`:

```python
print("Hello, World!")
print("My name is Python.")
print("I am going to help you automate things.")
```

Run it:

```bash
$ python3 hello.py
Hello, World!
My name is Python.
I am going to help you automate things.
```

**For this course, use script mode.** Create `.py` files and run them. It is closer to how you will write real automation.

### Key Difference: REPL vs .py Files

```
REPL (Interactive):              .py File (Script):

>>> 2 + 3                       # save as math.py
5          <-- auto-printed      result = 2 + 3
                                 print(result)    <-- must use print()
>>> name = "Alice"
>>> name                         # Without print(), nothing shows
'Alice'    <-- auto-printed
```

| Behavior | REPL | .py File |
|----------|------|----------|
| Expressions auto-display | Yes | No |
| Need `print()` to see output | No | Yes |
| Code saved after closing | No | Yes |
| Good for quick tests | Yes | No |
| Good for automation | No | Yes |

### How Python Executes a .py File

Python reads your file **top to bottom**, executing each line in order:

```
python3 demo.py

Line 1: name = "Alice"        → stores "Alice" in variable name
Line 2: age = 30               → stores 30 in variable age
Line 3: print(name)            → prints "Alice"
Line 4: print(age + 5)         → computes 35, prints it

Done — program exits
```

There is no `main()` function required (unlike Java or Go). Python starts at line 1 and works its way down.

> **Note:** You will see `if __name__ == "__main__":` in many Python scripts. This is covered in Module 7 — it controls whether code runs when the file is executed directly vs imported as a module.

---

## Your First Exercises

Try these on your own. Create a file for each one and run it.

**Exercise 1:** Create `greet.py`

```python
print("Welcome to Python for DevOps!")
print("Let's start learning.")
```

```bash
python3 greet.py
```

**Exercise 2:** Create `math.py`

```python
print(10 + 5)
print(10 - 3)
print(4 * 7)
print(20 / 4)
```

```bash
python3 math.py
```

**Expected output:**

```
15
7
28
5.0
```

> **Note:** Division (`/`) always returns a decimal number in Python. `20 / 4` gives `5.0`, not `5`. This is by design.

**Exercise 3:** Create `about_me.py`

```python
print("Name: Alex")
print("Role: DevOps Engineer")
print("Favorite tool: Kubernetes")
print("Years of experience: 3")
```

---

## What This Course Covers

```
Part 1: Python Fundamentals (Modules 1-8)
  |
  +-- Variables, data types, control flow, functions
  +-- File handling, CLI tools, APIs
  |
Part 2: DevOps Automation (Modules 9-17)
  |
  +-- Git, Terraform, Ansible, Docker, Kubernetes
  +-- AWS (boto3), CI/CD, Monitoring, Parallel execution
  |
Part 3: Production Skills (Modules 18-20)
  |
  +-- Building real tools, production-grade code, industry projects
  |
Bonus (Modules 21-27)
  |
  +-- Patterns, interview prep, generators, decorators
  +-- Exception handling, regex
```

By the end, you will be able to:
- Write Python scripts to automate DevOps tasks
- Build CLI tools with argument parsing and error handling
- Interact with cloud APIs (AWS, GitHub, Docker, Kubernetes)
- Process log files, configuration files, and JSON/YAML data
- Write production-grade code with logging, testing, and secrets management

---

## What is Next

In the next module, you will set up your Python environment properly — install Python, manage multiple versions with pyenv, create isolated environments, and manage dependencies.

---

[Next: Module 02 — Setting up Python Environment](02-setting-up-python-environment.md)
