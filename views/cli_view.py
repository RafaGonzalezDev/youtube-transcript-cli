from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional

from core import TranscriptController

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
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
    parser = build_parser()
    args = parser.parse_args(argv)

    url = args.url or input("Please enter the YouTube video URL: ").strip()
    controller = TranscriptController()

    try:
        if args.list_languages:
            manual, generated = controller.list_languages(url)
            _print_languages(manual, generated)
            return 0

        _, markdown = controller.fetch_transcript(url, args.language)
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Transcript saved to {output_path.resolve()}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        logger.exception("Unhandled exception while running CLI")
        print(f"An unexpected error occurred: {exc}")
        return 1


def _print_languages(manual: list[str], generated: list[str]) -> None:
    if not manual and not generated:
        print("No transcripts are available for this video.")
        return

    print("Available transcript languages:")
    if manual:
        print(f"  Manual:    {', '.join(manual)}")
    if generated:
        print(f"  Generated: {', '.join(generated)}")
