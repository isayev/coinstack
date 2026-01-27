import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        print("Navigating to Auctions...")
        try:
            await page.goto("http://localhost:3000/auctions", timeout=60000)
            await page.wait_for_selector("text=Auction Records", timeout=30000)
        except Exception as e:
            print(f"Error loading page: {e}")
            await page.screenshot(path="debug_auctions_fail.png")
            return

        print("Page loaded. Checking for headers...")
        
        # Check for new headers
        # Note: AuctionTableHeaderV2 uses uppercase in UI? 
        # "House", "Sale", "Lot", "Date", "Hammer", "Status"
        headers_to_check = ["House", "Sale", "Lot"]
        content = await page.content()
        
        for h in headers_to_check:
            if h in content:
                print(f"SUCCESS: Found header '{h}'")
            else:
                print(f"FAILURE: Header '{h}' not found (might be hidden on this screen size)")

        # Take screenshot of table
        await page.screenshot(path="verify_auctions_table.png", full_page=True)
        print("Saved verify_auctions_table.png")

        # Test View Toggle to Grid
        print("Testing Grid View Toggle...")
        try:
            # Find button with layout grid icon or title "Grid View"
            grid_btn = page.locator("button[title='Grid View']")
            if await grid_btn.count() > 0:
                await grid_btn.click()
                await asyncio.sleep(2) # Wait for render
                await page.screenshot(path="verify_auctions_grid.png", full_page=True)
                print("Clicked Grid view. Saved verify_auctions_grid.png")
            else:
                print("Grid view button not found.")
        except Exception as e:
            print(f"Error toggling view: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
