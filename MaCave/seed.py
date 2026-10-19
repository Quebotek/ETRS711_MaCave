#!/usr/bin/env python3
"""Jeu de démonstration multi-comptes pour MaCave.

Le script crée automatiquement deux utilisateurs, leurs caves, étagères,
bouteilles et évaluations afin de vérifier le comportement multi-utilisateurs.

Vous pouvez le relancer : il détecte les données existantes et ne duplique pas.
"""

from __future__ import annotations

import sqlite3

from macave.db import get_db
from macave.services import auth_service, stock_service


def _get_user_id(conn: sqlite3.Connection, username: str) -> int | None:
    """Retourne l'ID d'un utilisateur s'il existe."""
    row = conn.execute("SELECT id FROM utilisateurs WHERE username = ?", (username,)).fetchone()
    return row["id"] if row else None


def _get_cave_id(conn: sqlite3.Connection, utilisateur_id: int) -> int | None:
    """Retourne l'ID de la cave d'un utilisateur."""
    row = conn.execute(
        "SELECT id FROM caves WHERE utilisateur_id = ?", (utilisateur_id,)
    ).fetchone()
    return row["id"] if row else None


def _get_vin_id(conn: sqlite3.Connection, domaine: str, millesime: int) -> int | None:
    """Retourne l'ID d'un vin s'il existe déjà (identifié par domaine + millésime)."""
    row = conn.execute(
        "SELECT id FROM vins WHERE domaine = ? AND millesime = ?",
        (domaine, millesime),
    ).fetchone()
    return row["id"] if row else None


def _get_etagere_id(conn: sqlite3.Connection, cave_id: int, nom: str) -> int | None:
    """Retourne l'ID d'une étagère si elle existe déjà dans la cave."""
    row = conn.execute(
        "SELECT id FROM etageres WHERE cave_id = ? AND nom = ?",
        (cave_id, nom),
    ).fetchone()
    return row["id"] if row else None


def main() -> None:
    db_path = "macave.db"
    conn = get_db(db_path)

    # ------------------------------------------------------------------
    # 1. Vin commun : Château Montelena 1973
    # ------------------------------------------------------------------
    vin_id = _get_vin_id(conn, "Château Montelena", 1973)
    if vin_id is None:
        cursor = conn.execute(
            "INSERT INTO vins (domaine, cuvee, type_vin, millesime, region, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "Château Montelena",
                "Estate Cabernet Sauvignon",
                "Rouge",
                1973,
                "Napa Valley",
                "Vin mythique ayant triomphé à la dégustation de Paris 1976.",
            ),
        )
        vin_id = cursor.lastrowid
        print(f"Vin créé : Château Montelena 1973 (id={vin_id})")
    else:
        print(f"Vin existant : Château Montelena 1973 (id={vin_id})")

    # ------------------------------------------------------------------
    # 1b. Vin avec image : Château Margaux 2015
    # ------------------------------------------------------------------
    vin2_id = _get_vin_id(conn, "Château Margaux", 2015)
    if vin2_id is None:
        cursor = conn.execute(
            (
                "INSERT INTO vins "
                "(domaine, cuvee, type_vin, millesime, region, description, photo_url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                "Château Margaux",
                "Grand Vin",
                "Rouge",
                2015,
                "Bordeaux",
                "Premier Grand Cru Classé de Margaux. "
                "Un vin d'une élégance et d'une complexité exceptionnelles.",
                "uploads/vins/demo_vin.jpg",
            ),
        )
        vin2_id = cursor.lastrowid
        print(f"Vin créé : Château Margaux 2015 avec image (id={vin2_id})")
    else:
        # Mettre à jour l'image si le vin existe déjà
        conn.execute(
            "UPDATE vins SET photo_url = ? WHERE id = ?",
            ("uploads/vins/demo_vin.jpg", vin2_id)
        )
        print(f"Vin existant : Château Margaux 2015 (id={vin2_id}) — image mise à jour")

    # ------------------------------------------------------------------
    # 2. Compte ALICE
    # ------------------------------------------------------------------
    alice_id = _get_user_id(conn, "alice")
    if alice_id is None:
        alice = auth_service.register("alice", "alice@example.com", "password123", conn)
        if alice is None:
            raise RuntimeError("Impossible de créer l'utilisateur alice")
        alice_id = alice.id
        print(f"Utilisateur créé : alice (id={alice_id})")
    else:
        print(f"Utilisateur existant : alice (id={alice_id})")

    cave_alice_id = _get_cave_id(conn, alice_id)
    if cave_alice_id is None:
        raise RuntimeError("Cave manquante pour alice")

    # Étagères Alice
    bordeaux_id = _get_etagere_id(conn, cave_alice_id, "Bordeaux")
    if bordeaux_id is None:
        etagere = stock_service.create_etagere(cave_alice_id, "Bordeaux", 10, conn)
        if etagere is None:
            raise RuntimeError("Impossible de créer l'étagère Bordeaux pour alice")
        bordeaux_id = etagere.id
        print(f"Étagère créée : Bordeaux (id={bordeaux_id}, cap=10)")
    else:
        print(f"Étagère existante : Bordeaux (id={bordeaux_id})")

    bourgogne_id = _get_etagere_id(conn, cave_alice_id, "Bourgogne")
    if bourgogne_id is None:
        etagere = stock_service.create_etagere(cave_alice_id, "Bourgogne", 6, conn)
        if etagere is None:
            raise RuntimeError("Impossible de créer l'étagère Bourgogne pour alice")
        bourgogne_id = etagere.id
        print(f"Étagère créée : Bourgogne (id={bourgogne_id}, cap=6)")
    else:
        print(f"Étagère existante : Bourgogne (id={bourgogne_id})")

    # Bouteilles Alice
    alice_stock = conn.execute(
        "SELECT COUNT(*) as cnt FROM bouteilles WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_alice_id,),
    ).fetchone()["cnt"]

    if alice_stock == 0:
        # 6 exemplaires du vin Montelena : 5 resteront en stock, 1 sera archivée
        lot_alice = stock_service.add_bouteilles_lot(
            cave_alice_id, vin_id, bordeaux_id, 45.0, 6, conn
        )
        if lot_alice is None:
            raise RuntimeError("Impossible d'ajouter les bouteilles d'alice")
        print(f"Ajout de {len(lot_alice)} bouteilles pour alice sur Bordeaux")

        # Ajouter 3 bouteilles du Margaux 2015
        lot_margaux = stock_service.add_bouteilles_lot(
            cave_alice_id, vin2_id, bourgogne_id, 385.0, 3, conn
        )
        if lot_margaux:
            print(f"Ajout de {len(lot_margaux)} bouteilles Margaux pour alice")

        # Archiver la première bouteille avec note 16
        bouteille_archive = lot_alice[0]
        eval_alice = stock_service.archiver_bouteille(
            bouteille_archive.id, alice_id, 16, "Excellente structure et tanins soyeux.", conn
        )
        if eval_alice is None:
            raise RuntimeError("Impossible d'archiver la bouteille d'alice")
        print(f"Bouteille archivée (note 16/20) — id={bouteille_archive.id}")
    else:
        print(f"Alice a déjà {alice_stock} bouteille(s) en stock — ignoré.")

    # ------------------------------------------------------------------
    # 3. Compte BOB
    # ------------------------------------------------------------------
    bob_id = _get_user_id(conn, "bob")
    if bob_id is None:
        bob = auth_service.register("bob", "bob@example.com", "password123", conn)
        if bob is None:
            raise RuntimeError("Impossible de créer l'utilisateur bob")
        bob_id = bob.id
        print(f"Utilisateur créé : bob (id={bob_id})")
    else:
        print(f"Utilisateur existant : bob (id={bob_id})")

    cave_bob_id = _get_cave_id(conn, bob_id)
    if cave_bob_id is None:
        raise RuntimeError("Cave manquante pour bob")

    # Étagère Bob
    cave_princ_id = _get_etagere_id(conn, cave_bob_id, "Cave Principale")
    if cave_princ_id is None:
        etagere = stock_service.create_etagere(cave_bob_id, "Cave Principale", 12, conn)
        if etagere is None:
            raise RuntimeError("Impossible de créer l'étagère Cave Principale pour bob")
        cave_princ_id = etagere.id
        print(f"Étagère créée : Cave Principale (id={cave_princ_id}, cap=12)")
    else:
        print(f"Étagère existante : Cave Principale (id={cave_princ_id})")

    # Bouteilles Bob
    bob_stock = conn.execute(
        "SELECT COUNT(*) as cnt FROM bouteilles WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_bob_id,),
    ).fetchone()["cnt"]

    if bob_stock == 0:
        # 3 exemplaires du vin Montelena : 2 resteront en stock, 1 sera archivée avec note 14
        lot_bob = stock_service.add_bouteilles_lot(
            cave_bob_id, vin_id, cave_princ_id, 45.0, 3, conn
        )
        if lot_bob is None:
            raise RuntimeError("Impossible d'ajouter les bouteilles de bob")
        print(f"Ajout de {len(lot_bob)} bouteilles pour bob sur Cave Principale")

        # Ajouter 1 bouteille du Margaux 2015
        lot_margaux_bob = stock_service.add_bouteilles_lot(
            cave_bob_id, vin2_id, cave_princ_id, 385.0, 1, conn
        )
        if lot_margaux_bob:
            print(f"Ajout de {len(lot_margaux_bob)} bouteille Margaux pour bob")

        # Archiver la première bouteille avec note 14
        bouteille_archive = lot_bob[0]
        eval_bob = stock_service.archiver_bouteille(
            bouteille_archive.id, bob_id, 14, "Bon vin, mais moins d'éclat que prévu.", conn
        )
        if eval_bob is None:
            raise RuntimeError("Impossible d'archiver la bouteille de bob")
        print(f"Bouteille archivée (note 14/20) — id={bouteille_archive.id}")
    else:
        print(f"Bob a déjà {bob_stock} bouteille(s) en stock — ignoré.")

    # ------------------------------------------------------------------
    # 4. Vérification finale : notes moyennes
    # ------------------------------------------------------------------
    moyenne1 = stock_service.get_vin_moyenne(vin_id, conn)
    if moyenne1 is not None:
        print(f"\nNote moyenne communautaire Château Montelena : {moyenne1:.1f} / 20")
    else:
        print("\nAucune évaluation pour Château Montelena.")

    moyenne2 = stock_service.get_vin_moyenne(vin2_id, conn)
    if moyenne2 is not None:
        print(f"Note moyenne communautaire Château Margaux : {moyenne2:.1f} / 20")
    else:
        print("Aucune évaluation pour Château Margaux.")

    conn.commit()
    conn.close()
    print("\nSeed terminé !")


if __name__ == "__main__":
    main()
