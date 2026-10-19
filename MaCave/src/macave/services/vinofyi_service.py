"""Service d'intégration avec l'API VinoFYI.

Fournit des fonctions pour rechercher et récupérer des informations
sur les vins depuis l'encyclopédie VinoFYI (vinofyi.com).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://vinofyi.com/api/v1"
TIMEOUT_SECONDS = 5


def _fetch_json(url: str) -> dict[str, Any] | None:
    """Effectue une requête GET et retourne le JSON parsé.

    Returns:
        Dict des données JSON ou None en cas d'erreur.
    """
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MaCave-App/1.0 (Wine Catalog Integration)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            data = response.read()
            return json.loads(data.decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def search_wines(query: str) -> list[dict[str, Any]]:
    """Recherche des vins dans VinoFYI par nom.

    Args:
        query: Chaîne de recherche (ex: "Château Margaux").

    Returns:
        Liste de résultats avec name, slug, type, url.
    """
    if not query or len(query.strip()) < 2:
        return []

    encoded_query = urllib.parse.quote(query.strip())
    url = f"{BASE_URL}/search/?q={encoded_query}"
    data = _fetch_json(url)

    if data is None:
        return []

    results = data.get("results", [])
    # Ne garder que les vins (pas les régions, cépages, etc.)
    return [r for r in results if r.get("type") == "wine"]


def get_wine_detail(slug: str) -> dict[str, Any] | None:
    """Récupère le détail complet d'un vin par son slug.

    Args:
        slug: Identifiant unique du vin (ex: "chateau-margaux-2015").

    Returns:
        Dict avec winery_name, wine_type, region_name, country_name, etc.
    """
    url = f"{BASE_URL}/wines/{slug}/"
    return _fetch_json(url)


def get_styles() -> list[dict[str, Any]]:
    """Liste les 19 styles de vin VinoFYI avec descriptions pédagogiques.

    Returns:
        Liste de styles avec name, slug, wine_type, description, serving_temp, etc.
    """
    url = f"{BASE_URL}/styles/"
    data = _fetch_json(url)
    if data is None:
        return []
    return data.get("results", [])


def get_style_detail(slug: str) -> dict[str, Any] | None:
    """Récupère le détail d'un style de vin.

    Args:
        slug: Identifiant du style (ex: "bold-red").

    Returns:
        Dict avec description, food_pairing, serving_temp, etc.
    """
    url = f"{BASE_URL}/styles/{slug}/"
    return _fetch_json(url)


def search_grapes(query: str) -> list[dict[str, Any]]:
    """Recherche des cépages dans VinoFYI.

    Args:
        query: Nom du cépage (ex: "Cabernet").

    Returns:
        Liste de cépages avec name, slug, color, description.
    """
    if not query or len(query.strip()) < 2:
        return []

    encoded_query = urllib.parse.quote(query.strip())
    url = f"{BASE_URL}/search/?q={encoded_query}"
    data = _fetch_json(url)

    if data is None:
        return []

    results = data.get("results", [])
    return [r for r in results if r.get("type") == "grape"]


def get_grape_detail(slug: str) -> dict[str, Any] | None:
    """Récupère le détail d'un cépage.

    Args:
        slug: Identifiant du cépage (ex: "cabernet-sauvignon").

    Returns:
        Dict avec name, color, origin_country, description, etc.
    """
    url = f"{BASE_URL}/grapes/{slug}/"
    return _fetch_json(url)


def map_vinofyi_to_model(wine_data: dict[str, Any]) -> dict[str, Any]:
    """Convertit les données VinoFYI en champs compatibles avec le modèle Vin.

    Args:
        wine_data: Données brutes de l'API VinoFYI.

    Returns:
        Dict avec les champs : domaine, cuvee, type_vin, region, description.
    """
    # Mapping des types de vin VinoFYI → MaCave
    type_mapping = {
        "Red": "Rouge",
        "White": "Blanc",
        "Rose": "Rosé",
        "Sparkling": "Effervescent",
        "Dessert": "Doux",
        "Fortified": "Fortifié",
    }

    winery = wine_data.get("winery_name", "")
    name = wine_data.get("name", "")
    region = wine_data.get("region_name", "")
    country = wine_data.get("country_name", "")
    wine_type = type_mapping.get(wine_data.get("wine_type", ""), wine_data.get("wine_type", ""))
    description = wine_data.get("description", "") or wine_data.get("meta_description", "")

    # Essayer d'extraire la cuvée du nom
    cuvee = ""
    if winery and name.startswith(winery):
        cuvee = name[len(winery):].strip()
    elif name:
        cuvee = name

    return {
        "domaine": winery,
        "cuvee": cuvee,
        "type_vin": wine_type,
        "region": f"{region}, {country}" if country and region != country else region,
        "description": description,
        "note_moyenne": wine_data.get("avg_rating", ""),
        "nombre_notes": wine_data.get("rating_count", 0),
    }


def get_style_accords(style_slug: str) -> dict[str, Any]:
    """Récupère les accords mets-vins et recommandations d'un style.

    Args:
        style_slug: Identifiant du style.

    Returns:
        Dict avec description, température, verre, accords suggérés.
    """
    style = get_style_detail(style_slug)
    if not style:
        return {}

    return {
        "nom": style.get("name", ""),
        "description": style.get("description", ""),
        "temperature": f"{style.get('serving_temp_min', '')}-{style.get('serving_temp_max', '')}°C",
        "verre": style.get("glass_type", ""),
        "aging": style.get("aging_potential", ""),
    }
