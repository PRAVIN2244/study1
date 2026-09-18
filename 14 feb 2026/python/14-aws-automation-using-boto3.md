# Module 14 — AWS Automation with boto3

boto3 is the official AWS SDK for Python. It lets you manage AWS resources programmatically — EC2 instances, S3 buckets, IAM users, Lambda functions, and every other AWS service. If you can do it in the AWS console, you can automate it with boto3.

---

## Prerequisites

```bash
pip install boto3
```

Configure AWS credentials:

```bash
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region, Output format
```

Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

### Verify Connection

```python
import boto3

sts = boto3.client("sts")
identity = sts.get_caller_identity()

print(f"Account: {identity['Account']}")
print(f"User ARN: {identity['Arn']}")
```

**Output:**

```
Account: 123456789012
User ARN: arn:aws:iam::123456789012:user/devops-engineer
```

---

## Client vs Resource — Two Ways to Use boto3

boto3 offers two interfaces:

```python
import boto3

# Client — low-level, returns dictionaries
ec2_client = boto3.client("ec2")
response = ec2_client.describe_instances()
# response is a dict with nested dicts and lists

# Resource — high-level, returns objects
ec2_resource = boto3.resource("ec2")
instances = ec2_resource.instances.all()
# instances are objects with attributes and methods
```

**When to use which:**

- **Client** — when you need full control or the resource interface does not support the operation
- **Resource** — when you want cleaner, more Pythonic code

---

## EC2 — Managing Instances

### Listing Instances

```python
import boto3

ec2 = boto3.resource("ec2")

print(f"{'NAME':<25} {'ID':<20} {'TYPE':<12} {'STATE':<12} {'IP'}")
print("-" * 80)

for instance in ec2.instances.all():
    # Get the Name tag
    name = "N/A"
    for tag in (instance.tags or []):
        if tag["Key"] == "Name":
            name = tag["Value"]
    
    print(f"{name:<25} {instance.id:<20} {instance.instance_type:<12} "
          f"{instance.state['Name']:<12} {instance.public_ip_address or 'N/A'}")
```

**Output (example):**

```
NAME                      ID                   TYPE         STATE        IP
web-server-01             i-0abc123def456789   t3.small     running      54.123.45.67
api-server-01             i-0def789abc123456   t3.medium    running      54.234.56.78
dev-instance              i-0ghi456jkl789012   t2.micro     stopped      N/A
```

### Filtering Instances

```python
import boto3

ec2 = boto3.resource("ec2")

# Find all running instances with a specific tag
running = ec2.instances.filter(
    Filters=[
        {"Name": "instance-state-name", "Values": ["running"]},
        {"Name": "tag:Environment", "Values": ["production"]}
    ]
)

for instance in running:
    print(f"  {instance.id}: {instance.instance_type}")
```

### Starting and Stopping Instances

```python
import boto3

ec2 = boto3.resource("ec2")

def manage_instances(instance_ids, action):
    """Start or stop EC2 instances."""
    instances = ec2.instances.filter(InstanceIds=instance_ids)
    
    for instance in instances:
        name = "N/A"
        for tag in (instance.tags or []):
            if tag["Key"] == "Name":
                name = tag["Value"]
        
        if action == "start":
            instance.start()
            print(f"  Starting: {name} ({instance.id})")
        elif action == "stop":
            instance.stop()
            print(f"  Stopping: {name} ({instance.id})")

# Usage:
# manage_instances(["i-0abc123", "i-0def456"], "stop")
# manage_instances(["i-0abc123", "i-0def456"], "start")
```

### Launching a New Instance

```python
import boto3

ec2 = boto3.resource("ec2")

instances = ec2.create_instances(
    ImageId="ami-0c55b159cbfafe1f0",    # Amazon Linux 2
    InstanceType="t3.micro",
    MinCount=1,
    MaxCount=1,
    KeyName="my-key-pair",
    SecurityGroupIds=["sg-0abc123"],
    SubnetId="subnet-0def456",
    TagSpecifications=[{
        "ResourceType": "instance",
        "Tags": [
            {"Key": "Name", "Value": "automated-instance"},
            {"Key": "Environment", "Value": "dev"},
            {"Key": "ManagedBy", "Value": "python-automation"}
        ]
    }]
)

instance = instances[0]
print(f"Launched: {instance.id}")
print("Waiting for instance to be running...")
instance.wait_until_running()
instance.reload()
print(f"Public IP: {instance.public_ip_address}")
```

---

## S3 — Object Storage

### Listing Buckets

```python
import boto3

s3 = boto3.client("s3")

response = s3.list_buckets()

print("S3 Buckets:")
for bucket in response["Buckets"]:
    created = bucket["CreationDate"].strftime("%Y-%m-%d")
    print(f"  {bucket['Name']} (created: {created})")
```

### Uploading Files

```python
import boto3
from pathlib import Path

s3 = boto3.client("s3")

def upload_file(local_path, bucket, s3_key=None):
    """Upload a file to S3."""
    if s3_key is None:
        s3_key = Path(local_path).name
    
    s3.upload_file(local_path, bucket, s3_key)
    print(f"  Uploaded: {local_path} -> s3://{bucket}/{s3_key}")

def upload_directory(local_dir, bucket, s3_prefix=""):
    """Upload all files in a directory to S3."""
    local_path = Path(local_dir)
    
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            s3_key = f"{s3_prefix}/{file_path.relative_to(local_path)}"
            upload_file(str(file_path), bucket, s3_key)

# Usage:
# upload_file("report.pdf", "my-bucket", "reports/2024/report.pdf")
# upload_directory("./build", "my-bucket", "releases/v1.2.3")
```

### Downloading Files

```python
import boto3

s3 = boto3.client("s3")

s3.download_file("my-bucket", "config/app.json", "app.json")
print("Downloaded app.json")
```

### Listing Objects in a Bucket

```python
import boto3

s3 = boto3.client("s3")

def list_objects(bucket, prefix=""):
    """List all objects in an S3 bucket with a given prefix."""
    paginator = s3.get_paginator("list_objects_v2")
    
    total_size = 0
    total_count = 0
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            size_kb = obj["Size"] / 1024
            modified = obj["LastModified"].strftime("%Y-%m-%d %H:%M")
            print(f"  {obj['Key']:<50} {size_kb:>8.1f} KB  {modified}")
            total_size += obj["Size"]
            total_count += 1
    
    print(f"\nTotal: {total_count} objects, {total_size / 1024 / 1024:.1f} MB")

# Usage:
# list_objects("my-bucket", prefix="logs/2024/")
```

**Why use a paginator:** S3 returns at most 1000 objects per request. The paginator automatically handles multiple requests to get all objects.

### S3 Bucket Cleanup

```python
import boto3
from datetime import datetime, timezone, timedelta

def cleanup_old_objects(bucket, prefix, days=30, dry_run=True):
    """Delete S3 objects older than N days."""
    s3 = boto3.client("s3")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    paginator = s3.get_paginator("list_objects_v2")
    to_delete = []
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                to_delete.append(obj["Key"])
    
    print(f"Found {len(to_delete)} objects older than {days} days")
    
    if not to_delete:
        return
    
    if dry_run:
        for key in to_delete[:5]:
            print(f"  [DRY RUN] Would delete: {key}")
        if len(to_delete) > 5:
            print(f"  ... and {len(to_delete) - 5} more")
    else:
        # Delete in batches of 1000 (S3 limit)
        for i in range(0, len(to_delete), 1000):
            batch = to_delete[i:i+1000]
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": k} for k in batch]}
            )
        print(f"Deleted {len(to_delete)} objects")

# Usage:
# cleanup_old_objects("my-bucket", "logs/", days=90, dry_run=True)
```

---

## IAM — Identity and Access Management

### Listing Users

```python
import boto3

iam = boto3.client("iam")

paginator = iam.get_paginator("list_users")

print(f"{'USERNAME':<25} {'CREATED':<15} {'LAST ACTIVITY'}")
print("-" * 60)

for page in paginator.paginate():
    for user in page["Users"]:
        created = user["CreateDate"].strftime("%Y-%m-%d")
        last_used = user.get("PasswordLastUsed")
        last_activity = last_used.strftime("%Y-%m-%d") if last_used else "Never"
        print(f"{user['UserName']:<25} {created:<15} {last_activity}")
```

### Finding Unused Access Keys

```python
import boto3
from datetime import datetime, timezone, timedelta

def find_old_access_keys(days=90):
    """Find access keys not used in the last N days."""
    iam = boto3.client("iam")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    findings = []
    
    for page in iam.get_paginator("list_users").paginate():
        for user in page["Users"]:
            keys = iam.list_access_keys(UserName=user["UserName"])
            
            for key in keys["AccessKeyMetadata"]:
                if key["Status"] != "Active":
                    continue
                
                last_used = iam.get_access_key_last_used(
                    AccessKeyId=key["AccessKeyId"]
                )
                
                last_used_date = last_used["AccessKeyLastUsed"].get("LastUsedDate")
                
                if last_used_date is None or last_used_date < cutoff:
                    age = (datetime.now(timezone.utc) - key["CreateDate"]).days
                    findings.append({
                        "user": user["UserName"],
                        "key_id": key["AccessKeyId"],
                        "age_days": age,
                        "last_used": last_used_date.strftime("%Y-%m-%d") if last_used_date else "Never"
                    })
    
    print(f"\nAccess keys not used in {days}+ days:")
    for f in findings:
        print(f"  {f['user']}: {f['key_id']} "
              f"(age: {f['age_days']}d, last used: {f['last_used']})")
    
    return findings

# Usage:
# find_old_access_keys(days=90)
```

---

## Infrastructure Audit

```python
import boto3

def audit_aws_infrastructure(region="us-east-1"):
    """Audit AWS infrastructure for common issues."""
    findings = []
    
    # Check 1: Unencrypted S3 buckets
    s3 = boto3.client("s3", region_name=region)
    buckets = s3.list_buckets()["Buckets"]
    
    for bucket in buckets:
        try:
            s3.get_bucket_encryption(Bucket=bucket["Name"])
        except s3.exceptions.ClientError:
            findings.append({
                "severity": "HIGH",
                "service": "S3",
                "resource": bucket["Name"],
                "issue": "Bucket encryption not enabled"
            })
    
    # Check 2: Public security groups
    ec2 = boto3.client("ec2", region_name=region)
    sgs = ec2.describe_security_groups()["SecurityGroups"]
    
    for sg in sgs:
        for rule in sg.get("IpPermissions", []):
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    port = rule.get("FromPort", "all")
                    findings.append({
                        "severity": "HIGH",
                        "service": "EC2",
                        "resource": f"{sg['GroupId']} ({sg['GroupName']})",
                        "issue": f"Port {port} open to 0.0.0.0/0"
                    })
    
    # Check 3: Unattached EBS volumes
    volumes = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )["Volumes"]
    
    for vol in volumes:
        size = vol["Size"]
        findings.append({
            "severity": "MEDIUM",
            "service": "EBS",
            "resource": vol["VolumeId"],
            "issue": f"Unattached volume ({size} GB) — wasting money"
        })
    
    # Print report
    print(f"\nAWS Infrastructure Audit ({region})")
    print("=" * 60)
    print(f"Findings: {len(findings)}")
    
    for f in sorted(findings, key=lambda x: x["severity"]):
        icon = {"HIGH": "[!!]", "MEDIUM": "[!]", "LOW": "[i]"}[f["severity"]]
        print(f"\n  {icon} {f['severity']} — {f['service']}: {f['resource']}")
        print(f"      {f['issue']}")
    
    if not findings:
        print("\nNo issues found!")

# Usage:
# audit_aws_infrastructure("us-east-1")
```

---

## Cost Optimization

```python
import boto3
from datetime import datetime, timezone, timedelta

def find_idle_instances(region="us-east-1", cpu_threshold=5, days=7):
    """Find EC2 instances with low CPU usage (candidates for downsizing)."""
    ec2 = boto3.resource("ec2", region_name=region)
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    idle_instances = []
    
    for instance in ec2.instances.filter(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    ):
        # Get average CPU utilization
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance.id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,    # 1 day
            Statistics=["Average"]
        )
        
        if response["Datapoints"]:
            avg_cpu = sum(d["Average"] for d in response["Datapoints"]) / len(response["Datapoints"])
            
            if avg_cpu < cpu_threshold:
                name = "N/A"
                for tag in (instance.tags or []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                
                idle_instances.append({
                    "id": instance.id,
                    "name": name,
                    "type": instance.instance_type,
                    "avg_cpu": avg_cpu
                })
    
    print(f"\nIdle Instances (avg CPU < {cpu_threshold}% over {days} days):")
    for inst in idle_instances:
        print(f"  {inst['name']} ({inst['id']}): "
              f"{inst['type']}, avg CPU: {inst['avg_cpu']:.1f}%")
    
    return idle_instances

# Usage:
# find_idle_instances(cpu_threshold=5, days=7)
```

---

## Exercises

**Exercise 1:** Write a script that lists all EC2 instances across all regions and shows their state, type, and name tag.

**Exercise 2:** Write an S3 backup script that uploads a local directory to S3 with a date-based prefix (e.g., `backups/2024-01-15/`).

**Exercise 3:** Write a security audit that checks for S3 buckets with public access, security groups open to the internet, and IAM users without MFA.

**Exercise 4:** Build a cost report that lists all running EC2 instances grouped by instance type, with estimated monthly cost.

---

## Common Mistakes

### 1. Hardcoding Credentials

```python
# Bad — credentials in code
client = boto3.client("s3",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="secret..."
)

# Good — use environment variables or IAM roles
client = boto3.client("s3")    # Uses default credential chain
```

### 2. Not Using Paginators

```python
# Bad — only gets first 1000 objects
response = s3.list_objects_v2(Bucket="my-bucket")

# Good — gets all objects
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket="my-bucket"):
    for obj in page.get("Contents", []):
        process(obj)
```

### 3. Not Handling AWS Errors

```python
from botocore.exceptions import ClientError

try:
    s3.head_bucket(Bucket="my-bucket")
except ClientError as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "404":
        print("Bucket does not exist")
    elif error_code == "403":
        print("Access denied")
```

### 4. Not Specifying Region

```python
# Bad — uses default region, may not find resources
client = boto3.client("ec2")

# Good — explicit region
client = boto3.client("ec2", region_name="us-west-2")
```

---

## Summary

| Service | Client | Common Operations |
|---------|--------|-------------------|
| EC2 | `boto3.resource("ec2")` | List, start, stop, launch instances |
| S3 | `boto3.client("s3")` | Upload, download, list, delete objects |
| IAM | `boto3.client("iam")` | List users, audit access keys |
| CloudWatch | `boto3.client("cloudwatch")` | Get metrics, set alarms |
| STS | `boto3.client("sts")` | Get caller identity |

---

[Previous: Module 13 — Kubernetes Automation](13-kubernetes-automation.md) | [Next: Module 15 — CI/CD Automation](15-cicd-automation.md)
