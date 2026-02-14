"""
Canvas — 1-bit drawing surface for OLED/LCD displays.

Supports multiple byte-order export formats:
  - horizontal: row-major (Adafruit_GFX, SSD1306)
  - vertical: column-major (ST7565, SH1106)
  - page: 8px page blocks (U8g2, U8x8)
"""

from PIL import Image

FORMATS = ("horizontal", "vertical", "page")


class Canvas:
    """1-bit monochrome drawing surface."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.image = Image.new("1", (width, height), 0)

    def clear(self):
        self.image = Image.new("1", (self.width, self.height), 0)

    def get_image(self) -> Image.Image:
        return self.image.copy()

    def set_pixel(self, x: int, y: int, color: int = 1):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.image.putpixel((x, y), color)

    def get_pixel(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.image.getpixel((x, y))
        return 0

    def to_bytes(self, fmt: str = "horizontal") -> bytes:
        if fmt not in FORMATS:
            raise ValueError(f"Unknown format '{fmt}'. Use one of: {FORMATS}")
        converter = {
            "horizontal": self._to_horizontal,
            "vertical": self._to_vertical,
            "page": self._to_page,
        }
        return converter[fmt]()

    def _to_horizontal(self) -> bytes:
        """Row-major: 1 byte = 8 horizontal pixels, MSB = leftmost.
        Used by Adafruit_GFX drawBitmap(), SSD1306.
        """
        data = bytearray()
        pixels = self.image.load()
        for y in range(self.height):
            for x_byte in range(self.width // 8):
                byte = 0
                for bit in range(8):
                    x = x_byte * 8 + bit
                    if pixels[x, y]:
                        byte |= (0x80 >> bit)
                data.append(byte)
        return bytes(data)

    def _to_vertical(self) -> bytes:
        """Column-major: 1 byte = 8 vertical pixels, LSB = top.
        Used by ST7565, SH1106.
        """
        data = bytearray()
        pixels = self.image.load()
        for x in range(self.width):
            for y_byte in range(self.height // 8):
                byte = 0
                for bit in range(8):
                    y = y_byte * 8 + bit
                    if pixels[x, y]:
                        byte |= (1 << bit)
                data.append(byte)
        return bytes(data)

    def _to_page(self) -> bytes:
        """Page-based: 8px height pages, scanned left-to-right per page.
        Used by U8g2, U8x8.
        """
        data = bytearray()
        pixels = self.image.load()
        pages = self.height // 8
        for page in range(pages):
            for x in range(self.width):
                byte = 0
                for bit in range(8):
                    y = page * 8 + bit
                    if pixels[x, y]:
                        byte |= (1 << bit)
                data.append(byte)
        return bytes(data)

    @property
    def frame_size(self) -> int:
        return (self.width * self.height) // 8
