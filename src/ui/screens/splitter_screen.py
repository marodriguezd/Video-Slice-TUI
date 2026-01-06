"""Splitter screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static, DataTable, Checkbox, ProgressBar
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import format_hhmmss, run_ffmpeg, Range


class SplitterScreen(ScreenBase):
    """Screen for splitting videos into equal chunks."""

    CSS = (
        ScreenBase.CSS
        + """
    .splitter-title {
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
        self._ranges = []
        self._next_idx = 1

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("✂️ VIDEO SPLITTER", classes="splitter-title")

            with Vertical(classes="input-section"):
                yield Label("📁 Video Source")
                self.file_input = Input(
                    placeholder="Path to video file..."
                )
                yield self.file_input
                
                with Horizontal(classes="control-row"):
                    yield Button("Add Video", id="load_btn", variant="primary")
                    yield Button("Clear All", id="clear_all_btn", variant="error")

                with Horizontal(classes="time-inputs"):
                    with Vertical(classes="input-group"):
                        yield Label("⏱️ Chunk Duration (minutes)")
                        self.duration_input = Input(placeholder="e.g. 10")
                        yield self.duration_input

                    with Vertical(classes="input-group"):
                        yield Label("") # spacer
                        yield Button("Generate Chunks", id="split_btn", variant="success")

            with Vertical(classes="data-section"):
                yield Static("📋 CHUNK QUEUE", classes="section-header")
                self.ranges_table = DataTable()
                self.ranges_table.add_columns("#", "Start", "End", "Duration")
                self.ranges_table.cursor_type = "row"
                yield self.ranges_table

                with Horizontal(classes="control-row"):
                    self.reencode_cb = Checkbox(
                        "Precise Cut (Slower)", value=False
                    )
                    yield self.reencode_cb
                    yield Button("START EXPORT", id="export_btn", variant="success")

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

        if btn.id == "load_btn":
            def handle_file(file_path):
                if file_path:
                    self.try_load_path(file_path)
                else:
                    self.write_log("ℹ️ Use the input or the button to select a file\n")

            self.open_file_dialog(handle_file)

        elif btn.id == "clear_all_btn":
            self.try_load_path("")
            self.write_log("🗑️ Video cleared\n")

        elif btn.id == "split_btn":
            self.split_video()

        elif btn.id == "export_btn":
            asyncio.create_task(self.export_clips())

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input == self.file_input:
            value = event.value.strip()
            # If it looks like a PowerShell/CMD path or has extra artifacts
            if value.startswith('&') or ('"' in value and not (value.startswith('"') and value.endswith('"'))):
                cleaned = self.try_load_path(value)
                if cleaned:
                    self.write_log(f"🧹 Path cleaned and loaded\n")

    def on_video_cleared(self) -> None:
        """Reset internal state and clear UI tables."""
        self._ranges = []
        self._next_idx = 1
        if hasattr(self, "ranges_table"):
            self.ranges_table.clear()

    def split_video(self):
        try:
            if not self.video_path or not self._video_duration:
                self.write_log("⚠️ Load a video first\n")
                return

            duration_str = self.duration_input.value.strip()
            if not duration_str:
                self.write_log("⚠️ Please enter a chunk duration\n")
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

                self.write_log(
                    f"✅ Chunk #{r.idx}: {format_hhmmss(r.start)} → "
                    f"{format_hhmmss(r.end)} ({int(r.duration())}s)\n"
                )

                start_time = end_time

        except Exception as exc:
            self.write_log(f"❌ Error: {exc}\n")

    async def export_clips(self):
        if not self.video_path:
            self.write_log("⚠️ No video loaded\n")
            return

        video_path = clean_video_path(self.video_path)

        if not os.path.exists(video_path):
            self.write_log(f"❌ File not found for exporting\n")
            return

        if not self._ranges:
            self.write_log("⚠️ No chunks to export\n")
            return

        out_dir = os.path.join(
            os.path.dirname(video_path) or os.getcwd(), "clips_output"
        )
        os.makedirs(out_dir, exist_ok=True)

        use_reencode = self.reencode_cb.value
        total = len(self._ranges)

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)
        self.progress_label.update(f"🔄 Exporting 0/{total} clips...")

        self.write_log(f"\n{'=' * 50}\n")
        self.write_log(f"🚀 Starting export of {total} clips\n")
        self.write_log(f"📁 Destination: {out_dir}\n")
        self.write_log(
            f"⚙️ Mode: {'Re-encode (precise)' if use_reencode else 'Copy (fast)'}\n"
        )
        self.write_log(f"{'=' * 50}\n\n")

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

            await run_ffmpeg(cmd, self.write_log, r.idx, out_path)
            completed += 1

            self.progress_bar.update(progress=completed)
            self.progress_label.update(f"🔄 Exporting {completed}/{total} clips...")

        self.progress_bar.display = False
        self.progress_label.update("")

        self.write_log(f"\n{'=' * 50}\n")
        self.write_log(f"✅ Export complete: {completed}/{total} clips\n")
        self.write_log(f"📁 Clips saved in: {out_dir}\n")
        self.write_log(f"{'=' * 50}\n")


