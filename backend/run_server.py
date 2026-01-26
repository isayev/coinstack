"""Custom server startup script with Windows async fix."""
import sys
import asyncio

# CRITICAL: Fix Windows + Playwright + FastAPI async subprocess issue
# Must be set BEFORE uvicorn imports anything
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    # Disable reload to avoid subprocess issues with Playwright on Windows
    uvicorn.run(
        "src.infrastructure.web.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # CRITICAL: reload=True breaks Playwright on Windows
        log_level="info"
    )
