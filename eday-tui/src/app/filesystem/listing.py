from __future__ import annotations

from pathlib import Path

from .search import matches_filter
from .validation import is_hidden


def list_directory(path: Path, show_hidden: bool, filter_text: str = "") -> list[Path]:
    entries = []
    for child in path.iterdir():
        if not show_hidden and is_hidden(child):
            continue
        if not matches_filter(child, filter_text):
            continue
        entries.append(child)

    entries.sort(key=lambda item: (not item.is_dir(), item.name.lower()))
    return entries
