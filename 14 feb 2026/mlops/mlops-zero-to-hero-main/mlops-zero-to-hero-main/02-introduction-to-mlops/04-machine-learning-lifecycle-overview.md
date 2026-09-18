# Machine Learning Lifecycle

The Machine Learning lifecycle is the complete journey of building, deploying, and maintaining an ML model. It covers everything from collecting raw data to monitoring the model in production.

This is **not a one-time activity**. These stages are performed in a loop — just like the software development lifecycle. When model performance drops, you go back to earlier stages, fix the issue, retrain, and redeploy.

> To become an MLOps engineer, you should understand all the stages involved and know how to automate the operations in each stage.

### Why this matters for MLOps

MLOps automates the manual activities across these stages, making the ML lifecycle:

- **Faster** — automated pipelines instead of manual steps
- **Reliable** — consistent, repeatable processes
- **Scalable** — handle multiple models and large datasets
- **Reproducible** — every experiment and model version is tracked

---

## The Lifecycle at a Glance

```
┌──────────────────────────────────────────────────────────────────────┐
│                   MACHINE LEARNING LIFECYCLE                         │
│                                                                      │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│    │ 1. Problem   │───►│ 2. Data      │───►│ 3. Data      │         │
│    │ Definition   │    │ Collection   │    │ Cleaning     │         │
│    └──────────────┘    └──────────────┘    └──────┬───────┘         │
│                                                   │                  │
│                                                   ▼                  │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│    │ 6. Model     │◄───│ 5. Model     │◄───│ 4. Feature   │         │
│    │ Training     │    │ Selection    │    │ Engineering  │         │
│    └──────┬───────┘    └──────────────┘    └──────────────┘         │
│           │                                                          │
│           ▼                                                          │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│    │ 7. Model     │───►│ 8. Hyper-    │───►│ 9. Model     │         │
│    │ Evaluation   │    │ parameter    │    │ Deployment   │         │
│    │              │    │ Tuning       │    │              │         │
│    └──────┬───────┘    └──────────────┘    └──────┬───────┘         │
│           │                                       │                  │
│           │  If accuracy is low,                  ▼                  │
│           │  go back to step 4, 5, or 6    ┌──────────────┐         │
│           └───────────────────────────────►│ 10. Monitor  │         │
│                                            │ & Maintain   │─────┐   │
│                                            └──────────────┘     │   │
│                                                                 │   │
│              If performance drops, loop back ◄──────────────────┘   │
│              to Feature Engineering / Model Selection / Retraining  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Problem Definition

This is the same as in traditional software development — the first step is always understanding the problem in detail.

- What are you trying to predict or classify?
- What does success look like? (accuracy, latency, cost)
- Is this a classification, regression, or clustering problem?

**Examples:**

| Problem | Type | Success Metric |
|---------|------|---------------|
| Predict flower species | Classification | 95%+ accuracy |
| Predict house price | Regression | Low error (RMSE) |
| Detect fraudulent transactions | Classification | High precision (minimize false positives) |
| Recommend movies to users | Recommendation | User engagement rate |

---

## Stage 2: Data Collection

To train models, you need data. Data scientists gather data from various sources.

| Source | Example |
|--------|---------|
| Publicly available datasets | Iris dataset, MNIST, ImageNet |
| Databases | Company's internal PostgreSQL, MongoDB |
| APIs | Twitter API, weather API, stock market API |
| Logs | Application logs, server logs, user activity logs |
| Sensors | IoT devices, cameras, GPS |

If the problem has a publicly available dataset (like Iris for flower prediction), data scientists use that. If not, they must gather and create the dataset themselves.

### Code: Load data from different sources

```python
# From a public dataset (scikit-learn)
from sklearn.datasets import load_iris
iris = load_iris()
print(f"Loaded {len(iris.data)} samples from built-in dataset")

# From a CSV file
import pandas as pd
df = pd.read_csv('flower_data.csv')
print(f"Loaded {len(df)} rows from CSV")

# From a database
import sqlite3
conn = sqlite3.connect('flowers.db')
df = pd.read_sql('SELECT * FROM measurements', conn)
print(f"Loaded {len(df)} rows from database")
```

---

## Stage 3: Data Cleaning & Preparation

The gathered data often has problems. Data from logs and databases can contain:

- **Duplicates** — same entry recorded multiple times
- **Missing values** — some fields are empty
- **Wrong data** — incorrect entries, typos, outliers
- **Noise** — irrelevant or misleading data points

Cleaning ensures the model trains on accurate data and returns accurate results.

> **Golden Rule: Garbage In → Garbage Out.** If you feed bad data to the model, you get bad predictions — no matter how good the algorithm is.

### Code: Clean the data

```python
import pandas as pd

# Load raw data
df = pd.read_csv('raw_flower_data.csv')
print(f"Before cleaning: {len(df)} rows")

# Check for problems
print(f"Duplicates: {df.duplicated().sum()}")
print(f"Missing values:\n{df.isnull().sum()}")

# Remove duplicates
df = df.drop_duplicates()

# Remove rows with missing values
df = df.dropna()

# Remove outliers (e.g., petal_length > 10 is clearly wrong)
df = df[df['petal_length'] <= 10]

print(f"After cleaning: {len(df)} rows")
```

```
┌──────────────────────────────────────────────────┐
│              DATA CLEANING                        │
│                                                   │
│   Raw Data (messy)                                │
│   ┌──────────────────────────────────────┐       │
│   │ [5.1, 3.5, 1.4, 0.2, "setosa"]      │       │
│   │ [5.1, 3.5, 1.4, 0.2, "setosa"]  ◄── duplicate│
│   │ [NULL, 3.0, 1.4, 0.2, "setosa"] ◄── missing │
│   │ [99.0, 3.2, 1.3, 0.2, "setosa"] ◄── outlier │
│   │ [4.6, 3.1, 1.5, 0.2, "setosa"]      │       │
│   └──────────────────────────────────────┘       │
│                     │                             │
│                     ▼ Clean                       │
│   ┌──────────────────────────────────────┐       │
│   │ [5.1, 3.5, 1.4, 0.2, "setosa"]      │       │
│   │ [4.6, 3.1, 1.5, 0.2, "setosa"]      │       │
│   └──────────────────────────────────────┘       │
│                                                   │
│   Removed: 1 duplicate, 1 missing, 1 outlier    │
└──────────────────────────────────────────────────┘
```

---

## Stage 4: Feature Engineering

Feature engineering means **adding new features to the existing dataset** so the model can learn better patterns.

This is very important — the data you get from public sources or databases might not be enough on its own. With feature engineering, data takes a new shape.

### Example: Iris Dataset

The Iris dataset has 4 features:

| Feature | Description |
|---------|-------------|
| petal_length | Length of the petal |
| petal_width | Width of the petal |
| sepal_length | Length of the sepal |
| sepal_width | Width of the sepal |

Data scientists might add new features to help the model:

| New Feature | Formula | Why it might help |
|-------------|---------|-------------------|
| petal_ratio | petal_length / sepal_length | The ratio between petal and sepal might distinguish species better |
| total_area | (petal_length × petal_width) + (sepal_length × sepal_width) | Total flower area could be a strong predictor |
| petal_area | petal_length × petal_width | Petal area alone might separate species |

### Code: Add new features

```python
from sklearn.datasets import load_iris
import pandas as pd

iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target

print("Original features:")
print(df.head())
print(f"Columns: {len(df.columns)}")

# Feature Engineering — add new features
df['petal_ratio'] = df['petal length (cm)'] / df['sepal length (cm)']
df['total_area'] = (df['petal length (cm)'] * df['petal width (cm)']) + \
                   (df['sepal length (cm)'] * df['sepal width (cm)'])
df['petal_area'] = df['petal length (cm)'] * df['petal width (cm)']

print("\nAfter feature engineering:")
print(df.head())
print(f"Columns: {len(df.columns)}")
```

**Output:**
```
Original features:
   sepal length (cm)  sepal width (cm)  petal length (cm)  petal width (cm)  species
0                5.1               3.5                1.4               0.2        0
1                4.9               3.0                1.4               0.2        0
...
Columns: 5

After feature engineering:
   sepal length (cm)  ...  petal_ratio  total_area  petal_area  species
0                5.1  ...     0.274510       18.13        0.28        0
1                4.9  ...     0.285714       14.98        0.28        0
...
Columns: 8
```

The dataset went from 5 columns to 8 columns. These new features can help the model find patterns it couldn't see before.

---

## Stage 5: Model Selection (Algorithm Selection)

> **Note:** In machine learning, "model" and "algorithm" are often used interchangeably. When someone says "model selection," they usually mean choosing an algorithm. Don't get confused — you're not selecting a pre-built model, you're selecting the algorithm that will learn from your data.

Popular algorithms:

| Algorithm | Best for | Example use case |
|-----------|----------|-----------------|
| **Linear Regression** | Predicting numbers | House prices, stock prices |
| **Logistic Regression** | Binary/multi-class classification | Spam detection, flower species |
| **Decision Tree** | Classification with clear boundaries | Loan approval, flower species |
| **Random Forest** | When one tree isn't enough | Fraud detection, medical diagnosis |
| **Neural Networks** | Complex patterns (images, text, audio) | Image recognition, language translation |
| **Gradient Boosting** | Tabular data with high accuracy needs | Competition-winning models |

It is the **data scientist's responsibility** to pick the right algorithm based on the problem and data.

### Code: Try different algorithms

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

# Try multiple algorithms and compare
algorithms = {
    'Logistic Regression': LogisticRegression(max_iter=200),
    'Decision Tree': DecisionTreeClassifier(random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
}

print("Algorithm Comparison:")
print("-" * 40)
for name, algo in algorithms.items():
    algo.fit(X_train, y_train)
    predictions = algo.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"  {name:25s} → {accuracy * 100:.1f}%")
```

**Output:**
```
Algorithm Comparison:
----------------------------------------
  Logistic Regression       → 100.0%
  Decision Tree             → 96.7%
  Random Forest             → 100.0%
```

---

## Stage 6: Model Training

The most important stage. The algorithm is trained with the dataset (typically 80% of the data).

During training:
1. The algorithm receives input features and their correct output labels
2. It starts identifying patterns in the data
3. It develops a mathematical function — this function **is** the model

```
┌──────────────────────────────────────────────────────┐
│                  MODEL TRAINING                       │
│                                                       │
│   80% of Dataset                                      │
│   ┌────────────────────────────────────────┐          │
│   │ [5.1, 3.5, 1.4, 0.2] → Setosa        │          │
│   │ [7.0, 3.2, 4.7, 1.4] → Versicolor    │          │
│   │ [6.3, 3.3, 6.0, 2.5] → Virginica     │          │
│   │ ... (120 samples)                      │          │
│   └────────────────┬───────────────────────┘          │
│                    │                                   │
│                    ▼                                   │
│            Algorithm learns patterns                   │
│                    │                                   │
│                    ▼                                   │
│            OUTPUT: Trained Model                       │
│            (mathematical function)                     │
└──────────────────────────────────────────────────────┘
```

### Code: Train a model

```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

print(f"Model trained on {len(X_train)} samples")
print(f"Model type: {model.__class__.__name__}")
```

---

## Stage 7: Model Evaluation

Test the model using the remaining 20% of data that it has never seen. The test data has known answers, so you can compare predictions against reality.

Key question: **How accurate is your model?**
- Is it 90%? Might need improvement.
- Is it 95%? Good for most use cases.
- Is it 99%? Excellent.

If the model does not return accurate results, there will be **retraining** — go back to stage 4 (feature engineering), stage 5 (try a different algorithm), or stage 6 (retrain with more/better data).

### Common evaluation metrics

| Problem Type | Metrics |
|-------------|---------|
| **Classification** (predict a category) | Accuracy, Precision, Recall, F1 Score |
| **Regression** (predict a number) | MAE (Mean Absolute Error), MSE (Mean Squared Error), RMSE (Root MSE), R² |

### Code: Evaluate the model

```python
from sklearn.metrics import accuracy_score, classification_report

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Model Accuracy: {accuracy * 100:.1f}%")
print()
print("Detailed Report:")
print(classification_report(y_test, predictions, target_names=iris.target_names))
```

**Output:**
```
Model Accuracy: 96.7%

Detailed Report:
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       1.00      0.89      0.94         9
   virginica       0.92      1.00      0.96        11

    accuracy                           0.97        30
```

### What to do if accuracy is low

```
┌──────────────────────────────────────────────────────────┐
│           EVALUATION → DECISION FLOW                      │
│                                                           │
│   Model Accuracy                                          │
│        │                                                  │
│        ├── 95%+ ──► Proceed to Hyperparameter Tuning      │
│        │            and Deployment                        │
│        │                                                  │
│        ├── 80-95% ─► Try:                                 │
│        │             • Better feature engineering         │
│        │             • Different algorithm                │
│        │             • More training data                 │
│        │                                                  │
│        └── <80% ──► Likely need to:                       │
│                     • Rethink the problem definition      │
│                     • Collect better/more data            │
│                     • Completely change approach          │
└──────────────────────────────────────────────────────────┘
```

---

## Stage 8: Hyperparameter Tuning

Hyperparameters are settings you configure **before** training — they control how the algorithm learns.

Examples:
- **Decision Tree:** max depth, min samples per leaf
- **Random Forest:** number of trees, max features
- **Neural Network:** learning rate, number of layers, batch size

This stage fine-tunes these settings to squeeze out better performance. We will cover this in more depth later in the course.

### Code: Basic hyperparameter tuning

```python
from sklearn.model_selection import GridSearchCV
from sklearn.tree import DecisionTreeClassifier

# Define hyperparameters to try
param_grid = {
    'max_depth': [3, 5, 10, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
}

# Search for the best combination
grid_search = GridSearchCV(
    DecisionTreeClassifier(random_state=42),
    param_grid,
    cv=5,  # 5-fold cross-validation
    scoring='accuracy'
)
grid_search.fit(X_train, y_train)

print(f"Best hyperparameters: {grid_search.best_params_}")
print(f"Best accuracy: {grid_search.best_score_ * 100:.1f}%")
```

---

## Stage 9: Model Deployment

Until now, all stages happen on local environments (laptops, notebooks). But the model needs to reach end users.

Models are packaged into software applications and deployed so users can access them through:

| Deployment Method | Example |
|-------------------|---------|
| **REST API** | Flask/FastAPI serving predictions over HTTP |
| **Mobile application** | Netflix app recommending movies on your phone |
| **Website** | Netflix website showing personalized suggestions |
| **Batch jobs** | Processing millions of transactions overnight for fraud scoring |
| **Cloud ML services** | AWS SageMaker, Google Vertex AI |

### Real-life examples

| Company | Model | How users access it |
|---------|-------|-------------------|
| **Netflix** | Recommendation engine | Through their mobile app and website |
| **PayPal** | Fraud detection | Runs behind every transaction automatically |
| **Google** | Search ranking | Every time you search on google.com |
| **Spotify** | Music recommendations | Through their app's "Discover Weekly" |

### Code: Deploy as a simple API

```python
# app.py
from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('flower_model.pkl')
species = ['setosa', 'versicolor', 'virginica']

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = np.array([[
        data['sepal_length'], data['sepal_width'],
        data['petal_length'], data['petal_width']
    ]])
    prediction = model.predict(features)
    return jsonify({'species': species[prediction[0]]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

```bash
# Run the API
pip install flask
python app.py

# Test it
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

---

## Stage 10: Monitoring & Maintenance

Once deployed, the model must be monitored continuously. Model accuracy can drop over time as:

- **New data patterns emerge** — user behavior changes, new trends appear
- **Data distribution shifts** — the real-world data looks different from training data
- **New users** — different demographics, different usage patterns

This is called **model drift** — the model's predictions become less accurate over time.

When performance drops, you loop back to earlier stages:

```
┌──────────────────────────────────────────────────────────┐
│           MONITORING → RETRAINING LOOP                    │
│                                                           │
│   Model in Production                                     │
│        │                                                  │
│        ▼                                                  │
│   Monitor: accuracy, latency, prediction distribution     │
│        │                                                  │
│        ├── Performance OK ──► Continue monitoring          │
│        │                                                  │
│        └── Performance drops ──► Loop back to:            │
│                                                           │
│            ┌─────────────────────────────────────┐        │
│            │ • Stage 4: Feature Engineering      │        │
│            │   (add/modify features)             │        │
│            │ • Stage 5: Model Selection          │        │
│            │   (try a new algorithm)             │        │
│            │ • Stage 6: Retrain                  │        │
│            │   (train on newer data)             │        │
│            │ • Stage 7: Evaluate                 │        │
│            │   (verify improvement)              │        │
│            │ • Stage 9: Redeploy                 │        │
│            │   (ship new model version)          │        │
│            └─────────────────────────────────────┘        │
│                                                           │
│   This is why it's called a LIFECYCLE — not a one-time    │
│   activity. The stages repeat in a loop.                  │
└──────────────────────────────────────────────────────────┘
```

---

## Comparison: ML Lifecycle vs Software Development Lifecycle

The ML lifecycle is very similar to the SDLC. Both are loops, not one-time activities.

| SDLC | ML Lifecycle |
|------|-------------|
| Define requirements | Define the problem |
| Write code | Collect and prepare data |
| Build application | Train the model |
| Test application | Evaluate the model |
| Deploy application | Deploy the model |
| Monitor application | Monitor model performance |
| Fix bugs, add features → redeploy | Retrain with new data → redeploy |

```
┌────────────────────────────┐    ┌────────────────────────────┐
│    SOFTWARE LIFECYCLE       │    │    ML LIFECYCLE             │
│                             │    │                             │
│  Requirements               │    │  Problem Definition         │
│       ↓                     │    │       ↓                     │
│  Development                │    │  Data Collection + Cleaning │
│       ↓                     │    │       ↓                     │
│  Build                      │    │  Feature Engineering        │
│       ↓                     │    │       ↓                     │
│  Test                       │    │  Train + Evaluate           │
│       ↓                     │    │       ↓                     │
│  Deploy                     │    │  Deploy                     │
│       ↓                     │    │       ↓                     │
│  Monitor                    │    │  Monitor                    │
│       ↓                     │    │       ↓                     │
│  Bug found? → Loop back     │    │  Drift detected? → Loop back│
│                             │    │                             │
└────────────────────────────┘    └────────────────────────────┘
```

---

## The MLOps Engineer's Role in Each Stage

As an MLOps engineer, your job is to **automate the operations** in each stage:

| Stage | What MLOps automates |
|-------|---------------------|
| Data Collection | Automated data pipelines (Airflow, Kafka) |
| Data Cleaning | Data validation checks (Great Expectations) |
| Feature Engineering | Feature stores (Feast), automated feature pipelines |
| Model Selection | Experiment tracking (MLflow) to compare algorithms |
| Model Training | Training pipelines (Kubeflow, SageMaker) |
| Model Evaluation | Automated accuracy checks, threshold gates |
| Hyperparameter Tuning | Automated search (Optuna, Ray Tune) |
| Model Deployment | CI/CD pipelines, containerization, KServe |
| Monitoring | Drift detection (Evidently), alerting (Prometheus) |
| Maintenance | Automated retraining triggers |

---

## Quick Revision: All 10 Stages

| # | Stage | One-line summary |
|---|-------|-----------------|
| 1 | Problem Definition | Understand what you're solving |
| 2 | Data Collection | Gather data from public datasets, databases, APIs, logs |
| 3 | Data Cleaning | Remove duplicates, noise, missing values, wrong entries |
| 4 | Feature Engineering | Add new features like petal_ratio, total_area to improve model |
| 5 | Model Selection | Pick an algorithm (Decision Tree, Random Forest, etc.) |
| 6 | Model Training | Train the algorithm on 80% of data — it learns patterns |
| 7 | Model Evaluation | Test on 20% of data — is it 90%? 95%? 99%? |
| 8 | Hyperparameter Tuning | Fine-tune algorithm settings for better performance |
| 9 | Model Deployment | Package into API/app and deploy for end users |
| 10 | Monitoring & Maintenance | Watch for accuracy drops, retrain when needed |

---

## Complete Working Example: Mini Lifecycle

```python
"""
Mini ML Lifecycle — all stages in one script.
"""
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import pandas as pd
import joblib

# Stage 1: Problem Definition
print("Stage 1: Predict flower species from measurements")

# Stage 2: Data Collection
print("\nStage 2: Loading Iris dataset...")
iris = load_iris()
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = iris.target
print(f"  Collected {len(df)} samples")

# Stage 3: Data Cleaning
print("\nStage 3: Checking data quality...")
print(f"  Duplicates: {df.duplicated().sum()}")
print(f"  Missing values: {df.isnull().sum().sum()}")
df = df.drop_duplicates().dropna()
print(f"  Clean samples: {len(df)}")

# Stage 4: Feature Engineering
print("\nStage 4: Adding new features...")
df['petal_ratio'] = df['petal length (cm)'] / df['sepal length (cm)']
df['petal_area'] = df['petal length (cm)'] * df['petal width (cm)']
print(f"  Features: {len(df.columns)} (added petal_ratio, petal_area)")

# Stage 5: Model Selection
print("\nStage 5: Selecting Decision Tree algorithm")
algo = DecisionTreeClassifier(random_state=42)

# Prepare data with new features
feature_cols = iris.feature_names + ['petal_ratio', 'petal_area']
X = df[feature_cols].values
y = df['species'].values
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Stage 6: Model Training
print("\nStage 6: Training model on 80% of data...")
algo.fit(X_train, y_train)
print(f"  Trained on {len(X_train)} samples")

# Stage 7: Model Evaluation
print("\nStage 7: Evaluating model on 20% of data...")
predictions = algo.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"  Accuracy: {accuracy * 100:.1f}%")

# Stage 8: Hyperparameter Tuning
print("\nStage 8: Tuning hyperparameters...")
grid = GridSearchCV(
    DecisionTreeClassifier(random_state=42),
    {'max_depth': [3, 5, 10, None], 'min_samples_split': [2, 5]},
    cv=5, scoring='accuracy'
)
grid.fit(X_train, y_train)
print(f"  Best params: {grid.best_params_}")
print(f"  Best accuracy: {grid.best_score_ * 100:.1f}%")

# Stage 9: Model Deployment (save for API)
print("\nStage 9: Saving model for deployment...")
joblib.dump(grid.best_estimator_, 'flower_model.pkl')
print("  Saved as flower_model.pkl")

# Stage 10: Monitoring (simulate)
print("\nStage 10: Monitoring (simulated)...")
loaded = joblib.load('flower_model.pkl')
test_accuracy = accuracy_score(y_test, loaded.predict(X_test))
print(f"  Production accuracy: {test_accuracy * 100:.1f}%")
if test_accuracy >= 0.95:
    print("  Status: Model performing well")
else:
    print("  Status: Consider retraining")

print("\nAll 10 stages complete!")
```

```bash
python ml_lifecycle.py
```
