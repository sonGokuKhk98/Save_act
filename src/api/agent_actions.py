"""
FastAPI router that exposes lightweight "AI agent" helpers on top of
existing reel extractions.

For now this focuses on product reels: given a document_id, we send the
structured extraction + raw data to Gemini and ask it to propose a
short enhanced summary and suggested actions. The UI can surface this
as an "Enhance with AI" experience.
"""

from typing import Any, Dict, List, Optional
import json
import re
import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from src.api.reels import REELS
from src.services.reel_intelligence_agent import generate_reel_intelligence
from src.services.gemini_model_helper import _get_gemini_model
from src.utils.config import Config


router = APIRouter(prefix="/api/agents", tags=["agents"])


async def _ensure_document_cached(document_id: str) -> Dict[str, Any]:
    """
    Ensure a document is in the REELS cache. If not found, fetch from Supermemory.
    
    Returns the cached reel data.
    Raises HTTPException if document cannot be found or fetched.
    """
    # Check if already cached
    reel = REELS.get(document_id)
    if reel:
        return reel
    
    # Not in cache - try to fetch from Supermemory
    load_dotenv()
    api_key = os.environ.get("SUPERMEMORY_API_KEY")
    
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="Document not in cache and SUPERMEMORY_API_KEY not configured"
        )
    
    # Fetch main document
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
        raise HTTPException(
            status_code=404, 
            detail=f"Document {document_id} not found in cache or Supermemory: {str(e)}"
        )
    
    # Extract customId from main document metadata
    metadata = main_doc.get("metadata", {})
    custom_id = metadata.get("customId")
    
    keyframe_images = []
    # Search for all images with matching customId
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
                    keyframe_doc_id = item.get("documentId")
                    
                    if keyframe_doc_id:
                        try:
                            keyframe_doc_url = f"https://api.supermemory.ai/v3/documents/{keyframe_doc_id}"
                            keyframe_resp = requests.get(keyframe_doc_url, headers=headers, timeout=30)
                            keyframe_resp.raise_for_status()
                            keyframe_doc = keyframe_resp.json()
                            
                            image_url = keyframe_doc.get("url", "")
                            summary = keyframe_doc.get("summary", "")
                            
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
                            
                        except requests.RequestException:
                            continue
                            
        except requests.RequestException:
            pass  # Continue without keyframes
    
    # Parse content JSON to extract structured data
    content_data = {}
    try:
        content_str = main_doc.get("content", "{}")
        if content_str:
            content_data = json.loads(content_str)
    except (json.JSONDecodeError, Exception):
        pass
    
    # Build extraction object similar to regular reel format
    extraction = {
        "title": main_doc.get("title") or metadata.get("title") or metadata.get("topic") or "Untitled",
        "description": main_doc.get("summary", ""),
        "category": metadata.get("category") or content_data.get("category") or "generic",
        "confidence_score": metadata.get("confidence_score") or content_data.get("confidence_score") or 0,
        "source_url": metadata.get("source_url", ""),
        "raw_data": {
            **content_data,
            "_supermemory_id": document_id,
            "_custom_id": custom_id,
            "_keyframes": keyframe_images
        }
    }
    
    # Store in REELS dictionary with document_id as key
    REELS[document_id] = {
        "reel_id": document_id,
        "document_id": document_id,
        "category": extraction["category"],
        "is_generic": True,
        "model_name": "GenericExtraction",
        "extraction": extraction,
        "formatted_summary": None,
        "created_at": datetime.utcnow().isoformat(),
        "source_url": extraction["source_url"],
        "thumbnail_url": keyframe_images[0]["url"] if keyframe_images else metadata.get("thumbnail_url"),
        "errors": [],
        "_from_supermemory": True
    }
    
    return REELS[document_id]


class ProductAction(BaseModel):
    """Single suggested action label + description for the UI."""

    label: str
    description: Optional[str] = None


class ProductEnhancementPlan(BaseModel):
    """
    AI-enhanced summary for a reel plus suggested actions.

    This is intentionally small and UI-friendly so the front-end can
    render it in a simple overlay or sheet.
    """

    heading: str
    subtitle: Optional[str] = None
    bullets: List[str] = []
    suggested_actions: List[ProductAction] = []


class ReconstructionPlan(BaseModel):
    """
    AI-driven reconstruction focused on beautifying the leftover / generic
    context into a *single rich section* for the UI.
    
    Instead of trying to rebuild every structured field, this plan:
      - May propose an improved heading/subtitle
      - Returns one primary rich-text block summarizing and organising the
        messy `additional_context` / fallback data into something highly
        readable and actionable.
    """
    
    heading: Optional[str] = None
    subtitle: Optional[str] = None
    rich_text: str


def _build_system_prompt(category: str) -> str:
    """Return a category-aware system prompt."""
    base = (
        "You are an assistant that reads structured JSON extracted from a short social video.\n"
        "Your job is to summarize what is most useful for the user and propose a few high-impact "
        "actions they can take, WITHOUT hallucinating extra items or prices.\n"
        "The UI will show your output as a small hero section and a list of actions.\n"
    )

    cat = (category or "").lower()
    if cat == "product":
        extra = (
            "The content is about products or shopping. Focus on:\n"
            "- what is on offer (price ranges, promos, bundles),\n"
            "- how to act on it (visit store, capture shopping list, search visually, compare prices).\n"
        )
    elif cat == "recipe":
        extra = (
            "The content is a recipe. Focus on:\n"
            "- what kind of dish and key ingredients,\n"
            "- how it fits into a meal (snack, dinner, dessert),\n"
            "- useful actions like: generate shopping list, start guided cook mode, adapt to dietary needs.\n"
        )
    elif cat == "workout":
        extra = (
            "The content is a workout. Focus on:\n"
            "- workout type and difficulty,\n"
            "- major muscle groups and format (rounds, sets, intervals),\n"
            "- actions like: start guided timer, copy workout plan, adjust duration or sets.\n"
        )
    elif cat == "travel":
        extra = (
            "The content is travel/itinerary. Focus on:\n"
            "- destinations and day ranges,\n"
            "- highlight key activities and experiences,\n"
            "- actions like: copy itinerary, open maps links, estimate days or budget.\n"
        )
    else:
        extra = (
            "The content is generic. Focus on the main topic and any concrete items or steps, "
            "then suggest actions that help the user use or remember this information.\n"
        )

    return base + extra


def _build_user_prompt(extraction: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
    return (
        "Here is the structured extraction JSON for this reel:\n"
        f"{extraction}\n\n"
        "Here is the raw_data JSON (may contain additional context or items):\n"
        f"{raw_data}\n\n"
        "IMPORTANT: Respond with ONLY valid JSON. Ensure all strings are properly escaped.\n"
        "Use \\n for line breaks within strings, and escape any quotes with \\\".\n"
        "\n"
        "Respond strictly as compact JSON with the following shape:\n"
        "{\n"
        '  "heading": "short catchy heading, 3-8 words, no emojis",\n'
        '  "subtitle": "1 short sentence summarizing what matters most for the user",\n'
        '  "bullets": ["3-6 bullet points, each <= 18 words"],\n'
        '  "suggested_actions": [\n'
        '    {"label": "Button label, <= 32 chars", "description": "What this action helps the user do."}\n'
        "  ]\n"
        "}\n"
        "Do not add any extra keys, comments, trailing commas, or explanations outside this JSON object."
    )


def _build_reconstruct_prompt(extraction: Dict[str, Any], raw_data: Dict[str, Any]) -> str:
    """
    Build a prompt that asks Gemini to produce ONE rich, human-friendly section
    that makes the most of leftover / generic / additional_context data.
    """

    return (
        "You are given structured JSON extracted from a short social video.\n"
        "The main schema fields (ingredients, products, steps, etc.) have already been used for the UI.\n"
        "Now we only care about the *leftover context* — especially the `additional_context`\n"
        "and any other descriptive fields that did not fit the main schema.\n"
        "\n"
        "Your job is to create ONE rich, human-friendly section that:\n"
        "- Summarizes the most useful insights from this leftover/generic data.\n"
        "- Groups related ideas into short paragraphs or bullet lists.\n"
        "- Preserves any concrete facts (times, brands, locations) without hallucinating new ones.\n"
        "- Reads like a compact, well-organized explainer for the user.\n"
        "\n"
        "Do NOT try to rebuild all structured fields. Focus on meaningful narrative from the\n"
        "additional_context and any descriptive text fields.\n"
        "\n"
        "Here is the current extraction JSON (for light context):\n"
        f"{extraction}\n\n"
        "Here is the current raw_data JSON (including additional_context):\n"
        f"{raw_data}\n\n"
        "IMPORTANT: Respond with ONLY valid JSON. Ensure all strings are properly escaped.\n"
        "Use \\n for line breaks within strings, and escape any quotes with \\\".\n"
        "\n"
        "Respond strictly as compact JSON with the following shape:\n"
        "{\n"
        '  "heading": "optional improved heading, or null",\n'
        '  "subtitle": "optional improved one-line summary, or null",\n'
        '  "rich_text": "a single rich, multi-paragraph block of text. Use \\n for line breaks. You MAY use simple Markdown like bullet lists but ensure all text is properly escaped for JSON."\n'
        "}\n"
        "Do not add any extra keys, comments, trailing commas, or explanations outside this JSON object.\n"
    )


def _call_gemini_for_plan(
    extraction: Dict[str, Any],
    raw_data: Dict[str, Any],
) -> ProductEnhancementPlan:
    """Shared helper to call Gemini and parse the enhancement plan."""

    category = (extraction.get("category") or "").lower()
    system_prompt = _build_system_prompt(category)
    user_prompt = _build_user_prompt(extraction, raw_data)

    # First try with Pro preference; if we hit a quota error, fall back to
    # flash-only models in the same request.
    try:
        model = _get_gemini_model(allow_pro=True)
        resp = model.generate_content([system_prompt, user_prompt])
    except Exception as exc:  # pragma: no cover - depends on remote API
        msg = str(exc)
        if "ResourceExhausted" in msg or "quota" in msg or "429" in msg:
            # Quota limits on Pro: gracefully fall back to flash models
            model = _get_gemini_model(allow_pro=False)
            resp = model.generate_content([system_prompt, user_prompt])
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini error while generating enhancement plan: {exc}",
            ) from exc

    text = resp.text or ""

    # Try to extract JSON from code blocks first (```json ... ```)
    json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_block_match:
        json_str = json_block_match.group(1)
    else:
        # Fall back to finding raw JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HTTPException(
                status_code=502,
                detail="Gemini did not return a JSON object for the enhancement plan.",
            )
        json_str = match.group(0)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        # Log the problematic JSON for debugging
        print(f"Failed to parse enhancement JSON from Gemini. Raw response:\n{text}")
        print(f"Extracted JSON string:\n{json_str}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse enhancement JSON from Gemini: {exc}",
        ) from exc

    heading = data.get("heading") or "Highlights"
    subtitle = data.get("subtitle")
    bullets = data.get("bullets") or []
    actions_raw = data.get("suggested_actions") or []

    actions: List[ProductAction] = []
    for a in actions_raw:
        if not isinstance(a, dict):
            continue
        label = a.get("label")
        if not label:
            continue
        actions.append(
            ProductAction(
                label=label,
                description=a.get("description"),
            )
        )

    return ProductEnhancementPlan(
        heading=heading,
        subtitle=subtitle,
        bullets=bullets,
        suggested_actions=actions,
    )


@router.get("/product-plan/{document_id}", response_model=ProductEnhancementPlan)
async def product_enhancement_plan(document_id: str) -> ProductEnhancementPlan:
    """
    Backwards-compatible endpoint focused on product reels.

    Prefer using `/api/agents/plan/{document_id}` for new integrations, which
    works for all categories. This endpoint simply checks that the reel
    is a product and then delegates to the generic planner.
    """
    # Ensure document is cached (fetch from Supermemory if needed)
    reel = await _ensure_document_cached(document_id)

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    category = (extraction.get("category") or "").lower()
    if category != "product":
        raise HTTPException(
            status_code=400,
            detail=f"This helper currently supports product reels only (got {category or 'unknown'}).",
        )

    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_plan(extraction, raw_data)


@router.get("/plan/{document_id}", response_model=ProductEnhancementPlan)
async def generic_enhancement_plan(document_id: str) -> ProductEnhancementPlan:
    """
    Category-aware enhancement plan for ANY reel.

    Reads the extraction + raw_data for the given document_id, uses the
    reel's category to guide the system prompt, and returns a concise
    heading, subtitle, highlights and suggested actions.
    """
    # Ensure document is cached (fetch from Supermemory if needed)
    reel = await _ensure_document_cached(document_id)

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_plan(extraction, raw_data)


@router.get("/intelligence-plan/{document_id}", response_model=ProductEnhancementPlan)
async def intelligence_enhancement_plan(document_id: str) -> ProductEnhancementPlan:
    """
    Enhancement plan powered by the multi-agent Reel Intelligence flow.

    This reuses the same compact UI-friendly shape as ProductEnhancementPlan
    so existing front-end code (e.g. `gx-ai-plan-section` in `code.html`)
    can render heading, subtitle, bullets, and suggested actions.
    """
    # Ensure document is cached (fetch from Supermemory if needed)
    reel = await _ensure_document_cached(document_id)

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    raw_data: Dict[str, Any] = extraction.get("raw_data") or extraction

    # Synthesize a main_document + keyframes compatible with the
    # reel_intelligence_agent interface using stored Supermemory data.
    main_document: Dict[str, Any] = {
        "documentId": document_id,
        "title": extraction.get("title") or raw_data.get("title"),
        "summary": extraction.get("description") or raw_data.get("summary"),
        # Pack raw_data as the content payload expected by the agent.
        "content": json.dumps(raw_data),
        "metadata": {
            "source_url": extraction.get("source_url") or raw_data.get("source_url"),
            "extracted_at": reel.get("created_at"),
        },
    }
    keyframe_images: List[Dict[str, Any]] = raw_data.get("_keyframes") or []
    custom_id = raw_data.get("_custom_id") or ""

    # Run the multi-agent intelligence flow.
    intelligence = generate_reel_intelligence(
        document_id=document_id,
        custom_id=custom_id,
        main_document=main_document,
        keyframe_images=keyframe_images,
    )

    ctx: Dict[str, Any] = intelligence.get("reel_context") or {}
    understanding: Dict[str, Any] = intelligence.get("content_understanding") or {}
    type_specific: Dict[str, Any] = intelligence.get("type_specific_intelligence") or {}
    enrichments: Dict[str, Any] = type_specific.get("enrichments") or {}

    # Derive heading/subtitle from intelligence first, then fall back.
    heading = ctx.get("title") or extraction.get("title") or "Highlights"
    subtitle = (
        understanding.get("summary")
        or extraction.get("description")
        or main_document.get("summary")
    )

    bullets: List[str] = []
    topics = understanding.get("topics") or []
    entities = understanding.get("entities") or []
    if topics:
        bullets.append("Topics: " + ", ".join(map(str, topics[:3])))
    if entities:
        bullets.append("Key entities: " + ", ".join(map(str, entities[:3])))

    # Optionally add one bullet from type-specific enrichments if available.
    if enrichments.get("type") == "place_to_visit":
        places = enrichments.get("places") or []
        if places:
            bullets.append("Places to explore: " + ", ".join(map(str, places[:3])))
    elif enrichments.get("type") == "product_review":
        products = enrichments.get("products") or []
        if products:
            bullets.append("Products highlighted: " + ", ".join(map(str, products[:3])))

    # Map suggested actions from content understanding into ProductAction objects.
    # Prefer structured actions from enrichments (which have URLs), fall back to
    # generic suggested_actions from content understanding.
    structured_actions = enrichments.get("actions") or []
    suggested_raw = understanding.get("suggested_actions") or []
    if isinstance(suggested_raw, str):
        suggested_raw = [suggested_raw]

    actions: List[ProductAction] = []
    
    # First, add structured actions with URLs from enrichments
    for action in structured_actions:
        if not isinstance(action, dict):
            continue
        label = action.get("label")
        url = action.get("url")
        if not label:
            continue
        # Store URL in description field so the frontend can access it
        # Format: "URL: <url>" so frontend can detect and extract it
        description = f"URL: {url}" if url else None
        actions.append(
            ProductAction(
                label=str(label),
                description=description,
            )
        )
    
    # Then add generic suggested actions if we don't have enough structured ones
    if len(actions) < 3:
        for label in suggested_raw:
            if not label:
                continue
            actions.append(
                ProductAction(
                    label=str(label),
                    description=None,
                )
            )

    return ProductEnhancementPlan(
        heading=heading,
        subtitle=subtitle,
        bullets=bullets,
        suggested_actions=actions,
    )


def _call_gemini_for_reconstruct(
    extraction: Dict[str, Any],
    raw_data: Dict[str, Any],
) -> ReconstructionPlan:
    """
    Call Gemini to get a rich-text summary of additional_context plus optional
    improved heading/subtitle.
    """

    import json
    import re

    category = (extraction.get("category") or "").lower()
    system_prompt = _build_system_prompt(category)
    user_prompt = _build_reconstruct_prompt(extraction, raw_data)

    try:
        model = _get_gemini_model(allow_pro=True)
        resp = model.generate_content([system_prompt, user_prompt])
    except Exception as exc:  # pragma: no cover
        msg = str(exc)
        if "ResourceExhausted" in msg or "quota" in msg or "429" in msg:
            model = _get_gemini_model(allow_pro=False)
            resp = model.generate_content([system_prompt, user_prompt])
        else:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini error while generating reconstruction plan: {exc}",
            ) from exc

    text = resp.text or ""
    
    # Try to extract JSON from code blocks first (```json ... ```)
    json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_block_match:
        json_str = json_block_match.group(1)
    else:
        # Fall back to finding raw JSON object
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise HTTPException(
                status_code=502,
                detail="Gemini did not return a JSON object for the reconstruction plan.",
            )
        json_str = match.group(0)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        # Log the problematic JSON for debugging
        print(f"Failed to parse JSON from Gemini. Raw response:\n{text}")
        print(f"Extracted JSON string:\n{json_str}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse reconstruction JSON from Gemini: {exc}",
        ) from exc

    heading = data.get("heading")
    subtitle = data.get("subtitle")
    rich_text = data.get("rich_text")

    if not isinstance(rich_text, str) or not rich_text.strip():
        raise HTTPException(
            status_code=502,
            detail="Reconstruction plan rich_text must be a non-empty string.",
        )

    return ReconstructionPlan(
        heading=heading,
        subtitle=subtitle,
        rich_text=rich_text,
    )


@router.get("/reconstruct/{document_id}", response_model=ReconstructionPlan)
async def reconstruct_reel(document_id: str) -> ReconstructionPlan:
    """
    Ask Gemini to produce a cleaned/restructured raw_data for this reel, plus
    optional improved heading/subtitle.

    The frontend can then replace its in-memory raw_data with this object and
    re-render all sections (ingredients/items, details, steps, additional
    context) based on the new structure.
    """
    # Ensure document is cached (fetch from Supermemory if needed)
    reel = await _ensure_document_cached(document_id)

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_reconstruct(extraction, raw_data)


