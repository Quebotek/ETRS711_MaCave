"""Application Factory pour Flask."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, g, session

from . import db as db_module


def create_app(config_name: str = "dev") -> Flask:
    """Crée et configure l'application Flask."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        DATABASE="macave.db",
    )

    # Configuration spécifique pourrait être chargée ici via from_pyfile

    # Garantir que le dossier instance existe
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Enregistrement des blueprints
    from .routes.auth_routes import bp as auth_bp
    from .routes.catalogue_routes import bp as catalogue_bp
    from .routes.cave_routes import bp as cave_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cave_bp)
    app.register_blueprint(catalogue_bp)

    # Gestion de la base de données par requête
    @app.before_request
    def _prepare_request() -> None:
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
        db = g.pop("db", None)
        if db is not None:
            if exception is None:
                db.commit()
            else:
                db.rollback()
            db.close()

    return app
