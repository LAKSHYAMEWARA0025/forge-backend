import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Gemini client (one-time setup)
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-1.5-flash"


class GeminiService:
    @staticmethod
    def refine_transcript(data: dict) -> dict:
        """
        Step 3:
        Takes transcript JSON from backend (AssemblyAI output)
        Returns AI-refined JSON (title + emphasis + animation flags)
        """

        # 1. Prompt banana
        prompt = f"""
You are an AI video editor.

Your task is to convert a transcript into an editing plan.

Rules:
- Generate a short, clear video title
- Do NOT change transcript text
- For each segment, pick 1–3 important emphasis words
- Use animation ONLY for the first segment
- Allowed animation type: fade
- Output ONLY valid JSON (no explanation, no markdown)

Transcript:
{json.dumps(data)}
"""

        # 2. Gemini call
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        # 3. Gemini ka raw text
        raw_text = response.text.strip()

        # 4. JSON parse (IMPORTANT)
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini returned invalid JSON:\n{raw_text}"
            )
