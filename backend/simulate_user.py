
import asyncio
import os
from playwright.async_api import async_playwright

# Ensure HOME is set for playwright
if 'HOME' not in os.environ and 'USERPROFILE' in os.environ:
    os.environ['HOME'] = os.environ['USERPROFILE']

async def main():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))

        print("Navigating to http://127.0.0.1:3000 ...")
        try:
            await page.goto("http://127.0.0.1:3000", timeout=30000)
            print("Page loaded.")
        except Exception as e:
            print(f"Failed to load page: {e}")
            await browser.close()
            return

        # Screenshot Main Page
        await page.screenshot(path="frontend_main.png")
        print("Saved frontend_main.png")

        # Try to find "Add Coin" or "Import" button
        # Based on common patterns in this app.
        # It might be an icon or text.
        # I'll look for "Add Coin" or "Import".
        
        # Taking a guess at likely selectors or text
        try:
            # Look for button with text "Add Coin" or "Import"
            await page.wait_for_timeout(2000) # Wait for hydration
            
            # Check for "Add Coin" button
            add_coin_btn = page.get_by_text("Add Coin")
            import_btn = page.get_by_text("Import")
            
            if await add_coin_btn.count() > 0:
                print("Found 'Add Coin' button. Clicking...")
                await add_coin_btn.first.click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path="add_coin_dialog.png")
                print("Saved add_coin_dialog.png")
            elif await import_btn.count() > 0:
                print("Found 'Import' button. Clicking...")
                await import_btn.first.click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path="import_dialog.png")
                print("Saved import_dialog.png")
            else:
                print("Could not find 'Add Coin' or 'Import' buttons. Trying to find any button...")
                buttons = await page.get_by_role("button").all()
                if buttons:
                    print(f"Found {len(buttons)} buttons.")
                    # Screenshot with buttons highlighted? No, just keep main.
                else:
                    print("No buttons found.")

        except Exception as e:
            print(f"Error interacting with page: {e}")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
