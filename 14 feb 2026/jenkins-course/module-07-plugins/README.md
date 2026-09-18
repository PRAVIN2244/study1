# Module 07 — Plugins

## Plugin Architecture

Jenkins core is minimal. Plugins extend functionality for SCM, build tools, notifications, cloud integrations, and more.

```
Jenkins Core
├── Plugin Manager (loads/manages plugins)
├── Extension Points (interfaces plugins implement)
└── Plugin Dependencies (plugins can depend on other plugins)

Plugin (.hpi/.jpi file)
├── META-INF/MANIFEST.MF    # Plugin metadata
├── WEB-INF/
│   ├── classes/             # Compiled Java classes
│   └── lib/                 # Dependencies
└── resources/               # UI templates (Jelly/Groovy)
```

## Essential Plugins

### Source Control

| Plugin | Purpose |
|--------|---------|
| **Git** | Git integration (clone, checkout, polling) |
| **GitHub** | GitHub webhooks, status checks |
| **GitLab** | GitLab webhooks, merge request builds |
| **Bitbucket** | Bitbucket integration |

### Build Tools

| Plugin | Purpose |
|--------|---------|
| **Pipeline** | Pipeline as code (Jenkinsfile) |
| **Docker Pipeline** | Use Docker containers in pipelines |
| **Kubernetes** | Dynamic agents in K8s |
| **NodeJS** | Node.js tool installer |
| **Maven Integration** | Maven project type |

### Testing & Quality

| Plugin | Purpose |
|--------|---------|
| **JUnit** | Parse and display test results |
| **JaCoCo** | Code coverage reports |
| **SonarQube Scanner** | Code quality analysis |
| **HTML Publisher** | Publish HTML reports |
| **Warnings Next Gen** | Static analysis warnings |

### Notifications

| Plugin | Purpose |
|--------|---------|
| **Slack Notification** | Send messages to Slack |
| **Email Extension** | Advanced email notifications |
| **Microsoft Teams** | Teams notifications |

### Security & Credentials

| Plugin | Purpose |
|--------|---------|
| **Credentials** | Manage secrets (built-in) |
| **Credentials Binding** | Use credentials in builds |
| **Role-based Authorization** | RBAC for Jenkins |
| **LDAP** | LDAP authentication |
| **OWASP Markup Formatter** | Safe HTML in descriptions |

### Utility

| Plugin | Purpose |
|--------|---------|
| **Blue Ocean** | Modern UI for pipelines |
| **Job DSL** | Programmatically create jobs |
| **Configuration as Code (JCasC)** | YAML-based Jenkins config |
| **Timestamper** | Add timestamps to console output |
| **Workspace Cleanup** | Clean workspace before/after builds |
| **Copy Artifact** | Copy artifacts between jobs |
| **Rebuild** | Rebuild with same parameters |
| **Throttle Concurrent Builds** | Limit concurrent executions |

## Plugin Management

### Install via UI

**Manage Jenkins → Plugins**

- **Available plugins**: Search and install
- **Installed plugins**: View, update, uninstall
- **Updates**: Available updates for installed plugins

### Install via CLI

```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar -s http://localhost:8080/ \
  -auth admin:password \
  install-plugin git docker-workflow kubernetes -restart

# Using Plugin Installation Manager Tool (Docker)
jenkins-plugin-cli --plugins \
  git:latest \
  docker-workflow:latest \
  kubernetes:latest \
  configuration-as-code:latest
```

### Install via Docker (Pre-install)

```dockerfile
FROM jenkins/jenkins:lts-jdk17

# Install plugins
RUN jenkins-plugin-cli --plugins \
  git \
  workflow-aggregator \
  docker-workflow \
  kubernetes \
  configuration-as-code \
  credentials-binding \
  role-strategy \
  slack \
  blueocean \
  job-dsl
```

### Plugin File Management

```bash
# Plugins are stored in JENKINS_HOME/plugins/
ls /var/lib/jenkins/plugins/

# Each plugin has:
# - plugin-name.jpi     (the plugin archive)
# - plugin-name/        (extracted plugin directory)

# Manual install (not recommended for production)
cp my-plugin.hpi /var/lib/jenkins/plugins/
sudo systemctl restart jenkins

# Pin a plugin version (prevent auto-update)
touch /var/lib/jenkins/plugins/plugin-name.jpi.pinned
```

## Plugin Configuration Examples

### Slack Notification Plugin

```groovy
// Manage Jenkins → System → Slack
// Workspace: my-workspace
// Credential: slack-bot-token
// Default channel: #builds

// Usage in pipeline
pipeline {
    agent any
    stages {
        stage('Build') {
            steps { sh 'mvn package' }
        }
    }
    post {
        success {
            slackSend(
                channel: '#deployments',
                color: 'good',
                message: "SUCCESS: ${env.JOB_NAME} #${env.BUILD_NUMBER}\n${env.BUILD_URL}"
            )
        }
        failure {
            slackSend(
                channel: '#deployments',
                color: 'danger',
                message: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}\n${env.BUILD_URL}"
            )
        }
    }
}
```

### Job DSL Plugin

Programmatically create Jenkins jobs:

```groovy
// seed-job.groovy — run this as a freestyle job with "Process Job DSLs" build step

// Create a pipeline job
pipelineJob('my-app-pipeline') {
    description('Pipeline for My App')
    definition {
        cpsScm {
            scm {
                git {
                    remote {
                        url('https://github.com/org/my-app.git')
                        credentials('github-token')
                    }
                    branches('*/main')
                }
            }
            scriptPath('Jenkinsfile')
        }
    }
    triggers {
        githubPush()
    }
    properties {
        disableConcurrentBuilds()
    }
}

// Create a multibranch pipeline
multibranchPipelineJob('my-app-multibranch') {
    branchSources {
        github {
            id('my-app')
            repoOwner('org')
            repository('my-app')
            scanCredentialsId('github-token')
        }
    }
    orphanedItemStrategy {
        discardOldItems {
            numToKeep(10)
        }
    }
}

// Create multiple similar jobs
['frontend', 'backend', 'api'].each { service ->
    pipelineJob("${service}-build") {
        definition {
            cpsScm {
                scm {
                    git {
                        remote {
                            url("https://github.com/org/${service}.git")
                            credentials('github-token')
                        }
                    }
                }
                scriptPath('Jenkinsfile')
            }
        }
    }
}
```

### Configuration as Code (JCasC)

Define entire Jenkins configuration in YAML:

```yaml
# jenkins.yaml
jenkins:
  systemMessage: "Jenkins configured via JCasC"
  numExecutors: 0  # No builds on controller
  mode: EXCLUSIVE

  securityRealm:
    ldap:
      configurations:
        - server: "ldap://ldap.example.com"
          rootDN: "dc=example,dc=com"
          userSearchBase: "ou=users"

  authorizationStrategy:
    roleBased:
      roles:
        global:
          - name: "admin"
            permissions:
              - "Overall/Administer"
            entries:
              - user: "admin"
          - name: "developer"
            permissions:
              - "Overall/Read"
              - "Job/Build"
              - "Job/Read"
            entries:
              - group: "developers"

  nodes:
    - permanent:
        name: "linux-agent-01"
        remoteFS: "/home/jenkins"
        numExecutors: 4
        labelString: "linux docker"
        launcher:
          ssh:
            host: "192.168.1.100"
            credentialsId: "agent-ssh-key"
            sshHostKeyVerificationStrategy:
              knownHostsFileKeyVerificationStrategy: {}

  clouds:
    - kubernetes:
        name: "kubernetes"
        namespace: "jenkins"
        jenkinsUrl: "http://jenkins:8080"
        jenkinsTunnel: "jenkins-agent:50000"
        templates:
          - name: "default"
            label: "k8s"
            containers:
              - name: "jnlp"
                image: "jenkins/inbound-agent:latest-jdk17"
                workingDir: "/home/jenkins/agent"
                resourceLimitCpu: "1"
                resourceLimitMemory: "2Gi"

credentials:
  system:
    domainCredentials:
      - credentials:
          - usernamePassword:
              scope: GLOBAL
              id: "github-token"
              username: "jenkins-bot"
              password: "${GITHUB_TOKEN}"
          - string:
              scope: GLOBAL
              id: "slack-token"
              secret: "${SLACK_TOKEN}"

unclassified:
  slackNotifier:
    teamDomain: "my-workspace"
    tokenCredentialId: "slack-token"
    room: "#builds"

  location:
    url: "https://jenkins.example.com/"
    adminAddress: "admin@example.com"

tool:
  git:
    installations:
      - name: "git"
        home: "/usr/bin/git"
  maven:
    installations:
      - name: "Maven-3.9"
        properties:
          - installSource:
              installers:
                - maven:
                    id: "3.9.6"
```

```bash
# Apply JCasC
# Set environment variable
export CASC_JENKINS_CONFIG=/var/lib/jenkins/jenkins.yaml

# Or in Docker
docker run -d \
  -e CASC_JENKINS_CONFIG=/var/jenkins_home/casc.yaml \
  -v ./jenkins.yaml:/var/jenkins_home/casc.yaml \
  jenkins/jenkins:lts-jdk17
```

## Recommended Plugin Set for DevSecOps Pipelines

A practical set of plugins for a production Jenkins setup:

| Plugin | Purpose |
|--------|---------|
| **Git plugin** | Git SCM integration |
| **JDK plugin** | Java tool management |
| **Parameterized Trigger** | Trigger jobs with parameters |
| **Ansible plugin** | Run Ansible playbooks from Jenkins |
| **GitLab plugin** | GitLab webhook and MR integration |
| **Artifactory plugin** | Upload/download artifacts to JFrog |
| **Docker Pipeline** | Build and use Docker containers in pipelines |
| **Amazon ECR Plugin** | Push/pull images to AWS ECR |
| **Pipeline: AWS Steps** | AWS CLI integration in pipelines |
| **SonarQube Scanner** | Static code analysis with SonarQube |
| **Quality Gates** | Enforce SonarQube quality gate pass/fail |
| **Prometheus Metrics** | Expose Jenkins metrics for monitoring |

## Setting Up JFrog Artifactory

### Install Artifactory with Docker

```bash
# Create directories
mkdir -p ~/jfrog/artifactory/var/etc
chmod -R 777 ~/jfrog
touch ~/jfrog/artifactory/var/etc/system.yaml
chown -R 1030:1030 ~/jfrog/artifactory/var

# Run Artifactory OSS
docker run --name artifactory \
  -v ~/jfrog/artifactory/var:/var/opt/jfrog/artifactory \
  -d -p 8081:8081 -p 8082:8082 \
  releases-docker.jfrog.io/jfrog/artifactory-oss:latest

# If OSS image is unavailable, use Community Edition
docker run --name artifactory \
  -v ~/jfrog/artifactory/var/:/var/opt/jfrog/artifactory \
  -d -p 8081:8081 -p 8082:8082 \
  releases-docker.jfrog.io/jfrog/artifactory-cpp-ce:latest

# Default credentials: admin / password
# Access at: http://<server-ip>:8082
```

### Configure Artifactory in Jenkins

1. **Manage Jenkins → System → JFrog**
2. Add server:
   - Server ID: `wezvatechjfrog`
   - URL: `http://<artifactory-ip>:8082`
   - Credentials: (add Artifactory admin credentials)

### Upload Artifacts in Pipeline

```groovy
stage('Store Artifacts') {
    agent { label 'demo' }
    steps {
        script {
            def server = Artifactory.server 'wezvatechjfrog'
            def uploadSpec = """{
                "files": [{
                    "pattern": "target/backend_fb${BUILD_ID}.jar",
                    "target": "wezvatech_backend"
                }]
            }"""
            server.upload(uploadSpec)
        }
    }
}
```

## Setting Up SonarQube

### Install SonarQube with Docker

```bash
# Free memory for SonarQube (Elasticsearch requirement)
sync; echo 1 > /proc/sys/vm/drop_caches
sync; echo 2 > /proc/sys/vm/drop_caches
sync; echo 3 > /proc/sys/vm/drop_caches

# Run SonarQube
docker run -d --name sonarqube -p 9000:9000 sonarqube

# Default credentials: admin / admin
# Access at: http://<server-ip>:9000
```

### Configure SonarQube in Jenkins

1. **Manage Jenkins → System → SonarQube servers**
   - Name: `sonarqube`
   - URL: `http://<sonarqube-ip>:9000`
   - Token: (generate in SonarQube → My Account → Security → Tokens)

2. **Manage Jenkins → Tools → SonarQube Scanner installations**
   - Name: `SonarScanner`
   - Install automatically: ✓

### Install Dependency-Check Plugin in SonarQube

1. Go to SonarQube → Administration → Marketplace
2. Click "I understand the risk"
3. Search for "Dependency-Check" and install
4. Restart SonarQube

### Enable Webhook for Quality Gate

In SonarQube → Administration → Webhooks → Create:

```
Name: Jenkins
URL: http://<jenkins-url>:8080/sonarqube-webhook/
```

This allows the Quality Gates plugin in Jenkins to receive pass/fail results.

## Plugin Security

- Only install plugins from the official Jenkins Update Center
- Review plugin security advisories: https://www.jenkins.io/security/advisories/
- Keep plugins updated — security fixes are frequent
- Remove unused plugins to reduce attack surface
- Check plugin compatibility before Jenkins upgrades
