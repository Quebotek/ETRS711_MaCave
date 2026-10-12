"""Tests d'intégration des services métier avec une base SQLite en mémoire."""


import pytest

from macave.services import auth_service, stock_service


class TestAuthService:
    """Tests du service d'authentification."""

    def test_register_cree_utilisateur_et_cave(self, db):
        """L'inscription crée automatiquement un utilisateur et sa cave."""
        user = auth_service.register("alice", "alice@test.com", "pass123", db)
        assert user is not None
        assert user.id is not None
        assert user.username == "alice"

        # Cave créée automatiquement
        row = db.execute("SELECT id FROM caves WHERE utilisateur_id = ?", (user.id,)).fetchone()
        assert row is not None

    def test_register_username_unique(self, db):
        """On ne peut pas créer deux comptes avec le même username."""
        auth_service.register("bob", "bob1@test.com", "pass123", db)
        user2 = auth_service.register("bob", "bob2@test.com", "pass123", db)
        assert user2 is None

    def test_authenticate_success(self, db):
        """L'authentification réussit avec les bons identifiants."""
        auth_service.register("charlie", "charlie@test.com", "secret", db)
        user = auth_service.authenticate("charlie", "secret", db)
        assert user is not None
        assert user.username == "charlie"

    def test_authenticate_mauvais_mdp(self, db):
        """L'authentification échoue avec un mauvais mot de passe."""
        auth_service.register("dave", "dave@test.com", "secret", db)
        assert auth_service.authenticate("dave", "mauvais", db) is None

    def test_get_user_by_id(self, db):
        """Récupération d'un utilisateur par son ID."""
        created = auth_service.register("eve", "eve@test.com", "pass", db)
        fetched = auth_service.get_user_by_id(created.id, db)
        assert fetched is not None
        assert fetched.username == "eve"


class TestStockService:
    """Tests du service de gestion du stock."""

    @pytest.fixture(autouse=True)
    def setup_base(self, db):
        """Crée un utilisateur, une cave, un vin et une étagère avant chaque test."""
        self.db = db
        user = auth_service.register("tester", "test@test.com", "pass", db)
        self.user_id = user.id
        self.cave_id = db.execute(
            "SELECT id FROM caves WHERE utilisateur_id = ?", (user.id,)
        ).fetchone()["id"]

        db.execute(
            "INSERT INTO vins (domaine, cuvee, type_vin, millesime, region) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Château Test", "Cuvée Speciale", "Rouge", 2020, "Bordeaux"),
        )
        self.vin_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        etagere = stock_service.create_etagere(self.cave_id, "Principale", 10, db)
        self.etagere_id = etagere.id

    def test_create_etagere_nom_unique_par_cave(self):
        """R2 : les noms d'étagères sont uniques au sein d'une cave."""
        assert stock_service.create_etagere(self.cave_id, "Principale", 5, self.db) is None
        # Mais OK dans une autre cave
        user2 = auth_service.register("autre", "a@b.com", "pass", self.db)
        cave2_id = self.db.execute(
            "SELECT id FROM caves WHERE utilisateur_id = ?", (user2.id,)
        ).fetchone()["id"]
        e2 = stock_service.create_etagere(cave2_id, "Principale", 5, self.db)
        assert e2 is not None

    def test_r3_ajout_par_lot_tout_ou_rien(self):
        """R7 : ajout par lot atomicité (tout ou rien)."""
        # 12 bouteilles dans une étagère de 10 → refus total
        result = stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 12, self.db
        )
        assert result is None
        count = self.db.execute(
            "SELECT COUNT(*) as cnt FROM bouteilles WHERE cave_id = ?",
            (self.cave_id,),
        ).fetchone()["cnt"]
        assert count == 0

        # 5 bouteilles → OK
        result = stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 5, self.db
        )
        assert result is not None
        assert len(result) == 5

    def test_r7_deplacement_avec_capacite(self):
        """R7 : déplacement vérifie la capacité de l'étagère cible."""
        stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 8, self.db
        )
        petite = stock_service.create_etagere(self.cave_id, "Petite", 1, self.db)
        stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, petite.id, 30.0, 1, self.db
        )

        b_id = self.db.execute(
            "SELECT id FROM bouteilles WHERE cave_id = ? LIMIT 1",
            (self.cave_id,),
        ).fetchone()["id"]

        # déplacement impossible (pleine)
        assert stock_service.deplacer_bouteille(b_id, petite.id, self.db) is False

        # déplacement possible
        vide = stock_service.create_etagere(self.cave_id, "Vide", 10, self.db)
        assert stock_service.deplacer_bouteille(b_id, vide.id, self.db) is True

    def test_r8_archivage_et_evaluation(self):
        """R8 : archivage crée évaluation et mise à jour statut."""
        lot = stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 1, self.db
        )
        b_id = lot[0].id

        eval_obj = stock_service.archiver_bouteille(
            b_id, self.user_id, 17, "Très bon", self.db
        )
        assert eval_obj is not None
        assert eval_obj.note == 17
        assert eval_obj.bouteille_id == b_id

        # ré-archivage impossible
        assert stock_service.archiver_bouteille(
            b_id, self.user_id, 18, "Encore", self.db
        ) is None

    def test_r10_non_evalue(self):
        """R10 : vin non évalué retourne None."""
        assert stock_service.get_vin_moyenne(self.vin_id, self.db) is None

    def test_r9_note_moyenne_communautaire(self):
        """R9 : moyenne exacte sur plusieurs évaluations."""
        lot = stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 2, self.db
        )
        user2 = auth_service.register("autre", "autre@test.com", "pass", self.db)

        stock_service.archiver_bouteille(lot[0].id, self.user_id, 16, "A", self.db)
        stock_service.archiver_bouteille(lot[1].id, user2.id, 14, "B", self.db)

        moy = stock_service.get_vin_moyenne(self.vin_id, self.db)
        assert moy == 15.0

    def test_delete_etagere_non_vide(self):
        """R5 : une étagère non vide ne peut pas être supprimée."""
        stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 1, self.db
        )
        assert stock_service.delete_etagere(self.etagere_id, self.db) is False

    def test_cave_stats(self):
        """Statistiques du tableau de bord."""
        stock_service.add_bouteilles_lot(
            self.cave_id, self.vin_id, self.etagere_id, 25.0, 3, self.db
        )
        stats = stock_service.get_cave_stats(self.cave_id, self.db)
        assert stats["nb_bouteilles"] == 3
        assert stats["nb_references"] == 1
        assert stats["valeur_totale"] == 75.0
        assert stats["occupation_globale"] == (3 / 10 * 100)
