from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from app.models import UndoAction

ConflictResolver = Callable[[Path], bool]


def copy_path(source: Path, destination: Path, overwrite: bool) -> Path:
    target = destination / source.name
    if target.exists():
        if not overwrite:
            raise FileExistsError(f"Destination exists: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)

    return target


def move_path(source: Path, destination: Path, overwrite: bool) -> Path:
    target = destination / source.name
    if target.exists():
        if not overwrite:
            raise FileExistsError(f"Destination exists: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    return Path(shutil.move(str(source), str(target)))


def paste_items(
    sources: list[Path],
    destination: Path,
    *,
    cut_mode: bool,
    ask_once_overwrite: bool,
    resolver: ConflictResolver | None = None,
) -> tuple[list[Path], list[UndoAction]]:
    created: list[Path] = []
    undo_actions: list[UndoAction] = []
    overwrite_decision: bool | None = None

    for source in sources:
        target = destination / source.name
        overwrite = False
        if target.exists():
            if ask_once_overwrite:
                if overwrite_decision is None:
                    if resolver is None:
                        raise ValueError("Conflict resolver is required when conflicts exist.")
                    overwrite_decision = resolver(target)
                overwrite = overwrite_decision
            else:
                if resolver is None:
                    raise ValueError("Conflict resolver is required when conflicts exist.")
                overwrite = resolver(target)

            if not overwrite:
                continue

        if cut_mode:
            pasted = move_path(source, destination, overwrite=overwrite)
            undo_actions.append(UndoAction(source=pasted, destination=source, is_move=True))
        else:
            pasted = copy_path(source, destination, overwrite=overwrite)
        created.append(pasted)

    return created, undo_actions
