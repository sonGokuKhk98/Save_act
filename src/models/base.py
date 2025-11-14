"""
Base data model for all extraction types
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class BaseExtraction(BaseModel):
    """
    Base model that all category-specific extraction models inherit from.
    
    This ensures all extractions have common fields like category, title,
    description, and metadata.
    """
    category: Literal[
        "workout", 
        "recipe", 
        "travel", 
        "product", 
        "educational", 
        "music"
    ]
    title: Optional[str] = Field(None, description="Title of the extracted content")
    description: Optional[str] = Field(None, description="Brief description of the content")
    source_url: Optional[str] = Field(
        None, 
        description="Original URL of the reel/video"
    )
    extracted_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when extraction was performed"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0.0 to 1.0)"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Flexible JSON field for additional metadata, context, or information that doesn't fit structured fields"
    )

    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "category": "workout",
                "title": "HIIT Workout Routine",
                "description": "A 20-minute high-intensity interval training routine",
                "source_url": "https://instagram.com/reel/...",
                "extracted_at": "2024-01-01T12:00:00Z",
                "confidence_score": 0.95,
                "additional_context": {
                    "video_quality": "HD",
                    "trainer_name": "John Doe",
                    "location": "Outdoor park",
                    "hashtags": ["#fitness", "#hiit", "#workout"],
                    "any_other_info": "Flexible storage for any extra data"
                }
            }
        }

