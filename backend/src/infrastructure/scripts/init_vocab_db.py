import shutil
import os
from datetime import datetime
from sqlalchemy import create_engine
from src.infrastructure.persistence.models import Base
# Import all new models to ensure they are registered with Base
from src.infrastructure.persistence.models_vocab import IssuerModel, MintModel, IssuerAliasModel
from src.infrastructure.persistence.models_series import SeriesModel, SeriesSlotModel
from src.infrastructure.config import get_settings

def backup_database(db_url: str):
    if not db_url.startswith("sqlite:///"):
        print("Skipping backup for non-sqlite DB (or implement specific backup logic)")
        return

    db_path = db_url.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        print(f"No database found at {db_path} to backup.")
        return

    backup_dir = os.path.join("backups", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, os.path.basename(db_path))
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to {backup_path}")

def init_db():
    settings = get_settings()
    # Override for this specific task if needed, or trust settings
    # For safety in this environment where I see coinstack_v2.db in root:
    target_db = "coinstack_v2.db"
    database_url = f"sqlite:///{target_db}"
    
    print(f"Initializing database: {target_db}...")
    backup_database(database_url)
    
    engine = create_engine(database_url)
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()