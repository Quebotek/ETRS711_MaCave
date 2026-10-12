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
        self.id = id
        self.utilisateur_id = utilisateur_id
        self.vin_id = vin_id
        self.bouteille_id = bouteille_id
        self.note = note
        self.commentaire = commentaire
        self.date_degustation = date_degustation

    def __repr__(self) -> str:
        return (
            f"Evaluation(id={self.id}, note={self.note}, "
            f"vin_id={self.vin_id}, utilisateur_id={self.utilisateur_id})"
        )

    def modifier(self, nouvelle_note: int, nouveau_commentaire: str) -> None:
        """Met à jour la note et le commentaire de la dégustation."""
        self.note = nouvelle_note
        self.commentaire = nouveau_commentaire
