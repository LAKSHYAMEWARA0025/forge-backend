
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
    def apply_chat_edit(chat_prompt: str, current_config: dict) -> dict:
        """
        Process user's chat edit request and return structured edit instructions
        """
        
        # Extract current values safely
        try:
            entry_anim = current_config.get('tracks', {}).get('text', {}).get('animation', {}).get('entry', {}).get('presetId', 'unknown')
            exit_anim = current_config.get('tracks', {}).get('text', {}).get('animation', {}).get('exit', {}).get('presetId', 'unknown')
            highlight_anim = current_config.get('tracks', {}).get('text', {}).get('animation', {}).get('highlight', {}).get('presetId', 'unknown')
            video_anim = current_config.get('tracks', {}).get('video', {}).get('animation', {}).get('presetId', 'unknown')
            font_size = current_config.get('tracks', {}).get('text', {}).get('globalStyle', {}).get('fontSize', 'unknown')
            text_color = current_config.get('tracks', {}).get('text', {}).get('globalStyle', {}).get('color', 'unknown')
        except:
            entry_anim = exit_anim = highlight_anim = video_anim = font_size = text_color = 'unknown'
        
        # Build comprehensive prompt with guardrails
        prompt = f"""
You are an AI video editor assistant. Analyze the user's edit request and return structured edit instructions.

ALLOWED EDITS:
1. Text Animations: entry, exit, highlight animations
   - Available entry: fade_in, pop_in, slide_up, slide_down, slide_left, slide_right, slide_up_fade, slide_down_fade, slide_left_fade, slide_right_fade, scale_up, scale_down, scale_up_fade, bounce_in
   - Available exit: fade_out, pop_out, slide_up_out, slide_down_out, slide_left_out, slide_right_out, slide_up_fade_out, slide_down_fade_out, slide_left_fade_out, slide_right_fade_out, scale_down_out, scale_down_fade_out
   - Available highlight: none, pulse, pulse_fade, scale_up, bounce_soft, fade_emphasis, color_emphasis, scale_color_pulse

2. Video Effects: fade in/out only
   - Available: none, fade_in, fade_out, fade_in_out
   - Can enable/disable fadeIn or fadeOut
   - Can change duration and start time

3. Text Styles:
   - globalStyle: fontFamily, fontSize, fontWeight, color, background, padding, borderRadius
   - highlightStyle: color, scale, fontWeight
   - position: anchor, offsetY

4. Highlights: Add/remove word highlights

NOT ALLOWED:
- Changing caption text or timestamps
- Changing video source
- Changing timeline
- Adding/removing audio
- Changing export settings

USER REQUEST: "{chat_prompt}"

CURRENT CONFIG SUMMARY:
- Entry animation: {entry_anim}
- Exit animation: {exit_anim}
- Highlight animation: {highlight_anim}
- Video animation: {video_anim}
- Font size: {font_size}
- Text color: {text_color}

OUTPUT FORMAT (JSON only, no markdown):
{{
  "is_allowed": true/false,
  "edits": [
    {{
      "action": "update_text_animation",
      "target": "entry",
      "preset_id": "slide_up_fade",
      "duration": 0.3
    }}
  ],
  "message": "User-friendly message explaining what was changed",
  "rejection_reason": "Only if is_allowed is false, explain why"
}}

EDIT ACTIONS:
- update_text_animation: {{action, target (entry/exit/highlight), preset_id, duration (optional)}}
- update_video_animation: {{action, preset_id}}
- update_text_style: {{action, target (globalStyle/highlightStyle), properties: {{key: value}}}}
- update_highlight_style: {{action, properties: {{key: value}}}}
- update_text_position: {{action, properties: {{anchor, offsetY}}}}
- update_video_fade: {{action, fade_type (fadeIn/fadeOut), enabled (bool), duration (optional), start (optional)}}
- update_highlights: {{action, operation (add/remove/replace), highlights: [{{captionId, wordStartIndex, wordEndIndex}}]}}

RULES:
1. If request is ambiguous (e.g., "make it better"), set is_allowed=false with rejection_reason="Please be more specific about what you want to change"
2. If request tries to change something not allowed, set is_allowed=false with helpful rejection_reason
3. Support multiple edits in one request
4. Use exact preset IDs from the available lists
5. Provide clear, friendly messages
6. Output ONLY valid JSON, no explanation or markdown

Generate the JSON response now:"""

        response = model.generate_content(prompt)
        raw_text = response.text

        # Clean markdown
        clean_text = _clean_gemini_json(raw_text)

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Gemini:\n{clean_text}")


