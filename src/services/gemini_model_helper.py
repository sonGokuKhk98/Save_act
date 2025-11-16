from typing import Optional

from fastapi import HTTPException

from src.utils.config import Config

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime via HTTP error
    genai = None  # type: ignore


def _get_gemini_model(allow_pro: bool = True):
    """
    Initialize a Gemini model suitable for agentic enhancement and analysis.

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
                "Unable to initialize any Gemini model. "
                f"Tried: {', '.join(model_names)}. Last error: {last_error}"
            ),
        )

    return model


