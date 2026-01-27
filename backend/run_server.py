"""Custom server startup script with Windows async fix."""
import sys
import asyncio

import os

# CRITICAL: Fix Windows + Playwright + FastAPI async subprocess issue
# Must be set BEFORE uvicorn imports anything
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure we are running from the backend directory so that relative paths (like DB) work correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    # Disable reload to avoid subprocess issues with Playwright on Windows
    uvicorn.run(
        "src.infrastructure.web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # CRITICAL: reload=True breaks Playwright on Windows
        log_level="info"
    )
