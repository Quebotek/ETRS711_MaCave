"""Énumérations partagées entre les modèles."""

from enum import Enum


class StatutBouteille(Enum):
    """Énumération des statuts possibles d'une bouteille."""

    EN_STOCK = "en_stock"
    ARCHIVEE = "archivee"
