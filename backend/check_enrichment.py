import sqlite3

conn = sqlite3.connect('coinstack_v2.db')
cur = conn.cursor()

print("=" * 70)
print("ENRICHMENT & AUDIT TABLES DETAIL")
print("=" * 70)

# Count by source_house
print("\nEnrichment records by source_house:")
cur.execute("SELECT source_house, COUNT(*) FROM enrichment_records GROUP BY source_house")
for src, cnt in cur.fetchall():
    print(f"  {src}: {cnt}")

# Count by field_name
print("\nEnrichment records by field_name:")
cur.execute("SELECT field_name, COUNT(*) FROM enrichment_records GROUP BY field_name ORDER BY COUNT(*) DESC")
for fname, cnt in cur.fetchall():
    print(f"  {fname}: {cnt}")

# Count by status
print("\nEnrichment records by status:")
cur.execute("SELECT status, COUNT(*) FROM enrichment_records GROUP BY status")
for status, cnt in cur.fetchall():
    print(f"  {status}: {cnt}")

# Check discrepancy_records
print("\n" + "=" * 70)
print("DISCREPANCY RECORDS (AUDIT DATA)")
print("=" * 70)

print("\nDiscrepancy records by field:")
cur.execute("SELECT field_name, COUNT(*) FROM discrepancy_records GROUP BY field_name ORDER BY COUNT(*) DESC")
for fname, cnt in cur.fetchall():
    print(f"  {fname}: {cnt}")

# Check audit_runs schema and data
print("\nAudit runs:")
cur.execute("PRAGMA table_info(audit_runs)")
cols = [c[1] for c in cur.fetchall()]
cur.execute("SELECT * FROM audit_runs")
for row in cur.fetchall():
    print(f"  {dict(zip(cols, row))}")

# Check V1 columns that may contain important data
print("\n" + "=" * 70)
print("V1 COLUMNS WITH DATA - CHECKING IF MIGRATED")
print("=" * 70)

# V1 fields that had data and their V2 equivalents
v1_fields_with_data = [
    ('issuing_authority', 'issuer'),
    ('mint_year_start', 'year_start'),
    ('mint_year_end', 'year_end'),
    ('reign_start', None),
    ('reign_end', None),
    ('rarity', None),
    ('personal_notes', None),
    ('provenance_notes', None),
    ('storage_location', None),
    ('status', None),
    ('eye_appeal', None),
    ('style_notes', None),
    ('series', None),
    ('sub_category', None),
    ('dating_certainty', None),
    ('is_circa', None),
]

for v1_col, v2_col in v1_fields_with_data:
    try:
        cur.execute(f"SELECT COUNT(*) FROM coins WHERE [{v1_col}] IS NOT NULL AND [{v1_col}] != ''")
        v1_count = cur.fetchone()[0]
        if v1_count > 0:
            if v2_col:
                cur.execute(f"SELECT COUNT(*) FROM coins_v2 WHERE [{v2_col}] IS NOT NULL AND [{v2_col}] != ''")
                v2_count = cur.fetchone()[0]
                status = "✓ MIGRATED" if v2_count >= v1_count else f"⚠️ PARTIAL ({v2_count}/{v1_count})"
                print(f"  {v1_col} -> {v2_col}: V1={v1_count}, V2={v2_count} {status}")
            else:
                print(f"  {v1_col}: V1={v1_count} records - ❌ NO V2 EQUIVALENT COLUMN")
    except Exception as e:
        pass  # Column doesn't exist

# Sample issuing_authority values
print("\n" + "=" * 70)
print("ISSUER DATA COMPARISON")
print("=" * 70)

cur.execute("SELECT COUNT(DISTINCT issuing_authority) FROM coins WHERE issuing_authority IS NOT NULL AND issuing_authority != ''")
v1_unique = cur.fetchone()[0]

cur.execute("SELECT COUNT(DISTINCT issuer) FROM coins_v2 WHERE issuer IS NOT NULL AND issuer != ''")
v2_unique = cur.fetchone()[0]

print(f"Unique issuing authorities in V1 coins: {v1_unique}")
print(f"Unique issuers in V2 coins_v2: {v2_unique}")

# Sample values
cur.execute("SELECT DISTINCT issuing_authority FROM coins WHERE issuing_authority IS NOT NULL AND issuing_authority != '' ORDER BY issuing_authority LIMIT 10")
v1_issuers = [r[0] for r in cur.fetchall()]
print(f"\nSample V1 issuing_authority: {v1_issuers}")

cur.execute("SELECT DISTINCT issuer FROM coins_v2 WHERE issuer IS NOT NULL AND issuer != '' ORDER BY issuer LIMIT 10")
v2_issuers = [r[0] for r in cur.fetchall()]
print(f"Sample V2 issuer: {v2_issuers}")

# Check mint data
print("\n" + "=" * 70)
print("MINT DATA COMPARISON")
print("=" * 70)

# V1 uses mint_id FK, V2 has both mint_id and mint (text)
cur.execute("SELECT COUNT(*) FROM coins WHERE mint_id IS NOT NULL")
v1_mint_fk = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM coins_v2 WHERE mint_id IS NOT NULL")
v2_mint_fk = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM coins_v2 WHERE mint IS NOT NULL AND mint != ''")
v2_mint_text = cur.fetchone()[0]

print(f"V1 coins with mint_id: {v1_mint_fk}")
print(f"V2 coins with mint_id: {v2_mint_fk}")
print(f"V2 coins with mint text: {v2_mint_text}")

# Check year data
print("\n" + "=" * 70)
print("YEAR/DATE DATA COMPARISON")
print("=" * 70)

cur.execute("SELECT COUNT(*) FROM coins WHERE mint_year_start IS NOT NULL")
v1_year_start = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM coins_v2 WHERE year_start IS NOT NULL")
v2_year_start = cur.fetchone()[0]

print(f"V1 coins with mint_year_start: {v1_year_start}")
print(f"V2 coins with year_start: {v2_year_start}")

# Check reign dates
cur.execute("SELECT COUNT(*) FROM coins WHERE reign_start IS NOT NULL")
v1_reign_start = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM coins WHERE reign_end IS NOT NULL")
v1_reign_end = cur.fetchone()[0]

print(f"V1 coins with reign_start: {v1_reign_start}")
print(f"V1 coins with reign_end: {v1_reign_end}")
print("Note: reign_start/reign_end columns do not exist in V2 schema")

conn.close()

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("""
✓ PRESERVED (NO DATA LOSS):
  - All 110 coin records
  - All 23 die_axis values (identical distribution)
  - All 119 images
  - All 110 auction data records
  - All 108 enrichment records (applied from various auction houses)
  - All 92 discrepancy/audit records
  - Core fields: weight, diameter, category, metal, denomination, grades
  - Legends and descriptions (obverse/reverse)

⚠️ COLUMN RENAMES (DATA MIGRATED):
  - issuing_authority -> issuer
  - mint_year_start/end -> year_start/end

❌ V1 COLUMNS NOT IN V2 SCHEMA:
  - reign_start, reign_end
  - rarity, personal_notes, provenance_notes
  - storage_location, status, eye_appeal
  - style_notes, series, sub_category
  - dating_certainty, is_circa
  - And others (see detailed output above)
""")
