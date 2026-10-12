"""Routes du catalogue communautaire."""

from __future__ import annotations

from flask import Blueprint, g, render_template

bp = Blueprint("catalogue", __name__, url_prefix="/catalogue")


@bp.route("/vins")
def vins():
    """Liste des vins du catalogue."""
    rows = g.db.execute(
        "SELECT id, domaine, cuvee, type_vin, millesime, region FROM vins ORDER BY domaine"
    ).fetchall()
    return render_template("catalogue/vins.html", vins=rows)
