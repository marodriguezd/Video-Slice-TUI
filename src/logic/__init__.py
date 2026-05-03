"""Logic module exports."""

from .time_utils import parse_time, format_hhmmss
from .split_utils import build_ranges_by_interval, build_ranges_by_count
from .ffmpeg_utils import get_video_duration, run_ffmpeg
from .input_parsing import clean_video_path, clean_pasted_path
from .models import Range
from .output_utils import (
    get_default_output_path,
    get_output_directory,
    validate_output_path,
    ensure_output_dir,
    ensure_output_dir_verbose,
)
from .ffmpeg_builder import (
    build_cut_command,
    build_concat_command,
    generate_clip_filename,
    CLIPPER_OUTPUT_NAME,
    SPLITTER_OUTPUT_NAME,
    MERGER_OUTPUT_NAME,
)

__all__ = [
    "parse_time",
    "format_hhmmss",
    "build_ranges_by_interval",
    "build_ranges_by_count",
    "get_video_duration",
    "run_ffmpeg",
    "clean_video_path",
    "clean_pasted_path",
    "Range",
    "get_default_output_path",
    "get_output_directory",
    "validate_output_path",
    "ensure_output_dir",
    "ensure_output_dir_verbose",
    "build_cut_command",
    "build_concat_command",
    "generate_clip_filename",
    "CLIPPER_OUTPUT_NAME",
    "SPLITTER_OUTPUT_NAME",
    "MERGER_OUTPUT_NAME",
]
