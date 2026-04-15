import requests
import json
import os
from datetime import datetime, timedelta
from app.core import config

def fetch_environmental_data():
    # Set a 7-day window for recent data
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

    params = {
        "parameters": config.PARAMETERS,
        "community": config.COMMUNITY,
        "longitude": config.LON,
        "latitude": config.LAT,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }

    print(f"Fetching data from NASA for {start_date} to {end_date}...")
    response = requests.get(config.NASA_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        file_path = "data/raw/latest_env_data.json"
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        
        return {"status": "success", "file": file_path}
    else:
        return {"status": "error", "message": response.text}

if __name__ == "__main__":
    result = fetch_environmental_data()
    print(result)
