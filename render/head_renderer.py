"""Render LDraw minifigure heads to a front-facing PNG image."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, TypeAlias

from PIL import Image, ImageDraw

if __package__:
    from .parser import LDrawParser, Matrix3, Part, Vector3
else:
    from parser import LDrawParser, Matrix3, Part, Vector3

Colour: TypeAlias = tuple[int, int, int]
Triangle: TypeAlias = tuple[Vector3, Vector3, Vector3, Colour]
_IDENTITY: Final[Matrix3] = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_DEFAULT_COLOUR: Final[Colour] = (255, 205, 0)
_COLOUR_DEFINITION: Final[re.Pattern[str]] = re.compile(
    r"^0\s+!COLOUR\s+.+?\s+CODE\s+(\d+)\s+VALUE\s+#([0-9A-Fa-f]{6})\b"
)


@dataclass(frozen=True)
class RenderResult:
    """Details of a completed head render."""

    output_path: Path
    triangle_count: int


def load_colour_palette(config_path: Path) -> dict[int, Colour]:
    """Load LDraw material colours defined by ``LDConfig.ldr``."""
    palette: dict[int, Colour] = {}
    for line in config_path.read_text(encoding="utf-8-sig").splitlines():
        match = _COLOUR_DEFINITION.match(line)
        if match is None:
            continue
        code = int(match.group(1))
        value = match.group(2)
        palette[code] = (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))
    if not palette:
        raise ValueError(f"No LDraw colour definitions found in {config_path}")
    return palette


class HeadRenderer:
    """Resolve LDraw head geometry and render a front-facing PNG preview."""

    def __init__(self, library_path: Path) -> None:
        self.library_path = Path(library_path).expanduser().resolve()
        self.parser = LDrawParser(self.library_path)
        self.colours = load_colour_palette(self.library_path / "LDConfig.ldr")

    def render(
        self, head_name: str, output_path: Path, image_size: int = 512, root_colour: int = 14
    ) -> RenderResult:
        """Render a head from ``heads`` to ``output_path``.

        Type-1 references are resolved for rendering only. The parser itself
        remains a non-recursive, data-only component.
        """
        if image_size < 32:
            raise ValueError("image_size must be at least 32 pixels")

        head = self.parser.load_head(head_name)
        triangles = self._collect_triangles(head, _IDENTITY, (0.0, 0.0, 0.0), root_colour, set())
        if not triangles:
            raise ValueError(f"No renderable geometry found in head {head_name!r}")

        image = self._rasterize(triangles, image_size)
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG")
        return RenderResult(output_path=destination, triangle_count=len(triangles))

    def render_part(
        self, part_name: str, output_path: Path, image_size: int = 512, root_colour: int = 14
    ) -> RenderResult:
        """Render a standard LDraw part from the ``parts`` directory."""
        if image_size < 32:
            raise ValueError("image_size must be at least 32 pixels")

        part = self.parser.load_part(part_name)
        triangles = self._collect_triangles(part, _IDENTITY, (0.0, 0.0, 0.0), root_colour, set())
        if not triangles:
            raise ValueError(f"No renderable geometry found in part {part_name!r}")

        image = self._rasterize(triangles, image_size)
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG")
        return RenderResult(output_path=destination, triangle_count=len(triangles))

    def render_head_with_hair(
        self,
        head_name: str,
        hair_name: str,
        output_path: Path,
        image_size: int = 512,
        head_colour: int = 14,
        hair_colour: int = 70,
    ) -> RenderResult:
        """Render a minifigure head and hair part on their shared LDraw origin.

        Standard minifigure heads and hairpieces are authored to attach at the
        origin, so no placement translation is needed for this two-part assembly.
        """
        if image_size < 32:
            raise ValueError("image_size must be at least 32 pixels")

        head = self._load_head_or_part(head_name)
        hair = self.parser.load_part(hair_name)
        triangles = self._collect_triangles(head, _IDENTITY, (0.0, 0.0, 0.0), head_colour, set())
        triangles.extend(
            self._collect_triangles(hair, _IDENTITY, (0.0, 0.0, 0.0), hair_colour, set())
        )
        if not triangles:
            raise ValueError("No renderable geometry found in the head and hair assembly")

        image = self._rasterize(triangles, image_size)
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG")
        return RenderResult(output_path=destination, triangle_count=len(triangles))

    def _load_head_or_part(self, head_name: str) -> Part:
        """Load a head from the curated head library or the standard parts library."""
        head_path = self.library_path / "heads" / head_name
        if head_path.is_file():
            return self.parser.load_head(head_name)
        return self.parser.load_part(head_name)

    def _collect_triangles(
        self,
        part: Part,
        matrix: Matrix3,
        position: Vector3,
        inherited_colour: int,
        active_paths: set[Path],
    ) -> list[Triangle]:
        if part.source_path in active_paths:
            return []

        active_paths = active_paths | {part.source_path}
        triangles: list[Triangle] = []
        for primitive in part.triangles:
            triangles.append(
                (
                    self._transform_point(matrix, position, primitive.vertices[0]),
                    self._transform_point(matrix, position, primitive.vertices[1]),
                    self._transform_point(matrix, position, primitive.vertices[2]),
                    self._colour(primitive.colour_code, inherited_colour),
                )
            )
        for primitive in part.quads:
            vertices = tuple(
                self._transform_point(matrix, position, vertex) for vertex in primitive.vertices
            )
            colour = self._colour(primitive.colour_code, inherited_colour)
            triangles.extend(
                [
                    (vertices[0], vertices[1], vertices[2], colour),
                    (vertices[0], vertices[2], vertices[3], colour),
                ]
            )

        for reference in part.subfile_references:
            reference_path = self._resolve_reference(part.source_path, reference.filename)
            if reference_path is None:
                continue
            child = self.parser.load_file(reference_path.relative_to(self.library_path))
            child_matrix = self._multiply_matrices(matrix, reference.transformation)
            child_position = self._transform_point(matrix, position, reference.position)
            child_colour = inherited_colour if reference.colour_code == 16 else reference.colour_code
            triangles.extend(
                self._collect_triangles(
                    child, child_matrix, child_position, child_colour, active_paths
                )
            )
        return triangles

    def _resolve_reference(self, source_path: Path, filename: str) -> Path | None:
        name = Path(filename.replace("\\", "/"))
        candidates = (
            source_path.parent / name,
            self.library_path / name,
            self.library_path / "parts" / name,
            self.library_path / "p" / name,
        )
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.is_relative_to(self.library_path) and resolved.is_file():
                return resolved
        return None

    @staticmethod
    def _multiply_matrices(left: Matrix3, right: Matrix3) -> Matrix3:
        return tuple(
            tuple(sum(left[row][index] * right[index][column] for index in range(3)) for column in range(3))
            for row in range(3)
        )  # type: ignore[return-value]

    @staticmethod
    def _transform_point(matrix: Matrix3, position: Vector3, point: Vector3) -> Vector3:
        return (
            position[0] + sum(matrix[0][index] * point[index] for index in range(3)),
            position[1] + sum(matrix[1][index] * point[index] for index in range(3)),
            position[2] + sum(matrix[2][index] * point[index] for index in range(3)),
        )

    def _colour(self, colour_code: int, inherited_colour: int) -> Colour:
        code = inherited_colour if colour_code == 16 else colour_code
        if code & 0x02000000:
            return ((code >> 16) & 0xFF, (code >> 8) & 0xFF, code & 0xFF)
        return self.colours.get(code, _DEFAULT_COLOUR)

    @staticmethod
    def _rasterize(triangles: list[Triangle], image_size: int) -> Image.Image:
        vertices = [vertex for triangle in triangles for vertex in triangle[:3]]
        min_x, max_x = min(vertex[0] for vertex in vertices), max(vertex[0] for vertex in vertices)
        min_y, max_y = min(vertex[1] for vertex in vertices), max(vertex[1] for vertex in vertices)
        span = max(max_x - min_x, max_y - min_y, 1.0)
        padding = image_size * 0.08
        scale = (image_size - 2 * padding) / span

        image = Image.new("RGB", (image_size, image_size), (242, 244, 247))
        canvas = ImageDraw.Draw(image)
        for first, second, third, colour in sorted(
            triangles, key=lambda triangle: sum(vertex[2] for vertex in triangle[:3]) / 3, reverse=True
        ):
            polygon = [
                (padding + (vertex[0] - min_x) * scale, padding + (vertex[1] - min_y) * scale)
                for vertex in (first, second, third)
            ]
            canvas.polygon(polygon, fill=HeadRenderer._shade(colour, first, second, third))
        return image

    @staticmethod
    def _shade(colour: Colour, first: Vector3, second: Vector3, third: Vector3) -> Colour:
        """Apply neutral orthographic face shading without altering geometry."""
        first_edge = tuple(second[index] - first[index] for index in range(3))
        second_edge = tuple(third[index] - first[index] for index in range(3))
        normal = (
            first_edge[1] * second_edge[2] - first_edge[2] * second_edge[1],
            first_edge[2] * second_edge[0] - first_edge[0] * second_edge[2],
            first_edge[0] * second_edge[1] - first_edge[1] * second_edge[0],
        )
        magnitude = sum(component * component for component in normal) ** 0.5
        if magnitude == 0:
            return colour

        # The image projects along the Z axis. Using |Nz| keeps shading stable
        # for both BFC winding directions while distinguishing front and side faces.
        brightness = 0.42 + 0.58 * abs(normal[2]) / magnitude
        return tuple(round(component * brightness) for component in colour)  # type: ignore[return-value]


if __name__ == "__main__":
    result = HeadRenderer(Path("/home/alex/github/LegoCV/data/ldraw")).render(
        "3626bp3e.dat", Path("/tmp/3626bp3e.png")
    )
    print(f"Rendered {result.triangle_count} triangles to {result.output_path}")