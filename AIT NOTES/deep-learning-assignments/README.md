# Deep Learning Assignments

This folder contains two independent TensorFlow/Keras and Streamlit projects.

## Assignment 1 - Student Pass or Fail

`assignment-1-student-pass-fail/` contains a complete ANN project with sample data, training code, a saved `.keras` model after training, and Streamlit UI.

```powershell
cd "D:\AIT NOTES\deep-learning-assignments\assignment-1-student-pass-fail"
python train_model.py
streamlit run app.py
```

## Assignment 2 - Cat vs Dog Image Classification

`assignment-2-cat-dog-classifier/` contains a CNN trainer and Streamlit image-upload UI. Put real images into the required folders before training:

```text
dataset/
  cats/   # cat .jpg/.jpeg/.png images
  dogs/   # dog .jpg/.jpeg/.png images
```

Then run:

```powershell
cd "D:\AIT NOTES\deep-learning-assignments\assignment-2-cat-dog-classifier"
python train_model.py
streamlit run app.py
```

Install all shared packages once from this root folder:

```powershell
python -m pip install -r requirements.txt
```
