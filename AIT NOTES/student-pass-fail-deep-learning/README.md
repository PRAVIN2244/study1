# Student Pass/Fail Prediction - Deep Learning

This project predicts whether a student is likely to **Pass** or **Fail** using a TensorFlow/Keras multi-layer neural network.

## Model and features

The project uses TensorFlow/Keras with three hidden layers: **32 -> 16 -> 8**, ReLU activation, Adam optimizer, binary cross-entropy loss, and **100 epochs**. The model uses:

- Daily study hours
- Attendance percentage
- Previous marks percentage
- Number of assignments completed

## Run the project

```powershell
cd "D:\AIT NOTES\student-pass-fail-deep-learning"
python -m pip install -r requirements.txt
python main.py
streamlit run app.py
```

Run `main.py` before the Streamlit app. It creates `student_pass_fail_model.keras`, evaluation metrics, actual-vs-predicted CSV, and charts.

## Project files

```text
student-pass-fail-deep-learning/
├── student_data.csv
├── main.py
├── app.py
├── requirements.txt
├── student_pass_fail_model.keras # generated after training
├── actual_vs_predicted.csv      # generated after training
├── model_metrics.txt            # generated after training
└── charts/                      # generated after training
```

## Note

The sample dataset is for learning only. It is deliberately small and synthetic, so its results should not be used for real academic decisions.
