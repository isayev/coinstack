"""Coin reference model - Clean type-only design."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ReferenceSystem(enum.Enum):
    """Reference catalog system."""
    RIC = "ric"
    CRAWFORD = "crawford"
    RPC = "rpc"
    RSC = "rsc"
    BMCRE = "bmcre"
    SEAR = "sear"
    SYDENHAM = "sydenham"
    SNG = "sng"              # Sylloge Nummorum Graecorum
    BMC = "bmc"              # British Museum Catalogue (Greek)
    HN = "hn"                # Historia Numorum
    OTHER = "other"


class ReferencePosition(enum.Enum):
    """Which side of coin the reference describes."""
    OBVERSE = "obverse"
    REVERSE = "reverse"
    BOTH = "both"


class CoinReference(Base):
    """
    Links a coin specimen to a catalog type.
    
    CLEAN DESIGN: All catalog data lives in ReferenceType.
    This table only contains specimen-specific data.
    """
    
    __tablename__ = "coin_references"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # REQUIRED: Link to ReferenceType (no legacy fields)
    reference_type_id = Column(Integer, ForeignKey("reference_types.id"), nullable=False, index=True)
    
    # Specimen-specific fields only
    is_primary = Column(Boolean, default=False)
    plate_coin = Column(Boolean, default=False)
    position = Column(Enum(ReferencePosition), default=ReferencePosition.BOTH)
    variant_notes = Column(String(255))   # "var. b, different bust"
    
    # Scholarly citation additions
    page = Column(String(20))             # "123-124"
    plate = Column(String(30))            # "pl. 5" or "Taf. XII"
    note_number = Column(String(20))      # footnote references
    notes = Column(String(255))           # General notes
    
    # Relationships
    coin = relationship("Coin", back_populates="references")
    reference_type = relationship("ReferenceType", back_populates="coin_references")
    
    @property
    def display_reference(self) -> str:
        """Get the display reference string from ReferenceType."""
        if self.reference_type:
            return self.reference_type.local_ref
        return "Unknown"
    
    @property
    def external_url(self) -> str | None:
        """Get external catalog URL from ReferenceType."""
        if self.reference_type:
            return self.reference_type.external_url
        return None
    
    @property
    def lookup_status(self) -> str | None:
        """Get lookup status from reference type."""
        if self.reference_type:
            return self.reference_type.lookup_status
        return None
    
    @property
    def lookup_confidence(self) -> float | None:
        """Get lookup confidence from reference type."""
        if self.reference_type:
            return float(self.reference_type.lookup_confidence) if self.reference_type.lookup_confidence else None
        return None
