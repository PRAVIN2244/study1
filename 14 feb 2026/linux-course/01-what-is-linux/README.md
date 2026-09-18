# Module 1: Introduction to Linux

## 1.1 What is Linux?

Linux is an open-source, Unix-like operating system kernel created by **Linus Torvalds** in 1991.
What we commonly call "Linux" is actually **GNU/Linux** — the Linux kernel combined with GNU
utilities and other software to form a complete operating system.

### Key Characteristics

| Feature          | Description                                                  |
|------------------|--------------------------------------------------------------|
| Open Source      | Source code is freely available under the GPL license         |
| Multi-user       | Multiple users can use the system simultaneously             |
| Multi-tasking    | Multiple processes can run concurrently                      |
| Portable         | Runs on diverse hardware: servers, desktops, phones, IoT     |
| Secure           | Strong permission model, SELinux, AppArmor                   |
| Stable           | Servers run for years without rebooting                      |

### Windows vs Linux

| Aspect                | Windows                                    | Linux                                        |
|-----------------------|--------------------------------------------|----------------------------------------------|
| **License**           | Proprietary, paid license                  | Open source, free (GPL)                      |
| **Source code**       | Closed — only Microsoft can modify         | Open — anyone can view, modify, distribute   |
| **GUI vs CLI**        | GUI-first, CLI optional (PowerShell, CMD)  | CLI-first, GUI optional (GNOME, KDE)         |
| **File system**       | NTFS, FAT32; drive letters (C:, D:)       | ext4, xfs; single root `/` tree             |
| **Path separator**    | Backslash `\` (`C:\Users\devops`)          | Forward slash `/` (`/home/devops`)           |
| **Case sensitivity**  | Case-insensitive (`File.txt` = `file.txt`) | Case-sensitive (`File.txt` ≠ `file.txt`)     |
| **File extensions**   | Required (`.exe`, `.txt`, `.docx`)         | Optional — file type determined by content   |
| **Executable files**  | `.exe`, `.msi`, `.bat`                     | Any file with execute (`x`) permission       |
| **Package manager**   | Manual installers, Microsoft Store         | `apt`, `yum`/`dnf`, `apk`, `pacman`         |
| **User model**        | Administrator + Standard users             | Root (UID 0) + regular users, `sudo`         |
| **Line endings**      | `\r\n` (CRLF)                              | `\n` (LF)                                    |
| **Shell**             | CMD, PowerShell                            | bash, zsh, sh, fish                          |
| **Hidden files**      | File attribute (Properties → Hidden)       | Filename starts with `.` (e.g., `.bashrc`)   |
| **Services**          | Windows Services (`services.msc`)          | systemd (`systemctl`)                        |
| **Remote access**     | RDP (GUI), PuTTY/SSH                       | SSH (CLI), VNC (GUI)                         |
| **Server market**     | ~20-30% of servers                         | ~70-80% of servers, dominates cloud/DevOps   |
| **Reboot frequency**  | Often required after updates               | Rarely needed, kernel live patching available|

#### Line Endings: CRLF vs LF

Text files use invisible characters to mark the end of each line. Windows and Linux use different conventions:

| Term | Bytes | Meaning | Used By |
|------|-------|---------|---------|
| **LF** (`\n`) | `0x0A` | Line Feed — move cursor to next line | Linux, macOS, Unix |
| **CR** (`\r`) | `0x0D` | Carriage Return — move cursor to start of line | Old Mac (pre-OS X) |
| **CRLF** (`\r\n`) | `0x0D 0x0A` | Carriage Return + Line Feed | Windows |

The names come from typewriters: "carriage return" moved the print head back to the left margin, and "line feed" advanced the paper up one line.

**Why this matters in DevOps:**

- A shell script written on Windows will contain `\r\n` line endings. Linux sees the `\r` as a literal character, causing errors like:
  ```
  /bin/bash^M: bad interpreter: No such file or directory
  ```
- Config files (YAML, nginx configs, Dockerfiles) can also break silently with CRLF endings.

**How to detect and fix:**

```bash
# Detect line endings
file script.sh                  # Reports "with CRLF line terminators" if Windows-style
cat -A script.sh | head -3      # CRLF lines end with ^M$, LF lines end with $

# Convert CRLF → LF
dos2unix script.sh              # In-place conversion (install: apt install dos2unix)
sed -i 's/\r$//' script.sh     # Using sed (works everywhere)
tr -d '\r' < script.sh > fixed.sh  # Using tr

# Prevent the problem — configure Git to auto-convert
git config --global core.autocrlf input   # Convert CRLF→LF on commit, keep LF on checkout
```

**What `core.autocrlf input` does:**

```
              commit                    checkout
Working dir ──────────► Git repo      Git repo ──────────► Working dir
CRLF → LF (converts)   stores LF     LF stays LF (no change)
```

| Value | On commit | On checkout | Use case |
|-------|-----------|-------------|----------|
| `input` | CRLF → LF | No conversion | Linux/macOS developers (recommended) |
| `true` | CRLF → LF | LF → CRLF | Windows developers who want CRLF locally |
| `false` | No conversion | No conversion | Manual control only |

```bash
# Set it globally
git config --global core.autocrlf input

# Verify
git config --global core.autocrlf
# → input
```

**Even better — use `.gitattributes`** (applies to everyone who clones the repo, not just your machine):

```
# Force LF for all text files
* text=auto eol=lf
```

> **Best practice**: Configure your editor and Git to always use LF (`\n`) for any file that will run on Linux.

#### Key differences for DevOps

```
Windows:                              Linux:
C:\Users\devops\Documents             /home/devops/Documents
dir                                   ls
copy file.txt backup.txt              cp file.txt backup.txt
move file.txt folder\                 mv file.txt folder/
del file.txt                          rm file.txt
type file.txt                         cat file.txt
cls                                   clear
ipconfig                              ip addr / ifconfig
tasklist                              ps aux
taskkill /PID 1234                    kill 1234
notepad file.txt                      vim file.txt / nano file.txt
```

**Why Linux dominates DevOps**: Most cloud servers (AWS, Azure, GCP), containers (Docker), and orchestration tools (Kubernetes) run on Linux. It's free, lightweight, scriptable, and designed for automation.

---

## 1.1a History of Linux

| Year | Milestone |
|------|-----------|
| 1969 | UNIX created at Bell Labs by Ken Thompson and Dennis Ritchie |
| 1983 | Richard Stallman launches the GNU Project to create a free Unix-like OS |
| 1987 | MINIX released by Andrew Tanenbaum as an educational Unix-like OS |
| 1991 | Linus Torvalds writes the Linux kernel for x86, inspired by MINIX |
| 1992 | Linux licensed under GPL v2 — becoming truly open-source |
| 1994 | Linux 1.0 released |
| 2000s | Enterprise adoption grows (Red Hat, SUSE, Ubuntu) |
| 2010s+ | Cloud, IoT, Android, WSL, Containers use Linux extensively |

---

## 1.1b GNU vs Linux vs UNIX vs POSIX

| Term | Meaning |
|------|---------|
| **GNU** | "GNU's Not Unix" — a collection of open-source tools (bash, coreutils, gcc) intended to replace proprietary UNIX tools |
| **Linux** | Just the kernel. GNU + Linux = GNU/Linux (a complete operating system) |
| **UNIX** | Proprietary operating systems like Solaris, AIX, HP-UX. Linux is Unix-*like* but not UNIX |
| **POSIX** | Portable Operating System Interface — a standard for Unix compatibility. Scripts and programs written to POSIX standards work across compliant systems |

---

## 1.1c Open Source Licensing (GPL)

Linux is licensed under the **GNU General Public License (GPL v2)**:

- **Freedom to use**: Run the software for any purpose
- **Freedom to study**: Access and modify the source code
- **Freedom to share**: Redistribute copies
- **Freedom to improve**: Distribute modified versions

**Copyleft**: If you modify and distribute GPL software, your modifications must also be GPL-licensed.

Other common open-source licenses:

| License | Key Feature |
|---------|-------------|
| GPL v2/v3 | Copyleft — derivatives must also be open source |
| MIT | Permissive — do anything, just include the license |
| Apache 2.0 | Permissive + patent protection |
| BSD | Permissive — minimal restrictions |

---

## 1.1d The Linux Philosophy

Linux follows core design principles inherited from UNIX:

1. **Everything is a File**: Devices, sockets, pipes, configs — all treated as files in `/dev`, `/proc`, `/sys`
2. **Small is Beautiful**: Programs do one thing and do it well (`grep`, `sort`, `cut`, `awk`)
3. **Text is the Universal Interface**: Config files, scripts, and logs are plain text — easy to read, parse, and automate
4. **Transparency**: Logs, processes, services — everything is inspectable

```bash
# Everything is a file — examples:
cat /proc/cpuinfo          # CPU info as a file
cat /proc/meminfo          # Memory info as a file
echo "hello" > /dev/null   # /dev/null is a file (bit bucket)
cat /dev/urandom | head -c 16 | base64   # Random data from a device file
```

---

## 1.1e Who Maintains Linux?

- **Linus Torvalds**: Still leads kernel development
- **Linux Foundation**: Coordinates funding, security, and enterprise support
- **Thousands of contributors** from companies like Google, Red Hat, Intel, Meta, Microsoft

> Microsoft is now one of the top contributors to the Linux kernel.

---

## 1.1f Real-World Applications and Stats

| Metric | Value |
|--------|-------|
| Cloud workloads | ~96% run on Linux |
| Supercomputers | 100% of top 500 run Linux |
| Mobile market | ~75% (Android is Linux-based) |
| Web servers | ~70% use Linux |

### Use Cases

| Use Case | Examples |
|----------|---------|
| **Servers** | Ubuntu Server, RHEL, Amazon Linux — 95% of public cloud |
| **Desktops** | Ubuntu, Fedora, Pop!_OS, Linux Mint |
| **Mobile** | Android is Linux-based |
| **Embedded** | Routers, TVs, Raspberry Pi, IoT devices |
| **Containers** | Alpine Linux, BusyBox — optimized for Docker |
| **Supercomputing** | All top 500 supercomputers run Linux |
| **Gaming** | Steam Deck uses Arch Linux; Proton enables Windows game compatibility |
| **AI/ML** | TensorFlow, PyTorch — commonly deployed on Ubuntu/Debian |
| **DevOps** | Docker, Kubernetes, Jenkins, GitLab — all built for Linux first |

