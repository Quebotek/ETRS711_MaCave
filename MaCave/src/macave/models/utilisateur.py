"""Modèle Utilisateur."""

from __future__ import annotations


class Utilisateur:
    """Représente un compte utilisateur de l'application."""

    def __init__(
        self,
        id: int | None = None,
        username: str = "",
        email: str = "",
        password_hash: str = "",
    ) -> None:
        """Initialise un utilisateur.

        Args:
            id: Identifiant unique en base de données.
            username: Nom d'affichage de l'utilisateur.
            email: Adresse électronique pour la récupération de compte.
            password_hash: Empreinte cryptée du mot de passe (PBKDF2-SHA256).
        """
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def __repr__(self) -> str:
        """Retourne une représentation lisible de l'objet."""
        return f"Utilisateur(id={self.id}, username={self.username!r}, email={self.email!r})"

    def verifier_mot_de_passe(self, mdp: str) -> bool:
        """Vérifie un mot de passe en clair contre le hash stocké.

        Args:
            mdp: Mot de passe en clair à vérifier.

        Returns:
            True si le mot de passe correspond au hash, False sinon.
        """
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, mdp)
