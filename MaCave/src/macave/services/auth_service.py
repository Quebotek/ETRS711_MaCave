"""Services d'authentification et gestion des comptes."""

from __future__ import annotations

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from macave.models import Utilisateur


def register(
    username: str,
    email: str,
    password: str,
    conn: sqlite3.Connection,
) -> Utilisateur | None:
    """Crée un compte utilisateur + cave associée de manière atomique.

    Returns:
        L'utilisateur créé ou None si le username/email existe déjà.
    """
    password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO utilisateurs (username, email, password_hash) "
                "VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            user_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO caves (utilisateur_id) VALUES (?)",
                (user_id,),
            )
    except sqlite3.IntegrityError:
        return None

    return Utilisateur(id=user_id, username=username, email=email, password_hash=password_hash)


def authenticate(
    username: str,
    password: str,
    conn: sqlite3.Connection,
) -> Utilisateur | None:
    """Vérifie les identifiants et retourne l'utilisateur si valide."""
    row = conn.execute(
        "SELECT id, username, email, password_hash FROM utilisateurs WHERE username = ?",
        (username,),
    ).fetchone()

    if row is None:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    return Utilisateur(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        password_hash=row["password_hash"],
    )


def get_user_by_id(user_id: int, conn: sqlite3.Connection) -> Utilisateur | None:
    """Retourne un utilisateur par son identifiant."""
    row = conn.execute(
        "SELECT id, username, email, password_hash FROM utilisateurs WHERE id = ?",
        (user_id,),
    ).fetchone()

    if row is None:
        return None

    return Utilisateur(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        password_hash=row["password_hash"],
    )
