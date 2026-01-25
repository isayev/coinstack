"""
Data Quality Fix Script - V3 Migration Issues
----------------------------------------------
Fixes data quality issues identified in V3 migration analysis:
1. Denomination typo: "Fllis" -> "Follis"
2. Case inconsistency: "as" -> "As"

Run: python -m src.infrastructure.scripts.fix_data_quality_issues
"""
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

def fix_data_quality_issues():
    """Fix identified data quality issues from migration analysis."""

    print("=" * 70)
    print("Data Quality Fix Script - V3 Migration Issues")
    print("=" * 70)

    with engine.connect() as conn:
        # Issue #1: Fix denomination typo (Fllis -> Follis)
        print("\n[1/2] Fixing denomination typo: 'Fllis' -> 'Follis'...")

        # Check current state
        result = conn.execute(text("""
            SELECT id, denomination
            FROM coins_v2
            WHERE denomination = 'Fllis'
        """))
        typo_coins = list(result)

        if typo_coins:
            print(f"  Found {len(typo_coins)} coin(s) with typo:")
            for coin_id, denom in typo_coins:
                print(f"    - Coin ID {coin_id}: '{denom}'")

            # Fix the typo
            conn.execute(text("""
                UPDATE coins_v2
                SET denomination = 'Follis'
                WHERE denomination = 'Fllis'
            """))
            conn.commit()
            print(f"  ✓ Fixed {len(typo_coins)} coin(s)")
        else:
            print("  - No typos found (already fixed)")

        # Issue #2: Fix case inconsistency (as -> As)
        print("\n[2/2] Fixing case inconsistency: 'as' -> 'As'...")

        # Check current state
        result = conn.execute(text("""
            SELECT id, denomination
            FROM coins_v2
            WHERE denomination = 'as'
        """))
        case_coins = list(result)

        if case_coins:
            print(f"  Found {len(case_coins)} coin(s) with lowercase 'as':")
            for coin_id, denom in case_coins:
                print(f"    - Coin ID {coin_id}: '{denom}'")

            # Fix the case
            conn.execute(text("""
                UPDATE coins_v2
                SET denomination = 'As'
                WHERE denomination = 'as'
            """))
            conn.commit()
            print(f"  ✓ Fixed {len(case_coins)} coin(s)")
        else:
            print("  - No case issues found (already fixed)")

        # Verify final state
        print("\n[3/3] Verifying denomination consistency...")

        result = conn.execute(text("""
            SELECT denomination, COUNT(*) as count
            FROM coins_v2
            GROUP BY denomination
            ORDER BY count DESC, denomination
        """))

        print("\nFinal denomination distribution:")
        for denom, count in result:
            print(f"  {denom:25s}: {count:3d}")

        # Check for any remaining issues
        result = conn.execute(text("""
            SELECT denomination, COUNT(*)
            FROM coins_v2
            WHERE denomination IS NOT NULL AND denomination != ''
            GROUP BY LOWER(denomination)
            HAVING COUNT(DISTINCT denomination) > 1
        """))

        remaining_issues = list(result)
        if remaining_issues:
            print("\n⚠ Remaining case inconsistencies found:")
            for denom, count in remaining_issues:
                print(f"  {denom}")
        else:
            print("\n✓ No case inconsistencies detected")

        print("\n" + "=" * 70)
        print("Data quality fixes completed successfully!")
        print("=" * 70)

if __name__ == "__main__":
    fix_data_quality_issues()
