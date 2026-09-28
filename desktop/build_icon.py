from pathlib import Path
from PIL import Image, ImageDraw


OUT = Path(__file__).resolve().parent / "nexvary-realestate.ico"
SIZE = 512
img = Image.new("RGBA", (SIZE, SIZE), (2, 7, 13, 255))
draw = ImageDraw.Draw(img)

# Neutral metallic/electric rounded-square frame.
draw.rounded_rectangle((14, 14, 498, 498), radius=108, fill=(3, 14, 25, 255), outline=(225, 238, 247, 255), width=8)
draw.rounded_rectangle((31, 31, 481, 481), radius=92, outline=(39, 201, 255, 255), width=8)
draw.rounded_rectangle((48, 48, 464, 464), radius=80, outline=(55, 106, 145, 220), width=3)

# Neutral property mark with no company letters.
silver = (231, 241, 248, 255)
blue = (52, 207, 255, 255)
draw.line((100, 225, 256, 105, 412, 225), fill=blue, width=28, joint="curve")
draw.line((135, 215, 135, 390, 377, 390, 377, 215), fill=silver, width=25, joint="curve")
draw.line((215, 390, 215, 285, 297, 285, 297, 390), fill=silver, width=23, joint="curve")
draw.line((95, 425, 417, 425), fill=(69, 221, 255, 220), width=8)

img.save(
    OUT,
    format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print(OUT)
