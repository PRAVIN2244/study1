# MODULE 6: Undoing Changes

## 6.1 Overview: Choosing the Right Undo Command

| Situation | Command | Destructive? |
|-----------|---------|-------------|
| Discard unstaged changes to a file | `git restore <file>` | Yes â€” changes are lost |
| Unstage a file (keep changes in working dir) | `git restore --staged <file>` | No |
| Undo the last commit, keep changes staged | `git reset --soft HEAD~1` | No |
| Undo the last commit, keep changes unstaged | `git reset HEAD~1` (mixed) | No |
| Undo the last commit, discard all changes | `git reset --hard HEAD~1` | Yes â€” changes are lost |
| Undo a commit that's already pushed | `git revert <commit>` | No â€” creates a new commit |
| Save work temporarily | `git stash` | No |
| Remove untracked files | `git clean` | Yes â€” files are deleted |

---

## 6.8 Commit Navigation for Debugging

Sometimes you need to inspect an older commit to verify behavior:


```bash
git checkout <commit-id>
```

**Output:**
```
Note: switching to '5a8c1d2'.

You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

HEAD is now at 5a8c1d2 Initial commit
```

**What this means:** Git has moved your working directory to show the files exactly as they were at commit `5a8c1d2`. You can inspect files, run tests, or compare behavior.

This lets you view/project state at that point in history. After inspection, switch back:

```bash
git checkout <branch-name>
```

**Example:**

```bash
git checkout 5a8c1d2    # inspect old state
ls                      # see files as they were
git checkout master     # return to latest
```

**Output (on return):**
```
Switched to branch 'master'
```

### Content Still Exists Even When Not Visible

After a reset or branch switch, files may disappear from your working directory. This does not mean they are gone from Git. Commits are permanent snapshots stored in the repository. As long as a commit exists (reachable via branch, tag, or reflog), its content can be recovered.

- Switched branches and a file disappeared? It exists on the other branch.
- Used `git reset --hard`? The commit is still in the reflog for ~90 days (see `git reflog` in Module 7).
- The working directory only shows the current snapshot. The repository stores all snapshots.

### Practical Guideline

- Use this to validate when a bug was introduced or to compare old vs current behavior.
- Do not continue normal feature development in detached historical state.

---

## 6.2 Restoring Files â€” `git restore`

`git restore` (Git 2.23+) replaces the confusing dual-purpose `git checkout` for file operations.

### Discard Unstaged Changes

```bash
git restore src/app.js
```

**What it does:** Replaces the working directory version of `src/app.js` with the version from the staging area (or the last commit if nothing is staged).

**Output:** No output on success. The file is silently reverted.

**Warning:** This permanently discards your uncommitted changes. There is no undo.

### Discard All Unstaged Changes

**Older equivalent (pre-Git 2.23):**

```bash
git checkout -- src/app.js
```

This does the same thing. The `--` separates the command from the file path to avoid ambiguity with branch names.

```bash
git restore .
```

### Step-by-Step Example: Undo a Working Directory Change

```bash
# Make an unwanted edit
echo "bug" >> calc.py
git status
```

**Output:**
```
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   calc.py
```

```bash
# Discard the edit
git restore calc.py
git status
```

**Output:**
```
nothing to commit, working tree clean
```

The file is restored to its last committed version. The unwanted edit is gone.

### Unstage a File

```bash
git restore --staged src/app.js
```

**What it does:** Moves the file from the staging area back to the working directory. The changes are preserved â€” they're just no longer staged.

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

## 6.3 Resetting â€” `git reset`

`git reset` moves the branch pointer and optionally modifies the staging area and working directory.

### The Three Modes

```
                    --soft          --mixed (default)    --hard
                    â”€â”€â”€â”€â”€           â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€    â”€â”€â”€â”€â”€â”€
Repository:         Moves HEAD â†    Moves HEAD â†         Moves HEAD â†
Staging Area:       Unchanged       Reset to match HEAD  Reset to match HEAD
Working Directory:  Unchanged       Unchanged            Reset to match HEAD
```

### Soft Reset â€” Undo Commit, Keep Everything Staged

```bash
git reset --soft HEAD~1
```

**What it does:** Moves HEAD back one commit. All changes from that commit are now in the staging area, ready to be re-committed.

**Use case:** You committed too early and want to add more changes or fix the commit message.

**Before:**
```
A â”€â”€ B â”€â”€ C (HEAD)
          â†‘ committed: "Add login" with files X, Y
```

**After:**
```
A â”€â”€ B (HEAD)
     Files X, Y are staged
```

**Example:**

```bash
# Oops, committed with wrong message and forgot a file
git reset --soft HEAD~1
git add forgotten-file.js
git commit -m "feat(auth): add login with session management"
```

### Mixed Reset (Default) â€” Undo Commit, Unstage Changes

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

### Hard Reset â€” Undo Everything

```bash
git reset --hard HEAD~1
```

**What it does:** Moves HEAD back one commit. Discards ALL changes â€” staging area and working directory are reset to match the target commit.

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

### Keep Reset -- Move HEAD but Preserve Working Changes

```bash
git reset --keep HEAD~1
```

**What it does:** Moves HEAD back one commit, like `--hard`, but **keeps your working directory changes** if they don't conflict with the reset. If any working directory file would be overwritten, the reset is aborted.

**Comparison of all reset modes:**

| Mode | HEAD | Staging Area | Working Directory |
|------|------|-------------|-------------------|
| `--soft` | Moves back | Unchanged | Unchanged |
| `--mixed` (default) | Moves back | Reset | Unchanged |
| `--hard` | Moves back | Reset | Reset (destructive) |
| `--keep` | Moves back | Reset | Preserved if safe |

**Example:**

```bash
# You committed something on the wrong branch, but also have uncommitted work
git reset --keep HEAD~1
# The commit is undone, but your uncommitted edits are preserved
```

**Output:**
```
HEAD is now at 3a4b5c6 fix(auth): handle expired JWT tokens
```

**Real-life use case:** You accidentally committed to `main` instead of your feature branch. You have other uncommitted changes you don't want to lose. `--keep` undoes the commit while preserving your work-in-progress.

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

## 6.4 Reverting â€” `git revert`

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
A â”€â”€ B â”€â”€ C â”€â”€ D (revert of C)
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
| Undo a commit on your own feature branch | Either | Your choice â€” reset is cleaner |
| Production hotfix rollback | `git revert` | Auditable, doesn't rewrite history |

### Conflicts During Revert

A revert can produce conflicts when the code being reverted has been modified by subsequent commits. Git cannot automatically undo changes if the surrounding code has changed since the original commit.

**When this happens:**

```bash
git revert a1b2c3d
```

**Output:**
```
error: could not revert a1b2c3d... feat: add discount logic
hint: After resolving the conflicts, mark the corrected paths
hint: with 'git add <paths>' and run 'git revert --continue'.
CONFLICT (content): Merge conflict in src/pricing.js
```

**Example scenario:**

```
Commit A: Adds calculateDiscount() function
Commit B: Modifies calculateDiscount() to add a new parameter
Commit C: Refactors calculateDiscount() to use a config object

You want to revert Commit A, but Commits B and C have changed the same code.
Git cannot simply remove the function because it looks different now.
```

**How to resolve:**

```bash
# 1. Open the conflicted file and resolve the conflict markers
#    Decide what the code should look like without the reverted change

# 2. Stage the resolved file
git add src/pricing.js

# 3. Continue the revert
git revert --continue

# Or abort if the revert is too complex
git revert --abort
```

**Real-life use case:** A team deployed a feature that caused performance issues. They want to revert the original feature commit, but 3 subsequent commits have built on top of it. The revert produces conflicts that require manual resolution to remove the feature while keeping the later improvements.

---

## 6.5 Stashing â€” `git stash`

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

## 6.6 Cleaning Untracked Files â€” `git clean`

### Command

```bash
git clean
```

**What it does:** Removes untracked files from the working directory.

### Why Clean Is Needed (Build Context)

During development, build tools and test runners create files that Git does not track:

- Compiled outputs (`*.class`, `*.o`, `*.pyc`)
- Log files (`*.log`)
- Temporary test artifacts

These files can interfere with clean builds. If old compiled files remain from a previous build, the next build may be incremental rather than fresh, potentially hiding errors. `git clean` removes these untracked files so you start from a known state.

### Dry Run (Preview What Would Be Deleted)

```bash
git clean -n
# or
git clean --dry-run
# or with directories included
git clean -nd
```

**Output:**
```
Would remove debug.log
Would remove temp.txt
Would remove src/test-output.json
Would remove tmp/
```

**What `-nd` does:** Shows what untracked files AND directories would be removed, without actually deleting anything. Always run this before `git clean -fd`.

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
â”‚
â”œâ”€â”€ Changes are NOT committed?
â”‚   â”œâ”€â”€ Want to discard working directory changes? â†’ git restore <file>
â”‚   â”œâ”€â”€ Want to unstage? â†’ git restore --staged <file>
â”‚   â””â”€â”€ Want to save for later? â†’ git stash
â”‚
â”œâ”€â”€ Changes ARE committed but NOT pushed?
â”‚   â”œâ”€â”€ Want to redo the commit? â†’ git reset --soft HEAD~1
â”‚   â”œâ”€â”€ Want to reorganize commits? â†’ git reset HEAD~1
â”‚   â””â”€â”€ Want to completely discard? â†’ git reset --hard HEAD~1
â”‚
â””â”€â”€ Changes ARE committed AND pushed?
    â””â”€â”€ git revert <commit>  (always safe)
```

---

