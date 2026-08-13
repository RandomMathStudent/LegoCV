"""Generate PNG previews for filtered LDraw minifigure hair parts."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from head_renderer import HeadRenderer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = PROJECT_ROOT / "data" / "ldraw"
HAIR_CSV = PROJECT_ROOT / "data" / "metadata" / "hair.csv"
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "images" / "hair"
CANONICAL_HAIR_COLOUR = 70  # Reddish Brown in LDConfig.ldr


def load_hair_filenames(csv_path: Path) -> list[str]:
    """Load unique LDraw filenames from the generated hair metadata."""
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or "filename" not in reader.fieldnames:
            raise ValueError(f"{csv_path} must contain a filename column")
        return list(dict.fromkeys(row["filename"] for row in reader if row.get("filename")))


def parse_args() -> argparse.Namespace:
    """Parse generation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace existing PNGs")
    return parser.parse_args()


def main() -> None:
    """Render every filtered hair piece to a same-named PNG preview."""
    args = parse_args()
    hair_files = load_hair_filenames(HAIR_CSV)
    if not hair_files:
        raise ValueError(f"No hair files found in {HAIR_CSV}")

    renderer = HeadRenderer(LIBRARY_PATH)
    failures: list[tuple[str, Exception]] = []
    rendered = skipped = 0
    for index, hair_file in enumerate(hair_files, start=1):
        output_path = OUTPUT_DIRECTORY / f"{Path(hair_file).stem}.png"
        if output_path.is_file() and not args.force:
            skipped += 1
            print(f"[{index}/{len(hair_files)}] Skipped {hair_file} (already exists)")
            continue
        try:
            result = renderer.render_part(
                hair_file, output_path, root_colour=CANONICAL_HAIR_COLOUR
            )
        except (OSError, ValueError) as error:
            failures.append((hair_file, error))
            print(f"[{index}/{len(hair_files)}] Failed {hair_file}: {error}")
            continue
        rendered += 1
        print(f"[{index}/{len(hair_files)}] Rendered {hair_file} ({result.triangle_count} triangles)")

    print(f"Rendered: {rendered}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {len(failures)}")
    print(f"Output: {OUTPUT_DIRECTORY}")
    if failures:
        raise RuntimeError(f"Could not render {len(failures)} hair files")


if __name__ == "__main__":
    main()