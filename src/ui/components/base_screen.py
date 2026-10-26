"""Base screen class for Video Slice TUI screens."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    Label,
    Static,
    DataTable,
    Checkbox,
    ProgressBar,
)
from textual.reactive import reactive
from textual import work
import os
import asyncio

from logic import get_video_duration, format_hhmmss, clean_video_path


class ScreenBase(Container):
    """Base class for all tool screens with shared functionality."""

    video_path = reactive("", always_update=True)
    _video_duration = reactive(None)
    _load_generation = 0  # Token to prevent stale results from older async calls

    def watch_video_path(self, new_path: str) -> None:
        """Called when video_path changes."""
        if new_path:
            self.run_worker(self.load_video_info())

    CSS = """
    Screen {
        align: center middle;
    }
    .screen-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }
    .screen-title {
        dock: top;
        text-align: center;
        text-style: bold;
        margin: 1 0;
        padding: 1;
        background: $boost;
        color: $accent;
        border: double $accent;
    }
    .section-header {
        text-style: bold;
        margin: 1 0;
        color: $accent;
    }
    .control-row {
        height: auto;
        margin: 1 0;
        layout: horizontal;
        align: center middle;
    }
    .control-row > Button {
        width: auto;
        min-width: 16;
    }
    .input-group {
        width: 1fr;
        height: auto;
        padding: 0 1;
    }
    .input-group > Label {
        margin-bottom: 1;
        text-style: bold;
        color: $accent;
    }
    .input-section {
        dock: top;
        height: auto;
    }
    .output-section {
        dock: top;
        height: auto;
        padding: 1 0;
    }
    .export-row {
        dock: top;
        height: auto;
        margin: 1 0;
    }
    .data-section {
        height: 1fr;
        border: round $primary;
        padding: 1;
    }
    .status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
    }
    .status-bar.error { color: $error; }
    .status-bar.success { color: $success; }
    .status-bar.warning { color: $warning; }
    .progress-section {
        dock: bottom;
        height: auto;
        min-height: 3;
    }
    .progress-section > Static {
        margin-bottom: 1;
    }
    DataTable {
        height: auto;
        min-height: 3;
        border: none;
    }
    Input {
        width: 1fr;
        height: 3;
    }
    Button {
        margin: 0 1;
    }
    Checkbox {
        margin: 0 2;
    }
    .times-section {
        dock: top;
        height: auto;
    }
    .time-inputs {
        height: auto;
        margin: 1 0;
    }
    """

    async def on_mount(self) -> None:
        """Initial sync with hub state."""
        from ui.screens.hub_screen import HubScreen

        try:
            hub = self.app.query_one(HubScreen)
            if hub.shared_video_path and self.video_path != hub.shared_video_path:
                self.video_path = hub.shared_video_path
        except Exception:
            pass

        self.watch(
            self.app.query_one(HubScreen),
            "shared_video_path",
            self._on_hub_video_path_changed,
        )
        self.watch(
            self.app.query_one(HubScreen),
            "shared_export_path",
            self._on_hub_export_path_changed,
        )

    def _on_hub_video_path_changed(self, path: str) -> None:
        """Called when hub's shared_video_path changes."""
        if path != self.video_path:
            self.video_path = path

    def _on_hub_export_path_changed(self, path: str) -> None:
        """Called when hub's shared_export_path changes."""
        if path != getattr(self, "_custom_output_path", ""):
            self._custom_output_path = path

    def compose(self) -> ComposeResult:
        yield from self._compose_content()
        self.status_bar = Static("", classes="status-bar")
        yield self.status_bar

    def _compose_content(self) -> ComposeResult:
        raise NotImplementedError("Subclasses must implement _compose_content")

    @property
    def video_duration(self) -> float | None:
        return self._video_duration

    def show_status(self, message: str, style: str = "", duration: float = 3.0):
        self.status_bar.update(message)
        self.status_bar.set_class(bool(style), style)
        if style not in ("error",):

            async def _clear():
                await asyncio.sleep(duration)
                self.status_bar.update("")

            asyncio.create_task(_clear())

    def clear_status(self):
        self.status_bar.update("")

    def open_file_dialog(self, callback, multi: bool = False):
        """Open the native media chooser, falling back to terminal path entry."""
        from ui.components.file_dialog import open_native_dialog
        from ui.components.path_prompt import prompt_for_path
        from ui.preferences import get_last_media_dir

        def fallback():
            title = "Add media paths" if multi else "Enter media path"
            prompt_for_path(self.app, title, callback, multi=multi)

        open_native_dialog(
            self.app,
            callback,
            mode="files" if multi else "file",
            title="Select media files" if multi else "Select media file",
            initialdir=get_last_media_dir(),
            fallback=fallback,
            on_error=lambda message: self.show_status(
                f"⚠️ {message}. Paste a path instead.", "warning", duration=8
            ),
        )

    def open_folder_dialog(self, callback):
        """Open the native folder chooser, with a terminal path fallback."""
        from ui.components.file_dialog import open_native_dialog
        from ui.components.path_prompt import prompt_for_path

        open_native_dialog(
            self.app,
            callback,
            mode="folder",
            title="Select output folder",
            fallback=lambda: prompt_for_path(
                self.app, "Enter output folder", callback
            ),
            on_error=lambda message: self.show_status(
                f"⚠️ {message}. Paste a path instead.", "warning", duration=8
            ),
        )

    def try_load_path(self, path: str) -> bool:
        """Try to load a video path from input."""
        clean = clean_video_path(path)
        if clean and os.path.exists(clean):
            self.video_path = clean

            # Notify Hub
            from ui.screens.hub_screen import HubScreen

            self.post_message(HubScreen.UpdateVideoPath(clean))
            return True
        elif not path:
            # Handle clearing
            self.video_path = ""
            self._video_duration = None

            # Notify Hub
            from ui.screens.hub_screen import HubScreen

            self.post_message(HubScreen.UpdateVideoPath(""))
            self.on_video_cleared()
            return True
        return False

    def on_video_cleared(self) -> None:
        """Called when a video is cleared. Subclasses should override to clear queues."""
        pass

    async def load_video_info(self):
        if not self.video_path:
            return

        # Check generation to ignore stale results
        current_gen = self._load_generation + 1
        self._load_generation = current_gen
        
        path = clean_video_path(self.video_path)

        if not os.path.exists(path):
            self.show_status(f"❌ File not found: {path}", "error")
            return

        duration = await get_video_duration(path)
        # Only use result if this is still the current generation
        if current_gen != self._load_generation:
            return
            
        if duration is not None:
            self._video_duration = duration
            self.show_status(
                f"✅ {os.path.basename(path)} loaded - {format_hhmmss(duration)}",
                "success",
            )
        else:
            self.show_status("⚠️ Could not get media duration", "warning")

    def update_progress(self, current: int, total: int, label: str = ""):
        if hasattr(self, "progress_bar"):
            self.progress_bar.display = True
            self.progress_bar.update(total=total, progress=current)
        if hasattr(self, "progress_label"):
            self.progress_label.update(label)

    def hide_progress(self):
        if hasattr(self, "progress_bar"):
            self.progress_bar.display = False
        if hasattr(self, "progress_label"):
            self.progress_label.update("")
