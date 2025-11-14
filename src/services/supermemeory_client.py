"""
Supermemeory.ai integration service
"""
from typing import Dict, Any, Optional, Tuple
from src.utils.config import Config
from src.models.base import BaseExtraction

try:
    from supermemory import Supermemory
    SUPERMEMORY_AVAILABLE = True
except ImportError:
    SUPERMEMORY_AVAILABLE = False
    import httpx


class SupermemeoryClient:
    """
    Client to interact with supermemeory.ai API.
    
    Stores extracted data in supermemeory.ai.
    Uses the supermemory Python package if available, otherwise falls back to HTTP.
    """
    
    def __init__(self):
        """Initialize the supermemeory client"""
        if not Config.SUPERMEMEORY_API_KEY:
            raise ValueError("SUPERMEMEORY_API_KEY is required in .env file")
        
        self.api_key = Config.SUPERMEMEORY_API_KEY
        self.base_url = Config.SUPERMEMEORY_BASE_URL.rstrip('/')
        self.timeout = 30.0
        
        # Use supermemory package if available
        if SUPERMEMORY_AVAILABLE:
            self.client = Supermemory(
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.use_package = True
        else:
            self.use_package = False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def store_extraction(
        self, 
        extraction: BaseExtraction,
        source_url: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Store extracted data in supermemeory.ai.
        
        Args:
            extraction: Extracted data model instance
            source_url: Original video URL (optional)
        
        Returns:
            Tuple of (response dict, error_message)
        """
        try:
            # Prepare payload
            import json
            payload = {
                #"title": extraction.title,
                "content": json.dumps(extraction.model_dump(mode="json")),
                "container_tag": extraction.category,
                #"container_tags": self._generate_tags(extraction),
                "metadata": {
                    "topic": extraction.title,
                    "source_url": source_url or extraction.source_url,
                    "extracted_at": extraction.extracted_at.isoformat(),
                    "confidence_score": extraction.confidence_score,
                    #"word_count": len(extraction.model_dump().split())
                }
            }

            # Use supermemory package if available
            if self.use_package:
                try:
                    # Use the supermemory package API
                    # Note: The exact API may vary, adjust based on package documentation
                    result = self.client.memories.add(**payload)
                    return result.model_dump() if hasattr(result, 'model_dump') else result, None
                except Exception as e:
                    return None, f"Supermemory package error: {str(e)}"
            else:
                # Fallback to HTTP
                import httpx
                url = f"{self.base_url}/v1/memories"
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        url,
                        headers=self._get_headers(),
                        json=payload
                    )
                    response.raise_for_status()
                    return response.json(), None
                
        except Exception as e:
            return None, f"Error storing extraction: {str(e)}"
    

    def store_extraction1(
        self, 
        extraction: BaseExtraction,
        source_url: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Store extracted data in supermemeory.ai.
        
        Args:
            extraction: Extracted data model instance
            source_url: Original video URL (optional)
        
        Returns:
            Tuple of (response dict, error_message)
        """
        try:
            # Prepare payload
            import json
            payload = {
                #"title": extraction.title,
                "content": json.dumps(extraction.model_dump(mode="json")),
                "container_tag": extraction.category,
                #"container_tags": self._generate_tags(extraction),
                "metadata": {
                    "topic": extraction.title,
                    "source_url": source_url or extraction.source_url,
                    "extracted_at": extraction.extracted_at.isoformat(),
                    "confidence_score": extraction.confidence_score,
                    #"word_count": len(extraction.model_dump().split())
                }
            }

            import httpx
            url = f"{self.base_url}/v3/documents"
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                return response.json(), None
                
        except Exception as e:
            return None, f"Error storing extraction: {str(e)}"


    def _generate_tags(self, extraction: BaseExtraction) -> list[str]:
        """
        Generate tags based on extraction category and content.
        
        Args:
            extraction: Extracted data model instance
        
        Returns:
            List of tags
        """
        tags = [extraction.category]
        
        # Add category-specific tags
        if extraction.category == "workout":
            if hasattr(extraction, "difficulty_level"):
                tags.append(extraction.difficulty_level)
        elif extraction.category == "recipe":
            if hasattr(extraction, "cuisine_type") and extraction.cuisine_type:
                tags.append(extraction.cuisine_type.lower())
        elif extraction.category == "travel":
            if hasattr(extraction, "destination"):
                tags.append("travel")
        elif extraction.category == "product":
            tags.append("shopping")
        elif extraction.category == "educational":
            tags.append("tutorial")
        elif extraction.category == "music":
            if hasattr(extraction, "genre") and extraction.genre:
                tags.append(extraction.genre.lower())
        
        return tags
    
    def search_memories(
        self, 
        query: str,
        limit: int = 10
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Search memories in supermemeory.ai.
        
        Args:
            query: Search query
            limit: Maximum number of results
        
        Returns:
            Tuple of (response dict, error_message)
        """
        try:
            # Use supermemory package if available
            if self.use_package:
                try:
                    # Use the supermemory package API
                    result = self.client.search.execute(q=query)
                    return result.model_dump() if hasattr(result, 'model_dump') else result, None
                except Exception as e:
                    return None, f"Supermemory package error: {str(e)}"
            else:
                # Fallback to HTTP
                import httpx
                url = f"{self.base_url}/v1/search"
                
                payload = {
                    "q": query,
                    "limit": limit
                }
                
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        url,
                        headers=self._get_headers(),
                        json=payload
                    )
                    response.raise_for_status()
                    return response.json(), None
                
        except Exception as e:
            return None, f"Error searching memories: {str(e)}"

