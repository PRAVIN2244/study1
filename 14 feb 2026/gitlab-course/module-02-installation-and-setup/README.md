# Module 02 — Installation and Setup

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 4 GB | 8+ GB |
| Disk | 10 GB | 100+ GB (SSD) |
| OS | Ubuntu 20.04+, Debian 11+, RHEL 8+ | Ubuntu 22.04 LTS |
| Database | PostgreSQL 13+ (bundled) | PostgreSQL 14+ |

## Installation Methods

### Method 1: Omnibus Package (Recommended for Production)

The Omnibus package bundles GitLab with all dependencies (PostgreSQL, Redis, Nginx, etc.).

#### Ubuntu/Debian

```bash
# Install dependencies
sudo apt update
sudo apt install -y curl openssh-server ca-certificates tzdata perl postfix

# Add GitLab repository
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | sudo bash

# Install GitLab CE (set your domain)
sudo EXTERNAL_URL="https://gitlab.example.com" apt install -y gitlab-ce

# For Enterprise Edition:
# sudo EXTERNAL_URL="https://gitlab.example.com" apt install -y gitlab-ee
```

#### RHEL/CentOS

```bash
# Install dependencies
sudo yum install -y curl policycoreutils openssh-server openssh-clients postfix
sudo systemctl enable sshd postfix
sudo systemctl start sshd postfix

# Add GitLab repository
curl -sS https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.rpm.sh | sudo bash

# Install
sudo EXTERNAL_URL="https://gitlab.example.com" yum install -y gitlab-ce
```

#### Post-Install

```bash
# Reconfigure (applies settings)
sudo gitlab-ctl reconfigure

# Get initial root password
sudo cat /etc/gitlab/initial_root_password
# Password is auto-generated and valid for 24 hours

# Access GitLab
# Open https://gitlab.example.com
# Login: root / <password from above>
```

### Method 2: Docker

```bash
# Create directories
mkdir -p /srv/gitlab/{config,logs,data}

# Run GitLab
docker run -d \
  --hostname gitlab.example.com \
  --name gitlab \
  --restart always \
  -p 443:443 \
  -p 80:80 \
  -p 2222:22 \
  -v /srv/gitlab/config:/etc/gitlab \
  -v /srv/gitlab/logs:/var/log/gitlab \
  -v /srv/gitlab/data:/var/opt/gitlab \
  --shm-size 256m \
  gitlab/gitlab-ce:latest

# Get root password
docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password
```

### Method 3: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  gitlab:
    image: gitlab/gitlab-ce:latest
    container_name: gitlab
    restart: always
    hostname: gitlab.example.com
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'https://gitlab.example.com'
        gitlab_rails['gitlab_shell_ssh_port'] = 2222
        # Reduce memory usage (optional)
        puma['worker_processes'] = 2
        sidekiq['max_concurrency'] = 10
        postgresql['shared_buffers'] = "256MB"
        prometheus_monitoring['enable'] = false
    ports:
      - '80:80'
      - '443:443'
      - '2222:22'
    volumes:
      - gitlab_config:/etc/gitlab
      - gitlab_logs:/var/log/gitlab
      - gitlab_data:/var/opt/gitlab
    shm_size: '256m'

volumes:
  gitlab_config:
  gitlab_logs:
  gitlab_data:
```

```bash
docker compose up -d
```

### Method 4: Kubernetes (Helm)

```bash
# Add GitLab Helm repo
helm repo add gitlab https://charts.gitlab.io/
helm repo update

# Create namespace
kubectl create namespace gitlab

# Install (minimal configuration)
helm install gitlab gitlab/gitlab \
  --namespace gitlab \
  --set global.hosts.domain=example.com \
  --set global.hosts.externalIP=<your-external-ip> \
  --set certmanager-issuer.email=admin@example.com \
  --set global.edition=ce \
  --set gitlab-runner.install=true

# Get root password
kubectl get secret -n gitlab gitlab-gitlab-initial-root-password \
  -o jsonpath='{.data.password}' | base64 -d
```

## Configuration

### Main Configuration File

```ruby
# /etc/gitlab/gitlab.rb (Omnibus)

## External URL
external_url 'https://gitlab.example.com'

## Email (SMTP)
gitlab_rails['smtp_enable'] = true
gitlab_rails['smtp_address'] = "smtp.gmail.com"
gitlab_rails['smtp_port'] = 587
gitlab_rails['smtp_user_name'] = "gitlab@example.com"
gitlab_rails['smtp_password'] = "app-password"
gitlab_rails['smtp_domain'] = "example.com"
gitlab_rails['smtp_authentication'] = "login"
gitlab_rails['smtp_enable_starttls_auto'] = true
gitlab_rails['gitlab_email_from'] = 'gitlab@example.com'

## SSL/TLS (Let's Encrypt)
letsencrypt['enable'] = true
letsencrypt['contact_emails'] = ['admin@example.com']
letsencrypt['auto_renew'] = true

## SSH
gitlab_rails['gitlab_shell_ssh_port'] = 22

## Time zone
gitlab_rails['time_zone'] = 'UTC'

## Backup
gitlab_rails['backup_keep_time'] = 604800  # 7 days in seconds

## Container Registry
registry_external_url 'https://registry.example.com'

## Pages
pages_external_url 'https://pages.example.com'

## Performance tuning
puma['worker_processes'] = 4
sidekiq['max_concurrency'] = 25
postgresql['shared_buffers'] = "512MB"
```

```bash
# Apply configuration changes
sudo gitlab-ctl reconfigure

# Restart specific services
sudo gitlab-ctl restart nginx
sudo gitlab-ctl restart puma
```

### Essential gitlab-ctl Commands

```bash
# Service management
sudo gitlab-ctl start              # Start all services
sudo gitlab-ctl stop               # Stop all services
sudo gitlab-ctl restart            # Restart all services
sudo gitlab-ctl status             # Check service status
sudo gitlab-ctl reconfigure        # Apply config changes

# Logs
sudo gitlab-ctl tail               # Tail all logs
sudo gitlab-ctl tail nginx         # Tail specific service
sudo gitlab-ctl tail puma          # Application server logs

# Database
sudo gitlab-rake db:migrate        # Run database migrations
sudo gitlab-psql                   # Access PostgreSQL console

# Health check
sudo gitlab-rake gitlab:check      # Run diagnostics
sudo gitlab-rake gitlab:env:info   # Environment info

# User management
sudo gitlab-rake "gitlab:password:reset[root]"  # Reset root password
```

## Firewall Configuration

```bash
# Ubuntu (UFW)
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 22/tcp      # SSH (Git over SSH)
sudo ufw reload

# RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

## Initial Configuration (Web UI)

After first login as root:

1. **Change root password** (if not already done)
2. **Admin Area → Settings → General**
   - Sign-up restrictions: Disable open registration
   - Visibility: Set default project visibility
3. **Admin Area → Settings → CI/CD**
   - Default artifacts expiration: `30 days`
   - Max artifacts size: `100 MB`
4. **Admin Area → Settings → Repository**
   - Default branch name: `main`
5. **Create groups and projects**
6. **Register runners** (see Module 06)
