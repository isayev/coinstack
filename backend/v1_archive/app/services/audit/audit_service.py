"""
AuditService for comparing coin data against auction records.

Performs data quality audits by comparing coin fields against auction data,
tracking discrepancies and enrichment opportunities with trust-aware logic.
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.models.discrepancy import DiscrepancyRecord
from app.models.enrichment import EnrichmentRecord
from app.models.audit_run import AuditRun
from app.models.mint import Mint

from .trust_config import get_field_trust, TrustLevel
from .comparator import NumismaticComparator, ComparisonResult

logger = logging.getLogger(__name__)


# Fields to audit - mapped from Coin model to AuctionData
AUDIT_FIELD_MAPPING = {
    # Physical measurements
    "weight_g": "weight_g",
    "diameter_mm": "diameter_mm",
    "thickness_mm": "thickness_mm",
    "die_axis": "die_axis",
    
    # Grading (including slab details from Heritage/NGC)
    "grade": "grade",
    "grade_service": "grade_service",
    "certification_number": "certification_number",
    "strike_score": "strike_score",      # NGC strike quality (e.g., "4/5")
    "surface_score": "surface_score",    # NGC surface quality (e.g., "5/5")
    
    # Text fields - legends and descriptions
    "obverse_legend": "obverse_legend",
    "reverse_legend": "reverse_legend",
    "obverse_description": "obverse_description",
    "reverse_description": "reverse_description",
    "exergue": "exergue",
    
    # Attribution fields
    "ruler": "ruler",
    "denomination": "denomination",
    "mint": "mint",
    "mint_year_start": "mint_year_start",
    "mint_year_end": "mint_year_end",
    
    # References (primary catalog reference)
    "primary_reference": "primary_reference",
}

# Fields that can be enriched from auction data (filled when coin field is empty)
ENRICHABLE_FIELDS = [
    # Physical
    "weight_g",
    "diameter_mm",
    "thickness_mm",
    "die_axis",
    
    # Grading
    "grade",
    "grade_service",
    "certification_number",
    "strike_score",
    "surface_score",
    
    # Descriptions
    "obverse_description",
    "reverse_description",
    "obverse_legend",
    "reverse_legend",
    "exergue",
    
    # Attribution
    "ruler",
    "denomination",
    "mint",
    "mint_year_start",
    "mint_year_end",
    
    # References
    "primary_reference",
    
    # Pricing
    "estimate_low",
    "estimate_high",
    "acquisition_price",
]


class AuditService:
    """
    Service for auditing coin data against auction records.
    
    Features:
    - Trust-aware comparison using granular trust matrix
    - Numismatic-aware field comparison
    - Progress tracking for long-running audits
    - Discrepancy and enrichment record creation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.comparator = NumismaticComparator()
    
    async def audit_coin(
        self,
        coin_id: int,
        audit_run_id: int | None = None,
    ) -> dict:
        """
        Audit a single coin against its auction data.
        
        Args:
            coin_id: ID of coin to audit
            audit_run_id: Optional audit run to associate records with
            
        Returns:
            Dict with audit results summary
        """
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            raise ValueError(f"Coin {coin_id} not found")
        
        # Get linked auction data
        auction_records = self.db.query(AuctionData).filter(
            AuctionData.coin_id == coin_id
        ).all()
        
        if not auction_records:
            return {
                "coin_id": coin_id,
                "auctions_checked": 0,
                "discrepancies": 0,
                "enrichments": 0,
                "message": "No auction data linked to this coin"
            }
        
        discrepancies_created = 0
        enrichments_created = 0
        
        for auction in auction_records:
            d, e = await self._audit_against_auction(
                coin, auction, audit_run_id
            )
            discrepancies_created += d
            enrichments_created += e
        
        return {
            "coin_id": coin_id,
            "auctions_checked": len(auction_records),
            "discrepancies": discrepancies_created,
            "enrichments": enrichments_created,
        }
    
    async def _audit_against_auction(
        self,
        coin: Coin,
        auction: AuctionData,
        audit_run_id: int | None,
    ) -> tuple[int, int]:
        """
        Audit a coin against a single auction record.
        
        Returns:
            Tuple of (discrepancies_created, enrichments_created)
        """
        source_house = auction.auction_house or "unknown"
        discrepancies = 0
        enrichments = 0
        
        # Check each auditable field
        for coin_field, auction_field in AUDIT_FIELD_MAPPING.items():
            coin_value = self._get_coin_value(coin, coin_field)
            auction_value = getattr(auction, auction_field, None)
            
            # Get trust configuration for this field/source
            field_trust = get_field_trust(coin_field, source_house)
            
            # Skip untrusted fields entirely
            if field_trust.trust_level == TrustLevel.UNTRUSTED:
                continue
            
            # If both have values, check for discrepancy
            if coin_value is not None and auction_value is not None:
                result = self.comparator.compare(
                    coin_field, coin_value, auction_value
                )
                
                if not result.matches:
                    # Create discrepancy record
                    await self._create_discrepancy(
                        coin, auction, coin_field,
                        coin_value, auction_value,
                        result, field_trust, audit_run_id
                    )
                    discrepancies += 1
            
            # If coin is missing value but auction has it, create enrichment
            elif coin_value is None and auction_value is not None:
                if coin_field in ENRICHABLE_FIELDS and field_trust.trust_level.can_suggest:
                    await self._create_enrichment(
                        coin, auction, coin_field,
                        auction_value, field_trust, audit_run_id
                    )
                    enrichments += 1
        
        return discrepancies, enrichments
    
    async def _create_discrepancy(
        self,
        coin: Coin,
        auction: AuctionData,
        field_name: str,
        current_value: Any,
        auction_value: Any,
        comparison: ComparisonResult,
        field_trust: Any,
        audit_run_id: int | None,
    ):
        """Create a discrepancy record."""
        # Check if similar discrepancy already exists
        existing = self.db.query(DiscrepancyRecord).filter(
            DiscrepancyRecord.coin_id == coin.id,
            DiscrepancyRecord.field_name == field_name,
            DiscrepancyRecord.auction_data_id == auction.id,
            DiscrepancyRecord.status == "pending",
        ).first()
        
        if existing:
            return  # Don't create duplicate
        
        record = DiscrepancyRecord(
            coin_id=coin.id,
            auction_data_id=auction.id,
            audit_run_id=audit_run_id,
            field_name=field_name,
            current_value=self._serialize_value(current_value),
            auction_value=self._serialize_value(auction_value),
            similarity=comparison.similarity,
            difference_type=comparison.difference_type,
            comparison_notes=comparison.notes,
            normalized_current=str(comparison.normalized_current) if comparison.normalized_current else None,
            normalized_auction=str(comparison.normalized_auction) if comparison.normalized_auction else None,
            source_house=auction.auction_house or "unknown",
            trust_level=field_trust.trust_level.value,
            auto_acceptable=field_trust.auto_accept,
            status="pending",
        )
        
        self.db.add(record)
        self.db.commit()
    
    async def _create_enrichment(
        self,
        coin: Coin,
        auction: AuctionData,
        field_name: str,
        suggested_value: Any,
        field_trust: Any,
        audit_run_id: int | None,
    ):
        """Create an enrichment record."""
        # Check if similar enrichment already exists
        existing = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.coin_id == coin.id,
            EnrichmentRecord.field_name == field_name,
            EnrichmentRecord.status == "pending",
        ).first()
        
        if existing:
            return  # Don't create duplicate
        
        record = EnrichmentRecord(
            coin_id=coin.id,
            auction_data_id=auction.id,
            audit_run_id=audit_run_id,
            field_name=field_name,
            suggested_value=self._serialize_value(suggested_value),
            source_house=auction.auction_house or "unknown",
            trust_level=field_trust.trust_level.value,
            confidence=field_trust.confidence,
            auto_applicable=field_trust.auto_accept,
            status="pending",
        )
        
        self.db.add(record)
        self.db.commit()
    
    def _get_coin_value(self, coin: Coin, field_name: str) -> Any:
        """
        Get a coin field value, handling relationship fields specially.
        
        For relationship fields like 'mint', returns the name instead of object.
        """
        if field_name == "mint":
            # Return mint name instead of Mint object
            return coin.mint.name if coin.mint else None
        elif field_name == "ruler":
            # For ruler, it maps to issuing_authority on coin
            return getattr(coin, "issuing_authority", None)
        elif field_name == "strike_score":
            return getattr(coin, "strike_quality", None)
        elif field_name == "surface_score":
            return getattr(coin, "surface_quality", None)
        else:
            return getattr(coin, field_name, None)
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize a value for storage in text field."""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        # Handle ORM objects that might slip through
        if hasattr(value, '__tablename__'):
            # This is an ORM model, try to get a reasonable string representation
            if hasattr(value, 'name'):
                return str(value.name)
            return f"<{value.__class__.__name__}>"
        return str(value)
    
    def _deserialize_value(self, text: str, target_type: type = str) -> Any:
        """Deserialize a value from storage."""
        if not text:
            return None
        if target_type == float:
            return float(text)
        if target_type == int:
            return int(text)
        if target_type in (dict, list):
            return json.loads(text)
        return text
    
    # =========================================================================
    # Bulk Audit Operations
    # =========================================================================
    
    async def create_audit_run(
        self,
        scope: str,
        coin_ids: list[int] | None = None,
    ) -> AuditRun:
        """
        Create a new audit run record.
        
        Args:
            scope: "single", "selected", or "all"
            coin_ids: List of coin IDs if scope is "single" or "selected"
            
        Returns:
            Created AuditRun record
        """
        # Count total coins
        if scope == "all":
            total = self.db.query(Coin).count()
        elif coin_ids:
            total = len(coin_ids)
        else:
            total = 0
        
        run = AuditRun(
            scope=scope,
            coin_ids=coin_ids,
            total_coins=total,
            status="running",
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        return run
    
    async def run_full_audit(self, audit_run_id: int):
        """
        Run audit on all coins with auction data.
        
        This is designed to be run as a background task.
        """
        run = self.db.query(AuditRun).filter(AuditRun.id == audit_run_id).first()
        if not run:
            logger.error(f"Audit run {audit_run_id} not found")
            return
        
        try:
            # Get coins with auction data
            if run.scope == "all":
                coins = self.db.query(Coin).filter(
                    Coin.auction_data.any()
                ).all()
            elif run.coin_ids:
                coins = self.db.query(Coin).filter(
                    Coin.id.in_(run.coin_ids)
                ).all()
            else:
                coins = []
            
            run.total_coins = len(coins)
            
            for coin in coins:
                try:
                    result = await self.audit_coin(coin.id, audit_run_id)
                    
                    # Update progress
                    run.coins_audited += 1
                    run.discrepancies_found += result.get("discrepancies", 0)
                    run.enrichments_found += result.get("enrichments", 0)
                    
                    if result.get("discrepancies", 0) > 0 or result.get("enrichments", 0) > 0:
                        run.coins_with_issues += 1
                    
                    self.db.commit()
                    
                except Exception as e:
                    logger.error(f"Error auditing coin {coin.id}: {e}")
                    continue
            
            # Mark complete
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.exception(f"Audit run {audit_run_id} failed")
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def run_selected_audit(
        self,
        coin_ids: list[int],
        audit_run_id: int,
    ):
        """Run audit on selected coins."""
        run = self.db.query(AuditRun).filter(AuditRun.id == audit_run_id).first()
        if not run:
            return
        
        run.coin_ids = coin_ids
        run.total_coins = len(coin_ids)
        
        try:
            for coin_id in coin_ids:
                result = await self.audit_coin(coin_id, audit_run_id)
                
                run.coins_audited += 1
                run.discrepancies_found += result.get("discrepancies", 0)
                run.enrichments_found += result.get("enrichments", 0)
                
                if result.get("discrepancies", 0) > 0 or result.get("enrichments", 0) > 0:
                    run.coins_with_issues += 1
                
                self.db.commit()
            
            run.status = "completed"
            run.completed_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            self.db.commit()
    
    # =========================================================================
    # Resolution Operations
    # =========================================================================
    
    async def resolve_discrepancy(
        self,
        discrepancy_id: int,
        resolution: str,
        notes: str | None = None,
    ) -> DiscrepancyRecord:
        """
        Resolve a discrepancy.
        
        Args:
            discrepancy_id: ID of discrepancy to resolve
            resolution: "accepted", "rejected", or "ignored"
            notes: Optional resolution notes
            
        Returns:
            Updated discrepancy record
        """
        record = self.db.query(DiscrepancyRecord).filter(
            DiscrepancyRecord.id == discrepancy_id
        ).first()
        
        if not record:
            raise ValueError(f"Discrepancy {discrepancy_id} not found")
        
        if resolution == "accepted":
            # Apply the auction value to the coin
            coin = self.db.query(Coin).filter(Coin.id == record.coin_id).first()
            if coin:
                # Deserialize and set the value
                auction_value = record.auction_value
                field_name = record.field_name
                
                # Handle type conversion based on field
                if field_name in ("weight_g", "diameter_mm"):
                    auction_value = float(auction_value) if auction_value else None
                    setattr(coin, field_name, auction_value)
                
                # Handle relationship fields
                elif field_name == "mint":
                    # Mint is a relationship - look up or create the Mint record
                    if auction_value:
                        mint = self.db.query(Mint).filter(Mint.name == auction_value).first()
                        if not mint:
                            # Create new mint with the auction value
                            mint = Mint(name=auction_value)
                            self.db.add(mint)
                            self.db.flush()
                        coin.mint_id = mint.id
                    else:
                        coin.mint_id = None
                
                else:
                    # Regular field - direct assignment
                    setattr(coin, field_name, auction_value)
        
        record.status = resolution
        record.resolution = resolution
        record.resolved_at = datetime.utcnow()
        record.resolution_notes = notes
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    async def bulk_resolve_discrepancies(
        self,
        discrepancy_ids: list[int],
        resolution: str,
        notes: str | None = None,
    ) -> int:
        """
        Bulk resolve multiple discrepancies.
        
        Returns:
            Number of discrepancies resolved
        """
        count = 0
        for disc_id in discrepancy_ids:
            try:
                await self.resolve_discrepancy(disc_id, resolution, notes)
                count += 1
            except Exception as e:
                logger.error(f"Failed to resolve discrepancy {disc_id}: {e}")
        
        return count
    
    async def apply_enrichment(
        self,
        enrichment_id: int,
    ) -> EnrichmentRecord:
        """
        Apply an enrichment suggestion to a coin.
        
        Args:
            enrichment_id: ID of enrichment to apply
            
        Returns:
            Updated enrichment record
        """
        record = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.id == enrichment_id
        ).first()
        
        if not record:
            raise ValueError(f"Enrichment {enrichment_id} not found")
        
        coin = self.db.query(Coin).filter(Coin.id == record.coin_id).first()
        if not coin:
            raise ValueError(f"Coin {record.coin_id} not found")
        
        # Apply the suggested value
        suggested_value = record.suggested_value
        
        # Handle type conversion based on field
        if record.field_name in ("weight_g", "diameter_mm"):
            suggested_value = float(suggested_value) if suggested_value else None
        elif record.field_name in ("estimate_low", "estimate_high"):
            suggested_value = float(suggested_value) if suggested_value else None
        
        setattr(coin, record.field_name, suggested_value)
        
        record.status = "applied"
        record.applied = True
        record.applied_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    async def reject_enrichment(
        self,
        enrichment_id: int,
        reason: str | None = None,
    ) -> EnrichmentRecord:
        """Reject an enrichment suggestion."""
        record = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.id == enrichment_id
        ).first()
        
        if not record:
            raise ValueError(f"Enrichment {enrichment_id} not found")
        
        record.status = "rejected"
        record.rejection_reason = reason
        
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_audit_summary(self) -> dict:
        """Get summary statistics for audit dashboard."""
        pending_discrepancies = self.db.query(DiscrepancyRecord).filter(
            DiscrepancyRecord.status == "pending"
        ).count()
        
        pending_enrichments = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.status == "pending"
        ).count()
        
        # By trust level
        discrepancies_by_trust = {}
        for level in ["authoritative", "high", "medium", "low"]:
            count = self.db.query(DiscrepancyRecord).filter(
                DiscrepancyRecord.status == "pending",
                DiscrepancyRecord.trust_level == level,
            ).count()
            discrepancies_by_trust[level] = count
        
        # By field
        from sqlalchemy import func
        field_counts = self.db.query(
            DiscrepancyRecord.field_name,
            func.count(DiscrepancyRecord.id)
        ).filter(
            DiscrepancyRecord.status == "pending"
        ).group_by(DiscrepancyRecord.field_name).all()
        
        discrepancies_by_field = {f: c for f, c in field_counts}
        
        # By source
        source_counts = self.db.query(
            DiscrepancyRecord.source_house,
            func.count(DiscrepancyRecord.id)
        ).filter(
            DiscrepancyRecord.status == "pending"
        ).group_by(DiscrepancyRecord.source_house).all()
        
        discrepancies_by_source = {s: c for s, c in source_counts}
        
        # Recent runs
        recent_runs = self.db.query(AuditRun).order_by(
            AuditRun.started_at.desc()
        ).limit(5).all()
        
        return {
            "pending_discrepancies": pending_discrepancies,
            "pending_enrichments": pending_enrichments,
            "discrepancies_by_trust": discrepancies_by_trust,
            "discrepancies_by_field": discrepancies_by_field,
            "discrepancies_by_source": discrepancies_by_source,
            "recent_runs": [
                {
                    "id": r.id,
                    "scope": r.scope,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "coins_audited": r.coins_audited,
                    "discrepancies_found": r.discrepancies_found,
                }
                for r in recent_runs
            ],
        }
