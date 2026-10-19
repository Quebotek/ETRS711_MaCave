# 🍷 MaCave - Nouvelles Fonctionnalités d'Interface Web

## Vue d'ensemble

Cette mise à jour apporte une **interface web enrichie** pour la gestion de l'inventaire et le système de notation, comme spécifié dans le README principal.

---

## 🎯 Fonctionnalités Ajoutées

### 1. **Page d'Inventaire Avancée** (`/inventaire/`)

Une vue complète de toutes vos bouteilles avec :

- **Cartes de vins enrichies** avec photos (si disponibles)
- **Affichage des notes moyennes** pour chaque vin
- **Filtres intelligents** :
  - Recherche par domaine ou cuvée
  - Filtre par type de vin (Rouge, Blanc, Rosé, etc.)
  - Filtre par région
- **Regroupement par vin** : toutes les bouteilles d'un même vin sont regroupées
- **Informations détaillées** :
  - Nombre de bouteilles par vin
  - Prix d'achat
  - Localisation (étagère)
  - Millésime et région

#### Actions rapides depuis l'inventaire :
- **Voir détails** : accède à la fiche complète du vin
- **Archiver** : archive une bouteille après dégustation avec notation

---

### 2. **Page de Détail d'un Vin** (`/inventaire/vin/<id>`)

Une fiche complète pour chaque vin avec :

#### 📋 Informations du vin
- Photo du vin (si disponible)
- Domaine et cuvée
- Millésime, région et type
- Description détaillée
- **Note communautaire en grand** (0-20)

#### 🍾 Gestion de vos bouteilles
- Tableau de toutes vos bouteilles (en stock et archivées)
- Statut clair (En stock / Archivée)
- Localisation sur les étagères
- Prix et date d'achat

#### Actions disponibles :
- **Déplacer** : change une bouteille d'étagère via modal
- **Archiver** : archive avec évaluation après dégustation

#### 💬 Système de notation communautaire
- **Toutes les évaluations** des utilisateurs
- Notes et commentaires de dégustation
- Dates et auteurs des évaluations
- **Votre évaluation personnelle** (si vous avez dégusté ce vin)
- Possibilité de **modifier votre évaluation**

---

### 3. **Catalogue Amélioré** (`/catalogue/vins`)

Le catalogue communautaire affiche maintenant :

- **Notes moyennes** pour chaque vin
- **Nombre d'évaluations** communautaires
- **Photos des vins** (quand disponibles)
- **Cartes interactives** avec survol animé
- Lien rapide vers les détails

---

### 4. **Système de Notation Complet**

#### 📊 Calcul des notes
- **Moyenne arithmétique** de toutes les évaluations (Règle R9)
- Affichage "Non évalué" si aucune évaluation (Règle R10)
- Notes de 0 à 20 avec précision décimale

#### ✍️ Enregistrement d'une évaluation
Lors de l'archivage d'une bouteille :
1. Cliquez sur "Archiver"
2. Saisissez votre note (0-20)
3. Ajoutez un commentaire de dégustation
4. Validez → la bouteille est archivée et l'évaluation enregistrée

#### 🔄 Modification d'évaluation
- Seul l'**auteur** peut modifier son évaluation (Règle R12)
- Accès via la page de détail du vin
- Modification de la note et/ou du commentaire

---

## 🎨 Interface Utilisateur

### Design amélioré
- **Navigation sticky** : la barre de navigation reste visible
- **Cartes interactives** : effets de survol sur les vins
- **Badges de notes** : code couleur pour les vins évalués
- **Modals** : fenêtres contextuelles pour les actions
- **Responsive** : s'adapte aux écrans mobiles

### Palette de couleurs
- **Rouge bordeaux** (#8B0000) : couleur principale
- **Vert succès** : actions réussies
- **Orange warning** : actions d'archivage
- **Gris neutre** : éléments non évalués

---

## 📁 Nouveaux Fichiers

### Routes
- `src/macave/routes/inventaire_routes.py` : Routes de l'inventaire et du système de notation

### Templates
- `src/macave/templates/inventaire/index.html` : Page principale de l'inventaire
- `src/macave/templates/inventaire/detail_vin.html` : Détail d'un vin

### Fichiers modifiés
- `src/macave/__init__.py` : Enregistrement du nouveau blueprint
- `src/macave/routes/catalogue_routes.py` : Ajout des notes moyennes
- `src/macave/templates/catalogue/vins.html` : Affichage en cartes avec notes
- `src/macave/templates/base.html` : Navigation améliorée + lien vers inventaire

---

## 🚀 Utilisation

### Accéder à l'inventaire
1. Connectez-vous avec votre compte
2. Cliquez sur "**Mon Inventaire**" dans la navigation
3. Utilisez les filtres pour trouver un vin spécifique

### Archiver une bouteille
1. Depuis l'inventaire, cliquez sur "Archiver" sur une bouteille
2. Saisissez votre note (0-20)
3. Ajoutez un commentaire de dégustation (optionnel)
4. Validez

### Consulter les notes
- **Inventaire** : note moyenne sur chaque carte de vin
- **Catalogue** : note moyenne et nombre d'évaluations
- **Détail du vin** : note communautaire en grand + toutes les évaluations

### Modifier son évaluation
1. Allez sur la page de détail d'un vin que vous avez évalué
2. Dans la section "Votre évaluation", cliquez sur "Modifier"
3. Mettez à jour la note et/ou le commentaire
4. Validez

---

## 🧪 Tests

Un script de test est inclus pour vérifier les nouvelles fonctionnalités :

```bash
cd MaCave
uv run python test_inventaire.py
```

Ce script vérifie :
- ✓ Chargement de la page d'inventaire
- ✓ Affichage des vins et des notes
- ✓ Page de détail des vins
- ✓ Section de notation
- ✓ Catalogue avec notes

---

## 📋 Règles Métier Respectées

Les nouvelles fonctionnalités respectent les règles du README :

- **R1** : Confidentialité - seules vos bouteilles sont visibles dans votre inventaire
- **R4** : Archivage avec évaluation et libération de l'étagère
- **R8** : Impossible de ré-archiver une bouteille déjà archivée
- **R9** : Moyenne arithmétique exacte des notes
- **R10** : Affichage "Non évalué" si aucune évaluation
- **R11** : Toutes les évaluations ont le même poids
- **R12** : Seul l'auteur peut modifier son évaluation

---

## 💡 Perspectives d'Évolution

Comme mentionné dans le README :
- Export CSV/PDF de l'inventaire personnel
- Filtres avancés par accords mets-vins
- Statistiques personnelles de dégustation
- Comparaison de vos notes avec la moyenne communautaire
