"""
ASCII Preview — renders frames in the terminal.
"""

import os
import sys
import time
from ..canvas import Canvas


def print_frame(canvas: Canvas, chars: tuple = ("█", " "), border: bool = True):
    """Print a single frame to stdout using block characters."""
    pixels = canvas.image.load()
    on, off = chars

    if border:
        print("┌" + "─" * canvas.width + "┐")

    for y in range(canvas.height):
        row = ""
        for x in range(canvas.width):
            row += on if pixels[x, y] else off
        if border:
            print(f"│{row}│")
        else:
            print(row)

    if border:
        print("└" + "─" * canvas.width + "┘")


def print_animation(frames: list, fps: int, loops: int = 1, compact: bool = True):
    """Animate frames in terminal with clear between each.

    For large displays (>64px wide), use half-block chars for compact view.
    """
    delay = 1.0 / fps if fps > 0 else 0.1

    if compact and frames and frames[0].width > 40:
        chars = ("▓", " ")
    else:
        chars = ("█", " ")

    for loop in range(loops):
        for i, canvas in enumerate(frames):
            os.system("clear" if os.name != "nt" else "cls")
            print(f"  Frame {i + 1}/{len(frames)}  |  FPS: {fps}  |  Loop: {loop + 1}/{loops}")
            print_frame(canvas, chars=chars)
            time.sleep(delay)

    print(f"\n✓ Animation complete: {len(frames)} frames played.")
