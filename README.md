# 📟 remotionBinario

> **The Remotion of Embedded Systems.**  
> Create high-performance, smooth animations for OLED/LCD displays on microcontrollers (Arduino, ESP32, STM32) using a simple YAML-based DSL.

---

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Format Support](https://img.shields.io/badge/Formats-Horizontal_|_Vertical_|_Page-green.svg)](#output-formats)

---

## 🔥 Overview

**remotionBinario** is a specialized animation engine designed for the constraints of embedded displays. It allows you to describe complex visual sequences—complete with easing functions, sprites, and text—and exports them as highly optimized **PROGMEM C arrays**.

### Why use remotionBinario?

- **Zero Runtime Cost**: Animations are pre-rendered into bitmaps. Your MCU just needs to push pixels.
- **Delta Compression**: Saves up to **90% memory** by only storing changed regions between frames.
- **Easing System**: 9 standard curves (Bounce, Elastic, Cubic, etc.) for non-robotic feel.
- **Modern Workflow**: Preview your animations in the **Terminal**, as a **GIF**, or via a **Web-based Player** before compiling.

---

## ✨ Features

- 🖥️ **Canvas Agnostic**: Works with any resolution (128x64, 84x48, 128x128, etc.).
- 🎨 **Anti-Aliased Primitives**: Sub-pixel rendering simulation on 1-bit screens using 4x supersampling and dithering.
- 🔠 **Rich Typography**: Full support for `.ttf` and `.otf` fonts.
- 🖼️ **Sprite Imports**: Import PNG/JPG assets with intelligent 1-bit conversion (Threshold or Floyd-Steinberg dithering).
- 🎬 **Timeline Control**: Keyframe-based animation logic inspired by modern motion design tools.
- 📦 **Multi-Library Compatible**: Exports for `Adafruit_GFX`, `SSD1306`, `U8g2`, and more.

---

## 🚀 Getting Started

### Installation

```bash
git clone https://github.com/your-username/remotionBinario.git
cd remotionBinario
pip install -r requirements.txt
```

### Quick Run

```bash
# Generate a classic bouncing ball animation
python main.py examples/bouncing_ball.yaml
```

---

## 📖 Usage & DSL Reference

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
```

### Preview Modes

- **Web Preview**: `python main.py scene.yaml --serve` (Open `localhost:5050` for an interactive player).
- **GIF Export**: Automatically generated in `output/preview.gif`.
- **ASCII Debug**: Displays the animation directly in your terminal.

---

## 📦 Output Formats

| Format | Target Library | Scannning Logic |
| :--- | :--- | :--- |
| `horizontal` | Adafruit_GFX, SSD1306 | Row-major (1 byte = 8 horizontal pixels) |
| `vertical` | ST7565, SH1106 | Column-major (1 byte = 8 vertical pixels) |
| `page` | U8g2, U8x8 | 8px horizontal pages (Standard U8g2 format) |

---

## 🔧 Arduino Integration

1. Generate your header file: `python main.py your_scene.yaml --delta`.
2. Copy `output/animation.h` (or `animation_delta.h`) to your sketch folder.
3. Use the following snippet (Adafruit_GFX example):

```cpp
#include "animation.h"

void playAnimation() {
  for (int i = 0; i < FRAME_COUNT; i++) {
    display.clearDisplay();
    // Use pgm_read_ptr to fetch the far pointer from flash
    const uint8_t* framePtr = (const uint8_t*)pgm_read_ptr(&frames[i]);
    display.drawBitmap(0, 0, framePtr, FRAME_W, FRAME_H, WHITE);
    display.display();
    delay(1000 / FPS);
  }
}
```

---

## 🛠️ Commands

```bash
# Export with delta compression (recommended for ESP32/Arduino)
python main.py scene.yaml --delta

# Export specifically for U8g2
python main.py scene.yaml --format page

# View in browser with 6x scaling
python main.py scene.yaml --serve --scale 6
```

---

## 📜 License

MIT © [Raunick](https://github.com/raunick)
