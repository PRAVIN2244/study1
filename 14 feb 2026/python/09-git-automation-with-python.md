# Module 9 — Git Automation with Python

Git is the foundation of modern software delivery. Every DevOps workflow starts with code in a Git repository. Automating Git operations — cloning repos, checking branches, analyzing commits, enforcing policies — saves time and reduces human error.

This module covers two approaches: using the `GitPython` library for local Git operations, and using the GitHub API for remote operations.

---

## Prerequisites

```bash
pip install gitpython requests
```

```python
import git
print(git.__version__)
```

**Output:**

```
3.1.40
```

---

## GitPython — Working with Local Repositories

### Cloning a Repository

```python
import git

repo = git.Repo.clone_from(
    "https://github.com/octocat/Hello-World.git",
    "hello-world"
)

print(f"Cloned to: {repo.working_dir}")
print(f"Active branch: {repo.active_branch}")
```

**Output:**

```
Cloned to: /home/user/hello-world
Active branch: master
```

**What this does:** Downloads the entire repository to a local folder called `hello-world` and returns a `Repo` object you can use to inspect and manipulate it.

### Opening an Existing Repository

```python
import git

repo = git.Repo(".")    # Current directory

print(f"Active branch: {repo.active_branch}")
print(f"Is dirty: {repo.is_dirty()}")
print(f"Untracked files: {repo.untracked_files}")
```

**Output (example):**

```
Active branch: main
Is dirty: True
Untracked files: ['notes.txt', 'temp.py']
```

**What each method returns:**

- `repo.active_branch` — the currently checked-out branch
- `repo.is_dirty()` — `True` if there are uncommitted changes
- `repo.untracked_files` — list of files not tracked by Git

### Listing Branches

```python
import git

repo = git.Repo(".")

print("Local branches:")
for branch in repo.branches:
    marker = "*" if branch == repo.active_branch else " "
    print(f"  {marker} {branch.name}")

print("\nRemote branches:")
for ref in repo.remote().refs:
    print(f"    {ref.name}")
```

**Output (example):**

```
Local branches:
  * main
    feature/login
    bugfix/header

Remote branches:
    origin/main
    origin/feature/login
    origin/develop
```

### Viewing Commit History

```python
import git

repo = git.Repo(".")

print("Last 5 commits:")
for commit in list(repo.iter_commits("main", max_count=5)):
    short_sha = commit.hexsha[:7]
    author = commit.author.name
    date = commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
    message = commit.message.strip().split("\n")[0]    # First line only
    print(f"  {short_sha} | {date} | {author} | {message}")
```

**Output (example):**

```
Last 5 commits:
  a1b2c3d | 2024-01-15 14:30 | Alice | Fix login redirect bug
  e4f5g6h | 2024-01-15 10:15 | Bob | Add user profile page
  i7j8k9l | 2024-01-14 16:45 | Alice | Update dependencies
  m0n1o2p | 2024-01-14 09:00 | Charlie | Initial project setup
  q3r4s5t | 2024-01-13 17:30 | Bob | Add README
```

**How `iter_commits` works:** It returns commit objects in reverse chronological order (newest first). Each commit has attributes like `hexsha` (full hash), `author`, `committed_datetime`, and `message`.

### Checking What Changed

```python
import git

repo = git.Repo(".")

# Show uncommitted changes (like 'git diff')
if repo.is_dirty():
    diff = repo.index.diff(None)    # Changes not yet staged
    print("Modified files:")
    for d in diff:
        print(f"  {d.change_type}: {d.a_path}")
    
    staged = repo.index.diff("HEAD")    # Staged changes
    print("\nStaged files:")
    for d in staged:
        print(f"  {d.change_type}: {d.a_path}")
```

**Output (example):**

```
Modified files:
  M: src/config.py
  M: tests/test_auth.py

Staged files:
  A: src/new_feature.py
```

**Change types:** `M` = modified, `A` = added, `D` = deleted, `R` = renamed.

### Making Commits Programmatically

```python
import git
from pathlib import Path

repo = git.Repo(".")

# Create a file
Path("automated_change.txt").write_text("This was created by Python\n")

# Stage the file
repo.index.add(["automated_change.txt"])

# Commit
repo.index.commit("Add automated change file")

print(f"Latest commit: {repo.head.commit.hexsha[:7]}")
print(f"Message: {repo.head.commit.message.strip()}")
```

**Output:**

```
Latest commit: f8a9b0c
Message: Add automated change file
```

### Pulling and Pushing

```python
import git

repo = git.Repo(".")
origin = repo.remote("origin")

# Pull latest changes
print("Pulling...")
origin.pull()
print("Pull complete.")

# Push local commits
print("Pushing...")
origin.push()
print("Push complete.")
```

> **Note:** Push requires authentication. For HTTPS, use a personal access token. For SSH, ensure your SSH key is configured.

---

## GitHub API — Remote Repository Operations

For operations on GitHub itself (creating repos, managing issues, reviewing PRs), use the GitHub REST API:

### Setting Up

```python
import requests
import os

class GitHubClient:
    """Reusable GitHub API client."""
    
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        })
        self.base_url = "https://api.github.com"
    
    def get(self, endpoint, params=None):
        """Make a GET request to the GitHub API."""
        response = self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def post(self, endpoint, data=None):
        """Make a POST request to the GitHub API."""
        response = self.session.post(
            f"{self.base_url}{endpoint}",
            json=data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
```

### Listing Repositories

```python
gh = GitHubClient()

repos = gh.get("/user/repos", params={"per_page": 10, "sort": "updated"})

print("Your recent repositories:")
for repo in repos:
    visibility = "private" if repo["private"] else "public"
    print(f"  {repo['name']} ({visibility}) - {repo['language'] or 'N/A'}")
```

**Output (example):**

```
Your recent repositories:
  my-app (private) - Python
  infrastructure (private) - HCL
  dotfiles (public) - Shell
  blog (public) - JavaScript
```

### Creating a Repository

```python
gh = GitHubClient()

new_repo = gh.post("/user/repos", data={
    "name": "automated-repo",
    "description": "Created by Python automation",
    "private": True,
    "auto_init": True    # Creates with a README
})

print(f"Created: {new_repo['html_url']}")
print(f"Clone URL: {new_repo['clone_url']}")
```

**Output:**

```
Created: https://github.com/youruser/automated-repo
Clone URL: https://github.com/youruser/automated-repo.git
```

### Managing Issues

```python
gh = GitHubClient()

# Create an issue
issue = gh.post("/repos/owner/repo/issues", data={
    "title": "Automated: Update dependencies",
    "body": "Dependencies are outdated. Please update.",
    "labels": ["automation", "maintenance"]
})

print(f"Created issue #{issue['number']}: {issue['title']}")
print(f"URL: {issue['html_url']}")
```

### Listing Pull Requests

```python
gh = GitHubClient()

prs = gh.get("/repos/owner/repo/pulls", params={"state": "open"})

print(f"Open PRs: {len(prs)}")
for pr in prs:
    print(f"  #{pr['number']}: {pr['title']} (by {pr['user']['login']})")
```

---

## Practical Example: Repository Health Checker

A script that audits a repository for common issues:

```python
import git
from pathlib import Path
from datetime import datetime, timezone

def check_repo_health(repo_path):
    """Audit a Git repository for common issues."""
    repo = git.Repo(repo_path)
    issues = []
    info = []
    
    # Check 1: Uncommitted changes
    if repo.is_dirty():
        issues.append("Uncommitted changes detected")
    else:
        info.append("Working directory is clean")
    
    # Check 2: Untracked files
    untracked = repo.untracked_files
    if untracked:
        issues.append(f"{len(untracked)} untracked file(s)")
    
    # Check 3: Branch count
    branch_count = len(list(repo.branches))
    if branch_count > 10:
        issues.append(f"Too many local branches ({branch_count})")
    info.append(f"{branch_count} local branch(es)")
    
    # Check 4: Last commit age
    last_commit = repo.head.commit
    now = datetime.now(timezone.utc)
    age = now - last_commit.committed_datetime
    if age.days > 30:
        issues.append(f"Last commit was {age.days} days ago")
    info.append(f"Last commit: {age.days} day(s) ago")
    
    # Check 5: Required files
    required_files = ["README.md", ".gitignore"]
    for filename in required_files:
        filepath = Path(repo_path) / filename
        if filepath.exists():
            info.append(f"{filename} exists")
        else:
            issues.append(f"Missing {filename}")
    
    # Print report
    print(f"\nRepository Health Report: {repo_path}")
    print("=" * 50)
    
    print("\nInfo:")
    for item in info:
        print(f"  [OK] {item}")
    
    if issues:
        print("\nIssues:")
        for issue in issues:
            print(f"  [!!] {issue}")
    else:
        print("\nNo issues found!")
    
    return len(issues) == 0

# Usage:
# healthy = check_repo_health(".")
```

**Output (example):**

```
Repository Health Report: .
==================================================

Info:
  [OK] Working directory is clean
  [OK] 3 local branch(es)
  [OK] Last commit: 2 day(s) ago
  [OK] README.md exists

Issues:
  [!!] Missing .gitignore
```

---

## Practical Example: Commit Statistics

```python
import git
from collections import Counter
from datetime import datetime, timezone, timedelta

def commit_stats(repo_path, days=30):
    """Generate commit statistics for the last N days."""
    repo = git.Repo(repo_path)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    authors = Counter()
    daily = Counter()
    total = 0
    
    for commit in repo.iter_commits("main"):
        if commit.committed_datetime < since:
            break
        
        authors[commit.author.name] += 1
        day = commit.committed_datetime.strftime("%Y-%m-%d")
        daily[day] += 1
        total += 1
    
    print(f"\nCommit Statistics (last {days} days)")
    print("=" * 40)
    print(f"Total commits: {total}")
    
    print(f"\nBy author:")
    for author, count in authors.most_common():
        bar = "#" * count
        print(f"  {author:20s} {count:3d} {bar}")
    
    print(f"\nBy day (top 5):")
    for day, count in daily.most_common(5):
        bar = "#" * count
        print(f"  {day} {count:3d} {bar}")

# Usage:
# commit_stats(".", days=30)
```

**Output (example):**

```
Commit Statistics (last 30 days)
========================================
Total commits: 47

By author:
  Alice                 22 ######################
  Bob                   15 ###############
  Charlie               10 ##########

By day (top 5):
  2024-01-15  8 ########
  2024-01-12  6 ######
  2024-01-10  5 #####
  2024-01-14  4 ####
  2024-01-08  3 ###
```

---

## Practical Example: Branch Cleanup

```python
import git

def cleanup_merged_branches(repo_path, dry_run=True):
    """Delete local branches that have been merged into main."""
    repo = git.Repo(repo_path)
    main_branch = repo.active_branch.name
    deleted = []
    
    for branch in repo.branches:
        if branch.name == main_branch:
            continue
        
        # Check if branch is merged into main
        merged_commits = list(repo.iter_commits(f"{main_branch}..{branch.name}"))
        
        if not merged_commits:
            if dry_run:
                print(f"  [DRY RUN] Would delete: {branch.name}")
            else:
                repo.delete_head(branch, force=True)
                print(f"  Deleted: {branch.name}")
            deleted.append(branch.name)
    
    if not deleted:
        print("  No merged branches to clean up.")
    else:
        print(f"\n  {'Would delete' if dry_run else 'Deleted'} {len(deleted)} branch(es)")

# Usage:
# cleanup_merged_branches(".", dry_run=True)    # Preview first
# cleanup_merged_branches(".", dry_run=False)   # Actually delete
```

---

## Exercises

**Exercise 1:** Write a script that clones a repository and prints the total number of commits, unique authors, and the date of the first and last commit.

**Exercise 2:** Write a script that checks all repositories in a directory and reports which ones have uncommitted changes.

**Exercise 3:** Using the GitHub API, write a script that lists all open issues for a repository and groups them by label.

**Exercise 4:** Write a pre-commit hook (a script that runs before each commit) that checks if any Python files have `print()` statements and warns the user.

---

## Common Mistakes

### 1. Not Handling Authentication

```python
# Bad — push fails silently or with cryptic error
origin.push()

# Good — check authentication first
try:
    origin.push()
except git.exc.GitCommandError as e:
    print(f"Push failed: {e}")
    print("Check your SSH key or access token.")
```

### 2. Hardcoding Repository Paths

```python
# Bad
repo = git.Repo("/home/alice/projects/myapp")

# Good — accept as parameter
def analyze_repo(path="."):
    repo = git.Repo(path)
```

### 3. Not Using dry_run for Destructive Operations

Always preview destructive operations (deleting branches, force-pushing) before executing them. Use a `dry_run` parameter.

### 4. Ignoring Rate Limits on GitHub API

The GitHub API has rate limits (60/hour unauthenticated, 5000/hour with token). Always authenticate and check remaining limits.

---

## Summary

| Task | GitPython | GitHub API |
|------|-----------|------------|
| Clone repo | `git.Repo.clone_from()` | N/A |
| List branches | `repo.branches` | `GET /repos/:owner/:repo/branches` |
| View commits | `repo.iter_commits()` | `GET /repos/:owner/:repo/commits` |
| Check status | `repo.is_dirty()` | N/A |
| Create repo | N/A | `POST /user/repos` |
| Manage issues | N/A | `POST /repos/:owner/:repo/issues` |
| List PRs | N/A | `GET /repos/:owner/:repo/pulls` |

---

[Previous: Module 08 — Working with APIs](08-working-with-apis.md) | [Next: Module 10 — Terraform Automation](10-terraform-automation-with-python.md)
