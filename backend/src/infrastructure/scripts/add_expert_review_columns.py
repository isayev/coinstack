"""
Migration: Add Expert Review Fields to coins_v2
-------------------------------------------------
Adds denomination, portrait_subject, and design fields that were missing from the table.

Run: python -m src.infrastructure.scripts.add_expert_review_columns
"""
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

def migrate():
    columns_to_add = [
        ("denomination", "VARCHAR"),
        ("portrait_subject", "VARCHAR"),
        ("obverse_legend", "TEXT"),
        ("obverse_description", "TEXT"),
        ("reverse_legend", "TEXT"),
        ("reverse_description", "TEXT"),
        ("exergue", "VARCHAR"),
        ("obverse_legend_expanded", "TEXT"),
        ("reverse_legend_expanded", "TEXT"),
        ("historical_significance", "TEXT"),
        ("catalog_description", "TEXT"),
        ("condition_observations", "TEXT"),
        ("llm_enriched_at", "DATETIME"),
        ("issuer_term_id", "INTEGER"),
        ("mint_term_id", "INTEGER"),
        ("denomination_term_id", "INTEGER"),
        ("dynasty_term_id", "INTEGER"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            try:
                print(f"Adding {column_name} column...")
                conn.execute(text(f"ALTER TABLE coins_v2 ADD COLUMN {column_name} {column_type}"))
                conn.commit()
                print(f"  ✓ {column_name} added successfully")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  - {column_name} already exists")
                else:
                    print(f"  ✗ Error adding {column_name}: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Expert Review Columns to coins_v2")
    print("=" * 60)
    migrate()
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)
