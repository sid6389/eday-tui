from __future__ import annotations

import re
from pathlib import Path

INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*]')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def normalize_folder_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Folder name cannot be empty.")
    if normalized.endswith(".") or normalized.endswith(" "):
        raise ValueError("Folder name cannot end with a dot or space.")
    if INVALID_CHARS_PATTERN.search(normalized):
        raise ValueError("Folder name contains invalid characters.")
    if normalized.upper() in WINDOWS_RESERVED_NAMES:
        raise ValueError("Folder name is a reserved Windows name.")
    return normalized


def is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True

    try:
        import ctypes

        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & 0x2)
    except Exception:
        return False
