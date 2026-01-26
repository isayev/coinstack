"""
Review API Router

Provides unified review endpoints for vocabulary assignments, LLM suggestions, and other review queues.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.vocab_repository import SqlAlchemyVocabRepository
from src.infrastructure.web.dependencies import get_db, get_vocab_repo
from sqlalchemy.orm import Session
import json

router = APIRouter(prefix="/api/v2/review", tags=["Review"])


class ReviewCountsResponse(BaseModel):
    """Response model for review counts."""
    vocabulary: int = 0
    ai: int = 0
    images: int = 0
    discrepancies: int = 0
    enrichments: int = 0
    data: int = 0
    total: int = 0


@router.get("/counts", response_model=ReviewCountsResponse)
def get_review_counts(
    db: Session = Depends(get_db),
    vocab_repo: SqlAlchemyVocabRepository = Depends(get_vocab_repo)
):
    """
    Get counts of items pending review across all sources.
    
    Aggregates counts from:
    - Vocabulary assignments (pending_review status)
    - LLM suggestions (suggested references or rarity)
    - Images (future)
    - Data discrepancies (future)
    """
    # Count vocabulary review items
    vocab_items = vocab_repo.get_review_queue("pending_review", limit=1000)
    vocab_count = len(vocab_items)
    
    # Count LLM suggestions
    llm_result = db.execute(text("""
        SELECT COUNT(*) 
        FROM coins_v2 
        WHERE llm_suggested_references IS NOT NULL 
           OR llm_suggested_rarity IS NOT NULL
    """))
    ai_count = llm_result.scalar() or 0
    
    # Future: Image review count
    images_count = 0
    
    # Discrepancies and enrichments are computed dynamically
    # For now return 0, tabs will fetch their own counts
    discrepancies_count = 0
    enrichments_count = 0
    
    # Future: Data discrepancies count
    data_count = 0
    
    total = vocab_count + ai_count + images_count + discrepancies_count + enrichments_count + data_count
    
    return ReviewCountsResponse(
        vocabulary=vocab_count,
        ai=ai_count,
        images=images_count,
        discrepancies=discrepancies_count,
        enrichments=enrichments_count,
        data=data_count,
        total=total
    )
