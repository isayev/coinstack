#!/usr/bin/env python
"""
DEPRECATED Script

This script relied on V1 legacy scrapers which have been removed in CoinStack V2.
Please use the V2 scraper endpoints via the API or UI.

Legacy functionality: process_other_venues.py
V2 replacement: POST /api/v2/scrape/url
"""

import sys

def main():
    print("=" * 60)
    print("DEPRECATION NOTICE")
    print("=" * 60)
    print("This script is deprecated in CoinStack V2.")
    print("The legacy scraper service (app.services.scrapers) has been replaced by")
    print("the new infrastructure scraper package (src.infrastructure.scrapers).")
    print("\nPlease use the V2 API to scrape URLs.")
    sys.exit(1)

if __name__ == "__main__":
    main()
