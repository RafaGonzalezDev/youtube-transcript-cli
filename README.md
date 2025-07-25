# YouTube Transcript Downloader

Tool to download YouTube video transcripts in Markdown format. Available as both a command-line interface (CLI) and a desktop application (GUI).

## Key Features

- **Extracts Video ID**: Automatically extracts the YouTube video ID from various URL formats.
- **Multi-language Support**: Downloads transcripts in a specified language if available.
- **Markdown Formatting**: Formats the transcript into a clean, readable Markdown file.
- **CLI and GUI**: Use the tool from your terminal or through a user-friendly desktop interface.

## Requirements

- Python 3.x
- Install all dependencies from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Desktop Application (GUI)

For a graphical interface, run:

```bash
python desktop_app.py
```

**How it works:**
1.  **Enter URL**: Paste the YouTube video URL.
2.  **Filename**: A default filename `youtube_transcript.txt` is provided. You can change it if you wish.
3.  **Fetch Transcript**: Click to see a preview of the transcript.
4.  **Download Transcript**: Save the transcript to a Markdown file.

### Command Line Interface (CLI)

To use the script from your terminal:

```bash
python app.py
```

The script will prompt you to enter the YouTube video URL.

**CLI Options:**

-   `-o` or `--output`: Specify the output filename. (Default: `transcript.md`)
-   `-l` or `--language`: Define the transcript language (e.g., `en`, `es`).

**Example:**

```bash
python app.py -l es -o mi_transcripcion.md
```

## Output Format

The generated `.md` file will be structured as follows:

```markdown
# Video Transcript

URL: https://www.youtube.com/watch?v=VIDEO_ID_HERE

This is the first paragraph of the transcript, combining several spoken segments for readability.

This is the next paragraph, ensuring the text flows naturally.
```