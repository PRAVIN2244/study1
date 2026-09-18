# Module 07 — Security

## GitHub Security Features Overview

```
┌─────────────────────────────────────────────────────┐
│              GitHub Security                         │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Dependabot  │  │ Code        │  │ Secret     │ │
│  │             │  │ Scanning    │  │ Scanning   │ │
│  │ • Alerts    │  │ • CodeQL    │  │ • Push     │ │
│  │ • Updates   │  │ • SARIF     │  │   protection│ │
│  │ • Security  │  │ • Custom    │  │ • Alerts   │ │
│  │   updates   │  │   queries   │  │ • Partners │ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Security    │  │ Branch      │  │ OIDC       │ │
│  │ Advisories  │  │ Protection  │  │ (Keyless)  │ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Dependabot

### Dependency Alerts

Automatically detects vulnerable dependencies and creates alerts.

**Settings → Security → Code security and analysis → Dependabot alerts: Enable**

### Dependabot Updates

Automatically creates PRs to update dependencies.

```yaml
# .github/dependabot.yml
version: 2
updates:
  # npm dependencies
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "America/New_York"
    open-pull-requests-limit: 10
    reviewers:
      - "team-leads"
    labels:
      - "dependencies"
      - "automated"
    commit-message:
      prefix: "deps"
      include: "scope"
    ignore:
      - dependency-name: "aws-sdk"
        update-types: ["version-update:semver-major"]
    groups:
      dev-dependencies:
        patterns:
          - "@types/*"
          - "eslint*"
          - "prettier"
        update-types:
          - "minor"
          - "patch"

  # Docker base images
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"

  # Python
  - package-ecosystem: "pip"
    directory: "/backend"
    schedule:
      interval: "daily"

  # Go modules
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Dependabot Security Updates

Automatically creates PRs for security vulnerabilities (separate from version updates).

**Settings → Security → Dependabot security updates: Enable**

## Code Scanning (CodeQL)

### Enable CodeQL

```yaml
# .github/workflows/codeql.yml
name: CodeQL Analysis

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'             # Weekly Monday 6 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      actions: read

    strategy:
      fail-fast: false
      matrix:
        language: ['javascript', 'python']
        # Supported: javascript, python, ruby, go, java, csharp, cpp, swift

    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended    # security-extended or security-and-quality

      # For compiled languages, build step is needed
      # - name: Build
      #   run: make build

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### Custom CodeQL Queries

```yaml
- uses: github/codeql-action/init@v3
  with:
    languages: javascript
    queries: |
      security-extended
      ./.github/codeql/custom-queries
    config-file: ./.github/codeql/codeql-config.yml
```

```yaml
# .github/codeql/codeql-config.yml
name: "Custom CodeQL Config"
queries:
  - uses: security-extended
  - uses: ./.github/codeql/custom-queries
paths-ignore:
  - test
  - vendor
  - '**/*.test.js'
```

### Third-Party SARIF Upload

```yaml
# Upload results from any scanner
- name: Run Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    format: 'sarif'
    output: 'trivy-results.sarif'

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
```

## Secret Scanning

### Enable Secret Scanning

**Settings → Security → Code security and analysis → Secret scanning: Enable**

Detects:
- API keys (AWS, Azure, GCP, Stripe, etc.)
- Tokens (GitHub, Slack, npm, etc.)
- Passwords and connection strings
- Private keys
- 200+ partner patterns

### Push Protection

Blocks pushes that contain secrets:

**Settings → Security → Secret scanning → Push protection: Enable**

```
$ git push origin main
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote:
remote: - GITHUB PUSH PROTECTION
remote:   —————————————————————————————————————————
remote:     Resolve the following violations before pushing again
remote:
remote:     — Push cannot contain secrets —
remote:
remote:      (?) To push, you must remove the secret from your commits.
remote:
remote:      locations:
remote:        - commit: abc123
remote:          path: config.js:3
remote:          secret type: AWS Access Key ID
```

### Custom Secret Patterns

**Settings → Security → Code security and analysis → Secret scanning → Custom patterns**

```
Pattern name: Internal API Key
Secret format: MYAPP-[A-Za-z0-9]{32}
Before secret: api_key[=:]\s*["']?
After secret: ["']?
```

## OIDC (OpenID Connect) — Keyless Authentication

Authenticate to cloud providers without storing long-lived credentials.

### AWS OIDC

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write                # Required for OIDC
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: us-east-1
          # No access keys needed!

      - run: aws s3 ls
```

AWS IAM Role trust policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:*"
        }
      }
    }
  ]
}
```

### GCP OIDC

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123456/locations/global/workloadIdentityPools/github/providers/github'
    service_account: 'github-actions@project.iam.gserviceaccount.com'
```

### Azure OIDC

```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

## GITHUB_TOKEN Permissions

### Default Permissions

**Settings → Actions → General → Workflow permissions**

- **Read and write** (default for older repos)
- **Read-only** (recommended)

### Per-Workflow Permissions

```yaml
# Workflow level
permissions:
  contents: read
  pull-requests: write
  issues: write
  packages: write
  security-events: write

# Job level (overrides workflow level)
jobs:
  deploy:
    permissions:
      contents: read
      id-token: write
```

### Permission Reference

| Permission | Read | Write |
|-----------|------|-------|
| `actions` | List workflows | Cancel runs |
| `contents` | Read repo | Push commits |
| `issues` | Read issues | Create/edit issues |
| `packages` | Pull packages | Push packages |
| `pull-requests` | Read PRs | Comment, approve |
| `security-events` | Read alerts | Upload SARIF |
| `id-token` | — | Request OIDC token |
| `deployments` | Read deployments | Create deployments |
| `statuses` | Read statuses | Create statuses |

## Git Security Practices (Developer Level)

Security starts on the developer's machine before code even reaches GitHub.

### 1. Never Commit Secrets

```bash
# BAD — secret hardcoded in code
API_KEY = "sk-abc123def456"

# GOOD — read from environment variable
API_KEY = os.environ.get("API_KEY")
```

**What to never commit:**
```
├── API keys (AWS, GCP, Stripe, etc.)
├── Passwords and database connection strings
├── Private SSH keys (id_rsa, id_ed25519)
├── .env files with secrets
├── TLS/SSL certificates and private keys
├── OAuth client secrets
└── Personal access tokens
```

### 2. Use .gitignore Properly

```bash
# .gitignore — prevent secrets from being staged
.env
.env.local
.env.*.local
*.pem
*.key
*.p12
credentials.json
secrets/
```

**Verify nothing sensitive is staged:**
```bash
git status
git diff --cached    # Review what's about to be committed
```

### 3. Sign Your Commits (GPG/SSH)

Signed commits prove the commit was made by you, not someone impersonating you.

```bash
# Setup GPG signing
gpg --full-generate-key
gpg --list-secret-keys --keyid-format=long
git config --global user.signingkey <KEY_ID>
git config --global commit.gpgsign true

# Or use SSH signing (simpler)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

**Signed commit shows "Verified" badge on GitHub.**

### 4. Use SSH Keys (Not Passwords)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Add public key to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy output → GitHub → Settings → SSH keys → New SSH key

# Test connection
ssh -T git@github.com
```

**Expected output:**
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### 5. Use Credential Manager (Not Plaintext)

```bash
# NEVER store credentials in plaintext
# BAD: credentials stored in ~/.git-credentials

# GOOD: Use credential helper
git config --global credential.helper cache          # Cache for 15 min
git config --global credential.helper store          # Store encrypted
git config --global credential.helper osxkeychain    # macOS keychain

# BEST: Use GitHub CLI
gh auth login    # Handles authentication securely
```

### 6. Review Before Pushing

```bash
# Always review what you're about to push
git log origin/main..HEAD --oneline    # Commits not yet pushed
git diff origin/main..HEAD             # All changes not yet pushed

# Check for secrets in your changes
git diff --cached | grep -iE "(password|secret|key|token|api_key)"
```

### 7. Remove Secrets from Git History

If a secret was accidentally committed:

```bash
# Option 1: BFG Repo-Cleaner (recommended)
bfg --replace-text passwords.txt my-repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force

# Option 2: git filter-repo
git filter-repo --invert-paths --path secrets.env

# IMPORTANT: After removing from history:
# 1. Rotate the exposed secret immediately
# 2. Force push to GitHub
# 3. Contact GitHub support to clear cached views
```

⚠️ **Rotating the secret is mandatory.** Even after removing from history, the secret may have been cloned by others.

## GitHub Platform Security Practices

### 1. Enable Two-Factor Authentication (2FA)

**Settings → Password and authentication → Two-factor authentication**

```
Methods:
├── Authenticator app (TOTP) — recommended
├── SMS (less secure, SIM swap risk)
├── Security keys (FIDO2/WebAuthn) — most secure
└── GitHub Mobile app
```

**For organizations:** Require 2FA for all members.

**Organization → Settings → Authentication security → Require two-factor authentication**

### 2. Use Fine-Grained Personal Access Tokens

```
Settings → Developer settings → Personal access tokens → Fine-grained tokens

Token configuration:
├── Name: ci-deploy-token
├── Expiration: 30 days (never use "No expiration")
├── Repository access: Only select repositories
│   └── my-org/my-app (not "All repositories")
├── Permissions (minimal):
│   ├── Contents: Read-only
│   ├── Metadata: Read-only
│   └── Actions: Read and write
└── Generate token
```

**Classic tokens vs Fine-grained tokens:**

| Feature | Classic Token | Fine-Grained Token |
|---------|--------------|-------------------|
| Repository scope | All repos or public only | Specific repos |
| Permission granularity | Broad scopes | Per-permission |
| Expiration | Optional | Required |
| Approval | Not required | Can require admin approval |
| Audit | Limited | Full audit trail |

Always prefer fine-grained tokens.

### 3. Use GitHub Apps Instead of PATs

For CI/CD and automation, GitHub Apps are more secure than PATs:

```
GitHub App advantages:
├── Scoped to specific repositories
├── Permissions are granular
├── Installation-level access (not user-level)
├── Rate limits are higher (5000 → 15000 req/hr)
├── Tokens auto-expire (1 hour)
└── Audit trail shows app actions separately
```

### 4. Protect Webhooks

```bash
# Always use a webhook secret
# GitHub signs the payload with HMAC-SHA256

# Verify webhook signature in your server:
# Header: X-Hub-Signature-256: sha256=<signature>
```

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 5. Workflow Security Hardening

```yaml
# SECURITY CHECKLIST for every workflow:

# 1. Set minimal permissions at workflow level
permissions:
  contents: read

# 2. Pin actions to full SHA (not tags)
steps:
  - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# 3. Don't use pull_request_target with checkout
# BAD — runs untrusted PR code with write permissions
on: pull_request_target
steps:
  - uses: actions/checkout@v4
    with:
      ref: ${{ github.event.pull_request.head.sha }}  # DANGEROUS

# GOOD — use pull_request (runs in PR context, read-only)
on: pull_request

# 4. Never echo secrets
# BAD
- run: echo ${{ secrets.MY_SECRET }}
# GOOD
- run: ./deploy.sh
  env:
    MY_SECRET: ${{ secrets.MY_SECRET }}

# 5. Use environment protection for production
environment:
  name: production    # Requires approval before running
```

## Security Best Practices Summary

1. **Pin action versions to SHA** — `uses: actions/checkout@abc123` not `@v4`
2. **Use OIDC** instead of long-lived cloud credentials
3. **Minimize GITHUB_TOKEN permissions** — principle of least privilege
4. **Enable secret scanning** with push protection
5. **Enable Dependabot** for all ecosystems
6. **Enable CodeQL** for supported languages
7. **Never use self-hosted runners with public repos**
8. **Use environments** with required reviewers for production
9. **Audit third-party actions** before using them
10. **Use `concurrency`** to prevent parallel deployments

### Secure Workflow Template

```yaml
name: Secure CI/CD

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read                     # Minimal default

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-sha>  # Pinned to SHA
      - uses: actions/setup-node@<full-sha>
        with:
          node-version-file: '.node-version'
      - run: npm ci --ignore-scripts       # Don't run postinstall
      - run: npm test
      - run: npm run build

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      id-token: write                      # Only what's needed
      contents: read
    environment:
      name: production
    concurrency:
      group: deploy-production
      cancel-in-progress: false
    steps:
      - uses: aws-actions/configure-aws-credentials@<full-sha>
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: us-east-1
      - run: ./deploy.sh
```
