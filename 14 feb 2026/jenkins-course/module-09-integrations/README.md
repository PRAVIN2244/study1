# Module 09 — Integrations

## Git Integration

### Webhook Setup (GitHub)

```
GitHub Repository → Settings → Webhooks → Add webhook

Payload URL: https://jenkins.example.com/github-webhook/
Content type: application/json
Secret: (optional, for verification)
Events: Push, Pull Request
```

### Webhook Setup (GitLab)

```
GitLab Project → Settings → Webhooks

URL: https://jenkins.example.com/project/job-name
Secret token: (from Jenkins GitLab trigger config)
Trigger: Push events, Merge request events
```

### Git in Pipelines

```groovy
pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                // Automatic checkout (default behavior)
                checkout scm

                // Or explicit checkout
                git branch: 'main',
                    credentialsId: 'github-token',
                    url: 'https://github.com/org/repo.git'

                // Advanced checkout
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [
                        [$class: 'CloneOption', depth: 1, shallow: true],
                        [$class: 'CleanBeforeCheckout']
                    ],
                    userRemoteConfigs: [[
                        url: 'https://github.com/org/repo.git',
                        credentialsId: 'github-token'
                    ]]
                ])
            }
        }
    }
}
```

### GitHub Status Checks

```groovy
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                // GitHub plugin sets status automatically for multibranch pipelines
                sh 'mvn package'
            }
        }
    }
    post {
        success {
            // Manual status update
            githubNotify status: 'SUCCESS',
                         description: 'Build passed',
                         context: 'ci/jenkins/build'
        }
        failure {
            githubNotify status: 'FAILURE',
                         description: 'Build failed',
                         context: 'ci/jenkins/build'
        }
    }
}
```

## Docker Integration

### Docker in Pipelines

```groovy
pipeline {
    agent any
    environment {
        REGISTRY = 'docker.io'
        IMAGE = 'myorg/myapp'
        TAG = "${BUILD_NUMBER}"
    }
    stages {
        stage('Build Image') {
            steps {
                script {
                    docker.build("${IMAGE}:${TAG}")
                }
            }
        }
        stage('Test Image') {
            steps {
                script {
                    docker.image("${IMAGE}:${TAG}").inside {
                        sh 'run-tests.sh'
                    }
                }
            }
        }
        stage('Push Image') {
            steps {
                script {
                    docker.withRegistry("https://${REGISTRY}", 'docker-hub-creds') {
                        docker.image("${IMAGE}:${TAG}").push()
                        docker.image("${IMAGE}:${TAG}").push('latest')
                    }
                }
            }
        }
    }
}
```

### Docker as Build Agent

```groovy
pipeline {
    agent {
        docker {
            image 'node:20-alpine'
            args '-v /tmp:/tmp'
        }
    }
    stages {
        stage('Install') {
            steps {
                sh 'npm ci'
            }
        }
        stage('Test') {
            steps {
                sh 'npm test'
            }
        }
        stage('Build') {
            steps {
                sh 'npm run build'
            }
        }
    }
}
```

### Docker Compose in Pipeline

```groovy
stage('Integration Tests') {
    steps {
        sh 'docker compose -f docker-compose.test.yml up -d'
        sh 'sleep 10'  // Wait for services
        sh 'npm run test:integration'
    }
    post {
        always {
            sh 'docker compose -f docker-compose.test.yml down -v'
        }
    }
}
```

## Kubernetes Integration

### Deploy to Kubernetes

```groovy
pipeline {
    agent { label 'k8s' }
    environment {
        KUBECONFIG = credentials('kubeconfig-prod')
    }
    stages {
        stage('Deploy') {
            steps {
                sh '''
                    kubectl set image deployment/myapp \
                      myapp=myorg/myapp:${BUILD_NUMBER} \
                      --namespace=production

                    kubectl rollout status deployment/myapp \
                      --namespace=production \
                      --timeout=300s
                '''
            }
        }
        stage('Verify') {
            steps {
                sh '''
                    kubectl get pods -n production -l app=myapp
                    kubectl get svc -n production -l app=myapp
                '''
            }
        }
    }
    post {
        failure {
            sh 'kubectl rollout undo deployment/myapp --namespace=production'
        }
    }
}
```

### Helm Deployments

```groovy
stage('Deploy with Helm') {
    steps {
        sh '''
            helm upgrade --install myapp ./helm/myapp \
              --namespace production \
              --set image.tag=${BUILD_NUMBER} \
              --set replicas=3 \
              --wait \
              --timeout 5m
        '''
    }
}
```

## SonarQube Integration

### Setup

1. Install **SonarQube Scanner** plugin
2. **Manage Jenkins → System → SonarQube servers**
   - Name: `sonarqube`
   - URL: `https://sonar.example.com`
   - Token: (credential ID)

3. **Manage Jenkins → Tools → SonarQube Scanner installations**
   - Name: `SonarScanner`
   - Install automatically: ✓

### Pipeline Usage

```groovy
pipeline {
    agent any
    environment {
        SCANNER_HOME = tool 'SonarScanner'
    }
    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                        ${SCANNER_HOME}/bin/sonar-scanner \
                          -Dsonar.projectKey=my-app \
                          -Dsonar.sources=src/main \
                          -Dsonar.tests=src/test \
                          -Dsonar.java.binaries=target/classes \
                          -Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml
                    '''
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
```

## Artifactory / Nexus Integration

### Artifactory

```groovy
stage('Upload to Artifactory') {
    steps {
        rtUpload(
            serverId: 'artifactory',
            spec: '''{
                "files": [{
                    "pattern": "target/*.jar",
                    "target": "libs-release-local/com/myorg/myapp/${BUILD_NUMBER}/"
                }]
            }'''
        )
    }
}
```

### Nexus

```groovy
stage('Upload to Nexus') {
    steps {
        nexusArtifactUploader(
            nexusVersion: 'nexus3',
            protocol: 'https',
            nexusUrl: 'nexus.example.com',
            groupId: 'com.myorg',
            version: "${BUILD_NUMBER}",
            repository: 'maven-releases',
            credentialsId: 'nexus-creds',
            artifacts: [
                [artifactId: 'myapp',
                 classifier: '',
                 file: 'target/myapp.jar',
                 type: 'jar']
            ]
        )
    }
}
```

## Slack / Email Notifications

### Slack

```groovy
post {
    success {
        slackSend(
            channel: '#deployments',
            color: 'good',
            message: """
                *SUCCESS* :white_check_mark:
                Job: ${env.JOB_NAME} #${env.BUILD_NUMBER}
                Branch: ${env.GIT_BRANCH}
                Commit: ${env.GIT_COMMIT?.take(8)}
                <${env.BUILD_URL}|View Build>
            """.stripIndent()
        )
    }
    failure {
        slackSend(
            channel: '#deployments',
            color: 'danger',
            message: "*FAILED* :x: ${env.JOB_NAME} #${env.BUILD_NUMBER}\n<${env.BUILD_URL}|View Build>"
        )
    }
}
```

### Email

```groovy
post {
    failure {
        emailext(
            subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
            body: '''
                <h2>Build Failed</h2>
                <p>Job: ${JOB_NAME}<br>
                Build: #${BUILD_NUMBER}<br>
                URL: <a href="${BUILD_URL}">${BUILD_URL}</a></p>
                <h3>Changes:</h3>
                ${CHANGES}
                <h3>Console Output (last 100 lines):</h3>
                <pre>${BUILD_LOG, maxLines=100}</pre>
            ''',
            to: '${DEFAULT_RECIPIENTS}',
            mimeType: 'text/html',
            attachLog: true
        )
    }
}
```

## Terraform Integration

```groovy
pipeline {
    agent { label 'terraform' }
    environment {
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
        TF_VAR_environment = "${params.ENVIRONMENT}"
    }
    stages {
        stage('Init') {
            steps {
                dir('terraform') {
                    sh 'terraform init -backend-config=backend.hcl'
                }
            }
        }
        stage('Plan') {
            steps {
                dir('terraform') {
                    sh 'terraform plan -out=tfplan'
                    sh 'terraform show -no-color tfplan > plan.txt'
                }
                archiveArtifacts artifacts: 'terraform/plan.txt'
            }
        }
        stage('Apply') {
            when { branch 'main' }
            steps {
                input message: 'Apply Terraform changes?', ok: 'Apply'
                dir('terraform') {
                    sh 'terraform apply -auto-approve tfplan'
                }
            }
        }
    }
}
```
