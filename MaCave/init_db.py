#!/usr/bin/env python3
"""Script d'initialisation de la base SQLite ou MariaDB."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def init_db(
    db_path: Path | str | None = None,
    schema_path: Path | str | None = None,
) -> None:
    """Crée ou met à jour le schéma de la base de données."""
    database_url = os.environ.get("DATABASE_URL", "")

    if database_url:
        # --- mode MariaDB ---
        from macave.db import _connect_mysql

        schema_file = Path(schema_path) if schema_path else Path("schema_mariadb.sql")
        print(f"Connexion MariaDB : {database_url} ...")
        conn = _connect_mysql()
        print(f"Application du schéma {schema_file} ...")
        with schema_file.open("r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
    else:
        # --- mode SQLite ---
        if db_path is None:
            db_path = os.environ.get("DATABASE_PATH", "macave.db")
        db_path = Path(db_path)
        schema_file = Path(schema_path) if schema_path else Path("schema.sql")

        print(f"Connexion à {db_path.resolve()} ...")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        print(f"Application du schéma {schema_file} ...")
        with schema_file.open("r", encoding="utf-8") as f:
            conn.executescript(f.read())

        conn.commit()
        conn.close()

    print("Base initialisée avec succès.")


if __name__ == "__main__":
    init_db()
