# Module 6: AI and Machine Learning (ML)

## 6.1 What is Artificial Intelligence?

AI is a broad field for developing intelligent systems capable of performing tasks that typically require human intelligence: perception, reasoning, learning, problem solving, and decision-making.

AI is an umbrella term for various techniques:

```
┌─────────────────────────────────────────────┐
│           Artificial Intelligence            │
│  ┌───────────────────────────────────────┐  │
│  │         Machine Learning              │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │        Deep Learning            │  │  │
│  │  │  ┌───────────────────────────┐  │  │  │
│  │  │  │    Generative AI          │  │  │  │
│  │  │  └───────────────────────────┘  │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### AI Use Cases

| Use Case | Example |
|----------|---------|
| **Computer Vision** | Object detection, image classification |
| **Facial Recognition** | Identity verification, access control |
| **Fraud Detection** | Flagging suspicious transactions |
| **Intelligent Document Processing** | Extracting data from invoices and forms |

### AI is NOT Always Machine Learning

**Example: MYCIN Expert System (1970s)**

MYCIN was an AI system that diagnosed patients based on symptoms and test results — but it was NOT machine learning:

| Property | Details |
|----------|---------|
| **Type** | Rule-based expert system (AI, but not ML) |
| **How it worked** | Collection of over 500 hand-written rules |
| **Input** | Simple yes/no or textual questions |
| **Output** | List of bacteria ranked by probability, diagnosis reasoning, and dosage recommendations |
| **Limitation** | Never used in production — personal computers didn't exist yet |

> **Key Exam Point:** AI includes rule-based systems (like MYCIN) that don't learn from data. Machine Learning is a *subset* of AI where systems learn from data. Not all AI is ML.

### AI Components

```
┌──────────────────────────────────────────────┐
│  Application Layer                           │
│  How to serve the model for your users       │
├──────────────────────────────────────────────┤
│  Model Layer                                 │
│  Structure, parameters, functions, optimizer │
├──────────────────────────────────────────────┤
│  ML Framework and Algorithm Layer            │
│  Data scientists + engineers understand      │
│  use cases, requirements, and frameworks     │
├──────────────────────────────────────────────┤
│  Data Layer                                  │
│  Collect vast amounts of data                │
└──────────────────────────────────────────────┘
```

| Layer | Who | What |
|-------|-----|------|
| **Data Layer** | Data engineers | Collect and store vast amounts of data |
| **ML Framework Layer** | Data scientists + engineers | Understand use cases, select frameworks and algorithms |
| **Model Layer** | ML engineers | Implement model structure, parameters, optimizer functions |
| **Application Layer** | Developers | Serve the model's capabilities to end users |

---

## 6.2 What is Machine Learning?

Machine Learning is a type of AI for building methods that allow machines to learn. Data is leveraged to improve computer performance on a set of tasks — making predictions based on data used to train the model, with no explicit programming of rules.

```
Traditional Programming:          Machine Learning:
┌────────┐                        ┌────────┐
│ Rules   │                       │ Data    │
│ + Data  │──► Output             │ + Output│──► Rules (Model)
└────────┘                        └────────┘
```

- **Traditional Programming:** You write rules; the program applies them to data
- **Machine Learning:** You provide data and expected outputs; the algorithm learns the rules

---

## 6.3 Training Data

To train a model you must have good data. **Garbage in = Garbage out.** Data preparation is the most critical stage to build a good model.

### Labeled vs. Unlabeled Data

| Type | Description | Example | Used For |
|------|-------------|---------|----------|
| **Labeled Data** | Includes both input features AND corresponding output labels | Images of animals where each image is labeled "cat" or "dog" | Supervised Learning |
| **Unlabeled Data** | Includes only input features WITHOUT any output labels | A collection of images without any associated labels | Unsupervised Learning |

```
Labeled Data:                    Unlabeled Data:
┌───────┬───────┐               ┌───────┐
│ Image │ Label │               │ Image │
├───────┼───────┤               ├───────┤
│ 🐕    │ Dog   │               │ 🐕    │  (no label)
│ 🐈    │ Cat   │               │ 🐈    │  (no label)
│ 🐕    │ Dog   │               │ 🐕    │  (no label)
│ 🐈    │ Cat   │               │ 🐈    │  (no label)
└───────┴───────┘               └───────┘
```

### Structured vs. Unstructured Data

#### Structured Data

Data organized in a specific format, often in rows and columns (like Excel).

| Type | Description | Example |
|------|-------------|---------|
| **Tabular Data** | Arranged in a table with rows (records) and columns (features) | Customer database with Name, Age, Purchase Amount |
| **Time Series Data** | Data points collected at successive points in time | Stock prices recorded daily over a year |

```
Tabular Data:                    Time Series Data:
┌────┬───────┬─────┬────────┐   ┌────────────┬─────────────┐
│ ID │ Name  │ Age │ Amount │   │ Date       │ Stock Price │
├────┼───────┼─────┼────────┤   ├────────────┼─────────────┤
│ 1  │ Alice │ 30  │ $200   │   │ 01-07-2024 │ $197.20     │
│ 2  │ Bob   │ 45  │ $300   │   │ 02-07-2024 │ $200.00     │
└────┴───────┴─────┴────────┘   └────────────┴─────────────┘
```

#### Unstructured Data

Data that doesn't follow a specific structure — often text-heavy or multimedia content.

| Type | Description | Example |
|------|-------------|---------|
| **Text Data** | Articles, social media posts, customer reviews | Product reviews from an e-commerce site |
| **Image Data** | Images varying in format and content | Photos used for object recognition tasks |
| **Audio Data** | Sound recordings, speech | Customer service call recordings |
| **Video Data** | Video files | Security camera footage |

---

## 6.4 Types of Machine Learning

### 6.4.1 Supervised Learning

The model learns from **labeled data** (input-output pairs).

```
Training Data (Labeled):
┌──────────────┬──────────┐
│ Input (Email)│ Label    │
├──────────────┼──────────┤
│ "Buy now!!!" │ Spam     │
│ "Meeting at 3│ Not Spam │
│ "Free prize!"│ Spam     │
│ "Project upd"│ Not Spam │
└──────────────┴──────────┘
         │
         ▼
    [ML Algorithm]
         │
         ▼
    [Trained Model]
         │
    New email: "Win a free car!"
         │
         ▼
    Prediction: Spam (95% confidence)
```

**Common tasks:**
| Task | Description | Example |
|------|-------------|---------|
| **Classification** | Assign a category to input | Spam/Not Spam, Cat/Dog |
| **Regression** | Predict a continuous number | House price, temperature |

#### Regression (Predicting Numbers)

Used to predict a **numeric/continuous** value based on input data.

```
Predicting House Prices:

Price ($K)
500 │                          •
400 │                    •  •
300 │              •  •
200 │        •  •
100 │  •  •
    └──────────────────────────
     1000  1500  2000  2500  3000
              House Size (sq ft)
```

| Use Case | What It Predicts |
|----------|-----------------|
| **House Prices** | Price based on size, location, bedrooms |
| **Stock Prices** | Future price based on historical data |
| **Weather** | Temperature based on historical weather data |

#### Classification (Predicting Categories)

Used to predict the **categorical label** of input data. The output is discrete (falls into a specific category).

| Type | Description | Example |
|------|-------------|---------|
| **Binary Classification** | Two categories | Spam / Not Spam |
| **Multiclass Classification** | Multiple categories | Mammal / Bird / Reptile |
| **Multi-label Classification** | Multiple labels per item | A movie tagged as both "Action" AND "Comedy" |

**Key algorithm:** K-nearest neighbors (k-NN) — classifies based on the closest training examples.

```
Classification Model:
┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Labeled      │────>│ Classification│────>│ Inbox    │
│ Emails       │     │ Model        │     │ or       │
│ (training)   │     │              │     │ Spam     │
└──────────────┘     └──────┬───────┘     └──────────┘
                            │
                     Incoming email
                     "Win a free car!"
                            │
                            ▼
                        → Spam
```

### 6.4.2 Unsupervised Learning

The model discovers inherent patterns, structures, or relationships within **unlabeled data**. The machine uncovers and creates the groups itself, but humans still put labels on the output groups.

Feature Engineering can help improve the quality of unsupervised learning.

#### Clustering

Group similar data points together based on their features.

```
Customer Purchases:
┌─────────────────────┐
│ Pizza, Chips, Beers  │──► Group 1 (Party shoppers)
│ Baby Shampoo, Wipes  │──► Group 2 (Parents)
│ Fruits, Vegetables   │──► Group 3 (Health-conscious)
└─────────────────────┘
```

**Example: Customer Segmentation**
- **Scenario:** E-commerce company wants to segment customers
- **Data:** Customer purchase history (frequency, average order value)
- **Technique:** K-means Clustering
- **Outcome:** Tailored marketing strategies for each segment

#### Association Rule Learning

Discover relationships between items that frequently occur together.

**Example: Market Basket Analysis**
- **Scenario:** Supermarket wants to know which products are bought together
- **Data:** Transaction records from customer purchases
- **Technique:** Apriori algorithm
- **Outcome:** Place bread and butter together to boost sales

#### Anomaly Detection

Identify data points that deviate significantly from typical behavior.

```
Normal transactions:     Anomaly (outlier):
    •  •  •                    • ← Flagged!
  •  •  •  •
    •  •  •
```

**Example: Fraud Detection**
- **Scenario:** Detect fraudulent credit card transactions
- **Data:** Transaction data (amount, location, time)
- **Technique:** Isolation Forest
- **Outcome:** System flags potentially fraudulent transactions for investigation

### 6.4.3 Reinforcement Learning (RL)

A type of ML where an **agent** learns to make decisions by performing actions in an environment to **maximize cumulative rewards**.

#### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | The learner or decision-maker |
| **Environment** | The external system the agent interacts with |
| **Action** | The choices made by the agent |
| **Reward** | Feedback from the environment based on the agent's actions |
| **State** | The current situation of the environment |
| **Policy** | The strategy the agent uses to determine actions based on the state |

#### How RL Works

```
┌───────┐    Action     ┌─────────────┐
│ Agent │──────────────>│ Environment │
│       │<──────────────│             │
└───────┘  Reward +     └─────────────┘
           New State
```

1. The Agent observes the current **State** of the Environment
2. It selects an **Action** based on its **Policy**
3. The Environment transitions to a new **State** and provides a **Reward**
4. The Agent updates its **Policy** to improve future decisions
5. **Goal:** Maximize cumulative reward over time

#### Example: Robot Navigating a Maze

```
+100 = Exit (goal)
  -1 = Each step taken
 -10 = Hitting a wall

The robot simulates many times,
learns from mistakes and successes,
and eventually finds the optimal path.
```

#### Applications of RL

| Application | Example |
|------------|---------|
| **Gaming** | Teaching AI to play Chess, Go, StarCraft |
| **Robotics** | Navigating and manipulating objects in dynamic environments |
| **Finance** | Portfolio management and trading strategies |
| **Healthcare** | Optimizing treatment plans |
| **Autonomous Vehicles** | Path planning and decision-making |

#### RLHF — Reinforcement Learning from Human Feedback

RLHF uses **human feedback** in the reward function to align ML models with human goals, wants, and needs. It is used throughout Gen-AI applications including LLM models.

**How RLHF Works (Example: Internal Company Knowledge Chatbot):**

```
Step 1: Data Collection
  → Human-generated prompts and responses are created

Step 2: Supervised Fine-Tuning
  → Fine-tune an existing model with internal knowledge
  → Model creates responses for human-generated prompts
  → Responses are compared to human-generated answers

Step 3: Build a Reward Model
  → Humans indicate which response they prefer
  → Reward model learns to estimate human preferences

Step 4: Optimize with RL
  → Use the reward model as a reward function
  → This part can be fully automated
```

> **Key Exam Point:** RLHF significantly enhances model performance by incorporating human judgment. Example: grading text translations from "technically correct" to "natural-sounding human language."

### 6.4.4 Semi-Supervised Learning

Uses a **small amount of labeled data** and a **large amount of unlabeled data** to train systems.

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Small amount of  │     │              │     │ Model labels     │
│ labeled data     │────>│    Model     │────>│ the unlabeled    │
│ + Large amount   │     │  (partially  │     │ data itself      │
│ of unlabeled data│     │   trained)   │     │ (pseudo-labeling)│
└──────────────────┘     └──────────────┘     └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────────┐
                                              │ Re-train model   │
                                              │ on combined data │
                                              │ (labeled +       │
                                              │  pseudo-labeled) │
                                              └──────────────────┘
```

**How it works:**
1. Train the model on the small labeled dataset
2. The partially trained model **labels the unlabeled data** itself (pseudo-labeling)
3. The model is re-trained on the combined data (original labels + pseudo-labels)
4. No explicit programming needed — the model improves iteratively

### 6.4.5 Self-Supervised Learning

The model generates **pseudo-labels for its own data** without any human labeling. Then, using those pseudo-labels, it solves problems traditionally solved by supervised learning.

**Widely used in:**
- NLP (to create BERT and GPT models)
- Image recognition tasks

**How it works — Pretext Tasks:**

```
Original text:
"Amazon Web Services (AWS) is a subsidiary of Amazon that provides
on-demand cloud computing platforms and APIs to individuals,
companies, and governments..."

Pretext Task (fill in the blank):
"APIs to individuals, _________, and governments"
Answer: "companies"
```

The model learns by solving these "fill in the blank" tasks:
- **Predict any part** of the input from any other part
- **Predict the future** from the past
- **Predict the masked** from the visible

After solving pretext tasks, the model has learned language patterns and can solve real **downstream tasks** (translation, summarization, Q&A).

> **Key Exam Point:** Self-supervised learning is how LLMs like GPT and BERT are pre-trained — they learn language structure from massive unlabeled text without human labeling.

---

## 6.5 The ML Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 1. Data  │──>│ 2. Data  │──>│ 3. Model │──>│ 4. Model │──>│ 5. Model │
│ Collection│   │ Prep &   │   │ Training │   │ Evaluation│  │ Deployment│
│           │   │ Cleaning │   │          │   │          │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

| Step | What Happens | AWS Service |
|------|-------------|-------------|
| **Data Collection** | Gather raw data from various sources | S3, Kinesis, Glue |
| **Data Preparation** | Clean, transform, label data | SageMaker Data Wrangler, Glue |
| **Model Training** | Feed data to algorithm, model learns patterns | SageMaker Training |
| **Model Evaluation** | Test model accuracy on unseen data | SageMaker |
| **Model Deployment** | Make model available for predictions | SageMaker Endpoints |

---

## 6.6 Key ML Concepts

### Training, Validation, and Test Sets

```
              Dataset (100%)
┌──────────────────────────────────────────────┐
│                                              │
│  ┌────────────────────────────────┐          │
│  │     Training Set (60-80%)     │          │
│  │     Model learns from this    │          │
│  └────────────────────────────────┘          │
│  ┌──────────────────┐                        │
│  │ Validation (10-20%)│                      │
│  │ Tune hyperparams  │                       │
│  └──────────────────┘                        │
│  ┌──────────────────┐                        │
│  │ Test Set (10-20%) │                       │
│  │ Final evaluation  │                       │
│  └──────────────────┘                        │
└──────────────────────────────────────────────┘
```

| Set | Purpose | Typical % | Example (1000 images) |
|-----|---------|-----------|----------------------|
| **Training Set** | Train the model — it learns patterns from this data | 60-80% | 800 labeled images |
| **Validation Set** | Tune model parameters (hyperparameters) and validate performance during training | 10-20% | 100 labeled images for tuning |
| **Test Set** | Evaluate the final model performance on data it has never seen | 10-20% | 100 labeled images for final testing |

> **Key Exam Point:** The test set must NEVER be used during training. It's reserved for final evaluation only.

### Feature Engineering

The process of using domain knowledge to select and transform raw data into meaningful features that enhance ML model performance.

| Technique | Description | Example |
|-----------|-------------|---------|
| **Feature Extraction** | Extract useful information from raw data | Derive "age" from "date of birth" |
| **Feature Selection** | Select a subset of relevant features | Choose important predictors in a regression model |
| **Feature Transformation** | Transform data for better model performance | Normalize numerical data to a common scale |

**Example: Before and After Feature Engineering**

```
Before:
┌────┬───────┬────────────┬────────┐
│ ID │ Name  │ BirthDate  │ Amount │
├────┼───────┼────────────┼────────┤
│ 1  │ Alice │ 15-05-1993 │ $200   │
│ 2  │ Bob   │ 22-08-1978 │ $300   │
└────┴───────┴────────────┴────────┘

After Feature Engineering:
┌────┬───────┬─────┬────────┐
│ ID │ Name  │ Age │ Amount │
├────┼───────┼─────┼────────┤
│ 1  │ Alice │ 30  │ $200   │
│ 2  │ Bob   │ 45  │ $300   │
└────┴───────┴─────┴────────┘
```

#### Feature Engineering on Structured Data

- **Feature Creation** — Derive new features like "price per square foot" from price and size
- **Feature Selection** — Retain important features (location, bedrooms) and drop irrelevant ones
- **Feature Transformation** — Normalize features to a similar scale (helps algorithms converge faster)

#### Feature Engineering on Unstructured Data

- **Text Data** — Convert text into numerical features using TF-IDF or word embeddings
- **Image Data** — Extract features like edges or textures using CNNs

> Feature Engineering is particularly meaningful for **Supervised Learning**.

### Exploratory Data Analysis (EDA)

Before building a model, visualize and explore your data:

| Technique | Purpose |
|-----------|---------|
| **Graphs/Charts** | Visualize distributions, trends, outliers |
| **Correlation Matrix** | See how "linked" variables are to each other |
| **Feature Importance** | Decide which features matter for your model |

**Example: Correlation Matrix for Student Test Scores**

```
                Hours Studied  Test Score  Sleep Hours  Distractions
Hours Studied        1.00         0.85        0.40        -0.60
Test Score           0.85         1.00        0.30        -0.50
Sleep Hours          0.40         0.30        1.00        -0.20
Distractions        -0.60        -0.50       -0.20         1.00
```

- Values close to **1.0** = strong positive correlation (Hours Studied ↔ Test Score)
- Values close to **-1.0** = strong negative correlation (Distractions ↔ Test Score)
- Values close to **0** = weak or no correlation

### Model Fit: Overfitting vs. Underfitting

If your model has poor performance, examine its fit:

| Problem | Description | Symptom | Fix |
|---------|-------------|---------|-----|
| **Overfitting** | Model memorizes training data, fails on new data | High training accuracy, low test accuracy | More data, regularization, simpler model, feature selection |
| **Underfitting** | Model is too simple to capture patterns | Low training accuracy, low test accuracy | More features, more complex model, more training |
| **Balanced** | Neither overfitting nor underfitting | Good on both training and test data | Target state |

```
Underfitting          Good Fit            Overfitting
(too simple)          (just right)        (too complex)
High bias             Low bias/variance   High variance

    /                  ╱╲                 ╱╲╱╲╱╲
   /                  ╱  ╲╱╲             ╱      ╲
  /                  ╱      ╲           ╱        ╲
```

### Bias and Variance

| Concept | Definition | When It's High | How to Fix |
|---------|-----------|---------------|-----------|
| **Bias** | Difference between predicted and actual values | Model doesn't match training data (underfitting) | Use more complex model, increase features |
| **Variance** | How much performance changes on different datasets with similar distribution | Model is very sensitive to training data (overfitting) | Feature selection, cross-validation |

```
              Low Variance     High Variance
High Bias     Underfitting     (worst case)
Low Bias      Balanced ✅      Overfitting
```

### Confusion Matrix (for Classification)

**Binary Classification Example (Spam Detection):**

```
True Values:    Predictions:    Result:
Spam            Spam            True Positive (TP)
Not Spam        Spam            False Positive (FP)
Spam            Not Spam        False Negative (FN)
Not Spam        Not Spam        True Negative (TN)
```

```
                    Predicted
                 Positive  Negative
Actual Positive │  TP    │   FN    │
Actual Negative │  FP    │   TN    │
```

> Confusion matrices can be **multi-dimensional** too (e.g., 3x3 for Positive/Neutral/Negative).

| Metric | Formula | What It Measures |
|--------|---------|-----------------|
| **Accuracy** | (TP + TN) / Total | Overall correctness |
| **Precision** | TP / (TP + FP) | Of predicted positives, how many are correct |
| **Recall** | TP / (TP + FN) | Of actual positives, how many were found |
| **F1 Score** | 2 × (Precision × Recall) / (Precision + Recall) | Balance of precision and recall |

### When to Use Which Metric

| Metric | Best When | Example |
|--------|----------|---------|
| **Precision** | False positives are costly | Spam filter — don't want real emails marked as spam |
| **Recall** | False negatives are costly | Medical diagnosis — don't want to miss tumors |
| **F1 Score** | Balance needed, especially with imbalanced datasets | Fraud detection — both false alarms and missed fraud matter |
| **Accuracy** | Balanced datasets | General classification with equal class distribution |

> **Example: Medical Diagnosis**
> A model predicts whether an X-ray shows a tumor. **Recall** is more important — you'd rather have false positives (extra tests) than false negatives (missed tumors).

### AUC-ROC (Area Under the Curve — Receiver Operating Characteristic)

Evaluates classification models across different thresholds.

```
Sensitivity (True Positive Rate)
1.0 │         ╱── Model 3 (AUC: 0.893)
    │       ╱
0.8 │     ╱── Model 2 (AUC: 0.687)
    │   ╱╱
0.6 │  ╱╱
    │ ╱╱── Model 1 (AUC: 0.5 = random)
0.4 │╱╱
    │╱
0.2 │
    └──────────────────────────
    0   0.2  0.4  0.6  0.8  1.0
    1-Specificity (False Positive Rate)
```

| Property | Details |
|----------|---------|
| **Value range** | 0 to 1 (1 = perfect model) |
| **AUC = 0.5** | No better than random guessing |
| **AUC > 0.8** | Good model performance |
| **Use** | Compare models; find the best threshold for your business case |

### Regression Metrics

For models that predict **continuous values** (not categories):

| Metric | What It Measures | Interpretation |
|--------|-----------------|---------------|
| **MAE** (Mean Absolute Error) | Average absolute difference between predicted and actual | Lower is better |
| **MAPE** (Mean Absolute Percentage Error) | Average percentage difference | Lower is better |
| **RMSE** (Root Mean Squared Error) | Penalizes large errors more than MAE | Lower is better. RMSE = 5 means predictions are ~5 points off |
| **R-squared** | Proportion of variance explained by the model | Closer to 1 is better. R² = 0.8 means 80% of variation is explained |

> **Example:** Predicting student test scores. If RMSE = 5, predictions are about 5 points off on average. If R² = 0.8, 80% of score changes are explained by study hours; 20% is due to other factors.

---

## 6.7 ML Terms Glossary

Key ML terms you may encounter on the exam:

| Term | Full Name | What It Does |
|------|-----------|-------------|
| **GPT** | Generative Pre-trained Transformer | Generate human text or code based on input prompts |
| **BERT** | Bidirectional Encoder Representations from Transformers | Similar to GPT but reads text in two directions |
| **RNN** | Recurrent Neural Network | Sequential data (time-series, text); useful in speech recognition |
| **ResNet** | Residual Network | Deep CNN for image recognition, object detection, facial recognition |
| **SVM** | Support Vector Machine | ML algorithm for classification and regression |
| **WaveNet** | — | Model to generate raw audio waveforms; used in speech synthesis |
| **GAN** | Generative Adversarial Network | Generate synthetic data (images, videos, sounds) resembling training data; helpful for data augmentation |
| **XGBoost** | Extreme Gradient Boosting | Implementation of gradient boosting for classification and regression |
| **k-NN** | K-Nearest Neighbors | Classification based on closest training examples |
| **K-means** | — | Clustering algorithm that groups data into K clusters |
| **Apriori** | — | Association rule learning (market basket analysis) |
| **Isolation Forest** | — | Anomaly detection algorithm |

---

## 6.8 Deep Learning and Neural Networks

### What is Deep Learning?

Deep Learning uses **neurons and synapses** (like our brain) to train models that process more complex patterns than traditional ML. It's called "deep" because there are **more than one layer** of learning.

**Characteristics:**
- Large amount of input data required
- Requires **GPU** (Graphical Processing Unit) for training
- Used for Computer Vision (image classification, object detection) and NLP (text classification, sentiment analysis, translation)

### How Neural Networks Work

```
Input Layer      Hidden Layers       Output Layer
   ○─────────────○                      ○
   ○─────────────○──────────○           ○
   ○─────────────○──────────○───────────○
   ○─────────────○──────────○
   ○─────────────○
```

| Component | Role |
|-----------|------|
| **Input Layer** | Receives the raw data (pixels, text, numbers) |
| **Hidden Layers** | Process and transform data through learned weights |
| **Output Layer** | Produces the prediction (class label, number, text) |

**How nodes work:**
- Nodes (tiny units) are connected together and organized in layers
- When the neural network sees a lot of data, it identifies patterns and changes the connections between nodes
- Nodes "talk" to each other by passing (or not passing) data to the next layer
- Neural networks may have **billions of nodes**

### Deep Learning Example: Recognizing Handwritten Digits

```
Handwritten     Input Layer     Hidden Layers        Output Layer
Numbers         (pixels)        (lines & curves)     (highest probability)

  ┌───┐
  │ 7 │ ──────► [pixels] ──────► [vertical lines] ──► 7 (0.94)
  └───┘                          [angles]              4 (0.03)
                                 [no curves]           1 (0.02)
```

Each layer learns about a "pattern" in the data:
- **Layer 1:** Detects edges and simple lines
- **Layer 2:** Combines lines into shapes (vertical lines for 1, 4, 7; curved bottom for 6, 8, 0)
- **Layer 3:** Combines shapes into digit recognition
- All of this is **learned** by the neural network — not programmed

### Common Neural Network Types

| Type | Use Case | Example |
|------|----------|---------|
| **CNN** (Convolutional Neural Network) | Image recognition | Identifying objects in photos |
| **RNN** (Recurrent Neural Network) | Sequential data | Time series, speech |
| **Transformer** | Text generation, translation | GPT-4, BERT, Claude |
| **GAN** (Generative Adversarial Network) | Image generation | Creating realistic faces |

### The Transformer Model (LLM Architecture)

Transformers are the architecture behind modern LLMs. They process a sentence **as a whole** instead of word by word.

```
┌──────────────────────────────────────────┐
│            Transformer Architecture       │
│                                           │
│  ┌─────────────┐    ┌─────────────────┐  │
│  │   Encoder    │    │    Decoder      │  │
│  │              │    │                 │  │
│  │ Input        │    │ Output          │  │
│  │ Embedding    │    │ Embedding       │  │
│  │      ↓       │    │      ↓          │  │
│  │ Self         │    │ Self            │  │
│  │ Attention    │───>│ Attention       │  │
│  │      ↓       │    │      ↓          │  │
│  │ Feed Forward │    │ Feed Forward    │  │
│  │              │    │      ↓          │  │
│  │              │    │ Softmax         │  │
│  │              │    │      ↓          │  │
│  │              │    │ Output          │  │
│  │              │    │ Probabilities   │  │
│  └─────────────┘    └─────────────────┘  │
└──────────────────────────────────────────┘
```

**Key advantages:**
- Faster and more efficient text processing (less training time)
- Gives relative importance to specific words in a sentence (more coherent output)
- Trained on vast amounts of text data from the internet, books, and other sources

**Examples:** Google BERT, OpenAI ChatGPT (Chat Generative Pretrained Transformer)

> **Key Exam Point:** ChatGPT stands for "Chat Generative Pretrained **Transformer**" — it uses the Transformer architecture.

---

## 6.9 Multi-Modal Models

Multi-modal models do NOT rely on a single type of input or output. They can process and generate **multiple types of content** simultaneously.

```
┌──────────────────────────────────────────────────┐
│              Multi-Modal Model                    │
│              (e.g., GPT-4o)                       │
│                                                   │
│  Inputs:              Outputs:                    │
│  ┌──────────┐         ┌──────────┐               │
│  │ Text     │         │ Text     │               │
│  │ Image    │ ──────► │ Video    │               │
│  │ Audio    │         │ Image    │               │
│  └──────────┘         └──────────┘               │
│                                                   │
│  Example prompt:                                  │
│  "Generate a video making the picture of the cat │
│   speak the audio that is included"               │
└──────────────────────────────────────────────────┘
```

| Property | Single-Modal | Multi-Modal |
|----------|-------------|-------------|
| **Input** | One type (text only, or image only) | Mix of text, image, audio, video |
| **Output** | One type | Mix of text, image, audio, video |
| **Example** | GPT-3 (text only) | GPT-4o (text + image + audio) |

### Real-Life Use Case

> **Example: Accessibility Tool**
> A multi-modal model receives an image of a restaurant menu and audio of a user asking "What vegetarian options are available?" The model reads the menu image, understands the audio question, and responds with text listing the vegetarian dishes — combining vision, speech, and language understanding in one interaction.

---

## 6.10 Humans as a Mix of AI

Humans naturally use all levels of AI in daily life:

| Level | Human Analogy |
|-------|--------------|
| **AI (Rule-based)** | "If this happens, then do that" — following explicit rules |
| **Machine Learning** | "I've seen many similar things before, so I can classify this" — pattern recognition from experience |
| **Deep Learning** | "I haven't seen this exact thing, but I've learned similar concepts" — abstract reasoning |
| **Generative AI** | "Based on what I've learned, I can create something new" — creativity |

---

## 6.11 Natural Language Processing (NLP)

NLP enables machines to understand, interpret, and generate human language.

| NLP Task | Description | AWS Service |
|----------|-------------|-------------|
| **Sentiment Analysis** | Determine if text is positive, negative, or neutral | Amazon Comprehend |
| **Named Entity Recognition** | Extract names, dates, locations from text | Amazon Comprehend |
| **Translation** | Convert text between languages | Amazon Translate |
| **Speech-to-Text** | Convert audio to written text | Amazon Transcribe |
| **Text-to-Speech** | Convert written text to audio | Amazon Polly |
| **Text Summarization** | Condense long text into key points | Amazon Bedrock |

### Sample Code: Sentiment Analysis with Amazon Comprehend

```python
import boto3

comprehend = boto3.client('comprehend', region_name='us-east-1')

text = "I absolutely love this product! It exceeded all my expectations."

response = comprehend.detect_sentiment(
    Text=text,
    LanguageCode='en'
)

print(f"Sentiment: {response['Sentiment']}")
print(f"Scores: {response['SentimentScore']}")
```

**Output:**
```
Sentiment: POSITIVE
Scores: {
    'Positive': 0.9987,
    'Negative': 0.0001,
    'Neutral': 0.0008,
    'Mixed': 0.0004
}
```

**Output Explanation:**
- `Sentiment` — The dominant sentiment detected
- `SentimentScore` — Confidence scores for each sentiment category (sum to ~1.0)
- The model is 99.87% confident this text is positive

---

## 6.12 Computer Vision

Computer Vision enables machines to interpret and understand visual information.

| CV Task | Description | AWS Service |
|---------|-------------|-------------|
| **Object Detection** | Identify and locate objects in images | Amazon Rekognition |
| **Facial Recognition** | Identify or verify faces | Amazon Rekognition |
| **Text in Images (OCR)** | Extract text from images/documents | Amazon Textract |
| **Image Classification** | Categorize images into classes | Amazon Rekognition |
| **Video Analysis** | Analyze video content frame by frame | Amazon Rekognition Video |

### Step-by-Step: Try Amazon Rekognition (via Console UI)

1. **Navigate to Amazon Rekognition**
   - Go to [https://console.aws.amazon.com](https://console.aws.amazon.com)
   - Search for **"Rekognition"** → Click **Amazon Rekognition**

2. **Try Object Detection Demo**
   - Click **"Object and scene detection"** in the left sidebar
   - Upload an image or use a sample image
   - Click **"Analyze"**
   - View detected objects with confidence scores

3. **Try Facial Analysis**
   - Click **"Facial analysis"** in the left sidebar
   - Upload a photo with faces
   - View detected attributes: age range, emotions, glasses, etc.

4. **Try Text Detection**
   - Click **"Text in image"** in the left sidebar
   - Upload an image containing text (sign, document, etc.)
   - View extracted text with bounding boxes

---

## 6.13 Machine Learning Inferencing

Inferencing is when a trained model makes predictions on new data.

### Inference Types

| Type | Description | Speed vs. Accuracy | Example |
|------|-------------|-------------------|---------|
| **Real-Time** | Decisions made quickly as data arrives | Speed preferred over perfect accuracy | Chatbots, fraud detection |
| **Batch** | Large amount of data analyzed all at once | Accuracy preferred, speed not critical | Data analysis, report generation |

```
Real-Time Inference:              Batch Inference:
┌──────┐  prompt  ┌───────┐      ┌──────┐  dataset  ┌───────┐
│ User │────────>│ Model │      │ User │─────────>│ Model │
│      │<────────│       │      │      │          │       │
└──────┘ response └───────┘      │      │<─────────│       │
         (immediate)             └──────┘  results  └───────┘
                                          (async)
```

### Inferencing at the Edge

Edge devices have less computing power but are close to where data is generated, often with limited internet.

| Model Type | Location | Characteristics |
|-----------|----------|----------------|
| **SLM** (Small Language Model) | Edge device (e.g., Raspberry Pi) | Very low latency, low compute, offline capability, local inference |
| **LLM** (Large Language Model) | Remote server | More powerful, higher latency, must be online |

```
┌──────────────┐                    ┌──────────────┐
│ Raspberry Pi │   API calls over   │ Remote Server│
│              │   Internet         │              │
│ Small        │──────────────────>│ Large        │
│ Language     │<──────────────────│ Language     │
│ Model (SLM)  │                    │ Model (LLM)  │
│              │                    │              │
│ Local, fast  │                    │ Powerful,    │
│ Offline OK   │                    │ online only  │
└──────────────┘                    └──────────────┘
```

---

## 6.14 Phases of a Machine Learning Project

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Business │──>│ ML Problem│──>│ Data     │──>│ Feature  │
│ Problem  │   │ Framing  │   │ Collection│   │ Engineer.│
└──────────┘   └──────────┘   │ & Prep   │   └────┬─────┘
                               └──────────┘        │
                                                    ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Monitor  │<──│ Deploy & │<──│ Model    │<──│ Model    │
│ & Debug  │   │ Test     │   │ Evaluation│   │ Training │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
     │                              │
     │    Are business goals met?   │
     │    No → Add new data,        │
     │         retrain              │
     └──────────────────────────────┘
```

| Phase | What Happens | Who |
|-------|-------------|-----|
| **Define Business Goals** | Define value, budget, success criteria, KPIs | Stakeholders |
| **ML Problem Framing** | Convert business problem to ML problem; determine if ML is appropriate | Data scientists, ML architects, SMEs |
| **Data Processing** | Collect, integrate, preprocess, visualize data | Data engineers |
| **Feature Engineering** | Create, transform, extract variables from data | Data scientists |
| **Model Development** | Train, tune hyperparameters, evaluate (iterative) | ML engineers |
| **Deployment & Testing** | Deploy model, test in production | ML engineers, DevOps |
| **Monitoring & Debugging** | Track performance, retrain if needed | ML engineers |

> **Key Exam Point:** This is an iterative process. If business goals aren't met, add new data (data augmentation), add new features (feature augmentation), and retrain.

---

## 6.15 Hyperparameter Tuning

**Hyperparameters** are settings that define the model structure and learning process. They are set **before** training begins (unlike model parameters which are learned during training).

### Important Hyperparameters

| Hyperparameter | What It Controls | Trade-off |
|---------------|-----------------|-----------|
| **Learning Rate** | How large/small the steps are when updating model weights | High = faster convergence but risks overshooting; Low = more precise but slower |
| **Batch Size** | Number of training examples used per weight update | Smaller = more stable learning but slower; Larger = faster but less stable |
| **Number of Epochs** | How many times the model iterates over the entire dataset | Too few = underfitting; Too many = overfitting |
| **Regularization** | Balance between simple and complex model | Increase to reduce overfitting |

### Hyperparameter Tuning Methods

| Method | Description |
|--------|-------------|
| **Grid Search** | Try every combination of hyperparameter values |
| **Random Search** | Randomly sample hyperparameter combinations |
| **SageMaker AMT** | Automatic Model Tuning — AWS service that automatically finds optimal hyperparameters |

> SageMaker AMT automatically chooses hyperparameter ranges, search strategy, maximum runtime, and early stop conditions — saving time and money.

---

## 6.16 Preventing Overfitting

Overfitting occurs when the model gives good predictions for training data but not for new data.

### Causes

| Cause | Description |
|-------|-------------|
| **Too little training data** | Doesn't represent all possible input values |
| **Training too long** | Model trains too long on a single sample set |
| **Model too complex** | Learns from "noise" within the training data |

### Prevention Strategies

| Strategy | Description |
|----------|-------------|
| **Increase training data** | More diverse data reduces memorization |
| **Early stopping** | Stop training when validation performance stops improving |
| **Data augmentation** | Increase diversity in the dataset (rotate images, add noise) |
| **Adjust hyperparameters** | Tune regularization, learning rate, etc. (but you can't "add" hyperparameters) |
| **Ensembling** | Combine multiple models to get more accurate results |

---

## 6.17 When is Machine Learning NOT Appropriate?

ML is not always the right solution:

| Scenario | Why ML is Wrong | Better Approach |
|----------|----------------|----------------|
| **Deterministic problems** | Solution can be computed exactly | Write code adapted to the problem |
| **Simple calculations** | "What is the probability of drawing a blue card from a deck of 5 red, 3 blue, 2 yellow?" | Answer: 3/10 — no ML needed |
| **Small, static datasets** | Not enough data to learn patterns | Rule-based systems or manual analysis |
| **Explainability required** | ML models can be "black boxes" | Use interpretable algorithms or rule-based systems |

> **Key Exam Point:** For deterministic problems where the solution can be computed, it is better to write computer code. ML gives approximations, not exact answers. Even LLMs with reasoning capabilities are not perfect for mathematical computations.

---

## Module 6 Summary

| Concept | Key Takeaway |
|---------|-------------|
| AI vs ML | AI includes rule-based systems (MYCIN); ML is a subset that learns from data |
| AI Components | Data Layer → ML Framework → Model → Application |
| Training Data | Labeled vs. unlabeled; structured (tabular, time series) vs. unstructured (text, images) |
| Supervised Learning | Labeled data → Regression (predict numbers) or Classification (predict categories) |
| Unsupervised Learning | Unlabeled data → Clustering, Association Rules, Anomaly Detection |
| Reinforcement Learning | Agent learns via rewards/penalties; RLHF adds human feedback |
| Semi-Supervised | Small labeled + large unlabeled data; pseudo-labeling |
| Self-Supervised | Model generates its own labels from unlabeled data (how GPT/BERT are pre-trained) |
| Feature Engineering | Extract, select, and transform raw data into meaningful features |
| EDA | Visualize data, correlation matrices to understand feature relationships |
| Train/Validation/Test | 60-80% / 10-20% / 10-20%; test set never used during training |
| Bias and Variance | High bias = underfitting; High variance = overfitting; Goal = low both |
| Confusion Matrix | TP, FP, TN, FN → Precision, Recall, F1, Accuracy |
| AUC-ROC | 0-1 score comparing true positive vs false positive rates across thresholds |
| Regression Metrics | MAE, MAPE, RMSE (error measures); R-squared (variance explained) |
| ML Terms | GPT, BERT, RNN, ResNet, SVM, WaveNet, GAN, XGBoost |
| Deep Learning | Neural networks with multiple hidden layers; requires GPU |
| Transformer Model | Processes sentences as a whole; architecture behind LLMs (GPT, BERT) |
| Multi-Modal Models | Process and generate multiple content types (text + image + audio) |
| Inferencing | Real-time (fast, chatbots) vs. Batch (accurate, analysis) vs. Edge (local, offline) |
| ML Project Phases | Business Problem → ML Framing → Data → Features → Train → Evaluate → Deploy → Monitor |
| Hyperparameter Tuning | Learning rate, batch size, epochs, regularization; use SageMaker AMT |
| Preventing Overfitting | More data, early stopping, data augmentation, ensembling |
| When NOT to use ML | Deterministic problems, simple calculations — use code instead |

---

*Previous: [Module 5 — Amazon Q](module-05-amazon-q.md)*
*Next: [Module 7 — AWS Managed AI Services](module-07-aws-managed-ai-services.md)*
