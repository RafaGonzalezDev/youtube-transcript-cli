# YouTube Transcript Downloader

Tool to download YouTube video transcripts in Markdown format. Available as both a command-line interface (CLI) and a desktop application (GUI).

## Key Features

- **Automatic ID Extraction**: Automatically extracts YouTube video ID from various URL formats
- **Multi-language Support**: Downloads transcripts in specified language if available
- **Markdown Formatting**: Converts transcript into clean, readable Markdown file
- **CLI and GUI**: Use the tool from terminal or through a graphical interface
- **Automated Setup**: Setup script that verifies Python and installs dependencies

## Quick Installation (Windows)

### Option 1: Automated Script (Recommended)

Run the automated setup and launch script:

```cmd
run_desktop_app.bat
```

This script:
- Verifies Python installation
- Shows libraries to be installed:
  - youtube-transcript-api (>=0.6.0)
  - requests (>=2.25.0)
  - beautifulsoup4 (>=4.9.0)
- Requests confirmation before installing
- Automatically launches the desktop application

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

**Manual launch:**
```bash
python desktop_app.py
```

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