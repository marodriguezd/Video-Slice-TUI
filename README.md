# 🎬 Video Clipper TUI

A simple, efficient, and user-friendly Textual User Interface (TUI) for clipping video files directly from your terminal.

![Screenshot of Video Clipper TUI](https://i.imgur.com/8VfV3Yj.png) 

## Overview

Video Clipper TUI is a single-file Python application that allows you to:
- Load a video file.
- Define multiple time ranges to create clips.
- Export the clips quickly and easily.

It's built with [Textual](https://github.com/Textualize/textual), providing a rich and interactive experience in the terminal. The core clipping functionality is powered by [FFmpeg](https://ffmpeg.org/).

## Features

- **Interactive TUI:** A clean and intuitive interface that runs in your terminal.
- **Flexible File Input:** Load videos by passing a file path as a command-line argument or by using the built-in file selector.
- **Multiple Time Formats:** Specify start and end times in various formats (e.g., `HH:MM:SS`, `MM:SS`, `SS`, or decimal minutes like `2.5` for 2 minutes and 30 seconds).
- **Multiple Clip Definitions:** Add as many time ranges as you need to the queue.
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

You can run the application in two ways:

1.  **Passing a video file directly:**
    ```sh
    python src/video_clipper_tui.py "/path/to/your/video.mp4"
    ```

2.  **Without arguments (to open the file selector):**
    ```sh
    python src/video_clipper_tui.py
    ```

Once the application is running:
1.  The video path will be loaded if you provided it as an argument. Otherwise, you can paste the path into the input box or use the "Select" button to open a file dialog.
2.  Enter the `Start` and `End` times for a clip.
3.  Click the "Add" button to add the time range to the list.
4.  Repeat for all the clips you want to create.
5.  Choose between "Re-encode" for precision or leave it unchecked for speed.
6.  Click the "Export clips" button to start the process.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
