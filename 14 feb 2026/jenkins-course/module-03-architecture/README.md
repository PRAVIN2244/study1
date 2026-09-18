# Module 03 — Jenkins Architecture

## High-Level Architecture

```
                         ┌─────────────────────────────────────┐
                         │        Jenkins Controller           │
                         │  (formerly "Master")                │
                         │                                     │
                         │  ┌───────────┐  ┌───────────────┐  │
                         │  │ Web UI    │  │ REST API      │  │
                         │  └───────────┘  └───────────────┘  │
                         │  ┌───────────┐  ┌───────────────┐  │
                         │  │ Scheduler │  │ Plugin Engine │  │
                         │  └───────────┘  └───────────────┘  │
                         │  ┌───────────┐  ┌───────────────┐  │
                         │  │ Build     │  │ Credentials   │  │
                         │  │ Queue     │  │ Store         │  │
                         │  └───────────┘  └───────────────┘  │
                         └──────────┬──────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
              │  Agent 1  │  │  Agent 2  │  │  Agent 3  │
              │  (Linux)  │  │ (Windows) │  │  (Docker) │
              │           │  │           │  │           │
              │ Executor  │  │ Executor  │  │ Executor  │
              │ Executor  │  │ Executor  │  │ Executor  │
              └───────────┘  └───────────┘  └───────────┘
```

## Controller (Master) Responsibilities

The controller is the central brain of Jenkins:

| Responsibility | Description |
|---------------|-------------|
| **Scheduling** | Decides which jobs run on which agents |
| **Build Queue** | Manages pending builds waiting for executors |
| **Configuration** | Stores all job/pipeline configurations |
| **Plugin Management** | Loads and manages plugins |
| **Web Interface** | Serves the UI and REST API |
| **Monitoring** | Tracks agent health and build status |
| **Security** | Handles authentication and authorization |
| **Artifact Storage** | Stores build artifacts and logs |

⚠️ **Best Practice**: The controller should NOT run builds itself in production. Delegate all builds to agents.

## Agent (Slave) Responsibilities

Agents are worker machines that execute builds:

- Receive build instructions from the controller
- Execute build steps in a workspace
- Report results back to the controller
- Can run multiple builds simultaneously (one per executor)

## Executors

An executor is a computational slot on an agent (or controller) that runs a build.

```
Agent (4 executors)
├── Executor #1: Running "build-frontend" ████████░░ 80%
├── Executor #2: Running "test-backend"   ██████░░░░ 60%
├── Executor #3: Idle
└── Executor #4: Running "deploy-staging" ██░░░░░░░░ 20%
```

- Each executor runs one build at a time
- Number of executors = number of concurrent builds on that agent
- Rule of thumb: set executors = number of CPU cores (for CPU-bound builds)

## Build Queue and Scheduling

```
                    ┌─────────────────┐
  Trigger ────────▶ │   Build Queue   │
                    │                 │
                    │  Job A (waiting)│
                    │  Job B (waiting)│
                    │  Job C (blocked)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Scheduler     │
                    │                 │
                    │ Checks:         │
                    │ - Labels match? │
                    │ - Executor free?│
                    │ - Node online?  │
                    └────────┬────────┘
                             │
                    Assigns to Agent
```

**Queue states:**
- **Waiting**: No matching executor available
- **Blocked**: Waiting for upstream job or resource lock
- **Buildable**: Ready to run, waiting for executor
- **Stuck**: No agent matches the label/requirements

## Communication Protocols

### SSH (Recommended)

```
Controller ──── SSH (port 22) ────▶ Agent
```

- Controller initiates connection to agent
- Agent needs: SSH server, Java installed
- Most secure and reliable method

### JNLP / WebSocket (Inbound)

```
Agent ──── JNLP (port 50000) ────▶ Controller
```

- Agent initiates connection to controller
- Useful when agent is behind a firewall
- Agent runs `agent.jar` which connects back to controller

### Comparison

| Feature | SSH | JNLP/WebSocket |
|---------|-----|-----------------|
| Direction | Controller → Agent | Agent → Controller |
| Firewall | Need access to agent | Need access to controller |
| Setup | SSH keys on agent | Download agent.jar |
| Reliability | High | High (with reconnection) |
| Use Case | Linux agents | Windows / firewalled agents |

## Request Flow: What Happens When a Build Triggers

```
1. Trigger Event (webhook, timer, manual)
       │
2. Jenkins Controller receives trigger
       │
3. Job enters Build Queue
       │
4. Scheduler evaluates:
   ├── Which agents match the job's label expression?
   ├── Which matching agents have free executors?
   └── Apply load balancing
       │
5. Assign job to agent executor
       │
6. Agent:
   ├── Creates/cleans workspace directory
   ├── Checks out source code (SCM)
   ├── Executes build steps
   ├── Archives artifacts (if configured)
   └── Reports status back to controller
       │
7. Controller:
   ├── Stores build log
   ├── Updates build status
   ├── Sends notifications (email, Slack)
   └── Triggers downstream jobs (if configured)
```

## File System Layout on Agent

```
/home/jenkins/              # Agent root (configurable)
├── workspace/
│   ├── job-name/           # Workspace for "job-name"
│   │   ├── src/
│   │   ├── pom.xml
│   │   └── target/
│   └── another-job/
├── remoting/
│   ├── jarCache/           # Cached JARs from controller
│   └── logs/
└── tools/                  # Auto-installed tools (Maven, JDK, etc.)
    ├── maven/
    └── jdk/
```

## Labels and Node Assignment

Labels let you direct jobs to specific agents:

```groovy
// Jenkinsfile
pipeline {
    agent { label 'linux && docker' }
    // This job runs only on agents with BOTH labels
    stages {
        stage('Build') {
            steps {
                sh 'docker build -t myapp .'
            }
        }
    }
}
```

**Label expressions:**
- `linux` — any agent with label "linux"
- `linux && docker` — agent must have both labels
- `linux || windows` — agent with either label
- `!windows` — any agent except those labeled "windows"

## Distributed Build Architecture Patterns

### Pattern 1: Simple (Small Team)

```
┌────────────┐
│ Controller │──── 2-3 static agents
│ + builds   │
└────────────┘
```

### Pattern 2: Dedicated Agents (Medium Team)

```
┌────────────┐
│ Controller │──── Linux agents (build)
│ (no builds)│──── Windows agents (test)
└────────────┘──── Deploy agents (deploy)
```

### Pattern 3: Cloud-Based (Large Team)

```
┌────────────┐
│ Controller │──── Kubernetes plugin → ephemeral pods
│ (no builds)│──── EC2 plugin → on-demand instances
└────────────┘──── Docker plugin → containers
```

Ephemeral agents spin up for each build and terminate after — no idle resources.
