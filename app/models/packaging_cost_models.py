from pydantic import BaseModel
from typing import Optional

class PackagingCostBase(BaseModel):
    """Base model for packaging costs."""
    item_name: str
    cost_per_unit: float
    recipe_id: Optional[int] = None # Foreign key to recipes.id
    units_per_recipe_batch: Optional[float] = None

class PackagingCostCreate(PackagingCostBase):
    """Model for creating a new packaging cost item."""
    # All fields from Base are used. Add constraints if any.
    # e.g., if units_per_recipe_batch is required when recipe_id is present.
    # For now, basic inheritance is fine.
    pass

class PackagingCostUpdate(BaseModel):
    """
    Model for updating an existing packaging cost item.
    All fields are optional; only provided fields will be updated.
    """
    item_name: Optional[str] = None
    cost_per_unit: Optional[float] = None
    recipe_id: Optional[int] = None # Allow changing or unsetting the recipe association
    units_per_recipe_batch: Optional[float] = None # Allow changing or unsetting

class PackagingCostRead(PackagingCostBase):
    """Model for reading a packaging cost item from the database."""
    id: int
    recipe_name: Optional[str] = None # To be populated from the recipes table if recipe_id exists

    class Config:
        from_attributes = True
