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
import os
import requests
from dotenv import load_dotenv

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

class SearchRequest(BaseModel):
    """Request body for searching reels."""
    query: str
    limit: int = 10

class SearchResult(BaseModel):
    """Individual search result."""
    title: str
    thumbnail_url: Optional[str] = None
    reel_id: Optional[str] = None
    document_id: Optional[str] = None  # Explicit document ID field
    score: float

class SearchResponse(BaseModel):
    """Response containing search results."""
    results: list[SearchResult]
    total: int

class DocumentDetailsResponse(BaseModel):
    """Response containing document details with keyframes."""
    document: Dict[str, Any]
    keyframes: list[Dict[str, Any]]
    custom_id: Optional[str] = None

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

@router.post("/search", response_model=SearchResponse)
async def search_reels(payload: SearchRequest):
    """
    Search for reels using Supermemory API based on user query.
    
    Returns a list of matching reels with thumbnails and metadata.
    Filters for text-type results and removes duplicates.
    """
    load_dotenv()
    api_key = os.environ.get("SUPERMEMORY_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="SUPERMEMORY_API_KEY not configured")
    
    url = "https://api.supermemory.ai/v3/search"
    
    search_payload = {
        "q": payload.query,
        "chunkThreshold": 0.5,
        "includeFullDocs": True,
        "limit": payload.limit,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=search_payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract unique results (filter text type and remove duplicates)
        seen_ids = set()
        results = []
        
        for item in data.get("results", []):
            item_type = item.get("type")
            doc_id = item.get("documentId")
            
            # Filter only text type results
            if item_type != "text":
                continue
            
            # Skip duplicates
            if not doc_id or doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            
            # Extract metadata
            metadata = item.get("metadata", {})
            source_url = metadata.get("source_url") or "No source URL available"
            title = item.get("title") or metadata.get("topic") or "Untitled"
            thumbnail_url = metadata.get("thumbnail_url") or metadata.get("image_url")
            custom_id = metadata.get("customId")
            
            # Create search result
            result = SearchResult(
                title=title,
                thumbnail_url=thumbnail_url,
                reel_id=doc_id,
                document_id=doc_id,
                score=item.get("score", 0.0)
            )
            results.append(result)
            
            # Stop if we've reached the limit
            if len(results) >= payload.limit:
                break
        
        return SearchResponse(
            results=results,
            total=len(results)
        )
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/document/{document_id}")
async def get_document_details(document_id: str, custom_id: Optional[str] = None):
    """
    Fetch document details by document ID and optionally retrieve associated keyframes.
    
    This is a two-step process:
    1. Fetch main document details from Supermemory
    2. If customId exists, search for all images with matching customId
    """
    print(f"\n🚀 Starting document fetch for ID: {document_id}")

    load_dotenv()
    api_key = os.environ.get("SUPERMEMORY_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="SUPERMEMORY_API_KEY not configured")
    
    # Step 1: Fetch main document
    document_url = f"https://api.supermemory.ai/v3/documents/{document_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.get(document_url, headers=headers, timeout=30)
        resp.raise_for_status()
        main_doc = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")
    
    # Extract customId from main document metadata if not provided
    if not custom_id:
        metadata = main_doc.get("metadata", {})
        custom_id = metadata.get("customId")
    
    keyframe_images = []
    # Step 2: Search for all images with matching customId
    if custom_id:
        search_url = "https://api.supermemory.ai/v3/search"
        search_payload = {
            "q": "images",
            "chunkThreshold": 0.5,
            "filters": {
                "AND": [
                    {
                        "key": "customId",
                        "value": custom_id,
                        "negate": False
                    }
                ]
            }
        }
        
        try:
            search_resp = requests.post(search_url, json=search_payload, headers=headers, timeout=30)
            search_resp.raise_for_status()
            search_results = search_resp.json()
            
            # Filter only image type results and fetch full document details
            for item in search_results.get("results", []):
                if item.get("type") == "image":
                    # Get the documentId from the search result
                    keyframe_doc_id = item.get("documentId")
                    
                    if keyframe_doc_id:
                        try:
                            # Call Document API for this keyframe
                            keyframe_doc_url = f"https://api.supermemory.ai/v3/documents/{keyframe_doc_id}"
                            keyframe_resp = requests.get(keyframe_doc_url, headers=headers, timeout=30)
                            keyframe_resp.raise_for_status()
                            keyframe_doc = keyframe_resp.json()
                            
                            # Extract URL from chunks
                            image_url = None
                            #chunks = keyframe_doc.get("chunks", [])
                            #if chunks and len(chunks) > 0:
                                # Get content from first chunk (usually contains the image URL)
                            #    image_url = chunks[0].get("content", "")
                            
                            # If no URL in chunks, try content field directly
                            #if not image_url:
                            image_url = keyframe_doc.get("url", "")
                            summary = keyframe_doc.get("summary", "")
                            # Create enhanced keyframe object
                            keyframe_obj = {
                                "documentId": keyframe_doc_id,
                                "url": image_url,
                                "type": "image",
                                "metadata": keyframe_doc.get("metadata", {}),
                                "title": keyframe_doc.get("title", ""),
                                "summary": summary,
                                "timestamp": keyframe_doc.get("metadata", {}).get("extracted_at", ""),
                                "frame_number": keyframe_doc.get("metadata", {}).get("frame_index", "")
                            }
                            
                            keyframe_images.append(keyframe_obj)
                            
                        except requests.RequestException as e:
                            # Log error but continue with other keyframes
                            print(f"Warning: Failed to fetch keyframe document {keyframe_doc_id}: {str(e)}")
                            continue
                            
        except requests.RequestException as e:
            # Log error but don't fail the request
            print(f"Warning: Failed to fetch keyframes: {str(e)}")
    
    print("main_doc:",main_doc)
    print("keyframe_images:",keyframe_images)
    print("custom_id:",custom_id)
    return DocumentDetailsResponse(
        document=main_doc,
        keyframes=keyframe_images,
        custom_id=custom_id
    )
    