from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.persistence.models import Base

class CoinModel(Base):
    __tablename__ = "coins_v2"

    id = Column(Integer, primary_key=True, index=True)
    
    # Category/Metal
    category = Column(String, nullable=False)
    metal = Column(String, nullable=False)
    
    # Dimensions (Embedded)
    weight_g = Column(Numeric(10, 2), nullable=False)
    diameter_mm = Column(Numeric(10, 2), nullable=False)
    die_axis = Column(Integer, nullable=True)
    
    # Attribution (Embedded)
    issuer = Column(String, nullable=False)
    mint = Column(String, nullable=True)
    year_start = Column(Integer, nullable=True)
    year_end = Column(Integer, nullable=True)

    # Grading (Embedded)
    grading_state = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    grade_service = Column(String, nullable=True)
    certification_number = Column(String, nullable=True)
    strike_quality = Column(String, nullable=True)
    surface_quality = Column(String, nullable=True)

    # Acquisition (Embedded - Optional)
    acquisition_price = Column(Numeric(10, 2), nullable=True)
    acquisition_currency = Column(String, nullable=True)
    acquisition_source = Column(String, nullable=True)
    acquisition_date = Column(Date, nullable=True)
    acquisition_url = Column(String, nullable=True)

    # Description
    description = Column(String, nullable=True)

    # Relationships
    images = relationship("CoinImageModel", back_populates="coin", cascade="all, delete-orphan")

class CoinImageModel(Base):
    __tablename__ = "coin_images_v2"

    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins_v2.id"), nullable=False)
    url = Column(String, nullable=False)
    image_type = Column(String, nullable=False) # obverse, reverse
    is_primary = Column(Boolean, default=False)

    coin = relationship("CoinModel", back_populates="images")

class AuctionDataModel(Base):
    __tablename__ = "auction_data_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    coin_id = Column(Integer, ForeignKey("coins_v2.id"), nullable=True)
    
    # URL is unique key
    url = Column(String, unique=True, index=True, nullable=False)
    source = Column(String, nullable=False) # e.g. "Heritage", "CNG"
    sale_name = Column(String, nullable=True)
    lot_number = Column(String, nullable=True)
    source_lot_id = Column(String, nullable=True)
    
    # Financials
    hammer_price = Column(Numeric(10, 2), nullable=True)
    estimate_low = Column(Numeric(10, 2), nullable=True)
    estimate_high = Column(Numeric(10, 2), nullable=True)
    currency = Column(String, nullable=True)
    
    # Attribution from Scraper
    issuer = Column(String, nullable=True)
    mint = Column(String, nullable=True)
    year_start = Column(Integer, nullable=True)
    year_end = Column(Integer, nullable=True)
    
    # Physical
    weight_g = Column(Numeric(10, 3), nullable=True)
    diameter_mm = Column(Numeric(10, 2), nullable=True)
    die_axis = Column(Integer, nullable=True)
    
    # Descriptions
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    # Grading
    grade = Column(String, nullable=True)
    
    # Images (JSON list of URLs)
    primary_image_url = Column(String, nullable=True)
    additional_images = Column(String, nullable=True) # Stored as JSON string or array if supported
    
    # Metadata
    scraped_at = Column(Date, nullable=True)    
    
    coin = relationship("CoinModel", back_populates="auction_data")

# Add backref to CoinModel (monkey-patch or edit above)
CoinModel.auction_data = relationship("AuctionDataModel", back_populates="coin", uselist=False)

