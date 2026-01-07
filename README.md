# 🎬 Video Slice TUI

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/marodriguezd/Video-Slice-TUI)](LICENSE)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-green.svg)](https://ffmpeg.org/)

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
Automate your content creation. Split long videos into perfectly timed chunks (e.g., 10-minute segments) with a single click. Ideal for platform-specific uploads.

![Splitter Tool](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/splitter.png)

### 🔗 Video Merger
Combine multiple video files into a single, high-quality output. Add videos to your queue, manage their order, and merge them instantly using the concat protocol.

![Merger Tool](https://raw.githubusercontent.com/marodriguezd/Video-Slice-TUI/main/assets/merger.png)

---

## 🛠️ Prerequisites

- **Python 3.7+**
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

Launch the application:
```bash
python src/main.py
```

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `Tab` | Cycle through controls |
| `q` / `Esc` | Quit Application |
| `Mouse` | Full click support for all buttons and tabs |

---

## 🏛️ Project Structure

- `src/main.py`: Unified entry point.
- `src/logic/`: Core processing logic and FFmpeg wrappers.
- `src/ui/`: Responsive Terminal User Interface layer.
- `assets/`: UI snapshots and brand assets.

## 📄 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

---
*Created by [marodriguezd](https://github.com/marodriguezd)*
