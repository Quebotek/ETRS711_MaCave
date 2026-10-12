"""Services de gestion du stock (cave, étagères, bouteilles, évaluations)."""

from __future__ import annotations

import sqlite3

from macave.models import Bouteille, Etagere, Evaluation


def create_etagere(
    cave_id: int,
    nom: str,
    capacite_max: int,
    conn: sqlite3.Connection,
) -> Etagere | None:
    """Crée une étagère dans une cave.

    Returns:
        L'étagère créée ou None si le nom existe déjà dans cette cave.
    """
    try:
        cursor = conn.execute(
            "INSERT INTO etageres (cave_id, nom, capacite_max) VALUES (?, ?, ?)",
            (cave_id, nom, capacite_max),
        )
    except sqlite3.IntegrityError:
        return None

    return Etagere(id=cursor.lastrowid, nom=nom, capacite_max=capacite_max)


def get_etageres_by_cave(cave_id: int, conn: sqlite3.Connection) -> list[Etagere]:
    """Liste toutes les étagères d'une cave."""
    rows = conn.execute(
        "SELECT id, nom, capacite_max FROM etageres WHERE cave_id = ?",
        (cave_id,),
    ).fetchall()
    return [Etagere(id=r["id"], nom=r["nom"], capacite_max=r["capacite_max"]) for r in rows]


def delete_etagere(etagere_id: int, conn: sqlite3.Connection) -> bool:
    """Supprime une étagère si elle est vide.

    Règle R5 : échec silencieux si l'étagère contient encore des bouteilles
    (la contrainte FK `ON DELETE RESTRICT` sur `bouteilles.etagere_id`
    empêche la suppression si des bouteilles y sont référencées).
    """
    try:
        cursor = conn.execute("DELETE FROM etageres WHERE id = ?", (etagere_id,))
    except sqlite3.IntegrityError:
        return False
    return cursor.rowcount > 0


def get_etagere_occupation(etagere_id: int, conn: sqlite3.Connection) -> int:
    """Retourne le nombre de bouteilles actuellement stockées sur une étagère."""
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM bouteilles WHERE etagere_id = ? AND statut = 'en_stock'",
        (etagere_id,),
    ).fetchone()
    return row["cnt"] if row else 0


def add_bouteilles_lot(
    cave_id: int,
    vin_id: int,
    etagere_id: int,
    prix_achat: float,
    quantite: int,
    conn: sqlite3.Connection,
) -> list[Bouteille] | None:
    """Ajoute un lot d'exemplaires de manière atomique.

    Règle R7 : tout ou rien — si l'étagère n'a pas assez de place,
    aucune bouteille n'est insérée.

    Returns:
        Liste des bouteilles créées ou None si la capacité est insuffisante.
    """
    occ = get_etagere_occupation(etagere_id, conn)
    cap = conn.execute(
        "SELECT capacite_max FROM etageres WHERE id = ?", (etagere_id,)
    ).fetchone()["capacite_max"]

    if occ + quantite > cap:
        return None

    bouteilles = []
    for _ in range(quantite):
        cursor = conn.execute(
            "INSERT INTO bouteilles (vin_id, cave_id, etagere_id, prix_achat) "
            "VALUES (?, ?, ?, ?)",
            (vin_id, cave_id, etagere_id, prix_achat),
        )
        bouteilles.append(
            Bouteille(
                id=cursor.lastrowid,
                vin_id=vin_id,
                cave_id=cave_id,
                etagere_id=etagere_id,
                prix_achat=prix_achat,
            )
        )
    return bouteilles


def deplacer_bouteille(
    bouteille_id: int,
    nouvelle_etagere_id: int,
    conn: sqlite3.Connection,
) -> bool:
    """Déplace une bouteille vers une autre étagère de manière atomique.

    Règle R7 : la capacité de l'étagère cible est vérifiée.
    """
    b = conn.execute(
        "SELECT statut, cave_id FROM bouteilles WHERE id = ?", (bouteille_id,)
    ).fetchone()
    if b is None or b["statut"] != "en_stock":
        return False

    occ = get_etagere_occupation(nouvelle_etagere_id, conn)
    cap = conn.execute(
        "SELECT capacite_max FROM etageres WHERE id = ?", (nouvelle_etagere_id,)
    ).fetchone()
    if cap is None or occ + 1 > cap["capacite_max"]:
        return False

    conn.execute(
        "UPDATE bouteilles SET etagere_id = ? WHERE id = ?",
        (nouvelle_etagere_id, bouteille_id),
    )
    return True


def archiver_bouteille(
    bouteille_id: int,
    utilisateur_id: int,
    note: int,
    commentaire: str,
    conn: sqlite3.Connection,
) -> Evaluation | None:
    """Archive une bouteille en stock et crée l'évaluation associée.

    Règle R8 : impossible d'archiver une bouteille déjà archivée.
    Transaction atomique (UPDATE + INSERT).

    Returns:
        L'évaluation créée ou None si la bouteille est introuvable ou déjà archivée.
    """
    if not (0 <= note <= 20):
        return None

    b = conn.execute(
        "SELECT vin_id, statut FROM bouteilles WHERE id = ?", (bouteille_id,)
    ).fetchone()
    if b is None or b["statut"] == "archivee":
        return None

    conn.execute(
        "UPDATE bouteilles SET statut = 'archivee', date_sortie = DATE('now') "
        "WHERE id = ?",
        (bouteille_id,),
    )
    cur = conn.execute(
        "INSERT INTO evaluations (utilisateur_id, vin_id, bouteille_id, note, commentaire) "
        "VALUES (?, ?, ?, ?, ?)",
        (utilisateur_id, b["vin_id"], bouteille_id, note, commentaire),
    )
    return Evaluation(
        id=cur.lastrowid,
        utilisateur_id=utilisateur_id,
        vin_id=b["vin_id"],
        bouteille_id=bouteille_id,
        note=note,
        commentaire=commentaire,
    )


def get_cave_stats(cave_id: int, conn: sqlite3.Connection) -> dict:
    """Retourne les statistiques du tableau de bord d'une cave."""
    nb_bouteilles = conn.execute(
        "SELECT COUNT(*) as cnt FROM bouteilles WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_id,),
    ).fetchone()["cnt"]

    nb_references = conn.execute(
        "SELECT COUNT(DISTINCT vin_id) as cnt FROM bouteilles "
        "WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_id,),
    ).fetchone()["cnt"]

    valeur_totale = conn.execute(
        "SELECT COALESCE(SUM(prix_achat), 0) as total FROM bouteilles "
        "WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_id,),
    ).fetchone()["total"]

    cap = conn.execute(
        "SELECT COALESCE(SUM(capacite_max), 0) as total FROM etageres WHERE cave_id = ?",
        (cave_id,),
    ).fetchone()["total"]

    occ = conn.execute(
        "SELECT COUNT(*) as cnt FROM bouteilles "
        "WHERE cave_id = ? AND statut = 'en_stock'",
        (cave_id,),
    ).fetchone()["cnt"]

    occupation_globale = (occ / cap * 100) if cap > 0 else None

    return {
        "nb_bouteilles": nb_bouteilles,
        "nb_references": nb_references,
        "valeur_totale": valeur_totale,
        "occupation_globale": occupation_globale,
    }


def get_vin_moyenne(vin_id: int, conn: sqlite3.Connection) -> float | None:
    """Calcule la note moyenne communautaire d'un vin.

    Règle R9 : moyenne arithmétique exacte.
    Règle R10 : retourne None si aucune évaluation.
    """
    row = conn.execute(
        "SELECT AVG(note) as moy, COUNT(*) as cnt FROM evaluations WHERE vin_id = ?",
        (vin_id,),
    ).fetchone()
    if row["cnt"] == 0:
        return None
    return row["moy"]
