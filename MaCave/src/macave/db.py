from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from types import TracebackType
from typing import Any

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Exception unifiée (IntegrityError SQLite ou MySQL)
try:
    from pymysql.err import IntegrityError
except ImportError:
    pass

# ---------------------------------------------------------------------------
#  MariaDB / MySQL wrapper  (activé si DATABASE_URL commence par mysql)
# ---------------------------------------------------------------------------


class _MySQLCursor:
    """Curseur compatible sqlite3 pour pymysql."""

    def __init__(self, real_cursor: Any) -> None:
        """Initialise le curseur wrapper.

        Args:
            real_cursor: Curseur pymysql sous-jacent.
        """
        self._cursor = real_cursor

    @staticmethod
    def _tr(sql: str) -> str:
        """Traduit les placeholders SQLite (?) en MySQL (%s).

        Args:
            sql: Requête SQL avec placeholders SQLite.

        Returns:
            Requête SQL avec placeholders MySQL.
        """
        return sql.replace("?", "%s")

    def execute(self, sql: str, params: Any = ()) -> _MySQLCursor:
        """Exécute une requête SQL.

        Args:
            sql: Requête SQL.
            params: Paramètres de la requête.

        Returns:
            Le curseur actuel pour chaînage.
        """
        self._cursor.execute(self._tr(sql), params)
        return self

    def executemany(self, sql: str, seq_of_params: Any) -> None:
        """Exécute une requête avec plusieurs jeux de paramètres.

        Args:
            sql: Requête SQL.
            seq_of_params: Séquence de paramètres.
        """
        self._cursor.executemany(self._tr(sql), list(seq_of_params))

    def fetchone(self) -> Any:
        """Récupère la ligne suivante.

        Returns:
            Dictionnaire représentant la ligne ou None.
        """
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self) -> list[Any]:
        """Récupère toutes les lignes restantes.

        Returns:
            Liste de dictionnaires représentant les lignes.
        """
        return [dict(r) for r in self._cursor.fetchall()]

    @property
    def lastrowid(self) -> int | None:
        """Dernier ID inséré."""
        return self._cursor.lastrowid

    @property
    def rowcount(self) -> int:
        """Nombre de lignes affectées."""
        return self._cursor.rowcount

    def close(self) -> None:
        """Ferme le curseur."""
        self._cursor.close()


class _MySQLConnection:
    """Connexion compatible sqlite3 pour pymysql."""

    def __init__(self, conn: Any) -> None:
        """Initialise la connexion wrapper.

        Args:
            conn: Connexion pymysql sous-jacente.
        """
        self._conn = conn

    def cursor(self) -> _MySQLCursor:
        """Crée un nouveau curseur.

        Returns:
            Un curseur compatible.
        """
        return _MySQLCursor(self._conn.cursor())

    def execute(self, sql: str, params: Any = ()) -> _MySQLCursor:
        """Exécute une requête SQL.

        Args:
            sql: Requête SQL.
            params: Paramètres de la requête.

        Returns:
            Un curseur avec les résultats.
        """
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, seq_of_params: Any) -> _MySQLCursor:
        """Exécute une requête avec plusieurs jeux de paramètres.

        Args:
            sql: Requête SQL.
            seq_of_params: Séquence de paramètres.

        Returns:
            Un curseur avec les résultats.
        """
        cur = self.cursor()
        cur.executemany(sql, seq_of_params)
        return cur

    def executescript(self, sql: str) -> None:
        """Exécute un script SQL multi-lignes (compatible init_db).

        Args:
            sql: Script SQL complet.
        """
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        for stmt in stmts:
            if stmt.lower().startswith("pragma"):
                continue
            self.execute(stmt)

    def commit(self) -> None:
        """Valide la transaction en cours."""
        self._conn.commit()

    def rollback(self) -> None:
        """Annule la transaction en cours."""
        self._conn.rollback()

    def close(self) -> None:
        """Ferme la connexion."""
        self._conn.close()

    def __enter__(self) -> _MySQLConnection:
        """Gestionnaire de contexte - entrée."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Gestionnaire de contexte - sortie.

        Args:
            exc_type: Type d'exception si levée.
            exc_val: Valeur de l'exception.
            exc_tb: Traceback de l'exception.
        """
        if exc_type is None:
            self.commit()
        else:
            self.rollback()


def _parse_mysql_url(url: str) -> dict[str, str]:
    """Parse une URL de connexion MySQL.

    Args:
        url: URL au format mysql+pymysql://user:pass@host:port/db

    Returns:
        Dictionnaire avec user, password, host, port, database.

    Raises:
        ValueError: Si le format d'URL est invalide.
    """
    m = re.match(
        r"mysql+pymysql://([^:]+):([^@]+)@([^/:]+)(?::(\d+))?/(.+)", url
    )
    if not m:
        raise ValueError(f"DATABASE_URL invalide : {url}")
    return {
        "user": m.group(1),
        "password": m.group(2),
        "host": m.group(3),
        "port": m.group(4) or "3306",
        "database": m.group(5),
    }


def _connect_mysql() -> _MySQLConnection:
    """Établit une connexion MySQL via pymysql.

    Returns:
        Wrapper de connexion compatible.
    """
    import pymysql
    from pymysql.cursors import DictCursor

    parsed = _parse_mysql_url(DATABASE_URL)
    conn = pymysql.connect(
        host=parsed["host"],
        user=parsed["user"],
        password=parsed["password"],
        database=parsed["database"],
        port=int(parsed["port"]),
        cursorclass=DictCursor,
        charset="utf8mb4",
        autocommit=False,
    )
    return _MySQLConnection(conn)


# ---------------------------------------------------------------------------
#  SQLite driver utilisé par défaut (absence de DATABASE_URL)
# ---------------------------------------------------------------------------


class Database:
    """Wrapper context-manager autour d'une connexion sqlite3.

    Utilisation:
        with Database("macave.db") as db:
            db.execute("SELECT ...")
    """

    def __init__(self, db_path: Path | str = "macave.db") -> None:
        """Initialise la base de données.

        Args:
            db_path: Chemin vers le fichier SQLite.
        """
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | _MySQLConnection | None = None

    def __enter__(self) -> Any:
        """Ouvre la connexion (SQLite ou MySQL selon DATABASE_URL).

        Returns:
            Connexion configurée.
        """
        if DATABASE_URL:
            self._connection = _connect_mysql()
            return self._connection

        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row  # type: ignore[union-attr]
        self._connection.execute("PRAGMA foreign_keys = ON")  # type: ignore[union-attr]
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Ferme la connexion et gère la transaction.

        Args:
            exc_type: Type d'exception si levée.
            exc_val: Valeur de l'exception.
            exc_tb: Traceback de l'exception.
        """
        if self._connection is not None:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> Any:
        """Retourne la connexion active.

        Returns:
            La connexion SQLite ou MySQL.

        Raises:
            RuntimeError: Si la connexion n'est pas ouverte.
        """
        if self._connection is None:
            raise RuntimeError(
                "La connexion n'est pas ouverte. Utiliser 'with Database() as db:'"
            )
        return self._connection


def get_db(db_path: Path | str = "macave.db") -> Any:
    """Retourne une nouvelle connexion SQLite ou MySQL (usage hors-Flask / tests).

    Args:
        db_path: Chemin vers le fichier SQLite (ignoré si DATABASE_URL est défini).

    Returns:
        Connexion configurée avec row_factory = sqlite3.Row (SQLite) ou
        DictCursor (MySQL) et foreign_keys activées (SQLite).
    """
    if DATABASE_URL:
        return _connect_mysql()

    conn = sqlite3.connect(Path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
