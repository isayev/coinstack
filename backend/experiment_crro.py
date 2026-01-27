import asyncio
import httpx
import json

RECONCILE_URL = "http://numismatics.org/crro/apis/reconcile"

async def test_query(query_str):
    print(f"\nTesting Query: '{query_str}'")
    try:
        query = {"q0": {"query": query_str}}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                RECONCILE_URL,
                data={"queries": json.dumps(query)}
            )
            content = response.text.strip()
            # Handle JSONP or similar wrapper quirks if any (though usually strictly JSON validation fails first)
            if content.startswith('"q0"'): content = '{' + content + '}'
            
            data = json.loads(content)
            results = data.get("q0", {}).get("result", [])
            print(f"  Found {len(results)} matches")
            if results:
                print(f"  Top: {results[0].get('id')} ({results[0].get('name')}) Score: {results[0].get('score')}")
    except Exception as e:
        print(f"  Error: {e}")

async def main():
    queries = [
        "Crawford 335/1c",  # Current
        "RRC 335/1c",       # Standard abbr
        "335/1c",           # Just number
        "335/1",            # Main type
        "Crawford 335/1",   
        "RRC 335/1"
    ]
    
    for q in queries:
        await test_query(q)

if __name__ == "__main__":
    asyncio.run(main())
