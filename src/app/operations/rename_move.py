from pathlib import Path

from app.models import UndoAction


def rename_item(path: Path, new_name: str) -> tuple[Path, UndoAction]:
    destination = path.with_name(new_name)
    path.rename(destination)
    return destination, UndoAction(source=destination, destination=path, is_move=True)


def move_item(path: Path, destination_directory: Path) -> tuple[Path, UndoAction]:
    destination = destination_directory / path.name
    path.rename(destination)
    return destination, UndoAction(source=destination, destination=path, is_move=True)
