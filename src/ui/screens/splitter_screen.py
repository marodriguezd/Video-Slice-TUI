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
from ui.preferences import get_splitter_mode, set_splitter_mode
from logic import (
    format_hhmmss,
    parse_time,
    run_ffmpeg,
    clean_video_path,
    get_output_directory,
    validate_output_path,
    ensure_output_dir_verbose,
    build_cut_command,
    generate_clip_filename,
    SPLITTER_OUTPUT_NAME,
    build_ranges_by_interval,
    build_ranges_by_count,
)


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
    .input-group {
        width: 1fr;
    }
    """
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ranges = []
        self._next_idx = 1
        self._custom_output_path = None
        self._split_mode = "time"

    def _compose_content(self) -> ComposeResult:
        with Vertical(classes="screen-container"):
            yield Static("✂️ MEDIA SPLITTER", classes="screen-title")

            with Vertical(classes="split-section"):
                yield Label("⏱️ Split Settings", classes="section-header")
                with Horizontal(classes="split-inputs"):
                    with Vertical(classes="input-group"):
                        yield Label("🔀 Split mode")
                        self.mode_toggle_btn = Button(
                            "Mode: By Time", id="mode_toggle_btn", variant="primary"
                        )
                        yield self.mode_toggle_btn

                    self.interval_group = Vertical(classes="input-group")
                    with self.interval_group:
                        yield Label("⏱️ Chunk interval (MM:SS or HH:MM:SS)")
                        self.interval_input = Input(placeholder="e.g. 10:00")
                        yield self.interval_input

                    self.count_group = Vertical(classes="input-group")
                    with self.count_group:
                        yield Label("🔢 Total chunks")
                        self.total_chunks_input = Input(placeholder="e.g. 8")
                        yield self.total_chunks_input

                yield Button("Generate Chunks", id="split_btn", variant="success")

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

        if btn.id == "mode_toggle_btn":
            self._toggle_split_mode()
        elif btn.id == "split_btn":
            self.split_video()

        elif btn.id == "export_btn":
            self.export_clips()

    async def on_mount(self) -> None:
        await super().on_mount()
        self._split_mode = get_splitter_mode()
        self._apply_split_mode_ui()

    def _toggle_split_mode(self) -> None:
        self._split_mode = "count" if self._split_mode == "time" else "time"
        self._apply_split_mode_ui()
        set_splitter_mode(self._split_mode)

    def _apply_split_mode_ui(self) -> None:
        is_count_mode = self._split_mode == "count"
        self.mode_toggle_btn.label = (
            "Mode: By Total Chunks" if is_count_mode else "Mode: By Time"
        )
        self.interval_group.display = not is_count_mode
        self.count_group.display = is_count_mode

    def on_video_cleared(self) -> None:
        """Reset internal state and clear UI tables."""
        self._ranges = []
        self._next_idx = 1
        if hasattr(self, "ranges_table"):
            self.ranges_table.clear()

    def _get_output_directory(self) -> str:
        """Get the output directory, either custom or default."""
        return get_output_directory(
            self._custom_output_path, self.video_path, SPLITTER_OUTPUT_NAME
        )

    async def load_video_info(self):
        """Load video info from hub's shared video path."""
        await super().load_video_info()

    def split_video(self):
        try:
            if not self.video_path or not self._video_duration:
                self.show_status("⚠️ Load a video first", "warning")
                return

            self._ranges = []
            self.ranges_table.clear()
            self._next_idx = 1

            if self._split_mode == "count":
                total_chunks_str = self.total_chunks_input.value.strip()
                if not total_chunks_str:
                    self.show_status("⚠️ Please enter total chunks", "warning")
                    return

                total_chunks = int(total_chunks_str)
                if total_chunks <= 0:
                    raise ValueError("Total chunks must be > 0")

                self._ranges = build_ranges_by_count(self._video_duration, total_chunks)
            else:
                interval_str = self.interval_input.value.strip()
                if not interval_str:
                    self.show_status("⚠️ Please enter a chunk interval", "warning")
                    return
                if ":" not in interval_str:
                    raise ValueError("Use MM:SS or HH:MM:SS for interval")

                chunk_seconds = parse_time(interval_str)
                if chunk_seconds <= 0:
                    raise ValueError("Chunk interval must be > 0")

                self._ranges = build_ranges_by_interval(
                    self._video_duration, chunk_seconds
                )

            for r in self._ranges:
                self.ranges_table.add_row(
                    str(r.idx),
                    format_hhmmss(r.start),
                    format_hhmmss(r.end),
                    f"{int(r.duration())}s",
                )

            self.show_status(f"✅ Generated {len(self._ranges)} chunks", "success")

        except Exception as exc:
            self.show_status(f"❌ Error: {exc}", "error")

    @work
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

        valid, error_msg = validate_output_path(out_dir)
        if not valid:
            self.show_status(f"❌ {error_msg}", "error")
            return

        success, error_msg = ensure_output_dir_verbose(out_dir)
        if not success:
            self.show_status(f"❌ Could not create output directory: {error_msg}", "error")
            return

        use_reencode = self.reencode_cb.value
        total = len(self._ranges)

        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)
        self.progress_label.update(f"🔄 Exporting 0/{total} clips...")

        self.show_status(f"🚀 Starting export of {total} clips to {out_dir}", "success")

        completed = 0
        extension = os.path.splitext(video_path)[1] or ".mp4"
        for r in self._ranges:
            out_name = generate_clip_filename(
                r.idx,
                r.start,
                r.end,
                format_hhmmss(r.start),
                format_hhmmss(r.end),
                extension=extension,
            ).replace(":", "-")
            out_path = os.path.join(out_dir, out_name)
            duration = r.end - r.start

            cmd = build_cut_command(
                video_path, r.start, duration, out_path, use_reencode
            )

            await run_ffmpeg(cmd, lambda text: None, r.idx, out_path)
            completed += 1

            self.progress_bar.update(progress=completed)
            self.progress_label.update(f"🔄 Exporting {completed}/{total} clips...")

        self.progress_bar.display = False
        self.progress_label.update("")

        self.show_status(
            f"✅ Export complete: {completed}/{total} clips saved in {out_dir}",
            "success",
        )
