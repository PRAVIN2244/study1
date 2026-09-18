"""Assignment 1: TensorFlow ANN for Student Pass/Fail prediction."""
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).parent
FEATURES = ["study_hours", "attendance", "previous_marks"]
MODEL_PATH = BASE_DIR / "student_pass_fail_model.keras"

tf.keras.utils.set_random_seed(42)
df = pd.read_csv(BASE_DIR / "student_data.csv")
print("First records:\n", df.head())
print("Shape:", df.shape)
print("Missing values:\n", df.isnull().sum())

df = df.dropna().drop_duplicates()
X = df[FEATURES].astype("float32")
y = df["result"].astype("float32")  # 0 = Fail, 1 = Pass
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

normalizer = tf.keras.layers.Normalization()
normalizer.adapt(np.asarray(X_train))
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(3,)),
    normalizer,
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(8, activation="relu"),
    tf.keras.layers.Dense(1, activation="sigmoid"),
])
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.fit(X_train, y_train, epochs=100, batch_size=8, validation_split=0.20, verbose=0)

probabilities = model.predict(X_test, verbose=0).flatten()
predictions = (probabilities >= 0.5).astype(int)
accuracy = accuracy_score(y_test, predictions)
print(f"Test accuracy: {accuracy:.2%}")
print(classification_report(y_test, predictions, target_names=["Fail", "Pass"], zero_division=0))
model.save(MODEL_PATH)
pd.DataFrame({"Actual": y_test.to_numpy(), "Predicted": predictions, "Pass Probability": probabilities}).to_csv(BASE_DIR / "actual_vs_predicted.csv", index=False)
print(f"Model saved: {MODEL_PATH.name}")
