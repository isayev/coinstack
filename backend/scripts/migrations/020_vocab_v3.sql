-- ============================================
-- VOCAB V3 MIGRATION (Zero-Downtime)
-- Run with: sqlite3 coinstack_v2.db < 020_vocab_v3.sql
-- ============================================

-- 1. Unified vocab terms (content table)
CREATE TABLE IF NOT EXISTS vocab_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_type TEXT NOT NULL,           -- 'issuer', 'mint', 'denomination', 'dynasty', 'canonical_series'
    canonical_name TEXT NOT NULL,
    nomisma_uri TEXT,
    metadata TEXT,                       -- JSON blob
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vocab_type, canonical_name)
);
CREATE INDEX IF NOT EXISTS ix_vocab_terms_type ON vocab_terms(vocab_type);

-- 2. FTS5 index for fast search (external content table)
CREATE VIRTUAL TABLE IF NOT EXISTS vocab_terms_fts USING fts5(
    canonical_name, 
    content=vocab_terms, 
    content_rowid=id,
    tokenize='porter unicode61'
);

-- 3. Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS vocab_terms_ai AFTER INSERT ON vocab_terms BEGIN
    INSERT INTO vocab_terms_fts(rowid, canonical_name) VALUES (new.id, new.canonical_name);
END;
CREATE TRIGGER IF NOT EXISTS vocab_terms_ad AFTER DELETE ON vocab_terms BEGIN
    INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name) VALUES('delete', old.id, old.canonical_name);
END;
CREATE TRIGGER IF NOT EXISTS vocab_terms_au AFTER UPDATE ON vocab_terms BEGIN
    INSERT INTO vocab_terms_fts(vocab_terms_fts, rowid, canonical_name) VALUES('delete', old.id, old.canonical_name);
    INSERT INTO vocab_terms_fts(rowid, canonical_name) VALUES (new.id, new.canonical_name);
END;

-- 4. Audit trail + review queue (combined)
CREATE TABLE IF NOT EXISTS coin_vocab_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,           -- 'issuer', 'mint', 'denomination', 'dynasty'
    raw_value TEXT NOT NULL,
    vocab_term_id INTEGER,
    confidence REAL,
    method TEXT,                        -- 'exact', 'fts', 'nomisma', 'llm', 'manual'
    status TEXT DEFAULT 'assigned',     -- 'assigned', 'pending_review', 'approved', 'rejected'
    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT,
    FOREIGN KEY(coin_id) REFERENCES coins_v2(id),
    FOREIGN KEY(vocab_term_id) REFERENCES vocab_terms(id)
);
CREATE INDEX IF NOT EXISTS ix_cva_coin ON coin_vocab_assignments(coin_id);
CREATE INDEX IF NOT EXISTS ix_cva_status ON coin_vocab_assignments(status);

-- 5. Simple cache (1hr TTL for search, 1yr for external APIs)
CREATE TABLE IF NOT EXISTS vocab_cache (
    cache_key TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_vocab_cache_expires ON vocab_cache(expires_at);

-- 6. Add new FK columns to coins_v2 (nullable, zero-downtime)
-- Note: SQLite ALTER TABLE only supports adding columns, so we use separate statements
-- These will fail silently if column already exists (use IF NOT EXISTS workaround via pragma)

-- Check and add issuer_term_id
SELECT CASE 
    WHEN (SELECT COUNT(*) FROM pragma_table_info('coins_v2') WHERE name='issuer_term_id') = 0 
    THEN 'ALTER TABLE coins_v2 ADD COLUMN issuer_term_id INTEGER REFERENCES vocab_terms(id)'
END;

-- For SQLite, we'll handle column additions in Python migration script
-- Here we document the expected schema changes:
-- ALTER TABLE coins_v2 ADD COLUMN issuer_term_id INTEGER REFERENCES vocab_terms(id);
-- ALTER TABLE coins_v2 ADD COLUMN mint_term_id INTEGER REFERENCES vocab_terms(id);
-- ALTER TABLE coins_v2 ADD COLUMN denomination_term_id INTEGER REFERENCES vocab_terms(id);
-- ALTER TABLE coins_v2 ADD COLUMN dynasty_term_id INTEGER REFERENCES vocab_terms(id);

-- 7. Add canonical vocab link to series table (for canonical series definitions)
-- ALTER TABLE series ADD COLUMN canonical_vocab_id INTEGER REFERENCES vocab_terms(id);

-- 8. Bootstrap dynasty data (migrate from search_service.py DYNASTY_RULERS)
INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES
    ('dynasty', 'Julio-Claudian', '{"period_start": -27, "period_end": 68, "rulers": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"]}'),
    ('dynasty', 'Flavian', '{"period_start": 69, "period_end": 96, "rulers": ["Vespasian", "Titus", "Domitian"]}'),
    ('dynasty', 'Nerva-Antonine', '{"period_start": 96, "period_end": 192, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius", "Lucius Verus", "Commodus"]}'),
    ('dynasty', 'Severan', '{"period_start": 193, "period_end": 235, "rulers": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"]}'),
    ('dynasty', 'Constantinian', '{"period_start": 306, "period_end": 363, "rulers": ["Constantine I", "Constantine II", "Constans", "Constantius II", "Julian"]}'),
    ('dynasty', 'Theodosian', '{"period_start": 379, "period_end": 455, "rulers": ["Theodosius I", "Arcadius", "Honorius", "Theodosius II"]}'),
    ('dynasty', 'Tetrarchy', '{"period_start": 284, "period_end": 324, "rulers": ["Diocletian", "Maximian", "Constantius I", "Galerius"]}'),
    ('dynasty', 'Valentinianic', '{"period_start": 364, "period_end": 392, "rulers": ["Valentinian I", "Valens", "Gratian", "Valentinian II"]}'),
    ('dynasty', 'Year of Four Emperors', '{"period_start": 69, "period_end": 69, "rulers": ["Galba", "Otho", "Vitellius", "Vespasian"]}'),
    ('dynasty', 'Military Emperors', '{"period_start": 235, "period_end": 284, "rulers": ["Maximinus I", "Gordian I", "Gordian II", "Gordian III", "Philip I", "Decius", "Trebonianus Gallus", "Valerian", "Gallienus"]}'),
    ('dynasty', 'Gallic Empire', '{"period_start": 260, "period_end": 274, "rulers": ["Postumus", "Victorinus", "Tetricus I", "Tetricus II"]}'),
    ('dynasty', 'Late Republic', '{"period_start": -133, "period_end": -27, "rulers": ["Sulla", "Pompey", "Caesar", "Brutus", "Cassius", "Mark Antony", "Octavian"]}');

-- 9. Bootstrap canonical series definitions
INSERT OR IGNORE INTO vocab_terms (vocab_type, canonical_name, metadata) VALUES
    ('canonical_series', 'Twelve Caesars', '{"expected_count": 12, "rulers": ["Julius Caesar", "Augustus", "Tiberius", "Caligula", "Claudius", "Nero", "Galba", "Otho", "Vitellius", "Vespasian", "Titus", "Domitian"], "category": "imperial", "description": "The twelve rulers from Julius Caesar through Domitian, as chronicled by Suetonius"}'),
    ('canonical_series', 'Five Good Emperors', '{"expected_count": 5, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"], "category": "imperial", "description": "The five emperors who presided over the most prosperous era in Roman history (96-180 AD)"}'),
    ('canonical_series', 'Year of Four Emperors', '{"expected_count": 4, "rulers": ["Galba", "Otho", "Vitellius", "Vespasian"], "category": "imperial", "description": "The four emperors who ruled in 69 AD during the civil war"}'),
    ('canonical_series', 'Adoptive Emperors', '{"expected_count": 5, "rulers": ["Nerva", "Trajan", "Hadrian", "Antoninus Pius", "Marcus Aurelius"], "category": "imperial", "description": "Emperors who adopted their successors rather than passing power to biological heirs"}'),
    ('canonical_series', 'Severan Dynasty', '{"expected_count": 6, "rulers": ["Septimius Severus", "Caracalla", "Geta", "Macrinus", "Elagabalus", "Severus Alexander"], "category": "imperial", "description": "The Severan dynasty emperors (193-235 AD)"}'),
    ('canonical_series', 'Julio-Claudian Dynasty', '{"expected_count": 5, "rulers": ["Augustus", "Tiberius", "Caligula", "Claudius", "Nero"], "category": "imperial", "description": "The first Roman imperial dynasty"}'),
    ('canonical_series', 'Flavian Dynasty', '{"expected_count": 3, "rulers": ["Vespasian", "Titus", "Domitian"], "category": "imperial", "description": "The Flavian dynasty emperors (69-96 AD)"}'),
    ('canonical_series', 'Constantinian Dynasty', '{"expected_count": 5, "rulers": ["Constantine I", "Constantine II", "Constans", "Constantius II", "Julian"], "category": "imperial", "description": "The Constantinian dynasty emperors (306-363 AD)"}');
