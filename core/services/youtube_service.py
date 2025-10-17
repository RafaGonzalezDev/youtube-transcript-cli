from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from ..model import TranscriptSegment

logger = logging.getLogger(__name__)

YOUTUBE_ID_PATTERNS = [
    re.compile(r"(?:v=|/)([0-9A-Za-z_-]{11})(?:[\?&].*)?"),
    re.compile(r"youtu\.be/([0-9A-Za-z_-]{11})"),
    re.compile(r"youtube\.com/embed/([0-9A-Za-z_-]{11})"),
]


class YouTubeService:
    """
    Encapsulates interactions with YouTube for fetching transcripts and metadata.

    This service handles:
    - Extracting video IDs from various YouTube URL formats.
    - Fetching available transcript languages.
    - Retrieving transcript data using the `youtube_transcript_api`.
    - Getting video titles by querying YouTube's oEmbed endpoint or by scraping.
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 5) -> None:
        """
        Initializes the YouTubeService.

        Args:
            session: An optional requests.Session object to use for HTTP requests.
            timeout: The timeout in seconds for HTTP requests.
        """
        self._session = session or requests.Session()
        self._timeout = timeout

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extracts the 11-character video ID from a YouTube URL.

        Supports various URL formats (watch, youtu.be, embed).

        Args:
            url: The YouTube URL.

        Returns:
            The extracted video ID, or None if no valid ID is found.
        """
        if not url:
            return None
        for pattern in YOUTUBE_ID_PATTERNS:
            match = pattern.search(url)
            if match and len(match.group(1)) == 11:
                return match.group(1)
        return None

    def fetch_transcript(
        self, video_id: str, language: Optional[str] = None
    ) -> Tuple[List[TranscriptSegment], List[str], str, Optional[bool]]:
        """
        Fetches the transcript for a given video ID.

        It prioritizes the requested language, falls back to manually created
        transcripts, and finally to any available transcript if necessary.

        Args:
            video_id: The ID of the YouTube video.
            language: The preferred language code (e.g., 'en', 'es'). If None,
                      it attempts to find the best available transcript.

        Raises:
            ValueError: If no transcripts are found or the requested language
                        is unavailable.

        Returns:
            A tuple containing:
            - A list of TranscriptSegment objects.
            - A list of all available language codes.
            - The language code of the fetched transcript.
            - A boolean indicating if the transcript was auto-generated (or None).
        """
        transcript_list, available_languages = self._get_transcript_list(video_id)

        transcript = None
        if language:
            try:
                transcript = transcript_list.find_transcript([language])
            except NoTranscriptFound as exc:
                raise ValueError(
                    f"Language '{language}' not found. Available languages: {', '.join(available_languages)}"
                ) from exc

        if transcript is None:
            manual_langs = [t.language_code for t in transcript_list if not t.is_generated]
            if manual_langs:
                try:
                    transcript = transcript_list.find_transcript(manual_langs)
                except NoTranscriptFound:
                    transcript = None

        if transcript is None:
            try:
                transcript = transcript_list.find_transcript(available_languages)
            except NoTranscriptFound as exc:
                raise ValueError("No transcripts available for this video.") from exc

        try:
            raw_segments = transcript.fetch()
        except Exception as exc:
            logger.exception("Failed to fetch transcript for video %s", video_id)
            raise ValueError("An unexpected error occurred while fetching the transcript.") from exc

        unique_languages = sorted(set(available_languages))
        segments = [
            TranscriptSegment(
                start=float(self._segment_field(segment, "start", 0.0)),
                duration=float(self._segment_field(segment, "duration", 0.0)),
                text=str(self._segment_field(segment, "text", "")),
            )
            for segment in raw_segments
        ]
        return segments, unique_languages, transcript.language_code, transcript.is_generated

    def list_available_languages(self, video_id: str) -> Tuple[List[str], List[str]]:
        """
        Lists the available manual and auto-generated transcript languages.

        Args:
            video_id: The ID of the YouTube video.

        Returns:
            A tuple containing two sorted lists: (manual_languages, generated_languages).
        """
        transcript_list, _ = self._get_transcript_list(video_id)
        manual = sorted({t.language_code for t in transcript_list if not t.is_generated})
        generated = sorted({t.language_code for t in transcript_list if t.is_generated})
        return manual, generated

    def _get_transcript_list(self, video_id: str):
        """
        Retrieves the list of available transcripts for a video.

        Args:
            video_id: The ID of the YouTube video.

        Raises:
            ValueError: If transcripts are disabled or not found for the video.

        Returns:
            A tuple containing the TranscriptList object and a list of
            available language codes.
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except (TranscriptsDisabled, NoTranscriptFound) as exc:
            raise ValueError(
                "No transcripts could be found for this video. They may be disabled."
            ) from exc

        available_languages = sorted({t.language_code for t in transcript_list})
        return transcript_list, available_languages

    def get_video_title(self, video_id: str) -> Optional[str]:
        """
        Fetches the video title for a given video ID.

        It first tries to use the oEmbed endpoint for a reliable JSON response.
        If that fails, it falls back to scraping the video's watch page HTML.

        Args:
            video_id: The ID of the YouTube video.

        Returns:
            The video title as a string, or None if it cannot be fetched.
        """
        if not video_id:
            return None
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        oembed_url = f"https://www.youtube.com/oembed?url={watch_url}&format=json"

        try:
            response = self._session.get(oembed_url, timeout=self._timeout)
            if response.status_code == 200:
                data = response.json()
                return data.get("title")
        except Exception:
            logger.debug("oEmbed lookup failed for %s", video_id, exc_info=True)

        try:
            response = self._session.get(watch_url, timeout=self._timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.text.strip()
                    if title.endswith(" - YouTube"):
                        title = title[:-10]
                    return title
        except Exception:
            logger.debug("Fallback title scraping failed for %s", video_id, exc_info=True)

        return None

    @staticmethod
    def _segment_field(segment, name: str, default):
        """
        Safely extracts a field from a transcript segment object or dictionary.

        This utility function handles inconsistencies in the structure of segment
        objects returned by different versions of the underlying API.

        Args:
            segment: The segment object or dictionary.
            name: The name of the field to extract (e.g., 'start', 'text').
            default: The default value to return if the field is not found.

        Returns:
            The value of the field, or the default value.
        """
        if isinstance(segment, dict):
            return segment.get(name, default)

        # Some versions expose attributes directly
        if hasattr(segment, name):
            value = getattr(segment, name)
            if value is not None:
                return value

        # Allow objects to provide a mapping representation
        to_dict = getattr(segment, "to_dict", None)
        if callable(to_dict):
            try:
                data = to_dict()
                if isinstance(data, dict):
                    return data.get(name, default)
            except Exception:
                logger.debug("Failed to convert transcript segment to dict", exc_info=True)

        # Provide fallbacks for known aliases
        aliases = {
            "start": ("offset", "time"),
            "duration": ("length",),
            "text": ("snippet",),
        }
        for alias in aliases.get(name, ()):
            if isinstance(segment, dict):
                if alias in segment:
                    return segment[alias]
            elif hasattr(segment, alias):
                value = getattr(segment, alias)
                if value is not None:
                    return value

        return default
