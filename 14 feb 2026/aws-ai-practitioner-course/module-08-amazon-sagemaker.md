# Module 8: Amazon SageMaker

## 8.1 What is Amazon SageMaker?

Amazon SageMaker AI is a fully managed service for developers and data scientists to build, train, and deploy ML models. It covers the entire ML workflow in one place.

**Example: Predicting AWS Exam Scores**

```
Historical Data:                    New Data:
┌──────────────────────────┐       ┌──────────────────────────┐
│ exam scores              │       │ 3 yr experience in IT    │
│ years of IT experience   │       │ 1 yr on AWS              │
│ years of AWS experience  │       │ 10 hr on the course      │
│ time spent on course     │       └────────────┬─────────────┘
│ + passing score (output) │                    │
└────────────┬─────────────┘                    ▼
             │                          ┌──────────────┐
             ▼                          │ Apply Model  │
    ┌──────────────────┐                │              │
    │ Feature Engineer │                │ Prediction:  │
    │ → Build Model    │                │ PASS WITH 906│
    │ → Train & Tune   │                └──────────────┘
    └──────────────────┘
```

### SageMaker End-to-End Workflow

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Collect & Prepare│──>│ Build and Train  │──>│ Deploy Models    │
│                  │   │                  │   │ & Monitor        │
│ - Data Wrangler  │   │ - Built-in algos │   │ - Endpoints      │
│ - Feature Store  │   │ - Custom code    │   │ - Model Monitor  │
│ - Ground Truth   │   │ - AMT            │   │ - Model Registry │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 8.2 SageMaker Studio

A web-based, end-to-end ML development interface.

| Feature | Description |
|---------|-------------|
| **Unified Interface** | All SageMaker tools in one place |
| **Team Collaboration** | Share notebooks, experiments, models |
| **Tune & Debug** | Hyperparameter tuning, model debugging |
| **Deploy** | One-click deployment with auto-scaling |
| **Automated Workflows** | Build ML pipelines |

### Step-by-Step: Open SageMaker Studio (via Console UI)

1. **Navigate to SageMaker** → AWS Console → Search **"SageMaker"**
2. **Set Up a Domain** (first time only)
   - Click **"Set up SageMaker Domain"** → **"Quick setup"**
   - Select an execution role → Click **"Submit"**
   - Wait 5-10 minutes
3. **Open Studio** → Click **"Open Studio"** next to your user profile
4. **Create a Notebook** → File → New → Notebook → Select kernel (e.g., Python 3)

---

## 8.3 SageMaker Data Wrangler

Prepare tabular and image data for ML without writing code.

| Feature | Description |
|---------|-------------|
| **Data Selection** | Import from S3, Athena, Redshift, Snowflake |
| **Data Cleansing** | Handle missing values, remove duplicates |
| **Exploration & Visualization** | Charts, statistics, data profiling |
| **Transformation** | Drop columns, encode categories, normalize numbers |
| **SQL Support** | Query data using SQL |
| **Data Quality** | Built-in data quality checks |
| **Quick Model** | Train a quick model to validate data quality |
| **Export** | Generate processing jobs; output to S3 or Feature Store |

### Step-by-Step: Use Data Wrangler (via Console UI)

1. **Open Data Wrangler** in SageMaker Studio → Click **"Data Wrangler"**
2. **Import Data** → Choose source (S3, Athena, Redshift, Snowflake) → Select dataset
3. **Preview Data** → View data in a spreadsheet-like interface
4. **Visualize Data** → Create charts and histograms to understand distributions
5. **Transform Data** → Click **"Add step"** → Choose transformations (drop columns, handle missing values, normalize)
6. **Quick Model** → Train a quick model to validate your data is ML-ready
7. **Export** → Generate a processing job or publish to Feature Store

---

## 8.4 SageMaker Feature Store

A centralized repository for ML features, enabling feature reuse across teams and models.

| Feature | Description |
|---------|-------------|
| **Ingest Features** | From various sources |
| **Transform Data** | Define transformations within Feature Store |
| **Publish from Data Wrangler** | Direct integration |
| **Discoverable** | Features are searchable within SageMaker Studio |
| **Reuse** | High-quality features shared across datasets and teams |

> **What are ML Features?** Features are inputs to ML models used during training and inference. Example: in a music dataset, features include song ratings, listening duration, and listener demographics. Having high-quality, reusable features across your company is important.

---

## 8.5 SageMaker Clarify

Tools for model evaluation, explainability, and bias detection.

### Model Evaluation

| Feature | Description |
|---------|-------------|
| **Compare Models** | Evaluate and compare foundation models side by side |
| **Human Factors** | Evaluate friendliness, humor, helpfulness |
| **Work Teams** | Use AWS-managed team or your own employees |
| **Datasets** | Use built-in datasets or bring your own |
| **Metrics** | Built-in metrics and algorithms |

### Model Explainability

| Feature | Description |
|---------|-------------|
| **Pre-deployment** | Understand model characteristics before deployment |
| **Post-deployment** | Debug predictions after deployment |
| **Trust** | Increase trust and understanding of the model |
| **Example Questions** | "Why did the model reject this loan application?" / "Why was this prediction incorrect?" |

### Bias Detection

| Feature | Description |
|---------|-------------|
| **Dataset Bias** | Detect biases in training data |
| **Model Bias** | Detect biases in model predictions |
| **Statistical Metrics** | Measure bias using statistical methods |
| **Automatic Detection** | Specify input features and bias is automatically detected |

### Step-by-Step: Detect Bias with SageMaker Clarify (via Console UI)

1. **Open SageMaker Studio** → Navigate to **"Clarify"**
2. **Select Dataset** → Specify S3 path to training data
3. **Configure** → Specify label column, sensitive attribute (e.g., gender, age)
4. **Select Metrics** → Choose bias metrics to compute
5. **Run Analysis** → Create processing job → Wait for completion
6. **Review Results** → View bias report with metrics

---

## 8.6 SageMaker Ground Truth

Data labeling and RLHF (Reinforcement Learning from Human Feedback).

| Feature | Description |
|---------|-------------|
| **RLHF** | Align models to human preferences using human feedback in reward functions |
| **Model Review** | Human review, customization, and evaluation of models |
| **Data Labeling** | Create labels for training data (annotation) |
| **Reviewers** | Amazon Mechanical Turk workers, your employees, or third-party vendors |
| **Ground Truth Plus** | Managed labeling service |

```
Reviewers:
┌──────────────────┐
│ Mechanical Turk  │
│ 3rd Party        │──► Create Labels ──► Dog, Cat, Ship...
│ Your Employees   │
└──────────────────┘
```

---

## 8.7 Training Models with SageMaker

### Built-in Algorithms

| Category | Algorithms | Use Case |
|----------|-----------|----------|
| **Supervised** | Linear Learner, KNN | Regression, classification |
| **Unsupervised** | K-Means, PCA | Clustering, dimensionality reduction |
| **Anomaly Detection** | Random Cut Forest | Detect outliers |
| **Textual / NLP** | BlazingText, Seq2Seq | Text classification, summarization |
| **Image Processing** | Image Classification, Object Detection | Classify and detect objects |
| **Tabular** | XGBoost | Classification, regression on structured data |
| **Time Series** | DeepAR (uses RNN) | Forecasting |

### Automatic Model Tuning (AMT)

| Feature | Description |
|---------|-------------|
| **Define Objective Metric** | Specify what to optimize (accuracy, F1, etc.) |
| **Automatic Ranges** | AMT chooses hyperparameter ranges and search strategy |
| **Early Stopping** | Stops tuning jobs that aren't improving |
| **Cost Savings** | Prevents wasting money on suboptimal configurations |

### Step-by-Step: Train a Model (via Console UI)

1. **Navigate to SageMaker** → **"Training"** → **"Training jobs"** → **"Create"**
2. **Configure** → Enter job name, select algorithm (e.g., XGBoost), select instance type
3. **Set Hyperparameters** → Configure algorithm-specific parameters
4. **Specify Data** → S3 path for training data and output location
5. **Start Training** → Monitor progress, view metrics (loss, accuracy)

### Sample Code: Train with SageMaker SDK

```python
import sagemaker
from sagemaker import get_execution_role
from sagemaker.inputs import TrainingInput

role = get_execution_role()
session = sagemaker.Session()

xgb = sagemaker.estimator.Estimator(
    image_uri=sagemaker.image_uris.retrieve('xgboost', session.boto_region_name, '1.5-1'),
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    output_path=f's3://{session.default_bucket()}/output',
    sagemaker_session=session
)

xgb.set_hyperparameters(
    max_depth=5, eta=0.2, num_round=100,
    objective='binary:logistic', eval_metric='auc'
)

train_input = TrainingInput(s3_data='s3://my-bucket/train/train.csv', content_type='csv')
xgb.fit({'train': train_input})
```

**Output:**
```
[0]#011train-auc:0.8234
[50]#011train-auc:0.9456
[99]#011train-auc:0.9623
Training job completed
```

---

## 8.8 Deploying Models

### Inference Types Comparison

| Type | Latency | Payload | Max Time | Use Case |
|------|---------|---------|----------|----------|
| **Real-time** | Low (ms-seconds) | Up to 6 MB | 60 seconds | Fast predictions for web/mobile apps |
| **Serverless** | Low (ms-seconds) | Up to 4 MB | 60 seconds | Sporadic traffic, tolerates cold starts |
| **Asynchronous** | Medium-High | Up to 1 GB | 1 hour | Large payloads, longer processing |
| **Batch Transform** | High (min-hours) | Up to 100 MB/invocation | 1 hour | Bulk processing, large datasets |

```
Real-time:     App ──► Auto-Scaling Endpoint (CPU/GPU) ──► Result
Serverless:    App ──► Serverless Endpoint (auto-scales to zero) ──► Result
Asynchronous:  App ──► Job Queue ──► Async Endpoint ──► S3 (results)
Batch:         S3 (dataset) ──► Batch Transform ──► S3 (results)
```

### Step-by-Step: Deploy a Model (via Console UI)

1. **Create a Model** → **"Inference"** → **"Models"** → **"Create model"** → Specify S3 artifact path
2. **Create Endpoint Configuration** → Select instance type, initial count
3. **Create Endpoint** → Select configuration → Wait 5-10 minutes
4. **Test** → Use SDK to send predictions:

```python
import boto3, json

runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
response = runtime.invoke_endpoint(
    EndpointName='my-endpoint',
    ContentType='text/csv',
    Body='0.5,1.2,3.4,0.8,2.1'
)
result = json.loads(response['Body'].read().decode())
print(f"Prediction: {result}")  # Output: 0.8734 (87.34% probability)
```

---

## 8.9 SageMaker ML Governance

### Model Cards

| Feature | Description |
|---------|-------------|
| **Purpose** | Standardized documentation for ML models |
| **Content** | Intended uses, risk ratings, training details, metrics |
| **Source Citations** | Data origin documentation, licenses, known biases |
| **Audit Support** | Centralized place for audit activities |

> **AWS AI Service Cards** are examples of model cards published by AWS for their managed AI services.

### Model Dashboard

| Feature | Description |
|---------|-------------|
| **Centralized Portal** | View, search, and explore all your models |
| **Deployment Tracking** | Track which models are deployed for inference |
| **Threshold Violations** | Find models violating data quality, model quality, bias, or explainability thresholds |
| **Access** | Available from SageMaker Console |

### Model Monitor

| Feature | Description |
|---------|-------------|
| **Quality Monitoring** | Monitor model quality in production (continuous or scheduled) |
| **Drift Detection** | Alerts for deviations in model quality |
| **Example** | Loan model starts approving people with incorrect credit scores (drift) |
| **Action** | Fix data and retrain model |

### Model Registry

| Feature | Description |
|---------|-------------|
| **Version Control** | Track, manage, and version ML models |
| **Metadata** | Catalog models, associate metadata |
| **Approval Status** | Manage approval workflows |
| **Deployment** | Automate model deployment |
| **Sharing** | Share models across teams |

### Role Manager

| Feature | Description |
|---------|-------------|
| **Access Control** | Define roles for different personas |
| **Examples** | Data scientists, MLOps engineers, business analysts |

---

## 8.10 SageMaker Pipelines

CI/CD (Continuous Integration / Continuous Delivery) for Machine Learning.

| Feature | Description |
|---------|-------------|
| **Automated Workflows** | Automate building, training, and deploying ML models |
| **Scale** | Build, train, test, and deploy hundreds of models automatically |
| **Benefits** | Iterate faster, reduce errors (no manual steps), repeatable |

### Pipeline Step Types

| Step Type | Purpose |
|-----------|---------|
| **Processing** | Data processing (e.g., feature engineering) |
| **Training** | Train a model |
| **Tuning** | Hyperparameter tuning (HPO) |
| **AutoML** | Automatically train a model |
| **Model** | Create or register a SageMaker model |
| **ClarifyCheck** | Drift checks for data bias, model bias, model explainability |
| **QualityCheck** | Drift checks for data quality, model quality |

---

## 8.11 SageMaker JumpStart

An ML Hub for finding and deploying pre-trained models and solutions.

### Option 1: ML Hub (Foundation Models)

```
Browse ──► Experiment ──► Customize ──► Deploy
(public &    (test before    (fine-tune     (deploy & run
proprietary   choosing)       with your      inference)
FMs)                         data)
```

- Large collection from Hugging Face, Databricks, Meta, Stability AI
- Models can be fully customized for your data and use case
- Models deployed on SageMaker directly (full control of deployment)

### Option 2: ML Solutions (Pre-built Templates)

```
Access & Browse ──► Select & Customize ──► Deploy
(AWS CloudFormation   (use your own data)    (few clicks)
templates)
```

- Pre-built solutions for demand forecasting, credit prediction, fraud detection, computer vision

---

## 8.12 SageMaker Canvas

Build ML models using a **visual interface** — no coding required.

| Feature | Description |
|---------|-------------|
| **Visual Interface** | Point-and-click ML model building |
| **Ready-to-Use Models** | Access models from Bedrock or JumpStart |
| **Custom Models** | Build with AutoML (SageMaker Autopilot) |
| **Data Preparation** | Leverage Data Wrangler |
| **AWS AI Services** | Use Rekognition, Comprehend, Textract directly |
| **Part of Studio** | Integrated into SageMaker Studio |

### Step-by-Step: Build a Model with Canvas (via Console UI)

1. **Open Canvas** → SageMaker Console → **"Canvas"** → **"Open Canvas"**
2. **Import Data** → Upload CSV or connect to S3
3. **Select Target** → Choose the column to predict (e.g., "Churn")
4. **Build** → **"Quick build"** (2-15 min) or **"Standard build"** (2-4 hrs, more accurate)
5. **Analyze** → View accuracy, feature importance
6. **Predict** → Upload new data or enter values manually

---

## 8.13 MLFlow on SageMaker

| Feature | Description |
|---------|-------------|
| **MLFlow** | Open-source tool for managing the entire ML lifecycle |
| **Tracking Servers** | Track runs and experiments |
| **Integration** | Launch on SageMaker with a few clicks, fully integrated with Studio |

---

## 8.14 SageMaker Extra Features

| Feature | Description |
|---------|-------------|
| **Network Isolation Mode** | Run job containers without outbound internet access (can't even access S3) |
| **DeepAR Forecasting** | Time series forecasting using Recurrent Neural Networks (RNN) |

---

## Module 8 Summary

| Component | Key Takeaway |
|-----------|-------------|
| **SageMaker** | End-to-end managed ML service |
| **Studio** | Unified web IDE — collaborate, tune, debug, deploy |
| **Data Wrangler** | No-code data preparation, transformation, visualization |
| **Feature Store** | Centralized, reusable ML feature repository |
| **Clarify** | Model evaluation, explainability (SHAP), bias detection |
| **Ground Truth** | RLHF, data labeling with human reviewers |
| **Built-in Algorithms** | Supervised, unsupervised, NLP, image, XGBoost, DeepAR |
| **AMT** | Automatic hyperparameter tuning |
| **Inference Types** | Real-time (6MB/60s), Serverless (cold starts), Async (1GB), Batch (100MB) |
| **Model Cards** | Standardized ML model documentation |
| **Model Dashboard** | Centralized view of all models, threshold violations |
| **Model Monitor** | Production quality monitoring, drift detection |
| **Model Registry** | Version control, approval workflows |
| **Pipelines** | CI/CD for ML — automated build/train/deploy workflows |
| **JumpStart** | ML Hub (pre-trained FMs) + ML Solutions (templates) |
| **Canvas** | No-code ML with visual interface, AutoML |
| **MLFlow** | Open-source ML lifecycle management on SageMaker |

---

*Previous: [Module 7 — AWS Managed AI Services](module-07-aws-managed-ai-services.md)*
*Next: [Module 9 — Responsible AI, Security, Compliance and Governance](module-09-responsible-ai.md)*
