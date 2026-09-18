"""Assignment 2: TensorFlow CNN trainer for Cat vs Dog classification."""
from pathlib import Path

import matplotlib.pyplot as plt
import tensorflow as tf

BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
MODEL_PATH = BASE_DIR / "image_classifier.keras"
CHARTS_DIR = BASE_DIR / "charts"
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 16
EPOCHS = 10


def main():
    cats_dir, dogs_dir = DATASET_DIR / "cats", DATASET_DIR / "dogs"
    if not cats_dir.exists() or not dogs_dir.exists():
        raise FileNotFoundError(
            "Create dataset/cats and dataset/dogs, then add real cat and dog images before training."
        )
    CHARTS_DIR.mkdir(exist_ok=True)
    train_data = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR, validation_split=0.20, subset="training", seed=42,
        image_size=IMAGE_SIZE, batch_size=BATCH_SIZE, label_mode="binary"
    )
    validation_data = tf.keras.utils.image_dataset_from_directory(
        DATASET_DIR, validation_split=0.20, subset="validation", seed=42,
        image_size=IMAGE_SIZE, batch_size=BATCH_SIZE, label_mode="binary"
    )
    print("Class order:", train_data.class_names)  # Expected: ['cats', 'dogs']

    autotune = tf.data.AUTOTUNE
    train_data = train_data.cache().shuffle(500).prefetch(autotune)
    validation_data = validation_data.cache().prefetch(autotune)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(*IMAGE_SIZE, 3)),
        tf.keras.layers.Rescaling(1.0 / 255),
        tf.keras.layers.Conv2D(32, 3, activation="relu"),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(64, 3, activation="relu"),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Conv2D(128, 3, activation="relu"),
        tf.keras.layers.MaxPooling2D(),
        tf.keras.layers.Dropout(0.30),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    history = model.fit(train_data, validation_data=validation_data, epochs=EPOCHS)
    loss, accuracy = model.evaluate(validation_data, verbose=0)
    print(f"Validation loss: {loss:.4f}")
    print(f"Validation accuracy: {accuracy:.2%}")
    model.save(MODEL_PATH)

    plt.figure(figsize=(7, 4))
    plt.plot(history.history["accuracy"], label="Training accuracy")
    plt.plot(history.history["val_accuracy"], label="Validation accuracy")
    plt.xlabel("Epoch"); plt.ylabel("Accuracy"); plt.title("CNN Accuracy"); plt.legend(); plt.tight_layout()
    plt.savefig(CHARTS_DIR / "accuracy.png", dpi=150); plt.close()
    plt.figure(figsize=(7, 4))
    plt.plot(history.history["loss"], label="Training loss")
    plt.plot(history.history["val_loss"], label="Validation loss")
    plt.xlabel("Epoch"); plt.ylabel("Loss"); plt.title("CNN Loss"); plt.legend(); plt.tight_layout()
    plt.savefig(CHARTS_DIR / "loss.png", dpi=150); plt.close()
    print(f"Model saved: {MODEL_PATH.name}")


if __name__ == "__main__":
    main()
