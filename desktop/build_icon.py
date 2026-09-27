from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "nexvary-realestate.ico"
SOURCE = ROOT / "apps" / "web" / "public" / "assets" / "nexvary-logo.png"
SIZE = 512


def fallback_icon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (5, 13, 24, 255))
    draw = ImageDraw.Draw(img)
    for i in range(16):
        value = 28 + i * 4
        draw.rounded_rectangle(
            (18 + i, 18 + i, SIZE - 18 - i, SIZE - 18 - i),
            radius=86 - i,
            outline=(value, min(180, value + 70), min(255, value + 120), 255),
            width=2,
        )
    try:
        font = ImageFont.truetype("arialbd.ttf", 120)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "N", font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((SIZE - tw) / 2, 185), "N", font=font, fill=(240, 248, 255, 255), stroke_width=3, stroke_fill=(37, 162, 255, 255))
    return img


if SOURCE.exists():
    source = Image.open(SOURCE).convert("RGBA")
    side = min(source.size)
    left = (source.width - side) // 2
    top = (source.height - side) // 2
    img = source.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
else:
    img = fallback_icon()

img.save(
    OUT,
    format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print(OUT)
