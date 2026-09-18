"""Train a TensorFlow Deep Learning model to predict student pass/fail."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "student_data.csv"
MODEL_PATH = BASE_DIR / "student_pass_fail_model.keras"
CHARTS_DIR = BASE_DIR / "charts"
FEATURES = ["study_hours", "attendance", "previous_marks", "assignments_completed"]
EPOCHS = 100


def main():
    np.random.seed(42)
    tf.keras.utils.set_random_seed(42)
    CHARTS_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    print("\nFirst five rows:\n", df.head())
    print("\nDataset shape:", df.shape)
    print("\nDataset information:")
    df.info()
    print("\nSummary statistics:\n", df.describe())
    print("\nMissing values:\n", df.isnull().sum())
    print("\nDuplicate rows:", df.duplicated().sum())
    df = df.dropna().drop_duplicates()

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(6, 4))
    sns.countplot(data=df, x="pass_status", hue="pass_status", legend=False, palette="Set2")
    plt.title("Student Pass/Fail Distribution")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "pass_fail_distribution.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 5))
    sns.scatterplot(data=df, x="study_hours", y="previous_marks", hue="pass_status", s=85)
    plt.title("Study Hours and Previous Marks")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "study_hours_vs_marks.png", dpi=150)
    plt.close()

    X = df[FEATURES].astype("float32")
    # Binary target: Pass = 1, Fail = 0.
    y = (df["pass_status"] == "Pass").astype("int32")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Normalization is included inside the Keras model, so the saved model
    # can receive the original input values directly from the Streamlit UI.
    normalizer = tf.keras.layers.Normalization()
    normalizer.adapt(np.asarray(X_train))
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(len(FEATURES),)),
        normalizer,
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(16, activation="relu"),
        tf.keras.layers.Dense(8, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    # An epoch is one complete pass through all training records.
    history = model.fit(
        X_train, y_train,
        validation_split=0.20,
        epochs=EPOCHS,
        batch_size=8,
        verbose=0,
    )

    probabilities = model.predict(X_test, verbose=0).flatten()
    predicted_labels = (probabilities >= 0.5).astype(int)
    actual_labels = y_test.to_numpy()
    actual_names = np.where(actual_labels == 1, "Pass", "Fail")
    predicted_names = np.where(predicted_labels == 1, "Pass", "Fail")
    accuracy = accuracy_score(actual_labels, predicted_labels)
    comparison = pd.DataFrame({
        "Actual Result": actual_names,
        "Predicted Result": predicted_names,
        "Pass Probability": probabilities,
    })
    comparison.to_csv(BASE_DIR / "actual_vs_predicted.csv", index=False)

    print("\nTrain shape:", X_train.shape, "Test shape:", X_test.shape)
    print("\nActual vs Predicted:\n", comparison)
    print(f"\nTest Accuracy: {accuracy:.2%}")
    print("\nClassification report:\n", classification_report(actual_labels, predicted_labels, zero_division=0))

    matrix = confusion_matrix(actual_labels, predicted_labels, labels=[0, 1])
    display = ConfusionMatrixDisplay(matrix, display_labels=["Fail", "Pass"])
    display.plot(cmap="Blues")
    plt.title("Student Pass/Fail Confusion Matrix")
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "confusion_matrix.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.plot(history.history["loss"], label="Training loss")
    plt.plot(history.history["val_loss"], label="Validation loss")
    plt.xlabel("Epoch")
    plt.ylabel("Binary cross-entropy loss")
    plt.title("Training Loss by Epoch")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "training_loss.png", dpi=150)
    plt.close()

    model.save(MODEL_PATH)
    with open(BASE_DIR / "model_metrics.txt", "w", encoding="utf-8") as file:
        file.write(f"Test Accuracy: {accuracy:.2%}\n")
        file.write(f"Epochs: {EPOCHS}\n")
        file.write("Architecture: Input -> Normalization -> Dense(32) -> Dense(16) -> Dense(8) -> Sigmoid Output\n")

    sample_student = np.array([[6.0, 85, 75, 8]], dtype="float32")
    sample_probability = model.predict(sample_student, verbose=0)[0][0]
    print(f"\nSample pass probability: {sample_probability:.2%}")
    print("Sample result:", "Pass" if sample_probability >= 0.5 else "Fail")
    print(f"TensorFlow model saved to: {MODEL_PATH.name}")


if __name__ == "__main__":
    main()
