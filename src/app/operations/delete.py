from pathlib import Path
from typing import Literal

from send2trash import send2trash

DeleteMode = Literal["trash", "permanent"]


def _permanent_delete(path: Path) -> None:
    if path.is_dir():
        for child in sorted(path.iterdir(), key=lambda p: p.name.lower(), reverse=True):
            _permanent_delete(child)
        path.rmdir()
        return
    path.unlink()


def delete_item(path: Path, *, mode: DeleteMode = "trash") -> None:
    if mode == "trash":
        send2trash(str(path))
        return
    if mode == "permanent":
        _permanent_delete(path)
        return
    raise ValueError(f"Unsupported delete mode: {mode}")


def delete_items(paths: list[Path], *, mode: DeleteMode = "trash") -> None:
    for path in paths:
        delete_item(path, mode=mode)
