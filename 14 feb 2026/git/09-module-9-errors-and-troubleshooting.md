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
# Copy the output and add it to GitHub: Settings â†’ SSH Keys

# 5. Test the connection
ssh -T git@github.com
# Output: Hi username! You've successfully authenticated...
```

### Error: `remote: Invalid username or password`

```
remote: Invalid username or password.
fatal: Authentication failed for 'https://github.com/...'
```

**Cause:** HTTPS credentials are wrong or expired. GitHub no longer accepts passwords â€” you need a Personal Access Token (PAT).

**Fix:**

```bash
# 1. Generate a PAT on GitHub: Settings â†’ Developer Settings â†’ Personal Access Tokens

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

### Error: `rejected â€” non-fast-forward`

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

### Error: `rejected â€” fetch first`

```
! [rejected]        main -> main (fetch first)
```

**Cause:** Same as above â€” remote has diverged.

**Fix:** Same as above â€” `git pull` or `git pull --rebase` first.

### Error: `failed to push â€” remote contains work you do not have locally`

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

### Error: `You have unstaged changes â€” cannot rebase`

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

### Error: `cannot delete branch â€” checked out`

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

## 9.8 Undoing Mistakes â€” Quick Reference

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

## 9.10 Git Debug and Trace Commands

When standard troubleshooting isn't enough, Git provides low-level debug and trace tools to inspect internal operations.

### Environment Variable Tracing

Set environment variables before a Git command to see internal operations:

```bash
# Trace high-level Git calls to stderr
GIT_TRACE=1 git status
```

**Output:**
```
14:32:01.234567 git.c:460               trace: built-in: git status
14:32:01.234890 run-command.c:663       trace: run_command: unset GIT_PREFIX; cd .
On branch main
nothing to commit, working tree clean
```

```bash
# Trace wire protocol during network operations
GIT_TRACE_PACKET=1 git fetch
```

**Output:**
```
packet:        fetch< version 2
packet:        fetch< agent=git/2.43.0
packet:        fetch> command=ls-refs
```

```bash
# Verbose HTTP(S) transfer details
GIT_CURL_VERBOSE=1 git fetch
```

**Output:**
```
* Trying 140.82.121.4:443...
* Connected to github.com (140.82.121.4) port 443
> GET /user/repo.git/info/refs?service=git-upload-pack HTTP/2
< HTTP/2 200
```

**Real-life use case:** Debugging why `git push` fails behind a corporate proxy. `GIT_CURL_VERBOSE=1` reveals the exact HTTP request and response, showing whether the proxy is blocking the connection.

### Git Bugreport and Diagnose

```bash
# Auto-collect environment and repo info for support tickets
git bugreport
```

**Output:**
```
Created new report at git-bugreport-2025-01-15-1432.txt
```

The generated file contains Git version, OS info, enabled hooks, and other diagnostic data.

```bash
# Produce a diagnostic bundle (Git 2.38+)
git diagnose
```

**Output:**
```
Created diagnostics archive at .git/diagnostics/git-diagnostics-2025-01-15-1432.zip
```

**Real-life use case:** When filing a bug report with Git maintainers or your platform team, `git bugreport` collects all relevant environment details automatically.

---

## 9.11 Low-Level Object Inspection Commands

Git stores everything as objects (blobs, trees, commits, tags). These commands let you inspect them directly.

### Inspecting Objects with `git cat-file`

```bash
# Show the type of an object
git cat-file -t HEAD
```

**Output:**
```
commit
```

```bash
# Pretty-print an object's content
git cat-file -p HEAD
```

**Output:**
```
tree 7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e
parent 1f2e3d4c5b6a7890abcdef1234567890abcdef12
author Jane Smith <jane@company.com> 1705312800 +0000
committer Jane Smith <jane@company.com> 1705312800 +0000

feat: add user authentication
```

```bash
# Show the size of an object
git cat-file -s HEAD
```

**Output:**
```
245
```

### Listing Directory Snapshots with `git ls-tree`

```bash
# List the tree (directory snapshot) of a commit
git ls-tree HEAD
```

**Output:**
```
100644 blob a1b2c3d4e5f6    .gitignore
100644 blob d4e5f6a7b8c9    README.md
040000 tree 1a2b3c4d5e6f    src
100644 blob 7g8h9i0j1k2l    package.json
```

```bash
# Recursive listing to see all files
git ls-tree -r HEAD
```

**Output:**
```
100644 blob a1b2c3d4e5f6    .gitignore
100644 blob d4e5f6a7b8c9    README.md
100644 blob 4d5e6f7g8h9i    src/app.js
100644 blob 0j1k2l3m4n5o    src/server.js
100644 blob 7g8h9i0j1k2l    package.json
```

### Listing References with `git show-ref`

```bash
# Show all refs and their SHAs
git show-ref
```

**Output:**
```
a1b2c3d4e5f6 refs/heads/main
d4e5f6a7b8c9 refs/heads/feature/auth
7g8h9i0j1k2l refs/remotes/origin/main
0j1k2l3m4n5o refs/tags/v1.0.0
```

### Scriptable Ref Inspection with `git for-each-ref`

```bash
# List branches sorted by last commit date
git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads/
```

**Output:**
```
feature/auth 2 hours ago
main 1 day ago
feature/old-work 3 weeks ago
```

**Real-life use case:** Finding stale branches that should be cleaned up.

### Naming Commits with `git name-rev` and `git describe`

```bash
# Map a SHA to the nearest ref/branch
git name-rev a1b2c3d
```

**Output:**
```
a1b2c3d main~3
```

```bash
# Get a human-readable name for a commit based on the nearest tag
git describe --tags
```

**Output:**
```
v1.2.0-14-ga1b2c3d
```

This means: 14 commits after tag `v1.2.0`, at commit `a1b2c3d`.

```bash
# Which tag contains a specific commit
git describe --contains a1b2c3d
```

**Output:**
```
v1.3.0~5
```

**Real-life use case:** CI/CD pipelines use `git describe` to auto-generate version numbers for builds.

---

## 9.12 File and Index Inspection Commands

### Listing Tracked Files with `git ls-files`

```bash
# Show all tracked files
git ls-files
```

**Output:**
```
.gitignore
README.md
package.json
src/app.js
src/server.js
```

```bash
# Show staging info (useful during conflict resolution)
git ls-files -s
```

**Output:**
```
100644 a1b2c3d4 0	README.md
100644 d4e5f6a7 0	src/app.js
```

The third column is the stage number: `0` = normal, `1` = base, `2` = ours, `3` = theirs (during conflicts).

```bash
# Show unmerged entries (conflict details)
git ls-files -u
```

**Output (during a merge conflict):**
```
100644 abc123 1	src/config.js    # base version
100644 def456 2	src/config.js    # ours (current branch)
100644 789abc 3	src/config.js    # theirs (incoming branch)
```

```bash
# Show true untracked files
git ls-files --others --exclude-standard
```

### Inspecting Remote Refs with `git ls-remote`

```bash
# See remote refs without fetching
git ls-remote origin
```

**Output:**
```
a1b2c3d4e5f6    HEAD
a1b2c3d4e5f6    refs/heads/main
d4e5f6a7b8c9    refs/heads/develop
0j1k2l3m4n5o    refs/tags/v1.0.0
```

**Real-life use case:** CI pipelines use `git ls-remote` to check if a tag exists before creating a release, without cloning the entire repository.

### Controlling Index Behavior with `git update-index`

```bash
# Ignore local changes to a tracked file (useful for local config overrides)
git update-index --assume-unchanged config/local.yml
```

**What this does:** Git stops checking this file for changes. Useful when you have local configuration that differs from the repository version.

```bash
# Undo assume-unchanged
git update-index --no-assume-unchanged config/local.yml
```

```bash
# Skip worktree (stronger version, survives git reset)
git update-index --skip-worktree config/local.yml
```

```bash
# Undo skip-worktree
git update-index --no-skip-worktree config/local.yml
```

**Difference between `--assume-unchanged` and `--skip-worktree`:**

| Flag | Purpose | Survives `git reset`? |
|------|---------|----------------------|
| `--assume-unchanged` | Performance optimization for large repos | No |
| `--skip-worktree` | Intentionally keep local changes out of commits | Yes |

**Real-life use case:** A developer needs to modify `database.yml` to point to their local database. Using `--skip-worktree` prevents accidentally committing their local database credentials.

### Viewing Conflict Stage Files -- `git show :1:`, `:2:`, `:3:`

During a merge conflict, Git stores three versions of each conflicted file in the index:

```bash
# Show the base version (common ancestor)
git show :1:src/config.js
```

```bash
# Show "ours" version (current branch)
git show :2:src/config.js
```

```bash
# Show "theirs" version (incoming branch)
git show :3:src/config.js
```

**What the stage numbers mean:**

| Stage | Version | Description |
|-------|---------|-------------|
| `:0:` | Normal | File with no conflict (resolved) |
| `:1:` | Base | Common ancestor of both branches |
| `:2:` | Ours | Current branch (HEAD) version |
| `:3:` | Theirs | Incoming branch version |

**Real-life use case:** When resolving a complex conflict, you want to see the original base version to understand what both sides changed. `git show :1:file` shows the version before either branch modified it.

### Checking Applied Attributes -- `git check-attr`

```bash
# Show all .gitattributes rules applied to a file
git check-attr -a -- src/app.js
```

**Output:**
```
src/app.js: text: auto
src/app.js: eol: lf
src/app.js: diff: set
```

```bash
# Check a specific attribute
git check-attr merge -- package-lock.json
```

**Output:**
```
package-lock.json: merge: ours
```

**Real-life use case:** Debugging why a file isn't being diffed correctly or why merge conflicts aren't being resolved as expected by checking which `.gitattributes` rules apply.

### Validating Reference Names -- `git check-ref-format`

```bash
# Check if a branch name is valid
git check-ref-format --branch "feature/my-feature"
```

**Output:**
```
feature/my-feature
```

```bash
# Invalid name (contains spaces)
git check-ref-format --branch "my feature"
```

**Output:**
```
fatal: 'my feature' is not a valid branch name
```

**Real-life use case:** CI/CD hooks validate branch names before allowing pushes, ensuring they follow naming conventions like `feature/*`, `fix/*`, `release/*`.

### Checking What HEAD Points To -- `git symbolic-ref`

```bash
# Show which ref HEAD points to
git symbolic-ref HEAD
```

**Output:**
```
refs/heads/main
```

```bash
# In detached HEAD state
git symbolic-ref HEAD
```

**Output:**
```
fatal: ref HEAD is not a symbolic ref
```

**Real-life use case:** Scripts use `symbolic-ref` to determine the current branch name programmatically. If it fails, the script knows it's in detached HEAD state.

### Comparing Branches for Unique Commits -- `git cherry`

```bash
# Show commits in feature/auth that are NOT in main
git cherry -v main feature/auth
```

**Output:**
```
+ a1b2c3d feat: add OAuth2 login
+ d4e5f6a feat: add session management
- 7g8h9i0 fix: handle null user    # Already in main (cherry-picked)
```

**What the markers mean:**
- `+` = commit is unique to the right branch (not in left branch)
- `-` = commit has an equivalent in the left branch (already cherry-picked)

**Real-life use case:** Before merging a feature branch, checking which commits are truly new and which have already been applied to `main` via cherry-pick.

### Inspecting Pack Files -- `git verify-pack`

```bash
# Find large objects in pack files
git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -10
```

**Output:**
```
a1b2c3d4 blob   15234567  14523456  12345  data/large-dataset.csv
d4e5f6a7 blob    5234567   4523456  23456  assets/video.mp4
```

**What this shows:** Object hash, type, size (bytes), packed size, and offset. Sorted by size to find the largest objects.

**Real-life use case:** Diagnosing why a repository is slow to clone. Large binary files accidentally committed can be identified and removed with `git filter-branch` or BFG Repo-Cleaner.

### Counting and Listing Commits -- `git rev-list`

```bash
# Count total commits in the repository
git rev-list --count HEAD
```

**Output:**
```
1247
```

```bash
# Find the root commit(s)
git rev-list --max-parents=0 HEAD
```

**Output:**
```
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
```

```bash
# Count commits between two points
git rev-list --count v1.0.0..HEAD
```

**Output:**
```
42
```

**Real-life use case:** CI pipelines use `git rev-list --count` to generate build numbers. The root commit is useful for understanding repository history and grafts.

### Advanced Clean Options

```bash
# Remove ONLY ignored files (e.g., build artifacts, caches)
git clean -Xdf
```

**What `-X` does:** Only removes files matched by `.gitignore` patterns. Untracked files that aren't ignored are preserved.

**Output:**
```
Removing node_modules/
Removing dist/
Removing .cache/
```

```bash
# Remove ALL untracked files AND ignored files (full reset)
git clean -xdf
```

**What `-x` (lowercase) does:** Removes everything not tracked by Git, including ignored files. This is a complete sandbox reset.

**Output:**
```
Removing node_modules/
Removing dist/
Removing .cache/
Removing .env
Removing temp-notes.txt
```

| Flag | What It Removes |
|------|----------------|
| `-f` | Untracked files only |
| `-fd` | Untracked files and directories |
| `-Xdf` | Only ignored files and directories |
| `-xdf` | All untracked + ignored files and directories |

**Always dry-run first:**

```bash
git clean -Xdn    # Preview what -Xdf would remove
git clean -xdn    # Preview what -xdf would remove
```

**Real-life use case:** A developer's build is failing due to stale cache files. Running `git clean -Xdf` removes all build artifacts and caches while preserving any new untracked source files they're working on.

---

## 9.13 Reuse Recorded Resolution (rerere)

`git rerere` (reuse recorded resolution) records how you resolve merge conflicts and automatically applies the same resolution if the same conflict occurs again.

### Enabling rerere

```bash
git config --global rerere.enabled true
```

### How It Works

1. You encounter a merge conflict and resolve it manually
2. Git records the resolution
3. Next time the same conflict occurs, Git applies the recorded resolution automatically

### Commands

```bash
# See recorded conflict resolutions
git rerere status
```

**Output:**
```
src/config.js
```

```bash
# Show how conflicts were auto-resolved
git rerere diff
```

**Output:**
```
--- a/src/config.js
+++ b/src/config.js
@@ -1,7 +1,4 @@
-<<<<<<< HEAD
 const port = process.env.PORT || 3000;
-=======
-const port = 8080;
->>>>>>> feature/new-port
```

```bash
# Clean old rerere records
git rerere gc
```

**Real-life use case:** When rebasing a long-lived feature branch onto `main` repeatedly, the same conflicts may appear each time. With `rerere` enabled, Git remembers your resolutions and applies them automatically on subsequent rebases.

---

## 9.14 Additional Advanced Commands

### Creating Archives with `git archive`

```bash
# Create a tar archive of the current HEAD
git archive HEAD | tar -x -C /tmp/project-snapshot

# Create a zip archive of a specific tag
git archive --format=zip --output=release-v1.0.zip v1.0.0
```

**Real-life use case:** Creating a clean source distribution for release without `.git` metadata.

### Verifying Signed Commits and Tags

```bash
# Verify a GPG-signed commit
git verify-commit a1b2c3d
```

**Output (if valid):**
```
gpg: Signature made Wed Jan 15 14:32:00 2025 UTC
gpg: Good signature from "Jane Smith <jane@company.com>"
```

```bash
# Verify a signed tag
git verify-tag v1.0.0
```

**Real-life use case:** Security-sensitive projects require signed commits and tags to verify that code was actually authored by the claimed developer.

### Git Notes

```bash
# Add a note to a commit (without modifying the commit)
git notes add -m "Reviewed by security team" a1b2c3d

# Show notes for a commit
git notes show a1b2c3d
```

**Output:**
```
Reviewed by security team
```

**Real-life use case:** Adding audit annotations to commits without rewriting history.

### Comparing Commit Series with `git range-diff`

```bash
# Compare two versions of a branch (before and after rebase)
git range-diff main..feature@{1} main..feature
```

**Output:**
```
1:  a1b2c3d = 1:  d4e5f6a feat: add login page
2:  7g8h9i0 ! 2:  0j1k2l3 fix: handle null user
    @@ src/auth.js
    -  if (user) {
    +  if (user != null) {
```

**Real-life use case:** After force-pushing a rebased branch, reviewers use `range-diff` to see exactly what changed between the old and new versions of the branch.

### Normalizing Author Identities with `.mailmap`

Create a `.mailmap` file in the repository root to normalize author names:

```
# Format: Proper Name <proper@email.com> Old Name <old@email.com>
Jane Smith <jane@company.com> jane <jane@laptop.local>
Jane Smith <jane@company.com> J. Smith <jsmith@old-company.com>
Bob Wilson <bob@company.com> <bob.wilson@personal.com>
```

```bash
# After adding .mailmap, shortlog shows normalized names
git shortlog -sn
```

**Output (without .mailmap):**
```
    15  jane
    12  J. Smith
     8  Bob Wilson
     5  bob.wilson
```

**Output (with .mailmap):**
```
    27  Jane Smith
    13  Bob Wilson
```

**Real-life use case:** Developers who commit from different machines or email addresses appear as separate authors. `.mailmap` consolidates them for accurate contribution tracking.

### Git Replace (Temporary Object Substitution)

```bash
# Temporarily substitute one commit for another (for debugging)
git replace <old-commit> <new-commit>

# List all replacements
git replace -l

# Remove a replacement
git replace -d <old-commit>
```

**Real-life use case:** Debugging history issues by temporarily swapping commits without rewriting history.

---

## 9.15 Git Large File Storage (LFS)

Git is designed for text files. Large binary files (videos, datasets, compiled assets) bloat the repository and slow down cloning. Git LFS stores large files on a separate server and replaces them with lightweight pointers in the repository.

### Installing Git LFS

```bash
# Install Git LFS (one-time setup)
git lfs install
```

**Output:**
```
Updated git hooks.
Git LFS initialized.
```

### Tracking Large Files

```bash
# Track all MP4 files with LFS
git lfs track "*.mp4"

# Track all files in a specific directory
git lfs track "assets/videos/**"

# Track a specific large file
git lfs track "data/training-set.csv"
```

This creates or updates a `.gitattributes` file:

```
*.mp4 filter=lfs diff=lfs merge=lfs -text
assets/videos/** filter=lfs diff=lfs merge=lfs -text
data/training-set.csv filter=lfs diff=lfs merge=lfs -text
```

### Committing LFS-Tracked Files

```bash
# Always commit .gitattributes first
git add .gitattributes
git commit -m "chore: configure LFS for video files"

# Then add and commit the large files normally
git add assets/demo.mp4
git commit -m "feat: add product demo video"
git push origin main
```

### Checking LFS Status

```bash
# List all LFS-tracked patterns
git lfs track
```

**Output:**
```
Listing tracked patterns
    *.mp4 (.gitattributes)
    data/training-set.csv (.gitattributes)
```

```bash
# List all LFS objects in the repository
git lfs ls-files
```

**Output:**
```
a1b2c3d4e5 * assets/demo.mp4
d4e5f6a7b8 * data/training-set.csv
```

### Migrating Existing Files to LFS

```bash
# Migrate existing large files to LFS (rewrites history)
git lfs migrate import --include="*.mp4" --everything
```

**Real-life use case:** A game development team stores 3D model files (`.fbx`, `.blend`) and textures (`.psd`, `.tga`) in Git LFS. Without LFS, the repository would be 50GB+. With LFS, the Git repository stays under 500MB, and large assets are fetched on demand.

### Quick Recap

| Command | Purpose |
|---------|---------|
| `git lfs install` | Initialize LFS for the current user |
| `git lfs track "*.mp4"` | Track files matching a pattern |
| `git lfs ls-files` | List all LFS-tracked files |
| `git lfs migrate import` | Move existing files to LFS storage |


