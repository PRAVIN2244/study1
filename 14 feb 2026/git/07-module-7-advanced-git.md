# MODULE 7: Advanced Git

## 7.1 Cherry-Picking â€” `git cherry-pick`

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
# d4e5f6a fix: resolve null pointer in user lookup  â† you need this one
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

## 7.8 Tagging as Baseline Practice

Tags are commonly used to mark QA and release baselines so teams can reference stable points without memorizing long commit hashes.

Common pattern examples:

- `qa_2026_02_20_STORY123`
- `R_1.2.0`

### Why Teams Depend on Tags

- QA can confirm exactly what was tested.
- Release management can map deployment artifacts back to source baseline.
- Incident analysis can jump directly to tagged states.

### Operational Note

One commit can have multiple tags, but a tag name should represent one specific commit reference at a time.

---

## 7.9 Transcript Command Workflow: Tag Lifecycle

### List Existing Tags

```bash
git tag
```

- Displays all tags available in your local repository.

### Create Annotated Tag on a Specific Commit

```bash
git tag -a R_1.2 -m "Release 1.2 baseline" <commit-id>
```

- Creates a named baseline pointing to that commit.
- Annotated tags store tagger/message metadata.

### Inspect Tag Details

```bash
git show R_1.2
```

- Shows tag metadata and the referenced commit details.

### Publish Tags to Remote

```bash
git push --tags
```

- Pushes local tag references to remote (subject to permissions/policy).

### Delete Local Tag Reference

```bash
git tag -d R_1.2
```

- Deletes only the local tag reference, not the commit data itself.

---

## 7.2 Recovery with Reflog â€” `git reflog`

### What It Does

The reflog (reference log) records every time HEAD moves â€” every commit, checkout, reset, merge, rebase, etc. It's your safety net for recovering "lost" commits.

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
# 9f8e7d6 HEAD@{2}: commit: your last good commit  â† this one

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

## 7.3 Tags â€” `git tag`

### What Tags Are

Tags mark specific commits as important â€” typically used for release versions. Unlike branches, tags don't move when new commits are made.

### Tag Naming Conventions

Organizations define naming standards so tags are consistent and searchable:

| Pattern | Use Case | Example |
|---------|----------|---------|
| `R_X.Y` | Release baseline | `R_1.2`, `R_2.0` |
| `vX.Y.Z` | Semantic versioning | `v1.0.0`, `v2.3.1` |
| `qa_YYYY-MM-DD` | QA build baseline | `qa_2026-02-20` |
| `qa_YYYY-MM-DD_TICKET` | QA build with ticket ref | `qa_2026-02-20_JIRA-981` |

**Key rules:**

- A commit can have **multiple tags** (e.g., both `qa_2026-02-20` and `R_1.2` on the same commit)
- A tag name must be **unique** -- you cannot reuse the same tag name for a different commit
- Tags point to **commits**, not branches

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

### List Tags with Messages

```bash
git tag -n
```

**Output:**
```
v0.1.0          Initial alpha release
v0.2.0          Add user authentication
v1.0.0          First stable release
v1.0.1          Security patch for XSS vulnerability
v1.1.0          Add payment processing
```

**What `-n` does:** Shows the first line of each tag's annotation message. Use `-n3` to show the first 3 lines.

```bash
# Version-sorted tags (newest first)
git tag -l 'v*' --sort=-v:refname
```

**Output:**
```
v1.1.0
v1.0.1
v1.0.0
v0.2.0
v0.1.0
```

**Real-life use case:** Quickly checking which releases exist and what each one contains, sorted by version number.

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


### Tags in Log Output

After creating a tag, it appears in `git log` output next to the tagged commit:

```bash
git log --oneline
```

**Output:**
```
c3a91f2 (tag: R_1.2) Fix payment calculation
a88b120 Add checkout flow
b27d111 Initial version
```

The `(tag: R_1.2)` label makes it easy to identify which commit a tag points to without running `git show`.
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

## 7.4 Submodules â€” `git submodule`

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
    echo "âŒ Linting failed. Fix errors before committing."
    exit 1
fi

echo "Running tests..."
npm test

if [ $? -ne 0 ]; then
    echo "âŒ Tests failed. Fix tests before committing."
    exit 1
fi

echo "âœ… All checks passed."
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
    echo "âŒ Invalid commit message format."
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

## 7.6 Worktrees â€” `git worktree`

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

