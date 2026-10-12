"""Fixtures et configuration globale pour pytest."""

from datetime import date

import pytest

from macave.db import Database
from macave.models import (
    Bouteille,
    Cave,
    Etagere,
    Evaluation,
    Utilisateur,
    Vin,
)


@pytest.fixture
def utilisateur_alice() -> Utilisateur:
    """Un utilisateur de démo."""
    return Utilisateur(id=1, username="alice", email="alice@example.com")


@pytest.fixture
def cave_alice(utilisateur_alice) -> Cave:
    """Une cave vide pour Alice."""
    return Cave(id=1, utilisateur_id=1)


@pytest.fixture
def etagere_bordeaux() -> Etagere:
    """Une étagère de capacité 10."""
    return Etagere(id=1, nom="Bordeaux", capacite_max=10)


@pytest.fixture
def vin_chateau() -> Vin:
    """Une référence de vin de démo."""
    return Vin(
        id=1,
        domaine="Château Montelena",
        cuvee="Estate",
        type_vin="Rouge",
        millesime=2018,
        region="Napa Valley",
    )


@pytest.fixture
def bouteille_en_stock(vin_chateau) -> Bouteille:
    """Une bouteille en stock."""
    return Bouteille(
        id=1,
        vin_id=vin_chateau.id,
        prix_achat=45.0,
        date_ajout=date(2024, 1, 15),
    )


@pytest.fixture
def evaluation_16() -> Evaluation:
    """Une évaluation à 16/20."""
    return Evaluation(
        id=1,
        utilisateur_id=1,
        vin_id=1,
        note=16,
        commentaire="Excellente tenue",
        date_degustation=date(2024, 6, 10),
    )


@pytest.fixture
def db():
    """Base de données SQLite en mémoire, initialisée avec le schéma."""
    database = Database(":memory:")
    with database as conn:
        with open("schema.sql", encoding="utf-8") as f:
            conn.executescript(f.read())
        yield conn
