# Introduction to MLflow

MLflow is an **open-source MLOps framework** used to manage the end-to-end machine learning lifecycle.  
It helps you **track experiments, manage models, and make ML work reproducible**.

In simple terms:
> MLflow helps you answer the question:  
> **“Which model did we train, with what parameters, and how good was it?”**

---

## Why MLflow Exists

Once you start building real ML projects, common problems appear:

- Multiple experiments with different parameters
- No clear record of which model performed best
- Difficult to reproduce results
- Models stored locally with no versioning
- Hard to move models from training to deployment

**MLflow solves these problems by acting as a central system of record for ML work.**

---

## Core Components of MLflow

MLflow has four main components. Beginners should focus mainly on the first two.

---

### MLflow Tracking

Used to **track experiments**.

You can log:
- Parameters (learning rate, epochs, etc.)
- Metrics (accuracy, loss, F1-score)
- Artifacts (model files, plots, datasets)
- Source code version

Each training run is stored as a **Run**.

Example:

    import mlflow

    with mlflow.start_run():
        mlflow.log_param("learning_rate", 0.01)
        mlflow.log_metric("accuracy", 0.92)

To view runs:

    mlflow ui

This opens a UI where you can compare experiments.

---

### MLflow Models

MLflow provides a **standard way to package models**.

This allows the same model to be:
- Loaded in Python
- Served via REST API
- Containerized using Docker
- Deployed to cloud or Kubernetes

This makes models **portable and production-ready**.

---

### MLflow Projects

A way to package ML code with:
- Environment details
- Entry points
- Reproducible execution

Mostly useful for larger teams and advanced workflows.

---

### MLflow Model Registry

A centralized place to manage models:
- Model versions
- Stages (Staging, Production, Archived)
- Metadata and approvals

Very useful in enterprise MLOps setups.

---

## Simple Real-World Example

Imagine a **Wine Quality Prediction** model.

You try:
- Run 1: learning_rate = 0.01 → accuracy = 0.86
- Run 2: learning_rate = 0.1 → accuracy = 0.89
- Run 3: learning_rate = 0.001 → accuracy = 0.82

Without MLflow:
- You forget results
- You overwrite models
- You guess which model to deploy

With MLflow:
- Every run is logged
- Metrics are compared visually
- Best model is clearly identified
- Model file is stored and versioned

---

## How MLflow Fits into MLOps

MLflow helps MLOps Engineers with:

- Experiment tracking
- Reproducibility
- Model lineage
- Model packaging
- Deployment readiness

In real projects, MLflow is often combined with:
- Git (code versioning)
- DVC (data versioning)
- GitHub Actions (CI/CD)
- Docker (containerization)
- Kubernetes (serving)
- Cloud storage like S3 (remote tracking)



