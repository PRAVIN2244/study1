# Module 10 — Administration

## Backup and Restore

### Automated Backup

```bash
# Create backup (Omnibus)
sudo gitlab-backup create

# Backup location: /var/opt/gitlab/backups/
# File: <timestamp>_gitlab_backup.tar

# Also backup configuration files (not included in gitlab-backup)
sudo cp /etc/gitlab/gitlab.rb /backup/
sudo cp /etc/gitlab/gitlab-secrets.json /backup/
```

### Backup Configuration

```ruby
# /etc/gitlab/gitlab.rb

# Backup settings
gitlab_rails['backup_keep_time'] = 604800  # 7 days
gitlab_rails['backup_path'] = "/var/opt/gitlab/backups"

# Upload to S3
gitlab_rails['backup_upload_connection'] = {
  'provider' => 'AWS',
  'region' => 'us-east-1',
  'aws_access_key_id' => 'ACCESS_KEY',
  'aws_secret_access_key' => 'SECRET_KEY'
}
gitlab_rails['backup_upload_remote_directory'] = 'gitlab-backups'
gitlab_rails['backup_multipart_chunk_size'] = 104857600  # 100 MB
```

### Scheduled Backup (Cron)

```bash
# /etc/cron.d/gitlab-backup
0 2 * * * root /opt/gitlab/bin/gitlab-backup create CRON=1
0 3 * * * root cp /etc/gitlab/gitlab.rb /var/opt/gitlab/backups/
0 3 * * * root cp /etc/gitlab/gitlab-secrets.json /var/opt/gitlab/backups/
```

### Restore

```bash
# Stop services that write to the database
sudo gitlab-ctl stop puma
sudo gitlab-ctl stop sidekiq
sudo gitlab-ctl status  # Verify they're stopped

# Restore (specify timestamp)
sudo gitlab-backup restore BACKUP=1704067200_2024_01_01_16.7.0

# Restore configuration files
sudo cp /backup/gitlab.rb /etc/gitlab/
sudo cp /backup/gitlab-secrets.json /etc/gitlab/

# Reconfigure and restart
sudo gitlab-ctl reconfigure
sudo gitlab-ctl restart

# Verify
sudo gitlab-rake gitlab:check SANITIZE=true
```

## Monitoring

### Built-in Monitoring

GitLab bundles Prometheus and Grafana (optional):

```ruby
# /etc/gitlab/gitlab.rb

# Enable Prometheus
prometheus['enable'] = true
prometheus['listen_address'] = '0.0.0.0:9090'

# Enable Grafana
grafana['enable'] = true
grafana['admin_password'] = 'admin'

# Enable exporters
node_exporter['enable'] = true
redis_exporter['enable'] = true
postgres_exporter['enable'] = true
gitlab_exporter['enable'] = true
```

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| CPU usage | Overall CPU utilization | > 80% sustained |
| Memory usage | RAM utilization | > 90% |
| Disk usage | Storage utilization | > 85% |
| Sidekiq queue size | Pending background jobs | > 1000 |
| Puma active threads | Web server load | > 80% capacity |
| Gitaly request latency | Git operation speed | > 1s p95 |
| PostgreSQL connections | DB connection pool | > 80% max |

### Health Check Endpoints

```bash
# Readiness check (all services)
curl https://gitlab.example.com/-/readiness

# Liveness check
curl https://gitlab.example.com/-/liveness

# Specific service health
curl https://gitlab.example.com/-/readiness?all=1
# Returns status of: db, redis, gitaly, cache, queues, shared_state
```

### Log Management

```bash
# View all logs
sudo gitlab-ctl tail

# Specific service logs
sudo gitlab-ctl tail puma
sudo gitlab-ctl tail sidekiq
sudo gitlab-ctl tail gitaly
sudo gitlab-ctl tail nginx

# Log locations
/var/log/gitlab/
├── puma/
│   ├── puma_stdout.log
│   └── puma_stderr.log
├── sidekiq/
│   └── current
├── gitaly/
│   └── current
├── nginx/
│   ├── gitlab_access.log
│   └── gitlab_error.log
├── postgresql/
│   └── current
└── redis/
    └── current
```

### Structured Logging (JSON)

```ruby
# /etc/gitlab/gitlab.rb
# Enable JSON logging for easier parsing
gitlab_rails['log_format'] = 'json'
```

## Scaling GitLab

### Vertical Scaling

Increase resources on a single server:

```ruby
# /etc/gitlab/gitlab.rb

# Increase Puma workers (1 per CPU core)
puma['worker_processes'] = 8

# Increase Sidekiq concurrency
sidekiq['max_concurrency'] = 50

# Increase PostgreSQL resources
postgresql['shared_buffers'] = "2GB"
postgresql['work_mem'] = "128MB"
postgresql['max_connections'] = 200

# Increase Gitaly concurrency
gitaly['configuration'] = {
  concurrency: [
    { rpc: "/gitaly.SmartHTTPService/PostReceivePack", max_per_repo: 20 },
  ],
}
```

### Horizontal Scaling

Separate components onto different servers:

```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
┌──────▼───────┐     ┌──────────────┐
│ GitLab Rails │────▶│ PostgreSQL   │
│ (multiple)   │     │ (Patroni HA) │
└──────┬───────┘     └──────────────┘
       │
       ├────────────▶ Redis (Sentinel)
       │
       ├────────────▶ Gitaly Cluster (Praefect)
       │
       └────────────▶ Object Storage (S3/GCS)
```

### External PostgreSQL

```ruby
# /etc/gitlab/gitlab.rb

# Disable bundled PostgreSQL
postgresql['enable'] = false

# Configure external PostgreSQL
gitlab_rails['db_adapter'] = 'postgresql'
gitlab_rails['db_encoding'] = 'unicode'
gitlab_rails['db_host'] = 'db.example.com'
gitlab_rails['db_port'] = 5432
gitlab_rails['db_database'] = 'gitlabhq_production'
gitlab_rails['db_username'] = 'gitlab'
gitlab_rails['db_password'] = 'password'
```

### External Redis

```ruby
# Disable bundled Redis
redis['enable'] = false

# Configure external Redis
gitlab_rails['redis_host'] = 'redis.example.com'
gitlab_rails['redis_port'] = 6379
gitlab_rails['redis_password'] = 'password'

# Redis Sentinel (HA)
gitlab_rails['redis_sentinels'] = [
  { 'host' => 'sentinel1.example.com', 'port' => 26379 },
  { 'host' => 'sentinel2.example.com', 'port' => 26379 },
  { 'host' => 'sentinel3.example.com', 'port' => 26379 },
]
gitlab_rails['redis_sentinels_password'] = 'sentinel-password'
```

### Object Storage

```ruby
# /etc/gitlab/gitlab.rb

# Consolidated object storage configuration
gitlab_rails['object_store']['enabled'] = true
gitlab_rails['object_store']['connection'] = {
  'provider' => 'AWS',
  'region' => 'us-east-1',
  'aws_access_key_id' => 'ACCESS_KEY',
  'aws_secret_access_key' => 'SECRET_KEY'
}
gitlab_rails['object_store']['objects']['artifacts']['bucket'] = 'gitlab-artifacts'
gitlab_rails['object_store']['objects']['lfs']['bucket'] = 'gitlab-lfs'
gitlab_rails['object_store']['objects']['uploads']['bucket'] = 'gitlab-uploads'
gitlab_rails['object_store']['objects']['packages']['bucket'] = 'gitlab-packages'
gitlab_rails['object_store']['objects']['dependency_proxy']['bucket'] = 'gitlab-dependency-proxy'
gitlab_rails['object_store']['objects']['terraform_state']['bucket'] = 'gitlab-terraform'
gitlab_rails['object_store']['objects']['pages']['bucket'] = 'gitlab-pages'
```

## Upgrades

### Upgrade Path

GitLab requires sequential upgrades through specific versions. Check the upgrade path:
https://docs.gitlab.com/ee/update/index.html#upgrade-paths

```
Example: 14.0 → 14.10 → 15.0 → 15.11 → 16.0 → 16.7 → latest
```

### Upgrade Process (Omnibus)

```bash
# 1. Backup
sudo gitlab-backup create
sudo cp /etc/gitlab/gitlab.rb /backup/
sudo cp /etc/gitlab/gitlab-secrets.json /backup/

# 2. Check current version
sudo gitlab-rake gitlab:env:info

# 3. Update package
sudo apt update
sudo apt install gitlab-ce=<target-version>
# or
sudo yum install gitlab-ce-<target-version>

# 4. Reconfigure (runs migrations)
sudo gitlab-ctl reconfigure

# 5. Verify
sudo gitlab-rake gitlab:check
sudo gitlab-ctl status
```

### Upgrade Process (Docker)

```bash
# 1. Backup
docker exec gitlab gitlab-backup create

# 2. Stop and remove container
docker stop gitlab
docker rm gitlab

# 3. Pull new version
docker pull gitlab/gitlab-ce:<target-version>

# 4. Start with new version
docker run -d \
  --name gitlab \
  --hostname gitlab.example.com \
  -v /srv/gitlab/config:/etc/gitlab \
  -v /srv/gitlab/logs:/var/log/gitlab \
  -v /srv/gitlab/data:/var/opt/gitlab \
  gitlab/gitlab-ce:<target-version>
```

## User and Group Management

### LDAP Integration

```ruby
# /etc/gitlab/gitlab.rb
gitlab_rails['ldap_enabled'] = true
gitlab_rails['ldap_servers'] = {
  'main' => {
    'label' => 'LDAP',
    'host' => 'ldap.example.com',
    'port' => 636,
    'uid' => 'sAMAccountName',
    'encryption' => 'simple_tls',
    'bind_dn' => 'CN=gitlab,OU=Service,DC=example,DC=com',
    'password' => 'bind-password',
    'base' => 'DC=example,DC=com',
    'user_filter' => '(memberOf=CN=GitLabUsers,OU=Groups,DC=example,DC=com)',
    'group_base' => 'OU=Groups,DC=example,DC=com',
    'admin_group' => 'GitLabAdmins',
    'sync_ssh_keys' => false
  }
}
```

### SAML SSO

```ruby
gitlab_rails['omniauth_providers'] = [
  {
    name: "saml",
    label: "Company SSO",
    args: {
      assertion_consumer_service_url: "https://gitlab.example.com/users/auth/saml/callback",
      idp_cert_fingerprint: "XX:XX:XX:...",
      idp_sso_target_url: "https://idp.example.com/sso",
      issuer: "https://gitlab.example.com",
      name_identifier_format: "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    }
  }
]
```

## Troubleshooting

```bash
# Run full diagnostic
sudo gitlab-rake gitlab:check SANITIZE=true

# Check specific components
sudo gitlab-rake gitlab:gitaly:check
sudo gitlab-rake gitlab:sidekiq:check

# Database diagnostics
sudo gitlab-psql -c "SELECT version();"
sudo gitlab-rake db:migrate:status

# Reset admin password
sudo gitlab-rake "gitlab:password:reset[root]"

# Rebuild authorized_keys
sudo gitlab-rake gitlab:shell:setup

# Clear cache
sudo gitlab-rake cache:clear

# Check background migrations
sudo gitlab-rake db:migrate:status | grep down
```
