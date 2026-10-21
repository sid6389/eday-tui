from pathlib import Path

import pytest

from app.operations.delete import delete_item, delete_items


def test_delete_item_permanent_file(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("sample", encoding="utf-8")
    delete_item(file_path, mode="permanent")
    assert not file_path.exists()


def test_delete_item_permanent_directory(tmp_path: Path) -> None:
    directory = tmp_path / "folder"
    nested_file = directory / "nested.txt"
    nested_file.parent.mkdir(parents=True)
    nested_file.write_text("sample", encoding="utf-8")
    delete_item(directory, mode="permanent")
    assert not directory.exists()


def test_delete_items_uses_trash_mode(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_send_to_trash(path: str) -> None:
        calls.append(path)

    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("a", encoding="utf-8")
    file_b.write_text("b", encoding="utf-8")

    monkeypatch.setattr("app.operations.delete.send2trash", fake_send_to_trash)
    delete_items([file_a, file_b], mode="trash")
    assert calls == [str(file_a), str(file_b)]


def test_delete_item_rejects_invalid_mode(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("sample", encoding="utf-8")
    with pytest.raises(ValueError):
        delete_item(file_path, mode="unknown")  # type: ignore[arg-type]
