# MODULE 5: History and Inspection

## 5.1 Viewing Commit History â€” `git log`

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

The `-N` flag works with any number:

```bash
git log -1            # Show only the latest commit
git log -3            # Show the last 3 commits
git log --oneline -10 # Last 10 commits in short format
```


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
# or using relative dates
git log --since="2 weeks ago" --oneline
```

### Filter by Merge Commits

```bash
# Show only merge commits (trace integration points)
git log --merges --oneline
```

**Output:**
```
a1b2c3d Merge pull request #42 from feature/auth
d4e5f6a Merge pull request #41 from feature/payments
```

```bash
# Show only non-merge commits (focus on actual changes)
git log --no-merges --oneline
```

**Output:**
```
7g8h9i0 feat: add OAuth2 login
0j1k2l3 fix: handle null user
```

**Real-life use case:** When generating changelogs, `--no-merges` filters out merge commits to show only the actual feature/fix commits.

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

### Follow File History Through Renames

```bash
git log --follow -- src/utils/helpers.js
```

**What `--follow` does:** Tracks the file's history even if it was renamed or moved. Without `--follow`, history stops at the rename point.

**Real-life use case:** A file was renamed from `src/lib/utils.js` to `src/utils/helpers.js`. Using `--follow` shows the complete history including commits before the rename.

### Log with File List and Status

```bash
git log --name-status --oneline
```

**Output:**
```
a1b2c3d feat: add user auth
M       src/auth/login.js
A       src/auth/session.js
D       src/auth/old-auth.js
```

**What the status letters mean:** `A` = Added, `M` = Modified, `D` = Deleted, `R` = Renamed. Shows exactly which files were affected and how.

### Filter by Content Change (Pickaxe)

```bash
git log -S "calculateTotal" --oneline
```

**What `-S` does:** Finds commits where the string `calculateTotal` was added or removed. Useful for finding when a function was introduced or deleted.

### Filter by Regex in Diffs

```bash
git log -G 'function\s+calculate' --oneline
```

**What `-G` does:** Like `-S` but uses a regular expression to match against the diff content. Finds commits where the regex matched in the changed lines.

**Difference:** `-S` counts occurrences (finds add/remove). `-G` matches the regex against diff lines (finds any change matching the pattern).

### Log Between Two Commits/Tags

```bash
git log v1.0.0..v2.0.0 --oneline
```

Shows commits that are in `v2.0.0` but not in `v1.0.0`.

### Log Along Mainline Only -- `git log --first-parent`

```bash
git log --first-parent --oneline main
```

**Output:**
```
a1b2c3d Merge pull request #42 from feature/auth
d4e5f6a Merge pull request #41 from feature/payments
7g8h9i0 Merge pull request #40 from fix/login-bug
```

**What this does:** Shows only the commits along the main line of development, skipping commits that were part of merged branches. Each entry represents a merge point.

**Real-life use case:** Release managers use `--first-parent` to see a clean list of what was merged into `main` for release notes, without seeing the individual commits within each feature branch.

### Log Filtering by Change Type -- `git log --diff-filter`

```bash
# Find commits that deleted files
git log --diff-filter=D --name-only --oneline
```

**Output:**
```
a1b2c3d Remove deprecated API
 src/old-api.js
d4e5f6a Clean up unused tests
 tests/legacy-test.js
```

```bash
# Find commits that renamed files
git log --diff-filter=R --name-status --oneline
```

**Output:**
```
7g8h9i0 Rename config files
R100    config/old-name.yml    config/new-name.yml
```

| Filter | Meaning |
|--------|---------|
| `A` | Added |
| `C` | Copied |
| `D` | Deleted |
| `M` | Modified |
| `R` | Renamed |
| `T` | Type changed |

**Real-life use case:** Tracking down when a file was deleted from the repository, or finding all renames to update documentation references.

### Finding Unique Commits Between Branches -- `git log --cherry-pick`

```bash
# Show commits in feature/auth that are NOT in main (excluding cherry-picked duplicates)
git log --cherry-pick --right-only --oneline main...feature/auth
```

**Output:**
```
a1b2c3d feat: add OAuth2 provider
d4e5f6a feat: add session management
```

**What this does:** Compares two branches and shows commits unique to the right side, filtering out commits that were cherry-picked (same patch content but different hash).

**Real-life use case:** Before merging a feature branch, checking which commits are truly new and haven't already been cherry-picked to `main` as hotfixes.

### Old-Style File History -- `git whatchanged`

```bash
git whatchanged -- src/app.js
```

**Output:**
```
commit a1b2c3d
Author: Jane Smith <jane@company.com>
Date:   Mon Jan 15 14:32:00 2025

    feat: add error handling

:100644 100644 abc123 def456 M  src/app.js
```

**What this does:** Similar to `git log -p` but shows raw diff output format. Mostly used in older scripts; `git log` is preferred for new work.

### `git annotate` -- Alias for `git blame`

```bash
git annotate src/app.js
```

**Output:**
```
a1b2c3d4 (Jane Smith 2025-01-15 14:32:00 +0000 1) const express = require('express');
d4e5f6a7 (Bob Wilson 2025-01-16 09:15:00 +0000 2) const app = express();
```

**What this does:** Identical to `git blame` in most Git installations. Some older systems use `annotate` as the primary command.

---

## 5.2 Viewing Differences â€” `git diff`

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

### Diff from Common Ancestor -- `git diff --merge-base`

```bash
# Diff from the best common ancestor of two branches
git diff --merge-base main feature/auth
```

**What this does:** Shows only the changes introduced by `feature/auth` since it diverged from `main`, ignoring any changes made to `main` after the branch point.

**Why it matters:** A regular `git diff main feature/auth` shows ALL differences between the two branch tips. `--merge-base` shows only what the feature branch added, which is what you actually want to review.

**Real-life use case:** Code reviewers use this to see exactly what a feature branch changed, without noise from concurrent `main` updates.

### Detecting Renames and Copies in Diffs

```bash
# Detect renamed files
git diff --find-renames HEAD~1
```

**Output:**
```
diff --git a/src/old-name.js b/src/new-name.js
similarity index 95%
rename from src/old-name.js
rename to src/new-name.js
```

```bash
# Detect copied files (slower, checks all files)
git diff --find-copies HEAD~1
```

**Output:**
```
diff --git a/src/template.js b/src/new-module.js
similarity index 80%
copy from src/template.js
copy to src/new-module.js
```

**Real-life use case:** When refactoring a codebase, `--find-renames` shows that a file was renamed rather than deleted and recreated, preserving the connection in the diff output.

---

## 5.3 Viewing a Specific Commit â€” `git show`

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


**Reading the diff output:**

| Symbol | Meaning |
|--------|----------|
| `+` | Line was added |
| `-` | Line was removed |
| Lines without prefix | Context (unchanged lines shown for reference) |

Git compares the previous version of the file against the version in this commit.

### Show Only the Files Changed

```bash
git show --stat 3a4b5c6
```

**Show only filenames (no stats):**

```bash
git show --name-only 3a4b5c6
```

**Output:**
```
commit 3a4b5c6d7e8f
Author: Jane Smith <jane@company.com>
Date:   Mon Jan 15 14:32:00 2025

    feat: add user authentication

src/auth/login.js
src/auth/middleware.js
tests/auth.test.js
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

## 5.4 Finding Who Changed What â€” `git blame`

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

### Blame with Email Addresses

```bash
git blame --show-email src/app.js
```

**Output:**
```
a1b2c3d4 (<jane@company.com> 2025-01-15 1) const express = require('express');
d4e5f6a7 (<bob@personal.com> 2025-01-16 2) const app = express();
```

**What this does:** Shows the author's email instead of their name. Useful for identifying contributors when names are ambiguous or when debugging `.mailmap` issues.

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

### Blame in Reverse -- Track When Lines Were Introduced

```bash
# Track when lines were first introduced (reverse blame)
git blame --reverse HEAD~20..HEAD -- src/app.js
```

**What this does:** Instead of showing who last changed each line, it shows the *first* commit in the range where each line appeared. Useful for finding when a line was introduced rather than last modified.

### Blame Ignoring Formatting Commits

```bash
# Create a file listing commits to ignore (e.g., bulk formatting changes)
echo "a1b2c3d4  # Prettier reformatting" > .git-blame-ignore-revs
echo "d4e5f6a7  # ESLint auto-fix" >> .git-blame-ignore-revs

# Use it with blame
git blame --ignore-revs-file .git-blame-ignore-revs src/app.js
```

**What this does:** Skips over commits that only reformatted code (e.g., running Prettier or Black), showing the actual author of the logic instead.

**Set as default for the repository:**

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

**Real-life use case:** After running a code formatter across the entire codebase, every line shows the formatter commit as the last change. By adding that commit to `.git-blame-ignore-revs`, `git blame` shows the original authors.

### Blame Detecting Moved/Copied Code Across Files

```bash
# Detect code moved from other files (-C flag)
git blame -C -C src/utils/helpers.js
```

**Output:**
```
a1b2c3d4 src/old-utils.js (Jane Smith 2025-01-10 1) function formatDate(date) {
a1b2c3d4 src/old-utils.js (Jane Smith 2025-01-10 2)   return date.toISOString();
d4e5f6a7 src/utils/helpers.js (Bob Wilson 2025-01-15 3) function formatCurrency(amount) {
```

**What this shows:** Lines 1-2 were originally written in `src/old-utils.js` by Jane, then moved to the current file. Line 3 was written directly in this file by Bob.

```bash
# Detect code moved within the same file (-M flag)
git blame -M src/app.js
```

**Real-life use case:** During a refactoring where functions are moved between files, `-C -C` traces the original author of the code, not the person who moved it.

---

## 5.5 Binary Search for Bugs â€” `git bisect`

### What It Does

`git bisect` performs a binary search through your commit history to find the exact commit that introduced a bug. Instead of checking every commit, it halves the search space each time.

### How It Works

If you have 1000 commits between "working" and "broken," checking each one takes up to 1000 steps. Binary search takes at most 10 steps (log2(1000) â‰ˆ 10).

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

## 5.6 Searching Code â€” `git grep`

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

## 5.7 Short Log â€” `git shortlog`

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

