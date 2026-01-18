import datetime


def seconds_to_ass_time(seconds: float) -> str:
    """
    Convert seconds (float) to ASS time format: H:MM:SS.xx
    """
    total_seconds = int(seconds)
    ms = int((seconds - total_seconds) * 100)

    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    return f"{h}:{m:02}:{s:02}.{ms:02}"


def generate_ass_header(title: str) -> str:
    """
    Generate ASS subtitle header + default style
    """
    return f"""[Script Info]
Title: {title}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def apply_emphasis(text: str, emphasis_words: list) -> str:
    """
    Highlight emphasis words using ASS color tags
    """
    for word in emphasis_words:
        text = text.replace(
            word,
            r"{\c&H00FFFF00&}" + word + r"{\c&H00FFFFFF&}"
        )
    return text


def generate_dialogue_line(segment: dict) -> str:
    """
    Convert a single schema segment to ASS Dialogue line
    """
    start = seconds_to_ass_time(segment["start"])
    end = seconds_to_ass_time(segment["end"])

    text = segment["text"]
    emphasis_words = segment.get("emphasis_words", [])

    if emphasis_words:
        text = apply_emphasis(text, emphasis_words)

    return f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"


class RenderService:
    @staticmethod
    def prepare_ffmpeg_config(schema: dict) -> dict:
        """
        Step 9:
        Convert final approved schema into FFmpeg-ready render config
        (ASS subtitles generation)
        """

        title = schema.get("video_title", "Video")
        segments = schema.get("segments", [])

        ass_text = generate_ass_header(title)

        for segment in segments:
            ass_text += generate_dialogue_line(segment) + "\n"

        return {
            "ass_subtitles": ass_text,
            "title": title
        }


