"""Point d'entrée exécutable de l'application Flask."""

from macave import create_app

app = create_app()


@app.route("/")
def index():
    """Redirige vers le tableau de bord si connecté, sinon vers la connexion."""
    from flask import g, redirect, url_for

    if g.user is not None:
        return redirect(url_for("cave.dashboard"))
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    app.run(debug=True)
