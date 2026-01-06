# 🎬 Video Slice TUI

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/github/license/marodriguezd/Video-Slice-TUI)

A simple, efficient, and user-friendly Textual User Interface (TUI) for clipping, splitting, and merging video files directly from your terminal.

![Screenshot of Video Clipper TUI](https://raw.githubusercontent.com/marodriguezd/Video-Clipper-TUI/main/assets/screenshot.png)

## Overview

This project provides three video tools in a unified TUI application:

- **Clipper:** Extract specific clips by defining custom time ranges
- **Splitter:** Automatically split videos into equal-sized chunks
- **Merger:** Combine multiple videos into a single file

All tools are built with [Textual](https://github.com/Textualize/textual) and use [FFmpeg](https://ffmpeg.org/) for video processing.

## Architecture

```
src/
├── main.py                    # Unified entry point
├── logic/                     # Business logic (reusable)
│   ├── time_utils.py          # Time parsing/formatting
│   ├── ffmpeg_utils.py        # FFmpeg wrappers
│   └── models.py              # Domain models
└── ui/                        # Interface layer
    ├── app.py                 # Main application
    ├── screens/               # Each tool as a screen
    │   ├── hub_screen.py      # Tab-based navigation
    │   ├── clipper_screen.py
    │   ├── splitter_screen.py
    │   └── merger_screen.py
    └── components/            # Reusable UI components
        ├── base_screen.py     # Base class for screens
        ├── file_dialog.py     # File picker
        └── logger.py          # Log widget
```

## Features

- **Unified Hub:** Access all tools from one interface with tab navigation
- **Interactive TUI:** Clean, intuitive terminal interface
- **Flexible Input:** Load videos via argument or file selector
- **Multiple Time Formats:** `HH:MM:SS`, `MM:SS`, `SS`, or decimal hours (`1.5`)
- **Two Export Modes:**
  - **Copy Mode (Fast):** Stream copy without re-encoding
  - **Re-encode Mode (Precise):** Frame-accurate cuts
- **Extensible:** Easy to add new tools following the same patterns

## Requirements

- **Python 3.7+**
- **pip**
- **FFmpeg** (must be in PATH)

### FFmpeg Installation

- **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `bin` to PATH
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## Installation

```sh
git clone https://github.com/marodriguezd/Video-Slice-TUI.git
cd Video-Slice-TUI
pip install -r requirements.txt
```

## Usage

### Hub (all tools)

```sh
python src/main.py
```

Navigate between tools using:
- **Tab keys** or click on tabs
- **Keyboard shortcuts:** `1` = Clipper, `2` = Splitter, `3` = Merger
- **q** = Quit

### Direct tool access

```sh
python src/main.py --tool clipper    # Open directly in Clipper
python src/main.py --tool splitter   # Open directly in Splitter
python src/main.py --tool merger     # Open directly in Merger
```

### Load video on startup

```sh
python src/main.py --tool clipper --video "/path/to/video.mp4"
python src/main.py --tool splitter --video "/path/to/video.mp4"
```

### Alternative entry point

```sh
python -m src
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Switch to Clipper tab |
| `2` | Switch to Splitter tab |
| `3` | Switch to Merger tab |
| `q` | Quit application |
| `Esc` | Quit application |

## License

Apache License 2.0. See [LICENSE](LICENSE) file.
