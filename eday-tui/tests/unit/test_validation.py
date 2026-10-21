from pathlib import Path

import pytest

from app.filesystem.validation import normalize_folder_name


def test_normalize_folder_name_strips_and_accepts_valid() -> None:
    assert normalize_folder_name("  docs  ") == "docs"


@pytest.mark.parametrize("name", ["", "   ", "bad:name", "NUL", "folder."])
def test_normalize_folder_name_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ValueError):
        normalize_folder_name(name)


def test_normalize_folder_name_allows_simple_name() -> None:
    assert normalize_folder_name("project_files") == "project_files"
