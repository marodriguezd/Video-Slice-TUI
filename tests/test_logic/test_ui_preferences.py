"""Tests for UI preferences persistence."""

from ui.preferences import (
    DEFAULT_SPLITTER_MODE,
    get_splitter_mode,
    load_preferences,
    save_preferences,
    set_splitter_mode,
)


def test_load_preferences_missing_file(tmp_path):
    pref_path = tmp_path / "missing.json"
    assert load_preferences(str(pref_path)) == {}


def test_save_and_load_preferences(tmp_path):
    pref_path = tmp_path / "prefs.json"
    data = {"splitter_mode": "count", "other": True}
    assert save_preferences(data, str(pref_path))
    assert load_preferences(str(pref_path)) == data


def test_get_splitter_mode_default_when_missing(tmp_path):
    pref_path = tmp_path / "missing.json"
    assert get_splitter_mode(str(pref_path)) == DEFAULT_SPLITTER_MODE


def test_get_splitter_mode_fallback_on_invalid_value(tmp_path):
    pref_path = tmp_path / "prefs.json"
    assert save_preferences({"splitter_mode": "invalid"}, str(pref_path))
    assert get_splitter_mode(str(pref_path)) == DEFAULT_SPLITTER_MODE


def test_set_splitter_mode_and_reload(tmp_path):
    pref_path = tmp_path / "prefs.json"
    assert set_splitter_mode("count", str(pref_path))
    assert get_splitter_mode(str(pref_path)) == "count"
    assert set_splitter_mode("time", str(pref_path))
    assert get_splitter_mode(str(pref_path)) == "time"


def test_set_splitter_mode_rejects_invalid_value(tmp_path):
    pref_path = tmp_path / "prefs.json"
    assert not set_splitter_mode("foo", str(pref_path))
