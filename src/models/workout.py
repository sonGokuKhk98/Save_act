"""
Workout video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from .base import BaseExtraction


class Exercise(BaseModel):
    """
    Represents a single exercise in a workout routine.
    
    Example:
        Exercise(
            name="Squats",
            sets=3,
            reps=15,
            duration_seconds=30,
            rest_seconds=15
        )
    """
    name: str = Field(..., description="Name of the exercise")
    sets: Optional[int] = Field(
        None, 
        ge=1, 
        description="Number of sets for this exercise"
    )
    reps: Optional[int] = Field(
        None, 
        ge=1, 
        description="Number of repetitions per set"
    )
    duration_seconds: Optional[int] = Field(
        None, 
        ge=1, 
        description="Duration of the exercise in seconds (for time-based exercises)"
    )
    rest_seconds: Optional[int] = Field(
        None, 
        ge=0, 
        description="Rest period after this exercise in seconds"
    )


class WorkoutRoutine(BaseExtraction):
    """
    Complete workout routine extracted from a video reel.
    
    Example:
        WorkoutRoutine(
            category="workout",
            title="HIIT Cardio Blast",
            description="20-minute high-intensity workout",
            exercises=[
                Exercise(name="Squats", sets=3, reps=15, rest_seconds=15),
                Exercise(name="Burpees", duration_seconds=30, rest_seconds=15)
            ],
            total_rounds=3,
            estimated_duration_minutes=20.0,
            difficulty_level="intermediate"
        )
    """
    category: Literal["workout"] = "workout"
    exercises: List[Exercise] = Field(
        ..., 
        min_length=1, 
        description="List of exercises in the workout"
    )
    total_rounds: Optional[int] = Field(
        None, 
        ge=1, 
        description="Total number of rounds/circuits"
    )
    estimated_duration_minutes: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Estimated total duration of the workout in minutes"
    )
    difficulty_level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="intermediate", 
        description="Difficulty level of the workout"
    )
    music_tempo_bpm: Optional[int] = Field(
        None, 
        ge=60, 
        le=200, 
        description="Music tempo in beats per minute (if detected)"
    )

