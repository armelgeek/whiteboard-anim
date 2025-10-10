# Guide d'utilisation des couches (Layers)

## Vue d'ensemble

La fonctionnalité de couches (layers) permet de superposer plusieurs images sur une même slide, similaire à des applications comme Insta Doodle. Chaque couche peut être positionnée précisément, avoir sa propre vitesse d'animation, et des propriétés visuelles personnalisées.

## Installation et prérequis

### Prérequis Python
- Python 3.7+
- OpenCV (`cv2`)
- NumPy
- PyAV (optionnel, pour conversion H.264)

### Installation
```bash
cd public/animator
pip install opencv-python numpy pyav
```

## Utilisation

### Mode image unique (classique)
```bash
python whiteboard_animator.py image.png
```

### Mode couches (nouveau)
```bash
python whiteboard_animator.py --config layers_config.json
# ou
python whiteboard_animator.py layers_config.json
```

### Options disponibles
- `--frame-rate FPS` : Images par seconde (défaut: 30)
- `--split-len SIZE` : Taille de la grille de dessin (défaut: 15)
- `--skip-rate RATE` : Vitesse de dessin (défaut: 8)
- `--export-json` : Exporter les métadonnées d'animation

## Structure de configuration JSON

### Configuration de base

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
          "image_path": "chemin/vers/image.png",
          "position": {"x": 0, "y": 0},
          "z_index": 1,
          "skip_rate": 5,
          "scale": 1.0,
          "opacity": 1.0,
          "mode": "draw"
        }
      ]
    }
  ],
  "transitions": []
}
```

### Propriétés des couches

#### Propriétés obligatoires

- **image_path** (string) : Chemin vers l'image de la couche
  ```json
  "image_path": "assets/background.png"
  ```

#### Propriétés optionnelles

- **position** (object, défaut: `{x: 0, y: 0}`) : Position en pixels
  ```json
  "position": {"x": 100, "y": 50}
  ```

- **z_index** (int, défaut: 0) : Ordre de superposition (plus grand = au-dessus)
  ```json
  "z_index": 2
  ```

- **skip_rate** (int, hérite de la config globale) : Vitesse de dessin
  - Valeurs basses (3-5) : dessin lent et détaillé
  - Valeurs moyennes (8-15) : vitesse normale
  - Valeurs hautes (20-40) : dessin rapide
  ```json
  "skip_rate": 10
  ```

- **scale** (float, défaut: 1.0) : Échelle de l'image
  ```json
  "scale": 0.3
  ```

- **opacity** (float, défaut: 1.0) : Opacité (0.0 = transparent, 1.0 = opaque)
  ```json
  "opacity": 0.8
  ```

- **mode** (string, défaut: "draw") : Mode de dessin
  - `"draw"` : Animation normale avec main
  - `"eraser"` : Animation avec gomme
  - `"static"` : Affichage direct sans animation
  ```json
  "mode": "static"
  ```

#### Animations d'entrée et de sortie

- **entrance_animation** (object, optionnel) : Animation d'entrée
  ```json
  "entrance_animation": {
    "type": "fade_in",
    "duration": 1.0
  }
  ```
  Types disponibles : `fade_in`, `slide_in_left`, `slide_in_right`, `slide_in_top`, `slide_in_bottom`, `zoom_in`, `none`

- **exit_animation** (object, optionnel) : Animation de sortie
  ```json
  "exit_animation": {
    "type": "fade_out",
    "duration": 0.8
  }
  ```
  Types disponibles : `fade_out`, `slide_out_left`, `slide_out_right`, `slide_out_top`, `slide_out_bottom`, `zoom_out`, `none`

#### Contrôles de caméra

- **camera** (object, optionnel) : Configuration de zoom et focus
  ```json
  "camera": {
    "zoom": 1.5,
    "position": {"x": 0.5, "y": 0.3}
  }
  ```
  - `zoom` : Niveau de zoom (1.0 = normal, 2.0 = zoom x2)
  - `position` : Point focal (0.0-1.0, où 0.5 = centre)

#### Effets d'animation post-dessin

- **animation** (object, optionnel) : Effets après le dessin
  ```json
  "animation": {
    "type": "zoom_in",
    "duration": 2.0,
    "start_zoom": 1.0,
    "end_zoom": 2.5,
    "focus_position": {"x": 0.6, "y": 0.4}
  }
  ```
  Types : `zoom_in`, `zoom_out`, `none`

#### Morphing

- **morph** (object, optionnel) : Transition fluide depuis la couche précédente
  ```json
  "morph": {
    "enabled": true,
    "duration": 0.5
  }
  ```

### Propriétés des slides

- **index** (int) : Numéro de la slide (ordre de lecture)
- **duration** (float) : Durée totale de la slide en secondes
- **layers** (array) : Liste des couches

### Transitions entre slides

```json
"transitions": [
  {
    "after_slide": 0,
    "type": "fade",
    "duration": 0.8
  }
]
```

Types de transitions : `fade`, `dissolve`

## Exemples pratiques

### Exemple 1 : Logo + Fond simple

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
          "image_path": "background.png",
          "z_index": 1,
          "skip_rate": 5
        },
        {
          "image_path": "logo.png",
          "position": {"x": 50, "y": 50},
          "z_index": 2,
          "skip_rate": 20,
          "scale": 0.3
        }
      ]
    }
  ]
}
```

**Résultat :**
1. Le fond est dessiné lentement
2. Le logo apparaît rapidement en haut à gauche, réduit à 30%

### Exemple 2 : Présentation avec zoom progressif

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 10,
      "layers": [
        {
          "image_path": "scene.png",
          "z_index": 1,
          "skip_rate": 10,
          "camera": {
            "zoom": 1.5,
            "position": {"x": 0.5, "y": 0.4}
          },
          "animation": {
            "type": "zoom_in",
            "duration": 2.0,
            "start_zoom": 1.5,
            "end_zoom": 2.5,
            "focus_position": {"x": 0.6, "y": 0.4}
          }
        }
      ]
    }
  ]
}
```

**Résultat :**
1. La scène est dessinée avec un zoom de 1.5x
2. Après le dessin, un zoom progressif de 1.5x à 2.5x est appliqué

### Exemple 3 : Modes d'animation variés

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 12,
      "layers": [
        {
          "image_path": "scene.png",
          "z_index": 1,
          "skip_rate": 10,
          "mode": "draw"
        },
        {
          "image_path": "error.png",
          "position": {"x": 200, "y": 150},
          "z_index": 2,
          "skip_rate": 15,
          "mode": "eraser",
          "entrance_animation": {
            "type": "fade_in",
            "duration": 1.0
          }
        },
        {
          "image_path": "logo.png",
          "position": {"x": 50, "y": 50},
          "z_index": 3,
          "scale": 0.3,
          "mode": "static",
          "entrance_animation": {
            "type": "zoom_in",
            "duration": 1.5
          },
          "exit_animation": {
            "type": "fade_out",
            "duration": 1.0
          }
        }
      ]
    }
  ]
}
```

**Résultat :**
1. Scène de fond dessinée normalement
2. Élément "error" effacé avec animation de gomme
3. Logo apparaît statiquement avec zoom-in, puis disparaît en fondu

### Exemple 4 : Multi-slides avec transitions

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 4,
      "layers": [
        {
          "image_path": "intro.png",
          "z_index": 1,
          "skip_rate": 8
        }
      ]
    },
    {
      "index": 1,
      "duration": 3,
      "layers": [
        {
          "image_path": "content.png",
          "z_index": 1,
          "skip_rate": 15
        }
      ]
    }
  ],
  "transitions": [
    {
      "after_slide": 0,
      "type": "fade",
      "duration": 0.8
    }
  ]
}
```

## Cas d'usage

### 1. Tutoriels avec focus
Créez des animations éducatives qui zoomrent sur des détails importants.

### 2. Présentations de produits
Superposez logo, produit, et annotations avec différents timings.

### 3. Storytelling visuel
Créez des histoires multi-scènes avec transitions fluides.

### 4. Animations cinématiques
Utilisez les effets de zoom et les transitions pour un rendu professionnel.

## Dépannage

### L'image n'apparaît pas
- Vérifiez que le chemin `image_path` est correct (relatif ou absolu)
- Vérifiez que l'image existe et est lisible par OpenCV

### L'animation est trop rapide/lente
- Ajustez `skip_rate` : valeurs basses = lent, valeurs hautes = rapide
- Ajustez `duration` de la slide

### Le zoom ne fonctionne pas comme attendu
- Vérifiez que `camera.zoom` > 1.0
- Assurez-vous que `camera.position` est entre 0.0 et 1.0

### Les couches ne s'affichent pas dans le bon ordre
- Vérifiez les valeurs `z_index` : plus grand = au-dessus

## Fichiers d'exemple

Des configurations d'exemple sont disponibles dans `public/animator/examples/` :
- `layers_simple.json` : Configuration basique
- `layers_advanced.json` : Avec caméra et animations
- `layers_with_animations.json` : Modes variés
- `layers_multi_slide.json` : Multi-slides avec transitions

## Support et contributions

Pour signaler des bugs ou proposer des améliorations, consultez le README principal du projet.
