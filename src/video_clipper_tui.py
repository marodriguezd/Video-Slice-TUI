"""
Video Clipper TUI
Single-file Textual app to load a video (path passed as argument or chosen in app),
add multiple time ranges, and export clips using ffmpeg.

Requirements:
  pip install textual rich
  ffmpeg must be installed and available in PATH

Usage:
  python video_clipper_tui.py /path/to/video.mp4
"""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Input, Button, Static, DataTable, Checkbox, Label, ProgressBar
from textual.reactive import reactive
from textual.message import Message
import asyncio
import sys
import os
import shlex
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog


def parse_time(s: str) -> float:
    """Parse a time string into seconds.
    Accepts HH:MM:SS, MM:SS, SS, or decimal hours (e.g. 3.5 -> 3h30m)
    """
    s = s.strip()
    if not s:
        raise ValueError("Empty time")
    # detect decimal hours (e.g. 3.5)
    if s.replace('.', '', 1).replace('-', '', 1).isdigit() and ':' not in s:
        if '.' in s:
            hours = float(s)
            return hours * 3600.0
        else:
            return float(s)
    parts = s.split(':')
    parts = [p for p in parts if p != '']
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        minutes = float(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Can't parse time: {s}")


def format_hhmmss(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"


class Range:
    def __init__(self, start_s: float, end_s: float, idx: int):
        if end_s <= start_s:
            raise ValueError("End must be after start")
        self.start = start_s
        self.end = end_s
        self.idx = idx

    def duration(self):
        return self.end - self.start


class AddRange(Message):
    def __init__(self, start: str, end: str):
        super().__init__()
        self.start = start
        self.end = end


class VideoClipperApp(App):
    CSS = """
    Screen {
      align: center middle;
    }
    #main {
      width: 90%;
      height: 90%;
      border: round $primary;
      padding: 1 2;
    }
    #title {
      text-align: center;
      text-style: bold;
      margin-bottom: 1;
    }
    #filebox {
      height: auto;
      margin-bottom: 1;
    }
    #time_inputs {
      height: auto;
      margin-bottom: 1;
    }
    .time_group {
      width: 1fr;
      height: auto;
    }
    #ranges {
      height: 1fr;
      border: round $accent;
      padding: 1;
      margin-bottom: 1;
    }
    #ranges_header {
      text-style: bold;
      margin-bottom: 1;
    }
    DataTable {
      height: 1fr;
      margin-bottom: 1;
    }
    #actions {
      height: auto;
    }
    #log_section {
      height: 10;
      border: round $accent;
      padding: 1;
    }
    #log_title {
      text-style: bold;
    }
    #progress_section {
      height: 3;
      margin-bottom: 1;
    }
    ProgressBar {
      margin: 0 1;
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
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    video_path = reactive(None)

    def __init__(self, video_path_arg: str = None, **kwargs):
        super().__init__(**kwargs)
        self.video_path = video_path_arg
        self._ranges = []
        self._next_idx = 1
        self._video_duration = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main"):
            with Vertical():
                yield Static("🎬 Video Clipper TUI", id="title")
                
                # File input section
                with Horizontal(id="filebox"):
                    self.file_input = Input(
                        value=self.video_path or "", 
                        placeholder="Video path (or use the button to select)"
                    )
                    yield self.file_input
                    yield Button("📁 Select", id="load_btn", variant="primary")
                
                # Time inputs section
                with Horizontal(id="time_inputs"):
                    with Vertical(classes="time_group"):
                        yield Label("⏱️ Start (HH:MM:SS, MM:SS, SS or decimal hours)")
                        self.start_input = Input(placeholder="e.g., 3:50 or 1.5")
                        yield self.start_input
                    
                    with Vertical(classes="time_group"):
                        yield Label("⏱️ End (empty = until the end)")
                        self.end_input = Input(placeholder="e.g., 4:10 (optional)")
                        yield self.end_input
                    
                    yield Button("➕ Add", id="add_range_btn", variant="success")
                
                # Ranges table section
                with Vertical(id="ranges"):
                    yield Static("📋 Added Ranges:", id="ranges_header")
                    self.ranges_table = DataTable()
                    self.ranges_table.add_columns("#", "Start", "End", "Duration")
                    self.ranges_table.cursor_type = "row"
                    yield self.ranges_table
                    
                    # Actions
                    with Horizontal(id="actions"):
                        yield Button("🗑️ Delete", id="del_btn", variant="error")
                        self.reencode_cb = Checkbox("🎯 Re-encode (precise cut)", value=False)
                        yield self.reencode_cb
                        yield Button("🚀 Export Clips", id="export_btn", variant="success")
                
                # Log section
                with Vertical(id="log_section"):
                    yield Static("📝 Logs:", id="log_title")
                    self.log_box = Static("")
                    yield self.log_box
                
                # Progress section
                with Vertical(id="progress_section"):
                    self.progress_label = Static("")
                    yield self.progress_label
                    self.progress_bar = ProgressBar(total=100, show_eta=False)
                    self.progress_bar.display = False
                    yield self.progress_bar
        
        yield Footer()

    async def on_mount(self) -> None:
        if self.video_path:
            await self.load_video_info()

    def open_file_dialog(self):
        """Open tkinter file dialog to select video."""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        file_path = filedialog.askopenfilename(
            title="Select a video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("All files", "*.*")
            ]
        )
        root.destroy()
        return file_path

    async def load_video_info(self):
        """Get video duration using ffprobe"""
        # Clean the path - remove quotes and whitespace
        clean_path = self.video_path.strip().strip('"').strip("'").strip()
        
        # Try to resolve absolute path if it doesn't exist as-is
        if not os.path.exists(clean_path):
            # Try expanding user path
            expanded = os.path.expanduser(clean_path)
            if os.path.exists(expanded):
                clean_path = expanded
            else:
                # Try as absolute path
                abs_path = os.path.abspath(clean_path)
                if os.path.exists(abs_path):
                    clean_path = abs_path
        
        if not os.path.exists(clean_path):
            self.write_log(f"❌ File not found\n")
            self.write_log(f"   Searched path: {clean_path}\n")
            self.write_log(f"   Verify that the file exists\n")
            return
        
        # Store the clean path
        self.video_path = clean_path
        
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                clean_path
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                duration_str = stdout.decode().strip()
                self._video_duration = float(duration_str)
                self.write_log(f"✅ Video loaded: {os.path.basename(clean_path)}\n")
                self.write_log(f"⏱️ Total duration: {format_hhmmss(self._video_duration)}\n")
            else:
                err = stderr.decode(errors='ignore')[:300]
                self.write_log(f"⚠️ ffprobe error:\n{err}\n")
                self.write_log(f"   You can still add ranges by specifying start and end\n")
                self._video_duration = None
        except Exception as exc:
            self.write_log(f"⚠️ Error: {exc}\n")
            self.write_log(f"   You can still add ranges by specifying start and end\n")
            self._video_duration = None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button
        if btn.id == "load_btn":
            # First, try with manual input
            path = self.file_input.value.strip().strip('"').strip("'")
            if path and os.path.exists(path):
                self.video_path = path
                self.file_input.value = f'"{path}"'
                asyncio.create_task(self.load_video_info())
                return
            
            # Otherwise, open the dialog
            file_path = self.open_file_dialog()
            if file_path:
                self.video_path = file_path
                self.file_input.value = f'"{file_path}"'
                asyncio.create_task(self.load_video_info())
            else:
                self.write_log("ℹ️ Use the input or the button to select a file\n")
        
        elif btn.id == "add_range_btn":
            start = self.start_input.value.strip()
            end = self.end_input.value.strip()
            if not start:
                self.write_log("⚠️ You must specify at least the start time\n")
                return
            self.add_range(start, end)
        
        elif btn.id == "del_btn":
            self.delete_selected_range()
        
        elif btn.id == "export_btn":
            asyncio.create_task(self.export_clips())
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Auto-format file path when pasted/dragged"""
        if event.input == self.file_input:
            value = event.value.strip()
            
            # Skip if empty or already has quotes
            if not value or (value.startswith('"') and value.endswith('"')):
                return
            
            # If it looks like a file path (contains : or \ or /) and doesn't have quotes, add them
            if (':' in value or '\\' in value or '/' in value) and not value.startswith('"'):
                # Add quotes around the path
                self.file_input.value = f'"{value}"'

    def add_range(self, start_str: str, end_str: str) -> None:
        try:
            s = parse_time(start_str)
            
            # If no end time specified
            if not end_str:
                if self._video_duration is None:
                    self.write_log("⚠️ Specify end time or load video to use auto end\n")
                    return
                e = self._video_duration
                self.write_log(f"ℹ️ Using auto end: {format_hhmmss(e)}\n")
            else:
                e = parse_time(end_str)
            
            # Validate that we have a video path
            if not self.video_path:
                self.write_log("⚠️ Load a video first\n")
                return
            
            r = Range(s, e, self._next_idx)
            self._next_idx += 1
            self._ranges.append(r)
            
            # Add to table
            self.ranges_table.add_row(
                str(r.idx), 
                format_hhmmss(r.start), 
                format_hhmmss(r.end), 
                f"{int(r.duration())}s"
            )
            
            self.write_log(
                f"✅ Range #{r.idx}: {format_hhmmss(r.start)} → "
                f"{format_hhmmss(r.end)} ({int(r.duration())}s)\n"
            )
            
            # Clear inputs
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
            
            # Remove from list
            self._ranges = [r for r in self._ranges if r.idx != idx]
            
            # Clear and rebuild table
            self.ranges_table.clear()
            for r in self._ranges:
                self.ranges_table.add_row(
                    str(r.idx), 
                    format_hhmmss(r.start), 
                    format_hhmmss(r.end), 
                    f"{int(r.duration())}s"
                )
            
            self.write_log(f"🗑️ Deleted range #{idx}\n")
            
        except Exception as exc:
            self.write_log(f"❌ Error deleting: {exc}\n")

    def write_log(self, text: str):
        try:
            # Get current content from the Static widget
            current = str(self.log_box.render())
        except:
            current = ""
        
        new_text = current + text
        
        # Keep only last 20 lines
        lines = new_text.split('\n')
        if len(lines) > 20:
            lines = lines[-20:]
            new_text = '\n'.join(lines)
        
        self.log_box.update(new_text)

    async def export_clips(self):
        if not self.video_path:
            self.write_log("⚠️ No video loaded\n")
            return
        
        # Ensure path is clean (no quotes)
        video_path = self.video_path.strip().strip('"').strip("'").strip()
        
        if not os.path.exists(video_path):
            self.write_log(f"❌ File not found for exporting\n")
            self.write_log(f"   Path: {video_path}\n")
            return
        
        if not self._ranges:
            self.write_log("⚠️ No ranges to export\n")
            return
        
        out_dir = os.path.join(os.path.dirname(video_path) or os.getcwd(), "clips_output")
        os.makedirs(out_dir, exist_ok=True)
        
        use_reencode = self.reencode_cb.value
        total = len(self._ranges)
        
        # Show progress bar
        self.progress_bar.display = True
        self.progress_bar.update(total=total, progress=0)
        self.progress_label.update(f"🔄 Exporting 0/{total} clips...")
        
        self.write_log(f"\n{'='*50}\n")
        self.write_log(f"🚀 Starting export of {total} clips\n")
        self.write_log(f"📁 Destination: {out_dir}\n")
        self.write_log(f"⚙️ Mode: {'Re-encode (precise)' if use_reencode else 'Copy (fast)'}\n")
        self.write_log(f"{ '='*50}\n\n")
        
        completed = 0
        for r in self._ranges:
            out_name = f"clip_{r.idx}_{format_hhmmss(r.start).replace(':','-')}_to_{format_hhmmss(r.end).replace(':','-')}.mp4"
            out_path = os.path.join(out_dir, out_name)
            duration = r.end - r.start
            
            if use_reencode:
                cmd = [
                    "ffmpeg", "-y", "-ss", str(r.start), "-i", video_path,
                    "-t", str(duration), "-c:v", "libx264", "-c:a", "aac", out_path
                ]
            else:
                cmd = [
                    "ffmpeg", "-y", "-ss", str(r.start), "-i", video_path,
                    "-t", str(duration), "-c", "copy", out_path
                ]
            
            success = await self.run_command(cmd, r.idx, out_path)
            completed += 1
            
            # Update progress
            self.progress_bar.update(progress=completed)
            self.progress_label.update(f"🔄 Exporting {completed}/{total} clips...")
        
        # Hide progress bar
        self.progress_bar.display = False
        self.progress_label.update("")
        
        self.write_log(f"\n{'='*50}\n")
        self.write_log(f"✅ Export complete: {completed}/{total} clips\n")
        self.write_log(f"📁 Clips saved in: {out_dir}\n")
        self.write_log(f"{ '='*50}\n")

    async def run_command(self, cmd, idx, out_path):
        try:
            self.write_log(f"[Clip #{idx}] ⏳ Processing... {os.path.basename(out_path)}\n")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                self.write_log(f"[Clip #{idx}] ❌ FFmpeg Error\n")
                err = stderr.decode(errors='ignore')[:500]
                self.write_log(f"{err}\n")
                return False
            else:
                file_size = os.path.getsize(out_path) / (1024 * 1024)  # MB
                self.write_log(f"[Clip #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
                return True
        except Exception as exc:
            self.write_log(f"[Clip #{idx}] ❌ Exception: {exc}\n")
            return False


def main():
    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
    app = VideoClipperApp(video_path_arg=arg)
    app.run()


if __name__ == '__main__':
    main()