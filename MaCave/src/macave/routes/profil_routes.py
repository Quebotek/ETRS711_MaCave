"""Routes de gestion du profil utilisateur."""

from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from macave.db import IntegrityError

bp = Blueprint("profil", __name__, url_prefix="/profil")


@bp.route("/", methods=("GET", "POST"))
def voir_profil():
    """Affiche et permet de modifier le profil de l'utilisateur connecté."""
    if g.user is None:
        flash("Vous devez être connecté pour accéder à votre profil.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        nouveau_mdp = request.form.get("nouveau_mdp", "").strip()
        confirmation_mdp = request.form.get("confirmation_mdp", "").strip()

        erreurs = []

        # Validation username
        if not username:
            erreurs.append("Le nom d'utilisateur est obligatoire.")
        elif len(username) < 3:
            erreurs.append("Le nom d'utilisateur doit contenir au moins 3 caractères.")

        # Validation email
        if not email:
            erreurs.append("L'email est obligatoire.")
        elif "@" not in email or "." not in email:
            erreurs.append("L'email doit être une adresse valide.")

        # Validation mot de passe (si fourni)
        if nouveau_mdp:
            if len(nouveau_mdp) < 6:
                erreurs.append("Le mot de passe doit contenir au moins 6 caractères.")
            if nouveau_mdp != confirmation_mdp:
                erreurs.append("Les mots de passe ne correspondent pas.")

        if erreurs:
            for err in erreurs:
                flash(err, "danger")
            return render_template("auth/profil.html", user=g.user)

        # Mise à jour des informations
        try:
            # Vérifier l'unicité du username et email
            existing = g.db.execute(
                "SELECT id FROM utilisateurs WHERE (username = ? OR email = ?) AND id != ?",
                (username, email, g.user.id),
            ).fetchone()

            if existing:
                flash("Ce nom d'utilisateur ou cet email est déjà utilisé.", "danger")
                return render_template("auth/profil.html", user=g.user)

            # Mise à jour
            if nouveau_mdp:
                password_hash = generate_password_hash(nouveau_mdp, method="pbkdf2:sha256")
                g.db.execute(
                    "UPDATE utilisateurs SET username = ?, email = ?, "
                    "password_hash = ? WHERE id = ?",
                    (username, email, password_hash, g.user.id),
                )
                flash("Profil et mot de passe mis à jour avec succès !", "success")
            else:
                g.db.execute(
                    "UPDATE utilisateurs SET username = ?, email = ? WHERE id = ?",
                    (username, email, g.user.id),
                )
                flash("Profil mis à jour avec succès !", "success")

            g.db.commit()

            # Mettre à jour l'objet user en session
            g.user.username = username
            g.user.email = email

        except IntegrityError:
            flash("Erreur lors de la mise à jour. Veuillez réessayer.", "danger")
            return render_template("auth/profil.html", user=g.user)

        return redirect(url_for("cave.dashboard"))

    return render_template("auth/profil.html", user=g.user)
