from __future__ import annotations

import asyncio
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListView, Static

from app.bookmarks import BookmarkStore
from app.filesystem.clipboard import ClipboardManager
from app.keymap import (
    KEY_ADD_BOOKMARK,
    KEY_COMMAND_PALETTE,
    KEY_COPY,
    KEY_CUT,
    KEY_DELETE,
    KEY_FOCUS_BOOKMARKS,
    KEY_NEW_FOLDER,
    KEY_OPEN,
    KEY_PASTE,
    KEY_REMOVE_BOOKMARK,
    KEY_RENAME,
    KEY_SEARCH,
    KEY_SWITCH_PANE,
    KEY_TOGGLE_HIDDEN,
    KEY_TOGGLE_SELECT,
    KEY_UNDO,
    KEY_UP_DIR,
)
from app.models import UndoAction
from app.operations.copy_paste import paste_items
from app.operations.create_folder import create_folder
from app.operations.delete import delete_items
from app.operations.rename_move import rename_item
from app.panels import BookmarkPane, FilePane


def format_selection_status(active_pane: str, selected_count: int) -> str:
    if selected_count == 0:
        return f"Pane: {active_pane} | 0 selected | Batch mode: off"
    noun = "item" if selected_count == 1 else "items"
    return f"Pane: {active_pane} | {selected_count} {noun} selected | Batch mode: on"


class InputScreen(ModalScreen[str | None]):
    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self.prompt = prompt
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Label(self.prompt)
        yield Input(placeholder=self.placeholder, id="input")
        yield Label("Enter = submit, Esc = cancel")

    @on(Input.Submitted, "#input")
    def on_submit(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def key_escape(self) -> None:
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    def __init__(self, prompt: str) -> None:
        super().__init__()
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        yield Label(self.prompt)
        yield Label("y = yes, n = no")

    def key_y(self) -> None:
        self.dismiss(True)

    def key_n(self) -> None:
        self.dismiss(False)

    def key_escape(self) -> None:
        self.dismiss(False)


class FileManagerApp(App):
    DELETE_MODE = "trash"

    CSS = """
    Screen { layout: vertical; }
    #main-row { height: 1fr; }
    .pane-title { text-style: bold; }
    .path-label { color: cyan; height: 1; }
    .file-list, .bookmark-list { height: 1fr; border: round #555555; }
    .active-pane { border: round #7dd3fc; background: #0f172a; }
    .inactive-pane { border: round #555555; }
    #selection-status { height: 1; padding: 0 1; color: $text-muted; }
    #bookmark-pane { width: 33; }
    """

    BINDINGS = [
        Binding(KEY_SWITCH_PANE, "switch_pane", "Switch pane"),
        Binding(KEY_TOGGLE_SELECT, "toggle_select", "Select"),
        Binding(KEY_OPEN, "open_selected", "Open", priority=True),
        Binding(KEY_UP_DIR, "go_parent", "Up"),
        Binding(KEY_COPY, "copy_selected", "Copy"),
        Binding(KEY_CUT, "cut_selected", "Cut"),
        Binding(KEY_PASTE, "paste_clipboard", "Paste"),
        Binding(KEY_NEW_FOLDER, "new_folder", "New folder"),
        Binding(KEY_RENAME, "rename_selected", "Rename"),
        Binding(KEY_DELETE, "delete_selected", "Delete"),
        Binding(KEY_TOGGLE_HIDDEN, "toggle_hidden", "Toggle hidden"),
        Binding(KEY_SEARCH, "search_filter", "Search"),
        Binding(KEY_ADD_BOOKMARK, "add_bookmark", "Add bookmark"),
        Binding(KEY_REMOVE_BOOKMARK, "remove_bookmark", "Remove bookmark"),
        Binding(KEY_FOCUS_BOOKMARKS, "focus_bookmarks", "Focus bookmarks"),
        Binding(KEY_COMMAND_PALETTE, "command_palette", "Command palette"),
        Binding("l", "open_bookmark_left", "Bookmark -> Left"),
        Binding("p", "open_bookmark_right", "Bookmark -> Right"),
        Binding(KEY_UNDO, "undo_last", "Undo"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        start_path = Path.cwd()
        self.left_pane = FilePane("Left", start_path)
        self.left_pane.add_class("active-pane")
        self.right_pane = FilePane("Right", start_path)
        self.right_pane.add_class("inactive-pane")
        self.active_pane = self.left_pane
        self.clipboard = ClipboardManager()
        self.bookmark_store = BookmarkStore()
        self.bookmark_pane = BookmarkPane(self.bookmark_store.load())
        self.undo_stack: list[UndoAction] = []
        self.selection_status = Static(id="selection-status")
        self._last_status_text = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-row"):
            self.bookmark_pane.id = "bookmark-pane"
            yield self.bookmark_pane
            yield self.left_pane
            yield self.right_pane
        yield self.selection_status
        yield Footer()

    def on_mount(self) -> None:
        self.left_pane.refresh_entries()
        self.right_pane.refresh_entries()
        self.bookmark_pane.refresh_entries()
        self._focus_active_list()
        self._update_selection_status()
        self.notify("Ready")

    def _focus_active_list(self) -> None:
        self.active_pane.list_view.focus()

    def _focus_bookmark_list(self) -> None:
        self.bookmark_pane.list_view.focus()

    def _sync_active_pane_from_focus(self, focused_widget: object | None) -> None:
        if focused_widget is self.left_pane.list_view:
            self.active_pane = self.left_pane
        elif focused_widget is self.right_pane.list_view:
            self.active_pane = self.right_pane
        else:
            return
        self._apply_active_pane_styles()

    def _sync_active_pane_by_focus_state(self) -> None:
        if self.right_pane.list_view.has_focus:
            next_pane = self.right_pane
        elif self.left_pane.list_view.has_focus:
            next_pane = self.left_pane
        else:
            return
        if next_pane is not self.active_pane:
            self.active_pane = next_pane
            self._apply_active_pane_styles()

    def _apply_active_pane_styles(self) -> None:
        for pane in (self.left_pane, self.right_pane):
            pane.remove_class("active-pane")
            pane.remove_class("inactive-pane")
            if pane is self.active_pane:
                pane.add_class("active-pane")
            else:
                pane.add_class("inactive-pane")

    def _inactive_pane(self) -> FilePane:
        return self.right_pane if self.active_pane is self.left_pane else self.left_pane

    async def _ask_text(self, prompt: str, placeholder: str = "") -> str | None:
        future = asyncio.get_running_loop().create_future()

        def _complete(value: str | None) -> None:
            if not future.done():
                future.set_result(value)

        self.push_screen(InputScreen(prompt, placeholder), callback=_complete)
        return await future

    async def _confirm(self, prompt: str) -> bool:
        future = asyncio.get_running_loop().create_future()

        def _complete(value: bool) -> None:
            if not future.done():
                future.set_result(value)

        self.push_screen(ConfirmScreen(prompt), callback=_complete)
        return await future

    def _refresh_all(self) -> None:
        self.left_pane.refresh_entries()
        self.right_pane.refresh_entries()
        self.bookmark_pane.refresh_entries()
        self._update_selection_status()

    def _update_selection_status(self) -> None:
        self._sync_active_pane_by_focus_state()
        status = format_selection_status(self.active_pane.title, self.active_pane.selected_count())
        if status == self._last_status_text:
            return
        self._last_status_text = status
        self.selection_status.update(status)

    def _selected_path(self) -> Path | None:
        self._sync_active_pane_by_focus_state()
        return self.active_pane.selected_entry_path()

    def _operation_paths(self) -> list[Path]:
        self._sync_active_pane_by_focus_state()
        return [path for path in self.active_pane.operation_paths() if path.exists()]

    def action_switch_pane(self) -> None:
        self.active_pane = self._inactive_pane()
        self._apply_active_pane_styles()
        self._focus_active_list()
        self._update_selection_status()
        self.notify(f"Active pane: {self.active_pane.title}")

    def action_open_selected(self) -> None:
        self._sync_active_pane_by_focus_state()
        selected = self.active_pane.open_selected()
        if selected is None:
            self.notify("No selection", severity="warning")
            return
        self._update_selection_status()
        if selected.is_file():
            self.notify(f"Selected file: {selected.name}")

    def action_go_parent(self) -> None:
        self._sync_active_pane_by_focus_state()
        self.active_pane.clear_selection()
        self.active_pane.current_path = self.active_pane.current_path.parent
        self.active_pane.refresh_entries()
        self._update_selection_status()
        self._focus_active_list()

    def action_toggle_select(self) -> None:
        self._sync_active_pane_by_focus_state()
        selected = self.active_pane.toggle_selected_current()
        if selected is None:
            self.notify("Select a file or folder first", severity="warning")
            return
        self._update_selection_status()
        self._focus_active_list()
        self.notify(f"Selected {self.active_pane.selected_count()} item(s)")

    def action_copy_selected(self) -> None:
        self._sync_active_pane_by_focus_state()
        targets = self._operation_paths()
        if not targets:
            self.notify("Nothing selected", severity="warning")
            return
        self.clipboard.set_copy(targets)
        self.notify(f"Copied {len(targets)} item(s)")

    def action_cut_selected(self) -> None:
        self._sync_active_pane_by_focus_state()
        targets = self._operation_paths()
        if not targets:
            self.notify("Nothing selected", severity="warning")
            return
        self.clipboard.set_cut(targets)
        self.notify(f"Cut {len(targets)} item(s)")

    async def action_paste_clipboard(self) -> None:
        self._sync_active_pane_by_focus_state()
        state = self.clipboard.get_state()
        sources = [item.path for item in state.items if item.path.exists()]
        if not sources:
            os_paths = self.clipboard.read_os_clipboard_paths()
            if os_paths:
                sources = os_paths
                state.cut_mode = False

        if not sources:
            self.notify("Clipboard is empty", severity="warning")
            return

        destination = self.active_pane.current_path
        conflicts = [destination / source.name for source in sources if (destination / source.name).exists()]
        overwrite_all = False
        if conflicts:
            overwrite_all = await self._confirm(
                f"Overwrite all conflicts? ({len(conflicts)} conflict(s), first: {conflicts[0].name})"
            )

        def sync_resolver(_target: Path) -> bool:
            return overwrite_all

        try:
            created, undo_actions = paste_items(
                sources,
                destination,
                cut_mode=state.cut_mode,
                ask_once_overwrite=True,
                resolver=sync_resolver,
            )
        except Exception as error:
            self.notify(f"Paste failed: {error}", severity="error")
            return

        self.undo_stack.extend(undo_actions)
        if state.cut_mode:
            self.clipboard.clear()
            self.left_pane.clear_selection()
            self.right_pane.clear_selection()
        self._refresh_all()
        self.notify(f"Pasted {len(created)} item(s)")

    async def action_new_folder(self) -> None:
        self._sync_active_pane_by_focus_state()
        name = await self._ask_text("New folder name")
        if name is None:
            return
        try:
            create_folder(self.active_pane.current_path, name)
        except Exception as error:
            self.notify(f"Create folder failed: {error}", severity="error")
            return
        self.active_pane.refresh_entries()
        self._update_selection_status()
        self.notify("Folder created")

    async def action_rename_selected(self) -> None:
        self._sync_active_pane_by_focus_state()
        if self.active_pane.selected_count() > 1:
            self.notify("Rename supports only one selected item", severity="warning")
            return
        selected = self._selected_path()
        if selected is None or not selected.exists():
            self.notify("Nothing selected", severity="warning")
            return

        new_name = await self._ask_text("Rename to", selected.name)
        if not new_name:
            return

        try:
            new_path, undo_action = rename_item(selected, new_name)
        except Exception as error:
            self.notify(f"Rename failed: {error}", severity="error")
            return
        self.undo_stack.append(undo_action)
        self._refresh_all()
        self.notify(f"Renamed to {new_path.name}")

    async def action_delete_selected(self) -> None:
        self._sync_active_pane_by_focus_state()
        targets = self._operation_paths()
        if not targets:
            self.notify("Nothing selected", severity="warning")
            return
        item_label = targets[0].name if len(targets) == 1 else f"{len(targets)} items"
        delete_verb = "Move to Recycle Bin" if self.DELETE_MODE == "trash" else "Permanently delete"
        confirmed = await self._confirm(f"{delete_verb} {item_label}?")
        if not confirmed:
            self.notify("Delete cancelled")
            return
        try:
            delete_items(targets, mode=self.DELETE_MODE)
        except Exception as error:
            self.notify(f"Delete failed: {error}", severity="error")
            return
        self.active_pane.clear_selection()
        self._refresh_all()
        if self.DELETE_MODE == "trash":
            self.notify(f"Moved {len(targets)} item(s) to Recycle Bin")
        else:
            self.notify(f"Deleted {len(targets)} item(s)")

    async def action_search_filter(self) -> None:
        self._sync_active_pane_by_focus_state()
        text = await self._ask_text("Filter entries", self.active_pane.filter_text)
        if text is None:
            return
        self.active_pane.filter_text = text.strip()
        self.active_pane.refresh_entries()
        self._update_selection_status()
        self._focus_active_list()

    def action_toggle_hidden(self) -> None:
        self._sync_active_pane_by_focus_state()
        self.active_pane.show_hidden = not self.active_pane.show_hidden
        self.active_pane.refresh_entries()
        self._update_selection_status()
        state = "shown" if self.active_pane.show_hidden else "hidden"
        self.notify(f"Hidden files are now {state} in {self.active_pane.title}")

    def action_add_bookmark(self) -> None:
        self._sync_active_pane_by_focus_state()
        current = self.active_pane.current_path
        if current in self.bookmark_pane.bookmarks:
            self.notify("Bookmark already exists", severity="warning")
            return
        self.bookmark_pane.bookmarks.append(current)
        self.bookmark_store.save(self.bookmark_pane.bookmarks)
        self.bookmark_pane.refresh_entries()
        self._focus_bookmark_list()
        self.notify("Bookmark added")

    def action_focus_bookmarks(self) -> None:
        if not self.bookmark_pane.bookmarks:
            self.notify("No bookmarks available", severity="warning")
            return
        if self.bookmark_pane.list_view.index is None:
            self.bookmark_pane.list_view.index = 0
        self._focus_bookmark_list()
        self.notify("Focused bookmark panel")

    def action_remove_bookmark(self) -> None:
        if not self.bookmark_pane.list_view.has_focus:
            self.notify("Focus bookmark panel first (Ctrl+B)", severity="warning")
            return
        selected = self.bookmark_pane.selected_bookmark()
        if selected is None:
            self.notify("No bookmark selected", severity="warning")
            return
        self.bookmark_pane.bookmarks = [item for item in self.bookmark_pane.bookmarks if item != selected]
        self.bookmark_store.save(self.bookmark_pane.bookmarks)
        self.bookmark_pane.refresh_entries()
        self._focus_bookmark_list()
        self.notify("Bookmark removed")

    def action_open_bookmark_left(self) -> None:
        if not self.bookmark_pane.list_view.has_focus:
            self.notify("Focus bookmark panel first (Ctrl+B)", severity="warning")
            return
        selected = self.bookmark_pane.selected_bookmark()
        if selected is None:
            self.notify("No bookmark selected", severity="warning")
            return
        self.left_pane.current_path = selected
        self.left_pane.clear_selection()
        self.left_pane.refresh_entries()
        self._update_selection_status()
        self.notify(f"Opened in left: {selected}")

    def action_open_bookmark_right(self) -> None:
        if not self.bookmark_pane.list_view.has_focus:
            self.notify("Focus bookmark panel first (Ctrl+B)", severity="warning")
            return
        selected = self.bookmark_pane.selected_bookmark()
        if selected is None:
            self.notify("No bookmark selected", severity="warning")
            return
        self.right_pane.current_path = selected
        self.right_pane.clear_selection()
        self.right_pane.refresh_entries()
        self._update_selection_status()
        self.notify(f"Opened in right: {selected}")

    def action_undo_last(self) -> None:
        if not self.undo_stack:
            self.notify("Nothing to undo", severity="warning")
            return

        action = self.undo_stack.pop()
        try:
            if action.source.exists():
                action.source.rename(action.destination)
            else:
                self.notify("Undo skipped: source no longer exists", severity="warning")
                return
        except Exception as error:
            self.notify(f"Undo failed: {error}", severity="error")
            return
        self._refresh_all()
        self.notify("Undo complete")

    def on_focus(self, event) -> None:
        target = getattr(event, "widget", None)
        self._sync_active_pane_from_focus(target)

    @on(ListView.Selected)
    def on_list_selected(self, event: ListView.Selected) -> None:
        if event.list_view is self.left_pane.list_view:
            self.active_pane = self.left_pane
        elif event.list_view is self.right_pane.list_view:
            self.active_pane = self.right_pane
        elif event.list_view is self.bookmark_pane.list_view:
            self._focus_bookmark_list()
        self._update_selection_status()
