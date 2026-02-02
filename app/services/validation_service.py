"""
Validation service - Guardrails for edit requests
"""
from app.animation_presets import is_valid_preset, get_all_presets


class ValidationService:
    """Service for validating edit requests and changes"""
    
    # Allowed edit actions
    ALLOWED_ACTIONS = [
        "update_text_animation",
        "update_video_animation",
        "update_text_style",
        "update_highlight_style",
        "update_highlights",
        "update_video_fade",
        "update_text_position",
    ]
    
    # Allowed style properties
    ALLOWED_GLOBAL_STYLE_PROPS = [
        "fontFamily",
        "fontSize",
        "fontWeight",
        "color",
        "background",
        "padding",
        "borderRadius",
    ]
    
    ALLOWED_HIGHLIGHT_STYLE_PROPS = [
        "color",
        "scale",
        "fontWeight",
    ]
    
    ALLOWED_POSITION_PROPS = [
        "anchor",
        "offsetY",
    ]
    
    @staticmethod
    def validate_animation_preset(animation_type: str, preset_id: str) -> tuple[bool, str]:
        """
        Validate animation preset
        Returns: (is_valid, error_message)
        """
        if animation_type not in ["entry", "exit", "highlight", "video"]:
            return False, f"Invalid animation type: {animation_type}"
        
        if not is_valid_preset(animation_type, preset_id):
            available = get_all_presets()[animation_type]
            return False, f"Invalid {animation_type} animation preset: {preset_id}. Available: {', '.join(available)}"
        
        return True, ""
    
    @staticmethod
    def validate_edit_action(action: str) -> tuple[bool, str]:
        """
        Validate if edit action is allowed
        Returns: (is_valid, error_message)
        """
        if action not in ValidationService.ALLOWED_ACTIONS:
            return False, f"Action '{action}' is not allowed"
        
        return True, ""
    
    @staticmethod
    def validate_style_properties(target: str, properties: dict) -> tuple[bool, str]:
        """
        Validate style properties
        Returns: (is_valid, error_message)
        """
        if target == "globalStyle":
            allowed = ValidationService.ALLOWED_GLOBAL_STYLE_PROPS
        elif target == "highlightStyle":
            allowed = ValidationService.ALLOWED_HIGHLIGHT_STYLE_PROPS
        else:
            return False, f"Invalid style target: {target}"
        
        for prop in properties.keys():
            if prop not in allowed:
                return False, f"Property '{prop}' is not allowed for {target}. Allowed: {', '.join(allowed)}"
        
        return True, ""
    
    @staticmethod
    def validate_position_properties(properties: dict) -> tuple[bool, str]:
        """
        Validate position properties
        Returns: (is_valid, error_message)
        """
        allowed = ValidationService.ALLOWED_POSITION_PROPS
        
        for prop in properties.keys():
            if prop not in allowed:
                return False, f"Property '{prop}' is not allowed for position. Allowed: {', '.join(allowed)}"
        
        return True, ""
    
    @staticmethod
    def validate_single_edit(edit: dict) -> tuple[bool, str]:
        """
        Validate a single edit instruction
        Returns: (is_valid, error_message)
        """
        action = edit.get("action")
        
        # Validate action
        is_valid, error = ValidationService.validate_edit_action(action)
        if not is_valid:
            return False, error
        
        # Validate based on action type
        if action == "update_text_animation":
            target = edit.get("target")
            preset_id = edit.get("preset_id")
            
            if target not in ["entry", "exit", "highlight"]:
                return False, f"Invalid text animation target: {target}"
            
            return ValidationService.validate_animation_preset(target, preset_id)
        
        elif action == "update_video_animation":
            preset_id = edit.get("preset_id")
            return ValidationService.validate_animation_preset("video", preset_id)
        
        elif action == "update_text_style":
            target = edit.get("target")
            properties = edit.get("properties", {})
            return ValidationService.validate_style_properties(target, properties)
        
        elif action == "update_highlight_style":
            properties = edit.get("properties", {})
            return ValidationService.validate_style_properties("highlightStyle", properties)
        
        elif action == "update_text_position":
            properties = edit.get("properties", {})
            return ValidationService.validate_position_properties(properties)
        
        elif action == "update_video_fade":
            fade_type = edit.get("fade_type")
            if fade_type not in ["fadeIn", "fadeOut"]:
                return False, f"Invalid fade type: {fade_type}"
            
            # Validate fade properties
            if "enabled" in edit and not isinstance(edit["enabled"], bool):
                return False, "enabled must be a boolean"
            
            if "duration" in edit:
                duration = edit["duration"]
                if not isinstance(duration, (int, float)) or duration <= 0:
                    return False, "duration must be a positive number"
            
            if "start" in edit:
                start = edit["start"]
                if not isinstance(start, (int, float)) or start < 0:
                    return False, "start must be a non-negative number"
            
            return True, ""
        
        elif action == "update_highlights":
            # Validate highlight structure
            highlights = edit.get("highlights", [])
            for h in highlights:
                if "captionId" not in h or "wordStartIndex" not in h or "wordEndIndex" not in h:
                    return False, "Each highlight must have captionId, wordStartIndex, and wordEndIndex"
            
            return True, ""
        
        return True, ""
