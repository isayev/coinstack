
import requests
import json
import sys

def verify_live_api():
    try:
        # Search for Coson coin
        url = "http://localhost:8000/api/v2/coins"
        params = {"issuing_authority": "Coson"}
        
        print(f"Requesting: {url} with params {params}")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error: Status {response.status_code}")
            print(response.text)
            return

        data = response.json()
        items = data.get("items", [])
        
        if not items:
            print("No Coson coin found in API response.")
            return

        coin = items[0]
        print(f"Found Coin ID: {coin.get('id')}")
        
        # Check flat fields
        print(f"Flat mint_year_start: {coin.get('mint_year_start')}")
        print(f"Flat reign_start: {coin.get('reign_start')}")
        
        # Check nested attribution
        attribution = coin.get("attribution")
        if attribution:
            print("Attribution Object Found:")
            print(json.dumps(attribution, indent=2))
            
            year_start = attribution.get("year_start")
            print(f"Attribution year_start: {year_start} (Type: {type(year_start)})")
        else:
            print("Attribution Object MISSING in response!")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_live_api()
