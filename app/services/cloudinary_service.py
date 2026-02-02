"""
Cloudinary service for video upload
"""
import os
import io
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from typing import Callable, Optional

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


class ProgressTrackingStream:
    """Wrapper to track upload progress from a stream"""
    
    def __init__(self, stream, total_size: Optional[int] = None, progress_callback: Optional[Callable[[float], None]] = None):
        self.stream = stream
        self.total_size = total_size
        self.progress_callback = progress_callback
        self.bytes_uploaded = 0
    
    def read(self, size=-1):
        """Read from stream and track progress"""
        data = self.stream.read(size)
        if data:
            self.bytes_uploaded += len(data)
            
            # Report progress if we know total size
            if self.progress_callback and self.total_size and self.total_size > 0:
                progress = (self.bytes_uploaded / self.total_size) * 100
                self.progress_callback(min(progress, 100))
        
        return data
    
    def __getattr__(self, name):
        """Delegate other attributes to the underlying stream"""
        return getattr(self.stream, name)


class CloudinaryService:
    """Service for uploading videos to Cloudinary"""
    
    @staticmethod
    def upload_video_stream(
        video_stream, 
        filename: str, 
        folder: str = "rendered_videos",
        progress_callback: Optional[Callable[[float], None]] = None,
        estimated_size: Optional[int] = None
    ) -> str:
        """
        Upload video from stream to Cloudinary with progress tracking
        
        Args:
            video_stream: File-like object or bytes
            filename: Name for the uploaded file
            folder: Cloudinary folder path
            progress_callback: Callback for upload progress (0-100)
            estimated_size: Estimated size in bytes for progress calculation
            
        Returns:
            str: Public URL of uploaded video
        """
        try:
            # Wrap stream with progress tracking if callback provided
            if progress_callback:
                video_stream = ProgressTrackingStream(
                    video_stream, 
                    estimated_size, 
                    progress_callback
                )
            
            result = cloudinary.uploader.upload(
                video_stream,
                resource_type="video",
                folder=folder,
                public_id=filename,
                overwrite=True,
                format="mp4",
                chunk_size=6000000  # 6MB chunks for better progress tracking
            )
            
            return result.get("secure_url")
            
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
    
    @staticmethod
    def upload_video_file(file_path: str, filename: str, folder: str = "rendered_videos") -> str:
        """
        Upload video file to Cloudinary
        
        Args:
            file_path: Path to video file
            filename: Name for the uploaded file
            folder: Cloudinary folder path
            
        Returns:
            str: Public URL of uploaded video
        """
        try:
            result = cloudinary.uploader.upload(
                file_path,
                resource_type="video",
                folder=folder,
                public_id=filename,
                overwrite=True
            )
            
            return result.get("secure_url")
            
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
