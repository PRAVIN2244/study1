# MODULE 8: Collaboration Workflows

## 8.1 GitFlow Workflow

GitFlow is a branching model designed for projects with scheduled releases. It defines specific branch types and their purposes.

### Branch Structure

```
main (production)     â”€â”€â”€ v1.0 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ v1.1 â”€â”€â”€â”€â”€â”€â”€â”€ v2.0 â”€â”€â”€
                           â”‚                      â”‚              â”‚
hotfix                     â”‚              hotfix/fix-x           â”‚
                           â”‚                 â”‚    â”‚              â”‚
release                    â”‚         release/1.1â”€â”€â”˜              â”‚
                           â”‚            â”‚                        â”‚
develop               â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€
                              â”‚              â”‚           â”‚
feature                  feature/a      feature/b   feature/c
```

### Branch Types

| Branch | Purpose | Created From | Merges Into |
|--------|---------|-------------|-------------|
| `main` | Production-ready code | â€” | â€” |
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

# Feature complete â€” merge back to develop
git checkout develop
git merge --no-ff feature/user-dashboard -m "Merge feature/user-dashboard"
git branch -d feature/user-dashboard

# === RELEASE PREPARATION ===
# When develop has enough features for a release
git checkout -b release/1.1.0 develop

# Only bug fixes and release prep (version bumps, changelog)
git commit -m "chore: bump version to 1.1.0"
git commit -m "docs: update changelog for 1.1.0"

# Release is ready â€” merge to main AND develop
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

## 8.7 Feature Branching Strategy (Release-Oriented)

Many teams map branching directly to release planning:

1. Keep `main`/`master` as stable baseline.
2. Create a release/integration branch for upcoming release scope (when needed).
3. Create short-lived feature branches for each feature/epic.
4. Merge feature branches back for integration/regression/UAT.
5. Merge tested release content back to stable branch for final release.

### Hotfix Path

For urgent production issues:

1. Create a hotfix/bugfix branch from appropriate stable point.
2. Implement and validate fix quickly.
3. Merge back to stable and required active branches.

### Testing Flow Mapped to Branches

| Testing Phase | Branch | Who |
|---------------|--------|-----|
| Unit testing | Feature branch | Developer |
| Functional testing | Feature branch (build/deploy) | QA |
| Integration / Regression | Release/integration branch (after feature merges) | QA team |
| UAT (User Acceptance) | Release/integration branch | Business / stakeholders |
| Production release | `main`/`master` (after final merge) | Release manager |

Feature branches are tested individually first. After merging into the release/integration branch, combined testing (regression, UAT) validates that features work together before the final merge to `main`.

### Governance Requirement

At organization scale, workflows need branch controls:

- Protect stable branches from direct pushes.
- Restrict who can merge to release/stable branches.
- Enforce freeze windows and approval gates during release phases.

This is the difference between "knowing commands" and operating continuous development safely in production teams.

---

## 8.2 Trunk-Based Development

Trunk-based development uses a single main branch (`main` or `trunk`) with short-lived feature branches. Changes are integrated frequently â€” often multiple times per day.

### Branch Structure

```
main    â”€â”€ A â”€â”€ B â”€â”€ C â”€â”€ D â”€â”€ E â”€â”€ F â”€â”€ G â”€â”€ H â”€â”€ I â”€â”€
               â”‚    â”‚         â”‚    â”‚              â”‚
               â””â”€f1â”€â”˜         â””â”€f2â”€â”˜              â””â”€f3â”€â”˜
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
main:    A â”€â”€ B â”€â”€ C
                    \
feature:             D â”€â”€ E â”€â”€ F â”€â”€ G â”€â”€ H

After squash merge:
main:    A â”€â”€ B â”€â”€ C â”€â”€ DEFGH  (single commit with all changes)
```

### Industry PR Best Practices

1. **Keep PRs small** â€” Under 400 lines of changes. Large PRs get rubber-stamped.
2. **One concern per PR** â€” Don't mix features with refactoring.
3. **Write descriptive titles** â€” `feat(auth): add OAuth2 login` not `Update auth`.
4. **Include context in the description** â€” Why, not just what.
5. **Add screenshots for UI changes**.
6. **Link to tickets/issues** â€” `Closes #123` or `Fixes JIRA-456`.
7. **Respond to review comments promptly**.
8. **Don't force-push after review has started** â€” unless the reviewer asks for a rebase.

---

## 8.4.1 Protected Branches

### What Protected Branches Are

A protected branch is a branch with restricted push access. Platforms like GitHub, GitLab, and Bitbucket allow administrators to enforce rules on specific branches (typically `main`, `production`, or `release/*`).

### Why Protected Branches Matter

Without branch protection, any developer with write access can:
- Push directly to `main`, bypassing code review
- Force-push and rewrite shared history
- Merge code that hasn't passed CI checks

Protected branches prevent these scenarios.

### Common Protection Rules

| Rule | What It Does |
|------|-------------|
| **Require pull request reviews** | Changes must be reviewed and approved before merging |
| **Require status checks to pass** | CI/CD pipelines must succeed before merge is allowed |
| **Require signed commits** | Only GPG-signed commits can be merged |
| **Restrict who can push** | Only specific users or teams can push directly |
| **Prevent force pushes** | Disallows `git push --force` to the branch |
| **Prevent branch deletion** | The branch cannot be deleted |
| **Require linear history** | Only fast-forward merges or rebased commits allowed |

### Setting Up Protected Branches on GitHub

1. Go to **Settings -> Branches -> Branch protection rules**
2. Click **Add rule**
3. Enter the branch name pattern (e.g., `main`)
4. Select the desired protection rules
5. Click **Create**

### Setting Up Protected Branches on GitLab

1. Go to **Settings -> Repository -> Protected Branches**
2. Select the branch (e.g., `main`)
3. Set **Allowed to merge** (e.g., Maintainers only)
4. Set **Allowed to push** (e.g., No one -- forces merge requests)

### Example: Typical Enterprise Configuration

```
Branch: main
  Require pull request reviews: 2 approvals minimum
  Require status checks: CI pipeline must pass
  Require conversation resolution: All comments must be resolved
  Restrict pushes: Only release-managers team
  Prevent force pushes: Enabled
  Prevent deletion: Enabled

Branch: release/*
  Require pull request reviews: 1 approval minimum
  Require status checks: CI + security scan must pass
  Prevent force pushes: Enabled
```

**Real-life use case:** A fintech company protects `main` with 2 required approvals, mandatory CI checks, and security scanning. No developer can merge code that hasn't been reviewed by two peers and passed all automated tests. This prevents accidental deployments of untested code to production.

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

## 8.8 GitLab User Roles and Permissions

On GitLab (and similar platforms), roles control what each team member can do within a project or group.

### Role Summary

| Role | Access Level | Key Capabilities |
|------|-------------|-----------------|
| **Owner** | Full control | Rename/delete project, create subgroups, add/remove users, change visibility |
| **Maintainer** | High-level project management | Merge merge requests, add users, manage CI/CD, create branches |
| **Developer** | Normal contributor | Clone, push, pull, create branches, create merge requests |
| **Reporter** | Read-only access | View code, download repository, create issues (depending on settings) |

### Owner

The Owner has unrestricted access to the project or group.

**Can:**
- Rename or delete the project
- Create subgroups
- Add or remove users at any role level
- Change project visibility (private, internal, public)
- Transfer project ownership

**Example:**
```
Owner deletes project → Project is permanently removed.
Owner changes visibility from private to public → Repository becomes accessible to everyone.
```

### Maintainer

Maintainers handle day-to-day project management without full ownership privileges.

**Can:**
- Merge merge requests
- Add users (up to Maintainer level)
- Manage CI/CD pipelines and variables
- Create and delete branches
- Push to protected branches (if configured)

**Cannot:**
- Delete the project
- Delete the group (unless also an Owner)
- Change project visibility

**Example:**
```bash
# Maintainer merges a merge request via CLI
glab mr merge 42 --squash
```

### Developer

Developers are the standard contributors who write and share code.

**Can:**
- Clone the repository
- Push to non-protected branches
- Pull/fetch changes
- Create branches
- Create merge requests

**Cannot:**
- Delete the project
- Manage users or permissions
- Merge to protected branches directly (requires merge request)

**Example:**
```bash
git clone https://gitlab.com/team/project.git
git checkout -b feature/login
# ... make changes ...
git push origin feature/login
# Create merge request via GitLab UI or CLI
```

### Reporter

Reporters have read-only access, suitable for stakeholders or QA observers.

**Can:**
- View source code and commit history
- Download the repository
- Create issues (depending on project settings)

**Cannot:**
- Push code
- Create branches
- Merge merge requests

### Practical Workflow Mapped to Roles

```
Developer clones repo and creates a feature branch
    ↓
Developer pushes branch and creates Merge Request
    ↓
Maintainer reviews code and merges the Merge Request
    ↓
Owner manages project settings, user access, and visibility
    ↓
Reporter views code and creates issues for bugs found
```

### Role Assignment Example

On GitLab, roles are assigned at the project or group level:

```
Project: payment-service
├── Owner:      Alice (CTO)
├── Maintainer: Bob (Tech Lead)
├── Developer:  Carol, Dave, Eve
└── Reporter:   Frank (QA Observer)
```

Bob (Maintainer) can merge Carol's merge requests but cannot delete the project. Frank (Reporter) can view the code and file issues but cannot push changes.

---

