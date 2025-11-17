"""
Instagram API Client for fetching real-time metrics and data

This module provides integration with Instagram's Graph API to fetch
real-time metrics (likes, views, comments) and other metadata for reels.

Instagram Graph API Documentation:
https://developers.facebook.com/docs/instagram-api/
"""

import os
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv
import re

load_dotenv()


class InstagramAPIClient:
    """Client for interacting with Instagram Graph API"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Instagram API client
        
        Args:
            access_token: Instagram Graph API access token
                         If not provided, will look for INSTAGRAM_ACCESS_TOKEN env var
        """
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.base_url = "https://graph.instagram.com"
        self.graph_api_version = "v18.0"
        
        if not self.access_token:
            print("⚠️  Warning: INSTAGRAM_ACCESS_TOKEN not set. API calls will fail.")
    
    def extract_media_id_from_url(self, instagram_url: str) -> Optional[str]:
        """
        Extract media ID from Instagram URL
        
        Args:
            instagram_url: Instagram reel/post URL
        
        Returns:
            Media shortcode or None if not found
        
        Examples:
            https://www.instagram.com/reel/ABC123/ -> ABC123
            https://www.instagram.com/p/XYZ789/ -> XYZ789
        """
        patterns = [
            r'instagram\.com/reel/([A-Za-z0-9_-]+)',
            r'instagram\.com/p/([A-Za-z0-9_-]+)',
            r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, instagram_url)
            if match:
                return match.group(1)
        
        return None
    
    def get_media_id_from_shortcode(self, shortcode: str) -> Optional[str]:
        """
        Convert Instagram shortcode to media ID using Graph API
        
        Note: This requires a business/creator account and proper permissions
        
        Args:
            shortcode: Instagram media shortcode (e.g., "ABC123")
        
        Returns:
            Media ID or None if not found
        """
        if not self.access_token:
            return None
        
        # This endpoint requires the media to be from your own account
        # For public media, you'll need to use the shortcode directly
        # or use Instagram Basic Display API
        
        return shortcode  # For now, return shortcode as fallback
    
    def get_media_insights(
        self, 
        media_id: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch insights/metrics for a media item
        
        Args:
            media_id: Instagram media ID or shortcode
            metrics: List of metrics to fetch. Defaults to common metrics.
                    Available: impressions, reach, engagement, saved, 
                              video_views, likes, comments, shares
        
        Returns:
            Dictionary with metrics data
        """
        if not self.access_token:
            return {
                "error": "No access token provided",
                "metrics": {}
            }
        
        if metrics is None:
            # Default metrics for reels/videos
            metrics = [
                "impressions",
                "reach", 
                "engagement",
                "saved",
                "video_views",
                "likes",
                "comments",
                "shares"
            ]
        
        url = f"{self.base_url}/{media_id}/insights"
        params = {
            "metric": ",".join(metrics),
            "access_token": self.access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse insights into a cleaner format
            insights = {}
            for item in data.get("data", []):
                metric_name = item.get("name")
                values = item.get("values", [])
                if values:
                    insights[metric_name] = values[0].get("value", 0)
            
            return {
                "success": True,
                "metrics": insights,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "metrics": {}
            }
    
    def get_media_details(self, media_id: str) -> Dict[str, Any]:
        """
        Fetch detailed information about a media item
        
        Args:
            media_id: Instagram media ID or shortcode
        
        Returns:
            Dictionary with media details
        """
        if not self.access_token:
            return {
                "error": "No access token provided"
            }
        
        url = f"{self.base_url}/{media_id}"
        params = {
            "fields": "id,media_type,media_url,permalink,thumbnail_url,"
                     "caption,timestamp,username,like_count,comments_count,"
                     "video_title,is_comment_enabled",
            "access_token": self.access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "data": data,
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def get_media_comments(
        self, 
        media_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch comments for a media item
        
        Args:
            media_id: Instagram media ID
            limit: Maximum number of comments to fetch
        
        Returns:
            Dictionary with comments data
        """
        if not self.access_token:
            return {
                "error": "No access token provided",
                "comments": []
            }
        
        url = f"{self.base_url}/{media_id}/comments"
        params = {
            "fields": "id,text,username,timestamp,like_count",
            "limit": limit,
            "access_token": self.access_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "comments": data.get("data", []),
                "count": len(data.get("data", [])),
                "fetched_at": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "comments": []
            }
    
    def get_comprehensive_media_data(
        self, 
        instagram_url: str
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive data for a media item including details, 
        insights, and comments
        
        Args:
            instagram_url: Instagram reel/post URL
        
        Returns:
            Dictionary with all available data
        """
        # Extract media ID from URL
        shortcode = self.extract_media_id_from_url(instagram_url)
        if not shortcode:
            return {
                "success": False,
                "error": "Could not extract media ID from URL",
                "data": {}
            }
        
        media_id = self.get_media_id_from_shortcode(shortcode)
        
        # Fetch all data
        details = self.get_media_details(media_id)
        insights = self.get_media_insights(media_id)
        comments = self.get_media_comments(media_id)
        
        # Combine into comprehensive object
        result = {
            "success": details.get("success", False),
            "media_id": media_id,
            "shortcode": shortcode,
            "url": instagram_url,
            "details": details.get("data", {}),
            "insights": insights.get("metrics", {}),
            "comments": comments.get("comments", []),
            "comments_count": comments.get("count", 0),
            "fetched_at": datetime.now().isoformat()
        }
        
        # Add error information if any
        errors = []
        if not details.get("success"):
            errors.append(f"Details: {details.get('error')}")
        if not insights.get("success"):
            errors.append(f"Insights: {insights.get('error')}")
        if not comments.get("success"):
            errors.append(f"Comments: {comments.get('error')}")
        
        if errors:
            result["errors"] = errors
        
        return result
    
    def get_fallback_metrics_from_scraping(
        self, 
        instagram_url: str
    ) -> Dict[str, Any]:
        """
        Fallback method to get basic metrics using web scraping
        (when API access is not available)
        
        Note: This is less reliable and may break if Instagram changes their HTML
        
        Args:
            instagram_url: Instagram reel/post URL
        
        Returns:
            Dictionary with scraped metrics
        """
        try:
            # Use yt-dlp to extract metadata (it can handle Instagram)
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(instagram_url, download=False)
                
                return {
                    "success": True,
                    "method": "scraping",
                    "metrics": {
                        "likes": info.get("like_count", 0),
                        "views": info.get("view_count", 0),
                        "comments": info.get("comment_count", 0),
                        "title": info.get("title", ""),
                        "description": info.get("description", ""),
                        "uploader": info.get("uploader", ""),
                        "timestamp": info.get("timestamp"),
                    },
                    "fetched_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Scraping failed: {str(e)}",
                "metrics": {}
            }


# Convenience function for easy import
def fetch_instagram_metrics(instagram_url: str) -> Dict[str, Any]:
    """
    Convenience function to fetch Instagram metrics
    
    Tries API first, falls back to scraping if API is not available
    
    Args:
        instagram_url: Instagram reel/post URL
    
    Returns:
        Dictionary with metrics data
    """
    client = InstagramAPIClient()
    
    # Try API first
    if client.access_token:
        result = client.get_comprehensive_media_data(instagram_url)
        if result.get("success"):
            return result
    
    # Fallback to scraping
    print("ℹ️  API not available, using fallback scraping method...")
    return client.get_fallback_metrics_from_scraping(instagram_url)


if __name__ == "__main__":
    """Test the Instagram API client"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python instagram_api_client.py <instagram_url>")
        print("\nExample:")
        print("  python instagram_api_client.py 'https://www.instagram.com/reel/ABC123/'")
        print("\nNote: Set INSTAGRAM_ACCESS_TOKEN in .env for API access")
        print("      Otherwise, will use fallback scraping method")
        sys.exit(1)
    
    instagram_url = sys.argv[1]
    
    print("="*80)
    print("Instagram API Client - Test")
    print("="*80)
    print(f"\nURL: {instagram_url}\n")
    
    result = fetch_instagram_metrics(instagram_url)
    
    if result.get("success"):
        print("✅ Successfully fetched metrics!\n")
        
        metrics = result.get("metrics", {})
        print("Metrics:")
        for key, value in metrics.items():
            print(f"  - {key}: {value}")
        
        if result.get("details"):
            print("\nDetails:")
            details = result.get("details", {})
            print(f"  - Username: {details.get('username', 'N/A')}")
            print(f"  - Media Type: {details.get('media_type', 'N/A')}")
            print(f"  - Timestamp: {details.get('timestamp', 'N/A')}")
        
        if result.get("comments_count"):
            print(f"\nComments: {result.get('comments_count')} fetched")
    else:
        print("❌ Failed to fetch metrics")
        print(f"Error: {result.get('error')}")

