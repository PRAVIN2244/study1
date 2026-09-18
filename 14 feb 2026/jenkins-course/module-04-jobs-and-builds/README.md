# Module 04 — Jobs and Builds

## Job Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Freestyle** | GUI-configured job | Simple builds, beginners |
| **Pipeline** | Code-defined (Jenkinsfile) | Complex workflows |
| **Multibranch Pipeline** | Auto-discovers branches | Branch-based development |
| **Organization Folder** | Scans entire GitHub/GitLab org | Large organizations |
| **Matrix** | Run same job across multiple configurations | Cross-platform testing |

## Freestyle Jobs

### Creating a Freestyle Job

1. **Dashboard → New Item → Freestyle project**
2. Configure sections:

#### General
- Description
- Discard old builds (keep last N builds)
- Parameterized build
- Throttle concurrent builds

#### Source Code Management
```
Git:
  Repository URL: https://github.com/user/repo.git
  Credentials: (select stored credentials)
  Branch: */main
```

#### Build Triggers

| Trigger | Configuration | Description |
|---------|--------------|-------------|
| **Poll SCM** | `H/5 * * * *` | Check for changes every 5 minutes |
| **Webhook** | GitHub/GitLab webhook | Trigger on push events |
| **Build periodically** | `H 2 * * *` | Run at 2 AM daily |
| **Upstream** | After job X completes | Chain jobs together |
| **Manual** | (default) | Click "Build Now" |

**Cron syntax:**
```
MINUTE HOUR DOM MONTH DOW
  │      │   │    │    │
  │      │   │    │    └── Day of week (0-7, 0/7=Sun)
  │      │   │    └─────── Month (1-12)
  │      │   └──────────── Day of month (1-31)
  │      └───────────────── Hour (0-23)
  └──────────────────────── Minute (0-59)

H = hash-based spread (avoids all jobs running at :00)

Examples:
  H/15 * * * *        Every 15 minutes
  H 0 * * *           Once a day around midnight
  H 9-17 * * 1-5      Once per hour, 9-5, weekdays
  H H 1,15 * *        Twice a month (1st and 15th)
```

#### Build Steps

```bash
# Execute shell
echo "Building project..."
mvn clean package -DskipTests

# Or for Windows
# Execute Windows batch command
echo Building project...
mvn clean package -DskipTests
```

#### Post-Build Actions
- Archive artifacts: `target/*.jar`
- Publish JUnit test results: `target/surefire-reports/*.xml`
- Email notification
- Trigger downstream jobs

## Parameterized Builds

Add parameters to make jobs flexible:

```
Parameter Types:
├── String Parameter      → free text input
├── Boolean Parameter     → true/false checkbox
├── Choice Parameter      → dropdown selection
├── Password Parameter    → masked input
├── File Parameter        → upload a file
├── Multi-line String     → text area
└── Run Parameter         → select a build from another job
```

### Example: Parameterized Freestyle Job

```
Parameters:
  - Choice: ENVIRONMENT = [dev, staging, production]
  - String: BRANCH = main
  - Boolean: RUN_TESTS = true

Build Step (shell):
  echo "Deploying branch $BRANCH to $ENVIRONMENT"
  if [ "$RUN_TESTS" = "true" ]; then
    mvn test
  fi
  ./deploy.sh $ENVIRONMENT
```

### Parameterized Pipeline

```groovy
pipeline {
    agent any
    parameters {
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'])
        string(name: 'BRANCH', defaultValue: 'main', description: 'Branch to build')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run tests?')
    }
    stages {
        stage('Build') {
            steps {
                echo "Building ${params.BRANCH} for ${params.ENVIRONMENT}"
            }
        }
        stage('Test') {
            when { expression { params.RUN_TESTS } }
            steps {
                sh 'mvn test'
            }
        }
        stage('Deploy') {
            steps {
                sh "./deploy.sh ${params.ENVIRONMENT}"
            }
        }
    }
}
```

## Build Triggers in Detail

### Webhook (GitHub)

1. In Jenkins: Enable "GitHub hook trigger for GITScm polling"
2. In GitHub repo: Settings → Webhooks → Add webhook
   ```
   Payload URL: https://jenkins.example.com/github-webhook/
   Content type: application/json
   Events: Just the push event
   ```

### Webhook (GitLab)

1. Install GitLab Plugin in Jenkins
2. In Jenkins job: Build Triggers → "Build when a change is pushed to GitLab"
3. In GitLab: Settings → Webhooks
   ```
   URL: https://jenkins.example.com/project/job-name
   Secret Token: (from Jenkins trigger config)
   Trigger: Push events, Merge request events
   ```

### Upstream/Downstream Chaining

```
Job A (build) ──triggers──▶ Job B (test) ──triggers──▶ Job C (deploy)
```

Configure in Job B: Build Triggers → "Build after other projects are built" → Job A

## Build Environment

### Environment Variables

Jenkins provides built-in variables:

| Variable | Description |
|----------|-------------|
| `BUILD_NUMBER` | Current build number |
| `BUILD_ID` | Build identifier |
| `JOB_NAME` | Name of the job |
| `WORKSPACE` | Absolute path to workspace |
| `JENKINS_URL` | URL of Jenkins instance |
| `GIT_COMMIT` | Current Git commit hash |
| `GIT_BRANCH` | Current Git branch |
| `BUILD_URL` | URL to this build |
| `NODE_NAME` | Name of the agent |

```bash
# Use in shell build step
echo "Build #${BUILD_NUMBER} of ${JOB_NAME}"
echo "Commit: ${GIT_COMMIT}"
echo "Workspace: ${WORKSPACE}"
```

### Custom Environment Variables

```groovy
pipeline {
    agent any
    environment {
        APP_NAME = 'my-app'
        VERSION = sh(script: 'cat VERSION', returnStdout: true).trim()
        DEPLOY_KEY = credentials('deploy-key-id')
    }
    stages {
        stage('Build') {
            steps {
                echo "Building ${APP_NAME} v${VERSION}"
            }
        }
    }
}
```

## Artifacts

### Archiving Artifacts

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn package'
            }
        }
    }
    post {
        success {
            archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
        }
    }
}
```

### Copying Artifacts Between Jobs

Install **Copy Artifact Plugin**:

```groovy
// In downstream job
stage('Get Artifact') {
    steps {
        copyArtifacts(
            projectName: 'upstream-job',
            filter: 'target/*.jar',
            target: 'libs/',
            selector: lastSuccessful()
        )
    }
}
```

## Build Status and Notifications

### Build Results

| Status | Meaning |
|--------|---------|
| **SUCCESS** (blue) | All steps completed without errors |
| **UNSTABLE** (yellow) | Build succeeded but with warnings (e.g., test failures) |
| **FAILURE** (red) | Build failed |
| **ABORTED** (grey) | Build was manually cancelled |
| **NOT_BUILT** | Build was not executed |

### Post-Build Notifications

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps { sh 'mvn package' }
        }
    }
    post {
        success {
            slackSend(color: 'good', message: "Build ${BUILD_NUMBER} succeeded")
        }
        failure {
            slackSend(color: 'danger', message: "Build ${BUILD_NUMBER} failed")
            emailext(
                subject: "FAILED: ${JOB_NAME} #${BUILD_NUMBER}",
                body: "Check: ${BUILD_URL}",
                to: 'team@example.com'
            )
        }
        always {
            cleanWs()  // Clean workspace
        }
    }
}
```

## Workspace Management

```groovy
pipeline {
    agent any
    options {
        // Clean workspace before build
        skipDefaultCheckout()
    }
    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
            }
        }
        stage('Build') {
            steps {
                sh 'ls -la'
                sh 'mvn clean package'
            }
        }
    }
    post {
        always {
            cleanWs()  // Clean after build
        }
    }
}
```
