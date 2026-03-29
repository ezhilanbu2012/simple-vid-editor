# Fast Video Trimmer

A simple, lightweight video trimmer built with Python and PyQt6. It uses FFmpeg under the hood to perform "stream copy" trimming, which means it cuts your videos almost instantaneously without any quality loss or re-encoding.

## Features

- **Blazing Fast**: Trims video in seconds using FFmpeg's copy codec.
- **Preview Player**: Built-in video player to find the exact frame to cut.
- **Simple UI**: Intuitive "Set Start" and "Set End" buttons.
- **No Quality Loss**: Direct stream copy preserves original video and audio quality.

## Prerequisites

- **Python 3.x**
- **FFmpeg**: Must be installed and available in your system PATH.
  ```bash
  sudo apt install ffmpeg  # Linux (Debian/Ubuntu)
  brew install ffmpeg      # macOS
  ```

## Installation

1. Clone the repository (or navigate to the project folder).
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate  # Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python3 main.py
   ```
2. Click **Open Video...** to load a file.
3. Use the slider or Play button to navigate.
4. Click **Set Start [** at the desired start point.
5. Click **Set End ]** at the desired end point.
6. Click **Trim and Save Video** to export your clip.

## License

MIT
