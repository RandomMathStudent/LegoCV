from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEAD_DIR = PROJECT_ROOT / "data" / "images" / "heads"
OUTPUT = PROJECT_ROOT / "data" / "component_regions_debug.png"

# Normalised coordinates: x1, y1, x2, y2
#
# These are deliberately approximate initial regions.
# We will inspect the result and adjust them.
REGIONS = {
    "eyebrows":    (0.24, 0.23, 0.76, 0.35),

    "left_eye":    (0.25, 0.32, 0.48, 0.47),
    "right_eye":   (0.52, 0.32, 0.75, 0.47),

    "nose":        (0.38, 0.40, 0.62, 0.56),

    "mouth":       (0.30, 0.51, 0.70, 0.65),

    "left_cheek":  (0.14, 0.34, 0.43, 0.67),
    "right_cheek": (0.57, 0.34, 0.86, 0.67),

    "facial_hair": (0.24, 0.43, 0.76, 0.70),
}

# Pick representative heads spread throughout the dataset.
images = sorted(HEAD_DIR.glob("*.png"))

if not images:
    raise RuntimeError(f"No head images found in {HEAD_DIR}")

indices = [
    0,
    len(images) // 8,
    2 * len(images) // 8,
    3 * len(images) // 8,
    4 * len(images) // 8,
    5 * len(images) // 8,
    6 * len(images) // 8,
    7 * len(images) // 8,
]

selected = [images[i] for i in indices]

thumb_size = 512
label_height = 30
columns = 4
rows = 2

sheet = Image.new(
    "RGB",
    (columns * thumb_size, rows * (thumb_size + label_height)),
    "white",
)

draw = ImageDraw.Draw(sheet)

for index, path in enumerate(selected):
    with Image.open(path) as source:
        image = source.convert("RGB").resize((thumb_size, thumb_size))

    x_offset = (index % columns) * thumb_size
    y_offset = (index // columns) * (thumb_size + label_height)

    sheet.paste(image, (x_offset, y_offset))

    for name, (x1, y1, x2, y2) in REGIONS.items():
        x_start = x_offset + int(x1 * thumb_size)
        y_start = y_offset + int(y1 * thumb_size)
        x_end = x_offset + int(x2 * thumb_size)
        y_end = y_offset + int(y2 * thumb_size)

        draw.rectangle(
            (x_start, y_start, x_end, y_end),
            outline="red",
            width=2,
        )

        draw.text(
            (x_start + 3, y_start + 3),
            name,
            fill="red",
        )

    draw.rectangle(
        (
            x_offset,
            y_offset + thumb_size,
            x_offset + thumb_size,
            y_offset + thumb_size + label_height,
        ),
        fill="white",
    )

    draw.text(
        (x_offset + 5, y_offset + thumb_size + 5),
        path.stem,
        fill="black",
    )

sheet.save(OUTPUT)

print(f"Saved diagnostic image to: {OUTPUT}")