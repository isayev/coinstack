
import requests
import json
import sys

def verify_coson_live():
    try:
        # Fetch simple list
        url = "http://localhost:8000/api/v2/coins"
        print(f"Requesting: {url} (getting all)")
        response = requests.get(url, params={"per_page": 100}) # Ensure we get ID 2
        
        if response.status_code != 200:
            print(f"Error: Status {response.status_code}")
            return

        data = response.json()
        items = data.get("items", [])
        
        coson = None
        for c in items:
            if c.get("id") == 2:
                coson = c
                break
        
        if not coson:
            print("Coson (ID 2) NOT found in list!")
            # Try finding by name?
            for c in items:
                print(f"ID: {c.get('id')}, Issuer: {c.get('issuing_authority')}")
            return

        print(f"Found Coson (ID 2):")
        print(json.dumps(coson, indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    verify_coson_live()
