"""Clipper screen for Video Slice TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static, DataTable, Checkbox, ProgressBar
from textual import work
import asyncio
import os

from ui.components import ScreenBase
from logic import parse_time, format_hhmmss, run_ffmpeg, Range


class ClipperScreen(ScreenBase):
    """Screen for clipping videos into custom ranges."""

    CSS = (
        ScreenBase.CSS
        + """
    .clipper-title {
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
            yield Static("🔪 VIDEO CLIPPER", classes="clipper-title")

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
                        yield Label("⏱️ Start Time")
                        self.start_input = Input(placeholder="00:00:00")
                        yield self.start_input

                    with Vertical(classes="input-group"):
                        yield Label("⏱️ End Time")
                        self.end_input = Input(placeholder="End of video")
                        yield self.end_input

                    with Vertical(classes="input-group", id="add-btn-group"):
                        yield Label("") # spacer
                        yield Button("Add Range", id="add_range_btn", variant="success")

            with Vertical(classes="data-section"):
                yield Static("📋 CLIP QUEUE", classes="section-header")
                self.ranges_table = DataTable()
                self.ranges_table.add_columns("#", "Start", "End", "Duration")
                self.ranges_table.cursor_type = "row"
                yield self.ranges_table

                with Horizontal(classes="control-row"):
                    yield Button("Remove Selected", id="del_btn", variant="error")
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

        elif btn.id == "add_range_btn":
            self.add_range()

        elif btn.id == "del_btn":
            self.delete_selected_range()

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

    def add_range(self) -> None:
        start = self.start_input.value.strip()
        end = self.end_input.value.strip()

        if not start:
            self.write_log("⚠️ You must specify at least the start time\n")
            return

        try:
            s = parse_time(start)

            if not end:
                if self._video_duration is None:
                    self.write_log("⚠️ Specify end time or load video to use auto end\n")
                    return
                e = self._video_duration
                self.write_log(f"ℹ️ Using auto end: {format_hhmmss(e)}\n")
            else:
                e = parse_time(end)

            if not self.video_path:
                self.write_log("⚠️ Load a video first\n")
                return

            r = Range(s, e, self._next_idx)
            self._next_idx += 1
            self._ranges.append(r)

            self.ranges_table.add_row(
                str(r.idx),
                format_hhmmss(r.start),
                format_hhmmss(r.end),
                f"{int(r.duration())}s",
            )

            self.write_log(
                f"✅ Range #{r.idx}: {format_hhmmss(r.start)} → "
                f"{format_hhmmss(r.end)} ({int(r.duration())}s)\n"
            )

            self.start_input.value = ""
            self.end_input.value = ""
            self.start_input.focus()

        except Exception as exc:
            self.write_log(f"❌ Error: {exc}\n")

    def delete_selected_range(self):
        try:
            if self.ranges_table.row_count == 0:
                self.write_log("⚠️ No ranges to delete\n")
                return

            cursor_row = self.ranges_table.cursor_row
            row = self.ranges_table.get_row_at(cursor_row)
            idx = int(row[0])

            self._ranges = [r for r in self._ranges if r.idx != idx]

            self.ranges_table.clear()
            for r in self._ranges:
                self.ranges_table.add_row(
                    str(r.idx),
                    format_hhmmss(r.start),
                    format_hhmmss(r.end),
                    f"{int(r.duration())}s",
                )

            self.write_log(f"🗑️ Deleted range #{idx}\n")

        except Exception as exc:
            self.write_log(f"❌ Error deleting: {exc}\n")

    async def export_clips(self):
        if not self.video_path:
            self.write_log("⚠️ No video loaded\n")
            return

        video_path = clean_video_path(self.video_path)

        if not os.path.exists(video_path):
            self.write_log(f"❌ File not found for exporting\n")
            return

        if not self._ranges:
            self.write_log("⚠️ No ranges to export\n")
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


