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

# ─── Traductions VinoFYI → Français ──────────────────────────────

STYLE_NAMES_FR = {
    "Aromatic White": "Blanc Aromatique",
    "Bold Red": "Rouge Corsé",
    "Botrytized": "Botrytisé",
    "Charmat Method Sparkling": "Effervescent Méthode Charmat",
    "Crisp White": "Blanc Vif et Minéral",
    "Dry Rosé": "Rosé Sec",
    "Elegant Red": "Rouge Élégant",
    "Ice Wine": "Vin de Glace",
    "Late Harvest": "Vendange Tardive",
    "Light Red": "Rouge Léger",
    "Light White": "Blanc Léger",
    "Madeira Style": "Style Madère",
    "Medium Red": "Rouge Mi-Corsé",
    "Pétillant Naturel": "Pétillant Naturel",
    "Port Style": "Style Porto",
    "Rich White": "Blanc Riche et Onctueux",
    "Sherry Style": "Style Xérès",
    "Sweet Rosé": "Rosé Doux",
    "Traditional Method Sparkling": "Effervescent Méthode Traditionnelle",
}

GLASS_TYPES_FR = {
    "universal": "Universel",
    "bordeaux": "Bordeaux",
    "burgundy": "Bourgogne",
    "flute": "Flûte",
    "dessert": "Dessert",
    "copita": "Copita",
}

AGING_POTENTIAL_FR = {
    "drink_now": "À boire maintenant",
    "3_5_years": "3 à 5 ans",
    "5_10_years": "5 à 10 ans",
    "10_plus_years": "10+ ans",
}

WINE_TYPE_FR = {
    "Red": "Rouge",
    "White": "Blanc",
    "Rose": "Rosé",
    "Sparkling": "Effervescent",
    "Dessert": "Doux",
    "Fortified": "Fortifié",
}

BODY_RANGE_FR = {
    "light": "Léger",
    "medium": "Mi-corsé",
    "full": "Corsé",
}

CEPAGE_COLOR_FR = {
    "red": "rouge",
    "white": "blanc",
    "rose": "rosé",
}


def _translate_style(style: dict[str, Any]) -> dict[str, Any]:
    """Traduit un style VinoFYI en français (sauf la description)."""
    translated = dict(style)
    translated["name"] = STYLE_NAMES_FR.get(
        style.get("name", ""), style.get("name", "")
    )
    translated["wine_type"] = WINE_TYPE_FR.get(
        style.get("wine_type", ""), style.get("wine_type", "")
    )
    translated["glass_type"] = GLASS_TYPES_FR.get(
        style.get("glass_type", ""), style.get("glass_type", "")
    )
    translated["aging_potential"] = AGING_POTENTIAL_FR.get(
        style.get("aging_potential", ""), style.get("aging_potential", "")
    )
    translated["body_range"] = BODY_RANGE_FR.get(
        style.get("body_range", ""), style.get("body_range", "")
    )
    return translated


def _translate_grape(grape: dict[str, Any]) -> dict[str, Any]:
    """Traduit un cépage VinoFYI en français."""
    translated = dict(grape)
    color = grape.get("color", "")
    translated["color_fr"] = CEPAGE_COLOR_FR.get(color, color) if color else ""
    return translated


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
    """Liste les 19 styles de vin VinoFYI traduits en français.

    Returns:
        Liste de styles avec name, slug, wine_type, description, serving_temp, etc.
        Les noms, types, verres et catégories sont traduits. Les descriptions restent en anglais.
    """
    url = f"{BASE_URL}/styles/"
    data = _fetch_json(url)
    if data is None:
        return []

    results = data.get("results", [])
    return [_translate_style(style) for style in results]


def get_style_detail(slug: str) -> dict[str, Any] | None:
    """Récupère le détail d'un style de vin traduit en français.

    Args:
        slug: Identifiant du style (ex: "bold-red").

    Returns:
        Dict avec description (en), température, verre (traduit), etc.
    """
    url = f"{BASE_URL}/styles/{slug}/"
    data = _fetch_json(url)
    if not data:
        return None
    return _translate_style(data)


def search_grapes(query: str) -> list[dict[str, Any]]:
    """Recherche des cépages dans VinoFYI.

    Args:
        query: Nom du cépage (ex: "Cabernet").

    Returns:
        Liste de cépages avec name, slug, color, color_fr, description.
    """
    if not query or len(query.strip()) < 2:
        return []

    encoded_query = urllib.parse.quote(query.strip())
    url = f"{BASE_URL}/search/?q={encoded_query}"
    data = _fetch_json(url)

    if data is None:
        return []

    results = data.get("results", [])
    grapes = [r for r in results if r.get("type") == "grape"]
    return [_translate_grape(g) for g in grapes]


def get_grape_detail(slug: str) -> dict[str, Any] | None:
    """Récupère le détail d'un cépage.

    Args:
        slug: Identifiant du cépage (ex: "cabernet-sauvignon").

    Returns:
        Dict avec name, color, color_fr, origin_country, description, etc.
    """
    url = f"{BASE_URL}/grapes/{slug}/"
    data = _fetch_json(url)
    if not data:
        return None
    return _translate_grape(data)


def convertir_note_sur_20(note_sur_5: str | float | None) -> float | None:
    """Convertit une note VinoFYI (/5) en note MaCave (/20).

    Args:
        note_sur_5: Note sur 5 (ex: "4.43" ou 4.43).

    Returns:
        Note sur 20 arrondie à 1 décimale, ou None si invalide.
    """
    if note_sur_5 is None or note_sur_5 == "":
        return None
    try:
        n = float(note_sur_5)
        if n < 0 or n > 5:
            return None
        return round(n * 4, 1)
    except (ValueError, TypeError):
        return None


def map_vinofyi_to_model(wine_data: dict[str, Any]) -> dict[str, Any]:
    """Convertit les données VinoFYI en champs compatibles avec le modèle Vin.

    Args:
        wine_data: Données brutes de l'API VinoFYI.

    Returns:
        Dict avec les champs : domaine, cuvee, type_vin, region, description.
    """
    winery = wine_data.get("winery_name", "")
    name = wine_data.get("name", "")
    region = wine_data.get("region_name", "")
    country = wine_data.get("country_name", "")
    wine_type = WINE_TYPE_FR.get(
        wine_data.get("wine_type", ""),
        wine_data.get("wine_type", ""),
    )
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
        "note_moyenne": convertir_note_sur_20(wine_data.get("avg_rating")),
        "note_vinofyi_brute": wine_data.get("avg_rating", ""),
        "nombre_notes": wine_data.get("rating_count", 0),
    }


def get_style_accords(style_slug: str) -> dict[str, Any]:
    """Récupère les accords mets-vins et recommandations d'un style.

    Args:
        style_slug: Identifiant du style.

    Returns:
        Dict avec nom (traduit), description (en), température, verre (traduit).
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
        "corps": style.get("body_range", ""),
    }
