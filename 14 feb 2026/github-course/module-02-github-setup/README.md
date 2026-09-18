# Module 02 — GitHub Setup

## GitHub.com Setup

### Organization Setup

1. **Create Organization**: github.com → Settings → Organizations → New organization
2. **Configure**:
   - Organization name and email
   - Plan selection (Free/Team/Enterprise)
   - Add members and set roles

### Organization Roles

| Role | Permissions |
|------|------------|
| **Owner** | Full access, billing, settings, delete org |
| **Member** | Create repos, join teams, see members |
| **Billing Manager** | Manage billing only |
| **Outside Collaborator** | Access to specific repos only |

### Team Structure

```
Organization: my-company
├── Team: platform-team (Maintainer access)
│   ├── User A
│   └── User B
├── Team: frontend-team (Write access)
│   ├── User C
│   └── User D
├── Team: backend-team (Write access)
│   ├── User E
│   └── User F
└── Team: security-team (Admin access to security repos)
    └── User G
```

### Repository Settings

**Settings → General:**
- Default branch: `main`
- Features: Issues, Projects, Wiki, Discussions
- Merge button: Squash merging, Rebase merging
- Auto-delete head branches: ✓

**Settings → Branches → Branch protection rules:**

```
Branch: main
├── Require pull request before merging
│   ├── Required approving reviews: 2
│   ├── Dismiss stale reviews: ✓
│   └── Require review from code owners: ✓
├── Require status checks to pass
│   ├── Require branches to be up to date: ✓
│   └── Status checks: ci/tests, ci/lint
├── Require signed commits: ✓ (optional)
├── Include administrators: ✓
└── Restrict who can push: team-leads
```

## GitHub Enterprise Server (GHES) Installation

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| vCPUs | 4 | 8+ |
| RAM | 32 GB | 64+ GB |
| Root storage | 200 GB (SSD) | 200 GB (SSD) |
| Data storage | 100 GB (SSD) | 500+ GB (SSD) |
| OS | Custom appliance (OVA/AMI/Azure/GCP) | — |

### Installation on VMware/Hyper-V

1. **Download OVA**: enterprise.github.com → Download trial
2. **Import OVA** into VMware/Hyper-V
3. **Configure networking**: Static IP recommended
4. **Access setup**: `https://<hostname>:8443/setup`
5. **Upload license**: Upload your `.ghl` license file
6. **Configure**:
   - Hostname and SSL
   - Authentication (LDAP, SAML, CAS)
   - Email (SMTP)
   - Storage
7. **Save settings** → Appliance configures itself

### Installation on AWS

```bash
# Launch from AWS Marketplace or use AMI
# Instance type: r5.2xlarge or larger

# After launch, access:
# https://<public-ip>:8443/setup

# Configure via Management Console
# Or use the API:
curl -X PUT "https://<hostname>:8443/setup/api/settings" \
  -H "Authorization: api_key <setup-password>" \
  -d @settings.json
```

### Installation on Azure

```bash
# Deploy from Azure Marketplace
# VM size: Standard_E4s_v3 or larger

# Attach data disk (Premium SSD)
# Configure networking (NSG rules for 22, 80, 443, 8443, 9418)
```

### GHES Configuration

```bash
# SSH into appliance (admin shell)
ssh -p 122 admin@<hostname>

# Management console
ghe-config --list                    # View all settings
ghe-config core.hostname             # View specific setting
ghe-config core.hostname "ghes.example.com"  # Set value
ghe-config-apply                     # Apply changes

# Service management
ghe-service-list                     # List services
ghe-service-status                   # Service status

# Diagnostics
ghe-diagnostics                      # Generate diagnostic bundle
ghe-support-bundle                   # Generate support bundle
```

### GHES Networking

```
Required ports:
├── 22    → SSH (Git over SSH + admin)
├── 25    → SMTP (outbound)
├── 80    → HTTP (redirects to HTTPS)
├── 122   → Admin SSH
├── 443   → HTTPS (web + API + Git)
├── 8443  → Management Console (HTTPS)
├── 8080  → Management Console (HTTP)
└── 9418  → Git protocol (optional)
```

## GitHub Enterprise Cloud Setup

### SAML SSO

**Organization → Settings → Authentication security → SAML single sign-on**

Supported IdPs:
- Azure AD
- Okta
- OneLogin
- PingOne

```
SAML Configuration:
  Sign on URL: https://idp.example.com/sso/saml
  Issuer: https://idp.example.com
  Public certificate: (paste IdP certificate)
  Signature method: RSA-SHA256
  Digest method: SHA256
```

### SCIM Provisioning

Automatically sync users from your IdP:

```
SCIM endpoint: https://api.github.com/scim/v2/organizations/<org>
Bearer token: (generate in GitHub)
```

### IP Allow Lists

**Organization → Settings → Authentication security → IP allow list**

```
Allow list entries:
  10.0.0.0/8        Office network
  192.168.1.0/24    VPN
  203.0.113.50/32   CI/CD server
```

## GitHub CLI (gh)

```bash
# Install
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli-stable.list > /dev/null
sudo apt update && sudo apt install gh

# Authenticate
gh auth login

# Common commands
gh repo create my-repo --public
gh repo clone owner/repo
gh pr create --title "My PR" --body "Description"
gh pr list
gh pr merge 42
gh issue create --title "Bug" --body "Description"
gh workflow run ci.yml
gh run list
gh run view <run-id>
gh secret set MY_SECRET
```

## Personal Access Tokens (PAT)

**Settings → Developer settings → Personal access tokens → Fine-grained tokens**

```
Token name: ci-token
Expiration: 90 days
Repository access: Selected repositories
Permissions:
  ├── Contents: Read and write
  ├── Pull requests: Read and write
  ├── Actions: Read and write
  ├── Packages: Read and write
  └── Metadata: Read-only
```

## Webhooks

**Repository → Settings → Webhooks → Add webhook**

```
Payload URL: https://ci.example.com/webhook
Content type: application/json
Secret: (shared secret for verification)
Events:
  ├── Push
  ├── Pull request
  ├── Workflow run
  └── Release
```

### Webhook Payload Verification

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```
