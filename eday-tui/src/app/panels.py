from __future__ import annotations

from pathlib import Path

from textual.containers import Vertical
from textual.widgets import Label, ListItem, ListView, Static

from app.filesystem.listing import list_directory


class FilePane(Vertical):
    def __init__(self, title: str, start_path: Path, *, show_hidden: bool = False) -> None:
        super().__init__()
        self.title = title
        self.current_path = start_path
        self.show_hidden = show_hidden
        self.filter_text = ""
        self.entries: list[Path] = []
        self.selected_entries: set[Path] = set()
        self.path_label = Static("", classes="path-label")
        self.list_view = ListView(classes="file-list")

    def compose(self):
        yield Label(self.title, classes="pane-title")
        yield self.path_label
        yield self.list_view

    def refresh_entries(self) -> None:
        previous_index = self.list_view.index or 0
        self.entries = list_directory(self.current_path, self.show_hidden, self.filter_text)
        self.selected_entries = {entry for entry in self.selected_entries if entry in self.entries}
        self.path_label.update(str(self.current_path))
        self.list_view.clear()

        self.list_view.append(ListItem(Label("..")))
        for entry in self.entries:
            marker = "[D]" if entry.is_dir() else "   "
            selected_marker = "[*]" if entry in self.selected_entries else "[ ]"
            self.list_view.append(ListItem(Label(f"{selected_marker} {marker} {entry.name}")))
        max_index = len(self.entries)
        self.list_view.index = min(previous_index, max_index)

    def selected_navigation_path(self) -> Path | None:
        index = self.list_view.index
        if index is None:
            return None
        if index == 0:
            return self.current_path.parent
        adjusted = index - 1
        if adjusted < 0 or adjusted >= len(self.entries):
            return None
        return self.entries[adjusted]

    def selected_entry_path(self) -> Path | None:
        index = self.list_view.index
        if index is None:
            return None
        adjusted = index - 1
        if adjusted < 0 or adjusted >= len(self.entries):
            return None
        return self.entries[adjusted]

    def operation_paths(self) -> list[Path]:
        if self.selected_entries:
            return sorted(self.selected_entries, key=lambda item: item.name.lower())
        selected = self.selected_entry_path()
        if selected is None:
            return []
        return [selected]

    def toggle_selected_current(self) -> Path | None:
        selected = self.selected_entry_path()
        if selected is None:
            return None
        if selected in self.selected_entries:
            self.selected_entries.remove(selected)
        else:
            self.selected_entries.add(selected)
        self.refresh_entries()
        return selected

    def clear_selection(self) -> None:
        self.selected_entries.clear()

    def selected_count(self) -> int:
        return len(self.selected_entries)

    def open_selected(self) -> Path | None:
        selected = self.selected_navigation_path()
        if selected is None:
            return None
        if selected.is_dir():
            self.selected_entries.clear()
            self.current_path = selected.resolve()
            self.refresh_entries()
            return self.current_path
        return selected


class BookmarkPane(Vertical):
    def __init__(self, bookmarks: list[Path]) -> None:
        super().__init__()
        self.bookmarks = bookmarks
        self.list_view = ListView(classes="bookmark-list")

    def compose(self):
        yield Label("Bookmarks", classes="pane-title")
        yield self.list_view

    def refresh_entries(self) -> None:
        self.list_view.clear()
        for bookmark in self.bookmarks:
            self.list_view.append(ListItem(Label(str(bookmark))))
        if self.bookmarks:
            self.list_view.index = 0

    def selected_bookmark(self) -> Path | None:
        index = self.list_view.index
        if index is None or index < 0 or index >= len(self.bookmarks):
            return None
        return self.bookmarks[index]
