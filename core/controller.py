from __future__ import annotations

import logging
from typing import Optional, Tuple

from .formatter import MarkdownFormatter
from .model import TranscriptData
from .services.youtube_service import YouTubeService

logger = logging.getLogger(__name__)


class TranscriptController:
    """
    Coordinates the fetching of YouTube transcripts and their formatting.

    This class acts as a mediator between the user interface (views) and the
    underlying services (e.g., YouTubeService, MarkdownFormatter). It orchestrates
    the process of validating input, fetching data, and rendering the final output.
    """

    def __init__(
        self,
        youtube_service: Optional[YouTubeService] = None,
        formatter: Optional[MarkdownFormatter] = None,
    ) -> None:
        """
        Initializes the TranscriptController with optional service dependencies.

        This allows for dependency injection, making the controller more testable.
        If services are not provided, it creates default instances.

        Args:
            youtube_service (Optional[YouTubeService], optional): An instance of YouTubeService.
                                                               Defaults to None.
            formatter (Optional[MarkdownFormatter], optional): An instance of MarkdownFormatter.
                                                          Defaults to None.
        """
        self.youtube_service = youtube_service or YouTubeService()
        self.formatter = formatter or MarkdownFormatter()

    def validate_and_extract_video_id(self, url: str) -> str:
        """
        Validates a YouTube URL and extracts the video ID.

        Args:
            url (str): The YouTube video URL.

        Raises:
            ValueError: If the video ID cannot be extracted from the URL.

        Returns:
            str: The extracted YouTube video ID.
        """
        video_id = self.youtube_service.extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from the provided URL.")
        return video_id

    def fetch_transcript(self, url: str, language: Optional[str] = None) -> Tuple[TranscriptData, str]:
        """
        Fetches a transcript for a given YouTube URL and formats it as Markdown.

        Args:
            url (str): The YouTube video URL.
            language (Optional[str], optional): The desired language code for the transcript.
                                              Defaults to None.

        Returns:
            Tuple[TranscriptData, str]: A tuple containing the raw transcript data
                                        and the formatted Markdown string.
        """
        video_id = self.validate_and_extract_video_id(url)

        # Fetch raw transcript data from the YouTube service.
        segments, available_languages, lang_code, is_generated = self.youtube_service.fetch_transcript(
            video_id, language
        )
        title = self.youtube_service.get_video_title(video_id) or "Video Transcript"

        # Create a data model with the fetched information.
        transcript = TranscriptData(
            video_id=video_id,
            url=url,
            title=title,
            language=lang_code,
            segments=segments,
            available_languages=available_languages,
            is_generated=is_generated,
        )

        # Render the transcript data into Markdown format.
        markdown = self.formatter.render(transcript)
        return transcript, markdown

    def list_languages(self, url: str) -> Tuple[list[str], list[str]]:
        """
        Lists the available manual and auto-generated transcript languages for a video.

        Args:
            url (str): The YouTube video URL.

        Returns:
            Tuple[list[str], list[str]]: A tuple containing two lists:
                                         - Manually created language codes.
                                         - Auto-generated language codes.
        """
        video_id = self.validate_and_extract_video_id(url)
        manual, generated = self.youtube_service.list_available_languages(video_id)
        return manual, generated
