"""Routes d'authentification."""

from __future__ import annotations

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from macave.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Page d'inscription."""
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Le nom d'utilisateur est obligatoire."
        elif not password:
            error = "Le mot de passe est obligatoire."
        elif not email:
            error = "L'email est obligatoire."

        if error is None:
            user = auth_service.register(username, email, password, g.db)
            if user is None:
                error = f"L'utilisateur '{username}' ou l'email '{email}' existe déjà."
            else:
                flash("Inscription réussie. Vous pouvez vous connecter.", "success")
                return redirect(url_for("auth.login"))

        flash(error, "danger")

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Page de connexion."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        user = auth_service.authenticate(username, password, g.db)
        if user is None:
            error = "Identifiants invalides."

        if error is None:
            session.clear()
            session["user_id"] = user.id
            flash(f"Bienvenue, {user.username} !", "success")
            return redirect(url_for("cave.dashboard"))

        flash(error, "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Déconnexion."""
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("auth.login"))


@bp.before_app_request
def load_logged_in_user():
    """Charge l'utilisateur connecté dans `g.user` à chaque requête."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = auth_service.get_user_by_id(user_id, g.db)
