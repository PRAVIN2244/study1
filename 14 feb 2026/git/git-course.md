# The Complete Git Course: From Zero to Expert

## Course Overview

| Module | Topic | Level |
|--------|-------|-------|
| 1 | Git Fundamentals — Installation, Configuration, Core Concepts | Beginner |
| 2 | Repository Basics — init, clone, status, add, commit | Beginner |
| 3 | Branching and Merging — branch, checkout, switch, merge, rebase | Intermediate |
| 4 | Remote Repositories — remote, fetch, pull, push, upstream tracking | Intermediate |
| 5 | History and Inspection — log, diff, show, blame, bisect | Intermediate |
| 6 | Undoing Changes — reset, revert, restore, stash, clean | Intermediate–Advanced |
| 7 | Advanced Git — cherry-pick, reflog, submodules, hooks, worktrees, tags | Advanced |
| 8 | Collaboration Workflows — GitFlow, Trunk-Based, Forking, Pull Requests | Advanced |
| 9 | Common Errors and Troubleshooting | All Levels |

---

# MODULE 1: Git Fundamentals

## 1.1 What Is Git?

Git is a **distributed version control system (DVCS)**. It tracks changes to files over time so you can recall specific versions later. Unlike centralized systems (SVN, Perforce), every developer has a full copy of the repository history on their local machine.

### Key Properties

| Property | Meaning |
|----------|---------|
| **Distributed** | Every clone is a full repository with complete history |
| **Snapshot-based** | Git stores snapshots of the entire project, not file diffs |
| **Integrity** | Every object is checksummed with SHA-1 (40-character hex hash) |
| **Speed** | Nearly all operations are local — no network latency |
| **Non-linear development** | Branching and merging are first-class operations |

### Real-World Context

Companies like **Google, Microsoft, Netflix, Facebook, and Amazon** use Git as their primary version control system. The **Linux kernel** — one of the largest open-source projects — is managed with Git (Linus Torvalds created Git in 2005 specifically for kernel development).

---

## 1.2 Installing Git

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install git -y
```

**Output:**
```
Reading package lists... Done
Setting up git (1:2.43.0-1) ...
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install git -y
```

### macOS

```bash
# Using Homebrew (recommended)
brew install git

# Or use Xcode Command Line Tools
xcode-select --install
```

### Windows

Download from [https://git-scm.com/download/win](https://git-scm.com/download/win) and run the installer. Use **Git Bash** for a Unix-like terminal experience.

### Verify Installation

```bash
git --version
```

**Output:**
```
git version 2.43.0
```

**What this tells you:** Git is installed and available in your PATH. The version number helps when troubleshooting compatibility issues.

---

## 1.3 Configuring Git

Git configuration exists at three levels:

| Level | Flag | File Location | Scope |
|-------|------|---------------|-------|
| System | `--system` | `/etc/gitconfig` | All users on the machine |
| Global | `--global` | `~/.gitconfig` | Current user, all repositories |
| Local | `--local` | `.git/config` | Current repository only |

**Precedence:** Local > Global > System (most specific wins).

### Setting Your Identity

```bash
git config --global user.name "Jane Smith"
git config --global user.email "jane.smith@company.com"
```

**What this does:** Sets the author name and email that appear in every commit you make. This is **not** authentication — it's metadata embedded in commits.

**Why it matters:** In an industry project, commits are attributed to developers. If you don't set this, Git uses your system username and hostname, which looks unprofessional in commit logs:

```
Author: root@ip-172-31-22-45 <root@ip-172-31-22-45>   ← Bad
Author: Jane Smith <jane.smith@company.com>              ← Good
```

### Setting the Default Editor

```bash
git config --global core.editor "vim"
# Or for VS Code:
git config --global core.editor "code --wait"
```

**What `--wait` does:** Tells Git to wait until you close the editor tab before proceeding (important for commit messages, interactive rebase).

### Setting the Default Branch Name

```bash
git config --global init.defaultBranch main
```

**What this does:** New repositories will use `main` instead of `master` as the default branch name. Most companies and open-source projects have adopted `main`.

### Line Ending Configuration

```bash
# On macOS/Linux:
git config --global core.autocrlf input

# On Windows:
git config --global core.autocrlf true
```

**What this does:**
- `input`: Converts CRLF to LF on commit, leaves LF on checkout (Unix convention)
- `true`: Converts LF to CRLF on checkout, CRLF to LF on commit (Windows convention)

**Why it matters:** In a team with mixed OS environments, inconsistent line endings cause noisy diffs where every line appears changed.

### Viewing Configuration

```bash
git config --list
```

**Output:**
```
user.name=Jane Smith
user.email=jane.smith@company.com
core.editor=vim
init.defaultbranch=main
core.autocrlf=input
```

### Viewing a Specific Setting

```bash
git config user.name
```

**Output:**
```
Jane Smith
```

### Viewing Where a Setting Comes From

```bash
git config --show-origin user.name
```

**Output:**
```
file:/home/jane/.gitconfig    Jane Smith
```

---

## 1.4 Core Concepts: The Three Areas

Understanding Git's architecture is essential. Every file in a Git repository exists in one of three areas:

```
┌─────────────────┐     git add     ┌─────────────────┐    git commit    ┌─────────────────┐
│  Working        │ ──────────────► │  Staging Area   │ ──────────────► │  Repository     │
│  Directory      │                 │  (Index)        │                 │  (.git)         │
│                 │ ◄────────────── │                 │ ◄────────────── │                 │
└─────────────────┘  git restore    └─────────────────┘   git reset     └─────────────────┘
```

| Area | What It Is | Analogy |
|------|-----------|---------|
| **Working Directory** | The actual files on your filesystem that you edit | Your desk where you work |
| **Staging Area (Index)** | A snapshot of what will go into the next commit | A box where you pack items to ship |
| **Repository (.git)** | The permanent history of all committed snapshots | The warehouse storing all shipped boxes |

### File States

```
Untracked ──► Staged ──► Committed ──► Modified ──► Staged ──► Committed
                                          │
                                          └──► (cycle repeats)
```

| State | Meaning |
|-------|---------|
| **Untracked** | Git doesn't know about this file yet |
| **Staged** | File is marked to be included in the next commit |
| **Committed** | File is safely stored in the local repository |
| **Modified** | File has changed since the last commit but isn't staged |

---

## 1.5 How Git Stores Data

Git is a **content-addressable filesystem**. It stores four types of objects:

| Object | Purpose | Example |
|--------|---------|---------|
| **Blob** | Stores file content (no filename, no metadata) | The raw bytes of `index.html` |
| **Tree** | Stores directory structure (maps filenames to blobs) | A directory listing |
| **Commit** | Points to a tree + metadata (author, date, message, parent) | A snapshot in time |
| **Tag** | Points to a commit with a name and optional message | `v1.0.0` release marker |

```
commit 3a4b5c ──► tree 7d8e9f ──► blob a1b2c3  (README.md)
    │                         ──► blob d4e5f6  (index.html)
    │                         ──► tree 1a2b3c  (src/)
    │                                   ──► blob 4d5e6f  (app.js)
    │
    └──► parent commit 1f2e3d
```

Every object is identified by its **SHA-1 hash** — a 40-character hexadecimal string:

```
commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
```

This means Git has built-in integrity checking. If a single byte changes, the hash changes.

---

## 1.6 Getting Help

```bash
# Full manual page
git help <command>
git help commit

# Quick reference
git <command> -h
git commit -h

# Search for a command
git help -a          # List all commands
git help -g          # List concept guides
```

**Example:**

```bash
git commit -h
```

**Output:**
```
usage: git commit [-a | --interactive | --patch] [-s] [-v] [-u<mode>]
                  [--amend] [--dry-run] [(-c | -C | --squash) <commit>]
                  ...
    -m, --message <message>
                          commit message
    -a, --all             commit all changed files
    --amend               amend previous commit
    ...
```

---

# MODULE 2: Repository Basics

## 2.1 Creating a Repository — `git init`

### Command

```bash
git init
```

**What it does:** Creates a new Git repository in the current directory by generating a `.git` subdirectory that contains all the repository metadata.

### Example: Starting a New Project

```bash
mkdir ecommerce-api
cd ecommerce-api
git init
```

**Output:**
```
Initialized empty Git repository in /home/jane/ecommerce-api/.git/
```

### What's Inside `.git/`

```bash
ls -la .git/
```

**Output:**
```
drwxr-xr-x  HEAD
drwxr-xr-x  config
drwxr-xr-x  description
drwxr-xr-x  hooks/
drwxr-xr-x  info/
drwxr-xr-x  objects/
drwxr-xr-x  refs/
```

| File/Directory | Purpose |
|---------------|---------|
| `HEAD` | Points to the current branch (e.g., `ref: refs/heads/main`) |
| `config` | Repository-level configuration |
| `objects/` | Stores all blobs, trees, commits, and tags |
| `refs/` | Stores branch and tag pointers |
| `hooks/` | Scripts that run on Git events (pre-commit, post-merge, etc.) |

### Initializing with a Specific Branch Name

```bash
git init --initial-branch=main
# or
git init -b main
```

### Industry Example: Starting a Microservice

```bash
mkdir payment-service
cd payment-service
git init -b main

# Create initial project structure
mkdir -p src tests docs
touch src/app.py src/__init__.py tests/__init__.py README.md .gitignore

echo "# Payment Service" > README.md
echo -e "*.pyc\n__pycache__/\nvenv/\n.env\n*.log" > .gitignore
```

---

## 2.2 Cloning a Repository — `git clone`

### Command

```bash
git clone <url> [directory]
```

**What it does:** Creates a local copy of a remote repository, including all branches, commits, and history. Automatically sets up `origin` as the remote.

### Example: Cloning via HTTPS

```bash
git clone https://github.com/facebook/react.git
```

**Output:**
```
Cloning into 'react'...
remote: Enumerating objects: 234521, done.
remote: Counting objects: 100% (1523/1523), done.
remote: Compressing objects: 100% (687/687), done.
remote: Total 234521 (delta 912), reused 1201 (delta 789), pack-reused 232998
Receiving objects: 100% (234521/234521), 187.45 MiB | 12.30 MiB/s, done.
Resolving deltas: 100% (167234/167234), done.
```

### Example: Cloning via SSH

```bash
git clone git@github.com:facebook/react.git
```

**When to use SSH vs HTTPS:**

| Method | Auth | Best For |
|--------|------|----------|
| HTTPS | Username/password or token | CI/CD pipelines, quick access |
| SSH | SSH key pair | Daily development, no repeated auth prompts |

### Cloning into a Custom Directory

```bash
git clone https://github.com/expressjs/express.git my-express-fork
```

**Output:**
```
Cloning into 'my-express-fork'...
```

### Shallow Clone (Partial History)

```bash
git clone --depth 1 https://github.com/torvalds/linux.git
```

**What `--depth 1` does:** Downloads only the latest commit, not the full history. The Linux kernel repo is ~4 GB with full history but ~200 MB with `--depth 1`.

**When to use:** CI/CD pipelines where you only need the latest code, not the history.

### Cloning a Specific Branch

```bash
git clone --branch develop --single-branch https://github.com/company/api.git
```

**What this does:** Clones only the `develop` branch, saving time and disk space.

---

## 2.3 Checking Repository Status — `git status`

### Command

```bash
git status
```

**What it does:** Shows the state of the working directory and staging area — which files are modified, staged, or untracked.

### Example: Clean Repository

```bash
git status
```

**Output:**
```
On branch main
nothing to commit, working tree clean
```

**Meaning:** All files match the last commit. No changes anywhere.

### Example: After Creating New Files

```bash
touch index.html style.css app.js
git status
```

**Output:**
```
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        app.js
        index.html
        style.css

nothing added to commit but untracked files present (use "git add" to track)
```

**Meaning:** Git sees three new files but isn't tracking them yet. They exist only in the working directory.

### Example: After Modifying a Tracked File

```bash
echo "<h1>Hello</h1>" > index.html
git add index.html
git commit -m "Add index.html"

# Now modify it
echo "<h1>Hello World</h1>" > index.html
git status
```

**Output:**
```
On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   index.html

no changes added to commit (use "git add" and/or "git commit -a")
```

### Short Status Format

```bash
git status -s
# or
git status --short
```

**Output:**
```
 M index.html
?? app.js
?? style.css
A  README.md
```

| Symbol | Position | Meaning |
|--------|----------|---------|
| `M` | Left column | Modified and staged |
| `M` | Right column | Modified but not staged |
| `A` | Left column | New file, staged |
| `??` | Both | Untracked file |
| `D` | Left column | Deleted and staged |
| `R` | Left column | Renamed and staged |

### Example: Mixed States

```bash
git status -s
```

**Output:**
```
MM server.js
A  config.js
 M utils.js
?? temp.log
```

**Reading this:**
- `MM server.js` — Staged changes AND additional unstaged changes (you modified it after staging)
- `A  config.js` — New file, fully staged
- ` M utils.js` — Modified, not staged
- `?? temp.log` — Untracked

---

## 2.4 Staging Files — `git add`

### Command

```bash
git add <pathspec>
```

**What it does:** Moves changes from the working directory to the staging area (index). This is how you select which changes go into the next commit.

### Stage a Single File

```bash
git add index.html
```

### Stage Multiple Specific Files

```bash
git add index.html style.css app.js
```

### Stage All Changes in Current Directory

```bash
git add .
```

**What `.` means:** The current directory and all subdirectories. Stages new, modified, and deleted files.

### Stage All Changes in the Entire Repository

```bash
git add -A
# or
git add --all
```

**Difference between `.` and `-A`:**
- `git add .` — Stages changes relative to the current directory
- `git add -A` — Stages changes across the entire repository, regardless of where you run it

### Stage Only Modified and Deleted Files (Not New)

```bash
git add -u
# or
git add --update
```

**When to use:** When you want to stage changes to tracked files but not add new untracked files.

### Interactive Staging — Stage Parts of a File

```bash
git add -p
# or
git add --patch
```

**What it does:** Lets you stage individual hunks (sections) of changes within a file. This is one of Git's most powerful features for creating clean, focused commits.

**Example:**

```bash
# You changed both the login function and the logout function in auth.js
git add -p auth.js
```

**Output:**
```
diff --git a/auth.js b/auth.js
index 1234567..abcdefg 100644
--- a/auth.js
+++ b/auth.js
@@ -10,6 +10,8 @@ function login(username, password) {
+  // Rate limiting
+  if (loginAttempts > 5) throw new Error('Too many attempts');
   const user = db.findUser(username);
   if (!user) throw new Error('User not found');

Stage this hunk [y,n,q,a,d,s,e,?]?
```

| Option | Meaning |
|--------|---------|
| `y` | Stage this hunk |
| `n` | Skip this hunk |
| `q` | Quit (don't stage remaining hunks) |
| `a` | Stage this hunk and all remaining hunks |
| `s` | Split this hunk into smaller hunks |
| `e` | Manually edit this hunk |

### Industry Example: Clean Commits in a Feature Branch

```bash
# You've been working on a feature and made changes to 5 files
# But only 3 files are related to the feature; 2 are unrelated fixes

git status -s
#  M src/auth/login.js        ← feature work
#  M src/auth/session.js      ← feature work
#  M src/auth/middleware.js    ← feature work
#  M src/utils/logger.js      ← unrelated fix
#  M src/utils/validator.js   ← unrelated fix

# Stage only the feature files
git add src/auth/login.js src/auth/session.js src/auth/middleware.js
git commit -m "feat: add session timeout handling"

# Stage the fixes separately
git add src/utils/logger.js src/utils/validator.js
git commit -m "fix: correct log level and validation edge case"
```

### Unstaging a File

```bash
git restore --staged index.html
# or (older syntax)
git reset HEAD index.html
```

---

## 2.5 Committing Changes — `git commit`

### Command

```bash
git commit
```

**What it does:** Takes everything in the staging area and creates a permanent snapshot in the repository. Opens your configured editor for the commit message.

### Commit with Inline Message

```bash
git commit -m "Add user authentication endpoint"
```

**Output:**
```
[main 3a4b5c6] Add user authentication endpoint
 3 files changed, 127 insertions(+), 4 deletions(-)
 create mode 100644 src/auth/login.js
```

**Reading the output:**
- `[main 3a4b5c6]` — Branch name and abbreviated commit hash
- `3 files changed` — Number of files affected
- `127 insertions(+), 4 deletions(-)` — Lines added and removed
- `create mode 100644` — A new file was created (100644 = regular file)

### Commit with Multi-line Message

```bash
git commit -m "Add user authentication endpoint" -m "Implements JWT-based login with rate limiting.
Includes input validation and error handling for
invalid credentials and locked accounts."
```

**Or use the editor for longer messages:**

```bash
git commit
```

This opens your editor where you write:

```
Add user authentication endpoint

Implements JWT-based login with rate limiting.
Includes input validation and error handling for
invalid credentials and locked accounts.

Ticket: AUTH-1234
```

### Commit Message Conventions

Most industry projects follow the **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

| Type | When to Use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `chore` | Build process, dependencies, tooling |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

**Examples:**

```bash
git commit -m "feat(auth): add OAuth2 Google login"
git commit -m "fix(cart): resolve race condition in quantity update"
git commit -m "docs(api): add rate limiting section to API docs"
git commit -m "refactor(db): extract connection pooling into separate module"
git commit -m "test(payment): add integration tests for Stripe webhook"
```

### Stage and Commit in One Step

```bash
git commit -a -m "Update error handling in all controllers"
# or
git commit -am "Update error handling in all controllers"
```

**What `-a` does:** Automatically stages all **modified and deleted** tracked files before committing. Does NOT add untracked (new) files.

**When to use:** Quick fixes where you've only modified existing files and want to skip the `git add` step.

### Amending the Last Commit

```bash
# Fix the message
git commit --amend -m "feat(auth): add OAuth2 Google login support"

# Add forgotten files to the last commit
git add forgotten-file.js
git commit --amend --no-edit
```

**What `--amend` does:** Replaces the last commit with a new one. The old commit is discarded.

**What `--no-edit` does:** Keeps the existing commit message unchanged.

**Warning:** Never amend commits that have been pushed to a shared branch. It rewrites history and causes problems for other developers.

### Empty Commits

```bash
git commit --allow-empty -m "ci: trigger deployment pipeline"
```

**When to use:** Triggering CI/CD pipelines without code changes, or marking milestones.

---

## 2.6 Ignoring Files — `.gitignore`

### What It Does

The `.gitignore` file tells Git which files and directories to ignore. Ignored files won't appear in `git status` and won't be staged by `git add .`.

### Syntax

```gitignore
# Comments start with #

# Ignore a specific file
secrets.env

# Ignore all files with an extension
*.log
*.tmp

# Ignore a directory
node_modules/
dist/
build/

# Ignore files in any subdirectory
**/*.pyc

# Negate a pattern (don't ignore this)
!important.log

# Ignore files only in the root directory
/TODO.md

# Ignore all files in a directory except one
logs/*
!logs/.gitkeep
```

### Industry-Standard `.gitignore` for a Node.js Project

```gitignore
# Dependencies
node_modules/

# Build output
dist/
build/
.next/

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
npm-debug.log*
yarn-debug.log*

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Test coverage
coverage/
.nyc_output/

# Temporary files
*.tmp
*.bak
```

### Industry-Standard `.gitignore` for a Python Project

```gitignore
# Byte-compiled
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
.venv/

# Distribution
dist/
build/
*.egg-info/

# Environment
.env

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Jupyter
.ipynb_checkpoints/
```

### Checking Why a File Is Ignored

```bash
git check-ignore -v debug.log
```

**Output:**
```
.gitignore:3:*.log    debug.log
```

**Meaning:** Line 3 of `.gitignore` (the `*.log` pattern) is causing `debug.log` to be ignored.

### Ignoring Already-Tracked Files

If you accidentally committed `node_modules/` before creating `.gitignore`:

```bash
# Add to .gitignore first
echo "node_modules/" >> .gitignore

# Remove from Git's tracking (keeps files on disk)
git rm -r --cached node_modules/

# Commit the removal
git commit -m "chore: remove node_modules from tracking"
```

**What `--cached` does:** Removes the file from Git's index (staging area) but leaves it on your filesystem.

### Global `.gitignore`

For files you always want to ignore across all projects (OS files, editor files):

```bash
git config --global core.excludesfile ~/.gitignore_global
```

Then create `~/.gitignore_global`:

```gitignore
.DS_Store
Thumbs.db
*.swp
*.swo
*~
.idea/
.vscode/
```

---

## 2.7 Complete Workflow Example: Starting an Industry Project

```bash
# 1. Create project
mkdir inventory-service
cd inventory-service
git init -b main

# 2. Create .gitignore FIRST (before installing dependencies)
cat > .gitignore << 'EOF'
node_modules/
dist/
.env
*.log
coverage/
.DS_Store
EOF

# 3. Initialize the project
npm init -y

# 4. Install dependencies
npm install express mongoose dotenv
npm install --save-dev jest eslint

# 5. Create project structure
mkdir -p src/{routes,models,middleware,utils} tests

# 6. Create initial files
cat > src/app.js << 'EOF'
const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

module.exports = app;
EOF

cat > src/server.js << 'EOF'
const app = require('./app');
const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

# 7. Check status
git status

# Output:
# On branch main
# No commits yet
# Untracked files:
#   .gitignore
#   package-lock.json
#   package.json
#   src/

# Notice: node_modules/ is NOT listed (ignored!)

# 8. Stage all files
git add -A

# 9. Verify what's staged
git status

# Output:
# On branch main
# Changes to be committed:
#   new file:   .gitignore
#   new file:   package-lock.json
#   new file:   package.json
#   new file:   src/app.js
#   new file:   src/server.js

# 10. First commit
git commit -m "feat: initialize inventory service with Express setup"

# Output:
# [main (root-commit) a1b2c3d] feat: initialize inventory service with Express setup
#  5 files changed, 1847 insertions(+)
#  create mode 100644 .gitignore
#  create mode 100644 package-lock.json
#  create mode 100644 package.json
#  create mode 100644 src/app.js
#  create mode 100644 src/server.js
```

---

# MODULE 3: Branching and Merging

## 3.1 Understanding Branches

A branch in Git is simply a lightweight, movable pointer to a commit. When you create a branch, Git creates a new pointer — it doesn't copy any files.

```
main:       A ── B ── C
                      ↑
                     HEAD
```

When you create a new branch `feature`:

```
main:       A ── B ── C
                      ↑
feature:              (also points here)
```

After committing on `feature`:

```
main:       A ── B ── C
                       \
feature:                D ── E
                             ↑
                            HEAD
```

**HEAD** is a special pointer that tells Git which branch (and commit) you're currently on.

---

## 3.2 Creating Branches — `git branch`

### List All Local Branches

```bash
git branch
```

**Output:**
```
  develop
* main
  feature/login
```

The `*` indicates the current branch.

### List All Branches (Including Remote)

```bash
git branch -a
```

**Output:**
```
  develop
* main
  feature/login
  remotes/origin/main
  remotes/origin/develop
  remotes/origin/feature/payment
```

### List Branches with Last Commit Info

```bash
git branch -v
```

**Output:**
```
  develop       7a8b9c0 Add database migration scripts
* main          3d4e5f6 Merge pull request #42
  feature/login a1b2c3d Add JWT token validation
```

### Create a New Branch (Without Switching)

```bash
git branch feature/user-profile
```

**What it does:** Creates a new branch pointer at the current commit. You stay on your current branch.

### Create a Branch from a Specific Commit

```bash
git branch hotfix/security-patch 3a4b5c6
```

**What it does:** Creates a branch starting from commit `3a4b5c6` instead of the current HEAD.

### Rename a Branch

```bash
# Rename the current branch
git branch -m new-name

# Rename a specific branch
git branch -m old-name new-name
```

**Example:**

```bash
git branch -m feature/login feature/auth-login
```

### Delete a Branch

```bash
# Delete a merged branch
git branch -d feature/user-profile

# Force delete an unmerged branch
git branch -D feature/abandoned-experiment
```

**Output (successful):**
```
Deleted branch feature/user-profile (was a1b2c3d).
```

**Output (error — branch not merged):**
```
error: The branch 'feature/abandoned-experiment' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/abandoned-experiment'.
```

**What `-d` vs `-D` means:**
- `-d` (lowercase): Safe delete — refuses if the branch has unmerged changes
- `-D` (uppercase): Force delete — deletes regardless of merge status

---

## 3.3 Switching Branches — `git switch` and `git checkout`

### Modern Way: `git switch` (Git 2.23+)

```bash
git switch develop
```

**Output:**
```
Switched to branch 'develop'
Your branch is up to date with 'origin/develop'.
```

### Create and Switch in One Step

```bash
git switch -c feature/shopping-cart
```

**Output:**
```
Switched to a new branch 'feature/shopping-cart'
```

**What `-c` means:** Create the branch if it doesn't exist.

### Legacy Way: `git checkout`

```bash
# Switch to existing branch
git checkout develop

# Create and switch
git checkout -b feature/shopping-cart
```

**Why `git switch` was introduced:** `git checkout` does too many things (switch branches, restore files, detach HEAD). `git switch` is focused solely on branch switching, reducing confusion.

### Switch to a Remote Branch

```bash
# First, fetch remote branches
git fetch origin

# Switch to a remote branch (creates local tracking branch automatically)
git switch feature/payment
# or
git checkout feature/payment
```

**Output:**
```
branch 'feature/payment' set up to track 'origin/feature/payment'.
Switched to a new branch 'feature/payment'
```

### Detached HEAD State

```bash
git checkout 3a4b5c6
```

**Output:**
```
Note: switching to '3a4b5c6'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

HEAD is now at 3a4b5c6 Add user authentication
```

**What this means:** HEAD points directly to a commit, not a branch. Any commits you make here will be "orphaned" when you switch to a branch — unless you create a branch first:

```bash
git switch -c rescue-branch
```

---

## 3.4 Merging — `git merge`

### Command

```bash
git merge <branch>
```

**What it does:** Integrates changes from `<branch>` into the current branch.

### Fast-Forward Merge

When the current branch hasn't diverged from the branch being merged:

```
Before:
main:       A ── B ── C
                       \
feature:                D ── E

After (git merge feature while on main):
main:       A ── B ── C ── D ── E
                                ↑
                               HEAD
```

```bash
git switch main
git merge feature/add-search
```

**Output:**
```
Updating 3a4b5c6..7d8e9f0
Fast-forward
 src/search.js     | 45 +++++++++++++++++++++++++++++++++++++++++++++
 src/routes/api.js |  8 ++++++--
 2 files changed, 51 insertions(+), 2 deletions(-)
 create mode 100644 src/search.js
```

**"Fast-forward"** means Git just moved the branch pointer forward — no merge commit was created.

### Force a Merge Commit (No Fast-Forward)

```bash
git merge --no-ff feature/add-search
```

**Output:**
```
Merge made by the 'ort' strategy.
 src/search.js     | 45 +++++++++++++++++++++++++++++++++++++++++++++
 src/routes/api.js |  8 ++++++--
 2 files changed, 51 insertions(+), 2 deletions(-)
```

```
Before:
main:       A ── B ── C
                       \
feature:                D ── E

After (--no-ff):
main:       A ── B ── C ──────── M  (merge commit)
                       \        /
feature:                D ── E
```

**Why use `--no-ff`:** Preserves the fact that a feature branch existed. The merge commit acts as a marker. Many teams require this in their workflow.

### Three-Way Merge

When both branches have diverged:

```
Before:
main:       A ── B ── C ── F
                       \
feature:                D ── E

After merge:
main:       A ── B ── C ── F ── M  (merge commit)
                       \       /
feature:                D ── E
```

```bash
git switch main
git merge feature/notifications
```

**Output:**
```
Merge made by the 'ort' strategy.
 src/notifications.js | 78 ++++++++++++++++++++++++++++++++++++++++
 src/models/user.js   | 12 ++++---
 3 files changed, 86 insertions(+), 4 deletions(-)
```

---

## 3.5 Merge Conflicts

Conflicts occur when both branches modify the same lines in the same file.

### Example: Creating a Conflict

```bash
# On main
echo "port = 3000" > config.txt
git add config.txt && git commit -m "Add config"

# Create and switch to feature branch
git switch -c feature/update-port
echo "port = 8080" > config.txt
git add config.txt && git commit -m "Change port to 8080"

# Switch back to main and make a different change
git switch main
echo "port = 5000" > config.txt
git add config.txt && git commit -m "Change port to 5000"

# Now merge
git merge feature/update-port
```

**Output:**
```
Auto-merging config.txt
CONFLICT (content): Merge conflict in config.txt
Automatic merge failed; fix conflicts and then commit the result.
```

### What the Conflict Looks Like

```bash
cat config.txt
```

**Output:**
```
<<<<<<< HEAD
port = 5000
=======
port = 8080
>>>>>>> feature/update-port
```

| Marker | Meaning |
|--------|---------|
| `<<<<<<< HEAD` | Start of current branch's version |
| `=======` | Separator between the two versions |
| `>>>>>>> feature/update-port` | End of incoming branch's version |

### Resolving the Conflict

1. **Edit the file** — remove the markers and keep the correct content:

```
port = 8080
```

2. **Stage the resolved file:**

```bash
git add config.txt
```

3. **Complete the merge:**

```bash
git commit -m "merge: resolve port conflict, use 8080"
```

### Checking Conflict Status

```bash
git status
```

**Output (during conflict):**
```
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
        both modified:   config.txt
```

### Aborting a Merge

```bash
git merge --abort
```

**What it does:** Cancels the merge and returns to the state before you ran `git merge`. All conflict markers are removed.

### Industry Example: Resolving a Real Conflict

```javascript
// <<<<<<< HEAD (main branch - your teammate's change)
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}
// =======
// (your feature branch - you added tax calculation)
function calculateTotal(items, taxRate = 0.08) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return subtotal + (subtotal * taxRate);
}
// >>>>>>> feature/tax-calculation
```

**Resolution** — combine both changes:

```javascript
function calculateTotal(items, taxRate = 0.08) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return subtotal + (subtotal * taxRate);
}
```

---

## 3.6 Rebasing — `git rebase`

### Command

```bash
git rebase <base-branch>
```

**What it does:** Moves (replays) your branch's commits on top of another branch, creating a linear history.

### Merge vs Rebase — Visual Comparison

**Merge:**
```
main:       A ── B ── C ── F ── M
                       \       /
feature:                D ── E
```

**Rebase:**
```
main:       A ── B ── C ── F
                            \
feature:                     D' ── E'
```

After rebase, `D'` and `E'` are new commits (different hashes) with the same changes as `D` and `E`, but based on `F` instead of `C`.

### Example

```bash
# You're on feature/dashboard, main has moved ahead
git switch feature/dashboard
git rebase main
```

**Output:**
```
Successfully rebased and updated refs/heads/feature/dashboard.
```

**If conflicts occur during rebase:**

```
CONFLICT (content): Merge conflict in src/dashboard.js
error: could not apply 3a4b5c6... Add dashboard layout
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
```

**Resolving:**

```bash
# 1. Fix the conflict in the file
# 2. Stage the fix
git add src/dashboard.js
# 3. Continue the rebase
git rebase --continue
```

### Interactive Rebase — `git rebase -i`

```bash
git rebase -i HEAD~4
```

**What it does:** Opens an editor showing the last 4 commits, letting you reorder, squash, edit, or drop them.

**Editor content:**

```
pick a1b2c3d Add user model
pick d4e5f6a Add user controller
pick 7g8h9i0 Fix typo in user model
pick j1k2l3m Add user routes

# Rebase 3a4b5c6..j1k2l3m onto 3a4b5c6 (4 commands)
#
# Commands:
# p, pick   = use commit
# r, reword = use commit, but edit the commit message
# e, edit   = use commit, but stop for amending
# s, squash = use commit, but meld into previous commit
# f, fixup  = like "squash", but discard this commit's log message
# d, drop   = remove commit
```

**Common operations:**

| Action | What to Do |
|--------|-----------|
| Squash fix into previous | Change `pick` to `fixup` on the fix commit |
| Reword a message | Change `pick` to `reword` |
| Combine commits | Change `pick` to `squash` on commits to combine |
| Remove a commit | Change `pick` to `drop` |
| Reorder commits | Move lines up/down |

**Example: Squash the typo fix into the original commit:**

```
pick a1b2c3d Add user model
fixup 7g8h9i0 Fix typo in user model
pick d4e5f6a Add user controller
pick j1k2l3m Add user routes
```

**Result:** 3 clean commits instead of 4. The typo fix is absorbed into "Add user model."

### When to Rebase vs Merge

| Scenario | Use |
|----------|-----|
| Updating a feature branch with latest main | `git rebase main` |
| Merging a completed feature into main | `git merge --no-ff feature` |
| Cleaning up commits before a PR | `git rebase -i` |
| Shared branch with multiple developers | `git merge` (never rebase shared branches) |

### The Golden Rule of Rebasing

**Never rebase commits that have been pushed to a shared branch.** Rebasing rewrites commit history (creates new hashes). If others have based work on the original commits, their history will diverge.

```bash
# SAFE: Rebase your local feature branch onto updated main
git switch feature/my-work
git rebase main

# DANGEROUS: Rebase main (shared branch)
git switch main
git rebase feature/something   # DON'T DO THIS
```

---

## 3.7 Industry Branching Example: Feature Development

```bash
# 1. Start from latest main
git switch main
git pull origin main

# 2. Create feature branch
git switch -c feature/JIRA-1234-user-notifications

# 3. Work on the feature (multiple commits)
# ... edit files ...
git add src/notifications/
git commit -m "feat(notifications): add email notification service"

# ... more edits ...
git add src/notifications/ src/models/
git commit -m "feat(notifications): add notification preferences model"

# ... fix a bug you introduced ...
git add src/notifications/email.js
git commit -m "fix(notifications): handle null email addresses"

# 4. Before creating PR, clean up commits
git rebase -i HEAD~3
# Squash the fix into the first commit

# 5. Update with latest main
git fetch origin
git rebase origin/main

# 6. Push to remote
git push origin feature/JIRA-1234-user-notifications

# 7. Create Pull Request (via GitHub/GitLab UI or CLI)

# 8. After PR is merged, clean up
git switch main
git pull origin main
git branch -d feature/JIRA-1234-user-notifications
```

---

# MODULE 4: Remote Repositories

## 4.1 Understanding Remotes

A **remote** is a reference to a repository hosted on a server (GitHub, GitLab, Bitbucket, self-hosted). When you clone a repository, Git automatically creates a remote called `origin`.

```
Your Machine                          Server (GitHub)
┌──────────────┐                     ┌──────────────┐
│ Local Repo   │ ── git push ──────► │ Remote Repo  │
│              │ ◄── git fetch ───── │ (origin)     │
│ main         │                     │ main         │
│ feature/x    │                     │ feature/x    │
└──────────────┘                     └──────────────┘
```

Your local repository tracks **remote-tracking branches** like `origin/main`. These are read-only snapshots of where the remote branches were the last time you communicated with the server.

---

## 4.2 Managing Remotes — `git remote`

### List Remotes

```bash
git remote
```

**Output:**
```
origin
```

### List Remotes with URLs

```bash
git remote -v
```

**Output:**
```
origin  https://github.com/company/inventory-service.git (fetch)
origin  https://github.com/company/inventory-service.git (push)
```

### Add a Remote

```bash
git remote add upstream https://github.com/original-author/project.git
```

**What this does:** Adds a second remote called `upstream`. Common when you fork a project — `origin` is your fork, `upstream` is the original.

```bash
git remote -v
```

**Output:**
```
origin    https://github.com/your-username/project.git (fetch)
origin    https://github.com/your-username/project.git (push)
upstream  https://github.com/original-author/project.git (fetch)
upstream  https://github.com/original-author/project.git (push)
```

### Rename a Remote

```bash
git remote rename origin github
```

### Remove a Remote

```bash
git remote remove upstream
```

### Show Detailed Remote Info

```bash
git remote show origin
```

**Output:**
```
* remote origin
  Fetch URL: https://github.com/company/api.git
  Push  URL: https://github.com/company/api.git
  HEAD branch: main
  Remote branches:
    develop                tracked
    feature/payment        tracked
    main                   tracked
  Local branches configured for 'git pull':
    develop merges with remote develop
    main    merges with remote main
  Local refs configured for 'git push':
    develop pushes to develop (up to date)
    main    pushes to main    (up to date)
```

### Change a Remote's URL

```bash
# Switch from HTTPS to SSH
git remote set-url origin git@github.com:company/api.git
```

---

## 4.3 Fetching — `git fetch`

### Command

```bash
git fetch <remote>
```

**What it does:** Downloads commits, branches, and tags from the remote repository but does NOT modify your working directory or local branches. It updates your remote-tracking branches (`origin/main`, `origin/develop`, etc.).

### Fetch from Origin

```bash
git fetch origin
```

**Output:**
```
remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
remote: Compressing objects: 100% (8/8), done.
remote: Total 12 (delta 5), reused 10 (delta 4), pack-reused 0
Unpacking objects: 100% (12/12), 3.42 KiB | 349.00 KiB/s, done.
From https://github.com/company/api
   3a4b5c6..7d8e9f0  main       -> origin/main
 * [new branch]      feature/x  -> origin/feature/x
```

**Reading the output:**
- `3a4b5c6..7d8e9f0 main -> origin/main` — The remote `main` has new commits; your `origin/main` pointer was updated
- `[new branch] feature/x` — A new branch exists on the remote

### Fetch All Remotes

```bash
git fetch --all
```

### Fetch and Prune Deleted Remote Branches

```bash
git fetch --prune
# or
git fetch -p
```

**What `--prune` does:** Removes remote-tracking branches that no longer exist on the remote. Without this, deleted remote branches linger in your local list.

**Example:**

```bash
git fetch -p
```

**Output:**
```
From https://github.com/company/api
 - [deleted]         (none)     -> origin/feature/old-feature
   3a4b5c6..7d8e9f0  main       -> origin/main
```

### When to Use Fetch

- Before merging or rebasing, to see what's changed on the remote
- To check if there are new branches without modifying your work
- In scripts and CI/CD pipelines where you need control over when changes are applied

---

## 4.4 Pulling — `git pull`

### Command

```bash
git pull <remote> <branch>
```

**What it does:** `git pull` = `git fetch` + `git merge`. It downloads remote changes and immediately merges them into your current branch.

### Basic Pull

```bash
git pull origin main
```

**Output:**
```
remote: Enumerating objects: 5, done.
remote: Counting objects: 100% (5/5), done.
remote: Compressing objects: 100% (3/3), done.
remote: Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
Unpacking objects: 100% (3/3), 1.12 KiB | 1.12 MiB/s, done.
From https://github.com/company/api
 * branch            main       -> FETCH_HEAD
   3a4b5c6..7d8e9f0  main       -> origin/main
Updating 3a4b5c6..7d8e9f0
Fast-forward
 src/routes/users.js | 15 ++++++++++++---
 1 file changed, 12 insertions(+), 3 deletions(-)
```

### Pull with Rebase Instead of Merge

```bash
git pull --rebase origin main
# or
git pull -r origin main
```

**What this does:** Instead of creating a merge commit, it replays your local commits on top of the fetched changes. Results in a cleaner, linear history.

**Set rebase as default for pull:**

```bash
git config --global pull.rebase true
```

### Pull When Tracking Branch Is Set

If your local branch tracks a remote branch, you can simply:

```bash
git pull
```

Git knows which remote and branch to pull from.

### Pull vs Fetch — When to Use Which

| Situation | Command | Why |
|-----------|---------|-----|
| Quick update, no local changes | `git pull` | Simple and fast |
| Want to review changes first | `git fetch` then `git log origin/main` | Inspect before merging |
| Have local commits, want clean history | `git pull --rebase` | Avoids merge commits |
| CI/CD pipeline | `git fetch` + explicit merge/rebase | Full control |

---

## 4.5 Pushing — `git push`

### Command

```bash
git push <remote> <branch>
```

**What it does:** Uploads your local commits to the remote repository.

### Push to Origin

```bash
git push origin main
```

**Output:**
```
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Delta compression using up to 8 threads
Compressing objects: 100% (3/3), done.
Writing objects: 100% (3/3), 1.24 KiB | 1.24 MiB/s, done.
Total 3 (delta 1), reused 0 (delta 0), pack-reused 0
To https://github.com/company/api.git
   3a4b5c6..7d8e9f0  main -> main
```

### Push a New Branch for the First Time

```bash
git push -u origin feature/user-auth
# or
git push --set-upstream origin feature/user-auth
```

**What `-u` does:** Sets up tracking so that future `git push` and `git pull` commands on this branch don't need the remote and branch name.

**Output:**
```
Total 0 (delta 0), reused 0 (delta 0), pack-reused 0
remote:
remote: Create a pull request for 'feature/user-auth' on GitHub by visiting:
remote:      https://github.com/company/api/pull/new/feature/user-auth
remote:
To https://github.com/company/api.git
 * [new branch]      feature/user-auth -> feature/user-auth
branch 'feature/user-auth' set up to track 'origin/feature/user-auth'.
```

### Push All Branches

```bash
git push --all origin
```

### Push Tags

```bash
# Push a specific tag
git push origin v1.0.0

# Push all tags
git push origin --tags
```

### Force Push

```bash
git push --force origin feature/my-branch
# or safer:
git push --force-with-lease origin feature/my-branch
```

**What `--force` does:** Overwrites the remote branch with your local version, even if the remote has commits you don't have locally. **Destructive.**

**What `--force-with-lease` does:** Force pushes only if the remote branch is where you think it is. If someone else pushed commits since your last fetch, it fails instead of overwriting their work.

**When force push is needed:**
- After `git rebase` on a feature branch
- After `git commit --amend` on a pushed commit
- After `git rebase -i` to clean up history

**When force push is dangerous:**
- On `main`, `develop`, or any shared branch
- When you haven't fetched recently

### Delete a Remote Branch

```bash
git push origin --delete feature/old-branch
# or
git push origin :feature/old-branch
```

**Output:**
```
To https://github.com/company/api.git
 - [deleted]         feature/old-branch
```

---

## 4.6 Upstream Tracking

### What Is Tracking?

A local branch can "track" a remote branch. This means Git knows the default remote and branch for `push` and `pull` operations.

### Set Upstream for Existing Branch

```bash
git branch --set-upstream-to=origin/main main
# or shorter
git branch -u origin/main
```

### Check Tracking Configuration

```bash
git branch -vv
```

**Output:**
```
  develop       7a8b9c0 [origin/develop] Add migration scripts
* main          3d4e5f6 [origin/main] Merge PR #42
  feature/auth  a1b2c3d [origin/feature/auth: ahead 2] Add token refresh
  local-only    f1e2d3c No tracking branch
```

**Reading this:**
- `[origin/develop]` — Tracking, up to date
- `[origin/main]` — Tracking, up to date
- `[origin/feature/auth: ahead 2]` — Tracking, you have 2 local commits not yet pushed
- No bracket — Not tracking any remote branch

### Ahead and Behind

```bash
git status
```

**Output:**
```
On branch feature/auth
Your branch is ahead of 'origin/feature/auth' by 2 commits.
  (use "git push" to publish your local commits)
```

Other possible messages:

```
Your branch is behind 'origin/main' by 3 commits, and can be fast-forwarded.
Your branch and 'origin/main' have diverged,
and have 2 and 3 different commits each, respectively.
```

---

## 4.7 Industry Example: Fork and Contribute Workflow

This is the standard open-source contribution workflow:

```bash
# 1. Fork the project on GitHub (via web UI)

# 2. Clone YOUR fork
git clone https://github.com/your-username/react.git
cd react

# 3. Add the original repo as upstream
git remote add upstream https://github.com/facebook/react.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/your-username/react.git (fetch)
# origin    https://github.com/your-username/react.git (push)
# upstream  https://github.com/facebook/react.git (fetch)
# upstream  https://github.com/facebook/react.git (push)

# 5. Create a feature branch
git switch -c fix/memory-leak-useEffect

# 6. Make changes and commit
git add src/hooks/useEffect.js
git commit -m "fix: resolve memory leak in useEffect cleanup"

# 7. Before pushing, sync with upstream
git fetch upstream
git rebase upstream/main

# 8. Push to YOUR fork
git push origin fix/memory-leak-useEffect

# 9. Create Pull Request from your fork to the original repo (via web UI)

# 10. Keep your fork's main in sync
git switch main
git fetch upstream
git merge upstream/main
git push origin main
```

---

# MODULE 5: History and Inspection

## 5.1 Viewing Commit History — `git log`

### Basic Log

```bash
git log
```

**Output:**
```
commit 7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e (HEAD -> main, origin/main)
Author: Jane Smith <jane@company.com>
Date:   Mon Jan 15 14:30:00 2025 +0000

    feat(api): add rate limiting middleware

commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
Author: John Doe <john@company.com>
Date:   Mon Jan 15 10:15:00 2025 +0000

    fix(auth): handle expired JWT tokens gracefully

commit 1f2e3d4c5b6a7980fedc1234abcd5678ef901234
Author: Jane Smith <jane@company.com>
Date:   Fri Jan 12 16:45:00 2025 +0000

    feat(auth): add OAuth2 Google login
```

Press `q` to exit the pager.

### One-Line Format

```bash
git log --oneline
```

**Output:**
```
7d8e9f0 feat(api): add rate limiting middleware
3a4b5c6 fix(auth): handle expired JWT tokens gracefully
1f2e3d4 feat(auth): add OAuth2 Google login
a9b8c7d chore: update dependencies
5e6f7a8 feat(db): add connection pooling
```

### Limit Number of Commits

```bash
git log --oneline -5
```

Shows only the last 5 commits.

### Log with Graph (Branch Visualization)

```bash
git log --oneline --graph --all
```

**Output:**
```
*   7d8e9f0 (HEAD -> main) Merge branch 'feature/rate-limit'
|\
| * a1b2c3d feat(api): add rate limiting middleware
| * d4e5f6a feat(api): add rate limit config
|/
* 3a4b5c6 fix(auth): handle expired JWT tokens
| * 9f8e7d6 (feature/notifications) feat: add push notifications
|/
* 1f2e3d4 feat(auth): add OAuth2 Google login
```

### Log with Diff (Patch)

```bash
git log -p -2
```

**What `-p` does:** Shows the actual diff (patch) for each commit.
**What `-2` does:** Limits to the last 2 commits.

**Output:**
```
commit 7d8e9f0...
Author: Jane Smith <jane@company.com>
Date:   Mon Jan 15 14:30:00 2025 +0000

    feat(api): add rate limiting middleware

diff --git a/src/middleware/rateLimit.js b/src/middleware/rateLimit.js
new file mode 100644
index 0000000..a1b2c3d
--- /dev/null
+++ b/src/middleware/rateLimit.js
@@ -0,0 +1,15 @@
+const rateLimit = require('express-rate-limit');
+
+const apiLimiter = rateLimit({
+  windowMs: 15 * 60 * 1000,
+  max: 100,
+  message: { error: 'Too many requests' }
+});
+
+module.exports = { apiLimiter };
```

### Log with Statistics

```bash
git log --stat -3
```

**Output:**
```
commit 7d8e9f0...
Author: Jane Smith <jane@company.com>
Date:   Mon Jan 15 14:30:00 2025 +0000

    feat(api): add rate limiting middleware

 src/middleware/rateLimit.js | 15 +++++++++++++++
 src/app.js                 |  3 ++-
 package.json               |  1 +
 3 files changed, 18 insertions(+), 1 deletion(-)
```

### Custom Format

```bash
git log --pretty=format:"%h %an %ar %s" -10
```

**Output:**
```
7d8e9f0 Jane Smith 2 hours ago feat(api): add rate limiting middleware
3a4b5c6 John Doe 6 hours ago fix(auth): handle expired JWT tokens
1f2e3d4 Jane Smith 3 days ago feat(auth): add OAuth2 Google login
```

| Placeholder | Meaning |
|-------------|---------|
| `%H` | Full commit hash |
| `%h` | Abbreviated hash |
| `%an` | Author name |
| `%ae` | Author email |
| `%ar` | Relative date |
| `%ad` | Author date |
| `%s` | Subject (first line of message) |
| `%b` | Body of message |
| `%d` | Ref names (branches, tags) |

### Filter by Author

```bash
git log --author="Jane Smith" --oneline
```

### Filter by Date

```bash
git log --after="2025-01-01" --before="2025-02-01" --oneline
```

### Filter by Message

```bash
git log --grep="fix" --oneline
```

**Output:**
```
3a4b5c6 fix(auth): handle expired JWT tokens gracefully
b2c3d4e fix(cart): resolve race condition in quantity update
e5f6a7b fix(db): handle connection timeout
```

### Filter by File

```bash
git log --oneline -- src/auth/login.js
```

**What `--` does:** Separates the command options from the file path. Shows only commits that touched `src/auth/login.js`.

### Filter by Content Change (Pickaxe)

```bash
git log -S "calculateTotal" --oneline
```

**What `-S` does:** Finds commits where the string `calculateTotal` was added or removed. Useful for finding when a function was introduced or deleted.

### Log Between Two Commits/Tags

```bash
git log v1.0.0..v2.0.0 --oneline
```

Shows commits that are in `v2.0.0` but not in `v1.0.0`.

---

## 5.2 Viewing Differences — `git diff`

### Unstaged Changes (Working Directory vs Staging Area)

```bash
git diff
```

**Output:**
```
diff --git a/src/app.js b/src/app.js
index a1b2c3d..d4e5f6a 100644
--- a/src/app.js
+++ b/src/app.js
@@ -10,7 +10,9 @@ const app = express();
 app.use(express.json());
+app.use(cors());
+app.use(helmet());

 app.get('/health', (req, res) => {
-  res.json({ status: 'ok' });
+  res.json({ status: 'ok', version: '1.2.0', uptime: process.uptime() });
 });
```

**Reading the diff:**
- `---` = old version, `+++` = new version
- Lines starting with `-` (red) = removed
- Lines starting with `+` (green) = added
- Lines with no prefix = context (unchanged)
- `@@ -10,7 +10,9 @@` = hunk header: starting at line 10, showing 7 lines in old / 9 lines in new

### Staged Changes (Staging Area vs Last Commit)

```bash
git diff --staged
# or
git diff --cached
```

**What this shows:** Changes that are staged and will be included in the next commit.

### Diff Between Two Commits

```bash
git diff 3a4b5c6 7d8e9f0
```

### Diff Between Branches

```bash
git diff main..feature/auth
```

### Diff for a Specific File

```bash
git diff src/app.js
```

### Diff Statistics Only

```bash
git diff --stat
```

**Output:**
```
 src/app.js          | 5 +++--
 src/routes/users.js | 12 +++++++++---
 2 files changed, 12 insertions(+), 5 deletions(-)
```

### Diff with Word-Level Changes

```bash
git diff --word-diff
```

**Output:**
```
res.json({ status: 'ok', [-timestamp: new Date()-]{+version: '1.2.0', uptime: process.uptime()+} });
```

### Diff Names Only

```bash
git diff --name-only main..feature/auth
```

**Output:**
```
src/auth/login.js
src/auth/session.js
src/middleware/auth.js
tests/auth.test.js
```

### Diff with Name and Status

```bash
git diff --name-status main..feature/auth
```

**Output:**
```
M       src/auth/login.js
M       src/auth/session.js
A       src/middleware/auth.js
A       tests/auth.test.js
D       src/auth/legacy.js
```

| Status | Meaning |
|--------|---------|
| `M` | Modified |
| `A` | Added |
| `D` | Deleted |
| `R` | Renamed |
| `C` | Copied |

---

## 5.3 Viewing a Specific Commit — `git show`

### Command

```bash
git show <commit>
```

**What it does:** Displays the metadata and diff of a specific commit.

### Example

```bash
git show 3a4b5c6
```

**Output:**
```
commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
Author: John Doe <john@company.com>
Date:   Mon Jan 15 10:15:00 2025 +0000

    fix(auth): handle expired JWT tokens gracefully

diff --git a/src/auth/middleware.js b/src/auth/middleware.js
index 1234567..abcdefg 100644
--- a/src/auth/middleware.js
+++ b/src/auth/middleware.js
@@ -15,6 +15,10 @@ function verifyToken(req, res, next) {
     const decoded = jwt.verify(token, process.env.JWT_SECRET);
     req.user = decoded;
     next();
+  } catch (err) {
+    if (err.name === 'TokenExpiredError') {
+      return res.status(401).json({ error: 'Token expired', code: 'TOKEN_EXPIRED' });
+    }
+    return res.status(403).json({ error: 'Invalid token' });
   }
```

### Show Only the Files Changed

```bash
git show --stat 3a4b5c6
```

### Show a File at a Specific Commit

```bash
git show 3a4b5c6:src/auth/middleware.js
```

**What this does:** Displays the entire content of `middleware.js` as it existed at commit `3a4b5c6`.

### Show the Latest Commit

```bash
git show HEAD
```

### Show the Commit Before the Latest

```bash
git show HEAD~1
# or
git show HEAD^
```

---

## 5.4 Finding Who Changed What — `git blame`

### Command

```bash
git blame <file>
```

**What it does:** Shows who last modified each line of a file, along with the commit hash and date.

### Example

```bash
git blame src/auth/middleware.js
```

**Output:**
```
3a4b5c6d (John Doe   2025-01-15 10:15:00 +0000  1) const jwt = require('jsonwebtoken');
3a4b5c6d (John Doe   2025-01-15 10:15:00 +0000  2)
1f2e3d4c (Jane Smith 2025-01-12 16:45:00 +0000  3) function verifyToken(req, res, next) {
1f2e3d4c (Jane Smith 2025-01-12 16:45:00 +0000  4)   const token = req.headers.authorization?.split(' ')[1];
7d8e9f0a (Jane Smith 2025-01-15 14:30:00 +0000  5)   if (!token) {
7d8e9f0a (Jane Smith 2025-01-15 14:30:00 +0000  6)     return res.status(401).json({ error: 'No token provided' });
7d8e9f0a (Jane Smith 2025-01-15 14:30:00 +0000  7)   }
```

**Reading this:** Each line shows:
- Commit hash (abbreviated)
- Author name
- Date
- Line number
- Line content

### Blame a Specific Range of Lines

```bash
git blame -L 10,20 src/auth/middleware.js
```

**What `-L 10,20` does:** Shows blame only for lines 10 through 20.

### Blame Ignoring Whitespace Changes

```bash
git blame -w src/auth/middleware.js
```

### Blame Detecting Moved/Copied Lines

```bash
git blame -M src/auth/middleware.js    # Detect moved lines within a file
git blame -C src/auth/middleware.js    # Detect lines moved from other files
```

### Industry Use Case

A production bug is reported. You need to find who changed the payment calculation logic:

```bash
git blame src/payment/calculator.js -L 45,60
```

**Output:**
```
a9b8c7d6 (Bob Wilson 2025-01-10 09:00:00 +0000 45) function calculateDiscount(total, code) {
a9b8c7d6 (Bob Wilson 2025-01-10 09:00:00 +0000 46)   const discount = discountCodes[code];
f1e2d3c4 (Alice Chen 2025-01-14 11:30:00 +0000 47)   if (!discount) return total;
f1e2d3c4 (Alice Chen 2025-01-14 11:30:00 +0000 48)   return total - (total * discount.percentage);
```

Now you know Alice changed lines 47-48 on Jan 14. Check her commit:

```bash
git show f1e2d3c4
```

---

## 5.5 Binary Search for Bugs — `git bisect`

### What It Does

`git bisect` performs a binary search through your commit history to find the exact commit that introduced a bug. Instead of checking every commit, it halves the search space each time.

### How It Works

If you have 1000 commits between "working" and "broken," checking each one takes up to 1000 steps. Binary search takes at most 10 steps (log2(1000) ≈ 10).

### Step-by-Step Example

```bash
# 1. Start bisecting
git bisect start

# 2. Mark the current commit as bad (has the bug)
git bisect bad

# 3. Mark a known good commit (before the bug existed)
git bisect good v1.0.0
```

**Output:**
```
Bisecting: 512 revisions left to test after this (roughly 9 steps)
[abc123def456] feat: add caching layer
```

Git checks out a commit halfway between good and bad. Test your application:

```bash
# 4. Test the application. If the bug exists:
git bisect bad

# Output:
# Bisecting: 256 revisions left to test after this (roughly 8 steps)
# [def789abc012] refactor: update query builder

# 5. Test again. If the bug does NOT exist:
git bisect good

# Output:
# Bisecting: 128 revisions left to test after this (roughly 7 steps)
```

Continue marking `good` or `bad` until Git finds the culprit:

```bash
# Final output:
# f1e2d3c4a5b6 is the first bad commit
# commit f1e2d3c4a5b6
# Author: Bob Wilson <bob@company.com>
# Date:   Wed Jan 10 09:00:00 2025 +0000
#
#     refactor: optimize discount calculation
```

```bash
# 6. End bisecting (returns to your original branch)
git bisect reset
```

### Automated Bisect with a Test Script

```bash
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
git bisect run npm test
```

**What this does:** Git automatically runs `npm test` at each step. If the test exits with code 0 (pass), Git marks it as `good`. If it exits with non-zero (fail), Git marks it as `bad`.

**Output:**
```
running npm test
Tests: 142 passed, 0 failed
Bisecting: 256 revisions left...
running npm test
Tests: 140 passed, 2 failed
...
f1e2d3c4a5b6 is the first bad commit
```

### Bisect with a Custom Script

```bash
git bisect start HEAD v1.0.0
git bisect run bash -c 'curl -s http://localhost:3000/api/discount?code=SAVE20 | grep -q "\"amount\":80\"'
```

---

## 5.6 Searching Code — `git grep`

### Command

```bash
git grep <pattern>
```

**What it does:** Searches for a text pattern across all tracked files. Faster than `grep -r` because it only searches Git-tracked files and uses Git's internal index.

### Basic Search

```bash
git grep "TODO"
```

**Output:**
```
src/auth/login.js:12:  // TODO: add rate limiting
src/payment/checkout.js:45:  // TODO: handle currency conversion
src/utils/logger.js:3:  // TODO: switch to structured logging
```

### Search with Line Numbers

```bash
git grep -n "calculateTotal"
```

### Search in a Specific Commit

```bash
git grep "deprecated" v1.0.0
```

### Count Matches per File

```bash
git grep -c "console.log"
```

**Output:**
```
src/auth/login.js:3
src/routes/users.js:7
src/utils/debug.js:15
```

---

## 5.7 Short Log — `git shortlog`

### Command

```bash
git shortlog
```

**What it does:** Summarizes `git log` output, grouped by author.

### Example

```bash
git shortlog -sn
```

**Output:**
```
    142  Jane Smith
     98  John Doe
     67  Alice Chen
     34  Bob Wilson
```

| Flag | Meaning |
|------|---------|
| `-s` | Show only count (suppress commit messages) |
| `-n` | Sort by number of commits (descending) |
| `-e` | Show email addresses |

### Shortlog for a Date Range

```bash
git shortlog -sn --after="2025-01-01" --before="2025-02-01"
```

---

# MODULE 6: Undoing Changes

## 6.1 Overview: Choosing the Right Undo Command

| Situation | Command | Destructive? |
|-----------|---------|-------------|
| Discard unstaged changes to a file | `git restore <file>` | Yes — changes are lost |
| Unstage a file (keep changes in working dir) | `git restore --staged <file>` | No |
| Undo the last commit, keep changes staged | `git reset --soft HEAD~1` | No |
| Undo the last commit, keep changes unstaged | `git reset HEAD~1` (mixed) | No |
| Undo the last commit, discard all changes | `git reset --hard HEAD~1` | Yes — changes are lost |
| Undo a commit that's already pushed | `git revert <commit>` | No — creates a new commit |
| Save work temporarily | `git stash` | No |
| Remove untracked files | `git clean` | Yes — files are deleted |

---

## 6.2 Restoring Files — `git restore`

`git restore` (Git 2.23+) replaces the confusing dual-purpose `git checkout` for file operations.

### Discard Unstaged Changes

```bash
git restore src/app.js
```

**What it does:** Replaces the working directory version of `src/app.js` with the version from the staging area (or the last commit if nothing is staged).

**Output:** No output on success. The file is silently reverted.

**Warning:** This permanently discards your uncommitted changes. There is no undo.

### Discard All Unstaged Changes

```bash
git restore .
```

### Unstage a File

```bash
git restore --staged src/app.js
```

**What it does:** Moves the file from the staging area back to the working directory. The changes are preserved — they're just no longer staged.

**Before:**
```
Changes to be committed:
        modified:   src/app.js
```

**After:**
```
Changes not staged for commit:
        modified:   src/app.js
```

### Unstage All Files

```bash
git restore --staged .
```

### Restore a File from a Specific Commit

```bash
git restore --source=3a4b5c6 src/app.js
```

**What it does:** Replaces the working directory version with the version from commit `3a4b5c6`. The change appears as unstaged.

### Restore a Deleted File

```bash
# File was deleted but not committed
git restore deleted-file.js

# File was deleted in a previous commit
git restore --source=HEAD~1 deleted-file.js
```

---

## 6.3 Resetting — `git reset`

`git reset` moves the branch pointer and optionally modifies the staging area and working directory.

### The Three Modes

```
                    --soft          --mixed (default)    --hard
                    ─────           ─────────────────    ──────
Repository:         Moves HEAD ←    Moves HEAD ←         Moves HEAD ←
Staging Area:       Unchanged       Reset to match HEAD  Reset to match HEAD
Working Directory:  Unchanged       Unchanged            Reset to match HEAD
```

### Soft Reset — Undo Commit, Keep Everything Staged

```bash
git reset --soft HEAD~1
```

**What it does:** Moves HEAD back one commit. All changes from that commit are now in the staging area, ready to be re-committed.

**Use case:** You committed too early and want to add more changes or fix the commit message.

**Before:**
```
A ── B ── C (HEAD)
          ↑ committed: "Add login" with files X, Y
```

**After:**
```
A ── B (HEAD)
     Files X, Y are staged
```

**Example:**

```bash
# Oops, committed with wrong message and forgot a file
git reset --soft HEAD~1
git add forgotten-file.js
git commit -m "feat(auth): add login with session management"
```

### Mixed Reset (Default) — Undo Commit, Unstage Changes

```bash
git reset HEAD~1
# same as
git reset --mixed HEAD~1
```

**What it does:** Moves HEAD back one commit. Changes are in the working directory but NOT staged.

**Use case:** You want to reorganize what goes into which commit.

**Example:**

```bash
# You committed auth changes and logging changes together
git reset HEAD~1

# Now selectively stage and commit
git add src/auth/
git commit -m "feat(auth): add login endpoint"

git add src/logging/
git commit -m "feat(logging): add request logging"
```

### Hard Reset — Undo Everything

```bash
git reset --hard HEAD~1
```

**What it does:** Moves HEAD back one commit. Discards ALL changes — staging area and working directory are reset to match the target commit.

**Warning:** This is destructive. Uncommitted changes are permanently lost.

**Use case:** You want to completely abandon the last commit and all its changes.

**Example:**

```bash
# Experimental commit that didn't work out
git reset --hard HEAD~1
```

**Output:**
```
HEAD is now at 3a4b5c6 fix(auth): handle expired JWT tokens
```

### Reset to a Specific Commit

```bash
git reset --hard 3a4b5c6
```

### Reset a Single File (Unstage)

```bash
git reset HEAD src/app.js
# Modern equivalent:
git restore --staged src/app.js
```

### Industry Example: Squashing Last 3 Commits

```bash
# You made 3 small commits that should be one
git reset --soft HEAD~3
git commit -m "feat(dashboard): add analytics dashboard with charts"
```

---

## 6.4 Reverting — `git revert`

### Command

```bash
git revert <commit>
```

**What it does:** Creates a NEW commit that undoes the changes from the specified commit. The original commit remains in history. This is the safe way to undo changes that have been pushed.

### Example

```bash
git revert 3a4b5c6
```

**Opens editor with message:**
```
Revert "fix(auth): handle expired JWT tokens"

This reverts commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b.
```

**Output:**
```
[main 9f8e7d6] Revert "fix(auth): handle expired JWT tokens"
 1 file changed, 4 deletions(+), 10 insertions(+)
```

**History:**
```
A ── B ── C ── D (revert of C)
```

### Revert Without Committing

```bash
git revert --no-commit 3a4b5c6
# or
git revert -n 3a4b5c6
```

**What this does:** Applies the revert changes to the staging area but doesn't create a commit. Useful when you want to revert multiple commits in a single commit.

### Revert Multiple Commits

```bash
# Revert a range of commits (oldest..newest)
git revert --no-commit HEAD~3..HEAD
git commit -m "revert: undo last 3 commits due to regression"
```

### Revert a Merge Commit

```bash
git revert -m 1 <merge-commit-hash>
```

**What `-m 1` means:** When reverting a merge commit, you must specify which parent to revert to. `-m 1` means "keep the first parent" (usually the branch you merged into).

### When to Use Revert vs Reset

| Scenario | Use | Why |
|----------|-----|-----|
| Undo a pushed commit on a shared branch | `git revert` | Preserves history, safe for collaborators |
| Undo a local commit not yet pushed | `git reset` | Cleaner history, no revert commit |
| Undo a commit on your own feature branch | Either | Your choice — reset is cleaner |
| Production hotfix rollback | `git revert` | Auditable, doesn't rewrite history |

---

## 6.5 Stashing — `git stash`

### What It Does

`git stash` temporarily saves your uncommitted changes (both staged and unstaged) and reverts your working directory to the last commit. Think of it as a clipboard for your work-in-progress.

### Basic Stash

```bash
git stash
```

**Output:**
```
Saved working directory and index state WIP on feature/auth: 3a4b5c6 Add login endpoint
```

**Your working directory is now clean:**
```bash
git status
# On branch feature/auth
# nothing to commit, working tree clean
```

### Stash with a Message

```bash
git stash push -m "WIP: halfway through refactoring auth middleware"
```

### Stash Including Untracked Files

```bash
git stash -u
# or
git stash --include-untracked
```

**Why:** By default, `git stash` only saves tracked files. `-u` also saves new files that haven't been added to Git yet.

### Stash Only Staged Changes

```bash
git stash push --staged
```

### List All Stashes

```bash
git stash list
```

**Output:**
```
stash@{0}: On feature/auth: WIP: halfway through refactoring auth middleware
stash@{1}: WIP on main: 7d8e9f0 Add rate limiting
stash@{2}: On feature/payment: debugging stripe webhook
```

### Apply the Latest Stash (Keep It in the Stash List)

```bash
git stash apply
```

### Apply and Remove the Latest Stash

```bash
git stash pop
```

**Difference:** `apply` keeps the stash in the list; `pop` removes it after applying.

### Apply a Specific Stash

```bash
git stash apply stash@{2}
# or
git stash pop stash@{2}
```

### View Stash Contents

```bash
git stash show
```

**Output:**
```
 src/auth/middleware.js | 15 +++++++++------
 src/auth/session.js   |  8 ++++++++
 2 files changed, 17 insertions(+), 6 deletions(-)
```

### View Stash Diff

```bash
git stash show -p stash@{0}
```

### Drop a Specific Stash

```bash
git stash drop stash@{1}
```

### Clear All Stashes

```bash
git stash clear
```

**Warning:** This permanently deletes all stashed changes.

### Industry Example: Urgent Bug Fix While Working on a Feature

```bash
# You're working on a feature
# ... editing files ...

# Urgent bug report comes in!
git stash push -m "WIP: user profile feature"

# Switch to main and fix the bug
git switch main
git pull origin main
git switch -c hotfix/critical-payment-bug

# ... fix the bug ...
git add src/payment/checkout.js
git commit -m "fix(payment): prevent double charge on timeout"
git push origin hotfix/critical-payment-bug

# Switch back to your feature and restore your work
git switch feature/user-profile
git stash pop

# Continue working where you left off
```

---

## 6.6 Cleaning Untracked Files — `git clean`

### Command

```bash
git clean
```

**What it does:** Removes untracked files from the working directory.

### Dry Run (Preview What Would Be Deleted)

```bash
git clean -n
# or
git clean --dry-run
```

**Output:**
```
Would remove debug.log
Would remove temp.txt
Would remove src/test-output.json
```

### Remove Untracked Files

```bash
git clean -f
```

**What `-f` means:** Force. Git requires this flag to prevent accidental deletion.

### Remove Untracked Files and Directories

```bash
git clean -fd
```

### Remove Ignored Files Too

```bash
git clean -fdx
```

**What `-x` does:** Also removes files matched by `.gitignore` (like `node_modules/`, `dist/`, `.env`).

**Warning:** This is very destructive. Use `-n` first to preview.

### Interactive Clean

```bash
git clean -i
```

**Output:**
```
Would remove the following items:
  debug.log    temp.txt    src/test-output.json
*** Commands ***
    1: clean    2: filter by pattern    3: select by numbers
    4: ask each    5: quit    6: help
What now>
```

---

## 6.7 Summary: Undo Decision Tree

```
Want to undo changes?
│
├── Changes are NOT committed?
│   ├── Want to discard working directory changes? → git restore <file>
│   ├── Want to unstage? → git restore --staged <file>
│   └── Want to save for later? → git stash
│
├── Changes ARE committed but NOT pushed?
│   ├── Want to redo the commit? → git reset --soft HEAD~1
│   ├── Want to reorganize commits? → git reset HEAD~1
│   └── Want to completely discard? → git reset --hard HEAD~1
│
└── Changes ARE committed AND pushed?
    └── git revert <commit>  (always safe)
```

---

# MODULE 7: Advanced Git

## 7.1 Cherry-Picking — `git cherry-pick`

### Command

```bash
git cherry-pick <commit-hash>
```

**What it does:** Applies the changes from a specific commit onto your current branch. Creates a new commit with the same changes but a different hash.

### Example

```bash
# You're on main and need one specific fix from the develop branch
git log --oneline develop
# a1b2c3d feat: add caching
# d4e5f6a fix: resolve null pointer in user lookup  ← you need this one
# 7g8h9i0 feat: add logging

git switch main
git cherry-pick d4e5f6a
```

**Output:**
```
[main 9f8e7d6] fix: resolve null pointer in user lookup
 Date: Mon Jan 15 10:15:00 2025 +0000
 1 file changed, 3 insertions(+), 1 deletion(-)
```

### Cherry-Pick Without Committing

```bash
git cherry-pick --no-commit d4e5f6a
```

**What this does:** Applies the changes to the staging area but doesn't create a commit. Useful when you want to combine changes from multiple cherry-picks into one commit.

### Cherry-Pick Multiple Commits

```bash
git cherry-pick d4e5f6a 7g8h9i0 a1b2c3d
```

### Cherry-Pick a Range

```bash
git cherry-pick d4e5f6a..a1b2c3d
```

**Note:** The start commit is exclusive (not included). To include it:

```bash
git cherry-pick d4e5f6a^..a1b2c3d
```

### Handling Cherry-Pick Conflicts

```bash
git cherry-pick d4e5f6a
# CONFLICT (content): Merge conflict in src/user.js

# 1. Resolve the conflict in the file
# 2. Stage the resolution
git add src/user.js
# 3. Continue
git cherry-pick --continue

# Or abort
git cherry-pick --abort
```

### Industry Example: Hotfix Backporting

```bash
# A critical fix was made on main (v2.x)
# You need to apply it to the v1.x release branch

git switch release/v1.x
git cherry-pick abc123def   # the fix commit from main
git push origin release/v1.x

# Now both v1.x and v2.x have the fix
```

---

## 7.2 Recovery with Reflog — `git reflog`

### What It Does

The reflog (reference log) records every time HEAD moves — every commit, checkout, reset, merge, rebase, etc. It's your safety net for recovering "lost" commits.

### Command

```bash
git reflog
```

**Output:**
```
7d8e9f0 (HEAD -> main) HEAD@{0}: commit: feat(api): add rate limiting
3a4b5c6 HEAD@{1}: reset: moving to HEAD~2
f1e2d3c HEAD@{2}: commit: feat(auth): add session timeout
a9b8c7d HEAD@{3}: commit: feat(auth): add token refresh
5e6f7a8 HEAD@{4}: checkout: moving from develop to main
b2c3d4e HEAD@{5}: commit: feat(db): add connection pooling
```

### Recovering a "Lost" Commit After Hard Reset

```bash
# Oops! You accidentally reset too far
git reset --hard HEAD~3

# Check reflog to find the lost commit
git reflog
# 3a4b5c6 HEAD@{0}: reset: moving to HEAD~3
# 7d8e9f0 HEAD@{1}: commit: the commit you want back

# Recover it
git reset --hard 7d8e9f0
```

### Recovering After a Bad Rebase

```bash
# Rebase went wrong
git rebase main
# ... conflicts everywhere, things are broken

# Find the state before the rebase
git reflog
# abc1234 HEAD@{0}: rebase (continue): ...
# def5678 HEAD@{1}: rebase (start): checkout main
# 9f8e7d6 HEAD@{2}: commit: your last good commit  ← this one

# Go back to before the rebase
git reset --hard 9f8e7d6
```

### Recovering a Deleted Branch

```bash
# Oops, deleted a branch with unmerged work
git branch -D feature/important-work

# Find the last commit of that branch
git reflog
# ... look for the last commit on that branch ...
# a1b2c3d HEAD@{5}: commit: last commit on feature/important-work

# Recreate the branch
git branch feature/important-work a1b2c3d
```

### Reflog Expiry

Reflog entries expire after 90 days (30 days for unreachable commits). You can configure this:

```bash
git config --global gc.reflogExpire 180
git config --global gc.reflogExpireUnreachable 90
```

---

## 7.3 Tags — `git tag`

### What Tags Are

Tags mark specific commits as important — typically used for release versions. Unlike branches, tags don't move when new commits are made.

### Lightweight Tags

```bash
git tag v1.0.0
```

**What it does:** Creates a simple pointer to the current commit. No metadata.

### Annotated Tags (Recommended)

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
```

**What `-a` does:** Creates an annotated tag with metadata (tagger name, email, date, message). Annotated tags are stored as full objects in Git.

### List Tags

```bash
git tag
```

**Output:**
```
v0.1.0
v0.2.0
v1.0.0
v1.0.1
v1.1.0
```

### List Tags with Pattern

```bash
git tag -l "v1.*"
```

**Output:**
```
v1.0.0
v1.0.1
v1.1.0
```

### Show Tag Details

```bash
git show v1.0.0
```

**Output:**
```
tag v1.0.0
Tagger: Jane Smith <jane@company.com>
Date:   Fri Jan 12 16:45:00 2025 +0000

Release version 1.0.0

commit 1f2e3d4c5b6a7980fedc1234abcd5678ef901234
Author: Jane Smith <jane@company.com>
Date:   Fri Jan 12 16:45:00 2025 +0000

    feat(auth): add OAuth2 Google login
...
```

### Tag a Past Commit

```bash
git tag -a v0.9.0 -m "Beta release" 3a4b5c6
```

### Push Tags to Remote

```bash
# Push a specific tag
git push origin v1.0.0

# Push all tags
git push origin --tags
```

### Delete a Tag

```bash
# Delete locally
git tag -d v1.0.0

# Delete from remote
git push origin --delete v1.0.0
# or
git push origin :refs/tags/v1.0.0
```

### Checkout a Tag

```bash
git checkout v1.0.0
```

**Warning:** This puts you in detached HEAD state. To make changes, create a branch:

```bash
git checkout -b hotfix/v1.0.1 v1.0.0
```

### Industry Example: Semantic Versioning Release

```bash
# Finish feature work, merge to main
git switch main
git merge --no-ff feature/payment-v2

# Tag the release
git tag -a v2.0.0 -m "Major release: new payment system

Breaking changes:
- Payment API endpoints restructured
- Webhook payload format changed

New features:
- Multi-currency support
- Subscription billing
- Invoice generation"

# Push code and tag
git push origin main
git push origin v2.0.0
```

---

## 7.4 Submodules — `git submodule`

### What Submodules Are

Submodules let you include one Git repository inside another. The parent repo tracks a specific commit of the submodule, not its branch.

### Add a Submodule

```bash
git submodule add https://github.com/company/shared-utils.git libs/shared-utils
```

**Output:**
```
Cloning into '/home/jane/project/libs/shared-utils'...
remote: Enumerating objects: 45, done.
...
```

**What this creates:**
- A `libs/shared-utils/` directory with the submodule's code
- A `.gitmodules` file tracking the submodule configuration

```bash
cat .gitmodules
```

**Output:**
```
[submodule "libs/shared-utils"]
    path = libs/shared-utils
    url = https://github.com/company/shared-utils.git
```

### Clone a Repository with Submodules

```bash
# Method 1: Clone then initialize
git clone https://github.com/company/main-project.git
cd main-project
git submodule init
git submodule update

# Method 2: Clone with submodules in one step
git clone --recurse-submodules https://github.com/company/main-project.git
```

### Update Submodules

```bash
# Update to the commit tracked by the parent repo
git submodule update

# Update to the latest commit on the submodule's branch
git submodule update --remote
```

### Check Submodule Status

```bash
git submodule status
```

**Output:**
```
 a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0 libs/shared-utils (v1.2.0)
```

### Remove a Submodule

```bash
git submodule deinit libs/shared-utils
git rm libs/shared-utils
rm -rf .git/modules/libs/shared-utils
git commit -m "chore: remove shared-utils submodule"
```

---

## 7.5 Git Hooks

### What Hooks Are

Hooks are scripts that Git runs automatically before or after events like commit, push, and merge. They live in `.git/hooks/`.

### Available Hooks

| Hook | When It Runs | Common Use |
|------|-------------|------------|
| `pre-commit` | Before a commit is created | Lint code, run tests, check formatting |
| `prepare-commit-msg` | After default message is created, before editor opens | Add ticket number to message |
| `commit-msg` | After message is entered | Validate commit message format |
| `post-commit` | After commit is created | Notifications, logging |
| `pre-push` | Before push to remote | Run full test suite |
| `pre-rebase` | Before rebase starts | Prevent rebasing shared branches |
| `post-merge` | After merge completes | Install dependencies, run migrations |
| `post-checkout` | After checkout/switch | Install dependencies for the branch |

### Example: Pre-Commit Hook (Lint Before Commit)

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "Running linter..."
npm run lint

if [ $? -ne 0 ]; then
    echo "❌ Linting failed. Fix errors before committing."
    exit 1
fi

echo "Running tests..."
npm test

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Fix tests before committing."
    exit 1
fi

echo "✅ All checks passed."
EOF

chmod +x .git/hooks/pre-commit
```

### Example: Commit-Msg Hook (Enforce Conventional Commits)

```bash
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash

commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|test|chore|perf|ci)(\(.+\))?: .{1,72}$"

if ! echo "$commit_msg" | head -1 | grep -qE "$pattern"; then
    echo "❌ Invalid commit message format."
    echo "Expected: <type>(<scope>): <subject>"
    echo "Example:  feat(auth): add OAuth2 login"
    echo ""
    echo "Valid types: feat, fix, docs, style, refactor, test, chore, perf, ci"
    exit 1
fi
EOF

chmod +x .git/hooks/commit-msg
```

### Sharing Hooks with the Team

Hooks in `.git/hooks/` are not tracked by Git. To share them:

**Option 1: Use a hooks directory in the repo**

```bash
mkdir .githooks
# Create hooks in .githooks/
git config core.hooksPath .githooks
```

**Option 2: Use Husky (Node.js projects)**

```bash
npm install --save-dev husky
npx husky init

# Create a pre-commit hook
echo "npm run lint && npm test" > .husky/pre-commit
```

### Bypassing Hooks

```bash
git commit --no-verify -m "WIP: skip hooks for now"
# or
git commit -n -m "WIP: skip hooks for now"
```

---

## 7.6 Worktrees — `git worktree`

### What Worktrees Are

Worktrees let you check out multiple branches simultaneously in separate directories, all sharing the same `.git` repository. No need to stash or commit before switching context.

### Add a Worktree

```bash
git worktree add ../hotfix-branch hotfix/critical-fix
```

**What this does:** Creates a new directory `../hotfix-branch` with the `hotfix/critical-fix` branch checked out.

**Output:**
```
Preparing worktree (checking out 'hotfix/critical-fix')
HEAD is now at 3a4b5c6 fix: handle null pointer
```

### List Worktrees

```bash
git worktree list
```

**Output:**
```
/home/jane/project           3a4b5c6 [main]
/home/jane/hotfix-branch     7d8e9f0 [hotfix/critical-fix]
```

### Remove a Worktree

```bash
git worktree remove ../hotfix-branch
```

### Industry Example: Working on a Hotfix Without Disrupting Feature Work

```bash
# You're deep in feature work with many uncommitted changes
# A critical bug needs immediate attention

# Create a worktree for the hotfix (no need to stash!)
git worktree add ../hotfix hotfix/payment-fix main

# Work on the hotfix in the other directory
cd ../hotfix
# ... fix the bug ...
git add . && git commit -m "fix(payment): prevent double charge"
git push origin hotfix/payment-fix

# Go back to your feature work (everything is exactly as you left it)
cd ../project

# Clean up when done
git worktree remove ../hotfix
```

---

## 7.7 Advanced Configuration

### Aliases

```bash
# Short commands
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# Useful compound aliases
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "restore --staged"
git config --global alias.undo "reset HEAD~1 --mixed"
git config --global alias.amend "commit --amend --no-edit"
```

**Usage:**

```bash
git lg
# Same as: git log --oneline --graph --all --decorate

git last
# Shows the last commit with file stats

git unstage src/app.js
# Same as: git restore --staged src/app.js
```

### Conditional Configuration (Per-Directory)

In `~/.gitconfig`:

```ini
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work

[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal
```

In `~/.gitconfig-work`:

```ini
[user]
    name = Jane Smith
    email = jane@company.com
```

In `~/.gitconfig-personal`:

```ini
[user]
    name = Jane
    email = jane@personal.com
```

**What this does:** Automatically uses your work email for repos in `~/work/` and personal email for repos in `~/personal/`.

---

# MODULE 8: Collaboration Workflows

## 8.1 GitFlow Workflow

GitFlow is a branching model designed for projects with scheduled releases. It defines specific branch types and their purposes.

### Branch Structure

```
main (production)     ─── v1.0 ──────────────── v1.1 ──────── v2.0 ───
                           │                      │              │
hotfix                     │              hotfix/fix-x           │
                           │                 │    │              │
release                    │         release/1.1──┘              │
                           │            │                        │
develop               ─────┴────────────┴────────────────────────┴───
                              │              │           │
feature                  feature/a      feature/b   feature/c
```

### Branch Types

| Branch | Purpose | Created From | Merges Into |
|--------|---------|-------------|-------------|
| `main` | Production-ready code | — | — |
| `develop` | Integration branch for features | `main` | `release`, `main` |
| `feature/*` | New features | `develop` | `develop` |
| `release/*` | Prepare a release | `develop` | `main` and `develop` |
| `hotfix/*` | Emergency production fixes | `main` | `main` and `develop` |

### Complete GitFlow Example

```bash
# === SETUP ===
git init -b main
# ... initial commit ...
git checkout -b develop main

# === FEATURE DEVELOPMENT ===
# Developer starts a feature
git checkout -b feature/user-dashboard develop

# ... work on the feature ...
git add .
git commit -m "feat(dashboard): add user activity chart"
git commit -m "feat(dashboard): add export to CSV"

# Feature complete — merge back to develop
git checkout develop
git merge --no-ff feature/user-dashboard -m "Merge feature/user-dashboard"
git branch -d feature/user-dashboard

# === RELEASE PREPARATION ===
# When develop has enough features for a release
git checkout -b release/1.1.0 develop

# Only bug fixes and release prep (version bumps, changelog)
git commit -m "chore: bump version to 1.1.0"
git commit -m "docs: update changelog for 1.1.0"

# Release is ready — merge to main AND develop
git checkout main
git merge --no-ff release/1.1.0 -m "Release 1.1.0"
git tag -a v1.1.0 -m "Version 1.1.0"

git checkout develop
git merge --no-ff release/1.1.0 -m "Merge release/1.1.0 back to develop"
git branch -d release/1.1.0

# Push everything
git push origin main develop --tags

# === HOTFIX ===
# Critical bug in production!
git checkout -b hotfix/payment-crash main

# ... fix the bug ...
git commit -m "fix(payment): handle null payment method"

# Merge to main AND develop
git checkout main
git merge --no-ff hotfix/payment-crash -m "Hotfix: payment crash"
git tag -a v1.1.1 -m "Hotfix 1.1.1"

git checkout develop
git merge --no-ff hotfix/payment-crash -m "Merge hotfix to develop"
git branch -d hotfix/payment-crash

git push origin main develop --tags
```

### When to Use GitFlow

- Projects with scheduled releases (mobile apps, enterprise software)
- Teams that need to maintain multiple versions simultaneously
- Projects where production stability is paramount

### When NOT to Use GitFlow

- Continuous deployment environments (web apps deployed multiple times per day)
- Small teams or solo projects
- Projects where the overhead of multiple long-lived branches isn't justified

---

## 8.2 Trunk-Based Development

Trunk-based development uses a single main branch (`main` or `trunk`) with short-lived feature branches. Changes are integrated frequently — often multiple times per day.

### Branch Structure

```
main    ── A ── B ── C ── D ── E ── F ── G ── H ── I ──
               │    │         │    │              │
               └─f1─┘         └─f2─┘              └─f3─┘
           (feature 1)    (feature 2)         (feature 3)
           ~1-2 days       ~1 day              ~hours
```

### Rules

1. Feature branches live for **1-2 days maximum**
2. Merge to `main` frequently (at least daily)
3. `main` is always deployable
4. Use **feature flags** for incomplete features
5. No long-lived branches

### Example

```bash
# 1. Start from latest main
git switch main
git pull origin main

# 2. Create a short-lived feature branch
git switch -c add-search-filter

# 3. Make small, focused changes
git add src/search/filters.js
git commit -m "feat(search): add price range filter"

# 4. Push and create PR immediately
git push -u origin add-search-filter
# Create PR via GitHub/GitLab

# 5. After code review (same day), merge to main
# (Usually done via the PR UI with squash merge)

# 6. Clean up
git switch main
git pull origin main
git branch -d add-search-filter
```

### Feature Flags Example

```javascript
// Feature is merged to main but hidden behind a flag
const features = {
  newCheckout: process.env.FEATURE_NEW_CHECKOUT === 'true',
};

app.get('/checkout', (req, res) => {
  if (features.newCheckout) {
    return newCheckoutFlow(req, res);  // New code (incomplete)
  }
  return legacyCheckoutFlow(req, res); // Existing code (stable)
});
```

### When to Use Trunk-Based Development

- Continuous deployment environments
- Teams practicing CI/CD
- Web applications and SaaS products
- Companies like Google, Facebook, Netflix

---

## 8.3 Forking Workflow

Used primarily in open-source projects. Contributors don't have write access to the main repository. They fork (copy) it, make changes, and submit pull requests.

### Complete Forking Workflow

```bash
# 1. Fork the repository on GitHub (via web UI)
#    This creates: github.com/YOUR-USERNAME/project

# 2. Clone YOUR fork
git clone git@github.com:YOUR-USERNAME/project.git
cd project

# 3. Add the original repo as "upstream"
git remote add upstream git@github.com:ORIGINAL-OWNER/project.git

# 4. Verify remotes
git remote -v
# origin    git@github.com:YOUR-USERNAME/project.git (fetch)
# origin    git@github.com:YOUR-USERNAME/project.git (push)
# upstream  git@github.com:ORIGINAL-OWNER/project.git (fetch)
# upstream  git@github.com:ORIGINAL-OWNER/project.git (push)

# 5. Create a feature branch (NEVER work directly on main)
git switch -c fix/typo-in-readme

# 6. Make changes
git add README.md
git commit -m "docs: fix typo in installation instructions"

# 7. Sync with upstream before pushing
git fetch upstream
git rebase upstream/main

# 8. Push to YOUR fork
git push origin fix/typo-in-readme

# 9. Create Pull Request (via GitHub web UI)
#    From: YOUR-USERNAME/project:fix/typo-in-readme
#    To:   ORIGINAL-OWNER/project:main

# 10. After PR is merged, sync your fork
git switch main
git fetch upstream
git rebase upstream/main
git push origin main

# 11. Delete the feature branch
git branch -d fix/typo-in-readme
git push origin --delete fix/typo-in-readme
```

---

## 8.4 Pull Requests (PRs) / Merge Requests (MRs)

### What They Are

A Pull Request (GitHub, Bitbucket) or Merge Request (GitLab) is a formal request to merge changes from one branch into another. It provides:

- Code review interface
- Discussion threads
- CI/CD integration
- Approval workflows

### Creating a PR via GitHub CLI

```bash
# Install GitHub CLI
# https://cli.github.com/

# Create a PR
gh pr create --title "feat(auth): add OAuth2 login" \
  --body "Adds Google and GitHub OAuth2 login support.

## Changes
- Add OAuth2 strategy configuration
- Add callback route handlers
- Add user linking for existing accounts

## Testing
- Unit tests added for all OAuth flows
- Manual testing with Google and GitHub

Closes #123" \
  --base main \
  --head feature/oauth2-login

# List open PRs
gh pr list

# View a specific PR
gh pr view 42

# Check out a PR locally
gh pr checkout 42

# Merge a PR
gh pr merge 42 --squash --delete-branch
```

### PR Merge Strategies

| Strategy | Command | Result | When to Use |
|----------|---------|--------|-------------|
| **Merge commit** | `--merge` | Preserves all commits + merge commit | Full history needed |
| **Squash merge** | `--squash` | All commits combined into one | Clean main history |
| **Rebase merge** | `--rebase` | Commits replayed on top of base | Linear history, no merge commits |

**Squash merge example:**

```
Before (feature branch has 5 commits):
main:    A ── B ── C
                    \
feature:             D ── E ── F ── G ── H

After squash merge:
main:    A ── B ── C ── DEFGH  (single commit with all changes)
```

### Industry PR Best Practices

1. **Keep PRs small** — Under 400 lines of changes. Large PRs get rubber-stamped.
2. **One concern per PR** — Don't mix features with refactoring.
3. **Write descriptive titles** — `feat(auth): add OAuth2 login` not `Update auth`.
4. **Include context in the description** — Why, not just what.
5. **Add screenshots for UI changes**.
6. **Link to tickets/issues** — `Closes #123` or `Fixes JIRA-456`.
7. **Respond to review comments promptly**.
8. **Don't force-push after review has started** — unless the reviewer asks for a rebase.

---

## 8.5 Code Review with Git

### Reviewing a PR Locally

```bash
# Fetch the PR branch
git fetch origin pull/42/head:pr-42
git switch pr-42

# Or using GitHub CLI
gh pr checkout 42

# Review the changes
git log --oneline main..pr-42
git diff main..pr-42
git diff main..pr-42 --stat
```

### Suggesting Changes During Review

```bash
# Check out the PR branch
gh pr checkout 42

# Make suggested changes
# ... edit files ...

# Commit with a clear message
git add .
git commit -m "review: address feedback - extract validation logic"
git push
```

---

## 8.6 Industry Example: Complete Team Workflow

A team of 5 developers working on an e-commerce platform:

```bash
# === DEVELOPER 1: Starting a feature ===
git switch main && git pull
git switch -c feature/SHOP-101-product-search
# ... develop for 1-2 days ...
git push -u origin feature/SHOP-101-product-search
# Create PR, request review from Developer 2

# === DEVELOPER 2: Reviewing the PR ===
gh pr checkout 15
npm test
# ... review code, leave comments ...
gh pr review 15 --approve

# === DEVELOPER 1: Merging after approval ===
gh pr merge 15 --squash --delete-branch

# === DEVELOPER 3: Hotfix needed ===
git switch main && git pull
git switch -c hotfix/SHOP-105-cart-total-bug
# ... fix the bug ...
git push -u origin hotfix/SHOP-105-cart-total-bug
# Create PR with "urgent" label
# After expedited review:
gh pr merge 16 --merge --delete-branch

# === RELEASE MANAGER: Tagging a release ===
git switch main && git pull
git tag -a v2.3.0 -m "Release 2.3.0: product search, cart fix"
git push origin v2.3.0
# CI/CD pipeline deploys to production
```

---

# MODULE 9: Common Errors and Troubleshooting

## 9.1 Authentication and Connection Errors

### Error: `Permission denied (publickey)`

```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Cause:** SSH key is not set up or not added to your GitHub/GitLab account.

**Fix:**

```bash
# 1. Check if you have an SSH key
ls -la ~/.ssh/

# 2. If no key exists, generate one
ssh-keygen -t ed25519 -C "your.email@company.com"

# 3. Start the SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 4. Copy the public key
cat ~/.ssh/id_ed25519.pub
# Copy the output and add it to GitHub: Settings → SSH Keys

# 5. Test the connection
ssh -T git@github.com
# Output: Hi username! You've successfully authenticated...
```

### Error: `remote: Invalid username or password`

```
remote: Invalid username or password.
fatal: Authentication failed for 'https://github.com/...'
```

**Cause:** HTTPS credentials are wrong or expired. GitHub no longer accepts passwords — you need a Personal Access Token (PAT).

**Fix:**

```bash
# 1. Generate a PAT on GitHub: Settings → Developer Settings → Personal Access Tokens

# 2. Update stored credentials
git config --global credential.helper store
# Next time you push, enter your username and PAT as the password

# Or switch to SSH
git remote set-url origin git@github.com:username/repo.git
```

### Error: `Could not resolve host: github.com`

```
fatal: unable to access 'https://github.com/...': Could not resolve host: github.com
```

**Cause:** DNS resolution failure or no internet connection.

**Fix:**

```bash
# 1. Check internet connection
ping github.com

# 2. Check DNS
nslookup github.com

# 3. Try using a different DNS
# Add to /etc/resolv.conf: nameserver 8.8.8.8

# 4. If behind a proxy
git config --global http.proxy http://proxy.company.com:8080
```

---

## 9.2 Push and Pull Errors

### Error: `rejected — non-fast-forward`

```
! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'origin'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart.
```

**Cause:** The remote branch has commits that you don't have locally. Someone pushed before you.

**Fix:**

```bash
# Option 1: Pull and merge
git pull origin main
# Resolve any conflicts, then push
git push origin main

# Option 2: Pull with rebase (cleaner)
git pull --rebase origin main
git push origin main
```

### Error: `rejected — fetch first`

```
! [rejected]        main -> main (fetch first)
```

**Cause:** Same as above — remote has diverged.

**Fix:** Same as above — `git pull` or `git pull --rebase` first.

### Error: `failed to push — remote contains work you do not have locally`

```
error: failed to push some refs to 'origin'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally.
```

**Fix:**

```bash
git fetch origin
git rebase origin/main
# or
git merge origin/main
git push origin main
```

### Error: `refusing to merge unrelated histories`

```
fatal: refusing to merge unrelated histories
```

**Cause:** You're trying to merge two repositories that don't share a common ancestor. Common when you created a repo on GitHub with a README and then try to push a local repo.

**Fix:**

```bash
git pull origin main --allow-unrelated-histories
# Resolve any conflicts
git push origin main
```

---

## 9.3 Merge and Rebase Errors

### Error: `CONFLICT (content): Merge conflict in <file>`

```
Auto-merging src/app.js
CONFLICT (content): Merge conflict in src/app.js
Automatic merge failed; fix conflicts and then commit the result.
```

**Fix:**

```bash
# 1. See which files have conflicts
git status

# 2. Open conflicted files and resolve (remove <<<, ===, >>> markers)

# 3. Stage resolved files
git add src/app.js

# 4. Complete the merge
git commit

# Or abort the merge entirely
git merge --abort
```

### Error: `You have unstaged changes — cannot rebase`

```
error: cannot rebase: You have unstaged changes.
error: Please commit or stash them.
```

**Fix:**

```bash
# Option 1: Stash changes
git stash
git rebase main
git stash pop

# Option 2: Commit changes first
git add . && git commit -m "WIP: save progress"
git rebase main
```

### Error: `rebase in progress; cannot merge`

```
error: rebase in progress; cannot merge
```

**Cause:** A previous rebase was interrupted and not completed.

**Fix:**

```bash
# Check status
git status
# rebase in progress; onto 3a4b5c6

# Option 1: Continue the rebase
git add .  # stage resolved conflicts
git rebase --continue

# Option 2: Abort the rebase
git rebase --abort

# Option 3: Skip the current commit
git rebase --skip
```

---

## 9.4 Commit Errors

### Error: `Please tell me who you are`

```
*** Please tell me who you are.
Run
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
```

**Fix:**

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"
```

### Error: `nothing to commit, working tree clean`

```
On branch main
nothing to commit, working tree clean
```

**Cause:** You haven't made any changes, or you forgot to `git add`.

**Fix:**

```bash
# Check if you have unstaged changes
git status

# If files are modified but not staged
git add <file>
git commit -m "your message"
```

### Error: `pathspec '<file>' did not match any files`

```
error: pathspec 'src/app.js' did not match any files
```

**Cause:** The file doesn't exist, or you have a typo in the path.

**Fix:**

```bash
# Check the actual filename
ls src/
# Maybe it's src/App.js (capital A) on a case-sensitive filesystem

git add src/App.js
```

---

## 9.5 Branch Errors

### Error: `branch '<name>' already exists`

```
fatal: a branch named 'feature/login' already exists
```

**Fix:**

```bash
# Switch to the existing branch
git switch feature/login

# Or delete it and recreate
git branch -D feature/login
git switch -c feature/login
```

### Error: `cannot delete branch — checked out`

```
error: Cannot delete branch 'feature/login' checked out at '/home/jane/project'
```

**Cause:** You're trying to delete the branch you're currently on.

**Fix:**

```bash
git switch main
git branch -d feature/login
```

### Error: `branch not fully merged`

```
error: The branch 'feature/experiment' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/experiment'.
```

**Cause:** The branch has commits that haven't been merged into the current branch.

**Fix:**

```bash
# If you want to keep the changes, merge first
git merge feature/experiment
git branch -d feature/experiment

# If you want to discard the changes
git branch -D feature/experiment
```

---

## 9.6 Detached HEAD

### Warning: `You are in 'detached HEAD' state`

```
You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.
```

**Cause:** You checked out a specific commit, tag, or remote branch directly.

**Fix:**

```bash
# If you just want to look around, switch back to a branch
git switch main

# If you made commits in detached HEAD and want to keep them
git switch -c save-my-work
```

### Recovering Commits Made in Detached HEAD

```bash
# You made commits in detached HEAD and then switched to a branch
# The commits seem "lost"

# Find them in the reflog
git reflog
# abc1234 HEAD@{2}: commit: important work done in detached HEAD

# Create a branch at that commit
git branch recovered-work abc1234
```

---

## 9.7 Large File and Performance Issues

### Error: `file too large` or `this exceeds GitHub's file size limit`

```
remote: error: File large-data.csv is 150.00 MB; this exceeds GitHub's file size limit of 100.00 MB
```

**Fix:**

```bash
# 1. Remove the file from the commit
git rm --cached large-data.csv
echo "large-data.csv" >> .gitignore
git add .gitignore
git commit -m "chore: remove large file, add to gitignore"

# 2. If the file is in older commits, rewrite history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch large-data.csv' \
  --prune-empty --tag-name-filter cat -- --all

# 3. For large files you need to track, use Git LFS
git lfs install
git lfs track "*.csv"
git add .gitattributes
git add large-data.csv
git commit -m "chore: track large CSV with Git LFS"
```

### Slow `git status` or `git diff`

**Fix:**

```bash
# Enable filesystem monitor (Git 2.37+)
git config core.fsmonitor true
git config core.untrackedcache true

# For very large repos, enable sparse checkout
git sparse-checkout init --cone
git sparse-checkout set src/ tests/
```

---

## 9.8 Undoing Mistakes — Quick Reference

### "I committed to the wrong branch"

```bash
# 1. Note the commit hash
git log --oneline -1
# abc1234 feat: my changes

# 2. Undo the commit (keep changes)
git reset --soft HEAD~1

# 3. Stash the changes
git stash

# 4. Switch to the correct branch
git switch correct-branch

# 5. Apply the changes
git stash pop
git add . && git commit -m "feat: my changes"
```

### "I need to undo a pushed commit"

```bash
# Create a revert commit (safe for shared branches)
git revert abc1234
git push origin main
```

### "I accidentally deleted a file"

```bash
# If not committed yet
git restore deleted-file.js

# If committed
git checkout HEAD~1 -- deleted-file.js
```

### "I want to completely start over"

```bash
# Reset to match the remote exactly
git fetch origin
git reset --hard origin/main
git clean -fd
```

### "My repo is in a weird state and nothing works"

```bash
# Nuclear option: save your changes and re-clone
cp -r . ../backup-project
cd ..
git clone <url> fresh-project
# Manually copy your changes from backup-project to fresh-project
```

---

## 9.9 Useful Diagnostic Commands

```bash
# Check Git version
git --version

# Verify repository integrity
git fsck

# Show all configuration and where it comes from
git config --list --show-origin

# Check why a file is ignored
git check-ignore -v <file>

# Show the current HEAD
git rev-parse HEAD

# Show which remote branch you're tracking
git branch -vv

# Check if a branch contains a specific commit
git branch --contains abc1234

# Show the merge base of two branches
git merge-base main feature/x

# Verify objects in the database
git fsck --full

# Garbage collect (clean up unnecessary files)
git gc

# Show repository size
git count-objects -vH
```

**Output of `git count-objects -vH`:**
```
count: 0
size: 0 bytes
in-pack: 23456
packs: 1
size-pack: 45.67 MiB
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```

---

# Quick Reference Card

## Most-Used Commands

| Command | Purpose |
|---------|---------|
| `git init` | Create a new repository |
| `git clone <url>` | Copy a remote repository |
| `git status` | Check working directory state |
| `git add <file>` | Stage changes |
| `git commit -m "msg"` | Create a commit |
| `git push origin <branch>` | Upload to remote |
| `git pull origin <branch>` | Download and merge from remote |
| `git switch -c <branch>` | Create and switch to a branch |
| `git merge <branch>` | Merge a branch into current |
| `git log --oneline` | View commit history |
| `git diff` | View unstaged changes |
| `git stash` | Temporarily save changes |
| `git restore <file>` | Discard working directory changes |
| `git revert <commit>` | Undo a commit safely |
| `git reset --hard HEAD~1` | Discard the last commit |
| `git rebase -i HEAD~N` | Interactively edit last N commits |
| `git cherry-pick <commit>` | Apply a specific commit |
| `git reflog` | View HEAD movement history |
| `git tag -a v1.0 -m "msg"` | Create an annotated tag |

## Git Aliases to Set Up Immediately

```bash
git config --global alias.s "status -s"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.co "checkout"
git config --global alias.br "branch -vv"
git config --global alias.unstage "restore --staged"
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.wip "commit -am 'WIP'"
```

---

## Lecture 1 Topics (From Transcript)

### 1. DevOps Context: Continuous Development
- How release plans are broken down into epics, stories, and tasks.
- Why coding includes programs, scripts, configuration files, and documentation.
- Need for team-wide coordination when many people edit many files.

### 2. Version Control System (VCS) Basics
- VCS as a common place to store and track text-based project files.
- Core benefits:
  - Single source of truth.
  - Change history (`who`, `what`, `when`, `why`).
  - Access control and collaboration.
- Focus area: text files in software delivery (source, scripts, config, docs).

### 3. Centralized VCS Terminology
- `Server`: machine hosting repositories.
- `Repository`: project storage area (like product-specific folder/account).
- `Workspace`: local folder where users work.
- `Checkout`: copy files from repository to workspace.
- `Check-in`: send changed files back to repository.
- `Version`: tracked change record created for each check-in.

### 4. Why Git Became Popular in DevOps
- Faster local operations.
- Better support for non-linear development.
- Distributed model enables flexible sharing.
- Lightweight setup and easier maintenance for mixed roles (dev, QA, ops, support).

### 5. Centralized vs Distributed Model
- Centralized model pain points:
  - Network latency for checkout/check-in.
  - Dependency on central server availability.
  - Hard to keep private experimental work.
  - Slower developer-to-developer sharing.
- Git distributed model:
  - Every user has a local repository copy in their workspace.
  - Most operations are local and fast.
  - Users can share changes with central repo or directly with other repos.

### 6. Local and Remote Repositories
- `Local repository`: used to modify, commit, and experiment safely.
- `Central/remote repository`: shared source for team collaboration.
- Typical workflow:
  1. Clone from central.
  2. Work locally (checkout/edit/stage/commit).
  3. Share to central when ready.

### 7. Git Internal Working Areas
- `Working Directory`: actual files you edit.
- `Staging Area (Index)`: selected changes prepared for commit.
- `Repository (.git)`: committed history and metadata.

### 8. File Lifecycle in Git
- `Untracked` -> `Modified` -> `Staged` -> `Committed`.
- For tracked files: `Unmodified` <-> `Modified` -> `Staged` -> `Committed`.

### 9. Commit Concepts from the Session
- Check-in in Git is called a `commit`.
- Each commit has:
  - Unique commit ID (SHA-based hash, commonly shown as 40 hex chars).
  - Metadata (author, time, message, changed content).
- Git stores data as snapshots/objects and reconstructs file states from commit history.

### 10. Git vs GitHub/GitLab/Bitbucket
- `Git`: client-side version control tool for local work.
- `GitHub/GitLab/Bitbucket`: platforms to host/manage central Git repositories.
- In organizations, central repository management includes permissions, backup, governance, and collaboration controls.

### 11. Role Perspective in DevOps
- Individual contributor: use Git locally for day-to-day development.
- DevOps/platform responsibility: manage central repositories and policies for teams.

---

## Lecture 2 Topics (From Transcript)

### 1. Recap and Positioning
- Git workflow recap:
  - Local repository for day-to-day commits.
  - Central repository for team sharing.
- Two tool layers:
  - `git` client for local work.
  - Central repository managers (`GitHub`, `GitLab`, `Bitbucket`, `Gerrit`) for shared hosting/governance.

### 2. Source Code vs Production Artifact
- Central repository stores source text files (code, scripts, configs), not deployable runtime binaries.
- Production deployment uses build outputs (for example: `jar`, `war`, `dll`) generated by build systems.
- Release flow highlighted:
  1. Source from VCS.
  2. Build/compile/package.
  3. Deploy to QA/stages.
  4. Promote to production.

### 3. Practice Setup Using GitHub
- Create a repository on `github.com` (public/private based on need).
- Note repository URL/path; this is the source for clone operations.
- For local machine:
  - Install Git.
  - Verify with `git --version`.
  - Use Git Bash on Windows for Linux-like shell commands.

### 4. Initial Git Configuration
- One-time global setup per machine/user:
  - `git config --global user.name "<Your Name>"`
  - `git config --global user.email "<your.email@company.com>"`
  - `git config --global push.default simple`
- Purpose:
  - Author metadata for commits.
  - Default push behavior for streamlined workflow.

### 5. Clone: Creating a Local Workspace
- `git clone <central-repo-url>` creates a workspace folder and local repository.
- If destination is not specified, folder name defaults to repository name.
- Optional custom destination:
  - `git clone <central-repo-url> workspace00`
- Empty remote repository -> empty working tree after clone.

### 6. Core Local Workflow (User Workflow)
- Create/modify files in working directory.
- Inspect state:
  - `git status`
- Stage changes:
  - `git add <file>`
  - `git add .`
- Commit staged snapshot:
  - `git commit -m "<meaningful message>"`
- Inspect history:
  - `git log`
  - `git log -n 1`
  - `git log --oneline`
  - `git show <commit-id>`

### 7. File States Reinforced
- New file is `untracked` until staged/committed.
- After commit, file becomes tracked.
- Further edits on tracked file appear as `modified`.
- `git add` moves modified/untracked file changes to staging area.
- `git status` messages indicate whether files are staged, modified, or clean.

### 8. Staging and Commit Behavior
- Commit is a two-step flow:
  1. Stage snapshot (`git add`).
  2. Persist snapshot as commit (`git commit`).
- One commit can include multiple file changes.
- Commit message should map to work intent (task/story/ticket), not vague text.

### 9. .git Folder and Metadata
- Local repository lives under hidden `.git` folder.
- `.git` contains metadata, commit objects, and config references.
- Do not manually edit or delete `.git`; deleting it removes repository history in that workspace.

### 10. Push to Central Repository
- `git push` shares local commits not yet present in central repository.
- Push is incremental: only missing commits are transferred.
- Re-running push without new local commits returns up-to-date behavior.
- With `push.default simple`, default push target is streamlined for normal workflow.

### 11. Pull from Central Repository
- `git pull` updates local repository with commits present in central but missing locally.
- Pull is also incremental.
- Typical team rhythm:
  1. Pull latest.
  2. Modify.
  3. Add + commit.
  4. Push.

### 12. Multi-Workspace / Multi-User Illustration
- Multiple clones (for example `workspace00`, `workspace01`) can exist.
- New commits in one workspace do not appear in another workspace until:
  - first workspace pushes, and
  - second workspace pulls.
- This demonstrates local independence + centralized synchronization.

### 13. Notes and Clarifications from Q&A
- Git tracks files; empty directories are not tracked.
- Same workflow applies on Linux servers/VMs/cloud instances after installing Git.
- Global `user.name`/`user.email` are commit metadata settings, not centralized account/user provisioning.
- Branching terminology (for example `master/main`) was introduced as upcoming topic for next lecture.

---

*End of Course*
