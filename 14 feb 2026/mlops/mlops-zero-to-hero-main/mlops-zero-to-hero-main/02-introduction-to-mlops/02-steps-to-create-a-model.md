# How Data Scientists Create a Model

Now that you know what machine learning is and what a model is, the next step is understanding how data scientists actually build one.

There are **8 steps** typically involved in creating a model. We will walk through each one with explanations, code, and diagrams.

---

## The 8 Steps at a Glance

```
┌────────────────────────────────────────────────────────────────────┐
│                  MODEL CREATION PIPELINE                           │
│                                                                    │
│  Step 1          Step 2          Step 3          Step 4            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ Collect  │───►│  Split   │───►│  Choose  │───►│  Train   │     │
│  │ Dataset  │    │  Data    │    │Algorithm │    │  Model   │     │
│  │          │    │ (80/20)  │    │          │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│                                                       │            │
│                                                       ▼            │
│  Step 8          Step 7          Step 6          Step 5            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ Build    │◄───│ Package  │◄───│ Retrain  │◄───│  Test    │     │
│  │ API /    │    │  Model   │    │(if needed)│    │  Model   │     │
│  │ Deploy   │    │ (.pkl)   │    │          │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

```bash
pip install scikit-learn pandas numpy joblib
```

---

## Step 1: Start with a Dataset

Every model begins with data. A dataset contains **input features** and the **actual output** (label).

### What does a dataset look like?

| Petal Length | Petal Width | Sepal Length | Sepal Width | Flower (Output) |
|-------------|-------------|-------------|-------------|-----------------|
| 4.0 | 3.0 | 5.0 | 6.0 | Rose |
| 5.0 | 4.0 | 2.0 | 3.0 | Jasmine |
| 1.4 | 0.2 | 5.1 | 3.5 | Setosa |
| 4.7 | 1.4 | 7.0 | 3.2 | Versicolor |
| 5.9 | 2.1 | 6.3 | 3.3 | Virginica |

Each row is one data entry. The first four columns are **features** (inputs). The last column is the **label** (output the model should learn to predict).

Datasets with hundreds or thousands of such entries are freely available online (Kaggle, UCI ML Repository, scikit-learn built-in datasets).

### Code: Load a real dataset

```python
from sklearn.datasets import load_iris
import pandas as pd

# Load the Iris dataset (150 flower samples, 3 species)
iris = load_iris()

# View as a table
df = pd.DataFrame(iris.data, columns=iris.feature_names)
df['species'] = [iris.target_names[t] for t in iris.target]

print(df.head(10))
print(f"\nTotal entries: {len(df)}")
print(f"Features: {iris.feature_names}")
print(f"Species: {list(iris.target_names)}")
```

**Output:**
```
   sepal length (cm)  sepal width (cm)  petal length (cm)  petal width (cm)    species
0                5.1               3.5                1.4               0.2     setosa
1                4.9               3.0                1.4               0.2     setosa
2                4.7               3.2                1.3               0.2     setosa
3                4.6               3.1                1.5               0.2     setosa
4                5.0               3.6                1.4               0.2     setosa
...

Total entries: 150
Features: ['sepal length (cm)', 'sepal width (cm)', 'petal length (cm)', 'petal width (cm)']
Species: ['setosa', 'versicolor', 'virginica']
```

---

## Step 2: Split the Data (80/20 Ratio)

Data scientists split the dataset into two parts:

| Split | Percentage | Purpose |
|-------|-----------|---------|
| **Training data** | ~80% | The algorithm learns patterns from this portion |
| **Testing data** | ~20% | Used later to verify if the model actually learned correctly |

**Why split?** The testing data contains the actual output values. After training, you feed the test inputs to the model and compare its predictions against the known answers. If you test on the same data you trained on, you're just checking if the model memorized — not if it actually learned.

```
┌─────────────────────────────────────────────────┐
│                 FULL DATASET                     │
│              (150 entries)                       │
│                                                  │
│  ┌──────────────────────────┐  ┌──────────────┐  │
│  │    TRAINING DATA         │  │  TEST DATA   │  │
│  │    80% (120 entries)     │  │  20% (30)    │  │
│  │                          │  │              │  │
│  │  Model learns from this  │  │  Model is    │  │
│  │                          │  │  tested on   │  │
│  │                          │  │  this        │  │
│  └──────────────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
```

### Code: Split the data

```python
from sklearn.model_selection import train_test_split

X = iris.data    # Input features (measurements)
y = iris.target  # Output labels (species)

# Split: 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples: {len(X_train)}")  # 120
print(f"Testing samples:  {len(X_test)}")   # 30
```

---

## Step 3: Choose an Algorithm

This is a key decision. There are many algorithms, and the choice depends on the problem type.

### Popular algorithms for classification:

| Algorithm | When to use | Pros |
|-----------|------------|------|
| **Logistic Regression** | Binary or multi-class classification | Simple, fast, interpretable |
| **Decision Tree** | Classification with clear decision boundaries | Easy to visualize and understand |
| **k-Nearest Neighbors (KNN)** | When similar inputs should have similar outputs | No training phase, intuitive |
| **Random Forest** | When a single decision tree isn't accurate enough | Combines multiple trees for better accuracy |

For the flower prediction problem, **Decision Tree** or **Logistic Regression** work well.

> **Note for MLOps engineers:** Choosing the algorithm is the data scientist's responsibility. As an MLOps engineer, you don't need to decide which algorithm is best — that call is taken by the data scientists. Your job starts after the model is created.

### Code: Choose an algorithm

```python
from sklearn.tree import DecisionTreeClassifier

# Create the algorithm (not trained yet)
algorithm = DecisionTreeClassifier(random_state=42)
print(f"Algorithm chosen: {algorithm.__class__.__name__}")
```

---

## Step 4: Train the Model

Training means feeding the 80% training data to the algorithm. During training, the algorithm:

1. Looks at input features and their corresponding output labels
2. Identifies patterns — e.g., "if sepal length and sepal width are small, it's likely Setosa"
3. Builds a mathematical function that maps inputs to outputs

You don't manually code these patterns. The algorithm discovers them automatically.

```
┌──────────────────────────────────────────────────────┐
│                  TRAINING PROCESS                     │
│                                                       │
│   Training Data                                       │
│   [5.1, 3.5, 1.4, 0.2] → Setosa                     │
│   [7.0, 3.2, 4.7, 1.4] → Versicolor                 │
│   [6.3, 3.3, 6.0, 2.5] → Virginica                  │
│   ... (120 entries)                                   │
│              │                                        │
│              ▼                                        │
│   Algorithm analyzes patterns:                        │
│   • "Small petal length + small petal width → Setosa" │
│   • "Medium petal length → Versicolor"                │
│   • "Large petal length + large petal width → Virginica│
│              │                                        │
│              ▼                                        │
│   Output: TRAINED MODEL (mathematical function)       │
└──────────────────────────────────────────────────────┘
```

### Code: Train the model

```python
# Train the algorithm on 80% of the data
algorithm.fit(X_train, y_train)

print("Model trained successfully!")
print(f"The model learned from {len(X_train)} samples")
```

At this point, `algorithm` has become a trained **model** — a mathematical function capable of making predictions.

---

## Step 5: Test the Model

Testing is where you verify if the model actually learned useful patterns. You use the 20% test data that the model has never seen before.

The test data has known answers, so you can compare:
- What the model **predicted**
- What the **actual** answer is

### Code: Test the model

```python
from sklearn.metrics import accuracy_score, classification_report

# Predict on test data
predictions = algorithm.predict(X_test)

# Compare predictions vs actual values
accuracy = accuracy_score(y_test, predictions)
print(f"Model accuracy: {accuracy * 100:.1f}%")

# Detailed breakdown per species
print("\nDetailed Report:")
print(classification_report(y_test, predictions, target_names=iris.target_names))
```

**Output:**
```
Model accuracy: 96.7%

Detailed Report:
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       1.00      0.89      0.94         9
   virginica       0.92      1.00      0.96        11

    accuracy                           0.97        30
```

### Visualize: What went right and wrong

```python
# Show individual predictions vs actual
for i in range(len(y_test)):
    actual = iris.target_names[y_test[i]]
    predicted = iris.target_names[predictions[i]]
    status = "✓" if actual == predicted else "✗ WRONG"
    if actual != predicted:
        print(f"  Sample {i}: Actual={actual}, Predicted={predicted}  {status}")

print(f"\nCorrect: {sum(predictions == y_test)}/{len(y_test)}")
```

---

## Step 6: Retrain if Needed (Improve the Model)

If the model returns wrong results or low accuracy, the data scientist must go back and fix things.

```
┌──────────────────────────────────────────────────────────┐
│              PROBLEM → SOLUTION FLOW                      │
│                                                           │
│   Model accuracy is low (e.g., 60%)                       │
│              │                                            │
│              ▼                                            │
│   ┌─── What could be wrong? ───┐                          │
│   │                            │                          │
│   ▼                            ▼                          │
│   Dataset Problem          Algorithm Problem              │
│   • Too little data        • Wrong algorithm chosen       │
│   • Noisy/incorrect data   • Needs hyperparameter tuning  │
│   • Missing features       • Too simple for the problem   │
│   │                            │                          │
│   ▼                            ▼                          │
│   Fix: Clean data,         Fix: Try different algorithm   │
│   add more samples,        or tune hyperparameters        │
│   remove outliers                                         │
│   │                            │                          │
│   └────────────┬───────────────┘                          │
│                ▼                                          │
│         RETRAIN THE MODEL                                 │
│                │                                          │
│                ▼                                          │
│         Test again → Accuracy improved?                   │
│         Yes → Proceed to Step 7                           │
│         No  → Repeat this step                            │
└──────────────────────────────────────────────────────────┘
```

### Common improvement strategies:

| Strategy | When to use | Example |
|----------|------------|---------|
| **Clean the data** | Dataset has errors or missing values | Remove rows with null values |
| **Add more data** | Model hasn't seen enough examples | Collect 1000 more samples |
| **Try a different algorithm** | Current algorithm doesn't fit the problem | Switch from Decision Tree to Random Forest |
| **Tune hyperparameters** | Algorithm needs fine-tuning | Adjust tree depth, learning rate |
| **Feature engineering** | Existing features aren't informative enough | Add petal area = length × width |

### Code: Try a different algorithm if accuracy is low

```python
from sklearn.ensemble import RandomForestClassifier

# Try Random Forest instead of Decision Tree
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

rf_predictions = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_predictions)

print(f"Decision Tree accuracy: {accuracy * 100:.1f}%")
print(f"Random Forest accuracy: {rf_accuracy * 100:.1f}%")
print(f"Improvement: {(rf_accuracy - accuracy) * 100:.1f}%")
```

---

## Step 7: Package (Save) the Model

Once the model performs well, you save it as a file. This saved file is what gets deployed.

### Popular model file formats:

| Format | Extension | Library | Use case |
|--------|-----------|---------|----------|
| **Pickle** | `.pkl` | `pickle` | Most common Python format |
| **Joblib** | `.joblib` | `joblib` | Better for large numpy arrays |
| **ONNX** | `.onnx` | `onnx` | Cross-platform, language-agnostic |

`.pkl` and `.joblib` are the most frequently used.

### Code: Save and load the model

```python
import joblib

# Save the trained model to a file
joblib.dump(algorithm, 'flower_model.pkl')
print("Model saved as flower_model.pkl")

# Later, load and use it
loaded_model = joblib.load('flower_model.pkl')

# Predict with the loaded model
new_flower = [[5.1, 3.5, 1.4, 0.2]]
result = loaded_model.predict(new_flower)
print(f"Prediction: {iris.target_names[result[0]]}")
```

```bash
# Check the saved model file
ls -lh flower_model.pkl
```

**Output:**
```
-rw-r--r-- 1 user user 3.2K flower_model.pkl
```

The model is now a portable file that can be shipped anywhere.

---

## Step 8: Build API / Deploy the Model

Once the model is saved, software developers or ML engineers build an API around it so the model can be consumed by applications.

```
┌──────────────────────────────────────────────────────────┐
│              MODEL → PRODUCTION                           │
│                                                           │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│   │  Saved   │───►│  API     │───►│  Consumed by     │   │
│   │  Model   │    │  (Flask/ │    │                  │   │
│   │  (.pkl)  │    │  FastAPI)│    │  • Websites      │   │
│   │          │    │          │    │  • Mobile apps   │   │
│   │          │    │          │    │  • Microservices  │   │
│   │          │    │          │    │  • MLOps pipelines│   │
│   └──────────┘    └──────────┘    └──────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

### Code: Simple Flask API for the model

```bash
pip install flask
```

```python
# app.py — Simple API to serve the flower model
from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('flower_model.pkl')
species_names = ['setosa', 'versicolor', 'virginica']

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = np.array([[
        data['sepal_length'],
        data['sepal_width'],
        data['petal_length'],
        data['petal_width']
    ]])
    prediction = model.predict(features)
    return jsonify({
        'species': species_names[prediction[0]],
        'input': data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

```bash
# Run the API
python app.py

# Test it with curl (in another terminal)
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

**Response:**
```json
{
  "species": "setosa",
  "input": {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }
}
```

---

## Real-Life Examples: The Same 8 Steps Applied

### Example 1: Predicting House Prices

| Step | Action |
|------|--------|
| 1. Dataset | Collect data: square footage, bedrooms, location, age → price |
| 2. Split | 80% train, 20% test |
| 3. Algorithm | Linear Regression (predicting a number, not a category) |
| 4. Train | Algorithm learns: more bedrooms + larger area = higher price |
| 5. Test | Compare predicted prices vs actual prices |
| 6. Retrain | If predictions are off by too much, add more features (garage, pool) |
| 7. Package | Save as `house_price_model.pkl` |
| 8. Deploy | Real estate website calls the API to show estimated prices |

### Example 2: Detecting Spam Emails

| Step | Action |
|------|--------|
| 1. Dataset | Millions of emails labeled "spam" or "not spam" |
| 2. Split | 80% train, 20% test |
| 3. Algorithm | Naive Bayes (good for text classification) |
| 4. Train | Algorithm learns: words like "free", "winner", "click here" → spam |
| 5. Test | Check how many spam/not-spam emails are correctly classified |
| 6. Retrain | If too many false positives, adjust threshold or add more data |
| 7. Package | Save as `spam_detector.pkl` |
| 8. Deploy | Email service calls the model for every incoming email |

### Example 3: Credit Card Fraud Detection

| Step | Action |
|------|--------|
| 1. Dataset | Transaction history: amount, location, time, merchant → fraud/legit |
| 2. Split | 80% train, 20% test |
| 3. Algorithm | Random Forest or XGBoost |
| 4. Train | Algorithm learns: unusual amount + foreign location + midnight = fraud |
| 5. Test | Measure precision (don't block legitimate transactions) |
| 6. Retrain | Fraud patterns change over time — retrain monthly |
| 7. Package | Save as `fraud_model.pkl` |
| 8. Deploy | Bank's payment gateway calls the model in real-time |

---

## Who Does What?

| Role | Responsibility in this process |
|------|-------------------------------|
| **Data Scientist** | Steps 1–7: Collect data, choose algorithm, train, test, retrain, package |
| **ML Engineer** | Steps 7–8: Package model, build APIs, optimize for production |
| **Software Developer** | Step 8: Integrate model API into websites, mobile apps, services |
| **MLOps Engineer** | Automate Steps 1–8: CI/CD pipelines, monitoring, retraining automation |

> As an MLOps engineer, you don't decide which algorithm to use. You automate the pipeline so that data scientists can iterate faster and models get deployed reliably.

---

## Complete Working Example: All 8 Steps in One Script

Save as `model_pipeline.py`:

```python
"""
Complete model creation pipeline — all 8 steps.
"""
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import numpy as np

# Step 1: Load dataset
print("Step 1: Loading dataset...")
iris = load_iris()
print(f"  Loaded {len(iris.data)} samples with {len(iris.feature_names)} features")

# Step 2: Split data (80/20)
print("\nStep 2: Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)
print(f"  Training: {len(X_train)} samples")
print(f"  Testing:  {len(X_test)} samples")

# Step 3: Choose algorithm
print("\nStep 3: Choosing algorithm...")
model = DecisionTreeClassifier(random_state=42)
print(f"  Algorithm: {model.__class__.__name__}")

# Step 4: Train the model
print("\nStep 4: Training model...")
model.fit(X_train, y_train)
print("  Training complete!")

# Step 5: Test the model
print("\nStep 5: Testing model...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"  Accuracy: {accuracy * 100:.1f}%")
print(classification_report(y_test, predictions, target_names=iris.target_names))

# Step 6: Check if retraining is needed
print("Step 6: Evaluating if retraining is needed...")
if accuracy >= 0.95:
    print(f"  Accuracy {accuracy*100:.1f}% is above 95% threshold. No retraining needed.")
else:
    print(f"  Accuracy {accuracy*100:.1f}% is below 95%. Consider retraining with different algorithm.")

# Step 7: Save the model
print("\nStep 7: Saving model...")
joblib.dump(model, 'flower_model.pkl')
print("  Model saved as flower_model.pkl")

# Step 8: Simulate API usage
print("\nStep 8: Simulating prediction (as an API would)...")
loaded_model = joblib.load('flower_model.pkl')
new_input = np.array([[5.1, 3.5, 1.4, 0.2]])
prediction = loaded_model.predict(new_input)
print(f"  Input:  {new_input[0].tolist()}")
print(f"  Output: {iris.target_names[prediction[0]]}")
print("\nAll 8 steps complete!")
```

```bash
# Run the complete pipeline
python model_pipeline.py
```

**Expected output:**
```
Step 1: Loading dataset...
  Loaded 150 samples with 4 features

Step 2: Splitting data...
  Training: 120 samples
  Testing:  30 samples

Step 3: Choosing algorithm...
  Algorithm: DecisionTreeClassifier

Step 4: Training model...
  Training complete!

Step 5: Testing model...
  Accuracy: 96.7%
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       1.00      0.89      0.94         9
   virginica       0.92      1.00      0.96        11

    accuracy                           0.97        30

Step 6: Evaluating if retraining is needed...
  Accuracy 96.7% is above 95% threshold. No retraining needed.

Step 7: Saving model...
  Model saved as flower_model.pkl

Step 8: Simulating prediction (as an API would)...
  Input:  [5.1, 3.5, 1.4, 0.2]
  Output: setosa

All 8 steps complete!
```
