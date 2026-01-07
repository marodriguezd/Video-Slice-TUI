"""Splitter screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Button,
    Input,
    Label,
    Static,
    DataTable,
    Checkbox,
    ProgressBar,
)
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import format_hhmmss, run_ffmpeg, Range, clean_video_path


class SplitterScreen(ScreenBase):
    """Screen for splitting videos into equal chunks."""

    CSS = (
        ScreenBase.CSS
        + """
    .split-section {
        height: auto;
    }
    .split-inputs {
        height: auto;
        margin: 1 0;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ranges = []
        self._next_idx = 1
        self._custom_output_path = None

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("✂️ VIDEO SPLITTER", classes="screen-title")

            with Vertical(classes="split-section"):
                yield Label("⏱️ Chunk Duration", classes="section-header")
                with Horizontal(classes="split-inputs"):
                    with Vertical(classes="input-group"):
                        yield Label("⏱️ Duration (minutes)")
                        self.duration_input = Input(placeholder="e.g. 10")
                        yield self.duration_input

                    with Vertical(classes="input-group"):
                        yield Label("")
                        yield Button(
                            "Generate Chunks", id="split_btn", variant="success"
                        )

            with Vertical(classes="data-section"):
                yield Static("📋 CHUNK QUEUE", classes="section-header")
                self.ranges_table = DataTable()
                self.ranges_table.add_columns("#", "Start", "End", "Duration")
                self.ranges_table.cursor_type = "row"
                yield self.ranges_table

            with Horizontal(classes="export-row"):
                self.reencode_cb = Checkbox("Precise Cut (Slower)", value=False)
                yield self.reencode_cb
                yield Button("START EXPORT", id="export_btn", variant="success")

            with Vertical(classes="progress-section"):
                self.progress_label = Static("")
                yield self.progress_label
                self.progress_bar = ProgressBar(total=100, show_eta=False)
                self.progress_bar.display = False
                yield self.progress_bar

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button

        if btn.id == "split_btn":
            self.split_video()

        elif btn.id == "export_btn":
            asyncio.create_task(self.export_clips())

    def on_video_cleared(self) -> None:
        """Reset internal state and clear UI tables."""
        self._ranges = []
        self._next_idx = 1
        if hasattr(self, "ranges_table"):
            self.ranges_table.clear()

    def _get_default_output_path(self) -> str:
        """Get the default output directory path."""
        if self.video_path:
            video_dir = os.path.dirname(self.video_path) or os.getcwd()
        else:
            video_dir = os.getcwd()
        return os.path.join(video_dir, "clips_output")

    def _get_output_directory(self) -> str:
        """Get the output directory, either custom or default."""
        if self._custom_output_path:
            return self._custom_output_path
        return self._get_default_output_path()

    def _validate_output_path(self, path: str) -> tuple[bool, str]:
        """Validate that the output path is writable."""
        if not os.path.exists(path):
            return False, f"Folder does not exist: {path}"
        if not os.access(path, os.W_OK):
            return False, f"Folder is not writable: {path}"
        return True, ""

    async def load_video_info(self):
        """Load video info from hub's shared video path."""
        if not self.video_path:
            return

        path = self.video_path

        if not os.path.exists(path):
            self.show_status(f"❌ File not found: {path}", "error")
            return

        from logic import get_video_duration, format_hhmmss

        duration = await get_video_duration(path)
        if duration is not None:
            self._video_duration = duration
            self.show_status(
                f"✅ {os.path.basename(path)} loaded - {format_hhmmss(duration)}",
                "success",
            )
        else:
            self.show_status("⚠️ Could not get video duration", "warning")

    def split_video(self):
        try:
            if not self.video_path or not self._video_duration:
                self.show_status("⚠️ Load a video first", "warning")
                return

            duration_str = self.duration_input.value.strip()
            if not duration_str:
                self.show_status("⚠️ Please enter a chunk duration", "warning")
                return

            chunk_minutes = float(duration_str)
            chunk_seconds = chunk_minutes * 60

            self._ranges = []
            self.ranges_table.clear()
            self._next_idx = 1

            start_time = 0.0
            while start_time < self._video_duration:
                end_time = min(start_time + chunk_seconds, self._video_duration)

                r = Range(start_time, end_time, self._next_idx)
                self._next_idx += 1
                self._ranges.append(r)

                self.ranges_table.add_row(
                    str(r.idx),
                    format_hhmmss(r.start),
                    format_hhmmss(r.end),
                    f"{int(r.duration())}s",
                )

                start_time = end_time

            self.show_status(f"✅ Generated {len(self._ranges)} chunks", "success")

        except Exception as exc:
            self.show_status(f"❌ Error: {exc}", "error")

    async def export_clips(self):
        if not self.video_path:
            self.show_status("⚠️ No video loaded", "warning")
            return

        video_path = clean_video_path(self.video_path)

        if not os.path.exists(video_path):
            self.show_status("❌ File not found for exporting", "error")
            return

        if not self._ranges:
            self.show_status("⚠️ No chunks to export", "warning")
            return

        out_dir = self._get_output_directory()

        valid, error_msg = self._validate_output_path(out_dir)
        if not valid:
            self.show_status(f"❌ {error_msg}", "error")
            return

        os.makedirs(out_dir, exist_ok=True)

        use_reencode = self.reencode_cb.value
        total = len(self._ranges)

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)
        self.progress_label.update(f"🔄 Exporting 0/{total} clips...")

        self.show_status(f"🚀 Starting export of {total} clips to {out_dir}", "success")

        completed = 0
        for r in self._ranges:
            out_name = f"clip_{r.idx}_{format_hhmmss(r.start).replace(':', '-')}_to_{format_hhmmss(r.end).replace(':', '-')}.mp4"
            out_path = os.path.join(out_dir, out_name)
            duration = r.end - r.start

            if use_reencode:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(r.start),
                    "-i",
                    video_path,
                    "-t",
                    str(duration),
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    out_path,
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(r.start),
                    "-i",
                    video_path,
                    "-t",
                    str(duration),
                    "-c",
                    "copy",
                    out_path,
                ]

            await run_ffmpeg(cmd, self._ffmpeg_log, r.idx, out_path)
            completed += 1

            self.progress_bar.update(progress=completed)
            self.progress_label.update(f"🔄 Exporting {completed}/{total} clips...")

        self.progress_bar.display = False
        self.progress_label.update("")

        self.show_status(
            f"✅ Export complete: {completed}/{total} clips saved in {out_dir}",
            "success",
        )

    def _ffmpeg_log(self, text: str):
        pass
