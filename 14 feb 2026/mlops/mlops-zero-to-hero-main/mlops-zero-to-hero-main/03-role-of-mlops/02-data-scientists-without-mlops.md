# Role of a Data Scientist (Hands-On)

Think of a Data Scientist as the person who turns raw data into insights and a working model. Their focus is data, logic, and predictions — not deployment, automation, or production systems.

In this lecture, we'll see how a data scientist tackles the flower species prediction requirement step by step, using the [hello-world-mlops](hello-world-mlops/) project.

---

## The Business Requirement

An organization wants to build a system to **predict flower species** by taking petal length, petal width, sepal length, and sepal width as inputs.

---

## Data Scientist's Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│           DATA SCIENTIST'S STEPS                                  │
│                                                                   │
│   Step 1: Data Gathering / Collection                            │
│        ↓                                                          │
│   Step 2: Set up Python Environment                              │
│        ↓                                                          │
│   Step 3: Write the Training Script                              │
│           • Load dataset                                          │
│           • Split into training/test data                        │
│           • Choose algorithm                                      │
│           • Train the algorithm                                   │
│        ↓                                                          │
│   Step 4: Save the Model                                         │
│        ↓                                                          │
│   Step 5: Test the Model with Sample Inputs                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Data Gathering

For this requirement, data scientists don't have to prepare a dataset from scratch — there's a publicly available dataset called the **Iris dataset** that exactly meets the requirements.

Sometimes data scientists must prepare datasets using internal or external data sources (databases, APIs, logs). But when the use case is popular or simple, they can find datasets on the internet.

> As MLOps engineers, you don't have to understand how data scientists prepare a dataset. But let's quickly see how the Iris dataset looks.

### Exploring the Iris Dataset (Python inline commands)

```python
>>> from sklearn.datasets import load_iris
>>> import pandas as pd
>>> iris = load_iris()
>>> df = pd.DataFrame(iris.data, columns=iris.feature_names)
>>> df["target"] = iris.target
>>> print(df.head())
```

**Output:**

```
   sepal length (cm)  sepal width (cm)  petal length (cm)  petal width (cm)  target
0                5.1               3.5                1.4               0.2       0
1                4.9               3.0                1.4               0.2       0
2                4.7               3.2                1.3               0.2       0
3                4.6               3.1                1.5               0.2       0
4                5.0               3.6                1.4               0.2       0
```

These are the **input features** (sepal/petal measurements) and the **output target** (0, 1, or 2).

### What do the target numbers mean?

```python
>>> print("\nTarget Names:", iris.target_names)
Target Names: ['setosa' 'versicolor' 'virginica']
```

- `0` = Setosa (zeroth index)
- `1` = Versicolor
- `2` = Virginica

The target is represented numerically because ML algorithms work with numbers, not strings.

---

## Step 2: Set Up Python Environment

Before writing any code, data scientists set up a Python virtual environment. This isolates project dependencies from the system Python.

> Whenever you work with Python — for ML, DevOps, or anything else — always create a virtual environment.

### Commands

```bash
# Create virtual environment (using Python 3.12)
python3.12 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Verify it's activated (should show .venv path)
which python3.12
# Output: /Users/abhi/hello-world-mlops/.venv/bin/python3.12
```

### Install dependencies

```bash
python3.12 -m pip install -r requirements.txt
```

The `requirements.txt` contains:

```
flask==2.3.2
scikit-learn==1.3.2
joblib==1.4.2
pandas==2.2.2
```

---

## Step 3: Write the Training Script

The training script (`train.py`) is the core of the data scientist's work. Let's walk through it line by line.

### The complete script: `train.py`

```python
"""
Simple training script:
- loads iris dataset from sklearn
- trains a LogisticRegression
- saves model to model.pkl
"""

from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib
import os
import json

def main():
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LogisticRegression(max_iter=200)
    model.fit(X_train, y_train)

    # Save model
    os.makedirs("artifacts", exist_ok=True)
    model_path = os.path.join("artifacts", "model.pkl")
    joblib.dump(model, model_path)

    # Save a tiny metrics file
    acc = model.score(X_test, y_test)
    metrics = {"accuracy": float(acc)}
    with open(os.path.join("artifacts", "metrics.json"), "w") as f:
        json.dump(metrics, f)

    print(f"Saved model to {model_path}")
    print(f"Test accuracy: {acc:.4f}")

if __name__ == "__main__":
    main()
```

### Line-by-line explanation

| Lines | What it does |
|-------|-------------|
| `from sklearn.datasets import load_iris` | Import the Iris dataset |
| `from sklearn.linear_model import LogisticRegression` | Import the chosen algorithm |
| `from sklearn.model_selection import train_test_split` | Import the train/test split function |
| `iris = load_iris()` | Load the dataset |
| `X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, ...)` | Split: 80% training, 20% testing. `test_size=0.2` means 20% for testing. |
| `model = LogisticRegression(max_iter=200)` | **Choose the algorithm.** Data scientist decided Logistic Regression fits this problem. Could also use Random Forest or Decision Tree. |
| `model.fit(X_train, y_train)` | **Train the algorithm** on training data. It identifies patterns and develops a mathematical function — this is the model. |
| `joblib.dump(model, model_path)` | Save the model to `artifacts/model.pkl` |
| `acc = model.score(X_test, y_test)` | Evaluate accuracy on test data |
| `json.dump(metrics, f)` | Save accuracy to `artifacts/metrics.json` for tracking |

---

## Step 4: Execute the Training Script

```bash
python3.12 train.py
```

**Output:**

```
Saved model to artifacts/model.pkl
Test accuracy: 1.0000
```

> Seeing 100% accuracy is very rare in real-world use cases. This happens because the Iris dataset is small, clean, and the problem is simple. Real-time use cases are more complicated and you might not find such accurate training data.

### Verify the saved model

```bash
ls artifacts/
# Output: metrics.json  model.pkl
```

The `artifacts/` folder now contains:
- `model.pkl` — the trained model (mathematical function)
- `metrics.json` — accuracy metrics (`{"accuracy": 1.0}`)

---

## Step 5: Test the Model

Data scientists test the model by running predictions with sample inputs. The `run_model.py` script loads the saved model and predicts based on input features.

### The script: `run_model.py`

```python
#!/usr/bin/env python3
"""
Usage:
    python run_model.py --input "[5.1, 3.5, 1.4, 0.2]"
"""

import argparse
import json
from pathlib import Path
import numpy as np
import joblib

MODEL_PATH = Path("artifacts/model.pkl")

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True,
                        help="Feature list as JSON string.")
    args = parser.parse_args()

    features = json.loads(args.input)
    X = np.array(features).reshape(1, -1)

    model = load_model()
    pred = model.predict(X)

    print(json.dumps({"prediction": pred.tolist()}))

if __name__ == "__main__":
    main()
```

### Testing with different inputs

```bash
# Test 1: Input [10, 1, 5, 10]
python3 run_model.py --input "[10, 1, 5, 10]"
# Output: {"prediction": [2]}    ← Virginica

# Test 2: Change one parameter [10, 1, 5, 2]
python3 run_model.py --input "[10, 1, 5, 2]"
# Output: {"prediction": [1]}    ← Versicolor

# Test 3: Small values [1, 1, 1, 1]
python3 run_model.py --input "[1, 1, 1, 1]"
# Output: {"prediction": [0]}    ← Setosa
```

The model predicts different species depending on the input parameters. This is how data scientists verify the model works correctly.

---

## The Problem: Manual Activities

This was a very simple example, but notice how many manual activities are involved:

```
┌──────────────────────────────────────────────────────────────────┐
│           MANUAL ACTIVITIES IN DATA SCIENTIST'S WORKFLOW          │
│                                                                   │
│   1. Script lives on the local machine only                      │
│   2. Every time the script changes, must manually:               │
│      • Set up Python virtual environment                         │
│      • Download dependencies                                     │
│      • Run train.py                                              │
│      • Check accuracy                                            │
│      • Test with run_model.py                                    │
│   3. If moving to a different computer:                          │
│      • Copy all files                                            │
│      • Set up Python again                                       │
│      • Install dependencies again                                │
│      • Run everything again                                      │
│   4. If another data scientist wants to review changes:          │
│      • They must set up the entire environment locally           │
│      • Download dependencies                                     │
│      • Run the script themselves                                 │
│      • Verify the results                                        │
│   5. No version control                                          │
│   6. No automated testing                                        │
│   7. No reproducibility guarantees                               │
│                                                                   │
│   All of this for a simple hello-world model.                    │
│   For enterprise models, these steps multiply significantly.     │
└──────────────────────────────────────────────────────────────────┘
```

### The review problem

Imagine two data scientists in a team — A and B. A makes a change to `train.py` and wants B to review it.

B has to:
1. Set up the complete environment locally
2. Set up Python and virtual environment
3. Install dependencies
4. Get the latest changes
5. Run unit tests
6. Run end-to-end tests
7. Execute `train.py`
8. Verify the changes are fine

Now imagine the model must be compatible with **3 versions of Python**. B needs to:
- Set up 3 virtual machines, each with a different Python version
- Install dependencies on each
- Set up virtual environments on each
- Run `train.py` on each
- Verify results on each

For a simple hello-world model, this is already complex. For enterprise models, the number of manual steps only increases.

**This is where MLOps engineers help.** We'll see how in the next lecture.
