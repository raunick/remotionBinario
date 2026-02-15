# 📟 remotionBinario

> **The Remotion of Embedded Systems.**  
> Create high-performance, smooth animations for OLED/LCD displays on microcontrollers (Arduino, ESP32, STM32) using a simple YAML-based DSL.

---

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Format Support](https://img.shields.io/badge/Formats-Horizontal_|_Vertical_|_Page-green.svg)](#output-formats)

---

## 🔥 Overview

**remotionBinario** is a specialized animation engine designed for the constraints of embedded displays. It allows you to describe complex visual sequences—complete with easing functions, sprites, and text—and exports them as highly optimized **PROGMEM C arrays**.

### Why use remotionBinario?

- **Zero Runtime Cost**: Animations are pre-rendered into bitmaps. Your MCU just needs to push pixels.
- **Delta Compression**: Saves up to **90% memory** by only storing changed regions between frames.
- **Easing System**: 9 standard curves (Bounce, Elastic, Cubic, etc.) for non-robotic feel.
- **Studio Dashboard**: Preview, edit and export everything from a professional web interface.
- **SVG Import**: Bring any vector drawing into your project with automatic 1-bit conversion.

---

## ✨ Features

- 🖥️ **Canvas Agnostic**: Works with any resolution (128x64, 84x48, 128x128, etc.).
- 🎨 **Anti-Aliased Primitives**: Sub-pixel rendering simulation on 1-bit screens using 4x supersampling and dithering.
- 🔠 **Rich Typography**: Full support for `.ttf` and `.otf` fonts.
- 🖼️ **Sprite Imports**: Import PNG/JPG assets with intelligent 1-bit conversion (Threshold or Floyd-Steinberg dithering).
- 🎬 **Timeline Control**: Keyframe-based animation logic inspired by modern motion design tools.
- 📦 **Multi-Library Compatible**: Exports for `Adafruit_GFX`, `SSD1306`, `U8g2`, and more.
- 🎛️ **Studio Dashboard**: Web-based IDE with Monaco Editor, live OLED preview, and memory visualizer.
- 🖌️ **SVG Importer**: Convert any SVG to optimized sprites via Node.js toolchain.

---

## 🚀 Getting Started

### Installation

```bash
git clone https://github.com/raunick/remotionBinario.git
cd remotionBinario
pip install -r requirements.txt
```

### Quick Run

```bash
# Generate a classic bouncing ball animation
python3 main.py examples/bouncing_ball.yaml

# Launch the Studio Dashboard
python3 main.py --serve
```

---

## 🎛️ Studio Dashboard

The **remotionBinário Studio** is a professional web interface that integrates the entire toolchain:

```bash
python3 main.py --serve
# Open http://localhost:5050
```

| Feature | Description |
|---------|-------------|
| **Monaco Editor** | YAML editing with syntax highlighting, auto-complete, and custom dark theme |
| **Hot Reload** | Preview updates automatically ~600ms after editing |
| **OLED Simulator** | Simulated display with 4 color modes (white, blue, yellow, green) and screen-door effect |
| **Scene Explorer** | Browse and open all YAML scenes from the sidebar |
| **SVG Import** | Drag & drop SVG files — automatically converts and inserts YAML snippet |
| **Assets Library** | Visual grid of imported sprites, click to insert into editor |
| **Memory Visualizer** | Real-time ESP32 Flash usage (KB, %, bytes/frame) |
| **Export** | Download C-Array (.h), Delta (.h), or GIF directly from the browser |

---

## 🖌️ SVG Importer

Convert any SVG vector graphic into optimized 1-bit sprites for your OLED display.

### Setup

```bash
cd tools/svg_importer
npm install
```

### Usage

```bash
# Basic conversion
node svg2sprite.js icon.svg --width 64 --c-header

# With Floyd-Steinberg dithering
node svg2sprite.js logo.svg --width 128 --dither

# Inverted colors (for white-on-black OLEDs)
node svg2sprite.js drawing.svg --invert

# Animation sprite sheet (multiple frames)
node svg2sprite.js frame1.svg frame2.svg frame3.svg --spritesheet --height 64
```

**Output**: `*_preview.png` (visual check) + `*.h` (PROGMEM C array ready for Arduino/ESP32).

---

## 📖 YAML DSL Reference

Animations are defined in a structured YAML format.

```yaml
screen:
  width: 128
  height: 64
  fps: 15
  frames: 40

elements:
  - type: circle
    id: player_dot
    props:
      cx: 10
      cy: 32
      r: 6
      fill: true
      anti_alias: true
    keyframes:
      - frame: 0
        cx: 10
        easing: "ease-in-out"
      - frame: 20
        cx: 110
        easing: "bounce"
      - frame: 39
        cx: 10

output:
  c_array: true
  gif: true
  format: "horizontal"
  delta_compression: true
```

### Supported Elements

| Type | Required Props | Optional |
|------|---------------|----------|
| `circle` | `cx`, `cy`, `r` | `fill`, `anti_alias` |
| `rect` | `x`, `y`, `w`, `h` | `fill`, `anti_alias` |
| `line` | `x1`, `y1`, `x2`, `y2` | `anti_alias` |
| `text` | `x`, `y`, `text` | `font_size`, `font_path` |
| `sprite` | `x`, `y`, `src` | `dithering` |

### Easing Functions

`linear` · `ease-in` · `ease-out` · `ease-in-out` · `cubic-in` · `cubic-out` · `cubic-in-out` · `elastic` · `elastic-out` · `elastic-in-out` · `bounce` · `bounce-out`

> [!TIP]
> **Dasai Mochi Style**: Use `elastic-out` for the classic "bouncy" spring effect. The engine now includes automatic coordinate normalization, making it robust against negative dimensions during high-elasticity bounces.

---

## 🍶 Dasai Mochi Pack

This project includes a special set of examples inspired by the **Dasai Mochi** (Gen 3) robot. You can find them in `examples/dasai_mochi/`:

- **Turbo**: Boost explosion with elastic eyes and speed lines.
- **Rain**: Sad melancholy with falling rain drops.
- **F1**: Sequential shift lights and G-force effects.
- **One Piece**: Star-sparkle eyes and mega-grin (Luffy mode).
- **Retro**: 70s/80s Arcade vibes with scanlines and Pac-Man.

---

## 📦 Output Formats

| Format | Target Library | Scanning Logic |
| :--- | :--- | :--- |
| `horizontal` | Adafruit_GFX, SSD1306 | Row-major (1 byte = 8 horizontal pixels) |
| `vertical` | ST7565, SH1106 | Column-major (1 byte = 8 vertical pixels) |
| `page` | U8g2, U8x8 | 8px horizontal pages (Standard U8g2 format) |

---

## 🔧 Arduino Integration

1. Generate your header file: `python3 main.py your_scene.yaml --delta`.
2. Copy `output/animation.h` (or `animation_delta.h`) to your sketch folder.
3. Use the following snippet (Adafruit_GFX example):

```cpp
#include "animation.h"

void playAnimation() {
  for (int i = 0; i < FRAME_COUNT; i++) {
    display.clearDisplay();
    const uint8_t* framePtr = (const uint8_t*)pgm_read_ptr(&frames[i]);
    display.drawBitmap(0, 0, framePtr, FRAME_W, FRAME_H, WHITE);
    display.display();
    delay(1000 / FPS);
  }
}
```

---

## 🛠️ CLI Reference

```bash
# Render and export (C-array + GIF + ASCII preview)
python3 main.py scene.yaml

# Export with delta compression (recommended for ESP32)
python3 main.py scene.yaml --delta

# Export for U8g2
python3 main.py scene.yaml --format page

# Launch Studio Dashboard
python3 main.py --serve

# Custom port
python3 main.py --serve --port 8080
```

---

## 📁 Project Structure

```
remotionBinario/
├── main.py                    # CLI entry point
├── oled_animator/             # Python animation engine
│   ├── engine.py              # Core renderer + keyframe interpolation
│   ├── dsl.py                 # YAML parser
│   ├── canvas.py              # Bitmap canvas
│   ├── primitives.py          # Drawing functions
│   ├── easing.py              # Easing curves
│   └── exporters/             # C-array, delta, GIF, ASCII exporters
├── web_preview/               # Studio Dashboard (Flask)
│   ├── server.py              # Backend API
│   └── templates/
│       └── dashboard.html     # Studio SPA
├── tools/
│   └── svg_importer/          # Node.js SVG converter
│       └── svg2sprite.js      # CLI tool
├── examples/                  # Sample YAML scenes
├── assets/                    # Imported sprites
└── output/                    # Generated files
```

---

## 📜 License

MIT © [Raunick](https://github.com/raunick)
