"""
Data models for all extraction categories
"""

from .base import BaseExtraction, GenericExtraction
from .workout import WorkoutRoutine, Exercise
from .recipe import RecipeCard, Ingredient, RecipeStep
from .travel import TravelItinerary, Activity
from .product import ProductCatalog, Product
from .educational import TutorialSummary, TutorialStep
from .music import SongMetadata

__all__ = [
    "BaseExtraction",
    "GenericExtraction",
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

