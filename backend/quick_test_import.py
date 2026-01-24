"""Quick test import - no user input required."""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
import asyncio
from app.database import SessionLocal, Base, engine
from app.services.excel_import import import_collection_file

# Create tables and data directory
Path("data").mkdir(exist_ok=True)
Base.metadata.create_all(bind=engine)


async def test_import_dry_run():
    """Test importing the Excel file (dry run only)."""
    db = SessionLocal()
    
    try:
        excel_path = Path("../collection-v1.xlsx")
        
        if not excel_path.exists():
            print(f"Error: File not found: {excel_path}")
            return
        
        print(f"Testing import from: {excel_path}")
        print("=" * 60)
        
        # Dry run
        result = await import_collection_file(db, excel_path, dry_run=True)
        
        print(f"\nDry run results:")
        print(f"  ✓ Ready to import: {result.imported}")
        print(f"  ⚠ Skipped: {result.skipped}")
        print(f"  ✗ Errors: {len(result.errors)}")
        print(f"  ℹ Warnings: {len(result.warnings)}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors[:10]:
                print(f"  Row {error['row']}: {error['error']}")
        
        # Show why rows were skipped (non-dry-run warnings)
        real_warnings = [w for w in result.warnings if "Dry run" not in w]
        if real_warnings:
            print(f"\nWarnings (why rows were skipped):")
            for warning in real_warnings[:10]:
                print(f"  {warning}")
        
        print("\n" + "=" * 60)
        print("Dry run complete! To import, run:")
        print("  python test_import.py --import")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        db.close()


async def do_import():
    """Actually import the data."""
    db = SessionLocal()
    
    try:
        excel_path = Path("../collection-v1.xlsx")
        print(f"Importing from: {excel_path}")
        print("=" * 60)
        
        result = await import_collection_file(db, excel_path, dry_run=False)
        
        print(f"\nImport complete:")
        print(f"  ✓ Imported: {result.imported}")
        print(f"  ⚠ Skipped: {result.skipped}")
        print(f"  ✗ Errors: {len(result.errors)}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  Row {error['row']}: {error['error']}")
        
        if result.imported > 0:
            print(f"\n✅ Successfully imported {result.imported} coins!")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if "--import" in sys.argv:
        asyncio.run(do_import())
    else:
        asyncio.run(test_import_dry_run())
