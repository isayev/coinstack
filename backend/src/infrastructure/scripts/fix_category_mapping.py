"""
Migration: Fix Category Mapping from V1 to V2
----------------------------------------------
Corrects category values that were incorrectly migrated:
- V1 "IMPERIAL" → V2 "roman_imperial" ✓
- V1 "PROVINCIAL" → V2 "roman_provincial" (was incorrectly "roman_imperial")
- V1 "REPUBLIC" → V2 "roman_republic" ✓

Run: python -m src.infrastructure.scripts.fix_category_mapping
"""
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

def migrate():
    print("=" * 70)
    print("Fixing Category Mapping (V1 → V2)")
    print("=" * 70)

    with engine.connect() as conn:
        # Check current state
        print("\n[1/3] Checking current category distribution...")

        v1_result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM coins
            GROUP BY category
            ORDER BY category
        """))
        print("\nV1 (coins) table:")
        v1_categories = {}
        for row in v1_result:
            v1_categories[row[0]] = row[1]
            print(f"  {row[0]}: {row[1]} coins")

        v2_result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM coins_v2
            GROUP BY category
            ORDER BY category
        """))
        print("\nV2 (coins_v2) table (BEFORE fix):")
        for row in v2_result:
            print(f"  {row[0]}: {row[1]} coins")

        # Fix PROVINCIAL → roman_provincial
        print("\n[2/3] Fixing PROVINCIAL → roman_provincial...")

        provincial_ids_result = conn.execute(text("""
            SELECT id FROM coins WHERE category = 'PROVINCIAL'
        """))
        provincial_ids = [row[0] for row in provincial_ids_result]

        if provincial_ids:
            print(f"  Found {len(provincial_ids)} PROVINCIAL coins: {provincial_ids}")

            # Update coins_v2 with correct category
            id_list = ','.join(str(id) for id in provincial_ids)
            update_result = conn.execute(
                text(f"""
                    UPDATE coins_v2
                    SET category = 'roman_provincial'
                    WHERE id IN ({id_list})
                """)
            )
            conn.commit()
            print(f"  ✓ Updated {len(provincial_ids)} coins to 'roman_provincial'")
        else:
            print("  - No PROVINCIAL coins found")

        # Verify other mappings
        print("\n[3/3] Verifying all category mappings...")

        verification_result = conn.execute(text("""
            SELECT
                v1.category as v1_category,
                v2.category as v2_category,
                COUNT(*) as count
            FROM coins v1
            JOIN coins_v2 v2 ON v1.id = v2.id
            GROUP BY v1.category, v2.category
            ORDER BY v1.category, v2.category
        """))

        print("\nV1 → V2 Mapping:")
        mapping_correct = True
        expected_mappings = {
            'IMPERIAL': 'roman_imperial',
            'PROVINCIAL': 'roman_provincial',
            'REPUBLIC': 'roman_republic'
        }

        for row in verification_result:
            v1_cat, v2_cat, count = row[0], row[1], row[2]
            expected = expected_mappings.get(v1_cat, '???')
            status = "✓" if v2_cat == expected else "✗"
            print(f"  {status} {v1_cat} → {v2_cat} ({count} coins) [expected: {expected}]")
            if v2_cat != expected:
                mapping_correct = False

        # Final summary
        print("\n" + "=" * 70)
        if mapping_correct:
            print("✓ All category mappings are correct!")
        else:
            print("✗ Some mappings are still incorrect - manual investigation needed")

        # Show final V2 distribution
        final_result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM coins_v2
            GROUP BY category
            ORDER BY category
        """))
        print("\nV2 (coins_v2) table (AFTER fix):")
        for row in final_result:
            print(f"  {row[0]}: {row[1]} coins")

        print("=" * 70)

if __name__ == "__main__":
    migrate()
