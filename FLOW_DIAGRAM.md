# Document ID Flow - Visual Diagram

## Complete Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  User Types      │
                        │  Search Query    │
                        └──────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SEARCH ENDPOINT                                 │
│  POST /api/reels/search                                             │
│  { "query": "cooking", "limit": 10 }                                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Supermemory     │
                        │  Search API      │
                        └──────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SEARCH RESULTS                                  │
│  {                                                                   │
│    "results": [                                                      │
│      {                                                               │
│        "title": "Easy Pasta Recipe",                                │
│        "thumbnail_url": "https://...",                              │
│        "document_id": "abc123",  ← PRIMARY IDENTIFIER               │
│        "reel_id": "abc123",                                         │
│        "score": 0.95                                                │
│      }                                                               │
│    ]                                                                 │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  User Clicks     │
                        │  on Result       │
                        └──────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCUMENT FETCH ENDPOINT                           │
│  GET /api/reels/document/{document_id}                              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Fetch Main Document   │
                    │  from Supermemory      │
                    └────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Extract customId      │
                    │  from metadata         │
                    └────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Search for Keyframes  │
                    │  with matching         │
                    │  customId              │
                    └────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CACHE IN REELS DICTIONARY                         │
│  REELS[document_id] = {                                             │
│    "document_id": "abc123",                                         │
│    "category": "recipe",                                            │
│    "extraction": { ... },                                           │
│    "thumbnail_url": "...",                                          │
│    "_from_supermemory": True                                        │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RETURN TO FRONTEND                                │
│  {                                                                   │
│    "document": { ... },                                             │
│    "keyframes": [ ... ],                                            │
│    "custom_id": "unique_id"                                         │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Frontend Sets   │
                        │  window.         │
                        │  __REEL_ID__     │
                        │  = document_id   │
                        └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Render Content  │
                        │  in UI           │
                        └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  User Clicks     │
                        │  "AI Reconstruct"│
                        └──────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI RECONSTRUCT ENDPOINT                           │
│  GET /api/agents/reconstruct/{document_id}                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Check REELS Cache     │
                    │  for document_id       │
                    └────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                ▼ Found                    ▼ Not Found
        ┌──────────────┐          ┌──────────────────┐
        │ Use Cached   │          │ Fetch from       │
        │ Data         │          │ Supermemory      │
        └──────────────┘          │ & Cache          │
                    │             └──────────────────┘
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Extract extraction    │
                    │  and raw_data          │
                    └────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CALL GEMINI API                                   │
│  System Prompt: Category-aware instructions                         │
│  User Prompt: extraction + raw_data + JSON format instructions      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Gemini Generates      │
                    │  Enhanced Summary      │
                    └────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PARSE GEMINI RESPONSE                             │
│                                                                      │
│  Step 1: Try to extract from code blocks                            │
│          ```json { ... } ```                                        │
│                                                                      │
│  Step 2: If not found, extract raw JSON                             │
│          { ... }                                                     │
│                                                                      │
│  Step 3: Parse JSON                                                 │
│                                                                      │
│  Step 4: If parse fails, log full response for debugging            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RETURN RECONSTRUCTION PLAN                        │
│  {                                                                   │
│    "heading": "Enhanced Title",                                     │
│    "subtitle": "Clear summary",                                     │
│    "rich_text": "Multi-paragraph enhanced text...\n\n- Point 1"    │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Frontend        │
                        │  Applies Plan    │
                        │  to UI           │
                        └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  User Sees       │
                        │  Enhanced        │
                        │  Content         │
                        └──────────────────┘
```

## Key Components

### 1. Document ID
- **Primary identifier** throughout the system
- Comes from Supermemory's `documentId` field
- Used in all API calls after initial search

### 2. REELS Cache
- In-memory dictionary: `REELS[document_id] = {...}`
- Stores fetched documents to avoid repeated API calls
- Includes extraction, keyframes, and metadata

### 3. Gemini Integration
- Two main endpoints: `/plan/` and `/reconstruct/`
- Enhanced JSON parsing with fallback mechanisms
- Better error logging for debugging

### 4. Frontend Flow
- Sets `window.__REEL_ID__` with document_id
- Uses this for all subsequent API calls
- Renders content dynamically based on API responses

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Gemini Returns Response                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Try Code Block        │
                    │  Extraction            │
                    └────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                ▼ Found                    ▼ Not Found
        ┌──────────────┐          ┌──────────────────┐
        │ Extract JSON │          │ Try Raw JSON     │
        │ from Block   │          │ Extraction       │
        └──────────────┘          └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌────────────────────────┐
                    │  Parse JSON            │
                    └────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                ▼ Success                  ▼ Failure
        ┌──────────────┐          ┌──────────────────┐
        │ Return Plan  │          │ Log Full Response│
        └──────────────┘          │ Log Extracted    │
                                  │ JSON String      │
                                  │ Return Error     │
                                  └──────────────────┘
```

## Caching Strategy

```
API Call with document_id
        │
        ▼
    Is document_id in REELS cache?
        │
        ├─── Yes ──→ Return cached data
        │
        └─── No ──→ Fetch from Supermemory
                         │
                         ▼
                    Fetch main document
                         │
                         ▼
                    Extract customId
                         │
                         ▼
                    Search for keyframes
                         │
                         ▼
                    Build extraction object
                         │
                         ▼
                    Cache in REELS[document_id]
                         │
                         ▼
                    Return data
```

## JSON Parsing Strategy

```
Gemini Response Text
        │
        ▼
Try: ```json {...} ```
        │
        ├─── Found ──→ Extract JSON from block
        │                      │
        └─── Not Found ──→ Try: {...}
                               │
                               ├─── Found ──→ Extract raw JSON
                               │                      │
                               └─── Not Found ──→ Error: No JSON
                                                      │
                                        ┌─────────────┴─────────────┐
                                        │                           │
                                    ▼ Parse                     ▼ Parse
                                    Success                     Failure
                                        │                           │
                                        │                           ▼
                                        │                   Log full response
                                        │                   Log extracted JSON
                                        │                   Raise HTTPException
                                        │
                                        ▼
                                Return parsed data
```

## Summary

The flow is now:
1. **Search** → Get document_id
2. **Fetch** → Get document + keyframes + cache
3. **Render** → Show in UI
4. **Enhance** → AI Reconstruct with robust parsing
5. **Update** → Apply enhanced content to UI

All steps use `document_id` as the primary identifier, ensuring consistency throughout the system.

