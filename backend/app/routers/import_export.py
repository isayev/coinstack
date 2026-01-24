"""Import/Export API router."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
from app.database import get_db
from app.services.excel_import import import_collection_file

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/collection")
async def import_collection(
    file: UploadFile = File(...),
    dry_run: bool = False,
    db: Session = Depends(get_db),
):
    """Import collection from CSV or Excel file."""
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload CSV or Excel file.",
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    try:
        result = await import_collection_file(db, tmp_path, dry_run=dry_run)
        return result.to_dict()
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()
