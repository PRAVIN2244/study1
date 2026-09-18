# Module 1: AWS Fundamentals & Account Setup

## 1.1 What is Cloud Computing?

### Concept
Cloud computing is renting computing resources (servers, storage, databases, networking) over the internet instead of owning physical hardware.

### Real-World Analogy
Think of it like electricity:
- **Before cloud**: Every company had its own generator (own data center)
- **After cloud**: You plug into the power grid (AWS) and pay for what you use

### Types of Cloud Computing

| Type | What You Manage | What Provider Manages | Example |
|------|----------------|----------------------|---------|
| **IaaS** (Infrastructure as a Service) | OS, Apps, Data | Hardware, Networking, Virtualization | AWS EC2 |
| **PaaS** (Platform as a Service) | Apps, Data | Everything else | AWS Elastic Beanstalk |
| **SaaS** (Software as a Service) | Nothing (just use it) | Everything | Gmail, Slack |

### Cloud Deployment Models

```
┌─────────────────────────────────────────────────────┐
│                  Deployment Models                    │
├──────────────┬──────────────┬───────────────────────┤
│ Public Cloud │ Private Cloud│ Hybrid Cloud           │
│ (AWS, Azure) │ (On-premise) │ (Mix of both)          │
│              │              │                        │
│ Shared infra │ Dedicated    │ Sensitive data on-prem │
│ Pay-as-you-go│ Full control │ Scalable workloads     │
│ No maintenance│ High cost   │ on public cloud        │
└──────────────┴──────────────┴───────────────────────┘
```

---

## 1.2 What is AWS?

Amazon Web Services (AWS) is the world's largest cloud platform, offering 200+ services.

### AWS Global Infrastructure

```
AWS Global Infrastructure
│
├── Regions (33+) ─── Geographic areas (e.g., us-east-1, ap-south-1)
│   │
│   ├── Availability Zones (AZs) ─── Isolated data centers within a region
│   │   ├── AZ-a (us-east-1a)
│   │   ├── AZ-b (us-east-1b)
│   │   └── AZ-c (us-east-1c)
│   │
│   └── Each region has 2-6 AZs
│
├── Edge Locations (400+) ─── CDN endpoints for CloudFront
│
└── Local Zones ─── Extensions of regions for low-latency
```

### Key AWS Regions

| Region Code | Location | Common Use |
|------------|----------|------------|
| `us-east-1` | N. Virginia | Default, most services available first |
| `us-west-2` | Oregon | Cost-effective, popular for dev |
| `eu-west-1` | Ireland | European workloads |
| `ap-south-1` | Mumbai | Indian subcontinent |
| `ap-southeast-1` | Singapore | Southeast Asia |

### Real-Life Example: Why Regions Matter
**Netflix** uses multiple AWS regions to serve content globally. When you watch a show in India, it's served from `ap-south-1` (Mumbai), not `us-east-1` (Virginia), reducing latency from ~200ms to ~20ms.

---

## 1.3 AWS Account Setup

### Step 1: Create an AWS Account

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Enter email, password, account name
4. Choose "Personal" or "Business" account
5. Enter payment information (credit/debit card required)
6. Verify phone number
7. Select "Basic Support - Free"

### Step 2: Secure Your Root Account

The root account has unrestricted access. Treat it like the master key to your house.

**Enable MFA (Multi-Factor Authentication):**
1. Sign in to AWS Console → IAM
2. Click "Add MFA" under Security Recommendations
3. Choose "Virtual MFA device"
4. Scan QR code with Google Authenticator / Authy
5. Enter two consecutive MFA codes
6. Click "Assign MFA"

⚠️ **NEVER use the root account for daily tasks. Create IAM users instead.**

### Step 3: Set Up Billing Alerts

```
AWS Console → Billing → Billing Preferences
  ✓ Receive Free Tier Usage Alerts
  ✓ Receive Billing Alerts
  Enter email address → Save
```

---

## 1.4 AWS CLI Installation & Configuration

### What is AWS CLI?
AWS CLI (Command Line Interface) lets you manage AWS services from your terminal instead of clicking through the web console.

### Installation

**Linux:**
```bash
# Download the installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip it
unzip awscliv2.zip

# Install
sudo ./aws/install

# Verify installation
aws --version
```

**Expected Output:**
```
aws-cli/2.15.30 Python/3.11.8 Linux/5.15.0 exe/x86_64.ubuntu.22
```

**macOS:**
```bash
# Download and install
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify
aws --version
```

**Windows:**
```powershell
# Download and run the MSI installer from:
# https://awscli.amazonaws.com/AWSCLIV2.msi

# After installation, verify in Command Prompt:
aws --version
```

### Configuration

First, create an IAM user with programmatic access (covered in Module 2), then:

```bash
aws configure
```

**Interactive Prompts and What to Enter:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

**What each field means:**
| Field | Meaning | Example |
|-------|---------|---------|
| Access Key ID | Your username for API access | `AKIA...` (20 chars) |
| Secret Access Key | Your password for API access | `wJal...` (40 chars) |
| Default region | Where commands run by default | `us-east-1` |
| Output format | How results are displayed | `json`, `table`, `text` |

### Verify Configuration

```bash
# Check who you are
aws sts get-caller-identity
```

**Expected Output:**
```json
{
    "UserId": "AIDAIOSFODNN7EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/my-user"
}
```

**Command Breakdown:**
- `aws` → AWS CLI tool
- `sts` → Security Token Service
- `get-caller-identity` → Returns details about the IAM user/role whose credentials are used

### Where Credentials Are Stored

```bash
# View credentials file
cat ~/.aws/credentials
```

**Output:**
```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

```bash
# View config file
cat ~/.aws/config
```

**Output:**
```ini
[default]
region = us-east-1
output = json
```

### Named Profiles (Multiple Accounts)

```bash
# Configure a second profile
aws configure --profile production
```

```
AWS Access Key ID [None]: AKIAI44QH8DHBEXAMPLE
AWS Secret Access Key [None]: je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
Default region name [None]: us-west-2
Default output format [None]: json
```

```bash
# Use a specific profile
aws s3 ls --profile production

# Set profile for entire session
export AWS_PROFILE=production
```

---

## 1.5 AWS Free Tier

### Three Types of Free Tier

| Type | Duration | Example |
|------|----------|---------|
| **Always Free** | Forever | 1M Lambda requests/month, 25GB DynamoDB |
| **12 Months Free** | First year | 750 hrs EC2 t2.micro, 5GB S3 |
| **Trials** | Service-specific | 60 days of Amazon Inspector |

### Key Free Tier Limits

```
EC2:        750 hours/month of t2.micro (Linux/Windows)
S3:         5 GB storage, 20,000 GET, 2,000 PUT requests
RDS:        750 hours/month of db.t2.micro
Lambda:     1 million requests/month
DynamoDB:   25 GB storage, 25 read/write capacity units
CloudFront: 1 TB data transfer out/month
SNS:        1 million publishes
SQS:        1 million requests
CloudWatch: 10 custom metrics, 10 alarms
```

### Check Free Tier Usage

```bash
# Via Console: Billing → Free Tier
# Via CLI:
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

**Expected Output:**
```json
{
    "ResultsByTime": [
        {
            "TimePeriod": {
                "Start": "2024-01-01",
                "End": "2024-01-31"
            },
            "Groups": [
                {
                    "Keys": ["Amazon Elastic Compute Cloud - Compute"],
                    "Metrics": {
                        "BlendedCost": {
                            "Amount": "0.0",
                            "Unit": "USD"
                        }
                    }
                }
            ]
        }
    ]
}
```

---

## 1.6 AWS Console Walkthrough

### Key Console Sections

```
┌──────────────────────────────────────────────────┐
│  AWS Management Console                           │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────┐ │
│  │ Services│  │ Search   │  │ Region Selector │ │
│  │ Menu    │  │ Bar      │  │ (top-right)     │ │
│  └─────────┘  └──────────┘  └─────────────────┘ │
│                                                   │
│  Recently Visited Services                        │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐               │
│  │ EC2 │ │ S3  │ │ IAM │ │ VPC │               │
│  └─────┘ └─────┘ └─────┘ └─────┘               │
│                                                   │
│  AWS Health Dashboard                             │
│  Cost & Usage Summary                             │
└──────────────────────────────────────────────────┘
```

### Important: Region Selection
- Most AWS services are **region-specific**
- Always check your region in the top-right corner
- IAM and S3 bucket names are **global**
- If you can't find a resource, you might be in the wrong region

---

## 1.7 AWS Pricing Model

### How AWS Charges

```
┌─────────────────────────────────────────┐
│         AWS Pricing Principles           │
├─────────────────────────────────────────┤
│                                          │
│  1. Pay-as-you-go                        │
│     └── Pay only for what you use        │
│                                          │
│  2. Save when you reserve                │
│     └── Up to 75% discount for 1-3 year  │
│         commitments                      │
│                                          │
│  3. Pay less by using more               │
│     └── Volume discounts (S3 tiers)      │
│                                          │
│  4. Data Transfer                        │
│     └── Inbound: FREE                    │
│     └── Outbound: Charged per GB         │
│     └── Between AZs: Charged             │
│     └── Same AZ: Free (private IP)       │
└─────────────────────────────────────────┘
```

### AWS Pricing Calculator

```bash
# Use the online calculator:
# https://calculator.aws/

# Or check prices via CLI:
aws pricing get-products \
  --service-code AmazonEC2 \
  --filters "Type=TERM_MATCH,Field=instanceType,Value=t3.micro" \
            "Type=TERM_MATCH,Field=location,Value=US East (N. Virginia)" \
  --region us-east-1
```

---

## 1.8 Common Errors & Troubleshooting

### Error 1: "Unable to locate credentials"
```
$ aws s3 ls
Unable to locate credentials. You can configure credentials by running "aws configure".
```
**Cause:** AWS CLI is not configured.
**Fix:**
```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### Error 2: "The security token included in the request is invalid"
```
An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation:
The security token included in the request is invalid.
```
**Cause:** Wrong or expired access keys.
**Fix:**
```bash
# Check current credentials
cat ~/.aws/credentials

# Reconfigure with correct keys
aws configure
```

### Error 3: "You are not authorized to perform this operation"
```
An error occurred (AccessDenied) when calling the ListBuckets operation:
Access Denied
```
**Cause:** IAM user lacks permissions.
**Fix:** Attach the required policy to the IAM user (covered in Module 2).

### Error 4: Wrong Region
```
$ aws ec2 describe-instances
{
    "Reservations": []
}
```
**Cause:** You're querying the wrong region.
**Fix:**
```bash
# Specify the correct region
aws ec2 describe-instances --region us-west-2

# Or change default region
aws configure set region us-west-2
```

### Error 5: "aws: command not found"
```
$ aws --version
bash: aws: command not found
```
**Cause:** AWS CLI not installed or not in PATH.
**Fix:**
```bash
# Check if installed elsewhere
which aws
find / -name "aws" 2>/dev/null

# Reinstall
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

---

## 1.9 Module 1 Practice Exercises

### Exercise 1: Verify Your Setup
```bash
# 1. Check AWS CLI version
aws --version

# 2. Verify your identity
aws sts get-caller-identity

# 3. List all regions
aws ec2 describe-regions --output table

# 4. Check your default region
aws configure get region
```

### Exercise 2: Explore AWS Services
```bash
# List all available services
aws help | head -100

# Get help for a specific service
aws ec2 help

# Get help for a specific command
aws ec2 describe-instances help
```

### Exercise 3: Output Formats
```bash
# JSON output (default)
aws sts get-caller-identity --output json

# Table output (human-readable)
aws sts get-caller-identity --output table

# Text output (for scripting)
aws sts get-caller-identity --output text
```

**JSON Output:**
```json
{
    "UserId": "AIDAIOSFODNN7EXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/my-user"
}
```

**Table Output:**
```
----------------------------------------------------------------------
|                        GetCallerIdentity                            |
+------------+------------------------+-------------------------------+
|   Account  |        Arn             |           UserId              |
+------------+------------------------+-------------------------------+
| 123456789012| arn:aws:iam::123456789012:user/my-user | AIDAIOSFODNN7EXAMPLE |
+------------+------------------------+-------------------------------+
```

**Text Output:**
```
AIDAIOSFODNN7EXAMPLE    123456789012    arn:aws:iam::123456789012:user/my-user
```

---

## 1.10 Key Takeaways

1. AWS is an IaaS/PaaS/SaaS provider with 200+ services
2. Regions contain Availability Zones; always know which region you're in
3. Never use root account for daily work
4. Enable MFA on root account immediately
5. Set up billing alerts to avoid surprise charges
6. AWS CLI is your primary tool for automation
7. Free Tier has limits — monitor usage regularly
