"""One-off script to fetch coin data from various catalogs (RPC, RIC, Crawford) using real APIs/Scrapers."""
import asyncio
import json
import os
import sys

# Ensure backend is in path
sys.path.append(os.getcwd())

from src.infrastructure.services.catalogs.registry import CatalogRegistry
from src.infrastructure.services.catalogs.parser import parse_catalog_reference_full


async def main():
    # Mix of references covering:
    # 1. Standard lookups
    # 2. Complex parser edge cases (editions, parts)
    # 3. Internet/Dealer variants (vol, colon)
    refs = [
        # Standard OCRE (RIC)
        ("RIC I 207", "ric", None),
        ("RIC II 756", "ric", None),
        
        # Standard CRRO (Crawford)
        ("Crawford 335/1c", "crawford", None),
        
        # RPC (Scraper)
        ("RPC I 4374", "rpc", None),
        
        # --- Edge Cases (The ones we just fixed) ---
        
        # Editions
        ("RIC I (2nd ed) 1", "ric", None),  # Should normalize to I.2 1
        ("RIC I² 207", "ric", None),        # Should normalize to I.2 207
        
        # Bare Parts
        ("RIC IV 1 123", "ric", None),      # Should normalize to IV.1 123
        
        # Internet Variants
        ("RIC vol I 207", "ric", None),     # Should normalize to RIC I 207
        ("RIC VI: 123", "ric", None),       # Colon separator
        
        # RPC Variants
        ("RPC IV.1 1234", "rpc", None),     # Complex volume
    ]
    
    print(f"Fetching coin data for {len(refs)} references...\n")
    
    for reference, system, context in refs:
        print(f"--- Processing: '{reference}' ---")
        
        # 1. Test Parsing Logic
        parsed = parse_catalog_reference_full(reference)
        print(f"  Parsed: System={parsed.system}, Vol={parsed.volume}, Num={parsed.number}, Norm={parsed.normalized}")
        
        if parsed.warnings:
            print(f"  Warnings: {parsed.warnings}")
            
        if not parsed.system:
            print("  [SKIP] Parser failed to identify system.")
            print()
            continue

        # 2. Test Fetching Logic (Live API/Scraper)
        try:
            # We use the system from the parser if available, or the hint
            sys_to_use = parsed.system or system
            
            result = await CatalogRegistry.lookup(system=sys_to_use, reference=reference, context=context)
            
            status_icon = "✅" if result.status == "success" else ("⚠️" if result.status == "ambiguous" else "❌")
            print(f"  Result: {status_icon} {result.status.upper()}")
            
            if result.external_url:
                print(f"  URL: {result.external_url}")
                
            if result.error_message:
                print(f"  Error: {result.error_message}")
                
            if result.payload:
                title = result.payload.get('title') or result.payload.get('axis') or "No Title"
                print(f"  Payload: Found type data ({len(result.payload)} keys). Title: {title}")
                
            if result.candidates:
                print(f"  Candidates ({len(result.candidates)}):")
                for c in result.candidates[:3]:
                    print(f"    - {c.name} ({c.external_id}) Score: {c.score}")

        except Exception as e:
            print(f"  CRITICAL ERROR: {e}")
        
        print("-" * 60)
        print()

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())