"""Routes du catalogue communautaire."""

from __future__ import annotations

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from macave.services import stock_service, vinofyi_service

bp = Blueprint("catalogue", __name__, url_prefix="/catalogue")


@bp.route("/vins")
def vins():
    """Liste des vins du catalogue avec notes moyennes."""
    rows = g.db.execute("""
        SELECT
            v.id,
            v.domaine,
            v.cuvee,
            v.type_vin,
            v.millesime,
            v.region,
            v.photo_url,
            AVG(e.note) as note_moyenne,
            COUNT(e.id) as nb_evaluations
        FROM vins v
        LEFT JOIN evaluations e ON v.id = e.vin_id
        GROUP BY v.id
        ORDER BY v.domaine, v.cuvee
    """).fetchall()

    # Formater les notes
    vins = []
    for row in rows:
        note = row["note_moyenne"]
        note_affichage = f"{note:.1f} / 20" if note else "Non évalué"
        vins.append({
            "id": row["id"],
            "domaine": row["domaine"],
            "cuvee": row["cuvee"],
            "type_vin": row["type_vin"],
            "millesime": row["millesime"],
            "region": row["region"],
            "photo_url": row["photo_url"],
            "note_moyenne": note_affichage,
            "nb_evaluations": row["nb_evaluations"]
        })

    return render_template("catalogue/vins.html", vins=vins)


@bp.route("/vins/ajouter", methods=("GET", "POST"))
def ajouter_vin():
    """Ajout d'une nouvelle référence de vin au catalogue."""
    if g.user is None:
        flash("Vous devez être connecté pour ajouter un vin.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        domaine = request.form["domaine"].strip()
        cuvee = request.form["cuvee"].strip()
        type_vin = request.form["type_vin"].strip()
        millesime = request.form["millesime"].strip()
        region = request.form["region"].strip()
        description = request.form.get("description", "").strip()
        photo_url = request.form.get("photo_url", "").strip()

        # Validation des champs obligatoires
        erreurs = []
        if not domaine:
            erreurs.append("Le domaine est obligatoire.")
        if not cuvee:
            erreurs.append("La cuvée est obligatoire.")
        if not type_vin:
            erreurs.append("Le type de vin est obligatoire.")
        if not millesime:
            erreurs.append("Le millésime est obligatoire.")
        else:
            try:
                millesime_int = int(millesime)
                if millesime_int < 1800 or millesime_int > 2100:
                    erreurs.append("Le millésime doit être compris entre 1800 et 2100.")
            except ValueError:
                erreurs.append("Le millésime doit être un nombre entier.")
        if not region:
            erreurs.append("La région est obligatoire.")

        if erreurs:
            for erreur in erreurs:
                flash(erreur, "danger")
            return render_template(
                "catalogue/ajouter_vin.html",
                domaine=domaine,
                cuvee=cuvee,
                type_vin=type_vin,
                millesime=millesime,
                region=region,
                description=description,
                photo_url=photo_url,
            )

        vin = stock_service.create_vin(
            domaine=domaine,
            cuvee=cuvee,
            type_vin=type_vin,
            millesime=int(millesime),
            region=region,
            description=description,
            photo_url=photo_url,
            conn=g.db,
        )

        if vin is None:
            flash(
                f"Un vin identique existe déjà dans le catalogue "
                f"({domaine} — {cuvee} — {millesime}).",
                "danger",
            )
            return render_template(
                "catalogue/ajouter_vin.html",
                domaine=domaine,
                cuvee=cuvee,
                type_vin=type_vin,
                millesime=millesime,
                region=region,
                description=description,
                photo_url=photo_url,
            )

        g.db.commit()
        flash(f"'{domaine} — {cuvee} ({millesime})' ajouté au catalogue.", "success")
        return redirect(url_for("catalogue.vins"))

    return render_template("catalogue/ajouter_vin.html")


@bp.route("/vins/recherche-vinofyi")
def recherche_vinofyi():
    """Recherche AJAX de vins dans VinoFYI."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"results": []})

    results = vinofyi_service.search_wines(query)
    return jsonify({"results": results})


@bp.route("/vins/detail-vinofyi/<slug>")
def detail_vinofyi(slug):
    """Récupère le détail d'un vin VinoFYI pour pré-remplissage."""
    wine_data = vinofyi_service.get_wine_detail(slug)
    if wine_data is None:
        return jsonify({"error": "Vin non trouvé"}), 404

    mapped = vinofyi_service.map_vinofyi_to_model(wine_data)
    return jsonify(mapped)
