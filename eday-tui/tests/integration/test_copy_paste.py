from pathlib import Path

from app.operations.copy_paste import paste_items


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_recursive_folder_copy(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()

    project_dir = source_root / "project"
    nested_dir = project_dir / "a" / "b"
    nested_dir.mkdir(parents=True)

    _write_file(project_dir / "root.txt", "root")
    _write_file(nested_dir / "deep.txt", "deep")

    created, _undo = paste_items(
        [project_dir],
        destination_root,
        cut_mode=False,
        ask_once_overwrite=True,
        resolver=lambda _target: True,
    )

    copied_project = destination_root / "project"
    assert created == [copied_project]
    assert (copied_project / "root.txt").read_text(encoding="utf-8") == "root"
    assert (copied_project / "a" / "b" / "deep.txt").read_text(encoding="utf-8") == "deep"


def test_paste_conflict_skips_when_not_overwriting(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()

    source_file = source_root / "file.txt"
    destination_file = destination_root / "file.txt"
    source_file.write_text("new", encoding="utf-8")
    destination_file.write_text("existing", encoding="utf-8")

    created, _undo = paste_items(
        [source_file],
        destination_root,
        cut_mode=False,
        ask_once_overwrite=True,
        resolver=lambda _target: False,
    )

    assert created == []
    assert destination_file.read_text(encoding="utf-8") == "existing"


def test_batch_copy_multiple_sources(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    destination_root = tmp_path / "destination"
    source_root.mkdir()
    destination_root.mkdir()

    file_a = source_root / "a.txt"
    file_b = source_root / "b.txt"
    folder_c = source_root / "folder_c"
    folder_c.mkdir()
    nested = folder_c / "nested.txt"

    file_a.write_text("A", encoding="utf-8")
    file_b.write_text("B", encoding="utf-8")
    nested.write_text("C", encoding="utf-8")

    created, _undo = paste_items(
        [file_a, file_b, folder_c],
        destination_root,
        cut_mode=False,
        ask_once_overwrite=True,
        resolver=lambda _target: True,
    )

    assert {path.name for path in created} == {"a.txt", "b.txt", "folder_c"}
    assert (destination_root / "a.txt").read_text(encoding="utf-8") == "A"
    assert (destination_root / "b.txt").read_text(encoding="utf-8") == "B"
    assert (destination_root / "folder_c" / "nested.txt").read_text(encoding="utf-8") == "C"
