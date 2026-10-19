#  MaCave - Documentation Technique

Documentation technique détaillée du projet MaCave.

>  **Pour la documentation générale et l'installation**, consultez le [README principal](../README.md) à la racine du dépôt.

---

## 🆕 Nouvelles Fonctionnalités (Interface Web)

Cette mise à jour ajoute une interface web enrichie pour l'inventaire et le système de notation.

### Fichiers ajoutés

#### Routes
- `src/macave/routes/inventaire_routes.py` - Routes de gestion de l'inventaire
  - `GET /inventaire/` - Page principale de l'inventaire avec filtres
  - `GET /inventaire/vin/<id>` - Détail d'un vin avec évaluations
  - `POST /inventaire/bouteille/<id>/archiver` - Archiver avec évaluation
  - `POST /inventaire/bouteille/<id>/deplacer` - Déplacer une bouteille
  - `POST /inventaire/evaluation/<id>/modifier` - Modifier son évaluation

#### Templates
- `src/macave/templates/inventaire/index.html` - Interface de l'inventaire
  - Cartes de vins avec photos
  - Filtres (recherche, type, région)
  - Modal d'archivage avec notation
- `src/macave/templates/inventaire/detail_vin.html` - Fiche détaillée d'un vin
  - Note communautaire en évidence
  - Liste des bouteilles avec actions
  - Toutes les évaluations communautaires
  - Modification de sa propre évaluation

### Modifications apportées

#### Backend
- `src/macave/__init__.py` - Enregistrement du blueprint `inventaire`
- `src/macave/routes/catalogue_routes.py` - Ajout des notes moyennes dans la requête SQL

#### Frontend
- `src/macave/templates/catalogue/vins.html` - Affichage en cartes avec notes
- `src/macave/templates/base.html` - Navigation améliorée + lien vers inventaire

---

## Architecture Technique

### Modèle de Données

Les nouvelles fonctionnalités s'appuient sur les tables existantes :

```sql
-- Table VINS (catalogue partagé)
vins (
    id, domaine, cuvee, type_vin, millesime, region, 
    description, photo_url
)

-- Table BOUTEILLES (stock privé)
bouteilles (
    id, vin_id, cave_id, etagere_id, prix_achat,
    date_ajout, date_sortie, statut
)

-- Table EVALUATIONS (communautaire)
evaluations (
    id, utilisateur_id, vin_id, bouteille_id,
    note, commentaire, date_degustation
)
```

### Calcul des Notes Moyennes

```python
# Requête SQL optimisée avec JOIN et AVG
SELECT 
    v.id,
    AVG(e.note) as note_moyenne,
    COUNT(e.id) as nb_evaluations
FROM vins v
LEFT JOIN evaluations e ON v.id = e.vin_id
GROUP BY v.id
```

### Règles Métier Implémentées

| Règle | Description | Implémentation |
|-------|-------------|----------------|
| R9 | Moyenne arithmétique exacte | `AVG(note)` SQL |
| R10 | Affichage "Non évalué" si aucune note | Condition `if note_moyenne is None` |
| R11 | Toutes les évaluations ont le même poids | Moyenne simple sans pondération |
| R12 | Seul l'auteur peut modifier | Vérification `utilisateur_id` avant modification |

---

## Tests

### Script de Test des Nouvelles Fonctionnalités

```bash
cd MaCave
uv run python test_inventaire.py
```

Ce script vérifie :
-  Chargement de la page d'inventaire
-  Affichage des vins et des notes
-  Page de détail des vins
-  Section de notation
-  Catalogue avec notes

### Tests Existant

Les tests existants continuent de fonctionner :

```bash
uv run pytest -v
uv run pytest -v --cov=macave
```

---

## Guide de Développement

### Ajouter un Nouveau Filtre

Pour ajouter un filtre dans l'inventaire :

1. **Template** (`inventaire/index.html`) :
```html
<div>
  <label for="nouveau_filtre">Nom du filtre</label>
  <select id="nouveau_filtre" name="nouveau_filtre">
    <option value="">Tous</option>
    {% for valeur in valeurs %}
    <option value="{{ valeur }}">{{ valeur }}</option>
    {% endfor %}
  </select>
</div>
```

2. **Route** (`inventaire_routes.py`) :
```python
nouveau_filtre = request.args.get("nouveau_filtre", "")
# Ajouter la logique de filtrage
if nouveau_filtre and vin["champ"] != nouveau_filtre:
    continue
```

3. **Passer les données au template** :
```python
return render_template(
    "inventaire/index.html",
    vins=filtered_vins,
    valeurs=liste_des_valeurs,
    current_nouveau_filtre=nouveau_filtre
)
```

### Personnaliser le Design

Les styles CSS sont inclus directement dans les templates. Pour une personnalisation globale :

1. Modifier `src/macave/templates/base.html` pour les styles globaux
2. Modifier les sections `<style>` dans chaque template pour les styles spécifiques

Variables CSS disponibles :
```css
:root {
  --primary: #8B0000;      /* Rouge bordeaux */
  --bg: #f8f5f0;           /* Fond clair */
  --card: #fff;            /* Fond des cartes */
  --text: #333;            /* Texte principal */
  --border: #ddd;          /* Bordures */
  --success: #2e7d32;      /* Vert succès */
  --danger: #c62828;       /* Rouge erreur */
  --warning: #f9a825;      /* Orange warning */
  --info: #1565c0;         /* Bleu info */
}
```

---

## Dépannage

### Les notes ne s'affichent pas
- Vérifier que des évaluations existent dans la table `evaluations`
- Exécuter `uv run python seed.py` pour peupler la base

### Erreur "Aucune cave trouvée"
- L'utilisateur doit avoir une cave associée
- Se connecter avec un compte valide

### Photos non affichées
- Les URLs des photos doivent être accessibles
- Le fallback CSS s'active automatiquement en cas d'erreur

---

## Références

- [README principal](../README.md) - Installation et vue d'ensemble
- [NOUVELLES_FONCTIONNALITES.md](NOUVELLES_FONCTIONNALITES.md) - Guide utilisateur détaillé
- [Schema SQL](schema.sql) - Modèle de données complet
