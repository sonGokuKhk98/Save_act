# Reel Intelligence Agent Flow

## Overview

The Reel Intelligence Agent Flow is a multi-agent system built with LangGraph that processes Instagram reel data to generate comprehensive intelligence including trust scores, enriched metadata, and type-specific insights.

## Architecture

```
User clicks a reel result
        │
        ▼
[0] Reel Context Builder Agent
    - Fetch metrics, comments, transcript, frames, cache
        │
        ▼
[1] Gemini Content Understanding Agent
    - Type, entities, summary
        │
        ▼
[2] Trust Score Agent
    - Uses metrics + comments + Gemini to compute trust_score
        │
        ▼
[3] Type-specific Agent(s)
    - place_to_visit → Place Enrichment (Maps)
    - product_review → Product Enrichment (shopping links)
    - recipe → Recipe Agent
    - workout → Workout Agent
        │
        ▼
[4] Orchestrator merges everything into Reel Intelligence Object
        │
        ▼
Frontend renders: trust badge + links + structured info for this one reel
```

## Agent Details

### Agent 0: Reel Context Builder
**Purpose:** Builds comprehensive context from the reel document

**Inputs:**
- Main document data
- Keyframe images
- Document ID and Custom ID

**Outputs:**
- Structured reel context with:
  - Title, category, source URL
  - Transcript and description
  - Hashtags and mentions
  - Metrics (likes, views, comments)
  - Keyframe information

### Agent 1: Gemini Content Understanding
**Purpose:** Uses Gemini AI to understand content deeply

**Inputs:**
- Reel context from Agent 0

**Outputs:**
- Content type classification
- Key entities (people, places, products, brands)
- Main topics/themes
- Brief summary
- Sentiment analysis

**LLM:** Google Gemini 2.0 Flash Exp

### Agent 2: Trust Score Calculator
**Purpose:** Calculates trust score based on multiple factors

**Inputs:**
- Reel context
- Content understanding from Agent 1

**Factors Considered:**
1. Engagement rate (likes/views ratio)
2. Content completeness (transcript, description, etc.)
3. Sentiment alignment
4. Confidence score from extraction
5. Number of keyframes

**Outputs:**
- Trust score (0-100)
- Reasoning for the score
- Trust badge (🟢 Highly Trusted, 🟡 Moderately Trusted, 🟠 Needs Verification, 🔴 Low Trust)

### Agent 3: Type-Specific Enrichment
**Purpose:** Applies specialized processing based on content type

**Content Types & Enrichments:**

#### Travel/Place to Visit
- Extracts places mentioned
- Generates Google Maps search suggestions
- Action items: Get directions, Check reviews, Save to travel list

#### Product Review
- Identifies products and brands
- Generates shopping search links
- Action items: Compare prices, Read more reviews, Add to wishlist

#### Recipe
- Extracts ingredients and steps
- Action items: Save recipe, Create shopping list, Set cooking reminder

#### Workout
- Lists exercises
- Extracts duration and difficulty
- Action items: Add to workout plan, Track progress, Set reminder

#### General Content
- Extracts topics
- Basic action items: Save for later, Share with friends

### Agent 4: Orchestrator
**Purpose:** Assembles final Reel Intelligence Object

**Inputs:**
- All previous agent outputs

**Outputs:**
- Complete Reel Intelligence Object with:
  - Metadata (IDs, timestamps, version)
  - Reel context
  - Content understanding
  - Trust assessment
  - Type-specific intelligence
  - Keyframes information
  - Processing info (errors, messages)

## Usage

### From Streamlit UI

1. Search for reels using the search interface
2. Click "View Details" on any result
3. Click "🤖 Generate Agentic Flow" button
4. Wait for the multi-agent system to process
5. View the comprehensive Reel Intelligence output

### Programmatically

```python
from src.services.reel_intelligence_agent import generate_reel_intelligence

# Prepare inputs
document_id = "doc_123"
custom_id = "extraction_abc123"
main_document = {...}  # Document data from API
keyframe_images = [...]  # List of keyframe documents

# Generate intelligence
reel_intelligence = generate_reel_intelligence(
    document_id=document_id,
    custom_id=custom_id,
    main_document=main_document,
    keyframe_images=keyframe_images
)

# Access results
trust_score = reel_intelligence["trust_assessment"]["score"]
content_type = reel_intelligence["content_understanding"]["content_type"]
enrichments = reel_intelligence["type_specific_intelligence"]["enrichments"]
```

## State Management

The agent flow uses a shared state object (`ReelIntelligenceState`) that flows through all agents:

```python
class ReelIntelligenceState(TypedDict):
    # Input data
    document_id: str
    custom_id: str
    main_document: Dict[str, Any]
    keyframe_images: List[Dict[str, Any]]
    
    # Agent outputs
    reel_context: Optional[Dict[str, Any]]
    content_understanding: Optional[Dict[str, Any]]
    trust_score: Optional[float]
    trust_reasoning: Optional[str]
    type_specific_data: Optional[Dict[str, Any]]
    
    # Final output
    reel_intelligence: Optional[Dict[str, Any]]
    
    # Messages and errors
    messages: List[BaseMessage]
    errors: List[str]
```

## Output Format

### Reel Intelligence Object

```json
{
  "metadata": {
    "document_id": "doc_123",
    "custom_id": "extraction_abc123",
    "generated_at": "2024-01-15T10:30:00",
    "agent_version": "1.0.0"
  },
  "reel_context": {
    "title": "Amazing Workout Routine",
    "category": "workout",
    "source_url": "https://instagram.com/...",
    "metrics": {
      "likes": 1500,
      "views": 10000,
      "comments_count": 50
    },
    "keyframes_count": 5
  },
  "content_understanding": {
    "content_type": "workout",
    "entities": ["gym", "dumbbells", "trainer"],
    "topics": ["fitness", "strength training"],
    "summary": "A comprehensive workout routine...",
    "sentiment": "positive"
  },
  "trust_assessment": {
    "score": 85.5,
    "reasoning": "High engagement rate and complete content...",
    "badge": "🟢 Highly Trusted"
  },
  "type_specific_intelligence": {
    "content_type": "workout",
    "enrichments": {
      "type": "workout",
      "exercises": ["push-ups", "squats", "lunges"],
      "duration": "30 minutes",
      "difficulty": "intermediate",
      "action_items": [
        "Add to workout plan",
        "Track progress",
        "Set reminder"
      ]
    }
  },
  "keyframes": {
    "count": 5,
    "ids": ["kf_1", "kf_2", "kf_3", "kf_4", "kf_5"]
  }
}
```

## Dependencies

- **LangGraph**: Agent orchestration framework
- **LangChain**: LLM integration and chains
- **Google Gemini**: Content understanding and analysis
- **Python 3.9+**: Runtime environment

## Configuration

Set the following environment variables:

```bash
GEMINI_API_KEY=your_gemini_api_key
SUPERMEMORY_API_KEY=your_supermemory_api_key
```

## Error Handling

- Each agent has try-catch blocks to handle errors gracefully
- Errors are collected in the state's `errors` list
- Processing continues even if individual agents fail
- Fallback logic provides basic results when AI calls fail

## Future Enhancements

1. **Parallel Agent Execution**: Run independent agents in parallel
2. **Caching**: Cache Gemini responses to reduce API calls
3. **More Content Types**: Add support for educational, comedy, news, etc.
4. **External API Integration**: 
   - Google Maps API for place details
   - Shopping APIs for product prices
   - Recipe APIs for nutritional info
5. **User Feedback Loop**: Learn from user interactions to improve trust scores
6. **Multi-language Support**: Process content in different languages
7. **Video Analysis**: Analyze video content directly using Gemini Vision

## Monitoring

The agent flow provides detailed logging:

```
🚀 Starting Reel Intelligence Agent Flow
🔨 [Agent 0] Reel Context Builder - Starting...
✅ [Agent 0] Context built for: Amazing Workout Routine
🧠 [Agent 1] Gemini Content Understanding - Starting...
✅ [Agent 1] Content type: workout
🎯 [Agent 2] Trust Score Calculator - Starting...
✅ [Agent 2] Trust score: 85.5/100
🎨 [Agent 3] Type-Specific Enrichment - Starting...
✅ [Agent 3] Enriched as: workout
🎭 [Agent 4] Orchestrator - Assembling final intelligence...
✅ [Agent 4] Final intelligence object created!
✅ Reel Intelligence Generation Complete!
```

## License

Part of the Save_act project.

