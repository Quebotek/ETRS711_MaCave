--\Schema relationnel MaCave (SQLite)
-- Activation des contraintes d'intégrité référentielle

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS caves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS etageres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cave_id INTEGER NOT NULL,
    nom TEXT NOT NULL,
    capacite_max INTEGER NOT NULL DEFAULT 0,
    UNIQUE (cave_id, nom),
    FOREIGN KEY (cave_id) REFERENCES caves(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domaine TEXT NOT NULL,
    cuvee TEXT NOT NULL,
    type_vin TEXT NOT NULL,
    millesime INTEGER NOT NULL,
    region TEXT NOT NULL,
    description TEXT,
    photo_url TEXT
);

CREATE TABLE IF NOT EXISTS bouteilles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin_id INTEGER NOT NULL,
    cave_id INTEGER NOT NULL,
    etagere_id INTEGER,
    prix_achat REAL,
    date_ajout DATE NOT NULL DEFAULT (DATE('now')),
    date_sortie DATE,
    statut TEXT NOT NULL DEFAULT 'en_stock',
    FOREIGN KEY (vin_id) REFERENCES vins(id) ON DELETE RESTRICT,
    FOREIGN KEY (cave_id) REFERENCES caves(id) ON DELETE CASCADE,
    FOREIGN KEY (etagere_id) REFERENCES etageres(id) ON DELETE RESTRICT,
    CHECK (statut IN ('en_stock', 'archivee'))
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER NOT NULL,
    vin_id INTEGER NOT NULL,
    bouteille_id INTEGER NOT NULL,
    note INTEGER NOT NULL,
    commentaire TEXT,
    date_degustation DATE NOT NULL DEFAULT (DATE('now')),
    UNIQUE (utilisateur_id, bouteille_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (vin_id) REFERENCES vins(id) ON DELETE CASCADE,
    FOREIGN KEY (bouteille_id) REFERENCES bouteilles(id) ON DELETE CASCADE,
    CHECK (note >= 0 AND note <= 20)
);
