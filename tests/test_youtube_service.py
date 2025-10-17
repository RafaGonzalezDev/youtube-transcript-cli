import pytest

from youtube_transcript_api import NoTranscriptFound

from core.services.youtube_service import YouTubeService


def test_extract_video_id_from_standard_url():
    """Tests that the video ID is correctly extracted from a standard YouTube watch URL."""
    service = YouTubeService()
    video_id = service.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_from_short_url():
    """Tests that the video ID is correctly extracted from a shortened youtu.be URL."""
    service = YouTubeService()
    video_id = service.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_extract_video_id_returns_none_for_invalid_url():
    """Tests that None is returned when the URL is not a valid YouTube URL."""
    service = YouTubeService()
    assert service.extract_video_id("https://example.com/video") is None


def test_segment_field_supports_objects_without_get():
    """
    Tests that the _segment_field utility can extract data from objects
    that use attributes instead of a `get` method (i.e., are not dicts).
    """
    service = YouTubeService()

    class SegmentObject:
        def __init__(self):
            self.start = 1.5
            self.duration = 3.2
            self.text = "sample"

    segment = SegmentObject()

    assert service._segment_field(segment, "start", 0.0) == 1.5
    assert service._segment_field(segment, "duration", 0.0) == 3.2
    assert service._segment_field(segment, "text", "") == "sample"


def test_fetch_transcript_deduplicates_languages(monkeypatch):
    """
    Tests that the list of available languages is correctly deduplicated
    when a language is available in both manual and generated forms.
    """
    service = YouTubeService()

    class FakeTranscript:
        def __init__(self, language_code, is_generated):
            self.language_code = language_code
            self.is_generated = is_generated

        def fetch(self):
            return [{"start": 0, "duration": 1, "text": "hello"}]

    class FakeTranscriptList:
        def __init__(self, transcripts):
            self._transcripts = transcripts

        def __iter__(self):
            return iter(self._transcripts)

        def find_transcript(self, codes):
            for transcript in self._transcripts:
                if transcript.language_code in codes:
                    return transcript
            raise NoTranscriptFound

    transcripts = [
        FakeTranscript("en", False),
        FakeTranscript("en", True),
        FakeTranscript("es", True),
    ]

    def fake_list_transcripts(_video_id):
        return FakeTranscriptList(transcripts)

    monkeypatch.setattr(
        "core.services.youtube_service.YouTubeTranscriptApi.list_transcripts",
        fake_list_transcripts,
    )

    segments, languages, selected_language, _ = service.fetch_transcript("abc123xyz00", None)

    assert languages == ["en", "es"]
    assert selected_language in {"en", "es"}
    assert segments[0].text == "hello"
