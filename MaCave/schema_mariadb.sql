-- Schema relationnel MaCave (MariaDB)
-- Compatible MariaDB 10.5+

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS caves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL UNIQUE,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS etageres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cave_id INT NOT NULL,
    nom VARCHAR(255) NOT NULL,
    capacite_max INT NOT NULL DEFAULT 0,
    UNIQUE (cave_id, nom),
    FOREIGN KEY (cave_id) REFERENCES caves(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domaine VARCHAR(255) NOT NULL,
    cuvee VARCHAR(255) NOT NULL,
    type_vin VARCHAR(255) NOT NULL,
    millesime INT NOT NULL,
    region VARCHAR(255) NOT NULL,
    description TEXT,
    photo_url TEXT
);

CREATE TABLE IF NOT EXISTS bouteilles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vin_id INT NOT NULL,
    cave_id INT NOT NULL,
    etagere_id INT,
    prix_achat DECIMAL(10, 2),
    date_ajout DATE NOT NULL DEFAULT CURRENT_DATE,
    date_sortie DATE,
    statut VARCHAR(50) NOT NULL DEFAULT 'en_stock',
    FOREIGN KEY (vin_id) REFERENCES vins(id) ON DELETE RESTRICT,
    FOREIGN KEY (cave_id) REFERENCES caves(id) ON DELETE CASCADE,
    FOREIGN KEY (etagere_id) REFERENCES etageres(id) ON DELETE RESTRICT,
    CHECK (statut IN ('en_stock', 'archivee'))
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    vin_id INT NOT NULL,
    bouteille_id INT NOT NULL,
    note INT NOT NULL,
    commentaire TEXT,
    date_degustation DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (utilisateur_id, bouteille_id),
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id) ON DELETE CASCADE,
    FOREIGN KEY (vin_id) REFERENCES vins(id) ON DELETE CASCADE,
    FOREIGN KEY (bouteille_id) REFERENCES bouteilles(id) ON DELETE CASCADE,
    CHECK (note >= 0 AND note <= 20)
);
