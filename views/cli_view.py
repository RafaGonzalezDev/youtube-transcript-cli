from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional

from core import TranscriptController

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """
    Builds and configures the argument parser for the command-line interface.

    This function sets up the expected arguments, their types, default values,
    and help messages.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description="Download YouTube video transcripts in Markdown format.")
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("-o", "--output", default="transcript.md", help="Output filename")
    parser.add_argument("-l", "--language", help="Transcript language code (e.g., en, es)")
    parser.add_argument(
        "--list-languages",
        action="store_true",
        help="List available transcript languages for the provided URL and exit.",
    )
    return parser


def run_cli(argv: Optional[Iterable[str]] = None) -> int:
    """
    Runs the command-line interface for the YouTube transcript downloader.

    This function parses command-line arguments, interacts with the TranscriptController
    to fetch transcript data, and handles the overall execution flow, including
    error handling and user feedback.

    Args:
        argv (Optional[Iterable[str]], optional): A list of command-line arguments
                                                 (for testing purposes). Defaults to None.

    Returns:
        int: An exit code (0 for success, 1 for failure).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # If the URL is not provided as an argument, prompt the user to enter it.
    url = args.url or input("Please enter the YouTube video URL: ").strip()
    controller = TranscriptController()

    try:
        # If the --list-languages flag is used, list available languages and exit.
        if args.list_languages:
            manual, generated = controller.list_languages(url)
            _print_languages(manual, generated)
            return 0

        # Fetch the transcript and save it to the specified output file.
        _, markdown = controller.fetch_transcript(url, args.language)
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Transcript saved to {output_path.resolve()}")
        return 0
    except ValueError as exc:
        # Handle known errors, such as invalid URLs or unavailable transcripts.
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        # Handle unexpected errors and log them for debugging.
        logger.exception("Unhandled exception while running CLI")
        print(f"An unexpected error occurred: {exc}")
        return 1


def _print_languages(manual: list[str], generated: list[str]) -> None:
    """
    Prints the available manual and generated transcript languages.

    Args:
        manual (list[str]): A list of manually created transcript language codes.
        generated (list[str]): A list of auto-generated transcript language codes.
    """
    if not manual and not generated:
        print("No transcripts are available for this video.")
        return

    print("Available transcript languages:")
    if manual:
        print(f"  Manual:    {', '.join(manual)}")
    if generated:
        print(f"  Generated: {', '.join(generated)}")
