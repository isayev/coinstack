import requests
import json
import sys

def test_ocre_search(query):
    print(f"Searching OCRE for: {query}")
    # Try different search strategies
    
    # 1. Fulltext search
    url = "http://numismatics.org/ocre/apis/search"
    params = {
        "q": query,
        "format": "json",
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Response keys:", data.keys())
            # Parse XML/JSON structure (Numismatics.org often returns weird JSON wrapping detailed results)
            # Actually, standard response usually has 'numFound', 'result'
            
            print(json.dumps(data, indent=2)[:500]) # First 500 chars
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "RIC III 712"
    test_ocre_search(query)
