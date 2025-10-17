from dataclasses import dataclass
from typing import List, Optional


from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class TranscriptSegment:
    """
    Represents a single segment of a transcript with timing and text.

    Attributes:
        start: The start time of the segment in seconds.
        duration: The duration of the segment in seconds.
        text: The text content of the segment.
    """
    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class TranscriptData:
    """
    Represents the complete transcript data for a YouTube video.

    Attributes:
        video_id: The unique identifier of the YouTube video.
        url: The full URL of the YouTube video.
        title: The title of the YouTube video.
        language: The language code of the fetched transcript (e.g., 'en', 'es').
        segments: A list of TranscriptSegment objects.
        available_languages: A list of language codes available for the video.
        is_generated: True if the transcript was auto-generated, False if it was
                      manually created, None if unknown.
    """
    video_id: str
    url: str
    title: str
    language: str
    segments: List[TranscriptSegment]
    available_languages: List[str]
    is_generated: Optional[bool] = None

