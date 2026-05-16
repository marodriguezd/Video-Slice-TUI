#!/usr/bin/env python3
"""
Video Slice TUI - Unified entry point for all video tools.

Usage:
    python src/main.py                       # Hub with tabs
    python src/main.py --tool clipper        # Open directly in Clipper
    python src/main.py --tool splitter       # Open directly in Splitter
    python src/main.py --tool merger         # Open directly in Merger

    python src/main.py --tool clipper --video video.mp4
"""

import sys
import argparse

from ui import VideoSliceApp


def parse_args():
    parser = argparse.ArgumentParser(
        description="Video Slice TUI - Clip, split, and merge videos"
    )
    parser.add_argument(
        "--tool",
        "-t",
        choices=["clipper", "splitter", "merger"],
        help="Start directly in the specified tool",
    )
    parser.add_argument("--video", "-v", help="Video file path to load on startup")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch the GUI version")
    return parser.parse_args()


def main():
    args = parse_args()

    tool = args.tool
    video_path = args.video

    if args.gui:
        try:
            from ui.gui.app import VideoSliceGUIApp
            app = VideoSliceGUIApp(start_tab=tool, video_path=video_path)
            app.run()
        except ImportError as e:
            print(f"Error: GUI dependencies not found. Have you run 'pip install -r requirements.txt'?\nDetails: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Failed to launch GUI: {e}")
            sys.exit(1)
    else:
        app = VideoSliceApp(start_tab=tool, video_path=video_path)
        app.run()


if __name__ == "__main__":
    main()
