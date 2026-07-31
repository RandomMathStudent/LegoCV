"""Parse individual LDraw part files without resolving or rendering geometry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, TypeAlias

Vector3: TypeAlias = tuple[float, float, float]
Matrix3: TypeAlias = tuple[Vector3, Vector3, Vector3]
_METADATA_PREFIXES: Final[tuple[str, ...]] = ("!", "Name:", "Author:")


@dataclass(frozen=True)
class Comment:
    """A retained type-0 metadata comment."""

    text: str
    line_number: int
    key: str | None = None
    value: str | None = None


@dataclass(frozen=True)
class SubfileReference:
    """A type-1 reference to a subfile; it is not resolved by this parser."""

    colour_code: int
    position: Vector3
    transformation: Matrix3
    filename: str
    line_number: int


@dataclass(frozen=True)
class LinePrimitive:
    """A type-2 line primitive."""

    colour_code: int
    start: Vector3
    end: Vector3
    line_number: int


@dataclass(frozen=True)
class TrianglePrimitive:
    """A type-3 triangle primitive."""

    colour_code: int
    vertices: tuple[Vector3, Vector3, Vector3]
    line_number: int


@dataclass(frozen=True)
class QuadPrimitive:
    """A type-4 quadrilateral primitive."""

    colour_code: int
    vertices: tuple[Vector3, Vector3, Vector3, Vector3]
    line_number: int


@dataclass(frozen=True)
class ConditionalLine:
    """A type-5 conditional line primitive."""

    colour_code: int
    start: Vector3
    end: Vector3
    control_point_1: Vector3
    control_point_2: Vector3
    line_number: int


@dataclass
class Part:
    """The parsed contents of one LDraw part file."""

    name: str
    source_path: Path
    comments: list[Comment] = field(default_factory=list)
    subfile_references: list[SubfileReference] = field(default_factory=list)
    lines: list[LinePrimitive] = field(default_factory=list)
    triangles: list[TrianglePrimitive] = field(default_factory=list)
    quads: list[QuadPrimitive] = field(default_factory=list)
    conditional_lines: list[ConditionalLine] = field(default_factory=list)
    metadata: dict[str, list[str]] = field(default_factory=dict)


class LDrawParser:
    """Load and parse individual LDraw files from a local parts library."""

    def __init__(self, library_path: Path) -> None:
        self.library_path: Path = Path(library_path).expanduser().resolve()
        self.parts_path: Path = self.library_path / "parts"

        if not self.library_path.is_dir():
            raise FileNotFoundError(
                f"LDraw library directory does not exist: {self.library_path}"
            )
        if not self.parts_path.is_dir():
            raise FileNotFoundError(
                f"LDraw parts directory does not exist: {self.parts_path}"
            )

    def load_part(self, part_name: str) -> Part:
        """Parse one part from the library's ``parts`` directory.

        The parser only reads the requested file. In particular, type-1 subfile
        references are preserved as records and are never resolved.
        """
        return self._load_file(part_name, self.parts_path, "part_name")

    def load_head(self, head_name: str) -> Part:
        """Parse one head from the library's ``heads`` directory.

        As with :meth:`load_part`, referenced subfiles are retained but not
        resolved.
        """
        return self._load_file(head_name, self.library_path / "heads", "head_name")

    def load_file(self, relative_path: str | Path) -> Part:
        """Parse one file located anywhere within the LDraw library.

        This supports consumers, such as a renderer, which need to load files
        referenced from ``parts`` or ``p``. It still performs no recursion.
        """
        return self._load_file(relative_path, self.library_path, "relative_path")

    def _load_file(self, relative_path: str | Path, root_path: Path, argument_name: str) -> Part:
        part_path: Path = self._resolve_path(relative_path, root_path, argument_name)
        part: Part = Part(name=part_path.name, source_path=part_path)

        try:
            contents: str = part_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(f"Unable to decode LDraw part file: {part_path}") from error
        except OSError as error:
            raise OSError(f"Unable to read LDraw part file: {part_path}") from error

        for line_number, raw_line in enumerate(contents.splitlines(), start=1):
            line: str = raw_line.strip()
            if not line:
                continue
            self._parse_line(part, line, line_number)

        return part

    def _resolve_part_path(self, part_name: str) -> Path:
        return self._resolve_path(part_name, self.parts_path, "part_name")

    def _resolve_path(
        self, relative_path: str | Path, root_path: Path, argument_name: str
    ) -> Path:
        requested_path: Path = Path(relative_path)
        if requested_path.is_absolute() or ".." in requested_path.parts:
            raise ValueError(
                f"{argument_name} must be a relative path inside {root_path}: "
                f"{str(relative_path)!r}"
            )

        part_path: Path = (root_path / requested_path).resolve()
        if not part_path.is_relative_to(root_path):
            raise ValueError(f"Path escapes the allowed LDraw directory: {str(relative_path)!r}")
        if not part_path.is_file():
            raise FileNotFoundError(
                f"LDraw file {str(relative_path)!r} was not found in {root_path}"
            )
        return part_path

    def _parse_line(self, part: Part, line: str, line_number: int) -> None:
        tokens: list[str] = line.split()
        try:
            command_type: int = int(tokens[0])
        except (IndexError, ValueError) as error:
            raise self._parse_error(part, line_number, "missing or invalid command type") from error

        if command_type == 0:
            self._parse_comment(part, line[1:].strip(), line_number)
        elif command_type == 1:
            self._parse_subfile_reference(part, tokens, line_number)
        elif command_type == 2:
            self._parse_line_primitive(part, tokens, line_number)
        elif command_type == 3:
            self._parse_triangle(part, tokens, line_number)
        elif command_type == 4:
            self._parse_quad(part, tokens, line_number)
        elif command_type == 5:
            self._parse_conditional_line(part, tokens, line_number)
        else:
            raise self._parse_error(
                part, line_number, f"unsupported LDraw command type {command_type}"
            )

    def _parse_comment(self, part: Part, text: str, line_number: int) -> None:
        comment: Comment | None = self._metadata_comment(part, text, line_number)
        if comment is None:
            return

        part.comments.append(comment)
        if comment.key is not None and comment.value is not None:
            part.metadata.setdefault(comment.key, []).append(comment.value)

    def _metadata_comment(
        self, part: Part, text: str, line_number: int
    ) -> Comment | None:
        if not text:
            return None

        if text.startswith(_METADATA_PREFIXES):
            key, separator, value = text.partition(":")
            if separator:
                return Comment(
                    text=text,
                    line_number=line_number,
                    key=key.strip(),
                    value=value.strip(),
                )
            return Comment(text=text, line_number=line_number, key=key, value=text[len(key) :].strip())

        # The first free-form type-0 line is the conventional LDraw part title.
        if "Title" not in part.metadata:
            return Comment(text=text, line_number=line_number, key="Title", value=text)
        return None

    def _parse_subfile_reference(
        self, part: Part, tokens: list[str], line_number: int
    ) -> None:
        self._expect_token_count(part, tokens, 15, line_number)
        colour_code: int = self._parse_colour(part, tokens[1], line_number)
        values: list[float] = self._parse_floats(part, tokens[2:14], line_number)
        part.subfile_references.append(
            SubfileReference(
                colour_code=colour_code,
                position=self._vector(values[0:3]),
                transformation=(
                    self._vector(values[3:6]),
                    self._vector(values[6:9]),
                    self._vector(values[9:12]),
                ),
                filename=tokens[14],
                line_number=line_number,
            )
        )

    def _parse_line_primitive(self, part: Part, tokens: list[str], line_number: int) -> None:
        self._expect_token_count(part, tokens, 8, line_number)
        part.lines.append(
            LinePrimitive(
                colour_code=self._parse_colour(part, tokens[1], line_number),
                start=self._vector(self._parse_floats(part, tokens[2:5], line_number)),
                end=self._vector(self._parse_floats(part, tokens[5:8], line_number)),
                line_number=line_number,
            )
        )

    def _parse_triangle(self, part: Part, tokens: list[str], line_number: int) -> None:
        self._expect_token_count(part, tokens, 11, line_number)
        values: list[float] = self._parse_floats(part, tokens[2:11], line_number)
        part.triangles.append(
            TrianglePrimitive(
                colour_code=self._parse_colour(part, tokens[1], line_number),
                vertices=(
                    self._vector(values[0:3]),
                    self._vector(values[3:6]),
                    self._vector(values[6:9]),
                ),
                line_number=line_number,
            )
        )

    def _parse_quad(self, part: Part, tokens: list[str], line_number: int) -> None:
        self._expect_token_count(part, tokens, 14, line_number)
        values: list[float] = self._parse_floats(part, tokens[2:14], line_number)
        part.quads.append(
            QuadPrimitive(
                colour_code=self._parse_colour(part, tokens[1], line_number),
                vertices=(
                    self._vector(values[0:3]),
                    self._vector(values[3:6]),
                    self._vector(values[6:9]),
                    self._vector(values[9:12]),
                ),
                line_number=line_number,
            )
        )

    def _parse_conditional_line(self, part: Part, tokens: list[str], line_number: int) -> None:
        self._expect_token_count(part, tokens, 14, line_number)
        values: list[float] = self._parse_floats(part, tokens[2:14], line_number)
        part.conditional_lines.append(
            ConditionalLine(
                colour_code=self._parse_colour(part, tokens[1], line_number),
                start=self._vector(values[0:3]),
                end=self._vector(values[3:6]),
                control_point_1=self._vector(values[6:9]),
                control_point_2=self._vector(values[9:12]),
                line_number=line_number,
            )
        )

    @staticmethod
    def _vector(values: list[float]) -> Vector3:
        return (values[0], values[1], values[2])

    def _parse_colour(self, part: Part, token: str, line_number: int) -> int:
        try:
            return int(token, 16) if token.lower().startswith("0x") else int(token)
        except ValueError as error:
            raise self._parse_error(part, line_number, f"invalid colour code {token!r}") from error

    def _parse_floats(self, part: Part, tokens: list[str], line_number: int) -> list[float]:
        try:
            return [float(token) for token in tokens]
        except ValueError as error:
            raise self._parse_error(part, line_number, "invalid coordinate or matrix value") from error

    def _expect_token_count(
        self, part: Part, tokens: list[str], expected: int, line_number: int
    ) -> None:
        if len(tokens) != expected:
            raise self._parse_error(
                part,
                line_number,
                f"expected {expected} fields for type {tokens[0]}, found {len(tokens)}",
            )

    @staticmethod
    def _parse_error(part: Part, line_number: int, message: str) -> ValueError:
        return ValueError(f"{part.source_path}:{line_number}: {message}")


if __name__ == "__main__":
    parser = LDrawParser(Path("/home/alex/github/LegoCV/data/ldraw"))
    part = parser.load_part("3626bp01.dat")

    print(f"Part name: {part.name}")
    print(f"Number of comments: {len(part.comments)}")
    print(f"Number of subfile references: {len(part.subfile_references)}")
    print(f"Number of triangles: {len(part.triangles)}")
    print(f"Number of quads: {len(part.quads)}")
    print(f"Number of lines: {len(part.lines)}")
