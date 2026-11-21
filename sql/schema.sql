-- Schéma de la base SQLite du projet.
-- Deux tables : les transactions reçues (données "brutes") et le journal des anomalies.

-- Données brutes reçues. Volontairement SANS contraintes (pas de clé unique sur
-- transaction_id, colonnes nullables) : c'est ce qui arrive dans la vraie vie avec
-- des flux externes, et c'est justement ce que les contrôles qualité vérifient.
-- row_id est une clé technique de ligne, il permet de distinguer deux lignes
-- qui portent le même transaction_id.
CREATE TABLE IF NOT EXISTS transactions (
    row_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id  TEXT,
    product         TEXT,
    trade_date      TEXT,   -- format attendu : YYYY-MM-DD
    settlement_date TEXT,   -- format attendu : YYYY-MM-DD
    amount          REAL,
    currency        TEXT,
    counterparty    TEXT,
    status          TEXT
);

-- Journal des exceptions : une ligne = une anomalie détectée sur une transaction.
-- Sert au suivi de la remédiation (qui doit corriger, depuis quand, est-ce résolu ?).
CREATE TABLE IF NOT EXISTS exception_log (
    exception_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id         INTEGER NOT NULL,   -- ligne source concernée
    transaction_id TEXT,
    check_type     TEXT NOT NULL,      -- Completeness / Validity / Uniqueness / Consistency
    rule           TEXT NOT NULL,      -- code de la règle (ex. INVALID_CURRENCY)
    description    TEXT NOT NULL,
    owner_team     TEXT NOT NULL,      -- équipe qui doit intervenir
    status         TEXT NOT NULL DEFAULT 'À corriger',  -- À corriger / En cours / Résolu
    detected_date  TEXT NOT NULL,
    resolved_date  TEXT,
    comment        TEXT,
    UNIQUE (row_id, rule)              -- une même anomalie n'est loguée qu'une fois
);
