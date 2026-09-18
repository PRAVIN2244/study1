# MODULE 1: Git Fundamentals

## 1.1 What Is Git?

Git is a **distributed version control system (DVCS)**. It tracks changes to files over time so you can recall specific versions later. Unlike centralized systems (SVN, Perforce), every developer has a full copy of the repository history on their local machine.

### Key Properties

| Property | Meaning |
|----------|---------|
| **Distributed** | Every clone is a full repository with complete history |
| **Snapshot-based** | Git stores snapshots of the entire project, not file diffs |
| **Integrity** | Every object is checksummed with SHA-1 (40-character hex hash) |
| **Speed** | Nearly all operations are local â€” no network latency |
| **Non-linear development** | Branching and merging are first-class operations |

### Real-World Context

Companies like **Google, Microsoft, Netflix, Facebook, and Amazon** use Git as their primary version control system. The **Linux kernel** â€” one of the largest open-source projects â€” is managed with Git (Linus Torvalds created Git in 2005 specifically for kernel development).

---

## 1.7 DevOps Context for Git (Continuous Development)

In DevOps, "development" is broader than application code. Teams version-control:

- Source code
- Shell/Python/PowerShell scripts
- Configuration files
- Automation assets
- Documentation

### Why This Matters

When many people change many files in parallel, teams need:

- A common source of truth
- Full change traceability (`who`, `what`, `when`, `why`)
- Reliable collaboration rules

Git solves this using local repositories for fast, isolated work and shared remotes for collaboration.

### Git vs Repository Platforms

- **Git**: the version control engine and client commands.
- **GitHub/GitLab/Bitbucket/Gerrit**: platforms to host/manage central repositories, permissions, and workflows.

### Source Code vs Production Deliverables

Source code in Git is human-readable text. Production systems run machine-readable deliverables:

| Source (in Git) | Deliverable (built artifact) |
|----------------|------------------------------|
| `.java`, `pom.xml` | `.jar`, `.war` |
| `.cs`, `.csproj` | `.dll`, `.exe` |
| `.go` | compiled binary |
| `.ts`, `.tsx` | bundled `.js` |

The flow from code to production:

```
Central Repo (source code) --> Build System --> Deliverable --> QA --> Production
```

**Example:** Central repo has `app.java`, `pom.xml`, `config.yml`. The build system generates `payment-service.jar`. That `.jar` is what gets deployed to QA and production — not the source files.

### Git vs Build Management

GitHub/GitLab host and manage repositories. They do **not** handle:

- Building artifacts from source code
- Promoting artifacts through environments (QA, staging, production)
- Deploying to production servers

That responsibility belongs to **build management / CI-CD tools** (Jenkins, GitHub Actions, GitLab CI, etc.):

| Responsibility | Tool |
|---------------|------|
| Version control, code sharing | Git + GitHub/GitLab |
| Building artifacts from source | CI tool (Jenkins, GitHub Actions) |
| Deploying to QA/Production | CD tool / deployment pipeline |

---

## 1.8 Why VCS Is Mandatory (Lecture Framing)

### Storybook Analogy

- Product = storybook
- Files = pages/chapters
- Developers/QA = writing teams

Without version control, teams quickly lose track of:

- Which version is latest
- Who changed what
- Which change caused a break
- How dependent teams should coordinate updates

### Centralized Model Vocabulary

Classic tools (SVN/TFS/ClearCase/Perforce style) use these terms:

- **Server**: central machine that stores source files
- **Repository**: product-specific storage area
- **Client**: software used from user machine
- **Workspace**: local folder where user edits files
- **Checkout**: copy from server repo to workspace
- **Check-in**: send local edits back to server repo

Each check-in creates a tracked version event (similar to a transaction record) with:

- Author
- Changed files/lines
- Timestamp
- Purpose/message

### Why Centralized-Only Can Slow Teams

- Heavy dependence on network for checkout/check-in
- Slower collaboration for large repos or distributed teams
- Limited private experimentation without touching central repo
- Peer-to-peer sharing often still routed through central server

Git addresses these by making local operations first-class and syncing to shared remotes when needed.

---

## 1.9 Metadata Scope and Version Record (Interview Focus)

### Repository-Level vs User-Level Metadata

- Metadata is stored at **repository history** level.
- Each **version/commit** entry is created by a specific user action.

So both are true:

- Repository contains the complete metadata history.
- Each commit captures a specific user’s change event.

### What a Version Record Captures

Each commit/version tracks:

- `who` made the change (author)
- `what` changed (files/content)
- `when` it changed (timestamp)
- `why` it changed (message)

This is why commit history supports debugging, auditing, and release traceability.

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

Download from [https://git-scm.com/download/win](https://git-scm.com/download/win) and run the installer.

**Git Bash (Windows only):** The Git installer on Windows includes **Git Bash**, a terminal emulator that provides a Linux-like shell environment. This lets you use standard Unix commands (`ls`, `pwd`, `cd`, `touch`, `echo`, `cat`) on Windows, making it easier to follow tutorials and maintain consistency across operating systems.

### Verify Installation

#### Check Git Location

```bash
which git
```

**Output (Git Bash on Windows):**
```
/c/Program Files/Git/mingw64/bin/git
```

**Output (Linux/macOS):**
```
/usr/bin/git
```

**What this tells you:** The path where the Git binary is installed. If this returns nothing, Git is not in your PATH.

#### Check Git Version

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

**What this does:** Sets the author name and email that appear in every commit you make. This is **not** authentication â€” it's metadata embedded in commits.

**Why it matters:** In an industry project, commits are attributed to developers. If you don't set this, Git uses your system username and hostname, which looks unprofessional in commit logs:

```
Author: root@ip-172-31-22-45 <root@ip-172-31-22-45>   â† Bad
Author: Jane Smith <jane.smith@company.com>              â† Good
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

### Push Default Behavior (Transcript Workflow)

```bash
git config --global push.default simple
```

**What this does:** Makes default `git push` behavior safer and predictable by pushing the current branch to the branch with the same name on the default remote.

**Why it matters for this course flow:** Most examples assume branch-to-same-branch push/pull patterns (`local <branch>` <-> `remote <branch>`), which aligns with `simple`.

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
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     git add     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    git commit    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Working        â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º â”‚  Staging Area   â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º â”‚  Repository     â”‚
â”‚  Directory      â”‚                 â”‚  (Index)        â”‚                 â”‚  (.git)         â”‚
â”‚                 â”‚ â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ â”‚                 â”‚ â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ â”‚                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  git restore    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   git reset     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

| Area | What It Is | Analogy |
|------|-----------|---------|
| **Working Directory** | The actual files on your filesystem that you edit | Your desk where you work |
| **Staging Area (Index)** | A snapshot of what will go into the next commit | A box where you pack items to ship |
| **Repository (.git)** | The permanent history of all committed snapshots | The warehouse storing all shipped boxes |

### File States

```
Untracked â”€â”€â–º Staged â”€â”€â–º Committed â”€â”€â–º Modified â”€â”€â–º Staged â”€â”€â–º Committed
                                          â”‚
                                          â””â”€â”€â–º (cycle repeats)
```

| State | Meaning |
|-------|---------|
| **Untracked** | Git doesn't know about this file yet |
| **Staged** | File is marked to be included in the next commit |
| **Committed** | File is safely stored in the local repository |
| **Modified** | File has changed since the last commit but isn't staged |

### End-to-End Workflow (Including Remote)

The three local areas connect to the remote repository via `git push` and `git pull`:

```
Central Repo (GitHub/GitLab)
        ^           |
     git push    git pull
        |           v
Local Repo (.git folder)
        ^
     git commit
        |
   Staging Area
        ^
     git add
        |
Working Directory (your files)
```

This is the daily developer workflow:
1. Edit files in the working directory
2. `git add` to stage changes
3. `git commit` to save to local repository
4. `git push` to share with the team via central repository
5. `git pull` to get teammates' changes

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
commit 3a4b5c â”€â”€â–º tree 7d8e9f â”€â”€â–º blob a1b2c3  (README.md)
    â”‚                         â”€â”€â–º blob d4e5f6  (index.html)
    â”‚                         â”€â”€â–º tree 1a2b3c  (src/)
    â”‚                                   â”€â”€â–º blob 4d5e6f  (app.js)
    â”‚
    â””â”€â”€â–º parent commit 1f2e3d
```

Every object is identified by its **SHA-1 hash** â€” a 40-character hexadecimal string:

```
commit 3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b
```

This means Git has built-in integrity checking. If a single byte changes, the hash changes.

### Commits as Backup Reference Points

Every commit is a recoverable snapshot of your project. Unlike traditional backups (zip files, copies), Git commits are:

- **Identified by hash** -- you can return to any commit using its ID
- **Permanent** -- once committed, the snapshot exists in the repository history
- **Navigable** -- you can move backward and forward through commits using `git checkout`, `git reset`, or `git log`

This means "backup" in Git is not a separate action. Every `git commit` automatically creates a backup point you can return to at any time.

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

