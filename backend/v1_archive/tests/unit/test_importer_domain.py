import pytest
from src.domain.importer import ImportedCoinRow

class TestImporterDefinitions:
    def test_imported_row_structure(self):
        row = ImportedCoinRow(
            row_number=1,
            raw_data={"Weight": "3.5g"},
            weight=None
        )
        assert row.row_number == 1
