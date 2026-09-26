from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "nexvary-realestate.ico"
SIZE = 512

img = Image.new("RGBA", (SIZE, SIZE), (5, 13, 24, 255))
draw = ImageDraw.Draw(img)

# metallic/electric border
for i in range(16):
    value = 28 + i * 4
    draw.rounded_rectangle(
        (18 + i, 18 + i, SIZE - 18 - i, SIZE - 18 - i),
        radius=86 - i,
        outline=(value, min(180, value + 70), min(255, value + 120), 255),
        width=2,
    )

# building silhouette
base_y = 390
buildings = [
    (105, 215, 190, base_y),
    (205, 145, 300, base_y),
    (316, 245, 405, base_y),
]
for x1, y1, x2, y2 in buildings:
    draw.rounded_rectangle((x1, y1, x2, y2), radius=12, fill=(11, 43, 68, 255), outline=(48, 190, 255, 255), width=5)
    for y in range(y1 + 30, y2 - 25, 44):
        for x in range(x1 + 22, x2 - 18, 36):
            draw.rounded_rectangle((x, y, x + 12, y + 18), radius=3, fill=(82, 217, 255, 255))

# roof / AI circuit accent
draw.line((85, 400, 425, 400), fill=(104, 111, 255, 255), width=8)
draw.ellipse((230, 70, 282, 122), fill=(37, 194, 255, 255))
draw.line((256, 122, 256, 145), fill=(37, 194, 255, 255), width=7)
draw.line((256, 96, 170, 145), fill=(115, 103, 255, 255), width=5)
draw.line((256, 96, 342, 145), fill=(115, 103, 255, 255), width=5)

# central N
try:
    font = ImageFont.truetype("arialbd.ttf", 120)
except OSError:
    font = ImageFont.load_default()
text = "N"
bbox = draw.textbbox((0, 0), text, font=font)
tw = bbox[2] - bbox[0]
draw.text(((SIZE - tw) / 2, 235), text, font=font, fill=(240, 248, 255, 255), stroke_width=3, stroke_fill=(37, 162, 255, 255))

img.save(
    OUT,
    format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)],
)
print(OUT)
