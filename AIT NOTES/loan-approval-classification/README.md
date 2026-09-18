# Loan Approval Prediction Using Classification

This project predicts whether a loan application is **Approved (`Y`)** or **Rejected (`N`)**. It uses Logistic Regression, which is suitable because the target has two categories.

> Educational project only. A real lending system also requires fairness testing, explainability, regulatory compliance, and human review.

## Folder structure

```text
loan-approval-classification/
├── loan_approval_dataset.csv  # Historical loan applications
├── main.py                    # Loads, prepares, trains, evaluates, and saves the model
├── requirements.txt           # Libraries required by the project
├── loan_approval_model.pkl    # Created after running main.py
└── charts/                    # Created after running main.py
```

## Step 1: Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Expected prompt change:

```text
# (.venv) PS ...\loan-approval-classification>
```

## Step 2: Install libraries

```powershell
pip install -r requirements.txt
```

Expected final output (versions can differ):

```text
# Successfully installed numpy pandas matplotlib seaborn scikit-learn ...
```

## Step 3: Run the model

```powershell
python main.py
```

Expected output structure:

```text
# --- First Five Records ---
#   Loan_ID  Gender Married  ... Property_Area Loan_Status
# 0   LP001    Male     Yes  ...         Urban           Y
#
# --- Dataset Shape ---
# (30, 13)
#
# --- Missing Values ---
# Loan_ID               0
# Gender                0
# ...
# Loan_Status           0
#
# --- Train/Test Shapes ---
# X_train: (24, 11)
# X_test : (6, 11)
# y_train: (24,)
# y_test : (6,)
#
# --- Model Evaluation ---
# Accuracy : <value varies with the dataset>
# Precision: <value varies with the dataset>
# Recall   : <value varies with the dataset>
# F1 Score : <value varies with the dataset>
#
# --- New Application Result ---
# Loan Status: Approved or Rejected
# Approval Probability: <percentage>
#
# Model saved successfully: loan_approval_model.pkl
# Charts saved in folder: charts
```

The exact model metrics can differ if you replace the sample CSV file with another dataset.

## What every part of `main.py` does

| Code section | Why it exists | What it does |
| --- | --- | --- |
| `pd.read_csv(DATA_FILE)` | The model needs historical data. | Reads the CSV file into a DataFrame. |
| `head()`, `shape`, `info()`, `describe()` | Understand the data before modeling. | Displays records, size, data types, and numerical statistics. |
| `isnull().sum()` | Missing data can cause errors or bias. | Counts missing values per column. |
| `drop_duplicates()` | Duplicate records can distort training. | Keeps only unique loan applications. |
| `drop(columns=["Loan_ID"])` | Loan ID is an identifier, not a meaningful feature. | Prevents the model from learning from a record ID. |
| EDA charts | Visual inspection helps find patterns. | Saves count plots, histograms, box plots, and confusion matrix. |
| `X` | Inputs are needed for predictions. | Holds all feature columns. |
| `y` | The model needs the correct answer while learning. | Holds `Loan_Status`. |
| `SimpleImputer` | Real datasets often have blank values. | Fills numerical blanks with median and text blanks with most frequent value. |
| `OneHotEncoder` | Models work with numbers, not raw text. | Converts values such as `Urban` and `Graduate` into numeric columns. |
| `train_test_split()` | Testing with unseen data is essential. | Creates 80% training data and 20% testing data. |
| `random_state=42` | Repeatable results are useful. | Uses the same random split every run. |
| `stratify=y` | Class balance matters. | Keeps Approved/Rejected proportions similar in both datasets. |
| `LogisticRegression()` | The output has two classes. | Learns the probability of approval. |
| `model.fit()` | Training step. | Learns patterns from training data. |
| `model.predict()` | Make a decision for unseen records. | Returns `Y` or `N`. |
| Accuracy, Precision, Recall, F1 | One score alone is not enough. | Measures different aspects of classification quality. |
| Confusion Matrix | Errors must be understood. | Shows correct and incorrect Approved/Rejected predictions. |
| `pickle.dump()` | Training again is unnecessary for every prediction. | Saves the full trained pipeline in a `.pkl` file. |

## Classification metrics

| Metric | Meaning |
| --- | --- |
| Accuracy | Percentage of all predictions that are correct. |
| Precision | Among predicted approvals, how many were really approved. |
| Recall | Among actual approvals, how many the model found. |
| F1 Score | Balance between Precision and Recall. |
| Confusion Matrix | Counts correct and incorrect Approved/Rejected predictions. |

## Why this is a classification problem

The model predicts one of two labels:

```text
Y → Approved
N → Rejected
```

It does not predict a continuous number such as a house price. Therefore, this is a **binary classification** problem.

## Why Logistic Regression is suitable

Logistic Regression is a standard, simple algorithm for predicting a yes/no result. It estimates the probability of an application being approved, then converts that probability into `Y` or `N`.

## Credit history contribution

Credit history tells whether a customer has handled past credit reliably. It can be a strong indicator because applicants with a good credit history are generally more likely to receive approval. It is still only one input; real lending decisions must not rely on one feature alone.

## Conclusion template

```text
The Logistic Regression model was trained to predict loan approval status.
The model was evaluated using Accuracy, Precision, Recall, F1-Score, and a Confusion Matrix.
Credit history and applicant financial details may influence the prediction.
The sample dataset is small, so the metrics are only for learning purposes.
For a real system, more data, fairness checks, explainability, and human review are required.
```

## Streamlit UI

The project also includes `app.py`, a Streamlit interface for testing a new loan application. It loads the saved `loan_approval_model.pkl` pipeline and shows the predicted Approved/Rejected result with an approval probability.

First train the model, then start the UI:

```powershell
python main.py
streamlit run app.py
```

## Assignment and generated outputs

`assignment.txt` contains the complete Assignment 2 specification shared for this project. Running `main.py` creates `loan_approval_model.pkl`, `model_metrics.txt`, EDA charts, and a confusion-matrix chart. The EDA includes loan-status distribution, applicant-income distribution, loan-amount box plot, credit-history comparison, and a numerical correlation heatmap.
