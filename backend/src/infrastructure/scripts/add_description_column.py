from sqlalchemy import text
from src.infrastructure.persistence.database import engine

def migrate():
    with engine.connect() as conn:
        try:
            print("Adding description column...")
            conn.execute(text("ALTER TABLE coins_v2 ADD COLUMN description VARCHAR"))
            print("Success.")
        except Exception as e:
            print(f"Column might already exist or error: {e}")

if __name__ == "__main__":
    migrate()
