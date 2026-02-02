"""
Config service - Generate and manage edit configurations
"""
from typing import Dict, Any
from datetime import datetime
import uuid


class ConfigService:
    """Service for generating and managing edit configurations"""
    
    @staticmethod
    def generate_edit_config(
        job_id: str,
        video_url: str,
        video_metadata: Dict[str, Any],
        llm_response: Any
    ) -> Dict[str, Any]:
        """Generate edit configuration from LLM response"""
        
        video_id = str(uuid.uuid4())
        duration = video_metadata.get("duration", 0)
        width = video_metadata.get("width", 1920)
        height = video_metadata.get("height", 1080)
        aspect_ratio = video_metadata.get("aspect_ratio", "16:9")
        
        # Convert LLM captions to config format
        captions = [
            {
                "id": f"cap_{str(i+1).zfill(3)}",
                "text": cap.text,
                "start": cap.start,
                "end": cap.end,
                "word_count": cap.word_count,
                "duration_ms": cap.duration_ms,
            }
            for i, cap in enumerate(llm_response.captions)
        ]
        
        # Convert highlights
        highlights = [
            {
                "captionId": h.captionId,
                "wordStartIndex": h.wordStartIndex,
                "wordEndIndex": h.wordEndIndex,
            }
            for h in llm_response.highlightedWords
        ]
        
        # Build edit config
        edit_config = {
            "id": job_id,
            "meta": {
                "schemaVersion": "1.1",
                "createdAt": datetime.utcnow().isoformat() + "Z",
                "duration": duration,
                "timeUnit": "seconds",
            },
            "source": {
                "video": {
                    "id": video_id,
                    "url": video_url,
                    "width": width,
                    "height": height,
                    "aspectRatio": aspect_ratio,
                    "duration": duration,
                }
            },
            "timeline": {
                "start": 0,
                "end": duration,
            },
            "tracks": {
                "video": {
                    "animation": {
                        "presetId": "fade_in_out",
                        "fadeIn": {
                            "start": 0.0,
                            "duration": 0.8,
                        },
                        "fadeOut": {
                            "start": max(0, duration - 2.0),
                            "duration": 2.0,
                        },
                    }
                },
                "text": {
                    "globalStyle": {
                        "fontFamily": "Inter",
                        "fontSize": 14,
                        "fontWeight": 700,
                        "color": "#ffffff",
                        "background": "rgba(0,0,0,0.45)",
                        "padding": [12, 16],
                        "borderRadius": 12,
                        "position": {
                            "anchor": "bottom_center",
                            "offsetY": -50,
                        },
                    },
                    "highlightStyle": {
                        "color": llm_response.highlightStyle.color,
                        "scale": llm_response.highlightStyle.scale,
                        "fontWeight": llm_response.highlightStyle.fontWeight,
                    },
                    "animation": {
                        "entry": {
                            "presetId": "slide_up_fade",
                            "duration": 0.2,
                        },
                        "exit": {
                            "presetId": "fade_out",
                            "duration": 0.2,
                        },
                        "highlight": {
                            "presetId": "none",
                            "duration": 0.4,
                        },
                    },
                    "captions": captions,
                    "highlights": highlights,
                },
                "audio": [],
            },
            "settings": {
                "autoCaptions": True,
                "dynamicAnimations": True,
                "highlightKeywords": True,
                "introFadeIn": True,
                "outroFadeOut": True,
            },
            "export": {
                "resolution": {
                    "width": width,
                    "height": height,
                },
                "format": "mp4",
                "burnCaptions": True,
            },
        }
        
        return edit_config
