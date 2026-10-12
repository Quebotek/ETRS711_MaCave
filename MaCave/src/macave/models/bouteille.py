"""Modèle Bouteille."""

from __future__ import annotations

from datetime import date

from .enums import StatutBouteille
from .evaluation import Evaluation


class Bouteille:
    """Représente un exemplaire physique d'une bouteille dans le stock."""

    def __init__(
        self,
        id: int | None = None,
        vin_id: int = 0,
        etagere_id: int | None = None,
        prix_achat: float = 0.0,
        date_ajout: date = date.today(),
        date_sortie: date | None = None,
        statut: StatutBouteille = StatutBouteille.EN_STOCK,
    ) -> None:
        self.id = id
        self.vin_id = vin_id
        self.etagere_id = etagere_id
        self.prix_achat = prix_achat
        self.date_ajout = date_ajout
        self.date_sortie = date_sortie
        self.statut = statut

    def __repr__(self) -> str:
        return (
            f"Bouteille(id={self.id}, vin_id={self.vin_id}, "
            f"etagere_id={self.etagere_id}, statut={self.statut})"
        )

    def deplacer(self, nouvelle_etagere) -> bool:
        """Déplace la bouteille vers une autre étagère sous contrainte de capacité.

        Le déplacement est atomique : si l'étagère cible n'a pas la place,
        la bouteille reste sur son étagère actuelle.

        Args:
            nouvelle_etagere: Instance d'Etagere cible.

        Returns:
            True si le déplacement est effectué, False sinon.
        """
        from .etagere import Etagere

        if self.statut != StatutBouteille.EN_STOCK:
            return False
        if not isinstance(nouvelle_etagere, Etagere):
            return False
        if not nouvelle_etagere.peut_accueillir(1):
            return False

        self.etagere_id = nouvelle_etagere.id
        nouvelle_etagere.ajouter_bouteille(self)
        return True

    def archiver(self, evaluation: Evaluation) -> bool:
        """Archive la bouteille après dégustation.

        Règle R8 : une bouteille déjà archivée ne peut pas être ré-archivée.
        Libère implicitement son emplacement via le StockService.

        Args:
            evaluation: L'évaluation liée à la dégustation.

        Returns:
            True si l'archivage est effectué, False si déjà archivée.
        """
        if self.statut == StatutBouteille.ARCHIVEE:
            return False
        self.statut = StatutBouteille.ARCHIVEE
        self.date_sortie = date.today()
        evaluation.bouteille_id = self.id
        return True
