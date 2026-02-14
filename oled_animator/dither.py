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
    """Floyd-Steinberg error-diffusion dithering for 1-bit output.

    Converts any image to grayscale first, then applies dithering
    to simulate tonal range on monochrome displays.
    """
    gray = image.convert("L")
    pixels = np.array(gray, dtype=np.float64)
    h, w = pixels.shape

    for y in range(h):
        for x in range(w):
            old_val = pixels[y, x]
            new_val = 255.0 if old_val >= 128.0 else 0.0
            pixels[y, x] = new_val
            error = old_val - new_val

            if x + 1 < w:
                pixels[y, x + 1] += error * 7.0 / 16.0
            if y + 1 < h:
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += error * 3.0 / 16.0
                pixels[y + 1, x] += error * 5.0 / 16.0
                if x + 1 < w:
                    pixels[y + 1, x + 1] += error * 1.0 / 16.0

    result = np.clip(pixels, 0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="L").convert("1")
