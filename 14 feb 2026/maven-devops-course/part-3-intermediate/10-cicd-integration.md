# Module 10: Maven in CI/CD Pipelines

**Objective:** Understand how companies use Maven in CI/CD pipelines and implement real pipelines with Jenkins, GitLab CI, and GitHub Actions.

---

## 10.1 How Companies Use Maven in CI/CD

This is the standard workflow in almost every enterprise Java shop:

```
Developer          Git              CI Server          Artifact Repo       Production
  commit    ──►   Repository  ──►   (Jenkins)    ──►   (Nexus/JFrog)  ──►  Server
                                       │
                                       ▼
                                 mvn clean package
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  Build Steps:    │
                              │  1. Compile code │
                              │  2. Run tests    │
                              │  3. Package JAR  │
                              │  4. Upload to    │
                              │     Nexus        │
                              └─────────────────┘
```

### Step-by-Step — What Happens When a Developer Pushes Code

```
Step 1: Developer commits code
────────────────────────────
  git add .
  git commit -m "Add payment validation"
  git push origin main

Step 2: CI server detects the push
──────────────────────────────────
  Jenkins/GitLab CI has a webhook on the Git repository
  It automatically triggers a build job

Step 3: CI server runs Maven
────────────────────────────
  mvn clean install
  Result:
    ✓ Code compiled (150 .java → 150 .class)
    ✓ Tests run (300 tests passed)
    ✓ Artifact created (payment-service-2.1.jar)
    ✓ Artifact stored in local repo (~/.m2)

Step 4: Artifact uploaded to repository
───────────────────────────────────────
  mvn deploy
  payment-service-2.1.jar → uploaded to Nexus/Artifactory
  Now available for deployment

Step 5: Deployment
──────────────────
  Operations pulls payment-service-2.1.jar from Nexus
  Deploys to production server (or Docker container)
  Customers can use the new features
```

**This is standard in almost every enterprise.** The tools may differ (Jenkins vs GitLab CI vs GitHub Actions), but the flow is the same.

---

## 10.2 Jenkins Pipeline with Maven

**`Jenkinsfile`:**

```groovy
pipeline {
    agent {
        docker {
            image 'maven:3.9.6-eclipse-temurin-17'
            args '-v $HOME/.m2:/root/.m2'  // Cache dependencies
        }
    }

    environment {
        NEXUS_CREDS = credentials('nexus-deployer')
    }

    stages {
        stage('Compile') {
            steps {
                sh 'mvn clean compile'
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit 'target/surefire-reports/*.xml'
                    jacoco execPattern: 'target/jacoco.exec'
                }
            }
        }

        stage('Code Quality') {
            steps {
                sh 'mvn sonar:sonar -Dsonar.host.url=http://sonarqube:9000'
            }
        }

        stage('Package') {
            steps {
                sh 'mvn package -DskipTests'
            }
        }

        stage('Deploy to Nexus') {
            when {
                branch 'main'
            }
            steps {
                sh 'mvn deploy -DskipTests'
            }
        }

        stage('Build Docker Image') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    docker build -t myapp:${env.BUILD_NUMBER} .
                    docker push myregistry.com/myapp:${env.BUILD_NUMBER}
                """
            }
        }
    }

    post {
        failure {
            mail to: 'devops@company.com',
                 subject: "Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Check: ${env.BUILD_URL}"
        }
    }
}
```

---

## 10.3 GitLab CI with Maven

**`.gitlab-ci.yml`:**

```yaml
image: maven:3.9.6-eclipse-temurin-17

variables:
  MAVEN_OPTS: "-Dmaven.repo.local=$CI_PROJECT_DIR/.m2/repository"

cache:
  paths:
    - .m2/repository/

stages:
  - build
  - test
  - quality
  - package
  - deploy

compile:
  stage: build
  script:
    - mvn clean compile

unit-test:
  stage: test
  script:
    - mvn test
  artifacts:
    when: always
    reports:
      junit: target/surefire-reports/TEST-*.xml
    paths:
      - target/site/jacoco/

sonarqube:
  stage: quality
  script:
    - mvn sonar:sonar -Dsonar.host.url=$SONAR_URL -Dsonar.token=$SONAR_TOKEN
  only:
    - main
    - merge_requests

package:
  stage: package
  script:
    - mvn package -DskipTests
  artifacts:
    paths:
      - target/*.jar

deploy-nexus:
  stage: deploy
  script:
    - mvn deploy -DskipTests -s ci-settings.xml
  only:
    - main
```

---

## 10.4 GitHub Actions with Maven

**`.github/workflows/maven.yml`:**

```yaml
name: Maven CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: maven

      - name: Build
        run: mvn clean compile

      - name: Test
        run: mvn test

      - name: Package
        run: mvn package -DskipTests

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: app-jar
          path: target/*.jar

      - name: Deploy to Nexus
        if: github.ref == 'refs/heads/main'
        run: mvn deploy -DskipTests -s $GITHUB_WORKSPACE/.github/settings.xml
        env:
          NEXUS_USERNAME: ${{ secrets.NEXUS_USERNAME }}
          NEXUS_PASSWORD: ${{ secrets.NEXUS_PASSWORD }}
```

---

## 10.5 Optimizing Maven Builds in CI

```bash
# 1. Use dependency caching (shown above in each CI tool)

# 2. Run Maven in batch mode (no progress bar, cleaner logs)
mvn -B clean package

# 3. Run in offline mode if dependencies are cached
mvn -o clean package

# 4. Parallel builds (use available CPU cores)
mvn -T 1C clean package    # 1 thread per CPU core
mvn -T 4 clean package     # 4 threads

# 5. Only build changed modules
mvn -pl changed-module -am clean package

# 6. Fail fast on first error (in multi-module)
mvn --fail-fast clean package

# 7. Reduce memory usage
export MAVEN_OPTS="-Xmx512m -XX:MaxMetaspaceSize=256m"
```

---

## 10.6 Hands-On Exercise

```bash
# 1. Create a GitHub repository with your Maven project
# 2. Add the GitHub Actions workflow above
# 3. Push code and watch the pipeline run
# 4. Intentionally break a test — observe the pipeline fail
# 5. Fix the test — observe the pipeline pass
# 6. Add JaCoCo and publish coverage as a pipeline artifact
```

---

**Next:** [Module 11 — Advanced Maven for DevOps](../part-4-advanced/11-advanced-topics.md)
