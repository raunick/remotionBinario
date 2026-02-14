"""
GIF Preview — generates animated GIF from rendered frames.
"""

import os
from PIL import Image
from ..canvas import Canvas


def save_gif(
    frames: list,
    output_path: str,
    fps: int,
    scale: int = 4,
    bg_color: int = 0,
    fg_color: int = 255,
):
    """Save rendered frames as an animated GIF.

    Scales up the tiny OLED resolution for comfortable viewing.
    128x64 @ scale=4 → 512x256 GIF.
    """
    if not frames:
        return None

    duration_ms = int(1000 / fps) if fps > 0 else 100
    pil_frames = []

    for canvas in frames:
        img = canvas.get_image().convert("L")
        scaled = img.resize(
            (canvas.width * scale, canvas.height * scale),
            Image.NEAREST,
        )
        pil_frames.append(scaled.convert("P"))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    pil_frames[0].save(
        output_path,
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )

    return {
        "path": output_path,
        "frame_count": len(pil_frames),
        "resolution": f"{frames[0].width * scale}x{frames[0].height * scale}",
        "duration_ms": duration_ms,
    }
