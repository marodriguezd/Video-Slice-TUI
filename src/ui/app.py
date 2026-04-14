"""Video Slice TUI main application."""

import asyncio
import shutil
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from ui.screens import HubScreen


def check_ffmpeg_available() -> tuple[bool, str]:
    """Check if ffmpeg and ffprobe are available on the system."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    
    if not ffmpeg:
        return False, "ffmpeg not found in PATH"
    if not ffprobe:
        return False, "ffprobe not found in PATH"
    return True, ""


class VideoSliceApp(App):
    """Main application class for Video Slice TUI."""

    CSS = """
    Screen {
        align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
    ]

    def __init__(self, start_tab: str = None, video_path: str = None, **kwargs):
        super().__init__(**kwargs)
        self.start_tab = start_tab
        self.start_video_path = video_path
        self._ffmpeg_checked = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HubScreen()
        yield Footer()

    async def on_mount(self) -> None:
        # Check FFmpeg availability
        if not self._ffmpeg_checked:
            self._ffmpeg_checked = True
            available, error = check_ffmpeg_available()
            if not available:
                self.notify(
                    f"⚠️ FFmpeg Warning: {error}.\nPlease install FFmpeg to use this application.",
                    severity="error",
                    timeout=20
                )

        if self.start_video_path and self.start_tab:
            hub = self.query_one(HubScreen)
            hub.active_tab = self.start_tab

            content = hub.query_one(f"#{self.start_tab}_screen")
            if content and hasattr(content, "video_path"):
                content.video_path = self.start_video_path
                await content.load_video_info()
