from __future__ import annotations

from typing import Iterable

from .model import TranscriptData, TranscriptSegment


class MarkdownFormatter:
    """Renders transcript data into a human-readable Markdown document."""

    def render(self, transcript: TranscriptData) -> str:
        """
        Renders the complete transcript data into a single Markdown string.

        This method constructs a document with a header containing metadata and a
        body containing the formatted transcript segments.

        Args:
            transcript (TranscriptData): The transcript data to render.

        Returns:
            str: The fully formatted Markdown document.
        """
        header = [
            f"# {transcript.title or 'Video Transcript'}",
            "",
            f"- Video URL: {transcript.url}",
            f"- Language: {transcript.language}",
        ]
        if transcript.available_languages:
            langs = ", ".join(sorted(transcript.available_languages))
            header.append(f"- Available languages: {langs}")
        header.append("")

        body = self._segments_to_markdown(transcript.segments)
        return "\n".join(header + body)

    def _segments_to_markdown(self, segments: Iterable[TranscriptSegment]) -> list[str]:
        """
        Converts an iterable of transcript segments into a list of Markdown lines.

        Each segment is formatted as a list item with a timestamp and its text.

        Args:
            segments (Iterable[TranscriptSegment]): The transcript segments to format.

        Returns:
            list[str]: A list of Markdown-formatted strings.
        """
        lines: list[str] = []
        for segment in segments:
            timestamp = self._format_timestamp(segment.start)
            text = segment.text.replace("\n", " ").strip()
            if not text:
                continue
            lines.append(f"- [{timestamp}] {text}")
        if not lines:
            lines.append("_Transcript returned no readable segments._")
        return lines

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """
        Formats a duration in seconds into a `HH:MM:SS` or `MM:SS` string.

        Args:
            seconds (float): The duration in seconds.

        Returns:
            str: The formatted timestamp string.
        """
        total_seconds = max(int(seconds), 0)
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
