#!/usr/bin/env python3
"""Download normalized LEGO minifigure-head images from a public catalog.

The default :class:`BrickOwlSource` only uses public catalog pages.  Image
sources are deliberately isolated behind ``ImageSource`` so a source can be
replaced without changing the download, validation, or image-processing flow.

Example:
    python scripts/download_head_images.py
    python scripts/download_head_images.py --limit 10 --log-level DEBUG
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol
from urllib.parse import quote_plus, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps, UnidentifiedImageError
from requests import Response
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = PROJECT_ROOT / "data" / "metadata" / "heads.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "images" / "heads"
DEFAULT_FAILURE_CSV = PROJECT_ROOT / "data" / "failed_parts.csv"
TARGET_SIZE = 512
MIN_SOURCE_SIZE = 256
MAX_ATTEMPTS = 4
REQUEST_DELAY_SECONDS = 1.25
USER_AGENT = "LegoCV image dataset builder/1.0 (public catalog research)"

LOGGER = logging.getLogger(__name__)


class DownloadError(RuntimeError):
    """Raised when an image cannot be fetched or does not meet requirements."""


class ImageSource(Protocol):
    """A public catalog capable of finding an image for a LEGO part."""

    def find_image(self, part_id: str, title: str) -> str | None:
        """Return the most suitable image URL for a part, if one is found."""


@dataclass(frozen=True)
class Failure:
    """A part that could not be processed and the context needed to retry it."""

    part_id: str
    reason: str
    url: str


def load_heads(csv_path: Path) -> list[tuple[str, str]]:
    """Load and validate unique ``(part_id, title)`` records from ``heads.csv``.

    Raises:
        ValueError: If the required columns are absent or no usable IDs exist.
    """
    frame = pd.read_csv(csv_path, dtype={"part_id": "string", "title": "string"})
    required = {"part_id", "title"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{csv_path} is missing required columns: {', '.join(sorted(missing))}")

    heads: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in frame.loc[:, ["part_id", "title"]].dropna(subset=["part_id"]).itertuples(index=False):
        part_id = str(row.part_id).strip().lower()
        title = "" if pd.isna(row.title) else str(row.title).strip()
        if part_id and part_id not in seen:
            heads.append((part_id, title))
            seen.add(part_id)
    if not heads:
        raise ValueError(f"{csv_path} contains no usable part_id values")
    return heads


def _response_or_retry(session: requests.Session, url: str, *, stream: bool = False) -> Response:
    """GET ``url`` with exponential backoff for transient HTTP/network failures."""
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = session.get(url, timeout=(10, 45), stream=stream)
            if response.status_code == 429 or 500 <= response.status_code < 600:
                response.close()
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt == MAX_ATTEMPTS - 1:
                break
            retry_after = getattr(error.response, "headers", {}).get("Retry-After") if getattr(error, "response", None) else None
            try:
                delay = max(float(retry_after), 2**attempt) if retry_after else 2**attempt
            except ValueError:
                delay = 2**attempt
            delay += random.uniform(0, 0.25)
            LOGGER.warning("Request failed (%s); retrying %s in %.1fs", error, url, delay)
            time.sleep(delay)
    raise DownloadError(f"request failed after {MAX_ATTEMPTS} attempts: {last_error}") from last_error


class BrickOwlSource:
    """Find front-facing catalog renders through Brick Owl's public pages.

    Brick Owl exposes its catalog results in the returned HTML, including part
    pages with larger rendered product images. LDraw and marketplace IDs can
    differ, so searches use both the LDraw ID and title-derived keywords.
    """

    base_url = "https://www.brickowl.com"

    def __init__(self, session: requests.Session, delay: float = REQUEST_DELAY_SECONDS) -> None:
        self.session = session
        self.delay = delay

    def _get_html(self, url: str) -> BeautifulSoup:
        response = _response_or_retry(self.session, url)
        try:
            return BeautifulSoup(response.text, "html.parser")
        finally:
            response.close()
            time.sleep(self.delay)

    def _search_urls(self, part_id: str, title: str) -> Iterable[str]:
        # The title query is important: LDraw pattern IDs and marketplace IDs
        # are not guaranteed to be identical.
        title_query = re.sub(r"\s*\([^)]*\)", "", title).replace("Pattern", "").strip()
        queries = [part_id, title_query]
        seen: set[str] = set()
        for query in queries:
            if not query:
                continue
            search_url = f"{self.base_url}/search/catalog?query={quote_plus(query)}"
            soup = self._get_html(search_url)
            for anchor in soup.select('a.category-item-image[href^="/catalog/"]'):
                href = anchor.get("href")
                if href:
                    url = urljoin(self.base_url, href)
                    if url not in seen:
                        seen.add(url)
                        yield url

    @staticmethod
    def _image_urls(soup: BeautifulSoup, page_url: str) -> Iterable[str]:
        # Prefer Brick Owl's largest cache variant. It is a product render,
        # rather than a seller listing photograph or UI image.
        text = str(soup).replace("\\/", "/")
        for match in re.finditer(r'https?://[^"\'\\s]+/image_cache/(?:larger|large)/[^"\'\\s]+', text):
            yield urljoin(page_url, match.group(0))
        for meta in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
            content = meta.get("content")
            if content and "image_cache" in content:
                yield urljoin(page_url, content)

    def find_image(self, part_id: str, title: str) -> str | None:
        """Return the first deduplicated high-resolution product render URL."""
        seen: set[str] = set()
        for detail_url in self._search_urls(part_id, title):
            soup = self._get_html(detail_url)
            for image_url in self._image_urls(soup, detail_url):
                if image_url not in seen:
                    seen.add(image_url)
                    return image_url
        return None


def find_image(source: ImageSource, part_id: str, title: str) -> str | None:
    """Find the best source image, keeping source selection swappable."""
    return source.find_image(part_id, title)


def download_image(session: requests.Session, url: str) -> Image.Image:
    """Download, decode, and validate an image from ``url``.

    Images below 256 pixels on either side are rejected rather than upscaled,
    ensuring the dataset does not silently include low-resolution thumbnails.
    """
    response = _response_or_retry(session, url, stream=True)
    try:
        content_type = response.headers.get("Content-Type", "").lower()
        if "image" not in content_type:
            raise DownloadError(f"expected image content, received {content_type or 'unknown content type'}")
        payload = response.content
    finally:
        response.close()
        time.sleep(REQUEST_DELAY_SECONDS)

    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            if min(image.size) < MIN_SOURCE_SIZE:
                raise DownloadError(f"source image is too small: {image.width}x{image.height}")
            return image.copy()
    except UnidentifiedImageError as error:
        raise DownloadError("response is not a decodable image") from error


def save_image(image: Image.Image, destination: Path) -> None:
    """Save an image as a transparent, square 512×512 PNG.

    Larger images are reduced preserving aspect ratio; smaller qualifying images
    retain their native detail and are centered on a transparent canvas.
    """
    normalized = ImageOps.exif_transpose(image).convert("RGBA")
    normalized.thumbnail((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    offset = ((TARGET_SIZE - normalized.width) // 2, (TARGET_SIZE - normalized.height) // 2)
    canvas.alpha_composite(normalized, offset)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG", optimize=True)


def _write_failures(path: Path, failures: list[Failure]) -> None:
    """Write failures in a stable, machine-readable format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["part_id", "reason", "url"])
        writer.writeheader()
        writer.writerows(failure.__dict__ for failure in failures)


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="input heads.csv path")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="destination directory")
    parser.add_argument("--failed-csv", type=Path, default=DEFAULT_FAILURE_CSV, help="failure report path")
    parser.add_argument("--limit", type=int, help="process only the first N records")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def main() -> int:
    """Download all missing head images and return a process exit status."""
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s")
    try:
        heads = load_heads(args.csv)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        LOGGER.error("Could not load head metadata: %s", error)
        return 2
    if args.limit is not None:
        heads = heads[: max(args.limit, 0)]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8"})
    source = BrickOwlSource(session)
    downloaded = skipped = 0
    failures: list[Failure] = []

    try:
        for part_id, title in tqdm(heads, desc="Head images", unit="head"):
            destination = args.output_dir / f"{part_id}.png"
            if destination.is_file():
                skipped += 1
                LOGGER.info("skipped %s (already exists)", part_id)
                continue
            image_url = ""
            try:
                image_url = find_image(source, part_id, title) or ""
                if not image_url:
                    raise DownloadError("no matching public catalog image found")
                image = download_image(session, image_url)
                save_image(image, destination)
                downloaded += 1
                LOGGER.info("downloaded %s from %s", part_id, image_url)
            except (DownloadError, OSError, requests.RequestException) as error:
                failures.append(Failure(part_id, str(error), image_url))
                LOGGER.error("failed %s: %s", part_id, error)
    finally:
        session.close()

    _write_failures(args.failed_csv, failures)
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())