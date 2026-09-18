## Module 2: Variables, Data Types, Scope, and Comments

### 2.1 Comments — Single Line and Multi-Line

Bash only has single-line comments natively. Multi-line comments use a workaround.

```bash
#!/bin/bash

# ─── Single-line comment ───────────────────────────────
# This is a single-line comment. Everything after # is ignored.
echo "Hello"   # This is an inline comment

# ─── Multi-line comment (Method 1: heredoc to /dev/null) ──
# This is the most common way to comment out a block of code.

: <<'COMMENT'
This entire block is ignored by bash.
You can write anything here.
It won't be executed.
Useful for temporarily disabling code.
COMMENT

echo "This line runs normally"

# ─── Multi-line comment (Method 2: if false) ───────────
if false; then
    echo "This will never execute"
    echo "Neither will this"
    echo "Use this to disable a block of code"
fi

# ─── Multi-line comment (Method 3: colon with quotes) ──
: '
Another way to write
multi-line comments.
The colon (:) is a no-op command.
'

echo "Script continues here"
```

Run it:
```bash
$ bash comments.sh
```

**Output:**
```
Hello
This line runs normally
Script continues here
```

**Explanation:** Only the `echo` lines outside comment blocks execute. The heredoc (`<<'COMMENT'`), `if false`, and `: '...'` blocks are all ignored.

---

### 2.2 Variables — Declaration and Usage

```bash
#!/bin/bash

# ─── Variable assignment (NO spaces around =) ──────────
name="DevOps Engineer"
count=42
today=$(date +%Y-%m-%d)    # Command substitution — runs the command and stores output

# ─── Using variables ────────────────────────────────────
echo "Hello, $name"
echo "Today is $today"
echo "Count: ${count}"      # Braces for clarity and safety
```

**Output:**
```
Hello, DevOps Engineer
Today is 2025-01-15
Count: 42
```

```bash
# ─── Read-only variables (constants) ───────────────────
readonly PI=3.14159
echo "PI = $PI"
PI=3.14    # This will cause an error
```

**Output:**
```
PI = 3.14159
bash: PI: readonly variable
```

**Explanation:** `readonly` prevents a variable from being changed after assignment. Use it for values that should never change (like config paths, constants).

**Variable naming rules:**
- Letters, numbers, underscores only
- Cannot start with a number
- Convention: `UPPER_CASE` for constants/env vars, `lower_case` for local vars

```bash
# VALID names
my_var="hello"
SERVER_NAME="web01"
_private="hidden"
count2=10

# INVALID names (will cause errors)
# 2count=10        # Cannot start with number
# my-var="hello"   # Hyphens not allowed
# my var="hello"   # Spaces not allowed
```

---

### 2.3 Data Types in Bash

Bash does NOT have formal data types like Python or Java. **Everything is a string by default.** Bash interprets strings as numbers when needed for arithmetic.

```bash
#!/bin/bash

# ─── Strings (default type) ────────────────────────────
name="DevOps"
greeting='Hello World'     # Single quotes: no variable expansion
mixed="Hello, $name"       # Double quotes: variables ARE expanded

echo "$greeting"
echo "$mixed"
echo '$name is not expanded in single quotes'
```

**Output:**
```
Hello World
Hello, DevOps
$name is not expanded in single quotes
```

```bash
# ─── Integers ──────────────────────────────────────────
# Bash treats strings as integers inside $(( )) and [ -eq ]
num1=10
num2=20
sum=$((num1 + num2))
echo "Sum: $sum"

# But they're still strings underneath:
echo "num1 is stored as: '$num1'"
```

**Output:**
```
Sum: 30
num1 is stored as: '10'
```

```bash
# ─── Arrays (indexed list of values) ───────────────────
fruits=("apple" "banana" "cherry")
echo "First fruit: ${fruits[0]}"
echo "All fruits: ${fruits[@]}"
echo "Count: ${#fruits[@]}"
```

**Output:**
```
First fruit: apple
All fruits: apple banana cherry
Count: 3
```

```bash
# ─── Associative Arrays (key-value pairs, like a dictionary) ──
declare -A capitals
capitals[India]="New Delhi"
capitals[USA]="Washington DC"
capitals[UK]="London"

echo "Capital of India: ${capitals[India]}"

# Loop through all keys
for country in "${!capitals[@]}"; do
    echo "$country -> ${capitals[$country]}"
done
```

**Output:**
```
Capital of India: New Delhi
UK -> London
India -> New Delhi
USA -> Washington DC
```

**Note:** Associative array order is not guaranteed (hash map behavior).

```bash
# ─── Boolean (no native boolean — use strings or integers) ──
is_production=true
is_debug=false

if [ "$is_production" = "true" ]; then
    echo "Running in production mode"
fi

if [ "$is_debug" = "false" ]; then
    echo "Debug mode is OFF"
fi

# Alternative: use integers (0=true in exit codes, but 1=true in flags)
ENABLED=1
DISABLED=0

if [ "$ENABLED" -eq 1 ]; then
    echo "Feature is enabled"
fi
```

**Output:**
```
Running in production mode
Debug mode is OFF
Feature is enabled
```

```bash
# ─── Declare command — explicitly set types ─────────────
declare -i number=42       # Integer — arithmetic is automatic
number=number+8            # No need for $(( ))
echo "Number: $number"

declare -r CONSTANT="unchangeable"   # Read-only (same as readonly)
# CONSTANT="new"           # Error!

declare -l lower="HELLO"   # Auto-lowercase
echo "Lower: $lower"

declare -u upper="hello"   # Auto-uppercase
echo "Upper: $upper"

declare -a my_array        # Indexed array (explicit)
declare -A my_map          # Associative array (required for associative)
```

**Output:**
```
Number: 50
Lower: hello
Upper: HELLO
```

**Summary of data types:**

| Type | How to create | Example |
|------|--------------|---------|
| String | `var="text"` | `name="DevOps"` |
| Integer | `var=42` or `declare -i var=42` | `count=10` |
| Indexed Array | `var=("a" "b" "c")` | `servers=("web01" "web02")` |
| Associative Array | `declare -A var` | `declare -A config` |
| Boolean | `var=true` (just a string) | `is_active=true` |
| Read-only | `readonly var="val"` | `readonly PI=3.14` |

---

### 2.4 Variable Scope — Local, Session, User, and System

This is one of the most important concepts. Variables exist at different levels:

```
┌─────────────────────────────────────────────────────┐
│  SYSTEM SCOPE (/etc/profile, /etc/environment)      │
│  Available to ALL users on the machine              │
│  ┌─────────────────────────────────────────────┐    │
│  │  USER SCOPE (~/.bashrc, ~/.bash_profile)    │    │
│  │  Available to ONE specific user             │    │
│  │  ┌─────────────────────────────────────┐    │    │
│  │  │  SESSION SCOPE (export in terminal) │    │    │
│  │  │  Available in current terminal +    │    │    │
│  │  │  child processes                    │    │    │
│  │  │  ┌─────────────────────────────┐    │    │    │
│  │  │  │  LOCAL SCOPE (inside func) │    │    │    │
│  │  │  │  Available only in the     │    │    │    │
│  │  │  │  function that defined it  │    │    │    │
│  │  │  └─────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

#### 2.4.1 Local Scope (inside functions)

```bash
#!/bin/bash

my_function() {
    local secret="only inside function"
    global_var="I leak outside!"
    echo "Inside function: secret=$secret"
}

my_function
echo "Outside function: secret=$secret"        # Empty! local is gone
echo "Outside function: global_var=$global_var" # This works — no 'local' keyword
```

**Output:**
```
Inside function: secret=only inside function
Outside function: secret=
Outside function: global_var=I leak outside!
```

**Explanation:** `local` restricts a variable to the function. Without `local`, variables defined inside a function are global and leak out. Always use `local` inside functions.

#### 2.4.2 Session Scope (current terminal session)

```bash
# ─── Shell variable (current shell only) ────────────────
$ MY_VAR="hello"
$ echo $MY_VAR
hello

$ bash                    # Start a child shell
$ echo $MY_VAR            # Empty! Not inherited

$ exit                    # Back to parent shell

# ─── Exported variable (current shell + child processes) ─
$ export MY_VAR="hello"
$ echo $MY_VAR
hello

$ bash                    # Start a child shell
$ echo $MY_VAR            # Works! export makes it available to children
hello

$ exit
```

**Output:**
```
hello

hello
hello
```

**Explanation:** `export` makes a variable available to child processes (subshells, scripts you run). Without `export`, the variable only exists in the current shell. Session variables disappear when you close the terminal.

```bash
# ─── Demonstrate with a script ──────────────────────────
$ MY_COLOR="blue"
$ export MY_SHAPE="circle"

$ cat test.sh
#!/bin/bash
echo "Color: $MY_COLOR"    # Not exported — won't see it
echo "Shape: $MY_SHAPE"    # Exported — will see it

$ bash test.sh
```

**Output:**
```
Color:
Shape: circle
```

#### 2.4.3 User Scope (~/.bashrc, ~/.bash_profile, ~/.profile)

These files run automatically when a user logs in or opens a terminal.

```bash
# ─── ~/.bashrc — Runs every time you open a NEW terminal ─
# Add your personal aliases, functions, and variables here.

# Edit it:
$ vim ~/.bashrc

# Add these lines at the bottom:
export EDITOR="vim"
export JAVA_HOME="/usr/lib/jvm/java-17"
export PATH="$HOME/bin:$PATH"
alias ll='ls -la'
alias gs='git status'
alias k='kubectl'

# Apply changes without restarting terminal:
$ source ~/.bashrc
# or
$ . ~/.bashrc

$ echo $EDITOR
```

**Output:**
```
vim
```

```bash
# ─── ~/.bash_profile — Runs ONCE at login (SSH, console login) ─
# Use for login-specific setup. It usually sources ~/.bashrc.

# Typical ~/.bash_profile content:
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

export PATH="$HOME/.local/bin:$PATH"
```

**Which file to use?**

| File | When it runs | Use for |
|------|-------------|---------|
| `~/.bash_profile` | Login shells (SSH, console) | PATH, env vars needed at login |
| `~/.bashrc` | Every new terminal/subshell | Aliases, functions, prompt, env vars |
| `~/.profile` | Login shells (sh-compatible) | Portable settings (works with sh too) |

**Rule of thumb:** Put everything in `~/.bashrc` and have `~/.bash_profile` source it.

#### 2.4.4 System Scope (/etc/profile, /etc/environment, /etc/bash.bashrc)

These affect ALL users on the machine. Requires root/sudo to edit.

```bash
# ─── /etc/profile — Runs at login for ALL users ─────────
# System-wide environment variables and startup programs.

$ cat /etc/profile
# (shows system-wide settings)

# Example: Add a company-wide variable
$ sudo vim /etc/profile
# Add at the bottom:
export COMPANY_NAME="Acme Corp"
export ENVIRONMENT="production"
export LOG_LEVEL="warn"

# ─── /etc/environment — Simple key=value for ALL users ──
# No bash syntax — just KEY=VALUE pairs, one per line.
$ cat /etc/environment
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

$ sudo vim /etc/environment
# Add:
JAVA_HOME="/usr/lib/jvm/java-17"
LANG="en_US.UTF-8"

# ─── /etc/bash.bashrc — Runs for every bash shell for ALL users ─
$ sudo vim /etc/bash.bashrc
# Add system-wide aliases or functions here

# ─── /etc/profile.d/*.sh — Drop-in scripts for ALL users ─
# Best practice: create a file here instead of editing /etc/profile
$ sudo vim /etc/profile.d/company.sh
export COMPANY_NAME="Acme Corp"
export DEPLOY_ENV="production"
```

```bash
# ─── See where a variable comes from ────────────────────
$ echo $PATH
/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/devops/bin
```

**Loading order (login shell):**
```
1. /etc/profile              ← System-wide (all users)
2. /etc/profile.d/*.sh       ← Drop-in system scripts
3. ~/.bash_profile            ← User-specific login
   └── sources ~/.bashrc      ← User-specific every shell
```

**Real-Life Example: Setting up a DevOps workstation**

```bash
#!/bin/bash
# setup-devops-env.sh — Configure environment for a DevOps engineer
# Run once after creating a new user account

# Add to user's ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# ─── DevOps Environment ────────────────────────────────
export EDITOR="vim"
export KUBE_EDITOR="vim"
export AWS_DEFAULT_REGION="us-east-1"
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Aliases
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias d='docker'
alias dc='docker compose'
alias tf='terraform'
alias g='git'
alias gs='git status'
alias gl='git log --oneline -10'

# Prompt with git branch
parse_git_branch() {
    git branch 2>/dev/null | grep '^*' | sed 's/* //'
}
export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[33m\] ($(parse_git_branch))\[\033[00m\]\$ '
EOF

source ~/.bashrc
echo "DevOps environment configured!"
```

---

### 2.5 Special Variables

```bash
#!/bin/bash
# special-vars.sh — Demonstrate special variables

echo "Script name:        \$0  = $0"
echo "First argument:     \$1  = $1"
echo "Second argument:    \$2  = $2"
echo "All arguments:      \$@  = $@"
echo "Number of arguments:\$#  = $#"
echo "Process ID:         \$\$ = $$"
echo "Last exit code:     \$?  = $?"
```

Run it:
```bash
$ bash special-vars.sh hello world
```

**Output:**
```
Script name:        $0  = special-vars.sh
First argument:     $1  = hello
Second argument:    $2  = world
All arguments:      $@  = hello world
Number of arguments:$#  = 2
Process ID:         $$ = 12345
Last exit code:     $?  = 0
```

```bash
# ─── Important environment variables ────────────────────
echo "Home directory: $HOME"
echo "Current user:   $USER"
echo "Hostname:       $HOSTNAME"
echo "Current shell:  $SHELL"
echo "Search path:    $PATH"
```

**Output:**
```
Home directory: /home/devops
Current user:   devops
Hostname:       web01
Current shell:  /bin/bash
Search path:    /usr/local/bin:/usr/bin:/bin
```

---

### 2.6 User Input

```bash
#!/bin/bash

# Simple prompt
read -p "Enter your name: " username
echo "Hello, $username"

# Silent input (for passwords)
read -sp "Enter password: " password
echo    # Newline after silent input
echo "Password length: ${#password}"

# With timeout
read -t 5 -p "Quick! Enter something (5 sec): " answer

# With default value
read -p "Environment [staging]: " env
env=${env:-staging}    # Default to "staging" if empty
echo "Selected: $env"
```

Run it (user types "Alice", "secret", and presses Enter for default):
```bash
$ bash input.sh
```

**Output:**
```
Enter your name: Alice
Hello, Alice
Enter password:
Password length: 6
Quick! Enter something (5 sec): hi
Environment [staging]:
Selected: staging
```

---

### 2.7 String Operations

```bash
#!/bin/bash
name="DevOps Engineering"

# Length
echo "Length: ${#name}"

# Substring
echo "First 5 chars: ${name:0:5}"
echo "From position 6: ${name:6}"

# Replace
echo "Replace first: ${name/DevOps/SRE}"
echo "Replace all e: ${name//e/E}"

# Remove pattern
filepath="/var/log/nginx/access.log"
echo "Filename only: ${filepath##*/}"
echo "Directory only: ${filepath%/*}"

# Upper/lower case (bash 4+)
echo "UPPER: ${name^^}"
echo "lower: ${name,,}"
```

**Output:**
```
Length: 19
First 5 chars: DevOp
From position 6: Engineering
Replace first: SRE Engineering
Replace all e: DEvOps EnginEEring
Filename only: access.log
Directory only: /var/log/nginx
UPPER: DEVOPS ENGINEERING
lower: devops engineering
```

---

### 2.8 Arrays — Indexed and Associative

```bash
#!/bin/bash

# ─── Indexed Array ──────────────────────────────────────
servers=("web01" "web02" "db01" "cache01")

echo "First server:  ${servers[0]}"
echo "All servers:   ${servers[@]}"
echo "Server count:  ${#servers[@]}"
echo "Slice (1-2):   ${servers[@]:1:2}"

# Add element
servers+=("monitor01")
echo "After adding:  ${servers[@]}"
echo "New count:     ${#servers[@]}"
```

**Output:**
```
First server:  web01
All servers:   web01 web02 db01 cache01
Server count:  4
Slice (1-2):   web02 db01
After adding:  web01 web02 db01 cache01 monitor01
New count:     5
```

```bash
# ─── Loop through array ────────────────────────────────
for server in "${servers[@]}"; do
    echo "  Checking $server..."
done
```

**Output:**
```
  Checking web01...
  Checking web02...
  Checking db01...
  Checking cache01...
  Checking monitor01...
```

```bash
# ─── Associative Array (key-value pairs) ────────────────
declare -A server_ips
server_ips[web01]="10.0.1.10"
server_ips[web02]="10.0.1.11"
server_ips[db01]="10.0.2.10"

echo "web01 IP: ${server_ips[web01]}"

echo "All mappings:"
for name in "${!server_ips[@]}"; do
    echo "  $name -> ${server_ips[$name]}"
done
```

**Output:**
```
web01 IP: 10.0.1.10
All mappings:
  db01 -> 10.0.2.10
  web02 -> 10.0.1.11
  web01 -> 10.0.1.10
```

---

### 2.9 Arithmetic

```bash
#!/bin/bash
a=10
b=3

echo "a + b  = $((a + b))"
echo "a - b  = $((a - b))"
echo "a * b  = $((a * b))"
echo "a / b  = $((a / b))"       # Integer division
echo "a % b  = $((a % b))"       # Modulo (remainder)
echo "a ** 2 = $((a ** 2))"      # Exponent
```

**Output:**
```
a + b  = 13
a - b  = 7
a * b  = 30
a / b  = 3
a % b  = 1
a ** 2 = 100
```

```bash
# Increment / Decrement
x=5
((x++))
echo "After x++: $x"
((x += 10))
echo "After x+=10: $x"

# Floating point — use bc (bash can't do decimals)
result=$(echo "scale=2; 10 / 3" | bc)
echo "10 / 3 = $result"
```

**Output:**
```
After x++: 6
After x+=10: 16
10 / 3 = 3.33
```

---

### 2.10 Real-Life Example: Backup Script with Configurable Variables

```bash
#!/bin/bash
# backup.sh — Backup a directory with timestamp and retention

# Configuration
BACKUP_SOURCE="/var/www/html"
BACKUP_DEST="/backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="website_${TIMESTAMP}.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DEST"

# Create backup
echo "Backing up $BACKUP_SOURCE..."
tar -czf "${BACKUP_DEST}/${BACKUP_NAME}" "$BACKUP_SOURCE" 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_DEST}/${BACKUP_NAME}" | cut -f1)
    echo "Backup created: ${BACKUP_NAME} (${SIZE})"
else
    echo "ERROR: Backup failed!"
    exit 1
fi

# Clean old backups
echo "Removing backups older than ${RETENTION_DAYS} days..."
DELETED=$(find "$BACKUP_DEST" -name "website_*.tar.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
echo "Deleted $DELETED old backup(s)"

echo "Done. Current backups:"
ls -lh "$BACKUP_DEST"/website_*.tar.gz 2>/dev/null
```

### Exercises — Module 2
1. Write a script that asks for a server name and port, then checks if the port is open using `nc -z`.
2. Create a script that stores 5 server names in an array and pings each one, reporting which are reachable.
3. Write a calculator script that takes two numbers and an operator (+, -, *, /) as input.

---
