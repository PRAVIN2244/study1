# Module 06 — Master-Slave (Controller-Agent) Architecture

## Overview

In production, the Jenkins controller should not execute builds. Instead, builds are distributed to agents (formerly called slaves).

```
┌─────────────────────────────────────────────────────┐
│                 Jenkins Controller                   │
│                                                     │
│  • Manages configuration                            │
│  • Schedules builds                                 │
│  • Serves UI and API                                │
│  • Dispatches builds to agents                      │
│  • Stores build logs and artifacts                  │
│  • Set executors to 0 on controller                 │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐   ┌────▼────┐  ┌────▼────┐
    │ Agent 1 │   │ Agent 2 │  │ Agent 3 │
    │ (SSH)   │   │ (JNLP)  │  │ (Docker)│
    │ Linux   │   │ Windows │  │ Dynamic │
    │ 4 exec  │   │ 2 exec  │  │ 1 exec  │
    └─────────┘   └─────────┘  └─────────┘
```

## How Master-Agent Communication Works

### Connection Flow

```
Step 1: Agent registers with master (via UI or API)
Step 2: Connection established (SSH or JNLP)
Step 3: Master sends agent.jar to the agent
Step 4: agent.jar runs on the agent machine
Step 5: Agent polls master for jobs
Step 6: Master assigns job → Agent executes
Step 7: Agent streams console output back to master
Step 8: Agent uploads artifacts to master
Step 9: Agent reports build result (SUCCESS/FAILURE)
```

### What Runs Where

```
MASTER (Controller)                    AGENT (Slave)
├── Jenkins web UI                     ├── Receives job instructions
├── REST API                           ├── Clones source code
├── Job configuration                  ├── Runs build commands
├── Build queue                        ├── Executes tests
├── Credential store                   ├── Creates artifacts
├── Plugin management                  ├── Reports results back
├── Build logs (stored here)           └── Workspace (source + build output)
└── Artifact storage
```

### Connection Methods

Agents connect to the master using one of these methods:

```
Method 1: SSH (Master → Agent)
┌────────┐                    ┌────────┐
│ Master │───── SSH :22 ─────▶│ Agent  │
│        │                    │        │
│        │◀── results ────────│        │
└────────┘                    └────────┘
Master initiates the connection.
Agent needs: SSH server + Java installed.
Best for: Linux agents.

Method 2: JNLP/WebSocket (Agent → Master)
┌────────┐                    ┌────────┐
│ Master │◀── JNLP :50000 ───│ Agent  │
│        │                    │        │
│        │── job payload ────▶│        │
└────────┘                    └────────┘
Agent initiates the connection.
Agent downloads and runs agent.jar.
Best for: Windows agents, agents behind firewalls.

Method 3: Docker (Master → Docker daemon)
┌────────┐                    ┌────────────┐
│ Master │── Docker API ─────▶│ Container  │
│        │                    │ (ephemeral)│
│        │◀── results ────────│            │
└────────┘                    └────────────┘
Container created per build, destroyed after.
Best for: Isolated, reproducible builds.

Method 4: Kubernetes (Master → K8s API)
┌────────┐                    ┌────────────┐
│ Master │── K8s API ────────▶│    Pod     │
│        │                    │ (ephemeral)│
│        │◀── results ────────│            │
└────────┘                    └────────────┘
Pod created per build, terminated after.
Best for: Scalable, cloud-native environments.
```

## Agent Types

| Type | Connection | Best For |
|------|-----------|----------|
| **Permanent (SSH)** | Controller connects to agent via SSH | Linux servers |
| **Permanent (JNLP)** | Agent connects to controller | Windows, firewalled agents |
| **Cloud (Docker)** | Ephemeral containers | Isolated, reproducible builds |
| **Cloud (Kubernetes)** | Ephemeral pods | Scalable, cloud-native |
| **Cloud (EC2/Azure/GCP)** | On-demand VMs | Burst capacity |

## Setup: SSH Agent (Linux)

### Step 1: Prepare the Agent Machine

```bash
# On the agent (slave) machine

# Step 1: Install Java (same major version as controller)
sudo apt update
sudo apt install -y openjdk-17-jdk
```

**Verify Java:**
```bash
java -version
```
**Expected output:**
```
openjdk version "17.0.8" 2023-07-18
OpenJDK Runtime Environment (build 17.0.8+7)
OpenJDK 64-Bit Server VM (build 17.0.8+7, mixed mode)
```

```bash
# Step 2: Set hostname for identification
sudo hostnamectl set-hostname jenkinsslave
```

**Verify:**
```bash
hostnamectl
```
**Expected output:**
```
 Static hostname: jenkinsslave
```

```bash
# Step 3: Create jenkins user
sudo useradd -m -d /home/jenkins -s /bin/bash jenkins

# Step 4: Create workspace directory
sudo mkdir -p /home/jenkins/workspace
sudo chown -R jenkins:jenkins /home/jenkins

# Step 5: Install required build tools
sudo apt install -y git maven docker.io
sudo usermod -aG docker jenkins
```

### Step 2: Set Up SSH Key Authentication

```bash
# On the Jenkins controller
sudo -u jenkins ssh-keygen -t ed25519 -C "jenkins-agent" -f /var/lib/jenkins/.ssh/agent_key -N ""

# Copy public key to agent
sudo -u jenkins ssh-copy-id -i /var/lib/jenkins/.ssh/agent_key.pub jenkins@agent-ip

# Test connection
sudo -u jenkins ssh -i /var/lib/jenkins/.ssh/agent_key jenkins@agent-ip "java -version"
```

### Step 3: Add SSH Credentials in Jenkins

1. **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**
2. Kind: **SSH Username with private key**
3. ID: `agent-ssh-key`
4. Username: `jenkins`
5. Private Key: Enter directly (paste content of `agent_key`)

### Step 4: Add Agent Node in Jenkins

1. **Manage Jenkins → Nodes → New Node**
2. Configure:

```
Node name: linux-agent-01
Type: Permanent Agent

# Configuration
Number of executors: 4
Remote root directory: /home/jenkins
Labels: linux docker maven
Usage: Use this node as much as possible

# Launch method
Launch method: Launch agents via SSH
Host: 192.168.1.100
Credentials: agent-ssh-key (from step 3)
Host Key Verification Strategy: Known hosts file
                                (or "Non verifying" for testing)

# Availability
Availability: Keep this agent online as much as possible
```

3. Click **Save** → Jenkins connects to the agent automatically

## Setup: JNLP Agent (Windows)

### Step 1: Prepare Windows Machine

```powershell
# Install Java
choco install openjdk17 -y

# Create Jenkins directory
mkdir C:\Jenkins
```

### Step 2: Add Node in Jenkins

1. **Manage Jenkins → Nodes → New Node**
2. Configure:

```
Node name: windows-agent-01
Type: Permanent Agent

Number of executors: 2
Remote root directory: C:\Jenkins
Labels: windows dotnet
Usage: Only build jobs with label expressions matching this node

Launch method: Launch agent by connecting it to the controller
```

3. Save and note the agent connection command shown on the node page.

### Step 3: Connect Agent

```powershell
# Download agent.jar from Jenkins
Invoke-WebRequest -Uri "https://jenkins.example.com/jnlpJars/agent.jar" -OutFile "C:\Jenkins\agent.jar"

# Run agent (shown on the node page in Jenkins)
java -jar C:\Jenkins\agent.jar `
  -url https://jenkins.example.com/ `
  -secret <SECRET_FROM_JENKINS> `
  -name windows-agent-01 `
  -workDir C:\Jenkins
```

### Step 4: Install as Windows Service

```powershell
# Download the Windows service wrapper
# From the agent page, click "Install as a service"
# Or use NSSM:
choco install nssm -y

nssm install JenkinsAgent "C:\Program Files\Java\jdk-17\bin\java.exe" `
  "-jar C:\Jenkins\agent.jar -url https://jenkins.example.com/ -secret <SECRET> -name windows-agent-01 -workDir C:\Jenkins"

nssm set JenkinsAgent AppDirectory C:\Jenkins
nssm set JenkinsAgent Start SERVICE_AUTO_START
nssm start JenkinsAgent
```

## Setup: Docker Cloud Agent

### Step 1: Install Docker Plugin

**Manage Jenkins → Plugins → Available → Docker plugin**

### Step 2: Configure Docker Cloud

**Manage Jenkins → Clouds → New cloud → Docker**

```
Name: docker-cloud
Docker Host URI: unix:///var/run/docker.sock
  (or tcp://docker-host:2376 for remote Docker)

Docker Agent templates:
  Labels: docker-agent
  Docker Image: jenkins/agent:latest-jdk17
  Remote File System Root: /home/jenkins/agent
  Connect method: Attach Docker container
  Pull strategy: Pull once and update latest
```

### Step 3: Use in Pipeline

```groovy
pipeline {
    agent {
        docker {
            image 'maven:3.9-eclipse-temurin-17'
            label 'docker-agent'
            args '-v $HOME/.m2:/root/.m2'
        }
    }
    stages {
        stage('Build') {
            steps {
                sh 'mvn --version'
                sh 'mvn clean package'
            }
        }
    }
}
```

## Setup: Kubernetes Cloud Agent

### Step 1: Install Kubernetes Plugin

**Manage Jenkins → Plugins → Available → Kubernetes**

### Step 2: Configure Kubernetes Cloud

**Manage Jenkins → Clouds → New cloud → Kubernetes**

```
Name: kubernetes
Kubernetes URL: https://kubernetes.default.svc
  (or external cluster URL)
Kubernetes Namespace: jenkins
Credentials: (kubeconfig or service account token)
Jenkins URL: http://jenkins.jenkins.svc:8080
Jenkins tunnel: jenkins-agent.jenkins.svc:50000

Pod Templates:
  Name: default-agent
  Labels: k8s
  Containers:
    - Name: jnlp
      Image: jenkins/inbound-agent:latest-jdk17
      Working directory: /home/jenkins/agent
      Resource limits: CPU=1, Memory=2Gi
```

### Step 3: Use in Pipeline

```groovy
pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-agent
spec:
  containers:
  - name: maven
    image: maven:3.9-eclipse-temurin-17
    command: ['sleep', '99d']
    volumeMounts:
    - name: maven-cache
      mountPath: /root/.m2
  - name: docker
    image: docker:24-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
  volumes:
  - name: maven-cache
    persistentVolumeClaim:
      claimName: maven-cache-pvc
'''
        }
    }
    stages {
        stage('Build') {
            steps {
                container('maven') {
                    sh 'mvn clean package'
                }
            }
        }
        stage('Docker Build') {
            steps {
                container('docker') {
                    sh 'docker build -t myapp:latest .'
                }
            }
        }
    }
}
```

## Agent Management

### Labels Strategy

```
Environment-based:    dev, staging, production
OS-based:            linux, windows, macos
Tool-based:          docker, maven, node, python, dotnet
Size-based:          small, medium, large
Region-based:        us-east, eu-west, ap-south
```

Use compound labels in pipelines:
```groovy
agent { label 'linux && docker && large' }
```

### Monitoring Agents

```
Dashboard → Manage Jenkins → Nodes
├── Built-In Node (controller)  ● Online  [0 executors]
├── linux-agent-01              ● Online  [4 executors, 2 busy]
├── linux-agent-02              ● Online  [4 executors, 0 busy]
├── windows-agent-01            ● Online  [2 executors, 1 busy]
└── docker-cloud                ○ (dynamic, on-demand)
```

### Agent Availability Strategies

| Strategy | Behavior |
|----------|----------|
| **Keep online** | Always connected, reconnect on failure |
| **Take offline when idle** | Disconnect after N minutes of inactivity |
| **Schedule** | Online during specific hours (cron) |
| **On demand** | Spin up only when builds need it (cloud agents) |

### Troubleshooting Agent Connections

```bash
# Check agent logs in Jenkins UI
# Manage Jenkins → Nodes → agent-name → Log

# Test SSH connectivity
ssh -i /var/lib/jenkins/.ssh/agent_key jenkins@agent-ip

# Check Java version on agent
ssh jenkins@agent-ip "java -version"

# Check agent.jar connectivity (JNLP)
java -jar agent.jar -url http://jenkins:8080/ -secret <secret> -name agent -workDir /tmp -noCertificateCheck

# Check firewall
# SSH: port 22 open on agent
# JNLP: port 50000 open on controller
telnet jenkins-controller 50000
```

## Scaling Strategies

### Static Agents
- Fixed number of always-on machines
- Predictable capacity, potential waste during idle periods
- Best for: consistent workloads

### Dynamic/Cloud Agents
- Spin up on demand, terminate when idle
- Pay only for what you use
- Best for: variable workloads, cost optimization

### Hybrid
- Small pool of static agents for baseline load
- Cloud agents for burst capacity
- Best for: most production environments

```
Baseline load ──────────────────────────── Static agents (always on)
                    ╱╲      ╱╲
Peak load ─────────╱──╲────╱──╲─────────── Cloud agents (on demand)
                  ╱    ╲  ╱    ╲
                 ╱      ╲╱      ╲
```
