# Module 26: Cloud, CI/CD, and Automation

## 12.17 cloud-init — Cloud Instance Initialization

`cloud-init` runs during the first boot of a cloud VM to configure hostname, users, SSH keys, packages, and run commands.

### Example cloud-init user-data

```yaml
#cloud-config
hostname: devserver

users:
  - name: devops
    groups: sudo
    shell: /bin/bash
    ssh-authorized-keys:
      - ssh-rsa AAAA...

packages:
  - nginx
  - git
  - htop

runcmd:
  - systemctl enable nginx
  - systemctl start nginx
```

Attach this as user-data when launching an EC2 instance, GCP VM, or Azure VM.

```bash
# Debug cloud-init
cat /var/log/cloud-init.log
cat /var/log/cloud-init-output.log

# Check cloud-init status
cloud-init status

# Re-run cloud-init (for testing)
sudo cloud-init clean
sudo cloud-init init
```

### Real-world use case

When launching an autoscaling group in AWS, every new instance uses cloud-init to:
- Install application dependencies
- Pull code from a repository
- Register with a load balancer
- Start the application service

---

## 12.18 Linux in CI/CD Pipelines

Most CI/CD systems (GitHub Actions, GitLab CI, Jenkins) run on Linux. Bash scripts power the core execution blocks.

### Example deployment script

```bash
#!/bin/bash
set -euo pipefail

echo "=== Building application ==="
npm install
npm run build

echo "=== Running tests ==="
npm test

echo "=== Building Docker image ==="
docker build -t myapp:${BUILD_NUMBER:-latest} .

echo "=== Pushing to registry ==="
docker push myrepo/myapp:${BUILD_NUMBER:-latest}

echo "=== Deploying to cluster ==="
kubectl apply -f k8s/deployment.yaml

echo "=== Deployment complete ==="
```

### Best practices for CI/CD scripts

- Always use `set -euo pipefail` to fail on errors
- Use `trap` for cleanup on exit
- Log all output with timestamps
- Use environment variables for configs (image names, branch, region)
- Validate inputs before proceeding

```bash
# Validate required variables
: "${DOCKER_REGISTRY:?DOCKER_REGISTRY is required}"
: "${DEPLOY_ENV:?DEPLOY_ENV must be set to staging or production}"
```

---

## 12.19 Backup and Recovery

### rsync — Efficient File Synchronization

```bash
# Local sync
rsync -av /source/ /backup/

# Remote sync over SSH
rsync -avz -e ssh /etc/ user@remote:/backup/etc/

# Dry run (preview changes)
rsync -avn /source/ /backup/

# Delete files in destination that don't exist in source
rsync -av --delete /source/ /backup/
```

### tar — Archive and Compress

```bash
# Create compressed archive
tar -czvf backup-$(date +%F).tar.gz /etc /var/log

# Extract archive
tar -xzvf backup.tar.gz

# List contents without extracting
tar -tzvf backup.tar.gz
```

### dd — Block-Level Disk Imaging

```bash
# Create full disk image
sudo dd if=/dev/sda of=/mnt/backup/sda.img bs=4M status=progress

# Restore disk image
sudo dd if=/mnt/backup/sda.img of=/dev/sda bs=4M
```

⚠️ `dd` is powerful but dangerous — wrong `of=` target can overwrite critical data.

### scp — Secure Copy

```bash
# Copy file to remote
scp backup.tar.gz user@remote:/backups/

# Copy directory recursively
scp -r /etc user@remote:/backups/etc

# Copy from remote to local
scp user@remote:/var/log/syslog ./syslog-backup
```

### Automated Backup Script

```bash
#!/bin/bash
set -euo pipefail

DATE=$(date +%F)
BACKUP_DIR="/backups"
TARGET="/etc /var/www"

echo "$(date): Starting backup" >> /var/log/backup.log
tar -czf ${BACKUP_DIR}/backup-${DATE}.tar.gz ${TARGET}

# Upload to cloud storage
aws s3 cp ${BACKUP_DIR}/backup-${DATE}.tar.gz s3://mybucket/backups/

# Clean backups older than 30 days
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete

echo "$(date): Backup complete" >> /var/log/backup.log
```

Schedule with cron:
```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

---


## 12.25 Automation and Configuration Management

### Ansible — Agentless Configuration Management

Ansible manages Linux servers over SSH without installing agents.

```bash
# Install Ansible
sudo apt install ansible

# Inventory file (hosts)
cat > inventory.ini << EOF
[webservers]
web1.example.com
web2.example.com

[dbservers]
db1.example.com
EOF

# Run ad-hoc command on all servers
ansible all -i inventory.ini -m ping
ansible webservers -i inventory.ini -m shell -a "uptime"

# Install nginx on all web servers
ansible webservers -i inventory.ini -m apt -a "name=nginx state=present" --become
```

### Ansible Playbook Example

```yaml
# deploy.yml
---
- hosts: webservers
  become: yes
  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Start nginx
      systemd:
        name: nginx
        state: started
        enabled: yes

    - name: Deploy config
      copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx

  handlers:
    - name: Restart nginx
      systemd:
        name: nginx
        state: restarted
```

```bash
# Run playbook
ansible-playbook -i inventory.ini deploy.yml
```

### Infrastructure as Code (IaC)

| Tool | Purpose | Language |
|------|---------|----------|
| **Ansible** | Configuration management | YAML |
| **Terraform** | Infrastructure provisioning | HCL |
| **Puppet** | Configuration management | Puppet DSL |
| **Chef** | Configuration management | Ruby |
| **Packer** | Machine image building | JSON/HCL |

```bash
# Terraform example — provision an EC2 instance
cat > main.tf << EOF
provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  tags = {
    Name = "web-server"
  }
}
EOF

terraform init
terraform plan
terraform apply
```

**Real-world**: In production, you never configure servers manually. Use Ansible for configuration, Terraform for infrastructure, and Packer for building golden images.

---

## 12.26 Interview Questions — Module 12

**Q1: How do you create and manage a custom systemd service?**

Create a unit file at `/etc/systemd/system/myapp.service` with `[Unit]`, `[Service]`, and `[Install]` sections. Use `systemctl daemon-reload` after changes, `systemctl enable --now myapp` to start and enable on boot, `journalctl -u myapp -f` to monitor logs.

**Q2: What are Linux namespaces and how do containers use them?**

Namespaces isolate what a process can see: PID (process tree), NET (network stack), MNT (filesystems), UTS (hostname), IPC (inter-process communication), USER (UID mapping). Docker/Podman create a set of namespaces for each container, providing isolation without a separate kernel.

**Q3: What is the difference between Docker and Podman?**

Podman is daemonless (no background `dockerd` process), supports rootless containers by default, and can generate Kubernetes YAML (`podman generate kube`). Docker requires a daemon and root by default. CLI syntax is compatible — `alias docker=podman` works.

**Q4: How do you harden a Linux server for production?**

1. Disable root SSH login (`PermitRootLogin no`)
2. Key-only authentication (`PasswordAuthentication no`)
3. Enable firewall (ufw/firewalld)
4. Install fail2ban
5. Enable auditd
6. Apply security updates
7. Harden systemd services (ProtectSystem, PrivateTmp, NoNewPrivileges)
8. Set password policies via PAM

**Q5: What is cloud-init and how is it used in production?**

cloud-init runs on first boot of cloud VMs to configure hostname, users, SSH keys, install packages, and run commands. It's used in autoscaling groups — every new instance automatically configures itself from user-data without manual intervention.
