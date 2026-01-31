import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_lookup(ref):
    print(f"\nTesting: '{ref}'")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/catalog/lookup",
                json={"reference": ref, "context": {}}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"Status: {data.get('status')}")
                print(f"Confidence: {data.get('confidence')}")
                if data.get('payload'):
                    print(f"Payload: {data.get('payload').get('authority')} / {data.get('payload').get('mint')}")
                candidates = data.get('candidates')
                if candidates:
                    print(f"Candidates: {len(candidates)}")
                    print(f"Top 1: {candidates[0].get('external_id')}")
            else:
                print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

async def main():
    refs = [
        "Cr. 335/1",       # Crawford (should be auto-detected)
        "RIC III 712",     # RIC (OCRE)
        "RPC I 1234",      # RPC
        "Crawford 544/14"  # Another Crawford
    ]
    for ref in refs:
        await test_lookup(ref)

if __name__ == "__main__":
    asyncio.run(main())
