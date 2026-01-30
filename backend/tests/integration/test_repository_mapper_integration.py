import pytest
import json
from decimal import Decimal
from sqlalchemy import text
from src.domain.coin import (
    Coin, Category, Metal, Dimensions, Attribution, GradingDetails, 
    GradingState, ProvenanceEntry, EnrichmentData
)
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.persistence.orm import CoinModel

def test_provenance_persistence(db_session):
    """Test that provenance events are correctly persisted via the repository."""
    repo = SqlAlchemyCoinRepository(db_session)
    
    # 1. Create coin with provenance
    coin = Coin(
        id=None,
        category=Category.GREEK,
        metal=Metal.SILVER,
        dimensions=Dimensions(diameter_mm=Decimal("20.0"), weight_g=Decimal("4.0")),
        attribution=Attribution(issuer="Athens"),
        grading=GradingDetails(grading_state=GradingState.RAW, grade="VF"),
        provenance=[
            ProvenanceEntry(
                source_type="auction",
                source_name="Heritage",
                lot_number="12345",
                notes="Ex. Famous Collection"
            )
        ]
    )
    
    saved = repo.save(coin)
    assert saved.id is not None
    
    # 2. Reload from DB (clear session first to ensure fresh fetch)
    db_session.expunge_all()
    reloaded = repo.get_by_id(saved.id)
    
    assert len(reloaded.provenance) == 1
    assert reloaded.provenance[0].source_name == "Heritage"
    assert reloaded.provenance[0].lot_number == "12345"

def test_json_corruption_resilience(db_session):
    """Test that invalid JSON in the database does not crash the application."""
    repo = SqlAlchemyCoinRepository(db_session)
    
    # 1. Insert a coin manually with bad JSON
    # using raw SQL to bypass mapper protections on write
    db_session.execute(
        text("""
            INSERT INTO coins_v2 (
                category, metal, diameter_mm, issuer, grading_state, grade, 
                llm_analysis_sections, secondary_treatments, issue_status,
                historical_significance
            ) VALUES (
                'greek', 'silver', 20.0, 'Test', 'raw', 'VF',
                '{bad json', '[broken list', 'official',
                'Forces creation of EnrichmentData'
            )
        """)
    )
    db_session.commit()
    
    # Get ID of inserted coin
    coin_id = db_session.execute(text("SELECT last_insert_rowid()")).scalar()
    
    # 2. Load via repository
    coin = repo.get_by_id(coin_id)
    
    # 3. Verify it didn't crash and fields are None
    assert coin is not None
    assert coin.enrichment.analysis_sections is None
    assert coin.secondary_treatments is None

def test_grade_enum_persistence(db_session):
    """Test that specific grade enums persist correctly."""
    repo = SqlAlchemyCoinRepository(db_session)
    
    # Validation should catch missing service
    from src.domain.coin import GradeService
    with pytest.raises(ValueError):
        Coin(
            id=None,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.GOLD,
            dimensions=Dimensions(diameter_mm=Decimal("20.0"), weight_g=Decimal("7.2")),
            attribution=Attribution(issuer="Augustus"),
            grading=GradingDetails(
                grading_state=GradingState.SLABBED, # Enum
                grade="MS 65",
                service=None # Missing service for slabbed
            )
        )
        
    # Fix and save
    coin = Coin(
        id=None,
        category=Category.ROMAN_IMPERIAL,
        metal=Metal.GOLD,
        dimensions=Dimensions(diameter_mm=Decimal("20.0"), weight_g=Decimal("7.2")),
        attribution=Attribution(issuer="Augustus"),
        grading=GradingDetails(
            grading_state=GradingState.SLABBED,
            grade="MS 65",
            service=GradeService.NGC
        )
    )
    
    saved = repo.save(coin)
    db_session.expunge_all()
    reloaded = repo.get_by_id(saved.id)
    
    assert reloaded.grading.grading_state == GradingState.SLABBED
    assert reloaded.grading.service == GradeService.NGC