import asyncio
import sys
sys.path.insert(0, '.')

from pathlib import Path
from app.database import SessionLocal, engine, Base
from app.services.excel_import import import_collection_file

Base.metadata.create_all(bind=engine)

async def main():
    db = SessionLocal()
    try:
        file_path = Path(r'c:\vibecode\coinstack\original-data\collection-v1.xlsx')
        print(f"Importing from: {file_path}")
        result = await import_collection_file(db, file_path, dry_run=False)
        print(f"Import complete: {result.to_dict()}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
