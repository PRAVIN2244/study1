# MODULE 4: Remote Repositories

## 4.1 Understanding Remotes

A **remote** is a reference to a repository hosted on a server (GitHub, GitLab, Bitbucket, self-hosted). When you clone a repository, Git automatically creates a remote called `origin`.

```
Your Machine                          Server (GitHub)
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Local Repo   â”‚ â”€â”€ git push â”€â”€â”€â”€â”€â”€â–º â”‚ Remote Repo  â”‚
â”‚              â”‚ â—„â”€â”€ git fetch â”€â”€â”€â”€â”€ â”‚ (origin)     â”‚
â”‚ main         â”‚                     â”‚ main         â”‚
â”‚ feature/x    â”‚                     â”‚ feature/x    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Your local repository tracks **remote-tracking branches** like `origin/main`. These are read-only snapshots of where the remote branches were the last time you communicated with the server.

---

## 4.8 Remote Mapping, Branch Mapping, and Distributed Sharing

### Push/Pull Mapping

Push and pull are effectively branch-to-branch operations:

- Local `<branch>` <-> Remote `<branch>`

That is why default workflows usually target the same branch name on remote.

### Remote References

`origin` is a remote reference name, not a protocol or special server.
You can add additional remotes:

```bash
git remote add demo <url-or-path>
git remote -v
git pull demo master
git push demo master
```

This enables repository-to-repository sharing beyond only one central remote.

### Bare vs Non-Bare Repositories

- **Bare repository**: meant for shared storage/exchange (typical central repo).
- **Non-bare repository**: regular working clone with checked-out files.

In normal team setups, people push to bare remotes. Pushing to non-bare repos can have additional constraints and is generally not the default collaboration model.

### Error: Pushing to a Non-Bare Repository

If you add another developer's workspace (non-bare repo) as a remote and try to push to a branch they have checked out, Git will reject it:

```bash
git push origin master
```

**Error:**
```
remote: error: refusing to update checked out branch: refs/heads/master
remote: error: By default, updating the current branch in a non-bare repository
remote: is denied.
```

**Why this happens:** Pushing would change the files in someone else's working directory without their knowledge, potentially overwriting their uncommitted work.

**Fix:** In the target repository, checkout a different branch so `master` is no longer active:

```bash
# In the target workspace
git checkout ios
```

Then retry the push from the source workspace. It will succeed because `master` is no longer checked out in the target.

**In practice:** Central repositories (GitHub, GitLab) are bare repositories, so this problem does not occur there. This issue only arises when pushing directly between developer workspaces.

---

## 4.9 Explicit Push/Pull Syntax and Alternate Remote Demo

You will commonly see both styles:

```bash
git push
git pull
```

and explicit forms:

```bash
git push origin master
git pull origin master
```

### Why explicit form matters

- Makes it clear which remote and branch are involved.
- Useful when multiple remotes exist.
- Required in many distributed-sharing scenarios.

### Alternate remote example

```bash
git remote add demo <another-repo-url-or-path>
git remote -v
git pull demo master
git push demo master
```

This is the practical basis of distributed repository-to-repository sharing beyond one central remote.

---

## 4.10 Transcript Command Workflow: Remote References

### Inspect Current Remote Mapping

```bash
git remote -v
```

- Shows remote reference names (for example `origin`) and their fetch/push URLs.

### Add Another Remote Reference

```bash
git remote add demo <url-or-path>
git remote -v
```

- `demo` is just a reference label.
- You can now pull/push using `demo` explicitly.

### Pull from a Non-Default Remote/Branch

```bash
git pull demo master
```

- Pulls `master` updates from remote `demo` into your current branch context.

### Push to a Specific Remote/Branch

```bash
git push demo master
```

- Pushes local `master` commits to remote `demo` `master`.

### Replace Default Remote Mapping

```bash
git remote rm origin
git remote add origin <new-url-or-path>
git remote -v
```

- Removes old default remote and sets a new one as `origin`.
- After this, plain `git push` / `git pull` uses the new `origin` behavior (based on upstream/default settings).

---

## 4.2 Managing Remotes â€” `git remote`

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

**What this does:** Adds a second remote called `upstream`. Common when you fork a project â€” `origin` is your fork, `upstream` is the original.

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


### How Git Knows Where to Push

Remote URLs are stored inside `.git/config`. You can inspect this directly:

```bash
cat .git/config
```

**Output (relevant section):**
```
[remote "origin"]
    url = https://github.com/user/may2020.git
    fetch = +refs/heads/*:refs/remotes/origin/*
```

Git uses this URL automatically when you run `git push` or `git pull` without specifying a remote. The `git remote -v` command reads from this same configuration.

---

## 4.3 Fetching â€” `git fetch`

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
- `3a4b5c6..7d8e9f0 main -> origin/main` â€” The remote `main` has new commits; your `origin/main` pointer was updated
- `[new branch] feature/x` â€” A new branch exists on the remote

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

### Prune Stale Remote-Tracking Branches Directly

```bash
git remote prune origin
```

**What this does:** Removes local remote-tracking references (e.g., `origin/feature/old`) for branches that have been deleted on the remote. Same effect as `git fetch --prune` but without fetching new data.

**Output:**
```
Pruning origin
URL: https://github.com/company/api.git
 * [pruned] origin/feature/completed-work
 * [pruned] origin/feature/abandoned-experiment
```

**Real-life use case:** After a sprint, many feature branches are merged and deleted on GitHub. Running `git remote prune origin` cleans up the stale references so `git branch -r` shows only active branches.

### Listing Merged and Unmerged Branches

```bash
# Show branches already merged into current branch (safe to delete)
git branch --merged
```

**Output:**
```
  feature/auth
  feature/payments
* main
```

```bash
# Show branches NOT yet merged (still have pending work)
git branch --no-merged
```

**Output:**
```
  feature/dashboard
  feature/notifications
```

**Real-life use case:** Periodic cleanup -- delete all merged branches:

```bash
# Delete all local branches that have been merged into main
git branch --merged main | grep -v "main" | xargs git branch -d
```

### When to Use Fetch

- Before merging or rebasing, to see what's changed on the remote
- To check if there are new branches without modifying your work
- In scripts and CI/CD pipelines where you need control over when changes are applied

---

## 4.4 Pulling â€” `git pull`

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

### Pull vs Fetch â€” When to Use Which

| Situation | Command | Why |
|-----------|---------|-----|
| Quick update, no local changes | `git pull` | Simple and fast |
| Want to review changes first | `git fetch` then `git log origin/main` | Inspect before merging |
| Have local commits, want clean history | `git pull --rebase` | Avoids merge commits |
| CI/CD pipeline | `git fetch` + explicit merge/rebase | Full control |

### Pull with Fast-Forward Only

```bash
git pull --ff-only
```

**What this does:** Only updates your branch if it can be fast-forwarded (no diverging commits). If a merge would be required, the command fails instead of creating an unexpected merge commit.

**Output (success):**
```
Updating a1b2c3d..d4e5f6a
Fast-forward
 src/app.js | 5 +++++
 1 file changed, 5 insertions(+)
```

**Output (failure -- diverged):**
```
fatal: Not possible to fast-forward, aborting.
```

**Set as default:**

```bash
git config --global pull.ff only
```

**Real-life use case:** Teams that enforce linear history use `--ff-only` to prevent accidental merge commits. If the pull fails, the developer knows they need to rebase first.

### Shallow Fetch for CI/CD

```bash
# Fetch only the latest commit (no history)
git fetch --depth=1
```

**What this does:** Downloads only the most recent commit, not the full history. Dramatically reduces clone/fetch time for large repositories.

**Output:**
```
remote: Enumerating objects: 45, done.
remote: Counting objects: 100% (45/45), done.
Receiving objects: 100% (45/45), 12.34 KiB | 12.34 MiB/s, done.
```

```bash
# Clone with shallow depth (related)
git clone --depth=1 https://github.com/user/large-repo.git
```

**Real-life use case:** CI/CD pipelines clone repositories with `--depth=1` to speed up builds. A repository with 50,000 commits and 2GB of history can be cloned in seconds instead of minutes.

---

## 4.5 Pushing â€” `git push`

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

**Reading the output:** The line `main -> main` shows that push is a **branch-to-branch** operation. It pushes your local `main` to the remote `main`. Push does not transfer the entire repository -- it transfers commits from one branch to the matching branch on the remote.

### Push When No New Commits Exist

```bash
git push
```

**Output:**
```
Everything up-to-date
```

**What this means:** All local commits have already been pushed to the remote. There is nothing new to upload.

### Why Push Fails for a Locally-Created Branch

If you created a branch locally (e.g., `ios`) but the remote does not have a branch with that name, a plain `git push` will fail:

```bash
git checkout ios
git push
```

**Output:**
```
fatal: The current branch ios has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin ios
```

**Why this happens:** Git push works branch-to-branch. It tries to push local `ios` to remote `ios`, but remote `ios` does not exist yet. Git does not create remote branches automatically with a plain `git push`.

**Two ways to handle this:**

1. **Push and create the remote branch** (if you want to share it):

```bash
git push -u origin ios
```

2. **Merge locally into master, then push master** (if the branch is just for local work):

```bash
git checkout master
git merge ios
git push
```

**Best practice:** If a branch is meant for the whole team, some organizations prefer creating it in the central repository first. If it is only for personal experimentation, keep it local and merge into a shared branch when ready.

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
- `[origin/develop]` â€” Tracking, up to date
- `[origin/main]` â€” Tracking, up to date
- `[origin/feature/auth: ahead 2]` â€” Tracking, you have 2 local commits not yet pushed
- No bracket â€” Not tracking any remote branch

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

## 4.8 Multi-User Workflow Example

Two developers sharing a repository through push and pull:

### User 1: Creates and pushes work

```bash
# User 1 clones the repo
git clone https://github.com/user/may2020.git workspace00
cd workspace00

# Creates files and commits
echo "first line" > one.java
git add one.java
git commit -m "Add one.java"

# Pushes to central repo
git push
```

Central repository now has User 1's commits.

### User 2: Clones and adds their own work

```bash
# User 2 clones the same repo
git clone https://github.com/user/may2020.git workspace01
cd workspace01

# User 2 sees all of User 1's commits
git log --oneline

# User 2 creates a new file
echo "file4 content" > file4.java
git add file4.java
git commit -m "Add file4.java"
git push
```

Central repository now has commits from both users.

### User 1: Updates their workspace

```bash
cd workspace00
git pull
```

User 1's workspace now includes User 2's `file4.java`. Only the missing commits are downloaded.

### Key Points

- `git push` uploads **only new commits** to the central repository
- `git pull` downloads **only missing commits** from the central repository
- Each workspace is independent until synced via push/pull
- If both users push without pulling first, the second push will be rejected (see Module 9: non-fast-forward error)

---


