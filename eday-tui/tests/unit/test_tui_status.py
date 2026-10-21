from app.tui import format_selection_status


def test_status_shows_batch_off_for_zero_selection() -> None:
    assert format_selection_status("Left", 0) == "Pane: Left | 0 selected | Batch mode: off"


def test_status_singular_selected_item() -> None:
    assert format_selection_status("Right", 1) == "Pane: Right | 1 item selected | Batch mode: on"


def test_status_plural_selected_items() -> None:
    assert format_selection_status("Left", 3) == "Pane: Left | 3 items selected | Batch mode: on"
