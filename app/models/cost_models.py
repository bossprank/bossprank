from pydantic import BaseModel
from typing import List, Optional

class CalculatedIngredientCost(BaseModel):
    """Represents the calculated cost of a single ingredient within a recipe."""
    ingredient_id: int
    ingredient_name: str
    quantity_used_in_recipe: float
    unit_used_in_recipe: str
    cost_for_recipe: float

    # Reference data from the base ingredient for clarity in results
    purchase_unit: Optional[str] = None
    purchase_quantity: Optional[float] = None
    purchase_price: Optional[float] = None
    cost_per_purchase_unit: Optional[float] = None # Calculated: purchase_price / purchase_quantity

    warning: Optional[str] = None # To flag potential issues like unit mismatch

class CalculatedPackagingCost(BaseModel):
    """Represents the calculated cost of a single packaging item for a recipe."""
    packaging_cost_id: int
    item_name: str
    units_per_recipe_batch: float # Should not be None if used in calculation
    cost_per_unit: float
    cost_for_recipe: float

class RecipeCostDetails(BaseModel):
    """Overall cost details for a recipe."""
    recipe_id: int
    recipe_name: str
    servings_per_batch: float

    total_ingredient_cost: float
    total_packaging_cost: float
    total_production_cost: float # Sum of ingredient and packaging costs
    cost_per_serving: float

    ingredient_cost_breakdown: List[CalculatedIngredientCost]
    packaging_cost_breakdown: List[CalculatedPackagingCost]

    class Config:
        from_attributes = True # Useful if ever constructing from an ORM-like object directly
