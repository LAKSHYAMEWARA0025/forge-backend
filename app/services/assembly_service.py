import assemblyai as aai
from app.config import settings
from typing import Dict, Any


class AssemblyService:

    @staticmethod
    async def transcribe_video(video_url: str) -> Dict[str, Any]:
        """
        Transcribe video using AssemblyAI
        Returns word-by-word timestamps for LLM processing
        """
        print(f"Starting transcription for video: {video_url}")
        
        # Configure API
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

        config = aai.TranscriptionConfig(
            sentiment_analysis=False,
            speaker_labels=False,
            format_text=True
        )

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_url, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")

        raw = transcript.json_response
        
        # Extract word-level timestamps
        words = []
        for word_data in raw.get("words", []):
            words.append({
                "text": word_data["text"],
                "start": word_data["start"],  # milliseconds
                "end": word_data["end"],  # milliseconds
                "confidence": word_data["confidence"],
                "speaker": word_data.get("speaker")
            })
        
        transcription_data = {
            "text": raw.get("text", ""),
            "words": words,
            "duration": raw.get("audio_duration", 0) / 1000,  # Convert to seconds
            "confidence": raw.get("confidence", 0)
        }
        
        print(f"Transcription completed. Word count: {len(words)}")
        return transcription_data

    @staticmethod
    def parse_transcript(raw: dict):
        """
        Converts AssemblyAI format → our simplified segment structure for Gemini
        """
        sentiments = raw.get("sentiment_analysis_results", [])
        duration = raw.get("audio_duration", 0)

        segments = []

        for s in sentiments:
            segments.append({
                "text": s["text"],
                "start": round(s["start"] / 1000, 2),
                "end": round(s["end"] / 1000, 2),
                "sentiment": s["sentiment"]
            })

        parsed = {
            "segments": segments,
            "duration": duration
        }

        return parsed


    @staticmethod
    def transcribe_and_parse(video_url: str) -> dict:
        """
        Fetch raw transcript from AssemblyAI + convert to simplified format
        """
        # Configure API
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

        config = aai.TranscriptionConfig(
            sentiment_analysis=True,
            speaker_labels=False,
            format_text=True
        )

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_url, config=config)

        raw = transcript.json_response

        # Parse directly from raw
        return AssemblyService.parse_transcript(raw)
