# Module 15: AWS Cloud Security & Architecture — Interview & Scenario Guide

This module covers frequently asked AWS security and architecture scenarios. Each topic includes the concept, when to use it, CLI commands with expected output, and architecture diagrams.

**Topics Covered:**
1. IAM User vs IAM Role
2. IAM Role for S3 Bucket Access from Specific EC2
3. IAM User Security — Tools to Identify Risk
4. GuardDuty
5. High Availability in a 3-Tier Architecture
6. RDS Deployment
7. RDS Fixed Size but Huge Traffic — Cost Optimization
8. Site-to-Site VPN
9. Which Type of Auto Scaling to Use Where
10. AMI Creation (Process & Best Practices)
11. AWS Secret Retrieval in Jenkins Pipeline

---

## 15.1 IAM User vs IAM Role

### What's the Difference?

| Aspect | IAM User | IAM Role |
|--------|----------|----------|
| **Identity** | Represents a person or application | Represents a set of permissions |
| **Credentials** | Permanent (password + access keys) | Temporary (STS tokens, 15 min–12 hrs) |
| **Who uses it** | Humans, CI/CD pipelines | AWS services, cross-account access, federated users |
| **Limit** | 5,000 per account | 1,000 per account (soft limit, can increase) |
| **Best for** | Individual human access | Machine-to-machine, service-to-service |

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        IAM User                               │
│                                                               │
│  Developer (human) ──▶ IAM User "alice"                      │
│                          │                                    │
│                          ├── Password (console login)         │
│                          ├── Access Key + Secret Key (CLI)    │
│                          └── Attached Policies                │
│                                                               │
│  Credentials are PERMANENT until rotated or deleted           │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                        IAM Role                               │
│                                                               │
│  EC2 Instance ──▶ Assumes Role "EC2-S3-Role"                 │
│                          │                                    │
│                          ├── Trust Policy (who can assume)    │
│                          ├── Permission Policy (what allowed) │
│                          └── STS Temporary Credentials        │
│                                                               │
│  Credentials are TEMPORARY and auto-rotated by AWS            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### When to Use Each

**Use IAM User when:**
- A human needs console or CLI access
- You need long-lived credentials for a legacy system that cannot assume roles
- You need to track individual user activity in CloudTrail

**Use IAM Role when:**
- An AWS service (EC2, Lambda, ECS) needs to access other AWS services
- You need cross-account access
- You use federated identity (SSO, SAML, OIDC)
- You want to avoid embedding credentials in code

### Create an IAM User

```bash
# Create user with console access
aws iam create-user --user-name alice

aws iam create-login-profile \
  --user-name alice \
  --password "TempP@ss2024!" \
  --password-reset-required

# Attach a policy
aws iam attach-user-policy \
  --user-name alice \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess
```

**Expected Output (create-user):**
```json
{
    "User": {
        "Path": "/",
        "UserName": "alice",
        "UserId": "AIDAIOSFODNN7EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:user/alice",
        "CreateDate": "2024-06-15T10:00:00+00:00"
    }
}
```

### Create an IAM Role

```bash
# Step 1: Trust policy — defines WHO can assume this role
cat > trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Step 2: Create the role
aws iam create-role \
  --role-name EC2-App-Role \
  --assume-role-policy-document file://trust-policy.json

# Step 3: Attach permission policy — defines WHAT the role can do
aws iam attach-role-policy \
  --role-name EC2-App-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

**Expected Output (create-role):**
```json
{
    "Role": {
        "Path": "/",
        "RoleName": "EC2-App-Role",
        "RoleId": "AROAIOSFODNN7EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:role/EC2-App-Role",
        "CreateDate": "2024-06-15T10:05:00+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ec2.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    }
}
```

### Assume a Role Manually (for testing or cross-account)

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::987654321098:role/CrossAccountRole \
  --role-session-name test-session \
  --duration-seconds 3600
```

**Expected Output:**
```json
{
    "Credentials": {
        "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": "FwoGZXIvYXdzEBYaDH...(long token)...",
        "Expiration": "2024-06-15T11:05:00+00:00"
    },
    "AssumedRoleUser": {
        "AssumedRoleId": "AROAIOSFODNN7EXAMPLE:test-session",
        "Arn": "arn:aws:sts::987654321098:assumed-role/CrossAccountRole/test-session"
    }
}
```

### Common Interview Question

> "Your application on EC2 needs to read from S3. Should you create an IAM user with access keys or an IAM role?"

**Answer:** Always use an IAM Role. Attach the role to the EC2 instance via an instance profile. Reasons:
1. No credentials stored on the instance (no risk of key leakage)
2. Credentials auto-rotate (STS tokens refresh automatically)
3. Follows AWS best practice (principle of least privilege + no long-lived keys)

---

## 15.2 IAM Role for S3 Bucket Access from a Specific EC2 Instance

This is a common production scenario: an application running on EC2 needs to read/write to a specific S3 bucket without embedding credentials.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  EC2 Instance (i-0abc123)                                   │
│  ┌────────────────────────┐                                 │
│  │  Application Code      │                                 │
│  │  (no access keys!)     │                                 │
│  │                        │                                 │
│  │  aws s3 cp file.txt    │──────▶  S3 Bucket               │
│  │    s3://my-app-data/   │        ┌──────────────┐         │
│  └────────┬───────────────┘        │ my-app-data  │         │
│           │                         │              │         │
│           │ Instance Profile        │ Bucket Policy│         │
│           │ (EC2-S3-Role)           │ (optional)   │         │
│           │                         └──────────────┘         │
│           ▼                                                  │
│  ┌────────────────────────┐                                 │
│  │  STS (Security Token   │                                 │
│  │  Service)              │                                 │
│  │                        │                                 │
│  │  Auto-provides temp    │                                 │
│  │  credentials to EC2    │                                 │
│  └────────────────────────┘                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Setup

#### Step 1: Create the IAM Policy (scoped to one bucket)

```bash
cat > s3-specific-bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::my-app-data"
        },
        {
            "Sid": "ReadWriteObjects",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::my-app-data/*"
        }
    ]
}
EOF

POLICY_ARN=$(aws iam create-policy \
  --policy-name EC2-S3-MyAppData-Access \
  --policy-document file://s3-specific-bucket-policy.json \
  --query 'Policy.Arn' --output text)

echo "Policy ARN: $POLICY_ARN"
```

**Expected Output:**
```
Policy ARN: arn:aws:iam::123456789012:policy/EC2-S3-MyAppData-Access
```

**Why two Resource entries?**
- `arn:aws:s3:::my-app-data` — the bucket itself (needed for `ListBucket`)
- `arn:aws:s3:::my-app-data/*` — objects inside the bucket (needed for Get/Put/Delete)

#### Step 2: Create the IAM Role with EC2 Trust Policy

```bash
cat > ec2-trust.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

aws iam create-role \
  --role-name EC2-S3-MyAppData-Role \
  --assume-role-policy-document file://ec2-trust.json

# Attach the scoped policy
aws iam attach-role-policy \
  --role-name EC2-S3-MyAppData-Role \
  --policy-arn $POLICY_ARN
```

#### Step 3: Create Instance Profile and Attach Role

```bash
# Instance profile is the "container" that lets EC2 use the role
aws iam create-instance-profile \
  --instance-profile-name EC2-S3-MyAppData-Profile

aws iam add-role-to-instance-profile \
  --instance-profile-name EC2-S3-MyAppData-Profile \
  --role-name EC2-S3-MyAppData-Role
```

#### Step 4: Launch EC2 with the Instance Profile

```bash
# Launch new instance with the role
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.micro \
  --iam-instance-profile Name=EC2-S3-MyAppData-Profile \
  --key-name my-key \
  --subnet-id subnet-0abc123 \
  --security-group-ids sg-0abc123 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=AppServer}]'
```

#### Step 4b: Attach to an Existing EC2 Instance

```bash
# If the instance is already running
aws ec2 associate-iam-instance-profile \
  --instance-id i-0abc1234567890def \
  --iam-instance-profile Name=EC2-S3-MyAppData-Profile
```

**Expected Output:**
```json
{
    "IamInstanceProfileAssociation": {
        "AssociationId": "iip-assoc-0abc123",
        "InstanceId": "i-0abc1234567890def",
        "IamInstanceProfile": {
            "Arn": "arn:aws:iam::123456789012:instance-profile/EC2-S3-MyAppData-Profile",
            "Id": "AIPAJNKMQE5YKEXAMPLE"
        },
        "State": "associating"
    }
}
```

#### Step 5: Verify from Inside the EC2 Instance

```bash
# SSH into the instance, then:

# Check which role is attached
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
# Output: EC2-S3-MyAppData-Role

# Test S3 access
aws s3 ls s3://my-app-data/
# Output: lists objects in the bucket

aws s3 cp /tmp/test.txt s3://my-app-data/test.txt
# Output: upload: /tmp/test.txt to s3://my-app-data/test.txt

# Try accessing a different bucket (should fail)
aws s3 ls s3://some-other-bucket/
# Output: An error occurred (AccessDenied) when calling the ListObjectsV2 operation: Access Denied
```

### Optional: Add Bucket Policy for Extra Security

Restrict the bucket so only this specific role can access it:

```bash
cat > bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowOnlyEC2Role",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::my-app-data",
                "arn:aws:s3:::my-app-data/*"
            ],
            "Condition": {
                "StringNotEquals": {
                    "aws:PrincipalArn": [
                        "arn:aws:iam::123456789012:role/EC2-S3-MyAppData-Role",
                        "arn:aws:iam::123456789012:root"
                    ]
                }
            }
        }
    ]
}
EOF

aws s3api put-bucket-policy \
  --bucket my-app-data \
  --policy file://bucket-policy.json
```

This denies all access except from the EC2 role and the root account.

---

## 15.3 IAM User Security — Tools to Identify Risk

AWS provides several built-in tools to audit IAM users and find security risks. No third-party tools needed.

### Tool 1: IAM Credential Report

The credential report is a CSV file listing all IAM users and the status of their credentials.

```bash
# Generate the report
aws iam generate-credential-report

# Download the report
aws iam get-credential-report \
  --query 'Content' --output text | base64 --decode > credential-report.csv

# View key columns
cat credential-report.csv | column -t -s',' | head -5
```

**Expected Output (CSV columns):**
```
user              password_enabled  password_last_used    mfa_active  access_key_1_active  access_key_1_last_rotated
root              not_supported     2024-06-10T08:00:00Z  true        false                N/A
alice             true              2024-06-14T12:00:00Z  false       true                 2024-01-15T10:00:00Z
bob               true              2023-11-01T09:00:00Z  false       true                 2023-06-01T08:00:00Z
```

**Red flags to look for:**

| Risk | What to Check | Remediation |
|------|---------------|-------------|
| No MFA | `mfa_active = false` | Enable MFA immediately |
| Stale password | `password_last_used` > 90 days ago | Disable or delete user |
| Old access keys | `access_key_1_last_rotated` > 90 days ago | Rotate keys |
| Unused access keys | `access_key_1_last_used_date = N/A` | Deactivate keys |
| Root access keys | `root` row with `access_key_1_active = true` | Delete root access keys |

### Tool 2: IAM Access Analyzer

Access Analyzer identifies resources shared with external entities (cross-account, public access).

```bash
# Create an analyzer
aws accessanalyzer create-analyzer \
  --analyzer-name account-analyzer \
  --type ACCOUNT

# List findings (resources shared externally)
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/account-analyzer \
  --query 'findings[].{Resource:resource,Type:resourceType,Status:status}' \
  --output table
```

**Expected Output:**
```
-------------------------------------------------------------------
|                          ListFindings                             |
+---------------------------+----------+--------+------------------+
|         Resource          |   Type   | Status |   Principal      |
+---------------------------+----------+--------+------------------+
| arn:aws:s3:::public-bucket| AWS::S3  | ACTIVE | {"AWS": "*"}     |
| arn:aws:iam::123...:role  | AWS::IAM | ACTIVE | {"AWS": "9876.."}|
+---------------------------+----------+--------+------------------+
```

### Tool 3: IAM Access Advisor (Last Accessed Information)

Shows which services a user/role has accessed and when — helps identify over-permissioned entities.

```bash
# Generate service last accessed report
JOB_ID=$(aws iam generate-service-last-accessed-details \
  --arn arn:aws:iam::123456789012:user/alice \
  --query 'JobId' --output text)

# Wait a few seconds, then get results
sleep 5
aws iam get-service-last-accessed-details \
  --job-id $JOB_ID \
  --query 'ServicesLastAccessed[?LastAuthenticated!=`null`].{Service:ServiceName,LastUsed:LastAuthenticated}' \
  --output table
```

**Expected Output:**
```
-------------------------------------------------
|       GetServiceLastAccessedDetails            |
+---------------------+-------------------------+
|       Service       |        LastUsed          |
+---------------------+-------------------------+
|  Amazon S3          |  2024-06-14T11:00:00Z    |
|  Amazon EC2         |  2024-06-10T09:00:00Z    |
|  AWS IAM            |  2024-05-01T08:00:00Z    |
+---------------------+-------------------------+
```

If a user has `AdministratorAccess` but only uses S3 and EC2, scope down their permissions.

### Tool 4: AWS Config Rules for IAM

```bash
# Check for users without MFA
aws configservice put-config-rule --config-rule '{
    "ConfigRuleName": "iam-user-mfa-enabled",
    "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "IAM_USER_MFA_ENABLED"
    }
}'

# Check for unused credentials
aws configservice put-config-rule --config-rule '{
    "ConfigRuleName": "iam-user-unused-credentials-check",
    "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "IAM_USER_UNUSED_CREDENTIALS_CHECK"
    },
    "InputParameters": "{\"maxCredentialUsageAge\": \"90\"}"
}'

# Check compliance
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name iam-user-mfa-enabled \
  --compliance-types NON_COMPLIANT \
  --query 'EvaluationResults[].{Resource:EvaluationResultIdentifier.EvaluationResultQualifier.ResourceId,Status:ComplianceType}'
```

### Tool 5: Quick CLI Audit Script

```bash
#!/bin/bash
# === IAM Security Audit ===

echo "=== Users Without MFA ==="
aws iam generate-credential-report > /dev/null 2>&1
sleep 3
aws iam get-credential-report --query 'Content' --output text | \
  base64 --decode | \
  awk -F',' 'NR>1 && $4=="true" && $8=="false" {print "WARNING: "$1" has password but NO MFA"}'

echo ""
echo "=== Access Keys Older Than 90 Days ==="
for user in $(aws iam list-users --query 'Users[].UserName' --output text); do
  aws iam list-access-keys --user-name "$user" \
    --query "AccessKeyMetadata[?Status=='Active'].{User:UserName,KeyId:AccessKeyId,Created:CreateDate}" \
    --output text | while read line; do
      created=$(echo "$line" | awk '{print $1}')
      age_days=$(( ($(date +%s) - $(date -d "$created" +%s)) / 86400 ))
      if [ "$age_days" -gt 90 ]; then
        echo "WARNING: $user has key older than $age_days days"
      fi
  done
done

echo ""
echo "=== Users With Inline Policies (should use managed policies) ==="
for user in $(aws iam list-users --query 'Users[].UserName' --output text); do
  count=$(aws iam list-user-policies --user-name "$user" --query 'length(PolicyNames)')
  if [ "$count" -gt 0 ]; then
    echo "WARNING: $user has $count inline policies"
  fi
done

echo ""
echo "=== Root Account Access Key Check ==="
aws iam get-credential-report --query 'Content' --output text | \
  base64 --decode | \
  awk -F',' 'NR==2 {
    if ($9=="true") print "CRITICAL: Root has active access key 1!";
    if ($14=="true") print "CRITICAL: Root has active access key 2!";
    if ($9=="false" && $14=="false") print "OK: Root has no access keys"
  }'
```

### Summary: Which Tool for What

| Tool | What It Finds | Frequency |
|------|---------------|-----------|
| Credential Report | Stale passwords, old keys, missing MFA | Monthly |
| Access Analyzer | Public/cross-account resource exposure | Continuous |
| Access Advisor | Over-permissioned users/roles | Quarterly |
| AWS Config | Policy compliance violations | Continuous |
| GuardDuty | Active threats and anomalous behavior | Continuous |

---

## 15.4 GuardDuty

Amazon GuardDuty is a threat detection service that continuously monitors your AWS accounts and workloads for malicious activity.

### How GuardDuty Works

```
┌─────────────────────────────────────────────────────────────┐
│                     GuardDuty Architecture                   │
│                                                              │
│  Data Sources (automatically ingested):                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ CloudTrail   │ │ VPC Flow     │ │ DNS Query        │    │
│  │ Event Logs   │ │ Logs         │ │ Logs             │    │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘    │
│         │                │                   │               │
│         ▼                ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              GuardDuty Detection Engine               │   │
│  │                                                       │   │
│  │  - Machine Learning                                   │   │
│  │  - Anomaly Detection                                  │   │
│  │  - Threat Intelligence Feeds                          │   │
│  │  - Behavioral Analysis                                │   │
│  └──────────────────────┬────────────────────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Findings                           │   │
│  │                                                       │   │
│  │  Severity: Low (1-3) | Medium (4-6) | High (7-8.9)   │   │
│  │                                                       │   │
│  │  ──▶ EventBridge ──▶ SNS (email) / Lambda (auto-fix) │   │
│  │  ──▶ Security Hub (centralized view)                  │   │
│  │  ──▶ S3 (export for analysis)                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Enable GuardDuty

```bash
# Enable GuardDuty
DETECTOR_ID=$(aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --query 'DetectorId' --output text)

echo "Detector ID: $DETECTOR_ID"
```

**Expected Output:**
```
Detector ID: 6ab6e6ee780ed494f3b7ca56acdc74df
```

### Enable Additional Protection Features

```bash
# Enable S3 protection (detect suspicious S3 API calls)
aws guardduty update-detector \
  --detector-id $DETECTOR_ID \
  --data-sources '{"S3Logs":{"Enable":true}}'

# Enable EKS protection
aws guardduty update-detector \
  --detector-id $DETECTOR_ID \
  --data-sources '{"Kubernetes":{"AuditLogs":{"Enable":true}}}'

# Enable Malware protection
aws guardduty update-detector \
  --detector-id $DETECTOR_ID \
  --features '[{"Name":"EBS_MALWARE_PROTECTION","Status":"ENABLED"}]'
```

### List and Analyze Findings

```bash
# List all findings
aws guardduty list-findings \
  --detector-id $DETECTOR_ID \
  --finding-criteria '{
    "Criterion": {
      "severity": {"Gte": 4}
    }
  }' \
  --sort-criteria '{"AttributeName":"severity","OrderBy":"DESC"}' \
  --query 'FindingIds'
```

**Expected Output:**
```json
[
    "3ab6e6ee780ed494f3b7ca56acdc74df",
    "8cd6e6ee780ed494f3b7ca56acdc99ab"
]
```

```bash
# Get finding details
aws guardduty get-findings \
  --detector-id $DETECTOR_ID \
  --finding-ids '["3ab6e6ee780ed494f3b7ca56acdc74df"]' \
  --query 'Findings[0].{Type:Type,Severity:Severity,Title:Title,Description:Description}'
```

**Expected Output:**
```json
{
    "Type": "UnauthorizedAccess:IAMUser/ConsoleLoginSuccess.B",
    "Severity": 8,
    "Title": "API ConsoleLogin was invoked from an unusual IP address.",
    "Description": "An API was used to access an AWS account from an IP address that is not typically used."
}
```

### Common GuardDuty Finding Types

| Finding Type | Severity | What It Means |
|-------------|----------|---------------|
| `Recon:EC2/PortProbeUnprotectedPort` | Low | Someone is scanning your EC2 ports |
| `UnauthorizedAccess:EC2/SSHBruteForce` | Medium | SSH brute force attack on EC2 |
| `UnauthorizedAccess:IAMUser/ConsoleLoginSuccess.B` | High | Console login from unusual IP |
| `CryptoCurrency:EC2/BitcoinTool.B` | High | EC2 instance mining cryptocurrency |
| `Trojan:EC2/BlackholeTraffic` | High | EC2 communicating with known malicious IP |
| `Exfiltration:S3/MaliciousIPCaller` | High | S3 data accessed from malicious IP |
| `Impact:EC2/PortSweep` | Medium | EC2 probing ports on other hosts |

### Automate Response with EventBridge + Lambda

```bash
# Create EventBridge rule to trigger on high-severity findings
aws events put-rule \
  --name guardduty-high-severity \
  --event-pattern '{
    "source": ["aws.guardduty"],
    "detail-type": ["GuardDuty Finding"],
    "detail": {
      "severity": [{"numeric": [">=", 7]}]
    }
  }'

# Add SNS target for email alerts
aws events put-targets \
  --rule guardduty-high-severity \
  --targets '[{
    "Id": "sns-alert",
    "Arn": "arn:aws:sns:us-east-1:123456789012:security-alerts"
  }]'
```

### Auto-Remediation Example: Block Compromised EC2

```python
# Lambda function triggered by GuardDuty via EventBridge
import boto3

def lambda_handler(event, context):
    finding = event['detail']
    finding_type = finding['type']

    # If EC2 is compromised, isolate it
    if 'EC2' in finding_type and finding['severity'] >= 7:
        instance_id = finding['resource']['instanceDetails']['instanceId']
        ec2 = boto3.client('ec2')

        # Create isolation security group (no inbound/outbound)
        vpc_id = finding['resource']['instanceDetails']['networkInterfaces'][0]['vpcId']

        sg = ec2.create_security_group(
            GroupName=f'isolate-{instance_id}',
            Description='Isolation SG - no traffic allowed',
            VpcId=vpc_id
        )

        # Remove all egress rules
        ec2.revoke_security_group_egress(
            GroupId=sg['GroupId'],
            IpPermissions=[{'IpProtocol': '-1', 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}]
        )

        # Apply isolation SG to instance
        ec2.modify_instance_attribute(
            InstanceId=instance_id,
            Groups=[sg['GroupId']]
        )

        print(f"Isolated instance {instance_id} due to finding: {finding_type}")

    # If IAM credentials are compromised, disable access keys
    if 'IAMUser' in finding_type and finding['severity'] >= 7:
        iam = boto3.client('iam')
        username = finding['resource']['accessKeyDetails']['userName']
        access_key_id = finding['resource']['accessKeyDetails']['accessKeyId']

        iam.update_access_key(
            UserName=username,
            AccessKeyId=access_key_id,
            Status='Inactive'
        )

        print(f"Disabled access key {access_key_id} for user {username}")
```

### Multi-Account GuardDuty (Organizations)

```bash
# Designate a delegated administrator
aws guardduty enable-organization-admin-account \
  --admin-account-id 111111111111

# From the admin account: auto-enable for all member accounts
aws guardduty update-organization-configuration \
  --detector-id $DETECTOR_ID \
  --auto-enable
```

### GuardDuty Costs

| Data Source | Pricing |
|------------|---------|
| CloudTrail Management Events | Free (first 30 days), then per million events |
| VPC Flow Logs | Per GB analyzed |
| DNS Logs | Per million queries |
| S3 Data Events | Per million events |
| EKS Audit Logs | Per million events |

Typical cost: $1-5/month for small accounts, $50-500/month for large accounts.

### Common Interview Questions

> "How does GuardDuty differ from AWS Config?"

**GuardDuty** detects active threats (someone is attacking you right now). **AWS Config** checks compliance (is your S3 bucket public?). GuardDuty is reactive threat detection; Config is proactive compliance checking.

> "Can GuardDuty automatically remediate threats?"

Not directly. GuardDuty generates findings. You use EventBridge + Lambda to automate remediation (isolate EC2, disable keys, etc.).

---

## 15.5 High Availability in a 3-Tier AWS Architecture

A 3-tier architecture separates Presentation (web), Application (logic), and Data (database) tiers. HA means no single point of failure at any tier.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
│                            │                                     │
│                       ┌────▼────┐                                │
│                       │Route 53 │  DNS with health checks        │
│                       │(Global) │  Failover routing policy       │
│                       └────┬────┘                                │
│                            │                                     │
│              ┌─────────────▼──────────────┐                      │
│              │     CloudFront (CDN)        │  Edge caching        │
│              │     (Global - 400+ PoPs)    │                      │
│              └─────────────┬──────────────┘                      │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────┐           │
│  │              VPC (10.0.0.0/16)                     │           │
│  │                                                    │           │
│  │  TIER 1: PRESENTATION (Public Subnets)             │           │
│  │  ┌─────────────────────────────────────────────┐  │           │
│  │  │        Application Load Balancer (ALB)       │  │           │
│  │  │        (Cross-zone load balancing)           │  │           │
│  │  └──────────┬──────────────────┬───────────────┘  │           │
│  │             │                  │                    │           │
│  │  ┌──────────▼──────┐ ┌────────▼────────┐          │           │
│  │  │  NAT Gateway    │ │  NAT Gateway    │          │           │
│  │  │  (AZ-a)         │ │  (AZ-b)         │          │           │
│  │  │  10.0.1.0/24    │ │  10.0.2.0/24    │          │           │
│  │  └─────────────────┘ └─────────────────┘          │           │
│  │                                                    │           │
│  │  TIER 2: APPLICATION (Private Subnets)             │           │
│  │  ┌─────────────────┐ ┌─────────────────┐          │           │
│  │  │  Auto Scaling   │ │  Auto Scaling   │          │           │
│  │  │  Group          │ │  Group          │          │           │
│  │  │  EC2 (AZ-a)     │ │  EC2 (AZ-b)     │          │           │
│  │  │  10.0.3.0/24    │ │  10.0.4.0/24    │          │           │
│  │  │  Min:2 Max:10   │ │  Min:2 Max:10   │          │           │
│  │  └────────┬────────┘ └────────┬────────┘          │           │
│  │           │                    │                    │           │
│  │  TIER 3: DATA (Private Subnets - Isolated)         │           │
│  │  ┌─────────────────┐ ┌─────────────────┐          │           │
│  │  │  RDS Primary    │ │  RDS Standby    │          │           │
│  │  │  (AZ-a)         │◀▶│  (AZ-b)         │  Multi-AZ│           │
│  │  │  10.0.5.0/24    │ │  10.0.6.0/24    │          │           │
│  │  └─────────────────┘ └─────────────────┘          │           │
│  │                                                    │           │
│  │  ┌─────────────────┐ ┌─────────────────┐          │           │
│  │  │  ElastiCache    │ │  ElastiCache    │          │           │
│  │  │  Primary (AZ-a) │◀▶│  Replica (AZ-b) │          │           │
│  │  └─────────────────┘ └─────────────────┘          │           │
│  │                                                    │           │
│  └────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### HA at Each Tier

| Tier | Component | HA Strategy |
|------|-----------|-------------|
| **DNS** | Route 53 | Health checks + failover routing, 100% SLA |
| **CDN** | CloudFront | 400+ edge locations, automatic failover |
| **Load Balancer** | ALB | Multi-AZ by default, cross-zone balancing |
| **Web/App** | EC2 + ASG | Auto Scaling across 2+ AZs, min 2 instances |
| **Database** | RDS Multi-AZ | Synchronous standby, automatic failover (~60s) |
| **Cache** | ElastiCache | Multi-AZ with automatic failover |
| **NAT** | NAT Gateway | One per AZ (each AZ has its own) |

### Step-by-Step: Build HA 3-Tier Architecture

#### Step 1: VPC with Multi-AZ Subnets

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ha-3tier-vpc}]' \
  --query 'Vpc.VpcId' --output text)

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'

# Create subnets across 2 AZs
# Public subnets (ALB + NAT)
PUB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-a}]' \
  --query 'Subnet.SubnetId' --output text)

PUB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-b}]' \
  --query 'Subnet.SubnetId' --output text)

# Private subnets (App tier)
APP_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 \
  --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=app-a}]' \
  --query 'Subnet.SubnetId' --output text)

APP_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.4.0/24 \
  --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=app-b}]' \
  --query 'Subnet.SubnetId' --output text)

# Private subnets (Data tier)
DB_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.5.0/24 \
  --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=db-a}]' \
  --query 'Subnet.SubnetId' --output text)

DB_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.6.0/24 \
  --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=db-b}]' \
  --query 'Subnet.SubnetId' --output text)
```

#### Step 2: Internet Gateway + NAT Gateways (one per AZ)

```bash
# Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# Elastic IPs for NAT Gateways
EIP_A=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP_B=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

# NAT Gateway in each AZ (HA — if AZ-a NAT fails, AZ-b still works)
NAT_A=$(aws ec2 create-nat-gateway --subnet-id $PUB_A --allocation-id $EIP_A \
  --query 'NatGateway.NatGatewayId' --output text)
NAT_B=$(aws ec2 create-nat-gateway --subnet-id $PUB_B --allocation-id $EIP_B \
  --query 'NatGateway.NatGatewayId' --output text)
```

#### Step 3: ALB (Application Load Balancer)

```bash
# Create ALB spanning both AZs
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ha-3tier-alb \
  --subnets $PUB_A $PUB_B \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name app-targets \
  --protocol HTTP --port 80 \
  --vpc-id $VPC_ID \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

#### Step 4: Auto Scaling Group (App Tier)

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name ha-app-template \
  --launch-template-data '{
    "ImageId": "ami-0abcdef1234567890",
    "InstanceType": "t3.medium",
    "IamInstanceProfile": {"Name": "EC2-App-Profile"},
    "SecurityGroupIds": ["'$APP_SG'"],
    "UserData": "'$(base64 <<< '#!/bin/bash
yum install -y httpd
systemctl start httpd
echo "Healthy" > /var/www/html/health')'"
  }'

# Create ASG across both AZs
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name ha-app-asg \
  --launch-template LaunchTemplateName=ha-app-template,Version='$Latest' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 4 \
  --vpc-zone-identifier "$APP_A,$APP_B" \
  --target-group-arns $TG_ARN \
  --health-check-type ELB \
  --health-check-grace-period 300
```

#### Step 5: RDS Multi-AZ (Data Tier)

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name ha-db-subnets \
  --db-subnet-group-description "HA database subnets" \
  --subnet-ids $DB_A $DB_B

# Create Multi-AZ RDS
aws rds create-db-instance \
  --db-instance-identifier ha-app-db \
  --db-instance-class db.r6g.large \
  --engine mysql \
  --master-username admin \
  --master-user-password "$(aws secretsmanager get-random-password --password-length 32 --query 'RandomPassword' --output text)" \
  --allocated-storage 100 \
  --multi-az \
  --storage-encrypted \
  --db-subnet-group-name ha-db-subnets \
  --vpc-security-group-ids $DB_SG \
  --backup-retention-period 7 \
  --storage-type gp3
```

### What Happens During Failures?

| Failure | What Happens | Downtime |
|---------|-------------|----------|
| Single EC2 dies | ASG launches replacement, ALB routes around it | 0 (other instances serve) |
| Entire AZ goes down | ALB routes to other AZ, ASG launches in healthy AZ | 0 (cross-AZ) |
| RDS primary fails | Automatic failover to standby in other AZ | ~60 seconds |
| NAT Gateway fails | Only affects that AZ's outbound traffic | 0 (other AZ unaffected) |
| ALB node fails | ALB is inherently multi-AZ | 0 |

### Common Interview Question

> "How do you achieve HA in a 3-tier architecture?"

**Answer:** Deploy across at least 2 Availability Zones. Use ALB for load distribution, Auto Scaling Groups for the app tier (min 2 instances), RDS Multi-AZ for the database, and NAT Gateways in each AZ. No single component should be a single point of failure.

---

## 15.6 RDS Deployment

### RDS Deployment Options

```
┌─────────────────────────────────────────────────────────────┐
│                   RDS Deployment Options                     │
│                                                              │
│  1. Single-AZ          2. Multi-AZ           3. Read Replica │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐   │
│  │ Primary  │          │ Primary  │          │ Primary  │   │
│  │ (AZ-a)   │          │ (AZ-a)   │          │ (AZ-a)   │   │
│  └──────────┘          └────┬─────┘          └────┬─────┘   │
│                              │ Sync                │ Async   │
│  No standby              ┌──▼──────┐          ┌───▼─────┐   │
│  No failover             │ Standby │          │ Replica │   │
│  Dev/test only           │ (AZ-b)  │          │ (AZ-b)  │   │
│                          └─────────┘          └─────────┘   │
│                          Auto failover        Read traffic   │
│                          ~60 seconds          Can promote    │
│                                                              │
│  4. Aurora Multi-AZ      5. Aurora Global                    │
│  ┌──────────┐            ┌──────────┐                        │
│  │ Writer   │            │ Writer   │ Region 1               │
│  │ (AZ-a)   │            │ (us-east)│                        │
│  └────┬─────┘            └────┬─────┘                        │
│       │ Sync                  │ Async (<1s)                  │
│  ┌────▼─────┐ ┌──────────┐  ┌▼─────────┐                    │
│  │ Reader   │ │ Reader   │  │ Reader   │ Region 2            │
│  │ (AZ-b)   │ │ (AZ-c)   │  │ (eu-west)│                    │
│  └──────────┘ └──────────┘  └──────────┘                     │
│  Up to 15 readers         Cross-region DR                    │
│  Failover <30s            RPO <1s, RTO <1min                 │
└─────────────────────────────────────────────────────────────┘
```

### Deploy Single-AZ RDS (Dev/Test)

```bash
aws rds create-db-instance \
  --db-instance-identifier dev-mysql \
  --db-instance-class db.t3.micro \
  --engine mysql \
  --engine-version 8.0 \
  --master-username admin \
  --master-user-password "DevP@ss2024!" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --no-multi-az \
  --db-subnet-group-name my-db-subnets \
  --vpc-security-group-ids sg-db123 \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

### Deploy Multi-AZ RDS (Production)

```bash
aws rds create-db-instance \
  --db-instance-identifier prod-mysql \
  --db-instance-class db.r6g.large \
  --engine mysql \
  --engine-version 8.0 \
  --master-username admin \
  --master-user-password "$(aws secretsmanager get-random-password --password-length 32 --query 'RandomPassword' --output text)" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --iops 3000 \
  --multi-az \
  --storage-encrypted \
  --kms-key-id alias/rds-key \
  --db-subnet-group-name prod-db-subnets \
  --vpc-security-group-ids sg-proddb \
  --backup-retention-period 35 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:05:00-sun:06:00" \
  --enable-performance-insights \
  --monitoring-interval 60 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role \
  --deletion-protection \
  --copy-tags-to-snapshot \
  --no-publicly-accessible
```

**Expected Output:**
```json
{
    "DBInstance": {
        "DBInstanceIdentifier": "prod-mysql",
        "DBInstanceClass": "db.r6g.large",
        "Engine": "mysql",
        "DBInstanceStatus": "creating",
        "MultiAZ": true,
        "StorageEncrypted": true,
        "Endpoint": {
            "Address": "prod-mysql.c9abc123.us-east-1.rds.amazonaws.com",
            "Port": 3306
        }
    }
}
```

### Create Read Replica

```bash
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-mysql-replica \
  --source-db-instance-identifier prod-mysql \
  --db-instance-class db.r6g.large \
  --availability-zone us-east-1b \
  --no-publicly-accessible
```

### Deploy Aurora Cluster

```bash
# Create Aurora cluster
aws rds create-db-cluster \
  --db-cluster-identifier prod-aurora \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password "$(aws secretsmanager get-random-password --password-length 32 --query 'RandomPassword' --output text)" \
  --db-subnet-group-name prod-db-subnets \
  --vpc-security-group-ids sg-proddb \
  --storage-encrypted \
  --backup-retention-period 35 \
  --deletion-protection

# Create writer instance
aws rds create-db-instance \
  --db-instance-identifier prod-aurora-writer \
  --db-cluster-identifier prod-aurora \
  --db-instance-class db.r6g.large \
  --engine aurora-mysql

# Create reader instance (different AZ)
aws rds create-db-instance \
  --db-instance-identifier prod-aurora-reader \
  --db-cluster-identifier prod-aurora \
  --db-instance-class db.r6g.large \
  --engine aurora-mysql \
  --availability-zone us-east-1b
```

### RDS Security Checklist

```
Network:
  - Deploy in private subnets (no public access)
  - Security group: allow port 3306/5432 only from app tier SG
  - Use VPC endpoints for management API calls

Encryption:
  - Enable encryption at rest (KMS)
  - Enable SSL/TLS for connections (in-transit)
  - Store credentials in Secrets Manager

Access:
  - Use IAM database authentication where possible
  - Create application-specific DB users (not master)
  - Enable audit logging

Backup:
  - Automated backups: 35-day retention
  - Manual snapshots before major changes
  - Test restore process quarterly
```

### Connect to RDS from Application

```bash
# From EC2 in the same VPC
mysql -h prod-mysql.c9abc123.us-east-1.rds.amazonaws.com \
  -u admin -p \
  --ssl-ca=/tmp/rds-combined-ca-bundle.pem

# Verify SSL connection
mysql> SHOW STATUS LIKE 'Ssl_cipher';
# Output: TLS_AES_256_GCM_SHA384
```

---

## 15.7 RDS Fixed Size but Huge Traffic — Cost Optimization

**Scenario:** Your RDS instance has a fixed storage size (say 100 GB) but receives massive read/write traffic. The database is expensive because you're scaling up the instance class to handle load. How do you optimize costs?

### The Problem

```
┌─────────────────────────────────────────────────────────┐
│                    BEFORE (Expensive)                     │
│                                                          │
│  All traffic ──▶ db.r6g.4xlarge ($$$$)                  │
│                  ┌──────────────────┐                    │
│  Reads: 80%  ──▶ │   RDS Primary    │                    │
│  Writes: 20% ──▶ │   100 GB, 16 vCPU│                    │
│                  │   128 GB RAM      │                    │
│                  └──────────────────┘                    │
│                                                          │
│  Cost: ~$2,400/month                                     │
└─────────────────────────────────────────────────────────┘
```

### Solution Strategy

```
┌─────────────────────────────────────────────────────────┐
│                    AFTER (Optimized)                      │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              ElastiCache (Redis)                  │   │
│  │              cache.r6g.large                      │   │
│  │              Hot data cache (TTL: 5-60 min)       │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ Cache hit: 70-90% of reads        │
│                     │                                    │
│  App ──▶ Cache? ──Yes──▶ Return cached data             │
│              │                                           │
│              No (cache miss)                             │
│              │                                           │
│              ▼                                           │
│  ┌──────────────────┐    ┌──────────────────┐           │
│  │  RDS Primary     │    │  RDS Read Replica │           │
│  │  db.r6g.large    │    │  db.r6g.large     │           │
│  │  (writes only)   │    │  (remaining reads) │           │
│  │  100 GB          │    │  100 GB            │           │
│  └──────────────────┘    └──────────────────┘           │
│                                                          │
│  Cost: ~$800/month (67% savings)                         │
└─────────────────────────────────────────────────────────┘
```

### Optimization Techniques (Ranked by Impact)

#### 1. Add ElastiCache (Redis) for Read Caching

```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id app-cache \
  --replication-group-description "App read cache" \
  --engine redis \
  --cache-node-type cache.r6g.large \
  --num-cache-clusters 2 \
  --cache-subnet-group-name app-cache-subnets \
  --security-group-ids sg-cache123

# Application caching pattern (Python)
```

```python
import redis
import json
import mysql.connector

cache = redis.Redis(host='app-cache.abc123.use1.cache.amazonaws.com', port=6379)

def get_product(product_id):
    # Try cache first
    cached = cache.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)  # Cache HIT — no DB query

    # Cache MISS — query DB
    db = mysql.connector.connect(host='prod-mysql.rds.amazonaws.com', ...)
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    # Store in cache for 5 minutes
    cache.setex(f"product:{product_id}", 300, json.dumps(product))
    return product
```

#### 2. Add Read Replicas for Remaining Read Traffic

```bash
# Create read replica (handles reads that miss cache)
aws rds create-db-instance-read-replica \
  --db-instance-identifier prod-mysql-replica-1 \
  --source-db-instance-identifier prod-mysql \
  --db-instance-class db.r6g.large
```

#### 3. Downsize the Primary Instance

With cache + read replicas handling 90%+ of reads, the primary only handles writes:

```bash
# Downsize primary (schedule during maintenance window)
aws rds modify-db-instance \
  --db-instance-identifier prod-mysql \
  --db-instance-class db.r6g.large \
  --apply-immediately
```

#### 4. Use Reserved Instances for Predictable Workloads

```bash
# Check current on-demand pricing
aws rds describe-reserved-db-instances-offerings \
  --db-instance-class db.r6g.large \
  --duration 31536000 \
  --product-description mysql \
  --offering-type "All Upfront" \
  --query 'ReservedDBInstancesOfferings[0].{Price:FixedPrice,Savings:RecurringCharges}'
```

**Savings comparison:**

| Payment Option | 1-Year Savings | 3-Year Savings |
|---------------|---------------|---------------|
| No Upfront | ~25% | ~40% |
| Partial Upfront | ~35% | ~50% |
| All Upfront | ~40% | ~55% |

#### 5. Enable Aurora Serverless v2 (if applicable)

For unpredictable traffic patterns, Aurora Serverless scales automatically:

```bash
aws rds create-db-cluster \
  --db-cluster-identifier prod-aurora-serverless \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=16 \
  --master-username admin \
  --master-user-password "SecurePass123!"
```

### Cost Comparison

| Configuration | Monthly Cost (approx) |
|--------------|----------------------|
| Single db.r6g.4xlarge | $2,400 |
| db.r6g.large + 1 Read Replica + ElastiCache | $800 |
| Aurora Serverless v2 (avg 4 ACU) + ElastiCache | $600 |
| db.r6g.large (Reserved 1yr) + ElastiCache | $550 |

### Common Interview Question

> "Your RDS is 100 GB but getting crushed by traffic. You can't change the data size. How do you optimize?"

**Answer:** The bottleneck is compute/IOPS, not storage. Add ElastiCache (Redis) to offload 70-90% of reads. Add read replicas for remaining read traffic. Downsize the primary to handle writes only. Use Reserved Instances for the base load. Consider Aurora Serverless v2 if traffic is spiky.

---

## 15.8 Site-to-Site VPN

AWS Site-to-Site VPN connects your on-premises network to your AWS VPC over an encrypted IPsec tunnel through the public internet.

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  On-Premises Data Center              AWS Cloud                   │
│  ┌─────────────────────┐              ┌─────────────────────┐    │
│  │                     │              │      VPC             │    │
│  │  Servers            │              │   10.0.0.0/16        │    │
│  │  10.1.0.0/16        │              │                      │    │
│  │                     │              │  ┌────────────────┐  │    │
│  │  ┌───────────────┐  │   IPsec      │  │ Private Subnet │  │    │
│  │  │ Customer      │  │   Tunnel     │  │ EC2, RDS, etc  │  │    │
│  │  │ Gateway       │◀═╪═══════════╪═▶│  └────────────────┘  │    │
│  │  │ (your router) │  │   Tunnel 1  │  │                      │    │
│  │  │ Public IP:    │◀═╪═══════════╪═▶│  ┌────────────────┐  │    │
│  │  │ 203.0.113.1   │  │   Tunnel 2  │  │ Virtual Private │  │    │
│  │  └───────────────┘  │  (redundant) │  │ Gateway (VGW)   │  │    │
│  │                     │              │  │ or Transit GW   │  │    │
│  └─────────────────────┘              │  └────────────────┘  │    │
│                                       └─────────────────────┘    │
│                                                                   │
│  Each VPN connection has 2 tunnels for redundancy                │
│  Encrypted with IPsec (AES-256)                                  │
│  Bandwidth: up to 1.25 Gbps per tunnel                           │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | What It Is | Where |
|-----------|-----------|-------|
| **Customer Gateway (CGW)** | Represents your on-prem router in AWS | AWS config pointing to your router |
| **Virtual Private Gateway (VGW)** | VPN endpoint on the AWS side | Attached to your VPC |
| **Transit Gateway (TGW)** | Hub for multiple VPCs and VPN connections | Alternative to VGW for complex setups |
| **VPN Connection** | The actual IPsec tunnel configuration | Links CGW to VGW/TGW |

### Step-by-Step Setup

#### Step 1: Create Customer Gateway

```bash
# Your on-prem router's public IP
CGW_ID=$(aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65000 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=office-router}]' \
  --query 'CustomerGateway.CustomerGatewayId' --output text)

echo "Customer Gateway: $CGW_ID"
```

**Expected Output:**
```
Customer Gateway: cgw-0abc1234567890def
```

**Command Breakdown:**
- `--type ipsec.1` — IPsec VPN (only option)
- `--public-ip` — Your on-prem router's public IP address
- `--bgp-asn 65000` — Your BGP Autonomous System Number (use 65000 if you don't have one)

#### Step 2: Create Virtual Private Gateway

```bash
VGW_ID=$(aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512 \
  --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=aws-vpn-gw}]' \
  --query 'VpnGateway.VpnGatewayId' --output text)

# Attach to VPC
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id $VGW_ID \
  --vpc-id $VPC_ID

echo "VPN Gateway: $VGW_ID"
```

#### Step 3: Create VPN Connection

```bash
VPN_ID=$(aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id $CGW_ID \
  --vpn-gateway-id $VGW_ID \
  --options '{"StaticRoutesOnly":false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=office-to-aws}]' \
  --query 'VpnConnection.VpnConnectionId' --output text)

echo "VPN Connection: $VPN_ID"
```

**Expected Output:**
```
VPN Connection: vpn-0abc1234567890def
```

#### Step 4: Download Configuration for Your Router

```bash
# Download config for your specific router model
aws ec2 describe-vpn-connections \
  --vpn-connection-ids $VPN_ID \
  --query 'VpnConnections[0].CustomerGatewayConfiguration' \
  --output text > vpn-config.xml

# This XML contains:
# - Pre-shared keys for both tunnels
# - AWS tunnel endpoint IPs
# - BGP configuration
# - IPsec parameters (encryption, hashing, DH groups)
```

#### OpenSwan/Libreswan IPsec Configuration (Linux-based Customer Gateway)

If your on-premises router is a Linux server, use OpenSwan or Libreswan:

```bash
# Install Libreswan (successor to OpenSwan)
sudo yum install libreswan -y   # Amazon Linux / RHEL
# or
sudo apt-get install libreswan -y  # Ubuntu/Debian

# Enable IP forwarding
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.default.rp_filter = 0" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.default.accept_source_route = 0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Create IPsec tunnel configuration
sudo cat > /etc/ipsec.d/aws-vpn-tunnel1.conf << 'EOF'
conn aws-vpn-tunnel1
    type=tunnel
    authby=secret
    left=%defaultroute
    leftid=203.0.113.10          # Your public IP
    right=52.10.1.100            # AWS tunnel endpoint IP
    leftsubnet=10.1.0.0/16       # Your on-prem CIDR
    rightsubnet=10.0.0.0/16      # AWS VPC CIDR
    auto=start
    ike=aes256-sha256;modp2048
    phase2alg=aes256-sha256;modp2048
    ikelifetime=8h
    salifetime=1h
    dpddelay=10
    dpdtimeout=30
    dpdaction=restart_by_peer
EOF

# Create pre-shared key file
sudo cat > /etc/ipsec.d/aws-vpn-tunnel1.secrets << 'EOF'
203.0.113.10 52.10.1.100 : PSK "YourPreSharedKeyFromAWSConfig"
EOF

# Start IPsec
sudo systemctl enable ipsec
sudo systemctl start ipsec

# Verify tunnel status
sudo ipsec status
# Expected output:
# 000 "aws-vpn-tunnel1": STATE_V2_ESTABLISHED_IKE_SA
# 000 "aws-vpn-tunnel1": STATE_V2_ESTABLISHED_CHILD_SA

# Check tunnel traffic
sudo ipsec trafficstatus
# 006 "aws-vpn-tunnel1", type=ESP, add_time=1705312800, inBytes=1234, outBytes=5678
```

#### Step 5: Enable Route Propagation

```bash
# Get route table ID for private subnets
RT_ID=$(aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Name,Values=private-rt" \
  --query 'RouteTables[0].RouteTableId' --output text)

# Enable VGW route propagation
aws ec2 enable-vgw-route-propagation \
  --gateway-id $VGW_ID \
  --route-table-id $RT_ID
```

This automatically adds routes for your on-prem network (10.1.0.0/16) to the VPC route table.

#### Step 6: Verify VPN Status

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids $VPN_ID \
  --query 'VpnConnections[0].VgwTelemetry[].{Tunnel:OutsideIpAddress,Status:Status,StatusMessage:StatusMessage}' \
  --output table
```

**Expected Output (both tunnels UP):**
```
------------------------------------------------------
|              DescribeVpnConnections                  |
+------------------+--------+-------------------------+
|      Tunnel      | Status |     StatusMessage        |
+------------------+--------+-------------------------+
|  52.10.1.100     |  UP    |  2 BGP ROUTES            |
|  52.10.2.200     |  UP    |  2 BGP ROUTES            |
+------------------+--------+-------------------------+
```

### VPN vs Direct Connect

| Feature | Site-to-Site VPN | Direct Connect |
|---------|-----------------|----------------|
| **Connection** | Over public internet | Dedicated fiber |
| **Bandwidth** | Up to 1.25 Gbps/tunnel | 1 Gbps, 10 Gbps, 100 Gbps |
| **Latency** | Variable (internet) | Consistent, low |
| **Setup time** | Minutes | Weeks to months |
| **Cost** | ~$36/month + data transfer | $0.30/hr + data transfer |
| **Encryption** | IPsec (built-in) | Not encrypted (add VPN over DX) |
| **Redundancy** | 2 tunnels per connection | Need 2 connections for HA |
| **Best for** | Quick setup, backup, low bandwidth | High bandwidth, consistent latency |

### Common Interview Question

> "How do you connect your on-premises data center to AWS?"

**Answer:** Two main options:
1. **Site-to-Site VPN** — Quick to set up (minutes), encrypted IPsec over the internet, up to 1.25 Gbps per tunnel. Use for immediate connectivity or as a backup.
2. **Direct Connect** — Dedicated physical connection, consistent low latency, up to 100 Gbps. Use for high-bandwidth, latency-sensitive workloads.
3. **Both together** — Direct Connect as primary, VPN as failover. This is the recommended HA pattern.

---

## 15.9 Which Type of Auto Scaling to Use Where

AWS offers multiple Auto Scaling services. Each is designed for different resources and use cases.

### Auto Scaling Types Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  AWS Auto Scaling Services                    │
│                                                              │
│  1. EC2 Auto Scaling (ASG)                                  │
│     └── Scales EC2 instances in/out                         │
│     └── Most common, most configurable                      │
│                                                              │
│  2. Application Auto Scaling                                │
│     └── ECS tasks, DynamoDB, Aurora replicas,               │
│         Lambda concurrency, SageMaker, etc.                 │
│                                                              │
│  3. AWS Auto Scaling (Predictive)                           │
│     └── Uses ML to predict traffic patterns                 │
│     └── Pre-scales before demand hits                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### EC2 Auto Scaling — Scaling Policies

| Policy Type | How It Works | Best For |
|------------|-------------|----------|
| **Target Tracking** | Maintain a metric at a target value (e.g., CPU at 50%) | Most workloads (simplest) |
| **Step Scaling** | Add/remove instances based on alarm thresholds | Variable scaling needs |
| **Simple Scaling** | Add/remove fixed number on alarm | Legacy, avoid for new setups |
| **Scheduled Scaling** | Scale at specific times | Predictable traffic patterns |
| **Predictive Scaling** | ML-based, pre-scales before demand | Recurring traffic patterns |

### Target Tracking (Recommended Default)

```bash
# Scale to maintain average CPU at 50%
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-app-asg \
  --policy-name cpu-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 50.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

**When to use:** Default choice for most workloads. AWS handles the math — you just set the target.

**Available predefined metrics:**
- `ASGAverageCPUUtilization` — CPU usage
- `ASGAverageNetworkIn` — Network bytes in
- `ASGAverageNetworkOut` — Network bytes out
- `ALBRequestCountPerTarget` — Requests per instance (best for web apps)

### Target Tracking on ALB Request Count

```bash
# Scale based on requests per target (best for web servers)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-app-asg \
  --policy-name request-count-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ALBRequestCountPerTarget",
      "ResourceLabel": "app/my-alb/1234/targetgroup/my-tg/5678"
    },
    "TargetValue": 1000.0
  }'
```

**When to use:** Web applications behind an ALB. Scales based on actual request load, not CPU.

### Step Scaling (Fine-Grained Control)

```bash
# Create CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu-alarm \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 60 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=AutoScalingGroupName,Value=my-app-asg \
  --evaluation-periods 2 \
  --alarm-actions $SCALE_OUT_POLICY_ARN

# Step scaling policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-app-asg \
  --policy-name step-scale-out \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments '[
    {"MetricIntervalLowerBound": 0, "MetricIntervalUpperBound": 20, "ScalingAdjustment": 1},
    {"MetricIntervalLowerBound": 20, "MetricIntervalUpperBound": 40, "ScalingAdjustment": 2},
    {"MetricIntervalLowerBound": 40, "ScalingAdjustment": 4}
  ]'
```

**When to use:** When you need different scaling responses at different thresholds (e.g., add 1 at 70% CPU, add 4 at 90% CPU).

### Scheduled Scaling (Predictable Patterns)

```bash
# Scale up every weekday at 8 AM
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name my-app-asg \
  --scheduled-action-name scale-up-morning \
  --recurrence "0 8 * * MON-FRI" \
  --min-size 4 \
  --max-size 20 \
  --desired-capacity 8

# Scale down every weekday at 8 PM
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name my-app-asg \
  --scheduled-action-name scale-down-evening \
  --recurrence "0 20 * * MON-FRI" \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2
```

**When to use:** Business-hours traffic, known events (Black Friday), batch processing windows.

### Predictive Scaling (ML-Based)

```bash
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name my-app-asg \
  --policy-name predictive-scaling \
  --policy-type PredictiveScaling \
  --predictive-scaling-configuration '{
    "MetricSpecifications": [{
      "TargetValue": 50,
      "PredefinedMetricPairSpecification": {
        "PredefinedMetricType": "ASGCPUUtilization"
      }
    }],
    "Mode": "ForecastAndScale",
    "SchedulingBufferTime": 300
  }'
```

**When to use:** Recurring daily/weekly traffic patterns. AWS analyzes 14 days of history and pre-scales before demand arrives. Combine with target tracking for reactive scaling.

### Application Auto Scaling (Non-EC2 Resources)

```bash
# Scale ECS service
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 20

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/my-cluster/my-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name ecs-cpu-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "TargetValue": 50.0
  }'

# Scale DynamoDB
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/MyTable \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --min-capacity 5 \
  --max-capacity 1000

aws application-autoscaling put-scaling-policy \
  --service-namespace dynamodb \
  --resource-id table/MyTable \
  --scalable-dimension dynamodb:table:ReadCapacityUnits \
  --policy-name dynamo-read-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "DynamoDBReadCapacityUtilization"
    },
    "TargetValue": 70.0
  }'
```

### Decision Matrix: Which Scaling to Use

| Scenario | Scaling Type | Why |
|----------|-------------|-----|
| Web app, steady traffic | Target Tracking (CPU or ALB requests) | Simple, AWS manages it |
| E-commerce, Black Friday | Scheduled + Target Tracking | Pre-scale + reactive |
| Daily traffic pattern (9-5) | Predictive + Target Tracking | ML pre-scales + reactive backup |
| Batch processing at night | Scheduled Scaling | Fixed schedule |
| Microservices on ECS | Application Auto Scaling (Target Tracking) | Scales ECS tasks |
| DynamoDB with variable reads | Application Auto Scaling | Scales read/write capacity |
| Need different responses at thresholds | Step Scaling | Fine-grained control |
| Gaming launch (unknown spike) | Target Tracking + high max | Reactive, fast scale-out |

### Common Interview Question

> "Which Auto Scaling policy should you use for a web application?"

**Answer:** Start with **Target Tracking** on `ALBRequestCountPerTarget` — it scales based on actual request load per instance. If traffic is predictable (business hours), add **Scheduled Scaling** to pre-warm. For recurring patterns, add **Predictive Scaling** to let ML pre-scale. Always combine policies — they work together, and the one requesting the most capacity wins.

---

## 15.10 AMI Creation (Process & Best Practices)

An Amazon Machine Image (AMI) is a template containing the OS, application code, and configuration needed to launch EC2 instances.

### AMI Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AMI Structure                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    AMI                                  │ │
│  │                                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │ │
│  │  │ Root Volume  │  │ Data Volume  │  │ Permissions  │ │ │
│  │  │ Snapshot     │  │ Snapshot     │  │              │ │ │
│  │  │ (OS + App)   │  │ (optional)   │  │ Private /    │ │ │
│  │  │              │  │              │  │ Public /     │ │ │
│  │  │ /dev/xvda    │  │ /dev/xvdb    │  │ Shared       │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │ │
│  │                                                         │ │
│  │  + Launch permissions                                   │ │
│  │  + Block device mapping                                 │ │
│  │  + Architecture (x86_64 / arm64)                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  AMI ──▶ Launch Template ──▶ Auto Scaling Group ──▶ EC2     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Method 1: Create AMI from Running Instance

```bash
# Step 1: Prepare the instance (clean up sensitive data)
# SSH into the instance first:
sudo rm -rf /tmp/* /var/tmp/*
sudo rm -f /root/.bash_history /home/*/.bash_history
sudo rm -f /var/log/auth.log /var/log/secure
# Remove any hardcoded credentials
sudo find / -name "*.pem" -o -name "*.key" 2>/dev/null

# Step 2: Create AMI (from your local machine)
AMI_ID=$(aws ec2 create-image \
  --instance-id i-0abc1234567890def \
  --name "app-server-v1.2.0-$(date +%Y%m%d)" \
  --description "App server with Node.js 20, Nginx, deployed app v1.2.0" \
  --no-reboot \
  --tag-specifications 'ResourceType=image,Tags=[
    {Key=Name,Value=app-server-v1.2.0},
    {Key=Version,Value=1.2.0},
    {Key=OS,Value=AmazonLinux2023},
    {Key=CreatedBy,Value=devops-team}
  ]' \
  --query 'ImageId' --output text)

echo "AMI ID: $AMI_ID"
```

**Expected Output:**
```
AMI ID: ami-0abc1234567890def
```

**Command Breakdown:**
- `--no-reboot` — Don't reboot the instance (faster, but filesystem may not be fully consistent)
- Without `--no-reboot` — Instance reboots to ensure clean snapshot (recommended for production)

```bash
# Wait for AMI to be available
aws ec2 wait image-available --image-ids $AMI_ID
echo "AMI is ready!"

# Check AMI status
aws ec2 describe-images --image-ids $AMI_ID \
  --query 'Images[0].{State:State,Name:Name,Created:CreationDate}' --output table
```

**Expected Output:**
```
------------------------------------------------------
|                   DescribeImages                     |
+----------+---------------------------+--------------+
|  State   |          Name             |   Created    |
+----------+---------------------------+--------------+
| available| app-server-v1.2.0-20240615| 2024-06-15   |
+----------+---------------------------+--------------+
```

### Method 2: Create AMI with Packer (Automated, Recommended)

Packer by HashiCorp automates AMI creation. This is the industry-standard approach.

```bash
# Install Packer
curl -fsSL https://releases.hashicorp.com/packer/1.10.0/packer_1.10.0_linux_amd64.zip -o packer.zip
unzip packer.zip && sudo mv packer /usr/local/bin/
```

```json
// packer-template.pkr.hcl (HCL format)
// Save as: app-ami.pkr.hcl

packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

source "amazon-ebs" "app" {
  ami_name      = "app-server-{{timestamp}}"
  instance_type = "t3.medium"
  region        = "us-east-1"

  source_ami_filter {
    filters = {
      name                = "al2023-ami-*-x86_64"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    most_recent = true
    owners      = ["amazon"]
  }

  ssh_username = "ec2-user"

  tags = {
    Name    = "app-server"
    Version = "1.2.0"
    Builder = "packer"
  }
}

build {
  sources = ["source.amazon-ebs.app"]

  # Install dependencies
  provisioner "shell" {
    inline = [
      "sudo yum update -y",
      "sudo yum install -y nodejs nginx",
      "sudo systemctl enable nginx"
    ]
  }

  # Copy application code
  provisioner "file" {
    source      = "./app/"
    destination = "/tmp/app"
  }

  # Configure application
  provisioner "shell" {
    inline = [
      "sudo mv /tmp/app /opt/app",
      "cd /opt/app && npm install --production",
      "sudo cp /opt/app/nginx.conf /etc/nginx/nginx.conf",

      "# Clean up",
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo rm -f /root/.bash_history",
      "sudo rm -f /home/ec2-user/.bash_history"
    ]
  }
}
```

```bash
# Build the AMI
packer init app-ami.pkr.hcl
packer build app-ami.pkr.hcl
```

**Expected Output:**
```
==> amazon-ebs.app: Creating AMI: app-server-1718451234
    amazon-ebs.app: AMI: ami-0def4567890abc123
==> Builds finished. The artifacts of successful builds are:
--> amazon-ebs.app: AMIs were created:
us-east-1: ami-0def4567890abc123
```

### Method 3: EC2 Image Builder (AWS Native)

```bash
# Create Image Builder pipeline
aws imagebuilder create-image-pipeline \
  --name app-server-pipeline \
  --image-recipe-arn arn:aws:imagebuilder:us-east-1:123456789012:image-recipe/app-server/1.0.0 \
  --infrastructure-configuration-arn arn:aws:imagebuilder:us-east-1:123456789012:infrastructure-configuration/app-infra \
  --distribution-configuration-arn arn:aws:imagebuilder:us-east-1:123456789012:distribution-configuration/multi-region \
  --schedule '{"scheduleExpression":"cron(0 8 ? * MON *)","pipelineExecutionStartCondition":"EXPRESSION_MATCH_ONLY"}'
```

### AMI Best Practices

```
Build Process:
  - Use Packer or EC2 Image Builder (never manual)
  - Version your AMIs (include version in name/tags)
  - Build from a base AMI (Amazon Linux 2023, Ubuntu LTS)
  - Test AMI before deploying to production

Security:
  - Remove all SSH keys, credentials, and secrets
  - Clear bash history and temp files
  - Don't bake secrets into AMI — use Secrets Manager at boot
  - Encrypt AMI snapshots with KMS
  - Scan AMI for vulnerabilities (Inspector)

Lifecycle:
  - Tag AMIs with version, date, owner
  - Automate AMI cleanup (deregister old AMIs)
  - Keep last 3-5 versions for rollback
  - Copy AMIs to DR region

Performance:
  - Pre-install all dependencies (faster boot)
  - Use EBS-optimized instances
  - Consider warm pools in ASG for faster scaling
```

### Copy AMI to Another Region (DR)

```bash
aws ec2 copy-image \
  --source-image-id $AMI_ID \
  --source-region us-east-1 \
  --region eu-west-1 \
  --name "app-server-v1.2.0-dr-copy" \
  --encrypted \
  --kms-key-id alias/dr-key
```

### Deregister Old AMIs (Cleanup)

```bash
# Find AMIs older than 30 days
CUTOFF=$(date -d '30 days ago' +%Y-%m-%dT%H:%M:%S)

OLD_AMIS=$(aws ec2 describe-images \
  --owners self \
  --filters "Name=tag:Name,Values=app-server*" \
  --query "Images[?CreationDate<'$CUTOFF'].ImageId" --output text)

for ami in $OLD_AMIS; do
  echo "Deregistering $ami"

  # Get snapshot IDs before deregistering
  SNAPSHOTS=$(aws ec2 describe-images --image-ids $ami \
    --query 'Images[0].BlockDeviceMappings[].Ebs.SnapshotId' --output text)

  # Deregister AMI
  aws ec2 deregister-image --image-id $ami

  # Delete associated snapshots
  for snap in $SNAPSHOTS; do
    aws ec2 delete-snapshot --snapshot-id $snap
    echo "  Deleted snapshot $snap"
  done
done
```

### Use AMI in Launch Template + ASG

```bash
# Update launch template with new AMI
aws ec2 create-launch-template-version \
  --launch-template-name my-app-template \
  --source-version '$Latest' \
  --launch-template-data "{\"ImageId\":\"$AMI_ID\"}"

# Update ASG to use new version
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name my-app-asg \
  --launch-template LaunchTemplateName=my-app-template,Version='$Latest'

# Rolling update: replace instances with new AMI
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name my-app-asg \
  --preferences '{"MinHealthyPercentage":90,"InstanceWarmup":300}'
```

---

## 15.11 AWS Secret Retrieval in Jenkins Pipeline

Jenkins pipelines often need AWS credentials, database passwords, and API keys. The secure approach is to retrieve them from AWS Secrets Manager or SSM Parameter Store at runtime — never hardcode them.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Jenkins Server (EC2)                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  IAM Role: Jenkins-Server-Role                         │ │
│  │  (attached via Instance Profile)                       │ │
│  │                                                        │ │
│  │  Pipeline Stage: "Get Secrets"                         │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │  aws secretsmanager get-secret-value             │ │ │
│  │  │    --secret-id myapp/prod/db-credentials         │ │ │
│  │  │                                                   │ │ │
│  │  │  aws ssm get-parameter                           │ │ │
│  │  │    --name /myapp/prod/api-key                    │ │ │
│  │  │    --with-decryption                             │ │ │
│  │  └──────────────────┬───────────────────────────────┘ │ │
│  │                     │                                  │ │
│  └─────────────────────┼──────────────────────────────────┘ │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AWS Secrets Manager / SSM Parameter Store            │   │
│  │                                                       │   │
│  │  myapp/prod/db-credentials:                           │   │
│  │    {"username":"admin","password":"SecureP@ss!"}      │   │
│  │                                                       │   │
│  │  /myapp/prod/api-key:                                 │   │
│  │    "sk-abc123def456..."                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Secrets NEVER stored in Jenkins, Git, or environment vars   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Method 1: IAM Role on Jenkins EC2 (Recommended)

The Jenkins EC2 instance has an IAM role that allows it to read secrets. No credentials stored anywhere.

#### IAM Policy for Jenkins Role

```bash
cat > jenkins-secrets-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadSecrets",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:us-east-1:123456789012:secret:myapp/*"
            ]
        },
        {
            "Sid": "ReadSSMParameters",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": [
                "arn:aws:ssm:us-east-1:123456789012:parameter/myapp/*"
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
EOF

aws iam create-policy \
  --policy-name Jenkins-Secrets-Read \
  --policy-document file://jenkins-secrets-policy.json

# Attach to Jenkins EC2 role
aws iam attach-role-policy \
  --role-name Jenkins-Server-Role \
  --policy-arn arn:aws:iam::123456789012:policy/Jenkins-Secrets-Read
```

#### Jenkinsfile — Retrieve Secrets in Pipeline

```groovy
pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
    }

    stages {
        stage('Get Secrets') {
            steps {
                script {
                    // Retrieve from Secrets Manager
                    def dbCredsJson = sh(
                        script: '''
                            aws secretsmanager get-secret-value \
                              --secret-id myapp/prod/db-credentials \
                              --query 'SecretString' --output text
                        ''',
                        returnStdout: true
                    ).trim()

                    def dbCreds = readJSON text: dbCredsJson
                    env.DB_HOST = dbCreds.host
                    env.DB_USER = dbCreds.username
                    env.DB_PASS = dbCreds.password

                    // Retrieve from SSM Parameter Store
                    env.API_KEY = sh(
                        script: '''
                            aws ssm get-parameter \
                              --name /myapp/prod/api-key \
                              --with-decryption \
                              --query 'Parameter.Value' --output text
                        ''',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Build') {
            steps {
                sh '''
                    echo "Building with DB host: $DB_HOST"
                    # DB_PASS is available but never printed
                    docker build \
                      --build-arg DB_HOST=$DB_HOST \
                      --build-arg DB_USER=$DB_USER \
                      -t myapp:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    # Pass secrets as environment variables to container
                    aws ecs update-service \
                      --cluster prod \
                      --service myapp \
                      --force-new-deployment
                '''
            }
        }
    }

    post {
        always {
            // Clean up secrets from environment
            sh 'unset DB_PASS API_KEY 2>/dev/null || true'
        }
    }
}
```

### Method 2: Jenkins AWS Credentials Plugin

If Jenkins is not on EC2 (e.g., on-prem Jenkins), use the AWS Credentials plugin.

```groovy
pipeline {
    agent any

    stages {
        stage('Get Secrets') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-jenkins-creds',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']]) {

                    script {
                        env.DB_PASS = sh(
                            script: '''
                                aws secretsmanager get-secret-value \
                                  --secret-id myapp/prod/db-credentials \
                                  --query 'SecretString' --output text | \
                                  python3 -c "import sys,json; print(json.load(sys.stdin)['password'])"
                            ''',
                            returnStdout: true
                        ).trim()
                    }
                }
            }
        }
    }
}
```

### Method 3: AWS Secrets Manager Jenkins Plugin

```groovy
// Requires: AWS Secrets Manager Credentials Provider plugin
pipeline {
    agent any

    stages {
        stage('Deploy') {
            steps {
                withCredentials([string(credentialsId: 'myapp/prod/api-key', variable: 'API_KEY')]) {
                    sh '''
                        curl -H "Authorization: Bearer $API_KEY" https://api.example.com/deploy
                    '''
                }
            }
        }
    }
}
```

### Method 4: Shell Script (for non-Jenkins CI/CD)

```bash
#!/bin/bash
# === Retrieve secrets for deployment ===

# Get database credentials
DB_CREDS=$(aws secretsmanager get-secret-value \
  --secret-id myapp/prod/db-credentials \
  --query 'SecretString' --output text)

export DB_HOST=$(echo $DB_CREDS | python3 -c "import sys,json; print(json.load(sys.stdin)['host'])")
export DB_USER=$(echo $DB_CREDS | python3 -c "import sys,json; print(json.load(sys.stdin)['username'])")
export DB_PASS=$(echo $DB_CREDS | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")

# Get API key from SSM
export API_KEY=$(aws ssm get-parameter \
  --name /myapp/prod/api-key \
  --with-decryption \
  --query 'Parameter.Value' --output text)

# Run deployment
docker run -e DB_HOST -e DB_USER -e DB_PASS -e API_KEY myapp:latest

# Clean up
unset DB_PASS API_KEY
```

### Security Best Practices for Jenkins + AWS Secrets

```
DO:
  - Use IAM roles on EC2 (no stored credentials)
  - Scope IAM policy to specific secrets (not secretsmanager:*)
  - Use KMS encryption for secrets
  - Rotate secrets automatically (Secrets Manager supports this)
  - Mask secrets in Jenkins console output
  - Clean up secrets from environment after use

DON'T:
  - Store AWS access keys in Jenkins credentials store
  - Print secrets in build logs (echo $DB_PASS)
  - Pass secrets as build arguments in Dockerfile
  - Commit secrets to Git (even in Jenkinsfile)
  - Use the same secrets across environments (dev/staging/prod)
```

---

## 15.12 Key Takeaways

1. **IAM User vs Role:** Use Users for humans, Roles for services. Never embed access keys in code — use IAM roles with instance profiles.

2. **EC2 to S3 Access:** Create a scoped IAM policy (specific bucket), attach to a role, create an instance profile, and associate with the EC2 instance. Verify with metadata endpoint.

3. **IAM Security Audit:** Use Credential Report (monthly), Access Analyzer (continuous), Access Advisor (quarterly), and AWS Config rules. Automate with scripts.

4. **GuardDuty:** Enable it everywhere. It analyzes CloudTrail, VPC Flow Logs, and DNS logs to detect threats. Automate response with EventBridge + Lambda.

5. **3-Tier HA:** Deploy across 2+ AZs. ALB + ASG for web/app tier, RDS Multi-AZ for data tier, NAT Gateway per AZ. No single point of failure.

6. **RDS Deployment:** Use Multi-AZ for production (automatic failover). Use Aurora for high performance. Always encrypt, use private subnets, store credentials in Secrets Manager.

7. **RDS Cost Optimization:** Add ElastiCache to offload reads (70-90% cache hit). Add read replicas. Downsize primary. Use Reserved Instances. Consider Aurora Serverless v2 for variable traffic.

8. **Site-to-Site VPN:** Creates encrypted IPsec tunnels over the internet. Components: Customer Gateway (your router) + Virtual Private Gateway (AWS side) + VPN Connection. Each connection has 2 tunnels for redundancy.

9. **Auto Scaling:** Start with Target Tracking (simplest). Add Scheduled Scaling for predictable patterns. Use Predictive Scaling for recurring patterns. Step Scaling for fine-grained control. Application Auto Scaling for ECS, DynamoDB, etc.

10. **AMI Creation:** Use Packer or EC2 Image Builder (never manual). Clean up secrets before creating. Version and tag AMIs. Automate cleanup of old AMIs. Copy to DR region.

11. **Secrets in Jenkins:** Use IAM roles on EC2 (no stored credentials). Retrieve from Secrets Manager or SSM at runtime. Never print secrets in logs. Scope IAM policies to specific secrets.

