import sqlalchemy # For Row and other types if needed, though not directly used for core
from sqlalchemy import select, insert, update, delete, text
from app.db.database import engine
from app.db.schema import ingredients as ingredients_table # Alias to avoid confusion
from app.models.ingredient_models import IngredientCreate, IngredientUpdate, IngredientRead
from typing import List, Optional

async def create_ingredient(ingredient_data: IngredientCreate) -> IngredientRead:
    """
    Creates a new ingredient in the database.

    Args:
        ingredient_data: Pydantic model containing the data for the new ingredient.

    Returns:
        The created ingredient data including its database ID.
    """
    async with engine.connect() as conn:
        stmt = insert(ingredients_table).values(**ingredient_data.model_dump())
        result = await conn.execute(stmt)
        await conn.commit()

        # The result object for an insert typically has lastrowid for SQLite
        created_id = result.lastrowid
        if created_id is None:
            # This case should ideally not happen if insert was successful and table has autoincrement pk
            raise Exception("Failed to retrieve ID for newly created ingredient.")

        # Fetch the newly created ingredient to return it
        return await get_ingredient_by_id(created_id) # type: ignore

async def get_ingredient_by_id(ingredient_id: int) -> Optional[IngredientRead]:
    """
    Retrieves an ingredient by its ID.

    Args:
        ingredient_id: The ID of the ingredient to retrieve.

    Returns:
        The ingredient data if found, otherwise None.
    """
    async with engine.connect() as conn:
        stmt = select(ingredients_table).where(ingredients_table.c.id == ingredient_id)
        result = await conn.execute(stmt)
        row = result.fetchone()
        if row:
            # Manually map row to dict before Pydantic model creation if not using ORM
            # Pydantic's from_orm/from_attributes can handle SQLAlchemy Row objects.
            return IngredientRead.model_validate(row)
        return None

async def get_all_ingredients(skip: int = 0, limit: int = 100) -> List[IngredientRead]:
    """
    Retrieves a list of ingredients with pagination.

    Args:
        skip: Number of records to skip (for pagination).
        limit: Maximum number of records to return.

    Returns:
        A list of ingredients.
    """
    async with engine.connect() as conn:
        stmt = select(ingredients_table).offset(skip).limit(limit)
        result = await conn.execute(stmt)
        rows = result.fetchall()
        return [IngredientRead.model_validate(row) for row in rows]

async def update_ingredient_by_id(ingredient_id: int, ingredient_data: IngredientUpdate) -> Optional[IngredientRead]:
    """
    Updates an existing ingredient by its ID.

    Only fields present in ingredient_data (and not None) will be updated.

    Args:
        ingredient_id: The ID of the ingredient to update.
        ingredient_data: Pydantic model containing the fields to update.

    Returns:
        The updated ingredient data if found and updated, otherwise None.
    """
    async with engine.connect() as conn:
        # Check if ingredient exists first
        existing_ingredient = await get_ingredient_by_id(ingredient_id)
        if not existing_ingredient:
            return None

        # Get data to update, excluding unset fields
        update_data = ingredient_data.model_dump(exclude_unset=True)

        if not update_data: # No actual data to update
            return existing_ingredient # Return current state

        stmt = update(ingredients_table).where(ingredients_table.c.id == ingredient_id).values(**update_data)
        await conn.execute(stmt)
        await conn.commit()

        return await get_ingredient_by_id(ingredient_id)

async def delete_ingredient_by_id(ingredient_id: int) -> Optional[dict]:
    """
    Deletes an ingredient by its ID.

    Args:
        ingredient_id: The ID of the ingredient to delete.

    Returns:
        A dictionary with a success message if deleted, otherwise None.
    """
    async with engine.connect() as conn:
        # Check if ingredient exists first
        existing_ingredient = await get_ingredient_by_id(ingredient_id)
        if not existing_ingredient:
            return None

        stmt = delete(ingredients_table).where(ingredients_table.c.id == ingredient_id)
        await conn.execute(stmt)
        await conn.commit()
        return {"message": f"Ingredient with id {ingredient_id} deleted successfully."}

# Example of how to handle potential None from result.lastrowid for other DBs
# async def create_ingredient_alt(ingredient_data: IngredientCreate) -> IngredientRead:
#     async with engine.connect() as conn:
#         # For databases that don't support RETURNING or lastrowid easily with core,
#         # or if you need to be more explicit.
#         # This often involves a select statement after insert if id is db generated.
#         # For SQLite, lastrowid is fine. For PostgreSQL, RETURNING id is common.
#
#         # Simplified: assuming lastrowid works as it does in aiosqlite
#         query = ingredients_table.insert().values(**ingredient_data.model_dump())
#         result = await conn.execute(query)
#         await conn.commit()
#         new_id = result.lastrowid
#
#         # Fallback if lastrowid is None (should not happen for SQLite PK)
#         if new_id is None:
#             # This might be needed if not an autoincrement PK or different DB
#             # For example, query by a unique field used in ingredient_data
#             # This is a placeholder for more complex logic if needed.
#             # query_select = select(ingredients_table).where(ingredients_table.c.name == ingredient_data.name)
#             # new_ingredient_row = (await conn.execute(query_select)).fetchone()
#             # if not new_ingredient_row:
#             #     raise Exception("Could not retrieve newly created ingredient")
#             # new_id = new_ingredient_row.id
#             raise Exception("Failed to get ID of new ingredient")
#
#         return IngredientRead(id=new_id, **ingredient_data.model_dump())
