from core.formatter import MarkdownFormatter
from core.model import TranscriptData, TranscriptSegment


def test_markdown_formatter_renders_metadata_and_segments():
    formatter = MarkdownFormatter()
    transcript = TranscriptData(
        video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Never Gonna Give You Up",
        language="en",
        segments=[
            TranscriptSegment(start=0.0, duration=4.0, text="Never gonna give you up"),
            TranscriptSegment(start=4.2, duration=4.0, text="Never gonna let you down"),
        ],
        available_languages=["en", "es"],
        is_generated=False,
    )

    markdown = formatter.render(transcript)

    assert "# Never Gonna Give You Up" in markdown
    assert "- Video URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ" in markdown
    assert "- [00:00] Never gonna give you up" in markdown
    assert "- [00:04] Never gonna let you down" in markdown
    assert "Available languages: en, es" in markdown
