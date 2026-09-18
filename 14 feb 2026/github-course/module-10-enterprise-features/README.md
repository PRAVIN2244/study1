# Module 10 — Enterprise Features

## GitHub Enterprise Server (GHES)

### Architecture

```
┌─────────────────────────────────────────────────┐
│              GHES Appliance                      │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Nginx   │  │  Rails   │  │  Git (SSH)   │  │
│  │  (Web)   │  │  (API)   │  │  (Babeld)    │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  MySQL   │  │  Redis   │  │ Elasticsearch│  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Memcached│  │  Minio   │  │  Actions     │  │
│  │          │  │ (Storage) │  │  (Runner Svc)│  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

### Installation

See Module 02 for detailed installation steps. Summary:

1. Download appliance image (OVA, AMI, VHD, GCE)
2. Deploy to hypervisor or cloud
3. Configure via Management Console (`https://<host>:8443/setup`)
4. Upload license
5. Configure authentication, email, storage
6. Create first admin user

### GHES Administration

```bash
# SSH into appliance
ssh -p 122 admin@ghes.example.com

# Common admin commands
ghe-config-apply                     # Apply configuration changes
ghe-maintenance -s                   # Enable maintenance mode
ghe-maintenance -u                   # Disable maintenance mode
ghe-check-disk-usage                 # Check disk usage
ghe-storage-extend                   # Extend storage
ghe-repl-status                      # Check replication status
ghe-update-check                     # Check for updates
ghe-upgrade <package>                # Upgrade GHES
```

### Enable GitHub Actions on GHES

```bash
# SSH into GHES
ssh -p 122 admin@ghes.example.com

# Enable Actions
ghe-config app.actions.enabled true

# Configure external storage (required)
# S3
ghe-config secrets.actions.storage.blob-provider "s3"
ghe-config secrets.actions.storage.s3.bucket-name "ghes-actions"
ghe-config secrets.actions.storage.s3.service-url "https://s3.amazonaws.com"
ghe-config secrets.actions.storage.s3.access-key-id "ACCESS_KEY"
ghe-config secrets.actions.storage.s3.access-secret "SECRET_KEY"

# Azure Blob
# ghe-config secrets.actions.storage.blob-provider "azure"
# ghe-config secrets.actions.storage.azure.connection-string "CONNECTION_STRING"

# Apply
ghe-config-apply
```

## High Availability (GHES)

### Active-Passive Replication

```
┌──────────────┐         ┌──────────────┐
│   Primary    │────────▶│   Replica    │
│   (Active)   │  Async  │  (Passive)   │
│              │  Repl   │              │
│ ghes.example │         │ ghes-replica │
│ .com         │         │ .example.com │
└──────────────┘         └──────────────┘
       │
       │ DNS failover
       ▼
┌──────────────┐
│ Load Balancer│
│ / DNS        │
└──────────────┘
```

### Setup Replication

```bash
# On replica server (after initial GHES install)
ssh -p 122 admin@ghes-replica.example.com

# Configure as replica
ghe-repl-setup ghes.example.com

# Start replication
ghe-repl-start

# Check replication status
ghe-repl-status
# Output:
# OK: mysql replication in sync
# OK: redis replication is in sync
# OK: elasticsearch cluster is in sync
# OK: git replication is in sync
# OK: pages replication is in sync
```

### Failover

```bash
# On replica (during primary failure)
ghe-repl-promote

# Update DNS to point to the promoted replica
# The promoted replica becomes the new primary
```

### Geo-Replication

For geographically distributed teams:

```
┌──────────────┐
│   Primary    │
│  (US-East)   │
└──────┬───────┘
       │
  ┌────┴────┐
  │         │
┌─▼──┐  ┌──▼─┐
│ EU │  │Asia│
│Rep │  │Rep │
└────┘  └────┘

- Read traffic served by nearest replica
- Write traffic forwarded to primary
- Git clone/fetch from nearest replica
```

## Backup and Restore (GHES)

### GitHub Enterprise Backup Utilities

```bash
# Install backup utilities on a separate server
git clone https://github.com/github/backup-utils.git
cd backup-utils

# Configure
cp backup.config-example backup.config
```

```bash
# backup.config
GHE_HOSTNAME="ghes.example.com"
GHE_DATA_DIR="/data/github-backup"
GHE_NUM_SNAPSHOTS=10
GHE_EXTRA_SSH_OPTS="-p 122"
```

```bash
# Run backup
./bin/ghe-backup

# List snapshots
./bin/ghe-backup -l

# Restore (to a new GHES instance)
./bin/ghe-restore -c <snapshot-timestamp>
```

### Automated Backup Schedule

```bash
# /etc/cron.d/ghes-backup
0 */6 * * * root /opt/backup-utils/bin/ghe-backup >> /var/log/ghes-backup.log 2>&1
```

## SAML SSO (Enterprise Cloud)

### Configuration

**Enterprise → Settings → Authentication security → SAML single sign-on**

```
SAML SSO:
  Sign on URL: https://idp.example.com/sso/saml
  Issuer: https://idp.example.com
  Public certificate: (upload IdP certificate)
  Signature method: RSA-SHA256
  Digest method: SHA256
  
  ✓ Require SAML authentication
```

### Supported Identity Providers

| IdP | SAML | SCIM |
|-----|------|------|
| Azure AD (Entra ID) | ✓ | ✓ |
| Okta | ✓ | ✓ |
| OneLogin | ✓ | ✓ |
| PingOne | ✓ | ✓ |
| ADFS | ✓ | ✗ |

### SCIM Provisioning

Automatically sync users and teams from your IdP:

```
SCIM endpoint: https://api.github.com/scim/v2/enterprises/<enterprise>
Authentication: Bearer token (PAT with admin:enterprise scope)

Provisioning:
  ✓ Create users
  ✓ Update user attributes
  ✓ Deactivate users
  ✓ Sync group membership → GitHub teams
```

## Enterprise Managed Users (EMU)

Users are fully managed by the enterprise IdP. No personal GitHub accounts.

```
Enterprise (EMU)
├── Users provisioned via SCIM
│   ├── user1_company (managed)
│   ├── user2_company (managed)
│   └── user3_company (managed)
├── Cannot fork to personal accounts
├── Cannot contribute to external repos
└── Full audit trail
```

### EMU vs Regular Enterprise

| Feature | Regular Enterprise | EMU |
|---------|-------------------|-----|
| User accounts | Personal GitHub accounts | Enterprise-managed |
| External contributions | ✓ | ✗ |
| Fork to personal | ✓ | ✗ |
| IdP provisioning | Optional | Required |
| Account lifecycle | User-managed | Enterprise-managed |

## IP Allow Lists

**Enterprise → Settings → Authentication security → IP allow list**

```
Allow list:
  10.0.0.0/8          Corporate network
  172.16.0.0/12       VPN
  203.0.113.0/24      Office
  
  ✓ Enable IP allow list
  ✓ Enable IP allow list for GitHub Apps
```

## Enterprise Policies

### Repository Policies

```
Enterprise → Policies → Repositories

Base permissions: Read (default for all members)
Repository creation: Members can create public and private
Repository forking: Allow forking of private repos: ✗
Repository visibility change: Only enterprise owners
Repository deletion: Only enterprise owners
```

### Actions Policies

```
Enterprise → Policies → Actions

Enabled organizations: All organizations
Allowed actions: Allow select actions
  ✓ Allow actions created by GitHub
  ✓ Allow Marketplace verified creators
  ✓ Allow specified: docker/*, aws-actions/*

Default workflow permissions: Read-only
```

## Migration

### Migrating to GitHub Enterprise

```bash
# GitHub Enterprise Importer (GEI)
# Install CLI
gh extension install github/gh-gei

# Migrate from GitLab
gh gei migrate-repo \
  --gitlab-source-org "gitlab-group" \
  --source-repo "my-repo" \
  --github-target-org "github-org" \
  --target-repo "my-repo" \
  --gitlab-api-url "https://gitlab.example.com/api/v4"

# Migrate from Azure DevOps
gh gei migrate-repo \
  --ado-source-org "ado-org" \
  --ado-team-project "my-project" \
  --source-repo "my-repo" \
  --github-target-org "github-org" \
  --target-repo "my-repo"

# Migrate from Bitbucket Server
gh gei migrate-repo \
  --bbs-server-url "https://bitbucket.example.com" \
  --bbs-project "PROJ" \
  --source-repo "my-repo" \
  --github-target-org "github-org" \
  --target-repo "my-repo"
```

### What Gets Migrated

| Item | GitHub → GitHub | GitLab → GitHub |
|------|----------------|-----------------|
| Source code + history | ✓ | ✓ |
| Branches + tags | ✓ | ✓ |
| Pull/Merge requests | ✓ | ✓ |
| Issues | ✓ | ✓ (limited) |
| Comments | ✓ | ✓ |
| Labels | ✓ | ✓ |
| Milestones | ✓ | ✓ |
| CI/CD config | ✗ (manual) | ✗ (manual) |
| Webhooks | ✗ | ✗ |
| Secrets | ✗ | ✗ |

## Monitoring GHES

### Built-in Monitoring

**Management Console → Monitor**

```
Dashboard:
├── System health
│   ├── CPU usage
│   ├── Memory usage
│   ├── Disk usage
│   └── Network I/O
├── Service health
│   ├── Web (Nginx/Rails)
│   ├── Git (SSH/HTTP)
│   ├── API
│   └── Actions
└── Performance
    ├── Request latency
    ├── Git operations/sec
    └── Background jobs queue
```

### External Monitoring

```bash
# Health check endpoint
curl -k https://ghes.example.com/api/v3/meta

# Collectd (built-in, forwards to external)
# Management Console → Monitoring → Enable external collectd forwarding
# Host: monitoring.example.com
# Port: 25826

# SNMP monitoring
# Management Console → Monitoring → Enable SNMP
```

### Log Forwarding

```bash
# Forward logs to syslog server
ghe-config log-forwarding.enabled true
ghe-config log-forwarding.protocol "udp"
ghe-config log-forwarding.host "syslog.example.com"
ghe-config log-forwarding.port 514
ghe-config-apply
```

## Upgrade GHES

```bash
# Check current version
ssh -p 122 admin@ghes.example.com -- ghe-version

# Check for updates
ssh -p 122 admin@ghes.example.com -- ghe-update-check

# Download upgrade package
# From: https://enterprise.github.com/releases

# Upload and install
ssh -p 122 admin@ghes.example.com -- ghe-upgrade /tmp/github-enterprise-3.x.x.pkg

# Or hotpatch (minor updates)
ssh -p 122 admin@ghes.example.com -- ghe-upgrade --hotpatch
```

### Upgrade Best Practices

1. **Backup before upgrading** — always
2. **Test on staging** — if you have a test instance
3. **Read release notes** — check for breaking changes
4. **Schedule maintenance window** — upgrades cause brief downtime
5. **Upgrade replicas first** — then primary
6. **Verify after upgrade** — check all services
