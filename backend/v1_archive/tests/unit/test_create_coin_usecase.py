from unittest.mock import Mock
from decimal import Decimal
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.coin import Coin, Category, Metal
from src.domain.repositories import ICoinRepository

def test_create_coin_use_case():
    # Arrange
    mock_repo = Mock(spec=ICoinRepository)
    def save_side_effect(coin):
        # Return same coin but with ID
        return Coin(
            id=123,
            category=coin.category,
            metal=coin.metal,
            dimensions=coin.dimensions,
            attribution=coin.attribution,
            grading=coin.grading,
            acquisition=coin.acquisition
        )
    mock_repo.save.side_effect = save_side_effect
    
    use_case = CreateCoinUseCase(mock_repo)
    
    dto = CreateCoinDTO(
        category="roman_imperial",
        metal="silver",
        weight_g=Decimal("3.0"),
        diameter_mm=Decimal("18.0"),
        issuer="Nero",
        grading_state="raw",
        grade="VF"
    )

    # Act
    result = use_case.execute(dto)

    # Assert
    assert result.id == 123
    assert result.grading.grade == "VF"
    mock_repo.save.assert_called_once()