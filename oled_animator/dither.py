"""
Dithering & threshold conversion for 1-bit displays.
"""

from PIL import Image
import numpy as np


def apply_threshold(image: Image.Image, threshold: int = 128) -> Image.Image:
    """Simple binary threshold. Pixels >= threshold become white."""
    gray = image.convert("L")
    return gray.point(lambda p: 255 if p >= threshold else 0).convert("1")


def apply_dithering(image: Image.Image, method: str = "floyd-steinberg") -> Image.Image:
    """Apply dithering algorithm to convert image to 1-bit monochrome.

    Supported methods:
      - "floyd-steinberg": Standard error diffusion (default).
      - "atkinson": High-contrast error diffusion (HyperCard style).
      - "stucki": Clean, sharp error diffusion.
      - "ordered": Bayer 4x4 ordered dithering.
      - "simple": Simple threshold (no dithering).
    """
    if method == "simple":
        return apply_threshold(image)

    gray = image.convert("L")
    pixels = np.array(gray, dtype=np.float64)
    h, w = pixels.shape

    if method == "ordered":
        # Bayer 4x4 matrix
        bayer = np.array([
            [ 0,  8,  2, 10],
            [12,  4, 14,  6],
            [ 3, 11,  1,  9],
            [15,  7, 13,  5]
        ], dtype=np.float64) * (255.0 / 16.0)

        for y in range(h):
            for x in range(w):
                threshold = bayer[y % 4, x % 4]
                pixels[y, x] = 255.0 if pixels[y, x] > threshold else 0.0

    elif method in ["floyd-steinberg", "atkinson", "stucki"]:
        # Error diffusion loop
        for y in range(h):
            for x in range(w):
                old_val = pixels[y, x]
                new_val = 255.0 if old_val >= 128.0 else 0.0
                pixels[y, x] = new_val
                error = old_val - new_val

                if method == "floyd-steinberg":
                    propagate_error(pixels, x, y, w, h, error, [
                        (1, 0, 7/16),
                        (-1, 1, 3/16), (0, 1, 5/16), (1, 1, 1/16)
                    ])

                elif method == "atkinson":
                    propagate_error(pixels, x, y, w, h, error, [
                        (1, 0, 1/8), (2, 0, 1/8),
                        (-1, 1, 1/8), (0, 1, 1/8), (1, 1, 1/8),
                        (0, 2, 1/8)
                    ])

                elif method == "stucki":
                    propagate_error(pixels, x, y, w, h, error, [
                        (1, 0, 8/42), (2, 0, 4/42),
                        (-2, 1, 2/42), (-1, 1, 4/42), (0, 1, 8/42), (1, 1, 4/42), (2, 1, 2/42),
                        (-2, 2, 1/42), (-1, 2, 2/42), (0, 2, 4/42), (1, 2, 2/42), (2, 2, 1/42)
                    ])

    result = np.clip(pixels, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="L").convert("1")


def propagate_error(pixels, x, y, w, h, error, distribution):
    """Helper to distribute error to neighboring pixels."""
    for dx, dy, factor in distribution:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            pixels[ny, nx] += error * factor
