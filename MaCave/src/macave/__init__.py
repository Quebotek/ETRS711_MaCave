"""Application Factory pour Flask."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, g, session

from . import db as db_module


def create_app(config_name: str = "dev") -> Flask:
    """Crée et configure l'application Flask.

    Args:
        config_name: Nom de la configuration (dev, test, prod).

    Returns:
        Instance de l'application Flask configurée.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", "macave.db"),
    )

    # Configuration spécifique pourrait être chargée ici via from_pyfile

    # Garantir que le dossier instance existe
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Enregistrement des blueprints
    from .routes.auth_routes import bp as auth_bp
    from .routes.catalogue_routes import bp as catalogue_bp
    from .routes.cave_routes import bp as cave_bp
    from .routes.inventaire_routes import bp as inventaire_bp
    from .routes.profil_routes import bp as profil_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cave_bp)
    app.register_blueprint(catalogue_bp)
    app.register_blueprint(inventaire_bp)
    app.register_blueprint(profil_bp)

    # Gestion de la base de données par requête
    @app.before_request
    def _prepare_request() -> None:
        """Prépare l'objet g avant chaque requête.

        Initialise la connexion DB et charge l'utilisateur en session.
        """
        if "db" not in g:
            g.db = db_module.Database(app.config["DATABASE"]).__enter__()

        from macave.services import auth_service

        user_id = session.get("user_id")
        if user_id is None:
            g.user = None
        else:
            g.user = auth_service.get_user_by_id(user_id, g.db)

    @app.teardown_appcontext
    def _close_db(exception: BaseException | None = None) -> None:
        """Ferme la connexion DB après chaque requête.

        Args:
            exception: Exception levée pendant la requête (None si succès).
        """
        db = g.pop("db", None)
        if db is not None:
            if exception is None:
                db.commit()
            else:
                db.rollback()
            db.close()

    return app
