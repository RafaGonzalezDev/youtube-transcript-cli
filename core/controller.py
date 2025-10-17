from __future__ import annotations

import logging
from typing import Optional, Tuple

from .formatter import MarkdownFormatter
from .model import TranscriptData
from .services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)


class TranscriptController:
    """Coordinates model updates between services and the active view."""

    def __init__(
        self,
        youtube_service: Optional[YouTubeService] = None,
        formatter: Optional[MarkdownFormatter] = None,
    ) -> None:
        self.youtube_service = youtube_service or YouTubeService()
        self.formatter = formatter or MarkdownFormatter()

    def validate_and_extract_video_id(self, url: str) -> str:
        video_id = self.youtube_service.extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from the provided URL.")
        return video_id

    def fetch_transcript(self, url: str, language: Optional[str] = None) -> Tuple[TranscriptData, str]:
        video_id = self.validate_and_extract_video_id(url)

        segments, available_languages, lang_code, is_generated = self.youtube_service.fetch_transcript(
            video_id, language
        )
        title = self.youtube_service.get_video_title(video_id) or "Video Transcript"

        transcript = TranscriptData(
            video_id=video_id,
            url=url,
            title=title,
            language=lang_code,
            segments=segments,
            available_languages=available_languages,
            is_generated=is_generated,
        )

        markdown = self.formatter.render(transcript)
        return transcript, markdown

    def list_languages(self, url: str) -> Tuple[list[str], list[str]]:
        video_id = self.validate_and_extract_video_id(url)
        manual, generated = self.youtube_service.list_available_languages(video_id)
        return manual, generated
