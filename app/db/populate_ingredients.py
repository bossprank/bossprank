import asyncio
from sqlalchemy import select, insert
from app.db.core import metadata # For ensuring tables are created
from app.db.database import engine
from app.db.schema import ingredients

INITIAL_INGREDIENTS_DATA = [
    # General Bakery
    {"name": "All-Purpose Flour", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Bread Flour", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 16000}, # Often 'Cakra Kembar' in ID
    {"name": "Cake Flour", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 17000}, # Often 'Kunci Biru' in ID
    {"name": "Whole Wheat Flour", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 25000},
    {"name": "Granulated Sugar", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 18000},
    {"name": "Powdered Sugar (Icing Sugar)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Brown Sugar (Light/Dark)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 20000},
    {"name": "Eggs (Medium size)", "purchase_quantity": 10, "purchase_unit": "pcs", "purchase_price": 20000},
    {"name": "Unsalted Butter", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 30000},
    {"name": "Salted Butter", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 30000},
    {"name": "Active Dry Yeast", "purchase_quantity": 11, "purchase_unit": "g", "purchase_price": 5000},
    {"name": "Instant Yeast", "purchase_quantity": 11, "purchase_unit": "g", "purchase_price": 6000},
    {"name": "Baking Powder", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 8000},
    {"name": "Baking Soda", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 7000},
    {"name": "Salt (Fine)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 5000},
    {"name": "Whole Milk (UHT)", "purchase_quantity": 1000, "purchase_unit": "ml", "purchase_price": 17000},
    {"name": "Buttermilk", "purchase_quantity": 500, "purchase_unit": "ml", "purchase_price": 15000}, # Or DIY substitute
    {"name": "Vegetable Oil (Soy/Canola)", "purchase_quantity": 1000, "purchase_unit": "ml", "purchase_price": 25000},
    {"name": "Olive Oil (Extra Virgin)", "purchase_quantity": 250, "purchase_unit": "ml", "purchase_price": 50000},
    {"name": "Vanilla Extract", "purchase_quantity": 50, "purchase_unit": "ml", "purchase_price": 20000},
    {"name": "Cocoa Powder (Unsweetened)", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Chocolate Chips (Semi-sweet)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 25000},

    # Indonesian Specialties & Fruits
    {"name": "Rice Flour (Tepung Beras)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 10000},
    {"name": "Glutinous Rice Flour (Tepung Ketan)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 12000},
    {"name": "Tapioca Starch (Tepung Tapioka/Kanji)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 9000},
    {"name": "Sago Flour (Tepung Sagu)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 13000},
    {"name": "Palm Sugar (Gula Merah/Aren)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Cane Sugar (Gula Pasir Lokal)", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 16000}, # Duplicate of Granulated, but can be specific type
    {"name": "Coconut Milk (Santan Kental)", "purchase_quantity": 200, "purchase_unit": "ml", "purchase_price": 5000},
    {"name": "Coconut Milk (Santan Encer)", "purchase_quantity": 1000, "purchase_unit": "ml", "purchase_price": 15000}, # Larger pack or diluted
    {"name": "Coconut Oil (VCO)", "purchase_quantity": 500, "purchase_unit": "ml", "purchase_price": 40000},
    {"name": "Pandan Leaf Extract/Paste", "purchase_quantity": 50, "purchase_unit": "ml", "purchase_price": 10000},
    {"name": "Suji Leaf Extract (for green color)", "purchase_quantity": 50, "purchase_unit": "ml", "purchase_price": 12000}, # often homemade
    {"name": "Pandan Leaves", "purchase_quantity": 10, "purchase_unit": "pcs", "purchase_price": 3000},
    {"name": "Cinnamon Powder (Kayu Manis Bubuk)", "purchase_quantity": 50, "purchase_unit": "g", "purchase_price": 8000},
    {"name": "Nutmeg Powder (Pala Bubuk)", "purchase_quantity": 50, "purchase_unit": "g", "purchase_price": 10000},
    {"name": "Cloves (Cengkeh)", "purchase_quantity": 20, "purchase_unit": "g", "purchase_price": 7000},
    {"name": "Star Anise (Bunga Lawang)", "purchase_quantity": 20, "purchase_unit": "g", "purchase_price": 8000},
    {"name": "Cardamom (Kapulaga)", "purchase_quantity": 20, "purchase_unit": "g", "purchase_price": 10000},
    {"name": "Ginger (Jahe)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 8000},
    {"name": "Turmeric Powder (Kunyit Bubuk)", "purchase_quantity": 50, "purchase_unit": "g", "purchase_price": 6000},
    {"name": "Lemongrass (Sereh)", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 5000},
    {"name": "Galangal (Lengkuas)", "purchase_quantity": 200, "purchase_unit": "g", "purchase_price": 7000},
    {"name": "Kaffir Lime Leaves (Daun Jeruk Purut)", "purchase_quantity": 20, "purchase_unit": "pcs", "purchase_price": 4000}, # approx count
    {"name": "Vanilla Beans", "purchase_quantity": 2, "purchase_unit": "pcs", "purchase_price": 30000},
    {"name": "Banana (Pisang Raja)", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 15000}, # Approx 1 bunch/sisir
    {"name": "Banana (Pisang Ambon)", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 14000},
    {"name": "Apple (Granny Smith)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 20000}, # For fillings
    {"name": "Pineapple (Nanas Madu)", "purchase_quantity": 1, "purchase_unit": "pcs", "purchase_price": 12000},
    {"name": "Mango (Mangga Harum Manis)", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 20000},
    {"name": "Jackfruit (Nangka Matang)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 18000}, # Cleaned
    {"name": "Durian (Monthong type, flesh only)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 100000}, # Placeholder, market price varies
    {"name": "Shredded Coconut (Kelapa Parut Segar)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 8000}, # Fresh for 'santan' or 'unti'
    {"name": "Palm Fruit (Kolang-Kaling)", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 15000}, # Candied or fresh
    {"name": "Agar-Agar Powder (Plain)", "purchase_quantity": 7, "purchase_unit": "g", "purchase_price": 4000}, # Sachet
    {"name": "Jelly Powder (Nutrijell Plain)", "purchase_quantity": 15, "purchase_unit": "g", "purchase_price": 5000}, # Sachet
    {"name": "Food Coloring Red (Rose)", "purchase_quantity": 25, "purchase_unit": "ml", "purchase_price": 5000},
    {"name": "Food Coloring Yellow (Egg)", "purchase_quantity": 25, "purchase_unit": "ml", "purchase_price": 5000},
    {"name": "Food Coloring Green (Pandan)", "purchase_quantity": 25, "purchase_unit": "ml", "purchase_price": 5000},

    # Pizza/Bread Specific
    {"name": "'00' Flour (Pizza Flour)", "purchase_quantity": 1000, "purchase_unit": "g", "purchase_price": 30000},
    {"name": "Semolina Flour", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 20000},
    {"name": "Rye Flour", "purchase_quantity": 500, "purchase_unit": "g", "purchase_price": 22000},
    {"name": "Vital Wheat Gluten", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 30000},

    # Pastries/Cakes
    {"name": "Cream Cheese (Block)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 35000},
    {"name": "Heavy Cream (Whipping Cream Cair, Dairy)", "purchase_quantity": 250, "purchase_unit": "ml", "purchase_price": 20000},
    {"name": "Condensed Milk (Susu Kental Manis)", "purchase_quantity": 370, "purchase_unit": "g", "purchase_price": 10000},
    {"name": "Evaporated Milk", "purchase_quantity": 380, "purchase_unit": "g", "purchase_price": 12000}, # Can
    {"name": "Gelatin Powder", "purchase_quantity": 50, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Almonds (Whole/Sliced)", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 20000},
    {"name": "Walnuts", "purchase_quantity": 100, "purchase_unit": "g", "purchase_price": 25000},
    {"name": "Peanuts (Roasted, Unsalted)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 15000},
    {"name": "Cashews (Raw/Roasted)", "purchase_quantity": 200, "purchase_unit": "g", "purchase_price": 30000},
    {"name": "Desiccated Coconut (Fine)", "purchase_quantity": 250, "purchase_unit": "g", "purchase_price": 12000},
]

async def populate_initial_ingredients():
    """
    Populates the ingredients table with initial data.

    Iterates through `INITIAL_INGREDIENTS_DATA`. For each ingredient, it checks
    if an ingredient with the same name already exists in the database.
    If not, it inserts the new ingredient. This makes the script idempotent.
    """
    async with engine.connect() as conn:
        print("--- Processing all ingredients ---")
        for item_idx, item in enumerate(INITIAL_INGREDIENTS_DATA):
            # Check if ingredient already exists by name
            stmt_select = select(ingredients.c.id).where(ingredients.c.name == item["name"])
            result = await conn.execute(stmt_select)
            existing_ingredient = result.fetchone()

            if existing_ingredient is None:
                try:
                    stmt_insert = insert(ingredients).values(**item)
                    await conn.execute(stmt_insert)
                    print(f"({item_idx+1}/{len(INITIAL_INGREDIENTS_DATA)}) Added: {item['name']}")
                except Exception as e:
                    # This might catch IntegrityError if unique constraint is violated by a race condition (unlikely in this script)
                    print(f"({item_idx+1}/{len(INITIAL_INGREDIENTS_DATA)}) Error inserting new {item['name']}: {type(e).__name__} - {e}")
            else:
                print(f"({item_idx+1}/{len(INITIAL_INGREDIENTS_DATA)}) Exists: {item['name']} (ID: {existing_ingredient[0]})")

        await conn.commit() # Commit all changes (if any inserts or updates happened)

async def run_population_script():
    """
    Ensures database tables are created and then populates ingredients.
    This function is called when the script is run directly.
    """
    # print(f"Engine URL used by populate_ingredients: {engine.url}") # DEBUG removed
    # Re-add table creation to make this script self-sufficient for manual runs
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    print("Database tables ensured/created by populate_ingredients.py.")

    await populate_initial_ingredients()
    print("Finished populating ingredients.")

if __name__ == "__main__":
    print("Running ingredient population script...")
    asyncio.run(run_population_script())
    print("Script finished.")
