"""AuctionData model for tracking auction records and price comparisons."""
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, 
    ForeignKey, Boolean, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AuctionData(Base):
    """
    Auction record data - stores comprehensive metadata from auction listings.
    
    Captures full numismatic details extracted from CNG, Heritage, and other
    auction houses for data enrichment and price comparison.
    """
    
    __tablename__ = "auction_data"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Link to your coin (nullable for comparables)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUCTION IDENTIFICATION
    # ─────────────────────────────────────────────────────────────────────────
    auction_house = Column(String(100), nullable=False, index=True)  # Heritage, CNG, Biddr/Savoca, eBay
    sale_name = Column(String(200))               # "Triton XXIV", "Electronic Auction 603"
    lot_number = Column(String(50))               # Can be "1234" or "4-I2GBGT"
    source_lot_id = Column(String(50), index=True)  # CNG: "4-I2GBGT", Heritage: "3125-35124"
    auction_date = Column(Date, index=True)
    
    # URL - unique constraint ensures no duplicates
    url = Column(String(500), unique=True, nullable=False, index=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PRICING
    # ─────────────────────────────────────────────────────────────────────────
    estimate_low = Column(Numeric(10, 2))
    estimate_high = Column(Numeric(10, 2))
    estimate_usd = Column(Integer)                # Single estimate value
    hammer_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))          # Including buyer's premium
    buyers_premium_pct = Column(Numeric(4, 2))    # e.g., 20.00
    currency = Column(String(3), default="USD")
    sold = Column(Boolean, default=True)          # False if passed/unsold
    bids = Column(Integer)                        # Number of bids
    
    # ─────────────────────────────────────────────────────────────────────────
    # RULER & CLASSIFICATION (from CNG/Heritage structured data)
    # ─────────────────────────────────────────────────────────────────────────
    ruler = Column(String(200))                   # "Titus", "Faustina Junior"
    ruler_title = Column(String(100))             # "As Caesar", "Augusta"
    reign_dates = Column(String(50))              # "AD 69-79", "AD 147-175"
    
    denomination = Column(String(100))            # "Denarius", "Antoninianus"
    metal = Column(String(20))                    # "AR", "AV", "AE"
    mint = Column(String(100))                    # "Rome", "Alexandria"
    struck_dates = Column(String(100))            # "circa AD 161", "AD 75"
    struck_under = Column(String(200))            # "Vespasian", "Marcus Aurelius"
    
    # Categories/tags from auction house
    categories = Column(JSON)                     # ["Roman Imperial", "Silver"]
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHYSICAL MEASUREMENTS
    # ─────────────────────────────────────────────────────────────────────────
    weight_g = Column(Numeric(6, 3))
    diameter_mm = Column(Numeric(5, 2))
    thickness_mm = Column(Numeric(4, 2))          # Coin thickness (Biddr, eBay)
    die_axis = Column(Integer)                    # In hours (6h = 180°)
    die_axis_degrees = Column(Integer)            # In degrees (0-360)
    
    # ─────────────────────────────────────────────────────────────────────────
    # DESCRIPTIONS
    # ─────────────────────────────────────────────────────────────────────────
    title = Column(String(1000))                  # Full title line
    description = Column(Text)                    # Full raw description
    obverse_description = Column(Text)            # "Laureate head right"
    reverse_description = Column(Text)            # "Pax seated left..."
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONDITION & GRADING
    # ─────────────────────────────────────────────────────────────────────────
    grade = Column(String(50))                    # "VF", "Choice EF"
    grade_service = Column(String(20))            # "NGC", "PCGS"
    certification_number = Column(String(50))
    condition_notes = Column(Text)                # "scratch on obverse, porosity"
    
    # NGC/PCGS slab details (from Heritage)
    strike_score = Column(String(10))             # "4/5", "5/5"
    surface_score = Column(String(10))            # "4/5", "3/5"
    numeric_grade = Column(Integer)               # 1-70 Sheldon scale
    grade_designation = Column(String(50))        # "Fine Style", "Choice", "Star"
    
    # ─────────────────────────────────────────────────────────────────────────
    # CATALOG REFERENCES
    # ─────────────────────────────────────────────────────────────────────────
    catalog_references = Column(JSON)             # ["RIC II.1 783", "RSC 162"]
    catalog_references_raw = Column(JSON)         # Original text: ["RIC II.1 783 (Vespasian)"]
    primary_reference = Column(String(100))       # First/main reference
    
    # Reference match (for comparables)
    reference_type_id = Column(Integer, ForeignKey("reference_types.id"), nullable=True, index=True)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PROVENANCE
    # ─────────────────────────────────────────────────────────────────────────
    provenance_text = Column(Text)                # "Ex Berlin surgeon Collection..."
    pedigree_year = Column(Integer)               # Earliest documented year
    has_provenance = Column(Boolean, default=False)
    provenance_entries = Column(JSON)             # Structured provenance chain
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHOTOS
    # ─────────────────────────────────────────────────────────────────────────
    photos = Column(JSON)                         # List of image URLs
    primary_photo_url = Column(String(500))
    photos_downloaded = Column(Boolean, default=False)  # Track if images cached
    
    # ─────────────────────────────────────────────────────────────────────────
    # SOURCE-SPECIFIC METADATA
    # ─────────────────────────────────────────────────────────────────────────
    # Biddr sub-house (Savoca, Roma, Leu, Nomos, etc.)
    sub_house = Column(String(50))
    
    # eBay seller information
    seller_username = Column(String(100))
    seller_feedback_score = Column(Integer)
    seller_feedback_pct = Column(Numeric(5, 2))   # e.g., 99.50
    seller_is_top_rated = Column(Boolean)
    seller_location = Column(String(100))
    
    # Listing type details (eBay)
    listing_type = Column(String(50))             # "auction", "buy_it_now", "best_offer"
    shipping_cost = Column(Numeric(10, 2))
    watchers = Column(Integer)
    
    # ─────────────────────────────────────────────────────────────────────────
    # LEGENDS (structured text)
    # ─────────────────────────────────────────────────────────────────────────
    obverse_legend = Column(String(500))          # "CAESAR AVGVSTVS DIVI F"
    reverse_legend = Column(String(500))          # "AVGVSTI F COS DESIG"
    exergue = Column(String(200))                 # Text below main design
    
    # Historical/contextual notes
    historical_notes = Column(Text)               # From Heritage descriptions
    
    # ─────────────────────────────────────────────────────────────────────────
    # METADATA
    # ─────────────────────────────────────────────────────────────────────────
    scraped_at = Column(DateTime)                 # When data was scraped
    raw_data = Column(JSON)                       # Store full raw response for debugging
    
    # ─────────────────────────────────────────────────────────────────────────
    # CAMPAIGN TRACKING
    # ─────────────────────────────────────────────────────────────────────────
    campaign_scraped_at = Column(DateTime)        # When scraped by enrichment campaign
    campaign_successful = Column(Boolean)          # True if full data acquired (not just URL slug)
    campaign_error = Column(String(500))           # Error message if failed
    
    # ─────────────────────────────────────────────────────────────────────────
    # RELATIONSHIPS
    # ─────────────────────────────────────────────────────────────────────────
    coin = relationship("Coin", back_populates="auction_data")
    reference_type = relationship("ReferenceType")
    provenance_event = relationship("ProvenanceEvent", back_populates="auction_data", uselist=False)
