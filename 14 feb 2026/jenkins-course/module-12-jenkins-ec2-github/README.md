# Module 12: Jenkins on EC2 — GitHub Integration, Webhooks & API

## What This Module Covers

How to run Jenkins on an EC2 instance and connect it to GitHub so that:
- A `git push` automatically triggers a Jenkins build
- Jenkins reports build status back to GitHub (pass/fail checks)
- You can use the GitHub API from Jenkins and vice versa

---

## 1. Jenkins on EC2 — Setup

### 1.1 Launch EC2 Instance

**AWS Console steps:**

| Setting | Value |
|---------|-------|
| AMI | Ubuntu 22.04 LTS |
| Instance Type | t3.medium (2 vCPU, 4 GB — minimum for Jenkins) |
| Storage | 30 GB gp3 |
| Security Group | See below |
| Key Pair | Create or select existing |

**Security Group rules:**

| Type | Port | Source | Why |
|------|------|--------|-----|
| SSH | 22 | Your IP | Admin access |
| Custom TCP | 8080 | 0.0.0.0/0 | Jenkins web UI |
| HTTPS | 443 | 0.0.0.0/0 | If using reverse proxy |

> ⚠️ In production, restrict port 8080 to your VPN/office IP. Opening to 0.0.0.0/0 is for learning only.

### 1.2 Install Jenkins on EC2

SSH into the instance:

```bash
ssh -i my-key.pem ubuntu@<EC2-PUBLIC-IP>
```

Install Jenkins:

```bash
sudo hostnamectl set-hostname jenkinsmaster
```

```
# No output — sets the hostname
```

```bash
sudo apt update && sudo apt install -y fontconfig openjdk-17-jre
```

```
# Expected output (last lines):
# Setting up openjdk-17-jre:amd64 ...
# Setting up fontconfig ...
```

```bash
java -version
```

```
# Expected output:
# openjdk version "17.0.x" 2024-xx-xx
# OpenJDK Runtime Environment (build 17.0.x+x-Ubuntu-...)
# OpenJDK 64-Bit Server VM (build 17.0.x+x-Ubuntu-..., mixed mode, sharing)
```

```bash
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update && sudo apt install -y jenkins
```

```
# Expected output (last lines):
# Setting up jenkins (2.xxx.x) ...
```

```bash
sudo systemctl enable jenkins && sudo systemctl start jenkins
sudo systemctl status jenkins
```

```
# Expected output:
# ● jenkins.service - Jenkins Continuous Integration Server
#      Loaded: loaded (/lib/systemd/system/jenkins.service; enabled; ...)
#      Active: active (running) since ...
#    Main PID: 12345 (java)
```

Get the initial admin password:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

```
# Expected output:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Open `http://<EC2-PUBLIC-IP>:8080` in your browser, paste the password, install suggested plugins, create your admin user.

### 1.3 Network Requirement — Jenkins Must Be Reachable from GitHub

```
GitHub (internet) ──webhook POST──▶ http://<EC2-PUBLIC-IP>:8080/github-webhook/
```

For GitHub webhooks to work, Jenkins must have a **public IP or domain** that GitHub can reach. Options:

| Method | When to Use |
|--------|-------------|
| EC2 public IP + port 8080 open | Learning/dev |
| Elastic IP + Nginx reverse proxy + SSL | Staging |
| ALB + Route53 + ACM certificate | Production |
| Ngrok tunnel | Quick testing from private network |

---

## 2. How Jenkins and GitHub Communicate

### 2.1 The Complete Flow

```
Developer          GitHub              Jenkins (EC2)          Build Agent
   │                  │                     │                      │
   │── git push ─────▶│                     │                      │
   │                  │                     │                      │
   │                  │── webhook POST ────▶│                      │
   │                  │   (payload: repo,   │                      │
   │                  │    branch, commit)  │                      │
   │                  │                     │                      │
   │                  │                     │── assign build ─────▶│
   │                  │                     │                      │
   │                  │                     │                      │── clone repo
   │                  │                     │                      │── run pipeline
   │                  │                     │                      │── report result
   │                  │                     │                      │
   │                  │                     │◀── build result ─────│
   │                  │                     │                      │
   │                  │◀── GitHub API ──────│                      │
   │                  │   (commit status:   │                      │
   │                  │    success/failure) │                      │
   │                  │                     │                      │
   │◀── status shown ─│                     │                      │
   │   (green check   │                     │                      │
   │    or red X)     │                     │                      │
```

### 2.2 Two Directions of Communication

| Direction | Method | What Happens |
|-----------|--------|--------------|
| GitHub → Jenkins | Webhook (HTTP POST) | GitHub sends a POST request to Jenkins when events occur (push, PR, etc.) |
| Jenkins → GitHub | GitHub REST API | Jenkins calls GitHub API to report build status, create comments, fetch repo info |

### 2.3 Authentication Between the Two

```
┌─────────────────────────────────────────────────────────────┐
│                    CREDENTIALS NEEDED                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GitHub → Jenkins (webhook):                                 │
│    • Webhook secret (shared secret for HMAC verification)    │
│    • Jenkins validates the X-Hub-Signature-256 header        │
│                                                              │
│  Jenkins → GitHub (API calls):                               │
│    • GitHub Personal Access Token (PAT) or GitHub App        │
│    • Stored in Jenkins Credentials Manager                   │
│    • Used for: cloning private repos, posting commit status  │
│                                                              │
│  Jenkins → GitHub (clone repo):                              │
│    • SSH key (deploy key) or PAT over HTTPS                  │
│    • SSH: Jenkins private key → GitHub deploy key (public)   │
│    • HTTPS: PAT as password with username                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Setting Up GitHub → Jenkins (Webhooks)

### 3.1 What Is a Webhook?

A webhook is an HTTP POST request that GitHub sends to a URL you specify whenever an event happens in your repository. Jenkins listens on a specific endpoint and triggers a build when it receives the POST.

```
Event: developer pushes code
  │
  ▼
GitHub checks: "Are there webhooks configured for this repo?"
  │
  ▼
GitHub sends HTTP POST to: http://<JENKINS-URL>/github-webhook/
  │
  ▼
POST body contains JSON:
  {
    "ref": "refs/heads/main",
    "repository": { "full_name": "myorg/myapp", "clone_url": "..." },
    "head_commit": { "id": "abc123...", "message": "fix login bug" },
    "pusher": { "name": "developer1" }
  }
  │
  ▼
Jenkins receives POST → matches to a job configured for that repo → triggers build
```

### 3.2 Install GitHub Plugin in Jenkins

1. Go to **Manage Jenkins → Plugins → Available plugins**
2. Search for **"GitHub"** (not "GitHub Branch Source" — that's for multibranch)
3. Install **"GitHub plugin"**
4. Restart Jenkins

### 3.3 Create a GitHub Personal Access Token (PAT)

In GitHub:

1. Go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click **Generate new token**
3. Configure:

| Setting | Value |
|---------|-------|
| Token name | jenkins-ci |
| Expiration | 90 days (or custom) |
| Repository access | Only select repositories → pick your repo |
| Permissions | Contents: Read, Commit statuses: Read and write, Webhooks: Read and write |

4. Click **Generate token**
5. **Copy the token immediately** — you won't see it again

### 3.4 Add the PAT to Jenkins Credentials

1. Go to **Manage Jenkins → Credentials → System → Global credentials**
2. Click **Add Credentials**
3. Configure:

| Field | Value |
|-------|-------|
| Kind | Username with password |
| Scope | Global |
| Username | your-github-username |
| Password | paste the PAT here |
| ID | github-pat |
| Description | GitHub PAT for myorg |

### 3.5 Configure GitHub Server in Jenkins

1. Go to **Manage Jenkins → System → GitHub → GitHub Servers**
2. Click **Add GitHub Server**
3. Configure:

| Field | Value |
|-------|-------|
| Name | GitHub |
| API URL | https://api.github.com |
| Credentials | Select the PAT you just added |

4. Click **Test connection**

```
# Expected output:
# Credentials verified for user your-github-username, rate limit: 4999/5000
```

5. Check **"Manage hooks"** — this lets Jenkins auto-create webhooks in your repos

### 3.6 Configure the Webhook in GitHub (Manual Method)

If you prefer to set up the webhook manually instead of auto-manage:

1. Go to your GitHub repo → **Settings → Webhooks → Add webhook**
2. Configure:

| Field | Value |
|-------|-------|
| Payload URL | `http://<EC2-PUBLIC-IP>:8080/github-webhook/` |
| Content type | application/json |
| Secret | (optional but recommended — a random string) |
| Events | "Just the push event" or select specific events |
| Active | ✅ checked |

3. Click **Add webhook**
4. GitHub sends a **ping** event to verify:

```
# In the webhook's Recent Deliveries tab:
# ✅ ping — 200 OK
```

> ⚠️ The trailing slash in `/github-webhook/` is required. Without it, Jenkins returns 302 redirect and the webhook fails.

### 3.7 Create a Jenkins Job That Triggers on Push

**Freestyle job:**

1. New Item → Freestyle project → name: `my-app-build`
2. **Source Code Management** → Git
   - Repository URL: `https://github.com/myorg/myapp.git`
   - Credentials: select `github-pat`
   - Branch: `*/main`
3. **Build Triggers** → check **"GitHub hook trigger for GITScm polling"**
4. **Build Steps** → Execute shell:
   ```bash
   echo "Build triggered by GitHub webhook"
   echo "Commit: $GIT_COMMIT"
   echo "Branch: $GIT_BRANCH"
   ```
5. Save

**Pipeline job (Jenkinsfile):**

```groovy
pipeline {
    agent any

    triggers {
        githubPush()    // Listen for GitHub webhook push events
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/myorg/myapp.git',
                    branch: 'main',
                    credentialsId: 'github-pat'
            }
        }
        stage('Build') {
            steps {
                sh 'echo "Building commit: ${GIT_COMMIT}"'
            }
        }
    }
}
```

### 3.8 Test the Webhook

```bash
# On your local machine:
cd myapp
echo "test" >> README.md
git add . && git commit -m "test webhook" && git push
```

Check Jenkins — the job should start within seconds.

```
# Jenkins console output:
# Started by GitHub push by developer1
# Building in workspace /var/lib/jenkins/workspace/my-app-build
# ...
# Finished: SUCCESS
```

If the build doesn't trigger, check:

| Problem | Fix |
|---------|-----|
| Webhook shows ❌ in GitHub | Check Jenkins URL is reachable from internet |
| 403 Forbidden | Check Jenkins CSRF settings: Manage Jenkins → Security → enable "crumb" |
| 404 Not Found | Verify URL ends with `/github-webhook/` (trailing slash) |
| Job doesn't trigger | Verify "GitHub hook trigger for GITScm polling" is checked |

---

## 4. Setting Up Jenkins → GitHub (API Calls)

### 4.1 Reporting Build Status to GitHub

When Jenkins finishes a build, it can report the result back to GitHub as a **commit status**. This shows as a green check ✅ or red X ❌ next to the commit.

**How it works internally:**

```
Jenkins build finishes
  │
  ▼
Jenkins calls GitHub API:
  POST https://api.github.com/repos/myorg/myapp/statuses/<COMMIT-SHA>
  Headers:
    Authorization: token ghp_xxxxxxxxxxxx
    Content-Type: application/json
  Body:
    {
      "state": "success",          // or "failure", "pending", "error"
      "target_url": "http://<JENKINS-URL>/job/my-app-build/42/",
      "description": "Build passed",
      "context": "jenkins/build"
    }
  │
  ▼
GitHub receives this and shows the status on the commit/PR
```

### 4.2 Pipeline with Commit Status Reporting

```groovy
pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/myorg/myapp.git',
                    branch: 'main',
                    credentialsId: 'github-pat'
            }
        }

        stage('Set Pending Status') {
            steps {
                // Tell GitHub: "build is running"
                githubNotify context: 'jenkins/build',
                             status: 'PENDING',
                             description: 'Build in progress'
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }

        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
    }

    post {
        success {
            // Tell GitHub: "build passed"
            githubNotify context: 'jenkins/build',
                         status: 'SUCCESS',
                         description: 'Build passed'
        }
        failure {
            // Tell GitHub: "build failed"
            githubNotify context: 'jenkins/build',
                         status: 'FAILURE',
                         description: 'Build failed'
        }
    }
}
```

```
# Console output:
# Setting commit status on GitHub: PENDING
# [Pipeline] sh
# + mvn clean package -DskipTests
# ...
# [Pipeline] sh
# + mvn test
# ...
# Setting commit status on GitHub: SUCCESS
# Finished: SUCCESS
```

> The `githubNotify` step requires the **GitHub plugin** and a configured GitHub server (Section 3.5).

### 4.3 Using the GitHub API Directly from Pipeline

If you need more control than `githubNotify` provides, call the API directly:

```groovy
pipeline {
    agent any

    environment {
        GITHUB_TOKEN = credentials('github-pat-secret-text')  // Secret text credential
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh 'make build'
            }
        }

        stage('Comment on PR') {
            when {
                expression { env.CHANGE_ID != null }  // Only on PR builds
            }
            steps {
                sh '''
                    curl -s -X POST \
                      -H "Authorization: token $GITHUB_TOKEN" \
                      -H "Accept: application/vnd.github.v3+json" \
                      https://api.github.com/repos/myorg/myapp/issues/${CHANGE_ID}/comments \
                      -d '{"body": "Build #'${BUILD_NUMBER}' passed. [View logs]('${BUILD_URL}')"}'
                '''
            }
        }
    }
}
```

```
# Console output:
# + curl -s -X POST -H 'Authorization: token ****' ...
# {"id":123456,"body":"Build #42 passed. [View logs](http://jenkins:8080/job/...)"}
```

### 4.4 Common GitHub API Calls from Jenkins

| Action | API Endpoint | Method |
|--------|-------------|--------|
| Set commit status | `/repos/{owner}/{repo}/statuses/{sha}` | POST |
| Comment on PR | `/repos/{owner}/{repo}/issues/{number}/comments` | POST |
| List PR files | `/repos/{owner}/{repo}/pulls/{number}/files` | GET |
| Create release | `/repos/{owner}/{repo}/releases` | POST |
| Get repo info | `/repos/{owner}/{repo}` | GET |
| Download artifact | `/repos/{owner}/{repo}/zipball/{ref}` | GET |

**Example — Create a GitHub Release after successful deploy:**

```groovy
stage('Create Release') {
    when {
        branch 'main'
    }
    steps {
        script {
            def version = sh(script: 'cat VERSION', returnStdout: true).trim()
            sh """
                curl -s -X POST \
                  -H "Authorization: token \$GITHUB_TOKEN" \
                  -H "Accept: application/vnd.github.v3+json" \
                  https://api.github.com/repos/myorg/myapp/releases \
                  -d '{
                    "tag_name": "v${version}",
                    "name": "Release v${version}",
                    "body": "Deployed by Jenkins build #${BUILD_NUMBER}",
                    "draft": false,
                    "prerelease": false
                  }'
            """
        }
    }
}
```

---

## 5. GitHub API Calling Jenkins (Reverse Direction)

GitHub can also trigger specific Jenkins actions via the Jenkins Remote API:

### 5.1 Trigger a Jenkins Job from GitHub Actions

If you use GitHub Actions for some workflows but need to trigger a Jenkins job:

```yaml
# .github/workflows/trigger-jenkins.yml
name: Trigger Jenkins Deploy

on:
  release:
    types: [published]

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Jenkins job
        run: |
          curl -X POST \
            "http://<JENKINS-URL>/job/deploy-production/build" \
            --user "${{ secrets.JENKINS_USER }}:${{ secrets.JENKINS_API_TOKEN }}" \
            -H "Jenkins-Crumb: $(curl -s 'http://<JENKINS-URL>/crumbIssuer/api/json' \
              --user '${{ secrets.JENKINS_USER }}:${{ secrets.JENKINS_API_TOKEN }}' \
              | jq -r '.crumb')"
```

### 5.2 Jenkins Remote API Endpoints

| Action | Endpoint | Method |
|--------|----------|--------|
| Trigger build | `/job/{name}/build` | POST |
| Trigger with parameters | `/job/{name}/buildWithParameters?PARAM=value` | POST |
| Get build status | `/job/{name}/lastBuild/api/json` | GET |
| Get build console | `/job/{name}/{number}/consoleText` | GET |
| Get job config | `/job/{name}/config.xml` | GET |

### 5.3 Generate Jenkins API Token

1. Log into Jenkins as your user
2. Click your username (top right) → **Configure**
3. **API Token** → **Add new Token** → name it → **Generate**
4. Copy the token

Use it with: `curl --user username:api-token http://jenkins/...`

---

## 6. Webhook Payload — What Jenkins Receives

When GitHub sends a webhook, the JSON payload contains everything Jenkins needs:

### 6.1 Push Event Payload (Key Fields)

```json
{
  "ref": "refs/heads/main",
  "before": "abc1234...",
  "after": "def5678...",
  "repository": {
    "full_name": "myorg/myapp",
    "clone_url": "https://github.com/myorg/myapp.git",
    "ssh_url": "git@github.com:myorg/myapp.git",
    "default_branch": "main"
  },
  "pusher": {
    "name": "developer1",
    "email": "dev@example.com"
  },
  "head_commit": {
    "id": "def5678...",
    "message": "fix: resolve login timeout",
    "timestamp": "2024-01-15T10:30:00Z",
    "author": {
      "name": "developer1"
    }
  },
  "commits": [
    {
      "id": "def5678...",
      "message": "fix: resolve login timeout",
      "added": ["src/auth/login.java"],
      "removed": [],
      "modified": ["src/auth/session.java"]
    }
  ]
}
```

### 6.2 Pull Request Event Payload (Key Fields)

```json
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "title": "Add user authentication",
    "head": {
      "ref": "feature/auth",
      "sha": "abc1234..."
    },
    "base": {
      "ref": "main"
    },
    "user": {
      "login": "developer1"
    }
  },
  "repository": {
    "full_name": "myorg/myapp"
  }
}
```

### 6.3 Accessing Webhook Data in Jenkins Pipeline

```groovy
pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Info') {
            steps {
                script {
                    echo "Branch: ${env.GIT_BRANCH}"
                    echo "Commit: ${env.GIT_COMMIT}"
                    echo "Author: ${env.GIT_AUTHOR_NAME}"
                    echo "URL: ${env.GIT_URL}"
                    echo "Build cause: ${currentBuild.getBuildCauses()[0].shortDescription}"
                }
            }
        }
    }
}
```

```
# Console output:
# Branch: origin/main
# Commit: def5678abcdef1234567890abcdef12345678abcd
# Author: developer1
# URL: https://github.com/myorg/myapp.git
# Build cause: Started by GitHub push by developer1
```

---

## 7. Complete Setup Checklist

```
Step 1: EC2 Instance
  ├── Launch Ubuntu 22.04, t3.medium, 30GB
  ├── Security group: 22 (SSH), 8080 (Jenkins)
  └── Note the public IP

Step 2: Install Jenkins
  ├── Install Java 17
  ├── Add Jenkins repo and install
  ├── Start Jenkins, get initial password
  └── Complete setup wizard

Step 3: GitHub PAT
  ├── Create fine-grained token
  ├── Permissions: contents:read, statuses:write, webhooks:write
  └── Copy token

Step 4: Jenkins Credentials
  ├── Add PAT as "Username with password" credential
  └── ID: github-pat

Step 5: Jenkins GitHub Server
  ├── Manage Jenkins → System → GitHub Servers
  ├── Add server with API URL and credential
  ├── Test connection
  └── Enable "Manage hooks"

Step 6: Create Pipeline Job
  ├── Source: Git repo URL + credentials
  ├── Trigger: GitHub hook trigger for GITScm polling
  └── Pipeline: from Jenkinsfile or inline

Step 7: Verify
  ├── Push a commit
  ├── Check Jenkins: build starts automatically
  ├── Check GitHub: commit shows status (✅ or ❌)
  └── Check webhook deliveries in GitHub repo settings
```

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Webhook shows 403 | CSRF protection blocking | Manage Jenkins → Security → Configure CSRF, or add webhook secret |
| Webhook shows 404 | Wrong URL | Ensure URL ends with `/github-webhook/` (trailing slash) |
| Webhook shows timeout | Jenkins not reachable | Check security group, EC2 public IP, Jenkins is running |
| Build doesn't trigger | Job not configured for webhook | Check "GitHub hook trigger for GITScm polling" |
| Commit status not showing | Missing permissions | PAT needs `statuses:write` permission |
| Clone fails | Auth issue | Check credential ID matches, PAT has `contents:read` |
| "rate limit exceeded" | Too many API calls | Use GitHub App instead of PAT (higher rate limit) |
| Webhook delivers but wrong job triggers | Multiple jobs match | Use specific branch filters in job config |

---

## 9. GitHub App vs PAT — When to Use Which

| Feature | Personal Access Token (PAT) | GitHub App |
|---------|---------------------------|------------|
| Setup complexity | Simple | More complex |
| Rate limit | 5,000 req/hour | 15,000 req/hour |
| Tied to | A user account | The organization |
| Permissions | User's permissions | Fine-grained per install |
| Token expiry | Configurable | Auto-rotated (1 hour) |
| Best for | Small teams, learning | Production, organizations |

For production Jenkins setups, prefer GitHub Apps — they don't break when an employee leaves.
