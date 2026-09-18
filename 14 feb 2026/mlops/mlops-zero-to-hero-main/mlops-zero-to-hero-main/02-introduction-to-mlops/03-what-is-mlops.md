# What is MLOps?

MLOps stands for **Machine Learning Operations**.

In simple words, **MLOps is DevOps for machine learning**. It is directly inspired by DevOps and brings the same automation principles into the ML world.

To understand MLOps, let's first revisit what DevOps is and the problem it solved.

---

## Quick Recap: What is DevOps?

DevOps = **Development + Operations**

DevOps is a set of best practices that unify development activities and operations activities so that an organization can ship applications **faster, safer, and more reliably**.

---

## The Problem: Without DevOps

Imagine an organization building a website **without DevOps**. Here's what happens:

```
┌──────────────────────────────────────────────────────────────────────┐
│           WITHOUT DevOps — MANUAL SOFTWARE DELIVERY                  │
│                                                                      │
│   DEVELOPMENT TEAM (all manual)          OPERATIONS TEAM (all manual)│
│   ┌─────────────────────────┐            ┌─────────────────────────┐ │
│   │ 1. Write source code    │            │ 1. Set up app server    │ │
│   │ 2. Build app locally    │───share───►│ 2. Set up load balancer │ │
│   │ 3. Test app locally     │  info      │ 3. Configure API gateway│ │
│   │ 4. QA testing           │            │ 4. Set up SSL           │ │
│   │                         │            │ 5. Containerize the app │ │
│   │  ALL MANUAL             │            │ 6. Deploy to Kubernetes │ │
│   └─────────────────────────┘            │                         │ │
│                                          │  ALL MANUAL             │ │
│                                          └─────────────────────────┘ │
│                                                                      │
│   ⚠️  Applications are rarely built in the first iteration.          │
│       Teams may need 10+ iterations.                                 │
│       EVERY iteration = repeat ALL manual steps on BOTH sides.       │
│                                                                      │
│   Result: Extremely slow delivery, error-prone, frustrating.        │
└──────────────────────────────────────────────────────────────────────┘
```

### The iteration problem

Applications are not built in one go. The development team might need **10 iterations** to get the website right. For **every single iteration**:

- Development team manually writes, builds, tests, and coordinates with QA
- Operations team manually sets up servers, load balancers, SSL, containers, Kubernetes

Imagine how much time this takes.

---

## The Solution: With DevOps

DevOps automates most of these activities and ships the application much faster.

```
┌──────────────────────────────────────────────────────────────────────┐
│           WITH DevOps — AUTOMATED SOFTWARE DELIVERY                  │
│                                                                      │
│   Developer makes          DevOps Pipeline (CI/CD)                   │
│   a code change            ┌──────────────────────────────────┐      │
│        │                   │                                  │      │
│        └──────────────────►│  1. Build app         AUTOMATIC  │      │
│                            │  2. Run unit tests    AUTOMATIC  │      │
│                            │  3. Run functional    AUTOMATIC  │      │
│                            │     tests                        │      │
│                            │  4. Deploy to target  AUTOMATIC  │      │
│                            │     environment                  │      │
│                            └──────────────────────────────────┘      │
│                                                                      │
│   DevOps engineers also automate:                                    │
│   • Infrastructure as Code (IaC) — servers, networks, cloud setup   │
│   • Kubernetes management — cluster setup, scaling, monitoring       │
│   • Monitoring & alerting — application health, performance          │
│                                                                      │
│   Result: Every code change → automatically built, tested, deployed. │
│           10 iterations happen in hours, not weeks.                   │
└──────────────────────────────────────────────────────────────────────┘
```

### What DevOps automates:

| Activity | How |
|----------|-----|
| Build | CI pipeline triggers on every code change |
| Test | Unit tests, integration tests run automatically |
| Deploy | CD pipeline deploys to staging/production |
| Infrastructure | IaC tools (Terraform, Ansible) provision servers |
| Containers | Docker builds and Kubernetes deployments automated |
| Monitoring | Prometheus, Grafana track application health |

---

## Now Apply the Same Thinking to Machine Learning

Looking at what DevOps did for traditional applications, **MLOps came into picture** because building and shipping ML models to production is equally tedious — if not more.

---

## The Problem: Without MLOps

Imagine an organization (say, an OTT platform) building a **recommendation engine model** without MLOps:

```
┌──────────────────────────────────────────────────────────────────────┐
│           WITHOUT MLOps — MANUAL MODEL DELIVERY                      │
│                                                                      │
│   DATA SCIENTISTS + ML ENGINEERS         OPERATIONS TEAM             │
│   (all manual)                           (all manual)                │
│   ┌─────────────────────────┐            ┌─────────────────────────┐ │
│   │ 1. Collect & prepare    │            │ 1. Set up load balancer │ │
│   │    data                 │            │ 2. Set up API gateway   │ │
│   │ 2. Develop model        │───share───►│ 3. Containerize model   │ │
│   │ 3. Evaluate model       │  info      │ 4. Deploy to Kubernetes │ │
│   │ 4. Validate model       │            │ 5. Set up CDN           │ │
│   │ 5. Build API for model  │            │ 6. Configure monitoring │ │
│   │ 6. Test model locally   │            │                         │ │
│   │                         │            │  ALL MANUAL             │ │
│   │  ALL MANUAL             │            └─────────────────────────┘ │
│   └─────────────────────────┘                                        │
│                                                                      │
│   ⚠️  Models are rarely good enough in the first iteration.          │
│       Data scientists may need 10-20 iterations to get the           │
│       required model accuracy.                                       │
│       EVERY iteration = repeat ALL manual steps on BOTH sides.       │
│                                                                      │
│   Result: Months to ship a model. Painful, slow, unreliable.        │
└──────────────────────────────────────────────────────────────────────┘
```

### The iteration problem (even worse for ML)

The recommendation engine model might not perform well in the first iteration. Data scientists and ML engineers may need **10 to 20 iterations** to achieve the required accuracy. Every time:

- Data scientists manually collect data, train, evaluate, validate
- ML engineers manually build APIs, test locally
- Operations team manually sets up infrastructure, deploys

This is the same problem DevOps solved for traditional apps — but now for ML.

---

## The Solution: With MLOps

MLOps automates the machine learning lifecycle, just like DevOps automates the software development lifecycle.

```
┌──────────────────────────────────────────────────────────────────────┐
│           WITH MLOps — AUTOMATED MODEL DELIVERY                      │
│                                                                      │
│   Data Scientist /         MLOps Pipeline (CI/CD for Models)         │
│   ML Engineer makes        ┌──────────────────────────────────┐      │
│   a change                 │                                  │      │
│        │                   │  1. Data validation   AUTOMATIC  │      │
│        └──────────────────►│  2. Model training    AUTOMATIC  │      │
│                            │  3. Model evaluation  AUTOMATIC  │      │
│                            │  4. Model packaging   AUTOMATIC  │      │
│                            │  5. Model deployment  AUTOMATIC  │      │
│                            │  6. Model monitoring  AUTOMATIC  │      │
│                            └──────────────────────────────────┘      │
│                                                                      │
│   MLOps engineers also handle:                                       │
│   • Infrastructure as Code — cloud resources, GPU clusters           │
│   • Kubernetes management — model serving, scaling                   │
│   • Observability — model drift, prediction quality, latency         │
│   • Tool setup — MLflow, DVC, KServe, Kubeflow configuration        │
│   • Automation — retraining triggers, data pipeline scheduling       │
│                                                                      │
│   Result: Every model change → automatically trained, tested,        │
│           packaged, deployed. Iterations happen in hours.             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## MLOps = DevOps Practices Applied to ML

| DevOps Concept | MLOps Equivalent |
|----------------|------------------|
| Source code versioning (Git) | Data versioning (DVC) + model versioning |
| CI pipelines (build & test code) | Model training pipelines (train & evaluate models) |
| CD pipelines (deploy apps) | Automated model deployment (KServe, SageMaker) |
| Monitoring services (Prometheus) | Monitoring model performance (drift, accuracy) |
| Rollbacks (revert bad deploy) | Model version rollback (serve previous model) |
| Infrastructure as Code (Terraform) | ML infrastructure automation (GPU clusters, storage) |
| Containerization (Docker) | Model containerization (Docker + model serving) |

---

## Side-by-Side: DevOps vs MLOps

```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│          DevOps              │    │          MLOps               │
│                              │    │                              │
│  FOR: Traditional apps       │    │  FOR: ML models              │
│  (websites, APIs,            │    │  (recommendation engines,    │
│   microservices)             │    │   fraud detection, etc.)     │
│                              │    │                              │
│  WHO: Developers +           │    │  WHO: Data Scientists +      │
│       DevOps Engineers       │    │       ML Engineers +         │
│                              │    │       MLOps Engineers        │
│                              │    │                              │
│  AUTOMATES:                  │    │  AUTOMATES:                  │
│  • Build                     │    │  • Data preparation          │
│  • Test                      │    │  • Model training            │
│  • Deploy                    │    │  • Model evaluation          │
│  • Monitor                   │    │  • Model deployment          │
│  • Infrastructure            │    │  • Model monitoring          │
│                              │    │  • Infrastructure            │
│                              │    │                              │
│  TOOLS:                      │    │  TOOLS:                      │
│  Jenkins, GitHub Actions,    │    │  MLflow, DVC, KServe,        │
│  Terraform, Docker, K8s     │    │  Kubeflow, SageMaker,        │
│                              │    │  Docker, K8s                 │
└─────────────────────────────┘    └─────────────────────────────┘
```

---

## Can DevOps and MLOps Coexist in a Company?

**Yes.** They are not replacements for each other. They serve different purposes and coexist in the same organization.

### Example 1: Netflix

```
┌──────────────────────────────────────────────────────────────────┐
│                         NETFLIX                                   │
│                                                                   │
│   Traditional Application          Machine Learning Model         │
│   ┌─────────────────────┐          ┌─────────────────────┐       │
│   │ Payments            │          │ Recommendation      │       │
│   │ Microservice        │          │ Engine              │       │
│   │                     │          │                     │       │
│   │ • Payment gateway   │          │ • Suggest movies    │       │
│   │ • Billing logic     │          │   based on watch    │       │
│   │ • Subscription mgmt │          │   history           │       │
│   │                     │          │ • Personalize by    │       │
│   │                     │          │   user location     │       │
│   └────────┬────────────┘          └────────┬────────────┘       │
│            │                                │                     │
│            ▼                                ▼                     │
│   ┌─────────────────┐              ┌─────────────────┐           │
│   │   DevOps Team   │              │   MLOps Team    │           │
│   │                 │              │                 │           │
│   │ Automates CI/CD │              │ Automates model │           │
│   │ for payments    │              │ training &      │           │
│   │ service         │              │ deployment      │           │
│   └─────────────────┘              └─────────────────┘           │
│                                                                   │
│   Both teams coexist. Different responsibilities.                │
└──────────────────────────────────────────────────────────────────┘
```

| Aspect | DevOps Team handles | MLOps Team handles |
|--------|--------------------|--------------------|
| **What** | Payments microservice | Recommendation engine model |
| **Trigger** | Developer pushes code change | Data scientist updates model |
| **Pipeline** | Build → Test → Deploy service | Train → Evaluate → Deploy model |
| **Monitoring** | Service uptime, latency, errors | Model accuracy, prediction drift |

### Example 2: PayPal

```
┌──────────────────────────────────────────────────────────────────┐
│                         PAYPAL                                    │
│                                                                   │
│   Traditional Application          Machine Learning Model         │
│   ┌─────────────────────┐          ┌─────────────────────┐       │
│   │ User Interface /    │          │ Fraud Detection     │       │
│   │ Login Microservice  │          │ Model               │       │
│   │                     │          │                     │       │
│   │ • Login page        │          │ • Detect fraudulent │       │
│   │ • User dashboard    │          │   transactions      │       │
│   │ • Account settings  │          │ • Flag suspicious   │       │
│   │                     │          │   activity           │       │
│   └────────┬────────────┘          └────────┬────────────┘       │
│            │                                │                     │
│            ▼                                ▼                     │
│   ┌─────────────────┐              ┌─────────────────┐           │
│   │   DevOps Team   │              │   MLOps Team    │           │
│   │                 │              │                 │           │
│   │ Automates CI/CD │              │ Automates model │           │
│   │ for UI/login    │              │ training &      │           │
│   │ service         │              │ deployment for  │           │
│   │                 │              │ fraud detection │           │
│   └─────────────────┘              └─────────────────┘           │
│                                                                   │
│   Both teams coexist. Different responsibilities.                │
└──────────────────────────────────────────────────────────────────┘
```

| Aspect | DevOps Team handles | MLOps Team handles |
|--------|--------------------|--------------------|
| **What** | UI / Login microservice | Fraud detection model |
| **Trigger** | Developer updates UI code | Data scientist retrains fraud model |
| **Pipeline** | Build → Test → Deploy UI | Train → Evaluate → Deploy model |
| **Monitoring** | Page load time, login errors | Fraud detection accuracy, false positives |

---

## Key Takeaway

> **MLOps is NOT a replacement for DevOps.** They are completely different.
> - DevOps → for traditional software applications
> - MLOps → for machine learning models
>
> Both can and do coexist in the same organization.

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   DevOps enhances ──► Software Development Lifecycle     │
│                                                          │
│   MLOps enhances  ──► Machine Learning Lifecycle         │
│                                                          │
│   Same principles. Different domains.                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Operations Team Activities: What Gets Automated

For reference, here are the manual activities that both DevOps and MLOps automate:

### Traditional App (DevOps automates)

| Activity | Tool Example |
|----------|-------------|
| Set up application server | Terraform, Ansible |
| Set up load balancer | AWS ALB, Nginx (via IaC) |
| Configure API gateway | Kong, AWS API Gateway |
| Set up SSL certificates | cert-manager, Let's Encrypt |
| Containerize the application | Docker, Buildpacks |
| Deploy to Kubernetes | Helm, ArgoCD |
| Monitoring | Prometheus, Grafana |

### ML Model (MLOps automates)

| Activity | Tool Example |
|----------|-------------|
| Data validation & preparation | Great Expectations, DVC |
| Model training | Kubeflow, SageMaker |
| Model evaluation & validation | MLflow, custom scripts |
| Set up load balancer | AWS ALB, Istio |
| Configure API gateway | Kong, AWS API Gateway |
| Containerize the model | Docker |
| Deploy to Kubernetes | KServe, Seldon |
| Set up CDN | CloudFront, Cloudflare |
| Model monitoring | Evidently, Prometheus |

---

## Example: What a CI/CD Pipeline Looks Like

### DevOps CI/CD (for a web app)

```yaml
# .github/workflows/deploy-app.yml
name: Deploy Web App

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build application
        run: npm run build

      - name: Run unit tests
        run: npm test

      - name: Build Docker image
        run: docker build -t myapp:latest .

      - name: Deploy to Kubernetes
        run: kubectl apply -f k8s/deployment.yaml
```

### MLOps CI/CD (for a model)

```yaml
# .github/workflows/deploy-model.yml
name: Deploy ML Model

on:
  push:
    branches: [main]
    paths:
      - 'model/**'
      - 'data/**'

jobs:
  deploy-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate data
        run: python scripts/validate_data.py

      - name: Train model
        run: python scripts/train.py

      - name: Evaluate model
        run: python scripts/evaluate.py --min-accuracy 0.95

      - name: Package model
        run: python scripts/package.py --format pkl

      - name: Build model container
        run: docker build -t fraud-model:latest -f Dockerfile.model .

      - name: Deploy model to KServe
        run: kubectl apply -f k8s/inference-service.yaml
```

Both pipelines follow the same principle: **automate everything that was previously manual**.

---

## Why MLOps is Harder than DevOps

ML systems have more moving parts than traditional software. In DevOps, you manage **code**. In MLOps, you manage **code + data + models** — all of which change independently.

| Challenge | Why it's harder in ML |
|-----------|----------------------|
| **Data versioning** | Code changes are tracked with Git. But what about the training data? A model trained on different data produces different results, even with identical code. |
| **Experiment tracking** | Data scientists run dozens of experiments with different algorithms, hyperparameters, and datasets. Every combination needs to be tracked and compared. |
| **Model versioning** | Unlike app versions (v1.0, v1.1), model versions depend on code version + data version + hyperparameters. |
| **Model drift** | Software doesn't degrade on its own. ML models do — as real-world data changes, model accuracy drops silently. |
| **Continuous retraining** | Apps don't need to be "retrained." Models do, regularly, as new data arrives. |
| **Bias & fairness** | Models can learn biases from training data. This needs ongoing monitoring — not something traditional apps deal with. |

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   DevOps manages:    Code                                │
│                                                          │
│   MLOps manages:     Code + Data + Models                │
│                      (all change independently)          │
│                                                          │
│   More moving parts = More automation required           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Iteration Difference: DevOps vs MLOps

### DevOps iteration (simpler)

```
Change Code → Rebuild → Redeploy
```

### MLOps iteration (more complex)

```
Change Code
     +
Change Data
     +
Tune Hyperparameters
     +
Retrain Model
     +
Evaluate Again
     +
Redeploy
```

In MLOps, a single "iteration" involves changing multiple things — code, data, and configuration — then retraining and re-evaluating before deploying. This is why automation matters even more.

---

## 10 Components of MLOps

These are the building blocks that make up an MLOps system:

| # | Component | Purpose | Tool Examples |
|---|-----------|---------|---------------|
| 1 | **Data Ingestion Pipeline** | Collect and load data from various sources | Apache Airflow, Kafka |
| 2 | **Data Validation** | Check data quality before training | Great Expectations, TFDV |
| 3 | **Feature Store** | Store and serve reusable features | Feast, Tecton |
| 4 | **Model Training Pipeline** | Automate training across experiments | Kubeflow, SageMaker Pipelines |
| 5 | **Experiment Tracking** | Log and compare experiments | MLflow, Weights & Biases |
| 6 | **Model Registry** | Version and store trained models | MLflow Model Registry, SageMaker |
| 7 | **CI/CD for Models** | Automate testing and deployment of models | GitHub Actions, Jenkins, ArgoCD |
| 8 | **Monitoring & Logging** | Track model performance in production | Prometheus, Grafana, Evidently |
| 9 | **Drift Detection** | Detect when data or model behavior changes | Evidently, NannyML |
| 10 | **Automated Retraining** | Trigger retraining when performance drops | Kubeflow, custom pipelines |

```
┌──────────────────────────────────────────────────────────────────┐
│                    MLOps COMPONENT MAP                            │
│                                                                   │
│   Data Layer          Training Layer        Serving Layer         │
│   ┌────────────┐      ┌────────────┐        ┌────────────┐      │
│   │ Ingestion  │─────►│ Training   │───────►│ Deployment │      │
│   │ Pipeline   │      │ Pipeline   │        │ (CI/CD)    │      │
│   ├────────────┤      ├────────────┤        ├────────────┤      │
│   │ Validation │      │ Experiment │        │ Monitoring │      │
│   ├────────────┤      │ Tracking   │        ├────────────┤      │
│   │ Feature    │      ├────────────┤        │ Drift      │      │
│   │ Store      │      │ Model      │        │ Detection  │      │
│   │            │      │ Registry   │        ├────────────┤      │
│   │            │      │            │        │ Auto       │      │
│   │            │      │            │        │ Retrain    │      │
│   └────────────┘      └────────────┘        └────────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Benefits of MLOps

| Benefit | Without MLOps | With MLOps |
|---------|--------------|------------|
| **Deployment speed** | Weeks to months | Hours to days |
| **Manual effort** | High — every step by hand | Low — automated pipelines |
| **Reproducibility** | Hard — "it worked on my laptop" | Easy — versioned data, code, models |
| **Collaboration** | Siloed teams | Shared pipelines and registries |
| **Scalability** | One model at a time | Multiple models in parallel |
| **Monitoring** | None or ad-hoc | Continuous, automated alerts |
| **Retraining** | Manual, infrequent | Automated, triggered by drift |
| **Reliability** | Models break silently | Issues caught early |

---

## Prerequisites: What You Should Know

To follow this course effectively, familiarity with these topics helps:

| Topic | Why it matters |
|-------|---------------|
| Software development lifecycle | MLOps mirrors SDLC patterns |
| CI/CD concepts | MLOps uses the same pipeline approach |
| Infrastructure as Code | MLOps automates cloud/infra setup |
| Kubernetes basics | Models are often deployed on K8s |
| ML lifecycle | Understanding what data scientists do |
| Model training & evaluation | Knowing what the pipeline automates |

Don't worry if you're not an expert in all of these — the course covers them progressively.
