"""Streamlit UI for testing the trained house-price model."""
from pathlib import Path
import pickle

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "house_price_model.pkl"
CHART_PATH = BASE_DIR / "plots" / "actual_vs_predicted.png"


@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as file:
        return pickle.load(file)


st.set_page_config(page_title="House Price Prediction", page_icon="🏠", layout="centered")
st.title("🏠 House Price Prediction")
st.write("Enter the house details below to predict the price.")

if not MODEL_PATH.exists():
    st.error("No trained model found. In a terminal, run: `python main.py`")
    st.stop()

with st.form("house_prediction"):
    area = st.number_input("Area (Square Feet)", min_value=100, max_value=10000, value=2000, step=100)
    bedrooms = st.number_input("Number of Bedrooms", min_value=1, max_value=20, value=3, step=1)
    bathrooms = st.number_input("Number of Bathrooms", min_value=1, max_value=20, value=2, step=1)
    age = st.number_input("House Age (Years)", min_value=0, max_value=100, value=5, step=1)
    predict = st.form_submit_button("Predict House Price", type="primary")

if predict:
    input_data = pd.DataFrame({
        "area": [area], "bedrooms": [bedrooms], "bathrooms": [bathrooms], "age": [age]
    })
    prediction = load_model().predict(input_data)[0]
    st.success(f"Predicted House Price: ₹{prediction:,.2f}")
    st.dataframe(input_data, use_container_width=True, hide_index=True)

if CHART_PATH.exists():
    with st.expander("View model evaluation chart"):
        st.image(str(CHART_PATH), caption="Actual vs Predicted test prices")

st.markdown("---")
st.write("Machine Learning Model: Linear Regression")
