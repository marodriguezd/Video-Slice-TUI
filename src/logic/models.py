"""Data models for Video Slice TUI."""


class Range:
    """Represents a time range for cutting/splitting."""

    def __init__(self, start_s: float, end_s: float, idx: int):
        if end_s <= start_s:
            raise ValueError("End must be after start")
        self.start = start_s
        self.end = end_s
        self.idx = idx

    def duration(self) -> float:
        return self.end - self.start


class VideoFile:
    """Represents a video file."""

    def __init__(self, path: str, duration: float | None = None):
        self.path = path
        self.duration = duration

    @property
    def basename(self) -> str:
        return os.path.basename(self.path) if self.path else ""

    def __repr__(self):
        return f"VideoFile({self.basename})"


import os
