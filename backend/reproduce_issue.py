import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_lookup(ref):
    print(f"\n--- Testing: '{ref}' ---")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending request...")
            response = await client.post(
                f"{BASE_URL}/api/catalog/lookup",
                json={"reference": ref, "context": {}}
            )
            print(f"Response Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"API Status: {data.get('status')}")
                print(f"Error Message: {data.get('error_message')}")
                if data.get('payload'):
                    print(f"Payload: {data.get('payload').get('authority')} / {data.get('payload').get('mint')}")
                candidates = data.get('candidates')
                if candidates:
                    print(f"Candidates Found: {len(candidates)}")
                    for c in candidates[:3]:
                        print(f" - {c.get('external_id')} ({c.get('score')})")
            else:
                print(f"Error Body: {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

async def main():
    # Test cases reported by user
    await test_lookup("Crawford 335/1c")
    await test_lookup("Crawford:335/1c") 
    
    # Control case
    await test_lookup("Cr. 335/1")

if __name__ == "__main__":
    asyncio.run(main())
