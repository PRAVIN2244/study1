# Module 21: Shell Scripting Fundamentals

## 11.0 Shell Types

A shell script is a plain text file containing commands executed by a shell interpreter. Different shells have different features:

| Shell | Path | Description | Use Case |
|-------|------|-------------|----------|
| **sh** (Bourne) | `/bin/sh` | Original Unix shell, POSIX-compliant | Portable scripts |
| **bash** (Bourne Again) | `/bin/bash` | Most widely used, superset of sh | Default for most Linux distros |
| **zsh** | `/bin/zsh` | Advanced features, themes, plugins | Power users, macOS default |
| **fish** | `/usr/bin/fish` | Friendly interactive shell, auto-suggestions | Interactive use |
| **dash** | `/bin/dash` | Lightweight POSIX shell | System scripts (Ubuntu /bin/sh) |

```bash
# Check your current shell
echo $SHELL

# List available shells
cat /etc/shells

# Change default shell
chsh -s /bin/zsh

# Run a script with a specific shell
bash script.sh
sh script.sh
```

Most scripting is done in **bash**. Use `#!/bin/bash` for bash-specific features, or `#!/bin/sh` for maximum portability.

---

## 11.1 Getting Started

### Your first script

```bash
$ cat > hello.sh << 'EOF'
#!/bin/bash
echo "Hello, DevOps!"
echo "Today is $(date)"
echo "You are logged in as: $(whoami)"
echo "Current directory: $(pwd)"
EOF

$ chmod +x hello.sh
$ ./hello.sh
Hello, DevOps!
Today is Wed Feb  5 15:00:00 UTC 2025
You are logged in as: devops
Current directory: /home/devops
```

**Explanation**:
- `#!/bin/bash` — **shebang** line. Tells the system to use bash to interpret this script.
- `$(command)` — **command substitution**. Runs the command and inserts its output.
- `chmod +x` — makes the script executable.
- `./hello.sh` — runs the script (`./ ` means current directory).

### Running scripts

```bash
$ ./script.sh          # Execute directly (needs chmod +x and shebang)
$ bash script.sh       # Run with bash explicitly (no chmod needed)
$ source script.sh     # Run in current shell (variables persist)
$ . script.sh          # Same as source
```

### `source` — Run a Script in the Current Shell

```bash
$ cat set_env.sh
export APP_ENV="production"
export DB_HOST="db.example.com"
export DB_PORT="5432"
```

```bash
# Using ./script.sh — runs in a CHILD shell (variables are lost)
$ ./set_env.sh
$ echo $APP_ENV
                          # Empty — variable was set in child shell and lost

# Using source — runs in the CURRENT shell (variables persist)
$ source set_env.sh
$ echo $APP_ENV
production                # Variable is available in current session
$ echo $DB_HOST
db.example.com
```

**Explanation**: `source filename` (or `. filename`) executes the script in your **current** shell session. Variables, functions, and aliases defined in the script become available immediately. Running with `./` or `bash` creates a child process — any variables set inside are lost when the child exits.

### Source a `.env` file

```bash
$ cat .env
DB_USER="admin"
DB_PASS="s3cret"
API_KEY="abc123xyz"

$ source .env
$ echo $DB_USER
admin
```

**Explanation**: This is the standard way to load environment variables from a `.env` file before running an application.

### Reload shell configuration

```bash
$ echo 'alias ll="ls -la"' >> ~/.bashrc
$ source ~/.bashrc
$ ll
total 48
drwxr-xr-x 6 devops devops 4096 Feb  5 11:30 .
...
```

**Explanation**: After editing `~/.bashrc`, you must `source` it to apply changes without logging out and back in.

**Industry use case**: In DevOps, `source` is used to load environment-specific configs (`.env` files), activate Python virtual environments (`source venv/bin/activate`), and reload shell profiles after adding PATH entries or aliases.

**Real-life example**: A CI/CD pipeline sources different config files per environment:
```bash
source /etc/myapp/staging.env    # Load staging variables
./deploy.sh                       # Deploy with staging config
```

---

## 11.2 Variables

### Defining and using variables

```bash
#!/bin/bash
NAME="DevOps"
PORT=8080
LOG_DIR="/var/log/myapp"

echo "Hello, $NAME"
echo "Server running on port $PORT"
echo "Logs stored in ${LOG_DIR}"
```

Output:
```
Hello, DevOps
Server running on port 8080
Logs stored in /var/log/myapp
```

**Explanation**:
- No spaces around `=` (spaces cause errors)
- `$NAME` or `${NAME}` — reference a variable. Use `${}` when the variable is adjacent to other text: `${NAME}_backup`
- Quotes matter: double quotes `"` allow variable expansion, single quotes `'` treat everything literally

### Quoting rules

```bash
$ NAME="World"
$ echo "Hello $NAME"       # Double quotes: variable expanded
Hello World

$ echo 'Hello $NAME'       # Single quotes: literal string
Hello $NAME

$ echo "Path is: $(pwd)"   # Command substitution works in double quotes
Path is: /home/devops

$ echo 'Path is: $(pwd)'   # Not in single quotes
Path is: $(pwd)
```

### Special variables

```bash
#!/bin/bash
echo "Script name: $0"
echo "First argument: $1"
echo "Second argument: $2"
echo "All arguments: $@"
echo "Number of arguments: $#"
echo "Exit code of last command: $?"
echo "Process ID of this script: $$"
```

```bash
$ ./script.sh hello world
Script name: ./script.sh
First argument: hello
Second argument: world
All arguments: hello world
Number of arguments: 2
Exit code of last command: 0
Process ID of this script: 12345
```

### Exit Codes (`$?`) — Check if a Command Succeeded

Every command in Linux returns an **exit code** when it finishes. `$?` holds the exit code of the last executed command.

```bash
$ ls /etc/passwd
/etc/passwd
$ echo $?
0
```

**Explanation**: Exit code `0` means **success**. The file exists and `ls` ran without errors.

```bash
$ ls /nonexistent/path
ls: cannot access '/nonexistent/path': No such file or directory
$ echo $?
2
```

**Explanation**: Exit code `2` (non-zero) means **failure**. Any non-zero exit code indicates an error.

### Common exit codes

| Code | Meaning                          |
|------|----------------------------------|
| `0`  | Success                          |
| `1`  | General error                    |
| `2`  | Misuse of command / not found    |
| `126`| Command found but not executable |
| `127`| Command not found                |
| `130`| Terminated by Ctrl+C (SIGINT)    |

### Using `$?` in scripts

```bash
#!/bin/bash
apt update -y > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Package index updated successfully"
else
    echo "ERROR: Failed to update package index"
    exit 1
fi
```

### Using `$?` for deployment validation

```bash
#!/bin/bash
docker pull myapp:latest
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to pull Docker image"
    exit 1
fi

docker-compose up -d
echo $?    # Check if docker-compose succeeded
```

**Industry use case**: CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI) rely on exit codes to determine if a build step passed or failed. A non-zero exit code stops the pipeline and marks the build as failed.

**Real-life example**: Your deployment script runs `terraform apply`. You check `echo $?` after each step — if Terraform returns non-zero, the script stops and sends a Slack alert instead of deploying broken infrastructure.

---

### Command Chaining (`;` and `&&`)

```bash
# Generic syntax
command1 ; command2
command1 && command2
```

```bash
# Semicolon (;) — run both commands regardless of success/failure
$ mkdir /tmp/build ; echo "done"
done

# Even if the first command fails, the second still runs
$ mkdir /nonexistent/path ; echo "this still prints"
mkdir: cannot create directory '/nonexistent/path': No such file or directory
this still prints
```

```bash
# Double ampersand (&&) — run second command ONLY if first succeeds
$ mkdir /tmp/build && echo "build directory created"
build directory created

# If the first command fails, the second does NOT run
$ mkdir /nonexistent/path && echo "this will NOT print"
mkdir: cannot create directory '/nonexistent/path': No such file or directory
```

**Explanation**: `;` runs commands sequentially regardless of outcome. `&&` runs the next command only if the previous one returned exit code `0` (success). Use `&&` for safe deployment steps where each step depends on the previous one.

```bash
# Industry use case: safe build and deploy
$ make build && make test && make deploy
# deploy only runs if build AND test both succeed
```

---

### Read user input

```bash
#!/bin/bash
read -p "Enter your name: " USERNAME
read -sp "Enter password: " PASSWORD
echo ""
echo "Hello, $USERNAME"
```

```bash
$ ./script.sh
Enter your name: John
Enter password: ********
Hello, John
```

**Explanation**: `-p` sets a prompt. `-s` hides input (for passwords).

### Environment variables

```bash
# Set for current session
$ export APP_ENV="production"
$ echo $APP_ENV
production

# Set for a single command
$ APP_ENV=staging ./deploy.sh

# Common environment variables
$ echo $HOME          # /home/devops
$ echo $USER          # devops
$ echo $PATH          # /usr/local/bin:/usr/bin:/bin
$ echo $SHELL         # /bin/bash
$ echo $HOSTNAME      # devops-server
$ echo $BASH_VERSION  # 5.1.16(1)-release
$ echo $NAME          # (often empty unless you set it)
```

```bash
# If NAME is not set, define it first
$ export NAME="devops-student"
$ echo $NAME
devops-student
```

### `env` — List all environment variables

```bash
$ env
HOME=/home/devops
USER=devops
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
LANG=en_US.UTF-8
TERM=xterm-256color
SSH_CONNECTION=10.0.0.5 54321 172.17.0.2 22
...
```

**Explanation**: `env` prints all environment variables and their values. This is one of the first debugging commands when an application behaves differently across environments — the issue is often a missing or incorrect variable.

```bash
# Search for a specific variable
$ env | grep PATH
PATH=/usr/local/bin:/usr/bin:/bin

# Count total environment variables
$ env | wc -l
25

# Run a command with a clean environment
$ env -i /bin/bash --norc --noprofile
$ env
PWD=/home/devops
SHLVL=1
_=/usr/bin/env
```

**Industry use case**: When debugging issues like "works on my machine but not in production," comparing `env` output between environments reveals differences — wrong `JAVA_HOME`, missing `DATABASE_URL`, incorrect `PATH` entries, or conflicting `NODE_ENV` values.

**Real-life example**: An application fails to connect to the database in staging. Running `env | grep DB` reveals `DB_HOST` is set to the production database URL instead of staging — a misconfigured `.env` file.

---


---

## 12.9 Environment Variables & Profile Files

### Shell startup files (execution order)

```
Login shell:     /etc/profile → ~/.bash_profile → ~/.bashrc
Non-login shell: ~/.bashrc
```

```bash
# ~/.bashrc — runs for every new terminal
export EDITOR=vim
export PATH="$HOME/.local/bin:$PATH"
alias ll='ls -la'
alias gs='git status'
alias dc='docker compose'
alias k='kubectl'

# ~/.bash_profile — runs on login
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# /etc/environment — system-wide variables
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
```

### Useful aliases for DevOps

```bash
# Add to ~/.bashrc
alias update='sudo apt update && sudo apt upgrade -y'
alias ports='sudo ss -tlnp'
alias myip='curl -s ifconfig.me'
alias diskuse='du -h --max-depth=1 | sort -hr'
alias logs='sudo journalctl -f'
alias dps='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
alias kgp='kubectl get pods'
```

---

