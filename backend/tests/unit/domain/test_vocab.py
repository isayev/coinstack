import pytest
from datetime import date
from src.domain.vocab import Issuer, Mint, IssuerType

def test_issuer_creation():
    issuer = Issuer(
        id=1,
        canonical_name="Augustus",
        nomisma_id="augustus",
        issuer_type=IssuerType.EMPEROR,
        reign_start=-27,
        reign_end=14
    )
    assert issuer.canonical_name == "Augustus"
    assert issuer.reign_start == -27
    assert issuer.reign_end == 14
    assert issuer.is_active_in_year(0)
    assert not issuer.is_active_in_year(20)

def test_issuer_validation():
    with pytest.raises(ValueError, match="Reign start cannot be after reign end"):
        Issuer(
            id=1,
            canonical_name="Time Traveler",
            nomisma_id="time_traveler",
            issuer_type=IssuerType.EMPEROR,
            reign_start=100,
            reign_end=50
        )

def test_mint_creation():
    mint = Mint(
        id=1,
        canonical_name="Roma",
        nomisma_id="rome",
        active_from=-300,
        active_to=476
    )
    assert mint.canonical_name == "Roma"
    assert mint.is_active_in_year(100)

def test_mint_validation():
    with pytest.raises(ValueError, match="Active start cannot be after active end"):
        Mint(
            id=1,
            canonical_name="Impossible Mint",
            nomisma_id="impossible",
            active_from=500,
            active_to=400
        )
