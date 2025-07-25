import sys
import re
import argparse
import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse

# Compilar patrones una sola vez
PATTERNS = [
    re.compile(r'(?:v=|\/)([0-9A-Za-z_-]{11})(?:[\?&].*)?'),
    re.compile(r'youtu\.be\/([0-9A-Za-z_-]{11})'),
    re.compile(r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})')
]

def extract_video_id(url):
    """Extrae el ID del video de YouTube desde varias formas de URL."""
    for pattern in PATTERNS:
        match = pattern.search(url)
        if match and len(match.group(1)) == 11:
            return match.group(1)
    return None

def get_transcript(video_id, language=None):
    """
    Fetches the transcript for a video.
    If a language is specified, it fetches that specific transcript.
    Otherwise, it prioritizes manual over generated transcripts.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        raise ValueError("No transcripts could be found for this video. They may be disabled.")

    if language:
        try:
            transcript = transcript_list.find_transcript([language])
            return transcript.fetch()
        except NoTranscriptFound:
            available_langs = ", ".join([t.language_code for t in transcript_list])
            raise ValueError(f"Language '{language}' not found. Available languages: {available_langs}")

    # Prioritize manual transcripts
    manual_langs = [t.language_code for t in transcript_list if not t.is_generated]
    if manual_langs:
        try:
            return transcript_list.find_transcript(manual_langs).fetch()
        except NoTranscriptFound:
            # Fall through to generated transcripts if something goes wrong
            pass

    # Fallback to any available transcript (usually auto-generated)
    try:
        return transcript_list.find_transcript([t.language_code for t in transcript_list]).fetch()
    except NoTranscriptFound:
        # This should be unreachable if the initial check passed, but is here for safety
        raise ValueError("No transcripts available for this video.")

def get_video_title(url):
    """Extract video title from YouTube URL."""
    try:
        video_id = extract_video_id(url)
        if not video_id:
            return None
        
        # Use YouTube's oEmbed API to get video title
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('title', '')
    except Exception:
        pass
    
    return None

def format_transcript_to_markdown(transcript, url):
    """
    Convierte la transcripción en formato Markdown.
    Args:
        transcript: Lista de segmentos de transcripción.
        url: URL original del video.
    Returns:
        str: Contenido Markdown formateado.
    """
    title = get_video_title(url) or "Video Transcript"
    markdown_content = f"# {title}\n\nURL: {url}\n\n"
    
    # Concatenate all transcript segments into a single paragraph
    transcript_text = " ".join(segment.text for segment in transcript)
    markdown_content += transcript_text
    
    return markdown_content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube video transcript.")
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument("-o", "--output", default="transcript.md", help="Output filename")
    parser.add_argument("-l", "--language", help="Transcript language (e.g., 'en', 'es')")

    args = parser.parse_args()
    if args.url:
        url = args.url
    else:
        url = input("Please enter the YouTube video URL: ")

    # URL validation
    if not urlparse(url).scheme:
        print("Error: Invalid URL")
        exit(1)

    video_id = extract_video_id(url)
    if not video_id:
        print("Error: Could not extract video ID from the provided URL.")
        exit(1)

    try:
        transcript = get_transcript(video_id, args.language)
        markdown_content = format_transcript_to_markdown(transcript, url)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Transcript saved to {args.output}")
    except (ValueError, TranscriptsDisabled, NoTranscriptFound) as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)
