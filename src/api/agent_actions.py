"""
FastAPI router that exposes lightweight "AI agent" helpers on top of
existing reel extractions.

For now this focuses on product reels: given a reel_id, we send the
structured extraction + raw data to Gemini and ask it to propose a
short enhanced summary and suggested actions. The UI can surface this
as an "Enhance with AI" experience.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.reels import REELS
from src.utils.config import Config

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime via HTTP error
    genai = None  # type: ignore


router = APIRouter(prefix="/api/agents", tags=["agents"])


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


def _get_gemini_model(allow_pro: bool = True):
    """
    Initialize a Gemini model suitable for agentic enhancement.

    When allow_pro=True we prefer higher quality (2.5 Pro first).
    When allow_pro=False we skip Pro and fall back to flash variants,
    which have a more generous free-tier rate limit.
    """
    if not Config.GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured on the server.",
        )
    if genai is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "google-generativeai is not installed in this environment. "
                "Install it with: pip install google-generativeai"
            ),
        )

    genai.configure(api_key=Config.GEMINI_API_KEY)

    # Reuse a similar model selection strategy as the main Gemini analyzer,
    # but prefer the higher-quality 2.5 Pro model for this second-layer,
    # low-frequency "agentic enhance" pass. Fall back to flash variants if
    # Pro is unavailable or if we explicitly disable Pro due to quota.
    pro_first = [
        "models/gemini-2.5-pro",
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.0-flash",
    ]
    flash_only = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.0-flash",
    ]
    model_names = pro_first if allow_pro else flash_only
    model = None
    last_error: Optional[Exception] = None
    for name in model_names:
        try:
            candidate = genai.GenerativeModel(name)
            # Simple smoke test – a tiny prompt so we fail fast if unsupported.
            candidate.generate_content("ping")
            model = candidate
            break
        except Exception as exc:  # pragma: no cover - dependent on remote API
            last_error = exc
            continue

    if model is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to initialize any Gemini model for agent actions. "
                f"Tried: {', '.join(model_names)}. Last error: {last_error}"
            ),
        )

    return model


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
        "Respond strictly as compact JSON with the following shape:\n"
        "{\n"
        '  "heading": "short catchy heading, 3-8 words, no emojis",\n'
        '  "subtitle": "1 short sentence summarizing what matters most for the user",\n'
        '  "bullets": ["3-6 bullet points, each <= 18 words"],\n'
        '  "suggested_actions": [\n'
        '    {"label": "Button label, <= 32 chars", "description": "What this action helps the user do."}\n'
        "  ]\n"
        "}\n"
        "Do not add any extra keys, comments, or explanations outside this JSON object."
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
        "Respond strictly as compact JSON with the following shape:\n"
        "{\n"
        '  "heading": "optional improved heading, or null",\n'
        '  "subtitle": "optional improved one-line summary, or null",\n'
        '  "rich_text": "a single rich, multi-paragraph block of text. You MAY use simple Markdown like bullet lists (\"- \") and line breaks, but no HTML and no backticks."\n'
        "}\n"
        "Do not add any extra keys, comments, or explanations outside this JSON object.\n"
    )


def _call_gemini_for_plan(
    extraction: Dict[str, Any],
    raw_data: Dict[str, Any],
) -> ProductEnhancementPlan:
    """Shared helper to call Gemini and parse the enhancement plan."""

    import json
    import re

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

    # Try to locate the JSON object within the model response.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise HTTPException(
            status_code=502,
            detail="Gemini did not return a JSON object for the enhancement plan.",
        )

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
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


@router.get("/product-plan/{reel_id}", response_model=ProductEnhancementPlan)
async def product_enhancement_plan(reel_id: str) -> ProductEnhancementPlan:
    """
    Backwards-compatible endpoint focused on product reels.

    Prefer using `/api/agents/plan/{reel_id}` for new integrations, which
    works for all categories. This endpoint simply checks that the reel
    is a product and then delegates to the generic planner.
    """
    reel: Optional[Dict[str, Any]] = REELS.get(reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Unknown reel_id")

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    category = (extraction.get("category") or "").lower()
    if category != "product":
        raise HTTPException(
            status_code=400,
            detail=f"This helper currently supports product reels only (got {category or 'unknown'}).",
        )

    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_plan(extraction, raw_data)


@router.get("/plan/{reel_id}", response_model=ProductEnhancementPlan)
async def generic_enhancement_plan(reel_id: str) -> ProductEnhancementPlan:
    """
    Category-aware enhancement plan for ANY reel.

    Reads the extraction + raw_data for the given reel_id, uses the
    reel's category to guide the system prompt, and returns a concise
    heading, subtitle, highlights and suggested actions.
    """
    reel: Optional[Dict[str, Any]] = REELS.get(reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Unknown reel_id")

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_plan(extraction, raw_data)


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

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise HTTPException(
            status_code=502,
            detail="Gemini did not return a JSON object for the reconstruction plan.",
        )

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
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


@router.get("/reconstruct/{reel_id}", response_model=ReconstructionPlan)
async def reconstruct_reel(reel_id: str) -> ReconstructionPlan:
    """
    Ask Gemini to produce a cleaned/restructured raw_data for this reel, plus
    optional improved heading/subtitle.

    The frontend can then replace its in-memory raw_data with this object and
    re-render all sections (ingredients/items, details, steps, additional
    context) based on the new structure.
    """
    reel: Optional[Dict[str, Any]] = REELS.get(reel_id)
    if not reel:
        raise HTTPException(status_code=404, detail="Unknown reel_id")

    extraction: Dict[str, Any] = reel.get("extraction") or {}
    raw_data = extraction.get("raw_data") or extraction

    return _call_gemini_for_reconstruct(extraction, raw_data)


