from sqlalchemy import select, insert, update, delete, text, join
from sqlalchemy.ext.asyncio import AsyncConnection
from typing import List, Optional

from app.db.database import engine
from app.db.schema import recipes as recipes_table
from app.db.schema import recipe_ingredients as recipe_ingredients_table
from app.db.schema import ingredients as ingredients_table # For looking up ingredient names
from app.models.recipe_models import RecipeCreate, RecipeUpdate, RecipeRead, \
                                     RecipeIngredientCreate, RecipeIngredientRead


async def _populate_recipe_ingredients_details(conn: AsyncConnection, recipe_id: int) -> List[RecipeIngredientRead]:
    """
    Helper function to fetch and populate ingredient details for a given recipe.
    This includes the ingredient's name from the 'ingredients' table.
    """
    # Select from recipe_ingredients joined with ingredients table
    j = join(recipe_ingredients_table, ingredients_table,
             recipe_ingredients_table.c.ingredient_id == ingredients_table.c.id)

    stmt = select(
        recipe_ingredients_table.c.id, # ID of the recipe_ingredients entry
        recipe_ingredients_table.c.ingredient_id,
        recipe_ingredients_table.c.quantity_used_in_recipe,
        recipe_ingredients_table.c.unit_used_in_recipe,
        ingredients_table.c.name.label("ingredient_name") # Get the name from the ingredients table
    ).select_from(j).where(recipe_ingredients_table.c.recipe_id == recipe_id)

    result = await conn.execute(stmt)
    ingredient_details_db = result.fetchall()

    return [RecipeIngredientRead.model_validate(row) for row in ingredient_details_db]


async def create_recipe(recipe_data: RecipeCreate) -> RecipeRead:
    """
    Creates a new recipe in the database along with its ingredients.

    Args:
        recipe_data: Pydantic model for creating a recipe.

    Returns:
        The created recipe, including its ID and detailed ingredient list.
    """
    async with engine.connect() as conn:
        # Start a transaction
        async with conn.begin():
            # Insert into recipes table
            recipe_values = recipe_data.model_dump(exclude={"ingredients"})
            stmt_recipe = insert(recipes_table).values(**recipe_values)
            result_recipe = await conn.execute(stmt_recipe)
            recipe_id = result_recipe.lastrowid
            if recipe_id is None:
                # Should not happen with autoincrement PK
                raise Exception("Failed to create recipe or retrieve its ID.")

            # Insert into recipe_ingredients table
            if recipe_data.ingredients:
                for ingredient_assoc_data in recipe_data.ingredients:
                    stmt_ingredient_assoc = insert(recipe_ingredients_table).values(
                        recipe_id=recipe_id,
                        **ingredient_assoc_data.model_dump()
                    )
                    await conn.execute(stmt_ingredient_assoc)

            # Commit happens automatically with conn.begin() success

        # Fetch the newly created recipe with all details
        # Need a new connection or ensure the previous one can fetch after commit (conn.begin() handles this)
        # For simplicity, call the get_recipe_by_id which uses its own connection context
        # However, it's more efficient to use the same transaction/connection if possible.
        # Let's fetch directly here to ensure we are within a consistent state post-commit of the above transaction.

        # Fetch recipe base details
        stmt_get_recipe = select(recipes_table).where(recipes_table.c.id == recipe_id)
        created_recipe_row = (await conn.execute(stmt_get_recipe)).fetchone()
        if not created_recipe_row:
            raise Exception("Failed to fetch created recipe after insert.") # Should not happen

        # Populate ingredient details
        ingredient_details = await _populate_recipe_ingredients_details(conn, recipe_id)

        return RecipeRead(
            **created_recipe_row._asdict(), # type: ignore
            ingredients=ingredient_details
        )


async def get_recipe_by_id(recipe_id: int) -> Optional[RecipeRead]:
    """
    Retrieves a single recipe by its ID, including detailed ingredient information.

    Args:
        recipe_id: The ID of the recipe.

    Returns:
        The RecipeRead Pydantic model if found, otherwise None.
    """
    async with engine.connect() as conn:
        stmt_recipe = select(recipes_table).where(recipes_table.c.id == recipe_id)
        recipe_row = (await conn.execute(stmt_recipe)).fetchone()

        if not recipe_row:
            return None

        ingredient_details = await _populate_recipe_ingredients_details(conn, recipe_id)

        return RecipeRead(
            **recipe_row._asdict(), # type: ignore
            ingredients=ingredient_details
        )


async def get_all_recipes(skip: int = 0, limit: int = 100) -> List[RecipeRead]:
    """
    Retrieves a list of recipes with pagination, including detailed ingredient information.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of RecipeRead Pydantic models.
    """
    async with engine.connect() as conn:
        stmt_recipes = select(recipes_table).offset(skip).limit(limit)
        recipes_rows = (await conn.execute(stmt_recipes)).fetchall()

        recipes_list = []
        for recipe_row in recipes_rows:
            recipe_id = recipe_row.id
            ingredient_details = await _populate_recipe_ingredients_details(conn, recipe_id)
            recipes_list.append(RecipeRead(
                 **recipe_row._asdict(), # type: ignore
                ingredients=ingredient_details
            ))
        return recipes_list


async def update_recipe_by_id(recipe_id: int, recipe_data: RecipeUpdate) -> Optional[RecipeRead]:
    """
    Updates an existing recipe. This includes updating its base fields and/or its ingredients.
    If ingredients are provided, existing ones are replaced.

    Args:
        recipe_id: The ID of the recipe to update.
        recipe_data: Pydantic model with fields to update.

    Returns:
        The updated RecipeRead Pydantic model if found and updated, otherwise None.
    """
    async with engine.connect() as conn:
        async with conn.begin(): # Start transaction
            # Check if recipe exists
            recipe_exists_stmt = select(recipes_table.c.id).where(recipes_table.c.id == recipe_id)
            existing_recipe = (await conn.execute(recipe_exists_stmt)).fetchone()
            if not existing_recipe:
                return None

            # Update basic recipe fields if provided
            recipe_update_values = recipe_data.model_dump(exclude_unset=True, exclude={"ingredients"})
            if recipe_update_values:
                stmt_update_recipe = update(recipes_table).where(recipes_table.c.id == recipe_id).values(**recipe_update_values)
                await conn.execute(stmt_update_recipe)

            # Update ingredients if provided in recipe_data
            if recipe_data.ingredients is not None: # Empty list means remove all ingredients
                # Delete existing recipe_ingredients for this recipe
                stmt_delete_ingredients = delete(recipe_ingredients_table).where(recipe_ingredients_table.c.recipe_id == recipe_id)
                await conn.execute(stmt_delete_ingredients)

                # Add new recipe_ingredients
                for ingredient_assoc_data in recipe_data.ingredients:
                    stmt_add_ingredient = insert(recipe_ingredients_table).values(
                        recipe_id=recipe_id,
                        **ingredient_assoc_data.model_dump()
                    )
                    await conn.execute(stmt_add_ingredient)
            # Commit transaction

        # Fetch and return the updated recipe
        return await get_recipe_by_id(recipe_id)


async def delete_recipe_by_id(recipe_id: int) -> Optional[dict]:
    """
    Deletes a recipe and its associated ingredient links.

    Args:
        recipe_id: The ID of the recipe to delete.

    Returns:
        A confirmation dictionary if deletion was successful, otherwise None.
    """
    async with engine.connect() as conn:
        async with conn.begin(): # Start transaction
            # Check if recipe exists
            recipe_exists_stmt = select(recipes_table.c.id).where(recipes_table.c.id == recipe_id)
            existing_recipe = (await conn.execute(recipe_exists_stmt)).fetchone()
            if not existing_recipe:
                return None # Recipe not found

            # Delete associated recipe_ingredients first (due to foreign key constraints)
            stmt_delete_ingredients = delete(recipe_ingredients_table).where(recipe_ingredients_table.c.recipe_id == recipe_id)
            await conn.execute(stmt_delete_ingredients)

            # Delete the recipe itself
            stmt_delete_recipe = delete(recipes_table).where(recipes_table.c.id == recipe_id)
            await conn.execute(stmt_delete_recipe)
            # Commit transaction

        return {"message": f"Recipe with id {recipe_id} and its ingredient associations deleted successfully."}
