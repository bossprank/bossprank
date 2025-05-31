from typing import Optional, List
from app.db import crud_recipes, crud_ingredients, crud_packaging_costs
from app.models.recipe_models import RecipeRead # Used by crud_recipes.get_recipe_by_id
from app.models.ingredient_models import IngredientRead # Used by crud_ingredients.get_ingredient_by_id
from app.models.packaging_cost_models import PackagingCostRead # Used by crud_packaging_costs
from app.models.cost_models import RecipeCostDetails, CalculatedIngredientCost, CalculatedPackagingCost

async def calculate_recipe_production_cost(recipe_id: int) -> Optional[RecipeCostDetails]:
    """
    Calculates the production cost for a given recipe, including ingredients and packaging.

    Args:
        recipe_id: The ID of the recipe to calculate costs for.

    Returns:
        A RecipeCostDetails object containing the full cost breakdown, or None if the recipe is not found.
    """
    recipe: Optional[RecipeRead] = await crud_recipes.get_recipe_by_id(recipe_id)
    if not recipe:
        return None

    total_ingredient_cost: float = 0.0
    ingredient_cost_breakdown: List[CalculatedIngredientCost] = []

    for recipe_ingredient_assoc in recipe.ingredients:
        base_ingredient: Optional[IngredientRead] = await crud_ingredients.get_ingredient_by_id(
            recipe_ingredient_assoc.ingredient_id
        )

        current_warning: Optional[str] = None
        ingredient_cost_for_recipe: float = 0.0
        cost_per_purchase_unit: Optional[float] = None

        if not base_ingredient:
            current_warning = f"Base ingredient with ID {recipe_ingredient_assoc.ingredient_id} not found. Cannot calculate cost."
            # Add a placeholder to the breakdown with the warning
            ingredient_cost_breakdown.append(
                CalculatedIngredientCost(
                    ingredient_id=recipe_ingredient_assoc.ingredient_id,
                    ingredient_name=recipe_ingredient_assoc.ingredient_name or f"Unknown Ingredient (ID: {recipe_ingredient_assoc.ingredient_id})",
                    quantity_used_in_recipe=recipe_ingredient_assoc.quantity_used_in_recipe,
                    unit_used_in_recipe=recipe_ingredient_assoc.unit_used_in_recipe,
                    cost_for_recipe=0.0, # No cost can be calculated
                    warning=current_warning
                )
            )
            continue # Skip to next ingredient

        # Basic unit compatibility warning (placeholder for a real unit conversion system)
        if base_ingredient.purchase_unit.lower() != recipe_ingredient_assoc.unit_used_in_recipe.lower():
            current_warning = (
                f"Unit mismatch: Purchase unit is '{base_ingredient.purchase_unit}', "
                f"recipe unit is '{recipe_ingredient_assoc.unit_used_in_recipe}'. "
                "Cost calculation assumes units are directly compatible and might be inaccurate."
            )
            # More advanced: if warning is critical, could set cost to 0 or handle differently

        if base_ingredient.purchase_quantity == 0: # Avoid division by zero
            if current_warning:
                current_warning += " Additionally, purchase quantity is zero, cannot calculate cost per unit."
            else:
                current_warning = "Purchase quantity is zero. Cannot calculate cost per unit."
            ingredient_cost_for_recipe = 0.0 # Cannot calculate cost
        else:
            cost_per_purchase_unit = base_ingredient.purchase_price / base_ingredient.purchase_quantity
            ingredient_cost_for_recipe = cost_per_purchase_unit * recipe_ingredient_assoc.quantity_used_in_recipe

        total_ingredient_cost += ingredient_cost_for_recipe

        ingredient_cost_breakdown.append(
            CalculatedIngredientCost(
                ingredient_id=base_ingredient.id,
                ingredient_name=base_ingredient.name, # Use name from base_ingredient for consistency
                quantity_used_in_recipe=recipe_ingredient_assoc.quantity_used_in_recipe,
                unit_used_in_recipe=recipe_ingredient_assoc.unit_used_in_recipe,
                cost_for_recipe=ingredient_cost_for_recipe,
                purchase_unit=base_ingredient.purchase_unit,
                purchase_quantity=base_ingredient.purchase_quantity,
                purchase_price=base_ingredient.purchase_price,
                cost_per_purchase_unit=cost_per_purchase_unit,
                warning=current_warning
            )
        )

    total_packaging_cost: float = 0.0
    packaging_cost_breakdown: List[CalculatedPackagingCost] = []

    # Fetch packaging costs specifically associated with this recipe
    # crud_packaging_costs.get_all_packaging_costs can filter by recipe_id
    recipe_specific_packaging_items: List[PackagingCostRead] = await crud_packaging_costs.get_all_packaging_costs(
        recipe_id_filter=recipe_id
    )

    for packaging_item in recipe_specific_packaging_items:
        item_cost_for_recipe: float = 0.0
        # units_per_recipe_batch should not be None if recipe_id is set, but check for safety
        if packaging_item.units_per_recipe_batch is not None and packaging_item.units_per_recipe_batch > 0:
            item_cost_for_recipe = packaging_item.cost_per_unit * packaging_item.units_per_recipe_batch

        total_packaging_cost += item_cost_for_recipe
        packaging_cost_breakdown.append(
            CalculatedPackagingCost(
                packaging_cost_id=packaging_item.id,
                item_name=packaging_item.item_name,
                units_per_recipe_batch=packaging_item.units_per_recipe_batch or 0, # Default to 0 if None
                cost_per_unit=packaging_item.cost_per_unit,
                cost_for_recipe=item_cost_for_recipe
            )
        )

    total_production_cost = total_ingredient_cost + total_packaging_cost

    cost_per_serving: float = 0.0
    if recipe.servings_per_batch > 0:
        cost_per_serving = total_production_cost / recipe.servings_per_batch
    else:
        # Optionally, add a warning or handle as an error if servings_per_batch is not positive
        pass

    return RecipeCostDetails(
        recipe_id=recipe.id,
        recipe_name=recipe.name,
        servings_per_batch=recipe.servings_per_batch,
        total_ingredient_cost=total_ingredient_cost,
        total_packaging_cost=total_packaging_cost,
        total_production_cost=total_production_cost,
        cost_per_serving=cost_per_serving,
        ingredient_cost_breakdown=ingredient_cost_breakdown,
        packaging_cost_breakdown=packaging_cost_breakdown
    )
