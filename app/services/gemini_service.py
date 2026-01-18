
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-2.5-flash"

model = genai.GenerativeModel(MODEL_NAME)


def _clean_gemini_json(raw_text: str) -> str:
    """
    Gemini kabhi-kabhi JSON ko ```json ... ``` ke andar bhej deta hai.
    Ye function us markdown ko hata deta hai.
    """
    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = (
            raw_text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

    return raw_text


class GeminiService:
    @staticmethod
    def refine_transcript(data: dict) -> dict:
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

        response = model.generate_content(prompt)
        raw_text = response.text

        # 🔹 CLEAN MARKDOWN
        clean_text = _clean_gemini_json(raw_text)

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Gemini:\n{clean_text}")

    @staticmethod
    def apply_chat_edit(chat_prompt: str, previous_schema: dict) -> dict:
        prompt = f"""
You are an AI video editor assistant.

Rules:
- Modify ONLY what the user asks
- Do NOT change timestamps
- Do NOT change transcript text
- Keep schema structure same
- Output ONLY valid JSON

User request:
"{chat_prompt}"

Current schema:
{json.dumps(previous_schema)}
"""

        response = model.generate_content(prompt)
        raw_text = response.text

        # 🔹 CLEAN MARKDOWN
        clean_text = _clean_gemini_json(raw_text)

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Gemini:\n{clean_text}")


