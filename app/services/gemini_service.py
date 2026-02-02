
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "models/gemini-2.5-flash"

# Configure model with faster generation settings
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config=generation_config
)


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
    async def process_transcription(transcription_data: dict, duration: float):
        """
        Process transcription with Gemini LLM
        Returns grouped captions with highlights
        """
        from app.schemas.llm_schema import LLMResponse
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        print("Processing transcription with Gemini LLM")
        
        # Step 1: Convert words to captions using the conversion function
        words = transcription_data.get("words", [])
        captions = GeminiService._group_words_into_captions(transcription_data)
        
        print(f"Generated {len(captions)} captions from {len(words)} words")
        
        # Step 2: Build simplified prompt (only for highlights and title)
        prompt = GeminiService._build_highlight_prompt(captions, duration)
        
        # Call Gemini in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            # Increase timeout to 120 seconds for larger transcriptions
            print(f"Calling Gemini API with model: {MODEL_NAME}")
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,  # Uses default ThreadPoolExecutor
                    lambda: model.generate_content(prompt)
                ),
                timeout=120.0
            )
            print("Gemini API call completed successfully")
        except asyncio.TimeoutError:
            print("ERROR: Gemini API call timed out after 120 seconds")
            raise Exception("LLM processing timed out. The transcription may be too long. Please try again.")
        except Exception as e:
            print(f"ERROR: Gemini API call failed: {str(e)}")
            raise Exception(f"LLM processing failed: {str(e)}")
        
        # Parse response
        try:
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            llm_data = json.loads(response_text)
            
            # Combine captions with LLM response
            llm_response = LLMResponse(
                title=llm_data.get("title", "Untitled Video"),
                captions=captions,  # Use our generated captions
                highlightedWords=llm_data.get("highlightedWords", []),
                highlightStyle=llm_data.get("highlightStyle", {
                    "color": "#ffd166",
                    "scale": 1.03,
                    "fontWeight": 800
                })
            )
            
            print(f"LLM processing completed. Generated {len(captions)} captions with {len(llm_data.get('highlightedWords', []))} highlights")
            return llm_response
            
        except Exception as e:
            print(f"Failed to parse LLM response: {str(e)}")
            print(f"Response text: {response.text}")
            raise Exception(f"Failed to parse LLM response: {str(e)}")
    
    @staticmethod
    def _group_words_into_captions(transcription_data, max_words=5, max_duration_ms=3000, pause_threshold_ms=300):
        """
        Groups words into natural caption phrases based on pauses, duration, and punctuation
        """
        words = transcription_data['words']
        captions = []
        current_group = []
        caption_id = 1
        
        for i, word in enumerate(words):
            current_group.append(word)
            
            # Check if we should end this caption
            should_break = False
            
            # 1. Check for punctuation
            has_punctuation = any(p in word['text'] for p in ['.', '!', '?', ','])
            
            # 2. Check for pause after this word
            pause_after = 0
            if i < len(words) - 1:
                pause_after = words[i + 1]['start'] - word['end']
            
            # 3. Check caption duration
            if current_group:
                caption_duration = word['end'] - current_group[0]['start']
            else:
                caption_duration = 0
            
            # 4. Check word count
            word_count = len(current_group)
            
            # Decision logic for breaking
            if word_count >= max_words:
                should_break = True
            elif caption_duration >= max_duration_ms:
                should_break = True
            elif pause_after >= pause_threshold_ms:
                should_break = True
            elif has_punctuation and word_count >= 2:
                should_break = True
            
            # Create caption if breaking or last word
            if should_break or i == len(words) - 1:
                if current_group:
                    caption_text = ' '.join([w['text'] for w in current_group])
                    captions.append({
                        'text': caption_text,
                        'start': current_group[0]['start'] / 1000,  # Convert to seconds
                        'end': current_group[-1]['end'] / 1000,
                        'word_count': len(current_group),
                        'duration_ms': current_group[-1]['end'] - current_group[0]['start']
                    })
                    caption_id += 1
                    current_group = []
        
        return captions
    
    @staticmethod
    def _build_highlight_prompt(captions: list, duration: float) -> str:
        """Build simplified prompt for highlights and title only"""
        
        # Create a compact caption list with just text and index
        caption_texts = [f"{i+1}. {cap['text']}" for i, cap in enumerate(captions)]
        captions_str = '\n'.join(caption_texts)
        
        print(f"Building highlight prompt with {len(captions)} captions")
        
        prompt = f"""You are an AI video editor. Analyze these captions and identify key words to highlight.

CAPTIONS:
{captions_str}

DURATION: {duration}s

OUTPUT (JSON only):
{{
  "title": "Short Catchy Title",
  "highlightedWords": [
    {{"captionId": "cap_001", "wordStartIndex": 1, "wordEndIndex": 2}}
  ],
  "highlightStyle": {{"color": "#ffd166", "scale": 1.03, "fontWeight": 800}}
}}

Rules:
- Identify 5-10 important/emotional words to highlight
- captionId format: "cap_001", "cap_002" (3-digit, matches caption number)
- wordStartIndex/wordEndIndex are 0-indexed within each caption
- Return ONLY JSON"""

        return prompt
    
    @staticmethod
    def _build_transcription_prompt(words: list, duration: float) -> str:
        """Build prompt for transcription processing (DEPRECATED - use _build_highlight_prompt)"""
        
        # Compact JSON without indentation to reduce token count
        words_json = json.dumps(words)
        
        print(f"Building prompt with {len(words)} words, prompt size: ~{len(words_json)} chars")
        
        prompt = f"""You are an AI video editor. Analyze this transcription and create captions.

TRANSCRIPTION: {words_json}
DURATION: {duration}s

OUTPUT (JSON only):
{{
  "title": "Short Title",
  "captions": [{{"text": "caption", "start": 0.08, "end": 1.28, "word_count": 5, "duration_ms": 1200}}],
  "highlightedWords": [{{"captionId": "cap_001", "wordStartIndex": 1, "wordEndIndex": 2}}],
  "highlightStyle": {{"color": "#ffd166", "scale": 1.03, "fontWeight": 800}}
}}

Rules:
- Group words into 2-5 word captions
- captionId: "cap_001", "cap_002" (3-digit)
- Timestamps in seconds
- Highlight 5-10 key words
- Return ONLY JSON"""

        return prompt
    
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
You are an AI video editor assistant. Analyze the user's request and respond appropriately.

USER REQUEST: "{chat_prompt}"

CURRENT CONFIG:
- Entry animation: {entry_anim}
- Exit animation: {exit_anim}
- Highlight animation: {highlight_anim}
- Video animation: {video_anim}
- Font size: {font_size}
- Text color: {text_color}

REQUEST TYPES:

1. INFORMATIONAL QUERY (user asking about options/capabilities)
   Examples: "What font styles can I use?", "What animations are available?", "What can I change?"
   Response: Set is_informational=true, provide helpful information in message

2. EDIT REQUEST (user wants to change something)
   Examples: "Change font to Arial", "Make text bigger", "Add slide animation"
   Response: Set is_informational=false, provide edit actions

AVAILABLE OPTIONS:

Text Animations:
- Entry: fade_in, pop_in, slide_up, slide_down, slide_left, slide_right, slide_up_fade, slide_down_fade, slide_left_fade, slide_right_fade, scale_up, scale_down, scale_up_fade, bounce_in
- Exit: fade_out, pop_out, slide_up_out, slide_down_out, slide_left_out, slide_right_out, slide_up_fade_out, slide_down_fade_out, slide_left_fade_out, slide_right_fade_out, scale_down_out, scale_down_fade_out
- Highlight: none, pulse, pulse_fade, scale_up, bounce_soft, fade_emphasis, color_emphasis, scale_color_pulse

Video Effects:
- Available: none, fade_in, fade_out, fade_in_out

Text Styles:
- fontFamily: Any web-safe font (Arial, Helvetica, Times New Roman, Courier, Verdana, Georgia, Palatino, Garamond, Comic Sans MS, Trebuchet MS, Impact, etc.)
- fontSize: Any pixel value (e.g., 24, 32, 48, 64)
- fontWeight: 100-900 (100=thin, 400=normal, 700=bold, 900=black)
- color: Any hex color (e.g., #ffffff, #000000, #ff0000)
- background: Any hex color or "transparent"
- padding: Pixel value (e.g., 8, 12, 16)
- borderRadius: Pixel value (e.g., 0, 4, 8, 12)

Text Position:
- anchor: top, center, bottom
- offsetY: Pixel offset from anchor position

Highlight Styles:
- color: Any hex color
- scale: 1.0-1.5 (size multiplier)
- fontWeight: 100-900

NOT ALLOWED:
- Changing caption text or timestamps
- Changing video source
- Adding/removing audio

OUTPUT FORMAT (JSON only):
{{
  "is_informational": true/false,
  "is_allowed": true/false,
  "edits": [],
  "message": "Helpful response to user",
  "rejection_reason": "Only if is_allowed is false"
}}

EDIT ACTIONS (when is_informational=false and is_allowed=true):
- update_text_animation: {{action, target (entry/exit/highlight), preset_id, duration (optional)}}
- update_video_animation: {{action, preset_id}}
- update_text_style: {{action, target (globalStyle/highlightStyle), properties: {{key: value}}}}
- update_text_position: {{action, properties: {{anchor, offsetY}}}}
- update_video_fade: {{action, fade_type (fadeIn/fadeOut), enabled (bool), duration (optional)}}
- update_highlights: {{action, operation (add/remove/replace), highlights: [{{captionId, wordStartIndex, wordEndIndex}}]}}

RULES:
1. If user is asking "what", "which", "how many", "what are", "show me" → is_informational=true
2. If user is asking to change/update/modify → is_informational=false, provide edits
3. For informational queries, provide detailed, friendly explanations in message
4. For edit requests, provide clear confirmation of what will change
5. If request is ambiguous, ask for clarification
6. Output ONLY valid JSON

Generate JSON:"""

        response = model.generate_content(prompt)
        raw_text = response.text

        # Clean markdown
        clean_text = _clean_gemini_json(raw_text)

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Gemini:\n{clean_text}")


