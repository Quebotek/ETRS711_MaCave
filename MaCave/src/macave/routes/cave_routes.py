"""Routes de gestion de cave et stock."""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from macave.models import Etagere
from macave.services import stock_service

bp = Blueprint("cave", __name__, url_prefix="/cave")


def _get_cave_id() -> int | None:
    """Retourne l'ID de la cave de l'utilisateur connecté."""
    if g.user is None:
        return None
    row = g.db.execute(
        "SELECT id FROM caves WHERE utilisateur_id = ?", (g.user.id,)
    ).fetchone()
    return row["id"] if row else None


@bp.route("/dashboard")
def dashboard():
    """Tableau de bord personnel."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    stats = stock_service.get_cave_stats(cave_id, g.db)
    etageres = stock_service.get_etageres_by_cave(cave_id, g.db)

    # Enrichir chaque étagère avec son occupation réelle depuis la DB
    for e in etageres:
        occ = g.db.execute(
            "SELECT COUNT(*) as cnt FROM bouteilles WHERE etagere_id = ? AND statut = 'en_stock'",
            (e.id,),
        ).fetchone()["cnt"]
        e._occupation = occ

    return render_template(
        "cave/dashboard.html", stats=stats, etageres=etageres
    )


@bp.route("/etageres")
def etageres():
    """Liste des étagères et gestion."""
    cave_id = _get_cave_id()
    if cave_id is None:
        return redirect(url_for("auth.login"))

    rows = g.db.execute(
        "SELECT e.id, e.nom, e.capacite_max, "
        "(SELECT COUNT(*) FROM bouteilles b "
        " WHERE b.etagere_id = e.id AND b.statut = 'en_stock') as occ "
        "FROM etageres e WHERE e.cave_id = ?",
        (cave_id,),
    ).fetchall()

    etageres = []
    for r in rows:
        etagere = Etagere(id=r["id"], nom=r["nom"], capacite_max=r["capacite_max"])
        # Injection temporaire de l'occupation pour le template
        etagere._occupation = r["occ"]
        etageres.append(etagere)

    return render_template("cave/etageres.html", etageres=etageres)


@bp.route("/etageres/ajouter", methods=("POST",))
def ajouter_etagere():
    """Ajout d'une étagère."""
    cave_id = _get_cave_id()
    if cave_id is None:
        return redirect(url_for("auth.login"))

    nom = request.form["nom"]
    capacite = int(request.form["capacite"])

    etagere = stock_service.create_etagere(cave_id, nom, capacite, g.db)
    if etagere is None:
        flash("Une étagère avec ce nom existe déjà.", "danger")
    else:
        flash(f"Étagère '{nom}' créée.", "success")

    return redirect(url_for("cave.etageres"))


@bp.route("/etageres/supprimer/<int:etagere_id>", methods=("POST",))
def supprimer_etagere(etagere_id):
    """Suppression d'une étagère vide."""
    if stock_service.delete_etagere(etagere_id, g.db):
        flash("Étagère supprimée.", "success")
    else:
        flash("Impossible de supprimer : l'étagère n'est pas vide.", "danger")
    return redirect(url_for("cave.etageres"))
