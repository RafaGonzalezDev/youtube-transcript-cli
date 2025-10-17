from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    duration: float
    text: str


@dataclass(frozen=True)
class TranscriptData:
    video_id: str
    url: str
    title: str
    language: str
    segments: List[TranscriptSegment]
    available_languages: List[str]
    is_generated: Optional[bool] = None
