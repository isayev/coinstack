"""
Bulk catalog enrichment background task.

Resolves coin set, runs CatalogRegistry.lookup per coin reference,
builds diff (fills/conflicts), and applies fills via ApplyEnrichmentService.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.infrastructure.services.catalogs.registry import CatalogRegistry
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.persistence.orm import EnrichmentJobModel
from src.application.services.apply_enrichment import ApplyEnrichmentService
from src.domain.enrichment import EnrichmentApplication

logger = logging.getLogger(__name__)


def _ref_string_from_coin(coin: Any) -> Optional[str]:
    """Get first reference string from coin for catalog lookup."""
    if not coin or not getattr(coin, "references", None):
        return None
    for ref in coin.references:
        raw = getattr(ref, "raw_text", None) or (
            f"{getattr(ref, 'catalog', '')} {getattr(ref, 'volume', '') or ''} {getattr(ref, 'number', '')}".strip()
        )
        if raw:
            return raw
    return None


def _payload_to_fills(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map CatalogPayload keys to coin field names (fills)."""
    fills = {}
    if payload.get("authority"):
        fills["issuer"] = payload["authority"]
    if payload.get("mint"):
        fills["mint"] = payload["mint"]
    if payload.get("obverse_legend"):
        fills["obverse_legend"] = payload["obverse_legend"]
    if payload.get("reverse_legend"):
        fills["reverse_legend"] = payload["reverse_legend"]
    if payload.get("date_from") is not None:
        fills["year_start"] = payload["date_from"]
    if payload.get("date_to") is not None:
        fills["year_end"] = payload["date_to"]
    return fills


async def run_bulk_enrich(
    job_id: str,
    request: Any,  # BulkEnrichRequest-like
    session_factory: Any,
) -> None:
    """
    Background task: resolve coins, run catalog lookup per coin, update job and optionally apply fills.
    Uses its own session from session_factory; commits on success.
    """
    dry_run = getattr(request, "dry_run", True)
    max_coins = getattr(request, "max_coins", 50) or 50
    coin_ids = getattr(request, "coin_ids", None)
    category = getattr(request, "category", None)

    session = session_factory()
    try:
        job = session.get(EnrichmentJobModel, job_id)
        if not job:
            logger.warning("Enrichment job %s not found in DB; ensure job is committed before background task runs", job_id)
            return
        logger.info("Bulk enrich job %s starting (total=%s)", job_id, getattr(request, "coin_ids", None) or "filter-based")
        now = datetime.now(timezone.utc)
        job.status = "running"
        job.started_at = now
        session.flush()

        repo = SqlAlchemyCoinRepository(session)
        apply_service = ApplyEnrichmentService(repo)
        if coin_ids:
            coins = [repo.get_by_id(i) for i in coin_ids]
            coins = [c for c in coins if c is not None]
        else:
            filters = {}
            if category:
                filters["category"] = category
            coins = repo.get_all(limit=max_coins, filters=filters or None)
        total = len(coins)
        job.total = total
        session.flush()

        results_list: List[Dict[str, Any]] = []
        updated_count = 0
        conflict_count = 0
        not_found_count = 0
        error_count = 0

        for i, coin in enumerate(coins):
            ref_str = _ref_string_from_coin(coin)
            job.progress = i + 1
            if not ref_str:
                not_found_count += 1
                results_list.append({"coin_id": coin.id, "status": "no_reference"})
                session.flush()
                continue
            try:
                system = getattr(request, "reference_system", None) or "ric"
                result = await CatalogRegistry.lookup(
                    system=system,
                    reference=ref_str,
                    context={"ruler": getattr(coin.attribution, "issuer", None) if coin.attribution else None},
                )
            except Exception as e:
                logger.exception(f"Catalog lookup failed for coin {coin.id}: {e}")
                error_count += 1
                results_list.append({"coin_id": coin.id, "status": "error"})
                session.flush()
                continue
            if result.status == "not_found":
                not_found_count += 1
                results_list.append({"coin_id": coin.id, "status": "not_found"})
            elif result.status == "success" and result.payload:
                fills = _payload_to_fills(result.payload)
                applied_any = False
                if fills and not dry_run:
                    for field_name, value in fills.items():
                        app = EnrichmentApplication(
                            coin_id=coin.id,
                            field_name=field_name,
                            new_value=value,
                            source_type="catalog",
                            source_id=getattr(result, "external_id", None),
                        )
                        r = apply_service.apply(app)
                        if r.success:
                            applied_any = True
                    if applied_any:
                        updated_count += 1
                status_str = "success" if (applied_any or (fills and dry_run)) else ("unchanged" if fills else "no_fills")
                results_list.append({"coin_id": coin.id, "status": status_str})
            else:
                results_list.append({"coin_id": coin.id, "status": str(result.status)})
            session.flush()

        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.progress = total
        job.updated = updated_count
        job.conflicts = conflict_count
        job.not_found = not_found_count
        job.errors = error_count
        job.result_summary = json.dumps(results_list)
        session.commit()
        logger.info(
            "Bulk enrich job %s completed: updated=%s conflicts=%s not_found=%s errors=%s",
            job_id, updated_count, conflict_count, not_found_count, error_count,
        )
    except Exception as e:
        logger.exception(f"Bulk enrich job {job_id} failed: {e}")
        try:
            job = session.get(EnrichmentJobModel, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                session.commit()
        except Exception:
            session.rollback()
        raise
    finally:
        session.close()
