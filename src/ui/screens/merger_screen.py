"""Merger screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static, DataTable, Label, ProgressBar
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import run_ffmpeg


class MergerScreen(ScreenBase):
    """Screen for merging multiple videos into one."""

    CSS = (
        ScreenBase.CSS
        + """
    .merger-title {
        text-align: center;
        text-style: bold;
        margin: 1 0;
        color: $accent;
        background: $boost;
        border: double $accent;
    }
    .input-section {
        height: auto;
        border: tall $primary;
        margin-bottom: 1;
        padding: 1;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._videos = []

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("🔗 VIDEO MERGER", classes="merger-title")

            with Vertical(classes="input-section"):
                yield Label("📁 Source Videos")
                with Horizontal(classes="control-row"):
                    yield Button("Add Video(s)", id="add_videos_btn", variant="primary")
                    yield Button("Clear All", id="clear_all_btn", variant="error")

            with Vertical(classes="data-section"):
                yield Static("📋 MERGE QUEUE", classes="section-header")
                self.videos_table = DataTable()
                self.videos_table.add_columns("Path")
                self.videos_table.cursor_type = "row"
                yield self.videos_table

                with Horizontal(classes="control-row"):
                    yield Button("Remove Selected", id="del_video_btn", variant="error")
                    yield Button("START MERGE", id="export_btn", variant="success")

            with Vertical(classes="log-section"):
                yield Static("📝 LOGS", classes="section-header")
                self.log_box = Static("")
                yield self.log_box

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button

        if btn.id == "add_videos_btn":
            def handle_files(file_paths):
                if file_paths:
                    # FileSelector currently returns string or None. 
                    # If multi=True, it should ideally return a list.
                    # For now, let's assume it returns a string if one selected, 
                    # or we might need to adjust FileSelector to handle multi-select properly.
                    if isinstance(file_paths, str):
                        self.add_videos([file_paths])
                    else:
                        self.add_videos(file_paths)
            
            self.open_file_dialog(handle_files, multi=True)

        elif btn.id == "clear_all_btn":
            self._videos = []
            self.videos_table.clear()
            self.write_log("🗑️ All videos cleared from queue\n")
            
            # Notify Hub to clear shared state too
            from ui.screens.hub_screen import HubScreen
            self.post_message(HubScreen.UpdateVideoPath(""))

        elif btn.id == "del_video_btn":
            self.delete_selected_video()

        elif btn.id == "export_btn":
            asyncio.create_task(self.merge_videos())

    def add_videos(self, file_paths) -> None:
        for path in file_paths:
            self._videos.append(path)
            self.videos_table.add_row(path)
            self.write_log(f"✅ Added: {os.path.basename(path)}\n")

    def delete_selected_video(self):
        try:
            if self.videos_table.row_count == 0:
                self.write_log("⚠️ No videos to delete\n")
                return

            cursor_row = self.videos_table.cursor_row
            row = self.videos_table.get_row_at(cursor_row)
            path_to_delete = row[0]

            self._videos.remove(path_to_delete)

            self.videos_table.clear()
            for path in self._videos:
                self.videos_table.add_row(path)

            self.write_log(f"🗑️ Deleted: {os.path.basename(path_to_delete)}\n")

        except Exception as exc:
            self.write_log(f"❌ Error deleting: {exc}\n")

    async def merge_videos(self):
        if len(self._videos) < 2:
            self.write_log("⚠️ You need at least two videos to merge\n")
            return

        base_dir = os.path.dirname(self._videos[0])
        out_dir = os.path.join(base_dir, "merged_output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "merged_video.mp4")

        list_path = os.path.join(out_dir, "filelist.txt")
        with open(list_path, "w") as f:
            for video_path in self._videos:
                f.write(f"file '{video_path}'\n")

        self.progress_label.update("🔄 Merging videos...")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_path,
            "-c",
            "copy",
            out_path,
        ]

        success = await run_ffmpeg(cmd, self.write_log, 1, out_path)

        if success:
            self.progress_label.update("✅ Merge complete!")
        else:
            self.progress_label.update("❌ Merge failed.")

        await asyncio.sleep(3)
        self.progress_label.update("")

        self.write_log(f"\n{'=' * 50}\n")
        if success:
            self.write_log(f"✅ Merge complete!\n")
            self.write_log(f"📁 Merged video saved in: {out_path}\n")
        else:
            self.write_log(f"❌ Merge failed.\n")
        self.write_log(f"{'=' * 50}\n")

        try:
            os.remove(list_path)
        except:
            pass


