import logging
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.domain.repositories import ICoinRepository, IAuctionDataRepository
from src.application.services.apply_enrichment import ApplyEnrichmentService

logger = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit transaction on successful completion
    except Exception as e:
        logger.warning(f"Database transaction rolled back due to: {type(e).__name__}: {str(e)}")
        db.rollback()  # Rollback on any exception
        raise
    finally:
        db.close()

def get_coin_repo(db: Session = Depends(get_db)) -> ICoinRepository:
    return SqlAlchemyCoinRepository(db)


def get_apply_enrichment_service(db: Session = Depends(get_db)) -> ApplyEnrichmentService:
    """Build ApplyEnrichmentService with coin repo for audit/catalog apply flows."""
    return ApplyEnrichmentService(SqlAlchemyCoinRepository(db))

def get_auction_repo(db: Session = Depends(get_db)) -> IAuctionDataRepository:
    return SqlAlchemyAuctionDataRepository(db)

def get_vocab_repo(db: Session = Depends(get_db)) -> SqlAlchemyVocabRepository:
    return SqlAlchemyVocabRepository(db)
