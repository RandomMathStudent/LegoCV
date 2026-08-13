"""Render one canonical minifigure head-and-hair assembly preview.

Example:
    python render/generate_minifigure_preview.py 3626bp01 10048
"""

from __future__ import annotations

import argparse
from pathlib import Path

from head_renderer import HeadRenderer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = PROJECT_ROOT / "data" / "ldraw"
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "images" / "minifigures"
DEFAULT_HEAD_COLOUR = 14
DEFAULT_HAIR_COLOUR = 70


def part_filename(part_id: str) -> str:
    """Normalize a part ID or filename to an LDraw ``.dat`` filename."""
    return part_id if part_id.lower().endswith(".dat") else f"{part_id}.dat"


def parse_args() -> argparse.Namespace:
    """Parse the requested head, hair, colour, and output settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("head", help="head part ID or .dat filename")
    parser.add_argument("hair", help="hair part ID or .dat filename")
    parser.add_argument("--head-colour", type=int, default=DEFAULT_HEAD_COLOUR)
    parser.add_argument("--hair-colour", type=int, default=DEFAULT_HAIR_COLOUR)
    parser.add_argument("--output", type=Path, help="optional PNG destination")
    return parser.parse_args()


def main() -> None:
    """Generate the requested composed minifigure preview."""
    args = parse_args()
    head_name = part_filename(args.head)
    hair_name = part_filename(args.hair)
    output_path = args.output or OUTPUT_DIRECTORY / f"{Path(head_name).stem}_{Path(hair_name).stem}.png"

    result = HeadRenderer(LIBRARY_PATH).render_head_with_hair(
        head_name,
        hair_name,
        output_path,
        head_colour=args.head_colour,
        hair_colour=args.hair_colour,
    )
    print(f"Rendered {head_name} + {hair_name} ({result.triangle_count} triangles)")
    print(f"Output: {result.output_path}")


if __name__ == "__main__":
    main()