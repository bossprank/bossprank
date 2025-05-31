from pydantic import BaseModel
from typing import Optional

class IngredientBase(BaseModel):
    """Base model for an ingredient, containing common fields."""
    name: str
    purchase_quantity: Optional[float] = None
    purchase_unit: Optional[str] = None
    purchase_price: Optional[float] = None

class IngredientCreate(IngredientBase): # Reverted: Inherits from IngredientBase
    """
    Model for creating a new ingredient.
    All fields from IngredientBase are required here, but we can allow
    optionality in Base and enforce in Create if needed, or make them mandatory in Base.
    For this setup, we'll assume name is mandatory, others are optional during creation
    but might be enforced by DB constraints if not nullable there.
    Let's make purchase_quantity, unit, and price mandatory for creation as per table schema.
    """
    name: str # Overriding to ensure it's always present
    purchase_quantity: float # Override to make mandatory
    purchase_unit: str     # Override to make mandatory
    purchase_price: float  # Override to make mandatory

class IngredientUpdate(BaseModel):
    """
    Model for updating an existing ingredient.
    All fields are optional; only provided fields will be updated.
    """
    name: Optional[str] = None
    purchase_quantity: Optional[float] = None
    purchase_unit: Optional[str] = None
    purchase_price: Optional[float] = None

class IngredientRead(IngredientBase):
    """
    Model for reading an ingredient from the database.
    Includes the 'id' field.
    """
    id: int
    # Make all fields from IngredientBase non-optional for read, as they are stored in DB
    name: str
    purchase_quantity: float
    purchase_unit: str
    purchase_price: float

    class Config:
        from_attributes = True # For Pydantic v2 compatibility
        # Ensure this model can be created from ORM objects (SQLAlchemy models)

# Example of a list response model, though often not explicitly needed
# class IngredientList(BaseModel):
#     ingredients: list[IngredientRead]
