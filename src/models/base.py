"""
Base data model for all extraction types
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, Union
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
    keyframes: Optional[list] = Field(None, description="List of keyframe image paths")
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


class GenericExtraction(BaseModel):
    """
    Generic fallback model for when structured extraction fails.
    
    This model accepts any JSON structure and stores everything flexibly.
    Used as a safety net to ensure no data is lost when validation fails.
    """
    category: str = Field(..., description="Content category (workout, recipe, travel, etc.)")
    title: Optional[str] = Field(None, description="Title if available")
    description: Optional[str] = Field(None, description="Description if available")
    source_url: Optional[str] = Field(None, description="Original URL of the reel/video")
    extracted_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when extraction was performed"
    )
    keyframes: Optional[list] = Field(None, description="List of keyframe image paths")
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction (0.0 to 1.0)"
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="All extracted data stored as flexible JSON"
    )
    
    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow any additional fields
    
    def get_formatted_summary(self) -> str:
        """
        Get a nicely formatted summary of the extracted data.
        
        Returns:
            Formatted string representation
        """
        lines = []
        lines.append(f"Category: {self.category}")
        
        if self.title:
            lines.append(f"Title: {self.title}")
        
        if self.description:
            lines.append(f"Description: {self.description}")
        
        lines.append(f"Confidence: {self.confidence_score:.2f}")
        
        # Format main content items
        if "items" in self.raw_data:
            items = self.raw_data["items"]
            if isinstance(items, list):
                lines.append(f"\nItems ({len(items)}):")
                for i, item in enumerate(items[:10], 1):  # Show first 10
                    if isinstance(item, dict):
                        name = item.get("name", item.get("item", "Unknown"))
                        lines.append(f"  {i}. {name}")
                    else:
                        lines.append(f"  {i}. {item}")
                if len(items) > 10:
                    lines.append(f"  ... and {len(items) - 10} more")
        
        # Show other interesting fields
        interesting_fields = ["cuisine_type", "difficulty_level", "destination", "estimated_duration_minutes"]
        for field in interesting_fields:
            if field in self.raw_data and self.raw_data[field]:
                field_name = field.replace("_", " ").title()
                lines.append(f"{field_name}: {self.raw_data[field]}")
        
        # Show additional_context if it exists
        if "additional_context" in self.raw_data and self.raw_data["additional_context"]:
            lines.append(f"\nAdditional Context:")
            ctx = self.raw_data["additional_context"]
            if isinstance(ctx, dict):
                for key, value in list(ctx.items())[:5]:  # Show first 5 items
                    key_display = key.replace("_", " ").title()
                    if isinstance(value, list):
                        lines.append(f"  {key_display}: {len(value)} items")
                    elif isinstance(value, str) and len(value) > 50:
                        lines.append(f"  {key_display}: {value[:50]}...")
                    else:
                        lines.append(f"  {key_display}: {value}")
                if len(ctx) > 5:
                    lines.append(f"  ... and {len(ctx) - 5} more fields")
        
        # Add fallback note
        if "_original_category" in self.raw_data:
            lines.append(f"\n⚠️  Note: Intended for {self.raw_data['_original_category']} but used generic format")
        
        # Show total fields preserved
        lines.append(f"\n📊 Total fields preserved: {len(self.raw_data)}")
        
        return "\n".join(lines)

