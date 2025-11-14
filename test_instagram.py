"""
Test script for Instagram video download and extraction
"""
import sys
from main import ReelExtractor
from src.services.supermemeory_client import SupermemeoryClient
import json
from src.models import GenericExtraction

def test_instagram_video(instagram_url: str):
    """
    Test downloading and extracting data from an Instagram video
    
    Args:
        instagram_url: Instagram reel/video URL
    """
    print("=" * 60)
    print("Testing Instagram Video Download & Extraction")
    print("=" * 60)
    print(f"\n📱 Instagram URL: {instagram_url}\n")
    
    # Create extractor
    extractor = ReelExtractor()
    
    # Extract
    # Skip transcription by default for speed (can be enabled with --transcribe flag)
    import sys
    transcribe = "--transcribe" in sys.argv or "-t" in sys.argv
    
    result = extractor.extract(
        input_source=instagram_url,
        source_type="url",
        preferred_category=None,  # Auto-detect
        extract_keyframes=True,
        extract_audio=True,
        transcribe=transcribe  # Skip by default for speed
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    if result["success"]:
        print(" Extraction successful!")
        print(f" Category: {result['extraction'].category}")
        print(f" Title: {result['extraction'].title}")
        print(f" Description: {result['extraction'].description}")
        print(f" Stored in supermemeory.ai: {result['stored']}")
        
        # Print category-specific details
        extraction = result['extraction']
        
        # Check if it's a GenericExtraction (fallback)
        if isinstance(extraction, GenericExtraction):
            print(f"\n📋 Generic Extraction (formatted view):")
            print(extraction.get_formatted_summary())
        else:
            # Handle specific model types
            if extraction.category == "workout":
                print(f" Workout Details:")
                if hasattr(extraction, 'exercises') and extraction.exercises:
                    print(f"  - Exercises: {len(extraction.exercises)}")
                if hasattr(extraction, 'estimated_duration_minutes') and extraction.estimated_duration_minutes:
                    print(f"  - Duration: {extraction.estimated_duration_minutes} minutes")
                if hasattr(extraction, 'difficulty_level'):
                    print(f"  - Difficulty: {extraction.difficulty_level}")
            elif extraction.category == "recipe":
                print(f"  Recipe Details:")
                if hasattr(extraction, 'ingredients') and extraction.ingredients:
                    print(f"  - Ingredients: {len(extraction.ingredients)}")
                if hasattr(extraction, 'steps') and extraction.steps:
                    print(f"  - Steps: {len(extraction.steps)}")
            elif extraction.category == "travel":
                print(f" Travel Details:")
                if hasattr(extraction, 'destination') and extraction.destination:
                    print(f"  - Destination: {extraction.destination}")
                if hasattr(extraction, 'activities') and extraction.activities:
                    print(f"  - Activities: {len(extraction.activities)}")
            elif extraction.category == "product":
                print(f" Product Details:")
                if hasattr(extraction, 'products') and extraction.products:
                    print(f"  - Products: {len(extraction.products)}")
            elif extraction.category == "educational":
                print(f" Tutorial Details:")
                if hasattr(extraction, 'topic') and extraction.topic:
                    print(f"  - Topic: {extraction.topic}")
                if hasattr(extraction, 'steps') and extraction.steps:
                    print(f"  - Steps: {len(extraction.steps)}")
            elif extraction.category == "music":
                print(f" Music Details:")
                if hasattr(extraction, 'song_title') and extraction.song_title:
                    print(f"  - Song: {extraction.song_title}")
                if hasattr(extraction, 'artist') and extraction.artist:
                    print(f"  - Artist: {extraction.artist}")
        
        # Print full extraction data
        print(f" Full Extraction Data:")
        print(extraction.model_dump_json(indent=2))

        if result["errors"]:
            print("  Warnings:")
            for error in result["errors"]:
                print(f"  - {error}")
    else:
        print(" Extraction failed!")
        for error in result["errors"]:
            print(f"  - {error}")
    
    return result["success"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_instagram.py <instagram_url> [--transcribe]")
        print("\nExample:")
        print("  python test_instagram.py 'https://www.instagram.com/reel/ABC123/'")
        print("  python test_instagram.py 'URL' --transcribe  # Enable transcription (slower)")
        print("\nNote: Transcription is disabled by default for speed.")
        print("      Gemini Flash can analyze videos well without audio transcript.")
        sys.exit(1)
    
    instagram_url = sys.argv[1]
    success = test_instagram_video(instagram_url)
    storage = SupermemeoryClient()
    sys.exit(0 if success else 1)

