from fastapi import APIRouter, HTTPException, status
from typing import List, Optional

from app.models.recipe_models import RecipeCreate, RecipeUpdate, RecipeRead, RecipeIngredientCreate
from app.models.cost_models import RecipeCostDetails # For the new endpoint
from app.db import crud_recipes
from app.services import cost_calculator_service # For the new endpoint

router = APIRouter(
    prefix="/api/v1/recipes",
    tags=["Recipes"],
    responses={404: {"description": "Recipe not found"}},
)

# Attempt to import templates from app.main (adjust if needed for project structure)
try:
    from app.main import templates
except ImportError:
    templates = None # Placeholder

from fastapi import Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from app.db import crud_ingredients # To fetch all ingredients for forms

# HTML Views for Recipes

@router.get("/view/", response_class=HTMLResponse, name="view_list_recipes")
async def view_list_recipes(request: Request):
    """Serves HTML page to list all recipes."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    all_recipes_data = await crud_recipes.get_all_recipes(limit=1000) # Get all for now
    return templates.TemplateResponse(
        "recipes/list_recipes.html",
        {"request": request, "recipes": all_recipes_data}
    )

@router.get("/view/new", response_class=HTMLResponse, name="view_create_recipe_form")
async def view_create_recipe_form(request: Request):
    """Serves HTML form to create a new recipe."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    all_ingredients_data = await crud_ingredients.get_all_ingredients(limit=1000) # For dropdown
    all_ingredients_for_template = [ing.model_dump() for ing in all_ingredients_data]
    return templates.TemplateResponse(
        "recipes/form_recipe.html",
        {
            "request": request,
            "form_title": "Add New Recipe",
            "submit_button_text": "Create Recipe",
            "form_action_url": request.url_for("handle_create_recipe"),
            "recipe": None, # No existing recipe data for new form
            "all_ingredients": all_ingredients_for_template
        }
    )

def parse_dynamic_ingredients_from_form(form_data: dict) -> List[RecipeIngredientCreate]:
    """Helper to parse ingredient fields like ingredient_id_0, quantity_0, etc."""
    ingredients_create_list = []
    ingredient_indices = sorted(list(set([
        key.split('_')[-1] for key in form_data if key.startswith('ingredient_id_')
    ])))

    for index in ingredient_indices:
        ingredient_id = form_data.get(f"ingredient_id_{index}")
        quantity = form_data.get(f"quantity_{index}")
        unit = form_data.get(f"unit_{index}")

        if ingredient_id and quantity and unit: # Ensure all parts are present
            try:
                ingredients_create_list.append(
                    RecipeIngredientCreate(
                        ingredient_id=int(ingredient_id),
                        quantity_used_in_recipe=float(quantity),
                        unit_used_in_recipe=str(unit)
                    )
                )
            except ValueError:
                # Handle cases where conversion might fail, e.g., non-numeric quantity
                # Or raise an HTTPException for bad form data
                print(f"Warning: Could not parse ingredient at index {index}. Skipping.")
                continue # Or raise error
    return ingredients_create_list


@router.post("/view/new", name="handle_create_recipe")
async def handle_create_recipe(request: Request):
    """Handles submission of the new recipe form."""
    form_data = await request.form()
    form_data_dict = dict(form_data)

    recipe_ingredients_data = parse_dynamic_ingredients_from_form(form_data_dict)

    recipe_base_data = RecipeCreate(
        name=form_data_dict.get("name", ""),
        description=form_data_dict.get("description"),
        servings_per_batch=float(form_data_dict.get("servings_per_batch", 1.0)),
        preparation_instructions=form_data_dict.get("preparation_instructions"),
        mixing_instructions=form_data_dict.get("mixing_instructions"),
        proofing_instructions=form_data_dict.get("proofing_instructions"),
        baking_instructions=form_data_dict.get("baking_instructions"),
        resting_instructions=form_data_dict.get("resting_instructions"),
        packaging_instructions=form_data_dict.get("packaging_instructions"),
        ingredients=recipe_ingredients_data
    )

    try:
        await crud_recipes.create_recipe(recipe_base_data)
    except Exception as e:
        # TODO: Add user-friendly error feedback on the form page by re-rendering with error
        print(f"Error creating recipe: {e}")
        raise HTTPException(status_code=400, detail=f"Error creating recipe: {str(e)}")

    return RedirectResponse(url=router.url_path_for("view_list_recipes"), status_code=status.HTTP_303_SEE_OTHER)


@router.get("/view/{recipe_id}", response_class=HTMLResponse, name="view_single_recipe")
async def view_single_recipe(request: Request, recipe_id: int):
    """Serves HTML page to display details of a single recipe."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    recipe = await crud_recipes.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return templates.TemplateResponse(
        "recipes/view_recipe.html",
        {"request": request, "recipe": recipe}
    )

@router.get("/view/edit/{recipe_id}", response_class=HTMLResponse, name="view_edit_recipe_form")
async def view_edit_recipe_form(request: Request, recipe_id: int):
    """Serves HTML form to edit an existing recipe."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")

    recipe = await crud_recipes.get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    all_ingredients_data = await crud_ingredients.get_all_ingredients(limit=1000) # For dropdown
    all_ingredients_for_template = [ing.model_dump() for ing in all_ingredients_data]

    # Also convert current recipe's ingredients to dicts for the template
    recipe_dict = recipe.model_dump() if recipe else {}

    return templates.TemplateResponse(
        "recipes/form_recipe.html",
        {
            "request": request,
            "form_title": "Edit Recipe",
            "submit_button_text": "Update Recipe",
            "form_action_url": request.url_for("handle_edit_recipe", recipe_id=recipe_id),
            "recipe": recipe_dict, # Pass the dict version of the recipe
            "all_ingredients": all_ingredients_for_template
        }
    )

@router.post("/view/edit/{recipe_id}", name="handle_edit_recipe")
async def handle_edit_recipe(request: Request, recipe_id: int):
    """Handles submission of the edited recipe form."""
    form_data = await request.form()
    form_data_dict = dict(form_data)

    recipe_ingredients_data = parse_dynamic_ingredients_from_form(form_data_dict)

    recipe_update_data = RecipeUpdate(
        name=form_data_dict.get("name"), # Let Pydantic handle if it's missing or empty for optional
        description=form_data_dict.get("description"),
        servings_per_batch=float(form_data_dict.get("servings_per_batch", 1.0)) if form_data_dict.get("servings_per_batch") else None,
        preparation_instructions=form_data_dict.get("preparation_instructions"),
        mixing_instructions=form_data_dict.get("mixing_instructions"),
        proofing_instructions=form_data_dict.get("proofing_instructions"),
        baking_instructions=form_data_dict.get("baking_instructions"),
        resting_instructions=form_data_dict.get("resting_instructions"),
        packaging_instructions=form_data_dict.get("packaging_instructions"),
        ingredients=recipe_ingredients_data
    )

    updated_recipe = await crud_recipes.update_recipe_by_id(recipe_id, recipe_update_data)
    if not updated_recipe:
        # TODO: Add user-friendly error feedback
        raise HTTPException(status_code=404, detail="Recipe not found or failed to update")

    return RedirectResponse(url=router.url_path_for("view_list_recipes"), status_code=status.HTTP_303_SEE_OTHER)

@router.post("/view/delete/{recipe_id}", name="handle_delete_recipe")
async def handle_delete_recipe(recipe_id: int): # Request not needed if not using it
    """Handles deletion of a recipe."""
    result = await crud_recipes.delete_recipe_by_id(recipe_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Recipe not found, cannot delete.")

    return RedirectResponse(url=router.url_path_for("view_list_recipes"), status_code=status.HTTP_303_SEE_OTHER)

# New API Endpoint for Cost Details
@router.get("/{recipe_id}/cost-details", response_model=RecipeCostDetails, tags=["Recipes API", "Costing"])
async def get_recipe_cost_details(recipe_id: int):
    """
    Calculate and retrieve the detailed production costs for a specific recipe.
    Includes breakdown of ingredient costs and packaging costs.
    """
    cost_details = await cost_calculator_service.calculate_recipe_production_cost(recipe_id)
    if not cost_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found or cost calculation failed (e.g., underlying recipe data missing)."
        )
    return cost_details

# API Endpoints (ensure they are correctly tagged or separated if needed)
@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED, tags=["Recipes API"])
async def create_new_recipe(recipe: RecipeCreate):
    """
    Create a new recipe, including its ingredients.
    """
    try:
        created_recipe = await crud_recipes.create_recipe(recipe_data=recipe)
        return created_recipe
    except Exception as e:
        # Consider more specific error handling for unique name violations if added
        # For now, a general error for creation failure.
        # Also, log the error e for debugging.
        print(f"Error creating recipe: {e}") # Basic logging
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create recipe: {str(e)}")


@router.get("/", response_model=List[RecipeRead])
async def read_all_recipes(skip: int = 0, limit: int = 100):
    """
    Retrieve a list of all recipes, with ingredients populated.
    Supports pagination using `skip` and `limit` query parameters.
    """
    recipes = await crud_recipes.get_all_recipes(skip=skip, limit=limit)
    return recipes


@router.get("/{recipe_id}", response_model=RecipeRead)
async def read_recipe_by_id(recipe_id: int):
    """
    Retrieve a specific recipe by its ID, with ingredients populated.
    """
    recipe = await crud_recipes.get_recipe_by_id(recipe_id=recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.put("/{recipe_id}", response_model=RecipeRead)
async def update_existing_recipe(recipe_id: int, recipe: RecipeUpdate):
    """
    Update an existing recipe by its ID.
    This can update the recipe's own fields and/or replace its list of ingredients.
    - If `ingredients` list is provided in the payload, all existing ingredient associations
      for this recipe will be deleted and replaced with the new ones.
    - If `ingredients` list is omitted, existing ingredient associations remain unchanged.
    - To remove all ingredients, pass an empty list: `"ingredients": []`.
    """
    updated_recipe = await crud_recipes.update_recipe_by_id(
        recipe_id=recipe_id, recipe_data=recipe
    )
    if updated_recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found or update failed")
    return updated_recipe


@router.delete("/{recipe_id}", response_model=dict)
async def remove_recipe_by_id(recipe_id: int):
    """
    Delete a recipe by its ID.
    This will also delete all its associated ingredient entries in the `recipe_ingredients` table.
    """
    result = await crud_recipes.delete_recipe_by_id(recipe_id=recipe_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return result
