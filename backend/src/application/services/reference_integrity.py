"""
Reference integrity check for catalog references.

Used by scripts/check_reference_integrity.py and GET /api/catalog/integrity.
"""

import json
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.infrastructure.persistence.orm import CoinModel, CoinReferenceModel, ReferenceTypeModel


def _is_non_empty_json_array(val: str | None) -> bool:
    if not val or not val.strip():
        return False
    stripped = val.strip()
    if stripped in ("null", "[]", "{}"):
        return False
    if stripped.startswith("["):
        try:
            arr = json.loads(stripped)
            return isinstance(arr, list) and len(arr) > 0
        except (json.JSONDecodeError, TypeError):
            return bool(stripped)
    return False


def run_integrity_check(session: Session, include_orphans: bool = False) -> Dict[str, Any]:
    """
    Run reference integrity checks. Returns a dict suitable for JSON or summary.

    - Coins with non-empty llm_suggested_references but zero coin_references links.
    - Optionally: reference_types with no coin_references (orphans).
    """
    all_coins_with_suggestions = (
        session.query(CoinModel.id, CoinModel.llm_suggested_references)
        .filter(
            CoinModel.llm_suggested_references.isnot(None),
            CoinModel.llm_suggested_references != "",
        )
        .all()
    )
    coins_with_pending_refs = [
        (c.id, c.llm_suggested_references)
        for c in all_coins_with_suggestions
        if _is_non_empty_json_array(c.llm_suggested_references)
    ]
    coin_ids_pending = [c[0] for c in coins_with_pending_refs]

    ref_counts: Dict[int, int] = {}
    if coin_ids_pending:
        rows = (
            session.query(CoinReferenceModel.coin_id, func.count(CoinReferenceModel.id).label("ref_count"))
            .filter(CoinReferenceModel.coin_id.in_(coin_ids_pending))
            .group_by(CoinReferenceModel.coin_id)
            .all()
        )
        ref_counts = {r.coin_id: r.ref_count for r in rows}

    coins_pending_not_applied = [
        coin_id for coin_id in coin_ids_pending if ref_counts.get(coin_id, 0) == 0
    ]

    report: Dict[str, Any] = {
        "coins_with_pending_suggestions": len(coin_ids_pending),
        "coins_pending_with_zero_applied_refs": len(coins_pending_not_applied),
        "coin_ids_pending_not_applied": coins_pending_not_applied[:100],
        "summary": (
            f"{len(coins_pending_not_applied)} coin(s) have pending LLM reference suggestions but no applied references."
            if coins_pending_not_applied
            else "No integrity issues: all coins with pending suggestions have applied references or none."
        ),
    }

    if include_orphans:
        orphan_rt = (
            session.query(ReferenceTypeModel.id, ReferenceTypeModel.system, ReferenceTypeModel.local_ref)
            .outerjoin(CoinReferenceModel, CoinReferenceModel.reference_type_id == ReferenceTypeModel.id)
            .group_by(ReferenceTypeModel.id)
            .having(func.count(CoinReferenceModel.id) == 0)
            .all()
        )
        report["orphan_reference_types_count"] = len(orphan_rt)
        report["orphan_reference_types_sample"] = [
            {"id": r.id, "system": r.system, "local_ref": r.local_ref} for r in orphan_rt[:50]
        ]

    return report
