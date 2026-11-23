"""Point d'entrée exécutable de l'application Flask."""

import os

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
    # Mode debug contrôlé par variable d'environnement
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    # Hôte et port configurables (utile pour Docker)
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(debug=debug_mode, host=host, port=port)
