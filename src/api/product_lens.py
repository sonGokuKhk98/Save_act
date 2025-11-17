"""
FastAPI router that integrates with SerpApi's Google Lens engine to
find real product matches for a reel based on its thumbnail/keyframe.

This is used primarily for product reels: the generic view can call
`/api/products/lens/{document_id}` to retrieve visual/product matches and
open real "buy" links for the user.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.reels import REELS


router = APIRouter(prefix="/api/products", tags=["products"])


SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# Major e-commerce domains to filter for shopping links
SHOPPING_DOMAINS = [
    "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.ca", "amazon.in",
    "ebay.com", "ebay.co.uk", "ebay.de", "ebay.fr", "ebay.ca", "ebay.in",
    "walmart.com", "target.com", "bestbuy.com", "homedepot.com", "lowes.com",
    "etsy.com", "aliexpress.com", "alibaba.com", "shopify.com",
    "wayfair.com", "overstock.com", "newegg.com", "costco.com",
    "macys.com", "nordstrom.com", "zappos.com", "kohls.com",
    "sephora.com", "ulta.com", "nike.com", "adidas.com",
    "flipkart.com", "myntra.com", "ajio.com", "snapdeal.com",
    "shop", "store", "buy"  # Generic shopping keywords in domain
]


def _is_shopping_link(link: str) -> bool:
    """Check if a link is from a shopping website."""
    if not link:
        return False
    link_lower = link.lower()
    return any(domain in link_lower for domain in SHOPPING_DOMAINS)


def _extract_thumbnail_url(thumb_data):
    """Extract thumbnail URL from various possible formats."""
    if not thumb_data:
        return None
    
    # If it's already a string URL, return it
    if isinstance(thumb_data, str):
        return thumb_data
    
    # If it's a dict, try various possible keys
    if isinstance(thumb_data, dict):
        # Try common keys in order of preference
        for key in ['image', 'url', 'src', 'href']:
            if key in thumb_data and isinstance(thumb_data[key], str):
                return thumb_data[key]
    
    return None


def _extract_price_info(item: Dict[str, Any]) -> tuple:
    """Extract price and currency from various possible formats.
    
    Returns:
        tuple: (price_string, currency_string) or (None, None)
    """
    price = item.get("price")
    currency = item.get("currency")
    
    # Handle price as dict (e.g., {"value": "29.99", "currency": "USD"})
    if isinstance(price, dict):
        price_value = price.get("value") or price.get("amount") or price.get("price")
        price_currency = price.get("currency") or currency
        return (str(price_value) if price_value else None, 
                str(price_currency) if price_currency else None)
    
    # Handle extracted_price field (common in SerpAPI)
    if not price and "extracted_price" in item:
        price = item["extracted_price"]
    
    # Convert price to string if it's a number
    if isinstance(price, (int, float)):
        price = str(price)
    
    # Only return string prices
    if isinstance(price, str) and price.strip():
        return (price.strip(), str(currency) if currency else None)
    
    return (None, None)


def _normalize_visual_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  normalized: List[Dict[str, Any]] = []
  for m in matches or []:
    if not isinstance(m, dict):
      continue
    
    # Filter for shopping links only
    link = m.get("link")
    if not _is_shopping_link(link):
      continue
    
    # Extract thumbnail URL properly
    thumb = _extract_thumbnail_url(m.get("thumbnail"))
    
    # Skip if no valid thumbnail
    if not thumb:
      continue
    
    # Extract price and currency properly
    price, currency = _extract_price_info(m)
    
    normalized.append(
      {
        "title": m.get("title"),
        "link": link,
        "source": m.get("source"),
        "thumbnail": thumb,
        "price": price,
        "currency": currency,
      }
    )
  return normalized


def _normalize_product_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  normalized: List[Dict[str, Any]] = []
  for p in matches or []:
    if not isinstance(p, dict):
      continue
    
    # Filter for shopping links only
    link = p.get("link")
    if not _is_shopping_link(link):
      continue
    
    # Extract thumbnail URL properly
    thumb = _extract_thumbnail_url(p.get("thumbnail"))
    
    # Skip if no valid thumbnail
    if not thumb:
      continue
    
    # Extract price and currency properly
    price, currency = _extract_price_info(p)
    
    normalized.append(
      {
        "title": p.get("title"),
        "link": link,
        "source": p.get("source"),
        "price": price,
        "currency": currency,
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


def search_amazon_product(query: str) -> Optional[Dict[str, Any]]:
    """
    Use SerpAPI's Amazon engine to get a concrete product link for a query.
    Returns the first organic result, or None if nothing found.
    """
    if not SERPAPI_API_KEY:
        raise HTTPException(status_code=500, detail="SERPAPI_API_KEY not configured")

    params = {
        "engine": "amazon",
        "api_key": SERPAPI_API_KEY,
        "amazon_domain": "amazon.com",
        "query": query,
    }

    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    for item in data.get("organic_results", []):
        asin = item.get("asin")
        link = item.get("link")
        if link:
            return {
                "asin": asin,
                "link": link,
                "title": item.get("title"),
                "price": item.get("price"),
            }

    return None