"""Streamlit UI for Assignment 1."""
from pathlib import Path
import numpy as np
import streamlit as st
import tensorflow as tf

MODEL_PATH = Path(__file__).parent / "student_pass_fail_model.keras"
st.set_page_config(page_title="Student Pass/Fail", page_icon="🎓")
st.title("🎓 Student Pass/Fail Prediction")
st.write("TensorFlow/Keras ANN classification model")
if not MODEL_PATH.exists():
    st.error("Run `python train_model.py` first.")
    st.stop()

@st.cache_resource
def get_model():
    return tf.keras.models.load_model(MODEL_PATH)

hours = st.number_input("Study Hours", 0.0, 24.0, 7.0, 0.5)
attendance = st.slider("Attendance (%)", 0, 100, 85)
marks = st.slider("Previous Marks (%)", 0, 100, 72)
if st.button("Predict Result", type="primary"):
    probability = get_model().predict(np.array([[hours, attendance, marks]], dtype="float32"), verbose=0)[0][0]
    if probability >= 0.5:
        st.success(f"Prediction: PASS · Confidence: {probability:.1%}")
    else:
        st.error(f"Prediction: FAIL · Pass confidence: {probability:.1%}")
