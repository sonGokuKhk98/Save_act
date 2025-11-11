"""
Data models for all extraction categories
"""

from .base import BaseExtraction
from .workout import WorkoutRoutine, Exercise
from .recipe import RecipeCard, Ingredient, RecipeStep
from .travel import TravelItinerary, Activity
from .product import ProductCatalog, Product
from .educational import TutorialSummary, TutorialStep
from .music import SongMetadata

__all__ = [
    "BaseExtraction",
    "WorkoutRoutine",
    "Exercise",
    "RecipeCard",
    "Ingredient",
    "RecipeStep",
    "TravelItinerary",
    "Activity",
    "ProductCatalog",
    "Product",
    "TutorialSummary",
    "TutorialStep",
    "SongMetadata",
]

