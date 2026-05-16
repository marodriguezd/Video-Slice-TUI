import os
import customtkinter as ctk
from tkinter import filedialog
from logic.input_parsing import clean_pasted_path
from ui.preferences import get_last_media_dir, set_last_media_dir

class HubGUI(ctk.CTkFrame):
    """Hub screen for selecting input video and export directory."""

    def __init__(self, master, shared_state, **kwargs):
        super().__init__(master, **kwargs)
        self.shared_state = shared_state

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        self.label = ctk.CTkLabel(self, text="Video Slice Hub", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Video selection section
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.video_frame.grid_columnconfigure(1, weight=1)

        self.video_label = ctk.CTkLabel(self.video_frame, text="Input Video:", font=ctk.CTkFont(weight="bold"))
        self.video_label.grid(row=0, column=0, padx=10, pady=10)

        self.video_entry = ctk.CTkEntry(self.video_frame, placeholder_text="Path to video file...")
        self.video_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.video_entry.bind("<FocusOut>", self._on_video_entry_change)
        self.video_entry.bind("<Return>", self._on_video_entry_change)

        self.video_button = ctk.CTkButton(self.video_frame, text="Browse", command=self._browse_video)
        self.video_button.grid(row=0, column=2, padx=10, pady=10)

        # Export selection section
        self.export_frame = ctk.CTkFrame(self)
        self.export_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.export_frame.grid_columnconfigure(1, weight=1)

        self.export_label = ctk.CTkLabel(self.export_frame, text="Export Dir:", font=ctk.CTkFont(weight="bold"))
        self.export_label.grid(row=0, column=0, padx=10, pady=10)

        self.export_entry = ctk.CTkEntry(self.export_frame, placeholder_text="Path to export directory...")
        self.export_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.export_entry.bind("<FocusOut>", self._on_export_entry_change)
        self.export_entry.bind("<Return>", self._on_export_entry_change)

        self.export_button = ctk.CTkButton(self.export_frame, text="Browse", command=self._browse_export)
        self.export_button.grid(row=0, column=2, padx=10, pady=10)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=3, column=0, padx=20, pady=10)

        # Initialize entries with shared state
        self._update_ui_from_state()

    def _update_ui_from_state(self):
        if self.shared_state.get("video_path"):
            self.video_entry.delete(0, ctk.END)
            self.video_entry.insert(0, self.shared_state["video_path"])
        
        if self.shared_state.get("export_path"):
            self.export_entry.delete(0, ctk.END)
            self.export_entry.insert(0, self.shared_state["export_path"])

    def _on_video_entry_change(self, event=None):
        path = clean_pasted_path(self.video_entry.get())
        self.video_entry.delete(0, ctk.END)
        self.video_entry.insert(0, path)
        self.shared_state["video_path"] = path
        if path and os.path.exists(path):
            set_last_media_dir(os.path.dirname(os.path.abspath(path)))

    def _on_export_entry_change(self, event=None):
        path = clean_pasted_path(self.export_entry.get())
        self.export_entry.delete(0, ctk.END)
        self.export_entry.insert(0, path)
        self.shared_state["export_path"] = path

    def _browse_video(self):
        initial_dir = get_last_media_dir() or os.path.expanduser("~")
        filename = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Video File",
            filetypes=(("Video files", "*.mp4 *.mkv *.avi *.mov *.m4v"), ("all files", "*.*"))
        )
        if filename:
            filename = os.path.abspath(filename)
            self.video_entry.delete(0, ctk.END)
            self.video_entry.insert(0, filename)
            self.shared_state["video_path"] = filename
            set_last_media_dir(os.path.dirname(filename))

    def _browse_export(self):
        initial_dir = self.shared_state.get("export_path") or get_last_media_dir() or os.path.expanduser("~")
        directory = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Select Export Directory"
        )
        if directory:
            directory = os.path.abspath(directory)
            self.export_entry.delete(0, ctk.END)
            self.export_entry.insert(0, directory)
            self.shared_state["export_path"] = directory
