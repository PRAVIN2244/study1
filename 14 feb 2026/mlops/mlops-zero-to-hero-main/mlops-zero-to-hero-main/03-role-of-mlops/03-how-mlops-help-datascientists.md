# How MLOps Engineers Help Data Scientists

In the previous lecture, we saw how data scientists train and test a model — all manually. In this lecture, we'll see how MLOps engineers automate those manual activities.

---

## What Are the Manual Activities?

Before automation, data scientists:

- Run scripts manually on their local machine
- Click "Run" in a notebook
- Train only on their laptop
- Share model files over chat or email
- Set up environments from scratch on every new machine

When another data scientist wants to review changes, they must replicate the entire setup. If the model must work on multiple Python versions, the complexity multiplies.

---

## What MLOps Engineers Introduce

MLOps engineers address these problems by introducing:

```
┌──────────────────────────────────────────────────────────────────┐
│           WHAT MLOps ENGINEERS INTRODUCE                          │
│                                                                   │
│   1. Version Control System (Git + GitHub)                       │
│      • Branching strategy (one branch per environment)           │
│      • RBAC (only right people make changes)                     │
│      • Auditing (track who changed what)                         │
│      • .gitignore (exclude .venv and other local files)          │
│                                                                   │
│   2. CI/CD Pipelines (GitHub Actions)                            │
│      • Automate testing on every push/PR                         │
│      • Run on multiple Python versions automatically             │
│      • Train model and save artifacts                            │
│      • No manual setup needed                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Introduce Version Control

### Step 1: Create a .gitignore

MLOps engineers introduce best practices like `.gitignore` to avoid pushing local files (like `.venv`) to the repository.

```bash
# .gitignore
.venv
```

### Step 2: Initialize Git and push to GitHub

```bash
# Initialize local git repository
git init

# Add all files
git add .

# Check what's staged
git status
```

**Output:**
```
On branch main

No commits yet

Changes to be committed:
  (use "git rm --cached <file>..." to unstage)
        new file:   .gitignore
        new file:   README.md
        new file:   artifacts/metrics.json
        new file:   artifacts/model.pkl
        new file:   requirements.txt
        new file:   run_model.py
        new file:   train.py
```

```bash
# Commit
git commit -m "first commit"

# Set branch name
git branch -M main

# Add remote repository
git remote add origin https://github.com/iam-veeramalla/hello-world-mlops.git

# Push to GitHub
git push -u origin main
```

Now all files are in the remote repository. Any team member can clone and work on them.

---

## Part 2: Set Up CI/CD with GitHub Actions

This is where the real automation happens. Instead of manually setting up Python, installing dependencies, and running `train.py` on every change — CI/CD does it automatically.

### Create the workflow file

```
.github/
└── workflows/
    └── ci.yml
```

You can create this file directly in GitHub's web IDE (press `.` on the repo page) or in your local IDE.

### The complete CI file: `.github/workflows/ci.yml`

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

### Line-by-line explanation

#### Trigger configuration

```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

The workflow triggers when:
- Someone **pushes** (commits) to the `main` branch
- Someone creates a **pull request** to the `main` branch

#### Job configuration

```yaml
jobs:
  matrix-pip:
    name: Train and Save the model
    runs-on: ubuntu-latest
```

- `matrix-pip` — job name (can be anything)
- `runs-on: ubuntu-latest` — uses a GitHub-provided runner (free for public repos). This runner is terminated after the workflow completes, so no virtual environment setup is needed.

#### Matrix strategy (multiple Python versions)

```yaml
    strategy:
      matrix:
        python: [3.11, 3.12]
```

This runs the **same job on both Python 3.11 and 3.12** automatically. If you need 10 Python versions tomorrow, just add them to the list — no other changes needed. That's the power of CI/CD.

#### Steps (same as manual steps, but automated)

| Step | What it does | Manual equivalent |
|------|-------------|-------------------|
| **Checkout** | Pull source code to the runner | `git clone` the repo |
| **Setup python** | Install the specified Python version | `python3.12 -m venv .venv` |
| **Upgrade pip** | Update pip and setuptools | `pip install --upgrade pip` |
| **Install dependencies** | Install from requirements.txt | `pip install -r requirements.txt` |
| **Train the model** | Run train.py and verify artifacts | `python train.py && ls artifacts/` |
| **Upload artifacts** | Save model.pkl as downloadable artifact | Manually sharing the file |

> **Why no virtual environment in CI?** The GitHub runner is a one-time-use virtual machine. It's destroyed after the workflow completes. There's no need to isolate dependencies — the entire machine is yours for this run.

#### Artifact upload

```yaml
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ml-artifacts-${{ matrix.python }}-${{ github.run_id }}
          path: artifacts
```

This saves the trained model (`model.pkl`) and metrics (`metrics.json`) as downloadable artifacts in GitHub. Anyone can go to the workflow run and download the model — no need to share files over chat or email.

The artifact name includes the Python version and run ID so you can distinguish between different runs:
- `ml-artifacts-3.11-19426387104`
- `ml-artifacts-3.12-19426387104`

---

## What This Automates

```
┌──────────────────────────────────────────────────────────────────┐
│           BEFORE (Manual)              AFTER (CI/CD)             │
│                                                                   │
│   Set up Python manually        →  Automated by setup-python     │
│   Install dependencies manually →  Automated by pip install step │
│   Run train.py manually        →  Automated on every push/PR    │
│   Test on 1 Python version     →  Test on 2+ versions (matrix)  │
│   Share model via chat/email   →  Download from GitHub artifacts │
│   No version tracking          →  Every run linked to a commit  │
│   "Works on my machine"        →  Same environment every time   │
│   Manual review process        →  Automated on pull requests    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Benefits for Data Scientists

### Training becomes automatic

Instead of a human triggering training, the CI pipeline runs automatically when:
- New code is pushed
- Data changes
- A pull request is merged

Training is now predictable, consistent, and not dependent on someone's laptop.

### Standard environment every time

Local machines differ — different Python versions, library versions, OS settings. CI ensures every training run uses the exact same environment, same dependencies, same Python version.

This eliminates: *"The model worked on my machine but not in CI."*

### Clean, fresh training every run

Each CI run starts from a clean environment — no leftover files, no cached results, no manual tweaks. Training is reproducible and results are trustworthy.

### Consistent experiment tracking

Every CI training run is linked to:
- A Git commit (which code created this model?)
- A timestamp (when was it trained?)
- A specific change (what changed between two models?)

### Early failure detection

If something breaks — dependency issues, data format problems, training errors — CI fails immediately and visibly. Data scientists catch issues early, before broken models reach production.

---

## GitHub Actions Workflow Results

When the workflow runs, you'll see two jobs (one per Python version):

```
Jobs:
  ✅ Train and Save the model (3.11)
  ✅ Train and Save the model (3.12)
```

Each job uploads artifacts:

```
Upload artifacts
  Artifact name is valid!
  Root directory input is valid!
  Beginning upload of artifact content to blob storage
  Uploaded bytes 958
  Finished uploading artifact content to blob storage!
  Artifact ml-artifacts-3.12-19426387104 successfully finalized.
  Artifact ml-artifacts-3.12-19426387104 has been successfully uploaded!
  Final size is 958 bytes. Artifact ID is 4587029119
```

Anyone can download the model from the GitHub Actions artifacts page — no manual file sharing needed.

---

## Summary: What MLOps Engineers Did

| Problem | MLOps Solution |
|---------|---------------|
| Code on local machine only | Git + GitHub for version control |
| No branching strategy | Branch per environment, RBAC, auditing |
| Local files pushed to repo | `.gitignore` excludes `.venv` |
| Manual Python setup | GitHub Actions `setup-python` |
| Manual dependency install | Automated `pip install` in CI |
| Manual training | Automated `train.py` on every push/PR |
| Test on 1 Python version | Matrix strategy: test on 3.11 + 3.12 |
| Share model via chat | Upload as GitHub artifact |
| No reproducibility | Clean environment every run |
| No tracking | Every run linked to a Git commit |
