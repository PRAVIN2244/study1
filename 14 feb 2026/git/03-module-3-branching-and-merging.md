# MODULE 3: Branching and Merging

## 3.1 Understanding Branches

A branch in Git is simply a lightweight, movable pointer to a commit. When you create a branch, Git creates a new pointer â€” it doesn't copy any files.

```
main:       A â”€â”€ B â”€â”€ C
                      â†‘
                     HEAD
```

When you create a new branch `feature`:

```
main:       A â”€â”€ B â”€â”€ C
                      â†‘
feature:              (also points here)
```

After committing on `feature`:

```
main:       A â”€â”€ B â”€â”€ C
                       \
feature:                D â”€â”€ E
                             â†‘
                            HEAD
```

**HEAD** is a special pointer that tells Git which branch (and commit) you're currently on.

### Commits Belong to a Branch

Commits do not go "directly into the repository." They are stored under a branch. Even when you are not aware of branches, your commits go into the default branch (`master` or `main`). This means:

- Every commit is reachable through a branch pointer
- Different branches can have different commits
- Switching branches changes which commits (and files) are visible

### Why Branches Exist

In real projects, multiple streams of work happen in parallel:

- Separate releases (e.g., Android release vs iOS release)
- Multiple features being developed simultaneously
- Experimentation or proof-of-concept work that should not affect stable code

Branches allow each stream to have its own isolated history without interfering with others.

### Tree Analogy

Think of branches like a tree:

- The **trunk** is the main branch (`master`/`main`)
- **Branches** grow from the trunk (or from other branches)
- Every branch must have a parent -- it is created from the current commit of whatever branch you are on

When you create a new branch, it initially points to the **same commit** as the branch you created it from. Both branches are identical until you make new commits on one of them.

```
master:  C1 -> C2 -> C3 -> C4
                             ^
ios:                         (also points to C4)
```

After committing on `ios`:

```
master:  C1 -> C2 -> C3 -> C4
                              \
ios:                           C5 -> C6
```

---

## 3.8 Branch Isolation and Selective Integration

### Branch Isolation

After branching, each branch can diverge:

- New files/commits on `feature` are not visible on `main` until integrated.
- Switching branches changes visible working tree content to match that branch state.

### Example: Files Appear and Disappear When Switching Branches

```bash
# Start on master with existing files
git checkout master
ls
```

**Output:**
```
one.java  two.java
```

```bash
# Create and switch to ios branch
git branch ios
git checkout ios
```

**Output:**
```
Switched to branch 'ios'
```

```bash
# Create a file and commit on ios
echo "file in ios branch" > ios.txt
git add ios.txt
git commit -m "Add ios.txt for iOS release"
```

**Output:**
```
[ios 9004abc] Add ios.txt for iOS release
 1 file changed, 1 insertion(+)
 create mode 100644 ios.txt
```

```bash
# Switch back to master
git checkout master
ls
```

**Output (ios.txt is gone):**
```
one.java  two.java
```

```bash
# Create a file and commit on master
echo "file in master branch" > master.txt
git add master.txt
git commit -m "Add master.txt"
```

```bash
# Switch to ios again
git checkout ios
ls
```

**Output (master.txt is gone, ios.txt is back):**
```
one.java  two.java  ios.txt
```

**Key takeaway:** Git swaps the working directory contents to match the checked-out branch. Files committed on one branch are not visible on another until merged.

### Integration Options

- **Full integration**: `git merge <source-branch>` brings all missing commits.
- **Selective integration**: `git cherry-pick <commit-id>` brings one commit at a time.

Cherry-pick is useful when:

- A feature branch has many experimental commits.
- Only one or two production-ready commits should move to destination branch.

### Merge Conflict Reality

If both branches changed the same lines, Git may stop with conflicts.
Resolution pattern:

1. Open conflicted files and resolve content.
2. Stage resolved files with `git add`.
3. Complete merge with `git commit` (or `git merge --continue` depending on flow).

---

## 3.9 Local Branches vs Shared Branches

Git lets you create branches in your local repository at any time:

```bash
git branch ios
git checkout ios
```

Those branches are local until you publish them.

### Practical Distinction

- **Local branch**: for personal development/POC/experimentation.
- **Shared branch**: branch that exists on the central repository and is visible to team members.

### Important Workflow Rule

Push/pull works branch-to-branch. If a matching branch is not present on remote, your push behavior depends on permissions and upstream setup. In team environments, shared branch creation is often controlled by policy.

### Recommendation

- Use local branches freely for trial work.
- Publish only branches intended for collaboration.
- Keep stable branch (`main`/`master`) protected and avoid direct feature work on it.

---

## 3.10 Transcript Command Workflow: Branching, Merge, Cherry-Pick

### Create and Switch to a New Branch

```bash
git branch ios
git checkout ios
```

- `git branch ios`: creates a new branch from your current branch tip.
- `git checkout ios`: switches working tree and HEAD to `ios`.

### Return to Main/Master

```bash
git checkout master
```

- Switches back to `master` and shows files/commits from that branch context.

### Merge Full Branch Content

```bash
git checkout master
git merge ios
```

- Destination-first practice: checkout destination (`master`) first.
- `git merge ios`: brings commits from source branch `ios` not yet in `master`.

### Resolve Merge Conflict (When Same Lines Differ)

```bash
git status
# edit conflicted files manually
git add <conflicted-file>
git commit
```

- `git status` identifies conflicted files.
- After manual resolution, stage and commit to complete merge.

### Selective Merge (One Commit at a Time)

```bash
git checkout master
git cherry-pick <commit-id>
```

- Use when full merge is too broad and you only want selected commits.

---

## 3.2 Creating Branches â€” `git branch`

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

**Output (error â€” branch not merged):**
```
error: The branch 'feature/abandoned-experiment' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/abandoned-experiment'.
```

**What `-d` vs `-D` means:**
- `-d` (lowercase): Safe delete â€” refuses if the branch has unmerged changes
- `-D` (uppercase): Force delete â€” deletes regardless of merge status

---

## 3.3 Switching Branches â€” `git switch` and `git checkout`

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

**What this means:** HEAD points directly to a commit, not a branch. Any commits you make here will be "orphaned" when you switch to a branch â€” unless you create a branch first:

```bash
git switch -c rescue-branch
```

---

## 3.4 Merging â€” `git merge`

### Command

```bash
git merge <branch>
```

**What it does:** Integrates changes from `<branch>` into the current branch.

### Fast-Forward Merge

When the current branch hasn't diverged from the branch being merged:

```
Before:
main:       A â”€â”€ B â”€â”€ C
                       \
feature:                D â”€â”€ E

After (git merge feature while on main):
main:       A â”€â”€ B â”€â”€ C â”€â”€ D â”€â”€ E
                                â†‘
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

**"Fast-forward"** means Git just moved the branch pointer forward â€” no merge commit was created.

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
main:       A â”€â”€ B â”€â”€ C
                       \
feature:                D â”€â”€ E

After (--no-ff):
main:       A â”€â”€ B â”€â”€ C â”€â”€â”€â”€â”€â”€â”€â”€ M  (merge commit)
                       \        /
feature:                D â”€â”€ E
```

**Why use `--no-ff`:** Preserves the fact that a feature branch existed. The merge commit acts as a marker. Many teams require this in their workflow.

### Three-Way Merge

When both branches have diverged:

```
Before:
main:       A â”€â”€ B â”€â”€ C â”€â”€ F
                       \
feature:                D â”€â”€ E

After merge:
main:       A â”€â”€ B â”€â”€ C â”€â”€ F â”€â”€ M  (merge commit)
                       \       /
feature:                D â”€â”€ E
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


### Merge Opens an Editor for the Commit Message

When Git creates a merge commit (three-way merge or `--no-ff`), it may open your configured editor to write a merge commit message. You will see something like:

```
Merge branch 'ios'
# Please enter a commit message to explain why this merge is necessary,
# especially if it merges an updated upstream into a topic branch.
#
# Lines starting with '#' will be ignored.
```

Save and exit the editor (in vi: `:wq`) to complete the merge. The merge commit records that changes came from another branch, making it traceable in history.

### Why the Merge Commit Exists

Without a merge commit, both branches would look identical after merging and you could not tell which commits originated from which branch. The merge commit serves as a record: "at this point, branch X was integrated into branch Y."

### Merge When Nothing Is New: "Already up to date"

If the destination branch already contains all commits from the source branch:

```bash
git checkout master
git merge ios
```

**Output:**
```
Already up to date.
```

**What this means:** There are no new commits in `ios` that `master` does not already have. Nothing to merge.
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

1. **Edit the file** â€” remove the markers and keep the correct content:

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

**Resolution** â€” combine both changes:

```javascript
function calculateTotal(items, taxRate = 0.08) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  return subtotal + (subtotal * taxRate);
}
```

### How to Avoid Conflicts During Merges

Merge conflicts are inevitable in team environments, but their frequency and severity can be reduced with disciplined practices:

| Practice | Why It Helps |
|----------|-------------|
| **Pull frequently** | Keeps your branch close to `main`, reducing divergence |
| **Keep feature branches small** | Fewer changed files = fewer conflict opportunities |
| **Avoid editing the same files unnecessarily** | Coordinate with teammates on shared files |
| **Communicate with the team** | Discuss who is working on which modules |
| **Add CI gates** | Automated checks catch integration issues early |
| **Enforce code ownership** | Assign owners to critical modules to limit concurrent edits |

**Example workflow to minimize conflicts:**

```bash
# Start of each day: sync your feature branch with main
git checkout feature/user-auth
git pull origin main

# Work in small increments and commit often
git add src/auth.js
git commit -m "feat: add token validation"

# Before pushing, sync again
git pull origin main
git push origin feature/user-auth
```

**Real-life use case:** A team of 5 developers working on the same microservice. Developer A owns `src/auth/`, Developer B owns `src/payments/`. By assigning ownership and pulling daily, the team reduces conflicts from ~10/week to ~1/week.

### Why Testing Should Be Done After Merging

Two individually working features may collide when combined. Integration bugs only appear after merge.

**Example scenario:**

```
Feature A: Changes the user object to add a "role" field
Feature B: Changes the user serialization to JSON format

Both pass tests individually.
After merge: serialization breaks because it doesn't handle the new "role" field.
```

**Best practice:** Run unit tests, integration tests, and CI pipelines after every merge:

```bash
# After merging
git checkout main
git merge feature/user-roles

# Run the full test suite
npm test           # or: pytest, go test ./..., mvn test
npm run lint       # Check for code style issues

# If tests fail, investigate the merge result
git log --oneline -5
git diff HEAD~1
```

**Real-life use case:** A CI/CD pipeline configured to run on every merge to `main`. If tests fail, the merge is flagged and the team is notified via Slack. This catches integration bugs before they reach production.

### Why Merge Conflict Resolution Is a Key Interview Topic

Merge conflicts occur daily in real projects. Interviewers test this because it reveals:

1. **Technical skill** -- Can you read conflict markers and resolve them correctly?
2. **Thought process** -- Do you understand *why* the conflict happened?
3. **Communication** -- Do you talk to the other developer before overwriting their code?
4. **Prevention mindset** -- Do you know how to reduce conflicts through branching strategy?

**What interviewers expect you to demonstrate:**

```bash
# 1. Identify which files have conflicts
git status
# Output:
# Unmerged paths:
#   both modified:   src/auth.js

# 2. Open the file and understand both sides of the conflict
cat src/auth.js
# <<<<<<< HEAD
# const timeout = 3000;
# =======
# const timeout = 5000;
# >>>>>>> feature/increase-timeout

# 3. Make an informed decision (don't just pick one side blindly)
# Talk to the other developer if needed

# 4. Resolve, stage, and commit
git add src/auth.js
git commit -m "fix: resolve timeout conflict, use 5000ms per team decision"
```

**Real-life use case:** During a technical interview, a candidate is asked to resolve a conflict in a live coding exercise. The interviewer watches whether the candidate reads both sides carefully, asks clarifying questions about intent, and commits with a meaningful message explaining the resolution.

### Comparing Branch Heads with `git show-branch`

```bash
# Compare the tips of multiple branches quickly
git show-branch --more=10 main feature/auth feature/payments
```

**Output:**
```
* [main] fix: update dependencies
 ! [feature/auth] feat: add OAuth2 login
  ! [feature/payments] feat: add Stripe integration
---
  + [feature/payments] feat: add Stripe integration
 +  [feature/auth] feat: add OAuth2 login
*++ [main] fix: update dependencies
```

**What this shows:** Which commits are unique to each branch and where they diverge. The `+` and `*` markers indicate which branch contains each commit.

**Real-life use case:** Before merging multiple feature branches, a tech lead uses `show-branch` to see how far each branch has diverged from `main`.

---

## 3.6 Rebasing â€” `git rebase`

### Command

```bash
git rebase <base-branch>
```

**What it does:** Moves (replays) your branch's commits on top of another branch, creating a linear history.

### Merge vs Rebase â€” Visual Comparison

**Merge:**
```
main:       A â”€â”€ B â”€â”€ C â”€â”€ F â”€â”€ M
                       \       /
feature:                D â”€â”€ E
```

**Rebase:**
```
main:       A â”€â”€ B â”€â”€ C â”€â”€ F
                            \
feature:                     D' â”€â”€ E'
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

### Interactive Rebase â€” `git rebase -i`

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

### Rebase Preserving Merge Commits -- `git rebase --rebase-merges`

Standard rebase flattens merge commits into a linear sequence. If your branch contains intentional merge commits you want to preserve, use `--rebase-merges`:

```bash
# Rebase while preserving the merge structure
git rebase --rebase-merges main
```

**When to use:** When your feature branch merged another branch into it (e.g., you merged a shared library branch into your feature) and you want to keep that merge visible after rebasing onto updated `main`.

**Example:**

```bash
# Your feature branch merged a shared-utils branch
git switch feature/dashboard
git merge shared/utils    # This merge commit should be preserved

# Later, you rebase onto updated main
git rebase --rebase-merges main
# The merge of shared/utils is preserved in the rebased history
```

**Real-life use case:** A developer's feature branch merged a hotfix branch during development. When rebasing onto `main` before creating a PR, `--rebase-merges` keeps the hotfix merge visible in the history for traceability.

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

