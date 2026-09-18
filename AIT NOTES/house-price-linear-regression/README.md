# House Price Prediction using Linear Regression

This Assignment 1 project predicts a continuous house-price value using four input features: area, bedrooms, bathrooms, and house age.

## Included assignment requirements

- Data loading, `head()`, `tail()`, shape, columns, `info()`, `describe()`, missing-value and duplicate checks
- EDA charts: Area vs Price and a correlation heatmap
- Feature (`X`) and target (`y`) selection
- Cleaning of missing and duplicate rows
- 80% training / 20% testing split
- Linear Regression training, predictions, actual-vs-predicted comparison
- MAE, MSE, RMSE, and R² Score metrics
- Pickle model saving and unseen-data prediction
- Streamlit interface for interactive testing

## Setup and run

```powershell
cd "D:\AIT NOTES\house-price-linear-regression"
pip install -r requirements.txt
python main.py
streamlit run app.py
```

Run `python main.py` once before launching the Streamlit UI. This creates `house_price_model.pkl`, `actual_vs_predicted.csv`, and the `plots` folder.

## Project structure

```text
house-price-linear-regression/
├── dataset.csv
├── main.py
├── app.py
├── requirements.txt
├── house_price_model.pkl       # generated after training
├── actual_vs_predicted.csv     # generated after training
└── plots/                      # generated after training
```
