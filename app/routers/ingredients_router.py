from fastapi import APIRouter, HTTPException, status
from typing import List, Optional # Optional for response models if needed, though handled by 404

from app.models.ingredient_models import IngredientCreate, IngredientUpdate, IngredientRead
from app.db import crud_ingredients # Assuming crud_ingredients.py is in app/db/

router = APIRouter(
    prefix="/api/v1/ingredients",
    tags=["Ingredients"],
    responses={404: {"description": "Ingredient not found"}},
)

# Attempt to import templates from app.main
# This might require adjustment if app.main causes circular imports when router is imported back to main
# A common pattern is to have a core.templating module or pass templates instance around.
# For now, let's try direct import.
try:
    from app.main import templates
except ImportError:
    # Fallback or placeholder if direct import causes issues.
    # This indicates a need to refactor how templates are shared.
    # For this step, we'll assume it might fail and log it, but proceed with a dummy
    # if direct import fails, actual rendering would fail later.
    print("WARN: Could not import templates from app.main in ingredients_router.py. HTML rendering will fail.")
    templates = None

from fastapi import Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import List, Optional

# Note: Pydantic models (IngredientCreate, etc.) are already imported

# HTML Views for Ingredients

@router.get("/view/", response_class=HTMLResponse, name="view_list_ingredients") # Use response_class for direct Response types
async def view_list_ingredients(request: Request):
    """Serves HTML page to list all ingredients."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    all_ingredients_data = await crud_ingredients.get_all_ingredients(limit=1000) # Get all for now
    return templates.TemplateResponse(
        "ingredients/list_ingredients.html",
        {"request": request, "ingredients": all_ingredients_data}
    )

@router.get("/view/new", response_class=HTMLResponse, name="view_create_ingredient_form") # Use response_class
async def view_create_ingredient_form(request: Request):
    """Serves HTML form to create a new ingredient."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")
    return templates.TemplateResponse(
        "ingredients/form_ingredient.html",
        {
            "request": request,
            "form_title": "Add New Ingredient",
            "submit_button_text": "Create",
            "form_action_url": request.url_for("handle_create_ingredient"),
            "ingredient": None # No existing ingredient data for new form
        }
    )

@router.post("/view/new", name="handle_create_ingredient")
async def handle_create_ingredient(
    name: str = Form(...),
    purchase_quantity: float = Form(...),
    purchase_unit: str = Form(...),
    purchase_price: float = Form(...)
):
    """Handles submission of the new ingredient form."""
    ingredient_data = IngredientCreate(
        name=name,
        purchase_quantity=purchase_quantity,
        purchase_unit=purchase_unit,
        purchase_price=purchase_price
    )
    try:
        await crud_ingredients.create_ingredient(ingredient_data)
    except Exception as e:
        # TODO: Add user-friendly error feedback on the form page
        raise HTTPException(status_code=400, detail=f"Error creating ingredient: {str(e)}")

    return RedirectResponse(
        url=router.url_path_for("view_list_ingredients"),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/view/edit/{ingredient_id}", response_class=HTMLResponse, name="view_edit_ingredient_form") # Use response_class
async def view_edit_ingredient_form(request: Request, ingredient_id: int):
    """Serves HTML form to edit an existing ingredient."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    ingredient = await crud_ingredients.get_ingredient_by_id(ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return templates.TemplateResponse(
        "ingredients/form_ingredient.html",
        {
            "request": request,
            "form_title": "Edit Ingredient",
            "submit_button_text": "Update",
            "form_action_url": request.url_for("handle_edit_ingredient", ingredient_id=ingredient_id),
            "ingredient": ingredient
        }
    )

@router.post("/view/edit/{ingredient_id}", name="handle_edit_ingredient")
async def handle_edit_ingredient(
    ingredient_id: int,
    name: str = Form(...),
    purchase_quantity: float = Form(...),
    purchase_unit: str = Form(...),
    purchase_price: float = Form(...)
):
    """Handles submission of the edited ingredient form."""
    ingredient_data = IngredientUpdate(
        name=name,
        purchase_quantity=purchase_quantity,
        purchase_unit=purchase_unit,
        purchase_price=purchase_price
    )
    updated_ingredient = await crud_ingredients.update_ingredient_by_id(ingredient_id, ingredient_data)
    if not updated_ingredient:
        # TODO: Add user-friendly error feedback on the form page
        raise HTTPException(status_code=404, detail="Ingredient not found or failed to update")

    return RedirectResponse(
        url=router.url_path_for("view_list_ingredients"),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/view/delete/{ingredient_id}", name="handle_delete_ingredient")
async def handle_delete_ingredient(ingredient_id: int, request: Request):
    """Handles deletion of an ingredient."""
    result = await crud_ingredients.delete_ingredient_by_id(ingredient_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Ingredient not found, cannot delete.")

    return RedirectResponse(
        url=router.url_path_for("view_list_ingredients"),
        status_code=status.HTTP_303_SEE_OTHER
    )


# API Endpoints (already defined previously, ensure they are below HTML view routes or use separate routers if preferred)
@router.post("/", response_model=IngredientRead, status_code=status.HTTP_201_CREATED, tags=["Ingredients API"])
async def create_new_ingredient(ingredient: IngredientCreate):
    """
    Create a new ingredient.

    - **name**: Each ingredient must have a unique name.
    - **purchase_quantity**: The quantity in which this ingredient is typically purchased.
    - **purchase_unit**: The unit for the purchase quantity (e.g., 'g', 'ml', 'pcs').
    - **purchase_price**: The price for the `purchase_quantity`.
    """
    # Optional: Check if ingredient with the same name already exists
    # existing_ingredient_by_name = await crud_ingredients.get_ingredient_by_name(ingredient.name)
    # if existing_ingredient_by_name:
    #     raise HTTPException(status_code=400, detail="Ingredient with this name already exists")
    # This is the API version, distinct from the form handler
    try:
        created_ingredient = await crud_ingredients.create_ingredient(ingredient_data=ingredient)
        return created_ingredient
    except Exception as e:
        # A more specific exception handling might be needed
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"API: Failed to create ingredient: {str(e)}")


@router.get("/", response_model=List[IngredientRead], tags=["Ingredients API"])
async def read_all_ingredients(skip: int = 0, limit: int = 100):
    """
    Retrieve a list of all ingredients.
    Supports pagination using `skip` and `limit` query parameters.
    """
    ingredients = await crud_ingredients.get_all_ingredients(skip=skip, limit=limit)
    return ingredients


@router.get("/{ingredient_id}", response_model=IngredientRead)
async def read_ingredient_by_id(ingredient_id: int):
    """
    Retrieve a specific ingredient by its ID.
    """
    ingredient = await crud_ingredients.get_ingredient_by_id(ingredient_id=ingredient_id) # API version
    if ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return ingredient


@router.put("/{ingredient_id}", response_model=IngredientRead)
async def update_existing_ingredient(ingredient_id: int, ingredient: IngredientUpdate):
    """
    Update an existing ingredient by its ID.

    Only the fields provided in the request body will be updated.
    All fields in the `IngredientUpdate` model are optional.
    """
    updated_ingredient = await crud_ingredients.update_ingredient_by_id( # API version
        ingredient_id=ingredient_id, ingredient_data=ingredient
    )
    if updated_ingredient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return updated_ingredient


@router.delete("/{ingredient_id}", response_model=dict) # Or a specific success message model
async def remove_ingredient_by_id(ingredient_id: int):
    """
    Delete an ingredient by its ID.
    """
    result = await crud_ingredients.delete_ingredient_by_id(ingredient_id=ingredient_id) # API version
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return result

# Future consideration: Add an endpoint to get ingredient by name if needed
# @router.get("/name/{ingredient_name}", response_model=IngredientRead)
# async def read_ingredient_by_name(ingredient_name: str): # API version
# ...
