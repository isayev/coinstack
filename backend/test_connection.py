from src.infrastructure.persistence.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM coins_v2'))
    print(f'Database connection OK. Coins count: {result.scalar()}')
