"""Modèle Vin."""

from __future__ import annotations

from .evaluation import Evaluation


class Vin:
    """Représente une référence de vin dans le catalogue communautaire."""

    def __init__(
        self,
        id: int | None = None,
        domaine: str = "",
        cuvee: str = "",
        type_vin: str = "",
        millesime: int = 0,
        region: str = "",
        description: str = "",
        photo_url: str = "",
        evaluations: list[Evaluation] | None = None,
    ) -> None:
        """Initialise une référence de vin.

        Args:
            id: Identifiant unique en base de données.
            domaine: Nom du domaine viticole (ex: "Château Margaux").
            cuvee: Nom de la cuvée (ex: "Grand Vin").
            type_vin: Type (Rouge, Blanc, Rosé, Effervescent).
            millesime: Année de récolte du raisin.
            region: Région de production (ex: "Bordeaux, France").
            description: Présentation générale du vin.
            photo_url: URL ou chemin de l'image de l'étiquette.
            evaluations: Liste des évaluations communautaires.
        """
        self.id = id
        self.domaine = domaine
        self.cuvee = cuvee
        self.type_vin = type_vin
        self.millesime = millesime
        self.region = region
        self.description = description
        self.photo_url = photo_url
        self.evaluations = evaluations if evaluations is not None else []

    def __repr__(self) -> str:
        """Retourne une représentation lisible de l'objet."""
        return (
            f"Vin(id={self.id}, domaine={self.domaine!r}, "
            f"cuvee={self.cuvee!r}, millesime={self.millesime})"
        )

    def calculer_note_moyenne(self) -> float | None:
        """Calcule la note moyenne communautaire.

        Returns:
            Moyenne arithmétique des notes ou None si aucune évaluation.
        """
        if not self.evaluations:
            return None
        total = sum(e.note for e in self.evaluations)
        return total / len(self.evaluations)

    def get_note_affichage(self) -> str:
        """Retourne la note formatée pour l'affichage.

        Returns:
            Chaîne type "15.0 / 20" ou "Non évalué".
        """
        moyenne = self.calculer_note_moyenne()
        if moyenne is None:
            return "Non évalué"
        return f"{moyenne:.1f} / 20"
