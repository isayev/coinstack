"""One-off script to fetch coin data from various catalogs (RPC, RIC, Crawford)."""
import asyncio
import json
from src.infrastructure.services.catalogs.registry import CatalogRegistry
from src.infrastructure.services.catalogs.parser import parse_catalog_reference_full


async def main():
    # Mix of references: RPC (no API), RIC (OCRE API), Crawford (CRRO API)
    refs = [
        ("RPC I 4374", "rpc", None),
        ("RIC I 207", "ric", {"ruler": "Augustus"}),
        ("RIC II 756", "ric", None),
        ("Crawford 335/1c", "crawford", None),
    ]
    print("Fetching coin data from catalogs...\n")
    for reference, system, context in refs:
        parsed = parse_catalog_reference_full(reference)
        print(f"--- {reference} (parsed: system={parsed.system}, volume={parsed.volume}, number={parsed.number}) ---")
        try:
            result = await CatalogRegistry.lookup(system=system, reference=reference, context=context)
            out = {
                "status": result.status,
                "external_id": result.external_id,
                "external_url": result.external_url,
                "confidence": result.confidence,
                "error_message": result.error_message,
                "payload_keys": list(result.payload.keys()) if result.payload else None,
            }
            if result.payload:
                out["payload_sample"] = {
                    k: (v[:80] + "..." if isinstance(v, str) and len(v) > 80 else v)
                    for k, v in list(result.payload.items())[:10]
                }
            if result.candidates:
                out["candidates"] = [
                    {"id": c.external_id, "name": c.name, "score": c.score}
                    for c in result.candidates[:5]
                ]
            print(json.dumps(out, indent=2))
            if result.external_url:
                print(f"  URL: {result.external_url}")
            # If ambiguous but we have candidates, fetch first by id to get type data
            if result.status == "ambiguous" and result.candidates:
                c = result.candidates[0]
                print(f"  Fetching by id: {c.external_id}")
                by_id = await CatalogRegistry.get_by_id(system, c.external_id)
                if by_id.status == "success" and by_id.payload:
                    sample = {k: (v[:60] + "..." if isinstance(v, str) and len(v) > 60 else v)
                              for k, v in list(by_id.payload.items())[:6]}
                    print(f"  Type data: {json.dumps(sample, indent=4)}")
        except Exception as e:
            print(f"  Error: {e}")
        print()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
