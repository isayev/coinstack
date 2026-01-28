"""
Integration tests for LLM review API endpoints.

- GET /api/v2/llm/review
- POST /api/v2/llm/review/{coin_id}/dismiss
- POST /api/v2/llm/review/{coin_id}/approve
- POST /api/v2/llm/legend/transcribe/coin/{coin_id}
- POST /api/v2/llm/identify/coin/{coin_id}
"""
import json
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.infrastructure.web.main import create_app
from src.infrastructure.web.dependencies import get_db
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal,
    GradingDetails, GradingState, GradeService, AcquisitionDetails,
)
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.persistence.orm import CoinModel


@pytest.fixture
def app(db_session):
    """App with conftest's in-memory db_session."""
    def override_get_db():
        yield db_session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def _make_coin(**kw):
    """Minimal domain Coin for tests."""
    return Coin(
        id=kw.get("id"),
        category=kw.get("category", Category.ROMAN_IMPERIAL),
        metal=kw.get("metal", Metal.SILVER),
        dimensions=Dimensions(
            weight_g=kw.get("weight_g", Decimal("3.5")),
            diameter_mm=kw.get("diameter_mm", Decimal("18")),
        ),
        attribution=Attribution(
            issuer=kw.get("issuer", "Augustus"),
            year_start=kw.get("year_start"),
            year_end=kw.get("year_end"),
        ),
        grading=GradingDetails(
            grading_state=GradingState.SLABBED,
            grade=kw.get("grade", "VF"),
            service=GradeService.NGC,
            certification_number="test-001",
        ),
        acquisition=AcquisitionDetails(
            price=Decimal("100"),
            currency="USD",
            source="Test",
        ) if kw.get("acquisition") else None,
    )


# --- GET /api/v2/llm/review ---


def test_llm_review_empty_returns_200_and_empty_items(client: TestClient):
    """GET /api/v2/llm/review with no suggestions returns 200 and empty list."""
    r = client.get("/api/v2/llm/review", params={"limit": 100})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert data["items"] == []
    assert data["total"] == 0


def test_llm_review_with_suggestions_returns_item(client: TestClient, db_session):
    """GET /api/v2/llm/review returns coins that have llm_suggested_references or llm_suggested_rarity."""
    repo = SqlAlchemyCoinRepository(db_session)
    coin = _make_coin(issuer="Trajan")
    saved = repo.save(coin)
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin is not None
    orm_coin.llm_suggested_references = json.dumps(["RIC II 123"])
    orm_coin.llm_suggested_rarity = json.dumps({
        "rarity_code": "S",
        "rarity_description": "Scarce",
        "source": "RIC",
    })
    db_session.flush()

    r = client.get("/api/v2/llm/review", params={"limit": 100})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    items = [i for i in data["items"] if i["coin_id"] == saved.id]
    assert len(items) == 1
    assert "RIC II 123" in items[0]["suggested_references"]
    assert items[0]["rarity_info"] is not None
    assert items[0]["rarity_info"]["rarity_code"] == "S"


def test_llm_review_with_design_or_attribution_returns_item(client: TestClient, db_session):
    """GET /api/v2/llm/review returns coins that have llm_suggested_design or llm_suggested_attribution."""
    repo = SqlAlchemyCoinRepository(db_session)
    coin = _make_coin(issuer="Hadrian")
    saved = repo.save(coin)
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    orm_coin.llm_suggested_design = json.dumps({
        "obverse_legend": "IMP HADRIANUS AVG",
        "reverse_legend": "COS III",
        "exergue": "SC",
    })
    orm_coin.llm_suggested_attribution = json.dumps({
        "issuer": "Hadrian",
        "mint": "Rome",
        "denomination": "Denarius",
        "year_start": 128,
        "year_end": 131,
    })
    db_session.flush()

    r = client.get("/api/v2/llm/review", params={"limit": 100})
    assert r.status_code == 200
    data = r.json()
    items = [i for i in data["items"] if i["coin_id"] == saved.id]
    assert len(items) == 1
    assert items[0]["suggested_design"] is not None
    assert items[0]["suggested_design"]["obverse_legend"] == "IMP HADRIANUS AVG"
    assert items[0]["suggested_design"]["reverse_legend"] == "COS III"
    assert items[0]["suggested_design"]["exergue"] == "SC"
    assert items[0]["suggested_attribution"] is not None
    assert items[0]["suggested_attribution"]["issuer"] == "Hadrian"
    assert items[0]["suggested_attribution"]["mint"] == "Rome"
    assert items[0]["suggested_attribution"]["denomination"] == "Denarius"
    assert items[0]["suggested_attribution"]["year_start"] == 128
    assert items[0]["suggested_attribution"]["year_end"] == 131


# --- POST /api/v2/llm/review/{coin_id}/dismiss ---


def test_llm_review_dismiss_clears_suggestions(client: TestClient, db_session):
    """POST .../dismiss clears llm_suggested_references and llm_suggested_rarity."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Nero"))
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    orm_coin.llm_suggested_references = json.dumps(["RSC 456"])
    orm_coin.llm_suggested_rarity = json.dumps({"rarity_code": "R1"})
    db_session.flush()

    r = client.post(
        f"/api/v2/llm/review/{saved.id}/dismiss",
        params={"dismiss_references": "true", "dismiss_rarity": "true"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "dismissed"
    assert r.json()["coin_id"] == saved.id

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_references is None
    assert orm_coin.llm_suggested_rarity is None


def test_llm_review_dismiss_clears_design_and_attribution(client: TestClient, db_session):
    """POST .../dismiss with dismiss_design/dismiss_attribution clears llm_suggested_design and llm_suggested_attribution."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Antoninus"))
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    orm_coin.llm_suggested_design = json.dumps({"obverse_legend": "ANTONINVS AVG"})
    orm_coin.llm_suggested_attribution = json.dumps({"issuer": "Antoninus Pius", "mint": "Rome"})
    db_session.flush()

    r = client.post(
        f"/api/v2/llm/review/{saved.id}/dismiss",
        params={"dismiss_design": "true", "dismiss_attribution": "true"},
    )
    assert r.status_code == 200
    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_design is None
    assert orm_coin.llm_suggested_attribution is None


def test_llm_review_dismiss_nothing_to_dismiss_returns_400(client: TestClient, db_session):
    """POST .../dismiss with all dismiss flags false returns 400."""
    r = client.post(
        "/api/v2/llm/review/1/dismiss",
        params={
            "dismiss_references": "false",
            "dismiss_rarity": "false",
            "dismiss_design": "false",
            "dismiss_attribution": "false",
        },
    )
    assert r.status_code == 400


# --- POST /api/v2/llm/review/{coin_id}/approve ---


def test_llm_review_approve_applies_rarity_and_refs(client: TestClient, db_session):
    """POST .../approve applies rarity/refs and clears suggestions."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Domitian"))
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    orm_coin.llm_suggested_references = json.dumps(["RIC II 789"])
    orm_coin.llm_suggested_rarity = json.dumps({
        "rarity_code": "C",
        "rarity_description": "Common",
        "source": "RIC IV.1",
    })
    db_session.flush()

    r = client.post(f"/api/v2/llm/review/{saved.id}/approve")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["coin_id"] == saved.id
    assert body["applied_rarity"] is True
    assert body["applied_references"] == 1

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_references is None
    assert orm_coin.llm_suggested_rarity is None
    assert orm_coin.rarity in ("C", "Common")
    assert orm_coin.rarity_notes is not None


def test_llm_review_approve_coin_not_found_returns_404(client: TestClient):
    """POST .../approve for non-existent coin returns 404."""
    r = client.post("/api/v2/llm/review/999999/approve")
    assert r.status_code == 404


def test_llm_review_approve_no_suggestions_returns_400(client: TestClient, db_session):
    """POST .../approve when coin has no suggestions returns 400."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Titus"))
    db_session.flush()

    r = client.post(f"/api/v2/llm/review/{saved.id}/approve")
    assert r.status_code == 400
    assert "No pending" in r.json().get("detail", "")


def test_llm_review_approve_applies_design_and_attribution(client: TestClient, db_session):
    """POST .../approve applies design and attribution suggestions, returns applied_design/applied_attribution."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Old Issuer"))
    db_session.flush()

    orm_coin = db_session.get(CoinModel, saved.id)
    orm_coin.llm_suggested_design = json.dumps({
        "obverse_legend": "IMP CAES TRAIAN",
        "reverse_legend": "COS V",
        "exergue": "SC",
    })
    orm_coin.llm_suggested_attribution = json.dumps({
        "issuer": "Trajan",
        "mint": "Rome",
        "denomination": "Denarius",
        "year_start": 112,
        "year_end": 116,
    })
    db_session.flush()

    r = client.post(f"/api/v2/llm/review/{saved.id}/approve")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "approved"
    assert body["applied_design"] is True
    assert body["applied_attribution"] is True

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_design is None
    assert orm_coin.llm_suggested_attribution is None
    assert orm_coin.obverse_legend == "IMP CAES TRAIAN"
    assert orm_coin.reverse_legend == "COS V"
    assert orm_coin.exergue == "SC"
    assert orm_coin.issuer == "Trajan"
    assert orm_coin.mint == "Rome"
    assert orm_coin.denomination == "Denarius"
    assert orm_coin.year_start == 112
    assert orm_coin.year_end == 116


# --- POST /api/v2/llm/legend/transcribe/coin/{coin_id} ---


def test_transcribe_legend_for_coin_no_image_returns_400(client: TestClient, db_session):
    """POST .../legend/transcribe/coin/{id} returns 400 when coin has no primary image."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Test"))
    db_session.flush()
    r = client.post(f"/api/v2/llm/legend/transcribe/coin/{saved.id}")
    assert r.status_code == 400
    assert "primary image" in (r.json().get("detail") or "").lower()


def test_transcribe_legend_for_coin_not_found_returns_404(client: TestClient):
    """POST .../legend/transcribe/coin/999999 returns 404 when coin does not exist."""
    r = client.post("/api/v2/llm/legend/transcribe/coin/999999")
    assert r.status_code == 404


# --- POST /api/v2/llm/identify/coin/{coin_id} ---


def test_identify_coin_for_coin_no_image_returns_400(client: TestClient, db_session):
    """POST .../identify/coin/{id} returns 400 when coin has no primary image."""
    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Test"))
    db_session.flush()
    r = client.post(f"/api/v2/llm/identify/coin/{saved.id}")
    assert r.status_code == 400
    assert "primary image" in (r.json().get("detail") or "").lower()


def test_identify_coin_for_coin_not_found_returns_404(client: TestClient):
    """POST .../identify/coin/999999 returns 404 when coin does not exist."""
    r = client.post("/api/v2/llm/identify/coin/999999")
    assert r.status_code == 404


# --- Success paths (mocked LLM via dependency override + patched image resolver) ---


class _TranscribeResult:
    obverse_legend = "IMP CAES AVG"
    obverse_legend_expanded = "Imperator Caesar Augustus"
    reverse_legend = "COS III"
    reverse_legend_expanded = "Consul III"
    exergue = "SC"
    uncertain_portions = []
    confidence = 0.9
    cost_usd = 0.0


def test_transcribe_legend_for_coin_success_saves_design(client: TestClient, app, db_session):
    """POST .../legend/transcribe/coin/{id} with mocked image+LLM saves llm_suggested_design and returns 200."""
    from src.infrastructure.web.routers.llm import get_llm_service

    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Test"))
    db_session.flush()

    mock_svc = MagicMock()
    mock_svc.transcribe_legend = AsyncMock(return_value=_TranscribeResult())
    app.dependency_overrides[get_llm_service] = lambda: mock_svc

    try:
        with patch("src.infrastructure.web.routers.llm._resolve_coin_primary_image_b64", new_callable=AsyncMock, return_value="dummy_b64"):
            r = client.post(f"/api/v2/llm/legend/transcribe/coin/{saved.id}")
    finally:
        app.dependency_overrides.pop(get_llm_service, None)

    assert r.status_code == 200
    data = r.json()
    assert data.get("obverse_legend") == "IMP CAES AVG"
    assert data.get("exergue") == "SC"

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_design is not None
    design = json.loads(orm_coin.llm_suggested_design)
    assert design["obverse_legend"] == "IMP CAES AVG"
    assert design["reverse_legend"] == "COS III"
    assert design["exergue"] == "SC"
    assert orm_coin.llm_enriched_at is not None


class _IdentifyResult:
    ruler = "Gallienus"
    denomination = "Antoninianus"
    mint = "Rome"
    date_range = "268–270"
    obverse_description = "Radiate bust right"
    reverse_description = "Laetitia standing left"
    suggested_references = ["RIC V.1 123"]
    confidence = 0.85
    cost_usd = 0.0


def test_identify_coin_for_coin_success_saves_attribution_and_design(client: TestClient, app, db_session):
    """POST .../identify/coin/{id} with mocked image+LLM saves llm_suggested_attribution, design delta, refs."""
    from src.infrastructure.web.routers.llm import get_llm_service

    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Test"))
    db_session.flush()

    mock_svc = MagicMock()
    mock_svc.identify_coin = AsyncMock(return_value=_IdentifyResult())
    app.dependency_overrides[get_llm_service] = lambda: mock_svc

    try:
        with patch("src.infrastructure.web.routers.llm._resolve_coin_primary_image_b64", new_callable=AsyncMock, return_value="dummy_b64"):
            r = client.post(f"/api/v2/llm/identify/coin/{saved.id}")
    finally:
        app.dependency_overrides.pop(get_llm_service, None)

    assert r.status_code == 200
    data = r.json()
    assert data.get("ruler") == "Gallienus"
    assert data.get("mint") == "Rome"
    assert "268" in (data.get("date_range") or "")

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    assert orm_coin.llm_suggested_attribution is not None
    attr = json.loads(orm_coin.llm_suggested_attribution)
    assert attr["issuer"] == "Gallienus"
    assert attr["mint"] == "Rome"
    assert attr["denomination"] == "Antoninianus"
    assert attr["year_start"] == 268
    assert attr["year_end"] == 270
    assert orm_coin.llm_suggested_design is not None
    design = json.loads(orm_coin.llm_suggested_design)
    assert design.get("obverse_description") == "Radiate bust right"
    assert design.get("reverse_description") == "Laetitia standing left"
    assert orm_coin.llm_suggested_references is not None
    refs = json.loads(orm_coin.llm_suggested_references)
    assert "RIC V.1 123" in refs
    assert orm_coin.llm_enriched_at is not None


def test_transcribe_after_identify_preserves_descriptions(client: TestClient, app, db_session):
    """Transcribe merges into llm_suggested_design; identify-then-transcribe keeps descriptions."""
    from src.infrastructure.web.routers.llm import get_llm_service

    repo = SqlAlchemyCoinRepository(db_session)
    saved = repo.save(_make_coin(issuer="Test"))
    db_session.flush()

    # 1) Run identify: stores obverse/reverse descriptions (and attribution/refs)
    mock_svc = MagicMock()
    mock_svc.identify_coin = AsyncMock(return_value=_IdentifyResult())
    app.dependency_overrides[get_llm_service] = lambda: mock_svc
    try:
        with patch("src.infrastructure.web.routers.llm._resolve_coin_primary_image_b64", new_callable=AsyncMock, return_value="dummy_b64"):
            r1 = client.post(f"/api/v2/llm/identify/coin/{saved.id}")
    finally:
        app.dependency_overrides.pop(get_llm_service, None)
    assert r1.status_code == 200

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    design_after_identify = json.loads(orm_coin.llm_suggested_design or "{}")
    assert design_after_identify.get("obverse_description") == "Radiate bust right"
    assert design_after_identify.get("reverse_description") == "Laetitia standing left"

    # 2) Run transcribe: should merge legends into existing design, not overwrite
    mock_svc = MagicMock()
    mock_svc.transcribe_legend = AsyncMock(return_value=_TranscribeResult())
    app.dependency_overrides[get_llm_service] = lambda: mock_svc
    try:
        with patch("src.infrastructure.web.routers.llm._resolve_coin_primary_image_b64", new_callable=AsyncMock, return_value="dummy_b64"):
            r2 = client.post(f"/api/v2/llm/legend/transcribe/coin/{saved.id}")
    finally:
        app.dependency_overrides.pop(get_llm_service, None)
    assert r2.status_code == 200

    db_session.expire_all()
    orm_coin = db_session.get(CoinModel, saved.id)
    design_after_transcribe = json.loads(orm_coin.llm_suggested_design or "{}")
    # Legends from transcribe
    assert design_after_transcribe.get("obverse_legend") == "IMP CAES AVG"
    assert design_after_transcribe.get("reverse_legend") == "COS III"
    assert design_after_transcribe.get("exergue") == "SC"
    # Descriptions from identify must still be present (merge, not overwrite)
    assert design_after_transcribe.get("obverse_description") == "Radiate bust right"
    assert design_after_transcribe.get("reverse_description") == "Laetitia standing left"
