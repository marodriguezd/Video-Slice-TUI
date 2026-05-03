"""Utilities for generating splitter ranges."""

from .models import Range


def build_ranges_by_interval(video_duration: float, chunk_seconds: float) -> list[Range]:
    """Build sequential ranges using a fixed chunk interval."""
    if video_duration <= 0:
        raise ValueError("Video duration must be > 0")
    if chunk_seconds <= 0:
        raise ValueError("Chunk duration must be > 0")

    ranges: list[Range] = []
    start_time = 0.0
    idx = 1
    while start_time < video_duration:
        end_time = min(start_time + chunk_seconds, video_duration)
        ranges.append(Range(start_time, end_time, idx))
        idx += 1
        start_time = end_time

    return ranges


def build_ranges_by_count(video_duration: float, total_chunks: int) -> list[Range]:
    """Build sequential ranges targeting an explicit number of chunks."""
    if video_duration <= 0:
        raise ValueError("Video duration must be > 0")
    if total_chunks <= 0:
        raise ValueError("Total chunks must be > 0")

    chunk_seconds = video_duration / total_chunks
    ranges: list[Range] = []
    start_time = 0.0

    for idx in range(1, total_chunks + 1):
        if idx == total_chunks:
            end_time = video_duration
        else:
            end_time = min(start_time + chunk_seconds, video_duration)
        ranges.append(Range(start_time, end_time, idx))
        start_time = end_time

    return ranges
