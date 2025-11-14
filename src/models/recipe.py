"""
Recipe/Cooking video extraction models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from .base import BaseExtraction


class Ingredient(BaseModel):
    """
    Represents a single ingredient in a recipe.
    
    Example:
        Ingredient(
            name="Flour",
            quantity="2 cups",
            notes="All-purpose flour"
        )
    """
    name: str = Field(..., description="Name of the ingredient")
    quantity: str = Field(
        ..., 
        description="Quantity with unit (e.g., '2 cups', '1 tbsp', '200g')"
    )
    notes: Optional[str] = Field(
        None, 
        description="Additional notes about the ingredient"
    )


class RecipeStep(BaseModel):
    """
    Represents a single step in a recipe.
    
    Example:
        RecipeStep(
            step_number=1,
            instruction="Mix flour and water in a bowl",
            duration_minutes=2.0,
            utensils=["bowl", "whisk"]
        )
    """
    step_number: int = Field(..., ge=1, description="Step number in the recipe")
    instruction: str = Field(..., description="Instruction for this step")
    duration_minutes: Optional[float] = Field(
        None, 
        ge=0.0, 
        description="Time required for this step in minutes"
    )
    utensils: List[str] = Field(
        default_factory=list, 
        description="Utensils/tools needed for this step"
    )


class RecipeCard(BaseExtraction):
    """
    Complete recipe extracted from a cooking video reel.
    
    Example:
        RecipeCard(
            category="recipe",
            title="Chocolate Chip Cookies",
            description="Classic homemade chocolate chip cookies",
            ingredients=[
                Ingredient(name="Flour", quantity="2 cups"),
                Ingredient(name="Butter", quantity="1 cup")
            ],
            steps=[
                RecipeStep(step_number=1, instruction="Mix dry ingredients"),
                RecipeStep(step_number=2, instruction="Add wet ingredients")
            ],
            prep_time_minutes=15,
            cook_time_minutes=12,
            servings=24
        )
    """
    category: Literal["recipe"] = "recipe"
    ingredients: Optional[List[Ingredient]] = Field(
        default=None, 
        description="List of ingredients needed (if extractable)"
    )
    steps: Optional[List[RecipeStep]] = Field(
        default=None, 
        description="Step-by-step cooking instructions (if extractable)"
    )
    prep_time_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        description="Preparation time in minutes"
    )
    cook_time_minutes: Optional[int] = Field(
        None, 
        ge=0, 
        description="Cooking time in minutes"
    )
    servings: Optional[int] = Field(
        None, 
        ge=1, 
        description="Number of servings"
    )
    cuisine_type: Optional[str] = Field(
        None, 
        description="Type of cuisine (e.g., 'Italian', 'Asian', 'Mexican')"
    )

