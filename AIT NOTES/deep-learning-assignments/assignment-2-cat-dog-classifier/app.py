"""Streamlit Cat vs Dog image-classification UI."""
from pathlib import Path

import numpy as np
from PIL import Image
import streamlit as st
import tensorflow as tf

MODEL_PATH = Path(__file__).parent / "image_classifier.keras"
IMAGE_SIZE = (128, 128)
st.set_page_config(page_title="Cat vs Dog Classifier", page_icon="🐱")
st.title("🐱🐶 Cat vs Dog Image Classification")
st.write("Upload a JPG, JPEG, or PNG image to classify it.")
if not MODEL_PATH.exists():
    st.error("Model not found. Add images to dataset/cats and dataset/dogs, then run `python train_model.py`.")
    st.stop()

@st.cache_resource
def get_model():
    return tf.keras.models.load_model(MODEL_PATH)

uploaded_file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded image", use_container_width=True)
    resized = image.resize(IMAGE_SIZE)
    array = np.expand_dims(np.asarray(resized, dtype="float32"), axis=0)
    dog_probability = get_model().predict(array, verbose=0)[0][0]
    if dog_probability >= 0.5:
        st.success(f"Predicted Class: Dog 🐶\n\nPrediction Confidence: {dog_probability:.1%}")
    else:
        st.success(f"Predicted Class: Cat 🐱\n\nPrediction Confidence: {1 - dog_probability:.1%}")
