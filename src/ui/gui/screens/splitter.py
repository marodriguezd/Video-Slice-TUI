import os
import threading
import asyncio
import customtkinter as ctk
from tkinter import messagebox
from logic.models import Range
from logic.time_utils import parse_time, format_hhmmss
from logic.ffmpeg_builder import build_cut_command, generate_clip_filename, SPLITTER_OUTPUT_NAME
from logic.ffmpeg_utils import run_ffmpeg, get_video_duration
from logic.output_utils import get_output_directory, ensure_output_dir_verbose
from logic.split_utils import build_ranges_by_interval, build_ranges_by_count

class SplitterGUI(ctk.CTkFrame):
    """Splitter screen for dividing a video into multiple parts."""

    def __init__(self, master, shared_state, **kwargs):
        super().__init__(master, **kwargs)
        self.shared_state = shared_state
        self.ranges = []

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Title
        self.label = ctk.CTkLabel(self, text="Video Splitter", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Config Area
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.config_frame.grid_columnconfigure(2, weight=1)

        self.mode_label = ctk.CTkLabel(self.config_frame, text="Split Mode:")
        self.mode_label.grid(row=0, column=0, padx=10, pady=10)

        self.mode_var = ctk.StringVar(value="By Time")
        self.mode_menu = ctk.CTkOptionMenu(self.config_frame, values=["By Time", "By Chunks"], variable=self.mode_var, command=self._on_mode_change)
        self.mode_menu.grid(row=0, column=1, padx=10, pady=10)

        self.value_label = ctk.CTkLabel(self.config_frame, text="Interval (s):")
        self.value_label.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.value_entry = ctk.CTkEntry(self.config_frame, placeholder_text="e.g. 60")
        self.value_entry.grid(row=0, column=3, padx=10, pady=10)

        self.gen_button = ctk.CTkButton(self.config_frame, text="Generate Chunks", command=self._generate_chunks)
        self.gen_button.grid(row=0, column=4, padx=10, pady=10)

        # Queue Label
        self.queue_label = ctk.CTkLabel(self, text="Generated Chunks:", font=ctk.CTkFont(weight="bold"))
        self.queue_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")

        # Queue Display
        self.queue_frame = ctk.CTkScrollableFrame(self)
        self.queue_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # Options Area
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.precise_var = ctk.BooleanVar(value=False)
        self.precise_check = ctk.CTkCheckBox(self.options_frame, text="Precise Cut (Re-encode)", variable=self.precise_var)
        self.precise_check.grid(row=0, column=0, padx=10, pady=10)

        # Export Area
        self.export_button = ctk.CTkButton(self, text="START EXPORT", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self._start_export)
        self.export_button.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=6, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.grid(row=7, column=0, padx=20, pady=(0, 10))

        self.is_processing = False

    def _on_mode_change(self, mode):
        if mode == "By Time":
            self.value_label.configure(text="Interval (s):")
        else:
            self.value_label.configure(text="Chunk Count:")

    def _generate_chunks(self):
        video_path = self.shared_state.get("video_path")
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "No valid input video selected in Hub.")
            return

        val_str = self.value_entry.get().strip()
        if not val_str:
            return

        # Need video duration
        self.status_label.configure(text="Getting video duration...")
        threading.Thread(target=self._run_get_duration, args=(video_path, val_str), daemon=True).start()

    def _run_get_duration(self, video_path, val_str):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        duration = loop.run_until_complete(get_video_duration(video_path))
        loop.close()

        if duration is None:
            self.after(0, lambda: messagebox.showerror("Error", "Could not get video duration."))
            self.after(0, lambda: self.status_label.configure(text="Ready"))
            return

        self.after(0, lambda: self._on_duration_received(duration, val_str))

    def _on_duration_received(self, duration, val_str):
        mode = self.mode_var.get()
        try:
            if mode == "By Time":
                interval = float(val_str)
                self.ranges = build_ranges_by_interval(duration, interval)
            else:
                count = int(val_str)
                self.ranges = build_ranges_by_count(duration, count)
            
            self._update_queue_display()
            self.status_label.configure(text=f"Generated {len(self.ranges)} chunks.")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            self.status_label.configure(text="Ready")

    def _update_queue_display(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        for i, r in enumerate(self.ranges):
            row = ctk.CTkFrame(self.queue_frame)
            row.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            row.grid_columnconfigure(0, weight=1)

            txt = f"Part #{r.idx}: {format_hhmmss(r.start)} -> {format_hhmmss(r.end)} ({r.duration():.2f}s)"
            lbl = ctk.CTkLabel(row, text=txt)
            lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    def _log(self, message):
        self.after(0, lambda: self.status_label.configure(text=message.strip()))
        print(message.strip())

    def _start_export(self):
        if self.is_processing:
            return

        video_path = self.shared_state.get("video_path")
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "No valid input video selected in Hub.")
            return

        if not self.ranges:
            messagebox.showerror("Error", "No chunks generated.")
            return

        export_root = self.shared_state.get("export_path")
        out_dir = get_output_directory(export_root, video_path, SPLITTER_OUTPUT_NAME)
        
        success, err = ensure_output_dir_verbose(out_dir)
        if not success:
            messagebox.showerror("Error", f"Could not create output directory: {err}")
            return

        self.is_processing = True
        self.export_button.configure(state="disabled")
        self.gen_button.configure(state="disabled")
        self.progress_bar.set(0)

        threading.Thread(target=self._run_processing, args=(video_path, out_dir), daemon=True).start()

    def _run_processing(self, video_path, out_dir):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._process_async(video_path, out_dir))
        finally:
            loop.close()
            self.is_processing = False
            self.after(0, self._on_processing_finished)

    async def _process_async(self, video_path, out_dir):
        total = len(self.ranges)
        reencode = self.precise_var.get()
        extension = os.path.splitext(video_path)[1] or ".mp4"

        for i, r in enumerate(self.ranges):
            filename = generate_clip_filename(
                r.idx, r.start, r.end, format_hhmmss(r.start).replace(":", "-"), format_hhmmss(r.end).replace(":", "-"), extension
            )
            out_path = os.path.join(out_dir, filename)
            cmd = build_cut_command(video_path, r.start, r.duration(), out_path, reencode)
            
            self.after(0, lambda m=f"Processing chunk {i+1}/{total}...": self._log(m))
            await run_ffmpeg(cmd, self._log, r.idx, out_path)
            
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))

        self.after(0, lambda: self._log("Export Finished!"))

    def _on_processing_finished(self):
        self.export_button.configure(state="normal")
        self.gen_button.configure(state="normal")
        messagebox.showinfo("Success", "Export completed successfully.")
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
