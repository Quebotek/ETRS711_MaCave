"""Modèle Cave."""

from __future__ import annotations

from .etagere import Etagere


class Cave:
    """Représente la cave privée d'un utilisateur."""

    def __init__(
        self,
        id: int | None = None,
        utilisateur_id: int | None = None,
        etageres: list[Etagere] | None = None,
    ) -> None:
        self.id = id
        self.utilisateur_id = utilisateur_id
        self.etageres = etageres if etageres is not None else []

    def __repr__(self) -> str:
        return f"Cave(id={self.id}, utilisateur_id={self.utilisateur_id})"

    def calculer_valeur_totale(self) -> float:
        """Calcule la valeur totale du stock en évitant la division par zéro."""
        total = 0.0
        for etagere in self.etageres:
            for bouteille in etagere.bouteilles:
                if bouteille.statut.value == "en_stock":
                    total += bouteille.prix_achat
        return total

    def calculer_occupation_globale(self) -> float | None:
        """Calcule le taux d'occupation global de la cave.

        Returns:
            Pourcentage d'occupation ou None si aucune étagère
            (pour éviter la division par zéro).
        """
        capacite_totale = sum(e.capacite_max for e in self.etageres)
        if capacite_totale == 0:
            return None
        occupation_totale = sum(e.get_occupation() for e in self.etageres)
        return (occupation_totale / capacite_totale) * 100

    def get_etagere_par_nom(self, nom: str) -> Etagere | None:
        """Retourne une étagère par son nom (unicité garantie au sein d'une cave).

        Règle R2 : les noms d'étagères sont uniques au sein d'une cave.
        """
        for etagere in self.etageres:
            if etagere.nom == nom:
                return etagere
        return None

    def supprimer_etagere(self, etagere_id: int) -> bool:
        """Supprime une étagère si elle est vide.

        Règle R5 : une étagère contenant des bouteilles ne peut pas être supprimée.

        Returns:
            True si la suppression est effectuée, False sinon.
        """
        etagere = next((e for e in self.etageres if e.id == etagere_id), None)
        if etagere is None:
            return False
        if etagere.get_occupation() > 0:
            return False
        self.etageres.remove(etagere)
        return True
