import pytest
import pytest_asyncio # For async fixtures if needed, though direct use of pytest.mark.asyncio is common
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.cost_calculator_service import calculate_recipe_production_cost
from app.models.recipe_models import RecipeRead, RecipeIngredientRead
from app.models.ingredient_models import IngredientRead
from app.models.packaging_cost_models import PackagingCostRead
from app.models.cost_models import RecipeCostDetails, CalculatedIngredientCost, CalculatedPackagingCost

# Sample Data for Mocks

MOCK_INGREDIENT_FLOUR = IngredientRead(
    id=1, name="All-Purpose Flour", purchase_quantity=1000, purchase_unit="g", purchase_price=15000.0
) # Cost per g = 15

MOCK_INGREDIENT_SUGAR = IngredientRead(
    id=2, name="Granulated Sugar", purchase_quantity=1000, purchase_unit="g", purchase_price=18000.0
) # Cost per g = 18

MOCK_INGREDIENT_MISMATCH_UNIT = IngredientRead(
    id=3, name="Olive Oil", purchase_quantity=500, purchase_unit="ml", purchase_price=50000.0
) # Cost per ml = 100

MOCK_INGREDIENT_ZERO_QUANTITY = IngredientRead(
    id=4, name="Special Spice", purchase_quantity=0, purchase_unit="g", purchase_price=10000.0
) # Cost undefined

MOCK_RECIPE_INGREDIENT_FLOUR_ASSOC = RecipeIngredientRead(
    id=101, ingredient_id=1, quantity_used_in_recipe=200, unit_used_in_recipe="g", ingredient_name="All-Purpose Flour"
) # Expected cost = 200 * 15 = 3000

MOCK_RECIPE_INGREDIENT_SUGAR_ASSOC = RecipeIngredientRead(
    id=102, ingredient_id=2, quantity_used_in_recipe=100, unit_used_in_recipe="g", ingredient_name="Granulated Sugar"
) # Expected cost = 100 * 18 = 1800

MOCK_RECIPE_INGREDIENT_OIL_ASSOC_MISMATCH = RecipeIngredientRead(
    id=103, ingredient_id=3, quantity_used_in_recipe=50, unit_used_in_recipe="g", ingredient_name="Olive Oil" # Recipe uses 'g', purchase is 'ml'
) # Expected cost = 50 * 100 = 5000 (with warning)

MOCK_RECIPE_INGREDIENT_SPICE_ASSOC_ZERO_QUANTITY = RecipeIngredientRead(
    id=104, ingredient_id=4, quantity_used_in_recipe=5, unit_used_in_recipe="g", ingredient_name="Special Spice"
) # Expected cost = 0 (with warning)

MOCK_RECIPE_INGREDIENT_NOT_FOUND_ASSOC = RecipeIngredientRead(
    id=105, ingredient_id=999, quantity_used_in_recipe=10, unit_used_in_recipe="pcs", ingredient_name="Phantom Fruit"
) # Base ingredient will not be found

MOCK_PACKAGING_COST_BOX = PackagingCostRead(
    id=201, item_name="Cake Box", cost_per_unit=1500, recipe_id=1, units_per_recipe_batch=1, recipe_name="Test Recipe 1"
) # Expected cost = 1500 * 1 = 1500

MOCK_PACKAGING_COST_LABEL = PackagingCostRead(
    id=202, item_name="Sticker Label", cost_per_unit=500, recipe_id=1, units_per_recipe_batch=1, recipe_name="Test Recipe 1"
) # Expected cost = 500 * 1 = 500

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_calculate_full_recipe_cost_success(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test successful calculation with ingredients and packaging."""
    mock_recipe = RecipeRead(
        id=1, name="Test Recipe 1", servings_per_batch=10,
        ingredients=[MOCK_RECIPE_INGREDIENT_FLOUR_ASSOC, MOCK_RECIPE_INGREDIENT_SUGAR_ASSOC],
        description="Desc" # Add other required fields for RecipeRead if any
    )
    mock_get_recipe_by_id.return_value = mock_recipe

    def side_effect_get_ingredient(ingredient_id):
        if ingredient_id == 1: return MOCK_INGREDIENT_FLOUR
        if ingredient_id == 2: return MOCK_INGREDIENT_SUGAR
        return None
    mock_get_ingredient_by_id.side_effect = side_effect_get_ingredient

    mock_get_all_packaging_costs.return_value = [MOCK_PACKAGING_COST_BOX, MOCK_PACKAGING_COST_LABEL]

    result = await calculate_recipe_production_cost(recipe_id=1)

    assert result is not None
    assert result.recipe_id == 1
    assert result.recipe_name == "Test Recipe 1"
    assert result.total_ingredient_cost == pytest.approx(3000.0 + 1800.0) # Flour + Sugar
    assert result.total_packaging_cost == pytest.approx(1500.0 + 500.0) # Box + Label
    assert result.total_production_cost == pytest.approx(3000.0 + 1800.0 + 1500.0 + 500.0)
    assert result.cost_per_serving == pytest.approx((3000.0 + 1800.0 + 1500.0 + 500.0) / 10)
    assert len(result.ingredient_cost_breakdown) == 2
    assert len(result.packaging_cost_breakdown) == 2
    assert result.ingredient_cost_breakdown[0].cost_for_recipe == 3000.0
    assert result.ingredient_cost_breakdown[1].cost_for_recipe == 1800.0
    assert result.packaging_cost_breakdown[0].cost_for_recipe == 1500.0
    assert result.packaging_cost_breakdown[1].cost_for_recipe == 500.0

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_recipe_not_found(
    mock_get_all_packaging_costs: AsyncMock, # Needs to be passed due to patching order
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test case where the recipe ID does not exist."""
    mock_get_recipe_by_id.return_value = None
    result = await calculate_recipe_production_cost(recipe_id=999)
    assert result is None

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_unit_mismatch_warning(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test that a warning is generated for unit mismatches."""
    mock_recipe = RecipeRead(id=2, name="Mismatch Recipe", servings_per_batch=1, ingredients=[MOCK_RECIPE_INGREDIENT_OIL_ASSOC_MISMATCH])
    mock_get_recipe_by_id.return_value = mock_recipe
    mock_get_ingredient_by_id.return_value = MOCK_INGREDIENT_MISMATCH_UNIT
    mock_get_all_packaging_costs.return_value = [] # No packaging costs

    result = await calculate_recipe_production_cost(recipe_id=2)
    assert result is not None
    assert len(result.ingredient_cost_breakdown) == 1
    assert result.ingredient_cost_breakdown[0].warning is not None
    assert "Unit mismatch" in result.ingredient_cost_breakdown[0].warning
    # Cost is still calculated based on direct multiplication
    assert result.ingredient_cost_breakdown[0].cost_for_recipe == pytest.approx(50 * 100.0)

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_ingredient_purchase_quantity_zero(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test ingredient with purchase_quantity = 0, leading to a warning and zero cost for that ingredient."""
    mock_recipe = RecipeRead(id=3, name="ZeroQuant Recipe", servings_per_batch=1, ingredients=[MOCK_RECIPE_INGREDIENT_SPICE_ASSOC_ZERO_QUANTITY])
    mock_get_recipe_by_id.return_value = mock_recipe
    mock_get_ingredient_by_id.return_value = MOCK_INGREDIENT_ZERO_QUANTITY
    mock_get_all_packaging_costs.return_value = []

    result = await calculate_recipe_production_cost(recipe_id=3)
    assert result is not None
    assert len(result.ingredient_cost_breakdown) == 1
    assert result.ingredient_cost_breakdown[0].cost_for_recipe == 0.0
    assert result.ingredient_cost_breakdown[0].warning is not None
    assert "Purchase quantity is zero" in result.ingredient_cost_breakdown[0].warning

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_base_ingredient_not_found(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test scenario where a base ingredient referenced in a recipe is not found."""
    mock_recipe = RecipeRead(id=4, name="MissingIngredient Recipe", servings_per_batch=1, ingredients=[MOCK_RECIPE_INGREDIENT_NOT_FOUND_ASSOC])
    mock_get_recipe_by_id.return_value = mock_recipe
    mock_get_ingredient_by_id.return_value = None # Simulate ingredient not found
    mock_get_all_packaging_costs.return_value = []

    result = await calculate_recipe_production_cost(recipe_id=4)
    assert result is not None
    assert len(result.ingredient_cost_breakdown) == 1
    assert result.ingredient_cost_breakdown[0].cost_for_recipe == 0.0
    assert result.ingredient_cost_breakdown[0].warning is not None
    assert f"Base ingredient with ID {MOCK_RECIPE_INGREDIENT_NOT_FOUND_ASSOC.ingredient_id} not found" in result.ingredient_cost_breakdown[0].warning

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_zero_servings_per_batch(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock,
    mock_get_recipe_by_id: AsyncMock
):
    """Test calculation when servings_per_batch is zero."""
    mock_recipe = RecipeRead(id=5, name="ZeroServings Recipe", servings_per_batch=0, ingredients=[MOCK_RECIPE_INGREDIENT_FLOUR_ASSOC])
    mock_get_recipe_by_id.return_value = mock_recipe
    mock_get_ingredient_by_id.return_value = MOCK_INGREDIENT_FLOUR
    mock_get_all_packaging_costs.return_value = []

    result = await calculate_recipe_production_cost(recipe_id=5)
    assert result is not None
    assert result.cost_per_serving == 0.0 # Or handle as error/infinity, current logic results in 0
    assert result.total_ingredient_cost == pytest.approx(3000.0)
    assert result.total_production_cost == pytest.approx(3000.0)

@pytest.mark.asyncio
@patch('app.services.cost_calculator_service.crud_recipes.get_recipe_by_id')
@patch('app.services.cost_calculator_service.crud_ingredients.get_ingredient_by_id')
@patch('app.services.cost_calculator_service.crud_packaging_costs.get_all_packaging_costs')
async def test_no_ingredients_no_packaging(
    mock_get_all_packaging_costs: AsyncMock,
    mock_get_ingredient_by_id: AsyncMock, # Still needed by patch order
    mock_get_recipe_by_id: AsyncMock
):
    """Test calculation for a recipe with no ingredients and no packaging costs."""
    mock_recipe = RecipeRead(id=6, name="Empty Recipe", servings_per_batch=1, ingredients=[])
    mock_get_recipe_by_id.return_value = mock_recipe
    mock_get_all_packaging_costs.return_value = []

    result = await calculate_recipe_production_cost(recipe_id=6)
    assert result is not None
    assert result.total_ingredient_cost == 0.0
    assert result.total_packaging_cost == 0.0
    assert result.total_production_cost == 0.0
    assert result.cost_per_serving == 0.0
    assert len(result.ingredient_cost_breakdown) == 0
    assert len(result.packaging_cost_breakdown) == 0

# To run these tests:
# Ensure PYTHONPATH includes the project root (e.g., `export PYTHONPATH=/path/to/your/app_root:$PYTHONPATH`)
# Then run `pytest app/tests/test_cost_calculator_service.py`
# Ensure `__init__.py` files are present in `app`, `app/services`, `app/tests` etc. for pytest to discover modules.
