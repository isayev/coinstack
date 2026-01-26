"""
Migration script to add vocab_aliases table and populate vocabulary.

This script:
1. Creates the vocab_aliases table for alias support
2. Adds missing issuers from the collection
3. Adds missing mints with aliases for variations
4. Adds denominations vocabulary
5. Rebuilds FTS5 index
"""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent / "coinstack_v2.db"


def create_aliases_table(conn: sqlite3.Connection):
    """Create the vocab_aliases table."""
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vocab_aliases'")
    if cursor.fetchone():
        print("  vocab_aliases table already exists")
        return
    
    cursor.execute("""
        CREATE TABLE vocab_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vocab_term_id INTEGER NOT NULL REFERENCES vocab_terms(id) ON DELETE CASCADE,
            alias_name VARCHAR(200) NOT NULL,
            alias_type VARCHAR(50) DEFAULT 'variant',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vocab_term_id, alias_name)
        )
    """)
    
    # Create index for fast alias lookup
    cursor.execute("""
        CREATE INDEX idx_vocab_aliases_name ON vocab_aliases(alias_name)
    """)
    
    # Create index for case-insensitive lookup
    cursor.execute("""
        CREATE INDEX idx_vocab_aliases_name_lower ON vocab_aliases(LOWER(alias_name))
    """)
    
    print("  Created vocab_aliases table with indexes")


def add_issuers(conn: sqlite3.Connection):
    """Add missing issuers from the collection."""
    cursor = conn.cursor()
    
    # Issuers to add with metadata
    issuers = [
        # Julio-Claudian (existing: Augustus, Tiberius, Caligula, Claudius, Nero)
        
        # Flavian (existing: Vespasian, Titus, Domitian)
        
        # Nerva-Antonine (existing: Trajan, Hadrian, Marcus Aurelius)
        ("Nerva", {"reign_start": 96, "reign_end": 98, "issuer_type": "emperor"}),
        ("Antoninus Pius", {"reign_start": 138, "reign_end": 161, "issuer_type": "emperor"}),
        ("Lucius Verus", {"reign_start": 161, "reign_end": 169, "issuer_type": "emperor"}),
        ("Commodus", {"reign_start": 177, "reign_end": 192, "issuer_type": "emperor"}),
        
        # Severan
        ("Septimius Severus", {"reign_start": 193, "reign_end": 211, "issuer_type": "emperor"}),
        ("Caracalla", {"reign_start": 198, "reign_end": 217, "issuer_type": "emperor"}),
        ("Geta", {"reign_start": 209, "reign_end": 211, "issuer_type": "emperor"}),
        ("Macrinus", {"reign_start": 217, "reign_end": 218, "issuer_type": "emperor"}),
        ("Elagabalus", {"reign_start": 218, "reign_end": 222, "issuer_type": "emperor"}),
        ("Severus Alexander", {"reign_start": 222, "reign_end": 235, "issuer_type": "emperor"}),
        ("Julia Domna", {"reign_start": 193, "reign_end": 217, "issuer_type": "empress"}),
        ("Julia Maesa", {"reign_start": 218, "reign_end": 224, "issuer_type": "empress"}),
        ("Julia Mamaea", {"reign_start": 222, "reign_end": 235, "issuer_type": "empress"}),
        
        # Military Emperors / Crisis of 3rd Century
        ("Maximinus I Thrax", {"reign_start": 235, "reign_end": 238, "issuer_type": "emperor"}),
        ("Gordian I", {"reign_start": 238, "reign_end": 238, "issuer_type": "emperor"}),
        ("Gordian II", {"reign_start": 238, "reign_end": 238, "issuer_type": "emperor"}),
        ("Gordian III", {"reign_start": 238, "reign_end": 244, "issuer_type": "emperor"}),
        ("Pupienus", {"reign_start": 238, "reign_end": 238, "issuer_type": "emperor"}),
        ("Balbinus", {"reign_start": 238, "reign_end": 238, "issuer_type": "emperor"}),
        ("Philip I Arab", {"reign_start": 244, "reign_end": 249, "issuer_type": "emperor"}),
        ("Philip II", {"reign_start": 247, "reign_end": 249, "issuer_type": "emperor"}),
        ("Decius", {"reign_start": 249, "reign_end": 251, "issuer_type": "emperor"}),
        ("Herennius Etruscus", {"reign_start": 251, "reign_end": 251, "issuer_type": "emperor"}),
        ("Hostilian", {"reign_start": 251, "reign_end": 251, "issuer_type": "emperor"}),
        ("Trebonianus Gallus", {"reign_start": 251, "reign_end": 253, "issuer_type": "emperor"}),
        ("Volusian", {"reign_start": 251, "reign_end": 253, "issuer_type": "emperor"}),
        ("Aemilian", {"reign_start": 253, "reign_end": 253, "issuer_type": "emperor"}),
        ("Valerian I", {"reign_start": 253, "reign_end": 260, "issuer_type": "emperor"}),
        ("Gallienus", {"reign_start": 253, "reign_end": 268, "issuer_type": "emperor"}),
        ("Salonina", {"reign_start": 253, "reign_end": 268, "issuer_type": "empress"}),
        ("Claudius II Gothicus", {"reign_start": 268, "reign_end": 270, "issuer_type": "emperor"}),
        ("Quintillus", {"reign_start": 270, "reign_end": 270, "issuer_type": "emperor"}),
        ("Aurelian", {"reign_start": 270, "reign_end": 275, "issuer_type": "emperor"}),
        ("Tacitus", {"reign_start": 275, "reign_end": 276, "issuer_type": "emperor"}),
        ("Florian", {"reign_start": 276, "reign_end": 276, "issuer_type": "emperor"}),
        ("Probus", {"reign_start": 276, "reign_end": 282, "issuer_type": "emperor"}),
        ("Carus", {"reign_start": 282, "reign_end": 283, "issuer_type": "emperor"}),
        ("Carinus", {"reign_start": 283, "reign_end": 285, "issuer_type": "emperor"}),
        ("Numerian", {"reign_start": 283, "reign_end": 284, "issuer_type": "emperor"}),
        
        # Gallic Empire
        ("Postumus", {"reign_start": 260, "reign_end": 269, "issuer_type": "usurper"}),
        ("Laelianus", {"reign_start": 269, "reign_end": 269, "issuer_type": "usurper"}),
        ("Marius", {"reign_start": 269, "reign_end": 269, "issuer_type": "usurper"}),
        ("Victorinus", {"reign_start": 269, "reign_end": 271, "issuer_type": "usurper"}),
        ("Tetricus I", {"reign_start": 271, "reign_end": 274, "issuer_type": "usurper"}),
        ("Tetricus II", {"reign_start": 273, "reign_end": 274, "issuer_type": "usurper"}),
        
        # Tetrarchy and Constantinian
        ("Diocletian", {"reign_start": 284, "reign_end": 305, "issuer_type": "emperor"}),
        ("Maximian", {"reign_start": 286, "reign_end": 305, "issuer_type": "emperor"}),
        ("Constantius I Chlorus", {"reign_start": 293, "reign_end": 306, "issuer_type": "emperor"}),
        ("Galerius", {"reign_start": 293, "reign_end": 311, "issuer_type": "emperor"}),
        ("Severus II", {"reign_start": 306, "reign_end": 307, "issuer_type": "emperor"}),
        ("Maxentius", {"reign_start": 306, "reign_end": 312, "issuer_type": "usurper"}),
        ("Licinius I", {"reign_start": 308, "reign_end": 324, "issuer_type": "emperor"}),
        ("Licinius II", {"reign_start": 317, "reign_end": 324, "issuer_type": "emperor"}),
        ("Constantine I", {"reign_start": 306, "reign_end": 337, "issuer_type": "emperor"}),
        ("Constantine II", {"reign_start": 337, "reign_end": 340, "issuer_type": "emperor"}),
        ("Constans", {"reign_start": 337, "reign_end": 350, "issuer_type": "emperor"}),
        ("Constantius II", {"reign_start": 337, "reign_end": 361, "issuer_type": "emperor"}),
        ("Magnentius", {"reign_start": 350, "reign_end": 353, "issuer_type": "usurper"}),
        ("Julian II", {"reign_start": 360, "reign_end": 363, "issuer_type": "emperor"}),
        ("Jovian", {"reign_start": 363, "reign_end": 364, "issuer_type": "emperor"}),
        
        # Valentinianic
        ("Valentinian I", {"reign_start": 364, "reign_end": 375, "issuer_type": "emperor"}),
        ("Valens", {"reign_start": 364, "reign_end": 378, "issuer_type": "emperor"}),
        ("Gratian", {"reign_start": 367, "reign_end": 383, "issuer_type": "emperor"}),
        ("Valentinian II", {"reign_start": 375, "reign_end": 392, "issuer_type": "emperor"}),
        
        # Theodosian (existing: Honorius, Zeno)
        ("Theodosius I", {"reign_start": 379, "reign_end": 395, "issuer_type": "emperor"}),
        ("Arcadius", {"reign_start": 383, "reign_end": 408, "issuer_type": "emperor"}),
        ("Theodosius II", {"reign_start": 408, "reign_end": 450, "issuer_type": "emperor"}),
        ("Valentinian III", {"reign_start": 425, "reign_end": 455, "issuer_type": "emperor"}),
        
        # Special cases
        ("Coson", {"reign_start": -50, "reign_end": -29, "issuer_type": "king"}),  # Dacian/Thracian king
        ("C. Malleolus", {"issuer_type": "moneyer"}),  # Republican moneyer
    ]
    
    added = 0
    for name, metadata in issuers:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata)
                VALUES (?, ?, ?)
            """, ("issuer", name, json.dumps(metadata)))
            if cursor.rowcount > 0:
                added += 1
        except Exception as e:
            print(f"  Error adding issuer {name}: {e}")
    
    print(f"  Added {added} issuers")
    
    # Add issuer aliases
    issuer_aliases = [
        ("Galerius", ["Galerius Maximianus", "Galerius Maximianu"]),
        ("Constantine I", ["Constantine the Great"]),
        ("Julian II", ["Julian the Apostate"]),
        ("Claudius II Gothicus", ["Claudius Gothicus", "Claudius II"]),
        ("Philip I Arab", ["Philip I", "Philip the Arab"]),
        ("Maximinus I Thrax", ["Maximinus Thrax", "Maximinus I"]),
        ("Trebonianus Gallus", ["Gallus"]),
    ]
    
    alias_count = 0
    for canonical, aliases in issuer_aliases:
        cursor.execute("SELECT id FROM vocab_terms WHERE vocab_type='issuer' AND canonical_name=?", (canonical,))
        row = cursor.fetchone()
        if row:
            term_id = row[0]
            for alias in aliases:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO vocab_aliases (vocab_term_id, alias_name, alias_type)
                        VALUES (?, ?, 'variant')
                    """, (term_id, alias))
                    if cursor.rowcount > 0:
                        alias_count += 1
                except Exception as e:
                    pass
    
    print(f"  Added {alias_count} issuer aliases")


def add_mints(conn: sqlite3.Connection):
    """Add missing mints with aliases."""
    cursor = conn.cursor()
    
    # Mints to add with metadata and aliases
    mints_data = [
        # (canonical_name, metadata, [aliases])
        ("Siscia", {"modern_name": "Sisak, Croatia", "ric_abbrev": "SIS"}, ["Sisak"]),
        ("Cyzicus", {"modern_name": "Erdek, Turkey", "ric_abbrev": "K"}, ["Cyzikos", "Kyzikos"]),
        ("Heraclea", {"modern_name": "Marmara Ereğlisi, Turkey", "ric_abbrev": "H"}, ["Herakleia", "Heraclea Pontica"]),
        ("Nicomedia", {"modern_name": "İzmit, Turkey", "ric_abbrev": "N"}, ["Nikomedeia"]),
        ("Thessalonica", {"modern_name": "Thessaloniki, Greece", "ric_abbrev": "TES"}, ["Thessaloniki"]),
        ("Serdica", {"modern_name": "Sofia, Bulgaria", "ric_abbrev": "SER"}, ["Sofia"]),
        ("Ticinum", {"modern_name": "Pavia, Italy", "ric_abbrev": "T"}, ["Pavia"]),
        ("Aquileia", {"modern_name": "Aquileia, Italy", "ric_abbrev": "AQ"}, []),
        ("Ravenna", {"modern_name": "Ravenna, Italy", "ric_abbrev": "R"}, []),
        ("Londinium", {"modern_name": "London, UK", "ric_abbrev": "LON"}, ["London"]),
        ("Carthage", {"modern_name": "Carthage, Tunisia", "ric_abbrev": "K"}, ["Karthago"]),
        ("Mediolanum", {"modern_name": "Milan, Italy", "ric_abbrev": "MD"}, ["Milan"]),
        ("Lugdunum", {"modern_name": "Lyon, France", "ric_abbrev": "LVG"}, []),  # Lyon already exists
        ("Arelate", {"modern_name": "Arles, France", "ric_abbrev": "AR"}, ["Arles"]),
        ("Sirmium", {"modern_name": "Sremska Mitrovica, Serbia", "ric_abbrev": "SIRM"}, []),
        ("Apameia", {"modern_name": "Apamea, Syria"}, ["Apameia, Syria"]),
        ("Caesarea", {"modern_name": "Kayseri, Turkey"}, ["CAPPADOCIA, Caesarea-Eusebia", "Caesarea-Eusebia", "Caesarea Cappadociae"]),
        ("Emesa", {"modern_name": "Homs, Syria"}, []),
        ("Samosata", {"modern_name": "Samsat, Turkey"}, []),
        ("Viminacium", {"modern_name": "Kostolac, Serbia"}, []),
    ]
    
    added = 0
    for canonical, metadata, aliases in mints_data:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata)
                VALUES (?, ?, ?)
            """, ("mint", canonical, json.dumps(metadata)))
            if cursor.rowcount > 0:
                added += 1
        except Exception as e:
            print(f"  Error adding mint {canonical}: {e}")
    
    print(f"  Added {added} mints")
    
    # Add aliases for ALL mints (including existing ones)
    all_mint_aliases = [
        # Existing mints
        ("Rome", ["Roma", "ROMA", "Rome mint"]),
        ("Antioch", ["Antiochia", "ANTIOCH", "Antioch, Syria"]),
        ("Lyon", ["Lugdunum", "LVG"]),
        ("Constantinople", ["Constantinopolis", "CONST"]),
        ("Alexandria", ["Alexandria, Egypt"]),
        ("Trier", ["Treveri", "TR"]),
        # New mints (from above)
        ("Siscia", ["Sisak"]),
        ("Cyzicus", ["Cyzikos", "Kyzikos"]),
        ("Heraclea", ["Herakleia", "Heraclea Pontica"]),
        ("Nicomedia", ["Nikomedeia"]),
        ("Thessalonica", ["Thessaloniki"]),
        ("Serdica", ["Sofia"]),
        ("Ticinum", ["Pavia"]),
        ("Londinium", ["London"]),
        ("Carthage", ["Karthago"]),
        ("Mediolanum", ["Milan"]),
        ("Arelate", ["Arles"]),
        ("Apameia", ["Apameia, Syria"]),
        ("Caesarea", ["CAPPADOCIA, Caesarea-Eusebia", "Caesarea-Eusebia", "Caesarea Cappadociae"]),
    ]
    
    alias_count = 0
    for canonical, aliases in all_mint_aliases:
        cursor.execute("SELECT id FROM vocab_terms WHERE vocab_type='mint' AND canonical_name=?", (canonical,))
        row = cursor.fetchone()
        if row:
            term_id = row[0]
            for alias in aliases:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO vocab_aliases (vocab_term_id, alias_name, alias_type)
                        VALUES (?, ?, 'variant')
                    """, (term_id, alias))
                    if cursor.rowcount > 0:
                        alias_count += 1
                except Exception as e:
                    pass
    
    print(f"  Added {alias_count} mint aliases")


def add_denominations(conn: sqlite3.Connection):
    """Add denomination vocabulary."""
    cursor = conn.cursor()
    
    denominations = [
        # Silver
        ("Denarius", {"metal": "silver", "typical_weight_g": 3.9, "period": "211 BC - 238 AD"}),
        ("Quinarius", {"metal": "silver", "typical_weight_g": 1.9, "period": "211 BC - 3rd c. AD"}),
        ("Victoriatus", {"metal": "silver", "typical_weight_g": 3.4, "period": "211 - 170 BC"}),
        
        # Billon/Silver antoninianus era
        ("Antoninianus", {"metal": "billon", "typical_weight_g": 3.5, "period": "215 - 294 AD"}),
        ("Aurelianus", {"metal": "billon", "typical_weight_g": 4.0, "period": "274 - 294 AD"}),
        
        # Gold
        ("Aureus", {"metal": "gold", "typical_weight_g": 7.8, "period": "211 BC - 309 AD"}),
        ("Solidus", {"metal": "gold", "typical_weight_g": 4.5, "period": "309 AD onwards"}),
        ("Tremissis", {"metal": "gold", "typical_weight_g": 1.5, "period": "383 AD onwards"}),
        ("Semissis", {"metal": "gold", "typical_weight_g": 2.25, "period": "4th c. AD onwards"}),
        
        # Base metal imperial
        ("Sestertius", {"metal": "orichalcum", "typical_weight_g": 25.0, "period": "23 BC - 260s AD"}),
        ("Dupondius", {"metal": "orichalcum", "typical_weight_g": 12.5, "period": "23 BC - 260s AD"}),
        ("As", {"metal": "copper", "typical_weight_g": 10.0, "period": "3rd c. BC - 260s AD"}),
        ("Semis", {"metal": "copper", "typical_weight_g": 5.0, "period": "Roman Republic"}),
        ("Quadrans", {"metal": "copper", "typical_weight_g": 2.5, "period": "Roman Republic"}),
        
        # Late Roman bronze
        ("Follis", {"metal": "bronze", "typical_weight_g": 10.0, "period": "294 - 348 AD"}),
        ("Nummus", {"metal": "bronze", "typical_weight_g": 3.0, "period": "294 AD onwards"}),
        ("Centenionalis", {"metal": "bronze", "typical_weight_g": 4.5, "period": "348 - 354 AD"}),
        ("Maiorina", {"metal": "bronze", "typical_weight_g": 5.0, "period": "348 - 354 AD"}),
        ("Æ1", {"metal": "bronze", "typical_weight_g": 8.0, "size": "25mm+"}),
        ("Æ2", {"metal": "bronze", "typical_weight_g": 5.0, "size": "21-25mm"}),
        ("Æ3", {"metal": "bronze", "typical_weight_g": 2.5, "size": "17-21mm"}),
        ("Æ4", {"metal": "bronze", "typical_weight_g": 1.5, "size": "under 17mm"}),
        
        # Late Roman silver
        ("Siliqua", {"metal": "silver", "typical_weight_g": 2.25, "period": "4th c. AD onwards"}),
        ("Miliarense", {"metal": "silver", "typical_weight_g": 4.5, "period": "4th c. AD onwards"}),
        
        # Provincial
        ("Tetradrachm", {"metal": "silver", "typical_weight_g": 13.0, "period": "Provincial coinage"}),
        ("Drachm", {"metal": "silver", "typical_weight_g": 3.5, "period": "Provincial coinage"}),
        ("Didrachm", {"metal": "silver", "typical_weight_g": 7.0, "period": "Provincial coinage"}),
        ("Obol", {"metal": "silver", "typical_weight_g": 0.6, "period": "Greek/Provincial"}),
        
        # Republic
        ("Stater", {"metal": "gold", "typical_weight_g": 8.0, "period": "Greek/Celtic"}),
    ]
    
    added = 0
    for name, metadata in denominations:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata)
                VALUES (?, ?, ?)
            """, ("denomination", name, json.dumps(metadata)))
            if cursor.rowcount > 0:
                added += 1
        except Exception as e:
            print(f"  Error adding denomination {name}: {e}")
    
    print(f"  Added {added} denominations")


def rebuild_fts_index(conn: sqlite3.Connection):
    """Rebuild the FTS5 index to include all vocabulary."""
    cursor = conn.cursor()
    
    # Clear and rebuild FTS index
    cursor.execute("DELETE FROM vocab_terms_fts")
    cursor.execute("""
        INSERT INTO vocab_terms_fts (rowid, canonical_name)
        SELECT id, canonical_name FROM vocab_terms
    """)
    
    # Also index aliases
    cursor.execute("""
        INSERT INTO vocab_terms_fts (rowid, canonical_name)
        SELECT va.vocab_term_id, va.alias_name 
        FROM vocab_aliases va
    """)
    
    print("  Rebuilt FTS5 index with aliases")


def print_summary(conn: sqlite3.Connection):
    """Print vocabulary summary."""
    cursor = conn.cursor()
    
    print("\n=== VOCABULARY SUMMARY ===")
    cursor.execute("SELECT vocab_type, COUNT(*) FROM vocab_terms GROUP BY vocab_type ORDER BY vocab_type")
    for vtype, count in cursor.fetchall():
        print(f"  {vtype}: {count} terms")
    
    cursor.execute("SELECT COUNT(*) FROM vocab_aliases")
    alias_count = cursor.fetchone()[0]
    print(f"  aliases: {alias_count} total")


def main():
    """Run the migration."""
    print(f"Opening database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        print("\n[1/6] Creating vocab_aliases table...")
        create_aliases_table(conn)
        
        print("\n[2/6] Adding issuers...")
        add_issuers(conn)
        
        print("\n[3/6] Adding mints...")
        add_mints(conn)
        
        print("\n[4/6] Adding denominations...")
        add_denominations(conn)
        
        print("\n[5/6] Rebuilding FTS5 index...")
        rebuild_fts_index(conn)
        
        print("\n[6/6] Committing changes...")
        conn.commit()
        
        print_summary(conn)
        print("\n✅ Migration complete!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
