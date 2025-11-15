"""
Reel Intelligence Agent Flow using LangGraph

This module implements a multi-agent system that processes Instagram reel data
to generate comprehensive intelligence including trust scores, enriched metadata,
and type-specific insights.
"""

import os
from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from datetime import datetime
import operator
import json

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Import Instagram API client
from .instagram_api_client import fetch_instagram_metrics

load_dotenv()

# Initialize Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=gemini_api_key,
    temperature=0.7
)


# ============================================================================
# State Definition
# ============================================================================

class ReelIntelligenceState(TypedDict):
    """State object that flows through the agent graph"""
    
    # Input data
    document_id: str
    custom_id: str
    main_document: Dict[str, Any]
    keyframe_images: List[Dict[str, Any]]
    
    # Agent outputs
    reel_context: Optional[Dict[str, Any]]
    instagram_metrics: Optional[Dict[str, Any]]  # Real-time metrics from Instagram API
    content_understanding: Optional[Dict[str, Any]]
    trust_score: Optional[float]
    trust_reasoning: Optional[str]
    type_specific_data: Optional[Dict[str, Any]]
    
    # Final output
    reel_intelligence: Optional[Dict[str, Any]]
    
    # Messages for agent communication
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Error tracking
    errors: List[str]


# ============================================================================
# Agent 0: Reel Context Builder
# ============================================================================

def reel_context_builder_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 0: Builds comprehensive context from the reel document
    Extracts metrics, metadata, content, and organizes keyframes
    Also fetches real-time metrics from Instagram API
    """
    print("🔨 [Agent 0] Reel Context Builder - Starting...")
    
    try:
        main_doc = state["main_document"]
        keyframes = state["keyframe_images"]
        
        # Parse the content (which is JSON string of the extraction)
        content_str = main_doc.get("content", "{}")
        try:
            content_data = json.loads(content_str) if isinstance(content_str, str) else content_str
        except json.JSONDecodeError:
            content_data = {}
        
        source_url = main_doc.get("metadata", {}).get("source_url")
        
        # Fetch real-time Instagram metrics
        instagram_data = None
        if source_url and "instagram.com" in source_url:
            print("   📊 Fetching real-time Instagram metrics...")
            try:
                instagram_data = fetch_instagram_metrics(source_url)
                if instagram_data.get("success"):
                    state["instagram_metrics"] = instagram_data
                    print(f"   ✅ Instagram metrics fetched successfully")
                else:
                    print(f"   ⚠️  Could not fetch Instagram metrics: {instagram_data.get('error')}")
            except Exception as e:
                print(f"   ⚠️  Instagram API error: {str(e)}")
        
        # Use Instagram API metrics if available, otherwise use stored metrics
        if instagram_data and instagram_data.get("success"):
            api_metrics = instagram_data.get("metrics", {})
            metrics = {
                "likes": api_metrics.get("likes", api_metrics.get("like_count", 0)),
                "views": api_metrics.get("views", api_metrics.get("view_count", 0)),
                "comments_count": api_metrics.get("comments", api_metrics.get("comment_count", 0)),
                "shares": api_metrics.get("shares", 0),
                "saves": api_metrics.get("saved", 0),
                "reach": api_metrics.get("reach", 0),
                "impressions": api_metrics.get("impressions", 0),
                "engagement": api_metrics.get("engagement", 0),
                "source": "instagram_api",
                "fetched_at": instagram_data.get("fetched_at")
            }
        else:
            # Fallback to stored metrics from extraction
            metrics = {
                "likes": content_data.get("likes", 0),
                "views": content_data.get("views", 0),
                "comments_count": content_data.get("comments_count", 0),
                "source": "extraction_cache"
            }
        
        # Build reel context
        reel_context = {
            "document_id": state["document_id"],
            "custom_id": state["custom_id"],
            "title": content_data.get("title", "Untitled"),
            "category": content_data.get("category", "unknown"),
            "source_url": source_url,
            "extracted_at": main_doc.get("metadata", {}).get("extracted_at"),
            "confidence_score": content_data.get("confidence_score", 0.0),
            
            # Content details
            "transcript": content_data.get("transcript", ""),
            "description": content_data.get("description", ""),
            "hashtags": content_data.get("hashtags", []),
            "mentions": content_data.get("mentions", []),
            
            # Real-time or cached metrics
            "metrics": metrics,
            
            # Instagram user info (if available from API)
            "username": instagram_data.get("details", {}).get("username") if instagram_data else None,
            "timestamp": instagram_data.get("details", {}).get("timestamp") if instagram_data else None,
            
            # Keyframes info
            "keyframes_count": len(keyframes),
            "keyframes_ids": [kf.get("documentId") for kf in keyframes],
            
            # Type-specific data
            "type_specific": content_data.get("details", {}),
        }
        
        state["reel_context"] = reel_context
        state["messages"].append(
            AIMessage(content=f"✅ Built reel context for: {reel_context['title']} (Metrics: {metrics['source']})")
        )
        
        print(f"✅ [Agent 0] Context built for: {reel_context['title']}")
        print(f"   📊 Metrics source: {metrics['source']}")
        
    except Exception as e:
        error_msg = f"Error in Reel Context Builder: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 0] {error_msg}")
    
    return state


# ============================================================================
# Agent 1: Gemini Content Understanding
# ============================================================================

def gemini_content_understanding_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 1: Uses Gemini to understand content type, extract entities, and generate summary
    """
    print("🧠 [Agent 1] Gemini Content Understanding - Starting...")
    
    try:
        reel_context = state["reel_context"]
        
        # Build prompt for Gemini
        prompt = f"""
Analyze this Instagram reel content and provide structured insights:

Title: {reel_context['title']}
Category: {reel_context['category']}
Transcript: {reel_context['transcript'][:500]}...
Description: {reel_context['description']}
Hashtags: {', '.join(reel_context['hashtags'][:10])}

Please provide:
1. Content Type Classification (workout, recipe, travel, product_review, educational, entertainment, etc.)
2. Key Entities (people, places, products, brands mentioned)
3. Main Topics/Themes
4. Brief Summary (2-3 sentences)
5. Sentiment (positive, neutral, negative)

Format your response as JSON with keys: content_type, entities, topics, summary, sentiment
"""
        
        # Call Gemini
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        # Try to parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            content_understanding = json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            content_understanding = {
                "content_type": reel_context['category'],
                "entities": [],
                "topics": [],
                "summary": response_text[:200],
                "sentiment": "neutral"
            }
        
        state["content_understanding"] = content_understanding
        state["messages"].append(
            AIMessage(content=f"✅ Content understood: {content_understanding.get('content_type')}")
        )
        
        print(f"✅ [Agent 1] Content type: {content_understanding.get('content_type')}")
        
    except Exception as e:
        error_msg = f"Error in Gemini Content Understanding: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 1] {error_msg}")
    
    return state


# ============================================================================
# Agent 2: Trust Score Calculator
# ============================================================================

def trust_score_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 2: Calculates trust score based on metrics, content quality, and Gemini analysis
    """
    print("🎯 [Agent 2] Trust Score Calculator - Starting...")
    
    try:
        reel_context = state["reel_context"]
        content_understanding = state["content_understanding"]
        
        # Build trust score calculation prompt
        prompt = f"""
Calculate a trust score (0-100) for this Instagram reel based on the following factors:

Content Details:
- Title: {reel_context['title']}
- Category: {reel_context['category']}
- Confidence Score: {reel_context['confidence_score']}
- Content Type: {content_understanding.get('content_type')}
- Sentiment: {content_understanding.get('sentiment')}

Metrics:
- Likes: {reel_context['metrics']['likes']}
- Views: {reel_context['metrics']['views']}
- Comments: {reel_context['metrics']['comments_count']}

Content Quality:
- Has Transcript: {bool(reel_context['transcript'])}
- Has Description: {bool(reel_context['description'])}
- Number of Hashtags: {len(reel_context['hashtags'])}
- Number of Keyframes: {reel_context['keyframes_count']}

Consider:
1. Engagement rate (likes/views ratio)
2. Content completeness
3. Sentiment alignment
4. Confidence score from extraction

Provide:
1. Trust Score (0-100)
2. Brief reasoning (2-3 sentences)

Format as JSON: {{"trust_score": 85, "reasoning": "..."}}
"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content
        
        # Parse response
        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            
            trust_data = json.loads(json_str)
            state["trust_score"] = float(trust_data.get("trust_score", 50))
            state["trust_reasoning"] = trust_data.get("reasoning", "")
        except:
            # Fallback calculation
            base_score = reel_context['confidence_score'] * 100
            engagement_boost = min(20, (reel_context['metrics']['likes'] / max(1, reel_context['metrics']['views'])) * 100)
            state["trust_score"] = min(100, base_score + engagement_boost)
            state["trust_reasoning"] = "Calculated based on confidence score and engagement metrics"
        
        state["messages"].append(
            AIMessage(content=f"✅ Trust score calculated: {state['trust_score']:.1f}/100")
        )
        
        print(f"✅ [Agent 2] Trust score: {state['trust_score']:.1f}/100")
        
    except Exception as e:
        error_msg = f"Error in Trust Score Agent: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 2] {error_msg}")
    
    return state


# ============================================================================
# Agent 3: Type-Specific Enrichment
# ============================================================================

def type_specific_enrichment_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 3: Applies type-specific enrichment based on content type
    """
    print("🎨 [Agent 3] Type-Specific Enrichment - Starting...")
    
    try:
        content_type = state["content_understanding"].get("content_type", "").lower()
        reel_context = state["reel_context"]
        type_specific_data = reel_context.get("type_specific", {})
        
        enriched_data = {
            "content_type": content_type,
            "original_data": type_specific_data,
            "enrichments": {}
        }
        
        # Type-specific processing
        if "travel" in content_type or "place" in content_type:
            # Travel/Place enrichment
            places = state["content_understanding"].get("entities", [])
            enriched_data["enrichments"] = {
                "type": "place_to_visit",
                "places": places,
                "suggestions": [
                    f"Search Google Maps for: {place}" for place in places[:3]
                ],
                "action_items": [
                    "Get directions",
                    "Check reviews",
                    "Save to travel list"
                ]
            }
            
        elif "product" in content_type or "review" in content_type:
            # Product review enrichment
            entities = state["content_understanding"].get("entities", [])
            enriched_data["enrichments"] = {
                "type": "product_review",
                "products": entities,
                "shopping_links": [
                    f"Search Amazon for: {entity}" for entity in entities[:3]
                ],
                "action_items": [
                    "Compare prices",
                    "Read more reviews",
                    "Add to wishlist"
                ]
            }
            
        elif "recipe" in content_type or "food" in content_type:
            # Recipe enrichment
            enriched_data["enrichments"] = {
                "type": "recipe",
                "ingredients": type_specific_data.get("ingredients", []),
                "steps": type_specific_data.get("steps", []),
                "action_items": [
                    "Save recipe",
                    "Create shopping list",
                    "Set cooking reminder"
                ]
            }
            
        elif "workout" in content_type or "fitness" in content_type:
            # Workout enrichment
            enriched_data["enrichments"] = {
                "type": "workout",
                "exercises": type_specific_data.get("exercises", []),
                "duration": type_specific_data.get("duration"),
                "difficulty": type_specific_data.get("difficulty_level"),
                "action_items": [
                    "Add to workout plan",
                    "Track progress",
                    "Set reminder"
                ]
            }
        else:
            # Generic enrichment
            enriched_data["enrichments"] = {
                "type": "general",
                "topics": state["content_understanding"].get("topics", []),
                "action_items": [
                    "Save for later",
                    "Share with friends"
                ]
            }
        
        state["type_specific_data"] = enriched_data
        state["messages"].append(
            AIMessage(content=f"✅ Type-specific enrichment completed: {content_type}")
        )
        
        print(f"✅ [Agent 3] Enriched as: {content_type}")
        
    except Exception as e:
        error_msg = f"Error in Type-Specific Enrichment: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 3] {error_msg}")
    
    return state


# ============================================================================
# Agent 4: Orchestrator - Final Assembly
# ============================================================================

def orchestrator_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 4: Orchestrator that merges all agent outputs into final Reel Intelligence Object
    """
    print("🎭 [Agent 4] Orchestrator - Assembling final intelligence...")
    
    try:
        reel_intelligence = {
            "metadata": {
                "document_id": state["document_id"],
                "custom_id": state["custom_id"],
                "generated_at": datetime.now().isoformat(),
                "agent_version": "1.0.0"
            },
            
            "reel_context": state["reel_context"],
            
            "instagram_metrics": state.get("instagram_metrics"),  # Real-time Instagram data
            
            "content_understanding": state["content_understanding"],
            
            "trust_assessment": {
                "score": state["trust_score"],
                "reasoning": state["trust_reasoning"],
                "badge": _get_trust_badge(state["trust_score"])
            },
            
            "type_specific_intelligence": state["type_specific_data"],
            
            "keyframes": {
                "count": len(state["keyframe_images"]),
                "ids": [kf.get("documentId") for kf in state["keyframe_images"]],
                "metadata": [kf.get("metadata", {}) for kf in state["keyframe_images"]]
            },
            
            "processing_info": {
                "errors": state["errors"],
                "messages": [msg.content for msg in state["messages"]]
            }
        }
        
        state["reel_intelligence"] = reel_intelligence
        state["messages"].append(
            AIMessage(content="✅ Reel Intelligence Object assembled successfully!")
        )
        
        print("✅ [Agent 4] Final intelligence object created!")
        
    except Exception as e:
        error_msg = f"Error in Orchestrator: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 4] {error_msg}")
    
    return state


def _get_trust_badge(score: float) -> str:
    """Helper to determine trust badge based on score"""
    if score >= 80:
        return "🟢 Highly Trusted"
    elif score >= 60:
        return "🟡 Moderately Trusted"
    elif score >= 40:
        return "🟠 Needs Verification"
    else:
        return "🔴 Low Trust"


# ============================================================================
# LangGraph Workflow Definition
# ============================================================================

def create_reel_intelligence_graph():
    """
    Creates and returns the LangGraph workflow for reel intelligence generation
    """
    
    # Create the graph
    workflow = StateGraph(ReelIntelligenceState)
    
    # Add nodes (agents)
    workflow.add_node("reel_context_builder", reel_context_builder_agent)
    workflow.add_node("content_understanding", gemini_content_understanding_agent)
    workflow.add_node("trust_score", trust_score_agent)
    workflow.add_node("type_specific", type_specific_enrichment_agent)
    workflow.add_node("orchestrator", orchestrator_agent)
    
    # Define the flow
    workflow.set_entry_point("reel_context_builder")
    workflow.add_edge("reel_context_builder", "content_understanding")
    workflow.add_edge("content_understanding", "trust_score")
    workflow.add_edge("trust_score", "type_specific")
    workflow.add_edge("type_specific", "orchestrator")
    workflow.add_edge("orchestrator", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# ============================================================================
# Main Execution Function
# ============================================================================

def generate_reel_intelligence(
    document_id: str,
    custom_id: str,
    main_document: Dict[str, Any],
    keyframe_images: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main function to generate reel intelligence using the agent flow
    
    Args:
        document_id: The main document ID
        custom_id: The custom ID linking document and keyframes
        main_document: The main document data
        keyframe_images: List of keyframe image documents
    
    Returns:
        Reel Intelligence Object with all enriched data
    """
    print("\n" + "="*80)
    print("🚀 Starting Reel Intelligence Agent Flow")
    print("="*80 + "\n")
    
    # Initialize state
    initial_state = {
        "document_id": document_id,
        "custom_id": custom_id,
        "main_document": main_document,
        "keyframe_images": keyframe_images,
        "reel_context": None,
        "instagram_metrics": None,
        "content_understanding": None,
        "trust_score": None,
        "trust_reasoning": None,
        "type_specific_data": None,
        "reel_intelligence": None,
        "messages": [],
        "errors": []
    }
    
    # Create and run the graph
    app = create_reel_intelligence_graph()
    
    try:
        # Execute the workflow
        final_state = app.invoke(initial_state)
        
        print("\n" + "="*80)
        print("✅ Reel Intelligence Generation Complete!")
        print("="*80 + "\n")
        
        return final_state["reel_intelligence"]
        
    except Exception as e:
        print(f"\n❌ Error in agent flow: {str(e)}\n")
        return {
            "error": str(e),
            "metadata": {
                "document_id": document_id,
                "custom_id": custom_id,
                "generated_at": datetime.now().isoformat()
            }
        }


# ============================================================================
# Visualization Helper
# ============================================================================

def visualize_graph():
    """
    Generate a visualization of the agent graph
    """
    try:
        app = create_reel_intelligence_graph()
        # This requires graphviz to be installed
        return app.get_graph().draw_mermaid()
    except Exception as e:
        return f"Could not generate visualization: {str(e)}"


if __name__ == "__main__":
    # Example usage
    print("Reel Intelligence Agent Flow Module")
    print("\nAgent Flow:")
    print("  [0] Reel Context Builder")
    print("  [1] Gemini Content Understanding")
    print("  [2] Trust Score Calculator")
    print("  [3] Type-Specific Enrichment")
    print("  [4] Orchestrator")
    print("\nUse generate_reel_intelligence() to process a reel.")

