import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "corn_prices.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "corn_price_model.pkl")

MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}

def clean_data(df):
    """Filter out protected flags and invalid data."""
    # Ensure Value is treated as string first to strip out non-numerics
    df["Value"] = df["Value"].astype(str).str.strip()
    
    # Keep only rows that are not missing/suppressed
    valid_df = df[~df["Value"].isin(["(NA)", "(D)", ""])]
    valid_df = valid_df.copy()
    
    # Convert Value to float
    valid_df["Value"] = pd.to_numeric(valid_df["Value"], errors="coerce")
    
    # Map months
    valid_df["month"] = valid_df["reference_period_desc"].map(MONTH_MAP)
    
    # Drop where conversion failed
    valid_df.dropna(subset=["Value", "month", "year"], inplace=True)
    
    # Format year and month as integers
    valid_df["year"] = valid_df["year"].astype(int)
    valid_df["month"] = valid_df["month"].astype(int)
    
    return valid_df

def main():
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH, dtype=str)
    
    print(f"Raw data shape: {df.shape}")
    clean_df = clean_data(df)
    print(f"Clean data shape: {clean_df.shape}")
    
    if clean_df.empty:
        print("Error: No valid data found for training!")
        return

    # Prepare features and target
    X = clean_df[["year", "month"]]
    y = clean_df["Value"]
    
    # 80/20 train-test split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print("-" * 30)
    print("Training Complete!")
    print(f"Mean Absolute Error: ${mae:.2f} per BU")
    print(f"R-squared Score: {r2:.4f}")
    print("-" * 30)

    # Ensure model directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Serialize model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved successfully to: {MODEL_PATH}")

if __name__ == "__main__":
    main()
