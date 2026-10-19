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


@bp.route("/bouteilles/ajouter", methods=("GET", "POST"))
def ajouter_bouteilles():
    """Ajout d'un lot de bouteilles dans la cave."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    # Vins disponibles dans le catalogue
    vins = g.db.execute(
        "SELECT id, domaine, cuvee, type_vin, millesime, region "
        "FROM vins ORDER BY domaine, cuvee, millesime DESC"
    ).fetchall()

    # Étagères de la cave avec occupation
    etageres_rows = g.db.execute(
        "SELECT e.id, e.nom, e.capacite_max, "
        "(SELECT COUNT(*) FROM bouteilles b "
        " WHERE b.etagere_id = e.id AND b.statut = 'en_stock') as occ "
        "FROM etageres e WHERE e.cave_id = ?",
        (cave_id,),
    ).fetchall()

    etageres = []
    for r in etageres_rows:
        etageres.append({
            "id": r["id"],
            "nom": r["nom"],
            "capacite_max": r["capacite_max"],
            "places_libres": r["capacite_max"] - r["occ"],
        })

    if not etageres:
        flash("Vous devez d'abord créer une étagère pour stocker des bouteilles.", "warning")
        return redirect(url_for("cave.etageres"))

    if request.method == "POST":
        vin_id = request.form.get("vin_id", "").strip()
        etagere_id = request.form.get("etagere_id", "").strip()
        prix = request.form.get("prix", "").strip()
        quantite = request.form.get("quantite", "").strip()

        erreurs = []
        if not vin_id:
            erreurs.append("Veuillez sélectionner un vin.")
        if not etagere_id:
            erreurs.append("Veuillez sélectionner une étagère.")
        if not quantite:
            erreurs.append("La quantité est obligatoire.")
        else:
            try:
                q = int(quantite)
                if q < 1:
                    erreurs.append("La quantité doit être d'au moins 1.")
            except ValueError:
                erreurs.append("La quantité doit être un nombre entier.")
        if prix:
            try:
                float(prix)
            except ValueError:
                erreurs.append("Le prix doit être un nombre valide.")

        if erreurs:
            for e in erreurs:
                flash(e, "danger")
            return render_template(
                "cave/ajouter_bouteilles.html",
                vins=vins,
                etageres=etageres,
                vin_id=vin_id,
                etagere_id=etagere_id,
                prix=prix,
                quantite=quantite,
            )

        prix_val = float(prix) if prix else 0.0
        q = int(quantite)

        lot = stock_service.add_bouteilles_lot(
            cave_id=cave_id,
            vin_id=int(vin_id),
            etagere_id=int(etagere_id),
            prix_achat=prix_val,
            quantite=q,
            conn=g.db,
        )

        if lot is None:
            flash("Capacité de l'étagère insuffisante pour ce lot.", "danger")
            return render_template(
                "cave/ajouter_bouteilles.html",
                vins=vins,
                etageres=etageres,
                vin_id=vin_id,
                etagere_id=etagere_id,
                prix=prix,
                quantite=quantite,
            )

        g.db.commit()
        flash(f"{len(lot)} bouteille(s) ajoutée(s) avec succès !", "success")
        return redirect(url_for("cave.dashboard"))

    return render_template(
        "cave/ajouter_bouteilles.html",
        vins=vins,
        etageres=etageres,
    )


@bp.route("/etageres/supprimer/<int:etagere_id>", methods=("POST",))
def supprimer_etagere(etagere_id):
    """Suppression d'une étagère vide."""
    if stock_service.delete_etagere(etagere_id, g.db):
        flash("Étagère supprimée.", "success")
    else:
        flash("Impossible de supprimer : l'étagère n'est pas vide.", "danger")
    return redirect(url_for("cave.etageres"))
