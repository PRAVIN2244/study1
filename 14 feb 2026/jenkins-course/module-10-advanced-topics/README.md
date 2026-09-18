# Module 10 — Advanced Topics

## High Availability (HA)

Jenkins does not natively support active-active HA (two masters serving requests simultaneously). The JENKINS_HOME directory contains state that cannot be safely shared between two running instances. All HA strategies use active-passive or external redundancy.

### Why Jenkins HA is Hard

```
Problem: JENKINS_HOME is a single directory on disk
├── config.xml           ← global config (one writer at a time)
├── jobs/                ← job configs + build history
├── plugins/             ← loaded into JVM memory
├── credentials.xml      ← encrypted secrets
└── queue.xml            ← build queue state

Two Jenkins instances writing to the same JENKINS_HOME = data corruption.
```

### Strategy 1: Active-Passive with Shared Storage

One Jenkins runs at a time. If it fails, the standby takes over using the same JENKINS_HOME on shared storage.

```
                    ┌──────────────┐
                    │ Load Balancer│
                    │ (health check│
                    │  on :8080)   │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │                         │
        ┌─────▼─────┐           ┌──────▼────┐
        │  Jenkins   │           │  Jenkins  │
        │  Active    │           │  Standby  │
        │  (running) │           │  (stopped)│
        └─────┬──────┘           └─────┬─────┘
              │                        │
              └────────┬───────────────┘
                       │
                ┌──────▼──────┐
                │ Shared NFS  │
                │ or EFS/EBS  │
                │ JENKINS_HOME│
                └─────────────┘
```

#### Setup on AWS (EFS + EC2 + ALB)

```bash
# Step 1: Create EFS filesystem for JENKINS_HOME
aws efs create-file-system --performance-mode generalPurpose --throughput-mode bursting

# Step 2: Mount EFS on both EC2 instances
# On both Jenkins servers:
sudo apt install -y nfs-common
sudo mkdir -p /var/lib/jenkins
echo "fs-0123456789.efs.us-east-1.amazonaws.com:/ /var/lib/jenkins nfs4 defaults,_netdev 0 0" \
  | sudo tee -a /etc/fstab
sudo mount -a

# Step 3: Install Jenkins on BOTH servers (same version)
# Only START Jenkins on the active server
# On active:
sudo systemctl start jenkins
# On standby:
sudo systemctl stop jenkins
sudo systemctl disable jenkins

# Step 4: Configure ALB health check
# Target group health check: HTTP:8080/login
# Healthy threshold: 2
# Unhealthy threshold: 3
# Interval: 10 seconds
```

#### Failover Process

```
Normal operation:
  Active (running) ← ALB routes traffic here
  Standby (stopped)

Active server fails:
  1. ALB health check fails (3 consecutive failures)
  2. ALB marks active as unhealthy
  3. Admin (or automation) starts Jenkins on standby
  4. Standby reads same JENKINS_HOME from EFS
  5. ALB routes traffic to standby (now active)
  6. All jobs, configs, history are intact

Automated failover script:
```

```bash
#!/bin/bash
# failover.sh — run on standby server via CloudWatch alarm

# Check if active is truly down
if ! curl -sf http://active-jenkins:8080/login > /dev/null 2>&1; then
    echo "Active Jenkins is DOWN — starting standby..."

    # Start Jenkins on this (standby) server
    sudo systemctl start jenkins

    # Wait for Jenkins to be ready
    until curl -sf http://localhost:8080/login > /dev/null 2>&1; do
        echo "Waiting for Jenkins to start..."
        sleep 5
    done

    echo "Standby Jenkins is now ACTIVE"

    # Update DNS or ALB target (if not automatic)
    # aws elbv2 register-targets ...
fi
```

### Strategy 2: Jenkins on Kubernetes (Auto-Healing)

Kubernetes restarts Jenkins automatically if it crashes. Combined with persistent storage, this provides HA without a standby server.

```
┌─────────────────────────────────────────────┐
│              Kubernetes Cluster              │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Jenkins Deployment (replicas: 1)   │    │
│  │                                     │    │
│  │  ┌───────────────────────────────┐  │    │
│  │  │  Jenkins Pod                  │  │    │
│  │  │  ┌─────────────────────────┐  │  │    │
│  │  │  │ jenkins/jenkins:lts     │  │  │    │
│  │  │  │ Port: 8080              │  │  │    │
│  │  │  └──────────┬──────────────┘  │  │    │
│  │  │             │                 │  │    │
│  │  │  ┌──────────▼──────────────┐  │  │    │
│  │  │  │ PVC: jenkins-home       │  │  │    │
│  │  │  │ (Persistent Volume)     │  │  │    │
│  │  │  │ 100Gi, gp3             │  │  │    │
│  │  │  └─────────────────────────┘  │  │    │
│  │  └───────────────────────────────┘  │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  If pod crashes → K8s restarts it           │
│  PVC retains all data across restarts       │
└─────────────────────────────────────────────┘
```

```yaml
# jenkins-k8s-ha.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jenkins
  namespace: jenkins
spec:
  replicas: 1                    # Only 1 replica (Jenkins limitation)
  strategy:
    type: Recreate               # Stop old before starting new
  selector:
    matchLabels:
      app: jenkins
  template:
    metadata:
      labels:
        app: jenkins
    spec:
      containers:
        - name: jenkins
          image: jenkins/jenkins:lts-jdk17
          ports:
            - containerPort: 8080
            - containerPort: 50000
          resources:
            requests:
              cpu: "2"
              memory: "4Gi"
            limits:
              cpu: "4"
              memory: "8Gi"
          volumeMounts:
            - name: jenkins-home
              mountPath: /var/jenkins_home
          livenessProbe:
            httpGet:
              path: /login
              port: 8080
            initialDelaySeconds: 120
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /login
              port: 8080
            initialDelaySeconds: 60
            periodSeconds: 5
      volumes:
        - name: jenkins-home
          persistentVolumeClaim:
            claimName: jenkins-home-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jenkins-home-pvc
  namespace: jenkins
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi
```

**What happens when Jenkins crashes:**
```
1. Pod crashes (OOM, Java error, etc.)
2. K8s liveness probe fails
3. K8s restarts the pod automatically (within seconds)
4. New pod mounts the same PVC (JENKINS_HOME intact)
5. Jenkins starts up, loads all configs from PVC
6. All jobs, history, credentials are preserved
7. Agents reconnect automatically
```

### Strategy 3: Controller + Ephemeral Agents (Recommended)

The most resilient approach: keep the controller minimal and stateless agents.

```
┌──────────────────────────────────────────────────────┐
│                  Jenkins Controller                   │
│  (K8s pod with PVC, or EC2 with EFS)                 │
│                                                      │
│  Responsibilities:                                   │
│  ├── Serve UI and API                                │
│  ├── Store job configs                               │
│  ├── Schedule builds                                 │
│  └── Executors: 0 (NO builds on controller)          │
└──────────────────┬───────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
┌────▼────┐  ┌────▼────┐  ┌────▼────┐
│ K8s Pod │  │ K8s Pod │  │ K8s Pod │
│ (build) │  │ (build) │  │ (build) │
│ ephemeral│  │ ephemeral│  │ ephemeral│
│ dies     │  │ dies     │  │ dies     │
│ after    │  │ after    │  │ after    │
│ build    │  │ build    │  │ build    │
└─────────┘  └─────────┘  └─────────┘

If controller crashes → K8s restarts it
If agent crashes → K8s creates a new one
No state is lost because agents are stateless
```

### HA Comparison

| Strategy | Downtime | Complexity | Cost | Data Loss |
|----------|----------|-----------|------|-----------|
| **Active-Passive (NFS/EFS)** | Minutes (manual failover) | Medium | 2x servers | None |
| **Active-Passive (automated)** | 30-60 seconds | High | 2x servers + monitoring | None |
| **K8s with PVC** | 30-60 seconds (auto) | Medium | K8s cluster | None |
| **K8s + ephemeral agents** | 30-60 seconds (auto) | Medium | K8s cluster | None |
| **CloudBees HA (commercial)** | Seconds | Low (managed) | License cost | None |

### Backup and Restore

```bash
#!/bin/bash
# backup-jenkins.sh

JENKINS_HOME="/var/lib/jenkins"
BACKUP_DIR="/backup/jenkins"
DATE=$(date +%Y%m%d_%H%M%S)

# Stop Jenkins (optional, for consistency)
# sudo systemctl stop jenkins

# Backup essential directories
tar czf "${BACKUP_DIR}/jenkins_${DATE}.tar.gz" \
  --exclude="${JENKINS_HOME}/workspace" \
  --exclude="${JENKINS_HOME}/.cache" \
  --exclude="${JENKINS_HOME}/caches" \
  "${JENKINS_HOME}/config.xml" \
  "${JENKINS_HOME}/credentials.xml" \
  "${JENKINS_HOME}/secrets/" \
  "${JENKINS_HOME}/users/" \
  "${JENKINS_HOME}/jobs/*/config.xml" \
  "${JENKINS_HOME}/nodes/" \
  "${JENKINS_HOME}/plugins/*.jpi" \
  "${JENKINS_HOME}/*.xml" \
  "${JENKINS_HOME}/*.key"

# Keep last 7 backups
find "${BACKUP_DIR}" -name "jenkins_*.tar.gz" -mtime +7 -delete

echo "Backup completed: jenkins_${DATE}.tar.gz"
```

```bash
# Restore
sudo systemctl stop jenkins
tar xzf jenkins_20240101_120000.tar.gz -C /
sudo chown -R jenkins:jenkins /var/lib/jenkins
sudo systemctl start jenkins
```

### Automated Backup with ThinBackup Plugin

```yaml
# JCasC
unclassified:
  thinkBackup:
    backupPath: "/backup/jenkins"
    fullBackupSchedule: "H 2 * * 0"      # Weekly full backup
    diffBackupSchedule: "H 2 * * 1-6"    # Daily differential
    nrMaxStoredFull: 4
    excludedFilesRegex: ".*\\.log"
    backupBuildResults: true
    backupPluginArchives: true
    backupUserContents: true
```

## Performance Tuning

### JVM Settings

```bash
# /etc/default/jenkins (Debian) or /etc/sysconfig/jenkins (RHEL)
JAVA_ARGS="-Xms2g -Xmx4g \
  -XX:+UseG1GC \
  -XX:+ParallelRefProcEnabled \
  -XX:+DisableExplicitGC \
  -XX:MaxMetaspaceSize=512m \
  -Djava.awt.headless=true \
  -Dhudson.model.DirectoryBrowserSupport.CSP=\"\" \
  -Djenkins.install.runSetupWizard=false"
```

### Build Optimization

```groovy
pipeline {
    agent any
    options {
        // Limit build history
        buildDiscarder(logRotator(numToKeepStr: '20', artifactNumToKeepStr: '5'))
        // Timeout
        timeout(time: 30, unit: 'MINUTES')
        // Disable concurrent builds
        disableConcurrentBuilds()
        // Skip default checkout (do it manually for shallow clone)
        skipDefaultCheckout()
    }
    stages {
        stage('Checkout') {
            steps {
                // Shallow clone for speed
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [
                        [$class: 'CloneOption', depth: 1, shallow: true, noTags: true],
                        [$class: 'CleanBeforeCheckout']
                    ],
                    userRemoteConfigs: [[url: 'https://github.com/org/repo.git']]
                ])
            }
        }
        stage('Build') {
            steps {
                // Use build caches
                sh 'mvn package -T 1C -DskipTests'  // Parallel Maven build
            }
        }
    }
}
```

### Disk Space Management

```bash
# Cron job to clean old workspaces
# /etc/cron.daily/jenkins-cleanup
find /var/lib/jenkins/workspace -maxdepth 1 -mtime +7 -exec rm -rf {} \;
find /var/lib/jenkins/jobs/*/builds -maxdepth 1 -mtime +30 -exec rm -rf {} \;
```

## Monitoring Jenkins

### Prometheus + Grafana

Install **Prometheus Metrics Plugin**:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'jenkins'
    metrics_path: '/prometheus'
    static_configs:
      - targets: ['jenkins:8080']
    # If authentication is required
    basic_auth:
      username: 'monitoring'
      password: 'token'
```

Key metrics to monitor:
- `jenkins_queue_size_value` — build queue length
- `jenkins_node_online_value` — agent availability
- `jenkins_executor_count_value` — total executors
- `jenkins_executor_in_use_value` — busy executors
- `jenkins_job_building_duration` — build duration
- `vm_memory_heap_usage` — JVM heap usage

### Health Check Endpoint

```bash
# Jenkins health check
curl -s http://jenkins:8080/api/json?tree=mode,nodeDescription,useSecurity

# Queue status
curl -s http://jenkins:8080/queue/api/json

# Node status
curl -s http://jenkins:8080/computer/api/json
```

## Pipeline as Code Patterns

### Monorepo Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Detect Changes') {
            steps {
                script {
                    def changes = sh(
                        script: "git diff --name-only HEAD~1",
                        returnStdout: true
                    ).trim().split('\n')

                    env.BUILD_FRONTEND = changes.any { it.startsWith('frontend/') } ? 'true' : 'false'
                    env.BUILD_BACKEND = changes.any { it.startsWith('backend/') } ? 'true' : 'false'
                    env.BUILD_INFRA = changes.any { it.startsWith('terraform/') } ? 'true' : 'false'
                }
            }
        }
        stage('Build Services') {
            parallel {
                stage('Frontend') {
                    when { expression { env.BUILD_FRONTEND == 'true' } }
                    steps {
                        dir('frontend') { sh 'npm ci && npm run build' }
                    }
                }
                stage('Backend') {
                    when { expression { env.BUILD_BACKEND == 'true' } }
                    steps {
                        dir('backend') { sh 'mvn package' }
                    }
                }
            }
        }
    }
}
```

### Matrix Builds

```groovy
pipeline {
    agent none
    stages {
        stage('Test') {
            matrix {
                axes {
                    axis {
                        name 'OS'
                        values 'linux', 'windows', 'macos'
                    }
                    axis {
                        name 'JDK'
                        values '11', '17', '21'
                    }
                }
                excludes {
                    exclude {
                        axis { name 'OS'; values 'macos' }
                        axis { name 'JDK'; values '11' }
                    }
                }
                stages {
                    stage('Build & Test') {
                        agent { label "${OS}" }
                        steps {
                            sh "java -version"
                            sh "mvn test -Djava.version=${JDK}"
                        }
                    }
                }
            }
        }
    }
}
```

### GitOps Pipeline

```groovy
pipeline {
    agent any
    environment {
        IMAGE = "myorg/myapp:${BUILD_NUMBER}"
        GITOPS_REPO = 'https://github.com/org/k8s-manifests.git'
    }
    stages {
        stage('Build & Push Image') {
            steps {
                sh "docker build -t ${IMAGE} ."
                withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'U', passwordVariable: 'P')]) {
                    sh "echo $P | docker login -u $U --password-stdin"
                    sh "docker push ${IMAGE}"
                }
            }
        }
        stage('Update Manifests') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                        git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/org/k8s-manifests.git
                        cd k8s-manifests
                        sed -i "s|image: myorg/myapp:.*|image: ${IMAGE}|" production/deployment.yaml
                        git config user.email "jenkins@example.com"
                        git config user.name "Jenkins"
                        git add .
                        git commit -m "Update image to ${IMAGE}"
                        git push
                    '''
                }
                // ArgoCD or Flux picks up the change automatically
            }
        }
    }
}
```

## Jenkins on Kubernetes (Production Setup)

```yaml
# values.yaml for Helm chart
controller:
  image: jenkins/jenkins
  tag: lts-jdk17
  resources:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
  javaOpts: "-Xms4g -Xmx6g"
  numExecutors: 0
  installPlugins:
    - kubernetes
    - workflow-aggregator
    - git
    - configuration-as-code
    - credentials-binding
    - role-strategy
  JCasC:
    configScripts:
      welcome-message: |
        jenkins:
          systemMessage: "Production Jenkins"
  ingress:
    enabled: true
    hostName: jenkins.example.com
    tls:
      - secretName: jenkins-tls
        hosts:
          - jenkins.example.com

persistence:
  enabled: true
  size: 100Gi
  storageClass: gp3

agent:
  enabled: true
  image: jenkins/inbound-agent
  tag: latest-jdk17
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"

backup:
  enabled: true
  schedule: "0 2 * * *"
  destination: "s3://my-bucket/jenkins-backups"
```

```bash
helm upgrade --install jenkins jenkins/jenkins \
  -f values.yaml \
  --namespace jenkins \
  --create-namespace
```

## Migration Guide

### Jenkins 1.x → 2.x

1. Backup everything
2. Update plugins first
3. Upgrade Jenkins
4. Convert freestyle jobs to pipelines
5. Adopt Jenkinsfile in repositories

### Moving to Another Server

```bash
# On old server
sudo systemctl stop jenkins
tar czf jenkins_migration.tar.gz /var/lib/jenkins/

# On new server
# Install same Jenkins version
sudo systemctl stop jenkins
tar xzf jenkins_migration.tar.gz -C /
sudo chown -R jenkins:jenkins /var/lib/jenkins
sudo systemctl start jenkins

# Update Jenkins URL in:
# Manage Jenkins → System → Jenkins URL
# Update webhook URLs in Git repositories
# Update agent connection URLs
```
