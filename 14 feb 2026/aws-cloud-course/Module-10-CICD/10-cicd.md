# Module 10: CI/CD - Continuous Integration & Continuous Deployment

## 10.1 What is CI/CD?

```
┌──────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                             │
│                                                               │
│  Developer                                                    │
│     │                                                         │
│     ▼                                                         │
│  ┌──────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │ Code │──▶│  Build   │──▶│  Test    │──▶│   Deploy      │ │
│  │ Push │   │ Compile  │   │ Unit     │   │ Staging→Prod  │ │
│  │      │   │ Package  │   │ Integr.  │   │               │ │
│  └──────┘   └──────────┘   └──────────┘   └──────────────┘ │
│  CodeCommit  CodeBuild      CodeBuild      CodeDeploy       │
│  (or GitHub)                                                 │
│                                                               │
│  ◄──── Continuous Integration ────►◄── Continuous Delivery ──►│
└──────────────────────────────────────────────────────────────┘
```

### AWS CI/CD Services

| Service | Purpose | Equivalent |
|---------|---------|------------|
| **CodeCommit** | Git repository | GitHub, GitLab |
| **CodeBuild** | Build & test | Jenkins, GitHub Actions |
| **CodeDeploy** | Deploy to EC2/ECS/Lambda | Ansible, Spinnaker |
| **CodePipeline** | Orchestrate the pipeline | Jenkins Pipeline |
| **CodeArtifact** | Package repository | npm registry, Maven Central |

---

## 10.2 CodeCommit (Git Repository)

```bash
# Create repository
aws codecommit create-repository \
  --repository-name myapp \
  --repository-description "Main application repository"
```

**Expected Output:**
```json
{
    "repositoryMetadata": {
        "repositoryName": "myapp",
        "cloneUrlHttp": "https://git-codecommit.us-east-1.amazonaws.com/v1/repos/myapp",
        "cloneUrlSsh": "ssh://git-codecommit.us-east-1.amazonaws.com/v1/repos/myapp"
    }
}
```

```bash
# Clone and push
git clone https://git-codecommit.us-east-1.amazonaws.com/v1/repos/myapp
cd myapp
echo "# My App" > README.md
git add . && git commit -m "Initial commit"
git push origin main
```

---

## 10.3 CodeBuild

CodeBuild compiles code, runs tests, and produces deployable artifacts.

### buildspec.yml

```bash
cat > buildspec.yml << 'EOF'
version: 0.2

env:
  variables:
    NODE_ENV: "production"
  parameter-store:
    DB_PASSWORD: "/myapp/db-password"

phases:
  install:
    runtime-versions:
      nodejs: 20
    commands:
      - echo "Installing dependencies..."
      - npm ci

  pre_build:
    commands:
      - echo "Running linter..."
      - npm run lint
      - echo "Logging into ECR..."
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com

  build:
    commands:
      - echo "Running tests..."
      - npm test
      - echo "Building application..."
      - npm run build
      - echo "Building Docker image..."
      - docker build -t $IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION .
      - docker tag $IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - docker tag $IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest

  post_build:
    commands:
      - echo "Pushing Docker image..."
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest
      - echo "Creating imagedefinitions.json for ECS..."
      - printf '[{"name":"web","imageUri":"%s"}]' $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION > imagedefinitions.json

artifacts:
  files:
    - imagedefinitions.json
    - appspec.yml
    - scripts/**/*

reports:
  test-reports:
    files:
      - 'test-results/*.xml'
    file-format: JUNITXML

cache:
  paths:
    - 'node_modules/**/*'
EOF
```

### Create CodeBuild Project

```bash
cat > codebuild-project.json << 'EOF'
{
    "name": "myapp-build",
    "source": {
        "type": "GITHUB",
        "location": "https://github.com/myorg/myapp.git",
        "buildspec": "buildspec.yml"
    },
    "environment": {
        "type": "LINUX_CONTAINER",
        "image": "aws/codebuild/amazonlinux2-x86_64-standard:5.0",
        "computeType": "BUILD_GENERAL1_SMALL",
        "privilegedMode": true,
        "environmentVariables": [
            {"name": "AWS_ACCOUNT_ID", "value": "123456789012"},
            {"name": "IMAGE_REPO_NAME", "value": "myapp/web"},
            {"name": "AWS_DEFAULT_REGION", "value": "us-east-1"}
        ]
    },
    "artifacts": {
        "type": "S3",
        "location": "myapp-build-artifacts",
        "packaging": "ZIP"
    },
    "serviceRole": "arn:aws:iam::123456789012:role/codebuild-role",
    "cache": {
        "type": "S3",
        "location": "myapp-build-cache"
    }
}
EOF

aws codebuild create-project --cli-input-json file://codebuild-project.json
```

### Start a Build

```bash
aws codebuild start-build --project-name myapp-build
```

### View Build Logs

```bash
# List builds
aws codebuild list-builds-for-project --project-name myapp-build

# Get build details
aws codebuild batch-get-builds --ids myapp-build:build-id \
  --query 'builds[0].{Status:buildStatus,Duration:buildComplete,Phases:phases[*].{Name:phaseType,Status:phaseStatus}}'
```

---

## 10.4 CodeDeploy

CodeDeploy automates deployments to EC2, ECS, or Lambda.

### appspec.yml for EC2

```yaml
version: 0.0
os: linux

files:
  - source: /
    destination: /var/www/myapp

hooks:
  BeforeInstall:
    - location: scripts/before_install.sh
      timeout: 300
      runas: root

  AfterInstall:
    - location: scripts/after_install.sh
      timeout: 300
      runas: root

  ApplicationStart:
    - location: scripts/start_app.sh
      timeout: 300
      runas: root

  ValidateService:
    - location: scripts/validate.sh
      timeout: 300
      runas: root
```

### Deployment Scripts

```bash
# scripts/before_install.sh
#!/bin/bash
yum update -y
yum install -y nodejs npm

# scripts/after_install.sh
#!/bin/bash
cd /var/www/myapp
npm install --production

# scripts/start_app.sh
#!/bin/bash
systemctl restart myapp

# scripts/validate.sh
#!/bin/bash
curl -f http://localhost:3000/health || exit 1
```

### appspec.yml for ECS (Blue/Green)

```yaml
version: 0.0

Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: <TASK_DEFINITION>
        LoadBalancerInfo:
          ContainerName: "web"
          ContainerPort: 8080

Hooks:
  - BeforeInstall: "LambdaFunctionToValidateBeforeInstall"
  - AfterInstall: "LambdaFunctionToValidateAfterInstall"
  - AfterAllowTestTraffic: "LambdaFunctionToRunIntegrationTests"
  - BeforeAllowTraffic: "LambdaFunctionToValidateBeforeTraffic"
  - AfterAllowTraffic: "LambdaFunctionToValidateAfterTraffic"
```

### Create CodeDeploy Application

```bash
# Create application
aws deploy create-application \
  --application-name myapp \
  --compute-platform Server

# Create deployment group
aws deploy create-deployment-group \
  --application-name myapp \
  --deployment-group-name production \
  --service-role-arn arn:aws:iam::123456789012:role/CodeDeployRole \
  --deployment-config-name CodeDeployDefault.OneAtATime \
  --ec2-tag-filters Key=Environment,Value=production,Type=KEY_AND_VALUE \
  --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE
```

### Deployment Strategies

```
┌─────────────────────────────────────────────────────┐
│              Deployment Strategies                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. All-at-Once (fastest, most downtime risk)        │
│     [████████████] → [████████████]                  │
│      Old version      New version                    │
│                                                      │
│  2. Rolling (one at a time)                          │
│     [████████████] → [▓▓██████████] → [▓▓▓▓▓▓▓▓▓▓▓▓]│
│                                                      │
│  3. Blue/Green (zero downtime)                       │
│     Blue: [████████████] (live)                      │
│     Green: [▓▓▓▓▓▓▓▓▓▓▓▓] (new, tested)            │
│     Switch traffic: Blue → Green                     │
│                                                      │
│  4. Canary (gradual traffic shift)                   │
│     [90% old] [10% new] → [0% old] [100% new]       │
└─────────────────────────────────────────────────────┘
```

---

## 10.5 CodePipeline (Full Pipeline)

### Create a Complete Pipeline

```bash
cat > pipeline.json << 'EOF'
{
    "pipeline": {
        "name": "myapp-pipeline",
        "roleArn": "arn:aws:iam::123456789012:role/CodePipelineRole",
        "stages": [
            {
                "name": "Source",
                "actions": [{
                    "name": "GitHub-Source",
                    "actionTypeId": {
                        "category": "Source",
                        "owner": "ThirdParty",
                        "provider": "GitHub",
                        "version": "1"
                    },
                    "configuration": {
                        "Owner": "myorg",
                        "Repo": "myapp",
                        "Branch": "main",
                        "OAuthToken": "{{resolve:secretsmanager:github-token}}"
                    },
                    "outputArtifacts": [{"name": "SourceOutput"}]
                }]
            },
            {
                "name": "Build",
                "actions": [{
                    "name": "CodeBuild",
                    "actionTypeId": {
                        "category": "Build",
                        "owner": "AWS",
                        "provider": "CodeBuild",
                        "version": "1"
                    },
                    "configuration": {
                        "ProjectName": "myapp-build"
                    },
                    "inputArtifacts": [{"name": "SourceOutput"}],
                    "outputArtifacts": [{"name": "BuildOutput"}]
                }]
            },
            {
                "name": "Approval",
                "actions": [{
                    "name": "ManualApproval",
                    "actionTypeId": {
                        "category": "Approval",
                        "owner": "AWS",
                        "provider": "Manual",
                        "version": "1"
                    },
                    "configuration": {
                        "NotificationArn": "arn:aws:sns:us-east-1:123456789012:deploy-approvals",
                        "CustomData": "Please review the build artifacts before deploying to production."
                    }
                }]
            },
            {
                "name": "Deploy",
                "actions": [{
                    "name": "ECS-Deploy",
                    "actionTypeId": {
                        "category": "Deploy",
                        "owner": "AWS",
                        "provider": "ECS",
                        "version": "1"
                    },
                    "configuration": {
                        "ClusterName": "myapp-cluster",
                        "ServiceName": "myapp-web-service",
                        "FileName": "imagedefinitions.json"
                    },
                    "inputArtifacts": [{"name": "BuildOutput"}]
                }]
            }
        ],
        "artifactStore": {
            "type": "S3",
            "location": "myapp-pipeline-artifacts"
        }
    }
}
EOF

aws codepipeline create-pipeline --cli-input-json file://pipeline.json
```

### Pipeline Management

```bash
# List pipelines
aws codepipeline list-pipelines

# Get pipeline status
aws codepipeline get-pipeline-state --name myapp-pipeline \
  --query 'stageStates[].{Stage:stageName,Status:latestExecution.status}'

# Start pipeline manually
aws codepipeline start-pipeline-execution --name myapp-pipeline

# Approve manual approval
aws codepipeline put-approval-result \
  --pipeline-name myapp-pipeline \
  --stage-name Approval \
  --action-name ManualApproval \
  --result summary="Approved by DevOps team",status=Approved \
  --token <approval-token>
```

---

## 10.6 Industry Project: GitHub Actions + AWS (Alternative)

Many teams use GitHub Actions instead of CodePipeline.

### .github/workflows/deploy.yml

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: myapp/web
  ECS_CLUSTER: myapp-cluster
  ECS_SERVICE: myapp-web-service

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test

  build-and-deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition.json
          service: ${{ env.ECS_SERVICE }}
          cluster: ${{ env.ECS_CLUSTER }}
          wait-for-service-stability: true
```

---

## 10.7 Common Errors & Troubleshooting

### Error 1: CodeBuild "BUILD_FAILED"
```bash
# View build logs
aws codebuild batch-get-builds --ids <build-id> \
  --query 'builds[0].logs.deepLink'

# Common causes:
# - buildspec.yml syntax error
# - Missing permissions (IAM role)
# - Docker build failure
# - Test failures
```

### Error 2: CodeDeploy "DEPLOYMENT_FAILED"
```bash
# View deployment events
aws deploy get-deployment --deployment-id <id> \
  --query 'deploymentInfo.{Status:status,Error:errorInformation}'

# View instance-level details
aws deploy list-deployment-instances --deployment-id <id>
```

### Error 3: Pipeline stuck at "InProgress"
```bash
# Check which stage is stuck
aws codepipeline get-pipeline-state --name myapp-pipeline

# If stuck at approval, approve or reject
aws codepipeline put-approval-result ...

# If stuck at deploy, check ECS service events
aws ecs describe-services --cluster myapp-cluster --services myapp-web-service \
  --query 'services[0].events[0:5]'
```

---

## 10.8 Key Takeaways

1. CI = automated build + test on every commit
2. CD = automated deployment after successful CI
3. Use buildspec.yml for CodeBuild, appspec.yml for CodeDeploy
4. Blue/Green deployments provide zero-downtime releases
5. Always include rollback configuration in deployments
6. Use manual approval gates before production deployments
7. Store secrets in SSM Parameter Store or Secrets Manager, not in code
8. GitHub Actions is a viable alternative to AWS-native CI/CD tools
