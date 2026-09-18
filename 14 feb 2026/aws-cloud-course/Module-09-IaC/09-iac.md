# Module 9: CloudFormation & Infrastructure as Code

## 9.1 What is Infrastructure as Code (IaC)?

IaC means defining your infrastructure in code files instead of clicking through the console.

### Real-World Analogy
- **Manual (Console)** = Building a house by verbal instructions (error-prone, not repeatable)
- **IaC** = Building from blueprints (consistent, version-controlled, repeatable)

### Benefits
- **Reproducibility**: Deploy identical environments (dev, staging, prod)
- **Version Control**: Track changes via Git
- **Automation**: No manual clicking
- **Documentation**: Code IS the documentation
- **Disaster Recovery**: Recreate entire infrastructure from code

### IaC Tools on AWS

| Tool | Type | Language | Provider |
|------|------|----------|----------|
| **CloudFormation** | Declarative | YAML/JSON | AWS-native |
| **CDK** | Imperative | Python/TS/Java | AWS (generates CFN) |
| **Terraform** | Declarative | HCL | HashiCorp (multi-cloud) |
| **Pulumi** | Imperative | Python/TS/Go | Multi-cloud |

---

## 9.2 CloudFormation Basics

### Template Structure

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: My infrastructure template

Parameters:        # Input variables
  EnvironmentName:
    Type: String
    Default: dev

Mappings:          # Static lookup tables
  RegionMap:
    us-east-1:
      AMI: ami-0c55b159cbfafe1f0

Conditions:        # Conditional resource creation
  IsProduction: !Equals [!Ref EnvironmentName, production]

Resources:         # AWS resources (REQUIRED)
  MyEC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.micro
      ImageId: !FindInMap [RegionMap, !Ref 'AWS::Region', AMI]

Outputs:           # Return values
  InstanceId:
    Value: !Ref MyEC2Instance
    Description: EC2 Instance ID
```

### Create a Simple Stack

```bash
# Create template file
cat > simple-stack.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: Simple S3 bucket with versioning

Parameters:
  BucketName:
    Type: String
    Description: Name of the S3 bucket
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, production]

Resources:
  MyBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${BucketName}-${Environment}'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      Tags:
        - Key: Environment
          Value: !Ref Environment

Outputs:
  BucketArn:
    Value: !GetAtt MyBucket.Arn
    Description: S3 Bucket ARN
  BucketURL:
    Value: !Sub 'https://${MyBucket.DomainName}'
    Description: S3 Bucket URL
EOF

# Deploy the stack
aws cloudformation create-stack \
  --stack-name my-s3-stack \
  --template-body file://simple-stack.yaml \
  --parameters \
    ParameterKey=BucketName,ParameterValue=mycompany-data \
    ParameterKey=Environment,ParameterValue=dev
```

**Expected Output:**
```json
{
    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/my-s3-stack/abc123"
}
```

### Monitor Stack Creation

```bash
# Wait for completion
aws cloudformation wait stack-create-complete --stack-name my-s3-stack

# Check status
aws cloudformation describe-stacks \
  --stack-name my-s3-stack \
  --query 'Stacks[0].{Status:StackStatus,Outputs:Outputs}' \
  --output table

# View events (troubleshooting)
aws cloudformation describe-stack-events \
  --stack-name my-s3-stack \
  --query 'StackEvents[0:5].{Time:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}' \
  --output table
```

### Update a Stack

```bash
aws cloudformation update-stack \
  --stack-name my-s3-stack \
  --template-body file://simple-stack.yaml \
  --parameters \
    ParameterKey=BucketName,ParameterValue=mycompany-data \
    ParameterKey=Environment,ParameterValue=staging
```

### Delete a Stack

```bash
aws cloudformation delete-stack --stack-name my-s3-stack
aws cloudformation wait stack-delete-complete --stack-name my-s3-stack
```

---

## 9.3 CloudFormation Intrinsic Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `!Ref` | Reference parameter or resource | `!Ref MyBucket` |
| `!Sub` | String substitution | `!Sub '${AWS::StackName}-bucket'` |
| `!GetAtt` | Get resource attribute | `!GetAtt MyBucket.Arn` |
| `!Join` | Join strings | `!Join ['-', [my, bucket]]` |
| `!Select` | Select from list | `!Select [0, !GetAZs '']` |
| `!Split` | Split string | `!Split [',', 'a,b,c']` |
| `!If` | Conditional value | `!If [IsProduction, t3.large, t3.micro]` |
| `!FindInMap` | Lookup from mappings | `!FindInMap [RegionMap, !Ref 'AWS::Region', AMI]` |
| `!ImportValue` | Cross-stack reference | `!ImportValue VPC-ID` |

### Pseudo Parameters

| Parameter | Value |
|-----------|-------|
| `AWS::AccountId` | `123456789012` |
| `AWS::Region` | `us-east-1` |
| `AWS::StackName` | `my-stack` |
| `AWS::StackId` | Full stack ARN |
| `AWS::NoValue` | Removes property |

---

## 9.4 Production VPC Stack

```bash
cat > vpc-stack.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: Production VPC with public and private subnets

Parameters:
  ProjectName:
    Type: String
    Default: myapp
  VpcCIDR:
    Type: String
    Default: 10.0.0.0/16

Resources:
  # --- VPC ---
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCIDR
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-vpc'

  # --- Internet Gateway ---
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # --- Public Subnets ---
  PublicSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-public-a'

  PublicSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-public-b'

  # --- Private Subnets ---
  PrivateSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.3.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-private-a'

  PrivateSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.4.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-private-b'

  # --- NAT Gateway ---
  NatEIP:
    Type: AWS::EC2::EIP
    Properties:
      Domain: vpc

  NatGateway:
    Type: AWS::EC2::NatGateway
    Properties:
      AllocationId: !GetAtt NatEIP.AllocationId
      SubnetId: !Ref PublicSubnetA
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-nat'

  # --- Route Tables ---
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-public-rt'

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  PublicSubnetARouteAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnetA
      RouteTableId: !Ref PublicRouteTable

  PublicSubnetBRouteAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnetB
      RouteTableId: !Ref PublicRouteTable

  PrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${ProjectName}-private-rt'

  PrivateRoute:
    Type: AWS::EC2::Route
    Properties:
      RouteTableId: !Ref PrivateRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      NatGatewayId: !Ref NatGateway

  PrivateSubnetARouteAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateSubnetA
      RouteTableId: !Ref PrivateRouteTable

  PrivateSubnetBRouteAssoc:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PrivateSubnetB
      RouteTableId: !Ref PrivateRouteTable

Outputs:
  VpcId:
    Value: !Ref VPC
    Export:
      Name: !Sub '${ProjectName}-VpcId'
  PublicSubnets:
    Value: !Join [',', [!Ref PublicSubnetA, !Ref PublicSubnetB]]
    Export:
      Name: !Sub '${ProjectName}-PublicSubnets'
  PrivateSubnets:
    Value: !Join [',', [!Ref PrivateSubnetA, !Ref PrivateSubnetB]]
    Export:
      Name: !Sub '${ProjectName}-PrivateSubnets'
EOF

# Deploy
aws cloudformation create-stack \
  --stack-name myapp-vpc \
  --template-body file://vpc-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=myapp

# Wait
aws cloudformation wait stack-create-complete --stack-name myapp-vpc
```

---

## 9.5 Terraform Basics

Terraform uses HCL (HashiCorp Configuration Language) and works with multiple cloud providers.

### Install Terraform

```bash
# Linux
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform -y

# Verify
terraform version
```

**Expected Output:**
```
Terraform v1.7.0
```

### Terraform Project Structure

```
my-terraform-project/
├── main.tf          # Main resources
├── variables.tf     # Input variables
├── outputs.tf       # Output values
├── providers.tf     # Provider configuration
├── terraform.tfvars # Variable values (don't commit secrets)
└── modules/         # Reusable modules
    └── vpc/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Provider Configuration

```bash
cat > providers.tf << 'EOF'
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "mycompany-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      ManagedBy   = "terraform"
      Project     = var.project_name
      Environment = var.environment
    }
  }
}
EOF
```

### Variables

```bash
cat > variables.tf << 'EOF'
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
EOF

cat > terraform.tfvars << 'EOF'
project_name = "myapp"
environment  = "production"
aws_region   = "us-east-1"
EOF
```

### Main Resources

```bash
cat > main.tf << 'EOF'
# --- VPC ---
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# --- Subnets ---
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index + 1)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 3)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-${count.index + 1}"
  }
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# --- EC2 Instance ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-USERDATA
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
  USERDATA

  tags = {
    Name = "${var.project_name}-web"
  }
}

resource "aws_security_group" "web" {
  name_prefix = "${var.project_name}-web-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
EOF
```

### Outputs

```bash
cat > outputs.tf << 'EOF'
output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "public_subnets" {
  value       = aws_subnet.public[*].id
  description = "Public subnet IDs"
}

output "instance_public_ip" {
  value       = aws_instance.web.public_ip
  description = "Web server public IP"
}
EOF
```

### Terraform Workflow

```bash
# 1. Initialize (download providers)
terraform init
# Output: Initializing provider plugins... Terraform has been successfully initialized!

# 2. Format code
terraform fmt

# 3. Validate syntax
terraform validate
# Output: Success! The configuration is valid.

# 4. Plan (preview changes)
terraform plan
# Shows: + create, ~ modify, - destroy

# 5. Apply (create resources)
terraform apply
# Type "yes" to confirm

# 6. Show current state
terraform show

# 7. List resources
terraform state list

# 8. Destroy everything
terraform destroy
```

### Terraform State Commands

```bash
# List all resources in state
terraform state list

# Show details of a resource
terraform state show aws_instance.web

# Move a resource (rename)
terraform state mv aws_instance.web aws_instance.app

# Remove from state (without destroying)
terraform state rm aws_instance.web

# Import existing resource
terraform import aws_instance.web i-0abcd1234efgh5678
```

---

## 9.6 Common Errors & Troubleshooting

### CloudFormation Error 1: "ROLLBACK_COMPLETE"
```bash
# View failure reason
aws cloudformation describe-stack-events \
  --stack-name my-stack \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].{Resource:LogicalResourceId,Reason:ResourceStatusReason}' \
  --output table

# Must delete before recreating
aws cloudformation delete-stack --stack-name my-stack
```

### CloudFormation Error 2: "Template validation error"
```bash
# Validate template before deploying
aws cloudformation validate-template --template-body file://template.yaml
```

### Terraform Error 1: "Error acquiring the state lock"
```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Terraform Error 2: "Provider configuration not present"
```bash
# Re-initialize
terraform init -upgrade
```

---

## 9.7 Key Takeaways

1. IaC = reproducible, version-controlled infrastructure
2. CloudFormation is AWS-native; Terraform is multi-cloud
3. Always use remote state (S3 + DynamoDB for locking) in Terraform
4. Use `terraform plan` before every `terraform apply`
5. Use CloudFormation exports/imports for cross-stack references
6. Never store secrets in IaC files — use SSM Parameter Store or Secrets Manager
7. Use modules for reusable infrastructure components
8. Tag all resources for cost tracking and organization
