from pydantic import BaseModel
from typing import List, Optional

# Pydantic Models for Recipe Ingredients (association part)

class RecipeIngredientBase(BaseModel):
    """Base model for ingredients used in a recipe."""
    ingredient_id: int
    quantity_used_in_recipe: float
    unit_used_in_recipe: str

class RecipeIngredientCreate(RecipeIngredientBase):
    """Model for creating a recipe-ingredient link. Data comes from the client."""
    pass

class RecipeIngredientRead(RecipeIngredientBase):
    """Model for reading a recipe-ingredient link, including its own ID and ingredient details."""
    id: int  # This is the id from the recipe_ingredients association table
    ingredient_name: Optional[str] = None # To be populated from the ingredients table

    class Config:
        from_attributes = True

# Pydantic Models for Recipes

class RecipeBase(BaseModel):
    """Base model for a recipe, containing common fields."""
    name: str
    description: Optional[str] = None
    servings_per_batch: float = 1.0 # Default to 1 serving
    preparation_instructions: Optional[str] = None
    mixing_instructions: Optional[str] = None
    proofing_instructions: Optional[str] = None
    baking_instructions: Optional[str] = None
    resting_instructions: Optional[str] = None
    packaging_instructions: Optional[str] = None

class RecipeCreate(RecipeBase):
    """Model for creating a new recipe, including its list of ingredients."""
    ingredients: List[RecipeIngredientCreate] = []

class RecipeUpdate(BaseModel): # Not inheriting from RecipeBase to make all fields truly optional
    """
    Model for updating an existing recipe.
    All fields are optional; only provided fields will be updated.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    servings_per_batch: Optional[float] = None
    preparation_instructions: Optional[str] = None
    mixing_instructions: Optional[str] = None
    proofing_instructions: Optional[str] = None
    baking_instructions: Optional[str] = None
    resting_instructions: Optional[str] = None
    packaging_instructions: Optional[str] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None # Optional list of ingredients for update

class RecipeRead(RecipeBase):
    """Model for reading a recipe from the database, including its ID and full ingredient details."""
    id: int
    ingredients: List[RecipeIngredientRead] = []

    class Config:
        from_attributes = True
