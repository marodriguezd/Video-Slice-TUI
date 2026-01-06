from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import TabbedContent, TabPane, Static
from textual.reactive import reactive
from textual.message import Message

from ui.screens.clipper_screen import ClipperScreen
from ui.screens.splitter_screen import SplitterScreen
from ui.screens.merger_screen import MergerScreen
from logic.input_parsing import clean_pasted_path


class HubScreen(Container):
    """Main hub screen with tab navigation using TabbedContent."""

    shared_video_path = reactive("", always_update=True)

    CSS = """
    HubScreen {
        align: center middle;
        background: $boost;
    }
    #hub-container {
        width: 100%;
        height: 100%;
        padding: 0;
    }
    #app-header {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: $primary;
        color: $text;
        border-bottom: thick $accent;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 1 2;
    }
    """

    class UpdateVideoPath(Message):
        """Message to update the shared video path."""
        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._active_tab_id = "clipper"

    def compose(self) -> ComposeResult:
        with Vertical(id="hub-container"):
            yield Static("🎬 VIDEO SLICE TUI", id="app-header")
            with TabbedContent(initial="clipper"):
                with TabPane("🔪 Clipper", id="clipper"):
                    yield ClipperScreen(id="clipper_screen")
                with TabPane("✂️ Splitter", id="splitter"):
                    yield SplitterScreen(id="splitter_screen")
                with TabPane("🔗 Merger", id="merger"):
                    yield MergerScreen(id="merger_screen")

    @property
    def active_tab(self) -> str:
        return self.query_one(TabbedContent).active

    @active_tab.setter
    def active_tab(self, value: str) -> None:
        self.query_one(TabbedContent).active = value

    def on_paste(self, event: Message) -> None:
        """Handle drag and drop (terminal paste)."""
        # Event is 'textual.events.Paste' but usually we just handle it via on_paste
        path = clean_pasted_path(event.text)
        if path:
            self.shared_video_path = path

    def watch_shared_video_path(self, new_path: str) -> None:
        """Propagate shared video path to all screens."""
        for screen_id in ["clipper_screen", "splitter_screen"]:
            try:
                screen = self.query_one(f"#{screen_id}")
                if screen.video_path != new_path:
                    screen.video_path = new_path
            except:
                pass
        
        # Merger handles it differently (adds to list)
        try:
            merger = self.query_one("#merger_screen")
            if new_path and new_path not in merger._videos:
                merger.add_videos([new_path])
            elif not new_path:
                merger._videos = []
                merger.videos_table.clear()
        except:
            pass

    def on_hub_screen_update_video_path(self, message: UpdateVideoPath) -> None:
        """Handle update message from child screens."""
        self.shared_video_path = message.path
