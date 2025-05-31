from sqlalchemy import Table, Column, Integer, String, Float, Text, ForeignKey
from .core import metadata  # Import metadata from core.py

ingredients = Table(
    "ingredients",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True, index=True),
    Column("purchase_quantity", Float, nullable=False),
    Column("purchase_unit", String, nullable=False),  # e.g., 'g', 'ml', 'pcs'
    Column("purchase_price", Float, nullable=False)  # Price for the purchase_quantity
)
"""
Table to store information about ingredients.

Attributes:
    id: Primary key for the ingredient.
    name: Name of the ingredient (must be unique).
    purchase_quantity: The quantity in which the ingredient is typically purchased.
    purchase_unit: The unit for the purchase quantity (e.g., 'g', 'ml', 'pcs').
    purchase_price: The price for the purchased quantity.
"""

recipes = Table(
    "recipes",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True, index=True),
    Column("description", Text, nullable=True),
    Column("servings_per_batch", Float, nullable=False, default=1.0),
    Column("preparation_instructions", Text, nullable=True),
    Column("mixing_instructions", Text, nullable=True),
    Column("proofing_instructions", Text, nullable=True),
    Column("baking_instructions", Text, nullable=True),
    Column("resting_instructions", Text, nullable=True),
    Column("packaging_instructions", Text, nullable=True)
)
"""
Table to store information about recipes.

Attributes:
    id: Primary key for the recipe.
    name: Name of the recipe (must be unique).
    description: A short description of the recipe.
    servings_per_batch: How many servings a single batch of this recipe yields.
    preparation_instructions: Text field for preparation steps.
    mixing_instructions: Text field for mixing steps.
    proofing_instructions: Text field for proofing steps.
    baking_instructions: Text field for baking steps.
    resting_instructions: Text field for resting steps.
    packaging_instructions: Text field for packaging steps.
"""

recipe_ingredients = Table(
    "recipe_ingredients",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("recipe_id", Integer, ForeignKey("recipes.id"), nullable=False),
    Column("ingredient_id", Integer, ForeignKey("ingredients.id"), nullable=False),
    Column("quantity_used_in_recipe", Float, nullable=False),
    Column("unit_used_in_recipe", String, nullable=False)  # e.g., 'g', 'ml', 'pcs'
)
"""
Association table linking recipes to their ingredients.

Attributes:
    id: Primary key for the recipe-ingredient link.
    recipe_id: Foreign key referencing the recipes table.
    ingredient_id: Foreign key referencing the ingredients table.
    quantity_used_in_recipe: The amount of the ingredient used in the recipe.
    unit_used_in_recipe: The unit for the quantity used (e.g., 'g', 'ml', 'pcs').
"""

packaging_costs = Table(
    "packaging_costs",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("item_name", String, nullable=False, index=True),
    Column("cost_per_unit", Float, nullable=False),  # e.g., cost per box, per wrapper
    Column("recipe_id", Integer, ForeignKey("recipes.id"), nullable=True), # Optional
    Column("units_per_recipe_batch", Float, nullable=True) # How many of these packaging units are used for one batch of a recipe
)
"""
Table to store information about packaging costs.

Attributes:
    id: Primary key for the packaging cost item.
    item_name: Name of the packaging item.
    cost_per_unit: Cost for a single unit of this packaging item.
    recipe_id: Optional foreign key to link packaging cost directly to a specific recipe.
               If NULL, this is a general packaging item.
    units_per_recipe_batch: How many units of this packaging item are used per batch of the linked recipe.
                            Should be NULL if recipe_id is NULL.
"""
