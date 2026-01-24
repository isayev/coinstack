"""Test script for Excel import."""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.services.excel_import import import_collection_file

# Create tables
Base.metadata.create_all(bind=engine)

"""Test script for Excel import."""
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.services.excel_import import import_collection_file

# Create tables and data directory
Path("data").mkdir(exist_ok=True)
Base.metadata.create_all(bind=engine)


def test_import():
    """Test importing the Excel file."""
    db = SessionLocal()
    
    try:
        # Path to your Excel file
        excel_path = Path("../collection-v1.xlsx")
        
        if not excel_path.exists():
            print(f"Error: File not found: {excel_path}")
            print(f"Current directory: {Path.cwd()}")
            print(f"Looking for: {excel_path.absolute()}")
            return
        
        print(f"Importing from: {excel_path}")
        print("Running dry run first...")
        print("=" * 60)
        
        # Dry run
        import asyncio
        result = asyncio.run(import_collection_file(db, excel_path, dry_run=True))
        print(f"\nDry run results:")
        print(f"  Imported: {result.imported}")
        print(f"  Skipped: {result.skipped}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Warnings: {len(result.warnings)}")
        
        if result.errors:
            print("\nErrors (showing first 10):")
            for error in result.errors[:10]:
                print(f"  Row {error['row']}: {error['error']}")
        
        if result.warnings:
            print(f"\nWarnings (showing first 10 of {len(result.warnings)}):")
            for warning in result.warnings[:10]:
                print(f"  {warning}")
        
        # Ask for confirmation
        print("\n" + "=" * 60)
        response = input("\nProceed with actual import? (yes/no): ")
        if response.lower() == "yes":
            print("\nImporting...")
            result = asyncio.run(import_collection_file(db, excel_path, dry_run=False))
            print(f"\nImport complete:")
            print(f"  Imported: {result.imported}")
            print(f"  Skipped: {result.skipped}")
            print(f"  Errors: {len(result.errors)}")
            if result.errors:
                print("\nErrors:")
                for error in result.errors[:10]:
                    print(f"  Row {error['row']}: {error['error']}")
        else:
            print("Import cancelled.")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_import()
