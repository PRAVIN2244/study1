# Module 01 — Introduction to Jenkins

## What is Jenkins?

Jenkins is an open-source automation server written in Java. It enables developers to build, test, and deploy software through continuous integration and continuous delivery (CI/CD) pipelines.

- **Origin**: Forked from Hudson in 2011 after an Oracle dispute
- **License**: MIT
- **Language**: Java (runs on JVM)
- **Website**: https://www.jenkins.io

## CI/CD Concepts

### Continuous Integration (CI)

CI is the practice of frequently merging code changes into a shared repository, where automated builds and tests run against every change.

**Without CI:**
```
Developer A works for 2 weeks → merges → conflicts everywhere → broken build
Developer B works for 2 weeks → merges → more conflicts → days of fixing
```

**With CI:**
```
Developer A commits daily → automated build + test → immediate feedback
Developer B commits daily → automated build + test → issues caught early
```

### Continuous Delivery (CD)

CD extends CI by automatically deploying every validated change to a staging or production environment.

```
Code Commit → Build → Unit Tests → Integration Tests → Deploy to Staging → Deploy to Production
     CI ─────────────────────────────┘                        │
     CD ──────────────────────────────────────────────────────┘
```

### Continuous Deployment

A step beyond CD — every change that passes all pipeline stages is automatically deployed to production with no manual approval.

## What Problems Does Jenkins Solve?

If you have repetitive tasks that need automation, Jenkins answers three questions:

### Question 1: What to Do?

Define the task Jenkins should perform:

| Task | Example |
|------|---------|
| Build code | `mvn clean package`, `npm run build` |
| Run tests | `mvn test`, `npm test`, `pytest` |
| Deploy application | `kubectl apply`, `ansible-playbook deploy.yml` |
| Run a script | `./backup.sh`, `python migrate.py` |
| Scan for vulnerabilities | SonarQube analysis, OWASP dependency check |
| Provision infrastructure | `terraform apply` |

Tasks are defined using:
- **Freestyle jobs** — configured via the web UI (point-and-click)
- **Pipelines** — defined as code in a `Jenkinsfile` (stored in Git)

### Question 2: When to Run?

| Trigger | How It Works | Example |
|---------|-------------|---------|
| **On code push** | Git webhook fires → Jenkins starts build | Developer pushes to `main` branch |
| **On schedule** | Cron expression triggers at set time | `H 2 * * *` → every night at 2 AM |
| **Manual trigger** | User clicks "Build Now" in UI | Deploy to production on demand |
| **After another job** | Upstream job completes → downstream starts | Build finishes → tests start |
| **Based on condition** | Expression evaluates to true | Only deploy if branch is `main` |

### Question 3: Where to Run?

Jenkins can execute tasks on:

| Location | Description |
|----------|-------------|
| **Master node** | The Jenkins controller itself (not recommended for builds) |
| **Slave/agent node** | A separate machine connected to master |
| **Labeled machine** | Agent with specific label like `linux`, `docker`, `gpu` |
| **Docker container** | Ephemeral container spun up for the build |
| **Kubernetes pod** | Dynamic pod created per build |

### Authentication and Credentials

Jenkins handles authentication so users don't need to know passwords or keys:

- **Credentials store** — securely stores passwords, SSH keys, API tokens, certificates
- **Credential binding** — injects secrets into builds as environment variables
- **Masked output** — secrets are hidden in console logs (shown as `****`)
- **Scoped access** — credentials can be restricted to specific jobs or folders

Jenkins connects to external systems on behalf of users:

```
Jenkins Credentials Store
├── Git credentials      → clone private repositories
├── AWS credentials      → deploy to EC2, push to ECR
├── Docker credentials   → push images to registries
├── Artifactory token    → upload/download artifacts
├── SSH keys             → connect to remote servers
└── SonarQube token      → submit code for analysis
```

Users simply click "Build Now" — Jenkins handles all the authentication behind the scenes.

### Task Execution Modes

| Mode | Description | Example |
|------|-------------|---------|
| **Scheduled** | Run at regular intervals (cron) | Nightly builds at 2 AM |
| **On Demand** | Manual trigger via UI or API | Deploy to production |
| **Event-Based** | Triggered by external events | Build on Git push |

Instead of manually SSH-ing into a server and running commands, Jenkins automates the entire flow — connect to the server, run the application/commands, and report results.

## Why Jenkins?

| Feature | Description |
|---------|-------------|
| **Open Source** | Free, large community, extensive documentation |
| **Plugin Ecosystem** | 1800+ plugins for virtually any tool integration |
| **Pipeline as Code** | Define builds in `Jenkinsfile` stored in version control |
| **Distributed Builds** | Scale horizontally with master-agent architecture |
| **Platform Agnostic** | Runs on Linux, macOS, Windows, Docker, Kubernetes |
| **Extensible** | Write custom plugins in Java/Groovy |

### Key Advantages (with Examples)

**Connect and run automatically:**
```
Code pushed to GitLab → Webhook fires → Jenkins builds automatically
No human intervention needed.
```

**Periodic execution:**
```
Every night at 2 AM → Jenkins runs backup job
Cron: H 2 * * *
```

**Dashboard (Web UI):**
```
Access: http://<jenkins-ip>:8080

Dashboard shows:
├── Build history (last 10 builds)
├── Console logs (full output of each build)
├── Status indicators:
│   ├── Blue  = SUCCESS
│   ├── Red   = FAILURE
│   └── Yellow = UNSTABLE
└── Build duration and trends
```

**Event-based triggers:**
```
GitLab webhook → POST to Jenkins → Pipeline starts
GitHub push event → Jenkins builds the branch
```

**On-demand execution:**
```
User clicks "Build Now" → Job runs immediately
User clicks "Build with Parameters" → Enters inputs → Job runs
```

**Group of machines:**
```
Jenkins Master (controller)
├── Agent 1 (Linux, builds Java apps)
├── Agent 2 (Windows, builds .NET apps)
├── Agent 3 (Docker, runs containerized builds)
└── Agent 4 (GPU, runs ML training)

Master distributes work across all agents.
```

## Jenkins vs Other CI/CD Tools

| Feature | Jenkins | GitLab CI | GitHub Actions |
|---------|---------|-----------|----------------|
| Hosting | Self-hosted | Self-hosted / SaaS | SaaS / Self-hosted runners |
| Config | Jenkinsfile (Groovy) | .gitlab-ci.yml (YAML) | workflow YAML |
| Plugins | 1800+ | Built-in features | Marketplace actions |
| Learning Curve | Steep | Moderate | Low |
| Maintenance | High (self-managed) | Moderate | Low (GitHub manages) |
| Cost | Free (infra costs) | Free tier + paid | Free tier + paid |

## Core Terminology

- **Job/Project**: A runnable task (build, test, deploy)
- **Build**: A single execution of a job
- **Pipeline**: A sequence of stages defining the entire CI/CD workflow
- **Stage**: A logical grouping of steps (e.g., Build, Test, Deploy)
- **Step**: A single task within a stage (e.g., run a shell command)
- **Node/Agent**: A machine that executes builds
- **Master/Controller**: The central Jenkins server that orchestrates everything
- **Workspace**: The directory on an agent where a job runs
- **Artifact**: Files produced by a build (JARs, binaries, reports)
- **Trigger**: An event that starts a build (SCM change, timer, manual)

## Jenkins Workflow Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Developer   │────▶│  Git Push    │────▶│   Webhook    │
│  Commits     │     │  to Repo     │     │   Fires      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Jenkins    │
                                          │  Controller  │
                                          └──────┬───────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    ▼             ▼             ▼
                              ┌──────────┐ ┌──────────┐ ┌──────────┐
                              │ Agent 1  │ │ Agent 2  │ │ Agent 3  │
                              │ (Build)  │ │ (Test)   │ │ (Deploy) │
                              └──────────┘ └──────────┘ └──────────┘
```

## Hands-On: Explore Jenkins

After completing Module 02 (Installation), return here and:

1. Access Jenkins at `http://<your-server>:8080`
2. Navigate through the dashboard
3. Explore **Manage Jenkins** → **System Information**
4. Check installed plugins at **Manage Jenkins** → **Plugins**
5. Review the Jenkins home directory structure on disk
