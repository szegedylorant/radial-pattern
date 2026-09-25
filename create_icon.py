from PIL import Image, ImageDraw
import math


SIZE = 24

img = Image.new(
    "RGBA",
    (SIZE, SIZE),
    (0, 0, 0, 0),
)

draw = ImageDraw.Draw(img)

cx = 11.5
cy = 11.5

# Nine radial lines spread across a 120° fan.
angles = [
        -240,
#        -225,
        -210,
#        -195,
        -180,
#        -165,
        -150,
#        -135,
        -120,
#        -105,
        -90,
#        -75,
    -60,
#    -45,
    -30,
#    -15,
    0,
#    15,
    30,
#    45,
    60,
]

# Leave a gap around the center so the lines
# remain visually distinct.
inner_radius = 5.0
outer_radius = 10.0

for angle in angles:

    a = math.radians(angle)

    x1 = cx + inner_radius * math.cos(a)
    y1 = cy + inner_radius * math.sin(a)

    x2 = cx + outer_radius * math.cos(a)
    y2 = cy + outer_radius * math.sin(a)

    draw.line(
        (x1, y1, x2, y2),
        fill=(45, 45, 45, 255),
        width=1,
    )

# Center point
center_radius = 2.0

draw.ellipse(
    (
        cx - center_radius,
        cy - center_radius,
        cx + center_radius,
        cy + center_radius,
    ),
    fill=(45, 45, 45, 255),
)

img.save("icon.png")

