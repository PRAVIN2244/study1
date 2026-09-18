"""House Price Prediction using Linear Regression."""
from pathlib import Path
import pickle

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "dataset.csv"
MODEL_PATH = BASE_DIR / "house_price_model.pkl"
PLOTS_DIR = BASE_DIR / "plots"
FEATURES = ["area", "bedrooms", "bathrooms", "age"]


def save_eda_plots(df: pd.DataFrame) -> None:
    """Create charts that show feature relationships and model performance."""
    PLOTS_DIR.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(8, 5))
    plt.scatter(df["area"], df["price"], color="royalblue", s=70)
    plt.xlabel("Area (square feet)")
    plt.ylabel("House price (INR)")
    plt.title("Area vs House Price")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "area_vs_price.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.heatmap(df.corr(numeric_only=True), annot=True, cmap="Blues", fmt=".2f")
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "correlation_heatmap.png", dpi=150)
    plt.close()


def main() -> None:
    # Load and understand the dataset.
    df = pd.read_csv(DATA_PATH)
    print("\nComplete dataset:\n", df)
    print("\nFirst 5 rows:\n", df.head())
    print("\nLast 5 rows:\n", df.tail())
    print("\nShape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nInfo:")
    df.info()
    print("\nDescription:\n", df.describe())
    print("\nMissing values:\n", df.isnull().sum())
    print("\nDuplicate records:", df.duplicated().sum())

    # Clean missing and duplicate records before training.
    df = df.dropna(subset=FEATURES + ["price"]).drop_duplicates()
    save_eda_plots(df)

    # Independent variables (X) and target variable (y).
    X = df[FEATURES]
    y = df["price"]

    # 80% training and 20% testing.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print("\nX_train:", X_train.shape, "X_test:", X_test.shape)
    print("y_train:", y_train.shape, "y_test:", y_test.shape)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    results = pd.DataFrame({
        "Actual Price": y_test.to_numpy(),
        "Predicted Price": y_pred,
    })
    print("\nActual vs Predicted:\n", results)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, y_pred)
    print(f"\nMAE: {mae:,.2f}")
    print(f"MSE: {mse:,.2f}")
    print(f"RMSE: {rmse:,.2f}")
    print(f"R² Score: {r2:.4f}")

    plt.figure(figsize=(7, 5))
    plt.scatter(y_test, y_pred, color="seagreen", s=80)
    low, high = min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())
    plt.plot([low, high], [low, high], "r--", label="Perfect prediction")
    plt.xlabel("Actual price (INR)")
    plt.ylabel("Predicted price (INR)")
    plt.title("Actual vs Predicted House Prices")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "actual_vs_predicted.png", dpi=150)
    plt.close()

    new_house = pd.DataFrame({"area": [5000], "bedrooms": [7], "bathrooms": [7], "age": [1]})
    predicted_price = model.predict(new_house)[0]
    print(f"\nPredicted House Price for sample input (INR): {predicted_price:,.2f}")

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(model, file)
    results.to_csv(BASE_DIR / "actual_vs_predicted.csv", index=False)
    print(f"Model saved to: {MODEL_PATH}")
    print("Conclusion: compare the error metrics and R² score to judge model performance.")


if __name__ == "__main__":
    main()
