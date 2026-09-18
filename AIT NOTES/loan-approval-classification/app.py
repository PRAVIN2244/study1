"""Streamlit interface for the saved Loan Approval prediction model."""
from pathlib import Path
import pickle

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "loan_approval_model.pkl"
CHARTS_DIR = BASE_DIR / "charts"

st.set_page_config(page_title="Loan Approval Predictor", page_icon="🏦", layout="wide")


@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as file:
        return pickle.load(file)


st.title("🏦 Loan Approval Predictor")
st.caption("Assignment 2 · Logistic Regression Classification")
st.info("Educational use only — this prediction must not be used for real lending decisions.")

if not MODEL_PATH.exists():
    st.error("Model file not found. Run `python main.py` before opening this application.")
    st.stop()

left, right = st.columns(2)
with left:
    gender = st.selectbox("Gender", ["Male", "Female"])
    married = st.selectbox("Married", ["Yes", "No"])
    dependents = st.selectbox("Dependents", ["0", "1", "2", "3+"])
    education = st.selectbox("Education", ["Graduate", "Not Graduate"])
    self_employed = st.selectbox("Self Employed", ["No", "Yes"])
    property_area = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])

with right:
    applicant_income = st.number_input("Applicant Income (INR)", min_value=0, value=50000, step=1000)
    coapplicant_income = st.number_input("Coapplicant Income (INR)", min_value=0, value=0, step=1000)
    loan_amount = st.number_input("Loan Amount (thousand INR)", min_value=1, value=200, step=10)
    loan_term = st.selectbox("Loan Amount Term (months)", [120, 180, 240, 300, 360, 480], index=4)
    credit_history = st.selectbox("Credit History", [1.0, 0.0], format_func=lambda value: "Good (1)" if value == 1 else "Poor (0)")

if st.button("Check Loan Approval", type="primary", use_container_width=True):
    new_application = pd.DataFrame({
        "Gender": [gender], "Married": [married], "Dependents": [dependents],
        "Education": [education], "Self_Employed": [self_employed],
        "ApplicantIncome": [applicant_income], "CoapplicantIncome": [coapplicant_income],
        "LoanAmount": [loan_amount], "Loan_Amount_Term": [loan_term],
        "Credit_History": [credit_history], "Property_Area": [property_area],
    })
    model = load_model()
    prediction = model.predict(new_application)[0]
    approval_probability = model.predict_proba(new_application)[0][list(model.classes_).index("Y")]
    if prediction == "Y":
        st.success(f"Likely Approved · Approval probability: {approval_probability:.1%}")
    else:
        st.error(f"Likely Rejected · Approval probability: {approval_probability:.1%}")
    with st.expander("View submitted application"):
        st.dataframe(new_application, hide_index=True, use_container_width=True)

if (CHARTS_DIR / "confusion_matrix.png").exists():
    st.markdown("---")
    st.subheader("Model evaluation")
    st.image(str(CHARTS_DIR / "confusion_matrix.png"), caption="Confusion Matrix")

st.markdown("---")
st.caption("Machine Learning Model: Logistic Regression · Classification")
