#!/usr/bin/env python3
"""
Generate Sessions Site Index

This module generates a markdown index page (index.md) from structured session
folders in the sessions directory. Each session folder can contain:
    - video.txt: Required. Contains the YouTube video URL.
    - name.txt: Optional. Contains the original session name with numeric prefix.
    - urls.txt: Optional. Contains additional resource links in "Title: URL" format.
    - Files.zip: Optional. Session materials available for download.

Usage:
    python scripts/generate_sessions.py

The script is designed to be run from the repository root directory.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration constants
SESSIONS_DIR = Path("sessions")
OUTPUT_FILE = Path("index.md")
OUTPUT_HEADER = "# 📺 Video Sessions\n\n"
SECTION_SEPARATOR = "\n\n---\n\n"
DEFAULT_GITHUB_REPO = "Hermione-Granger-1176/TheSundayGamingLearning"

# File name constants
VIDEO_FILE = "video.txt"
NAME_FILE = "name.txt"
URLS_FILE = "urls.txt"
ZIP_FILE = "Files.zip"


def generate_site() -> None:
    """
    Generate the markdown index file from session folders.

    Scans the sessions directory for valid session folders (those containing
    a video.txt file), processes each folder in numerical order, and writes
    the combined markdown output to index.md.

    Raises:
        FileNotFoundError: If the sessions directory does not exist.
    """
    if not SESSIONS_DIR.exists():
        logger.error("Sessions directory not found: %s", SESSIONS_DIR)
        raise FileNotFoundError(f"Sessions directory not found: {SESSIONS_DIR}")

    logger.info("Starting site generation from %s", SESSIONS_DIR)

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

    # Process all folders and generate markdown content
    processed_entries = [_process_folder(folder) for folder in session_folders]

    # Write output file
    output_content = OUTPUT_HEADER + SECTION_SEPARATOR.join(processed_entries)
    OUTPUT_FILE.write_text(output_content, encoding="utf-8")

    logger.info("Successfully generated %s", OUTPUT_FILE)


def _session_sort_key(folder: Path) -> int:
    """
    Extract numeric sort key from session folder.

    Attempts to extract a numeric prefix from the session name stored in
    name.txt, falling back to the folder name pattern if no name file exists.

    Args:
        folder: Path to the session folder.

    Returns:
        Integer sort key, or 0 if no numeric prefix is found.

    Examples:
        >>> _session_sort_key(Path("sessions/session_001"))  # name.txt: "01-Title"
        1
        >>> _session_sort_key(Path("sessions/session_010"))  # no name.txt
        10
    """
    original_name = _get_original_name(folder)

    # Try to extract leading digits from original name
    if match := re.match(r"^(\d+)", original_name):
        return int(match.group(1))

    # Fall back to session_NNN folder name pattern
    if match := re.match(r"^session_(\d+)$", folder.name):
        return int(match.group(1))

    return 0


def _process_folder(folder: Path) -> str:
    """
    Transform a session folder into markdown content.

    Reads the session files and generates formatted markdown including
    the title, video link, optional download link, and optional resource links.

    Args:
        folder: Path to the session folder to process.

    Returns:
        Formatted markdown string for the session.

    Raises:
        FileNotFoundError: If video.txt is missing (should not happen due to
                          filtering in generate_site).
        ValueError: If video.txt is empty or contains only whitespace.
    """
    # Generate title from folder name
    original_name = _get_original_name(folder)
    title = re.sub(r"^\d+-", "", original_name).replace("-", " ")

    # Read video URL
    video_url = _read_file_content(folder / VIDEO_FILE)
    if not video_url:
        logger.warning("Empty video.txt in %s", folder)
        raise ValueError(f"Empty video.txt in {folder}")

    # Build markdown components
    components: list[str] = [
        f"## 🎬 {title}",
        f"📺 Watch: [YouTube Link]({video_url})",
    ]

    # Add download link if Files.zip exists
    zip_path = folder / ZIP_FILE
    if zip_path.exists():
        repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_GITHUB_REPO)
        components.append(
            f"📥 Download: [Session Materials]"
            f"(https://raw.githubusercontent.com/{repo}/main/{zip_path})"
        )

    # Add additional resource links if urls.txt exists
    urls_path = folder / URLS_FILE
    if urls_path.exists():
        resource_links = list(_parse_urls_file(urls_path))
        if resource_links:
            components.append("🔗 Additional Resources:")
            components.extend(resource_links)

    return "\n\n".join(components)


@lru_cache(maxsize=128)
def _get_original_name(folder: Path) -> str:
    """
    Retrieve the original session name from metadata.

    Reads the name from name.txt if it exists, otherwise uses the folder name.
    Results are cached to avoid repeated file reads during sorting.

    Args:
        folder: Path to the session folder.

    Returns:
        The original session name or folder name as fallback.
    """
    name_file = folder / NAME_FILE
    if name_file.exists():
        content = _read_file_content(name_file)
        if content:
            return content
    return folder.name


def _read_file_content(file_path: Path) -> str:
    """
    Read and return stripped content from a text file.

    Args:
        file_path: Path to the file to read.

    Returns:
        Stripped file content, or empty string if file doesn't exist.
    """
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8").strip()


def _parse_urls_file(urls_path: Path) -> Iterator[str]:
    """
    Parse URLs file and yield formatted markdown links.

    Each line in the URLs file should be in the format "Title: URL".
    Lines without a colon separator are skipped.

    Args:
        urls_path: Path to the urls.txt file.

    Yields:
        Formatted markdown link strings in the format "- [Title](URL)".
    """
    content = _read_file_content(urls_path)
    if not content:
        return

    for line in content.splitlines():
        line = line.strip()
        if ":" not in line:
            continue

        title, url = line.split(":", 1)
        title = title.strip()
        url = url.strip()

        if title and url:
            yield f"- [{title}]({url})"


if __name__ == "__main__":
    try:
        generate_site()
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to generate site: %s", e)
        sys.exit(1)
