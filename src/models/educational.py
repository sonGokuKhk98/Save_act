"""
Educational/How-to video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from .base import BaseExtraction


class TutorialStep(BaseModel):
    """
    Represents a single step in a tutorial or how-to guide.
    
    Example:
        TutorialStep(
            step_number=1,
            description="Open Canva and create a new design",
            tools_required=["Canva", "Computer"],
            resource_links=["https://canva.com"]
        )
    """
    step_number: int = Field(..., ge=1, description="Step number in the tutorial")
    description: str = Field(..., description="Description of what to do in this step")
    tools_required: List[str] = Field(
        default_factory=list, 
        description="Tools, software, or resources needed for this step"
    )
    resource_links: List[str] = Field(
        default_factory=list, 
        description="Links to helpful resources, tools, or websites"
    )


class TutorialSummary(BaseExtraction):
    """
    Tutorial or how-to guide extracted from an educational video reel.
    
    Example:
        TutorialSummary(
            category="educational",
            title="How to Create Animated Graphics in Canva",
            description="Step-by-step guide to creating animations",
            topic="Graphic Design",
            steps=[
                TutorialStep(
                    step_number=1,
                    description="Open Canva and create a new design",
                    tools_required=["Canva"]
                ),
                TutorialStep(
                    step_number=2,
                    description="Import your asset",
                    tools_required=["Canva"]
                )
            ],
            prerequisites=["Basic Canva knowledge"],
            estimated_time_minutes=15
        )
    """
    category: Literal["educational"] = "educational"
    topic: Optional[str] = Field(None, description="Topic or subject of the tutorial (if extractable)")
    steps: Optional[List[TutorialStep]] = Field(
        default=None, 
        description="Step-by-step instructions (if extractable)"
    )
    prerequisites: List[str] = Field(
        default_factory=list, 
        description="Prerequisites or required knowledge before starting"
    )
    estimated_time_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        description="Estimated time to complete the tutorial in minutes"
    )

