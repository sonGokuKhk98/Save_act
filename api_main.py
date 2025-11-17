"""
FastAPI entrypoint for the Reel Extraction API and HTML UI pages.

Run with:

    uvicorn api_main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.api import reels as reels_api
from src.api import product_lens as product_lens_api
from src.api import agent_actions as agent_actions_api


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(title="Reel Extraction API")

app.include_router(reels_api.router)
app.include_router(product_lens_api.router)
app.include_router(agent_actions_api.router)

# Serve temp_storage contents (e.g., keyframes) under /temp so we can
# expose thumbnails for features like Google Lens product search.
from src.utils.config import Config  # local import to avoid circulars at top-level

app.mount(
    "/temp",
    StaticFiles(directory=str(Config.TEMP_STORAGE_PATH)),
    name="temp",
)


def _load_html(relative_path: str) -> str:
    """Utility to load an HTML file from the repo."""
    html_path = BASE_DIR / relative_path
    return html_path.read_text(encoding="utf-8")


@app.get("/reel-input", response_class=HTMLResponse)
async def reel_input_page() -> HTMLResponse:
    """Landing page where the user pastes an Instagram reel link."""
    return HTMLResponse(
        _load_html("src/models/UI elements/reel_input/code.html")
    )


@app.get("/browse-reels", response_class=HTMLResponse)
async def browse_reels_page() -> HTMLResponse:
    """Browse previously saved reels, organized by category."""
    return HTMLResponse(
        _load_html("src/models/UI elements/browse_reels/code.html")
    )

@app.get("/processing-status", response_class=HTMLResponse)
async def processing_status_page() -> HTMLResponse:
    """Processing screen that polls task status."""
    return HTMLResponse(
        _load_html("src/models/UI elements/processing_status/code.html")
    )

@app.get("/generic-view", response_class=HTMLResponse)
async def generic_view_page() -> HTMLResponse:
    return HTMLResponse(
        _load_html("src/code.html") 
    )

@app.get("/extracted-view", response_class=HTMLResponse)
async def extracted_view_page() -> HTMLResponse:
    """
    Structured extraction detail page.

    For now this uses the first extracted_data_display variant.
    """
    return HTMLResponse(
        _load_html("src/models/UI elements/extracted_data_display_1/code.html")
    )
