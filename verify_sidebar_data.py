import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Capture response
        async def handle_response(response):
             if "stats/summary" in response.url and response.status == 200:
                 print(f"Stats Response Status: {response.status}")
                 try:
                     json_data = await response.json()
                     print(f"Total Coins: {json_data.get('total_coins')}")
                     print(f"Categories: {[c['category'] for c in json_data.get('by_category', [])]}")
                     print(f"Grades: {[g['grade'] for g in json_data.get('by_grade', [])]}")
                     print(f"Rulers: {[r['ruler'] for r in json_data.get('by_ruler', [])]}")
                 except Exception as e:
                     print(f"Error parsing JSON: {e}")

        page.on("response", handle_response)

        print("Navigating to /collection...")
        await page.goto("http://localhost:3000/collection")
        await page.wait_for_timeout(3000) # Wait for initial loads

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
