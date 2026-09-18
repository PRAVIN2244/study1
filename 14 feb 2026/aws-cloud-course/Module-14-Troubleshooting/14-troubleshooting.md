# Module 14: Common Errors & Troubleshooting Guide

## Quick Reference: Error → Fix

This module consolidates all common AWS errors with step-by-step troubleshooting.

---

## 14.1 Authentication & Authorization Errors

### Error: "Unable to locate credentials"
```
Unable to locate credentials. You can configure credentials by running "aws configure".
```
**Cause:** No AWS credentials configured.
**Fix:**
```bash
# Option 1: Configure credentials
aws configure

# Option 2: Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Option 3: Check credentials file
cat ~/.aws/credentials

# Option 4: Check if using IAM role (EC2)
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

### Error: "The security token included in the request is invalid"
```
An error occurred (InvalidClientTokenId)
```
**Cause:** Expired or incorrect access keys.
**Fix:**
```bash
# Verify current identity
aws sts get-caller-identity

# If using temporary credentials, check expiration
# Reconfigure with valid keys
aws configure

# If using SSO
aws sso login --profile my-profile
```

### Error: "Access Denied" / "Not authorized to perform"
```
An error occurred (AccessDenied) when calling the <Action> operation
```
**Troubleshooting Steps:**
```bash
# 1. Check who you are
aws sts get-caller-identity

# 2. Check your policies
aws iam list-attached-user-policies --user-name $(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)

# 3. Simulate the permission
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/myuser \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::my-bucket/*

# 4. Check for explicit DENY policies
# - Service Control Policies (AWS Organizations)
# - Permission boundaries
# - Resource-based policies (S3 bucket policy, KMS key policy)

# 5. Check if MFA is required
# Some policies deny access without MFA
```

### Error: "ExpiredToken"
```
An error occurred (ExpiredToken): The security token included in the request is expired
```
**Fix:**
```bash
# For SSO sessions
aws sso login

# For assumed roles, re-assume
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/MyRole --role-session-name session1

# For temporary credentials, request new ones
```

---

## 14.2 EC2 Errors

### Error: "InsufficientInstanceCapacity"
```
An error occurred (InsufficientInstanceCapacity)
```
**Fix:**
```bash
# Try different AZ
aws ec2 run-instances --availability-zone us-east-1b ...

# Try different instance type
# t3.micro → t3.small

# For Spot: try different instance types
aws ec2 run-instances --instance-market-options 'MarketType=spot' \
  --instance-type t3.small ...
```

### Error: SSH "Connection timed out"
**Troubleshooting:**
```bash
# 1. Check instance is running
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].State.Name'

# 2. Check public IP exists
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# 3. Check security group allows SSH
aws ec2 describe-security-groups --group-ids sg-xxx \
  --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]'

# 4. Check your IP
curl -s ifconfig.me
# Compare with security group CIDR

# 5. Check route table has internet gateway
aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=subnet-xxx" \
  --query 'RouteTables[0].Routes[?DestinationCidrBlock==`0.0.0.0/0`]'

# 6. Check NACL allows SSH
aws ec2 describe-network-acls \
  --filters "Name=association.subnet-id,Values=subnet-xxx"
```

### Error: SSH "Permission denied (publickey)"
```bash
# 1. Check file permissions
chmod 400 my-key.pem

# 2. Check correct username
# Amazon Linux / AL2023: ec2-user
# Ubuntu: ubuntu
# CentOS: centos
# Debian: admin
# RHEL: ec2-user

# 3. Check correct key pair
aws ec2 describe-instances --instance-ids i-xxx \
  --query 'Reservations[0].Instances[0].KeyName'

# 4. Correct SSH command
ssh -i my-key.pem -v ec2-user@<PUBLIC_IP>
# -v flag shows verbose debug output
```

### Error: Instance stuck in "stopping" or "pending"
```bash
# Force stop
aws ec2 stop-instances --instance-ids i-xxx --force

# Check system status
aws ec2 describe-instance-status --instance-ids i-xxx

# If truly stuck, contact AWS Support
```

### Error: "InvalidAMIID.NotFound"
```bash
# AMIs are region-specific
# Find correct AMI for your region
aws ec2 describe-images --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --region us-east-1
```

---

## 14.3 S3 Errors

### Error: "BucketAlreadyExists"
```bash
# Bucket names are globally unique
# Add a unique suffix
aws s3 mb s3://my-bucket-$(aws sts get-caller-identity --query 'Account' --output text)
```

### Error: "AccessDenied" on S3
```bash
# Troubleshooting checklist:

# 1. Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/myuser \
  --action-names s3:GetObject \
  --resource-arns arn:aws:s3:::my-bucket/file.txt

# 2. Check bucket policy
aws s3api get-bucket-policy --bucket my-bucket 2>/dev/null || echo "No bucket policy"

# 3. Check Block Public Access
aws s3api get-public-access-block --bucket my-bucket

# 4. Check object ACL
aws s3api get-object-acl --bucket my-bucket --key file.txt

# 5. Check if bucket is in another account
aws s3api get-bucket-acl --bucket my-bucket

# 6. Check KMS key permissions (if encrypted)
aws s3api head-object --bucket my-bucket --key file.txt
```

### Error: "NoSuchKey"
```bash
# Check if object exists (case-sensitive!)
aws s3 ls s3://my-bucket/ --recursive | grep -i "filename"

# Check for trailing slashes
aws s3 ls s3://my-bucket/path/to/file.txt
```

### Error: "EntityTooLarge" (>5GB single upload)
```bash
# Use multipart upload
aws configure set default.s3.multipart_threshold 64MB
aws s3 cp large-file.zip s3://my-bucket/
```

### Error: "SlowDown" (429 Too Many Requests)
```bash
# S3 rate limit: 5,500 GET/s and 3,500 PUT/s per prefix
# Solution: Distribute objects across prefixes
# Bad:  s3://bucket/data/file1, s3://bucket/data/file2
# Good: s3://bucket/a1/file1, s3://bucket/b2/file2
```

---

## 14.4 RDS Errors

### Error: Cannot connect to RDS
```bash
# Complete troubleshooting:

# 1. Is RDS available?
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].DBInstanceStatus'
# Must be "available"

# 2. Get endpoint
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].Endpoint'

# 3. Is it publicly accessible?
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].PubliclyAccessible'
# If false, connect from EC2 in same VPC

# 4. Check security group
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].VpcSecurityGroups'

# Then check if your source is allowed
aws ec2 describe-security-groups --group-ids sg-xxx

# 5. Test connectivity
nc -zv mydb.c9abc123.us-east-1.rds.amazonaws.com 3306
# or
telnet mydb.c9abc123.us-east-1.rds.amazonaws.com 3306

# 6. Check DNS resolution
nslookup mydb.c9abc123.us-east-1.rds.amazonaws.com
```

### Error: "Storage full"
```bash
# Check current storage
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[0].AllocatedStorage'

# Increase storage (no downtime)
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --allocated-storage 100 \
  --apply-immediately
```

### Error: "Too many connections"
```bash
# Check current connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=mydb \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Maximum

# Fix: Scale up instance or optimize connection pooling
aws rds modify-db-instance \
  --db-instance-identifier mydb \
  --db-instance-class db.t3.medium \
  --apply-immediately
```

---

## 14.5 Lambda Errors

### Error: "Task timed out"
```bash
# Increase timeout (max 15 minutes)
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 300

# Check if function is waiting on external resource
# - Database connection timeout
# - API call timeout
# - VPC cold start (add VPC endpoint or increase memory)
```

### Error: "Unable to import module"
```bash
# Check handler format: filename.function_name
# For lambda_function.py with def handler():
# Handler should be: lambda_function.handler

# Check if dependencies are included in zip
unzip -l function.zip

# For Python: pip install -t . requests
# For Node.js: npm install in same directory
```

### Error: "Runtime.ImportModuleError"
```bash
# Wrong runtime selected
aws lambda get-function-configuration --function-name my-function \
  --query 'Runtime'

# Update runtime
aws lambda update-function-configuration \
  --function-name my-function \
  --runtime python3.12
```

### Error: Lambda returns 502 from API Gateway
```bash
# Lambda must return specific format:
# {
#   "statusCode": 200,
#   "headers": {"Content-Type": "application/json"},
#   "body": "{\"key\": \"value\"}"  ← MUST be a string, not object
# }

# Check Lambda logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/my-function \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s000)
```

### Error: Lambda out of memory
```bash
# Check memory usage in logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/my-function \
  --filter-pattern "REPORT" \
  --query 'events[-1].message'

# Output: REPORT ... Max Memory Used: 128 MB

# Increase memory (CPU scales proportionally)
aws lambda update-function-configuration \
  --function-name my-function \
  --memory-size 512
```

---

## 14.6 ECS/EKS Errors

### Error: ECS task keeps stopping
```bash
# 1. Check stopped reason
aws ecs describe-tasks --cluster my-cluster --tasks <task-arn> \
  --query 'tasks[0].{Status:lastStatus,Reason:stoppedReason,ContainerReason:containers[0].reason}'

# Common reasons and fixes:
# "OutOfMemoryError" → Increase task memory in task definition
# "CannotPullContainerError" → Check ECR image exists, check IAM role
# "HealthCheckFailure" → Fix health check endpoint or increase startPeriod
# "Essential container exited" → Check application logs
```

### Error: "CannotPullContainerError"
```bash
# 1. Check image exists
aws ecr describe-images --repository-name myapp/web

# 2. Check task execution role
aws iam list-attached-role-policies --role-name ecsTaskExecutionRole
# Must have: AmazonECSTaskExecutionRolePolicy

# 3. Check network (Fargate needs NAT Gateway or VPC endpoint for ECR)
# Create ECR VPC endpoints:
aws ec2 create-vpc-endpoint --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.ecr.dkr \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-xxx
```

### Error: EKS pods in CrashLoopBackOff
```bash
# 1. Check pod events
kubectl describe pod <pod-name>

# 2. Check previous container logs
kubectl logs <pod-name> --previous

# 3. Check resource limits
kubectl top pod <pod-name>

# 4. Check if image exists
kubectl get pod <pod-name> -o jsonpath='{.spec.containers[0].image}'
```

---

## 14.7 VPC/Networking Errors

### Error: No internet access from EC2
```bash
# Decision tree:
# Is instance in PUBLIC subnet?
#   YES → Check: Public IP? IGW route? Security group outbound?
#   NO  → Check: NAT Gateway? NAT route? Security group outbound?

# Step-by-step:
INSTANCE_ID="i-xxx"

# Get subnet
SUBNET=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SubnetId' --output text)

# Check if public IP assigned
aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress'

# Check route table
RT=$(aws ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=$SUBNET" \
  --query 'RouteTables[0].RouteTableId' --output text)

aws ec2 describe-route-tables --route-table-ids $RT \
  --query 'RouteTables[0].Routes' --output table

# Look for: 0.0.0.0/0 → igw-xxx (public) or nat-xxx (private)

# Check security group outbound
SG=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)

aws ec2 describe-security-groups --group-ids $SG \
  --query 'SecurityGroups[0].IpPermissionsEgress'
```

### Error: "VpcLimitExceeded"
```bash
# Default: 5 VPCs per region
aws service-quotas get-service-quota \
  --service-code vpc \
  --quota-code L-F678F1CE

# Request increase
aws service-quotas request-service-quota-increase \
  --service-code vpc \
  --quota-code L-F678F1CE \
  --desired-value 10
```

---

## 14.8 CloudFormation Errors

### Error: Stack in ROLLBACK_COMPLETE
```bash
# 1. Find the failure reason
aws cloudformation describe-stack-events \
  --stack-name my-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].{Resource:LogicalResourceId,Reason:ResourceStatusReason}' \
  --output table

# 2. Must delete before recreating
aws cloudformation delete-stack --stack-name my-stack
aws cloudformation wait stack-delete-complete --stack-name my-stack

# 3. Fix the template and redeploy
aws cloudformation create-stack --stack-name my-stack --template-body file://fixed-template.yaml
```

### Error: "Template validation error"
```bash
# Validate before deploying
aws cloudformation validate-template --template-body file://template.yaml

# Common issues:
# - YAML indentation errors
# - Missing required properties
# - Invalid resource type names
# - Circular dependencies
```

### Error: Stack DELETE_FAILED
```bash
# Some resources can't be deleted (non-empty S3 bucket, etc.)
# 1. Empty the S3 bucket
aws s3 rm s3://bucket-name --recursive

# 2. Retry delete, skipping problematic resources
aws cloudformation delete-stack \
  --stack-name my-stack \
  --retain-resources LogicalResourceId1 LogicalResourceId2
```

---

## 14.9 Billing & Cost Errors

### Unexpected Charges

```bash
# 1. Check what's running
# EC2 instances
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?State.Name==`running`].{ID:InstanceId,Type:InstanceType,AZ:Placement.AvailabilityZone}' \
  --output table

# NAT Gateways ($0.045/hr each!)
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" \
  --query 'NatGateways[].{ID:NatGatewayId,Subnet:SubnetId}' \
  --output table

# Elastic IPs (charged when NOT attached)
aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].{IP:PublicIp,AllocID:AllocationId}' \
  --output table

# EBS volumes (charged even when unattached)
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query 'Volumes[].{ID:VolumeId,Size:Size,Type:VolumeType}' \
  --output table

# RDS instances
aws rds describe-db-instances \
  --query 'DBInstances[].{ID:DBInstanceIdentifier,Class:DBInstanceClass,Status:DBInstanceStatus}' \
  --output table

# Load Balancers
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[].{Name:LoadBalancerName,Type:Type}' \
  --output table

# 2. Check cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[-1].Groups[?Metrics.BlendedCost.Amount > `0.01`].{Service:Keys[0],Cost:Metrics.BlendedCost.Amount}' \
  --output table
```

### Cleanup Script (Delete Unused Resources)

```bash
#!/bin/bash
echo "=== AWS Resource Cleanup ==="

# Delete unattached EBS volumes
for vol in $(aws ec2 describe-volumes --filters "Name=status,Values=available" --query 'Volumes[].VolumeId' --output text); do
  echo "Deleting unattached volume: $vol"
  aws ec2 delete-volume --volume-id $vol
done

# Release unassociated Elastic IPs
for alloc in $(aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].AllocationId' --output text); do
  echo "Releasing EIP: $alloc"
  aws ec2 release-address --allocation-id $alloc
done

# Delete old snapshots (older than 30 days)
CUTOFF=$(date -d '30 days ago' +%Y-%m-%dT%H:%M:%S)
for snap in $(aws ec2 describe-snapshots --owner-ids self --query "Snapshots[?StartTime<'$CUTOFF'].SnapshotId" --output text); do
  echo "Deleting old snapshot: $snap"
  aws ec2 delete-snapshot --snapshot-id $snap
done

echo "Cleanup complete!"
```

---

## 14.10 General Troubleshooting Framework

When you encounter ANY AWS error, follow this framework:

```
Step 1: READ the error message carefully
  └── AWS error messages are usually descriptive

Step 2: CHECK identity and permissions
  └── aws sts get-caller-identity
  └── Do you have the right IAM permissions?

Step 3: CHECK the region
  └── aws configure get region
  └── Is the resource in a different region?

Step 4: CHECK the resource exists
  └── aws <service> describe-<resource> --<id>

Step 5: CHECK CloudWatch Logs
  └── aws logs filter-log-events --log-group-name <group> --filter-pattern "ERROR"

Step 6: CHECK CloudTrail (who did what?)
  └── aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=<action>

Step 7: CHECK service quotas
  └── aws service-quotas list-service-quotas --service-code <service>

Step 8: SEARCH AWS documentation
  └── https://docs.aws.amazon.com/
  └── https://repost.aws/ (community)

Step 9: CONTACT AWS Support
  └── AWS Console → Support → Create Case
```

### Useful Debug Commands

```bash
# Who am I?
aws sts get-caller-identity

# What region am I in?
aws configure get region

# What's my account ID?
aws sts get-caller-identity --query 'Account' --output text

# List all resources in a region (AWS Config)
aws configservice list-discovered-resources --resource-type AWS::EC2::Instance

# Check service health
# https://health.aws.amazon.com/health/status

# Check API call history
aws cloudtrail lookup-events --max-results 10 \
  --query 'Events[].{Time:EventTime,Event:EventName,User:Username}'

# Check service quotas
aws service-quotas list-service-quotas --service-code ec2 \
  --query 'Quotas[?Used > `0`].{Name:QuotaName,Used:UsageMetric,Value:Value}' \
  --output table
```

---

## 14.11 AWS Support Tiers

| Tier | Cost | Response Time | Features |
|------|------|--------------|----------|
| **Basic** | Free | No technical support | Documentation, forums |
| **Developer** | $29/mo | 12-24 hours | 1 contact, business hours |
| **Business** | $100/mo+ | 1-24 hours | Unlimited contacts, 24/7 |
| **Enterprise** | $15,000/mo+ | 15 min (critical) | TAM, concierge, 24/7 |

---

## 14.12 Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              AWS CLI Quick Reference                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Identity:    aws sts get-caller-identity                │
│  Region:      aws configure get region                   │
│  Profiles:    aws configure list-profiles                │
│                                                          │
│  EC2:         aws ec2 describe-instances                 │
│  S3:          aws s3 ls                                  │
│  IAM:         aws iam list-users                         │
│  RDS:         aws rds describe-db-instances              │
│  Lambda:      aws lambda list-functions                  │
│  ECS:         aws ecs list-clusters                      │
│  VPC:         aws ec2 describe-vpcs                      │
│                                                          │
│  Logs:        aws logs filter-log-events                 │
│  Metrics:     aws cloudwatch get-metric-statistics       │
│  Audit:       aws cloudtrail lookup-events               │
│  Cost:        aws ce get-cost-and-usage                  │
│                                                          │
│  Help:        aws <service> help                         │
│  Docs:        aws <service> <command> help               │
│                                                          │
│  Output:      --output json|table|text                   │
│  Filter:      --query 'JMESPath expression'              │
│  Region:      --region us-east-1                         │
│  Profile:     --profile production                       │
│  Debug:       --debug                                    │
└─────────────────────────────────────────────────────────┘
```
