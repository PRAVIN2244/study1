# Module 2 — Setting up Python Environment

Before writing Python code, you need Python installed and a proper workspace set up. This module walks you through every step.

---

## Step 1: Check if Python is Already Installed

Open your terminal and type:

```bash
python3 --version
```

**Expected output (if installed):**

```
Python 3.11.6
```

The version number may differ (3.9, 3.10, 3.12, etc.). Any version 3.8 or higher works for this course.

**If you see an error like this:**

```
python3: command not found
```

It means Python is not installed. Follow the installation steps below for your operating system.

You can also check where Python is installed:

```bash
which python3
```

**Output:**

```
/usr/bin/python3
```

This tells you the exact location of the Python program on your system.

---

## Step 2: Install Python (If Not Already Installed)

### On Ubuntu / Debian Linux

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
```

**What each part does:**

- `sudo apt update` — Updates the list of available packages from the internet.
- `sudo apt install -y` — Installs packages. The `-y` flag means "yes, install without asking for confirmation."
- `python3` — The Python interpreter itself.
- `python3-pip` — The package manager for installing Python libraries.
- `python3-venv` — The tool for creating virtual environments (explained later in this module).

### On CentOS / RHEL / Amazon Linux

```bash
sudo yum install -y python3 python3-pip
```

Or on newer versions:

```bash
sudo dnf install -y python3 python3-pip
```

### On macOS

```bash
brew install python@3.11
```

This requires [Homebrew](https://brew.sh). If you do not have Homebrew, install it first with the command on their website.

### From python.org (Any OS)

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the installer for your operating system
3. Run the installer

**Windows users:** Check "Add Python to PATH" during installation. Without this, `python` will not work from the command line.

### Verify the Installation

After installing, run:

```bash
python3 --version
pip3 --version
```

**Expected output:**

```
Python 3.11.6
pip 23.3.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
```

If both commands work, you are ready.

### Three Ways to Install Python — Summary

```
Method 1: python.org          Method 2: Package Manager     Method 3: pyenv (recommended)
  |                             |                              |
  v                             v                              v
Download installer            apt / yum / brew               curl https://pyenv.run | bash
  |                             |                              |
  v                             v                              v
One version only              One version only               Multiple versions
  |                             |                              |
  v                             v                              v
Manual updates                System updates                 pyenv install 3.12.2
                                                             pyenv install 3.10.13
                                                             pyenv global 3.12.2
```

**Recommendation:** Use pyenv (covered below) for flexibility. Use package managers for quick setup on servers.

---

## Step 3: Understand pip — The Package Manager

`pip` is Python's package manager. It downloads and installs libraries (pre-written code) from the internet so you can use them in your scripts.

### Installing a Package

```bash
pip3 install requests
```

**What this does:** Downloads the `requests` library from [PyPI](https://pypi.org) (Python Package Index) and installs it on your system.

**Output:**

```
Collecting requests
  Downloading requests-2.31.0-py3-none-any.whl (62 kB)
Installing collected packages: requests
Successfully installed requests-2.31.0
```

### Checking What is Installed

```bash
pip3 list
```

**Output:**

```
Package    Version
---------- -------
pip        23.3.1
requests   2.31.0
setuptools 68.2.2
```

This shows all installed packages and their versions.

### Uninstalling a Package

```bash
pip3 uninstall requests -y
```

**Output:**

```
Found existing installation: requests 2.31.0
Uninstalling requests-2.31.0:
  Successfully uninstalled requests-2.31.0
```

---

## Step 4: Virtual Environments — Why They Matter

### The Problem Without Virtual Environments

Imagine you have two projects:

- **Project A** needs `requests` version 2.28
- **Project B** needs `requests` version 2.31

If you install packages globally (without virtual environments), only one version can exist at a time. Upgrading for Project B breaks Project A.

```
┌─────────────────────────────────────────────────────┐
│  System Python (no virtual environments)            │
│                                                     │
│  Project A needs requests==2.28                     │
│  Project B needs requests==2.31                     │
│                                                     │
│  Only one version can be installed at a time.       │
│  Upgrading for B breaks A.                          │
└─────────────────────────────────────────────────────┘
```

### The Solution: Virtual Environments

A virtual environment is an isolated copy of Python with its own packages. Each project gets its own environment, so they never conflict.

```
┌──────────────────┐  ┌──────────────────┐
│  venv: project-a │  │  venv: project-b │
│  requests==2.28  │  │  requests==2.31  │
│  Isolated        │  │  Isolated        │
└──────────────────┘  └──────────────────┘
```

### Creating a Virtual Environment

```bash
python3 -m venv myenv
```

**What this does:**

- `python3 -m venv` — Runs the `venv` module (built into Python).
- `myenv` — The name of the directory where the environment will be created. You can use any name.

**What happens:** Python creates a folder called `myenv/` with its own copy of the Python interpreter and an empty package directory.

Let us look at what was created:

```bash
ls myenv/
```

**Output:**

```
bin  include  lib  pyvenv.cfg
```

- `bin/` — Contains the Python interpreter and `pip` for this environment.
- `lib/` — Where packages installed in this environment are stored.
- `pyvenv.cfg` — Configuration file that tells Python this is a virtual environment.

### Activating the Virtual Environment

Creating the environment does not activate it. You must activate it:

```bash
source myenv/bin/activate
```

**What changes:** Your terminal prompt changes to show the active environment:

```
(myenv) $
```

The `(myenv)` prefix tells you that you are now working inside the virtual environment. Any `pip install` commands will install packages only inside this environment, not globally.

**Verify it is active:**

```bash
which python
```

**Output:**

```
/home/user/myenv/bin/python
```

Notice it points to the `myenv/bin/python`, not `/usr/bin/python3`. This confirms you are using the virtual environment's Python.

### Installing Packages Inside the Virtual Environment

```bash
(myenv) $ pip install requests
```

**Output:**

```
Collecting requests
  ...
Successfully installed requests-2.31.0
```

This installs `requests` only inside `myenv/`. Your system Python and other virtual environments are not affected.

### Deactivating the Virtual Environment

When you are done working on the project:

```bash
(myenv) $ deactivate
```

**What changes:** The `(myenv)` prefix disappears from your prompt. You are back to using the system Python.

```bash
$ which python3
/usr/bin/python3
```

**Activation flow diagram:**

```
Before Activation:                After Activation:

$ which python                    (myenv) $ which python
~/.pyenv/versions/3.12/bin/python myenv/bin/python
         |                                 |
         v                                 v
   Global Python                  Virtual Environment Python
   (shared by all)                (isolated to this project)
```

### Multiple Virtual Environments — Isolation in Action

Each project gets its own virtual environment with its own packages:

```
Project A/                        Project B/
  |                                 |
  +-- .venv/                        +-- .venv/
       +-- requests 2.31.0              +-- requests 2.28.0
       +-- boto3 1.34.0                 +-- flask 3.0.0
       +-- pyyaml 6.0.1                +-- sqlalchemy 2.0.0
```

These environments are completely independent. Installing a package in Project A does not affect Project B.

**Demonstrating isolation:**

```bash
# Terminal 1 — Project A
cd project-a
python -m venv .venv
source .venv/bin/activate
pip install requests==2.31.0
pip list
# Shows: requests 2.31.0

# Terminal 2 — Project B
cd project-b
python -m venv .venv
source .venv/bin/activate
pip install requests==2.28.0
pip list
# Shows: requests 2.28.0
```

Each project has its own version of `requests` — no conflict.

### Deleting a Virtual Environment

A virtual environment is just a folder. To delete it:

```bash
deactivate                    # Exit the environment first
rm -rf myenv                  # Delete the folder
```

That is it. No uninstaller needed. All packages inside are gone. You can recreate it anytime from `requirements.txt`:

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

---

## Step 5: Managing Dependencies with requirements.txt

When you share your project with others (or deploy it to a server), they need to install the same packages you used. The `requirements.txt` file lists all packages and their exact versions.

### Creating requirements.txt

After installing all the packages your project needs, run:

```bash
(myenv) $ pip freeze > requirements.txt
```

**What this does:**

- `pip freeze` — Lists all installed packages with their exact versions.
- `> requirements.txt` — Writes the output to a file called `requirements.txt`.

**View the file:**

```bash
cat requirements.txt
```

**Output:**

```
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.6
requests==2.31.0
urllib3==2.1.0
```

You installed only `requests`, but it depends on other packages (`certifi`, `charset-normalizer`, `idna`, `urllib3`). `pip freeze` captures everything.

### Installing from requirements.txt

On another machine (or in a CI/CD pipeline), recreate the exact same environment:

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

**What `-r requirements.txt` does:** Reads the file and installs every package listed in it, at the exact versions specified.

**Output:**

```
Collecting certifi==2023.11.17
Collecting charset-normalizer==3.3.2
Collecting idna==3.6
Collecting requests==2.31.0
Collecting urllib3==2.1.0
Installing collected packages: urllib3, idna, charset-normalizer, certifi, requests
Successfully installed certifi-2023.11.17 charset-normalizer-3.3.2 idna-3.6 requests-2.31.0 urllib3-2.1.0
```

### Why Pin Exact Versions?

```
# Bad — installs whatever the latest version is
requests

# Good — installs exactly this version
requests==2.31.0
```

Without pinning, `pip install requests` installs the latest version. Six months later, a new version with breaking changes is released, and your script stops working. Pinning with `==` ensures reproducible builds.

---

## Step 6: Project Structure

Here is a standard structure for a Python automation project:

```
my-project/
├── .gitignore            # Files Git should ignore
├── requirements.txt      # Pinned dependencies
├── README.md             # Project documentation
├── config/
│   └── settings.yaml     # Configuration files
├── scripts/
│   ├── health_check.py   # Your automation scripts
│   ├── deploy.py
│   └── cleanup.py
└── tests/
    └── test_health.py    # Tests for your scripts
```

### The .gitignore File

The `.gitignore` file tells Git which files to ignore. You should never commit virtual environments or secrets to Git.

Create a `.gitignore` file:

```bash
cat > .gitignore << 'EOF'
# Virtual environments
myenv/
venv/
.venv/

# Python bytecode
__pycache__/
*.pyc

# Secrets — never commit these
.env
*.pem
*.key

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
EOF
```

**What each section does:**

- `myenv/`, `venv/`, `.venv/` — Ignores virtual environment directories. These contain platform-specific binaries and should not be shared via Git. Share `requirements.txt` instead.
- `__pycache__/`, `*.pyc` — Ignores Python bytecode files. These are auto-generated when you run Python scripts and are not needed in Git.
- `.env`, `*.pem`, `*.key` — Ignores files that contain secrets (API keys, passwords, certificates). These must never be committed.
- `.vscode/`, `.idea/` — Ignores IDE configuration files. These are personal preferences and should not be shared.
- `.DS_Store` — Ignores macOS system files.

### Why This Matters

If you run `pip install` before creating `.gitignore`, the entire `myenv/` directory (thousands of files) gets tracked by Git. To fix this:

```bash
# Add the pattern to .gitignore
echo "myenv/" >> .gitignore

# Remove the directory from Git tracking (but keep it on disk)
git rm -r --cached myenv/

# Commit the fix
git add .gitignore
git commit -m "Remove virtual environment from tracking"
```

---

## Step 7: Using a Makefile for Convenience

Typing `python3 -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt` every time is tedious. A `Makefile` automates this:

```makefile
.PHONY: setup clean run

setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "Setup complete. Run: source venv/bin/activate"

clean:
	rm -rf venv __pycache__ *.pyc

run:
	. venv/bin/activate && python3 scripts/health_check.py
```

**Usage:**

```bash
make setup    # Create environment and install dependencies
make run      # Run the main script
make clean    # Delete the environment and bytecode files
```

**What each target does:**

- `make setup` — Creates a virtual environment, installs all dependencies from `requirements.txt`, and prints a reminder to activate it.
- `make run` — Activates the environment and runs your script.
- `make clean` — Deletes the virtual environment and Python cache files. Useful for starting fresh.

---

## Common Mistakes

### Mistake 1: Installing Packages Globally with sudo

```bash
sudo pip3 install requests    # Bad!
```

**Why this is bad:** This installs packages into the system Python, which can break operating system tools that depend on specific package versions. Always use a virtual environment.

**Fix:** Create a virtual environment first, then install inside it.

### Mistake 2: Not Pinning Versions

```bash
pip install requests          # Installs latest — could be different tomorrow
pip install requests==2.31.0  # Always installs this exact version
```

**Why this matters:** Your script works today with `requests` 2.31. In 6 months, `requests` 3.0 is released with breaking changes. Without pinning, `pip install requests` on a new server installs 3.0, and your script breaks.

### Mistake 3: Committing the Virtual Environment to Git

```bash
git add myenv/    # Bad! This adds thousands of platform-specific files
```

**Why this is bad:** The `myenv/` directory contains compiled binaries specific to your operating system. It will not work on a different OS. It also adds thousands of unnecessary files to your repository.

**Fix:** Add `myenv/` to `.gitignore` and share `requirements.txt` instead.

### Mistake 4: Using pip Instead of pip3

On systems with both Python 2 and Python 3, `pip` may point to Python 2:

```bash
pip --version
# pip 20.0.2 from /usr/lib/python2.7/dist-packages/pip (python 2.7)
```

**Fix:** Always use `pip3` or `python3 -m pip` to ensure you are using Python 3.

### Mistake 5: Forgetting to Activate the Virtual Environment

```bash
python3 -m venv myenv
pip install requests          # This installs globally, not in myenv!
```

**Why:** Creating the environment does not activate it. You must run `source myenv/bin/activate` first. Check your prompt — if you do not see `(myenv)`, the environment is not active.

---

## System Python vs Your Own Python

### What is System Python?

Many operating systems come with Python pre-installed. This is called **System Python**:

```bash
python3 --version
```

**Output (example):**

```
Python 3.10.12
```

System Python is used by the operating system itself — package managers, internal tools, and OS scripts depend on it.

**Why you should NOT use System Python for your projects:**

```
Operating System
      |
      +---- System Python (used by OS tools — DO NOT TOUCH)
      |
      +---- Your Own Python (use this for projects)
```

If you install or upgrade packages in System Python, you can break OS tools. For example, upgrading `requests` globally might break a system utility that depends on an older version.

**Real-life problem:**

```bash
# Bad — modifies system Python
sudo pip install requests --upgrade

# Later, an OS tool that depends on the old version breaks
# Error: ImportError: cannot import name 'X' from 'requests'
```

**Rule:** Never use `sudo pip install` for your project dependencies. Always use a virtual environment.

### What is CPython?

CPython is the standard Python implementation — the one you download from python.org. When people say "Python," they usually mean CPython. It is written in C and is the reference implementation.

Other implementations exist (Jython, PyPy, IronPython) but CPython is what you use for DevOps work.

---

## pyenv — Managing Multiple Python Versions

### Why pyenv?

Different projects may need different Python versions:

```
pyenv
  |
  +---- Python 3.8  (legacy enterprise tool)
  +---- Python 3.10 (stable automation project)
  +---- Python 3.12 (new project with latest features)
          |
          +---- global (default for your user)
          +---- local  (per-project, stored in .python-version)
          +---- shell  (temporary, current terminal only)
```

Without pyenv, switching versions is messy. With pyenv, it is one command.

### Installing pyenv

**Linux/macOS (automatic installer):**

```bash
curl https://pyenv.run | bash
```

**macOS with Homebrew:**

```bash
brew update && brew install pyenv
```

**Add pyenv to your shell** — add these lines to `~/.bashrc` (or `~/.zshrc` for Zsh):

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Then reload your shell:

```bash
source ~/.bashrc
```

**Verify installation:**

```bash
pyenv --version
```

**Output:**

```
pyenv 2.4.8
```

### Common pyenv Commands

```bash
# List all available Python versions you can install
pyenv install --list | grep "^  3\."

# Install a specific version
pyenv install 3.12.2

# List installed versions (* marks the active one)
pyenv versions
```

**Output:**

```
  system
  3.10.13
* 3.12.2 (set by /home/user/.pyenv/version)
```

```bash
# Set the default Python version for your user
pyenv global 3.12.2

# Set Python version for a specific project (creates .python-version file)
cd myproject
pyenv local 3.11.5

# Set Python version for current terminal session only
pyenv shell 3.10.13
```

**How to verify which Python is active:**

```bash
python --version
```

**Output:**

```
Python 3.12.2
```

```bash
which python
```

**Output:**

```
/home/user/.pyenv/shims/python
```

```bash
pyenv which python
```

**Output:**

```
/home/user/.pyenv/versions/3.12.2/bin/python
```

### Common pyenv Problems

**Problem:** `pyenv: command not found`

**Cause:** Shell config not updated.

**Fix:** Add the pyenv setup lines to `~/.bashrc` or `~/.zshrc` and run `source ~/.bashrc`.

**Problem:** `python` still points to system Python after installing pyenv.

**Cause:** PATH order is wrong — system Python comes before pyenv.

**Fix:** Make sure `$PYENV_ROOT/bin` comes before system locations in PATH. Restart your terminal.

> **Tip:** Use `pyenv local` inside a project folder so teammates know which Python version the project expects. The `.python-version` file can be committed to Git.

---

## Python REPL — Interactive Testing

REPL stands for **R**ead, **E**valuate, **P**rint, **L**oop. It is an interactive Python shell where you can test code one line at a time.

### Starting the REPL

```bash
python
```

**Output:**

```
Python 3.12.2 (main, Jan 15 2024, 10:00:00)
>>> 
```

The `>>>` prompt means Python is waiting for your input.

### Using the REPL

```python
>>> 1 + 1
2

>>> name = "Laura"
>>> print(name)
Laura

>>> import json
>>> json.loads('{"env": "prod"}')
{'env': 'prod'}

>>> for i in range(3):
...     print(i)
...
0
1
2
```

**How it works:** You type a line, Python evaluates it immediately, prints the result, and waits for the next line. Expressions are automatically printed (unlike in `.py` files where you need `print()`).

### Exiting the REPL

```python
>>> exit()
```

Or press `Ctrl+D` (Linux/macOS) or `Ctrl+Z` then Enter (Windows).

### When to Use the REPL

- Quick experiments ("does this function work the way I think?")
- Testing one line of code
- Checking module behavior
- Small debugging

### When NOT to Use the REPL

- Long scripts (hard to manage)
- Code you want to save and reuse
- Multi-line programs (awkward to type)

```
Development Workflow
--------------------

Quick test? -----> REPL / IPython
                      |
                      v
              Does it work?
                      |
              +-------+-------+
              |               |
             Yes              No
              |               |
              v               v
     Write .py file     Debug in REPL
              |
              v
     Run and automate
```

---

## IPython — Enhanced Interactive Shell

IPython is a better REPL with autocomplete, syntax highlighting, and history.

### Installing IPython

```bash
pip install ipython
```

### Using IPython

```bash
ipython
```

**Output:**

```
In [1]: 
```

```python
In [1]: 1 + 1
Out[1]: 2

In [2]: name = "DevOps"
In [3]: print(name)
DevOps

In [4]: name.upper()
Out[4]: 'DEVOPS'
```

### Why IPython is Better Than the Standard REPL

| Feature | Standard REPL | IPython |
|---------|--------------|---------|
| Syntax highlighting | No | Yes |
| Tab autocomplete | Limited | Full |
| Command history | Basic | Advanced |
| Help system | `help(func)` | `func?` |
| Output numbering | No | `In[1]`, `Out[1]` |

**Getting help in IPython:**

```python
In [4]: print?
```

This shows the documentation for `print` without leaving the shell.

**Tab completion:**

```python
In [5]: name.<TAB>
# Shows all string methods: capitalize, count, endswith, find, ...
```

### IPython Help System — `?` and `??`

```python
In [1]: len?
```

**Output:**

```
Signature: len(obj, /)
Docstring: Return the number of items in a container.
Type:      builtin_function_or_method
```

**Double `??` shows the source code** (for Python-defined functions):

```python
In [2]: import json
In [3]: json.dumps??
```

This shows the actual source code of `json.dumps`. Not available for built-in C functions like `len`.

### IPython History

```python
In [10]: history
```

Shows all commands you have typed in the session. You can also press the up arrow to cycle through previous commands.

### REPL Loop Diagram

```
+---> Read: User types a line of code
|          |
|          v
|     Evaluate: Python executes the code
|          |
|          v
|     Print: Result is displayed
|          |
|          v
+---- Loop: Wait for next input
```

This is why it is called REPL — Read, Evaluate, Print, Loop. It repeats until you type `exit()` or press `Ctrl+D`.

### Real-Life Use

You are exploring a new library like `requests`. IPython helps you inspect functions, test calls, and see results faster than the standard REPL.

---

## Jupyter Notebooks — Interactive Documents

Jupyter notebooks combine code, output, and documentation in a single file. They are useful for exploration, learning, and demonstrations.

### Installing JupyterLab

```bash
pip install jupyterlab
```

### Starting JupyterLab

```bash
jupyter lab
```

This opens a browser window with the JupyterLab interface.

### How Notebooks Work

A notebook is made of **cells**. Each cell is either **code** or **markdown**:

```
Notebook (.ipynb)
  |
  +---- Markdown cell (notes, headings, explanations)
  +---- Code cell (Python code — runs and shows output below)
  +---- Code cell (more Python code)
  +---- Markdown cell (more notes)
  |
  v
Output appears below each code cell
```

**Example cells:**

Cell 1 (code):
```python
1 + 1
```
Output: `2`

Cell 2 (code):
```python
myvar = "Hello"
print(myvar)
```
Output: `Hello`

Cell 3 (markdown):
```markdown
# My Notes
This section explains the variable above.
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Shift+Enter` | Run cell and move to next |
| `Ctrl+Enter` | Run cell and stay |
| `A` | Insert cell above |
| `B` | Insert cell below |
| `M` | Convert cell to Markdown |
| `Y` | Convert cell to Code |
| `DD` | Delete selected cell |

### Multi-Line Cells and Auto-Display

In a notebook code cell, the **last expression** is automatically displayed (like the REPL):

```python
# Cell content:
x = 10
y = 20
x + y
```

**Output below cell:** `30`

But if the last line is an assignment, nothing is displayed:

```python
# Cell content:
x = 10
y = 20
result = x + y
```

**Output below cell:** (nothing)

To see the value, add it on its own line or use `print()`:

```python
# Cell content:
result = 10 + 20
result
```

**Output below cell:** `30`

### The Kernel

The **kernel** is the Python interpreter used by the notebook. Always make sure the notebook uses the correct virtual environment's kernel.

```
Kernel Selection:

JupyterLab
    |
    +-- Kernel menu -> Change Kernel
            |
            +-- Python 3 (system)        <-- might be wrong
            +-- myenv (Python 3.12.2)    <-- your venv
```

**Problem:** Notebook says "module not found" even though you installed the package.

**Cause:** Wrong kernel selected — the notebook is using a different Python than your virtual environment.

**Fix — register your venv as a Jupyter kernel:**

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Install ipykernel
pip install ipykernel

# Register the venv as a Jupyter kernel
python -m ipykernel install --user --name=myproject --display-name="My Project (Python 3.12)"
```

Now "My Project (Python 3.12)" appears in the kernel picker.

### Stopping the Jupyter Server

The Jupyter server runs in your terminal. To stop it:

- Press `Ctrl+C` in the terminal where you started `jupyter lab`
- Or close the browser tab and press `Ctrl+C`

Your notebooks are saved as `.ipynb` files. You can reopen them later.

### When to Use Notebooks vs Scripts

| Use Case | Notebook | .py Script |
|----------|----------|-----------|
| Quick exploration | Yes | No |
| Learning/demos | Yes | No |
| Production automation | No | Yes |
| CI/CD pipelines | No | Yes |
| Long-term maintenance | No | Yes |
| Sharing with non-coders | Yes | No |

**Real-life example:** A DevOps engineer uses a notebook to call an API, inspect the JSON response, and test transformation logic. Once the logic works, they move it to a `.py` script for production use.

> **Rule:** Use notebooks for exploration and learning. Use `.py` files for production scripts and automation.

---

## REPL vs Script vs Notebook — When to Use What

```
What are you doing?
        |
        +---- Quick one-line test? ---------> REPL / IPython
        |
        +---- Exploring a new library? ----> IPython or Notebook
        |
        +---- Writing reusable code? ------> .py script
        |
        +---- Building automation? --------> .py script
        |
        +---- Creating a demo/report? -----> Notebook
        |
        +---- Production deployment? ------> .py script + CI/CD
```

---

## Complete Setup Workflow

Here is the full workflow from installing Python to writing your first script:

```
Install Python (or use pyenv)
        |
        v
Install pyenv (manage multiple versions)
        |
        v
pyenv install 3.12.2
pyenv global 3.12.2
        |
        v
Create project folder
mkdir myproject && cd myproject
        |
        v
Create virtual environment
python -m venv .venv
        |
        v
Activate virtual environment
source .venv/bin/activate
        |
        v
Install packages
pip install requests boto3
        |
        v
Write code (REPL for testing, .py for scripts)
        |
        v
Save dependencies
pip freeze > requirements.txt
        |
        v
Add .gitignore (exclude .venv/, __pycache__/, .env)
        |
        v
Commit to Git
```

---

## Exercises

**Exercise 1:** Create a virtual environment called `practice-env`, activate it, install the `pyyaml` package, and verify it is installed with `pip list`.

**Exercise 2:** Run `pip freeze > requirements.txt` inside your virtual environment. Open the file and read its contents. Then deactivate the environment, create a new environment called `practice-env-2`, and install from the requirements file.

**Exercise 3:** Create a `.gitignore` file that ignores virtual environments, Python bytecode, and `.env` files. Verify it works by running `git status` (the ignored files should not appear).

---

## Summary

| Step | Command | Purpose |
|------|---------|---------|
| Check Python version | `python3 --version` | Verify Python is installed |
| Create virtual environment | `python3 -m venv myenv` | Isolated package space |
| Activate environment | `source myenv/bin/activate` | Start using the environment |
| Install a package | `pip install requests` | Add a library |
| Save dependencies | `pip freeze > requirements.txt` | Record exact versions |
| Install from file | `pip install -r requirements.txt` | Reproduce environment |
| Deactivate | `deactivate` | Return to system Python |

---

[Previous: Module 01 — Introduction](01-introduction-to-python-for-devops.md) | [Next: Module 03 — Python Fundamentals](03-python-fundamentals.md)
