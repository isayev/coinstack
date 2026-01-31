import logging
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.infrastructure.repositories.collection_repository import SqlAlchemyCollectionRepository
from src.infrastructure.repositories.market_price_repository import SqlAlchemyMarketPriceRepository
from src.infrastructure.repositories.coin_valuation_repository import SqlAlchemyCoinValuationRepository
from src.infrastructure.repositories.price_alert_repository import SqlAlchemyPriceAlertRepository
from src.infrastructure.repositories.wishlist_item_repository import SqlAlchemyWishlistItemRepository
from src.infrastructure.repositories.wishlist_match_repository import SqlAlchemyWishlistMatchRepository
from src.infrastructure.repositories.llm_enrichment_repository import SqlAlchemyLLMEnrichmentRepository
from src.infrastructure.repositories.prompt_template_repository import SqlAlchemyPromptTemplateRepository
from src.infrastructure.repositories.llm_feedback_repository import SqlAlchemyLLMFeedbackRepository
from src.infrastructure.repositories.llm_usage_repository import SqlAlchemyLLMUsageRepository
from src.infrastructure.repositories.market_data_point_repository import SqlAlchemyMarketDataPointRepository
from src.infrastructure.repositories.census_snapshot_repository import SqlAlchemyCensusSnapshotRepository
from src.infrastructure.repositories.countermark_repository import SqlAlchemyCountermarkRepository
from src.domain.repositories import (
    ICoinRepository, IAuctionDataRepository, ICollectionRepository,
    IMarketPriceRepository, ICoinValuationRepository, IPriceAlertRepository,
    IWishlistItemRepository, IWishlistMatchRepository, ILLMEnrichmentRepository,
    IPromptTemplateRepository, ILLMFeedbackRepository, ILLMUsageRepository,
    IMarketDataPointRepository, ICensusSnapshotRepository, ICountermarkRepository,
)
from src.domain.vocab import IVocabRepository
from src.application.services.apply_enrichment import ApplyEnrichmentService
from src.application.services.valuation_service import ValuationService
from src.application.services.price_alert_service import PriceAlertService
from src.application.services.wishlist_matching_service import WishlistMatchingService
from src.application.commands.save_llm_enrichment import SaveLLMEnrichmentUseCase

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

def get_vocab_repo(db: Session = Depends(get_db)) -> IVocabRepository:
    return SqlAlchemyVocabRepository(db)


def get_collection_repo(db: Session = Depends(get_db)) -> ICollectionRepository:
    return SqlAlchemyCollectionRepository(db)


def get_market_price_repo(db: Session = Depends(get_db)) -> IMarketPriceRepository:
    return SqlAlchemyMarketPriceRepository(db)


def get_coin_valuation_repo(db: Session = Depends(get_db)) -> ICoinValuationRepository:
    return SqlAlchemyCoinValuationRepository(db)


def get_price_alert_repo(db: Session = Depends(get_db)) -> IPriceAlertRepository:
    return SqlAlchemyPriceAlertRepository(db)


def get_wishlist_item_repo(db: Session = Depends(get_db)) -> IWishlistItemRepository:
    return SqlAlchemyWishlistItemRepository(db)


def get_wishlist_match_repo(db: Session = Depends(get_db)) -> IWishlistMatchRepository:
    return SqlAlchemyWishlistMatchRepository(db)


def get_llm_enrichment_repo(db: Session = Depends(get_db)) -> ILLMEnrichmentRepository:
    return SqlAlchemyLLMEnrichmentRepository(db)


def get_valuation_service(db: Session = Depends(get_db)) -> ValuationService:
    """Build ValuationService with market price and coin valuation repositories."""
    return ValuationService(
        market_repo=SqlAlchemyMarketPriceRepository(db),
        valuation_repo=SqlAlchemyCoinValuationRepository(db),
    )


def get_price_alert_service(db: Session = Depends(get_db)) -> PriceAlertService:
    """Build PriceAlertService with price alert and market price repositories."""
    return PriceAlertService(
        alert_repo=SqlAlchemyPriceAlertRepository(db),
        market_repo=SqlAlchemyMarketPriceRepository(db),
    )


def get_wishlist_matching_service(db: Session = Depends(get_db)) -> WishlistMatchingService:
    """Build WishlistMatchingService with wishlist item and match repositories."""
    return WishlistMatchingService(
        wishlist_repo=SqlAlchemyWishlistItemRepository(db),
        match_repo=SqlAlchemyWishlistMatchRepository(db),
    )


def get_save_llm_enrichment_use_case(db: Session = Depends(get_db)) -> SaveLLMEnrichmentUseCase:
    """Build SaveLLMEnrichmentUseCase with LLM enrichment repository."""
    return SaveLLMEnrichmentUseCase(
        enrichment_repo=SqlAlchemyLLMEnrichmentRepository(db),
    )


def get_prompt_template_repo(db: Session = Depends(get_db)) -> IPromptTemplateRepository:
    """Build PromptTemplateRepository for LLM prompt template management."""
    return SqlAlchemyPromptTemplateRepository(db)


def get_llm_feedback_repo(db: Session = Depends(get_db)) -> ILLMFeedbackRepository:
    """Build LLMFeedbackRepository for user feedback on LLM outputs."""
    return SqlAlchemyLLMFeedbackRepository(db)


def get_llm_usage_repo(db: Session = Depends(get_db)) -> ILLMUsageRepository:
    """Build LLMUsageRepository for LLM usage metrics and cost tracking."""
    return SqlAlchemyLLMUsageRepository(db)


def get_market_data_point_repo(db: Session = Depends(get_db)) -> IMarketDataPointRepository:
    """Build MarketDataPointRepository for individual price observations."""
    return SqlAlchemyMarketDataPointRepository(db)


def get_census_snapshot_repo(db: Session = Depends(get_db)) -> ICensusSnapshotRepository:
    """Build CensusSnapshotRepository for TPG census population tracking."""
    return SqlAlchemyCensusSnapshotRepository(db)


def get_countermark_repo(db: Session = Depends(get_db)) -> ICountermarkRepository:
    """Build CountermarkRepository for countermark management (Phase 1.5b)."""
    return SqlAlchemyCountermarkRepository(db)
