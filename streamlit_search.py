import os
import requests
import streamlit as st
from dotenv import load_dotenv
import json

# Import the reel intelligence agent
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.services.reel_intelligence_agent import generate_reel_intelligence

load_dotenv()
API_URL = "https://api.supermemory.ai/v3/search"
DOCUMENT_API_URL = "https://api.supermemory.ai/v3/documents"
API_KEY = os.environ.get("SUPERMEMORY_API_KEY") or ""


def call_search_api(query: str):
    if not API_KEY:
        st.error("SUPERMEMORY_API_KEY is not set in environment variables.")
        return None

    payload = {"q": query, "chunkThreshold": 0.7}
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Error calling Supermemory API: {e}")
        return None


def call_document_api(document_id: str):
    """Fetch document details by document ID"""
    if not API_KEY:
        st.error("SUPERMEMORY_API_KEY is not set in environment variables.")
        return None

    url = f"{DOCUMENT_API_URL}/{document_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Error calling Document API: {e}")
        return None


def get_document_with_keyframes(document_id: str, custom_id: str = None):
    """
    Two-step process:
    1. Fetch main document details
    2. Search for all images with matching customId
    
    Returns: (main_document, keyframe_images)
    """
    if not API_KEY:
        st.error("SUPERMEMORY_API_KEY is not set in environment variables.")
        return None, []
    
    # Step 1: Fetch main document
    main_doc = call_document_api(document_id)
    
    if not main_doc:
        return None, []
    
    # Extract customId from main document metadata
    if not custom_id:
        metadata = main_doc.get("metadata", {})
        custom_id = metadata.get("customId")
    
    if not custom_id:
        # No customId found, return just the main document
        return main_doc, []
    
    # Step 2: Search for all images with matching customId
    search_payload = {
        "q": "images",  # Empty query to get all matching documents
        "chunkThreshold": 0.5,
        "filters": {
            "AND": [
                {
                    "key": "customId",
                    "value": custom_id,
                    "negate": False
                }
            ]
        }
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.post(API_URL, json=search_payload, headers=headers, timeout=30)
        resp.raise_for_status()
        search_results = resp.json()
        
        # Filter only image type results
        keyframe_images = []
        for item in search_results.get("results", []):
            if item.get("type") == "image":
                keyframe_images.append(item)
        
        return main_doc, keyframe_images
        
    except requests.RequestException as e:
        st.error(f"Error searching for keyframes: {e}")
        return main_doc, []


def extract_unique_results(data):
    if not data or "results" not in data:
        return []

    seen_ids = set()
    unique = []


    for item in data.get("results", []):
        item_type = item.get("type")
        doc_id = item.get("documentId")
        
        
        # Filter only text type results
        if item_type != "text":
            continue
            
        if not doc_id or doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)

        metadata = item.get("metadata") or {}
        source_url = metadata.get("source_url") or "No source URL available"
        title = item.get("title") or metadata.get("topic") or "Untitled"

        unique.append(
            {
                "documentId": doc_id,
                "source_url": source_url,
                "title": title,
                "customId": metadata.get("customId"),
            }
        )

    return unique


def main():
    st.set_page_config(page_title="Supermemory Search", page_icon="🔍", layout="wide")

    # Initialize session state
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "search"
    if "selected_result" not in st.session_state:
        st.session_state.selected_result = None
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "reel_intelligence" not in st.session_state:
        st.session_state.reel_intelligence = None
    if "show_intelligence" not in st.session_state:
        st.session_state.show_intelligence = False

    # Back button if in detail view
    if st.session_state.view_mode == "detail":
        if st.button("← Back to Search Results"):
            st.session_state.view_mode = "search"
            st.session_state.selected_result = None
            st.rerun()

    # Search View
    if st.session_state.view_mode == "search":
        st.title("Supermemory Search")
        st.write(
            "Enter a query below. The app will call the Supermemory search API and show unique documents using their source URLs."
        )

        query = st.text_input("Search query", placeholder="e.g. routine for skin care for melasma")

        if st.button("Search") and query.strip():
            with st.spinner("Searching..."):
                data = call_search_api(query.strip())

            results = extract_unique_results(data)
            st.session_state.search_results = results

        # Display results
        if not st.session_state.search_results:
            if query:
                st.info("No results found.")
        else:
            st.subheader(f"Results ({len(st.session_state.search_results)})")
            for idx, r in enumerate(st.session_state.search_results):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(
                        f"**{r['title']}**  \n"
                        f"Document ID: `{r['documentId']}`  \n"
                        f"Source: {r['source_url'] if r['source_url'].startswith('http') else r['source_url']}"
                    )
                
                with col2:
                    if st.button("View Details", key=f"view_{idx}"):
                        st.session_state.selected_result = r
                        st.session_state.view_mode = "detail"
                        st.rerun()
                
                st.divider()

    # Detail View
    elif st.session_state.view_mode == "detail":
        result = st.session_state.selected_result
        if result:
            st.title(f"📄 {result['title']}")
            st.markdown(f"**Document ID:** `{result['documentId']}`")
            st.markdown(f"**Source:** {result['source_url']}")
            if result.get('customId'):
                st.markdown(f"**Custom ID:** `{result['customId']}`")
            
            st.divider()
            
            # Two-step process: Fetch main document and all related keyframes
            with st.spinner("Loading document details and keyframes..."):
                main_doc, keyframe_images = get_document_with_keyframes(
                    result['documentId'], 
                    result.get('customId')
                )
            
            # Action buttons
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("🤖 Generate Agentic Flow", type="primary", use_container_width=True):
                    st.session_state.show_intelligence = True
                    
                    # Run the agent flow
                    with st.spinner("🚀 Running multi-agent intelligence flow..."):
                        try:
                            reel_intelligence = generate_reel_intelligence(
                                document_id=result['documentId'],
                                custom_id=result.get('customId', ''),
                                main_document=main_doc,
                                keyframe_images=keyframe_images
                            )
                            st.session_state.reel_intelligence = reel_intelligence
                            st.success("✅ Reel Intelligence generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Error generating intelligence: {str(e)}")
                            st.session_state.reel_intelligence = None
            
            # Display Reel Intelligence if generated
            if st.session_state.show_intelligence and st.session_state.reel_intelligence:
                st.divider()
                st.header("🧠 Reel Intelligence")
                
                intelligence = st.session_state.reel_intelligence
                
                # Instagram Metrics (if available)
                instagram_metrics = intelligence.get("instagram_metrics")
                if instagram_metrics and instagram_metrics.get("success"):
                    st.subheader("📊 Real-Time Instagram Metrics")
                    metrics = instagram_metrics.get("metrics", {})
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("👍 Likes", f"{metrics.get('likes', 0):,}")
                    with col2:
                        st.metric("👁️ Views", f"{metrics.get('views', 0):,}")
                    with col3:
                        st.metric("💬 Comments", f"{metrics.get('comments', 0):,}")
                    with col4:
                        engagement_rate = 0
                        if metrics.get('views', 0) > 0:
                            engagement_rate = (metrics.get('likes', 0) / metrics.get('views', 0)) * 100
                        st.metric("📈 Engagement", f"{engagement_rate:.1f}%")
                    
                    # Additional metrics if available from API
                    if metrics.get('shares') or metrics.get('saves') or metrics.get('reach'):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if metrics.get('shares'):
                                st.metric("🔄 Shares", f"{metrics.get('shares', 0):,}")
                        with col2:
                            if metrics.get('saves'):
                                st.metric("💾 Saves", f"{metrics.get('saves', 0):,}")
                        with col3:
                            if metrics.get('reach'):
                                st.metric("📡 Reach", f"{metrics.get('reach', 0):,}")
                    
                    st.caption(f"Fetched at: {instagram_metrics.get('fetched_at', 'Unknown')}")
                    st.divider()
                
                # Trust Badge
                trust_info = intelligence.get("trust_assessment", {})
                col1, col2, col3 = st.columns([1, 2, 3])
                with col1:
                    st.metric("Trust Score", f"{trust_info.get('score', 0):.1f}/100")
                with col2:
                    st.markdown(f"### {trust_info.get('badge', '🟡 Unknown')}")
                with col3:
                    st.info(trust_info.get('reasoning', 'No reasoning available'))
                
                st.divider()
                
                # Content Understanding
                content_understanding = intelligence.get("content_understanding", {})
                st.subheader("📊 Content Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Content Type:** {content_understanding.get('content_type', 'Unknown')}")
                    st.markdown(f"**Sentiment:** {content_understanding.get('sentiment', 'Unknown')}")
                with col2:
                    topics = content_understanding.get('topics', [])
                    if topics:
                        st.markdown(f"**Topics:** {', '.join(topics[:5])}")
                    entities = content_understanding.get('entities', [])
                    if entities:
                        st.markdown(f"**Entities:** {', '.join(entities[:5])}")
                
                st.markdown(f"**Summary:** {content_understanding.get('summary', 'No summary available')}")
                # Gemini-suggested generic actions (non-clickable text)
                suggested_actions = content_understanding.get("suggested_actions") or []
                if suggested_actions:
                    st.markdown("**Model-Suggested Actions:**")
                    for act in suggested_actions[:5]:
                        st.markdown(f"- {act}")
                
                st.divider()
                
                # Type-Specific Intelligence
                type_specific = intelligence.get("type_specific_intelligence", {})
                if type_specific:
                    st.subheader("🎯 Type-Specific Intelligence")
                    enrichments = type_specific.get("enrichments", {})
                    
                    if enrichments:
                        st.markdown(f"**Type:** {enrichments.get('type', 'Unknown')}")
                        
                        # Display action items (generic text)
                        action_items = enrichments.get("action_items", [])
                        if action_items:
                            st.markdown("**Suggested Actions:**")
                            for action in action_items:
                                st.markdown(f"- {action}")

                        # Display structured, clickable actions (e.g. maps / shopping)
                        actions = enrichments.get("actions", [])
                        if actions:
                            st.markdown("**Quick Actions:**")
                            for a in actions:
                                label = a.get("label", "Open")
                                url = a.get("url")
                                if url:
                                    st.link_button(label, url)
                        
                        # Display type-specific data
                        if enrichments.get('type') == 'place_to_visit':
                            places = enrichments.get('places', [])
                            if places:
                                st.markdown(f"**Places:** {', '.join(places)}")
                            suggestions = enrichments.get('suggestions', [])
                            for suggestion in suggestions:
                                st.markdown(f"🗺️ {suggestion}")
                        
                        elif enrichments.get('type') == 'product_review':
                            products = enrichments.get('products', [])
                            if products:
                                st.markdown(f"**Products:** {', '.join(products)}")
                            links = enrichments.get('shopping_links', [])
                            for link in links:
                                st.markdown(f"🛒 {link}")
                        
                        elif enrichments.get('type') == 'recipe':
                            ingredients = enrichments.get('ingredients', [])
                            if ingredients:
                                st.markdown("**Ingredients:**")
                                for ing in ingredients[:10]:
                                    st.markdown(f"- {ing}")
                        
                        elif enrichments.get('type') == 'workout':
                            exercises = enrichments.get('exercises', [])
                            if exercises:
                                st.markdown("**Exercises:**")
                                for ex in exercises[:10]:
                                    st.markdown(f"- {ex}")
                            if enrichments.get('duration'):
                                st.markdown(f"**Duration:** {enrichments.get('duration')}")
                            if enrichments.get('difficulty'):
                                st.markdown(f"**Difficulty:** {enrichments.get('difficulty')}")
                
                st.divider()
                
                # Full Intelligence Object (expandable)
                with st.expander("🔍 View Full Intelligence Object (JSON)"):
                    st.json(intelligence)
            
            st.divider()
            
            # Original document details
            if main_doc:
                with st.expander("📝 View Raw Document Details"):
                    st.json(main_doc)
            
            # Display keyframe images found via customId filter
            if keyframe_images:
                st.divider()
                st.subheader(f"🖼️ Keyframes ({len(keyframe_images)})")
                st.write(f"Found {len(keyframe_images)} images with matching customId: `{result.get('customId')}`")
                
                for kf_idx, kf_item in enumerate(keyframe_images):
                    with st.expander(f"Keyframe {kf_idx + 1} - ID: {kf_item.get('documentId')}"):
                        st.json(kf_item)
                        
                        # Display metadata if available
                        metadata = kf_item.get('metadata', {})
                        if metadata:
                            st.write("**Metadata:**")
                            st.write(f"- Frame Index: {metadata.get('frame_index', 'N/A')}")
                            st.write(f"- Category: {metadata.get('category', 'N/A')}")
                            st.write(f"- Topic: {metadata.get('topic', 'N/A')}")
            else:
                st.info("No keyframe images found for this document.")


if __name__ == "__main__":
    main()


