# 🎬 Video Slice TUI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/marodriguezd/Video-Slice-TUI)](LICENSE)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green.svg)](https://ffmpeg.org/)
[![Tests](https://img.shields.io/badge/Tests-104%20passed-green.svg)](#-testing)

**Video Slice TUI** is a modern, high-performance terminal interface designed for effortless video manipulation. Built with [Textual](https://github.com/Textualize/textual), it provides a suite of professional tools—Clipper, Splitter, and Merger—powered by the robust FFmpeg engine.

![Hub Screen](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/hub.png)

---

## 🚀 Overview

Tired of complex GUI video editors or bloated software? Video Slice TUI brings professional-grade video processing directly to your terminal. It offers a clean, keyboard-centric workflow that simplifies common tasks like extracting highlights, creating chunks for social media, or concatenating multiple clips.

## ✨ Key Features

### 🏠 Centralized Hub
Managing your project starts here. Select your main video and define your global export route. The Hub acts as the command center, propagating your settings across all tools for a seamless experience.

### ✂️ Video Clipper
Extract specific moments with precision. Define multiple time ranges, preview durations, and choose between lightning-fast "Stream Copy" or frame-accurate "Re-encoding".

![Clipper Tool](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/clipper.png)

### 🔪 Video Splitter
Automate your content creation. Split long videos by interval (MM:SS / HH:MM:SS) or by target total chunks with a single click. Ideal for platform-specific uploads.

![Splitter Tool](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/splitter.png)

### 🔗 Video Merger
Combine multiple video files into a single, high-quality output. Add videos to your queue, manage their order, and merge them instantly using the concat protocol.

![Merger Tool](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/merger.png)

---

## 🛠️ Prerequisites

- **Python 3.10+**
- **FFmpeg**: Must be installed and accessible in your system's PATH.
  - **Windows**: [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
  - **macOS**: `brew install ffmpeg`
  - **Linux**: `sudo apt install ffmpeg`

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/marodriguezd/Video-Slice-TUI.git
   cd Video-Slice-TUI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## ⌨️ Usage

### Launch the application:
```bash
# Full application with all tools
python src/main.py

# Launch directly to a specific tool
python src/main.py --tool clipper --video "C:\path\to\video.mp4"
python src/main.py --tool splitter --video "C:\path\to\video.mp4"
python src/main.py --tool merger
```

### CLI Arguments:
| Flag | Description |
|------|-------------|
| `--tool <name>` | Launch specific tool: `clipper`, `splitter`, or `merger` |
| `--video <path>` | Pre-load a video file (used with clipper/splitter) |

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Tab` | Cycle through controls |
| `q` / `Esc` | Quit Application |
| `Mouse` | Full click support for all buttons and tabs |

---

## 🧪 Testing

The project includes a comprehensive test suite with 104 tests covering unit, integration, and E2E scenarios.

### Run all tests:
```bash
# Set video path for integration tests (Windows)
set TEST_VIDEO_PATH=C:\Users\marod\Videos\2025-12-17 00-00-10.mp4

# Run all tests
python -m pytest tests/ -v

# Run only unit tests (fast)
python -m pytest tests/test_logic/ -v

# Run with test runner script
python run_tests.py
```

### Test Coverage:
- **Unit tests**: Time parsing, path cleaning, command building, models
- **Integration tests**: FFmpeg operations with real video files
- **E2E tests**: CLI arguments, syntax verification, imports

---

## 🏛️ Project Structure

```
Video-Slice-TUI/
├── src/
│   ├── main.py              # Unified entry point
│   ├── logic/               # Core processing logic
│   │   ├── __init__.py      # Module exports
│   │   ├── time_utils.py    # Time parsing/formatting
│   │   ├── ffmpeg_utils.py  # FFmpeg wrappers
│   │   ├── ffmpeg_builder.py # FFmpeg command building
│   │   ├── input_parsing.py # Path cleaning utilities
│   │   ├── output_utils.py  # Output path utilities
│   │   └── models.py        # Domain models
│   └── ui/                  # Terminal interface
│       ├── app.py           # Main App class
│       ├── screens/         # Tool screens (hub, clipper, splitter, merger)
│       └── components/      # Reusable UI components
├── tests/                   # Test suite
│   ├── test_logic/          # Unit tests
│   ├── test_integration/    # Integration tests
│   └── test_e2e/            # End-to-end tests
├── requirements.txt         # Dependencies
├── pytest.ini               # Pytest configuration
└── run_tests.py             # Test runner script
```

## 📄 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

---

*Created by [marodriguezd](https://github.com/marodriguezd)*
