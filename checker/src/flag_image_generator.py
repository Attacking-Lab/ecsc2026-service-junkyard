import os
import random
import string
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFont, ImageDraw

type Color = tuple[int, int, int]

BLACK: Color = (0, 0, 0)
WHITE: Color = (255, 255, 255)

# chars inside the braces
FLAG_CHARS = string.ascii_letters + string.digits + '_-'
FLAG_CHARS_ALL = FLAG_CHARS + "{}"
CHAR_WIDTH = 25


@dataclass
class Dimensions:
    x: int
    y: int
    width: int
    height: int

    def intersect(self, crop_area: Dimensions) -> Dimensions:
        result = Dimensions(self.x - crop_area.x, self.y - crop_area.y, self.width, self.height)
        if result.x < 0:
            result.width += result.x
            result.x = 0
        if result.y < 0:
            result.height += result.y
            result.y = 0
        return result

    def __str__(self) -> str:
        return f"(x={self.x}, y={self.y}, w={self.width}, h={self.height})"


def rnd_flag() -> str:
    return 'ECSC{' + ''.join(random.choice(FLAG_CHARS) for _ in range(32)) + '}'
    # return 'ECSC{hardcoded}'


def generate_char_bitmaps() -> None:
    if not os.path.exists("font-bitmaps"):
        os.mkdir("font-bitmaps")
    # flag chars + {}
    all_flag_chars = FLAG_CHARS + "{}"
    for c in all_flag_chars:
        image, _ = gen_string_image(c, randomize_colors=False)
        with open(f"font-bitmaps/char_{c}.bmp","wb") as f:
            f.write(image_to_bitmap(image))


def colorpair(rnd: random.Random) -> tuple[Color, Color]:
    while True:
        r = rnd.randint(0, 255)
        g = rnd.randint(0, 255)
        b = rnd.randint(0, 255)
        c1 = (r, g, b)
        c2 = (255 - r, 255 - g, 255 - b)
        d = abs(c1[0] - c1[1]) + abs(c1[1] - c1[2]) + abs(c1[0] - c1[2])
        if d > 10:
            return c1, c2


def gen_string_image(text: str, /, seed: int = 0, randomize_colors: bool = True) -> tuple[Image.Image, Dimensions]:
    """Return the image with the text and where it is on the image"""
    if any(c not in FLAG_CHARS_ALL for c in text):
        raise ValueError(f"Text {text!r} contains invalid characters, you won't be able to OCR them!")

    rnd = random.Random(seed or None)
    font = Path(__file__).parent.parent / "res" / "Inconsolata-Regular.ttf"
    img = Image.new('RGBA', (CHAR_WIDTH * len(text), 50), BLACK)
    fnt = ImageFont.truetype(font, 40)
    d = ImageDraw.Draw(img)
    for i, c in enumerate(text):
        if randomize_colors:
            c1, c2 = colorpair(rnd)
        else:
            c1 = BLACK
            c2 = WHITE
        d.rectangle((i * CHAR_WIDTH, 0, (i + 1) * CHAR_WIDTH, 50), fill=c1)
        d.text((i * CHAR_WIDTH, 5), c, font=fnt, fill=c2, stroke_width=1.2)
    return img, Dimensions(0, 0, CHAR_WIDTH * len(text), 50)


def image_to_bitmap(img: Image.Image) -> bytes:
    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    img_bytes = img.tobytes()
    data = b""
    # 0x424d header
    data += b"\x42\x4d"
    # file size in bytes, u32
    data += struct.pack("<I", len(img_bytes) + 54)
    # something that is always 0
    data += struct.pack("<H", 0)
    # something else that is always 0
    data += struct.pack("<H", 0)
    # offset of actual data
    data += struct.pack("<I", 54)
    # second header size
    data += struct.pack("<I", 40)
    # image width
    data += struct.pack("<I", img.width)
    # image height
    data += struct.pack("<I", img.height)
    # always 1
    data += struct.pack("<H", 1)
    # bits per pixel, 32
    data += struct.pack("<H", 32)
    # compression, always 3
    # is this actually required to be 3?
    # data += struct.pack("<I", 3)
    data += struct.pack("<I", 0)  # TODO

    # image size
    data += struct.pack("<I", len(img_bytes))
    # useless
    data += struct.pack("<I", 0)
    # more useless
    data += struct.pack("<I", 0)
    # unused
    data += struct.pack("<I", 0)
    # unused
    data += struct.pack("<I", 0)
    # data
    for i in range(0, len(img_bytes), 4):
        red, green, blue, alpha = img_bytes[i:i + 4]
        # offset 0 becomes offset 2, and vice versa
        data += blue.to_bytes(1) + green.to_bytes(1) + red.to_bytes(1) + alpha.to_bytes(1)

    return data

if __name__ == "__main__":
    generate_char_bitmaps()

