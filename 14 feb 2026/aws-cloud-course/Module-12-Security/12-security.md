# Module 12: Security, KMS, WAF & Best Practices

## 12.1 AWS Security Model

### Shared Responsibility Model

```
┌─────────────────────────────────────────────────────┐
│           Shared Responsibility Model                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  CUSTOMER Responsibility ("Security IN the Cloud"):  │
│  ┌─────────────────────────────────────────────────┐│
│  │ Data encryption & integrity                      ││
│  │ Identity & access management (IAM)               ││
│  │ Operating system patches (EC2)                   ││
│  │ Network & firewall configuration                 ││
│  │ Application security                             ││
│  │ Client-side encryption                           ││
│  └─────────────────────────────────────────────────┘│
│                                                      │
│  AWS Responsibility ("Security OF the Cloud"):       │
│  ┌─────────────────────────────────────────────────┐│
│  │ Physical data center security                    ││
│  │ Hardware & infrastructure                        ││
│  │ Network infrastructure                           ││
│  │ Hypervisor                                       ││
│  │ Managed service patching (RDS, Lambda, etc.)     ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## 12.2 KMS (Key Management Service)

KMS manages encryption keys for your data.

### Create a KMS Key

```bash
KEY_ID=$(aws kms create-key \
  --description "Application encryption key" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS \
  --query 'KeyMetadata.KeyId' --output text)

# Create an alias (friendly name)
aws kms create-alias \
  --alias-name alias/myapp-key \
  --target-key-id $KEY_ID

echo "Key ID: $KEY_ID"
```

**Expected Output:**
```
Key ID: 1234abcd-12ab-34cd-56ef-1234567890ab
```

### Encrypt and Decrypt Data

```bash
# Encrypt a string
aws kms encrypt \
  --key-id alias/myapp-key \
  --plaintext "MySecretPassword123" \
  --query 'CiphertextBlob' --output text > encrypted.txt

cat encrypted.txt
# Output: AQICAHh... (base64 encoded ciphertext)

# Decrypt
aws kms decrypt \
  --ciphertext-blob fileb://<(base64 --decode < encrypted.txt) \
  --query 'Plaintext' --output text | base64 --decode

# Output: MySecretPassword123
```

### Encrypt a File

```bash
# Encrypt
aws kms encrypt \
  --key-id alias/myapp-key \
  --plaintext fileb://sensitive-data.txt \
  --output text --query CiphertextBlob | base64 --decode > sensitive-data.encrypted

# Decrypt
aws kms decrypt \
  --ciphertext-blob fileb://sensitive-data.encrypted \
  --output text --query Plaintext | base64 --decode > sensitive-data.decrypted
```

### Key Rotation

```bash
# Enable automatic key rotation (every year)
aws kms enable-key-rotation --key-id $KEY_ID

# Check rotation status
aws kms get-key-rotation-status --key-id $KEY_ID
```

### KMS Key Policy

```bash
aws kms put-key-policy \
  --key-id $KEY_ID \
  --policy-name default \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "Enable Root Account",
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
        "Action": "kms:*",
        "Resource": "*"
      },
      {
        "Sid": "Allow App Role",
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::123456789012:role/AppRole"},
        "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
        "Resource": "*"
      }
    ]
  }'
```

---

## 12.3 Secrets Manager

Secrets Manager stores and rotates secrets (database passwords, API keys).

### Store a Secret

```bash
aws secretsmanager create-secret \
  --name myapp/database \
  --description "Production database credentials" \
  --secret-string '{
    "username": "admin",
    "password": "MyStr0ng!Pass#2024",
    "host": "mydb.c9abc123.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "dbname": "myapp"
  }'
```

### Retrieve a Secret

```bash
# Get the secret value
aws secretsmanager get-secret-value \
  --secret-id myapp/database \
  --query 'SecretString' --output text | python3 -m json.tool
```

**Expected Output:**
```json
{
    "username": "admin",
    "password": "MyStr0ng!Pass#2024",
    "host": "mydb.c9abc123.us-east-1.rds.amazonaws.com",
    "port": 3306,
    "dbname": "myapp"
}
```

### Use in Application (Python)

```python
import boto3
import json

def get_db_credentials():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='myapp/database')
    return json.loads(response['SecretString'])

creds = get_db_credentials()
# Connect: mysql.connect(host=creds['host'], user=creds['username'], ...)
```

### Enable Automatic Rotation

```bash
aws secretsmanager rotate-secret \
  --secret-id myapp/database \
  --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:secret-rotator \
  --rotation-rules AutomaticallyAfterDays=30
```

---

## 12.4 SSM Parameter Store

Parameter Store is a simpler (and cheaper) alternative to Secrets Manager.

```bash
# Store a parameter (free)
aws ssm put-parameter \
  --name "/myapp/production/db-host" \
  --value "mydb.c9abc123.us-east-1.rds.amazonaws.com" \
  --type String

# Store encrypted parameter
aws ssm put-parameter \
  --name "/myapp/production/db-password" \
  --value "MyStr0ng!Pass#2024" \
  --type SecureString \
  --key-id alias/myapp-key

# Retrieve parameter
aws ssm get-parameter \
  --name "/myapp/production/db-host" \
  --query 'Parameter.Value' --output text

# Retrieve encrypted parameter (decrypted)
aws ssm get-parameter \
  --name "/myapp/production/db-password" \
  --with-decryption \
  --query 'Parameter.Value' --output text

# Get all parameters by path
aws ssm get-parameters-by-path \
  --path "/myapp/production/" \
  --with-decryption \
  --query 'Parameters[].{Name:Name,Value:Value}' \
  --output table
```

### Parameter Store vs Secrets Manager

| Feature | Parameter Store | Secrets Manager |
|---------|----------------|-----------------|
| Cost | Free (standard) | $0.40/secret/month |
| Rotation | Manual | Automatic |
| Cross-account | No | Yes |
| Max size | 8 KB | 64 KB |
| Best for | Config values | Database passwords, API keys |

---

## 12.5 WAF (Web Application Firewall)

WAF protects web applications from common attacks (SQL injection, XSS, DDoS).

### Create WAF Web ACL

```bash
aws wafv2 create-web-acl \
  --name myapp-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules '[
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 1,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRules"
      }
    },
    {
      "Name": "AWSManagedRulesSQLiRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesSQLiRuleSet"
        }
      },
      "OverrideAction": {"None": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "SQLiRules"
      }
    },
    {
      "Name": "RateLimit",
      "Priority": 3,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimit"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=myapp-waf
```

### Associate WAF with ALB

```bash
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:us-east-1:123456789012:regional/webacl/myapp-waf/abc123 \
  --resource-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/myapp-alb/1234
```

---

## 12.6 AWS Shield (DDoS Protection)

```bash
# Shield Standard: Free, automatic, protects against common DDoS
# Shield Advanced: $3,000/month, 24/7 DDoS response team

# Check Shield status
aws shield describe-subscription 2>/dev/null || echo "Shield Advanced not enabled"

# List protected resources (Shield Advanced)
aws shield list-protections
```

---

## 12.7 Security Hub & GuardDuty

### Enable GuardDuty (Threat Detection)

```bash
aws guardduty create-detector --enable

# List findings
aws guardduty list-findings \
  --detector-id <detector-id> \
  --finding-criteria '{
    "Criterion": {
      "severity": {"Gte": 7}
    }
  }'
```

### Enable Security Hub

```bash
aws securityhub enable-security-hub \
  --enable-default-standards

# Get security score
aws securityhub get-findings \
  --filters '{"SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}]}' \
  --query 'Findings[0:5].{Title:Title,Severity:Severity.Label,Resource:Resources[0].Id}'
```

---

## 12.8 Security Best Practices Checklist

```
Account Security:
  ✅ Enable MFA on root account
  ✅ Never use root for daily operations
  ✅ Enable CloudTrail in all regions
  ✅ Set up billing alerts
  ✅ Enable GuardDuty

IAM:
  ✅ Use groups, not individual user policies
  ✅ Enforce MFA for console access
  ✅ Rotate access keys every 90 days
  ✅ Use IAM roles for services (not access keys)
  ✅ Review IAM credential report monthly

Network:
  ✅ Use VPCs with private subnets for databases
  ✅ Never open port 22 to 0.0.0.0/0 in production
  ✅ Use Security Groups + NACLs
  ✅ Enable VPC Flow Logs
  ✅ Use VPC endpoints for AWS services

Data:
  ✅ Enable encryption at rest (S3, EBS, RDS)
  ✅ Enable encryption in transit (TLS/SSL)
  ✅ Use KMS for key management
  ✅ Store secrets in Secrets Manager or SSM
  ✅ Enable S3 versioning and MFA delete

Application:
  ✅ Use WAF for web applications
  ✅ Enable Shield for DDoS protection
  ✅ Scan container images (ECR scanning)
  ✅ Use Security Hub for compliance checks
  ✅ Implement least privilege access
```

### Enable VPC Flow Logs

```bash
aws ec2 create-flow-log \
  --resource-type VPC \
  --resource-ids vpc-0abcd1234 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/VPCFlowLogsRole
```

---

## 12.9 Industry Project: Secure Architecture

```bash
#!/bin/bash
# === Security Hardening Script ===

ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

# --- 1. Enable CloudTrail ---
aws s3 mb s3://${ACCOUNT_ID}-cloudtrail-logs
aws cloudtrail create-trail \
  --name security-trail \
  --s3-bucket-name ${ACCOUNT_ID}-cloudtrail-logs \
  --is-multi-region-trail \
  --enable-log-file-validation
aws cloudtrail start-logging --name security-trail

# --- 2. Enable GuardDuty ---
aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES

# --- 3. Enable Config ---
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::${ACCOUNT_ID}:role/ConfigRole \
  --recording-group allSupported=true,includeGlobalResourceTypes=true

# --- 4. Password Policy ---
aws iam update-account-password-policy \
  --minimum-password-length 14 \
  --require-symbols --require-numbers \
  --require-uppercase-characters --require-lowercase-characters \
  --max-password-age 90 --password-reuse-prevention 12

# --- 5. S3 Block Public Access (account level) ---
aws s3control put-public-access-block \
  --account-id $ACCOUNT_ID \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# --- 6. EBS Default Encryption ---
aws ec2 enable-ebs-encryption-by-default

echo "Security hardening complete!"
```

---

## 12.10 Common Errors & Troubleshooting

### Error 1: "AccessDeniedException" on KMS
```bash
# Check key policy
aws kms get-key-policy --key-id $KEY_ID --policy-name default

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/MyRole \
  --action-names kms:Decrypt
```

### Error 2: Secret rotation failing
```bash
# Check Lambda rotation function logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/secret-rotator \
  --filter-pattern "ERROR"

# Test rotation manually
aws secretsmanager rotate-secret --secret-id myapp/database
```

### Error 3: WAF blocking legitimate traffic
```bash
# Check sampled requests
aws wafv2 get-sampled-requests \
  --web-acl-arn <acl-arn> \
  --rule-metric-name CommonRules \
  --scope REGIONAL \
  --time-window StartTime=$(date -d '1 hour ago' +%s),EndTime=$(date +%s) \
  --max-items 10
```

---

## 12.11 AWS CloudHSM

CloudHSM provides dedicated hardware security modules (HSMs) that you manage. Unlike KMS (shared, AWS-managed), CloudHSM gives you full control over encryption keys.

### KMS vs CloudHSM

| Feature | KMS | CloudHSM |
|---------|-----|----------|
| **Management** | AWS manages HSM hardware | You manage HSM, AWS manages hardware |
| **Key access** | AWS can access keys (for managed services) | Only you can access keys |
| **Multi-tenancy** | Shared infrastructure | Dedicated HSM per customer |
| **HA** | Built-in | You must deploy across AZs |
| **Compliance** | FIPS 140-2 Level 3 | FIPS 140-2 Level 3 |
| **Integration** | Native with 100+ AWS services | Custom integration, SSL/TLS offloading |
| **Cost** | Per key + per request | ~$1.50/hr per HSM |

Use CloudHSM when you need full control over keys, regulatory requirements demand dedicated HSMs, or for SSL/TLS offloading.

---

## 12.12 AWS Certificate Manager (ACM)

ACM provisions, manages, and deploys SSL/TLS certificates for AWS services.

### Request a Public Certificate

```bash
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names "*.example.com" \
  --validation-method DNS
```

DNS validation: Add a CNAME record to your domain. Auto-renews.
Email validation: Confirm via email. Must manually renew.

### Integration Points

| Service | How It Uses ACM |
|---------|----------------|
| **ALB** | HTTPS listener with ACM certificate |
| **CloudFront** | Custom SSL certificate (must be in us-east-1) |
| **API Gateway** | Custom domain with TLS |
| **Elastic Beanstalk** | HTTPS on load balancer |

ACM certificates are free. You cannot use ACM certificates on EC2 directly — use them with ALB/CloudFront/API Gateway.

---

## 12.13 Amazon Inspector

Inspector automatically discovers and scans EC2 instances, container images (ECR), and Lambda functions for vulnerabilities.

- Scans for: software vulnerabilities (CVEs), network exposure, unintended network accessibility
- Integrates with Security Hub for centralized findings
- Continuous scanning — re-scans when new CVEs are published or packages are updated

```bash
aws inspector2 enable --resource-types EC2 ECR LAMBDA
```

---

## 12.14 Amazon Macie

Macie uses machine learning to discover, classify, and protect sensitive data in S3.

- Automatically identifies PII (names, credit cards, SSNs), PHI, financial data
- Alerts on publicly accessible buckets containing sensitive data
- Integrates with EventBridge for automated remediation

```bash
aws macie2 enable-macie
aws macie2 create-classification-job \
  --job-type ONE_TIME \
  --s3-job-definition '{"bucketDefinitions": [{"accountId": "123456789012", "buckets": ["my-data-bucket"]}]}'
```

---

## 12.15 AWS Firewall Manager

Centrally manage security rules across all accounts in an AWS Organization.

- Manages: WAF rules, Shield Advanced, Security Groups, Network Firewall, Route 53 Resolver DNS Firewall
- Automatically applies rules to new accounts and resources
- Requires AWS Organizations

### WAF vs Firewall Manager vs Shield

| Service | Purpose | Scope |
|---------|---------|-------|
| **WAF** | Protect individual resources (ALB, CloudFront, API Gateway) with web ACL rules | Per resource |
| **Shield** | DDoS protection (Standard = free, Advanced = $3,000/mo with DRT support) | Per account/resource |
| **Firewall Manager** | Manage WAF/Shield/SG rules across all accounts in an Organization | Organization-wide |

```bash
# WAF: Create a web ACL with rate limiting
aws wafv2 create-web-acl \
  --name "api-protection" \
  --scope REGIONAL \
  --default-action '{"Allow":{}}' \
  --rules '[{
    "Name": "rate-limit",
    "Priority": 1,
    "Action": {"Block": {}},
    "Statement": {
      "RateBasedStatement": {
        "Limit": 2000,
        "AggregateKeyType": "IP"
      }
    },
    "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "rate-limit"}
  }]' \
  --visibility-config '{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"api-protection"}'

# Shield Advanced: Enable on an ALB
aws shield create-protection \
  --name "prod-alb-protection" \
  --resource-arn arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/prod-alb/abcdef

# Firewall Manager: Create a WAF policy for all accounts
aws fms put-policy \
  --policy '{
    "PolicyName": "org-waf-policy",
    "SecurityServicePolicyData": {
      "Type": "WAFV2",
      "ManagedServiceData": "{\"type\":\"WAFV2\",\"preProcessRuleGroups\":[{\"ruleGroupArn\":\"arn:aws:wafv2:us-east-1:123456789012:regional/rulegroup/common-rules/abcdef\",\"overrideAction\":{\"type\":\"NONE\"},\"managedRuleGroupIdentifier\":null,\"ruleGroupType\":\"RuleGroup\",\"excludeRules\":[]}],\"postProcessRuleGroups\":[],\"defaultAction\":{\"type\":\"ALLOW\"}}"
    },
    "ResourceType": "AWS::ElasticLoadBalancingV2::LoadBalancer",
    "ResourceTags": [],
    "ExcludeResourceTags": false,
    "RemediationEnabled": true
  }'
```

**Decision guide:** Use WAF for individual app protection. Add Shield Advanced if you're a high-profile target needing DDoS response team. Use Firewall Manager when you have 5+ accounts and need consistent security rules.

---

## 12.16 DDoS Best Practices

```
Edge Layer:
  - CloudFront (absorbs DDoS at edge, 400+ PoPs)
  - Route 53 (DNS-level protection, health checks)
  - AWS Shield Standard (free, automatic L3/L4 protection)

Infrastructure Layer:
  - AWS Shield Advanced ($3,000/mo, L3/L4/L7 protection, DRT team)
  - Elastic Load Balancing (distributes traffic, scales automatically)
  - Auto Scaling (absorbs traffic spikes)

Application Layer:
  - WAF (rate limiting, IP blocking, SQL injection/XSS protection)
  - WAF rate-based rules (block IPs exceeding threshold)
  - CloudFront + WAF (filter at edge before reaching origin)

Detection:
  - GuardDuty (detect anomalous traffic patterns)
  - CloudWatch (monitor for traffic spikes)
  - Shield Advanced (real-time attack visibility)
```

---

## 12.17 KMS — Advanced Features

### KMS Multi-Region Keys

Same key replicated across multiple regions. Same key ID, same key material. Encrypt in one region, decrypt in another without cross-region API calls. Use cases: global DynamoDB encryption, global Aurora encryption, cross-region S3 replication with encryption.

```bash
# Create a multi-region primary key
aws kms create-key \
  --description "Multi-region key for global encryption" \
  --multi-region \
  --region us-east-1

# Expected output:
# {
#   "KeyMetadata": {
#     "KeyId": "mrk-abcdef1234567890",
#     "MultiRegion": true,
#     "MultiRegionConfiguration": {
#       "MultiRegionKeyType": "PRIMARY",
#       "PrimaryKey": {"Arn": "arn:aws:kms:us-east-1:123456789012:key/mrk-abcdef1234567890", "Region": "us-east-1"},
#       "ReplicaKeys": []
#     }
#   }
# }

# Replicate to another region
aws kms replicate-key \
  --key-id mrk-abcdef1234567890 \
  --replica-region eu-west-1 \
  --region us-east-1

# Encrypt in us-east-1
aws kms encrypt \
  --key-id mrk-abcdef1234567890 \
  --plaintext "sensitive data" \
  --region us-east-1

# Decrypt in eu-west-1 (same key, no cross-region call)
aws kms decrypt \
  --ciphertext-blob fileb://encrypted.bin \
  --region eu-west-1
```

**Real-life use case:** A global application uses DynamoDB Global Tables with client-side encryption. Data encrypted with a multi-region KMS key in us-east-1 can be decrypted locally in eu-west-1 without cross-region KMS API calls, reducing latency.

### SSE-KMS Limitation

KMS has API rate limits (5,500–30,000 requests/second depending on region). High-throughput S3 workloads can be throttled. Solution: enable **S3 Bucket Keys** to reduce KMS API calls by up to 99%.

---

## 12.18 Secrets Manager — Multi-Region Secrets

Replicate secrets across multiple regions. Keeps read replicas in sync with the primary secret. Use cases: multi-region applications, disaster recovery, multi-region databases.

```bash
# Create a secret in the primary region
aws secretsmanager create-secret \
  --name "prod/database/credentials" \
  --secret-string '{"username":"admin","password":"MySecretPass123"}' \
  --region us-east-1

# Replicate to another region
aws secretsmanager replicate-secret-to-regions \
  --secret-id "prod/database/credentials" \
  --add-replica-regions Region=eu-west-1 Region=ap-southeast-1 \
  --region us-east-1

# Expected output:
# {
#   "ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/database/credentials-AbCdEf",
#   "ReplicationStatus": [
#     {"Region": "eu-west-1", "Status": "InSync"},
#     {"Region": "ap-southeast-1", "Status": "InSync"}
#   ]
# }

# Read the secret from the replica region (local read, no cross-region call)
aws secretsmanager get-secret-value \
  --secret-id "prod/database/credentials" \
  --region eu-west-1

# Promote a replica to standalone (for DR)
aws secretsmanager stop-replication-to-replica \
  --secret-id "prod/database/credentials" \
  --region eu-west-1
```

**Real-life use case:** A multi-region application reads database credentials from Secrets Manager. With multi-region secrets, each region reads locally, reducing latency. During a regional failover, the replica is promoted to primary.

---

## 12.19 AWS Directory Services

| Service | Description | Use Case |
|---------|-------------|----------|
| **AWS Managed Microsoft AD** | Full Microsoft AD in AWS, trust with on-prem AD | Enterprise with existing AD |
| **AD Connector** | Proxy to redirect requests to on-prem AD | Keep all data on-prem |
| **Simple AD** | Standalone managed directory (no on-prem integration) | Small/medium, no AD needed |

```bash
# Create an AWS Managed Microsoft AD
aws ds create-microsoft-ad \
  --name corp.example.com \
  --short-name CORP \
  --password "AdminPassword123!" \
  --edition Enterprise \
  --vpc-settings VpcId=vpc-0abcdef1234567890,SubnetIds=subnet-0abcdef1234567890,subnet-0fedcba0987654321

# Expected output:
# {
#   "DirectoryId": "d-0abcdef1234567890"
# }

# Create an AD Connector (proxy to on-prem AD)
aws ds connect-directory \
  --name corp.example.com \
  --short-name CORP \
  --password "ConnectorPassword123!" \
  --size Small \
  --connect-settings '{
    "VpcId": "vpc-0abcdef1234567890",
    "SubnetIds": ["subnet-0abcdef1234567890", "subnet-0fedcba0987654321"],
    "CustomerDnsIps": ["192.168.1.53", "192.168.1.54"],
    "CustomerUserName": "Admin"
  }'

# List directories
aws ds describe-directories \
  --query 'DirectoryDescriptions[].{Id:DirectoryId,Name:Name,Type:Type,Stage:Stage}'

# Expected output:
# [
#   {"Id": "d-0abcdef1234567890", "Name": "corp.example.com", "Type": "MicrosoftAD", "Stage": "Active"}
# ]
```

**Real-life use case:** A company uses AWS Managed Microsoft AD for SSO to AWS Console, RDS SQL Server authentication, and EC2 Windows domain join. AD Connector is used when they want to authenticate against their existing on-premises AD without storing any directory data in AWS.

---

## 12.20 AWS Trusted Advisor

Inspects your AWS account and provides recommendations across 5 categories:

| Category | Examples |
|----------|---------|
| **Cost Optimization** | Idle EC2, underutilized EBS, unused EIPs |
| **Performance** | High-utilization EC2, CloudFront optimization |
| **Security** | Open security groups, MFA on root, IAM key rotation |
| **Fault Tolerance** | Multi-AZ RDS, ELB health checks, S3 versioning |
| **Service Limits** | Approaching service quotas |

Basic plan: 7 core checks free. Business/Enterprise Support: all checks + API access.

---

## 12.21 Key Takeaways

1. Shared Responsibility: AWS secures the cloud; you secure what's IN the cloud
2. Use KMS for encryption key management; enable key rotation
3. Store secrets in Secrets Manager (auto-rotation) or SSM Parameter Store (free)
4. Use WAF to protect web apps from SQL injection, XSS, and DDoS
5. Enable CloudTrail, GuardDuty, and Security Hub for visibility
6. Encrypt everything: at rest (KMS) and in transit (TLS)
7. Block public S3 access at the account level
8. Review security posture monthly using credential reports and Security Hub
9. CloudHSM for dedicated HSMs when you need full key control
10. ACM for free SSL/TLS certificates — use with ALB, CloudFront, API Gateway
11. Inspector for vulnerability scanning (EC2, ECR, Lambda)
12. Macie for discovering sensitive data (PII) in S3
13. Firewall Manager for centralized security rule management across accounts
14. DDoS defense: CloudFront + Shield + WAF + Auto Scaling (layered approach)
