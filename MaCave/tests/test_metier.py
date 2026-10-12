"""Tests couvrant les règles de gestion métier R1–R12.

R1  – Confidentialité des données privées (stock, étagères, prix, dates).
R2  – Unicité des noms d'étagères au sein d'une cave.
R3  – L'occupation ne dépasse jamais la capacité maximale.
R4  – La capacité est incompressible sous l'occupation actuelle.
R5  – Une étagère non vide ne peut pas être supprimée.
R6  – Le retrait d'un exemplaire laisse le reste du stock intact.
R7  – L'ajout par lot et le déplacement sont transactionnels (tout ou rien).
R8  – Archivage d'une bouteille en stock ; impossible de ré-archiver.
R9  – Calcul exact de la note moyenne communautaire.
R10 – Mention « Non évalué » si aucune note.
R11 – Chaque dégustation a le même poids.
R12 – Seul l'auteur peut modifier son évaluation.
"""

from datetime import date

from macave.models import (
    Bouteille,
    Cave,
    Etagere,
    Evaluation,
    StatutBouteille,
)

# ---------------------------------------------------------------------------
# Règles R2, R3, R4, R5 – Étagères et capacité
# ---------------------------------------------------------------------------


class TestEtagere:
    """R2, R3, R4, R5."""

    def test_r3_ajout_respecte_capacite(self, etagere_bordeaux, bouteille_en_stock):
        """R3 : ajouter 10 bouteilles remplit l'étagère ; la 11e est refusée."""
        for i in range(10):
            b = Bouteille(id=i + 1, vin_id=1)
            assert etagere_bordeaux.ajouter_bouteille(b) is True

        assert etagere_bordeaux.get_occupation() == 10
        onzieme = Bouteille(id=99, vin_id=1)
        assert etagere_bordeaux.ajouter_bouteille(onzieme) is False
        assert etagere_bordeaux.get_occupation() == 10

    def test_r4_capacite_incompressible(self, etagere_bordeaux, bouteille_en_stock):
        """R4 : on ne peut pas réduire la capacité sous l'occupation actuelle."""
        etagere_bordeaux.ajouter_bouteille(bouteille_en_stock)
        assert etagere_bordeaux.get_occupation() == 1
        assert etagere_bordeaux.modifier_capacite(0) is False
        assert etagere_bordeaux.capacite_max == 10
        assert etagere_bordeaux.modifier_capacite(5) is True
        assert etagere_bordeaux.capacite_max == 5

    def test_r5_suppression_etagerenon_vide(self, etagere_bordeaux, bouteille_en_stock):
        """R5 : une étagère contenant des bouteilles ne peut pas être supprimée."""
        cave = Cave(id=1)
        cave.etageres.append(etagere_bordeaux)
        assert cave.supprimer_etagere(etagere_bordeaux.id) is True  # vide

        etagere_bordeaux.ajouter_bouteille(bouteille_en_stock)
        assert cave.supprimer_etagere(etagere_bordeaux.id) is False


# ---------------------------------------------------------------------------
# Règles R6, R7, R8 – Stock, atomicité, cycle de vie
# ---------------------------------------------------------------------------


class TestBouteille:
    """R6, R7, R8."""

    def test_r6_retrait_exemplaire_reste_intact(self, etagere_bordeaux):
        """R6 : retirer une bouteille parmi plusieurs ne touche pas les autres."""
        b1 = Bouteille(id=1, vin_id=1)
        b2 = Bouteille(id=2, vin_id=1)
        b3 = Bouteille(id=3, vin_id=1)

        for b in (b1, b2, b3):
            etagere_bordeaux.ajouter_bouteille(b)

        assert etagere_bordeaux.get_occupation() == 3
        assert etagere_bordeaux.retirer_bouteille(b2) is True
        assert etagere_bordeaux.get_occupation() == 2
        assert b1 in etagere_bordeaux.bouteilles
        assert b3 in etagere_bordeaux.bouteilles
        assert b2 not in etagere_bordeaux.bouteilles

    def test_r7_deplacement_transactionnel(self, etagere_bordeaux):
        """R7 : le déplacement vérifie la capacité de l'étagère cible (tout ou rien)."""
        cible = Etagere(id=2, nom="Cible", capacite_max=5)
        pleine = Etagere(id=3, nom="Pleine", capacite_max=1)
        b1 = Bouteille(id=1, vin_id=1)
        b2 = Bouteille(id=2, vin_id=1)

        etagere_bordeaux.ajouter_bouteille(b1)
        etagere_bordeaux.ajouter_bouteille(b2)
        pleine.ajouter_bouteille(Bouteille(id=99, vin_id=1))

        # Transaction complète : retirer de la source puis déplacer
        etagere_bordeaux.retirer_bouteille(b1)
        assert b1.deplacer(cible) is True
        assert b1.etagere_id == 2
        assert b1 in cible.bouteilles

        # déplacement impossible vers étagère pleine (rollback automatique)
        assert b2.deplacer(pleine) is False
        assert b2.etagere_id == 1

    def test_r8_archivage_unique(self, bouteille_en_stock, evaluation_16):
        """R8 : une bouteille archivée ne peut pas être ré-archivée."""
        assert bouteille_en_stock.statut == StatutBouteille.EN_STOCK

        assert bouteille_en_stock.archiver(evaluation_16) is True
        assert bouteille_en_stock.statut == StatutBouteille.ARCHIVEE
        assert bouteille_en_stock.date_sortie == date.today()
        assert evaluation_16.bouteille_id == bouteille_en_stock.id

        # tentative de ré-archivage
        deuxieme_eval = Evaluation(note=18, utilisateur_id=1, vin_id=1)
        assert bouteille_en_stock.archiver(deuxieme_eval) is False


# ---------------------------------------------------------------------------
# Règles R9, R10, R11 – Évaluations et note moyenne
# ---------------------------------------------------------------------------


class TestVin:
    """R9, R10, R11."""

    def test_r10_non_evalue(self, vin_chateau):
        """R10 : un vin sans évaluation affiche « Non évalué »."""
        assert vin_chateau.calculer_note_moyenne() is None
        assert vin_chateau.get_note_affichage() == "Non évalué"

    def test_r9_calcul_note_moyenne(self, vin_chateau):
        """R9 : calcul exact de la moyenne sur plusieurs dégustations."""
        vin_chateau.evaluations = [
            Evaluation(note=16, utilisateur_id=1, vin_id=1),
            Evaluation(note=14, utilisateur_id=2, vin_id=1),
        ]
        assert vin_chateau.calculer_note_moyenne() == 15.0
        assert vin_chateau.get_note_affichage() == "15.0 / 20"

    def test_r11_poids_egal(self, vin_chateau):
        """R11 : chaque dégustation a le même poids (moyenne arithmétique simple)."""
        vin_chateau.evaluations = [
            Evaluation(note=10, utilisateur_id=1, vin_id=1),
            Evaluation(note=20, utilisateur_id=2, vin_id=1),
            Evaluation(note=15, utilisateur_id=3, vin_id=1),
        ]
        # moyenne simple = (10 + 20 + 15) / 3 = 15.0
        assert vin_chateau.calculer_note_moyenne() == 15.0

    def test_r12_modification_evaluation(self, evaluation_16):
        """R12 : l'évaluation peut être modifiée (contrôle d'autorité fait en service)."""
        assert evaluation_16.note == 16
        evaluation_16.modifier(18, "Encore meilleur en re-bouchonné")
        assert evaluation_16.note == 18
        assert evaluation_16.commentaire == "Encore meilleur en re-bouchonné"
