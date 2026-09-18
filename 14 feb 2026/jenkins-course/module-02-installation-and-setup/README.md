# Module 02 — Installation and Setup

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 1 core | 4+ cores |
| RAM | 256 MB | 4+ GB |
| Disk | 1 GB | 50+ GB |
| Java | JDK 11 | JDK 17 |
| OS | Any (Linux preferred) | Ubuntu 22.04 / RHEL 9 |

## Installation Methods

### Method 1: Install on Ubuntu/Debian

#### Step 1: Add the Repository Key

Downloads the official GPG key used to verify Jenkins package authenticity.

```bash
wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
```

**Expected output:**
```
Saving to: '/usr/share/keyrings/jenkins-keyring.asc'
/usr/share/keyrings/jenkins-keyring.asc  100%[===================>]  3.17K  --.-KB/s
```

#### Step 2: Add Jenkins Repository

Adds the Jenkins APT repository to your system's package sources.

```bash
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
```

**What this does:** Creates `/etc/apt/sources.list.d/jenkins.list` so `apt` knows where to download Jenkins from.

#### Step 3: Install Java (Required)

Jenkins requires Java to run. Install JDK 17.

```bash
sudo apt update
sudo apt install -y fontconfig openjdk-17-jre
```

**Verify Java is installed:**
```bash
java -version
```

**Expected output:**
```
openjdk version "17.0.8" 2023-07-18
OpenJDK Runtime Environment (build 17.0.8+7-Debian-1deb12u1)
OpenJDK 64-Bit Server VM (build 17.0.8+7-Debian-1deb12u1, mixed mode, sharing)
```

#### Step 4: Install Jenkins

```bash
sudo apt install -y jenkins
```

**Expected output:**
```
Setting up jenkins (2.xxx.x) ...
```

#### Step 5: Start Jenkins and Check Status

```bash
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
```

**Expected output (status):**
```
● jenkins.service - Jenkins Continuous Integration Server
     Loaded: loaded (/lib/systemd/system/jenkins.service; enabled)
     Active: active (running) since ...
   Main PID: 12345 (java)
```

If it shows `inactive (dead)`, start it manually:
```bash
sudo systemctl start jenkins
```

#### Step 6: Verify Port 8080

```bash
netstat -an | grep 8080
```

**Expected output:**
```
tcp6       0      0 :::8080                 :::*                    LISTEN
```

This confirms Jenkins is listening on port 8080.

#### Step 7: Set Hostname

Set a descriptive hostname to identify this machine as the Jenkins master.

```bash
sudo hostnamectl set-hostname jenkinsmaster
```

**Verify:**
```bash
hostnamectl
```

**Expected output:**
```
 Static hostname: jenkinsmaster
       Icon name: computer-vm
         Chassis: vm
```

#### Step 8: Access Jenkins Web UI

Open in browser:
```
http://<your-server-ip>:8080
```

On first access, Jenkins asks for the initial admin password:
```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

**Expected output:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Copy this password and paste it into the web UI to unlock Jenkins.

### Method 2: Install on RHEL/CentOS/Amazon Linux

```bash
# Install Java
sudo yum install -y java-17-openjdk-devel

# Add Jenkins repo
sudo wget -O /etc/yum.repos.d/jenkins.repo \
  https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io-2023.key

# Install Jenkins
sudo yum install -y jenkins

# Start Jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins
```

### Method 3: Run with Docker

```bash
# Create a Docker network
docker network create jenkins

# Run Jenkins
docker run -d \
  --name jenkins \
  --network jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts-jdk17

# Get initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Method 4: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  jenkins:
    image: jenkins/jenkins:lts-jdk17
    container_name: jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - JAVA_OPTS=-Xmx2g -Xms512m

volumes:
  jenkins_home:
```

```bash
docker compose up -d
```

### Method 5: Install on Kubernetes (Helm)

```bash
# Add Jenkins Helm repo
helm repo add jenkins https://charts.jenkins.io
helm repo update

# Create namespace
kubectl create namespace jenkins

# Install with Helm
helm install jenkins jenkins/jenkins \
  --namespace jenkins \
  --set controller.serviceType=LoadBalancer \
  --set controller.adminPassword=admin123 \
  --set persistence.size=50Gi

# Get admin password (if not set above)
kubectl exec -n jenkins svc/jenkins -c jenkins -- \
  cat /run/secrets/additional/chart-admin-password
```

## Initial Setup Wizard

1. **Access Jenkins**: Open `http://<server-ip>:8080`

2. **Unlock Jenkins**: Retrieve the initial admin password:
   ```bash
   # Package install
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword

   # Docker
   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```

3. **Install Plugins**: Choose one:
   - **Install suggested plugins** (recommended for beginners)
   - **Select plugins to install** (for experienced users)

4. **Create Admin User**: Set up the first admin account

5. **Configure URL**: Set the Jenkins URL (used in notifications, webhooks)

## Post-Installation Configuration

### Configure JDK

**Manage Jenkins → Tools → JDK installations**

```
Name: JDK-17
JAVA_HOME: /usr/lib/jvm/java-17-openjdk-amd64
```

### Configure Git

```bash
# Install Git on Jenkins server
sudo apt install -y git

# Verify
git --version
```

### Configure Maven (if needed)

**Manage Jenkins → Tools → Maven installations**

```
Name: Maven-3.9
Install automatically: ✓
Version: 3.9.x
```

### Configure Node.js (if needed)

Install the **NodeJS Plugin**, then:

**Manage Jenkins → Tools → NodeJS installations**

```
Name: Node-20
Install automatically: ✓
Version: 20.x
```

## Jenkins Home Directory Structure

```
/var/lib/jenkins/              # JENKINS_HOME (package install)
├── config.xml                 # Global configuration
├── credentials.xml            # Encrypted credentials
├── hudson.model.UpdateCenter.xml
├── identity.key.enc
├── jobs/                      # All job configurations and build history
│   └── my-job/
│       ├── config.xml         # Job configuration
│       ├── builds/            # Build history
│       │   ├── 1/
│       │   │   ├── build.xml
│       │   │   ├── log
│       │   │   └── changelog.xml
│       │   └── 2/
│       └── workspace/         # Working directory (source code)
├── logs/                      # Jenkins logs
├── nodes/                     # Agent configurations
├── plugins/                   # Installed plugins (.jpi/.hpi files)
├── secrets/                   # Encryption keys
├── updates/                   # Plugin update metadata
├── userContent/               # Static files served at /userContent/
├── users/                     # User configurations
└── workspace/                 # Default workspace root
```

## Firewall Configuration

```bash
# Ubuntu (UFW)
sudo ufw allow 8080/tcp    # Jenkins web UI
sudo ufw allow 50000/tcp   # Agent communication (JNLP)
sudo ufw reload

# RHEL/CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=50000/tcp
sudo firewall-cmd --reload
```

## Reverse Proxy Setup (Nginx)

```nginx
# /etc/nginx/sites-available/jenkins
upstream jenkins {
    keepalive 32;
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name jenkins.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name jenkins.example.com;

    ssl_certificate     /etc/ssl/certs/jenkins.crt;
    ssl_certificate_key /etc/ssl/private/jenkins.key;

    location / {
        proxy_pass http://jenkins;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (required for Jenkins)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 90;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/jenkins /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Verify Installation

```bash
# Check Jenkins is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
# Expected: 200 (or 403 before setup)

# Check Jenkins version
curl -s -I http://localhost:8080 | grep X-Jenkins
# X-Jenkins: 2.xxx

# Check Java version used by Jenkins
sudo -u jenkins java -version
```
