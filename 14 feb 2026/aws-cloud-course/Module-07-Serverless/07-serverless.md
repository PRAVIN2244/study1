# Module 7: Lambda, API Gateway & Serverless

## 7.1 What is Serverless?

Serverless means you write code without managing servers. AWS handles provisioning, scaling, and maintenance.

### Real-World Analogy
- **EC2** = Renting an apartment (you pay monthly, even when you're not home)
- **Lambda** = Staying at a hotel (you pay only for the nights you stay)

### Serverless Services on AWS

```
┌─────────────────────────────────────────────────┐
│              AWS Serverless Stack                 │
├─────────────────────────────────────────────────┤
│  Compute:    Lambda, Fargate                     │
│  API:        API Gateway                         │
│  Storage:    S3, DynamoDB                        │
│  Messaging:  SQS, SNS, EventBridge              │
│  Orchestration: Step Functions                   │
│  Auth:       Cognito                             │
└─────────────────────────────────────────────────┘
```

---

## 7.2 AWS Lambda

### Lambda Concepts

| Concept | Meaning |
|---------|---------|
| **Function** | Your code + configuration |
| **Handler** | Entry point function (e.g., `index.handler`) |
| **Runtime** | Language environment (Python, Node.js, Java, Go, .NET) |
| **Trigger** | What invokes the function (API Gateway, S3, SQS, etc.) |
| **Timeout** | Max execution time (1 sec to 15 min) |
| **Memory** | 128 MB to 10,240 MB (CPU scales with memory) |
| **Cold Start** | First invocation delay (container initialization) |

### Lambda Execution Flow

```
Trigger (API Gateway, S3, SQS...)
    │
    ▼
┌──────────────────────────────┐
│  Lambda Service               │
│                               │
│  1. Receive event             │
│  2. Find/create container     │
│  3. Load your code            │
│  4. Execute handler function  │
│  5. Return response           │
│  6. Keep container warm (reuse)│
└──────────────────────────────┘
    │
    ▼
Response / Side effects
```

### Create a Lambda Function (Python)

```bash
# Step 1: Write the function code
mkdir lambda-demo && cd lambda-demo

cat > lambda_function.py << 'EOF'
import json

def handler(event, context):
    """
    event: Input data (JSON)
    context: Runtime info (function name, memory, timeout remaining)
    """
    print(f"Event received: {json.dumps(event)}")

    name = event.get('name', 'World')

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'function': context.function_name,
            'memory_mb': context.memory_limit_in_mb,
            'remaining_ms': context.get_remaining_time_in_millis()
        })
    }
EOF

# Step 2: Package the code
zip function.zip lambda_function.py

# Step 3: Create IAM role for Lambda
cat > trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}
EOF

ROLE_ARN=$(aws iam create-role \
  --role-name lambda-basic-role \
  --assume-role-policy-document file://trust-policy.json \
  --query 'Role.Arn' --output text)

# Attach basic execution policy (CloudWatch Logs)
aws iam attach-role-policy \
  --role-name lambda-basic-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Wait for role propagation
sleep 10

# Step 4: Create the Lambda function
aws lambda create-function \
  --function-name hello-world \
  --runtime python3.12 \
  --handler lambda_function.handler \
  --role $ROLE_ARN \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 128 \
  --environment Variables='{STAGE=production}'
```

**Expected Output:**
```json
{
    "FunctionName": "hello-world",
    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:hello-world",
    "Runtime": "python3.12",
    "Handler": "lambda_function.handler",
    "CodeSize": 350,
    "Timeout": 30,
    "MemorySize": 128,
    "State": "Active"
}
```

### Invoke Lambda Function

```bash
# Synchronous invocation
aws lambda invoke \
  --function-name hello-world \
  --payload '{"name": "Alice"}' \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json
```

**Expected Output:**
```json
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```

**response.json:**
```json
{
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": "{\"message\": \"Hello, Alice!\", \"function\": \"hello-world\", \"memory_mb\": \"128\"}"
}
```

### Update Function Code

```bash
# Edit code, re-zip, and update
zip function.zip lambda_function.py

aws lambda update-function-code \
  --function-name hello-world \
  --zip-file fileb://function.zip
```

### Update Function Configuration

```bash
aws lambda update-function-configuration \
  --function-name hello-world \
  --timeout 60 \
  --memory-size 256 \
  --environment Variables='{STAGE=production,DB_HOST=mydb.example.com}'
```

### Lambda with Dependencies (Node.js Example)

```bash
mkdir node-lambda && cd node-lambda

# Create package.json
cat > package.json << 'EOF'
{
  "name": "lambda-api",
  "version": "1.0.0",
  "dependencies": {
    "axios": "^1.6.0",
    "uuid": "^9.0.0"
  }
}
EOF

# Create handler
cat > index.js << 'EOF'
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

exports.handler = async (event) => {
    const requestId = uuidv4();

    try {
        const response = await axios.get('https://api.github.com/users/octocat');

        return {
            statusCode: 200,
            body: JSON.stringify({
                requestId,
                user: response.data.login,
                followers: response.data.followers
            })
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message, requestId })
        };
    }
};
EOF

# Install dependencies and package
npm install --production
zip -r function.zip index.js node_modules/

# Deploy
aws lambda create-function \
  --function-name github-api \
  --runtime nodejs20.x \
  --handler index.handler \
  --role $ROLE_ARN \
  --zip-file fileb://function.zip \
  --timeout 10 \
  --memory-size 256
```

### Lambda Layers (Shared Dependencies)

```bash
# Create a layer with shared libraries
mkdir -p python/lib/python3.12/site-packages
pip install requests -t python/lib/python3.12/site-packages/
zip -r layer.zip python/

aws lambda publish-layer-version \
  --layer-name common-libs \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.12

# Attach layer to function
aws lambda update-function-configuration \
  --function-name hello-world \
  --layers arn:aws:lambda:us-east-1:123456789012:layer:common-libs:1
```

### Lambda Versions and Aliases

```bash
# Publish a version (immutable snapshot)
aws lambda publish-version \
  --function-name hello-world \
  --description "v1.0 - initial release"

# Create alias pointing to version
aws lambda create-alias \
  --function-name hello-world \
  --name production \
  --function-version 1

# Weighted alias (canary deployment: 90% v1, 10% v2)
aws lambda update-alias \
  --function-name hello-world \
  --name production \
  --routing-config AdditionalVersionWeights={"2"=0.1}
```

---

## 7.3 API Gateway

API Gateway creates RESTful and WebSocket APIs that trigger Lambda functions.

### Architecture

```
Client (Browser/Mobile)
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ API Gateway  │────▶│   Lambda     │────▶│  DynamoDB    │
│              │     │   Function   │     │              │
│ /users GET   │     │  getUsers()  │     │  Users table │
│ /users POST  │     │  createUser()│     │              │
│ /users/{id}  │     │  getUser()   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Create REST API

```bash
# Step 1: Create the API
API_ID=$(aws apigateway create-rest-api \
  --name "UserService" \
  --description "User management API" \
  --endpoint-configuration types=REGIONAL \
  --query 'id' --output text)

echo "API ID: $API_ID"

# Step 2: Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Step 3: Create /users resource
USERS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part users \
  --query 'id' --output text)

# Step 4: Create GET method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $USERS_ID \
  --http-method GET \
  --authorization-type NONE

# Step 5: Integrate with Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $USERS_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:123456789012:function:hello-world/invocations"

# Step 6: Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name hello-world \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:123456789012:${API_ID}/*/GET/users"

# Step 7: Deploy the API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod \
  --description "Production deployment"
```

**API URL:**
```
https://{API_ID}.execute-api.us-east-1.amazonaws.com/prod/users
```

### Test the API

```bash
curl https://${API_ID}.execute-api.us-east-1.amazonaws.com/prod/users
```

**Expected Output:**
```json
{
    "message": "Hello, World!",
    "function": "hello-world"
}
```

### HTTP API (Simpler, Cheaper Alternative)

```bash
# Create HTTP API with Lambda integration (much simpler)
API_ID=$(aws apigatewayv2 create-api \
  --name "UserServiceV2" \
  --protocol-type HTTP \
  --target "arn:aws:lambda:us-east-1:123456789012:function:hello-world" \
  --query 'ApiId' --output text)

# Get the endpoint
aws apigatewayv2 get-api --api-id $API_ID \
  --query 'ApiEndpoint' --output text
```

---

## 7.4 S3 Event → Lambda (Image Processing)

```bash
# Lambda function that processes uploaded images
cat > image_processor.py << 'EOF'
import json
import boto3
import os

s3 = boto3.client('s3')

def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']

        print(f"New file: s3://{bucket}/{key} ({size} bytes)")

        # Get object metadata
        response = s3.head_object(Bucket=bucket, Key=key)
        content_type = response['ContentType']

        # Copy to processed folder with metadata
        s3.copy_object(
            Bucket=bucket,
            CopySource=f"{bucket}/{key}",
            Key=f"processed/{os.path.basename(key)}",
            Metadata={'processed': 'true', 'original-key': key},
            MetadataDirective='REPLACE'
        )

        print(f"Processed: {key} -> processed/{os.path.basename(key)}")

    return {'statusCode': 200, 'body': 'Processing complete'}
EOF

zip function.zip image_processor.py

aws lambda create-function \
  --function-name image-processor \
  --runtime python3.12 \
  --handler image_processor.handler \
  --role $ROLE_ARN \
  --zip-file fileb://function.zip \
  --timeout 60 \
  --memory-size 512

# Grant S3 permission to invoke Lambda
aws lambda add-permission \
  --function-name image-processor \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::my-upload-bucket

# Configure S3 event notification
aws s3api put-bucket-notification-configuration \
  --bucket my-upload-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:image-processor",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {"Name": "prefix", "Value": "uploads/"},
            {"Name": "suffix", "Value": ".jpg"}
          ]
        }
      }
    }]
  }'
```

---

## 7.5 SQS → Lambda (Queue Processing)

```bash
# Create SQS queue
QUEUE_URL=$(aws sqs create-queue \
  --queue-name order-processing \
  --attributes '{
    "VisibilityTimeout": "60",
    "MessageRetentionPeriod": "86400",
    "ReceiveMessageWaitTimeSeconds": "20"
  }' \
  --query 'QueueUrl' --output text)

QUEUE_ARN=$(aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

# Create Lambda event source mapping
aws lambda create-event-source-mapping \
  --function-name order-processor \
  --event-source-arn $QUEUE_ARN \
  --batch-size 10

# Send test message
aws sqs send-message \
  --queue-url $QUEUE_URL \
  --message-body '{"orderId": "ORD-001", "amount": 99.99}'
```

---

## 7.6 Industry Project: Serverless REST API

### Full-Stack Serverless API for a Todo Application

```bash
#!/bin/bash
# === Serverless Todo API ===

# --- DynamoDB Table ---
aws dynamodb create-table \
  --table-name Todos \
  --attribute-definitions \
    AttributeName=userId,AttributeType=S \
    AttributeName=todoId,AttributeType=S \
  --key-schema \
    AttributeName=userId,KeyType=HASH \
    AttributeName=todoId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

# --- Lambda Function ---
cat > todo_api.py << 'PYEOF'
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Todos')

def handler(event, context):
    method = event['httpMethod']
    path = event['path']

    try:
        if method == 'GET' and path == '/todos':
            return get_todos(event)
        elif method == 'POST' and path == '/todos':
            return create_todo(event)
        elif method == 'PUT' and '/todos/' in path:
            return update_todo(event)
        elif method == 'DELETE' and '/todos/' in path:
            return delete_todo(event)
        else:
            return response(404, {'error': 'Not found'})
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'error': str(e)})

def get_todos(event):
    user_id = event['queryStringParameters'].get('userId', 'default')
    result = table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    return response(200, result['Items'])

def create_todo(event):
    body = json.loads(event['body'])
    item = {
        'userId': body.get('userId', 'default'),
        'todoId': str(uuid.uuid4()),
        'title': body['title'],
        'completed': False,
        'createdAt': datetime.utcnow().isoformat()
    }
    table.put_item(Item=item)
    return response(201, item)

def update_todo(event):
    todo_id = event['pathParameters']['id']
    body = json.loads(event['body'])
    result = table.update_item(
        Key={'userId': body.get('userId', 'default'), 'todoId': todo_id},
        UpdateExpression='SET completed = :c, title = :t',
        ExpressionAttributeValues={':c': body.get('completed', False), ':t': body['title']},
        ReturnValues='ALL_NEW'
    )
    return response(200, result['Attributes'])

def delete_todo(event):
    todo_id = event['pathParameters']['id']
    body = json.loads(event['body']) if event.get('body') else {}
    table.delete_item(
        Key={'userId': body.get('userId', 'default'), 'todoId': todo_id}
    )
    return response(200, {'message': 'Deleted'})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }
PYEOF

zip todo-api.zip todo_api.py

aws lambda create-function \
  --function-name todo-api \
  --runtime python3.12 \
  --handler todo_api.handler \
  --role $ROLE_ARN \
  --zip-file fileb://todo-api.zip \
  --timeout 30 \
  --memory-size 256

echo "Serverless Todo API deployed!"
```

---

## 7.7 Common Errors & Troubleshooting

### Error 1: "Task timed out after X seconds"
```
Task timed out after 3.00 seconds
```
**Fix:** Increase timeout or optimize code:
```bash
aws lambda update-function-configuration \
  --function-name my-function \
  --timeout 60
```

### Error 2: "Unable to import module"
```
Unable to import module 'lambda_function': No module named 'requests'
```
**Fix:** Include dependencies in the zip or use Lambda Layers.

### Error 3: Lambda has no permissions to access DynamoDB
```
An error occurred (AccessDeniedException) when calling the PutItem operation
```
**Fix:** Attach DynamoDB policy to Lambda's IAM role:
```bash
aws iam attach-role-policy \
  --role-name lambda-basic-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### Error 4: API Gateway returns 502 Bad Gateway
**Cause:** Lambda returned an invalid response format.
**Fix:** Ensure response has `statusCode`, `headers`, and `body`:
```python
return {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps({'message': 'success'})  # body MUST be a string
}
```

### Error 5: Cold start latency (5-10 seconds for Java/.NET)
**Fix:** Use Provisioned Concurrency:
```bash
aws lambda put-provisioned-concurrency-config \
  --function-name my-function \
  --qualifier production \
  --provisioned-concurrent-executions 5
```

---

## 7.8 Lambda — Limits and Concurrency

### Lambda Limits (per region)

| Limit | Value |
|-------|-------|
| Memory | 128 MB – 10,240 MB (10 GB) |
| Timeout | Max 15 minutes |
| Environment variables | 4 KB total |
| /tmp storage | 512 MB – 10,240 MB |
| Concurrent executions | 1,000 (soft limit, can increase) |
| Deployment package | 50 MB zipped, 250 MB unzipped |
| Container image | 10 GB |

### Concurrency and Throttling

- Default: 1,000 concurrent executions per region (shared across all functions)
- **Reserved Concurrency**: Guarantee a function gets N concurrent executions (others can't use them)
- **Provisioned Concurrency**: Pre-initialize N execution environments (eliminates cold starts)

```bash
# Set reserved concurrency (guarantees 100 for this function)
aws lambda put-function-concurrency \
  --function-name my-function \
  --reserved-concurrent-executions 100

# Set provisioned concurrency on an alias
aws lambda put-provisioned-concurrency-config \
  --function-name my-function \
  --qualifier prod \
  --provisioned-concurrent-executions 50
```

If a function exceeds its concurrency limit, additional invocations are throttled (429 error for sync, retried for async).

### Lambda SnapStart (Java)

Pre-initializes Java functions by snapshotting the initialized execution environment. Reduces cold start from ~5s to ~200ms.

```bash
# Enable SnapStart on a Java Lambda function
aws lambda update-function-configuration \
  --function-name my-java-function \
  --snap-start ApplyOn=PublishedVersions

# Expected output:
# {
#   "SnapStart": {
#     "ApplyOn": "PublishedVersions",
#     "OptimizationStatus": "On"
#   }
# }

# Publish a version (SnapStart only works on published versions)
aws lambda publish-version --function-name my-java-function

# Verify SnapStart is active
aws lambda get-function-configuration \
  --function-name my-java-function \
  --qualifier 1 \
  --query 'SnapStart'

# Expected output:
# {
#   "ApplyOn": "PublishedVersions",
#   "OptimizationStatus": "On"
# }
```

**How it works:** When you publish a version, Lambda initializes the function, takes a Firecracker microVM snapshot (including memory and disk state), and caches it. On cold start, Lambda restores from the snapshot instead of re-initializing. Works with Java 11+ (Corretto).

**Caveat:** Uniqueness — if your init code generates unique IDs or connections, they'll be shared across restored instances. Use `CRaC` (Coordinated Restore at Checkpoint) hooks to regenerate unique values after restore.

---

## 7.9 Lambda@Edge and CloudFront Functions

Run code at AWS edge locations to customize CDN behavior.

| Feature | CloudFront Functions | Lambda@Edge |
|---------|---------------------|-------------|
| **Runtime** | JavaScript only | Node.js, Python |
| **Execution time** | < 1 ms | Up to 5 seconds (viewer), 30s (origin) |
| **Memory** | 2 MB | 128–10,240 MB |
| **Network/File access** | No | Yes |
| **Scale** | Millions of requests/sec | Thousands/sec |
| **Cost** | 1/6th of Lambda@Edge | Higher |
| **Use cases** | Header manipulation, URL rewrites, cache key normalization | A/B testing, user auth, dynamic content |

### Trigger Points

```
Viewer Request ──▶ CloudFront ──▶ Origin Request ──▶ Origin Server
                                                         │
Viewer Response ◀── CloudFront ◀── Origin Response ◀─────┘
```

### CloudFront Function Example: Geo-Based URL Rewrite

```javascript
// CloudFront Function: redirect users to country-specific content
function handler(event) {
    var request = event.request;
    var headers = request.headers;
    var country = headers['cloudfront-viewer-country']
        ? headers['cloudfront-viewer-country'].value
        : 'US';

    // Rewrite URI to country-specific path
    if (country === 'DE' || country === 'AT' || country === 'CH') {
        request.uri = '/de' + request.uri;
    } else if (country === 'FR') {
        request.uri = '/fr' + request.uri;
    } else if (country === 'JP') {
        request.uri = '/ja' + request.uri;
    }
    // Default: English (no rewrite)

    return request;
}
```

```bash
# Create the CloudFront Function
aws cloudfront create-function \
  --name geo-rewrite \
  --function-config '{"Comment":"Geo-based URL rewrite","Runtime":"cloudfront-js-2.0"}' \
  --function-code fileb://geo-rewrite.js

# Publish the function
aws cloudfront publish-function \
  --name geo-rewrite \
  --if-match ETVPDKIKX0DER

# Associate with a distribution's cache behavior
# In the distribution config:
# "FunctionAssociations": {
#   "Quantity": 1,
#   "Items": [{
#     "FunctionARN": "arn:aws:cloudfront::123456789012:function/geo-rewrite",
#     "EventType": "viewer-request"
#   }]
# }

# Test the function
aws cloudfront test-function \
  --name geo-rewrite \
  --if-match ETVPDKIKX0DER \
  --event-object '{"version":"1.0","context":{"eventType":"viewer-request"},"viewer":{"ip":"203.0.113.1"},"request":{"method":"GET","uri":"/index.html","headers":{"cloudfront-viewer-country":{"value":"DE"}}}}'

# Expected output:
# {
#   "FunctionOutput": "{\"request\":{\"uri\":\"/de/index.html\",...}}"
# }
```

---

## 7.10 Lambda in VPC

By default, Lambda runs outside your VPC. To access private resources (RDS, ElastiCache), deploy Lambda in your VPC.

```bash
aws lambda update-function-configuration \
  --function-name my-function \
  --vpc-config SubnetIds=subnet-0abc123,subnet-0def456,SecurityGroupIds=sg-0abc123
```

**Trade-off:** Lambda in VPC loses direct internet access. To access the internet, route through a NAT Gateway in a public subnet.

```
Lambda (private subnet) ──▶ NAT Gateway (public subnet) ──▶ Internet
Lambda (private subnet) ──▶ VPC Endpoint ──▶ AWS Services (no NAT needed)
```

Use **RDS Proxy** between Lambda and RDS to manage connection pooling.

```bash
# Create an RDS Proxy
aws rds create-db-proxy \
  --db-proxy-name my-lambda-proxy \
  --engine-family MYSQL \
  --auth '[{
    "AuthScheme": "SECRETS",
    "SecretArn": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-creds",
    "IAMAuth": "REQUIRED"
  }]' \
  --role-arn arn:aws:iam::123456789012:role/RDSProxyRole \
  --vpc-subnet-ids subnet-0abcdef1234567890 subnet-0fedcba0987654321 \
  --vpc-security-group-ids sg-0abcdef1234567890

# Expected output:
# {
#   "DBProxy": {
#     "DBProxyName": "my-lambda-proxy",
#     "DBProxyArn": "arn:aws:rds:us-east-1:123456789012:db-proxy:prx-0abcdef",
#     "Endpoint": "my-lambda-proxy.proxy-abcdef.us-east-1.rds.amazonaws.com",
#     "Status": "creating"
#   }
# }

# Register the RDS instance as a target
aws rds register-db-proxy-targets \
  --db-proxy-name my-lambda-proxy \
  --db-instance-identifiers my-database

# Configure Lambda to use the proxy endpoint
aws lambda update-function-configuration \
  --function-name my-function \
  --environment 'Variables={DB_HOST=my-lambda-proxy.proxy-abcdef.us-east-1.rds.amazonaws.com}'
```

**Why RDS Proxy with Lambda:** Lambda can spawn hundreds of concurrent executions, each opening a database connection. Without RDS Proxy, this exhausts the database's max_connections limit. RDS Proxy pools connections and reuses them, reducing database load by 90%+. Also reduces failover time from ~60s to ~1s.

---

## 7.11 DynamoDB — Advanced Features

### DynamoDB Accelerator (DAX)

In-memory cache for DynamoDB. Microsecond latency for reads. No application code changes needed.

```
App ──▶ DAX Cluster ──▶ DynamoDB
        (cache hit: μs)   (cache miss: ms)
```

DAX vs ElastiCache: DAX is for DynamoDB-specific caching. ElastiCache is for general-purpose caching or when you need to store aggregation results.

### DynamoDB Streams

Capture item-level changes (insert, update, delete) as an ordered stream of events.

```
DynamoDB Table ──▶ DynamoDB Stream ──▶ Lambda (process changes)
                                   ──▶ Kinesis Data Streams
```

Use cases: Trigger Lambda on data changes, replicate data, analytics, audit logging.

### DynamoDB Global Tables

Multi-region, multi-active replication. Read and write to any region.

- Requires DynamoDB Streams enabled
- Active-Active: read/write in any region
- Replication latency: typically < 1 second

### DynamoDB TTL (Time To Live)

Automatically delete items after a specified timestamp. No cost for deletions.

```bash
aws dynamodb update-time-to-live \
  --table-name SessionTable \
  --time-to-live-specification Enabled=true,AttributeName=expiration_time
```

---

## 7.12 Amazon Cognito

Cognito provides authentication, authorization, and user management for web and mobile apps.

### Cognito User Pools (CUP)

Sign-in functionality — user directory with sign-up, sign-in, MFA, social login (Google, Facebook, SAML).

```
User ──▶ Cognito User Pool ──▶ JWT Token ──▶ API Gateway ──▶ Lambda
```

### Cognito Identity Pools (Federated Identities)

Provide temporary AWS credentials to users so they can access AWS services directly (e.g., S3, DynamoDB).

```
User ──▶ Login (CUP, Google, etc.) ──▶ Cognito Identity Pool ──▶ Temporary AWS Credentials
                                                                    ──▶ Access S3, DynamoDB directly
```

---

## 7.13 API Gateway — Endpoint Types and Security

### Endpoint Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Edge-Optimized** (default) | Routed through CloudFront edge locations | Global clients |
| **Regional** | For clients in the same region | Same-region clients, custom CloudFront setup |
| **Private** | Accessible only from within VPC via VPC Endpoint | Internal microservices |

```bash
# Create a Regional REST API
aws apigateway create-rest-api \
  --name "my-regional-api" \
  --endpoint-configuration types=REGIONAL

# Expected output:
# {
#   "id": "abc123def4",
#   "name": "my-regional-api",
#   "endpointConfiguration": {"types": ["REGIONAL"]}
# }

# Create a Private API (accessible only from VPC)
aws apigateway create-rest-api \
  --name "my-private-api" \
  --endpoint-configuration types=PRIVATE \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "execute-api:/*",
      "Condition": {
        "StringEquals": {"aws:sourceVpce": "vpce-0abcdef1234567890"}
      }
    }]
  }'

# Create a VPC Endpoint for API Gateway (required for Private APIs)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0abcdef1234567890 \
  --service-name com.amazonaws.us-east-1.execute-api \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0abcdef1234567890 \
  --security-group-ids sg-0abcdef1234567890 \
  --private-dns-enabled

# Invoke the private API from within the VPC
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/prod/resource
```

### Security Options

- **IAM Roles/Policies**: For AWS users/services
- **Cognito User Pools**: For external users (returns JWT)
- **Lambda Authorizer** (Custom Authorizer): Custom auth logic in Lambda
- **API Keys + Usage Plans**: For rate limiting and throttling

### API Gateway + Lambda Example

```python
import json

def lambda_handler(event, context):
    body = "Hello from Lambda!"
    return {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json"
        }
    }
```

---

## 7.14 SQS — Advanced Features

### SQS Message Visibility Timeout

After a consumer receives a message, it becomes invisible to other consumers for the visibility timeout period (default: 30 seconds). If not deleted within this time, the message becomes visible again (reprocessed). Call `ChangeMessageVisibility` to extend.

```bash
# Set visibility timeout when creating a queue
aws sqs create-queue --queue-name my-queue \
  --attributes VisibilityTimeout=60

# Change visibility timeout for a specific message (extend processing time)
aws sqs change-message-visibility \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-queue \
  --receipt-handle "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a..." \
  --visibility-timeout 120

# Receive a message with custom visibility timeout
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/my-queue \
  --visibility-timeout 45 \
  --max-number-of-messages 1

# Expected output:
# {
#   "Messages": [{
#     "MessageId": "abcdef-1234",
#     "ReceiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
#     "Body": "{\"orderId\": 12345}"
#   }]
# }
```

**Best practice:** Set visibility timeout to 6x your average processing time. If processing takes 10 seconds, set timeout to 60 seconds. If a consumer crashes, the message becomes visible again after the timeout and another consumer picks it up.

### SQS FIFO Queue

Guarantees ordering and exactly-once processing. Throughput: 300 msg/s (without batching), 3,000 msg/s (with batching). Queue name must end with `.fifo`.

### SQS as Buffer to Database Writes

```
Client ──▶ SQS Queue ──▶ ASG (EC2 workers) ──▶ Database
```

Decouples writes — if DB is slow, messages queue up instead of failing.

---

## 7.15 SNS — Advanced Features

### SNS FIFO Topic

Ordered message delivery. Can only have SQS FIFO queues as subscribers.

### SNS Message Filtering

JSON policy on the subscription to filter which messages are delivered.

```json
{
    "store": ["shoes"],
    "price_usd": [{"numeric": [">=", 100]}]
}
```

Only messages matching the filter are delivered to that subscriber.

---

## 7.16 SQS vs SNS vs Kinesis

| Feature | SQS | SNS | Kinesis |
|---------|-----|-----|---------|
| **Model** | Queue (pull) | Pub/Sub (push) | Stream (pull) |
| **Consumers** | 1 consumer per message | Many subscribers | Many consumers per shard |
| **Ordering** | FIFO only | FIFO only | Per shard |
| **Retention** | 1–14 days | No retention | 1–365 days |
| **Throughput** | Unlimited | Unlimited | Per shard (1 MB/s in) |
| **Replay** | No | No | Yes |
| **Use case** | Decouple, buffer | Fan-out, notifications | Real-time analytics, logs |

**Decision guide:**
- Need to decouple two services? → **SQS**
- Need to send one message to many receivers? → **SNS** (or SNS + SQS fan-out)
- Need to process a stream of data with multiple consumers and replay? → **Kinesis**
- Need ordering + exactly-once? → **SQS FIFO** or **Kinesis**

```bash
# Common pattern: SNS + SQS Fan-out
# One SNS topic fans out to multiple SQS queues

# Create SNS topic
aws sns create-topic --name order-events
# arn:aws:sns:us-east-1:123456789012:order-events

# Create SQS queues for different consumers
aws sqs create-queue --queue-name email-notifications
aws sqs create-queue --queue-name inventory-updates
aws sqs create-queue --queue-name analytics-pipeline

# Subscribe each queue to the SNS topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:email-notifications

aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789012:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:123456789012:inventory-updates

# Publish one message → all 3 queues receive it
aws sns publish \
  --topic-arn arn:aws:sns:us-east-1:123456789012:order-events \
  --message '{"orderId": 12345, "status": "placed"}'
```

---

## 7.17 Amazon MQ

Managed message broker for Apache ActiveMQ and RabbitMQ. Use when migrating from on-premises message brokers that use open protocols (MQTT, AMQP, STOMP, OpenWire, WSS).

- Runs on dedicated instances (not serverless)
- Supports Multi-AZ with failover
- Has both queue and topic features

```bash
# Create an Amazon MQ broker (RabbitMQ)
aws mq create-broker \
  --broker-name my-rabbitmq \
  --engine-type RABBITMQ \
  --engine-version 3.11.20 \
  --host-instance-type mq.m5.large \
  --deployment-mode CLUSTER_MULTI_AZ \
  --users '[{"Username":"admin","Password":"MyPassword123!","ConsoleAccess":true}]' \
  --publicly-accessible false \
  --subnet-ids subnet-0abcdef1234567890 subnet-0fedcba0987654321 subnet-0aabbccdd1122334

# Expected output:
# {
#   "BrokerId": "b-1234-5678-abcd",
#   "BrokerArn": "arn:aws:mq:us-east-1:123456789012:broker:b-1234-5678-abcd"
# }

# Get broker details (including endpoints)
aws mq describe-broker --broker-id b-1234-5678-abcd \
  --query '{Endpoints:BrokerInstances[0].Endpoints,Console:BrokerInstances[0].ConsoleURL}'

# Connect using AMQP (Python example)
# import pika
# connection = pika.BlockingConnection(
#     pika.URLParameters('amqps://admin:MyPassword123!@b-1234-5678-abcd.mq.us-east-1.amazonaws.com:5671')
# )
# channel = connection.channel()
# channel.queue_declare(queue='orders')
# channel.basic_publish(exchange='', routing_key='orders', body='Order #12345')
```

**When to use:** Migrating existing apps that use standard messaging protocols. For new cloud-native apps, use SQS/SNS instead.

| Feature | Amazon MQ | SQS/SNS |
|---------|-----------|---------|
| **Protocols** | AMQP, MQTT, STOMP, OpenWire | AWS SDK only |
| **Migration** | Drop-in replacement for ActiveMQ/RabbitMQ | Requires code changes |
| **Scaling** | Manual (instance size) | Automatic (serverless) |
| **Cost** | Instance-based (always running) | Pay per message |

---

## 7.18 Key Takeaways

1. Lambda: Pay per invocation (1M free/month), max 15 min timeout, 10 GB memory
2. Use API Gateway for HTTP endpoints; HTTP API is cheaper than REST API
3. Lambda + DynamoDB + API Gateway = fully serverless stack
4. Use Lambda Layers for shared dependencies
5. Use aliases and weighted routing for canary deployments
6. Cold starts matter for latency-sensitive apps — use Provisioned Concurrency or SnapStart (Java)
7. Lambda in VPC needs NAT Gateway for internet access, VPC Endpoints for AWS services
8. Use RDS Proxy between Lambda and RDS for connection pooling
9. DAX for DynamoDB caching (microsecond reads); ElastiCache for general caching
10. DynamoDB Streams + Lambda for event-driven processing on data changes
11. Cognito User Pools for authentication; Identity Pools for temporary AWS credentials
12. CloudFront Functions for lightweight edge logic; Lambda@Edge for complex edge processing
