"""User preferences persistence for UI features."""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_SPLITTER_MODE = "time"
VALID_SPLITTER_MODES = {"time", "count"}


def get_preferences_path() -> str:
    """Return preferences file path."""
    return os.path.expanduser("~/.config/video-slice-tui/preferences.json")


def load_preferences(path: str | None = None) -> dict[str, Any]:
    """Load preferences from disk."""
    pref_path = path or get_preferences_path()
    try:
        with open(pref_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_preferences(preferences: dict[str, Any], path: str | None = None) -> bool:
    """Save preferences to disk."""
    pref_path = path or get_preferences_path()
    try:
        os.makedirs(os.path.dirname(pref_path), exist_ok=True)
        with open(pref_path, "w", encoding="utf-8") as f:
            json.dump(preferences, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_splitter_mode(path: str | None = None) -> str:
    """Get persisted splitter mode."""
    prefs = load_preferences(path)
    mode = prefs.get("splitter_mode", DEFAULT_SPLITTER_MODE)
    return mode if mode in VALID_SPLITTER_MODES else DEFAULT_SPLITTER_MODE


def set_splitter_mode(mode: str, path: str | None = None) -> bool:
    """Persist splitter mode."""
    if mode not in VALID_SPLITTER_MODES:
        return False

    prefs = load_preferences(path)
    prefs["splitter_mode"] = mode
    return save_preferences(prefs, path)


def get_last_media_dir(path: str | None = None) -> str | None:
    """Get the last used media directory if it is still valid."""
    prefs = load_preferences(path)
    media_dir = prefs.get("last_media_dir")
    if not isinstance(media_dir, str):
        return None
    if os.path.isdir(media_dir):
        return media_dir
    return None


def set_last_media_dir(directory: str, path: str | None = None) -> bool:
    """Persist the last used media directory."""
    if not directory or not isinstance(directory, str):
        return False

    if not os.path.isdir(directory):
        return False

    prefs = load_preferences(path)
    prefs["last_media_dir"] = directory
    return save_preferences(prefs, path)
