from pathlib import Path

from app.filesystem.validation import normalize_folder_name


def create_folder(parent: Path, name: str) -> Path:
    normalized = normalize_folder_name(name)
    candidate = parent / normalized
    candidate.mkdir(parents=False, exist_ok=False)
    return candidate
