# YouTube Transcript Downloader

Tool to download YouTube video transcripts in Markdown format. Available as both a command-line interface (CLI) and a desktop application (GUI).

## Key Features

- **Automatic ID Extraction**: Automatically extracts YouTube video ID from various URL formats
- **Multi-language Support**: Downloads transcripts in specified language if available
- **Markdown Formatting**: Converts transcript into clean, readable Markdown file
- **CLI and GUI**: Use the tool from terminal or through a graphical interface
- **Automated Setup**: Setup script that verifies Python and manages dependencies interactively

## Quick Installation (Windows)

### Option 1: Automated Script (Recommended)

Run the automated setup and launch script:

```cmd
run_desktop_app.bat
```

This script will:
- Verify Python installation
- Check that `requirements.txt` exists
- Check whether required libraries are already installed
  - If any are missing, it lists them and asks for confirmation to install
- After dependencies are ready, it asks for confirmation to open the application (Y/N)
- Launch the desktop app (uses `pythonw.exe` on Windows to avoid a lingering console) and closes the console window

### Option 2: Manual Installation

**Requirements:**
- Python 3.x
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Desktop Application (GUI)

**Automated launch:**
```cmd
run_desktop_app.bat
```

What to expect:
- The script shows dependency checks and, if needed, asks to install missing libraries
- You will be asked to confirm opening the application (Y/N)
- The console window closes after launch (use manual launch for debugging)

**Manual launch:**
```bash
python desktop_app.py
```

Keyboard shortcuts:
- Enter: Fetch transcript
- Ctrl+S: Save/download transcript

UI details:
- Modernized minimal UI using ttk styles
- Indeterminate progress bar while fetching
- Status message at the bottom with a smaller font size

**How it works:**
1. **Enter URL**: Paste the YouTube video URL
2. **Filename**: Default filename provided, can be changed
3. **Fetch Transcript**: Click to see transcript preview
4. **Download**: Save transcript as Markdown file

### Command Line Interface (CLI)

**Basic usage:**
```bash
python app.py
```

**With URL argument:**
```bash
python app.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Available options:**
- `-o` or `--output`: Specify output filename (default: `transcript.md`)
- `-l` or `--language`: Define transcript language (e.g., `en`, `es`)

**Example:**
```bash
python app.py -l es -o my_transcript.md
```

## Output Format

The generated `.md` file will have the following structure:

```markdown
# Video Transcript

URL: https://www.youtube.com/watch?v=VIDEO_ID_HERE

This is the first paragraph of the transcript, combining several spoken segments for readability.

This is the next paragraph, ensuring the text flows naturally.
```

## Fonts

- The desktop app bundles and uses `JetBrains Mono` for the entire UI and transcript area.
- Fonts are loaded privately at runtime (Windows) and are not installed system-wide.
- Place font files under `assets/fonts/` (already included). If the exact font family name differs, the app falls back to common monospace fonts (e.g., Consolas).

## Troubleshooting

### Error: Python not found
If the automated script shows "Python is not installed or not found in PATH":
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart terminal and run the script again

### Error: Library installation failed
If dependencies don't install correctly:
1. Verify internet connection
2. Run manually: `pip install -r requirements.txt`
3. If error persists, update pip: `python -m pip install --upgrade pip`

### Application won't start
If the desktop application doesn't run:
1. Verify all dependencies are installed
2. Run manually: `python desktop_app.py`
3. Check error messages in terminal
4. On Windows, to keep the console open for diagnostics, use manual launch instead of the `.bat` script (the script launches with `pythonw.exe` and closes the console)