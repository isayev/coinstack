import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        print("Navigating to Collection...")
        try:
            await page.goto("http://localhost:3000/", timeout=60000)
            await page.wait_for_selector("text=CoinStack", timeout=30000)
        except Exception as e:
            print(f"Error loading page: {e}")
            await page.screenshot(path="debug_load_fail.png")
            return

        print("Page loaded. Switching to Table View...")
        
        # Click Table View button (title="Table View")
        try:
            await page.click('button[title="Table View"]')
            await asyncio.sleep(2) # Wait for render
        except Exception as e:
            print(f"Error switching view: {e}")
            return

        print("Table View active. Checking headers...")
        
        # Check for new headers
        headers_to_check = ["MINT", "AXIS", "SG", "STS"]
        content = await page.content()
        
        for h in headers_to_check:
            if h in content:
                print(f"SUCCESS: Found header '{h}'")
            else:
                print(f"FAILURE: Header '{h}' not found (might be hidden on this screen size)")

        # Take screenshot of table
        await page.screenshot(path="verify_table_view.png", full_page=True)
        print("Saved verify_table_view.png")

        # Test Sorting: Click "MINT"
        print("Testing Mint Sort...")
        try:
            # Find button with text "MINT"
            # Note: In our component, it's uppercase.
            # Using xpath to find button containing text
            mint_btn = page.locator("button", has_text="MINT")
            if await mint_btn.count() > 0:
                await mint_btn.first.click()
                await asyncio.sleep(2) # Wait for sort
                await page.screenshot(path="verify_sort_mint.png", full_page=True)
                print("Clicked Mint sort. Saved verify_sort_mint.png")
            else:
                print("Mint sort header not found/visible.")
        except Exception as e:
            print(f"Error sorting: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
