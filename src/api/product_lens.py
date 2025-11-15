"""
FastAPI router that integrates with SerpApi's Google Lens engine to
find real product matches for a reel based on its thumbnail/keyframe.

This is used primarily for product reels: the generic view can call
`/api/products/lens/{document_id}` to retrieve visual/product matches and
open real "buy" links for the user.
"""

import os
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.reels import REELS


router = APIRouter(prefix="/api/products", tags=["products"])


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")


def _normalize_visual_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  normalized: List[Dict[str, Any]] = []
  for m in matches or []:
    if not isinstance(m, dict):
      continue
    thumb = m.get("thumbnail") or {}
    if isinstance(thumb, dict):
      thumb = thumb.get("image")
    normalized.append(
      {
        "title": m.get("title"),
        "link": m.get("link"),
        "source": m.get("source"),
        "thumbnail": thumb,
      }
    )
  return normalized


def _normalize_product_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  normalized: List[Dict[str, Any]] = []
  for p in matches or []:
    if not isinstance(p, dict):
      continue
    thumb = p.get("thumbnail") or {}
    if isinstance(thumb, dict):
      thumb = thumb.get("image")
    normalized.append(
      {
        "title": p.get("title"),
        "link": p.get("link"),
        "source": p.get("source"),
        "price": p.get("price"),
        "currency": p.get("currency"),
        "thumbnail": thumb,
      }
    )
  return normalized


class ImageURLRequest(BaseModel):
    image_url: str


@router.get("/lens/{document_id}")
async def product_lens_search(document_id: str):
  """
  Use SerpApi Google Lens to search for visually similar / matching products
  based on the reel's thumbnail image.
  """
  if not SERPAPI_API_KEY:
    raise HTTPException(status_code=500, detail="SERPAPI_API_KEY not configured")

  reel = REELS.get(document_id)
  if not reel:
    raise HTTPException(status_code=404, detail="Unknown document_id")

  image_url = reel.get("thumbnail_url")
  if not image_url:
    raise HTTPException(status_code=400, detail="No thumbnail available for this reel")

  params = {
    "api_key": SERPAPI_API_KEY,
    "engine": "google_lens",
    "url": image_url,
  }

  try:
    resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Error contacting SerpApi: {e}")

  if resp.status_code != 200:
    raise HTTPException(
      status_code=502,
      detail=f"SerpApi error {resp.status_code}: {resp.text[:200]}",
    )

  data = resp.json()

  visual_matches = _normalize_visual_matches(data.get("visual_matches") or [])
  product_matches = _normalize_product_matches(data.get("product_results") or [])

  return {
    "image_url": image_url,
    "visual_matches": visual_matches,
    "product_matches": product_matches,
  }


@router.post("/lens/search-by-url")
async def product_lens_search_by_url(request: ImageURLRequest):
    """
    Use SerpApi Google Lens to search for visually similar / matching products
    based on a direct image URL (for Supermemory keyframes).
    """
    if not SERPAPI_API_KEY:
        raise HTTPException(status_code=500, detail="SERPAPI_API_KEY not configured")

    image_url = request.image_url
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")

    params = {
        "api_key": SERPAPI_API_KEY,
        "engine": "google_lens",
        "url": image_url,
    }

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error contacting SerpApi: {e}")

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"SerpApi error {resp.status_code}: {resp.text[:200]}",
        )

    data = resp.json()

    visual_matches = _normalize_visual_matches(data.get("visual_matches") or [])
    product_matches = _normalize_product_matches(data.get("product_results") or [])

    return {
        "image_url": image_url,
        "visual_matches": visual_matches,
        "product_matches": product_matches,
        "google_lens_url": data.get("search_metadata", {}).get("google_lens_url", "")
    }