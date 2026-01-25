import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, declarative_base

# We need to import the Base from the real app to ensure compatibility
# But for this isolated test, if we can't easily import the app's Base, 
# we might need to mock or rely on the one we create.
# However, the goal is to test the *actual* model definition.

from src.infrastructure.persistence.models import Base
from src.infrastructure.persistence.models_vocab import IssuerModel, MintModel

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_issuer_model_persistence(db_session):
    issuer = IssuerModel(
        canonical_name="Augustus",
        nomisma_id="augustus",
        issuer_type="emperor",
        reign_start=-27,
        reign_end=14
    )
    db_session.add(issuer)
    db_session.commit()

    stmt = select(IssuerModel).where(IssuerModel.canonical_name == "Augustus")
    result = db_session.scalar(stmt)

    assert result is not None
    assert result.nomisma_id == "augustus"
    assert result.reign_start == -27

def test_mint_model_persistence(db_session):
    mint = MintModel(
        canonical_name="Roma",
        nomisma_id="rome"
    )
    db_session.add(mint)
    db_session.commit()

    result = db_session.scalar(select(MintModel).where(MintModel.nomisma_id == "rome"))
    assert result.canonical_name == "Roma"

def test_issuer_alias_persistence(db_session):
    from src.infrastructure.persistence.models_vocab import IssuerAliasModel
    
    # Create issuer first
    issuer = IssuerModel(
        canonical_name="Hadrian",
        nomisma_id="hadrian",
        issuer_type="emperor"
    )
    db_session.add(issuer)
    db_session.commit()

    # Add alias
    alias = IssuerAliasModel(
        issuer_id=issuer.id,
        alias="Hadrianus",
        normalized_form="hadrianus"
    )
    db_session.add(alias)
    db_session.commit()

    # Verify relationship
    loaded_issuer = db_session.scalar(select(IssuerModel).where(IssuerModel.canonical_name == "Hadrian"))
    assert len(loaded_issuer.aliases) == 1
    assert loaded_issuer.aliases[0].alias == "Hadrianus"
