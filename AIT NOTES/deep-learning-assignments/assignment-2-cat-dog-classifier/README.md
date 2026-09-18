# Assignment 2 - Cat vs Dog Image Classification

This project uses a TensorFlow/Keras CNN with convolution, pooling, dropout, and sigmoid output layers.

## Dataset setup

Create the following folders and add real images:

```text
dataset/
  cats/   # cat images
  dogs/   # dog images
```

The project dataset has been populated with 655 cat images and 745 dog images from the public **Cats and Dogs sample** dataset. The downloaded archive and extracted source are retained in `D:\AIT NOTES\deep-learning-assignments\downloads`.

## Train and run

```powershell
python train_model.py
streamlit run app.py
```

Training uses an automatic 80/20 train/validation split, evaluates validation accuracy and loss, saves `image_classifier.keras`, and saves accuracy/loss charts. The Streamlit UI accepts JPG, JPEG, and PNG uploads.
