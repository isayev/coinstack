import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.persistence.models import Base
# Import all ORM models here so Base.metadata populates
import src.infrastructure.persistence.orm
import src.infrastructure.persistence.models_vocab
import src.infrastructure.persistence.models_series

@pytest.fixture(scope="session")
def db_engine():
    """Create a shared in-memory SQLite engine for the session."""
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}
    )
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Creates a fresh database session for a test.
    Rolls back transaction after test completes.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Bind session to the connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    # Create tables
    Base.metadata.create_all(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
