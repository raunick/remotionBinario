"""
Image Converter — handles image loading, processing, and conversion to 1-bit Canvas.
Supports single images and ZIP archives.
"""

import io
import os
import zipfile
from PIL import Image, ImageOps
from typing import List, Dict, Union, Tuple

from .dither import apply_dithering, apply_threshold
from .canvas import Canvas


VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp")


def process_image(
    file_stream: Union[str, bytes, io.BytesIO],
    filename: str,
    settings: Dict,
) -> Dict:
    """
    Process a single image file stream into a 1-bit Canvas.

    Args:
        file_stream: Path or file-like object
        filename: Original filename
        settings: Dict with keys:
            - width, height (int)
            - background (str): "white", "black", "transparent"
            - scale_mode (str): "original", "fit", "stretch", "center"
            - dither (str): "floyd-steinberg", "atkinson", "ordered", "simple"
            - threshold (int): 0-255
            - invert (bool)
            - rotate (int): 0, 90, 180, 270

    Returns:
        Dict with keys: name, canvas, preview_image, width, height
    """
    # Load image
    try:
        img = Image.open(file_stream)
        img.load()  # Ensure loaded
    except Exception as e:
        return {"error": str(e), "name": filename}

    target_w = settings.get("width", 128)
    target_h = settings.get("height", 64)
    bg_color = settings.get("background", "black")  # default to black background
    scale_mode = settings.get("scale_mode", "fit")
    dither_method = settings.get("dither", "floyd-steinberg")
    threshold = settings.get("threshold", 128)
    invert = settings.get("invert", False)
    rotate = settings.get("rotate", 0)

    # 1. Handle Alpha / Background
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        # Create background
        if bg_color == "white":
            bg = Image.new("RGB", img.size, (255, 255, 255))
        elif bg_color == "transparent": # Treat transparent as black effectively for 1-bit
            bg = Image.new("RGB", img.size, (0, 0, 0))
        else: # black
            bg = Image.new("RGB", img.size, (0, 0, 0))
        
        bg.paste(img, mask=img.convert("RGBA").split()[3])
        img = bg
    else:
        img = img.convert("RGB")

    # 2. Rotate
    if rotate in [90, 180, 270]:
        img = img.rotate(rotate, expand=True)

    # 3. Scale / Resize
    if scale_mode == "original":
        # Crop or pad to target size
        pass # Handle later during placement
    elif scale_mode == "fit":
        img = ImageOps.contain(img, (target_w, target_h), method=Image.Resampling.LANCZOS)
    elif scale_mode == "stretch":
        img = img.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)
    elif scale_mode == "center":
        # Keep original size, will center on canvas
        pass

    # 4. Create Final Canvas Image
    # Create a new image of target size with background color
    if bg_color == "white":
        final_bg_color = 255
    else:
        final_bg_color = 0

    # For dithering, we need grayscale.
    # If using threshold, we can stay in grayscale.
    
    # Place processed image onto target canvas
    canvas_img = Image.new("L", (target_w, target_h), final_bg_color)
    
    # Calculate position
    paste_x = (target_w - img.width) // 2
    paste_y = (target_h - img.height) // 2
    
    if scale_mode == "original" or scale_mode == "center":
        # For original, we might default to top-left (0,0) or center.
        # "center" implies centering. "original" usually implies 0,0 crop
        if scale_mode == "original":
            paste_x, paste_y = 0, 0
    
    canvas_img.paste(img.convert("L"), (paste_x, paste_y))

    # 5. Dithering / Threshold
    # We apply specific threshold if method is simple
    if dither_method == "simple":
        # Custom threshold logic (apply_threshold uses a fixed val, let's just use point)
        processed = canvas_img.point(lambda p: 255 if p >= threshold else 0).convert("1")
    else:
        # Apply error diffusion or ordered dithering
        # Check if we need to adjust brightness/contrast before dithering? 
        # For now, just apply dithering helper
        processed = apply_dithering(canvas_img, dither_method)

    # 6. Invert
    if invert:
        processed = ImageOps.invert(processed.convert("L")).convert("1")

    # 7. Create Canvas Object
    canvas = Canvas(target_w, target_h)
    canvas.image = processed
    
    return {
        "name": filename,
        "canvas": canvas,
        "preview_image": processed,
        "width": target_w,
        "height": target_h
    }


def process_zip(file_stream: Union[str, bytes, io.BytesIO], settings: Dict) -> List[Dict]:
    """
    Process all images in a ZIP file.
    """
    results = []
    try:
        with zipfile.ZipFile(file_stream) as z:
            for filename in sorted(z.namelist()):
                if filename.lower().endswith(VALID_EXTENSIONS) and not filename.startswith("__macosx"):
                    with z.open(filename) as f:
                        file_data = io.BytesIO(f.read())
                        res = process_image(file_data, filename, settings)
                        if "error" not in res:
                            results.append(res)
    except Exception as e:
        return [{"error": f"ZIP Error: {str(e)}"}]
    
    return results


def bytes_to_image(
    hex_string: str, 
    width: int, 
    height: int, 
    mode: str = "horizontal"
) -> Image.Image:
    """
    Convert a C-array hex string back to an image.
    Supports "horizontal" (row-major) and "vertical" (column-major) modes.
    """
    # Clean input
    clean_hex = hex_string.replace("{", "").replace("}", "").replace(";", "").replace("0x", "").replace(",", " ").replace("\n", " ")
    parts = clean_hex.split()
    
    byte_data = []
    for p in parts:
        try:
            byte_data.append(int(p, 16))
        except:
            pass

    expected_bytes = (width * height) // 8
    # Pad if missing
    if len(byte_data) < expected_bytes:
        byte_data.extend([0] * (expected_bytes - len(byte_data)))
    
    img = Image.new("1", (width, height), 0)
    
    if mode == "horizontal":
        # Row-major: 1 byte = 8 pixels horizontally
        mask = 0x80 # MSB first usually
        idx = 0
        for y in range(height):
            for x in range(0, width, 8):
                if idx >= len(byte_data): break
                byte = byte_data[idx]
                idx += 1
                for bit in range(8):
                    if x + bit < width:
                        if byte & (0x80 >> bit):
                            img.putpixel((x + bit, y), 1)
                            
    elif mode == "vertical":
        # Column-major: 1 byte = 8 pixels vertically
        idx = 0
        for x in range(width):
            for y in range(0, height, 8):
                if idx >= len(byte_data): break
                byte = byte_data[idx]
                idx += 1
                for bit in range(8):
                    if y + bit < height:
                        if byte & (1 << bit): # LSB first usually for vertical
                            img.putpixel((x, y + bit), 1)
                            
    elif mode == "page":
         # Same as vertical but organized by pages (rows of 8px height)
         # Actually loop order is different
         idx = 0
         pages = range(0, height, 8)
         for page_y in pages:
             for x in range(width):
                 if idx >= len(byte_data): break
                 byte = byte_data[idx]
                 idx += 1
                 for bit in range(8):
                     if page_y + bit < height:
                         if byte & (1 << bit):
                             img.putpixel((x, page_y + bit), 1)

    return img
