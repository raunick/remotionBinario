---
name: create_oled_animation
description: Create and export optimized OLED animations for Arduino/ESP32 using remotionBinario. Supports YAML DSL, SVG import, Studio Dashboard, and multiple export formats.
---

# OLED Animation Expert

This skill allows you to create high-performance animations for embedded displays (OLED/LCD) using the `remotionBinario` engine. You will define animations in YAML, preview them in the Studio Dashboard, import SVGs, and export to C arrays.

## 🛠️ Usage Steps

### 1. Understand Requirements
- **Resolution**: Typically 128x64 (default), but can be 128x32, 84x48, etc. Must be divisible by 8.
- **Duration**: How long should it last? (Frames = FPS × Seconds).
- **Style**: Shapes, text, sprites, or complex motion?
- **Assets**: Does the user have SVGs or images to import?

### 2. Create Scene File (YAML)
Create a new YAML file (e.g., `examples/my_scene.yaml`) with the animation definition.

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
      anti_alias: true
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

**Supported Elements:**

| Type | Required Props | Optional Props |
|------|---------------|----------------|
| `circle` | `cx`, `cy`, `r` | `fill`, `anti_alias` |
| `rect` | `x`, `y`, `w`, `h` | `fill`, `anti_alias` |
| `line` | `x1`, `y1`, `x2`, `y2` | `anti_alias` |
| `text` | `x`, `y`, `text` | `font_size`, `font_path` |
| `sprite` | `x`, `y`, `src` | `dithering` |

**Easings:** `linear`, `ease-in`, `ease-out`, `ease-in-out`, `cubic-in`, `cubic-out`, `cubic-in-out`, `bounce`, `elastic`

### 3. Import SVGs (if needed)
If the user has SVG assets, convert them to 1-bit sprites:

```bash
# Install dependencies (first time only)
cd tools/svg_importer && npm install && cd ../..

# Convert SVG → optimized PNG + C header
node tools/svg_importer/svg2sprite.js icon.svg --width 64 --dither --c-header

# With color inversion (white on black)
node tools/svg_importer/svg2sprite.js logo.svg --width 32 --invert
```

The output PNG goes to `assets/` and can be used as a `sprite` element in YAML:
```yaml
  - type: sprite
    id: my_icon
    props:
      x: 0
      y: 0
      src: "assets/icon.png"
```

### 4. Preview with Studio Dashboard
For an interactive preview with hot-reload:

```bash
python3 main.py --serve
# Open http://localhost:5050
```

The Studio provides:
- **Monaco Editor** with YAML syntax highlighting
- **Live OLED Preview** that updates automatically when you edit
- **SVG Drag & Drop** import directly in the browser
- **Memory Visualizer** showing ESP32 Flash usage
- **Export buttons** for C-Array, Delta, and GIF

### 5. Generate Animation (CLI)
Run the engine to process the YAML file:

```bash
# Full export (C-array + GIF + ASCII preview)
python3 main.py examples/my_scene.yaml

# With delta compression (recommended for ESP32)
python3 main.py examples/my_scene.yaml --delta

# For U8g2 displays
python3 main.py examples/my_scene.yaml --format page
```

**CLI Arguments:**
- `--delta`: Delta compression (saves up to 90% flash memory).
- `--format`: Override format (`horizontal`, `vertical`, `page`).
- `--serve`: Launch Studio Dashboard (no scene file needed).
- `--port`: Custom port for Studio (default: 5050).
- `--no-gif`: Skip GIF generation.
- `--no-ascii`: Skip ASCII terminal preview.

### 6. Verify Output
Check the output directory (default `output/`):
- `animation.h`: Standard C-array header file.
- `animation_delta.h`: Delta-compressed header (if `--delta` used).
- `preview.gif`: Visual confirmation of the animation.

## 💡 Pro Tips
- **Performance**: Keep FPS between 10-20 for heavy animations on 8-bit MCUs.
- **Memory**: Always use `--delta` for ESP32 to save flash memory.
- **Text**: Use `font_path` to load custom TTF/OTF files if available.
- **SVGs**: Complex designs (logos, icons) should be imported as sprites, not drawn with primitives.
- **Studio**: Use the dashboard for rapid iteration — edit YAML, see results instantly.
- **Screen door**: The OLED preview in Studio simulates the real pixel grid for accurate visualization.
