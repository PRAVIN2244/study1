# Create and Save Models to SageMaker

### Create an S3 bucket

`aws s3 mb s3://my-sagemaker-demo-bucket-abhishek`

### Create IAM Execution Role for SageMaker

Create trust policy - trust.json

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "sagemaker.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Create the role

```
aws iam create-role \
  --role-name SageMakerDemoExecutionRole \
  --assume-role-policy-document file://trust.json
```

Attach permissions

```
aws iam attach-role-policy \
  --role-name SageMakerDemoExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
```

```
aws iam attach-role-policy \
  --role-name SageMakerDemoExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

### Find default VPC + default subnets

Get Default VPC

```
aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query "Vpcs[0].VpcId" --output text
```

Get subnets

```
aws ec2 describe-subnets --filters Name=vpc-id,Values=<VPC-ID> \
  --query "Subnets[*].SubnetId" --output text
```

Pick 2 subnets.

### Create SageMaker Domain (Studio)

```
aws sagemaker create-domain \
  --domain-name demo-domain \
  --auth-mode IAM \
  --default-user-settings "ExecutionRole=arn:aws:iam::<ACCOUNT-ID>:role/SageMakerDemoExecutionRole" \
  --vpc-id <VPC-ID> \
  --subnet-ids "<SUBNET-1>" "<SUBNET-2>"
```

Note the returned DomainId.

### Create User Profile

```
aws sagemaker create-user-profile \
  --domain-id <DOMAIN-ID> \
  --user-profile-name demo-user
```

### Open SageMaker Studio

Go to:

AWS Console → SageMaker → Domains → demo-domain → Launch app → Studio

Select demo-user.

A JupyterLab interface will open.

### Inside Studio: Train a simple model & Push to S3

Open a Python 3 Notebook.

Now run the following code.

### Import libraries

```
import boto3
import joblib
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
import os
```

#### Train a tiny ML model

```
iris = load_iris()
X, y = iris.data, iris.target

model = DecisionTreeClassifier()
model.fit(X, y)

joblib.dump(model, "iris-model.pkl")

print("Model saved as iris-model.pkl")
```

#### Upload model to S3

```
import boto3

s3 = boto3.client("s3")
bucket = "my-sagemaker-demo-bucket-abhishek"

s3.upload_file("iris-model.pkl", bucket, "model-artifacts/iris-model.pkl")

print("Uploaded to S3:", f"s3://{bucket}/model-artifacts/iris-model.pkl")
```

### Verify upload from CLI

`aws s3 ls s3://my-sagemaker-demo-bucket-abhishek/model-artifacts/`

You will see:

`iris-model.pkl`