from sqlalchemy import select, insert, update, delete, text # Removed left_join
from sqlalchemy.ext.asyncio import AsyncConnection # For type hinting if needed directly
from typing import List, Optional
# sqlalchemy.join can be used if needed, or table.join(..., isouter=True)

from app.db.database import engine
from app.db.schema import packaging_costs as packaging_costs_table
from app.db.schema import recipes as recipes_table # For looking up recipe names
from app.models.packaging_cost_models import PackagingCostCreate, PackagingCostUpdate, PackagingCostRead


async def _map_row_to_packaging_cost_read(row) -> PackagingCostRead:
    """Helper to map a DB row (potentially with joined recipe_name) to PackagingCostRead."""
    if not row:
        return None # Should not happen if called with a valid row

    # Create a dictionary from the row
    packaging_cost_data = dict(row._mapping if hasattr(row, '_mapping') else row.__dict__) # Compatibility for different row types

    # Ensure recipe_name is present if recipe_id is, otherwise it might be missing from dict
    if 'recipe_id' in packaging_cost_data and packaging_cost_data['recipe_id'] is not None:
        if 'recipe_name' not in packaging_cost_data or packaging_cost_data['recipe_name'] is None:
            # This case implies a recipe_id was set but the join didn't occur or recipe_name was null
            # For robustness, could do another lookup, but ideally the query provides it.
            # For now, we assume the query correctly provides recipe_name if recipe_id is not null.
            pass # recipe_name might be None if the joined recipe has no name (should not happen)
    else: # If no recipe_id, ensure recipe_name is not spuriously included
        packaging_cost_data['recipe_name'] = None

    return PackagingCostRead.model_validate(packaging_cost_data)


async def create_packaging_cost(cost_data: PackagingCostCreate) -> PackagingCostRead:
    """
    Creates a new packaging cost item in the database.

    Args:
        cost_data: Pydantic model containing the data for the new item.

    Returns:
        The created packaging cost item, including its database ID and recipe_name if applicable.
    """
    async with engine.connect() as conn:
        stmt = insert(packaging_costs_table).values(**cost_data.model_dump())
        result = await conn.execute(stmt)
        await conn.commit()

        created_id = result.lastrowid
        if created_id is None:
            raise Exception("Failed to retrieve ID for newly created packaging cost.")

        # Fetch the newly created item to return it with recipe_name populated
        return await get_packaging_cost_by_id(created_id) # type: ignore


async def get_packaging_cost_by_id(cost_id: int) -> Optional[PackagingCostRead]:
    """
    Retrieves a packaging cost item by its ID.
    If recipe_id is present, the recipe's name is also fetched.

    Args:
        cost_id: The ID of the packaging cost item.

    Returns:
        The PackagingCostRead Pydantic model if found, otherwise None.
    """
    async with engine.connect() as conn:
        # Select from packaging_costs and optionally join recipes table
        # Use a left join to ensure packaging cost is returned even if recipe_id is null or recipe is deleted
        stmt = select(
            packaging_costs_table, # Select all columns from packaging_costs_table
            recipes_table.c.name.label("recipe_name") # And the recipe name
        ).join( # Use the .join() method
            recipes_table,
            packaging_costs_table.c.recipe_id == recipes_table.c.id,
            isouter=True # This makes it a LEFT OUTER JOIN
        ).where(packaging_costs_table.c.id == cost_id)

        result = await conn.execute(stmt)
        row = result.fetchone()

        if row:
            return await _map_row_to_packaging_cost_read(row)
        return None


async def get_all_packaging_costs(
    skip: int = 0,
    limit: int = 100,
    recipe_id_filter: Optional[int] = None
) -> List[PackagingCostRead]:
    """
    Retrieves a list of packaging cost items with pagination and optional filtering by recipe_id.
    If recipe_id is present for an item, the recipe's name is also fetched.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        recipe_id_filter: Optional recipe ID to filter packaging costs by.

    Returns:
        A list of PackagingCostRead Pydantic models.
    """
    async with engine.connect() as conn:
        stmt = select(
            packaging_costs_table,
            recipes_table.c.name.label("recipe_name")
        ).join( # Use the .join() method
            recipes_table,
            packaging_costs_table.c.recipe_id == recipes_table.c.id,
            isouter=True # This makes it a LEFT OUTER JOIN
        ).offset(skip).limit(limit)

        if recipe_id_filter is not None:
            stmt = stmt.where(packaging_costs_table.c.recipe_id == recipe_id_filter)

        result = await conn.execute(stmt)
        rows = result.fetchall()

        return [await _map_row_to_packaging_cost_read(row) for row in rows if row]


async def update_packaging_cost_by_id(cost_id: int, cost_data: PackagingCostUpdate) -> Optional[PackagingCostRead]:
    """
    Updates an existing packaging cost item by its ID.
    Only fields present in cost_data (and not None) will be updated.

    Args:
        cost_id: The ID of the packaging cost item to update.
        cost_data: Pydantic model containing the fields to update.

    Returns:
        The updated packaging cost item if found and updated, otherwise None.
    """
    async with engine.connect() as conn:
        # Check if item exists (also useful to get current recipe_id if needed for validation)
        existing_item_stmt = select(packaging_costs_table.c.id).where(packaging_costs_table.c.id == cost_id)
        if not (await conn.execute(existing_item_stmt)).fetchone():
            return None

        update_values = cost_data.model_dump(exclude_unset=True)
        if not update_values: # No actual data to update
            return await get_packaging_cost_by_id(cost_id) # Return current state

        stmt = update(packaging_costs_table).where(packaging_costs_table.c.id == cost_id).values(**update_values)
        await conn.execute(stmt)
        await conn.commit()

        return await get_packaging_cost_by_id(cost_id)


async def delete_packaging_cost_by_id(cost_id: int) -> Optional[dict]:
    """
    Deletes a packaging cost item by its ID.

    Args:
        cost_id: The ID of the item to delete.

    Returns:
        A dictionary with a success message if deleted, otherwise None.
    """
    async with engine.connect() as conn:
        # Check if item exists first
        existing_item_stmt = select(packaging_costs_table.c.id).where(packaging_costs_table.c.id == cost_id)
        if not (await conn.execute(existing_item_stmt)).fetchone():
            return None

        stmt = delete(packaging_costs_table).where(packaging_costs_table.c.id == cost_id)
        await conn.execute(stmt)
        await conn.commit()
        return {"message": f"Packaging cost with id {cost_id} deleted successfully."}
