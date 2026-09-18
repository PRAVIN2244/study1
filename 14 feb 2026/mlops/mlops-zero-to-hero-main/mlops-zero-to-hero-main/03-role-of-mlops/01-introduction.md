# Introduction: Role of MLOps in Practice

Till now we focused on the theory — what machine learning is, what a model is, what MLOps is, the ML lifecycle, and the differences between Data Science, ML Engineering, and MLOps.

Now let's take things to the next level. Using a **hello-world project**, we'll see how MLOps engineers help data scientists and ML engineers in real time.

---

## The Business Requirement

Imagine an organization planning to build a system to **predict flower species** by taking these inputs:

| Input Feature | Description |
|--------------|-------------|
| Petal length | Length of the flower's petal |
| Petal width | Width of the flower's petal |
| Sepal length | Length of the flower's sepal |
| Sepal width | Width of the flower's sepal |

**Output:** The predicted flower species (Setosa, Versicolor, or Virginica)

This is the classic Iris classification problem — simple enough to understand, but covers all the stages of the ML lifecycle.

---

## What We'll Cover in This Section

We'll walk through 4 parts, each building on the previous one:

```
┌──────────────────────────────────────────────────────────────────┐
│           SECTION ROADMAP                                        │
│                                                                   │
│   Part 1: Data Scientists Without MLOps                          │
│   ┌──────────────────────────────────────────────────┐           │
│   │ How data scientists tackle the business           │           │
│   │ requirement — what activities do they perform?    │           │
│   └──────────────────────┬───────────────────────────┘           │
│                          │                                        │
│                          ▼                                        │
│   Part 2: How MLOps Helps Data Scientists                        │
│   ┌──────────────────────────────────────────────────┐           │
│   │ How MLOps engineers automate and improve          │           │
│   │ the data scientist's workflow                     │           │
│   └──────────────────────┬───────────────────────────┘           │
│                          │                                        │
│                          ▼                                        │
│   Part 3: ML Engineers Without MLOps                             │
│   ┌──────────────────────────────────────────────────┐           │
│   │ How ML engineers take the model to the next       │           │
│   │ level — making it production-ready                │           │
│   └──────────────────────┬───────────────────────────┘           │
│                          │                                        │
│                          ▼                                        │
│   Part 4: How MLOps Helps ML Engineers                           │
│   ┌──────────────────────────────────────────────────┐           │
│   │ How MLOps engineers automate deployment,          │           │
│   │ infrastructure, and monitoring for ML engineers   │           │
│   └──────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────┘
```

| Part | File | Focus |
|------|------|-------|
| -- | [00 — Hands-On Guide](00-hands-on-guide.md) | **Step-by-step commands** — run the entire project end-to-end |
| 1 | [02 — Data Scientists Without MLOps](02-data-scientists-without-mlops.md) | What data scientists do manually to build the model |
| 2 | [03 — How MLOps Helps Data Scientists](03-how-mlops-help-datascientists.md) | How MLOps automates training, tracking, and reproducibility |
| 3 | [04 — ML Engineers Without MLOps](04-ml-engineers-without-mlops.md) | How ML engineers wrap the model into APIs and optimize for production |
| 4 | [05 — How MLOps Helps ML Engineers](05-how-mlops-engineers-help-ml-engineers.md) | How MLOps automates deployment, containerization, and infrastructure |

---

## Project Repository

All project files and code for this section are available:

- **Local path:** [hello-world-mlops/](hello-world-mlops/) (included in this course folder)
- **GitHub:** https://github.com/iam-veeramalla/hello-world-mlops

### Project structure

```
hello-world-mlops/
├── .github/workflows/ci.yml   ← CI/CD pipeline (GitHub Actions)
├── artifacts/
│   ├── model.pkl               ← Saved trained model
│   └── metrics.json            ← Model accuracy metrics
├── train.py                    ← Training script (Data Scientist)
├── run_model.py                ← CLI to test predictions (Data Scientist)
├── app.py                      ← Flask API for model serving (ML Engineer)
├── Dockerfile                  ← Container config (MLOps Engineer)
├── requirements.txt            ← Python dependencies
└── .gitignore                  ← Excludes .venv from version control
```

---

## The Pattern You'll See

Each pair of lectures follows the same pattern:

```
┌─────────────────────────┐         ┌─────────────────────────┐
│ WITHOUT MLOps           │         │ WITH MLOps              │
│                         │         │                         │
│ • Manual steps          │  ──►    │ • Automated pipelines   │
│ • Repetitive work       │         │ • Reproducible          │
│ • Error-prone           │         │ • Scalable              │
│ • Slow iterations       │         │ • Fast iterations       │
└─────────────────────────┘         └─────────────────────────┘
```

By the end of this section, you'll understand exactly where MLOps fits in a real project and what value it adds at each stage.

---

## Terminal Screenshots Reference

Terminal screenshots from the hands-on sessions are available at `mlops/` for reference:

| Screenshot | What it shows |
|-----------|---------------|
| `1.png` | Exploring the Iris dataset in Python REPL — features, target values, target names |
| `2.png` | Setting up Python virtual environment — `python3.12 -m venv`, `source activate`, `which python` |
| `3.png` | Installing dependencies — `pip install -r requirements.txt` |
| `4.png` | Running `train.py` (accuracy: 1.0), listing artifacts, testing with `run_model.py` (predictions 0, 1, 2) |
| `5.png` | Git init, `.gitignore`, `git add`, `git status` — version control setup |
| `6.png` | Git commit, branch, remote add, push — pushing to GitHub |
| `7.png` | GitHub Actions `ci.yml` — trigger config, matrix strategy, checkout, setup-python |
| `8.png` | GitHub Actions `ci.yml` — pip upgrade, install deps, train model, upload artifacts |
| `9.png` | Close-up of CI steps: upgrade pip, install dependencies, train the model |
| `10.png` | GitHub Actions run result — artifact upload success for Python 3.11 and 3.12 |
| `11.png` | Running Flask API — `python3.12 app.py`, serving on port 5001 |
| `12.png` | Testing API with curl — 3 predictions with different inputs |
| `13.png` | Dockerfile content — Python base image, requirements, app.py |
| `14.png` | Docker build failure — missing `install` in pip upgrade command |
| `15.png` | Fixed Dockerfile — `pip install --upgrade pip` |
| `16.png` | Docker run and docker ps — container running on port 5001 |
| `17.png` | Testing containerized model with curl — prediction works |

---

## Complete End-to-End Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│           END-TO-END HELLO WORLD MLOps FLOW                       │
│                                                                   │
│              DATA SCIENTIST                                       │
│         (Builds & Trains Model)                                   │
│         train.py → model.pkl                                      │
│                    │                                              │
│                    ▼                                              │
│              MLOps (CI/CD + CT)                                   │
│         GitHub Actions pipeline                                   │
│         Automated training on push/PR                             │
│                    │                                              │
│                    ▼                                              │
│              MODEL ARTIFACT                                       │
│         artifacts/model.pkl + metrics.json                        │
│                    │                                              │
│                    ▼                                              │
│              ML ENGINEER                                          │
│         (API + Optimization)                                      │
│         app.py → Flask API on /predict                            │
│                    │                                              │
│                    ▼                                              │
│              MLOps (Docker + Infra)                               │
│         Dockerfile → docker build → docker run                    │
│                    │                                              │
│                    ▼                                              │
│              CONTAINER IMAGE                                      │
│         hello-mlops:latest                                        │
│                    │                                              │
│                    ▼                                              │
│              KUBERNETES / CLOUD                                   │
│         (Future lectures)                                         │
│                    │                                              │
│                    ▼                                              │
│              END USERS                                            │
│         Mobile apps, websites, services                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## What You Learned in This Section

| Topic | What you now understand |
|-------|------------------------|
| ML lifecycle in practice | How theory maps to real code and commands |
| Data Scientist workflow | train.py, run_model.py, manual testing |
| Continuous Training (CT) | CI/CD automates training on every code change |
| CI/CD for ML | GitHub Actions with matrix strategy for multi-version testing |
| Model artifacts | Automated upload and download via GitHub |
| API creation | Flask API wrapping the model for HTTP access |
| Dockerization | Containerizing the model API for portability |
| Role collaboration | DS builds → MLOps automates training → ML Engineer builds API → MLOps deploys |

You now have a strong foundation in MLOps fundamentals. The next sections cover versioning, experiment tracking, and production deployment.
