# Module 18: Additional Services & Solutions Architecture

## 18.1 CloudFormation — Advanced Features

### Service Role

A service role allows CloudFormation to create resources on your behalf, even if you don't have direct permissions to create those resources.

```bash
aws cloudformation create-stack \
  --stack-name my-stack \
  --template-body file://template.yaml \
  --role-arn arn:aws:iam::123456789012:role/CloudFormationServiceRole
```

### CloudFormation with Security Group and Elastic IP

```yaml
Parameters:
  SecurityGroupDescription:
    Description: Security Group Description
    Type: String

Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      AvailabilityZone: us-east-1a
      ImageId: ami-0abcdef1234567890
      InstanceType: t3.micro
      SecurityGroups:
        - !Ref SSHSecurityGroup
        - !Ref ServerSecurityGroup

  MyEIP:
    Type: AWS::EC2::EIP
    Properties:
      InstanceId: !Ref MyInstance

  SSHSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Enable SSH access via port 22
      SecurityGroupIngress:
        - CidrIp: 0.0.0.0/0
          FromPort: 22
          IpProtocol: tcp
          ToPort: 22

  ServerSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: !Ref SecurityGroupDescription
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

Outputs:
  ElasticIP:
    Description: Elastic IP Value
    Value: !Ref MyEIP
```

### Infrastructure Composer (formerly Application Composer)

Visual drag-and-drop tool for designing CloudFormation templates. Generates YAML/JSON automatically.

---

## 18.2 Systems Manager (SSM)

### SSM Session Manager

Start a shell session on EC2 without SSH, bastion hosts, or open ports.

- No port 22 needed (no SSH keys)
- Full audit logging to S3/CloudWatch
- Works through IAM permissions
- Supports Linux, Windows, macOS

### SSM Run Command

Execute commands across multiple EC2 instances without SSH.

```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Environment,Values=production" \
  --parameters 'commands=["yum update -y"]'
```

### SSM Patch Manager

Automate OS and software patching across EC2 instances.

- Define patch baselines (which patches to apply)
- Schedule patching with maintenance windows
- Report compliance status

### SSM Parameter Store

Hierarchical storage for configuration data and secrets.

```bash
# Store parameters
aws ssm put-parameter --name "/my-app/dev/db-url" --value "mydb.dev.rds.amazonaws.com" --type String
aws ssm put-parameter --name "/my-app/dev/db-password" --value "SecretPass!" --type SecureString

# Retrieve parameters
aws ssm get-parameters --names /my-app/dev/db-url /my-app/dev/db-password --with-decryption

# Get all parameters by path
aws ssm get-parameters-by-path --path /my-app/ --recursive --with-decryption
```

### SSM Parameter Store in Lambda

```python
import boto3
import os

ssm = boto3.client('ssm', region_name="us-east-1")
dev_or_prod = os.environ['DEV_OR_PROD']

def lambda_handler(event, context):
    db_url = ssm.get_parameters(Names=[f"/my-app/{dev_or_prod}/db-url"])
    db_password = ssm.get_parameters(
        Names=[f"/my-app/{dev_or_prod}/db-password"],
        WithDecryption=True
    )
    return {
        "statusCode": 200,
        "body": f"Connected to {db_url['Parameters'][0]['Value']}"
    }
```

```bash
# Create the parameters first
aws ssm put-parameter --name "/my-app/prod/db-url" \
  --value "mydb.cluster-abcdef.us-east-1.rds.amazonaws.com" \
  --type String

aws ssm put-parameter --name "/my-app/prod/db-password" \
  --value "SuperSecretPassword123" \
  --type SecureString

# Deploy the Lambda function
aws lambda create-function \
  --function-name ssm-demo \
  --runtime python3.12 \
  --handler index.lambda_handler \
  --role arn:aws:iam::123456789012:role/LambdaSSMRole \
  --zip-file fileb://function.zip \
  --environment 'Variables={DEV_OR_PROD=prod}'

# The Lambda role needs ssm:GetParameters and kms:Decrypt permissions

# Test the function
aws lambda invoke --function-name ssm-demo output.json && cat output.json
# Expected output:
# {"statusCode": 200, "body": "Connected to mydb.cluster-abcdef.us-east-1.rds.amazonaws.com"}
```

**Best practice:** Cache SSM parameters in Lambda using the AWS Parameters and Secrets Lambda Extension (Layer). This reduces API calls and latency by caching parameters for a configurable TTL.

---

## 18.3 AWS Cost Management

### Cost Explorer

Visualize, understand, and manage AWS costs and usage over time.

- View costs by service, account, tag, region
- Forecast future costs (up to 12 months)
- Identify Savings Plan and Reserved Instance recommendations
- Hourly and resource-level granularity

### AWS Cost Anomaly Detection

Uses ML to detect unusual spending patterns. Sends alerts via SNS or email.

### AWS Budgets

Set custom budgets and receive alerts when costs or usage exceed thresholds.

```bash
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "monthly-100",
    "BudgetLimit": {"Amount": "100", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "admin@example.com"
    }]
  }]'
```

---

## 18.4 Amazon SES (Simple Email Service)

Managed email service for sending and receiving emails.

- Transactional emails, marketing emails, bulk emails
- High deliverability
- Pay per email sent (~$0.10 per 1,000 emails)

```bash
# Verify an email identity
aws ses verify-email-identity --email-address sender@example.com

# Verify a domain (for production use)
aws ses verify-domain-identity --domain example.com
# Returns a TXT record to add to DNS for verification

# Send a simple email
aws ses send-email \
  --from sender@example.com \
  --destination '{"ToAddresses":["recipient@example.com"]}' \
  --message '{
    "Subject": {"Data": "Order Confirmation"},
    "Body": {"Html": {"Data": "<h1>Your order #12345 is confirmed</h1>"}}
  }'

# Expected output:
# {
#   "MessageId": "0100018d1234abcd-12345678-1234-1234-1234-123456789012-000000"
# }

# Send using a template (for bulk emails)
aws ses create-template --template '{
  "TemplateName": "OrderConfirmation",
  "SubjectPart": "Order #{{orderId}} Confirmed",
  "HtmlPart": "<h1>Hi {{name}}, your order #{{orderId}} is confirmed!</h1>"
}'

aws ses send-templated-email \
  --source sender@example.com \
  --destination '{"ToAddresses":["customer@example.com"]}' \
  --template OrderConfirmation \
  --template-data '{"name":"John","orderId":"12345"}'

# Check sending statistics
aws ses get-send-statistics
```

**SES vs SNS:** SES is for email (transactional/marketing). SNS is for notifications (email, SMS, push, SQS, Lambda). Use SES when you need email-specific features like templates, deliverability tracking, and bounce handling.

---

## 18.5 Amazon Pinpoint

Marketing communication service for targeted messaging.

- Email, SMS, push notifications, voice, in-app messaging
- Segment users and create targeted campaigns
- A/B testing for messages
- Unlike SNS (single message), Pinpoint manages campaigns and audiences

```bash
# Create a Pinpoint project
aws pinpoint create-app --create-application-request Name=my-marketing-app

# Expected output:
# {
#   "ApplicationResponse": {
#     "Arn": "arn:aws:mobiletargeting:us-east-1:123456789012:apps/abcdef1234567890",
#     "Id": "abcdef1234567890",
#     "Name": "my-marketing-app"
#   }
# }

# Enable the email channel
aws pinpoint update-email-channel \
  --application-id abcdef1234567890 \
  --email-channel-request '{
    "FromAddress": "marketing@example.com",
    "Identity": "arn:aws:ses:us-east-1:123456789012:identity/example.com",
    "Enabled": true
  }'

# Send a direct message
aws pinpoint send-messages \
  --application-id abcdef1234567890 \
  --message-request '{
    "Addresses": {
      "user@example.com": {"ChannelType": "EMAIL"}
    },
    "MessageConfiguration": {
      "EmailMessage": {
        "SimpleEmail": {
          "Subject": {"Data": "Flash Sale!"},
          "HtmlPart": {"Data": "<h1>50% off today only!</h1>"}
        }
      }
    }
  }'
```

**SES vs SNS vs Pinpoint:**
| Feature | SES | SNS | Pinpoint |
|---------|-----|-----|----------|
| **Purpose** | Transactional email | Notifications | Marketing campaigns |
| **Channels** | Email only | Email, SMS, push, SQS | Email, SMS, push, voice, in-app |
| **Audience** | Individual recipients | Topic subscribers | Segmented user groups |
| **Analytics** | Delivery/bounce stats | Basic delivery | Full campaign analytics, A/B testing |

---

## 18.6 AWS Batch

Run batch computing jobs at any scale. AWS manages the compute infrastructure.

```
Job Queue ──▶ AWS Batch ──▶ EC2 / Spot / Fargate (auto-provisioned)
```

### Batch vs Lambda

| Feature | Lambda | Batch |
|---------|--------|-------|
| **Time limit** | 15 minutes | No limit |
| **Runtime** | Limited languages | Any Docker image |
| **Storage** | 10 GB /tmp | EBS volumes |
| **Serverless** | Yes | Yes (Fargate) or EC2 |
| **Best for** | Short tasks, event-driven | Long-running jobs, HPC |

---

## 18.7 Amazon AppFlow

Managed integration service for transferring data between SaaS apps and AWS.

```
Salesforce ──▶ AppFlow ──▶ S3 / Redshift
Slack ──▶ AppFlow ──▶ S3
SAP ──▶ AppFlow ──▶ S3
```

- Supports: Salesforce, SAP, Zendesk, Slack, ServiceNow, Google Analytics, etc.
- Data transformation: filtering, validation, mapping
- Encrypted in transit and at rest
- Schedule or event-driven transfers

---

## 18.8 AWS Amplify

Build and deploy full-stack web and mobile applications.

- Frontend: React, Vue, Angular, Next.js
- Backend: Authentication (Cognito), API (AppSync/API Gateway), Storage (S3), Database (DynamoDB)
- CI/CD: Connect to Git repo, auto-deploy on push
- Hosting: Global CDN with custom domains

---

## 18.9 AWS Organizations — Advanced

### Service Control Policies (SCPs)

SCPs restrict what actions accounts in an Organization can perform. They don't grant permissions — they set maximum permission boundaries.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyDeleteS3",
            "Effect": "Deny",
            "Action": ["s3:DeleteBucket", "s3:DeleteObject"],
            "Resource": "*"
        }
    ]
}
```

### IAM Permission Boundaries

Set the maximum permissions an IAM user or role can have. Even if a policy grants broader access, the boundary limits it.

```
Effective permissions = IAM Policy ∩ Permission Boundary
```

### Tag Policies

Standardize tags across all accounts in an Organization. Define allowed tag keys and values. Enforce consistent tagging for cost allocation and resource management.

```bash
# Enable tag policies in the Organization
aws organizations enable-policy-type \
  --root-id r-abcd \
  --policy-type TAG_POLICY

# Create a tag policy (enforce "Environment" tag with specific values)
aws organizations create-policy \
  --name "environment-tag-policy" \
  --type TAG_POLICY \
  --content '{
    "tags": {
      "Environment": {
        "tag_key": {"@@assign": "Environment"},
        "tag_value": {"@@assign": ["production", "staging", "development"]},
        "enforced_for": {"@@assign": ["ec2:instance", "s3:bucket", "rds:db"]}
      },
      "CostCenter": {
        "tag_key": {"@@assign": "CostCenter"},
        "tag_value": {"@@assign": ["engineering", "marketing", "finance"]}
      }
    }
  }' \
  --description "Enforce standard tag keys and values"

# Attach the policy to an OU
aws organizations attach-policy \
  --policy-id p-abcdef1234567890 \
  --target-id ou-abcd-12345678

# Check tag compliance
aws resourcegroupstaggingapi get-compliance-summary \
  --tag-key-filters Key=Environment
```

**Real-life use case:** A company with 50 AWS accounts enforces that every EC2 instance and S3 bucket must have an `Environment` tag with value `production`, `staging`, or `development`. This enables accurate cost allocation reports by environment.

### IAM Policy Evaluation Logic

```
1. Explicit Deny? ──▶ DENY (always wins)
2. SCP allows? ──▶ If no, DENY
3. Resource-based policy allows? ──▶ If yes, ALLOW
4. Permission boundary allows? ──▶ If no, DENY
5. Session policy allows? ──▶ If no, DENY
6. Identity-based policy allows? ──▶ If yes, ALLOW
7. Default: DENY
```

---

## 18.10 Solutions Architecture Patterns

### Fan-Out Pattern

```
S3 Upload ──▶ SNS Topic ──▶ SQS Queue 1 ──▶ Lambda (process)
                         ──▶ SQS Queue 2 ──▶ Lambda (archive)
                         ──▶ SQS Queue 3 ──▶ Lambda (notify)
```

S3 can only send events to one destination per prefix. Use SNS fan-out to send to multiple SQS queues.

### Caching Strategy

```
Client ──▶ CloudFront (edge cache)
              │ miss
              ▼
         API Gateway (API cache)
              │ miss
              ▼
         Lambda ──▶ ElastiCache (app cache)
                        │ miss
                        ▼
                    DynamoDB / RDS
```

### Blocking an IP Address

| Layer | Method |
|-------|--------|
| **CloudFront + WAF** | WAF IP set rule (best — blocks at edge) |
| **ALB** | Security Group (allow only CloudFront IPs) |
| **NLB** | NACL (NLB doesn't support SGs) |
| **EC2** | Security Group + NACL |

### High Performance Computing (HPC)

| Component | Service |
|-----------|---------|
| **Data transfer** | Direct Connect, Snowball, DataSync |
| **Compute** | EC2 (GPU/CPU optimized), Spot instances |
| **Networking** | Cluster Placement Group, EFA (Elastic Fabric Adapter), Enhanced Networking |
| **Storage** | EBS io2, Instance Store, FSx for Lustre, S3 |
| **Orchestration** | AWS Batch, ParallelCluster |

---

## 18.11 AWS Machine Learning Services (Overview)

| Service | Purpose |
|---------|---------|
| **Rekognition** | Image and video analysis (faces, objects, text, content moderation) |
| **Transcribe** | Speech to text |
| **Polly** | Text to speech |
| **Translate** | Language translation |
| **Lex** | Chatbots (same tech as Alexa) |
| **Connect** | Cloud contact center |
| **Comprehend** | NLP — sentiment analysis, entity extraction |
| **SageMaker** | Build, train, deploy ML models |
| **Kendra** | ML-powered document search |
| **Personalize** | Real-time personalized recommendations |
| **Textract** | Extract text and data from documents (OCR+) |

---

## 18.12 AWS Elastic Beanstalk

Deploy and manage web applications without worrying about infrastructure. Supports: Java, .NET, PHP, Node.js, Python, Ruby, Go, Docker.

- Handles capacity provisioning, load balancing, auto-scaling, health monitoring
- You retain full control over underlying resources
- Free — you only pay for the resources created

### Deployment Modes

| Mode | Description |
|------|-------------|
| **Single Instance** | One EC2 + Elastic IP (dev) |
| **High Availability** | ALB + ASG across AZs (prod) |

---

## 18.13 AWS Transfer Family

Managed file transfer service using SFTP, FTPS, and FTP protocols. Backed by S3 or EFS.

```
SFTP Client ──▶ AWS Transfer Family ──▶ S3 / EFS
```

Use case: migrate existing file transfer workflows to AWS without changing client applications.

---

## 18.14 AWS Outposts

AWS infrastructure and services deployed on-premises. Fully managed by AWS — same hardware, APIs, and tools as in the cloud.

```
┌─────────────────────────────────────────────┐
│              Your Data Center               │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │         AWS Outpost Rack              │  │
│  │                                       │  │
│  │  EC2  │  EBS  │  S3  │  RDS  │  ECS  │  │
│  │                                       │  │
│  │  Same APIs as AWS Region              │  │
│  └───────────────────────────────────────┘  │
│              │                              │
│              │ Service Link (to AWS Region)  │
└──────────────┼──────────────────────────────┘
               │
         AWS Region (parent)
```

```bash
# List Outpost sites
aws outposts list-sites

# List Outposts
aws outposts list-outposts \
  --query 'Outposts[].{Id:OutpostId,Name:Name,AZ:AvailabilityZone}'

# Launch an EC2 instance on Outpost
aws ec2 run-instances \
  --instance-type m5.xlarge \
  --placement "AvailabilityZone=us-east-1a" \
  --subnet-id subnet-outpost-0abcdef \
  --image-id ami-0abcdef1234567890 \
  --min-count 1 --max-count 1

# Create an S3 bucket on Outpost (S3 on Outposts)
aws s3control create-bucket \
  --bucket my-outpost-bucket \
  --outpost-id op-0abcdef1234567890
```

**Use cases:** Data residency requirements (data must stay on-premises), low-latency local processing, migration stepping stone. **Services available:** EC2, EBS, S3, RDS, ECS, EKS, EMR, ALB.

---

## 18.15 AWS WaveLength

Deploy applications at the edge of 5G networks for ultra-low latency. WaveLength Zones are AWS infrastructure embedded in telecom providers' data centers (Verizon, Vodafone, KDDI, SK Telecom).

```bash
# List available WaveLength Zones
aws ec2 describe-availability-zones \
  --filters Name=zone-type,Values=wavelength-zone \
  --query 'AvailabilityZones[].{Zone:ZoneName,State:State}'

# Expected output:
# [
#   {"Zone": "us-east-1-wl1-bos-wlz-1", "State": "available"},
#   {"Zone": "us-east-1-wl1-nyc-wlz-1", "State": "available"}
# ]

# Enable a WaveLength Zone
aws ec2 modify-availability-zone-group \
  --group-name us-east-1-wl1 \
  --opt-in-status opted-in

# Create a subnet in the WaveLength Zone
aws ec2 create-subnet \
  --vpc-id vpc-0abcdef1234567890 \
  --cidr-block 10.0.100.0/24 \
  --availability-zone us-east-1-wl1-bos-wlz-1

# Launch an instance in the WaveLength Zone
aws ec2 run-instances \
  --instance-type t3.medium \
  --subnet-id subnet-wavelength-0abcdef \
  --image-id ami-0abcdef1234567890 \
  --min-count 1 --max-count 1
```

**Use cases:** Interactive live video streaming, AR/VR, real-time gaming, connected vehicles. Traffic from 5G devices reaches the WaveLength Zone without leaving the telecom network, achieving single-digit millisecond latency.

---

## 18.16 AWS Local Zones

Extend a VPC to a location closer to end users. Provides compute, storage, database, and other services in metro areas. Use for latency-sensitive applications that need single-digit millisecond latency.

```bash
# List available Local Zones
aws ec2 describe-availability-zones \
  --filters Name=zone-type,Values=local-zone \
  --query 'AvailabilityZones[].{Zone:ZoneName,State:State,Group:GroupName}' | head -20

# Expected output:
# [
#   {"Zone": "us-east-1-bos-1a", "State": "available", "Group": "us-east-1-bos-1"},
#   {"Zone": "us-west-2-lax-1a", "State": "available", "Group": "us-west-2-lax-1"}
# ]

# Enable a Local Zone
aws ec2 modify-availability-zone-group \
  --group-name us-west-2-lax-1 \
  --opt-in-status opted-in

# Create a subnet in the Local Zone
aws ec2 create-subnet \
  --vpc-id vpc-0abcdef1234567890 \
  --cidr-block 10.0.200.0/24 \
  --availability-zone us-west-2-lax-1a

# Launch an instance in the Local Zone
aws ec2 run-instances \
  --instance-type t3.medium \
  --subnet-id subnet-localzone-0abcdef \
  --image-id ami-0abcdef1234567890 \
  --min-count 1 --max-count 1
```

**Outposts vs WaveLength vs Local Zones:**

| Feature | Outposts | WaveLength | Local Zones |
|---------|----------|------------|-------------|
| **Location** | Your data center | Telecom 5G edge | AWS metro PoPs |
| **Managed by** | AWS (on your premises) | AWS (at telecom) | AWS |
| **Latency** | On-premises | Single-digit ms (5G) | Single-digit ms |
| **Use case** | Data residency, hybrid | 5G edge apps | Metro-area low latency |
| **Network** | Service Link to Region | Carrier Gateway | Internet/DX |

---

## 18.17 Application Discovery Service

Plan migration by collecting information about on-premises data centers.

| Discovery Type | Method | Data Collected |
|---------------|--------|----------------|
| **Agentless** | OVA appliance in VMware | VM inventory, CPU, memory, disk |
| **Agent-based** | Install agent on each server | System config, processes, network connections |

```bash
# Start agentless discovery (after deploying the Discovery Connector)
aws discovery start-data-collection-by-agent-ids \
  --agent-ids agent-0abcdef1234567890

# List discovered servers
aws discovery describe-configurations \
  --configuration-ids server-0abcdef1234567890

# Export discovery data for Migration Hub
aws discovery start-export-task \
  --export-data-format CSV
```

**Real-life use case:** Before migrating 200 servers to AWS, the team deploys the Discovery Agent to understand dependencies between servers. The data feeds into AWS Migration Hub for planning the migration waves.

---

## 18.18 Key Takeaways

1. SSM Session Manager replaces bastion hosts — no SSH, no open ports, full audit
2. SSM Parameter Store for config; Secrets Manager for secrets with auto-rotation
3. Cost Explorer for cost analysis; Budgets for alerts; Cost Anomaly Detection for ML-based alerts
4. AWS Batch for long-running jobs; Lambda for short event-driven tasks
5. AppFlow for SaaS-to-AWS data integration (Salesforce, SAP, etc.)
6. SCPs set maximum permissions for Organization accounts (don't grant, only restrict)
7. Permission Boundaries set maximum permissions for IAM users/roles
8. Fan-out pattern: S3 → SNS → multiple SQS queues for parallel processing
9. Block IPs at the edge with CloudFront + WAF for best performance
10. Use Cluster Placement Groups + EFA for HPC networking
