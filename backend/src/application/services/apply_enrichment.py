"""
ApplyEnrichmentService - single place that applies suggested value to a coin field.

Maps API-level field_name to domain value objects (Attribution, GradingDetails, Design)
and uses dataclasses.replace to produce updated Coin before persisting.
"""
from dataclasses import replace
from typing import Any, List, Optional

from src.domain.coin import Coin, Attribution, GradingDetails, Design
from src.application.services.grade_normalizer import normalize_grade_for_storage
from src.domain.enrichment import (
    ALLOWED_FIELDS,
    EnrichmentApplication,
    ApplicationResult,
)
from src.domain.repositories import ICoinRepository


def _coerce_value(field_name: str, raw: Any) -> Any:
    """Coerce raw value to the type expected by the field."""
    if raw is None:
        return None
    if field_name in ("year_start", "year_end"):
        if isinstance(raw, int):
            return raw
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    if field_name == "grade":
        return str(raw) if raw is not None else ""
    return str(raw) if raw is not None else ""


def _apply_field(coin: Coin, field_name: str, new_value: Any) -> Coin:
    """
    Build updated Coin with one field set. Uses replace() on value objects.
    Raises ValueError if field is unknown or value invalid.
    """
    if field_name not in ALLOWED_FIELDS:
        raise ValueError(f"Field '{field_name}' is not enrichable")
    val = _coerce_value(field_name, new_value)

    if field_name in ("issuer", "mint", "year_start", "year_end"):
        att = coin.attribution
        updated_att = Attribution(
            issuer=val if field_name == "issuer" else att.issuer,
            issuer_id=att.issuer_id,
            mint=val if field_name == "mint" else att.mint,
            mint_id=att.mint_id,
            year_start=val if field_name == "year_start" else att.year_start,
            year_end=val if field_name == "year_end" else att.year_end,
        )
        return replace(coin, attribution=updated_att)

    if field_name == "grade":
        g = coin.grading
        updated_grading = GradingDetails(
            grading_state=g.grading_state,
            grade=normalize_grade_for_storage(val) or val or g.grade,
            service=g.service,
            certification_number=g.certification_number,
            strike=g.strike,
            surface=g.surface,
        )
        return replace(coin, grading=updated_grading)

    if field_name in ("obverse_legend", "reverse_legend", "obverse_description", "reverse_description"):
        d = coin.design or Design()
        updated_design = Design(
            obverse_legend=val if field_name == "obverse_legend" else d.obverse_legend,
            obverse_description=val if field_name == "obverse_description" else d.obverse_description,
            reverse_legend=val if field_name == "reverse_legend" else d.reverse_legend,
            reverse_description=val if field_name == "reverse_description" else d.reverse_description,
            exergue=d.exergue,
        )
        return replace(coin, design=updated_design)

    raise ValueError(f"Field '{field_name}' is not enrichable")


def _get_old_value(coin: Coin, field_name: str) -> Any:
    """Return current value of field on coin for ApplicationResult.old_value."""
    if field_name in ("issuer", "mint", "year_start", "year_end"):
        att = coin.attribution
        return getattr(att, field_name, None)
    if field_name == "grade":
        return coin.grading.grade
    if field_name in ("obverse_legend", "reverse_legend", "obverse_description", "reverse_description"):
        d = coin.design
        return getattr(d, field_name, None) if d else None
    return None


class ApplyEnrichmentService:
    """Single source of truth for 'apply suggested value to coin field'."""

    def __init__(self, coin_repo: ICoinRepository):
        self._repo = coin_repo

    def apply(self, application: EnrichmentApplication) -> ApplicationResult:
        """
        Apply one enrichment to the coin. Returns ApplicationResult with success/error.
        """
        if application.field_name not in ALLOWED_FIELDS:
            return ApplicationResult(
                success=False,
                field_name=application.field_name,
                old_value=None,
                new_value=application.new_value,
                error=f"Field '{application.field_name}' is not enrichable",
            )
        coin = self._repo.get_by_id(application.coin_id)
        if not coin:
            return ApplicationResult(
                success=False,
                field_name=application.field_name,
                old_value=None,
                new_value=application.new_value,
                error="Coin not found",
            )
        old_value = _get_old_value(coin, application.field_name)
        try:
            updated = _apply_field(coin, application.field_name, application.new_value)
            self._repo.save(updated)
            return ApplicationResult(
                success=True,
                field_name=application.field_name,
                old_value=old_value,
                new_value=application.new_value,
            )
        except ValueError as e:
            return ApplicationResult(
                success=False,
                field_name=application.field_name,
                old_value=old_value,
                new_value=application.new_value,
                error=str(e),
            )

    def apply_batch(
        self,
        applications: List[EnrichmentApplication],
    ) -> List[ApplicationResult]:
        """Apply multiple enrichments; returns one result per application."""
        return [self.apply(app) for app in applications]
