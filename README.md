# 🎬 Video Clipper & Splitter TUI

A simple, efficient, and user-friendly Textual User Interface (TUI) for clipping and splitting video files directly from your terminal.

![Screenshot of Video Clipper TUI](https://raw.githubusercontent.com/marodriguezd/Video-Clipper-TUI/main/assets/screenshot.png) 
![Screenshot of Video Splitter TUI](https://raw.githubusercontent.com/marodriguezd/Video-Clipper-TUI/main/assets/screenshot2.png) 

## Overview

This project provides two simple and efficient Python applications with a Textual User Interface (TUI):

- **Video Clipper:** Allows you to load a video file, define multiple specific time ranges, and export them as individual clips.
- **Video Splitter:** An adaptation of the clipper that automatically splits a video into equal-sized chunks based on a specified duration (in minutes).

Both tools are built with [Textual](https://github.com/Textualize/textual) and use [FFmpeg](https://ffmpeg.org/) for the core video processing.

## Features

- **Two Tools in One:** A precise clipper for custom time ranges and an automatic splitter for fixed-duration chunks.
- **Interactive TUI:** A clean and intuitive interface that runs in your terminal for both tools.
- **Flexible File Input:** Load videos by passing a file path as a command-line argument or by using the built-in file selector.
- **Multiple Time Formats (Clipper):** Specify start and end times in various formats (e.g., `HH:MM:SS`, `MM:SS`, `SS`, or decimal hours like `1.5` for 1 hour and 30 minutes).
- **Automatic Splitting (Splitter):** Just define the chunk duration in minutes, and the tool will calculate the segments for you.
- **Two Export Modes:**
  - **Copy Mode (Fast):** Quickly creates clips by copying the video stream without re-encoding. This is very fast but may result in less precise cuts.
  - **Re-encode Mode (Precise):** Re-encodes the video for frame-accurate cuts, which is slower but more precise.
- **Organized Output:** All generated clips are saved in a `clips_output` folder created in the same directory as the source video.

## Requirements

To run this application, you need:
- **Python 3.7+**
- **pip** (Python package installer)
- **FFmpeg**

### FFmpeg Installation

FFmpeg is a crucial dependency for this application. You must install it and ensure it's available in your system's PATH.

- **Windows:**
  1. Download a static build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
  2. Extract the archive (e.g., to `C:\ffmpeg`).
  3. Add the `bin` directory (e.g., `C:\ffmpeg\bin`) to your system's `PATH` environment variable.

- **macOS** (using [Homebrew](https://brew.sh/)):
  ```sh
  brew install ffmpeg
  ```

- **Linux** (using `apt` for Debian/Ubuntu):
  ```sh
  sudo apt update
  sudo apt install ffmpeg
  ```

## Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/Video-Clipper-TUI.git
    cd Video-Clipper-TUI
    ```

2.  **Install the Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

Run the desired tool from your terminal. You can select a video file from within the application's interface.

### 1. Video Clipper

Use this tool to extract specific clips by defining start and end times.
```sh
python src/video_clipper_tui.py
```

### 2. Video Splitter

Use this tool to automatically split a video into equal-sized chunks.
```sh
python src/video_splitter_tui.py
```

Optionally, you can pass a path to a video file as an argument to load it automatically on startup:
```sh
# For the clipper
python src/video_clipper_tui.py "/path/to/your/video.mp4"

# For the splitter
python src/video_splitter_tui.py "/path/to/your/video.mp4"
```

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
