from typing import List
from dataclasses import dataclass
from src.domain.coin import Coin, Category, Metal, Dimensions, Attribution, GradingDetails, GradingState, AcquisitionDetails
from src.domain.repositories import ICoinRepository
from src.domain.importer import ICollectionImporter
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO

@dataclass
class ImportResult:
    total_rows: int
    imported: int
    failed: int
    errors: List[str]

class ImportCollectionUseCase:
    def __init__(self, repository: ICoinRepository, importer: ICollectionImporter):
        self.repository = repository
        self.importer = importer
        self.create_coin = CreateCoinUseCase(repository)

    def execute(self, file_path: str) -> ImportResult:
        rows = self.importer.load(file_path)
        success_count = 0
        errors = []

        for row in rows:
            try:
                # Map ImportedRow -> CreateCoinDTO
                # This logic handles defaults and basic type conversions
                
                # Default "Raw" if not specified
                grading_state = GradingState.RAW.value 
                
                # Basic DTO creation
                dto = CreateCoinDTO(
                    category=row.category or "Unknown",
                    metal=row.metal or "Unknown",
                    weight_g=row.weight or 0, # Validator will catch 0 later if strict
                    diameter_mm=row.diameter or 0,
                    issuer=row.issuer or "Unknown",
                    grading_state=grading_state,
                    grade=row.grade or "Unknown",
                    acquisition_price=row.price,
                    acquisition_date=row.date
                )
                
                self.create_coin.execute(dto)
                success_count += 1
                
            except Exception as e:
                errors.append(f"Row {row.row_number}: {str(e)}")

        return ImportResult(
            total_rows=len(rows),
            imported=success_count,
            failed=len(errors),
            errors=errors
        )
