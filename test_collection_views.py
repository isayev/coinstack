import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Capture requests
        requests = []
        page.on("request", lambda request: requests.append(request))

        print("Navigating to /collection...")
        await page.goto("http://localhost:3000/collection")
        await page.wait_for_url("**/collection/grid")
        
        # 1. Check if stats request was made
        await page.wait_for_timeout(2000) # Wait for initial loads
        stats_req = next((r for r in requests if "stats/summary" in r.url), None)
        if stats_req:
            print("SUCCESS: Stats API called")
        else:
             print("FAILURE: Stats API NOT called")

        # 2. Test Sorting
        # Clear requests to track new ones
        requests.clear()
        print("Clicking Sort by Date...")
        await page.click("text=Date")
        
        await page.wait_for_timeout(1000)
        
        # Check for coins request with sort_by=year
        coins_req = next((r for r in requests if "coins" in r.url and "sort_by=year" in r.url), None)
        if coins_req:
             print("SUCCESS: Sort triggered API call with sort_by=year")
        else:
             print("FAILURE: Sort did NOT trigger API call")
             # Print last few requests to debug
             for r in requests[-3:]:
                 print(f"DEBUG: Request: {r.url}")

        # 3. Test Filter (Sidebar)
        # Click a metal filter "silver" if it exists
        # We need to find a metal button. They are dynamically generated.
        # We can try to click any button inside the Metal filter section.
        # Assuming Metal section is first.
        # But without knowing content, maybe hard.
        # Let's just rely on sort for now as proof of store connection.

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
