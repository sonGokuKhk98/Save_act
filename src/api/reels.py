"""
FastAPI router providing endpoints for reel submission, status polling,
and retrieval of extracted reel data.

This wraps the existing `ReelExtractor` pipeline so the UI can interact
with it over HTTP instead of via the CLI.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from main import ReelExtractor
from src.models import GenericExtraction
from src.utils.config import Config


router = APIRouter(prefix="/api/reels", tags=["reels"])


# NOTE: These are simple in-memory stores intended for local/dev usage.
# In production you would replace these with Redis, a database, or
# another persistent task/result store.
TASKS: Dict[str, Dict[str, Any]] = {}
REELS: Dict[str, Dict[str, Any]] = {}


class SubmitRequest(BaseModel):
    """Request body for submitting a new reel for processing."""

    instagram_url: str


class SubmitResponse(BaseModel):
    """Response returned immediately after a reel is submitted."""

    task_id: str
    status: str
    eta_seconds: int = 120


class StatusResponse(BaseModel):
    """Status for a given task id."""

    task_id: str
    status: str  # queued | processing | completed | failed
    progress: int  # 0–100
    stage: str  # queued|downloading|segmenting|analyzing|storing|done|error
    reel_id: Optional[str] = None
    error: Optional[str] = None


def _update_task(task_id: str, **fields: Any) -> None:
    """Helper to update a task record if it exists."""
    if task_id in TASKS:
        TASKS[task_id].update(fields)


@router.post("/submit", response_model=SubmitResponse)
async def submit_reel(payload: SubmitRequest, background_tasks: BackgroundTasks):
    """
    Submit a new reel URL for processing.

    Returns a task_id that can be used to poll `/api/reels/status/{task_id}`.
    """
    task_id = str(uuid4())
    TASKS[task_id] = {
        "status": "queued",
        "progress": 0,
        "stage": "queued",
        "reel_id": None,
        "error": None,
    }

    def run_extraction(task_id: str, url: str) -> None:
        """Background task that runs the existing ReelExtractor pipeline."""
        _update_task(task_id, status="processing", stage="downloading", progress=10)

        extractor = ReelExtractor()

        def progress_callback(stage: str, progress: int) -> None:
            _update_task(task_id, stage=stage, progress=progress)

        # Re-use the CLI pipeline, but tell it this is a URL and skip audio/transcription
        result = extractor.extract(
            input_source=url,
            source_type="url",
            preferred_category=None,
            extract_keyframes=True,
            extract_audio=False,
            transcribe=False,
            progress_callback=progress_callback,
        )

        if not result["success"]:
            _update_task(
                task_id,
                status="failed",
                stage="error",
                progress=100,
                error="; ".join(result["errors"]),
            )
            return

        extraction = result["extraction"]
        reel_id = str(uuid4())

        is_generic = isinstance(extraction, GenericExtraction)

        # Convert thumbnail_path (if available) into a URL under the /temp mount
        thumbnail_url: Optional[str] = None
        thumb_path_str = result.get("thumbnail_path")
        if thumb_path_str:
            try:
                thumb_path = Path(thumb_path_str)
                # Derive path relative to TEMP_STORAGE_PATH to form the URL
                rel_path = thumb_path.relative_to(Config.TEMP_STORAGE_PATH)
                thumbnail_url = f"/temp/{rel_path.as_posix()}"
            except Exception:
                thumbnail_url = None

        REELS[reel_id] = {
            "reel_id": reel_id,
            "category": extraction.category,
            "is_generic": is_generic,
            "model_name": type(extraction).__name__,
            "extraction": extraction.model_dump(),
            "formatted_summary": extraction.get_formatted_summary() if is_generic else None,
            "created_at": datetime.utcnow().isoformat(),
            "source_url": getattr(extraction, "source_url", None),
            "thumbnail_url": thumbnail_url,
            "errors": result["errors"],
        }

        _update_task(task_id, status="completed", stage="done", progress=100, reel_id=reel_id)

    background_tasks.add_task(run_extraction, task_id, payload.instagram_url)

    return SubmitResponse(task_id=task_id, status="queued", eta_seconds=120)


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(task_id: str):
    """
    Check the status of a previously submitted reel.

    Used by the Processing Status UI to drive progress updates.
    """
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Unknown task_id")
    return StatusResponse(task_id=task_id, **task)


@router.get("/{reel_id}")
async def get_reel(reel_id: str):
    """
    Retrieve the extracted data for a completed reel.

    The response includes whether the extraction was generic and the
    model name used, so the UI can choose the correct detail view.
    """
    reel = REELS.get(reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Unknown reel_id")
    return reel


