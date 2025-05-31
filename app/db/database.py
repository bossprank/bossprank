from sqlalchemy.ext.asyncio import create_async_engine
# Import MetaData from sqlalchemy, not needed if we only use metadata from core
from .core import metadata # Import central metadata
from .schema import ingredients, recipes, recipe_ingredients, packaging_costs # Ensure tables are loaded

DATABASE_URL = "sqlite+aiosqlite:///app/db/recipe_app.db" # Corrected path
engine = create_async_engine(DATABASE_URL, echo=False) # Set echo to False

async def create_db_and_tables():
    """Creates the database and all tables defined in the metadata."""
    # schema.py has already run due to top-level imports, populating core.metadata
    print(f"Tables in metadata (in create_db_and_tables): {metadata.tables.keys()}") # DEBUG
    async with engine.begin() as conn:
        # await conn.run_sync(metadata.drop_all) # Use with caution: drops all tables
        await conn.run_sync(metadata.create_all)
    print("Database and tables created successfully (if they didn't exist).")

# To run this (e.g., from a main script or manually for setup):
if __name__ == "__main__":
    import asyncio
    # The imports at the top of the file should ensure metadata is populated already
    asyncio.run(create_db_and_tables())
