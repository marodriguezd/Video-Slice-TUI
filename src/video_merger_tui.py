"""
Video Merger TUI
Single-file Textual app to select multiple videos and merge them into a single file using ffmpeg.

Requirements:
  pip install textual rich
  ffmpeg must be installed and available in PATH

Usage:
  python video_merger_tui.py
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








class VideoMergerApp(App):
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._videos = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main"):
            with Vertical():
                yield Static("🎬 Video Merger TUI", id="title")
                
                # File input section
                with Horizontal(id="filebox"):
                    yield Button("➕ Add Videos", id="add_videos_btn", variant="success")
                
                # Videos table section
                with Vertical(id="videos"):
                    yield Static("📋 Videos to Merge:", id="videos_header")
                    self.videos_table = DataTable()
                    self.videos_table.add_columns("Path")
                    self.videos_table.cursor_type = "row"
                    yield self.videos_table
                    
                    # Actions
                    with Horizontal(id="actions"):
                        yield Button("🗑️ Delete", id="del_video_btn", variant="error")
                        yield Button("🚀 Merge Videos", id="export_btn", variant="success")
                
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



    def open_file_dialog(self):
        """Open tkinter file dialog to select one or more videos."""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        file_paths = filedialog.askopenfilenames(
            title="Select one or more videos",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v"),
                ("All files", "*.*")
            ]
        )
        root.destroy()
        return file_paths



    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn = event.button
        if btn.id == "add_videos_btn":
            file_paths = self.open_file_dialog()
            if file_paths:
                self.add_videos(file_paths)
        
        elif btn.id == "del_video_btn":
            self.delete_selected_video()
        
        elif btn.id == "export_btn":
            asyncio.create_task(self.merge_videos())
    
    def add_videos(self, file_paths: list[str]) -> None:
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
            
            # Remove from list
            self._videos.remove(path_to_delete)
            
            # Clear and rebuild table
            self.videos_table.clear()
            for path in self._videos:
                self.videos_table.add_row(path)
            
            self.write_log(f"🗑️ Deleted video: {os.path.basename(path_to_delete)}\n")
            
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

    async def merge_videos(self):
        if len(self._videos) < 2:
            self.write_log("⚠️ You need at least two videos to merge\n")
            return

        # Use the directory of the first video as the base for the output
        base_dir = os.path.dirname(self._videos[0])
        out_dir = os.path.join(base_dir, "merged_output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "merged_video.mp4")

        # Create a temporary file with the list of videos
        list_path = os.path.join(out_dir, "filelist.txt")
        with open(list_path, "w") as f:
            for video_path in self._videos:
                f.write(f"file '{video_path}'\n")

        # Show status label
        self.progress_label.update("🔄 Merging videos...")

        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
            "-c", "copy", out_path
        ]

        success = await self.run_command(cmd, 1, out_path)

        # Update status label
        if success:
            self.progress_label.update("✅ Merge complete!")
        else:
            self.progress_label.update("❌ Merge failed.")

        # Hide status label after a delay
        await asyncio.sleep(3)
        self.progress_label.update("")

        self.write_log(f"\n{'='*50}\n")
        if success:
            self.write_log(f"✅ Merge complete!\n")
            self.write_log(f"📁 Merged video saved in: {out_path}\n")
        else:
            self.write_log(f"❌ Merge failed.\n")
        self.write_log(f"{ '='*50}\n")

        # Clean up the temporary file
        os.remove(list_path)

    async def run_command(self, cmd, idx, out_path):
        try:
            self.write_log(f"[Task #{idx}] ⏳ Processing... {os.path.basename(out_path)}\n")
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                self.write_log(f"[Task #{idx}] ❌ FFmpeg Error\n")
                err = stderr.decode(errors='ignore')[:500]
                self.write_log(f"{err}\n")
                return False
            else:
                file_size = os.path.getsize(out_path) / (1024 * 1024)  # MB
                self.write_log(f"[Task #{idx}] ✅ Completed ({file_size:.1f} MB)\n")
                return True
        except Exception as exc:
            self.write_log(f"[Task #{idx}] ❌ Exception: {exc}\n")
            return False


def main():
    app = VideoMergerApp()
    app.run()


if __name__ == '__main__':
    main()