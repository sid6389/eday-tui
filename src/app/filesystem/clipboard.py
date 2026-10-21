from __future__ import annotations

import subprocess
from pathlib import Path

from app.models import ClipboardItem, ClipboardState


class ClipboardManager:
    def __init__(self) -> None:
        self._state = ClipboardState(items=[], cut_mode=False)

    def get_state(self) -> ClipboardState:
        return self._state

    def set_copy(self, paths: list[Path]) -> None:
        self._state = ClipboardState(items=[ClipboardItem(path=p) for p in paths], cut_mode=False)
        self._write_os_clipboard(paths)

    def set_cut(self, paths: list[Path]) -> None:
        self._state = ClipboardState(items=[ClipboardItem(path=p) for p in paths], cut_mode=True)
        self._write_os_clipboard(paths)

    def clear(self) -> None:
        self._state = ClipboardState(items=[], cut_mode=False)

    def read_os_clipboard_paths(self) -> list[Path]:
        try:
            command = "Get-Clipboard -Raw"
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return []

            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            paths = [Path(line) for line in lines]
            return [p for p in paths if p.exists()]
        except Exception:
            return []

    def _write_os_clipboard(self, paths: list[Path]) -> None:
        payload = "\n".join(str(path) for path in paths)
        if not payload:
            return

        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
                input=payload,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return
