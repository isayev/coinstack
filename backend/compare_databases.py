import sqlite3
import os

# Database paths
v1_path = 'data/coinstack.db'
v2_path = 'coinstack_v2.db'

print("=" * 70)
print("DATABASE COMPARISON: V1 vs V2")
print("=" * 70)

print(f"\nV1 Database: {v1_path} ({os.path.getsize(v1_path) / 1024:.1f} KB)")
print(f"V2 Database: {v2_path} ({os.path.getsize(v2_path) / 1024:.1f} KB)")

# Connect to both
conn_v1 = sqlite3.connect(v1_path)
conn_v2 = sqlite3.connect(v2_path)
cur_v1 = conn_v1.cursor()
cur_v2 = conn_v2.cursor()

# Get tables in each database
cur_v1.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
v1_tables = [t[0] for t in cur_v1.fetchall()]

cur_v2.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
v2_tables = [t[0] for t in cur_v2.fetchall()]

print("\n" + "=" * 70)
print("TABLES COMPARISON")
print("=" * 70)
print(f"\nV1 Tables ({len(v1_tables)}): {', '.join(v1_tables)}")
print(f"\nV2 Tables ({len(v2_tables)}): {', '.join(v2_tables)}")

# Count records in each table
print("\n" + "=" * 70)
print("RECORD COUNTS")
print("=" * 70)

print("\nV1 Tables:")
for table in v1_tables:
    try:
        cur_v1.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cur_v1.fetchone()[0]
        print(f"  {table}: {count} records")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

print("\nV2 Main Tables:")
main_v2_tables = ['coins_v2', 'coin_images_v2', 'auction_data_v2', 'coins', 'coin_images', 'auction_data', 
                  'mints', 'issuers', 'enrichment_records', 'discrepancy_records', 'audit_runs']
for table in main_v2_tables:
    if table in v2_tables:
        cur_v2.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cur_v2.fetchone()[0]
        print(f"  {table}: {count} records")

# Find coin tables
v1_coin_table = 'coins' if 'coins' in v1_tables else None
v2_coin_table = 'coins_v2' if 'coins_v2' in v2_tables else 'coins'

# Get column info
cur_v1.execute(f"PRAGMA table_info({v1_coin_table})")
v1_columns = {row[1]: row[2] for row in cur_v1.fetchall()}

cur_v2.execute(f"PRAGMA table_info({v2_coin_table})")
v2_columns = {row[1]: row[2] for row in cur_v2.fetchall()}

print("\n" + "=" * 70)
print("COLUMN COMPARISON")
print("=" * 70)
print(f"\nV1 coin columns ({len(v1_columns)}):")
print(f"  {', '.join(sorted(v1_columns.keys()))}")
print(f"\nV2 coin columns ({len(v2_columns)}):")
print(f"  {', '.join(sorted(v2_columns.keys()))}")

# Check for columns in V1 but not in V2
v1_only = set(v1_columns.keys()) - set(v2_columns.keys())
v2_only = set(v2_columns.keys()) - set(v1_columns.keys())

if v1_only:
    print(f"\n⚠️  Columns in V1 but NOT in V2: {', '.join(sorted(v1_only))}")
if v2_only:
    print(f"\n✓ New columns in V2: {', '.join(sorted(v2_only))}")

# Check key fields for data preservation
print("\n" + "=" * 70)
print("KEY FIELD DATA PRESERVATION CHECK")
print("=" * 70)

key_fields = ['weight_g', 'diameter_mm', 'die_axis', 'category', 'metal', 'denomination', 
              'issuing_authority', 'grade', 'acquisition_price', 'acquisition_date',
              'obverse_legend', 'obverse_description', 'reverse_legend', 'reverse_description',
              'mint', 'year_start', 'year_end', 'reference', 'historical_significance', 'notes']

for field in key_fields:
    v1_has = field in v1_columns
    v2_has = field in v2_columns
    
    if v1_has and v2_has:
        cur_v1.execute(f"SELECT COUNT(*) FROM {v1_coin_table} WHERE [{field}] IS NOT NULL AND [{field}] != ''")
        v1_count = cur_v1.fetchone()[0]
        cur_v2.execute(f"SELECT COUNT(*) FROM {v2_coin_table} WHERE [{field}] IS NOT NULL AND [{field}] != ''")
        v2_count = cur_v2.fetchone()[0]
        
        if v2_count >= v1_count:
            status = "✓"
        elif v2_count == 0 and v1_count > 0:
            status = "❌ ALL DATA LOST"
        else:
            status = "⚠️  PARTIAL LOSS"
        diff = v2_count - v1_count
        print(f"  {field:25s}: V1={v1_count:3d}, V2={v2_count:3d} ({'+' if diff >= 0 else ''}{diff:3d}) {status}")
    elif v1_has and not v2_has:
        cur_v1.execute(f"SELECT COUNT(*) FROM {v1_coin_table} WHERE [{field}] IS NOT NULL AND [{field}] != ''")
        v1_count = cur_v1.fetchone()[0]
        print(f"  {field:25s}: V1={v1_count:3d}, V2=N/A - ⚠️  COLUMN MISSING IN V2")
    elif v2_has and not v1_has:
        cur_v2.execute(f"SELECT COUNT(*) FROM {v2_coin_table} WHERE [{field}] IS NOT NULL AND [{field}] != ''")
        v2_count = cur_v2.fetchone()[0]
        print(f"  {field:25s}: V1=N/A, V2={v2_count:3d} - New in V2")

# Die Axis specific check
print("\n" + "=" * 70)
print("DIE AXIS DETAILED CHECK")
print("=" * 70)

if 'die_axis' in v1_columns:
    cur_v1.execute(f"SELECT die_axis, COUNT(*) FROM {v1_coin_table} WHERE die_axis IS NOT NULL AND die_axis != '' GROUP BY die_axis ORDER BY die_axis")
    v1_die_axis = cur_v1.fetchall()
    print(f"\nV1 die_axis distribution: {dict(v1_die_axis)}")

cur_v2.execute(f"SELECT die_axis, COUNT(*) FROM {v2_coin_table} WHERE die_axis IS NOT NULL AND die_axis != '' GROUP BY die_axis ORDER BY die_axis")
v2_die_axis = cur_v2.fetchall()
print(f"V2 die_axis distribution: {dict(v2_die_axis)}")

# Check for enrichment/audit data in V2
print("\n" + "=" * 70)
print("ENRICHMENT & AUDIT DATA (V2)")
print("=" * 70)

# Enrichment columns
enrichment_cols = ['llm_description', 'llm_historical_context', 'llm_enriched_at', 
                   'expert_reviewed', 'expert_reviewed_at', 'expert_notes',
                   'grading_state', 'description']

print("\nEnrichment columns in coins_v2:")
for col in enrichment_cols:
    if col in v2_columns:
        cur_v2.execute(f"SELECT COUNT(*) FROM {v2_coin_table} WHERE [{col}] IS NOT NULL AND [{col}] != ''")
        count = cur_v2.fetchone()[0]
        print(f"  {col}: {count} records with data")
    else:
        print(f"  {col}: Not present in schema")

# Check enrichment_records table
if 'enrichment_records' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM enrichment_records")
    total = cur_v2.fetchone()[0]
    cur_v2.execute("SELECT enrichment_type, COUNT(*) FROM enrichment_records GROUP BY enrichment_type")
    by_type = cur_v2.fetchall()
    print(f"\nEnrichment records table: {total} total")
    for etype, cnt in by_type:
        print(f"  {etype}: {cnt}")

# Check discrepancy_records table (audit)
if 'discrepancy_records' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM discrepancy_records")
    total = cur_v2.fetchone()[0]
    cur_v2.execute("SELECT field_name, COUNT(*) FROM discrepancy_records GROUP BY field_name ORDER BY COUNT(*) DESC")
    by_field = cur_v2.fetchall()
    print(f"\nDiscrepancy records (audit): {total} total")
    for fname, cnt in by_field[:10]:
        print(f"  {fname}: {cnt}")

# Check audit_runs table
if 'audit_runs' in v2_tables:
    cur_v2.execute("SELECT id, created_at, total_coins, total_discrepancies FROM audit_runs ORDER BY created_at DESC LIMIT 5")
    runs = cur_v2.fetchall()
    print(f"\nAudit runs:")
    for run in runs:
        print(f"  Run #{run[0]}: {run[1]}, {run[2]} coins, {run[3]} discrepancies")

# Check images
print("\n" + "=" * 70)
print("IMAGE DATA COMPARISON")
print("=" * 70)

if 'coin_images' in v1_tables:
    cur_v1.execute("SELECT COUNT(*) FROM coin_images")
    v1_images = cur_v1.fetchone()[0]
    print(f"V1 coin_images: {v1_images}")

if 'coin_images_v2' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM coin_images_v2")
    v2_images = cur_v2.fetchone()[0]
    print(f"V2 coin_images_v2: {v2_images}")
    
if 'coin_images' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM coin_images")
    v2_images_old = cur_v2.fetchone()[0]
    print(f"V2 coin_images (legacy table): {v2_images_old}")

# Check auction data
print("\n" + "=" * 70)
print("AUCTION DATA COMPARISON")
print("=" * 70)

if 'auction_data' in v1_tables:
    cur_v1.execute("SELECT COUNT(*) FROM auction_data")
    v1_auction = cur_v1.fetchone()[0]
    print(f"V1 auction_data: {v1_auction}")

if 'auction_data' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM auction_data")
    v2_auction = cur_v2.fetchone()[0]
    print(f"V2 auction_data: {v2_auction}")

if 'auction_data_v2' in v2_tables:
    cur_v2.execute("SELECT COUNT(*) FROM auction_data_v2")
    v2_auction_new = cur_v2.fetchone()[0]
    print(f"V2 auction_data_v2: {v2_auction_new}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

cur_v1.execute(f"SELECT COUNT(*) FROM {v1_coin_table}")
v1_total = cur_v1.fetchone()[0]
cur_v2.execute(f"SELECT COUNT(*) FROM {v2_coin_table}")
v2_total = cur_v2.fetchone()[0]

print(f"\nTotal coins: V1={v1_total}, V2={v2_total}")
if v2_total >= v1_total:
    print("✓ No coin records lost")
else:
    print(f"❌ POTENTIAL DATA LOSS: {v1_total - v2_total} coins missing in V2")

conn_v1.close()
conn_v2.close()
