from __future__ import annotations

import json
from pathlib import Path

BOOKMARK_FILE = Path.home() / ".pytui_file_manager_bookmarks.json"


class BookmarkStore:
    def __init__(self, path: Path = BOOKMARK_FILE) -> None:
        self.path = path

    def load(self) -> list[Path]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            paths = [Path(value) for value in data if isinstance(value, str)]
            return [item for item in paths if item.exists() and item.is_dir()]
        except Exception:
            return []

    def save(self, bookmarks: list[Path]) -> None:
        serialized = [str(path) for path in bookmarks]
        self.path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
