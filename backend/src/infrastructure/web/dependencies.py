from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.domain.repositories import ICoinRepository

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_coin_repo(db: Session = Depends(get_db)) -> ICoinRepository:
    return SqlAlchemyCoinRepository(db)
