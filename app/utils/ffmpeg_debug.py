"""
FFmpeg debugging utilities
"""
import subprocess
import sys


def check_ffmpeg_installation():
    """Check if FFmpeg is installed and get version"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Extract version from first line
            first_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg is installed: {first_line}")
            return True
        else:
            print("✗ FFmpeg command failed")
            return False
            
    except FileNotFoundError:
        print("✗ FFmpeg not found in PATH")
        print("\nPlease install FFmpeg:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        return False
    except Exception as e:
        print(f"✗ Error checking FFmpeg: {e}")
        return False


def check_font_availability():
    """Check if required fonts are available"""
    import os
    import platform
    
    system = platform.system()
    print(f"\nChecking fonts on {system}...")
    
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "C:/WINDOWS/Fonts/arial.ttf",
        ]
    elif system == "Darwin":
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    
    found = False
    for path in font_paths:
        if os.path.exists(path):
            print(f"✓ Font found: {path}")
            found = True
            break
    
    if not found:
        print("✗ No suitable fonts found")
        print(f"Searched paths: {font_paths}")
    
    return found


def test_simple_render(input_file: str, output_file: str):
    """Test a simple FFmpeg render without filters"""
    try:
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-t", "5",  # Only 5 seconds
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "fast",
            "-y",
            output_file
        ]
        
        print(f"\nTesting simple render...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Simple render successful")
            return True
        else:
            print("✗ Simple render failed")
            print(f"Error: {result.stderr[-500:]}")  # Last 500 chars
            return False
            
    except Exception as e:
        print(f"✗ Error during test render: {e}")
        return False


def run_diagnostics():
    """Run all FFmpeg diagnostics"""
    print("=" * 60)
    print("FFmpeg Diagnostics")
    print("=" * 60)
    
    ffmpeg_ok = check_ffmpeg_installation()
    font_ok = check_font_availability()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if ffmpeg_ok and font_ok:
        print("✓ All checks passed - FFmpeg should work correctly")
        return True
    else:
        print("✗ Some checks failed - please fix the issues above")
        return False


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
