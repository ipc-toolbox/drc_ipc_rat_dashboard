# make_icons.py  (run once: python make_icons.py)
from PIL import Image, ImageDraw, ImageFont
import os

def make_icon(size, path):
    img  = Image.new("RGB", (size, size), color="#0d6efd")
    draw = ImageDraw.Draw(img)

    # Try to load a bold system font; fall back to Pillow's built-in
    font_size = size // 5
    font = None
    for candidate in [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        try:
            font = ImageFont.truetype(candidate, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    for i, line in enumerate(["IPC", "RAT"]):
        bbox  = draw.textbbox((0, 0), line, font=font)
        w, h  = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x     = (size - w) // 2
        y     = size // 3 + i * (h + size // 16) - h
        draw.text((x, y), line, fill="white", font=font)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"✅  {path}")

make_icon(192, "public/icon-192.png")
make_icon(512, "public/icon-512.png")