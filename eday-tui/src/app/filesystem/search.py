from pathlib import Path


def matches_filter(path: Path, filter_text: str) -> bool:
    if not filter_text:
        return True
    return filter_text.lower() in path.name.lower()
