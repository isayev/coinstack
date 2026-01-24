"""Coin tag model."""
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class CoinTag(Base):
    """Coin tag model."""
    
    __tablename__ = "coin_tags"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    
    coin = relationship("Coin", back_populates="tags")
    
    __table_args__ = (
        UniqueConstraint("coin_id", "tag", name="uq_coin_tag"),
    )
