"""
File utility functions for video handling
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from src.utils.config import Config


def generate_unique_filename(original_filename: str, extension: Optional[str] = None) -> str:
    """
    Generate a unique filename using UUID.
    
    Args:
        original_filename: Original filename
        extension: Optional file extension (if not provided, extracted from original)
    
    Returns:
        Unique filename
    """
    if extension is None:
        extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{extension}"


def get_temp_file_path(filename: str) -> Path:
    """
    Get full path for a temporary file.
    
    Args:
        filename: Filename
    
    Returns:
        Full path to temporary file
    """
    Config.ensure_temp_storage()
    return Config.TEMP_STORAGE_PATH / filename


def validate_video_file(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate video file exists and meets size requirements.
    
    Args:
        file_path: Path to video file
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > Config.MAX_VIDEO_SIZE_MB:
        return False, f"File size ({file_size_mb:.2f}MB) exceeds maximum ({Config.MAX_VIDEO_SIZE_MB}MB)"
    
    # Check if it's a video file
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}
    if file_path.suffix.lower() not in video_extensions:
        return False, f"Unsupported video format: {file_path.suffix}"
    
    return True, None


def cleanup_temp_file(file_path: Path) -> bool:
    """
    Delete a temporary file.
    
    Args:
        file_path: Path to file to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False
    return False

