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
import re
from urllib.parse import quote_plus

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from src.services.gemini_model_helper import _get_gemini_model

load_dotenv()

# Initialize Gemini (kept for backwards compatibility; most calls now use _get_gemini_model)
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
    #document_id: str
    #custom_id: str
    main_document: Dict[str, Any]
    keyframe_images: List[Dict[str, Any]]
    
    # Agent outputs
    reel_context: Optional[Dict[str, Any]]
    #instagram_metrics: Optional[Dict[str, Any]]  # Real-time metrics from Instagram API
    content_understanding: Optional[Dict[str, Any]]
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
        
        # NOTE: Real-time Instagram metrics are disabled for now.
        # We rely solely on cached/extracted metrics in the document.
        #instagram_data = None
        
        # Use Instagram API metrics if available, otherwise use stored metrics
        #if instagram_data and instagram_data.get("success"):
        #    api_metrics = instagram_data.get("metrics", {})
        #    metrics = {
        #        "likes": api_metrics.get("likes", api_metrics.get("like_count", 0)),
        #        "views": api_metrics.get("views", api_metrics.get("view_count", 0)),
        #        "comments_count": api_metrics.get("comments", api_metrics.get("comment_count", 0)),
        #        "shares": api_metrics.get("shares", 0),
        #        "saves": api_metrics.get("saved", 0),
        #        "reach": api_metrics.get("reach", 0),
        #        "impressions": api_metrics.get("impressions", 0),
        #        "engagement": api_metrics.get("engagement", 0),
        #        "source": "instagram_api",
        #        "fetched_at": instagram_data.get("fetched_at")
        #    }
        #else:
            # Fallback to stored metrics from extraction
        #    metrics = {
        #        "likes": content_data.get("likes", 0),
        #        "views": content_data.get("views", 0),
        #        "comments_count": content_data.get("comments_count", 0),
        #        "source": "extraction_cache"
        #    }
        
        # Build reel context
        reel_context = {
            #"document_id": state["document_id"],
            #"custom_id": state["custom_id"],
            "title": content_data.get("title", "Untitled"),
            "category": content_data.get("category", "unknown"),
            "source_url": source_url,
            "extracted_at": main_doc.get("metadata", {}).get("extracted_at"),
            #"confidence_score": content_data.get("confidence_score", 0.0),
            
            # Content details
            #"transcript": content_data.get("transcript", ""),
            #"description": content_data.get("description", ""),
            #"hashtags": content_data.get("hashtags", []),
            #"mentions": content_data.get("mentions", []),
            
            # Real-time or cached metrics
            #"metrics": metrics,
            
            # Instagram user info (if available from API)
            #"username": instagram_data.get("details", {}).get("username") if instagram_data else None,
            #"timestamp": instagram_data.get("details", {}).get("timestamp") if instagram_data else None,
            
            # Keyframes info
            "keyframes_count": len(keyframes),
            "keyframes_summary": [kf.get("summary") for kf in keyframes],
            
            # Type-specific data
            "type_specific": content_data.get("details", {}),
            "content": content_data,
        }
        
        state["reel_context"] = reel_context
        state["messages"].append(
            AIMessage(content=f"✅ Built reel context for: {reel_context['title']}")
        )
        
        print(f"✅ [Agent 0] Context built for: {reel_context['title']}")
        
    except Exception as e:
        error_msg = f"Error in Reel Context Builder: {str(e)}"
        state["errors"].append(error_msg)
        state["messages"].append(AIMessage(content=f"❌ {error_msg}"))
        print(f"❌ [Agent 0] {error_msg}")
    
    return state


# ============================================================================
# Agent 1: Gemini Content Understanding
# ============================================================================

def _call_gemini_for_content_understanding(reel_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shared helper to call Gemini and parse structured content understanding.

    Returns a dict with keys: content_type, entities, topics, summary, sentiment, suggested_actions.
    """
    import json as _json

    system_prompt = (
        "You are an assistant that analyzes short social video content.\n"
        "You receive structured JSON context for an Instagram reel and must "
        "return compact JSON describing what the content is about, without "
        "hallucinating concrete facts that are not implied.\n"
    )

    user_prompt = (
        "Here is the structured reel_context JSON:\n"
        f"{reel_context}\n\n"
        "Respond strictly as compact JSON with the following shape:\n"
        "{\n"
        #'  "content_type": "workout | recipe | travel | product_review | educational | entertainment | other",\n'
        '  "entities": ["list of key entities such as people, brands, products, or places"],\n'
        #'  "topics": ["list of high-level topics/themes"],\n'
        #'  "summary": "2-3 sentence plain-text summary of the reel",\n'
        #'  "sentiment": "positive | neutral | negative",\n'
        '  "suggested_actions": [\n'
        '    "short, user-facing action labels such as \\"Open in maps\\", \\"Search products\\", \\"Save recipe\\", etc."\n'
        "  ]\n"
        "}\n"
        "Do not add any extra keys, comments, or explanations outside this JSON object."
    )

    try:
        # Prefer Pro model when available; fall back to flash if we hit quota limits.
        model = _get_gemini_model(allow_pro=True)
        resp = model.generate_content([system_prompt, user_prompt])
    except Exception as exc:  # pragma: no cover - depends on remote API
        msg = str(exc)
        if "ResourceExhausted" in msg or "quota" in msg or "429" in msg:
            model = _get_gemini_model(allow_pro=False)
            resp = model.generate_content([system_prompt, user_prompt])
        else:
            raise

    text = resp.text or ""

    # Try to locate the JSON object within the model response.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        # Fallback: treat whole response as summary only.
        return {
            "content_type": reel_context.get("category", "unknown"),
            "entities": [],
            "topics": [],
            "summary": text[:400],
            "sentiment": "neutral",
        }

    try:
        data = _json.loads(match.group(0))
    except _json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "content_type": reel_context.get("category", "unknown"),
            "entities": [],
            "topics": [],
            "summary": text[:400],
            "sentiment": "neutral",
        }

    # Normalize and provide safe defaults
    suggested_actions = data.get("suggested_actions") or []
    if isinstance(suggested_actions, str):
        suggested_actions = [suggested_actions]

    return {
        "content_type": data.get("content_type") or reel_context.get("category", "unknown"),
        "entities": data.get("entities") or [],
        "topics": data.get("topics") or [],
        "summary": data.get("summary") or "",
        "sentiment": data.get("sentiment") or "neutral",
        "suggested_actions": suggested_actions,
    }


def gemini_content_understanding_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 1: Uses Gemini to understand content type, extract entities, and generate summary.

    This version reuses the shared Gemini model helper and robust JSON parsing
    pattern from the agent_actions module.
    """
    print("🧠 [Agent 1] Gemini Content Understanding - Starting...")
    
    try:
        reel_context = state["reel_context"]
        content_understanding = _call_gemini_for_content_understanding(reel_context)
        
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
# Agent 2: Type-Specific Enrichment
# ============================================================================

def type_specific_enrichment_agent(state: ReelIntelligenceState) -> ReelIntelligenceState:
    """
    Agent 2: Applies type-specific enrichment based on content type
    """
    print("🎨 [Agent 2] Type-Specific Enrichment - Starting...")
    
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

            # Build concrete Google Maps actions for the UI
            actions = []
            for place in places[:3]:
                if not place:
                    continue
                query = quote_plus(str(place))
                url = f"https://www.google.com/maps/search/?api=1&query={query}"
                actions.append(
                    {
                        "label": f"Open {place} in Google Maps",
                        "url": url,
                        "action_type": "maps_search",
                        "query": place,
                    }
                )

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
                ],
                # Structured actions the UI can render as clickable buttons
                "actions": actions,
            }
            
        elif "product" in content_type or "review" in content_type:
            # Product review enrichment
            entities = state["content_understanding"].get("entities", [])

            # Build concrete Amazon search actions for the UI
            from src.api.product_lens import search_amazon_product  # or wherever you put it

            actions = []
            for entity in entities[:3]:
                if not entity:
                    continue
                result = None
                try:
                    result = search_amazon_product(str(entity))
                except Exception:
                    result = None

                if result and result.get("link"):
                    url = result["link"]
                    label = f"View {entity} on Amazon"
                else:
                    # Fallback to simple search URL
                    query = quote_plus(str(entity))
                    url = f"https://www.amazon.com/s?k={query}"
                    label = f"Search Amazon for {entity}"

                actions.append(
                    {
                        "label": label,
                        "url": url,
                        "action_type": "shopping_search",
                        "query": entity,
                    }
                )

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
                ],
                # Structured actions the UI can render as clickable buttons
                "actions": actions,
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
                #"document_id": state["document_id"],
                #"custom_id": state["custom_id"],
                "generated_at": datetime.now().isoformat(),
                "agent_version": "1.0.0"
            },
            
            "reel_context": state["reel_context"],
            
            "instagram_metrics": state.get("instagram_metrics"),  # Real-time Instagram data
            
            "content_understanding": state["content_understanding"],
            
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
    workflow.add_node("type_specific", type_specific_enrichment_agent)
    workflow.add_node("orchestrator", orchestrator_agent)
    
    # Define the flow
    workflow.set_entry_point("reel_context_builder")
    workflow.add_edge("reel_context_builder", "content_understanding")
    workflow.add_edge("content_understanding", "type_specific")
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
        #"document_id": document_id,
        #"custom_id": custom_id,
        "main_document": main_document,
        "keyframe_images": keyframe_images,
        "reel_context": None,
        #"instagram_metrics": None,
        "content_understanding": None,
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
    print("  [2] Type-Specific Enrichment")
    print("  [3] Orchestrator")
    print("\nUse generate_reel_intelligence() to process a reel.")

