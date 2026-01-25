from unittest.mock import Mock
from src.application.commands.import_collection import ImportCollectionUseCase
from src.domain.importer import ICollectionImporter, ImportedCoinRow
from src.domain.repositories import ICoinRepository
from src.domain.coin import Category, Metal # Import Enum
from decimal import Decimal

def test_import_collection_success():
    # Arrange
    mock_repo = Mock(spec=ICoinRepository)
    mock_importer = Mock(spec=ICollectionImporter)
    
    # Stub importer return using VALID Enum values
    mock_importer.load.return_value = [
        ImportedCoinRow(
            row_number=1, 
            raw_data={},
            category="roman_imperial", # Valid Enum Value
            metal="silver",            # Valid Enum Value
            weight=Decimal("3.5"),
            diameter=Decimal("18.0"),
            issuer="Augustus",
            grade="VF",
            price=Decimal("100.00")
        )
    ]
    
    # Stub repo save to return input (identity)
    mock_repo.save.side_effect = lambda c: c
    
    use_case = ImportCollectionUseCase(mock_repo, mock_importer)
    
    # Act
    result = use_case.execute("dummy.xlsx")
    
    # Assert
    assert result.total_rows == 1
    assert result.imported == 1
    assert result.failed == 0
    mock_repo.save.assert_called_once()

def test_import_collection_failure_handling():
    # Arrange
    mock_repo = Mock(spec=ICoinRepository)
    mock_importer = Mock(spec=ICollectionImporter)
    
    mock_importer.load.return_value = [
        ImportedCoinRow(
            row_number=1,
            raw_data={},
            category="roman_imperial", # Valid
            metal="silver",            # Valid
            # Invalid weight to trigger ValueError in CreateCoinUseCase/Domain
            weight=Decimal("-5.0"), 
            diameter=Decimal("18.0"),
            issuer="Augustus"
        )
    ]
    
    use_case = ImportCollectionUseCase(mock_repo, mock_importer)
    
    # Act
    result = use_case.execute("dummy.xlsx")
    
    # Assert
    assert result.imported == 0
    assert result.failed == 1
    assert "Weight must be positive" in result.errors[0]