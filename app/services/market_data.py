import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("USDA_API_KEY")
BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"

def fetch_historical_prices(commodity="CORN", state="LOUISIANA"):
    params = {
        "key": API_KEY,
        "commodity_desc": commodity,
        "state_name": state,
        "statisticcat_desc": "PRICE RECEIVED",
        "unit_desc": "$ / BU",  # Dollars per Bushel
        "freq_desc": "MONTHLY",
        "format": "CSV"
    }
    
    print(f"Fetching historical {commodity} prices for {state}...")
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        # Save as CSV for your team's AI training
        file_path = f"data/raw/{commodity.lower()}_prices.csv"
        with open(file_path, "w") as f:
            f.write(response.text)
        return {"status": "success", "path": file_path}
    else:
        return {"status": "error", "code": response.status_code}

if __name__ == "__main__":
    fetch_historical_prices()
