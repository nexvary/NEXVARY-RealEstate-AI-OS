from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "nexvary-realestate.ico"
SIZE = 512
img = Image.new("RGBA", (SIZE, SIZE), (1, 4, 9, 255))
draw = ImageDraw.Draw(img)

# NEXVARY-style circular metallic/electric frame.
for width, inset, color in [
    (7, 14, (215, 231, 242, 255)),
    (6, 23, (29, 187, 255, 255)),
    (2, 42, (75, 132, 176, 220)),
]:
    draw.ellipse((inset, inset, SIZE-inset, SIZE-inset), outline=color, width=width)

# Security lock.
draw.arc((225, 68, 287, 130), start=180, end=360, fill=(75, 220, 255, 255), width=8)
draw.rounded_rectangle((218, 103, 294, 167), radius=9, fill=(20, 170, 245, 255), outline=(110, 230, 255, 255), width=3)
draw.ellipse((250, 126, 262, 138), fill=(1, 12, 21, 255))
draw.rectangle((254, 136, 258, 151), fill=(1, 12, 21, 255))

# Circuit accents.
for y in (214, 256, 298):
    draw.line((55, y, 156, y), fill=(25, 196, 255, 255), width=3)
    draw.line((356, y, 457, y), fill=(25, 196, 255, 255), width=3)
    draw.ellipse((46, y-6, 58, y+6), outline=(25, 196, 255, 255), width=2)
    draw.ellipse((454, y-6, 466, y+6), outline=(25, 196, 255, 255), width=2)

# Metallic NX monogram.
try:
    mono = ImageFont.truetype("arialbd.ttf", 176)
except OSError:
    mono = ImageFont.load_default()
for offset, color in [(5, (22, 111, 168, 255)), (0, (229, 239, 247, 255))]:
    bbox = draw.textbbox((0, 0), "NX", font=mono)
    tw = bbox[2] - bbox[0]
    draw.text(((SIZE - tw) / 2 + offset, 165 + offset), "NX", font=mono, fill=color)

# Electric diagonal accent.
draw.polygon([(271, 203), (309, 165), (326, 180), (289, 219)], fill=(24, 182, 255, 255))

img.save(
    OUT,
    format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print(OUT)
