"""
Travel/Things to Do video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from .base import BaseExtraction


class Activity(BaseModel):
    """
    Represents a single activity or place to visit in a travel itinerary.
    
    Example:
        Activity(
            name="Louvre Museum",
            location="Paris, France",
            google_maps_link="https://maps.google.com/...",
            booking_link="https://louvre.fr/tickets",
            estimated_duration_hours=3.0
        )
    """
    name: str = Field(..., description="Name of the activity or place")
    location: str = Field(..., description="Location/address of the activity")
    google_maps_link: Optional[str] = Field(
        None, 
        description="Google Maps link to the location"
    )
    booking_link: Optional[str] = Field(
        None, 
        description="Link to book tickets or make reservations"
    )
    estimated_duration_hours: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Estimated time to spend at this activity in hours"
    )


class TravelItinerary(BaseExtraction):
    """
    Travel itinerary extracted from a travel video reel.
    
    Example:
        TravelItinerary(
            category="travel",
            title="3 Days in Paris",
            description="Complete guide to exploring Paris",
            destination="Paris, France",
            activities=[
                Activity(name="Louvre Museum", location="Paris, France"),
                Activity(name="Eiffel Tower", location="Paris, France")
            ],
            day_breakdown=[
                {"day": 1, "activities": ["Louvre Museum", "Seine River Cruise"]},
                {"day": 2, "activities": ["Eiffel Tower", "Montmartre"]}
            ],
            estimated_budget="$500-800"
        )
    """
    category: Literal["travel"] = "travel"
    destination: str = Field(..., description="Main destination or location")
    activities: List[Activity] = Field(
        ..., 
        min_length=1, 
        description="List of activities and places to visit"
    )
    day_breakdown: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Day-by-day breakdown of activities (optional)"
    )
    estimated_budget: Optional[str] = Field(
        None, 
        description="Estimated budget for the trip (e.g., '$500-800', '₹50,000')"
    )

