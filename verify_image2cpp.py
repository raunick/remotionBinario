
import os
import sys
from PIL import Image
import io

# Add project root to path
sys.path.insert(0, os.getcwd())

from oled_animator.image_converter import process_image, bytes_to_image
from oled_animator.dither import apply_dithering

def test_dithering():
    print("Testing Dithering...")
    img = Image.new('L', (32, 32), 128) # 50% gray
    
    methods = ['floyd-steinberg', 'atkinson', 'ordered', 'stucki', 'simple']
    for method in methods:
        try:
            result = apply_dithering(img, method)
            assert result.size == (32, 32)
            assert result.mode == '1'
            print(f"  ✅ Method '{method}' OK")
        except Exception as e:
            print(f"  ❌ Method '{method}' FAILED: {e}")

def test_image_process():
    print("\nTesting Image Processing...")
    # Create valid dummy image
    img = Image.new('RGB', (100, 100), 'red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    settings = {
        "width": 128,
        "height": 64,
        "dither": "floyd-steinberg",
        "scale_mode": "fit"
    }
    
    result = process_image(buf, "test.png", settings)
    
    if "error" in result:
        print(f"  ❌ Process failed: {result['error']}")
    else:
        print(f"  ✅ Process OK. Size: {result['width']}x{result['height']}")
        print(f"  ✅ Canvas bytes len: {len(result['canvas'].to_bytes())}")

def test_reverse():
    print("\nTesting Reverse Conversion...")
    # 8x8 checkerboard pattern
    # 10101010 = 0xAA
    hex_str = "0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55" 
    
    img = bytes_to_image(hex_str, 8, 8, 'horizontal')
    if img.size == (8, 8):
        print("  ✅ Reverse Horizontal OK")
    else:
        print("  ❌ Reverse Horizontal FAILED")

if __name__ == "__main__":
    test_dithering()
    test_image_process()
    test_reverse()
