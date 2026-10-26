"""Textual path entry fallback for unavailable native file selectors."""

from collections.abc import Callable

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, TextArea

from logic.input_parsing import clean_pasted_path


class PathPrompt(ModalScreen[str | list[str] | None]):
    """Ask for one path, or one path per line for a multi-file selection."""

    CSS = """
    PathPrompt { align: center middle; }
    #path-dialog {
        width: 80;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: round $accent;
        background: $surface;
    }
    #path-help { color: $text-muted; margin-bottom: 1; }
    #path-entry { height: 3; }
    #path-list { height: 10; }
    #path-actions { height: 3; margin-top: 1; align: right middle; }
    """

    def __init__(self, title: str, *, multi: bool = False) -> None:
        super().__init__()
        self.dialog_title = title
        self.multi = multi

    def compose(self) -> ComposeResult:
        with Vertical(id="path-dialog"):
            yield Static(self.dialog_title, classes="section-header")
            if self.multi:
                yield Static("Paste one file path per line.", id="path-help")
                yield TextArea(id="path-list")
            else:
                yield Static("Paste a path here. Quotes around the path are OK.", id="path-help")
                yield Input(placeholder="/path/to/file", id="path-entry")
            with Horizontal(id="path-actions"):
                yield Button("Cancel", id="path-cancel")
                yield Button("Use path", id="path-confirm", variant="primary")

    def on_mount(self) -> None:
        self.set_focus(self.query_one(TextArea if self.multi else Input))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "path-cancel":
            self.dismiss(None)
            return

        if self.multi:
            raw_paths = self.query_one(TextArea).text.splitlines()
            paths = [clean_pasted_path(path) for path in raw_paths]
            paths = [path for path in paths if path]
            self.dismiss(paths or None)
        else:
            path = clean_pasted_path(self.query_one(Input).value)
            self.dismiss(path or None)


def prompt_for_path(
    app,
    title: str,
    callback: Callable[[str | list[str]], None],
    *,
    multi: bool = False,
) -> None:
    """Open the in-app path prompt and pass its result to ``callback``."""

    def on_result(value: str | list[str] | None) -> None:
        if value:
            callback(value)

    app.push_screen(PathPrompt(title, multi=multi), on_result)
