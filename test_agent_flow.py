"""
Test script for the Reel Intelligence Agent Flow

This script tests the agent flow with sample data to verify the installation
and configuration are correct.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPERMEMORY_API_KEY = os.getenv("SUPERMEMORY_API_KEY")

print("="*80)
print("Reel Intelligence Agent Flow - Test Script")
print("="*80)
print()

# Check API keys
print("1. Checking API Keys...")
if GEMINI_API_KEY:
    print("   ✅ GEMINI_API_KEY is set")
else:
    print("   ❌ GEMINI_API_KEY is not set")
    print("   Please add it to your .env file")

if SUPERMEMORY_API_KEY:
    print("   ✅ SUPERMEMORY_API_KEY is set")
else:
    print("   ❌ SUPERMEMORY_API_KEY is not set")
    print("   Please add it to your .env file")

print()

# Check dependencies
print("2. Checking Dependencies...")
try:
    import langgraph
    print("   ✅ langgraph installed")
except ImportError:
    print("   ❌ langgraph not installed")
    print("   Run: pip install langgraph")

try:
    import langchain
    print("   ✅ langchain installed")
except ImportError:
    print("   ❌ langchain not installed")
    print("   Run: pip install langchain")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("   ✅ langchain-google-genai installed")
except ImportError:
    print("   ❌ langchain-google-genai not installed")
    print("   Run: pip install langchain-google-genai")

try:
    import streamlit
    print("   ✅ streamlit installed")
except ImportError:
    print("   ❌ streamlit not installed")
    print("   Run: pip install streamlit")

print()

# Test agent flow import
print("3. Testing Agent Flow Import...")
try:
    from src.services.reel_intelligence_agent import (
        generate_reel_intelligence,
        create_reel_intelligence_graph
    )
    print("   ✅ Agent flow module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import agent flow: {str(e)}")
    exit(1)

print()

# Create sample test data
print("4. Creating Sample Test Data...")

sample_main_document = {
    "documentId": "test_doc_123",
    "content": json.dumps({
        "title": "Amazing Morning Workout Routine",
        "category": "workout",
        "confidence_score": 0.95,
        "transcript": "Hey everyone! Today I'm going to show you my favorite morning workout routine. "
                     "It's perfect for beginners and takes only 15 minutes. "
                     "We'll start with some stretching, then move to bodyweight exercises.",
        "description": "Quick 15-minute morning workout routine for beginners. "
                      "No equipment needed! #workout #fitness #morningroutine",
        "hashtags": ["workout", "fitness", "morningroutine", "exercise", "health"],
        "mentions": ["@fitnessguru"],
        "likes": 2500,
        "views": 15000,
        "comments_count": 120,
        "details": {
            "exercises": [
                "Jumping Jacks - 30 seconds",
                "Push-ups - 10 reps",
                "Squats - 15 reps",
                "Plank - 30 seconds",
                "Lunges - 10 reps each leg"
            ],
            "duration": "15 minutes",
            "difficulty_level": "beginner",
            "equipment_needed": "none"
        }
    }),
    "metadata": {
        "source_url": "https://instagram.com/p/test123",
        "extracted_at": datetime.now().isoformat(),
        "customId": "extraction_test123"
    }
}

sample_keyframes = [
    {
        "documentId": "kf_test_1",
        "type": "image",
        "metadata": {
            "frame_index": 0,
            "category": "workout",
            "topic": "Morning Workout",
            "customId": "extraction_test123"
        }
    },
    {
        "documentId": "kf_test_2",
        "type": "image",
        "metadata": {
            "frame_index": 2,
            "category": "workout",
            "topic": "Morning Workout",
            "customId": "extraction_test123"
        }
    }
]

print("   ✅ Sample data created")
print()

# Test agent flow execution
print("5. Testing Agent Flow Execution...")
print("   This will make API calls to Gemini (if API key is set)")
print()

if not GEMINI_API_KEY:
    print("   ⚠️  Skipping agent flow test (no Gemini API key)")
    print("   Set GEMINI_API_KEY in .env to test the full flow")
else:
    try:
        print("   Running agent flow...")
        result = generate_reel_intelligence(
            document_id="test_doc_123",
            custom_id="extraction_test123",
            main_document=sample_main_document,
            keyframe_images=sample_keyframes
        )
        
        print()
        print("   ✅ Agent flow completed successfully!")
        print()
        print("   Results Summary:")
        print(f"   - Trust Score: {result.get('trust_assessment', {}).get('score', 'N/A')}/100")
        print(f"   - Trust Badge: {result.get('trust_assessment', {}).get('badge', 'N/A')}")
        print(f"   - Content Type: {result.get('content_understanding', {}).get('content_type', 'N/A')}")
        print(f"   - Sentiment: {result.get('content_understanding', {}).get('sentiment', 'N/A')}")
        
        type_specific = result.get('type_specific_intelligence', {})
        enrichments = type_specific.get('enrichments', {})
        if enrichments:
            print(f"   - Enrichment Type: {enrichments.get('type', 'N/A')}")
            action_items = enrichments.get('action_items', [])
            if action_items:
                print(f"   - Action Items: {len(action_items)}")
        
        print()
        print("   Full result saved to: test_agent_flow_result.json")
        with open("test_agent_flow_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
    except Exception as e:
        print(f"   ❌ Agent flow failed: {str(e)}")
        import traceback
        traceback.print_exc()

print()
print("="*80)
print("Test Complete!")
print("="*80)
print()
print("Next Steps:")
print("1. If any checks failed, install missing dependencies")
print("2. Set up your API keys in .env file")
print("3. Run the Streamlit app: streamlit run streamlit_search.py")
print("4. Search for reels and click 'Generate Agentic Flow'")
print()

