# MODULE 2: Repository Basics

## 2.1 Creating a Repository â€” `git init`

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


**Warning:** Never modify the `.git` folder manually. It contains the entire repository history, staging area data, and configuration. If this folder is deleted, all commit history is permanently lost.

To view hidden files including `.git`:

```bash
ls -a
```

**Output:**
```
.git  one.java  two.java
```

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

## 2.8 Practical User Workflow (Transcript-Aligned)

This is the day-to-day flow highlighted in the sessions:

```bash
git clone <repo-url>
cd <repo-folder>
git status
```

Create/modify files, then:

```bash
git add <file>        # or git add .
git commit -m "meaningful message"
git log --oneline
git show <commit-id>
```

### Key Behavioral Points

- `git status` tells whether files are untracked, modified, staged, or clean.
- `git add` does not commit; it stages a snapshot for the next commit.
- One commit can include multiple file changes.
- Commit messages should map to real work context (story/task/ticket), not vague text.

### Local First, Shared Later

- Commits are created in your **local** repository first.
- Sharing to team happens only when you push to remote (covered deeply in Module 4).

---

## 2.9 Terminology Mapping: Check-in vs Commit

In older centralized VCS language:

- **Checkout**: copy files from repository to workspace
- **Check-in**: send changes back to repository

In Git command workflow:

- `git clone` / `git checkout <branch>` support local working copy setup
- `git add` + `git commit` is the check-in-equivalent into local repository
- `git push` shares those commits to central/remote repository

This mapping helps when transitioning from SVN/TFS/ClearCase terminology to Git.

---

## 2.2 Creating a Central Repository on GitHub

Before cloning, you need a central repository to clone from. Here is how to create one on GitHub:

### Steps

1. Go to [github.com](https://github.com) and sign in (or create an account)
2. Click the **+** icon (top-right) and select **New repository**
3. Enter a repository name (e.g., `may2020`)
4. Choose **Public** or **Private**
5. Optionally add a README, `.gitignore`, or license
6. Click **Create repository**

### After Creation

GitHub provides the repository URL. This is what users need for cloning:

```
https://github.com/<username>/may2020.git
```

**Why GitHub for practice:** Free, no infrastructure setup required, and works as a central repository manager. For enterprise use, teams may use GitHub Enterprise, GitLab, Bitbucket, or Gerrit.

---


## 2.2 Cloning a Repository â€” `git clone`

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

### Cloning an Empty Repository

When you clone a newly created repository that has no commits yet:

```bash
git clone https://github.com/user/may2020.git
```

**Output:**
```
Cloning into 'may2020'...
warning: You appear to have cloned an empty repository.
done.
```

**What this means:** The repository exists on GitHub but has no commits. The workspace folder is created with a `.git` directory, but no files are present yet.

### Cloning into a Custom Directory

```bash
git clone https://github.com/expressjs/express.git my-express-fork
```

**Output:**
```
Cloning into 'my-express-fork'...
```

**What this does:** Creates a folder named `my-express-fork` instead of using the repository name. Useful when you want a different local folder name.

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

## 2.3 Checking Repository Status â€” `git status`

### Command

```bash
git status
```

**What it does:** Shows the state of the working directory and staging area â€” which files are modified, staged, or untracked.

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

**Short status with branch info:**

```bash
git status -sb
```

**Output:**
```
## main...origin/main [ahead 2]
 M index.html
?? app.js
```

**What `-sb` adds:** The first line shows the current branch, its tracking branch, and how many commits ahead/behind you are. This is the most compact and informative status view.

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
- `MM server.js` â€” Staged changes AND additional unstaged changes (you modified it after staging)
- `A  config.js` â€” New file, fully staged
- ` M utils.js` â€” Modified, not staged
- `?? temp.log` â€” Untracked

---

## 2.4 Staging Files â€” `git add`

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
- `git add .` â€” Stages changes relative to the current directory
- `git add -A` â€” Stages changes across the entire repository, regardless of where you run it

### Stage Only Modified and Deleted Files (Not New)

```bash
git add -u
# or
git add --update
```

**When to use:** When you want to stage changes to tracked files but not add new untracked files.

### Interactive Staging â€” Stage Parts of a File

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
#  M src/auth/login.js        â† feature work
#  M src/auth/session.js      â† feature work
#  M src/auth/middleware.js    â† feature work
#  M src/utils/logger.js      â† unrelated fix
#  M src/utils/validator.js   â† unrelated fix

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

## 2.5 Committing Changes â€” `git commit`

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
- `[main 3a4b5c6]` â€” Branch name and abbreviated commit hash
- `3 files changed` â€” Number of files affected
- `127 insertions(+), 4 deletions(-)` â€” Lines added and removed
- `create mode 100644` â€” A new file was created (100644 = regular file)

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

### Ticket/Sprint-Referenced Commit Messages

In teams using Agile/Scrum with tools like JIRA, commit messages often reference the ticket or sprint:

```bash
git commit -m "JIRA-102 Fix login validation bug"
git commit -m "Add timeout config for payment API"
git commit -m "Sprint 12: Add retry mechanism"
```

This helps trace which bug/feature/sprint a change belongs to when reviewing history.


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

## 2.6 Ignoring Files â€” `.gitignore`

### What It Does

The `.gitignore` file tells Git which files and directories to ignore. Ignored files won't appear in `git status` and won't be staged by `git add .`.

### Quick Example: Before and After .gitignore

**Before creating .gitignore:**

```bash
git status
```

**Output:**
```
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        app.java
        one.class
        two.class
        app.log
```

**Create .gitignore:**

```bash
echo "*.class" > .gitignore
echo "*.log" >> .gitignore
```

**After .gitignore:**

```bash
git status
```

**Output:**
```
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        app.java
```

The `.class` and `.log` files no longer appear. Git ignores them even with `git add .`.

### .gitignore Must Be Committed

`.gitignore` is a regular file in your repository. You should commit and push it so everyone who clones the repo gets the same ignore rules:

```bash
git add .gitignore
git commit -m "Add .gitignore to ignore build artifacts"
git push
```

### Can You Ignore .gitignore Itself?

No. `.gitignore` is meant to be part of the project's shared configuration. It lives in your working directory (not inside `.git/`) and should be tracked so all team members use the same ignore rules.

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

## 2.6.2 Configuring File Handling with `.gitattributes`

### What `.gitattributes` Does

`.gitattributes` lets you define per-path settings that control how Git handles files. It is committed to the repository and applies to all collaborators.

Common uses:
- Define line ending normalization rules
- Mark files as binary (prevent diff/merge on them)
- Set custom merge strategies for specific files
- Configure diff drivers for non-text files

### Syntax

```
# Pattern    attribute=value

# Normalize line endings for all text files
*           text=auto

# Force LF line endings for shell scripts
*.sh        text eol=lf

# Force CRLF for Windows batch files
*.bat       text eol=crlf

# Mark images as binary (no diff, no merge)
*.png       binary
*.jpg       binary

# Mark lock files to always use the current branch version during merge
*.lock      merge=ours

# Use a custom diff driver for CSV files
*.csv       diff=csv
```

### `.gitattributes` in Conflict Resolution

You can define custom merge strategies for specific files to avoid conflicts entirely:

```
# Always keep the current branch's version of package-lock.json during merge
package-lock.json   merge=ours

# Always keep the current branch's version of compiled assets
dist/**             merge=ours

# Binary files should never be merged textually
*.pdf               binary
*.docx              binary
```

**Setting up the `ours` merge strategy:**

```bash
# Configure the "ours" merge driver
git config --global merge.ours.driver true
```

**What this does:** When Git encounters a conflict in files matching these patterns, it automatically keeps the current branch's version instead of showing conflict markers.

**Example:**

```bash
# Create .gitattributes in the project root
echo "package-lock.json merge=ours" > .gitattributes
git add .gitattributes
git commit -m "chore: add gitattributes for merge strategy"
```

**Real-life use case:** In a Node.js project, `package-lock.json` frequently causes merge conflicts because it changes with every dependency update. By setting `merge=ours`, the team avoids these conflicts and regenerates the lock file after merge with `npm install`.

### Industry-Standard `.gitattributes`

```
# Auto-detect text files and normalize line endings
*               text=auto

# Source code
*.js            text eol=lf
*.ts            text eol=lf
*.py            text eol=lf
*.java          text eol=lf
*.go            text eol=lf
*.sh            text eol=lf
*.bat           text eol=crlf

# Documentation
*.md            text eol=lf
*.txt           text eol=lf

# Serialization
*.json          text eol=lf
*.yaml          text eol=lf
*.yml           text eol=lf
*.xml           text eol=lf

# Binary files
*.png           binary
*.jpg           binary
*.gif           binary
*.ico           binary
*.pdf           binary
*.zip           binary
*.tar.gz        binary
*.jar           binary

# Merge strategies
package-lock.json   merge=ours
yarn.lock           merge=ours
```

### Quick Recap

| Pattern | Effect |
|---------|--------|
| `* text=auto` | Auto-detect text files and normalize line endings |
| `*.sh text eol=lf` | Force LF endings for shell scripts |
| `*.png binary` | Treat PNG files as binary (no diff/merge) |
| `*.lock merge=ours` | Always keep current branch version on merge |

---

## 2.6.1 Git Tracks Files, Not Empty Folders

Git only tracks **files**, not empty directories. If you create an empty folder, `git status` will not show it.

### Example

```bash
mkdir test
git status
```

**Output:** No mention of the `test/` folder -- Git ignores it entirely.

```bash
# Create a file inside the folder
echo "test content" > test/file1.txt
git status
```

**Output:**
```
Untracked files:
  (use "git add <file>..." to include in what will be committed)
        test/
```

**Now** Git sees the folder because it contains a tracked file.

### Keeping Empty Directories in Git

If you need an empty directory in your repository (e.g., `logs/`, `uploads/`), the convention is to add a `.gitkeep` placeholder file:

```bash
mkdir logs
touch logs/.gitkeep
git add logs/.gitkeep
```

`.gitkeep` is not a Git feature -- it is a community convention. The file can be named anything; its purpose is to make the directory non-empty so Git tracks it.

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

