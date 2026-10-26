"""Desktop shell for the optional CustomTkinter interface."""

import customtkinter as ctk
from ui.gui.screens import ClipperGUI, HubGUI, MergerGUI, SplitterGUI


class VideoSliceGUIApp(ctk.CTk):
    """Window with persistent navigation and a shared media workspace."""

    SCREENS = {
        "Hub": ("⌂", HubGUI),
        "Clipper": ("✂", ClipperGUI),
        "Splitter": ("▤", SplitterGUI),
        "Merger": ("⇄", MergerGUI),
    }

    def __init__(self, start_tab: str | None = None, video_path: str | None = None):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.title("Video Slice")
        self.geometry("1120x760")
        self.minsize(900, 620)
        self.configure(fg_color="#111318")

        self.shared_state = {"video_path": video_path or "", "export_path": ""}
        self._current_screen = None
        self._nav_buttons = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_workspace()

        for name, (_, screen_class) in self.SCREENS.items():
            screen = screen_class(self.content, self.shared_state)
            self._screens[name] = screen

        target = next(
            (name for name in self.SCREENS if name.lower() == (start_tab or "hub").lower()),
            "Hub",
        )
        self.show_screen(target)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#171a20")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="VIDEO\nSLICE",
            justify="left",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color="#f4f6fb",
        ).grid(row=0, column=0, padx=24, pady=(28, 5), sticky="w")
        ctk.CTkLabel(
            self.sidebar,
            text="VIDEO WORKSPACE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#7e8797",
        ).grid(row=1, column=0, padx=25, pady=(0, 28), sticky="w")

        self._screens = {}
        for row, (name, (icon, _)) in enumerate(self.SCREENS.items(), start=2):
            button = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}     {name}",
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color="transparent",
                hover_color="#262b35",
                text_color="#aeb6c4",
                command=lambda item=name: self.show_screen(item),
            )
            button.grid(row=row, column=0, padx=14, pady=4, sticky="ew")
            self._nav_buttons[name] = button

        ctk.CTkLabel(
            self.sidebar,
            text="FFmpeg powered",
            font=ctk.CTkFont(size=11),
            text_color="#687181",
        ).grid(row=20, column=0, padx=24, pady=20, sticky="sw")

    def _build_workspace(self):
        self.workspace = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.workspace.grid(row=0, column=1, padx=(18, 24), pady=(20, 18), sticky="nsew")
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(1, weight=1)

        self.topbar = ctk.CTkFrame(self.workspace, fg_color="#191d24", corner_radius=14)
        self.topbar.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.topbar.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.topbar,
            text="Hub",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f4f6fb",
        )
        self.page_title.grid(row=0, column=0, padx=20, pady=(15, 0), sticky="w")
        self.page_subtitle = ctk.CTkLabel(
            self.topbar,
            text="Choose your media and export location",
            font=ctk.CTkFont(size=12),
            text_color="#8993a3",
        )
        self.page_subtitle.grid(row=1, column=0, padx=20, pady=(2, 15), sticky="w")

        self.content = ctk.CTkFrame(self.workspace, fg_color="transparent", corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def show_screen(self, name: str):
        screen = self._screens[name]
        if self._current_screen is not None:
            self._current_screen.pack_forget()
        screen.pack(fill="both", expand=True)
        self._current_screen = screen
        self.page_title.configure(text=name)

        subtitles = {
            "Hub": "Choose your media and export location",
            "Clipper": "Create precise clips from selected time ranges",
            "Splitter": "Divide a video into consistent parts",
            "Merger": "Arrange and combine multiple video files",
        }
        self.page_subtitle.configure(text=subtitles[name])
        for button_name, button in self._nav_buttons.items():
            active = button_name == name
            button.configure(
                fg_color="#26364c" if active else "transparent",
                text_color="#8fc4ff" if active else "#aeb6c4",
            )

    def run(self):
        """Start the application event loop."""
        self.mainloop()


if __name__ == "__main__":
    VideoSliceGUIApp().run()
