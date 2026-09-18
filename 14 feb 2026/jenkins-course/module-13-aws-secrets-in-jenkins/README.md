# Module 13: AWS Secrets Retrieval in Jenkins Pipelines

## What This Module Covers

How to securely retrieve secrets (database passwords, API keys, tokens) from AWS in Jenkins pipelines — without hardcoding them anywhere.

---

## 1. The Problem

```
❌ BAD — secrets in Jenkinsfile:
  environment {
      DB_PASSWORD = 'MyS3cretP@ss!'     // Visible in source control
      API_KEY = 'sk-abc123...'           // Anyone with repo access can see this
  }

❌ BAD — secrets in Jenkins credentials only:
  - Jenkins is a single point of failure
  - No audit trail of who accessed what
  - No automatic rotation
  - If Jenkins is compromised, all secrets are exposed

✅ GOOD — secrets in AWS, retrieved at runtime:
  - Secrets stored in AWS Secrets Manager or Parameter Store
  - Jenkins retrieves them only when the pipeline runs
  - Automatic rotation supported
  - CloudTrail logs every access
  - IAM controls who/what can read each secret
```

---

## 2. AWS Secrets Manager vs Systems Manager Parameter Store

| Feature | Secrets Manager | Parameter Store |
|---------|----------------|-----------------|
| **Purpose** | Designed for secrets (passwords, tokens, keys) | General config + secrets |
| **Cost** | $0.40/secret/month + $0.05/10K API calls | Free tier: 10K standard params; Advanced: $0.05/param/month |
| **Automatic rotation** | ✅ Built-in with Lambda | ❌ Manual |
| **Cross-account access** | ✅ Resource policies | ⚠️ Requires IAM roles |
| **Max size** | 64 KB | 4 KB (standard) / 8 KB (advanced) |
| **Versioning** | ✅ Automatic | ✅ Labels |
| **Encryption** | ✅ Always encrypted (KMS) | ✅ SecureString type (KMS) |
| **Best for** | DB credentials, API keys, certificates | Feature flags, config values, non-rotating secrets |

**Rule of thumb:** If it rotates or is highly sensitive → Secrets Manager. If it's config or rarely changes → Parameter Store.

---

## 3. Setting Up IAM for Jenkins on EC2

### 3.1 Create an IAM Role for the EC2 Instance

Jenkins running on EC2 should use an **IAM instance profile** — not access keys. This is the most secure method.

```
Jenkins (EC2) ──uses instance profile──▶ IAM Role ──has policy──▶ Access to secrets
```

**Step 1: Create the IAM policy**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadSecrets",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:123456789012:secret:jenkins/*"
            ]
        },
        {
            "Sid": "ReadParameters",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": [
                "arn:aws:ssm:us-east-1:123456789012:parameter/jenkins/*"
            ]
        },
        {
            "Sid": "DecryptWithKMS",
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": [
                "arn:aws:kms:us-east-1:123456789012:key/your-kms-key-id"
            ]
        }
    ]
}
```

> The `Resource` field restricts access to secrets under the `jenkins/` prefix only. Jenkins cannot read secrets outside this path.

**Step 2: Create the IAM role**

```bash
# Create the role with EC2 trust policy
aws iam create-role \
  --role-name JenkinsEC2Role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }'
```

```
# Expected output:
# {
#     "Role": {
#         "RoleName": "JenkinsEC2Role",
#         "Arn": "arn:aws:iam::123456789012:role/JenkinsEC2Role",
#         ...
#     }
# }
```

```bash
# Attach the policy
aws iam put-role-policy \
  --role-name JenkinsEC2Role \
  --policy-name JenkinsSecretsAccess \
  --policy-document file://jenkins-secrets-policy.json
```

**Step 3: Create instance profile and attach to EC2**

```bash
# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name JenkinsEC2Profile

# Add role to profile
aws iam add-role-to-instance-profile \
  --instance-profile-name JenkinsEC2Profile \
  --role-name JenkinsEC2Role

# Attach to running EC2 instance
aws ec2 associate-iam-instance-profile \
  --instance-id i-0abc123def456 \
  --iam-instance-profile Name=JenkinsEC2Profile
```

```
# Expected output:
# {
#     "IamInstanceProfileAssociation": {
#         "InstanceId": "i-0abc123def456",
#         "IamInstanceProfile": {
#             "Arn": "arn:aws:iam::123456789012:instance-profile/JenkinsEC2Profile"
#         },
#         "State": "associating"
#     }
# }
```

**Verify it works from the EC2 instance:**

```bash
# SSH into Jenkins EC2
aws secretsmanager get-secret-value \
  --secret-id jenkins/myapp/db-password \
  --query SecretString \
  --output text
```

```
# Expected output:
# {"username":"admin","password":"MyS3cretP@ss!"}
```

### 3.2 Why Not Use Access Keys?

| Method | Security | Rotation | Audit |
|--------|----------|----------|-------|
| IAM Instance Profile | ✅ No keys to leak | ✅ Auto-rotated by AWS | ✅ CloudTrail |
| Access Keys in Jenkins | ❌ Keys stored on disk | ❌ Manual rotation | ⚠️ Partial |
| Access Keys in Jenkinsfile | ❌❌ Keys in source control | ❌ Manual | ❌ None |

Always use IAM instance profiles for EC2-based Jenkins.

---

## 4. Storing Secrets in AWS

### 4.1 AWS Secrets Manager

**Create a secret via CLI:**

```bash
aws secretsmanager create-secret \
  --name jenkins/myapp/db-credentials \
  --description "Database credentials for myapp" \
  --secret-string '{"username":"admin","password":"MyS3cretP@ss!","host":"mydb.cluster-abc.us-east-1.rds.amazonaws.com","port":"5432"}'
```

```
# Expected output:
# {
#     "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:jenkins/myapp/db-credentials-AbCdEf",
#     "Name": "jenkins/myapp/db-credentials",
#     "VersionId": "a1b2c3d4-..."
# }
```

**Create a secret via AWS Console:**

1. Go to **AWS Secrets Manager → Store a new secret**
2. Secret type: **Other type of secret**
3. Key/value pairs:
   - `username` = `admin`
   - `password` = `MyS3cretP@ss!`
4. Secret name: `jenkins/myapp/db-credentials`
5. Rotation: configure if needed

### 4.2 Systems Manager Parameter Store

```bash
# Store a plain text parameter
aws ssm put-parameter \
  --name "/jenkins/myapp/api-url" \
  --type "String" \
  --value "https://api.example.com/v2"

# Store an encrypted parameter (SecureString)
aws ssm put-parameter \
  --name "/jenkins/myapp/api-key" \
  --type "SecureString" \
  --value "sk-abc123def456" \
  --key-id "alias/aws/ssm"
```

```
# Expected output:
# {
#     "Version": 1,
#     "Tier": "Standard"
# }
```

**Naming convention recommendation:**

```
/jenkins/{app-name}/{secret-name}

Examples:
  /jenkins/myapp/db-password
  /jenkins/myapp/api-key
  /jenkins/shared/docker-registry-token
  /jenkins/shared/sonarqube-token
```

---

## 5. Retrieving Secrets in Jenkins Pipelines

### 5.1 Method 1: AWS CLI in Shell Steps (Simple)

```groovy
pipeline {
    agent any

    stages {
        stage('Get Secrets and Deploy') {
            steps {
                script {
                    // Retrieve from Secrets Manager
                    def dbCreds = sh(
                        script: '''
                            aws secretsmanager get-secret-value \
                              --secret-id jenkins/myapp/db-credentials \
                              --query SecretString \
                              --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    // Parse JSON
                    def creds = readJSON text: dbCreds
                    def dbUser = creds.username
                    def dbPass = creds.password

                    // Use in deployment (values are masked in logs)
                    sh """
                        export DB_USER='${dbUser}'
                        export DB_PASS='${dbPass}'
                        ./deploy.sh
                    """
                }
            }
        }
    }
}
```

```
# Console output:
# + aws secretsmanager get-secret-value --secret-id jenkins/myapp/db-credentials ...
# + ./deploy.sh
# Deploying with database user: admin
# Finished: SUCCESS
```

> ⚠️ With this method, the secret value passes through the shell. Use `set +x` to prevent echoing.

### 5.2 Method 2: AWS CLI with Masking (Recommended for CLI approach)

```groovy
pipeline {
    agent any

    stages {
        stage('Deploy') {
            steps {
                script {
                    // Retrieve secret
                    def secretJson = sh(
                        script: '''
                            set +x
                            aws secretsmanager get-secret-value \
                              --secret-id jenkins/myapp/db-credentials \
                              --query SecretString \
                              --output text 2>/dev/null
                        ''',
                        returnStdout: true
                    ).trim()

                    def creds = readJSON text: secretJson

                    // Wrap in Jenkins credentials to mask in logs
                    wrap([$class: 'MaskPasswordsBuildWrapper',
                          varPasswordPairs: [
                              [password: creds.password, var: 'DB_PASS']
                          ]]) {
                        sh """
                            echo "Connecting to DB as ${creds.username}"
                            echo "Password is: ${creds.password}"
                        """
                        // Output: "Password is: ********"
                    }
                }
            }
        }
    }
}
```

### 5.3 Method 3: AWS Secrets Manager Jenkins Plugin (Best)

Install the **"AWS Secrets Manager Credentials Provider"** plugin.

**Plugin setup:**

1. **Manage Jenkins → Plugins → Available → search "AWS Secrets Manager Credentials Provider"**
2. Install and restart
3. **Manage Jenkins → System → AWS Secrets Manager Credentials Provider**
   - AWS Region: `us-east-1`
   - Authentication: Default (uses instance profile)

**How the plugin works:**

```
AWS Secrets Manager                    Jenkins Credentials
┌──────────────────────┐              ┌──────────────────────┐
│ jenkins/myapp/db-pw  │  ──syncs──▶  │ ID: jenkins/myapp/   │
│ Value: "MyS3cret"    │              │     db-pw            │
│ Tag: jenkins:cred    │              │ Type: Secret text    │
│     entials:type =   │              │ Value: "MyS3cret"    │
│     string           │              │                      │
└──────────────────────┘              └──────────────────────┘
```

The plugin automatically maps AWS secrets to Jenkins credentials. You use them like any other Jenkins credential:

```groovy
pipeline {
    agent any

    environment {
        // The credential ID matches the secret name in AWS
        DB_PASSWORD = credentials('jenkins/myapp/db-password')
    }

    stages {
        stage('Deploy') {
            steps {
                sh '''
                    echo "DB password is: $DB_PASSWORD"
                    # Output: "DB password is: ****"
                    # Jenkins automatically masks credential values in logs
                '''
            }
        }
    }
}
```

**For username/password secrets (JSON with `username` and `password` keys):**

```groovy
environment {
    DB_CREDS = credentials('jenkins/myapp/db-credentials')
    // This creates three variables:
    //   DB_CREDS_USR = username
    //   DB_CREDS_PSW = password
    //   DB_CREDS     = username:password
}
```

**AWS secret tags required by the plugin:**

| Tag Key | Tag Value | Purpose |
|---------|-----------|---------|
| `jenkins:credentials:type` | `string` | Maps to Secret text credential |
| `jenkins:credentials:type` | `usernamePassword` | Maps to Username with password |
| `jenkins:credentials:type` | `sshUserPrivateKey` | Maps to SSH key credential |
| `jenkins:credentials:type` | `certificate` | Maps to Certificate credential |

**Create a tagged secret:**

```bash
aws secretsmanager create-secret \
  --name jenkins/myapp/db-password \
  --secret-string 'MyS3cretP@ss!' \
  --tags '[{"Key":"jenkins:credentials:type","Value":"string"}]'
```

### 5.4 Method 4: Parameter Store in Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('Get Config') {
            steps {
                script {
                    // Get a single parameter
                    def apiUrl = sh(
                        script: '''
                            aws ssm get-parameter \
                              --name /jenkins/myapp/api-url \
                              --query Parameter.Value \
                              --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    // Get an encrypted parameter (SecureString)
                    def apiKey = sh(
                        script: '''
                            set +x
                            aws ssm get-parameter \
                              --name /jenkins/myapp/api-key \
                              --with-decryption \
                              --query Parameter.Value \
                              --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    // Get multiple parameters by path
                    def allParams = sh(
                        script: '''
                            aws ssm get-parameters-by-path \
                              --path /jenkins/myapp/ \
                              --with-decryption \
                              --query "Parameters[*].{Name:Name,Value:Value}" \
                              --output json
                        ''',
                        returnStdout: true
                    ).trim()

                    echo "API URL: ${apiUrl}"
                    // apiKey is used but not printed
                }
            }
        }
    }
}
```

---

## 6. Complete Pipeline Example

A real-world pipeline that retrieves secrets from AWS and uses them across stages:

```groovy
pipeline {
    agent any

    environment {
        AWS_REGION       = 'us-east-1'
        ECR_REGISTRY     = '123456789012.dkr.ecr.us-east-1.amazonaws.com'
        APP_NAME         = 'myapp'
        // Plugin-managed credentials (from AWS Secrets Manager)
        SONAR_TOKEN      = credentials('jenkins/shared/sonarqube-token')
        DOCKER_CREDS     = credentials('jenkins/shared/docker-registry')
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/myorg/myapp.git',
                    branch: 'main',
                    credentialsId: 'github-pat'
            }
        }

        stage('Get DB Credentials') {
            steps {
                script {
                    // Retrieve database credentials for integration tests
                    def secretJson = sh(
                        script: '''
                            set +x
                            aws secretsmanager get-secret-value \
                              --secret-id jenkins/myapp/db-credentials \
                              --query SecretString \
                              --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    def creds = readJSON text: secretJson
                    env.DB_HOST = creds.host
                    env.DB_USER = creds.username
                    env.DB_PASS = creds.password
                    env.DB_PORT = creds.port
                }
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }

        stage('Integration Tests') {
            steps {
                // Tests use DB_HOST, DB_USER, DB_PASS from environment
                sh '''
                    set +x
                    mvn verify \
                      -Ddb.host=$DB_HOST \
                      -Ddb.user=$DB_USER \
                      -Ddb.password=$DB_PASS \
                      -Ddb.port=$DB_PORT
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                // SONAR_TOKEN comes from AWS Secrets Manager via plugin
                sh '''
                    mvn sonar:sonar \
                      -Dsonar.host.url=http://sonarqube:9000 \
                      -Dsonar.token=$SONAR_TOKEN
                '''
            }
        }

        stage('Docker Build & Push') {
            steps {
                sh '''
                    # Login to ECR using instance profile (no keys needed)
                    aws ecr get-login-password --region $AWS_REGION | \
                      docker login --username AWS --password-stdin $ECR_REGISTRY

                    docker build -t $ECR_REGISTRY/$APP_NAME:${BUILD_NUMBER} .
                    docker push $ECR_REGISTRY/$APP_NAME:${BUILD_NUMBER}
                '''
            }
        }

        stage('Deploy to K8s') {
            steps {
                script {
                    // Get K8s config from Parameter Store
                    def k8sCluster = sh(
                        script: '''
                            aws ssm get-parameter \
                              --name /jenkins/myapp/k8s-cluster-name \
                              --query Parameter.Value \
                              --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    sh """
                        aws eks update-kubeconfig \
                          --name ${k8sCluster} \
                          --region ${AWS_REGION}

                        kubectl set image deployment/${APP_NAME} \
                          ${APP_NAME}=${ECR_REGISTRY}/${APP_NAME}:${BUILD_NUMBER} \
                          -n production
                    """
                }
            }
        }
    }

    post {
        always {
            // Clean up sensitive environment variables
            script {
                env.DB_PASS = ''
            }
            cleanWs()
        }
    }
}
```

```
# Console output:
# [Pipeline] stage (Get DB Credentials)
# + set +x                                    ← commands hidden
# [Pipeline] stage (Build)
# + mvn clean package -DskipTests
# ...
# [Pipeline] stage (Integration Tests)
# + set +x                                    ← DB password not visible
# ...
# [Pipeline] stage (Docker Build & Push)
# + aws ecr get-login-password ...
# Login Succeeded
# + docker build -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/myapp:42 .
# + docker push ...
# [Pipeline] stage (Deploy to K8s)
# + aws eks update-kubeconfig --name my-cluster --region us-east-1
# + kubectl set image deployment/myapp myapp=...myapp:42 -n production
# deployment.apps/myapp image updated
# Finished: SUCCESS
```

---

## 7. Secret Rotation

### 7.1 Automatic Rotation with Secrets Manager

```bash
# Enable rotation with a Lambda function
aws secretsmanager rotate-secret \
  --secret-id jenkins/myapp/db-credentials \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:SecretsRotation \
  --rotation-rules '{"AutomaticallyAfterDays": 30}'
```

**What happens during rotation:**

```
Day 0: Secret = "OldPassword123"
  │
  ▼ (rotation Lambda runs)
  │
Day 30: Secret = "NewPassword456" (automatically generated)
  │
  ▼
Jenkins pipeline runs → retrieves "NewPassword456" → works seamlessly
  │
  ▼
No Jenkinsfile changes needed — the secret name stays the same
```

### 7.2 Pipeline-Triggered Rotation Check

```groovy
stage('Verify Secret Freshness') {
    steps {
        script {
            def secretMeta = sh(
                script: '''
                    aws secretsmanager describe-secret \
                      --secret-id jenkins/myapp/db-credentials \
                      --query '{LastRotated:LastRotatedDate,NextRotation:NextRotationDate}' \
                      --output json
                ''',
                returnStdout: true
            ).trim()

            echo "Secret rotation info: ${secretMeta}"
        }
    }
}
```

---

## 8. Security Best Practices

| Practice | Why |
|----------|-----|
| Use IAM instance profiles, not access keys | Keys can leak; profiles are automatic |
| Restrict IAM policy to `jenkins/*` prefix | Least privilege — Jenkins can't read other secrets |
| Enable CloudTrail logging | Audit who accessed which secret and when |
| Use `set +x` before secret retrieval | Prevents shell from echoing commands with secrets |
| Clean workspace after build | `cleanWs()` removes any files containing secrets |
| Use the Secrets Manager plugin | Automatic masking in Jenkins logs |
| Tag secrets with `jenkins:credentials:type` | Plugin auto-maps to correct credential type |
| Rotate secrets on a schedule | Limits blast radius if a secret is compromised |
| Use separate secrets per environment | `jenkins/myapp/prod/db-pw` vs `jenkins/myapp/dev/db-pw` |
| Never print secrets in echo/sh | Even masked values can leak in error messages |

---

## 9. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Unable to locate credentials` | No instance profile attached | Attach IAM instance profile to EC2 |
| `AccessDeniedException` | IAM policy too restrictive | Check Resource ARN matches secret path |
| `ResourceNotFoundException` | Wrong secret name or region | Verify secret name and `--region` flag |
| `KMS access denied` | Missing KMS decrypt permission | Add `kms:Decrypt` for the KMS key ARN |
| Secret not appearing in Jenkins credentials | Missing plugin tag | Add `jenkins:credentials:type` tag to secret |
| Stale secret value in Jenkins | Plugin cache | Restart Jenkins or wait for cache refresh (default: 5 min) |
| `command not found: aws` | AWS CLI not installed on agent | Install AWS CLI on all build agents |
