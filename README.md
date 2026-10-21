# PyTUI File Manager

Terminal-based file manager for Windows (Python 3.11+, Textual), with:
- Dual-pane navigation
- Multi-select batch operations
- Copy/Cut/Paste for files and folders (recursive for folders)
- New folder, rename, delete with confirmation
- Recycle-bin delete mode (default)
- Hidden-file toggle
- Search/filter in active pane
- Bookmark quick-access panel (persistent local storage)
- Undo for move/rename-style operations
- Selection status indicator above footer (active pane + selected count)

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python src\main.py
```

## Default keys

- `Tab`: switch active pane
- `Space`: toggle selection for current file/folder (batch mode)
- `Enter`: open selected directory/file item
- `Backspace`: go to parent directory
- `c`: copy
- `x`: cut
- `v`: paste
- `n`: create folder
- `r`: rename selected
- `d`: delete selected (with confirm)
- `h`: toggle hidden files in active pane
- `/`: filter/search in active pane
- `b`: add current folder to bookmarks
- `Ctrl+B`: focus bookmark panel
- `Shift+B`: remove selected bookmark (when bookmark panel is focused)
- `Shift+I`: open command palette
- `l`: open selected bookmark in left pane (from bookmark panel)
- `p`: open selected bookmark in right pane (from bookmark panel)
- `u`: undo last move/rename-style action
- `q`: quit

## Notes

- Delete (`d`) moves selected items to Recycle Bin by default.
- Batch operations apply to all selected items; if no batch selection exists, actions apply to the current row.
