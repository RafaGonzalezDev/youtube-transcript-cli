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
    """Encapsulates interactions with the YouTube transcript and metadata APIs."""

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = 5) -> None:
        self._session = session or requests.Session()
        self._timeout = timeout

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
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
        transcript_list, _ = self._get_transcript_list(video_id)
        manual = sorted({t.language_code for t in transcript_list if not t.is_generated})
        generated = sorted({t.language_code for t in transcript_list if t.is_generated})
        return manual, generated

    def _get_transcript_list(self, video_id: str):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except (TranscriptsDisabled, NoTranscriptFound) as exc:
            raise ValueError(
                "No transcripts could be found for this video. They may be disabled."
            ) from exc

        available_languages = sorted({t.language_code for t in transcript_list})
        return transcript_list, available_languages

    def get_video_title(self, video_id: str) -> Optional[str]:
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
