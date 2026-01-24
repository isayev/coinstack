"""Diff-oriented enrichment service for catalog data merging."""
import re
from typing import Any
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Coin
from app.services.catalogs.base import CatalogPayload


class Conflict(BaseModel):
    """A conflict between coin data and catalog data."""
    
    field: str
    current: Any
    catalog: Any
    note: str | None = None  # LLM-generated explanation


class EnrichmentDiff(BaseModel):
    """Result of comparing coin to catalog data."""
    
    fills: dict[str, Any] = {}           # Fields to auto-fill (were empty)
    conflicts: dict[str, Conflict] = {}  # Fields with mismatches
    unchanged: list[str] = []            # Fields that already match
    
    # Summary counts
    fill_count: int = 0
    conflict_count: int = 0
    unchanged_count: int = 0
    
    # Status
    has_changes: bool = False


class EnrichmentResult(BaseModel):
    """Result of applying enrichment."""
    
    success: bool
    coin_id: int
    diff: EnrichmentDiff
    applied_fills: list[str] = []
    applied_conflicts: list[str] = []
    error: str | None = None


# Field mapping from CatalogPayload to Coin model
FIELD_MAP = {
    # CatalogPayload field -> Coin model field
    "authority": "issuing_authority",
    "denomination": "denomination",
    "mint": None,  # Handled specially - creates/links Mint record
    "date_from": "mint_year_start",
    "date_to": "mint_year_end",
    "material": "metal",  # Needs enum conversion
    "obverse_description": "obverse_description",
    "obverse_legend": "obverse_legend",
    "reverse_description": "reverse_description",
    "reverse_legend": "reverse_legend",
}

# Fields that require special handling
SPECIAL_FIELDS = {"mint", "material"}


class DiffEnricher:
    """
    Diff-oriented enrichment service.
    
    Compares coin fields to catalog data and produces a structured diff:
    - fills: Empty fields that can be auto-filled
    - conflicts: Fields where values differ
    - unchanged: Fields that already match
    """
    
    def compute_diff(
        self,
        coin: Coin,
        catalog_data: CatalogPayload | dict
    ) -> EnrichmentDiff:
        """
        Compare coin fields to catalog data.
        
        Args:
            coin: The Coin model instance
            catalog_data: CatalogPayload or dict from catalog lookup
        
        Returns:
            EnrichmentDiff with fills, conflicts, and unchanged fields
        """
        if isinstance(catalog_data, dict):
            catalog_data = CatalogPayload(**catalog_data)
        
        fills = {}
        conflicts = {}
        unchanged = []
        
        for catalog_field, coin_field in FIELD_MAP.items():
            if coin_field is None:
                continue  # Skip specially handled fields
            
            catalog_value = getattr(catalog_data, catalog_field, None)
            
            if catalog_value is None:
                continue
            
            # Get coin value
            coin_value = getattr(coin, coin_field, None)
            
            # Normalize for comparison
            norm_coin = self._normalize_value(coin_value)
            norm_catalog = self._normalize_value(catalog_value)
            
            if norm_coin is None or norm_coin == "":
                # Coin field is empty - this is a fill
                fills[coin_field] = catalog_value
            elif norm_coin == norm_catalog:
                # Values match
                unchanged.append(coin_field)
            else:
                # Values differ - this is a conflict
                conflicts[coin_field] = Conflict(
                    field=coin_field,
                    current=coin_value,
                    catalog=catalog_value,
                    note=self._generate_conflict_note(coin_field, coin_value, catalog_value)
                )
        
        # Handle mint specially
        if catalog_data.mint:
            mint_name = coin.mint.name if coin.mint else None
            norm_mint = self._normalize_value(mint_name)
            norm_catalog_mint = self._normalize_value(catalog_data.mint)
            
            if norm_mint is None or norm_mint == "":
                fills["mint_name"] = catalog_data.mint
            elif norm_mint == norm_catalog_mint:
                unchanged.append("mint_name")
            else:
                conflicts["mint_name"] = Conflict(
                    field="mint_name",
                    current=mint_name,
                    catalog=catalog_data.mint,
                    note=f"Current mint '{mint_name}' differs from catalog '{catalog_data.mint}'"
                )
        
        diff = EnrichmentDiff(
            fills=fills,
            conflicts=conflicts,
            unchanged=unchanged,
            fill_count=len(fills),
            conflict_count=len(conflicts),
            unchanged_count=len(unchanged),
            has_changes=len(fills) > 0 or len(conflicts) > 0
        )
        
        return diff
    
    def apply_diff(
        self,
        db: Session,
        coin: Coin,
        diff: EnrichmentDiff,
        apply_conflicts: list[str] | None = None,
        dry_run: bool = False
    ) -> EnrichmentResult:
        """
        Apply enrichment diff to a coin.
        
        Args:
            db: Database session
            coin: The Coin model instance
            diff: The EnrichmentDiff to apply
            apply_conflicts: List of conflict field names to force-apply
            dry_run: If True, don't actually save changes
        
        Returns:
            EnrichmentResult with applied changes
        """
        apply_conflicts = apply_conflicts or []
        applied_fills = []
        applied_conflicts = []
        
        try:
            # Apply fills (always safe)
            for field, value in diff.fills.items():
                if field == "mint_name":
                    # Handle mint specially
                    if not dry_run:
                        from app.services.excel_import import get_or_create_mint
                        mint = get_or_create_mint(db, value)
                        coin.mint_id = mint.id
                    applied_fills.append(field)
                elif field == "metal":
                    # Convert to enum
                    if not dry_run:
                        from app.models.coin import Metal
                        try:
                            coin.metal = Metal(value.lower())
                        except ValueError:
                            pass  # Invalid metal value, skip
                    applied_fills.append(field)
                else:
                    if not dry_run:
                        setattr(coin, field, value)
                    applied_fills.append(field)
            
            # Apply approved conflicts
            for field in apply_conflicts:
                if field in diff.conflicts:
                    conflict = diff.conflicts[field]
                    if field == "mint_name":
                        if not dry_run:
                            from app.services.excel_import import get_or_create_mint
                            mint = get_or_create_mint(db, conflict.catalog)
                            coin.mint_id = mint.id
                        applied_conflicts.append(field)
                    elif field == "metal":
                        if not dry_run:
                            from app.models.coin import Metal
                            try:
                                coin.metal = Metal(conflict.catalog.lower())
                            except ValueError:
                                pass
                        applied_conflicts.append(field)
                    else:
                        if not dry_run:
                            setattr(coin, field, conflict.catalog)
                        applied_conflicts.append(field)
            
            if not dry_run:
                db.commit()
                db.refresh(coin)
            
            return EnrichmentResult(
                success=True,
                coin_id=coin.id,
                diff=diff,
                applied_fills=applied_fills,
                applied_conflicts=applied_conflicts
            )
            
        except Exception as e:
            db.rollback()
            return EnrichmentResult(
                success=False,
                coin_id=coin.id,
                diff=diff,
                error=str(e)
            )
    
    def _normalize_value(self, value: Any) -> str | None:
        """Normalize a value for comparison."""
        if value is None:
            return None
        
        # Convert to string and normalize
        s = str(value).strip().lower()
        
        # Remove common variations
        s = re.sub(r"\s+", " ", s)  # Normalize whitespace
        s = re.sub(r"[.,;:]+$", "", s)  # Remove trailing punctuation
        
        return s if s else None
    
    def _generate_conflict_note(
        self,
        field: str,
        current: Any,
        catalog: Any
    ) -> str:
        """Generate a note explaining a conflict."""
        
        # Field-specific notes
        if field == "denomination":
            return f"Your denomination '{current}' differs from catalog '{catalog}'"
        elif field == "issuing_authority":
            return f"Ruler/authority mismatch: you have '{current}', catalog has '{catalog}'"
        elif field in ("mint_year_start", "mint_year_end"):
            return f"Date mismatch: your date vs catalog date"
        elif field in ("obverse_legend", "reverse_legend"):
            return f"Legend text differs - catalog may have expanded/different reading"
        elif field in ("obverse_description", "reverse_description"):
            return f"Description differs - catalog may use standard terminology"
        
        return f"Value '{current}' differs from catalog '{catalog}'"
    
    def merge_multiple_payloads(
        self,
        payloads: list[CatalogPayload]
    ) -> CatalogPayload:
        """
        Merge multiple catalog payloads into one.
        
        Uses first non-null value for each field.
        Useful for multi-catalog synthesis.
        """
        if not payloads:
            return CatalogPayload()
        
        if len(payloads) == 1:
            return payloads[0]
        
        merged = {}
        for field in CatalogPayload.model_fields:
            for payload in payloads:
                value = getattr(payload, field, None)
                if value is not None:
                    merged[field] = value
                    break
        
        return CatalogPayload(**merged)


# Singleton instance
enricher = DiffEnricher()
