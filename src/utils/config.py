"""
Configuration management using environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class to manage all environment variables"""
    
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Supermemeory.ai API (support both spellings for compatibility)
    SUPERMEMEORY_API_KEY: str = os.getenv("SUPERMEMORY_API_KEY") or os.getenv("SUPERMEMEORY_API_KEY", "")
    SUPERMEMEORY_BASE_URL: str = os.getenv(
        "SUPERMEMORY_BASE_URL"
    ) or os.getenv(
        "SUPERMEMEORY_BASE_URL", 
        "https://api.supermemory.ai/"
    )
    
    # Processing Configuration
    MAX_VIDEO_SIZE_MB: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
    KEYFRAME_INTERVAL_SECONDS: int = int(os.getenv("KEYFRAME_INTERVAL_SECONDS", "3"))
    MAX_VIDEO_DURATION_MINUTES: int = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "5"))
    
    # Storage Configuration
    TEMP_STORAGE_PATH: Path = Path(os.getenv("TEMP_STORAGE_PATH", "./temp_storage"))
    CLEANUP_AFTER_HOURS: int = int(os.getenv("CLEANUP_AFTER_HOURS", "24"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required in .env file")
        if not cls.SUPERMEMEORY_API_KEY:
            raise ValueError("SUPERMEMEORY_API_KEY is required in .env file")
        return True
    
    @classmethod
    def ensure_temp_storage(cls):
        """Ensure temporary storage directory exists"""
        cls.TEMP_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

