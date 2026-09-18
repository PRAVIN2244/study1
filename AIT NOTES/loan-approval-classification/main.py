"""Train and evaluate a Logistic Regression loan-approval classifier."""

from pathlib import Path
import pickle

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# File locations. The script and dataset are stored in the same folder.
PROJECT_FOLDER = Path(__file__).parent
DATA_FILE = PROJECT_FOLDER / "loan_approval_dataset.csv"
MODEL_FILE = PROJECT_FOLDER / "loan_approval_model.pkl"
METRICS_FILE = PROJECT_FOLDER / "model_metrics.txt"
COMPARISON_FILE = PROJECT_FOLDER / "actual_vs_predicted.csv"
CHARTS_FOLDER = PROJECT_FOLDER / "charts"
CHARTS_FOLDER.mkdir(exist_ok=True)


# Load the historical loan-application data.
df = pd.read_csv(DATA_FILE)

print("\n--- First Five Records ---")
print(df.head())

print("\n--- Dataset Shape ---")
print(df.shape)
# (30, 13) means 30 records and 13 columns in the sample dataset.

print("\n--- Dataset Information ---")
df.info()

print("\n--- Numerical Summary ---")
print(df.describe())

print("\n--- Missing Values ---")
print(df.isnull().sum())

print("\n--- Duplicate Rows ---")
print(df.duplicated().sum())


# Remove duplicate records and the identifier column.
df = df.drop_duplicates()
df = df.drop(columns=["Loan_ID"])


# Create EDA charts and save them in the charts folder.
plt.figure(figsize=(6, 4))
sns.countplot(data=df, x="Loan_Status")
plt.title("Loan Status Distribution")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "loan_status_distribution.png")
plt.close()

plt.figure(figsize=(7, 4))
sns.histplot(data=df, x="ApplicantIncome", kde=True)
plt.title("Applicant Income Distribution")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "applicant_income_distribution.png")
plt.close()

plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="LoanAmount")
plt.title("Loan Amount Box Plot")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "loan_amount_boxplot.png")
plt.close()

plt.figure(figsize=(7, 4))
sns.countplot(data=df, x="Credit_History", hue="Loan_Status")
plt.title("Credit History vs Loan Status")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "credit_history_vs_status.png")
plt.close()

plt.figure(figsize=(8, 6))
sns.heatmap(df.select_dtypes(include="number").corr(), annot=True, cmap="Blues", fmt=".2f")
plt.title("Numerical Feature Correlation Heatmap")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "correlation_heatmap.png")
plt.close()


# X contains all input features. y contains the target to predict.
X = df.drop(columns=["Loan_Status"])
y = df["Loan_Status"]


# Separate numeric columns from text/categorical columns.
numerical_columns = X.select_dtypes(include=["int64", "float64"]).columns
categorical_columns = X.select_dtypes(include=["object", "str"]).columns


# Numeric missing values will use the median. Text missing values use the most common value.
numeric_pipeline = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
])

categorical_pipeline = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])


# Apply the appropriate pipeline to each set of columns.
preprocessor = ColumnTransformer(transformers=[
    ("numbers", numeric_pipeline, numerical_columns),
    ("categories", categorical_pipeline, categorical_columns),
])


# Use 80% of records for training and 20% for testing.
# stratify=y keeps Approved/Rejected proportions similar in both sets.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\n--- Train/Test Shapes ---")
print("X_train:", X_train.shape)
print("X_test :", X_test.shape)
print("y_train:", y_train.shape)
print("y_test :", y_test.shape)


# The pipeline first preprocesses data and then trains Logistic Regression.
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000)),
])

model.fit(X_train, y_train)


# Predict loan status for the test records.
y_pred = model.predict(X_test)

comparison_df = pd.DataFrame({
    "Actual Loan Status": y_test.to_numpy(),
    "Predicted Loan Status": y_pred,
})

print("\n--- Actual vs Predicted ---")
print(comparison_df)
comparison_df.to_csv(COMPARISON_FILE, index=False)


# Calculate classification metrics. Y is treated as the Approved positive class.
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, pos_label="Y", zero_division=0)
recall = recall_score(y_test, y_pred, pos_label="Y", zero_division=0)
f1 = f1_score(y_test, y_pred, pos_label="Y", zero_division=0)

print("\n--- Model Evaluation ---")
print(f"Accuracy : {accuracy:.2%}")
print(f"Precision: {precision:.2%}")
print(f"Recall   : {recall:.2%}")
print(f"F1 Score : {f1:.2%}")

with open(METRICS_FILE, "w", encoding="utf-8") as file:
    file.write("Loan Approval Logistic Regression - Evaluation Results\n")
    file.write(f"Accuracy: {accuracy:.2%}\n")
    file.write(f"Precision: {precision:.2%}\n")
    file.write(f"Recall: {recall:.2%}\n")
    file.write(f"F1 Score: {f1:.2%}\n")

print("\n--- Classification Report ---")
print(classification_report(y_test, y_pred, zero_division=0))


# Create and save a confusion-matrix chart.
matrix = confusion_matrix(y_test, y_pred, labels=["N", "Y"])
display = ConfusionMatrixDisplay(
    confusion_matrix=matrix,
    display_labels=["Rejected (N)", "Approved (Y)"],
)
display.plot(cmap="Blues")
plt.title("Loan Approval Confusion Matrix")
plt.tight_layout()
plt.savefig(CHARTS_FOLDER / "confusion_matrix.png")
plt.close()


# Predict a new applicant. Column names must match X exactly.
new_application = pd.DataFrame({
    "Gender": ["Male"],
    "Married": ["Yes"],
    "Dependents": ["0"],
    "Education": ["Graduate"],
    "Self_Employed": ["No"],
    "ApplicantIncome": [50000],
    "CoapplicantIncome": [0],
    "LoanAmount": [200],
    "Loan_Amount_Term": [360],
    "Credit_History": [1],
    "Property_Area": ["Urban"],
})

new_prediction = model.predict(new_application)[0]
new_probability = model.predict_proba(new_application)[0]
approved_probability = new_probability[list(model.classes_).index("Y")]

print("\n--- New Application Result ---")
print("Loan Status:", "Approved" if new_prediction == "Y" else "Rejected")
print(f"Approval Probability: {approved_probability:.2%}")


# Save the complete pipeline, including preprocessing and the trained model.
with open(MODEL_FILE, "wb") as file:
    pickle.dump(model, file)

print(f"\nModel saved successfully: {MODEL_FILE.name}")
print(f"Charts saved in folder: {CHARTS_FOLDER.name}")
