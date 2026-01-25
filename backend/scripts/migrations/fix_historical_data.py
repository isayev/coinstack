"""
Historical Data Corrections Script

Fixes identified by Roman history expert review:
1. Remove Macrinus from Severan dynasty (he assassinated Caracalla - NOT Severan)
2. Add Palmyrene Empire dynasty (Zenobia, Vabalathus)
3. Add Imperial Women series
4. Add Gallic Emperors series
5. Fix Severan Dynasty canonical series

Run from backend directory: python -m scripts.migrations.fix_historical_data
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
    """Get path to the database file."""
    possible_paths = [
        Path("coinstack_v2.db"),
        Path("backend/coinstack_v2.db"),
        Path(__file__).parent.parent.parent / "coinstack_v2.db",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    raise FileNotFoundError("Could not find coinstack_v2.db")


def run_fixes(db_path: Path):
    """Apply historical data corrections."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        print("=" * 60)
        print("Historical Data Corrections")
        print("=" * 60)
        
        # =====================================================================
        # 1. Fix Severan Dynasty - Remove Macrinus (NOT Severan - he killed Caracalla)
        # =====================================================================
        print("\n1. Fixing Severan dynasty (removing Macrinus)...")
        
        # Correct Severan rulers (with Julia Domna, without Macrinus)
        severan_correct = {
            "period_start": 193,
            "period_end": 235,
            "rulers": [
                "Septimius Severus",
                "Julia Domna",      # Added - important empress
                "Caracalla",
                "Geta",
                "Elagabalus",
                "Julia Maesa",      # Added - power behind throne
                "Severus Alexander",
                "Julia Mamaea"      # Added - mother of Severus Alexander
            ]
        }
        
        conn.execute(
            "UPDATE vocab_terms SET metadata = ? WHERE vocab_type = 'dynasty' AND canonical_name = 'Severan'",
            (json.dumps(severan_correct),)
        )
        print("   Updated Severan dynasty (removed Macrinus, added Julias)")
        
        # =====================================================================
        # 2. Add Palmyrene Empire dynasty
        # =====================================================================
        print("\n2. Adding Palmyrene Empire dynasty...")
        
        palmyrene = {
            "period_start": 267,
            "period_end": 273,
            "rulers": ["Odaenathus", "Zenobia", "Vabalathus"],
            "description": "Breakaway empire centered on Palmyra (267-273 AD)"
        }
        
        conn.execute(
            "INSERT OR REPLACE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
            ("dynasty", "Palmyrene Empire", json.dumps(palmyrene))
        )
        print("   Added Palmyrene Empire dynasty")
        
        # =====================================================================
        # 3. Add Romano-British dynasty (Carausius/Allectus)
        # =====================================================================
        print("\n3. Adding Romano-British Empire dynasty...")
        
        romano_british = {
            "period_start": 286,
            "period_end": 296,
            "rulers": ["Carausius", "Allectus"],
            "description": "Breakaway British empire (286-296 AD)"
        }
        
        conn.execute(
            "INSERT OR REPLACE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
            ("dynasty", "Romano-British Empire", json.dumps(romano_british))
        )
        print("   Added Romano-British Empire dynasty")
        
        # =====================================================================
        # 4. Add Imperial Women canonical series
        # =====================================================================
        print("\n4. Adding Imperial Women canonical series...")
        
        imperial_women = {
            "expected_count": 0,  # Variable - no fixed count
            "rulers": [
                "Livia",
                "Agrippina Senior",
                "Agrippina Junior",
                "Messalina",
                "Poppaea",
                "Faustina I",
                "Faustina II",
                "Lucilla",
                "Crispina",
                "Julia Domna",
                "Julia Maesa",
                "Julia Soaemias",
                "Julia Mamaea",
                "Otacilia Severa",
                "Salonina",
                "Helena",
                "Fausta",
                "Aelia Flaccilla",
                "Pulcheria"
            ],
            "category": "imperial",
            "description": "Empresses and imperial women who appeared on Roman coinage"
        }
        
        conn.execute(
            "INSERT OR REPLACE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
            ("canonical_series", "Imperial Women", json.dumps(imperial_women))
        )
        print("   Added Imperial Women series")
        
        # =====================================================================
        # 5. Add Gallic Emperors canonical series
        # =====================================================================
        print("\n5. Adding Gallic Emperors canonical series...")
        
        gallic_emperors = {
            "expected_count": 9,
            "rulers": [
                "Postumus",
                "Laelianus",
                "Marius",
                "Victorinus",
                "Domitianus II",
                "Tetricus I",
                "Tetricus II"
            ],
            "category": "gallic_empire",
            "description": "Emperors of the breakaway Gallic Empire (260-274 AD)"
        }
        
        conn.execute(
            "INSERT OR REPLACE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
            ("canonical_series", "Gallic Emperors", json.dumps(gallic_emperors))
        )
        print("   Added Gallic Emperors series")
        
        # =====================================================================
        # 6. Fix Severan Dynasty canonical series (remove Macrinus)
        # =====================================================================
        print("\n6. Fixing Severan Dynasty canonical series...")
        
        severan_series = {
            "expected_count": 5,
            "rulers": [
                "Septimius Severus",
                "Caracalla",
                "Geta",
                "Elagabalus",
                "Severus Alexander"
            ],
            "category": "imperial",
            "description": "The Severan dynasty emperors (193-235 AD) - male rulers only"
        }
        
        conn.execute(
            "UPDATE vocab_terms SET metadata = ? WHERE vocab_type = 'canonical_series' AND canonical_name = 'Severan Dynasty'",
            (json.dumps(severan_series),)
        )
        print("   Fixed Severan Dynasty canonical series (removed Macrinus)")
        
        # =====================================================================
        # 7. Add Tetrarchy canonical series
        # =====================================================================
        print("\n7. Adding Tetrarchy canonical series...")
        
        tetrarchy_series = {
            "expected_count": 8,
            "rulers": [
                "Diocletian",
                "Maximian",
                "Constantius I",
                "Galerius",
                "Severus II",
                "Maximinus II",
                "Licinius",
                "Constantine I"
            ],
            "category": "imperial",
            "description": "The tetrarchs and their successors (284-324 AD)"
        }
        
        conn.execute(
            "INSERT OR REPLACE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES (?, ?, ?)",
            ("canonical_series", "Tetrarchy", json.dumps(tetrarchy_series))
        )
        print("   Added Tetrarchy canonical series")
        
        conn.commit()
        
        # =====================================================================
        # Print summary
        # =====================================================================
        print("\n" + "=" * 60)
        print("Historical data corrections applied successfully!")
        print("=" * 60)
        
        cursor = conn.execute(
            "SELECT canonical_name, metadata FROM vocab_terms WHERE vocab_type = 'dynasty' ORDER BY canonical_name"
        )
        print("\nDynasties in database:")
        for row in cursor.fetchall():
            data = json.loads(row[1] or "{}")
            rulers = data.get("rulers", [])
            print(f"  {row[0]}: {len(rulers)} rulers")
        
        cursor = conn.execute(
            "SELECT canonical_name, metadata FROM vocab_terms WHERE vocab_type = 'canonical_series' ORDER BY canonical_name"
        )
        print("\nCanonical series in database:")
        for row in cursor.fetchall():
            data = json.loads(row[1] or "{}")
            count = data.get("expected_count", "?")
            print(f"  {row[0]}: {count} expected")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def main():
    try:
        db_path = get_db_path()
        print(f"Database: {db_path}")
        run_fixes(db_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Failed: {e}")
        raise
    return 0


if __name__ == "__main__":
    exit(main())
