import copy
from typing import Dict, Any, List


class SchemaService:

    @staticmethod
    def merge_gemini_into_schema(
        base_schema: Dict[str, Any],
        gemini_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gemini gives something like:
        {
            "title": "...",
            "segments": [
                { id, text, start, end, emphasis_words?, animation? }
            ]
        }

        We convert + merge into our main schema format.

        Merging rules:
        - override only things gemini provides
        - keep base values for missing fields
        - keep extra old captions (Option-1 safe)
        """

        new_schema = copy.deepcopy(base_schema)

        # ---- Title ----
        title_text = gemini_json.get("title")
        if title_text:
            if "tracks" not in new_schema:
                new_schema["tracks"] = {}

            if "text" not in new_schema["tracks"]:
                new_schema["tracks"]["text"] = {}

            new_schema["tracks"]["text"]["title"] = SchemaService._make_title_block(
                title_text,
                base=new_schema["tracks"]["text"].get("title")
            )

        # ---- Captions (Segments) ----
        gem_segments = gemini_json.get("segments", [])
        old_captions = new_schema.get("tracks", {}).get("text", {}).get("captions", [])

        merged = SchemaService._merge_segments(old_captions, gem_segments)
        new_schema["tracks"]["text"]["captions"] = merged

        return new_schema


    @staticmethod
    def _make_title_block(text: str, base: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Builds title metadata with fallback to previous version.
        """

        default_title = {
            "id": base.get("id") if base else "title_001",
            "type": "title",
            "content": text,
            "start": base.get("start", 0) if base else 0,
            "end": base.get("end", 3) if base else 3,
            "style": base.get("style", {
                "fontFamily": "Inter",
                "fontSize": 64,
                "fontWeight": 800,
                "color": "#ffffff",
                "background": "rgba(0,0,0,0.45)",
                "padding": [24, 32],
                "borderRadius": 16
            }) if base else {
                "fontFamily": "Inter",
                "fontSize": 64,
                "fontWeight": 800,
                "color": "#ffffff",
                "background": "rgba(0,0,0,0.45)",
                "padding": [24, 32],
                "borderRadius": 16
            },
            "position": base.get("position", {
                "anchor": "top_center",
                "offsetY": 160
            }) if base else {
                "anchor": "top_center",
                "offsetY": 160
            },
            "animation": base.get("animation", {
                "in": {"type": "slide_down_fade", "duration": 0.5},
                "out": {"type": "fade", "duration": 0.3}
            }) if base else {
                "in": {"type": "slide_down_fade", "duration": 0.5},
                "out": {"type": "fade", "duration": 0.3}
            }
        }

        return default_title


    @staticmethod
    def _merge_segments(
        old: List[Dict[str, Any]],
        new: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply Gemini output onto old captions.
        Option-1 safe behavior for extra old segments.
        """

        merged = []

        for i, seg in enumerate(new):
            base = old[i] if i < len(old) else SchemaService._default_caption_block(i)
            merged.append(SchemaService._merge_segment(base, seg, i))

        # Option-1: keep extra old captions not touched by Gemini
        if len(old) > len(new):
            for j in range(len(new), len(old)):
                merged.append(old[j])

        return merged


    @staticmethod
    def _merge_segment(base: Dict[str, Any], gem: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """
        Field-level selective override.
        """

        out = copy.deepcopy(base)

        # text override
        if gem.get("text"):
            out["content"] = gem["text"]

        # timing override
        if gem.get("start") is not None:
            out["start"] = gem["start"]

        if gem.get("end") is not None:
            out["end"] = gem["end"]

        # emphasis (future use)
        if gem.get("emphasis_words"):
            out["emphasis_words"] = gem["emphasis_words"]

        # animation override (deep merge)
        if "animation" in gem:
            out["animation"] = {**base.get("animation", {}), **gem["animation"]}

        # style override (deep merge)
        if "style" in gem:
            out["style"] = {**base.get("style", {}), **gem["style"]}

        # effects override (deep merge)
        if "effects" in gem:
            out["effects"] = {**base.get("effects", {}), **gem["effects"]}

        return out


    @staticmethod
    def _default_caption_block(i: int) -> Dict[str, Any]:
        """
        For new Gemini segments when old does not exist.
        """

        return {
            "id": f"caption_{i}",
            "type": "caption",
            "content": "",
            "start": 0,
            "end": 1,
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
            },
            "animation": {
                "in": {"type": "slide_up_fade", "duration": 0.4},
                "out": {"type": "fade", "duration": 0.3}
            }
        }
