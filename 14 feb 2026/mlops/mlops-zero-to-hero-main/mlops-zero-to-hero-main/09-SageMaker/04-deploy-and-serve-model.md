# Deploy and Save Model for Inference using AWS SageMaker

### Create Inference Script (UI)

Inside SageMaker Studio:

Click File → New → Text File

Name it: inference.py

Paste this:

```
import joblib
import os
import json

def model_fn(model_dir):
    model = joblib.load(os.path.join(model_dir, "iris-model.pkl"))
    return model

def input_fn(request_body, request_content_type):
    data = json.loads(request_body)
    return data["instances"]

def predict_fn(input_data, model):
    return model.predict(input_data)

def output_fn(prediction, content_type):
    return json.dumps({"predictions": prediction.tolist()})
```

Save the file.

### Package Model for SageMaker

SageMaker does NOT deploy loose files. It expects a tar.gz file.

Run this in the notebook:

```
import tarfile

with tarfile.open("model.tar.gz", "w:gz") as tar:
    tar.add("iris-model.pkl")
    tar.add("inference.py")

print("model.tar.gz created")
```

### Upload model.tar.gz to S3

```
s3.upload_file(
    "model.tar.gz",
    bucket_name,
    "model-artifacts/model.tar.gz"
)

print("Packaged model uploaded to S3")
```

Now SageMaker can deploy this model.

### Create Model

Go to SageMaker → Models

Click Create model

Model name: `iris-demo-model`

Container settings

Framework: `Scikit-learn`

Version: `1.2`

Model data location: [Change accordingly]

`s3://my-sagemaker-demo-bucket-abhishek/model-artifacts/model.tar.gz`

IAM role

Select your SageMaker execution role

Click Create model

### Create Endpoint Configuration (UI)

Go to Inference → Endpoint configurations

Click Create endpoint configuration

Name: `iris-endpoint-config`

Production variant

Model: `iris-demo-model`

Instance type: `ml.t2.medium`

Initial instance count: `1`

Click Create

### Create Endpoint 

Go to Inference → Endpoints

Click Create endpoint

Endpoint name: `iris-demo-endpoint`

Select endpoint configuration: `iris-endpoint-config`

Click Create endpoint

⏳ Wait ~5–7 minutes

Status should become InService

### Test Endpoint (UI)

Open Endpoints

Click `iris-demo-endpoint`

Click Test inference

Input:

```
{
  "instances": [[5.1, 3.5, 1.4, 0.2]]
}
```

Click Test

You’ll see:

```
{"predictions":[0]}
```

🎉 Your model is live.