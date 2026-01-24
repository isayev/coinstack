"""Settings and data management API router."""
import os
import csv
import io
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.config import get_settings
from app.models.coin import Coin

router = APIRouter(prefix="/settings", tags=["settings"])
settings = get_settings()


class DatabaseInfo(BaseModel):
    """Database information."""
    size_mb: float
    coin_count: int
    last_modified: str
    path: str


@router.get("/database-info", response_model=DatabaseInfo)
async def get_database_info(db: Session = Depends(get_db)):
    """Get database file information."""
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    
    size_bytes = 0
    last_modified = "Unknown"
    
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
        last_modified = mtime.strftime("%Y-%m-%d %H:%M:%S")
    
    coin_count = db.query(func.count(Coin.id)).scalar() or 0
    
    return DatabaseInfo(
        size_mb=round(size_bytes / (1024 * 1024), 2),
        coin_count=coin_count,
        last_modified=last_modified,
        path=str(db_path),
    )


@router.get("/backup")
async def download_backup():
    """Download database backup file."""
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    
    if not db_path.exists():
        return {"error": "Database file not found"}
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"coinstack_backup_{timestamp}.db"
    
    return FileResponse(
        path=str(db_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.get("/export-csv")
async def export_to_csv(db: Session = Depends(get_db)):
    """Export collection to CSV."""
    coins = db.query(Coin).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    headers = [
        "ID", "Category", "Denomination", "Metal", "Issuing Authority",
        "Portrait Subject", "Reign Start", "Reign End", "Mint Year Start", 
        "Mint Year End", "Weight (g)", "Diameter (mm)", "Die Axis",
        "Obverse Legend", "Obverse Description", "Reverse Legend", 
        "Reverse Description", "Exergue", "Grade", "Grade Service",
        "Acquisition Date", "Acquisition Price", "Acquisition Source",
        "Storage Location", "Rarity", "Personal Notes", "Created At"
    ]
    writer.writerow(headers)
    
    # Data rows
    for coin in coins:
        writer.writerow([
            coin.id,
            coin.category.value if coin.category else "",
            coin.denomination,
            coin.metal.value if coin.metal else "",
            coin.issuing_authority,
            coin.portrait_subject or "",
            coin.reign_start or "",
            coin.reign_end or "",
            coin.mint_year_start or "",
            coin.mint_year_end or "",
            float(coin.weight_g) if coin.weight_g else "",
            float(coin.diameter_mm) if coin.diameter_mm else "",
            coin.die_axis or "",
            coin.obverse_legend or "",
            coin.obverse_description or "",
            coin.reverse_legend or "",
            coin.reverse_description or "",
            coin.exergue or "",
            coin.grade or "",
            coin.grade_service.value if coin.grade_service else "",
            coin.acquisition_date.isoformat() if coin.acquisition_date else "",
            float(coin.acquisition_price) if coin.acquisition_price else "",
            coin.acquisition_source or "",
            coin.storage_location or "",
            coin.rarity.value if coin.rarity else "",
            coin.personal_notes or "",
            coin.created_at.isoformat() if coin.created_at else "",
        ])
    
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=coinstack_export_{timestamp}.csv"
        }
    )
