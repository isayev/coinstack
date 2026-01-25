"""SQLAlchemy models - Clean refactored schema."""
from app.models.coin import (
    Coin, 
    Category, 
    Metal, 
    DatingCertainty, 
    GradeService, 
    HolderType, 
    Rarity,
    Orientation
)
from app.models.mint import Mint
from app.models.reference import CoinReference, ReferenceSystem, ReferencePosition
from app.models.reference_type import ReferenceType, ReferenceMatchAttempt
from app.models.provenance import ProvenanceEvent, ProvenanceType
from app.models.image import CoinImage, ImageType
from app.models.tag import CoinTag
from app.models.countermark import Countermark, CountermarkType, CountermarkCondition, CountermarkPlacement
from app.models.auction_data import AuctionData
from app.models.price_history import PriceHistory

# Audit models
from app.models.discrepancy import DiscrepancyRecord
from app.models.enrichment import EnrichmentRecord
from app.models.audit_run import AuditRun
from app.models.image_source import ImageAuctionSource
from app.models.field_history import FieldHistory

# Import tracking
from app.models.import_record import ImportRecord, ImportSourceType

__all__ = [
    # Core models
    "Coin",
    "Mint",
    "CoinReference",
    "ReferenceType",
    "ReferenceMatchAttempt",
    "ProvenanceEvent",
    "CoinImage",
    "CoinTag",
    
    # New models
    "Countermark",
    "AuctionData",
    "PriceHistory",
    
    # Audit models
    "DiscrepancyRecord",
    "EnrichmentRecord",
    "AuditRun",
    "ImageAuctionSource",
    "FieldHistory",
    
    # Import tracking
    "ImportRecord",
    "ImportSourceType",
    
    # Enums - Coin
    "Category",
    "Metal",
    "DatingCertainty",
    "GradeService",
    "HolderType",
    "Rarity",
    "Orientation",
    
    # Enums - Reference
    "ReferenceSystem",
    "ReferencePosition",
    
    # Enums - Provenance
    "ProvenanceType",
    
    # Enums - Countermark
    "CountermarkType",
    "CountermarkCondition",
    "CountermarkPlacement",
    
    # Enums - Image
    "ImageType",
]
