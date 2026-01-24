"""Comprehensive database migration - Add all missing columns to all tables."""
import sqlite3

conn = sqlite3.connect('data/coinstack.db')
cur = conn.cursor()

def get_existing_columns(table_name):
    """Get list of existing column names for a table."""
    cur.execute(f'PRAGMA table_info({table_name})')
    return set(col[1] for col in cur.fetchall())

def add_column_if_missing(table, column, col_type):
    """Add column to table if it doesn't exist."""
    existing = get_existing_columns(table)
    if column not in existing:
        try:
            cur.execute(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}')
            print(f'  Added: {table}.{column}')
            return True
        except Exception as e:
            print(f'  Error adding {table}.{column}: {e}')
    return False

# ============================================
# COINS TABLE MIGRATIONS
# ============================================
print("Migrating coins table...")
coins_columns = [
    ('sub_category', 'TEXT'),
    ('is_circa', 'INTEGER DEFAULT 0'),
    ('orientation', 'TEXT'),
    ('is_test_cut', 'INTEGER DEFAULT 0'),
    ('estimated_value_usd', 'REAL'),
    ('die_study_obverse_id', 'INTEGER'),
    ('die_study_reverse_id', 'INTEGER'),
    ('die_study_group', 'TEXT'),
    ('field_sources', 'TEXT'),
]
for col, typ in coins_columns:
    add_column_if_missing('coins', col, typ)

# ============================================
# COIN_REFERENCES TABLE MIGRATIONS
# ============================================
print("Migrating coin_references table...")
ref_columns = [
    ('position', 'TEXT DEFAULT "both"'),
    ('plate_coin', 'INTEGER DEFAULT 0'),
    ('variant_notes', 'TEXT'),
    ('page', 'TEXT'),
    ('plate', 'TEXT'),
    ('note_number', 'TEXT'),
    ('notes', 'TEXT'),
]
for col, typ in ref_columns:
    add_column_if_missing('coin_references', col, typ)

# ============================================
# REFERENCE_TYPES TABLE MIGRATIONS
# ============================================
print("Migrating reference_types table...")
rt_columns = [
    ('local_ref_normalized', 'TEXT'),
    ('volume', 'TEXT'),
    ('number', 'TEXT'),
    ('edition', 'TEXT'),
    ('external_id', 'TEXT'),
    ('external_url', 'TEXT'),
    ('lookup_status', 'TEXT DEFAULT "pending"'),
    ('lookup_confidence', 'REAL'),
    ('last_lookup', 'TEXT'),
    ('source_version', 'TEXT'),
    ('error_message', 'TEXT'),
    ('payload', 'TEXT'),
    ('citation', 'TEXT'),
    ('bibliography_refs', 'TEXT'),
]
for col, typ in rt_columns:
    add_column_if_missing('reference_types', col, typ)

# ============================================
# COIN_IMAGES TABLE MIGRATIONS  
# ============================================
print("Migrating coin_images table...")
img_columns = [
    ('image_type', 'TEXT'),
    ('storage_path', 'TEXT'),
    ('phash', 'TEXT'),
    ('width', 'INTEGER'),
    ('height', 'INTEGER'),
    ('file_size', 'INTEGER'),
    ('mime_type', 'TEXT'),
    ('is_primary', 'INTEGER DEFAULT 0'),
    ('caption', 'TEXT'),
    ('source_url', 'TEXT'),
    ('source_attribution', 'TEXT'),
]
for col, typ in img_columns:
    add_column_if_missing('coin_images', col, typ)

# ============================================
# MINTS TABLE MIGRATIONS
# ============================================
print("Migrating mints table...")
mint_columns = [
    ('city', 'TEXT'),
    ('region', 'TEXT'),
    ('country', 'TEXT'),
    ('latitude', 'REAL'),
    ('longitude', 'REAL'),
    ('date_opened', 'TEXT'),
    ('date_closed', 'TEXT'),
    ('notes', 'TEXT'),
]
for col, typ in mint_columns:
    add_column_if_missing('mints', col, typ)

# ============================================
# PROVENANCE EVENTS TABLE MIGRATIONS
# ============================================
print("Migrating provenance_events table...")
prov_columns = [
    ('auction_house', 'TEXT'),
    ('auction_name', 'TEXT'),
    ('lot_number', 'TEXT'),
    ('price_realized', 'REAL'),
    ('price_currency', 'TEXT'),
    ('buyer_premium', 'REAL'),
    ('hammer_price', 'REAL'),
    ('publication_reference', 'TEXT'),
    ('confidence_level', 'TEXT'),
    ('verified', 'INTEGER DEFAULT 0'),
    ('verification_notes', 'TEXT'),
]
for col, typ in prov_columns:
    add_column_if_missing('provenance_events', col, typ)

# ============================================
# FIX ENUM VALUES (lowercase -> UPPERCASE)
# ============================================
print("Fixing enum values...")

# Fix coin_references.position
cur.execute('UPDATE coin_references SET position = NULL WHERE position = "both"')
print(f'  Fixed coin_references.position: {cur.rowcount} rows')

# Fix coins.orientation  
cur.execute('UPDATE coins SET orientation = NULL WHERE orientation = "obverse_up"')
print(f'  Fixed coins.orientation: {cur.rowcount} rows')

conn.commit()
conn.close()
print("\nMigration complete!")
