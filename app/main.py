from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.db.database import create_db_and_tables # Import the function
import asyncio # For running async function on startup

app = FastAPI() # Create app instance first

# Startup event to create database tables
@app.on_event("startup")
async def startup_event():
    print("INFO:     Running create_db_and_tables on application startup...")
    # Need to ensure this is awaited correctly if it's an async function
    # create_db_and_tables is async, so await it.
    await create_db_and_tables()
    print("INFO:     create_db_and_tables finished.")
    # Note: Populating ingredients on every startup might be too much,
    # that should be a separate, deliberate script run.

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Import the ingredients router
from app.routers import ingredients_router
from app.routers import recipes_router
from app.routers import packaging_costs_router # Import packaging costs router

# Include the ingredients router in the app
app.include_router(ingredients_router.router)
app.include_router(recipes_router.router)
app.include_router(packaging_costs_router.router) # Include packaging_costs router


@app.get("/")
async def read_index(request: Request):
    """Serves the main index page."""
    return templates.TemplateResponse("index.html", {"request": request})
