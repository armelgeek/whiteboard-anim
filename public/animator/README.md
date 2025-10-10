# Whiteboard-It

Application de création d'animations de type "dessin sur tableau blanc" (whiteboard animation) à partir d'images.

## Fonctionnalités

- ✅ Génération de vidéos d'animation de dessin à partir d'images
- ✅ Personnalisation des paramètres (FPS, vitesse, grille)
- ✅ Export JSON des données d'animation
- ✅ Support de plusieurs formats d'image
- ✅ Animation avec main réaliste
- ✨ **NOUVEAU** : Système de couches (layers) avec slides multiples
- ✨ **NOUVEAU** : Animations d'entrée/sortie personnalisées
- ✨ **NOUVEAU** : Contrôles de caméra (zoom et focus)
- ✨ **NOUVEAU** : Transitions entre slides
- ✨ **NOUVEAU** : Modes de dessin variés (draw, eraser, static)

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/armelgeek/whiteboard-it.git
cd whiteboard-it

# Installer les dépendances
pip install opencv-python numpy

# Optionnel : pour la conversion H.264
pip install av
```

## Utilisation

### Mode image unique (classique)

```bash
# Génération simple
python whiteboard_animator.py image.png

# Avec paramètres personnalisés
python whiteboard_animator.py image.png --split-len 15 --frame-rate 30 --skip-rate 8
```

### Mode couches (nouveau)

Le mode couches permet de créer des animations complexes avec plusieurs images superposées, des effets de caméra, et des transitions.

```bash
# Utiliser une configuration JSON
python whiteboard_animator.py --config layers_config.json

# Ou directement avec le chemin JSON
python whiteboard_animator.py layers_config.json
```

**📖 Guide complet : [LAYERS_GUIDE.md](LAYERS_GUIDE.md)**

Exemples de configuration disponibles dans `examples/` :
- `layers_simple.json` - Configuration de base
- `layers_advanced.json` - Avec caméra et animations
- `layers_with_animations.json` - Modes variés
- `layers_multi_slide.json` - Multi-slides avec transitions

### Export des données d'animation (JSON)

```bash
# Générer vidéo + données JSON
python whiteboard_animator.py image.png --export-json
```

Cela génère :
- Une vidéo MP4 de l'animation
- Un fichier JSON contenant les données d'animation (séquence de dessin, positions de la main, etc.)

### Vérifier les valeurs recommandées

```bash
python whiteboard_animator.py image.png --get-split-lens
```

## Paramètres

- `--config` : Chemin vers un fichier JSON de configuration (mode couches)
- `--split-len` : Taille de la grille pour le dessin (par défaut: 15)
- `--frame-rate` : Images par seconde (par défaut: 30)
- `--skip-rate` : Vitesse de dessin (plus grand = plus rapide, par défaut: 8)
- `--duration` : Durée de l'image finale en secondes (par défaut: 3)
- `--export-json` : Exporter les données d'animation au format JSON
- `--get-split-lens` : Afficher les valeurs recommandées pour split-len

## Format d'export JSON

Voir [EXPORT_FORMAT.md](EXPORT_FORMAT.md) pour la documentation complète du format JSON.

Les données exportées incluent :
- Métadonnées (résolution, FPS, paramètres)
- Séquence de dessin frame par frame
- Positions de la main pour chaque frame
- Coordonnées des tuiles dessinées

## Exemples d'utilisation

Le dossier [examples/](examples/) contient des scripts d'exemple pour utiliser les données JSON exportées :

```bash
# Analyser une animation
python examples/use_animation_data.py animation.json

# Analyser et exporter une séquence simplifiée
python examples/use_animation_data.py animation.json --export-sequence sequence.json
```

## Cas d'utilisation du format JSON

L'export JSON permet de :
1. **Recréer l'animation** dans d'autres logiciels (After Effects, Blender, VideoScribe, etc.)
2. **Analyser la séquence** pour optimiser les paramètres
3. **Créer des animations personnalisées** en modifiant les données
4. **Intégrer dans des applications web** avec Canvas ou WebGL
5. **Générer des animations procédurales** basées sur les données

## Structure du projet

```
whiteboard-it/
├── whiteboard_animator.py   # Script principal
├── data/
│   └── images/              # Images de la main
├── save_videos/             # Dossier de sortie (ignoré par git)
├── examples/                # Scripts et configurations d'exemple
│   ├── use_animation_data.py
│   ├── layers_simple.json
│   ├── layers_advanced.json
│   ├── layers_with_animations.json
│   ├── layers_multi_slide.json
│   └── README.md
├── EXPORT_FORMAT.md         # Documentation du format JSON
├── LAYERS_GUIDE.md          # Guide complet du système de couches
└── README.md               # Ce fichier
```

## Licence

MIT

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou un pull request.
