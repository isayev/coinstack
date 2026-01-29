"""RPC Online (Roman Provincial Coinage) HTML scraper.

Fetches a single type page (e.g. /coins/1/4374), parses the table into CatalogPayload.
Polite: robots.txt check, rate limit, one request per reference. Graceful degradation:
returns partial payload when only some fields parse; structure-change detection.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from src.infrastructure.services.catalogs.base import CatalogPayload
from src.infrastructure.services.catalogs.robots_cache import (
    enforce_rate_limit,
    is_allowed,
)
from src.infrastructure.services.catalogs.parsers.base import roman_to_arabic

logger = logging.getLogger(__name__)

RPC_BASE_HOST = "rpc.ashmus.ox.ac.uk"
# Versioned selectors: table rows with first cell = label, second = value (or link text)
RPC_TABLE_ROW_LABELS = [
    "Volume", "Number", "Province", "Region", "City", "Reign", "Person (obv.)",
    "Issue", "Dating", "Obverse inscription", "Obverse design", "Reverse inscription",
    "Reverse design", "Metal", "Average diameter", "Average weight", "Axis",
]


@dataclass
class RPCScrapeResult:
    """Result of scraping one RPC type page."""
    payload: Optional[CatalogPayload] = None
    status: str = "url_only"  # full, partial, url_only, failed, disallowed
    fields_found: List[str] = field(default_factory=list)
    fields_missing: List[str] = field(default_factory=list)
    degradation_reason: Optional[str] = None
    message: Optional[str] = None


def _parse_table_to_dict(html: str) -> Tuple[dict, List[str], List[str]]:
    """
    Parse RPC type page HTML table into label -> value dict.
    Returns (data, fields_found, fields_missing).
    """
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    # RPC page: table with rows like <tr><td>Reign</td><td><a>Tiberius</a></td></tr>
    tables = soup.find_all("table")
    for table in tables:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = (cells[0].get_text() or "").strip()
                value_cell = cells[1]
                # Prefer link text if present (e.g. <a>Tiberius</a>)
                link = value_cell.find("a")
                if link and link.get_text(strip=True):
                    value = link.get_text(strip=True)
                else:
                    value = value_cell.get_text(separator=" ", strip=True)
                if label and value:
                    data[label] = value
    fields_found = list(data.keys())
    fields_missing = [l for l in RPC_TABLE_ROW_LABELS if l not in data]
    return data, fields_found, fields_missing


def _map_table_to_payload(data: dict) -> CatalogPayload:
    """Map parsed table data to CatalogPayload."""
    def get(k: str) -> Optional[str]:
        v = data.get(k)
        return (v.strip() if v else None) or None

    # Reign -> authority; City or Province -> mint; Dating -> date_string
    authority = get("Reign") or get("Person (obv.)")
    mint = get("City") or get("Province") or get("Region")
    date_string = get("Dating")
    obverse_description = get("Obverse design")
    obverse_legend = get("Obverse inscription")
    reverse_description = get("Reverse design")
    reverse_legend = get("Reverse inscription")
    material = get("Metal")

    return CatalogPayload(
        authority=authority,
        mint=mint,
        date_string=date_string,
        obverse_description=obverse_description,
        obverse_legend=obverse_legend,
        reverse_description=reverse_description,
        reverse_legend=reverse_legend,
        material=material,
    )


def _structure_match_ratio(fields_found: List[str]) -> float:
    """Return ratio of expected labels that were found (for structure-change detection)."""
    if not RPC_TABLE_ROW_LABELS:
        return 1.0
    found_set = {f.strip().lower() for f in fields_found}
    expected = {f.strip().lower() for f in RPC_TABLE_ROW_LABELS}
    matches = len(found_set & expected)
    return matches / len(expected) if expected else 1.0


def parse_rpc_html(html: str) -> RPCScrapeResult:
    """
    Parse RPC type page HTML into CatalogPayload.
    Returns RPCScrapeResult with payload (full/partial), fields_found, fields_missing.
    """
    if not html or not html.strip():
        return RPCScrapeResult(
            status="failed",
            degradation_reason="empty_response",
            message="Empty page response",
        )
    try:
        data, fields_found, fields_missing = _parse_table_to_dict(html)
    except Exception as e:
        logger.warning("RPC HTML parse error: %s", e)
        return RPCScrapeResult(
            status="failed",
            degradation_reason="parse_error",
            message=str(e),
        )
    ratio = _structure_match_ratio(fields_found)
    if ratio < 0.3:
        logger.warning(
            "RPC HTML structure change detected: only %.0f%% of expected rows found",
            ratio * 100,
        )
        return RPCScrapeResult(
            status="failed",
            fields_found=fields_found,
            fields_missing=fields_missing,
            degradation_reason="structure_change",
            message="Page structure may have changed; selectors need update",
        )
    payload = _map_table_to_payload(data)
    # Determine if we have meaningful data (tier 1: authority or mint or date)
    has_tier1 = bool(payload.authority or payload.mint or payload.date_string)
    has_descriptions = bool(payload.obverse_description or payload.reverse_description)
    if has_tier1 or has_descriptions:
        status = "full" if ratio >= 0.5 and (has_tier1 or has_descriptions) else "partial"
        return RPCScrapeResult(
            payload=payload,
            status=status,
            fields_found=fields_found,
            fields_missing=fields_missing,
            message="Partial data retrieved; some fields unavailable" if status == "partial" else None,
        )
    return RPCScrapeResult(
        payload=payload,
        status="partial",
        fields_found=fields_found,
        fields_missing=fields_missing,
        message="Basic type data retrieved; descriptions unavailable",
    )


def build_rpc_type_url(volume: str, number: str) -> str:
    """Build RPC type page URL. Prefer arabic volume (site uses /coins/1/4374)."""
    vol_clean = (volume or "").strip().upper()
    num_clean = (number or "").strip().split("/")[0].split(" ")[0]
    if not num_clean:
        return ""
    try:
        # Check that every character is a valid Roman numeral (I,V,X,L,C,D,M)
        if vol_clean and all(c in "IVXLCDM" for c in vol_clean):
            arabic = roman_to_arabic(vol_clean)
            return f"https://{RPC_BASE_HOST}/coins/{arabic}/{num_clean}"
    except Exception:
        pass
    return f"https://{RPC_BASE_HOST}/coins/{volume}/{number}"


async def fetch_rpc_type_page(
    url: str,
    user_agent: str,
    timeout_sec: float = 20.0,
    rate_limit_sec: float = 10.0,
) -> RPCScrapeResult:
    """
    Fetch one RPC type page and parse into CatalogPayload.
    Checks robots.txt and enforces rate limit before request.
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.netloc or RPC_BASE_HOST

    allowed = await is_allowed(user_agent, url)
    if not allowed:
        logger.info("RPC fetch disallowed by robots.txt: %s", url)
        return RPCScrapeResult(
            status="disallowed",
            degradation_reason="robots_txt",
            message="Fetch disallowed by robots.txt; use link for manual lookup",
        )

    await enforce_rate_limit(host, rate_limit_sec)

    try:
        async with httpx.AsyncClient(
            timeout=timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        ) as client:
            r = await client.get(url)
            r.raise_for_status()
            html = r.text
    except httpx.HTTPStatusError as e:
        logger.warning("RPC fetch HTTP error %s: %s", e.response.status_code, url)
        return RPCScrapeResult(
            status="failed",
            degradation_reason=f"http_{e.response.status_code}",
            message=f"Catalog returned {e.response.status_code}",
        )
    except httpx.TimeoutException:
        logger.warning("RPC fetch timeout: %s", url)
        return RPCScrapeResult(
            status="failed",
            degradation_reason="timeout",
            message="Catalog site slow or unavailable; use link to open in browser",
        )
    except Exception as e:
        logger.warning("RPC fetch error: %s", e)
        return RPCScrapeResult(
            status="failed",
            degradation_reason="request_error",
            message=str(e),
        )

    return parse_rpc_html(html)
