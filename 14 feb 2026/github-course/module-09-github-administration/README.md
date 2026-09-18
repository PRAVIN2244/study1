# Module 09 — GitHub Administration

## Organization Management

### Organization Structure

```
Enterprise Account (optional)
├── Organization: my-company
│   ├── Team: engineering
│   │   ├── Team: frontend (nested)
│   │   ├── Team: backend (nested)
│   │   └── Team: devops (nested)
│   ├── Team: security
│   ├── Team: qa
│   └── Repositories
│       ├── frontend-app (Team: frontend → Write)
│       ├── backend-api (Team: backend → Write)
│       ├── infrastructure (Team: devops → Admin)
│       └── shared-libs (Team: engineering → Write)
```

### Repository Permissions

| Permission | Capabilities |
|-----------|-------------|
| **Read** | Clone, view code, open issues |
| **Triage** | Manage issues and PRs (no code write) |
| **Write** | Push code, manage issues/PRs |
| **Maintain** | Manage repo settings (no destructive actions) |
| **Admin** | Full access including settings, delete |

### Team Permissions

```
Team: backend
├── Repository: backend-api → Write
├── Repository: shared-libs → Read
└── Repository: docs → Write

Team: devops
├── Repository: infrastructure → Admin
├── Repository: backend-api → Maintain
└── Repository: frontend-app → Maintain
```

## Branch Protection Rules

**Settings → Branches → Add branch protection rule**

```yaml
# Rulesets (newer, more flexible than branch protection rules)
# Settings → Rules → Rulesets → New ruleset

Ruleset: Production Protection
Target: main, release/*
Enforcement: Active

Rules:
  - Restrict deletions
  - Require linear history
  - Require pull request:
      Required approvals: 2
      Dismiss stale reviews: true
      Require review from code owners: true
      Require approval of most recent push: true
  - Require status checks:
      - ci/tests
      - ci/lint
      - security/codeql
      Require branches to be up to date: true
  - Require signed commits
  - Block force pushes
  - Require deployments to succeed:
      - staging
```

## CODEOWNERS

```
# .github/CODEOWNERS

# Default owners
* @my-org/engineering

# Frontend
/frontend/                @my-org/frontend
*.tsx                     @my-org/frontend
*.css                     @my-org/frontend

# Backend
/backend/                 @my-org/backend
*.go                      @my-org/backend

# Infrastructure
/terraform/               @my-org/devops
/k8s/                     @my-org/devops
Dockerfile                @my-org/devops
docker-compose*.yml       @my-org/devops

# CI/CD
/.github/                 @my-org/devops
.github/workflows/        @my-org/devops @my-org/security

# Security-sensitive
/auth/                    @my-org/security
**/security*              @my-org/security

# Documentation
/docs/                    @my-org/docs-team
*.md                      @my-org/docs-team
```

## Actions Policies

### Organization-Level Actions Settings

**Organization → Settings → Actions → General**

```
Actions permissions:
  ○ Allow all actions and reusable workflows
  ● Allow select actions and reusable workflows
    ✓ Allow actions created by GitHub
    ✓ Allow actions by Marketplace verified creators
    ✓ Allow specified actions and reusable workflows:
      docker/*, aws-actions/*, hashicorp/*

Default workflow permissions:
  ● Read repository contents and packages permissions
  ○ Read and write permissions
  ☐ Allow GitHub Actions to create and approve pull requests

Runner groups:
  Default → All repositories
  Production → Selected repositories only
```

### Required Workflows (Enterprise)

Force specific workflows to run on all repositories:

```yaml
# Required workflow (runs on every push/PR in the org)
name: Required Security Scan

on:
  push:
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
      - uses: github/codeql-action/analyze@v3
```

## Audit Log

### Viewing Audit Log

**Organization → Settings → Audit log**

Key events:
- `repo.create` / `repo.destroy`
- `org.add_member` / `org.remove_member`
- `team.add_repository` / `team.remove_repository`
- `protected_branch.create` / `protected_branch.update`
- `action.disable` / `action.enable`
- `oauth_application.create`
- `secret_scanning_alert.create`

### Audit Log API

```bash
# Query audit log
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/audit-log?phrase=action:repo.create&per_page=100"

# Stream to SIEM
# Enterprise Cloud supports streaming to:
# - Splunk
# - Azure Event Hubs
# - Amazon S3
# - Google Cloud Storage
# - Datadog
```

## Billing and Usage

### Actions Usage

**Organization → Settings → Billing → Actions**

```
Usage this month:
├── Ubuntu: 1,500 / 3,000 minutes
├── Windows: 200 / 3,000 minutes (2x multiplier = 400 minutes)
├── macOS: 50 / 3,000 minutes (10x multiplier = 500 minutes)
└── Total: 1,900 / 3,000 included minutes

Spending limit: $50/month
```

### Cost Multipliers

| Runner OS | Multiplier |
|-----------|-----------|
| Linux | 1x |
| Windows | 2x |
| macOS | 10x |

### Cost Optimization

1. **Use Linux runners** when possible (1x cost)
2. **Cache dependencies** to reduce build time
3. **Use `paths` filter** to skip unnecessary runs
4. **Cancel redundant runs** with `concurrency`
5. **Use self-hosted runners** for high-volume repos
6. **Set spending limits** to prevent surprises
7. **Monitor usage** with billing API

```bash
# Check Actions usage via API
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/settings/billing/actions"
```

## GitHub Apps

### Creating a GitHub App

**Organization → Settings → Developer settings → GitHub Apps → New GitHub App**

```
App name: My CI Bot
Homepage URL: https://example.com
Webhook URL: https://ci.example.com/webhook
Webhook secret: (generate random string)

Permissions:
  Repository:
    Contents: Read
    Pull requests: Read & Write
    Checks: Read & Write
    Actions: Read
  Organization:
    Members: Read

Events:
  ✓ Pull request
  ✓ Push
  ✓ Check run
```

### Using GitHub App in Actions

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Generate token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ vars.APP_ID }}
          private-key: ${{ secrets.APP_PRIVATE_KEY }}

      - uses: actions/checkout@v4
        with:
          token: ${{ steps.app-token.outputs.token }}

      - name: Create PR
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: gh pr create --title "Automated update" --body "..."
```

## Repository Templates

Create template repositories for standardized project setup:

**Settings → Template repository: ✓**

Template includes:
- Directory structure
- `.github/workflows/` (CI/CD)
- `.github/CODEOWNERS`
- `.github/dependabot.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`
- Standard config files (`.eslintrc`, `tsconfig.json`, etc.)

```bash
# Create repo from template
gh repo create my-new-project --template my-org/project-template
```

## Webhooks Management

### Organization Webhooks

**Organization → Settings → Webhooks**

```bash
# Create webhook via API
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/hooks" \
  -d '{
    "name": "web",
    "active": true,
    "events": ["push", "pull_request", "workflow_run"],
    "config": {
      "url": "https://ci.example.com/webhook",
      "content_type": "json",
      "secret": "webhook-secret",
      "insecure_ssl": "0"
    }
  }'
```

### Webhook Deliveries

Monitor webhook delivery status:

**Organization → Settings → Webhooks → (webhook) → Recent Deliveries**

Each delivery shows:
- Request headers and payload
- Response status code and body
- Delivery time
- Option to redeliver

---

## GitHub Admin Security Practices

### Security Checklist for Organization Admins

```
Organization Security Setup
│
├── 1. Authentication
│   ├── Require 2FA for all members                    ✅ Must do
│   ├── Configure SAML SSO (Enterprise)                ✅ If available
│   ├── Enable SCIM provisioning                       ✅ Auto-sync users
│   └── Set session timeout                            ✅ 8 hours max
│
├── 2. Access Control
│   ├── Set base permission to "Read" (not Write)      ✅ Least privilege
│   ├── Disable forking of private repos               ✅ Prevent data leak
│   ├── Restrict repo creation to admins               ⚠️  Depends on team
│   ├── Restrict repo visibility changes               ✅ Prevent accidental public
│   └── Restrict repo deletion to owners               ✅ Prevent accidents
│
├── 3. Branch Protection
│   ├── Protect main/production branches               ✅ Must do
│   ├── Require PR reviews (2+ approvals)              ✅ Must do
│   ├── Require status checks to pass                  ✅ Must do
│   ├── Require signed commits                         ⚠️  If feasible
│   ├── Block force pushes                             ✅ Must do
│   └── Require CODEOWNERS review                      ✅ For sensitive paths
│
├── 4. Code Security
│   ├── Enable Dependabot alerts                       ✅ Must do
│   ├── Enable Dependabot security updates             ✅ Must do
│   ├── Enable secret scanning                         ✅ Must do
│   ├── Enable push protection                         ✅ Must do
│   ├── Enable CodeQL analysis                         ✅ For supported languages
│   └── Enable dependency review                       ✅ On PRs
│
├── 5. Actions Security
│   ├── Restrict allowed actions                       ✅ Only verified creators
│   ├── Set default token permissions to read-only     ✅ Must do
│   ├── Disable Actions on fork PRs (public repos)     ✅ Prevent abuse
│   └── Use runner groups for sensitive repos           ✅ If self-hosted
│
└── 6. Monitoring
    ├── Review audit log regularly                     ✅ Weekly
    ├── Set up audit log streaming (Enterprise)        ✅ To SIEM
    ├── Monitor for unusual activity                   ✅ Failed logins, new admins
    └── Review outside collaborators quarterly          ✅ Remove stale access
```

### Configuring Organization Security Settings

**Step-by-step in the UI:**

#### Authentication Security

**Organization → Settings → Authentication security**

```
Two-factor authentication:
  ☑ Require two-factor authentication for everyone in the organization
  → Members without 2FA will be removed from the org

SAML single sign-on (Enterprise):
  ☑ Enable SAML authentication
  ☑ Require SAML SSO authentication for all members

Session policy:
  Session timeout: 8 hours
  ☑ Require re-authentication for sensitive operations
```

#### Member Privileges

**Organization → Settings → Member privileges**

```
Base permissions:
  ● Read (recommended)
  ○ Write
  ○ Admin
  ○ None

Repository forking:
  ☐ Allow forking of private repositories

Repository creation:
  ☐ Allow members to create public repositories
  ☑ Allow members to create private repositories
  ☐ Allow members to create internal repositories

Repository visibility change:
  ☐ Allow members to change repository visibility

Repository deletion and transfer:
  ☐ Allow members to delete or transfer repositories

Pages creation:
  ● Public (only public repos can have Pages)
```

#### Actions Permissions

**Organization → Settings → Actions → General**

```
Actions permissions:
  ● Allow select actions and reusable workflows
    ☑ Allow actions created by GitHub
    ☑ Allow actions by Marketplace verified creators
    ☑ Allow specified actions:
      aws-actions/*, docker/*, hashicorp/*, actions/*

Default workflow permissions:
  ● Read repository contents and packages permissions
  ☐ Allow GitHub Actions to create and approve pull requests
```

### Audit Log Monitoring

**Organization → Settings → Audit log**

Key events to monitor:

| Event | What It Means | Severity |
|-------|--------------|----------|
| `org.add_member` | New member added | Info |
| `org.remove_member` | Member removed | Info |
| `repo.create` | New repository created | Info |
| `repo.destroy` | Repository deleted | High |
| `repo.access` | Repository visibility changed | High |
| `protected_branch.destroy` | Branch protection removed | High |
| `org.update_member_repository_permission` | Permission changed | Medium |
| `org.disable_two_factor_requirement` | 2FA requirement disabled | Critical |
| `oauth_application.create` | OAuth app authorized | Medium |
| `integration_installation.create` | GitHub App installed | Medium |

```bash
# Query audit log via API
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/audit-log?phrase=action:repo.destroy&per_page=10"
```

**Expected output:**
```json
[
  {
    "action": "repo.destroy",
    "actor": "username",
    "repo": "my-org/deleted-repo",
    "created_at": 1704067200000,
    "@timestamp": 1704067200000
  }
]
```

---

## How to Give Limited Access to a GitHub User

### Scenario 1: External Contractor Needs Access to One Repo

**Do NOT add them as an org member.** Add them as an outside collaborator.

```
Repository → Settings → Collaborators → Add people

Username: contractor-jane
Permission: Read (or Write if they need to push)
```

**What they can do (Read):**
```
✅ Clone the repository
✅ View code, issues, PRs
✅ Fork the repository (if allowed)
✅ Open issues
❌ Push code
❌ Merge PRs
❌ Change settings
❌ See other org repos
```

**What they can do (Write):**
```
✅ Everything in Read
✅ Push to non-protected branches
✅ Create branches
✅ Open and merge PRs (if no review required)
❌ Push to protected branches
❌ Change repo settings
❌ See other org repos
```

### Scenario 2: Junior Developer Needs Limited Access

Create a team with restricted permissions:

```bash
# Step 1: Create a team
# Organization → Teams → New team
Team name: junior-developers
Visibility: Visible
Parent team: engineering (optional)

# Step 2: Add repositories with specific permissions
# Team → Repositories → Add repository
Repository: frontend-app → Write
Repository: shared-libs → Read
Repository: infrastructure → (no access)

# Step 3: Add the user to the team
# Team → Members → Add member
Username: junior-dev-john
Role: Member (not Maintainer)
```

**Result:**
```
junior-dev-john can:
├── frontend-app: Push code, create PRs, manage issues
├── shared-libs: Clone and read only
├── infrastructure: Cannot see this repo at all
└── Other repos: Read-only (base permission)
```

### Scenario 3: Read-Only Access for Auditor/Manager

```
# Option 1: Outside collaborator with Read
Repository → Settings → Collaborators → Add people
Permission: Read

# Option 2: Team with Read-only access
Team: auditors
├── All repos → Read
└── Members: auditor-user
```

### Scenario 4: CI/CD Bot Needs Specific Permissions

Use a GitHub App or fine-grained PAT (not a user account):

```
Fine-grained PAT:
├── Repository access: Only select repositories
│   └── my-org/my-app
├── Permissions:
│   ├── Contents: Read and write (push code)
│   ├── Pull requests: Read and write (create PRs)
│   ├── Actions: Read (view workflow runs)
│   └── Metadata: Read-only
└── Expiration: 30 days
```

### Scenario 5: Restrict Who Can Deploy to Production

Use environment protection rules:

```
Repository → Settings → Environments → production

Protection rules:
├── Required reviewers: @team-leads, @devops-team
│   (up to 6 reviewers, any 1 must approve)
├── Wait timer: 15 minutes
│   (delay before deployment starts)
├── Deployment branches:
│   ● Selected branches
│   └── main (only main can deploy to production)
└── Environment secrets:
    ├── AWS_ACCESS_KEY_ID (only available in production env)
    └── AWS_SECRET_ACCESS_KEY
```

**Result:**
```
Developer pushes to main
    │
    ▼
CI pipeline runs (build, test)
    │
    ▼
Deploy job reaches "production" environment
    │
    ▼
⏸️  PAUSED — Waiting for approval
    │
    ▼
Team lead approves in GitHub UI
    │
    ▼
15-minute wait timer
    │
    ▼
Deployment proceeds
```

### Permission Comparison Table

| Role | See Repo | Clone | Push | Merge PR | Settings | Delete |
|------|----------|-------|------|----------|----------|--------|
| **No access** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Read** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Triage** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Write** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Maintain** | ✅ | ✅ | ✅ | ✅ | ⚠️ partial | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Triage vs Read:** Triage can manage issues/PRs (assign, label, close) but cannot push code.
**Maintain vs Admin:** Maintain can manage most settings but cannot delete the repo, manage access, or change visibility.

### Revoking Access

```bash
# Remove outside collaborator
curl -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/my-org/my-repo/collaborators/username"

# Remove from team
curl -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/teams/team-name/memberships/username"

# Remove from organization
curl -X DELETE \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/members/username"

# Revoke PAT (user must do this themselves, or admin can via Enterprise)
# Settings → Developer settings → Personal access tokens → Revoke
```

---

## How to Save / Protect a GitHub Repository

### 1. Branch Protection Rules

Prevent accidental or unauthorized changes to important branches.

**Repository → Settings → Branches → Add branch protection rule**

```
Branch name pattern: main

☑ Require a pull request before merging
  ├── Required approving reviews: 2
  ├── ☑ Dismiss stale pull request approvals when new commits are pushed
  ├── ☑ Require review from Code Owners
  └── ☑ Require approval of the most recent reviewable push

☑ Require status checks to pass before merging
  ├── ☑ Require branches to be up to date before merging
  └── Status checks: ci/test, ci/lint, security/codeql

☑ Require conversation resolution before merging

☑ Require signed commits

☑ Require linear history (no merge commits)

☐ Require merge queue

☑ Do not allow bypassing the above settings
  └── Even admins must follow these rules

☑ Restrict who can push to matching branches
  └── Only: deploy-bot, release-team

☑ Block force pushes

☑ Restrict deletions
```

**What this prevents:**
```
❌ Direct push to main (must use PR)
❌ Merge without 2 approvals
❌ Merge with failing tests
❌ Force push (rewriting history)
❌ Branch deletion
❌ Unsigned commits
❌ Bypassing rules (even for admins)
```

### 2. CODEOWNERS File

Automatically require specific people to review changes to specific files.

```
# .github/CODEOWNERS

# Default — all changes need engineering review
* @my-org/engineering

# Frontend changes need frontend team review
/frontend/          @my-org/frontend-team
*.tsx               @my-org/frontend-team
*.css               @my-org/frontend-team

# Backend changes need backend team review
/backend/           @my-org/backend-team
*.go                @my-org/backend-team

# Infrastructure changes need devops AND security review
/terraform/         @my-org/devops @my-org/security
/k8s/               @my-org/devops
Dockerfile          @my-org/devops
docker-compose*.yml @my-org/devops

# CI/CD changes need devops review
/.github/           @my-org/devops
.github/workflows/  @my-org/devops @my-org/security

# Security-sensitive files need security team
/auth/              @my-org/security
**/security*        @my-org/security
*.pem               @my-org/security
*.key               @my-org/security

# Documentation
/docs/              @my-org/docs-team
*.md                @my-org/docs-team
```

**How it works:**
```
Developer modifies /terraform/main.tf
    │
    ▼
Opens Pull Request
    │
    ▼
GitHub automatically requests review from:
├── @my-org/devops (matches /terraform/)
└── @my-org/security (matches /terraform/)
    │
    ▼
PR cannot be merged until BOTH teams approve
```

### 3. Repository Rulesets (Newer, More Flexible)

**Repository → Settings → Rules → Rulesets → New ruleset**

```yaml
Ruleset: Production Protection
Enforcement: Active
Bypass list: (none — no one can bypass)

Target branches:
  - main
  - release/*

Rules:
  - Restrict creations          # Can't create matching branches
  - Restrict updates            # Can't push directly
  - Restrict deletions          # Can't delete branches
  - Require pull request:
      Required approvals: 2
      Dismiss stale reviews: true
      Require code owner review: true
      Require last push approval: true
  - Require status checks:
      - ci/test
      - ci/lint
      - security/scan
  - Require signed commits
  - Block force pushes
  - Require linear history
```

### 4. Backup Your Repository

#### Method 1: Git Clone (Simple)

```bash
# Full clone with all branches and tags
git clone --mirror https://github.com/my-org/my-repo.git my-repo-backup.git

# Schedule daily backup
# /etc/cron.d/github-backup
0 2 * * * root cd /backup && git clone --mirror https://github.com/my-org/my-repo.git my-repo-$(date +\%Y\%m\%d).git
```

#### Method 2: GitHub API Export

```bash
# Export repository metadata (issues, PRs, wiki)
# Use GitHub's migration API

# Start migration
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/migrations" \
  -d '{
    "repositories": ["my-org/my-repo"],
    "lock_repositories": false
  }'

# Check migration status
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/migrations/<migration-id>"

# Download archive when ready
curl -L -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/orgs/my-org/migrations/<migration-id>/archive" \
  -o backup.tar.gz
```

**What's included in the archive:**
```
backup.tar.gz
├── repositories/
│   └── my-repo.git          # Full Git history
├── issues/                   # All issues with comments
├── pull_requests/            # All PRs with reviews
├── releases/                 # Release metadata
├── labels/                   # Issue labels
├── milestones/               # Milestones
└── webhooks/                 # Webhook configurations
```

#### Method 3: Third-Party Backup Tools

```bash
# github-backup (Python tool)
pip install github-backup
github-backup my-org \
  --token $GITHUB_TOKEN \
  --output-directory /backup/github \
  --repositories \
  --issues \
  --pull-requests \
  --wikis \
  --releases

# BackHub (SaaS — automatic daily backups)
# Rewind.io (SaaS — continuous backup with restore)
```

#### Method 4: Mirror to Another Git Host

```bash
# Mirror to GitLab as backup
git clone --mirror https://github.com/my-org/my-repo.git
cd my-repo.git
git remote add gitlab https://gitlab.com/my-org/my-repo-mirror.git
git push --mirror gitlab

# Automate with GitHub Actions
```

```yaml
# .github/workflows/mirror.yml
name: Mirror to GitLab

on:
  push:
    branches: ['**']
  delete:

jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Mirror to GitLab
        run: |
          git remote add mirror https://oauth2:${{ secrets.GITLAB_TOKEN }}@gitlab.com/my-org/my-repo.git
          git push --mirror mirror
```

### 5. Prevent Repository Deletion

**Organization → Settings → Member privileges**

```
Repository deletion and transfer:
  ☐ Allow members to delete or transfer repositories
  → Only organization owners can delete repos
```

**For extra protection (Enterprise):**
```
Enterprise → Policies → Repositories
  Repository deletion: Only enterprise owners
  Repository visibility change: Only enterprise owners
```

### 6. Archive a Repository

If a repo is no longer active but should be preserved:

**Repository → Settings → General → Danger Zone → Archive this repository**

```
Archived repository:
├── ✅ Code is still readable and cloneable
├── ✅ Issues and PRs are visible (read-only)
├── ✅ Appears in search results
├── ❌ No new pushes
├── ❌ No new issues or PRs
├── ❌ No new comments
└── ❌ No webhook deliveries
```

```bash
# Archive via API
curl -X PATCH \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/my-org/my-repo" \
  -d '{"archived": true}'
```

### Repository Protection Summary

| Protection | What It Prevents | How to Enable |
|-----------|-----------------|---------------|
| **Branch protection** | Direct pushes, force pushes, deletion | Settings → Branches |
| **CODEOWNERS** | Merging without owner approval | `.github/CODEOWNERS` file |
| **Rulesets** | Bypassing any protection rule | Settings → Rules |
| **Required reviews** | Merging without peer review | Branch protection rule |
| **Status checks** | Merging with failing CI | Branch protection rule |
| **Signed commits** | Impersonation, unsigned code | Branch protection rule |
| **Restrict deletion** | Accidental repo deletion | Org settings |
| **Archive** | Changes to inactive repos | Settings → Danger Zone |
| **Backup** | Data loss from any cause | Cron + git clone --mirror |
| **Mirror** | Single point of failure | GitHub Actions workflow |
