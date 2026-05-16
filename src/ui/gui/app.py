import customtkinter as ctk
from ui.gui.screens import HubGUI, ClipperGUI, SplitterGUI, MergerGUI

class VideoSliceGUIApp(ctk.CTk):
    """Main application class for Video Slice GUI."""

    def __init__(self, start_tab: str = None, video_path: str = None):
        super().__init__()

        self.title("Video Slice TUI (GUI Mode)")
        self.geometry("900x700")

        # Shared state
        self.shared_state = {
            "video_path": video_path or "",
            "export_path": ""
        }

        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.tabview.add("Hub")
        self.tabview.add("Clipper")
        self.tabview.add("Splitter")
        self.tabview.add("Merger")

        # Configure tabs
        self.tabview.tab("Hub").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Clipper").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Splitter").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Merger").grid_columnconfigure(0, weight=1)

        # Initialize Hub Screen
        self.hub_screen = HubGUI(self.tabview.tab("Hub"), self.shared_state)
        self.hub_screen.pack(fill="both", expand=True)

        # Initialize Clipper Screen
        self.clipper_screen = ClipperGUI(self.tabview.tab("Clipper"), self.shared_state)
        self.clipper_screen.pack(fill="both", expand=True)

        # Initialize Splitter Screen
        self.splitter_screen = SplitterGUI(self.tabview.tab("Splitter"), self.shared_state)
        self.splitter_screen.pack(fill="both", expand=True)

        # Initialize Merger Screen
        self.merger_screen = MergerGUI(self.tabview.tab("Merger"), self.shared_state)
        self.merger_screen.pack(fill="both", expand=True)

        # Handle start tab
        if start_tab:
            # Map tool name to tab name if they differ in case
            tab_map = {"clipper": "Clipper", "splitter": "Splitter", "merger": "Merger"}
            target_tab = tab_map.get(start_tab.lower())
            if target_tab:
                self.tabview.set(target_tab)

    def run(self):
        """Start the application main loop."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.mainloop()

if __name__ == "__main__":
    app = VideoSliceGUIApp()
    app.run()
