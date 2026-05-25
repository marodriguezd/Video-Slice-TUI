import os
import threading
import asyncio
import customtkinter as ctk
from tkinter import messagebox
from logic.models import Range
from logic.time_utils import parse_time, format_hhmmss
from logic.ffmpeg_builder import build_cut_command, generate_clip_filename, CLIPPER_OUTPUT_NAME
from logic.ffmpeg_utils import run_ffmpeg, get_video_duration
from logic.output_utils import get_output_directory, ensure_output_dir_verbose

class ClipperGUI(ctk.CTkFrame):
    """Clipper screen for cutting specific ranges from a video."""

    def __init__(self, master, shared_state, **kwargs):
        super().__init__(master, **kwargs)
        self.shared_state = shared_state
        self.ranges = []

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1) # Queue area expands

        # Title
        self.label = ctk.CTkLabel(self, text="Video Clipper", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Input Area
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure((1, 3), weight=1)

        self.start_label = ctk.CTkLabel(self.input_frame, text="Start:")
        self.start_label.grid(row=0, column=0, padx=(10, 5), pady=10)
        self.start_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. 00:01:30")
        self.start_entry.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.end_label = ctk.CTkLabel(self.input_frame, text="End:")
        self.end_label.grid(row=0, column=2, padx=(10, 5), pady=10)
        self.end_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. 00:02:00")
        self.end_entry.grid(row=0, column=3, padx=5, pady=10, sticky="ew")

        self.add_button = ctk.CTkButton(self.input_frame, text="Add Range", command=self._add_range)
        self.add_button.grid(row=0, column=4, padx=10, pady=10)

        # Queue Label
        self.queue_label = ctk.CTkLabel(self, text="Ranges to Export:", font=ctk.CTkFont(weight="bold"))
        self.queue_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")

        # Queue Display (Scrollable Frame)
        self.queue_frame = ctk.CTkScrollableFrame(self)
        self.queue_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # Options Area
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.precise_var = ctk.BooleanVar(value=False)
        self.precise_check = ctk.CTkCheckBox(self.options_frame, text="Precise Cut (Re-encode)", variable=self.precise_var)
        self.precise_check.grid(row=0, column=0, padx=10, pady=10)

        self.clear_button = ctk.CTkButton(self.options_frame, text="Clear All", fg_color="transparent", border_width=2, command=self._clear_ranges)
        self.clear_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        self.options_frame.grid_columnconfigure(1, weight=1)

        # Export Area
        self.export_button = ctk.CTkButton(self, text="START EXPORT", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self._start_export)
        self.export_button.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=6, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.grid(row=7, column=0, padx=20, pady=(0, 10))

        self.is_processing = False

    def _add_range(self):
        start_str = self.start_entry.get().strip()
        end_str = self.end_entry.get().strip()

        if not start_str or not end_str:
            return

        try:
            start_s = parse_time(start_str)
            end_s = parse_time(end_str)
            
            # Basic validation
            if end_s <= start_s:
                messagebox.showerror("Error", "End time must be after start time.")
                return

            idx = len(self.ranges) + 1
            new_range = Range(start_s, end_s, idx)
            self.ranges.append(new_range)
            self._update_queue_display()
            
            # Clear entries
            self.start_entry.delete(0, ctk.END)
            self.end_entry.delete(0, ctk.END)
            self.start_entry.focus()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid time format: {e}")

    def _update_queue_display(self):
        # Clear current display
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        for i, r in enumerate(self.ranges):
            row = ctk.CTkFrame(self.queue_frame)
            row.grid(row=i, column=0, padx=5, pady=2, sticky="ew")
            row.grid_columnconfigure(0, weight=1)

            txt = f"Clip #{r.idx}: {format_hhmmss(r.start)} -> {format_hhmmss(r.end)} ({r.duration():.2f}s)"
            lbl = ctk.CTkLabel(row, text=txt)
            lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            del_btn = ctk.CTkButton(row, text="X", width=30, fg_color="#aa0000", hover_color="#880000", command=lambda idx=i: self._remove_range(idx))
            del_btn.grid(row=0, column=1, padx=5, pady=5)
            
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

    def _remove_range(self, index):
        self.ranges.pop(index)
        # Re-index
        for i, r in enumerate(self.ranges):
            r.idx = i + 1
        self._update_queue_display()

    def _clear_ranges(self):
        self.ranges = []
        self._update_queue_display()

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
            messagebox.showerror("Error", "No ranges added to queue.")
            return

        export_root = self.shared_state.get("export_path")
        out_dir = get_output_directory(export_root, video_path, CLIPPER_OUTPUT_NAME)
        
        success, err = ensure_output_dir_verbose(out_dir)
        if not success:
            messagebox.showerror("Error", f"Could not create output directory: {err}")
            return

        self.is_processing = True
        self.export_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.add_button.configure(state="disabled")
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
            
            self.after(0, lambda m=f"Processing clip {i+1}/{total}...": self._log(m))
            
            success = await run_ffmpeg(cmd, self._log, r.idx, out_path)
            
            # Update progress
            progress = (i + 1) / total
            self.after(0, lambda p=progress: self.progress_bar.set(p))

        self.after(0, lambda: self._log("Export Finished!"))

    def _on_processing_finished(self):
        self.export_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        self.add_button.configure(state="normal")
        messagebox.showinfo("Success", "Export completed successfully.")
        self.status_label.configure(text="Ready")
        self.progress_bar.set(0)
