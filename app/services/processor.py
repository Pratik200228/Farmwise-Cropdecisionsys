import json
import pandas as pd

def process_env_data():
    with open("data/raw/latest_env_data.json", "r") as f:
        raw_data = json.load(f)
    
    # Extracting the actual parameter values from NASA's format
    features = raw_data['properties']['parameter']
    df = pd.DataFrame(features)
    
    # Calculate averages for the AI Agent to read
    summary = {
        "avg_temp": df['T2M'].mean(),
        "avg_humidity": df['RH2M'].mean(),
        "total_rainfall": df['PRECTOTCORR'].sum()
    }
    
    with open("data/processed/current_features.json", "w") as f:
        json.dump(summary, f)
    
    print("Data Processed: Features ready for the AI Agent.")

if __name__ == "__main__":
    process_env_data()
