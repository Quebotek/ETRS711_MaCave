"""Modèle Étagère."""

from __future__ import annotations

from .bouteille import Bouteille


class Etagere:
    """Représente une étagère au sein d'une cave."""

    def __init__(
        self,
        id: int | None = None,
        nom: str = "",
        capacite_max: int = 0,
        bouteilles: list[Bouteille] | None = None,
    ) -> None:
        self.id = id
        self.nom = nom
        self.capacite_max = capacite_max
        self.bouteilles = bouteilles if bouteilles is not None else []

    def __repr__(self) -> str:
        return f"Etagere(id={self.id}, nom={self.nom!r}, capacite_max={self.capacite_max})"

    def get_occupation(self) -> int:
        """Nombre de bouteilles actuellement stockées."""
        return len(self.bouteilles)

    def get_places_disponibles(self) -> int:
        """Nombre de places libres restantes."""
        return self.capacite_max - self.get_occupation()

    def peut_accueillir(self, nb: int) -> bool:
        """Vérifie si l'étagère peut accueillir *nb* bouteilles supplémentaires.

        Règle R3 : l'occupation ne doit jamais dépasser la capacité maximale.
        """
        return self.get_occupation() + nb <= self.capacite_max

    def modifier_capacite(self, nouvelle_capacite: int) -> bool:
        """Modifie la capacité maximale si possible.

        Règle R4 : la capacité est incompressible sous l'occupation actuelle.

        Returns:
            True si la modification a été effectuée, False sinon.
        """
        if nouvelle_capacite < self.get_occupation():
            return False
        self.capacite_max = nouvelle_capacite
        return True

    def ajouter_bouteille(self, bouteille: Bouteille) -> bool:
        """Ajoute une bouteille si la capacité le permet.

        Returns:
            True si l'ajout est réussi, False sinon.
        """
        if not self.peut_accueillir(1):
            return False
        self.bouteilles.append(bouteille)
        bouteille.etagere_id = self.id
        return True

    def retirer_bouteille(self, bouteille: Bouteille) -> bool:
        """Retire une bouteille de l'étagère.

        Returns:
            True si le retrait est effectué, False si la bouteille
            n'était pas présente.
        """
        if bouteille in self.bouteilles:
            self.bouteilles.remove(bouteille)
            bouteille.etagere_id = None
            return True
        return False
