"""
Video download and preprocessing service
"""
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from src.utils.config import Config
from src.utils.file_utils import (
    generate_unique_filename,
    get_temp_file_path,
    validate_video_file
)


class VideoDownloader:
    """
    Service to handle video download and preprocessing.
    
    For now, supports local file paths. URL downloading can be added later.
    """
    
    def __init__(self):
        """Initialize the video downloader"""
        Config.ensure_temp_storage()
    
    def download_from_url(self, url: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Download video from URL (TikTok, YouTube Shorts, Twitter, etc.).
        
        Uses yt-dlp to download videos from various platforms.
        
        Note: Instagram is NOT supported due to authentication requirements.
        Use TikTok, YouTube Shorts, Twitter, or other platforms instead.
        
        Args:
            url: URL of the video to download
        
        Returns:
            Tuple of (file_path, error_message)
        """
        
        # Block Instagram for security reasons (requires login cookies)
        if 'instagram.com' in url.lower():
            return None, (
                "Instagram is not supported due to authentication requirements. "
                "Please use TikTok, YouTube Shorts, Twitter, or other platforms instead. "
                "These platforms work without requiring login credentials."
            )
        try:
            import yt_dlp
            
            # Generate unique filename for downloaded video
            unique_filename = generate_unique_filename("video", ".mp4")
            temp_path = get_temp_file_path(unique_filename)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'best[ext=mp4]/best',  # Prefer MP4, fallback to best quality
                'outtmpl': str(temp_path.with_suffix('')),  # Output filename (without extension)
                'quiet': False,  # Show progress
                'no_warnings': False,
                'extract_flat': False,
                # Add headers to appear more like a real browser
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }
            
            # No cookies needed - we only support platforms that work without authentication
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"📥 Downloading video from: {url}")
                ydl.download([url])
            
            # yt-dlp might download with or without extension
            # Check for file with the base name (with or without extension)
            downloaded_file = None
            base_name = temp_path.stem
            
            # First, check if the file exists without extension (yt-dlp sometimes does this)
            if temp_path.exists() and temp_path.is_file():
                downloaded_file = temp_path
            else:
                # Check for files with common video extensions
                possible_extensions = ['.mp4', '.webm', '.mkv', '.mov', '.avi', '.m4v']
                for ext in possible_extensions:
                    candidate = temp_path.with_suffix(ext)
                    if candidate.exists():
                        downloaded_file = candidate
                        break
                
                # If still not found, search for any file starting with the base name
                if downloaded_file is None:
                    for file in temp_path.parent.glob(f"{base_name}*"):
                        if file.is_file():
                            # Check if it's a reasonable size (at least 1KB)
                            if file.stat().st_size > 1024:
                                downloaded_file = file
                                break
            
            if downloaded_file is None or not downloaded_file.exists():
                # List files in temp directory for debugging
                files_in_dir = list(temp_path.parent.glob("*"))
                return None, f"Video downloaded but file not found. Files in temp_storage: {[f.name for f in files_in_dir]}"
            
            # If file has no extension, try to detect it or add .mp4
            if not downloaded_file.suffix:
                # Try to detect file type or just add .mp4 (most common)
                downloaded_file_with_ext = downloaded_file.with_suffix('.mp4')
                try:
                    downloaded_file.rename(downloaded_file_with_ext)
                    downloaded_file = downloaded_file_with_ext
                except Exception as e:
                    # If rename fails, continue with original file
                    pass
            
            # Validate downloaded file
            is_valid, error = validate_video_file(downloaded_file)
            if not is_valid:
                return None, f"Downloaded file validation failed: {error}"
            
            print(f"✓ Video downloaded successfully: {downloaded_file}")
            return downloaded_file, None
            
        except ImportError:
            return None, "yt-dlp not installed. Install with: pip install yt-dlp"
        except Exception as e:
            return None, f"Error downloading video: {str(e)}"
    
    def process_local_file(self, file_path: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Process a local video file.
        
        This copies the file to temp storage with a unique name.
        
        Args:
            file_path: Path to local video file
        
        Returns:
            Tuple of (temp_file_path, error_message)
        """
        source_path = Path(file_path)
        
        # Validate source file
        is_valid, error = validate_video_file(source_path)
        if not is_valid:
            return None, error
        
        # Generate unique filename
        unique_filename = generate_unique_filename(source_path.name)
        temp_path = get_temp_file_path(unique_filename)
        
        # Copy file to temp storage
        try:
            shutil.copy2(source_path, temp_path)
            return temp_path, None
        except Exception as e:
            return None, f"Error copying file: {str(e)}"
    
    def process(self, input_source: str, source_type: str = "file") -> Tuple[Optional[Path], Optional[str]]:
        """
        Process video input (file path or URL).
        
        Args:
            input_source: File path or URL
            source_type: "file" or "url"
        
        Returns:
            Tuple of (temp_file_path, error_message)
        """
        if source_type == "url":
            return self.download_from_url(input_source)
        elif source_type == "file":
            return self.process_local_file(input_source)
        else:
            return None, f"Unknown source type: {source_type}"

