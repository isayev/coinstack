import asyncio
from src.infrastructure.services.catalogs.parser import parser
from src.infrastructure.services.catalogs.crro import CRROService

async def debug_logic():
    refs = [
        "Crawford 335/1c",
        "Crawford:335/1c", 
        "Cr. 335/1"
    ]
    
    print("\n=== PARSER DEBUG ===")
    for ref in refs:
        result = parser.parse(ref)
        print(f"Ref: '{ref}'")
        print(f"  System: {result.system}")
        print(f"  Normalized: {result.normalized}")
        print(f"  Number: {result.number}")
        print(f"  Needs LLM: {result.needs_llm}")
        
    print("\n=== CRRO SERVICE DEBUG ===")
    service = CRROService()
    for ref in refs:
        result = parser.parse(ref)
        if result.system == "crawford":
            query = await service.build_reconcile_query(ref)
            print(f"Ref: '{ref}' -> Query: {query}")
        else:
            print(f"Ref: '{ref}' -> Not detected as Crawford")

if __name__ == "__main__":
    asyncio.run(debug_logic())
