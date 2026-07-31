"""Generate PNG previews for every LDraw head in the local library."""

from __future__ import annotations

from pathlib import Path

from head_renderer import HeadRenderer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LIBRARY_PATH = PROJECT_ROOT / "data" / "ldraw"
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "images" / "heads"


def main() -> None:
    """Render each head file to a same-named PNG preview."""
    head_files = sorted((LIBRARY_PATH / "heads").glob("*.dat"))
    if not head_files:
        raise FileNotFoundError(f"No head files found in {LIBRARY_PATH / 'heads'}")

    renderer = HeadRenderer(LIBRARY_PATH)
    failures: list[tuple[str, Exception]] = []
    for index, head_file in enumerate(head_files, start=1):
        output_path = OUTPUT_DIRECTORY / f"{head_file.stem}.png"
        try:
            result = renderer.render(head_file.name, output_path)
        except (OSError, ValueError) as error:
            failures.append((head_file.name, error))
            print(f"[{index}/{len(head_files)}] Failed {head_file.name}: {error}")
            continue
        print(
            f"[{index}/{len(head_files)}] Rendered {head_file.name} "
            f"({result.triangle_count} triangles)"
        )

    print(
        f"Generated {len(head_files) - len(failures)} of {len(head_files)} "
        f"head images in {OUTPUT_DIRECTORY}"
    )
    if failures:
        raise RuntimeError(f"Could not render {len(failures)} head files")


if __name__ == "__main__":
    main()