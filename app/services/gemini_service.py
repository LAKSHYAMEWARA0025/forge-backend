import os
import json
from google import genai
from dotenv import load_dotenv


load_dotenv()


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

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = response.text.strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini returned invalid JSON in refine_transcript:\n{raw_text}"
            )

    @staticmethod
    def apply_chat_edit(chat_prompt: str, previous_schema: dict) -> dict:
        """
        Step 6:
        Takes user chat instruction + previous schema
        Returns updated schema using Gemini
        """

        prompt = f"""
You are an AI video editor assistant.

A user wants to modify an existing video edit using natural language.

Rules:
- Modify ONLY what the user asks
- Do NOT remove or change timestamps
- Do NOT change transcript text
- Keep schema structure exactly the same
- If user asks to remove animation, set use_animation = false
- If user asks to increase caption size, update global_style.font_size
- Output ONLY valid JSON (no explanation, no markdown)

User request:
"{chat_prompt}"

Current schema:
{json.dumps(previous_schema)}
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = response.text.strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            raise ValueError(
                f"Gemini returned invalid JSON in apply_chat_edit:\n{raw_text}"
            )
