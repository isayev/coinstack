"""
EnrichmentService for suggesting and applying field updates from auction data.

Analyzes auction data to find missing fields in coin records and suggests
enrichments based on trust configuration.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.models.enrichment import EnrichmentRecord

from .trust_config import get_field_trust, TrustLevel, get_all_trusted_fields

logger = logging.getLogger(__name__)


# Fields that can be enriched from auction data
ENRICHABLE_FIELDS = {
    # Physical measurements
    "weight_g": {"auction_field": "weight_g", "type": float},
    "diameter_mm": {"auction_field": "diameter_mm", "type": float},
    "die_axis": {"auction_field": "die_axis", "type": int},
    
    # Grading
    "grade": {"auction_field": "grade", "type": str},
    "grade_service": {"auction_field": "grade_service", "type": str},
    "certification_number": {"auction_field": "certification_number", "type": str},
    # strike_score/surface_score from auction data maps to strike_quality/surface_quality on coin
    "strike_score": {"auction_field": "strike_score", "type": str, "coin_field": "strike_quality"},
    "surface_score": {"auction_field": "surface_score", "type": str, "coin_field": "surface_quality"},
    "strike_quality": {"auction_field": "strike_score", "type": int},
    "surface_quality": {"auction_field": "surface_score", "type": int},
    
    # Descriptions
    "obverse_description": {"auction_field": "obverse_description", "type": str},
    "reverse_description": {"auction_field": "reverse_description", "type": str},
    
    # Valuation (from auction estimates)
    "estimate_low": {"auction_field": "estimate_low", "type": float},
    "estimate_high": {"auction_field": "estimate_high", "type": float},
}


class EnrichmentService:
    """
    Service for suggesting and applying enrichments from auction data.
    
    Features:
    - Identifies missing fields that can be filled from auction data
    - Considers trust levels when making suggestions
    - Tracks all enrichment applications for audit trail
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_enrichment_suggestions(
        self,
        coin_id: int,
        min_trust: TrustLevel = TrustLevel.MEDIUM,
    ) -> list[dict]:
        """
        Get enrichment suggestions for a coin.
        
        Args:
            coin_id: ID of coin to analyze
            min_trust: Minimum trust level for suggestions
            
        Returns:
            List of enrichment suggestions
        """
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            raise ValueError(f"Coin {coin_id} not found")
        
        # Get linked auction data
        auctions = self.db.query(AuctionData).filter(
            AuctionData.coin_id == coin_id
        ).all()
        
        if not auctions:
            return []
        
        suggestions = []
        
        for field_name, field_config in ENRICHABLE_FIELDS.items():
            # Check if field is missing in coin
            current_value = getattr(coin, field_name, None)
            if current_value is not None:
                continue  # Field already has value
            
            # Look for value in auction data
            best_suggestion = self._find_best_value(
                field_name,
                field_config,
                auctions,
                min_trust,
            )
            
            if best_suggestion:
                suggestions.append(best_suggestion)
        
        return suggestions
    
    def _find_best_value(
        self,
        field_name: str,
        field_config: dict,
        auctions: list[AuctionData],
        min_trust: TrustLevel,
    ) -> dict | None:
        """
        Find the best value for a field from available auction data.
        
        Prioritizes by trust level, then by recency.
        """
        auction_field = field_config["auction_field"]
        candidates = []
        
        for auction in auctions:
            auction_value = getattr(auction, auction_field, None)
            if auction_value is None:
                continue
            
            # Get trust configuration
            source_house = auction.auction_house or "unknown"
            field_trust = get_field_trust(field_name, source_house)
            
            # Skip if below minimum trust
            if not self._meets_trust_threshold(field_trust.trust_level, min_trust):
                continue
            
            candidates.append({
                "value": auction_value,
                "source_house": source_house,
                "trust_level": field_trust.trust_level,
                "confidence": field_trust.confidence,
                "auto_applicable": field_trust.auto_accept,
                "auction_id": auction.id,
                "auction_date": auction.auction_date,
            })
        
        if not candidates:
            return None
        
        # Sort by trust level (highest first), then by date (most recent first)
        trust_order = {
            TrustLevel.AUTHORITATIVE: 0,
            TrustLevel.HIGH: 1,
            TrustLevel.MEDIUM: 2,
            TrustLevel.LOW: 3,
            TrustLevel.UNTRUSTED: 4,
        }
        
        candidates.sort(key=lambda x: (
            trust_order.get(x["trust_level"], 5),
            -(x["auction_date"].toordinal() if x["auction_date"] else 0)
        ))
        
        best = candidates[0]
        
        return {
            "field_name": field_name,
            "suggested_value": best["value"],
            "source_house": best["source_house"],
            "trust_level": best["trust_level"].value,
            "confidence": best["confidence"],
            "auto_applicable": best["auto_applicable"],
            "auction_data_id": best["auction_id"],
            "alternative_count": len(candidates) - 1,
        }
    
    def _meets_trust_threshold(
        self,
        level: TrustLevel,
        minimum: TrustLevel,
    ) -> bool:
        """Check if trust level meets minimum threshold."""
        order = [
            TrustLevel.AUTHORITATIVE,
            TrustLevel.HIGH,
            TrustLevel.MEDIUM,
            TrustLevel.LOW,
            TrustLevel.UNTRUSTED,
        ]
        return order.index(level) <= order.index(minimum)
    
    async def create_enrichment_records(
        self,
        coin_id: int,
        audit_run_id: int | None = None,
        min_trust: TrustLevel = TrustLevel.MEDIUM,
    ) -> list[EnrichmentRecord]:
        """
        Create enrichment records for all missing fields.
        
        This is used during audits to persist enrichment suggestions.
        """
        suggestions = await self.get_enrichment_suggestions(coin_id, min_trust)
        records = []
        
        for suggestion in suggestions:
            # Check if record already exists
            existing = self.db.query(EnrichmentRecord).filter(
                EnrichmentRecord.coin_id == coin_id,
                EnrichmentRecord.field_name == suggestion["field_name"],
                EnrichmentRecord.status == "pending",
            ).first()
            
            if existing:
                continue
            
            record = EnrichmentRecord(
                coin_id=coin_id,
                auction_data_id=suggestion["auction_data_id"],
                audit_run_id=audit_run_id,
                field_name=suggestion["field_name"],
                suggested_value=str(suggestion["suggested_value"]),
                source_house=suggestion["source_house"],
                trust_level=suggestion["trust_level"],
                confidence=suggestion["confidence"],
                auto_applicable=suggestion["auto_applicable"],
                status="pending",
            )
            
            self.db.add(record)
            records.append(record)
        
        self.db.commit()
        
        for r in records:
            self.db.refresh(r)
        
        return records
    
    async def apply_enrichment(
        self,
        enrichment_id: int,
    ) -> EnrichmentRecord:
        """
        Apply a single enrichment to a coin.
        
        Args:
            enrichment_id: ID of enrichment record
            
        Returns:
            Updated enrichment record
        """
        record = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.id == enrichment_id
        ).first()
        
        if not record:
            raise ValueError(f"Enrichment {enrichment_id} not found")
        
        if record.status != "pending":
            raise ValueError(f"Enrichment {enrichment_id} is not pending")
        
        coin = self.db.query(Coin).filter(Coin.id == record.coin_id).first()
        if not coin:
            raise ValueError(f"Coin {record.coin_id} not found")
        
        # Get field configuration
        field_config = ENRICHABLE_FIELDS.get(record.field_name, {"type": str})
        field_type = field_config.get("type", str)
        
        # Map field names if needed (e.g., strike_score -> strike_quality)
        coin_field = field_config.get("coin_field", record.field_name)
        
        # Convert value to appropriate type
        value = record.suggested_value
        if value:
            # Special handling for score fields (e.g., "5/5" -> 5)
            if record.field_name in ("strike_score", "surface_score"):
                # Extract first number from "5/5" format
                if "/" in str(value):
                    value = int(str(value).split("/")[0])
                else:
                    value = int(float(value))
                coin_field = "strike_quality" if record.field_name == "strike_score" else "surface_quality"
            elif field_type == float:
                value = float(value)
            elif field_type == int:
                value = int(float(value))  # Handle "5.0" -> 5
        
        # Apply to coin
        setattr(coin, coin_field, value)
        
        # Update enrichment record
        record.status = "applied"
        record.applied = True
        record.applied_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(f"Applied enrichment {enrichment_id}: {record.field_name} = {value}")
        
        return record
    
    async def apply_all_auto_enrichments(
        self,
        coin_id: int,
    ) -> list[EnrichmentRecord]:
        """
        Apply all auto-applicable enrichments for a coin.
        
        Only applies enrichments where trust level allows auto-accept.
        
        Returns:
            List of applied enrichment records
        """
        records = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.coin_id == coin_id,
            EnrichmentRecord.status == "pending",
            EnrichmentRecord.auto_applicable == True,
        ).all()
        
        applied = []
        
        for record in records:
            try:
                await self.apply_enrichment(record.id)
                applied.append(record)
            except Exception as e:
                logger.error(f"Failed to auto-apply enrichment {record.id}: {e}")
        
        return applied
    
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
    
    async def bulk_apply_enrichments(
        self,
        enrichment_ids: list[int],
    ) -> dict:
        """
        Apply multiple enrichments.
        
        Returns:
            Summary of results
        """
        applied = 0
        failed = 0
        
        for eid in enrichment_ids:
            try:
                await self.apply_enrichment(eid)
                applied += 1
            except Exception as e:
                logger.error(f"Failed to apply enrichment {eid}: {e}")
                failed += 1
        
        return {
            "applied": applied,
            "failed": failed,
            "total": len(enrichment_ids),
        }
    
    async def bulk_reject_enrichments(
        self,
        enrichment_ids: list[int],
        reason: str | None = None,
    ) -> dict:
        """
        Reject multiple enrichments.
        
        Returns:
            Summary of results
        """
        rejected = 0
        failed = 0
        
        for eid in enrichment_ids:
            try:
                await self.reject_enrichment(eid, reason)
                rejected += 1
            except Exception as e:
                logger.error(f"Failed to reject enrichment {eid}: {e}")
                failed += 1
        
        return {
            "rejected": rejected,
            "failed": failed,
            "total": len(enrichment_ids),
        }
    
    async def apply_all_empty_field_enrichments(self) -> dict:
        """
        Apply all pending enrichments that fill empty fields.
        
        Enrichments are by definition for empty fields (they're created when
        the coin field is null), so this applies all pending enrichments.
        
        Returns:
            Summary of results with details
        """
        # Get all pending enrichments
        records = self.db.query(EnrichmentRecord).filter(
            EnrichmentRecord.status == "pending",
        ).all()
        
        applied = 0
        failed = 0
        failed_details = []
        applied_by_field = {}
        
        for record in records:
            try:
                await self.apply_enrichment(record.id)
                applied += 1
                # Track by field
                field = record.field_name
                applied_by_field[field] = applied_by_field.get(field, 0) + 1
            except Exception as e:
                logger.error(f"Failed to apply enrichment {record.id}: {e}")
                failed += 1
                failed_details.append({
                    "id": record.id,
                    "field": record.field_name,
                    "coin_id": record.coin_id,
                    "error": str(e),
                })
        
        return {
            "applied": applied,
            "failed": failed,
            "total": len(records),
            "applied_by_field": applied_by_field,
            "failed_details": failed_details[:10],  # Limit details to 10
        }
    
    # =========================================================================
    # Statistics
    # =========================================================================
    
    def get_enrichment_stats(self, coin_id: int | None = None) -> dict:
        """Get enrichment statistics."""
        query = self.db.query(EnrichmentRecord)
        
        if coin_id:
            query = query.filter(EnrichmentRecord.coin_id == coin_id)
        
        total = query.count()
        pending = query.filter(EnrichmentRecord.status == "pending").count()
        applied = query.filter(EnrichmentRecord.status == "applied").count()
        rejected = query.filter(EnrichmentRecord.status == "rejected").count()
        
        # By field
        field_counts = self.db.query(
            EnrichmentRecord.field_name,
            func.count(EnrichmentRecord.id)
        ).filter(
            EnrichmentRecord.status == "pending"
        )
        
        if coin_id:
            field_counts = field_counts.filter(EnrichmentRecord.coin_id == coin_id)
        
        field_counts = field_counts.group_by(EnrichmentRecord.field_name).all()
        
        return {
            "total": total,
            "pending": pending,
            "applied": applied,
            "rejected": rejected,
            "by_field": {f: c for f, c in field_counts},
        }
