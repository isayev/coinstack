"""
ReferenceSyncService - single write path for coin catalog references.

Syncs a list of references to reference_types and coin_references so that
LLM approve, manual update, import, and bulk enrich all persist refs consistently.
Uses the central parser from catalogs/parser for normalization.
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from src.infrastructure.persistence.orm import (
    CoinReferenceModel,
    ReferenceTypeModel,
)
from src.infrastructure.services.catalogs.catalog_systems import catalog_to_system
from src.infrastructure.services.catalogs.parser import (
    parse_catalog_reference,
    parse_catalog_reference_full,
    canonical,
)


def _normalize_ref_input(
    ref: Union[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Normalize a ref (string or dict) to dict with catalog, number, volume, local_ref, raw_text, is_primary, notes.
    local_ref is always canonical so that equivalent refs (e.g. 'RIC IV-1 351 b' and dict RIC IV.1 351b) dedupe to one row.
    """
    if isinstance(ref, str):
        parsed = parse_catalog_reference(ref.strip())
        full = parse_catalog_reference_full(ref.strip())
        local_ref = canonical(parsed) if (parsed.get("catalog") and parsed.get("number")) else ref.strip()
        return {
            "catalog": parsed.get("catalog") or "Unknown",
            "number": parsed.get("number") or "",
            "volume": parsed.get("volume"),
            "variant": full.subtype if full.system else None,
            "mint": getattr(full, "mint", None),
            "supplement": getattr(full, "supplement", None),
            "collection": getattr(full, "collection", None),
            "local_ref": local_ref,
            "raw_text": ref.strip(),
            "is_primary": False,
            "notes": None,
        }
    out = {
        "catalog": (ref.get("catalog") or "Unknown").strip(),
        "number": (ref.get("number") or "").strip(),
        "volume": ref.get("volume"),
        "variant": ref.get("variant"),
        "mint": ref.get("mint"),
        "supplement": ref.get("supplement"),
        "collection": ref.get("collection"),
        "raw_text": (ref.get("raw_text") or "").strip(),
        "is_primary": bool(ref.get("is_primary")),
        "notes": ref.get("notes"),
    }
    if not out["raw_text"] and (out["catalog"] or out["number"]):
        out["raw_text"] = f"{out['catalog']} {out.get('volume') or ''} {out['number']}".strip()
    out["local_ref"] = canonical(out) if (out["catalog"] and out["catalog"] != "Unknown" and out["number"]) else out["raw_text"]
    return out


def sync_coin_references(
    session: Session,
    coin_id: int,
    refs: List[Union[str, Dict[str, Any]]],
    source: str,
    *,
    external_ids: Optional[Dict[str, Optional[str]]] = None,
    merge: bool = False,
) -> None:
    """
    Sync references for a coin: find-or-create reference_types, upsert/delete coin_references.

    refs: List of reference strings or dicts with catalog, number, volume?, raw_text?, is_primary?, notes?.
    source: "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup".
    external_ids: Optional dict keyed by ref index or local_ref, value (external_id, external_url) for catalog lookup results.
    merge: If True, only add new refs and do not remove existing links (e.g. for LLM approve).
    """
    if not refs and not merge:
        # Remove all existing links for this coin
        session.query(CoinReferenceModel).filter(
            CoinReferenceModel.coin_id == coin_id
        ).delete()
        session.flush()
        return
    if not refs and merge:
        return

    normalized = [_normalize_ref_input(r) for r in refs]
    # Deduplicate by (system, local_ref) keeping first occurrence; local_ref is canonical
    seen: set = set()
    unique_refs: List[Dict[str, Any]] = []
    for n in normalized:
        system = catalog_to_system(n["catalog"])
        local_ref = n.get("local_ref") or n["raw_text"] or f"{n['catalog']} {n.get('volume') or ''} {n['number']}".strip()
        key = (system, local_ref)
        if key in seen:
            continue
        seen.add(key)
        unique_refs.append(n)

    # Mark first ref as primary if none set
    if unique_refs and not any(r.get("is_primary") for r in unique_refs):
        unique_refs[0]["is_primary"] = True

    ref_type_ids: List[int] = []
    ref_meta: List[Dict[str, Any]] = []  # is_primary, notes per ref

    for n in unique_refs:
        system = catalog_to_system(n["catalog"])
        local_ref = n.get("local_ref") or n["raw_text"] or f"{n['catalog']} {n.get('volume') or ''} {n['number']}".strip()
        volume = n.get("volume")
        number = n.get("number") or ""

        rt = (
            session.query(ReferenceTypeModel)
            .filter(
                ReferenceTypeModel.system == system,
                ReferenceTypeModel.local_ref == local_ref,
            )
            .first()
        )
        if not rt:
            rt = ReferenceTypeModel(
                system=system,
                local_ref=local_ref,
                volume=volume,
                number=number,
                variant=n.get("variant"),
                mint=n.get("mint"),
                supplement=n.get("supplement"),
                collection=n.get("collection"),
            )
            session.add(rt)
            session.flush()
        ref_type_ids.append(rt.id)
        ref_meta.append({"is_primary": n.get("is_primary", False), "notes": n.get("notes")})

    # Optional: set external_id/external_url from lookup results
    if external_ids is not None:
        for i, rt_id in enumerate(ref_type_ids):
            rt = session.get(ReferenceTypeModel, rt_id)
            if not rt:
                continue
            key = rt.local_ref
            val = external_ids.get(key) or external_ids.get(i)
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                rt.external_id = val[0]
                rt.external_url = val[1]
            elif isinstance(val, dict):
                rt.external_id = val.get("external_id")
                rt.external_url = val.get("external_url")
        session.flush()

    existing_links = (
        session.query(CoinReferenceModel)
        .filter(CoinReferenceModel.coin_id == coin_id)
        .all()
    )
    existing_by_rt: Dict[int, CoinReferenceModel] = {
        c.reference_type_id: c for c in existing_links if c.reference_type_id
    }

    target_rt_ids = set(ref_type_ids)
    if not merge:
        for link in existing_links:
            if link.reference_type_id not in target_rt_ids:
                session.delete(link)
        session.flush()

    for i, rt_id in enumerate(ref_type_ids):
        meta = ref_meta[i] if i < len(ref_meta) else {}
        if rt_id in existing_by_rt:
            link = existing_by_rt[rt_id]
            link.is_primary = meta.get("is_primary", False)
            link.notes = meta.get("notes")
            link.source = source
        else:
            link = CoinReferenceModel(
                coin_id=coin_id,
                reference_type_id=rt_id,
                is_primary=meta.get("is_primary", False),
                notes=meta.get("notes"),
                source=source,
            )
            session.add(link)
    session.flush()
