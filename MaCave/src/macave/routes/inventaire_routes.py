"""Routes de l'inventaire et du système de notation."""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from macave.services import stock_service

bp = Blueprint("inventaire", __name__, url_prefix="/inventaire")


def _get_cave_id() -> int | None:
    """Retourne l'ID de la cave de l'utilisateur connecté."""
    if g.user is None:
        return None
    row = g.db.execute(
        "SELECT id FROM caves WHERE utilisateur_id = ?", (g.user.id,)
    ).fetchone()
    return row["id"] if row else None


@bp.route("/")
def index():
    """Page principale de l'inventaire avec toutes les bouteilles en stock."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    # Récupérer toutes les bouteilles en stock avec les détails du vin
    rows = g.db.execute("""
        SELECT
            b.id as bouteille_id,
            b.prix_achat,
            b.date_ajout,
            e.nom as etagere_nom,
            v.id as vin_id,
            v.domaine,
            v.cuvee,
            v.type_vin,
            v.millesime,
            v.region,
            v.photo_url,
            (SELECT AVG(note) FROM evaluations WHERE vin_id = v.id) as note_moyenne,
            (SELECT COUNT(*) FROM evaluations WHERE vin_id = v.id) as nb_evaluations
        FROM bouteilles b
        JOIN vins v ON b.vin_id = v.id
        LEFT JOIN etageres e ON b.etagere_id = e.id
        WHERE b.cave_id = ? AND b.statut = 'en_stock'
        ORDER BY v.domaine, v.cuvee, b.date_ajout DESC
    """, (cave_id,)).fetchall()

    # Regrouper les bouteilles par vin
    vins_dict = {}
    for row in rows:
        vin_key = row["vin_id"]
        if vin_key not in vins_dict:
            note_moy = row["note_moyenne"]
            vins_dict[vin_key] = {
                "id": row["vin_id"],
                "domaine": row["domaine"],
                "cuvee": row["cuvee"],
                "type_vin": row["type_vin"],
                "millesime": row["millesime"],
                "region": row["region"],
                "photo_url": row["photo_url"],
                "note_moyenne": f"{note_moy:.1f}" if note_moy else "Non évalué",
                "nb_evaluations": row["nb_evaluations"],
                "bouteilles": []
            }
        vins_dict[vin_key]["bouteilles"].append({
            "id": row["bouteille_id"],
            "prix_achat": row["prix_achat"],
            "date_ajout": row["date_ajout"],
            "etagere_nom": row["etagere_nom"] or "Aucune étagère"
        })

    # Filtres
    type_filter = request.args.get("type", "")
    region_filter = request.args.get("region", "")
    search = request.args.get("search", "")

    filtered_vins = []
    for vin in vins_dict.values():
        if type_filter and vin["type_vin"] != type_filter:
            continue
        if region_filter and vin["region"] != region_filter:
            continue
        if search:
            search_lower = search.lower()
            if (search_lower not in vin["domaine"].lower() and
                search_lower not in vin["cuvee"].lower()):
                continue
        filtered_vins.append(vin)

    # Récupérer les types et régions pour les filtres
    types = g.db.execute(
        "SELECT DISTINCT type_vin FROM vins ORDER BY type_vin"
    ).fetchall()
    regions = g.db.execute(
        "SELECT DISTINCT region FROM vins ORDER BY region"
    ).fetchall()

    # Récupérer les étagères de la cave pour le modal de déplacement
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
            "_occupation": r["occ"],
        })

    return render_template(
        "inventaire/index.html",
        vins=filtered_vins,
        etageres=etageres,
        types=[t["type_vin"] for t in types],
        regions=[r["region"] for r in regions],
        current_type=type_filter,
        current_region=region_filter,
        current_search=search
    )


@bp.route("/vin/<int:vin_id>")
def detail_vin(vin_id):
    """Page de détail d'un vin avec toutes ses bouteilles et évaluations."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    # Infos du vin
    vin = g.db.execute("""
        SELECT id, domaine, cuvee, type_vin, millesime, region, description, photo_url
        FROM vins WHERE id = ?
    """, (vin_id,)).fetchone()

    if vin is None:
        flash("Vin non trouvé.", "danger")
        return redirect(url_for("inventaire.index"))

    # Bouteilles de cet utilisateur pour ce vin
    bouteilles = g.db.execute("""
        SELECT b.id, b.prix_achat, b.date_ajout, e.nom as etagere_nom, b.statut
        FROM bouteilles b
        LEFT JOIN etageres e ON b.etagere_id = e.id
        WHERE b.cave_id = ? AND b.vin_id = ?
        ORDER BY b.statut, b.date_ajout DESC
    """, (cave_id, vin_id)).fetchall()

    # Toutes les évaluations de ce vin (communautaires)
    evaluations = g.db.execute("""
        SELECT e.note, e.commentaire, e.date_degustation, u.username
        FROM evaluations e
        JOIN utilisateurs u ON e.utilisateur_id = u.id
        WHERE e.vin_id = ?
        ORDER BY e.date_degustation DESC
    """, (vin_id,)).fetchall()

    # Note moyenne
    note_moy = stock_service.get_vin_moyenne(vin_id, g.db)
    note_affichage = f"{note_moy:.1f} / 20" if note_moy else "Non évalué"

    # Mes évaluations pour ce vin
    my_eval = g.db.execute("""
        SELECT e.id, e.note, e.commentaire
        FROM evaluations e
        JOIN bouteilles b ON e.bouteille_id = b.id
        WHERE e.utilisateur_id = ? AND b.cave_id = ? AND e.vin_id = ?
    """, (g.user.id, cave_id, vin_id)).fetchone()

    # Récupérer les étagères pour le modal de déplacement
    etageres_rows = g.db.execute("""
        SELECT e.id, e.nom, e.capacite_max,
               (SELECT COUNT(*) FROM bouteilles b
                WHERE b.etagere_id = e.id AND b.statut = 'en_stock') as occ
        FROM etageres e WHERE e.cave_id = ?
    """, (cave_id,)).fetchall()

    etageres = []
    for r in etageres_rows:
        etageres.append({
            "id": r["id"],
            "nom": r["nom"],
            "capacite_max": r["capacite_max"],
            "_occupation": r["occ"]
        })

    # ─── Recherche VinoFYI pour enrichir la fiche ───
    vinofyi_info = None
    try:
        from macave.services import vinofyi_service
        # Chercher le vin par nom
        query = f"{vin['domaine']} {vin['cuvee']}"
        results = vinofyi_service.search_wines(query)
        if results:
            # Prendre le premier résultat
            wine_detail = vinofyi_service.get_wine_detail(results[0]['slug'])
            if wine_detail:
                vinofyi_info = {
                    "note_vinofyi": wine_detail.get("avg_rating"),
                    "nb_avis": wine_detail.get("rating_count"),
                    "corps": wine_detail.get("body"),
                    "acidite": wine_detail.get("acidity"),
                    "elaboration": wine_detail.get("elaborate"),
                    "alcool": wine_detail.get("abv"),
                }
    except Exception:
        pass  # Ignorer silencieusement si VinoFYI est indisponible

    return render_template(
        "inventaire/detail_vin.html",
        vin=vin,
        bouteilles=list(bouteilles),
        evaluations=list(evaluations),
        note_moyenne=note_affichage,
        ma_evaluation=my_eval,
        etageres=etageres,
        vinofyi_info=vinofyi_info,
    )


@bp.route("/bouteille/<int:bouteille_id>/archiver", methods=["POST"])
def archiver_bouteille(bouteille_id):
    """Archiver une bouteille avec évaluation."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    note = int(request.form.get("note", 0))
    commentaire = request.form.get("commentaire", "")

    if not (0 <= note <= 20):
        flash("La note doit être comprise entre 0 et 20.", "danger")
        return redirect(url_for("inventaire.index"))

    result = stock_service.archiver_bouteille(
        bouteille_id, g.user.id, note, commentaire, g.db
    )

    if result:
        flash("Bouteille archivée avec évaluation enregistrée !", "success")
    else:
        flash("Impossible d'archiver cette bouteille.", "danger")

    return redirect(url_for("inventaire.index"))


@bp.route("/bouteille/<int:bouteille_id>/deplacer", methods=["POST"])
def deplacer_bouteille(bouteille_id):
    """Déplacer une bouteille vers une autre étagère."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    nouvelle_etagere_id = int(request.form.get("etagere_id", 0))

    # Vérifier que l'étagère appartient à la cave
    etagere = g.db.execute(
        "SELECT id FROM etageres WHERE id = ? AND cave_id = ?",
        (nouvelle_etagere_id, cave_id)
    ).fetchone()

    if not etagere:
        flash("Étagère invalide.", "danger")
        return redirect(url_for("inventaire.index"))

    if stock_service.deplacer_bouteille(bouteille_id, nouvelle_etagere_id, g.db):
        flash("Bouteille déplacée avec succès.", "success")
    else:
        flash("Impossible de déplacer la bouteille (capacité insuffisante ?).", "danger")

    return redirect(url_for("inventaire.index"))


@bp.route("/evaluation/<int:evaluation_id>/modifier", methods=["POST"])
def modifier_evaluation(evaluation_id):
    """Modifier sa propre évaluation."""
    cave_id = _get_cave_id()
    if cave_id is None:
        flash("Aucune cave trouvée.", "warning")
        return redirect(url_for("auth.login"))

    note = int(request.form.get("note", 0))
    commentaire = request.form.get("commentaire", "")

    if not (0 <= note <= 20):
        flash("La note doit être comprise entre 0 et 20.", "danger")
        return redirect(url_for("inventaire.index"))

    # Vérifier que l'évaluation appartient à l'utilisateur
    eval_row = g.db.execute("""
        SELECT e.id FROM evaluations e
        JOIN bouteilles b ON e.bouteille_id = b.id
        WHERE e.id = ? AND e.utilisateur_id = ? AND b.cave_id = ?
    """, (evaluation_id, g.user.id, cave_id)).fetchone()

    if not eval_row:
        flash("Évaluation non trouvée ou non autorisée.", "danger")
        return redirect(url_for("inventaire.index"))

    g.db.execute(
        "UPDATE evaluations SET note = ?, commentaire = ? WHERE id = ?",
        (note, commentaire, evaluation_id)
    )

    flash("Évaluation mise à jour avec succès !", "success")
    return redirect(url_for("inventaire.index"))
