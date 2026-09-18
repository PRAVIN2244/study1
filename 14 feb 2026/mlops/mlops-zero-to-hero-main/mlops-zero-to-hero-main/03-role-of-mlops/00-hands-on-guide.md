# Hands-On Guide: Hello World MLOps Project

This is a step-by-step implementation guide. Follow each command in order. All code is in the [hello-world-mlops/](hello-world-mlops/) folder.

**What you'll build:** A flower species prediction system — from training to containerized deployment.

**Prerequisites:** Python 3.12, Git, Docker installed on your machine.

---

## Phase 1: Data Scientist — Train the Model

### 1.1 Clone or navigate to the project

```bash
cd hello-world-mlops
```

### 1.2 Explore the Iris dataset

Open a Python REPL to see what the data looks like:

```bash
python3.12
```

```python
>>> from sklearn.datasets import load_iris
>>> import pandas as pd
>>> iris = load_iris()
>>> df = pd.DataFrame(iris.data, columns=iris.feature_names)
>>> df["target"] = iris.target
>>> print(df.head())
```

**Expected output:**

```
   sepal length (cm)  sepal width (cm)  petal length (cm)  petal width (cm)  target
0                5.1               3.5                1.4               0.2       0
1                4.9               3.0                1.4               0.2       0
2                4.7               3.2                1.3               0.2       0
3                4.6               3.1                1.5               0.2       0
4                5.0               3.6                1.4               0.2       0
```

Check what the target numbers mean:

```python
>>> print("\nTarget Names:", iris.target_names)
Target Names: ['setosa' 'versicolor' 'virginica']
>>> exit()
```

- `0` = Setosa
- `1` = Versicolor
- `2` = Virginica

### 1.3 Set up Python virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Verify activation:

```bash
which python3.12
```

**Expected output:** Something like `/path/to/hello-world-mlops/.venv/bin/python3.12`

### 1.4 Install dependencies

```bash
python3.12 -m pip install -r requirements.txt
```

### 1.5 Review the training script

Open `train.py` and understand what it does:

```
train.py
├── Loads Iris dataset
├── Splits into 80% training / 20% testing
├── Trains LogisticRegression algorithm
├── Saves model to artifacts/model.pkl
└── Saves accuracy to artifacts/metrics.json
```

### 1.6 Train the model

```bash
python3.12 train.py
```

**Expected output:**

```
Saved model to artifacts/model.pkl
Test accuracy: 1.0000
```

### 1.7 Verify saved artifacts

```bash
ls artifacts/
```

**Expected output:**

```
metrics.json  model.pkl
```

### 1.8 Test the model with sample inputs

```bash
# Prediction: 2 (Virginica)
python3 run_model.py --input "[10, 1, 5, 10]"

# Prediction: 1 (Versicolor)
python3 run_model.py --input "[10, 1, 5, 2]"

# Prediction: 0 (Setosa)
python3 run_model.py --input "[1, 1, 1, 1]"
```

**Expected output:**

```
{"prediction": [2]}
{"prediction": [1]}
{"prediction": [0]}
```

---

## Phase 2: MLOps Engineer — Automate Training with CI/CD

### 2.1 Create .gitignore

```bash
echo ".venv" > .gitignore
```

### 2.2 Initialize Git and push to GitHub

Create a new repository on GitHub first (e.g., `hello-world-mlops`), then:

```bash
git init
git add .
git status
```

**Expected output:**

```
On branch main

No commits yet

Changes to be committed:
        new file:   .gitignore
        new file:   README.md
        new file:   artifacts/metrics.json
        new file:   artifacts/model.pkl
        new file:   requirements.txt
        new file:   run_model.py
        new file:   train.py
```

```bash
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<your-username>/hello-world-mlops.git
git push -u origin main
```

### 2.3 Create the CI/CD pipeline

Create the workflow directory and file:

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/ci.yml`:

```yaml
name: CI - Train and Save the model

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  matrix-pip:
    name: Train and Save the model
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: [3.11, 3.12]

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup python
        uses: actions/setup-python@v4
        with:
           python-version: ${{ matrix.python }}

      - name: Upgrade pip
        run: python -m pip install --upgrade pip setuptools wheel

      - name: Install project dependencies
        run: python -m pip install -r requirements.txt

      - name: Train the model
        run: |
           python train.py
           ls -la artifacts

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ml-artifacts-${{ matrix.python }}-${{ github.run_id }}
          path: artifacts
```

### 2.4 Push the CI file

```bash
git add .github/workflows/ci.yml
git commit -m "add CI/CD pipeline for model training"
git push
```

### 2.5 Verify the pipeline runs

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You should see "CI - Train and Save the model" running
4. Two jobs will execute: one for Python 3.11, one for Python 3.12

**Expected result:**

```
Jobs:
  ✅ Train and Save the model (3.11)
  ✅ Train and Save the model (3.12)
```

### 2.6 Download artifacts

1. Click on a completed job
2. Expand "Upload artifacts"
3. Find the artifact download URL at the bottom
4. Download the zip — it contains `model.pkl` and `metrics.json`

---

## Phase 3: ML Engineer — Build the API

### 3.1 Review the API script

Open `app.py` and understand the structure:

```
app.py
├── Loads model from artifacts/model.pkl
├── /health endpoint (GET) — returns {"status": "ok"}
├── /predict endpoint (POST) — accepts features, returns prediction
└── Runs on host 0.0.0.0, port 5001
```

### 3.2 Start the API

```bash
python3.12 app.py
```

**Expected output:**

```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
```

### 3.3 Test the API (open a new terminal)

```bash
# Test 1: Setosa
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

**Expected output:** `{"prediction":0}`

```bash
# Test 2: Versicolor
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[10,1,5,2]}'
```

**Expected output:** `{"prediction":1}`

```bash
# Test 3: Setosa
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[1,1,1,1]}'
```

**Expected output:** `{"prediction":0}`

### 3.4 Stop the API

Press `CTRL+C` in the terminal running `app.py`.

---

## Phase 4: MLOps Engineer — Containerize and Deploy

### 4.1 Review the Dockerfile

```
Dockerfile
├── FROM python:3.12-slim          ← Python base image
├── WORKDIR /app                   ← Working directory
├── COPY requirements.txt .        ← Copy deps first (layer caching)
├── RUN pip install --upgrade pip  ← Upgrade pip
├── RUN pip install -r req.txt     ← Install dependencies
├── COPY . .                       ← Copy source code
├── EXPOSE 5001                    ← Document the port
└── CMD ["python", "app.py"]       ← Start the API
```

### 4.2 Build the Docker image

```bash
docker build -t hello-mlops:latest .
```

**Expected output (last lines):**

```
 => [6/6] COPY . .
 => exporting to image
 => => naming to docker.io/library/hello-mlops:latest
```

### 4.3 Run the container

```bash
docker run -d -p 5001:5001 hello-mlops:latest
```

### 4.4 Verify the container is running

```bash
docker ps
```

**Expected output:**

```
CONTAINER ID   IMAGE                COMMAND            STATUS       PORTS
026be724d502   hello-mlops:latest   "python app.py"    Up 4 secs    0.0.0.0:5001->5001/tcp
```

### 4.5 Test the containerized model

```bash
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
```

**Expected output:** `{"prediction":0}`

```bash
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[10,1,5,2]}'
```

**Expected output:** `{"prediction":1}`

### 4.6 Stop and clean up

```bash
# Find the container ID
docker ps

# Stop the container
docker stop <container-id>

# Remove the container
docker rm <container-id>
```

---

## Quick Reference: All Commands in Order

```bash
# ─── PHASE 1: DATA SCIENTIST ───
cd hello-world-mlops
python3.12 -m venv .venv
source .venv/bin/activate
python3.12 -m pip install -r requirements.txt
python3.12 train.py
ls artifacts/
python3 run_model.py --input "[10, 1, 5, 10]"
python3 run_model.py --input "[10, 1, 5, 2]"
python3 run_model.py --input "[1, 1, 1, 1]"

# ─── PHASE 2: MLOps (CI/CD) ───
echo ".venv" > .gitignore
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/<your-username>/hello-world-mlops.git
git push -u origin main
mkdir -p .github/workflows
# Create .github/workflows/ci.yml (see section 2.3)
git add .github/workflows/ci.yml
git commit -m "add CI/CD pipeline for model training"
git push

# ─── PHASE 3: ML ENGINEER (API) ───
python3.12 app.py
# In another terminal:
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'

# ─── PHASE 4: MLOps (DOCKER) ───
docker build -t hello-mlops:latest .
docker run -d -p 5001:5001 hello-mlops:latest
docker ps
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[1,1,1,1]}'
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python3.12: command not found` | Install Python 3.12 or use `python3` instead |
| `pip install` fails with permission error | Make sure virtual environment is activated (`source .venv/bin/activate`) |
| `train.py` fails with import error | Run `pip install -r requirements.txt` first |
| Docker build fails with `no such option: --upgrade` | Use `python -m pip install --upgrade pip` (don't forget `install`) |
| `curl: connection refused` on port 5001 | Make sure `app.py` or the Docker container is running |
| GitHub Actions fails with "file not found" | Check file names in `ci.yml` match actual files (e.g., `train.py` not `trained.python`) |
| Docker container exits immediately | Run `docker logs <container-id>` to see the error |

---

## Terminal Screenshots

Reference screenshots from the hands-on sessions are available at `mlops/`:

| Phase | Screenshots | What they show |
|-------|------------|----------------|
| **Phase 1** | `1.png` — `4.png` | Iris dataset exploration, venv setup, pip install, train.py execution, run_model.py testing |
| **Phase 2** | `5.png` — `10.png` | Git init/push, ci.yml creation, GitHub Actions running, artifact upload |
| **Phase 3** | `11.png` — `12.png` | Flask API running, curl testing with predictions |
| **Phase 4** | `13.png` — `17.png` | Dockerfile, docker build (with error fix), docker run, container testing |
