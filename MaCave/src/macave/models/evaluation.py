"""Modèle Évaluation."""

from __future__ import annotations

from datetime import date


class Evaluation:
    """Représente une évaluation (dégustation) d'un vin par un utilisateur."""

    def __init__(
        self,
        id: int | None = None,
        utilisateur_id: int = 0,
        vin_id: int = 0,
        bouteille_id: int | None = None,
        note: int = 0,
        commentaire: str = "",
        date_degustation: date = date.today(),
    ) -> None:
        """Initialise une évaluation.

        Args:
            id: Identifiant unique en base de données.
            utilisateur_id: ID de l'auteur de l'évaluation.
            vin_id: ID de la référence de vin évaluée.
            bouteille_id: ID de la bouteille archivée (dégustation).
            note: Note de 0 à 20 attribuée lors de la dégustation.
            commentaire: Commentaire de dégustation (accords, impressions).
            date_degustation: Date de la dégustation.
        """
        self.id = id
        self.utilisateur_id = utilisateur_id
        self.vin_id = vin_id
        self.bouteille_id = bouteille_id
        self.note = note
        self.commentaire = commentaire
        self.date_degustation = date_degustation

    def __repr__(self) -> str:
        """Retourne une représentation lisible de l'objet."""
        return (
            f"Evaluation(id={self.id}, note={self.note}, "
            f"vin_id={self.vin_id}, utilisateur_id={self.utilisateur_id})"
        )

    def modifier(self, nouvelle_note: int, nouveau_commentaire: str) -> None:
        """Met à jour la note et le commentaire de la dégustation.

        Args:
            nouvelle_note: Nouvelle note (0-20).
            nouveau_commentaire: Nouveau commentaire de dégustation.
        """
        self.note = nouvelle_note
        self.commentaire = nouveau_commentaire
