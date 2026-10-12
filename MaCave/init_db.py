#!/usr/bin/env python3
"""Script d'initialisation de la base SQLite locale."""

import sqlite3
from pathlib import Path


def init_db(db_path: Path | str = "macave.db", schema_path: Path | str = "schema.sql") -> None:
    """Crée ou met à jour le schéma de la base de données."""
    db_path = Path(db_path)
    schema_path = Path(schema_path)

    print(f"Connexion à {db_path.resolve()} ...")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"Application du schéma {schema_path} ...")
    with schema_path.open("r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()
    print("Base initialisée avec succès.")


if __name__ == "__main__":
    init_db()
