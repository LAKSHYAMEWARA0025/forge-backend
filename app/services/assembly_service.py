# app/services/assembly_service.py

import assemblyai as aai
from app.config import settings
from app.db.supabase import get_supabase
from app.services.schema_service import merge_gemini_into_schema
from app.services.gemini_service import GeminiService   # teammate module

class AssemblyService:

    @staticmethod
    def transcribe_and_parse(video_url: str) -> dict:
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

        config = aai.TranscriptionConfig(
            sentiment_analysis=True,
            speaker_labels=False,
            format_text=True
        )

        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(video_url, config=config)
        raw = transcript.json_response

        # convert Assembly→Segments
        parsed_segments = []
        for s in raw.get("sentiment_analysis_results", []):
            parsed_segments.append({
                "text": s["text"],
                "start": round(s["start"] / 1000, 2),
                "end": round(s["end"] / 1000, 2),
                "sentiment": s["sentiment"]
            })

        return {
            "segments": parsed_segments,
            "duration": raw.get("audio_duration", None)
        }


def start_transcription(project_id: str, video_url: str):
    supabase = get_supabase()

    # update: pending→working_transcript
    supabase.table("project").update({
        "status": "working_transcript"
    }).eq("project_id", project_id).execute()

    try:
        parsed = AssemblyService.transcribe_and_parse(video_url)

        # now call Gemini
        supabase.table("project").update({
            "status": "working_gemini"
        }).eq("project_id", project_id).execute()

        gemini_out = GeminiService.generate_from_transcript(parsed)

        # merge with stored schema_v0
        merge_gemini_into_schema(project_id, gemini_out)

        # mark ready
        supabase.table("project").update({
            "status": "ready"
        }).eq("project_id", project_id).execute()

    except Exception as e:
        supabase.table("project").update({
            "status": "failed",
            "error": str(e)
        }).eq("project_id", project_id).execute()
