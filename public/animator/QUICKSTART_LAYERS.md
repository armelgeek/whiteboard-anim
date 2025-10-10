# Quick Start Guide: Layers Feature

## What is the Layers Feature?

The layers feature allows you to create complex whiteboard animations by stacking multiple images with individual properties, similar to apps like Insta Doodle. Each layer can have its own:
- Position and scale
- Drawing speed
- Animation mode (hand, eraser, or static)
- Entrance/exit effects
- Camera zoom and focus

## Prerequisites

```bash
# Install Python dependencies
cd public/animator
pip install opencv-python numpy

# Optional: for H.264 video conversion
pip install av
```

## Basic Usage

### 1. Simple Two-Layer Animation

Create a file `my_animation.json`:

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
          "scale": 0.3,
          "skip_rate": 20
        }
      ]
    }
  ]
}
```

Run it:
```bash
python whiteboard_animator.py my_animation.json
```

### 2. With Camera Zoom

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 8,
      "layers": [
        {
          "image_path": "scene.png",
          "z_index": 1,
          "camera": {
            "zoom": 1.5,
            "position": {"x": 0.5, "y": 0.5}
          },
          "animation": {
            "type": "zoom_in",
            "duration": 2.0,
            "start_zoom": 1.5,
            "end_zoom": 2.0
          }
        }
      ]
    }
  ]
}
```

### 3. Multiple Slides with Transitions

```json
{
  "width": 1280,
  "height": 720,
  "slides": [
    {
      "index": 0,
      "duration": 4,
      "layers": [{"image_path": "intro.png", "z_index": 1}]
    },
    {
      "index": 1,
      "duration": 4,
      "layers": [{"image_path": "content.png", "z_index": 1}]
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

## Key Parameters

### Layer Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `image_path` | string | required | Path to image file |
| `position` | object | `{x:0, y:0}` | Position in pixels |
| `z_index` | int | 0 | Stacking order (higher = on top) |
| `skip_rate` | int | 8 | Drawing speed (higher = faster) |
| `scale` | float | 1.0 | Image scale (0.5 = 50%, 2.0 = 200%) |
| `opacity` | float | 1.0 | Transparency (0.0 = invisible, 1.0 = opaque) |
| `mode` | string | "draw" | Drawing mode: "draw", "eraser", or "static" |

### Animation Modes

- **"draw"** - Animated with hand drawing effect
- **"eraser"** - Animated with eraser effect
- **"static"** - No animation, appears instantly

### Entrance Animations

```json
"entrance_animation": {
  "type": "fade_in",
  "duration": 1.0
}
```

Types: `fade_in`, `slide_in_left`, `slide_in_right`, `zoom_in`

### Camera Controls

```json
"camera": {
  "zoom": 1.5,
  "position": {"x": 0.5, "y": 0.3}
}
```

- `zoom`: 1.0 = normal, 2.0 = 2x zoom
- `position`: 0.0 to 1.0 (0.5, 0.5 = center)

### Post-Drawing Animation

```json
"animation": {
  "type": "zoom_in",
  "duration": 2.0,
  "start_zoom": 1.0,
  "end_zoom": 2.5,
  "focus_position": {"x": 0.6, "y": 0.4}
}
```

Types: `zoom_in`, `zoom_out`, `none`

## Common Use Cases

### Tutorial/Educational Video
Focus on specific details with camera zoom:
```json
{
  "camera": {"zoom": 2.0, "position": {"x": 0.3, "y": 0.3}},
  "animation": {
    "type": "zoom_out",
    "duration": 1.5,
    "start_zoom": 2.0,
    "end_zoom": 1.0
  }
}
```

### Product Presentation
Logo + product + annotations at different speeds:
```json
{
  "layers": [
    {"image_path": "product.png", "z_index": 1, "skip_rate": 5},
    {"image_path": "logo.png", "z_index": 2, "scale": 0.2, "mode": "static"},
    {"image_path": "labels.png", "z_index": 3, "skip_rate": 30}
  ]
}
```

### Story with Multiple Scenes
```json
{
  "slides": [
    {"index": 0, "duration": 3, "layers": [{"image_path": "scene1.png"}]},
    {"index": 1, "duration": 3, "layers": [{"image_path": "scene2.png"}]},
    {"index": 2, "duration": 3, "layers": [{"image_path": "scene3.png"}]}
  ],
  "transitions": [
    {"after_slide": 0, "type": "fade", "duration": 0.5},
    {"after_slide": 1, "type": "fade", "duration": 0.5}
  ]
}
```

## Tips and Best Practices

1. **Image Preparation**: Use high-quality images with good contrast for best results
2. **Skip Rate**: Lower values (3-5) for detailed drawing, higher (20-40) for quick reveals
3. **Z-Index**: Organize layers logically (background=1, mid=2, foreground=3)
4. **Camera Zoom**: Values above 2.0 may show pixelation
5. **Duration**: Account for drawing time + animation time
6. **Transitions**: Keep them short (0.5-1.0 seconds) for smooth flow

## Troubleshooting

### Video is too fast/slow
- Adjust `skip_rate` (lower = slower)
- Increase `duration` in slide config

### Image doesn't appear
- Check `image_path` is correct (relative or absolute)
- Verify image file exists and is readable
- Check image format is supported (PNG, JPG)

### Layers in wrong order
- Verify `z_index` values (higher numbers on top)
- Make sure all layers have explicit z_index

### Camera zoom looks wrong
- Check `position` values are between 0.0 and 1.0
- Ensure `zoom` is reasonable (1.0-3.0 range)

## Examples

Pre-made examples are in `public/animator/examples/`:
- `layers_simple.json` - Basic two-layer setup
- `layers_advanced.json` - With camera controls
- `layers_with_animations.json` - Different animation modes
- `layers_multi_slide.json` - Multiple slides with transitions

Try them:
```bash
python whiteboard_animator.py examples/layers_simple.json
```

## Full Documentation

For complete details, see:
- **[LAYERS_GUIDE.md](LAYERS_GUIDE.md)** - Complete reference
- **[README.md](README.md)** - Animator documentation
- **[examples/README.md](examples/README.md)** - Example configurations

## Command Line Options

```bash
# Basic usage
python whiteboard_animator.py config.json

# With custom frame rate
python whiteboard_animator.py config.json --frame-rate 60

# Export animation metadata
python whiteboard_animator.py config.json --export-json
```

Options:
- `--config FILE` - Path to JSON configuration
- `--frame-rate FPS` - Video frame rate (default: 30)
- `--split-len SIZE` - Grid size for drawing (default: 15)
- `--export-json` - Export animation metadata

## Next Steps

1. Try the example configurations
2. Create your own simple 2-layer animation
3. Experiment with camera zoom and animations
4. Build a multi-slide story
5. Read [LAYERS_GUIDE.md](LAYERS_GUIDE.md) for advanced features

Happy animating! 🎨
