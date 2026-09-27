from pathlib import Path
from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent / "nexvary-realestate.ico"
SIZE = 512
img = Image.new("RGBA", (SIZE, SIZE), (2, 7, 13, 255))
draw = ImageDraw.Draw(img)

# NEXVARY metallic/electric rounded-square frame.
draw.rounded_rectangle((14, 14, 498, 498), radius=108, fill=(3, 14, 25, 255), outline=(225, 238, 247, 255), width=8)
draw.rounded_rectangle((31, 31, 481, 481), radius=92, outline=(39, 201, 255, 255), width=8)
draw.rounded_rectangle((48, 48, 464, 464), radius=80, outline=(55, 106, 145, 220), width=3)

# Circuit accents.
for y in (214, 256, 298):
    draw.line((55, y, 156, y), fill=(25, 196, 255, 255), width=3)
    draw.line((356, y, 457, y), fill=(25, 196, 255, 255), width=3)
    draw.ellipse((46, y-6, 58, y+6), outline=(25, 196, 255, 255), width=2)
    draw.ellipse((454, y-6, 466, y+6), outline=(25, 196, 255, 255), width=2)

# Clear vector N and X monogram; no font dependency and no ambiguous M shape.
silver = (231, 241, 248, 255)
blue = (52, 207, 255, 255)
draw.line((116, 348, 116, 164, 246, 348, 246, 164), fill=silver, width=31, joint="curve")
draw.line((286, 164, 404, 348), fill=blue, width=31)
draw.line((404, 164, 286, 348), fill=blue, width=31)
draw.line((105, 402, 407, 402), fill=(69, 221, 255, 220), width=8)

img.save(
    OUT,
    format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print(OUT)
