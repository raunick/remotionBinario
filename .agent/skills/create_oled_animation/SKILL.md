---
name: create_oled_animation
description: Create and export optimized OLED animations for Arduino/ESP32 using remotionBinario.
---

# OLED Animation Expert

This skill allows you to create high-performance animations for embedded displays (OLED/LCD) using the `remotionBinario` engine. You will define animations in YAML and export them to C arrays.

## 🛠️ Usage Steps

### 1. Understand Requirements
- **Resolution**: Typically 128x64 (default), but can be 128x32, 84x48, etc. Must be divisible by 8.
- **Duration**: How long should it last? (Frames = FPS * Seconds).
- **Style**: Shapes, text, sprites, or complex motion?

### 2. Create Scene File (YAML)
Create a new YAML file (e.g., `scene.yaml`) with the animation definition.

**Template:**
```yaml
screen:
  width: 128
  height: 64
  fps: 15
  frames: 30

elements:
  - type: circle  # options: circle, rect, line, text, sprite
    id: my_obj
    props:
      cx: 10
      cy: 32
      r: 5
      fill: true
    keyframes:
      - frame: 0
        cx: 10
        easing: "ease-in-out"
      - frame: 29
        cx: 118
        
output:
  c_array: true
  gif: true
  delta_compression: true
  format: "horizontal" # horizontal (Adafruit), vertical (SH1106), page (U8g2)
```

**Key Constraints:**
- **Coords**: `x, y` for rect/text/sprite; `cx, cy` for circle; `x1, y1` for line.
- **Easings**: `linear`, `ease-in`, `ease-out`, `ease-in-out`, `bounce`, `elastic`.

### 3. Generate Animation
Run the engine to process the YAML file:

```bash
python main.py scene.yaml --delta
```

**Arguments:**
- `--delta`: Basic compression (recommended for ESP32).
- `--format`: Override format (`page`, `vertical`, `horizontal`).
- `--serve`: If user wants to preview in browser (stops script until killed).

### 4. Verify Output
Check the output directory (default `output/`):
- `animation_delta.h`: The C header file to give to the user.
- `preview.gif`: A visual confirmation of the animation.

## 💡 Pro Tips
- **Performance**: Keep FPS between 10-20 for heavy animations on 8-bit MCUs.
- **Memory**: Use `--delta` to save flash memory.
- **Text**: Use `font_path` to load custom TTF files if available.
