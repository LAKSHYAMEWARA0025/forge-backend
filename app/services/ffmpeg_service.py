"""
FFmpeg service for video rendering with captions and effects
"""
import subprocess
import os
import tempfile
import json
from typing import Dict, Any, Callable, Optional
import re


class FFmpegService:
    """Service for rendering videos with FFmpeg"""
    
    @staticmethod
    def generate_ass_subtitles(config: Dict[str, Any]) -> str:
        """
        Generate ASS subtitle content from config
        
        Args:
            config: Edit configuration with captions
            
        Returns:
            str: ASS subtitle file content
        """
        captions = config.get("tracks", {}).get("text", {}).get("captions", [])
        global_style = config.get("tracks", {}).get("text", {}).get("globalStyle", {})
        
        if not captions:
            return ""
        
        # Extract styles
        font_family = global_style.get("fontFamily", "Arial")
        font_size = global_style.get("fontSize", 48)
        font_color = global_style.get("color", "#ffffff")
        
        # Convert hex color to ASS format (&HAABBGGRR)
        if font_color.startswith("#"):
            hex_color = font_color[1:]
            if len(hex_color) == 6:
                r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
                ass_color = f"&H00{b}{g}{r}"
            else:
                ass_color = "&H00FFFFFF"
        else:
            ass_color = "&H00FFFFFF"
        
        # Build ASS header
        ass_content = f"""[Script Info]
Title: Video Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_family},{font_size},{ass_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Add caption events
        for cap in captions:
            text = cap["text"].replace("\n", "\\N")
            start_time = FFmpegService._format_ass_time(cap["start"])
            end_time = FFmpegService._format_ass_time(cap["end"])
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
        
        return ass_content
    
    @staticmethod
    def _format_ass_time(seconds: float) -> str:
        """Format time in ASS format (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    @staticmethod
    def get_font_path() -> str:
        """Get the correct font path for the current OS"""
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Try common Windows font paths
            # Use backslashes for Windows (FFmpeg on Windows expects this)
            font_paths = [
                "C:\\\\Windows\\\\Fonts\\\\arial.ttf",  # Double backslash for FFmpeg escaping
                "C:\\\\Windows\\\\Fonts\\\\Arial.ttf",
            ]
            # Check if font exists (using single backslash for Python)
            for path in ["C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\Arial.ttf"]:
                if os.path.exists(path):
                    # Return with double backslash for FFmpeg
                    return path.replace("\\", "\\\\")
            return "C:\\\\Windows\\\\Fonts\\\\arial.ttf"  # Default with double backslash
        elif system == "Darwin":  # macOS
            return "/System/Library/Fonts/Supplemental/Arial.ttf"
        else:  # Linux
            return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    @staticmethod
    def build_caption_filter(config: Dict[str, Any]) -> str:
        """
        Build FFmpeg drawtext filter for captions with animations
        
        Args:
            config: Edit configuration with captions and styles
            
        Returns:
            str: FFmpeg filter string for captions
        """
        captions = config.get("tracks", {}).get("text", {}).get("captions", [])
        global_style = config.get("tracks", {}).get("text", {}).get("globalStyle", {})
        highlights = config.get("tracks", {}).get("text", {}).get("highlights", [])
        animation = config.get("tracks", {}).get("text", {}).get("animation", {})
        
        if not captions:
            return ""
        
        # Extract styles
        font_family = global_style.get("fontFamily", "Arial")
        font_size = global_style.get("fontSize", 48)
        font_color = global_style.get("color", "#ffffff").replace("#", "")
        bg_color = global_style.get("background", "rgba(0,0,0,0.45)")
        
        # Get correct font path
        font_path = FFmpegService.get_font_path()
        
        # Convert rgba to FFmpeg format
        if "rgba" in bg_color:
            # Extract rgba values
            rgba_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', bg_color)
            if rgba_match:
                r, g, b, a = rgba_match.groups()
                # FFmpeg uses hex with alpha: 0xAARRGGBB
                alpha_hex = format(int(float(a) * 255), '02x')
                bg_hex = f"0x{alpha_hex}{int(r):02x}{int(g):02x}{int(b):02x}"
            else:
                bg_hex = "0x80000000"  # Default semi-transparent black
        else:
            bg_hex = "0x80000000"
        
        # Position
        position = global_style.get("position", {})
        anchor = position.get("anchor", "bottom_center")
        offset_y = position.get("offsetY", -50)
        
        # Calculate position
        if "bottom" in anchor:
            y_pos = f"h-text_h{offset_y:+d}"
        elif "top" in anchor:
            y_pos = f"0{offset_y:+d}"
        else:  # center
            y_pos = f"(h-text_h)/2{offset_y:+d}"
        
        x_pos = "(w-text_w)/2"  # Always center horizontally
        
        # Build filter for each caption
        filters = []
        for cap in captions:
            text = cap["text"].replace("'", "\\'").replace(":", "\\:")
            start = cap["start"]
            end = cap["end"]
            
            # Entry animation
            entry_anim = animation.get("entry", {})
            entry_preset = entry_anim.get("presetId", "fade_in")
            entry_duration = entry_anim.get("duration", 0.2)
            
            # Exit animation
            exit_anim = animation.get("exit", {})
            exit_preset = exit_anim.get("presetId", "fade_out")
            exit_duration = exit_anim.get("duration", 0.2)
            
            # Alpha animation for fade
            alpha_expr = "1"
            if entry_preset in ["fade_in", "slide_up_fade", "slide_down_fade"]:
                # Fade in at start
                alpha_expr = f"if(lt(t,{start}),0,if(lt(t,{start+entry_duration}),(t-{start})/{entry_duration},1))"
            
            if exit_preset in ["fade_out", "slide_up_fade_out", "slide_down_fade_out"]:
                # Fade out at end
                fade_start = end - exit_duration
                alpha_expr = f"if(lt(t,{start}),0,if(lt(t,{start+entry_duration}),(t-{start})/{entry_duration},if(lt(t,{fade_start}),1,if(lt(t,{end}),1-(t-{fade_start})/{exit_duration},0))))"
            
            # Y position animation for slide
            y_expr = y_pos
            if "slide_up" in entry_preset:
                y_expr = f"if(lt(t,{start+entry_duration}),{y_pos}+50*(1-(t-{start})/{entry_duration}),{y_pos})"
            elif "slide_down" in entry_preset:
                y_expr = f"if(lt(t,{start+entry_duration}),{y_pos}-50*(1-(t-{start})/{entry_duration}),{y_pos})"
            
            # Enable/disable based on time
            enable_expr = f"between(t,{start},{end})"
            
            filter_str = (
                f"drawtext=text='{text}':"
                f"fontfile={font_path}:"
                f"fontsize={font_size}:"
                f"fontcolor={font_color}@{alpha_expr}:"
                f"box=1:boxcolor={bg_hex}:"
                f"boxborderw=10:"
                f"x={x_pos}:y={y_expr}:"
                f"enable='{enable_expr}'"
            )
            
            filters.append(filter_str)
        
        # Combine all caption filters
        return ",".join(filters) if filters else ""
    
    @staticmethod
    def build_video_filter(config: Dict[str, Any]) -> str:
        """
        Build FFmpeg filter for video effects (fade in/out, etc.)
        
        Args:
            config: Edit configuration with video effects
            
        Returns:
            str: FFmpeg filter string for video effects
        """
        video_anim = config.get("tracks", {}).get("video", {}).get("animation", {})
        duration = config.get("meta", {}).get("duration", 0)
        
        filters = []
        
        # Fade in
        fade_in = video_anim.get("fadeIn", {})
        if fade_in:
            fade_start = fade_in.get("start", 0)
            fade_duration = fade_in.get("duration", 0.8)
            filters.append(f"fade=t=in:st={fade_start}:d={fade_duration}")
        
        # Fade out
        fade_out = video_anim.get("fadeOut", {})
        if fade_out:
            fade_start = fade_out.get("start", max(0, duration - 2.0))
            fade_duration = fade_out.get("duration", 2.0)
            filters.append(f"fade=t=out:st={fade_start}:d={fade_duration}")
        
        return ",".join(filters) if filters else ""
    
    @staticmethod
    def build_ffmpeg_command(
        input_url: str,
        output_path: str,
        config: Dict[str, Any],
        resolution: str = "original",
        quality: str = "high",
        subtitle_file_path: Optional[str] = None
    ) -> list:
        """
        Build complete FFmpeg command
        
        Args:
            input_url: Source video URL
            output_path: Output file path (or pipe:1 for stdout)
            config: Edit configuration
            resolution: Output resolution
            quality: Output quality
            subtitle_file_path: Path to ASS subtitle file (if captions exist)
            
        Returns:
            list: FFmpeg command as list of arguments
        """
        cmd = ["ffmpeg", "-i", input_url]
        
        # Build video filters (fade in/out only - short filters)
        video_filter = FFmpegService.build_video_filter(config)
        
        # Combine video filter and subtitles
        filters = []
        if video_filter:
            filters.append(video_filter)
        
        # Add subtitles from ASS file if provided
        if subtitle_file_path:
            # Escape backslashes for Windows paths in FFmpeg
            escaped_path = subtitle_file_path.replace('\\', '\\\\').replace(':', '\\:')
            filters.append(f"subtitles='{escaped_path}'")
        
        # Apply combined filters
        if filters:
            cmd.extend(["-vf", ",".join(filters)])
        
        # Resolution - maintain aspect ratio
        if resolution != "original":
            # Get source dimensions from config
            source_width = config.get("source", {}).get("video", {}).get("width", 1920)
            source_height = config.get("source", {}).get("video", {}).get("height", 1080)
            source_aspect = source_width / source_height if source_height > 0 else 16/9
            
            # Determine target height based on resolution
            target_heights = {
                "1080p": 1080,
                "720p": 720,
                "480p": 480
            }
            target_height = target_heights.get(resolution, 1080)
            
            # Calculate width maintaining aspect ratio
            target_width = int(target_height * source_aspect)
            
            # Ensure even dimensions (required for H.264)
            if target_width % 2 != 0:
                target_width += 1
            if target_height % 2 != 0:
                target_height += 1
            
            cmd.extend(["-s", f"{target_width}x{target_height}"])
        
        # Quality settings
        if quality == "high":
            cmd.extend(["-crf", "18", "-preset", "slow"])
        elif quality == "medium":
            cmd.extend(["-crf", "23", "-preset", "medium"])
        else:  # low
            cmd.extend(["-crf", "28", "-preset", "fast"])
        
        # Codec and format
        cmd.extend([
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-y",  # Overwrite output
            output_path
        ])
        
        return cmd
    
    @staticmethod
    def render_video(
        input_url: str,
        output_path: str,
        config: Dict[str, Any],
        resolution: str = "original",
        quality: str = "high",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Render video with FFmpeg using ASS subtitles
        
        Args:
            input_url: Source video URL
            output_path: Output file path
            config: Edit configuration
            resolution: Output resolution
            quality: Output quality
            progress_callback: Callback function for progress updates (0-100)
            
        Returns:
            bool: True if successful
        """
        subtitle_file = None
        
        try:
            # Generate ASS subtitle file if captions exist
            ass_content = FFmpegService.generate_ass_subtitles(config)
            if ass_content:
                temp_sub = tempfile.NamedTemporaryFile(mode='w', suffix='.ass', delete=False, encoding='utf-8')
                subtitle_file = temp_sub.name
                temp_sub.write(ass_content)
                temp_sub.close()
            
            cmd = FFmpegService.build_ffmpeg_command(
                input_url, output_path, config, resolution, quality, subtitle_file
            )
            
            # Removed print statement for cleaner logs
            
            duration = config.get("meta", {}).get("duration", 0)
            
            # Collect stderr output for error reporting
            stderr_lines = []
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Parse progress from stderr
            for line in process.stderr:
                stderr_lines.append(line)
                if progress_callback and "time=" in line:
                    # Extract time from FFmpeg output
                    time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                    if time_match and duration > 0:
                        h, m, s = time_match.groups()
                        current_time = int(h) * 3600 + int(m) * 60 + float(s)
                        progress = min(100, (current_time / duration) * 100)
                        progress_callback(progress)
            
            process.wait()
            
            if process.returncode == 0:
                if progress_callback:
                    progress_callback(100)
                return True
            else:
                # Get last 20 lines of stderr for error context
                error_output = "\n".join(stderr_lines[-20:]) if stderr_lines else "Unknown error"
                raise Exception(f"FFmpeg failed with code {process.returncode}:\n{error_output}")
                
        except Exception as e:
            print(f"FFmpeg render error: {str(e)}")
            raise
        finally:
            # Clean up subtitle file
            if subtitle_file and os.path.exists(subtitle_file):
                try:
                    os.remove(subtitle_file)
                except:
                    pass
    
    @staticmethod
    def render_video_to_pipe(
        input_url: str,
        config: Dict[str, Any],
        resolution: str = "original",
        quality: str = "high",
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> tuple:
        """
        Render video to stdout pipe for streaming upload
        
        Args:
            input_url: Source video URL
            config: Edit configuration
            resolution: Output resolution
            quality: Output quality
            progress_callback: Callback for render progress (0-100)
            
        Returns:
            tuple: (process, filter_file_path) - Process with stdout pipe and temp filter file path
        """
        # Create temporary filter file for long filter strings
        temp_filter = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        filter_file = temp_filter.name
        temp_filter.close()
        
        cmd = FFmpegService.build_ffmpeg_command(
            input_url, "pipe:1", config, resolution, quality, filter_file
        )
        
        # Fix command for pipe output - remove last element and add proper pipe format
        cmd = cmd[:-1]  # Remove the "pipe:1" that was added as output
        cmd.extend(["-f", "mp4", "-movflags", "frag_keyframe+empty_moov", "pipe:1"])
        
        # Removed print statement for cleaner logs
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**8  # Large buffer for streaming
        )
        
        # Start thread to monitor progress if callback provided
        if progress_callback:
            import threading
            duration = config.get("meta", {}).get("duration", 0)
            
            def monitor_progress():
                for line in iter(process.stderr.readline, b''):
                    try:
                        line_str = line.decode('utf-8', errors='ignore')
                        if "time=" in line_str and duration > 0:
                            time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line_str)
                            if time_match:
                                h, m, s = time_match.groups()
                                current_time = int(h) * 3600 + int(m) * 60 + float(s)
                                progress = min(100, (current_time / duration) * 100)
                                progress_callback(progress)
                    except:
                        pass
            
            thread = threading.Thread(target=monitor_progress, daemon=True)
            thread.start()
        
        return process, filter_file

