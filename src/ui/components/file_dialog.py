"""Native file selectors shared by the Textual and desktop interfaces."""

from collections.abc import Callable
import os
import threading


def open_native_dialog(
    app,
    callback: Callable[[str | list[str]], None],
    *,
    mode: str,
    title: str,
    initialdir: str | None = None,
    fallback: Callable[[], None],
    on_error: Callable[[str], None],
) -> None:
    """Open a native Tk chooser without blocking Textual's event loop.

    If Tk cannot create a native window, switch to the in-app path prompt.
    """

    def run_dialog() -> None:
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog

            start_dir = initialdir if initialdir and os.path.isdir(initialdir) else os.path.expanduser("~")
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except tk.TclError:
                pass
            root.update_idletasks()
            root.lift()
            root.focus_force()

            if mode == "folder":
                selection = filedialog.askdirectory(
                    parent=root,
                    initialdir=start_dir,
                    title=title,
                )
                result = os.path.abspath(selection) if selection else None
            else:
                options = {
                    "parent": root,
                    "initialdir": start_dir,
                    "title": title,
                    "filetypes": [
                        ("Video and audio", "*.mp4 *.mkv *.avi *.mov *.m4v *.mp3 *.wav *.flac *.m4a *.ogg"),
                        ("All files", "*.*"),
                    ],
                }
                if mode == "files":
                    selections = filedialog.askopenfilenames(**options)
                    result = [os.path.abspath(path) for path in selections] or None
                else:
                    selection = filedialog.askopenfilename(**options)
                    result = os.path.abspath(selection) if selection else None

            if result:
                if mode != "folder":
                    from ui.preferences import set_last_media_dir

                    first_path = result[0] if isinstance(result, list) else result
                    set_last_media_dir(os.path.dirname(first_path))
                app.call_from_thread(callback, result)
        except Exception as error:
            message = f"Native file chooser unavailable: {error}"
            try:
                app.call_from_thread(on_error, message)
                app.call_from_thread(fallback)
            except RuntimeError:
                pass
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass

    threading.Thread(target=run_dialog, name="native-file-dialog", daemon=True).start()


def open_file_dialog(multi: bool = False, title: str = "Select a video"):
    """Open a file dialog and return selected path(s)."""
    import tkinter as tk
    from tkinter import filedialog
    
    root = tk.Tk()
    root.withdraw()
    try:
        if multi:
            file_paths = filedialog.askopenfilenames(
                parent=root,
                title=title,
                filetypes=[
                    ("Video and audio", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v *.mp3 *.wav *.flac *.m4a *.ogg"),
                    ("All files", "*.*"),
                ],
            )
            return list(file_paths) if file_paths else None
        file_path = filedialog.askopenfilename(
            parent=root,
            title=title,
            filetypes=[
                ("Video and audio", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.m4v *.mp3 *.wav *.flac *.m4a *.ogg"),
                ("All files", "*.*"),
            ],
        )
        return file_path or None
    finally:
        root.destroy()
