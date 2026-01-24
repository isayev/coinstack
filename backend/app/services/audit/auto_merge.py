"""
Auto-Merge Service for Auction Data Enrichment.

Implements safe automatic merging of auction data into coin records with:
- Rollback support via FieldHistory
- User-verified field protection
- Conflict classification and trust-based resolution
- Dry-run preview capability
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4
from dataclasses import dataclass, field as dataclass_field
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.coin import Coin
from app.models.auction_data import AuctionData
from app.models.field_history import FieldHistory
from app.services.audit.trust_config import (
    get_field_trust_numeric,
    USER_VERIFIED_TRUST,
    USER_TRUST,
    normalize_source,
)
from app.services.audit.conflict_classifier import (
    classify_conflict,
    is_safe_conflict,
    ConflictType,
)

logger = logging.getLogger(__name__)


def make_json_serializable(value: Any) -> Any:
    """Convert a value to a JSON-serializable type."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [make_json_serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: make_json_serializable(v) for k, v in value.items()}
    return value


# Fields that can be enriched from auction data
ENRICHABLE_FIELDS = {
    # Physical measurements
    "weight_g": {"auction_field": "weight_g", "type": float},
    "diameter_mm": {"auction_field": "diameter_mm", "type": float},
    "thickness_mm": {"auction_field": "thickness_mm", "type": float},
    "die_axis": {"auction_field": "die_axis", "type": int},
    
    # Grading (including Heritage/NGC slab details)
    "grade": {"auction_field": "grade", "type": str},
    "grade_service": {"auction_field": "grade_service", "type": str},
    "certification_number": {"auction_field": "certification_number", "type": str},
    "strike_score": {"auction_field": "strike_score", "type": str},      # NGC "4/5"
    "surface_score": {"auction_field": "surface_score", "type": str},    # NGC "5/5"
    
    # Descriptions and legends
    "obverse_description": {"auction_field": "obverse_description", "type": str},
    "reverse_description": {"auction_field": "reverse_description", "type": str},
    "obverse_legend": {"auction_field": "obverse_legend", "type": str},
    "reverse_legend": {"auction_field": "reverse_legend", "type": str},
    "exergue": {"auction_field": "exergue", "type": str},
    
    # Attribution
    "mint": {"auction_field": "mint", "type": str},
    "ruler": {"auction_field": "ruler", "type": str},
    "reign_dates": {"auction_field": "reign_dates", "type": str},
    "denomination": {"auction_field": "denomination", "type": str},
    "mint_year_start": {"auction_field": "mint_year_start", "type": int},
    "mint_year_end": {"auction_field": "mint_year_end", "type": int},
    
    # References
    "primary_reference": {"auction_field": "primary_reference", "type": str},
    
    # Pricing (from acquisition)
    "acquisition_price": {"auction_field": "hammer_price", "type": float},
    "estimate_low": {"auction_field": "estimate_low", "type": float},
    "estimate_high": {"auction_field": "estimate_high", "type": float},
}

# Minimum trust difference to auto-update on conflicts
MIN_TRUST_DIFFERENCE = 20


@dataclass
class FieldChange:
    """Record of a single field change."""
    field: str
    old_value: Any
    new_value: Any
    old_source: Optional[str]
    new_source: str
    trust_old: int
    trust_new: int
    conflict_type: Optional[ConflictType] = None
    reason: str = ""


@dataclass
class MergeResult:
    """Result of a merge operation."""
    batch_id: str
    coin_id: int
    auction_data_id: Optional[int]
    auto_filled: list[FieldChange] = dataclass_field(default_factory=list)
    auto_updated: list[FieldChange] = dataclass_field(default_factory=list)
    skipped: list[dict] = dataclass_field(default_factory=list)
    flagged: list[FieldChange] = dataclass_field(default_factory=list)
    errors: list[str] = dataclass_field(default_factory=list)
    
    @property
    def total_changes(self) -> int:
        return len(self.auto_filled) + len(self.auto_updated)
    
    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "coin_id": self.coin_id,
            "auction_data_id": self.auction_data_id,
            "auto_filled": [
                {
                    "field": c.field,
                    "value": c.new_value,
                    "source": c.new_source,
                    "trust": c.trust_new,
                }
                for c in self.auto_filled
            ],
            "auto_updated": [
                {
                    "field": c.field,
                    "old": c.old_value,
                    "new": c.new_value,
                    "old_source": c.old_source,
                    "new_source": c.new_source,
                    "conflict_type": c.conflict_type.value if c.conflict_type else None,
                    "reason": c.reason,
                }
                for c in self.auto_updated
            ],
            "skipped": self.skipped,
            "flagged": [
                {
                    "field": c.field,
                    "current": c.old_value,
                    "auction": c.new_value,
                    "current_source": c.old_source,
                    "auction_source": c.new_source,
                    "trust_current": c.trust_old,
                    "trust_auction": c.trust_new,
                    "conflict_type": c.conflict_type.value if c.conflict_type else None,
                    "reason": c.reason,
                }
                for c in self.flagged
            ],
            "errors": self.errors,
            "total_changes": self.total_changes,
            "rollback_available": self.total_changes > 0,
        }


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    batch_id: str
    restored_count: int
    fields_affected: list[str]
    coins_affected: list[int]
    
    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "restored": self.restored_count,
            "fields_affected": self.fields_affected,
            "coins_affected": self.coins_affected,
        }


class AutoMergeService:
    """
    Service for automatically merging auction data into coin records.
    
    Merge Rules:
    1. If field has user_verified=True -> SKIP (absolute protection)
    2. If coin field is empty -> AUTO-FILL (regardless of trust)
    3. If conflict is safe type (tolerance, minor, additional) -> AUTO-UPDATE
    4. If auction trust > current trust + MIN_TRUST_DIFFERENCE -> AUTO-UPDATE
    5. Otherwise -> FLAG for manual review
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_field_source_info(self, coin: Coin, field: str) -> tuple[Any, Optional[str], bool, int]:
        """
        Get current value and source info for a field.
        
        Returns:
            (value, source, user_verified, trust_level)
        """
        value = getattr(coin, field, None)
        
        # Get source info from field_sources JSON
        field_sources = coin.field_sources or {}
        source_info = field_sources.get(field, {})
        
        source = source_info.get("source")
        user_verified = source_info.get("user_verified", False)
        
        # Calculate trust
        if user_verified:
            trust = USER_VERIFIED_TRUST
        elif source:
            trust = get_field_trust_numeric(source, field)
        else:
            trust = USER_TRUST  # Default for user-entered data
        
        return value, source, user_verified, trust
    
    def _update_field_source(
        self, 
        coin: Coin, 
        field: str, 
        value: Any,
        source: str,
        source_id: Optional[str],
        trust_level: int,
        batch_id: str,
        changed_by: str,
        previous_value: Any = None,
        previous_source: Optional[str] = None,
    ) -> None:
        """Update field_sources JSON for a field."""
        # Create new dict to ensure SQLAlchemy detects the change
        field_sources = dict(coin.field_sources or {})
        
        field_sources[field] = {
            "value": make_json_serializable(value),
            "source": source,
            "source_id": source_id,
            "trust_level": trust_level,
            "set_at": datetime.utcnow().isoformat(),
            "set_by": changed_by,
            "batch_id": batch_id,
            "user_verified": False,
            "previous": {
                "value": make_json_serializable(previous_value),
                "source": previous_source,
            }
        }
        
        coin.field_sources = field_sources
        flag_modified(coin, "field_sources")
    
    def _record_change(
        self,
        coin_id: int,
        field: str,
        old_value: Any,
        new_value: Any,
        old_source: Optional[str],
        new_source: str,
        change_type: str,
        batch_id: str,
        changed_by: str,
        trust_old: int,
        trust_new: int,
        conflict_type: Optional[ConflictType] = None,
        reason: str = "",
    ) -> FieldHistory:
        """Record a field change in history."""
        history = FieldHistory(
            coin_id=coin_id,
            field_name=field,
            old_value={"value": make_json_serializable(old_value)},
            new_value={"value": make_json_serializable(new_value)},
            old_source=old_source,
            new_source=new_source,
            change_type=change_type,
            changed_at=datetime.utcnow(),
            changed_by=changed_by,
            batch_id=batch_id,
            trust_old=trust_old,
            trust_new=trust_new,
            conflict_type=conflict_type.value if conflict_type else None,
            reason=reason,
        )
        self.db.add(history)
        return history
    
    def merge_auction_to_coin(
        self,
        coin_id: int,
        auction_data_id: Optional[int] = None,
        dry_run: bool = False,
        batch_id: Optional[str] = None,
        changed_by: str = "system:auto_merge",
    ) -> MergeResult:
        """
        Merge auction data into a coin record.
        
        Args:
            coin_id: ID of the coin to update
            auction_data_id: Specific auction data to merge (optional, uses linked data if None)
            dry_run: If True, don't actually apply changes
            batch_id: Batch ID for grouping (auto-generated if None)
            changed_by: Who/what initiated the change
            
        Returns:
            MergeResult with details of what was/would be changed
        """
        batch_id = batch_id or str(uuid4())
        result = MergeResult(
            batch_id=batch_id,
            coin_id=coin_id,
            auction_data_id=auction_data_id,
        )
        
        # Get coin
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            result.errors.append(f"Coin {coin_id} not found")
            return result
        
        # Get auction data
        if auction_data_id:
            auction = self.db.query(AuctionData).filter(AuctionData.id == auction_data_id).first()
            if not auction:
                result.errors.append(f"AuctionData {auction_data_id} not found")
                return result
            auctions = [auction]
        else:
            # Use all linked auction data
            auctions = self.db.query(AuctionData).filter(
                AuctionData.coin_id == coin_id
            ).all()
        
        if not auctions:
            result.errors.append(f"No auction data found for coin {coin_id}")
            return result
        
        # Build context for trust calculations
        context = {
            "is_slabbed": bool(coin.grade_service),
        }
        
        # Process each enrichable field
        for coin_field, config in ENRICHABLE_FIELDS.items():
            auction_field = config["auction_field"]
            field_type = config["type"]
            
            # Get current value and source
            current_value, current_source, user_verified, current_trust = \
                self._get_field_source_info(coin, coin_field)
            
            # Rule 1: Skip user-verified fields (absolute protection)
            if user_verified:
                result.skipped.append({
                    "field": coin_field,
                    "reason": "user_verified",
                    "current_value": current_value,
                })
                continue
            
            # Find best auction value for this field
            best_auction_value = None
            best_auction_source = None
            best_auction_source_id = None
            best_auction_trust = 0
            
            for auction in auctions:
                auction_value = getattr(auction, auction_field, None)
                if auction_value is None or auction_value == "":
                    continue
                
                source = normalize_source(auction.auction_house or "unknown")
                trust = get_field_trust_numeric(source, coin_field, context)
                
                if trust > best_auction_trust:
                    best_auction_value = auction_value
                    best_auction_source = source
                    best_auction_source_id = auction.source_lot_id or str(auction.id)
                    best_auction_trust = trust
            
            # No auction data for this field
            if best_auction_value is None:
                continue
            
            # Convert type if needed
            try:
                if field_type == float and best_auction_value is not None:
                    best_auction_value = float(best_auction_value)
                elif field_type == int and best_auction_value is not None:
                    best_auction_value = int(best_auction_value)
            except (ValueError, TypeError):
                continue
            
            # Rule 2: Auto-fill empty fields
            is_empty = current_value is None or current_value == "" or current_value == []
            if is_empty:
                change = FieldChange(
                    field=coin_field,
                    old_value=current_value,
                    new_value=best_auction_value,
                    old_source=current_source,
                    new_source=best_auction_source,
                    trust_old=current_trust,
                    trust_new=best_auction_trust,
                    reason="Empty field filled",
                )
                result.auto_filled.append(change)
                
                if not dry_run:
                    setattr(coin, coin_field, best_auction_value)
                    self._update_field_source(
                        coin, coin_field, best_auction_value,
                        best_auction_source, best_auction_source_id,
                        best_auction_trust, batch_id, changed_by,
                        current_value, current_source,
                    )
                    self._record_change(
                        coin_id, coin_field, current_value, best_auction_value,
                        current_source, best_auction_source, "auto_fill",
                        batch_id, changed_by, current_trust, best_auction_trust,
                        reason="Empty field filled",
                    )
                continue
            
            # Values differ - classify conflict
            conflict_type = classify_conflict(coin_field, current_value, best_auction_value)
            
            # Rule 3: Auto-update safe conflicts
            if is_safe_conflict(conflict_type):
                change = FieldChange(
                    field=coin_field,
                    old_value=current_value,
                    new_value=best_auction_value,
                    old_source=current_source,
                    new_source=best_auction_source,
                    trust_old=current_trust,
                    trust_new=best_auction_trust,
                    conflict_type=conflict_type,
                    reason=f"Safe conflict: {conflict_type.value}",
                )
                result.auto_updated.append(change)
                
                if not dry_run:
                    setattr(coin, coin_field, best_auction_value)
                    self._update_field_source(
                        coin, coin_field, best_auction_value,
                        best_auction_source, best_auction_source_id,
                        best_auction_trust, batch_id, changed_by,
                        current_value, current_source,
                    )
                    self._record_change(
                        coin_id, coin_field, current_value, best_auction_value,
                        current_source, best_auction_source, "auto_update",
                        batch_id, changed_by, current_trust, best_auction_trust,
                        conflict_type, f"Safe conflict: {conflict_type.value}",
                    )
                continue
            
            # Rule 4: Auto-update if trust difference is significant
            trust_diff = best_auction_trust - current_trust
            if trust_diff >= MIN_TRUST_DIFFERENCE:
                change = FieldChange(
                    field=coin_field,
                    old_value=current_value,
                    new_value=best_auction_value,
                    old_source=current_source,
                    new_source=best_auction_source,
                    trust_old=current_trust,
                    trust_new=best_auction_trust,
                    conflict_type=conflict_type,
                    reason=f"Trust difference: {best_auction_source}({best_auction_trust}) > {current_source or 'user'}({current_trust})",
                )
                result.auto_updated.append(change)
                
                if not dry_run:
                    setattr(coin, coin_field, best_auction_value)
                    self._update_field_source(
                        coin, coin_field, best_auction_value,
                        best_auction_source, best_auction_source_id,
                        best_auction_trust, batch_id, changed_by,
                        current_value, current_source,
                    )
                    self._record_change(
                        coin_id, coin_field, current_value, best_auction_value,
                        current_source, best_auction_source, "auto_update",
                        batch_id, changed_by, current_trust, best_auction_trust,
                        conflict_type, f"Trust winner: +{trust_diff}",
                    )
                continue
            
            # Rule 5: Flag for review
            change = FieldChange(
                field=coin_field,
                old_value=current_value,
                new_value=best_auction_value,
                old_source=current_source,
                new_source=best_auction_source,
                trust_old=current_trust,
                trust_new=best_auction_trust,
                conflict_type=conflict_type,
                reason=f"Conflict requires review: {conflict_type.value}, trust diff={trust_diff}",
            )
            result.flagged.append(change)
        
        # Commit changes if not dry run
        if not dry_run and result.total_changes > 0:
            self.db.commit()
            logger.info(f"Auto-merged {result.total_changes} fields for coin {coin_id} (batch {batch_id})")
        
        return result
    
    def rollback_batch(self, batch_id: str) -> RollbackResult:
        """
        Rollback all changes from a batch operation.
        
        Args:
            batch_id: The batch ID to rollback
            
        Returns:
            RollbackResult with details of restored fields
        """
        # Get all changes for this batch in reverse order
        changes = self.db.query(FieldHistory).filter(
            FieldHistory.batch_id == batch_id,
            FieldHistory.change_type.in_(["auto_fill", "auto_update", "manual"]),
        ).order_by(FieldHistory.changed_at.desc()).all()
        
        if not changes:
            return RollbackResult(
                batch_id=batch_id,
                restored_count=0,
                fields_affected=[],
                coins_affected=[],
            )
        
        rollback_batch_id = str(uuid4())
        fields_affected = set()
        coins_affected = set()
        
        for change in changes:
            # Get the coin
            coin = self.db.query(Coin).filter(Coin.id == change.coin_id).first()
            if not coin:
                continue
            
            # Restore old value
            old_value = change.old_value.get("value") if change.old_value else None
            setattr(coin, change.field_name, old_value)
            
            # Update field_sources (create new dict to ensure SQLAlchemy detects change)
            field_sources = dict(coin.field_sources or {})
            if change.field_name in field_sources:
                field_sources[change.field_name] = {
                    "value": make_json_serializable(old_value),
                    "source": change.old_source,
                    "trust_level": change.trust_old,
                    "set_at": datetime.utcnow().isoformat(),
                    "set_by": "system:rollback",
                    "batch_id": rollback_batch_id,
                    "user_verified": False,
                    "previous": field_sources[change.field_name].get("previous"),
                }
            coin.field_sources = field_sources
            flag_modified(coin, "field_sources")
            
            # Record the rollback
            self._record_change(
                change.coin_id,
                change.field_name,
                change.new_value.get("value") if change.new_value else None,
                old_value,
                change.new_source,
                change.old_source,
                "rollback",
                rollback_batch_id,
                "system:rollback",
                change.trust_new or 0,
                change.trust_old or 0,
                reason=f"Rollback of batch {batch_id}",
            )
            
            fields_affected.add(change.field_name)
            coins_affected.add(change.coin_id)
        
        self.db.commit()
        
        logger.info(f"Rolled back batch {batch_id}: {len(changes)} changes across {len(coins_affected)} coins")
        
        return RollbackResult(
            batch_id=batch_id,
            restored_count=len(changes),
            fields_affected=list(fields_affected),
            coins_affected=list(coins_affected),
        )
    
    def verify_field(
        self,
        coin_id: int,
        field: str,
        user_note: Optional[str] = None,
    ) -> bool:
        """
        Mark a field as user-verified, protecting it from auto-updates.
        
        Args:
            coin_id: Coin ID
            field: Field name to verify
            user_note: Optional note about the verification
            
        Returns:
            True if successful
        """
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            return False
        
        # Create new dict to ensure SQLAlchemy detects the change
        field_sources = dict(coin.field_sources or {})
        current_info = dict(field_sources.get(field, {}))
        
        current_info["user_verified"] = True
        current_info["verified_at"] = datetime.utcnow().isoformat()
        if user_note:
            current_info["user_note"] = user_note
        
        field_sources[field] = current_info
        coin.field_sources = field_sources
        flag_modified(coin, "field_sources")
        
        self.db.commit()
        
        logger.info(f"Field {field} marked as user-verified for coin {coin_id}")
        return True
    
    def unverify_field(self, coin_id: int, field: str) -> bool:
        """Remove user verification from a field."""
        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
        if not coin:
            return False
        
        # Create new dict to ensure SQLAlchemy detects the change
        field_sources = dict(coin.field_sources or {})
        if field in field_sources:
            field_info = dict(field_sources[field])
            field_info["user_verified"] = False
            field_info.pop("verified_at", None)
            field_sources[field] = field_info
            coin.field_sources = field_sources
            flag_modified(coin, "field_sources")
            self.db.commit()
        
        return True


def get_auto_merge_service(db: Session) -> AutoMergeService:
    """Factory function for AutoMergeService."""
    return AutoMergeService(db)
