import pytest
from unittest.mock import AsyncMock, MagicMock
from src.infrastructure.services.vocab_sync import VocabSyncService
from src.infrastructure.persistence.models_vocab import IssuerModel

# Sample SPARQL response from Nomisma
NOMISMA_RESPONSE = {
    "results": {
        "bindings": [
            {
                "uri": {"value": "http://nomisma.org/id/augustus"},
                "label": {"value": "Augustus"},
                "start": {"value": "-0027"},
                "end": {"value": "0014"}
            },
            {
                "uri": {"value": "http://nomisma.org/id/tiberius"},
                "label": {"value": "Tiberius"},
                "start": {"value": "0014"},
                "end": {"value": "0037"}
            }
        ]
    }
}

@pytest.mark.asyncio
async def test_sync_issuers():
    # Mock DB Session
    mock_session = MagicMock()
    # Mock query to return None (no existing issuers)
    mock_session.scalar.return_value = None 

    # Mock HTTP Client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = NOMISMA_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response

    service = VocabSyncService(session=mock_session, client=mock_client)
    
    stats = await service.sync_nomisma_issuers()

    assert stats["added"] == 2
    assert stats["updated"] == 0
    
    # Verify DB calls
    assert mock_session.add.call_count == 2
    mock_session.commit.assert_called()

@pytest.mark.asyncio
async def test_parse_year():
    service = VocabSyncService(MagicMock(), MagicMock())
    assert service._parse_year("-0027") == -27
    assert service._parse_year("0014") == 14
    assert service._parse_year(None) is None
    assert service._parse_year("invalid") is None
