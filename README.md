# 📍 RoadBook Pro

> **Professional roadbook editor for orienteering, raids, and navigation sports**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/username/roadbook-pro/releases)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Open%20Source-orange.svg)](#license)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

## 🚀 **Installation Ultra-Simple**

**Aucune configuration requise !** L'application installe automatiquement tout ce dont elle a besoin.

1. **📥 Télécharger** l' [archive](https://github.com/guiguoz/RoadBook-Creator/archive/refs/heads/main.zip)
2. **📂 Extraire** le dossier ZIP
3. **🖱️ Double-cliquer** sur `launch.bat`
4. **✨ L'application se lance** automatiquement !

> **Note** : Connexion internet requise lors de la première utilisation pour l'installation automatique de Python et des dépendances.

## ✨ **Fonctionnalités**

### 🎨 **Éditeur Graphique Avancé**
- **Outils de dessin** : Flèches (épaisse, moyenne, fine), traits, pointillés
- **Routes goudronnées** : Lignes parallèles avec flèches triangulaires
- **Balises** : Cercles colorés pour marquer les points de contrôle
- **Textes** : Annotations avec police et couleur personnalisables
- **Mode déplacement** : Repositionner tous les éléments
- **Mode effaceur** : Supprimer des éléments individuellement

### 🔄 **Édition Complète**
- **Ré-édition totale** : Modifier les schémas après validation
- **Ajouter/Supprimer/Déplacer** : Tous les éléments restent éditables
- **Undo/Redo** : Annuler et rétablir les actions
- **Sauvegarde vectorielle** : Aucune perte de qualité

### 📊 **Gestion des Vignettes**
- **Distances** : Intermédiaires et cumulées automatiques
- **Numérotation automatique** : Renumérotation après ajout/suppression
- **Observations** : Notes textuelles pour chaque vignette
- **Interface intuitive** : Tableau clair avec colonnes redimensionnables

### 💾 **Sauvegarde et Export**
- **Sauvegarde automatique** : Toutes les 5 minutes
- **Format .rbk** : Projets complets avec tous les éléments
- **Export PDF** : Mise en page professionnelle optimisée
- **Export JPEG** : Images haute qualité pour partage

### 🔧 **Fonctionnalités Techniques**
- **Installation automatique Python** : Aucune intervention utilisateur
- **Vérification des mises à jour** : Notification automatique
- **Logs détaillés** : Diagnostic et support facilités
- **Interface française** : Terminologie orienteering

## 🎯 **Utilisation**

### **Créer un Roadbook**
1. **Ajouter des vignettes** avec le bouton ➕
2. **Saisir les distances** dans la colonne correspondante
3. **Double-cliquer sur "Schéma"** pour ouvrir l'éditeur
4. **Dessiner** avec les outils disponibles
5. **Valider** pour sauvegarder le schéma

### **Éditer un Schéma Existant**
1. **Double-cliquer** sur le schéma à modifier
2. **Tous les éléments** sont automatiquement rechargés
3. **Ajouter, supprimer, déplacer** selon vos besoins
4. **Valider** les modifications

### **Exporter le Roadbook**
- **PDF** : Format professionnel pour impression
- **JPEG** : Image pour partage numérique

## 🏗️ **Architecture Technique**

```
roadbook_app/
├── src/
│   ├── main.py              # Interface principale
│   ├── vignette_editor.py   # Éditeur graphique
│   ├── vignette_model.py    # Modèle de données
│   ├── pdf_exporter.py     # Export PDF optimisé
│   ├── jpeg_exporter.py    # Export JPEG
│   ├── update_checker.py   # Vérification MAJ
│   ├── widgets.py          # Composants UI
│   └── logging_config.py   # Configuration logs
├── launch.bat              # Lanceur automatique
├── update.bat             # Script de mise à jour
└── version.json           # Informations version
```

## 🔄 **Mises à Jour**

L'application vérifie automatiquement les mises à jour au démarrage et vous notifie quand une nouvelle version est disponible.

**Mise à jour manuelle** :
1. Télécharger la nouvelle version
2. Extraire et remplacer les fichiers
3. Vos projets sont automatiquement préservés

## 📝 **Logs et Support**

Les logs sont stockés dans `logs/roadbook_YYYYMMDD.log` pour le diagnostic en cas de problème.

## ⚖️ **Licence**

- **Open Source** - Code source libre
- **Usage personnel et associatif** autorisé
- **Usage commercial** strictement interdit
- **Redistribution** libre avec mention de l'auteur

## 👨‍💻 **Développement**

**Projet mené par** : Guillaume Lemiègre  
**Développé par** : Intelligence Artificielle  
**Technologies** : Python 3.7+, PyQt5, ReportLab, SVG  
**Version** : 1.0.0 (Décembre 2024)

---

**⚠️ Avertissement** : Outil d'aide à la navigation uniquement. Vérifiez toujours vos itinéraires. L'auteur décline toute responsabilité en cas d'erreur de navigation.

**© 2024 Guillaume Lemiègre - Tous droits réservés**
