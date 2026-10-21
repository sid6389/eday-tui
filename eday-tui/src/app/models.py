from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OperationResult:
    success: bool
    message: str


@dataclass(frozen=True)
class ClipboardItem:
    path: Path


@dataclass
class ClipboardState:
    items: list[ClipboardItem]
    cut_mode: bool


@dataclass(frozen=True)
class UndoAction:
    source: Path
    destination: Path
    is_move: bool
