import assemblyai as aai
from app.config import settings
from app.db.supabase import get_supabase
from app.services.schema_service import apply_gemini_to_schema


class AssemblyService:

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
    

    @staticmethod
    def start_transcription(project_id: str, video_url: str):
        supabase = get_supabase()

        # Step 1: AssemblyAI → parsed
        parsed = AssemblyService.transcribe_and_parse(video_url)

        # Step 2: Store parsed in DB as intermediate
        supabase.table("project").update({
            "intermediate_transcript": parsed,   # optional column for debugging
            "status": "transcribed"
        }).eq("project_id", project_id).execute()

        # Step 3: return parsed so another service can handoff
        return parsed


# now we need to return or call this to netram's function
