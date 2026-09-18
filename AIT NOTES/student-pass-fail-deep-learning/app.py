"""Streamlit UI for the TensorFlow Student Pass/Fail prediction model."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import tensorflow as tf

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "student_pass_fail_model.keras"
CHART_PATH = BASE_DIR / "charts" / "confusion_matrix.png"

st.set_page_config(page_title="Student Result Predictor", page_icon="🎓", layout="centered")


@st.cache_resource
def load_model():
    return tf.keras.models.load_model(MODEL_PATH)


st.title("🎓 Student Pass/Fail Predictor")
st.caption("TensorFlow Deep Learning Model")
st.write("Enter student information to predict whether the student is likely to pass or fail.")

if not MODEL_PATH.exists():
    st.error("TensorFlow model not found. Run `python main.py` first.")
    st.stop()

with st.form("student_form"):
    study_hours = st.slider("Daily Study Hours", 0.0, 15.0, 6.0, 0.5)
    attendance = st.slider("Attendance (%)", 0, 100, 85)
    previous_marks = st.slider("Previous Marks (%)", 0, 100, 75)
    assignments = st.slider("Assignments Completed", 0, 10, 8)
    predict = st.form_submit_button("Predict Result", type="primary", use_container_width=True)

if predict:
    student = pd.DataFrame({
        "study_hours": [study_hours], "attendance": [attendance],
        "previous_marks": [previous_marks], "assignments_completed": [assignments],
    })
    probability = load_model().predict(np.asarray(student, dtype="float32"), verbose=0)[0][0]
    if probability >= 0.5:
        st.success(f"Likely Result: Pass · Pass probability: {probability:.1%}")
    else:
        st.error(f"Likely Result: Fail · Pass probability: {probability:.1%}")
    st.dataframe(student, hide_index=True, use_container_width=True)

if CHART_PATH.exists():
    with st.expander("Model evaluation chart"):
        st.image(str(CHART_PATH), caption="Test-data confusion matrix")

st.markdown("---")
st.caption("Educational model only. Actual results depend on many factors beyond these inputs.")
