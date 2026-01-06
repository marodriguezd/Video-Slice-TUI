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

    def watch_video_path(self, new_path: str) -> None:
        """Called when video_path changes."""
        if hasattr(self, "file_input"):
            expected_val = f'"{new_path}"' if new_path else ""
            if self.file_input.value != expected_val:
                self.file_input.value = expected_val
        
        if new_path:
             asyncio.create_task(self.load_video_info())

    CSS = """
    Screen {
        align: center middle;
    }
    .screen-container {
        width: 100%;
        height: 100%;
        padding: 0;
    }
    .screen-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .control-row {
        height: auto;
        margin-top: 1;
        layout: horizontal;
        align: center middle;
    }
    .control-row > Button {
        width: auto;
        min-width: 16;
    }
    .filebox {
        height: auto;
        margin-bottom: 1;
        layout: horizontal;
    }
    .filebox > Input {
        width: 1fr;
    }
    .filebox > Button {
        width: auto;
        min-width: 12;
    }
    .time-inputs {
        height: auto;
        margin-bottom: 1;
    }
    .input-group {
        width: 1fr;
        height: auto;
    }
    .data-section {
        height: 1fr;
        border: round $accent;
        padding: 1;
        margin-bottom: 1;
    }
    .section-header {
        text-style: bold;
        margin-bottom: 1;
    }
    .actions-row {
        height: auto;
    }
    .log-section {
        height: 10;
        border: round $accent;
        padding: 1;
    }
    .progress-section {
        height: 3;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
        margin-bottom: 1;
    }
    Label {
        width: auto;
        padding: 0 1;
    }
    Input {
        width: 1fr;
    }
    Button {
        margin: 0 1;
        width: auto;
    }
    ProgressBar {
        margin: 0 1;
    }
    """

    async def on_mount(self) -> None:
        """Initial sync with hub state."""
        from ui.screens.hub_screen import HubScreen
        try:
            hub = self.app.query_one(HubScreen)
            shared = hub.shared_video_path
            if shared and self.video_path != shared:
                self.video_path = shared
        except:
            pass

    def compose(self) -> ComposeResult:
        yield from self._compose_content()

    def _compose_content(self) -> ComposeResult:
        raise NotImplementedError("Subclasses must implement _compose_content")

    @property
    def video_duration(self) -> float | None:
        return self._video_duration

    def write_log(self, text: str):
        try:
            current = str(self.log_box.render())
        except:
            current = ""

        new_text = current + text
        lines = new_text.split("\n")
        if len(lines) > 20:
            lines = lines[-20:]
            new_text = "\n".join(lines)

        self.log_box.update(new_text)

    def open_file_dialog(self, callback, multi: bool = False):
        """Open a native OS file selector using Tkinter in a separate thread."""
        import tkinter as tk
        from tkinter import filedialog
        import threading

        def run_dialog():
            try:
                # Initialize a temporary hidden root
                root = tk.Tk()
                root.withdraw()
                # Bring dialog to front
                root.attributes('-topmost', True)
                root.focus_force()
                
                if multi:
                    file_paths = filedialog.askopenfilenames(
                        title="Select Videos",
                        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v"), ("All files", "*.*")]
                    )
                    if file_paths:
                        self.app.call_from_thread(callback, list(file_paths))
                else:
                    file_path = filedialog.askopenfilename(
                        title="Select a Video",
                        filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v"), ("All files", "*.*")]
                    )
                    if file_path:
                        self.app.call_from_thread(callback, file_path)
                
                root.destroy()
            except Exception as e:
                self.app.call_from_thread(self.write_log, f"❌ Dialog Error: {str(e)}\n")

        thread = threading.Thread(target=run_dialog, daemon=True)
        thread.start()

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

        path = clean_video_path(self.video_path)

        if not os.path.exists(path):
            self.write_log(f"❌ File not found: {path}\n")
            return

        duration = await get_video_duration(path)
        if duration is not None:
            self._video_duration = duration
            self.write_log(f"✅ Video loaded: {os.path.basename(path)}\n")
            self.write_log(f"⏱️ Duration: {format_hhmmss(duration)}\n")
        else:
            self.write_log(f"⚠️ Could not get video duration\n")

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
