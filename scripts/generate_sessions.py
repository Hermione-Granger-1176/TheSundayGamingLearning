#!/usr/bin/env python3
"""
Generate Sessions Data

This module scans the session folders and generates a JavaScript data file
(js/data.js) containing the session information. This file is used by the
index.html website to display content without a backend server.

Each session folder can contain:
    - video.txt: Required. YouTube video URL.
    - name.txt: Optional. Session name. If it starts with NNN-, the prefix
      should match the session_NNN folder number.
    - urls.txt: Optional. Additional resource links.
        Format: Title: URL
        If the title contains a ":", use: Title | URL or Title<TAB>URL.
    - Files.zip: Optional. Downloadable materials.

Usage:
    python scripts/generate_sessions.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Iterator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration constants
SESSIONS_DIR = Path("sessions")
JS_OUTPUT_FILE = Path("js/data.js")
DEFAULT_GITHUB_REPO = "Hermione-Granger-1176/TheSundayGamingLearning"

# File name constants
VIDEO_FILE = "video.txt"
NAME_FILE = "name.txt"
URLS_FILE = "urls.txt"
ZIP_FILE = "Files.zip"


class ResourceLink(TypedDict):
    title: str
    url: str


class SessionData(TypedDict):
    id: int
    title: str
    video_url: str
    download_url: str | None
    resources: list[ResourceLink]


def generate_site() -> None:
    """
    Generate the data.js file from session folders.
    """
    if not SESSIONS_DIR.exists():
        logger.error("Sessions directory not found: %s", SESSIONS_DIR)
        raise FileNotFoundError(f"Sessions directory not found: {SESSIONS_DIR}")

    logger.info("Starting data generation from %s", SESSIONS_DIR)

    # Get sorted session folders that contain video files
    session_folders = sorted(
        (
            folder
            for folder in SESSIONS_DIR.iterdir()
            if folder.is_dir() and (folder / VIDEO_FILE).exists()
        ),
        key=_session_sort_key,
    )

    logger.info("Found %d valid session folders", len(session_folders))

    # Process all folders
    sessions_data: list[SessionData] = []
    for folder in session_folders:
        try:
            sessions_data.append(_extract_session_data(folder))
        except ValueError as e:
            logger.warning("Skipping folder %s: %s", folder, e)

    _ensure_unique_ids(sessions_data)

    # Ensure js directory exists
    JS_OUTPUT_FILE.parent.mkdir(exist_ok=True)

    # Generate JS content
    js_content = f"window.SESSIONS_DATA = {json.dumps(sessions_data, indent=2, ensure_ascii=False)};"
    JS_OUTPUT_FILE.write_text(js_content, encoding="utf-8")

    logger.info("Successfully generated %s", JS_OUTPUT_FILE)


def _ensure_unique_ids(sessions_data: list[SessionData]) -> None:
    seen: set[int] = set()
    duplicates: set[int] = set()
    for session in sessions_data:
        session_id = session["id"]
        if session_id in seen:
            duplicates.add(session_id)
        seen.add(session_id)
    if duplicates:
        raise ValueError(f"Duplicate session IDs found: {sorted(duplicates)}")


def _get_folder_id(folder: Path) -> int | None:
    if match := re.match(r"^session_(\d+)$", folder.name):
        return int(match.group(1))
    return None


def _parse_name_prefix(name: str) -> int | None:
    if match := re.match(r"^(\d+)", name):
        return int(match.group(1))
    return None


def _session_sort_key(folder: Path) -> int:
    """Extract numeric sort key from session folder."""
    if folder_id := _get_folder_id(folder):
        return folder_id
    original_name = _get_original_name(folder)
    if name_id := _parse_name_prefix(original_name):
        return name_id
    return 0


def _extract_title(original_name: str) -> str:
    title = re.sub(r"^\s*\d+\s*-\s*", "", original_name).strip()
    return title or original_name.strip()


def _extract_session_data(folder: Path) -> SessionData:
    """Extract structured data from a session folder."""
    original_name = _get_original_name(folder)
    folder_id = _get_folder_id(folder)
    name_id = _parse_name_prefix(original_name)
    if folder_id is not None and name_id is not None and folder_id != name_id:
        logger.warning(
            "Session name prefix %s does not match folder id %s in %s",
            name_id,
            folder_id,
            folder,
        )

    title = _extract_title(original_name)

    video_url = _read_file_content(folder / VIDEO_FILE)
    if not video_url:
        raise ValueError(f"Empty video.txt in {folder}")
    if not _is_valid_url(video_url):
        raise ValueError(f"Invalid video URL in {folder / VIDEO_FILE}: {video_url}")

    download_url = None
    zip_path = folder / ZIP_FILE
    if zip_path.exists():
        repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_GITHUB_REPO)
        download_url = f"https://raw.githubusercontent.com/{repo}/main/{zip_path.as_posix()}"

    resources: list[ResourceLink] = []
    urls_path = folder / URLS_FILE
    if urls_path.exists():
        resources = list(_parse_urls_file(urls_path))

    session_id = folder_id if folder_id is not None else name_id or 0

    return {
        "id": session_id,
        "title": title,
        "video_url": video_url,
        "download_url": download_url,
        "resources": resources,
    }


@lru_cache(maxsize=128)
def _get_original_name(folder: Path) -> str:
    name_file = folder / NAME_FILE
    if name_file.exists():
        content = _read_file_content(name_file)
        if content:
            return content
    return folder.name


def _read_file_content(file_path: Path) -> str:
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8").strip()


def _parse_url_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    for separator in ("|", "\t", ":"):
        if separator in stripped:
            left, right = stripped.split(separator, 1)
            title = left.strip()
            url = right.strip()
            if title and url:
                return title, url
            return None

    return None


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _parse_urls_file(urls_path: Path) -> Iterator[ResourceLink]:
    content = _read_file_content(urls_path)
    if not content:
        return
    for line_number, line in enumerate(content.splitlines(), 1):
        parsed = _parse_url_line(line)
        if not parsed:
            continue
        title, url = parsed
        if not _is_valid_url(url):
            logger.warning(
                "Skipping invalid resource URL in %s:%d: %s",
                urls_path,
                line_number,
                url,
            )
            continue
        yield {"title": title, "url": url}


if __name__ == "__main__":
    try:
        generate_site()
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to generate data: %s", e)
        sys.exit(1)
