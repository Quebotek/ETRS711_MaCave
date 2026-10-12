"""Gestion du cycle de vie de la connexion SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType


class Database:
    """Wrapper context-manager autour d'une connexion sqlite3.

    Utilisation :
        with Database("macave.db") as db:
            db.execute("SELECT ...")
    """

    def __init__(self, db_path: Path | str = "macave.db") -> None:
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._connection is not None:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Retourne la connexion active (à utiliser uniquement entre enter/exit)."""
        if self._connection is None:
            raise RuntimeError("La connexion n'est pas ouverte. Utiliser 'with Database() as db:'")
        return self._connection
