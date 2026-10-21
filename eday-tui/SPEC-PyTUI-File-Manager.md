# Spec: PyTUI File Manager

## Assumptions I Am Making
1. The app targets local filesystem management only (no cloud storage integration in v1).
2. The app is terminal-first and keyboard-first, with optional mouse interaction.
3. Paths and filesystem semantics follow Windows behavior first, with future portability in mind.
4. This spec defines v1 scope and acceptance criteria only; packaging/distribution can be phased later.
5. Paste conflict handling asks once per operation and applies the choice to all conflicts in that operation.

If any assumption is wrong, this spec should be revised before coding.

## Objective
Build a Python-based TUI file manager that runs on Windows and supports fast everyday file operations through a dual-pane interface.

Primary user outcome:
- Navigate directories quickly
- Copy/paste files and folders
- Create new folders
- Rename/move files and folders
- Delete files and folders safely
- Filter/search visible entries

Success is achieved when users can complete common file-management tasks without leaving the terminal.

## Tech Stack
- Language: Python 3.11+
- TUI Framework: Textual
- Standard libraries (expected): `pathlib`, `shutil`, `os`, `send2trash` (if recycle-bin behavior is implemented)

## Commands
Development commands (target commands for project setup):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m textual run src\main.py
pytest -q
ruff check .
ruff format .
```

## Project Structure
```text
src/
  main.py                 -> app entrypoint
  app/
    tui.py                -> Textual app + layout composition
    keymap.py             -> keyboard/mouse bindings
    panels.py             -> dual-pane widgets and focus handling
    bookmarks.py          -> bookmarked-folder quick access widget
    operations/
      copy_paste.py       -> copy/cut/paste workflows
      create_folder.py    -> mkdir flow + validation
      rename_move.py      -> rename and move operations
      delete.py           -> delete flow + confirmations
    filesystem/
      listing.py          -> directory listing, hidden-file filtering
      validation.py       -> path/name validation utilities
      clipboard.py        -> internal + OS clipboard path support
      search.py           -> in-pane filtering/search
    models.py             -> operation/result data models
tests/
  unit/
  integration/
```

## Code Style
Conventions:
- Type hints on public functions
- Clear operation result objects instead of silent failures
- Explicit error messages surfaced to UI
- Small focused modules by operation

Example style:

```python
from pathlib import Path

def create_folder(parent: Path, name: str) -> Path:
    candidate = (parent / name.strip()).resolve()
    if not name.strip():
        raise ValueError("Folder name cannot be empty.")
    candidate.mkdir(parents=False, exist_ok=False)
    return candidate
```

## Functional Requirements
1. **Dual-pane layout**
   - Two file panels visible: active source pane and target pane.
   - User can switch active pane.
   - Include a small bookmarks section for fast access to linked favorite folders.
   - Selecting a bookmark opens that folder in the active pane.
   - User can also open a bookmark directly in the left or right pane.

2. **Navigation**
   - Open folders, go up one level, refresh listing.
   - Hidden files are hidden by default, with a toggle to show/hide.

3. **Copy/paste (both clipboards)**
   - Internal clipboard support for app-native copy/cut/paste.
   - OS clipboard path integration when available on Windows.
   - On name conflicts, app prompts once and applies that decision to all conflicts in the current paste operation.
   - Copying a folder must recursively copy all nested files and subfolders.
   - For large copy operations, show a simple status message (no progress bar in v1).

4. **Create folder**
   - New folder operation available from keyboard and command/action menu.
   - Strict validation: disallow empty names, invalid characters, reserved names, and trailing/leading-only whitespace names.

5. **Rename/move**
   - Rename item in current pane.
   - Move item to another directory/pane destination.

6. **Delete**
   - Delete files/folders with confirmation prompt before execution.
   - Default delete mode moves items to Recycle Bin.
   - If multiple items are selected, delete operation applies to the full selected batch.
   - Errors must be shown explicitly to user.

7. **Search/filter**
   - Filter entries in active pane by typed text.
   - Clear filter restores full listing.

8. **Input modes**
   - Keyboard-first, custom simple keymap.
   - Mouse interactions supported (selection, pane focus, scroll).
   - Multi-select is supported for batch operations.

9. **Undo (non-destructive operations)**
   - Undo support for operations that can be safely reversed in v1.
   - At minimum, support undo for rename and move if operation metadata is available.

10. **Bookmarks**
   - Bookmarks are persisted locally and reloaded on app start.
   - v1 bookmark actions:
     - Add current folder
     - Remove bookmark
     - Open bookmark in active pane
     - Open bookmark explicitly in left or right pane

## Non-Functional Requirements
- **Reliability:** file operations must report success/failure deterministically.
- **Performance:** pane navigation and listing refresh should feel immediate for normal directories (target < 200ms for directories up to ~2,000 entries on typical local disk).
- **Usability:** actions discoverable via status bar/help legend.
- **Safety:** confirmations before delete and overwrite.
- **Error handling:** no silent failures; every failed operation returns an actionable message.

## Testing Strategy
- Unit tests for path validation, clipboard state, conflict handling, and operation planners.
- Integration tests for copy/paste, rename/move, create folder, and delete flows using temp directories.
- Integration tests must validate recursive folder copy (deeply nested files/subfolders).
- Keyboard interaction tests for primary shortcuts and pane switching.
- Regression tests for hidden-file toggle and search/filter behavior.

Minimum verification:
- `pytest -q` passes for all unit/integration tests.
- Manual scenario check:
  1) Create folder
  2) Copy file
  3) Paste to other pane
  4) Rename moved file
  5) Delete with confirmation
  6) Undo supported operation

## Boundaries
- **Always do**
  - Validate all filesystem input names and paths.
  - Show explicit success/error feedback in UI.
  - Ask for confirmation before delete and overwrite.
  - Keep operations atomic where possible.

- **Ask first**
  - Adding third-party dependencies beyond core TUI/file handling.
  - Changing conflict policy from "ask once/apply to all" behavior.
  - Expanding scope to cloud/remote filesystems.

- **Never do**
  - Silent destructive actions.
  - Hidden background file operations without user intent.
  - Persisting sensitive path history outside user control.

## Success Criteria
1. Windows user can fully manage files/folders from terminal using the app.
2. Copy/paste, create folder, rename/move, and delete all work with confirmations and explicit error handling.
3. Folder copy operations include complete recursive contents (files + subfolders).
4. Hidden files are hidden by default and can be toggled visible.
5. Search/filter works on active pane.
6. Keyboard + mouse both usable in primary workflows.
7. Bookmark links provide fast navigation to user-selected folders.
8. Test suite passes and covers core operations.
9. Multi-select batch copy/cut/delete works in active pane.
10. Delete mode sends items to Recycle Bin by default.

## Open Questions
1. What exact key bindings should be used for:
   - Copy
   - Cut
   - Paste
   - New folder
   - Rename
   - Delete
   - Toggle hidden files
   - Search/filter
2. Should undo include delete (requires recycle-bin/trash strategy), or only rename/move in v1?
