"""Utilities for output path handling."""

import os


def get_default_output_path(source_path: str | None, folder_name: str) -> str:
    """Get the default output directory path based on source file location."""
    if source_path:
        video_dir = os.path.dirname(source_path) or os.getcwd()
    else:
        video_dir = os.getcwd()
    return os.path.join(video_dir, folder_name)


def get_output_directory(
    custom_path: str | None, source_path: str | None, folder_name: str
) -> str:
    """Get the output directory, either custom or default."""
    if custom_path:
        return custom_path
    return get_default_output_path(source_path, folder_name)


def validate_output_path(path: str) -> tuple[bool, str]:
    """Validate that the output path is writable."""
    if not os.path.exists(path):
        return False, f"Folder does not exist: {path}"
    if not os.access(path, os.W_OK):
        return False, f"Folder is not writable: {path}"
    return True, ""


def ensure_output_dir(path: str) -> bool:
    """Create output directory if it doesn't exist. Returns True on success."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False
