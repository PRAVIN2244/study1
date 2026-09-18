# What is SageMaker?

AWS SageMaker is Amazon’s fully managed platform for building, training, and deploying machine learning models at scale.

In real-world ML systems, the actual training code is only 5–10% of the work.

MLOps challenges include:

- Environment and dependency management
- Scalable training workloads
- Handling large datasets
- Model versioning
- Model registry
- Automated deployments
- Monitoring predictions & model drift
- Cost control for GPUs/instances

SageMaker bundles these into managed services so that MLOps engineers can avoid building the entire ML control plane from scratch.

### What MLOps Engineers Actually Do With SageMaker

A) Build ML Environments

- Prepare Docker images with Python/ML libraries
- Manage dependency consistency
- Use CDK/Terraform to provision infrastructure

B) Automate Training

- Use SageMaker Training Jobs with CI pipelines
- Configure distributed training
- Use Spot instances to control cost

C) Manage Model Registry

- Store versioned models
- Integrate approval workflows (“manual gate” for prod)

D) Automate Deployments

- Blue/Green deployments
- Canary deployments
- Event-driven retraining
- Update production endpoints with zero downtime

E) Observability & Monitoring

- CloudWatch for logs/metrics
- SageMaker Model Monitor for:
- Data drift
- Feature drift
- Prediction drift
- Outlier detection

F) Cost Optimization

- Spot training
- Multi-model endpoints
- Serverless endpoints

Endpoint autoscaling

