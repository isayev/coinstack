"""
Data Migration: Copy denomination and design fields from V1 to V2
------------------------------------------------------------------
Migrates denomination, obverse_legend, reverse_legend, and other design
fields from the old 'coins' table to 'coins_v2'.

Run: python -m src.infrastructure.scripts.migrate_v1_to_v2_data
"""
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

def migrate():
    # Fields to migrate from V1 to V2
    fields_to_migrate = [
        "denomination",
        "obverse_legend",
        "obverse_description",
        "reverse_legend",
        "reverse_description",
    ]

    with engine.connect() as conn:
        # Check how many V1 coins have denomination data
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM coins
            WHERE denomination IS NOT NULL AND denomination != ''
        """))
        v1_count = result.fetchone()[0]
        print(f"Found {v1_count} coins with denomination in V1 table")

        # Migrate each field
        for field in fields_to_migrate:
            try:
                print(f"\nMigrating {field}...")

                # Update V2 with V1 data where IDs match
                update_sql = f"""
                    UPDATE coins_v2
                    SET {field} = (
                        SELECT coins.{field}
                        FROM coins
                        WHERE coins.id = coins_v2.id
                    )
                    WHERE EXISTS (
                        SELECT 1 FROM coins
                        WHERE coins.id = coins_v2.id
                        AND coins.{field} IS NOT NULL
                        AND coins.{field} != ''
                    )
                """

                result = conn.execute(text(update_sql))
                conn.commit()

                # Count updated rows
                count_result = conn.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM coins_v2
                    WHERE {field} IS NOT NULL AND {field} != ''
                """))
                v2_count = count_result.fetchone()[0]

                print(f"  ✓ Migrated {field}: {v2_count} coins now have data")

            except Exception as e:
                print(f"  ✗ Error migrating {field}: {e}")
                conn.rollback()

if __name__ == "__main__":
    print("=" * 70)
    print("Migrating Data from V1 (coins) to V2 (coins_v2)")
    print("=" * 70)
    migrate()
    print("\n" + "=" * 70)
    print("Migration complete! Restart the backend to see changes.")
    print("=" * 70)
