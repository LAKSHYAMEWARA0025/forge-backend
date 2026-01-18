"""
Config update service - Apply changes to edit configuration
"""
import copy
from typing import Dict, Any


class ConfigUpdateService:
    """Service for applying edits to configuration"""
    
    @staticmethod
    def apply_edit(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a single edit to the configuration
        Returns updated config
        """
        action = edit.get("action")
        
        if action == "update_text_animation":
            return ConfigUpdateService._update_text_animation(config, edit)
        
        elif action == "update_video_animation":
            return ConfigUpdateService._update_video_animation(config, edit)
        
        elif action == "update_text_style":
            return ConfigUpdateService._update_text_style(config, edit)
        
        elif action == "update_highlight_style":
            return ConfigUpdateService._update_highlight_style(config, edit)
        
        elif action == "update_text_position":
            return ConfigUpdateService._update_text_position(config, edit)
        
        elif action == "update_video_fade":
            return ConfigUpdateService._update_video_fade(config, edit)
        
        elif action == "update_highlights":
            return ConfigUpdateService._update_highlights(config, edit)
        
        return config
    
    @staticmethod
    def _update_text_animation(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update text animation (entry, exit, highlight)"""
        target = edit.get("target")  # entry, exit, or highlight
        preset_id = edit.get("preset_id")
        duration = edit.get("duration")
        
        # Update preset ID
        config["tracks"]["text"]["animation"][target]["presetId"] = preset_id
        
        # Update duration if provided
        if duration is not None:
            config["tracks"]["text"]["animation"][target]["duration"] = duration
        
        return config
    
    @staticmethod
    def _update_video_animation(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update video animation preset"""
        preset_id = edit.get("preset_id")
        
        config["tracks"]["video"]["animation"]["presetId"] = preset_id
        
        return config
    
    @staticmethod
    def _update_text_style(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update text style (globalStyle or highlightStyle)"""
        target = edit.get("target")  # globalStyle or highlightStyle
        properties = edit.get("properties", {})
        
        # Update each property
        for key, value in properties.items():
            config["tracks"]["text"][target][key] = value
        
        return config
    
    @staticmethod
    def _update_highlight_style(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update highlight style"""
        properties = edit.get("properties", {})
        
        # Update each property
        for key, value in properties.items():
            config["tracks"]["text"]["highlightStyle"][key] = value
        
        return config
    
    @staticmethod
    def _update_text_position(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update text position"""
        properties = edit.get("properties", {})
        
        # Update each property
        for key, value in properties.items():
            config["tracks"]["text"]["globalStyle"]["position"][key] = value
        
        return config
    
    @staticmethod
    def _update_video_fade(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update video fade in/out"""
        fade_type = edit.get("fade_type")  # fadeIn or fadeOut
        
        # Check if we need to enable/disable
        if "enabled" in edit:
            if edit["enabled"]:
                # Enable fade - ensure it exists
                if fade_type not in config["tracks"]["video"]["animation"]:
                    # Set default values
                    if fade_type == "fadeIn":
                        config["tracks"]["video"]["animation"][fade_type] = {
                            "start": 0.0,
                            "duration": 0.8
                        }
                    else:  # fadeOut
                        video_duration = config["meta"]["duration"]
                        config["tracks"]["video"]["animation"][fade_type] = {
                            "start": max(0, video_duration - 2.0),
                            "duration": 2.0
                        }
            else:
                # Disable fade - remove it
                if fade_type in config["tracks"]["video"]["animation"]:
                    del config["tracks"]["video"]["animation"][fade_type]
                return config
        
        # Update duration if provided
        if "duration" in edit and fade_type in config["tracks"]["video"]["animation"]:
            config["tracks"]["video"]["animation"][fade_type]["duration"] = edit["duration"]
        
        # Update start if provided
        if "start" in edit and fade_type in config["tracks"]["video"]["animation"]:
            config["tracks"]["video"]["animation"][fade_type]["start"] = edit["start"]
        
        return config
    
    @staticmethod
    def _update_highlights(config: Dict[str, Any], edit: Dict[str, Any]) -> Dict[str, Any]:
        """Update highlights (add/remove/replace)"""
        operation = edit.get("operation", "replace")  # add, remove, or replace
        highlights = edit.get("highlights", [])
        
        if operation == "replace":
            # Replace all highlights
            config["tracks"]["text"]["highlights"] = highlights
        
        elif operation == "add":
            # Add new highlights
            existing = config["tracks"]["text"]["highlights"]
            config["tracks"]["text"]["highlights"] = existing + highlights
        
        elif operation == "remove":
            # Remove specific highlights
            existing = config["tracks"]["text"]["highlights"]
            caption_ids_to_remove = [h["captionId"] for h in highlights]
            config["tracks"]["text"]["highlights"] = [
                h for h in existing if h["captionId"] not in caption_ids_to_remove
            ]
        
        return config
