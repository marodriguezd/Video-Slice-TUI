import os
import threading
import asyncio
import tempfile
import customtkinter as ctk
from tkinter import filedialog, messagebox
from logic.ffmpeg_builder import build_concat_command, MERGER_OUTPUT_NAME
from logic.ffmpeg_utils import run_ffmpeg
from logic.output_utils import get_output_directory, ensure_output_dir_verbose
from ui.preferences import get_last_media_dir, set_last_media_dir

class MergerGUI(ctk.CTkFrame):
    """Merger screen for concatenating multiple videos into one."""

    def __init__(self, master, shared_state, **kwargs):
        super().__init__(master, **kwargs)
        self.shared_state = shared_state
        self.media_list = []

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Title
        self.label = ctk.CTkLabel(self, text="Video Merger", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Controls Area
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.add_button = ctk.CTkButton(self.controls_frame, text="Add Media", command=self._add_media)
        self.add_button.grid(row=0, column=0, padx=10, pady=10)

        self.clear_button = ctk.CTkButton(self.controls_frame, text="Clear All", fg_color="transparent", border_width=2, command=self._clear_media)
        self.clear_button.grid(row=0, column=1, padx=10, pady=10)
        
        self.controls_frame.grid_columnconfigure(2, weight=1)

        # Queue Label
        self.queue_label = ctk.CTkLabel(self, text="Videos to Merge (Order matters):", font=ctk.CTkFont(weight="bold"))
        self.queue_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="sw")

        # Queue Display
        self.queue_frame = ctk.CTkScrollableFrame(self)
        self.queue_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # Export Area
        self.export_button = ctk.CTkButton(self, text="START MERGE", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self._start_merge)
        self.export_button.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.grid(row=6, column=0, padx=20, pady=(0, 10))

        self.is_processing = False

    def _add_media(self):
        initial_dir = get_last_media_dir() or os.path.expanduser("~")
        filenames = filedialog.askopenfilenames(
            initialdir=initial_dir,
            title="Select Video Files to Merge",
            filetypes=(("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v"), ("all files", "*.*"))
        )
        if filenames:
            for f in filenames:
                f_abs = os.path.abspath(f)
                if f_abs not in self.media_list:
                    self.media_list.append(f_abs)
            set_last_media_dir(os.path.dirname(filenames[0]))
            self._update_queue_display()

    def _clear_media(self):
        self.media_list = []
        self._update_queue_display()

    def _update_queue_display(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        for i, path in enumerate(self.media_list):
            row = ctk.CTkFrame(self.queue_frame)
            row.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            row.grid_columnconfigure(0, weight=1)

            lbl = ctk.CTkLabel(row, text=f"{i+1}. {os.path.basename(path)}", tooltip=path if hasattr(ctk, "CTkToolTip") else None)
            lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            # Simple up/down buttons
            if i > 0:
                up_btn = ctk.CTkButton(row, text="▲", width=30, command=lambda idx=i: self._move_item(idx, -1))
                up_btn.grid(row=0, column=1, padx=2, pady=5)
            
            if i < len(self.media_list) - 1:
                down_btn = ctk.CTkButton(row, text="▼", width=30, command=lambda idx=i: self._move_item(idx, 1))
                down_btn.grid(row=0, column=2, padx=2, pady=5)

            del_btn = ctk.CTkButton(row, text="X", width=30, fg_color="#aa0000", hover_color="#880000", command=lambda idx=i: self._remove_item(idx))
            del_btn.grid(row=0, column=3, padx=5, pady=5)
            
            # Bind scroll events to row and its children
            self._bind_scroll_to_widgets(row)

    def _bind_scroll_to_widgets(self, widget):
        """Recursively bind mouse wheel events to propagate to the scrollable frame."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_scroll_to_widgets(child)

    def _on_mouse_wheel(self, event):
        """Redirect mouse wheel events to the scrollable frame canvas."""
        # Support Linux (Button-4/5) and Windows/macOS (MouseWheel)
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = int(-1 * (event.delta / 120))
        
        # Access CTkScrollableFrame internal canvas
        try:
            if hasattr(self.queue_frame, "_parent_canvas"):
                self.queue_frame._parent_canvas.yview_scroll(delta, "units")
            elif hasattr(self.queue_frame, "_canvas"):
                self.queue_frame._canvas.yview_scroll(delta, "units")
        except Exception:
            pass

    def _move_item(self, index, direction):
        new_index = index + direction
        self.media_list[index], self.media_list[new_index] = self.media_list[new_index], self.media_list[index]
        self._update_queue_display()

    def _remove_item(self, index):
        self.media_list.pop(index)
        self._update_queue_display()

    def _log(self, message):
        self.after(0, lambda: self.status_label.configure(text=message.strip()))
        print(message.strip())

    def _start_merge(self):
        if self.is_processing:
            return

        if len(self.media_list) < 2:
            messagebox.showerror("Error", "At least two videos are required to merge.")
            return

        # Use first video's directory for default output if not set
        first_video = self.media_list[0]
        export_root = self.shared_state.get("export_path")
        out_dir = get_output_directory(export_root, first_video, MERGER_OUTPUT_NAME)
        
        success, err = ensure_output_dir_verbose(out_dir)
        if not success:
            messagebox.showerror("Error", f"Could not create output directory: {err}")
            return

        out_path = os.path.join(out_dir, "merged_video.mp4") # Default name

        self.is_processing = True
        self.export_button.configure(state="disabled")
        self.add_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        threading.Thread(target=self._run_processing, args=(out_path,), daemon=True).start()

    def _run_processing(self, out_path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_async(out_path))
        finally:
            loop.close()
            self.is_processing = False
            self.after(0, self._on_processing_finished)

    async def _process_async(self, out_path):
        # Create temporary file for concat
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            for path in self.media_list:
                # FFmpeg concat file format: file 'path'
                # Use absolute path and escape single quotes
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
            temp_list_path = f.name

        try:
            cmd = build_concat_command(temp_list_path, out_path)
            self.after(0, lambda: self._log("Merging videos..."))
            success = await run_ffmpeg(cmd, self._log, 0, out_path)
            if success:
                self.after(0, lambda: self._log("Merge Finished!"))
            else:
                self.after(0, lambda: self._log("Merge Failed!"))
        finally:
            if os.path.exists(temp_list_path):
                os.remove(temp_list_path)

    def _on_processing_finished(self):
        self.export_button.configure(state="normal")
        self.add_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(1)
        messagebox.showinfo("Success", "Merge completed successfully.")
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
