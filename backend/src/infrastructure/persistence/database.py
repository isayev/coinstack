from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.models import Base
from src.infrastructure.config import get_settings

# Import all models to register them with Base.metadata
from src.infrastructure.persistence import orm  # CoinModel, CoinImageModel, AuctionDataModel
from src.infrastructure.persistence import models_vocab  # IssuerModel, MintModel
from src.infrastructure.persistence import models_series  # SeriesModel, SeriesSlotModel
from src.infrastructure.persistence import models_die_study  # DieLinkModel, DieStudyGroupModel

settings = get_settings()
# Normalize URL if needed (remove ./ prefix logic handled by create_engine usually but consistent with other files)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# NOTE: get_db() is defined in src.infrastructure.web.dependencies
# with proper transaction management (auto-commit/rollback).
# Import from there instead of duplicating here.
