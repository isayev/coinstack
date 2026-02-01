import logging
import time
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.models import Base
from src.infrastructure.config import get_settings

# Import all models to register them with Base.metadata
from src.infrastructure.persistence import orm  # CoinModel, CoinImageModel, AuctionDataModel, DieModels (Phase 1.5d)
from src.infrastructure.persistence import models_vocab  # IssuerModel, MintModel
from src.infrastructure.persistence import models_series  # SeriesModel, SeriesSlotModel
# from src.infrastructure.persistence import models_die_study  # DieLinkModel, DieStudyGroupModel (Legacy - replaced by Phase 1.5d)

logger = logging.getLogger(__name__)

settings = get_settings()
# Normalize URL if needed (remove ./ prefix logic handled by create_engine usually but consistent with other files)
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Slow query threshold in seconds (configurable via settings)
SLOW_QUERY_THRESHOLD_SECONDS = getattr(settings, 'SLOW_QUERY_THRESHOLD_SECONDS', 0.1)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# --- Slow Query Logging (Thread-safe using execution context) ---

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time in execution context (thread-safe)."""
    context._query_start_time = time.perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries exceeding threshold with request ID correlation."""
    from src.infrastructure.logging_config import get_request_id

    start_time = getattr(context, '_query_start_time', None)
    if start_time is None:
        return

    duration = time.perf_counter() - start_time

    if duration > SLOW_QUERY_THRESHOLD_SECONDS:
        # Truncate very long statements for readability
        stmt_preview = statement[:200] + "..." if len(statement) > 200 else statement
        request_id = get_request_id() or "-"
        logger.warning(
            "SLOW QUERY (%.3fs) [%s]: %s | params=%s",
            duration,
            request_id,
            stmt_preview,
            str(parameters)[:100] if parameters else "None"
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# NOTE: get_db() is defined in src.infrastructure.web.dependencies
# with proper transaction management (auto-commit/rollback).
# Import from there instead of duplicating here.
