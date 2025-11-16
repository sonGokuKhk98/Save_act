# Document ID Flow

## Overview

The application now uses `document_id` as the primary identifier for reels fetched from Supermemory. This document explains the complete flow from search to AI reconstruction.

## Flow Diagram

```
User Search Query
    ↓
/api/reels/search (POST)
    ↓
Supermemory Search API
    ↓
Returns: document_id, title, thumbnail_url, score
    ↓
User Clicks on Result
    ↓
/api/reels/document/{document_id} (GET)
    ↓
Fetches main document + keyframes from Supermemory
    ↓
Caches in REELS dictionary with document_id as key
    ↓
Renders in UI (code.html)
    ↓
User Clicks "AI Reconstruct"
    ↓
/api/agents/reconstruct/{document_id} (GET)
    ↓
Gemini generates enhanced summary
    ↓
Returns: heading, subtitle, rich_text
    ↓
UI updates with reconstructed content
```

## Key Endpoints

### 1. Search Reels
**Endpoint:** `POST /api/reels/search`

**Request:**
```json
{
  "query": "user search query",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "title": "Reel Title",
      "thumbnail_url": "https://...",
      "reel_id": "document_id_value",
      "document_id": "document_id_value",
      "score": 0.95
    }
  ],
  "total": 5
}
```

### 2. Get Document Details
**Endpoint:** `GET /api/reels/document/{document_id}`

**Response:**
```json
{
  "document": {
    "documentId": "...",
    "title": "...",
    "summary": "...",
    "content": "{...}",
    "metadata": {...}
  },
  "keyframes": [
    {
      "documentId": "keyframe_doc_id",
      "url": "https://...",
      "type": "image",
      "summary": "...",
      "timestamp": "...",
      "frame_number": 1
    }
  ],
  "custom_id": "unique_custom_id"
}
```

**Side Effect:** Caches the document in the `REELS` dictionary:
```python
REELS[document_id] = {
    "document_id": document_id,
    "category": "generic",
    "is_generic": True,
    "model_name": "GenericExtraction",
    "extraction": {...},
    "source_url": "...",
    "thumbnail_url": "...",
    "_from_supermemory": True
}
```

### 3. AI Reconstruct
**Endpoint:** `GET /api/agents/reconstruct/{document_id}`

**Flow:**
1. Checks if `document_id` exists in `REELS` cache
2. If not cached, fetches from Supermemory (via `_ensure_document_cached`)
3. Extracts `extraction` and `raw_data` from cached reel
4. Calls Gemini with reconstruction prompt
5. Parses and validates JSON response
6. Returns reconstruction plan

**Response:**
```json
{
  "heading": "Enhanced Heading",
  "subtitle": "Improved one-line summary",
  "rich_text": "Multi-paragraph enhanced summary with proper formatting...\n\n- Bullet point 1\n- Bullet point 2"
}
```

## Frontend Integration

### Setting Up Document ID
```javascript
// In code.html, when loading from Supermemory
const documentId = urlParams.get('document_id');
window.__REEL_ID__ = documentId;
```

### AI Reconstruct Button Handler
```javascript
const reconstructBtn = document.getElementById('gx-agentic-reconstruct');
reconstructBtn.addEventListener('click', async () => {
  const documentId = window.__REEL_ID__;
  const resp = await fetch(
    `/api/agents/reconstruct/${encodeURIComponent(documentId)}`
  );
  const plan = await resp.json();
  applyReconstructPlan(plan);
});
```

## Error Handling Improvements

### JSON Parsing Robustness
The `_call_gemini_for_reconstruct` function now:

1. **Tries multiple extraction methods:**
   - First attempts to extract from code blocks (```json ... ```)
   - Falls back to raw JSON object extraction

2. **Better error messages:**
   - Logs the raw Gemini response on parse failure
   - Shows the extracted JSON string for debugging
   - Provides clear error details to frontend

3. **Enhanced prompt:**
   - Explicitly instructs Gemini to escape strings properly
   - Warns about trailing commas and invalid JSON
   - Requests proper use of `\n` for line breaks

### Document Caching
The `_ensure_document_cached` function:
- Checks `REELS` cache first
- Fetches from Supermemory if not cached
- Includes keyframes in the cached data
- Handles errors gracefully with HTTPException

## Data Structure

### Cached Reel Object
```python
{
    "document_id": "abc123",           # Primary identifier
    "reel_id": "abc123",               # For backwards compatibility
    "category": "generic",
    "is_generic": True,
    "model_name": "GenericExtraction",
    "extraction": {
        "title": "...",
        "description": "...",
        "category": "generic",
        "confidence_score": 0.85,
        "source_url": "...",
        "raw_data": {
            # Original content data
            "_supermemory_id": "abc123",
            "_custom_id": "unique_id",
            "_keyframes": [...]
        }
    },
    "formatted_summary": None,
    "created_at": "2025-11-16T...",
    "source_url": "...",
    "thumbnail_url": "...",
    "errors": [],
    "_from_supermemory": True
}
```

## Testing the Flow

### 1. Search for Content
```bash
curl -X POST http://localhost:8000/api/reels/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cooking recipe", "limit": 5}'
```

### 2. Get Document Details
```bash
curl http://localhost:8000/api/reels/document/{document_id}
```

### 3. AI Reconstruct
```bash
curl http://localhost:8000/api/agents/reconstruct/{document_id}
```

## Common Issues and Solutions

### Issue: "Failed to parse reconstruction JSON from Gemini"
**Cause:** Gemini returned malformed JSON (unescaped quotes, trailing commas, etc.)

**Solution:** 
- The improved prompt now explicitly requests proper JSON escaping
- The parser tries multiple extraction methods
- Logs are printed for debugging

### Issue: "Document not found in cache or Supermemory"
**Cause:** Invalid document_id or document was deleted

**Solution:**
- Verify the document_id is correct
- Check Supermemory API key is configured
- Ensure document exists in Supermemory

### Issue: "Reconstruction plan rich_text must be a non-empty string"
**Cause:** Gemini didn't provide the `rich_text` field

**Solution:**
- Check the prompt is being sent correctly
- Verify Gemini API is working
- Try with a different model (flash vs pro)

## Future Enhancements

1. **Persistent Cache:** Replace in-memory `REELS` dict with Redis or database
2. **Retry Logic:** Add automatic retries for Gemini API failures
3. **Streaming:** Support streaming responses for long reconstructions
4. **Versioning:** Track multiple reconstruction versions per document
5. **User Feedback:** Allow users to rate reconstruction quality

