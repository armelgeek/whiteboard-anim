# Exemples d'utilisation

Ce répertoire contient des exemples de scripts et de configurations pour utiliser l'animateur whiteboard.

## 📄 Configurations JSON pour le mode couches

### layers_simple.json
Configuration de base avec deux couches simples : fond et logo.

```bash
python ../whiteboard_animator.py layers_simple.json
```

**Fonctionnalités démontrées :**
- Superposition de couches
- Ordre z-index
- Vitesses de dessin différentes
- Échelle d'image

### layers_advanced.json
Configuration avancée avec contrôles de caméra et animations post-dessin.

```bash
python ../whiteboard_animator.py layers_advanced.json
```

**Fonctionnalités démontrées :**
- Zoom et focus de caméra
- Animation zoom-in progressive
- Effets cinématiques

### layers_with_animations.json
Démontre les différents modes de dessin et animations d'entrée/sortie.

```bash
python ../whiteboard_animator.py layers_with_animations.json
```

**Fonctionnalités démontrées :**
- Mode "draw" (main)
- Mode "eraser" (gomme)
- Mode "static" (sans animation)
- Animations d'entrée (fade_in, zoom_in)
- Animations de sortie (fade_out)

### layers_multi_slide.json
Exemple avec plusieurs slides et transitions.

```bash
python ../whiteboard_animator.py layers_multi_slide.json
```

**Fonctionnalités démontrées :**
- Multi-slides
- Transitions entre slides (fade)
- Narration visuelle

## 🐍 Scripts Python

### use_animation_data.py

Script Python qui démontre comment charger et analyser les données d'animation exportées en JSON.

#### Utilisation

```bash
# Analyser un fichier d'animation
python use_animation_data.py animation.json

# Analyser et exporter une séquence simplifiée
python use_animation_data.py animation.json --export-sequence sequence.json
```

#### Fonctionnalités

- **Résumé de l'animation** : Affiche les métadonnées (résolution, FPS, etc.)
- **Analyse du chemin** : Calcule la distance parcourue par la main
- **Export de séquence** : Exporte une version simplifiée de la séquence de dessin

#### Exemple de sortie

```
============================================================
RÉSUMÉ DE L'ANIMATION
============================================================

📊 Métadonnées:
  • Résolution: 720x640
  • FPS: 30
  • Taille de grille: 15
  • Taux de saut: 10
  • Nombre total de frames: 19
  • Dimensions de la main: 284x467

🎬 Séquence de dessin:
  • Frames enregistrées: 19
  • Première tuile dessinée: position grille [9, 7]
  • Dernière tuile dessinée: position grille [21, 36]
  • Durée estimée du dessin: 0.63 secondes

============================================================

============================================================
ANALYSE DU CHEMIN DE DESSIN
============================================================

📏 Distance totale parcourue par la main: 2123.45 pixels
📏 Distance moyenne entre frames: 117.97 pixels

📍 Zone de dessin:
  • X: 97 → 547 (étendue: 450 pixels)
  • Y: 112 → 487 (étendue: 375 pixels)

============================================================
```

## 📝 Créer vos propres configurations

### Structure minimale

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 5,
      "layers": [
        {
          "image_path": "your_image.png",
          "z_index": 1
        }
      ]
    }
  ]
}
```

### Personnalisation des couches

Voir [LAYERS_GUIDE.md](../LAYERS_GUIDE.md) pour la documentation complète de toutes les propriétés disponibles :
- Position et échelle
- Modes de dessin (draw, eraser, static)
- Animations d'entrée/sortie
- Contrôles de caméra
- Effets post-dessin
- Morphing entre couches

## 🎨 Créer vos propres scripts

Vous pouvez créer vos propres scripts pour utiliser les données d'animation. Voici un exemple simple :

```python
import json

# Charger les données
with open('animation.json', 'r') as f:
    data = json.load(f)

# Accéder aux métadonnées
width = data['metadata']['width']
height = data['metadata']['height']

# Parcourir les frames
for frame in data['animation']['frames_written']:
    x = frame['hand_position']['x']
    y = frame['hand_position']['y']
    print(f"Frame {frame['frame_number']}: Main à ({x}, {y})")
```

## 💡 Cas d'utilisation

Les données d'animation exportées peuvent être utilisées pour :

1. **Recréer l'animation** dans d'autres logiciels (After Effects, Blender, etc.)
2. **Optimiser les paramètres** en analysant la séquence de dessin
3. **Créer des animations personnalisées** en modifiant la séquence
4. **Intégrer dans des applications web** avec Canvas ou WebGL
5. **Générer des animations procédurales** basées sur les données

### Le système de couches permet de :

1. **Tutoriels interactifs** : Zoom sur des détails importants
2. **Présentations produits** : Superposition logo + produit + annotations
3. **Storytelling visuel** : Histoires multi-scènes avec transitions
4. **Animations cinématiques** : Effets de zoom et transitions professionnelles

## 📚 Documentation

- [LAYERS_GUIDE.md](../LAYERS_GUIDE.md) - Guide complet du système de couches
- [EXPORT_FORMAT.md](../EXPORT_FORMAT.md) - Format JSON d'export
- [README.md](../README.md) - Documentation principale
