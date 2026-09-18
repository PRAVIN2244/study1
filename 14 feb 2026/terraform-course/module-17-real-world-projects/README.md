# Module 17: Real-World Projects

## Level: SUPER ADVANCED | Estimated Time: 5 hours

---

## 17.1 Project 1: Production-Ready Three-Tier Web Application

### Architecture

```
Internet
    │
┌───▼───────────────────────────────────────────────────┐
│   ALB (Application Load Balancer)                     │
│   - HTTPS termination                                 │
│   - Health checks                                     │
└───┬───────────────────────────────────────────────────┘
    │
┌───▼───────────────────────────────────────────────────┐
│   Auto Scaling Group (Private Subnets)                │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│   │  EC2    │  │  EC2    │  │  EC2    │             │
│   │  App    │  │  App    │  │  App    │             │
│   └─────────┘  └─────────┘  └─────────┘             │
└───┬───────────────────────────────────────────────────┘
    │
┌───▼───────────────────────────────────────────────────┐
│   RDS Aurora (Multi-AZ)                               │
│   ┌──────────┐     ┌──────────┐                      │
│   │  Writer  │────▶│  Reader  │                      │
│   └──────────┘     └──────────┘                      │
└───────────────────────────────────────────────────────┘
```

### File Structure

```
three-tier-app/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── locals.tf
├── modules/
│   ├── networking/
│   ├── compute/
│   └── database/
├── environments/
│   ├── dev.tfvars
│   └── prod.tfvars
└── tests/
    └── basic.tftest.hcl
```

### Networking Module

```hcl
# modules/networking/main.tf

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${var.name}-vpc" }
}

resource "aws_subnet" "public" {
  count                   = length(var.azs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "${var.name}-public-${var.azs[count.index]}" }
}

resource "aws_subnet" "private" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = var.azs[count.index]
  tags = { Name = "${var.name}-private-${var.azs[count.index]}" }
}

resource "aws_subnet" "database" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 20)
  availability_zone = var.azs[count.index]
  tags = { Name = "${var.name}-db-${var.azs[count.index]}" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name}-igw" }
}

resource "aws_eip" "nat" {
  count  = var.enable_nat ? 1 : 0
  domain = "vpc"
}

resource "aws_nat_gateway" "this" {
  count         = var.enable_nat ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  depends_on    = [aws_internet_gateway.this]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  dynamic "route" {
    for_each = var.enable_nat ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this[0].id
    }
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

### Compute Module (ALB + ASG)

```hcl
# modules/compute/main.tf

resource "aws_security_group" "alb" {
  name   = "${var.name}-alb-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
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

resource "aws_security_group" "app" {
  name   = "${var.name}-app-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "this" {
  name               = "${var.name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids
}

resource "aws_lb_target_group" "this" {
  name     = "${var.name}-tg"
  port     = var.app_port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_launch_template" "this" {
  name_prefix   = "${var.name}-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.app.id]

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    app_port    = var.app_port
    environment = var.environment
    db_endpoint = var.db_endpoint
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.name}-app"
    }
  }
}

resource "aws_autoscaling_group" "this" {
  name                = "${var.name}-asg"
  min_size            = var.min_size
  max_size            = var.max_size
  desired_capacity    = var.desired_size
  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [aws_lb_target_group.this.arn]
  health_check_type   = "ELB"

  launch_template {
    id      = aws_launch_template.this.id
    version = "$Latest"
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.name}-scale-up"
  autoscaling_group_name = aws_autoscaling_group.this.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = 1
  cooldown               = 300
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 70
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.this.name
  }
}
```

### Database Module

```hcl
# modules/database/main.tf

resource "aws_security_group" "db" {
  name   = "${var.name}-db-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = var.app_security_group_ids
  }
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db-subnet"
  subnet_ids = var.database_subnet_ids
}

resource "aws_rds_cluster" "this" {
  cluster_identifier     = "${var.name}-cluster"
  engine                 = "aurora-mysql"
  engine_version         = "8.0.mysql_aurora.3.04.0"
  database_name          = var.db_name
  master_username        = var.db_username
  master_password        = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = var.environment != "prod"

  backup_retention_period = var.environment == "prod" ? 30 : 1
  deletion_protection     = var.environment == "prod"
}

resource "aws_rds_cluster_instance" "this" {
  count              = var.environment == "prod" ? 2 : 1
  identifier         = "${var.name}-instance-${count.index}"
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.this.engine
}
```

### Root Module Composition

```hcl
# main.tf
module "networking" {
  source     = "./modules/networking"
  name       = local.name
  vpc_cidr   = var.vpc_cidr
  azs        = var.azs
  enable_nat = var.environment == "prod"
}

module "compute" {
  source             = "./modules/compute"
  name               = local.name
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  ami_id             = data.aws_ami.amazon_linux.id
  instance_type      = var.instance_type
  min_size           = var.min_size
  max_size           = var.max_size
  desired_size       = var.desired_size
  app_port           = 8080
  environment        = var.environment
  db_endpoint        = module.database.cluster_endpoint
}

module "database" {
  source                 = "./modules/database"
  name                   = local.name
  vpc_id                 = module.networking.vpc_id
  database_subnet_ids    = module.networking.database_subnet_ids
  app_security_group_ids = [module.compute.app_security_group_id]
  db_name                = var.db_name
  db_username            = var.db_username
  db_password            = var.db_password
  db_instance_class      = var.db_instance_class
  environment            = var.environment
}
```

---

## 17.2 Project 2: Serverless API with Lambda + API Gateway

```hcl
# Lambda function
resource "aws_lambda_function" "api" {
  filename         = data.archive_file.lambda.output_path
  function_name    = "${var.name}-api"
  role             = aws_iam_role.lambda.arn
  handler          = "index.handler"
  runtime          = "nodejs20.x"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      TABLE_NAME  = aws_dynamodb_table.this.name
      ENVIRONMENT = var.environment
    }
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/src"
  output_path = "${path.module}/lambda/function.zip"
}

# API Gateway
resource "aws_apigatewayv2_api" "this" {
  name          = "${var.name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["Content-Type", "Authorization"]
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "apigw" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# DynamoDB table
resource "aws_dynamodb_table" "this" {
  name         = "${var.name}-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }
}

output "api_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}
```

---

## 17.3 Project 3: EKS Cluster

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.name}-eks"
  cluster_version = "1.29"

  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    general = {
      desired_size = 2
      min_size     = 1
      max_size     = 5

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "general"
      }
    }

    spot = {
      desired_size = 2
      min_size     = 0
      max_size     = 10

      instance_types = ["t3.medium", "t3.large"]
      capacity_type  = "SPOT"

      labels = {
        role = "spot-workers"
      }

      taints = [{
        key    = "spot"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
  }
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "kubeconfig_command" {
  value = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.region}"
}
```

---

## 17.3.1 Detailed EKS Provisioning with Custom Modules

When you need full control over EKS (instead of using the community module), build it from individual resources. This approach is common in enterprises with strict security requirements.

### VPC Module for EKS

EKS requires a VPC with both public and private subnets across multiple AZs, plus specific Kubernetes tags:

```hcl
# modules/vpc/main.tf

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name                                        = "${var.cluster_name}-vpc"
    "kubernetes.io/cluster/${var.cluster_name}"  = "shared"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name                                        = "${var.cluster_name}-private-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}"  = "shared"
    "kubernetes.io/role/internal-elb"            = "1"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name                                        = "${var.cluster_name}-public-${count.index + 1}"
    "kubernetes.io/cluster/${var.cluster_name}"  = "shared"
    "kubernetes.io/role/elb"                     = "1"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.cluster_name}-igw" }
}

resource "aws_eip" "nat" {
  count  = length(var.public_subnet_cidrs)
  domain = "vpc"
  tags   = { Name = "${var.cluster_name}-nat-${count.index + 1}" }
}

resource "aws_nat_gateway" "main" {
  count         = length(var.public_subnet_cidrs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  tags          = { Name = "${var.cluster_name}-nat-${count.index + 1}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.cluster_name}-public" }
}

resource "aws_route_table" "private" {
  count  = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  tags = { Name = "${var.cluster_name}-private-${count.index + 1}" }
}

resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

### EKS Module with IAM Roles

```hcl
# modules/eks/main.tf

# IAM Role for EKS Control Plane
resource "aws_iam_role" "eks_cluster" {
  name = "${var.cluster_name}-eks-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.cluster_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy]
}

# IAM Role for Worker Nodes
resource "aws_iam_role" "eks_nodes" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "eks_cni" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_nodes.name
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_nodes.name
}

# Managed Node Group
resource "aws_eks_node_group" "main" {
  for_each = var.node_groups

  cluster_name    = aws_eks_cluster.main.name
  node_group_name = each.key
  node_role_arn   = aws_iam_role.eks_nodes.arn
  subnet_ids      = var.subnet_ids
  instance_types  = each.value.instance_types
  capacity_type   = each.value.capacity_type

  scaling_config {
    desired_size = each.value.scaling_config.desired_size
    max_size     = each.value.scaling_config.max_size
    min_size     = each.value.scaling_config.min_size
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node,
    aws_iam_role_policy_attachment.eks_cni,
    aws_iam_role_policy_attachment.ecr_read,
  ]
}
```

### Root Configuration with Remote Backend

```hcl
# main.tf (root)

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "my-terraform-eks-state"
    key            = "eks/terraform.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-eks-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.region
}

module "vpc" {
  source               = "./modules/vpc"
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnet_cidrs  = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
  cluster_name         = "my-eks-cluster"
}

module "eks" {
  source          = "./modules/eks"
  cluster_name    = "my-eks-cluster"
  cluster_version = "1.30"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids

  node_groups = {
    general = {
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
      scaling_config = {
        desired_size = 2
        max_size     = 4
        min_size     = 1
      }
    }
  }
}
```

### Deployment Commands

```bash
# Initialize and deploy
terraform init
terraform plan
terraform apply

# Connect to the cluster
aws eks update-kubeconfig --region us-west-2 --name my-eks-cluster

# Verify
kubectl get nodes
kubectl config current-context

# Clean up
terraform destroy
```

**Sample output after `kubectl get nodes`:**

```
NAME                                       STATUS   ROLES    AGE   VERSION
ip-10-0-1-45.us-west-2.compute.internal   Ready    <none>   5m    v1.30.0
ip-10-0-2-78.us-west-2.compute.internal   Ready    <none>   5m    v1.30.0
```

---

## 17.3.2 Scaling GCP Infrastructure with Terraform

### GCP Provider Configuration

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

### Compute Scaling: Managed Instance Groups with Autoscaler

```hcl
# Instance template — blueprint for VMs
resource "google_compute_instance_template" "web" {
  name_prefix  = "web-template-"
  machine_type = "e2-medium"
  region       = "us-central1"

  disk {
    source_image = "debian-cloud/debian-12"
    auto_delete  = true
    boot         = true
    disk_size_gb = 20
  }

  network_interface {
    network = google_compute_network.vpc.id
    access_config {}  # Assigns external IP
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update && apt-get install -y nginx
    echo "Hello from $(hostname)" > /var/www/html/index.html
    systemctl start nginx
  EOF

  lifecycle {
    create_before_destroy = true
  }
}

# Managed Instance Group
resource "google_compute_region_instance_group_manager" "web" {
  name               = "web-mig"
  region             = "us-central1"
  base_instance_name = "web-instance"

  version {
    instance_template = google_compute_instance_template.web.id
  }

  target_size = 2

  named_port {
    name = "http"
    port = 80
  }
}

# Autoscaler — scales based on CPU utilization
resource "google_compute_region_autoscaler" "web" {
  name   = "web-autoscaler"
  region = "us-central1"
  target = google_compute_region_instance_group_manager.web.id

  autoscaling_policy {
    max_replicas    = 5
    min_replicas    = 2
    cooldown_period = 60

    cpu_utilization {
      target = 0.6  # Scale when CPU exceeds 60%
    }
  }
}
```

**How it works:**
- When average CPU across the MIG exceeds 60%, GCP adds instances (up to 5)
- When CPU drops below the target, instances are removed (down to 2)
- The `cooldown_period` prevents rapid scaling oscillation

### Dynamic VPC and Subnet Creation

```hcl
variable "regions" {
  default = ["us-central1", "us-west1"]
}

variable "region_index" {
  default = {
    "us-central1" = 1
    "us-west1"    = 2
  }
}

resource "google_compute_network" "vpc" {
  name                    = "terraform-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "regional" {
  for_each      = toset(var.regions)
  name          = "subnet-${each.key}"
  region        = each.key
  network       = google_compute_network.vpc.id
  ip_cidr_range = "10.${var.region_index[each.key]}.0.0/16"
}
```

### Managed Services: Cloud SQL and Cloud Functions

```hcl
# Cloud SQL with High Availability
resource "google_sql_database_instance" "production" {
  name             = "prod-sql"
  database_version = "MYSQL_8_0"
  region           = "us-central1"

  settings {
    tier              = "db-custom-2-7680"
    availability_type = "REGIONAL"  # Multi-zone HA

    backup_configuration {
      enabled            = true
      binary_log_enabled = true
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = true
}

# Cloud Function with auto-scaling
resource "google_cloudfunctions2_function" "processor" {
  name     = "data-processor"
  location = "us-central1"

  build_config {
    runtime     = "nodejs20"
    entry_point = "handler"
    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.code.name
      }
    }
  }

  service_config {
    available_memory   = "512M"
    timeout_seconds    = 60
    max_instance_count = 10
    min_instance_count = 2
  }
}
```

### Real-Life Use Case

An e-commerce company uses GCP Managed Instance Groups for their web tier. During Black Friday, CPU utilization spikes above 60%, triggering the autoscaler to add instances from 2 to 5. Cloud SQL handles the database load with regional HA. After the sale ends, instances scale back down automatically, reducing costs.

---

## 17.3.3 Scaling Azure Infrastructure with Terraform

### Azure Provider Configuration

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}
```

### Compute Scaling: VM Scale Sets with Autoscaling

```hcl
resource "azurerm_resource_group" "main" {
  name     = "scaling-resources"
  location = "East US"
}

resource "azurerm_virtual_network" "main" {
  name                = "scaling-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "internal" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}

# VM Scale Set
resource "azurerm_linux_virtual_machine_scale_set" "web" {
  name                = "web-vmss"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard_DS1_v2"
  instances           = 2
  admin_username      = "adminuser"

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  network_interface {
    name    = "web-nic"
    primary = true

    ip_configuration {
      name      = "internal"
      subnet_id = azurerm_subnet.internal.id
      primary   = true
    }
  }
}

# Autoscale Settings
resource "azurerm_monitor_autoscale_setting" "web" {
  name                = "web-autoscale"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.web.id

  profile {
    name = "default-profile"

    capacity {
      default = 2
      minimum = 2
      maximum = 5
    }

    # Scale OUT when CPU > 70%
    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.web.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 70
      }
      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }

    # Scale IN when CPU < 30%
    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.web.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 30
      }
      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }
  }
}
```

### Dynamic Subnet Creation

```hcl
variable "subnet_prefixes" {
  default = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

resource "azurerm_subnet" "dynamic" {
  count                = length(var.subnet_prefixes)
  name                 = "subnet-${count.index + 1}"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_prefixes[count.index]]
}
```

### Managed Services: Azure SQL Elastic Pool and Function Apps

```hcl
# Azure SQL with Elastic Pool — shares resources across databases
resource "azurerm_mssql_elasticpool" "main" {
  name                = "prod-elastic-pool"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  server_name         = azurerm_mssql_server.main.name

  sku {
    name     = "StandardPool"
    tier     = "Standard"
    capacity = 50
  }

  per_database_settings {
    min_capacity = 10
    max_capacity = 20
  }

  max_size_gb = 5
}

# Azure Function App with dynamic scaling
resource "azurerm_service_plan" "functions" {
  name                = "functions-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"  # Consumption plan — auto-scales
}

resource "azurerm_linux_function_app" "processor" {
  name                       = "data-processor-func"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  service_plan_id            = azurerm_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

  site_config {
    application_stack {
      dotnet_version = "8.0"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "dotnet-isolated"
  }
}
```

### Real-Life Use Case

A healthcare SaaS provider runs their patient portal on Azure VM Scale Sets. During morning hours (8-10 AM) when doctors log in, CPU spikes above 70% and Azure Monitor automatically adds VMs. The SQL Elastic Pool shares DTUs across 15 tenant databases, so a spike in one tenant doesn't starve others. Azure Functions handle async tasks like report generation, scaling to zero when idle to minimize costs.

---

## 17.4 ALB Advanced Routing Patterns

### Path-Based Routing

Route traffic to different target groups based on URL path:

```hcl
# ALB with path-based routing using the terraform-aws-modules/alb module
module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name               = "${local.name}-alb"
  load_balancer_type = "application"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets
  security_groups    = [module.alb_sg.security_group_id]

  enable_deletion_protection = false

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"

      # Default action: fixed response for unmatched paths
      fixed_response = {
        content_type = "text/plain"
        message_body = "Nothing here. Try /app1 or /app2"
        status_code  = "404"
      }

      rules = {
        # Rule 1: /app1/* → App1 target group
        app1 = {
          priority = 1
          conditions = [{
            path_pattern = {
              values = ["/app1/*"]
            }
          }]
          actions = [{
            type             = "forward"
            target_group_key = "app1-tg"
          }]
        }

        # Rule 2: /app2/* → App2 target group
        app2 = {
          priority = 2
          conditions = [{
            path_pattern = {
              values = ["/app2/*"]
            }
          }]
          actions = [{
            type             = "forward"
            target_group_key = "app2-tg"
          }]
        }
      }
    }
  }

  target_groups = {
    app1-tg = {
      create_attachment = false
      name_prefix       = "app1-"
      protocol          = "HTTP"
      port              = 80
      target_type       = "instance"
      health_check = {
        path    = "/app1/index.html"
        matcher = "200-399"
      }
    }
    app2-tg = {
      create_attachment = false
      name_prefix       = "app2-"
      protocol          = "HTTP"
      port              = 80
      target_type       = "instance"
      health_check = {
        path    = "/app2/index.html"
        matcher = "200-399"
      }
    }
  }
}

# Attach EC2 instances to target groups
resource "aws_lb_target_group_attachment" "app1" {
  for_each         = { for k, v in module.ec2_app1 : k => v }
  target_group_arn = module.alb.target_groups["app1-tg"].arn
  target_id        = each.value.id
  port             = 80
}

resource "aws_lb_target_group_attachment" "app2" {
  for_each         = { for k, v in module.ec2_app2 : k => v }
  target_group_arn = module.alb.target_groups["app2-tg"].arn
  target_id        = each.value.id
  port             = 80
}
```

### Host-Header Based Routing

Route traffic based on the `Host` header (different subdomains → different apps):

```hcl
# HTTPS listener with host-header routing
listeners = {
  https = {
    port            = 443
    protocol        = "HTTPS"
    certificate_arn = module.acm.acm_certificate_arn

    # Default: app1
    forward = {
      target_group_key = "app1-tg"
    }

    rules = {
      # api.example.com → API target group
      api-route = {
        priority = 1
        conditions = [{
          host_header = {
            values = ["api.example.com"]
          }
        }]
        actions = [{
          type             = "forward"
          target_group_key = "api-tg"
        }]
      }

      # admin.example.com → Admin target group
      admin-route = {
        priority = 2
        conditions = [{
          host_header = {
            values = ["admin.example.com"]
          }
        }]
        actions = [{
          type             = "forward"
          target_group_key = "admin-tg"
        }]
      }
    }
  }
}
```

### HTTP to HTTPS Redirect

```hcl
listeners = {
  # Redirect all HTTP to HTTPS
  http-redirect = {
    port     = 80
    protocol = "HTTP"
    redirect = {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  # HTTPS listener with actual routing
  https = {
    port            = 443
    protocol        = "HTTPS"
    certificate_arn = module.acm.acm_certificate_arn
    forward = {
      target_group_key = "app1-tg"
    }
  }
}
```

### Query String and Custom Header Routing

```hcl
rules = {
  # Route based on query string: ?platform=mobile → mobile TG
  mobile-route = {
    priority = 3
    conditions = [{
      query_string = {
        key   = "platform"
        value = "mobile"
      }
    }]
    actions = [{
      type             = "forward"
      target_group_key = "mobile-tg"
    }]
  }

  # Route based on custom HTTP header
  custom-header-route = {
    priority = 4
    conditions = [{
      http_header = {
        http_header_name = "X-Custom-Header"
        values           = ["my-app-1"]
      }
    }]
    actions = [{
      type             = "forward"
      target_group_key = "app1-tg"
    }]
  }

  # Redirect based on query string
  redirect-route = {
    priority = 5
    conditions = [{
      query_string = {
        key   = "website"
        value = "docs"
      }
    }]
    actions = [{
      type = "redirect"
      redirect = {
        host        = "docs.example.com"
        path        = "/"
        protocol    = "HTTPS"
        status_code = "HTTP_302"
      }
    }]
  }
}
```

---

## 17.5 Network Load Balancer (NLB) with TCP/TLS

NLB operates at Layer 4 (TCP/UDP) — use it for high-performance, low-latency workloads:

```hcl
module "nlb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name_prefix        = "mynlb-"
  load_balancer_type = "network"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = false

  listeners = {
    # TCP listener (port 80)
    tcp = {
      port     = 80
      protocol = "TCP"
      forward = {
        target_group_key = "app-tcp"
      }
    }

    # TLS listener (port 443 — NLB terminates TLS)
    tls = {
      port            = 443
      protocol        = "TLS"
      certificate_arn = module.acm.acm_certificate_arn
      forward = {
        target_group_key = "app-tcp"
      }
    }
  }

  target_groups = {
    app-tcp = {
      create_attachment    = false
      name_prefix          = "app-"
      protocol             = "TCP"
      port                 = 80
      target_type          = "instance"
      deregistration_delay = 10
      health_check = {
        enabled             = true
        interval            = 30
        path                = "/app1/index.html"
        port                = "traffic-port"
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
      }
    }
  }

  tags = local.common_tags
}

# Attach instances to NLB target group
resource "aws_lb_target_group_attachment" "nlb" {
  for_each         = { for k, v in module.ec2_private : k => v }
  target_group_arn = module.nlb.target_groups["app-tcp"].arn
  target_id        = each.value.id
  port             = 80
}
```

> ⚠️ NLB requires the private security group to allow ingress from `0.0.0.0/0` (not just the VPC CIDR) because NLB preserves the client's source IP.

### ALB vs NLB — When to Use Which

```
┌──────────────────────┬──────────────────────────┬──────────────────────────┐
│                      │ ALB (Application)        │ NLB (Network)            │
├──────────────────────┼──────────────────────────┼──────────────────────────┤
│ OSI Layer            │ Layer 7 (HTTP/HTTPS)     │ Layer 4 (TCP/UDP/TLS)    │
│ Routing              │ Path, host, header,      │ Port-based only          │
│                      │ query string             │                          │
│ Performance          │ Good                     │ Ultra-low latency        │
│ Static IP            │ No (use Global Accel.)   │ Yes (Elastic IP per AZ)  │
│ SSL termination      │ Yes                      │ Yes (TLS listener)       │
│ WebSocket            │ Yes                      │ Yes                      │
│ Use case             │ Web apps, APIs,          │ Gaming, IoT, financial   │
│                      │ microservices            │ trading, TCP services    │
│ Health checks        │ HTTP/HTTPS path-based    │ TCP, HTTP, HTTPS         │
│ Preserve client IP   │ Via X-Forwarded-For      │ Natively preserved       │
└──────────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## 17.6 Auto Scaling Deep Dive

### Launch Template

```hcl
resource "aws_launch_template" "app" {
  name          = "${local.name}-lt"
  description   = "Launch template for app servers"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  key_name      = var.instance_keypair

  vpc_security_group_ids = [module.private_sg.security_group_id]
  user_data              = filebase64("${path.module}/scripts/app-install.sh")
  ebs_optimized          = true
  update_default_version = true  # New versions become default automatically

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      delete_on_termination = true
      encrypted             = true
    }
  }

  monitoring {
    enabled = true  # Detailed monitoring (1-minute intervals)
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${local.name}-asg-instance"
    })
  }
}
```

### Auto Scaling Group with Instance Refresh

```hcl
resource "aws_autoscaling_group" "app" {
  name_prefix         = "${local.name}-asg-"
  desired_capacity    = 2
  min_size            = 2
  max_size            = 10
  vpc_zone_identifier = module.vpc.private_subnets
  target_group_arns   = [module.alb.target_groups["app-tg"].arn]
  health_check_type   = "ELB"  # Use ALB health checks (not just EC2)

  launch_template {
    id      = aws_launch_template.app.id
    version = aws_launch_template.app.latest_version
  }

  # Rolling update when launch template changes
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50  # Keep at least 50% healthy during refresh
      # instance_warmup uses health_check_grace_period if not set
    }
    triggers = ["desired_capacity"]  # Also refresh when capacity changes
  }

  tag {
    key                 = "Name"
    value               = "${local.name}-asg"
    propagate_at_launch = true
  }
}
```

**What instance refresh does:**

```
┌─────────────────────────────────────────────────────────────────┐
│              Instance Refresh — Rolling Update                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Before: [Instance-A (v1)] [Instance-B (v1)]                   │
│                                                                 │
│  Step 1: Terminate Instance-A                                   │
│  Step 2: Launch Instance-C (v2) from new launch template        │
│  Step 3: Wait for Instance-C to pass health checks              │
│  Step 4: Terminate Instance-B                                   │
│  Step 5: Launch Instance-D (v2)                                 │
│  Step 6: Wait for Instance-D to pass health checks              │
│                                                                 │
│  After:  [Instance-C (v2)] [Instance-D (v2)]                   │
│                                                                 │
│  min_healthy_percentage = 50% means at least 1 of 2 instances   │
│  must be healthy at all times during the refresh.               │
└─────────────────────────────────────────────────────────────────┘
```

### Target Tracking Scaling Policies

```hcl
# Scale based on CPU utilization (target: 50%)
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "${local.name}-cpu-target"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name
  estimated_instance_warmup = 180

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

# Scale based on ALB request count per target (target: 1000 requests)
resource "aws_autoscaling_policy" "request_count" {
  name                   = "${local.name}-request-count"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name
  estimated_instance_warmup = 120

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ALBRequestCountPerTarget"
      resource_label = "${module.alb.arn_suffix}/${module.alb.target_groups["app-tg"].arn_suffix}"
    }
    target_value = 1000.0
  }
}
```

### Scheduled Scaling Actions

```hcl
# Scale up during business hours (7 AM EST = 12 PM UTC)
resource "aws_autoscaling_schedule" "scale_up" {
  scheduled_action_name  = "scale-up-business-hours"
  autoscaling_group_name = aws_autoscaling_group.app.name
  min_size               = 4
  max_size               = 10
  desired_capacity       = 8
  recurrence             = "0 12 * * MON-FRI"  # Cron: 12 PM UTC, Mon-Fri
}

# Scale down after business hours (9 PM UTC = 5 PM EST)
resource "aws_autoscaling_schedule" "scale_down" {
  scheduled_action_name  = "scale-down-after-hours"
  autoscaling_group_name = aws_autoscaling_group.app.name
  min_size               = 2
  max_size               = 10
  desired_capacity       = 2
  recurrence             = "0 21 * * MON-FRI"  # Cron: 9 PM UTC, Mon-Fri
}
```

### SNS Notifications for ASG Events

```hcl
resource "aws_sns_topic" "asg_notifications" {
  name = "${local.name}-asg-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.asg_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

resource "aws_autoscaling_notification" "asg_events" {
  group_names = [aws_autoscaling_group.app.name]
  notifications = [
    "autoscaling:EC2_INSTANCE_LAUNCH",
    "autoscaling:EC2_INSTANCE_TERMINATE",
    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
    "autoscaling:EC2_INSTANCE_TERMINATE_ERROR",
  ]
  topic_arn = aws_sns_topic.asg_notifications.arn
}
```

---

## 17.7 CloudWatch Alarms and Synthetics

### ASG CloudWatch Alarms

```hcl
# Alarm: Scale out when CPU > 80%
resource "aws_autoscaling_policy" "high_cpu" {
  name                   = "${local.name}-high-cpu"
  scaling_adjustment     = 4
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${local.name}-cpu-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }

  alarm_description = "Scale out when CPU > 80% for 4 minutes"
  alarm_actions     = [
    aws_autoscaling_policy.high_cpu.arn,
    aws_sns_topic.asg_notifications.arn,
  ]
  ok_actions = [aws_sns_topic.asg_notifications.arn]
}
```

### ALB CloudWatch Alarms

```hcl
# Alarm: Alert when HTTP 4xx errors exceed threshold
resource "aws_cloudwatch_metric_alarm" "alb_4xx" {
  alarm_name          = "${local.name}-alb-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  metric_name         = "HTTPCode_Target_4XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 120
  statistic           = "Sum"
  threshold           = 100
  treat_missing_data  = "missing"

  dimensions = {
    LoadBalancer = module.alb.arn_suffix
  }

  alarm_description = "Alert when 4xx errors exceed 100 in 4 minutes"
  alarm_actions     = [aws_sns_topic.asg_notifications.arn]
  ok_actions        = [aws_sns_topic.asg_notifications.arn]
}

# Alarm: Alert on 5xx errors (server-side issues)
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${local.name}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10

  dimensions = {
    LoadBalancer = module.alb.arn_suffix
  }

  alarm_description = "Alert when 5xx errors exceed 10 in 2 minutes"
  alarm_actions     = [aws_sns_topic.asg_notifications.arn]
}
```

### CloudWatch Synthetics (Canary Monitoring)

Synthetics canaries run on a schedule to monitor your endpoints — like a heartbeat check:

```hcl
# IAM role for the canary Lambda
resource "aws_iam_role" "canary" {
  name = "${local.name}-canary-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "canary" {
  role       = aws_iam_role.canary.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsFullAccess"
}

# S3 bucket for canary artifacts
resource "aws_s3_bucket" "canary" {
  bucket        = "${local.name}-canary-artifacts-${random_id.suffix.hex}"
  force_destroy = true
}

# Synthetics canary — heartbeat monitor
resource "aws_synthetics_canary" "app_monitor" {
  name                 = "${local.name}-heartbeat"
  artifact_s3_location = "s3://${aws_s3_bucket.canary.id}/"
  execution_role_arn   = aws_iam_role.canary.arn
  handler              = "heartbeat.handler"
  runtime_version      = "syn-nodejs-puppeteer-6.2"
  start_canary         = true

  schedule {
    expression = "rate(5 minutes)"  # Check every 5 minutes
  }

  run_config {
    timeout_in_seconds = 60
    active_tracing     = true
  }

  # Inline canary script
  zip_file = data.archive_file.canary_script.output_path
}

# Canary script
data "archive_file" "canary_script" {
  type        = "zip"
  output_path = "${path.module}/canary.zip"

  source {
    content  = <<-EOF
      const synthetics = require('Synthetics');
      const log = require('SyntheticsLogger');

      const heartbeat = async function () {
        const page = await synthetics.getPage();
        await synthetics.executeHttpStep(
          'Verify App1',
          'https://${var.domain_name}/app1/index.html'
        );
        log.info('Heartbeat check passed');
      };

      exports.handler = async () => {
        return await heartbeat();
      };
    EOF
    filename = "nodejs/node_modules/heartbeat.js"
  }
}

# Alarm when canary fails
resource "aws_cloudwatch_metric_alarm" "canary_failed" {
  alarm_name          = "${local.name}-canary-failed"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SuccessPercent"
  namespace           = "CloudWatchSynthetics"
  period              = 300
  statistic           = "Average"
  threshold           = 100

  dimensions = {
    CanaryName = aws_synthetics_canary.app_monitor.name
  }

  alarm_description = "Alert when canary health check fails"
  alarm_actions     = [aws_sns_topic.asg_notifications.arn]
}
```

---

## 17.8 ACM Certificate + Route53 DNS Validation

```hcl
# ACM certificate with DNS validation
module "acm" {
  source  = "terraform-aws-modules/acm/aws"
  version = "~> 5.0"

  domain_name = var.domain_name
  zone_id     = data.aws_route53_zone.main.zone_id

  # Wildcard + root domain
  subject_alternative_names = [
    "*.${var.domain_name}",
  ]

  validation_method = "DNS"
  wait_for_validation = true

  tags = local.common_tags
}

# Route53 zone data source
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

# DNS record pointing to ALB
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "apps.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.alb.dns_name
    zone_id                = module.alb.zone_id
    evaluate_target_health = true
  }
}
```

**Common ACM error:**

```
Error: Error requesting certificate: LimitExceededException:
Error: you have reached your limit of 20 certificates in the last year.
```

**Fix:** Request a limit increase via AWS Support → Service Quotas → ACM.

---

## 17.9 RDS with Templatefile for User Data

```hcl
# RDS database
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier     = "${local.name}-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.medium"

  allocated_storage = 20
  storage_encrypted = true

  db_name  = "appdb"
  username = var.db_username
  port     = 3306

  vpc_security_group_ids = [module.db_sg.security_group_id]
  db_subnet_group_name   = module.vpc.database_subnet_group_name

  multi_az            = var.environment == "prod" ? true : false
  deletion_protection = var.environment == "prod" ? true : false

  tags = local.common_tags
}

# Pass DB endpoint to EC2 via templatefile
resource "aws_launch_template" "app" {
  # ...
  user_data = base64encode(templatefile("${path.module}/scripts/app-install.tftpl", {
    db_host     = module.rds.db_instance_address
    db_port     = module.rds.db_instance_port
    db_name     = "appdb"
    db_username = var.db_username
    db_password = var.db_password
    app_port    = 8080
  }))
}
```

**Template file (`scripts/app-install.tftpl`):**

```bash
#!/bin/bash
sudo yum update -y
sudo yum install -y java-17-amazon-corretto

# Write database config
cat > /opt/app/application.properties <<PROPS
server.port=${app_port}
spring.datasource.url=jdbc:mysql://${db_host}:${db_port}/${db_name}
spring.datasource.username=${db_username}
spring.datasource.password=${db_password}
PROPS

# Start application
sudo systemctl start myapp
sudo systemctl enable myapp
```

---

## 17.10 Bastion Host Pattern

A bastion (jumpbox) provides SSH access to private instances without exposing them to the internet:

```
┌──────────────────────────────────────────────────────────────┐
│                         VPC                                  │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │  Public Subnet    │    │  Private Subnet               │   │
│  │                  │    │                              │   │
│  │  ┌────────────┐  │    │  ┌────────────┐              │   │
│  │  │  Bastion   │──┼────┼──│  App Server │              │   │
│  │  │  (SSH:22)  │  │    │  │  (SSH:22)   │              │   │
│  │  └────────────┘  │    │  └────────────┘              │   │
│  │       ↑ EIP      │    │                              │   │
│  └──────────────────┘    └──────────────────────────────┘   │
│          ↑                                                   │
│     Internet (SSH)                                           │
└──────────────────────────────────────────────────────────────┘
```

```hcl
# Bastion security group — SSH from your IP only
module "bastion_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name}-bastion-sg"
  vpc_id      = module.vpc.vpc_id
  description = "Bastion host SSH access"

  ingress_rules       = ["ssh-tcp"]
  ingress_cidr_blocks = [var.my_ip_cidr]  # e.g., "203.0.113.50/32"
  egress_rules        = ["all-all"]
}

# Private SG — SSH only from bastion
module "private_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "${local.name}-private-sg"
  vpc_id      = module.vpc.vpc_id
  description = "Private instances — SSH from bastion only"

  ingress_with_source_security_group_id = [
    {
      rule                     = "ssh-tcp"
      source_security_group_id = module.bastion_sg.security_group_id
    },
    {
      from_port                = 8080
      to_port                  = 8080
      protocol                 = "tcp"
      source_security_group_id = module.alb_sg.security_group_id
    },
  ]
  egress_rules = ["all-all"]
}

# Bastion EC2 instance
module "bastion" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.0"

  name          = "${local.name}-bastion"
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  key_name      = var.instance_keypair
  subnet_id     = module.vpc.public_subnets[0]
  vpc_security_group_ids = [module.bastion_sg.security_group_id]

  tags = local.common_tags
}

# Elastic IP for bastion (stable public IP across stop/start)
resource "aws_eip" "bastion" {
  instance   = module.bastion.id
  domain     = "vpc"
  depends_on = [module.bastion, module.vpc]  # Ensure VPC IGW exists first

  tags = merge(local.common_tags, {
    Name = "${local.name}-bastion-eip"
  })
}

# Copy SSH key to bastion, then use it to reach private instances
resource "null_resource" "copy_key_to_bastion" {
  depends_on = [module.bastion, aws_eip.bastion]

  connection {
    type        = "ssh"
    host        = aws_eip.bastion.public_ip
    user        = "ec2-user"
    private_key = file("~/.ssh/${var.instance_keypair}.pem")
  }

  provisioner "file" {
    source      = "~/.ssh/${var.instance_keypair}.pem"
    destination = "/home/ec2-user/${var.instance_keypair}.pem"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod 400 /home/ec2-user/${var.instance_keypair}.pem",
    ]
  }
}
```

**SSH through bastion to private instance:**

```bash
# Direct SSH to bastion
ssh -i ~/.ssh/mykey.pem ec2-user@<BASTION_EIP>

# From bastion, SSH to private instance
ssh -i mykey.pem ec2-user@<PRIVATE_IP>

# Or use SSH ProxyJump (single command)
ssh -J ec2-user@<BASTION_EIP> ec2-user@<PRIVATE_IP> -i ~/.ssh/mykey.pem
```

---

## 17.11 Sensitive Variables with secrets.tfvars

For database passwords and other secrets, use a separate `.tfvars` file that is **never committed to Git**:

```hcl
# variables.tf
variable "db_username" {
  description = "Database admin username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}
```

```hcl
# secrets.tfvars (NEVER commit this file)
db_username = "admin"
db_password = "SuperSecretP@ssw0rd!"
```

```ini
# .gitignore — add this line
secrets.tfvars
*.auto.tfvars  # if using auto-loaded secrets
```

```bash
# Pass secrets file explicitly
terraform plan -var-file="secrets.tfvars"
terraform apply -var-file="secrets.tfvars"
```

**Output (sensitive values are masked):**

```
  # aws_db_instance.main will be created
  + resource "aws_db_instance" "main" {
      + username = (sensitive value)
      + password = (sensitive value)
      ...
    }
```

**Alternative: Use environment variables (no file needed):**

```bash
export TF_VAR_db_username="admin"
export TF_VAR_db_password="SuperSecretP@ssw0rd!"
terraform apply
```

---

## 17.12 Classic Load Balancer (CLB) — Legacy

> ⚠️ CLB is a legacy service. AWS recommends ALB (Layer 7) or NLB (Layer 4) for new deployments. This section is included for teams maintaining existing CLB infrastructure.

```hcl
module "clb" {
  source  = "terraform-aws-modules/elb/aws"
  version = "~> 4.0"

  name     = "${local.name}-clb"
  subnets  = module.vpc.public_subnets
  security_groups = [module.alb_sg.security_group_id]
  internal = false

  listener = [
    {
      instance_port     = 80
      instance_protocol = "HTTP"
      lb_port           = 80
      lb_protocol       = "HTTP"
    },
  ]

  health_check = {
    target              = "HTTP:80/"
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
  }

  tags = local.common_tags
}

# Attach instances to CLB
resource "aws_elb_attachment" "web" {
  for_each = { for k, v in module.ec2_private : k => v }
  elb      = module.clb.elb_id
  instance = each.value.id
}

output "clb_dns_name" {
  value = module.clb.elb_dns_name
}
```

### CLB vs ALB vs NLB

```
┌──────────────────────┬──────────┬──────────┬──────────┐
│                      │ CLB      │ ALB      │ NLB      │
├──────────────────────┼──────────┼──────────┼──────────┤
│ OSI Layer            │ 4 + 7    │ 7        │ 4        │
│ Path routing         │ No       │ Yes      │ No       │
│ Host routing         │ No       │ Yes      │ No       │
│ WebSocket            │ No       │ Yes      │ Yes      │
│ Static IP            │ No       │ No       │ Yes      │
│ Multiple TGs         │ No       │ Yes      │ Yes      │
│ Status               │ Legacy   │ Current  │ Current  │
│ Use for new projects │ No       │ Yes      │ Yes      │
└──────────────────────┴──────────┴──────────┴──────────┘
```

---

## 17.13 Deprecated: Launch Configuration

> ⚠️ `aws_launch_configuration` is deprecated. Use `aws_launch_template` instead (see §17.6). This section exists for teams migrating legacy configs.

```hcl
# ❌ DEPRECATED — do not use for new projects
resource "aws_launch_configuration" "legacy" {
  name_prefix     = "${local.name}-lc-"
  image_id        = data.aws_ami.amazon_linux.id
  instance_type   = "t3.micro"
  security_groups = [module.private_sg.security_group_id]
  user_data       = file("${path.module}/scripts/app-install.sh")

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "legacy" {
  name_prefix          = "${local.name}-asg-"
  launch_configuration = aws_launch_configuration.legacy.name  # ← deprecated
  min_size             = 2
  max_size             = 10
  vpc_zone_identifier  = module.vpc.private_subnets
}
```

**Migration to launch template:**

```hcl
# ✅ CURRENT — use launch templates
resource "aws_launch_template" "current" {
  name_prefix   = "${local.name}-lt-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  vpc_security_group_ids = [module.private_sg.security_group_id]
  user_data     = filebase64("${path.module}/scripts/app-install.sh")

  # Launch templates support features that launch configs don't:
  # - Multiple instance types
  # - Instance refresh (rolling updates)
  # - Spot instances mixed with on-demand
  # - EBS optimization settings
}

resource "aws_autoscaling_group" "current" {
  name_prefix         = "${local.name}-asg-"
  min_size            = 2
  max_size            = 10
  vpc_zone_identifier = module.vpc.private_subnets

  launch_template {
    id      = aws_launch_template.current.id
    version = aws_launch_template.current.latest_version
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
  }
}
```

---

## 17.14 CloudWatch CIS Benchmark Alarms

CIS (Center for Internet Security) benchmark alarms monitor AWS account-level security events via CloudTrail logs:

```hcl
# CloudWatch Log Group for CloudTrail
resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = "${local.name}-cloudtrail-logs"
  retention_in_days = 90
}

# CIS 3.1 — Unauthorized API calls
resource "aws_cloudwatch_log_metric_filter" "unauthorized_api" {
  name           = "UnauthorizedAPICalls"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ ($.errorCode = \"*UnauthorizedAccess*\") || ($.errorCode = \"AccessDenied*\") }"

  metric_transformation {
    name      = "UnauthorizedAPICalls"
    namespace = "CISBenchmark"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "unauthorized_api" {
  alarm_name          = "CIS-3.1-UnauthorizedAPICalls"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "UnauthorizedAPICalls"
  namespace           = "CISBenchmark"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "CIS 3.1: Monitoring unauthorized API calls"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

# CIS 3.3 — Root account usage
resource "aws_cloudwatch_log_metric_filter" "root_usage" {
  name           = "RootAccountUsage"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ $.userIdentity.type = \"Root\" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != \"AwsServiceEvent\" }"

  metric_transformation {
    name      = "RootAccountUsage"
    namespace = "CISBenchmark"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "root_usage" {
  alarm_name          = "CIS-3.3-RootAccountUsage"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "RootAccountUsage"
  namespace           = "CISBenchmark"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "CIS 3.3: Alert on root account usage"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

# CIS 3.4 — IAM policy changes
resource "aws_cloudwatch_log_metric_filter" "iam_changes" {
  name           = "IAMPolicyChanges"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ ($.eventName = CreatePolicy) || ($.eventName = DeletePolicy) || ($.eventName = AttachRolePolicy) || ($.eventName = DetachRolePolicy) || ($.eventName = AttachUserPolicy) || ($.eventName = DetachUserPolicy) }"

  metric_transformation {
    name      = "IAMPolicyChanges"
    namespace = "CISBenchmark"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "iam_changes" {
  alarm_name          = "CIS-3.4-IAMPolicyChanges"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "IAMPolicyChanges"
  namespace           = "CISBenchmark"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "CIS 3.4: Alert on IAM policy changes"
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}

# SNS topic for security alerts
resource "aws_sns_topic" "security_alerts" {
  name = "${local.name}-security-alerts"
}
```

---

## Exercises

### Exercise 17.1
Deploy the three-tier application with dev and prod configurations. Compare the resource counts and costs.

### Exercise 17.2
Build the serverless API project. Test it with curl after deployment.

### Exercise 17.3
Add monitoring (CloudWatch dashboards, SNS alerts) to any of the projects above.

---

## Key Takeaways

- Real projects compose multiple modules together
- Use environment-specific tfvars for different configurations
- Security groups should follow least-privilege (reference other SGs, not CIDRs)
- Use data sources for AMIs, AZs, and account info instead of hardcoding
- Production needs: Multi-AZ, backups, deletion protection, monitoring
- Serverless architectures need fewer Terraform resources but more IAM config

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| **VPC and Networking** | |
| `aws_vpc` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc) |
| `aws_subnet` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet) |
| `aws_nat_gateway` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/nat_gateway](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/nat_gateway) |
| `aws_route_table` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table) |
| **Compute** | |
| `aws_instance` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance) |
| `aws_autoscaling_group` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_group) |
| `aws_launch_template` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/launch_template](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/launch_template) |
| **Load Balancing** | |
| `aws_lb` (ALB) | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb) |
| `aws_lb_target_group` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group) |
| `aws_lb_listener` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) |
| **Database** | |
| `aws_db_instance` (RDS) | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance) |
| `aws_db_subnet_group` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group) |
| **Serverless** | |
| `aws_lambda_function` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) |
| `aws_api_gateway_rest_api` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api) |
| `aws_dynamodb_table` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table) |
| **EKS** | |
| `aws_eks_cluster` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_cluster) |
| `aws_eks_node_group` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_node_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_node_group) |
| AWS EKS Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/eks/aws/latest) |
| **ALB Routing** | |
| `aws_lb_listener_rule` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener_rule) |
| `aws_lb_target_group_attachment` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group_attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group_attachment) |
| AWS ALB Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest) |
| **Auto Scaling** | |
| `aws_autoscaling_policy` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_policy) |
| `aws_autoscaling_schedule` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_schedule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_schedule) |
| `aws_autoscaling_notification` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/autoscaling_notification) |
| **CloudWatch** | |
| `aws_cloudwatch_metric_alarm` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) |
| `aws_synthetics_canary` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/synthetics_canary](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/synthetics_canary) |
| **SNS** | |
| `aws_sns_topic` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) |
| `aws_sns_topic_subscription` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) |
| **ACM and Route53** | |
| `aws_acm_certificate` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate) |
| `aws_route53_record` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) |
| AWS ACM Module (Registry) | [registry.terraform.io/modules/terraform-aws-modules/acm/aws/latest](https://registry.terraform.io/modules/terraform-aws-modules/acm/aws/latest) |
| **CI/CD** | |
| `aws_codepipeline` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codepipeline](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codepipeline) |
| `aws_codebuild_project` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project) |
| **IAM** | |
| `aws_iam_role` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) |
| `aws_iam_policy` | [registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) |

---

[← Previous Module](../module-16-cicd-and-automation/README.md) | [Next Module: Troubleshooting Guide →](../module-18-troubleshooting-guide/README.md)
