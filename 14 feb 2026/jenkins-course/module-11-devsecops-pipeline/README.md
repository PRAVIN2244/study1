# Module 11 — DevSecOps Pipeline

## Overview

A DevSecOps pipeline integrates security checks at every stage of the CI/CD process, shifting security left.

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Checkout │─▶│  Build   │─▶│Code Cov. │─▶│   SCA    │─▶│  SAST    │─▶│  DAST    │
│          │  │          │  │ (Jacoco) │  │ (OWASP)  │  │(Sonar)   │  │(OWASP ZAP│
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                                            │
                                                                            ▼
                                                                     ┌──────────┐
                                                                     │  Deploy  │
                                                                     └──────────┘
```

## Security Testing Types

### Code Coverage — Jacoco

Code coverage measures how much of your source code is exercised by tests.

**Purpose:**
- Find out whether more test cases are needed
- Identify dead code that is unused
- Measure test effectiveness

```xml
<!-- Add Jacoco plugin to pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>org.jacoco</groupId>
            <artifactId>jacoco-maven-plugin</artifactId>
            <version>0.8.11</version>
            <executions>
                <execution>
                    <goals>
                        <goal>prepare-agent</goal>
                    </goals>
                </execution>
                <execution>
                    <id>report</id>
                    <phase>test</phase>
                    <goals>
                        <goal>report</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
    </plugins>
</build>
```

```groovy
// Pipeline stage for code coverage
stage('Code Coverage') {
    agent { label 'demo' }
    steps {
        sh 'mvn test'
        jacoco(
            execPattern: '**/target/jacoco.exec',
            classPattern: '**/target/classes',
            sourcePattern: '**/src/main/java',
            exclusionPattern: '**/test/**'
        )
    }
}
```

### SCA — Static Code Analysis (OWASP Dependency Check)

SCA scans third-party dependencies for known vulnerabilities.

**What it detects:**
- Vulnerable third-party libraries
- Outdated dependencies with known CVEs
- Coding standard violations

⚠️ **Note:** SCA tools can produce false positives and false negatives. Always review results.

```xml
<!-- Add OWASP Dependency Check to pom.xml -->
<build>
    <plugins>
        <plugin>
            <groupId>org.owasp</groupId>
            <artifactId>dependency-check-maven</artifactId>
            <version>9.0.7</version>
            <configuration>
                <format>ALL</format>
                <outputDirectory>${project.build.directory}/dependency-check</outputDirectory>
            </configuration>
        </plugin>
    </plugins>
</build>

<!-- Add properties for report location -->
<properties>
    <sonar.dependencyCheck.reportPath>
        ${project.build.directory}/dependency-check/dependency-check-report.json
    </sonar.dependencyCheck.reportPath>
    <sonar.dependencyCheck.htmlReportPath>
        ${project.build.directory}/dependency-check/dependency-check-report.html
    </sonar.dependencyCheck.htmlReportPath>
</properties>
```

```groovy
// Pipeline stage for OWASP Dependency Check
stage('SCA - Dependency Check') {
    agent { label 'demo' }
    steps {
        sh 'mvn org.owasp:dependency-check-maven:check'
    }
    post {
        always {
            dependencyCheckPublisher pattern: 'target/dependency-check/dependency-check-report.xml'
        }
    }
}
```

### SAST — Static Application Security Testing (SonarQube)

SAST analyzes source code **without executing it**. It reads the source files and looks for patterns that indicate vulnerabilities.

**What it detects:**
- Memory leaks
- Endless loops
- Falling into unknown states
- Unhandled errors and exceptions
- SQL injection patterns
- Cross-site scripting (XSS) vulnerabilities
- Security misconfigurations

**SonarQube setup:**
```bash
# Run SonarQube (requires at least 4 GB RAM)
docker run -d --name sonarqube -p 9000:9000 sonarqube
```

**Access:** `http://<server>:9000`
**Default credentials:** `admin` / `admin` (you'll be prompted to change on first login)

**SonarQube Dependency-Check plugin setup:**
1. Go to SonarQube → Administration → Marketplace
2. Click "I understand the risk"
3. Search for "Dependency-Check" and install
4. Restart SonarQube

**Enable webhook for Quality Gate results:**
1. SonarQube → Administration → Webhooks → Create
2. Name: `Jenkins`
3. URL: `http://<jenkins-url>:8080/sonarqube-webhook/`

This webhook allows Jenkins to receive pass/fail results from SonarQube's Quality Gate.

```groovy
// Pipeline stage for SonarQube analysis
stage('SAST - SonarQube') {
    agent { label 'demo' }
    steps {
        withSonarQubeEnv('sonarqube') {
            sh '''
                mvn sonar:sonar \
                  -Dsonar.projectKey=my-app \
                  -Dsonar.host.url=http://sonarqube:9000 \
                  -Dsonar.login=$SONAR_TOKEN
            '''
        }
    }
}
```

**Expected console output:**
```
[INFO] --- sonar-maven-plugin:3.9.1:sonar ---
[INFO] User cache: /home/jenkins/.sonar/cache
[INFO] SonarQube version: 10.x
[INFO] Analysis report generated in 145ms
[INFO] Analysis report compressed in 89ms
[INFO] Analysis report uploaded in 234ms
[INFO] ANALYSIS SUCCESSFUL, you can find the results at:
[INFO] http://sonarqube:9000/dashboard?id=my-app
[INFO] BUILD SUCCESS
```

```groovy
// Quality Gate check — fails the build if quality gate fails
stage('Quality Gate') {
    agent { label 'demo' }
    steps {
        timeout(time: 5, unit: 'MINUTES') {
            waitForQualityGate abortPipeline: true
        }
    }
}
```

**Expected output (pass):**
```
SonarQube task 'AYx...' status is 'SUCCESS'
SonarQube Quality Gate status: OK
```

**Expected output (fail):**
```
SonarQube Quality Gate status: ERROR
Pipeline aborted due to quality gate failure
Finished: FAILURE
```

### DAST — Dynamic Application Security Testing (OWASP ZAP)

DAST tests a running application for vulnerabilities by sending requests and analyzing responses.

```groovy
// Pipeline stage for OWASP ZAP
stage('DAST - OWASP ZAP') {
    agent { label 'demo' }
    steps {
        sh '''
            docker run --rm \
              -v $(pwd)/zap-report:/zap/wrk:rw \
              ghcr.io/zaproxy/zaproxy:stable \
              zap-baseline.py \
              -t http://staging.example.com \
              -r zap-report.html \
              -l WARN
        '''
    }
    post {
        always {
            publishHTML([
                reportDir: 'zap-report',
                reportFiles: 'zap-report.html',
                reportName: 'OWASP ZAP Report'
            ])
        }
    }
}
```

## IaC Security Scanning

### Checkov (Infrastructure as Code Scanner)

Scans Terraform, CloudFormation, Kubernetes, and Dockerfile for misconfigurations.

```bash
# Install Checkov via Ansible
# install_checkov.yml
---
- hosts: "{{ server }}"
  become: yes
  tasks:
    - name: Install pip
      apt:
        name: python3-pip
        state: present

    - name: Install Checkov
      pip:
        name: checkov
        state: latest
```

```bash
# Test Ansible connectivity first
ansible demo -i hosts -m ping
```

**Expected output:**
```
demo | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

```bash
# Run Checkov setup via Ansible
ansible-playbook install_checkov.yml -i hosts -e "server=terraform"
```

**Expected output:**
```
PLAY [terraform] *****
TASK [Install pip] *****
ok: [terraform]
TASK [Install Checkov] *****
changed: [terraform]
PLAY RECAP *****
terraform : ok=2  changed=1  failed=0
```

```groovy
// Pipeline stage for IaC scanning
stage('IaC Security Scan') {
    agent { label 'demo' }
    steps {
        sh '''
            checkov -d . \
              --output junitxml \
              --output-file checkov-report.xml \
              --soft-fail
        '''
    }
    post {
        always {
            junit 'checkov-report.xml'
        }
    }
}
```

## Spring Boot Build Pipeline (Complete Example)

A real-world pipeline for building a Spring Boot application with artifact storage. Each stage explained line by line.

```groovy
pipeline {
    agent none                        // No default agent — each stage specifies its own
    stages {
        stage('Checkout') {
            agent { label 'demo' }    // Run on agent labeled 'demo'
            steps {
                git branch: 'newfeature',           // Clone this branch
                    credentialsId: 'GitlabCred',    // Use stored GitLab credentials
                    url: 'https://gitlab.com/myorg/backend/springboot.git'
            }
        }

        stage('Build') {
            agent { label 'demo' }
            steps {
                echo "Building Spring Boot Jar ..."
                sh "mvn clean package -Dmaven.test.skip=true"
                // mvn clean    → removes previous build output (target/)
                // mvn package  → compiles code and creates JAR file
                // -Dmaven.test.skip=true → skips running tests (faster build)

                sh "cp target/myapp-springboot.jar target/backend_fb${BUILD_ID}.jar"
                // Renames JAR with build number for traceability
                // BUILD_ID is a Jenkins built-in variable (e.g., 42)
                // Result: target/backend_fb42.jar
            }
        }

        stage('Store Artifacts') {
            agent { label 'demo' }
            steps {
                script {
                    // Connect to Artifactory server configured in Jenkins
                    def server = Artifactory.server 'wezvatechjfrog'

                    // Define what to upload and where
                    def uploadSpec = """{
                        "files": [{
                            "pattern": "target/backend_fb${BUILD_ID}.jar",
                            "target": "wezvatech_backend"
                        }]
                    }"""

                    // Upload the JAR to Artifactory repository
                    server.upload(uploadSpec)
                }
            }
        }
    }
}
```

**Expected console output — Checkout stage:**
```
Cloning repository https://gitlab.com/myorg/backend/springboot.git
 > git fetch --no-tags +refs/heads/newfeature
 > git checkout -b newfeature
```

**Expected console output — Build stage:**
```
Building Spring Boot Jar ...
[INFO] --- maven-clean-plugin:3.2.0:clean ---
[INFO] Deleting /home/jenkins/workspace/my-job/target
[INFO] --- maven-compiler-plugin:3.11.0:compile ---
[INFO] Compiling 45 source files to target/classes
[INFO] --- maven-jar-plugin:3.3.0:jar ---
[INFO] Building jar: target/myapp-springboot.jar
[INFO] BUILD SUCCESS
[INFO] Total time: 23.456 s
```

**Expected console output — Store Artifacts stage:**
```
Deploying artifact: target/backend_fb42.jar
Deploying to: http://artifactory:8082/wezvatech_backend/backend_fb42.jar
Upload successful.
```

**Key build command explained:**
```
mvn clean package -Dmaven.test.skip=true

mvn           → Maven build tool
clean         → Delete target/ directory (previous build output)
package       → Compile source → run tests → create JAR/WAR
-Dmaven.test.skip=true → Skip test execution (faster, use in CI when tests run separately)

Output file: target/myapp-springboot.jar
```

## Full DevSecOps Pipeline

Combines all security stages into a single pipeline:

```groovy
pipeline {
    agent none
    environment {
        SONAR_TOKEN = credentials('sonarqube-token')
    }
    stages {
        stage('Checkout') {
            agent { label 'demo' }
            steps {
                git branch: 'main',
                    credentialsId: 'GitlabCred',
                    url: 'https://gitlab.com/myorg/backend/springboot.git'
            }
        }

        stage('Build') {
            agent { label 'demo' }
            steps {
                sh 'mvn clean package -Dmaven.test.skip=true'
            }
        }

        stage('Code Coverage - Jacoco') {
            agent { label 'demo' }
            steps {
                sh 'mvn test'
                jacoco()
            }
        }

        stage('SCA - OWASP Dependency Check') {
            agent { label 'demo' }
            steps {
                sh 'mvn org.owasp:dependency-check-maven:check'
            }
            post {
                always {
                    dependencyCheckPublisher pattern: 'target/dependency-check/dependency-check-report.xml'
                }
            }
        }

        stage('SAST - SonarQube Analysis') {
            agent { label 'demo' }
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh 'mvn sonar:sonar'
                }
            }
        }

        stage('Quality Gate') {
            agent { label 'demo' }
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Store Artifacts') {
            agent { label 'demo' }
            steps {
                script {
                    def server = Artifactory.server 'wezvatechjfrog'
                    def uploadSpec = """{
                        "files": [{
                            "pattern": "target/*.jar",
                            "target": "backend-releases/"
                        }]
                    }"""
                    server.upload(uploadSpec)
                }
            }
        }

        stage('Docker Build & Push to ECR') {
            agent { label 'demo' }
            steps {
                script {
                    docker.withRegistry(
                        'https://303255670930.dkr.ecr.ap-south-1.amazonaws.com',
                        'ecr:ap-south-1:aws-credentials'
                    ) {
                        def image = docker.build("wezvatechbackend:${BUILD_ID}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }

        stage('DAST - OWASP ZAP') {
            agent { label 'demo' }
            steps {
                sh '''
                    docker run --rm \
                      -v $(pwd)/zap-report:/zap/wrk:rw \
                      ghcr.io/zaproxy/zaproxy:stable \
                      zap-baseline.py \
                      -t http://staging.example.com \
                      -r zap-report.html
                '''
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'zap-report',
                        reportFiles: 'zap-report.html',
                        reportName: 'OWASP ZAP Report'
                    ])
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed'
        }
        failure {
            echo 'Pipeline failed — check security reports'
        }
    }
}
```

## AWS ECR Setup

### Create ECR Repository with Terraform

```hcl
provider "aws" {
  region = "ap-south-1"
}

resource "aws_ecr_repository" "backend" {
  name                 = "wezvatechbackend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
    # ECR uses Clair for vulnerability scanning
  }
}
```

### Create Kubernetes Secret for ECR

```bash
# Ensure AWS CLI is configured on the workstation
kubectl create secret docker-registry regcred \
  --docker-server=303255670930.dkr.ecr.ap-south-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password) \
  --namespace=myapp
```

### Install jq (Required for ECR Scripts)

```bash
sudo apt install -y jq
```

### Use ECR Image in Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: myapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      imagePullSecrets:
        - name: regcred
      containers:
        - name: backend
          image: 303255670930.dkr.ecr.ap-south-1.amazonaws.com/wezvatechbackend:latest
          ports:
            - containerPort: 8080
```

## Server Sizing Recommendations

For DevSecOps pipelines with SonarQube, OWASP checks, and Docker builds, use a larger build server:

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Jenkins Master | t2.small (2 vCPU, 2 GB) | t2.medium (2 vCPU, 4 GB) |
| Build Agent (DevSecOps) | t2.medium (2 vCPU, 4 GB) | t2.large (2 vCPU, 8 GB) |
| SonarQube | t2.medium (2 vCPU, 4 GB) | t2.large (2 vCPU, 8 GB) |

### Memory Management on Build Agents

If SonarQube or builds fail due to memory, clear the page cache:

```bash
sync; echo 1 > /proc/sys/vm/drop_caches
sync; echo 2 > /proc/sys/vm/drop_caches
sync; echo 3 > /proc/sys/vm/drop_caches
```

## DevSecOps Pipeline Summary

| Stage | Tool | What It Checks |
|-------|------|----------------|
| **Code Coverage** | Jacoco | Test coverage percentage, dead code |
| **SCA** | OWASP Dependency Check | Vulnerable third-party libraries |
| **SAST** | SonarQube + SonarScanner | Source code vulnerabilities, code smells, bugs |
| **Quality Gate** | SonarQube Quality Gate | Pass/fail based on defined thresholds |
| **Container Scan** | ECR (Clair) / Trivy | OS-level vulnerabilities in Docker images |
| **DAST** | OWASP ZAP | Runtime vulnerabilities in deployed application |
| **IaC Scan** | Checkov | Terraform/K8s misconfigurations |

---

## Pipeline Failure Conditions for Security Tools

In a DevSecOps pipeline, you don't just run security scans — you **fail the build** when thresholds are exceeded. This section shows how to configure each tool to break the pipeline.

### SonarQube Quality Gate Failure

The SonarQube Quality Gate is a set of conditions (e.g., "no new bugs", "coverage > 80%"). If any condition fails, the pipeline should stop.

**How it works:**

```
Jenkins runs SonarScanner → uploads results to SonarQube server
  │
  ▼
Jenkins calls: GET /api/qualitygates/project_status?projectKey=myapp
  │
  ▼
SonarQube responds: { "projectStatus": { "status": "ERROR" } }
  │
  ▼
Jenkins pipeline: waitForQualityGate() returns FAILURE → pipeline stops
```

**Pipeline implementation:**

```groovy
stage('SonarQube Analysis') {
    steps {
        withSonarQubeEnv('SonarQube-Server') {
            sh '''
                mvn sonar:sonar \
                  -Dsonar.projectKey=myapp \
                  -Dsonar.projectName=myapp
            '''
        }
    }
}

stage('Quality Gate') {
    steps {
        // This step pauses the pipeline and polls SonarQube
        // until the analysis is complete, then checks the gate
        timeout(time: 5, unit: 'MINUTES') {
            waitForQualityGate abortPipeline: true
            //                 ^^^^^^^^^^^^^^^^^^^^
            //  abortPipeline: true → if quality gate fails, pipeline STOPS
            //  abortPipeline: false → logs warning but continues
        }
    }
}
```

```
# Console output when quality gate PASSES:
# [Pipeline] waitForQualityGate
# Checking status of SonarQube task '...' on server 'SonarQube-Server'
# SonarQube task '...' status is 'SUCCESS'
# SonarQube task '...' completed. Quality gate is 'OK'

# Console output when quality gate FAILS:
# [Pipeline] waitForQualityGate
# Checking status of SonarQube task '...' on server 'SonarQube-Server'
# SonarQube task '...' status is 'SUCCESS'
# SonarQube task '...' completed. Quality gate is 'ERROR'
# Pipeline aborted due to quality gate failure: ERROR
```

**Setting up the Quality Gate in SonarQube:**

1. Go to SonarQube → **Quality Gates** → **Create**
2. Add conditions:

| Metric | Operator | Value |
|--------|----------|-------|
| New Bugs | is greater than | 0 |
| New Vulnerabilities | is greater than | 0 |
| New Code Coverage | is less than | 80% |
| New Duplicated Lines (%) | is greater than | 3% |
| Security Hotspots Reviewed | is less than | 100% |

3. Set as **Default** quality gate

**Webhook requirement:** SonarQube must call Jenkins back when analysis is done:
- SonarQube → **Administration → Configuration → Webhooks → Create**
- URL: `http://<JENKINS-URL>/sonarqube-webhook/`

### OWASP Dependency-Check Threshold

OWASP Dependency-Check scans your project's dependencies for known CVEs. You configure thresholds to fail the build based on vulnerability severity.

**How it works:**

```
Dependency-Check scans pom.xml / package.json / requirements.txt
  │
  ▼
Finds vulnerabilities and assigns CVSS scores:
  CRITICAL (9.0-10.0), HIGH (7.0-8.9), MEDIUM (4.0-6.9), LOW (0.1-3.9)
  │
  ▼
Jenkins plugin checks: "Are there more vulnerabilities than the threshold?"
  │
  ▼
If CRITICAL > 0 → pipeline FAILS
```

**Pipeline implementation:**

```groovy
stage('OWASP Dependency Check') {
    steps {
        dependencyCheck additionalArguments: '''
            --scan .
            --format HTML
            --format XML
            --out dependency-check-report
            --prettyPrint
        ''', odcInstallation: 'OWASP-DC'

        dependencyCheckPublisher pattern: 'dependency-check-report/dependency-check-report.xml',
            failedTotalCritical: 1,    // Fail if >= 1 CRITICAL vulnerability
            failedTotalHigh: 5,        // Fail if >= 5 HIGH vulnerabilities
            failedTotalMedium: 10,     // Fail if >= 10 MEDIUM vulnerabilities
            failedTotalLow: 20,        // Fail if >= 20 LOW vulnerabilities
            unstableTotalCritical: 0,  // Mark UNSTABLE if any CRITICAL found
            unstableTotalHigh: 2,      // Mark UNSTABLE if >= 2 HIGH found
            unstableTotalMedium: 5
    }
}
```

```
# Console output when thresholds PASS:
# [DependencyCheck] Parsing dependency-check-report.xml
# [DependencyCheck] Found 2 vulnerabilities (0 critical, 1 high, 1 medium, 0 low)
# [DependencyCheck] Thresholds: critical < 1 ✓, high < 5 ✓, medium < 10 ✓
# Finished: SUCCESS

# Console output when thresholds FAIL:
# [DependencyCheck] Parsing dependency-check-report.xml
# [DependencyCheck] Found 8 vulnerabilities (2 critical, 3 high, 2 medium, 1 low)
# [DependencyCheck] FAILURE: Total critical vulnerabilities (2) >= threshold (1)
# Finished: FAILURE
```

**Threshold explanation:**

| Parameter | Meaning | Recommended |
|-----------|---------|-------------|
| `failedTotalCritical: 1` | Build FAILS if 1+ critical CVEs found | 1 (zero tolerance) |
| `failedTotalHigh: 5` | Build FAILS if 5+ high CVEs found | 3-5 |
| `unstableTotalCritical: 0` | Build marked UNSTABLE (yellow) if any critical | 0 |
| `unstableTotalHigh: 2` | Build marked UNSTABLE if 2+ high | 1-2 |

> **UNSTABLE vs FAILURE:** UNSTABLE (yellow ball) means "warning, review needed." FAILURE (red ball) means "build is broken, cannot proceed."

### Trivy — Container Image Scanning

Trivy scans Docker images for OS and application vulnerabilities. It uses exit codes to signal severity.

**How it works:**

```
Trivy scans Docker image layers
  │
  ▼
Checks each package against vulnerability databases (NVD, GitHub Advisory, etc.)
  │
  ▼
Exit code determines pipeline result:
  exit 0 → no vulnerabilities above threshold → pipeline continues
  exit 1 → vulnerabilities found above threshold → pipeline FAILS
```

**Pipeline implementation:**

```groovy
stage('Build Docker Image') {
    steps {
        sh 'docker build -t myapp:${BUILD_NUMBER} .'
    }
}

stage('Trivy Image Scan') {
    steps {
        // Fail if any CRITICAL or HIGH vulnerabilities found
        sh '''
            trivy image \
              --exit-code 1 \
              --severity CRITICAL,HIGH \
              --no-progress \
              --format table \
              myapp:${BUILD_NUMBER}
        '''
    }
}
```

```
# Console output when scan PASSES:
# 2024-01-15T10:30:00.000Z  INFO  Vulnerability scanning is enabled
# 2024-01-15T10:30:05.000Z  INFO  Detected OS: ubuntu 22.04
# 2024-01-15T10:30:05.000Z  INFO  Number of language-specific files: 1
#
# myapp:42 (ubuntu 22.04)
# Total: 0 (CRITICAL: 0, HIGH: 0)
#
# + exit 0

# Console output when scan FAILS:
# myapp:42 (ubuntu 22.04)
# ┌──────────────┬────────────────┬──────────┬───────────────────┬──────────────┐
# │   Library    │ Vulnerability  │ Severity │ Installed Version │ Fixed Version│
# ├──────────────┼────────────────┼──────────┼───────────────────┼──────────────┤
# │ libssl3      │ CVE-2024-XXXXX │ CRITICAL │ 3.0.2-0ubuntu1.6  │ 3.0.2-0ubu.. │
# │ curl         │ CVE-2024-YYYYY │ HIGH     │ 7.81.0-1ubuntu1.7 │ 7.81.0-1ub.. │
# └──────────────┴────────────────┴──────────┴───────────────────┴──────────────┘
# Total: 2 (CRITICAL: 1, HIGH: 1)
#
# + exit 1
# Finished: FAILURE
```

**Trivy exit code options:**

| Flag | Value | Meaning |
|------|-------|---------|
| `--exit-code 0` | 0 | Always pass (scan only, don't fail) |
| `--exit-code 1` | 1 | Fail if vulnerabilities matching `--severity` are found |
| `--severity CRITICAL` | | Only fail on CRITICAL |
| `--severity CRITICAL,HIGH` | | Fail on CRITICAL or HIGH |
| `--severity CRITICAL,HIGH,MEDIUM` | | Fail on CRITICAL, HIGH, or MEDIUM |

**Advanced: Trivy with JSON report and threshold logic:**

```groovy
stage('Trivy Scan with Report') {
    steps {
        // Generate JSON report
        sh '''
            trivy image \
              --format json \
              --output trivy-report.json \
              --severity CRITICAL,HIGH,MEDIUM \
              myapp:${BUILD_NUMBER}
        '''

        // Parse and enforce custom thresholds
        script {
            def report = readJSON file: 'trivy-report.json'
            def critical = 0
            def high = 0

            report.Results.each { result ->
                result.Vulnerabilities?.each { vuln ->
                    if (vuln.Severity == 'CRITICAL') critical++
                    if (vuln.Severity == 'HIGH') high++
                }
            }

            echo "Trivy results: ${critical} CRITICAL, ${high} HIGH"

            if (critical > 0) {
                error "Pipeline failed: ${critical} CRITICAL vulnerabilities found"
            }
            if (high > 3) {
                error "Pipeline failed: ${high} HIGH vulnerabilities (threshold: 3)"
            }
            if (high > 0) {
                unstable "Warning: ${high} HIGH vulnerabilities found"
            }
        }
    }
}
```

### Checkov — IaC Scan Failure

```groovy
stage('IaC Security Scan') {
    steps {
        // Checkov exits with code 1 if any check fails
        sh '''
            checkov \
              -d . \
              --framework terraform \
              --output cli \
              --compact \
              --hard-fail-on CRITICAL,HIGH
        '''
        //  --hard-fail-on CRITICAL,HIGH → exit 1 only for CRITICAL/HIGH findings
        //  Without this flag, ANY failed check causes exit 1
    }
}
```

```
# Console output when checks FAIL:
# Passed checks: 15, Failed checks: 2, Skipped checks: 0
#
# Check: CKV_AWS_18: "Ensure the S3 bucket has access logging enabled"
#   FAILED for resource: aws_s3_bucket.data
#   File: /main.tf:25-30
#
# Check: CKV_AWS_145: "Ensure S3 bucket is encrypted with KMS"
#   FAILED for resource: aws_s3_bucket.data
#   File: /main.tf:25-30
#
# + exit 1
# Finished: FAILURE
```

### OWASP ZAP — DAST Failure

```groovy
stage('DAST - OWASP ZAP') {
    steps {
        sh '''
            docker run --rm \
              -v $(pwd)/zap-report:/zap/wrk:rw \
              ghcr.io/zaproxy/zaproxy:stable \
              zap-baseline.py \
                -t http://staging-app:8080 \
                -r zap-report.html \
                -c zap-rules.conf \
                -l WARN
        '''
        //  -l WARN → fail on WARN level and above
        //  -l FAIL → only fail on FAIL level (more lenient)
        //  Exit codes: 0 = pass, 1 = WARN alerts, 2 = FAIL alerts, 3 = error
    }
}
```

**ZAP rules configuration file (`zap-rules.conf`):**

```
# Rule ID    Action     (IGNORE, WARN, FAIL)
10010        WARN       # Cookie No HttpOnly Flag
10011        FAIL       # Cookie Without Secure Flag
10015        FAIL       # Incomplete or No Cache-control
10020        IGNORE     # X-Frame-Options Header Not Set (handled by CSP)
10021        FAIL       # X-Content-Type-Options Header Missing
40012        FAIL       # Cross Site Scripting (Reflected)
40014        FAIL       # Cross Site Scripting (Persistent)
90001        FAIL       # Insecure JSF ViewState
```

### Summary — Failure Conditions at a Glance

| Tool | What Fails the Build | How to Configure |
|------|---------------------|------------------|
| **SonarQube** | Quality Gate status = ERROR | `waitForQualityGate abortPipeline: true` |
| **OWASP DC** | Vulnerability count exceeds threshold | `failedTotalCritical: 1, failedTotalHigh: 5` |
| **Trivy** | Vulnerabilities found at specified severity | `--exit-code 1 --severity CRITICAL,HIGH` |
| **Checkov** | IaC misconfigurations at specified severity | `--hard-fail-on CRITICAL,HIGH` |
| **OWASP ZAP** | Alerts at WARN or FAIL level | `-l WARN` or custom rules in `.conf` file |
| **Jacoco** | Coverage below minimum | Maven plugin `<minimum>0.80</minimum>` |

### Jacoco — Coverage Threshold

```xml
<!-- In pom.xml -->
<execution>
    <id>check</id>
    <goals><goal>check</goal></goals>
    <configuration>
        <rules>
            <rule>
                <element>BUNDLE</element>
                <limits>
                    <limit>
                        <counter>LINE</counter>
                        <value>COVEREDRATIO</value>
                        <minimum>0.80</minimum>  <!-- Fail if < 80% line coverage -->
                    </limit>
                    <limit>
                        <counter>BRANCH</counter>
                        <value>COVEREDRATIO</value>
                        <minimum>0.70</minimum>  <!-- Fail if < 70% branch coverage -->
                    </limit>
                </limits>
            </rule>
        </rules>
    </configuration>
</execution>
```

```
# Console output when coverage FAILS:
# [ERROR] Failed to execute goal org.jacoco:jacoco-maven-plugin:check
# [ERROR] Rule violated for bundle myapp:
# [ERROR]   lines covered ratio is 0.65, but expected minimum is 0.80
# Finished: FAILURE
```
