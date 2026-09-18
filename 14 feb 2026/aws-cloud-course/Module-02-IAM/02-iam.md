# Module 2: IAM - Identity and Access Management

## 2.1 What is IAM?

IAM (Identity and Access Management) controls **who** can access **what** in your AWS account.

### Real-World Analogy
Think of IAM like a building security system:
- **Users** = Employee badges (individual people)
- **Groups** = Departments (Marketing, Engineering)
- **Roles** = Temporary visitor passes (assumed by services)
- **Policies** = Access rules (who can enter which rooms)

### IAM Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Account (Root)                     │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │                    IAM                             │   │
│  │                                                    │   │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐        │   │
│  │  │  Users   │   │ Groups  │   │  Roles  │        │   │
│  │  │         │   │         │   │         │        │   │
│  │  │ alice   │──▶│  devs   │   │ EC2Role │        │   │
│  │  │ bob     │──▶│  ops    │   │ LambdaR │        │   │
│  │  │ charlie │   │  admin  │   │         │        │   │
│  │  └─────────┘   └────┬────┘   └────┬────┘        │   │
│  │                      │             │              │   │
│  │                      ▼             ▼              │   │
│  │              ┌──────────────────────────┐         │   │
│  │              │       Policies           │         │   │
│  │              │                          │         │   │
│  │              │  S3ReadOnly              │         │   │
│  │              │  EC2FullAccess           │         │   │
│  │              │  AdministratorAccess     │         │   │
│  │              │  CustomPolicy            │         │   │
│  │              └──────────────────────────┘         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Key IAM Facts
- IAM is **global** (not region-specific)
- IAM is **free** (no charges for users, groups, roles, policies)
- Root account should NEVER be used for daily operations
- Follow the **Principle of Least Privilege** — give minimum permissions needed

---

## 2.2 IAM Users

An IAM user represents a person or application that interacts with AWS.

### Create an IAM User (CLI)

```bash
# Create a user named "developer"
aws iam create-user --user-name developer
```

**Command Breakdown:**
- `aws iam` → IAM service
- `create-user` → Action to create a new user
- `--user-name developer` → Name of the user

**Expected Output:**
```json
{
    "User": {
        "Path": "/",
        "UserName": "developer",
        "UserId": "AIDAIOSFODNN7EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:user/developer",
        "CreateDate": "2024-01-15T10:30:00+00:00"
    }
}
```

### Understanding ARN (Amazon Resource Name)

```
arn:aws:iam::123456789012:user/developer
│   │   │    │            │
│   │   │    │            └── Resource (user name)
│   │   │    └── Account ID
│   │   └── Service (IAM)
│   └── Partition (aws, aws-cn, aws-us-gov)
└── Prefix (always "arn")
```

### Create Access Keys (for CLI/API access)

```bash
aws iam create-access-key --user-name developer
```

**Expected Output:**
```json
{
    "AccessKey": {
        "UserName": "developer",
        "AccessKeyId": "AKIAI44QH8DHBEXAMPLE",
        "Status": "Active",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "CreateDate": "2024-01-15T10:35:00+00:00"
    }
}
```

⚠️ **Save the SecretAccessKey immediately — it's shown only once!**

### Create Console Login (for web access)

```bash
aws iam create-login-profile \
  --user-name developer \
  --password "MyStr0ng!Pass#2024" \
  --password-reset-required
```

**Command Breakdown:**
- `create-login-profile` → Enables console (web) login
- `--password` → Initial password
- `--password-reset-required` → Forces password change on first login

**Expected Output:**
```json
{
    "LoginProfile": {
        "UserName": "developer",
        "CreateDate": "2024-01-15T10:40:00+00:00",
        "PasswordResetRequired": true
    }
}
```

### List All Users

```bash
aws iam list-users
```

**Expected Output:**
```json
{
    "Users": [
        {
            "Path": "/",
            "UserName": "developer",
            "UserId": "AIDAIOSFODNN7EXAMPLE",
            "Arn": "arn:aws:iam::123456789012:user/developer",
            "CreateDate": "2024-01-15T10:30:00+00:00"
        }
    ]
}
```

```bash
# Table format for readability
aws iam list-users --output table
```

**Expected Output:**
```
---------------------------------------------------------
|                       ListUsers                        |
+-------------------------------------------------------+
||                        Users                         ||
|+-----------+------------------------------------------+|
|| UserName  | Arn                                      ||
|+-----------+------------------------------------------+|
|| developer | arn:aws:iam::123456789012:user/developer  ||
|+-----------+------------------------------------------+|
```

### Delete a User

```bash
# First remove all attached resources
aws iam delete-login-profile --user-name developer
aws iam list-access-keys --user-name developer
aws iam delete-access-key --user-name developer --access-key-id AKIAI44QH8DHBEXAMPLE
aws iam list-attached-user-policies --user-name developer
aws iam detach-user-policy --user-name developer --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Then delete the user
aws iam delete-user --user-name developer
```

**Expected Output:** (No output on success — HTTP 200)

---

## 2.3 IAM Groups

Groups are collections of users. Attach policies to groups instead of individual users.

### Create a Group

```bash
aws iam create-group --group-name developers
```

**Expected Output:**
```json
{
    "Group": {
        "Path": "/",
        "GroupName": "developers",
        "GroupId": "AGPAJNKMQE5YKEXAMPLE",
        "Arn": "arn:aws:iam::123456789012:group/developers",
        "CreateDate": "2024-01-15T11:00:00+00:00"
    }
}
```

### Add User to Group

```bash
aws iam add-user-to-group --user-name developer --group-name developers
```

**Expected Output:** (No output on success)

### Verify Group Membership

```bash
aws iam get-group --group-name developers
```

**Expected Output:**
```json
{
    "Users": [
        {
            "Path": "/",
            "UserName": "developer",
            "UserId": "AIDAIOSFODNN7EXAMPLE",
            "Arn": "arn:aws:iam::123456789012:user/developer",
            "CreateDate": "2024-01-15T10:30:00+00:00"
        }
    ],
    "Group": {
        "Path": "/",
        "GroupName": "developers",
        "GroupId": "AGPAJNKMQE5YKEXAMPLE",
        "Arn": "arn:aws:iam::123456789012:group/developers",
        "CreateDate": "2024-01-15T11:00:00+00:00"
    }
}
```

### List All Groups

```bash
aws iam list-groups --output table
```

### Remove User from Group

```bash
aws iam remove-user-from-group --user-name developer --group-name developers
```

---

## 2.4 IAM Policies

Policies are JSON documents that define permissions.

### Policy Structure

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3Read",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-bucket",
                "arn:aws:s3:::my-bucket/*"
            ]
        }
    ]
}
```

**Field Breakdown:**

| Field | Meaning | Values |
|-------|---------|--------|
| `Version` | Policy language version | Always `"2012-10-17"` |
| `Statement` | Array of permission rules | One or more statements |
| `Sid` | Statement ID (optional label) | Any descriptive string |
| `Effect` | Allow or deny | `"Allow"` or `"Deny"` |
| `Action` | What operations are permitted | Service-specific actions |
| `Resource` | Which resources it applies to | ARNs or `"*"` for all |
| `Condition` | When the policy applies (optional) | IP, time, MFA, etc. |

### AWS Managed Policies (Pre-built)

```bash
# List AWS managed policies
aws iam list-policies --scope AWS --query 'Policies[?starts_with(PolicyName, `Amazon`)].[PolicyName,Arn]' --output table | head -30
```

**Common Managed Policies:**

| Policy Name | What It Allows |
|------------|----------------|
| `AdministratorAccess` | Full access to everything |
| `PowerUserAccess` | Full access except IAM management |
| `ReadOnlyAccess` | Read-only access to all services |
| `AmazonS3FullAccess` | Full S3 access |
| `AmazonS3ReadOnlyAccess` | Read-only S3 access |
| `AmazonEC2FullAccess` | Full EC2 access |
| `AmazonVPCFullAccess` | Full VPC access |
| `AmazonRDSFullAccess` | Full RDS access |

### Attach a Managed Policy to a Group

```bash
aws iam attach-group-policy \
  --group-name developers \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

**Expected Output:** (No output on success)

### Verify Attached Policies

```bash
aws iam list-attached-group-policies --group-name developers
```

**Expected Output:**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "AmazonS3ReadOnlyAccess",
            "PolicyArn": "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        }
    ]
}
```

### Create a Custom Policy

```bash
# Create a policy file
cat > s3-upload-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowUploadToSpecificBucket",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::company-uploads",
                "arn:aws:s3:::company-uploads/*"
            ]
        }
    ]
}
EOF

# Create the policy in AWS
aws iam create-policy \
  --policy-name S3UploadPolicy \
  --policy-document file://s3-upload-policy.json
```

**Expected Output:**
```json
{
    "Policy": {
        "PolicyName": "S3UploadPolicy",
        "PolicyId": "ANPAJNKMQE5YKEXAMPLE",
        "Arn": "arn:aws:iam::123456789012:policy/S3UploadPolicy",
        "Path": "/",
        "DefaultVersionId": "v1",
        "AttachmentCount": 0,
        "CreateDate": "2024-01-15T12:00:00+00:00"
    }
}
```

### Attach Custom Policy to User

```bash
aws iam attach-user-policy \
  --user-name developer \
  --policy-arn arn:aws:iam::123456789012:policy/S3UploadPolicy
```

### Policy with Conditions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowEC2OnlyFromOfficeIP",
            "Effect": "Allow",
            "Action": "ec2:*",
            "Resource": "*",
            "Condition": {
                "IpAddress": {
                    "aws:SourceIp": "203.0.113.0/24"
                }
            }
        },
        {
            "Sid": "DenyWithoutMFA",
            "Effect": "Deny",
            "Action": "*",
            "Resource": "*",
            "Condition": {
                "BoolIfExists": {
                    "aws:MultiFactorAuthPresent": "false"
                }
            }
        }
    ]
}
```

### Policy Evaluation Logic

```
┌─────────────────────────────────────────┐
│         Policy Evaluation Order          │
│                                          │
│  1. By default, all requests are DENIED  │
│              │                           │
│              ▼                           │
│  2. Explicit ALLOW overrides default     │
│              │                           │
│              ▼                           │
│  3. Explicit DENY overrides any ALLOW    │
│              │                           │
│              ▼                           │
│  Result: DENY wins over ALLOW always     │
└─────────────────────────────────────────┘
```

---

## 2.5 IAM Roles

Roles are temporary credentials assumed by AWS services, applications, or users.

### Real-World Analogy
A role is like a contractor badge:
- An EC2 instance (contractor) assumes a role (badge) to access S3 (restricted area)
- The badge is temporary and can be revoked
- No permanent credentials are stored on the EC2 instance

### Create a Role for EC2

```bash
# Step 1: Create the trust policy (who can assume this role)
cat > ec2-trust-policy.json << 'EOF'
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
  --role-name EC2-S3-Access-Role \
  --assume-role-policy-document file://ec2-trust-policy.json
```

**Expected Output:**
```json
{
    "Role": {
        "Path": "/",
        "RoleName": "EC2-S3-Access-Role",
        "RoleId": "AROAIOSFODNN7EXAMPLE",
        "Arn": "arn:aws:iam::123456789012:role/EC2-S3-Access-Role",
        "CreateDate": "2024-01-15T13:00:00+00:00",
        "AssumeRolePolicyDocument": {
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
    }
}
```

### Attach Policy to Role

```bash
aws iam attach-role-policy \
  --role-name EC2-S3-Access-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### Create Instance Profile (to attach role to EC2)

```bash
# Create instance profile
aws iam create-instance-profile --instance-profile-name EC2-S3-Profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name EC2-S3-Profile \
  --role-name EC2-S3-Access-Role
```

### List Roles

```bash
aws iam list-roles --query 'Roles[?starts_with(RoleName, `EC2`)].[RoleName,Arn]' --output table
```

### Assume a Role (for cross-account access)

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::987654321098:role/CrossAccountRole \
  --role-session-name my-session
```

**Expected Output:**
```json
{
    "Credentials": {
        "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": "FwoGZXIvYXdzEBYaDH...(long token)...",
        "Expiration": "2024-01-15T14:00:00+00:00"
    },
    "AssumedRoleUser": {
        "AssumedRoleId": "AROAIOSFODNN7EXAMPLE:my-session",
        "Arn": "arn:aws:sts::987654321098:assumed-role/CrossAccountRole/my-session"
    }
}
```

---

## 2.6 IAM Password Policy

```bash
# Set a strong password policy
aws iam update-account-password-policy \
  --minimum-password-length 14 \
  --require-symbols \
  --require-numbers \
  --require-uppercase-characters \
  --require-lowercase-characters \
  --max-password-age 90 \
  --password-reuse-prevention 12 \
  --allow-users-to-change-password
```

**Command Breakdown:**
| Flag | Meaning |
|------|---------|
| `--minimum-password-length 14` | At least 14 characters |
| `--require-symbols` | Must include special characters |
| `--require-numbers` | Must include digits |
| `--max-password-age 90` | Password expires after 90 days |
| `--password-reuse-prevention 12` | Can't reuse last 12 passwords |

### View Current Password Policy

```bash
aws iam get-account-password-policy
```

---

## 2.7 IAM MFA (Multi-Factor Authentication)

### Enable Virtual MFA for a User

```bash
# Create virtual MFA device
aws iam create-virtual-mfa-device \
  --virtual-mfa-device-name developer-mfa \
  --outfile /tmp/QRCode.png \
  --bootstrap-method QRCodePNG

# Enable MFA (after scanning QR code and getting two consecutive codes)
aws iam enable-mfa-device \
  --user-name developer \
  --serial-number arn:aws:iam::123456789012:mfa/developer-mfa \
  --authentication-code1 123456 \
  --authentication-code2 789012
```

### List MFA Devices

```bash
aws iam list-mfa-devices --user-name developer
```

**Expected Output:**
```json
{
    "MFADevices": [
        {
            "UserName": "developer",
            "SerialNumber": "arn:aws:iam::123456789012:mfa/developer-mfa",
            "EnableDate": "2024-01-15T14:30:00+00:00"
        }
    ]
}
```

---

## 2.8 IAM Best Practices

```
┌─────────────────────────────────────────────────────────┐
│              IAM Security Best Practices                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. ✅ Enable MFA on root account                        │
│  2. ✅ Never use root account for daily tasks             │
│  3. ✅ Create individual IAM users (no shared accounts)   │
│  4. ✅ Use groups to assign permissions                   │
│  5. ✅ Grant least privilege                              │
│  6. ✅ Use roles for EC2/Lambda (not access keys)         │
│  7. ✅ Rotate credentials regularly                       │
│  8. ✅ Use policy conditions for extra security           │
│  9. ✅ Enable CloudTrail for auditing                     │
│  10. ✅ Remove unused users and credentials               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Generate Credential Report

```bash
# Generate the report
aws iam generate-credential-report

# Download the report
aws iam get-credential-report --query 'Content' --output text | base64 --decode > credential-report.csv

# View it
cat credential-report.csv
```

---

## 2.9 Industry Project: Multi-Team IAM Setup

### Scenario
A startup has three teams: **Developers**, **DevOps**, and **Finance**. Set up IAM with proper access controls.

```bash
#!/bin/bash
# === IAM Setup Script for Startup ===

# --- Create Groups ---
aws iam create-group --group-name Developers
aws iam create-group --group-name DevOps
aws iam create-group --group-name Finance

# --- Attach Policies to Groups ---

# Developers: EC2 + S3 + Lambda + CloudWatch (read)
aws iam attach-group-policy --group-name Developers \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess
aws iam attach-group-policy --group-name Developers \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-group-policy --group-name Developers \
  --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-group-policy --group-name Developers \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess

# DevOps: Admin access (with MFA requirement)
aws iam attach-group-policy --group-name DevOps \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Finance: Billing access only
aws iam attach-group-policy --group-name Finance \
  --policy-arn arn:aws:iam::aws:policy/job-function/Billing

# --- Create Users ---
for user in alice bob charlie; do
  aws iam create-user --user-name $user
  aws iam create-login-profile --user-name $user \
    --password "TempPass!${user}2024" --password-reset-required
  echo "Created user: $user"
done

# --- Assign Users to Groups ---
aws iam add-user-to-group --user-name alice --group-name Developers
aws iam add-user-to-group --user-name bob --group-name DevOps
aws iam add-user-to-group --user-name charlie --group-name Finance

# --- Create EC2 Role ---
cat > /tmp/ec2-trust.json << 'TRUST'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }
    ]
}
TRUST

aws iam create-role --role-name AppServerRole \
  --assume-role-policy-document file:///tmp/ec2-trust.json

aws iam attach-role-policy --role-name AppServerRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
aws iam attach-role-policy --role-name AppServerRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

aws iam create-instance-profile --instance-profile-name AppServerProfile
aws iam add-role-to-instance-profile \
  --instance-profile-name AppServerProfile --role-name AppServerRole

# --- Set Password Policy ---
aws iam update-account-password-policy \
  --minimum-password-length 14 \
  --require-symbols --require-numbers \
  --require-uppercase-characters --require-lowercase-characters \
  --max-password-age 90 --password-reuse-prevention 12

echo "IAM setup complete!"
```

### Verification Commands

```bash
# List all users and their groups
for user in alice bob charlie; do
  echo "=== $user ==="
  aws iam list-groups-for-user --user-name $user --query 'Groups[].GroupName' --output text
done

# List all groups and their policies
for group in Developers DevOps Finance; do
  echo "=== $group ==="
  aws iam list-attached-group-policies --group-name $group --query 'AttachedPolicies[].PolicyName' --output text
done
```

---

## 2.10 Common Errors & Troubleshooting

### Error 1: "EntityAlreadyExists"
```
An error occurred (EntityAlreadyExists) when calling the CreateUser operation:
User with name developer already exists.
```
**Fix:** The user already exists. List users to verify:
```bash
aws iam list-users --query 'Users[].UserName' --output text
```

### Error 2: "DeleteConflict"
```
An error occurred (DeleteConflict) when calling the DeleteUser operation:
Cannot delete entity, must remove all attached policies first.
```
**Fix:** Remove all policies, access keys, MFA devices, and group memberships first:
```bash
# List and detach all policies
aws iam list-attached-user-policies --user-name developer
aws iam detach-user-policy --user-name developer --policy-arn <policy-arn>

# List and delete access keys
aws iam list-access-keys --user-name developer
aws iam delete-access-key --user-name developer --access-key-id <key-id>

# Remove from groups
aws iam list-groups-for-user --user-name developer
aws iam remove-user-from-group --user-name developer --group-name <group>

# Now delete
aws iam delete-user --user-name developer
```

### Error 3: "MalformedPolicyDocument"
```
An error occurred (MalformedPolicyDocument) when calling the CreatePolicy operation:
Syntax errors in policy.
```
**Fix:** Validate your JSON:
```bash
# Check JSON syntax
python3 -m json.tool < policy.json

# Common issues:
# - Missing comma after a statement
# - Using single quotes instead of double quotes
# - Missing "Version": "2012-10-17"
# - Incorrect ARN format
```

### Error 4: "LimitExceeded"
```
An error occurred (LimitExceeded) when calling the CreateUser operation:
Cannot exceed quota for UsersPerAccount: 5000.
```
**Fix:** Delete unused users or request a limit increase:
```bash
aws service-quotas request-service-quota-increase \
  --service-code iam \
  --quota-code L-F55AF5E4 \
  --desired-value 10000
```

### Error 5: Policy Not Taking Effect
**Symptoms:** User has a policy attached but still gets "Access Denied"
**Troubleshooting:**
```bash
# 1. Check if there's an explicit DENY (overrides ALLOW)
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/developer \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::my-bucket/file.txt

# 2. Check all policies (user + group + inline)
aws iam list-attached-user-policies --user-name developer
aws iam list-user-policies --user-name developer  # inline policies
aws iam list-groups-for-user --user-name developer

# 3. Check for Service Control Policies (if using AWS Organizations)
aws organizations list-policies --filter SERVICE_CONTROL_POLICY
```

---

## 2.11 IAM Policies Inheritance

Policies are inherited through group membership and organizational hierarchy.

```
AWS Organization
├── Root OU (SCP: FullAWSAccess)
│   ├── Prod OU (SCP: DenyDeleteS3)
│   │   └── Account A
│   │       └── User "alice" (Group: Developers)
│   │           Effective = SCP ∩ Group Policy ∩ User Policy
│   └── Dev OU (SCP: FullAWSAccess)
│       └── Account B
```

- A user inherits all policies from their groups
- If a user is in multiple groups, all policies are combined
- SCPs from the Organization further restrict what's allowed

---

## 2.12 IAM Conditions

Conditions add fine-grained control to policies. They evaluate request context (IP, time, tags, MFA, etc.).

```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Deny",
        "Action": "*",
        "Resource": "*",
        "Condition": {
            "NotIpAddress": {"aws:SourceIp": ["192.168.1.0/24", "10.0.0.0/8"]},
            "Bool": {"aws:MultiFactorAuthPresent": "false"}
        }
    }]
}
```

**Common Condition Keys:**

| Key | Use Case |
|-----|----------|
| `aws:SourceIp` | Restrict by client IP |
| `aws:RequestedRegion` | Restrict to specific regions |
| `aws:MultiFactorAuthPresent` | Require MFA |
| `aws:PrincipalTag` | Match user/role tags |
| `aws:ResourceTag` | Match resource tags |
| `aws:PrincipalOrgID` | Restrict to Organization members |
| `s3:prefix` | Restrict S3 access to specific prefixes |

---

## 2.13 IAM Roles vs Resource-Based Policies

| Approach | How It Works | Cross-Account |
|----------|-------------|---------------|
| **IAM Role** | User assumes role, gives up original permissions | Yes — user loses original permissions |
| **Resource-Based Policy** | Policy on the resource grants access | Yes — user keeps original permissions |

Resource-based policies are supported by: S3, SQS, SNS, Lambda, KMS, API Gateway, etc.

Use resource-based policies when you need the principal to retain their original permissions (e.g., Lambda in Account A accessing DynamoDB in Account B while also accessing S3 in Account A).

---

## 2.14 AWS IAM Identity Center (formerly AWS SSO)

Single sign-on for all AWS accounts in an Organization and business applications.

```
Users ──▶ IAM Identity Center ──▶ Multiple AWS Accounts
                               ──▶ Business Apps (Salesforce, Slack, etc.)
                               ──▶ SAML 2.0 apps
```

- One login for all AWS accounts
- Integrates with Active Directory, Okta, Azure AD
- Permission Sets define what users can do in each account
- Built-in identity store or external identity provider

### Identity Center Login Flow

```
User ──▶ IAM Identity Center Portal (https://d-xxxxxxxxxx.awsapps.com/start)
  │
  ├── Built-in Identity Store ──▶ Username/Password stored in Identity Center
  │
  └── External IdP (Active Directory / Okta / Azure AD)
        │
        ├── AWS Managed Microsoft AD ──▶ Two-way trust or direct integration
        ├── AD Connector ──▶ Proxy to on-premises Active Directory
        └── SAML 2.0 IdP ──▶ Okta, Azure AD, OneLogin, etc.
  │
  ▼
Permission Set applied ──▶ Temporary STS credentials ──▶ Access AWS Account
```

**Login flow steps:**
1. User navigates to Identity Center portal URL
2. Authenticates against identity source (built-in store or external IdP)
3. Selects target AWS account from list of assigned accounts
4. Selects Permission Set (e.g., AdministratorAccess, ReadOnlyAccess)
5. Identity Center calls STS AssumeRole with the mapped IAM role
6. User receives temporary credentials (valid 1-12 hours)

### Active Directory Integration

```
┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  On-Premises AD     │────▶│  AD Connector (proxy) │────▶│ IAM Identity │
│  (corp.example.com) │     │  (no caching)         │     │   Center     │
└─────────────────────┘     └──────────────────────┘     └──────────────┘

┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  On-Premises AD     │◀──▶│  AWS Managed          │────▶│ IAM Identity │
│  (corp.example.com) │trust│  Microsoft AD         │     │   Center     │
└─────────────────────┘     └──────────────────────┘     └──────────────┘
```

**Option 1: AD Connector** — lightweight proxy, no data stored in AWS, requires VPN/DX to on-prem AD.

**Option 2: AWS Managed Microsoft AD** — full AD in AWS, supports two-way trust with on-prem AD, works even if VPN is down.

```bash
# Create a Permission Set via CLI
aws sso-admin create-permission-set \
  --instance-arn arn:aws:sso:::instance/ssoins-1234567890abcdef \
  --name "DeveloperAccess" \
  --description "Developer access with limited admin" \
  --session-duration PT8H

# Expected output:
# {
#   "PermissionSet": {
#     "Name": "DeveloperAccess",
#     "PermissionSetArn": "arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-abcdef1234567890",
#     "SessionDuration": "PT8H",
#     "CreatedDate": "2024-01-15T10:30:00Z"
#   }
# }

# Attach AWS managed policy to Permission Set
aws sso-admin attach-managed-policy-to-permission-set \
  --instance-arn arn:aws:sso:::instance/ssoins-1234567890abcdef \
  --permission-set-arn arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-abcdef1234567890 \
  --managed-policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Assign Permission Set to a user for a specific account
aws sso-admin create-account-assignment \
  --instance-arn arn:aws:sso:::instance/ssoins-1234567890abcdef \
  --permission-set-arn arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-abcdef1234567890 \
  --principal-type USER \
  --principal-id "94482488-3aff-11e9-b210-d663bd873d93" \
  --target-type AWS_ACCOUNT \
  --target-id "123456789012"

# Expected output:
# {
#   "AccountAssignmentCreationStatus": {
#     "Status": "IN_PROGRESS",
#     "RequestId": "a1b2c3d4-5678-90ab-cdef-example11111"
#   }
# }

# List all Permission Sets
aws sso-admin list-permission-sets \
  --instance-arn arn:aws:sso:::instance/ssoins-1234567890abcdef

# Expected output:
# {
#   "PermissionSets": [
#     "arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-abcdef1234567890",
#     "arn:aws:sso:::permissionSet/ssoins-1234567890abcdef/ps-1234567890abcdef"
#   ]
# }
```

**Real-life use case:** A company with 500 employees and 20 AWS accounts uses IAM Identity Center with their existing on-premises Active Directory via AD Connector. Developers get "DeveloperAccess" Permission Set for dev/staging accounts, while only the platform team gets "AdministratorAccess" for production. When an employee leaves, disabling their AD account immediately revokes all AWS access across all 20 accounts.

---

## 2.15 AWS Control Tower

Automates the setup and governance of a multi-account AWS environment.

- Sets up a landing zone (multi-account structure)
- Applies guardrails (preventive SCPs + detective Config rules)
- Automates account provisioning
- Dashboard for compliance monitoring

**Guardrail Types:**
- **Preventive**: SCPs that prevent actions (e.g., deny region changes)
- **Detective**: AWS Config rules that detect non-compliance (e.g., unencrypted EBS)

---

## 2.16 Key Takeaways

1. IAM = Users + Groups + Roles + Policies
2. Always use groups to manage permissions (never attach policies directly to users)
3. Use roles for AWS services (EC2, Lambda) — never embed access keys
4. Policies follow: Default Deny → Explicit Allow → Explicit Deny wins
5. Enable MFA for all human users, especially root
6. Rotate access keys every 90 days
7. Use `aws iam simulate-principal-policy` to debug permission issues
8. IAM Conditions for fine-grained control (IP, MFA, region, tags)
9. Resource-based policies let principals keep original permissions (unlike assuming roles)
10. IAM Identity Center for SSO across all Organization accounts
11. Control Tower for automated multi-account governance with guardrails
