from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional

from app.models.packaging_cost_models import PackagingCostCreate, PackagingCostUpdate, PackagingCostRead
from app.db import crud_packaging_costs

router = APIRouter(
    prefix="/api/v1/packaging-costs",
    tags=["Packaging Costs"],
    responses={404: {"description": "Packaging cost item not found"}},
)

# Import templates and other necessary modules for HTML views
try:
    from app.main import templates
except ImportError:
    templates = None # Placeholder

from fastapi import Request, Form, Depends, HTTPException, status # Response already imported if needed by API part
from fastapi.responses import HTMLResponse, RedirectResponse
from app.db import crud_recipes # To fetch all recipes for forms

# HTML Views for Packaging Costs

@router.get("/view/", response_class=HTMLResponse, name="view_list_packaging_costs")
async def view_list_packaging_costs(
    request: Request,
    recipe_id_filter: Optional[int] = Query(None)
):
    """Serves HTML page to list all packaging costs, with optional recipe filter."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    all_costs_data = await crud_packaging_costs.get_all_packaging_costs(
        limit=1000, recipe_id_filter=recipe_id_filter
    )
    all_recipes_data = await crud_recipes.get_all_recipes(limit=1000) # For filter dropdown

    # Convert Pydantic models to dicts for template, especially if they contain nested models
    # For PackagingCostRead, recipe_name is already a simple attribute, so direct pass might be fine.
    # However, if all_recipes_data contains RecipeRead (which has nested IngredientRead), convert.

    return templates.TemplateResponse(
        "packaging_costs/list_packaging_costs.html",
        {
            "request": request,
            "packaging_costs": all_costs_data,
            "all_recipes": [recipe.model_dump() for recipe in all_recipes_data], # Ensure recipes are dicts
            "current_recipe_filter": recipe_id_filter
        }
    )

@router.get("/view/new", response_class=HTMLResponse, name="view_create_packaging_cost_form")
async def view_create_packaging_cost_form(request: Request):
    """Serves HTML form to create a new packaging cost item."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    all_recipes_data = await crud_recipes.get_all_recipes(limit=1000)
    return templates.TemplateResponse(
        "packaging_costs/form_packaging_cost.html",
        {
            "request": request,
            "form_title": "Add New Packaging Cost",
            "submit_button_text": "Create Cost",
            "form_action_url": request.url_for("handle_create_packaging_cost"),
            "cost_item": None,
            "all_recipes": [recipe.model_dump() for recipe in all_recipes_data]
        }
    )

@router.post("/view/new", name="handle_create_packaging_cost")
async def handle_create_packaging_cost(
    item_name: str = Form(...),
    cost_per_unit: float = Form(...),
    recipe_id: Optional[str] = Form(None), # Comes as string, might be ""
    units_per_recipe_batch: Optional[float] = Form(None)
):
    """Handles submission of the new packaging cost form."""
    actual_recipe_id = int(recipe_id) if recipe_id and recipe_id.isdigit() else None

    if actual_recipe_id is not None and units_per_recipe_batch is None:
        # This validation could also be done in Pydantic model if preferred
        raise HTTPException(status_code=422, detail="Units per recipe batch is required if a recipe is selected.")

    cost_data = PackagingCostCreate(
        item_name=item_name,
        cost_per_unit=cost_per_unit,
        recipe_id=actual_recipe_id,
        units_per_recipe_batch=units_per_recipe_batch if actual_recipe_id else None
    )
    try:
        await crud_packaging_costs.create_packaging_cost(cost_data)
    except Exception as e:
        # TODO: Better error display on form
        raise HTTPException(status_code=400, detail=f"Error creating packaging cost: {str(e)}")

    return RedirectResponse(url=router.url_path_for("view_list_packaging_costs"), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/view/edit/{cost_id}", response_class=HTMLResponse, name="view_edit_packaging_cost_form")
async def view_edit_packaging_cost_form(request: Request, cost_id: int):
    """Serves HTML form to edit an existing packaging cost item."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    cost_item = await crud_packaging_costs.get_packaging_cost_by_id(cost_id)
    if not cost_item:
        raise HTTPException(status_code=404, detail="Packaging cost item not found")

    all_recipes_data = await crud_recipes.get_all_recipes(limit=1000)

    return templates.TemplateResponse(
        "packaging_costs/form_packaging_cost.html",
        {
            "request": request,
            "form_title": "Edit Packaging Cost",
            "submit_button_text": "Update Cost",
            "form_action_url": request.url_for("handle_edit_packaging_cost", cost_id=cost_id),
            "cost_item": cost_item.model_dump(), # Convert to dict for template
            "all_recipes": [recipe.model_dump() for recipe in all_recipes_data]
        }
    )

@router.post("/view/edit/{cost_id}", name="handle_edit_packaging_cost")
async def handle_edit_packaging_cost(
    cost_id: int,
    request: Request # Added request to access form data directly
    # item_name: str = Form(...), # Will get from form_data
    # cost_per_unit: float = Form(...),
    # recipe_id: Optional[str] = Form(None),
    # units_per_recipe_batch: Optional[float] = Form(None)
):
    """Handles submission of the edited packaging cost form."""
    form_data = await request.form()
    item_name = form_data.get("item_name")
    cost_per_unit_str = form_data.get("cost_per_unit")
    recipe_id_str = form_data.get("recipe_id")
    units_per_recipe_batch_str = form_data.get("units_per_recipe_batch")

    if not item_name or not cost_per_unit_str:
        raise HTTPException(status_code=422, detail="Item name and cost per unit are required.")

    try:
        cost_per_unit = float(cost_per_unit_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid cost per unit format.")

    actual_recipe_id = int(recipe_id_str) if recipe_id_str and recipe_id_str.isdigit() else None

    actual_units_batch = None
    if units_per_recipe_batch_str and units_per_recipe_batch_str.strip():
        try:
            actual_units_batch = float(units_per_recipe_batch_str)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid units per recipe batch format.")

    if actual_recipe_id is not None and actual_units_batch is None:
        raise HTTPException(status_code=422, detail="Units per recipe batch is required if a recipe is selected, and must be a valid number.")

    cost_update_data = PackagingCostUpdate(
        item_name=item_name,
        cost_per_unit=cost_per_unit,
        recipe_id=actual_recipe_id,
        units_per_recipe_batch=actual_units_batch if actual_recipe_id else None
    )

    updated_item = await crud_packaging_costs.update_packaging_cost_by_id(cost_id, cost_update_data)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Packaging cost item not found or failed to update")

    return RedirectResponse(url=router.url_path_for("view_list_packaging_costs"), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/view/delete/{cost_id}", name="handle_delete_packaging_cost")
async def handle_delete_packaging_cost(cost_id: int):
    """Handles deletion of a packaging cost item."""
    result = await crud_packaging_costs.delete_packaging_cost_by_id(cost_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Packaging cost item not found, cannot delete.")

    return RedirectResponse(url=router.url_path_for("view_list_packaging_costs"), status_code=status.HTTP_303_SEE_OTHER)


# API Endpoints (ensure they are correctly tagged or separated if needed)
@router.post("/", response_model=PackagingCostRead, status_code=status.HTTP_201_CREATED, tags=["Packaging Costs API"])
async def create_new_packaging_cost_item(cost_item: PackagingCostCreate):
    """
    Create a new packaging cost item.
    - `item_name`: Name of the packaging item (e.g., "Box Size M", "Plastic Seal Sticker").
    - `cost_per_unit`: Cost for one unit of this item.
    - `recipe_id` (optional): Link this cost item directly to a specific recipe.
    - `units_per_recipe_batch` (optional): How many units of this packaging item are used per batch of the linked recipe.
      Should generally be provided if `recipe_id` is set.
    """
    try:
        # Optional: Add validation, e.g., if recipe_id is provided, units_per_recipe_batch should also be.
        if cost_item.recipe_id is not None and cost_item.units_per_recipe_batch is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="units_per_recipe_batch is required if recipe_id is provided."
            )
        created_item = await crud_packaging_costs.create_packaging_cost(cost_data=cost_item)
        return created_item
    except HTTPException: # Re-raise specific HTTP exceptions
        raise
    except Exception as e:
        # Log the error e for server-side debugging
        print(f"Error creating packaging cost: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create packaging cost item: {str(e)}")


@router.get("/", response_model=List[PackagingCostRead])
async def read_all_packaging_cost_items(
    skip: int = 0,
    limit: int = 100,
    recipe_id_filter: Optional[int] = Query(None, description="Filter packaging costs by a specific recipe ID")
):
    """
    Retrieve a list of all packaging cost items.
    Supports pagination and optional filtering by `recipe_id_filter`.
    `recipe_name` will be populated if the item is linked to a recipe.
    """
    items = await crud_packaging_costs.get_all_packaging_costs(
        skip=skip, limit=limit, recipe_id_filter=recipe_id_filter
    )
    return items


@router.get("/{cost_id}", response_model=PackagingCostRead)
async def read_packaging_cost_item_by_id(cost_id: int):
    """
    Retrieve a specific packaging cost item by its ID.
    `recipe_name` will be populated if the item is linked to a recipe.
    """
    item = await crud_packaging_costs.get_packaging_cost_by_id(cost_id=cost_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging cost item not found")
    return item


@router.put("/{cost_id}", response_model=PackagingCostRead)
async def update_existing_packaging_cost_item(cost_id: int, cost_item: PackagingCostUpdate):
    """
    Update an existing packaging cost item by its ID.
    Only the fields provided in the request body will be updated.
    """
    # Optional: Add validation for units_per_recipe_batch if recipe_id is being set or changed.
    if cost_item.recipe_id is not None and cost_item.units_per_recipe_batch is None:
        # If an existing item is being updated to link to a recipe, units_per_recipe_batch should be specified.
        # However, if only other fields are updated and recipe_id is not in payload, this check is not needed.
        # This logic might be better placed in the Pydantic model with validators if complex.
        pass # Current Pydantic model allows units_per_recipe_batch to be None even if recipe_id is set.

    updated_item = await crud_packaging_costs.update_packaging_cost_by_id(
        cost_id=cost_id, cost_data=cost_item
    )
    if updated_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging cost item not found or update failed")
    return updated_item


@router.delete("/{cost_id}", response_model=dict)
async def remove_packaging_cost_item_by_id(cost_id: int):
    """
    Delete a packaging cost item by its ID.
    """
    result = await crud_packaging_costs.delete_packaging_cost_by_id(cost_id=cost_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging cost item not found")
    return result
