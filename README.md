# youtube-transcript-cli

CLI tool to download YouTube video transcripts in Markdown format.

## Key Features

- Extracts YouTube video ID from any URL format
- Downloads transcript in the specified language
- Formats transcript and saves it to a .md file

## Requirements

- Python 3.x
- Install dependency:
```bash
pip install youtube-transcript-api
```

## Basic Usage

To run the script, simply execute the following command in your terminal:

```bash
python app.py
```

The script will then prompt you to enter the YouTube video URL.

### Options

You can still use the following optional flags:

- `-o`: Specify the output filename (default: `transcript.md`)
- `-l`: Define the transcript language (e.g., `en`, `es`)

#### Example with options:

```bash
python app.py -l en -o my_transcript.md
```

After running this command, you will be prompted to paste the video URL.

## Output Example

The generated `transcript.md` file will have a format similar to this:

```markdown
# Video Transcript

URL: https://www.youtube.com/watch?v=PR__eFQsnhg

Lorem ipsum dolor sit amet, consectetur adipiscing elit.

Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
```