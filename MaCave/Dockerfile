# syntax=docker/dockerfile:1

##############
# Étape de build / dépendances
##############
FROM python:3.12-slim AS builder

# Installation d'uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copie des fichiers de dépendances en premier (cache Docker optimal)
COPY pyproject.toml uv.lock README.md ./

# Synchronisation des dépendances + package en mode editable
COPY --chown=macave:macave src/ ./src/
RUN uv sync --frozen --no-dev

##############
# Image finale
##############
FROM python:3.12-slim

WORKDIR /app

# Création d'un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 macave && mkdir -p /data && chown macave:macave /data

# Copie du virtualenv depuis l'étape builder
COPY --from=builder /app/.venv /app/.venv

# Rendre les binaires du venv accessibles sans préciser le chemin complet
ENV PATH="/app/.venv/bin:$PATH"

# Copie du code source
COPY --chown=macave:macave src/ ./src/
COPY --chown=macave:macave schema.sql schema_mariadb.sql ./
COPY --chown=macave:macave init_db.py seed.py ./

# Variables d'environnement
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Droits
USER macave

# Exposition du port
EXPOSE 5000

# Script d'entrée : init DB + seed, puis lancement Gunicorn
CMD ["sh", "-c", "python init_db.py && python seed.py; exec gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 macave.app:app"]
