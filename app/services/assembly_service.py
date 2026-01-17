import assemblyai as aai
from app.config import settings

class AssemblyService:

    @staticmethod
    def fetch_transcript(video_url: str):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            sentiment_analysis=True,
            speaker_labels=False,   # we don't need multi-speaker
            format_text=True
        )

        transcript = transcriber.transcribe(
            video_url,
            config=config
        )

        # raw transcript object from assembly ai
        return transcript.json_response
