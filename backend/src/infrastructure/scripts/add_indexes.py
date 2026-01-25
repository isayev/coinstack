"""
Add critical indexes to CoinStack V2 database.

This script creates indexes on frequently queried columns to improve performance.
Currently, all queries do full table scans. These indexes will enable O(log n) lookups.

Run with:
    python src/infrastructure/scripts/add_indexes.py
"""

from sqlalchemy import create_engine, text, inspect
from src.infrastructure.config import get_settings


def add_indexes():
    """Create indexes on critical columns."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)

    # Indexes to create
    indexes = [
        # Coins table - most frequently queried
        ("ix_coins_v2_issuer", "CREATE INDEX IF NOT EXISTS ix_coins_v2_issuer ON coins_v2(issuer);"),
        ("ix_coins_v2_category", "CREATE INDEX IF NOT EXISTS ix_coins_v2_category ON coins_v2(category);"),
        ("ix_coins_v2_metal", "CREATE INDEX IF NOT EXISTS ix_coins_v2_metal ON coins_v2(metal);"),
        ("ix_coins_v2_year_start", "CREATE INDEX IF NOT EXISTS ix_coins_v2_year_start ON coins_v2(year_start);"),
        ("ix_coins_v2_acquisition_date", "CREATE INDEX IF NOT EXISTS ix_coins_v2_acquisition_date ON coins_v2(acquisition_date);"),
        ("ix_coins_v2_grading_state", "CREATE INDEX IF NOT EXISTS ix_coins_v2_grading_state ON coins_v2(grading_state);"),

        # Issuers table - used in vocab search
        ("ix_issuers_canonical_name", "CREATE INDEX IF NOT EXISTS ix_issuers_canonical_name ON issuers(canonical_name);"),
        ("ix_issuers_nomisma_uri", "CREATE INDEX IF NOT EXISTS ix_issuers_nomisma_uri ON issuers(nomisma_uri);"),

        # Mints table - used in filtering
        ("ix_mints_canonical_name", "CREATE INDEX IF NOT EXISTS ix_mints_canonical_name ON mints(canonical_name);"),

        # Series table - slug lookups
        ("ix_series_slug", "CREATE UNIQUE INDEX IF NOT EXISTS ix_series_slug ON series(slug);"),

        # Auction data - URL lookups for deduplication
        ("ix_auction_data_v2_url", "CREATE UNIQUE INDEX IF NOT EXISTS ix_auction_data_v2_url ON auction_data_v2(url);"),
        ("ix_auction_data_v2_coin_id", "CREATE INDEX IF NOT EXISTS ix_auction_data_v2_coin_id ON auction_data_v2(coin_id);"),
    ]

    # Check existing indexes
    inspector = inspect(engine)
    existing_indexes = {}
    for table_name in ['coins_v2', 'issuers', 'mints', 'series', 'auction_data_v2']:
        try:
            existing_indexes[table_name] = [idx['name'] for idx in inspector.get_indexes(table_name)]
        except Exception:
            existing_indexes[table_name] = []

    print("Creating indexes on CoinStack V2 database...")
    print(f"Database: {settings.DATABASE_URL}\n")

    created_count = 0
    skipped_count = 0

    with engine.connect() as conn:
        for idx_name, idx_sql in indexes:
            # Check if index already exists
            table_name = idx_sql.split(" ON ")[1].split("(")[0].strip()
            if idx_name in existing_indexes.get(table_name, []):
                print(f"⏭️  {idx_name} (already exists)")
                skipped_count += 1
                continue

            try:
                print(f"Creating: {idx_name}...")
                conn.execute(text(idx_sql))
                conn.commit()
                print(f"✅ {idx_name} created successfully")
                created_count += 1
            except Exception as e:
                print(f"❌ {idx_name} failed: {e}")

    print(f"\n📊 Summary:")
    print(f"   Created: {created_count}")
    print(f"   Skipped: {skipped_count}")
    print(f"   Total: {len(indexes)}")

    if created_count > 0:
        print("\n✅ Indexes created successfully. Query performance should improve significantly.")
    else:
        print("\n✅ All indexes already exist.")


def verify_indexes():
    """Verify that indexes are being used in query plans."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)

    print("\n🔍 Verifying index usage with EXPLAIN QUERY PLAN...\n")

    test_queries = [
        ("SELECT * FROM coins_v2 WHERE issuer LIKE '%Augustus%'", "issuer index"),
        ("SELECT * FROM coins_v2 WHERE category = 'imperial'", "category index"),
        ("SELECT * FROM coins_v2 WHERE year_start >= -27 AND year_start <= 14", "year_start index"),
        ("SELECT * FROM issuers WHERE canonical_name = 'Augustus'", "issuer canonical_name index"),
        ("SELECT * FROM series WHERE slug = 'test-series'", "series slug index"),
    ]

    with engine.connect() as conn:
        for query, index_desc in test_queries:
            print(f"Testing: {index_desc}")
            print(f"Query: {query}")
            result = conn.execute(text(f"EXPLAIN QUERY PLAN {query}"))
            plan = result.fetchall()
            for row in plan:
                detail = row[3] if len(row) > 3 else str(row)
                if "INDEX" in detail.upper():
                    print(f"✅ Using index: {detail}")
                else:
                    print(f"⚠️  {detail}")
            print()


if __name__ == "__main__":
    import sys

    print("="*60)
    print("CoinStack V2 Database Index Creation")
    print("="*60)
    print()

    add_indexes()

    if "--verify" in sys.argv:
        verify_indexes()

    print("\n" + "="*60)
    print("Complete! Run with --verify flag to check query plans.")
    print("="*60)
