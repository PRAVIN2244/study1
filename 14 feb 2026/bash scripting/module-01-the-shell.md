## Module 1: The Shell — Your First Tool

### 1.1 What is a Shell?

The shell is a command-line interpreter that sits between you and the operating system kernel. When you type a command, the shell interprets it and asks the kernel to execute it.

```
You (human) → Shell (interpreter) → Kernel (OS core) → Hardware
```

**Common shells:**
| Shell | Path | Notes |
|-------|------|-------|
| bash | `/bin/bash` | Default on most Linux distros. This course uses bash. |
| zsh | `/bin/zsh` | Default on macOS. Mostly bash-compatible. |
| sh | `/bin/sh` | POSIX shell. Minimal, portable. |
| dash | `/bin/dash` | Lightweight, used as `/bin/sh` on Debian/Ubuntu. |

Check your current shell:

```bash
echo $SHELL
# /bin/bash
```

### 1.2 Your First Script

Create a file called `hello.sh`:

```bash
#!/bin/bash
# This is a comment
echo "Hello, DevOps World!"
```

Run it:

```bash
chmod +x hello.sh    # Make it executable
./hello.sh           # Run it
```

**The shebang (`#!/bin/bash`)** tells the OS which interpreter to use. Always include it.

### 1.3 Essential Terminal Commands (Quick Reference)

Before scripting, you need fluency with these:

```bash
# Navigation
pwd                    # Print working directory
ls -la                 # List files (long format, hidden files)
cd /var/log            # Change directory
cd -                   # Go back to previous directory

# File operations
touch file.txt         # Create empty file
cp file.txt backup.txt # Copy
mv old.txt new.txt     # Move/rename
rm -rf directory/      # Remove recursively (CAREFUL!)
mkdir -p a/b/c         # Create nested directories

# Viewing files
cat file.txt           # Print entire file
head -20 file.txt      # First 20 lines
tail -f /var/log/syslog # Follow log in real-time (DevOps essential!)
less file.txt          # Paginated view

# Searching
find / -name "*.log" -mtime -1    # Files modified in last day
grep -r "error" /var/log/         # Search recursively for "error"
which python3                      # Find command location

# System info
whoami                 # Current user
hostname               # Machine name
uname -a               # OS info
df -h                  # Disk usage
free -m                # Memory usage
```

### 1.4 File Permissions

```bash
ls -la script.sh
# -rwxr-xr-- 1 devops devops 45 Jan 15 10:00 script.sh
#  ^^^         owner
#     ^^^      group
#        ^^^   others
# r=read(4) w=write(2) x=execute(1)

chmod 755 script.sh    # rwxr-xr-x (owner: all, group/others: read+execute)
chmod +x script.sh     # Add execute for everyone
chown devops:devops script.sh  # Change owner and group
```

### 1.5 VI Editor Basics

The VI editor is essential for editing files directly on servers where graphical editors aren't available. It operates in multiple modes:

**Modes:**
- **Command mode** (default): Navigate and manipulate text
- **Insert mode**: Type text into the file
- **Line mode**: Execute commands like save, quit, search/replace

**Opening and creating files:**

```bash
vi myfile.txt          # Open existing file or create new one
```

**Entering and exiting insert mode:**

```bash
# Press 'i'    → Enter insert mode (start typing)
# Press 'Esc'  → Return to command mode
```

**Saving and quitting (from command mode, type `:` to enter line mode):**

```bash
:wq        # Save (write) and quit
:wq!       # Force save and quit (ignore warnings)
:q!        # Quit without saving
:w         # Save without quitting
```

**Inserting new lines:**

```bash
# Press 'o'   → Open new line BELOW cursor and enter insert mode
# Press 'O'   → Open new line ABOVE cursor and enter insert mode
```

**Copy, paste, and delete:**

```bash
# yy          → Yank (copy) current line
# p           → Paste after cursor
# dd          → Delete current line
# u           → Undo last change
# Ctrl+R      → Redo undone change
```

**Navigation:**

```bash
# gg          → Go to first line
# G           → Go to last line
# k / j       → Move cursor up / down
# h / l       → Move cursor left / right
```

**Searching:**

```bash
/search_term       # Search forward for 'search_term'
# Press 'n'        → Jump to next match
```

**Find and replace (substitute):**

```bash
:%s/old/new/g      # Replace all occurrences of 'old' with 'new' in entire file
# %  = entire file
# s  = substitute
# g  = global (all occurrences on each line)
```

**Quick reference table:**

| Key/Command | Action |
|-------------|--------|
| `i` | Enter insert mode |
| `Esc` | Return to command mode |
| `:wq` | Save and quit |
| `:q!` | Quit without saving |
| `o` / `O` | New line below / above |
| `yy` | Copy line |
| `p` | Paste |
| `dd` | Delete line |
| `u` | Undo |
| `Ctrl+R` | Redo |
| `gg` / `G` | Go to first / last line |
| `/text` | Search for text |
| `n` | Next search match |
| `:%s/x/y/g` | Replace x with y globally |

**DevOps relevance:** On production servers, VI (or vim) is often the only editor available. Being comfortable with it lets you edit config files, scripts, and logs directly during troubleshooting and deployments.

### 1.6 Real-Life Example: Server First-Login Info Script

When you SSH into a server, you want a quick status overview:

```bash
#!/bin/bash
# server-info.sh — Quick server status on login
# Add to ~/.bashrc to run on every login

echo "========================================="
echo "  Hostname : $(hostname)"
echo "  IP       : $(hostname -I | awk '{print $1}')"
echo "  OS       : $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"
echo "  Uptime   : $(uptime -p)"
echo "  Users    : $(who | wc -l) logged in"
echo "  Disk     : $(df -h / | awk 'NR==2 {print $5 " used of " $2}')"
echo "  Memory   : $(free -m | awk 'NR==2 {printf "%dMB / %dMB (%.1f%%)", $3, $2, $3/$2*100}')"
echo "  Load     : $(cat /proc/loadavg | awk '{print $1, $2, $3}')"
echo "========================================="
```

### Exercises — Module 1
1. Write a script that prints your username, home directory, and current shell.
2. Create a script that lists all `.conf` files in `/etc/`.
3. Modify `server-info.sh` to also show the number of running Docker containers (hint: `docker ps -q | wc -l`).

---
