"""Data models for Video Slice TUI."""

import os


class Range:
    """Represents a time range for cutting/splitting."""

    def __init__(self, start_s: float, end_s: float, idx: int):
        if end_s <= start_s:
            raise ValueError(f"End ({end_s}) must be after start ({start_s})")
        if start_s < 0:
            raise ValueError(f"Start time cannot be negative: {start_s}")
        self.start = start_s
        self.end = end_s
        self.idx = idx

    def duration(self) -> float:
        """Return the duration of this range in seconds."""
        return max(0.0, self.end - self.start)

    def __repr__(self) -> str:
        return f"Range(idx={self.idx}, start={self.start:.2f}, end={self.end:.2f}, duration={self.duration():.2f})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Range):
            return False
        return (self.start == other.start 
                and self.end == other.end 
                and self.idx == other.idx)
