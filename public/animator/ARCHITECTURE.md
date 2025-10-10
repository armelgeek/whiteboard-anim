# Layers System Architecture

## Conceptual Overview

```
┌─────────────────────────────────────────────────────────┐
│                    VIDEO OUTPUT                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                     │  │
│  │  ┌──────────────────────┐  ← z_index: 3          │  │
│  │  │  Logo (static)       │                          │  │
│  │  │  scale: 0.3          │                          │  │
│  │  └──────────────────────┘                          │  │
│  │                                                     │  │
│  │        ┌────────────────────────┐  ← z_index: 2   │  │
│  │        │  Annotation (drawn)    │                  │  │
│  │        │  skip_rate: 20         │                  │  │
│  │        └────────────────────────┘                  │  │
│  │                                                     │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Background (drawn slowly)                   │  │  │
│  │  │  z_index: 1, skip_rate: 5                   │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Layer Processing Flow

```
┌─────────────┐
│ JSON Config │
└──────┬──────┘
       │
       ├─> Load Configuration
       │   - width, height
       │   - slides array
       │   - transitions
       │
       ├─> For Each Slide:
       │   │
       │   ├─> Sort Layers by z_index
       │   │   (lower numbers first)
       │   │
       │   └─> For Each Layer:
       │       │
       │       ├─> Load Image
       │       │
       │       ├─> Apply Properties
       │       │   - position (x, y)
       │       │   - scale
       │       │   - opacity
       │       │
       │       ├─> Apply Mode
       │       │   - draw: hand animation
       │       │   - eraser: eraser animation
       │       │   - static: no animation
       │       │
       │       ├─> Entrance Animation?
       │       │   - fade_in
       │       │   - slide_in_*
       │       │   - zoom_in
       │       │
       │       ├─> Camera Transform?
       │       │   - zoom level
       │       │   - focus position
       │       │
       │       ├─> Post Animation?
       │       │   - zoom_in/out
       │       │   - duration
       │       │
       │       └─> Composite onto Canvas
       │
       └─> Apply Slide Transition
           - fade
           - dissolve
           │
           ├─> Next Slide
           │
           └─> Write Video Frames
```

## Animation Timeline Example

```
Slide 0 (duration: 8 seconds)
┌────────────────────────────────────────────────────────────┐
│ Layer 1 (Background)                                       │
│ ════════════════════════ (drawn over 3s)                   │
│                                                            │
│     Layer 2 (Logo)                                         │
│     ▓▓▓▓ (static, appears at 3s with zoom_in)             │
│                                                            │
│         Layer 3 (Annotation)                               │
│         ────────────── (drawn 1s)                          │
│                                                            │
│                   Post-Animation (zoom)                    │
│                   ░░░░░░░░░░░░ (2s)                       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ 0s   1s   2s   3s   4s   5s   6s   7s   8s               │
└────────────────────────────────────────────────────────────┘
                          ↓
                   [Transition: fade 0.8s]
                          ↓
Slide 1 (duration: 4 seconds)
┌────────────────────────────────────────────────────────────┐
│ Layer 1 (New Scene)                                        │
│ ════════════════════════════════                           │
└────────────────────────────────────────────────────────────┘
```

## Layer Properties Matrix

```
Property         │ Type   │ Default    │ Effect
─────────────────┼────────┼────────────┼─────────────────────────
image_path       │ string │ required   │ Source image
position.x       │ int    │ 0          │ Horizontal offset (pixels)
position.y       │ int    │ 0          │ Vertical offset (pixels)
z_index          │ int    │ 0          │ Stacking order
skip_rate        │ int    │ 8          │ Drawing speed (↑ faster)
scale            │ float  │ 1.0        │ Size multiplier
opacity          │ float  │ 1.0        │ Transparency (0-1)
mode             │ string │ "draw"     │ draw/eraser/static
entrance_anim    │ object │ null       │ How it appears
exit_anim        │ object │ null       │ How it disappears
camera           │ object │ null       │ Zoom & focus
animation        │ object │ null       │ Post-drawing effect
morph            │ object │ null       │ Blend from previous
```

## Camera System

```
Original Image (1280x720)
┌─────────────────────────────────────┐
│                                     │
│                                     │
│         ┌───────────┐               │
│         │  Focus    │               │  Camera Config:
│         │  Point    │               │  {
│         │  (0.5,0.3)│               │    "zoom": 1.5,
│         └───────────┘               │    "position": {
│              ↑                      │      "x": 0.5,
│         Crop & Zoom                 │      "y": 0.3
│         this region                 │    }
│                                     │  }
│                                     │
└─────────────────────────────────────┘
              ↓
       Zoom 1.5x
              ↓
Rendered Frame (1280x720)
┌─────────────────────────────────────┐
│                                     │
│                                     │
│                                     │
│         ZOOMED CONTENT              │
│         (focused on 0.5, 0.3)       │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

## Animation Effect System

```
Post-Drawing Animation: zoom_in
┌─────────────────────────────────────┐
│ Frame 0 (start_zoom: 1.0)           │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │        Full Scene               │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
              ↓ (progress)
┌─────────────────────────────────────┐
│ Frame N/2 (zoom: 1.75)              │
│   ┌───────────────────────────┐     │
│   │                           │     │
│   │    Zooming In             │     │
│   │                           │     │
│   └───────────────────────────┘     │
└─────────────────────────────────────┘
              ↓ (progress)
┌─────────────────────────────────────┐
│ Frame N (end_zoom: 2.5)             │
│     ┌─────────────────────┐         │
│     │                     │         │
│     │   Fully Zoomed     │         │
│     │                     │         │
│     └─────────────────────┘         │
└─────────────────────────────────────┘
```

## Mode Comparison

```
┌──────────────────────────────────────────────────────────┐
│                    MODE: "draw"                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Hand      ┌──────┐                             │    │
│  │  Icon  →   │░░░░░░│  (drawing progressively)    │    │
│  │            └──────┘                             │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   MODE: "eraser"                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Eraser    ┌──────┐                             │    │
│  │  Icon  →   │░░░░░░│  (erasing progressively)    │    │
│  │            └──────┘                             │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                   MODE: "static"                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  │  ████████  (appears instantly)                  │    │
│  │                                                  │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

## Complete Example Structure

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
          "image_path": "bg.png",
          "z_index": 1,
          "skip_rate": 5,
          "mode": "draw"
        },
        {
          "image_path": "content.png",
          "position": {"x": 100, "y": 100},
          "z_index": 2,
          "skip_rate": 15,
          "scale": 0.8,
          "mode": "draw",
          "camera": {
            "zoom": 1.2,
            "position": {"x": 0.5, "y": 0.5}
          }
        },
        {
          "image_path": "logo.png",
          "position": {"x": 50, "y": 50},
          "z_index": 3,
          "scale": 0.3,
          "mode": "static",
          "entrance_animation": {
            "type": "fade_in",
            "duration": 1.0
          }
        }
      ]
    }
  ]
}
```

This creates:
1. Background drawn slowly (5 second base)
2. Content drawn at medium speed with slight zoom
3. Logo appears instantly with fade effect

## Performance Considerations

```
Layer Count       Video Quality      Processing Time
────────────────────────────────────────────────────
1-2 layers   →    Excellent      →   Fast (< 1 min)
3-5 layers   →    Good           →   Medium (1-3 min)
6-10 layers  →    Fair           →   Slow (3-10 min)
10+ layers   →    Variable       →   Very Slow (10+ min)

Factors affecting performance:
- Image resolution
- skip_rate (lower = more frames)
- Animation complexity
- Number of post-effects
```

## Best Practices Checklist

```
✓ Use consistent image sizes (or resize appropriately)
✓ Set explicit z_index for all layers
✓ Balance skip_rate (3-5 slow, 10-15 medium, 20+ fast)
✓ Keep zoom values reasonable (1.0-3.0)
✓ Limit post-animations to key moments
✓ Test with short durations first
✓ Use static mode for logos/watermarks
✓ Keep slide transitions brief (0.5-1.0s)
✓ Total slides < 10 for maintainability
✓ Document your layer purpose in comments
```
