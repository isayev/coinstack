"""Unit tests for OCRE (RIC) catalog service - parse_reference and build_reconcile_query."""
import pytest
from src.infrastructure.services.catalogs.ocre import OCREService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ric_v_ii_325_query_no_edition_suffix():
    """RIC V.II 325: volume.part (V.2) must not get (2) edition suffix in OCRE query."""
    svc = OCREService()
    query = await svc.build_reconcile_query("RIC V.II 325", None)
    assert query["q0"]["query"] == "RIC V.2 325"
    assert "(2)" not in query["q0"]["query"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ric_iv_1_query_no_edition_suffix():
    """RIC IV.1 351: volume.part (IV.1) must not get (2) edition suffix."""
    svc = OCREService()
    query = await svc.build_reconcile_query("RIC IV.1 351", None)
    assert query["q0"]["query"] == "RIC IV.1 351"
    assert "(2)" not in query["q0"]["query"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ric_ii_single_volume_gets_edition():
    """RIC II 756 (no part): single volume gets (2) edition for OCRE."""
    svc = OCREService()
    query = await svc.build_reconcile_query("RIC II 756", None)
    assert "II(2)" in query["q0"]["query"] or "II(2) 756" == query["q0"]["query"]
    assert query["q0"]["query"] == "RIC II(2) 756"


@pytest.mark.unit
def test_parse_reference_ric_v_ii_325():
    """parse_reference returns volume V.2, number 325 for RIC V.II 325."""
    svc = OCREService()
    parsed = svc.parse_reference("RIC V.II 325")
    assert parsed is not None
    assert parsed["volume"] == "V.2"
    assert parsed["number"] == "325"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ric_v_325_with_authority_no_edition_suffix():
    """When context has ruler (e.g. Diocletian), OCRE query omits (2) so 'RIC V Diocletian 325' matches."""
    svc = OCREService()
    query = await svc.build_reconcile_query("RIC V 325", {"ruler": "Diocletian"})
    assert query["q0"]["query"] == "RIC V Diocletian 325"
    assert "(2)" not in query["q0"]["query"]
