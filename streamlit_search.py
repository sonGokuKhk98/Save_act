import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
API_URL = "https://api.supermemory.ai/v3/search"
API_KEY = os.environ.get("SUPERMEMORY_API_KEY") or ""


def call_search_api(query: str):
    if not API_KEY:
        st.error("SUPERMEMORY_API_KEY is not set in environment variables.")
        return None

    payload = {"q": query, "chunkThreshold": 0.6}
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


def extract_unique_results(data):
    if not data or "results" not in data:
        return []

    seen_ids = set()
    unique = []

    for item in data.get("results", []):
        doc_id = item.get("documentId")
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
            }
        )

    return unique


def main():
    st.set_page_config(page_title="Supermemory Search", page_icon="🔍", layout="centered")

    st.title("Supermemory Search")
    st.write(
        "Enter a query below. The app will call the Supermemory search API and show unique documents using their source URLs."
    )

    query = st.text_input("Search query", placeholder="e.g. routine for skin care for melasma")

    if st.button("Search") and query.strip():
        with st.spinner("Searching..."):
            data = call_search_api(query.strip())

        results = extract_unique_results(data)

        if not results:
            st.info("No results found.")
        else:
            st.subheader(f"Results ({len(results)})")
            for r in results:
                st.markdown(
                    f"- **{r['title']}**  \n"
                    f"  Document ID: `{r['documentId']}`  \n"
                    f"  Source: {r['source_url'] if r['source_url'].startswith('http') else r['source_url']}"
                )


if __name__ == "__main__":
    main()


