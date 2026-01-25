import pytest
from pathlib import Path
import openpyxl
from datetime import date
from decimal import Decimal
from src.infrastructure.importers.excel_importer import ExcelImporter
from src.domain.importer import ImportedCoinRow

@pytest.fixture
def sample_excel_file(tmp_path):
    """Creates a temporary Excel file for testing."""
    file_path = tmp_path / "test_coins.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # Headers
    ws.append(["Category", "Issuer", "Weight", "Diameter", "Price", "Date"])
    # Row 1
    ws.append(["Roman Imperial", "Augustus", "3.52", "18.5", "250.00", "2023-01-15"])
    # Row 2 (Missing optional data)
    ws.append(["Greek", "Athens", 17.2, 24.0, None, None])
    
    wb.save(file_path)
    return str(file_path)

def test_excel_importer_reads_rows(sample_excel_file):
    importer = ExcelImporter()
    rows = importer.load(sample_excel_file)
    
    assert len(rows) == 2
    
    # Check Row 1
    row1 = rows[0]
    assert row1.row_number == 2 # 1-based index, skipping header
    assert row1.raw_data["Category"] == "Roman Imperial"
    assert row1.category == "Roman Imperial"
    assert row1.weight == Decimal("3.52")
    assert row1.price == Decimal("250.00")
    # Note: openpyxl reads dates as datetime objects usually, logic needs to handle that
    
    # Check Row 2
    row2 = rows[1]
    assert row2.issuer == "Athens"
    assert row2.weight == Decimal("17.2")
    assert row2.price is None
