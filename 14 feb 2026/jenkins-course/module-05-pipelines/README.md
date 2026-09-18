# Module 05 — Pipelines

## Pipeline Overview

A Jenkins Pipeline is a suite of plugins that supports implementing and integrating CI/CD pipelines as code.

**Two syntaxes:**
- **Declarative Pipeline** — structured, opinionated, easier to learn
- **Scripted Pipeline** — flexible, full Groovy power, steeper learning curve

## Declarative Pipeline

### Basic Structure

```groovy
pipeline {
    agent any                    // Where to run

    options {                    // Pipeline-level options
        timeout(time: 30, unit: 'MINUTES')
        retry(2)
        disableConcurrentBuilds()
    }

    environment {                // Environment variables
        APP = 'my-app'
        REGISTRY = 'docker.io/myorg'
    }

    stages {                     // Define stages
        stage('Build') {         // Stage name
            steps {              // What to do
                sh 'mvn clean package'
            }
        }
        stage('Test') {
            steps {
                sh 'mvn test'
            }
        }
        stage('Deploy') {
            steps {
                sh './deploy.sh'
            }
        }
    }

    post {                       // Post-build actions
        always { cleanWs() }
        success { echo 'Build succeeded' }
        failure { echo 'Build failed' }
    }
}
```

### Agent Directive

```groovy
// Run on any available agent
agent any

// Run on agent with specific label
agent { label 'linux' }

// Run in a Docker container
agent {
    docker {
        image 'maven:3.9-eclipse-temurin-17'
        args '-v $HOME/.m2:/root/.m2'
    }
}

// Run in a Docker container built from Dockerfile
agent {
    dockerfile {
        filename 'Dockerfile.build'
        dir 'docker'
        args '-v /tmp:/tmp'
    }
}

// Run in Kubernetes pod
agent {
    kubernetes {
        yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: maven
            image: maven:3.9-eclipse-temurin-17
            command: ['sleep', '99d']
          - name: docker
            image: docker:24-dind
            securityContext:
              privileged: true
        '''
    }
}

// No global agent — define per stage
agent none
```

### Stage-Level Agents

```groovy
pipeline {
    agent none
    stages {
        stage('Build') {
            agent { label 'linux' }
            steps {
                sh 'mvn package'
                stash includes: 'target/*.jar', name: 'app'
            }
        }
        stage('Test on Windows') {
            agent { label 'windows' }
            steps {
                unstash 'app'
                bat 'java -jar target\\app.jar --test'
            }
        }
        stage('Test on Linux') {
            agent { label 'linux' }
            steps {
                unstash 'app'
                sh 'java -jar target/app.jar --test'
            }
        }
    }
}
```

### Conditional Execution (when)

```groovy
pipeline {
    agent any
    stages {
        // Run only on main branch
        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                sh './deploy.sh production'
            }
        }

        // Run only on feature branches
        stage('Deploy to Dev') {
            when {
                branch pattern: 'feature/*', comparator: 'GLOB'
            }
            steps {
                sh './deploy.sh dev'
            }
        }

        // Run based on environment variable
        stage('Integration Tests') {
            when {
                environment name: 'RUN_INTEGRATION', value: 'true'
            }
            steps {
                sh 'mvn verify'
            }
        }

        // Run based on expression
        stage('Notify') {
            when {
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                echo 'Sending notification...'
            }
        }

        // Combine conditions
        stage('Release') {
            when {
                allOf {
                    branch 'main'
                    tag pattern: 'v\\d+\\.\\d+\\.\\d+', comparator: 'REGEXP'
                }
            }
            steps {
                sh './release.sh'
            }
        }
    }
}
```

### Parallel Stages

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'mvn package -DskipTests'
            }
        }
        stage('Tests') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh 'mvn test -Dtest.type=unit'
                    }
                }
                stage('Integration Tests') {
                    steps {
                        sh 'mvn test -Dtest.type=integration'
                    }
                }
                stage('Security Scan') {
                    steps {
                        sh 'trivy fs --exit-code 1 .'
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

### Input and Approval

```groovy
stage('Deploy to Production') {
    steps {
        // Pause and wait for manual approval
        input message: 'Deploy to production?', ok: 'Deploy',
              submitter: 'admin,release-team'

        sh './deploy.sh production'
    }
}

// With timeout
stage('Approval') {
    steps {
        timeout(time: 1, unit: 'HOURS') {
            input message: 'Approve deployment?',
                  parameters: [
                      choice(name: 'TARGET', choices: ['staging', 'production']),
                      string(name: 'VERSION', defaultValue: '1.0.0')
                  ]
        }
    }
}
```

### Credentials in Pipelines

```groovy
pipeline {
    agent any
    environment {
        // Username/password credential
        DB_CREDS = credentials('database-credentials')
        // Exposes: DB_CREDS (user:pass), DB_CREDS_USR, DB_CREDS_PSW

        // Secret text
        API_KEY = credentials('api-key-id')

        // Secret file
        KUBECONFIG = credentials('kubeconfig-file')
    }
    stages {
        stage('Deploy') {
            steps {
                sh '''
                    echo "Connecting as ${DB_CREDS_USR}"
                    ./deploy.sh --api-key ${API_KEY}
                '''
                // Credentials are masked in console output
            }
        }
    }
}

// Using withCredentials block
stage('Push Image') {
    steps {
        withCredentials([
            usernamePassword(
                credentialsId: 'docker-hub',
                usernameVariable: 'DOCKER_USER',
                passwordVariable: 'DOCKER_PASS'
            )
        ]) {
            sh '''
                echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                docker push myapp:latest
            '''
        }
    }
}
```

## Scripted Pipeline

Full Groovy flexibility:

```groovy
node('linux') {
    try {
        stage('Checkout') {
            checkout scm
        }

        stage('Build') {
            def mvnHome = tool 'Maven-3.9'
            sh "${mvnHome}/bin/mvn clean package -DskipTests"
        }

        stage('Test') {
            sh "${tool('Maven-3.9')}/bin/mvn test"
            junit 'target/surefire-reports/*.xml'
        }

        stage('Deploy') {
            if (env.BRANCH_NAME == 'main') {
                sh './deploy.sh production'
            } else {
                sh './deploy.sh staging'
            }
        }

        currentBuild.result = 'SUCCESS'
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        // Cleanup
        cleanWs()
        // Notify
        emailext(
            subject: "${currentBuild.result}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: "Check: ${env.BUILD_URL}",
            to: 'team@example.com'
        )
    }
}
```

## Shared Libraries

### What is a Shared Library?

A shared library is a **separate Git repository** containing reusable Groovy code that multiple Jenkins pipelines can call. Instead of copying the same pipeline logic into every project's Jenkinsfile, you write it once in the shared library.

```
WITHOUT shared library:                WITH shared library:

Repo A: Jenkinsfile (200 lines)        Repo A: Jenkinsfile (5 lines)
Repo B: Jenkinsfile (200 lines)  →     Repo B: Jenkinsfile (5 lines)
Repo C: Jenkinsfile (200 lines)        Repo C: Jenkinsfile (5 lines)
                                       Shared Lib: (200 lines, one place)
Same code duplicated 3 times           Code written once, used everywhere
```

### Why Use Shared Libraries?

| Problem | Solution |
|---------|----------|
| Same pipeline code in 50 repos | Write once in shared library, call from all repos |
| Pipeline change needed across all projects | Change one file in the library, all projects get the update |
| Complex Groovy logic cluttering Jenkinsfile | Move logic to library, keep Jenkinsfile clean |
| Non-developers need to trigger builds | Give them a simple Jenkinsfile that calls library functions |
| Enforce standards (security scans, approvals) | Library enforces them — teams can't skip steps |

### Directory Structure (Explained)

Create a Git repository with this structure:

```
jenkins-shared-library/          ← This is a separate Git repo
│
├── vars/                        ← MOST IMPORTANT: Global functions
│   │                               Each .groovy file becomes a callable function
│   ├── buildJava.groovy         ← Called as: buildJava()
│   ├── buildNode.groovy         ← Called as: buildNode()
│   ├── deployToK8s.groovy       ← Called as: deployToK8s()
│   ├── notifySlack.groovy       ← Called as: notifySlack()
│   └── standardPipeline.groovy  ← Called as: standardPipeline()
│
├── src/                         ← Helper Groovy classes (optional)
│   └── org/
│       └── mycompany/
│           ├── Docker.groovy    ← Utility class for Docker operations
│           └── Slack.groovy     ← Utility class for Slack messages
│
└── resources/                   ← Non-code files (templates, configs)
    └── org/
        └── mycompany/
            ├── k8s-deployment.yaml
            └── email-template.html
```

**Key rule:** The filename in `vars/` becomes the function name.
- `vars/buildJava.groovy` → call it as `buildJava()` in any pipeline
- `vars/deployToK8s.groovy` → call it as `deployToK8s()`

### Step 1: Create the Shared Library Functions

#### vars/buildJava.groovy

```groovy
// This function is called as: buildJava(version: '17', skipTests: false)
// The 'call' method is what Jenkins executes when you call buildJava()

def call(Map config = [:]) {
    // Set defaults if not provided
    def javaVersion = config.version ?: '17'
    def skipTests = config.skipTests ?: false
    def mavenGoal = skipTests ? 'package -DskipTests' : 'package'

    pipeline {
        agent { label 'build' }

        tools {
            maven 'Maven-3.9'
            jdk "JDK-${javaVersion}"
        }

        stages {
            stage('Checkout') {
                steps {
                    checkout scm    // Checks out the CALLING repo (not the library)
                }
            }

            stage('Build') {
                steps {
                    sh "mvn clean ${mavenGoal}"
                }
            }

            stage('Test') {
                when { expression { !skipTests } }
                steps {
                    sh 'mvn test'
                }
                post {
                    always {
                        junit 'target/surefire-reports/*.xml'
                    }
                }
            }

            stage('Archive') {
                steps {
                    archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
                }
            }
        }

        post {
            failure {
                echo "Build failed for ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            }
        }
    }
}
```

#### vars/deployToK8s.groovy

```groovy
// Called as: deployToK8s(namespace: 'staging', image: 'myapp:1.0')

def call(Map config) {
    def namespace = config.namespace ?: 'default'
    def image = config.image
    def deployment = config.deployment ?: env.JOB_BASE_NAME
    def timeout = config.timeout ?: 120

    if (!image) {
        error "deployToK8s requires 'image' parameter"
    }

    echo "Deploying ${image} to ${namespace}..."

    sh """
        kubectl set image deployment/${deployment} \
            ${deployment}=${image} \
            --namespace ${namespace}
        kubectl rollout status deployment/${deployment} \
            --namespace ${namespace} \
            --timeout=${timeout}s
    """

    echo "Deployment successful: ${image} → ${namespace}"
}
```

#### vars/notifySlack.groovy

```groovy
// Called as: notifySlack(status: 'SUCCESS', channel: '#builds')

def call(Map config = [:]) {
    def status = config.status ?: currentBuild.result ?: 'SUCCESS'
    def channel = config.channel ?: '#builds'
    def color = status == 'SUCCESS' ? 'good' : 'danger'

    def message = """
        *${status}*: ${env.JOB_NAME} #${env.BUILD_NUMBER}
        Branch: ${env.GIT_BRANCH ?: 'unknown'}
        Duration: ${currentBuild.durationString}
        <${env.BUILD_URL}|View Build>
    """.stripIndent()

    slackSend(channel: channel, color: color, message: message)
}
```

### Step 2: Register the Library in Jenkins

**Manage Jenkins → System → Global Pipeline Libraries**

```
Name: my-shared-library
Default version: main                    ← Git branch
☑ Load implicitly                        ← Available to all pipelines without @Library
☐ Allow default version to be overridden

Retrieval method: Modern SCM
  Source Code Management: Git
  Project Repository: https://github.com/myorg/jenkins-shared-library.git
  Credentials: github-creds
```

### Step 3: Use the Library in Jenkinsfiles

#### Simple Usage (Entire Pipeline from Library)

```groovy
// Jenkinsfile in your application repo — just 3 lines!

@Library('my-shared-library') _

buildJava(version: '17', skipTests: false)
```

**What happens:**
```
1. Jenkins loads the shared library from GitHub
2. Finds vars/buildJava.groovy
3. Calls the call() method with {version: '17', skipTests: false}
4. The pipeline defined inside buildJava.groovy runs
5. It checks out THIS repo (not the library repo)
6. Builds, tests, and archives the JAR
```

**Console output:**
```
Loading library my-shared-library@main
 > git fetch https://github.com/myorg/jenkins-shared-library.git
Loaded library my-shared-library@main
[Pipeline] stage (Checkout)
[Pipeline] checkout
Cloning repository https://github.com/myorg/my-app.git   ← YOUR app repo
[Pipeline] stage (Build)
[INFO] BUILD SUCCESS
[Pipeline] stage (Test)
Tests run: 45, Failures: 0
[Pipeline] stage (Archive)
Archiving artifacts
Finished: SUCCESS
```

#### Mixed Usage (Library Functions + Custom Stages)

```groovy
@Library('my-shared-library') _

pipeline {
    agent { label 'build' }
    stages {
        stage('Build') {
            steps {
                checkout scm
                sh 'mvn clean package -DskipTests'
            }
        }
        stage('Deploy to Staging') {
            steps {
                // Call library function inside a regular pipeline
                deployToK8s(
                    namespace: 'staging',
                    image: "myapp:${BUILD_NUMBER}",
                    timeout: 120
                )
            }
        }
        stage('Deploy to Production') {
            steps {
                input 'Deploy to production?'
                deployToK8s(
                    namespace: 'production',
                    image: "myapp:${BUILD_NUMBER}",
                    timeout: 300
                )
            }
        }
    }
    post {
        always {
            notifySlack(channel: '#deployments')
        }
    }
}
```

#### Loading Library Without Global Configuration

```groovy
// Load from a specific repo and branch — no Jenkins config needed
library identifier: 'my-lib@main',
        retriever: modernSCM([
            $class: 'GitSCMSource',
            remote: 'https://github.com/myorg/jenkins-shared-library.git',
            credentialsId: 'github-token'
        ])

// Now use functions from the library
buildJava(version: '17')
```

### Shared Library Flow Diagram

```
Developer pushes to app repo
    │
    ▼
Jenkins triggers pipeline
    │
    ▼
Reads Jenkinsfile from app repo
    │
    ├── Sees: @Library('my-shared-library')
    │
    ▼
Clones shared library repo from GitHub
    │
    ├── Loads vars/*.groovy files
    ├── Loads src/**/*.groovy classes
    │
    ▼
Executes the pipeline
    │
    ├── checkout scm → clones the APP repo (not the library)
    ├── Runs build/test/deploy steps from library code
    │
    ▼
Pipeline completes
```

### Shared Library Best Practices

1. **Version your library** — use tags (`@Library('my-lib@v1.2.0')`) in production
2. **Test your library** — write unit tests for Groovy classes in `src/`
3. **Keep `vars/` functions simple** — complex logic goes in `src/` classes
4. **Document parameters** — add comments showing expected inputs
5. **Don't hardcode values** — pass everything as parameters
6. **Use `error()` for validation** — fail fast if required params are missing

## Multibranch Pipeline

Automatically creates pipeline jobs for each branch in a repository.

### Configuration

1. **New Item → Multibranch Pipeline**
2. **Branch Sources**: Add Git/GitHub/GitLab source
3. **Build Configuration**: Jenkinsfile path (default: `Jenkinsfile`)
4. **Scan Triggers**: How often to check for new branches

```
Repository
├── main          → Pipeline job "repo/main"
├── develop       → Pipeline job "repo/develop"
├── feature/auth  → Pipeline job "repo/feature%2Fauth"
└── feature/api   → Pipeline job "repo/feature%2Fapi"
```

### Branch-Specific Behavior

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps { sh 'mvn package' }
        }
        stage('Deploy to Dev') {
            when { branch 'develop' }
            steps { sh './deploy.sh dev' }
        }
        stage('Deploy to Staging') {
            when { branch 'release/*' }
            steps { sh './deploy.sh staging' }
        }
        stage('Deploy to Production') {
            when { branch 'main' }
            steps {
                input 'Deploy to production?'
                sh './deploy.sh production'
            }
        }
    }
}
```

## Pipeline Best Practices

1. **Keep Jenkinsfile in the repository** — version control your pipeline
2. **Use declarative syntax** unless you need scripted flexibility
3. **Use shared libraries** for common patterns across projects
4. **Fail fast** — put quick checks (lint, compile) before slow ones (integration tests)
5. **Use parallel stages** for independent tasks
6. **Clean workspace** in post-always block
7. **Use credentials()** — never hardcode secrets
8. **Set timeouts** — prevent hung builds from consuming executors
9. **Use `agent none`** at pipeline level when stages need different agents
10. **Archive artifacts** for traceability

---

## Practical Pipeline Examples

The following examples demonstrate pipeline concepts progressively, from basic to advanced.

### Pipeline Syntax Overview

A pipeline is a series of tasks done in order, potentially on different servers.

- **Pipeline as Code** — declarative syntax (recommended)
- **DSL** — Groovy-based scripted pipelines
- **Jenkinsfile** — stored in your Git repository

**Advantages of pipelines over freestyle jobs:**
- Combine multiple freestyle jobs into a single pipeline
- Reuse code across stages
- A single job can connect to multiple servers
- Call other jobs from within a pipeline
- Flexible conditional logic

```
pipeline {
  stages {
    stage('stage1'){
      agent {}
      steps {}
    } // end of stage1
    stage('stage2'){
      agent {}
      steps {}
    } // end of stage2
  } // end of stages
} // end of pipeline
```

### Line-by-Line Syntax Breakdown

```groovy
pipeline {                    // Start of pipeline block — everything lives inside this
    agent any                 // WHERE to run: "any" = any available node (master or agent)
    stages {                  // Container for all stages — defines execution blocks
        stage('Stage1') {     // A logical step with a name (shown in UI)
            steps {           // Actual commands to execute
                echo 'Hello'  // Print "Hello" to the console log
            }
        }
    }
}
```

| Keyword | Purpose | Required? |
|---------|---------|-----------|
| `pipeline` | Top-level block, wraps everything | Yes |
| `agent` | Defines where the pipeline/stage runs | Yes |
| `stages` | Contains one or more `stage` blocks | Yes |
| `stage('name')` | A named group of steps (visible in UI) | Yes (at least one) |
| `steps` | Contains the actual commands | Yes (inside each stage) |
| `echo` | Prints a message to the build console | No (just a step) |
| `sh` | Runs a shell command (Linux/macOS) | No (just a step) |
| `bat` | Runs a batch command (Windows) | No (just a step) |

### Example 1: Basic Pipeline (agent any)

Runs on any available agent:

```groovy
pipeline {
    agent any
    stages {
       stage('Stage1') {
            steps {
                echo 'First Stage'
            }
        }
       stage('Stage2') {
            steps {
                echo 'Second Stage'
            }
        }
   }
}
```

**Console output:**
```
[Pipeline] Start of Pipeline
[Pipeline] node
Running on Jenkins in /var/lib/jenkins/workspace/my-job
[Pipeline] {
[Pipeline] stage
[Pipeline] { (Stage1)
[Pipeline] echo
First Stage
[Pipeline] }
[Pipeline] stage
[Pipeline] { (Stage2)
[Pipeline] echo
Second Stage
[Pipeline] }
[Pipeline] }
[Pipeline] End of Pipeline
Finished: SUCCESS
```

### Example 2: Pipeline with Labeled Agent

Runs all stages on an agent with the label `demo`:

```groovy
pipeline {
    agent { label 'demo' }
    stages {
        stage('Stage1') {
            steps {
                echo 'First Stage'
            }
        }
        stage('Stage2') {
            steps {
                echo 'Second Stage'
            }
        }
    }
}
```

### Example 3: Per-Stage Agent Assignment

Different stages run on different agents:

```groovy
pipeline {
    agent none
    stages {
        stage('Stage1') {
            agent { label 'demo' }
            steps {
                echo 'First Stage'
            }
        }
        stage('Stage2') {
            agent any
            steps {
                echo 'Second Stage'
            }
        }
    }
}
```

### Example 4: Custom Workspace

Override the default workspace directory:

```groovy
pipeline {
    agent none
    stages {
        stage('Stage1') {
            agent {
                node {
                    label 'demo'
                    customWorkspace '/tmp/jenkins'
                }
            }
            steps {
                echo 'First Stage'
            }
        }
        stage('Stage2') {
            agent any
            steps {
                echo 'Second Stage'
            }
        }
    }
}
```

### Example 5: Environment Variables (Global)

```groovy
pipeline {
    agent { label 'demo' }
    environment {
        MYNAME = 'Adam'           // Global variable — available in all stages
    }
    stages {
        stage('Stage1') {
            steps {
                sh " echo 'Your name: $MYNAME' "   // Access via shell interpolation
            }
        }
        stage('Stage2') {
            steps {
                echo env.MYNAME                     // Access via Groovy env object
            }
        }
    }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
[Pipeline] sh
+ echo 'Your name: Adam'
Your name: Adam
[Pipeline] { (Stage2)
[Pipeline] echo
Adam
```

### Example 6: Environment Variables (Local Override)

Stage-level `environment` overrides global within that stage only. Other stages still see the global value.

```groovy
pipeline {
    agent { label 'demo' }
    environment {
        MYNAME = 'global'         // Global scope
    }
    stages {
        stage('Stage1') {
            environment {
                MYNAME = 'local'  // Overrides ONLY in Stage1
            }
            steps {
                sh "echo 'Your name: $MYNAME'"
            }
        }
        stage('Stage2') {
            steps {
                echo env.MYNAME   // Still sees 'global'
            }
        }
    }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
+ echo 'Your name: local'
Your name: local
[Pipeline] { (Stage2)
[Pipeline] echo
global
```

### Example 7: Parameters (All Types)

Parameters allow user input when triggering a build. After the first run, a "Build with Parameters" button appears.

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'PERSON', defaultValue: 'Mr Adam', description: 'Who are you?')
        text(name: 'BIOGRAPHY', defaultValue: '', description: 'Enter some information about the person')
        booleanParam(name: 'TOGGLE', defaultValue: true, description: 'Toggle this value')
        choice(name: 'CHOICE', choices: ['One', 'Two', 'Three'], description: 'Pick something')
        password(name: 'PASSWORD', defaultValue: 'SECRET', description: 'Enter a password')
        file(name: "file.properties", description: "Choose a file to upload")
    }
    stages {
        stage('Example') {
            steps {
                echo "Hello ${params.PERSON}"          // Access with ${params.NAME}
                echo "Biography: ${params.BIOGRAPHY}"
                echo "Toggle: ${params.TOGGLE}"
                echo "Choice: ${params.CHOICE}"
                echo "Password: ${params.PASSWORD}"
            }
        }
    }
}
```

**Parameter types explained:**

| Type | UI Element | Example Value |
|------|-----------|---------------|
| `string` | Text input field | `Mr Adam` |
| `text` | Multi-line text area | `Born in 1990...` |
| `booleanParam` | Checkbox | `true` / `false` |
| `choice` | Dropdown menu | `One`, `Two`, `Three` |
| `password` | Masked text input | `****` (hidden in logs) |
| `file` | File upload button | `config.properties` |

**Console output:**
```
Hello Mr Adam
Biography:
Toggle: true
Choice: One
Password: ****
```

### Example 8: Options — Build Discarder

Keep only the last N builds to save disk space:

```groovy
pipeline {
    agent { label 'demo' }
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    stages {
        stage('Stage1') {
            steps {
                echo 'First Stage'
            }
        }
   }
}
```

### Example 9: Options — Retry (Pipeline Level)

`retry(3)` at pipeline level: if any stage fails, the **entire pipeline** restarts (up to 3 attempts total).

```groovy
pipeline {
    agent { label 'demo' }
    options {
       retry(3)
    }
    stages {
        stage('Stage1') {
            steps {
                sh 'exit 1'       // Forces failure (exit code 1)
            }
        }
        stage('stage2') {
            steps {
               sh 'echo Stage 2'
            }
        }
     }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
+ exit 1
ERROR: script returned exit code 1
Retrying...
[Pipeline] { (Stage1)
+ exit 1
ERROR: script returned exit code 1
Retrying...
[Pipeline] { (Stage1)
+ exit 1
ERROR: script returned exit code 1
Finished: FAILURE
```

Stage2 never runs because the pipeline-level retry restarts from Stage1 each time.

### Example 10: Options — Retry (Stage Level)

`retry(3)` at stage level: only **that stage** retries. If it still fails after 3 attempts, the pipeline fails and Stage2 does NOT run.

```groovy
pipeline {
    agent { label 'demo' }
    stages {
        stage('Stage1') {
             options {
               retry(3)           // Only Stage1 retries, not the whole pipeline
             }
            steps {
                sh 'exit 1'
            }
        }
        stage('stage2') {
            steps {
               sh 'echo Stage 2'
            }
        }
     }
}
```

**Key difference:** Pipeline-level retry restarts everything. Stage-level retry only retries that one stage.

### Example 11: Options — Timeout and Timestamps

```groovy
pipeline {
    agent { label 'demo' }
    options {
          timeout(time: 15, unit: 'SECONDS')
          timestamps()
    }
    stages {
        stage('Stage1') {
            steps {
                echo "Stage 1"
                sh 'sleep 5'
            }
        }
        stage('Stage2') {
            steps {
                echo "Stage 2"
                sh 'sleep 5'
            }
        }
    }
}
```

### Example 12: Git Checkout with Credentials

The `git` step clones a repository. Parameters explained:

```groovy
pipeline {
    agent { label 'demo' }
    stages {
        stage('Clone Repo') {
            steps {
                echo 'Going to Checkout from Git'
                git branch: 'newfeature',          // Branch to checkout
                    changelog: false,               // Don't compute changelog
                    credentialsId: 'Gitlab',        // Credential ID from Jenkins store
                    poll: false,                    // Don't poll for SCM changes
                    url: 'https://gitlab.com/myorg/myproject.git'
                echo 'Completed Checkout from Git'
            }
        }
    }
}
```

**Console output:**
```
Going to Checkout from Git
Cloning repository https://gitlab.com/myorg/myproject.git
 > git init /home/jenkins/workspace/my-job
 > git fetch --no-tags https://gitlab.com/myorg/myproject.git +refs/heads/newfeature
 > git checkout -b newfeature
Completed Checkout from Git
```

The `credentialsId: 'Gitlab'` references a credential stored in **Manage Jenkins → Credentials**. Jenkins injects the username/password or token automatically — the pipeline code never contains secrets.

### Example 13: Trigger Another Job (build job)

`build job` calls another Jenkins job by name and waits for it to complete. You can pass parameters to the child job.

```groovy
pipeline {
    agent { label 'demo' }
    stages {
        stage('Stage1') {
            steps {
              build job: 'basics', parameters: [string(name: 'YOURNAME', value: 'ADAM')]
              echo 'Completed running child job'
             }
        }
        stage('Stage2') {
            steps {
                echo 'Testing'
            }
        }
    }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
[Pipeline] build
Scheduling project: basics
Starting building: basics #5
Completed running child job
[Pipeline] { (Stage2)
Testing
Finished: SUCCESS
```

The parent pipeline pauses until the child job `basics` finishes. If the child fails, the parent also fails (unless you add `propagate: false`).

### Example 14: Directory Navigation (dir)

`dir('/path')` temporarily changes the working directory. After the `dir` block ends, you're back in the original workspace.

```groovy
pipeline {
    agent { label 'demo' }
    stages {
        stage('Stage1') {
            steps {
                  sh 'touch testfirst'        // Created in workspace
                  dir('/tmp/jenkins') {        // Switch to /tmp/jenkins
                     sh 'touch DUMMY'          // Created in /tmp/jenkins
                  }                            // Back to workspace
                  sh 'touch testlast'          // Created in workspace
            }
        }
    }
}
```

**Result:**
```
/home/jenkins/workspace/my-job/testfirst    ← created in workspace
/tmp/jenkins/DUMMY                          ← created in /tmp/jenkins
/home/jenkins/workspace/my-job/testlast     ← back in workspace
```

### Example 15: catchError — Continue on Failure

Normally, if a step fails, the pipeline stops. `catchError` catches the failure, marks the build as UNSTABLE (yellow) instead of FAILED (red), and allows subsequent stages to continue.

```groovy
pipeline {
    agent any
    stages {
        stage('Stage1') {
          steps {
             catchError(buildResult: 'UNSTABLE', message: 'ERROR FOUND') {
                 sh 'exit 1'       // This fails, but catchError handles it
             }
          }
        }
       stage('Stage2') {
            steps {
                  echo 'Running Stage2'   // This STILL runs
            }
        }
    }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
+ exit 1
ERROR FOUND
[Pipeline] { (Stage2)
Running Stage2
[Pipeline] End of Pipeline
Finished: UNSTABLE
```

**Without `catchError`:** Stage1 fails → Stage2 is skipped → build is FAILURE.
**With `catchError`:** Stage1 fails → build marked UNSTABLE → Stage2 still runs.

### Example 16: when — Environment Condition

The `when` block controls whether a stage runs. If the condition is false, the stage is skipped entirely.

```groovy
pipeline {
    agent any
    environment { DEPLOY_TO = 'qa'}       // Set to 'qa'
    stages {
        stage('Stage1') {
            when {
                  environment name: 'DEPLOY_TO', value: 'qa'    // TRUE → runs
             }
            steps {
                  echo 'Running Stage1 for QA'
            }
        }
       stage('Stage2') {
            when {
                  environment name: 'DEPLOY_TO', value: 'production'  // FALSE → skipped
             }
            steps {
                  echo 'Running Stage2 for production'
            }
        }
    }
}
```

**Console output:**
```
[Pipeline] { (Stage1)
Running Stage1 for QA
[Pipeline] { (Stage2)
Stage "Stage2" skipped due to when conditional
Finished: SUCCESS
```

Stage2 is skipped because `DEPLOY_TO` is `qa`, not `production`.

### Example 17: when — Boolean Expression

```groovy
pipeline {
    agent any
    parameters {
        booleanParam(name: 'TOGGLE', defaultValue: true, description: 'Toggle this value')
    }
    stages {
        stage('Stage1') {
            when {
                  expression { return params.TOGGLE }
            }
            steps {
                  echo 'Testing'
            }
        }
    }
}
```

### Example 18: when — equals

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'PERSON', defaultValue: 'Mr Adam', description: 'Who are you?')
    }
    stages {
        stage('Stage1') {
            when { equals expected: 'adam' , actual: params.PERSON }
            steps {
                  echo 'Hi Adam !!'
            }
        }
    }
}
```

### Example 19: when — allOf (AND Logic)

All conditions must be true:

```
COND1 AND COND2 → Result
True      True  → True
False     True  → False
True      False → False
False     False → False
```

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'PERSON', defaultValue: 'Mr Adam', description: 'Who are you?')
        booleanParam(name: 'TOGGLE', defaultValue: true, description: 'Toggle this value')
    }
    stages {
        stage('Stage1') {
            when {
              allOf {
                equals expected: 'adam' , actual: params.PERSON
                expression { return params.TOGGLE }
               }
            }
            steps {
                  echo 'Hi Adam !!'
            }
        }
    }
}
```

### Example 20: when — anyOf (OR Logic)

At least one condition must be true:

```
COND1 OR  COND2 → Result
True      True  → True
False     True  → True
True      False → True
False     False → False
```

```groovy
pipeline {
    agent any
    parameters {
        string(name: 'PERSON', defaultValue: 'Mr Adam', description: 'Who are you?')
        booleanParam(name: 'TOGGLE', defaultValue: true, description: 'Toggle this value')
    }
    stages {
        stage('Stage1') {
            when {
                anyOf {
                   equals expected: 'adam' , actual: params.PERSON
                   expression { return params.TOGGLE }
                }
             }
            steps {
                  echo 'Hi Adam !!'
            }
        }
    }
}
```

### Example 21: Post Block (Pipeline Level)

The `post` block runs after all stages complete. It executes regardless of build result when using `always`.

```groovy
pipeline {
  agent any
  stages{
    stage('stage1'){
      steps { echo "stage1"}
    }
    stage('stage2'){
      steps { echo "stage2"}
    }
  }
  post {
    always{ echo "Post Stage"}       // Runs after ALL stages, regardless of result
  }
}
```

**Console output:**
```
stage1
stage2
Post Stage
Finished: SUCCESS
```

**Available post conditions:**

| Condition | When It Runs |
|-----------|-------------|
| `always` | Always, regardless of result |
| `success` | Only if build succeeded |
| `failure` | Only if build failed |
| `unstable` | Only if build is unstable (e.g., test failures) |
| `changed` | Only if build result changed from previous build |
| `aborted` | Only if build was manually cancelled |
| `cleanup` | Runs after all other post conditions |

### Example 22: Post Block (Stage Level)

`post` can also be placed inside a specific stage — it runs after that stage completes.

```groovy
pipeline {
  agent any
  stages{
    stage('stage1'){
      steps { echo "stage1"}
      post {
         always { echo "Post Stage1" }   // Runs after stage1 only
      }
    }
    stage('stage2'){
      steps { echo "stage2"}
    }
  }
}
```

**Console output:**
```
stage1
Post Stage1
stage2
Finished: SUCCESS
```

**Common use case:** Cleanup after a specific stage (e.g., stop Docker containers, remove temp files) without affecting other stages.

---

## Multi-Stage Pipeline (Real-World Example)

A multi-stage pipeline chains multiple stages across different agents, passing artifacts between them. This is how production CI/CD pipelines work.

### What is a Multi-Stage Pipeline?

```
Stage 1          Stage 2          Stage 3          Stage 4          Stage 5
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Checkout │───▶│  Build   │───▶│  Test    │───▶│  Scan    │───▶│  Deploy  │
│          │    │          │    │          │    │          │    │          │
│ Agent:   │    │ Agent:   │    │ Agent:   │    │ Agent:   │    │ Agent:   │
│ any      │    │ maven    │    │ maven    │    │ sonar    │    │ deploy   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     │          Produces JAR    Produces reports  Pass/Fail gate  App is live
     │               │               │               │               │
     └───────────────┴───────────────┴───────────────┴───────────────┘
                        Artifacts flow forward through stages
```

### Complete Multi-Stage Pipeline

```groovy
pipeline {
    agent none                                // No default agent — each stage picks its own

    environment {
        APP_NAME    = 'my-backend-api'        // Available in ALL stages
        VERSION     = "1.0.${BUILD_NUMBER}"   // e.g., 1.0.42
        REGISTRY    = '303255670930.dkr.ecr.ap-south-1.amazonaws.com'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))   // Keep last 10 builds
        timeout(time: 30, unit: 'MINUTES')               // Entire pipeline timeout
        timestamps()                                      // Add timestamps to console
        disableConcurrentBuilds()                         // One build at a time
    }

    stages {
        // ─── STAGE 1: CHECKOUT ───────────────────────────────────────
        stage('Checkout') {
            agent { label 'build' }
            steps {
                echo "Checking out source code..."
                git branch: 'main',
                    credentialsId: 'github-creds',
                    url: 'https://github.com/myorg/my-backend-api.git'

                // Save the commit hash for later use
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "Commit: ${env.GIT_COMMIT_SHORT}"
            }
        }

        // ─── STAGE 2: BUILD ─────────────────────────────────────────
        stage('Build') {
            agent { label 'build' }
            steps {
                echo "Building ${APP_NAME} version ${VERSION}..."
                sh 'mvn clean package -DskipTests'
                // mvn clean    → deletes target/ directory
                // mvn package  → compiles and creates JAR
                // -DskipTests  → skip tests here (separate stage)
            }
            post {
                success {
                    // Archive the JAR so later stages can use it
                    archiveArtifacts artifacts: 'target/*.jar', fingerprint: true
                    echo "Build artifact archived: target/*.jar"
                }
            }
        }

        // ─── STAGE 3: UNIT TESTS ────────────────────────────────────
        stage('Unit Tests') {
            agent { label 'build' }
            steps {
                echo "Running unit tests..."
                sh 'mvn test'
            }
            post {
                always {
                    // Publish test results (visible in Jenkins UI)
                    junit 'target/surefire-reports/*.xml'
                    // Publish code coverage
                    jacoco(execPattern: '**/target/jacoco.exec')
                }
                failure {
                    echo "Unit tests FAILED — pipeline will stop here"
                }
            }
        }

        // ─── STAGE 4: SECURITY SCAN ─────────────────────────────────
        stage('Security Scan') {
            agent { label 'build' }
            parallel {
                // Run SCA and SAST in parallel (saves time)
                stage('SCA - Dependency Check') {
                    steps {
                        sh 'mvn org.owasp:dependency-check-maven:check'
                    }
                    post {
                        always {
                            dependencyCheckPublisher pattern: 'target/dependency-check-report.xml'
                        }
                    }
                }
                stage('SAST - SonarQube') {
                    steps {
                        withSonarQubeEnv('sonarqube') {
                            sh 'mvn sonar:sonar'
                        }
                    }
                }
            }
        }

        // ─── STAGE 5: QUALITY GATE ──────────────────────────────────
        stage('Quality Gate') {
            agent { label 'build' }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                    // If SonarQube quality gate FAILS → pipeline STOPS
                    // If SonarQube quality gate PASSES → continue
                }
            }
        }

        // ─── STAGE 6: DOCKER BUILD & PUSH ───────────────────────────
        stage('Docker Build & Push') {
            agent { label 'build' }
            steps {
                echo "Building Docker image..."
                sh """
                    docker build -t ${REGISTRY}/${APP_NAME}:${VERSION} .
                    docker tag ${REGISTRY}/${APP_NAME}:${VERSION} ${REGISTRY}/${APP_NAME}:latest
                """

                echo "Pushing to ECR..."
                sh """
                    aws ecr get-login-password --region ap-south-1 | \
                        docker login --username AWS --password-stdin ${REGISTRY}
                    docker push ${REGISTRY}/${APP_NAME}:${VERSION}
                    docker push ${REGISTRY}/${APP_NAME}:latest
                """
            }
        }

        // ─── STAGE 7: DEPLOY TO STAGING ─────────────────────────────
        stage('Deploy to Staging') {
            agent { label 'deploy' }
            steps {
                echo "Deploying ${APP_NAME}:${VERSION} to staging..."
                sh """
                    kubectl set image deployment/${APP_NAME} \
                        ${APP_NAME}=${REGISTRY}/${APP_NAME}:${VERSION} \
                        --namespace staging
                    kubectl rollout status deployment/${APP_NAME} \
                        --namespace staging --timeout=120s
                """
            }
        }

        // ─── STAGE 8: DEPLOY TO PRODUCTION (MANUAL APPROVAL) ────────
        stage('Deploy to Production') {
            agent { label 'deploy' }
            steps {
                // Pipeline PAUSES here and waits for human approval
                input message: "Deploy ${APP_NAME}:${VERSION} to production?",
                      ok: 'Deploy',
                      submitter: 'admin,release-team'

                echo "Deploying to production..."
                sh """
                    kubectl set image deployment/${APP_NAME} \
                        ${APP_NAME}=${REGISTRY}/${APP_NAME}:${VERSION} \
                        --namespace production
                    kubectl rollout status deployment/${APP_NAME} \
                        --namespace production --timeout=300s
                """
            }
        }
    }

    // ─── POST: RUNS AFTER ALL STAGES ─────────────────────────────────
    post {
        success {
            slackSend(
                channel: '#deployments',
                color: 'good',
                message: "SUCCESS: ${APP_NAME} v${VERSION} deployed to production"
            )
        }
        failure {
            slackSend(
                channel: '#deployments',
                color: 'danger',
                message: "FAILED: ${APP_NAME} v${VERSION} — check ${BUILD_URL}"
            )
        }
        always {
            cleanWs()    // Clean workspace after pipeline completes
        }
    }
}
```

### Console Output (Successful Run)

```
[Pipeline] Start of Pipeline
[Pipeline] timestamps
[05:32:01] [Pipeline] stage (Checkout)
[05:32:01] Checking out source code...
[05:32:03] Commit: a1b2c3d
[05:32:03] [Pipeline] stage (Build)
[05:32:03] Building my-backend-api version 1.0.42...
[05:32:15] [INFO] BUILD SUCCESS
[05:32:15] Build artifact archived: target/*.jar
[05:32:15] [Pipeline] stage (Unit Tests)
[05:32:15] Running unit tests...
[05:32:28] Tests run: 145, Failures: 0, Errors: 0, Skipped: 3
[05:32:28] [INFO] BUILD SUCCESS
[05:32:28] [Pipeline] stage (Security Scan)
[05:32:28] [Pipeline] parallel
[05:32:28]   [SCA] Running OWASP Dependency Check...
[05:32:28]   [SAST] Running SonarQube analysis...
[05:32:45]   [SCA] No vulnerabilities found with CVSS > 7.0
[05:32:50]   [SAST] Analysis report uploaded to SonarQube
[05:32:50] [Pipeline] stage (Quality Gate)
[05:32:55] SonarQube Quality Gate status: OK
[05:32:55] [Pipeline] stage (Docker Build & Push)
[05:32:55] Building Docker image...
[05:33:10] Successfully built abc123def456
[05:33:10] Pushing to ECR...
[05:33:18] latest: digest: sha256:abc123... size: 1234
[05:33:18] [Pipeline] stage (Deploy to Staging)
[05:33:18] Deploying my-backend-api:1.0.42 to staging...
[05:33:25] deployment "my-backend-api" successfully rolled out
[05:33:25] [Pipeline] stage (Deploy to Production)
[05:33:25] Deploy my-backend-api:1.0.42 to production?
           [Deploy] [Abort]
           ⏸️  Waiting for input...
[05:45:00] Approved by: admin
[05:45:00] Deploying to production...
[05:45:15] deployment "my-backend-api" successfully rolled out
[05:45:15] [Pipeline] End of Pipeline
Finished: SUCCESS
```

### How Stages Connect

```
Each stage can:
├── Use a DIFFERENT agent (label)
├── Access artifacts from previous stages (archiveArtifacts + copyArtifacts)
├── Use stash/unstash to pass files between agents
├── Run in parallel (parallel block inside a stage)
├── Have its own post block (cleanup, notifications)
├── Have its own timeout and retry options
└── Be skipped with when conditions
```

### Passing Artifacts Between Stages on Different Agents

When stages run on different agents, files don't persist. Use `stash`/`unstash`:

```groovy
pipeline {
    agent none
    stages {
        stage('Build') {
            agent { label 'build-server' }
            steps {
                sh 'mvn clean package -DskipTests'
                // Stash the JAR file — saves it on the Jenkins master
                stash includes: 'target/*.jar', name: 'build-artifact'
            }
        }
        stage('Deploy') {
            agent { label 'deploy-server' }    // Different machine!
            steps {
                // Unstash — downloads the JAR from Jenkins master
                unstash 'build-artifact'
                sh 'ls target/*.jar'           // File is now available here
                sh 'cp target/*.jar /opt/app/'
                sh 'systemctl restart myapp'
            }
        }
    }
}
```

```
Build Agent                Jenkins Master              Deploy Agent
┌──────────┐              ┌──────────────┐             ┌──────────┐
│ mvn build │──stash──────▶│ Stores JAR   │──unstash───▶│ Gets JAR │
│ target/   │              │ temporarily  │             │ deploys  │
│  app.jar  │              │              │             │ to /opt/ │
└──────────┘              └──────────────┘             └──────────┘
```
