# Role of an ML Engineer in a Project

In the previous lectures, we learned how data scientists train a model and how MLOps engineers set up continuous training. When a data scientist makes changes, the CI pipeline runs, trains the model, and uploads a new version to the artifact location.

Fellow data scientists or ML engineers can download the model from there for evaluation or testing. **But what about end users?**

---

## The Problem: End Users Can't Use Artifacts

Imagine you're a data scientist at Netflix and you've developed a recommendation model. MLOps engineers set up the Git repository and continuous training. Every time you make changes, a new model version is uploaded to the artifact location.

Your fellow data scientists can download and evaluate the model. But you **cannot expect end users** to:
- Go to the GitHub artifact location
- Download `model.pkl`
- Run it on their machine to get movie recommendations

That's impossible. What you need is an **API** — so the model can be integrated into backend systems like the Netflix mobile app or website. Users click a button, the API calls the model, and they get their recommendations.

**This is where ML engineers come into picture.**

---

## Two Primary Responsibilities of ML Engineers

```
┌──────────────────────────────────────────────────────────────────┐
│           ML ENGINEER'S RESPONSIBILITIES                          │
│                                                                   │
│   1. Ensure Scalability & Performance                            │
│      • Data scientists develop models locally                    │
│      • Their focus is model accuracy, not scale                  │
│      • ML engineers ensure the model can handle                  │
│        millions of users (Netflix scale)                         │
│      • Optimize for latency, throughput, memory                  │
│                                                                   │
│   2. Develop an API for the Model                                │
│      • So the model can be integrated into backend systems       │
│      • Mobile apps, websites, microservices can call the API     │
│      • End users access the model through these applications     │
└──────────────────────────────────────────────────────────────────┘
```

In this lecture, we focus on **building the API**.

---

## Building the API: `app.py`

ML engineers typically use Python for building model APIs. Two popular frameworks:

| Framework | When to use |
|-----------|------------|
| **Flask** | Simple requirements, lightweight, quick to set up |
| **FastAPI** | More features, async support, auto-generated docs |

For this project, we use Flask because the requirement is simple — you can develop an API in a couple of minutes.

### The complete API: `app.py`

```python
from flask import Flask, request, jsonify
import joblib
import os
from pathlib import Path

app = Flask(__name__)
MODEL_PATH = Path("artifacts/model.pkl")

if not MODEL_PATH.exists():
    # convenience: train if model missing
    import train as _train
    _train.main()

model = joblib.load(MODEL_PATH)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or "features" not in data:
        return jsonify({"error": "send JSON with key 'features'"}), 400
    features = data["features"]
    try:
        pred = model.predict([features])
        return jsonify({"prediction": int(pred[0])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
```

### Line-by-line explanation

#### Model loading

```python
MODEL_PATH = Path("artifacts/model.pkl")

if not MODEL_PATH.exists():
    import train as _train
    _train.main()

model = joblib.load(MODEL_PATH)
```

- `MODEL_PATH` points to the saved model in the `artifacts/` folder
- If the model doesn't exist, the script can either return an error or retrigger training
- `joblib.load()` loads the model into memory once — it's not reloaded for every request

#### Health check endpoint

```python
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
```

A simple endpoint to verify the API is running. Used by monitoring tools and load balancers.

#### Prediction endpoint (the important part)

```python
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data or "features" not in data:
        return jsonify({"error": "send JSON with key 'features'"}), 400
    features = data["features"]
    try:
        pred = model.predict([features])
        return jsonify({"prediction": int(pred[0])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

| Line | What it does |
|------|-------------|
| `@app.route("/predict", methods=["POST"])` | API is available at `/predict` and accepts HTTP POST requests |
| `data = request.get_json()` | Read input features in JSON format |
| `if not data or "features" not in data` | Validate that input is in expected format |
| `model.predict([features])` | Run the model with input features and get prediction |
| `return jsonify({"prediction": int(pred[0])})` | Return the output in JSON format |
| `except Exception as e` | Handle errors gracefully — don't crash the service |

> **Why HTTP POST?** Because you provide the model with input features (sepal length, sepal width, petal length, petal width) and the model returns the output. POST is used when sending data to the server. GET, PUT, or DELETE would return an error.

#### Running the API

```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
```

- `host="0.0.0.0"` — listen on all network interfaces
- `port=5001` — run on port 5001 (5000 is the default, but may conflict with other services)

---

## Running and Testing the API

### Start the API

```bash
python3.12 app.py
```

**Output:**
```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5001
 * Running on http://192.168.100.102:5001
Press CTRL+C to quit
```

### Test with curl (in a separate terminal)

```bash
# Test 1: Input [5.1, 3.5, 1.4, 0.2]
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[5.1,3.5,1.4,0.2]}'
# Output: {"prediction":0}    ← Setosa

# Test 2: Input [10, 1, 5, 2]
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[10,1,5,2]}'
# Output: {"prediction":1}    ← Versicolor

# Test 3: Input [1, 1, 1, 1]
curl -X POST "http://127.0.0.1:5001/predict" \
  -H "Content-Type: application/json" \
  -d '{"features":[1,1,1,1]}'
# Output: {"prediction":0}    ← Setosa
```

The model is now accessible via an API. Any application — mobile app, website, microservice — can call this endpoint and get predictions.

---

## What ML Engineers Handle

| Responsibility | What they do |
|---------------|-------------|
| **Input validation** | Ensure inputs are in expected format, handle missing/incorrect fields |
| **Error handling** | Errors don't crash the service — return proper error messages |
| **Model loading** | Load model once at startup, not on every request |
| **Performance** | Optimize for low latency and high throughput |
| **API design** | Clean endpoints, proper HTTP methods, JSON input/output |

---

## The Remaining Problem

The API works, but it's running on **localhost**. To make it publicly available, more steps are needed:

```
┌──────────────────────────────────────────────────────────────────┐
│           WHAT'S STILL MISSING                                    │
│                                                                   │
│   ✅ Model trained and saved (Data Scientist)                    │
│   ✅ CI/CD set up for training (MLOps Engineer)                  │
│   ✅ API built for the model (ML Engineer)                       │
│                                                                   │
│   ❌ Model runs on localhost only                                │
│   ❌ Not containerized                                           │
│   ❌ No infrastructure (servers, clusters)                       │
│   ❌ No Kubernetes deployment                                    │
│   ❌ No load balancing, networking, security                     │
│   ❌ No monitoring                                               │
│                                                                   │
│   This is where MLOps engineers help ML engineers.               │
│   → Next lecture                                                  │
└──────────────────────────────────────────────────────────────────┘
```
