from typing import List, Any, Optional
import openpyxl
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from src.domain.importer import ICollectionImporter, ImportedCoinRow

class ExcelImporter(ICollectionImporter):
    def load(self, file_path: str) -> List[ImportedCoinRow]:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        rows_data = list(ws.iter_rows(values_only=True))
        if not rows_data:
            return []
            
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows_data[0])]
        
        imported_rows = []
        
        # Start from index 1 (skip headers)
        for idx, row_values in enumerate(rows_data[1:], start=2):
            # Create raw map
            raw_map = {}
            for h_idx, header in enumerate(headers):
                if h_idx < len(row_values):
                    raw_map[header] = row_values[h_idx]
            
            # Skip empty rows
            if not any(raw_map.values()):
                continue

            # Parse normalized fields
            imported_rows.append(ImportedCoinRow(
                row_number=idx,
                raw_data=raw_map,
                category=self._get_str(raw_map, ["Category", "Type"]),
                issuer=self._get_str(raw_map, ["Issuer", "Ruler", "City"]),
                weight=self._get_decimal(raw_map, ["Weight", "Weight (g)"]),
                diameter=self._get_decimal(raw_map, ["Diameter", "Size", "Diameter (mm)"]),
                price=self._get_decimal(raw_map, ["Price", "Cost", "Acquisition Price"]),
                date=self._get_date(raw_map, ["Date", "Acquired", "Acquisition Date"])
            ))
            
        return imported_rows

    def _get_str(self, data: dict, keys: List[str]) -> Optional[str]:
        for k in keys:
            if k in data and data[k] is not None:
                return str(data[k]).strip()
        return None

    def _get_decimal(self, data: dict, keys: List[str]) -> Optional[Decimal]:
        for k in keys:
            val = data.get(k)
            if val is not None:
                try:
                    return Decimal(str(val))
                except (InvalidOperation, ValueError):
                    pass
        return None

    def _get_date(self, data: dict, keys: List[str]) -> Optional[date]:
        for k in keys:
            val = data.get(k)
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, date):
                return val
            # Could add string parsing here if needed
            if isinstance(val, str):
                try:
                    # Basic ISO support
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    pass
        return None
