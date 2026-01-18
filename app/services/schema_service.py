import copy
from typing import Dict, Any, List


class SchemaService:

    @staticmethod
    def merge_gemini_into_schema(
        base_schema: Dict[str, Any],
        gemini_out: Dict[str, Any],
        first_run: bool = True
    ) -> Dict[str, Any]:
        """
        Final canonical Gemini → Schema merge
        first_run = True → title override allowed
        re-edit mode → only override if Gemini provides new title
        """

        new_schema = copy.deepcopy(base_schema)

        # ensure nested keys
        if "tracks" not in new_schema:
            new_schema["tracks"] = {}

        if "text" not in new_schema["tracks"]:
            new_schema["tracks"]["text"] = {}

        # -------- TITLE ----------
        title = gemini_out.get("title")
        if first_run:
            if title:
                new_schema["tracks"]["text"]["title"] = SchemaService._make_title_block(title)
        else:
            # re-edit logic: override only if explicitly provided
            if title:
                prev = new_schema["tracks"]["text"].get("title")
                new_schema["tracks"]["text"]["title"] = SchemaService._make_title_block(title, base=prev)
            # else keep old

        # -------- SEGMENTS (Captions) ----------
        segments = gemini_out.get("segments", [])
        new_captions = []

        for i, seg in enumerate(segments):
            new_captions.append(
                SchemaService._make_caption_block(seg, index=i)
            )

        new_schema["tracks"]["text"]["captions"] = new_captions

        return new_schema

    # ---------------------------------------------------
    # TITLE GEN
    # ---------------------------------------------------
    @staticmethod
    def _make_title_block(text: str, base: Dict[str, Any] = None) -> Dict[str, Any]:

        title = {
            "id": base.get("id") if base else "title_001",
            "type": "title",
            "content": text,
            "start": base.get("start", 0) if base else 0,
            "end": base.get("end", 3) if base else 3,
            "style": base.get("style") if base else {
                "fontFamily": "Inter",
                "fontSize": 64,
                "fontWeight": 800,
                "color": "#ffffff",
                "background": "rgba(0,0,0,0.45)",
                "padding": [24, 32],
                "borderRadius": 16
            },
            "position": base.get("position") if base else {
                "anchor": "top_center",
                "offsetY": 160
            },
            "animation": base.get("animation") if base else {
                "in": {"type": "slide_down_fade", "duration": 0.5},
                "out": {"type": "fade", "duration": 0.3}
            }
        }

        return title

    # ---------------------------------------------------
    # CAPTION GEN
    # ---------------------------------------------------
    @staticmethod
    def _make_caption_block(seg: Dict[str, Any], index: int) -> Dict[str, Any]:

        base = SchemaService._default_caption_style()

        out = {
            "id": f"caption_{index+1:03d}",
            "type": "caption",
            "content": seg.get("text", ""),
            "start": seg.get("start", 0),
            "end": seg.get("end", seg.get("start", 0) + 1),
            "style": base["style"],
            "position": base["position"],
            "animation": SchemaService._resolve_animation(seg),
        }

        if seg.get("emphasis_words"):
            out["emphasis_words"] = seg["emphasis_words"]

        return out

    # ---------------------------------------------------
    # DEFAULTS
    # ---------------------------------------------------
    @staticmethod
    def _default_caption_style():
        return {
            "style": {
                "fontFamily": "Inter",
                "fontSize": 48,
                "fontWeight": 600,
                "color": "#ffffff",
                "background": "rgba(0,0,0,0.45)",
                "padding": [16, 24],
                "borderRadius": 12
            },
            "position": {
                "anchor": "bottom_center",
                "offsetY": -120
            }
        }

    # ---------------------------------------------------
    # ANIMATION LOGIC
    # ---------------------------------------------------
    @staticmethod
    def _resolve_animation(seg: dict) -> dict:
        if "animation" in seg:
            return seg["animation"]

        # default fallback
        return {
            "in": {"type": "slide_up_fade", "duration": 0.4},
            "out": {"type": "fade", "duration": 0.3}
        }
