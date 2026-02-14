"""
Drawing primitives for OLED canvas.

Supports: rect, circle, line, text (TTF), sprite (PNG).
Anti-aliasing via 4x supersampling + dithering on edges.
"""

from PIL import Image, ImageDraw, ImageFont
from .canvas import Canvas
from .dither import apply_dithering, apply_threshold

DEFAULT_FONT = ImageFont.load_default()
AA_SCALE = 4


def _load_font(font_path: str = None, font_size: int = 10) -> ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except (IOError, OSError):
            pass
    return DEFAULT_FONT


def draw_rect(canvas: Canvas, x: int, y: int, w: int, h: int,
              fill: bool = True, anti_alias: bool = False):
    draw = ImageDraw.Draw(canvas.image)
    coords = [x, y, x + w - 1, y + h - 1]
    if fill:
        draw.rectangle(coords, fill=1)
    else:
        draw.rectangle(coords, outline=1)


def draw_circle(canvas: Canvas, cx: int, cy: int, r: int,
                fill: bool = True, anti_alias: bool = False):
    if anti_alias:
        _draw_circle_aa(canvas, cx, cy, r, fill)
    else:
        draw = ImageDraw.Draw(canvas.image)
        bbox = [cx - r, cy - r, cx + r, cy + r]
        if fill:
            draw.ellipse(bbox, fill=1)
        else:
            draw.ellipse(bbox, outline=1)


def _draw_circle_aa(canvas: Canvas, cx: int, cy: int, r: int, fill: bool):
    """Anti-aliased circle via 4x supersampling + dithering."""
    big = Image.new("L", (canvas.width * AA_SCALE, canvas.height * AA_SCALE), 0)
    draw = ImageDraw.Draw(big)
    s = AA_SCALE
    bbox = [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s]
    if fill:
        draw.ellipse(bbox, fill=255)
    else:
        draw.ellipse(bbox, outline=255, width=s)

    small = big.resize((canvas.width, canvas.height), Image.LANCZOS)
    dithered = apply_dithering(small)

    mask = dithered.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if mask[x, y]:
                canvas.set_pixel(x, y, 1)


def draw_line(canvas: Canvas, x1: int, y1: int, x2: int, y2: int,
              anti_alias: bool = False):
    if anti_alias:
        _draw_line_aa(canvas, x1, y1, x2, y2)
    else:
        draw = ImageDraw.Draw(canvas.image)
        draw.line([x1, y1, x2, y2], fill=1)


def _draw_line_aa(canvas: Canvas, x1: int, y1: int, x2: int, y2: int):
    """Anti-aliased line via supersampling."""
    big = Image.new("L", (canvas.width * AA_SCALE, canvas.height * AA_SCALE), 0)
    draw = ImageDraw.Draw(big)
    s = AA_SCALE
    draw.line([x1 * s, y1 * s, x2 * s, y2 * s], fill=255, width=s)

    small = big.resize((canvas.width, canvas.height), Image.LANCZOS)
    dithered = apply_dithering(small)

    mask = dithered.load()
    for y in range(canvas.height):
        for x in range(canvas.width):
            if mask[x, y]:
                canvas.set_pixel(x, y, 1)


def draw_text(canvas: Canvas, x: int, y: int, text: str,
              font_size: int = 10, font_path: str = None):
    draw = ImageDraw.Draw(canvas.image)
    font = _load_font(font_path, font_size)
    draw.text((x, y), text, fill=1, font=font)


def draw_sprite(canvas: Canvas, x: int, y: int, src: str,
                dithering: bool = False):
    """Paste a PNG sprite onto the canvas at (x, y).

    Handles RGBA images by compositing onto black background first.
    """
    sprite = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", sprite.size, (0, 0, 0, 255))
    composited = Image.alpha_composite(bg, sprite).convert("L")

    if dithering:
        mono = apply_dithering(composited)
    else:
        mono = apply_threshold(composited)

    mono_pixels = mono.load()
    sw, sh = sprite.size
    for sy in range(sh):
        for sx in range(sw):
            px = x + sx
            py = y + sy
            if 0 <= px < canvas.width and 0 <= py < canvas.height:
                if mono_pixels[sx, sy]:
                    canvas.set_pixel(px, py, 1)
