from __future__ import annotations

from typing import Iterable

from .model import TranscriptData, TranscriptSegment


class MarkdownFormatter:
    """Render transcript data into a readable Markdown document."""

    def render(self, transcript: TranscriptData) -> str:
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
        total_seconds = max(int(seconds), 0)
        minutes, secs = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
